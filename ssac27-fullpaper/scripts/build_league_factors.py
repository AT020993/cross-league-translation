"""Estimate cross-league translation factors → data/processed/translation/.

The identification strategy is the **same-season dual-tier natural experiment**
(ATI-2788, `docs/superpowers/specs/2026-08-04-player-translation-projection-design.md`
§3): some European clubs play a domestic league and a continental competition in
the same season, so the same player, in the same season, produces on both sides.
The player is his own control, which removes the selection confound that ruins
consecutive-season transfer studies (players move *because* they improved or
declined).

A factor is the ratio of continental per-36 production to domestic per-36
production for a (source league → destination competition) pair. 0.78 means a
player's domestic rate multiplied by 0.78 is his expected continental rate.

What this script exists to fix (ATI-2827): the factor table in the spec was
produced in an ad-hoc session, was never committed as code, and **does not
reproduce under any reconstructable filter**. Everything here is therefore
explicit and printed: the sample filter, the estimator, the clustering, the
pooling, and the per-league-season sample sizes.

Method commitments, each from a specific prior error:

1. **Three estimators, always.** `docs/research/METHOD.md` §3/§6: the published
   per-stat factors moved 0.902 → 0.939 on weighting alone, which killed a
   headline. The primary is exposure-weighted; ratio-of-sums and
   mean-of-per-pair-ratios run beside it and the spread is reported. When the
   spread exceeds the bootstrap interval the choice is LOAD-BEARING and the
   table says so.
2. **Cluster bootstrap by (season × destination club), not by pair** (ATI-2827
   req 3). Pairs are heavily clustered — a couple of clubs supply most of some
   leagues' pairs — so resampling pairs understates the SE on exactly the
   leagues we most want to quote. The naive pair bootstrap is computed too, and
   its ratio to the clustered SE is reported as `se_ratio_pair_boot`.
3. **All pairs are the primary sample; role-stability is a sensitivity.** The
   spec's roster-quota argument (§3) made |Δusage| ≤ 5 and |Δmin/g| ≤ 5 the
   primary cut. It was measured on 2026-08-15 and demoted: no out-of-sample
   value (mean −0.003% RMSE over 16 splits, p = 0.97), Δusage has split-half
   reliability 0.31 so the cut is mostly noise, and the discarded pairs
   translate *worse* — excluding them censored the weak tail and biased factors
   up. `HEADLINE_SAMPLE` below is the single source of truth; the cut still runs
   at 3 / 5 / 7 as sensitivities. The quota confound is consequently NOT
   controlled here — ATI-2766 is the real fix.
4. **Partial pooling toward the destination-tier mean** (spec §4[1]).
   Empirical-Bayes shrinkage by sample size, with `reliable = false` below
   `--min-pairs`. Consumers must use the pooled factor when `reliable` is false.
5. **BCL and the continental cups are never a source league.** BCL is a parallel
   continental competition — 55% of its club-seasons also appear in a domestic
   league in the same season — so it is not "the league a player comes from".
   Treating it as one is a taxonomy error, not a thin-sample problem.

Outputs
-------
`league_factors.parquet`
    One row per (source league, destination, era, stat, sample) with the pooled
    factor, its cluster-bootstrap SE and interval, the estimator spread, and the
    `reliable` flag. This is the consumable artifact.
`league_factor_sample_sizes.parquet`
    Per (source league, destination, season) pair counts and club concentration
    — so a reader can reconstruct the sample rather than trust the total.
`league_factor_pairs.parquet`
    The pair-level sample itself, one row per player-season pair.

6. **The destination side is the EuroLeague API** (Amendment 4, ATI-2957,
   decided 2026-09-03). The Proballers copy of 2025-26 stopped in the first
   week of January 2026 and holds half the continental games; the league's
   own box scores are complete and reproduce the shipped factors within one
   bootstrap SE on 18 of 19 cells (`continental-source-check-2026-09-03.md`).
   `--continental-source proballers` keeps the old corpus reproducible. When
   the API side is used, both sides are keyed through one name normaliser
   (`src.data.corpus.euroleague_api.pairing_key`) and pairs whose destination
   season is 2015 drop, because the API holds no 2015-16 — the count is logged
   and recorded in the checks JSON.

Usage:
    uv run python scripts/build_league_factors.py
        [--continental-source api|proballers]
        [--min-games 8] [--min-pairs 75] [--n-boot 2000] [--seed 0]
        [--usage-cut 5.0] [--out-dir data/processed/translation]
        [--exclude-leagues LEAGUE ...]
"""

from __future__ import annotations

import argparse
import datetime
import glob
import json
import logging
import sys
import zlib
from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from src.data.corpus.euroleague_api import (  # noqa: E402
    API_SEASONS,
    load_api_continental,
    pairing_key,
)

logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")
logger = logging.getLogger(__name__)

_ROOT = PROJECT_ROOT
_RAW_GLOBS = (
    "data/raw/proballers/*/*/player_stats_*.parquet",
    "data/raw/_inactive_leagues/proballers/*/*/player_stats_*.parquet",
)
_OUT_DIR = _ROOT / "data" / "processed" / "translation"

#: Destination competitions. These are the scale everything is translated ONTO.
CONTINENTAL = ("euroleague", "eurocup")

#: Where the destination side of every pair is read from. `api` is the default
#: since Amendment 4 (2026-09-03); `proballers` reproduces the corpus every note
#: dated before that was fitted on.
CONTINENTAL_SOURCES = ("api", "proballers")
DEFAULT_CONTINENTAL_SOURCE = "api"

