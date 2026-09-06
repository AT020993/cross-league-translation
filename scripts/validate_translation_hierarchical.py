"""Hierarchical translation arm: P4's model fitted as ONE model, scored walk-forward.

Comparator only. Nothing here touches the shipped basis, the lock, or any
pre-registered gate; it answers one question the propositions note left open:

    The shipped pipeline fits `log rate = alpha_p + beta_L + eps` in two
    disconnected stages -- a 20-cell ratio table with empirical-Bayes shrinkage
    for beta, then a separate four-column OLS for regression to the mean. What
    does the SAME model, fitted jointly with a player random effect, score on
    the same 674 walk-forward transfers?

Model (Proposition 4 of ``translation-propositions-2026-09-04.md``)::

    log rate_{p,L,t} = alpha_p + beta_L + eps_{p,L,t}
    alpha_p ~ N(mu, tau^2)            (player ability)
    eps     ~ N(0, sigma^2 / games)   (game-sampling noise; Proposition 3)

Prediction for a transfer of player p into destination D in season S::

    yhat = exp( E[alpha_p | every row of p with season < S] + beta_D )

The posterior mean of ``alpha_p`` shrinks the player's own league-adjusted
history toward ``mu`` in proportion to ``tau^2 / (tau^2 + sigma^2 / games)``
-- that shrinkage IS regression to the mean, and ``beta_D`` IS the league
level. No coefficient is fitted on the target. The primary arm was declared
before the first run (see ``PRIMARY`` below); everything else is printed as an
alternative and is not the claim.

Walk-forward discipline is the validator's: for destination season S, beta,
the variance components and every player's history use rows with season < S
only. The five shipped arm MAEs must reproduce ``walkforward_summary.json`` to
1e-6 or the script stops -- the same gate as the propositions generator.

Writes ``hierarchical_summary.json`` and ``hierarchical_rows.parquet`` to
``--out-dir`` (default ``data/processed/translation``).
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

import scripts.instantiate_translation_propositions as itp  # noqa: E402
import scripts.validate_translation_holdout as vh  # noqa: E402
import scripts.validate_translation_walkforward as wf  # noqa: E402

_DEFAULT_OUT = REPO / "data" / "processed" / "translation"

#: Declared BEFORE the first corpus run (2026-09-05): league effects from the
#: same-season pairs only (the paper's identification), equal weight on every
#: prior season, log scale. The alternatives below are sensitivity, not choices.
#: One thing changed after run 2 and is disclosed in the note: the tau^2 moment
#: estimator (``TAU2_ESTIMATOR``), replaced because an ALTERNATIVE arm collapsed;
#: the primary's tau^2 never floored under either form, and both are runnable.
PRIMARY = "hier"
ALTERNATIVES = ("hier_joint_beta", "hier_recency1", "hier_additive", "hier_plus_rtm")
#: hier_no_league drops beta entirely (level AND mapping); hier_tier_beta keeps
#: the domestic->continental level but replaces every domestic beta by their
#: pair-weighted mean, so ``hier - hier_tier_beta`` is per-league resolution
#: alone -- the analogue of per_league vs one_global in the walk-forward.
DECOMPOSITION = ("hier_no_league", "hier_tier_beta")
#: A stint shorter than one full game of minutes gives a per-36 rate that is
#: mostly noise on the log scale; the floor keeps a scoreless stint finite.
MIN_STINT_MINUTES = 36.0
RATE_FLOOR = 0.1
#: tau^2 at or below this is a collapsed fit: every player shrinks to the grand mean.
TAU2_FLOOR = 1e-6
#: Which tau^2 moment estimator ``variance_components`` uses. Run 1 and run 2
#: (2026-09-05) used ``naive``; the recency arm then floored (see the function's
#: docstring), and ``dl`` became the default. Both stay runnable so both records
#: come from committed code: ``--tau2-estimator naive`` reproduces run 2.
TAU2_ESTIMATORS = ("dl", "naive")
TAU2_ESTIMATOR = "dl"
N_SHUFFLE = 200
#: A cohort season whose prior pairs are fewer than this has no usable beta.
MIN_PRIOR_PAIRS = 100
SEED = 0


# ------------------------------------------------------------------ the model
def player_season_league_rows(games: pd.DataFrame) -> pd.DataFrame:
    """One row per (player, season, league) stint: games, minutes, EFF per 36."""
    obs = (
        games[games.minutes > 0]
        .groupby(["player_name", "season", "league"])
        .agg(
            games=("game_id", "nunique"), minutes=("minutes", "sum"), pir=("pir", "sum")
        )
        .reset_index()
    )
    obs = obs[obs.minutes >= MIN_STINT_MINUTES].copy()
    obs["rate"] = 36.0 * obs.pir / obs.minutes
    return obs


def league_effects_from_pairs(pairs: pd.DataFrame, pin: str) -> dict[str, float]:
    """Two-way fixed effects on the same-season dual-tier pairs (P4, log scale)."""
    pa = pairs[pairs.pir_per36_src > 0]
    leagues = sorted(set(pa.league_src) | set(pa.league_dest))
    X = itp.league_incidence(pa.league_src, pa.league_dest, leagues)
    y = np.log(pa.pir_per36_dest.clip(lower=RATE_FLOOR) / pa.pir_per36_src).to_numpy()
    w = np.minimum(pa.minutes_src, pa.minutes_dest).to_numpy(float)
    beta = itp.solve_two_way_fe(X, y, w, leagues, pin)
    return dict(zip(leagues, map(float, beta)))


def league_effects_joint(obs: pd.DataFrame, value: np.ndarray, pin: str) -> dict:
    """Within-player demeaned WLS on every stint: beta identified through any
    player seen in two leagues, same season or not (the confounded route the
    paper avoids; printed as the alternative)."""
    d = obs.assign(v=value)
    d = d[d.groupby("player_name").league.transform("nunique") >= 2]
    leagues = sorted(d.league.unique())
    keep = [lg for lg in leagues if lg != pin]
    idx = {lg: i for i, lg in enumerate(keep)}
    w = d.games.to_numpy(float)
    X = np.zeros((len(d), len(keep)))
    col = d.league.map(idx)
    m = col.notna().to_numpy()
    X[np.flatnonzero(m), col[m].astype(int).to_numpy()] = 1.0
    # weighted within-player demeaning removes alpha_p exactly
    g = d.player_name.to_numpy()
    y = d.v.to_numpy(float)
    Wp = pd.Series(w).groupby(g).transform("sum").to_numpy()
    Xbar = np.vstack(
        [
            pd.Series(w * X[:, j]).groupby(g).transform("sum").to_numpy() / Wp
            for j in range(X.shape[1])
        ]
    ).T
    ybar = pd.Series(w * y).groupby(g).transform("sum").to_numpy() / Wp
    sw = np.sqrt(w)[:, None]
    bk, *_ = np.linalg.lstsq((X - Xbar) * sw, (y - ybar) * sw[:, 0], rcond=None)
    out = {pin: 0.0}
    out.update(dict(zip(keep, map(float, bk))))
    return out


def collapse_domestic_to_tier(beta: dict, pairs: pd.DataFrame) -> dict:
    """Every domestic league effect replaced by their pair-count-weighted mean.

    Keeps the domestic -> continental level (and the EuroLeague/EuroCup gap),
    removes per-league resolution. Leagues without pairs keep their own beta.
    """
    counts = pairs.league_src.value_counts()
    dom = [lg for lg in beta if lg not in vh.blf.CONTINENTAL and lg in counts.index]
    if not dom:
        return dict(beta)
    w = np.array([counts[lg] for lg in dom], float)
    mean = float(np.sum(w * np.array([beta[lg] for lg in dom])) / w.sum())
    out = dict(beta)
    out.update({lg: mean for lg in dom})
    return out


def variance_components(resid: np.ndarray, w: np.ndarray, players: np.ndarray) -> dict:
    """(mu, tau^2, sigma^2) under Var(eps_i) = sigma^2 / w_i, by moments.

    sigma^2 from the within-player weighted spread, E[sum_i w_i (r_i - rbar_p)^2]
    = sigma^2 (n_p - 1). tau^2 by the DerSimonian-Laird moment estimator with
    per-player precision v_p = W_p / sigma^2: tau^2 = (Q - (k - 1)) /
    (sum v - sum v^2 / sum v), Q = sum v (rbar_p - mu_v)^2. The first run
    (2026-09-05) used the naive form Var_p(rbar_p) - mean_p(sigma^2 / W_p); with
    recency weights a few players carry W_p near zero, the mean of sigma^2 / W_p
    explodes and tau^2 floors -- every player then shrinks to the grand mean.
    ``tau2_floored`` prints so that collapse is never silent again (cf. T9).
    """
    d = pd.DataFrame({"r": resid, "w": w, "p": players})
    grp = d.groupby("p")
    W = grp.w.sum()
    rbar = (d.w * d.r).groupby(d.p).sum() / W
    n = grp.size()
    d["rbar"] = d.p.map(rbar)
    within = float(np.sum(d.w * (d.r - d.rbar) ** 2))
    dof = float((n - 1).sum())
    sigma2 = within / dof if dof > 0 else float("nan")
    v = W / sigma2
    mu_v = float(np.sum(v * rbar) / np.sum(v))
    q = float(np.sum(v * (rbar - mu_v) ** 2))
    k = len(rbar)
    denom = float(np.sum(v) - np.sum(v**2) / np.sum(v))
    if TAU2_ESTIMATOR == "dl":
        tau2_raw = (q - (k - 1)) / denom if denom > 0 else float("nan")
    else:  # the run-1/run-2 form, kept so that record reproduces
        tau2_raw = float(rbar.var(ddof=1) - np.mean(sigma2 / W))
    floored = not (tau2_raw > TAU2_FLOOR)
    tau2 = TAU2_FLOOR if floored else float(tau2_raw)
    # prior mean under the fitted components: precision 1 / (tau^2 + sigma^2 / W)
    prec = 1.0 / (tau2 + sigma2 / W)
    mu = float(np.sum(prec * rbar) / np.sum(prec))
    return {
        "mu": mu,
        "tau2": tau2,
        "tau2_raw": float(tau2_raw),
        "tau2_floored": bool(floored),
        "sigma2_per_game": sigma2,
        "n_players": int(k),
        "n_players_multi_stint": int((n >= 2).sum()),
        "_rbar": rbar,
        "_W": W,
    }


def posterior_alpha(vc: dict, players: pd.Series) -> np.ndarray:
    """E[alpha_p | history] = mu + kappa_p (rbar_p - mu).

    kappa_p = tau^2 / (tau^2 + sigma^2 / W_p); the shrinkage IS regression to the mean.
    """
    rbar = players.map(vc["_rbar"]).to_numpy(float)
    W = players.map(vc["_W"]).to_numpy(float)
    kappa = vc["tau2"] / (vc["tau2"] + vc["sigma2_per_game"] / W)
    return vc["mu"] + kappa * (rbar - vc["mu"])


def fit_hierarchical(
    obs: pd.DataFrame,
    pairs: pd.DataFrame,
    season: int,
    *,
    beta_source: str = "pairs",
    half_life: float | None = None,
    scale: str = "log",
    no_league: bool = False,
    tier_beta: bool = False,
    pin: str = itp.PIN_LEAGUE,
) -> dict:
    """Fit beta, the variance components and every player's posterior on rows < season.

    Each keyword selects one printed alternative; the defaults are the declared primary.
    """
    train = obs[obs.season < season].copy()
    value = (
        np.log(train.rate.clip(lower=RATE_FLOOR)).to_numpy()
        if scale == "log"
        else train.rate.to_numpy(float)
    )
    if no_league:
        beta = {lg: 0.0 for lg in train.league.unique()}
    elif beta_source == "pairs":
        pp = pairs[pairs.season < season]
        if scale == "log":
            beta = league_effects_from_pairs(pp, pin)
        else:  # additive league offsets from the same pairs
            pa = pp[pp.pir_per36_src > 0]
            leagues = sorted(set(pa.league_src) | set(pa.league_dest))
            X = itp.league_incidence(pa.league_src, pa.league_dest, leagues)
            y = (pa.pir_per36_dest - pa.pir_per36_src).to_numpy(float)
            w = np.minimum(pa.minutes_src, pa.minutes_dest).to_numpy(float)
            beta = dict(
                zip(leagues, map(float, itp.solve_two_way_fe(X, y, w, leagues, pin)))
            )
    else:
        beta = league_effects_joint(train, value, pin)
    if tier_beta:
        beta = collapse_domestic_to_tier(beta, pairs[pairs.season < season])
    known = train.league.isin(beta.keys()).to_numpy()
    train, value = train[known], value[known]
    w = train.games.to_numpy(float)
    if half_life is not None:
        w = w * 0.5 ** ((season - 1 - train.season.to_numpy(float)) / half_life)
    resid = value - train.league.map(beta).to_numpy(float)
    vc = variance_components(resid, w, train.player_name.to_numpy())
    return {"season": season, "beta": beta, "vc": vc, "scale": scale}


def predict(fit: dict, rows: pd.DataFrame) -> np.ndarray:
    """Destination-season rate for each transfer row from its player's posterior."""
    beta = fit["beta"]
    vc = fit["vc"]
    alpha = posterior_alpha(vc, rows.player_name)
    # a player with no usable history falls back to the source stint alone
    miss = ~np.isfinite(alpha)
    if miss.any():
        src_val = (
            np.log(rows.pir_per36_src.clip(lower=RATE_FLOOR))
            if fit["scale"] == "log"
            else rows.pir_per36_src
        ).to_numpy(float) - rows.league_src.map(beta).fillna(0.0).to_numpy(float)
        W = rows.games_src.to_numpy(float)
        kappa = vc["tau2"] / (vc["tau2"] + vc["sigma2_per_game"] / W)
        alpha = np.where(miss, vc["mu"] + kappa * (src_val - vc["mu"]), alpha)
    lin = alpha + rows.league_dest.map(beta).to_numpy(float)
    # the MAE-optimal point of a lognormal is its median: exp(mu), no correction
    return np.exp(lin) if fit["scale"] == "log" else lin


