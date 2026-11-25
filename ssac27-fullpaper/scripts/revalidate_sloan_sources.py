"""Versioned source-quality revalidation; never overwrite historical results.

Threats: data changes masquerade as predictive improvement (common populations);
repairs fail to reach prior history (rebuild from games); same-name collisions
masquerade as duplicates (explicit adjudication); stale caches masquerade as runs
(input/code fingerprints and complete states). No network calls.
"""

from __future__ import annotations

import argparse
import contextlib
import io
import itertools
import json
from pathlib import Path
import shutil
import sys

import numpy as np
import pandas as pd
from threadpoolctl import threadpool_limits

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import audit_translation_estimators as alt  # noqa: E402
from scripts import build_league_factors as blf  # noqa: E402
from scripts import compare_translation_designs as design  # noqa: E402
from scripts import sloan_source_adjudication as source  # noqa: E402
from scripts import validate_translation_holdout as vh  # noqa: E402
from scripts import validate_translation_walkforward as wf  # noqa: E402
from scripts import verify_sloan_baseline as baseline  # noqa: E402
from scripts.translation_research_common import fit_table, sha256_file  # noqa: E402

VARIANTS = (
    "baseline",
    "invalid_minutes_quarantine",
    "all_questioned_quarantine",
    "alternative_tree",
    "evidence_backed_repair",
)
KEY = ["player_name", "season_dest"]
LEGACY_ARMS = baseline.ARMS
CODE_NAMES = (
    "revalidate_sloan_sources.py",
    "sloan_source_adjudication.py",
    "audit_translation_estimators.py",
    "translation_research_common.py",
    "build_league_factors.py",
    "validate_translation_holdout.py",
    "validate_translation_walkforward.py",
    "compare_translation_designs.py",
)


def json_write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    design.dump_json(path, value)


def keyed_equal(actual, expected, keys):
    """Compare every saved column, allowing only floating reassociation noise."""
    for frame in (actual, expected):
        if frame[keys].isna().any().any() or frame.duplicated(keys).any():
            raise ValueError(f"nonunique or missing cohort keys: {keys}")
    if not set(expected.columns).issubset(actual.columns):
        raise ValueError("reconstruction is missing saved scientific columns")
    left, right = [
        frame.sort_values(keys).reset_index(drop=True)[expected.columns]
        for frame in (actual, expected)
    ]
    pd.testing.assert_frame_equal(
        left, right, check_dtype=False, check_exact=False, atol=1e-9, rtol=0
    )
    return {"rows": len(left), "columns": len(left.columns), "equal": True}


def build_inputs(canonical_games, ambiguous_names=()):
    """Recompute rates AND cumulative prior histories through existing loaders."""
    raw = canonical_games.drop(
        columns=[c for c in canonical_games if c.startswith("_")], errors="ignore"
    )
    # Match the legacy loader before its API replacement and name filtering.
    if float(raw.pir.isna().mean()) > 0.001:
        raise ValueError("PIR null fraction exceeds inherited 0.001 refusal")
    games = blf._swap_in_api_destination(raw)
    games = games[~games.player_name.isin(ambiguous_names)].copy()
    games = blf.add_usage(games)
    pairs = blf.build_pairs(games, min_games=vh.MIN_GAMES)
    with contextlib.redirect_stdout(io.StringIO()):
        switchers, _ = vh.build_switchers(games)
    return pairs.reset_index(drop=True), switchers.reset_index(drop=True)


def code_fingerprints():
    paths = [f"scripts/{name}" for name in CODE_NAMES]
    paths.append("src/data/corpus/euroleague_api.py")
    return {name: sha256_file(ROOT / name) for name in paths}


def api_inventory():
    """Hash exactly the directories the existing API loader can read."""
    records = []
    for competition in blf.CONTINENTAL:
        for season in blf.API_SEASONS:
            directory = ROOT / "data/raw" / competition / str(season) / "boxscores"
            if directory.exists():
                paths = (
                    [directory] if directory.is_file() else sorted(directory.rglob("*"))
                )
                for path in paths:
                    if path.is_file():
                        records.append(
                            {
                                "source_file": str(path.resolve()),
                                "sha256": sha256_file(path),
                            }
                        )
    if not records:
        raise ValueError("no API source files available for provenance")
    return records


