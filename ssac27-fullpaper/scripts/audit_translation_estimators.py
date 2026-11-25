#!/usr/bin/env python
"""Study A of the 2026-09-07 Sloan protocol; alternative fits stay research-only.

Threat controls: identical generated rows/resamples across estimators; own raw
intervals; replicate-level Monte Carlo SE; exact expected-key completion checks;
content-addressed caches; baseline MAE reproduction before alternative reporting.
No raw corpus loader or operating-model mutation is used.
"""

from __future__ import annotations

import argparse
from concurrent.futures import ProcessPoolExecutor
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from scripts import simulate_translation_estimator as sim  # noqa: E402
from scripts import validate_translation_walkforward as wf  # noqa: E402
from scripts.translation_research_common import (  # noqa: E402
    ESTIMATORS,
    fit_table,
    sha256_file,
    stable_seed,
)

OUT = REPO / "docs/research/artifacts/sloan-validation-2026-09-07"
PRIVATE = REPO / "data/processed/sloan_validation"
SCENARIOS = ("gaussian", "student_t5", "correlated_gaussian")
FACTORS = (1.0, 0.8, 0.9)
KEY = [
    "template",
    "scenario",
    "truth",
    "replicate",
    "n_boot",
    "estimator",
    "league",
    "destination",
]
ARMS = ("per_league", "one_global", "b0", "rtm", "rtm_plus_league")


def write_json(path: Path, obj: dict) -> None:
    """Strict JSON: unavailable quantities are null, never nonstandard NaN."""

    def clean(value):
        if isinstance(value, dict):
            return {str(k): clean(v) for k, v in value.items()}
        if isinstance(value, (list, tuple)):
            return [clean(v) for v in value]
        if isinstance(value, (np.integer, np.bool_)):
            return value.item()
        if isinstance(value, (float, np.floating)):
            return float(value) if np.isfinite(value) else None
        return value

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(clean(obj), indent=2, allow_nan=False) + "\n")


def cache_key(config: dict, files: list[Path]) -> tuple[str, dict]:
    hashes = {
        str(p.relative_to(REPO)) if p.is_relative_to(REPO) else str(p): sha256_file(p)
        for p in files
    }
    payload = {"config": config, "hashes": hashes}
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True).encode()
    ).hexdigest(), payload


def generate_table(
    pairs: pd.DataFrame, cal: dict, *, truth: float, scenario: str, seed: int
) -> pd.DataFrame:
    """Legacy ability/cluster/role generator; only sampling errors vary."""
    if scenario not in SCENARIOS:
        raise ValueError(f"Unknown scenario: {scenario}")
    rng = np.random.default_rng(seed)
    cell_truth = {k: truth for k in pairs.groupby(["league_src", "league_dest"]).groups}
    if scenario == "gaussian":
        return sim.synth_table(pairs, cell_truth, cal, rng)
    clusters = pairs.cluster.unique()
    club_eff = dict(zip(clusters, rng.normal(0, cal["sigma_u"], len(clusters))))
    cells = []
    for _, rows in pairs.groupby(["league_src", "league_dest"]):
        n = len(rows)
        s = rows.sample(
            n=n, replace=True, random_state=int(rng.integers(2**31))
        ).reset_index(drop=True)
        ability = np.maximum(rng.normal(cal["mu"], cal["sigma_a"], n), sim.TRUNCATE_AT)
        if scenario == "student_t5":
            source_noise = rng.standard_t(5, n) * np.sqrt(3 / 5)
        else:
            source_noise = rng.normal(size=n)
        role = 1 + rng.normal(0, cal["sigma_r"], n)
        if scenario == "student_t5":
            dest_noise = rng.standard_t(5, n) * np.sqrt(3 / 5)
        else:
            dest_noise = 0.5 * source_noise + np.sqrt(0.75) * rng.normal(size=n)
        x = ability + cal["sigma_g"] * source_noise / np.sqrt(s.games_src.to_numpy())
        y = (
            truth * ability * role
            + s.cluster.map(club_eff).to_numpy()
            + cal["sigma_g"] * dest_noise / np.sqrt(s.games_dest.to_numpy())
        )
        s["pir_per36_src"], s["pir_per36_dest"] = x, y
        s["pir_src"], s["pir_dest"] = x * s.minutes_src / 36, y * s.minutes_dest / 36
        cells.append(s)
    return pd.concat(cells, ignore_index=True)


