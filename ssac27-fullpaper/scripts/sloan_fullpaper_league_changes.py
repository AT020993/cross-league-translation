#!/usr/bin/env python3
"""Amendment 14 analysis: E30, the league table tested on league changes (REGISTERED).

Pre-registration: docs/research/sloan-full-paper-preregistration-2026-11-03.md
and its Amendment 14,
docs/research/sloan-full-paper-preregistration-amendment-14-2026-11-17.md
(pushed alone on 2026-11-17, before this file existed). E31b of Amendment 15
(docs/research/sloan-full-paper-preregistration-amendment-15-2026-11-17.md) is
computed in the same scoring run. Amendment 17
(docs/research/sloan-full-paper-preregistration-amendment-17-2026-11-17.md,
pushed alone before the freeze) fixes the readings this file had to choose
between; the freeze and the scoring run refuse to run unless that file is
byte-identical (gate G17a), and the freeze record names it by its sha256.

E30 asks whether the paper's league table (the European League Equivalents),
fitted only on first EuroLeague and EuroCup seasons, predicts what happens to
players who change domestic league. For a move from league A to league B the
table predicts a change g = equivalent(B) - equivalent(A). Every league changer
is measured against what the same season would predict for a player who
stayed (the stayer forecast). The primary result is the slope of the
unexplained change e on g.

Three subcommands, in the registered order of events:

* ``gates``  -- gate G30c on MADE-UP data only. Reads the pinned league table
  and nothing else. Writes ``e30_made_up_gates.json``.
* ``freeze`` -- reads the domestic box scores, checks the pins (G30a) and the
  registered counts (G30b), fits the stayer forecast on players who stayed and
  writes one row per league change (key, the two leagues, x, h, a, g, the
  stayer forecast). It joins no league changer's rate in the destination
  season, and this code path computes no e, no slope and no summary of
  outcomes: ``transitions`` attaches the next season's rate to stayers only.
* ``score``  -- reads the frozen file by its sha256 (G30e), joins the rates in
  the destination league and computes everything registered, and E31b.

Which function produces each input (the paper's own definitions):

* The player-league-season aggregates (games, minutes, EFF, EFF/36) are
  ``validate_translation_holdout.build_switchers`` (its second return value),
  called through ``sloan_fullpaper_prospective.aggregates``, on the corpus of
  ``build_league_factors.load_player_games("proballers")`` (raw Proballers
  ``player_name``; no continental API rows).
* x (last season's EFF/36 in the league with the most minutes), h (the career
  rate before it: all games on record in earlier seasons, domestic and
  continental, no minimum) and a = 1[x > h] are
  ``sloan_fullpaper_prospective.source_player_seasons`` (columns
  ``pir_per36_src``, ``prior_mean_pir36``, ``above_own_prior``). For a player
  with no earlier season h := x and a = 0.
* The population is the ten source leagues. ``source_player_seasons`` lets a
  larger Polish stint take the place of a stint in one of the ten leagues and
  then drops the player-season; under that reading the counts are 3,381 and
  9,031. The counts registered on 17 November (3,423 and 9,057) take the ten
  leagues first. ``eligible_sources`` therefore marks every stint outside the
  ten leagues as not eligible to be a source season before the repository
  function is called; those games still count in h.

Threats and their controls (Amendment 14, all in this file): stale or changed
inputs (G30a, sha256 pins, with a changed-byte control); a population that is
not the registered one (G30b, with a games floor of 9 as control); code that
cannot recover a slope (G30c on made-up outcomes, with shuffled league labels
as control); a slope where none can exist (G30d on stayers, with the made-up
change added as control); predictions changed after outcomes were seen (G30e,
the frozen file read by its pushed sha256, with a changed-byte control);
regression to the mean that differs by direction (the stayer forecast, S-c,
sensitivity 4); ten leagues and not thousands of tests (the permutation test,
S-b); wrong name links (sensitivities 1 and 6); a partial last season
(sensitivity 3). No 2026-27 statistic is read: a path or a row of season 2026
or later stops the run.
"""

# ruff: noqa: E501 -- gate messages and registered sentences
from __future__ import annotations

if __name__ == "__main__":
    import sys as _sys
    from pathlib import Path as _Path

    _sys.path.insert(0, str(_Path(__file__).resolve().parents[1]))
    from src.research.execution import enter as _enter

    _enter(__file__)

import argparse
import contextlib
import io
import json
import logging
import os
from pathlib import Path
import sys
import tempfile

for _name in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_name, "1")
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from scripts import build_league_factors as blf  # noqa: E402
from scripts import sloan_fullpaper_prospective as p1  # noqa: E402
from scripts import validate_translation_holdout as holdout  # noqa: E402
from scripts.translation_research_common import sha256_file  # noqa: E402

AMENDMENT = Path(
    "docs/research/sloan-full-paper-preregistration-amendment-14-2026-11-17.md"
)
AMENDMENT_SHA = "87471565393c01beb3ad4a5ce119fde74ac9d5c75fd96051944f16df5f476750"
AMENDMENT_15 = Path(
    "docs/research/sloan-full-paper-preregistration-amendment-15-2026-11-17.md"
)
AMENDMENT_15_SHA = "f078841abdd37dbcb463bf37d7525422f436b8ccc1967622e753b2a2c09a755f"
#: Amendment 17: the readings made explicit before the freeze (gate G17a).
AMENDMENT_17 = Path(
    "docs/research/sloan-full-paper-preregistration-amendment-17-2026-11-17.md"
)
AMENDMENT_17_SHA = "d2072f085a0cbb3381cfde3eb72eac47adbdd7185948037b0a3aad9df84350ae"

#: Amendment 14, "Pinned inputs".
TABLE = Path(
    "docs/research/artifacts/sloan-fullpaper-amend1-decisions-2026-11/exchange_rate_acb16.csv"
)
TABLE_SHA = "c8341a37947adcad882f90c9747ea6fee274723b367a0948bbfc50462fead2ca"
REFITS = Path(
    "docs/research/artifacts/sloan-fullpaper-amend3-2026-11/e19_equivalents_by_refit.csv"
)
REFITS_SHA = "49814ea0b0a2d4d443e891c4104fe480749876b32585861405454e7ebf502481"
#: Amendment 15, "Pinned inputs": the 2015 table, committed by the lead.
PUBLISHED = Path(
    "docs/research/artifacts/sloan-fullpaper-published-tables-2026-11/vashro_2015_competition_scores.csv"
)
PUBLISHED_SHA = "2c004c88d10c60f68dabb038330a9f8d282ba87f56b521cb6a87c59a26252d04"
#: The ten domestic values as printed in Amendment 15.
PUBLISHED_REGISTERED = {
    "spain-acb": 1.52,
    "italy-lba": 1.12,
    "vtb": 0.87,
    "aba-league": 0.82,
    "turkey-bsl": 0.77,
    "france-pro-a": 0.69,
    "germany-bbl": 0.65,
    "israel-bsl": 0.52,
    "greece-a1": 0.43,
    "lithuania-lkl": 0.33,
}

#: The ten source leagues of the paper, in a fixed order.
LEAGUES = (
    "aba-league",
    "france-pro-a",
    "germany-bbl",
    "greece-a1",
    "israel-bsl",
    "italy-lba",
    "lithuania-lkl",
    "spain-acb",
    "turkey-bsl",
    "vtb",
)
#: Names for sentences (Turkey and Israel are never both "BSL").
LEAGUE_NAMES = {
    "aba-league": "the Adriatic league",
    "france-pro-a": "France",
    "germany-bbl": "Germany",
    "greece-a1": "Greece",
    "israel-bsl": "Israel",
    "italy-lba": "Italy",
    "lithuania-lkl": "Lithuania",
    "spain-acb": "Spain",
    "turkey-bsl": "Turkey",
    "vtb": "the VTB United League",
}
MIN_GAMES = holdout.MIN_GAMES
LAST_SEASON = 2025  # stored season of 2025-26; nothing later may be read
ARRIVAL_SEASONS = tuple(range(2016, 2026))
#: Amendment 14, G30b.
EXPECTED = {"league_changes": 3423, "stayer_pairs": 9057}
#: Amendment 14, counted on 17 November and printed in the registration.
COUNTED = {
    "players": 1649,
    "ordered_league_pairs": 90,
    "smallest_ordered_pair_at_least": 10,
    "second_league_either_season": 447,
    "arrivals_2020_2025": 2083,
}
CONTROL_FLOOR = 9
N_BOOT = 2000
N_PERM = 10000
MADE_UP_PLAYERS = 20000
#: One seed for every random step, fixed before any run (the amendment's date).
SEED = 20261117
PLANTED_TOLERANCE = 0.05
#: Amendment 14, the Null wording: "a slope of 0.11 would have been detected
#: with 80% power under the planning assumptions".
PLANNING_DETECTABLE = "0.11"
REFIT_FROM = 2020  # sensitivity 7 and sensitivity 2
PARTIAL_LAST = 2024  # sensitivity 3 keeps arrivals up to here
STRICT_GAMES = 15  # sensitivity 6
PAIR_FLOOR = 30  # sensitivity 8
E31B_FIRST_SCORED = 2018

FROZEN_NAME = "e30_frozen_league_changes.parquet"
STAYERS_NAME = "e30_stayer_pairs.parquet"
FREEZE_NAME = "e30_freeze.json"
GATES_NAME = "e30_made_up_gates.json"
KEY = ["player_name", "season_from"]
FROZEN_COLUMNS = (
    "player_name",
    "season_from",
    "season_to",
    "league_from",
    "league_to",
    "games_from",
    "minutes_from",
    "x",
    "h_recorded",
    "h",
    "a",
    "g",
    "stayer_forecast",
    "g_euroleague",
    "g_refit",
    "stayer_forecast_origin",
    "second_league",
    "both_seasons_15_games",
    "pair_moves",
)
STAYER_COLUMNS = (
    "player_name",
    "season_from",
    "season_to",
    "league",
    "x",
    "h_recorded",
    "h",
    "a",
    "rate_next",
)
STAYER_TERMS = ("intercept", "x", "h", "a")

