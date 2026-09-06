"""The 2026-27 prediction set: schema, refusal codes, and the pure builder.

The pre-registration (`docs/research/preregistration-2026-27-predictions.md`)
fixes what a prediction is: a projected destination per-36 PIR **with an
interval**, a declared scoring method, and a first-class refusal list. This
module is the single place that shape is defined, so the builder and the
evaluator cannot drift into two schemas with no common producer -- which is the
ATI-2917 defect one layer up.

Nothing here touches the filesystem or the network. The script wires I/O; this
decides what a row is.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field

#: §4 interval construction. Kept as multipliers because that is how the base
#: document states it, and restating it as a sigma would invite a re-derivation
#: that lands somewhere else.
INTERVAL_LOW_MULT = 0.4986
INTERVAL_HIGH_MULT = 1.6392

#: Amendment 1 Change 3. Every published interval carries this string. The
#: nominal figure alone is the claim ATI-2799 G7 measured and disproved.
INTERVAL_LABEL = "nominal 95%, realised 0.922 on held-out transfers (ATI-2799 G7)"


@dataclass(frozen=True)
class IntervalSpec:
    """How a projection's interval is built.

    ``multiplier`` is the base document's construction (§4, Amendment 1 Change
    3). ``conformal`` is the split-conformal interval Study C of the pre-lock
    program selected on rolling out-of-sample residuals (ATI-2963): the point
    plus and minus one calibrated half-width, the same for every row. Which one
    the lock carries is Amendment 8's decision; the default stays the base
    document's until that amendment says otherwise.
    """

    kind: str = "multiplier"
    low_mult: float = INTERVAL_LOW_MULT
    high_mult: float = INTERVAL_HIGH_MULT
    half_width: float | None = None
    label: str = INTERVAL_LABEL
    source: str = "base document §4 / Amendment 1 Change 3"

    def bounds(self, point: float) -> tuple[float, float]:
        if self.kind == "multiplier":
            return point * self.low_mult, point * self.high_mult
        if self.kind == "conformal":
            if self.half_width is None or not self.half_width >= 0:
                raise ValueError("a conformal interval needs a calibrated half-width")
            return point - self.half_width, point + self.half_width
        raise ValueError(f"unknown interval kind {self.kind!r}")

    def describe(self) -> dict:
        out = {"kind": self.kind, "label": self.label, "source": self.source}
        if self.kind == "multiplier":
            out.update({"low_mult": self.low_mult, "high_mult": self.high_mult})
        else:
            out["half_width"] = self.half_width
        return out


DEFAULT_INTERVAL = IntervalSpec()

#: Amendment 2 Change 2: a source season PLUS prior history.
MIN_SEASONS_FOR_COMBINED_ARM = 2

K_LAG_RULE = (
    "median realised ratio of observed to predicted per-36 PIR on newcomer "
    "cohorts from seasons strictly before the prediction season (Amendment 1 "
    "Change 2). Computed once, recorded here before tip-off, never refit after."
)

#: §3. A refusal is published with its code AND the rule that produced it: a
#: bare code makes the list unreadable without the document beside it.
REFUSAL_REASONS = {
    "R1": "NO_PRIOR_LEAGUE — an import whose prior league is not in the corpus",
    "R2": (
        "NOT_AN_IMPORT — intra_league_move, returning_to_club or "
        "returning_to_league; his prior production is already continental"
    ),
    "R3": (
        "SOURCE_REFUSED — prior league is poland-plk (its euroleague cell rests "
        "on n=7) or in the estimator's NOT_A_SOURCE set"
    ),
    "R4": "DEGENERATE_RATE — a non-positive source per-36 rate; the ratio is undefined",
    "R5": "INSUFFICIENT_SOURCE_GAMES — fewer than 8 games in the source league-season",
    "R9": (
        "SOURCE_SEASON_INCOMPLETE — the source league-season holds fewer games "
        "in the corpus than the league's complete-season count because "
        "collection stopped (Amendment 4 Change 3); checked before R5, so a "
        "refusal caused by the corpus is never reported as one caused by the "
        "player"
    ),
    "R7": (
        "ROSTER_MISSING — the club's 2026-27 roster is absent upstream. "
        "Missing, not zero"
    ),
    "R8": "NOT_SCORED_YET — fewer than 8 destination games at this checkpoint",
}

#: R6 is deliberately absent above: an unreliable cell is a LABELLED FALLBACK to
#: the tier mean, which the estimator's docstring requires of consumers, not a
#: refusal. Dropping those players would silently shrink the scored population.
LABELLED_FALLBACK_CODE = "R6"

PREDICTION_FIELDS = (
    "person_code",
    "name",
    "competition",
    "club_code",
    "origin_league",
    "destination",
    "pir_per36_src",
    "prior_mean_pir36",
    "factor",
    "factor_reliable",
    "scoring_method",
    "projection",
    "interval_low",
    "interval_high",
    "baseline_b0",
    "baseline_b1c",
    # Amendment 3 Change 2 (accepted in Amendment 4): the completeness of the
    # source league-season travels with every row, denominator printed.
    "source_season",
    "source_games_held",
    "source_last_game",
    "source_completeness",
    "source_complete_season_games",
    # Amendment 6 (ATI-2959, option 2): how far the source season sits behind
    # the latest possible one; 0 is the season before the prediction season.
    "source_season_lag",
)

REFUSAL_FIELDS = (
    "person_code",
    "name",
    "competition",
    "club_code",
    "code",
    "reason",
    "source_league",
    "source_season",
    "source_games_held",
    "source_last_game",
    "source_completeness",
    "source_complete_season_games",
    "source_season_lag",
)

COMBINED_ARM = "combined"
PER_LEAGUE_ONLY = "per_league_only"


#: §2/§3. `poland-plk` is refused by declaration (its euroleague cell rests on
#: n=7); the rest is the estimator's own NOT_A_SOURCE definition.
REFUSED_SOURCE_LEAGUES = frozenset(
    {"poland-plk", "bcl", "test", "euroleague", "eurocup"}
)

#: §2. Fewer than this in the source league-season and the rate is not a rate.
MIN_SOURCE_GAMES = 8

#: Amendment 4 Change 3, floor written down BEFORE the first run (2026-09-04).
#: `source_completeness` is games held ÷ the league's maximum distinct-game
#: count over seasons 2022–2024 (Amendment 3 Change 2). Measured on the corpus
#: the day the floor was set: the six leagues whose collection stopped in
#: January 2026 sit at 0.30–0.48 for season 2025; every league scraped in full
#: sits at 0.93–1.00. 0.9 separates them with margin on both sides. It is a
#: property of the corpus, not a tuning knob: the reversal condition in
#: Amendment 4 (a completed season stops firing R9) works through this number
#: without a code change, and a league-size change that lowers a COMPLETE
#: season below it (france-pro-a 2024: 240 of a 306 maximum) is reported by the
#: builder as such rather than hidden by moving the floor.
SOURCE_COMPLETENESS_FLOOR = 0.9

#: Seasons the completeness denominator is the maximum over (Amendment 3).
COMPLETENESS_DENOMINATOR_SEASONS = (2022, 2023, 2024)  # season-literal-ok

IMPORT_KIND = "import"


def _missing(value: object) -> bool:
    """Is this absent?

    `NaN` needs naming explicitly. The signings artifacts carry bare `NaN`
    literals, `json.load` turns them into `float('nan')`, and **a NaN is
    truthy** -- so a plain `if not value` reads "he has a prior league" for a
    player who has none, and he is refused under the wrong rule.
    """
    if value is None:
        return True
    if isinstance(value, float) and value != value:
        return True
    return not str(value).strip()


def classify_refusal(
    *,
    kind: str,
    prior_league: str | None,
    source_games: int | None,
    source_rate: float | None,
    roster_missing: bool = False,
    source_completeness: float | None = None,
    completeness_floor: float = SOURCE_COMPLETENESS_FLOOR,
) -> str | None:
    """Which §3 rule refuses this arrival, or ``None`` if he is scorable.

    Order matters and is fixed here rather than emerging from the call site.
    R7 outranks everything: with no published roster nothing about the player is
    known, so returning R1 would assert something the data cannot support.
    R9 precedes R5 (Amendment 4): a player whose source season is half-scraped
    would otherwise be refused for "too few games" — a fact about the corpus
    reported as a fact about him. Because R9 runs first, Amendment 3's `R5c`
    label (an R5 caused by the corpus) can no longer occur and is not emitted.
    ``source_completeness=None`` means no measurement exists (the player has no
    corpus season at all) and R9 stays silent; the row falls through to R5.
    """
    if roster_missing:
        return "R7"
    if kind != IMPORT_KIND:
        return "R2"
    if _missing(prior_league):
        return "R1"
    if prior_league in REFUSED_SOURCE_LEAGUES:
        return "R3"
    if source_completeness is not None and source_completeness < completeness_floor:
        return "R9"
    if source_games is not None and source_games < MIN_SOURCE_GAMES:
        return "R5"
    if source_rate is None or source_rate <= 0:
        return "R4"
    return None


@dataclass(frozen=True)
class SourceSeasonCompleteness:
    """Amendment 3 Change 2: how complete the source league-season is in the corpus.

    ``games_held`` is distinct games the corpus holds for that league-season,
    ``complete_season_games`` the league's maximum distinct-game count over
    :data:`COMPLETENESS_DENOMINATOR_SEASONS`, and ``completeness`` their ratio
    (above 1 is possible when a league grew, and is reported as is).
    ``last_game`` is the latest game date held, ISO ``YYYY-MM-DD``.
    """

    league: str
    season: int
    games_held: int
    last_game: str | None
    complete_season_games: int
    completeness: float


@dataclass(frozen=True)
class ScorableCandidate:
    """One import the model will project."""

    person_code: str
    name: str
    competition: str
    club_code: str
    origin_league: str
    destination: str
    pir_per36_src: float
    projection: float
    scoring_method: str
    factor: float
    factor_reliable: bool
    baseline_b1c: float
    prior_mean_pir36: float | None = None
    source: SourceSeasonCompleteness | None = None


@dataclass(frozen=True)
class RefusedCandidate:
    """One arrival the model declines to project, and why."""

    person_code: str
    name: str
    competition: str
    club_code: str
    code: str
    detail: dict = field(default_factory=dict)
    source: SourceSeasonCompleteness | None = None


def build_prediction_set(
    scorable: list[ScorableCandidate],
    refused: list[RefusedCandidate],
    *,
    season: int,
    collected_at: str,
    built_at: str,
    k_lag: float,
    source_collection: str,
    status: str = "draft",
    completeness_floor: float = SOURCE_COMPLETENESS_FLOOR,
    completeness_denominators: dict | None = None,
    continental_source: str | None = None,
    interval: IntervalSpec = DEFAULT_INTERVAL,
) -> dict:
    """Assemble the versioned prediction artifact.

    Refuses an empty refusal list: acceptance criterion 5 of ATI-2891 states
    that a prediction set with no refusals means the refusal rule is not
    working, and a rule that never rejects is indistinguishable from one that
    never runs.
    """
    if not refused:
        raise ValueError(
            "no refusals: a prediction set with an empty refusal list means the "
            "refusal rule did not run. Refusals are a first-class output "
            "(ATI-2891 acceptance criterion 5), not an error state."
        )

    unknown = sorted({r.code for r in refused} - set(REFUSAL_REASONS))
    if unknown:
        raise ValueError(
            f"unknown refusal code(s): {unknown}. Every published refusal must "
            f"trace to a rule in §3; known codes are {sorted(REFUSAL_REASONS)}."
        )

    methods = [c.scoring_method for c in scorable]
    return {
        "season": season,
        "status": status,
        "built_at": built_at,
        "collected_at": collected_at,
        "source_collection": source_collection,
        "basis": {
            "k_lag": k_lag,
            "k_lag_rule": K_LAG_RULE,
            "min_seasons_for_combined_arm": MIN_SEASONS_FOR_COMBINED_ARM,
            "interval": interval.describe(),
            # Amendment 4: which corpus the factors, K_LAG and RTM arms were
            # fitted on, and the R9 floor with its denominators, so a reader
            # can re-derive every refusal from the artifact alone.
            "continental_source": continental_source,
            "source_completeness": {
                "floor": completeness_floor,
                "rule": (
                    "R9 SOURCE_SEASON_INCOMPLETE fires when games held in the "
                    "source league-season / the league's maximum distinct-game "
                    f"count over seasons {list(COMPLETENESS_DENOMINATOR_SEASONS)} "
                    "is below the floor (Amendment 4 Change 3; measure from "
                    "Amendment 3 Change 2). Checked before R5."
                ),
                "denominator_seasons": list(COMPLETENESS_DENOMINATOR_SEASONS),
                "complete_season_games_by_league": completeness_denominators or {},
            },
        },
        "counts": {
            "predicted": len(scorable),
            "refused": len(refused),
            "combined_arm": sum(1 for m in methods if m == COMBINED_ARM),
            "per_league_only": sum(1 for m in methods if m == PER_LEAGUE_ONLY),
            "refused_by_code": _count_by_code(refused),
        },
        "predictions": [
            _prediction_row(c, season=season, interval=interval) for c in scorable
        ],
        "refusals": [_refusal_row(r, season=season) for r in refused],
    }


def _count_by_code(refused: list[RefusedCandidate]) -> dict[str, int]:
    out: dict[str, int] = {}
    for r in refused:
        out[r.code] = out.get(r.code, 0) + 1
    return dict(sorted(out.items()))


def source_season_lag(source_season: int | None, *, season: int) -> int | None:
    """Amendment 6: `(season - 1) - source_season`, `None` without a source season.

    The base document's source-season rule permits a prediction to rest on a
    season several years back; the lag is recorded on every row so the scoring
    can split by it (a descriptive read, not a gate). Staleness is NOT a
    refusal rule (ATI-2959 option 2): refusing would lower the B0 power the
    set already lacks, to remove an effect nobody has measured.
    """
    if source_season is None:
        return None
    lag = (season - 1) - int(source_season)
    if lag < 0:
        raise ValueError(
            f"source season {source_season} is not before prediction season "
            f"{season}: the source-season rule admits only prior seasons"
        )
    return lag


def _source_fields(src: SourceSeasonCompleteness | None, *, season: int) -> dict:
    """The Amendment 3 fields, `None` when no corpus season exists for the player."""
    if src is None:
        return {
            "source_league": None,
            "source_season": None,
            "source_games_held": None,
            "source_last_game": None,
            "source_completeness": None,
            "source_complete_season_games": None,
            "source_season_lag": None,
        }
    return {
        "source_league": src.league,
        "source_season": src.season,
        "source_games_held": src.games_held,
        "source_last_game": src.last_game,
        "source_completeness": src.completeness,
        "source_complete_season_games": src.complete_season_games,
        "source_season_lag": source_season_lag(src.season, season=season),
    }


def _prediction_row(
    c: ScorableCandidate, *, season: int, interval: IntervalSpec = DEFAULT_INTERVAL
) -> dict:
    row = asdict(c)
    row["interval_low"], row["interval_high"] = interval.bounds(c.projection)
    # B0 is the untranslated source rate by definition (§5), so it is derived
    # rather than passed -- there is no way for it to disagree with the input.
    row["baseline_b0"] = c.pir_per36_src
    row.update(_source_fields(c.source, season=season))
    return {k: row[k] for k in PREDICTION_FIELDS}


def _refusal_row(r: RefusedCandidate, *, season: int) -> dict:
    row = asdict(r)
    row["reason"] = REFUSAL_REASONS[r.code]
    row.update(_source_fields(r.source, season=season))
    return {k: row[k] for k in REFUSAL_FIELDS}
