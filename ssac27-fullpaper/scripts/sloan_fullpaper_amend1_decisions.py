#!/usr/bin/env python3
"""Amendment 1 decision analyses: E10, E11, E12 and E17 (all EXPLORATORY).

Pre-registration: docs/research/sloan-full-paper-preregistration-2026-11-03.md
(commit f52e7c831) and its Amendment 1,
docs/research/sloan-full-paper-preregistration-amendment-1-2026-11-04.md
(commit f1a3453da, pushed alone 2026-11-04 before this file existed).
Destination seasons 2020-2025 were exposed, so every number here is
exploratory.

* E10 -- the E7 pairwise ordering metrics split into cross-league pairs
  (different source leagues) and same-league pairs, inside the 12 pools
  (destination competition x season). Primary: D1(offsets l10) - D1(history)
  on cross-league pairs. Uncertainty: the E7 cluster bootstrap (destination
  club-seasons within pool, 2,000 draws, seed 0), drawn in the same order as
  E7 so the all-pairs intervals reproduce E7 exactly.
* E11 -- mean signed error (forecast - actual EFF/36) by source league for
  history, history + translation and offsets l10 on the 674, with the same
  within-pool club-season bootstrap; Holm across the 10 leagues of the
  history-only bootstrap two-sided p-values.
* E12 -- the coefficient on a = 1[source season above own history] in the
  offsets l10 model: the e9 full fit through 2025 with the e9 cluster bootstrap
  (re-drawn identically, so the e9 grid intervals reproduce), the six
  walk-forward refits used to forecast 2020-2025, and the same for the
  history-only model.
* E17 -- completions of registered tables: E1 C_H and S at l = 1 and 100;
  minutes-weighted MAE for the four primary arms and the three headline
  contrasts; every Table 1 MAE as a share of reducible error (E6 floor);
  per-league counts; the 2% margin and every recipe's upper bound in EFF/36 and
  as a share of the history-vs-translation gain.
* Descriptive (not a registered estimand): the ACB-16 equivalent of each source
  league per destination, from the e9 coefficients and their bootstrap draws.

Threats and their controls (all in this file): drift from the submitted numbers
(G0 with its negative control); a changed target set (scope gate); forecasts
that differ from the E1/E7 runs whose outputs are reused (reproduction gate,
1e-9, on every arm); a pair split that loses or double-counts pairs (partition
gate: cross + same = all, per pool); arithmetic error in the pair counts (D1/D2
identity per pair type); a bootstrap that is not E7's (E7 interval
reproduction gate); an E12 coefficient that is not the one that produced the
forecasts (fold-coefficient gate re-predicting every anchor forecast, and the
e9 reproduction gate on coefficients and grid intervals); a weighted interval
that does not reduce to the registered one (equal-weight reduction gate); a
floor other than the registered 2.18 (floor gate); counts that do not add up
(count gates). Every gate has a negative control that must reject (METHOD.md
section 8). No 2026-27 data is read.
"""

# ruff: noqa: E501, E741 -- gate messages and licensed sentences; O is the offsets arm
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
from scipy import stats  # noqa: E402

from scripts import sloan_context_benchmarks as benchmark  # noqa: E402
from scripts import sloan_fullpaper_common as common  # noqa: E402
from scripts import sloan_fullpaper_decisions as dec  # noqa: E402
from scripts import sloan_fullpaper_recipes as recipes  # noqa: E402
from scripts.translation_research_common import sha256_file  # noqa: E402

KEY = common.KEY
OUTCOME = dec.OUTCOME
N_BOOT = 2000
SEED = 0
AMENDMENT = Path(
    "docs/research/sloan-full-paper-preregistration-amendment-1-2026-11-04.md"
)
AMENDMENT_COMMIT = "f1a3453dae4ed77b069ad8c12f963eb3e32d27ee"

H, HT, O, OT = dec.HISTORY, dec.HISTORY_T, dec.OFFSETS, dec.OFFSETS_T
MODELS = dec.MODELS
LABELS = dec.LABELS
PAIR_TYPES = ("cross", "same")
#: E10 D1 contrasts (first, second); a positive difference favours the second.
E10_PRIMARY = (H, O)
E10_D1 = ((H, O), (H, HT), (HT, O), (O, OT))
#: E10 D2: offsets l10 vs + translation (registered); history vs + translation (reference).
E10_D2 = ((O, OT), (H, HT))

E11_ARMS = (H, HT, O)
EXPECTED_LEAGUES = 10
HOLM_ALPHA = 0.05

E12_FLAG = "above_prior"
E12_ARMS = (O, H)

HEADLINE_CONTRASTS = ((H, HT), (HT, O), (O, OT))
TABLE1_ARMS = (
    "history_only",
    "scheduled_history",
    "history_destination_slope",
    "history_destination_slope_scheduled",
    "source_ridge_1",
    "source_ridge_1_scheduled",
    "source_ridge_10",
    "source_ridge_10_scheduled",
    "source_ridge_100",
    "source_ridge_100_scheduled",
    "cell_slope_10",
    "cell_slope_10_scheduled",
)
REGISTERED_FLOOR = 2.18  # E6 floor named in Amendment 1, section E17.3
FLOOR_TOLERANCE = 0.005  # the registered value is printed to two decimals
RECIPES = ("R1", "R2", "R3", "R4", "R5", "R6")
EXPECTED_PAIRS = 4074
EXPECTED_TRAINING = 1059

REFERENCE_LEAGUE = "spain-acb"
REFERENCE_RATE = 16.0

#: Outputs of earlier retained runs reused as inputs, pinned to their receipts.
PRIOR_FILES = {
    "decide-02/e7_keyed_forecasts.csv": "83589795f00df04cdb272155697f6f9d55c8f7604e49ae3bc45e0e1aac04b8f6",
    "decide-02/summary.json": "ce1d9bafd1364c548c29a9a8e774bf3d32dc3ac39a431dc0742377f9eff56666",
    "decide-02/e9_league_tiers_full.csv": "9c233bad8bde45e67e53fd06f94feb4d899b3ee59e720bfd181b94091e8f3ef1",
    "recipes-01/rows_pool_A.parquet": "ce4f91e0ef854b684522efcf7d736b7c48a074277ac83a1fad016be7f7006eb3",
    "recipes-01/summary.json": "e4d826741bd4f629c713216cd592e19ae7d2d2a89b77fad2cbe7ed350c51d030",
    "robustness-02/summary.json": "ec2e2c10f44b801a1af099600841a73058872f9430b3aecfaf507a7fc32c91db",
}
REPRO_TOLERANCE = 1e-9
EXACT_TOLERANCE = 1e-12


class GateFailure(common.GateFailure):
    pass


def negative_control(check, *args, **kwargs) -> str:
    """A gate that cannot fail checks nothing (METHOD.md section 8)."""
    try:
        check(*args, **kwargs)
    except common.GateFailure:
        return "rejected as required"
    raise GateFailure(f"negative control passed for {check.__name__}")


interval = dec.interval
power_line = dec.power_line