FUNCTIONS = {
    "corpus": "scripts/build_league_factors.py::load_player_games('proballers'), then add_usage",
    "aggregates": "scripts/sloan_fullpaper_prospective.py::aggregates (the second return value of scripts/validate_translation_holdout.py::build_switchers)",
    "x": "scripts/sloan_fullpaper_prospective.py::source_player_seasons, column pir_per36_src",
    "h": "scripts/sloan_fullpaper_prospective.py::source_player_seasons, column prior_mean_pir36; h := x where it is missing",
    "a": "scripts/sloan_fullpaper_prospective.py::source_player_seasons, column above_own_prior",
    "population": "eligible_sources (this file) marks stints outside the ten leagues as not eligible before source_player_seasons is called; their games still count in h",
    "g": "league_table (this file) on the pinned exchange_rate_acb16.csv, column acb16_equivalent_eff36, rows with destination eurocup",
    "stayer_forecast": "fit_stayers (this file): ordinary least squares of next season's rate on intercept, x, h and a, on players who stayed",
}


class GateFailure(RuntimeError):
    """A registered gate did not hold; nothing further is computed."""


def negative_control(check, *args, **kwargs) -> str:
    """A gate must reject its negative control, or it proves nothing."""
    try:
        check(*args, **kwargs)
    except GateFailure:
        return "rejected as required"
    raise GateFailure(f"negative control passed: {check.__name__}")


