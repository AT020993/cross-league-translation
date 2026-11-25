# ruff: noqa: E402
"""Registered same-club evidence and overlapping-appearance sensitivity.

Threats: name/club guesses, equal-score fixture collisions, missing birthdays,
duplicate fixtures, calendar fan-out, outcome-selected support and source reuse.
Crosswalks require two component-matched fixtures and independent profile DOBs.
They are observational evidence, not contracts or complete historical coverage.
"""

from __future__ import annotations

# Input identity must be checked before scientific imports or output creation.
if __name__ == "__main__":
    import sys as _research_sys
    from pathlib import Path as _ResearchPath

    _research_sys.path.insert(0, str(_ResearchPath(__file__).resolve().parents[1]))
    from src.research.execution import enter as _enter_research

    _enter_research(__file__)


import argparse
import json
import logging
from pathlib import Path
import re
import shutil
import sys
import unicodedata

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts import build_league_factors as blf  # noqa: E402
from scripts.translation_research_common import sha256_file  # noqa: E402
from src.data.corpus import euroleague_api as api  # noqa: E402
from src.utils.player_ids import box_player_id  # noqa: E402

PROTOCOL = ROOT / "docs/research/sloan-same-club-evidence-amendment-2026-09-17.md"
COUNTS = {
    "points": "Points",
    "rebounds": "TotalRebounds",
    "assists": "Assistances",
    "steals": "Steals",
    "blocks": "BlocksFavour",
    "turnovers": "Turnovers",
    "fouls": "FoulsCommited",
    "fg_made": "FieldGoalsMade2",
    "fg_attempted": "FieldGoalsAttempted2",
    "fg3_made": "FieldGoalsMade3",
    "fg3_attempted": "FieldGoalsAttempted3",
    "ft_made": "FreeThrowsMade",
    "ft_attempted": "FreeThrowsAttempted",
    "offensive_rebounds": "OffensiveRebounds",
    "defensive_rebounds": "DefensiveRebounds",
}


def strict_name(value):
    """Normalize order/diacritics/punctuation, deliberately retaining suffixes."""
    if not isinstance(value, str) or not value.strip():
        return None
    value = api.api_name_to_first_last(value)
    text = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", re.sub(r"[^A-Z0-9]", " ", text.upper())).strip() or None


def dates(series):
    return (
        pd.to_datetime(series, format="mixed", errors="coerce", utc=True)
        .dt.tz_localize(None)
        .dt.normalize()
    )


def require_unique(frame, keys, label):
    if frame[keys].isna().any().any() or frame.duplicated(keys).any():
        raise ValueError(f"nonunique or missing {label}: {keys}")


def match_calendars(provider, official):
    """Match immutable fixture identities without using inferred club aliases."""
    left, right = provider.copy(), official.copy()
    require_unique(left, ["game_id"], "provider fixture")
    require_unique(right, ["gameCode"], "official fixture")
    left["day"], right["day"] = dates(left.date), dates(right.date)
    right = right.rename(columns={"homescore": "home_score", "awayscore": "away_score"})
    keys = ["day", "home_score", "away_score"]
    for table in (left, right):
        for key in ("home_score", "away_score"):
            table[key] = pd.to_numeric(table[key], errors="coerce")
    left_bad = left[keys].isna().any(axis=1) | left.duplicated(keys, keep=False)
    right_bad = right[keys].isna().any(axis=1) | right.duplicated(keys, keep=False)
    matched = left.loc[~left_bad].merge(
        right.loc[~right_bad, [*keys, "gameCode", "homecode", "awaycode"]],
        on=keys,
        how="inner",
        validate="1:1",
    )
    return matched, {
        "provider_fixtures": len(left),
        "official_fixtures": len(right),
        "provider_ambiguous_or_missing": int(left_bad.sum()),
        "official_ambiguous_or_missing": int(right_bad.sum()),
        "matched": len(matched),
    }


