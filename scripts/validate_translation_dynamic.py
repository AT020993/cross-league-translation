"""Dynamic (random-walk) player ability in the translation model, scored walk-forward.

Pre-registered in ``docs/research/translation-dynamic-ability-preregistration-
2026-09-05.md``
(committed a62be01e, before this file existed). Comparator only: nothing here
touches the shipped basis, the lock, or any pre-registered gate of the 2026-27 set.

Model (additive scale, declared)::

    rate_{p,L,t} = alpha_{p,t} + beta_L + eps,   eps ~ N(0, sigma^2 / games)
    alpha_{p,t}  = alpha_{p,t-1} + eta,          eta ~ N(0, q * gap)
    alpha_{p,first} ~ N(mu, tau^2)

Every component is a closed-form moment estimator fitted on rows strictly
before the scored season S:

* beta      two-way fixed effects on the same-season dual-tier pairs (P4)
* sigma^2   from two stints of one player in ONE season (they share alpha_{p,t}):
            E[(r1 - r2)^2] = sigma^2 (1/W1 + 1/W2)
* q         from consecutive observed seasons of one player:
            E[(rbar_t - rbar_prev)^2] = q * gap + sigma^2 (1/W_t + 1/W_prev)
* mu, tau^2 DerSimonian-Laird on each player's first observed season

then a Kalman filter per player over seasons < S and the random-walk forecast
``E[alpha_{p,S}] = E[alpha_{p,S-1} | data]``; prediction
``yhat = E[alpha_{p,S}] + beta_D``.

The primary arm is ``dyn``. ``dyn_q0`` is the pre-registered filter-correctness
check (T1): run with the STATIC arm's own (mu, tau^2, sigma^2) and q = 0 the
filter must reproduce the static additive posterior exactly, which the script
asserts; with its own components it is reported against ``hier_additive`` as a
gap, not asserted (the two sigma^2 definitions differ by construction).

Writes ``dynamic_summary.json`` and ``dynamic_rows.parquet`` to ``--out-dir``.
"""

from __future__ import annotations

import argparse
import datetime
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

import scripts.instantiate_translation_propositions as itp  # noqa: E402
import scripts.validate_translation_hierarchical as vth  # noqa: E402
import scripts.validate_translation_holdout as vh  # noqa: E402
import scripts.validate_translation_walkforward as wf  # noqa: E402

_DEFAULT_OUT = REPO / "data" / "processed" / "translation"

PRIMARY = "dyn"
ALTERNATIVES = ("dyn_log", "dyn_q_half", "dyn_q_double")
CHECKS = ("dyn_q0",)
DECOMPOSITION = ("dyn_tier_beta",)
STATIC_COMPARATORS = ("hier_additive", "hier_recency1")
SELECTION_FOLDS = (2020, 2021, 2022, 2023, 2024)
CONFIRMATION_FOLD = 2025
FLOOR = 1e-6
T1_TOLERANCE_MAE = 0.05
T1_EXACT_TOLERANCE = 1e-8
N_SHUFFLE = 200
SEED = 0


# ------------------------------------------------------------ components
def league_effects(pairs: pd.DataFrame, scale: str, pin: str) -> dict[str, float]:
    """Two-way fixed effects on same-season pairs, additive or log."""
    pa = pairs[pairs.pir_per36_src > 0]
    leagues = sorted(set(pa.league_src) | set(pa.league_dest))
    X = itp.league_incidence(pa.league_src, pa.league_dest, leagues)
    if scale == "log":
        y = np.log(pa.pir_per36_dest.clip(lower=vth.RATE_FLOOR) / pa.pir_per36_src)
    else:
        y = pa.pir_per36_dest - pa.pir_per36_src
    w = np.minimum(pa.minutes_src, pa.minutes_dest).to_numpy(float)
    beta = itp.solve_two_way_fe(X, y.to_numpy(float), w, leagues, pin)
    return dict(zip(leagues, map(float, beta)))


