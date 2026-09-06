"""The 2026-27 checkpoint evaluator (ATI-2891 acceptance criterion 4).

The criterion is that this runs end-to-end on synthetic or partial data BEFORE
tip-off, so the first real checkpoint is not also the first time it executes.
These tests are that dry run: every branch of the §11 verdict, including the
two that only fire when the model does badly.

METHOD.md §8's corollary is the reason the FAIL and PARTIAL branches get the
same attention as PASS — a gate that has only ever been seen to pass is
indistinguishable from one that never checks.

Source: scripts/evaluate_translation_predictions.py
"""

from __future__ import annotations

import pytest

from scripts.evaluate_translation_predictions import (
    B0_MARGIN,
    COVERAGE_BAND,
    beats_by_margin,
    interval_coverage,
    load_secondary,
    score_checkpoint,
    verdict,
)
from src.research.gates import assert_gate_rejects


def _gates(b0=True, b1b=True, b1c=True, coverage=True):
    return {
        "P1_beats_b0": b0,
        "P2_beats_b1b": b1b,
        "S1_beats_b1c": b1c,
        "S2_coverage_in_band": coverage,
    }


def test_both_primaries_met_is_a_pass():
    assert verdict(_gates()) == "PASS"


def test_missing_the_B0_primary_is_a_FAIL_whatever_else_passed():
    """§11: publishing projections from a model that does not beat untranslated
    production would be indefensible. The negative result is the output."""
    assert verdict(_gates(b0=False)) == "FAIL"
    assert verdict(_gates(b0=False, b1b=True, b1c=True)) == "FAIL"


def test_beating_B0_but_not_B1b_is_a_PARTIAL():
    """The branch Amendment 1 Change 1 added, and the one §7 says the 2026-27
    set will most often return: B1b has ~36% power at n=110, so a PARTIAL here
    is the season being too small to adjudicate, not the model failing."""
    assert verdict(_gates(b1b=False)) == "PARTIAL"


def test_a_secondary_miss_alone_does_not_move_the_verdict():
    """S1 and S2 are secondary by §8. Letting them decide would be moving a bar
    after the fact, in the direction of a worse verdict."""
    assert verdict(_gates(b1c=False)) == "PASS"
    assert verdict(_gates(coverage=False)) == "PASS"


def test_the_verdict_refuses_an_incomplete_gate_set():
    """A missing gate must not default. Defaulting a missing primary to True
    would publish a PASS nobody measured."""
    with pytest.raises(KeyError):
        verdict({"P1_beats_b0": True})


def test_the_margin_is_relative_to_the_baseline_not_absolute():
    """§8: "beat B0 by >=12.8% OF B0's MAE". An absolute 0.128 PIR/36 would be a
    far weaker bar at these error levels."""
    assert beats_by_margin(model_mae=3.0, baseline_mae=4.0, margin=B0_MARGIN)
    assert not beats_by_margin(model_mae=3.6, baseline_mae=4.0, margin=B0_MARGIN)
    # exactly on the bar passes; the bar is ">= 12.8% better"
    assert beats_by_margin(
        model_mae=4.0 * (1 - B0_MARGIN), baseline_mae=4.0, margin=B0_MARGIN
    )


def test_over_coverage_fails_the_band_just_as_under_coverage_does():
    """§6: an interval too wide is as uninformative as one too narrow, so both
    directions are failures. A one-sided check would let a model pass by
    publishing intervals wide enough to contain everything."""
    lo, hi = COVERAGE_BAND

    assert interval_coverage([(1.0, 0.0, 2.0)] * 100)["covered"] == 1.0
    assert not interval_coverage([(1.0, 0.0, 2.0)] * 100)["in_band"], (
        "100% coverage is OVER-coverage and must fail"
    )

    half = [(1.0, 0.0, 2.0)] * 50 + [(9.0, 0.0, 2.0)] * 50
    assert interval_coverage(half)["covered"] == 0.5
    assert not interval_coverage(half)["in_band"]

    inside = [(1.0, 0.0, 2.0)] * 95 + [(9.0, 0.0, 2.0)] * 5
    got = interval_coverage(inside)
    assert lo <= got["covered"] <= hi
    assert got["in_band"]


# ---------------------------------------------------------------------------
# ATI-2891 acceptance criterion 4: the evaluator must run end to end on
# synthetic data BEFORE tip-off, so the first real checkpoint is not also its
# first execution. All three verdict branches are exercised, not only PASS.
# ---------------------------------------------------------------------------


