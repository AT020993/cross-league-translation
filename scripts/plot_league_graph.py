"""Study D — the league graph as a figure and a product.

Draws the weighted league graph the same-season pairs form (Proposition 4):
nodes are the twelve leagues that carry pairs, edge width is the number of
pairs between a domestic league and a continental competition, the node label
is the factor onto EuroLeague from the two-way fixed-effect fit (1/β for every
node, EuroCup included -- never the raw multiplier β). Beside it,
the implied domestic-to-domestic factor matrix with effective-resistance
standard errors -- factors for leagues that never meet, which no transfer-based
method can produce. Every number is read from ``propositions.json``
(`P4_identification`) and ``league_factor_pairs.parquet``; nothing is fitted
here.

    uv run python scripts/plot_league_graph.py --propositions P --pairs PAIRS --out-dir OUT
"""  # noqa: E501

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
_DEFAULT_PROPS = (
    REPO
    / "docs"
    / "research"
    / "artifacts"
    / "translation-propositions-2026-09-04"
    / "propositions.json"
)
_DEFAULT_PAIRS = (
    REPO / "data" / "processed" / "translation" / "league_factor_pairs.parquet"
)
_DEFAULT_OUT = REPO / "docs" / "plans" / "figures"
WELL_BRIDGED_SE = 0.02  # log scale
CONTINENTAL = ("euroleague", "eurocup")
CONTINENTAL_LABELS = {"euroleague": "EuroLeague", "eurocup": "EuroCup"}
#: marker areas in pt²; sqrt(area) is the disc diameter in pt and must exceed the
#: widest label ("EuroLeague" at 7.5 pt is ~44 pt wide) -- a test renders and checks
CONTINENTAL_NODE_SIZE = 2400
DOMESTIC_NODE_SIZE = 520
#: the pairs table under its private name, or the public export's name
PAIRS_FILENAMES = ("league_factor_pairs.parquet", "pairs.parquet")


def resolve_pairs_path(directory: Path) -> Path:
    """The pairs table in `directory`: the private name first, then the public
    export's `pairs.parquet`; the private name when neither exists, so the
    error names the canonical file."""
    for name in PAIRS_FILENAMES:
        if (directory / name).exists():
            return directory / name
    return directory / PAIRS_FILENAMES[0]


def implied_matrix(props: dict) -> pd.DataFrame:
    """from x to matrix of implied factors, with se_log and ci beside."""
    rows = props["P4_identification"]["implied_all_pairs"]
    return pd.DataFrame(rows)


def check_symmetry(m: pd.DataFrame, tol: float = 1e-9) -> float:
    """factor(a->b) * factor(b->a) == 1 for every pair (a consistency read)."""
    f = m.set_index(["from", "to"]).factor
    worst = 0.0
    for (a, b), v in f.items():
        worst = max(worst, abs(v * f[(b, a)] - 1.0))
    assert worst < tol, (
        f"implied factors are not reciprocal: max |f_ab f_ba - 1| = {worst}"
    )
    return worst


def edge_weights(pairs: pd.DataFrame) -> pd.DataFrame:
    return (
        pairs.groupby(["league_src", "league_dest"])
        .size()
        .rename("n_pairs")
        .reset_index()
    )


def graph_inputs(
    props: dict, pairs: pd.DataFrame
) -> tuple[pd.DataFrame, dict, pd.DataFrame, list[str]]:
    """Everything the graph panel reads: the implied matrix (checked for
    reciprocity), the two-way multipliers, the edge table, the domestic leagues
    ordered by multiplier."""
    m = implied_matrix(props)
    check_symmetry(m)
    beta = {
        r["league"]: r["rate_multiplier_vs_euroleague"]
        for r in props["P4_identification"]["twfe_beta_vs_euroleague"]
    }
    edges = edge_weights(pairs)
    domestic = sorted(
        {lg for lg in beta if lg not in CONTINENTAL}, key=lambda g: beta[g]
    )
    return m, beta, edges, domestic


