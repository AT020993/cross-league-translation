"""Research-only PIR/all factor fitting with legacy-compatible cluster draws.

Threats: optimization changes draws (slow-kernel equivalence tests); estimator
dispatch reuses primary intervals (each estimator has its own sufficient sums);
missing uncertainty looks reliable (explicit invalid counts and legacy floor).
No operating estimator defaults are mutated.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from scripts import build_league_factors as blf

ESTIMATORS = tuple(blf.ESTIMATORS)
TABLE_COLUMNS = [
    "league",
    "destination",
    "factor_raw",
    "factor",
    "se",
    "ci_lo",
    "ci_hi",
    "n_pairs",
    "n_clusters",
    "tier_mean",
    "tau",
    "reliable",
    "pooled_collapsed",
    "n_boot_valid",
    "n_boot_invalid",
    "era",
    "stat",
    "sample",
]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def stable_seed(seed: int, *key: object) -> int:
    return int.from_bytes(
        hashlib.sha256(json.dumps([seed, *key]).encode()).digest()[:8], "little"
    )


def bootstrap_draws(
    sub: pd.DataFrame, *, estimator: str, n_boot: int, seed: int
) -> np.ndarray:
    """Same ordered cluster selections as legacy, summed before resampling.

    Group order is first appearance, and the (B,G) integer array is exactly the
    stream of B legacy calls of size G. Summation reassociation can change last
    bits; tests compare the actual slow estimator on the identical selections.
    """
    if estimator not in ESTIMATORS:
        raise ValueError(f"Unknown estimator: {estimator}")
    if n_boot < 2:
        raise ValueError("n_boot must be at least 2")
    codes, clusters = pd.factorize(sub.cluster, sort=False)
    if (codes < 0).any():
        raise ValueError("Missing cluster identity")
    if len(clusters) < 2:
        return np.full(n_boot, np.nan)
    x = sub.pir_per36_src.to_numpy(dtype=float)
    y = sub.pir_per36_dest.to_numpy(dtype=float)
    ms, md = (
        sub.minutes_src.to_numpy(dtype=float),
        sub.minutes_dest.to_numpy(dtype=float),
    )
    if estimator == "ratio_of_sums":
        # pandas sum skips NaN in the legacy aggregate estimator.
        values = [
            np.nan_to_num(sub.pir_dest.to_numpy(dtype=float), nan=0),
            np.nan_to_num(md, nan=0),
            np.nan_to_num(sub.pir_src.to_numpy(dtype=float), nan=0),
            np.nan_to_num(ms, nan=0),
        ]
    else:
        ok = x > 0
        w = (
            np.minimum(ms, md)
            if estimator == "exposure_weighted"
            else np.ones(len(sub))
        )
        num = np.zeros(len(sub))
        num[ok] = w[ok] * y[ok] / x[ok]
        values = [num, np.where(ok, w, 0)]
    sums = np.column_stack(
        [np.bincount(codes, weights=v, minlength=len(clusters)) for v in values]
    )
    rng = np.random.default_rng(seed)
    result = np.empty(n_boot)
    # Bound memory even when users increase bootstrap depth substantially.
    for start in range(0, n_boot, 256):
        stop = min(start + 256, n_boot)
        picked = rng.integers(0, len(clusters), (stop - start, len(clusters)))
        totals = sums[picked].sum(axis=1)
        with np.errstate(divide="ignore", invalid="ignore"):
            if estimator == "ratio_of_sums":
                src_rate = totals[:, 2] / totals[:, 3]
                draws = np.where(
                    src_rate > 0, (totals[:, 0] / totals[:, 1]) / src_rate, np.nan
                )
            else:
                draws = totals[:, 0] / totals[:, 1]
        result[start:stop] = draws
    return result


def fit_table(
    pairs: pd.DataFrame,
    *,
    estimator: str = "exposure_weighted",
    n_boot: int = 2000,
    seed: int = 0,
) -> pd.DataFrame:
    """PIR/all/all_pairs, existing pooler and 75-pair floor, no global mutation."""
    if estimator not in ESTIMATORS:
        raise ValueError(f"Unknown estimator: {estimator}")
    if n_boot < 2:
        raise ValueError("n_boot must be at least 2")
    if pairs.empty:
        return pd.DataFrame(columns=TABLE_COLUMNS)
    pairs = pairs[pairs.season.between(2015, 2026)]
    blocks = []
    for dest in blf.CONTINENTAL:
        cells = []
        for source, sub in pairs[pairs.league_dest == dest].groupby("league_src"):
            draws = bootstrap_draws(
                sub,
                estimator=estimator,
                n_boot=n_boot,
                seed=blf.cell_seed(seed, "all_pairs", "all", dest, "pir", source),
            )
            finite = draws[np.isfinite(draws)]
            se = lo = hi = np.nan
            if len(finite) >= max(2, n_boot // 2):
                se = float(finite.std(ddof=1))
                lo, hi = np.percentile(finite, [2.5, 97.5])
            cells.append(
                dict(
                    league=source,
                    destination=dest,
                    factor_raw=blf.ESTIMATORS[estimator](sub, "pir"),
                    se=se,
                    ci_lo=lo,
                    ci_hi=hi,
                    n_pairs=len(sub),
                    n_clusters=sub.cluster.nunique(),
                    n_boot_valid=len(finite),
                    n_boot_invalid=n_boot - len(finite),
                    era="all",
                    stat="pir",
                    sample="all_pairs",
                )
            )
        if not cells:
            continue
        block = pd.DataFrame(cells)
        pooled, grand, tau = blf.partial_pool(
            block.factor_raw.to_numpy(), block.se.to_numpy()
        )
        block["factor"], block["tier_mean"], block["tau"] = pooled, grand, tau
        block["pooled_collapsed"] = blf.pooled_collapsed(tau, block.se.to_numpy())
        block["reliable"] = (
            (block.n_pairs >= 75) & np.isfinite(block.se) & ~block.pooled_collapsed
        )
        blocks.append(block)
    return (
        pd.concat(blocks, ignore_index=True)[TABLE_COLUMNS]
        if blocks
        else pd.DataFrame(columns=TABLE_COLUMNS)
    )
