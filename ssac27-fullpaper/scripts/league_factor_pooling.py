"""Selectable tau^2 estimators for the league-factor partial pooling (ATI-2960).

`scripts/build_league_factors.py::partial_pool` estimates the between-league
variance of a destination block as ``var(factors) - mean(se^2)`` over EVERY cell.
One thin cell's se^2 can exceed var(factors) by itself, clip tau^2 to 0 and
collapse the whole block onto the tier mean (ATI-2901; poland-plk -> EuroLeague,
n = 2, SE 0.21, on 2026-09-04).

`build_league_factors.py` is sha256-pinned by the Sloan v10 artifacts
(`sloan_full_refit.CODE_FILES`), so it is NOT edited. This module adds the
alternatives beside it and selects one at run time:

* ``moment_all`` -- the shipped pooler. It CALLS ``blf.partial_pool``; it is not
  a re-implementation, so the old flag reproduces the table of record bitwise.
* ``floor_clearing`` (default for new fits) -- tau^2 from cells with
  ``n_pairs >= floor`` only; every usable cell is still shrunk, and the grand
  mean is still the precision-weighted mean over all usable cells. Identical to
  `simulate_translation_estimator.floor_clearing_pool`, the estimator ATI-2890
  measured, except that the fallback (fewer than 2 clearing cells) records the
  tau actually used instead of NaN.
* ``dersimonian_laird`` -- the printed alternative; same grand mean, so only
  tau^2 differs.

Every fit reports ``tau2_unclipped``, ``tau2_floored``, ``tau2_basis`` and
``n_tau_cells`` per block. ``tau`` is always the tau used for shrinkage: the
walk-forward reads a NaN tau as collapsed and the holdout reads it as not
collapsed, so NaN is never written for a block that was shrunk.

`pooler_in_effect` swaps the pooler inside the UNPINNED callers (the walk-forward
and holdout validators reach `blf.estimate_table` through the module attribute)
without touching their bytes.
"""

from __future__ import annotations

import contextlib
from collections.abc import Iterator
from dataclasses import dataclass

import numpy as np
import pandas as pd

import scripts.build_league_factors as blf

POOLERS = ("floor_clearing", "moment_all", "dersimonian_laird")
DEFAULT_POOLER = "floor_clearing"
SHIPPED_POOLER = "moment_all"
BLOCK_KEY = ["sample", "era", "destination", "stat"]
FLAG_COLUMNS = ["tau2_unclipped", "tau2_floored", "tau2_basis", "n_tau_cells", "pooler"]
DERIVED_COLUMNS = ["factor", "tier_mean", "tau", "pooled_collapsed", "reliable"]


@dataclass(frozen=True)
class PoolFit:
    """One block's pooling outcome."""

    pooled: np.ndarray
    grand: float
    tau: float
    tau2_unclipped: float
    tau2_floored: bool
    tau2_basis: str
    n_tau_cells: int


def _moment_unclipped(factors: np.ndarray, ses: np.ndarray) -> float:
    # Same expression, same operand order as blf.partial_pool.
    return float(np.var(factors, ddof=1) - np.mean(ses**2))


def _shrink(
    factors: np.ndarray, ses: np.ndarray, ok: np.ndarray, tau2: float
) -> tuple[np.ndarray, float]:
    """Shrink every usable cell toward the fixed-effect mean -- blf's arithmetic."""
    w0 = 1 / ses[ok] ** 2
    grand = float(np.sum(w0 * factors[ok]) / np.sum(w0))
    pooled = factors.copy()
    shrink = tau2 / (tau2 + ses[ok] ** 2) if tau2 > 0 else np.zeros(int(ok.sum()))
    pooled[ok] = grand + shrink * (factors[ok] - grand)
    return pooled, grand


def pool_block(
    factors: np.ndarray,
    ses: np.ndarray,
    n_pairs: np.ndarray,
    *,
    pooler: str,
    tau_floor: int,
) -> PoolFit:
    """Pool one destination block with the named tau^2 estimator."""
    if pooler not in POOLERS:
        raise ValueError(f"unknown pooler {pooler!r}; choose from {POOLERS}")
    factors = np.asarray(factors, dtype=float)
    ses = np.asarray(ses, dtype=float)
    n_pairs = np.asarray(n_pairs)
    ok = np.isfinite(factors) & np.isfinite(ses) & (ses > 0)
    if ok.sum() < 2:
        # blf.partial_pool leaves the block raw here; so does every pooler.
        return PoolFit(
            factors.copy(),
            float("nan"),
            float("nan"),
            float("nan"),
            False,
            "none",
            int(ok.sum()),
        )

    basis = pooler
    tau_cells = ok
    if pooler == "floor_clearing":
        clear = ok & (n_pairs >= tau_floor)
        if clear.sum() >= 2:
            tau_cells = clear
        else:
            basis = "all_cells_fallback"

    if basis in ("moment_all", "all_cells_fallback"):
        pooled, grand, tau = blf.partial_pool(factors, ses)
        unclipped = _moment_unclipped(factors[ok], ses[ok])
        return PoolFit(
            pooled, grand, tau, unclipped, bool(unclipped <= 0), basis, int(ok.sum())
        )

    if basis == "floor_clearing":
        unclipped = _moment_unclipped(factors[tau_cells], ses[tau_cells])
    else:  # dersimonian_laird
        w = 1 / ses[ok] ** 2
        fbar = float(np.sum(w * factors[ok]) / np.sum(w))
        q = float(np.sum(w * (factors[ok] - fbar) ** 2))
        c = float(np.sum(w) - np.sum(w**2) / np.sum(w))
        if not (np.isfinite(c) and c > 0):
            # One near-zero SE (a single-cluster bootstrap, se ~ 1e-16) carries
            # all the weight and c cancels to 0: DL is undefined, not zero.
            basis = "dersimonian_laird_undefined"
            pooled, grand = _shrink(factors, ses, ok, 0.0)
            return PoolFit(
                pooled, grand, 0.0, float("nan"), False, basis, int(ok.sum())
            )
        unclipped = (q - (int(ok.sum()) - 1)) / c
    tau2 = max(0.0, unclipped)
    pooled, grand = _shrink(factors, ses, ok, tau2)
    return PoolFit(
        pooled,
        grand,
        float(np.sqrt(tau2)),
        unclipped,
        bool(unclipped <= 0),
        basis,
        int(tau_cells.sum()),
    )


