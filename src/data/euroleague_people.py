"""EuroLeague ``/people`` client — roster people with their FULL bio record.

ATI-2766. The repo already called this endpoint, in
``src/web/services/analytics_photos.py``, and kept exactly one field:

    person = item.get("person", {})
    name = person.get("name", "")
    headshot = item.get("images", {}).get("headshot", "")

Everything else was discarded. What was being discarded is precisely what
ATI-2766 went looking for, and had planned to scrape from Proballers:

    {"code": "014169", "name": "LEN, ALEX", "passportName": "OLEKSII",
     "country": {"code": "UKR", "name": "Ukraine"},
     "birthCountry": {"code": "UKR", "name": "Ukraine"},
     "birthDate": "1993-06-16T00:00:00", "height": 213, "weight": 120}

Two things make this a better source than the ticket's assumed one:

* ``country`` and ``birthCountry`` are **separate fields**. The ticket asks to
  "capture the raw nationality field and derive eligibility separately", because
  some leagues count EU/non-EU or locally-trained status rather than passport.
  Passport-vs-origin arrives already split.
* ``person.code`` is a stable id, so bios join to the registry by **ID** rather
  than by normalised name — the ticket's stated main risk.

What it is NOT: complete. This is EuroLeague + EuroCup only, which is 43.6% of
the 7,334-player corpus. The 4,136 domestic-league-only players need a different
source, and Proballers -- the ticket's assumption -- returned a Cloudflare
interstitial when checked on 2026-08-06. That gap is tracked on the ticket; it is
not something this module can close.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass

import requests

logger = logging.getLogger(__name__)

_API_ROOT = "https://api-live.euroleague.net/v2/competitions"

#: ``item["type"]`` for a player (as opposed to coaching/technical staff).
PLAYER_TYPE = "J"

_TIMEOUT_SECONDS = 10

#: Retries for the club-list call. It throttles under a multi-season sweep, and
#: an un-retried failure is worse than slow: ``fetch_club_codes`` fails soft, so
#: a throttled season silently contributes ZERO players to the artifact rather
#: than raising. Observed live on 2026-08-07 -- a ten-season sweep produced
#: FEWER players than a single season, all of it well-formed.
#:
#: Backoff is EXPONENTIAL, not linear. The 4-attempt linear ladder (2/4/6 s,
#: 12 s total) was measured insufficient on 2026-08-07: a full sweep still lost
#: 3 of 11 seasons entirely. Probing those same seasons ONE AT A TIME, well
#: spaced, returned 36-52 clubs every time -- so the endpoint is rate limiting,
#: not missing data, and the club list is being punished for the ~40 roster
#: requests that precede it. What that needs is a wait long enough to leave the
#: limiter's window, which a linear ladder reaches too slowly.
_CLUB_LIST_ATTEMPTS = 6
_CLUB_LIST_BACKOFF_SECONDS = 2.0

#: The ROSTER call retries on a deliberately SHORTER ladder than the club list,
#: and the asymmetry is the point. Losing a club list loses a whole season, so
#: it is worth waiting ~62 s for; losing one roster loses one squad, and with
#: `--resume` a later run picks it up for free. Running both at 6 attempts made
#: a full sweep take over half an hour, most of it sleeping on clubs that were
#: going to fail anyway. Fail fast here, resume later.
_ROSTER_ATTEMPTS = 3


@dataclass(frozen=True)
class PersonRecord:
    """One roster person, with every bio field the endpoint carries.

    ``code`` is the EuroLeague person id and the join key. Everything else is
    optional -- the endpoint omits fields for some people, and a missing value
    must stay missing rather than be inferred (ATI-2766 is explicit that a
    silently-wrong age is worse than no age).
    """

    code: str
    name: str
    competition: str
    club_code: str
    season: int
    #: Passport / representative nationality.
    country_code: str | None = None
    country_name: str | None = None
    #: Country of BIRTH — deliberately separate; the two differ often enough
    #: that collapsing them would destroy the distinction quota rules need.
    birth_country_code: str | None = None
    birth_country_name: str | None = None
    birth_date: str | None = None  # ISO date (the API's timestamp, truncated)
    height_cm: int | None = None
    weight_kg: int | None = None
    position: str | None = None
    headshot_url: str | None = None


def _clean_str(value: object) -> str | None:
    """Return a non-empty stripped string, else ``None``."""
    if not isinstance(value, str):
        return None
    stripped = value.strip()
    return stripped or None


def _clean_int(value: object) -> int | None:
    """Return a positive int, else ``None``.

    The endpoint uses ``0`` for "unknown" on height/weight, which would read as
    a real measurement of zero.
    """
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    as_int = int(value)
    return as_int if as_int > 0 else None


def _birth_date(value: object) -> str | None:
    """``"1993-06-16T00:00:00"`` -> ``"1993-06-16"``; anything else -> ``None``."""
    raw = _clean_str(value)
    if raw is None:
        return None
    date_part = raw.split("T", 1)[0]
    # Cheap shape check — never coerce, never guess. A malformed value stays
    # missing rather than becoming a confidently-wrong birthdate.
    parts = date_part.split("-")
    if len(parts) != 3 or not all(p.isdigit() for p in parts):
        return None
    return date_part


def _nested_country(person: dict, key: str) -> tuple[str | None, str | None]:
    node = person.get(key)
    if not isinstance(node, dict):
        return None, None
    return _clean_str(node.get("code")), _clean_str(node.get("name"))


def parse_people_payload(
    payload: object,
    *,
    comp: str,
    club_code: str,
    season: int,
) -> list[PersonRecord]:
    """Parse a ``/people`` response into player records.

    Split out from the fetch so the shape can be tested without a network call —
    the whole reason the endpoint's contents went unnoticed for as long as they
    did is that nothing ever asserted on them.
    """
    items = payload.get("data", payload) if isinstance(payload, dict) else payload
    if not isinstance(items, list):
        return []

    records: list[PersonRecord] = []
    for item in items:
        if not isinstance(item, dict) or item.get("type") != PLAYER_TYPE:
            continue
        person = item.get("person")
        if not isinstance(person, dict):
            continue
        code = _clean_str(person.get("code"))
        name = _clean_str(person.get("name"))
        if not code or not name:
            continue

        country_code, country_name = _nested_country(person, "country")
        birth_code, birth_name = _nested_country(person, "birthCountry")
        images = item.get("images")
        headshot = (
            _clean_str(images.get("headshot")) if isinstance(images, dict) else None
        )

        records.append(
            PersonRecord(
                code=code,
                name=name,
                competition=comp,
                club_code=club_code,
                season=season,
                country_code=country_code,
                country_name=country_name,
                birth_country_code=birth_code,
                birth_country_name=birth_name,
                birth_date=_birth_date(person.get("birthDate")),
                height_cm=_clean_int(person.get("height")),
                weight_kg=_clean_int(person.get("weight")),
                position=_clean_str(item.get("positionName"))
                or _clean_str(item.get("position")),
                headshot_url=headshot,
            )
        )
    return records


def fetch_club_codes(
    season: int, comps: tuple[str, ...] = ("E", "U")
) -> list[tuple[str, str]]:
    """Return ``(competition, club_code)`` pairs for a season.

    Fails soft per competition: one competition being unavailable must not lose
    the other's clubs.
    """
    pairs: list[tuple[str, str]] = []
    for comp in comps:
        url = f"{_API_ROOT}/{comp}/seasons/{comp}{season}/clubs"
        for attempt in range(1, _CLUB_LIST_ATTEMPTS + 1):
            try:
                resp = requests.get(url, timeout=_TIMEOUT_SECONDS)
                resp.raise_for_status()
                for club in resp.json().get("data", []):
                    code = _clean_str(club.get("code"))
                    if code:
                        pairs.append((comp, code))
                break
            except Exception:  # noqa: BLE001 — network + JSON boundary
                if attempt == _CLUB_LIST_ATTEMPTS:
                    logger.warning(
                        "Failed to fetch club list for %s season %d after %d "
                        "attempts — this season will contribute NO players",
                        comp,
                        season,
                        _CLUB_LIST_ATTEMPTS,
                    )
                    break
                time.sleep(_CLUB_LIST_BACKOFF_SECONDS * (2 ** (attempt - 1)))
    return pairs


def fetch_club_people(comp: str, club_code: str, season: int) -> list[PersonRecord]:
    """Fetch one club's roster people with their full bio records.

    Retries on the same ladder as the club list, and reports a final failure at
    WARNING. Both were earned on 2026-08-07: this call previously made ONE
    attempt and logged its failure at DEBUG, so a throttled roster contributed
    zero players in complete silence. The club-list guard could not see it —
    the season's club list had succeeded — and the result was a season
    reporting 42 clubs and 83 people, roughly two per roster where twelve to
    eighteen is normal. Well-formed, plausible at a glance, and missing most of
    its players.
    """
    url = f"{_API_ROOT}/{comp}/seasons/{comp}{season}/clubs/{club_code}/people"
    for attempt in range(1, _ROSTER_ATTEMPTS + 1):
        try:
            resp = requests.get(url, timeout=_TIMEOUT_SECONDS)
            resp.raise_for_status()
            return parse_people_payload(
                resp.json(), comp=comp, club_code=club_code, season=season
            )
        except Exception:  # noqa: BLE001 — outer boundary for network + JSON errors
            if attempt == _ROSTER_ATTEMPTS:
                logger.warning(
                    "Failed to fetch people for club %s (%s %d) after %d attempts "
                    "— this club contributes NO players; re-run --resume",
                    club_code,
                    comp,
                    season,
                    _ROSTER_ATTEMPTS,
                )
                return []
            time.sleep(_CLUB_LIST_BACKOFF_SECONDS * (2 ** (attempt - 1)))
    return []