def run_replicate(task: dict) -> pd.DataFrame:
    table = generate_table(
        task["pairs"],
        task["cal"],
        truth=task["truth"],
        scenario=task["scenario"],
        seed=task["table_seed"],
    )
    frames = []
    for n_boot in task["depths"]:
        for estimator in ESTIMATORS:
            fitted = fit_table(
                table, estimator=estimator, n_boot=n_boot, seed=task["fit_seed"]
            )
            for k in [
                "template",
                "scenario",
                "truth",
                "replicate",
                "table_seed",
                "fit_seed",
            ]:
                fitted[k] = task[k]
            fitted["estimator"], fitted["n_boot"] = estimator, n_boot
            fitted["raw_error"] = fitted.factor_raw - task["truth"]
            fitted["pooled_error"] = fitted.factor - task["truth"]
            fitted["interval_valid"] = np.isfinite(fitted.ci_lo) & np.isfinite(
                fitted.ci_hi
            )
            fitted["fit_invalid"] = (
                ~np.isfinite(fitted.factor_raw) | ~fitted.interval_valid
            )
            fitted["covered"] = np.where(
                fitted.interval_valid,
                (fitted.ci_lo <= task["truth"]) & (fitted.ci_hi >= task["truth"]),
                np.nan,
            )
            fitted["interval_width"] = fitted.ci_hi - fitted.ci_lo
            frames.append(fitted)
    return pd.concat(frames, ignore_index=True)


def _cached_replicate(task: dict) -> pd.DataFrame:
    path = Path(task["cache_path"])
    expected = {
        (n, e, lg, d)
        for n in task["depths"]
        for e in ESTIMATORS
        for lg, d in task["cells"]
    }
    if path.exists():
        frame = pd.read_parquet(path)
        keys = ["n_boot", "estimator", "league", "destination"]
        actual = (
            set(frame[keys].itertuples(index=False, name=None))
            if set(keys) <= set(frame)
            else set()
        )
        if actual == expected and len(frame) == len(expected):
            return frame
        # Interrupted or incomplete entries are never accepted as completed.
    frame = run_replicate(task)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp.parquet")
    frame.to_parquet(temporary, index=False)
    temporary.replace(path)
    return frame


def summarise(rows: pd.DataFrame) -> dict:
    """Cells summarize a table; Monte Carlo uncertainty uses table replicates."""
    conditions = []
    group_keys = ["template", "scenario", "truth", "n_boot", "estimator"]
    for key, block in rows.groupby(group_keys):
        replicate_stats = []
        for rep, frame in block.groupby("replicate"):
            replicate_stats.append(
                dict(
                    replicate=int(rep),
                    raw_bias=frame.raw_error.mean(),
                    raw_rmse=np.sqrt((frame.raw_error**2).mean()),
                    raw_coverage=frame.covered.mean(),
                    raw_width=frame.interval_width.mean(),
                    pooled_bias=frame.pooled_error.mean(),
                    pooled_rmse=np.sqrt((frame.pooled_error**2).mean()),
                    invalid_fit_frequency=frame.fit_invalid.mean(),
                    pooling_collapse_frequency=frame.pooled_collapsed.mean(),
                    invalid_draw_frequency=frame.n_boot_invalid.sum()
                    / (len(frame) * int(frame.n_boot.iloc[0])),
                )
            )
        stats = pd.DataFrame(replicate_stats)
        metrics = {}
        for column in stats.columns.drop("replicate"):
            values = stats[column].dropna()
            metrics[column] = {
                "mean": values.mean(),
                "mc_se": values.std(ddof=1) / np.sqrt(len(values))
                if len(values) > 1
                else np.nan,
                "n_table_replicates": len(values),
            }
        conditions.append(
            dict(zip(group_keys, key))
            | {
                "n_cells": len(block),
                "coverage_denominator": int(block.interval_valid.sum()),
                "invalid_intervals": int((~block.interval_valid).sum()),
                "invalid_bootstrap_draws": int(block.n_boot_invalid.sum()),
                "metrics": metrics,
                "replicate_statistics": replicate_stats,
            }
        )
    return {
        "conditions": conditions,
        "uncertainty_unit": (
            "table replicate, after cell averaging; RMSE is mean within-table RMSE"
        ),
        "interval_target": (
            "raw estimator percentile interval; no pooled point interval claimed"
        ),
    }


