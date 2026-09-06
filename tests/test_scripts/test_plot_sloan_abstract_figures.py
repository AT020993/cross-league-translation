"""ATI-2955 — the ordering test the abstract quotes must be able to FAIL.

The 2026-08-17 holdout note reported rho = +0.688 from a session script whose
definition is unrecorded. ``scripts/plot_sloan_abstract_figures.py`` is the
committed generator; these tests pin (a) that it recovers a planted ordering,
(b) that its negative control rejects a null input, and (c) the key set of the
read-back JSON the abstract is written from, so a renamed field fails loudly
instead of silently emptying a sentence.
"""

from __future__ import annotations

import inspect

import numpy as np
import pandas as pd
import pytest

import scripts.plot_sloan_abstract_figures as fig

pytestmark = pytest.mark.guard


def _cells(rho_sign: float, seed: int = 0, n_cells: int = 16) -> pd.DataFrame:
    """Cells whose realised ratio tracks the factor (rho_sign=1) or not (0)."""
    rng = np.random.default_rng(seed)
    dest = np.array(["euroleague", "eurocup"] * (n_cells // 2))
    factor = rng.uniform(0.75, 1.05, n_cells)
    noise = rng.normal(0, 0.02, n_cells)
    realised = rho_sign * factor + (1 - rho_sign) * rng.uniform(0.75, 1.05, n_cells)
    return pd.DataFrame(
        {
            "league": [f"lg{i}" for i in range(n_cells)],
            "destination": dest,
            "factor": factor,
            "realised": realised + noise,
            "n": np.full(n_cells, fig.MIN_CELL_N + 3),
        }
    )


def test_ordering_test_recovers_a_planted_ordering() -> None:
    t = fig.ordering_test(_cells(1.0), n_perm=2000)
    assert t["rho"] > 0.8
    assert t["p_permutation"] < 0.01
    assert abs(t["null_mean"]) < fig.NULL_CENTRE_TOL
    assert set(t) >= {"rho", "p_permutation", "null_p95", "null_mean", "n_cells"}


def test_ordering_test_reports_nothing_on_a_null_input() -> None:
    """A gate that only ever passes is indistinguishable from one that never checks."""
    t = fig.ordering_test(_cells(0.0), n_perm=2000)
    assert t["p_permutation"] > 0.05


def test_negative_control_passes_on_real_shaped_cells_and_records_its_draws() -> None:
    neg = fig.ordering_negative_control(_cells(1.0), draws=8, n_perm=300)
    assert neg["mean_p_permutation"] >= fig.NEG_CONTROL_MIN_MEAN_P
    assert abs(neg["mean_rho"]) < 0.3
    assert neg["draws"] == 8


def test_negative_control_raises_when_the_test_cannot_reject(monkeypatch) -> None:
    """Mutation: an ordering_test that always reports p=0 must be caught."""

    def always_significant(cells, n_perm=0, seed=0):
        return {"rho": 0.9, "p_permutation": 0.0}

    monkeypatch.setattr(fig, "ordering_test", always_significant)
    with pytest.raises(AssertionError, match="cannot reject"):
        fig.ordering_negative_control(_cells(1.0), draws=3, n_perm=50)


def test_cells_below_the_floor_are_excluded() -> None:
    c = _cells(1.0)
    c.loc[:3, "n"] = fig.MIN_CELL_N - 1
    assert fig.ordering_test(c, n_perm=200)["n_cells"] == len(c) - 4


def test_readback_key_set_is_pinned() -> None:
    """The abstract is written off ``sloan_readback.json``; a renamed key fails here."""
    src = fig.__file__
    text = open(src).read()
    for key in (
        '"walkforward"',
        '"holdout"',
        '"ordering"',
        '"ordering_negative_control"',
        '"ordering_definition_sensitivity"',
        '"armA_g2"',
        '"armA_g4_b1b"',
        '"ladder_mae"',
        '"contrasts"',
        '"r2"',
        '"ceiling"',
        '"oracle"',
        '"design"',
    ):
        assert key in text, f"readback key {key} no longer emitted by {src}"


def test_fig1_r2_panel_reads_arms_in_ladder_order_and_the_ceiling_from_the_artifact():
    """Panel (b) must never carry a typed-in ceiling: both the per-arm R² and the
    ceiling come from `walkforward_summary.json`, and the R² order matches the
    ladder rows. Mutation: reorder `_LADDER_R2_KEYS` -- the per-league bar takes
    the global scalar's value and this test fails.
    """
    summary = {
        "pooled": {
            "mae_b0": 3.9,
            "mae_one_global": 3.3,
            "mae_per_league": 3.1,
            "r2": {
                "b0": -0.04,
                "one_global": 0.26,
                "per_league": 0.35,
                "rtm": 0.34,
                "rtm_plus_league": 0.40,
            },
            "ceiling": {
                "ceiling_r2_at_mean_games": 0.676,
                "split_half_r": 0.547,
                "mean_dest_games_scored": 17.8,
            },
        },
        "rtm_comparator": {"mae_rtm": 3.12, "mae_rtm_plus_league": 2.94},
    }
    ladder = fig.ladder_from_walkforward(summary, n_cells=20)
    r2, ceiling = fig.r2_from_walkforward(summary)
    assert len(r2) == len(ladder)
    assert list(r2) == [-0.04, 0.26, 0.35, 0.34, 0.40]
    assert ladder.predictor.iloc[2] == "20 per-league factors" and r2.iloc[2] == 0.35
    assert ceiling["ceiling_r2_at_mean_games"] == 0.676


def test_ladder_label_carries_no_typed_cell_count():
    """The cell count in the per-league label comes from `league_factors.parquet`
    via `shipped_cells`, never from a literal: the label said 22 for a 20-cell
    table for two days after poland-plk was refused. Mutation: hardcode the
    count in `ladder_from_walkforward` -- the no-count call fails here."""
    summary = {
        "pooled": {"mae_b0": 3.9, "mae_one_global": 3.3, "mae_per_league": 3.1},
        "rtm_comparator": {"mae_rtm": 3.12, "mae_rtm_plus_league": 2.94},
    }
    assert (
        fig.ladder_from_walkforward(summary).predictor.iloc[2] == "per-league factors"
    )
    assert (
        "22"
        not in open(fig.__file__)
        .read()
        .split("def ladder_from_walkforward")[1]
        .split("def ")[0]
    )
    factors = pd.DataFrame(
        {
            "league": ["a", "a", "b", "b", "a"],
            "destination": ["euroleague", "eurocup"] * 2 + ["euroleague"],
            "stat": ["pir"] * 4 + ["points"],
            "era": ["all"] * 5,
            "sample": ["all_pairs"] * 5,
            "factor": [0.8, 0.9, 0.85, 0.95, 0.7],
            "ci_lo": [0.7] * 5,
            "ci_hi": [1.0] * 5,
            "n_pairs": [100] * 5,
            "reliable": [True] * 5,
            "tier_mean": [0.85, 0.95, 0.85, 0.95, 0.8],
        }
    )
    cells = fig.shipped_cells(factors)
    assert len(cells) == 4 and set(cells.destination) == {"euroleague", "eurocup"}


def test_oracle_is_read_from_the_propositions_artifact():
    """The league-only bound on the R² panel comes from `propositions.json`
    (Amendment 11), never a typed constant. Mutation: return a literal 0.38 --
    the planted value below is not reproduced."""
    props = {
        "P1_league_information_bound": {
            "dest_units": {"oracle_league": {"r2": 0.4321, "mae": 2.5, "n": 674}}
        }
    }
    o = fig.oracle_from_propositions(props)
    assert o == {"r2": 0.4321, "mae": 2.5, "n": 674}
    src = open(fig.__file__).read()
    assert "0.38" not in src.split("def oracle_from_propositions")[1].split("def ")[0]


# ---- abstract v4 figures (2026-09-06): the panels the two figures are cut from ----


def _shipped_cells() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "league": ["a", "a", "b", "b"],
            "destination": ["euroleague", "eurocup"] * 2,
            "factor": [0.8, 0.9, 0.85, 0.95],
            "ci_lo": [0.7, 0.8, 0.75, 0.85],
            "ci_hi": [0.9, 1.0, 0.95, 1.05],
            "n_pairs": [100] * 4,
            "reliable": [True, True, True, False],
            "tier_mean": [0.85, 0.95] * 2,
        }
    )


