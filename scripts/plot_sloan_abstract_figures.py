#!/usr/bin/env python
"""Figures and read-back numbers for the SSAC27 abstract (ATI-2807).

Two figures, both generated from the committed validators' outputs so that every
number the abstract quotes has a generator in the repo (METHOD.md §16):

  fig 1  nested-predictor ladder from the six-window walk-forward
         (``scripts/validate_translation_walkforward.py``): untranslated ->
         one global scalar -> 22 per-league factors -> league-free RTM ->
         RTM + per-league, with the paired cluster-bootstrap contrasts.
  fig 2  does the per-league ORDERING survive out of sample? Fitted factor
         (fit <= 2023) against the realised 2024-25 transfer ratio per
         (source league, destination) cell, from the holdout validator's
         ``scored_switchers.parquet`` and ``factors_heldout_le2023.parquet``
         (``scripts/validate_translation_holdout.py``). The Spearman rho and
         its permutation p are computed HERE, because the 2026-08-17 holdout
         note reported them post-hoc from a session and no committed script
         produced them until this one.

Nothing here refits anything or moves a bar. It reads the validators' outputs
and draws them. Run both validators first (each accepts ``--out-dir``)::

    uv run python scripts/validate_translation_walkforward.py --out-dir OUT
    uv run python scripts/validate_translation_holdout.py    --out-dir OUT
    uv run python scripts/plot_sloan_abstract_figures.py --in-dir OUT \
        --out-dir docs/plans/figures

The script prints a ``[readback]`` block: the exact values the abstract text
should carry, so prose is read off this output and never off a note.

The abstract v4 (approved 2026-09-06) carries two figures cut from these panels:

  sloan_abstract_fig1_graph_cells.png  the league graph (Study D, panel (a) of
         ``plot_league_graph.py``, read from ``propositions.json`` P4) beside
         the 20 shipped cells (panel (b) of fig 0);
  sloan_abstract_fig2_ladder.png       the MAE ladder and its paired contrasts
         (panels (a) and (c) of fig 1); the R² panel's ceiling and oracle are
         carried in the text.

fig 0-3 stay generated: they are the manuscript's figures.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from scripts.plot_league_graph import draw_graph_panel, resolve_pairs_path  # noqa: E402

_DEFAULT_IN = REPO / "data" / "processed" / "translation"
_DEFAULT_OUT = REPO / "docs" / "plans" / "figures"
_DEFAULT_PROPOSITIONS = (
    REPO
    / "docs"
    / "research"
    / "artifacts"
    / "translation-propositions-2026-09-04"
    / "propositions.json"
)

#: the abstract v4's two figures (decision 2026-09-06), cited by these names in
#: docs/plans/sloan-ssac27-abstract-draft.md §Figures (pinned by tests/test_docs)
ABSTRACT_FIG1 = "sloan_abstract_fig1_graph_cells.png"
ABSTRACT_FIG2 = "sloan_abstract_fig2_ladder.png"

MIN_CELL_N = (
    5  # cells with fewer realised transfers are drawn hollow and excluded from rho
)
N_PERM = 10_000
SEED = 0


# ----------------------------------------------------------------- figure 1 --
#: the shipped factor table: one row per (source league, destination) for the
#: headline stat, all pairs, all eras -- the cells the walk-forward refits
_SHIPPED_TABLE = {"stat": "pir", "era": "all", "sample": "all_pairs"}


def shipped_cells(factors: pd.DataFrame) -> pd.DataFrame:
    """The 20-cell table (10 source leagues x 2 destinations) as shipped, read
    from `league_factors.parquet`; the cell COUNT in every label comes from
    here, never from a typed constant (the label said 22 for a 20-cell table
    for two days after poland-plk was refused)."""
    m = np.ones(len(factors), dtype=bool)
    for k, v in _SHIPPED_TABLE.items():
        m &= factors[k].to_numpy() == v
    cols = [
        "league",
        "destination",
        "factor",
        "ci_lo",
        "ci_hi",
        "n_pairs",
        "reliable",
        "tier_mean",
    ]
    return factors.loc[m, cols].reset_index(drop=True)


def ladder_from_walkforward(summary: dict, n_cells: int | None = None) -> pd.DataFrame:
    p, r = summary["pooled"], summary["rtm_comparator"]
    label = f"{n_cells} per-league factors" if n_cells else "per-league factors"
    rows = [
        ("untranslated (B0)", 0, p["mae_b0"]),
        ("one global scalar", 1, p["mae_one_global"]),
        (label, n_cells, p["mae_per_league"]),
        ("RTM, no league identity", None, r["mae_rtm"]),
        ("RTM + per-league", None, r["mae_rtm_plus_league"]),
    ]
    return pd.DataFrame(rows, columns=["predictor", "params", "mae"])


def contrasts_from_walkforward(summary: dict) -> pd.DataFrame:
    p, r = summary["pooled"], summary["rtm_comparator"]
    rows = [
        ("per-league vs B0", p["delta_vs_b0"], *p["ci_b0"]),
        ("per-league vs one global", p["delta_vs_global"], *p["ci"]),
        (
            "per-league vs RTM",
            r["per_league_vs_rtm"]["delta"],
            *r["per_league_vs_rtm"]["ci"],
        ),
        (
            "RTM + per-league vs RTM",
            r["rtm_plus_league_vs_rtm"]["delta"],
            *r["rtm_plus_league_vs_rtm"]["ci"],
        ),
        (
            "RTM + per-league vs per-league",
            r["rtm_plus_league_vs_per_league"]["delta"],
            *r["rtm_plus_league_vs_per_league"]["ci"],
        ),
    ]
    return pd.DataFrame(rows, columns=["contrast", "delta", "lo", "hi"])


#: arm key in `walkforward_summary.json: pooled.r2` for each ladder row, in order
_LADDER_R2_KEYS = ("b0", "one_global", "per_league", "rtm", "rtm_plus_league")
_LADDER_COLOURS = ["#9e9e9e", "#9e9e9e", "#4c78a8", "#9e9e9e", "#e45756"]


def r2_from_walkforward(summary: dict) -> tuple[pd.Series, dict]:
    """Out-of-sample R² per ladder arm and the reliability ceiling, both read from
    the artifact (`pooled.r2`, `pooled.ceiling`) -- never typed in."""
    r2 = pd.Series([summary["pooled"]["r2"][k] for k in _LADDER_R2_KEYS])
    return r2, summary["pooled"]["ceiling"]


def oracle_from_propositions(props: dict) -> dict:
    """The league-only oracle (Proposition 1): the in-sample least-squares cell
    multiplier on the scored rows, read from `propositions.json`
    (`P1_league_information_bound.dest_units.oracle_league`). It is a BOUND on
    every predictor of the form source x league multiplier, drawn hatched and
    never compared to an arm as if it were one (Amendment 11)."""
    o = props["P1_league_information_bound"]["dest_units"]["oracle_league"]
    return {"r2": float(o["r2"]), "mae": float(o["mae"]), "n": int(o["n"])}


def draw_fig1(
    ladder: pd.DataFrame,
    contrasts: pd.DataFrame,
    n_pooled: int,
    out: Path,
    r2: pd.Series | None = None,
    ceiling: dict | None = None,
    oracle: dict | None = None,
) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    three = r2 is not None and ceiling is not None
    if three:
        fig, (a, c, b) = plt.subplots(
            1, 3, figsize=(15, 4.2), gridspec_kw={"width_ratios": [1.1, 0.9, 1]}
        )
    else:
        fig, (a, b) = plt.subplots(
            1, 2, figsize=(11, 4.2), gridspec_kw={"width_ratios": [1.1, 1]}
        )
    y = np.arange(len(ladder))[::-1]
    a.barh(y, ladder["mae"], color=_LADDER_COLOURS)
    for yi, m in zip(y, ladder["mae"]):
        a.text(m + 0.03, yi, f"{m:.2f}", va="center", fontsize=9)
    a.set_yticks(y)
    a.set_yticklabels(ladder["predictor"])
    a.set_xlabel(f"MAE, realised EFF/36 (n = {n_pooled:,} transfers, 2020-25)")
    a.set_xlim(0, ladder["mae"].max() * 1.18)
    a.set_title("(a) What each predictor costs", loc="left", fontsize=10)

    y2 = np.arange(len(contrasts))[::-1]
    b.errorbar(
        contrasts["delta"],
        y2,
        xerr=[
            contrasts["delta"] - contrasts["lo"],
            contrasts["hi"] - contrasts["delta"],
        ],
        fmt="o",
        color="#333",
        capsize=3,
    )
    b.axvline(0, color="#999", lw=1)
    b.set_yticks(y2)
    b.set_yticklabels(contrasts["contrast"])
    b.set_xlabel("MAE saved (95% cluster-bootstrap CI)")
    b.set_title(
        f"({'c' if three else 'b'}) Which differences separate from zero",
        loc="left",
        fontsize=10,
    )
    if three:
        # (b): every R² against the ceiling the target's own reliability sets
        # (Propositions 2-3): a single-season rate at the scored rows' mean
        # exposure cannot be predicted beyond it by any model.
        ceil = float(ceiling["ceiling_r2_at_mean_games"])
        # negative R² is drawn as a negative bar, not clipped to a zero-length
        # bar labelled with a negative number
        c.barh(y, r2, color=_LADDER_COLOURS)
        for yi, v in zip(y, r2):
            c.text(max(v, 0) + 0.01, yi, f"{v:+.2f}", va="center", fontsize=9)
        if oracle is not None:
            # the league-only bound: hatched, above the arms, in-sample
            yo = y.max() + 1
            c.barh(
                yo,
                oracle["r2"],
                color="white",
                edgecolor="#4c78a8",
                hatch="////",
                lw=1.0,
            )
            c.text(
                oracle["r2"] + 0.01,
                yo,
                f"{oracle['r2']:+.2f} league-only oracle\n(in-sample bound, P1)",
                va="center",
                fontsize=8,
                color="#4c78a8",
            )
        c.axvline(ceil, color="#333", lw=1.2, ls="--")
        c.text(
            ceil - 0.01,
            y.max() + (1.55 if oracle is not None else 0.55),
            f"reliability ceiling {ceil:.2f}\n"
            f"(split-half r {ceiling['split_half_r']:.2f} at "
            f"{ceiling['mean_dest_games_scored']:.0f} games)",
            ha="right",
            va="bottom",
            fontsize=8,
            color="#333",
        )
        c.set_yticks(y)
        c.set_yticklabels([])
        c.set_xlim(min(0.0, float(r2.min()) - 0.05), min(1.0, ceil * 1.25))
        c.set_ylim(a.get_ylim()[0], y.max() + (2.3 if oracle is not None else 1.3))
        c.set_xlabel("out-of-sample R², same transfers")
        c.set_title(
            "(b) What share of the predictable variance", loc="left", fontsize=10
        )
    fig.tight_layout()
    fig.savefig(out, dpi=300, bbox_inches="tight")
    plt.close(fig)


# ----------------------------------------------------------------- figure 0 --
_DEST_COLOURS = {"euroleague": "#4c78a8", "eurocup": "#e45756"}
_DEST_LABELS = {"euroleague": "EuroLeague", "eurocup": "EuroCup"}


def draw_fig0(pairs: pd.DataFrame, cells: pd.DataFrame, out: Path) -> None:
    """The identification sample and the estimate in one frame: (a) the
    same-season dual-tier pairs, domestic per-36 EFF against continental per-36
    EFF, one point per player-season, coloured by destination competition, with
    the destination-tier mean multiplier drawn through the origin; (b) the 20
    shipped cells with cluster-bootstrap 95% CIs, EuroCup beside EuroLeague for
    every source league, hollow where the cell is below the reliability floor
    and served from the tier mean."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, (a, b) = plt.subplots(
        1, 2, figsize=(12.5, 4.6), gridspec_kw={"width_ratios": [1, 1.05]}
    )
    lim = float(np.nanpercentile(pairs[["pir_per36_src", "pir_per36_dest"]], 99.5))
    for dest, col in _DEST_COLOURS.items():
        d = pairs[pairs["league_dest"] == dest]
        a.scatter(
            d["pir_per36_src"],
            d["pir_per36_dest"],
            s=7,
            alpha=0.35,
            color=col,
            lw=0,
            label=f"{_DEST_LABELS[dest]} (n = {len(d):,})",
        )
    a.plot([0, lim], [0, lim], color="#999", lw=1, ls="--", label="1 : 1")
    for dest, col in _DEST_COLOURS.items():
        tm = cells.loc[cells["destination"] == dest, "tier_mean"]
        if len(tm):
            t = float(tm.iloc[0])
            a.plot([0, lim], [0, lim * t], color=col, lw=1.6)
            a.text(
                lim * 0.98,
                lim * t,
                f"tier mean ×{t:.2f}",
                color=col,
                fontsize=8,
                ha="right",
                va="bottom",
            )
    a.set_xlim(0, lim)
    a.set_ylim(0, lim)
    a.set_xlabel("domestic league, EFF per 36 (same season)")
    a.set_ylabel("continental competition, EFF per 36 (same season)")
    a.set_title(
        f"(a) The design: {len(pairs):,} player-seasons observed at two levels "
        "by schedule",
        loc="left",
        fontsize=10,
    )
    a.legend(loc="upper left", fontsize=8, frameon=False)

    draw_cells_panel(b, cells)
    fig.tight_layout()
    fig.savefig(out, dpi=300, bbox_inches="tight")
    plt.close(fig)


