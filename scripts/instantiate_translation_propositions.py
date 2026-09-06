"""Five propositions behind the translation model, instantiated on the corpus.

The Sloan draft states three of its main results as empirical nulls: the
per-league factor table adds little over one constant, no model reaches an R²
above about 0.7, and a hot source season predicts a worse translation. Each is
a consequence of a short inequality plus ONE number measured from the corpus.
This script measures those numbers, so the paper can say "it cannot exist
beyond this bound, and here is the bound" instead of "we did not find it". The
propositions themselves (statements and proofs) are in
``docs/research/translation-propositions-2026-09-04.md``.

Design, fixed before the run:

* **Same rows as the walk-forward.** The corpus is loaded through
  ``validate_translation_holdout.load_corpus`` and the six walk-forward folds
  are rebuilt with ``validate_translation_walkforward.one_season`` /
  ``_fit_rtm_arms`` / ``fold_rows``. The five arm MAEs MUST reproduce
  ``walkforward_summary.json`` to 1e-6 or the run fails — a proposition
  instantiated on different rows than the paper's table is worthless.
* **P1 (league-information bound).** Law of total variance: no predictor that
  sees only the league cell can cut MSE below ``Var(R) - Var(E[R|L])``. The
  in-sample least-squares cell multiplier ``m_c = sum(s*y)/sum(s^2)`` is the
  oracle for the ``src * multiplier`` form, so its in-sample MSE is a floor on
  the out-of-sample MSE of the shipped table. In-script assert: the oracle's
  MSE is at or below the shipped per-league arm's MSE.
* **P2 (reliability ceiling).** Cauchy–Schwarz: ``Corr(f, Y)^2 <= Var(T)/Var(Y)``
  for any predictor ``f`` of ``Y = T + e``. Reliability is estimated from
  odd/even split halves of the destination season, stepped up with
  Spearman–Brown. In-script assert: every arm's ``Corr^2`` is at or below the
  split-half reliability on the same 674 rows.
* **P3 (Spearman–Brown).** The formula is a testable assumption: split-half
  reliability from the first ``2k`` games only, ``k = 1..12``, against the
  one-parameter curve (drawn three ways: r1 from the single-game split,
  r1 from the corpus-wide inversion, and a least-squares fit). Games needed
  for 0.6/0.7/0.8/0.9 and the share of scored transfers that have them.
* **P4 (identification).** Two-way fixed effects ``log rate = alpha_p + beta_L``:
  the exposure-weighted league Laplacian has rank ``leagues - components``, the
  pinned solution gives factors to EuroLeague, and the hot/cold split (source
  season above / below the player's own prior-seasons rate) measures the level
  shift that selection through the source-season noise leaves behind.
* **P5 (weighted-mean identity).** ``sum(w r)/sum(w) - mean(r) = Cov(w, r)/mean(w)``,
  checked to 1e-10 on every cell for two weightings. In-script assert.

Outputs: ``data/processed/translation/propositions.json`` and the three-panel
figure ``docs/research/translation_propositions.png``.

Usage:
    uv run python scripts/instantiate_translation_propositions.py
"""

from __future__ import annotations

import argparse
import contextlib
import io
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats
from scipy.optimize import minimize_scalar

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

import scripts.validate_translation_holdout as vh  # noqa: E402
import scripts.validate_translation_walkforward as wf  # noqa: E402

SEED = 0
N_BOOT_ETA = 2000
N_BOOT_SHIFT = 500
PIN_LEAGUE = "euroleague"
#: Domestic-to-domestic moves the corpus never observes directly; their factor is
#: a consequence of connectivity (P4 ii) and its SE of the effective resistance.
IMPLIED_MOVES = (
    ("spain-acb", "italy-lba"),
    ("germany-bbl", "spain-acb"),
    ("aba-league", "turkey-bsl"),
)
MAE_TOL = 1e-6
IDENTITY_TOL = 1e-10
RELIABILITY_TARGETS = (0.6, 0.7, 0.8, 0.9)
CURVE_MIN_GAMES = 24
CURVE_MAX_HALF = 12
_DEFAULT_OUT = REPO / "data" / "processed" / "translation"
_DEFAULT_FIG = REPO / "docs" / "research" / "translation_propositions.png"

#: The walk-forward arms, in the order the summary reports them.
ARMS = ("per_league", "one_global", "b0", "rtm", "rtm_plus_league")


# --------------------------------------------------------------------- helpers
def cell(df: pd.DataFrame) -> pd.Series:
    """League cell of a pair: source league x destination competition."""
    return df.league_src + "\u2192" + df.league_dest


def mse(a, b) -> float:
    return float(np.mean((np.asarray(a, float) - np.asarray(b, float)) ** 2))


def corr(a, b) -> float:
    return float(np.corrcoef(np.asarray(a, float), np.asarray(b, float))[0, 1])