def _graph_props_and_pairs() -> tuple[dict, pd.DataFrame]:
    props = {
        "P4_identification": {
            "twfe_beta_vs_euroleague": [
                {"league": "euroleague", "rate_multiplier_vs_euroleague": 1.0},
                {"league": "eurocup", "rate_multiplier_vs_euroleague": 1.13},
                {"league": "a", "rate_multiplier_vs_euroleague": 1.25},
                {"league": "b", "rate_multiplier_vs_euroleague": 1.1},
            ],
            "implied_all_pairs": [
                {"from": "a", "to": "b", "factor": 1.1, "se_log": 0.01},
                {"from": "b", "to": "a", "factor": 1 / 1.1, "se_log": 0.01},
            ],
        }
    }
    pairs = pd.DataFrame(
        {
            "league_src": ["a", "a", "b"],
            "league_dest": ["euroleague", "eurocup", "euroleague"],
        }
    )
    return props, pairs


def _walkforward_summary() -> dict:
    return {
        "pooled": {
            "mae_b0": 3.9,
            "mae_one_global": 3.3,
            "mae_per_league": 3.1,
            "delta_vs_b0": 0.8,
            "ci_b0": [0.6, 1.0],
            "delta_vs_global": 0.2,
            "ci": [0.13, 0.28],
        },
        "rtm_comparator": {
            "mae_rtm": 3.12,
            "mae_rtm_plus_league": 2.94,
            "per_league_vs_rtm": {"delta": 0.03, "ci": [-0.1, 0.15]},
            "rtm_plus_league_vs_rtm": {"delta": 0.17, "ci": [0.11, 0.24]},
            "rtm_plus_league_vs_per_league": {"delta": 0.14, "ci": [0.04, 0.25]},
        },
    }