# --------------------------------------------------------------------- folds
def build_folds(
    continental_source: str,
) -> tuple[pd.DataFrame, pd.DataFrame, list[dict]]:
    """Corpus, pairs and the validator's six folds, as the propositions generator."""
    games, pairs = vh.load_corpus(continental_source)
    with contextlib.redirect_stdout(io.StringIO()):
        switch, _ = vh.build_switchers(games)
    cohorts = switch[switch.was_cont == 0]
    cohorts = cohorts[~cohorts.league_src.isin(vh.EXCLUDED_SOURCE)]
    cohorts = cohorts[cohorts.pir_per36_src > 0]
    fits = [wf.one_season(pairs, cohorts, s) for s in wf.SEASONS]
    for f in fits:
        f["rtm_arms"] = wf._fit_rtm_arms(f)
    return games, pairs, fits


def hier_plus_rtm(
    fold: dict, hier_train: np.ndarray, hier_test: np.ndarray
) -> np.ndarray:
    """The RTM OLS with the hierarchical prediction as one more column."""
    train, test = fold["train_rows"], fold["test_rows"]
    ok = np.isfinite(hier_train)
    y = train.pir_per36_dest.to_numpy(float)[ok]
    beta, *_ = np.linalg.lstsq(wf._rtm_design(train[ok], hier_train[ok]), y, rcond=None)
    return wf._rtm_design(test, hier_test) @ beta