def _synthetic(n=60, *, outcome):
    """n predictions plus the outcomes `outcome(i, src, projection)` produces."""
    preds, outs = [], []
    for i in range(n):
        src = 10.0 + (i % 7)
        factor = 0.7 + 0.03 * (i % 5)
        projection = src * factor
        preds.append(
            {
                "person_code": f"p{i}",
                "projection": projection,
                "baseline_b0": src,
                "baseline_b1c": src * 0.85,
                "interval_low": projection * 0.4986,
                "interval_high": projection * 1.6392,
                # Amendment 6: every seventh row reaches back one season
                "source_season_lag": 1 if i % 7 == 0 else 0,
            }
        )
        outs.append(
            {
                "person_code": f"p{i}",
                "games": 20,
                "club_season": f"club{i % 10}-2026",
                "pir_per36": outcome(i, src, projection),
            }
        )
    return preds, {o["person_code"]: o for o in outs}


def test_the_evaluator_returns_PASS_when_the_model_is_right():
    preds, outs = _synthetic(outcome=lambda i, src, proj: proj + 0.05 * (-1) ** i)

    got = score_checkpoint(preds, outs, min_games=8)

    assert got["verdict"] == "PASS"
    assert got["n_scored"] == 60


def test_the_evaluator_returns_FAIL_when_translation_hurts():
    """Outcomes land on untranslated production, so the model is worse than B0
    and §11's FAIL branch fires. This is the branch that must be publishable."""
    preds, outs = _synthetic(outcome=lambda i, src, proj: src + 0.05 * (-1) ** i)

    got = score_checkpoint(preds, outs, min_games=8)

    assert got["verdict"] == "FAIL"
    assert not got["gates"]["P1_beats_b0"]


def test_the_evaluator_returns_PARTIAL_when_one_constant_does_the_same_job():
    """Every player translated by the SAME factor, so B1b -- one constant fitted
    to the scored set -- reproduces the model exactly. The B0 primary passes and
    the B1b primary ties, which is precisely the ATI-2799 G4 situation §7 says
    2026-27 will most often reproduce."""
    preds, outs = [], {}
    for i in range(60):
        src = 10.0 + (i % 7)
        projection = src * 0.8
        preds.append(
            {
                "person_code": f"p{i}",
                "projection": projection,
                "baseline_b0": src,
                "baseline_b1c": src * 0.85,
                "interval_low": projection * 0.4986,
                "interval_high": projection * 1.6392,
                # Amendment 6: every seventh row reaches back one season
                "source_season_lag": 1 if i % 7 == 0 else 0,
            }
        )
        outs[f"p{i}"] = {
            "person_code": f"p{i}",
            "games": 20,
            "club_season": f"club{i % 10}-2026",
            "pir_per36": projection + 0.05 * (-1) ** i,
        }

    got = score_checkpoint(preds, outs, min_games=8)

    assert got["gates"]["P1_beats_b0"], "the model still beats untranslated production"
    assert not got["gates"]["P2_beats_b1b"], "but one constant does the same job"
    assert got["verdict"] == "PARTIAL"


def test_players_below_the_games_floor_are_censored_and_counted():
    """§7's survivorship threat is only measurable if the unscored are reported
    beside the scored, so R8 is a count in the output, never a silent drop."""
    preds, outs = _synthetic(n=20, outcome=lambda i, src, proj: proj)
    for i in range(10):
        outs[f"p{i}"]["games"] = 3

    got = score_checkpoint(preds, outs, min_games=8)

    assert got["n_scored"] == 10
    assert got["n_censored_R8"] == 10


def test_a_fully_censored_checkpoint_refuses_rather_than_scoring_nobody():
    """A mid-season read before anyone has 8 games is not a FAIL."""
    preds, outs = _synthetic(n=10, outcome=lambda i, src, proj: proj)
    for o in outs.values():
        o["games"] = 1

    with pytest.raises(ValueError, match="censored read, not a result"):
        score_checkpoint(preds, outs, min_games=8)


def test_the_margin_gate_can_be_shown_to_reject():
    """METHOD.md §8 corollary, via the repo's own helper: a gate that only ever
    passes is indistinguishable from one that never checks."""

    def gate(model_mae=3.0, baseline_mae=4.0, margin=B0_MARGIN):
        if not beats_by_margin(
            model_mae=model_mae, baseline_mae=baseline_mae, margin=margin
        ):
            raise AssertionError(f"P1: {model_mae} does not beat {baseline_mae}")
        return True

    got = assert_gate_rejects(
        gate,
        (),
        [
            {"model_mae": 3.99},  # better than B0, but not by 12.8%
            {"model_mae": 4.50},  # worse than B0 outright
        ],
        label="P1_beats_b0",
    )

    assert got["rejects_bad"] == 2