def assert_complete(
    rows: pd.DataFrame,
    cells: dict,
    *,
    reps: int = 200,
    check_reps: int = 50,
    n_boot: int = 500,
    check_boot: int = 2000,
) -> None:
    if rows.duplicated(KEY).any():
        raise ValueError("Duplicate estimator audit keys")
    expected = {
        (t, s, f, r, b, e, lg, d)
        for t, table_cells in cells.items()
        for s in SCENARIOS
        for f in FACTORS
        for r in range(reps)
        for b in ([n_boot, check_boot] if r < check_reps else [n_boot])
        for e in ESTIMATORS
        for lg, d in table_cells
    }
    actual = set(rows[KEY].itertuples(index=False, name=None))
    if expected != actual:
        raise ValueError(
            f"Incomplete estimator audit: missing={len(expected - actual)} "
            f"unexpected={len(actual - expected)}"
        )


def render_note(summary: dict) -> str:
    if summary.get("status") != "complete":
        raise ValueError("Refusing publication rendering of incomplete estimator audit")
    lines = [
        "# Estimator audit — artifact readback",
        "",
        "Raw percentile intervals target raw estimators. "
        "Pooled points have no calibrated interval here.",
        "",
        "| Template | Sampling noise | True factor | Bootstrap | Estimator | "
        "Raw bias (MC SE) | Raw RMSE | Coverage | Pooled RMSE | "
        "Invalid fit | Collapse |",
        "|---|---|---:|---:|---|---:|---:|---:|---:|---:|---:|",
    ]
    for c in summary["conditions"]:
        m = c["metrics"]
        lines.append(
            f"| {c['template']} | {c['scenario']} | {c['truth']:.2f} | {c['n_boot']} | "
            f"{c['estimator']} | {m['raw_bias']['mean']:+.4f} "
            f"({m['raw_bias']['mc_se']:.4f}) | {m['raw_rmse']['mean']:.4f} | "
            f"{m['raw_coverage']['mean']:.3f} | {m['pooled_rmse']['mean']:.4f} | "
            f"{m['invalid_fit_frequency']['mean']:.3f} | "
            f"{m['pooling_collapse_frequency']['mean']:.3f} |"
        )
    lines += [
        "",
        "Monte Carlo SE uses table replicates after summarizing nested cells. "
        "Coverage excludes invalid intervals; every denominator and invalid draw "
        "count is in the summary. The 2,000-draw sensitivity uses the first 50 "
        "identical tables. These generator checks do not establish real-world "
        "calibration or select a replacement estimator.",
        "",
    ]
    return "\n".join(lines)


