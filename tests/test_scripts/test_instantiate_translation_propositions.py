"""Tests for ``scripts/instantiate_translation_propositions.py`` on synthetic data.

The script instantiates five propositions on the corpus. These tests do not
touch the corpus: each proposition is an inequality or identity that must hold
on ANY data satisfying its premise, so each is checked on a small synthetic
dataset built to satisfy that premise — and, where the proposition is an
inequality, on a perturbation that must sit on the wrong side of it.

Each test drives the real functions and names the mutation that breaks it.
Every mutation below was applied to the script, confirmed to fail, and
reverted (the list is in the PR description).
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

import scripts.instantiate_translation_propositions as itp

pytestmark = pytest.mark.guard


def _cells(rng: np.random.Generator, n: int) -> np.ndarray:
    return rng.choice(["a\u2192EL", "b\u2192EL", "a\u2192EC", "c\u2192EC"], n)


# --------------------------------------------------------------------------- P1
def test_oracle_cell_multiplier_minimises_in_sample_mse_against_perturbations():
    """P1 in destination units: ``m_c = sum(s y)/sum(s^2)`` is the exact oracle.

    Any other cell multiplier — every cell nudged up, every cell nudged down, or
    a random re-scaling — must give a strictly larger in-sample MSE. Mutation:
    replace the numerator with ``sum(y)`` (a mean-of-y multiplier) — the oracle
    then loses to the nudged variants and the test fails.
    """
    rng = np.random.default_rng(1)
    n = 400
    cells = _cells(rng, n)
    src = rng.uniform(5, 25, n)
    true_m = pd.Series(
        {"a\u2192EL": 0.8, "b\u2192EL": 0.9, "a\u2192EC": 1.0, "c\u2192EC": 0.85}
    )
    y = src * true_m.loc[cells].to_numpy() + rng.normal(0, 3, n)

    m_or = itp.oracle_cell_multipliers(src, y, cells)
    base = itp.mse(y, src * m_or.loc[cells].to_numpy())
    for factor in (0.97, 1.03):
        assert itp.mse(y, src * (m_or * factor).loc[cells].to_numpy()) > base
    jitter = m_or * (1 + rng.normal(0, 0.05, len(m_or)))
    assert itp.mse(y, src * jitter.loc[cells].to_numpy()) > base
    # and the oracle is at least as good as the true generating multipliers
    assert base <= itp.mse(y, src * true_m.loc[cells].to_numpy())


def test_eta_squared_times_variance_is_the_between_cell_variance():
    """``eta2_raw * Var(R)`` must equal ``Var(E[R|L])`` — the P1 bound itself.

    Mutation: divide the between-cell sum of squares by ``n - 1`` instead of
    using the population total — the identity then fails at the 1e-9 level.
    """
    rng = np.random.default_rng(2)
    n = 300
    cells = _cells(rng, n)
    r = (
        rng.normal(0.85, 0.2, n)
        + pd.Series(cells)
        .map({"a\u2192EL": -0.1, "b\u2192EL": 0.0, "a\u2192EC": 0.1, "c\u2192EC": 0.05})
        .to_numpy()
    )
    e = itp.eta_squared(r, cells)
    cond_mean = pd.Series(r).groupby(cells).transform("mean").to_numpy()
    assert e["eta2_raw"] * np.var(r) == pytest.approx(np.var(cond_mean), abs=1e-9)
    assert 0 <= e["eta2_adj"] <= e["eta2_raw"]
    assert e["groups"] == 4 and e["n"] == n


# --------------------------------------------------------------------------- P2
def test_corr_squared_never_exceeds_reliability_under_y_equals_t_plus_e():
    """P2: for ``Y = T + e`` with ``E[e|X] = 0``, ``Corr(f(X), Y)^2 <= Var(T)/Var(Y)``.

    The premise is made to hold EXACTLY in the sample: the noise is
    orthogonalised against every predictor input (a constant, ``T`` and the
    extra noise the "noisy" arm uses), so ``Cov(f, e) = 0`` for each arm and the
    inequality must hold without any sampling slack. The bound is checked for
    the best possible predictor (``f = T`` itself), a noisy one and a
    badly-scaled one. Mutation: report ``corr_y`` instead of ``corr_y**2`` in
    ``corr2_y`` — ``f = T`` then exceeds the ceiling.
    """
    rng = np.random.default_rng(3)
    n = 20_000
    t = rng.normal(10, 3, n)
    extra = rng.normal(0, 4, n)
    e = rng.normal(0, 2, n)
    design = np.column_stack([np.ones(n), t, extra])
    e = e - design @ np.linalg.lstsq(design, e, rcond=None)[0]  # E[e | X] = 0
    y = t + e
    reliability = float(np.var(t) / np.var(y))
    arms = {
        "perfect": t,
        "noisy": t + extra,
        "scaled": 3 * t - 7,
    }
    out = itp.reliability_ceiling_check(y, arms, reliability)
    for name, v in out.items():
        assert v["corr2_y"] <= reliability * (1 + 1e-12), name
        assert v["share_of_ceiling"] <= 1.0 + 1e-12, name
    # the perfect predictor sits exactly AT the ceiling; the others below it
    assert out["perfect"]["corr2_y"] == pytest.approx(reliability, rel=1e-9)
    assert out["perfect"]["disattenuated"] == pytest.approx(1.0, rel=1e-9)
    assert out["noisy"]["corr2_y"] < reliability
    assert out["scaled"]["corr2_y"] == pytest.approx(reliability, rel=1e-9)


# --------------------------------------------------------------------------- P3
def test_spearman_brown_inversion_round_trips():
    """``games_needed(r1, spearman_brown(r1, n)) == n`` for every r1 and n.

    Mutation: swap ``(1 - r1)`` and ``(1 - target)`` in ``games_needed`` — the
    round trip then fails for every n except the fixed point n = 1.
    """
    for r1 in (0.05, 0.105, 0.3, 0.7):
        for n in (1, 2, 5, 17.8, 40, 100):
            rho = itp.spearman_brown(r1, n)
            assert itp.games_needed(r1, rho) == pytest.approx(n, rel=1e-10)
    # monotone: a higher target always needs more games
    needs = [itp.games_needed(0.105, t) for t in itp.RELIABILITY_TARGETS]
    assert needs == sorted(needs) and needs[0] < needs[-1]


# --------------------------------------------------------------------------- P4
def test_laplacian_rank_is_leagues_minus_components():
    """P4(ii): rank ``X^T W X`` = #leagues − #connected components.

    A connected toy (three domestic leagues each paired with EL) has rank 3
    on 4 nodes; removing the bridge leaves 4 isolated nodes and rank 0; a
    two-component toy (two bridges, no cross edges) has rank 4 on 6 nodes.
    Mutation: put +1 on BOTH source and destination in the incidence matrix —
    the Laplacian becomes full rank on the connected toy and the test fails.
    """
    leagues = ["EL", "a", "b", "c"]
    src = ["a", "b", "c", "a", "b"]
    dest = ["EL", "EL", "EL", "EL", "EL"]
    X = itp.league_incidence(src, dest, leagues)
    w = np.array([100.0, 50.0, 80.0, 20.0, 10.0])
    rank, fiedler = itp.laplacian_rank(X, w)
    assert rank == len(leagues) - 1
    assert fiedler > 0
    # every row of the incidence matrix sums to zero: the all-ones vector is
    # always in the null space, which is the "one constant" of the proposition
    assert np.allclose(X.sum(axis=1), 0)

    # no edges at all: every node its own component
    empty = np.zeros((0, len(leagues)))
    rank0, _ = itp.laplacian_rank(empty, np.zeros(0))
    assert rank0 == 0

    # two islands: {EL, a, b} and {EC, c, d}
    leagues2 = ["EL", "EC", "a", "b", "c", "d"]
    src2 = ["a", "b", "c", "d"]
    dest2 = ["EL", "EL", "EC", "EC"]
    X2 = itp.league_incidence(src2, dest2, leagues2)
    rank2, _ = itp.laplacian_rank(X2, np.ones(4))
    assert rank2 == len(leagues2) - 2


def test_two_way_fixed_effects_recover_league_effects_up_to_the_pin():
    """The pinned WLS recovers ``beta`` exactly on noise-free differenced data.

    Player ability is added to BOTH sides of every pair and must cancel
    (P4(i)). Mutation: drop the ``sqrt(w)`` weighting on the response only —
    the estimate is then biased whenever the weights vary.
    """
    rng = np.random.default_rng(4)
    leagues = ["EL", "a", "b", "c"]
    truth = {"EL": 0.0, "a": 0.2, "b": 0.1, "c": 0.3}
    n = 60
    src = rng.choice(["a", "b", "c"], n)
    dest = np.array(["EL"] * n)
    alpha = rng.normal(2, 0.5, n)  # player ability, cancels in the difference
    y = np.array(
        [
            (alpha[i] + truth[d]) - (alpha[i] + truth[s])
            for i, (s, d) in enumerate(zip(src, dest))
        ]
    )
    X = itp.league_incidence(src, dest, leagues)
    w = rng.uniform(1, 500, n)
    beta = itp.solve_two_way_fe(X, y, w, leagues, "EL")
    assert beta[0] == 0.0
    assert np.allclose(beta, [truth[lg] for lg in leagues], atol=1e-10)


# --------------------------------------------------------------------------- P5
def test_weighted_mean_gap_identity_holds_and_sign_follows_covariance():
    """P5: ``sum(w r)/sum(w) - mean(r) == Cov(w, r)/mean(w)``, so the sign of the
    gap is the sign of ``Cov(w, r)``.

    Mutation: divide by ``np.sum(w)`` instead of ``w.mean()`` in the identity
    side — the two sides then differ by a factor of n and the test fails.
    """
    rng = np.random.default_rng(5)
    for _ in range(20):
        n = int(rng.integers(5, 300))
        w = rng.uniform(1, 1000, n)
        r = rng.normal(0.85, 0.25, n)
        gap, ident = itp.weighted_mean_gap(w, r)
        assert gap == pytest.approx(ident, abs=itp.IDENTITY_TOL)
        assert np.sign(gap) == np.sign(np.cov(w, r, ddof=0)[0, 1])

    # constructed signs: heavy weights on high ratios -> positive gap; and the
    # mirror image -> negative gap
    r = np.array([0.6, 0.7, 0.8, 0.9, 1.0])
    gap_pos, _ = itp.weighted_mean_gap(np.array([1.0, 2.0, 3.0, 4.0, 5.0]), r)
    gap_neg, _ = itp.weighted_mean_gap(np.array([5.0, 4.0, 3.0, 2.0, 1.0]), r)
    gap_zero, _ = itp.weighted_mean_gap(np.ones(5), r)
    assert gap_pos > 0 > gap_neg
    assert gap_zero == pytest.approx(0.0, abs=1e-12)


# ------------------------------------------------------------------- guards
def test_walkforward_reproduction_gate_fails_on_drift():
    """The script must refuse to run on folds that do not reproduce the summary.

    Mutation: raise ``MAE_TOL`` to 1.0 — the drifted frame then passes and the
    test fails.
    """
    rows = pd.DataFrame(
        {
            "y": [10.0, 12.0, 8.0],
            "per_league": [9.0, 12.0, 9.0],
            "one_global": [8.0, 12.0, 9.0],
            "b0": [7.0, 12.0, 9.0],
            "rtm": [9.5, 12.0, 9.0],
            "rtm_plus_league": [9.8, 12.0, 9.0],
        }
    )
    summary = {
        "n_pooled": 3,
        "pooled": {"mae_per_league": 2 / 3, "mae_one_global": 1.0, "mae_b0": 4 / 3},
        "rtm_comparator": {"mae_rtm": 0.5, "mae_rtm_plus_league": 0.4},
    }
    got = itp.assert_reproduces_walkforward(rows, summary)
    assert got["per_league"] == pytest.approx(2 / 3)

    drifted = {**summary, "pooled": {**summary["pooled"], "mae_per_league": 0.7}}
    with pytest.raises(AssertionError, match="does not reproduce"):
        itp.assert_reproduces_walkforward(rows, drifted)
    with pytest.raises(AssertionError, match="walk-forward rows"):
        itp.assert_reproduces_walkforward(rows, {**summary, "n_pooled": 4})


def test_source_asserts_the_three_proposition_gates():
    """The P1 oracle floor, the P2 ceiling and the P5 identity are in-script
    asserts, so a run fails rather than reports if a proposition stops holding
    on the corpus. Pinned as source text so a refactor cannot quietly turn an
    assert into a printed warning.
    """
    text = open(itp.__file__, encoding="utf-8").read()
    assert 'assert dest["oracle_league"]["mse"] <= dest["per_league"]["mse"]' in text
    assert 'assert v["corr2_y"] <= rel_full' in text
    assert "assert abs(gap - ident) < IDENTITY_TOL" in text
    assert "assert abs(got[arm] - expected[arm]) < MAE_TOL" in text


# ------------------------------------------------------- P4: effective resistance
def test_effective_resistance_on_a_path_graph_adds_in_series():
    """Two unit conductors in series a-b-c: R_eff(a, c) = 2, R_eff(a, b) = 1.

    Mutation: drop the ``- 2 Lap^+_ij`` cross term -- R_eff(a, c) no longer
    equals the series sum.
    """
    leagues = ["a", "b", "c"]
    X = itp.league_incidence(["a", "b"], ["b", "c"], leagues)
    r = itp.effective_resistance(X, np.ones(2))
    assert np.isclose(r[0, 2], 2.0)
    assert np.isclose(r[0, 1], 1.0)
    assert np.isclose(r[1, 2], 1.0)
    assert np.allclose(np.diag(r), 0.0)


def test_effective_resistance_halves_with_a_parallel_path_and_scales_with_weight():
    """A second edge in parallel halves the resistance; doubling every weight
    halves it too (conductance = weight)."""
    leagues = ["a", "b"]
    single = itp.effective_resistance(
        itp.league_incidence(["a"], ["b"], leagues), [1.0]
    )
    double = itp.effective_resistance(
        itp.league_incidence(["a", "a"], ["b", "b"], leagues), [1.0, 1.0]
    )
    heavy = itp.effective_resistance(itp.league_incidence(["a"], ["b"], leagues), [2.0])
    assert np.isclose(single[0, 1], 1.0)
    assert np.isclose(double[0, 1], 0.5)
    assert np.isclose(heavy[0, 1], 0.5)


def test_contrast_se_matches_the_wls_covariance_and_ignores_the_pin():
    """SE(beta_i - beta_j) = sigma * sqrt(R_eff) equals the contrast SE read off
    the pinned WLS covariance, whichever league is pinned; the implied
    (unobserved) contrast a-c gets an SE from the same matrix.

    Mutation: use ``len(y) - 1`` instead of ``len(y) - rank`` for sigma^2 --
    the two SEs part by the rank factor.
    """
    rng = np.random.default_rng(7)
    leagues = ["a", "b", "c"]
    n = 300
    src = rng.choice(["a", "b"], n)
    dest = np.where(src == "a", "b", "c")
    X = itp.league_incidence(src, dest, leagues)
    w = rng.uniform(0.5, 2.0, n)
    true = np.array([0.0, 0.3, 0.5])
    y = X @ true + rng.normal(0, 1, n) / np.sqrt(w)
    for pin in leagues:
        beta = itp.solve_two_way_fe(X, y, w, leagues, pin)
        se, sigma2 = itp.contrast_se(X, y, w, beta)
        keep = [i for i, lg in enumerate(leagues) if lg != pin]
        Xk = X[:, keep] * np.sqrt(w)[:, None]
        # sigma^2 computed HERE, independently: n - 2 free league effects
        resid = y - X @ beta
        sigma2_direct = float(np.sum(w * resid**2) / (n - 2))
        assert np.isclose(sigma2, sigma2_direct, rtol=1e-12)
        cov = sigma2_direct * np.linalg.inv(Xk.T @ Xk)
        # contrast between the two non-pinned leagues via the covariance
        c = np.array([1.0, -1.0])
        direct = float(np.sqrt(c @ cov @ c))
        i, j = keep
        assert np.isclose(se[i, j], direct, rtol=1e-8), pin
        # the same SE whichever league is pinned
        assert np.isclose(se[0, 2], se[2, 0])
    # implied a-c (never observed directly) is the series sum of the two edges
    assert se[0, 2] > max(se[0, 1], se[1, 2])
