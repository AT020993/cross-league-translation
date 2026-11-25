#!/usr/bin/env python3
"""E15 of SSAC27 full-paper Amendment 1: which box-score skills travel.

Amendment: docs/research/sloan-full-paper-preregistration-amendment-1-2026-11-04.md
(commit f1a3453da, pushed alone before this file existed). Everything here is
EXPLORATORY: destination seasons 2017-2025 were already inspected.

Components per 36 minutes: points, offensive and defensive rebounds, assists,
steals, blocks, turnovers, 3-point attempts, free-throw attempts. Secondary,
with >= 20 attempts on both sides: 3P% and FT%.

* E15a (same player, same season). For each component, the exposure-weighted
  retention ratio (continental per-36 / domestic per-36) over the 4,074 pool-A
  factor-estimation pairs, with the house estimator of the factor table
  (per-pair ratio weighted by the thinner side's exposure; pairs with a zero
  domestic count cannot form a ratio and are counted, never hidden). Interval:
  cluster bootstrap by player, 2,000 draws, seed 0. Printed pooled, by
  destination, and by source league where a league has >= 75 pairs.
* E15b (arrivals, the 674 v10 targets). For each component: the source-
  destination correlation disattenuated by the destination split-half
  reliability (the E6 odd/even method applied to the component, from per-game
  continental box scores); the source-rate slope; and the lambda-10 source-
  offset spread in component SD units (the registered source_ridge_10 model,
  refitted with the component in place of EFF, history rebuilt by the v10
  rule). Interval: cluster bootstrap over destination club-seasons, 2,000
  draws, seed 0 (the registered default for ratios and coefficients).

Threats: estimator drift from the factor table (gate G15a reproduces every
EFF factor_raw of fit_table, with an impossible-tolerance negative control);
history drift (G3 on the rebuilt corpus, reused unchanged); per-game rows that
do not add up to the cohort (E6 reconciliation plus a per-component total gate
with a +1 negative control); 2026-27 leakage (only the frozen 2015-2025 raw
inventory is read, sha-checked by the robustness rebuild); zero denominators
(counted per component and subset).
"""

# ruff: noqa: E501 -- gate messages and labels
from __future__ import annotations

if __name__ == "__main__":
    import sys as _sys
    from pathlib import Path as _Path

    _sys.path.insert(0, str(_Path(__file__).resolve().parents[1]))
    from src.research.execution import enter as _enter

    _enter(__file__)

import argparse
import contextlib
import io
import itertools
import json
import os
from pathlib import Path
import sys

for _name in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_name, "1")
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from scripts import sloan_context_benchmarks as benchmark  # noqa: E402
from scripts import sloan_fullpaper_common as common  # noqa: E402
from scripts import sloan_fullpaper_robustness as robust  # noqa: E402
from scripts.translation_research_common import fit_table, sha256_file  # noqa: E402

KEY = common.KEY
AMENDMENT = (
    ROOT / "docs/research/sloan-full-paper-preregistration-amendment-1-2026-11-04.md"
)
AMENDMENT_COMMIT = "f1a3453dae4ed77b069ad8c12f963eb3e32d27ee"
N_BOOT = 2000
SEED = 0
ATTEMPT_FLOOR = 20
SOURCE_LEAGUE_FLOOR = 75
N_PAIRS = 4074
N_TARGETS = 674
OFFSET_ARM = "source_ridge_10"
G15A_TOLERANCE = 1e-12
TOTAL_TOLERANCE = 1e-9

