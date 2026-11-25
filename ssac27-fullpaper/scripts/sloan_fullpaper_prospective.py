#!/usr/bin/env python3
"""P1 of the SSAC27 full paper: freeze 2026-27 forecasts, and score them later.

Pre-registration: docs/research/sloan-full-paper-preregistration-2026-11-03.md
(commit f52e7c831, pushed 2026-11-03T09:15:02Z), section "P1. 2026-27
frozen-forecast test".

``freeze`` builds every 2025-26 (stored season 2025) domestic source
player-season on disk with the v10 cohort code path, and forecasts it for both
continental destinations with all 17 v10 arms. Factors come from pool-A pairs
<= 2025 (recipe R1), the lag from destinations <= 2025, and every arm is trained
on the feature-eligible destination rows <= 2025. The forecasts do not depend
on who later qualifies.

Scoring is a separate entry point, ``scripts/sloan_fullpaper_prospective_score.py``:
it selects the 2026 newcomers by the v10 eligibility rules from continental
games dated on or before 24 Nov 2026 and computes P-a, P-b, P-c and the
registered read-outs. It refuses to run before 25 Nov 2026.

Threats: a freeze that reads 2026-27 statistics (path assertion before any file
is opened; no season-2026 continental path may be in the inputs); a
prospective path that is not the v10 path (the freeze code pointed at
destination 2025 must reproduce the anchor's 127 forecasts on every arm to
1e-9, and the corpus rebuild must reproduce the source side of all 1,371
cohort rows); partial 2025-26 source seasons (per-row flag and the
complete-source sensitivity); a gate that cannot fail (impossible-tolerance
negative control); silent loss (every source player-season is forecast or
carries a refusal status).
"""

# ruff: noqa: E501 -- gate messages and pre-registered wording
from __future__ import annotations

if __name__ == "__main__":
    import sys as _sys
    from pathlib import Path as _Path

    _sys.path.insert(0, str(_Path(__file__).resolve().parents[1]))
    from src.research.execution import enter as _enter

    _enter(__file__)

import argparse
import contextlib
import datetime as dt
import io
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

from scripts import adjudicate_sloan_acb_sources as acb  # noqa: E402
from scripts import build_league_factors as blf  # noqa: E402
from scripts import sloan_context_benchmarks as benchmark  # noqa: E402
from scripts import sloan_corrected_sources as corrected  # noqa: E402
from scripts import sloan_fullpaper_common as common  # noqa: E402
from scripts import sloan_full_refit as refit  # noqa: E402
from scripts import sloan_revision_analysis as revision  # noqa: E402
from scripts import sloan_source_adjudication as adjudication  # noqa: E402
from scripts import sloan_v10_slopes as v10  # noqa: E402
from scripts import validate_translation_holdout as holdout  # noqa: E402
from scripts.translation_research_common import fit_table, sha256_file  # noqa: E402
from src.data.corpus import euroleague_api as api  # noqa: E402