# --------------------------------------------------------------------------- P1
def eta_squared(values, groups) -> dict:
    """Between-group share of variance: raw eta^2 and bias-corrected omega^2.

    ``eta2_raw * Var(R)`` is exactly ``Var(E[R|L])``, the P1 bound on the MSE
    gain any league-only predictor can achieve over the constant.
    """
    df = pd.DataFrame({"v": np.asarray(values, float), "g": np.asarray(groups)})
    gm = df.v.mean()
    sst = float(((df.v - gm) ** 2).sum())
    agg = df.groupby("g").v.agg(["mean", "count"])
    ssb = float((agg["count"] * (agg["mean"] - gm) ** 2).sum())
    k, n = len(agg), len(df)
    msw = (sst - ssb) / (n - k)
    return {
        "eta2_raw": ssb / sst,
        "eta2_adj": max((ssb - (k - 1) * msw) / (sst + msw), 0.0),
        "groups": int(k),
        "n": int(n),
    }


def oracle_cell_multipliers(src, y, cells) -> pd.Series:
    """In-sample least-squares multiplier per cell for the form ``src * m_c``.

    ``m_c = sum(src*y) / sum(src^2)`` minimises ``sum((y - src*m)^2)`` within a
    cell, so ``src * m_c`` is the oracle for every predictor of that form —
    including the shipped table, whose cells are fitted on prior seasons.
    """
    df = pd.DataFrame(
        {"s": np.asarray(src, float), "y": np.asarray(y, float), "c": np.asarray(cells)}
    )
    num = (df.s * df.y).groupby(df.c).sum()
    den = (df.s**2).groupby(df.c).sum()
    return num / den


def cluster_bootstrap_eta2(values, groups, clusters, *, n_boot: int, seed: int):
    """Percentile CI for eta^2 resampling whole destination club-seasons."""
    df = pd.DataFrame({"v": values, "g": groups, "c": clusters})
    by = {c: d for c, d in df.groupby("c")}
    keys = np.array(list(by))
    rng = np.random.default_rng(seed)
    draws = np.empty(n_boot)
    for i in range(n_boot):
        pick = rng.choice(keys, size=len(keys), replace=True)
        boot = pd.concat([by[k] for k in pick], ignore_index=True)
        draws[i] = eta_squared(boot.v, boot.g)["eta2_raw"]
    return [float(np.percentile(draws, 2.5)), float(np.percentile(draws, 97.5))]


# --------------------------------------------------------------------------- P2
def split_half_games(games: pd.DataFrame) -> pd.DataFrame:
    """Destination player-games with an odd/even half label per player-season.

    Same construction as ``validate_translation_holdout.destination_reliability``,
    kept at game level so the halves can be re-cut (P3) and joined onto the
    scored rows (P2).
    """
    d = games[games.league.isin(vh.blf.CONTINENTAL) & (games.minutes > 0)].copy()
    d["gidx"] = d.groupby(["player_name", "season", "league"]).cumcount()
    d["half"] = np.where(d.gidx % 2 == 0, "a", "b")
    return d


def half_table(d: pd.DataFrame) -> pd.DataFrame:
    """Per-half minutes-weighted PIR/36 and game counts, one row per unit."""
    h = (
        d.groupby(["player_name", "season", "league", "half"])
        .agg(pir=("pir", "sum"), minutes=("minutes", "sum"), n=("game_id", "nunique"))
        .reset_index()
    )
    h["rate"] = 36 * h.pir / h.minutes
    hp = h.pivot_table(
        index=["player_name", "season", "league"], columns="half", values=["rate", "n"]
    )
    hp.columns = [f"{a}_{b}" for a, b in hp.columns]
    return hp.reset_index()


def reliability_ceiling_check(y, arms: dict[str, np.ndarray], reliability: float):
    """P2 on the scored rows: ``Corr(f, Y)^2`` per arm, and its share of the ceiling."""
    out = {}
    for name, p in arms.items():
        c = corr(p, y)
        out[name] = {
            "corr_y": c,
            "corr2_y": c * c,
            "disattenuated": c / float(np.sqrt(reliability)),
            "share_of_ceiling": c * c / reliability,
        }
    return out


# --------------------------------------------------------------------------- P3
def spearman_brown(r1, n):
    """Reliability of the mean of ``n`` exchangeable games with per-game ``r1``."""
    return vh.spearman_brown(r1, n)


def games_needed(r1: float, target: float) -> float:
    """Inverse of Spearman–Brown: games needed for reliability ``target``."""
    return target * (1.0 - r1) / (r1 * (1.0 - target))


def reliability_curve(d: pd.DataFrame, *, min_games: int, max_half: int):
    """Split-half reliability from the first ``2k`` games only, k = 1..max_half."""
    big = d.groupby(["player_name", "season", "league"]).game_id.nunique()
    keep = big[big >= min_games].index
    dd = d.set_index(["player_name", "season", "league"]).loc[keep].reset_index()
    curve = []
    for k in range(1, max_half + 1):
        sub = dd[dd.gidx < 2 * k]
        hh = (
            sub.groupby(["player_name", "season", "league", "half"])
            .agg(pir=("pir", "sum"), minutes=("minutes", "sum"))
            .reset_index()
        )
        hh["rate"] = 36 * hh.pir / hh.minutes
        pv = hh.pivot_table(
            index=["player_name", "season", "league"], columns="half", values="rate"
        ).dropna()
        r = corr(pv.a, pv.b)
        curve.append(
            {
                "games_per_half": k,
                "n_units": int(len(pv)),
                "r_half": r,
                "rel_2k_games": 2 * r / (1 + r),
            }
        )
    return pd.DataFrame(curve)