def tag(first: str, second: str) -> str:
    return f"{first}__{second}"


def load_prior(prior_dir: Path) -> dict:
    """The reused retained-run outputs, each checked against its receipt sha256."""
    out = {}
    for name, expected in PRIOR_FILES.items():
        path = Path(prior_dir) / name
        common.check_sha(path, expected)
        if name.endswith(".json"):
            out[name] = json.loads(path.read_text())
        elif name.endswith(".parquet"):
            out[name] = pd.read_parquet(path)
        else:
            out[name] = pd.read_csv(path)
    return out


# ------------------------------------------------------------------ gates --
def max_abs(a, b) -> float:
    a, b = np.asarray(a, float), np.asarray(b, float)
    if a.shape != b.shape:
        return math.inf
    if not (np.isfinite(a) == np.isfinite(b)).all():
        return math.inf
    both = np.isfinite(a)
    return float(np.max(np.abs(a[both] - b[both]), initial=0.0))


def assert_close(name: str, worst: float, tolerance: float) -> float:
    if not worst <= tolerance:
        raise GateFailure(f"{name}: off by {worst:.3e} (tolerance {tolerance:.0e})")
    return float(worst)


def gate_max(name: str, worst: dict, tolerance: float) -> float:
    key = max(worst, key=worst.get)
    return assert_close(f"{name} ({key})", worst[key], tolerance)


def reproduction_difference(
    rows: pd.DataFrame, keyed: pd.DataFrame, r1: pd.DataFrame
) -> dict:
    """Rebuilt anchor forecasts vs the E7 keyed file and the E1 R1 rows."""
    cols = [*MODELS, OUTCOME]
    a = rows[KEY + cols].merge(
        keyed[KEY + cols], on=KEY, how="outer", suffixes=("", "_e7"), validate="1:1"
    )
    arms = [*common.ALL_ARMS, OUTCOME]
    b = rows[KEY + arms].merge(
        r1[KEY + arms], on=KEY, how="outer", suffixes=("", "_r1"), validate="1:1"
    )
    worst = {f"e7:{c}": max_abs(a[c], a[f"{c}_e7"]) for c in cols}
    worst.update({f"r1:{c}": max_abs(b[c], b[f"{c}_r1"]) for c in arms})
    return worst


def assert_leagues(rows: pd.DataFrame, expected: int = EXPECTED_LEAGUES) -> list:
    leagues = sorted(rows.league_src.unique())
    if len(leagues) != expected or rows.league_src.isna().any():
        raise GateFailure(
            f"league gate: {len(leagues)} source leagues (expected {expected})"
        )
    return leagues


# ----------------------------------------------------------- E10 counting --
def typed_pair_counts(y, preds, origin, src, odd, even) -> dict:
    """E7's within-pool pair counts, split by whether the two source leagues differ.

    Pairs of two copies of one forecast (bootstrap duplicates) are excluded, as
    in E7. Keys are f"{type}|{count}" for type in all / cross / same.
    """
    i, j = np.triu_indices(len(y), 1)
    keep = origin[i] != origin[j]
    i, j = i[keep], j[keep]
    cross = src[i] != src[j]
    dy = np.sign(y[i] - y[j])
    unequal = dy != 0
    signs = {arm: np.sign(p[i] - p[j]) for arm, p in preds.items()}
    a, b = np.sign(odd[i] - odd[j]), np.sign(even[i] - even[j])
    usable = (a != 0) & (b != 0)
    out = {}
    for kind, mask in (
        ("all", np.ones(len(i), bool)),
        ("cross", cross),
        ("same", ~cross),
    ):
        u = unequal & mask
        out[f"{kind}|pairs"] = int(mask.sum())
        out[f"{kind}|unequal"] = int(u.sum())
        for arm, dp in signs.items():
            out[f"{kind}|correct:{arm}"] = float(
                np.sum((dp == dy) & u) + 0.5 * np.sum((dp == 0) & u)
            )
            out[f"{kind}|ties:{arm}"] = int(np.sum((dp == 0) & mask))
        for first, second in E10_D2:
            t = tag(first, second)
            flip = (signs[first] * signs[second] < 0) & mask
            out[f"{kind}|flips:{t}"] = int(flip.sum())
            out[f"{kind}|flips_unequal:{t}"] = int((flip & unequal).sum())
            out[f"{kind}|right:{t}"] = int(
                (flip & unequal & (signs[second] == dy)).sum()
            )
        out[f"{kind}|half_pairs"] = int((usable & mask).sum())
        out[f"{kind}|half_agree"] = int(((a == b) & usable & mask).sum())
    return out


def true_rate_concordance(half_concordance: float) -> float:
    """E6/E7 normal model: half-vs-half concordance -> true-rate vs full season.

    r = sin(pi (c - 1/2)); Spearman-Brown R = 2r / (1 + r); ceiling
    1/2 + asin(sqrt(R)) / pi (the E7 'true rate vs full season' reading).
    NaN when the half concordance is not above 1/2.
    """
    if not np.isfinite(half_concordance):
        return math.nan
    r = math.sin(math.pi * (half_concordance - 0.5))
    if r <= 0:
        return math.nan
    full = 2 * r / (1 + r)
    return 0.5 + math.asin(math.sqrt(full)) / math.pi


def typed_ratios(c: dict, kind: str) -> dict:
    """Pooled shares for one pair type from summed counts."""

    def g(name):
        return c[f"{kind}|{name}"]

    unequal = g("unequal")
    r = {
        f"d1:{arm}": g(f"correct:{arm}") / unequal if unequal else math.nan
        for arm in MODELS
    }
    for first, second in E10_D1:
        r[f"d1diff:{tag(first, second)}"] = r[f"d1:{second}"] - r[f"d1:{first}"]
    for first, second in E10_D2:
        t = tag(first, second)
        r[f"flip_share:{t}"] = g(f"flips:{t}") / g("pairs") if g("pairs") else math.nan
        r[f"right_share:{t}"] = (
            g(f"right:{t}") / g(f"flips_unequal:{t}")
            if g(f"flips_unequal:{t}")
            else math.nan
        )
    half = g("half_agree") / g("half_pairs") if g("half_pairs") else math.nan
    r["ceiling_split_half"] = half
    r["ceiling_true_rate_normal_model"] = true_rate_concordance(half)
    return r


def assert_partition(pool_counts: pd.DataFrame, tolerance: float = 0.0) -> float:
    """cross + same = all, for every count in every pool."""
    worst = 0.0
    names = [c.split("|", 1)[1] for c in pool_counts.columns if c.startswith("all|")]
    for name in names:
        total = pool_counts[f"all|{name}"].to_numpy(float)
        parts = pool_counts[f"cross|{name}"].to_numpy(float)
        parts = parts + pool_counts[f"same|{name}"].to_numpy(float)
        worst = max(worst, float(np.max(np.abs(total - parts))))
    return assert_close("pair partition gate", worst, tolerance)