def verify_inventory(records):
    for item in records:
        path = Path(item["source_file"])
        if not path.is_file() or sha256_file(path) != item["sha256"]:
            raise ValueError(f"raw input changed: {path}")


def prepare_inputs(raw_root, reference_dir, out_dir, baseline_manifest, evidence_path):
    gate = json.loads(Path(baseline_manifest).read_text())
    baseline.check_manifest(gate)
    if gate.get("status") != "passed":
        raise ValueError("baseline gate has not passed")
    api_files = api_inventory()
    raw, inventory = source.load_raw(Path(raw_root))
    diagnosis = source.diagnose(raw)
    evidence = json.loads(Path(evidence_path).read_text()) if evidence_path else None
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    json_write(out_dir / "source_diagnosis.json", diagnosis)
    json_write(out_dir / "protected_baseline_manifest.json", gate)
    if evidence_path:
        shutil.copyfile(evidence_path, out_dir / "official_minute_evidence.json")
    original_pairs = pd.read_parquet(Path(reference_dir) / "pairs.parquet")
    original_switchers = pd.read_parquet(Path(reference_dir) / "switchers.parquet")
    entries = {}
    for variant in VARIANTS:
        games, adjudication = source.apply_variant(raw, variant, evidence=evidence)
        dest = out_dir / "inputs" / variant
        dest.mkdir(parents=True, exist_ok=True)
        json_write(dest / "adjudication.json", adjudication)
        if adjudication.get("status") == "not_run":
            entries[variant] = {"status": "not_run", "reason": adjudication}
            continue
        verify_inventory(api_files)
        pairs, switchers = build_inputs(
            games, adjudication.get("ambiguous_normalized_names", [])
        )
        if api_inventory() != api_files:
            raise ValueError("API source inventory changed between variants")
        if variant == "baseline":
            checks = {
                "pairs": keyed_equal(pairs, original_pairs, ["player_name", "season"]),
                "switchers": keyed_equal(switchers, original_switchers, KEY),
            }
            json_write(out_dir / "raw_reconstruction_gate.json", checks)
        paths = {
            "pairs.parquet": pairs,
            "switchers.parquet": switchers,
        }
        for name, frame in paths.items():
            frame.to_parquet(dest / name, index=False)
        entries[variant] = {
            "status": "prepared",
            "n_pairs": len(pairs),
            "n_switchers": len(switchers),
            "hashes": {name: sha256_file(dest / name) for name in paths},
        }
        print(
            f"[prepare] {variant}: pairs={len(pairs)} switchers={len(switchers)}",
            flush=True,
        )
    # Source files remain protected even if an interrupted run produced inputs.
    for record in inventory:
        path = Path(record["source_file"])
        if not path.is_absolute():
            path = Path(raw_root) / path
        if sha256_file(path) != record["sha256"]:
            raise ValueError(f"raw input changed during preparation: {path}")
    manifest = {
        "status": "prepared",
        "variants": entries,
        "raw_inputs": inventory,
        "api_inputs": api_files,
        "baseline_manifest_sha256": sha256_file(Path(baseline_manifest)),
        "evidence_sha256": sha256_file(Path(evidence_path)) if evidence_path else None,
        "code": code_fingerprints(),
        "limitations": (
            "Research variants; original corpus and operating forecasts unchanged."
        ),
    }
    json_write(out_dir / "preparation_manifest.json", manifest)
    return manifest