def sigma2_from_shared_seasons(stints: pd.DataFrame) -> dict:
    """sigma^2 from the two largest stints of one player in one season.

    Both observe the same alpha_{p,t}, so E[(r1 - r2)^2] = sigma^2 (1/W1 + 1/W2).
    Ratio-of-sums moment estimator over every such (player, season).
    """
    keys = ["player_name", "season"]
    d = stints.sort_values(keys + ["w"], ascending=[True, True, False]).copy()
    d["k"] = d.groupby(keys).cumcount()
    two = d[d.groupby(keys).k.transform("max") >= 1]
    # both sides sorted by the same keys, so row i of `a` and of `b` share a season
    a = two[two.k == 0].sort_values(keys).reset_index(drop=True)
    b = two[two.k == 1].sort_values(keys).reset_index(drop=True)
    assert (a.player_name.to_numpy() == b.player_name.to_numpy()).all()
    assert (a.season.to_numpy() == b.season.to_numpy()).all()
    num = float(np.sum((a.r.to_numpy() - b.r.to_numpy()) ** 2))
    den = float(np.sum(1.0 / a.w.to_numpy() + 1.0 / b.w.to_numpy()))
    raw = num / den if den > 0 else float("nan")
    floored = not (raw > FLOOR)
    return {
        "sigma2_per_game": FLOOR if floored else raw,
        "sigma2_raw": raw,
        "sigma2_floored": bool(floored),
        "n_shared_season_pairs": int(len(a)),
    }


def season_means(stints: pd.DataFrame) -> pd.DataFrame:
    """One row per (player, season): precision-weighted mean r and total weight W."""
    g = stints.groupby(["player_name", "season"])
    out = pd.DataFrame(
        {
            "W": g.w.sum(),
            "rbar": (stints.w * stints.r)
            .groupby([stints.player_name, stints.season])
            .sum(),
        }
    ).reset_index()
    out["rbar"] = out.rbar / out.W
    return out.sort_values(["player_name", "season"]).reset_index(drop=True)


def q_from_consecutive_seasons(means: pd.DataFrame, sigma2: float) -> dict:
    """Innovation variance from consecutive observed seasons of the same player.

    E[(rbar_t - rbar_prev)^2] = q * gap + sigma^2 (1/W_t + 1/W_prev), gap in seasons.
    Ratio-of-sums: q = sum(d^2 - noise) / sum(gap).
    """
    m = means.copy()
    m["prev_r"] = m.groupby("player_name").rbar.shift(1)
    m["prev_W"] = m.groupby("player_name").W.shift(1)
    m["prev_s"] = m.groupby("player_name").season.shift(1)
    m = m[m.prev_r.notna()]
    gap = (m.season - m.prev_s).to_numpy(float)
    d2 = (m.rbar - m.prev_r).to_numpy(float) ** 2
    noise = sigma2 * (1.0 / m.W.to_numpy(float) + 1.0 / m.prev_W.to_numpy(float))
    raw = float(np.sum(d2 - noise) / np.sum(gap)) if len(m) else float("nan")
    floored = not (raw > FLOOR)
    return {
        "q": FLOOR if floored else raw,
        "q_raw": raw,
        "q_floored": bool(floored),
        "n_consecutive_pairs": int(len(m)),
        "mean_gap": float(gap.mean()) if len(m) else float("nan"),
    }


def dl_prior(first: pd.DataFrame, sigma2: float) -> dict:
    """DerSimonian-Laird (mu, tau^2) on each player's first observed season."""
    v = first.W.to_numpy(float) / sigma2
    r = first.rbar.to_numpy(float)
    mu_v = float(np.sum(v * r) / np.sum(v))
    qstat = float(np.sum(v * (r - mu_v) ** 2))
    k = len(r)
    denom = float(np.sum(v) - np.sum(v**2) / np.sum(v))
    raw = (qstat - (k - 1)) / denom if denom > 0 else float("nan")
    floored = not (raw > FLOOR)
    tau2 = FLOOR if floored else float(raw)
    prec = 1.0 / (tau2 + sigma2 / first.W.to_numpy(float))
    mu = float(np.sum(prec * r) / np.sum(prec))
    return {
        "mu": mu,
        "tau2": tau2,
        "tau2_raw": float(raw),
        "tau2_floored": bool(floored),
    }