#: code -> (label, numerator, exposure, per-game numerator, per-game exposure, scale, family).
#: Aggregate, pair and cohort columns carry ``_src``/``_dest``; per-game columns are corpus names.
COMPONENTS = {
    "pts": ("points", "pts", "minutes", "points", "minutes", 36.0, "primary"),
    "oreb": (
        "offensive rebounds",
        "oreb",
        "minutes",
        "offensive_rebounds",
        "minutes",
        36.0,
        "primary",
    ),
    "dreb": (
        "defensive rebounds",
        "dreb",
        "minutes",
        "defensive_rebounds",
        "minutes",
        36.0,
        "primary",
    ),
    "ast": ("assists", "ast", "minutes", "assists", "minutes", 36.0, "primary"),
    "stl": ("steals", "stl", "minutes", "steals", "minutes", 36.0, "primary"),
    "blk": ("blocks", "blk", "minutes", "blocks", "minutes", 36.0, "primary"),
    "tov": ("turnovers", "tov", "minutes", "turnovers", "minutes", 36.0, "primary"),
    "fg3a": (
        "3-point attempts",
        "fg3a",
        "minutes",
        "fg3_attempted",
        "minutes",
        36.0,
        "primary",
    ),
    "fta": (
        "free-throw attempts",
        "fta",
        "minutes",
        "ft_attempted",
        "minutes",
        36.0,
        "primary",
    ),
    "fg3_pct": (
        "3-point percentage",
        "fg3m",
        "fg3a",
        "fg3_made",
        "fg3_attempted",
        1.0,
        "secondary",
    ),
    "ft_pct": (
        "free-throw percentage",
        "ftm",
        "fta",
        "ft_made",
        "ft_attempted",
        1.0,
        "secondary",
    ),
}
EFF = ("EFF", "pir", "minutes", "pir", "minutes", 36.0, "reference")
PRIMARY = tuple(c for c, s in COMPONENTS.items() if s[6] == "primary")
SECONDARY = tuple(c for c, s in COMPONENTS.items() if s[6] == "secondary")
E15A_SENTENCE = "the same player keeps more of his {c1} than his {c2} when he faces continental opponents"
E15B_SENTENCE = "{c} is the skill that travels"
E15B_RULE = (
    'E15b is descriptive. No single component is called "the" skill that travels unless its '
    "disattenuated correlation interval is above every other component's point estimate."
)


class GateFailure(common.GateFailure):
    """A registered E15 gate did not hold."""


# --------------------------------------------------------------- components --
def spec(code: str):
    return EFF if code == "pir" else COMPONENTS[code]


def side(frame: pd.DataFrame, code: str, suffix: str):
    """(numerator, exposure, rate) of one component on one side (``_src``/``_dest``)."""
    _, num, exp, _, _, scale, _ = spec(code)
    n = frame[f"{num}{suffix}"].to_numpy(dtype=float)
    e = frame[f"{exp}{suffix}"].to_numpy(dtype=float)
    rate = np.full(len(frame), np.nan)
    ok = e > 0
    rate[ok] = scale * n[ok] / e[ok]
    return n, e, rate


def eligible(frame: pd.DataFrame, code: str) -> np.ndarray:
    """Per-36 components use every row; percentages need >= 20 attempts on both sides."""
    _, _, exp, _, _, _, family = spec(code)
    if family != "secondary":
        return np.ones(len(frame), dtype=bool)
    return (frame[f"{exp}_src"].to_numpy(dtype=float) >= ATTEMPT_FLOOR) & (
        frame[f"{exp}_dest"].to_numpy(dtype=float) >= ATTEMPT_FLOOR
    )


def interval(draws) -> list:
    d = np.asarray(draws, float)
    d = d[np.isfinite(d)]
    if len(d) < 2:
        return [None, None]
    return [float(np.percentile(d, 2.5)), float(np.percentile(d, 97.5))]


# ------------------------------------------------------------------- E15a --
def retention_parts(pairs: pd.DataFrame, code: str) -> dict:
    """Per-pair pieces of the exposure-weighted ratio and of the ratio of sums.

    Weight = the thinner side's exposure (minutes for per-36 rates, attempts for
    percentages), as in build_league_factors._exposure_weighted. A pair whose
    domestic rate is zero cannot form a ratio; it is excluded and counted.
    """
    ns, es, x = side(pairs, code, "_src")
    nd, ed, y = side(pairs, code, "_dest")
    elig = eligible(pairs, code)
    w = np.minimum(es, ed)
    use = elig & (x > 0) & np.isfinite(y)
    ratio = np.zeros(len(pairs))
    ratio[use] = y[use] / x[use]
    z = elig.astype(float)
    return {
        "eligible": elig,
        "use": use,
        "zero_source": elig & ~(x > 0),
        # ew numerator, ew denominator, num_dest, exp_dest, num_src, exp_src
        "sums": np.column_stack(
            [
                np.where(use, w * ratio, 0.0),
                np.where(use, w, 0.0),
                z * nd,
                z * ed,
                z * ns,
                z * es,
            ]
        ),
    }


