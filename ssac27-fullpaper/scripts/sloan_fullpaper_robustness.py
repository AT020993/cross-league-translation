#!/usr/bin/env python3
"""Robustness track of the SSAC27 full-paper pre-registration (E3, E4, E5, E5b, E6).

Pre-registration: docs/research/sloan-full-paper-preregistration-2026-11-03.md
(commit f52e7c831, pushed 2026-11-03T09:15:02Z). All analyses here are
EXPLORATORY: destination seasons 2017-2025 were already inspected.

* E3 rebuilds the whole v10 pipeline (pair rates, factors, lag, history h,
  above-flag a, all 17 arms) for points/36, Game Score/36 and EFF per 100
  on-court possessions. Gate G3 first: the rebuilt EFF history must equal the
  cohort's ``prior_mean_pir36`` on all 1,371 rows to 1e-9.
* E4 scores the ladder and the E1 head-to-head separately for EuroLeague and
  EuroCup (anchor 194/480, extended 218/594) with a two-sided destination
  difference test of the lambda-10 increment.
* E5 extends evaluation to 2019-2025 (812 forecasts), with per-season direction
  counts and leave-one-evaluation-season-out ranges.
* E5b adds (age - 26) and (age - 26)^2, unpenalised, to every arm through new
  fitting code that wraps the v10 model matrices (v10 files are not edited).
* E6 splits each target's destination games into odd/even appearances in date
  order and derives split-half reliability and the noise-floor MAE.

Threats: history rebuild drift (G3 exact gate with negative control); 2026-27
leakage (only the frozen 2015-2025 raw inventory is read, sha-checked);
dropped targets (every target is joined 1:1; an unscorable target is reported
as inconclusive); identity mismatches (repo identity rules, join rates
asserted); gates that cannot fail (impossible-threshold negative controls).
"""

# ruff: noqa: E501 -- gate messages and labels
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

for _name in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_name, "1")
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from scipy.stats import t as student_t  # noqa: E402

from scripts import adjudicate_sloan_acb_sources as acb  # noqa: E402
from scripts import sloan_context_benchmarks as benchmark  # noqa: E402
from scripts import sloan_corrected_sources as corrected  # noqa: E402
from scripts import sloan_fullpaper_common as common  # noqa: E402
from scripts import sloan_revision_analysis as revision  # noqa: E402
from scripts import sloan_source_adjudication as adjudication  # noqa: E402
from scripts import validate_translation_holdout as holdout  # noqa: E402
from scripts import validate_translation_v2 as identity  # noqa: E402
from scripts.translation_research_common import sha256_file  # noqa: E402
from src.data.corpus.euroleague_api import drop_non_player_rows  # noqa: E402

KEY = common.KEY
G3_TOLERANCE = 1e-9
AGE_CENTRE = 26.0
AGE_COVERAGE_GATE = 0.95
MARGIN_SHARE = 0.02
N_BOOT = 2000
SEED = 0
RAW_SEASONS = tuple(range(2015, 2026))
API_SEASONS = tuple(range(2016, 2026))
E6_SEASONS = tuple(range(2020, 2026))
CONTINENTAL = ("euroleague", "eurocup")

#: Outcome code -> (label, numerator, exposure, scale). Rate = scale * num / exposure.
OUTCOMES = {
    "O1": ("EFF/36 (v10)", "eff", "minutes", 36.0),
    "O2": ("points/36", "pts", "minutes", 36.0),
    "O3": ("Game Score/36 (Hollinger)", "game_score", "minutes", 36.0),
    "O4": ("EFF per 100 on-court possessions", "eff", "oncourt", 100.0),
}

#: Primary and printed contrasts: name -> (left, right); positive favours right.
CONTRASTS = {
    "history_gain": ("history_only", "scheduled_history"),
    "destination_increment": (
        "history_destination_slope",
        "history_destination_slope_scheduled",
    ),
    **{
        f"offsets{p}_increment": (f"source_ridge_{p}", f"source_ridge_{p}_scheduled")
        for p in common.PENALTIES
    },
    **{
        f"cell_slopes{p}_increment": (f"cell_slope_{p}", f"cell_slope_{p}_scheduled")
        for p in common.PENALTIES
    },
    "e1_head_to_head": ("scheduled_history", "source_ridge_10"),
}
PRIMARY_CONTRASTS = ("history_gain", "offsets10_increment", "e1_head_to_head")


# --------------------------------------------------------------- components --
def components(frame: pd.DataFrame, suffix: str = "") -> dict[str, pd.Series]:
    """Numerators and exposures from aggregate columns (``fga2``/``fgm2`` are 2PT only)."""

    def c(name):
        return frame[f"{name}{suffix}"].astype(float)

    fgm = c("fgm2") + c("fg3m")
    fga = c("fga2") + c("fg3a")
    game_score = (
        c("pts")
        + 0.4 * fgm
        - 0.7 * fga
        - 0.4 * (c("fta") - c("ftm"))
        + 0.7 * c("oreb")
        + 0.3 * c("dreb")
        + c("stl")
        + 0.7 * c("ast")
        + 0.7 * c("blk")
        - 0.4 * c("pf")
        - c("tov")
    )
    return {
        "eff": c("pir"),
        "pts": c("pts"),
        "game_score": game_score,
        "minutes": c("minutes"),
        "oncourt": c("team_poss") * c("minutes") / (c("team_minutes") / 5.0),
    }


def outcome_rate(frame: pd.DataFrame, outcome: str, suffix: str = "") -> pd.Series:
    _, numerator, exposure, scale = OUTCOMES[outcome]
    parts = components(frame, suffix)
    return scale * parts[numerator] / parts[exposure]


# ------------------------------------------------------------ corpus rebuild --
def frozen_inventory() -> dict:
    return json.loads((acb.SOURCE / "preparation_manifest.json").read_text())


def _relative_raw(path: str) -> str:
    text = Path(path).as_posix()
    if "/data/raw/" not in text:
        raise common.GateFailure(f"not a raw corpus path: {path}")
    return text.split("/data/raw/", 1)[1]