def legacy_forecasts(pairs, switchers, seed):
    cohort = switchers[
        (switchers.was_cont == 0)
        & ~switchers.league_src.isin(vh.EXCLUDED_SOURCE)
        & (switchers.pir_per36_src > 0)
    ].copy()
    folds = [
        alt.alternative_fold(
            pairs, cohort, season, estimator=blf.PRIMARY, n_boot=2000, seed=seed
        )
        for season in wf.SEASONS
    ]
    rows = pd.concat([wf.fold_rows(fold) for fold in folds], ignore_index=True)
    rows = rows.rename(columns={"season": "season_dest"})
    rows["scored"] = np.isfinite(rows[list(LEGACY_ARMS)]).all(axis=1)
    diagnostics = [
        {
            "season": f["season"],
            "k_lag": f["k_lag"],
            "collapsed_blocks": f["collapsed_blocks"],
            "n_train_pairs": f["n_train_pairs"],
            "n_train_cohort": f["n_train_cohort"],
            "cells": f["table"].to_dict("records"),
        }
        for f in folds
    ]
    return rows, diagnostics


def error_metrics(rows, arms, outcome):
    if not len(rows):
        return {a: {"n": 0, "mae": None, "rmse": None, "bias": None} for a in arms}
    if not np.isfinite(rows[[outcome, *arms]].to_numpy(dtype=float)).all():
        raise ValueError("nonfinite values cannot silently change scoring population")
    return {
        a: {
            "n": len(rows),
            "mae": float(np.abs(rows[a] - rows[outcome]).mean()),
            "rmse": float(np.sqrt(np.square(rows[a] - rows[outcome]).mean())),
            "bias": float((rows[a] - rows[outcome]).mean()),
        }
        for a in arms
    }


def common_population(frames):
    sets = []
    for frame in frames.values():
        if frame[KEY].isna().any().any() or frame.duplicated(KEY).any():
            raise ValueError("missing or duplicate comparison keys")
        sets.append(set(map(tuple, frame.loc[frame.scored, KEY].to_numpy())))
    common = set.intersection(*sets) if sets else set()
    if not common:
        raise ValueError("no common eligible prediction population")
    return {
        name: frame[[tuple(k) in common for k in frame[KEY].to_numpy()]]
        .sort_values(KEY)
        .reset_index(drop=True)
        for name, frame in frames.items()
    }


def before_after_contrast(base, changed, arm, outcome, seed):
    """Conditional paired-error differences; positive means changed is worse."""
    if not base[KEY].equals(changed[KEY]):
        raise ValueError("before/after population differs")
    if not np.allclose(base[outcome], changed[outcome], atol=1e-9, rtol=0):
        raise ValueError("destination outcomes changed on common rows")
    delta = np.abs(changed[arm] - changed[outcome]) - np.abs(base[arm] - base[outcome])
    results = {}
    for cluster in ("cluster", "player_name"):
        ids, inverse = np.unique(base[cluster].astype(str), return_inverse=True)
        counts = np.bincount(inverse)
        sums = np.bincount(inverse, weights=delta)
        rng = np.random.default_rng(
            design.stable_seed(seed, "source-change", arm, cluster)
        )
        draws = np.empty(4000)
        for i in range(4000):
            ix = rng.integers(0, len(ids), len(ids))
            draws[i] = sums[ix].sum() / counts[ix].sum()
        results[cluster] = {
            "n_clusters": len(ids),
            "ci95": np.quantile(draws, [0.025, 0.975]).tolist()
            if len(ids) > 1
            else None,
        }
    return {
        "n": len(base),
        "mae_changed_minus_original": float(delta.mean()),
        "mean_prediction_change": float((changed[arm] - base[arm]).mean()),
        "max_absolute_prediction_change": float(np.abs(changed[arm] - base[arm]).max()),
        "conditional_intervals": results,
    }


def legacy_summary(rows, seed=0):
    contrasts = {}
    for first, second in itertools.combinations(LEGACY_ARMS, 2):
        result = before_after_contrast(
            rows.assign(_prediction=rows[first]),
            rows.assign(_prediction=rows[second]),
            "_prediction",
            "y",
            seed,
        )
        contrasts[f"{second}_minus_{first}"] = {
            "n": result["n"],
            "mae_second_minus_first": result["mae_changed_minus_original"],
            "conditional_intervals": result["conditional_intervals"],
        }
    return {
        "metrics": error_metrics(rows, LEGACY_ARMS, "y"),
        "paired_arm_contrasts": contrasts,
        "per_season": {
            int(season): error_metrics(group, LEGACY_ARMS, "y")
            for season, group in rows.groupby("season_dest")
        },
        "above_prior": error_metrics(
            rows[rows.above_own_prior.fillna(False).astype(bool)], LEGACY_ARMS, "y"
        ),
    }