KEY = common.KEY
FREEZE_SEASON = 2026  # stored destination season of 2026-27
SOURCE_SEASON = FREEZE_SEASON - 1
GATE_SEASON = 2025  # the freeze path pointed at the anchor's last season
DESTINATIONS = tuple(blf.CONTINENTAL)
#: Pre-registration, "Source data": 2025-26 data stop in early January 2026.
PARTIAL_SOURCE_LEAGUES = ("turkey-bsl", "france-pro-a", "vtb", "lithuania-lkl")
#: Pre-registration, "Source data": 2025-26 data complete on disk.
COMPLETE_SOURCE_LEAGUES = (
    "spain-acb",
    "germany-bbl",
    "greece-a1",
    "italy-lba",
    "israel-bsl",
)
SCORING_GAME_CUTOFF = dt.date(2026, 11, 24)
SCORING_REFRESH_FROM = dt.date(2026, 11, 25)
MIN_SCORED = 60
GATE_TOLERANCE = 1e-9
CORRECTION_SUMMARY = Path(
    "docs/research/artifacts/sloan-source-completion-2026-09-17/correction-summary.json"
)
#: Counts the September official-corrected reconstruction recorded; the control
#: path must land on the same canonical game population.
EXPECTED_COUNTS = {
    "raw_rows": 691645,
    "deduplicated_rows": 681890,
    "canonical_games": 626380,
    "identity_excluded": 118,
    "earlier_minute_repairs": 45,
}
SOURCE_COLUMNS = (
    "season_src",
    "league_src",
    "games_src",
    "minutes_src",
    "pir_src",
    "pir_per36_src",
    "club_src",
    "n_clubs_src",
    "prior_mean_pir36",
    "above_own_prior",
)
PRIMARY_CONTRASTS = {
    "P-a": ("history_only", "scheduled_history"),
    "P-b": ("scheduled_history", "source_ridge_10"),
    "P-c": ("source_ridge_10", "source_ridge_10_scheduled"),
}
FROZEN_COLUMNS = (
    "player_name",
    "season_src",
    "league_src",
    "club_src",
    "n_clubs_src",
    "games_src",
    "minutes_src",
    "pir_src",
    "pir_per36_src",
    "prior_mean_pir36",
    "above_own_prior",
    "source_positive_finite",
    "source_first_game_date",
    "source_last_game_date",
    "league_last_game_date",
    "source_partial_season",
    "source_complete_season",
    "source_disputed_fields",
    "season_dest",
    "league_dest",
    "scheduled_multiplier_value",
    "scheduled_fallback",
    "scheduled_k",
    "scheduled_translated",
    "transfer_translated",
    "feature_eligible",
)


class GateFailure(common.GateFailure):
    """A P1 gate did not hold; nothing is frozen or scored."""


# ---------------------------------------------------------------------------
# Inputs: the corpus on disk, with no 2026-27 path admitted.


def continental_paths(root: Path) -> list[Path]:
    """Every continental API season directory present (paths only, never read)."""
    found = []
    for competition in DESTINATIONS:
        base = Path(root) / "data" / "raw" / competition
        if base.exists():
            found.extend(sorted(p for p in base.iterdir() if p.name.isdigit()))
    return found


def assert_no_freeze_season_inputs(root: Path, paths=()) -> None:
    """Refuse, before any statistic is opened, if a 2026-27 path is an input."""
    if max(api.API_SEASONS) >= FREEZE_SEASON:
        raise GateFailure("the API loader would read the 2026-27 season")
    bad = [p for p in continental_paths(root) if int(p.name) >= FREEZE_SEASON]
    for path in paths:
        if any(
            part.isdigit() and int(part) >= FREEZE_SEASON for part in Path(path).parts
        ):
            bad.append(Path(path))
    if bad:
        raise GateFailure(
            f"freeze inputs contain {len(bad)} season->=2026 paths, e.g. {bad[0]}"
        )


def raw_paths(root: Path) -> list[Path]:
    return [
        path
        for pattern in blf._RAW_GLOBS
        for path in sorted(
            (Path(root) / "data/raw").glob(pattern.removeprefix("data/raw/"))
        )
        if "proballers/test/" not in path.as_posix()
    ]


def quarantine_scopes(root: Path) -> list[tuple[str, int]]:
    summary = json.loads((Path(root) / CORRECTION_SUMMARY).read_text())
    return sorted({(q["player_name"], int(q["season"])) for q in summary["quarantine"]})


def _relative(path: str, root: Path) -> str:
    resolved, base = Path(path).resolve(), Path(root).resolve()
    if resolved.is_relative_to(base):
        return resolved.relative_to(base).as_posix()
    parts = Path(path).parts
    return "/".join(parts[parts.index("data") :]) if "data" in parts else str(path)


def rebase_evidence(evidence: dict, root: Path) -> dict:
    """Point the minute evidence at this tree's copy of its raw file.

    The evidence records the absolute path of the September checkout; a
    retained run reads a copy. ``_repair_minutes`` still checks the copy's
    sha256 against the recorded hash, so only the location changes.
    """
    parts = Path(evidence["raw_source_file"]).parts
    relative = Path(*parts[parts.index("data") :])
    return {**evidence, "raw_source_file": str((Path(root) / relative).resolve())}


