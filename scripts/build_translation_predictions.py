#!/usr/bin/env python
"""Build the 2026-27 prospective prediction set (ATI-2891).

The pre-registration fixes what a prediction is; this produces it. Every arm,
constant and fallback here is imported from the scripts the amendments name as
the executable form rather than reimplemented -- `build_league_factors.py` for
the estimator, `validate_translation_holdout.py` for the population rules, and
`validate_translation_walkforward.py` for the fold that refits factors, `K_LAG`
and the RTM arms on seasons strictly before the prediction season. A
reimplementation would be free to drift from the evidence the document cites,
which is the whole thing this artifact exists to prevent.

What comes out is a versioned artifact with a schema (`src/data/translation_
predictions.py`), a refusal list, and a per-player scoring-method label.

Usage::

    uv run python scripts/build_translation_predictions.py \\
        --signings data/processed/signings/\
import_signings_2026_both_competitions_<collection-date>.json \\
        --out data/processed/predictions

The signings artifact is stamped with its collection date (ATI-2917): pass the
collection the publication names, not "the latest file", or the prediction set
silently rests on a different population than the one it reports.
"""

from __future__ import annotations

import argparse
import datetime
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

import scripts.build_league_factors as blf  # noqa: E402
import scripts.validate_translation_holdout as vh  # noqa: E402
import scripts.validate_translation_walkforward as wf  # noqa: E402
from scripts.collect_import_signings import write_payload  # noqa: E402
from src.data.corpus.euroleague_api import pairing_key  # noqa: E402
from src.data.translation_predictions import (  # noqa: E402
    COMBINED_ARM,
    COMPLETENESS_DENOMINATOR_SEASONS,
    DEFAULT_INTERVAL,
    MIN_SEASONS_FOR_COMBINED_ARM,
    MIN_SOURCE_GAMES,
    PER_LEAGUE_ONLY,
    SOURCE_COMPLETENESS_FLOOR,
    IntervalSpec,
    RefusedCandidate,
    ScorableCandidate,
    SourceSeasonCompleteness,
    build_prediction_set,
    classify_refusal,
)

#: Proballers writes game dates as ``"Oct 6, 2025"``; the API side carries none.
_PROBALLERS_DATE_FORMAT = "%b %d, %Y"

_DEFAULT_OUT = REPO / "data" / "processed" / "predictions"