#: Source leagues dropped from the corpus BEFORE pairing when the destination
#: side is the API. poland-plk is refused as a source by the pre-registration
#: (§2/§3 R3: its EuroLeague cell rested on n = 7). On the API corpus that
#: cell holds n = 2 with a bootstrap SE of 0.21, and the method-of-moments
#: tau^2 = var(factors) - mean(SE^2) goes to zero for the WHOLE EuroLeague
#: PIR block: every league's pooled factor becomes the tier mean (0.852) and
#: `reliable` reads false on all eleven cells (measured 2026-09-04, first
#: API-side fit). One n = 2 cell erased ten leagues' factors. Excluding the
#: league the pre-registration already refuses is the declared response; the
#: estimator fragility itself — a below-floor cell participates in the
#: pooling that decides whether the floor-clearing cells keep their per-league
#: dimension — is recorded, not fixed, here (see ATI-2955 / ATI-2957).
API_SIDE_EXCLUDED_SOURCES = ("poland-plk",)

#: Never a source league. BCL is a parallel continental cup played *alongside* a
#: domestic league, not a league players are recruited out of; `test` is scraper
#: scaffolding. Excluding BCL is a definition, not a sample-size judgement.
NOT_A_SOURCE = ("bcl", "test", *CONTINENTAL)

#: Stats to translate. PIR is the headline because it is a public index the
#: league already prints — which is exactly what makes it safe to translate.
STATS: dict[str, str] = {
    "pir": "pir",
    "points": "pts",
    "rebounds": "reb",
    "assists": "ast",
    "steals": "stl",
    "blocks": "blk",
}

#: Consensus European league ordering, strongest first, as an external-validity
#: regression check (spec §3). NOT an input to estimation — nothing in the
#: method encodes it, so recovering it is evidence the method works.
CONSENSUS_ORDER = (
    "spain-acb",
    "turkey-bsl",
    "france-pro-a",
    "israel-bsl",
    "vtb",
    "lithuania-lkl",
    "aba-league",
    "poland-plk",
)

#: Era split for the drift check (spec §7: factors may drift across eras).
ERAS: dict[str, tuple[int, int]] = {
    "all": (2015, 2026),
    "2015-2019": (2015, 2019),
    "2020-2025": (2020, 2026),
}


# --------------------------------------------------------------------- load --
def load_player_games(
    continental_source: str = DEFAULT_CONTINENTAL_SOURCE,
) -> pd.DataFrame:
    """Load the box-score corpus: Proballers domestic, plus the destination side.

    ``continental_source="api"`` (default since Amendment 4) replaces the
    Proballers ``euroleague`` / ``eurocup`` rows with the league's own box
    scores mapped onto the same schema, and keys BOTH sides through
    :func:`pairing_key` so a name spelled differently by the two sources still
    pairs. ``"proballers"`` is the pre-amendment corpus, byte-for-byte: raw
    names, both sides from the scrape.

    The two Proballers trees overlap: `data/raw/proballers/{spain-acb,bcl}`
    hold one season each that is *also* present in `_inactive_leagues`.
    De-duplicating on (game_id, player_name, league) removes 9,757 rows that
    would otherwise double-weight two league-seasons.
    """
    if continental_source not in CONTINENTAL_SOURCES:
        raise ValueError(
            f"continental_source must be one of {CONTINENTAL_SOURCES}, "
            f"got {continental_source!r}"
        )
    frames = []
    for pattern in _RAW_GLOBS:
        for path in sorted(glob.glob(str(_ROOT / pattern))):
            if f"{'proballers'}/test/" in path.replace("\\", "/"):
                continue
            frames.append(pd.read_parquet(path))
    if not frames:
        raise SystemExit(f"no player_stats parquets found under {_ROOT}/data/raw")
    df = pd.concat(frames, ignore_index=True)

    before = len(df)
    df = df.drop_duplicates(["game_id", "player_name", "league"]).reset_index(drop=True)
    logger.info(
        "corpus: %d player-games (%d duplicate rows dropped across the two "
        "league trees), %d leagues, seasons %d-%d",
        len(df),
        before - len(df),
        df.league.nunique(),
        df.season.min(),
        df.season.max(),
    )

    # ATI-2827 req 2: state the PIR-availability rule explicitly rather than
    # letting a reader assume it. ATI-2826 repaired the parser bug that wrote
    # PIR into plus_minus, so `pir` should now be fully populated and the
    # `coalesce(pir, plus_minus)` workaround should be unnecessary.
    pir_null = float(df.pir.isna().mean())
    logger.info(
        "PIR availability: %.4f%% null — rule: use `pir` directly, no coalesce "
        "(ATI-2826 repaired the parser; a non-zero figure here means the repair "
        "regressed and the estimate is running on a partial sample)",
        100 * pir_null,
    )
    if pir_null > 0.001:
        raise SystemExit(
            f"pir is {100 * pir_null:.2f}% null. ATI-2826 took this to 0%. "
            "Estimating now would silently reproduce the 739-pair sample the "
            "spec warns about — repair the corpus first."
        )
    if continental_source == "proballers":
        return df
    return _swap_in_api_destination(df)


def _swap_in_api_destination(df: pd.DataFrame) -> pd.DataFrame:
    """Replace the Proballers continental rows with the API's, one key both sides.

    Printed, not implied: how many Proballers destination rows were dropped,
    how many API rows replaced them, and how many domestic player-games sit in
    a season the API does not hold (2015) and therefore can no longer pair.
    """
    api, report = load_api_continental(_ROOT)
    n_pb_cont = int(df.league.isin(CONTINENTAL).sum())
    domestic = df[~df.league.isin(CONTINENTAL)].copy()
    n_2015 = int((domestic.season < min(API_SEASONS)).sum())
    logger.info(
        "destination side from the EuroLeague API: dropped %d Proballers "
        "continental player-games, added %d API player-games (%d raw rows; "
        "%d Total/DNP/unparseable dropped; %d points mismatches), seasons %s. "
        "%d domestic player-games fall in seasons before %d, which the API "
        "does not hold — they cannot pair and are reported, not silently lost",
        n_pb_cont,
        report["rows_kept"],
        report["rows_raw"],
        report["rows_dropped_total_dnp_unparseable"],
        report["points_reconciliation_mismatches"],
        report["seasons"],
        n_2015,
        min(API_SEASONS),
    )
    n_excl = int(domestic.league.isin(API_SIDE_EXCLUDED_SOURCES).sum())
    domestic = domestic[~domestic.league.isin(API_SIDE_EXCLUDED_SOURCES)]
    logger.info(
        "continental_source=api: excluded %s before pairing (%d player-games) — "
        "refused as a source by the pre-registration; on this corpus its n=2 "
        "EuroLeague cell collapses the block's partial pooling (tau=0)",
        ", ".join(API_SIDE_EXCLUDED_SOURCES),
        n_excl,
    )
    out = pd.concat([domestic, api], ignore_index=True)
    before = len(out)
    out["player_name"] = out.player_name.map(pairing_key)
    out = out[out.player_name.notna()].reset_index(drop=True)
    if len(out) != before:
        logger.warning(
            "%d rows dropped for an empty name after normalisation", before - len(out)
        )
    out.attrs["continental_source"] = "api"
    out.attrs["api_report"] = report
    out.attrs["n_domestic_rows_before_api_seasons"] = n_2015
    out.attrs["api_side_excluded_sources"] = list(API_SIDE_EXCLUDED_SOURCES)
    out.attrs["n_player_games_excluded_api_side"] = n_excl
    return out