def kalman_forecast(
    means: pd.DataFrame, season: int, *, mu: float, tau2: float, sigma2: float, q: float
) -> pd.DataFrame:
    """Filter each player over observed seasons < `season`, forecast to `season`.

    Vectorised over players: the k-th observed season of every player is one
    update step, so the loop runs over at most the number of seasons in the
    corpus. Returns one row per player: m (E[alpha_{p,season}]), P (its
    variance), the last observed season and the number of seasons used.
    """
    d = means.sort_values(["player_name", "season"]).reset_index(drop=True)
    d["k"] = d.groupby("player_name").cumcount()
    players = d.player_name.unique()
    idx = {p: i for i, p in enumerate(players)}
    pi = d.player_name.map(idx).to_numpy()
    n = len(players)
    m = np.full(n, float(mu))
    P = np.full(n, float(tau2))
    prev = np.full(n, np.nan)
    count = np.zeros(n, int)
    for k in range(int(d.k.max()) + 1):
        rows = d[d.k == k]
        i = pi[rows.index.to_numpy()]
        s_k = rows.season.to_numpy(float)
        gap = np.where(np.isnan(prev[i]), 0.0, s_k - prev[i])
        P_i = P[i] + q * gap
        R = sigma2 / rows.W.to_numpy(float)
        K = P_i / (P_i + R)
        m[i] = m[i] + K * (rows.rbar.to_numpy(float) - m[i])
        P[i] = (1.0 - K) * P_i
        prev[i] = s_k
        count[i] += 1
    P = P + q * (season - prev)
    return pd.DataFrame(
        {
            "player_name": players,
            "m": m,
            "P": P,
            "last_season": prev,
            "n_seasons": count,
        }
    )


def fit_dynamic(
    obs: pd.DataFrame,
    pairs: pd.DataFrame,
    season: int,
    *,
    scale: str = "additive",
    q_mult: float = 1.0,
    q_zero: bool = False,
    tier_beta: bool = False,
    components: dict | None = None,
    pin: str = itp.PIN_LEAGUE,
) -> dict:
    """Every component on rows strictly before `season`, then the forecast.

    `components` overrides (mu, tau2, sigma2_per_game) with another arm's values
    -- used only by the T1 filter-correctness check.
    """
    train = obs[obs.season < season].copy()
    value = (
        np.log(train.rate.clip(lower=vth.RATE_FLOOR)).to_numpy()
        if scale == "log"
        else train.rate.to_numpy(float)
    )
    pp = pairs[pairs.season < season]
    beta = league_effects(pp, scale, pin)
    if tier_beta:
        beta = vth.collapse_domestic_to_tier(beta, pp)
    known = train.league.isin(beta.keys()).to_numpy()
    train, value = train[known], value[known]
    stints = pd.DataFrame(
        {
            "player_name": train.player_name.to_numpy(),
            "season": train.season.to_numpy(),
            "w": train.games.to_numpy(float),
            "r": value - train.league.map(beta).to_numpy(float),
        }
    )
    sig = sigma2_from_shared_seasons(stints)
    means = season_means(stints)
    qq = q_from_consecutive_seasons(means, sig["sigma2_per_game"])
    first = means.groupby("player_name").head(1)
    prior = dl_prior(first, sig["sigma2_per_game"])
    comp = {
        "mu": prior["mu"],
        "tau2": prior["tau2"],
        "sigma2_per_game": sig["sigma2_per_game"],
    }
    if components is not None:
        comp = {k: float(components[k]) for k in comp}
    q = 0.0 if q_zero else qq["q"] * q_mult
    fc = kalman_forecast(
        means,
        season,
        mu=comp["mu"],
        tau2=comp["tau2"],
        sigma2=comp["sigma2_per_game"],
        q=q,
    )
    return {
        "season": season,
        "scale": scale,
        "beta": beta,
        "q": q,
        "q_info": qq,
        "sigma2_info": sig,
        "prior": prior,
        "components_used": comp,
        "_forecast": fc.set_index("player_name"),
    }