def rebuild_games(raw_root: Path):
    """Canonical player-games through the official_corrected identity rules.

    Reads exactly the frozen 2015-2025 raw inventory of the source revalidation
    manifest (sha-checked); the 2025 ACB field decisions are not applied because
    they touch only destination-2026 history. G3 tests the consequence.
    """
    raw_root = Path(raw_root).resolve()
    if raw_root != (ROOT / "data/raw").resolve():
        raise common.GateFailure(
            "raw root must be the checkout's data/raw (API loader reads ROOT)"
        )
    prep = frozen_inventory()
    raw, inventory = adjudication.load_raw(raw_root)
    got = {_relative_raw(r["source_file"]): r["sha256"] for r in inventory}
    want = {_relative_raw(r["source_file"]): r["sha256"] for r in prep["raw_inputs"]}
    if got != want:
        raise common.GateFailure(
            "raw domestic inventory differs from the frozen 2015-2025 manifest"
        )
    for record in prep["api_inputs"]:
        path = raw_root / _relative_raw(record["source_file"])
        if sha256_file(path) != record["sha256"]:
            raise common.GateFailure(f"API box score changed: {path}")
    seasons = sorted(int(s) for s in raw.season.unique())
    if any(s not in RAW_SEASONS for s in seasons):
        raise common.GateFailure(f"raw seasons outside 2015-2025: {seasons}")
    diagnosis = json.loads((acb.SOURCE / "source_diagnosis.json").read_text())
    evidence = json.loads((acb.SOURCE / "official_minute_evidence.json").read_text())
    # The evidence names its raw file by an absolute path in the primary checkout;
    # point it at the same relative file under raw_root (same bytes, sha checked).
    evidence_file = raw_root / _relative_raw(evidence["raw_source_file"])
    if want.get(_relative_raw(evidence["raw_source_file"])) != evidence["raw_sha256"]:
        raise common.GateFailure(
            "minute evidence names a file outside the frozen inventory"
        )
    evidence = {**evidence, "raw_source_file": str(evidence_file.resolve())}
    repaired, _ = adjudication._repair_minutes(
        adjudication._prepare(raw), diagnosis, evidence
    )
    repaired["official_person_id"] = pd.Series(
        None, index=repaired.index, dtype="object"
    )
    repaired["identity_status"] = "NAME_ONLY_UNVERIFIED"
    repaired = repaired.loc[~repaired.duplicated(adjudication.TEAM_KEY)].copy()
    scopes = corrected.collision_scopes(diagnosis, ())
    previous_level = logging.root.manager.disable
    logging.disable(logging.WARNING)
    try:
        games, excluded = corrected.normalize_games(repaired, scopes)
    finally:
        logging.disable(previous_level)
    if games.season.max() > max(RAW_SEASONS):
        raise common.GateFailure("a season after 2025 entered the rebuilt corpus")
    with contextlib.redirect_stdout(io.StringIO()):
        _, agg = holdout.build_switchers(games)
    return (
        games,
        agg,
        {
            "raw_rows": len(raw),
            "canonical_games": len(games),
            "identity_excluded": len(excluded),
            "aggregate_rows": len(agg),
            "seasons": seasons,
            "frozen_raw_files": len(want),
            "frozen_api_files": len(prep["api_inputs"]),
        },
    )


def history(agg: pd.DataFrame, outcome: str) -> pd.DataFrame:
    """v10's prior_mean_pir36 rule for any outcome: pooled rate over all earlier seasons."""
    _, numerator, exposure, scale = OUTCOMES[outcome]
    parts = components(agg)
    frame = pd.DataFrame(
        {
            "player_name": agg.player_name,
            "season": agg.season,
            "num": parts[numerator],
            "exp": parts[exposure],
        }
    ).loc[agg.minutes.gt(0)]
    hist = (
        frame.groupby(["player_name", "season"])[["num", "exp"]]
        .sum()
        .sort_index()
        .reset_index()
    )
    hist[["cum_num", "cum_exp"]] = hist.groupby("player_name")[["num", "exp"]].cumsum()
    hist["prior"] = np.where(
        hist.cum_exp > hist.exp,
        scale * (hist.cum_num - hist.num) / (hist.cum_exp - hist.exp),
        np.nan,
    )
    return hist[["player_name", "season", "prior"]]


def attach_history(cohort: pd.DataFrame, hist: pd.DataFrame) -> pd.Series:
    merged = cohort[["player_name", "season_src"]].merge(
        hist.rename(columns={"season": "season_src"}),
        on=["player_name", "season_src"],
        how="left",
        validate="m:1",
    )
    if len(merged) != len(cohort):
        raise common.GateFailure("history join changed the cohort row count")
    return merged.prior.to_numpy(dtype=float)


def g3_difference(cohort: pd.DataFrame, rebuilt: np.ndarray) -> dict:
    stored = cohort.prior_mean_pir36.to_numpy(dtype=float)
    nan_mismatch = int((np.isnan(stored) != np.isnan(rebuilt)).sum())
    both = ~np.isnan(stored) & ~np.isnan(rebuilt)
    worst = float(np.max(np.abs(stored[both] - rebuilt[both]))) if both.any() else 0.0
    return {
        "rows": len(cohort),
        "nan_rows": int(np.isnan(stored).sum()),
        "nan_pattern_mismatches": nan_mismatch,
        "max_abs_difference": worst,
    }


def assert_g3(diff: dict, tolerance: float = G3_TOLERANCE) -> None:
    if (
        diff["rows"] != 1371
        or diff["nan_pattern_mismatches"]
        or not diff["max_abs_difference"] <= tolerance
    ):
        raise common.GateFailure(f"G3 failed: {diff} (tolerance {tolerance:.0e})")


def outcome_inputs(pairs, cohort, hist, outcome):
    """Copies of the v10 inputs with the outcome's rates in the pipeline's columns."""
    p, c = pairs.copy(), cohort.copy()
    for frame in (p, c):
        for side in ("src", "dest"):
            rate = outcome_rate(frame, outcome, f"_{side}").to_numpy(dtype=float)
            if not np.isfinite(rate).all():
                raise common.GateFailure(f"{outcome}: nonfinite {side} rate")
            frame[f"pir_per36_{side}"] = rate
            # Keep ratio-of-sums inputs consistent with the substituted rate.
            frame[f"pir_{side}"] = rate * frame[f"minutes_{side}"].astype(float) / 36.0
    prior = attach_history(c, hist)
    c["prior_mean_pir36"] = prior
    c["above_own_prior"] = c.pir_per36_src.to_numpy() > prior
    return p, c


# ------------------------------------------------------------------ metrics --
def arm_metrics(rows: pd.DataFrame, arm: str) -> dict:
    error = (rows[arm] - rows.pir_per36_dest).to_numpy(dtype=float)
    absolute = np.abs(error)
    return {
        "n": len(rows),
        "mae": float(absolute.mean()),
        "rmse": float(np.sqrt(np.mean(error**2))),
        "median_ae": float(np.median(absolute)),
        "p90_ae": float(np.quantile(absolute, 0.9)),
        "bias": float(error.mean()),
    }