def clean(value):
    if isinstance(value, dict):
        return {str(k): clean(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [clean(v) for v in value]
    if isinstance(value, np.ndarray):
        return [clean(v) for v in value.tolist()]
    if isinstance(value, np.bool_):
        return bool(value)
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, (np.floating, float)):
        return float(value) if np.isfinite(value) else None
    return value


def write_json(path: Path, record: dict) -> None:
    Path(path).write_text(json.dumps(clean(record), indent=2, sort_keys=True) + "\n")


# ---------------------------------------------------------------------------
# Pinned inputs (G30a, G30e).


def check_pin(path: Path, expected: str) -> str:
    path = Path(path)
    if not path.is_file():
        raise GateFailure(f"pinned file is missing: {path}")
    found = sha256_file(path)
    if found != expected:
        raise GateFailure(f"{path} has sha256 {found}, pinned {expected}")
    return found


def changed_byte_control(path: Path, expected: str) -> str:
    """The same check on a copy with one byte changed must fail."""
    data = bytearray(Path(path).read_bytes())
    data[len(data) // 2] ^= 0x01
    with tempfile.TemporaryDirectory() as scratch:
        copy = Path(scratch) / Path(path).name
        copy.write_bytes(bytes(data))
        return negative_control(check_pin, copy, expected)


def pin_gate(root: Path, pins: dict) -> dict:
    """``pins``: name -> (relative path, sha256). Each must match; a changed byte must fail."""
    out = {}
    for name, (relative, expected) in pins.items():
        check_pin(Path(root) / relative, expected)
        out[name] = {
            "path": Path(relative).as_posix(),
            "sha256": expected,
            "negative_control_changed_byte": changed_byte_control(
                Path(root) / relative, expected
            ),
        }
    return {"status": "passed", "files": out}


def league_table(path: Path) -> pd.DataFrame:
    """The ten league values: EuroCup (registered), EuroLeague (sensitivity 5), spread (S-d)."""
    raw = pd.read_csv(path)
    wide = {}
    for destination, frame in raw.groupby("destination"):
        frame = frame.set_index("source_league")
        if sorted(frame.index) != sorted(LEAGUES):
            raise GateFailure(
                f"league table rows for {destination} are not the ten leagues"
            )
        wide[destination] = frame.loc[list(LEAGUES)]
    if sorted(wide) != ["eurocup", "euroleague"]:
        raise GateFailure("league table destinations are not eurocup and euroleague")
    ec = wide["eurocup"]
    return pd.DataFrame(
        {
            "eurocup": ec.acb16_equivalent_eff36.astype(float),
            "euroleague": wide["euroleague"].acb16_equivalent_eff36.astype(float),
            # S-d: "a normal distribution with the spread of its committed interval"
            "eurocup_sd": (ec.ci95_high - ec.ci95_low).astype(float) / 3.92,
        },
        index=pd.Index(LEAGUES, name="league"),
    )


def yearly_refits(path: Path) -> pd.DataFrame:
    """EuroCup equivalents refitted only on arrivals before each season (sensitivity 7)."""
    raw = pd.read_csv(path)
    raw = raw[raw.destination.eq("eurocup") & raw.refit_season.notna()]
    wide = raw.assign(refit_season=raw.refit_season.astype(int)).pivot(
        index="refit_season", columns="source_league", values="acb16_equivalent_eff36"
    )
    seasons = [s for s in ARRIVAL_SEASONS if s >= REFIT_FROM]
    if sorted(wide.columns) != sorted(LEAGUES) or not set(seasons) <= set(wide.index):
        raise GateFailure("yearly refits do not cover the ten leagues for 2020 to 2025")
    wide = wide.loc[seasons, list(LEAGUES)]
    if wide.isna().any().any():
        raise GateFailure("a yearly refit value is missing")
    return wide


def published_scores(path: Path) -> pd.Series:
    """The 2015 published table (Amendment 15); ``score`` refuses to run without it."""
    path = Path(path)
    if not path.is_file():
        raise GateFailure(f"the published-table file is missing: {path}")
    check_pin(path, PUBLISHED_SHA)
    scores = pd.read_csv(path).set_index("league").score.astype(float)
    for league, value in PUBLISHED_REGISTERED.items():
        if league not in scores.index or abs(scores[league] - value) > 1e-12:
            raise GateFailure(
                f"published score for {league} is not the registered {value}"
            )
    return scores.loc[list(LEAGUES)]


# ---------------------------------------------------------------------------
# The corpus: Proballers box scores, seasons 2015 to 2025.


def raw_files(root: Path) -> list[Path]:
    """The files ``load_player_games`` reads (paths only, nothing opened)."""
    return p1.raw_paths(Path(root))


def assert_seasons_allowed(paths) -> None:
    bad = [
        p
        for p in paths
        if any(part.isdigit() and int(part) > LAST_SEASON for part in Path(p).parts)
    ]
    if bad:
        raise GateFailure(
            f"{len(bad)} input paths are of a season after 2025-26, e.g. {bad[0]}"
        )


def raw_hashes(root: Path) -> dict:
    """sha256 of every box-score file the loader will read (no statistic is opened)."""
    root = Path(root).resolve()
    paths = raw_files(root)
    if not paths:
        raise GateFailure("no Proballers player_stats file under data/raw")
    assert_seasons_allowed(paths)
    return {p.relative_to(root).as_posix(): sha256_file(p) for p in paths}


def load_aggregates(root: Path):
    """(player-league-season aggregates, facts). Refuses any path or row after 2025-26."""
    root = Path(root).resolve()
    if Path(blf._ROOT).resolve() != root:
        raise GateFailure("the box-score loader reads another tree than the run's root")
    assert_seasons_allowed(raw_files(root))
    level = logging.getLogger().level
    logging.getLogger().setLevel(logging.WARNING)
    try:
        games = blf.load_player_games("proballers")
    finally:
        logging.getLogger().setLevel(level)
    if int(games.season.max()) > LAST_SEASON:
        raise GateFailure("the corpus holds a row of a season after 2025-26")
    agg = p1.aggregates(blf.add_usage(games))
    facts = {
        "files": len(raw_files(root)),
        "player_games": int(len(games)),
        "leagues": sorted(games.league.unique()),
        "seasons": [int(games.season.min()), int(games.season.max())],
    }
    return agg, facts


# ---------------------------------------------------------------------------
# Population: player-seasons, league changes and stayers.


def eligible_sources(agg: pd.DataFrame, min_games: int = MIN_GAMES) -> pd.DataFrame:
    """Mark stints that cannot be a source season, without removing their games.

    ``source_player_seasons`` keeps stints with ``games >= 8`` and takes the
    one with the most minutes. A stint outside the ten leagues, or below
    ``min_games``, gets ``games = 0`` here, so it cannot be chosen; its EFF and
    minutes stay in the frame and so stay in every later career rate h.
    """
    out = agg.copy()
    out.loc[~out.league.isin(LEAGUES) | (out.games < min_games), "games"] = 0
    return out


def player_seasons(agg: pd.DataFrame, min_games: int = MIN_GAMES) -> pd.DataFrame:
    """One row per qualifying player-season with x, h and a (repository functions)."""
    prepared = eligible_sources(agg, min_games)
    with contextlib.redirect_stdout(io.StringIO()):
        rows = pd.concat(
            [
                p1.source_player_seasons(prepared, int(season))
                for season in sorted(prepared.season.unique())
            ],
            ignore_index=True,
        )
    if not rows.league_src.isin(LEAGUES).all():
        raise GateFailure("a source season outside the ten leagues was selected")
    qualifying = prepared[
        (prepared.games >= holdout.MIN_GAMES) & (prepared.minutes > 0)
    ]
    leagues = (
        qualifying.groupby(["player_name", "season"])
        .league.nunique()
        .rename("domestic_leagues")
        .reset_index()
    )
    x = rows.pir_per36_src.astype(float)
    if not np.isfinite(x).all():
        raise GateFailure("a source rate is not finite")
    recorded = rows.prior_mean_pir36.astype(float)
    out = pd.DataFrame(
        {
            "player_name": rows.player_name,
            "season": rows.season_src.astype(int),
            "league": rows.league_src,
            "games": rows.games_src.astype(int),
            "minutes": rows.minutes_src.astype(float),
            "x": x,
            "h_recorded": recorded,
            "h": recorded.where(recorded.notna(), x),
            "a": rows.above_own_prior.astype(int),
        }
    ).merge(leagues, on=["player_name", "season"], how="left", validate="1:1")
    if (
        out.duplicated(["player_name", "season"]).any()
        or out.domestic_leagues.isna().any()
    ):
        raise GateFailure("player-seasons are not unique")
    if not (out.a == (out.x > out.h).astype(int)).all():
        raise GateFailure("a is not 1[x > h]")
    return out.sort_values(["player_name", "season"]).reset_index(drop=True)


def transitions(seasons: pd.DataFrame):
    """(league changes, stayers) over consecutive seasons t -> t+1.

    The next season contributes its league, its games and its count of
    domestic leagues to every pair. Its RATE is attached to stayers only: the
    frame of league changes never holds a rate of the destination season.
    """
    following = seasons[
        ["player_name", "season", "league", "games", "domestic_leagues"]
    ].rename(
        columns={
            "league": "league_to",
            "games": "games_to",
            "domestic_leagues": "domestic_leagues_to",
        }
    )
    following = following.assign(season=following.season - 1)
    pairs = seasons.merge(following, on=["player_name", "season"], validate="1:1")
    pairs = pairs.rename(columns={"season": "season_from", "league": "league_from"})
    pairs["season_to"] = pairs.season_from + 1
    changed = pairs.league_from != pairs.league_to
    moves = pairs.loc[changed].reset_index(drop=True)
    stayers = pairs.loc[~changed].reset_index(drop=True)
    rate_next = seasons[["player_name", "season", "league", "x"]].rename(
        columns={"season": "season_to", "league": "league_from", "x": "rate_next"}
    )
    stayers = stayers.merge(
        rate_next, on=["player_name", "season_to", "league_from"], validate="1:1"
    )
    if len(stayers) != int((~changed).sum()):
        raise GateFailure("a stayer has no rate in the next season")
    stayers = stayers.rename(columns={"league_from": "league"})
    return moves, stayers[list(STAYER_COLUMNS)]


def population_counts(moves: pd.DataFrame, stayers: pd.DataFrame) -> dict:
    ordered = moves.groupby(["league_from", "league_to"]).size()
    second = (moves.domestic_leagues > 1) | (moves.domestic_leagues_to > 1)
    return {
        "league_changes": int(len(moves)),
        "stayer_pairs": int(len(stayers)),
        "players": int(moves.player_name.nunique()),
        "ordered_league_pairs": int(len(ordered)),
        "smallest_ordered_pair": int(ordered.min()) if len(ordered) else 0,
        "second_league_either_season": int(second.sum()),
        "arrivals_2020_2025": int((moves.season_to >= REFIT_FROM).sum()),
        "by_arrival_season": {
            int(k): int(v) for k, v in moves.groupby("season_to").size().items()
        },
    }


def assert_counts(counts: dict, expected: dict | None = None) -> None:
    expected = EXPECTED if expected is None else expected
    found = {k: counts[k] for k in expected}
    if found != expected:
        raise GateFailure(
            f"population counts {found} are not the registered {expected}"
        )


def pair_ends(moves: pd.DataFrame):
    """The two leagues of each move in alphabetical order (the unordered pair)."""
    first = moves.league_from < moves.league_to
    low = moves.league_from.where(first, moves.league_to).rename("pair_low")
    high = moves.league_to.where(first, moves.league_from).rename("pair_high")
    return low, high


# ---------------------------------------------------------------------------
# The stayer forecast.


def design(frame: pd.DataFrame, origin: bool = False, league: str = "league_from"):
    """Intercept (or one intercept per league of origin), x, h, a."""
    base = np.column_stack(
        [frame.x.to_numpy(float), frame.h.to_numpy(float), frame.a.to_numpy(float)]
    )
    if not origin:
        return np.column_stack([np.ones(len(frame)), base])
    codes = pd.Categorical(frame[league], categories=list(LEAGUES)).codes
    if (codes < 0).any():
        raise GateFailure("a league of origin is not one of the ten")
    dummies = np.zeros((len(frame), len(LEAGUES)))
    dummies[np.arange(len(frame)), codes] = 1.0
    return np.column_stack([dummies, base])


def wls(X: np.ndarray, y: np.ndarray, w: np.ndarray | None = None) -> np.ndarray:
    """Least squares; integer weights w equal repeating each row w times."""
    Xw = X if w is None else X * w[:, None]
    return np.linalg.solve(Xw.T @ X, Xw.T @ y)


def fit_stayers(stayers: pd.DataFrame, origin: bool = False) -> dict:
    X = design(stayers, origin, league="league")
    y = stayers.rate_next.to_numpy(float)
    beta = wls(X, y)
    residual = y - X @ beta
    names = (
        [f"origin:{league}" for league in LEAGUES] + list(STAYER_TERMS[1:])
        if origin
        else list(STAYER_TERMS)
    )
    return {
        "coefficients": dict(zip(names, beta.tolist())),
        "beta": beta,
        "n": int(len(y)),
        "residual_sd": float(np.sqrt((residual**2).sum() / (len(y) - X.shape[1]))),
    }


# ---------------------------------------------------------------------------
# Freeze: predictions only. Nothing below this line up to "Analysis" reads,
# computes or stores a league changer's rate in the destination season.


def freeze_frames(seasons: pd.DataFrame, table: pd.DataFrame, refits=None):
    """(frozen league changes, stayer pairs, facts) from player-seasons and the table."""
    moves, stayers = transitions(seasons)
    main = fit_stayers(stayers)
    origin = fit_stayers(stayers, origin=True)
    g = moves.league_to.map(table.eurocup) - moves.league_from.map(table.eurocup)
    g_refit = pd.Series(np.nan, index=moves.index)
    if refits is not None:
        late = moves.season_to >= REFIT_FROM
        values = refits.stack()
        to = pd.MultiIndex.from_arrays([moves.season_to[late], moves.league_to[late]])
        frm = pd.MultiIndex.from_arrays(
            [moves.season_to[late], moves.league_from[late]]
        )
        g_refit[late] = values.reindex(to).to_numpy() - values.reindex(frm).to_numpy()
        if g_refit[late].isna().any():
            raise GateFailure(
                "a league change of 2020 to 2025 has no refitted table value"
            )
    low, high = pair_ends(moves)
    pair_moves = moves.groupby([low, high]).player_name.transform("size")
    frozen = pd.DataFrame(
        {
            "player_name": moves.player_name,
            "season_from": moves.season_from.astype(int),
            "season_to": moves.season_to.astype(int),
            "league_from": moves.league_from,
            "league_to": moves.league_to,
            "games_from": moves.games.astype(int),
            "minutes_from": moves.minutes.astype(float),
            "x": moves.x.astype(float),
            "h_recorded": moves.h_recorded.astype(float),
            "h": moves.h.astype(float),
            "a": moves.a.astype(int),
            "g": g.astype(float),
            "stayer_forecast": design(moves) @ main["beta"],
            "g_euroleague": (
                moves.league_to.map(table.euroleague)
                - moves.league_from.map(table.euroleague)
            ).astype(float),
            "g_refit": g_refit.astype(float),
            "stayer_forecast_origin": design(moves, origin=True) @ origin["beta"],
            "second_league": (moves.domestic_leagues > 1)
            | (moves.domestic_leagues_to > 1),
            "both_seasons_15_games": (moves.games >= STRICT_GAMES)
            & (moves.games_to >= STRICT_GAMES),
            "pair_moves": pair_moves.astype(int),
        }
    )
    frozen = frozen.sort_values(KEY).reset_index(drop=True)
    if tuple(frozen.columns) != FROZEN_COLUMNS:
        raise GateFailure("the frozen file has columns that were not registered")
    if frozen.duplicated(KEY).any():
        raise GateFailure("a league change appears twice in the frozen file")
    required = [c for c in FROZEN_COLUMNS if c not in ("h_recorded", "g_refit")]
    if frozen[required].isna().any().any():
        raise GateFailure("a frozen prediction is missing")
    stayers = stayers.sort_values(KEY).reset_index(drop=True)
    facts = {
        "stayer_model": {k: main[k] for k in ("coefficients", "n", "residual_sd")},
        "stayer_model_origin_intercepts": {
            k: origin[k] for k in ("coefficients", "n", "residual_sd")
        },
        "predicted_change": {
            "min": float(frozen.g.min()),
            "max": float(frozen.g.max()),
            "sd": float(frozen.g.std()),
            "zero": int((frozen.g == 0).sum()),
        },
        "counts": population_counts(moves, stayers),
        "sensitivity_rows": {
            "1_no_second_league": int((~frozen.second_league).sum()),
            "2_arrivals_2020_2025": int((frozen.season_to >= REFIT_FROM).sum()),
            "3_arrivals_2016_2024": int((frozen.season_to <= PARTIAL_LAST).sum()),
            "6_both_seasons_15_games": int(frozen.both_seasons_15_games.sum()),
            "7_refitted_table": int(frozen.g_refit.notna().sum()),
            "8_pairs_with_30_moves": int((frozen.pair_moves >= PAIR_FLOOR).sum()),
        },
        "no_earlier_season": int(frozen.h_recorded.isna().sum()),
    }
    return frozen, stayers, facts


def repository_rows(agg: pd.DataFrame) -> pd.DataFrame:
    """``source_player_seasons`` on the aggregates as they are, every season."""
    with contextlib.redirect_stdout(io.StringIO()):
        return pd.concat(
            [
                p1.source_player_seasons(agg, int(season))
                for season in sorted(agg.season.unique())
            ],
            ignore_index=True,
        ).rename(columns={"season_src": "season"})


def assert_repository_values(
    agg: pd.DataFrame, seasons: pd.DataFrame, shift: float = 0.0
) -> int:
    """x, h and a equal the repository function on the unmodified aggregates.

    ``source_player_seasons`` on the aggregates as they are returns a subset of
    the registered player-seasons (it drops a player-season whose largest stint
    was in Poland). On every row it returns, league, x, h and a must be equal.
    ``shift`` exists for the negative control only.
    """
    reference = repository_rows(agg)
    both = reference.merge(seasons, on=["player_name", "season"], validate="1:1")
    if len(both) != len(reference):
        raise GateFailure(
            "a repository source season is not in the registered population"
        )
    same = (
        both.league_src.eq(both.league)
        & (both.pir_per36_src == both.x + shift)
        & (
            (both.prior_mean_pir36 == both.h_recorded)
            | (both.prior_mean_pir36.isna() & both.h_recorded.isna())
        )
        & (both.above_own_prior.astype(int) == both.a)
    )
    if not same.all():
        raise GateFailure(
            f"{int((~same).sum())} player-seasons differ from the repository function"
        )
    return int(len(both))


def unmodified_rule_counts(agg: pd.DataFrame) -> dict:
    """Counts if ``source_player_seasons`` were used as it is (Poland competes)."""
    rows = repository_rows(agg)[["player_name", "season", "league_src"]]
    following = rows.assign(season=rows.season - 1).rename(
        columns={"league_src": "league_to"}
    )
    pairs = rows.merge(following, on=["player_name", "season"], validate="1:1")
    changed = pairs.league_src != pairs.league_to
    return {
        "league_changes": int(changed.sum()),
        "stayer_pairs": int((~changed).sum()),
    }


def freeze(root: Path, gates_path: Path, out: Path) -> dict:
    root = Path(root)
    made_up = json.loads(Path(gates_path).read_text())
    if made_up.get("status") != "passed" or made_up.get("seed") != SEED:
        raise GateFailure("G30c has not passed on made-up data; nothing is frozen")
    pins = {
        "amendment_14": (AMENDMENT, AMENDMENT_SHA),
        "amendment_17": (AMENDMENT_17, AMENDMENT_17_SHA),
        "league_table": (TABLE, TABLE_SHA),
        "yearly_refits": (REFITS, REFITS_SHA),
    }
    g30a = pin_gate(
        root, pins
    )  # G17a: stops here if Amendment 17 is not the pushed file
    table = league_table(root / TABLE)
    refits = yearly_refits(root / REFITS)
    hashes = raw_hashes(root)
    agg, corpus_facts = load_aggregates(root)

    seasons = player_seasons(agg)
    frozen, stayers, facts = freeze_frames(seasons, table, refits)
    counts = facts["counts"]
    assert_counts(counts)  # G30b: stops here, before anything is written
    control = player_seasons(agg, CONTROL_FLOOR)
    control_moves, control_stayers = transitions(control)
    control_counts = population_counts(control_moves, control_stayers)
    g30b = {
        "status": "passed",
        "registered": EXPECTED,
        "found": {k: counts[k] for k in EXPECTED},
        "negative_control": {
            "games_floor": CONTROL_FLOOR,
            "found": {k: control_counts[k] for k in EXPECTED},
            "result": negative_control(assert_counts, control_counts),
        },
        "counted_on_17_november": {
            name: {
                "registered": value,
                "found": counts[key],
                "equal": counts[key] == value,
            }
            for name, key, value in (
                ("players", "players", COUNTED["players"]),
                (
                    "ordered_league_pairs",
                    "ordered_league_pairs",
                    COUNTED["ordered_league_pairs"],
                ),
                (
                    "second_league_either_season",
                    "second_league_either_season",
                    COUNTED["second_league_either_season"],
                ),
                (
                    "arrivals_2020_2025",
                    "arrivals_2020_2025",
                    COUNTED["arrivals_2020_2025"],
                ),
            )
        },
        "smallest_ordered_pair": counts["smallest_ordered_pair"],
        "every_ordered_pair_holds_at_least_10": counts["smallest_ordered_pair"]
        >= COUNTED["smallest_ordered_pair_at_least"],
    }
    repository = {
        "status": "passed",
        "counts_under_the_unmodified_repository_rule": unmodified_rule_counts(agg),
        "rows_compared": assert_repository_values(agg, seasons),
        "rows_only_in_the_registered_population": int(len(seasons))
        - assert_repository_values(agg, seasons),
        "negative_control_shifted_rate": negative_control(
            assert_repository_values, agg, seasons, 1e-6
        ),
    }

    out = Path(out)
    out.mkdir(parents=True, exist_ok=False)
    frozen.to_parquet(out / FROZEN_NAME, index=False)
    stayers.to_parquet(out / STAYERS_NAME, index=False)
    record = {
        "analysis": "Amendment 14, E30: frozen predictions for every league change (no outcome joined)",
        "registered": True,
        "amendment": {"path": AMENDMENT.as_posix(), "sha256": AMENDMENT_SHA},
        "amendment_17": {
            "path": AMENDMENT_17.as_posix(),
            "sha256": AMENDMENT_17_SHA,
            "role": "the readings of Amendments 14 to 16 fixed before this freeze",
        },
        "outcome_joined": False,
        "seed": SEED,
        "registered_constants": {
            "bootstrap_draws": N_BOOT,
            "permutation_draws": N_PERM,
            "games_floor": MIN_GAMES,
            "arrival_seasons": [ARRIVAL_SEASONS[0], ARRIVAL_SEASONS[-1]],
        },
        "functions": FUNCTIONS,
        "inputs": {
            "pinned": {
                k: {"path": Path(p).as_posix(), "sha256": s}
                for k, (p, s) in pins.items()
            },
            "raw_files": hashes,
            "corpus": corpus_facts,
            "made_up_gates_sha256": sha256_file(gates_path),
        },
        "league_table": {
            league: {k: float(table.loc[league, k]) for k in table.columns}
            for league in LEAGUES
        },
        "player_seasons": int(len(seasons)),
        **facts,
        "gates": {
            "G17a": {
                "status": "passed",
                "rule": "the freeze names Amendment 17 by its sha256 and refuses to run on any other file",
                **g30a["files"]["amendment_17"],
            },
            "G30a": g30a,
            "G30b": g30b,
            "G30c": {
                "status": made_up["status"],
                "where": "the gates subcommand, on made-up data only",
                "planted_slope_one": made_up["planted_slope_one"],
                "planted_slope_zero": made_up["planted_slope_zero"],
                "negative_control_shuffled_leagues": made_up[
                    "negative_control_shuffled_leagues"
                ],
            },
            "repository_values": repository,
            "no_2026_27_input": {
                "status": "passed",
                "last_season_read": corpus_facts["seasons"][1],
            },
        },
        "files": {
            "frozen": {
                "name": FROZEN_NAME,
                "sha256": sha256_file(out / FROZEN_NAME),
                "rows": int(len(frozen)),
                "columns": list(FROZEN_COLUMNS),
            },
            "stayers": {
                "name": STAYERS_NAME,
                "sha256": sha256_file(out / STAYERS_NAME),
                "rows": int(len(stayers)),
                "columns": list(STAYER_COLUMNS),
            },
        },
    }
    write_json(out / FREEZE_NAME, record)
    return record


# ---------------------------------------------------------------------------
# Analysis (used by ``gates`` on made-up outcomes and by ``score``).


def interval(draws) -> list:
    """Percentile 95% interval, the rule of the paper's other bootstraps."""
    d = np.asarray(draws, float)
    d = d[np.isfinite(d)]
    if not len(d):  # a statistic with no league change behind it (made-up trees only)
        return [np.nan, np.nan]
    return [float(np.percentile(d, 2.5)), float(np.percentile(d, 97.5))]


def wslope(g: np.ndarray, e: np.ndarray, w: np.ndarray):
    """(slope, intercept) of the weighted least-squares line of e on g."""
    total = w.sum()
    if total <= 0:
        return np.nan, np.nan
    g_mean = (w * g).sum() / total
    e_mean = (w * e).sum() / total
    spread = (w * (g - g_mean) ** 2).sum()
    if spread <= 0:
        return np.nan, np.nan
    slope = (w * (g - g_mean) * (e - e_mean)).sum() / spread
    return slope, e_mean - slope * g_mean


def wmean(values: np.ndarray, w: np.ndarray) -> float:
    total = w.sum()
    return float((w * values).sum() / total) if total > 0 else np.nan


def context(
    moves: pd.DataFrame, stayers: pd.DataFrame, table: pd.DataFrame, published=None
) -> dict:
    """Arrays for the statistics. ``moves`` carries the outcome in ``rate_to``."""
    players = pd.Index(
        np.unique(
            np.concatenate(
                [stayers.player_name.to_numpy(), moves.player_name.to_numpy()]
            )
        )
    )
    frm = pd.Categorical(moves.league_from, categories=list(LEAGUES)).codes
    to = pd.Categorical(moves.league_to, categories=list(LEAGUES)).codes
    if (frm < 0).any() or (to < 0).any():
        raise GateFailure("a league change names a league outside the ten")
    season = moves.season_to.to_numpy(int)
    g = moves.g.to_numpy(float)
    eq = table.eurocup.to_numpy(float)
    masks = {}
    for k, league in enumerate(LEAGUES):
        masks[f"lolo:{league}"] = (frm != k) & (to != k)
    masks["up"] = g > 0
    masks["down"] = g < 0
    masks["sens:1"] = ~moves.second_league.to_numpy(bool)
    masks["sens:2"] = season >= REFIT_FROM
    masks["sens:3"] = season <= PARTIAL_LAST
    masks["sens:6"] = moves.both_seasons_15_games.to_numpy(bool)
    masks["sens:7"] = np.isfinite(moves.g_refit.to_numpy(float))
    masks["sens:8"] = moves.pair_moves.to_numpy(int) >= PAIR_FLOOR
    ctx = {
        "n_players": len(players),
        "stayer_player": players.get_indexer(stayers.player_name),
        "move_player": players.get_indexer(moves.player_name),
        "SX": design(stayers, league="league"),
        "SX_origin": design(stayers, origin=True, league="league"),
        "Sy": stayers.rate_next.to_numpy(float),
        "MX": design(moves),
        "MX_origin": design(moves, origin=True),
        "My": moves.rate_to.to_numpy(float),
        "g": g,
        "g_euroleague": moves.g_euroleague.to_numpy(float),
        "g_refit": np.nan_to_num(moves.g_refit.to_numpy(float)),
        "from": frm,
        "to": to,
        "season_index": season - ARRIVAL_SEASONS[0],
        "scored": season >= E31B_FIRST_SCORED,
        "masks": {k: v.astype(float) for k, v in masks.items()},
        "eq": eq,
        "eq_sd": table.eurocup_sd.to_numpy(float),
        "published_difference": None,
    }
    if not np.allclose(eq[to] - eq[frm], g, rtol=0, atol=1e-12):
        raise GateFailure("the frozen predicted change is not the table's difference")
    if published is not None:
        scores = published.loc[list(LEAGUES)].to_numpy(float)
        ctx["published_difference"] = scores[to] - scores[frm]
    if not np.isfinite(ctx["My"]).all() or not np.isfinite(ctx["Sy"]).all():
        raise GateFailure("an outcome is missing")
    return ctx


def walk_forward(e, d, w, season_index, scored):
    """One coefficient per arrival season, fitted (through the origin) on earlier arrivals.

    Returns (coefficient by season, weighted mean absolute error of the stayer
    forecast plus coefficient x d on the scored league changes).
    """
    k = len(ARRIVAL_SEASONS)
    num = np.bincount(season_index, weights=w * e * d, minlength=k)
    den = np.bincount(season_index, weights=w * d * d, minlength=k)
    earlier_num = np.cumsum(num) - num
    earlier_den = np.cumsum(den) - den
    with np.errstate(divide="ignore", invalid="ignore"):
        coefficient = np.where(earlier_den > 0, earlier_num / earlier_den, np.nan)
    error = np.abs(e - coefficient[season_index] * d)
    return coefficient, wmean(error[scored], w[scored])


def draw_statistics(ctx: dict, ws, wm, eq=None, primary_only: bool = False) -> dict:
    """Every registered statistic for one set of player weights.

    Unit weights give the point estimates. In a bootstrap draw the weights are
    how often each player was drawn, and the stayer forecast is refitted here.
    """
    beta = wls(ctx["SX"], ctx["Sy"], ws)
    e = ctx["My"] - ctx["MX"] @ beta
    g = ctx["g"]
    slope, intercept = wslope(g, e, wm)
    out = {"slope": slope}
    if primary_only:
        return out
    out["intercept"] = intercept
    masks = ctx["masks"]
    for league in LEAGUES:
        out[f"lolo:{league}"] = wslope(g, e, wm * masks[f"lolo:{league}"])[0]
    for direction in ("up", "down"):
        w = wm * masks[direction]
        out[f"direction:{direction}:slope"] = wslope(g, e, w)[0]
        out[f"direction:{direction}:mean_e"] = wmean(e, w)
    out["mae:stayer"] = wmean(np.abs(e), wm)
    out["mae:stayer_plus_g"] = wmean(np.abs(e - g), wm)
    out["mae:difference"] = out["mae:stayer"] - out["mae:stayer_plus_g"]
    for k in (1, 2, 3, 6, 8):
        out[f"sens:{k}"] = wslope(g, e, wm * masks[f"sens:{k}"])[0]
    beta_origin = wls(ctx["SX_origin"], ctx["Sy"], ws)
    out["sens:4"] = wslope(g, ctx["My"] - ctx["MX_origin"] @ beta_origin, wm)[0]
    out["sens:5"] = wslope(ctx["g_euroleague"], e, wm)[0]
    out["sens:7"] = wslope(ctx["g_refit"], e, wm * masks["sens:7"])[0]
    if eq is not None:
        out["table_redrawn"] = wslope(eq[ctx["to"]] - eq[ctx["from"]], e, wm)[0]
    if ctx["published_difference"] is not None:
        scored = ctx["scored"]
        out["e31b:mae:stayer"] = wmean(np.abs(e[scored]), wm[scored])
        for name, d in (("paper", g), ("published", ctx["published_difference"])):
            coefficient, error = walk_forward(e, d, wm, ctx["season_index"], scored)
            out[f"e31b:mae:{name}"] = error
            for season, value in zip(ARRIVAL_SEASONS, coefficient):
                if season >= E31B_FIRST_SCORED:
                    out[f"e31b:coefficient:{name}:{season}"] = value
        out["e31b:difference"] = out["e31b:mae:published"] - out["e31b:mae:paper"]
    return out


def point_estimates(ctx: dict, primary_only: bool = False) -> dict:
    ones_s = np.ones(len(ctx["Sy"]))
    ones_m = np.ones(len(ctx["My"]))
    return draw_statistics(ctx, ones_s, ones_m, None, primary_only)


def bootstrap(
    ctx: dict, n_boot: int = N_BOOT, seed: int = SEED, primary_only: bool = False
) -> dict:
    """Resample players; refit the stayer forecast in every draw (Amendment 14)."""
    rng = np.random.default_rng([seed, 0])
    table_rng = np.random.default_rng([seed, 1])
    n = ctx["n_players"]
    draws: dict = {}
    for b in range(n_boot):
        counts = np.bincount(rng.integers(0, n, n), minlength=n).astype(float)
        eq = None
        if not primary_only:
            # S-d: the ten table values redrawn as well (an approximation)
            eq = ctx["eq"] + ctx["eq_sd"] * table_rng.standard_normal(len(LEAGUES))
        stats = draw_statistics(
            ctx,
            counts[ctx["stayer_player"]],
            counts[ctx["move_player"]],
            eq,
            primary_only,
        )
        for name, value in stats.items():
            draws.setdefault(name, np.full(n_boot, np.nan))[b] = value
    return draws


def permutation(
    ctx: dict, slope: float, n_perm: int = N_PERM, seed: int = SEED
) -> dict:
    """Reassign the ten table values among the ten leagues; the stayer forecast is fixed."""
    rng = np.random.default_rng([seed, 2])
    e = ctx["My"] - ctx["MX"] @ wls(ctx["SX"], ctx["Sy"])
    centred = e - e.mean()
    slopes = np.empty(n_perm)
    for start in range(0, n_perm, 500):
        size = min(500, n_perm - start)
        values = np.stack([rng.permutation(ctx["eq"]) for _ in range(size)])
        g = values[:, ctx["to"]] - values[:, ctx["from"]]
        g = g - g.mean(axis=1, keepdims=True)
        slopes[start : start + size] = (g @ centred) / (g**2).sum(axis=1)
    at_least = int((slopes >= slope).sum())
    return {
        "draws": int(n_perm),
        "draws_with_slope_at_least_as_large": at_least,
        "p": at_least / n_perm,
        "permuted_slope_quantiles": {
            q: float(np.percentile(slopes, float(q))) for q in ("2.5", "50", "97.5")
        },
    }


def number(value: float, digits: int = 2) -> str:
    return f"{value:.{digits}f}".replace("-", "−")


def span(ci95, digits: int = 2) -> str:
    return f"95% interval {number(ci95[0], digits)} to {number(ci95[1], digits)}"


def classify(slope: float, ci95, p: float, leave_one_out: dict, n_players: int) -> dict:
    """Amendment 14, "What the paper may say": the case and its registered wording."""
    lo, hi = ci95
    includes_zero = [
        k for k, v in leave_one_out.items() if v["ci95"][0] <= 0 <= v["ci95"][1]
    ]
    below_zero = [k for k, v in leave_one_out.items() if v["ci95"][1] < 0]
    reading = f"slope {number(slope)} ({span(ci95)})"
    inner = f"slope {number(slope)}, {span(ci95)}"
    out = {
        "leagues_whose_interval_includes_zero": includes_zero,
        "leagues_whose_interval_lies_below_zero": below_zero,
        "size_reading": None,
        "limits": [],
        "unregistered": [],
        "to_amir_before_writing": False,
    }
    if hi < 0:
        out.update(
            case="Against",
            to_amir_before_writing=True,
            sentence=f"players who changed league moved against the table ({inner})",
        )
        return out
    if lo <= 0:
        out.update(
            case="Null",
            to_amir_before_writing=True,
            sentence=f"the league table did not predict what happened to players who changed domestic league ({inner}; a slope of {PLANNING_DETECTABLE} would have been detected with 80% power under the planning assumptions)",
        )
        return out
    if p >= 0.05:
        out.update(
            case="Positive, not separable from chance",
            sentence=f"a positive slope ({number(slope)}, {span(ci95)}) that a random assignment of the ten league values produces in {number(100 * p, 1)}% of draws; with ten leagues the test cannot tell the table's order from chance",
        )
        return out
    clear = f"The league table, fitted only on first continental seasons, predicted what happened to {n_players:,} players who changed domestic league: {reading}, where 1 would mean the table's size is exactly right."
    if lo <= 1 <= hi:
        out["size_reading"] = "consistent with the table's size"
    elif hi < 1:
        out["size_reading"] = f"about {number(slope)} of the size the table implies"
    else:
        # Amendment 17, rule 7: the interval lies wholly above 1
        out["size_reading"] = "larger than the table implies"
    # Amendment 14 names a league whose leave-one-out interval includes zero;
    # Amendment 17, rule 7 names one whose interval lies wholly below zero
    out["limits"] = [
        f"without {LEAGUE_NAMES[league]} the interval includes zero"
        for league in includes_zero
    ] + [
        f"without {LEAGUE_NAMES[league]} the slope is below zero ({span(leave_one_out[league]['ci95'])})"
        for league in below_zero
    ]
    if not out["limits"]:
        out.update(case="Clear", sentence=clear)
        return out
    out.update(
        case="Positive, with a named limit",
        sentence=f"{clear} {'; '.join(out['limits'])}",
        to_amir_before_writing=bool(below_zero),
    )
    return out


def pair_picture(
    moves: pd.DataFrame, e: np.ndarray, table: pd.DataFrame
) -> pd.DataFrame:
    """S-f: per league pair, half the difference between the two directions against g."""
    frame = moves[["league_from", "league_to"]].assign(e=e)
    rows = []
    leagues = sorted(LEAGUES, key=lambda k: (table.eurocup[k], k))
    for i, lower in enumerate(leagues):
        for higher in leagues[i + 1 :]:
            up = frame[(frame.league_from == lower) & (frame.league_to == higher)].e
            down = frame[(frame.league_from == higher) & (frame.league_to == lower)].e
            both = len(up) > 0 and len(down) > 0
            rows.append(
                {
                    "league_lower_equivalent": lower,
                    "league_higher_equivalent": higher,
                    "predicted_change": float(
                        table.eurocup[higher] - table.eurocup[lower]
                    ),
                    "moves_to_higher": int(len(up)),
                    "moves_to_lower": int(len(down)),
                    "n_up": int(len(up)),
                    "n_down": int(len(down)),
                    "mean_e_to_higher": float(up.mean()) if len(up) else np.nan,
                    "mean_e_to_lower": float(down.mean()) if len(down) else np.nan,
                    "half_difference": float((up.mean() - down.mean()) / 2)
                    if both
                    else np.nan,
                }
            )
    return pd.DataFrame(rows)


SENSITIVITIES = {
    1: "without league changes where either season has a second domestic league with 8 or more games",
    2: "arrival seasons 2020 to 2025 only",
    3: "arrival seasons 2016 to 2024 only (four leagues' 2025-26 files stop in January 2026)",
    4: "the stayer forecast with one intercept per league of origin",
    5: "the EuroLeague equivalents in place of the EuroCup ones",
    6: "at least 15 games in both seasons",
    7: "arrival seasons 2020 to 2025, the table refitted only on arrivals before that season",
    8: "league pairs with fewer than 30 moves in the two directions together left out",
}


def analyse(
    moves, stayers, table, published=None, *, n_boot=N_BOOT, n_perm=N_PERM, seed=SEED
):
    """Everything Amendment 14 registers, and E31b of Amendment 15 when ``published`` is given."""
    ctx = context(moves, stayers, table, published)
    point = point_estimates(ctx)
    draws = bootstrap(ctx, n_boot, seed)
    masks = ctx["masks"]

    def entry(name, n=None):
        return {
            "estimate": float(point[name]),
            "ci95": interval(draws[name]),
            **({} if n is None else {"league_changes": int(n)}),
        }

    n_moves = len(moves)
    primary = entry("slope", n_moves)
    primary["intercept"] = float(point["intercept"])
    primary["bootstrap_se"] = float(np.nanstd(draws["slope"], ddof=1))
    # descriptive, the repository's power line (2.80 x bootstrap SE); the registered
    # Null wording quotes the planning value instead
    primary["detectable_slope_80"] = 2.80 * primary["bootstrap_se"]
    primary["permutation"] = permutation(ctx, point["slope"], n_perm, seed)
    leave_one_out = {
        league: entry(f"lolo:{league}", masks[f"lolo:{league}"].sum())
        for league in LEAGUES
    }
    n_players = int(moves.player_name.nunique())
    case = classify(
        primary["estimate"],
        primary["ci95"],
        primary["permutation"]["p"],
        leave_one_out,
        n_players,
    )
    directions = {
        d: {
            "league_changes": int(masks[d].sum()),
            "slope": entry(f"direction:{d}:slope"),
            "mean_e": entry(f"direction:{d}:mean_e"),
        }
        for d in ("up", "down")
    }
    signs = [np.sign(directions[d]["slope"]["estimate"]) for d in ("up", "down")]
    sensitivities = {}
    for k, label in SENSITIVITIES.items():
        n = masks[f"sens:{k}"].sum() if f"sens:{k}" in masks else n_moves
        sensitivities[str(k)] = {"label": label, **entry(f"sens:{k}", n)}
    e = ctx["My"] - ctx["MX"] @ wls(ctx["SX"], ctx["Sy"])
    summary = {
        "league_changes": int(n_moves),
        "players": n_players,
        "n_league_changes": int(n_moves),
        "n_players": n_players,  # Amendment 17, rule 4: N in the registered sentence
        "stayer_pairs": int(len(stayers)),
        "bootstrap_draws": int(n_boot),
        "seed": int(seed),
        "primary": primary,
        "case": case,
        "S_a": {
            "mae_stayer_forecast": float(point["mae:stayer"]),
            "mae_stayer_forecast_plus_g": float(point["mae:stayer_plus_g"]),
            "difference": entry("mae:difference"),
            "reading": "positive: adding the table's predicted change lowers the error",
        },
        "S_b": leave_one_out,
        "S_c": {
            "to_higher_equivalent": directions["up"],
            "to_lower_equivalent": directions["down"],
            "opposite_signs": bool(signs[0] * signs[1] < 0),
        },
        "S_d": {
            "ci95": interval(draws["table_redrawn"]),
            "use": "reported for its width only: redrawing the table values adds noise to the predicted change, so its centre sits low by construction; it does not decide the case (Amendment 17, rule 6)",
            "approximation": "each table value redrawn from a normal distribution with standard deviation (upper - lower) / 3.92 of its committed interval, independently; the committed files hold intervals and not the bootstrap draws",
        },
        "S_e": sensitivities,
        "S_f": pair_picture(moves, e, table).to_dict("records"),
    }
    if published is not None:
        seasons = [s for s in ARRIVAL_SEASONS if s >= E31B_FIRST_SCORED]
        difference = entry("e31b:difference")
        lo, hi = difference["ci95"]
        value = difference["estimate"]
        if lo <= 0 <= hi:
            reading = "not distinguishable"
        elif lo > 0:
            reading = f"the paper's equivalents predicted league changes better by {number(value, 3)} ({span(difference['ci95'], 3)})"
        else:
            reading = f"the 2015 table predicted league changes better by {number(-value, 3)} ({span([-hi, -lo], 3)})"
        summary["E31b"] = {
            "scored_league_changes": int(ctx["scored"].sum()),
            "first_scored_arrival_season": E31B_FIRST_SCORED,
            "mae_stayer_forecast": entry("e31b:mae:stayer"),
            "scales": {
                name: {
                    "mae": entry(f"e31b:mae:{name}"),
                    "coefficient_by_scored_season": {
                        str(s): entry(f"e31b:coefficient:{name}:{s}") for s in seasons
                    },
                }
                for name in ("paper", "published")
            },
            "difference_published_minus_paper": difference,
            "reading": reading,
            "to_amir_before_writing": bool(value <= 0),
        }
    return summary


# ---------------------------------------------------------------------------
# Gates on made-up data (G30c) and on stayers (G30d).


def made_up_seasons(n_players: int = MADE_UP_PLAYERS, seed: int = SEED) -> pd.DataFrame:
    """Made-up player-seasons in the ten leagues. No real player, rate or move."""
    rng = np.random.default_rng([seed, 10])
    start = rng.integers(2015, 2022, n_players)
    length = rng.integers(2, 7, n_players)
    league = rng.integers(0, len(LEAGUES), n_players)
    talent = rng.normal(0, 1.5, n_players)
    names = np.array([f"made-up-{k:05d}" for k in range(n_players)])
    x = 12 + talent + rng.normal(0, 4, n_players)
    total = np.zeros(n_players)
    count = np.zeros(n_players)
    frames = []
    for step in range(6):
        active = (step < length) & (start + step <= LAST_SEASON)
        recorded = np.where(count > 0, total / np.maximum(count, 1), np.nan)
        h = np.where(np.isnan(recorded), x, recorded)
        a = (x > h).astype(int)
        frames.append(
            pd.DataFrame(
                {
                    "player_name": names[active],
                    "season": (start + step)[active],
                    "league": np.array(LEAGUES)[league[active]],
                    "games": 20,
                    "minutes": 600.0,
                    "x": x[active],
                    "h_recorded": recorded[active],
                    "h": h[active],
                    "a": a[active],
                    "domestic_leagues": 1,
                }
            )
        )
        total += x
        count += 1
        following = 3.5 + 0.55 * x + 0.2 * h - 0.6 * a + 0.5 * talent
        moved = rng.random(n_players) < 0.27
        elsewhere = (league + rng.integers(1, len(LEAGUES), n_players)) % len(LEAGUES)
        league = np.where(moved, elsewhere, league)
        x = following + rng.normal(0, 2.5, n_players)
    out = pd.concat(frames, ignore_index=True)
    return out.sort_values(["player_name", "season"]).reset_index(drop=True)


def planted_outcomes(
    frozen: pd.DataFrame, slope: float, seed: int = SEED
) -> np.ndarray:
    """G30c: made-up outcomes built as stayer forecast + slope x g + noise."""
    rng = np.random.default_rng([seed, 11])
    _, player = np.unique(frozen.player_name.to_numpy(), return_inverse=True)
    noise = rng.normal(0, 1.0, player.max() + 1)[player] + rng.normal(
        0, 2.3, len(frozen)
    )
    return (
        frozen.stayer_forecast.to_numpy(float)
        + slope * frozen.g.to_numpy(float)
        + noise
    )


def shuffle_leagues(
    moves: pd.DataFrame, table: pd.DataFrame, seed: int = SEED
) -> pd.DataFrame:
    """League labels shuffled across the moves; g follows the shuffled labels."""
    order = np.random.default_rng([seed, 12]).permutation(len(moves))
    out = moves.copy()
    out["league_from"] = moves.league_from.to_numpy()[order]
    out["league_to"] = moves.league_to.to_numpy()[order]
    for column, scale in (("g", table.eurocup), ("g_euroleague", table.euroleague)):
        out[column] = (out.league_to.map(scale) - out.league_from.map(scale)).astype(
            float
        )
    return out


def primary_result(ctx: dict, n_boot: int, seed: int) -> dict:
    """The primary slope with its registered bootstrap interval, and nothing else."""
    slope = point_estimates(ctx, primary_only=True)["slope"]
    draws = bootstrap(ctx, n_boot, seed, primary_only=True)
    return {"slope": float(slope), "ci95": interval(draws["slope"])}


def assert_planted_slope(result: dict, tolerance: float = PLANTED_TOLERANCE) -> None:
    if not abs(result["slope"] - 1.0) <= tolerance:
        raise GateFailure(f"planted slope 1.0 came back as {result['slope']:.4f}")


def assert_includes_zero(result: dict) -> None:
    lo, hi = result["ci95"]
    if not lo <= 0 <= hi:
        raise GateFailure(f"the interval {lo:.4f} to {hi:.4f} does not include zero")


def assert_excludes_zero(result: dict) -> None:
    lo, hi = result["ci95"]
    if lo <= 0 <= hi:
        raise GateFailure(f"the interval {lo:.4f} to {hi:.4f} includes zero")


def _attempt(check, *args) -> str | None:
    try:
        check(*args)
    except GateFailure as error:
        return str(error)
    return None


def made_up_gates(
    table: pd.DataFrame, *, n_players=MADE_UP_PLAYERS, n_boot=N_BOOT, seed=SEED
) -> dict:
    """G30c and its negative control, on made-up player-seasons through the freeze code."""
    seasons = made_up_seasons(n_players, seed)
    frozen, stayers, facts = freeze_frames(seasons, table)
    one = frozen.assign(rate_to=planted_outcomes(frozen, 1.0, seed))
    zero = frozen.assign(rate_to=planted_outcomes(frozen, 0.0, seed))
    planted_one = primary_result(context(one, stayers, table), n_boot, seed)
    planted_zero = primary_result(context(zero, stayers, table), n_boot, seed)
    shuffled = primary_result(
        context(shuffle_leagues(one, table, seed), stayers, table), n_boot, seed
    )
    failures = [
        message
        for message in (
            _attempt(assert_planted_slope, planted_one),
            _attempt(assert_includes_zero, planted_zero),
            # negative control: with shuffled league labels no slope may be found
            _attempt(assert_includes_zero, shuffled),
        )
        if message
    ]
    return {
        "analysis": "Amendment 14, gate G30c: the code recovers a planted slope (made-up data only)",
        "status": "failed" if failures else "passed",
        "failures": failures,
        "seed": int(seed),
        "bootstrap_draws": int(n_boot),
        "made_up": {
            "players": int(n_players),
            "player_seasons": int(len(seasons)),
            "league_changes": int(len(frozen)),
            "stayer_pairs": int(len(stayers)),
            "noise_sd": "player effect 1.0 and row noise 2.3 EFF/36",
            "predicted_change_sd": facts["predicted_change"]["sd"],
        },
        "planted_slope_one": {
            **planted_one,
            "rule": f"within {PLANTED_TOLERANCE} of 1.0",
        },
        "planted_slope_zero": {**planted_zero, "rule": "the interval includes zero"},
        "negative_control_shuffled_leagues": {
            **shuffled,
            "rule": "league labels shuffled across the made-up moves: the interval must include zero",
        },
    }


def no_slope_gate(
    stayers: pd.DataFrame, g_values: np.ndarray, *, n_boot=N_BOOT, seed=SEED
) -> dict:
    """G30d: a made-up predicted change given at random to stayers finds no slope.

    Negative control: the same made-up change added to the stayers' rates must
    be found. Uses stayers only; no league changer's outcome is involved.
    """
    rng = np.random.default_rng([seed, 13])
    made_up = rng.choice(np.asarray(g_values, float), size=len(stayers), replace=True)
    players = pd.Index(np.unique(stayers.player_name.to_numpy()))
    index = players.get_indexer(stayers.player_name)
    X = design(stayers, league="league")
    y = stayers.rate_next.to_numpy(float)

    def run(added):
        ctx = {
            "n_players": len(players),
            "stayer_player": index,
            "move_player": index,
            "SX": X,
            "Sy": y,
            "MX": X,
            "My": y + added,
            "g": made_up,
        }
        return primary_result(ctx, n_boot, seed)

    plain = run(0.0)
    added = run(made_up)
    failures = [
        message
        for message in (
            _attempt(assert_includes_zero, plain),
            _attempt(assert_excludes_zero, added),
        )
        if message
    ]
    return {
        "status": "failed" if failures else "passed",
        "failures": failures,
        "stayer_pairs": int(len(stayers)),
        "made_up_change_on_stayers": {**plain, "rule": "the interval includes zero"},
        "negative_control_change_added_to_rates": {
            **added,
            "rule": "the interval must exclude zero",
        },
    }


def gates(root: Path, out: Path) -> dict:
    root = Path(root)
    check_pin(root / TABLE, TABLE_SHA)
    record = made_up_gates(league_table(root / TABLE))
    record["league_table_sha256"] = TABLE_SHA
    out = Path(out)
    out.mkdir(parents=True, exist_ok=False)
    write_json(out / GATES_NAME, record)
    if record["status"] != "passed":
        raise GateFailure(f"G30c failed: {record['failures']}")
    return record


# ---------------------------------------------------------------------------
# Score: the only code path that joins a league changer's destination rate.


def join_outcomes(frozen: pd.DataFrame, seasons: pd.DataFrame) -> pd.DataFrame:
    """Attach each league changer's rate in league B in season t+1 (column ``rate_to``)."""
    here = seasons[["player_name", "season", "league", "x"]]
    start = frozen.merge(
        here.rename(
            columns={"season": "season_from", "league": "league_now", "x": "x_now"}
        ),
        on=["player_name", "season_from"],
        how="left",
        validate="1:1",
    )
    same = start.league_now.eq(start.league_from) & (
        (start.x_now - start.x).abs() <= 1e-9
    )
    if not same.all():
        raise GateFailure(
            "a frozen starting season is not reproduced from the box scores"
        )
    out = frozen.merge(
        here.rename(
            columns={"season": "season_to", "league": "league_found", "x": "rate_to"}
        ),
        on=["player_name", "season_to"],
        how="left",
        validate="1:1",
    )
    if out.rate_to.isna().any() or not out.league_found.eq(out.league_to).all():
        raise GateFailure("a league change has no rate in its destination league")
    return out.drop(columns="league_found")


def slope_rows(summary: dict) -> pd.DataFrame:
    rows = [
        {
            "result": "primary",
            "label": "all league changes",
            "league_changes": summary["primary"]["league_changes"],
            "slope": summary["primary"]["estimate"],
            "ci95_low": summary["primary"]["ci95"][0],
            "ci95_high": summary["primary"]["ci95"][1],
        }
    ]
    for league, item in summary["S_b"].items():
        rows.append(
            {
                "result": "S-b",
                "label": f"without {league}",
                "league_changes": item["league_changes"],
                "slope": item["estimate"],
                "ci95_low": item["ci95"][0],
                "ci95_high": item["ci95"][1],
            }
        )
    for label, key in (
        ("moves to a higher equivalent (g > 0)", "to_higher_equivalent"),
        ("moves to a lower equivalent (g < 0)", "to_lower_equivalent"),
    ):
        item = summary["S_c"][key]
        rows.append(
            {
                "result": "S-c",
                "label": label,
                "league_changes": item["league_changes"],
                "slope": item["slope"]["estimate"],
                "ci95_low": item["slope"]["ci95"][0],
                "ci95_high": item["slope"]["ci95"][1],
            }
        )
    rows.append(
        {
            "result": "S-d",
            "label": "the ten table values redrawn as well (approximation)",
            "league_changes": summary["primary"]["league_changes"],
            "slope": summary["primary"]["estimate"],
            "ci95_low": summary["S_d"]["ci95"][0],
            "ci95_high": summary["S_d"]["ci95"][1],
        }
    )
    for k, item in summary["S_e"].items():
        rows.append(
            {
                "result": f"S-e ({k})",
                "label": item["label"],
                "league_changes": item["league_changes"],
                "slope": item["estimate"],
                "ci95_low": item["ci95"][0],
                "ci95_high": item["ci95"][1],
            }
        )
    return pd.DataFrame(rows)


def scale_rows(e31b: dict) -> pd.DataFrame:
    """E31b: each scale's error and its coefficient in every scored season."""
    rows = []
    for name, block in e31b["scales"].items():
        base = {
            "scale": name,
            "mae": block["mae"]["estimate"],
            "mae_ci95_low": block["mae"]["ci95"][0],
            "mae_ci95_high": block["mae"]["ci95"][1],
        }
        for season, item in block["coefficient_by_scored_season"].items():
            rows.append(
                {
                    **base,
                    "scored_arrival_season": int(season),
                    "coefficient_fitted_on_earlier_arrivals": item["estimate"],
                    "coefficient_ci95_low": item["ci95"][0],
                    "coefficient_ci95_high": item["ci95"][1],
                }
            )
    return pd.DataFrame(rows)


#: The two files the paper renderer reads. Every value in them is copied from
#: the full record; they hold nothing of their own.
PAPER_SUMMARY_NAME = "summary.json"
PAPER_PAIRS_NAME = "s_f_league_pairs.csv"
CASE_CODES = {
    "Clear": "clear",
    "Positive, with a named limit": "positive_named_limit",
    "Positive, not separable from chance": "positive_not_separable",
    "Null": "null",
    "Against": "against",
}


def paper_summary(result: dict, source_sha256: str) -> dict:
    """The leaves of the scored record that the paper's first page is built from."""
    primary, case = result["primary"], result["case"]
    return {
        "analysis": "Amendment 14, E30: the leaves the paper renderer reads, copied from e30_summary.json",
        "source": "e30_summary.json",
        "source_sha256": source_sha256,
        "case": CASE_CODES[case["case"]],
        "case_name": case["case"],
        "slope": primary["estimate"],
        "ci_low": primary["ci95"][0],
        "ci_high": primary["ci95"][1],
        "perm_p": primary["permutation"]["p"],
        "n_players": result["n_players"],
        "n_moves": result["n_league_changes"],
        "limit_league": case["leagues_whose_interval_includes_zero"]
        + case["leagues_whose_interval_lies_below_zero"],
        "limit_league_includes_zero": case["leagues_whose_interval_includes_zero"],
        "limit_league_below_zero": case["leagues_whose_interval_lies_below_zero"],
        "limits": case["limits"],
        "size_reading": case["size_reading"],
        "sentence": case["sentence"],
        "to_amir_before_writing": case["to_amir_before_writing"],
        "frozen_sha256": result["frozen_sha256"],
    }


def score(
    root: Path,
    frozen_path: Path,
    expected_sha: str,
    stayers_path: Path,
    freeze_path: Path,
    out: Path,
    *,
    n_boot: int = N_BOOT,
    n_perm: int = N_PERM,
    made_up_players: int = MADE_UP_PLAYERS,
) -> dict:
    """The single scoring run. The keyword arguments exist for tests on made-up data only."""
    root = Path(root)
    # G30e: the prediction file whose sha256 was pushed, and nothing else
    check_pin(frozen_path, expected_sha)
    record = json.loads(Path(freeze_path).read_text())
    if record["files"]["frozen"]["sha256"] != expected_sha or record["outcome_joined"]:
        raise GateFailure("the freeze record does not describe this frozen file")
    check_pin(stayers_path, record["files"]["stayers"]["sha256"])
    g30e = {
        "status": "passed",
        "sha256": expected_sha,
        "negative_control_changed_byte": changed_byte_control(
            frozen_path, expected_sha
        ),
    }
    # the published table of Amendment 15: no file, no scoring run
    published = published_scores(root / PUBLISHED)
    pins = {
        "amendment_14": (AMENDMENT, AMENDMENT_SHA),
        "amendment_15": (AMENDMENT_15, AMENDMENT_15_SHA),
        "amendment_17": (AMENDMENT_17, AMENDMENT_17_SHA),
        "league_table": (TABLE, TABLE_SHA),
        "yearly_refits": (REFITS, REFITS_SHA),
        "published_table": (PUBLISHED, PUBLISHED_SHA),
    }
    g30a = pin_gate(root, pins)
    # G17a: the freeze this run scores must itself name Amendment 17
    if record.get("amendment_17", {}).get("sha256") != AMENDMENT_17_SHA:
        raise GateFailure("the freeze record does not name Amendment 17 by its sha256")
    hashes = raw_hashes(root)
    if hashes != record["inputs"]["raw_files"]:
        raise GateFailure(
            "the box-score files are not the files hashed in the freeze run"
        )
    g30a["box_score_files_equal_the_freeze_run"] = len(hashes)
    table = league_table(root / TABLE)
    frozen = pd.read_parquet(frozen_path)
    stayers = pd.read_parquet(stayers_path)
    if (
        tuple(frozen.columns) != FROZEN_COLUMNS
        or len(frozen) != EXPECTED["league_changes"]
    ):
        raise GateFailure("the frozen file is not the registered population")
    if len(stayers) != EXPECTED["stayer_pairs"]:
        raise GateFailure("the stayer file is not the registered population")
    refit = fit_stayers(stayers)
    if (
        np.abs(
            design(frozen) @ refit["beta"] - frozen.stayer_forecast.to_numpy(float)
        ).max()
        > 1e-9
    ):
        raise GateFailure(
            "the frozen stayer forecast is not reproduced from the stayer file"
        )
    # G30c and G30d run before any outcome is joined; a failure stops the run here
    g30c = made_up_gates(table, n_players=made_up_players, n_boot=n_boot)
    g30d = no_slope_gate(stayers, frozen.g.to_numpy(float), n_boot=n_boot)
    for name, gate in (("G30c", g30c), ("G30d", g30d)):
        if gate["status"] != "passed":
            raise GateFailure(
                f"{name} failed before any outcome was joined: {gate['failures']}"
            )

    agg, corpus_facts = load_aggregates(root)
    scored = join_outcomes(frozen, player_seasons(agg))
    summary = analyse(scored, stayers, table, published, n_boot=n_boot, n_perm=n_perm)
    scored["unexplained_change"] = scored.rate_to - scored.stayer_forecast
    pairs = pd.DataFrame(summary.pop("S_f"))
    result = {
        "analysis": "Amendment 14, E30: the league table tested on players who changed domestic league; and E31b of Amendment 15",
        "registered": True,
        "amendment": {"path": AMENDMENT.as_posix(), "sha256": AMENDMENT_SHA},
        "amendment_15": {"path": AMENDMENT_15.as_posix(), "sha256": AMENDMENT_15_SHA},
        "amendment_17": {"path": AMENDMENT_17.as_posix(), "sha256": AMENDMENT_17_SHA},
        "functions": FUNCTIONS,
        "frozen_sha256": expected_sha,
        "stayers_sha256": record["files"]["stayers"]["sha256"],
        "freeze_record_sha256": sha256_file(freeze_path),
        "corpus": corpus_facts,
        "stayer_model": {k: refit[k] for k in ("coefficients", "n", "residual_sd")},
        "gates": {
            "G30a": g30a,
            "G30b": record["gates"]["G30b"],
            "G30c": g30c,
            "G30d": g30d,
            "G30e": g30e,
        },
        **summary,
        "S_f_league_pairs": int(len(pairs)),
        "S_f_caption": "The 45 points come from ten numbers and are not 45 independent tests.",
        "sentences": [summary["case"]["sentence"], summary["E31b"]["reading"]],
    }
    out = Path(out)
    out.mkdir(parents=True, exist_ok=False)
    slope_rows(summary).to_csv(out / "e30_slopes.csv", index=False)
    pairs.to_csv(out / "e30_league_pairs.csv", index=False)
    pairs.to_csv(out / PAPER_PAIRS_NAME, index=False)
    scale_rows(summary["E31b"]).to_csv(out / "e31b_scales.csv", index=False)
    scored.to_parquet(out / "e30_scored_league_changes.parquet", index=False)
    write_json(out / "e30_summary.json", result)
    write_json(
        out / PAPER_SUMMARY_NAME,
        paper_summary(result, sha256_file(out / "e30_summary.json")),
    )
    return result


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    commands = parser.add_subparsers(dest="command", required=True)
    made_up = commands.add_parser("gates", help="G30c on made-up data only")
    made_up.add_argument("--out", type=Path, required=True)
    frozen = commands.add_parser(
        "freeze", help="write the frozen predictions; joins no outcome"
    )
    frozen.add_argument(
        "--gates",
        type=Path,
        required=True,
        help="the committed record of the gates subcommand",
    )
    frozen.add_argument("--out", type=Path, required=True)
    scoring = commands.add_parser("score", help="the single scoring run")
    scoring.add_argument("--frozen", type=Path, required=True)
    scoring.add_argument("--expected-sha256", required=True)
    scoring.add_argument("--stayers", type=Path, required=True)
    scoring.add_argument("--freeze-record", type=Path, required=True)
    scoring.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    root = Path.cwd()
    if args.command == "gates":
        record = gates(root, args.out)
        print(
            f"G30c {record['status']}: planted 1.0 -> {record['planted_slope_one']['slope']:.4f}"
        )
    elif args.command == "freeze":
        record = freeze(root, args.gates, args.out)
        files = record["files"]
        print(
            f"frozen {files['frozen']['rows']} league changes, sha256 {files['frozen']['sha256']}"
        )
        print(f"stayer pairs {files['stayers']['rows']}; no outcome joined")
    else:
        result = score(
            root,
            args.frozen,
            args.expected_sha256,
            args.stayers,
            args.freeze_record,
            args.out,
        )
        for sentence in result["sentences"]:
            print(sentence)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
