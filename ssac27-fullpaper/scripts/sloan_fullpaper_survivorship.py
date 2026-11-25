#!/usr/bin/env python3
"""Survivorship and playing time (E14) of SSAC27 full-paper Amendments 1 and 2.

Amendment 1: docs/research/sloan-full-paper-preregistration-amendment-1-2026-11-04.md
(commit f1a3453da, pushed alone before this file existed). Amendment 2:
docs/research/sloan-full-paper-preregistration-amendment-2-2026-11-05.md (commit
41efa97c2, pushed alone after G14 failed under the literal Amendment 1 rule and
before any E14 outcome, contrast or profile was computed). Base pre-registration:
docs/research/sloan-full-paper-preregistration-2026-11-03.md. Everything here is
EXPLORATORY: destination seasons 2017-2025 were already inspected.

* Rebuild. The documented corpus path (``load_raw`` -> ``_repair_minutes`` ->
  TEAM_KEY dedupe -> ``normalize_games`` with the two quarantine scopes ->
  ``holdout.build_switchers``) gives the player-league-season aggregates. The
  all-arrivals population applies the v10 cohort rules of
  ``revision.reconstruct_cohort`` with ONE change, the Amendment 2 stint rule:
  a player with a continental stint of >= 8 games enters exactly as in v10
  (largest-minutes stint among those); a player with none enters with his
  largest-minutes stint among stints with >= 1 appearance and positive
  minutes. The source floor (>= 8 domestic games) and the qualified-continental incumbency
  rule (a previous continental season with >= 8 games) are unchanged.
* Training rows are unchanged. Factors, the lag correction and every
  regression are fitted on the v10 cohort only, exactly as in v10; the new
  rows are only scored.
* Gate G14: the rows with >= 8 destination games reproduce the 674 anchor keys
  and their ``pir_per36_dest`` to 1e-9. Negative control: the same gate on a
  population built with the floor at 9 must fail, and (Amendment 2) so must
  the literal Amendment 1 rule (threshold at 1, then largest). If G14 fails, the
  generator writes the gate printout and a stint-level diagnosis of each
  missing key (no outcome values) and stops: E14a-E14c do not run.
* E14a: who is missing (arrivals with 1-7 continental games).
* E14b: the three headline contrasts on the >= 3 games & >= 60 minutes
  population, unweighted and minutes-weighted, two-way clustered; the
  >= 1-game population minutes-weighted only (descriptive).
* E14c: playing-time outcome T = 5 x minutes / team minutes, the same ladder
  with the source share x_T and the career prior h_T (prior_mean_pir36 rule),
  each with and without the EFF/36 translated feature z.

Threats: identity of the rebuilt population (G14 exact gate with a floor-9
negative control); leakage of the new rows into fits (estimation frame is the
pinned v10 cohort; anchor features and forecasts must be reproduced to 1e-9);
silently dropped rows (every exclusion counted by game band); a history rule
that does not reproduce v10 (h_T built only if the same pooled-prior code
reproduces ``prior_mean_pir36`` to 1e-9).
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
from scipy.stats import t as student_t  # noqa: E402

from scripts import build_league_factors as blf  # noqa: E402
from scripts import compare_translation_designs as design  # noqa: E402
from scripts import sloan_context_benchmarks as benchmark  # noqa: E402
from scripts import sloan_fullpaper_common as common  # noqa: E402
from scripts import sloan_fullpaper_robustness as robust  # noqa: E402
from scripts import sloan_revision_analysis as revision  # noqa: E402
from scripts import validate_translation_holdout as holdout  # noqa: E402
from scripts.translation_research_common import fit_table, sha256_file  # noqa: E402

AMENDMENT = (
    ROOT / "docs/research/sloan-full-paper-preregistration-amendment-1-2026-11-04.md"
)
AMENDMENT_COMMIT = "f1a3453dae4ed77b069ad8c12f963eb3e32d27ee"
AMENDMENT_2 = (
    ROOT / "docs/research/sloan-full-paper-preregistration-amendment-2-2026-11-05.md"
)
AMENDMENT_2_COMMIT = "41efa97c2fa122993d712b0880c525113774291b"
STINT_RULE = "two_step"
KEY = common.KEY
SEASONS = common.ANCHOR_SEASONS
V10_FLOOR = holdout.MIN_GAMES  # 8
ALL_FLOOR = 1
NEGATIVE_FLOOR = 9
WIDE_GAMES = 3
WIDE_MINUTES = 60.0
ROTATION_MPG = 15.0
ROTATION_GAMES = 8
G14_TOLERANCE = 1e-9
PRIOR_TOLERANCE = 1e-9
N_ANCHOR = 674
ARMS = tuple(benchmark.ARMS)
SPECS = ("player_club_season", "player_season")
PRIMARY_SPEC = "player_club_season"
MARGIN_SHARE = 0.02
WEIGHTINGS = ("unweighted", "minutes_weighted")

#: The three registered headline contrasts (left, right); positive favours right.
HEADLINE = {
    "history_gain": ("history_only", "scheduled_history"),
    "e1_head_to_head": ("scheduled_history", "source_ridge_10"),
    "offsets10_increment": ("source_ridge_10", "source_ridge_10_scheduled"),
}
#: E14c ladder contrasts for T. Primary first, secondary second; the rest printed.
T_CONTRASTS = {
    "offsets10_gain_over_history": ("history_only", "source_ridge_10"),
    "z_increment_offsets10": ("source_ridge_10", "source_ridge_10_scheduled"),
    "destination_gain_over_history": ("history_only", "history_destination"),
    "destination_slope_gain_over_history": (
        "history_only",
        "history_destination_slope",
    ),
    "offsets1_gain_over_history": ("history_only", "source_ridge_1"),
    "offsets100_gain_over_history": ("history_only", "source_ridge_100"),
    "z_increment_history": ("history_only", "scheduled_history"),
    "z_increment_destination_slope": (
        "history_destination_slope",
        "history_destination_slope_scheduled",
    ),
    "z_increment_offsets1": ("source_ridge_1", "source_ridge_1_scheduled"),
    "z_increment_offsets100": ("source_ridge_100", "source_ridge_100_scheduled"),
}
T_PRIMARY = "offsets10_gain_over_history"
T_SECONDARY = "z_increment_offsets10"

LICENSE_E14B = "the result is not an artefact of the 8-game rule"
LICENSE_E14C = "knowing the leagues also predicts how much a signing will play"


class GateFailure(common.GateFailure):
    """A registered E14 gate did not hold."""


# --------------------------------------------------------------- population --
def select_stints(
    continental: pd.DataFrame, dest_floor: int, rule: str
) -> pd.DataFrame:
    """One destination stint per player-season.

    ``two_step`` (Amendment 2, registered): a player with a stint of >= 8
    games (and >= the floor) keeps v10's choice, the largest-minutes stint
    among those; a player with none keeps his largest-minutes stint among
    stints with >= ``dest_floor`` appearances and positive minutes.
    ``literal`` (Amendment 1 as first implemented; kept as the gate's added
    negative control): threshold at the floor, then the largest-minutes stint.
    """
    eligible = continental[
        (continental.games >= dest_floor) & (continental.minutes > 0)
    ]
    if rule == "literal":
        return eligible.sort_values("minutes", ascending=False).drop_duplicates(
            ["player_name", "season"]
        )
    if rule != "two_step":
        raise ValueError(f"unknown stint rule: {rule}")
    high = (
        eligible[eligible.games >= max(dest_floor, V10_FLOOR)]
        .sort_values("minutes", ascending=False)
        .drop_duplicates(["player_name", "season"])
    )
    rest = eligible.merge(
        high[["player_name", "season"]].assign(_high=True),
        on=["player_name", "season"],
        how="left",
        validate="m:1",
    )
    low = (
        rest[rest._high.isna()]
        .drop(columns="_high")
        .sort_values("minutes", ascending=False)
        .drop_duplicates(["player_name", "season"])
    )
    return pd.concat([high, low], ignore_index=True)


def arrivals_ledger(
    agg: pd.DataFrame, dest_floor: int, rule: str = "two_step"
) -> pd.DataFrame:
    """``revision.reconstruct_cohort`` with the destination floor as a parameter.

    Only the continental destination stint rule changes (``select_stints``);
    the source floor and the qualified-continental incumbency rule stay at
    v10's 8 games. With ``dest_floor=8`` the ledger equals
    ``reconstruct_cohort`` under either rule (asserted in ``run`` and tested).
    """
    revision.unique(agg, ["player_name", "season", "league"])
    q = agg[(agg.games >= holdout.MIN_GAMES) & (agg.minutes > 0)]
    continental = agg[agg.league.isin(blf.CONTINENTAL)]
    source_all = agg[~agg.league.isin(blf.NOT_A_SOURCE)]
    qualified = (
        q[q.league.isin(blf.CONTINENTAL)]
        .sort_values("minutes", ascending=False)
        .drop_duplicates(["player_name", "season"])
    )
    dest = select_stints(continental, dest_floor, rule)
    remaining = continental.merge(
        dest[["player_name", "season"]].assign(_kept=True),
        on=["player_name", "season"],
        how="left",
        validate="m:1",
    )
    remaining = remaining[remaining._kept.isna()].drop(columns="_kept")
    remaining = remaining.sort_values("minutes", ascending=False).drop_duplicates(
        ["player_name", "season"]
    )
    observed = pd.concat([dest, remaining], ignore_index=True)
    src = (
        q[~q.league.isin(blf.NOT_A_SOURCE)]
        .sort_values("minutes", ascending=False)
        .drop_duplicates(["player_name", "season"])
    )
    s = src.assign(season_join=src.season + 1)
    ledger = observed.merge(
        s,
        left_on=["player_name", "season"],
        right_on=["player_name", "season_join"],
        suffixes=("_dest", "_src"),
        how="left",
        validate="1:1",
    )
    prev_cont = qualified[["player_name", "season"]].assign(
        season_dest=lambda x: x.season + 1, was_cont=1
    )
    ledger = ledger.merge(
        prev_cont[[*KEY, "was_cont"]], on=KEY, how="left", validate="1:1"
    )
    ledger["was_cont"] = ledger.was_cont.fillna(0).astype(int)
    hist = pooled_prior(agg, "pir", "minutes", 36.0).rename(
        columns={"prior": "prior_mean_pir36", "season": "season_src"}
    )
    ledger = ledger.merge(
        hist, on=["player_name", "season_src"], how="left", validate="m:1"
    )
    ledger["above_own_prior"] = ledger.pir_per36_src > ledger.prior_mean_pir36
    ledger["name_multi_league"] = (
        ledger.player_name.map(agg.groupby("player_name").league.nunique())
        .fillna(0)
        .astype(int)
    )
    ledger["name_multiclub_season"] = ledger.player_name.isin(
        agg.loc[agg.n_clubs > 1, "player_name"]
    )
    ledger["cluster"] = (
        ledger.season_dest.astype(str)
        + "|"
        + ledger.league_dest
        + "|"
        + ledger.club_dest
    )
    available = set(zip(source_all.player_name, source_all.season + 1))
    ledger["source_available"] = [tuple(k) in available for k in ledger[KEY].to_numpy()]
    ledger["destination_qualified"] = (
        (ledger.games_dest >= dest_floor)
        & np.isfinite(ledger.minutes_dest)
        & (ledger.minutes_dest > 0)
    )
    ledger["source_qualified"] = ledger.season_src.notna()
    ledger["qualified_incumbent"] = ledger.was_cont.ne(0)
    ledger["registered_source_exclusion"] = ledger.league_src.isin(
        holdout.EXCLUDED_SOURCE
    )
    ledger["source_positive_finite"] = np.isfinite(ledger.pir_per36_src) & (
        ledger.pir_per36_src > 0
    )
    ledger["destination_finite"] = np.isfinite(ledger.pir_per36_dest)
    ledger["destination_positive"] = ledger.pir_per36_dest > 0
    ledger["first_exclusion"] = ""
    for flag, positive, reason in (
        ("destination_qualified", True, "destination_exposure"),
        ("source_available", True, "no_consecutive_domestic_source"),
        ("source_qualified", True, "source_exposure"),
        ("qualified_incumbent", False, "continental_incumbent"),
        ("registered_source_exclusion", False, "registered_source_exclusion"),
        ("source_positive_finite", True, "source_nonpositive_or_nonfinite"),
        ("destination_finite", True, "destination_nonfinite"),
    ):
        bad = ~ledger[flag] if positive else ledger[flag]
        ledger.loc[bad & ledger.first_exclusion.eq(""), "first_exclusion"] = reason
    ledger["expanded_eligible"] = ledger.first_exclusion.eq("")
    ledger["original_eligible"] = ledger.expanded_eligible & ledger.destination_positive
    ledger.loc[
        ledger.expanded_eligible & ~ledger.destination_positive, "first_exclusion"
    ] = "destination_nonpositive"
    revision.unique(ledger)
    return ledger


def population(ledger: pd.DataFrame, seasons=SEASONS) -> pd.DataFrame:
    """v10-eligible rows (``original_eligible``) in the evaluation seasons."""
    rows = ledger.loc[ledger.original_eligible & ledger.season_dest.isin(seasons)]
    return rows.sort_values(KEY).reset_index(drop=True)


def g14_differences(
    rows: pd.DataFrame, cohort: pd.DataFrame, keys: pd.DataFrame
) -> dict:
    """Rows with >= 8 destination games against the 674 anchor keys and outcomes."""
    eight = rows.loc[rows.games_dest >= V10_FLOOR, [*KEY, "pir_per36_dest"]]
    anchor = keys.merge(
        cohort[[*KEY, "pir_per36_dest"]], on=KEY, how="left", validate="1:1"
    )
    got = set(map(tuple, eight[KEY].to_numpy()))
    want = set(map(tuple, anchor[KEY].to_numpy()))
    both = anchor.merge(eight, on=KEY, suffixes=("_anchor", "_rebuilt"), validate="1:1")
    worst = (
        float(np.max(np.abs(both.pir_per36_dest_anchor - both.pir_per36_dest_rebuilt)))
        if len(both)
        else float("inf")
    )
    return {
        "rows_at_least_8_games": len(eight),
        "anchor_keys": len(want),
        "missing_anchor_keys": len(want - got),
        "extra_keys": len(got - want),
        "matched": len(both),
        "max_abs_difference_pir_per36_dest": worst,
    }


def assert_g14(diff: dict, tolerance: float = G14_TOLERANCE) -> None:
    if (
        diff["anchor_keys"] != N_ANCHOR
        or diff["missing_anchor_keys"]
        or diff["extra_keys"]
        or diff["matched"] != N_ANCHOR
        or not diff["max_abs_difference_pir_per36_dest"] <= tolerance
    ):
        raise GateFailure(f"G14 failed: {diff} (tolerance {tolerance:.0e})")


STOPPED = (
    "G14 failed: E14a, E14b and E14c were not run (registered gate; no "
    "workaround). No statistic of the arrivals with fewer than 8 continental "
    "games was computed."
)


def g14_missing(ledger, cohort, keys, agg) -> list:
    """Why an anchor key left the >= 8-game rows: its stints, without outcomes."""
    selected = ledger.set_index(KEY)
    anchor = keys.merge(cohort, on=KEY, how="left", validate="1:1").set_index(KEY)
    out = []
    for player, season in keys.itertuples(index=False):
        key = (player, season)
        if key in selected.index and selected.loc[key, "games_dest"] >= V10_FLOOR:
            if bool(selected.loc[key, "original_eligible"]):
                continue
        stints = agg.loc[
            agg.player_name.eq(player)
            & agg.season.eq(season)
            & agg.league.isin(blf.CONTINENTAL)
        ].sort_values("minutes", ascending=False)
        row = selected.loc[key] if key in selected.index else None
        out.append(
            {
                "player_name": player,
                "season_dest": int(season),
                "v10_league_dest": anchor.loc[key, "league_dest"],
                "v10_games_dest": int(anchor.loc[key, "games_dest"]),
                "v10_minutes_dest": float(anchor.loc[key, "minutes_dest"]),
                "floor1_league_dest": None if row is None else row["league_dest"],
                "floor1_games_dest": None if row is None else int(row["games_dest"]),
                "floor1_minutes_dest": None
                if row is None
                else float(row["minutes_dest"]),
                "continental_stints": [
                    f"{r.league}: {int(r.games)} games, {r.minutes:.1f} minutes"
                    for r in stints.itertuples()
                ],
            }
        )
    return out


def negative_control(check, *args, **kwargs) -> str:
    try:
        check(*args, **kwargs)
    except common.GateFailure:
        return "rejected as required"
    raise GateFailure(f"negative control passed: {check.__name__}")


# ------------------------------------------------------------------ history --
def pooled_prior(
    agg: pd.DataFrame, numerator: str, exposure: str, scale: float
) -> pd.DataFrame:
    """v10's ``prior_mean_pir36`` rule for any ratio: pooled over all earlier seasons.

    Exposure ``team_slots`` is team minutes / 5 (one full-time slot).
    """
    frame = agg.loc[agg.minutes > 0].copy()
    frame["team_slots"] = frame.team_minutes.astype(float) / 5.0
    hist = (
        frame.groupby(["player_name", "season"])[[numerator, exposure]]
        .sum()
        .sort_index()
        .reset_index()
        .rename(columns={numerator: "num", exposure: "exp"})
    )
    hist[["cum_num", "cum_exp"]] = hist.groupby("player_name")[["num", "exp"]].cumsum()
    hist["prior"] = np.where(
        hist.cum_exp > hist.exp,
        scale * (hist.cum_num - hist.num) / (hist.cum_exp - hist.exp),
        np.nan,
    )
    return hist[["player_name", "season", "prior"]]


def prior_rule_difference(cohort: pd.DataFrame, agg: pd.DataFrame) -> dict:
    """The pooled-prior code must reproduce the cohort's prior_mean_pir36."""
    rebuilt = robust.attach_history(cohort, pooled_prior(agg, "pir", "minutes", 36.0))
    return robust.g3_difference(cohort, rebuilt)