def add_usage(df: pd.DataFrame) -> pd.DataFrame:
    """Attach possession-based usage rate, the load-bearing role column.

    Usage — not the production ratio — is what identifies a role-stable pair
    (spec §3): if a player carries the same share of his team's possessions in
    both competitions, the only thing that changed for him is the league.
    """
    df = df.copy()
    df["fga"] = df.fg_attempted + df.fg3_attempted
    team_key = ["league", "season", "game_id", "team"]
    totals = (
        df.groupby(team_key)[["fga", "ft_attempted", "turnovers", "minutes"]]
        .sum()
        .rename(columns=lambda c: f"team_{c}")
        .reset_index()
    )
    df = df.merge(totals, on=team_key, how="left", validate="m:1")
    df["poss"] = df.fga + 0.44 * df.ft_attempted + df.turnovers
    df["team_poss"] = df.team_fga + 0.44 * df.team_ft_attempted + df.team_turnovers
    return df


def build_pairs(df: pd.DataFrame, *, min_games: int) -> pd.DataFrame:
    """One row per (player, season) observed in a source league AND a destination.

    Key is `player_name + season` — Proballers has no stable person id, which is
    why `name_collision` is a declared threat and gets its own control.
    """
    df = df.copy()
    df["tier"] = np.where(df.league.isin(CONTINENTAL), "destination", "source")
    agg = (
        df.groupby(["player_name", "season", "league", "tier"])
        .agg(
            games=("game_id", "nunique"),
            minutes=("minutes", "sum"),
            pts=("points", "sum"),
            reb=("rebounds", "sum"),
            ast=("assists", "sum"),
            stl=("steals", "sum"),
            blk=("blocks", "sum"),
            pir=("pir", "sum"),
            poss=("poss", "sum"),
            team_poss=("team_poss", "sum"),
            team_minutes=("team_minutes", "sum"),
            n_clubs=("team", "nunique"),
            club=("team", lambda s: s.value_counts().idxmax()),
            # Study B (prelock program): the component sums behind the
            # counting and rate families. Additive — nothing above reads them.
            **{k: (v, "sum") for k, v in EXTRA_SUMS.items()},
        )
        .reset_index()
    )
    agg["usage"] = (
        100 * agg.poss * (agg.team_minutes / 5) / (agg.minutes * agg.team_poss)
    )
    agg["min_per_game"] = agg.minutes / agg.games
    qualified = agg[(agg.games >= min_games) & (agg.minutes > 0)]

    dest = qualified[qualified.tier == "destination"]
    src = qualified[qualified.tier == "source"]
    src = src[~src.league.isin(NOT_A_SOURCE)]

    # Keep the largest-minutes stint per side. A player can qualify in both
    # EuroLeague and EuroCup in one season (57 cases) and in two domestic
    # leagues (1,857) — taking both sides would double-count one player-season.
    dest_n, src_n = len(dest), len(src)
    dest = dest.sort_values("minutes", ascending=False).drop_duplicates(
        ["player_name", "season"]
    )
    src = src.sort_values("minutes", ascending=False).drop_duplicates(
        ["player_name", "season"]
    )
    logger.info(
        "qualifying sides at >=%d games: %d destination (%d discarded as a "
        "smaller second stint), %d source (%d discarded)",
        min_games,
        len(dest),
        dest_n - len(dest),
        len(src),
        src_n - len(src),
    )

    pairs = dest.merge(src, on=["player_name", "season"], suffixes=("_dest", "_src"))
    pairs["d_usage"] = pairs.usage_dest - pairs.usage_src
    pairs["d_min_per_game"] = pairs.min_per_game_dest - pairs.min_per_game_src
    for stat, col in STATS.items():
        pairs[f"{stat}_per36_dest"] = 36 * pairs[f"{col}_dest"] / pairs.minutes_dest
        pairs[f"{stat}_per36_src"] = 36 * pairs[f"{col}_src"] / pairs.minutes_src
    pairs["cluster"] = (
        pairs.season.astype(str) + "|" + pairs.league_dest + "|" + pairs.club_dest
    )
    return pairs.reset_index(drop=True)


# ---------------------------------------------------------------- estimate --
def _exposure_weighted(sub: pd.DataFrame, stat: str) -> float:
    """Primary estimator: per-pair ratio weighted by the pair's exposure.

    Weight is the smaller of the two sides' minutes — a pair is only as well
    measured as its thinner side.
    """
    src = sub[f"{stat}_per36_src"].to_numpy()
    dest = sub[f"{stat}_per36_dest"].to_numpy()
    w = np.minimum(sub.minutes_dest.to_numpy(), sub.minutes_src.to_numpy())
    ok = src > 0
    if not ok.any():
        return float("nan")
    return float(np.sum(w[ok] * dest[ok] / src[ok]) / np.sum(w[ok]))