def cohort_diagnostics(switchers, rows):
    _, _, flow = design.prepare(
        pd.DataFrame(columns=["player_name", "season"]), switchers
    )
    scored = rows[rows.scored]
    club_sizes = scored.groupby("cluster").size()
    player_sizes = scored.groupby("player_name").size()
    return {
        "input_exclusions": flow.input_exclusion.value_counts().to_dict(),
        "input_switchers": len(flow),
        "eligible_all_seasons": int(flow.input_exclusion.eq("").sum()),
        "outer_rows": len(rows),
        "scored_outer_rows": len(scored),
        "club_season_sizes": club_sizes.to_dict(),
        "player_sizes": player_sizes.to_dict(),
        "players_in_multiple_club_seasons": int(
            (scored.groupby("player_name").cluster.nunique() > 1).sum()
        ),
        "seasons": sorted(int(x) for x in scored.season_dest.unique()),
        "uncertainty_scope": (
            "Resampling fixed retrospective errors; no refitting, "
            "no joint crossed-dependence correction."
        ),
    }


def score(prepared_dir, *, seed=0, matched_repetitions=200):
    prepared_dir = Path(prepared_dir)
    manifest = json.loads((prepared_dir / "preparation_manifest.json").read_text())
    if manifest["status"] != "prepared":
        raise ValueError("inputs not completely prepared")
    for name, fingerprint in manifest["code"].items():
        if sha256_file(ROOT / name) != fingerprint:
            raise ValueError(f"preparation code changed: {name}; re-prepare inputs")
    protected = json.loads(
        (prepared_dir / "protected_baseline_manifest.json").read_text()
    )
    baseline.check_manifest(protected)
    json_write(prepared_dir / "revalidation_status.json", {"status": "running"})
    # Never leave a former completed summary beside a newly started run.
    (prepared_dir / "revalidation_summary.json").unlink(missing_ok=True)
    legacy, strict, results = {}, {}, {}
    for variant, entry in manifest["variants"].items():
        if entry["status"] != "prepared":
            results[variant] = entry
            continue
        input_dir = prepared_dir / "inputs" / variant
        for name, fingerprint in entry["hashes"].items():
            if sha256_file(input_dir / name) != fingerprint:
                raise ValueError(f"input changed: {variant}/{name}")
        pairs = pd.read_parquet(input_dir / "pairs.parquet")
        switchers = pd.read_parquet(input_dir / "switchers.parquet")
        output = prepared_dir / "results" / variant
        output.mkdir(parents=True, exist_ok=True)
        old_rows, old_folds = legacy_forecasts(pairs, switchers, seed)
        pair_input, cohort, flow = design.prepare(pairs, switchers)
        rows, diagnostics = design.Study(pair_input, cohort, seed=seed).run()
        factors = fit_table(pairs, seed=seed, n_boot=2000)
        factors.to_csv(output / "factor_table.csv", index=False)
        old_rows.to_parquet(output / "legacy_rows.parquet", index=False)
        rows.to_parquet(output / "chronological_rows.parquet", index=False)
        flow.to_parquet(output / "cohort_flow.parquet", index=False)
        json_write(output / "legacy_fit_diagnostics.json", old_folds)
        json_write(output / "chronological_fit_diagnostics.json", diagnostics)
        legacy[variant], strict[variant] = old_rows, rows
        results[variant] = {
            "status": "complete",
            "n_pairs": len(pairs),
            "legacy_native": legacy_summary(old_rows[old_rows.scored], seed),
            "chronological_native": design.summarize(rows, seed),
            "cohort": cohort_diagnostics(switchers, rows),
            "factor_targets": (
                "Raw-estimator intervals; pooled points have no "
                "claimed confidence interval."
            ),
        }
        if variant == "baseline":
            reference = json.loads(
                (prepared_dir / "reference_walkforward_summary.json").read_text()
            )
            baseline.compare_maes(
                old_rows.rename(columns={"season_dest": "season"}), reference
            )
        print(
            f"[score] {variant}: legacy={int(old_rows.scored.sum())} "
            f"chronological={int(rows.scored.sum())}",
            flush=True,
        )
    # One intersection across BOTH analysis designs and all completed variants.
    all_frames = {
        **{f"legacy:{k}": v for k, v in legacy.items()},
        **{f"strict:{k}": v for k, v in strict.items()},
    }
    aligned = common_population(all_frames)
    for variant in legacy:
        old = aligned[f"legacy:{variant}"]
        new = aligned[f"strict:{variant}"]
        results[variant]["legacy_common"] = legacy_summary(old, seed)
        results[variant]["chronological_common"] = design.summarize(new, seed)
        results[variant]["changes_on_common"] = {
            "legacy": {
                arm: before_after_contrast(
                    aligned["legacy:baseline"], old, arm, "y", seed
                )
                for arm in LEGACY_ARMS
            },
            "chronological": {
                arm: before_after_contrast(
                    aligned["strict:baseline"], new, arm, "pir_per36_dest", seed
                )
                for arm in design.ARMS
            },
        }
        old.to_csv(
            prepared_dir / "results" / variant / "legacy_common_rows.csv", index=False
        )
        new.to_csv(
            prepared_dir / "results" / variant / "chronological_common_rows.csv",
            index=False,
        )
    repetitions = []
    if matched_repetitions:
        if matched_repetitions != 200:
            raise ValueError(
                "registered matched study requires exactly 200 repetitions"
            )
        input_dir = prepared_dir / "inputs/all_questioned_quarantine"
        output = prepared_dir / "matched_all_questioned"
        design.main(
            [
                "--input-dir",
                str(input_dir),
                "--out-dir",
                str(output),
                "--seed",
                str(seed),
                "--workers",
                "1",
            ]
        )
        matched = json.loads((output / "design_comparison_summary.json").read_text())
        repetitions = matched["matched_repetitions"]
    protection = baseline.check_manifest(protected)
    verify_inventory(manifest["raw_inputs"] + manifest["api_inputs"])
    summary = {
        "status": "complete" if len(repetitions) == 200 else "incomplete",
        "seed": seed,
        "factor_bootstrap": 2000,
        "contrast_bootstrap": 4000,
        "common_n": len(aligned["strict:baseline"]),
        "variants": results,
        "matched_repetitions": repetitions,
        "matched_status": "complete" if len(repetitions) == 200 else "not_run",
        "original_results_preserved": protection["status"] == "passed",
        "protection_check": protection,
        "interpretation": (
            "Exploratory source handling sensitivity; native "
            "populations differ; common-population changes are primary."
        ),
        "preparation_manifest_sha256": sha256_file(
            prepared_dir / "preparation_manifest.json"
        ),
    }
    json_write(prepared_dir / "revalidation_summary.json", summary)
    json_write(prepared_dir / "revalidation_status.json", {"status": summary["status"]})
    return summary


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-root", type=Path)
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--baseline-manifest", type=Path)
    parser.add_argument("--evidence", type=Path)
    parser.add_argument("--stage", choices=("prepare", "score", "all"), default="all")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--skip-matched", action="store_true")
    args = parser.parse_args(argv)
    if args.seed != 0 or args.workers != 1:
        parser.error("registered run requires --seed 0 --workers 1")
    with threadpool_limits(limits=1):
        if args.stage in ("prepare", "all"):
            if args.raw_root is None or args.baseline_manifest is None:
                parser.error("preparation requires --raw-root and --baseline-manifest")
            prepare_inputs(
                args.raw_root,
                args.input_dir,
                args.out_dir,
                args.baseline_manifest,
                args.evidence,
            )
            shutil.copyfile(
                args.input_dir / "walkforward_summary.json",
                args.out_dir / "reference_walkforward_summary.json",
            )
        if args.stage in ("score", "all"):
            score(
                args.out_dir,
                seed=args.seed,
                matched_repetitions=0 if args.skip_matched else 200,
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
