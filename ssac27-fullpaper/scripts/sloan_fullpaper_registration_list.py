#!/usr/bin/env python3
"""Write the 2026-27 registration list the frozen-test scorer needs.

Amendment 18, rule 7 (and Amendment 8, rule 3): the list that names each
newcomer's club and previous club is the 2026-27 registration list of the
EuroLeague API, in the layout of the list pinned for E26: competition, season,
name, previous team, club. It holds no statistic. It is written by this
committed script, fetched on or after 25 November 2026, and its sha256 is
written into the score record.

Requests: one club list per competition, then one ``/people`` call per club,
the calls ``scripts/snapshot_euroleague_rosters.py`` and
``scripts/fetch_euroleague_bios.py`` already make. The previous team is the
``lastTeam`` field of each roster item, which the shared parser does not keep,
so this script reads the same response itself.

It refuses (exit 2, nothing written):

* before 25 November 2026 (UTC);
* when a club list fails or is empty, when a club's roster call fails, or
  when a club lists no player: a partial list would make the scorer's join
  rule miss players of a club it never reached;
* when the output file already exists.

Only five named fields are copied from a response. Anything else the API
returns, a statistic included, is never written.

Usage (on or after 25 November 2026)::

    python scripts/sloan_fullpaper_registration_list.py \\
        --out data/raw/euroleague/2026/people/registration_list_2026.csv

Writes the CSV and, beside it, ``<name>.record.json`` with the fetch time
(UTC) and the sha256 of the CSV. The scorer reads both.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
import sys
import time

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

#: The layout of the list pinned for E26, without identifiers: no statistic.
COLUMNS = ("comp", "season", "name", "last_team", "club")
SEASON = 2026  # stored season of 2026-27; this script writes no other season
#: 3 Nov registration, "Population at scoring": files refreshed on or after 25 Nov.
FETCH_FROM = dt.date(2026, 11, 25)
COMPETITIONS = ("E", "U")
PLAYER_TYPE = "J"
RECORD_SUFFIX = ".record.json"
ATTEMPTS = 3
TIMEOUT_SECONDS = 10
EXIT_OK = 0
EXIT_REFUSED = 2


class Refused(RuntimeError):
    """The list is not written."""


def sha256_file(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def record_path(csv_path: Path) -> Path:
    csv_path = Path(csv_path)
    return csv_path.with_name(csv_path.name + RECORD_SUFFIX)


def _text(value: object) -> str:
    return value.strip() if isinstance(value, str) else ""


def registration_rows(payload: object, *, comp: str, club: str, season: int) -> list:
    """Players of one ``/people`` response, as rows of the five columns.

    Each row is built from named fields only (the person's name and the item's
    ``lastTeam``), so no other field of the response can reach the file.
    """
    items = payload.get("data", payload) if isinstance(payload, dict) else payload
    if not isinstance(items, list):
        raise Refused(f"/people for {club} ({comp}{season}) is not a list")
    rows = []
    for item in items:
        if not isinstance(item, dict) or item.get("type") != PLAYER_TYPE:
            continue
        person = item.get("person")
        name = _text(person.get("name")) if isinstance(person, dict) else ""
        if not name:
            continue
        rows.append(
            {
                "comp": comp,
                "season": str(season),
                "name": name,
                "last_team": _text(item.get("lastTeam")),
                "club": club,
            }
        )
    return rows


def default_club_codes(comp: str, season: int) -> list:
    """The repository's own club-list call, strict: a failure or an empty
    list raises."""
    from src.data.euroleague_people import ClubListUnavailable, fetch_club_codes

    try:
        return [
            code for _, code in fetch_club_codes(season, comps=(comp,), strict=True)
        ]
    except ClubListUnavailable as exc:
        raise Refused(f"club list for {comp}{season}: {exc}") from exc


def default_people_payload(
    comp: str, club: str, season: int, *, get=None, sleep=time.sleep
):
    """The repository's ``/people`` call, returning the response itself."""
    from src.data import euroleague_people as people

    if get is None:
        import requests

        get = requests.get
    url = f"{people._API_ROOT}/{comp}/seasons/{comp}{season}/clubs/{club}/people"
    last = None
    for attempt in range(1, ATTEMPTS + 1):
        try:
            response = get(url, timeout=TIMEOUT_SECONDS)
            response.raise_for_status()
            return response.json()
        except Exception as exc:  # noqa: BLE001 -- network and JSON boundary
            last = exc
            if attempt < ATTEMPTS:
                sleep(2.0 * attempt)
    raise Refused(
        f"/people for {club} ({comp}{season}) failed after {ATTEMPTS} attempts: "
        f"{type(last).__name__}"
    )


def collect(
    *,
    club_codes=default_club_codes,
    people_payload=default_people_payload,
    delay: float = 1.0,
    sleep=time.sleep,
) -> tuple[list, dict]:
    """Every club's players for both competitions, or a refusal."""
    rows, clubs = [], {}
    for comp in COMPETITIONS:
        codes = sorted(set(club_codes(comp, SEASON)))
        if not codes:
            raise Refused(f"no club is listed for {comp}{SEASON}")
        clubs[comp] = len(codes)
        for club in codes:
            if delay:
                sleep(delay)
            found = registration_rows(
                people_payload(comp, club, SEASON), comp=comp, club=club, season=SEASON
            )
            if not found:
                raise Refused(f"{club} ({comp}{SEASON}) lists no player")
            rows.extend(found)
    return rows, clubs