def profile_maps(provider, official):
    pb, el = provider.copy(), official.copy()
    pb["name_key"] = pb.name.map(strict_name)
    pb["dob"] = dates(pb.birth_date).dt.strftime("%Y-%m-%d")
    numeric_id = pd.to_numeric(pb.proballers_id, errors="coerce")
    pb["valid_id"] = (
        numeric_id.notna()
        & np.isfinite(numeric_id)
        & numeric_id.gt(0)
        & numeric_id.eq(np.floor(numeric_id))
    )
    pb["canonical_id"] = numeric_id.where(pb.valid_id).astype("Int64").astype("string")
    el["dob"] = dates(el.birth_date).dt.strftime("%Y-%m-%d")
    pb_map, el_map = {}, {}
    for name, group in pb.groupby("name_key", sort=True):
        unique = group[["canonical_id", "dob"]].drop_duplicates()
        if group.valid_id.all() and len(unique) == 1 and unique.dob.notna().all():
            pb_map[name] = (str(unique.iloc[0].canonical_id), unique.iloc[0].dob)
    for person, group in el.groupby("person_code", sort=True):
        valid = group.dob.dropna().unique()
        if (
            isinstance(person, str)
            and person.strip()
            and len(valid) == 1
            and group.dob.notna().all()
        ):
            # The retained people endpoint omits the box-score P prefix.
            el_map[box_player_id(person)] = valid[0]
    return pb_map, el_map


def matched_players(fixtures, provider, official, pb_profiles, el_profiles):
    """Return evidence, including rejected component/DOB comparisons."""
    pb, el = provider.copy(), api.drop_non_player_rows(official).copy()
    pb["game_id"] = pb.game_id.astype(str)
    el["Gamecode"] = pd.to_numeric(el.Gamecode, errors="raise").astype(int)
    el["Player_ID"] = el.Player_ID.astype("string").str.strip()
    require_unique(pb, ["game_id", "team", "player_name"], "provider player-game")
    require_unique(el, ["Gamecode", "Team", "Player_ID"], "official player-game")
    pb["name_key"], el["name_key"] = (
        pb.player_name.map(strict_name),
        el.Player.map(strict_name),
    )
    pbg = {str(k): g for k, g in pb.groupby("game_id", sort=False)}
    elg = {int(k): g for k, g in el.groupby("Gamecode", sort=False)}
    evidence, clubs = [], []
    for fixture in fixtures.itertuples(index=False):
        left, right = pbg.get(str(fixture.game_id)), elg.get(int(fixture.gameCode))
        if left is None or right is None:
            continue
        totals = left.groupby("team").points.sum(min_count=1)
        if len(totals) != 2 or fixture.home_score == fixture.away_score:
            continue
        home = totals[totals.eq(fixture.home_score)]
        away = totals[totals.eq(fixture.away_score)]
        if len(home) != 1 or len(away) != 1:
            continue
        bindings = [
            (home.index[0], str(fixture.homecode)),
            (away.index[0], str(fixture.awaycode)),
        ]
        fixture_clubs, fixture_evidence = [], []
        for raw_club, code in bindings:
            side_pb, side_el = (
                left[left.team.eq(raw_club)],
                right[right.Team.astype(str).eq(code)],
            )
            for player in side_pb.to_dict("records"):
                candidates = side_el[side_el.name_key.eq(player["name_key"])]
                record = {
                    "game_id": str(fixture.game_id),
                    "game_code": int(fixture.gameCode),
                    "day": fixture.day.isoformat(),
                    "raw_name": player["player_name"],
                    "raw_club": raw_club,
                    "club_code": code,
                    "name_key": player["name_key"],
                    "person_code": None,
                    "provider_id": None,
                    "dob": None,
                    "status": "ambiguous_or_missing_name",
                }
                if len(candidates) == 1:
                    target = candidates.iloc[0]
                    record["person_code"] = str(target.Player_ID)
                    a = pd.to_numeric(
                        pd.Series({k: player[k] for k in COUNTS}), errors="coerce"
                    )
                    b = pd.to_numeric(
                        pd.Series({k: target[v] for k, v in COUNTS.items()}),
                        errors="coerce",
                    )
                    if (
                        not np.isfinite(a).all()
                        or not np.isfinite(b).all()
                        or not np.array_equal(a.to_numpy(), b.to_numpy())
                    ):
                        record["status"] = "component_mismatch"
                    else:
                        record["status"] = "components_match_profile_missing"
                        profile = pb_profiles.get(player["name_key"])
                        birthday = el_profiles.get(str(target.Player_ID))
                        if profile and birthday:
                            record.update(provider_id=profile[0], dob=profile[1])
                            record["status"] = (
                                "matched" if profile[1] == birthday else "dob_mismatch"
                            )
                fixture_evidence.append(record)
            fixture_clubs.append(
                {
                    "game_id": str(fixture.game_id),
                    "raw_club": raw_club,
                    "club_code": code,
                }
            )
        # A full component/name match corroborates the otherwise ambiguous club labels.
        if any(
            r["status"]
            in ("matched", "components_match_profile_missing", "dob_mismatch")
            for r in fixture_evidence
        ):
            clubs.extend(fixture_clubs)
            evidence.extend(fixture_evidence)
    return pd.DataFrame(evidence), pd.DataFrame(clubs)


