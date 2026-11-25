#!/usr/bin/env python3
"""Amendment 3 analyses: E18, E19, E20, E21, E22 and E23 (all EXPLORATORY).

Pre-registration: docs/research/sloan-full-paper-preregistration-2026-11-03.md
(commit f52e7c831) and its Amendment 3,
docs/research/sloan-full-paper-preregistration-amendment-3-2026-11-11.md
(commit caf090288, pushed alone 2026-11-11 16:06 UTC, before this file
existed). Destination seasons 2020-2025 were exposed, so every number here is
exploratory.

* E18 -- the level of the forecasts. E18a: mean signed error (forecast - actual
  EFF/36) on the 674, by destination and by season, for history, history +
  translation and offsets l10. E18b: each source league's signed error minus
  the all-arrival mean, computed inside every bootstrap draw, with Holm across
  the 10 leagues for history-only, and the spread contrast S(history) -
  S(offsets l10). E18c (descriptive): continental EFF/36 by competition and
  season, for benchmark arrivals and for all continental player-seasons with at
  least eight games (the E14 corpus rebuild).
* E19 -- the ACB-16 equivalent of every league in the six registered
  walk-forward refits and the full fit, with per-league ranges, consecutive
  changes and the 144 tier-1 x tier-3 comparisons.
* E20 -- ordering accuracy by size of the forecast gap, bins fixed in the
  amendment, with the E7/E10 within-pool cluster bootstrap.
* E21 -- flip share and right share of offsets l10 against history-only, on
  all, cross-league and same-league pairs (a re-expression of E10's gain).
* E22 -- coverage of the registered E8 conformal bands by source league, with
  Wilson intervals. No interval method is fitted here.
* E23 -- the above-average-season discount. E23a: the coefficient on the jump
  u = max(0, source rate - earlier career rate) added to the offsets l10 model
  (M1), and replacing the flag (M2), with the e9 cluster bootstrap and the six
  refits; paired walk-forward MAE against the registered model (M0). E23b: the
  share of arrivals signed after an above-average season, against all
  comparable domestic player-seasons.

Threats and their controls (all in this file): drift from the submitted numbers
(G0); a changed target set (scope gate); forecasts that differ from the E7 run
(reproduction gate); league means that are not E11's (G18: the arrival-weighted
mean of the registered E11 errors equals the overall mean, and the per-league
intervals reproduce E11's); refit coefficients that are not the registered
ones (G19: full-fit equivalents equal the published table, per-refit flag
coefficients equal E12's); a bin split that loses pairs (G20: bins partition
the pairs and pooled accuracy equals E7's); a flip count that is not E10's gain
(G21); bands that are not E8's (G22); a re-implemented model that is not the
registered one (G23: M0 reproduces the e9 coefficients and every anchor
forecast); a jump that disagrees with the registered flag (jump gate); a
history rule that does not reproduce v10 (prior-rule gate). Every gate has a
negative control that must reject (METHOD.md section 8). No 2026-27 data is
read. M1 and M2 are sensitivity checks only: M0 stays the league-aware model.
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

from scripts import sloan_context_benchmarks as benchmark  # noqa: E402
from scripts import sloan_fullpaper_amend1_decisions as a1  # noqa: E402
from scripts import sloan_fullpaper_common as common  # noqa: E402
from scripts import sloan_fullpaper_decisions as dec  # noqa: E402
from scripts import sloan_fullpaper_recipes as recipes  # noqa: E402
from scripts import sloan_fullpaper_robustness as robust  # noqa: E402
from scripts import sloan_fullpaper_survivorship as surv  # noqa: E402
from scripts.translation_research_common import sha256_file  # noqa: E402

KEY = common.KEY
OUTCOME = dec.OUTCOME
N_BOOT = 2000
SEED = 0
AMENDMENT = Path(
    "docs/research/sloan-full-paper-preregistration-amendment-3-2026-11-11.md"
)
AMENDMENT_COMMIT = "caf090288864a71e8dc06ac364ad1640f625fd96"

H, HT, O = dec.HISTORY, dec.HISTORY_T, dec.OFFSETS
ARMS = (H, HT, O)
LABELS = dec.LABELS
REPRO_TOLERANCE = 1e-9
EXACT_TOLERANCE = 1e-12
HOLM_ALPHA = 0.05

#: E19 tiers of the published table (Amendment 3, E19).
TIER1 = ("spain-acb", "france-pro-a", "italy-lba")
TIER3 = ("aba-league", "germany-bbl", "vtb", "lithuania-lkl")
THIN_TRAINING = 10
EXPECTED_TIER_COMPARISONS = 144

#: E20 bins of the absolute forecast gap, EFF/36 (Amendment 3, E20).
BIN_EDGES = (0.0, 1.0, 2.0, 3.0, 4.0, 6.0, math.inf)
BIN_LABELS = ("0 to 1", "1 to 2", "2 to 3", "3 to 4", "4 to 6", "6 or more")
E20_KINDS = ("all", "cross")
E21_KINDS = ("all", "cross", "same")
EXPECTED_PAIRS = 22365
TRUST_LEVELS = (0.60, 0.70)

E22_LEVELS = (0.80, 0.95)
WILSON_Z = 1.959963984540054

#: E23 model variants. M0 is the registered offsets l10 model.
VARIANTS = ("M0", "M1", "M2")
JUMP = "jump_above_prior"
FLAG = "above_prior"
E23_COLUMNS = {"M1": "e23_m1", "M2": "e23_m2"}
RIDGE_PENALTY = 10

#: Outputs of earlier retained runs reused as inputs, pinned to their receipts.
PRIOR_FILES = {
    "decide-02/e7_keyed_forecasts.csv": "83589795f00df04cdb272155697f6f9d55c8f7604e49ae3bc45e0e1aac04b8f6",
    "decide-02/summary.json": "ce1d9bafd1364c548c29a9a8e774bf3d32dc3ac39a431dc0742377f9eff56666",
    "decide-02/e9_league_tiers_full.csv": "9c233bad8bde45e67e53fd06f94feb4d899b3ee59e720bfd181b94091e8f3ef1",
    "decide-02/e8_conformal.csv": "30733719510cd90aa4402c0bc3ea93450e6bafd2e8c0fd331f6199cce80d7842",
    "recipes-01/rows_pool_A.parquet": "ce4f91e0ef854b684522efcf7d736b7c48a074277ac83a1fad016be7f7006eb3",
    "amend1-decisions-01/summary.json": "94a1bb6576234d6f94bff9da12293799cca4ff71fa4d6589d7a30169e8935fe9",
    "amend1-decisions-01/e11_signed_error_by_league.csv": "ab3fcb15675fbeb6199b80f23ff14bf51bf6fed037b717dbc555933c6f2e5d57",
    "amend1-decisions-01/e12_career_year.csv": "80ebb339c543371edbf22b397354e677a2b13ad7d1fda86843d3164cda3cbdb4",
    "amend1-decisions-01/exchange_rate_acb16.csv": "c8341a37947adcad882f90c9747ea6fee274723b367a0948bbfc50462fead2ca",
}

#: What had been seen before this amendment was registered, and after.
EXPOSURE = {
    "seen_before_registration_2026-11-11": [
        "mean signed error on the 674 for history-only and offsets l10, with intervals",
        "offsets l10 signed error by destination and by season; history-only by season",
        "the registered E11 signed errors by league and arithmetic on them",
        "all-pairs flip share and right share of offsets l10 against history-only",
        "the registered E8 coverage by season",
        "the distribution of forecast gaps under offsets l10 (no outcome used)",
    ],
    "seen_after_registration_before_this_run": [
        "the count of above-own-history flags on the 674 targets (359 of 582 with a history), printed while loading the inputs during implementation",
    ],
}


class GateFailure(common.GateFailure):
    """A registered Amendment 3 gate did not hold."""


interval = dec.interval
power_line = dec.power_line
negative_control = a1.negative_control
max_abs = a1.max_abs
gate_max = a1.gate_max
passed = a1.passed
clean = a1.clean


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


def pool_frame(rows: pd.DataFrame):
    """Rows in E11's order, with E11's within-pool cluster index."""
    frame = rows.sort_values(dec.POOL_KEY + KEY).reset_index(drop=True)
    pool_of = frame.groupby(dec.POOL_KEY, sort=True).ngroup().to_numpy()
    pool_groups = []
    for g in range(pool_of.max() + 1):
        pos = np.flatnonzero(pool_of == g)
        groups = dec.cluster_index(frame.iloc[pos].reset_index(drop=True))
        pool_groups.append((pos, groups))
    return frame, pool_groups


def pool_draw(pool_groups: list, rng: np.random.Generator) -> np.ndarray:
    """One draw: destination club-seasons resampled within every pool, in order."""
    return np.concatenate(
        [pos[dec.cluster_draw(groups, rng)] for pos, groups in pool_groups]
    )


def ratio(a: float, b: float) -> float:
    return a / b if b else math.nan


# -------------------------------------------------------------------- E18 --
def spread(biases: np.ndarray, counts: np.ndarray) -> float:
    """Arrival-weighted root mean square of the re-based league biases."""
    ok = counts > 0
    if not ok.any():
        return math.nan
    return float(np.sqrt(np.sum(counts[ok] * biases[ok] ** 2) / np.sum(counts[ok])))


def e18(rows: pd.DataFrame, leagues: list, *, n_boot=N_BOOT, seed=SEED) -> dict:
    """E18a level and E18b re-based league biases, on E11's bootstrap draws."""
    frame, pool_groups = pool_frame(rows)
    signed = {arm: (frame[arm] - frame[OUTCOME]).to_numpy(float) for arm in ARMS}
    codes = pd.Categorical(frame.league_src, categories=leagues).codes
    if (codes < 0).any():
        raise GateFailure("a target's source league is outside the league list")
    m = len(leagues)
    dest = frame.league_dest.to_numpy(object)
    season = frame.season_dest.to_numpy(int)
    scopes = {"all": np.ones(len(frame), bool)}
    for d in dec.DESTINATIONS:
        if (dest == d).any():
            scopes[f"destination:{d}"] = dest == d
    for s in sorted(set(season)):
        scopes[f"season:{s}"] = season == s

    def evaluate(idx):
        n = np.bincount(codes[idx], minlength=m).astype(float)
        out = {}
        for arm, s in signed.items():
            v = s[idx]
            overall = float(v.mean())
            with np.errstate(invalid="ignore", divide="ignore"):
                league = np.bincount(codes[idx], weights=v, minlength=m) / n
            out[arm] = {
                "level": {
                    name: float(v[mask[idx]].mean()) if mask[idx].any() else math.nan
                    for name, mask in scopes.items()
                },
                "league": league,
                "rebased": league - overall,
                "spread": spread(np.nan_to_num(league - overall), n),
            }
        return out

    point = evaluate(np.arange(len(frame)))
    rng = np.random.default_rng(seed)
    draws = [evaluate(pool_draw(pool_groups, rng)) for _ in range(n_boot)]

    level_rows = []
    for arm in ARMS:
        for name, mask in scopes.items():
            d = np.array([x[arm]["level"][name] for x in draws])
            lo, hi = interval(d)
            level_rows.append(
                {
                    "arm": arm,
                    "label": LABELS[arm],
                    "scope": name,
                    "n": int(mask.sum()),
                    "mean_signed_error": point[arm]["level"][name],
                    "ci95_low": lo,
                    "ci95_high": hi,
                    **power_line(d),
                }
            )
    league_rows, pvalues = [], {}
    n_point = np.bincount(codes, minlength=m)
    for k, league in enumerate(leagues):
        row = {"source_league": league, "arrivals": int(n_point[k])}
        for arm in ARMS:
            raw = np.array([x[arm]["league"][k] for x in draws])
            reb = np.array([x[arm]["rebased"][k] for x in draws])
            row[f"signed_error_{arm}"] = float(point[arm]["league"][k])
            row[f"raw_ci95_low_{arm}"], row[f"raw_ci95_high_{arm}"] = interval(raw)
            row[f"rebased_{arm}"] = float(point[arm]["rebased"][k])
            row[f"rebased_ci95_low_{arm}"], row[f"rebased_ci95_high_{arm}"] = interval(
                reb
            )
            row[f"rebased_p_bootstrap_{arm}"] = a1.bootstrap_p(reb)
            row[f"rebased_mde_80_{arm}"] = power_line(reb)["mde_80"]
        pvalues[league] = row[f"rebased_p_bootstrap_{H}"]
        league_rows.append(row)
    adjusted = recipes.holm(pvalues)
    for row in league_rows:
        row[f"rebased_p_holm_{H}"] = adjusted[row["source_league"]]
        row.update(e18b_licence(row))
    spreads = {}
    for arm in ARMS:
        d = np.array([x[arm]["spread"] for x in draws])
        spreads[arm] = {"point": point[arm]["spread"], "ci95": interval(d)}
    contrast = np.array([x[H]["spread"] - x[O]["spread"] for x in draws])
    spread_contrast = {
        "definition": "S(history-only) - S(offsets l10); S = arrival-weighted RMS of the 10 re-based league biases",
        "point": point[H]["spread"] - point[O]["spread"],
        "ci95": interval(contrast),
        **power_line(contrast),
        "note": "S is inflated by sampling noise in both arms; the contrast is read, not the level",
    }
    spread_contrast["licensed"] = bool(spread_contrast["ci95"][0] > 0)
    spread_contrast["sentence"] = (
        "The league table flattens the league pattern."
        if spread_contrast["licensed"]
        else "The spread of league biases is not detectably smaller with the league table at this n."
    )
    level = pd.DataFrame(level_rows)
    return {
        "level": level,
        "leagues": pd.DataFrame(league_rows),
        "spread": spreads,
        "spread_contrast": spread_contrast,
        "level_licence": [e18a_licence(r) for r in level_rows if r["scope"] == "all"],
        "holm_family": "history-only re-based bootstrap two-sided p, 10 source leagues",
    }