def write_list(rows: list, out: Path, *, fetched_at: dt.datetime, clubs: dict) -> dict:
    """Write the CSV and its record. ``rows`` may hold only the five columns."""
    import pandas as pd

    out = Path(out)
    if out.exists() or record_path(out).exists():
        raise Refused(f"{out} or its record already exists; nothing is overwritten")
    extra = sorted({key for row in rows for key in row} - set(COLUMNS))
    if extra:
        raise Refused(f"a row carries columns outside the registered layout: {extra}")
    frame = (
        pd.DataFrame(rows, columns=list(COLUMNS))
        .drop_duplicates()
        .sort_values(list(COLUMNS), kind="mergesort")
        .reset_index(drop=True)
    )
    if not len(frame):
        raise Refused("no player is listed at all")
    if fetched_at.tzinfo is None:
        raise Refused("the fetch time must carry a time zone")
    out.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(out, index=False)
    record = {
        "what": "EuroLeague API registration list, 2026-27 (Amendment 18, rule 7)",
        "script": "scripts/sloan_fullpaper_registration_list.py",
        "file": out.name,
        "sha256": sha256_file(out),
        "fetched_at_utc": fetched_at.astimezone(dt.timezone.utc).isoformat(),
        "season": SEASON,
        "columns": list(COLUMNS),
        "rows": int(len(frame)),
        "clubs": {comp: int(n) for comp, n in clubs.items()},
        "players_by_competition": {
            comp: int(n) for comp, n in frame.comp.value_counts().sort_index().items()
        },
        "holds_a_statistic": False,
    }
    record_path(out).write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    return record


def check_record(csv_path: Path, fetched_from: dt.date = FETCH_FROM) -> dict:
    """What the scorer requires of a list: its record, its hash, its layout
    and a fetch time on or after 25 November 2026 (UTC). Raises ``Refused``."""
    import csv

    csv_path = Path(csv_path)
    path = record_path(csv_path)
    if not csv_path.is_file() or not path.is_file():
        raise Refused(
            f"{csv_path.name}: the list or its record {path.name} is missing; "
            "the list is written by scripts/sloan_fullpaper_registration_list.py"
        )
    record = json.loads(path.read_text())
    got = sha256_file(csv_path)
    if record.get("sha256") != got:
        raise Refused(f"{csv_path.name}: sha256 {got} differs from its record")
    with csv_path.open(newline="") as handle:
        header = next(csv.reader(handle), [])
    if tuple(header) != COLUMNS or tuple(record.get("columns", ())) != COLUMNS:
        raise Refused(
            f"{csv_path.name}: columns {header} are not the registered layout "
            f"{list(COLUMNS)}"
        )
    if record.get("season") != SEASON:
        raise Refused(
            f"{csv_path.name}: the record is for season {record.get('season')}"
        )
    try:
        fetched = dt.datetime.fromisoformat(str(record.get("fetched_at_utc")))
    except ValueError as exc:
        raise Refused(
            f"{csv_path.name}: the record holds no readable fetch time"
        ) from exc
    if fetched.tzinfo is None:
        raise Refused(f"{csv_path.name}: the fetch time carries no time zone")
    if fetched.astimezone(dt.timezone.utc).date() < fetched_from:
        raise Refused(
            f"{csv_path.name} was fetched on "
            f"{fetched.astimezone(dt.timezone.utc).date()} (UTC), before {fetched_from}"
        )
    return {**record, "record_file": path.name, "record_sha256": sha256_file(path)}


def build(
    out: Path,
    *,
    now: dt.datetime | None = None,
    club_codes=default_club_codes,
    people_payload=default_people_payload,
    delay: float = 1.0,
    sleep=time.sleep,
) -> dict:
    """Fetch and write the list. Nothing is fetched before 25 November 2026."""
    started = now or dt.datetime.now(dt.timezone.utc)
    if started.astimezone(dt.timezone.utc).date() < FETCH_FROM:
        raise Refused(
            "the 2026-27 registration list may not be fetched before 25 November 2026"
        )
    out = Path(out)
    if out.exists() or record_path(out).exists():
        raise Refused(f"{out} or its record already exists; nothing is overwritten")
    rows, clubs = collect(
        club_codes=club_codes, people_payload=people_payload, delay=delay, sleep=sleep
    )
    fetched_at = now or dt.datetime.now(dt.timezone.utc)
    return write_list(rows, out, fetched_at=fetched_at, clubs=clubs)


def main(argv: list | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", type=Path, required=True, help="the CSV to write")
    parser.add_argument(
        "--delay", type=float, default=1.0, help="seconds between roster calls"
    )
    args = parser.parse_args(argv)
    try:
        record = build(args.out, delay=args.delay)
    except Refused as exc:
        print(f"REFUSED, nothing written: {exc}", file=sys.stderr)
        return EXIT_REFUSED
    print(
        f"wrote {args.out}: {record['rows']} players, clubs {record['clubs']}, "
        f"fetched {record['fetched_at_utc']}, sha256 {record['sha256']}"
    )
    return EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