def corpus_games(root: Path, decisions_dir: Path | None = None):
    """The v10 canonical games, through the registered correction code.

    The official 2025 ACB field decisions are a local, hash-pinned file that is
    not in the repository. Without it the control path of
    ``sloan_corrected_sources.run`` is used: the same minute repair, duplicate
    rule and identity quarantine, without the 2025 ACB field corrections. That
    path reproduces every v10 cohort row (gate below); 2025-26 ACB rows carry a
    count of disputed fields instead.
    """
    root = Path(root)
    paths = raw_paths(root)
    assert_no_freeze_season_inputs(root, paths)
    raw, inventory = adjudication.load_raw(root / "data/raw")
    if int(raw.season.max()) >= FREEZE_SEASON:
        raise GateFailure("raw corpus holds a 2026-27 row")
    diagnosis = json.loads((acb.SOURCE / "source_diagnosis.json").read_text())
    evidence = rebase_evidence(
        json.loads((acb.SOURCE / "official_minute_evidence.json").read_text()), root
    )
    repaired, minute_rows = adjudication._repair_minutes(
        adjudication._prepare(raw), diagnosis, evidence
    )
    scopes = quarantine_scopes(root)
    decisions_used = False
    if decisions_dir is not None:
        decisions = json.loads((Path(decisions_dir) / "decisions.json").read_text())
        repaired, _ = corrected.apply_decisions(repaired, decisions, diagnosis)
        if corrected.collision_scopes(diagnosis, decisions) != scopes:
            raise GateFailure("decision scopes differ from the recorded quarantine")
        decisions_used = True
    duplicate = repaired.duplicated(adjudication.TEAM_KEY)
    kept = repaired.loc[~duplicate].copy()
    games, excluded = corrected.normalize_games(kept, scopes)
    counts = {
        "raw_rows": len(raw),
        "deduplicated_rows": len(kept),
        "canonical_games": len(games),
        "identity_excluded": len(excluded),
        "earlier_minute_repairs": len(minute_rows),
    }
    if counts != EXPECTED_COUNTS:
        raise GateFailure(f"corpus counts {counts} != recorded {EXPECTED_COUNTS}")
    disputed = (
        pd.DataFrame(
            [
                {
                    "player_name": blf.pairing_key(r["player_name"]),
                    "league": r["league"],
                    "season": int(r["values"][0]["season"]),
                }
                for r in diagnosis["field_disagreements"]
            ]
        )
        .value_counts()
        .rename("disputed_fields")
        .reset_index()
    )
    provenance = {
        "raw_inputs": [
            {
                "path": _relative(r["source_file"], root),
                "sha256": r["sha256"],
                "rows": r["rows"],
            }
            for r in inventory
        ],
        "api_seasons": list(api.API_SEASONS),
        "counts": counts,
        "quarantine_scopes": [list(s) for s in scopes],
        "acb_2025_official_decisions_applied": decisions_used,
    }
    return games, disputed, provenance


def aggregates(games: pd.DataFrame) -> pd.DataFrame:
    with contextlib.redirect_stdout(io.StringIO()):
        _, agg = holdout.build_switchers(games)
    return agg