def assert_prior_rule(diff: dict, tolerance: float = PRIOR_TOLERANCE) -> None:
    try:
        robust.assert_g3(diff, tolerance)
    except common.GateFailure as error:
        raise GateFailure(f"prior rule not reproduced: {error}") from error


# ----------------------------------------------------------------- features --
def evaluation_features(
    pairs, estimation, rows, *, seed=0, n_boot=2000, fitter=fit_table
):
    """``refit.refit_features`` for scoring rows that never enter any fit.

    Factors and the lag correction at each row's cutoff come from the pinned
    pairs and the v10 ``estimation`` cohort only; ``rows`` are looked up.
    """
    revision.unique(pairs, ["player_name", "season"])
    revision.unique(estimation)
    revision.unique(rows)
    study = design.Study(
        pairs.copy(), estimation.copy(), seed=seed, n_boot=n_boot, fitter=fitter
    )
    out = rows.copy().reset_index(drop=True)
    for season, group in out.groupby("season_dest", sort=True):
        earlier = estimation.loc[estimation.season_dest.lt(season)]
        for kind, table in study.at(int(season)).items():
            multiplier, fallback, reliable = design.lookup(table, group)
            old_multiplier, _, _ = design.lookup(table, earlier)
            denominator = earlier.pir_per36_src.to_numpy() * old_multiplier
            valid = np.isfinite(denominator) & (denominator > 0)
            lag = (
                float(
                    np.median(
                        earlier.pir_per36_dest.to_numpy()[valid] / denominator[valid]
                    )
                )
                if valid.any()
                else np.nan
            )
            for name, value in (
                ("multiplier_value", multiplier),
                ("fallback", fallback),
                ("reliable", reliable),
                ("k", lag),
                ("translated", group.pir_per36_src.to_numpy() * multiplier * lag),
            ):
                out.loc[group.index, f"{kind}_{name}"] = value
            reason = np.where(
                ~np.isfinite(multiplier), "no_finite_destination_tier", ""
            )
            out.loc[group.index, f"{kind}_reason"] = np.where(
                np.isfinite(multiplier) & ~np.isfinite(lag),
                "no_prior_lag_outcomes",
                reason,
            )
    out["feature_eligible"] = np.isfinite(
        out[[f"{d}_translated" for d in design.DESIGNS]]
    ).all(axis=1)
    return out


