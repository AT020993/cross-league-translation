#!/usr/bin/env python3
"""Decision value of league translation: E7 (D1, D2, D3), E8 and E9.

Pre-registration: docs/research/sloan-full-paper-preregistration-2026-11-03.md
(commit f52e7c831, pushed 2026-11-03T09:15:02Z, before this file existed),
sections E7, E8 and E9. Every analysis here is EXPLORATORY: destination
seasons 2020-2025 were inspected for the submitted abstract.

* E7 -- decision terms on the 674 v10 anchor forecasts (pool A), pools =
  destination competition x destination season (12). D1 pairwise ordering
  accuracy; D2 (primary) the share of within-pool head-to-head comparisons
  whose order flips when translation is added to the league-aware model, and
  the share of those the translation model gets right (null 0.5); D3 top-5 /
  top-10 shortlist overlap and the mean realised EFF/36 of each shortlist. The
  D1 ceiling is the split-half (odd/even appearances in date order) pairwise
  ordering accuracy from per-game box scores, seasons 2020-2025 only.
* E8 -- walk-forward split-conformal intervals on absolute residuals.
* E9 -- source-league adjustments as tiers by the pre-registered 0.90 rule.

Threats and their controls (all in this file): drift from the submitted
numbers (G0 re-run with its negative control); a changed target set (674 keys,
12 pools, four finite arms, scope gate with an impossible-count negative
control); arithmetic error in the pair counts (D1/D2 identity gate); a box-score
ceiling computed on different games than the outcome (per-target reconciliation
gate on games, minutes and EFF); 2026-27 exposure (the box-score loader is
called for 2020-2025 only and refuses any later season); bootstrap duplicates
paired with themselves (pairs of copies of one forecast are excluded from every
denominator).
"""

# ruff: noqa: E501 -- gate messages and licensed sentences
from __future__ import annotations

if __name__ == "__main__":
    import sys as _sys
    from pathlib import Path as _Path

    _sys.path.insert(0, str(_Path(__file__).resolve().parents[1]))
    from src.research.execution import enter as _enter

    _enter(__file__)

import argparse
import json
import math
import os
from pathlib import Path
import sys

for _name in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_name, "1")
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from scripts import calibrate_prediction_intervals as intervals  # noqa: E402
from scripts import sloan_context_benchmarks as benchmark  # noqa: E402
from scripts import sloan_fullpaper_common as common  # noqa: E402
from scripts.translation_research_common import sha256_file  # noqa: E402
from src.data.corpus.euroleague_api import (  # noqa: E402
    load_api_continental,
    pairing_key,
)

KEY = common.KEY
OUTCOME = "pir_per36_dest"  # holds EFF/36 exactly (v10 naming)
N_BOOT = 2000
SEED = 0
POOL_KEY = ["league_dest", "season_dest"]
EXPECTED_POOLS = 12
EXPECTED_TARGETS = 674

HISTORY = common.PRIMARY_ARMS["history"]
HISTORY_T = common.PRIMARY_ARMS["history_translation"]
OFFSETS = common.PRIMARY_ARMS["offsets10"]
OFFSETS_T = common.PRIMARY_ARMS["offsets10_translation"]
MODELS = (HISTORY, HISTORY_T, OFFSETS, OFFSETS_T)
LABELS = {
    HISTORY: "history",
    HISTORY_T: "history + translation",
    OFFSETS: "offsets λ10",
    OFFSETS_T: "offsets λ10 + translation",
}
#: D1 contrasts, (first, second); a positive difference favours the second.
D1_CONTRASTS = ((HISTORY_T, OFFSETS), (OFFSETS, OFFSETS_T))
#: D2: primary is the league-aware model with vs without translation.
D2_PRIMARY = (OFFSETS, OFFSETS_T)
D2_REFERENCE = (HISTORY, HISTORY_T)
D2_CONTRASTS = (D2_PRIMARY, D2_REFERENCE)
#: D3 overlaps: with/without translation (both families) and the head-to-head.
D3_CONTRASTS = ((OFFSETS, OFFSETS_T), (HISTORY, HISTORY_T), (HISTORY_T, OFFSETS))
TOP_K = (5, 10)

E8_ARMS = (OFFSETS, HISTORY_T)
E8_LEVELS = (0.80, 0.95)
E8_EVALUATION = tuple(range(2021, 2026))

E9_ARM = OFFSETS
E9_SOURCE_RATE = 16.0
E9_HISTORY = 16.0
E9_LAST_SEASON = 2025
TIER_SHARE = 0.90
DESTINATIONS = ("euroleague", "eurocup")

CEILING_SEASONS = tuple(range(2020, 2026))  # never 2026 (2026-27 is unexposed)
POWER_Z = 1.959964 + 0.841621  # two-sided 5%, 80% power


class GateFailure(common.GateFailure):
    pass


def tag(first: str, second: str) -> str:
    return f"{first}__{second}"


