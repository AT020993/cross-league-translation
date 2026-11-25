"""Registered full model refits conditional on historical player measurements.

Threats: stale upstream fits (pristine keyed replay); omitted/future estimation
labels re-enter lag or regression (separate fitting/evaluation); changing support
(hidden refusals); numerical randomness (fixed-depth seed sensitivity); stale or
partial caches (complete hash manifests). No future-accuracy interval is claimed.
"""

from __future__ import annotations

import argparse
from concurrent.futures import ProcessPoolExecutor
import hashlib
import json
import os
import re
from pathlib import Path
import shutil
import sys
import time

for _name in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[_name] = "1"
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from threadpoolctl import threadpool_limits  # noqa: E402

from scripts import compare_translation_designs as design  # noqa: E402
from scripts import revalidate_sloan_sources as source  # noqa: E402
from scripts import sloan_context_benchmarks as benchmark  # noqa: E402
from scripts import sloan_revision_analysis as revision  # noqa: E402
from scripts.translation_research_common import fit_table, sha256_file  # noqa: E402

KEY = revision.KEY
ARMS = benchmark.ARMS
PROTOCOL = (
    ROOT / "docs/research/sloan-evidence-completion-preregistration-2026-09-17.md"
)
CODE_FILES = (
    "scripts/sloan_full_refit.py",
    "scripts/compare_translation_designs.py",
    "scripts/translation_research_common.py",
    "scripts/build_league_factors.py",
    "scripts/validate_translation_walkforward.py",
    "scripts/sloan_revision_analysis.py",
    "scripts/sloan_context_benchmarks.py",
    "scripts/revalidate_sloan_sources.py",
)
CONVENTION = (
    "Full factor, pooling, lag and regression refits conditional on measured "
    "source/prior rates, fixed eligibility and reused historical seasons. "
    "Deleting estimation season s does not delete every measurement from s. "
    "Input row order is hash-bound; factor bootstrap streams retain historical "
    "first-occurrence cluster order. Regression/output keys are sorted. "
    "Influence and seed ranges are not calibrated future confidence intervals."
)


def _json(path, value):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    design.dump_json(path, value)


def _check(path, expected):
    path = Path(path)
    if not path.is_file() or sha256_file(path) != expected:
        raise ValueError(f"fingerprint mismatch: {path}")


def _digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def _keys(rows):
    return set(map(tuple, rows[KEY].to_numpy()))


def _select(rows, keys):
    return rows.loc[[tuple(key) in keys for key in rows[KEY].to_numpy()]].copy()


def _variant_path(root, name):
    if (
        not isinstance(name, str)
        or re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]*", name) is None
    ):
        raise ValueError("invalid variant name")
    return benchmark._safe_child(Path(root).resolve(), name)


def _preflight_output(output, manifest):
    """Never change unrelated or incompatible artifacts, even their status."""
    output = Path(output)
    if not output.exists() or not any(output.iterdir()):
        return
    if (
        not (output / "manifest.json").is_file()
        or not (output / "status.json").is_file()
    ):
        raise ValueError("nonempty output is not a recognized refit run")
    old = json.loads((output / "manifest.json").read_text())
    if old != json.loads(json.dumps(manifest)):
        raise ValueError("run manifest changed; use a new versioned output directory")
    state = json.loads((output / "status.json").read_text())
    if state.get("status") not in ("running", "failed", "complete"):
        raise ValueError("invalid existing refit status")
    if state["status"] == "complete":
        _check(output / "summary.json", state.get("summary_sha256"))