def assert_typed_identity(
    pool_counts: pd.DataFrame, tolerance: float = EXACT_TOLERANCE
) -> float:
    """Per pool and pair type: D1(b) - D1(a) = (2 right - flips) / unequal."""
    worst = 0.0
    for kind in ("all", *PAIR_TYPES):
        for first, second in E10_D2:
            t = tag(first, second)
            for _, row in pool_counts.iterrows():
                if row[f"{kind}|ties:{first}"] or row[f"{kind}|ties:{second}"]:
                    raise GateFailure(
                        "tied forecasts inside a pool; identity not applicable"
                    )
                n = row[f"{kind}|unequal"]
                if not n:
                    continue
                d1 = (
                    row[f"{kind}|correct:{second}"] - row[f"{kind}|correct:{first}"]
                ) / n
                d2 = (
                    2 * row[f"{kind}|right:{t}"] - row[f"{kind}|flips_unequal:{t}"]
                ) / n
                worst = max(worst, abs(d1 - d2))
    return assert_close("typed D1/D2 identity", worst, tolerance)


def e10_data(rows: pd.DataFrame, halves: pd.DataFrame) -> list:
    """The 12 pools in E7's order, with E7's cluster index."""
    merged = rows.merge(
        halves[KEY + ["odd_rate", "even_rate"]], on=KEY, how="left", validate="1:1"
    )
    if merged[["odd_rate", "even_rate"]].isna().any().any():
        raise GateFailure("a target lacks an odd or an even half")
    data = []
    for (league, season), frame in dec.pools(merged):
        data.append(
            {
                "name": f"{league}|{season}",
                "league": league,
                "season": season,
                "y": frame[OUTCOME].to_numpy(float),
                "p": {arm: frame[arm].to_numpy(float) for arm in MODELS},
                "src": frame.league_src.to_numpy(object),
                "odd": frame.odd_rate.to_numpy(float),
                "even": frame.even_rate.to_numpy(float),
                "groups": dec.cluster_index(frame),
                "n": len(frame),
            }
        )
    return data


def e10(rows: pd.DataFrame, halves: pd.DataFrame, *, n_boot=N_BOOT, seed=SEED):
    data = e10_data(rows, halves)

    def evaluate(index_sets):
        return pd.DataFrame(
            [
                typed_pair_counts(
                    d["y"][idx],
                    {a: p[idx] for a, p in d["p"].items()},
                    idx,
                    d["src"][idx],
                    d["odd"][idx],
                    d["even"][idx],
                )
                for d, idx in zip(data, index_sets)
            ]
        )

    point = evaluate([np.arange(d["n"]) for d in data])
    point.index = [d["name"] for d in data]
    cols = list(point.columns)
    # Same generator and call order as E7: one draw resamples every pool in turn.
    rng = np.random.default_rng(seed)
    draws = np.empty((n_boot, len(data), len(cols)))
    for b in range(n_boot):
        sample = evaluate([dec.cluster_draw(d["groups"], rng) for d in data])
        draws[b] = sample[cols].to_numpy(float)

    def summarise(sel) -> dict:
        totals = point.loc[sel].sum().to_dict()
        boot = [dict(zip(cols, draws[b][sel].sum(axis=0))) for b in range(n_boot)]
        out = {}
        for kind in ("all", *PAIR_TYPES):
            values = typed_ratios(totals, kind)
            bt = pd.DataFrame([typed_ratios(x, kind) for x in boot])
            block = {
                "pairs": int(totals[f"{kind}|pairs"]),
                "unequal_pairs": int(totals[f"{kind}|unequal"]),
                "values": {},
            }
            for name, value in values.items():
                entry = {"point": float(value), "ci95": interval(bt[name])}
                if name.startswith(("d1diff:", "right_share:")):
                    entry.update(power_line(bt[name]))
                block["values"][name] = entry
            for first, second in E10_D2:
                t = tag(first, second)
                for what in ("flips", "flips_unequal", "right"):
                    block["values"][f"{what}:{t}"] = int(totals[f"{kind}|{what}:{t}"])
            out[kind] = block
        return out

    league = np.array([d["league"] for d in data])
    pooled = {
        "all_pools": summarise(np.ones(len(data), bool)),
        "euroleague": summarise(league == "euroleague"),
        "eurocup": summarise(league == "eurocup"),
    }
    per_pool = []
    for p, d in enumerate(data):
        row = {"destination": d["league"], "season": d["season"], "forecasts": d["n"]}
        counts = point.iloc[p].to_dict()
        for kind in ("all", *PAIR_TYPES):
            row[f"{kind}_pairs"] = int(counts[f"{kind}|pairs"])
            row[f"{kind}_unequal_pairs"] = int(counts[f"{kind}|unequal"])
            r = typed_ratios(counts, kind)
            for arm in MODELS:
                row[f"{kind}_d1_{arm}"] = r[f"d1:{arm}"]
        per_pool.append(row)
    return {"pooled": pooled, "per_pool": pd.DataFrame(per_pool), "pool_counts": point}


def e7_reproduction(e10_pooled: dict, e7_summary: dict) -> dict:
    """All-pairs points and intervals against the E7 run (same draws)."""
    mine = e10_pooled["all_pools"]["all"]["values"]
    theirs = e7_summary["e7"]["pooled"]["all"]["values"]
    names = [f"d1:{arm}" for arm in MODELS] + [
        f"{what}:{tag(*pair)}"
        for pair in E10_D2
        for what in ("flip_share", "right_share")
    ]
    worst = {}
    for name in [*names, "ceiling_split_half"]:
        worst[f"{name}:point"] = abs(mine[name]["point"] - theirs[name]["point"])
        worst[f"{name}:ci95"] = max_abs(mine[name]["ci95"], theirs[name]["ci95"])
    return worst


def e10_licence(pooled: dict) -> dict:
    cross = pooled["all_pools"]["cross"]["values"]
    diff = cross[f"d1diff:{tag(*E10_PRIMARY)}"]
    lo, hi = diff["ci95"]
    x, y = cross[f"d1:{O}"]["point"], cross[f"d1:{H}"]["point"]
    if lo > 0:
        verdict = "above_zero"
        sentence = (
            f"Between candidates from different leagues, the league-aware forecast orders {100 * x:.1f}% "
            f"of pairs correctly against {100 * y:.1f}% for history alone."
        )
    elif hi >= 0:
        verdict = "spans_zero"
        sentence = "League adjustment does not detectably improve cross-league ordering at this n."
    else:
        verdict = "below_zero"
        sentence = (
            "No registered sentence: the cross-league interval lies below zero (league-aware "
            "ordering worse than history alone); reported as is."
        )
    return {"verdict": verdict, "sentence": sentence}


