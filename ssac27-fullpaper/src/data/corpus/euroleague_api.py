"""The destination side of the translation corpus, read from the EuroLeague API.

Amendment 4 to the 2026-27 pre-registration (decided 2026-09-03, ATI-2957):
the continental side of every player-season pair — EuroLeague and EuroCup — is
read from the league's own box scores under ``data/raw/{euroleague,eurocup}/
<season>/boxscores`` rather than from the Proballers copy, which stopped
writing games in the first week of January 2026 and holds 207 of 402 EuroLeague
games for 2025-26 (ATI-2956). The domestic side stays Proballers.

This module was lifted from ``scripts/compare_continental_sources.py``, the
cross-source check that licensed the switch (``continental-source-check-
2026-09-03.md``: raw factors within one bootstrap SE on 18 of 19 cells). The
script now imports from here so there is one definition of the mapping.

Two facts the mapping rests on, both measured 2026-09-03 on the full corpus:

* Proballers' ``pir`` column is **EFF** (PTS + REB + AST + STL + BLK − missed FG
  − missed FT − TOV) on 100% of 98,208 continental rows. It is *not* PIR. The
  API's ``Valuation`` is full PIR (EFF + fouls received − fouls committed −
  blocks against) on 100% of rows. The like-for-like destination metric is
  therefore EFF computed from components; ``Valuation`` is never used.
* Proballers' ``fg_made`` / ``fg_attempted`` are **two-point** figures
  (``points == 2*fg_made + 3*fg3_made + ft_made`` on every row), so the API's
  ``FieldGoalsMade2`` maps onto them and the threes travel separately.

Name key
--------
Proballers writes ``Alberto Abalde``; the API writes ``ABALDE, ALBERTO``.
:func:`pairing_key` puts both through one normaliser — diacritics stripped,
generational suffix dropped, ``LAST, FIRST`` reordered — because the estimator
pairs on ``player_name + season`` and a key that differs by source pairs
nothing. Measured on the Proballers-only corpus, applying the normaliser to
both sides moves every factor by ≤ 0.0001, so it is inert where the source does
not change.
"""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Iterable
from pathlib import Path

import pandas as pd

#: Seasons the API holds box scores for. There is no 2015-16, so pairs whose
#: destination season is 2015 drop when this side is used — the count is
#: printed by the loader that consumes this.
API_SEASONS: tuple[int, ...] = tuple(range(2016, 2026))  # season-literal-ok

#: The two destination competitions, in the directory names used under
#: ``data/raw/``. Mirrors ``scripts.build_league_factors.CONTINENTAL``.
CONTINENTAL: tuple[str, ...] = ("euroleague", "eurocup")

_SUFFIX = re.compile(r"\b(JR\.?|SR\.?|II|III|IV|V)$", re.I)
_MINUTES_RE = r"^\d+:\d+$"


# ------------------------------------------------------------------ names --
def _ascii_upper(s: str) -> str:
    return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().upper()