def restore_originals(source_run, revision_dir, output):
    """Restore retained input bytes and independently verify cohort equivalence."""
    source_run, revision_dir, output = map(Path, (source_run, revision_dir, output))
    summary = json.loads((revision_dir / "summary.json").read_text())
    state = json.loads((revision_dir / "status.json").read_text())
    if state.get("status") != "complete":
        raise ValueError("historical revision is incomplete")
    _check(revision_dir / "summary.json", state["summary_sha256"])
    expected = summary["historical_inventory"]["variants"]
    if set(expected) != set(source.VARIANTS):
        raise ValueError("historical variant inventory is incomplete")
    recovered, pending = {}, []
    for variant in source.VARIANTS:
        target = _variant_path(output, variant)
        records, hashes = {}, {}
        for name, digest in expected[variant]["hashes"].items():
            if name not in ("pairs.parquet", "switchers.parquet"):
                raise ValueError("unexpected original input filename")
            old, new = source_run / "inputs" / variant / name, target / name
            _check(old, digest)
            hashes[name] = digest
            records[name] = {
                "source": str(old.resolve()),
                "destination": str(new.resolve()),
                "expected_sha256": digest,
                "actual_sha256": sha256_file(old),
                "action": "restored_verified_bytes",
            }
        ledger_path = revision_dir / variant / "cohort_ledger.parquet"
        _check(
            ledger_path, summary["output_hashes"][f"{variant}/cohort_ledger.parquet"]
        )
        ledger = pd.read_parquet(ledger_path)
        cohort = ledger.loc[ledger.original_eligible].copy().reset_index(drop=True)
        original = source_run / "inputs" / variant
        pairs = pd.read_parquet(original / "pairs.parquet")
        switchers = pd.read_parquet(original / "switchers.parquet")
        _, prepared, _ = design.prepare(pairs, switchers)
        equality = source.keyed_equal(
            cohort[switchers.columns], prepared[switchers.columns], KEY
        )
        cohort_bytes = cohort.to_parquet(index=False)
        hashes["cohort.parquet"] = hashlib.sha256(cohort_bytes).hexdigest()
        record = {
            "schema_version": 1,
            "status": "prepared",
            "variant": variant,
            "reference_variant": variant,
            "files": hashes,
            "recovery": records,
            "cohort_reconstruction": equality,
            "cohort_source": str(ledger_path.resolve()),
            "cohort_source_sha256": sha256_file(ledger_path),
            "ordering": "Original pair bytes and frozen original-eligible ledger order",
        }
        if target.exists() and any(target.iterdir()):
            if not (target / "variant.json").is_file():
                raise ValueError("nonempty restore target is not a recognized variant")
            existing = json.loads((target / "variant.json").read_text())
            if existing != record or {p.name for p in target.iterdir()} != {
                *hashes,
                "variant.json",
            }:
                raise ValueError("incompatible existing restored variant")
            for name, digest in hashes.items():
                _check(target / name, digest)
        pending.append((target, original, cohort_bytes, record))
        recovered[variant] = record
    manifest = {
        "schema_version": 1,
        "status": "complete",
        "source_run": str(source_run.resolve()),
        "revision_summary_sha256": sha256_file(revision_dir / "summary.json"),
        "variants": recovered,
    }
    if (output / "recovery-manifest.json").exists() and json.loads(
        (output / "recovery-manifest.json").read_text()
    ) != manifest:
        raise ValueError("incompatible recovery manifest")
    # All protected paths pass before the first write.
    for target, original, cohort_bytes, record in pending:
        target.mkdir(parents=True, exist_ok=True)
        for name in ("pairs.parquet", "switchers.parquet"):
            if not (target / name).exists():
                shutil.copyfile(original / name, target / name)
        if not (target / "cohort.parquet").exists():
            (target / "cohort.parquet").write_bytes(cohort_bytes)
        if not (target / "variant.json").exists():
            _json(target / "variant.json", record)
    _json(output / "recovery-manifest.json", manifest)
    return manifest


def load_variant(directory):
    directory = Path(directory).resolve()
    meta = json.loads((directory / "variant.json").read_text())
    if meta.get("status") != "prepared":
        raise ValueError(f"unprepared variant: {directory}")
    if not {"pairs.parquet", "cohort.parquet"}.issubset(meta.get("files", {})):
        raise ValueError("missing required variant inputs")
    for name, expected in meta["files"].items():
        _check(benchmark._safe_child(directory, name), expected)
    pairs, cohort = [
        pd.read_parquet(directory / name)
        for name in ("pairs.parquet", "cohort.parquet")
    ]
    revision.unique(pairs, ["player_name", "season"])
    revision.unique(cohort)
    if not cohort.league_dest.isin(("euroleague", "eurocup")).all():
        raise ValueError("invalid destination category")
    if cohort.league_src.isna().any() or cohort.league_src.eq("").any():
        raise ValueError("missing source category")
    if not np.isfinite(cohort[["pir_per36_src", "pir_per36_dest"]]).all().all():
        raise ValueError("nonfinite measured rates")
    return pairs, cohort, meta


def scenario_matrix(seasons):
    years = sorted({int(s) for s in seasons if int(s) < max(design.SEASONS)})
    return [
        {"name": "reference", "omitted_season": None, "seed": 0},
        *[{"name": f"omit_{s}", "omitted_season": s, "seed": 0} for s in years],
        *[
            {"name": f"seed_{s}", "omitted_season": None, "seed": s}
            for s in range(1, 5)
        ],
    ]


