#!/usr/bin/env python3
"""E27 of the SSAC27 full paper: the frozen forecasts tested on older seasons.

Pre-registration: docs/research/sloan-full-paper-preregistration-amendment-7-2026-11-12.md
(commit e884afe8b, pushed alone 2026-11-12T22:01:38Z).

``freeze`` builds every qualifying 2007-08 to 2014-15 source player-season of
ACB, ABA and Israel from the leagues' own box scores, links each to an API
person by the registered name rule, and forecasts it for both continental
destinations with the code path that produced the frozen 2026-27 forecasts
(factors, lag and training rows up to 2025). It computes no error and joins
no arrival-season outcome.

``score`` refuses to run unless the forecast file has the sha256 that was
pushed, joins the arrival-season outcomes from the EuroLeague API season
totals, selects the arrivals by the v10 rules and computes the three
registered comparisons for both versions (all three leagues; without ACB).

Threats: models tuned on the test seasons (the forecasts come from the P1
freeze path, G27b reproduces the published 2026-27 forecasts to 1e-9); a
different outcome definition (G27c, on the 674); a name key that joins two
players (the full-first-name rule, unique keys on both sides, G27d, the
rare-surname subset); forecasts changed after outcomes were seen (two runs,
the pushed sha256, G27e); choosing the version by its result (both are
computed, the printing rule depends only on ACB's permission).
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
import gzip
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import unicodedata

for _name in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_name, "1")
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from scripts import sloan_fullpaper_arrivals_audit as e26  # noqa: E402
from scripts import sloan_fullpaper_common as common  # noqa: E402
from scripts import sloan_fullpaper_prospective as p1  # noqa: E402
from scripts import sloan_fullpaper_robustness as robust  # noqa: E402
from scripts.translation_research_common import sha256_file  # noqa: E402

GateFailure = common.GateFailure
AMENDMENT = (
    ROOT / "docs/research/sloan-full-paper-preregistration-amendment-7-2026-11-12.md"
)
AMENDMENT_COMMIT = "e884afe8b"
P1_DIR = ROOT / "docs/research/artifacts/sloan-fullpaper-p1-freeze-2026-11"
ARRIVALS_674 = (
    ROOT
    / "docs/research/artifacts/sloan-fullpaper-arrivals-audit-2026-11/e26_arrivals.csv"
)
#: Amendment 7, "Pinned inputs".
BOX_PINS = {
    "aba/games.parquet": "c11b7e8c9ef8b4f6261c271f4d9bf0828106c69900092a58dcd64b88c03b0eea",
    "aba/player_boxscores.parquet": "009c7e1611c6546058f4e66722b73cc29484830ef4016cdc313fcc15f20b3e1e",
    "acb/games.parquet": "9883aba851234e20988e73a0a0cfe0e3ccf4baa1cbdbf768c48b774c16a5eda4",
    "acb/player_boxscores.parquet": "344f7694dc17d356431ee219294da356574954bf3957589ad54aee01c6361808",
    "israel/games.parquet": "14b86022f51309a50519d5245bfab0ddf79982e89ec22dbf10ccfb7e5e1a0c3f",
    "israel/player_boxscores.parquet": "875a358225216de4fd28b5a56af7382e8fb3e000875aca64d283afab24920c58",
}
API_MANIFEST_SHA = "c42cf830ad31d7c739dd34aed8f37f7eb9b9c0efcf4b8458529ac0336047e50b"
P1_FORECAST_SHA = "f3530c1a5ac369c032a996756ced226a93aa2d9f71d2e63aab21694de3d55316"
LEAGUES = {"acb": "spain-acb", "aba": "aba-league", "israel": "israel-bsl"}
COMPETITIONS = {"E": "euroleague", "U": "eurocup"}
SOURCE_SEASONS = tuple(range(2007, 2015))
PINNED_API_SEASONS = tuple(range(2007, 2016))
FREEZE_SEASON = p1.FREEZE_SEASON
MIN_GAMES = 8
TOLERANCE = 1e-9
#: Amendment 7, G27c and G27d.
OUTCOME_JOIN_MIN = 0.95
OUTCOME_CORRELATION_MIN = 0.99
ISRAEL_LINKS = {"all": (9, 282), "rare_surname": (0, 181)}
SHUFFLE_SEED = 20261112
SHUFFLE_MAX_SHARE = 0.10
VERSIONS = {"V-all": ("acb", "aba", "israel"), "V-noACB": ("aba", "israel")}
ACB_NAME = re.compile(
    r'\\?"id\\?":(\d+),\\?"firstInitialAndLastName\\?":\\?"([^"\\]+)\\?",'
    r'\\?"firstName\\?":\\?"([^"\\]*)\\?",\\?"lastName\\?":\\?"([^"\\]*)\\?"'
)
ABA_NAME = re.compile(
    r"""href=['"]/player/(\d+)/\d+/\d+/([a-z0-9\-]+)/['"]\s*>\s*([^<]{2,60})</a>"""
)

# ------------------------------------------------------------------ names --


def fold(text: object) -> str:
    """Upper-case letters and spaces; accents, hyphens and punctuation removed."""
    plain = (
        unicodedata.normalize("NFKD", str(text))
        .encode("ascii", "ignore")
        .decode()
        .upper()
        .replace("-", " ")
        .replace("'", "")
    )
    return re.sub(r"[^A-Z ]", "", plain).strip()