def ratios_from_totals(t: np.ndarray):
    """(exposure-weighted ratio, ratio of sums) from summed columns; last axis = 6."""
    t = np.asarray(t, float)
    with np.errstate(divide="ignore", invalid="ignore"):
        ew = np.where(t[..., 1] > 0, t[..., 0] / t[..., 1], np.nan)
        src = np.where(t[..., 5] > 0, t[..., 4] / t[..., 5], np.nan)
        dest = np.where(t[..., 3] > 0, t[..., 2] / t[..., 3], np.nan)
        ros = np.where(src > 0, dest / src, np.nan)
    return ew, ros


def player_counts(players: pd.Series, n_boot: int, seed: int):
    """Cluster codes and a (n_boot, G) matrix of how often each player is drawn."""
    codes, uniques = pd.factorize(players, sort=True)
    g = len(uniques)
    rng = np.random.default_rng(seed)
    counts = np.zeros((n_boot, g))
    for b in range(n_boot):
        counts[b] = np.bincount(rng.integers(0, g, g), minlength=g)
    return codes, counts


def e15a_subset(sub: pd.DataFrame, *, n_boot=N_BOOT, seed=SEED) -> list[dict]:
    """Every component on one subset of pairs, with one joint player-cluster bootstrap."""
    codes, counts = player_counts(sub.player_name, n_boot, seed)
    g = counts.shape[1]
    out = []
    for code in COMPONENTS:
        parts = retention_parts(sub, code)
        per_player = np.column_stack(
            [
                np.bincount(codes, weights=parts["sums"][:, j], minlength=g)
                for j in range(6)
            ]
        )
        point_ew, point_ros = ratios_from_totals(per_player.sum(axis=0))
        draw_ew, draw_ros = ratios_from_totals(counts @ per_player)
        ew_ci, ros_ci = interval(draw_ew), interval(draw_ros)
        out.append(
            {
                "component": code,
                "label": spec(code)[0],
                "family": spec(code)[6],
                "n_pairs": int(len(sub)),
                "n_players": int(g),
                "n_eligible": int(parts["eligible"].sum()),
                "n_used": int(parts["use"].sum()),
                "n_zero_source_excluded": int(parts["zero_source"].sum()),
                "retention": float(point_ew),
                "ci_low": ew_ci[0],
                "ci_high": ew_ci[1],
                "bootstrap_se": float(np.nanstd(draw_ew, ddof=1)),
                "n_boot_valid": int(np.isfinite(draw_ew).sum()),
                "ratio_of_sums": float(point_ros),
                "ratio_of_sums_ci_low": ros_ci[0],
                "ratio_of_sums_ci_high": ros_ci[1],
            }
        )
    return out


def e15a(pairs: pd.DataFrame, *, n_boot=N_BOOT, seed=SEED) -> pd.DataFrame:
    """Pooled, by destination, and by source league with >= 75 pairs."""
    subsets = [("pooled", "all", pairs)]
    subsets += [
        ("destination", d, g) for d, g in pairs.groupby("league_dest", sort=True)
    ]
    counts = pairs.league_src.value_counts()
    for league in sorted(counts.index):
        if counts[league] >= SOURCE_LEAGUE_FLOOR:
            subsets.append(
                ("source_league", league, pairs[pairs.league_src.eq(league)])
            )
    rows = []
    for kind, name, sub in subsets:
        for record in e15a_subset(sub.reset_index(drop=True), n_boot=n_boot, seed=seed):
            rows.append({"subset_type": kind, "subset": name, **record})
    return pd.DataFrame(rows)


def e15a_licences(table: pd.DataFrame) -> pd.DataFrame:
    """Every ordered pair of pooled components whose intervals do not overlap."""
    pooled = table[table.subset_type.eq("pooled")].set_index("component")
    out = []
    for c1, c2 in itertools.permutations(COMPONENTS, 2):
        low, high = pooled.loc[c1, "ci_low"], pooled.loc[c2, "ci_high"]
        if pd.isna(low) or pd.isna(high) or not low > high:
            continue
        out.append(
            {
                "higher": c1,
                "lower": c2,
                "families": f"{pooled.loc[c1, 'family']}/{pooled.loc[c2, 'family']}",
                "higher_ci_low": float(low),
                "lower_ci_high": float(high),
                "sentence": E15A_SENTENCE.format(
                    c1=pooled.loc[c1, "label"], c2=pooled.loc[c2, "label"]
                ),
            }
        )
    columns = [
        "higher",
        "lower",
        "families",
        "higher_ci_low",
        "lower_ci_high",
        "sentence",
    ]
    return pd.DataFrame(out, columns=columns)