def e10_table(pooled: dict) -> pd.DataFrame:
    """Figure-ready: one row per scope x pair type x quantity."""
    out = []
    for scope, block in pooled.items():
        for kind in ("all", *PAIR_TYPES):
            b = block[kind]
            for name, v in b["values"].items():
                if not isinstance(v, dict):
                    continue
                quantity, _, which = name.partition(":")
                out.append(
                    {
                        "scope": scope,
                        "pair_type": kind,
                        "quantity": quantity,
                        "models": which,
                        "label": " vs ".join(
                            LABELS.get(m, m) for m in which.split("__") if m
                        ),
                        "pairs": b["pairs"],
                        "unequal_pairs": b["unequal_pairs"],
                        "point": v["point"],
                        "ci95_low": v["ci95"][0],
                        "ci95_high": v["ci95"][1],
                        "mde_80": v.get("mde_80", math.nan),
                    }
                )
    return pd.DataFrame(out)


# -------------------------------------------------------------------- E11 --
def bootstrap_p(draws) -> float:
    """Two-sided bootstrap p for 'mean = 0': twice the smaller tail share, with
    the (k + 1) / (B + 1) Monte-Carlo correction so p is never exactly zero."""
    d = np.asarray(draws, float)
    d = d[np.isfinite(d)]
    k = min(int(np.sum(d <= 0)), int(np.sum(d >= 0)))
    return float(min(1.0, 2 * (k + 1) / (len(d) + 1)))


def e11(rows: pd.DataFrame, leagues: list, *, n_boot=N_BOOT, seed=SEED) -> dict:
    """Mean signed error per source league; within-pool club-season bootstrap."""
    frame = rows.sort_values(dec.POOL_KEY + KEY).reset_index(drop=True)
    signed = {arm: (frame[arm] - frame[OUTCOME]).to_numpy(float) for arm in E11_ARMS}
    codes = pd.Categorical(frame.league_src, categories=leagues).codes
    if (codes < 0).any():
        raise GateFailure("a target's source league is outside the league list")
    pool_of = frame.groupby(dec.POOL_KEY, sort=True).ngroup().to_numpy()
    pool_groups = []
    for g in range(pool_of.max() + 1):
        pos = np.flatnonzero(pool_of == g)
        groups = dec.cluster_index(frame.iloc[pos].reset_index(drop=True))
        pool_groups.append((pos, groups))
    m = len(leagues)

    def league_means(idx):
        n = np.bincount(codes[idx], minlength=m).astype(float)
        with np.errstate(invalid="ignore", divide="ignore"):
            means = {
                arm: np.bincount(codes[idx], weights=s[idx], minlength=m) / n
                for arm, s in signed.items()
            }
        return means, n

    rng = np.random.default_rng(seed)
    draws = {arm: np.empty((n_boot, m)) for arm in E11_ARMS}
    absent = np.zeros(m, int)
    for b in range(n_boot):
        idx = np.concatenate(
            [pos[dec.cluster_draw(groups, rng)] for pos, groups in pool_groups]
        )
        means, n = league_means(idx)
        absent += (n == 0).astype(int)
        for arm in E11_ARMS:
            draws[arm][b] = means[arm]
    point, n = league_means(np.arange(len(frame)))
    table, pvalues = [], {}
    for k, league in enumerate(leagues):
        sub = frame.loc[codes == k]
        row = {
            "source_league": league,
            "arrivals": int(n[k]),
            "club_seasons": int(sub.cluster.nunique()),
            "mean_actual_eff36": float(sub[OUTCOME].mean()),
            "draws_league_absent": int(absent[k]),
        }
        for arm in E11_ARMS:
            d = draws[arm][:, k]
            row[f"mean_forecast_{arm}"] = float(sub[arm].mean())
            row[f"signed_error_{arm}"] = float(point[arm][k])
            row[f"ci95_low_{arm}"], row[f"ci95_high_{arm}"] = interval(d)
            p = power_line(d)
            row[f"bootstrap_se_{arm}"], row[f"mde_80_{arm}"] = (
                p["bootstrap_se"],
                p["mde_80"],
            )
            row[f"p_bootstrap_{arm}"] = bootstrap_p(d)
        pvalues[league] = row[f"p_bootstrap_{H}"]
        table.append(row)
    adjusted = recipes.holm(pvalues)
    for row in table:
        row[f"p_holm_{H}"] = adjusted[row["source_league"]]
        row.update(e11_licence(row))
    return {
        "table": pd.DataFrame(table),
        "overall_signed_error": {arm: float(signed[arm].mean()) for arm in E11_ARMS},
        "holm_family": "history-only bootstrap two-sided p, 10 source leagues",
    }


def e11_licence(row: dict) -> dict:
    name = row["source_league"]
    x = row[f"signed_error_{H}"]
    covers = bool(row[f"ci95_low_{O}"] <= 0 <= row[f"ci95_high_{O}"])
    if row[f"p_holm_{H}"] < HOLM_ALPHA:
        verb = "overrates" if x > 0 else "underrates"
        sentence = f"A league-blind forecast {verb} arrivals from {name} by {abs(x):.2f} EFF/36."
        if covers:
            sentence += " The league-aware forecast removes that bias."
        return {
            "licence": "bias",
            "league_aware_covers_zero": covers,
            "sentence": sentence,
        }
    return {
        "licence": "not_distinguishable",
        "league_aware_covers_zero": covers,
        "sentence": f"{name}: not distinguishable at this n.",
    }


def assert_signed_identity(
    e11_result: dict, rows: pd.DataFrame, tolerance: float = EXACT_TOLERANCE
) -> float:
    """Arrival-weighted league means reproduce the overall mean signed error."""
    t = e11_result["table"]
    if int(t.arrivals.sum()) != len(rows):
        raise GateFailure("E11 league counts do not add up to the targets")
    worst = 0.0
    for arm in E11_ARMS:
        overall = float((rows[arm] - rows[OUTCOME]).mean())
        weighted = float((t[f"signed_error_{arm}"] * t.arrivals).sum() / len(rows))
        worst = max(worst, abs(overall - weighted))
    return assert_close("E11 signed-error identity", worst, tolerance)


# -------------------------------------------------------------------- E12 --
def design(frame: pd.DataFrame, arm: str, info: dict) -> np.ndarray:
    """fit_model's design for `arm`, with source-offset columns from `info`."""
    x, names = benchmark.model_matrix(frame, arm)
    if arm.startswith("source_ridge_"):
        cats = info["source_categories"]
        dummies = [frame.league_src.eq(c).to_numpy(float) for c in cats]
        x = np.column_stack([x, *dummies])
        names = names + [f"source_offset:{c}" for c in cats]
    if names != info["features"]:
        raise GateFailure(f"design columns differ from the fit's features for {arm}")
    return x


def coefficient(info: dict, name: str = E12_FLAG) -> float:
    return float(info["coefficients"][info["features"].index(name)])


def fold_difference(rows: pd.DataFrame, folds: list, arms=E12_ARMS) -> float:
    """Re-predict every anchor forecast from its fold's own coefficients."""
    worst = 0.0
    for fold in folds:
        test = rows.loc[rows.season_dest.eq(fold["season"])]
        for arm in arms:
            info = fold["arms"][arm]
            pred = design(test, arm, info) @ np.asarray(info["coefficients"], float)
            worst = max(worst, max_abs(pred, test[arm]))
    return float(worst)