# ------------------------------------------------------------------ gates --
def assert_scope(
    rows: pd.DataFrame,
    *,
    expected_targets: int = EXPECTED_TARGETS,
    expected_pools: int = EXPECTED_POOLS,
) -> dict:
    """674 targets, 12 pools, the four models finite, anchor seasons only."""
    n_pools = rows.groupby(POOL_KEY).ngroups
    finite = np.isfinite(rows[list(MODELS) + [OUTCOME]].to_numpy(float)).all()
    seasons = sorted(int(s) for s in rows.season_dest.unique())
    problems = []
    if len(rows) != expected_targets:
        problems.append(f"{len(rows)} targets (expected {expected_targets})")
    if n_pools != expected_pools:
        problems.append(f"{n_pools} pools (expected {expected_pools})")
    if not finite:
        problems.append("a model forecast or outcome is not finite")
    if seasons != list(common.ANCHOR_SEASONS):
        problems.append(f"seasons {seasons} differ from the anchor 2020-2025")
    if rows.duplicated(KEY).any():
        problems.append("duplicate target keys")
    if problems:
        raise GateFailure("scope gate failed: " + "; ".join(problems))
    return {"targets": int(len(rows)), "pools": int(n_pools), "seasons": seasons}


def assert_identity(pool_counts: pd.DataFrame, tolerance: float = 1e-12) -> float:
    """D1 difference equals (2 x right - flipped) / unequal pairs, per pool.

    Exact when neither model has tied forecasts inside a pool; a tie makes the
    identity inapplicable, which this gate also refuses.
    """
    worst = 0.0
    for first, second in D2_CONTRASTS:
        t = tag(first, second)
        for _, row in pool_counts.iterrows():
            if row[f"ties:{first}"] or row[f"ties:{second}"]:
                raise GateFailure(
                    "tied forecasts inside a pool; identity not applicable"
                )
            d1 = (row[f"correct:{second}"] - row[f"correct:{first}"]) / row["unequal"]
            d2 = (2 * row[f"right:{t}"] - row[f"flips_unequal:{t}"]) / row["unequal"]
            worst = max(worst, abs(d1 - d2))
    if not worst <= tolerance:
        raise GateFailure(
            f"D1/D2 identity off by {worst:.3e} (tolerance {tolerance:.0e})"
        )
    return float(worst)


def assert_reconciled(recon: pd.DataFrame, tolerance: float = 1e-6) -> list:
    """Per-game box scores rebuild every target's games, minutes and EFF."""
    bad = recon.loc[
        recon.games.isna()
        | recon.games.ne(recon.games_dest)
        | (recon.minutes - recon.minutes_dest).abs().gt(tolerance)
        | (recon.eff - recon.pir_dest).abs().gt(tolerance)
    ]
    if len(bad):
        raise GateFailure(
            f"{len(bad)} targets do not reconcile to the cohort: "
            + ", ".join(
                f"{r.player_name} {int(r.season_dest)}" for r in bad.itertuples()
            )
        )
    return []


def negative_control(check, *args, **kwargs) -> str:
    """A gate that cannot fail checks nothing (METHOD.md §8)."""
    try:
        check(*args, **kwargs)
    except GateFailure:
        return "rejected as required"
    raise GateFailure(f"negative control passed for {check.__name__}")


# --------------------------------------------------------------- pooling --
def pools(rows: pd.DataFrame) -> list:
    out = []
    for key, group in rows.groupby(POOL_KEY, sort=True):
        frame = group.sort_values(KEY).reset_index(drop=True)
        out.append(((str(key[0]), int(key[1])), frame))
    return out


def cluster_index(frame: pd.DataFrame) -> list:
    """Row positions of each destination club-season, in sorted cluster order."""
    codes = pd.factorize(frame.cluster, sort=True)[0]
    return [np.flatnonzero(codes == c) for c in range(codes.max() + 1)]


def cluster_draw(groups: list, rng: np.random.Generator) -> np.ndarray:
    """Row positions of one cluster-bootstrap resample (clusters with replacement)."""
    picks = rng.integers(0, len(groups), len(groups))
    return np.concatenate([groups[i] for i in picks])


# ------------------------------------------------------------ pair counts --
def pair_counts(y: np.ndarray, preds: dict, origin: np.ndarray) -> dict:
    """Within-pool pair counts; pairs of two copies of one forecast are excluded.

    correct[arm]: pairs with unequal outcomes ordered as the outcome (a tied
    forecast counts one half). flips[a__b]: pairs whose predicted order is
    strictly reversed between a and b. right[a__b]: flipped pairs with unequal
    outcomes on which b orders correctly.
    """
    i, j = np.triu_indices(len(y), 1)
    keep = origin[i] != origin[j]
    i, j = i[keep], j[keep]
    dy = np.sign(y[i] - y[j])
    unequal = dy != 0
    out = {"pairs": int(len(i)), "unequal": int(unequal.sum())}
    signs = {}
    for arm, p in preds.items():
        dp = np.sign(p[i] - p[j])
        signs[arm] = dp
        out[f"correct:{arm}"] = float(
            np.sum((dp == dy) & unequal) + 0.5 * np.sum((dp == 0) & unequal)
        )
        out[f"ties:{arm}"] = int(np.sum(dp == 0))
    for first, second in D2_CONTRASTS:
        t = tag(first, second)
        flip = signs[first] * signs[second] < 0
        out[f"flips:{t}"] = int(flip.sum())
        out[f"flips_unequal:{t}"] = int((flip & unequal).sum())
        out[f"right:{t}"] = int((flip & unequal & (signs[second] == dy)).sum())
    return out