# ----------------------------------------------------------- G15a (estimator) --
def g15a_differences(pairs: pd.DataFrame) -> dict:
    """This module's estimator on EFF against fit_table's factor_raw, per cell."""
    table = fit_table(pairs, estimator="exposure_weighted", n_boot=2, seed=SEED)
    diffs = {}
    for _, cell in table.iterrows():
        sub = pairs[
            pairs.league_dest.eq(cell.destination) & pairs.league_src.eq(cell.league)
        ]
        parts = retention_parts(sub, "pir")
        mine, _ = ratios_from_totals(parts["sums"].sum(axis=0))
        diffs[f"{cell.destination}:{cell.league}"] = abs(
            float(mine) - float(cell.factor_raw)
        )
    return diffs


def assert_g15a(diffs: dict, tolerance: float = G15A_TOLERANCE) -> None:
    worst = max(diffs, key=diffs.get)
    if len(diffs) != 20 or not diffs[worst] <= tolerance:
        raise GateFailure(
            f"G15a failed: {len(diffs)} cells, {worst} differs by {diffs[worst]:.3e} (tolerance {tolerance:.0e})"
        )


# ----------------------------------------------------------------- history --
def component_history(agg: pd.DataFrame, code: str) -> pd.DataFrame:
    """v10's prior_mean_pir36 rule for any component: pooled rate over earlier seasons."""
    _, num, exp, _, _, scale, _ = spec(code)
    frame = pd.DataFrame(
        {
            "player_name": agg.player_name,
            "season": agg.season,
            "num": agg[num].astype(float),
            "exp": agg[exp].astype(float),
        }
    ).loc[agg.minutes.gt(0)]
    hist = (
        frame.groupby(["player_name", "season"])[["num", "exp"]]
        .sum()
        .sort_index()
        .reset_index()
    )
    hist[["cum_num", "cum_exp"]] = hist.groupby("player_name")[["num", "exp"]].cumsum()
    earlier = hist.cum_exp - hist.exp
    prior = np.full(len(hist), np.nan)
    ok = (earlier > 0).to_numpy()
    prior[ok] = (
        scale * (hist.cum_num - hist.num).to_numpy()[ok] / earlier.to_numpy()[ok]
    )
    hist["prior"] = prior
    return hist[["player_name", "season", "prior"]]


# ------------------------------------------------------------- box scores --
def assert_totals(
    target_rows: pd.DataFrame, targets: pd.DataFrame, tolerance=TOTAL_TOLERANCE
) -> dict:
    """Per-game rows must add up to the cohort's destination totals for every component."""
    columns = sorted({c for s in COMPONENTS.values() for c in (s[3], s[4])})
    got = target_rows.groupby(["player_name", "season"])[columns].sum()
    got.index = got.index.set_names(KEY)
    want = targets.set_index(KEY)
    worst = {}
    for code, (_, num, exp, gnum, gexp, _, _) in COMPONENTS.items():
        for a, b in ((num, gnum), (exp, gexp)):
            d = (
                want[f"{a}_dest"].astype(float)
                - got[b].reindex(want.index).astype(float)
            ).abs()
            worst[f"{code}:{a}"] = float(d.max()) if d.notna().all() else float("inf")
    name = max(worst, key=worst.get)
    if not worst[name] <= tolerance:
        raise GateFailure(
            f"per-game totals differ from the cohort: {name} by {worst[name]}"
        )
    return worst


def split_halves(target_rows: pd.DataFrame, targets: pd.DataFrame) -> pd.DataFrame:
    """Odd/even destination appearances in date order (E6), per component."""
    records = []
    for (name, season), group in target_rows.groupby(
        ["player_name", "season"], sort=True
    ):
        g = group.reset_index(drop=True)
        parts = {"odd": g.iloc[0::2], "even": g.iloc[1::2], "full": g}
        record = {"player_name": name, "season_dest": int(season), "games": len(g)}
        for code in (*COMPONENTS, "pir"):
            _, _, _, gnum, gexp, scale, _ = spec(code)
            for label, part in parts.items():
                e = float(part[gexp].sum())
                record[f"{code}_{label}"] = (
                    scale * float(part[gnum].sum()) / e if e > 0 else np.nan
                )
        records.append(record)
    return targets[KEY].merge(pd.DataFrame(records), on=KEY, how="left", validate="1:1")