def e18a_licence(row: dict) -> dict:
    below = row["ci95_high"] < 0
    return {
        "arm": row["arm"],
        "licensed": bool(below),
        "sentence": (
            f"On average the {row['label']} forecast is {abs(row['mean_signed_error']):.2f} EFF/36 below what arrivals delivered."
            if below
            else f"The {row['label']} forecast's average signed error ({row['mean_signed_error']:+.2f} EFF/36) is not distinguishable from zero at this n."
        ),
    }


def e18b_licence(row: dict) -> dict:
    value = row[f"rebased_{H}"]
    if row[f"rebased_p_holm_{H}"] < HOLM_ALPHA:
        verb = "underrates" if value < 0 else "overrates"
        return {
            "licence": "licensed",
            "sentence": (
                "Measured against the average arrival, a league-blind forecast "
                f"{verb} arrivals from {row['source_league']} by {abs(value):.2f} EFF/36."
            ),
        }
    return {
        "licence": "not_distinguishable",
        "sentence": f"{row['source_league']}: not distinguishable at this n.",
    }


def g18_differences(
    result: dict, e11_table: pd.DataFrame, drop=None, check_intervals=True
) -> dict:
    """E11's arrival-weighted league mean equals the overall mean; E11 intervals reproduce."""
    table = (
        e11_table if drop is None else e11_table.loc[e11_table.source_league != drop]
    )
    level = result["level"]
    worst = {}
    for arm in ARMS:
        overall = float(
            level.loc[
                level.arm.eq(arm) & level.scope.eq("all"), "mean_signed_error"
            ].iloc[0]
        )
        weighted = float(
            np.sum(table.arrivals * table[f"signed_error_{arm}"])
            / np.sum(table.arrivals)
        )
        worst[f"weighted_mean:{arm}"] = abs(weighted - overall)
    if drop is None:
        mine = result["leagues"].set_index("source_league")
        theirs = e11_table.set_index("source_league")
        if set(mine.index) != set(theirs.index):
            return {"league_set": math.inf}
        theirs = theirs.loc[mine.index]
        for arm in ARMS:
            worst[f"point:{arm}"] = max_abs(
                mine[f"signed_error_{arm}"], theirs[f"signed_error_{arm}"]
            )
            if check_intervals:
                worst[f"ci_low:{arm}"] = max_abs(
                    mine[f"raw_ci95_low_{arm}"], theirs[f"ci95_low_{arm}"]
                )
                worst[f"ci_high:{arm}"] = max_abs(
                    mine[f"raw_ci95_high_{arm}"], theirs[f"ci95_high_{arm}"]
                )
    return worst