def name_key(first: object, surname: object) -> str | None:
    """The registered key: first initial + surname."""
    f, s = fold(first), fold(surname).replace(" ", "")
    return f"{f[:1]}|{s}" if f and s else None


def api_parts(name: object) -> tuple[str, str]:
    """('FIRST NAMES', 'SURNAME') from the API's 'SURNAME, FIRST NAMES'."""
    text = str(name)
    if "," in text:
        surname, first = text.split(",", 1)
    else:
        tokens = text.split()
        surname, first = " ".join(tokens[:-1]), " ".join(tokens[-1:])
    return first.strip(), surname.strip()


def printed_parts(league: str, name: object) -> tuple[str, str]:
    """(first or initial, surname) from a box-score name as the league prints it."""
    tokens = str(name).replace(".", " ").split()
    if len(tokens) < 2:
        return "", ""
    if league == "aba":  # "Surname I."
        return tokens[-1], " ".join(tokens[:-1])
    return tokens[0], " ".join(tokens[1:])  # "I. Surname" / "First Surname"


def first_three(first: object) -> str | None:
    letters = fold(first).replace(" ", "")
    return letters[:3] if len(letters) >= 2 else None


# ------------------------------------------------------------- box scores --


def check_api_pins(api_root: Path) -> int:
    manifest = "".join(
        f"{sha256_file(api_root / f'{c}{y}.json')}  {c}{y}.json\n"
        for c, y in sorted((c, y) for c in COMPETITIONS for y in PINNED_API_SEASONS)
    )
    if hashlib.sha256(manifest.encode()).hexdigest() != API_MANIFEST_SHA:
        raise GateFailure("G27a: the API season files differ from the pinned manifest")
    return manifest.count("\n")


def check_pins(box_root: Path, api_root: Path) -> dict:
    for rel, expected in BOX_PINS.items():
        common.check_sha(box_root / rel, expected)
    manifest = "".join(
        f"{sha256_file(api_root / f'{c}{y}.json')}  {c}{y}.json\n"
        for c, y in sorted((c, y) for c in COMPETITIONS for y in PINNED_API_SEASONS)
    )
    if hashlib.sha256(manifest.encode()).hexdigest() != API_MANIFEST_SHA:
        raise GateFailure("G27a: the API season files differ from the pinned manifest")
    common.check_sha(P1_DIR / "p1_frozen_forecasts.parquet", P1_FORECAST_SHA)
    return {"box_files": len(BOX_PINS), "api_files": manifest.count("\n")}


def league_games(league: str, games: pd.DataFrame) -> pd.DataFrame:
    """League games (regular season and playoffs) of the registered seasons."""
    keep = games.season.isin(SOURCE_SEASONS)
    if league == "acb":
        keep &= games.competition.eq("acb_competition_1")
    elif league == "israel":
        keep &= ~games.competition.astype(str).str.contains("Cup")
    return games.loc[keep]


def page_names(league: str, pages: Path, game_keys) -> pd.DataFrame:
    """Per game and printed name: the league's player id and full first name."""
    pattern = ACB_NAME if league == "acb" else ABA_NAME
    rows = set()
    for key in game_keys:
        path = pages / f"{key}.html.gz"
        if not path.is_file():
            continue
        with gzip.open(path, "rb") as handle:
            text = handle.read().decode("utf-8", "replace")
        for m in pattern.finditer(text):
            if league == "acb":
                rows.add((key, m.group(2), m.group(1), m.group(3)))
            else:
                printed = re.sub(r"\s+", " ", m.group(3)).strip()
                rows.add((key, printed, m.group(1), m.group(2).split("-")[0]))
    out = pd.DataFrame(
        sorted(rows), columns=["game_key", "player_name", "league_player_id", "first"]
    )
    one = out.groupby(["game_key", "player_name"]).league_player_id.transform("nunique")
    return out.loc[one.eq(1)].drop_duplicates(["game_key", "player_name"])


def box_rows(league: str, box_root: Path) -> tuple[pd.DataFrame, dict]:
    """Player-game rows of league games, with a player id and a first name."""
    games = pd.read_parquet(box_root / league / "games.parquet")
    box = pd.read_parquet(box_root / league / "player_boxscores.parquet")
    kept = league_games(league, games)
    reconciled = kept.loc[kept.points_reconcile.astype(bool)]
    rows = box.loc[box.game_key.isin(reconciled.game_key) & (box.minutes > 0)].copy()
    rows["season"] = rows.game_key.map(reconciled.set_index("game_key").season)
    rows["eff"] = (
        rows.pts
        + rows.reb
        + rows.ast
        + rows.stl
        + rows.blk
        - (rows.fga - rows.fgm)
        - (rows.fta - rows.ftm)
        - rows.tov
    )
    parts = [printed_parts(league, n) for n in rows.player_name]
    rows["printed_first"] = [p[0] for p in parts]
    rows["surname"] = [fold(p[1]).replace(" ", "") for p in parts]
    counts = {
        "league_games": int(len(kept)),
        "games_not_reconciled": int(len(kept) - len(reconciled)),
        "player_rows": int(len(rows)),
    }
    if league == "israel":
        rows["first"] = rows.printed_first
        rows["league_player_id"] = [
            f"{fold(f).replace(' ', '')}|{s}" if s else None
            for f, s in zip(rows.printed_first, rows.surname, strict=True)
        ]
    else:
        names = page_names(league, box_root / league / "pages", reconciled.game_key)
        rows = rows.merge(names, on=["game_key", "player_name"], how="left")
        if (
            league == "aba"
        ):  # the slug's first word, only if it fits the printed initial
            ok = [
                isinstance(f, str) and fold(f)[:1] == fold(p)[:1]
                for f, p in zip(rows["first"], rows.printed_first, strict=True)
            ]
            rows["first"] = rows["first"].where(pd.Series(ok, index=rows.index))
    missing = rows.league_player_id.isna() | rows.surname.eq("")
    counts["player_rows_without_id"] = int(missing.sum())
    rows = rows.loc[~missing].copy()
    rows["key"] = [
        name_key(p, s) for p, s in zip(rows.printed_first, rows.surname, strict=True)
    ]
    rows["first3"] = rows["first"].map(first_three)
    rows["league"] = league
    return rows.loc[rows.key.notna()], counts


