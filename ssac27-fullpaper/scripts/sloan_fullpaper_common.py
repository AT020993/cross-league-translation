#!/usr/bin/env python3
"""Shared inputs and the G0 reproduction gate for the SSAC27 full-paper analyses.

Pre-registration: docs/research/sloan-full-paper-preregistration-2026-11-03.md
(commit f52e7c831, pushed 2026-11-03T09:15:02Z, before this file existed).

Threats: stale or substituted inputs (sha256 pins equal to the v10 analysis
manifest); silent drift from the submitted numbers (G0 at absolute 1e-9);
a gate that cannot fail (impossible-tolerance negative control); changing
targets (the 674 v10 keys are fixed and joined 1:1).

Every analysis generator imports this module. Nothing here edits a v9/v10
pinned file; the v10 estimators are imported, not copied.
"""

# ruff: noqa: E501 -- sha256 pins and gate messages
from __future__ import annotations

if __name__ == "__main__":
    import sys as _sys
    from pathlib import Path as _Path

    _sys.path.insert(0, str(_Path(__file__).resolve().parents[1]))
    from src.research.execution import enter as _enter

    _enter(__file__)

import argparse
import json
import os
from pathlib import Path
import sys

for _name in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_name, "1")
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from scripts import sloan_context_benchmarks as benchmark  # noqa: E402
from scripts import sloan_full_refit as refit  # noqa: E402
from scripts import sloan_v10_slopes as v10  # noqa: E402
from scripts.translation_research_common import fit_table, sha256_file  # noqa: E402

PROTOCOL = ROOT / "docs/research/sloan-full-paper-preregistration-2026-11-03.md"
PROTOCOL_COMMIT = "f52e7c831fef6759eab202c8ff8c56fa76037533"
KEY = list(refit.KEY)

#: Staged copy of github.com/AT020993/cross-league-translation ssac27-v10/data.
INPUT_DIR = Path("data/processed/sloan_v10_public")
POOLS = {
    "A": "official_corrected",
    "B": "verified_same_club_full",
    "C": "overlap_keys_full",
    "D": "same_club",
}
COHORT_SHA = "c629f43e3194642d483701c3d07666252938d587e747c99dbb031a2346bf2abf"
PAIRS_SHA = {
    "official_corrected": "d964727924630dbf32c1764daf1e536c81d58988218a230fea591c62c1a62f58",
    "verified_same_club_full": "85ba5c9125e164c8eb7918c62680b969ff2f168bb2059cd3343bfecd10e5204d",
    "overlap_keys_full": "80fa11a25642650783f38b7771147f311bc2d1f64deb7477d5037e324212a841",
    "same_club": "43b1dca8192b6aaeed78a5b8c254853b528656a514f25d7fce96b55fb5f67881",
}
V9_DIAGNOSTICS = Path("docs/research/artifacts/sloan-v9-2026-09-19/diagnostics.json")
V10_SUMMARY = Path("docs/research/artifacts/sloan-v10-2026-09-20/summary.json")
V9_DIAGNOSTICS_SHA = "b8ba21daae872e97cb08357d9c5be09e016f23a8cb92ad8d588a2d93ba2a9a40"
V10_SUMMARY_SHA = "58f2cdc5a032415de2b2331e7aaa8e9975914903daac156970edfe37a28dc638"

ORIGINAL_ARMS = tuple(benchmark.ARMS)
SLOPE_ARMS = tuple(v10.ARMS)
ALL_ARMS = ORIGINAL_ARMS + SLOPE_ARMS
PENALTIES = tuple(benchmark.PENALTIES)
PRIMARY_PENALTY = 10
ANCHOR_SEASONS = tuple(range(2020, 2026))
EXTENDED_SEASONS = tuple(range(2019, 2026))
G0_TOLERANCE = 1e-9

#: Readable names for the primary arms (with/without translation pairs).
PRIMARY_ARMS = {
    "history": "history_only",
    "history_translation": "scheduled_history",
    "offsets10": "source_ridge_10",
    "offsets10_translation": "source_ridge_10_scheduled",
}


class GateFailure(AssertionError):
    """A pre-registered gate did not hold; downstream analyses must not run."""


def check_sha(path: Path, expected: str) -> None:
    actual = sha256_file(path)
    if actual != expected:
        raise GateFailure(
            f"input fingerprint mismatch: {path} ({actual} != {expected})"
        )


def load_pool(input_dir: Path, pool: str = "official_corrected"):
    """Pairs and cohort for one factor pool, hash-checked against the v10 pins."""
    if pool not in PAIRS_SHA:
        raise ValueError(f"unknown pool: {pool}")
    directory = Path(input_dir) / pool
    check_sha(directory / "pairs.parquet", PAIRS_SHA[pool])
    check_sha(directory / "cohort.parquet", COHORT_SHA)
    pairs = pd.read_parquet(directory / "pairs.parquet")
    cohort = pd.read_parquet(directory / "cohort.parquet")
    refit.revision.unique(pairs, ["player_name", "season"])
    refit.revision.unique(cohort)
    return pairs, cohort


def load_references(root: Path):
    v9_path, v10_path = Path(root) / V9_DIAGNOSTICS, Path(root) / V10_SUMMARY
    check_sha(v9_path, V9_DIAGNOSTICS_SHA)
    check_sha(v10_path, V10_SUMMARY_SHA)
    return json.loads(v9_path.read_text()), json.loads(v10_path.read_text())


def target_keys(v10_summary: dict) -> pd.DataFrame:
    keys = pd.DataFrame(v10_summary["common_keys"], columns=KEY)
    if len(keys) != v10_summary["target_n"] or keys.duplicated().any():
        raise GateFailure("v10 target keys are not the unique 674")
    return keys


