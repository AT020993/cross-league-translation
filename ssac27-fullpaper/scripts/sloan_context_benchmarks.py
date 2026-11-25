"""Registered destination-aware Sloan benchmarks from frozen September 8 outputs.

Threats: destination confounding (nested context arms), retrospective reuse
(explicit scope), mask/feature drift (keyed old-forecast reproduction), sparse
categories (symmetric fixed-penalty offsets), dependence (conditional intervals).
No raw-data reconstruction, factor refitting, or operating forecast changes.
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import subprocess
from pathlib import Path
import sys

for _name in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[_name] = "1"
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import scipy  # noqa: E402
from threadpoolctl import threadpool_limits  # noqa: E402

from scripts import compare_translation_designs as design  # noqa: E402
from scripts import sloan_revision_analysis as previous  # noqa: E402
from scripts.translation_research_common import sha256_file  # noqa: E402
from scripts.validate_translation_walkforward import _rtm_design  # noqa: E402

KEY = previous.KEY
VARIANTS = tuple(previous.source.VARIANTS)
PENALTIES = (1, 10, 100)
SEASONS = design.SEASONS
PROTOCOL = ROOT / "docs/research/sloan-benchmark-preregistration-2026-09-16.md"
DEFAULT_SOURCE = ROOT / "docs/research/artifacts/sloan-revision-2026-09-08"
DEFAULT_OUTPUT = ROOT / "docs/research/artifacts/sloan-benchmark-2026-09-16"
ARMS = (
    "history_only",
    "scheduled_history",
    "history_destination",
    "history_destination_slope",
    "history_destination_slope_scheduled",
    *(
        arm
        for penalty in PENALTIES
        for arm in (f"source_ridge_{penalty}", f"source_ridge_{penalty}_scheduled")
    ),
)
CODE_FILES = (
    "scripts/sloan_context_benchmarks.py",
    "scripts/sloan_revision_analysis.py",
    "scripts/compare_translation_designs.py",
    "scripts/validate_translation_walkforward.py",
    "scripts/translation_research_common.py",
)


def _hashes(paths):
    return {str(Path(p).relative_to(ROOT)): sha256_file(Path(p)) for p in paths}


def _verify_hash(path, expected):
    path = Path(path)
    if not path.is_file() or sha256_file(path) != expected:
        raise ValueError(f"fingerprint mismatch: {path}")


def _safe_child(root, name):
    root = Path(root).resolve()
    path = (root / name).resolve()
    if not path.is_relative_to(root):
        raise ValueError(f"path escapes artifact directory: {name}")
    return path


def verify_source(source_dir):
    """Verify the frozen output package, without claiming raw-source freshness."""
    source_dir = Path(source_dir).resolve()
    state = json.loads((source_dir / "status.json").read_text())
    if state.get("status") != "complete":
        raise ValueError("frozen revision is incomplete")
    _verify_hash(source_dir / "summary.json", state.get("summary_sha256"))
    summary = json.loads((source_dir / "summary.json").read_text())
    if summary.get("status") != "complete" or set(summary["variants"]) != set(VARIANTS):
        raise ValueError("frozen revision variants are incomplete")
    required = {
        f"{variant}/{mode}/{filename}"
        for variant in VARIANTS
        for mode in previous.MODES
        for filename in ("predictions.parquet", "folds.json")
    } | {f"{variant}/cohort_ledger.parquet" for variant in VARIANTS}
    if set(summary.get("output_hashes", {})) != required:
        raise ValueError("frozen revision output hash set is incomplete")
    paths = [source_dir / "summary.json", source_dir / "status.json"]
    for name, expected in summary["output_hashes"].items():
        path = _safe_child(source_dir, name)
        _verify_hash(path, expected)
        paths.append(path)
    return {
        str(path.relative_to(ROOT))
        if path.is_relative_to(ROOT)
        else str(path): sha256_file(path)
        for path in paths
    }


def _key_set(frame):
    previous.unique(frame)
    return set(map(tuple, frame[KEY].to_numpy()))


def recover_features(ledger, audit):
    """Recover historical row-cutoff translations from frozen cells and lag."""
    previous.unique(ledger)
    rows = ledger.loc[ledger.original_eligible].copy().reset_index(drop=True)
    if not rows.league_dest.isin(("euroleague", "eurocup")).all():
        raise ValueError("unrecognized destination")
    if rows.league_src.isna().any() or rows.league_src.eq("").any():
        raise ValueError("missing source category")
    for season, group in rows.groupby("season_dest", sort=True):
        cutoff = audit.get("cutoffs", {}).get(str(int(season)))
        if cutoff is None:
            raise ValueError(f"missing historical cutoff: {season}")
        for kind in design.DESIGNS:
            info = cutoff.get(kind)
            if info is None or "cells" not in info or "k" not in info:
                raise ValueError(f"incomplete historical cutoff: {season}/{kind}")
            table = pd.DataFrame(info["cells"])
            if len(table) and table.duplicated(["league", "destination"]).any():
                raise ValueError("duplicate factor cell")
            multiplier, fallback, reliable = design.lookup(table, group)
            lag = np.nan if info["k"] is None else float(info["k"])
            rows.loc[group.index, f"{kind}_translated"] = (
                group.pir_per36_src.to_numpy() * multiplier * lag
            )
            rows.loc[group.index, f"{kind}_fallback"] = fallback
            rows.loc[group.index, f"{kind}_reliable"] = reliable
    rows["feature_eligible"] = np.isfinite(
        rows[[f"{kind}_translated" for kind in design.DESIGNS]]
    ).all(axis=1)
    return rows


def _fold_rows(features, fold):
    season = int(fold["season"])
    declared = pd.DataFrame(fold["train_keys"], columns=KEY)
    previous.unique(declared)
    if (declared.season_dest >= season).any():
        raise ValueError("training key is not strictly prior")
    derived = features.loc[features.season_dest.lt(season) & features.feature_eligible]
    if _key_set(derived) != _key_set(declared):
        raise ValueError(f"training key mismatch: {season}")
    train = derived.sort_values(KEY).copy()
    test = features.loc[features.season_dest.eq(season)].sort_values(KEY).copy()
    return train, test


def reproduce_historical(features, saved, audit):
    """Refuse changed masks, saved predictors, outcomes, coefficients or forecasts."""
    previous.unique(saved)
    folds = audit["folds"]
    if [int(f["season"]) for f in folds] != list(SEASONS):
        raise ValueError("historical outer folds are missing or reordered")
    expected_test = features.loc[features.season_dest.isin(SEASONS)]
    if _key_set(expected_test) != _key_set(saved):
        raise ValueError("historical evaluation key mismatch")
    maximum = 0.0
    for fold in folds:
        train, test = _fold_rows(features, fold)
        expected = saved.loc[saved.season_dest.eq(fold["season"])].sort_values(KEY)
        for col in (
            "pir_per36_dest",
            "pir_per36_src",
            "prior_mean_pir36",
            "above_own_prior",
            "scheduled_translated",
            "transfer_translated",
        ):
            try:
                np.testing.assert_allclose(
                    test[col].to_numpy(dtype=float),
                    expected[col].to_numpy(dtype=float),
                    atol=1e-9,
                    rtol=0,
                    equal_nan=True,
                )
            except AssertionError as exc:
                raise ValueError(f"historical field changed: {col}") from exc
        for arm, kind in (
            ("history_only", None),
            ("scheduled_history", "scheduled"),
            ("transfer_history", "transfer"),
        ):
            x = _rtm_design(
                train, None if kind is None else train[f"{kind}_translated"].to_numpy()
            )
            rank = int(np.linalg.matrix_rank(x))
            if len(train) < x.shape[1] or rank != x.shape[1]:
                raise ValueError("historical reference fit lacks rank")
            beta = np.linalg.lstsq(x, train.pir_per36_dest.to_numpy(), rcond=None)[0]
            info = fold["arms"][arm]
            if info["status"] != "ok" or info["rank"] != rank:
                raise ValueError("historical fit status changed")
            try:
                np.testing.assert_allclose(
                    beta, info["coefficients"], atol=1e-9, rtol=0
                )
            except AssertionError as exc:
                raise ValueError("historical coefficients do not reproduce") from exc
            supported = test.feature_eligible.to_numpy(dtype=bool)
            pred = np.full(len(test), np.nan)
            subset = test.loc[supported]
            pred[supported] = (
                _rtm_design(
                    subset,
                    None if kind is None else subset[f"{kind}_translated"].to_numpy(),
                )
                @ beta
            )
            try:
                np.testing.assert_allclose(
                    pred, expected[arm], atol=1e-9, rtol=0, equal_nan=True
                )
            except AssertionError as exc:
                raise ValueError(
                    f"historical forecast does not reproduce: {arm}"
                ) from exc
            finite = np.isfinite(pred)
            if finite.any():
                maximum = max(
                    maximum,
                    float(
                        np.max(
                            np.abs(pred[finite] - expected.loc[finite, arm].to_numpy())
                        )
                    ),
                )
        scored = pd.DataFrame(fold["scoring_keys"], columns=KEY)
        if _key_set(scored) != _key_set(expected.loc[expected.scored]):
            raise ValueError("historical scoring keys changed")
        if not np.array_equal(
            test.feature_eligible.to_numpy(dtype=bool),
            expected.scored.to_numpy(dtype=bool),
        ):
            raise ValueError("historical scoring support changed")
    return {
        "status": "reproduced",
        "tolerance": 1e-9,
        "max_absolute_forecast_difference": maximum,
        "n": int(saved.scored.sum()),
        "fold_training_counts": {str(f["season"]): len(f["train_keys"]) for f in folds},
    }


def model_matrix(rows, arm):
    x = _rtm_design(rows)
    names = ["intercept", "source_rate", "prior_rate", "above_prior"]
    if arm == "history_only":
        return x, names
    if arm == "scheduled_history":
        return np.column_stack([x, rows.scheduled_translated]), [
            *names,
            "scheduled_translated",
        ]
    destination = rows.league_dest.eq("euroleague").to_numpy(dtype=float)
    x = np.column_stack([x, destination])
    names.append("destination_euroleague")
    if arm != "history_destination":
        x = np.column_stack([x, destination * rows.pir_per36_src.to_numpy()])
        names.append("destination_x_source")
    if arm.endswith("_scheduled"):
        x = np.column_stack([x, rows.scheduled_translated])
        names.append("scheduled_translated")
    return x, names


def fit_model(train, test, arm):
    """Only source offsets are penalized; no test outcomes enter the fit."""
    if arm not in ARMS:
        raise ValueError(f"unknown arm: {arm}")
    x, names = model_matrix(train, arm)
    z, _ = model_matrix(test, arm)
    if not np.isfinite(x).all() or not np.isfinite(z).all():
        raise ValueError("nonfinite model input")
    rank = int(np.linalg.matrix_rank(x)) if len(x) else 0
    info = {
        "unpenalized_rank": rank,
        "unpenalized_columns": x.shape[1],
        "status": "ok",
        "features": names.copy(),
        "source_categories": [],
        "unseen_source_rows": 0,
    }
    if len(train) < x.shape[1] or rank != x.shape[1]:
        info["status"] = (
            "insufficient_training" if len(train) < x.shape[1] else "rank_deficient"
        )
        return np.full(len(test), np.nan), info
    outcome = train.pir_per36_dest.to_numpy(dtype=float)
    if not np.isfinite(outcome).all():
        raise ValueError("nonfinite training outcome")
    if arm.startswith("source_ridge_"):
        penalty = int(arm.split("_")[2])
        categories = sorted(train.league_src.unique())
        source = np.column_stack([train.league_src.eq(c) for c in categories]).astype(
            float
        )
        target = np.column_stack([test.league_src.eq(c) for c in categories]).astype(
            float
        )
        base_columns = x.shape[1]
        x, z = np.column_stack([x, source]), np.column_stack([z, target])
        regularizer = np.zeros((len(categories), x.shape[1]))
        regularizer[:, base_columns:] = np.sqrt(penalty) * np.eye(len(categories))
        x_fit = np.vstack([x, regularizer])
        y_fit = np.r_[outcome, np.zeros(len(categories))]
        info.update(
            penalty=penalty,
            source_categories=categories,
            unseen_source_rows=int((~test.league_src.isin(categories)).sum()),
            features=names + [f"source_offset:{c}" for c in categories],
        )
    else:
        x_fit, y_fit = x, outcome
    beta = np.linalg.lstsq(x_fit, y_fit, rcond=None)[0]
    prediction = z @ beta
    if not np.isfinite(prediction).all():
        raise ValueError("nonfinite fitted prediction")
    info["coefficients"] = beta.tolist()
    return prediction, info


def fit_benchmarks(features, saved, audit):
    reproduction = reproduce_historical(features, saved, audit)
    output, fold_records = [], []
    for fold in audit["folds"]:
        train, all_test = _fold_rows(features, fold)
        test = all_test.copy()
        support = test.feature_eligible
        record = {
            "season": int(fold["season"]),
            "train_keys": previous.key_list(train),
            "arms": {},
        }
        for arm in ARMS:
            test[arm] = np.nan
            prediction, diagnostic = fit_model(train, test.loc[support], arm)
            test.loc[support, arm] = prediction
            test[f"{arm}_status"] = np.where(
                support, diagnostic["status"], "historical_support_refusal"
            )
            record["arms"][arm] = diagnostic
        test["scored"] = np.isfinite(test[list(ARMS)]).all(axis=1)
        record["common_scoring_keys"] = previous.key_list(test.loc[test.scored])
        fold_records.append(record)
        output.append(test)
    return pd.concat(output, ignore_index=True), fold_records, reproduction


def arm_metrics(rows, arm):
    if not len(rows):
        return {"n": 0, "mae": None, "rmse": None, "bias": None}
    difference = rows[arm].to_numpy() - rows.pir_per36_dest.to_numpy()
    return {
        "n": len(rows),
        "mae": float(np.abs(difference).mean()),
        "rmse": float(np.sqrt(np.square(difference).mean())),
        "bias": float(difference.mean()),
    }


def contrast_pairs():
    pairs = {
        "destination_increment": (
            "history_destination_slope",
            "history_destination_slope_scheduled",
        ),
        **{
            f"source_ridge_{p}_increment": (
                f"source_ridge_{p}",
                f"source_ridge_{p}_scheduled",
            )
            for p in PENALTIES
        },
    }
    pairs.update(
        {
            f"original_vs_{arm}": (arm, "scheduled_history")
            for arm in ARMS
            if arm != "scheduled_history"
        }
    )
    return pairs


def paired_contrast(rows, left, right, *, season_sensitivity=True):
    difference = np.abs(rows[left] - rows.pir_per36_dest) - np.abs(
        rows[right] - rows.pir_per36_dest
    )
    result = {
        "left": left,
        "right": right,
        "positive_favors": right,
        "player_club_season": previous.multiway_interval(
            difference, rows.player_name, rows.cluster
        ),
        "player_season": {
            **previous.multiway_interval(
                difference, rows.player_name, rows.season_dest
            ),
            "few_season_clusters": True,
        },
    }
    if season_sensitivity:
        means = [
            float(difference.loc[group.index].mean())
            for _, group in rows.groupby("season_dest")
        ]
        result["equal_season_difference"] = float(np.mean(means)) if means else None
        result["leave_one_season_out"] = {
            str(int(s)): (
                float(difference.loc[rows.season_dest.ne(s)].mean())
                if rows.season_dest.ne(s).any()
                else None
            )
            for s in sorted(rows.season_dest.unique())
        }
    return result


def summarize(rows, *, breakdown=True):
    common = rows.loc[np.isfinite(rows[list(ARMS)]).all(axis=1)].copy()
    result = {
        "n": len(common),
        "metrics": {arm: arm_metrics(common, arm) for arm in ARMS},
        "native_metrics": {
            arm: arm_metrics(rows.loc[np.isfinite(rows[arm])], arm) for arm in ARMS
        },
        "contrasts": {
            name: paired_contrast(common, left, right, season_sensitivity=breakdown)
            for name, (left, right) in contrast_pairs().items()
        },
    }
    if breakdown:
        result["season_results"] = {
            str(int(season)): summarize(group, breakdown=False)
            for season, group in rows.groupby("season_dest", sort=True)
        }
        result["destination_results"] = {
            destination: summarize(group, breakdown=False)
            for destination, group in rows.groupby("league_dest", sort=True)
        }
    return result


def _equivalent(actual, expected, path="summary"):
    if isinstance(actual, dict):
        if not isinstance(expected, dict) or set(actual) != set(expected):
            raise ValueError(f"summary keys disagree: {path}")
        for key, value in actual.items():
            _equivalent(value, expected[key], f"{path}.{key}")
    elif isinstance(actual, (list, tuple)):
        if not isinstance(expected, list) or len(actual) != len(expected):
            raise ValueError(f"summary lengths disagree: {path}")
        for i, (a, e) in enumerate(zip(actual, expected)):
            _equivalent(a, e, f"{path}.{i}")
    elif isinstance(actual, (float, np.floating)):
        if not np.isfinite(actual):
            if expected is not None:
                raise ValueError(f"summary unavailable value changed: {path}")
        elif expected is None or not np.isclose(actual, expected, atol=1e-9, rtol=0):
            raise ValueError(f"summary value disagrees: {path}")
    elif actual != expected:
        raise ValueError(f"summary value disagrees: {path}")


def _common_summaries(frames):
    keys = set.intersection(
        *[
            _key_set(rows.loc[np.isfinite(rows[list(ARMS)]).all(axis=1)])
            for rows in frames.values()
        ]
    )
    variants = {
        variant: summarize(
            rows.loc[[tuple(key) in keys for key in rows[KEY].to_numpy()]]
        )
        for variant, rows in frames.items()
    }
    return {"n": len(keys), "variants": variants}


def source_support(folds):
    return {
        "unseen_source_rows": {
            str(f["season"]): {
                arm: info["unseen_source_rows"]
                for arm, info in f["arms"].items()
                if arm.startswith("source_ridge_")
            }
            for f in folds
        },
        "source_category_counts": {
            str(f["season"]): {
                arm: len(info["source_categories"])
                for arm, info in f["arms"].items()
                if arm.startswith("source_ridge_")
            }
            for f in folds
        },
    }


def render_results(summary):
    """Generate the numerical companion only from the recorded summary."""

    def table(headers, records):
        return "\n".join(
            [
                "| " + " | ".join(headers) + " |",
                "| " + " | ".join(["---"] * len(headers)) + " |",
                *["| " + " | ".join(map(str, row)) + " |" for row in records],
            ]
        )

    def value(number):
        return "unavailable" if number is None else f"{number:.6f}"

    def ci(item):
        interval = item.get("ci95")
        return (
            f"[{interval[0]:.6f}, {interval[1]:.6f}]"
            if interval is not None
            else "refused: " + item.get("reason", item["status"])
        )

    common = summary["cross_variant_common"]
    lines = [
        "# Sloan destination-aware benchmarks: numerical companion",
        "",
        "Generated from the registered frozen-output benchmark. Exploratory "
        "retrospective evidence; no independent confirmation or deployment.",
        "",
        "## Specification",
        "",
        table(
            ["Field", "Specification"],
            [
                [
                    "Unit",
                    "Player/destination-season, six destination seasons 2020–2025",
                ],
                [
                    "Population",
                    "Five frozen source variants; original eligibility "
                    "and saved fold keys",
                ],
                [
                    "Estimator",
                    "OLS history/context; symmetric source offsets with fixed "
                    "ridge penalties 1, 10, 100",
                ],
                [
                    "Null",
                    "No incremental MAE reduction from scheduled translation "
                    "after destination context",
                ],
                [
                    "Filter",
                    "Original support; common finite predictions; "
                    "unseen sources have zero offsets",
                ],
                ["Key", "player_name + season_dest"],
                [
                    "Uncertainty",
                    "Conditional player × club-season; player × season sensitivity",
                ],
            ],
        ),
        "",
        "All penalties were fixed before this extension. They are sensitivity arms, "
        "not an outcome-selected winner. Source offsets are intercept adjustments; "
        "they do not exhaust generic source-dependent slope models.",
        "",
        "## Common-population arm errors",
        "",
        f"Cross-variant common n = {common['n']}. Positive signed bias means "
        "prediction minus outcome. Full-precision results and native arm counts "
        "remain in summary.json.",
        "",
        table(
            ["Source variant", "Arm", "n", "MAE", "RMSE", "Signed bias"],
            [
                [
                    variant,
                    arm,
                    item["n"],
                    value(item["mae"]),
                    value(item["rmse"]),
                    value(item["bias"]),
                ]
                for variant, report in common["variants"].items()
                for arm, item in report["metrics"].items()
            ],
        ),
        "",
        "## Incremental scheduled-translation contrasts",
        "",
        "Every contrast is baseline MAE minus baseline-plus-scheduled MAE; "
        "positive favors adding scheduled translation.",
        "",
        table(
            [
                "Source variant",
                "Baseline",
                "Difference",
                "Player × club-season 95%",
                "Player × season 95%",
            ],
            [
                [
                    variant,
                    name,
                    value(item["player_club_season"]["difference"]),
                    ci(item["player_club_season"]),
                    ci(item["player_season"]),
                ]
                for variant, report in common["variants"].items()
                for name, item in report["contrasts"].items()
                if name.endswith("_increment")
            ],
        ),
        "",
        "## Comparisons with original scheduled + history",
        "",
        "Each difference is the compared arm MAE minus the original scheduled + "
        "history MAE. Positive favors the original scheduled + history model; "
        "negative favors the compared arm. These are paired conditional contrasts "
        "on the same cross-variant common rows.",
        "",
        table(
            [
                "Source variant",
                "Compared arm",
                "Difference",
                "Player × club-season 95%",
                "Player × season 95%",
            ],
            [
                [
                    variant,
                    item["left"],
                    value(item["player_club_season"]["difference"]),
                    ci(item["player_club_season"]),
                    ci(item["player_season"]),
                ]
                for variant, report in common["variants"].items()
                for name, item in report["contrasts"].items()
                if name.startswith("original_vs_")
            ],
        ),
        "",
        "## Destination diagnostics",
        "",
        table(
            [
                "Source variant",
                "Destination",
                "n",
                "Context MAE",
                "Context + scheduled MAE",
                "Difference",
                "Conditional 95%",
            ],
            [
                [
                    variant,
                    destination,
                    report["n"],
                    value(report["metrics"]["history_destination_slope"]["mae"]),
                    value(
                        report["metrics"]["history_destination_slope_scheduled"]["mae"]
                    ),
                    value(
                        report["contrasts"]["destination_increment"][
                            "player_club_season"
                        ]["difference"]
                    ),
                    ci(
                        report["contrasts"]["destination_increment"][
                            "player_club_season"
                        ]
                    ),
                ]
                for variant, whole in common["variants"].items()
                for destination, report in whole["destination_results"].items()
            ],
        ),
        "",
        "## Annual primary contrasts",
        "",
        table(
            ["Source variant", "Season", "n", "Difference", "Conditional 95%"],
            [
                [
                    variant,
                    season,
                    report["n"],
                    value(
                        report["contrasts"]["destination_increment"][
                            "player_club_season"
                        ]["difference"]
                    ),
                    ci(
                        report["contrasts"]["destination_increment"][
                            "player_club_season"
                        ]
                    ),
                ]
                for variant, whole in common["variants"].items()
                for season, report in whole["season_results"].items()
            ],
        ),
        "",
        "## Equal-season and leave-one-season-out primary sensitivity",
        "",
        "These leave-one-season-out summaries retain predictions. They do not refit "
        "forecasts after omitting a season.",
        "",
        table(
            ["Source variant", "Equal-season mean", *map(str, SEASONS)],
            [
                [
                    variant,
                    value(
                        report["contrasts"]["destination_increment"][
                            "equal_season_difference"
                        ]
                    ),
                    *[
                        value(
                            report["contrasts"]["destination_increment"][
                                "leave_one_season_out"
                            ][str(s)]
                        )
                        for s in SEASONS
                    ],
                ]
                for variant, report in common["variants"].items()
            ],
        ),
        "",
        "## Reproduction and source support",
        "",
        "Historical forecast discrepancies were computed during generation. "
        "Readback recomputes forecast-loss summaries and verifies artifact hashes; "
        "it does not rerun the historical regression-reproduction check. "
        "Support counts are reconciled with the saved fold diagnostics.",
        "",
        table(
            [
                "Source variant",
                "Scored old rows",
                "Maximum old forecast discrepancy",
                "Training rows by outer season",
            ],
            [
                [
                    variant,
                    report["reproduction"]["n"],
                    f"{report['reproduction']['max_absolute_forecast_difference']:.3g}",
                    "; ".join(
                        f"{s}: {n}"
                        for s, n in report["reproduction"][
                            "fold_training_counts"
                        ].items()
                    ),
                ]
                for variant, report in summary["variants"].items()
            ],
        ),
        "",
        table(
            [
                "Source variant",
                "Season",
                "Ridge arm",
                "Training source categories",
                "Unseen source rows",
            ],
            [
                [
                    variant,
                    season,
                    arm,
                    report["source_support"]["source_category_counts"][season][arm],
                    count,
                ]
                for variant, report in summary["variants"].items()
                for season, counts in report["source_support"][
                    "unseen_source_rows"
                ].items()
                for arm, count in counts.items()
            ],
        ),
        "",
        "## Interpretation and provenance",
        "",
        "All confidence intervals condition on fitted forecasts and frozen factor/lag "
        "estimates. They do not include full-pipeline refitting uncertainty. Six "
        "outer seasons limit season-level inference. Intervals spanning zero leave "
        "incremental benefit undetermined; they do not establish equivalence.",
        "",
        "Original holdout PARTIAL, unresolved source adjudication, human statistical "
        "and scout review, exposure selection, and all-signings coverage remain "
        "separate limitations. No improved signings, salaries, wins, causal league "
        "effect, or prospective accuracy is established.",
        "",
        "Environment: " + json.dumps(summary["environment"], sort_keys=True) + ".",
        "",
        "Input, output, protocol and generator fingerprints are recorded "
        "in summary.json. "
        "The historical source manifest is " + summary["source_summary_path"] + ".",
        "",
    ]
    return "\n".join(lines)


def repository_provenance(root):
    """Missing Git metadata is unavailable provenance, never an invented revision."""
    unavailable = {
        "repository_revision": None,
        "working_tree_dirty": None,
        "git_status": "unavailable",
    }
    if not (Path(root) / ".git").exists():
        return {**unavailable, "git_reason": "no_git_metadata"}
    try:
        head = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=root,
            text=True,
            capture_output=True,
            check=False,
        )
        state = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=root,
            text=True,
            capture_output=True,
            check=False,
        )
    except OSError as exc:
        return {**unavailable, "git_reason": f"git_unavailable:{type(exc).__name__}"}
    if head.returncode or state.returncode or not head.stdout.strip():
        return {
            **unavailable,
            "git_reason": "git_provenance_command_failed",
            "git_head_returncode": head.returncode,
            "git_status_returncode": state.returncode,
        }
    return {
        "repository_revision": head.stdout.strip(),
        "working_tree_dirty": bool(state.stdout.strip()),
        "git_status": "available",
        "git_reason": None,
    }


def run(source_dir=DEFAULT_SOURCE, out_dir=DEFAULT_OUTPUT):
    source_dir, out_dir = Path(source_dir).resolve(), Path(out_dir).resolve()
    if source_dir == out_dir or source_dir in out_dir.parents:
        raise ValueError("benchmark output must be outside the frozen source")
    out_dir.mkdir(parents=True, exist_ok=True)
    design.dump_json(out_dir / "status.json", {"status": "running"})
    try:
        input_hashes = verify_source(source_dir)
        input_hashes.update(_hashes([PROTOCOL]))
        code_hashes = _hashes([ROOT / name for name in CODE_FILES])
        frames, variants, output_hashes = {}, {}, {}
        for variant in VARIANTS:
            ledger = pd.read_parquet(source_dir / variant / "cohort_ledger.parquet")
            saved = pd.read_parquet(
                source_dir / variant / "original/predictions.parquet"
            )
            audit = json.loads(
                (source_dir / variant / "original/folds.json").read_text()
            )
            features = recover_features(ledger, audit)
            rows, folds, reproduction = fit_benchmarks(features, saved, audit)
            frames[variant] = rows
            variants[variant] = {
                **summarize(rows),
                "reproduction": reproduction,
                "source_support": source_support(folds),
            }
            variant_dir = out_dir / variant
            variant_dir.mkdir(exist_ok=True)
            rows.to_parquet(variant_dir / "predictions.parquet", index=False)
            design.dump_json(variant_dir / "folds.json", {"folds": folds})
            for name in ("predictions.parquet", "folds.json"):
                path = variant_dir / name
                output_hashes[str(path.relative_to(out_dir))] = sha256_file(path)
            primary = variants[variant]["contrasts"]["destination_increment"]
            print(
                json.dumps(
                    {
                        "variant": variant,
                        "n": variants[variant]["n"],
                        "reproduction": reproduction,
                        "destination_increment": primary["player_club_season"],
                        "metrics": variants[variant]["metrics"],
                    }
                ),
                flush=True,
            )
        if verify_source(source_dir) != {
            k: v
            for k, v in input_hashes.items()
            if k != str(PROTOCOL.relative_to(ROOT))
        }:
            raise ValueError("frozen source changed during run")
        for name, expected in {**input_hashes, **code_hashes}.items():
            _verify_hash(ROOT / name, expected)
        summary = {
            "schema_version": 1,
            "status": "complete",
            "scope": "exploratory retrospective, conditional on frozen factor fits",
            "source_dir": str(source_dir.relative_to(ROOT))
            if source_dir.is_relative_to(ROOT)
            else str(source_dir),
            "source_summary_path": str((source_dir / "summary.json").relative_to(ROOT))
            if source_dir.is_relative_to(ROOT)
            else str(source_dir / "summary.json"),
            "source_summary_sha256": sha256_file(source_dir / "summary.json"),
            "protocol": str(PROTOCOL.relative_to(ROOT)),
            "arms": list(ARMS),
            "penalties": list(PENALTIES),
            "input_hashes": input_hashes,
            "code_hashes": code_hashes,
            "output_hashes": output_hashes,
            "variants": variants,
            "cross_variant_common": _common_summaries(frames),
            "environment": {
                "python": platform.python_version(),
                "numpy": np.__version__,
                "pandas": pd.__version__,
                "scipy": scipy.__version__,
                **repository_provenance(ROOT),
                "threads": 1,
            },
            "limitations": [
                "The historical evaluation population has already informed research.",
                "Intervals condition on saved factors and fitted forecasting models.",
                "Six outer seasons limit season-level uncertainty.",
                "Source ridge comparators adjust intercept offsets, not source slopes.",
                "No all-signings, causal effect, or recruitment-utility claim follows.",
            ],
        }
        (out_dir / "results.md").write_text(render_results(summary))
        output_hashes["results.md"] = sha256_file(out_dir / "results.md")
        design.dump_json(out_dir / "summary.json", summary)
        design.dump_json(
            out_dir / "status.json",
            {
                "status": "complete",
                "summary_sha256": sha256_file(out_dir / "summary.json"),
            },
        )
        return load_verified(out_dir)
    except Exception as exc:
        design.dump_json(
            out_dir / "status.json",
            {"status": "failed", "error": f"{type(exc).__name__}: {exc}"},
        )
        raise


def load_verified(out_dir=DEFAULT_OUTPUT):
    """Verify hashes and recompute loss summaries from saved predictions.

    Historical fit-reproduction diagnostics are recorded at generation and
    protected by the summary fingerprint; this reader does not refit regressions.
    Source-support summaries are reconciled with hash-verified fold diagnostics.
    """
    out_dir = Path(out_dir).resolve()
    state = json.loads((out_dir / "status.json").read_text())
    if state.get("status") != "complete":
        raise ValueError("benchmark is incomplete")
    _verify_hash(out_dir / "summary.json", state.get("summary_sha256"))
    summary = json.loads((out_dir / "summary.json").read_text())
    if summary.get("status") != "complete" or set(summary["variants"]) != set(VARIANTS):
        raise ValueError("benchmark variant set is incomplete")
    required = {
        f"{v}/{name}"
        for v in VARIANTS
        for name in ("predictions.parquet", "folds.json")
    }
    required.add("results.md")
    if set(summary.get("output_hashes", {})) != required:
        raise ValueError("benchmark output hash set is incomplete")
    for name, expected in summary["output_hashes"].items():
        _verify_hash(_safe_child(out_dir, name), expected)
    for group in ("input_hashes", "code_hashes"):
        if not summary.get(group):
            raise ValueError(f"missing {group}")
        for name, expected in summary[group].items():
            _verify_hash(ROOT / name, expected)
    _verify_hash(
        ROOT / summary["source_summary_path"], summary["source_summary_sha256"]
    )
    frames = {}
    for variant in VARIANTS:
        rows = pd.read_parquet(out_dir / variant / "predictions.parquet")
        previous.unique(rows)
        frames[variant] = rows
        expected = {
            k: v
            for k, v in summary["variants"][variant].items()
            if k not in ("reproduction", "source_support")
        }
        _equivalent(summarize(rows), expected, variant)
        folds = json.loads((out_dir / variant / "folds.json").read_text())["folds"]
        _equivalent(
            source_support(folds), summary["variants"][variant]["source_support"]
        )
    _equivalent(_common_summaries(frames), summary["cross_variant_common"], "common")
    if (out_dir / "results.md").read_text() != render_results(summary):
        raise ValueError("numerical companion does not reproduce")
    return summary


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args(argv)
    with threadpool_limits(limits=1):
        run(args.source_dir, args.out_dir)


if __name__ == "__main__":
    main()