def ladder(rows: pd.DataFrame) -> dict:
    return {arm: arm_metrics(rows, arm) for arm in common.ALL_ARMS}


def interval_summary(result: dict) -> dict:
    out = {
        "status": result["status"],
        "ci95": result.get("ci95"),
        "degrees_of_freedom": result.get("degrees_of_freedom"),
        "se": float(np.sqrt(result["variance"]))
        if result.get("variance") and result["variance"] > 0
        else None,
    }
    if out["se"] is not None:
        df = out["degrees_of_freedom"]
        out["mde80"] = float(
            (student_t.ppf(0.975, df) + student_t.ppf(0.80, df)) * out["se"]
        )
    else:
        out["mde80"] = None
    return out


def contrast_record(rows: pd.DataFrame, left: str, right: str, sd: float) -> dict:
    result = common.contrast(rows, left, right)
    difference = result["player_club_season"]["difference"]
    parent = float(np.mean(np.abs(rows[left] - rows.pir_per36_dest)))
    d = np.abs(rows[left] - rows.pir_per36_dest) - np.abs(
        rows[right] - rows.pir_per36_dest
    )
    seasons = {
        str(int(s)): float(d.loc[g.index].mean())
        for s, g in rows.groupby("season_dest", sort=True)
    }
    loso = {k: v for k, v in result["leave_one_season_out"].items() if v is not None}
    record = {
        "left": left,
        "right": right,
        "positive_favours": right,
        "n": len(rows),
        "difference": difference,
        "mae_left": parent,
        "mae_right": float(np.mean(np.abs(rows[right] - rows.pir_per36_dest))),
        "pct_of_parent_mae": 100.0 * difference / parent,
        "outcome_sd_units": difference / sd,
        "player_club_season": interval_summary(result["player_club_season"]),
        "player_season": interval_summary(result["player_season"]),
        "equal_season_difference": result["equal_season_difference"],
        "season_difference": seasons,
        "positive_seasons": int(sum(v > 0 for v in seasons.values())),
        "n_seasons": len(seasons),
        "leave_one_season_out": loso,
        "loso_range": [min(loso.values()), max(loso.values())] if len(loso) else None,
        "sd_paired_difference": float(d.std(ddof=1)),
    }
    for spec in ("player_club_season", "player_season"):
        ci = record[spec]["ci95"]
        record[spec]["upper_pct_of_parent_mae"] = (
            None if ci is None else 100.0 * ci[1] / parent
        )
        record[spec]["lower_pct_of_parent_mae"] = (
            None if ci is None else 100.0 * ci[0] / parent
        )
        record[spec]["verdict"] = (
            "not_estimable"
            if ci is None
            else "above_zero"
            if ci[0] > 0
            else "below_zero"
            if ci[1] < 0
            else "spans_zero"
        )
    return record


def contrasts(rows: pd.DataFrame, sd: float) -> dict:
    return {name: contrast_record(rows, *pair, sd) for name, pair in CONTRASTS.items()}


def recovered_share(
    rows: pd.DataFrame, *, n_boot: int = N_BOOT, seed: int = SEED
) -> dict:
    """S = [MAE(h) - MAE(offsets10)] / [MAE(h) - MAE(h + z)], destination club-season bootstrap."""
    errors = {
        arm: np.abs(rows[arm] - rows.pir_per36_dest).to_numpy(dtype=float)
        for arm in ("history_only", "source_ridge_10", "scheduled_history")
    }
    codes, clusters = pd.factorize(rows.cluster, sort=False)
    sums = {
        a: np.bincount(codes, weights=e, minlength=len(clusters))
        for a, e in errors.items()
    }
    point = (errors["history_only"].sum() - errors["source_ridge_10"].sum()) / (
        errors["history_only"].sum() - errors["scheduled_history"].sum()
    )
    rng = np.random.default_rng(seed)
    draws = np.empty(n_boot)
    denominators = np.empty(n_boot)
    for start in range(0, n_boot, 250):
        stop = min(start + 250, n_boot)
        picked = rng.integers(0, len(clusters), (stop - start, len(clusters)))
        h = sums["history_only"][picked].sum(axis=1)
        r = sums["source_ridge_10"][picked].sum(axis=1)
        z = sums["scheduled_history"][picked].sum(axis=1)
        denominators[start:stop] = h - z
        with np.errstate(divide="ignore", invalid="ignore"):
            draws[start:stop] = (h - r) / (h - z)
    finite = np.isfinite(draws)
    return {
        "point": float(point),
        "ci95_percentile": [
            float(np.quantile(draws[finite], 0.025)),
            float(np.quantile(draws[finite], 0.975)),
        ],
        "share_draws_at_least_1": float(np.mean(draws[finite] >= 1.0)),
        "draws_nonpositive_denominator": int((denominators <= 0).sum()),
        "clusters": len(clusters),
        "n_boot": n_boot,
        "seed": seed,
    }


def destination_difference(rows: pd.DataFrame, left: str, right: str) -> dict:
    """Two-sided test of EuroLeague minus EuroCup paired difference, cluster-robust."""
    d = (
        np.abs(rows[left] - rows.pir_per36_dest)
        - np.abs(rows[right] - rows.pir_per36_dest)
    ).to_numpy(dtype=float)
    el = rows.league_dest.eq("euroleague").to_numpy()
    n, n1, n0 = len(d), int(el.sum()), int((~el).sum())
    m1, m0 = float(d[el].mean()), float(d[~el].mean())
    delta = m1 - m0
    u = delta + n * np.where(el, (d - m1) / n1, -(d - m0) / n0)
    out = {
        "left": left,
        "right": right,
        "euroleague": m1,
        "eurocup": m0,
        "difference_el_minus_ec": delta,
        "n_el": n1,
        "n_ec": n0,
    }
    for spec, second in (
        ("player_club_season", rows.cluster),
        ("player_season", rows.season_dest),
    ):
        res = revision.multiway_interval(u, rows.player_name, second)
        summary = interval_summary(res)
        if summary["se"]:
            stat = delta / summary["se"]
            summary["t"] = float(stat)
            summary["p_two_sided"] = float(
                2 * student_t.sf(abs(stat), summary["degrees_of_freedom"])
            )
        out[spec] = summary
    return out