def source_season_rows(games: pd.DataFrame, prediction_season: int) -> pd.DataFrame:
    """One row per player: the domestic season the 2026-27 projection starts from.

    The rules mirror the estimator's own `build_pairs` rather than restating
    them: >=8 games, largest-minutes stint per season, continental competitions
    are never a source. `prior_mean_pir36` is minutes-weighted over every
    domestic season strictly BEFORE the source season -- including it would make
    the regression-to-the-mean term partly a copy of the predictor it regresses.
    """
    games = games.copy()
    # Reconcile the two spellings ONCE, through the key the corpus itself pairs
    # on since Amendment 4 (`pairing_key`: diacritics stripped, suffix dropped,
    # `LAST, FIRST` reordered). The corpus writes "Both Gach", the roster
    # endpoint writes "GACH, BOTH"; both become "BOTH GACH". Matching on a
    # different rule here would source a player's rate from one matching and
    # his prior league from another. Measured before any normaliser existed:
    # 0 of 120 arrivals joined, and every one fell through to refusal R1. The
    # caller applies the same function to the signings names.
    games["player_name"] = games.player_name.map(pairing_key)
    games = games[games.player_name.notna()]

    agg = (
        games.groupby(["player_name", "season", "league"])
        .agg(
            games=("game_id", "nunique"),
            minutes=("minutes", "sum"),
            pir=("pir", "sum"),
        )
        .reset_index()
    )
    agg = agg[agg.minutes > 0].copy()
    agg["pir_per36"] = 36 * agg.pir / agg.minutes

    domestic = agg[~agg.league.isin(blf.NOT_A_SOURCE)]
    domestic = domestic[domestic.season < prediction_season]

    # Pre-threshold, for the prior mean: a season too thin to BE a source is
    # still evidence about the player, exactly as `build_switchers` treats it.
    hist = (
        domestic.groupby(["player_name", "season"])[["pir", "minutes"]]
        .sum()
        .sort_index()
        .reset_index()
    )
    hist[["cum_pir", "cum_min"]] = hist.groupby("player_name")[
        ["pir", "minutes"]
    ].cumsum()
    hist["prior_pir"] = hist.cum_pir - hist.pir
    hist["prior_min"] = hist.cum_min - hist.minutes
    hist["prior_mean_pir36"] = np.where(
        hist.prior_min > 0, 36 * hist.prior_pir / hist.prior_min, np.nan
    )

    eligible = domestic[domestic.games >= MIN_SOURCE_GAMES].copy()
    # largest-minutes stint per season, then the latest qualifying season
    eligible = eligible.sort_values("minutes", ascending=False).drop_duplicates(
        ["player_name", "season"]
    )
    n_seasons = (
        eligible.groupby("player_name").season.nunique().rename("n_domestic_seasons")
    )
    latest = eligible.sort_values("season", ascending=False).drop_duplicates(
        ["player_name"]
    )

    out = latest.rename(
        columns={
            "season": "season_src",
            "league": "league_src",
            "pir_per36": "pir_per36_src",
            "games": "games_src",
            "minutes": "minutes_src",
        }
    )[
        [
            "player_name",
            "season_src",
            "league_src",
            "pir_per36_src",
            "games_src",
            "minutes_src",
        ]
    ]
    out = out.merge(n_seasons, on="player_name", how="left")
    out = out.merge(
        hist[["player_name", "season", "prior_mean_pir36"]].rename(
            columns={"season": "season_src"}
        ),
        on=["player_name", "season_src"],
        how="left",
        validate="1:1",
    )
    out["above_own_prior"] = out.pir_per36_src > out.prior_mean_pir36
    return out.reset_index(drop=True)


def source_season_completeness(games: pd.DataFrame) -> pd.DataFrame:
    """Amendment 3 Change 2: games held, last game and completeness per league-season.

    Domestic (source) leagues only — the continental side is never a source.
    ``complete_season_games`` is the league's MAXIMUM distinct-game count over
    :data:`COMPLETENESS_DENOMINATOR_SEASONS`, not the previous season's, because
    a single prior season is not a safe yardstick on this corpus (greece-a1
    2024 is itself partial; france-pro-a went 306 -> 240 as the league shrank).
    A ratio above 1 is possible when a league grew and is reported as is.
    """
    dom = games[~games.league.isin(blf.NOT_A_SOURCE)]
    dates = pd.to_datetime(dom.date, format=_PROBALLERS_DATE_FORMAT, errors="coerce")
    per = (
        dom.assign(_date=dates)
        .groupby(["league", "season"])
        .agg(games_held=("game_id", "nunique"), last_game=("_date", "max"))
        .reset_index()
    )
    den = (
        per[per.season.isin(COMPLETENESS_DENOMINATOR_SEASONS)]
        .groupby("league")
        .games_held.max()
        .rename("complete_season_games")
    )
    per = per.merge(den, on="league", how="left")
    per["completeness"] = per.games_held / per.complete_season_games
    per["last_game"] = per.last_game.dt.strftime("%Y-%m-%d")
    return per.sort_values(["league", "season"]).reset_index(drop=True)


def completeness_lookup(
    per: pd.DataFrame,
) -> dict[tuple[str, int], SourceSeasonCompleteness]:
    return {
        (r.league, int(r.season)): SourceSeasonCompleteness(
            league=r.league,
            season=int(r.season),
            games_held=int(r.games_held),
            last_game=None if pd.isna(r.last_game) else str(r.last_game),
            complete_season_games=int(r.complete_season_games),
            completeness=float(r.completeness),
        )
        for r in per.itertuples()
        if pd.notna(r.complete_season_games)
    }