def e18c(features: pd.DataFrame, agg: pd.DataFrame) -> pd.DataFrame:
    """Continental EFF/36 by competition and season: arrivals, and all players."""
    arrivals = features.loc[features.feature_eligible & features.season_dest.ge(2017)]
    a = (
        arrivals.groupby(["league_dest", "season_dest"])[OUTCOME]
        .agg(arrivals="size", arrivals_mean_eff36="mean")
        .reset_index()
        .rename(columns={"league_dest": "competition", "season_dest": "season"})
    )
    q = agg.loc[
        agg.league.isin(surv.blf.CONTINENTAL)
        & (agg.games >= surv.holdout.MIN_GAMES)
        & (agg.minutes > 0)
        & agg.season.ge(2017)
    ]
    q = q.assign(rate=36.0 * q.pir / q.minutes)
    b = (
        q.groupby(["league", "season"])["rate"]
        .agg(player_seasons="size", all_players_mean_eff36="mean")
        .reset_index()
        .rename(columns={"league": "competition"})
    )
    out = a.merge(b, on=["competition", "season"], how="outer", validate="1:1")
    out = out.sort_values(["competition", "season"]).reset_index(drop=True)
    # The level a walk-forward refit learned: arrivals of all earlier seasons.
    learned, learned_all = [], []
    for row in out.itertuples():
        earlier = arrivals.loc[
            arrivals.league_dest.eq(row.competition)
            & arrivals.season_dest.lt(row.season)
        ]
        learned.append(float(earlier[OUTCOME].mean()) if len(earlier) else math.nan)
        prev = q.loc[q.league.eq(row.competition) & q.season.lt(row.season)]
        learned_all.append(float(prev.rate.mean()) if len(prev) else math.nan)
    out["arrivals_mean_earlier_seasons"] = learned
    out["arrivals_minus_earlier"] = (
        out.arrivals_mean_eff36 - out.arrivals_mean_earlier_seasons
    )
    out["all_players_mean_earlier_seasons"] = learned_all
    out["all_players_minus_earlier"] = (
        out.all_players_mean_eff36 - out.all_players_mean_earlier_seasons
    )
    return out


# -------------------------------------------------------------------- E19 --
def fold_coefficients(fold: dict, arm: str = O) -> dict:
    info = fold["arms"][arm]
    return dict(zip(info["features"], info["coefficients"]))


def equivalent(coefs: dict, league: str, destination: str) -> float:
    """a1.equivalent_rate, NaN when the league is absent from the fit."""
    if f"source_offset:{league}" not in coefs:
        return math.nan
    return a1.equivalent_rate(coefs, league, destination)


def e19(features: pd.DataFrame, folds: list, full_coefs: dict, leagues: list) -> dict:
    eligible = features.loc[features.feature_eligible]
    fits = []
    for fold in folds:
        season = int(fold["season"])
        train = eligible.loc[eligible.season_dest.lt(season)]
        if len(train) != len(fold["train_keys"]):
            raise GateFailure(
                f"E19: training rows differ from the fold's keys ({season})"
            )
        fits.append(
            {
                "fit": f"refit for {season}",
                "season": season,
                "coefs": fold_coefficients(fold),
                "counts": train.league_src.value_counts().to_dict(),
                "training": len(train),
            }
        )
    full_train = dec.e9_training(features)
    full = {
        "fit": "full fit through 2025",
        "season": None,
        "coefs": full_coefs,
        "counts": full_train.league_src.value_counts().to_dict(),
        "training": len(full_train),
    }
    rows = []
    for f in [*fits, full]:
        for dest in dec.DESTINATIONS:
            for league in leagues:
                n = int(f["counts"].get(league, 0))
                rows.append(
                    {
                        "fit": f["fit"],
                        "refit_season": f["season"],
                        "training_forecasts": f["training"],
                        "destination": dest,
                        "source_league": league,
                        "training_arrivals_from_league": n,
                        "thin": bool(n < THIN_TRAINING),
                        "acb16_equivalent_eff36": equivalent(f["coefs"], league, dest),
                    }
                )
    table = pd.DataFrame(rows)
    refits = table.loc[table.refit_season.notna()]
    stability, changes = [], []
    for (dest, league), g in refits.groupby(["destination", "source_league"]):
        g = g.sort_values("refit_season")
        v = g.acb16_equivalent_eff36.to_numpy(float)
        step = np.abs(np.diff(v))
        full_value = float(
            table.loc[
                table.refit_season.isna()
                & table.destination.eq(dest)
                & table.source_league.eq(league),
                "acb16_equivalent_eff36",
            ].iloc[0]
        )
        stability.append(
            {
                "destination": dest,
                "source_league": league,
                "full_fit": full_value,
                "lowest_refit": float(np.nanmin(v)),
                "highest_refit": float(np.nanmax(v)),
                "range": float(np.nanmax(v) - np.nanmin(v)),
                "largest_consecutive_change": float(np.nanmax(step)),
                "refits_with_thin_training": int(g.thin.sum()),
            }
        )
        if league != a1.REFERENCE_LEAGUE:
            changes.extend(step[np.isfinite(step)].tolist())
    checks = []
    for fold in fits:
        for dest in dec.DESTINATIONS:
            for low in TIER1:
                for high in TIER3:
                    a = equivalent(fold["coefs"], low, dest)
                    b = equivalent(fold["coefs"], high, dest)
                    thin = (
                        fold["counts"].get(low, 0) < THIN_TRAINING
                        or fold["counts"].get(high, 0) < THIN_TRAINING
                    )
                    checks.append(
                        {
                            "refit_season": fold["season"],
                            "destination": dest,
                            "tier1_league": low,
                            "tier3_league": high,
                            "tier1_equivalent": a,
                            "tier3_equivalent": b,
                            "tier3_higher": bool(b > a),
                            "thin_cell": bool(thin),
                        }
                    )
    checks = pd.DataFrame(checks)
    if len(checks) != EXPECTED_TIER_COMPARISONS:
        raise GateFailure(f"E19: {len(checks)} tier comparisons (expected 144)")
    held = int(checks.tier3_higher.sum())
    solid = checks.loc[~checks.thin_cell]
    summary = {
        "comparisons": int(len(checks)),
        "tier3_higher": held,
        "comparisons_without_thin_cells": int(len(solid)),
        "tier3_higher_without_thin_cells": int(solid.tier3_higher.sum()),
        "median_consecutive_change": float(np.median(changes)),
        "max_consecutive_change": float(np.max(changes)),
        "failures": checks.loc[~checks.tier3_higher]
        .drop(columns=["tier3_higher"])
        .to_dict(orient="records"),
        "note": "refits share most of their training data: this describes stability and is not a test",
    }
    summary["sentence"] = (
        "In every yearly refit, every tier-3 league needed a higher domestic rate than every tier-1 league."
        if held == len(checks)
        else f"Tier 3 stayed above tier 1 in {held} of {len(checks)} comparisons."
    )
    summary["movement_sentence"] = (
        "From one summer to the next a league's equivalent moved by a median of "
        f"{summary['median_consecutive_change']:.2f} EFF/36 (at most {summary['max_consecutive_change']:.2f})."
    )
    return {
        "table": table,
        "stability": pd.DataFrame(stability),
        "checks": checks,
        "summary": summary,
    }