def evaluate(
    rows: pd.DataFrame, *, sd: float | None = None, share: bool = True
) -> dict:
    sd = float(rows.pir_per36_dest.std(ddof=1)) if sd is None else sd
    out = {
        "n": len(rows),
        "by_destination_n": rows.league_dest.value_counts().sort_index().to_dict(),
        "by_season_n": {
            str(int(k)): int(v)
            for k, v in rows.season_dest.value_counts().sort_index().items()
        },
        "outcome_sd": sd,
        "ladder": ladder(rows),
        "contrasts": contrasts(rows, sd),
    }
    if share:
        out["e1_recovered_share"] = recovered_share(rows)
    return out


# ------------------------------------------------------- age-aware arm fits --
def _arm_parts(arm: str):
    if arm in common.SLOPE_ARMS:
        return (
            arm.replace("cell_slope_", "source_ridge_", 1),
            int(arm.split("_")[2]),
            True,
        )
    if arm.startswith("source_ridge_"):
        return arm, int(arm.split("_")[2]), False
    return arm, None, False


def fit_covariate_arm(train, test, arm, covariates=()):
    """v10 arm with extra unpenalised covariates appended to the v10 model matrix.

    With ``covariates=()`` this reproduces sloan_context_benchmarks.fit_model and
    sloan_v10_slopes.fit_model (tested); only the design columns are extended.
    """
    parent, penalty, slopes = _arm_parts(arm)
    x, _ = benchmark.model_matrix(train, parent)
    z, _ = benchmark.model_matrix(test, parent)
    if covariates:
        x = np.column_stack([x, train[list(covariates)].to_numpy(dtype=float)])
        z = np.column_stack([z, test[list(covariates)].to_numpy(dtype=float)])
    if not np.isfinite(x).all() or not np.isfinite(z).all():
        raise ValueError("nonfinite model input")
    rank = int(np.linalg.matrix_rank(x)) if len(x) else 0
    if len(train) < x.shape[1] or rank != x.shape[1]:
        return np.full(len(test), np.nan), "insufficient_training" if len(
            train
        ) < x.shape[1] else "rank_deficient"
    outcome = train.pir_per36_dest.to_numpy(dtype=float)
    if penalty is None:
        return z @ np.linalg.lstsq(x, outcome, rcond=None)[0], "ok"
    categories = sorted(train.league_src.unique())

    def penalised(rows, scale=None, cells=()):
        cols = [rows.league_src.eq(c).to_numpy(float) for c in categories]
        cols.extend(
            (rows.league_src.eq(s) & rows.league_dest.eq(d)).to_numpy(float)
            * rows.pir_per36_src.to_numpy(float)
            / scale
            for s, d in cells
        )
        return np.column_stack(cols)

    if slopes:
        scale = float(train.pir_per36_src.to_numpy(float).std(ddof=0))
        if not np.isfinite(scale) or scale <= 0:
            return np.full(len(test), np.nan), "invalid_training_scale"
        cells = sorted(set(zip(train.league_src, train.league_dest)))
        c_train, c_test = penalised(train, scale, cells), penalised(test, scale, cells)
    else:
        c_train, c_test = penalised(train), penalised(test)
    n_base = x.shape[1]
    x, z = np.column_stack([x, c_train]), np.column_stack([z, c_test])
    regulariser = np.zeros((c_train.shape[1], x.shape[1]))
    regulariser[:, n_base:] = np.sqrt(penalty) * np.eye(c_train.shape[1])
    beta = np.linalg.lstsq(
        np.vstack([x, regulariser]),
        np.r_[outcome, np.zeros(c_train.shape[1])],
        rcond=None,
    )[0]
    return z @ beta, "ok"


def covariate_forecast(
    features, covariates=(), seasons=common.ANCHOR_SEASONS, *, impute_test_at=None
):
    """Chronological forecasts for all 17 arms; rows lacking a covariate never train.

    A test row lacking a covariate is refused, unless ``impute_test_at`` is given,
    in which case its missing covariates are set to that value for prediction only.
    """
    has = (
        np.isfinite(features[list(covariates)]).all(axis=1)
        if covariates
        else pd.Series(True, index=features.index)
    )
    out, training = [], {}
    for season in seasons:
        train = features.loc[
            features.season_dest.lt(season) & features.feature_eligible & has
        ].sort_values(KEY)
        test = features.loc[features.season_dest.eq(season)].sort_values(KEY).copy()
        test_has = has.loc[test.index]
        if impute_test_at is not None and covariates:
            test[list(covariates)] = test[list(covariates)].fillna(impute_test_at)
            test_has = pd.Series(True, index=test.index)
        support = test.feature_eligible & test_has
        training[str(season)] = {
            "train_rows": len(train),
            "train_rows_without_covariate": int(
                (
                    features.season_dest.lt(season) & features.feature_eligible & ~has
                ).sum()
            ),
        }
        for arm in common.ALL_ARMS:
            test[arm] = np.nan
            test[f"{arm}_cov_status"] = "covariate_or_feature_refusal"
            if support.any():
                prediction, status = fit_covariate_arm(
                    train, test.loc[support], arm, covariates
                )
                test.loc[support, arm] = prediction
                test.loc[support, f"{arm}_cov_status"] = status
        out.append(test)
    return pd.concat(out, ignore_index=True), training


def assert_age_coverage(coverage: float, threshold: float = AGE_COVERAGE_GATE) -> None:
    if not coverage >= threshold:
        raise common.GateFailure(f"E5b birthdate coverage {coverage:.4f} < {threshold}")


# ------------------------------------------------------------- identities --
def api_raw(raw_root: Path, seasons=API_SEASONS) -> pd.DataFrame:
    frames = []
    for league in CONTINENTAL:
        for season in seasons:
            path = (
                Path(raw_root)
                / league
                / str(season)
                / "boxscores"
                / f"season_{season}_boxscores.parquet"
            )
            frame = pd.read_parquet(path)
            frame["league"] = league
            frames.append(frame)
    return drop_non_player_rows(pd.concat(frames, ignore_index=True))


def ages(cohort: pd.DataFrame, raw_root: Path, bio: pd.DataFrame) -> pd.DataFrame:
    """Age at 1 Oct of the destination season via the repo's v2 identity rules."""
    person_map, collisions = identity.api_person_map(api_raw(raw_root))
    names = identity.name_fallback_map(bio)
    rows = identity.attach_identity(
        cohort[[*KEY, "league_dest", "club_dest"]], person_map, collisions, names
    )
    births = bio.drop_duplicates("person_code").set_index("person_code").birth_date
    birth = pd.to_datetime(rows.person_code.map(births.to_dict()), errors="coerce")
    reference = pd.to_datetime(rows.season_dest.astype(int).astype(str) + "-10-01")
    rows["birth_date"] = birth.dt.strftime("%Y-%m-%d")
    rows["age"] = (reference - birth).dt.days / 365.25
    rows["age_c26"] = rows.age - AGE_CENTRE
    rows["age_c26_sq"] = rows.age_c26**2
    return rows