def predict(train_features: pd.DataFrame, rows: pd.DataFrame, *, seasons=SEASONS):
    """Every benchmark arm, trained on the v10 rows of earlier seasons only."""
    out, folds = [], []
    for season in seasons:
        train = train_features.loc[
            train_features.season_dest.lt(season) & train_features.feature_eligible
        ].sort_values(KEY)
        test = rows.loc[rows.season_dest.eq(season)].sort_values(KEY).copy()
        support = test.feature_eligible.astype(bool)
        fold = {
            "season": int(season),
            "train_rows": len(train),
            "test_rows": len(test),
            "unseen_source_rows": {},
        }
        for arm in ARMS:
            test[arm] = np.nan
            status = "no_supported_rows"
            if support.any():
                prediction, info = benchmark.fit_model(train, test.loc[support], arm)
                test.loc[support, arm] = prediction
                status = info["status"]
                fold["unseen_source_rows"][arm] = int(info.get("unseen_source_rows", 0))
            test[f"{arm}_status"] = np.where(support, status, "feature_refusal")
        test["scored"] = np.isfinite(test[list(ARMS)]).all(axis=1)
        out.append(test)
        folds.append(fold)
    return pd.concat(out, ignore_index=True), folds


def share_frame(frame: pd.DataFrame, prior: pd.DataFrame | None) -> pd.DataFrame:
    """Copy with the playing-time share T in the pipeline's columns.

    x_T = 5 x minutes_src / team_minutes_src; T = 5 x minutes_dest /
    team_minutes_dest; h_T = the pooled career share before the source season
    (NaN -> x_T inside the design, as for EFF); a_T = 1[x_T > h_T]. The EFF/36
    translated feature ``scheduled_translated`` is kept unchanged as z.
    """
    out = frame.copy()
    out["eff_per36_dest"] = out.pir_per36_dest
    out["pir_per36_src"] = 5.0 * out.minutes_src / out.team_minutes_src
    out["pir_per36_dest"] = 5.0 * out.minutes_dest / out.team_minutes_dest
    if prior is None:
        out["prior_mean_pir36"] = np.nan
    else:
        out["prior_mean_pir36"] = robust.attach_history(out, prior)
    out["above_own_prior"] = out.pir_per36_src > out.prior_mean_pir36
    for side in ("src", "dest"):
        if not np.isfinite(out[f"pir_per36_{side}"]).all():
            raise GateFailure(f"nonfinite playing-time share ({side})")
    return out