def test_the_checkpoint_splits_mae_by_source_season_lag_without_gating_on_it():
    """Amendment 6 (ATI-2959 option 2): the lag split is a descriptive read.

    Lagged rows are scored, counted separately, and the verdict does not
    change when they miss badly; a row without the field is reported as
    `unknown`, never pooled into lag 0.
    """
    preds, outs = _synthetic(outcome=lambda i, src, proj: proj)
    lagged = [p["person_code"] for p in preds if p["source_season_lag"] > 0]
    for code in lagged:
        outs[code]["pir_per36"] += 30.0  # stale rows miss by a lot
    del preds[1]["source_season_lag"]
    got = score_checkpoint(preds, outs, min_games=8)
    split = got["by_source_season_lag"]
    assert split["lag_gt_0"]["n"] == len(lagged)
    assert split["unknown"]["n"] == 1
    total = split["lag_0"]["n"] + split["lag_gt_0"]["n"] + split["unknown"]["n"]
    assert total == got["n_scored"]
    assert split["lag_gt_0"]["model_mae"] > split["lag_0"]["model_mae"] + 20
    assert "by_source_season_lag" not in got["gates"]


def test_the_outcomes_loader_takes_both_the_bare_list_and_the_builder_payload():
    from scripts.evaluate_translation_predictions import load_outcomes

    rows = [{"person_code": "a", "games": 9}, {"person_code": "b", "games": 2}]
    assert load_outcomes(rows) == load_outcomes({"n": 2, "outcomes": rows})
    assert set(load_outcomes(rows)) == {"a", "b"}


def test_the_population_filter_restricts_predictions_not_the_censor_count():
    """Amendment 5's primary population is a filter on WHO WAS PREDICTED, read
    off the full-season outcomes; the as-of checkpoint's R8 censoring is
    unchanged by it, so a later arrival is dropped, not censored."""
    from scripts.evaluate_translation_predictions import restrict_population

    preds, outs = _synthetic(n=20, outcome=lambda i, src, proj: proj)
    full = {
        c: dict(o, first_round=1 if int(c[1:]) < 12 else 9) for c, o in outs.items()
    }
    full["p3"]["first_round"] = None  # never seen in the RS
    for i in range(10):
        outs[f"p{i}"]["games"] = 3  # as-of checkpoint: ten below the floor

    kept, info = restrict_population(preds, full, first_round_max=3)

    assert info["n_after"] == 11 and info["n_dropped_later_arrivals"] == 9
    assert {p["person_code"] for p in kept} == {f"p{i}" for i in range(12) if i != 3}
    before = score_checkpoint(preds, outs, min_games=8)
    after = score_checkpoint(kept, outs, min_games=8)
    # the nine dropped are all >= p12, so every censored player survives the filter
    assert after["n_censored_R8"] == 9 and before["n_censored_R8"] == 10
    assert after["n_scored"] == 2


# ---------------------------------------------------------------------------
# Amendment 10: the dynamic-ability arm is REPORTED beside the primary and can
# move nothing. Executable form of the amendment's "no bar moves" clause.
# ---------------------------------------------------------------------------


def test_the_secondary_arm_leaves_gates_and_verdict_byte_identical():
    """Same synthetic data with and without `secondary`: metrics gain a
    `dynamic` entry and two contrasts appear; gates and verdict are identical.

    Mutation: add `"dynamic"` to `_SECONDARY_GATES` handling (or gate on the
    dynamic contrast) -- the verdict dict changes and this test fails.
    """
    preds, outs = _synthetic(outcome=lambda i, src, proj: proj + (1 if i % 2 else -1))
    secondary = {p["person_code"]: p["projection"] * 0.97 for p in preds}
    without = score_checkpoint(preds, outs, 8)
    with_ = score_checkpoint(preds, outs, 8, secondary)
    assert with_["gates"] == without["gates"]
    assert with_["verdict"] == without["verdict"]
    assert set(with_["metrics"]) == set(without["metrics"]) | {"dynamic"}
    assert set(with_["contrasts"]) == set(without["contrasts"]) | {
        "dynamic",
        "dynamic_vs_B0",
    }
    for name in without["metrics"]:
        assert with_["metrics"][name] == without["metrics"][name]


def test_the_secondary_loader_refuses_an_incomplete_population():
    """Amendment 10 fixes the two populations as identical: a primary row with
    no secondary row is an error, never a silent drop."""
    preds, _ = _synthetic(n=10, outcome=lambda i, src, proj: proj)
    raw = {
        "predictions": [
            {"person_code": p["person_code"], "projection_dynamic": 1.0}
            for p in preds[:-1]
        ]
    }
    with pytest.raises(ValueError, match="Amendment 10"):
        load_secondary(raw, preds)
    full = {
        "predictions": [
            {"person_code": p["person_code"], "projection_dynamic": 1.0} for p in preds
        ]
    }
    assert len(load_secondary(full, preds)) == 10
