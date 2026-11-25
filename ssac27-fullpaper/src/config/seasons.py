"""Single source of truth for the basketball season cutover (ATI-2245).

EuroLeague / EuroCup / BSL seasons start in **September**, so a season is
identified by its *start year*: ``2025`` means the 2025-26 season.  We treat
**August** as the cutover — from August onward the new season has begun (the
month before tip-off, when rosters and schedules publish).

Historically the cutover was reimplemented in several places (the agent used
August, the lineup web route used July) and several modules pinned a literal
``2025`` default that silently drifts once the calendar rolls over.  Everything
season-relative should now derive from :func:`current_season` here.

ATI-3769: the cutover was still re-derived wherever a DATE became a season
(July in two web services, August elsewhere), and the "2025-26" label was
hand-formatted at ~50 sites. :func:`season_of`, :func:`in_start_year`,
:func:`calendar_year` and :func:`season_label` own both rules now, and
``tests/test_architecture/test_season_rules_single_source.py`` keeps them here.

This module lives in ``src/config`` (the lowest layer, dependency-free) so the
agent, web, data-validation, and scraper layers can all import it without
inverting the dependency graph.  ``src.agent.data_loading`` re-exports
:func:`current_season` / :func:`get_data_years` for backward compatibility.
"""

from __future__ import annotations

from datetime import date, datetime

#: Month (1-12) from which the new season is considered current.  August,
#: matching the EuroLeague/EuroCup calendar (seasons tip off in September).
SEASON_CUTOVER_MONTH: int = 8

#: Earliest season the product loads / reasons about (2016 = 2016-17 season).
#: This is an intentional *floor*, not drift — it never moves with the calendar.
DATA_START_SEASON: int = 2016


def in_start_year(month: int) -> bool:
    """Does *month* (1-12) fall in a season's START calendar year?

    August-December do (2025-26 opens in August 2025); January-July belong to
    the next calendar year.
    """
    return month >= SEASON_CUTOVER_MONTH


def season_of(day: date) -> int:
    """The season start-year a calendar *day* belongs to (a ``datetime`` too).

    ``2026-07-31`` -> ``2025`` (2025-26), ``2026-08-01`` -> ``2026``.
    """
    return day.year if in_start_year(day.month) else day.year - 1


def calendar_year(season: int, month: int) -> int:
    """The calendar year *month* falls in during the season starting *season*.

    The inverse of :func:`season_of`: for 2025-26, August-December are 2025
    and January-July are 2026.
    """
    return season if in_start_year(month) else season + 1


def season_label(season: object) -> str:
    """Render a season as its display form (``2025`` -> ``"2025-26"``).

    Accepts a start-year int (``2025``), a start-year string (``"2025"``), or
    an already-formatted ``"YYYY-YY"`` string (passed through unchanged).
    Anything else falls back to ``str(season)``, so a span label or ``None``
    never becomes a wrong season.
    """
    if isinstance(season, str) and "-" in season:
        return season
    try:
        start = int(season)  # type: ignore[call-overload]
    except (TypeError, ValueError):
        return str(season)
    return f"{start}-{(start + 1) % 100:02d}"


def current_season() -> int:
    """Return the current season start-year (e.g. ``2025`` for 2025-26).

    Uses an **August** cutover: in August or later, the current calendar year
    is the season start; before August it is the previous year.
    """
    return season_of(datetime.now())


def get_data_years() -> list[int]:
    """Return every season year from :data:`DATA_START_SEASON` to current."""
    return list(range(DATA_START_SEASON, current_season() + 1))