# --------------------------------------------------------------- inference --
def weighted_interval(differences, weights, first, second) -> dict:
    """Weighted mean with v10's two-way CGM CR1 interval (Student t, min(G)-1 df).

    theta = sum(w d) / sum(w); the scores w (d - theta) / mean(w) replace the
    residuals of ``revision.multiway_interval`` (identical when w = 1).
    """
    d = np.asarray(differences, dtype=float)
    w = np.ones(len(d)) if weights is None else np.asarray(weights, dtype=float)
    if len(w) != len(d) or not np.isfinite(w).all() or (w <= 0).any():
        raise ValueError("weights must be finite and positive, one per row")
    first = pd.Series(first).reset_index(drop=True)
    second = pd.Series(second).reset_index(drop=True)
    if len(first) != len(d) or len(second) != len(d):
        raise ValueError("cluster length mismatch")
    result = {"n": len(d), "difference": None, "ci95": None, "status": "not_estimable"}
    if not len(d) or not np.isfinite(d).all():
        return {**result, "reason": "empty_or_nonfinite"}
    theta = float(np.sum(w * d) / np.sum(w))
    result["difference"] = theta
    score = w * (d - theta) / w.mean()
    components = {}
    for name, values in (
        ("first", first),
        ("second", second),
        ("intersection", pd.Series(list(zip(first, second)))),
    ):
        codes, ids = pd.factorize(values, sort=False)
        g = len(ids)
        totals = np.bincount(codes, weights=score)
        components[name] = {
            "clusters": g,
            "variance": float(g / (g - 1) * (totals @ totals) / len(d) ** 2)
            if g > 1
            else None,
        }
    if any(c["clusters"] < 2 for c in components.values()):
        return {**result, "reason": "fewer_than_two_clusters"}
    variance = (
        components["first"]["variance"]
        + components["second"]["variance"]
        - components["intersection"]["variance"]
    )
    df = min(components["first"]["clusters"], components["second"]["clusters"]) - 1
    result.update(
        variance=variance,
        degrees_of_freedom=df,
        clusters={k: v["clusters"] for k, v in components.items()},
    )
    if not np.isfinite(variance) or variance <= 0:
        return {**result, "reason": "nonpositive_or_nonfinite_variance"}
    se = float(np.sqrt(variance))
    half = float(student_t.ppf(0.975, df) * se)
    return {
        **result,
        "status": "ok",
        "se": se,
        "p_two_sided": float(2 * student_t.sf(abs(theta) / se, df)),
        "ci95": [theta - half, theta + half],
    }