def score_fold(obs: pd.DataFrame, pairs: pd.DataFrame, fold: dict) -> pd.DataFrame:
    """Every hierarchical arm on one fold's test rows, beside the five shipped arms."""
    s = fold["season"]
    rows = wf.fold_rows(fold)
    test = fold["test_rows"]
    fits = {
        "hier": fit_hierarchical(obs, pairs, s),
        "hier_joint_beta": fit_hierarchical(obs, pairs, s, beta_source="joint"),
        "hier_recency1": fit_hierarchical(obs, pairs, s, half_life=1.0),
        "hier_additive": fit_hierarchical(obs, pairs, s, scale="additive"),
        "hier_no_league": fit_hierarchical(obs, pairs, s, no_league=True),
        "hier_tier_beta": fit_hierarchical(obs, pairs, s, tier_beta=True),
    }
    for name, fit in fits.items():
        rows[name] = predict(fit, test)
        if fit["vc"]["tau2_floored"]:
            print(
                f"[T9 hier {s}] WARNING {name}: tau^2 floored "
                f"(raw {fit['vc']['tau2_raw']:.2e}) -- the arm predicts the grand mean"
            )
    # hier as a feature: the train rows need a prediction from THEIR OWN prior seasons
    train = fold["train_rows"]
    hier_train = np.full(len(train), np.nan)
    for sd, g in train.groupby("season_dest"):
        # the earliest cohorts have no prior pairs to fit beta on: they stay NaN
        # and drop out of the hier_plus_rtm fit only (MIN_PRIOR_PAIRS below)
        if int((pairs.season < int(sd)).sum()) < MIN_PRIOR_PAIRS:
            continue
        f_sd = fit_hierarchical(obs, pairs, int(sd))
        hier_train[train.index.get_indexer(g.index)] = predict(f_sd, g)
    rows["hier_plus_rtm"] = hier_plus_rtm(fold, hier_train, rows["hier"].to_numpy())
    rows["hier_plus_rtm_n_train"] = int(np.isfinite(hier_train).sum())
    rows.attrs[f"fit_{s}"] = {
        "beta_pairs_to_euroleague": {
            lg: round(float(np.exp(-b)), 4)
            for lg, b in fits["hier"]["beta"].items()
            if lg not in vh.blf.CONTINENTAL
        },
        "mu": fits["hier"]["vc"]["mu"],
        "tau2": fits["hier"]["vc"]["tau2"],
        "tau2_floored_by_arm": {
            name: f["vc"]["tau2_floored"] for name, f in fits.items()
        },
        "sigma2_per_game": fits["hier"]["vc"]["sigma2_per_game"],
        "n_players": fits["hier"]["vc"]["n_players"],
        "kappa_at_mean_games": float(
            fits["hier"]["vc"]["tau2"]
            / (
                fits["hier"]["vc"]["tau2"]
                + fits["hier"]["vc"]["sigma2_per_game"] / float(test.games_src.mean())
            )
        ),
    }
    return rows


