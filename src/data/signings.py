"""2026-27 import signings, from a first-party EuroLeague roster diff (ATI-2828).

Gates ATI-2801 (Cut 1, 20 Sep) and ATI-2807 (Sloan abstract, 1 Oct). The list is
not scrapeable from box scores — those games have not been played.

Why this artifact has clean provenance
-------------------------------------
It comes from the EuroLeague ``/people`` endpoint, which is first-party and
publicly accessible, so it sits entirely outside the Proballers licensing
question (ATI-2793). Better still, ``PersonRecord.code`` is EuroLeague's own
person id, so the **diff itself needs no name matching** — the 7.43% false-merge
rate that the cross-league name join carries (ATI-2796) does not apply here. Names
re-enter only at the boundary where an arrival is looked up in the Proballers
corpus for his prior production, and that step is labelled as name-matched.

Four kinds of new face, and only one is an import
------------------------------------------------
A naive ``current - previous`` set difference calls all four "new", which is the
trap ATI-2828 names explicitly:

* ``import`` — never appeared in this competition in any season we hold. This is
  the population the translation factors are for.
* ``intra_league_move`` — was on a DIFFERENT club in the competition last season.
  A transfer, but not an import; his prior production is already in our EL/EC
  data and needs no translation.
* ``returning_to_club`` — was on THIS club in an earlier season, left, came back.
* ``returning_to_league`` — was in the competition before, though not last season
  and not at this club.

Getting this wrong inflates the headline count and puts players in a "translated
from league X" table who never left.
"""

from __future__ import annotations

import collections
from dataclasses import dataclass, field

#: Classification labels, ordered from "needs translation" to "does not".
IMPORT = "import"
INTRA_LEAGUE_MOVE = "intra_league_move"
RETURNING_TO_CLUB = "returning_to_club"
RETURNING_TO_LEAGUE = "returning_to_league"

ALL_KINDS = (IMPORT, INTRA_LEAGUE_MOVE, RETURNING_TO_CLUB, RETURNING_TO_LEAGUE)


@dataclass(frozen=True)
class RosterPerson:
    """One person on one club's roster in one season."""

    code: str
    name: str
    competition: str
    club_code: str
    season: int


@dataclass(frozen=True)
class Arrival:
    """A person on a club's roster who was not there the previous season."""

    person_code: str
    name: str
    competition: str
    club_code: str
    season: int
    kind: str
    #: For an intra-league move, the club he came from.
    previous_club: str | None = None
    #: Most recent earlier season we saw him in this competition, if any.
    last_seen_season: int | None = None
    #: Prior domestic league from the Proballers corpus. NAME-MATCHED, so it
    #: carries the ATI-2796 error rate. ``None`` means not found, which is not
    #: the same as "he played nowhere".
    prior_league: str | None = None

    @property
    def needs_translation(self) -> bool:
        """Only a true import needs a cross-league factor."""
        return self.kind == IMPORT

    @property
    def translation_available(self) -> bool:
        """An import whose prior league is actually in the corpus."""
        return self.needs_translation and self.prior_league is not None