def g19_differences(
    result: dict, folds: list, exchange: pd.DataFrame, e12: pd.DataFrame, shift: int = 0
) -> dict:
    """Full-fit equivalents equal the published table; refit flags equal E12's."""
    full = result["table"].loc[result["table"].refit_season.isna()]
    m = full.merge(
        exchange,
        on=["destination", "source_league"],
        suffixes=("", "_published"),
        validate="1:1",
    )
    if len(m) != len(exchange):
        return {"rows": math.inf}
    worst = {
        "equivalents": max_abs(
            m.acb16_equivalent_eff36, m.acb16_equivalent_eff36_published
        )
    }
    recorded = e12.loc[e12.arm.eq(O) & e12.scope.eq("walk-forward refit")]
    recorded = dict(zip(recorded.season.astype(int), recorded.beta_a))
    gaps = []
    for fold in folds:
        season = int(fold["season"]) + shift
        if season not in recorded:
            continue
        gaps.append(abs(fold_coefficients(fold)[FLAG] - recorded[season]))
    worst["refit_flag_coefficients"] = max(gaps) if gaps else math.inf
    return worst


# ------------------------------------------------------------- E20 and E21 --
def gap_counts(y, preds, origin, src) -> dict:
    """Within-pool pair counts by forecast-gap bin, and the H -> O flip counts."""
    i, j = np.triu_indices(len(y), 1)
    keep = origin[i] != origin[j]
    i, j = i[keep], j[keep]
    cross = src[i] != src[j]
    dy = np.sign(y[i] - y[j])
    unequal = dy != 0
    masks = {"all": np.ones(len(i), bool), "cross": cross, "same": ~cross}
    out = {}
    signs, good = {}, {}
    for arm, p in preds.items():
        diff = p[i] - p[j]
        signs[arm] = np.sign(diff)
        bins = np.digitize(np.abs(diff), BIN_EDGES[1:-1])
        good[arm] = np.where(signs[arm] == dy, 1.0, np.where(signs[arm] == 0, 0.5, 0.0))
        for kind in E20_KINDS:
            u = unequal & masks[kind]
            out[f"{kind}|unequal"] = int(u.sum())
            for k in range(len(BIN_LABELS)):
                sel = u & (bins == k)
                out[f"{kind}|pairs:{arm}:{k}"] = int(sel.sum())
                out[f"{kind}|correct:{arm}:{k}"] = float(good[arm][sel].sum())
    for kind in E21_KINDS:
        mask = masks[kind]
        flip = (signs[H] * signs[O] < 0) & mask
        out[f"{kind}|e21_pairs"] = int(mask.sum())
        out[f"{kind}|e21_unequal"] = int((unequal & mask).sum())
        out[f"{kind}|e21_flips"] = int(flip.sum())
        out[f"{kind}|e21_flips_unequal"] = int((flip & unequal).sum())
        out[f"{kind}|e21_right"] = int((flip & unequal & (signs[O] == dy)).sum())
        for arm in (H, O):
            out[f"{kind}|e21_ties:{arm}"] = int(((signs[arm] == 0) & mask).sum())
    return out


def pav(values, weights) -> list:
    """Weighted pool-adjacent-violators fit, non-decreasing."""
    blocks = [[float(v), float(w), 1] for v, w in zip(values, weights)]
    k = 0
    while k < len(blocks) - 1:
        if blocks[k][0] > blocks[k + 1][0] + 1e-15:
            v0, w0, n0 = blocks[k]
            v1, w1, n1 = blocks[k + 1]
            blocks[k : k + 2] = [[(v0 * w0 + v1 * w1) / (w0 + w1), w0 + w1, n0 + n1]]
            k = max(k - 1, 0)
        else:
            k += 1
    out = []
    for v, _, n in blocks:
        out.extend([v] * n)
    return out


def e20_e21(rows: pd.DataFrame, *, n_boot=N_BOOT, seed=SEED) -> dict:
    """E20 bins and E21 flips on the E7/E10 bootstrap (same generator and order)."""
    data = []
    for _, frame in dec.pools(rows):
        data.append(
            {
                "y": frame[OUTCOME].to_numpy(float),
                "p": {arm: frame[arm].to_numpy(float) for arm in ARMS},
                "src": frame.league_src.to_numpy(object),
                "groups": dec.cluster_index(frame),
                "n": len(frame),
            }
        )

    def evaluate(index_sets) -> dict:
        total: dict = {}
        for d, idx in zip(data, index_sets):
            c = gap_counts(
                d["y"][idx], {a: p[idx] for a, p in d["p"].items()}, idx, d["src"][idx]
            )
            for name, value in c.items():
                total[name] = total.get(name, 0.0) + value
        return total

    point = evaluate([np.arange(d["n"]) for d in data])
    rng = np.random.default_rng(seed)
    draws = [
        evaluate([dec.cluster_draw(d["groups"], rng) for d in data])
        for _ in range(n_boot)
    ]

    bins = []
    for kind in E20_KINDS:
        for arm in ARMS:
            block = []
            for k, label in enumerate(BIN_LABELS):
                pairs = point[f"{kind}|pairs:{arm}:{k}"]
                d = np.array(
                    [
                        ratio(
                            x[f"{kind}|correct:{arm}:{k}"], x[f"{kind}|pairs:{arm}:{k}"]
                        )
                        for x in draws
                    ]
                )
                lo, hi = interval(d)
                block.append(
                    {
                        "pair_type": kind,
                        "arm": arm,
                        "label": LABELS[arm],
                        "bin": k,
                        "gap_eff36": label,
                        "gap_low": BIN_EDGES[k],
                        "gap_high": BIN_EDGES[k + 1],
                        "pairs": int(pairs),
                        "share_correct": ratio(
                            point[f"{kind}|correct:{arm}:{k}"], pairs
                        ),
                        "ci95_low": lo,
                        "ci95_high": hi,
                    }
                )
            fitted = pav(
                [r["share_correct"] for r in block], [r["pairs"] for r in block]
            )
            for row, value in zip(block, fitted):
                row["share_correct_monotone"] = value
            bins.extend(block)
    bins = pd.DataFrame(bins)

    flips = []
    for kind in E21_KINDS:
        d_flip = np.array(
            [ratio(x[f"{kind}|e21_flips"], x[f"{kind}|e21_pairs"]) for x in draws]
        )
        d_right = np.array(
            [
                ratio(x[f"{kind}|e21_right"], x[f"{kind}|e21_flips_unequal"])
                for x in draws
            ]
        )
        flips.append(
            {
                "pair_type": kind,
                "pairs": int(point[f"{kind}|e21_pairs"]),
                "unequal_pairs": int(point[f"{kind}|e21_unequal"]),
                "flips": int(point[f"{kind}|e21_flips"]),
                "flips_unequal": int(point[f"{kind}|e21_flips_unequal"]),
                "right": int(point[f"{kind}|e21_right"]),
                "flip_share": ratio(
                    point[f"{kind}|e21_flips"], point[f"{kind}|e21_pairs"]
                ),
                "flip_share_ci95_low": interval(d_flip)[0],
                "flip_share_ci95_high": interval(d_flip)[1],
                "right_share": ratio(
                    point[f"{kind}|e21_right"], point[f"{kind}|e21_flips_unequal"]
                ),
                "right_share_ci95_low": interval(d_right)[0],
                "right_share_ci95_high": interval(d_right)[1],
                "right_share_mde_80": power_line(d_right)["mde_80"],
                "gain_from_counts": ratio(
                    2 * point[f"{kind}|e21_right"] - point[f"{kind}|e21_flips_unequal"],
                    point[f"{kind}|e21_unequal"],
                ),
                "ties_history": int(point[f"{kind}|e21_ties:{H}"]),
                "ties_offsets": int(point[f"{kind}|e21_ties:{O}"]),
            }
        )
    flips = pd.DataFrame(flips)
    return {
        "bins": bins,
        "flips": flips,
        "point": point,
        "e20_licence": e20_licence(bins),
        "e21_licence": e21_licence(flips),
    }