def e6_differences(halves: pd.DataFrame, e6_table: pd.DataFrame) -> dict:
    """EFF halves from this module against E6's split_half_table, per target."""
    merged = halves.merge(e6_table, on=KEY, how="left", validate="1:1")
    return {
        part: float(np.max(np.abs(merged[f"pir_{part}"] - merged[f"O1_{part}"])))
        for part in ("odd", "even", "full")
    }


def assert_e6(diffs: dict, tolerance: float = G15A_TOLERANCE) -> None:
    worst = max(diffs, key=diffs.get)
    if not diffs[worst] <= tolerance:
        raise GateFailure(
            f"E6 split halves not reproduced: {worst} by {diffs[worst]:.3e}"
        )


# ------------------------------------------------------------------- E15b --
def reliability(odd: np.ndarray, even: np.ndarray):
    """Split-half r and its Spearman-Brown reliability over targets with both halves."""
    ok = np.isfinite(odd) & np.isfinite(even)
    if ok.sum() < 3:
        return np.nan, np.nan, int(ok.sum())
    r = float(np.corrcoef(odd[ok], even[ok])[0, 1])
    return r, 2 * r / (1 + r), int(ok.sum())


def model_frame(targets: pd.DataFrame, prior: np.ndarray, code: str) -> pd.DataFrame:
    """The v10 model columns with the component's rates and history in EFF's place."""
    _, _, x = side(targets, code, "_src")
    _, _, y = side(targets, code, "_dest")
    frame = targets[[*KEY, "league_dest", "league_src", "cluster"]].copy()
    frame["pir_per36_src"], frame["pir_per36_dest"] = x, y
    frame["prior_mean_pir36"] = prior
    frame["above_own_prior"] = x > prior  # NaN history -> False, as in E3
    return frame


SCALARS = (
    "r",
    "reliability",
    "ceiling",
    "r_disattenuated",
    "slope_unadjusted",
    "slope_source_rate_eurocup",
    "slope_source_rate_euroleague",
    "offset_spread_sd_units",
)


def carryover(frame: pd.DataFrame, odd: np.ndarray, even: np.ndarray, leagues) -> dict:
    """Correlation, reliability, disattenuated correlation, slopes and offsets on one sample."""
    x, y = frame.pir_per36_src.to_numpy(float), frame.pir_per36_dest.to_numpy(float)
    r = float(np.corrcoef(x, y)[0, 1])
    r_half, rel, n_rel = reliability(odd, even)
    positive = bool(np.isfinite(rel) and rel > 0)
    sd_y = float(np.std(y, ddof=1))
    _, info = benchmark.fit_model(frame, frame.iloc[:1], OFFSET_ARM)
    if info["status"] != "ok":
        raise GateFailure(f"lambda-10 fit failed: {info['status']}")
    coef = dict(zip(info["features"], info["coefficients"]))
    offsets = {c: float(coef.get(f"source_offset:{c}", np.nan)) for c in leagues}
    present = np.array([v for v in offsets.values() if np.isfinite(v)])
    return {
        "n": int(len(frame)),
        "r": r,
        "split_half_r": r_half,
        "reliability": rel,
        "n_reliability": n_rel,
        "ceiling": float(np.sqrt(rel)) if positive else np.nan,
        "r_disattenuated": float(r / np.sqrt(rel)) if positive else np.nan,
        "slope_unadjusted": float(np.cov(x, y, ddof=1)[0, 1] / np.var(x, ddof=1)),
        "slope_source_rate_eurocup": float(coef["source_rate"]),
        "slope_source_rate_euroleague": float(
            coef["source_rate"] + coef["destination_x_source"]
        ),
        "component_sd": sd_y,
        "offset_spread_sd_units": float(np.std(present, ddof=1) / sd_y),
        "offsets_sd_units": {c: v / sd_y for c, v in offsets.items()},
    }