def _mode(series: pd.Series):
    values = series.dropna()
    return values.value_counts().idxmax() if len(values) else None


def player_seasons(rows: pd.DataFrame) -> pd.DataFrame:
    """One row per league player and season: exposure, EFF and his name parts."""
    out = (
        rows.groupby(["league", "league_player_id", "season"])
        .agg(
            games=("game_key", "nunique"),
            minutes=("minutes", "sum"),
            eff=("eff", "sum"),
            club=("team", _mode),
            n_clubs=("team", "nunique"),
            printed_name=("player_name", _mode),
            key=("key", _mode),
            surname=("surname", _mode),
            first3=("first3", _mode),
        )
        .reset_index()
    )
    out["eff36"] = 36 * out.eff / out.minutes
    return out


# -------------------------------------------------------------------- API --


def api_seasons(api_root: Path, seasons) -> pd.DataFrame:
    """One row per API person, season and competition, from the season totals."""
    rows = []
    for comp in COMPETITIONS:
        for year in seasons:
            data = json.loads((api_root / f"{comp}{year}.json").read_text())
            for p in data["players"]:
                player, team = p["player"], p["player"].get("team") or {}
                rows.append(
                    {
                        "code": str(player["code"]).zfill(6),
                        "name": player["name"],
                        "season": year,
                        "comp": comp,
                        "team_code": team.get("code"),
                        "team_name": team.get("name"),
                        "games": p["gamesPlayed"],
                        "minutes": p["minutesPlayed"],
                        "eff": (
                            p["pointsScored"]
                            + p["totalRebounds"]
                            + p["assists"]
                            + p["steals"]
                            + p["blocks"]
                            - (
                                p["twoPointersAttempted"]
                                + p["threePointersAttempted"]
                                - p["twoPointersMade"]
                                - p["threePointersMade"]
                            )
                            - (p["freeThrowsAttempted"] - p["freeThrowsMade"])
                            - p["turnovers"]
                        ),
                    }
                )
    frame = pd.DataFrame(rows)
    top = frame.sort_values("games", ascending=False).drop_duplicates(
        ["code", "season", "comp"]
    )[["code", "season", "comp", "name", "team_code", "team_name"]]
    out = (
        frame.groupby(["code", "season", "comp"])[["games", "minutes", "eff"]]
        .sum()
        .reset_index()
        .merge(top, on=["code", "season", "comp"], validate="1:1")
    )
    parts = [api_parts(n) for n in out.name]
    out["key"] = [name_key(f, s) for f, s in parts]
    out["surname"] = [fold(s).replace(" ", "") for _, s in parts]
    out["first3"] = [first_three(f) for f, _ in parts]
    out["league_dest"] = out.comp.map(COMPETITIONS)
    return out


# ---------------------------------------------------------------- linking --


def link_sources(seasons: pd.DataFrame, api: pd.DataFrame) -> pd.DataFrame:
    """Amendment 7, "Linking players": one API person per source row, or a reason."""
    league_keys = seasons.groupby(
        ["league", "season", "key"]
    ).league_player_id.nunique()
    people = api[["code", "season", "key", "first3"]].drop_duplicates(
        ["code", "season"]
    )
    api_keys = people.groupby(["season", "key"]).code.nunique()
    one = people.loc[
        people.set_index(["season", "key"]).index.map(api_keys).to_numpy() == 1
    ].set_index(["season", "key"])
    codes, status = [], []
    for r in seasons.itertuples(index=False):
        index = (r.season + 1, r.key)
        if index not in api_keys.index:
            codes.append(None), status.append("no API person with this key")
        elif league_keys[(r.league, r.season, r.key)] > 1:
            codes.append(None), status.append("key not unique in the league")
        elif api_keys[index] > 1:
            codes.append(None), status.append("key not unique in the API")
        elif pd.isna(r.first3) or pd.isna(one.loc[index, "first3"]):
            codes.append(None), status.append("no full first name")
        elif r.first3 != one.loc[index, "first3"]:
            codes.append(None), status.append("first name differs")
        else:
            codes.append(one.loc[index, "code"]), status.append("linked")
    return seasons.assign(api_code=codes, link_status=status)


def rare_surnames(api_all: pd.DataFrame, box_root: Path) -> dict:
    """Per league: surnames with one API person (2007-2016) and one key in the league's files."""
    window = api_all.loc[api_all.season.between(2007, 2016) & api_all.key.notna()]
    people = window.groupby("surname").code.nunique()
    out = {}
    for league in LEAGUES:
        box = pd.read_parquet(
            box_root / league / "player_boxscores.parquet", columns=["player_name"]
        )
        parts = [printed_parts(league, n) for n in box.player_name.unique()]
        keys = (
            pd.DataFrame(
                {
                    "key": [name_key(f, s) for f, s in parts],
                    "surname": [fold(s).replace(" ", "") for _, s in parts],
                }
            )
            .dropna()
            .drop_duplicates("key")
        )
        counts = keys.surname.value_counts()
        out[league] = {s for s, n in counts.items() if n <= 1 and people.get(s, 0) <= 1}
    return out