def source_player_seasons(agg: pd.DataFrame, season: int) -> pd.DataFrame:
    """Every qualifying domestic source player-season, by the v10 cohort rules.

    The operations and their order are those of
    ``sloan_revision_analysis.reconstruct_cohort`` (threshold, then the
    largest-minutes source stint over the whole frame, then the cumulative
    prior), so ties resolve identically. Poland is the registered exclusion.
    """
    revision.unique(agg, ["player_name", "season", "league"])
    q = agg[(agg.games >= holdout.MIN_GAMES) & (agg.minutes > 0)]
    src = (
        q[~q.league.isin(blf.NOT_A_SOURCE)]
        .sort_values("minutes", ascending=False)
        .drop_duplicates(["player_name", "season"])
    )
    hist = (
        agg[agg.minutes > 0]
        .groupby(["player_name", "season"])[["pir", "minutes"]]
        .sum()
        .sort_index()
        .reset_index()
    )
    hist[["cum_pir", "cum_min"]] = hist.groupby("player_name")[
        ["pir", "minutes"]
    ].cumsum()
    hist["prior_mean_pir36"] = np.where(
        hist.cum_min > hist.minutes,
        36 * (hist.cum_pir - hist.pir) / (hist.cum_min - hist.minutes),
        np.nan,
    )
    rows = src.loc[src.season.eq(season)].copy()
    rows = rows.rename(
        columns={c: f"{c}_src" for c in rows.columns if c != "player_name"}
    )
    rows = rows.merge(
        hist[["player_name", "season", "prior_mean_pir36"]].rename(
            columns={"season": "season_src"}
        ),
        on=["player_name", "season_src"],
        how="left",
        validate="1:1",
    )
    rows["above_own_prior"] = rows.pir_per36_src > rows.prior_mean_pir36
    rows = rows.loc[~rows.league_src.isin(holdout.EXCLUDED_SOURCE)].copy()
    rows["source_positive_finite"] = np.isfinite(rows.pir_per36_src) & (
        rows.pir_per36_src > 0
    )
    revision.unique(rows, ["player_name"])
    return rows.sort_values("player_name").reset_index(drop=True)


def source_dates(games: pd.DataFrame, season: int):
    """First and last game date of each domestic player-season-league on disk."""
    frame = games.loc[games.season.eq(season), ["player_name", "league", "date"]]
    frame = frame.assign(
        date=pd.to_datetime(frame.date, format="%b %d, %Y", errors="coerce")
    )
    out = (
        frame.groupby(["player_name", "league"])
        .date.agg(["min", "max"])
        .rename(
            columns={"min": "source_first_game_date", "max": "source_last_game_date"}
        )
        .reset_index()
        .rename(columns={"league": "league_src"})
    )
    league_last = frame.groupby("league").date.max().rename("league_last_game_date")
    return out, league_last


def candidates(agg, games, disputed, season):
    """Source rows x both destinations, flagged; outcomes unknown (NaN)."""
    rows = source_player_seasons(agg, season)
    dates, league_last = source_dates(games, season)
    rows = rows.merge(
        dates, on=["player_name", "league_src"], how="left", validate="1:1"
    )
    rows["league_last_game_date"] = rows.league_src.map(league_last)
    rows["source_partial_season"] = rows.league_src.isin(PARTIAL_SOURCE_LEAGUES)
    rows["source_complete_season"] = rows.league_src.isin(COMPLETE_SOURCE_LEAGUES)
    d = disputed.rename(columns={"league": "league_src", "season": "season_src"})
    rows = rows.merge(
        d, on=["player_name", "league_src", "season_src"], how="left", validate="1:1"
    )
    rows["source_disputed_fields"] = rows.disputed_fields.fillna(0).astype(int)
    rows = rows.drop(columns="disputed_fields")
    return pd.concat(
        [
            rows.assign(
                season_dest=season + 1, league_dest=destination, pir_per36_dest=np.nan
            )
            for destination in DESTINATIONS
        ],
        ignore_index=True,
    )


def previous_continental(agg: pd.DataFrame, season: int) -> pd.DataFrame:
    """Season-``season`` continental aggregates, kept for the incumbency rule."""
    rows = agg.loc[
        agg.season.eq(season) & agg.league.isin(DESTINATIONS),
        ["player_name", "season", "league", "games", "minutes"],
    ]
    return rows.sort_values(["player_name", "league"]).reset_index(drop=True)


# ---------------------------------------------------------------------------
# The v10 forecast path for rows whose outcome is unknown.