def accept_crosswalk(evidence, club_evidence):
    columns = [
        "competition",
        "season",
        "raw_name",
        "raw_club",
        "person_code",
        "club_code",
        "provider_id",
        "dob",
        "matched_fixtures",
        "status",
    ]
    if evidence.empty:
        return pd.DataFrame(columns=columns)
    records = []
    group_keys = ["competition", "season", "raw_name", "raw_club"]
    for key, group in evidence.groupby(group_keys, sort=True):
        known = group[group.person_code.notna()]
        accepted = group[group.status.eq("matched")]
        club_rows = club_evidence[
            (club_evidence.competition == key[0])
            & (club_evidence.season == key[1])
            & (club_evidence.raw_club == key[3])
        ]
        row = dict(zip(group_keys, key))
        row.update(
            person_code=None,
            club_code=None,
            provider_id=None,
            dob=None,
            matched_fixtures=accepted.game_id.nunique(),
            status="insufficient_verified_fixtures",
        )
        if known.person_code.nunique() != 1 or club_rows.club_code.nunique() != 1:
            row["status"] = "conflicting_identity_or_club"
        elif group.status.eq("dob_mismatch").any():
            row["status"] = "dob_mismatch"
        elif accepted.game_id.nunique() >= 2:
            identities = accepted[
                ["person_code", "club_code", "provider_id", "dob"]
            ].drop_duplicates()
            if len(identities) == 1:
                row.update(
                    identities.iloc[0].to_dict(),
                    status="verified_observational_crosswalk",
                )
            else:
                row["status"] = "conflicting_profile"
        records.append(row)
    return pd.DataFrame(records, columns=columns)


def official_index(raw, calendar, competition, season):
    """Bind observed API appearances to dated fixture and person identities."""
    people = api.drop_non_player_rows(raw).copy()
    require_unique(people, ["Gamecode", "Team", "Player_ID"], "API appearance")
    require_unique(calendar, ["gameCode"], "API calendar")
    calendar = calendar[["gameCode", "date"]].copy()
    calendar["date"] = dates(calendar.date)
    people = people.merge(
        calendar, left_on="Gamecode", right_on="gameCode", how="left", validate="m:1"
    )
    result = pd.DataFrame(
        {
            "game_id": "api-"
            + competition
            + "-"
            + str(season)
            + "-"
            + people.Gamecode.astype(str),
            "team": people.Team.astype(str),
            "player_name": people.Player.map(api.pairing_key),
            "person_code": people.Player_ID.astype(str).str.strip(),
            "official_date": people.date,
        }
    )
    # A normalized name collision must not be joined, even inside one fixture.
    result["ambiguous"] = result.duplicated(
        ["game_id", "team", "player_name"], keep=False
    )
    return result