def e20_licence(bins: pd.DataFrame) -> dict:
    primary = bins.loc[bins.pair_type.eq("all") & bins.arm.eq(O)].sort_values("bin")
    sentences = []
    for r in primary.itertuples():
        span = (
            f"by {r.gap_low:g} to {r.gap_high:g} EFF/36"
            if math.isfinite(r.gap_high)
            else f"by {r.gap_low:g} EFF/36 or more"
        )
        sentences.append(
            f"When two candidates' forecasts differed {span}, the higher-forecast player turned out better in {100 * r.share_correct:.1f}% of pairs."
        )
    first = primary.iloc[0]
    coin = bool(first.ci95_low <= 0.5 <= first.ci95_high)
    out = {
        "bin_sentences": sentences,
        "coin_flip_below_1": {
            "licensed": coin,
            "sentence": (
                "A forecast gap below 1 EFF/36 is not distinguishable from a coin flip."
                if coin
                else f"Even forecast gaps below 1 EFF/36 were right more often than a coin flip ({100 * first.share_correct:.1f}%)."
            ),
        },
        "trust": {},
    }
    lows = primary.ci95_low.to_numpy(float)
    for level in TRUST_LEVELS:
        start = None
        for k in range(len(lows)):
            if (lows[k:] >= level).all():
                start = k
                break
        if start is None:
            out["trust"][f"{level:.2f}"] = {
                "licensed": False,
                "sentence": f"No gap bin was right at least {100 * level:.0f}% of the time with its interval's lower bound.",
            }
        else:
            out["trust"][f"{level:.2f}"] = {
                "licensed": True,
                "from_gap": BIN_EDGES[start],
                "sentence": f"Forecast gaps of at least {BIN_EDGES[start]:g} EFF/36 were right at least {100 * level:.0f}% of the time.",
            }
    return out


def e21_licence(flips: pd.DataFrame) -> dict:
    row = flips.loc[flips.pair_type.eq("cross")].iloc[0]
    above = bool(row.right_share_ci95_low > 0.5)
    return {
        "licensed": above,
        "sentence": (
            f"The league table changes {100 * row.flip_share:.1f}% of cross-league comparisons and is right on {100 * row.right_share:.1f}% of them."
            if above
            else "The league table's ranking changes are not distinguishable from a coin flip at this n."
        ),
        "note": "E21 re-expresses E10's gain (gain = flip share x (2 x right share - 1)); it adds no new evidence",
    }


def g20_differences(result: dict, e10_pooled: dict, drop_bin=None) -> dict:
    """Bins partition the pairs; accuracy pooled over bins equals the registered D1."""
    point = result["point"]
    worst = {}
    for kind in E20_KINDS:
        registered = e10_pooled["all_pools"][kind]
        for arm in ARMS:
            ks = [k for k in range(len(BIN_LABELS)) if k != drop_bin]
            pairs = sum(point[f"{kind}|pairs:{arm}:{k}"] for k in ks)
            correct = sum(point[f"{kind}|correct:{arm}:{k}"] for k in ks)
            worst[f"partition:{kind}:{arm}"] = abs(pairs - registered["unequal_pairs"])
            worst[f"accuracy:{kind}:{arm}"] = abs(
                ratio(correct, pairs) - registered["values"][f"d1:{arm}"]["point"]
            )
    worst["expected_pairs"] = abs(
        e10_pooled["all_pools"]["all"]["unequal_pairs"] - EXPECTED_PAIRS
    )
    return worst


def g21_differences(result: dict, e10_pooled: dict, arm_pair=(H, O)) -> dict:
    """(2 right - flips) / unequal equals the registered E10 gain, per pair type."""
    worst = {}
    name = f"d1diff:{a1.tag(*arm_pair)}"
    for row in result["flips"].itertuples():
        if row.ties_history or row.ties_offsets:
            return {"ties": math.inf}
        registered = e10_pooled["all_pools"][row.pair_type]["values"][name]["point"]
        worst[row.pair_type] = abs(row.gain_from_counts - registered)
    return worst


# -------------------------------------------------------------------- E22 --
def wilson(k: int, n: int, z: float = WILSON_Z) -> list:
    if n <= 0:
        return [math.nan, math.nan]
    p = k / n
    centre = (p + z * z / (2 * n)) / (1 + z * z / n)
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return [max(0.0, centre - half), min(1.0, centre + half)]


def e22(rows: pd.DataFrame, leagues: list) -> dict:
    tables, pooled, seasons = [], {}, {}
    for level in E22_LEVELS:
        test, _ = dec.conformal_rows(rows, O, level)
        test = test.merge(
            rows[KEY + ["league_src"]], on=KEY, how="left", validate="1:1"
        )
        if test.league_src.isna().any():
            raise GateFailure("E22: a banded forecast has no source league")
        pooled[f"{level:.2f}"] = {
            "n": int(len(test)),
            "hits": int(test.hit.sum()),
            "coverage": float(test.hit.mean()),
        }
        seasons[f"{level:.2f}"] = {
            str(int(s)): {"n": int(len(g)), "coverage": float(g.hit.mean())}
            for s, g in test.groupby("season_dest")
        }
        for league in leagues:
            g = test.loc[test.league_src.eq(league)]
            lo, hi = wilson(int(g.hit.sum()), len(g))
            tables.append(
                {
                    "level": level,
                    "source_league": league,
                    "n": int(len(g)),
                    "hits": int(g.hit.sum()),
                    "coverage": float(g.hit.mean()) if len(g) else math.nan,
                    "wilson95_low": lo,
                    "wilson95_high": hi,
                    "interval_excludes_nominal": bool(not (lo <= level <= hi)),
                }
            )
    table = pd.DataFrame(tables)
    primary = table.loc[np.isclose(table.level, 0.80)]
    off = primary.loc[primary.interval_excludes_nominal]
    licence = {
        "range_sentence": (
            f"By source league, the 80% bands contained between {100 * primary.coverage.min():.1f}% and {100 * primary.coverage.max():.1f}% of arrivals."
        ),
        "leagues_off_nominal": off.source_league.tolist(),
        "sentence": (
            f"No league's coverage was distinguishable from 80% at these sample sizes (n from {int(primary.n.min())} to {int(primary.n.max())})."
            if off.empty
            else "Coverage was distinguishable from 80% for: "
            + ", ".join(
                f"{r.source_league} ({100 * r.coverage:.1f}%, n = {r.n})"
                for r in off.itertuples()
            )
            + "."
        ),
    }
    return {"table": table, "pooled": pooled, "by_season": seasons, "licence": licence}


def g22_differences(result: dict, e8_table: pd.DataFrame, drop=None) -> dict:
    """Coverage pooled over leagues equals the registered E8 pooled coverage."""
    worst = {}
    for level in E22_LEVELS:
        t = result["table"].loc[np.isclose(result["table"].level, level)]
        if drop is not None:
            t = t.loc[t.source_league != drop]
        theirs = e8_table.loc[
            e8_table.arm.eq(O)
            & np.isclose(e8_table.level, level)
            & e8_table.scope.eq("pooled")
        ]
        if len(theirs) != 1:
            return {"e8_rows": math.inf}
        worst[f"coverage:{level:.2f}"] = abs(
            t.hits.sum() / t.n.sum() - float(theirs.coverage.iloc[0])
        )
        worst[f"n:{level:.2f}"] = float(abs(t.n.sum() - int(theirs.n.iloc[0])))
    return worst