@pytest.fixture
def ax():
    """One axes on the Agg backend, closed even when an assertion fails."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    figure, axes = plt.subplots()
    try:
        yield axes
    finally:
        plt.close(figure)


def test_cells_panel_title_counts_the_table_not_a_literal(ax) -> None:
    """The abstract's Figure 1(b) is this panel; the cell count AND the
    "EuroCup above EuroLeague for N of M leagues" claim are read from the table.
    Mutation: type "for every league" back into the title -- the second table,
    where league b's EuroCup cell is below its EuroLeague cell, fails."""
    fig.draw_cells_panel(ax, _shipped_cells())
    assert ax.get_title(loc="left").startswith("(b) The estimate: 4 cells")
    assert ax.get_title(loc="left").endswith("for 2 of 2 leagues")
    body = inspect.getsource(fig.draw_cells_panel)
    assert "every league" not in body and "20" not in body
    below = _shipped_cells()
    row = (below.league == "b") & (below.destination == "eurocup")
    below.loc[row, ["factor", "ci_lo", "ci_hi"]] = [0.5, 0.4, 0.6]
    assert fig.eurocup_above_euroleague(below) == (1, 2)
    ax.clear()
    fig.draw_cells_panel(ax, below)
    assert ax.get_title(loc="left").endswith("for 1 of 2 leagues")