def split_half_counts(odd: np.ndarray, even: np.ndarray, origin: np.ndarray) -> dict:
    """Pairs ordered the same way by the odd and by the even half of the season."""
    i, j = np.triu_indices(len(odd), 1)
    keep = origin[i] != origin[j]
    i, j = i[keep], j[keep]
    a, b = np.sign(odd[i] - odd[j]), np.sign(even[i] - even[j])
    usable = (a != 0) & (b != 0)
    return {
        "half_pairs": int(usable.sum()),
        "half_agree": int(((a == b) & usable).sum()),
    }


def ratios(c: dict) -> dict:
    """Pooled shares from summed pair counts."""
    r = {f"d1:{arm}": c[f"correct:{arm}"] / c["unequal"] for arm in MODELS}
    for first, second in D1_CONTRASTS:
        r[f"d1diff:{tag(first, second)}"] = r[f"d1:{second}"] - r[f"d1:{first}"]
    for first, second in D2_CONTRASTS:
        t = tag(first, second)
        r[f"flip_share:{t}"] = c[f"flips:{t}"] / c["pairs"]
        r[f"right_share:{t}"] = (
            c[f"right:{t}"] / c[f"flips_unequal:{t}"]
            if c[f"flips_unequal:{t}"]
            else math.nan
        )
    r["ceiling_split_half"] = (
        c["half_agree"] / c["half_pairs"] if c["half_pairs"] else math.nan
    )
    return r


# ------------------------------------------------------------------- top-k --
def top_k(pred: np.ndarray, k: int) -> np.ndarray:
    """Positions of the k highest forecasts; ties broken by key order (stable)."""
    return np.argsort(-pred, kind="stable")[:k]


def shortlist_stats(y: np.ndarray, preds: dict) -> dict:
    out = {}
    for k in TOP_K:
        tops = {arm: top_k(p, k) for arm, p in preds.items()}
        for arm in preds:
            out[f"realised:{k}:{arm}"] = float(y[tops[arm]].mean())
        for first, second in D3_CONTRASTS:
            a, b = set(tops[first].tolist()), set(tops[second].tolist())
            out[f"jaccard:{k}:{tag(first, second)}"] = len(a & b) / len(a | b)
            out[f"realised_diff:{k}:{tag(first, second)}"] = (
                out[f"realised:{k}:{second}"] - out[f"realised:{k}:{first}"]
            )
    return out


# ----------------------------------------------------------------- E7 run --
def interval(draws) -> list:
    d = np.asarray(draws, float)
    d = d[np.isfinite(d)]
    return [float(np.percentile(d, 2.5)), float(np.percentile(d, 97.5))]


def power_line(draws) -> dict:
    """Minimum effect detectable with 80% power at two-sided 5%: 2.80 x bootstrap SE."""
    se = float(np.nanstd(np.asarray(draws, float), ddof=1))
    return {"bootstrap_se": se, "mde_80": float(POWER_Z * se)}