def e12(features: pd.DataFrame, folds: list, *, n_boot=N_BOOT, seed=SEED):
    """Full-fit beta_a with the e9 bootstrap (identical draws), plus the refits."""
    train = dec.e9_training(features)
    grid = dec.e9_grid(sorted(train.league_src.unique()))
    fits = {}
    for arm in E12_ARMS:
        _, info = benchmark.fit_model(train, grid, arm)
        if info["status"] != "ok":
            raise GateFailure(f"E12 full fit failed for {arm}: {info['status']}")
        fits[arm] = info
    groups = dec.cluster_index(train)
    rng = np.random.default_rng(seed)
    grid_draws = np.empty((n_boot, len(grid)))
    coef = {arm: [] for arm in E12_ARMS}
    for b in range(n_boot):
        sample = train.iloc[dec.cluster_draw(groups, rng)]
        for arm in E12_ARMS:
            pred, info = benchmark.fit_model(sample, grid, arm)
            if info["status"] != "ok":
                raise GateFailure(f"E12 bootstrap fit failed: {info['status']}")
            coef[arm].append(dict(zip(info["features"], info["coefficients"])))
            if arm == dec.E9_ARM:
                grid_draws[b] = pred
    point_grid, _ = benchmark.fit_model(train, grid, dec.E9_ARM)
    out = {"training_forecasts": int(len(train)), "arms": {}}
    for arm in E12_ARMS:
        d = np.array([c.get(E12_FLAG, math.nan) for c in coef[arm]])
        refits = [
            {
                "season": int(fold["season"]),
                "training_forecasts": len(fold["train_keys"]),
                "beta_a": coefficient(fold["arms"][arm]),
            }
            for fold in folds
        ]
        out["arms"][arm] = {
            "label": LABELS[arm],
            "beta_a": coefficient(fits[arm]),
            "ci95": interval(d),
            **power_line(d),
            "share_of_draws_below_zero": float(np.mean(d < 0)),
            "walk_forward": refits,
            "walk_forward_negative": int(sum(r["beta_a"] < 0 for r in refits)),
            "coefficients_full_fit": dict(
                zip(fits[arm]["features"], fits[arm]["coefficients"])
            ),
        }
    out["licence"] = e12_licence(out["arms"][O])
    fit = {
        "grid": grid.assign(forecast=point_grid),
        "grid_draws": grid_draws,
        "coef_draws": coef[dec.E9_ARM],
        "point": fits[dec.E9_ARM],
    }
    return out, fit


def e12_licence(block: dict) -> dict:
    lo, hi = block["ci95"]
    stable = block["walk_forward_negative"] == len(block["walk_forward"])
    if hi < 0 and stable:
        return {
            "licensed": True,
            "sentence": (
                "Holding his domestic rate and history fixed, a player signed after a season above "
                f"his own history is forecast {abs(block['beta_a']):.2f} EFF/36 lower."
            ),
        }
    return {
        "licensed": False,
        "sentence": "The career-year coefficient is not stable enough to report as a finding.",
    }


def e9_reproduction(fit: dict, e9_summary: dict, e9_table: pd.DataFrame) -> dict:
    """Point coefficients and grid intervals against the e9 run (same draws)."""
    recorded = e9_summary["e9"]["coefficients"]
    mine = dict(zip(fit["point"]["features"], fit["point"]["coefficients"]))
    if set(mine) != set(recorded):
        return {"coefficient_names": math.inf}
    worst = {"coefficients": max(abs(mine[k] - recorded[k]) for k in recorded)}
    grid = fit["grid"].copy()
    grid["lo"] = np.percentile(fit["grid_draws"], 2.5, axis=0)
    grid["hi"] = np.percentile(fit["grid_draws"], 97.5, axis=0)
    m = grid.merge(
        e9_table,
        on=["league_dest", "league_src"],
        suffixes=("", "_e9"),
        validate="1:1",
    )
    if len(m) != len(grid) or len(m) != len(e9_table):
        return {"grid_rows": math.inf}
    worst["forecast"] = max_abs(m.forecast, m.forecast_e9)
    worst["ci95_low"] = max_abs(m.lo, m.ci95_low)
    worst["ci95_high"] = max_abs(m.hi, m.ci95_high)
    return worst


# ---------------------------------------------- descriptive exchange rate --
def equivalent_rate(coefs: dict, league: str, destination: str) -> float:
    """Domestic EFF/36 in `league` forecast the same as an ACB 16 (history = rate)."""
    slope = coefs["source_rate"] + coefs["prior_rate"]
    if destination == "euroleague":
        slope += coefs["destination_x_source"]
    if not slope > 0:
        return math.nan
    gap = coefs[f"source_offset:{REFERENCE_LEAGUE}"] - coefs[f"source_offset:{league}"]
    return REFERENCE_RATE + gap / slope


def exchange_table(fit: dict, e9_table: pd.DataFrame) -> pd.DataFrame:
    point = dict(zip(fit["point"]["features"], fit["point"]["coefficients"]))
    leagues = sorted(
        c.split(":", 1)[1] for c in point if c.startswith("source_offset:")
    )
    rows = []
    for dest in dec.DESTINATIONS:
        for league in leagues:
            d = np.array([equivalent_rate(c, league, dest) for c in fit["coef_draws"]])
            lo, hi = interval(d)
            e9 = e9_table.loc[
                e9_table.league_dest.eq(dest) & e9_table.league_src.eq(league)
            ]
            rows.append(
                {
                    "destination": dest,
                    "source_league": league,
                    "acb16_equivalent_eff36": equivalent_rate(point, league, dest),
                    "ci95_low": lo,
                    "ci95_high": hi,
                    "finite_draws": int(np.isfinite(d).sum()),
                    "e9_tier": int(e9.tier.iloc[0]),
                    "e9_forecast_eff36": float(e9.forecast.iloc[0]),
                    "training_forecasts": int(e9.training_forecasts.iloc[0]),
                    "how_to_read": (
                        "Domestic EFF/36 in this league that the e9 league-aware model forecasts "
                        f"the same as a {REFERENCE_RATE:g} in {REFERENCE_LEAGUE} (career history equal "
                        "to that rate; source season not above it). Descriptive: offsets describe the "
                        "players clubs sign from a league, not pure league strength."
                    ),
                }
            )
    return pd.DataFrame(rows)


def exchange_difference(fit: dict, table: pd.DataFrame) -> float:
    """The forecast at each equivalent rate equals the forecast for an ACB 16."""
    info = fit["point"]
    beta = np.asarray(info["coefficients"], float)
    frame = pd.DataFrame(
        {
            "league_dest": table.destination.to_numpy(),
            "league_src": table.source_league.to_numpy(),
            "pir_per36_src": table.acb16_equivalent_eff36.to_numpy(),
            "prior_mean_pir36": table.acb16_equivalent_eff36.to_numpy(),
            "above_own_prior": False,
        }
    )
    ref = frame.assign(
        league_src=REFERENCE_LEAGUE,
        pir_per36_src=REFERENCE_RATE,
        prior_mean_pir36=REFERENCE_RATE,
    )
    left = design(frame, dec.E9_ARM, info) @ beta
    return max_abs(left, design(ref, dec.E9_ARM, info) @ beta)