# --------------------------------------------------------------------------- P4
def league_incidence(league_src, league_dest, leagues: list[str]) -> np.ndarray:
    """Pair incidence matrix: +1 on the destination league, -1 on the source."""
    idx = {lg: i for i, lg in enumerate(leagues)}
    src = pd.Series(league_src).map(idx).to_numpy()
    dest = pd.Series(league_dest).map(idx).to_numpy()
    X = np.zeros((len(src), len(leagues)))
    X[np.arange(len(src)), dest] += 1
    X[np.arange(len(src)), src] -= 1
    return X


def laplacian_rank(X: np.ndarray, w: np.ndarray) -> tuple[int, float]:
    """Rank of the weighted league Laplacian ``X^T W X`` and its Fiedler value.

    P4(ii): rank equals ``#leagues - #connected components``, so with one
    component exactly one direction (the all-ones vector) is unidentified.
    """
    lap = X.T @ (X * np.asarray(w, float)[:, None])
    rank = int(np.linalg.matrix_rank(lap))
    eig = np.sort(np.linalg.eigvalsh(lap))
    return rank, float(eig[1]) if len(eig) > 1 else float("nan")


def solve_two_way_fe(
    X: np.ndarray, y: np.ndarray, w: np.ndarray, leagues: list[str], pin: str
) -> np.ndarray:
    """Weighted least squares for the league effects, ``pin`` fixed at zero."""
    keep = [i for i, lg in enumerate(leagues) if lg != pin]
    sw = np.sqrt(np.asarray(w, float))
    bk, *_ = np.linalg.lstsq(X[:, keep] * sw[:, None], np.asarray(y) * sw, rcond=None)
    beta = np.zeros(len(leagues))
    beta[keep] = bk
    return beta


def effective_resistance(X: np.ndarray, w: np.ndarray) -> np.ndarray:
    """Effective-resistance matrix of the weighted league graph.

    With ``Lap = X^T W X`` and ``Lap^+`` its pseudo-inverse,
    ``R_eff(i, j) = Lap^+_ii + Lap^+_jj - 2 Lap^+_ij``. Under the two-way model
    with ``Var(eps_i) = sigma^2 / w_i``, ``Var(beta_i - beta_j) = sigma^2 R_eff(i, j)``
    for EVERY pair of leagues -- observed cells and implied ones alike -- and it
    does not depend on which league is pinned. The electrical reading: each pair
    is a conductor of conductance ``w``; a contrast is well identified when many
    parallel paths join its two nodes.
    """
    lap = X.T @ (X * np.asarray(w, float)[:, None])
    lp = np.linalg.pinv(lap)
    d = np.diag(lp)
    return d[:, None] + d[None, :] - 2 * lp


def contrast_se(
    X: np.ndarray, y: np.ndarray, w: np.ndarray, beta: np.ndarray
) -> tuple[np.ndarray, float]:
    """Standard error of every ``beta_i - beta_j`` from the effective resistance.

    ``sigma^2`` is the weighted residual variance of the fitted two-way model,
    ``sum w r^2 / (n - rank)``. Returns the SE matrix and ``sigma^2``.
    """
    w = np.asarray(w, float)
    r = np.asarray(y, float) - X @ beta
    rank = int(np.linalg.matrix_rank(X.T @ (X * w[:, None])))
    sigma2 = float(np.sum(w * r**2) / (len(y) - rank))
    return np.sqrt(sigma2 * effective_resistance(X, w)), sigma2


def prior_seasons_rate(games: pd.DataFrame) -> pd.DataFrame:
    """Minutes-weighted PIR/36 over all strictly earlier seasons, any league."""
    ps = (
        games[games.minutes > 0]
        .groupby(["player_name", "season"])
        .agg(pir=("pir", "sum"), minutes=("minutes", "sum"))
        .reset_index()
        .sort_values(["player_name", "season"])
    )
    grp = ps.groupby("player_name")
    c_pir = grp.pir.cumsum() - ps.pir
    c_min = grp.minutes.cumsum() - ps.minutes
    ps["prior_rate"] = np.where(c_min > 0, 36 * c_pir / c_min, np.nan)
    return ps[["player_name", "season", "prior_rate"]]


# --------------------------------------------------------------------------- P5
def weighted_mean_gap(w, r) -> tuple[float, float]:
    """(weighted mean - unweighted mean, Cov(w, r)/mean(w)) — P5 says they agree."""
    w, r = np.asarray(w, float), np.asarray(r, float)
    gap = float(np.sum(w * r) / np.sum(w) - r.mean())
    ident = float(np.mean((w - w.mean()) * (r - r.mean())) / w.mean())
    return gap, ident


