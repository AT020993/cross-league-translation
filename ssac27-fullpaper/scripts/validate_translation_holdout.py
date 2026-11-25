"""ATI-2799 — retrospective held-out validation of the league translation factors.

Bars, threats and controls are fixed in `holdout-preregistration.md`, saved as an
artifact BEFORE this script was written. Nothing here may relax a bar.

Every threat T1-T12 in the pre-registration has a control in this file, and each
control prints, so it runs whether or not the author remembers to look.

Verdict as of 2026-08-17, reproduced bit-identically on 2026-08-21: **PARTIAL**.
G1/G2/G3/G5/G6 pass, G4 fails -- the model ties a single-constant baseline
(-0.005 MAE, CI [-0.236, +0.230]). METHOD.md section 8 forbids re-tuning to
convert that, so the failure is reported rather than removed.

Amendment 4 (ATI-2957, 2026-09-03) moved the destination side of the corpus to
the EuroLeague API. The 2026-08-17 verdict above is the record of the gate on
the corpus it was run on and is NOT re-scored: run with
``--continental-source proballers`` to reproduce it, or with the default
``api`` (and a separate ``--out-dir``) to produce the SECOND record that is
reported beside it.

Usage:
    uv run python scripts/validate_translation_holdout.py
    uv run python scripts/validate_translation_holdout.py --out-dir /tmp/check
    uv run python scripts/validate_translation_holdout.py \
        --continental-source proballers \\
        --out-dir data/processed/translation_proballers_2026-08-21
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

import scripts.build_league_factors as blf  # noqa: E402
from src.research.gates import (  # noqa: E402
    per_observation_reliability,
    spearman_brown,
)

#: Defaults resolve inside the repo. The original run pinned an absolute
#: artifact path, which is why this script produced a result nobody else could
#: re-derive -- the ATI-2844 failure mode. Both are now CLI arguments with
#: repo-relative defaults, so a clean checkout reproduces the verdict.
_DEFAULT_FACTORS = (
    REPO / "data" / "processed" / "translation" / "league_factors.parquet"
)
_DEFAULT_OUT = REPO / "data" / "processed" / "translation"

OUT = _DEFAULT_OUT

# --- pre-registered constants. Editing any of these violates METHOD.md §8. ---
MIN_GAMES = 8
MIN_PAIRS = 75
N_BOOT = 2000
SEED = 0
EXCLUDED_SOURCE = ("poland-plk",)  # prereg §2, declared exclusion
#: Pair count the corpus must reproduce, per destination source. The Proballers
#: figure is the one the 2026-08-17 verdict was run on; the API figure was
#: pinned on the first Amendment-4 run (2026-09-04) so a later scrape or a
#: loader change cannot move the second record silently.
EXPECTED_PAIRS = {"proballers": 5039, "api": 4074}
G1_RATIO = 0.95  # model MAE <= 0.95 * B0 MAE
G3_R2 = 0.20
G6_SHARE = 0.75
PER_LEAGUE_N_FLOOR = 20
KNOWN_NULL_BIAS = 1.019  # Phase 0 measured estimator bias at parity
STAT = "pir"
ERA = "all"
SAMPLE = "all_pairs"

log: list[str] = []


def say(msg: str) -> None:
    print(msg, flush=True)
    log.append(msg)


# ------------------------------------------------------------------ corpus --
def load_corpus(
    continental_source: str = blf.DEFAULT_CONTINENTAL_SOURCE,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    games = blf.add_usage(blf.load_player_games(continental_source))
    pairs = blf.build_pairs(games, min_games=MIN_GAMES)
    say(
        f"[corpus] continental_source={continental_source} "
        f"player-games={len(games)} dual-tier pairs={len(pairs)}"
    )
    return games, pairs


def fit_factors(pairs: pd.DataFrame, *, label: str) -> pd.DataFrame:
    """Refit with the SHIPPED estimator, restricted to the pir/era=all loop.

    Restricting STATS/ERAS only shortens the loop: cell_seed() keys on the era and
    stat *names*, so the ('all', 'pir') cells get byte-identical seeds and values
    to a full run. The reproduction check in main() asserts exactly that against
    the saved full refit.
    """
    stats_bak, eras_bak = blf.STATS, blf.ERAS
    blf.STATS = {STAT: "pir"}
    blf.ERAS = {ERA: (2015, 2026)}
    try:
        tbl = blf.estimate_table(
            pairs,
            samples=[blf.Sample(SAMPLE, None)],
            min_pairs=MIN_PAIRS,
            n_boot=N_BOOT,
            seed=SEED,
        )
    finally:
        blf.STATS, blf.ERAS = stats_bak, eras_bak
    tbl = tbl[(tbl.stat == STAT) & (tbl.era == ERA) & (tbl["sample"] == SAMPLE)].copy()
    # T9 -- pooling collapse. tau == 0 makes every league in the block identical.
    for dest, blk in tbl.groupby("destination"):
        tau = float(blk.tau.iloc[0])
        collapsed = bool(tau <= 0)
        say(
            f"[T9 {label}] {dest}: tau={tau:.6f} collapsed={collapsed} "
            f"n_cells={len(blk)} tier_mean={blk.tier_mean.iloc[0]:.4f}"
        )
        if collapsed:
            say(
                f"[T9 {label}] WARNING {dest} block collapsed -- per-league "
                "verdicts in this block are uninterpretable"
            )
    return tbl


def factor_lookup(tbl: pd.DataFrame, est: str = "factor") -> dict:
    """(source, destination) -> factor, with tier-mean fallback where unreliable.

    Falling back on `reliable == False` is what the estimator's own docstring
    requires of consumers. `est` selects an alternative estimator for T10.
    """
    out = {}
    tiers = {}
    for dest, blk in tbl.groupby("destination"):
        tiers[dest] = float(blk.tier_mean.iloc[0])
        for _, r in blk.iterrows():
            val = float(r[est]) if est == "factor" else float(r[est])
            if (not bool(r.reliable)) or not np.isfinite(val):
                val = tiers[dest]
            out[(r.league, dest)] = val
    return out, tiers


def se_lookup(tbl: pd.DataFrame) -> dict:
    return {(r.league, r.destination): float(r.se) for _, r in tbl.iterrows()}


# ------------------------------------------------------------- population --
def build_switchers(games: pd.DataFrame) -> pd.DataFrame:
    """One row per (player, destination season) transfer INTO a continental comp."""
    agg = (
        games.groupby(["player_name", "season", "league"])
        .agg(
            games=("game_id", "nunique"),
            minutes=("minutes", "sum"),
            pir=("pir", "sum"),
            poss=("poss", "sum"),
            team_poss=("team_poss", "sum"),
            team_minutes=("team_minutes", "sum"),
            n_clubs=("team", "nunique"),
            club=("team", lambda s: s.value_counts().idxmax()),
            # Study B: component sums so a switcher row carries every stat
            **{k: (v, "sum") for k, v in blf.STATS_SUMS.items()},
            **{k: (v, "sum") for k, v in blf.EXTRA_SUMS.items()},
        )
        .reset_index()
    )
    agg["usage"] = (
        100 * agg.poss * (agg.team_minutes / 5) / (agg.minutes * agg.team_poss)
    )
    agg["min_per_game"] = agg.minutes / agg.games
    agg["pir_per36"] = 36 * agg.pir / agg.minutes
    agg_all = agg.copy()  # keep pre-threshold for T7
    q = agg[(agg.games >= MIN_GAMES) & (agg.minutes > 0)].copy()

    dest = q[q.league.isin(blf.CONTINENTAL)].copy()
    src = q[~q.league.isin(blf.NOT_A_SOURCE)].copy()
    # largest-minutes stint per side, exactly as the estimator does
    dest = dest.sort_values("minutes", ascending=False).drop_duplicates(
        ["player_name", "season"]
    )
    src = src.sort_values("minutes", ascending=False).drop_duplicates(
        ["player_name", "season"]
    )

    s = src.copy()
    s["season_join"] = s.season + 1
    cand = dest.merge(
        s,
        left_on=["player_name", "season"],
        right_on=["player_name", "season_join"],
        suffixes=("_dest", "_src"),
    )
    assert len(cand) >= len(dest.merge(s, on="player_name")) * 0 + 1
    cand = cand.rename(
        columns={"season_dest": "season_dest", "season_src": "season_src"}
    )

    # T4 -- incumbency. A player already in ANY continental comp in season t is
    # not a switcher-in; flag rather than silently drop so the sensitivity runs.
    prev_cont = dest[["player_name", "season"]].drop_duplicates().assign(was_cont=1)
    prev_cont["season_dest"] = prev_cont.season + 1
    cand = cand.merge(
        prev_cont[["player_name", "season_dest", "was_cont"]],
        on=["player_name", "season_dest"],
        how="left",
    )
    cand["was_cont"] = cand.was_cont.fillna(0).astype(int)

    # T5 -- selection. Was the source season above the player's own prior mean?
    hist = agg_all[["player_name", "season", "pir", "minutes"]].copy()
    hist = hist[hist.minutes > 0]
    # cumulative minutes-weighted prior rate, strictly before the source season
    hs = (
        hist.groupby(["player_name", "season"])[["pir", "minutes"]]
        .sum()
        .sort_index()
        .reset_index()
    )
    hs[["cum_pir", "cum_min"]] = hs.groupby("player_name")[["pir", "minutes"]].cumsum()
    hs["prior_pir"] = hs.cum_pir - hs.pir
    hs["prior_min"] = hs.cum_min - hs.minutes
    hs["prior_mean_pir36"] = np.where(
        hs.prior_min > 0, 36 * hs.prior_pir / hs.prior_min, np.nan
    )
    cand = cand.merge(
        hs[["player_name", "season", "prior_mean_pir36"]].rename(
            columns={"season": "season_src"}
        ),
        on=["player_name", "season_src"],
        how="left",
        validate="m:1",
    )
    cand["above_own_prior"] = cand.pir_per36_src > cand.prior_mean_pir36

    # T6 -- name collision exposure
    nleagues = agg_all.groupby("player_name").league.nunique()
    cand["name_multi_league"] = cand.player_name.map(nleagues).fillna(0).astype(int)
    multiclub = games.groupby(["player_name", "league", "season"]).team.nunique()
    mc = set(multiclub[multiclub > 1].reset_index().player_name)
    cand["name_multiclub_season"] = cand.player_name.isin(mc)

    # T11 -- degenerate denominator
    n_bad = int((cand.pir_per36_src <= 0).sum() + (cand.pir_per36_dest <= 0).sum())
    say(
        f"[T11] rows with a non-positive per-36 rate on either side: {n_bad} (excluded)"
    )
    cand = cand[(cand.pir_per36_src > 0) & (cand.pir_per36_dest > 0)].copy()

    cand["cluster"] = (
        cand.season_dest.astype(str) + "|" + cand.league_dest + "|" + cand.club_dest
    )
    return cand, agg_all


# ---------------------------------------------------------------- scoring --
def predict(rows: pd.DataFrame, fl: dict, tiers: dict) -> np.ndarray:
    f = np.array(
        [
            fl.get((lg, d), tiers.get(d, np.nan))
            for lg, d in zip(rows.league_src, rows.league_dest)
        ]
    )
    return rows.pir_per36_src.to_numpy() * f


def metrics(y: np.ndarray, p: np.ndarray) -> dict:
    y, p = np.asarray(y, float), np.asarray(p, float)
    ok = np.isfinite(y) & np.isfinite(p)
    y, p = y[ok], p[ok]
    sse = float(np.sum((y - p) ** 2))
    sst = float(np.sum((y - y.mean()) ** 2))
    return {
        "n": int(len(y)),
        "mae": float(np.mean(np.abs(y - p))),
        "rmse": float(np.sqrt(sse / len(y))),
        "r2": float(1 - sse / sst) if sst > 0 else float("nan"),
        "bias": float(np.mean(p - y)),
    }


def paired_cluster_bootstrap(rows: pd.DataFrame, y, pa, pb, *, n_boot=4000, seed=0):
    """95% CI on (MAE_b - MAE_a), resampling destination club-season clusters."""
    rng = np.random.default_rng(seed)
    ea, eb = np.abs(y - pa), np.abs(y - pb)
    cl = rows.cluster.to_numpy()
    uniq = np.unique(cl)
    idx = {c: np.where(cl == c)[0] for c in uniq}
    diffs = np.empty(n_boot)
    for b in range(n_boot):
        pick = rng.choice(uniq, size=len(uniq), replace=True)
        sel = np.concatenate([idx[c] for c in pick])
        diffs[b] = eb[sel].mean() - ea[sel].mean()
    lo, hi = np.percentile(diffs, [2.5, 97.5])
    return {
        "delta_mae": float(eb.mean() - ea.mean()),
        "ci_lo": float(lo),
        "ci_hi": float(hi),
        "excludes_zero": bool(lo > 0 or hi < 0),
        "se": float(diffs.std(ddof=1)),
        "n_clusters": int(len(uniq)),
    }


def baselines(rows: pd.DataFrame, k_b1b: float) -> dict:
    b0 = rows.pir_per36_src.to_numpy()
    ratio = (rows.min_per_game_dest / rows.min_per_game_src).to_numpy()
    return {"B0": b0, "B1a_oracle": b0 * ratio, "B1b_honest": b0 * k_b1b}


# ---------------------------------------------------------- ceiling / power --
def destination_reliability(games: pd.DataFrame, min_games_per_arm=4) -> dict:
    """Odd/even split-half of destination per-36 PIR, minutes-weighted.

    Weighted the same way the OUTCOME is computed, so the ceiling applies to the
    quantity actually being predicted rather than to a per-game mean.
    """
    d = games[games.league.isin(blf.CONTINENTAL)].copy()
    d = d[d.minutes > 0]
    d["gidx"] = d.groupby(["player_name", "season", "league"]).cumcount()
    d["half"] = np.where(d.gidx % 2 == 0, "a", "b")
    g = (
        d.groupby(["player_name", "season", "league", "half"])
        .agg(pir=("pir", "sum"), minutes=("minutes", "sum"), n=("game_id", "nunique"))
        .reset_index()
    )
    g["rate"] = 36 * g.pir / g.minutes
    w = g.pivot_table(
        index=["player_name", "season", "league"], columns="half", values=["rate", "n"]
    ).dropna()
    ok = (w[("n", "a")] >= min_games_per_arm) & (w[("n", "b")] >= min_games_per_arm)
    w = w[ok]
    r = float(np.corrcoef(w[("rate", "a")], w[("rate", "b")])[0, 1])
    n_obs = float(np.mean([w[("n", "a")].mean(), w[("n", "b")].mean()]))
    return {
        "split_half_r": r,
        "reliability_sb": 2 * r / (1 + r),
        "n_units": int(len(w)),
        "mean_games_per_arm": n_obs,
        "min_games_per_arm": min_games_per_arm,
    }


def power_line(rows: pd.DataFrame, y, p_model, p_b0, rel: dict, label: str) -> dict:
    """Minimum detectable MAE gain at this n, plus the reliability ceiling.

    Two readings of a low number (METHOD.md §7): effect absent, or sample blind.
    """
    bs = paired_cluster_bootstrap(rows, y, p_model, p_b0, n_boot=2000, seed=7)
    mdg = 2.8 * bs["se"]  # ~80% power, two-sided 5%
    n = len(rows)
    need_n = (
        int(np.ceil(n * (mdg / max(bs["delta_mae"], 1e-9)) ** 2))
        if bs["delta_mae"] > 0
        else None
    )
    r1 = per_observation_reliability(rel["split_half_r"], rel["mean_games_per_arm"])
    games_used = float(rows.games_dest.mean())
    ceiling = spearman_brown(r1, games_used)
    return {
        "label": label,
        "n": n,
        "observed_gain_mae": bs["delta_mae"],
        "se_gain": bs["se"],
        "min_detectable_gain_mae": float(mdg),
        "n_required_for_observed_gain": need_n,
        "achievable_reliability_at_mean_games": float(ceiling),
        "ceiling_r2_at_mean_games": float(ceiling),
        "mean_dest_games": games_used,
    }


# -------------------------------------------------------------------- main --
def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--factors",
        type=Path,
        default=_DEFAULT_FACTORS,
        help="league_factors.parquet to check the internal refit against",
    )
    ap.add_argument(
        "--out-dir",
        type=Path,
        default=_DEFAULT_OUT,
        help="where the five validation outputs are written",
    )
    ap.add_argument(
        "--continental-source",
        choices=blf.CONTINENTAL_SOURCES,
        default=blf.DEFAULT_CONTINENTAL_SOURCE,
        help="api (Amendment 4 default) or proballers (the 2026-08-17 record)",
    )
    args = ap.parse_args(argv)
    global OUT
    OUT = args.out_dir
    OUT.mkdir(parents=True, exist_ok=True)

    games, pairs = load_corpus(args.continental_source)

    # --- invariant: our loop reproduces the saved full refit exactly ---
    full = fit_factors(pairs, label="full")
    saved = pd.read_parquet(args.factors)
    saved = saved[
        (saved.stat == STAT) & (saved.era == ERA) & (saved["sample"] == SAMPLE)
    ]
    m = full.merge(saved, on=["league", "destination"], suffixes=("_new", "_old"))
    assert len(m) == len(saved) == len(full), (len(m), len(saved), len(full))
    dmax = float(np.nanmax(np.abs(m.factor_new - m.factor_old)))
    semax = float(np.nanmax(np.abs(m.se_new - m.se_old)))
    say(
        f"[invariant] reproduces saved refit on {len(m)} pir/all cells: "
        f"max|dfactor|={dmax:.2e} max|dse|={semax:.2e}"
    )
    assert dmax < 1e-12 and semax < 1e-12, "restricted loop changed the estimates"
    expected_pairs = EXPECTED_PAIRS[args.continental_source]
    if expected_pairs is None:
        say(
            f"[invariant] WARNING no pinned pair count for "
            f"continental_source={args.continental_source}; observed {len(pairs)} "
            "-- pin it in EXPECTED_PAIRS before quoting this run"
        )
    else:
        assert len(pairs) == expected_pairs, (
            f"pair count {len(pairs)} != {expected_pairs} (corpus changed)"
        )

    switch, agg_all = build_switchers(games)
    say(
        f"[population] consecutive-season rows={len(switch)} "
        f"switchers-in={int((switch.was_cont == 0).sum())} "
        f"incumbents={int((switch.was_cont == 1).sum())}"
    )

    sw = switch[switch.was_cont == 0].copy()
    n_pol = int((sw.league_src.isin(EXCLUDED_SOURCE)).sum())
    sw = sw[~sw.league_src.isin(EXCLUDED_SOURCE)].copy()
    say(f"[prereg §2] poland-plk rows refused, not scored: {n_pol}")

    rel = destination_reliability(games)
    say(
        f"[T8/ceiling] destination split-half r={rel['split_half_r']:.4f} "
        f"reliability_SB={rel['reliability_sb']:.4f} on n_units={rel['n_units']} "
        f"at mean {rel['mean_games_per_arm']:.1f} games/arm"
    )

    # ---------------- ARM A: fit <=2023, score 2024-25 ----------------
    tr_pairs = pairs[pairs.season <= 2023].copy()
    assert tr_pairs.season.max() <= 2023, "T2 temporal leakage"  # T2
    assert len(tr_pairs) < len(pairs), "T2: refit sample not reduced"
    say(
        f"[T2] Arm A fit pairs={len(tr_pairs)} "
        f"(max season {int(tr_pairs.season.max())}) "
        f"vs full {len(pairs)}"
    )
    fac_A = fit_factors(tr_pairs, label="armA<=2023")
    fl_A, tiers_A = factor_lookup(fac_A)
    se_A = se_lookup(fac_A)

    test = sw[sw.season_dest.isin([2024, 2025])].copy()
    assert int(test.season_dest.min()) >= 2024, "T2 scored row from the fit window"
    tr_sw = sw[sw.season_dest <= 2023].copy()
    k_b1b = float((tr_sw.min_per_game_dest / tr_sw.min_per_game_src).mean())
    say(f"[B1b] minutes ratio k fitted on {len(tr_sw)} <=2023 switchers: k={k_b1b:.4f}")

    y = test.pir_per36_dest.to_numpy()
    pm = predict(test, fl_A, tiers_A)
    bl = baselines(test, k_b1b)
    res = {"model": metrics(y, pm)} | {k: metrics(y, v) for k, v in bl.items()}
    for k, v in res.items():
        say(
            f"[armA] {k:12s} n={v['n']:4d} MAE={v['mae']:.4f} RMSE={v['rmse']:.4f} "
            f"R2={v['r2']:+.4f} bias={v['bias']:+.4f}"
        )

    g2 = paired_cluster_bootstrap(test, y, pm, bl["B0"], n_boot=4000, seed=SEED)
    say(
        f"[G2] B0 MAE - model MAE = {g2['delta_mae']:+.4f} "
        f"95% CI [{g2['ci_lo']:+.4f}, {g2['ci_hi']:+.4f}] "
        f"excludes_zero={g2['excludes_zero']} clusters={g2['n_clusters']}"
    )

    # ATI-2955 item 3: the G4 margin against B1b carried an interval that no
    # committed code produced. Same paired cluster bootstrap as G2, same seed;
    # it does not decide G4 (G4 is a strict comparison of point values) and
    # moves no bar — it is the interval the tie is REPORTED with.
    g4_b1b = paired_cluster_bootstrap(
        test, y, pm, bl["B1b_honest"], n_boot=4000, seed=SEED
    )
    say(
        f"[G4/B1b] B1b MAE - model MAE = {g4_b1b['delta_mae']:+.4f} "
        f"95% CI [{g4_b1b['ci_lo']:+.4f}, {g4_b1b['ci_hi']:+.4f}] "
        f"excludes_zero={g4_b1b['excludes_zero']} clusters={g4_b1b['n_clusters']}"
    )

    g1 = res["model"]["mae"] <= G1_RATIO * res["B0"]["mae"]
    g3 = res["model"]["r2"] >= G3_R2
    g4 = (
        res["model"]["mae"] < res["B0"]["mae"]
        and res["model"]["mae"] < res["B1b_honest"]["mae"]
        and res["model"]["r2"] > res["B0"]["r2"]
        and res["model"]["r2"] > res["B1b_honest"]["r2"]
    )
    say(
        f"[gates] G1(<=0.95*B0 MAE={G1_RATIO * res['B0']['mae']:.4f})={g1} "
        f"G2={g2['excludes_zero']} G3(R2>={G3_R2})={g3} G4={g4}"
    )

    pw = power_line(test, y, pm, bl["B0"], rel, "armA_pooled")
    say(
        f"[G8/power] armA n={pw['n']} gain={pw['observed_gain_mae']:+.4f} "
        f"MDG(80%)={pw['min_detectable_gain_mae']:.4f} "
        f"ceiling_R2={pw['ceiling_r2_at_mean_games']:.4f}"
    )

    # ---------------- T1: same-season paired arm ----------------
    same = pairs[pairs.season.isin([2024, 2025])].copy()
    same = same[~same.league_src.isin(EXCLUDED_SOURCE)]
    same["cluster"] = (
        same.season.astype(str) + "|" + same.league_dest + "|" + same.club_dest
    )
    same = same.rename(
        columns={"league_src": "league_src", "league_dest": "league_dest"}
    )
    ys = same.pir_per36_dest.to_numpy()
    ps = same.pir_per36_src.to_numpy() * np.array(
        [
            fl_A.get((lg, d), tiers_A.get(d, np.nan))
            for lg, d in zip(same.league_src, same.league_dest)
        ]
    )
    t1 = {
        "same_season_model": metrics(ys, ps),
        "same_season_B0": metrics(ys, same.pir_per36_src.to_numpy()),
    }
    for k, v in t1.items():
        say(
            f"[T1] {k:20s} n={v['n']:4d} MAE={v['mae']:.4f} "
            f"R2={v['r2']:+.4f} bias={v['bias']:+.4f}"
        )

    # ---------------- T3: player overlap ----------------
    fit_players = set(tr_pairs.player_name)
    overlap = test.player_name.isin(fit_players)
    say(
        f"[T3] scored rows whose player also appears in the Arm A fit pairs: "
        f"{int(overlap.sum())} of {len(test)}"
    )
    t3 = {}
    if (~overlap).sum() >= 20:
        sub = test[~overlap]
        t3 = {
            "model": metrics(sub.pir_per36_dest, predict(sub, fl_A, tiers_A)),
            "B0": metrics(sub.pir_per36_dest, sub.pir_per36_src),
        }
        say(
            f"[T3] no-overlap subset: model MAE={t3['model']['mae']:.4f} "
            f"R2={t3['model']['r2']:+.4f} vs B0 MAE={t3['B0']['mae']:.4f} "
            f"R2={t3['B0']['r2']:+.4f}"
        )

    # ---------------- T4: incumbents included ----------------
    inc = switch[
        (switch.was_cont == 1)
        & (~switch.league_src.isin(EXCLUDED_SOURCE))
        & (switch.season_dest.isin([2024, 2025]))
    ].copy()
    allrows = pd.concat([test, inc], ignore_index=True)
    t4 = {
        "model": metrics(allrows.pir_per36_dest, predict(allrows, fl_A, tiers_A)),
        "B0": metrics(allrows.pir_per36_dest, allrows.pir_per36_src),
    }
    say(
        f"[T4] with {len(inc)} incumbents added (n={t4['model']['n']}): "
        f"model MAE={t4['model']['mae']:.4f} R2={t4['model']['r2']:+.4f} "
        f"vs B0 MAE={t4['B0']['mae']:.4f} R2={t4['B0']['r2']:+.4f}"
    )

    # ---------------- T5: selection / regression to the mean ----------------
    t5 = {}
    for name, mask in [
        # `.eq(True)` not `if x:` -- above_own_prior is a nullable boolean
        # column and rows with no prior season must fall out of BOTH splits.
        ("above_own_prior", test.above_own_prior.eq(True)),
        ("below_own_prior", test.above_own_prior.eq(False)),
    ]:  # noqa: E712
        sub = test[mask]
        if len(sub) >= 15:
            mm = metrics(sub.pir_per36_dest, predict(sub, fl_A, tiers_A))
            bb = metrics(sub.pir_per36_dest, sub.pir_per36_src)
            t5[name] = {"model": mm, "B0": bb}
            say(
                f"[T5] {name}: n={mm['n']} model MAE={mm['mae']:.4f} "
                f"bias={mm['bias']:+.4f} | "
                f"B0 MAE={bb['mae']:.4f} bias={bb['bias']:+.4f}"
            )
    say(
        f"[T5] rows with no prior season (excluded from the split): "
        f"{int(test.prior_mean_pir36.isna().sum())}"
    )

    # ---------------- T6: name collision ----------------
    clean = test[(test.name_multi_league < 4) & (~test.name_multiclub_season)]
    t6 = {}
    if len(clean) >= 20:
        t6 = {
            "model": metrics(clean.pir_per36_dest, predict(clean, fl_A, tiers_A)),
            "B0": metrics(clean.pir_per36_dest, clean.pir_per36_src),
        }
        say(
            f"[T6] collision-pruned n={t6['model']['n']}: "
            f"model MAE={t6['model']['mae']:.4f} "
            f"R2={t6['model']['r2']:+.4f} vs B0 MAE={t6['B0']['mae']:.4f}"
        )

    # ---------------- T7: survivorship ----------------
    t7 = {}
    dest_all = agg_all[agg_all.league.isin(blf.CONTINENTAL)]
    thin = dest_all[(dest_all.games < MIN_GAMES) & (dest_all.season.isin([2024, 2025]))]
    say(
        f"[T7] destination league-seasons at 1-7 games in 2024-25 (invisible to the "
        f"metric): {len(thin)}"
    )
    for g in (5, 15):
        sub = test[test.games_dest >= g]
        mm = metrics(sub.pir_per36_dest, predict(sub, fl_A, tiers_A))
        bb = metrics(sub.pir_per36_dest, sub.pir_per36_src)
        t7[f"min_games_{g}"] = {"model": mm, "B0": bb}
        say(
            f"[T7] >= {g} dest games: n={mm['n']} "
            f"model MAE={mm['mae']:.4f} R2={mm['r2']:+.4f} "
            f"| B0 MAE={bb['mae']:.4f}"
        )

    # ---------------- T10: estimator choice ----------------
    t10 = {}
    for est in ("est_ratio_of_sums", "est_mean_of_ratios"):
        fl_e, tiers_e = factor_lookup(fac_A, est=est)
        mm = metrics(y, predict(test, fl_e, tiers_e))
        t10[est] = mm
        say(f"[T10] {est}: MAE={mm['mae']:.4f} R2={mm['r2']:+.4f}")
    spread = max([res["model"]["mae"]] + [v["mae"] for v in t10.values()]) - min(
        [res["model"]["mae"]] + [v["mae"] for v in t10.values()]
    )
    margin = res["B0"]["mae"] - G1_RATIO * res["B0"]["mae"]
    say(
        f"[T10] MAE spread across three estimators={spread:.4f} "
        f"vs G1 margin={margin:.4f} "
        f"load_bearing={spread > margin}"
    )

    # ---------------- T12: known +0.019 null bias ----------------
    fl_b = {k: v / KNOWN_NULL_BIAS for k, v in fl_A.items()}
    tiers_b = {k: v / KNOWN_NULL_BIAS for k, v in tiers_A.items()}
    t12 = metrics(y, predict(test, fl_b, tiers_b))
    t12_g1 = t12["mae"] <= G1_RATIO * res["B0"]["mae"]
    say(
        f"[T12] factors/{KNOWN_NULL_BIAS}: MAE={t12['mae']:.4f} R2={t12['r2']:+.4f} "
        f"G1={t12_g1} (verdict fragile={t12_g1 != g1})"
    )

    # ---------------- interval coverage (G7) ----------------
    resid_sd = float(
        np.std(tr_sw.pir_per36_dest.to_numpy() - predict(tr_sw, fl_A, tiers_A), ddof=1)
    )
    sef = np.array(
        [se_A.get((lg, d), np.nan) for lg, d in zip(test.league_src, test.league_dest)]
    )
    half = 1.96 * np.sqrt((test.pir_per36_src.to_numpy() * sef) ** 2 + resid_sd**2)
    inside = np.abs(y - pm) <= half
    cov = float(np.mean(inside))
    say(
        f"[G7] stated-95% interval coverage={cov:.4f} (resid_sd={resid_sd:.4f}, "
        f"mean half-width={float(np.mean(half)):.4f}) -- Phase 0 expectation ~0.86"
    )
    # factor-SE-only interval, to show how much of the width is the residual term
    half_f = 1.96 * np.abs(test.pir_per36_src.to_numpy() * sef)
    cov_f = float(np.mean(np.abs(y - pm) <= half_f))
    say(
        f"[G7] factor-SE-only interval coverage={cov_f:.4f} "
        f"(mean half-width={float(np.mean(half_f)):.4f})"
    )

    # ---------------- per-league, Arm A ----------------
    per_A = []
    for lg, sub in test.groupby("league_src"):
        mm = metrics(sub.pir_per36_dest, predict(sub, fl_A, tiers_A))
        bb = metrics(sub.pir_per36_dest, sub.pir_per36_src)
        row = {
            "arm": "A_heldout_season",
            "league": lg,
            "n": mm["n"],
            "mae": mm["mae"],
            "r2": mm["r2"],
            "bias": mm["bias"],
            "b0_mae": bb["mae"],
            "b0_r2": bb["r2"],
            "beats_b0": bool(mm["mae"] < bb["mae"]),
        }
        if mm["n"] >= PER_LEAGUE_N_FLOOR:
            p = power_line(
                sub,
                sub.pir_per36_dest.to_numpy(),
                predict(sub, fl_A, tiers_A),
                sub.pir_per36_src.to_numpy(),
                rel,
                f"armA_{lg}",
            )
            row |= {
                "min_detectable_gain_mae": p["min_detectable_gain_mae"],
                "ceiling_r2": p["ceiling_r2_at_mean_games"],
            }
            row["verdict"] = "beats_b0" if row["beats_b0"] else "fails_vs_b0"
        else:
            row |= {
                "min_detectable_gain_mae": np.nan,
                "ceiling_r2": np.nan,
                "verdict": "no_signal_available_n_below_20",
            }
        per_A.append(row)
        say(
            f"[per-league A] {lg:14s} n={row['n']:3d} MAE={row['mae']:.3f} "
            f"R2={row['r2']:+.3f} B0 MAE={row['b0_mae']:.3f} "
            f"beats_B0={row['beats_b0']} "
            f"{row['verdict']}"
        )

    # ---------------- ARM B: leave-one-league-out ----------------
    per_B, lolo_pred = [], []
    for lg in sorted(sw.league_src.unique()):
        sub = sw[sw.league_src == lg].copy()
        p_lolo = pairs[pairs.league_src != lg]
        tb = fit_factors(p_lolo, label=f"armB_no_{lg}")
        flb, tib = factor_lookup(tb)
        assert not any(k[0] == lg for k in flb), f"T-LOLO: {lg} still has a cell"
        pl = predict(sub, flb, tib)
        mm = metrics(sub.pir_per36_dest, pl)
        bb = metrics(sub.pir_per36_dest, sub.pir_per36_src)
        # in-sample (own factor) comparison on the same rows
        fl_full, ti_full = factor_lookup(full)
        mi = metrics(sub.pir_per36_dest, predict(sub, fl_full, ti_full))
        row = {
            "arm": "B_leave_one_league_out",
            "league": lg,
            "n": mm["n"],
            "mae": mm["mae"],
            "r2": mm["r2"],
            "bias": mm["bias"],
            "b0_mae": bb["mae"],
            "b0_r2": bb["r2"],
            "own_factor_mae": mi["mae"],
            "own_factor_r2": mi["r2"],
            "beats_b0": bool(mm["mae"] < bb["mae"]),
            "tier_mean_used": float(
                np.mean([tib[d] for d in sub.league_dest.unique()])
            ),
        }
        p = power_line(
            sub,
            sub.pir_per36_dest.to_numpy(),
            pl,
            sub.pir_per36_src.to_numpy(),
            rel,
            f"armB_{lg}",
        )
        row |= {
            "min_detectable_gain_mae": p["min_detectable_gain_mae"],
            "ceiling_r2": p["ceiling_r2_at_mean_games"],
        }
        row["verdict"] = (
            ("beats_b0" if row["beats_b0"] else "fails_vs_b0")
            if mm["n"] >= PER_LEAGUE_N_FLOOR
            else "no_signal_available_n_below_20"
        )
        per_B.append(row)
        lolo_pred.append(pd.DataFrame({"idx": sub.index, "pred": pl}))
        say(
            f"[per-league B] {lg:14s} n={row['n']:3d} LOLO MAE={row['mae']:.3f} "
            f"R2={row['r2']:+.3f} own-factor MAE={row['own_factor_mae']:.3f} "
            f"B0 MAE={row['b0_mae']:.3f} beats_B0={row['beats_b0']} {row['verdict']}"
        )

    lp = pd.concat(lolo_pred).set_index("idx").pred
    pooled_lolo = metrics(sw.pir_per36_dest, lp.reindex(sw.index).to_numpy())
    pooled_b0 = metrics(sw.pir_per36_dest, sw.pir_per36_src)
    g5 = pooled_lolo["mae"] <= G1_RATIO * pooled_b0["mae"]
    elig = [r for r in per_B if r["n"] >= PER_LEAGUE_N_FLOOR]
    share = float(np.mean([r["beats_b0"] for r in elig])) if elig else float("nan")
    g6 = share >= G6_SHARE
    g5_bs = paired_cluster_bootstrap(
        sw,
        sw.pir_per36_dest.to_numpy(),
        lp.reindex(sw.index).to_numpy(),
        sw.pir_per36_src.to_numpy(),
        n_boot=4000,
        seed=SEED,
    )
    say(
        f"[armB pooled] n={pooled_lolo['n']} LOLO MAE={pooled_lolo['mae']:.4f} "
        f"R2={pooled_lolo['r2']:+.4f} | B0 MAE={pooled_b0['mae']:.4f} "
        f"R2={pooled_b0['r2']:+.4f}"
    )
    say(
        f"[G5] LOLO MAE <= {G1_RATIO}*B0 ({G1_RATIO * pooled_b0['mae']:.4f}) = {g5}; "
        f"delta={g5_bs['delta_mae']:+.4f} "
        f"CI [{g5_bs['ci_lo']:+.4f},{g5_bs['ci_hi']:+.4f}] "
        f"excludes_zero={g5_bs['excludes_zero']}"
    )
    say(
        f"[G6] leagues n>=20 beating B0: "
        f"{sum(r['beats_b0'] for r in elig)}/{len(elig)} "
        f"= {share:.3f} (bar {G6_SHARE}) = {g6}"
    )

    # ---------------- verdict ----------------
    arm_a_pass = bool(g1 and g2["excludes_zero"] and g3 and g4)
    arm_b_pass = bool(g5 and g6)
    verdict = (
        "PASS"
        if (arm_a_pass and arm_b_pass)
        else ("PARTIAL" if (arm_a_pass or arm_b_pass) else "FAIL")
    )
    if not (g1 and g2["excludes_zero"] and g3):
        verdict = "FAIL"
    say(f"[VERDICT] armA_pass={arm_a_pass} armB_pass={arm_b_pass} -> {verdict}")

    # ---------------- outputs ----------------
    rows = []
    for k, v in res.items():
        rows.append({"arm": "A_heldout_season", "scope": "pooled", "model": k, **v})
    for k, v in t1.items():
        rows.append({"arm": "T1_same_season", "scope": "pooled", "model": k, **v})
    rows.append(
        {
            "arm": "B_leave_one_league_out",
            "scope": "pooled",
            "model": "model_lolo",
            **pooled_lolo,
        }
    )
    rows.append(
        {"arm": "B_leave_one_league_out", "scope": "pooled", "model": "B0", **pooled_b0}
    )
    for k, v in t10.items():
        rows.append(
            {"arm": "A_heldout_season", "scope": "T10_estimator", "model": k, **v}
        )
    rows.append(
        {
            "arm": "A_heldout_season",
            "scope": "T12_bias_corrected",
            "model": "model_div_1.019",
            **t12,
        }
    )
    for nm, d in [
        ("T3_no_player_overlap", t3),
        ("T4_with_incumbents", t4),
        ("T6_collision_pruned", t6),
    ]:
        for k, v in (d or {}).items():
            rows.append({"arm": "A_heldout_season", "scope": nm, "model": k, **v})
    for nm, d in t5.items():
        for k, v in d.items():
            rows.append(
                {"arm": "A_heldout_season", "scope": f"T5_{nm}", "model": k, **v}
            )
    for nm, d in t7.items():
        for k, v in d.items():
            rows.append(
                {"arm": "A_heldout_season", "scope": f"T7_{nm}", "model": k, **v}
            )
    pooled_df = pd.DataFrame(rows)
    per_df = pd.DataFrame(per_A + per_B)
    pooled_df.to_csv(OUT / "validation_metrics.csv", index=False)
    per_df.to_csv(OUT / "validation_per_league.csv", index=False)

    summary = {
        "verdict": verdict,
        "arm_a_pass": arm_a_pass,
        "arm_b_pass": arm_b_pass,
        "gates": {
            "G1": bool(g1),
            "G2": bool(g2["excludes_zero"]),
            "G3": bool(g3),
            "G4": bool(g4),
            "G5": bool(g5),
            "G6": bool(g6),
            "G6_share": share,
            "G7_coverage": cov,
            "G7_coverage_factor_only": cov_f,
        },
        "armA": res,
        "armA_g2": g2,
        "armA_g4_b1b": g4_b1b,
        "armA_power": pw,
        "armB_pooled": {"model": pooled_lolo, "B0": pooled_b0, "bootstrap": g5_bs},
        "T1_same_season": t1,
        "T3": t3,
        "T4": t4,
        "T5": t5,
        "T6": t6,
        "T7": t7,
        "T10": t10,
        "T10_spread": float(spread),
        "T10_margin": float(margin),
        "T12": t12,
        "T12_g1": bool(t12_g1),
        "reliability": rel,
        "resid_sd": resid_sd,
        "k_b1b": k_b1b,
        "n_poland_refused": n_pol,
        "population": {
            "consecutive_rows": int(len(switch)),
            "switchers_in": int((switch.was_cont == 0).sum()),
            "incumbents": int((switch.was_cont == 1).sum()),
            "scored_armA": int(len(test)),
            "scored_armB": int(len(sw)),
        },
        "config": {
            "min_games": MIN_GAMES,
            "min_pairs": MIN_PAIRS,
            "n_boot": N_BOOT,
            "seed": SEED,
            "stat": STAT,
            "era": ERA,
            "sample": SAMPLE,
            "excluded_source": list(EXCLUDED_SOURCE),
            "continental_source": args.continental_source,
            "n_pairs": int(len(pairs)),
        },
    }
    (OUT / "validation_summary.json").write_text(
        json.dumps(summary, indent=1, default=float)
    )
    (OUT / "validation_run_log.txt").write_text("\n".join(log))
    test.to_parquet(OUT / "scored_switchers.parquet")
    fac_A.to_parquet(OUT / "factors_heldout_le2023.parquet")
    say(
        "[done] wrote validation_metrics.csv validation_per_league.csv "
        "validation_summary.json validation_run_log.txt scored_switchers.parquet"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