def cluster_index(frame: pd.DataFrame) -> list:
    """Row positions of each destination club-season, in sorted cluster order."""
    codes = pd.factorize(frame.cluster, sort=True)[0]
    return [np.flatnonzero(codes == c) for c in range(codes.max() + 1)]


def e15b(
    targets: pd.DataFrame,
    halves: pd.DataFrame,
    priors: dict,
    *,
    n_boot=N_BOOT,
    seed=SEED,
):
    """Point estimates and one joint destination club-season bootstrap for all components."""
    leagues = sorted(targets.league_src.unique())
    frames, points, keeps = {}, {}, {}
    for code in COMPONENTS:
        keep = eligible(targets, code)
        keeps[code] = keep
        frames[code] = (
            model_frame(targets, priors[code], code)[keep].reset_index(drop=True),
            halves[f"{code}_odd"].to_numpy(float)[keep],
            halves[f"{code}_even"].to_numpy(float)[keep],
        )
        points[code] = carryover(*frames[code], leagues)
    groups = cluster_index(targets)
    rng = np.random.default_rng(seed)
    draws = {c: {k: np.full(n_boot, np.nan) for k in SCALARS} for c in COMPONENTS}
    offset_draws = {c: np.full((n_boot, len(leagues)), np.nan) for c in COMPONENTS}
    for b in range(n_boot):
        picks = rng.integers(0, len(groups), len(groups))
        idx = np.concatenate([groups[i] for i in picks])
        for code in COMPONENTS:
            keep = keeps[code]
            # positions of the drawn rows inside the eligible sub-frame
            pos = (np.cumsum(keep) - 1)[idx[keep[idx]]]
            frame, odd, even = frames[code]
            res = carryover(
                frame.iloc[pos].reset_index(drop=True), odd[pos], even[pos], leagues
            )
            for k in SCALARS:
                draws[code][k][b] = res[k]
            offset_draws[code][b] = [res["offsets_sd_units"][c] for c in leagues]
    table, offsets = [], []
    for code in COMPONENTS:
        p = points[code]
        row = {
            "component": code,
            "label": spec(code)[0],
            "family": spec(code)[6],
            "n": p["n"],
            "n_reliability": p["n_reliability"],
            "split_half_r": p["split_half_r"],
            "component_sd": p["component_sd"],
        }
        for k in SCALARS:
            lo, hi = interval(draws[code][k])
            row[k], row[f"{k}_ci_low"], row[f"{k}_ci_high"] = p[k], lo, hi
            row[f"{k}_n_boot_valid"] = int(np.isfinite(draws[code][k]).sum())
        table.append(row)
        for j, league in enumerate(leagues):
            lo, hi = interval(offset_draws[code][:, j])
            offsets.append(
                {
                    "component": code,
                    "league_src": league,
                    "n_targets": int(frames[code][0].league_src.eq(league).sum()),
                    "offset_sd_units": p["offsets_sd_units"][league],
                    "ci_low": lo,
                    "ci_high": hi,
                    "draws_league_absent": int(
                        np.isnan(offset_draws[code][:, j]).sum()
                    ),
                }
            )
    boot = {"club_seasons": len(groups), "n_boot": n_boot, "seed": seed}
    return pd.DataFrame(table), pd.DataFrame(offsets), boot


def e15b_licences(table: pd.DataFrame) -> list[dict]:
    """A component is 'the' skill only if its interval clears every other point estimate."""
    out = []
    for _, row in table.iterrows():
        others = table.loc[table.component.ne(row.component), "r_disattenuated"]
        best_other = float(np.nanmax(others.to_numpy(float)))
        low = row.r_disattenuated_ci_low
        earned = bool(pd.notna(low) and low > best_other)
        out.append(
            {
                "component": row.component,
                "ci_low": None if pd.isna(low) else float(low),
                "highest_other_point": best_other,
                "earned": earned,
                "sentence": E15B_SENTENCE.format(c=row.label) if earned else None,
            }
        )
    return out