# ------------------------------------------------------------ split halves --
def load_game_dates(raw_root: Path, seasons=E6_SEASONS) -> pd.DataFrame:
    frames = []
    for league in CONTINENTAL:
        for season in seasons:
            path = (
                Path(raw_root)
                / league
                / str(season)
                / "games"
                / f"season_{season}_games.parquet"
            )
            frame = pd.read_parquet(path, columns=["gameCode", "date", "time"])
            frame["game_id"] = f"api-{league}-{season}-" + frame.gameCode.astype(
                int
            ).astype(str)
            frames.append(frame)
    dates = pd.concat(frames, ignore_index=True)
    if dates.game_id.duplicated().any():
        raise common.GateFailure("duplicate game codes in the schedule files")
    dates["when"] = pd.to_datetime(
        dates.date + " " + dates.time.fillna("00:00"),
        format="%b %d, %Y %H:%M",
        errors="coerce",
    )
    return dates[["game_id", "when"]]


def target_games(games, cohort_targets, dates):
    """Destination player-games of each target, under the cohort's own identity keys."""
    continental = games.loc[
        games.league.isin(CONTINENTAL) & games.season.isin(E6_SEASONS)
    ]
    keyed = cohort_targets.rename(
        columns={"season_dest": "season", "league_dest": "league"}
    )
    rows = continental.merge(
        keyed[["player_name", "season", "league"]],
        on=["player_name", "season", "league"],
        how="inner",
    )
    rows = rows.merge(dates, on="game_id", how="left", validate="m:1")
    rows["gamecode"] = rows.game_id.str.rsplit("-", n=1).str[1].astype(int)
    return rows.sort_values(["player_name", "season", "when", "gamecode"]).reset_index(
        drop=True
    )


def game_parts(rows: pd.DataFrame) -> pd.DataFrame:
    fgm, fga = rows.fg_made + rows.fg3_made, rows.fg_attempted + rows.fg3_attempted
    return pd.DataFrame(
        {
            "eff": rows.pir.astype(float),
            "pts": rows.points.astype(float),
            "game_score": rows.points
            + 0.4 * fgm
            - 0.7 * fga
            - 0.4 * (rows.ft_attempted - rows.ft_made)
            + 0.7 * rows.offensive_rebounds
            + 0.3 * rows.defensive_rebounds
            + rows.steals
            + 0.7 * rows.assists
            + 0.7 * rows.blocks
            - 0.4 * rows.fouls
            - rows.turnovers,
            "minutes": rows.minutes.astype(float),
            "team_poss": rows.team_poss.astype(float),
            "team_minutes": rows.team_minutes.astype(float),
        }
    )


def half_rates(parts: pd.DataFrame, outcome: str) -> float:
    _, numerator, exposure, scale = OUTCOMES[outcome]
    s = parts.sum()
    if exposure == "minutes":
        return float(scale * s[numerator] / s.minutes), float(s.minutes)
    oncourt = s.team_poss * s.minutes / (s.team_minutes / 5.0)
    return float(scale * s[numerator] / oncourt), float(oncourt)


def reconcile(target_rows: pd.DataFrame, cohort_targets: pd.DataFrame) -> pd.DataFrame:
    got = (
        target_rows.groupby(["player_name", "season"])
        .agg(
            games_boxscore=("game_id", "nunique"),
            rows=("game_id", "size"),
            minutes_boxscore=("minutes", "sum"),
            eff_boxscore=("pir", "sum"),
            undated=("when", lambda s: int(s.isna().sum())),
        )
        .reset_index()
        .rename(columns={"season": "season_dest"})
    )
    merged = cohort_targets.merge(got, on=KEY, how="left", validate="1:1")
    merged["games_boxscore"] = merged.games_boxscore.fillna(0).astype(int)
    merged["exception"] = ""
    rules = (
        (merged.games_boxscore.ne(merged.games_dest), "game_count_differs"),
        (merged.rows.ne(merged.games_boxscore), "duplicate_player_game_rows"),
        (
            ~np.isclose(
                merged.minutes_boxscore, merged.minutes_dest, atol=1e-6, rtol=0
            ),
            "minutes_differ",
        ),
        (
            ~np.isclose(merged.eff_boxscore, merged.pir_dest, atol=1e-9, rtol=0),
            "eff_differs",
        ),
        (merged.undated.fillna(1).gt(0), "undated_game"),
    )
    for mask, reason in rules:
        merged.loc[mask & merged.exception.eq(""), "exception"] = reason
    return merged


def split_half_table(
    target_rows: pd.DataFrame, cohort_targets: pd.DataFrame
) -> pd.DataFrame:
    records = []
    lookup = cohort_targets.set_index(KEY)
    for (name, season), group in target_rows.groupby(
        ["player_name", "season"], sort=True
    ):
        parts = game_parts(group).reset_index(drop=True)
        odd, even = parts.iloc[0::2], parts.iloc[1::2]
        record = {
            "player_name": name,
            "season_dest": int(season),
            "league_dest": lookup.loc[(name, season), "league_dest"],
            "games": len(parts),
            "games_odd": len(odd),
            "games_even": len(even),
            "minutes_odd": float(odd.minutes.sum()),
            "minutes_even": float(even.minutes.sum()),
        }
        for code in OUTCOMES:
            full, full_exp = half_rates(parts, code)
            o, o_exp = half_rates(odd, code)
            e, e_exp = half_rates(even, code)
            record.update(
                {
                    f"{code}_full": full,
                    f"{code}_odd": o,
                    f"{code}_even": e,
                    f"{code}_exp_odd": o_exp,
                    f"{code}_exp_even": e_exp,
                }
            )
        records.append(record)
    return pd.DataFrame(records)