def contrast_block(rows: pd.DataFrame, left: str, right: str, *, weight=None) -> dict:
    """Paired MAE(left) - MAE(right) (positive favours right), both cluster specs."""
    y = rows.pir_per36_dest.to_numpy(dtype=float)
    e_left = np.abs(rows[left].to_numpy(dtype=float) - y)
    e_right = np.abs(rows[right].to_numpy(dtype=float) - y)
    w = None if weight is None else rows[weight].to_numpy(dtype=float)
    ww = np.ones(len(y)) if w is None else w
    parent = float(np.sum(ww * e_left) / np.sum(ww))
    record = {
        "left": left,
        "right": right,
        "positive_favours": right,
        "weight": weight or "none",
        "n": len(rows),
        "mae_left": parent,
        "mae_right": float(np.sum(ww * e_right) / np.sum(ww)),
    }
    for spec, second in (
        ("player_club_season", "cluster"),
        ("player_season", "season_dest"),
    ):
        block = weighted_interval(e_left - e_right, w, rows.player_name, rows[second])
        ci = block["ci95"]
        block["pct_of_parent_mae"] = 100.0 * block["difference"] / parent
        block["upper_pct_of_parent_mae"] = (
            None if ci is None else 100.0 * ci[1] / parent
        )
        block["verdict"] = (
            "not_estimable"
            if ci is None
            else "above_zero"
            if ci[0] > 0
            else "below_zero"
            if ci[1] < 0
            else "spans_zero"
        )
        record[spec] = block
    record["difference"] = record[PRIMARY_SPEC]["difference"]
    return record


def ladder(rows: pd.DataFrame, *, weight=None) -> dict:
    y = rows.pir_per36_dest.to_numpy(dtype=float)
    w = np.ones(len(y)) if weight is None else rows[weight].to_numpy(dtype=float)
    out = {}
    for arm in ARMS:
        e = rows[arm].to_numpy(dtype=float) - y
        out[arm] = {
            "n": len(rows),
            "mae": float(np.sum(w * np.abs(e)) / np.sum(w)),
            "rmse": float(np.sqrt(np.sum(w * e**2) / np.sum(w))),
            "bias": float(np.sum(w * e) / np.sum(w)),
        }
    return out


def headline_pattern(blocks: dict, spec: str = PRIMARY_SPEC) -> dict:
    """The registered licence pattern of the three headline contrasts.

    (a) history vs history + translation: interval above zero (E3 rule);
    (b) E1 C_H: interval not below zero with point >= 0 (the 'matches' or 'more
    accurate' licence; below zero withdraws the headline); (c) offsets
    lambda-10 vs + translation: no interval above zero and an upper bound
    below 2% of its parent MAE (E2 rule).
    """
    a, b, c = (blocks[name] for name in HEADLINE)
    a_ci, b_ci, c_ci = a[spec]["ci95"], b[spec]["ci95"], c[spec]["ci95"]
    checks = {
        "history_gain_above_zero": a_ci is not None and a_ci[0] > 0,
        "e1_not_below_zero_point_nonnegative": b_ci is not None
        and b_ci[1] >= 0
        and b[spec]["difference"] >= 0,
        "offsets10_increment_not_above_zero": c_ci is not None and not c_ci[0] > 0,
        "offsets10_upper_below_2pct_of_parent": c_ci is not None
        and c_ci[1] < MARGIN_SHARE * c["mae_left"],
    }
    needs = {
        "history_gain": ("history_gain_above_zero",),
        "e1_head_to_head": ("e1_not_below_zero_point_nonnegative",),
        "offsets10_increment": (
            "offsets10_increment_not_above_zero",
            "offsets10_upper_below_2pct_of_parent",
        ),
    }
    failing = [n for n, ks in needs.items() if not all(checks[k] for k in ks)]
    return {
        **{k: bool(v) for k, v in checks.items()},
        "failing_contrasts": failing,
        "holds": not failing,
    }


def e14b_licence(block: dict) -> dict:
    """Licence on the >= 3 games & >= 60 minutes population: both weightings must hold."""
    patterns = {w: block[w]["pattern"][PRIMARY_SPEC] for w in WEIGHTINGS}
    holds = all(p["holds"] for p in patterns.values())
    failing = sorted({c for p in patterns.values() for c in p["failing_contrasts"]})
    return {
        "holds": holds,
        "failing_contrasts": failing,
        "sentence": LICENSE_E14B if holds else None,
        "otherwise": None
        if holds
        else f"failing contrast(s) {failing}: reported as the paper's main qualification and flagged to Amir",
        "rule": "registered pattern on the >= 3 games & >= 60 minutes population, unweighted AND minutes-weighted, two-way clustered (player, destination club-season)",
    }


