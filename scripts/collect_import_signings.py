#!/usr/bin/env python
"""Collect the 2026-27 EuroLeague and EuroCup import signings (ATI-2828, ATI-2917).

Gates ATI-2801 (Cut 1, 20 Sep) and ATI-2807 (Sloan abstract, 1 Oct). Signings
announce continuously through August and the season tips 24 September, so this is
built incrementally and re-run weekly — far cheaper than reconstructing it under
deadline.

**The both-competitions mode is why ATI-2917 exists.** A merged EuroLeague +
EuroCup artifact of exactly this shape sat in `data/processed/signings/` and
**no committed script could produce it** — the collector took one
`--competition` per run, wrote a different filename, and emitted a different key
set. Every 2026-27 population figure in the pre-registration descends from that
file. The artifact looked like this script's output until you diffed the keys,
which is how it survived review. `--competition both` is now the default and
writes its own filename, so the two shapes can never overwrite each other.

Artifacts are stamped with their COLLECTION DATE, not just the season. Two
both-competitions runs a week apart are two different populations — the count
grew 69 -> 94 -> 110 across three of them — and a season-stamped name silently
made each one overwrite the last. Omitting `--out` writes nothing at all, so a
run meant to produce the artifact must pass it.

Season labels: ``--season 2026`` means the **2026-27** season. That is the season
the Aug-1 cutover rolls to and it has not been played — which is exactly what we
want here, unlike the phantom-season trap in ATI-2836 where a not-yet-played label
was used to request *box scores*. Roster endpoints legitimately publish forward.

Two reasons a roster comes back empty, and they get separate budgets. Upstream
genuinely has not published some squads (2026-08-21: BCR, BOU, BUD, LJU, MCO,
TTK in EuroCup) — name those in ``--known-empty-clubs`` and they are recorded as
MISSING, never as clubs that signed nobody. Everything else counts against
``--max-empty-clubs``, because the endpoint answers **429 under a burst** and a
throttled sweep otherwise prints a diff that looks complete. Accommodating the
genuine gaps by raising the threshold would blind the guard to the throttled
ones.

Usage::

    uv run python scripts/collect_import_signings.py --out data/processed/signings \
        --known-empty-clubs BCR,BOU,BUD,LJU,MCO,TTK \
        --provenance "what changed since the previous collection"
    # -> data/processed/signings/import_signings_2026_both_competitions_<date>.json
    uv run python scripts/collect_import_signings.py --competition E
    uv run python scripts/collect_import_signings.py --delay 1.0   # after a 429
"""

from __future__ import annotations

import argparse
import datetime
import json
import pathlib
import sys
import time

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.data.euroleague_people import (  # noqa: E402
    fetch_club_codes,
    fetch_club_people,
)
from src.data.signings import (  # noqa: E402
    RosterPerson,
    SigningsReport,
    classify_arrivals,
)

#: Leagues added by the ATI-2895 scrape. Counted separately because before that
#: scrape their seasons read as "no domestic league", which both mis-attributed
#: imports and made others unscorable.
ATI2895_LEAGUES = ("italy-lba", "germany-bbl", "greece-a1")

#: API competition code -> the label used in the artifact.
COMPETITION_LABELS = {"E": "euroleague", "U": "eurocup"}

#: Scoring-method labels (Amendment 2 Change 2).
COMBINED_ARM = "combined"
PER_LEAGUE_ONLY = "per_league_only"

#: A source season PLUS prior history. One season carries no RTM term.
MIN_SEASONS_FOR_COMBINED_ARM = 2


def _snapshot(
    season: int, comp: str = "E", delay: float = 0.4
) -> dict[str, list[RosterPerson]]:
    """Fetch every club's roster for one season.

    ``delay`` paces the per-club calls. The underlying helpers retry with
    backoff but do not pace BETWEEN clubs, and a full history sweep is ~20 clubs
    x N seasons in a burst. Measured 2026-08-13: an unpaced sweep got the club
    list throttled to the point of failing all 6 attempts, on an endpoint that had
    answered fine seconds earlier. The collector refused rather than reporting
    zero signings (which is the guard working), but the run still produced
    nothing — so pace it.
    """
    pairs = [(c, code) for c, code in fetch_club_codes(season, comps=(comp,))]
    out: dict[str, list[RosterPerson]] = {}
    for competition, club_code in pairs:
        if delay:
            time.sleep(delay)
        people = fetch_club_people(competition, club_code, season)
        out[club_code] = [
            RosterPerson(
                code=p.code,
                name=p.name,
                competition=competition,
                club_code=club_code,
                season=season,
            )
            for p in people
        ]
    return out