def _rtm_predictions(fold: dict, cand: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    """(combined arm, league-free RTM) for the candidates.

    Both are fitted on the fold's strictly-prior cohort rows with
    `validate_translation_walkforward`'s own design matrix, so the coefficients
    are the ones its published contrasts were measured on.
    """
    train = fold["train_rows"]
    k = fold["k_lag"]
    mult_fn = fold["multiplier_fn"]

    def translated(df: pd.DataFrame) -> np.ndarray:
        return df.pir_per36_src.to_numpy(dtype=float) * mult_fn(df) * k

    y_train = train.pir_per36_dest.to_numpy(dtype=float)
    out = []
    for tr_col, te_col in (
        (translated(train), translated(cand)),  # combined: RTM + per-league
        (None, None),  # B1c: RTM alone, no league information
    ):
        beta, *_ = np.linalg.lstsq(wf._rtm_design(train, tr_col), y_train, rcond=None)
        out.append(wf._rtm_design(cand, te_col) @ beta)
    return out[0], out[1]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--signings", type=Path, required=True)
    ap.add_argument("--season", type=int, default=2026, help="2026 == 2026-27")
    ap.add_argument("--out", type=Path, default=_DEFAULT_OUT)
    ap.add_argument(
        "--interval-params",
        type=Path,
        default=None,
        help="interval_params_lock.json from calibrate_prediction_intervals.py "
        "--lock-calibration; omitted, the base document's multiplier interval "
        "is used. Amendment 8 decides which the lock carries.",
    )
    ap.add_argument("--built-at", default=None)
    ap.add_argument(
        "--status",
        default="draft",
        choices=("draft", "locked"),
        help="`locked` is the pre-tip-off artifact. Anything built from an "
        "earlier collection must say draft in the FILE, not only in a commit "
        "message.",
    )
    ap.add_argument(
        "--continental-source",
        choices=blf.CONTINENTAL_SOURCES,
        default=blf.DEFAULT_CONTINENTAL_SOURCE,
        help="corpus the factors, K_LAG and RTM arms are refit on (Amendment 4: api)",
    )
    args = ap.parse_args(argv)

    signings = json.loads(args.signings.read_text())
    built_at = args.built_at or datetime.date.today().isoformat()

    print(f"Loading corpus (continental_source={args.continental_source})…")
    games, pairs = vh.load_corpus(args.continental_source)
    switch, _ = vh.build_switchers(games)
    cohorts = switch[switch.was_cont == 0]
    cohorts = cohorts[~cohorts.league_src.isin(vh.EXCLUDED_SOURCE)]
    cohorts = cohorts[cohorts.pir_per36_src > 0]

    fold = wf.one_season(pairs, cohorts, args.season)
    print(
        f"factors refit on {fold['n_train_pairs']} pairs < {args.season}; "
        f"K_LAG = {fold['k_lag']:.4f} from {fold['n_train_cohort']} cohort rows"
    )

    src = source_season_rows(games, args.season).set_index("player_name")
    missing_clubs = {
        c
        for block in signings["competitions"].values()
        for c in block.get("clubs_with_empty_roster", [])
    }

    # Amendment 3 Change 2 / Amendment 4 Change 3: completeness per source
    # league-season, denominators printed BEFORE any refusal is classified.
    per_season = source_season_completeness(games)
    comp = completeness_lookup(per_season)
    den = (
        per_season.drop_duplicates("league")
        .set_index("league")
        .complete_season_games.dropna()
        .astype(int)
        .to_dict()
    )
    print(
        f"\nR9 floor: source_completeness < {SOURCE_COMPLETENESS_FLOOR} "
        "(denominator = max distinct games over "
        f"{list(COMPLETENESS_DENOMINATOR_SEASONS)})"
    )
    latest = per_season[per_season.season == args.season - 1]
    print(
        latest[
            [
                "league",
                "season",
                "games_held",
                "last_game",
                "complete_season_games",
                "completeness",
            ]
        ].to_string(index=False, float_format=lambda x: f"{x:.3f}")
    )

    scorable_rows, refused = [], []
    joined = 0
    for a in signings["arrivals"]:
        key = pairing_key(a["name"])
        s = src.loc[key] if key in src.index else None
        joined += s is not None
        source = None if s is None else comp.get((str(s.league_src), int(s.season_src)))
        code = classify_refusal(
            kind=a["kind"],
            prior_league=a.get("prior_league"),
            # 0 games, not None: a player absent from the corpus has no
            # qualifying source season (R5). Passing None would land him on R4
            # DEGENERATE_RATE, which asserts a measurement never taken.
            source_games=0 if s is None else int(s.games_src),
            source_rate=None if s is None else float(s.pir_per36_src),
            roster_missing=a["club_code"] in missing_clubs,
            source_completeness=None if source is None else source.completeness,
        )
        if code is not None:
            refused.append(
                RefusedCandidate(
                    person_code=a["person_code"],
                    name=a["name"],
                    competition=a["competition"],
                    club_code=a["club_code"],
                    code=code,
                    source=source,
                )
            )
            continue
        # no leading underscore: itertuples() would rename it positionally
        scorable_rows.append({**a, **s.to_dict(), "source_row": source})
    print(
        f"{joined} of {len(signings['arrivals'])} arrivals joined a corpus "
        "source season"
    )

    if not scorable_rows:
        print("REFUSING: no scorable arrivals at all.", file=sys.stderr)
        return 2

    cand = pd.DataFrame(scorable_rows)
    cand["league_dest"] = cand.competition
    mult = fold["multiplier_fn"](cand)
    per_league = cand.pir_per36_src.to_numpy(dtype=float) * mult * fold["k_lag"]
    combined, rtm_only = _rtm_predictions(fold, cand)

    use_combined = cand.n_domestic_seasons.to_numpy() >= MIN_SEASONS_FOR_COMBINED_ARM
    projection = np.where(use_combined, combined, per_league)

    reliable = reliable_lookup(fold)
    scorable = [
        ScorableCandidate(
            person_code=r.person_code,
            name=r.name,
            competition=r.competition,
            club_code=r.club_code,
            origin_league=r.league_src,
            destination=r.league_dest,
            pir_per36_src=float(r.pir_per36_src),
            prior_mean_pir36=(
                None if pd.isna(r.prior_mean_pir36) else float(r.prior_mean_pir36)
            ),
            factor=float(mult[i]),
            factor_reliable=bool(reliable.get((r.league_src, r.league_dest), False)),
            scoring_method=COMBINED_ARM if use_combined[i] else PER_LEAGUE_ONLY,
            projection=float(projection[i]),
            baseline_b1c=float(rtm_only[i]),
            source=r.source_row,
        )
        for i, r in enumerate(cand.itertuples())
    ]

    payload = build_prediction_set(
        scorable,
        refused,
        season=args.season,
        collected_at=signings["collected_at"],
        built_at=built_at,
        k_lag=float(fold["k_lag"]),
        source_collection=args.signings.name,
        status=args.status,
        completeness_denominators=den,
        continental_source=args.continental_source,
        interval=interval_spec(args.interval_params),
    )
    counts = payload["counts"]
    print(
        f"\n{counts['predicted']} predicted "
        f"({counts['combined_arm']} combined arm, "
        f"{counts['per_league_only']} per-league only), "
        f"{counts['refused']} refused"
    )
    for code, n in counts["refused_by_code"].items():
        print(f"  {code}: {n}")
    r9 = [r for r in payload["refusals"] if r["code"] == "R9"]
    if r9:
        print("\nR9 by source league-season (last game held beside it):")
        by = (
            pd.DataFrame(r9)
            .groupby(
                [
                    "source_league",
                    "source_season",
                    "source_last_game",
                    "source_completeness",
                ]
            )
            .size()
        )
        print(by.to_string())
        print(
            "R9 rows whose source league-season is NOT one of the six leagues "
            "Amendment 4 names: "
            + str(
                sorted(
                    {
                        (r["source_league"], r["source_season"])
                        for r in r9
                        if r["source_league"] not in AMENDMENT_4_INCOMPLETE_LEAGUES
                    }
                )
                or "none"
            )
        )
    scorable_by_league = pd.Series([c.origin_league for c in scorable]).value_counts()
    print("\npredicted, by source league:")
    print(scorable_by_league.to_string())

    args.out.mkdir(parents=True, exist_ok=True)
    path = write_payload(
        payload, args.out / f"translation_predictions_{args.season}.json"
    )
    # The factor cells the projections were multiplied by, committed beside
    # them (data/processed/translation/ is gitignored). Same fold table the
    # projections read, so the two cannot disagree.
    fac = fold["table"][
        [
            "league",
            "destination",
            "factor",
            "factor_raw",
            "se",
            "ci_lo",
            "ci_hi",
            "n_pairs",
            "n_clusters",
            "reliable",
            "tier_mean",
            "tau",
        ]
    ].copy()
    fac.insert(0, "continental_source", args.continental_source)
    fac.insert(1, "fit_seasons_max", int(fold["train_rows"].season_dest.max()))
    fac_path = args.out / f"translation_factors_{args.season}.csv"
    fac.to_csv(fac_path, index=False, float_format="%.6f")
    print(f"\nWrote {path}\nWrote {fac_path}")
    return 0


#: The six leagues Amendment 4 Change 3 names. NOT an input to R9 — the code is
#: driven by the completeness measure — but the run prints any R9 refusal that
#: falls OUTSIDE this set, because such a row is either the reversal condition
#: working in the wrong direction or a league-size artifact of the denominator,
#: and a reader must see it rather than infer it from a count.
AMENDMENT_4_INCOMPLETE_LEAGUES = frozenset(
    {"france-pro-a", "turkey-bsl", "aba-league", "vtb", "lithuania-lkl", "poland-plk"}
)


def interval_spec(path: Path | None) -> IntervalSpec:
    """The interval the artifact carries: the multiplier unless a calibrated
    conformal half-width is handed in (Amendment 8)."""
    if path is None:
        return DEFAULT_INTERVAL
    params = json.loads(path.read_text())
    if params.get("family") != "conformal":
        raise ValueError(
            f"{path}: only the split-conformal family is wired into the builder; "
            f"got {params.get('family')!r}"
        )
    folds = params.get("calibration_folds", [])
    return IntervalSpec(
        kind="conformal",
        half_width=float(params["q_hat"]),
        label=(
            f"nominal {int(round(100 * (1 - params.get('alpha', 0.05))))}%, split "
            f"conformal half-width {float(params['q_hat']):.2f} PIR/36 calibrated on "
            f"walk-forward folds {folds[0] if folds else '?'}–{folds[-1] if folds else '?'} "  # noqa: E501
            f"({params.get('n_cal', '?')} out-of-sample rows); Study C, Amendment 8"
        ),
        source=str(path.name),
    )


def reliable_lookup(fold: dict) -> dict:
    """Which (source, destination) cells carried their own factor.

    A `False` means the projection used the destination tier mean -- §3's R6
    labelled fallback. It is published, not refused, but it must be visible.

    Refuses a fold with no factor table rather than returning an empty mapping:
    an empty mapping publishes EVERY cell as `factor_reliable: False`, i.e. a
    prediction set claiming a tier-mean fallback it never made. A silent False
    is as wrong as a silent True and harder to spot, because it reads as the
    conservative answer.
    """
    if "table" not in fold:
        raise KeyError(
            "fold carries no factor table, so cell reliability cannot be "
            "reported. Defaulting it would label every projection a tier-mean "
            "fallback (§3 R6) that never happened."
        )
    return {
        (r.league, r.destination): bool(r.reliable) for r in fold["table"].itertuples()
    }


if __name__ == "__main__":
    sys.exit(main())