def career_history(seasons: pd.DataFrame, api: pd.DataFrame) -> pd.DataFrame:
    """v10's career history from the seasons on disk, strictly before the source season.

    Earlier seasons of the same league player; earlier seasons in the other two
    leagues under the same surname and first three letters, where that pair is
    unique in the league-season; and, for a linked row, the API person's earlier
    EuroLeague and EuroCup seasons.
    """
    strong = seasons.loc[seasons.first3.notna()].copy()
    strong["pair"] = strong.surname + "|" + strong.first3
    unique = strong.groupby(["league", "season", "pair"]).league_player_id.transform(
        "nunique"
    )
    strong = strong.loc[unique.eq(1)]
    by_player = {k: g for k, g in seasons.groupby(["league", "league_player_id"])}
    by_pair = {k: g for k, g in strong.groupby("pair")}
    by_code = {k: g for k, g in api.groupby("code")}
    prior, n_seasons = [], []
    for r in seasons.itertuples(index=False):
        own = by_player[(r.league, r.league_player_id)]
        parts = [own.loc[own.season.lt(r.season), ["eff", "minutes"]]]
        seen = int(own.season.lt(r.season).sum())
        if pd.notna(r.first3):
            other = by_pair.get(f"{r.surname}|{r.first3}")
            if other is not None:
                other = other.loc[other.league.ne(r.league) & other.season.lt(r.season)]
                parts.append(other[["eff", "minutes"]])
                seen += len(other)
        if pd.notna(r.api_code) and r.api_code in by_code:
            cont = by_code[r.api_code]
            cont = cont.loc[cont.season.lt(r.season) & (cont.minutes > 0)]
            parts.append(cont[["eff", "minutes"]])
            seen += cont.season.nunique()
        total = pd.concat(parts)
        minutes = float(total.minutes.sum())
        prior.append(36 * float(total.eff.sum()) / minutes if minutes > 0 else np.nan)
        n_seasons.append(seen)
    return seasons.assign(prior_mean_pir36=prior, history_seasons=n_seasons)


def source_rows(seasons: pd.DataFrame, rare: dict) -> pd.DataFrame:
    """Qualifying source player-seasons in the frozen path's row format."""
    q = seasons.loc[
        seasons.season.isin(SOURCE_SEASONS)
        & (seasons.games >= MIN_GAMES)
        & (seasons.minutes > 0)
    ].copy()
    q["rare_surname"] = [
        s in rare[lg] for s, lg in zip(q.surname, q.league, strict=True)
    ]
    out = pd.DataFrame(
        {
            "player_name": "e27:"
            + q.league
            + ":"
            + q.league_player_id.astype(str)
            + ":"
            + q.season.astype(str),
            "league": q.league,
            "league_player_id": q.league_player_id.astype(str),
            "printed_name": q.printed_name,
            "true_season_src": q.season.astype(int),
            "true_season_dest": q.season.astype(int) + 1,
            "api_code": q.api_code,
            "link_status": q.link_status,
            "rare_surname": q.rare_surname,
            "history_seasons": q.history_seasons.astype(int),
            "season_src": FREEZE_SEASON - 1,
            "league_src": q.league.map(LEAGUES),
            "games_src": q.games.astype(int),
            "minutes_src": q.minutes.astype(float),
            "pir_src": q.eff.astype(float),
            "pir_per36_src": q.eff36.astype(float),
            "club_src": q.club,
            "n_clubs_src": q.n_clubs.astype(int),
            "prior_mean_pir36": q.prior_mean_pir36.astype(float),
        }
    )
    out["above_own_prior"] = out.pir_per36_src > out.prior_mean_pir36
    out["source_positive_finite"] = np.isfinite(out.pir_per36_src) & (
        out.pir_per36_src > 0
    )
    return out.sort_values("player_name").reset_index(drop=True)


def both_destinations(rows: pd.DataFrame) -> pd.DataFrame:
    return pd.concat(
        [
            rows.assign(season_dest=FREEZE_SEASON, league_dest=d, pir_per36_dest=np.nan)
            for d in p1.DESTINATIONS
        ],
        ignore_index=True,
    )


# ------------------------------------------------------------------ gates --


def p1_source_rows(published: pd.DataFrame) -> pd.DataFrame:
    """The 2025-26 source rows of the published frozen file, outcomes unknown."""
    columns = [
        "player_name",
        *p1.SOURCE_COLUMNS,
        "source_positive_finite",
        "season_dest",
        "league_dest",
    ]
    return published[columns].assign(pir_per36_dest=np.nan)