def e7(rows: pd.DataFrame, halves: pd.DataFrame, *, n_boot=N_BOOT, seed=SEED) -> dict:
    """D1, D2, D3 and the split-half ceiling, with one joint cluster bootstrap.

    Every draw resamples destination club-seasons within each of the 12 pools
    (seed 0), so pooled and per-pool intervals come from the same draws.
    """
    rows = rows.merge(
        halves[KEY + ["odd_rate", "even_rate"]], on=KEY, how="left", validate="1:1"
    )
    pool_list = pools(rows)
    data = []
    for (league, season), frame in pool_list:
        data.append(
            {
                "name": f"{league}|{season}",
                "league": league,
                "season": season,
                "y": frame[OUTCOME].to_numpy(float),
                "p": {arm: frame[arm].to_numpy(float) for arm in MODELS},
                "odd": frame.odd_rate.to_numpy(float),
                "even": frame.even_rate.to_numpy(float),
                "groups": cluster_index(frame),
                "n": len(frame),
                "clusters": int(frame.cluster.nunique()),
            }
        )

    def evaluate(index_sets):
        counts, shorts = [], []
        for d, idx in zip(data, index_sets):
            y, preds = d["y"][idx], {a: p[idx] for a, p in d["p"].items()}
            c = pair_counts(y, preds, idx)
            c.update(split_half_counts(d["odd"][idx], d["even"][idx], idx))
            counts.append(c)
            shorts.append(shortlist_stats(y, preds))
        return pd.DataFrame(counts), pd.DataFrame(shorts)

    point_counts, point_short = evaluate([np.arange(d["n"]) for d in data])
    point_counts.index = point_short.index = [d["name"] for d in data]
    count_cols, short_cols = list(point_counts.columns), list(point_short.columns)

    rng = np.random.default_rng(seed)
    count_draws = np.empty((n_boot, len(data), len(count_cols)))
    short_draws = np.empty((n_boot, len(data), len(short_cols)))
    for b in range(n_boot):
        c, s = evaluate([cluster_draw(d["groups"], rng) for d in data])
        count_draws[b], short_draws[b] = (
            c[count_cols].to_numpy(float),
            s[short_cols].to_numpy(float),
        )

    def boot_ratios(sel):
        out = []
        for b in range(n_boot):
            out.append(ratios(dict(zip(count_cols, count_draws[b][sel].sum(axis=0)))))
        return pd.DataFrame(out)

    def summarise(sel, label):
        point = ratios(point_counts.loc[sel].sum().to_dict())
        boot = boot_ratios(sel)
        short_point = point_short.loc[sel].mean().to_dict()  # each pool weighs equally
        short_boot = pd.DataFrame(
            short_draws[:, sel, :].mean(axis=1), columns=short_cols
        )
        out = {
            "label": label,
            "pools": int(sel.sum()),
            "forecasts": int(sum(d["n"] for d, s in zip(data, sel) if s)),
            "pairs": int(point_counts.loc[sel, "pairs"].sum()),
            "unequal_pairs": int(point_counts.loc[sel, "unequal"].sum()),
            "values": {},
        }
        for name, value in {**point, **short_point}.items():
            draws = (boot if name in boot.columns else short_boot)[name].to_numpy(float)
            entry = {"point": float(value), "ci95": interval(draws)}
            if name.startswith(("d1diff:", "right_share:", "realised_diff:")):
                entry.update(power_line(draws))
            out["values"][name] = entry
        for first, second in D2_CONTRASTS:
            t = tag(first, second)
            for what in ("flips", "flips_unequal", "right"):
                out["values"][f"{what}:{t}"] = int(
                    point_counts.loc[sel, f"{what}:{t}"].sum()
                )
        return out

    league = np.array([d["league"] for d in data])
    pooled = {
        "all": summarise(np.ones(len(data), bool), "all 12 pools"),
        "euroleague": summarise(league == "euroleague", "EuroLeague pools"),
        "eurocup": summarise(league == "eurocup", "EuroCup pools"),
    }

    per_pool = []
    for p, d in enumerate(data):
        sel = np.zeros(len(data), bool)
        sel[p] = True
        point = ratios(point_counts.iloc[p].to_dict())
        boot = boot_ratios(sel)
        row = {
            "destination": d["league"],
            "season": d["season"],
            "forecasts": d["n"],
            "club_seasons": d["clusters"],
            "pairs": int(point_counts.iloc[p]["pairs"]),
            "unequal_pairs": int(point_counts.iloc[p]["unequal"]),
        }
        for arm in MODELS:
            row[f"d1_{arm}"] = point[f"d1:{arm}"]
        for first, second in D2_CONTRASTS:
            t = tag(first, second)
            row[f"flips_{t}"] = int(point_counts.iloc[p][f"flips:{t}"])
            for what in ("flip_share", "right_share"):
                row[f"{what}_{t}"] = point[f"{what}:{t}"]
                row[f"{what}_{t}_ci_low"], row[f"{what}_{t}_ci_high"] = interval(
                    boot[f"{what}:{t}"]
                )
        row["ceiling_split_half"] = point["ceiling_split_half"]
        for k in TOP_K:
            for first, second in D3_CONTRASTS:
                row[f"jaccard_top{k}_{tag(first, second)}"] = point_short.iloc[p][
                    f"jaccard:{k}:{tag(first, second)}"
                ]
            for arm in MODELS:
                row[f"realised_top{k}_{arm}"] = point_short.iloc[p][
                    f"realised:{k}:{arm}"
                ]
        per_pool.append(row)
    return {
        "pooled": pooled,
        "per_pool": pd.DataFrame(per_pool),
        "pool_counts": point_counts,
    }