def alternative_fold(
    pairs: pd.DataFrame,
    cohorts: pd.DataFrame,
    season: int,
    *,
    estimator: str,
    n_boot: int,
    seed: int,
) -> dict:
    """Recompute the legacy five-arm procedure, including pooling, K and OLS."""
    train_pairs = pairs[pairs.season < season]
    table = fit_table(train_pairs, estimator=estimator, n_boot=n_boot, seed=seed)
    tier = table.groupby("destination").tier_mean.first().to_dict()
    lookup = {
        (r.league, r.destination): r.factor if r.reliable else tier[r.destination]
        for r in table.itertuples()
    }

    def multiplier(frame):
        return np.array(
            [
                lookup.get((lg, d), tier.get(d, np.nan))
                for lg, d in zip(frame.league_src, frame.league_dest)
            ]
        )

    train, test = (
        cohorts[cohorts.season_dest < season],
        cohorts[cohorts.season_dest == season],
    )
    with np.errstate(divide="ignore", invalid="ignore"):
        k = float(
            np.median(
                train.pir_per36_dest.to_numpy()
                / (train.pir_per36_src.to_numpy() * multiplier(train))
            )
        )
    reliable = table[table.reliable.astype(bool)]
    scalar = (
        float(np.average(reliable.factor, weights=reliable.n_pairs))
        if len(reliable)
        else np.nan
    )
    tau = table.groupby("destination").tau.first().to_dict()
    fold = dict(
        season=season,
        n=len(test),
        train_rows=train,
        test_rows=test,
        multiplier_fn=multiplier,
        k_lag=k,
        global_scalar=scalar,
        table=table,
        tau=tau,
        collapsed_blocks=[d for d, t in tau.items() if not t > 0],
        n_train_pairs=len(train_pairs),
        n_train_cohort=len(train),
        multiplier=multiplier(test),
        src=test.pir_per36_src.to_numpy(),
        y=test.pir_per36_dest.to_numpy(),
        clusters=test.cluster.to_numpy(),
    )
    # Fail explicitly instead of allowing linalg to report or hide an absent tier.
    if (
        not np.isfinite(multiplier(train)).all()
        or not np.isfinite(multiplier(test)).all()
    ):
        raise ValueError(f"Missing finite tier in {estimator} fold {season}")
    fold["rtm_arms"] = wf._fit_rtm_arms(fold)
    return fold