def same_models_gate(
    forecast: pd.DataFrame,
    features: pd.DataFrame,
    history_features: pd.DataFrame,
    published: pd.DataFrame,
) -> dict:
    """G27b: this path reproduces the published 2026-27 forecasts on every arm."""
    key = ["player_name", "league_dest"]
    arms = list(common.ALL_ARMS)

    def worst(got):
        joined = published[[*key, *arms]].merge(
            got[[*key, *arms]], on=key, suffixes=("", "_got"), validate="1:1"
        )
        if len(joined) != len(published):
            raise GateFailure("G27b: the published source rows were not all forecast")
        gaps = [float(np.nanmax(np.abs(joined[a] - joined[f"{a}_got"]))) for a in arms]
        same_missing = all(
            joined[a].isna().equals(joined[f"{a}_got"].isna()) for a in arms
        )
        return max(gaps) if same_missing else float("inf")

    gap = worst(forecast)
    if not gap <= TOLERANCE:
        raise GateFailure(
            f"G27b: the published forecasts are not reproduced (max gap {gap:.3g})"
        )
    shifted = features.loc[features.player_name.isin(published.player_name)].copy()
    shifted["scheduled_translated"] *= 1.01
    again, _ = p1.forecast_rows(history_features, shifted, FREEZE_SEASON)
    if worst(again) <= TOLERANCE:
        raise GateFailure(
            "G27b negative control: a shifted factor reproduced the forecasts"
        )
    return {
        "status": "passed",
        "max_abs_gap": gap,
        "tolerance": TOLERANCE,
        "rows": int(len(published)),
        "arms": len(arms),
        "negative_control": "rejected as required",
    }


def same_outcome_gate(rows674: pd.DataFrame, api: pd.DataFrame, sd: float) -> dict:
    """G27c: outcomes rebuilt from API season totals, on the 674."""
    arrivals = pd.read_csv(ARRIVALS_674, keep_default_na=False, dtype=str)
    one = arrivals.loc[arrivals.n_api_persons.astype(int).eq(1)].copy()
    one["code"] = one.api_persons.str.extract(r"(\d+)")[0].str.zfill(6)
    one["season_dest"] = one.season_dest.astype(int)
    totals = api.assign(api_rate=36 * api.eff / api.minutes)[
        ["code", "season", "league_dest", "api_rate"]
    ].rename(columns={"season": "season_dest"})
    joined = rows674.merge(
        one[["player_name", "season_dest", "code"]],
        on=["player_name", "season_dest"],
        how="left",
        validate="1:1",
    ).merge(totals, on=["code", "season_dest", "league_dest"], how="left")
    have = joined.loc[np.isfinite(joined.api_rate)].reset_index(drop=True)
    share = len(have) / len(rows674)

    def check(frame):
        r = float(np.corrcoef(frame.api_rate, frame.pir_per36_dest)[0, 1])
        scored = frame.assign(pir_per36_dest=frame.api_rate)
        readings = {
            n: e26.comparison(scored, n, sd)["registered_reading_holds"]
            for n in e26.COMPARISONS
        }
        return r, readings

    r, readings = check(have)
    if (
        share < OUTCOME_JOIN_MIN
        or r < OUTCOME_CORRELATION_MIN
        or not all(readings.values())
    ):
        raise GateFailure(
            f"G27c failed: join share {share:.3f}, correlation {r:.4f}, readings {readings}"
        )
    shuffled = have.assign(
        api_rate=have.api_rate.sample(frac=1, random_state=SHUFFLE_SEED).to_numpy()
    )
    if check(shuffled)[0] >= OUTCOME_CORRELATION_MIN:
        raise GateFailure("G27c negative control: shuffled outcomes passed")
    return {
        "status": "passed",
        "n": int(len(rows674)),
        "joined": int(len(have)),
        "join_share": share,
        "correlation": r,
        "readings_hold": readings,
        "median_abs_gap": float((have.api_rate - have.pir_per36_dest).abs().median()),
        "negative_control": "rejected as required",
    }


def israel_measurement(box_root: Path, api_all: pd.DataFrame, *, shuffle=None) -> dict:
    """G27d: the readiness check's Israeli measurement, with initials only."""
    games = pd.read_parquet(box_root / "israel/games.parquet")
    box = pd.read_parquet(box_root / "israel/player_boxscores.parquet")
    league = games.loc[~games.competition.astype(str).str.contains("Cup")]
    rows = box.loc[box.game_key.isin(league.game_key) & (box.minutes > 0)].copy()
    rows["season"] = rows.game_key.map(games.set_index("game_key").season)
    parts = [printed_parts("israel", n) for n in rows.player_name]
    rows["first"] = [fold(p[0]).replace(" ", "") for p in parts]
    rows["surname"] = [fold(p[1]).replace(" ", "") for p in parts]
    if shuffle is not None:
        names = rows[["first", "surname"]].drop_duplicates().reset_index(drop=True)
        mixed = names.surname.sample(frac=1, random_state=shuffle).to_numpy()
        swap = dict(zip(zip(names["first"], names.surname), mixed, strict=True))
        rows["surname"] = [
            swap[(f, s)] for f, s in zip(rows["first"], rows.surname, strict=True)
        ]
    rows = rows.loc[rows["first"].ne("") & rows.surname.ne("")]
    rows["key"] = rows["first"].str[:1] + "|" + rows.surname
    rows["full"] = rows["first"] + "|" + rows.surname
    dom = (
        rows.groupby(["season", "key"])
        .agg(
            games=("game_key", "nunique"),
            n_full=("full", "nunique"),
            full=("full", "first"),
        )
        .reset_index()
    )
    dom = dom.loc[
        (dom.games >= MIN_GAMES) & dom.season.isin(SOURCE_SEASONS) & dom.n_full.eq(1)
    ]
    best = api_all.sort_values("games", ascending=False).drop_duplicates(
        ["code", "season"]
    )
    best = best.loc[(best.games >= MIN_GAMES) & best.key.notna()]
    n_codes = best.groupby(["season", "key"]).code.transform("nunique")
    best = best.loc[n_codes.eq(1), ["season", "key", "surname", "first3"]]
    links = pd.concat(
        [
            dom.assign(season=dom.season + shift).merge(best, on=["season", "key"])
            for shift in (0, 1)
        ],
        ignore_index=True,
    )
    links["wrong"] = links.full.str.split("|").str[0].str[:3] != links.first3
    window = api_all.loc[api_all.season.between(2007, 2016) & api_all.key.notna()]
    people = window.groupby("surname").code.nunique()
    all_parts = [printed_parts("israel", n) for n in box.player_name.unique()]
    keys = (
        pd.DataFrame(
            {
                "key": [name_key(f, s) for f, s in all_parts],
                "surname": [fold(s).replace(" ", "") for _, s in all_parts],
            }
        )
        .dropna()
        .drop_duplicates("key")
    )
    league_n = keys.surname.value_counts()
    rare = links.surname.map(people).fillna(0).le(1) & links.surname.map(
        league_n
    ).fillna(0).le(1)
    return {
        "all": (int(links.wrong.sum()), int(len(links))),
        "rare_surname": (int(links.loc[rare, "wrong"].sum()), int(rare.sum())),
    }