# -------------------------------------------------------------------- E17 --
def nested_difference(a, b, path="") -> dict:
    """Largest numeric difference between two JSON-like records (keys must match)."""
    if isinstance(a, dict) and isinstance(b, dict):
        if set(a) != set(b):
            return {path: math.inf}
        out = {}
        for k in a:
            out.update(nested_difference(a[k], b[k], f"{path}/{k}"))
        return out
    if isinstance(a, (list, tuple)) and isinstance(b, (list, tuple)):
        if len(a) != len(b):
            return {path: math.inf}
        out = {}
        for k, (x, y) in enumerate(zip(a, b)):
            out.update(nested_difference(x, y, f"{path}/{k}"))
        return out
    if (
        a is None
        or b is None
        or isinstance(a, (str, bool))
        or isinstance(b, (str, bool))
    ):
        return {path: 0.0 if a == b else math.inf}
    return {path: abs(float(a) - float(b))}


def reading(block: dict) -> str:
    lo, hi = block["ci95"]
    if lo > 0:
        return "above_zero"
    if hi < 0:
        return "below_zero"
    return (
        "spans_zero_point_nonnegative"
        if block["difference"] >= 0
        else "spans_zero_point_negative"
    )


def e17_head_to_head(rows: pd.DataFrame, recipes_summary: dict):
    heads, shares = {}, {}
    for p in common.PENALTIES:
        heads[f"lambda_{p}"] = recipes.contrast_summary(rows, HT, f"source_ridge_{p}")
        shares[f"lambda_{p}"] = recipes.recovered_share(rows, f"source_ridge_{p}")
    worst = nested_difference(
        {"head_to_head": heads, "recovered_share": shares},
        {
            "head_to_head": recipes_summary["e1"]["head_to_head"],
            "recovered_share": recipes_summary["e1"]["recovered_share"],
        },
    )
    out = {}
    for p in common.PENALTIES:
        block = heads[f"lambda_{p}"]
        out[f"lambda_{p}"] = {
            "primary": p == common.PRIMARY_PENALTY,
            "c_h": block["player_club_season"],
            "c_h_player_season": block["player_season"],
            "parent_mae": block["parent_mae"],
            "recovered_share": shares[f"lambda_{p}"],
            "reading": reading(block["player_club_season"]),
        }
    return out, worst


def weighted_multiway(d, w, first, second) -> dict:
    """Weighted mean of paired differences with the two-way CGM CR1 interval.

    With equal weights this is v10's multiway_interval exactly: residual totals
    w_i (d_i - d_w) per cluster, variance g/(g-1) sum(T_c^2) / (sum w)^2,
    V = V_first + V_second - V_intersection, Student t with min(G) - 1 df.
    """
    d, w = np.asarray(d, float), np.asarray(w, float)
    ok = np.isfinite(d).all() and np.isfinite(w).all() and (w >= 0).all()
    if not ok or not w.sum() > 0:
        raise GateFailure("weighted contrast needs finite values and weights >= 0")
    first = pd.Series(first).reset_index(drop=True)
    second = pd.Series(second).reset_index(drop=True)
    mean = float(np.sum(w * d) / np.sum(w))
    residual = w * (d - mean)
    variance, clusters = 0.0, {}
    for name, values, sign in (
        ("first", first, 1),
        ("second", second, 1),
        ("intersection", pd.Series(list(zip(first, second))), -1),
    ):
        codes, ids = pd.factorize(values, sort=False)
        g = len(ids)
        totals = np.bincount(codes, weights=residual)
        variance += sign * g / (g - 1) * (totals @ totals) / np.sum(w) ** 2
        clusters[name] = g
    df = min(clusters["first"], clusters["second"]) - 1
    se = math.sqrt(variance) if variance > 0 else math.nan
    half = float(stats.t.ppf(0.975, df) * se)
    p = float(2 * stats.t.sf(abs(mean / se), df)) if se > 0 else math.nan
    return {
        "n": int(len(d)),
        "difference": mean,
        "ci95": [mean - half, mean + half],
        "se": se,
        "df": int(df),
        "p_two_sided": p,
        "clusters": clusters,
    }


def paired_difference(rows, left, right) -> np.ndarray:
    e_left = np.abs(rows[left] - rows[OUTCOME])
    return (e_left - np.abs(rows[right] - rows[OUTCOME])).to_numpy(float)


def equal_weight_difference(rows: pd.DataFrame) -> float:
    """Equal weights must reproduce the registered unweighted interval exactly."""
    worst = 0.0
    for left, right in HEADLINE_CONTRASTS:
        ref = common.contrast(rows, left, right)["player_club_season"]
        got = weighted_multiway(
            paired_difference(rows, left, right),
            np.ones(len(rows)),
            rows.player_name,
            rows.cluster,
        )
        worst = max(
            worst,
            abs(got["difference"] - ref["difference"]),
            max_abs(got["ci95"], ref["ci95"]),
        )
    return worst


def e17_weighted(rows: pd.DataFrame) -> dict:
    w = rows.minutes_dest.to_numpy(float)
    mae = {}
    for arm in MODELS:
        err = np.abs(rows[arm] - rows[OUTCOME]).to_numpy(float)
        mae[arm] = {
            "unweighted": float(err.mean()),
            "minutes_weighted": float(np.sum(w * err) / np.sum(w)),
        }
    contrasts = {}
    for left, right in HEADLINE_CONTRASTS:
        d = paired_difference(rows, left, right)
        weighted = weighted_multiway(d, w, rows.player_name, rows.cluster)
        unweighted = weighted_multiway(
            d, np.ones(len(rows)), rows.player_name, rows.cluster
        )
        parent = mae[left]["minutes_weighted"]
        weighted["parent_mae"] = parent
        weighted["pct_of_parent"] = 100 * weighted["difference"] / parent
        weighted["upper_pct_of_parent"] = 100 * weighted["ci95"][1] / parent
        weighted["reading"] = reading(weighted)
        unweighted["reading"] = reading(unweighted)
        contrasts[tag(left, right)] = {
            "left": left,
            "right": right,
            "minutes_weighted": weighted,
            "unweighted": unweighted,
        }
    return {
        "weights": "destination minutes (minutes_dest)",
        "total_minutes": float(w.sum()),
        "mae": mae,
        "contrasts": contrasts,
    }


def assert_floor(
    floor: float,
    registered: float = REGISTERED_FLOOR,
    tolerance: float = FLOOR_TOLERANCE,
) -> float:
    return assert_close(
        f"E6 floor gate (registered {registered})", abs(floor - registered), tolerance
    )


