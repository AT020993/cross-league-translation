#!/usr/bin/env python
"""Fetch NBA per-season player totals and birthdates for the NBA arm (ATI-2958).

Source: the NBA's own stats endpoints through the ``nba_api`` wrapper (not a
declared dependency -- run with ``uv run --with nba_api``). Terms (NBA.com ToU
section 9, read 2026-09-03): statistics may be used for private, non-commercial
purposes and published in that capacity; they may NOT be redistributed or used
in a commercial product. So:

* everything lands under ``data/raw/nba/`` which is gitignored -- **no NBA row
  is ever committed**; the public repo carries this script and derived
  per-move pair tables only;
* nothing here is imported by the product.

Sequence matters: ``docs/research/preregistration-nba-arm-2026-09-03.md`` was
committed before this script first ran. Birthdates are fetched only for the
players whose normalised name also appears in the EuroLeague corpus, because
identity is name AND birth year (the EuroLeague "Devin Booker" is not the NBA
one).

Usage::

    uv run --with nba_api python scripts/fetch_nba_player_seasons.py \
        [--seasons 2015 2025] [--out data/raw/nba] [--delay 0.6]
"""

from __future__ import annotations

import argparse
import datetime as dt
import os
import re
import sys
import time
import unicodedata
from pathlib import Path

import pandas as pd

# BA_REPO lets a worktree without an equipped data/ tree read and write the
# primary checkout's data/raw (the corpus and the gitignored NBA landing dir).
REPO = Path(os.environ.get("BA_REPO", Path(__file__).resolve().parents[1]))
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))


def norm_key(name: str) -> str:
    """Same normaliser as compare_continental_sources: ASCII upper, no suffix."""
    s = (
        unicodedata.normalize("NFKD", str(name))
        .encode("ascii", "ignore")
        .decode()
        .upper()
    )
    s = re.sub(r"[^\w\s-]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return re.sub(r"\b(JR\.?|SR\.?|II|III|IV|V)$", "", s).strip()


def api_name_to_first_last(last_first: str) -> str:
    if "," not in last_first:
        return last_first.strip()
    last, first = last_first.split(",", 1)
    return f"{first.strip()} {last.strip()}"


def euroleague_name_keys(seasons: range) -> set[str]:
    keys: set[str] = set()
    for s in seasons:
        p = REPO / "data" / "raw" / "euroleague" / str(s) / "boxscores"
        if not p.exists():
            continue
        d = pd.read_parquet(p, columns=["Player"])
        keys |= {
            norm_key(api_name_to_first_last(x))
            for x in d.Player.unique()
            if x != "Total"
        }
    return keys


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument(
        "--seasons", nargs=2, type=int, default=[2015, 2025], metavar=("FIRST", "LAST")
    )
    ap.add_argument("--out", type=Path, default=REPO / "data" / "raw" / "nba")
    ap.add_argument("--delay", type=float, default=0.6)
    ap.add_argument("--skip-info", action="store_true", help="do not fetch birthdates")
    args = ap.parse_args(argv)
    args.out.mkdir(parents=True, exist_ok=True)

    try:
        from nba_api.stats.endpoints import commonplayerinfo, leaguedashplayerstats
    except ImportError:
        raise SystemExit(
            "nba_api is not installed: run with `uv run --with nba_api`"
        ) from None

    fetched_at = dt.datetime.now(dt.UTC).isoformat()
    first, last = args.seasons
    frames = []
    for start in range(first, last + 1):
        label = f"{start}-{str(start + 1)[-2:]}"
        df = leaguedashplayerstats.LeagueDashPlayerStats(
            season=label,
            season_type_all_star="Regular Season",
            per_mode_detailed="Totals",
            timeout=60,
        ).get_data_frames()[0]
        df["season"] = start
        df["_fetched_at"] = fetched_at
        df.to_parquet(args.out / f"player_season_totals_{start}.parquet", index=False)
        frames.append(df)
        print(f"[totals] {label}: {len(df):,} player-team rows")
        time.sleep(args.delay)
    allt = pd.concat(frames, ignore_index=True)
    print(
        f"[totals] {len(allt):,} rows, {allt.PLAYER_ID.nunique():,} players, "
        f"seasons {first}-{last}"
    )

    if args.skip_info:
        return 0

    el_keys = euroleague_name_keys(range(2016, 2026))
    allt["key"] = allt.PLAYER_NAME.map(norm_key)
    cand = allt[allt.key.isin(el_keys)].drop_duplicates("PLAYER_ID")[
        ["PLAYER_ID", "PLAYER_NAME", "key"]
    ]
    print(
        f"[info] {len(cand)} NBA players share a normalised name with a "
        "EuroLeague player; fetching birthdates"
    )
    rows = []
    for i, r in enumerate(cand.itertuples(index=False), 1):
        for attempt in range(3):
            try:
                info = commonplayerinfo.CommonPlayerInfo(
                    player_id=int(r.PLAYER_ID), timeout=60
                ).get_data_frames()[0]
                rows.append(
                    {
                        "PLAYER_ID": int(r.PLAYER_ID),
                        "PLAYER_NAME": r.PLAYER_NAME,
                        "key": r.key,
                        "BIRTHDATE": str(info.BIRTHDATE.iloc[0])[:10],
                        "COUNTRY": info.COUNTRY.iloc[0],
                        "_fetched_at": fetched_at,
                    }
                )
                break
            except Exception as exc:  # noqa: BLE001 -- transient endpoint errors; retried
                print(f"[info] retry {attempt + 1} for {r.PLAYER_NAME}: {exc}")
                time.sleep(2 + 2 * attempt)
        if i % 25 == 0:
            print(f"[info] {i}/{len(cand)}")
        time.sleep(args.delay)
    pd.DataFrame(rows).to_parquet(args.out / "player_info.parquet", index=False)
    print(f"[info] wrote {len(rows)} birthdates to {args.out / 'player_info.parquet'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