def linking_gate(box_root: Path, api_all: pd.DataFrame) -> dict:
    measured = israel_measurement(box_root, api_all)
    if measured != ISRAEL_LINKS:
        raise GateFailure(
            f"G27d: the Israeli measurement is {measured}, registered {ISRAEL_LINKS}"
        )
    shuffled = israel_measurement(box_root, api_all, shuffle=SHUFFLE_SEED)["all"][1]
    if shuffled >= SHUFFLE_MAX_SHARE * measured["all"][1]:
        raise GateFailure(
            f"G27d negative control: {shuffled} links survive shuffled surnames"
        )
    return {
        "status": "passed",
        "measured": {k: list(v) for k, v in measured.items()},
        "links_after_shuffled_surnames": shuffled,
        "negative_control": "rejected as required",
    }


# ----------------------------------------------------------------- freeze --


def freeze(box_root: Path, api_root: Path, input_dir: Path, out: Path) -> dict:
    out.mkdir(parents=True, exist_ok=False)
    pins = check_pins(box_root, api_root)  # G27a
    control = out / "_g27a_control.parquet"
    data = (box_root / "aba/games.parquet").read_bytes()
    control.write_bytes(data[:-1] + (b"0" if data[-1:] != b"0" else b"1"))
    try:
        common.check_sha(control, BOX_PINS["aba/games.parquet"])
    except GateFailure:
        pins["negative_control"] = "rejected as required"
    else:
        raise GateFailure("G27a negative control: a changed box-score table passed")
    finally:
        control.unlink()
    pairs, cohort = common.load_pool(input_dir, "official_corrected")
    freeze_meta = json.loads((P1_DIR / "freeze.json").read_text())
    if (
        sha256_file(input_dir / "official_corrected/pairs.parquet")
        != freeze_meta["pairs_sha256"]
        or sha256_file(input_dir / "official_corrected/cohort.parquet")
        != freeze_meta["cohort_sha256"]
    ):
        raise GateFailure("G27a: pairs or cohort are not the ones the P1 freeze used")

    api_all = api_seasons(api_root, range(2007, 2026))
    later_files = "".join(
        f"{sha256_file(api_root / f'{c}{y}.json')}  {c}{y}.json\n"
        for c in sorted(COMPETITIONS)
        for y in range(2016, 2026)
    )
    api = api_all.loc[api_all.season.isin(PINNED_API_SEASONS)]
    gate_d = linking_gate(box_root, api_all)

    rows674, _, _ = common.anchor_rows(ROOT, input_dir)
    sd = float(json.loads(e26.REGISTERED.read_text())["e3"]["O1"]["outcome_sd"])
    gate_c = same_outcome_gate(rows674, api_all, sd)

    rows, counts, manifests = {}, {}, {}
    for league in LEAGUES:
        rows[league], counts[league] = box_rows(league, box_root)
        manifests[league] = sha256_file(box_root / league / "manifest.jsonl")
    full_first = {
        league: float(rows[league].first3.notna().mean()) for league in LEAGUES
    }
    seasons = pd.concat([player_seasons(r) for r in rows.values()], ignore_index=True)
    seasons = link_sources(seasons, api)
    seasons = career_history(seasons, api)
    old = source_rows(seasons, rare_surnames(api_all, box_root))

    published = pd.read_parquet(P1_DIR / "p1_frozen_forecasts.parquet")
    test = pd.concat(
        [p1_source_rows(published), both_destinations(old)], ignore_index=True
    )
    features, history_features = p1.prospective_features(pairs, cohort, test)
    forecast, info = p1.forecast_rows(history_features, features, FREEZE_SEASON)
    gate_b = same_models_gate(forecast, features, history_features, published)

    frozen = forecast.loc[forecast.player_name.str.startswith("e27:")].copy()
    frozen = frozen.sort_values(["league_dest", "player_name"]).reset_index(drop=True)
    if frozen.pir_per36_dest.notna().any() or len(frozen) != 2 * len(old):
        raise GateFailure(
            "the frozen file is not one forecast per source row and destination"
        )
    path = out / "e27_frozen_forecasts.parquet"
    frozen.to_parquet(path, index=False)
    record = {
        "analysis": "E27 freeze",
        "amendment_commit": AMENDMENT_COMMIT,
        "amendment_sha256": sha256_file(AMENDMENT),
        "forecast_file": path.name,
        "forecast_sha256": sha256_file(path),
        "rows": int(len(frozen)),
        "source_player_seasons": int(len(old)),
        "rows_all_arms_forecast": int(frozen.all_arms_forecast.sum()),
        "train_n": info["train_n"],
        "by_league": {
            league: {
                **counts[league],
                "source_player_seasons": int(old.league.eq(league).sum()),
                "linked": int(
                    (old.league.eq(league) & old.link_status.eq("linked")).sum()
                ),
                "link_status": old.loc[old.league.eq(league)]
                .link_status.value_counts()
                .to_dict(),
                "share_rows_with_full_first_name": full_first[league],
                "pages_manifest_sha256": manifests[league],
            }
            for league in LEAGUES
        },
        "name_rule": {
            league: "surname + first three letters of the first name (the Israeli rule)"
            for league in LEAGUES
        },
        "share_without_history": float(old.prior_mean_pir36.isna().mean()),
        "gates": {
            "G27a_inputs": {"status": "passed", **pins},
            "G27b_same_models": gate_b,
            "G27c_same_outcome": gate_c,
            "G27d_linking": gate_d,
        },
        "gate_only_api_files_2016_2025_manifest_sha256": hashlib.sha256(
            later_files.encode()
        ).hexdigest(),
        "outcomes_joined": False,
    }
    (out / "e27_freeze.json").write_text(
        json.dumps(record, indent=2, sort_keys=True) + "\n"
    )
    return record