def norm_key(first_last: str) -> str:
    """'Alberto Abalde' / 'Robert Baker II' -> 'ALBERTO ABALDE' / 'ROBERT BAKER'.

    Diacritics stripped, suffix dropped, punctuation collapsed. Expects the name
    in ``FIRST LAST`` order; use :func:`pairing_key` when the order is unknown.
    """
    s = _ascii_upper(first_last)
    s = re.sub(r"[^\w\s-]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    s = _SUFFIX.sub("", s).strip()
    return s


def api_name_to_first_last(last_first: str) -> str:
    """'BAKER II, ROBERT' -> 'ROBERT BAKER II'.

    Reorders only; :func:`norm_key` does the suffix and diacritic work. A name
    without a comma is returned stripped, so Proballers names pass through.
    """
    if "," not in last_first:
        return last_first.strip()
    last, first = last_first.split(",", 1)
    return f"{first.strip()} {last.strip()}"


def pairing_key(name: object) -> str | None:
    """The one key both corpus sides and the signings roster share.

    ``None`` for an empty or non-string name so a caller can drop the row and
    count it, rather than pairing a blank against a blank.
    """
    if name is None or (isinstance(name, float) and name != name):
        return None
    key = norm_key(api_name_to_first_last(str(name)))
    return key or None


# ------------------------------------------------------------------- load --
def parse_minutes(s: pd.Series) -> pd.Series:
    """'MM:SS' -> float minutes. Non-matching values become NaN."""
    mm = s.str.extract(r"^(\d+):(\d+)$")
    return mm[0].astype(float) + mm[1].astype(float) / 60.0


def eff_from_components(raw: pd.DataFrame) -> pd.Series:
    """EFF = PTS + REB + AST + STL + BLK − missed FG − missed FT − TOV.

    The formula the Proballers ``pir`` column actually carries. ``Valuation``
    (official PIR) is deliberately not an option here: putting PIR on the
    destination side against EFF on the domestic side shifts every factor by
    about −0.04, which the cross-source check's negative control measured.
    """
    fgm = raw.FieldGoalsMade2 + raw.FieldGoalsMade3
    fga = raw.FieldGoalsAttempted2 + raw.FieldGoalsAttempted3
    return (
        raw.Points
        + raw.TotalRebounds
        + raw.Assistances
        + raw.Steals
        + raw.BlocksFavour
        - (fga - fgm)
        - (raw.FreeThrowsAttempted - raw.FreeThrowsMade)
        - raw.Turnovers
    )


def drop_non_player_rows(raw: pd.DataFrame) -> pd.DataFrame:
    """Drop per-team ``Total`` rows, DNP rows and unparseable minutes.

    Measured 2026-09-03 on 2016–2025: 134,241 raw rows → 103,767 player-games.
    The API records a non-appearance as ``Minutes == "DNP"``, never as ``0:00``
    (zero ``^0+:0+$`` rows in the corpus), so the minutes regex is the whole
    filter; ``IsPlaying`` is *not* a played-flag (it is 0 on 54,906 rows that
    carry minutes and points) and must not be used as one.
    """
    keep = (raw.Player != "Total") & (raw.Minutes != "DNP")
    keep &= raw.Minutes.astype(str).str.match(_MINUTES_RE, na=False)
    return raw[keep]


def to_proballers_schema(raw: pd.DataFrame) -> pd.DataFrame:
    """Map filtered API box-score rows onto the Proballers player_stats columns.

    ``raw`` must carry a ``league`` column (the competition directory name) and
    have been through :func:`drop_non_player_rows`. Names are left in the API's
    ``LAST, FIRST`` form here; the corpus loader applies :func:`pairing_key` to
    both sides at once, so the two sides cannot be normalised differently.
    """
    out = pd.DataFrame(
        {
            "game_id": "api-"
            + raw.league
            + "-"
            + raw.Season.astype(str)
            + "-"
            + raw.Gamecode.astype(str),
            "date": None,
            "player_name": raw.Player,
            "team": raw.Team,
            "minutes": parse_minutes(raw.Minutes.astype(str)),
            "points": raw.Points,
            "rebounds": raw.TotalRebounds,
            "assists": raw.Assistances,
            "steals": raw.Steals,
            "blocks": raw.BlocksFavour,
            "turnovers": raw.Turnovers,
            "fouls": raw.FoulsCommited,
            "fg_made": raw.FieldGoalsMade2,
            "fg_attempted": raw.FieldGoalsAttempted2,
            "fg3_made": raw.FieldGoalsMade3,
            "fg3_attempted": raw.FieldGoalsAttempted3,
            "ft_made": raw.FreeThrowsMade,
            "ft_attempted": raw.FreeThrowsAttempted,
            "offensive_rebounds": raw.OffensiveRebounds,
            "defensive_rebounds": raw.DefensiveRebounds,
            "plus_minus": raw.Plusminus,
            "pir": eff_from_components(raw).astype(float),
            "league": raw.league,
            "season": raw.Season.astype(int),
        }
    )
    return out.reset_index(drop=True)


def load_api_continental(
    root: Path,
    *,
    seasons: Iterable[int] = API_SEASONS,
    competitions: Iterable[str] = CONTINENTAL,
) -> tuple[pd.DataFrame, dict]:
    """Read every available API box-score season into the Proballers schema.

    Returns ``(frame, report)``. The report carries what was dropped and the
    points-reconciliation count, because a loader that silently drops rows is
    indistinguishable from one that never saw them. Raises if no box scores
    are found — an empty destination side would let the estimator run on
    nothing and report zero pairs as if that were a finding.
    """
    frames = []
    seasons_found: dict[str, list[int]] = {}
    for comp in competitions:
        for season in seasons:
            p = Path(root) / "data" / "raw" / comp / str(season) / "boxscores"
            if not p.exists():
                continue
            df = pd.read_parquet(p)
            df["league"] = comp
            frames.append(df)
            seasons_found.setdefault(comp, []).append(int(season))
    if not frames:
        raise FileNotFoundError(
            f"no EuroLeague API box scores under {root}/data/raw/"
            f"{{{','.join(competitions)}}}/<season>/boxscores"
        )
    raw = pd.concat(frames, ignore_index=True)
    n_raw = len(raw)
    raw = drop_non_player_rows(raw)
    # Reconciliation invariant (METHOD.md §4): points == 2*fg2 + 3*fg3 + ft.
    pts = 2 * raw.FieldGoalsMade2 + 3 * raw.FieldGoalsMade3 + raw.FreeThrowsMade
    bad = int((pts.to_numpy() != raw.Points.to_numpy()).sum())
    if len(raw) and bad / len(raw) >= 0.001:
        raise ValueError(
            f"API points do not reconcile with made shots on {bad} of {len(raw)} rows"
        )
    out = to_proballers_schema(raw)
    report = {
        "rows_raw": n_raw,
        "rows_kept": int(len(out)),
        "rows_dropped_total_dnp_unparseable": n_raw - int(len(out)),
        "points_reconciliation_mismatches": bad,
        "seasons": {k: sorted(v) for k, v in seasons_found.items()},
        "metric": "eff_from_components",
    }
    return out, report