def random_split_floor(target_rows, outcome, *, n_draws=N_BOOT, seed=SEED):
    """Half-vs-half simulation: random equal-size game splits per target."""
    _, numerator, exposure, scale = OUTCOMES[outcome]
    rng = np.random.default_rng(seed)
    per_draw = np.zeros(n_draws)
    count = 0
    for _, group in target_rows.groupby(["player_name", "season"], sort=True):
        p = game_parts(group).to_numpy(dtype=float)
        cols = {
            c: i
            for i, c in enumerate(
                ["eff", "pts", "game_score", "minutes", "team_poss", "team_minutes"]
            )
        }
        n = len(p)
        k = (n + 1) // 2
        order = np.argsort(rng.random((n_draws, n)), axis=1)
        mask = np.zeros((n_draws, n), dtype=bool)
        np.put_along_axis(mask, order[:, :k], True, axis=1)

        def sums(col, m):
            return (m * p[:, cols[col]]).sum(axis=1)

        a, b = mask, ~mask
        num_a, num_b = sums(numerator, a), sums(numerator, b)
        if exposure == "minutes":
            ea, eb = sums("minutes", a), sums("minutes", b)
        else:
            ea = (
                sums("team_poss", a)
                * sums("minutes", a)
                / (sums("team_minutes", a) / 5.0)
            )
            eb = (
                sums("team_poss", b)
                * sums("minutes", b)
                / (sums("team_minutes", b) / 5.0)
            )
        diff = scale * num_a / ea - scale * num_b / eb
        per_draw += np.abs(diff) * np.sqrt(ea * eb) / (ea + eb)
        count += 1
    per_draw /= count
    return {
        "mean": float(per_draw.mean()),
        "ci95": [
            float(np.quantile(per_draw, 0.025)),
            float(np.quantile(per_draw, 0.975)),
        ],
        "n_draws": n_draws,
        "seed": seed,
        "targets": count,
    }


def noise_floor(
    table: pd.DataFrame,
    outcome: str,
    target_rows: pd.DataFrame | None,
    *,
    n_draws=N_BOOT,
) -> dict:
    odd, even = table[f"{outcome}_odd"].to_numpy(), table[f"{outcome}_even"].to_numpy()
    full = table[f"{outcome}_full"].to_numpy()
    eo, ee = (
        table[f"{outcome}_exp_odd"].to_numpy(),
        table[f"{outcome}_exp_even"].to_numpy(),
    )
    r = float(np.corrcoef(odd, even)[0, 1])
    rel = 2 * r / (1 + r)
    sd = float(np.std(full, ddof=1))
    sigma = sd * np.sqrt(max(1 - rel, 0.0))
    direct = float(np.mean(np.abs(odd - even) * np.sqrt(eo * ee) / (eo + ee)))
    out = {
        "n": len(table),
        "split_half_r": r,
        "spearman_brown_reliability": rel,
        "outcome_sd": sd,
        "noise_sd_normal": float(sigma),
        "floor_normal": float(np.sqrt(2 / np.pi) * sigma),
        "floor_half_vs_half_odd_even": direct,
    }
    if target_rows is not None:
        out["floor_half_vs_half_random_splits"] = random_split_floor(
            target_rows, outcome, n_draws=n_draws
        )
    return out


def reducible(evaluation: dict, floor: dict) -> dict:
    """Every primary MAE and gain as 'X of a reducible Y' (Y = parent MAE - floor)."""
    out = {}
    for kind in ("floor_normal", "floor_half_vs_half_odd_even"):
        f = floor[kind]
        out[kind] = {
            "floor": f,
            "mae_reducible": {
                arm: m["mae"] - f for arm, m in evaluation["ladder"].items()
            },
            "gains": {
                name: {
                    "gain": c["difference"],
                    "reducible_parent": c["mae_left"] - f,
                    "share_of_reducible": c["difference"] / (c["mae_left"] - f),
                }
                for name, c in evaluation["contrasts"].items()
            },
        }
    return out


# -------------------------------------------------------------------- run --
def pattern_holds(evaluation: dict) -> dict:
    a = evaluation["contrasts"]["history_gain"]
    b = evaluation["contrasts"]["offsets10_increment"]
    out = {}
    for spec in ("player_club_season", "player_season"):
        a_ci, b_ci = a[spec]["ci95"], b[spec]["ci95"]
        a_ok = a_ci is not None and a_ci[0] > 0
        b_ok = b_ci is not None and b_ci[1] < MARGIN_SHARE * b["mae_left"]
        out[spec] = {
            "a_history_gain_above_zero": bool(a_ok),
            "b_offsets10_upper_below_2pct": bool(b_ok),
            "holds": bool(a_ok and b_ok),
        }
    return out


def _run_e6(summary, games, cohort, keys, raw_root, out):
    """E6: odd/even split halves, reconciliation gate and noise floors."""
    # ---- E6 split halves (needed to express E3 effects against the ceiling) ----
    targets = keys.merge(
        cohort[
            [*KEY, "league_dest", "club_dest", "games_dest", "minutes_dest", "pir_dest"]
        ],
        on=KEY,
        how="left",
        validate="1:1",
    )
    dates = load_game_dates(raw_root)
    target_rows = target_games(games, targets, dates)
    reconciliation = reconcile(target_rows, targets)
    exceptions = reconciliation.loc[reconciliation.exception.ne("")]
    control = reconcile(target_rows, targets.assign(games_dest=targets.games_dest + 1))
    if not control.exception.ne("").all():
        raise common.GateFailure(
            "E6 reconciliation negative control did not flag every target"
        )
    exceptions.to_csv(out / "e6_reconciliation_exceptions.csv", index=False)
    usable = reconciliation.loc[reconciliation.exception.eq(""), KEY]
    usable_rows = target_rows.merge(
        usable.rename(columns={"season_dest": "season"}), on=["player_name", "season"]
    )
    table = split_half_table(usable_rows, targets)
    if table.empty:
        raise common.GateFailure("no reconciled targets for E6")
    table.to_csv(out / "e6_split_half_players.csv", index=False)
    summary["e6"] = {
        "targets": len(targets),
        "reconciled": int(len(usable)),
        "exceptions": exceptions[[*KEY, "exception"]].to_dict("records"),
        "gate": "passed" if exceptions.empty else "exceptions_listed",
        "negative_control": "every target flagged as required",
        "schedule_files_sha256": {
            f"{lg}/{s}": sha256_file(
                Path(raw_root) / lg / str(s) / "games" / f"season_{s}_games.parquet"
            )
            for lg in CONTINENTAL
            for s in E6_SEASONS
        },
        "outcomes": {},
    }
    # The full-season rate from box scores must equal the cohort's rate for every outcome.
    check = table[[*KEY, *(f"{c}_full" for c in OUTCOMES)]].merge(
        cohort, on=KEY, how="left", validate="1:1"
    )
    for code in OUTCOMES:
        expected = outcome_rate(check, code, "_dest").to_numpy()
        worst = float(np.max(np.abs(check[f"{code}_full"].to_numpy() - expected)))
        if worst > 1e-9:
            raise common.GateFailure(
                f"E6 {code}: box-score full-season rate differs from cohort by {worst}"
            )
        summary["e6"]["outcomes"][code] = {
            "label": OUTCOMES[code][0],
            "full_rate_max_difference": worst,
            **noise_floor(table, code, usable_rows),
        }