def refit_features(
    pairs, cohort, *, omitted_season=None, seed=0, n_boot=2000, fitter=fit_table
):
    """Every row keeps its cutoff; only estimation records are omitted."""
    revision.unique(pairs, ["player_name", "season"])
    revision.unique(cohort)
    estimation = cohort.loc[cohort.season_dest.ne(omitted_season)].copy()
    retained_pairs = pairs.loc[pairs.season.ne(omitted_season)].copy()
    study = design.Study(
        retained_pairs, estimation, seed=seed, n_boot=n_boot, fitter=fitter
    )
    rows = cohort.copy().reset_index(drop=True)
    for season, group in rows.groupby("season_dest", sort=True):
        earlier = estimation.loc[estimation.season_dest.lt(season)]
        tables = study.at(int(season))
        for kind, table in tables.items():
            multiplier, fallback, reliable = design.lookup(table, group)
            old_multiplier, _, _ = design.lookup(table, earlier)
            denominator = earlier.pir_per36_src.to_numpy() * old_multiplier
            valid = np.isfinite(denominator) & (denominator > 0)
            lag = (
                float(
                    np.median(
                        earlier.pir_per36_dest.to_numpy()[valid] / denominator[valid]
                    )
                )
                if valid.any()
                else np.nan
            )
            for name, value in (
                ("multiplier_value", multiplier),
                ("fallback", fallback),
                ("reliable", reliable),
                ("k", lag),
                ("translated", group.pir_per36_src.to_numpy() * multiplier * lag),
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
            factor_rows = (
                retained_pairs.loc[retained_pairs.season.lt(season)]
                if kind == "scheduled"
                else earlier
            )
            factor_season = "season" if kind == "scheduled" else "season_dest"
            info = study.diagnostics[int(season)][kind]
            info.update(
                k=lag,
                lag_eligible=int(valid.sum()),
                lag_excluded=int((~valid).sum()),
                lag_keys=revision.key_list(earlier.loc[valid]),
                factor_season_counts={
                    str(int(k)): int(v)
                    for k, v in factor_rows[factor_season]
                    .value_counts()
                    .sort_index()
                    .items()
                },
            )
            if omitted_season is not None and (
                factor_rows[factor_season].eq(omitted_season).any()
                or earlier.season_dest.eq(omitted_season).any()
            ):
                raise ValueError("omitted estimation season re-entered factors or lag")
    rows["feature_eligible"] = np.isfinite(
        rows[[f"{d}_translated" for d in design.DESIGNS]]
    ).all(axis=1)
    return rows, study.diagnostics


def fit_refit_predictions(features, *, omitted_season=None, seasons=design.SEASONS):
    output, folds = [], []
    for season in seasons:
        train = features.loc[
            features.season_dest.lt(season)
            & features.season_dest.ne(omitted_season)
            & features.feature_eligible
        ].sort_values(KEY)
        test = features.loc[features.season_dest.eq(season)].sort_values(KEY).copy()
        support = test.feature_eligible
        fold = {
            "season": int(season),
            "train_keys": revision.key_list(train),
            "arms": {},
        }
        for arm in ARMS:
            test[arm] = np.nan
            prediction, diagnostic = benchmark.fit_model(train, test.loc[support], arm)
            test.loc[support, arm] = prediction
            test[f"{arm}_status"] = np.where(
                support, diagnostic["status"], "feature_refusal"
            )
            fold["arms"][arm] = diagnostic
        test["scored"] = np.isfinite(test[list(ARMS)]).all(axis=1)
        test["scoring_exclusion"] = ""
        for kind in design.DESIGNS:
            mask = test.scoring_exclusion.eq("") & test[f"{kind}_reason"].ne("")
            test.loc[mask, "scoring_exclusion"] = test.loc[mask, f"{kind}_reason"]
        for arm in ARMS:
            mask = test.scoring_exclusion.eq("") & test[f"{arm}_status"].ne("ok")
            test.loc[mask, "scoring_exclusion"] = test.loc[mask, f"{arm}_status"]
        if ((~test.scored) & test.scoring_exclusion.eq("")).any():
            raise ValueError("unexplained unscorable forecast")
        fold["common_scoring_keys"] = revision.key_list(test.loc[test.scored])
        fold["scoring_exclusions"] = test.scoring_exclusion.value_counts().to_dict()
        output.append(test)
        folds.append(fold)
    return pd.concat(output, ignore_index=True), folds


def execute_scenario(
    pairs, cohort, scenario, *, fitter=fit_table, n_boot=2000, seasons=design.SEASONS
):
    features, cutoffs = refit_features(
        pairs,
        cohort,
        omitted_season=scenario["omitted_season"],
        seed=scenario["seed"],
        n_boot=n_boot,
        fitter=fitter,
    )
    rows, folds = fit_refit_predictions(
        features, omitted_season=scenario["omitted_season"], seasons=seasons
    )
    return rows, {"folds": folds, "cutoffs": cutoffs}, features


def verify_reference(features, rows, audit, variant, revision_dir, reference_dir):
    """Refuse changed upstream cells, historical features, masks or v7 forecasts."""
    revision_dir, reference_dir = Path(revision_dir), Path(reference_dir)
    old = pd.read_parquet(revision_dir / variant / "original/predictions.parquet")
    old_audit = json.loads((revision_dir / variant / "original/folds.json").read_text())
    benchmark.reproduce_historical(features, old, old_audit)
    for cutoff, old_cutoff in old_audit["cutoffs"].items():
        current = audit["cutoffs"][int(cutoff)]
        for kind in design.DESIGNS:
            a, z = (
                pd.DataFrame(current[kind]["cells"]),
                pd.DataFrame(old_cutoff[kind]["cells"]),
            )
            if len(z):
                source.keyed_equal(a, z, ["league", "destination"])
            elif len(a):
                raise ValueError("formerly empty factor cutoff changed")
            np.testing.assert_allclose(
                current[kind]["k"],
                np.nan if old_cutoff[kind]["k"] is None else old_cutoff[kind]["k"],
                atol=1e-9,
                rtol=0,
                equal_nan=True,
            )
    expected = pd.read_parquet(reference_dir / variant / "predictions.parquet")
    columns = [
        *KEY,
        "pir_per36_dest",
        "pir_per36_src",
        "prior_mean_pir36",
        "above_own_prior",
        "scheduled_translated",
        "transfer_translated",
        *ARMS,
        "scored",
    ]
    source.keyed_equal(rows[columns], expected[columns], KEY)
    old_folds = json.loads((reference_dir / variant / "folds.json").read_text())[
        "folds"
    ]
    if [f["train_keys"] for f in audit["folds"]] != [
        f["train_keys"] for f in old_folds
    ]:
        raise ValueError("v7 regression training keys changed")
    return {
        "status": "reproduced",
        "tolerance": 1e-9,
        "rows": len(rows),
        "scored": int(rows.scored.sum()),
        "factor_cutoffs": len(old_audit["cutoffs"]),
        "reference_variant": variant,
    }


def summarize_scenario(rows, reference_keys):
    common = _select(rows, reference_keys)
    scored_keys = _keys(rows.loc[rows.scored])
    return {
        "native": benchmark.summarize(rows),
        "original_common": benchmark.summarize(common),
        "reference_target_n": len(reference_keys),
        "reference_target_missing": len(reference_keys - _keys(rows)),
        "reference_target_unscored": len(reference_keys - scored_keys),
        "scored_key_sha256": _digest(revision.key_list(rows.loc[rows.scored])),
        "refusals": rows.scoring_exclusion.value_counts().to_dict(),
        "fallbacks": {d: int(rows[f"{d}_fallback"].sum()) for d in design.DESIGNS},
        "per_season": {
            str(int(s)): benchmark.summarize(g, breakdown=False)
            for s, g in rows.groupby("season_dest")
        },
    }


def _cached(directory, fingerprint):
    directory = Path(directory)
    done = json.loads((directory / "complete.json").read_text())
    if done.get("fingerprint") != fingerprint or set(done.get("files", {})) != {
        "predictions.parquet",
        "fits.json",
        "summary.json",
    }:
        raise ValueError(f"incomplete or stale cache: {directory}")
    for name, expected in done["files"].items():
        _check(directory / name, expected)
    return pd.read_parquet(directory / "predictions.parquet"), json.loads(
        (directory / "summary.json").read_text()
    )


def _job(job):
    with threadpool_limits(limits=1):
        pairs, cohort, meta = load_variant(job["input_dir"])
        directory = Path(job["output_dir"])
        fingerprint = job["fingerprint"]
        if (directory / "complete.json").exists():
            _, report = _cached(directory, fingerprint)
            return report
        if directory.exists() and any(directory.iterdir()):
            raise ValueError(f"incomplete scenario directory: {directory}")
        directory.mkdir(parents=True, exist_ok=True)
        start = time.monotonic()
        rows, audit, features = execute_scenario(pairs, cohort, job["scenario"])
        reference = None
        if job["scenario"]["name"] == "reference" and meta.get("reference_variant"):
            reference = verify_reference(
                features,
                rows,
                audit,
                meta["reference_variant"],
                job["revision_dir"],
                job["reference_dir"],
            )
        report = {
            "variant": meta["variant"],
            "scenario": job["scenario"],
            "reference_reproduction": reference,
            "elapsed_seconds": time.monotonic() - start,
            **summarize_scenario(rows, {tuple(k) for k in job["reference_keys"]}),
        }
        rows.to_parquet(directory / "predictions.parquet", index=False)
        _json(directory / "fits.json", audit)
        _json(directory / "summary.json", report)
        _json(
            directory / "complete.json",
            {
                "fingerprint": fingerprint,
                "files": {
                    n: sha256_file(directory / n)
                    for n in ("predictions.parquet", "fits.json", "summary.json")
                },
            },
        )
        return report


def ranges(reports):
    result = {}
    for group, chosen in (
        ("sample_influence", [r for r in reports if r["scenario"]["seed"] == 0]),
        (
            "monte_carlo",
            [r for r in reports if r["scenario"]["omitted_season"] is None],
        ),
    ):
        entries = {}
        for contrast in benchmark.contrast_pairs():
            values = {
                r["scenario"]["name"]: r["original_common"]["contrasts"][contrast][
                    "player_club_season"
                ]["difference"]
                for r in chosen
            }
            finite = [v for v in values.values() if v is not None]
            entries[contrast] = {
                "values": values,
                "range": [min(finite), max(finite)] if finite else None,
                "direction_changes": bool(finite and min(finite) <= 0 <= max(finite)),
            }
        result[group] = {
            "scenarios": [r["scenario"]["name"] for r in chosen],
            "contrasts": entries,
            "support_changes": len({r["scored_key_sha256"] for r in chosen}) > 1,
            "fallback_changes": len({_digest(r["fallbacks"]) for r in chosen}) > 1,
            "scope": "Descriptive range, not a confidence interval",
        }
    return result


def fixed_scenario_support(output, variant, scenarios):
    """All declared scenarios determine support before any influence range."""
    frames = {
        s["name"]: pd.read_parquet(
            Path(output) / variant / s["name"] / "predictions.parquet"
        )
        for s in scenarios
    }
    common = set.intersection(
        *[_keys(rows.loc[rows.scored]) for rows in frames.values()]
    )
    reports = []
    for scenario in scenarios:
        rows = _select(frames[scenario["name"]], common)
        reports.append(
            {
                "scenario": scenario,
                "original_common": benchmark.summarize(rows),
                "scored_key_sha256": _digest(sorted(common)),
                "fallbacks": {
                    d: int(rows[f"{d}_fallback"].sum()) for d in design.DESIGNS
                },
            }
        )
    return {
        "n": len(common),
        "status": "ok" if common else "not_estimable",
        "keys_sha256": _digest(sorted(common)),
        "definition": (
            "Intersection of scored keys over every declared scenario for this variant"
        ),
        "scenarios": {r["scenario"]["name"]: r["original_common"] for r in reports},
        "ranges": ranges(reports),
    }


def _reference_inventory(revision_dir, reference_dir):
    """Pin every verified historical dependency, including each package manifest."""
    revision_dir, reference_dir = Path(revision_dir), Path(reference_dir)
    verified = benchmark.verify_source(revision_dir)
    revision_hashes = {}
    for name, digest in verified.items():
        path = Path(name)
        if not path.is_absolute():
            path = benchmark.ROOT / path
        revision_hashes[str(path.resolve().relative_to(revision_dir.resolve()))] = (
            digest
        )
    state = json.loads((reference_dir / "status.json").read_text())
    if state.get("status") != "complete":
        raise ValueError("v7 benchmark is incomplete")
    _check(reference_dir / "summary.json", state["summary_sha256"])
    summary = json.loads((reference_dir / "summary.json").read_text())
    required = {
        f"{variant}/{name}"
        for variant in source.VARIANTS
        for name in ("predictions.parquet", "folds.json")
    }
    if not required.issubset(summary.get("output_hashes", {})):
        raise ValueError("v7 benchmark dependency inventory is incomplete")
    reference_hashes = {
        name: sha256_file(reference_dir / name)
        for name in ("summary.json", "status.json")
    }
    for name, digest in summary["output_hashes"].items():
        _check(benchmark._safe_child(reference_dir, name), digest)
        reference_hashes[name] = digest
    return {"revision": revision_hashes, "benchmark": reference_hashes}


def _check_reference_inventory(revision_dir, reference_dir, inventory):
    for kind, root in (("revision", revision_dir), ("benchmark", reference_dir)):
        for name, expected in inventory[kind].items():
            _check(benchmark._safe_child(Path(root), name), expected)


def run(input_root, revision_dir, reference_dir, output, *, variants, workers=1):
    if workers not in (1, 2):
        raise ValueError("workers must be one or two")
    input_root, revision_dir, reference_dir, output = map(
        lambda p: Path(p).resolve(), (input_root, revision_dir, reference_dir, output)
    )
    if (
        output == input_root
        or output in input_root.parents
        or input_root in output.parents
    ):
        raise ValueError("model outputs and inputs must be separate trees")
    started = False
    try:
        reference_dependencies = _reference_inventory(revision_dir, reference_dir)
        reference_sets = []
        for variant in source.VARIANTS:
            rows = pd.read_parquet(reference_dir / variant / "predictions.parquet")
            reference_sets.append(_keys(rows.loc[rows.scored]))
        target_keys = set.intersection(*reference_sets)
        code = {name: sha256_file(ROOT / name) for name in CODE_FILES}
        inputs, years = {}, set()
        for variant in variants:
            pairs, cohort, meta = load_variant(_variant_path(input_root, variant))
            if meta["variant"] != variant:
                raise ValueError("variant name/path mismatch")
            years.update(map(int, pairs.season.unique()))
            years.update(map(int, cohort.season_dest.unique()))
            inputs[variant] = {
                "metadata_sha256": sha256_file(input_root / variant / "variant.json"),
                "files": meta["files"],
            }
        scenarios = scenario_matrix(years)
        manifest = {
            "schema_version": 1,
            "protocol_sha256": sha256_file(PROTOCOL),
            "code_hashes": code,
            "inputs": inputs,
            "input_root": str(input_root),
            "factor_bootstrap": 2000,
            "outer_seasons": list(design.SEASONS),
            "scenarios": scenarios,
            "observed_estimation_seasons": sorted(years),
            "variants": list(variants),
            "reference_keys": sorted(target_keys),
            "reference_summary_sha256": reference_dependencies["benchmark"][
                "summary.json"
            ],
            "revision_summary_sha256": reference_dependencies["revision"][
                "summary.json"
            ],
            "reference_dependency_hashes": reference_dependencies,
            "revision_dir": str(revision_dir),
            "reference_dir": str(reference_dir),
            "convention": CONVENTION,
        }
        _preflight_output(output, manifest)
        output.mkdir(parents=True, exist_ok=True)
        _json(output / "manifest.json", manifest)
        _json(output / "status.json", {"status": "running"})
        started = True
        jobs = [
            {
                "input_dir": str(input_root / variant),
                "output_dir": str(output / variant / scenario["name"]),
                "scenario": scenario,
                "fingerprint": _digest(
                    {"manifest": manifest, "variant": variant, "scenario": scenario}
                ),
                "revision_dir": str(revision_dir),
                "reference_dir": str(reference_dir),
                "reference_keys": sorted(target_keys),
            }
            for variant in variants
            for scenario in scenarios
        ]
        reports = []
        # Every pristine reference gate passes before any perturbation is run.
        for job in [j for j in jobs if j["scenario"]["name"] == "reference"]:
            report = _job(job)
            reports.append(report)
            print(
                json.dumps(
                    {
                        "variant": report["variant"],
                        "scenario": "reference",
                        "reproduction": report["reference_reproduction"],
                        "seconds": report["elapsed_seconds"],
                    }
                ),
                flush=True,
            )
        remaining = [j for j in jobs if j["scenario"]["name"] != "reference"]
        if workers == 1:
            iterator = map(_job, remaining)
            for report in iterator:
                reports.append(report)
                print(
                    json.dumps(
                        {
                            "variant": report["variant"],
                            "scenario": report["scenario"]["name"],
                            "seconds": report["elapsed_seconds"],
                        }
                    ),
                    flush=True,
                )
        else:
            with ProcessPoolExecutor(max_workers=workers) as pool:
                for report in pool.map(_job, remaining):
                    reports.append(report)
                    print(
                        json.dumps(
                            {
                                "variant": report["variant"],
                                "scenario": report["scenario"]["name"],
                                "seconds": report["elapsed_seconds"],
                            }
                        ),
                        flush=True,
                    )
        summary = {
            "schema_version": 1,
            "status": "complete",
            "convention": CONVENTION,
            "manifest_sha256": sha256_file(output / "manifest.json"),
            "scenario_count": len(reports),
            "expected_scenario_count": len(jobs),
            "reference_target_n": len(target_keys),
            "variants": {
                v: {
                    "scenarios": {
                        r["scenario"]["name"]: r for r in reports if r["variant"] == v
                    },
                    "ranges": ranges([r for r in reports if r["variant"] == v]),
                    "fixed_scenario_support": fixed_scenario_support(
                        output, v, scenarios
                    ),
                }
                for v in variants
            },
            "output_hashes": {
                str((Path(j["output_dir"]) / n).relative_to(output)): sha256_file(
                    Path(j["output_dir"]) / n
                )
                for j in jobs
                for n in (
                    "predictions.parquet",
                    "fits.json",
                    "summary.json",
                    "complete.json",
                )
            },
        }
        if len(reports) != len(jobs):
            raise ValueError("incomplete scenario matrix")
        # Recheck every input and executable file before publishing a complete state.
        for variant in variants:
            load_variant(_variant_path(input_root, variant))
            _check(
                input_root / variant / "variant.json",
                inputs[variant]["metadata_sha256"],
            )
        for name, expected in code.items():
            _check(ROOT / name, expected)
        _check(PROTOCOL, manifest["protocol_sha256"])
        _check_reference_inventory(revision_dir, reference_dir, reference_dependencies)
        _json(output / "summary.json", summary)
        _json(
            output / "status.json",
            {
                "status": "complete",
                "summary_sha256": sha256_file(output / "summary.json"),
            },
        )
        return summary
    except Exception as exc:
        if started:
            _json(
                output / "status.json",
                {"status": "failed", "error": f"{type(exc).__name__}: {exc}"},
            )
        raise


def verify(output):
    output = Path(output)
    status = json.loads((output / "status.json").read_text())
    if status.get("status") != "complete":
        raise ValueError("refit run is incomplete")
    _check(output / "summary.json", status["summary_sha256"])
    summary = json.loads((output / "summary.json").read_text())
    _check(output / "manifest.json", summary["manifest_sha256"])
    manifest = json.loads((output / "manifest.json").read_text())
    expected = {
        f"{v}/{s['name']}/{n}"
        for v in manifest["variants"]
        for s in manifest["scenarios"]
        for n in ("predictions.parquet", "fits.json", "summary.json", "complete.json")
    }
    if (
        set(summary["output_hashes"]) != expected
        or summary["scenario_count"] != len(expected) // 4
    ):
        raise ValueError("refit scenario set is incomplete")
    for name, digest in summary["output_hashes"].items():
        _check(benchmark._safe_child(output, name), digest)
    keys = {tuple(k) for k in manifest["reference_keys"]}
    for variant in manifest["variants"]:
        reports = []
        for scenario in manifest["scenarios"]:
            directory = output / variant / scenario["name"]
            fingerprint = _digest(
                {"manifest": manifest, "variant": variant, "scenario": scenario}
            )
            rows, report = _cached(directory, fingerprint)
            benchmark._equivalent(
                summarize_scenario(rows, keys),
                {
                    k: v
                    for k, v in report.items()
                    if k
                    not in (
                        "variant",
                        "scenario",
                        "reference_reproduction",
                        "elapsed_seconds",
                    )
                },
            )
            benchmark._equivalent(
                report, summary["variants"][variant]["scenarios"][scenario["name"]]
            )
            reports.append(report)
        benchmark._equivalent(ranges(reports), summary["variants"][variant]["ranges"])
        benchmark._equivalent(
            fixed_scenario_support(output, variant, manifest["scenarios"]),
            summary["variants"][variant]["fixed_scenario_support"],
        )
    return {
        "status": "verified",
        "scenario_count": summary["scenario_count"],
        "reference_target_n": len(keys),
    }


def render_report(summary):
    """Compact numerical companion from completed scenario tables."""
    spec = {
        "Unit": "Player/destination-season",
        "Population": "Original exposure-qualified newcomers, seasons 2020–2025",
        "Estimator": "Existing factor/pooling/lag, all v7 arms, 2,000 factor draws",
        "Null": "Incremental predictive benefit remains undetermined",
        "Filter": "Native and fixed all-scenario common support",
        "Key": "player_name + season_dest",
        "Uncertainty": "Refit/seed ranges conditional on historical measurements",
    }
    lines = [
        "# Sloan full model-refit sensitivity",
        "",
        CONVENTION,
        "",
        "## Specification",
        "",
        "| Field | Declaration |",
        "| --- | --- |",
        *[f"| {name} | {value} |" for name, value in spec.items()],
        "",
        f"Completed scenarios: {summary['scenario_count']}. "
        f"Original common target: {summary['reference_target_n']} rows.",
        "",
        "## Primary contrast on fixed support",
        "",
        "Positive differences favor adding the scheduled feature "
        "to destination-aware history.",
        "",
        "| Variant | Reference n | Fixed n | Reference delta | "
        "Season range | Seed range | Replay |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]

    def number(value):
        return "not estimable" if value is None else f"{value:.6f}"

    def interval(value):
        if value is None:
            return "not estimable"
        return "[" + ", ".join(number(x) for x in value) + "]"

    for variant, item in summary["variants"].items():
        fixed = item["fixed_scenario_support"]
        reference = item["scenarios"]["reference"]
        contrast = fixed["scenarios"]["reference"]["contrasts"]
        delta = contrast["destination_increment"]["player_club_season"]
        influence = fixed["ranges"]["sample_influence"]["contrasts"]
        seeds = fixed["ranges"]["monte_carlo"]["contrasts"]
        replay = reference["reference_reproduction"]
        values = (
            variant,
            reference["native"]["n"],
            fixed["n"],
            number(delta["difference"]),
            interval(influence["destination_increment"]["range"]),
            interval(seeds["destination_increment"]["range"]),
            replay["status"] if replay else "new variant",
        )
        lines.append("| " + " | ".join(map(str, values)) + " |")
    lines.extend(
        [
            "",
            "All arms, penalties, masks, coefficients, factor/lag diagnostics, "
            "conditional intervals, annual errors and refusals remain in the hashed "
            "JSON/parquet companion. Fixed sets intersect every declared scenario "
            "within each variant. Native/original-target tables retain support shifts.",
            "",
            "Seed/deletion interactions are not measured. Reused historical "
            "seasons do not provide prospective confirmation, equivalence, causal "
            "identification or demonstrated recruitment utility.",
            "",
        ]
    )
    return "\n".join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    restore = sub.add_parser("restore-originals")
    restore.add_argument("--source-run", type=Path, required=True)
    restore.add_argument("--revision-dir", type=Path, required=True)
    restore.add_argument("--out-dir", type=Path, required=True)
    execute = sub.add_parser("run")
    execute.add_argument("--input-root", type=Path, required=True)
    execute.add_argument("--revision-dir", type=Path, required=True)
    execute.add_argument("--reference-dir", type=Path, required=True)
    execute.add_argument("--out-dir", type=Path, required=True)
    execute.add_argument("--variants", nargs="+", default=list(source.VARIANTS))
    execute.add_argument("--workers", type=int, choices=(1, 2), default=1)
    render = sub.add_parser("render")
    render.add_argument("--out-dir", type=Path, required=True)
    render.add_argument("--report-path", type=Path, required=True)
    check = sub.add_parser("verify")
    check.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args(argv)
    with threadpool_limits(limits=1):
        if args.command == "restore-originals":
            result = restore_originals(args.source_run, args.revision_dir, args.out_dir)
        elif args.command == "run":
            result = run(
                args.input_root,
                args.revision_dir,
                args.reference_dir,
                args.out_dir,
                variants=args.variants,
                workers=args.workers,
            )
        elif args.command == "render":
            result = verify(args.out_dir)
            report = render_report(
                json.loads((args.out_dir / "summary.json").read_text())
            )
            args.report_path.parent.mkdir(parents=True, exist_ok=True)
            args.report_path.write_text(report)
        else:
            result = verify(args.out_dir)
    print(
        json.dumps(
            {"status": result["status"], "scenario_count": result.get("scenario_count")}
        ),
        flush=True,
    )


if __name__ == "__main__":
    main()