# ------------------------------------------------------------------- pipeline
def load_inputs(
    continental_source: str,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Corpus, pairs and the pooled walk-forward rows, exactly as the validator."""
    games, pairs = vh.load_corpus(continental_source)
    with contextlib.redirect_stdout(io.StringIO()):
        switch, _ = vh.build_switchers(games)
    cohorts = switch[switch.was_cont == 0]
    cohorts = cohorts[~cohorts.league_src.isin(vh.EXCLUDED_SOURCE)]
    cohorts = cohorts[cohorts.pir_per36_src > 0]
    fits = [wf.one_season(pairs, cohorts, s) for s in wf.SEASONS]
    for f in fits:
        f["rtm_arms"] = wf._fit_rtm_arms(f)
    rows = pd.concat([wf.fold_rows(f) for f in fits], ignore_index=True)
    rows = rows[np.isfinite(rows.per_league)].reset_index(drop=True)
    return games, pairs, rows


def assert_reproduces_walkforward(rows: pd.DataFrame, summary: dict) -> dict:
    """The five arm MAEs must match the shipped summary, or nothing below counts."""
    expected = {
        "per_league": summary["pooled"]["mae_per_league"],
        "one_global": summary["pooled"]["mae_one_global"],
        "b0": summary["pooled"]["mae_b0"],
        "rtm": summary["rtm_comparator"]["mae_rtm"],
        "rtm_plus_league": summary["rtm_comparator"]["mae_rtm_plus_league"],
    }
    got = {arm: float(np.abs(rows[arm] - rows.y).mean()) for arm in ARMS}
    assert len(rows) == summary["n_pooled"], (
        f"walk-forward rows: {len(rows)} here vs {summary['n_pooled']} in the summary"
    )
    for arm in ARMS:
        assert abs(got[arm] - expected[arm]) < MAE_TOL, (
            f"{arm} MAE {got[arm]:.6f} does not reproduce the shipped "
            f"{expected[arm]:.6f} -- the folds have drifted; fix that first"
        )
    return got


def proposition_1(pairs: pd.DataFrame, rows: pd.DataFrame) -> dict:
    pa = pairs[pairs.pir_per36_src > 0].copy()
    pa["R"] = pa.pir_per36_dest / pa.pir_per36_src
    rb = rows.copy()
    rb["R"] = rb.y / rb.src

    def population(df: pd.DataFrame) -> dict:
        e = eta_squared(df.R, cell(df))
        var_r = float(df.R.var(ddof=0))
        return {
            "n": e["n"],
            "cells": e["groups"],
            "var_R": var_r,
            "sd_R": float(np.sqrt(var_r)),
            "eta2_raw": e["eta2_raw"],
            "eta2_adj": e["eta2_adj"],
            "eta2_ci": cluster_bootstrap_eta2(
                df.R, cell(df), df.cluster, n_boot=N_BOOT_ETA, seed=SEED
            ),
            "mse_gain_bound_ratio": e["eta2_raw"] * var_r,
            "rmse_ratio_global": float(np.sqrt(var_r)),
            "rmse_ratio_oracle": float(np.sqrt(var_r * (1 - e["eta2_raw"]))),
        }

    out = {"pairs": population(pa), "switchers": population(rb)}

    # ratio space: the walk-forward arms as implied multipliers
    rb["m_league"] = rb.per_league / rb.src
    rb["m_global"] = rb.one_global / rb.src
    cm = rb.groupby(cell(rb)).R.transform("mean")
    out["ratio_space_mse"] = {
        "constant": float(rb.R.var(ddof=0)),
        "oracle_cells_in_sample": mse(rb.R, cm),
        "wf_global": mse(rb.R, rb.m_global),
        "wf_per_league": mse(rb.R, rb.m_league),
        "bound_var_cond_mean": out["switchers"]["mse_gain_bound_ratio"],
        "realised_gain": mse(rb.R, rb.m_global) - mse(rb.R, rb.m_league),
    }

    # destination units: the oracle for the multiplicative form
    m_or = oracle_cell_multipliers(rb.src, rb.y, cell(rb))
    rb["oracle_league"] = rb.src * m_or.loc[cell(rb)].to_numpy()
    rb["oracle_global"] = rb.src * (rb.src * rb.y).sum() / (rb.src**2).sum()
    arms = {
        "one_global": rb.one_global,
        "oracle_global": rb.oracle_global,
        "per_league": rb.per_league,
        "oracle_league": rb.oracle_league,
        "rtm": rb.rtm,
        "rtm_plus_league": rb.rtm_plus_league,
        "b0_untranslated": rb.b0,
    }
    dest = {k: vh.metrics(rb.y, v) for k, v in arms.items()}
    for v in dest.values():
        v["mse"] = v.pop("rmse") ** 2
    assert dest["oracle_league"]["mse"] <= dest["per_league"]["mse"], (
        "the in-sample league-only oracle lost to the out-of-sample table -- "
        "impossible under P1; the oracle is mis-specified"
    )
    out["dest_units"] = dest
    out["dest_units_gain"] = {
        "realised_global_to_league": dest["one_global"]["mse"]
        - dest["per_league"]["mse"],
        "oracle_ceiling": dest["one_global"]["mse"] - dest["oracle_league"]["mse"],
        "var_y": float(rb.y.var(ddof=0)),
    }
    return out


def proposition_2(games: pd.DataFrame, rows: pd.DataFrame) -> dict:
    ceil = wf.r2_ceiling(games, float(rows.games_dest.mean()))
    r1 = float(
        vh.per_observation_reliability(ceil["split_half_r"], ceil["mean_games_per_arm"])
    )
    d = split_half_games(games)
    hp = half_table(d)
    m = rows.merge(
        hp,
        left_on=["player_name", "season", "league_dest"],
        right_on=["player_name", "season", "league"],
        how="left",
    )
    mm = m[m.rate_a.notna() & m.rate_b.notna()]
    assert len(mm) == len(rows), f"{len(rows) - len(mm)} scored rows lack split halves"
    r_ab = corr(mm.rate_a, mm.rate_b)
    rel_full = 2 * r_ab / (1 + r_ab)
    arm_names = ("one_global", "per_league", "rtm", "rtm_plus_league")
    arms = {k: mm[k].to_numpy() for k in arm_names}
    check = reliability_ceiling_check(mm.y, arms, rel_full)
    for name, v in check.items():
        v["corr_half_a"] = corr(arms[name], mm.rate_a)
        v["corr_half_b"] = corr(arms[name], mm.rate_b)
        v["r2_oos"] = vh.metrics(mm.y, arms[name])["r2"]
        assert v["corr2_y"] <= rel_full, (
            f"{name}: Corr^2 {v['corr2_y']:.4f} exceeds the reliability {rel_full:.4f} "
            "-- P2 is violated, so the noise model E[e|X]=0 does not hold"
        )
    return {
        "corpus_split_half_r": ceil["split_half_r"],
        "mean_games_per_arm": ceil["mean_games_per_arm"],
        "r1_per_game": r1,
        "ceiling_at_mean_scored_games": ceil["ceiling_r2_at_mean_games"],
        "mean_per_row_ceiling": float(np.mean(spearman_brown(r1, rows.games_dest))),
        "scored_rows_split_half_r": r_ab,
        "scored_rows_reliability_sb": rel_full,
        "arms": check,
        "_games_split": d,
    }


def proposition_3(d: pd.DataFrame, rows: pd.DataFrame, r1: float) -> dict:
    curve = reliability_curve(d, min_games=CURVE_MIN_GAMES, max_half=CURVE_MAX_HALF)
    n2k = 2 * curve.games_per_half.to_numpy()
    r1_fit = float(
        minimize_scalar(
            lambda r: np.sum((spearman_brown(r, n2k) - curve.rel_2k_games) ** 2),
            bounds=(0.01, 0.5),
            method="bounded",
        ).x
    )
    r1_single = float(curve.r_half.iloc[0])
    curve["sb_pred_from_r1"] = spearman_brown(r1_single, n2k)
    curve["sb_pred_corpus_r1"] = spearman_brown(r1, n2k)
    curve["sb_pred_fit"] = spearman_brown(r1_fit, n2k)
    need = {str(t): games_needed(r1, t) for t in RELIABILITY_TARGETS}
    share = {t: float((rows.games_dest >= np.ceil(v)).mean()) for t, v in need.items()}
    return {
        "r1_single_game": r1_single,
        "r1_corpus_inversion": r1,
        "r1_ls_fit": r1_fit,
        "curve": curve.round(5).to_dict("records"),
        "games_needed": need,
        "share_scored_rows_meeting": share,
    }


def proposition_4(games: pd.DataFrame, pairs: pd.DataFrame) -> dict:
    pa = pairs[pairs.pir_per36_src > 0].copy()
    pa["logR"] = np.log(pa.pir_per36_dest.clip(lower=0.1) / pa.pir_per36_src)
    pa["R"] = pa.pir_per36_dest / pa.pir_per36_src
    leagues = sorted(set(pa.league_src) | set(pa.league_dest))
    idx = {lg: i for i, lg in enumerate(leagues)}
    X = league_incidence(pa.league_src, pa.league_dest, leagues)
    w = np.minimum(pa.minutes_src, pa.minutes_dest).to_numpy(float)
    y = pa.logR.to_numpy()
    rank, fiedler = laplacian_rank(X, w)
    components = len(leagues) - rank
    assert components == 1, f"league graph has {components} components; P4 needs 1"

    beta = solve_two_way_fe(X, y, w, leagues, PIN_LEAGUE)
    domestic = [lg for lg in leagues if lg not in vh.blf.CONTINENTAL]
    se_mat, sigma2_fe = contrast_se(X, y, w, beta)
    r_eff = effective_resistance(X, w)

    def factor(a: str, b: str, b_vec: np.ndarray = beta) -> float:
        """Multiplier for a move a -> b implied by the league effects."""
        return float(np.exp(b_vec[idx[b]] - b_vec[idx[a]]))

    def factor_with_se(a: str, b: str) -> dict:
        """Implied multiplier a -> b with its effective-resistance interval."""
        se = float(se_mat[idx[a], idx[b]])
        lg = float(beta[idx[b]] - beta[idx[a]])
        return {
            "factor": float(np.exp(lg)),
            "se_log": se,
            "ci95": [float(np.exp(lg - 1.96 * se)), float(np.exp(lg + 1.96 * se))],
            "effective_resistance": float(r_eff[idx[a], idx[b]]),
            "direct_pairs": int(
                (
                    ((pa.league_src == a) & (pa.league_dest == b))
                    | ((pa.league_src == b) & (pa.league_dest == a))
                ).sum()
            ),
        }

    # ordering against the shipped estimator, refitted on the same pairs
    with contextlib.redirect_stdout(io.StringIO()):
        tbl = vh.fit_factors(pa, label="propositions_all_pairs")
    spearman: dict[str, float | int] = {}
    for dest in vh.blf.CONTINENTAL:
        t = tbl[tbl.destination == dest].set_index("league")
        fe = [factor(lg, dest) for lg in domestic]
        sh = [float(t.loc[lg, "factor"]) for lg in domestic]
        spearman[dest] = float(stats.spearmanr(fe, sh).correlation)
    spearman["n_leagues_each"] = len(domestic)

    # the failure mode: pairing conditional on the source-season noise
    pa2 = pa.merge(prior_seasons_rate(games), on=["player_name", "season"], how="left")
    has = pa2.prior_rate.notna().to_numpy()
    hot = has & (pa2.pir_per36_src > pa2.prior_rate).to_numpy()
    cold = has & ~hot

    def mean_factor_to_pin(mask: np.ndarray) -> tuple[float, np.ndarray]:
        b = solve_two_way_fe(X[mask], y[mask], w[mask], leagues, PIN_LEAGUE)
        per = np.array([factor(lg, PIN_LEAGUE, b) for lg in domestic])
        return float(per.mean()), per

    f_hot, per_hot = mean_factor_to_pin(hot)
    f_cold, per_cold = mean_factor_to_pin(cold)
    shift = f_hot - f_cold

    rng = np.random.default_rng(SEED)
    clusters = pa2.cluster.to_numpy()
    keys = np.unique(clusters)
    members = {k: np.flatnonzero(clusters == k) for k in keys}
    hot_idx, cold_idx = np.flatnonzero(hot), np.flatnonzero(cold)
    draws = np.empty(N_BOOT_SHIFT)
    implied_draws = np.empty((N_BOOT_SHIFT, len(IMPLIED_MOVES)))
    el_draws = np.empty((N_BOOT_SHIFT, len(domestic)))
    for i in range(N_BOOT_SHIFT):
        pick = np.concatenate([members[k] for k in rng.choice(keys, len(keys))])
        draws[i] = (
            mean_factor_to_pin(pick[np.isin(pick, hot_idx)])[0]
            - mean_factor_to_pin(pick[np.isin(pick, cold_idx)])[0]
        )
        # the same resample, full sample: the alternative SE for every contrast
        b_full = solve_two_way_fe(X[pick], y[pick], w[pick], leagues, PIN_LEAGUE)
        implied_draws[i] = [b_full[idx[b]] - b_full[idx[a]] for a, b in IMPLIED_MOVES]
        el_draws[i] = [b_full[idx[PIN_LEAGUE]] - b_full[idx[lg]] for lg in domestic]
    implied_boot_se = {
        f"{a}->{b}": float(implied_draws[:, j].std(ddof=1))
        for j, (a, b) in enumerate(IMPLIED_MOVES)
    }
    el_boot_se = el_draws.std(axis=0, ddof=1)
    per_league = [
        {
            "league": lg,
            "factor_to_EL_all": round(factor(lg, PIN_LEAGUE), 4),
            "factor_to_EL_hot_season": round(float(per_hot[i]), 4),
            "factor_to_EL_cold_season": round(float(per_cold[i]), 4),
        }
        for i, lg in enumerate(domestic)
    ]
    return {
        "n_leagues": len(leagues),
        "laplacian_rank": rank,
        "components": components,
        "fiedler_weighted": fiedler,
        "twfe_beta_vs_euroleague": [
            {
                "league": lg,
                "beta_log": round(float(beta[idx[lg]]), 5),
                "rate_multiplier_vs_euroleague": round(float(np.exp(beta[idx[lg]])), 5),
            }
            for lg in sorted(leagues, key=lambda g: beta[idx[g]])
        ],
        "spearman_vs_shipped": spearman,
        "implied_unobserved": {
            f"{a}->{b}": factor_with_se(a, b) for a, b in IMPLIED_MOVES
        },
        # Study D (translation-application-studies-preregistration-2026-09-06.md):
        # every domestic pair, observed together or not. Additive; the three
        # named moves above are a subset and are asserted unchanged by the test.
        "implied_all_pairs": [
            {"from": a, "to": b, **factor_with_se(a, b)}
            for a in domestic
            for b in domestic
            if a != b
        ],
        "implied_unobserved_cluster_bootstrap_se_log": implied_boot_se,
        "sigma2_two_way_fe": sigma2_fe,
        "domestic_to_euroleague_se": [
            {
                "league": lg,
                "se_log_effective_resistance": float(se_mat[idx[lg], idx[PIN_LEAGUE]]),
                "se_log_cluster_bootstrap": float(el_boot_se[i]),
                "effective_resistance": float(r_eff[idx[lg], idx[PIN_LEAGUE]]),
            }
            for i, lg in enumerate(domestic)
        ],
        "selection_test": {
            "pairs_with_prior": int(has.sum()),
            "above_prior": int(hot.sum()),
            "mean_factor_hot": f_hot,
            "mean_factor_cold": f_cold,
            "shift": shift,
            "shift_ci": [
                float(np.percentile(draws, 2.5)),
                float(np.percentile(draws, 97.5)),
            ],
            "ordering_spearman_hot_vs_cold": float(
                stats.spearmanr(per_hot, per_cold).correlation
            ),
            "corr_src_rate_R": corr(pa2.pir_per36_src, pa2.R),
            "corr_src_minus_prior_R": corr(
                (pa2.pir_per36_src - pa2.prior_rate)[has], pa2.R[has]
            ),
            "per_league": per_league,
        },
        "_hot_cold": (domestic, per_hot, per_cold),
    }


def proposition_5(pairs: pd.DataFrame) -> dict:
    pa = pairs[pairs.pir_per36_src > 0].copy()
    pa["R"] = pa.pir_per36_dest / pa.pir_per36_src
    recs = []
    for c, dfc in pa.groupby(cell(pa)):
        r = dfc.R.to_numpy()
        weights = {
            "source_volume": (dfc.pir_per36_src * dfc.minutes_src / 36).to_numpy(),
            "exposure_min": np.minimum(dfc.minutes_src, dfc.minutes_dest).to_numpy(),
        }
        for wname, wv in weights.items():
            gap, ident = weighted_mean_gap(wv, r)
            assert abs(gap - ident) < IDENTITY_TOL, (
                f"P5 identity broke on {c}/{wname}: gap {gap} vs Cov/mean {ident}"
            )
            recs.append(
                {
                    "cell": c,
                    "n": int(len(dfc)),
                    "weight": wname,
                    "gap": gap,
                    "ident": ident,
                    "abs_err": abs(gap - ident),
                    "corr_w_r": corr(wv, r),
                }
            )
    p5 = pd.DataFrame(recs)
    summary = (
        p5.groupby("weight")
        .agg(
            cells=("cell", "size"),
            negative_gap=("gap", lambda s: int((s < 0).sum())),
            mean_gap=("gap", "mean"),
            mean_corr=("corr_w_r", "mean"),
        )
        .reset_index()
    )
    sv = p5[p5.weight == "source_volume"]
    return {
        "max_abs_identity_error": float(p5.abs_err.max()),
        "summary": summary.to_dict("records"),
        "per_cell_source_volume": [
            {
                "cell": r.cell,
                "n": int(r.n),
                "weighted_minus_unweighted": round(r.gap, 5),
                "corr_w_r": round(r.corr_w_r, 5),
            }
            for r in sv.itertuples()
        ],
    }


# --------------------------------------------------------------------- figure
def render_figure(p1: dict, p2: dict, p3: dict, p4: dict, path: Path) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    blue, grey, red = "#3b6fb6", "#9a9a9a", "#d2521f"
    fig, axes = plt.subplots(1, 3, figsize=(15.6, 5.6))

    # (a) R² ladder with the league-only oracle as a hatched bound
    ax = axes[0]
    d = p1["dest_units"]
    names = ["one_global", "per_league", "oracle_league", "rtm", "rtm_plus_league"]
    labels = ["one\nconst.", "per-\nleague", "league\noracle", "RTM", "RTM +\nleague"]
    vals = [d[n]["r2"] for n in names]
    colors = [grey, blue, "white", grey, red]
    bars = ax.bar(labels, vals, color=colors, edgecolor=[grey, blue, blue, grey, red])
    bars[2].set_hatch("///")
    ax.axhline(vals[2], color=blue, ls=":", lw=1.2)
    ax.text(2, vals[2] + 0.01, f"\u2264 {vals[2]:.2f}", ha="center", color=blue)
    ax.text(4, vals[4] + 0.01, f"{vals[4]:.2f}", ha="center", color=red)
    ax.set_ylabel("out-of-sample $R^2$")
    ax.set_ylim(0, 0.5)
    ax.set_title(
        "A player's own history beats any\nleague-only predictor (bound, hatched)"
    )

    # (b) Spearman–Brown curve against the measured split-half points
    ax = axes[1]
    curve = pd.DataFrame(p3["curve"])
    n = np.linspace(1, 45, 200)
    r1 = p2["r1_per_game"]
    ax.plot(
        n,
        spearman_brown(r1, n),
        color=red,
        lw=2,
        label=f"Spearman-Brown, $r_1$={r1:.3f}",
    )
    ax.scatter(
        2 * curve.games_per_half,
        curve.rel_2k_games,
        facecolor="white",
        edgecolor="black",
        zorder=3,
        label="measured split-half",
    )
    need70 = p3["games_needed"]["0.7"]
    ax.axhline(0.7, color=grey, ls="--", lw=1)
    ax.axvline(need70, color=grey, ls="--", lw=1)
    ax.text(need70 + 1, 0.56, f"{need70:.0f} games\nfor 0.70", color="dimgray")
    ax.set_xlabel("destination games played")
    ax.set_ylabel("reliability of season PIR/36")
    ax.set_ylim(-0.02, 0.95)
    share70 = p3["share_scored_rows_meeting"]["0.7"]
    ax.set_title(
        f"Target reliability caps $R^2$;\n{share70:.0%} of transfers reach 0.70"
    )
    ax.legend(loc="lower right", frameon=False)

    # (c) hot vs cold factors to EuroLeague
    ax = axes[2]
    domestic, per_hot, per_cold = p4["_hot_cold"]
    ax.scatter(per_cold, per_hot, color=blue, s=60, zorder=3)
    lo = min(per_cold.min(), per_hot.min()) - 0.03
    hi = max(per_cold.max(), per_hot.max()) + 0.03
    ax.plot([lo, hi], [lo, hi], color=grey, ls=":", lw=1)
    st = p4["selection_test"]
    ax.plot([lo, hi], [lo + st["shift"], hi + st["shift"]], color=red, ls="--", lw=1.5)
    ax.text(
        lo + 0.005,
        hi - 0.06,
        f"level shift {st['shift']:+.2f}\n"
        f"[{st['shift_ci'][0]:.2f}, {st['shift_ci'][1]:.2f}]",
        color=red,
    )
    for lg, tag in (
        ("spain-acb", "Spain"),
        ("italy-lba", "Italy"),
        ("aba-league", "ABA"),
    ):
        i = domestic.index(lg)
        ax.annotate(
            tag, (per_cold[i], per_hot[i]), xytext=(5, -3), textcoords="offset points"
        )
    ax.set_xlabel("factor to EuroLeague,\nsource season below own prior")
    ax.set_ylabel("factor to EuroLeague,\nsource season above own prior")
    ax.set_title("Stable ability cancels (order kept);\na hot season does not")

    for ax, tag in zip(axes, "abc"):
        ax.spines[["top", "right"]].set_visible(False)
        ax.text(
            -0.18, 1.08, tag, transform=ax.transAxes, fontweight="bold", fontsize=14
        )
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)


# ----------------------------------------------------------------------- main
def _public(d: dict) -> dict:
    """Drop the frame-valued intermediates the figure needs and the JSON must not."""
    return {k: v for k, v in d.items() if not k.startswith("_")}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out-dir", type=Path, default=_DEFAULT_OUT)
    ap.add_argument("--figure", type=Path, default=_DEFAULT_FIG)
    ap.add_argument(
        "--walkforward-summary",
        type=Path,
        default=None,
        help="walkforward_summary.json to reproduce "
        "(default: <out-dir>/walkforward_summary.json)",
    )
    ap.add_argument(
        "--continental-source",
        choices=vh.blf.CONTINENTAL_SOURCES,
        default=vh.blf.DEFAULT_CONTINENTAL_SOURCE,
    )
    args = ap.parse_args(argv)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    summary_path = args.walkforward_summary or args.out_dir / "walkforward_summary.json"
    summary = json.loads(summary_path.read_text())
    assert summary["continental_source"] == args.continental_source, (
        f"summary was built with --continental-source {summary['continental_source']}"
    )

    games, pairs, rows = load_inputs(args.continental_source)
    maes = assert_reproduces_walkforward(rows, summary)
    print("[folds] " + " ".join(f"{k}={v:.4f}" for k, v in maes.items()))

    p1 = proposition_1(pairs, rows)
    print(
        f"[P1] eta2 pairs={p1['pairs']['eta2_raw']:.4f} "
        f"switchers={p1['switchers']['eta2_raw']:.4f} | "
        f"oracle_league R2={p1['dest_units']['oracle_league']['r2']:.4f} "
        f"rtm_plus_league R2={p1['dest_units']['rtm_plus_league']['r2']:.4f}"
    )
    p2 = proposition_2(games, rows)
    print(
        f"[P2] reliability(scored rows)={p2['scored_rows_reliability_sb']:.4f} "
        + " ".join(f"{k}.corr2={v['corr2_y']:.4f}" for k, v in p2["arms"].items())
    )
    p3 = proposition_3(p2["_games_split"], rows, p2["r1_per_game"])
    print(
        f"[P3] r1_fit={p3['r1_ls_fit']:.4f} games_needed="
        + " ".join(f"{k}:{v:.1f}" for k, v in p3["games_needed"].items())
    )
    p4 = proposition_4(games, pairs)
    st = p4["selection_test"]
    print(
        f"[P4] rank={p4['laplacian_rank']}/{p4['n_leagues']} "
        f"shift={st['shift']:+.4f} "
        f"CI [{st['shift_ci'][0]:+.4f},{st['shift_ci'][1]:+.4f}]"
    )
    for mv, v in p4["implied_unobserved"].items():
        print(
            f"[P4 implied] {mv}: {v['factor']:.3f} "
            f"CI [{v['ci95'][0]:.3f}, {v['ci95'][1]:.3f}] "
            f"(R_eff={v['effective_resistance']:.2e}, se_log={v['se_log']:.4f}, "
            f"cluster-boot se_log="
            f"{p4['implied_unobserved_cluster_bootstrap_se_log'][mv]:.4f}, "
            f"direct pairs={v['direct_pairs']})"
        )
    p5 = proposition_5(pairs)
    print(f"[P5] max identity error={p5['max_abs_identity_error']:.1e}")

    render_figure(p1, p2, p3, p4, args.figure)
    out = {
        "corpus": {
            "continental_source": args.continental_source,
            "player_games": int(len(games)),
            "dual_tier_pairs": int((pairs.pir_per36_src > 0).sum()),
            "cells": int(cell(pairs).nunique()),
            "walkforward_scored_rows": int(len(rows)),
            "seasons": list(wf.SEASONS),
            "walkforward_mae_reproduced": maes,
        },
        "P1_league_information_bound": _public(p1),
        "P2_reliability_ceiling": _public(p2),
        "P3_spearman_brown": p3,
        "P4_identification": _public(p4),
        "P5_weighted_mean_identity": p5,
    }
    (args.out_dir / "propositions.json").write_text(
        json.dumps(out, indent=1, default=float)
    )
    print(f"[done] wrote propositions.json to {args.out_dir} and {args.figure}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