def _run_e3(summary, pairs, cohort, histories, keys, v9, v10_summary, out):
    """E3: the whole pipeline rebuilt per outcome on the 674 targets."""
    # ---- E3 outcomes, whole pipeline per outcome ----
    summary["e3"] = {}
    e3_rows = {}
    for code in OUTCOMES:
        p, c = outcome_inputs(pairs, cohort, histories[code], code)
        with contextlib.redirect_stdout(io.StringIO()):
            features, _ = common.build_features(p, c)
        rows, _ = common.forecast(features, seasons=common.ANCHOR_SEASONS)
        rows = common.on_targets(rows, keys)
        if code == "O1":
            diffs = common.g0_differences(rows, v9, v10_summary)
            common.assert_g0(diffs)
        e3_rows[code] = rows
        rows.to_parquet(out / f"e3_{code}_anchor_rows.parquet", index=False)
        evaluation = evaluate(rows)
        evaluation["label"] = OUTCOMES[code][0]
        evaluation["pattern"] = pattern_holds(evaluation)
        evaluation["reducible"] = reducible(evaluation, summary["e6"]["outcomes"][code])
        evaluation["fallback_share"] = (
            float(rows.scheduled_fallback.astype(bool).mean())
            if "scheduled_fallback" in rows
            else None
        )
        summary["e3"][code] = evaluation
    summary["e3_pattern_holds_k_of_3"] = {
        spec: int(
            sum(summary["e3"][c]["pattern"][spec]["holds"] for c in ("O2", "O3", "O4"))
        )
        for spec in ("player_club_season", "player_season")
    }


def _run_e4_e5(summary, base_features, base_rows, anchor, cohort, keys, out):
    """E4 destinations and E5 extended window on the original EFF inputs."""
    # ---- E4 / E5 on the original (O1) inputs ----
    extended_keys = pd.concat(
        [keys, cohort.loc[cohort.season_dest.eq(2019), KEY]], ignore_index=True
    ).drop_duplicates()
    if len(extended_keys) != 812:
        raise common.GateFailure(f"extended target count {len(extended_keys)} != 812")
    extended = common.on_targets(base_rows, extended_keys)
    extended.to_parquet(out / "e5_extended_rows.parquet", index=False)
    windows = {"anchor": anchor, "extended": extended}
    summary["e4"] = {}
    for window, rows in windows.items():
        sd = float(rows.pir_per36_dest.std(ddof=1))
        record = {}
        for destination, group in rows.groupby("league_dest", sort=True):
            record[destination] = evaluate(
                group, sd=float(group.pir_per36_dest.std(ddof=1))
            )
        record["difference_test_offsets10"] = destination_difference(
            rows, "source_ridge_10", "source_ridge_10_scheduled"
        )
        record["difference_test_history_gain"] = destination_difference(
            rows, "history_only", "scheduled_history"
        )
        record["pooled_outcome_sd"] = sd
        summary["e4"][window] = record
    summary["e5"] = {"extended": evaluate(extended), "anchor": evaluate(anchor)}
    early, early_folds = common.forecast(base_features, seasons=(2017, 2018))
    summary["e5"]["unscorable_seasons"] = {
        str(s): {
            "rows": int(early.season_dest.eq(s).sum()),
            "train_rows": len(early_folds[i]["train_keys"]),
            "status_counts": {
                arm: early.loc[early.season_dest.eq(s), f"{arm}_status"]
                .value_counts()
                .to_dict()
                for arm in common.ALL_ARMS
            },
        }
        for i, s in enumerate((2017, 2018))
    }
    s19 = extended.loc[extended.season_dest.eq(2019)]
    summary["e5"]["season_2019_fallback_share"] = float(
        s19.scheduled_fallback.astype(bool).mean()
    )


def _run_e5b(summary, base_features, anchor, cohort, keys, raw_root, bio_path, out):
    """E5b: age-aware baselines behind the 95% birthdate coverage gate."""
    # ---- E5b age-aware baselines ----
    bio = pd.read_parquet(bio_path)
    age_rows = ages(cohort, raw_root, bio)
    age_rows.to_parquet(out / "e5b_ages.parquet", index=False)
    on_target = keys.merge(age_rows, on=KEY, how="left", validate="1:1")
    coverage = float(on_target.age.notna().mean())
    e5b = {
        "coverage_targets": int(on_target.age.notna().sum()),
        "targets": len(on_target),
        "coverage_share": coverage,
        "coverage_all_cohort_rows": int(age_rows.age.notna().sum()),
        "id_how_targets": on_target.id_how.value_counts().to_dict(),
        "missing_targets": on_target.loc[
            on_target.age.isna(), [*KEY, "id_how"]
        ].to_dict("records"),
        "gate_threshold": AGE_COVERAGE_GATE,
    }
    try:
        assert_age_coverage(coverage, threshold=1.01)
    except common.GateFailure:
        e5b["negative_control"] = "rejected as required"
    else:
        raise common.GateFailure(
            "E5b coverage negative control passed an impossible threshold"
        )
    reproduction, _ = covariate_forecast(base_features, (), common.ANCHOR_SEASONS)
    reproduction = common.on_targets(reproduction, keys)
    worst = float(
        max(np.max(np.abs(reproduction[a] - anchor[a])) for a in common.ALL_ARMS)
    )
    if worst > 1e-9:
        raise common.GateFailure(
            f"age-arm fitter does not reproduce v10 arms without covariates ({worst})"
        )
    e5b["fitter_reproduction_max_difference"] = worst
    try:
        assert_age_coverage(coverage)
    except common.GateFailure:
        e5b["status"] = "not_adjudicable"
    else:
        e5b["status"] = "adjudicable"
        feats = base_features.merge(
            age_rows[[*KEY, "age", "age_c26", "age_c26_sq"]],
            on=KEY,
            how="left",
            validate="1:1",
        )
        covariates = ("age_c26", "age_c26_sq")
        aged, training = covariate_forecast(feats, covariates, common.ANCHOR_SEASONS)
        e5b["training"] = training
        aged_targets = keys.merge(aged, on=KEY, how="left", validate="1:1")
        scorable = np.isfinite(aged_targets[list(common.ALL_ARMS)]).all(axis=1)
        e5b["scorable_targets"] = int(scorable.sum())
        e5b["inconclusive_targets"] = aged_targets.loc[~scorable, KEY].to_dict(
            "records"
        )
        aged_targets.to_parquet(out / "e5b_age_rows.parquet", index=False)
        covered = aged_targets.loc[scorable].reset_index(drop=True)
        e5b["with_age"] = evaluate(covered)
        same = anchor.merge(covered[KEY], on=KEY, how="inner", validate="1:1")
        e5b["without_age_same_targets"] = evaluate(same)
        e5b["age_effect_same_targets"] = {
            arm: e5b["without_age_same_targets"]["ladder"][arm]["mae"]
            - e5b["with_age"]["ladder"][arm]["mae"]
            for arm in common.ALL_ARMS
        }
        # Sensitivity: all 674, a missing test age set to the centre (26); training unchanged.
        full_rows, _ = covariate_forecast(
            feats, covariates, common.ANCHOR_SEASONS, impute_test_at=0.0
        )
        full_rows = common.on_targets(full_rows, keys)
        e5b["all_targets_missing_age_at_centre"] = evaluate(full_rows, share=False)
    summary["e5b"] = e5b