# ---------------------------------------------------- split-half reference --
def per_game_rows(root: Path, seasons=CEILING_SEASONS):
    """EuroLeague-API box scores with game dates; 2020-2025 only, never 2026."""
    seasons = tuple(int(s) for s in seasons)
    if max(seasons) > 2025:
        raise GateFailure("the 2026-27 season is unexposed and may not be read")
    games, report = load_api_continental(root, seasons=seasons)
    if int(games.season.max()) > 2025:
        raise GateFailure("a 2026-27 player-game was loaded")
    dates = []
    for league in DESTINATIONS:
        for season in seasons:
            path = (
                Path(root)
                / "data/raw"
                / league
                / str(season)
                / "games"
                / f"season_{season}_games.parquet"
            )
            g = pd.read_parquet(path, columns=["gameCode", "date"])
            g["game_id"] = f"api-{league}-{season}-" + g.gameCode.astype(int).astype(
                str
            )
            dates.append(g[["game_id", "date"]])
    dates = pd.concat(dates, ignore_index=True)
    if dates.game_id.duplicated().any():
        raise GateFailure("duplicate game codes in the schedule files")
    dates["game_date"] = pd.to_datetime(dates.date, format="%b %d, %Y", errors="raise")
    games = games.merge(
        dates[["game_id", "game_date"]], on="game_id", how="left", validate="m:1"
    )
    if games.game_date.isna().any():
        raise GateFailure(
            f"{int(games.game_date.isna().sum())} player-games have no date"
        )
    games["player_name"] = games.player_name.map(pairing_key)
    games["gamecode"] = games.game_id.str.rsplit("-", n=1).str[-1].astype(int)
    report["seasons_read"] = list(seasons)
    return games, report


def split_halves(games: pd.DataFrame, rows: pd.DataFrame):
    """Odd/even appearances in date order; minutes-weighted EFF/36 per half."""
    target = rows[KEY + ["league_dest", "games_dest", "minutes_dest", "pir_dest"]]
    g = games.merge(
        target,
        left_on=["player_name", "season", "league"],
        right_on=["player_name", "season_dest", "league_dest"],
        how="inner",
    ).sort_values(
        ["player_name", "season_dest", "game_date", "gamecode"], kind="stable"
    )
    g["appearance"] = g.groupby(KEY).cumcount()
    g["half"] = np.where(
        g.appearance % 2 == 0, "odd", "even"
    )  # 1st, 3rd, ... appearance
    recon = (
        g.groupby(KEY)
        .agg(
            games=("game_id", "nunique"), minutes=("minutes", "sum"), eff=("pir", "sum")
        )
        .reset_index()
    )
    recon = target.merge(recon, on=KEY, how="left", validate="1:1")
    halves = (
        g.groupby(KEY + ["half"])
        .agg(eff=("pir", "sum"), minutes=("minutes", "sum"), n=("game_id", "nunique"))
        .reset_index()
    )
    halves["rate"] = 36 * halves.eff / halves.minutes
    wide = halves.pivot(index=KEY, columns="half", values=["rate", "n"])
    wide.columns = [
        f"{half}_{'rate' if what == 'rate' else 'games'}" for what, half in wide.columns
    ]
    return wide.reset_index(), recon


def reliability(halves: pd.DataFrame, rows: pd.DataFrame) -> dict:
    """Split-half correlation (pool-demeaned) and two normal-model readings."""
    m = rows[KEY + ["league_dest"]].merge(halves, on=KEY, validate="1:1")
    for col in ("odd_rate", "even_rate"):
        m[col + "_c"] = m[col] - m.groupby(POOL_KEY)[col].transform("mean")
    r = float(np.corrcoef(m.odd_rate_c, m.even_rate_c)[0, 1])
    full = 2 * r / (1 + r)
    return {
        "note": (
            "half_vs_half is the pre-registered split-half reading: both halves carry half-season "
            "noise, so it is a floor-like reference, not an upper bound. The full-season reading "
            "(normal model, Spearman-Brown) is supplementary and not pre-registered."
        ),
        "split_half_r_within_pool": r,
        "spearman_brown_full_season": full,
        "normal_model_half_vs_half_concordance": 0.5 + math.asin(r) / math.pi,
        "normal_model_true_rate_vs_full_season_concordance": 0.5
        + math.asin(math.sqrt(full)) / math.pi,
        "mean_games_per_half": float(
            np.mean([m.odd_games.mean(), m.even_games.mean()])
        ),
        "targets": int(len(m)),
    }


def reachable(pooled: dict, rel: dict) -> dict:
    """(D1 - 0.5) / (full-season normal-model concordance - 0.5), per model.

    Supplementary (not pre-registered): the share of the ordering accuracy
    above chance that a forecaster who knew each player's true rate would reach.
    """
    bound = rel["normal_model_true_rate_vs_full_season_concordance"]
    return {
        arm: (pooled["values"][f"d1:{arm}"]["point"] - 0.5) / (bound - 0.5)
        for arm in MODELS
    }


# -------------------------------------------------------------------- E8 --
def conformal_rows(rows: pd.DataFrame, arm: str, level: float):
    """Season s is calibrated on anchor residuals of seasons < s only."""
    alpha = 1 - level
    out, quantiles = [], {}
    for season in E8_EVALUATION:
        calib = rows.loc[rows.season_dest.lt(season)]
        scores = np.abs(calib[OUTCOME] - calib[arm]).to_numpy(float)
        q = intervals.conformal_quantile(scores, alpha=alpha)
        quantiles[str(season)] = {
            "calibration_n": int(len(scores)),
            "half_width": float(q),
        }
        test = rows.loc[
            rows.season_dest.eq(season), KEY + ["league_dest", "cluster", OUTCOME, arm]
        ].copy()
        test["lo"], test["hi"] = test[arm] - q, test[arm] + q
        out.append(test)
    test = pd.concat(out, ignore_index=True)
    y = test[OUTCOME].to_numpy(float)
    test["hit"] = (y >= test.lo) & (y <= test.hi)
    test["width"] = test.hi - test.lo
    test["winkler"] = intervals.winkler(
        y, test.lo.to_numpy(), test.hi.to_numpy(), alpha=alpha
    )
    return test, quantiles