def _ratio_of_sums(sub: pd.DataFrame, stat: str) -> float:
    """Aggregate rate on each side, then divide. Weights by total minutes."""
    col = STATS[stat]
    dest_rate = sub[f"{col}_dest"].sum() / sub.minutes_dest.sum()
    src_rate = sub[f"{col}_src"].sum() / sub.minutes_src.sum()
    return float(dest_rate / src_rate) if src_rate > 0 else float("nan")


def _mean_of_ratios(sub: pd.DataFrame, stat: str) -> float:
    """Unweighted mean of per-pair ratios. Every pair counts equally."""
    src = sub[f"{stat}_per36_src"].to_numpy()
    dest = sub[f"{stat}_per36_dest"].to_numpy()
    ok = src > 0
    return float(np.mean(dest[ok] / src[ok])) if ok.any() else float("nan")


def source_volume_weighted(sub: pd.DataFrame, stat: str) -> float:
    """Per-pair ratio carrying `ratio_of_sums`'s own weights.

    Deliberately NOT in `ESTIMATORS`: this is not a candidate for reporting a
    factor, it is the counterfactual that separates the two things the primary
    and `ratio_of_sums` differ by. They differ in *form* (a mean of per-pair
    ratios versus a ratio of aggregates, which is the E[X/Y] vs E[X]/E[Y] bias)
    and in *weights* (exposure `min(minutes)` versus source volume). Comparing
    them directly confounds the two.

    Holding the weights at `ratio_of_sums`'s implicit choice — source volume,
    since sum(dest)/sum(src) up-weights whoever produced most on the source
    side — removes the form difference entirely, because the weight IS the
    denominator. That collapse is exact, not approximate:

        sum(w_i * r_i) / sum(w_i)
            with w_i = rate_src_i * min_src_i / 36 and r_i = rate_dest_i / rate_src_i
            == sum(rate_dest_i * min_src_i) / sum(rate_src_i * min_src_i)

    i.e. an AGGREGATE ratio taken with source-side minutes on both sides. So this
    estimator carries no E[X/Y] > E[X]/E[Y] bias at all, and its gap to
    `ratio_of_sums` is NOT that bias — verified: set min_src == min_dest per pair
    and the gap is 1e-16. What remains is `ratio_of_sums` weighting the
    destination aggregate by DESTINATION minutes while weighting the source
    aggregate by source minutes. The gap is an exposure-asymmetry term.

    ATI-2917 note: the surviving audit JSON labels this difference `ratio_bias`,
    which the algebra above says it is not. The label is recorded as wrong rather
    than propagated; `mean_of_ratios - ratio_of_sums` is the genuinely
    ratio-biased comparison.

    Recovered on 2026-08-26 (ATI-2917). The `machinery_artifact` control quoted
    this estimator's result as a hardcoded "~0.020" whose generator was an
    ad-hoc session script; the surviving audit JSON pinned the definition, which
    reproduces its seven EuroLeague values to 0.0003 mean absolute error where
    every alternative weighting missed by 0.007-0.017. The VALUE is recomputed
    from the current sample rather than restored from that file.
    """
    src = sub[f"{stat}_per36_src"].to_numpy()
    dest = sub[f"{stat}_per36_dest"].to_numpy()
    w = sub[f"{STATS[stat]}_src"].to_numpy()
    ok = (src > 0) & (w > 0)
    if not ok.any():
        return float("nan")
    return float(np.sum(w[ok] * dest[ok] / src[ok]) / np.sum(w[ok]))


#: Component sums carried on every pair for the stat-specific study
#: (`scripts/validate_stat_translation.py`). Short name -> corpus column. Not
#: in `STATS`, so no factor table is fitted on them unless a study asks.
STATS_SUMS: dict[str, str] = {
    "pts": "points",
    "reb": "rebounds",
    "ast": "assists",
    "stl": "steals",
    "blk": "blocks",
}
EXTRA_SUMS: dict[str, str] = {
    "oreb": "offensive_rebounds",
    "dreb": "defensive_rebounds",
    "tov": "turnovers",
    "pf": "fouls",
    "fta": "ft_attempted",
    "ftm": "ft_made",
    "fga2": "fg_attempted",
    "fgm2": "fg_made",
    "fg3a": "fg3_attempted",
    "fg3m": "fg3_made",
}

ESTIMATORS = {
    "exposure_weighted": _exposure_weighted,
    "ratio_of_sums": _ratio_of_sums,
    "mean_of_ratios": _mean_of_ratios,
}
PRIMARY = "exposure_weighted"

#: Where each estimator lands when the true factor is exactly 1.0 (ATI-2890's
#: synthetic validation, which drives `ESTIMATORS[PRIMARY]`, `cluster_bootstrap`
#: and `partial_pool` directly and reproduces `estimate_table` to 0.0 on every
#: real PIR cell of both corpora — so these are properties of this code, not of
#: a model of it). Re-pinned 2026-09-04 to the committed API-template study
#: (`docs/research/artifacts/translation-estimator-synthetic-2026-09-04/
#: summary_api.json: s2.null_by_estimator.<estimator>.mean`); the 2026-08-17
#: values (1.0181 / 0.9998 / 1.0231) came from an artifact that no longer exists
#: on any disk and are kept only in that note's record column.
#:
#: The primary is biased UP by +0.0287 on average (Monte-Carlo SE 0.0022), and
#: the bias is **flat in n from 10 to 500** (mean +0.0271 at n = 50, +0.0263 at
#: n = 500). Switching the source-side sampling noise off removes all of it
#: (residual −0.0003): the term is the noisy denominator, E[1/x_obs] > 1/E[x].
#: It is not a thin-cell artifact and more corpus cannot cure it. Comparing an
#: interval against 1.0 therefore rejects at 13% (n = 10) rising to 43%
#: (n = 500) against a nominal 5%, and is *worst at large n* because the
#: interval narrows around a bias that never moves.
#:
#: `ratio_of_sums` looks clean here and is NOT the fix: the placebo that clears it
#: has exposure independent of talent, and at the corpus's measured coupling
#: (corr(log minutes, PIR/36) = +0.17 source, +0.36 destination) the 2026-08-17
#: study measured a +0.036 weight-mismatch bias — worse than the primary's. That
#: figure's generator is lost and it is quoted, not re-derived. The real-corpus
#: gap (expw − ros = −0.0044 across 22 cells) rejects the independent-exposure
#: model. None of the three is unbiased on realistic data; keeping the primary
#: is correct.
MEASURED_NULL = {
    "exposure_weighted": 1.0287,
    "ratio_of_sums": 0.9995,
    "mean_of_ratios": 1.0431,
}