def _write_flat(summary, out):
    """One row per analysis x subset x contrast x interval specification."""
    # ---- flat headline table ----
    flat = []

    def add(analysis, subset, name, record):
        for spec in ("player_club_season", "player_season"):
            ci = record[spec]["ci95"] or [None, None]
            flat.append(
                {
                    "analysis": analysis,
                    "subset": subset,
                    "contrast": name,
                    "spec": spec,
                    "n": record["n"],
                    "difference": record["difference"],
                    "ci_low": ci[0],
                    "ci_high": ci[1],
                    "pct_of_parent_mae": record["pct_of_parent_mae"],
                    "outcome_sd_units": record["outcome_sd_units"],
                    "upper_pct_of_parent_mae": record[spec]["upper_pct_of_parent_mae"],
                    "mde80": record[spec]["mde80"],
                    "positive_seasons": record["positive_seasons"],
                    "n_seasons": record["n_seasons"],
                    "loso_min": (record["loso_range"] or [None, None])[0],
                    "loso_max": (record["loso_range"] or [None, None])[1],
                }
            )

    for code, ev in summary["e3"].items():
        for name, rec in ev["contrasts"].items():
            add("E3", code, name, rec)
    for window in ("anchor", "extended"):
        for dest in CONTINENTAL:
            for name, rec in summary["e4"][window][dest]["contrasts"].items():
                add("E4", f"{window}:{dest}", name, rec)
    for name, rec in summary["e5"]["extended"]["contrasts"].items():
        add("E5", "extended", name, rec)
    e5b = summary["e5b"]
    if e5b["status"] == "adjudicable":
        for name, rec in e5b["with_age"]["contrasts"].items():
            add("E5b", "with_age", name, rec)
        for name, rec in e5b["without_age_same_targets"]["contrasts"].items():
            add("E5b", "without_age_same_targets", name, rec)
    pd.DataFrame(flat).to_csv(out / "headline_contrasts.csv", index=False)


def run(input_dir: Path, raw_root: Path, bio_path: Path, out: Path) -> dict:
    root = ROOT
    v9, v10_summary = common.load_references(root)
    pairs, cohort = common.load_pool(input_dir, "official_corrected")
    keys = common.target_keys(v10_summary)
    summary: dict = {
        "protocol": str(common.PROTOCOL.relative_to(ROOT)),
        "protocol_commit": common.PROTOCOL_COMMIT,
        "protocol_sha256": sha256_file(common.PROTOCOL),
        "exploratory": True,
        "inputs": {
            "pairs_sha256": common.PAIRS_SHA["official_corrected"],
            "cohort_sha256": common.COHORT_SHA,
            "player_bio_sha256": sha256_file(bio_path),
        },
    }

    # G0 recheck on the original inputs: the shared reproduction must still hold here.
    base_features, _ = common.build_features(pairs, cohort)
    base_rows, _ = common.forecast(base_features, seasons=common.EXTENDED_SEASONS)
    anchor = common.on_targets(base_rows, keys)
    g0 = common.g0_differences(anchor, v9, v10_summary)
    common.assert_g0(g0)
    summary["g0_recheck"] = {"status": "passed", "max_difference": max(g0.values())}

    # ---- corpus rebuild and G3 (before any E3 computation) ----
    games, agg, rebuild = rebuild_games(raw_root)
    summary["corpus_rebuild"] = rebuild
    histories = {code: history(agg, code) for code in OUTCOMES}
    g3 = g3_difference(cohort, attach_history(cohort, histories["O1"]))
    try:
        assert_g3(g3, tolerance=-1.0)
    except common.GateFailure:
        g3_control = "rejected as required"
    else:
        raise common.GateFailure("G3 negative control passed an impossible tolerance")
    assert_g3(g3)
    summary["g3"] = {
        **g3,
        "status": "passed",
        "tolerance": G3_TOLERANCE,
        "negative_control": g3_control,
    }

    out.mkdir(parents=True, exist_ok=False)
    hist_frame = cohort[KEY].copy()
    for code in OUTCOMES:
        hist_frame[f"{code}_history"] = attach_history(cohort, histories[code])
    hist_frame.to_parquet(out / "history_rebuild.parquet", index=False)

    _run_e6(summary, games, cohort, keys, raw_root, out)
    _run_e3(summary, pairs, cohort, histories, keys, v9, v10_summary, out)
    _run_e4_e5(summary, base_features, base_rows, anchor, cohort, keys, out)
    _run_e5b(summary, base_features, anchor, cohort, keys, raw_root, bio_path, out)
    _write_flat(summary, out)
    (out / "summary.json").write_text(
        json.dumps(clean(summary), indent=2, sort_keys=True, allow_nan=False) + "\n"
    )
    return summary


def clean(value):
    if isinstance(value, dict):
        return {str(k): clean(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [clean(v) for v in value]
    if isinstance(value, np.generic):
        return clean(value.item())
    if isinstance(value, float) and not np.isfinite(value):
        return None
    return value


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument("--raw-root", type=Path, required=True)
    parser.add_argument("--bio", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    summary = run(args.input_dir, args.raw_root, args.bio, args.out)
    print(
        json.dumps(
            {
                "g3": summary["g3"]["status"],
                "e3_k_of_3": summary["e3_pattern_holds_k_of_3"],
                "e5b": summary["e5b"]["status"],
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