def e17_reducible(rows: pd.DataFrame, floor: float) -> pd.DataFrame:
    base = common.mae(rows, H) - floor
    out = []
    for arm in common.ALL_ARMS:
        m = common.mae(rows, arm)
        out.append(
            {
                "arm": arm,
                "in_table_1": arm in TABLE1_ARMS,
                "mae": m,
                "floor": floor,
                "excess_over_floor": m - floor,
                "history_reducible": base,
                "share_of_reducible_remaining": (m - floor) / base,
                "share_of_reducible_removed": 1 - (m - floor) / base,
            }
        )
    return pd.DataFrame(out)


def e17_counts(train, rows, pairs, leagues) -> pd.DataFrame:
    out = []
    frames = (("e9_training", train), ("anchor_674", rows), ("factor_pairs", pairs))
    for league in leagues:
        row = {"source_league": league}
        for name, frame in frames:
            sub = frame.loc[frame.league_src.eq(league)]
            row[name] = int(len(sub))
            for dest in dec.DESTINATIONS:
                row[f"{name}_{dest}"] = int(sub.league_dest.eq(dest).sum())
        out.append(row)
    return pd.DataFrame(out)


def assert_counts(table: pd.DataFrame, expected: dict) -> dict:
    got = {k: int(table[k].sum()) for k in expected}
    bad = {k: [got[k], v] for k, v in expected.items() if got[k] != v}
    for k in expected:
        split = table[f"{k}_euroleague"].sum() + table[f"{k}_eurocup"].sum()
        if int(split) != got[k]:
            bad[f"{k}:destinations"] = [int(split), got[k]]
    if bad:
        raise GateFailure(f"count gate failed: {bad}")
    return got


def e17_recipes(r_rows: pd.DataFrame, recipes_summary: dict, gain: float):
    out, worst = [], {}
    margin = recipes_summary["margin_share_of_parent"]
    for recipe in RECIPES:
        rr = r_rows.loc[r_rows.recipe.eq(recipe)].reset_index(drop=True)
        inc = recipes.contrast_summary(rr, O, OT)
        own = recipes.contrast_summary(rr, H, HT)
        ladder = recipes_summary["results"]["A"][recipe]["ladder"]
        for name, (mine, recorded) in {
            "increment": (inc, ladder[f"{O}->{OT}"]),
            "history_gain": (own, ladder[f"{H}->{HT}"]),
        }.items():
            diff = nested_difference(
                {s: mine[s] for s in recipes.SPECS},
                {s: recorded[s] for s in recipes.SPECS},
            )
            worst.update({f"{recipe}/{name}{k}": v for k, v in diff.items()})
        for spec in recipes.SPECS:
            block = inc[spec]
            parent = inc["parent_mae"]
            out.append(
                {
                    "recipe": recipe,
                    "spec": spec,
                    "increment": block["difference"],
                    "ci95_low": block["ci95"][0],
                    "upper_bound_eff36": block["ci95"][1],
                    "parent_mae": parent,
                    "margin_2pct_eff36": margin * parent,
                    "upper_pct_of_parent": block["upper_pct_of_parent"],
                    "history_gain_r1": gain,
                    "upper_share_of_history_gain_r1": block["ci95"][1] / gain,
                    "margin_share_of_history_gain_r1": margin * parent / gain,
                    "history_gain_own_recipe": own[spec]["difference"],
                    "upper_share_of_own_history_gain": block["ci95"][1]
                    / own[spec]["difference"],
                }
            )
    return pd.DataFrame(out), worst


# ------------------------------------------------------------------- main --
def passed(value: float, control: str, **extra) -> dict:
    return {
        "status": "passed",
        "max_difference": value,
        **extra,
        "negative_control": control,
    }