# -------------------------------------------------------------------- E23 --
def jump(frame: pd.DataFrame) -> np.ndarray:
    """u = max(0, source rate - earlier career rate); 0 for players with no history."""
    x = frame.pir_per36_src.to_numpy(float)
    h = frame.prior_mean_pir36.to_numpy(float)
    return np.where(np.isnan(h), 0.0, np.maximum(0.0, x - h))


def assert_jump_matches_flag(frame: pd.DataFrame, shift: float = 0.0) -> int:
    """The registered flag equals 1 exactly when the jump is positive."""
    flag = frame.above_own_prior.fillna(0).to_numpy(bool)
    positive = (jump(frame) + shift) > 0
    wrong = int(np.sum(flag != positive))
    if wrong:
        raise GateFailure(f"jump gate: flag and jump disagree on {wrong} rows")
    return wrong


def variant_design(frame: pd.DataFrame, variant: str, categories: list, flag=True):
    """The offsets l10 design with the history terms of `variant`."""
    x, names = benchmark.model_matrix(frame, O)
    names = list(names)
    at = names.index(FLAG)
    u = jump(frame)
    if variant == "M1":
        x = np.column_stack([x[:, : at + 1], u, x[:, at + 1 :]])
        names = [*names[: at + 1], JUMP, *names[at + 1 :]]
    elif variant == "M2":
        x = np.column_stack([x[:, :at], u, x[:, at + 1 :]])
        names = [*names[:at], JUMP, *names[at + 1 :]]
    elif variant != "M0":
        raise ValueError(f"unknown variant: {variant}")
    if not flag and FLAG in names:  # negative control only
        keep = [k for k, n in enumerate(names) if n != FLAG]
        x, names = x[:, keep], [names[k] for k in keep]
    dummies = np.column_stack([frame.league_src.eq(c) for c in categories]).astype(
        float
    )
    return np.column_stack([x, dummies]), [
        *names,
        *[f"source_offset:{c}" for c in categories],
    ]


def variant_fit(train: pd.DataFrame, variant: str, flag=True) -> dict:
    """benchmark.fit_model's ridge (only the source offsets are penalised)."""
    categories = sorted(train.league_src.unique())
    x, names = variant_design(train, variant, categories, flag=flag)
    base = x.shape[1] - len(categories)
    if np.linalg.matrix_rank(x[:, :base]) != base:
        raise GateFailure(f"E23 {variant}: unpenalised design is rank deficient")
    regulariser = np.zeros((len(categories), x.shape[1]))
    regulariser[:, base:] = np.sqrt(RIDGE_PENALTY) * np.eye(len(categories))
    beta = np.linalg.lstsq(
        np.vstack([x, regulariser]),
        np.r_[train[OUTCOME].to_numpy(float), np.zeros(len(categories))],
        rcond=None,
    )[0]
    return {"names": names, "beta": beta, "categories": categories, "flag": flag}


def variant_predict(fit: dict, frame: pd.DataFrame, variant: str) -> np.ndarray:
    x, names = variant_design(frame, variant, fit["categories"], flag=fit["flag"])
    if names != fit["names"]:
        raise GateFailure("E23: prediction design differs from the fit")
    return x @ fit["beta"]


def walk_forward(features: pd.DataFrame, rows: pd.DataFrame, folds: list, flag=True):
    """Every anchor forecast under M0, M1 and M2, refitted on earlier seasons only."""
    eligible = features.loc[features.feature_eligible]
    out = pd.DataFrame(
        {v: np.full(len(rows), np.nan) for v in VARIANTS}, index=rows.index
    )
    coefs = []
    for fold in folds:
        season = int(fold["season"])
        train = eligible.loc[eligible.season_dest.lt(season)].sort_values(KEY)
        if len(train) != len(fold["train_keys"]):
            raise GateFailure(
                f"E23: training rows differ from the fold's keys ({season})"
            )
        test = rows.loc[rows.season_dest.eq(season)]
        record = {"season": season, "training_forecasts": len(train)}
        for v in VARIANTS:
            fit = variant_fit(train, v, flag=flag)
            out.loc[test.index, v] = variant_predict(fit, test, v)
            c = dict(zip(fit["names"], fit["beta"]))
            record[f"{v}_flag"] = float(c.get(FLAG, math.nan))
            record[f"{v}_jump"] = float(c.get(JUMP, math.nan))
        coefs.append(record)
    if out.isna().any().any():
        raise GateFailure("E23: an anchor forecast was not produced")
    return out, coefs


def g23_differences(
    features: pd.DataFrame, rows: pd.DataFrame, folds: list, e9_coefs: dict, flag=True
) -> dict:
    """M0 reproduces the e9 full-fit coefficients and every anchor forecast."""
    train = dec.e9_training(features)
    fit = variant_fit(train, "M0", flag=flag)
    mine = dict(zip(fit["names"], fit["beta"]))
    if set(mine) != set(e9_coefs):
        coefficient_gap = math.inf
    else:
        coefficient_gap = max(abs(mine[k] - e9_coefs[k]) for k in e9_coefs)
    forecasts, _ = walk_forward(features, rows, folds, flag=flag)
    return {
        "coefficients": coefficient_gap,
        "anchor_forecasts": max_abs(forecasts["M0"], rows[O]),
        "mae": abs(
            float(np.mean(np.abs(forecasts["M0"] - rows[OUTCOME])))
            - common.mae(rows, O)
        ),
    }


def e23a(features, rows, folds, *, n_boot=N_BOOT, seed=SEED):
    train = dec.e9_training(features)
    point = {v: variant_fit(train, v) for v in VARIANTS}
    coefs = {
        v: {k: float(b) for k, b in zip(point[v]["names"], point[v]["beta"])}
        for v in VARIANTS
    }
    groups = dec.cluster_index(train)
    rng = np.random.default_rng(seed)
    draws = {"M1_jump": [], "M1_flag": [], "M2_jump": []}
    with_history = train.prior_mean_pir36.notna().to_numpy()
    flagged = train.above_own_prior.fillna(0).to_numpy(bool)
    share_draws = []
    for _ in range(n_boot):
        idx = dec.cluster_draw(groups, rng)
        sample = train.iloc[idx]
        for v in ("M1", "M2"):
            fit = variant_fit(sample, v)
            c = dict(zip(fit["names"], fit["beta"]))
            draws[f"{v}_jump"].append(float(c[JUMP]))
            if v == "M1":
                draws["M1_flag"].append(float(c[FLAG]))
        share_draws.append(
            ratio(flagged[idx][with_history[idx]].sum(), with_history[idx].sum())
        )
    forecasts, refits = walk_forward(features, rows, folds)
    scored = rows.copy()
    for v, column in E23_COLUMNS.items():
        scored[column] = forecasts[v].to_numpy(float)
    contrasts = {}
    for v, column in E23_COLUMNS.items():
        block = recipes.contrast_summary(scored, O, column)
        contrasts[v] = {
            "mae_m0": common.mae(scored, O),
            "mae_variant": common.mae(scored, column),
            "difference_positive_favours_variant": block["player_club_season"][
                "difference"
            ],
            "ci95": block["player_club_season"]["ci95"],
            "seasons_favouring_variant": block["seasons_favouring_right"],
        }
    u = jump(train)
    out = {
        "training_forecasts": int(len(train)),
        "jump_among_flagged": {
            "n": int((u > 0).sum()),
            "median": float(np.median(u[u > 0])),
            "p90": float(np.percentile(u[u > 0], 90)),
        },
        "M0": {"flag": coefs["M0"][FLAG]},
        "M1": {
            "jump": coefs["M1"][JUMP],
            "jump_ci95": interval(draws["M1_jump"]),
            **{f"jump_{k}": v for k, v in power_line(draws["M1_jump"]).items()},
            "flag": coefs["M1"][FLAG],
            "flag_ci95": interval(draws["M1_flag"]),
            "walk_forward_jump": [r["M1_jump"] for r in refits],
            "walk_forward_flag": [r["M1_flag"] for r in refits],
        },
        "M2": {
            "jump": coefs["M2"][JUMP],
            "jump_ci95": interval(draws["M2_jump"]),
            "walk_forward_jump": [r["M2_jump"] for r in refits],
        },
        "refits": refits,
        "walk_forward_contrasts": contrasts,
        "coefficients_full_fit": coefs,
        "note": "M0 stays the league-aware model; M1 and M2 are sensitivity checks and are not adopted",
    }
    negative = sum(1 for x in out["M1"]["walk_forward_jump"] if x < 0)
    out["M1"]["walk_forward_negative"] = int(negative)
    licensed = bool(out["M1"]["jump_ci95"][1] < 0 and negative == len(refits))
    out["licence"] = {
        "licensed": licensed,
        "sentence": (
            f"The discount grows by {abs(out['M1']['jump']):.2f} EFF/36 for each point above his history."
            if licensed
            else "The data do not show the discount growing with the size of the jump."
        ),
    }
    arrivals_share = {
        "with_history": int(with_history.sum()),
        "flagged": int(flagged[with_history].sum()),
        "share": ratio(flagged[with_history].sum(), with_history.sum()),
        "ci95": interval(share_draws),
    }
    return out, arrivals_share, np.asarray(share_draws, float)