def shuffled_league_control(
    obs: pd.DataFrame,
    pairs: pd.DataFrame,
    fits: list[dict],
    rows: pd.DataFrame,
    observed: float,
) -> dict:
    """Permute the domestic league effects (refit per fold) and re-score `hier`.

    Reports how many of N_SHUFFLE permutations reach the observed MAE gain over
    the tier-beta decomposition arm (same level, no mapping): a permutation
    preserves the level, so this is the mapping's own test. Not an assert: a
    comparator note reports.
    """
    rng = np.random.default_rng(SEED)
    base = {f["season"]: fit_hierarchical(obs, pairs, f["season"]) for f in fits}
    gains = np.empty(N_SHUFFLE)
    y = rows.y.to_numpy(float)
    tier_err = np.abs(rows.hier_tier_beta.to_numpy(float) - y).mean()
    for i in range(N_SHUFFLE):
        preds = []
        for f in fits:
            fit = dict(base[f["season"]])
            beta = dict(fit["beta"])
            dom = [lg for lg in beta if lg not in vh.blf.CONTINENTAL]
            vals = rng.permutation([beta[lg] for lg in dom])
            beta.update(dict(zip(dom, map(float, vals))))
            fit["beta"] = beta
            preds.append(predict(fit, f["test_rows"]))
        p = np.concatenate(preds)[rows.index.to_numpy()]
        gains[i] = tier_err - np.abs(p - y).mean()
    return {
        "observed_gain_vs_tier_beta": observed,
        "n_shuffles": N_SHUFFLE,
        "shuffles_reaching_observed": int((gains >= observed).sum()),
        "shuffle_mean_gain": float(gains.mean()),
        "shuffle_p95_gain": float(np.percentile(gains, 95)),
    }


