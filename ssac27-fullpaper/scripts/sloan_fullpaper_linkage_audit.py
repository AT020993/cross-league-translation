#!/usr/bin/env python3
"""E13 identity-linkage audit of the unverified factor-estimation pairs.

Pre-registration: docs/research/sloan-full-paper-preregistration-amendment-1-2026-11-04.md
(commit f1a3453da, pushed 2026-11-04, before this file existed), section E13.
EXPLORATORY, like everything in Amendment 1.

* Frame: the pool-A factor-estimation pairs (official_corrected, 4,074) whose
  E13 key (player_name x season x league_src x league_dest) is absent from the
  verified pool B (verified_same_club_full).
* Sample: 100 pairs, simple random sample without replacement,
  numpy.random.default_rng(20261104), drawn from the frame sorted by the E13
  key. The drawn keys are written to the run output BEFORE any raw record is
  read (``--stage draw`` stops there).

* Checks per pair, from raw EuroLeague-API and Proballers files only:
  normalised name (the repo pairing_key, the key the pairs were joined on; the
  number of distinct API persons behind the key is printed); birthdate where
  both sides carry one (EuroLeague people bio; the unique Proballers profile
  of the same strict name, the rule of scripts/sloan_same_club.profile_maps);
  club consistency (a domestic team and a continental club are the same club
  when they share most of their roster, teammates other than the audited
  player; a mid-season move is documented when the clubs' date spells do not
  overlap and the continental club is linked to a domestic team the player
  played for); schedule feasibility (no calendar date with a domestic game in
  the pair's source league and a continental game in its destination for
  clubs not shown to be the same).
* Classes, rule-based first (CLASS_RULES), then hand review of the remaining
  UNRESOLVED pairs from a committed per-pair decisions file (``--hand-review``).
* Primary: WRONG share with a Wilson 95% interval; UNRESOLVED share printed.

Threats and their controls (all in this file): a draw chosen after looking
(keys written first; the draw gate re-draws with the seed and must reproduce
them; a different seed must give a different sample, the negative control);
a frame that is not the registered one (sha256 pins on both pools, B must be a
subset of A, frame size printed).
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

from scripts import sloan_fullpaper_common as common  # noqa: E402
from scripts.translation_research_common import sha256_file  # noqa: E402
from scripts import sloan_same_club as same_club  # noqa: E402
from scripts import sloan_source_adjudication as adjudication  # noqa: E402
from src.data.corpus import euroleague_api as api  # noqa: E402

AMENDMENT = (
    ROOT / "docs/research/sloan-full-paper-preregistration-amendment-1-2026-11-04.md"
)
AMENDMENT_COMMIT = "f1a3453da"
E13_KEY = ["player_name", "season", "league_src", "league_dest"]
SEED = 20261104
CONTROL_SEED = SEED + 1
SAMPLE_N = 100
POOL_A = "official_corrected"
POOL_B = "verified_same_club_full"
EXPECTED_POOL_A = 4074
API_SEASONS = tuple(range(2016, 2026))  # season-literal-ok
CONTINENTAL = ("euroleague", "eurocup")
CLASSES = ("CONFIRMED", "WRONG", "UNRESOLVED")
#: Club identity from shared rosters (teammates other than the audited player).
SAME_MIN_SHARED = 3
SAME_MIN_SHARE = 0.5
DIFFERENT_MAX_SHARED = 1
WILSON_Z = 1.959963984540054
UPPER_LICENCE = 0.05
REPORT_TO_AMIR = 0.10
CLASS_RULES = {
    "WRONG": "a contradicting birthdate, or an infeasible schedule, or a "
    "different person shown by club and date records (a pair-entering "
    "domestic team and continental club shown to be different clubs whose "
    "date spells overlap)",
    "CONFIRMED": "name agrees (one API person behind the key), plus birthdate "
    "agrees or club agrees, and no contradiction",
    "UNRESOLVED": "otherwise",
}
LICENCES = {
    "upper_below_5pct": "at most X% of unverified estimation pairs are identity mismatches",
    "point_at_least_10pct": "reported to Amir before any writing, as a data-quality finding that touches every factor",
}


class GateFailure(AssertionError):
    """A pre-registered gate did not hold; the analysis must stop."""


def load_pairs(input_dir: Path, pool: str) -> pd.DataFrame:
    path = Path(input_dir) / pool / "pairs.parquet"
    common.check_sha(path, common.PAIRS_SHA[pool])
    pairs = pd.read_parquet(path, columns=E13_KEY)
    if pairs.duplicated(E13_KEY).any():
        raise GateFailure(f"{pool}: the E13 key is not unique")
    return pairs


def build_frame(pool_a: pd.DataFrame, pool_b: pd.DataFrame) -> pd.DataFrame:
    """Pool-A keys absent from pool B, in a fixed order (sorted E13 key)."""
    if len(pool_a) != EXPECTED_POOL_A:
        raise GateFailure(f"pool A has {len(pool_a)} pairs, not {EXPECTED_POOL_A}")
    joined = pool_b.merge(pool_a, on=E13_KEY, how="left", indicator=True)
    if len(joined) != len(pool_b) or joined["_merge"].ne("both").any():
        raise GateFailure("pool B is not a subset of pool A on the E13 key")
    merged = pool_a.merge(pool_b, on=E13_KEY, how="left", indicator=True)
    if len(merged) != len(pool_a):
        raise GateFailure("frame anti-join changed the pool-A row count")
    frame = merged.loc[merged["_merge"].eq("left_only"), E13_KEY]
    frame = frame.sort_values(E13_KEY, kind="mergesort").reset_index(drop=True)
    if len(frame) != len(pool_a) - len(pool_b):
        raise GateFailure("frame size is not |A| - |B|")
    return frame


def draw(frame: pd.DataFrame, seed: int = SEED, n: int = SAMPLE_N) -> pd.DataFrame:
    """Simple random sample without replacement, the registered generator."""
    rng = np.random.default_rng(seed)
    rows = rng.choice(len(frame), size=n, replace=False)
    sample = frame.iloc[rows].copy()
    sample.insert(0, "frame_row", rows.astype(int))
    sample.insert(0, "draw_order", np.arange(1, n + 1))
    return sample.reset_index(drop=True)


def assert_draw_reproduces(
    frame: pd.DataFrame, written: pd.DataFrame, seed: int
) -> None:
    """Re-draw with ``seed``; it must reproduce the written keys row for row."""
    again = draw(frame, seed=seed, n=len(written))
    cols = ["draw_order", "frame_row", *E13_KEY]
    left = written[cols].reset_index(drop=True).astype(str)
    right = again[cols].reset_index(drop=True).astype(str)
    if not left.equals(right):
        raise GateFailure(
            f"E13 draw gate: seed {seed} does not reproduce the written keys"
        )


def draw_gate(frame: pd.DataFrame, written: pd.DataFrame) -> dict:
    """The registered draw gate and its negative control (different seed)."""
    assert_draw_reproduces(frame, written, SEED)
    try:
        assert_draw_reproduces(frame, written, CONTROL_SEED)
    except GateFailure:
        control = "rejected as required"
    else:
        raise GateFailure(
            f"E13 draw negative control: seed {CONTROL_SEED} gave the same sample"
        )
    control_sample = draw(frame, seed=CONTROL_SEED, n=len(written))
    overlap = len(
        written[E13_KEY]
        .astype(str)
        .merge(control_sample[E13_KEY].astype(str), on=E13_KEY, how="inner")
    )
    return {
        "status": "passed",
        "redraw_seed": SEED,
        "redraw_reproduces": True,
        "negative_control_seed": CONTROL_SEED,
        "negative_control": control,
        "negative_control_overlap_keys": int(overlap),
    }


def write_draw(input_dir: Path, out: Path):
    """Frame, draw and draw gate; keys hit the disk before anything else is read."""
    pool_a = load_pairs(input_dir, POOL_A)
    pool_b = load_pairs(input_dir, POOL_B)
    frame = build_frame(pool_a, pool_b)
    sample = draw(frame)
    out.mkdir(parents=True, exist_ok=False)
    keys_path = out / "e13_drawn_keys.csv"
    sample.to_csv(keys_path, index=False)
    written = pd.read_csv(keys_path)
    gate = draw_gate(frame, written)
    record = {
        "analysis": "E13",
        "exploratory": True,
        "amendment_commit": AMENDMENT_COMMIT,
        "amendment_sha256": sha256_file(AMENDMENT),
        "input_sha256": {
            POOL_A: common.PAIRS_SHA[POOL_A],
            POOL_B: common.PAIRS_SHA[POOL_B],
        },
        "e13_key": E13_KEY,
        "frame_order": "sorted by the E13 key (stable)",
        "pool_a_pairs": int(len(pool_a)),
        "pool_b_pairs": int(len(pool_b)),
        "frame_pairs": int(len(frame)),
        "seed": SEED,
        "sample_n": int(len(sample)),
        "drawn_keys_file": keys_path.name,
        "drawn_keys_sha256": sha256_file(keys_path),
        "gates": {"E13_draw": gate},
    }
    (out / "e13_draw.json").write_text(
        json.dumps(record, indent=2, sort_keys=True) + "\n"
    )
    return frame, written, record


# ------------------------------------------------------------- raw records --
def load_continental(raw_root: Path) -> tuple[pd.DataFrame, dict]:
    """API appearances with dates and person codes, 2016-2025, both competitions."""
    frames, used = [], {}
    for comp in CONTINENTAL:
        for season in API_SEASONS:
            base = Path(raw_root) / comp / str(season)
            calendar_path = base / "games" / f"season_{season}_games.parquet"
            boxes = sorted((base / "boxscores").glob("*.parquet"))
            if not boxes or not calendar_path.exists():
                raise GateFailure(f"missing API files for {comp} {season}")
            for path in [*boxes, calendar_path]:
                used[str(path.relative_to(raw_root))] = sha256_file(path)
            raw = pd.concat([pd.read_parquet(b) for b in boxes], ignore_index=True)
            raw = api.drop_non_player_rows(raw)
            calendar = pd.read_parquet(calendar_path)[["gameCode", "date"]]
            same_club.require_unique(calendar, ["gameCode"], "API calendar")
            calendar["day"] = same_club.dates(calendar.date)
            rows = raw.merge(
                calendar[["gameCode", "day"]],
                left_on="Gamecode",
                right_on="gameCode",
                how="left",
                validate="m:1",
            )
            frames.append(
                pd.DataFrame(
                    {
                        "league": comp,
                        "season": int(season),
                        "game_id": f"api-{comp}-{season}-" + rows.Gamecode.astype(str),
                        "raw_name": rows.Player.astype(str),
                        "key": rows.Player.map(api.pairing_key),
                        "person": rows.Player_ID.astype(str).str.strip(),
                        "club": rows.Team.astype(str).str.strip(),
                        "day": rows.day,
                    }
                )
            )
    out = pd.concat(frames, ignore_index=True)
    if out.day.isna().any():
        raise GateFailure(f"{int(out.day.isna().sum())} API appearances lack a date")
    return out, used


def load_domestic(raw_root: Path) -> tuple[pd.DataFrame, dict]:
    """Proballers domestic player-games, both trees, TEAM_KEY de-duplicated."""
    raw, inventory = adjudication.load_raw(Path(raw_root))
    raw = raw.loc[~raw.league.isin(CONTINENTAL + ("test",))]
    raw = raw.sort_values("_priority", kind="mergesort")
    raw = raw.drop_duplicates(adjudication.TEAM_KEY, keep="first")
    out = pd.DataFrame(
        {
            "league": raw.league.astype(str),
            "season": raw.season.astype(int),
            "game_id": raw.game_id.astype(str),
            "raw_name": raw.player_name.astype(str),
            "key": raw.player_name.map(api.pairing_key),
            "club": raw.team.astype(str),
            "day": same_club.dates(raw.date),
        }
    ).reset_index(drop=True)
    used = {
        str(Path(r["source_file"]).resolve().relative_to(Path(raw_root).resolve())): r[
            "sha256"
        ]
        for r in inventory
    }
    return out, used


def load_birthdates(raw_root: Path, bio_path: Path) -> tuple[dict, dict, dict]:
    """(Proballers strict-name -> (id, dob), API box id -> dob), the repo rule."""
    root = Path(raw_root)
    paths = sorted((root / "proballers").glob("*/2025/player_bios_*.parquet"))
    paths += sorted(
        (root / "_inactive_leagues/proballers").glob("*/2025/player_bios_*.parquet")
    )
    if not paths:
        raise GateFailure("no retained Proballers profile files")
    used = {str(p.relative_to(root)): sha256_file(p) for p in paths}
    used[Path(bio_path).name] = sha256_file(bio_path)
    official = pd.read_parquet(bio_path)
    official = official.loc[official._source.eq("euroleague_api_people")]
    provider = pd.concat([pd.read_parquet(p) for p in paths], ignore_index=True)
    pb_map, el_map = same_club.profile_maps(provider, official)
    return pb_map, el_map, used


# ------------------------------------------------------------------ checks --
def spell(rows: pd.DataFrame) -> tuple:
    return rows.day.min(), rows.day.max()


def overlaps(a: tuple, b: tuple) -> bool:
    return max(a[0], b[0]) <= min(a[1], b[1])


def club_identity(cont_roster: set, dom_rows: pd.DataFrame, team: str) -> dict:
    """Same/different/unresolved for one continental club vs one domestic team."""
    league_keys = set(dom_rows.key)
    found = len(cont_roster & league_keys)
    shared = len(cont_roster & set(dom_rows.loc[dom_rows.club.eq(team), "key"]))
    if found <= DIFFERENT_MAX_SHARED:
        status = "different"  # the continental club's roster is not in this league
    elif shared >= SAME_MIN_SHARED and shared >= SAME_MIN_SHARE * found:
        status = "same"
    elif shared <= DIFFERENT_MAX_SHARED:
        status = "different"
    else:
        status = "unresolved"
    return {"status": status, "shared": shared, "found": found}


def _fmt_day(value) -> str:
    return pd.Timestamp(value).strftime("%Y-%m-%d")


def _clubs_text(rows: pd.DataFrame, by: list[str]) -> str:
    parts = []
    for key, group in rows.groupby(by, sort=True):
        label = "|".join(key) if isinstance(key, tuple) else str(key)
        first, last = spell(group)
        parts.append(
            f"{label}:{group.game_id.nunique()}g:{_fmt_day(first)}..{_fmt_day(last)}"
        )
    return "; ".join(parts)


def check_pair(pair, cont: pd.DataFrame, dom: pd.DataFrame, pb_map, el_map) -> dict:
    """Every registered check for one pair, with its evidence, and the rule class."""
    key, season = pair.player_name, int(pair.season)
    c_all = cont.loc[cont.season.eq(season) & cont.key.eq(key)]
    c_rows = c_all.loc[c_all.league.eq(pair.league_dest)]
    d_all = dom.loc[dom.season.eq(season) & dom.key.eq(key)]
    d_rows = d_all.loc[d_all.league.eq(pair.league_src)]
    rec = {
        "games_dest_pair": int(pair.games_dest),
        "games_src_pair": int(pair.games_src),
        "games_dest_found": int(c_rows.game_id.nunique()),
        "games_src_found": int(d_rows.game_id.nunique()),
        "club_dest_pair": pair.club_dest,
        "club_src_pair": pair.club_src,
        "cont_persons": ";".join(sorted(c_rows.person.unique())),
        "cont_raw_names": ";".join(sorted(c_rows.raw_name.unique())),
        "dom_raw_names": ";".join(sorted(d_rows.raw_name.unique())),
        "cont_clubs": _clubs_text(c_rows, ["club"]),
        "dom_clubs": _clubs_text(d_rows, ["club"]),
        "other_domestic": _clubs_text(
            d_all.loc[~d_all.league.eq(pair.league_src)], ["league", "club"]
        ),
        "other_continental": _clubs_text(
            c_all.loc[~c_all.league.eq(pair.league_dest)], ["league", "club"]
        ),
    }
    found = not c_rows.empty and not d_rows.empty
    persons = sorted(c_rows.person.unique())
    keys = set(c_rows.key) | set(d_rows.key)
    rec["name_status"] = (
        "records_missing"
        if not found
        else "agrees"
        if keys == {key} and len(persons) == 1
        else f"{len(persons)}_api_persons"
        if keys == {key}
        else "disagrees"
    )
    strict = {same_club.strict_name(n) for n in c_rows.raw_name} | {
        same_club.strict_name(n) for n in d_rows.raw_name
    }
    rec["strict_name_equal"] = bool(found and len(strict) == 1)

    # Birthdate, where both sides carry one.
    dob_c = sorted({el_map.get(p) for p in persons} - {None})
    profiles = sorted(
        {pb_map[n] for n in map(same_club.strict_name, d_rows.raw_name) if n in pb_map}
    )
    rec["dob_cont"] = ";".join(dob_c)
    rec["dob_dom"] = ";".join(d for _, d in profiles)
    rec["dom_profile_ids"] = ";".join(i for i, _ in profiles)
    if len(dob_c) == 1 and len(profiles) == 1:
        rec["dob_status"] = "agrees" if profiles[0][1] == dob_c[0] else "contradicts"
    elif len(dob_c) > 1 or len(profiles) > 1:
        rec["dob_status"] = "multiple"
    else:
        rec["dob_status"] = "not_available"

    # Club identity for every (domestic team, continental club) combination.
    links, combos = [], []
    for c_club, c_group in c_rows.groupby("club", sort=True):
        roster = set(
            cont.loc[
                cont.league.eq(pair.league_dest)
                & cont.season.eq(season)
                & cont.club.eq(c_club)
                & cont.key.ne(key),
                "key",
            ]
        )
        for (d_league, d_club), d_group in d_all.groupby(["league", "club"], sort=True):
            league_rows = dom.loc[
                dom.league.eq(d_league) & dom.season.eq(season) & dom.key.ne(key)
            ]
            ident = club_identity(roster, league_rows, d_club)
            entering = d_league == pair.league_src
            overlap = overlaps(spell(c_group), spell(d_group))
            combos.append(
                f"{d_league}|{d_club}~{c_club}:{ident['status']}"
                f"({ident['shared']}/{ident['found']}),"
                f"{'overlap' if overlap else 'disjoint'}"
                f"{'' if entering else ',evidence-only'}"
            )
            if ident["status"] == "same":
                links.append((d_league, d_club, c_club))
            if entering:
                if ident["status"] == "different" and overlap:
                    rec.setdefault("club_contradiction", []).append(
                        f"{d_club} vs {c_club}"
                    )
                elif ident["status"] == "unresolved" and overlap:
                    rec.setdefault("club_unresolved_overlap", []).append(
                        f"{d_club} vs {c_club}"
                    )
    rec["club_combinations"] = "; ".join(combos)
    rec["club_links"] = "; ".join(f"{a}|{b}={c}" for a, b, c in links)
    if not found:
        rec["club_status"] = "records_missing"
    elif rec.get("club_contradiction"):
        rec["club_status"] = "contradicts"
    elif links and not rec.get("club_unresolved_overlap"):
        rec["club_status"] = "agrees"
    else:
        rec["club_status"] = "unresolved"
    rec["club_contradiction"] = "; ".join(rec.get("club_contradiction", []))
    rec["club_unresolved_overlap"] = "; ".join(rec.get("club_unresolved_overlap", []))

    # Schedule feasibility: same calendar date, both sides, clubs not shown same.
    linked = {(b, c) for a, b, c in links if a == pair.league_src}
    clashes = []
    for day in sorted(set(c_rows.day) & set(d_rows.day)):
        c_clubs = set(c_rows.loc[c_rows.day.eq(day), "club"])
        d_clubs = set(d_rows.loc[d_rows.day.eq(day), "club"])
        if not any((d, c) in linked for d in d_clubs for c in c_clubs):
            clashes.append(
                f"{_fmt_day(day)}:{'/'.join(sorted(d_clubs))} vs {'/'.join(sorted(c_clubs))}"
            )
    rec["schedule_clashes"] = "; ".join(clashes)
    rec["schedule_status"] = (
        "records_missing" if not found else "infeasible" if clashes else "feasible"
    )
    rec["rule_class"], rec["rule_reason"] = classify(rec)
    return rec


def evidence_pack(pair, cont: pd.DataFrame, dom: pd.DataFrame) -> list[dict]:
    """Hand-review evidence for one rule-UNRESOLVED pair, from the same records.

    For every API season of the person(s) behind the key: each continental club,
    its games and date spell, the roster-identity status against every domestic
    team the same key played for that season, and in which corpus domestic
    leagues that club's roster (other players) appears.
    """
    key, season = pair.player_name, int(pair.season)
    persons = sorted(
        cont.loc[
            cont.season.eq(season)
            & cont.key.eq(key)
            & cont.league.eq(pair.league_dest),
            "person",
        ].unique()
    )
    rows = []
    history = cont.loc[cont.person.isin(persons)]
    for (s, league, club), group in history.groupby(["season", "league", "club"]):
        roster = set(
            cont.loc[
                cont.league.eq(league)
                & cont.season.eq(s)
                & cont.club.eq(club)
                & cont.key.ne(key),
                "key",
            ]
        )
        d_season = dom.loc[dom.season.eq(s)]
        links = []
        for (d_league, d_club), d_group in d_season.loc[d_season.key.eq(key)].groupby(
            ["league", "club"]
        ):
            ident = club_identity(
                roster,
                d_season.loc[d_season.league.eq(d_league) & d_season.key.ne(key)],
                d_club,
            )
            first, last = spell(d_group)
            links.append(
                f"{d_league}|{d_club}:{ident['status']}({ident['shared']}/{ident['found']})"
                f":{d_group.game_id.nunique()}g:{_fmt_day(first)}..{_fmt_day(last)}"
            )
        found = {
            lg: len(roster & set(d_season.loc[d_season.league.eq(lg), "key"]))
            for lg in sorted(d_season.league.unique())
        }
        first, last = spell(group)
        rows.append(
            {
                "draw_order": int(pair.draw_order),
                **{c: getattr(pair, c) for c in E13_KEY},
                "person": ";".join(sorted(group.person.unique())),
                "api_season": int(s),
                "api_league": league,
                "api_club": club,
                "api_games": int(group.game_id.nunique()),
                "api_spell": f"{_fmt_day(first)}..{_fmt_day(last)}",
                "api_roster_size": len(roster),
                "domestic_records_same_key": "; ".join(links),
                "api_roster_found_by_domestic_league": "; ".join(
                    f"{lg}:{n}" for lg, n in found.items() if n
                )
                or "none",
            }
        )
    return rows


def classify(rec: dict) -> tuple[str, str]:
    """The registered classes (Amendment 1, E13), applied mechanically."""
    wrong = []
    if rec["dob_status"] == "contradicts":
        wrong.append("birthdate contradicts")
    if rec["schedule_status"] == "infeasible":
        wrong.append("infeasible schedule")
    if rec["club_status"] == "contradicts":
        wrong.append("different person shown by club and date records")
    if wrong:
        return "WRONG", "; ".join(wrong)
    name = rec["name_status"] == "agrees"
    support = [
        label
        for label, ok in (
            ("birthdate agrees", rec["dob_status"] == "agrees"),
            ("club agrees", rec["club_status"] == "agrees"),
        )
        if ok
    ]
    if name and support:
        return "CONFIRMED", "name agrees; " + "; ".join(support)
    missing = []
    if not name:
        missing.append(f"name {rec['name_status']}")
    if not support:
        missing.append(f"birthdate {rec['dob_status']}, club {rec['club_status']}")
    return "UNRESOLVED", "; ".join(missing)


def wilson(k: int, n: int, z: float = WILSON_Z) -> tuple[float, float]:
    if n <= 0:
        raise ValueError("Wilson interval needs n > 0")
    p = k / n
    centre = (p + z * z / (2 * n)) / (1 + z * z / n)
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return max(0.0, centre - half), min(1.0, centre + half)


def apply_hand_review(audit: pd.DataFrame, review: pd.DataFrame | None) -> pd.DataFrame:
    """Hand decisions apply ONLY to rule-UNRESOLVED pairs, each with evidence."""
    out = audit.copy()
    out["hand_decision"], out["hand_evidence"] = "", ""
    if review is None:
        out["final_class"] = out.rule_class
        return out
    review = review.fillna("")
    if review.duplicated(E13_KEY).any():
        raise GateFailure("hand review lists a pair twice")
    merged = (
        out[E13_KEY + ["rule_class"]]
        .astype(str)
        .merge(review.astype(str), on=E13_KEY, how="right", indicator=True)
    )
    if merged["_merge"].ne("both").any():
        raise GateFailure("hand review names a pair that was not drawn")
    if merged.rule_class.ne("UNRESOLVED").any():
        raise GateFailure("hand review may only decide rule-UNRESOLVED pairs")
    if not merged.hand_decision.isin(CLASSES).all():
        raise GateFailure("hand decision outside CONFIRMED/WRONG/UNRESOLVED")
    if merged.hand_evidence.str.strip().eq("").any():
        raise GateFailure("every hand decision needs its evidence")
    pending = out.rule_class.eq("UNRESOLVED")
    if int(pending.sum()) != len(review):
        raise GateFailure(
            f"hand review covers {len(review)} of {int(pending.sum())} UNRESOLVED pairs"
        )
    keyed = out[E13_KEY].astype(str).apply(tuple, axis=1)
    rev = {tuple(r[E13_KEY].astype(str)): r for _, r in review.astype(str).iterrows()}
    for i in out.index[pending]:
        r = rev[keyed[i]]
        out.loc[i, "hand_decision"] = r.hand_decision
        out.loc[i, "hand_evidence"] = r.hand_evidence
    out["final_class"] = np.where(pending, out.hand_decision, out.rule_class)
    return out


def summarise(final: pd.DataFrame, hand_reviewed: bool) -> dict:
    n = len(final)
    counts = {c: int(final.final_class.eq(c).sum()) for c in CLASSES}
    rule_counts = {c: int(final.rule_class.eq(c).sum()) for c in CLASSES}
    low, high = wilson(counts["WRONG"], n)
    share = counts["WRONG"] / n
    licences = {
        "upper_below_5pct": bool(high < UPPER_LICENCE),
        "point_at_least_10pct": bool(share >= REPORT_TO_AMIR),
    }
    sentence = None
    if hand_reviewed and licences["upper_below_5pct"]:
        sentence = LICENCES["upper_below_5pct"].replace("X%", f"{100 * high:.1f}%")
    return {
        "n": n,
        "hand_review_applied": hand_reviewed,
        "rule_counts": rule_counts,
        "final_counts": counts,
        "wrong_share": share,
        "wrong_wilson95": [low, high],
        "unresolved_share": counts["UNRESOLVED"] / n,
        "licences": licences,
        "licensed_sentence": sentence,
    }


def audit_sample(
    input_dir: Path, raw_root: Path, bio_path: Path, written: pd.DataFrame
) -> tuple[pd.DataFrame, dict]:
    """Read the raw records only now, after the keys are on disk."""
    pairs = pd.read_parquet(Path(input_dir) / POOL_A / "pairs.parquet")
    sample = written.merge(pairs, on=E13_KEY, how="left", validate="1:1")
    if sample.games_src.isna().any():
        raise GateFailure("a drawn key is missing from pool A")
    cont, used_c = load_continental(raw_root)
    dom, used_d = load_domestic(raw_root)
    pb_map, el_map, used_b = load_birthdates(raw_root, bio_path)
    records, pack = [], []
    for pair in sample.itertuples(index=False):
        rec = {c: getattr(pair, c) for c in ["draw_order", "frame_row", *E13_KEY]}
        rec.update(check_pair(pair, cont, dom, pb_map, el_map))
        records.append(rec)
        if rec["rule_class"] == "UNRESOLVED":
            pack.extend(evidence_pack(pair, cont, dom))
    audit = pd.DataFrame(records)
    reconciliation = {
        "dest_games_match": int(audit.games_dest_found.eq(audit.games_dest_pair).sum()),
        "src_games_match": int(audit.games_src_found.eq(audit.games_src_pair).sum()),
        "n": int(len(audit)),
    }
    inputs = {"continental": used_c, "domestic": used_d, "profiles": used_b}
    return audit, {
        "reconciliation": reconciliation,
        "raw_inputs": inputs,
        "evidence_pack": pd.DataFrame(pack),
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--stage", choices=("draw", "audit"), default="audit")
    parser.add_argument("--raw-root", type=Path)
    parser.add_argument("--bio", type=Path)
    parser.add_argument("--hand-review", type=Path)
    args = parser.parse_args(argv)
    _, written, record = write_draw(args.input_dir, args.out)
    gate = record["gates"]["E13_draw"]
    print(
        f"E13 frame {record['frame_pairs']} of {record['pool_a_pairs']} pool-A pairs; "
        f"drew {len(written)} keys (seed {SEED}); draw gate {gate['status']}, "
        f"negative control {gate['negative_control']}"
    )
    if args.stage == "draw":
        return 0
    if args.raw_root is None or args.bio is None:
        parser.error("--stage audit needs --raw-root and --bio")
    audit, info = audit_sample(args.input_dir, args.raw_root, args.bio, written)
    review = None
    if args.hand_review is not None:
        review = pd.read_csv(args.hand_review, dtype=str, keep_default_na=False)
    final = apply_hand_review(audit, review)
    final.to_csv(args.out / "e13_audit_pairs.csv", index=False)
    info["evidence_pack"].to_csv(args.out / "e13_unresolved_evidence.csv", index=False)
    summary = summarise(final, hand_reviewed=review is not None)
    record.update(
        stage="audit",
        class_rules=CLASS_RULES,
        club_identity_rule={
            "same_min_shared": SAME_MIN_SHARED,
            "same_min_share": SAME_MIN_SHARE,
            "different_max_shared": DIFFERENT_MAX_SHARED,
        },
        licences_registered=LICENCES,
        hand_review_file=(
            None
            if args.hand_review is None
            else {
                "name": args.hand_review.name,
                "sha256": sha256_file(args.hand_review),
            }
        ),
        reconciliation=info["reconciliation"],
        raw_inputs=info["raw_inputs"],
        unresolved_evidence_rows=int(len(info["evidence_pack"])),
        check_status_counts={
            col: audit[col].value_counts().sort_index().to_dict()
            for col in ("name_status", "dob_status", "club_status", "schedule_status")
        },
        e13=summary,
    )
    (args.out / "e13_summary.json").write_text(
        json.dumps(record, indent=2, sort_keys=True, default=str) + "\n"
    )
    low, high = summary["wrong_wilson95"]
    print(
        f"E13 rule classes {summary['rule_counts']}; final {summary['final_counts']}; "
        f"WRONG share {summary['wrong_share']:.3f} (Wilson 95% {low:.3f}-{high:.3f}); "
        f"UNRESOLVED share {summary['unresolved_share']:.3f}; "
        f"hand review {'applied' if summary['hand_review_applied'] else 'NOT applied'}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