#: Realised coverage of the nominal-95% cluster-bootstrap intervals, measured by
#: the same study (`summary_api.json: s1.pooled_coverage_95.mean` and
#: `s1.by_n_at_0.85.500.coverage_95.mean`; the Proballers template reads 0.74 /
#: 0.64). Published alongside the intervals because the parquet is what
#: consumers read; a "95%" label on 0.77 overstates them. Coverage *degrades*
#: with sample size for the reason above — that direction is the
#: counter-intuitive part and is why this cannot be phrased as a thin-cell caveat.
INTERVAL_CALIBRATION = {
    "nominal": 0.95,
    "realised_pooled": 0.77,
    "realised_at_n_500": 0.65,
    "source": (
        "ATI-2890 synthetic validation, re-run 2026-09-04: "
        "docs/research/artifacts/translation-estimator-synthetic-2026-09-04/"
        "summary_api.json"
    ),
}


def excludes_measured_null(ci_lo, ci_hi, *, estimator: str = PRIMARY):
    """Does the interval sit clear of where this estimator lands under no effect?

    Descriptive, not inferential. It reports that an interval excludes the
    estimator's measured null — it is **not** a significance test, and must not
    be narrated as one. Its predecessor `differs_from_parity` compared against
    1.0, which read as a test and was not one at the measured false-positive rate
    (ATI-2904).

    Renamed rather than redefined in place: a consumer reaching for the old name
    now gets a `KeyError`, where a same-named column with quietly moved meaning
    would have gone on returning a wrong answer in silence.
    """
    null = MEASURED_NULL[estimator]
    return (ci_hi < null) | (ci_lo > null)


#: The sample the headline factors and the external-validity checks both read.
#: Demoted from role_stable_5 to all_pairs on 2026-08-15 — see the block comment on
#: HEADLINE_SAMPLE in report_league_factors.py for the five reasons, and
#: role_stability_filter_test.json for the tests. Defined here so the estimator's
#: validity checks cannot silently validate a different sample than the note reports.
HEADLINE_SAMPLE = "all_pairs"


def cluster_bootstrap(
    sub: pd.DataFrame, stat: str, *, n_boot: int, rng: np.random.Generator
) -> tuple[float, float, float]:
    """Resample whole (season × destination club) clusters, not pairs.

    Israel's factor rests on two clubs' rotations and Lithuania's largely on
    one; a pair-level bootstrap treats those as independent observations and
    reports an SE that is too small on exactly the leagues a GM will ask about.
    """
    groups = [g.index.to_numpy() for _, g in sub.groupby("cluster", sort=False)]
    if len(groups) < 2:
        return float("nan"), float("nan"), float("nan")
    draws = np.empty(n_boot)
    for b in range(n_boot):
        picked = rng.integers(0, len(groups), len(groups))
        idx = np.concatenate([groups[i] for i in picked])
        draws[b] = ESTIMATORS[PRIMARY](sub.loc[idx], stat)
    draws = draws[np.isfinite(draws)]
    if draws.size < n_boot // 2:
        return float("nan"), float("nan"), float("nan")
    return (
        float(draws.std(ddof=1)),
        float(np.percentile(draws, 2.5)),
        float(np.percentile(draws, 97.5)),
    )


def pair_bootstrap_se(
    sub: pd.DataFrame, stat: str, *, n_boot: int, rng: np.random.Generator
) -> float:
    """The naive bootstrap, computed only to show how much it understates."""
    idx = sub.index.to_numpy()
    draws = np.array(
        [
            ESTIMATORS[PRIMARY](sub.loc[rng.choice(idx, idx.size, replace=True)], stat)
            for _ in range(n_boot)
        ]
    )
    draws = draws[np.isfinite(draws)]
    return float(draws.std(ddof=1)) if draws.size > 1 else float("nan")


def partial_pool(
    factors: np.ndarray, ses: np.ndarray
) -> tuple[np.ndarray, float, float]:
    """Empirical-Bayes shrinkage toward the destination-tier mean.

    7 of 16 league-pairs have fewer than 50 pairs. A thin league's raw factor is
    mostly noise, and shrinking it toward the tier mean in proportion to its own
    precision is what stops us quoting that noise as a league difference.
    Returns (pooled factors, grand mean, tau).
    """
    ok = np.isfinite(factors) & np.isfinite(ses) & (ses > 0)
    if ok.sum() < 2:
        return factors.copy(), float("nan"), float("nan")
    w0 = 1 / ses[ok] ** 2
    grand = float(np.sum(w0 * factors[ok]) / np.sum(w0))
    tau2 = max(0.0, float(np.var(factors[ok], ddof=1) - np.mean(ses[ok] ** 2)))
    pooled = factors.copy()
    shrink = tau2 / (tau2 + ses[ok] ** 2) if tau2 > 0 else np.zeros(int(ok.sum()))
    pooled[ok] = grand + shrink * (factors[ok] - grand)
    return pooled, grand, float(np.sqrt(tau2))