def eurocup_above_euroleague(cells: pd.DataFrame) -> tuple[int, int]:
    """(leagues whose EuroCup factor exceeds their EuroLeague factor, leagues):
    the count behind the abstract's "EuroCup is the easier destination for every
    league", read from the table by the panel title and the readback alike."""
    wide = cells.pivot(index="league", columns="destination", values="factor")
    return int((wide["eurocup"] > wide["euroleague"]).sum()), int(len(wide))


def draw_cells_panel(b, cells: pd.DataFrame) -> None:
    """Panel (b) on the given axes: the shipped cells with cluster-bootstrap
    95% CIs, EuroCup beside EuroLeague for every source league, hollow where the
    cell is below the reliability floor and served from the tier mean. The cell
    count in the title is read from the table, never typed."""
    order = (
        cells[cells["destination"] == "euroleague"]
        .sort_values("factor")["league"]
        .tolist()
    )
    ypos = {lg: i for i, lg in enumerate(order)}
    for dest, col in _DEST_COLOURS.items():
        d = cells[cells["destination"] == dest]
        off = -0.18 if dest == "euroleague" else 0.18
        for _, r in d.iterrows():
            yv = ypos[r["league"]] + off
            b.errorbar(
                r["factor"],
                yv,
                xerr=[[r["factor"] - r["ci_lo"]], [r["ci_hi"] - r["factor"]]],
                fmt="o",
                color=col,
                mfc=col if r["reliable"] else "white",
                capsize=2,
                ms=5,
                lw=1,
            )
        tm = d["tier_mean"]
        if len(tm):
            b.axvline(float(tm.iloc[0]), color=col, lw=0.8, ls=":")
    b.axvline(1.0, color="#999", lw=1)
    b.set_yticks(range(len(order)))
    b.set_yticklabels([lg.replace("-", " ") for lg in order])
    b.set_xlabel("factor: continental ÷ domestic per-36 EFF (95% cluster-bootstrap CI)")
    n_above, n_leagues = eurocup_above_euroleague(cells)
    b.set_title(
        f"(b) The estimate: {len(cells)} cells, EuroCup (red) above EuroLeague (blue) "
        f"for {n_above} of {n_leagues} leagues",
        loc="left",
        fontsize=10,
    )
    b.text(
        0.99,
        0.02,
        "hollow = below the reliability floor,\nserved from the tier mean (dotted)",
        transform=b.transAxes,
        ha="right",
        va="bottom",
        fontsize=7.5,
        color="#555",
    )