def draw_graph_panel(a, props: dict, pairs: pd.DataFrame) -> dict:
    """Panel (a) on the given axes: the league graph. Domestic leagues on an
    arc, the two continental competitions in the middle, edge width = same-season
    pairs, node label = factor onto EuroLeague. The abstract v4's Figure 1 reuses
    this panel beside the shipped cells (``plot_sloan_abstract_figures``)."""
    m, beta, edges, domestic = graph_inputs(props, pairs)
    # layout: domestic leagues on an arc, the two bridges in the middle
    n = len(domestic)
    ang = np.linspace(np.pi * 0.04, np.pi * 0.96, n)
    pos = {lg: (2.7 * np.cos(t), 1.9 * np.sin(t) + 0.1) for lg, t in zip(domestic, ang)}
    pos["euroleague"] = (-0.75, -0.9)
    pos["eurocup"] = (0.75, -0.9)
    wmax = edges.n_pairs.max()
    for r in edges.itertuples():
        if r.league_src not in pos or r.league_dest not in pos:
            continue
        x0, y0 = pos[r.league_src]
        x1, y1 = pos[r.league_dest]
        col = "#4c78a8" if r.league_dest == "euroleague" else "#e45756"
        a.plot(
            [x0, x1],
            [y0, y1],
            color=col,
            alpha=0.55,
            lw=0.6 + 5.5 * r.n_pairs / wmax,
            zorder=1,
        )
    for lg, (x, y) in pos.items():
        cont = lg in CONTINENTAL
        a.scatter(
            [x],
            [y],
            s=CONTINENTAL_NODE_SIZE if cont else DOMESTIC_NODE_SIZE,
            color="#333" if cont else "white",
            edgecolor="#333",
            zorder=3,
            lw=1.2,
        )
        label = CONTINENTAL_LABELS.get(lg, lg.replace("-", " "))
        a.text(
            x,
            y,
            # every node, EuroCup included, carries its factor ONTO EuroLeague
            # (1/β); printing β for the continental nodes read as the inverse
            f"{label}\n→EL ×{1 / beta[lg]:.2f}",
            ha="center",
            va="center",
            fontsize=7.5,
            color="white" if cont else "#222",
            zorder=4,
        )
    a.set_xlim(-3.3, 3.3)
    a.set_ylim(-1.5, 2.5)
    a.axis("off")
    a.set_title(
        "(a) The league graph: domestic leagues are bridged only through\nthe two continental competitions. "  # noqa: E501
        "Edge width = same-season pairs;\nlabel = factor onto EuroLeague (two-way fit, Prop. 4)",  # noqa: E501
        loc="left",
        fontsize=9,
    )
    return {"pos": pos, "beta": beta, "edges": edges, "domestic": domestic, "matrix": m}


def draw(props: dict, pairs: pd.DataFrame, out: Path) -> dict:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, (a, b) = plt.subplots(
        1, 2, figsize=(14, 6.2), gridspec_kw={"width_ratios": [1, 1.15]}
    )
    g = draw_graph_panel(a, props, pairs)
    m, edges, domestic, pos = g["matrix"], g["edges"], g["domestic"], g["pos"]
    n = len(domestic)

    # (b) implied domestic-to-domestic matrix
    mat = m.pivot(index="from", columns="to", values="factor").reindex(
        index=domestic, columns=domestic
    )
    se = m.pivot(index="from", columns="to", values="se_log").reindex(
        index=domestic, columns=domestic
    )
    vals = mat.to_numpy(float)
    im = b.imshow(vals, cmap="RdBu_r", vmin=0.75, vmax=1.25, aspect="auto")
    b.set_xticks(range(n))
    b.set_xticklabels(
        [g.replace("-", " ") for g in domestic], rotation=45, ha="right", fontsize=8
    )
    b.set_yticks(range(n))
    b.set_yticklabels([g.replace("-", " ") for g in domestic], fontsize=8)
    b.set_xlabel("to")
    b.set_ylabel("from")
    well = 0
    for i in range(n):
        for j in range(n):
            if i == j:
                b.text(j, i, "—", ha="center", va="center", fontsize=8, color="#888")
                continue
            s = float(se.iloc[i, j])
            ok = s < WELL_BRIDGED_SE
            well += ok
            b.text(
                j,
                i,
                f"{vals[i, j]:.2f}",
                ha="center",
                va="center",
                fontsize=7.5,
                fontweight="bold" if ok else "normal",
                color="#111" if ok else "#666",
            )
    fig.colorbar(
        im,
        ax=b,
        fraction=0.04,
        pad=0.02,
        label="implied factor, from → to (per-36 EFF)",
    )
    b.set_title(
        f"(b) Implied factors between leagues that never meet (bold: R_eff SE < {WELL_BRIDGED_SE} on the log scale, "  # noqa: E501
        f"{well} of {n * (n - 1)})",
        loc="left",
        fontsize=9,
    )
    fig.tight_layout()
    fig.savefig(out, dpi=300, bbox_inches="tight")
    plt.close(fig)
    return {
        "n_leagues": len(pos),
        "n_domestic": n,
        "implied_contrasts": int(n * (n - 1)),
        "well_bridged": int(well),
        "well_bridged_se_log": WELL_BRIDGED_SE,
        "max_reciprocity_error": check_symmetry(m),
        "edges": edges.to_dict("records"),
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--propositions", type=Path, default=_DEFAULT_PROPS)
    ap.add_argument("--pairs", type=Path, default=_DEFAULT_PAIRS)
    ap.add_argument("--out-dir", type=Path, default=_DEFAULT_OUT)
    ap.add_argument("--summary-out", type=Path, default=None)
    args = ap.parse_args(argv)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    props = json.loads(args.propositions.read_text())
    pairs_path = (
        args.pairs if args.pairs.exists() else resolve_pairs_path(args.pairs.parent)
    )
    pairs = pd.read_parquet(pairs_path)
    out = args.out_dir / "sloan_fig3_league_graph.png"
    rb = draw(props, pairs, out)
    implied_matrix(props).to_csv(
        args.out_dir / "sloan_fig3_implied_factors.csv", index=False
    )
    summary = args.summary_out or (args.out_dir / "sloan_fig3_readback.json")
    summary.write_text(json.dumps(rb, indent=1, default=float))
    print(
        f"[D] {rb['well_bridged']} of {rb['implied_contrasts']} implied contrasts well bridged"  # noqa: E501
    )
    print(f"[done] wrote {out.name}, sloan_fig3_implied_factors.csv, {summary.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