def prospective_features(pairs, cohort, rows, *, fitter=fit_table):
    """Translated features for ``rows`` at their own cutoff, via refit_features.

    One call per destination keeps the cohort key (player, destination season)
    unique. Only cohort rows from earlier destination seasons enter factors,
    lag and pooling, exactly as for every historical row.
    """
    season = int(rows.season_dest.iloc[0])
    if rows.season_dest.ne(season).any():
        raise ValueError("one destination season at a time")
    history = cohort.loc[cohort.season_dest.lt(season)]
    out = []
    for _, group in rows.groupby("league_dest", sort=True):
        augmented = pd.concat([history, group], ignore_index=True)
        features, _ = refit.refit_features(pairs, augmented, fitter=fitter)
        out.append(features.loc[features.season_dest.eq(season)])
    history_features, _ = refit.refit_features(pairs, history, fitter=fitter)
    return pd.concat(out, ignore_index=True), history_features


def forecast_rows(train_features, test, season):
    """All 11 original and 6 cell-slope arms, trained on rows < season."""
    train = train_features.loc[
        train_features.season_dest.lt(season) & train_features.feature_eligible
    ].sort_values(KEY)
    test = (
        test.sort_values(["league_dest", "player_name"]).reset_index(drop=True).copy()
    )
    support = test.feature_eligible.astype(bool)
    info = {}
    fits = [(a, benchmark.fit_model) for a in common.ORIGINAL_ARMS] + [
        (a, v10.fit_model) for a in common.SLOPE_ARMS
    ]
    for arm, fit in fits:
        test[arm] = np.nan
        status = "feature_refusal"
        if support.any():
            prediction, diagnostic = fit(train, test.loc[support], arm)
            test.loc[support, arm] = prediction
            status = diagnostic["status"]
            info[arm] = {
                "status": status,
                "unseen_source_rows": diagnostic.get("unseen_source_rows"),
            }
        test[f"{arm}_status"] = np.where(support, status, "feature_refusal")
    test["all_arms_forecast"] = np.isfinite(test[list(common.ALL_ARMS)]).all(axis=1)
    return test, {"train_n": len(train), "arms": info}


def freeze_path(pairs, cohort, agg, games, disputed, season, *, fitter=fit_table):
    """The one prospective code path: candidates, features, all 17 arms."""
    rows = candidates(agg, games, disputed, season - 1)
    features, history_features = prospective_features(
        pairs, cohort, rows, fitter=fitter
    )
    return forecast_rows(history_features, features, season)


# ---------------------------------------------------------------------------
# Gates.


def assert_within(diffs: dict, tolerance: float = GATE_TOLERANCE) -> None:
    values = {k: (v if np.isfinite(v) else np.inf) for k, v in diffs.items()}
    worst = max(values, key=values.get)
    if not values[worst] <= tolerance:
        raise GateFailure(
            f"gate failed: {worst} differs by {values[worst]:.3e} (tolerance {tolerance:.0e})"
        )


def _column_difference(a: pd.Series, b: pd.Series) -> float:
    if pd.api.types.is_bool_dtype(a) or not pd.api.types.is_numeric_dtype(a):
        same = (a.astype(object) == b.astype(object)) | (a.isna() & b.isna())
        return float((~same).sum())
    x, y = a.to_numpy(float), b.to_numpy(float)
    delta = np.where(np.isnan(x) & np.isnan(y), 0.0, np.abs(x - y))
    return float(np.max(np.where(np.isnan(delta), np.inf, delta))) if len(x) else 0.0


def cohort_identity(agg, cohort) -> dict:
    """Rebuilt source rows equal the cohort's on every row and source column."""
    diffs, missing = {}, 0
    for season, group in cohort.groupby("season_dest"):
        rebuilt = source_player_seasons(agg, int(season) - 1)
        merged = group.merge(
            rebuilt, on="player_name", how="left", suffixes=("", "_rebuilt")
        )
        missing += int(merged.league_src_rebuilt.isna().sum())
        for column in SOURCE_COLUMNS:
            diffs[f"{column}@{int(season)}"] = _column_difference(
                merged[column], merged[f"{column}_rebuilt"]
            )
    diffs["missing_rows"] = float(missing)
    return diffs