def run(root: Path, input_dir: Path, prior_dir: Path, out: Path, n_boot=N_BOOT):
    root = Path(root)
    prior = load_prior(prior_dir)
    v9, v10_summary = common.load_references(root)
    rows, features, folds = common.anchor_rows(root, input_dir)
    gates = {}

    diffs = common.g0_differences(rows, v9, v10_summary)
    g0_control = negative_control(common.assert_g0, diffs, tolerance=-1.0)
    common.assert_g0(diffs)
    gates["G0"] = passed(max(diffs.values()), g0_control, tolerance=common.G0_TOLERANCE)
    control = negative_control(
        dec.assert_scope, rows, expected_targets=dec.EXPECTED_TARGETS + 1
    )
    gates["scope"] = {
        "status": "passed",
        **dec.assert_scope(rows),
        "negative_control": control,
    }

    keyed = prior["decide-02/e7_keyed_forecasts.csv"]
    r_rows = prior["recipes-01/rows_pool_A.parquet"]
    worst = reproduction_difference(rows, keyed, r_rows.loc[r_rows.recipe.eq("R1")])
    gates["reproduction"] = passed(
        gate_max("reproduction gate", worst, REPRO_TOLERANCE),
        negative_control(gate_max, "reproduction gate", worst, -1.0),
        tolerance=REPRO_TOLERANCE,
        checked=sorted(worst),
    )
    leagues = assert_leagues(rows)
    gates["source_leagues"] = {
        "status": "passed",
        "leagues": leagues,
        "negative_control": negative_control(
            assert_leagues, rows, expected=EXPECTED_LEAGUES + 1
        ),
    }

    # ---- E10
    ten = e10(rows, keyed[KEY + ["odd_rate", "even_rate"]], n_boot=n_boot)
    counts10 = ten["pool_counts"]
    gates["E10_partition"] = passed(
        assert_partition(counts10),
        negative_control(assert_partition, counts10, tolerance=-1.0),
    )
    gates["E10_identity"] = passed(
        assert_typed_identity(counts10),
        negative_control(assert_typed_identity, counts10, tolerance=-1.0),
    )
    w7 = e7_reproduction(ten["pooled"], prior["decide-02/summary.json"])
    gates["E10_reproduces_E7"] = passed(
        gate_max("E7 reproduction gate", w7, EXACT_TOLERANCE),
        negative_control(gate_max, "E7 reproduction gate", w7, -1.0),
        checked=sorted(w7),
    )

    # ---- E11
    eleven = e11(rows, leagues, n_boot=n_boot)
    gates["E11_identity"] = passed(
        assert_signed_identity(eleven, rows),
        negative_control(assert_signed_identity, eleven, rows, tolerance=-1.0),
    )

    # ---- E12 and the descriptive exchange rate (same draws)
    twelve, fit = e12(features, folds, n_boot=n_boot)
    fw = {"fold": fold_difference(rows, folds)}
    gates["E12_fold_coefficients"] = passed(
        gate_max("E12 fold-coefficient gate", fw, REPRO_TOLERANCE),
        negative_control(gate_max, "E12 fold-coefficient gate", fw, -1.0),
    )
    e9_table = prior["decide-02/e9_league_tiers_full.csv"]
    w9 = e9_reproduction(fit, prior["decide-02/summary.json"], e9_table)
    gates["E12_reproduces_e9"] = passed(
        gate_max("e9 reproduction gate", w9, REPRO_TOLERANCE),
        negative_control(gate_max, "e9 reproduction gate", w9, -1.0),
        checked=sorted(w9),
    )
    exchange = exchange_table(fit, e9_table)
    xw = {"equivalence": exchange_difference(fit, exchange)}
    gates["exchange_rate_equivalence"] = passed(
        gate_max("exchange-rate equivalence gate", xw, REPRO_TOLERANCE),
        negative_control(gate_max, "exchange-rate equivalence gate", xw, -1.0),
        finite_draws_min=int(exchange.finite_draws.min()),
    )

    # ---- E17
    head, w1 = e17_head_to_head(rows, prior["recipes-01/summary.json"])
    gates["E17_reproduces_E1"] = passed(
        gate_max("E1 reproduction gate", w1, EXACT_TOLERANCE),
        negative_control(gate_max, "E1 reproduction gate", w1, -1.0),
    )
    ew = {"equal_weights": equal_weight_difference(rows)}
    gates["E17_equal_weight_reduction"] = passed(
        gate_max("equal-weight reduction gate", ew, EXACT_TOLERANCE),
        negative_control(gate_max, "equal-weight reduction gate", ew, -1.0),
    )
    weighted = e17_weighted(rows)
    floor = float(
        prior["robustness-02/summary.json"]["e6"]["outcomes"]["O1"]["floor_normal"]
    )
    gates["E17_floor"] = passed(
        assert_floor(floor),
        negative_control(assert_floor, floor, registered=REGISTERED_FLOOR + 0.1),
        floor=floor,
    )
    reducible = e17_reducible(rows, floor)
    pairs, _ = common.load_pool(input_dir, "official_corrected")
    counts = e17_counts(dec.e9_training(features), rows, pairs, leagues)
    expected = {
        "e9_training": EXPECTED_TRAINING,
        "anchor_674": dec.EXPECTED_TARGETS,
        "factor_pairs": EXPECTED_PAIRS,
    }
    gates["E17_counts"] = {
        "status": "passed",
        **assert_counts(counts, expected),
        "negative_control": negative_control(
            assert_counts, counts, {**expected, "factor_pairs": EXPECTED_PAIRS + 1}
        ),
    }
    gain = recipes.contrast_summary(rows, H, HT)["player_club_season"]["difference"]
    recipe_table, w2 = e17_recipes(r_rows, prior["recipes-01/summary.json"], gain)
    gates["E17_reproduces_E2"] = passed(
        gate_max("E2 reproduction gate", w2, EXACT_TOLERANCE),
        negative_control(gate_max, "E2 reproduction gate", w2, -1.0),
    )

    out = Path(out)
    out.mkdir(parents=True, exist_ok=False)
    e10_table(ten["pooled"]).to_csv(out / "e10_pair_types.csv", index=False)
    ten["per_pool"].to_csv(out / "e10_pools.csv", index=False)
    eleven["table"].to_csv(out / "e11_signed_error_by_league.csv", index=False)
    e12_rows = []
    for arm, b in twelve["arms"].items():
        e12_rows.append(
            {
                "arm": arm,
                "scope": "full fit through 2025",
                "season": None,
                "training_forecasts": twelve["training_forecasts"],
                "beta_a": b["beta_a"],
                "ci95_low": b["ci95"][0],
                "ci95_high": b["ci95"][1],
            }
        )
        for r in b["walk_forward"]:
            e12_rows.append(
                {
                    "arm": arm,
                    "scope": "walk-forward refit",
                    **r,
                    "ci95_low": None,
                    "ci95_high": None,
                }
            )
    pd.DataFrame(e12_rows).to_csv(out / "e12_career_year.csv", index=False)
    exchange.to_csv(out / "exchange_rate_acb16.csv", index=False)
    reducible.to_csv(out / "e17_reducible.csv", index=False)
    counts.to_csv(out / "e17_league_counts.csv", index=False)
    recipe_table.to_csv(out / "e17_recipe_margins.csv", index=False)

    summary = {
        "analysis": "Amendment 1: E10, E11, E12, E17 (exploratory; destination seasons 2020-2025 already seen)",
        "exploratory": True,
        "protocol_commit": common.PROTOCOL_COMMIT,
        "protocol_sha256": sha256_file(root / common.PROTOCOL),
        "amendment_commit": AMENDMENT_COMMIT,
        "amendment_sha256": sha256_file(root / AMENDMENT),
        "input_sha256": {
            "pairs": common.PAIRS_SHA["official_corrected"],
            "cohort": common.COHORT_SHA,
            **PRIOR_FILES,
        },
        "n_boot": n_boot,
        "seed": SEED,
        "n_targets": int(len(rows)),
        "models": {arm: LABELS[arm] for arm in MODELS},
        "gates": gates,
        "e10": {"pooled": ten["pooled"], "licence": e10_licence(ten["pooled"])},
        "e11": {
            "overall_signed_error": eleven["overall_signed_error"],
            "holm_family": eleven["holm_family"],
            "p_value_rule": "two-sided bootstrap p = min(1, 2 (k + 1) / (B + 1)), k = draws on the smaller side of 0",
            "leagues": eleven["table"].to_dict(orient="records"),
        },
        "e12": twelve,
        "exchange_rate": {
            "descriptive": True,
            "reference": {"league": REFERENCE_LEAGUE, "eff36": REFERENCE_RATE},
            "rule": "x_L = 16 + (offset_ACB - offset_L) / (b_source + b_prior + b_ELxsource [EuroLeague only]); history = x_L, a = 0",
            "rows": exchange.to_dict(orient="records"),
        },
        "e17": {
            "head_to_head": head,
            "minutes_weighted": weighted,
            "reducible": {
                "floor": floor,
                "floor_source": "robustness-02 summary e6 O1 floor_normal",
                "rows": reducible.to_dict(orient="records"),
            },
            "league_counts": counts.to_dict(orient="records"),
            "recipe_margins": {
                "history_gain_r1": gain,
                "margin_share_of_parent": prior["recipes-01/summary.json"][
                    "margin_share_of_parent"
                ],
                "rows": recipe_table.to_dict(orient="records"),
            },
        },
    }
    (out / "summary.json").write_text(
        json.dumps(clean(summary), indent=2, sort_keys=True) + "\n"
    )
    return summary


def clean(value):
    """JSON-safe: NaN/inf -> None, numpy scalars -> Python."""
    if isinstance(value, dict):
        return {str(k): clean(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [clean(v) for v in value]
    if isinstance(value, (bool, np.bool_)):
        return bool(value)
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, (float, np.floating)):
        return float(value) if math.isfinite(value) else None
    return value


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument(
        "--prior-dir",
        type=Path,
        required=True,
        help="staged outputs of retained runs decide-02, recipes-01 and robustness-02",
    )
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--n-boot", type=int, default=N_BOOT)
    args = parser.parse_args(argv)
    summary = run(Path.cwd(), args.input_dir, args.prior_dir, args.out, args.n_boot)
    print(summary["e10"]["licence"]["sentence"])
    print(summary["e12"]["licence"]["sentence"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