def build_features(pairs, cohort, *, fitter=fit_table, seed=0, n_boot=2000):
    """Translated features at every row's own cutoff (the v10 code path)."""
    features, diagnostics = refit.refit_features(
        pairs, cohort, seed=seed, n_boot=n_boot, fitter=fitter
    )
    return features, diagnostics


def forecast(features: pd.DataFrame, *, seasons=ANCHOR_SEASONS):
    """All 11 original and 6 cell-slope arms, chronological, keyed rows."""
    rows, folds = refit.fit_refit_predictions(features, seasons=seasons)
    out = []
    for season in seasons:
        train = features.loc[
            features.season_dest.lt(season) & features.feature_eligible
        ].sort_values(KEY)
        test = rows.loc[rows.season_dest.eq(season)].sort_values(KEY).copy()
        support = test.feature_eligible.astype(bool)
        for arm in SLOPE_ARMS:
            test[arm] = np.nan
            if support.any():
                prediction, info = v10.fit_model(train, test.loc[support], arm)
                test.loc[support, arm] = prediction
                test[f"{arm}_status"] = np.where(
                    support, info["status"], "feature_refusal"
                )
            else:
                test[f"{arm}_status"] = "feature_refusal"
        out.append(test)
    rows = pd.concat(out, ignore_index=True)
    rows["all_arms_scored"] = np.isfinite(rows[list(ALL_ARMS)]).all(axis=1)
    return rows, folds


def on_targets(rows: pd.DataFrame, keys: pd.DataFrame) -> pd.DataFrame:
    """Join to a fixed target; an unscorable target is a failure, never a drop."""
    merged = keys.merge(rows, on=KEY, how="left", validate="1:1")
    missing = merged[list(ALL_ARMS)].isna().any(axis=1) | merged.pir_per36_dest.isna()
    if missing.any():
        raise GateFailure(f"{int(missing.sum())} target forecasts are unscorable")
    return merged


def mae(rows: pd.DataFrame, arm: str, outcome: str = "pir_per36_dest") -> float:
    return float(np.mean(np.abs(rows[arm] - rows[outcome])))


def contrast(rows: pd.DataFrame, left: str, right: str) -> dict:
    """Paired MAE(left) - MAE(right); positive favours `right` (v10 convention)."""
    return benchmark.paired_contrast(rows, left, right, season_sensitivity=True)


def g0_differences(rows: pd.DataFrame, v9: dict, v10_summary: dict) -> dict:
    """Absolute differences between reproduced and recorded pool-A reference values."""
    original = v9["variants"]["official_corrected"]["scenarios"]["reference"]
    slopes = v10_summary["variants"]["official_corrected"]["scenarios"]["reference"]
    diffs = {}
    for arm in ORIGINAL_ARMS:
        diffs[f"mae:{arm}"] = abs(mae(rows, arm) - original["metrics"][arm]["mae"])
    for arm in SLOPE_ARMS:
        diffs[f"mae:{arm}"] = abs(mae(rows, arm) - slopes["metrics"][arm]["mae"])
    recorded = original["contrasts"]["original_vs_history_only"]["player_club_season"]
    got = contrast(rows, "history_only", "scheduled_history")["player_club_season"]
    diffs["history_gain"] = abs(got["difference"] - recorded["difference"])
    diffs["history_ci_low"] = abs(got["ci95"][0] - recorded["ci95"][0])
    diffs["history_ci_high"] = abs(got["ci95"][1] - recorded["ci95"][1])
    return diffs


def assert_g0(diffs: dict, tolerance: float = G0_TOLERANCE) -> None:
    worst = max(diffs, key=diffs.get)
    if not diffs[worst] <= tolerance:
        raise GateFailure(
            f"G0 failed: {worst} differs by {diffs[worst]:.3e} (tolerance {tolerance:.0e})"
        )


def anchor_rows(
    root: Path, input_dir: Path, *, pool="official_corrected", fitter=fit_table
):
    """Pool reference rows on the 674 targets, after G0 has passed for pool A."""
    v9, v10_summary = load_references(root)
    pairs, cohort = load_pool(input_dir, pool)
    features, _ = build_features(pairs, cohort, fitter=fitter)
    rows, folds = forecast(features)
    return on_targets(rows, target_keys(v10_summary)), features, folds


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    root = Path.cwd()
    v9, v10_summary = load_references(root)
    rows, features, folds = anchor_rows(root, args.input_dir)
    diffs = g0_differences(rows, v9, v10_summary)
    # Negative control first: a gate that cannot fail checks nothing (METHOD.md §8).
    try:
        assert_g0(diffs, tolerance=-1.0)
    except GateFailure:
        negative_control = "rejected as required"
    else:
        raise GateFailure("G0 negative control passed an impossible tolerance")
    assert_g0(diffs)
    args.out.mkdir(parents=True, exist_ok=False)
    rows.to_parquet(args.out / "anchor_rows_pool_A.parquet", index=False)
    features.to_parquet(args.out / "features_pool_A.parquet", index=False)
    result = {
        "gate": "G0",
        "status": "passed",
        "tolerance": G0_TOLERANCE,
        "max_difference": max(diffs.values()),
        "differences": diffs,
        "negative_control": negative_control,
        "n_targets": len(rows),
        "protocol_commit": PROTOCOL_COMMIT,
        "protocol_sha256": sha256_file(root / PROTOCOL),
        "mae": {arm: mae(rows, arm) for arm in ALL_ARMS},
    }
    (args.out / "g0.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n"
    )
    print(
        f"G0 passed: {len(diffs)} values, max |difference| {result['max_difference']:.3e}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