def anchor_gate(frozen_rows, anchor) -> dict:
    """Freeze path at destination 2025 against the anchor's 2025 forecasts."""
    target = anchor.loc[anchor.season_dest.eq(GATE_SEASON)]
    merged = target[["player_name", "league_dest", *common.ALL_ARMS]].merge(
        frozen_rows[["player_name", "league_dest", *common.ALL_ARMS]],
        on=["player_name", "league_dest"],
        how="left",
        suffixes=("", "_freeze"),
        validate="1:1",
    )
    diffs = {}
    for arm in common.ALL_ARMS:
        delta = np.abs(merged[arm].to_numpy() - merged[f"{arm}_freeze"].to_numpy())
        diffs[arm] = float(np.max(np.where(np.isnan(delta), np.inf, delta)))
    return diffs, len(target)


def negative_control(diffs: dict) -> str:
    try:
        assert_within(diffs, tolerance=-1.0)
    except GateFailure:
        return "rejected as required"
    raise GateFailure("negative control passed an impossible tolerance")


# ---------------------------------------------------------------------------
# freeze


def _manifest_commit(root: Path) -> str | None:
    path = Path(root) / "MANIFEST.json"
    if path.is_file():
        return json.loads(path.read_text()).get("commit")
    return None


def freeze(root: Path, input_dir: Path, out: Path, decisions_dir: Path | None = None):
    root = Path(root)
    assert_no_freeze_season_inputs(root, raw_paths(root))
    v9, v10_summary = common.load_references(root)
    pairs, cohort = common.load_pool(input_dir, "official_corrected")
    if (
        int(pairs.season.max()) > SOURCE_SEASON
        or int(cohort.season_dest.max()) > SOURCE_SEASON
    ):
        raise GateFailure("training inputs reach past destination 2025")
    anchor, _, _ = common.anchor_rows(root, input_dir)
    g0 = common.g0_differences(anchor, v9, v10_summary)
    common.assert_g0(g0)
    games, disputed, provenance = corpus_games(root, decisions_dir)
    agg = aggregates(games)
    identity = cohort_identity(agg, cohort)
    gates = {"G0": {"status": "passed", "max_difference": max(g0.values())}}
    gates["cohort_identity"] = {
        "negative_control": negative_control(identity),
        "max_difference": max(identity.values()),
        "rows": len(cohort),
        "columns": list(SOURCE_COLUMNS),
    }
    assert_within(identity)
    gates["cohort_identity"]["status"] = "passed"
    # The freeze code pointed at destination 2025 (training <= 2024).
    gate_rows, _ = freeze_path(
        pairs,
        cohort.loc[cohort.season_dest.lt(GATE_SEASON)],
        agg,
        games,
        disputed,
        GATE_SEASON,
    )
    anchor_diffs, n_targets = anchor_gate(gate_rows, anchor)
    gates["anchor_2025"] = {
        "negative_control": negative_control(anchor_diffs),
        "max_difference": max(anchor_diffs.values()),
        "per_arm": anchor_diffs,
        "n_targets": n_targets,
        "tolerance": GATE_TOLERANCE,
    }
    assert_within(anchor_diffs)
    if n_targets != 127:
        raise GateFailure(f"anchor 2025 has {n_targets} targets, not 127")
    gates["anchor_2025"]["status"] = "passed"
    rows, info = freeze_path(pairs, cohort, agg, games, disputed, FREEZE_SEASON)
    if (
        rows.season_src.ne(SOURCE_SEASON).any()
        or rows.season_dest.ne(FREEZE_SEASON).any()
    ):
        raise GateFailure("frozen rows outside 2025 source / 2026 destination")
    out = Path(out)
    out.mkdir(parents=True, exist_ok=False)
    keep = [
        *FROZEN_COLUMNS,
        *common.ALL_ARMS,
        *[f"{a}_status" for a in common.ALL_ARMS],
        "all_arms_forecast",
    ]
    frozen = (
        rows[keep].sort_values(["league_dest", "player_name"]).reset_index(drop=True)
    )
    path = out / "p1_frozen_forecasts.parquet"
    frozen.to_parquet(path, index=False)
    incumbency = previous_continental(agg, SOURCE_SEASON)
    incumbency_path = out / "p1_incumbency_2025_continental.parquet"
    incumbency.to_parquet(incumbency_path, index=False)
    one = frozen.loc[frozen.league_dest.eq(DESTINATIONS[0])]
    per_league = (
        one.groupby("league_src")
        .agg(
            players=("player_name", "size"),
            partial=("source_partial_season", "first"),
            complete=("source_complete_season", "first"),
            league_last_game=("league_last_game_date", "first"),
            median_games=("games_src", "median"),
            nonpositive=("source_positive_finite", lambda s: int((~s).sum())),
        )
        .reset_index()
    )
    result = {
        "analysis": "P1 freeze",
        "status": "frozen",
        "protocol_commit": common.PROTOCOL_COMMIT,
        "protocol_sha256": sha256_file(root / common.PROTOCOL),
        "generating_commit": _manifest_commit(root),
        "forecast_file": path.name,
        "forecast_sha256": sha256_file(path),
        "incumbency_file": incumbency_path.name,
        "incumbency_sha256": sha256_file(incumbency_path),
        "rows": len(frozen),
        "source_player_seasons": int(one.player_name.nunique()),
        "destinations": list(DESTINATIONS),
        "rows_all_arms_forecast": int(frozen.all_arms_forecast.sum()),
        "rows_feature_refusal": int((~frozen.feature_eligible).sum()),
        "rows_source_nonpositive": int((~frozen.source_positive_finite).sum()),
        "rows_partial_source": int(frozen.source_partial_season.sum()),
        "rows_complete_source": int(frozen.source_complete_season.sum()),
        "rows_with_disputed_acb_fields": int((frozen.source_disputed_fields > 0).sum()),
        "per_source_league": json.loads(
            per_league.to_json(orient="records", date_format="iso")
        ),
        "training_rows": info["train_n"],
        "arm_status": info["arms"],
        "gates": gates,
        "corpus": provenance,
        "pairs_sha256": common.PAIRS_SHA["official_corrected"],
        "cohort_sha256": common.COHORT_SHA,
        "recipe": "R1 (fit_table: exposure-weighted, moment pooler, 75-pair floor)",
        "scoring_rule": {
            "games_dated_on_or_before": SCORING_GAME_CUTOFF.isoformat(),
            "files_refreshed_on_or_after": SCORING_REFRESH_FROM.isoformat(),
            "min_newcomers": MIN_SCORED,
            "incumbency": "qualifying (>= 8 games, positive minutes) 2025-26 continental stint, applied at scoring",
        },
        "limitations": (
            "2025-26 ACB rows use the control path without the local official "
            "2025 field decisions (counted per row in source_disputed_fields). "
            "Partial-season source leagues use the games on disk; "
            "league_last_game_date records where each league's data stop."
        ),
    }
    (out / "freeze.json").write_text(
        json.dumps(result, indent=2, sort_keys=True, default=str) + "\n"
    )
    print(
        f"P1 frozen: {len(frozen)} rows, {result['source_player_seasons']} player-seasons; "
        f"anchor gate max {gates['anchor_2025']['max_difference']:.3e}; "
        f"sha256 {result['forecast_sha256']}"
    )
    return result


# ---------------------------------------------------------------------------
# Scoring lives in scripts/sloan_fullpaper_prospective_score.py. This file is
# registered with a source-season envelope that ends at 2025, so the research
# harness cannot stage a 2026-27 file for it; the scoring entry has its own
# envelope and every control of the 3 Nov registration and of Amendments 8 and
# 15. The constants above (cutoff, refresh date, minimum n, primary contrasts)
# are the registered values both files share.


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    f = sub.add_parser("freeze")
    f.add_argument("--input-dir", type=Path, required=True)
    f.add_argument("--out", type=Path, required=True)
    f.add_argument("--decisions-dir", type=Path)
    sub.add_parser(
        "score", help="moved: run scripts/sloan_fullpaper_prospective_score.py score"
    )
    args, _ = parser.parse_known_args(argv)
    if args.command == "score":
        raise GateFailure(
            "P1 is scored by scripts/sloan_fullpaper_prospective_score.py (its own "
            "2026 season envelope and the registered controls), not by this file"
        )
    freeze(Path.cwd(), args.input_dir, args.out, args.decisions_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
