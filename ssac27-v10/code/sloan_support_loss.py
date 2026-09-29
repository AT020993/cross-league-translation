# ruff: noqa: E501 -- long strings are rendered research prose and tables
"""Registered restriction diagnostic; immutable inputs and fixed forecast keys.

Ranges describe artificial restrictions, not confidence intervals or a randomized
verification effect. The original v10 evidence and estimators remain unchanged.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import platform
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from threadpoolctl import threadpool_limits  # noqa: E402

from scripts import sloan_v10_slopes as frozen  # noqa: E402
from scripts.translation_research_common import sha256_file, stable_seed  # noqa: E402
from src.research.input_receipts import snapshot_inputs, verify_snapshot  # noqa: E402

KEY = frozen.KEY
PAIR_KEY = ["player_name", "season"]
CONTROLS = {
    "season_count": ["season"],
    "cell_season_count": ["league_src", "league_dest", "season"],
}
REPETITIONS = 200
BASE_SEED = 28092026
ARMS = tuple(
    f"{family}_{p}{suffix}"
    for family in ("source_ridge", "cell_slope")
    for p in frozen.PENALTIES
    for suffix in ("", "_scheduled")
)
PROTOCOL = "docs/research/sloan-support-loss-preregistration-2026-09-28.md"
CODE_FILES = tuple(
    dict.fromkeys(
        (
            "scripts/sloan_support_loss.py",
            "src/research/input_receipts.py",
            *frozen.CODE_FILES,
        )
    )
)
FILES = (
    "features.parquet",
    "predictions.parquet",
    "fits.json",
    "sample-keys.json",
    "summary.json",
)
read = frozen.read_json
dump = frozen.dump


def validate_pools(full, verified):
    """B must be a literal subset of A; matching never reads outcome values."""
    a = frozen.diagnostics.keys(full, PAIR_KEY)
    b = frozen.diagnostics.keys(verified, PAIR_KEY)
    if not b <= a:
        raise ValueError("verified pool is not nested")
    if full[CONTROLS["cell_season_count"]].isna().any().any():
        raise ValueError("missing sampling stratum")
    try:
        pd.testing.assert_frame_equal(
            full.set_index(PAIR_KEY).loc[sorted(b)].sort_index(),
            verified.set_index(PAIR_KEY).sort_index(),
            check_exact=True,
        )
    except AssertionError as exc:
        raise ValueError("verified measurements changed") from exc


def sample_keys(full, verified, control, repetition):
    """Stable selection uses only identities and the registered strata."""
    frozen.diagnostics.keys(full, PAIR_KEY)
    frozen.diagnostics.keys(verified, PAIR_KEY)
    columns = CONTROLS[control]
    candidates = {
        (k if isinstance(k, tuple) else (k,)): sorted(
            map(tuple, group[PAIR_KEY].itertuples(index=False, name=None))
        )
        for k, group in full.groupby(columns, sort=True, dropna=False)
    }
    counts = verified.groupby(columns, sort=True, dropna=False).size()
    rng = np.random.default_rng(stable_seed(BASE_SEED, control, repetition))
    chosen = set()
    for key, count in counts.items():
        key = key if isinstance(key, tuple) else (key,)
        pool = candidates.get(key, [])
        if count > len(pool):
            raise ValueError("infeasible sampling stratum")
        chosen.update(pool[i] for i in rng.choice(len(pool), int(count), replace=False))
    if len(chosen) != len(verified):
        raise ValueError("sample count mismatch")
    return chosen


def restrict_pairs(full, chosen):
    return frozen.diagnostics.restrict(full, chosen, PAIR_KEY)


def fit_predictions(features, folds, target):
    """Never change the original training mask when a feature becomes missing."""
    frozen.key_set(features)
    selected = frozen.select(features, target)
    output, fitted = [], []
    if len({f["season"] for f in folds}) != len(folds):
        raise ValueError("duplicate forecast fold")
    for fold in folds:
        season = int(fold["season"])
        train_keys = frozen.key_set(pd.DataFrame(fold["train_keys"], columns=KEY))
        train = frozen.select(features, train_keys).sort_values(KEY)
        if frozen.key_set(train) != train_keys:
            raise ValueError("missing training keys")
        if train.season_dest.ge(season).any():
            raise ValueError("future training observation")
        test = selected.loc[selected.season_dest.eq(season)].sort_values(KEY).copy()
        audit = {"season": season, "train_keys": fold["train_keys"], "arms": {}}
        support = test.feature_eligible
        for arm in ARMS:
            test[arm] = np.nan
            test[f"{arm}_status"] = "feature_refusal"
            if not train.feature_eligible.all():
                info = {"status": "required_training_feature_unavailable"}
                test[f"{arm}_status"] = info["status"]
            else:
                fit = (
                    frozen.fit_model
                    if arm.startswith("cell_slope")
                    else frozen.benchmark.fit_model
                )
                prediction, info = fit(train, test.loc[support], arm)
                test.loc[support, arm] = prediction
                test.loc[support, f"{arm}_status"] = info["status"]
            audit["arms"][arm] = info
        fitted.append(audit)
        output.append(test)
    rows = pd.concat(output, ignore_index=True)
    if frozen.key_set(rows) != target:
        raise ValueError("changed forecast target")
    return rows, fitted


def support_counts(rows):
    finite = np.isfinite(rows.scheduled_multiplier_value)
    fallback = rows.scheduled_fallback.eq(True)
    return {
        "n": len(rows),
        "nonfallback": int((finite & ~fallback).sum()),
        "fallback": int((finite & fallback).sum()),
        "unavailable": int((~finite).sum()),
    }


def score(rows):
    frozen.key_set(rows)
    metrics = {}
    for arm in ARMS:
        valid = np.isfinite(rows[arm]) & np.isfinite(rows.pir_per36_dest)
        metrics[arm] = {
            "n_scored": int(valid.sum()),
            "mae": float(np.abs(rows[arm] - rows.pir_per36_dest).mean())
            if valid.all()
            else None,
            "refusals": rows.loc[~valid, f"{arm}_status"].value_counts().to_dict(),
        }
    increments = {}
    for arm in ARMS[::2]:
        a, b = metrics[arm]["mae"], metrics[arm + "_scheduled"]["mae"]
        increments[arm] = None if a is None or b is None else a - b
    return {
        "status": "complete_target"
        if all(m["n_scored"] == len(rows) for m in metrics.values())
        else "incomplete_target",
        "support": support_counts(rows),
        "metrics": metrics,
        "increments": increments,
        "by_season": {
            str(k): support_counts(g) for k, g in rows.groupby("season_dest")
        },
        "by_destination": {
            str(k): support_counts(g) for k, g in rows.groupby("league_dest")
        },
    }


def distribution(values):
    good = [v for v in values if v is not None]
    return {
        "planned": len(values),
        "available": len(good),
        **(
            dict(
                zip(
                    ("minimum", "q025", "median", "q975", "maximum"),
                    map(float, np.quantile(good, [0, 0.025, 0.5, 0.975, 1])),
                    strict=True,
                )
            )
            if good
            else {}
        ),
    }


def aggregate(records, references):
    expected = {
        f"{control}/{i:03d}" for control in CONTROLS for i in range(REPETITIONS)
    }
    if set(records) != expected:
        raise ValueError("incomplete repetition inventory")
    result = {}
    for control in CONTROLS:
        reports = [records[f"{control}/{i:03d}"] for i in range(REPETITIONS)]
        result[control] = {
            "repetitions": len(reports),
            "incomplete_targets": [
                i for i, r in enumerate(reports) if r["status"] != "complete_target"
            ],
            "support": {
                k: distribution([r["support"][k] for r in reports])
                for k in ("nonfallback", "fallback", "unavailable")
            },
            "mae": {
                arm: distribution([r["metrics"][arm]["mae"] for r in reports])
                for arm in ARMS
            },
            "change_from_full": {
                arm: distribution(
                    [
                        None
                        if r["metrics"][arm]["mae"] is None
                        else r["metrics"][arm]["mae"]
                        - references["full"]["metrics"][arm]["mae"]
                        for r in reports
                    ]
                )
                for arm in ARMS
            },
            "increments": {
                arm: distribution([r["increments"][arm] for r in reports])
                for arm in ARMS[::2]
            },
        }
    return result


def prepare_snapshot(inputs, refits, slopes, archive):
    manifest, hashes = frozen.verify_inputs(inputs, refits)
    frozen.check_outputs(slopes)
    roots = {"inputs": inputs, "refits": refits, "v9": frozen.DIAGNOSTICS.parent}
    paths = {
        name: roots[name.split("/", 1)[0]] / name.split("/", 1)[1] for name in hashes
    }
    saved = read(slopes / "summary.json")
    for name, digest in saved["output_hashes"].items():
        if "/reference/" in name:
            paths[f"slopes/{name}"] = slopes / name
            hashes[f"slopes/{name}"] = digest
    for name in ("summary.json", "manifest.json", "status.json"):
        paths[f"slopes/{name}"] = slopes / name
        hashes[f"slopes/{name}"] = sha256_file(slopes / name)
    for name in (*CODE_FILES, PROTOCOL):
        paths[f"source/{name}"] = ROOT / name
        hashes[f"source/{name}"] = sha256_file(ROOT / name)
    snapshot, receipt = snapshot_inputs(paths, hashes, archive)
    return snapshot, receipt, manifest


def write_run(directory, features, rows, fits, cutoffs, chosen, fingerprint):
    directory.mkdir(parents=True, exist_ok=False)
    features.to_parquet(directory / "features.parquet", index=False)
    rows.to_parquet(directory / "predictions.parquet", index=False)
    dump(directory / "fits.json", {"folds": fits, "cutoffs": cutoffs})
    dump(directory / "sample-keys.json", [list(k) for k in sorted(chosen)])
    report = score(rows)
    dump(directory / "summary.json", report)
    dump(
        directory / "complete.json",
        {
            "fingerprint": fingerprint,
            "files": {name: sha256_file(directory / name) for name in FILES},
        },
    )
    return report


def cached_run(directory, fingerprint):
    if not directory.exists():
        return None
    if {p.name for p in directory.iterdir()} != {*FILES, "complete.json"}:
        raise ValueError("incomplete cached run")
    complete = read(directory / "complete.json")
    if complete["fingerprint"] != fingerprint or set(complete["files"]) != set(FILES):
        raise ValueError("changed cache fingerprint or inventory")
    for name, digest in complete["files"].items():
        frozen.refit._check(directory / name, digest)
    report = score(pd.read_parquet(directory / "predictions.parquet"))
    frozen.benchmark._equivalent(report, read(directory / "summary.json"))
    return report


def report_text(summary):
    def interval(value, digits=1):
        if not value["available"]:
            return "unavailable"
        return f"{value['median']:.{digits}f} [{value['q025']:.{digits}f}, {value['q975']:.{digits}f}]"

    lines = [
        "# Registered support-restriction diagnostic",
        "",
        "## Specification",
        "",
        "| Field | Declaration |",
        "| --- | --- |",
        "| Unit | Restricted pair sample on the same 674 forecast keys |",
        "| Estimator | Two controls, 200 repetitions each; frozen fitting procedure |",
        "| Uncertainty | Empirical restriction quantiles, not confidence intervals |",
        "| Decision | Exploratory diagnosis; no randomized verification effect |",
        "",
        "Median and empirical 2.5th/97.5th percentiles below. MAE and increments use source-offset penalty 10. Positive increment favors translation. All penalties, failures, full ranges and keyed outputs are retained.",
        "",
        "| Pool/control | Nonfallback / 674 | MAE with translation | Translation increment | Complete repetitions |",
        "| --- | --- | --- | --- | --- |",
    ]
    for name, r in summary["references"].items():
        lines.append(
            f"| {name} | {r['support']['nonfallback']} | {r['metrics']['source_ridge_10_scheduled']['mae']:.3f} | {r['increments']['source_ridge_10']:+.3f} | reference |"
        )
    for name, r in summary["controls"].items():
        lines.append(
            f"| {name} | {interval(r['support']['nonfallback'])} | {interval(r['mae']['source_ridge_10_scheduled'], 3)} | {interval(r['increments']['source_ridge_10'], 3)} | {r['repetitions'] - len(r['incomplete_targets'])}/{r['repetitions']} |"
        )
    lines.extend(
        [
            "",
            "These restrictions are conditional on the observed pool and inherited estimator. Verified rows were not randomized. Values inside these ranges are attainable under the declared restriction; this does not establish that sample loss caused the observed verification result. Successful-repetition loss summaries are conditional if any target is incomplete.",
            "",
        ]
    )
    return "\n".join(lines)


def run(inputs, refits, slopes, out, archive):
    inputs, refits, slopes, out, archive = map(
        lambda p: Path(p).resolve(), (inputs, refits, slopes, out, archive)
    )
    for protected in (inputs, refits, slopes, archive):
        if out == protected or out in protected.parents or protected in out.parents:
            raise ValueError("output overlaps retained inputs")
    snapshot, receipt, original = prepare_snapshot(inputs, refits, slopes, archive)
    manifest = {
        "input_receipt": receipt,
        "controls": CONTROLS,
        "repetitions": REPETITIONS,
        "seed": BASE_SEED,
        "factor_bootstrap": 2000,
        "factor_seed": 0,
        "arms": list(ARMS),
        "runtime": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "pandas": pd.__version__,
        },
    }
    frozen.refit._preflight_output(out, manifest)
    dump(out / "manifest.json", manifest)
    dump(out / "status.json", {"status": "running"})
    try:
        a, cohort, _ = frozen.refit.load_variant(snapshot / "inputs/official_corrected")
        b, b_cohort, _ = frozen.refit.load_variant(
            snapshot / "inputs/verified_same_club_full"
        )
        validate_pools(a, b)
        pd.testing.assert_frame_equal(cohort, b_cohort, check_exact=True)
        target = {tuple(k) for k in original["reference_keys"]}
        reference_folds = read(
            snapshot / "refits/official_corrected/reference/fits.json"
        )["folds"]
        references, records = {}, {}
        fingerprint = frozen.refit._digest(manifest)
        with threadpool_limits(limits=1):
            for label, pool, variant in (
                ("full", a, "official_corrected"),
                ("verified", b, "verified_same_club_full"),
            ):
                dest = out / "references" / label
                report = cached_run(dest, fingerprint)
                if report is None:
                    features, cutoffs = frozen.refit.refit_features(pool, cohort)
                    audit = read(snapshot / f"refits/{variant}/reference/fits.json")
                    frozen.benchmark._equivalent(
                        json.loads(json.dumps(cutoffs)), audit["cutoffs"]
                    )
                    for left, right in zip(
                        reference_folds, audit["folds"], strict=True
                    ):
                        if left["train_keys"] != right["train_keys"]:
                            raise ValueError("reference training keys differ")
                    rows, fits = fit_predictions(features, reference_folds, target)
                    for folder, arms in (("refits", ARMS[:6]), ("slopes", ARMS[6:])):
                        saved = frozen.select(
                            pd.read_parquet(
                                snapshot
                                / f"{folder}/{variant}/reference/predictions.parquet"
                            ),
                            target,
                        ).sort_values(KEY)
                        np.testing.assert_allclose(
                            rows.sort_values(KEY)[list(arms)],
                            saved[list(arms)],
                            atol=1e-9,
                            rtol=0,
                        )
                    report = write_run(
                        dest,
                        features,
                        rows,
                        fits,
                        cutoffs,
                        frozen.diagnostics.keys(pool, PAIR_KEY),
                        fingerprint,
                    )
                references[label] = report
                print(f"Reference {label}: reproduced", flush=True)
            for control in CONTROLS:
                for i in range(REPETITIONS):
                    name = f"{control}/{i:03d}"
                    dest = out / "restrictions" / name
                    report = cached_run(dest, fingerprint)
                    if report is None:
                        chosen = sample_keys(a, b, control, i)
                        features, cutoffs = frozen.refit.refit_features(
                            restrict_pairs(a, chosen), cohort
                        )
                        rows, fits = fit_predictions(features, reference_folds, target)
                        report = write_run(
                            dest, features, rows, fits, cutoffs, chosen, fingerprint
                        )
                    records[name] = report
                    dump(
                        out / "status.json",
                        {"status": "running", "completed": len(records)},
                    )
                    if (i + 1) % 10 == 0:
                        print(f"{control}: {i + 1}/{REPETITIONS}", flush=True)
        verify_snapshot(snapshot, receipt["inputs"])
        summary = {
            "status": "complete",
            "manifest_sha256": sha256_file(out / "manifest.json"),
            "references": references,
            "controls": aggregate(records, references),
            "records": records,
            "interpretation": "Conditional restriction ranges, not confidence intervals or verification effects.",
        }
        summary["output_hashes"] = {
            str(p.relative_to(out)): sha256_file(p)
            for parent in (out / "references", out / "restrictions")
            for p in sorted(parent.rglob("*"))
            if p.is_file()
        }
        dump(out / "summary.json", summary)
        (out / "results.md").write_text(report_text(summary))
        dump(
            out / "status.json",
            {
                "status": "complete",
                "summary_sha256": sha256_file(out / "summary.json"),
                "results_sha256": sha256_file(out / "results.md"),
            },
        )
        return summary
    except Exception as exc:
        dump(
            out / "status.json",
            {"status": "failed", "error": f"{type(exc).__name__}: {exc}"},
        )
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("inputs", "refits", "slopes", "out", "archive"):
        parser.add_argument(f"--{name}", type=Path, required=True)
    args = parser.parse_args()
    run(args.inputs, args.refits, args.slopes, args.out, args.archive)


if __name__ == "__main__":
    main()