def e8(rows: pd.DataFrame, *, n_boot=N_BOOT, seed=SEED) -> dict:
    """Coverage, width and Winkler, by destination and pooled, 2021-2025.

    The bootstrap resamples destination club-seasons within each pool with
    each season's calibration quantile held fixed (it conditions on the
    calibration, as every interval in this paper conditions on fitted forecasts).
    """
    results, table = {}, []
    for arm in E8_ARMS:
        for level in E8_LEVELS:
            alpha = 1 - level
            test, quantiles = conformal_rows(rows, arm, level)
            test["pool"] = test.league_dest + "|" + test.season_dest.astype(str)
            frames = {
                p: f.reset_index(drop=True) for p, f in test.groupby("pool", sort=True)
            }
            groups = {p: cluster_index(f) for p, f in frames.items()}
            rng = np.random.default_rng(seed)
            scopes = ("pooled", *DESTINATIONS)
            draws = {s: np.empty((n_boot, 3)) for s in scopes}
            for b in range(n_boot):
                sample = pd.concat(
                    [frames[p].iloc[cluster_draw(groups[p], rng)] for p in frames],
                    ignore_index=True,
                )
                for s in scopes:
                    sub = (
                        sample
                        if s == "pooled"
                        else sample.loc[sample.league_dest.eq(s)]
                    )
                    draws[s][b] = [sub.hit.mean(), sub.width.mean(), sub.winkler.mean()]
            entry = {"calibration": quantiles, "scopes": {}}
            for s in scopes:
                sub = test if s == "pooled" else test.loc[test.league_dest.eq(s)]
                scored = intervals.score_rows(sub[OUTCOME], sub.lo, sub.hi, alpha=alpha)
                values = {
                    "n": scored["n"],
                    "coverage": scored["coverage"],
                    "coverage_ci95": interval(draws[s][:, 0]),
                    "mean_width": scored["mean_width"],
                    "mean_width_ci95": interval(draws[s][:, 1]),
                    "winkler": scored["winkler"],
                    "winkler_ci95": interval(draws[s][:, 2]),
                }
                entry["scopes"][s] = values
                table.append(
                    {
                        "arm": arm,
                        "level": level,
                        "scope": s,
                        "n": values["n"],
                        "coverage": values["coverage"],
                        "coverage_ci_low": values["coverage_ci95"][0],
                        "coverage_ci_high": values["coverage_ci95"][1],
                        "mean_width": values["mean_width"],
                        "winkler": values["winkler"],
                        "winkler_ci_low": values["winkler_ci95"][0],
                        "winkler_ci_high": values["winkler_ci95"][1],
                    }
                )
            for season in E8_EVALUATION:
                sub = test.loc[test.season_dest.eq(season)]
                scored = intervals.score_rows(sub[OUTCOME], sub.lo, sub.hi, alpha=alpha)
                table.append(
                    {"arm": arm, "level": level, "scope": f"season {season}", **scored}
                )
            results[f"{arm}@{level:.2f}"] = entry
    return {"results": results, "table": pd.DataFrame(table)}


# -------------------------------------------------------------------- E9 --
def e9_training(features: pd.DataFrame) -> pd.DataFrame:
    """All scorable training rows through destination season 2025."""
    if int(features.season_dest.max()) > E9_LAST_SEASON:
        raise GateFailure("features carry a destination season after 2025")
    train = features.loc[
        features.feature_eligible & features.season_dest.le(E9_LAST_SEASON)
    ]
    return train.sort_values(KEY).reset_index(drop=True)


def e9_grid(leagues) -> pd.DataFrame:
    """The reference player: source EFF/36 16, history 16, so not above own prior."""
    return pd.DataFrame(
        [
            {
                "league_dest": dest,
                "league_src": league,
                "pir_per36_src": E9_SOURCE_RATE,
                "prior_mean_pir36": E9_HISTORY,
                "above_own_prior": bool(E9_SOURCE_RATE > E9_HISTORY),
            }
            for dest in DESTINATIONS
            for league in leagues
        ]
    )


def assign_tiers(
    point: pd.Series, draws: pd.DataFrame, share: float = TIER_SHARE
) -> pd.DataFrame:
    """The pre-registered rule. Sort by point estimate; start a tier at the top
    league; the next league joins the current tier unless the tier's top league
    exceeds it in >= `share` of bootstrap draws, in which case it starts a new tier."""
    order = point.sort_values(ascending=False, kind="stable").index.tolist()
    tier, top, out = 1, order[0], []
    for league in order:
        beaten = math.nan
        if league != top:
            beaten = float(np.mean(draws[top].to_numpy() > draws[league].to_numpy()))
            if beaten >= share:
                tier, top = tier + 1, league
        out.append(
            {
                "league_src": league,
                "tier": tier,
                "tier_top": top,
                "share_previous_tier_top_higher": beaten,
            }
        )
    return pd.DataFrame(out)