def artifact_path(
    out_dir: pathlib.Path,
    season: int,
    competitions: tuple[str, ...],
    *,
    collected_at: str,
) -> pathlib.Path:
    """Where a run's artifact goes.

    A multi-competition run gets its own name. The two payloads carry different
    schemas, so letting one overwrite the other destroys the lineage the
    pre-registration's dated-count rule depends on.

    The COLLECTION DATE is in the filename for that same reason one step down
    (ATI-2917). Season-stamping alone sent every both-competitions run to a
    single path, so the pre-lock collection would have overwritten the
    2026-08-21 artifact -- the only committed evidence for the middle of the
    published 69 -> 94 -> 110 chain, and a file the amendment's dated-count
    rule requires to stay readable. That the overwrite is now recoverable from
    git is not enough: the lineage has to be legible without archaeology.

    ``collected_at`` is keyword-only and REQUIRED. A default would restore the
    single-path behaviour by omission, which is how this was missed the first
    time.
    """
    stem = f"import_signings_{season}"
    if len(competitions) > 1:
        stem += "_both_competitions"
    return out_dir / f"{stem}_{collected_at}.json"


#: A history sweep thinner than this per club is a throttled fetch, not a set
#: of clubs that fielded nobody. Deliberately loose: history spans seasons a
#: club may not have played in the competition, so the bar is coverage, not
#: roster size.
MIN_HISTORY_PEOPLE_PER_CLUB = 3.0


def implausible_history(
    history: dict, clubs: list[str], min_per_club: float = MIN_HISTORY_PEOPLE_PER_CLUB
) -> str | None:
    """Is the history sweep too thin to have done its job?

    `SigningsReport.implausible_snapshots` guards the current and previous
    rosters. History is a THIRD fetch and it is the one that stops a returning
    player being miscounted as an import (ATI-2828). A throttled history sweep
    therefore inflates the import count while both guarded snapshots look
    healthy -- measured 2026-08-25, when the endpoint 429'd partway through the
    sweep and every earlier season came back empty.

    Returns a description of the problem, or None when the sweep is plausible.
    """
    if not clubs:
        return None
    people = sum(len(v) for v in history.values())
    per_club = people / len(clubs)
    if per_club >= min_per_club:
        return None
    return (
        f"history sweep returned {people} people across {len(clubs)} clubs "
        f"({per_club:.1f}/club, floor {min_per_club}). Without history every "
        "returning player is miscounted as an import, which INFLATES the "
        "signings count while the current and previous snapshots look healthy"
    )


def unexpected_empty_clubs(
    report: SigningsReport, known_empty: tuple[str, ...] = ()
) -> list[str]:
    """Empty rosters that are NOT a known upstream gap.

    Both kinds are "missing, not zero", but only these mean the fetch should be
    re-run. Keeping them on separate budgets matters: raising the throttle
    threshold to accommodate six genuine gaps would also blind it to six
    THROTTLED clubs, which is how a guard gets relaxed until it means nothing.
    """
    return [c for c in report.clubs_with_empty_roster if c not in set(known_empty)]


def summarise_corpus_history(
    appearances, domestic_leagues
) -> tuple[dict[str, str], dict[str, int]]:
    """Per player: his most recent domestic league, and how many domestic seasons.

    The season count drives the combined-arm split. Continental appearances are
    excluded from BOTH: they are the destination side, and counting them would
    qualify a player for the RTM arm on the very history the prediction is
    trying to anticipate.
    """
    latest: dict[str, tuple[int, str]] = {}
    seasons: dict[str, set[int]] = {}
    for a in appearances:
        if a.league not in domestic_leagues:
            continue
        best = latest.get(a.player)
        if best is None or a.season > best[0]:
            latest[a.player] = (a.season, a.league)
        seasons.setdefault(a.player, set()).add(a.season)
    return (
        {name: league for name, (_, league) in latest.items()},
        {name: len(s) for name, s in seasons.items()},
    )