def run_alternative_forecasts(
    input_dir: Path, out_dir: Path, *, n_boot: int = 2000, seed: int = 0
) -> dict:
    pairs = pd.read_parquet(input_dir / "pairs.parquet")
    switch = pd.read_parquet(input_dir / "switchers.parquet")
    cohort = switch[
        (switch.was_cont == 0)
        & ~switch.league_src.isin(wf.vh.EXCLUDED_SOURCE)
        & (switch.pir_per36_src > 0)
    ].copy()
    identity = ["player_name", "season_dest"]
    if cohort.duplicated(identity).any():
        raise ValueError("Duplicate newcomer identities")
    saved = json.loads((input_dir / "walkforward_summary.json").read_text())
    frames, summaries = [], {}
    for estimator in ESTIMATORS:
        fits = [
            alternative_fold(
                pairs, cohort, s, estimator=estimator, n_boot=n_boot, seed=seed
            )
            for s in wf.SEASONS
        ]
        rows = pd.concat([wf.fold_rows(f) for f in fits], ignore_index=True)
        rows["estimator"] = estimator
        metrics = {
            arm: {
                "mae": float(np.abs(rows[arm] - rows.y).mean()),
                "rmse": float(np.sqrt(np.mean((rows[arm] - rows.y) ** 2))),
                "bias": float((rows[arm] - rows.y).mean()),
                "invalid_predictions": int((~np.isfinite(rows[arm])).sum()),
            }
            for arm in ARMS
        }
        if estimator == "exposure_weighted":
            expected = {
                arm: saved[
                    "pooled"
                    if arm not in ("rtm", "rtm_plus_league")
                    else "rtm_comparator"
                ][f"mae_{arm}"]
                for arm in ARMS
            }
            differences = {
                arm: abs(metrics[arm]["mae"] - expected[arm]) for arm in ARMS
            }
            if not all(np.isfinite(v) and v <= 1e-6 for v in differences.values()):
                raise ValueError(
                    f"Primary walk-forward baseline mismatch: {differences}"
                )
        frames.append(rows)
        summaries[estimator] = {
            "n": len(rows),
            "metrics": metrics,
            "folds": [
                {
                    "season": f["season"],
                    "n": f["n"],
                    "k_lag": f["k_lag"],
                    "collapsed_blocks": f["collapsed_blocks"],
                    "reliable_cells": int(f["table"].reliable.sum()),
                }
                for f in fits
            ],
        }
        print(f"[alternative] {estimator}: {metrics}", flush=True)
    base = frames[0]
    contrasts = []
    for alternative in frames[1:]:
        if not alternative[["season", "player_name"]].equals(
            base[["season", "player_name"]]
        ):
            raise ValueError("Alternative forecast population mismatch")
        for arm in ARMS:
            delta, lo, hi = wf.paired_cluster_bootstrap(
                base[arm].to_numpy(),
                alternative[arm].to_numpy(),
                base.y.to_numpy(),
                base.cluster.to_numpy(),
                seed=seed,
            )
            contrasts.append(
                {
                    "estimator": alternative.estimator.iloc[0],
                    "arm": arm,
                    "mae_alternative_minus_primary": delta,
                    "ci": [lo, hi],
                }
            )
    all_rows = pd.concat(frames, ignore_index=True)
    out_dir.mkdir(parents=True, exist_ok=True)
    all_rows.to_parquet(out_dir / "alternative_forecast_rows.parquet", index=False)
    files = [
        input_dir / p
        for p in ["pairs.parquet", "switchers.parquet", "walkforward_summary.json"]
    ]
    summary = {
        "status": "complete",
        "estimators": summaries,
        "paired_contrasts": contrasts,
        "primary_max_abs_mae_difference": max(differences.values()),
        "n_boot_factors": n_boot,
        "n_boot_contrasts": wf.N_BOOT,
        "seed": seed,
        "input_hashes": {p.name: sha256_file(p) for p in files},
        "interpretation": (
            "Retrospective estimator sensitivity in existing "
            "five-arm pipeline; not Study B chronological redesign"
        ),
    }
    write_json(out_dir / "alternative_forecast_summary.json", summary)
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, default=OUT)
    parser.add_argument("--input-dir", type=Path, default=PRIVATE / "inputs")
    parser.add_argument("--cache-dir", type=Path, default=PRIVATE / "estimator_cache")
    parser.add_argument("--template-root", type=Path, default=REPO / "data/processed")
    parser.add_argument(
        "--calibration-dir",
        type=Path,
        default=REPO
        / "docs/research/artifacts/translation-estimator-synthetic-2026-09-04",
    )
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--reps", type=int, default=200)
    parser.add_argument("--check-reps", type=int, default=50)
    parser.add_argument("--n-boot", type=int, default=500)
    parser.add_argument("--check-boot", type=int, default=2000)
    parser.add_argument("--alternatives-only", action="store_true")
    parser.add_argument("--skip-alternatives", action="store_true")
    parser.add_argument("--render", action="store_true")
    args = parser.parse_args(argv)
    if args.render:
        summary = json.loads(
            (args.out_dir / "estimator_audit_summary.json").read_text()
        )
        rows = pd.read_parquet(args.out_dir / "estimator_audit_rows.parquet")
        assert_complete(rows, summary["cells"])
        (args.out_dir / "estimator_audit_note.md").write_text(render_note(summary))
        return 0
    if not (
        1 <= args.workers <= 4
        and args.reps >= args.check_reps >= 0
        and args.n_boot >= 2
        and args.check_boot > args.n_boot
    ):
        parser.error(
            "Require workers 1..4, reps>=check-reps>=0, and check-boot>n-boot>=2"
        )
    args.out_dir.mkdir(parents=True, exist_ok=True)
    if args.alternatives_only:
        run_alternative_forecasts(args.input_dir, args.out_dir, seed=args.seed)
        return 0
    templates = {
        "api": args.template_root / "translation",
        "proballers": args.template_root / "translation_proballers_2026-08-21",
    }
    source_files = [
        Path(__file__),
        REPO / "scripts/translation_research_common.py",
        REPO / "scripts/simulate_translation_estimator.py",
        REPO / "scripts/build_league_factors.py",
    ]
    input_files = [p / "league_factor_pairs.parquet" for p in templates.values()] + [
        args.calibration_dir / f"summary_{t}.json" for t in templates
    ]
    config = {
        "seed": args.seed,
        "reps": args.reps,
        "check_reps": args.check_reps,
        "n_boot": args.n_boot,
        "check_boot": args.check_boot,
        "factors": FACTORS,
        "scenarios": SCENARIOS,
        "estimators": ESTIMATORS,
        "min_pairs": 75,
    }
    digest, provenance = cache_key(config, source_files + input_files)
    tasks, cells = [], {}
    for name, directory in templates.items():
        pairs = pd.read_parquet(directory / "league_factor_pairs.parquet")
        if name == "api":
            pairs = pairs[~pairs.league_src.isin(sim.blf.API_SIDE_EXCLUDED_SOURCES)]
        pairs = pairs.reset_index(drop=True)
        if pairs.duplicated(["player_name", "season"]).any():
            raise ValueError(f"Duplicated template identity in {name}")
        calibration = json.loads(
            (args.calibration_dir / f"summary_{name}.json").read_text()
        )
        cal = calibration["calibration"]
        if (
            max(v["rel_error"] for v in calibration["calibration_check"].values())
            > sim.CALIBRATION_TOL
        ):
            raise ValueError(f"Saved calibration fails for {name}")
        cells[name] = list(pairs.groupby(["league_src", "league_dest"]).groups)
        for scenario in SCENARIOS:
            for truth in FACTORS:
                for rep in range(args.reps):
                    key = (name, scenario, truth, rep)
                    tasks.append(
                        dict(
                            template=name,
                            scenario=scenario,
                            truth=truth,
                            replicate=rep,
                            pairs=pairs,
                            cal=cal,
                            cells=cells[name],
                            table_seed=stable_seed(args.seed, *key, "table"),
                            fit_seed=stable_seed(args.seed, *key, "bootstrap"),
                            depths=[args.n_boot, args.check_boot]
                            if rep < args.check_reps
                            else [args.n_boot],
                            cache_path=str(
                                args.cache_dir
                                / digest
                                / f"{name}_{scenario}_{truth}_{rep}.parquet"
                            ),
                        )
                    )
    write_json(
        args.out_dir / "estimator_audit_manifest.json",
        {
            "status": "incomplete",
            "cache_key": digest,
            **provenance,
            "expected_table_tasks": len(tasks),
        },
    )
    frames = []
    executor = (
        ProcessPoolExecutor(max_workers=args.workers) if args.workers > 1 else None
    )
    try:
        results = (
            executor.map(_cached_replicate, tasks, chunksize=1)
            if executor
            else map(_cached_replicate, tasks)
        )
        for i, frame in enumerate(results, 1):
            frames.append(frame)
            if i % 25 == 0 or i == len(tasks):
                print(f"[audit] {i}/{len(tasks)} table replicates complete", flush=True)
    finally:
        if executor:
            executor.shutdown()
    rows = pd.concat(frames, ignore_index=True)
    assert_complete(
        rows,
        cells,
        reps=args.reps,
        check_reps=args.check_reps,
        n_boot=args.n_boot,
        check_boot=args.check_boot,
    )
    full = (
        args.reps == 200
        and args.check_reps == 50
        and args.n_boot == 500
        and args.check_boot == 2000
        and args.seed == 0
    )
    summary = summarise(rows) | {
        "status": "complete" if full else "incomplete",
        "config": config,
        "cells": cells,
        "cache_key": digest,
        "completion_reason": "all preregistered keys present"
        if full
        else "reduced or altered configuration; publication rendering refused",
        **provenance,
    }
    rows.to_parquet(args.out_dir / "estimator_audit_rows.parquet", index=False)
    write_json(args.out_dir / "estimator_audit_summary.json", summary)
    write_json(
        args.out_dir / "estimator_audit_manifest.json",
        {
            "status": summary["status"],
            "cache_key": digest,
            **provenance,
            "expected_table_tasks": len(tasks),
            "completed_table_tasks": len(frames),
            "rows_sha256": sha256_file(args.out_dir / "estimator_audit_rows.parquet"),
        },
    )
    if full:
        (args.out_dir / "estimator_audit_note.md").write_text(render_note(summary))
    if not args.skip_alternatives:
        run_alternative_forecasts(args.input_dir, args.out_dir, seed=args.seed)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