def e9(features: pd.DataFrame, *, n_boot=N_BOOT, seed=SEED) -> dict:
    train = e9_training(features)
    leagues = sorted(train.league_src.unique())
    grid = e9_grid(leagues)
    point, info = benchmark.fit_model(train, grid, E9_ARM)
    if info["status"] != "ok":
        raise GateFailure(f"E9 fit failed: {info['status']}")
    groups = cluster_index(train)
    rng = np.random.default_rng(seed)
    draws = np.empty((n_boot, len(grid)))
    absent = {league: 0 for league in leagues}
    for b in range(n_boot):
        sample = train.iloc[cluster_draw(groups, rng)]
        present = set(sample.league_src.unique())
        for league in leagues:
            absent[league] += int(league not in present)
        draws[b], status = benchmark.fit_model(sample, grid, E9_ARM)
        if status["status"] != "ok":
            raise GateFailure(f"E9 bootstrap fit failed: {status['status']}")
    grid["forecast"] = point
    grid["ci95_low"] = np.percentile(draws, 2.5, axis=0)
    grid["ci95_high"] = np.percentile(draws, 97.5, axis=0)
    support = train.groupby("league_src").agg(
        training_forecasts=("player_name", "size"),
        training_club_seasons=("cluster", "nunique"),
    )
    tables = []
    for dest in DESTINATIONS:
        mask = grid.league_dest.eq(dest).to_numpy()
        sub = grid.loc[mask].set_index("league_src")
        sub_draws = pd.DataFrame(draws[:, mask], columns=sub.index)
        centred = sub_draws.sub(sub_draws.mean(axis=1), axis=0)
        table = assign_tiers(sub.forecast, sub_draws).merge(
            sub.reset_index(), on="league_src"
        )
        table["adjustment_vs_league_average"] = table.forecast - sub.forecast.mean()
        table["adjustment_ci95_low"] = [
            float(np.percentile(centred[x], 2.5)) for x in table.league_src
        ]
        table["adjustment_ci95_high"] = [
            float(np.percentile(centred[x], 97.5)) for x in table.league_src
        ]
        tables.append(table.merge(support, left_on="league_src", right_index=True))
    table = pd.concat(tables, ignore_index=True)
    return {
        "table": table,
        "training_forecasts": int(len(train)),
        "training_club_seasons": int(train.cluster.nunique()),
        "training_seasons": sorted(int(s) for s in train.season_dest.unique()),
        "draws_with_league_absent": absent,
        "coefficients": dict(zip(info["features"], info["coefficients"])),
    }


def club_csv(table: pd.DataFrame) -> pd.DataFrame:
    """The front-office table: tiers, not ranks; one row per league x destination."""
    out = table.copy()
    out["destination"] = out.league_dest.map(
        {"euroleague": "EuroLeague", "eurocup": "EuroCup"}
    )
    out["leagues_in_tier"] = out.groupby(["league_dest", "tier"]).league_src.transform(
        lambda s: "; ".join(sorted(s))
    )
    out["how_to_read"] = (
        "Forecast destination EFF/36 for a player who posted EFF/36 = 16 in this source league "
        "with a 16 career history (source season not above his own history). Leagues in the same "
        "tier are not distinguishable from one another; do not rank inside a tier."
    )
    cols = {
        "destination": "destination",
        "tier": "tier",
        "league_src": "source_league",
        "leagues_in_tier": "leagues_in_tier",
        "forecast": "forecast_eff36",
        "ci95_low": "forecast_ci95_low",
        "ci95_high": "forecast_ci95_high",
        "adjustment_vs_league_average": "adjustment_vs_average_league_eff36",
        "adjustment_ci95_low": "adjustment_ci95_low",
        "adjustment_ci95_high": "adjustment_ci95_high",
        "training_forecasts": "training_forecasts",
        "training_club_seasons": "training_club_seasons",
        "how_to_read": "how_to_read",
    }
    out = out[list(cols)].rename(columns=cols)
    out = out.sort_values(
        ["destination", "tier", "source_league"], ascending=[False, True, True]
    )
    numeric = [c for c in out.columns if c.startswith(("forecast_", "adjustment_"))]
    return out.round({c: 2 for c in numeric}).reset_index(drop=True)