# ------------------------------------------------------------------ score --


def arrivals(frozen: pd.DataFrame, api: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """v10 eligibility on the older seasons: exposure on both sides, no incumbency."""
    q = api.loc[(api.games >= MIN_GAMES) & (api.minutes > 0)]
    dest = q.sort_values("minutes", ascending=False).drop_duplicates(["code", "season"])
    was = set(zip(q.code, q.season + 1, strict=True))
    dest = dest.assign(
        was_cont=[(c, s) in was for c, s in zip(dest.code, dest.season, strict=True)],
        pir_per36_dest=36 * dest.eff / dest.minutes,
    ).rename(
        columns={
            "code": "api_code",
            "season": "true_season_dest",
            "games": "games_dest",
            "minutes": "minutes_dest",
            "team_code": "club_code_dest",
            "team_name": "club_dest",
        }
    )
    # The frozen rows carry the cohort's destination columns, all empty.
    incoming = {
        "games_dest",
        "minutes_dest",
        "club_code_dest",
        "club_dest",
        "was_cont",
        "pir_per36_dest",
    }
    linked = frozen.loc[frozen.api_code.notna()].drop(
        columns=sorted(incoming.intersection(frozen.columns))
    )
    rows = linked.merge(
        dest[
            [
                "api_code",
                "true_season_dest",
                "league_dest",
                "games_dest",
                "minutes_dest",
                "club_code_dest",
                "club_dest",
                "was_cont",
                "pir_per36_dest",
            ]
        ],
        on=["api_code", "true_season_dest", "league_dest"],
        how="inner",
    )
    incumbent = rows.was_cont.astype(bool)
    bad_source = ~rows.source_positive_finite.astype(bool)
    bad_outcome = ~(np.isfinite(rows.pir_per36_dest) & (rows.pir_per36_dest > 0))
    unforecast = ~rows.all_arms_forecast.astype(bool)
    kept = rows.loc[~(incumbent | bad_source | bad_outcome | unforecast)]
    kept = kept.sort_values("minutes_src", ascending=False)
    final = kept.drop_duplicates(["api_code", "true_season_dest"]).copy()
    counts = {
        "linked_source_rows_with_a_qualifying_destination_stint": int(len(rows)),
        "removed_incumbents": int(incumbent.sum()),
        "removed_source_rate_not_positive": int((~incumbent & bad_source).sum()),
        "removed_outcome_rate_not_positive": int(
            (~incumbent & ~bad_source & bad_outcome).sum()
        ),
        "removed_without_all_arms": int(
            (~incumbent & ~bad_source & ~bad_outcome & unforecast).sum()
        ),
        "removed_second_source_league_of_one_person": int(len(kept) - len(final)),
        "arrivals": int(len(final)),
    }
    final["frozen_key"] = final.player_name
    final["player_name"] = final.api_code
    final["season_dest"] = final.true_season_dest
    final["cluster"] = (
        final.true_season_dest.astype(str)
        + "|"
        + final.league_dest
        + "|"
        + final.club_code_dest.astype(str)
    )
    final["club_confirmed"] = [
        e26.clubs_match(a, b)
        for a, b in zip(final.club_dest, final.club_src, strict=True)
    ]
    final = final.sort_values(["true_season_dest", "player_name"])
    return final.reset_index(drop=True), counts


def reading(name: str, record: dict) -> str:
    """Amendment 7, "Readings and licences", as a fixed label."""
    low, high = record["ci95"]
    margin = record["margin"]
    if name == "history_gain":
        return (
            "above zero" if low > 0 else "below zero" if high < 0 else "includes zero"
        )
    if low <= 0 <= high:
        inside = -margin < low and high < margin
        return (
            "includes zero, inside the margin"
            if inside
            else "includes zero, wider than the margin"
        )
    return (
        "excludes zero, favours the first forecast"
        if high < 0
        else "excludes zero, favours the second forecast"
    )


def comparisons(rows: pd.DataFrame) -> list[dict]:
    if len(rows) < e26.MIN_SUBSET:
        return [
            {
                "comparison": n,
                "n": int(len(rows)),
                "difference": None,
                "ci95": None,
                "margin": None,
                "reading": "not estimable",
            }
            for n in e26.COMPARISONS
        ]
    sd = float(rows.pir_per36_dest.std(ddof=1))
    out = []
    for name in e26.COMPARISONS:
        record = e26.comparison(rows.reset_index(drop=True), name, sd)
        left, right = robust.CONTRASTS[name]
        out.append(
            {
                "comparison": name,
                "left": left,
                "right": right,
                "n": record["n"],
                "difference": record["difference"],
                "ci95": record["ci95"],
                "margin": record["margin"],
                "reading": reading(name, record) if record["ci95"] else "not estimable",
            }
        )
    return out


def score(frozen_path: Path, expected_sha: str, api_root: Path, out: Path) -> dict:
    if sha256_file(frozen_path) != expected_sha:  # G27e
        raise GateFailure("G27e: the forecast file does not match the pushed sha256")
    out.mkdir(parents=True, exist_ok=False)
    control = out / "_g27e_control.parquet"
    data = frozen_path.read_bytes()
    control.write_bytes(data[:-1] + (b"0" if data[-1:] != b"0" else b"1"))
    changed = sha256_file(control) != expected_sha
    control.unlink()
    if not changed:
        raise GateFailure("G27e negative control: a changed forecast file passed")
    api_files = check_api_pins(api_root)  # G27a, for the outcome files
    frozen = pd.read_parquet(frozen_path)
    api = api_seasons(api_root, PINNED_API_SEASONS)
    rows, selection = arrivals(frozen, api)
    rows.to_csv(out / "e27_arrivals.csv", index=False)
    table, versions = [], {}
    arms = list(common.PRIMARY_ARMS.values())
    for version, leagues in VERSIONS.items():
        part = rows.loc[rows.league.isin(leagues)]
        subsets = {
            "all": part,
            "rare surname": part.loc[part.rare_surname.astype(bool)],
            "club confirmed": part.loc[part.club_confirmed.astype(bool)],
            "with career history": part.loc[part.history_seasons > 0],
            **{f"league: {lg}": part.loc[part.league.eq(lg)] for lg in leagues},
            **{
                f"destination: {d}": part.loc[part.league_dest.eq(d)]
                for d in p1.DESTINATIONS
            },
        }
        for label, subset in subsets.items():
            for record in comparisons(subset):
                table.append({"version": version, "subset": label, **record})
        versions[version] = {
            "n": int(len(part)),
            "by_season": part.true_season_dest.value_counts().sort_index().to_dict(),
            "by_league": part.league.value_counts().to_dict(),
            "by_destination": part.league_dest.value_counts().to_dict(),
            "share_without_history": float((part.history_seasons == 0).mean())
            if len(part)
            else None,
            "share_club_confirmed": float(part.club_confirmed.mean())
            if len(part)
            else None,
            "share_rare_surname": float(part.rare_surname.mean())
            if len(part)
            else None,
            "mae": {
                a: float(np.mean(np.abs(part[a] - part.pir_per36_dest))) for a in arms
            },
            "mean_error": {
                a: float(np.mean(part[a] - part.pir_per36_dest)) for a in arms
            },
        }
    frame = pd.DataFrame(table)
    frame = frame.assign(
        ci_low=[c[0] if c else None for c in frame.ci95],
        ci_high=[c[1] if c else None for c in frame.ci95],
    ).drop(columns="ci95")
    frame.to_csv(out / "e27_comparisons.csv", index=False)
    summary = {
        "analysis": "E27 score",
        "amendment_commit": AMENDMENT_COMMIT,
        "amendment_sha256": sha256_file(AMENDMENT),
        "forecast_sha256": expected_sha,
        "gates": {
            "G27e_frozen_before_scored": {
                "status": "passed",
                "negative_control": "rejected as required",
            }
        },
        "outcome_api_files": api_files,
        "selection": selection,
        "versions": versions,
        "primary": {
            version: {
                r["comparison"]: {
                    k: r[k] for k in ("n", "difference", "ci95", "margin", "reading")
                }
                for r in table
                if r["version"] == version and r["subset"] == "all"
            }
            for version in VERSIONS
        },
    }
    (out / "e27_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n"
    )
    return summary


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    f = sub.add_parser("freeze")
    f.add_argument("--boxscores", type=Path, required=True)
    f.add_argument("--api", type=Path, required=True)
    f.add_argument("--input-dir", type=Path, required=True)
    f.add_argument("--out", type=Path, required=True)
    s = sub.add_parser("score")
    s.add_argument("--frozen", type=Path, required=True)
    s.add_argument("--expected-sha256", required=True)
    s.add_argument("--api", type=Path, required=True)
    s.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.command == "freeze":
        record = freeze(args.boxscores, args.api, args.input_dir, args.out)
        print(
            json.dumps(
                {
                    k: record[k]
                    for k in ("forecast_sha256", "rows", "source_player_seasons")
                }
            )
        )
    else:
        summary = score(args.frozen, args.expected_sha256, args.api, args.out)
        print(json.dumps({v: summary["versions"][v]["n"] for v in VERSIONS}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