def construct_evidence(source_root):
    """Only read retained files; record unavailable seasons instead of guessing."""
    source_root = Path(source_root)
    used = {}

    def read(path):
        used[str(path)] = sha256_file(path)
        return pd.read_parquet(path)

    bios = sorted(
        (source_root / "data/raw/proballers").glob("*/2025/player_bios_*.parquet")
    )
    bios += sorted(
        (source_root / "data/raw/_inactive_leagues/proballers").glob(
            "*/2025/player_bios_*.parquet"
        )
    )
    if not bios:
        raise FileNotFoundError("retained provider profiles missing")
    official_bio = read(source_root / "data/processed/player_bio.parquet")
    official_bio = official_bio.loc[official_bio._source.eq("euroleague_api_people")]
    pb_profiles, el_profiles = profile_maps(
        pd.concat([read(p) for p in bios], ignore_index=True), official_bio
    )
    all_evidence, all_clubs, all_indices, inventory = [], [], [], []
    for competition in ("euroleague", "eurocup"):
        for season in range(2016, 2026):
            pbdir = source_root / "data/raw/proballers" / competition / str(season)
            apidir = source_root / "data/raw" / competition / str(season)
            paths = [
                pbdir / f"games_{competition}_{season}.parquet",
                pbdir / f"player_stats_{competition}_{season}.parquet",
                apidir / "games" / f"season_{season}_games.parquet",
            ]
            boxes = sorted((apidir / "boxscores").glob("*.parquet"))
            row = {"competition": competition, "season": season}
            if not boxes or not paths[2].exists():
                row.update(status="official_calendar_or_boxscores_missing")
                inventory.append(row)
                continue
            calendar = read(paths[2])
            raw = pd.concat([read(p) for p in boxes], ignore_index=True)
            all_indices.append(official_index(raw, calendar, competition, season))
            if not paths[0].exists() or not paths[1].exists():
                row.update(status="provider_calendar_or_boxscores_missing")
                inventory.append(row)
                continue
            fixtures, stats = read(paths[0]), read(paths[1])
            matched, diagnostics = match_calendars(fixtures, calendar)
            evidence, clubs = matched_players(
                matched, stats, raw, pb_profiles, el_profiles
            )
            for frame in (evidence, clubs):
                frame["competition"], frame["season"] = competition, season
            all_evidence.append(evidence)
            all_clubs.append(clubs)
            row.update(
                status="examined", **diagnostics, player_comparisons=len(evidence)
            )
            inventory.append(row)
    if not all_indices:
        raise ValueError("no observed official appearance dates")
    evidence = (
        pd.concat(all_evidence, ignore_index=True) if all_evidence else pd.DataFrame()
    )
    clubs = pd.concat(all_clubs, ignore_index=True) if all_clubs else pd.DataFrame()
    index = pd.concat(all_indices, ignore_index=True)
    return evidence, clubs, index, pd.DataFrame(inventory), used