def domestic_population(agg: pd.DataFrame, leagues: list) -> pd.DataFrame:
    """One row per player-season: the largest-minutes qualified domestic stint, with v10's prior."""
    q = agg.loc[
        agg.league.isin(leagues)
        & (agg.games >= surv.holdout.MIN_GAMES)
        & (agg.minutes > 0)
    ]
    q = q.sort_values("minutes", ascending=False).drop_duplicates(
        ["player_name", "season"]
    )
    prior = surv.pooled_prior(agg, "pir", "minutes", 36.0)
    q = q.merge(prior, on=["player_name", "season"], how="left", validate="1:1")
    q = q.assign(rate=36.0 * q.pir / q.minutes)
    q["has_history"] = q.prior.notna()
    q["flag"] = q.has_history & (q.rate > q.prior)
    return q.reset_index(drop=True)


def arrival_match(train: pd.DataFrame, population: pd.DataFrame) -> dict:
    """Training arrivals found in the population with the same rate and flag."""
    left = train.assign(season=train.season_dest - 1)[
        ["player_name", "season", "league_src", "pir_per36_src", "above_own_prior"]
    ]
    m = left.merge(population, on=["player_name", "season"], how="left", validate="1:1")
    found = m.rate.notna()
    same_league = found & m.league.eq(m.league_src)
    rate_gap = max_abs(m.loc[same_league, "rate"], m.loc[same_league, "pir_per36_src"])
    flag_wrong = int(
        (
            m.loc[same_league, "flag"].to_numpy(bool)
            != m.loc[same_league, "above_own_prior"].fillna(0).to_numpy(bool)
        ).sum()
    )
    return {
        "training_arrivals": int(len(train)),
        "found_in_population": int(found.sum()),
        "same_source_league": int(same_league.sum()),
        "max_rate_difference": rate_gap,
        "flag_disagreements": flag_wrong,
    }


def assert_arrival_match(match: dict, min_share: float = 0.99) -> dict:
    share = match["same_source_league"] / match["training_arrivals"]
    if share < min_share:
        raise GateFailure(f"E23b: only {share:.3f} of arrivals matched the population")
    if match["max_rate_difference"] > REPRO_TOLERANCE or match["flag_disagreements"]:
        raise GateFailure("E23b: matched arrivals differ in rate or flag")
    return {**match, "matched_share": share}


def e23b(
    train, population, arrivals_share, share_draws, *, n_boot=N_BOOT, seed=SEED
) -> dict:
    seasons = sorted(
        set((train.loc[train.prior_mean_pir36.notna(), "season_dest"] - 1).astype(int))
    )
    pop = population.loc[population.season.isin(seasons) & population.has_history]
    codes, players = pd.factorize(pop.player_name, sort=True)
    flag = pop.flag.to_numpy(float)
    flag_sum = np.bincount(codes, weights=flag, minlength=len(players))
    count = np.bincount(codes, minlength=len(players)).astype(float)
    # A separate generator: the arrival draws above stay the e9 stream.
    rng = np.random.default_rng(seed + 1)
    pop_draws = np.empty(n_boot)
    for b in range(n_boot):
        pick = rng.integers(0, len(players), len(players))
        pop_draws[b] = flag_sum[pick].sum() / count[pick].sum()
    share = float(flag.mean())
    lo, hi = interval(share_draws - pop_draws)
    by_season = (
        pop.groupby("season")["flag"]
        .agg(player_seasons="size", share_flagged="mean")
        .reset_index()
    )
    out = {
        "arrivals": arrivals_share,
        "population": {
            "source_seasons": seasons,
            "player_seasons_with_history": int(len(pop)),
            "players": int(len(players)),
            "share": share,
            "ci95": interval(pop_draws),
            "resampling": "players with replacement (a player contributes several seasons), generator seed + 1",
        },
        "difference_arrivals_minus_population": {
            "point": arrivals_share["share"] - share,
            "ci95": [lo, hi],
        },
        "by_season": by_season.to_dict(orient="records"),
    }
    licensed = bool(lo > 0)
    out["licence"] = {
        "licensed": licensed,
        "sentence": (
            f"{100 * arrivals_share['share']:.0f}% of signings followed an above-average season, against {100 * share:.0f}% of all comparable domestic player-seasons."
            if licensed
            else f"{100 * arrivals_share['share']:.0f}% of signings with a history followed an above-average season; this is not distinguishable from the share among all comparable domestic player-seasons at this n."
        ),
    }
    return out