# ------------------------------------------------------------- figure CSV --
def figure_table(a: pd.DataFrame, b: pd.DataFrame) -> pd.DataFrame:
    """One row per component: everything a 'which skills travel' chart needs."""
    pooled = a[a.subset_type.eq("pooled")].set_index("component")
    dest = a[a.subset_type.eq("destination")].set_index(["component", "subset"])
    b = b.set_index("component")
    rows = []
    for code in COMPONENTS:
        rows.append(
            {
                "component": code,
                "label": spec(code)[0],
                "family": spec(code)[6],
                "retention": pooled.loc[code, "retention"],
                "retention_ci_low": pooled.loc[code, "ci_low"],
                "retention_ci_high": pooled.loc[code, "ci_high"],
                "retention_n_used": pooled.loc[code, "n_used"],
                "retention_euroleague": dest.loc[(code, "euroleague"), "retention"],
                "retention_eurocup": dest.loc[(code, "eurocup"), "retention"],
                "carryover_n": b.loc[code, "n"],
                "carryover_r": b.loc[code, "r"],
                "carryover_r_disattenuated": b.loc[code, "r_disattenuated"],
                "carryover_r_disattenuated_ci_low": b.loc[
                    code, "r_disattenuated_ci_low"
                ],
                "carryover_r_disattenuated_ci_high": b.loc[
                    code, "r_disattenuated_ci_high"
                ],
                "destination_reliability": b.loc[code, "reliability"],
                "reliability_ceiling": b.loc[code, "ceiling"],
                "slope_source_rate_eurocup": b.loc[code, "slope_source_rate_eurocup"],
                "slope_source_rate_euroleague": b.loc[
                    code, "slope_source_rate_euroleague"
                ],
                "offset_spread_sd_units": b.loc[code, "offset_spread_sd_units"],
                "offset_spread_ci_low": b.loc[code, "offset_spread_sd_units_ci_low"],
                "offset_spread_ci_high": b.loc[code, "offset_spread_sd_units_ci_high"],
            }
        )
    return pd.DataFrame(rows)


# -------------------------------------------------------------------- run --
def negative_control(check, *args, **kwargs) -> str:
    """A gate that cannot fail checks nothing (METHOD.md §8)."""
    try:
        check(*args, **kwargs)
    except common.GateFailure:
        return "rejected as required"
    raise GateFailure(f"{check.__name__} negative control passed")