def e14c_licence(record: dict) -> dict:
    ci = record[PRIMARY_SPEC]["ci95"]
    holds = ci is not None and ci[0] > 0
    return {
        "primary": T_PRIMARY,
        "holds": bool(holds),
        "sentence": LICENSE_E14C if holds else None,
    }


# ------------------------------------------------------------ E14a / E14c --
def band(games: pd.Series) -> np.ndarray:
    g = np.asarray(games, dtype=float)
    return np.where(g >= V10_FLOOR, "8+", np.where(g >= WIDE_GAMES, "3-7", "1-2"))


def exclusion_counts(ledger: pd.DataFrame, seasons=SEASONS) -> list:
    """Every continental stint of the evaluation seasons by game band and reason."""
    frame = ledger.loc[ledger.season_dest.isin(seasons)].copy()
    frame["band"] = band(frame.games_dest)
    frame["reason"] = frame.first_exclusion.replace("", "eligible")
    table = frame.groupby(["band", "reason"]).size().rename("n").reset_index()
    return table.to_dict("records")


PROFILE_COLUMNS = {
    "source_eff36": "pir_per36_src",
    "source_min_per_game": "min_per_game_src",
    "source_games": "games_src",
    "destination_games": "games_dest",
    "destination_minutes": "minutes_dest",
    "destination_min_per_game": "min_per_game_dest",
    "destination_eff36": "pir_per36_dest",
}


def profile(rows: pd.DataFrame) -> dict:
    out = {"n": len(rows)}
    for name, col in PROFILE_COLUMNS.items():
        v = rows[col].astype(float)
        out[name] = {
            "mean": float(v.mean()) if len(v) else None,
            "median": float(v.median()) if len(v) else None,
        }
    return out


def e14a(rows: pd.DataFrame) -> dict:
    short = rows.loc[rows.games_dest < V10_FLOOR]
    anchor = rows.loc[rows.games_dest >= V10_FLOOR]
    group = np.where(rows.games_dest < V10_FLOOR, "1-7", "8+")
    counts = (
        rows.assign(group=group)
        .groupby(["group", "league_dest", "league_src"])
        .size()
        .rename("n")
        .reset_index()
    )
    destinations = sorted(rows.league_dest.unique())
    return {
        "n_short_1_to_7": len(short),
        "n_anchor_8_plus": len(anchor),
        "short_share_of_all_arrivals": len(short) / len(rows),
        "by_destination": {
            d: {
                "short": int((short.league_dest == d).sum()),
                "anchor": int((anchor.league_dest == d).sum()),
            }
            for d in destinations
        },
        "by_source": {
            s: {
                "short": int((short.league_src == s).sum()),
                "anchor": int((anchor.league_src == s).sum()),
            }
            for s in sorted(rows.league_src.unique())
        },
        "counts": counts.to_dict("records"),
        "profile": {
            "short_1_to_7": profile(short),
            "anchor_8_plus": profile(anchor),
            **{
                f"short_1_to_7:{d}": profile(short.loc[short.league_dest == d])
                for d in destinations
            },
            **{
                f"anchor_8_plus:{d}": profile(anchor.loc[anchor.league_dest == d])
                for d in destinations
            },
        },
    }


def rotation(rows: pd.DataFrame) -> dict:
    flag = (rows.min_per_game_dest >= ROTATION_MPG) & (
        rows.games_dest >= ROTATION_GAMES
    )
    frame = rows.assign(rotation=flag)

    def rate(g):
        return {
            "n": len(g),
            "rotation": int(g.rotation.sum()),
            "rate": float(g.rotation.mean()),
        }

    return {
        "rule": f">= {ROTATION_MPG:g} minutes per game and >= {ROTATION_GAMES} games",
        "overall": rate(frame),
        "by_source_league": {
            s: rate(g) for s, g in frame.groupby("league_src", sort=True)
        },
        "by_destination": {
            d: rate(g) for d, g in frame.groupby("league_dest", sort=True)
        },
    }


# --------------------------------------------------------------------- run --
def scored_rows(rows: pd.DataFrame, label: str, counts: dict) -> pd.DataFrame:
    """Rows where every arm scored; the unscorable are counted, never hidden."""
    bad = ~rows.scored.astype(bool)
    by_band = pd.Series(band(rows.games_dest[bad])).value_counts()
    counts[label] = {
        "rows": len(rows),
        "unscorable": int(bad.sum()),
        "unscorable_by_band": {str(k): int(v) for k, v in by_band.items()},
    }
    return rows.loc[~bad].reset_index(drop=True)


def flat_contrasts(analysis, population_name, weighting, contrasts) -> list:
    out = []
    for name, rec in contrasts.items():
        for spec in SPECS:
            blk = rec[spec]
            ci = blk["ci95"]
            out.append(
                {
                    "analysis": analysis,
                    "population": population_name,
                    "weight": weighting,
                    "contrast": name,
                    "left": rec["left"],
                    "right": rec["right"],
                    "spec": spec,
                    "n": rec["n"],
                    "mae_left": rec["mae_left"],
                    "mae_right": rec["mae_right"],
                    "difference": blk["difference"],
                    "ci_low": None if ci is None else ci[0],
                    "ci_high": None if ci is None else ci[1],
                    "pct_of_parent_mae": blk["pct_of_parent_mae"],
                    "upper_pct_of_parent_mae": blk["upper_pct_of_parent_mae"],
                    "verdict": blk["verdict"],
                }
            )
    return out