# -------------------------------------------------------------------- run --
def run(
    root: Path,
    input_dir: Path,
    prior_dir: Path,
    raw_root: Path,
    out: Path,
    n_boot=N_BOOT,
):
    root = Path(root)
    prior = load_prior(prior_dir)
    v9, v10_summary = common.load_references(root)
    rows, features, folds = common.anchor_rows(root, input_dir)
    gates = {}

    diffs = common.g0_differences(rows, v9, v10_summary)
    g0_control = negative_control(common.assert_g0, diffs, tolerance=-1.0)
    common.assert_g0(diffs)
    gates["G0"] = passed(max(diffs.values()), g0_control, tolerance=common.G0_TOLERANCE)
    gates["scope"] = {
        "status": "passed",
        **dec.assert_scope(rows),
        "negative_control": negative_control(
            dec.assert_scope, rows, expected_targets=dec.EXPECTED_TARGETS + 1
        ),
    }
    keyed = prior["decide-02/e7_keyed_forecasts.csv"]
    r_rows = prior["recipes-01/rows_pool_A.parquet"]
    worst = a1.reproduction_difference(rows, keyed, r_rows.loc[r_rows.recipe.eq("R1")])
    gates["reproduction"] = passed(
        gate_max("reproduction gate", worst, REPRO_TOLERANCE),
        negative_control(gate_max, "reproduction gate", worst, -1.0),
        tolerance=REPRO_TOLERANCE,
    )
    leagues = a1.assert_leagues(rows)
    a1_summary = prior["amend1-decisions-01/summary.json"]
    e10_pooled = a1_summary["e10"]["pooled"]

    # ---- E18
    eighteen = e18(rows, leagues, n_boot=n_boot)
    e11_table = prior["amend1-decisions-01/e11_signed_error_by_league.csv"]
    same_draws = n_boot == a1.N_BOOT
    w18 = g18_differences(eighteen, e11_table, check_intervals=same_draws)
    control = g18_differences(eighteen, e11_table, drop=leagues[0])
    gates["G18"] = passed(
        gate_max("G18", w18, REPRO_TOLERANCE),
        negative_control(gate_max, "G18", control, REPRO_TOLERANCE),
        checked=sorted(w18),
        e11_intervals_checked=bool(same_draws),
    )
    _, agg, rebuild = robust.rebuild_games(raw_root)
    _, cohort = common.load_pool(input_dir, "official_corrected")
    prior_diff = surv.prior_rule_difference(cohort, agg)
    surv.assert_prior_rule(prior_diff)
    gates["prior_rule"] = {
        "status": "passed",
        "differences": prior_diff,
        "negative_control": negative_control(
            surv.assert_prior_rule, prior_diff, tolerance=-1.0
        ),
    }
    drift = e18c(features, agg)

    # ---- E19
    full_coefs = a1_summary["e12"]["arms"][O]["coefficients_full_fit"]
    nineteen = e19(features, folds, full_coefs, leagues)
    exchange = prior["amend1-decisions-01/exchange_rate_acb16.csv"]
    e12_table = prior["amend1-decisions-01/e12_career_year.csv"]
    w19 = g19_differences(nineteen, folds, exchange, e12_table)
    control = g19_differences(nineteen, folds, exchange, e12_table, shift=1)
    gates["G19"] = passed(
        gate_max("G19", w19, REPRO_TOLERANCE),
        negative_control(gate_max, "G19", control, REPRO_TOLERANCE),
        checked=sorted(w19),
    )
    tiers = prior["decide-02/e9_league_tiers_full.csv"]
    tier_of = dict(zip(tiers.league_src, tiers.tier))
    tier1 = sorted(name for name, t in tier_of.items() if t == 1)
    tier3 = sorted(name for name, t in tier_of.items() if t == 3)
    if tier1 != sorted(TIER1) or tier3 != sorted(TIER3):
        raise GateFailure("E19: registered tiers differ from the published table")
    gates["E19_tiers"] = {"status": "passed", "tier1": tier1, "tier3": tier3}

    # ---- E20 and E21
    twenty = e20_e21(rows, n_boot=n_boot)
    w20 = g20_differences(twenty, e10_pooled)
    control = g20_differences(twenty, e10_pooled, drop_bin=0)
    gates["G20"] = passed(
        gate_max("G20", w20, EXACT_TOLERANCE),
        negative_control(gate_max, "G20", control, EXACT_TOLERANCE),
    )
    w21 = g21_differences(twenty, e10_pooled)
    control = g21_differences(twenty, e10_pooled, arm_pair=(H, HT))
    gates["G21"] = passed(
        gate_max("G21", w21, EXACT_TOLERANCE),
        negative_control(gate_max, "G21", control, EXACT_TOLERANCE),
    )

    # ---- E22
    twentytwo = e22(rows, leagues)
    e8_table = prior["decide-02/e8_conformal.csv"]
    w22 = g22_differences(twentytwo, e8_table)
    control = g22_differences(twentytwo, e8_table, drop=leagues[0])
    gates["G22"] = passed(
        gate_max("G22", w22, EXACT_TOLERANCE),
        negative_control(gate_max, "G22", control, EXACT_TOLERANCE),
    )

    # ---- E23
    eligible = features.loc[features.feature_eligible]
    gates["E23_jump_matches_flag"] = {
        "status": "passed",
        "disagreements": assert_jump_matches_flag(eligible),
        "negative_control": negative_control(
            assert_jump_matches_flag, eligible, shift=1.0
        ),
    }
    w23 = g23_differences(features, rows, folds, full_coefs)
    control = g23_differences(features, rows, folds, full_coefs, flag=False)
    gates["G23"] = passed(
        gate_max("G23", w23, REPRO_TOLERANCE),
        negative_control(gate_max, "G23", control, REPRO_TOLERANCE),
        checked=sorted(w23),
    )
    twentythree, arrivals_share, share_draws = e23a(
        features, rows, folds, n_boot=n_boot
    )
    population = domestic_population(agg, leagues)
    train = dec.e9_training(features)
    match = arrival_match(train, population)
    gates["E23b_arrivals_in_population"] = {
        "status": "passed",
        **assert_arrival_match(match),
        "negative_control": negative_control(
            assert_arrival_match, match, min_share=1.01
        ),
    }
    share = e23b(train, population, arrivals_share, share_draws, n_boot=n_boot)

    out = Path(out)
    out.mkdir(parents=True, exist_ok=False)
    eighteen["level"].to_csv(out / "e18_level.csv", index=False)
    eighteen["leagues"].to_csv(out / "e18_league_rebased.csv", index=False)
    drift.to_csv(out / "e18_drift.csv", index=False)
    nineteen["table"].to_csv(out / "e19_equivalents_by_refit.csv", index=False)
    nineteen["stability"].to_csv(out / "e19_stability.csv", index=False)
    nineteen["checks"].to_csv(out / "e19_tier_check.csv", index=False)
    twenty["bins"].to_csv(out / "e20_gap_bins.csv", index=False)
    twenty["flips"].to_csv(out / "e21_league_table_flips.csv", index=False)
    twentytwo["table"].to_csv(out / "e22_coverage_by_league.csv", index=False)
    pd.DataFrame(twentythree["refits"]).to_csv(out / "e23_refits.csv", index=False)

    summary = {
        "analysis": "Amendment 3: E18-E23 (exploratory; destination seasons 2020-2025 already seen)",
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
        "exposure": EXPOSURE,
        "n_boot": n_boot,
        "seed": SEED,
        "n_targets": int(len(rows)),
        "models": {arm: LABELS[arm] for arm in ARMS},
        "gates": gates,
        "rebuild": rebuild,
        "e18": {
            "level": eighteen["level"].to_dict(orient="records"),
            "level_licence": eighteen["level_licence"],
            "leagues": eighteen["leagues"].to_dict(orient="records"),
            "holm_family": eighteen["holm_family"],
            "spread": eighteen["spread"],
            "spread_contrast": eighteen["spread_contrast"],
            "drift": drift.to_dict(orient="records"),
            "drift_note": "descriptive only; licenses no statement about cause",
        },
        "e19": {
            "summary": nineteen["summary"],
            "stability": nineteen["stability"].to_dict(orient="records"),
        },
        "e20": {
            "bins": twenty["bins"].to_dict(orient="records"),
            "licence": twenty["e20_licence"],
            "bin_edges": [b if math.isfinite(b) else None for b in BIN_EDGES],
        },
        "e21": {
            "flips": twenty["flips"].to_dict(orient="records"),
            "licence": twenty["e21_licence"],
        },
        "e22": {
            "pooled": twentytwo["pooled"],
            "by_season": twentytwo["by_season"],
            "leagues": twentytwo["table"].to_dict(orient="records"),
            "licence": twentytwo["licence"],
        },
        "e23": {"a": twentythree, "b": share},
    }
    (out / "summary.json").write_text(
        json.dumps(clean(summary), indent=2, sort_keys=True) + "\n"
    )
    return summary


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument(
        "--prior-dir",
        type=Path,
        required=True,
        help="staged outputs of retained runs decide-02, recipes-01 and amend1-decisions-01",
    )
    parser.add_argument("--raw-root", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--n-boot", type=int, default=N_BOOT)
    args = parser.parse_args(argv)
    summary = run(
        Path.cwd(), args.input_dir, args.prior_dir, args.raw_root, args.out, args.n_boot
    )
    for line in summary["e18"]["level_licence"]:
        print(line["sentence"])
    print(summary["e18"]["spread_contrast"]["sentence"])
    print(summary["e19"]["summary"]["sentence"])
    print(summary["e20"]["licence"]["coin_flip_below_1"]["sentence"])
    print(summary["e21"]["licence"]["sentence"])
    print(summary["e22"]["licence"]["sentence"])
    print(summary["e23"]["a"]["licence"]["sentence"])
    print(summary["e23"]["b"]["licence"]["sentence"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