def repool_table(
    table: pd.DataFrame,
    *,
    pooler: str,
    min_pairs: int,
    tau_floor: int | None = None,
) -> pd.DataFrame:
    """Recompute every pooling-derived column of a factor table, block by block.

    ``factor_raw``, ``se`` and the bootstrap columns do not depend on the pooler
    and pass through untouched. ``reliable`` keeps its definition
    (``n_pairs >= min_pairs``, finite SE, not collapsed). ``tau_floor`` is the
    floor that decides which cells enter tau^2 (default: ``min_pairs``).
    """
    floor = min_pairs if tau_floor is None else tau_floor
    missing = {"factor_raw", "se", "n_pairs", *BLOCK_KEY} - set(table.columns)
    if missing:
        raise KeyError(f"factor table lacks {sorted(missing)}")
    if not table.index.is_unique:
        # blocks are written back by index label; a repeated label would
        # silently write one block's pooling into another's rows
        raise ValueError("factor table index must be unique")
    out = table.copy()
    out["tau2_unclipped"] = np.nan
    out["tau2_floored"] = False
    out["tau2_basis"] = pd.Series([None] * len(out), index=out.index, dtype=object)
    out["n_tau_cells"] = 0
    out["pooler"] = pooler
    # sort=False + the original index keeps each block's cells in the order
    # estimate_table produced them, so floating sums run in the same order.
    for _, idx in out.groupby(BLOCK_KEY, sort=False).groups.items():
        block = out.loc[idx]
        ses = block.se.to_numpy()
        fit = pool_block(
            block.factor_raw.to_numpy(),
            ses,
            block.n_pairs.to_numpy(),
            pooler=pooler,
            tau_floor=floor,
        )
        collapsed = blf.pooled_collapsed(fit.tau, ses)
        out.loc[idx, "factor"] = fit.pooled
        out.loc[idx, "tier_mean"] = fit.grand
        out.loc[idx, "tau"] = fit.tau
        out.loc[idx, "pooled_collapsed"] = collapsed
        out.loc[idx, "reliable"] = (
            (block.n_pairs.to_numpy() >= min_pairs) & np.isfinite(ses) & ~collapsed
        )
        out.loc[idx, "tau2_unclipped"] = fit.tau2_unclipped
        out.loc[idx, "tau2_floored"] = fit.tau2_floored
        out.loc[idx, "tau2_basis"] = fit.tau2_basis
        out.loc[idx, "n_tau_cells"] = fit.n_tau_cells
    for col in ("pooled_collapsed", "reliable", "tau2_floored"):
        out[col] = out[col].astype(bool)
    return out


def block_flags(table: pd.DataFrame) -> pd.DataFrame:
    """One row per block: tau, tau2_unclipped, tau2_floored, basis, cells."""
    cols = ["tau", "tier_mean", *FLAG_COLUMNS]
    return table.groupby(BLOCK_KEY, sort=False)[cols].first().reset_index()


@contextlib.contextmanager
def pooler_in_effect(
    pooler: str, *, tau_floor: int | None = None
) -> Iterator[dict[str, int]]:
    """Route every `blf.estimate_table` call through `repool_table(pooler)`.

    Yields a counter; callers assert ``counter["calls"] > 0`` afterwards so a
    patch that never reached the fit (wrong module object) cannot pass silently.
    Restores the original on exit, as `fit_factors` does for STATS/ERAS.
    """
    if pooler not in POOLERS:
        raise ValueError(f"unknown pooler {pooler!r}; choose from {POOLERS}")
    original = blf.estimate_table
    counter = {"calls": 0}

    def wrapped(pairs, *, samples, min_pairs, n_boot, seed):
        counter["calls"] += 1
        table = original(
            pairs, samples=samples, min_pairs=min_pairs, n_boot=n_boot, seed=seed
        )
        if table.empty:
            return table
        return repool_table(
            table, pooler=pooler, min_pairs=min_pairs, tau_floor=tau_floor
        )

    blf.estimate_table = wrapped
    try:
        yield counter
    finally:
        blf.estimate_table = original
