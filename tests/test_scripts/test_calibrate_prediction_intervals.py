"""Study C — interval families (ATI-2963).

What is pinned: the finite-sample conformal quantile, the Winkler score on a
hand case, honest ~95% coverage under exchangeable noise, both negative
controls firing, the tie rule keeping the simpler family, the confirmation fold
staying unread by default, and the normalised family earning its keep only
when the noise actually scales with the point.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

import scripts.calibrate_prediction_intervals as ci

pytestmark = pytest.mark.guard


def _rows(
    n_per_fold=600,
    seed=0,
    *,
    hetero=False,
    seasons=(2020, 2021, 2022, 2023, 2024, 2025),
):
    rng = np.random.default_rng(seed)
    frames = []
    for s in seasons:
        yhat = rng.uniform(6, 22, n_per_fold)
        sigma = 0.25 * yhat if hetero else 3.5
        frames.append(
            pd.DataFrame(
                {
                    "season": s,
                    "cluster": rng.choice([f"c{i}" for i in range(40)], n_per_fold),
                    "games_src": rng.integers(8, 34, n_per_fold),
                    "factor_reliable": rng.integers(0, 2, n_per_fold).astype(bool),
                    "per_league": yhat,
                    "y": yhat + rng.normal(0, sigma, n_per_fold),
                }
            )
        )
    return pd.concat(frames, ignore_index=True)


def test_conformal_quantile_uses_the_finite_sample_index():
    scores = np.arange(1, 101, dtype=float)  # 1..100
    # ceil(101 * 0.95) = 96 -> the 96th order statistic
    assert ci.conformal_quantile(scores, 0.05) == 96.0
    # too few points for the level -> infinite, never silently narrow
    assert ci.conformal_quantile(np.array([1.0, 2.0]), 0.05) == np.inf


def test_winkler_score_on_a_hand_case():
    y, lo, hi = np.array([5.0, 12.0]), np.array([0.0, 0.0]), np.array([10.0, 10.0])
    got = ci.winkler(y, lo, hi, alpha=0.05)
    assert got[0] == 10.0  # hit: width only
    assert got[1] == 10.0 + (2 / 0.05) * 2.0  # miss by 2 above


def test_rolling_conformal_covers_about_95_percent_out_of_sample():
    rows = _rows()
    per_row, metrics = ci.rolling(rows, ci.SELECTION_FOLDS, ("conformal",))
    cov = metrics.coverage.mean()
    assert abs(cov - 0.95) < 0.025, metrics


def test_both_negative_controls_fire():
    rows = _rows()
    nc = ci.negative_controls(rows, ci.SELECTION_FOLDS)
    assert nc["alpha_0.5_fails_band"]
    assert abs(nc["alpha_0.5_coverage"] - 0.5) < 0.05
    assert nc["leak_over_covers"]


def test_selection_keeps_the_simpler_family_on_a_tie_and_excludes_out_of_band():
    pooled = {
        "multiplier": {"coverage": 0.95, "winkler": 20.5, "winkler_se": 1.0},
        "conformal": {"coverage": 0.95, "winkler": 20.0, "winkler_se": 1.0},
        "normalised": {"coverage": 0.95, "winkler": 19.9, "winkler_se": 1.0},
        "cqr": {"coverage": 0.85, "winkler": 15.0, "winkler_se": 1.0},  # out of band
    }
    got = ci.select(pooled)
    assert got["selected"] == "multiplier"  # within one SE of the best, simpler
    assert "cqr" not in got["eligible"]
    pooled["conformal"]["winkler"] = 18.0
    assert ci.select(pooled)["selected"] == "conformal"


def test_the_confirmation_fold_is_not_read_unless_asked():
    rows = _rows(n_per_fold=200)
    s = ci.run(rows, confirm_2025=False)
    assert "confirmation_2025" not in s
    assert all(m["fold"] <= 2024 for m in s["per_fold"])
    s2 = ci.run(rows, confirm_2025=True)
    assert s2["confirmation_2025"]["per_family"][0]["fold"] == 2025


def test_the_normalised_family_wins_only_when_noise_scales_with_the_point():
    hom = _rows(seed=1)
    het = _rows(seed=1, hetero=True)
    _, m_hom = ci.rolling(hom, ci.SELECTION_FOLDS, ("conformal", "normalised"))
    _, m_het = ci.rolling(het, ci.SELECTION_FOLDS, ("conformal", "normalised"))
    w_hom = m_hom.groupby("family").winkler.mean()
    w_het = m_het.groupby("family").winkler.mean()
    assert w_het["normalised"] < w_het["conformal"] * 0.9, w_het
    assert abs(w_hom["normalised"] - w_hom["conformal"]) < 0.1 * w_hom["conformal"], (
        w_hom
    )


def test_lock_calibration_uses_every_fold_through_2025():
    rows = _rows(n_per_fold=100)
    params = ci.lock_calibration(rows, "conformal")
    assert params["calibration_folds"] == [2020, 2021, 2022, 2023, 2024, 2025]
    assert params["n_cal"] == 600
    assert np.isfinite(params["q_hat"])


def test_lock_calibration_can_stop_before_the_confirmation_fold_for_the_rehearsal():
    rows = _rows(n_per_fold=100)
    params = ci.lock_calibration(rows, "conformal", through=2024)
    assert params["calibration_folds"] == [2020, 2021, 2022, 2023, 2024]
    assert params["n_cal"] == 500


def test_the_confirmation_reading_is_read_off_the_fold_and_does_not_move_the_selection():  # noqa: E501
    c = {
        "selected_family": "conformal",
        "selected_family_read": {
            "family": "conformal",
            "coverage": 0.93,
            "winkler": 20.0,
        },
        "per_family": [
            {"family": "multiplier", "coverage": 0.93, "winkler": 21.0},
            {"family": "conformal", "coverage": 0.93, "winkler": 20.0},
            {"family": "cqr", "coverage": 0.94, "winkler": 19.5},
        ],
    }
    got = ci.confirmation_reading(c)
    assert "sits inside" in got and "beats the multiplier control by +1.00" in got
    assert "lowest 2025 Winkler is cqr's" in got and "does not move" in got
    c["selected_family_read"]["coverage"] = 0.85
    assert "falls outside" in ci.confirmation_reading(c)