def window_pair(domestic, continental, mapping, *, min_games=8):
    """Reaggregate one verified identity using full-game usage denominators."""
    dom, dest = domestic.copy(), continental.copy()
    if dom.empty or dest.empty:
        return None, "missing_appearance_side", {}
    if dom.team.nunique() != 1 or dest.team.nunique() != 1:
        return None, "multiple_clubs", {}
    if mapping.empty or not mapping.status.eq("verified_observational_crosswalk").all():
        return None, "unverified_identity", {}
    identities = mapping[["person_code", "club_code"]].drop_duplicates()
    if len(identities) != 1:
        return None, "conflicting_crosswalk", {}
    person, club = identities.iloc[0].astype(str)
    if (
        dest.person_code.isna().any()
        or not dest.person_code.astype(str).eq(person).all()
    ):
        return None, "different_or_missing_person", {}
    if not dest.team.astype(str).eq(club).all():
        return None, "different_club", {}
    dom["date"], dest["date"] = dates(dom.date), dates(dest.official_date)
    if dom.date.isna().any() or dest.date.isna().any():
        return None, "missing_appearance_date", {}
    for frame in (dom, dest):
        require_unique(frame, ["game_id"], "window player fixture")
    start = max(dom.date.min(), dest.date.min())
    end = min(dom.date.max(), dest.date.max())
    detail = {
        "person_code": person,
        "club_code": club,
        "window_start": start.isoformat(),
        "window_end": end.isoformat(),
        "games_before_src": len(dom),
        "games_before_dest": len(dest),
    }
    if start > end:
        return None, "no_common_window", detail
    dom, dest = dom[dom.date.between(start, end)], dest[dest.date.between(start, end)]
    detail.update(games_window_src=len(dom), games_window_dest=len(dest))
    if len(dom) < min_games or len(dest) < min_games:
        return None, "fewer_than_eight_after_trimming", detail
    combined = pd.concat([dom, dest], ignore_index=True)
    if (
        combined.minutes.isna().any()
        or not np.isfinite(combined.minutes).all()
        or combined.minutes.le(0).any()
    ):
        return None, "invalid_appearance_minutes", detail
    original_name = str(combined.player_name.iloc[0])
    combined["player_name"] = "api:" + person
    combined["team"] = club
    pair = blf.build_pairs(combined, min_games=min_games)
    if len(pair) != 1:
        raise ValueError("verified identity window did not yield exactly one pair")
    pair["player_name"] = original_name
    for key, value in detail.items():
        pair[key] = value
    return pair, "included", detail


def build_windows(games, pairs, crosswalk, index):
    required = ["raw_player_name", "raw_team", "poss", "team_poss", "team_minutes"]
    if any(col not in games for col in required):
        raise ValueError(
            "corrected games lack raw identity or complete-game usage provenance"
        )
    require_unique(pairs, ["player_name", "season"], "corrected pair")
    require_unique(
        crosswalk, ["competition", "season", "raw_name", "raw_club"], "crosswalk"
    )
    good_index = index.loc[~index.ambiguous].drop(columns="ambiguous")
    require_unique(good_index, ["game_id", "team", "player_name"], "dated appearance")
    # The left merge retains unmatched appearances so absent dates/IDs refuse.
    games = games.merge(
        good_index, on=["game_id", "team", "player_name"], how="left", validate="m:1"
    )
    groups = games.groupby(["player_name", "season", "league"], sort=False).indices
    outputs, flows = [], []
    for row in pairs.itertuples(index=False):
        detail = {
            "player_name": row.player_name,
            "season": int(row.season),
            "league_src": row.league_src,
            "league_dest": row.league_dest,
        }
        dom = games.iloc[
            groups.get((row.player_name, row.season, row.league_src), [])
        ].copy()
        dest = games.iloc[
            groups.get((row.player_name, row.season, row.league_dest), [])
        ].copy()
        scope = crosswalk.loc[
            crosswalk.competition.eq(row.league_dest) & crosswalk.season.eq(row.season)
        ]
        names = (
            dom[["raw_player_name", "raw_team"]]
            .drop_duplicates()
            .rename(columns={"raw_player_name": "raw_name", "raw_team": "raw_club"})
        )
        mapping = names.merge(
            scope, on=["raw_name", "raw_club"], how="left", validate="1:1"
        )
        if row.n_clubs_src != 1 or row.n_clubs_dest != 1:
            pair, status, extra = None, "multiple_clubs", {}
        else:
            pair, status, extra = window_pair(dom, dest, mapping)
        flows.append({**detail, **extra, "status": status})
        if pair is not None:
            outputs.append(pair)
    flow = pd.DataFrame(flows)
    result = pd.concat(outputs, ignore_index=True) if outputs else pairs.iloc[:0].copy()
    if len(flow) != len(pairs) or len(result) != int(flow.status.eq("included").sum()):
        raise ValueError("same-club pair flow does not conserve rows")
    require_unique(result, ["player_name", "season"], "same-club pair")
    return result, flow