def predict(fit: dict, rows: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    """(prediction, is_fallback). Debutants: the source stint shrunk toward mu."""
    fc = fit["_forecast"]
    beta = fit["beta"]
    comp = fit["components_used"]
    alpha = rows.player_name.map(fc.m).to_numpy(float)
    fallback = ~np.isfinite(alpha)
    if fallback.any():
        src = (
            np.log(rows.pir_per36_src.clip(lower=vth.RATE_FLOOR))
            if fit["scale"] == "log"
            else rows.pir_per36_src
        ).to_numpy(float) - rows.league_src.map(beta).fillna(0.0).to_numpy(float)
        W = rows.games_src.to_numpy(float)
        kappa = comp["tau2"] / (comp["tau2"] + comp["sigma2_per_game"] / W)
        alpha = np.where(fallback, comp["mu"] + kappa * (src - comp["mu"]), alpha)
    lin = alpha + rows.league_dest.map(beta).to_numpy(float)
    pred = np.exp(lin) if fit["scale"] == "log" else lin
    return pred, fallback


# ------------------------------------------------------------------ folds
def score_fold(
    obs: pd.DataFrame, pairs: pd.DataFrame, fold: dict
) -> tuple[pd.DataFrame, dict]:
    s = fold["season"]
    rows = wf.fold_rows(fold)
    test = fold["test_rows"]
    fits = {
        "dyn": fit_dynamic(obs, pairs, s),
        "dyn_log": fit_dynamic(obs, pairs, s, scale="log"),
        "dyn_q_half": fit_dynamic(obs, pairs, s, q_mult=0.5),
        "dyn_q_double": fit_dynamic(obs, pairs, s, q_mult=2.0),
        "dyn_q0": fit_dynamic(obs, pairs, s, q_zero=True),
        "dyn_tier_beta": fit_dynamic(obs, pairs, s, tier_beta=True),
    }
    record: dict = {}
    for name, fit in fits.items():
        rows[name], fb = predict(fit, test)
        record[name] = {
            "q": fit["q"],
            "q_floored": fit["q_info"]["q_floored"],
            "sigma2_per_game": fit["components_used"]["sigma2_per_game"],
            "sigma2_floored": fit["sigma2_info"]["sigma2_floored"],
            "mu": fit["components_used"]["mu"],
            "tau2": fit["components_used"]["tau2"],
            "tau2_floored": fit["prior"]["tau2_floored"],
            "fallback_share": float(fb.mean()),
            "n_negative_predictions": int((rows[name] < 0).sum()),
        }
        if fit["q_info"]["q_floored"] or fit["sigma2_info"]["sigma2_floored"]:
            print(
                f"[T7 dyn {s}] WARNING {name}: a variance component floored -- "
                f"{record[name]}"
            )
    # static comparators on the same stints (hierarchical script, DL tau^2)
    static_add = vth.fit_hierarchical(obs, pairs, s, scale="additive")
    rows["hier_additive"] = vth.predict(static_add, test)
    rows["hier_recency1"] = vth.predict(
        vth.fit_hierarchical(obs, pairs, s, half_life=1.0), test
    )
    # T1 exact: the filter with the static arm's components and q = 0 IS the
    # static posterior
    exact = fit_dynamic(obs, pairs, s, q_zero=True, components=static_add["vc"])
    p_exact, _ = predict(exact, test)
    gap_exact = float(
        np.nanmax(np.abs(p_exact - rows["hier_additive"].to_numpy(float)))
    )
    assert gap_exact < T1_EXACT_TOLERANCE, (
        f"T1: Kalman filter at q=0 with the static components does not reproduce the "
        f"static posterior (max |diff| {gap_exact:.3e}) -- the filter is wrong"
    )
    record["t1"] = {
        "max_abs_pred_gap_exact_components": gap_exact,
        "mae_gap_dyn_q0_vs_hier_additive": float(
            np.abs(rows.dyn_q0 - rows.y).mean()
            - np.abs(rows.hier_additive - rows.y).mean()
        ),
        "static_sigma2_per_game": float(static_add["vc"]["sigma2_per_game"]),
        "dynamic_sigma2_per_game": float(
            fits["dyn"]["components_used"]["sigma2_per_game"]
        ),
    }
    record["beta_additive_to_euroleague"] = {
        lg: round(-b, 3)
        for lg, b in fits["dyn"]["beta"].items()
        if lg not in vh.blf.CONTINENTAL
    }
    print(
        f"[dyn {s}] q={fits['dyn']['q']:.4f} "
        f"sigma2/game={record['dyn']['sigma2_per_game']:.3f} "
        f"tau2={record['dyn']['tau2']:.3f} mu={record['dyn']['mu']:.3f} "
        f"fallback={record['dyn']['fallback_share']:.3f} "
        f"neg={record['dyn']['n_negative_predictions']} "
        f"T1 exact gap={gap_exact:.1e}"
    )
    return rows, record


def shuffled_league_control(
    obs: pd.DataFrame,
    pairs: pd.DataFrame,
    fits: list[dict],
    rows: pd.DataFrame,
    observed: float,
) -> dict:
    """Permute the domestic beta per fold, re-forecast, score against dyn_tier_beta."""
    rng = np.random.default_rng(SEED)
    base = {f["season"]: fit_dynamic(obs, pairs, f["season"]) for f in fits}
    y = rows.y.to_numpy(float)
    tier_err = np.abs(rows.dyn_tier_beta.to_numpy(float) - y).mean()
    gains = np.empty(N_SHUFFLE)
    for i in range(N_SHUFFLE):
        preds = []
        for f in fits:
            beta = dict(base[f["season"]]["beta"])
            dom = [lg for lg in beta if lg not in vh.blf.CONTINENTAL]
            beta.update(
                dict(zip(dom, map(float, rng.permutation([beta[lg] for lg in dom]))))
            )
            # beta enters the forecast through the stint residuals too; a shuffle
            # that only moved beta_dest would understate the mapping, so refit
            fit_sh = fit_dynamic_with_beta(obs, pairs, f["season"], beta)
            preds.append(predict(fit_sh, f["test_rows"])[0])
        p = np.concatenate(preds)[rows.index.to_numpy()]
        gains[i] = tier_err - np.abs(p - y).mean()
    return {
        "observed_gain_vs_tier_beta": observed,
        "n_shuffles": N_SHUFFLE,
        "shuffles_reaching_observed": int((gains >= observed).sum()),
        "shuffle_mean_gain": float(gains.mean()),
        "shuffle_p95_gain": float(np.percentile(gains, 95)),
    }


def fit_dynamic_with_beta(
    obs: pd.DataFrame, pairs: pd.DataFrame, season: int, beta: dict
) -> dict:
    """The primary fit with a supplied beta (for the shuffle control)."""
    train = obs[obs.season < season]
    known = train.league.isin(beta.keys()).to_numpy()
    train = train[known]
    stints = pd.DataFrame(
        {
            "player_name": train.player_name.to_numpy(),
            "season": train.season.to_numpy(),
            "w": train.games.to_numpy(float),
            "r": train.rate.to_numpy(float) - train.league.map(beta).to_numpy(float),
        }
    )
    sig = sigma2_from_shared_seasons(stints)
    means = season_means(stints)
    qq = q_from_consecutive_seasons(means, sig["sigma2_per_game"])
    prior = dl_prior(means.groupby("player_name").head(1), sig["sigma2_per_game"])
    comp = {
        "mu": prior["mu"],
        "tau2": prior["tau2"],
        "sigma2_per_game": sig["sigma2_per_game"],
    }
    fc = kalman_forecast(
        means,
        season,
        q=qq["q"],
        **{k: comp[k] for k in ("mu", "tau2")},
        sigma2=comp["sigma2_per_game"],
    )
    return {
        "season": season,
        "scale": "additive",
        "beta": beta,
        "q": qq["q"],
        "q_info": qq,
        "sigma2_info": sig,
        "prior": prior,
        "components_used": comp,
        "_forecast": fc.set_index("player_name"),
    }


def block(rows: pd.DataFrame, arms: list[str], label: str) -> dict:
    """Pooled metrics and the pre-registered contrasts on one set of rows."""
    y = rows.y.to_numpy(float)
    clusters = (rows.season.astype(str) + "|" + rows.cluster.astype(str)).to_numpy()
    pooled = wf.arm_metrics(y, {a: rows[a].to_numpy(float) for a in arms})

    def contrast(a: str, b: str) -> dict:
        d, lo, hi = wf.paired_cluster_bootstrap(
            rows[a].to_numpy(float), rows[b].to_numpy(float), y, clusters
        )
        print(f"[{label}] {a} vs {b}: delta={d:+.4f} CI [{lo:+.4f}, {hi:+.4f}]")
        return {"a": a, "b": b, "delta_mae_b_minus_a": d, "ci95": [lo, hi]}

    contrasts = {
        "dyn_vs_combined": contrast("dyn", "rtm_plus_league"),
        "dyn_vs_hier_recency1": contrast("dyn", "hier_recency1"),
        "dyn_vs_hier_additive": contrast("dyn", "hier_additive"),
        "dyn_vs_per_league": contrast("dyn", "per_league"),
        "dyn_vs_dyn_tier_beta": contrast("dyn", "dyn_tier_beta"),
        "dyn_log_vs_dyn": contrast("dyn_log", "dyn"),
        "dyn_q_half_vs_dyn": contrast("dyn_q_half", "dyn"),
        "dyn_q_double_vs_dyn": contrast("dyn_q_double", "dyn"),
    }
    for a in arms:
        print(
            f"[{label} pooled] {a:18s} MAE={pooled[a]['mae']:.4f} "
            f"R2={pooled[a]['r2']:+.4f}"
        )
    return {
        "n": int(len(rows)),
        "seasons": sorted(rows.season.unique().tolist()),
        "pooled": pooled,
        "contrasts": contrasts,
    }


def verdict(sel: dict) -> dict:
    c = sel["contrasts"]["dyn_vs_combined"]
    lo, hi = c["ci95"]
    if c["delta_mae_b_minus_a"] > 0 and lo > 0:
        v = "PASS"
    elif c["delta_mae_b_minus_a"] > 0:
        v = "PARTIAL"
    elif hi < 0:
        v = "FAIL"
    else:
        v = "PARTIAL"  # combined ahead on the point, CI spans zero: not separable
    return {
        "gate": "pooled selection folds 2020-2024, paired cluster bootstrap "
        "MAE(combined) - MAE(dyn)",
        "delta": c["delta_mae_b_minus_a"],
        "ci95": c["ci95"],
        "verdict": v,
        "reading": {
            "PASS": "dyn beats the combined arm, CI excludes zero",
            "PARTIAL": "not separable at this n (pre-registered as the likeliest "
            "outcome)",
            "FAIL": "the combined arm wins, CI excludes zero",
        }[v],
    }


# --------------------------------------------------------- predict mode (Amendment 10)
def predict_population(
    obs: pd.DataFrame, pairs: pd.DataFrame, primary: dict, *, season: int
) -> tuple[list[dict], dict]:
    """The dynamic arm's point prediction for EVERY row of the primary artifact.

    Amendment 10: the population is the primary's `predictions` list, nothing
    more and nothing less -- an import the primary refuses is not scored here,
    and the refusal logic never runs in this file. Rows are joined to the corpus
    by `pairing_key(name)`, which is what the corpus loader keys stints on.
    """
    from src.data.corpus.euroleague_api import pairing_key

    fit = fit_dynamic(obs, pairs, season)
    prim = primary["predictions"]
    keys = [pairing_key(r["name"]) for r in prim]
    src_games = (
        obs[obs.season == season - 1].groupby("player_name").games.max().to_dict()
    )
    rows = pd.DataFrame(
        {
            "player_name": keys,
            "league_src": [r["origin_league"] for r in prim],
            "league_dest": [r["destination"] for r in prim],
            "pir_per36_src": [float(r["pir_per36_src"]) for r in prim],
            "games_src": [float(src_games.get(k, 8.0)) for k in keys],
        }
    )
    pred, fallback = predict(fit, rows)
    fc = fit["_forecast"]
    out = []
    for i, (r, k) in enumerate(zip(prim, keys)):
        have = k in fc.index
        out.append(
            {
                "person_code": r["person_code"],
                "name": r["name"],
                "pairing_key": k,
                "competition": r["competition"],
                "destination": r["destination"],
                "origin_league": r["origin_league"],
                "projection_dynamic": float(pred[i]),
                "n_seasons_used": int(fc.n_seasons[k]) if have else 0,
                "last_season": int(fc.last_season[k]) if have else None,
                "forecast_variance": float(fc.P[k]) if have else None,
                "fallback": bool(fallback[i]),
            }
        )
    emitted = {o["person_code"] for o in out}
    expected = {r["person_code"] for r in prim}
    assert emitted == expected, (
        f"population drift: {len(emitted ^ expected)} person_codes differ "
        "from the primary"
    )
    header = {
        "season": season,
        "status": primary["status"],
        "arm": "dynamic_ability",
        "role": "secondary arm scored beside the primary (Amendment 10); point "
        "predictions only, no interval, no success criterion of its own",
        "primary_artifact_built_at": primary["built_at"],
        "primary_source_collection": primary["source_collection"],
        "continental_source": primary.get("basis", {}).get("continental_source"),
        "preregistration": "docs/research/"
        "translation-dynamic-ability-preregistration-2026-09-05.md",
        "amendment": "docs/research/preregistration-2026-27-amendment-10-2026-09-05.md",
        "components": {
            "q": fit["q"],
            "q_floored": fit["q_info"]["q_floored"],
            "sigma2_per_game": fit["components_used"]["sigma2_per_game"],
            "sigma2_floored": fit["sigma2_info"]["sigma2_floored"],
            "tau2": fit["components_used"]["tau2"],
            "tau2_floored": fit["prior"]["tau2_floored"],
            "mu": fit["components_used"]["mu"],
            "n_shared_season_pairs": fit["sigma2_info"]["n_shared_season_pairs"],
            "n_consecutive_pairs": fit["q_info"]["n_consecutive_pairs"],
        },
        "n_predicted": len(out),
        "n_joined_to_corpus_history": int(sum(1 for o in out if not o["fallback"])),
        "fallback_share": float(np.mean([o["fallback"] for o in out])) if out else 0.0,
    }
    return out, header


def run_predict(args) -> int:
    primary = json.loads(args.primary.read_text())
    assert int(primary["season"]) == args.predict, (
        f"--predict {args.predict} but the primary artifact is season "
        f"{primary['season']}"
    )
    games, pairs = vh.load_corpus(args.continental_source)
    obs = vth.player_season_league_rows(games)
    rows, header = predict_population(obs, pairs, primary, season=args.predict)
    header["built_at"] = args.built_at or datetime.date.today().isoformat()
    header["generated_by"] = "scripts/validate_translation_dynamic.py --predict"
    payload = {**header, "predictions": rows}
    args.predictions_out.mkdir(parents=True, exist_ok=True)
    path = args.predictions_out / f"dynamic_predictions_{args.predict}.json"
    path.write_text(json.dumps(payload, indent=1, default=float) + "\n")
    c = header["components"]
    print(
        f"[predict {args.predict}] {header['n_predicted']} rows (= primary), "
        f"{header['n_joined_to_corpus_history']} with corpus history, "
        f"fallback share {header['fallback_share']:.3f}; q={c['q']:.3f} "
        f"sigma2/game={c['sigma2_per_game']:.2f} tau2={c['tau2']:.2f} "
        f"mu={c['mu']:.3f}; "
        f"status={header['status']}"
    )
    print(f"[predict] wrote {path}")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out-dir", type=Path, default=_DEFAULT_OUT)
    ap.add_argument("--walkforward-summary", type=Path, default=None)
    ap.add_argument(
        "--continental-source",
        choices=vh.blf.CONTINENTAL_SOURCES,
        default=vh.blf.DEFAULT_CONTINENTAL_SOURCE,
    )
    ap.add_argument("--skip-shuffle", action="store_true")
    ap.add_argument(
        "--predict",
        type=int,
        default=None,
        metavar="SEASON",
        help="Amendment 10 predict mode: emit dynamic_predictions_<SEASON>.json on the "
        "primary artifact's population (needs --primary); skips the walk-forward",
    )
    ap.add_argument(
        "--primary",
        type=Path,
        default=None,
        help="translation_predictions_<season>.json",
    )
    ap.add_argument(
        "--predictions-out",
        type=Path,
        default=REPO / "data" / "processed" / "predictions",
    )
    ap.add_argument("--built-at", default=None)
    args = ap.parse_args(argv)
    if args.predict is not None:
        if args.primary is None:
            ap.error("--predict needs --primary")
        return run_predict(args)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    summary_path = args.walkforward_summary or args.out_dir / "walkforward_summary.json"
    summary = json.loads(summary_path.read_text())
    assert summary["continental_source"] == args.continental_source

    games, pairs, fits = vth.build_folds(args.continental_source)
    obs = vth.player_season_league_rows(games)
    print(f"[obs] stints (>= {vth.MIN_STINT_MINUTES:.0f} min): {len(obs)}")

    scored = [score_fold(obs, pairs, f) for f in fits]
    rows = pd.concat([r for r, _ in scored], ignore_index=True)
    records = {f"fit_{r.season.iloc[0]}": rec for r, rec in scored}
    rows = rows[np.isfinite(rows.per_league)].reset_index(drop=True)
    maes = itp.assert_reproduces_walkforward(rows, summary)
    print("[folds] " + " ".join(f"{k}={v:.4f}" for k, v in maes.items()))

    arms = list(itp.ARMS) + [
        PRIMARY,
        *CHECKS,
        *DECOMPOSITION,
        *ALTERNATIVES,
        *STATIC_COMPARATORS,
    ]
    sel_rows = rows[rows.season.isin(SELECTION_FOLDS)]
    con_rows = rows[rows.season == CONFIRMATION_FOLD]
    selection = block(sel_rows, arms, "selection 2020-2024")
    confirmation = block(con_rows, arms, "confirmation 2025")
    per_season = (
        rows.assign(**{f"ae_{a}": np.abs(rows[a] - rows.y) for a in arms})
        .groupby("season")
        .agg(n=("y", "size"), **{f"mae_{a}": (f"ae_{a}", "mean") for a in arms})
        .reset_index()
    )
    print(per_season.round(4).to_string(index=False))

    t1_gaps = [records[k]["t1"]["mae_gap_dyn_q0_vs_hier_additive"] for k in records]
    t1 = {
        # the per-fold assert would have stopped the run otherwise
        "exact_check_passed_every_fold": True,
        "max_abs_pred_gap_exact_components": max(
            records[k]["t1"]["max_abs_pred_gap_exact_components"] for k in records
        ),
        "mae_gap_dyn_q0_vs_hier_additive_pooled": float(
            np.abs(rows.dyn_q0 - rows.y).mean()
            - np.abs(rows.hier_additive - rows.y).mean()
        ),
        "mae_gap_per_fold": t1_gaps,
        "within_preregistered_0_05": bool(
            abs(
                np.abs(rows.dyn_q0 - rows.y).mean()
                - np.abs(rows.hier_additive - rows.y).mean()
            )
            <= T1_TOLERANCE_MAE
        ),
    }
    print(f"[T1] {json.dumps(t1)}")

    control = None
    if not args.skip_shuffle:
        observed = (
            selection["pooled"]["dyn_tier_beta"]["mae"]
            - selection["pooled"]["dyn"]["mae"]
        )
        sel_fits = [f for f in fits if f["season"] in SELECTION_FOLDS]
        control = shuffled_league_control(obs, pairs, sel_fits, sel_rows, observed)
        print(f"[control] {json.dumps(control)}")

    v = verdict(selection)
    print(f"[verdict] {json.dumps(v)}")
    out = {
        "generated_by": "scripts/validate_translation_dynamic.py",
        "preregistration": "docs/research/"
        "translation-dynamic-ability-preregistration-2026-09-05.md",
        "continental_source": args.continental_source,
        "primary": PRIMARY,
        "n_pooled_all_folds": int(len(rows)),
        "walkforward_mae_reproduced": maes,
        "selection": selection,
        "confirmation_2025_read_once": confirmation,
        "per_season": per_season.to_dict(orient="records"),
        "fits": records,
        "t1_filter_check": t1,
        "shuffled_league_control": control,
        "verdict": v,
    }
    (args.out_dir / "dynamic_summary.json").write_text(
        json.dumps(out, indent=1, default=float)
    )
    rows.to_parquet(args.out_dir / "dynamic_rows.parquet", index=False)
    print(
        f"[done] wrote dynamic_summary.json and dynamic_rows.parquet to {args.out_dir}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
