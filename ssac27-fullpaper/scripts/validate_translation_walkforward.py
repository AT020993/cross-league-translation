"""ATI-2891 — does per-league resolution beat one global scalar out-of-sample?

ATI-2799 measured this on ONE held-out window (n=231) and could not separate the
two: +0.056 MAE, CI [-0.134, +0.246]. That null was read as "the 22-cell table
buys nothing." This script tests whether that was a property of the estimator or
a limit of the sample, by walking forward season by season.

Design, fixed before the run:

* For each destination season S in 2020..2025, refit the factor table on pairs
  from seasons strictly < S, and refit the lag correction K on newcomer cohorts
  from seasons strictly < S. Nothing from S or later touches either fit.
* Score season S's switchers-in five ways: per-league factors, one global
  exposure-weighted scalar, untranslated B0, a regression-to-the-mean model that
  uses NO league information, and RTM plus the per-league translated rate.
* Compare by paired cluster bootstrap on destination club-season.

The RTM arm exists because the first four arms could not answer the obvious
objection. Only a small share of the variance in realised translation ratios is
BETWEEN leagues -- 8.7% on the same-season pairs and 14.5% on the scored
transfers of the API-destination corpus (``instantiate_translation_propositions.py``,
P1; the "~4%" this docstring carried until 2026-09-05 was measured on the
Proballers-destination corpus); the rest is player-to-player within a league. So
the honest comparator
for a 22-cell league table is not one constant -- it is a model that predicts
regression to the mean from a player's own history and ignores league identity
entirely. Against THAT, per-league resolution is a tie. The two are
complementary rather than competing, which is the result this script now
reports.

Controls:

* **Shuffled-factor null.** Permute the league->multiplier assignment within each
  season. If the gain came from dispersion rather than from the league mapping,
  shuffled draws would match it. This is the check that can fail.
* **Level correction removed.** Re-run with K = 1 throughout, to establish
  whether the gain depends on the level correction or is independent of it.
* **Shuffled mapping inside the combined arm.** The combined arm adds a column,
  and an extra degree of freedom can improve fit on its own. Permuting the
  league->multiplier assignment and refitting tests whether the joint gain is the
  mapping or the column.

Usage:
    uv run python scripts/validate_translation_walkforward.py
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

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

import scripts.validate_translation_holdout as vh  # noqa: E402

SEASONS = (2020, 2021, 2022, 2023, 2024, 2025)
N_BOOT = 4000
N_SHUFFLE = 200
SEED = 0
_DEFAULT_OUT = REPO / "data" / "processed" / "translation"


def paired_cluster_bootstrap(
    pred_a: np.ndarray,
    pred_b: np.ndarray,
    y: np.ndarray,
    clusters: np.ndarray,
    *,
    n_boot: int = N_BOOT,
    seed: int = SEED,
) -> tuple[float, float, float]:
    """MAE(b) - MAE(a), resampling whole destination club-seasons.

    Positive means `a` is the better predictor. Clustering is on club-season
    because teammates share a coaching staff, a pace and a role structure, so
    treating them as independent would understate the interval.
    """
    err_a, err_b = np.abs(pred_a - y), np.abs(pred_b - y)
    uniq = np.unique(clusters)
    rng = np.random.default_rng(seed)
    draws = np.empty(n_boot)
    for i in range(n_boot):
        pick = rng.choice(uniq, uniq.size, replace=True)
        idx = np.concatenate([np.flatnonzero(clusters == c) for c in pick])
        draws[i] = err_b[idx].mean() - err_a[idx].mean()
    return (
        float(err_b.mean() - err_a.mean()),
        float(np.percentile(draws, 2.5)),
        float(np.percentile(draws, 97.5)),
    )


def arm_metrics(y: np.ndarray, arms: dict[str, np.ndarray]) -> dict[str, dict]:
    """MAE and R² per arm, on the same rows (ATI-2955 item 1).

    The 2026-08-21 note printed an R² per arm that this script never computed —
    the values came from a session. R² is now read off the same ``metrics``
    the holdout uses, so the two validators cannot disagree on its definition.
    """
    return {name: vh.metrics(y, p) for name, p in arms.items()}


def r2_ceiling(games: pd.DataFrame, mean_dest_games: float) -> dict:
    """Spearman-Brown ceiling on out-of-sample R² at the scored rows' exposure.

    Pre-registration §6: an R² is reported beside the reliability of the
    quantity it predicts, or it is not interpretable — 0.36 against a ceiling
    of 0.70 and against a ceiling of 0.40 are different findings.
    """
    rel = vh.destination_reliability(games)
    r1 = vh.per_observation_reliability(rel["split_half_r"], rel["mean_games_per_arm"])
    return {
        "split_half_r": rel["split_half_r"],
        "n_units": rel["n_units"],
        "mean_games_per_arm": rel["mean_games_per_arm"],
        "mean_dest_games_scored": float(mean_dest_games),
        "ceiling_r2_at_mean_games": float(vh.spearman_brown(r1, mean_dest_games)),
    }


def one_season(pairs: pd.DataFrame, cohorts: pd.DataFrame, season: int) -> dict:
    """Refit on seasons strictly before `season`, then score `season`."""
    train_pairs = pairs[pairs.season < season]
    with contextlib.redirect_stdout(io.StringIO()):
        tbl = vh.fit_factors(train_pairs, label=f"wf_{season}")

    tier = tbl.groupby("destination").tier_mean.first().to_dict()
    # T9 (pre-registration): tau == 0 collapses a block onto its tier mean, so
    # the "per-league" arm would be a two-constant arm in that fold. fit_factors
    # prints the warning, but this function silences its stdout — record it.
    tau = tbl.groupby("destination").tau.first().to_dict()
    collapsed = sorted(d for d, t in tau.items() if not (t > 0))
    if collapsed:
        print(
            f"[T9 wf_{season}] WARNING block(s) collapsed (tau=0): {collapsed} — "
            "per-league resolution is absent in this fold"
        )
    lookup = {
        (r.league, r.destination): (r.factor if r.reliable else tier[r.destination])
        for r in tbl.itertuples()
    }

    def multiplier(df: pd.DataFrame) -> np.ndarray:
        return np.array(
            [
                lookup.get((lg, d), tier.get(d, np.nan))
                for lg, d in zip(df.league_src, df.league_dest)
            ]
        )

    train_co = cohorts[cohorts.season_dest < season]
    k_lag = float(
        np.median(
            train_co.pir_per36_dest.to_numpy()
            / (train_co.pir_per36_src.to_numpy() * multiplier(train_co))
        )
    )
    scalar = float(
        np.average(tbl[tbl.reliable].factor, weights=tbl[tbl.reliable].n_pairs)
    )

    test = cohorts[cohorts.season_dest == season]
    return {
        "season": season,
        "n": int(len(test)),
        # kept so an arm can be FITTED on strictly-prior seasons inside the fold
        "train_rows": train_co,
        "test_rows": test,
        "multiplier_fn": multiplier,
        "k_lag": k_lag,
        "global_scalar": scalar,
        # carried so a consumer can report per-cell reliability (ATI-2891):
        # without it a prediction set cannot tell a real factor from a
        # tier-mean fallback, and defaulting that flag mislabels every row.
        "table": tbl,
        "tau": tau,
        "collapsed_blocks": collapsed,
        "n_train_pairs": int(len(train_pairs)),
        "n_train_cohort": int(len(train_co)),
        "multiplier": multiplier(test),
        "src": test.pir_per36_src.to_numpy(),
        "y": test.pir_per36_dest.to_numpy(),
        "clusters": test.cluster.to_numpy(),
    }


def _rtm_design(df: pd.DataFrame, league_col: np.ndarray | None = None) -> np.ndarray:
    """Predictors knowable BEFORE the destination season is played.

    `prior_mean_pir36` is the player's own rate over earlier seasons and
    `above_own_prior` flags a source season that beat his own history -- together
    they are the regression-to-the-mean signal. Neither uses league identity, so
    an RTM-only fit is a league-free comparator. Players with no prior history
    fall back to their own source rate, which is the no-information answer.
    """
    prior = df.prior_mean_pir36.to_numpy(dtype=float)
    prior = np.where(np.isnan(prior), df.pir_per36_src.to_numpy(dtype=float), prior)
    cols = [
        np.ones(len(df)),
        df.pir_per36_src.to_numpy(dtype=float),
        prior,
        df.above_own_prior.fillna(0).to_numpy(dtype=float),
    ]
    if league_col is not None:
        cols.append(league_col)
    return np.column_stack(cols)


def _fit_rtm_arms(fold: dict, multiplier: np.ndarray | None = None) -> dict:
    """OLS on the fold's strictly-prior seasons, scored on its held-out season.

    `multiplier` overrides the per-league lookup on BOTH train and test rows, so
    the shuffled-mapping control refits the combined arm rather than merely
    re-scoring it.
    """
    train, test = fold["train_rows"], fold["test_rows"]
    mult_fn = fold["multiplier_fn"]
    k = fold["k_lag"]

    def translated(df: pd.DataFrame, override: np.ndarray | None) -> np.ndarray:
        m = mult_fn(df) if override is None else override
        return df.pir_per36_src.to_numpy(dtype=float) * m * k

    if multiplier is None:
        tr_league, te_league = translated(train, None), translated(test, None)
    else:
        # map each distinct real multiplier to a permuted one, consistently
        real = mult_fn(train)
        uniq = np.unique(real[~np.isnan(real)])
        mapping = dict(zip(uniq, multiplier))
        remap = lambda d: np.array(  # noqa: E731
            [mapping.get(v, np.nan) for v in mult_fn(d)]
        )
        tr_league, te_league = (
            translated(train, remap(train)),
            translated(test, remap(test)),
        )

    y_train = train.pir_per36_dest.to_numpy(dtype=float)
    out = {}
    for name, tr_col, te_col in (
        ("rtm", None, None),
        ("rtm_plus_league", tr_league, te_league),
    ):
        beta, *_ = np.linalg.lstsq(_rtm_design(train, tr_col), y_train, rcond=None)
        out[name] = _rtm_design(test, te_col) @ beta
    return out


def fold_rows(fold: dict) -> pd.DataFrame:
    """Every test row of one fold with every arm's prediction beside it.

    The pre-lock program (Studies B, C, D — `prelock-program-preregistration-
    2026-09-04.md`) reads THIS frame rather than refitting the folds, so the
    three studies cannot drift apart from the walk-forward or from each other.
    Nothing here is a new arm: `per_league`, `one_global`, `b0`, `rtm` and
    `rtm_plus_league` are the five the summary already scores.
    """
    test = fold["test_rows"]
    tbl = fold["table"]
    reliable = {(r.league, r.destination): bool(r.reliable) for r in tbl.itertuples()}
    rtm = fold.get("rtm_arms") or {}
    out = pd.DataFrame(
        {
            "season": fold["season"],
            "player_name": test.player_name.to_numpy()
            if "player_name" in test
            else np.arange(len(test)),
            "league_src": test.league_src.to_numpy(),
            "league_dest": test.league_dest.to_numpy(),
            "cluster": fold["clusters"],
            "games_src": test.games_src.to_numpy() if "games_src" in test else np.nan,
            "games_dest": test.games_dest.to_numpy()
            if "games_dest" in test
            else np.nan,
            "minutes_src": test.minutes_src.to_numpy()
            if "minutes_src" in test
            else np.nan,
            "src": fold["src"],
            "y": fold["y"],
            "multiplier": fold["multiplier"],
            "factor_reliable": [
                reliable.get((lg, d), False)
                for lg, d in zip(test.league_src, test.league_dest)
            ],
            "k_lag": fold["k_lag"],
            "global_scalar": fold["global_scalar"],
            "per_league": fold["src"] * fold["multiplier"] * fold["k_lag"],
            "one_global": fold["src"] * fold["global_scalar"] * fold["k_lag"],
            "b0": fold["src"],
            "rtm": rtm.get("rtm", np.full(len(test), np.nan)),
            "rtm_plus_league": rtm.get("rtm_plus_league", np.full(len(test), np.nan)),
            # Application studies (translation-application-studies-preregistration-
            # 2026-09-06.md, Study B): the player's own history beside the arms.
            # Additive -- nothing above reads these two columns.
            "prior_mean_pir36": test.prior_mean_pir36.to_numpy(dtype=float)
            if "prior_mean_pir36" in test
            else np.nan,
            "above_own_prior": test.above_own_prior.to_numpy()
            if "above_own_prior" in test
            else np.nan,
        }
    )
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out-dir", type=Path, default=_DEFAULT_OUT)
    ap.add_argument(
        "--rows-out",
        type=Path,
        default=None,
        help="write every fold's test rows with every arm's prediction "
        "(parquet). The pre-lock program's studies read this file.",
    )
    ap.add_argument(
        "--continental-source",
        choices=vh.blf.CONTINENTAL_SOURCES,
        default=vh.blf.DEFAULT_CONTINENTAL_SOURCE,
        help="api (Amendment 4 default) or proballers (the 2026-08-21 record)",
    )
    args = ap.parse_args(argv)
    args.out_dir.mkdir(parents=True, exist_ok=True)

    games, pairs = vh.load_corpus(args.continental_source)
    switch, _ = vh.build_switchers(games)
    cohorts = switch[switch.was_cont == 0]
    cohorts = cohorts[~cohorts.league_src.isin(vh.EXCLUDED_SOURCE)]
    cohorts = cohorts[cohorts.pir_per36_src > 0]
    print(f"[corpus] newcomer cohort rows across all seasons: {len(cohorts)}")

    fits = [one_season(pairs, cohorts, s) for s in SEASONS]
    for f in fits:
        f["rtm_arms"] = _fit_rtm_arms(f)
    if args.rows_out is not None:
        all_rows = pd.concat([fold_rows(f) for f in fits], ignore_index=True)
        args.rows_out.parent.mkdir(parents=True, exist_ok=True)
        all_rows.to_parquet(args.rows_out, index=False)
        print(
            f"[rows] wrote {len(all_rows)} test rows across {len(fits)} folds "
            f"→ {args.rows_out}"
        )

    rows = []
    for f in fits:
        per_league = f["src"] * f["multiplier"] * f["k_lag"]
        one_global = f["src"] * f["global_scalar"] * f["k_lag"]
        d, lo, hi = paired_cluster_bootstrap(
            per_league, one_global, f["y"], f["clusters"]
        )
        d0, lo0, _ = paired_cluster_bootstrap(
            per_league, f["src"], f["y"], f["clusters"]
        )
        rows.append(
            {
                "season": f["season"],
                "n": f["n"],
                "k_lag": round(f["k_lag"], 4),
                "tau_euroleague": round(f["tau"].get("euroleague", float("nan")), 4),
                "tau_eurocup": round(f["tau"].get("eurocup", float("nan")), 4),
                "collapsed_blocks": ",".join(f["collapsed_blocks"]),
                "mae_per_league": round(float(np.abs(per_league - f["y"]).mean()), 4),
                "mae_one_global": round(float(np.abs(one_global - f["y"]).mean()), 4),
                "mae_b0": round(float(np.abs(f["src"] - f["y"]).mean()), 4),
                "delta_vs_global": round(d, 4),
                "ci_lo": round(lo, 4),
                "ci_hi": round(hi, 4),
                "per_league_wins": bool(d > 0),
                "separable": bool(lo > 0),
                "beats_b0": bool(lo0 > 0),
                "mae_rtm": round(
                    float(np.abs(f["rtm_arms"]["rtm"] - f["y"]).mean()), 4
                ),
                "mae_rtm_plus_league": round(
                    float(np.abs(f["rtm_arms"]["rtm_plus_league"] - f["y"]).mean()), 4
                ),
                **{
                    f"r2_{k}": round(v["r2"], 4)
                    for k, v in arm_metrics(
                        f["y"],
                        {
                            "per_league": per_league,
                            "one_global": one_global,
                            "b0": f["src"],
                            "rtm": f["rtm_arms"]["rtm"],
                            "rtm_plus_league": f["rtm_arms"]["rtm_plus_league"],
                        },
                    ).items()
                },
            }
        )
        print(
            f"[wf {f['season']}] n={f['n']:4d} K={f['k_lag']:.4f} "
            f"per_league={rows[-1]['mae_per_league']:.4f} "
            f"global={rows[-1]['mae_one_global']:.4f} "
            f"delta={d:+.4f} CI [{lo:+.4f},{hi:+.4f}] separable={lo > 0}"
        )

    per_season = pd.DataFrame(rows)
    wins = int(per_season.per_league_wins.sum())
    sep = int(per_season.separable.sum())
    print(
        f"[seasons] per-league beats global in {wins}/{len(per_season)}, "
        f"separable in {sep}/{len(per_season)}"
    )

    # --- pooled across every walk-forward season: no season informs its own fit --
    def stack(key_fn) -> np.ndarray:
        return np.concatenate([key_fn(f) for f in fits])

    y = stack(lambda f: f["y"])
    clusters = stack(
        lambda f: np.char.add(f"{f['season']}|", f["clusters"].astype(str))
    )
    per_league = stack(lambda f: f["src"] * f["multiplier"] * f["k_lag"])
    one_global = stack(lambda f: f["src"] * f["global_scalar"] * f["k_lag"])
    b0 = stack(lambda f: f["src"])
    rtm = stack(lambda f: f["rtm_arms"]["rtm"])
    rtm_league = stack(lambda f: f["rtm_arms"]["rtm_plus_league"])

    d, lo, hi = paired_cluster_bootstrap(per_league, one_global, y, clusters)
    d0, lo0, hi0 = paired_cluster_bootstrap(per_league, b0, y, clusters)
    pooled_metrics = arm_metrics(
        y,
        {
            "per_league": per_league,
            "one_global": one_global,
            "b0": b0,
            "rtm": rtm,
            "rtm_plus_league": rtm_league,
        },
    )
    ceiling = r2_ceiling(
        games, float(stack(lambda f: f["test_rows"].games_dest.to_numpy()).mean())
    )
    print(
        "[pooled R2] "
        + " ".join(f"{k}={v['r2']:+.4f}" for k, v in pooled_metrics.items())
        + f" | ceiling_R2={ceiling['ceiling_r2_at_mean_games']:.4f} "
        f"at {ceiling['mean_dest_games_scored']:.1f} dest games"
    )
    print(
        f"[pooled] n={len(y)} clusters={len(np.unique(clusters))} "
        f"per_league={np.abs(per_league - y).mean():.4f} "
        f"global={np.abs(one_global - y).mean():.4f} b0={np.abs(b0 - y).mean():.4f}"
    )
    print(
        f"[pooled] per-league vs global: delta={d:+.4f} CI [{lo:+.4f},{hi:+.4f}] "
        f"excludes_zero={lo > 0}"
    )
    print(
        f"[pooled] per-league vs B0:     delta={d0:+.4f} CI [{lo0:+.4f},{hi0:+.4f}] "
        f"excludes_zero={lo0 > 0}"
    )

    # --- the comparator that decides whether the league table earns its place --
    # A 22-cell table must beat a model that uses NO league information, not just
    # one constant. It does not: this contrast is a tie. What survives is that the
    # two are complementary, which the next two contrasts establish.
    dr, lor, hir = paired_cluster_bootstrap(per_league, rtm, y, clusters)
    dcr, locr, hicr = paired_cluster_bootstrap(rtm_league, rtm, y, clusters)
    dcp, locp, hicp = paired_cluster_bootstrap(rtm_league, per_league, y, clusters)
    print(
        f"[pooled] rtm={np.abs(rtm - y).mean():.4f} "
        f"rtm_plus_league={np.abs(rtm_league - y).mean():.4f}"
    )
    print(
        f"[pooled] per-league vs RTM:      delta={dr:+.4f} CI [{lor:+.4f},{hir:+.4f}] "
        f"excludes_zero={lor > 0 or hir < 0}"
    )
    print(
        f"[pooled] RTM+league vs RTM:      delta={dcr:+.4f} "
        f"CI [{locr:+.4f},{hicr:+.4f}] excludes_zero={locr > 0}"
    )
    print(
        f"[pooled] RTM+league vs per-league: delta={dcp:+.4f} "
        f"CI [{locp:+.4f},{hicp:+.4f}] excludes_zero={locp > 0}"
    )
    assert locr > 0, (
        "the combined arm no longer beats RTM alone -- league identity adds "
        "nothing once regression to the mean is modelled, and the paper claim fails"
    )

    # --- control 1: is the gain the league MAPPING, or just dispersion? ---------
    rng = np.random.default_rng(7)
    null = np.empty(N_SHUFFLE)
    for i in range(N_SHUFFLE):
        shuffled = np.concatenate(
            [f["src"] * rng.permutation(f["multiplier"]) * f["k_lag"] for f in fits]
        )
        null[i] = np.abs(one_global - y).mean() - np.abs(shuffled - y).mean()
    beat = int((null > d).sum())
    print(
        f"[control shuffle] {N_SHUFFLE} reps: mean delta={null.mean():+.4f}, "
        f"p95={np.percentile(null, 95):+.4f}, reps beating the real delta={beat}"
    )
    assert beat == 0, (
        "shuffled factors matched the real assignment -- gain is not the mapping"
    )

    # --- control 3: is the COMBINED gain the mapping, or just an extra column? -
    # The combined arm has one more degree of freedom than RTM, which can improve
    # fit on its own. Permute the league->multiplier assignment and REFIT, so the
    # extra column survives and only its meaning is destroyed.
    rng3 = np.random.default_rng(11)
    mae_rtm = float(np.abs(rtm - y).mean())
    real_gain = mae_rtm - float(np.abs(rtm_league - y).mean())
    null3 = np.empty(N_SHUFFLE)
    for i in range(N_SHUFFLE):
        shuffled_arms = [
            _fit_rtm_arms(
                f,
                multiplier=rng3.permutation(
                    np.unique(f["multiplier_fn"](f["train_rows"]))
                ),
            )["rtm_plus_league"]
            for f in fits
        ]
        null3[i] = mae_rtm - float(np.abs(np.concatenate(shuffled_arms) - y).mean())
    beat3 = int((null3 >= real_gain).sum())
    print(
        f"[control combined-shuffle] {N_SHUFFLE} reps: real gain={real_gain:+.4f}, "
        f"shuffled mean={null3.mean():+.4f}, p95={np.percentile(null3, 95):+.4f}, "
        f"reps reaching real={beat3}"
    )
    assert beat3 == 0, (
        "a shuffled league mapping matched the combined arm's gain -- the joint "
        "result is an extra degree of freedom, not the league mapping"
    )

    # --- control 2: does the gain depend on the level correction at all? -------
    pl_nok = stack(lambda f: f["src"] * f["multiplier"])
    gl_nok = stack(lambda f: f["src"] * f["global_scalar"])
    dn, lon, hin = paired_cluster_bootstrap(pl_nok, gl_nok, y, clusters)
    print(
        f"[control no-K] per-league vs global with K=1: delta={dn:+.4f} "
        f"CI [{lon:+.4f},{hin:+.4f}] excludes_zero={lon > 0}"
    )

    per_season.to_csv(args.out_dir / "walkforward_per_season.csv", index=False)
    summary = {
        "continental_source": args.continental_source,
        "n_pairs": int(len(pairs)),
        "folds_with_collapsed_block": [
            f["season"] for f in fits if f["collapsed_blocks"]
        ],
        "seasons": list(SEASONS),
        "n_pooled": int(len(y)),
        "n_clusters": int(len(np.unique(clusters))),
        "seasons_per_league_wins": wins,
        "seasons_separable": sep,
        "pooled": {
            "mae_per_league": float(np.abs(per_league - y).mean()),
            "mae_one_global": float(np.abs(one_global - y).mean()),
            "mae_b0": float(np.abs(b0 - y).mean()),
            "delta_vs_global": d,
            "ci": [lo, hi],
            "delta_vs_b0": d0,
            "ci_b0": [lo0, hi0],
            # ATI-2955 item 1: R² per arm, with the ceiling beside it (§6)
            "r2": {k: v["r2"] for k, v in pooled_metrics.items()},
            "rmse": {k: v["rmse"] for k, v in pooled_metrics.items()},
            "ceiling": ceiling,
        },
        "control_shuffle": {
            "n_reps": N_SHUFFLE,
            "mean_delta": float(null.mean()),
            "p95": float(np.percentile(null, 95)),
            "reps_beating_real": beat,
        },
        "rtm_comparator": {
            "mae_rtm": float(np.abs(rtm - y).mean()),
            "mae_rtm_plus_league": float(np.abs(rtm_league - y).mean()),
            "per_league_vs_rtm": {
                "delta": dr,
                "ci": [lor, hir],
                "separable": bool(lor > 0 or hir < 0),
            },
            "rtm_plus_league_vs_rtm": {
                "delta": dcr,
                "ci": [locr, hicr],
                "separable": bool(locr > 0),
            },
            "rtm_plus_league_vs_per_league": {
                "delta": dcp,
                "ci": [locp, hicp],
                "separable": bool(locp > 0),
            },
        },
        "control_combined_shuffle": {
            "n_reps": N_SHUFFLE,
            "real_gain": float(real_gain),
            "mean_delta": float(null3.mean()),
            "p95": float(np.percentile(null3, 95)),
            "reps_reaching_real": beat3,
        },
        "control_no_level_correction": {
            "delta_vs_global": dn,
            "ci": [lon, hin],
            "separable": bool(lon > 0),
        },
    }
    (args.out_dir / "walkforward_summary.json").write_text(
        json.dumps(summary, indent=1, default=float)
    )
    print(
        f"[done] wrote walkforward_per_season.csv walkforward_summary.json "
        f"to {args.out_dir}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