def _corpus_history(
    repo_root: pathlib.Path,
) -> tuple[dict[str, str], dict[str, int] | None]:
    """Prior domestic league per player, and his domestic-season count.

    NAME-MATCHED, so it inherits the ATI-2796 false-merge rate. When the corpus
    is absent it returns an empty map and ``None`` for the season counts -- the
    season counts are deliberately ``None`` rather than ``{}`` so the payload
    reports the combined-arm split as UNKNOWN instead of publishing a 0% that
    would read as a measurement.
    """
    from src.data.corpus import load_proballers_player_stats
    from src.data.corpus.identity import (
        DOMESTIC_LEAGUES,
        build_appearances,
    )

    frame, _ = load_proballers_player_stats(repo_root=repo_root)
    if frame.height == 0:
        print(
            "WARNING: no Proballers corpus under this checkout, so NO import can "
            "be given a prior league. The 'no translation available' list below "
            "is therefore meaningless — re-run with --repo-root pointing at a "
            "data-equipped checkout.",
            file=sys.stderr,
        )
        return {}, None

    appearances, _ = build_appearances(frame)
    return summarise_corpus_history(appearances, DOMESTIC_LEAGUES)


def build_multi_competition_payload(
    reports: dict[str, SigningsReport],
    *,
    collected_at: str,
    provenance: str,
    ati2895_leagues: tuple[str, ...] = ATI2895_LEAGUES,
    corpus_seasons: dict[str, int] | None = None,
    known_empty_clubs: tuple[str, ...] = (),
) -> dict:
    """Merge one report per competition into the artifact the publication reads.

    ``corpus_seasons`` maps player name -> qualifying corpus seasons, and drives
    the per-player scoring method Amendment 2 Change 2 requires the publication
    to label. When it is absent the method is ``None`` everywhere and both
    counts are ``None`` -- an unknown split, never a zero one, because a
    published "0% combined arm" would read as a measurement rather than a
    missing input.
    """

    def _method(arrival) -> str | None:
        if corpus_seasons is None or not arrival.translation_available:
            return None
        return (
            COMBINED_ARM
            if corpus_seasons.get(arrival.name, 0) >= MIN_SEASONS_FOR_COMBINED_ARM
            else PER_LEAGUE_ONLY
        )

    if not reports:
        raise ValueError("no reports: refusing to write an empty artifact")

    seasons = {(r.season, r.previous_season) for r in reports.values()}
    if len(seasons) != 1:
        raise ValueError(
            f"reports disagree on the season: {sorted(seasons)}. One artifact "
            "carries one season; merging two would count a population that "
            "never existed."
        )
    season, previous_season = seasons.pop()

    imports = [a for r in reports.values() for a in r.imports]
    methods = [_method(a) for a in imports]
    return {
        "season": season,
        "previous_season": previous_season,
        "collected_at": collected_at,
        "competitions": {
            name: {
                "clubs": r.clubs,
                "clubs_with_empty_roster": list(r.clubs_with_empty_roster),
                "known_upstream_gap": [
                    c for c in r.clubs_with_empty_roster if c in set(known_empty_clubs)
                ],
                "unexplained_empty_roster": unexpected_empty_clubs(
                    r, known_empty_clubs
                ),
            }
            for name, r in reports.items()
        },
        "counts": {
            "imports": len(imports),
            "scorable": sum(1 for a in imports if a.translation_available),
            "from_ati2895_leagues": sum(
                1 for a in imports if a.prior_league in ati2895_leagues
            ),
            "combined_arm": (
                None
                if corpus_seasons is None
                else sum(1 for m in methods if m == COMBINED_ARM)
            ),
            "per_league_only": (
                None
                if corpus_seasons is None
                else sum(1 for m in methods if m == PER_LEAGUE_ONLY)
            ),
        },
        "provenance": provenance,
        "arrivals": [
            {
                "person_code": a.person_code,
                "name": a.name,
                "club_code": a.club_code,
                "kind": a.kind,
                "previous_club": a.previous_club,
                "last_seen_season": a.last_seen_season,
                "prior_league": a.prior_league,
                "translation_available": a.translation_available,
                "competition": competition,
                "scoring_method": _method(a),
            }
            for competition, r in reports.items()
            for a in r.arrivals
        ],
    }


