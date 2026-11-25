"""Registered competition-slope comparison using immutable v9 features.

Threats: reused outcomes, changed support, zero imputation, test scale leakage,
omitted-year re-entry, stale upstream forecasts and incomplete artifacts. All
original arms replay before new fits; factor fitting is deliberately absent.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys

for _name in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[_name] = "1"
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from threadpoolctl import threadpool_limits  # noqa: E402

from scripts import sloan_context_benchmarks as benchmark  # noqa: E402
from scripts import sloan_full_refit as refit  # noqa: E402
from scripts import sloan_v9_diagnostics as diagnostics  # noqa: E402
from scripts.translation_research_common import sha256_file  # noqa: E402

KEY = refit.KEY
VARIANTS = diagnostics.VARIANTS
PENALTIES = benchmark.PENALTIES
ARMS = tuple(
    arm for p in PENALTIES for arm in (f"cell_slope_{p}", f"cell_slope_{p}_scheduled")
)
CONTRASTS = {
    f"cell_slope_{p}_increment": (f"cell_slope_{p}", f"cell_slope_{p}_scheduled")
    for p in PENALTIES
}
PROTOCOL = (
    ROOT / "docs/research/sloan-v10-slope-comparison-preregistration-2026-09-20.md"
)
DIAGNOSTICS = ROOT / "docs/research/artifacts/sloan-v9-2026-09-19/diagnostics.json"
CODE_FILES = tuple(
    dict.fromkeys(
        (
            "scripts/sloan_v10_slopes.py",
            "scripts/sloan_v9_diagnostics.py",
            *refit.CODE_FILES,
        )
    )
)


def read_json(path):
    return json.loads(Path(path).read_text())


def dump(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    refit.design.dump_json(path, value)


def key_set(rows):
    return diagnostics.keys(rows, KEY)


def select(rows, wanted):
    return diagnostics.restrict(rows, wanted, KEY)


def verify_inputs(inputs, refits, diagnostic_path=DIAGNOSTICS):
    """Bind frozen bytes to the committed diagnostic, without factor fits."""
    inputs, refits, diagnostic_path = map(Path, (inputs, refits, diagnostic_path))
    d_state = read_json(diagnostic_path.parent / "status.json")
    if d_state.get("status") != "complete":
        raise ValueError("v9 diagnostic is incomplete")
    refit._check(diagnostic_path, d_state["diagnostics_sha256"])
    diag = read_json(diagnostic_path)
    state, saved = read_json(refits / "status.json"), read_json(refits / "summary.json")
    if state.get("status") != "complete" or saved.get("status") != "complete":
        raise ValueError("v9 refits are incomplete")
    refit._check(refits / "summary.json", state["summary_sha256"])
    refit._check(refits / "summary.json", diag["refit_summary_sha256"])
    refit._check(refits / "manifest.json", saved["manifest_sha256"])
    manifest = read_json(refits / "manifest.json")
    expected_scenarios = refit.scenario_matrix(range(2016, 2026))
    if (
        tuple(manifest["variants"]) != VARIANTS
        or manifest["scenarios"] != expected_scenarios
        or manifest["outer_seasons"] != list(benchmark.SEASONS)
        or manifest["factor_bootstrap"] != 2000
    ):
        raise ValueError("v9 scenario definition changed")
    target = {tuple(k) for k in manifest["reference_keys"]}
    if (
        len(target) != len(manifest["reference_keys"])
        or target != {tuple(k) for k in diag["common_keys"]}
        or len(target) != diag["common_n"]
    ):
        raise ValueError("v9 target key mismatch")
    expected = {
        f"{v}/{s['name']}/{name}"
        for v in VARIANTS
        for s in expected_scenarios
        for name in (
            "predictions.parquet",
            "fits.json",
            "summary.json",
            "complete.json",
        )
    }
    if set(saved["output_hashes"]) != expected or saved["scenario_count"] != 56:
        raise ValueError("v9 refit inventory is incomplete")
    render = read_json(diagnostic_path.parent / "render_manifest.json")
    refit._check(
        diagnostic_path.parent / "preparation.json", render["preparation_sha256"]
    )
    refit._check(inputs / "preparation.json", render["preparation_sha256"])
    hashes = {
        "v9/diagnostics.json": sha256_file(diagnostic_path),
        "v9/preparation.json": render["preparation_sha256"],
        "inputs/preparation.json": render["preparation_sha256"],
    }
    for name in ("summary.json", "manifest.json", "status.json"):
        hashes[f"refits/{name}"] = sha256_file(refits / name)
    for name, digest in saved["output_hashes"].items():
        refit._check(benchmark._safe_child(refits, name), digest)
        hashes[f"refits/{name}"] = digest
    for name, digest in manifest["code_hashes"].items():
        refit._check(benchmark._safe_child(ROOT, name), digest)
    for variant in VARIANTS:
        directory = inputs / variant
        _, _, meta = refit.load_variant(directory)
        if (
            meta["variant"] != variant
            or meta["files"] != manifest["inputs"][variant]["files"]
        ):
            raise ValueError("v9 input variant mismatch")
        digest = manifest["inputs"][variant]["metadata_sha256"]
        refit._check(directory / "variant.json", digest)
        hashes[f"inputs/{variant}/variant.json"] = digest
        for name, digest in meta["files"].items():
            hashes[f"inputs/{variant}/{name}"] = digest
    return manifest, hashes


def recover_features(cohort, audit, scenario):
    """Recover, never estimate, every historical factor and lag feature."""
    key_set(cohort)
    if not cohort.original_eligible.eq(True).all():
        raise ValueError("frozen cohort contains ineligible rows")
    rows = benchmark.recover_features(cohort, audit)
    omitted = scenario["omitted_season"]
    for season, group in rows.groupby("season_dest", sort=True):
        cutoff = audit["cutoffs"][str(int(season))]
        for kind in refit.design.DESIGNS:
            info = cutoff[kind]
            if any(
                int(y) >= season or int(y) == omitted
                for y in info["factor_season_counts"]
            ):
                raise ValueError("future or omitted season in frozen factor support")
            lag_keys = pd.DataFrame(info["lag_keys"], columns=KEY)
            key_set(lag_keys)
            if (
                lag_keys.season_dest.ge(season) | lag_keys.season_dest.eq(omitted)
            ).any():
                raise ValueError("future or omitted season in frozen lag support")
            multiplier, fallback, reliable = refit.design.lookup(
                pd.DataFrame(info["cells"]), group
            )
            lag = np.nan if info["k"] is None else float(info["k"])
            for name, value in (
                ("multiplier_value", multiplier),
                ("fallback", fallback),
                ("reliable", reliable),
                ("k", lag),
            ):
                rows.loc[group.index, f"{kind}_{name}"] = value
            reason = np.where(
                ~np.isfinite(multiplier), "no_finite_destination_tier", ""
            )
            rows.loc[group.index, f"{kind}_reason"] = np.where(
                np.isfinite(multiplier) & ~np.isfinite(lag),
                "no_prior_lag_outcomes",
                reason,
            )
    return rows


def replay_original(cohort, saved, audit, scenario, *, seasons=benchmark.SEASONS):
    """Check old forecasts, scientific fields, fold keys and coefficients."""
    key_set(saved)
    features = recover_features(cohort, audit, scenario)
    rows, folds = refit.fit_refit_predictions(
        features, omitted_season=scenario["omitted_season"], seasons=seasons
    )
    try:
        refit.source.keyed_equal(rows, saved, KEY)
        benchmark._equivalent(folds, audit["folds"], "original_folds")
    except (AssertionError, KeyError) as exc:
        raise ValueError("saved original-arm reproduction failed") from exc
    return features, {
        "status": "reproduced",
        "tolerance": 1e-9,
        "n": len(rows),
        "arms": list(benchmark.ARMS),
        "folds": len(folds),
        "omitted_season": scenario["omitted_season"],
    }


def fit_model(train, test, arm, *, slopes=True):
    """Penalize source offsets and pure cell slopes; test labels are unused."""
    if arm not in ARMS:
        raise ValueError(f"unknown slope arm: {arm}")
    parent = arm.replace("cell_slope_", "source_ridge_", 1)
    penalty = int(arm.split("_")[2])
    for rows in (train, test):
        if (
            rows[["league_src", "league_dest"]].isna().any().any()
            or rows[["league_src", "league_dest"]].eq("").any().any()
        ):
            raise ValueError("missing competition category")
    x, names = benchmark.model_matrix(train, parent)
    z, _ = benchmark.model_matrix(test, parent)
    if not np.isfinite(x).all() or not np.isfinite(z).all():
        raise ValueError("nonfinite model input")
    rank = int(np.linalg.matrix_rank(x)) if len(x) else 0
    scale = (
        float(train.pir_per36_src.to_numpy(float).std(ddof=0)) if len(train) else np.nan
    )
    categories = sorted(train.league_src.unique())
    cells = sorted(set(zip(train.league_src, train.league_dest))) if slopes else []
    info = {
        "status": "ok",
        "penalty": penalty,
        "source_scale": scale,
        "scale_ddof": 0,
        "centered": False,
        "train_n": len(train),
        "unpenalized_rank": rank,
        "unpenalized_columns": x.shape[1],
        "features": names.copy(),
        "source_categories": categories,
        "cell_categories": [list(c) for c in cells],
        "unseen_source_rows": int((~test.league_src.isin(categories)).sum()),
        "unseen_cell_rows": sum(
            c not in cells for c in zip(test.league_src, test.league_dest)
        )
        if slopes
        else 0,
    }
    if slopes and (not np.isfinite(scale) or scale <= 0):
        info["status"] = "invalid_training_scale"
        return np.full(len(test), np.nan), info
    if len(train) < x.shape[1] or rank != x.shape[1]:
        info["status"] = (
            "insufficient_training" if len(train) < x.shape[1] else "rank_deficient"
        )
        return np.full(len(test), np.nan), info
    outcome = train.pir_per36_dest.to_numpy(float)
    if not np.isfinite(outcome).all():
        raise ValueError("nonfinite training outcome")

    def penalized(rows):
        columns = [rows.league_src.eq(c).to_numpy(float) for c in categories]
        columns.extend(
            (rows.league_src.eq(s) & rows.league_dest.eq(d)).to_numpy(float)
            * rows.pir_per36_src.to_numpy(float)
            / scale
            for s, d in cells
        )
        return np.column_stack(columns)

    c, t = penalized(train), penalized(test)
    n_base = x.shape[1]
    x, z = np.column_stack([x, c]), np.column_stack([z, t])
    regularizer = np.zeros((c.shape[1], x.shape[1]))
    regularizer[:, n_base:] = np.sqrt(penalty) * np.eye(c.shape[1])
    beta = np.linalg.lstsq(
        np.vstack([x, regularizer]), np.r_[outcome, np.zeros(c.shape[1])], rcond=None
    )[0]
    prediction = z @ beta
    if not np.isfinite(prediction).all():
        raise ValueError("nonfinite slope forecast")
    info.update(
        features=names
        + [f"source_offset:{c}" for c in categories]
        + [f"cell_slope:{s}:{d}" for s, d in cells],
        coefficients=beta.tolist(),
    )
    return prediction, info


def fit_predictions(features, saved, audit, scenario):
    """Use declared historical keys; refusals remain in the forecast ledger."""
    key_set(features)
    key_set(saved)
    outputs, folds = [], []
    for old in audit["folds"]:
        season = int(old["season"])
        declared = pd.DataFrame(old["train_keys"], columns=KEY)
        declared_keys = key_set(declared)
        train = features.loc[
            features.season_dest.lt(season)
            & features.season_dest.ne(scenario["omitted_season"])
            & features.feature_eligible
        ].sort_values(KEY)
        if key_set(train) != declared_keys:
            raise ValueError("declared training keys differ from chronological support")
        test = saved.loc[saved.season_dest.eq(season)].sort_values(KEY).copy()
        test_features = features.loc[features.season_dest.eq(season)].sort_values(KEY)
        if key_set(test) != key_set(test_features):
            raise ValueError("saved test keys differ from recovered features")
        support = test.feature_eligible.astype(bool)
        fold = {"season": season, "train_keys": old["train_keys"], "arms": {}}
        for arm in ARMS:
            test[arm] = np.nan
            pred, info = fit_model(train, test.loc[support], arm)
            test.loc[support, arm] = pred
            test[f"{arm}_status"] = np.where(support, info["status"], "feature_refusal")
            fold["arms"][arm] = info
        test["v10_scored"] = np.isfinite(test[list(ARMS)]).all(axis=1) & np.isfinite(
            test.pir_per36_dest
        )
        test["v10_scoring_exclusion"] = np.where(
            np.isfinite(test.pir_per36_dest), "", "unknown_outcome"
        )
        for arm in ARMS:
            mask = test.v10_scoring_exclusion.eq("") & test[f"{arm}_status"].ne("ok")
            test.loc[mask, "v10_scoring_exclusion"] = test.loc[mask, f"{arm}_status"]
        if ((~test.v10_scored) & test.v10_scoring_exclusion.eq("")).any():
            raise ValueError("unexplained slope scoring refusal")
        fold["scoring_keys"] = refit.revision.key_list(test.loc[test.v10_scored])
        folds.append(fold)
        outputs.append(test)
    return pd.concat(outputs, ignore_index=True), folds


def score(rows):
    if not len(rows):
        return {
            "status": "not_estimable",
            "n": 0,
            "metrics": None,
            "contrasts": None,
            "paired": None,
        }
    if not np.isfinite(rows[[*ARMS, "pir_per36_dest"]]).all().all():
        return {
            "status": "inconclusive",
            "n": len(rows),
            "metrics": None,
            "contrasts": None,
            "paired": None,
        }
    return {
        "status": "ok",
        "n": len(rows),
        "metrics": {a: diagnostics.errors(rows, a) for a in ARMS},
        "contrasts": {
            c: benchmark.paired_contrast(rows, *pair, season_sensitivity=False)
            for c, pair in CONTRASTS.items()
        },
        "paired": {c: diagnostics.paired(rows, *pair) for c, pair in CONTRASTS.items()},
    }


def scenario_summary(rows, folds, target, common):
    present = key_set(rows)
    selected = select(rows, target)
    native = rows.loc[rows.v10_scored]
    scorable = key_set(native)
    missing, unscored = len(target - present), len((target & present) - scorable)
    primary = (
        score(selected)
        if not missing and not unscored
        else {
            "status": "inconclusive",
            "n": len(selected),
            "metrics": None,
            "contrasts": None,
            "paired": None,
        }
    )
    return {
        **primary,
        "target_n": len(target),
        "target_missing": missing,
        "target_unscored": unscored,
        "native_n": len(native),
        "native_arm_metrics": {
            arm: diagnostics.errors(eligible, arm)
            if len(eligible)
            else {
                "n": 0,
                "mae": None,
                "rmse": None,
                "bias": None,
                "median_absolute_error": None,
                "p90_absolute_error": None,
            }
            for arm in ARMS
            for eligible in [
                rows.loc[np.isfinite(rows[arm]) & np.isfinite(rows.pir_per36_dest)]
            ]
        },
        "common_n": len(common),
        "native": score(native),
        "common": score(select(rows, common)),
        "refusals": rows.v10_scoring_exclusion.value_counts().sort_index().to_dict(),
        "fold_support": [
            {
                "season": f["season"],
                "train_n": len(f["train_keys"]),
                "scored_n": len(f["scoring_keys"]),
                "arms": {
                    a: {
                        k: v
                        for k, v in info.items()
                        if k not in ("coefficients", "features")
                    }
                    for a, info in f["arms"].items()
                },
            }
            for f in folds
        ],
    }


def check_outputs(out):
    """Read back artifacts and recompute scenario reports from saved rows."""
    out = Path(out)
    state, summary = read_json(out / "status.json"), read_json(out / "summary.json")
    if state["status"] != "complete":
        raise ValueError("slope artifact package is incomplete")
    refit._check(out / "summary.json", state["summary_sha256"])
    refit._check(out / "manifest.json", summary["manifest_sha256"])
    manifest = read_json(out / "manifest.json")
    if sorted(summary["variants"]) != sorted(manifest["variants"]):
        raise ValueError("saved variant inventory changed")
    for name in (
        "protocol_sha256",
        "code_hashes",
        "input_hashes",
        "v9_diagnostics_sha256",
        "v9_preparation_sha256",
    ):
        if summary[name] != manifest[name]:
            raise ValueError("saved manifest binding changed: " + name)
    expected = {
        f"{v}/{s['name']}/{name}"
        for v in manifest["variants"]
        for s in manifest["scenarios"]
        for name in (
            "features.parquet",
            "predictions.parquet",
            "fits.json",
            "reproduction.json",
        )
    }
    if set(summary["output_hashes"]) != expected:
        raise ValueError("slope artifact inventory is incomplete")
    for name, digest in summary["output_hashes"].items():
        refit._check(benchmark._safe_child(out, name), digest)
    target = {tuple(k) for k in manifest["target_keys"]}
    common = set(target)
    for v in manifest["variants"]:
        for s in manifest["scenarios"]:
            rows = pd.read_parquet(out / v / s["name"] / "predictions.parquet")
            common &= key_set(rows.loc[rows.v10_scored])
    if summary["target_n"] != len(target) or summary["common_n"] != len(common):
        raise ValueError("saved target/common counts changed")
    if sorted(common) != [tuple(k) for k in summary["common_keys"]]:
        raise ValueError("saved common support changed")
    for v in manifest["variants"]:
        for s in manifest["scenarios"]:
            directory = out / v / s["name"]
            rows = pd.read_parquet(directory / "predictions.parquet")
            folds = read_json(directory / "fits.json")["folds"]
            benchmark._equivalent(
                scenario_summary(rows, folds, target, common),
                summary["variants"][v]["scenarios"][s["name"]],
            )
        rows = select(
            pd.read_parquet(out / v / "reference/predictions.parquet"), target
        )
        valid = summary["variants"][v]["scenarios"]["reference"]["status"] == "ok"
        expected_paired = score(rows)["paired"] if valid else None
        benchmark._equivalent(expected_paired, summary["variants"][v]["paired"])
        for name, column in (
            ("by_season", "season_dest"),
            ("by_destination", "league_dest"),
        ):
            expected_groups = (
                {
                    c: diagnostics.breakdown(rows, column, *p)
                    for c, p in CONTRASTS.items()
                }
                if valid
                else None
            )
            benchmark._equivalent(expected_groups, summary["variants"][v][name])
    return {
        "status": "verified",
        "target_n": len(target),
        "common_n": len(common),
        "scenarios": len(manifest["variants"]) * len(manifest["scenarios"]),
    }


def _separate_output(out, protected):
    for root in protected:
        if out == root or out in root.parents or root in out.parents:
            raise ValueError("output overlaps a protected input tree")
    if out.exists() and (not out.is_dir() or any(out.iterdir())):
        raise ValueError("output must be a new or empty directory")


def run(inputs, refits, out):
    inputs, refits, out = map(lambda p: Path(p).resolve(), (inputs, refits, out))
    _separate_output(out, (inputs, refits, DIAGNOSTICS.parent.resolve()))
    old_manifest, input_hashes = verify_inputs(inputs, refits)
    code_hashes = {name: sha256_file(ROOT / name) for name in CODE_FILES}
    protocol_hash = sha256_file(PROTOCOL)
    target = {tuple(k) for k in old_manifest["reference_keys"]}
    manifest = {
        "schema_version": 1,
        "protocol_sha256": protocol_hash,
        "code_hashes": code_hashes,
        "input_hashes": input_hashes,
        "v9_diagnostics_sha256": input_hashes["v9/diagnostics.json"],
        "v9_preparation_sha256": input_hashes["v9/preparation.json"],
        "inputs": str(inputs),
        "refits": str(refits),
        "variants": list(VARIANTS),
        "scenarios": old_manifest["scenarios"],
        "target_keys": sorted(target),
        "arms": list(ARMS),
        "penalties": list(PENALTIES),
        "exposure": "All historical outcomes already exposed; exploratory comparison",
    }
    out.mkdir(parents=True, exist_ok=True)
    dump(out / "manifest.json", manifest)
    dump(out / "status.json", {"status": "running", "phase": "original_reproduction"})
    try:
        with threadpool_limits(limits=1):
            # ALL upstream reproductions pass before ANY new model fit.
            for variant in VARIANTS:
                _, cohort, _ = refit.load_variant(inputs / variant)
                for scenario in old_manifest["scenarios"]:
                    directory, original = (
                        out / variant / scenario["name"],
                        refits / variant / scenario["name"],
                    )
                    audit = read_json(original / "fits.json")
                    saved = pd.read_parquet(original / "predictions.parquet")
                    features, gate = replay_original(cohort, saved, audit, scenario)
                    directory.mkdir(parents=True)
                    features.to_parquet(directory / "features.parquet", index=False)
                    dump(directory / "reproduction.json", gate)
            dump(out / "status.json", {"status": "running", "phase": "slope_fitting"})
            common = set(target)
            for variant in VARIANTS:
                for scenario in old_manifest["scenarios"]:
                    directory, original = (
                        out / variant / scenario["name"],
                        refits / variant / scenario["name"],
                    )
                    features = pd.read_parquet(directory / "features.parquet")
                    saved = pd.read_parquet(original / "predictions.parquet")
                    rows, folds = fit_predictions(
                        features, saved, read_json(original / "fits.json"), scenario
                    )
                    rows.to_parquet(directory / "predictions.parquet", index=False)
                    dump(
                        directory / "fits.json", {"scenario": scenario, "folds": folds}
                    )
                    common &= key_set(rows.loc[rows.v10_scored])
            variants, outputs = {}, {}
            for variant in VARIANTS:
                reports = {}
                for scenario in old_manifest["scenarios"]:
                    directory = out / variant / scenario["name"]
                    rows = pd.read_parquet(directory / "predictions.parquet")
                    folds = read_json(directory / "fits.json")["folds"]
                    reports[scenario["name"]] = scenario_summary(
                        rows, folds, target, common
                    )
                    for name in (
                        "features.parquet",
                        "predictions.parquet",
                        "fits.json",
                        "reproduction.json",
                    ):
                        outputs[str((directory / name).relative_to(out))] = sha256_file(
                            directory / name
                        )
                rows = select(
                    pd.read_parquet(out / variant / "reference/predictions.parquet"),
                    target,
                )
                valid = reports["reference"]["status"] == "ok"
                variants[variant] = {
                    "scenarios": reports,
                    "paired": reports["reference"]["paired"],
                    "by_season": {
                        c: diagnostics.breakdown(rows, "season_dest", *p)
                        for c, p in CONTRASTS.items()
                    }
                    if valid
                    else None,
                    "by_destination": {
                        c: diagnostics.breakdown(rows, "league_dest", *p)
                        for c, p in CONTRASTS.items()
                    }
                    if valid
                    else None,
                }
            _, current_hashes = verify_inputs(inputs, refits)
            if current_hashes != input_hashes:
                raise ValueError("frozen inputs changed during run")
            for name, digest in code_hashes.items():
                refit._check(ROOT / name, digest)
            refit._check(PROTOCOL, protocol_hash)
            summary = {
                "schema_version": 1,
                "status": "complete"
                if all(
                    s["status"] == "ok"
                    for v in variants.values()
                    for s in v["scenarios"].values()
                )
                else "inconclusive",
                "manifest_sha256": sha256_file(out / "manifest.json"),
                "protocol_sha256": protocol_hash,
                "code_hashes": code_hashes,
                "input_hashes": input_hashes,
                "v9_diagnostics_sha256": input_hashes["v9/diagnostics.json"],
                "v9_preparation_sha256": input_hashes["v9/preparation.json"],
                "target_n": len(target),
                "common_n": len(common),
                "common_keys": sorted(common),
                "variants": variants,
                "output_hashes": outputs,
            }
            dump(out / "summary.json", summary)
            dump(
                out / "status.json",
                {
                    "status": "complete",
                    "analysis_status": summary["status"],
                    "summary_sha256": sha256_file(out / "summary.json"),
                },
            )
            check_outputs(out)
            return summary
    except Exception as exc:
        dump(
            out / "status.json",
            {"status": "failed", "error": f"{type(exc).__name__}: {exc}"},
        )
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inputs", required=True, type=Path)
    parser.add_argument("--refits", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    summary = run(args.inputs, args.refits, args.out)
    print(json.dumps({k: summary[k] for k in ("status", "target_n", "common_n")}))


if __name__ == "__main__":
    main()