def run(input_dir: Path, raw_root: Path, out: Path) -> dict:
    v9, v10_summary = common.load_references(ROOT)
    pairs, cohort = common.load_pool(input_dir, "official_corrected")
    keys = common.target_keys(v10_summary)
    summary: dict = {
        "analysis": "E14 survivorship and playing time (Amendments 1 and 2), EXPLORATORY",
        "amendment_commit": AMENDMENT_COMMIT,
        "amendment_sha256": sha256_file(AMENDMENT),
        "amendment_2_commit": AMENDMENT_2_COMMIT,
        "amendment_2_sha256": sha256_file(AMENDMENT_2),
        "protocol_commit": common.PROTOCOL_COMMIT,
        "seasons": list(SEASONS),
        "rules": {
            "all_arrivals_destination_floor": f">= {ALL_FLOOR} appearance with positive minutes",
            "v10_destination_floor": V10_FLOOR,
            "stint_rule": "Amendment 2 two-step: a player with a >= 8-game continental stint keeps v10's largest-minutes stint among those; otherwise his largest-minutes stint with >= 1 appearance and positive minutes",
            "source_floor": int(holdout.MIN_GAMES),
            "incumbency": "a previous-season continental stint with >= 8 games",
            "other_rules": "v10 original_eligible: consecutive domestic source, Poland excluded, positive source and destination EFF/36",
            "wide_population": f">= {WIDE_GAMES} games and >= {WIDE_MINUTES:g} minutes",
            "weights": "destination minutes",
            "training_rows": "v10 cohort only (factors, lag and regressions); new rows are scored only",
        },
    }

    # ---- precondition: G0 on the pinned inputs (the v10 code path) ----
    features, _ = common.build_features(pairs, cohort)
    v10_rows, _ = common.forecast(features)
    anchor = common.on_targets(v10_rows, keys)
    g0 = common.g0_differences(anchor, v9, v10_summary)
    summary["g0"] = {
        "negative_control": negative_control(common.assert_g0, g0, tolerance=-1.0)
    }
    common.assert_g0(g0)
    summary["g0"].update(status="passed", max_difference=max(g0.values()))

    # ---- rebuild and G14 ----
    _, agg, rebuild = robust.rebuild_games(raw_root)
    summary["rebuild"] = rebuild
    reference, _ = revision.reconstruct_cohort(agg)
    right = reference.sort_values(KEY).reset_index(drop=True)
    for rule in ("two_step", "literal"):
        left = arrivals_ledger(agg, V10_FLOOR, rule).sort_values(KEY)
        left = left.reset_index(drop=True)
        if list(left.columns) != list(right.columns) or not left.equals(right):
            raise GateFailure(
                f"arrivals_ledger(floor=8, {rule}) differs from reconstruct_cohort"
            )
    ledger = arrivals_ledger(agg, ALL_FLOOR, STINT_RULE)
    rows = population(ledger)
    g14 = g14_differences(rows, cohort, keys)
    control = g14_differences(
        population(arrivals_ledger(agg, NEGATIVE_FLOOR, STINT_RULE)), cohort, keys
    )
    literal = g14_differences(
        population(arrivals_ledger(agg, ALL_FLOOR, "literal")), cohort, keys
    )
    summary["g14"] = {
        "stint_rule": STINT_RULE,
        "differences": g14,
        "negative_control_floor_9": control,
        "negative_control": negative_control(assert_g14, control),
        "literal_amendment_1_rule": literal,
        "literal_rule_control": negative_control(assert_g14, literal),
        "tolerance": G14_TOLERANCE,
        "ledger_floor_8_equals_reconstruct_cohort": True,
    }
    try:
        assert_g14(g14)
    except GateFailure as error:
        # Registered gate failed: record the printout and stop. Nothing in
        # E14a-E14c runs, and no statistic of the new rows is computed.
        missing = g14_missing(ledger, cohort, keys, agg)
        summary["g14"].update(status="failed", error=str(error), missing=missing)
        summary["stopped"] = STOPPED
        out.mkdir(parents=True, exist_ok=False)
        pd.DataFrame(
            [{**m, "stint": s} for m in missing for s in m["continental_stints"]]
        ).to_csv(out / "g14_missing_anchor_stints.csv", index=False)
        (out / "summary.json").write_text(
            json.dumps(clean(summary), indent=2, sort_keys=True) + "\n"
        )
        return summary
    summary["g14"]["status"] = "passed"
    summary["exclusions_by_band"] = exclusion_counts(ledger)
    games3 = rows.games_dest >= WIDE_GAMES
    summary["population_counts"] = {
        "all_arrivals": len(rows),
        "games_1_to_2": int((~games3).sum()),
        "games_3_to_7": int((games3 & (rows.games_dest < V10_FLOOR)).sum()),
        "games_8_plus": int((rows.games_dest >= V10_FLOOR).sum()),
        "wide_3_games_60_minutes": int(
            (games3 & (rows.minutes_dest >= WIDE_MINUTES)).sum()
        ),
        "by_season": {
            str(int(s)): int(n)
            for s, n in rows.season_dest.value_counts().sort_index().items()
        },
    }

    # ---- E14a ----
    summary["e14a"] = e14a(rows)

    # ---- features for the wider rows; estimation frame = the v10 cohort ----
    wide = evaluation_features(pairs, cohort, rows)
    translated = [f"{d}_translated" for d in design.DESIGNS]
    check = anchor[KEY + translated].merge(
        wide[KEY + translated], on=KEY, suffixes=("_v10", ""), validate="1:1"
    )
    feature_diff = max(
        float(np.max(np.abs(check[f"{c}_v10"] - check[c]))) for c in translated
    )
    if len(check) != N_ANCHOR or not feature_diff <= G14_TOLERANCE:
        raise GateFailure(
            f"anchor features not reproduced ({len(check)}, {feature_diff:.3e})"
        )
    scored, folds = predict(features, wide)
    pred_check = anchor[KEY + list(ARMS)].merge(
        scored[KEY + list(ARMS)], on=KEY, suffixes=("_v10", ""), validate="1:1"
    )
    pred_diff = max(
        float(np.max(np.abs(pred_check[f"{arm}_v10"] - pred_check[arm])))
        for arm in ARMS
    )
    if len(pred_check) != N_ANCHOR or not pred_diff <= G14_TOLERANCE:
        raise GateFailure(f"anchor forecasts not reproduced ({pred_diff:.3e})")
    summary["g14"]["anchor_feature_max_abs_difference"] = feature_diff
    summary["g14"]["anchor_forecast_max_abs_difference"] = pred_diff
    summary["folds_eff"] = folds

    # ---- E14b ----
    counts: dict = {}
    eff = scored_rows(scored, "eff_all_arrivals", counts)
    populations = {
        "anchor_8_plus": eff.loc[eff.games_dest >= V10_FLOOR],
        "wide_3_games_60_minutes": eff.loc[
            (eff.games_dest >= WIDE_GAMES) & (eff.minutes_dest >= WIDE_MINUTES)
        ],
        "all_arrivals_1_plus": eff,
    }
    e14b = {"scoring": counts}
    flat = []
    for name, frame in populations.items():
        frame = frame.reset_index(drop=True)
        descriptive = name == "all_arrivals_1_plus"
        block = {"n": len(frame), "descriptive": descriptive}
        for weighting in ("minutes_weighted",) if descriptive else WEIGHTINGS:
            weight = "minutes_dest" if weighting == "minutes_weighted" else None
            contrasts = {
                c: contrast_block(frame, *pair, weight=weight)
                for c, pair in HEADLINE.items()
            }
            block[weighting] = {
                "ladder": ladder(frame, weight=weight),
                "contrasts": contrasts,
                "pattern": {spec: headline_pattern(contrasts, spec) for spec in SPECS},
            }
            flat += flat_contrasts("E14b", name, weighting, contrasts)
        e14b[name] = block
    e14b["licence"] = e14b_licence(e14b["wide_3_games_60_minutes"])
    summary["e14b"] = e14b

    # ---- E14c: playing-time share T ----
    prior_diff = prior_rule_difference(cohort, agg)
    try:
        assert_prior_rule(prior_diff)
        h_status = "built"
    except GateFailure:
        h_status = "not_buildable"
    summary["e14c_prior_rule"] = {
        "difference": prior_diff,
        "negative_control": negative_control(
            assert_prior_rule, prior_diff, tolerance=-1.0
        ),
        "h_T": h_status,
    }
    share_prior = (
        pooled_prior(agg, "minutes", "team_slots", 1.0) if h_status == "built" else None
    )
    t_train = share_frame(features, share_prior)
    t_rows = share_frame(wide, share_prior)
    t_scored, t_folds = predict(t_train, t_rows)
    t_counts: dict = {}
    t_all = scored_rows(t_scored, "t_all_arrivals", t_counts)
    t_anchor = t_all.loc[t_all.games_dest >= V10_FLOOR].reset_index(drop=True)
    e14c = {
        "scoring": t_counts,
        "folds": t_folds,
        "outcome": "T = 5 x minutes_dest / team_minutes_dest (team minutes summed over the player's own games)",
        "features": "x_T = 5 x minutes_src / team_minutes_src; h_T = pooled career share before the source season; a_T = 1[x_T > h_T]; z = EFF/36 translated feature",
    }
    for name, frame in (("all_arrivals_1_plus", t_all), ("anchor_8_plus", t_anchor)):
        contrasts = {c: contrast_block(frame, *pair) for c, pair in T_CONTRASTS.items()}
        e14c[name] = {
            "n": len(frame),
            "mean_T": float(frame.pir_per36_dest.mean()),
            "sd_T": float(frame.pir_per36_dest.std(ddof=1)),
            "ladder": ladder(frame),
            "contrasts": contrasts,
        }
        flat += flat_contrasts("E14c", name, "unweighted", contrasts)
    e14c["licence"] = e14c_licence(e14c["all_arrivals_1_plus"]["contrasts"][T_PRIMARY])
    e14c["rotation"] = rotation(t_all)
    e14c["rotation_anchor_8_plus"] = rotation(t_anchor)
    summary["e14c"] = e14c

    # ---- outputs ----
    out.mkdir(parents=True, exist_ok=False)
    keep = [
        *KEY,
        "league_dest",
        "league_src",
        "club_dest",
        "cluster",
        "games_dest",
        "minutes_dest",
        "min_per_game_dest",
        "team_minutes_dest",
        "games_src",
        "minutes_src",
        "min_per_game_src",
        "team_minutes_src",
        "pir_per36_src",
        "prior_mean_pir36",
        "above_own_prior",
        "scheduled_translated",
        "pir_per36_dest",
        "scored",
        *ARMS,
    ]
    scored[keep].to_parquet(out / "e14_eff_rows.parquet", index=False)
    t_scored[[*keep, "eff_per36_dest"]].rename(
        columns={
            "pir_per36_src": "share_src_xT",
            "prior_mean_pir36": "share_prior_hT",
            "above_own_prior": "share_above_prior_aT",
            "pir_per36_dest": "share_dest_T",
        }
    ).to_parquet(out / "e14c_share_rows.parquet", index=False)
    pd.DataFrame(summary["e14a"]["counts"]).to_csv(out / "e14a_counts.csv", index=False)
    pd.DataFrame(summary["exclusions_by_band"]).to_csv(
        out / "e14_exclusions_by_band.csv", index=False
    )
    pd.DataFrame(
        [
            {"source_league": s, **v}
            for s, v in e14c["rotation"]["by_source_league"].items()
        ]
    ).to_csv(out / "e14c_rotation_by_source.csv", index=False)
    pd.DataFrame(flat).to_csv(out / "e14_contrasts.csv", index=False)
    (out / "summary.json").write_text(
        json.dumps(clean(summary), indent=2, sort_keys=True) + "\n"
    )
    return summary


def clean(value):
    if isinstance(value, dict):
        return {str(k): clean(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [clean(v) for v in value]
    if isinstance(value, np.bool_):
        return bool(value)
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, (np.floating, float)):
        return float(value) if np.isfinite(value) else None
    return value


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument("--raw-root", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    summary = run(args.input_dir, args.raw_root, args.out)
    status = {"g0": summary["g0"]["status"], "g14": summary["g14"]["status"]}
    if "stopped" in summary:
        status.update(
            stopped=summary["stopped"], g14_printout=summary["g14"]["differences"]
        )
    else:
        status.update(
            h_T=summary["e14c_prior_rule"]["h_T"],
            e14b_licence_holds=summary["e14b"]["licence"]["holds"],
            e14c_licence_holds=summary["e14c"]["licence"]["holds"],
        )
    print(json.dumps(status))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