def pooled_collapsed(tau: float, ses: np.ndarray) -> np.ndarray:
    """Which rows lost their per-league dimension to complete shrinkage?

    `tau == 0` is a real fit outcome, not a crash: the between-league variance
    estimate went non-positive, so `shrink = 0` and every poolable league in the
    block is assigned the identical tier mean. The per-league column still
    *exists*, but it carries no per-league information, and `reliable = true`
    would actively vouch for that (ATI-2901).

    Returned per row so a consumer can branch on it, rather than having to
    re-derive `tau == 0` and re-check that the factors really are identical.
    Rows the pooler could not touch at all (non-finite or zero SE) keep their raw
    factor and are NOT collapsed — they are a different failure, already carried
    by `reliable` via the `isfinite(se)` term.
    """
    poolable = np.isfinite(ses) & (ses > 0)
    return poolable & bool(np.isfinite(tau) and tau == 0.0)


@dataclass(frozen=True)
class Sample:
    """A named pair-selection rule.

    The primary sample is one row among its own sensitivities, so a reader can
    see whether the headline depends on the cut.
    """

    name: str
    usage_cut: float | None

    def apply(self, pairs: pd.DataFrame) -> pd.DataFrame:
        if self.usage_cut is None:
            return pairs
        return pairs[
            (pairs.d_usage.abs() <= self.usage_cut)
            & (pairs.d_min_per_game.abs() <= self.usage_cut)
        ]


def cell_seed(
    seed: int,
    sample: str,
    era: str,
    dest: str,
    stat: str,
    source: str,
) -> int:
    """Derive a per-cell bootstrap seed that is stable ACROSS PROCESSES.

    This was `abs(hash((...))) % 2**32`. `hash()` on a tuple containing `str` is
    salted per interpreter process unless `PYTHONHASHSEED` is pinned, and it is
    pinned nowhere in this repo — so every run seeded every cell differently and
    `--seed` was inert.

    The damage was not confined to the intervals. `factor_raw` stayed
    deterministic, but partial pooling weights by the bootstrap SE, so the
    randomness propagated into the published `factor` and into the booleans
    derived from it. Measured across two runs at the same `--seed`: `se` moved on
    1,091 of 1,134 rows, `factor` on the same 1,091 (max 0.038 — wider than the
    +/-0.03 this analysis advertises), and **46 `differs_from_parity` (the column
    now called `excludes_measured_null`) plus 39 `load_bearing_estimator` verdicts
    flipped**. The headline PIR->EuroLeague
    cells were stable to <0.001, so the published table was never wrong; the
    reproducibility claim was.

    `crc32` over a stable `repr` is deterministic across processes, machines and
    Python versions, and stays in `[0, 2**32)` where the generator wants it.
    Pinned by `test_cell_seed_is_stable_across_processes`, which asserts a golden
    value computed in a *different* process — an in-process round-trip would pass
    on the buggy `hash()` too, since `hash()` is stable within one process.
    """
    return zlib.crc32(repr((seed, sample, era, dest, stat, source)).encode())