# ------------------------------------------------------------------- main --
def licensed_d2(pooled: dict) -> str:
    """The pre-registered D2 sentence, with the coin-flip and power qualifiers."""
    v = pooled["values"]
    t = tag(*D2_PRIMARY)
    flip, right = v[f"flip_share:{t}"], v[f"right_share:{t}"]
    sentence = (
        f"Adding translation to the league-aware model changes {100 * flip['point']:.1f}% of "
        f"head-to-head comparisons (95% CI {100 * flip['ci95'][0]:.1f}-{100 * flip['ci95'][1]:.1f}%) "
        f"and is right on {100 * right['point']:.1f}% of those "
        f"(95% CI {100 * right['ci95'][0]:.1f}-{100 * right['ci95'][1]:.1f}%)"
    )
    if right["ci95"][0] <= 0.5 <= right["ci95"][1]:
        sentence += (
            ", which is not distinguishable from a coin flip; the smallest departure from 50% this "
            f"test could detect with 80% power is about {100 * right['mde_80']:.1f} percentage points"
        )
    elif right["ci95"][0] > 0.5:
        sentence += ", more often right than wrong"
    else:
        sentence += ", more often wrong than right"
    return sentence + "."


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument(
        "--raw-dir",
        type=Path,
        required=True,
        help="a data/raw directory holding {euroleague,eurocup}/<season> (2020-2025 only)",
    )
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--n-boot", type=int, default=N_BOOT)
    args = parser.parse_args(argv)
    root = Path.cwd()

    v9, v10_summary = common.load_references(root)
    rows, features, _ = common.anchor_rows(root, args.input_dir)
    diffs = common.g0_differences(rows, v9, v10_summary)
    try:
        common.assert_g0(diffs, tolerance=-1.0)
    except common.GateFailure:
        g0_control = "rejected as required"
    else:
        raise GateFailure("G0 negative control passed an impossible tolerance")
    common.assert_g0(diffs)

    scope_control = negative_control(
        assert_scope, rows, expected_targets=EXPECTED_TARGETS + 1
    )
    scope = assert_scope(rows)

    games, load_report = per_game_rows(args.raw_dir.resolve().parents[1])
    halves, recon = split_halves(games, rows)
    recon_control = negative_control(assert_reconciled, recon, tolerance=-1.0)
    assert_reconciled(recon)
    if halves[["odd_rate", "even_rate"]].isna().any().any() or len(halves) != len(rows):
        raise GateFailure("a target lacks an odd or an even half")

    decision = e7(rows, halves, n_boot=args.n_boot)
    identity_control = negative_control(
        assert_identity, decision["pool_counts"], tolerance=-1.0
    )
    identity_worst = assert_identity(decision["pool_counts"])
    calibrated = e8(rows, n_boot=args.n_boot)
    tiers = e9(features, n_boot=args.n_boot)

    args.out.mkdir(parents=True, exist_ok=False)
    keyed = rows[KEY + ["league_dest", "cluster", OUTCOME, *MODELS]].merge(
        halves, on=KEY, validate="1:1"
    )
    keyed.to_csv(args.out / "e7_keyed_forecasts.csv", index=False)
    decision["per_pool"].to_csv(args.out / "e7_pools.csv", index=False)
    calibrated["table"].to_csv(args.out / "e8_conformal.csv", index=False)
    tiers["table"].to_csv(args.out / "e9_league_tiers_full.csv", index=False)
    club_csv(tiers["table"]).to_csv(args.out / "e9_league_tiers_club.csv", index=False)

    summary = {
        "protocol_commit": common.PROTOCOL_COMMIT,
        "protocol_sha256": sha256_file(root / common.PROTOCOL),
        "input_sha256": {
            "pairs": common.PAIRS_SHA["official_corrected"],
            "cohort": common.COHORT_SHA,
        },
        "exploratory": True,
        "n_boot": args.n_boot,
        "seed": SEED,
        "models": {arm: LABELS[arm] for arm in MODELS},
        "mae": {arm: common.mae(rows, arm) for arm in MODELS},
        "gates": {
            "G0": {
                "status": "passed",
                "max_difference": max(diffs.values()),
                "tolerance": common.G0_TOLERANCE,
                "negative_control": g0_control,
            },
            "scope": {"status": "passed", **scope, "negative_control": scope_control},
            "box_score_reconciliation": {
                "status": "passed",
                "targets": int(len(recon)),
                "exceptions": [],
                "negative_control": recon_control,
            },
            "d1_d2_identity": {
                "status": "passed",
                "max_difference": identity_worst,
                "negative_control": identity_control,
            },
        },
        "box_scores": load_report,
        "e7": {
            "pooled": decision["pooled"],
            "reliability": reliability(halves, rows),
            "share_of_reachable_ordering": reachable(
                decision["pooled"]["all"], reliability(halves, rows)
            ),
            "licensed_d2": licensed_d2(decision["pooled"]["all"]),
        },
        "e8": calibrated["results"],
        "e9": {k: v for k, v in tiers.items() if k != "table"},
        "e9_reference_player": {
            "source_eff36": E9_SOURCE_RATE,
            "history_eff36": E9_HISTORY,
            "above_own_prior": bool(E9_SOURCE_RATE > E9_HISTORY),
            "arm": E9_ARM,
            "tier_share": TIER_SHARE,
        },
    }
    (args.out / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True, default=float) + "\n"
    )
    print(summary["e7"]["licensed_d2"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