@dataclass
class SigningsReport:
    """The signings inventory, with the refusals enumerated rather than dropped."""

    season: int
    previous_season: int
    clubs: int = 0
    #: The PREVIOUS season's field size. A competition can change size between
    #: the two snapshots — EuroCup ran 20 clubs in 2025-26 and 32 in 2026-27 —
    #: so `clubs` is the wrong denominator for `roster_size_previous`
    #: (ATI-2921). Defaults to `clubs` when unset so an old caller that only
    #: fills `clubs` keeps its current behaviour rather than dividing by zero.
    #: Deliberately NOT serialized into the signings artifact: that payload is
    #: the pre-registration evidence chain ATI-2917 protects, and its shape must
    #: not move before the pre-lock collection is committed.
    clubs_previous: int = 0
    roster_size_current: int = 0
    roster_size_previous: int = 0
    arrivals: list[Arrival] = field(default_factory=list)
    departures: list[RosterPerson] = field(default_factory=list)
    #: Clubs whose current roster came back empty — an upstream publishing gap,
    #: not a club that signed nobody. Kept separate because a 0 here would
    #: otherwise read as a real observation.
    clubs_with_empty_roster: list[str] = field(default_factory=list)

    #: Rosters thinner than this are a fetch failure, not a small squad.
    #: EuroLeague clubs publish 12-18 people; ``fetch_club_people``'s own
    #: docstring records a 2026-08-07 incident where throttling produced
    #: "roughly two per roster ... well-formed, plausible at a glance, and
    #: missing most of its players".
    MIN_PLAUSIBLE_MEAN_ROSTER = 8.0

    def of_kind(self, kind: str) -> list[Arrival]:
        return [a for a in self.arrivals if a.kind == kind]

    def implausible_snapshots(self) -> list[str]:
        """Which snapshot(s) are too thin to be a real roster set.

        Checks BOTH sides. A first version of this guard only inspected the
        CURRENT snapshot's empty clubs, and a run on 2026-08-13 sailed past it
        with 273 people now vs **97** then — ~4.9 per club in the previous
        season — inflating "arrivals" from ~40 to 232 because players who never
        left looked new. The diff is only as trustworthy as its THINNER side.

        **Each side is divided by its OWN field size** (ATI-2921). Using the
        current count for both is wrong by exactly the ratio the field changed
        by, and it fails in the unsafe direction: when the competition GROWS,
        the previous season's mean is understated, so a healthy snapshot reads
        as implausible and the collection refuses. EuroCup 2025-26 is the live
        case — 358 people over 20 clubs is 17.9, but against the 2026-27 field
        of 32 it reads 11.2.
        """
        bad = []
        if self.clubs:
            if self.roster_size_current / self.clubs < self.MIN_PLAUSIBLE_MEAN_ROSTER:
                bad.append(
                    f"current season {self.season}: "
                    f"{self.roster_size_current / self.clubs:.1f} people/club"
                )
        prev_clubs = self.clubs_previous or self.clubs
        if prev_clubs:
            if self.roster_size_previous / prev_clubs < self.MIN_PLAUSIBLE_MEAN_ROSTER:
                bad.append(
                    f"previous season {self.previous_season}: "
                    f"{self.roster_size_previous / prev_clubs:.1f} people/club"
                )
        return bad

    @property
    def imports(self) -> list[Arrival]:
        return self.of_kind(IMPORT)

    @property
    def imports_without_translation(self) -> list[Arrival]:
        """Imports whose prior league is NOT in the corpus.

        ATI-2828: enumerate these explicitly rather than silently dropping them.
        "We cannot translate these six players, and here they are" is a stronger
        position than a table that quietly omits them.
        """
        return [a for a in self.imports if not a.translation_available]

    def _clubs_phrase(self) -> str:
        """Name both field sizes when they differ, so the means are readable.

        A single "32 clubs" next to "194 people now vs 358 then" invites the
        reader to compute 358/32 — the exact division ATI-2921 removed.
        """
        prev = self.clubs_previous or self.clubs
        if prev == self.clubs:
            return f"{self.clubs} clubs"
        return f"{self.clubs} clubs now vs {prev} then"

    def format(self) -> str:
        counts = collections.Counter(a.kind for a in self.arrivals)
        lines = [
            f"EuroLeague {self.season}-{str(self.season + 1)[-2:]} roster diff "
            f"vs {self.previous_season}: {self._clubs_phrase()}, "
            f"{self.roster_size_current} people now vs "
            f"{self.roster_size_previous} then.",
            f"  {len(self.arrivals)} arrival(s), {len(self.departures)} departure(s)",
        ]
        for thin in self.implausible_snapshots():
            lines.append(
                f"  !! IMPLAUSIBLE ROSTER SIZE — {thin}. A EuroLeague club "
                "publishes 12-18 people; this snapshot is a fetch failure, and "
                "every count above it is wrong."
            )
        for kind in ALL_KINDS:
            lines.append(f"    {kind:22s} {counts.get(kind, 0):>4d}")
        lines.append(
            f"  of {len(self.imports)} import(s), "
            f"{len(self.imports) - len(self.imports_without_translation)} have a "
            f"prior league in the corpus"
        )
        if self.imports_without_translation:
            lines.append(
                f"  !! {len(self.imports_without_translation)} import(s) with NO "
                "translation available — listed, not dropped:"
            )
            for a in self.imports_without_translation:
                lines.append(f"       {a.name} -> {a.club_code}")
        if self.clubs_with_empty_roster:
            lines.append(
                f"  !! {len(self.clubs_with_empty_roster)} club(s) returned an "
                f"EMPTY roster (upstream gap, not zero signings): "
                f"{', '.join(sorted(self.clubs_with_empty_roster))}"
            )
        return "\n".join(lines)