def estimate_table(
    pairs: pd.DataFrame,
    *,
    samples: list[Sample],
    min_pairs: int,
    n_boot: int,
    seed: int,
) -> pd.DataFrame:
    """Estimate every (source, destination, era, stat, sample) cell."""
    rows: list[dict] = []
    for sample in samples:
        selected = sample.apply(pairs)
        for era, (lo, hi) in ERAS.items():
            era_pairs = selected[(selected.season >= lo) & (selected.season <= hi)]
            for dest in CONTINENTAL:
                dest_pairs = era_pairs[era_pairs.league_dest == dest]
                for stat in STATS:
                    cells = []
                    for source, sub in dest_pairs.groupby("league_src"):
                        sub = sub.reset_index(drop=True)
                        # A fresh generator per cell keeps a cell's SE
                        # reproducible regardless of iteration order.
                        rng = np.random.default_rng(
                            cell_seed(seed, sample.name, era, dest, stat, source)
                        )
                        values = {
                            label: fn(sub, stat) for label, fn in ESTIMATORS.items()
                        }
                        se, lo_ci, hi_ci = cluster_bootstrap(
                            sub, stat, n_boot=n_boot, rng=rng
                        )
                        se_pair = pair_bootstrap_se(
                            sub, stat, n_boot=max(200, n_boot // 4), rng=rng
                        )
                        finite = [v for v in values.values() if np.isfinite(v)]
                        cells.append(
                            {
                                "league": source,
                                "destination": dest,
                                "era": era,
                                "stat": stat,
                                "sample": sample.name,
                                "factor_raw": values[PRIMARY],
                                "se": se,
                                "ci_lo": lo_ci,
                                "ci_hi": hi_ci,
                                "n_pairs": len(sub),
                                "n_clusters": sub.cluster.nunique(),
                                "n_seasons": sub.season.nunique(),
                                "n_clubs_src": sub.club_src.nunique(),
                                "top_cluster_share": float(
                                    sub.cluster.value_counts(normalize=True).iloc[0]
                                )
                                if len(sub)
                                else float("nan"),
                                "estimator_spread": (
                                    max(finite) - min(finite)
                                    if finite
                                    else float("nan")
                                ),
                                "se_ratio_pair_boot": (
                                    se_pair / se
                                    if np.isfinite(se)
                                    and se > 0
                                    and np.isfinite(se_pair)
                                    else float("nan")
                                ),
                                "method": f"{PRIMARY}+cluster_bootstrap_season_club",
                                **{f"est_{k}": v for k, v in values.items()},
                            }
                        )
                    if not cells:
                        continue
                    block = pd.DataFrame(cells)
                    pooled, grand, tau = partial_pool(
                        block.factor_raw.to_numpy(), block.se.to_numpy()
                    )
                    block["factor"] = pooled
                    block["tier_mean"] = grand
                    block["tau"] = tau
                    # tau == 0 collapses every poolable league onto one number.
                    # Such a row cannot support a per-league claim, so it must not
                    # be flagged reliable (ATI-2901).
                    block["pooled_collapsed"] = pooled_collapsed(
                        tau, block.se.to_numpy()
                    )
                    block["reliable"] = (
                        (block.n_pairs >= min_pairs)
                        & np.isfinite(block.se)
                        & ~block.pooled_collapsed
                    )
                    # An interval covering the estimator's measured null means
                    # "no measured league difference". Compared against
                    # MEASURED_NULL[PRIMARY], not 1.0 — see ATI-2904.
                    block["excludes_measured_null"] = excludes_measured_null(
                        block.ci_lo, block.ci_hi
                    )
                    block["load_bearing_estimator"] = block.estimator_spread > block.se
                    rows.extend(block.to_dict("records"))
    return pd.DataFrame(rows)


# ------------------------------------------------------------- regressions --
def external_validity(table: pd.DataFrame) -> dict:
    """Does the recovered ordering reproduce the consensus league hierarchy?

    Nothing in the estimator encodes a prior about European basketball, so this
    is a genuine check rather than a restatement of the input (spec §3). Two
    parts: rank agreement with `CONSENSUS_ORDER`, and the tier ordering — a
    source league should translate *better* into EuroCup than into EuroLeague,
    because EuroCup is the weaker destination.
    """
    from scipy.stats import spearmanr

    headline = table[
        (table["stat"] == "pir")
        & (table.era == "all")
        & (table["sample"] == HEADLINE_SAMPLE)
        & table.reliable
    ]
    el = headline[headline.destination == "euroleague"].set_index("league")
    ranked = [lg for lg in CONSENSUS_ORDER if lg in el.index]
    rho, p = (float("nan"), float("nan"))
    if len(ranked) >= 3:
        observed = [-el.loc[lg, "factor"] for lg in ranked]
        rho, p = spearmanr(range(len(ranked)), observed)

    # ATI-2903: CONSENSUS_ORDER is an external judgement, not something the data
    # can supply, so a league absent from it cannot be scored. That is tolerable;
    # scoring it SILENTLY is not. Until 2026-08-18 the tuple held 8 leagues
    # against an 11-league corpus, and rho was identical to twelve decimals
    # before and after the corpus grew by 1,383 player-seasons -- not the method
    # proving robust, just the same leagues scored twice. Emit what was left out
    # and how many were compared, so a future corpus change cannot move the
    # comparison set without moving a visible number.
    unscored = sorted(set(el.index) - set(CONSENSUS_ORDER))

    ec = headline[headline.destination == "eurocup"].set_index("league")
    shared = sorted(set(el.index) & set(ec.index))
    ec_higher = sum(ec.loc[lg, "factor"] > el.loc[lg, "factor"] for lg in shared)
    return {
        "consensus_leagues_ranked": ranked,
        "n_leagues_compared": len(ranked),
        "n_leagues_available": int(el.index.nunique()),
        "leagues_without_consensus_position": unscored,
        "consensus_coverage_note": (
            "rho scores only the leagues with a committed consensus position; it "
            "is silent about the rest. Do NOT cite rho holding across a corpus "
            "change as evidence the method survived it (ATI-2903)."
        )
        if unscored
        else "",
        "spearman_rho_vs_consensus": float(rho),
        "spearman_p": float(p),
        "eurocup_above_euroleague": f"{ec_higher}/{len(shared)}",
        "shared_source_leagues": shared,
        "interval_calibration": INTERVAL_CALIBRATION,
        "measured_null": MEASURED_NULL[PRIMARY],
    }


def sample_size_table(pairs: pd.DataFrame) -> pd.DataFrame:
    """Per (source, destination, season) counts — the reconstructable sample."""
    return (
        pairs.groupby(["league_src", "league_dest", "season"])
        .agg(
            n_pairs=("player_name", "size"),
            n_clusters=("cluster", "nunique"),
            n_src_clubs=("club_src", "nunique"),
            top_dest_club_share=(
                "club_dest",
                lambda s: float(s.value_counts(normalize=True).iloc[0]),
            ),
            median_games_src=("games_src", "median"),
            median_games_dest=("games_dest", "median"),
        )
        .reset_index()
        .rename(columns={"league_src": "league", "league_dest": "destination"})
    )


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--min-games", type=int, default=8)
    # 75, not 50. Subsampling the one well-populated cell (ACB, n=506) against its
    # own full-sample value shows the p90 absolute error is 0.038 at n=50 — wider
    # than the +/-0.03 the note claims a factor is good to — and 0.029 at n=75.
    # The threshold has to match the precision actually being advertised.
    # Those two figures are the 2026-08-15 measurement that set this default. The
    # live curve is recomputed every run and published as `p90_err` in the checks
    # JSON, which is what the note reads — cite that, not a side artifact. An
    # earlier revision pointed readers at a power-analysis file that has never
    # been written, which reads as "derived and checkable" and goes nowhere
    # (ATI-2905). A test pins that the dead name stays gone.
    ap.add_argument("--min-pairs", type=int, default=75)
    ap.add_argument("--n-boot", type=int, default=2000)
    # Pin the corpus to a reproducible subset. Needed because ATI-2895 is scraping
    # italy-lba/germany-bbl/greece-a1 right now: a note generated against a corpus
    # that is still growing cannot be reproduced later, which is precisely the
    # ATI-2827 failure this script exists to fix. Excluding the in-flight leagues
    # gives a baseline that reproduces both today and after the scrape lands.
    ap.add_argument(
        "--exclude-leagues",
        nargs="*",
        default=[],
        metavar="LEAGUE",
        help="source leagues to drop before pairing (e.g. leagues mid-scrape)",
    )
    ap.add_argument("--usage-cut", type=float, default=5.0)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--out-dir", type=Path, default=_OUT_DIR)
    ap.add_argument(
        "--continental-source",
        choices=CONTINENTAL_SOURCES,
        default=DEFAULT_CONTINENTAL_SOURCE,
        help="where the EuroLeague/EuroCup side of every pair is read from "
        "(Amendment 4: api). `proballers` reproduces the pre-2026-09-03 corpus.",
    )
    args = ap.parse_args()

    raw = load_player_games(args.continental_source)
    n_2015_rows = int(raw.attrs.get("n_domestic_rows_before_api_seasons", 0))
    games = add_usage(raw)
    if args.exclude_leagues:
        before = len(games)
        games = games[~games.league.isin(args.exclude_leagues)].reset_index(drop=True)
        logger.info(
            "excluded %s: %d -> %d player-games",
            ", ".join(args.exclude_leagues),
            before,
            len(games),
        )
    pairs = build_pairs(games, min_games=args.min_games)
    logger.info(
        "pairs: %d across %d source leagues x %d destinations, seasons %d-%d",
        len(pairs),
        pairs.league_src.nunique(),
        pairs.league_dest.nunique(),
        pairs.season.min(),
        pairs.season.max(),
    )
    # Amendment 4: the API holds no 2015-16, so no pair can have a 2015
    # destination season. How many the Proballers-side table had is a fact
    # about the OTHER table; `scripts/compare_factor_tables.py` reads both
    # pair parquets and states it.

    samples = [
        Sample(f"role_stable_{int(args.usage_cut)}", args.usage_cut),
        Sample("role_stable_3", 3.0),
        Sample("role_stable_7", 7.0),
        Sample("all_pairs", None),
    ]
    table = estimate_table(
        pairs,
        samples=samples,
        min_pairs=args.min_pairs,
        n_boot=args.n_boot,
        seed=args.seed,
    )

    out = args.out_dir
    out.mkdir(parents=True, exist_ok=True)
    cols = [
        "league",
        "destination",
        "era",
        "stat",
        "sample",
        "factor",
        "se",
        "ci_lo",
        "ci_hi",
        "n_pairs",
        "n_clusters",
        "n_seasons",
        "n_clubs_src",
        "top_cluster_share",
        "reliable",
        "pooled_collapsed",
        "excludes_measured_null",
        "factor_raw",
        "tier_mean",
        "tau",
        "estimator_spread",
        "load_bearing_estimator",
        "se_ratio_pair_boot",
        "method",
        *[f"est_{k}" for k in ESTIMATORS],
    ]
    table[cols].to_parquet(out / "league_factors.parquet", index=False)
    sample_size_table(pairs).to_parquet(
        out / "league_factor_sample_sizes.parquet", index=False
    )
    pairs.to_parquet(out / "league_factor_pairs.parquet", index=False)

    checks = external_validity(table)
    (out / "league_factors_checks.json").write_text(
        json.dumps(
            {
                "generated_at": datetime.datetime.now(datetime.timezone.utc)
                .replace(microsecond=0)
                .isoformat(),
                "external_validity": checks,
                "config": {
                    "min_games": args.min_games,
                    "min_pairs": args.min_pairs,
                    "n_boot": args.n_boot,
                    "usage_cut": args.usage_cut,
                    "seed": args.seed,
                    "primary_estimator": PRIMARY,
                    "not_a_source": list(NOT_A_SOURCE),
                    "pir_rule": "pir used directly; no coalesce (ATI-2826)",
                    "headline_sample": HEADLINE_SAMPLE,
                    "excluded_leagues": list(args.exclude_leagues),
                    # Amendment 4 (ATI-2957): which corpus the destination side
                    # came from. A consumer that cannot tell the two tables
                    # apart would compare a factor against its own SE from the
                    # other source.
                    "continental_source": args.continental_source,
                },
                "continental_side": {
                    "source": args.continental_source,
                    "api": raw.attrs.get("api_report"),
                    "n_domestic_player_games_before_api_seasons": n_2015_rows,
                    "first_api_season": min(API_SEASONS),
                    "excluded_sources": raw.attrs.get("api_side_excluded_sources", []),
                    "n_player_games_excluded": raw.attrs.get(
                        "n_player_games_excluded_api_side", 0
                    ),
                },
                # The corpus actually fitted on, AFTER any --exclude-leagues.
                # Recorded here rather than typed into the note: the note's
                # Specification block hardcoded "531,106 player-games" while the
                # two raw trees had already grown to 535,662 (ATI-2895 scraping
                # italy-lba), so the block described a filtered corpus as if it
                # were the unfiltered glob and gave no way to tell.
                "n_player_games": int(len(games)),
                "n_pairs": int(len(pairs)),
                "n_rows": int(len(table)),
                # ATI-2901: tau == 0 blocks lose their per-league dimension.
                # Counted here so the collapse is a fact in the artifact rather
                # than a warning someone has to have been watching for.
                "pooling": {
                    "n_rows_collapsed": int(table.pooled_collapsed.sum()),
                    "collapsed_stats": sorted(
                        table.loc[table.pooled_collapsed, "stat"].unique().tolist()
                    ),
                    "n_reliable": int(table.reliable.sum()),
                },
            },
            indent=2,
        )
    )
    logger.info(
        "external validity: spearman rho=%.3f on %d of %d source leagues, "
        "EuroCup above EuroLeague on %s source leagues",
        checks["spearman_rho_vs_consensus"],
        checks["n_leagues_compared"],
        checks["n_leagues_available"],
        checks["eurocup_above_euroleague"],
    )
    if checks["leagues_without_consensus_position"]:
        logger.warning(
            "external validity is SILENT about %d source league(s) with no "
            "committed consensus position: %s. rho=%.3f scores %d of %d leagues "
            "-- do not read it as covering the full corpus (ATI-2903).",
            len(checks["leagues_without_consensus_position"]),
            ", ".join(checks["leagues_without_consensus_position"]),
            checks["spearman_rho_vs_consensus"],
            checks["n_leagues_compared"],
            checks["n_leagues_available"],
        )
    n_collapsed = int(table.pooled_collapsed.sum())
    if n_collapsed:
        logger.warning(
            "partial pooling collapsed %d of %d rows onto the tier mean "
            "(tau == 0); all are flagged reliable=false (ATI-2901). Affected "
            "stats: %s",
            n_collapsed,
            len(table),
            ", ".join(sorted(table.loc[table.pooled_collapsed, "stat"].unique())),
        )
    logger.info("wrote %d rows → %s", len(table), out / "league_factors.parquet")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