def run(source_root, corrected_dir, out_dir):
    corrected_dir, out_dir = Path(corrected_dir), Path(out_dir)
    if out_dir.exists() and any(out_dir.iterdir()):
        raise ValueError("output must be new or empty")
    metadata_path = corrected_dir / "variant.json"
    metadata_hash = sha256_file(metadata_path)
    metadata = json.loads(metadata_path.read_text())
    if (
        metadata.get("status") != "prepared"
        or metadata.get("variant") != "official_corrected"
    ):
        raise ValueError("corrected source is not prepared")
    for name, digest in metadata["files"].items():
        if Path(name).name != name or sha256_file(corrected_dir / name) != digest:
            raise ValueError("corrected source file changed or invalid")
    evidence, clubs, index, inventory, source_hashes = construct_evidence(source_root)
    crosswalk = accept_crosswalk(evidence, clubs)
    pairs, flow = build_windows(
        pd.read_parquet(corrected_dir / "games.parquet"),
        pd.read_parquet(corrected_dir / "pairs.parquet"),
        crosswalk,
        index,
    )
    for name, digest in source_hashes.items():
        if sha256_file(Path(name)) != digest:
            raise ValueError("source changed during evidence construction")
    out_dir.mkdir(parents=True, exist_ok=True)
    frames = {
        "pairs.parquet": pairs,
        "identity_evidence.parquet": evidence,
        "club_evidence.parquet": clubs,
        "crosswalk.parquet": crosswalk,
        "pair_flow.parquet": flow,
        "calendar_inventory.parquet": inventory,
    }
    for name, frame in frames.items():
        frame.to_parquet(out_dir / name, index=False)
    shutil.copyfile(corrected_dir / "cohort.parquet", out_dir / "cohort.parquet")
    if sha256_file(metadata_path) != metadata_hash:
        raise ValueError("corrected metadata changed during evidence construction")
    for name, digest in metadata["files"].items():
        if sha256_file(corrected_dir / name) != digest:
            raise ValueError("corrected input changed during evidence construction")
    if sha256_file(out_dir / "cohort.parquet") != metadata["files"]["cohort.parquet"]:
        raise ValueError("copied cohort differs from corrected source")
    result = {
        "schema_version": 1,
        "status": "prepared",
        "variant": "same_club",
        "reference_variant": None,
        "files": {
            name: sha256_file(out_dir / name) for name in [*frames, "cohort.parquet"]
        },
        "protocol_sha256": sha256_file(PROTOCOL),
        "code_sha256": sha256_file(Path(__file__)),
        "corrected_variant_sha256": metadata_hash,
        "source_files": source_hashes,
        "counts": {
            "input_pairs": len(flow),
            "included_pairs": len(pairs),
            "flow_status": flow.status.value_counts().sort_index().to_dict(),
            "crosswalk_status": crosswalk.status.value_counts().sort_index().to_dict(),
        },
        "interpretation": (
            "Overlapping observed same-club appearances; not continuous employment "
            "or equal roles. Current bio coverage may select survivors. Cross-source "
            "agreement does not establish source independence."
        ),
    }
    (out_dir / "variant.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n"
    )
    return result


def main():
    logging.getLogger("scripts.build_league_factors").setLevel(logging.WARNING)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--corrected-dir", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()
    result = run(args.source_root, args.corrected_dir, args.out_dir)
    print(json.dumps(result["counts"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