def main(argv: list[str] | None = None) -> int:
    global TAU2_ESTIMATOR  # noqa: PLW0603
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out-dir", type=Path, default=_DEFAULT_OUT)
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
    ap.add_argument(
        "--skip-shuffle", action="store_true", help="omit the 200-rep control"
    )
    ap.add_argument(
        "--tau2-estimator",
        choices=TAU2_ESTIMATORS,
        default=TAU2_ESTIMATOR,
        help="dl (default since run 3) or naive (reproduces run 2)",
    )
    args = ap.parse_args(argv)
    TAU2_ESTIMATOR = args.tau2_estimator
    args.out_dir.mkdir(parents=True, exist_ok=True)
    summary_path = args.walkforward_summary or args.out_dir / "walkforward_summary.json"
    summary = json.loads(summary_path.read_text())
    assert summary["continental_source"] == args.continental_source

    games, pairs, fits = build_folds(args.continental_source)
    obs = player_season_league_rows(games)
    print(
        f"[obs] player-season-league stints "
        f"(>= {MIN_STINT_MINUTES:.0f} min): {len(obs)}"
    )

    per_fold = [score_fold(obs, pairs, f) for f in fits]
    rows = pd.concat(per_fold, ignore_index=True)
    fit_records = {k: v for r in per_fold for k, v in r.attrs.items()}
    keep = np.isfinite(rows.per_league)
    rows = rows[keep].reset_index(drop=True)
    maes = itp.assert_reproduces_walkforward(rows, summary)
    print("[folds] " + " ".join(f"{k}={v:.4f}" for k, v in maes.items()))

    y = rows.y.to_numpy(float)
    clusters = (rows.season.astype(str) + "|" + rows.cluster.astype(str)).to_numpy()
    arms = list(itp.ARMS) + [PRIMARY, *DECOMPOSITION, *ALTERNATIVES]
    pooled = wf.arm_metrics(y, {a: rows[a].to_numpy(float) for a in arms})
    for a in arms:
        print(f"[pooled] {a:18s} MAE={pooled[a]['mae']:.4f} R2={pooled[a]['r2']:+.4f}")

    def contrast(a: str, b: str) -> dict:
        d, lo, hi = wf.paired_cluster_bootstrap(
            rows[a].to_numpy(float), rows[b].to_numpy(float), y, clusters
        )
        print(f"[contrast] {a} vs {b}: delta={d:+.4f} CI [{lo:+.4f}, {hi:+.4f}]")
        return {"a": a, "b": b, "delta_mae_b_minus_a": d, "ci95": [lo, hi]}

    contrasts = {
        "hier_vs_rtm_plus_league": contrast("hier", "rtm_plus_league"),
        "hier_vs_per_league": contrast("hier", "per_league"),
        "hier_vs_rtm": contrast("hier", "rtm"),
        "hier_vs_one_global": contrast("hier", "one_global"),
        "hier_vs_b0": contrast("hier", "b0"),
        "hier_vs_hier_no_league": contrast("hier", "hier_no_league"),
        "hier_vs_hier_tier_beta": contrast("hier", "hier_tier_beta"),
        "hier_plus_rtm_vs_rtm_plus_league": contrast(
            "hier_plus_rtm", "rtm_plus_league"
        ),
        "hier_joint_beta_vs_hier": contrast("hier_joint_beta", "hier"),
        "hier_recency1_vs_hier": contrast("hier_recency1", "hier"),
        "hier_additive_vs_hier": contrast("hier_additive", "hier"),
        # the two alternatives that reach the combined arm's level, against it
        "hier_recency1_vs_rtm_plus_league": contrast(
            "hier_recency1", "rtm_plus_league"
        ),
        "hier_additive_vs_rtm_plus_league": contrast(
            "hier_additive", "rtm_plus_league"
        ),
    }
    per_season = (
        rows.assign(**{f"ae_{a}": np.abs(rows[a] - rows.y) for a in arms})
        .groupby("season")
        .agg(
            n=("y", "size"),
            hier_plus_rtm_n_train=("hier_plus_rtm_n_train", "first"),
            **{f"mae_{a}": (f"ae_{a}", "mean") for a in arms},
        )
        .reset_index()
    )
    print(per_season.round(4).to_string(index=False))

    control = None
    if not args.skip_shuffle:
        observed = pooled["hier_tier_beta"]["mae"] - pooled["hier"]["mae"]
        control = shuffled_league_control(obs, pairs, fits, rows, observed)
        print(
            f"[control] shuffled domestic league effects reach the observed gain "
            f"{observed:+.4f} in {control['shuffles_reaching_observed']}/{N_SHUFFLE}"
        )

    verdict = {
        "question": "does the joint hierarchical model beat the two-stage "
        "combined arm on MAE?",
        "hier_mae": pooled["hier"]["mae"],
        "rtm_plus_league_mae": pooled["rtm_plus_league"]["mae"],
        "hier_at_or_below_combined": bool(
            pooled["hier"]["mae"] <= pooled["rtm_plus_league"]["mae"]
        ),
        "ci_excludes_zero": bool(
            contrasts["hier_vs_rtm_plus_league"]["ci95"][0] > 0
            or contrasts["hier_vs_rtm_plus_league"]["ci95"][1] < 0
        ),
    }
    print(f"[verdict] {json.dumps(verdict)}")

    out = {
        "generated_by": "scripts/validate_translation_hierarchical.py",
        "continental_source": args.continental_source,
        "primary_arm_declared_before_run": PRIMARY,
        "tau2_estimator": TAU2_ESTIMATOR,
        "alternatives": list(ALTERNATIVES),
        "decomposition": list(DECOMPOSITION),
        "min_stint_minutes": MIN_STINT_MINUTES,
        "rate_floor": RATE_FLOOR,
        "n_pooled": int(len(rows)),
        "n_stints": int(len(obs)),
        "walkforward_mae_reproduced": maes,
        "pooled": pooled,
        "per_season": per_season.to_dict(orient="records"),
        "contrasts": contrasts,
        "fits": fit_records,
        "shuffled_league_control": control,
        "verdict": verdict,
    }
    (args.out_dir / "hierarchical_summary.json").write_text(
        json.dumps(out, indent=1, default=float)
    )
    rows.to_parquet(args.out_dir / "hierarchical_rows.parquet", index=False)
    print(
        "[done] wrote hierarchical_summary.json and hierarchical_rows.parquet "
        f"to {args.out_dir}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