def test_graph_panel_labels_every_node_with_its_factor_onto_euroleague(ax):
    """Figure 1(a) is `plot_league_graph.draw_graph_panel`: nodes are the leagues
    in `propositions.json` P4, ordered by their two-way multiplier, and EVERY node
    label -- EuroCup included -- is the factor ONTO EuroLeague (1/beta). The
    submission figure once printed EuroCup's raw multiplier (×1.13) under a legend
    saying "factor onto EuroLeague"; with beta 1.13 the label must read ×0.88.
    Mutation: label beta itself -- ×1.13 / ×1.25 appear and this fails."""
    from scripts.plot_league_graph import draw_graph_panel

    props, pairs = _graph_props_and_pairs()
    g = draw_graph_panel(ax, props, pairs)
    assert ax.get_title(loc="left").startswith("(a) The league graph")
    assert g["domestic"] == ["b", "a"]
    assert set(g["pos"]) == {"euroleague", "eurocup", "a", "b"}
    labels = [t.get_text() for t in ax.texts]
    assert any("→EL ×0.80" in s for s in labels), labels
    assert any(s == "EuroCup\n→EL ×0.88" for s in labels), labels
    assert any(s == "EuroLeague\n→EL ×1.00" for s in labels), labels
    assert not any("×1.13" in s or "×1.25" in s for s in labels), labels
    assert len(g["edges"]) == 3


def test_continental_labels_fit_inside_their_discs() -> None:
    """The white continental labels sit on dark discs, so any overflow is
    white-on-white and invisible to a text assertion. Render the panel at the
    abstract's figure size and check each label's ink is narrower than the disc
    chord at the first line's height. Mutation: CONTINENTAL_NODE_SIZE = 1500
    (the value that shipped "uroLeagu") -- fails."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    from scripts.plot_league_graph import (
        CONTINENTAL_LABELS,
        CONTINENTAL_NODE_SIZE,
        draw_graph_panel,
    )

    props, pairs = _graph_props_and_pairs()
    figure, (a, _b) = plt.subplots(
        1, 2, figsize=(14, 5.4), gridspec_kw={"width_ratios": [1.05, 1]}
    )
    try:
        draw_graph_panel(a, props, pairs)
        figure.canvas.draw()
        renderer = figure.canvas.get_renderer()
        px_per_pt = figure.dpi / 72
        radius = np.sqrt(CONTINENTAL_NODE_SIZE) / 2 * px_per_pt
        # the first text line is centred ~half a line above the disc centre
        # (two-line block); use the chord one line-height (7.5 pt) up, the worst case
        chord = 2 * np.sqrt(radius**2 - (7.5 * px_per_pt) ** 2)
        checked = 0
        for text in a.texts:
            if text.get_text().split("\n")[0] in CONTINENTAL_LABELS.values():
                width = text.get_window_extent(renderer).width
                assert width <= chord, (text.get_text(), width, chord)
                checked += 1
        assert checked == 2
    finally:
        plt.close(figure)


def test_abstract_figures_are_cut_by_main_from_the_same_inputs(tmp_path) -> None:
    """Both v4 figures are written by the committed generator from the inputs the
    manuscript figures use, under the names the draft cites (`ABSTRACT_FIG1/2`,
    pinned to the draft by tests/test_docs). `main()` must (a) call
    `draw_abstract_fig1` and write `ABSTRACT_FIG1`, and (b) write `ABSTRACT_FIG2`
    with the two-panel `draw_fig1` (no `r2=`; the ceiling and oracle are carried
    in the text). Mutation: delete either call from `main()`, or pass `r2=` to the
    fig-2 call -- fails. The names in the module docstring do not satisfy this."""
    props, pairs = _graph_props_and_pairs()
    f1 = tmp_path / fig.ABSTRACT_FIG1
    fig.draw_abstract_fig1(props, pairs, _shipped_cells(), f1)
    assert f1.stat().st_size > 0
    s = _walkforward_summary()
    f2 = tmp_path / fig.ABSTRACT_FIG2
    fig.draw_fig1(
        fig.ladder_from_walkforward(s, n_cells=4),
        fig.contrasts_from_walkforward(s),
        674,
        f2,
    )
    assert f2.stat().st_size > 0
    body = inspect.getsource(fig.main)
    assert "draw_abstract_fig1(" in body and "ABSTRACT_FIG1" in body
    fig2_call = body[body.rindex("draw_fig1(", 0, body.index("ABSTRACT_FIG2")) :]
    fig2_call = fig2_call[: fig2_call.index(")") + 1]
    assert "ABSTRACT_FIG2" in fig2_call and "r2=" not in fig2_call, fig2_call