def classify_arrivals(
    *,
    current: dict[str, list[RosterPerson]],
    previous: dict[str, list[RosterPerson]],
    history: dict[str, list[RosterPerson]] | None = None,
    prior_leagues: dict[str, str] | None = None,
) -> SigningsReport:
    """Diff two roster snapshots and classify every new face.

    Args:
        current: club_code -> roster for the target season.
        previous: club_code -> roster for the season before.
        history: club_code -> roster people from any EARLIER seasons (may span
            several). Without it, "returning" cannot be distinguished from
            "import" and every returning player is miscounted as a signing.
        prior_leagues: person name -> prior domestic league, from the Proballers
            corpus. NAME-MATCHED; see the module docstring.

    Returns:
        A ``SigningsReport``.
    """
    history = history or {}
    prior_leagues = prior_leagues or {}

    seasons_current = {p.season for roster in current.values() for p in roster}
    seasons_prev = {p.season for roster in previous.values() for p in roster}
    season = max(seasons_current) if seasons_current else 0
    previous_season = max(seasons_prev) if seasons_prev else season - 1

    report = SigningsReport(season=season, previous_season=previous_season)
    report.clubs = len(current)
    report.clubs_previous = len(previous)
    report.roster_size_current = sum(len(r) for r in current.values())
    report.roster_size_previous = sum(len(r) for r in previous.values())

    # Codes present anywhere in the competition last season, and their club.
    prev_club_by_code: dict[str, str] = {}
    for club, roster in previous.items():
        for person in roster:
            prev_club_by_code[person.code] = club

    # Earlier appearances: code -> (latest earlier season, clubs seen).
    earlier_seasons: dict[str, int] = {}
    earlier_clubs: dict[str, set[str]] = collections.defaultdict(set)
    for club, roster in history.items():
        for person in roster:
            if person.season >= previous_season:
                continue
            earlier_clubs[person.code].add(club)
            if person.code not in earlier_seasons:
                earlier_seasons[person.code] = person.season
            else:
                earlier_seasons[person.code] = max(
                    earlier_seasons[person.code], person.season
                )

    for club, roster in sorted(current.items()):
        if not roster:
            report.clubs_with_empty_roster.append(club)
            continue
        prev_codes = {p.code for p in previous.get(club, [])}
        for person in roster:
            if person.code in prev_codes:
                continue  # stayed
            if club in earlier_clubs.get(person.code, ()):
                kind = RETURNING_TO_CLUB
            elif person.code in prev_club_by_code:
                kind = INTRA_LEAGUE_MOVE
            elif person.code in earlier_seasons:
                kind = RETURNING_TO_LEAGUE
            else:
                kind = IMPORT
            report.arrivals.append(
                Arrival(
                    person_code=person.code,
                    name=person.name,
                    competition=person.competition,
                    club_code=club,
                    season=person.season,
                    kind=kind,
                    previous_club=prev_club_by_code.get(person.code)
                    if kind == INTRA_LEAGUE_MOVE
                    else None,
                    last_seen_season=earlier_seasons.get(person.code),
                    prior_league=prior_leagues.get(person.name)
                    if kind == IMPORT
                    else None,
                )
            )

    current_codes = {p.code for roster in current.values() for p in roster}
    for club, roster in sorted(previous.items()):
        for person in roster:
            if person.code not in current_codes:
                report.departures.append(person)

    return report
