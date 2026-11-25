"""Immutable raw-source sensitivities for the pushed Sloan revalidation protocol.

Names in returned games remain raw. Normalized names are diagnostic/quarantine
keys only; the existing API destination adapter owns the eventual pairing keys.
Evidence is an explicit fixture-specific official roster mapping, never a parser
heuristic. This module neither changes source files nor runs predictive studies.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from urllib.parse import urlparse

import pandas as pd

from scripts import build_league_factors as blf

VARIANTS = (
    "baseline",
    "invalid_minutes_quarantine",
    "all_questioned_quarantine",
    "alternative_tree",
    "evidence_backed_repair",
)
RAW_KEY = ["game_id", "player_name", "league"]
TEAM_KEY = [*RAW_KEY, "team"]
GAME_KEY = ["game_id", "league"]
SEASON_KEY = ["normalized_name", "league", "season"]
REQUIRED_STATS = tuple(
    dict.fromkeys(
        ["minutes", "points", "rebounds", "assists", "steals", "blocks", "pir"]
        + list(blf.EXTRA_SUMS.values())
    )
)


def _sha256(path: Path) -> str:
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def _records(frame: pd.DataFrame) -> list[dict]:
    """Convert numpy values and missing cells to strict JSON-compatible values."""
    return json.loads(frame.to_json(orient="records", date_format="iso"))


def load_raw(raw_root: Path) -> tuple[pd.DataFrame, list[dict]]:
    """Read both historical trees in legacy order with immutable-file checks.

    ``raw_root`` is the directory containing ``proballers`` and
    ``_inactive_leagues``, conventionally ``PROJECT_ROOT / 'data/raw'``.
    """
    frames, inventory = [], []
    for priority, pattern in enumerate(blf._RAW_GLOBS):
        for path in sorted(raw_root.glob(pattern.removeprefix("data/raw/"))):
            if "proballers/test/" in path.as_posix():
                continue
            before = _sha256(path)
            frame = pd.read_parquet(path)
            if before != _sha256(path):
                raise ValueError(f"Raw source changed while reading: {path}")
            if {"_source_file", "_priority"} & set(frame.columns):
                raise ValueError(f"Reserved provenance columns in {path}")
            frame["_source_file"] = str(path.resolve())
            frame["_priority"] = priority
            frames.append(frame)
            inventory.append(
                dict(
                    source_file=str(path.resolve()),
                    sha256=before,
                    priority=priority,
                    rows=len(frame),
                )
            )
    if not frames:
        raise ValueError(f"No player_stats parquets under {raw_root}")
    return pd.concat(frames, ignore_index=True), inventory


def _prepare(raw: pd.DataFrame) -> pd.DataFrame:
    missing = set(
        TEAM_KEY
        + ["season", "date", "_source_file", "_priority"]
        + list(REQUIRED_STATS)
    ) - set(raw.columns)
    if missing:
        raise ValueError(f"Missing raw columns: {sorted(missing)}")
    frame = raw.copy().reset_index(drop=True)
    frame["normalized_name"] = frame.player_name.map(blf.pairing_key)
    frame["_raw_row_id"] = frame.index
    return frame


def diagnose(raw: pd.DataFrame) -> dict:
    """Return complete JSON tables, separating identity from numeric conflicts."""
    frame = _prepare(raw)
    fatal = []
    identity_columns = TEAM_KEY + ["season", "date", "normalized_name"]
    if frame[identity_columns].isna().any().any() or frame.normalized_name.eq("").any():
        fatal.append({"reason": "missing_identity_or_calendar"})
    duplicate = frame.duplicated(TEAM_KEY + ["_source_file"], keep=False)
    if duplicate.any():
        fatal.append(
            {
                "reason": "duplicate_team_identity_within_file",
                "rows": _records(frame.loc[duplicate]),
            }
        )
    calendars = frame.groupby(GAME_KEY, dropna=False)[["season", "date"]].nunique(
        dropna=False
    )
    for key in calendars.index[(calendars > 1).any(axis=1)]:
        rows = frame.set_index(GAME_KEY).loc[[key]].reset_index()
        fatal.append(
            {
                "reason": "game_date_or_season_disagreement",
                "rows": _records(
                    rows[
                        GAME_KEY + ["season", "date", "_source_file", "_priority"]
                    ].drop_duplicates()
                ),
            }
        )
    collision_key = ["game_id", "league", "normalized_name"]
    teams = frame.groupby(collision_key, dropna=False).team.nunique(dropna=False)
    collisions = []
    for key in teams.index[teams > 1]:
        rows = frame.set_index(collision_key).loc[[key]].reset_index()
        collisions.append(
            {
                **dict(zip(collision_key, key, strict=True)),
                "rows": _records(
                    rows[TEAM_KEY + ["season", "_source_file", "_priority"]]
                ),
            }
        )
    negative_keys = frame.loc[frame.minutes < 0, GAME_KEY].drop_duplicates()
    negative_games = []
    for key in negative_keys.itertuples(index=False, name=None):
        rows = frame.set_index(GAME_KEY).loc[[key]].reset_index()
        negative_games.append(
            {
                **dict(zip(GAME_KEY, key, strict=True)),
                "negative_rows": int((rows.minutes < 0).sum()),
                "rows": _records(
                    rows[TEAM_KEY + ["season", "minutes", "_source_file", "_priority"]]
                ),
            }
        )
    numeric = set(frame.select_dtypes(include="number").columns) - {
        "season",
        "_priority",
        "_raw_row_id",
    }
    fields = sorted(numeric | set(REQUIRED_STATS))
    disagreements = []
    overlaps = frame.loc[frame.duplicated(TEAM_KEY, keep=False)]
    for key, rows in overlaps.groupby(TEAM_KEY, sort=True, dropna=False):
        if rows._priority.nunique() < 2:
            continue
        for field in fields:
            if rows[field].nunique(dropna=False) > 1:
                disagreements.append(
                    {
                        **dict(zip(TEAM_KEY, key, strict=True)),
                        "normalized_name": rows.normalized_name.iloc[0],
                        "field": field,
                        "required": field in REQUIRED_STATS,
                        "values": _records(
                            rows[["season", field, "_source_file", "_priority"]].rename(
                                columns={field: "value"}
                            )
                        ),
                    }
                )
    return {
        "status": "failed" if fatal else "complete",
        "fatal_errors": fatal,
        "negative_games": negative_games,
        "identity_collisions": collisions,
        "field_disagreements": disagreements,
        "counts": {
            "raw_rows": len(frame),
            "negative_rows": int((frame.minutes < 0).sum()),
            "negative_games": len(negative_games),
            "identity_collisions": len(collisions),
            "field_disagreements": len(disagreements),
        },
    }


def _official_url(value: object) -> bool:
    """Only the supplied ACB official evidence schema is currently supported."""
    if not isinstance(value, str):
        return False
    parsed = urlparse(value)
    return parsed.scheme == "https" and (
        parsed.hostname == "acb.com" or (parsed.hostname or "").endswith(".acb.com")
    )


def _repair_minutes(
    frame: pd.DataFrame, diagnosis: dict, evidence: dict | None
) -> tuple[pd.DataFrame, list[dict]]:
    if not evidence or evidence.get("schema_version") != 1:
        raise ValueError("Missing supported official minute evidence")
    source = evidence.get("raw_source_file")
    if not source or not evidence.get("raw_sha256"):
        raise ValueError("Evidence lacks raw source and SHA-256")
    # Verify against the actual input bytes, not an unrelated file with a matching name.
    paths = frame._source_file.unique()
    if source not in paths or _sha256(Path(source)) != evidence["raw_sha256"]:
        raise ValueError("Evidence raw source/hash does not match input")
    expected = {
        (str(item["game_id"]), item["league"]) for item in diagnosis["negative_games"]
    }
    seen, repairs = set(), []
    out = frame.copy()
    for game in evidence.get("games", []):
        game_id = str(game.get("raw_game_id"))
        subset = frame.loc[frame.game_id.astype(str).eq(game_id)]
        if subset.empty or subset.league.nunique() != 1:
            raise ValueError(f"Wrong or ambiguous evidence game: {game_id}")
        key = (game_id, subset.league.iloc[0])
        if key not in expected or key in seen:
            raise ValueError(f"Unexpected or duplicate evidence game: {game_id}")
        seen.add(key)
        if not _official_url(game.get("source_url")) or not game.get(
            "official_game_id"
        ):
            raise ValueError(f"Unverified official game: {game_id}")
        if set(subset._source_file) != {source}:
            raise ValueError(f"Evidence does not cover all source copies: {game_id}")
        actual_dates = pd.to_datetime(subset.date, format="mixed", errors="coerce")
        official_date = pd.to_datetime(game.get("date"), errors="coerce")
        if (
            pd.isna(official_date)
            or actual_dates.isna().any()
            or not actual_dates.eq(official_date).all()
        ):
            raise ValueError(f"Evidence date mismatch: {game_id}")
        team_map = {
            game.get("home_team_raw"): game.get("home_team_official"),
            game.get("away_team_raw"): game.get("away_team_official"),
        }
        if set(subset.team) != set(team_map) or not all(team_map.values()):
            raise ValueError(f"Evidence teams mismatch: {game_id}")
        roster = game.get("rows", [])
        roster_keys = [(r.get("raw_player_name"), r.get("raw_team")) for r in roster]
        expected_roster = set(
            subset[["player_name", "team"]].itertuples(index=False, name=None)
        )
        if (
            len(roster_keys) != len(set(roster_keys))
            or set(roster_keys) != expected_roster
        ):
            raise ValueError(f"Incomplete or duplicate evidence roster: {game_id}")
        if game.get("unmatched_raw_rows") or game.get("raw_rows_matched") != len(
            expected_roster
        ):
            raise ValueError(f"Incomplete raw coverage declaration: {game_id}")
        official_ids = [r.get("official_player_id") for r in roster]
        if any(not value for value in official_ids) or len(set(official_ids)) != len(
            official_ids
        ):
            raise ValueError(f"Ambiguous official player identity: {game_id}")
        for row in roster:
            stamp = row.get("official_minutes_mm_ss", "")
            if not isinstance(stamp, str) or not re.fullmatch(r"\d{2}:[0-5]\d", stamp):
                raise ValueError(f"Invalid official MM:SS: {stamp!r}")
            if (
                not row.get("match_basis", "").strip()
                or not _official_url(row.get("official_player_url"))
                or row.get("official_team") != team_map[row["raw_team"]]
            ):
                raise ValueError(f"Unverified roster identity: {game_id}")
            selected = subset.loc[
                subset.player_name.eq(row["raw_player_name"])
                & subset.team.eq(row["raw_team"])
            ]
            if len(selected) != 1 or selected.minutes.iloc[0] != row.get("raw_minutes"):
                raise ValueError(f"Raw minute/mapping mismatch: {game_id}")
            mm, ss = map(int, stamp.split(":"))
            minutes = mm + ss / 60
            out.loc[selected.index, "minutes"] = minutes
            repairs.append(
                {
                    "game_id": game_id,
                    "league": key[1],
                    "player_name": row["raw_player_name"],
                    "team": row["raw_team"],
                    "old_minutes": row["raw_minutes"],
                    "minutes": minutes,
                    "official_minutes_mm_ss": stamp,
                    "source_url": game["source_url"],
                    "official_player_url": row["official_player_url"],
                    "identity_rationale": row["match_basis"],
                }
            )
        for row in game.get("official_only_rows", []):
            if row.get("official_minutes_mm_ss") != "00:00":
                raise ValueError(f"Unmatched official participant: {game_id}")
    if seen != expected:
        raise ValueError("Evidence missing a suspect game's complete roster")
    return out, repairs


def apply_variant(
    raw: pd.DataFrame, variant: str, evidence: dict | None = None
) -> tuple[pd.DataFrame, dict]:
    """Produce a research copy and exhaustive row/season conservation ledger.

    Fatal input inconsistencies raise ``ValueError`` for corrective variants.
    Missing or inadmissible repair evidence returns an empty frame and a
    ``status='not_run'`` report, so callers cannot accidentally study guesses.
    """
    if variant not in VARIANTS:
        raise ValueError(f"Unknown variant: {variant}")
    frame = _prepare(raw)
    diagnosis = diagnose(raw)
    if variant != "baseline" and diagnosis["fatal_errors"]:
        raise ValueError(f"Source diagnosis failed closed: {diagnosis['fatal_errors']}")
    report = {
        "variant": variant,
        "status": "complete",
        "repair_rows": [],
        "quarantine_player_seasons": [],
        "ambiguous_normalized_names": [],
    }
    if variant == "evidence_backed_repair":
        try:
            frame, report["repair_rows"] = _repair_minutes(frame, diagnosis, evidence)
        except (ValueError, OSError, TypeError, KeyError) as exc:
            return raw.iloc[:0].copy(), {
                **report,
                "status": "not_run",
                "errors": [str(exc)],
            }
    reasons = pd.Series("", index=frame.index, dtype="str")
    seasons = {}
    if variant != "baseline":
        names = sorted(
            {item["normalized_name"] for item in diagnosis["identity_collisions"]}
        )
        report["ambiguous_normalized_names"] = names
        reasons.loc[frame.normalized_name.isin(names)] = "ambiguous_normalized_identity"
        if variant != "evidence_backed_repair":
            bad_games = {
                (item["game_id"], item["league"])
                for item in diagnosis["negative_games"]
            }
            affected = frame.loc[
                pd.MultiIndex.from_frame(frame[GAME_KEY]).isin(bad_games)
            ]
            for key in affected.loc[
                ~affected.league.isin(blf.CONTINENTAL), SEASON_KEY
            ].itertuples(index=False, name=None):
                seasons.setdefault(key, set()).add("whole_game_invalid_minutes")
        if variant in ("all_questioned_quarantine", "evidence_backed_repair"):
            for conflict in diagnosis["field_disagreements"]:
                if conflict["required"] and conflict["league"] not in blf.CONTINENTAL:
                    for value in conflict["values"]:
                        key = (
                            conflict["normalized_name"],
                            conflict["league"],
                            value["season"],
                        )
                        seasons.setdefault(key, set()).add(
                            f"cross_tree_{conflict['field']}"
                        )
        for key, why in sorted(seasons.items()):
            report["quarantine_player_seasons"].append(
                {**dict(zip(SEASON_KEY, key, strict=True)), "reasons": sorted(why)}
            )
        season_reasons = {key: ";".join(sorted(why)) for key, why in seasons.items()}
        reasons = pd.Series(
            [
                ";".join(filter(None, [old, season_reasons.get(key, "")]))
                for old, key in zip(
                    reasons,
                    frame[SEASON_KEY].itertuples(index=False, name=None),
                    strict=True,
                )
            ],
            index=frame.index,
            dtype="str",
        )
    kept = frame.loc[reasons.eq("")]
    if variant == "alternative_tree":
        kept = kept.sort_values("_priority", ascending=False, kind="stable")
    duplicate = kept.duplicated(RAW_KEY if variant == "baseline" else TEAM_KEY)
    reasons.loc[kept.index[duplicate]] = (
        "historical_duplicate"
        if variant == "baseline"
        else "team_aware_source_duplicate"
    )
    kept = kept.loc[~duplicate]
    ledger_columns = TEAM_KEY + ["season", "_source_file", "_priority", "_raw_row_id"]
    dropped = frame.loc[reasons.ne(""), ledger_columns].copy()
    dropped["reason"] = reasons.loc[dropped.index]
    report["dropped_raw_keys"] = _records(dropped)
    # Row IDs are input positions in deterministic historical file order. The
    # digest uses the full identity/provenance ledger but keeps reports bounded.
    report["retained_keys_digest"] = {
        "algorithm": "sha256",
        "serialization": (
            "UTF-8 pandas to_json(orient=records,date_format=iso,"
            "double_precision=15,force_ascii=True), sorted by _raw_row_id"
        ),
        "columns": ledger_columns,
        "rows": len(kept),
        "sha256": hashlib.sha256(
            kept[ledger_columns]
            .sort_values("_raw_row_id")
            .to_json(orient="records", date_format="iso", double_precision=15)
            .encode("utf-8")
        ).hexdigest(),
    }
    report["counts"] = {
        "input_rows": len(frame),
        "output_rows": len(kept),
        "dropped_rows": len(dropped),
        "repaired_rows": len(report["repair_rows"]),
        "quarantined_player_seasons": len(seasons),
    }
    input_ids = set(frame._raw_row_id)
    kept_ids, dropped_ids = set(kept._raw_row_id), set(dropped._raw_row_id)
    report["conservation"] = {
        "input_equals_retained_plus_dropped": input_ids == kept_ids | dropped_ids,
        "retained_dropped_disjoint": not bool(kept_ids & dropped_ids),
        "output_raw_keys_unique": not kept.duplicated(
            RAW_KEY if variant == "baseline" else TEAM_KEY
        ).any(),
    }
    report["remaining_negative_rows"] = int((kept.minutes < 0).sum())
    report["remaining_identity_collisions"] = int(
        (
            kept.groupby(["game_id", "league", "normalized_name"]).team.nunique() > 1
        ).sum()
    )
    return kept[list(raw.columns)].reset_index(drop=True), report