def run(input_dir: Path, raw_root: Path, out: Path, *, n_boot=N_BOOT) -> dict:
    _, v10_summary = common.load_references(ROOT)
    pairs, cohort = common.load_pool(input_dir, "official_corrected")
    keys = common.target_keys(v10_summary)
    if len(pairs) != N_PAIRS:
        raise GateFailure(f"pool-A pairs are {len(pairs)}, not {N_PAIRS}")
    summary: dict = {
        "analysis": "E15 which skills travel",
        "exploratory": True,
        "amendment": str(AMENDMENT.relative_to(ROOT)),
        "amendment_commit": AMENDMENT_COMMIT,
        "amendment_sha256": sha256_file(AMENDMENT),
        "inputs": {
            "pairs_sha256": common.PAIRS_SHA["official_corrected"],
            "cohort_sha256": common.COHORT_SHA,
        },
        "n_boot": n_boot,
        "seed": SEED,
        "components": {
            c: {"label": s[0], "family": s[6]} for c, s in COMPONENTS.items()
        },
        "attempt_floor": ATTEMPT_FLOOR,
        "source_league_floor": SOURCE_LEAGUE_FLOOR,
    }

    # ---- G15a: the estimator is the factor table's, on every EFF cell ----
    diffs = g15a_differences(pairs)
    summary["g15a"] = {
        "cells": len(diffs),
        "max_difference": max(diffs.values()),
        "tolerance": G15A_TOLERANCE,
        "negative_control": negative_control(assert_g15a, diffs, tolerance=-1.0),
    }
    assert_g15a(diffs)
    summary["g15a"]["status"] = "passed"

    # ---- corpus rebuild, G3 and per-component histories ----
    games, agg, rebuild = robust.rebuild_games(raw_root)
    summary["corpus_rebuild"] = rebuild
    g3 = robust.g3_difference(
        cohort, robust.attach_history(cohort, component_history(agg, "pir"))
    )
    summary["g3"] = {
        **g3,
        "tolerance": robust.G3_TOLERANCE,
        "negative_control": negative_control(robust.assert_g3, g3, tolerance=-1.0),
    }
    robust.assert_g3(g3)
    summary["g3"]["status"] = "passed"

    targets = keys.merge(cohort, on=KEY, how="left", validate="1:1")
    if len(targets) != N_TARGETS or targets.league_src.isna().any():
        raise GateFailure("the 674 targets do not join 1:1 to the cohort")
    priors = {
        code: robust.attach_history(targets, component_history(agg, code))
        for code in COMPONENTS
    }

    # ---- E6 reconciliation and per-component totals on per-game box scores ----
    dates = robust.load_game_dates(raw_root)
    target_rows = robust.target_games(games, targets, dates)
    recon = robust.reconcile(target_rows, targets)
    exceptions = recon.loc[recon.exception.ne(""), [*KEY, "exception"]]
    control = robust.reconcile(
        target_rows, targets.assign(games_dest=targets.games_dest + 1)
    )
    if not control.exception.ne("").all():
        raise GateFailure("reconciliation negative control did not flag every target")
    if not exceptions.empty:
        raise GateFailure(f"{len(exceptions)} targets do not reconcile")
    totals = assert_totals(target_rows, targets)
    summary["box_scores"] = {
        "targets": len(targets),
        "reconciled": int(recon.exception.eq("").sum()),
        "player_games": int(len(target_rows)),
        "max_total_difference": max(totals.values()),
        "tolerance": TOTAL_TOLERANCE,
        "reconciliation_negative_control": "every target flagged as required",
        "totals_negative_control": negative_control(
            assert_totals, target_rows, targets.assign(pts_dest=targets.pts_dest + 1)
        ),
        "status": "passed",
    }

    out.mkdir(parents=True, exist_ok=False)

    # ---- E15a ----
    a = e15a(pairs, n_boot=n_boot)
    a.to_csv(out / "e15a_retention.csv", index=False)
    licences_a = e15a_licences(a)
    licences_a.to_csv(out / "e15a_licences.csv", index=False)
    counts = pairs.league_src.value_counts()
    summary["e15a"] = {
        "pairs": int(len(pairs)),
        "players": int(pairs.player_name.nunique()),
        "pairs_by_destination": {
            k: int(v) for k, v in sorted(pairs.league_dest.value_counts().items())
        },
        "pairs_by_source_league": {k: int(v) for k, v in sorted(counts.items())},
        "source_leagues_below_floor": sorted(
            k for k, v in counts.items() if v < SOURCE_LEAGUE_FLOOR
        ),
        "licences": licences_a.to_dict("records"),
    }

    # ---- E15b ----
    halves = split_halves(target_rows, targets)
    e6 = e6_differences(halves, robust.split_half_table(target_rows, targets))
    summary["e6_reproduction"] = {
        "max_difference": max(e6.values()),
        "tolerance": G15A_TOLERANCE,
        "negative_control": negative_control(assert_e6, e6, tolerance=-1.0),
    }
    assert_e6(e6)
    summary["e6_reproduction"]["status"] = "passed"
    halves.to_csv(out / "e15b_split_halves.csv", index=False)
    b, offsets, boot = e15b(targets, halves, priors, n_boot=n_boot)
    b.to_csv(out / "e15b_carryover.csv", index=False)
    offsets.to_csv(out / "e15b_source_offsets.csv", index=False)
    summary["e15b"] = {
        "targets": len(targets),
        "bootstrap": boot,
        "history_missing": {c: int(np.isnan(p).sum()) for c, p in priors.items()},
        "licences": e15b_licences(b),
        "rule": E15B_RULE,
    }
    figure_table(a, b).to_csv(out / "skills_travel_figure.csv", index=False)
    (out / "summary.json").write_text(
        json.dumps(robust.clean(summary), indent=2, sort_keys=True, allow_nan=False)
        + "\n"
    )
    return summary


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument("--raw-root", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--n-boot", type=int, default=N_BOOT)
    args = parser.parse_args(argv)
    with contextlib.redirect_stdout(io.StringIO()):
        summary = run(args.input_dir, args.raw_root, args.out, n_boot=args.n_boot)
    print(
        json.dumps(
            {
                "g15a": summary["g15a"]["status"],
                "g3": summary["g3"]["status"],
                "box_scores": summary["box_scores"]["status"],
                "e6_reproduction": summary["e6_reproduction"]["status"],
                "e15a_licences": len(summary["e15a"]["licences"]),
                "e15b_the_skill": [
                    x["component"] for x in summary["e15b"]["licences"] if x["earned"]
                ],
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