def write_payload(payload: dict, path: pathlib.Path) -> pathlib.Path:
    """Serialise to STRICT JSON, refusing rather than emitting `NaN`.

    `json.dump` writes bare `NaN`/`Infinity` by default. Those are not JSON --
    `JSON.parse` rejects them, as does `json.load` with a strict
    `parse_constant`. The committed 2026-08-21 artifact carries them, which is
    both a portability bug and the fingerprint of a pandas-shaped writer that is
    not this script.

    Serialise fully before touching the filesystem so a refusal leaves no
    half-written artifact behind for someone to quote.
    """
    text = json.dumps(payload, indent=2, ensure_ascii=False, allow_nan=False)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    return path


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--season", type=int, default=2026, help="2026 == 2026-27")
    ap.add_argument(
        "--competition",
        default="both",
        choices=("E", "U", "both"),
        help="E (EuroLeague), U (EuroCup), or both. `both` is the artifact "
        "the pre-registration reads; it writes its own filename so it can "
        "never overwrite a single-competition run.",
    )
    ap.add_argument(
        "--collected-at",
        default=None,
        help="collection date stamped into the artifact (YYYY-MM-DD). "
        "Defaults to today. The pre-registration states the population as a "
        "DATED count, so this is load-bearing, not decoration.",
    )
    ap.add_argument(
        "--provenance",
        default="",
        help="free text recorded in the artifact: what changed since the "
        "previous collection and why this one supersedes it.",
    )
    ap.add_argument(
        "--history-seasons",
        type=int,
        default=5,
        help="how many EARLIER seasons to fetch for returning-player detection. "
        "Without history every returning player is miscounted as a signing.",
    )
    ap.add_argument(
        "--delay",
        type=float,
        default=0.4,
        help="seconds between per-club calls; 0 got us throttled (2026-08-13)",
    )
    ap.add_argument(
        "--max-empty-clubs",
        type=int,
        default=2,
        help="refuse if more UNEXPLAINED empty rosters than this; a throttled "
        "sweep otherwise prints an incomplete diff that looks complete. Clubs "
        "named in --known-empty-clubs do not spend this budget.",
    )
    ap.add_argument(
        "--known-empty-clubs",
        default="",
        help="comma-separated club codes whose roster upstream genuinely has "
        "not published (2026-08-21: BCR,BOU,BUD,LJU,MCO,TTK in EuroCup). They "
        "are recorded in the artifact as MISSING, never as clubs that signed "
        "nobody, and are excluded from the --max-empty-clubs budget so that "
        "accommodating them cannot blind the throttle guard.",
    )
    ap.add_argument(
        "--allow-thin-rosters",
        action="store_true",
        help="proceed despite an implausibly thin snapshot. For inspecting a "
        "known-partial fetch only -- never for an artifact anyone will quote.",
    )
    ap.add_argument("--out", type=pathlib.Path, default=None)
    ap.add_argument("--repo-root", type=pathlib.Path, default=REPO_ROOT)
    args = ap.parse_args(argv)

    season, prev = args.season, args.season - 1
    comps = ("E", "U") if args.competition == "both" else (args.competition,)
    collected_at = args.collected_at or datetime.date.today().isoformat()
    known_empty = tuple(
        c.strip().upper() for c in args.known_empty_clubs.split(",") if c.strip()
    )

    prior, corpus_seasons = _corpus_history(args.repo_root)
    print(f"prior-league map: {len(prior):,} names from the corpus")
    if corpus_seasons is None:
        print(
            "  combined-arm split will be reported as UNKNOWN (no corpus here)",
            file=sys.stderr,
        )
    print()

    reports: dict[str, SigningsReport] = {}
    for comp in comps:
        label = COMPETITION_LABELS[comp]
        print(f"Fetching {label} rosters: {season}, {prev}, and history…")

        current = _snapshot(season, comp, args.delay)
        previous = _snapshot(prev, comp, args.delay)

        if not current:
            print(
                f"REFUSING: no clubs returned for {label} {season}. That is "
                "an upstream/API failure, not a season with no teams.",
                file=sys.stderr,
            )
            return 2

        history: dict[str, list[RosterPerson]] = {}
        for older in range(prev - args.history_seasons, prev):
            for club, roster in _snapshot(older, comp, args.delay).items():
                history.setdefault(club, []).extend(roster)

        bad_history = implausible_history(history, list(current))
        if bad_history and not args.allow_thin_rosters:
            print(
                f"\nREFUSING ({label}): {bad_history}. Wait for the cooldown and "
                "re-run with a larger --delay.",
                file=sys.stderr,
            )
            return 5

        report = classify_arrivals(
            current=current,
            previous=previous,
            history=history,
            prior_leagues=prior,
        )
        print(report.format())

        # Observed 2026-08-13: under a full-history sweep the endpoint throttles
        # and individual clubs come back empty. Each empty club is already
        # reported as an upstream gap rather than "signed nobody" -- but a run
        # where several clubs failed still exits 0 and prints a diff that LOOKS
        # complete, and an undercounted signings list is exactly the artifact
        # that would go into a published report. Refuse past a threshold.
        #
        # The refusal is per COMPETITION and aborts the whole run: a half-good
        # merged artifact is worse than none, because its headline count looks
        # like a measurement of both competitions.
        thin = report.implausible_snapshots()
        if thin and not args.allow_thin_rosters:
            print(
                f"\nREFUSING ({label}): " + "; ".join(thin) + ". A EuroLeague "
                "club publishes 12-18 people, so this is a throttled fetch, not "
                "a small squad. The diff is only as good as its THINNER side: a "
                "gutted PREVIOUS snapshot makes players who never left look like "
                "arrivals (measured 2026-08-13: 232 'arrivals' against a "
                "97-person previous season, vs ~40 real). Wait for the cooldown "
                "and re-run with a larger --delay.",
                file=sys.stderr,
            )
            return 4

        unexplained = unexpected_empty_clubs(report, known_empty)
        if len(unexplained) > args.max_empty_clubs:
            print(
                f"\nREFUSING ({label}): {len(unexplained)} of {report.clubs} "
                f"clubs returned an unexplained empty roster (limit "
                f"{args.max_empty_clubs}): {unexplained}. The endpoint is "
                "throttling -- it answers 429 under a burst -- so this diff is "
                "INCOMPLETE and would undercount arrivals. Wait for the cooldown "
                "and re-run with a larger --delay. If a club here is a genuine "
                "upstream publishing gap, name it in --known-empty-clubs: it is "
                "then recorded as MISSING rather than as a club that signed "
                "nobody, WITHOUT weakening this guard for the others.",
                file=sys.stderr,
            )
            return 3

        print(f"\n=== {label.upper()} IMPORTS (the translation population) ===")
        for a in sorted(report.imports, key=lambda x: (x.club_code, x.name)):
            league = a.prior_league or "NO TRANSLATION AVAILABLE"
            print(f"  {a.club_code:5s} {a.name:32s} <- {league}")

        reports[label] = report

    payload = build_multi_competition_payload(
        reports,
        collected_at=collected_at,
        provenance=args.provenance,
        corpus_seasons=corpus_seasons,
        known_empty_clubs=known_empty,
    )
    counts = payload["counts"]
    print(
        f"\n=== {collected_at}: {counts['imports']} imports, "
        f"{counts['scorable']} scorable "
        f"(combined arm {counts['combined_arm']}, "
        f"per-league only {counts['per_league_only']}) ==="
    )
    for label, block in payload["competitions"].items():
        print(f"  {label}: {block['clubs']} clubs")
        if block["known_upstream_gap"]:
            print(
                f"    MISSING upstream (not zero signings): "
                f"{block['known_upstream_gap']}"
            )
        if block["unexplained_empty_roster"]:
            print(f"    UNEXPLAINED empty roster: {block['unexplained_empty_roster']}")

    if args.out:
        path = write_payload(
            payload,
            artifact_path(
                args.out,
                payload["season"],
                tuple(reports),
                collected_at=collected_at,
            ),
        )
        print(f"\nWrote {path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