# ------------------------------------------------------ abstract figures (v4) --
def draw_abstract_fig1(
    props: dict, pairs: pd.DataFrame, cells: pd.DataFrame, out: Path
) -> None:
    """The abstract v4's Figure 1: the league graph (Study D; ``propositions.json``
    P4 via ``plot_league_graph.draw_graph_panel``) beside the 20 shipped cells.
    The identification and the estimate in one frame; fig 0's scatter is
    manuscript material."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, (a, b) = plt.subplots(
        1, 2, figsize=(14, 5.4), gridspec_kw={"width_ratios": [1.05, 1]}
    )
    draw_graph_panel(a, props, pairs)
    draw_cells_panel(b, cells)
    fig.tight_layout()
    fig.savefig(out, dpi=300, bbox_inches="tight")
    plt.close(fig)


# ----------------------------------------------------------------- figure 2 --
def ordering_cells(scored: pd.DataFrame, factors: pd.DataFrame) -> pd.DataFrame:
    """One row per (source league, destination): fitted factor vs realised ratio."""
    s = scored.rename(columns={"league_src": "league", "league_dest": "destination"})
    s["ratio"] = s["pir_per36_dest"] / s["pir_per36_src"]
    cells = (
        s.groupby(["league", "destination"])
        .agg(realised=("ratio", "mean"), n=("ratio", "size"))
        .reset_index()
    )
    f = factors[["league", "destination", "factor"]]
    return cells.merge(f, on=["league", "destination"], how="inner")


def within_destination_deviation(df: pd.DataFrame, col: str) -> pd.Series:
    return df[col] - df.groupby("destination")[col].transform("mean")


def ordering_sensitivity(scored: pd.DataFrame, factors: pd.DataFrame) -> dict:
    """rho under five definitions of the realised cell ratio (METHOD.md §3).

    The 2026-08-17 holdout note reported rho = +0.688 from a session script whose
    definition is unrecorded; none of these reproduces it exactly, so the point
    value is definition-dependent and the abstract quotes the primary
    (mean of per-player ratios) with this range beside it.
    """
    from scipy.stats import spearmanr

    s = scored.rename(columns={"league_src": "league", "league_dest": "destination"})
    s["ratio"] = s["pir_per36_dest"] / s["pir_per36_src"]
    g = s.groupby(["league", "destination"])
    defs = {
        "mean_of_ratios": g["ratio"].mean(),
        "median_ratio": g["ratio"].median(),
        "ratio_of_sums_pir": g["pir_dest"].sum() / g["pir_src"].sum(),
        "ratio_of_mean_per36": g["pir_per36_dest"].mean() / g["pir_per36_src"].mean(),
        "minutes_weighted": g.apply(
            lambda d: np.average(
                d["ratio"], weights=np.minimum(d["minutes_dest"], d["minutes_src"])
            )
        ),
    }
    n = g.size()
    out = {}
    for name, v in defs.items():
        c = (
            pd.DataFrame({"realised": v, "n": n})
            .reset_index()
            .merge(
                factors[["league", "destination", "factor"]],
                on=["league", "destination"],
            )
        )
        c = c[c["n"] >= MIN_CELL_N]
        rho, p = spearmanr(
            within_destination_deviation(c, "factor"),
            within_destination_deviation(c, "realised"),
        )
        out[name] = {
            "rho": float(rho),
            "p_asymptotic": float(p),
            "n_cells": int(len(c)),
        }
    return out


#: Negative control (METHOD.md §8 corollary): a gate must be shown to fail.
#: The null distribution of rho must be centred on zero to within this
#: tolerance (its SE at 10,000 draws over 16 cells is ~0.003), and the test
#: re-run on realised ratios that were permuted BEFORE it saw them must, on
#: average over ``NEG_CONTROL_DRAWS`` draws, report a permutation p that reads
#: as "nothing here" (expected 0.5).
NULL_CENTRE_TOL = 0.02
NEG_CONTROL_DRAWS = 20
NEG_CONTROL_MIN_MEAN_P = 0.2


def _permute_within_destination(
    c: pd.DataFrame, rng: np.random.Generator
) -> np.ndarray:
    # permute realised ratios WITHIN destination, so the EuroLeague/EuroCup
    # tier gap cannot carry the test
    yp = c["realised"].to_numpy().copy()
    for dest in c["destination"].unique():
        idx = np.flatnonzero(c["destination"].to_numpy() == dest)
        yp[idx] = rng.permutation(yp[idx])
    return yp


def ordering_test(cells: pd.DataFrame, n_perm: int = N_PERM, seed: int = SEED) -> dict:
    from scipy.stats import spearmanr

    c = cells[cells["n"] >= MIN_CELL_N].copy()
    x = within_destination_deviation(c, "factor").to_numpy()
    y = within_destination_deviation(c, "realised").to_numpy()
    rho, p_asym = spearmanr(x, y)
    rng = np.random.default_rng(seed)
    null = np.empty(n_perm)
    for i in range(n_perm):
        cp = c.assign(realised=_permute_within_destination(c, rng))
        null[i] = spearmanr(x, within_destination_deviation(cp, "realised").to_numpy())[
            0
        ]
    p_perm = float((null >= rho).mean())
    return {
        "n_cells": int(len(c)),
        "rho": float(rho),
        "p_asymptotic": float(p_asym),
        "p_permutation": p_perm,
        "null_p95": float(np.percentile(null, 95)),
        "null_mean": float(null.mean()),
        "n_perm": n_perm,
    }


def ordering_negative_control(
    cells: pd.DataFrame,
    *,
    draws: int = NEG_CONTROL_DRAWS,
    n_perm: int = 500,
    seed: int = SEED + 1,
) -> dict:
    """Run ``ordering_test`` on realised ratios it should find NOTHING in.

    Two assertions, both of which a test that "only ever passes" would fail:
    the null is centred on zero, and the same test handed pre-permuted
    outcomes reports, on average, no ordering. Raises — the run fails rather
    than reports — because a positive result from a gate that cannot reject is
    not a result (METHOD.md §8).
    """
    c = cells[cells["n"] >= MIN_CELL_N].copy()
    rng = np.random.default_rng(seed)
    rhos, ps = [], []
    for i in range(draws):
        shuffled = c.assign(realised=_permute_within_destination(c, rng))
        t = ordering_test(shuffled, n_perm=n_perm, seed=seed + 100 + i)
        rhos.append(t["rho"])
        ps.append(t["p_permutation"])
    out = {
        "draws": draws,
        "n_perm_per_draw": n_perm,
        "mean_rho": float(np.mean(rhos)),
        "mean_p_permutation": float(np.mean(ps)),
        "share_significant_at_0_05": float(np.mean(np.asarray(ps) < 0.05)),
    }
    assert out["mean_p_permutation"] >= NEG_CONTROL_MIN_MEAN_P, (
        f"ordering test reports an ordering in pre-permuted outcomes "
        f"(mean p={out['mean_p_permutation']:.3f}) — the gate cannot reject"
    )
    return out


def draw_fig2(cells: pd.DataFrame, test: dict, out: Path) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(5.6, 4.6))
    for dest, colour in (("euroleague", "#4c78a8"), ("eurocup", "#e45756")):
        d = cells[cells["destination"] == dest]
        big, small = d[d["n"] >= MIN_CELL_N], d[d["n"] < MIN_CELL_N]
        ax.scatter(
            big["factor"],
            big["realised"],
            s=20 + 3 * big["n"],
            color=colour,
            label=f"→ {dest}",
        )
        ax.scatter(
            small["factor"],
            small["realised"],
            s=25,
            facecolors="none",
            edgecolors=colour,
        )
        for _, r in big.iterrows():
            ax.annotate(
                r["league"].replace("-", " "),
                (r["factor"], r["realised"]),
                fontsize=7,
                xytext=(3, 3),
                textcoords="offset points",
            )
    lo = min(cells["factor"].min(), cells["realised"].min()) - 0.03
    hi = max(cells["factor"].max(), cells["realised"].max()) + 0.03
    ax.plot([lo, hi], [lo, hi], color="#bbb", lw=1, ls="--")
    ax.set_xlabel("fitted factor (same-season pairs, seasons ≤ 2023)")
    ax.set_ylabel("realised transfer ratio, 2024-25 (mean per cell)")
    ax.set_title(
        f"Ordering survives out of sample: ρ = {test['rho']:+.2f} within destination, "
        f"permutation p = {test['p_permutation']:.4f} "
        f"({test['n_cells']} cells, n ≥ {MIN_CELL_N})",
        fontsize=9,
        loc="left",
    )
    ax.legend(fontsize=8, loc="upper left")
    fig.tight_layout()
    fig.savefig(out, dpi=300, bbox_inches="tight")
    plt.close(fig)


# --------------------------------------------------------------------- main --
def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument(
        "--in-dir",
        type=Path,
        default=_DEFAULT_IN,
        help="where both validators wrote their outputs",
    )
    ap.add_argument("--out-dir", type=Path, default=_DEFAULT_OUT)
    ap.add_argument("--n-perm", type=int, default=N_PERM)
    ap.add_argument(
        "--propositions",
        type=Path,
        default=_DEFAULT_PROPOSITIONS,
        help="propositions.json (Amendment 11); the oracle bound is read from it",
    )
    args = ap.parse_args(argv)
    args.out_dir.mkdir(parents=True, exist_ok=True)

    wf = json.loads((args.in_dir / "walkforward_summary.json").read_text())
    ho = json.loads((args.in_dir / "validation_summary.json").read_text())
    scored = pd.read_parquet(args.in_dir / "scored_switchers.parquet")
    factors = pd.read_parquet(args.in_dir / "factors_heldout_le2023.parquet")
    shipped = shipped_cells(pd.read_parquet(args.in_dir / "league_factors.parquet"))
    pairs = pd.read_parquet(resolve_pairs_path(args.in_dir))
    props = json.loads(args.propositions.read_text())
    oracle = oracle_from_propositions(props)
    assert oracle["n"] == wf["n_pooled"], (oracle["n"], wf["n_pooled"])

    draw_fig0(pairs, shipped, args.out_dir / "sloan_fig0_design.png")
    shipped.to_csv(args.out_dir / "sloan_fig0_cells.csv", index=False)

    ladder = ladder_from_walkforward(wf, n_cells=len(shipped))
    contrasts = contrasts_from_walkforward(wf)
    r2, ceiling = r2_from_walkforward(wf)
    draw_fig1(
        ladder,
        contrasts,
        wf["n_pooled"],
        args.out_dir / "sloan_fig1_walkforward_ladder.png",
        r2=r2,
        ceiling=ceiling,
        oracle=oracle,
    )

    # the abstract v4's two figures (decision 2026-09-06): graph beside cells,
    # and the ladder with its contrasts -- the R² panel is carried in the text
    draw_abstract_fig1(props, pairs, shipped, args.out_dir / ABSTRACT_FIG1)
    draw_fig1(ladder, contrasts, wf["n_pooled"], args.out_dir / ABSTRACT_FIG2)

    cells = ordering_cells(scored, factors)
    test = ordering_test(cells, n_perm=args.n_perm)
    assert abs(test["null_mean"]) < NULL_CENTRE_TOL, (
        f"permutation null is not centred on zero (mean {test['null_mean']:+.4f})"
    )
    neg = ordering_negative_control(cells)
    print(
        f"[ordering] rho={test['rho']:+.4f} p_perm={test['p_permutation']:.4f} "
        f"null_mean={test['null_mean']:+.4f} | negative control: mean rho="
        f"{neg['mean_rho']:+.4f} mean p={neg['mean_p_permutation']:.3f} "
        f"sig@0.05={neg['share_significant_at_0_05']:.2f}"
    )
    draw_fig2(cells, test, args.out_dir / "sloan_fig2_ordering.png")
    cells.to_csv(args.out_dir / "sloan_fig2_cells.csv", index=False)

    a = ho["armA"]
    rb = {
        # corpus size is printed by the validators' own [corpus] line, not here
        "walkforward": {
            "n_pooled": wf["n_pooled"],
            "n_clusters": wf["n_clusters"],
            "seasons_per_league_wins": wf["seasons_per_league_wins"],
            "seasons_separable": wf["seasons_separable"],
            "ladder_mae": ladder.set_index("predictor")["mae"].round(4).to_dict(),
            "r2": dict(zip(_LADDER_R2_KEYS, [round(float(v), 4) for v in r2])),
            "ceiling": ceiling,
            "oracle": oracle,
            "contrasts": contrasts.round(4).to_dict("records"),
            "shuffle_reps_beating_real": wf["control_shuffle"]["reps_beating_real"],
            "combined_shuffle_reps_reaching_real": wf["control_combined_shuffle"][
                "reps_reaching_real"
            ],
        },
        "holdout": {
            "verdict": ho["verdict"],
            "gates": ho["gates"],
            "armA_n": ho["population"]["scored_armA"],
            "armB_n": ho["population"]["scored_armB"],
            "armA_metrics": a,
            "armA_g2": ho["armA_g2"],
            # ATI-2955 item 3: the G4 tie's interval, from the validator
            "armA_g4_b1b": ho.get("armA_g4_b1b"),
            "armB_pooled": ho["armB_pooled"],
            "reliability": ho["reliability"],
            "resid_sd": ho["resid_sd"],
            "k_b1b": ho["k_b1b"],
        },
        "ordering": test,
        "ordering_negative_control": neg,
        "ordering_definition_sensitivity": ordering_sensitivity(scored, factors),
    }
    (args.out_dir / "sloan_readback.json").write_text(
        json.dumps(rb, indent=1, default=float)
    )
    print("[readback]", json.dumps(rb, indent=1, default=float))
    rb["design"] = {
        "n_pairs": int(len(pairs)),
        "n_cells": int(len(shipped)),
        "n_reliable": int(shipped["reliable"].sum()),
        "eurocup_above_euroleague": eurocup_above_euroleague(shipped)[0],
    }
    (args.out_dir / "sloan_readback.json").write_text(
        json.dumps(rb, indent=1, default=float)
    )
    print(
        "[done] wrote sloan_fig0_design.png sloan_fig1_walkforward_ladder.png "
        f"sloan_fig2_ordering.png {ABSTRACT_FIG1} {ABSTRACT_FIG2} "
        f"sloan_readback.json to {args.out_dir}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
