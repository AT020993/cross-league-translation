"""Synthetic tests for the four application studies
(``docs/research/translation-application-studies-preregistration-2026-09-06.md``).

Each test plants a known structure and checks the generator recovers it; each
was mutation-checked (the named mutation applied, the test confirmed red, the
mutation reverted).
"""

from __future__ import annotations

import json

import numpy as np
import pandas as pd
import pytest

import scripts.instantiate_translation_propositions as itp
import scripts.measure_pairing_vs_form as pvf
import scripts.plot_league_graph as plg
import scripts.rank_shortlist_double_count as rsd
import scripts.score_lifted_refusals as slr
import scripts.validate_translation_walkforward as wf


# ------------------------------------------------------------------ Study A --
def _pop(n_clusters=80, per=15, seed=0, form_shift=0.0, level_shift=1.0):
    rng = np.random.default_rng(seed)
    rows = []
    for c in range(n_clusters):
        for i in range(per):
            paired = int(i < per // 3)
            prior = 12 + rng.normal() + level_shift * paired
            dev = rng.normal() + form_shift * paired
            rows.append(
                {
                    "player_name": f"p{c}_{i}",
                    "season": 2020,
                    "league": "lg",
                    "club": f"c{c}",
                    "paired": paired,
                    "cluster": f"2020|lg|c{c}",
                    "prior_rate": prior,
                    "deviation": dev,
                }
            )
    return pd.DataFrame(rows)


def test_cohens_d_recovers_a_planted_standardised_difference():
    rng = np.random.default_rng(1)
    x = np.concatenate([rng.normal(0, 1, 20000), rng.normal(0.3, 1, 20000)])
    g = np.concatenate([np.zeros(20000), np.ones(20000)])
    assert pvf.cohens_d(x, g) == pytest.approx(0.3, abs=0.03)


def test_population_keeps_only_dual_competition_club_seasons():
    """A domestic player at a club with no paired player is not in the
    population. Mutation: drop the `dual` filter -- the lone club survives."""
    dom = pd.DataFrame(
        {
            "player_name": ["a", "b", "c"],
            "season": [2020, 2020, 2020],
            "league": ["lg", "lg", "lg"],
            "club": ["X", "X", "Y"],
            "games": [10, 10, 10],
            "minutes": [300, 300, 300],
            "pir": [100, 100, 100],
            "pir_per36": [12.0, 12.0, 12.0],
        }
    )
    cont = pd.DataFrame({"player_name": ["a"], "season": [2020]})
    pop = pvf.population(dom, cont)
    assert set(pop.player_name) == {"a", "b"}
    assert pop.set_index("player_name").paired.to_dict() == {"a": 1, "b": 0}


def test_form_null_reads_independent_and_level_reads_selected():
    """Plant no form shift and a one-SD level shift: the form read is
    'independent', the level d is large. Mutation: plant form_shift=0.6 --
    the read flips to 'selection on form measured'."""
    pop = _pop(form_shift=0.0, level_shift=1.0)
    pvf.N_BOOT, pvf.N_PERM = 200, 50
    arm = pvf.run_arm(pop, "synthetic")
    assert arm["form"]["read"].startswith("independent")
    assert arm["level"]["cohens_d"] > 0.6
    pop2 = _pop(form_shift=0.6)
    arm2 = pvf.run_arm(pop2, "synthetic-selected")
    assert arm2["form"]["read"].startswith("selection")
    assert arm2["form"]["share_of_null_draws_at_or_beyond"] < 0.05


# ------------------------------------------------------------------ Study B --
def _rows(seed=0, n=120, seasons=(2020, 2021)):
    rng = np.random.default_rng(seed)
    out = []
    for s in seasons:
        y = rng.normal(12, 5, n)
        # multiplier-only arm is y plus a career-year bump; combined removes it
        career = rng.random(n) < 0.4
        out.append(
            pd.DataFrame(
                {
                    "season": s,
                    "y": y,
                    "per_league": y + 4 * career + rng.normal(0, 1, n),
                    "rtm_plus_league": y + rng.normal(0, 1, n),
                    "one_global": y + 4 * career + rng.normal(0, 1.2, n),
                    "above_own_prior": career,
                }
            )
        )
    return pd.concat(out, ignore_index=True)


def test_top_k_stats_reads_the_planted_shortlist():
    df = pd.DataFrame(
        {
            "y": [1.0, 2.0, 3.0, 4.0, 5.0],
            "arm": [5.0, 4.0, 3.0, 2.0, 1.0],  # ranks the worst first
            "above_own_prior": [True, True, False, False, False],
        }
    )
    st = rsd.top_k_stats(df, "arm", 2)
    assert st["mean_realised"] == pytest.approx(1.5)
    assert st["career_year_share"] == 1.0
    assert st["overpaid"] == 1  # 2k = 4 covers ranks 0..3; y=1 is rank 4
    st3 = rsd.top_k_stats(df, "arm", 1)
    assert st3["overpaid"] == 1  # top-1 is y=1, realised rank 4 >= 2


def test_pooled_contrast_separates_a_planted_double_count():
    """The combined arm's top-10 realises more and carries fewer career-year
    players when the multiplier arm is inflated on career years. Mutation:
    swap PRIMARY's order -- the delta turns negative and the verdict fails."""
    rsd.N_BOOT, rsd.N_PERM = 100, 20
    rows = _rows()
    p = rsd.pooled_contrast(rows, "per_league", "rtm_plus_league", 10)
    assert p["pooled_delta_mean_realised_b_minus_a"] > 0
    assert p["pooled_ci95"][0] > 0
    assert p["pooled_career_year_share_a"] > p["pooled_career_year_share_b"]
    assert p["seasons_b_beats_a_on_mean_realised"] == 2


def test_fold_rows_carries_the_history_columns_additively():
    """Study B reads `prior_mean_pir36` and `above_own_prior` off the rows; the
    five arm columns are untouched. Mutation: drop the two columns from
    `fold_rows` -- this fails and Study B's assert fires."""
    test = pd.DataFrame(
        {
            "player_name": ["a", "b"],
            "league_src": ["x", "x"],
            "league_dest": ["euroleague", "eurocup"],
            "prior_mean_pir36": [10.0, np.nan],
            "above_own_prior": [True, False],
        }
    )
    fold = {
        "season": 2020,
        "test_rows": test,
        "table": pd.DataFrame(
            {"league": ["x"], "destination": ["euroleague"], "reliable": [True]}
        ),
        "clusters": np.array(["c1", "c2"]),
        "src": np.array([10.0, 12.0]),
        "y": np.array([9.0, 11.0]),
        "multiplier": np.array([0.9, 0.95]),
        "k_lag": 0.94,
        "global_scalar": 0.9,
    }
    rows = wf.fold_rows(fold)
    assert rows.prior_mean_pir36.iloc[0] == 10.0
    assert np.isnan(rows.prior_mean_pir36.iloc[1])
    assert list(rows.above_own_prior) == [True, False]
    assert np.allclose(rows.per_league, fold["src"] * fold["multiplier"] * 0.94)


# ------------------------------------------------------------------ Study C --
def test_lifting_rule_lifts_only_r9_and_r5_at_three_games():
    """Mutation: lift R5 at any game count -- the 2-game row becomes scorable."""
    assert slr.lifted_code("R9", 0) is None
    assert slr.lifted_code("R5", 3) is None
    assert slr.lifted_code("R5", 2) == "R5"
    assert slr.lifted_code("R5", None) == "R5"
    for code in ("R1", "R2", "R3", "R4", "R7"):
        assert slr.lifted_code(code, 30) == code
    assert slr.lifted_code(None, 30) is None


def test_two_sample_bootstrap_reads_a_planted_mae_gap():
    rng = np.random.default_rng(0)
    y_a = rng.normal(0, 1, 400)
    p_a = y_a + rng.normal(0, 1, 400)
    y_b = rng.normal(0, 1, 400)
    p_b = y_b + rng.normal(0, 3, 400)
    c_a = np.repeat(np.arange(40), 10)
    c_b = np.repeat(np.arange(40), 10)
    pt, lo, hi = slr.two_sample_cluster_bootstrap(
        y_a, p_a, c_a, y_b, p_b, c_b, n_boot=300
    )
    assert pt > 1.0 and lo > 0.5 and hi > pt


def test_score_group_censors_below_the_floor_and_reads_coverage():
    preds = [
        {
            "person_code": "1",
            "projection": 10.0,
            "baseline_b0": 12.0,
            "baseline_b1c": 11.0,
            "interval_low": 5.0,
            "interval_high": 15.0,
        },
        {
            "person_code": "2",
            "projection": 10.0,
            "baseline_b0": 12.0,
            "baseline_b1c": 11.0,
            "interval_low": 5.0,
            "interval_high": 15.0,
        },
    ]
    outcomes = {
        "1": {"games": 20, "pir_per36": 12.0, "club_season": "A-2025"},
        "2": {"games": 3, "pir_per36": 30.0, "club_season": "B-2025"},
    }
    g = slr.score_group(preds, outcomes, "t")
    assert g["n_scored"] == 1 and g["n_censored_R8"] == 1
    assert g["mae_model"] == pytest.approx(2.0)
    assert g["coverage"] == 1.0


# ------------------------------------------------------------------ Study D --
def _props_from_betas(betas: dict[str, float]) -> dict:
    leagues = list(betas)
    dom = [lg for lg in leagues if lg not in plg.CONTINENTAL]
    rows = []
    for a in dom:
        for b in dom:
            if a == b:
                continue
            lg = betas[b] - betas[a]
            rows.append(
                {
                    "from": a,
                    "to": b,
                    "factor": float(np.exp(lg)),
                    "se_log": 0.01 if a < b else 0.03,
                    "ci95": [float(np.exp(lg - 0.02)), float(np.exp(lg + 0.02))],
                    "effective_resistance": 0.5,
                    "direct_pairs": 0,
                }
            )
    return {
        "P4_identification": {
            "implied_all_pairs": rows,
            "twfe_beta_vs_euroleague": [
                {"league": lg, "rate_multiplier_vs_euroleague": float(np.exp(b))}
                for lg, b in betas.items()
            ],
        }
    }


def test_implied_matrix_is_reciprocal_and_symmetry_check_bites():
    props = _props_from_betas(
        {"euroleague": 0.0, "eurocup": 0.1, "spain-acb": 0.2, "italy-lba": 0.3}
    )
    m = plg.implied_matrix(props)
    assert plg.check_symmetry(m) < 1e-12
    m.loc[0, "factor"] *= 1.05
    with pytest.raises(AssertionError):
        plg.check_symmetry(m)


def test_draw_league_graph_writes_a_figure_and_counts_well_bridged(tmp_path):
    props = _props_from_betas(
        {
            "euroleague": 0.0,
            "eurocup": 0.1,
            "spain-acb": 0.2,
            "italy-lba": 0.3,
            "vtb": 0.25,
        }
    )
    pairs = pd.DataFrame(
        {
            "league_src": ["spain-acb", "italy-lba", "vtb", "vtb"],
            "league_dest": ["euroleague", "eurocup", "euroleague", "eurocup"],
        }
    )
    out = tmp_path / "g.png"
    rb = plg.draw(props, pairs, out)
    assert out.exists() and out.stat().st_size > 1000
    assert rb["implied_contrasts"] == 6
    assert rb["well_bridged"] == 3  # se_log 0.01 only where a < b


def test_effective_resistance_all_pairs_matches_named_moves_on_a_toy_graph():
    """`implied_all_pairs` is the same computation as the three named moves,
    on every pair: the effective-resistance SE for a named move must equal the
    matrix entry. Mutation: transpose the incidence -- the entries differ."""
    leagues = ["euroleague", "a", "b"]
    X = itp.league_incidence(["a", "b", "a"], ["euroleague"] * 3, leagues)
    w = np.array([1.0, 2.0, 1.0])
    r = itp.effective_resistance(X, w)
    assert r.shape == (3, 3)
    assert np.allclose(np.diag(r), 0)
    assert r[1, 2] == pytest.approx(r[1, 0] + r[0, 2])  # series path through EL


def test_propositions_artifact_keeps_the_named_moves_inside_all_pairs():
    """Real artifact, if present: the three named implied moves reproduce
    verbatim inside `implied_all_pairs` (the extension is additive)."""
    path = (
        itp.REPO
        / "docs"
        / "research"
        / "artifacts"
        / "translation-propositions-2026-09-04"
        / "propositions.json"
    )
    if not path.exists():
        pytest.skip("propositions artifact not present")
    p4 = json.loads(path.read_text())["P4_identification"]
    if "implied_all_pairs" not in p4:
        pytest.skip("artifact predates the all-pairs field")
    index = {(r["from"], r["to"]): r for r in p4["implied_all_pairs"]}
    for key, named in p4["implied_unobserved"].items():
        a, b = key.split("->")
        assert index[(a, b)]["factor"] == pytest.approx(named["factor"])
        assert index[(a, b)]["se_log"] == pytest.approx(named["se_log"])
