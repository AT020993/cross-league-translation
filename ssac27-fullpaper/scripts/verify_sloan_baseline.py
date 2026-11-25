# ruff: noqa: E402
"""Freeze and reproduce the Sloan baseline from saved aggregate inputs.

Threats: an inner join can hide missing factor cells; pandas can silently omit
non-finite errors; a cache can come from another corpus; and a presentation
refresh can conceal a changed scientific record. All four fail closed here.
This implements the baseline gate in the 2026-09-07 Sloan protocol, not a new
analysis. No game files are traversed or hashed. Corpus loading requires the
explicit --build-switchers option; a previous companion aggregate is sufficient.
"""

from __future__ import annotations

# Input identity must be checked before scientific imports or output creation.
if __name__ == "__main__":
    import sys as _research_sys
    from pathlib import Path as _ResearchPath

    _research_sys.path.insert(0, str(_ResearchPath(__file__).resolve().parents[1]))
    from src.research.execution import enter as _enter_research

    _enter_research(__file__)


import argparse
import contextlib
import hashlib
import io
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from threadpoolctl import threadpool_limits

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

import scripts.validate_translation_holdout as vh  # noqa: E402
import scripts.validate_translation_walkforward as wf  # noqa: E402

DEFAULT_INPUT = REPO / "data/processed/sloan_validation/inputs"
DEFAULT_OUT = REPO / "docs/research/artifacts/sloan-validation-2026-09-07"
FACTOR_TOLERANCE = 1e-9
MAE_TOLERANCE = 1e-6
ARMS = ("per_league", "one_global", "b0", "rtm", "rtm_plus_league")
INPUT_NAMES = (
    "pairs.parquet",
    "switchers.parquet",
    "league_factors.parquet",
    "walkforward_summary.json",
)


class BaselineMismatch(ValueError):
    """A protected file or a historical numerical result failed its gate."""


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def file_record(path: Path, *, root: Path, kind: str) -> dict:
    """Keep checkout-relative paths relocatable; external inputs stay explicit."""
    path = path.absolute()
    try:
        name = str(path.relative_to(root.absolute()))
    except ValueError:
        name = str(path)
    return {
        "path": name,
        "kind": kind,
        "sha256": sha256(path),
        "bytes": path.stat().st_size,
    }


def check_manifest(manifest: dict, *, root: Path = REPO) -> dict:
    """Reject scientific changes; report permitted presentation changes.

    The closed list records the original files, so newly added study outputs do
    not invalidate it. Missing protected files count as changes, not absence.
    """
    if manifest.get("status") != "passed" or not manifest.get("files"):
        raise BaselineMismatch("manifest is not a completed baseline")
    changes: dict[str, list[dict]] = {"scientific": [], "presentation": []}
    for record in manifest["files"]:
        kind = record["kind"]
        if kind not in changes:
            raise BaselineMismatch(f"unknown protection class: {kind}")
        path = root / record["path"]
        current = sha256(path) if path.is_file() else None
        if current != record["sha256"]:
            changes[kind].append(
                {"path": record["path"], "before": record["sha256"], "after": current}
            )
    if changes["scientific"]:
        names = ", ".join(row["path"] for row in changes["scientific"])
        raise BaselineMismatch(f"protected scientific records changed: {names}")
    return {"status": "passed", "presentation_changes": changes["presentation"]}


def compare_factors(recomputed: pd.DataFrame, reference: pd.DataFrame) -> dict:
    """Require every factor cell exactly once on both sides before comparing."""
    keys = ["league", "destination"]
    selected = reference[
        (reference.stat == vh.STAT)
        & (reference.era == vh.ERA)
        & (reference["sample"] == vh.SAMPLE)
    ]
    if recomputed.empty or selected.empty:
        raise BaselineMismatch("factor table is empty")
    try:
        joined = recomputed[keys + ["factor"]].merge(
            selected[keys + ["factor"]],
            on=keys,
            how="outer",
            validate="one_to_one",
            suffixes=("", "_reference"),
            indicator=True,
        )
    except pd.errors.MergeError as exc:
        raise BaselineMismatch("factor cells are not unique") from exc
    if not joined["_merge"].eq("both").all():
        raise BaselineMismatch("factor cell keys differ from the reference")
    values = joined[["factor", "factor_reference"]].to_numpy(dtype=float)
    if not np.isfinite(values).all():
        raise BaselineMismatch("factor table contains non-finite values")
    gap = float(np.abs(values[:, 0] - values[:, 1]).max())
    if gap >= FACTOR_TOLERANCE:
        raise BaselineMismatch(f"factor table differs by {gap:.12g}")
    return {
        "n_cells": len(joined),
        "max_absolute_difference": gap,
        "tolerance_strictly_below": FACTOR_TOLERANCE,
    }


def compare_maes(rows: pd.DataFrame, summary: dict) -> dict:
    """Score five arms on one complete cohort, never pandas' per-arm dropna."""
    if rows.empty or len(rows) != summary["n_pooled"]:
        raise BaselineMismatch(
            f"walk-forward row count differs: {len(rows)} != {summary['n_pooled']}"
        )
    if not np.isfinite(rows[["y", *ARMS]].to_numpy(dtype=float)).all():
        raise BaselineMismatch("walk-forward outcome or prediction is non-finite")
    expected = {
        "per_league": summary["pooled"]["mae_per_league"],
        "one_global": summary["pooled"]["mae_one_global"],
        "b0": summary["pooled"]["mae_b0"],
        "rtm": summary["rtm_comparator"]["mae_rtm"],
        "rtm_plus_league": summary["rtm_comparator"]["mae_rtm_plus_league"],
    }
    result = {}
    for arm in ARMS:
        value = float(np.abs(rows[arm].to_numpy() - rows.y.to_numpy()).mean())
        gap = abs(value - expected[arm])
        if not np.isfinite(expected[arm]) or gap >= MAE_TOLERANCE:
            raise BaselineMismatch(
                f"{arm} MAE does not reproduce: {value:.12g} != {expected[arm]:.12g}"
            )
        result[arm] = {
            "recomputed": value,
            "reference": expected[arm],
            "absolute_difference": gap,
            "tolerance_strictly_below": MAE_TOLERANCE,
        }
    return result


def reproduce(
    pairs: pd.DataFrame,
    switchers: pd.DataFrame,
    factors: pd.DataFrame,
    summary: dict,
) -> dict:
    """Use the same estimator and folds as the existing companion reproduce.py."""
    if len(pairs) != summary["n_pairs"]:
        raise BaselineMismatch("pair count differs from historical summary")
    if list(wf.SEASONS) != summary["seasons"]:
        raise BaselineMismatch("walk-forward seasons differ from historical summary")
    with threadpool_limits(limits=1):
        with contextlib.redirect_stdout(io.StringIO()):
            fitted = vh.fit_factors(pairs, label="sloan_baseline")
        factor_check = compare_factors(fitted, factors)
        print(
            f"[baseline] factor cells={factor_check['n_cells']} reproduced", flush=True
        )
        cohorts = switchers[
            (switchers.was_cont == 0)
            & ~switchers.league_src.isin(vh.EXCLUDED_SOURCE)
            & (switchers.pir_per36_src > 0)
        ]
        folds = []
        counts = []
        for season in wf.SEASONS:
            fold = wf.one_season(pairs, cohorts, season)
            fold["rtm_arms"] = wf._fit_rtm_arms(fold)
            rows = wf.fold_rows(fold)
            folds.append(rows)
            counts.append({"season": season, "n_before_finite_filter": len(rows)})
            print(f"[baseline] fold={season} rows={len(rows)}", flush=True)
        all_rows = pd.concat(folds, ignore_index=True)
        scored = all_rows[np.isfinite(all_rows.per_league)].copy()
        maes = compare_maes(scored, summary)
    return {
        "factor_table": factor_check,
        "walkforward_maes": maes,
        "n_pairs": len(pairs),
        "n_switchers_unfiltered": len(switchers),
        "n_newcomers_filtered": len(cohorts),
        "n_pooled": len(scored),
        "n_excluded_nonfinite_per_league": len(all_rows) - len(scored),
        "folds": counts,
    }


def prepare_inputs(
    input_dir: Path,
    *,
    root: Path = REPO,
    switchers_from: Path | None = None,
    build_switchers: bool = False,
) -> None:
    """Cache aggregate inputs locally, refusing to replace a different cache."""
    source = root / "data/processed/translation"
    sources = {
        "pairs.parquet": source / "league_factor_pairs.parquet",
        "league_factors.parquet": source / "league_factors.parquet",
        "walkforward_summary.json": source / "walkforward_summary.json",
    }
    if switchers_from is not None:
        sources["switchers.parquet"] = switchers_from
        companion_pairs = switchers_from.parent / "pairs.parquet"
        if not companion_pairs.exists() or sha256(companion_pairs) != sha256(
            sources["pairs.parquet"]
        ):
            raise BaselineMismatch(
                "switchers companion pair-table hash differs or is absent"
            )
    input_dir.mkdir(parents=True, exist_ok=True)
    for name, src in sources.items():
        dst = input_dir / name
        if dst.exists():
            if sha256(dst) != sha256(src):
                raise BaselineMismatch(f"refusing to replace differing cached {name}")
        else:
            shutil.copyfile(src, dst)
    switcher_path = input_dir / "switchers.parquet"
    if not switcher_path.exists() and build_switchers:
        build_switchers_table().to_parquet(switcher_path, index=False)
    missing = [name for name in INPUT_NAMES if not (input_dir / name).is_file()]
    if missing:
        raise BaselineMismatch(
            f"missing aggregate inputs {missing}; supply --switchers-from or "
            "explicitly authorize a corpus load with --build-switchers"
        )


def build_switchers_table() -> "pd.DataFrame":
    """The consecutive-season transfers the validators score, unfiltered.

    Computed from the corpus so the public export needs no game rows; the
    scripts' own filters (``was_cont``, excluded sources, positive rates) run on
    it visibly in the export's ``reproduce.py``.

    Lives here rather than in ``scripts/export_public_translation_repo.py``
    because this module is in that exporter's public allowlist while the
    exporter is not — a build tool has no place in the repository it builds. The
    exporter's own import-closure gate caught the cycle and refused to cut
    (2026-09-20). It is not in ``scripts/translation_research_common.py`` either:
    that file's sha256 is pinned in the committed Sloan benchmark
    (``sloan_context_benchmarks.CODE_FILES``), so editing it invalidates a frozen
    scientific record.
    """
    import contextlib
    import io

    import scripts.validate_translation_holdout as vh

    games, _ = vh.load_corpus("api")
    with contextlib.redirect_stdout(io.StringIO()):
        switch, _ = vh.build_switchers(games)
    return switch.reset_index(drop=True)


def snapshot_inputs(input_dir: Path, *, root: Path = REPO) -> list[dict]:
    """Hash bounded research/forecast roots, never the raw-game trees.

    Numeric figure readbacks are protected scientific records. Images and the
    abstract text are presentation, which the approved revision may replace.
    """
    paths: dict[Path, str] = {}
    for name in INPUT_NAMES:
        paths[input_dir / name] = "scientific"
    for directory in (
        "data/processed/translation",
        "data/processed/predictions",
        "docs/research/artifacts/holdout-proballers-2026-08-21",
        "docs/research/artifacts/prelock-program-2026-09",
    ):
        for path in (root / directory).glob("*"):
            if path.is_file() and path.suffix in {".parquet", ".json", ".csv"}:
                paths[path] = "scientific"
    for relative in (
        "scripts/build_league_factors.py",
        "scripts/validate_translation_holdout.py",
        "scripts/validate_translation_walkforward.py",
        "docs/research/sloan-validation-preregistration-2026-09-07.md",
    ):
        paths[root / relative] = "scientific"
    for path in (root / "docs/plans/figures").glob("sloan*"):
        if path.is_file():
            paths[path] = "presentation" if path.suffix == ".png" else "scientific"
    paths[root / "docs/plans/sloan-ssac27-abstract-draft.md"] = "presentation"
    return [
        file_record(path, root=root, kind=kind)
        for path, kind in sorted(paths.items(), key=lambda item: str(item[0]))
    ]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--switchers-from", type=Path)
    parser.add_argument("--build-switchers", action="store_true")
    parser.add_argument("--check-manifest", type=Path)
    args = parser.parse_args(argv)
    try:
        if args.check_manifest:
            print(
                json.dumps(
                    check_manifest(json.loads(args.check_manifest.read_text())),
                    indent=2,
                )
            )
            return 0
        if args.seed != 0 or vh.SEED != 0 or args.workers != 1:
            raise BaselineMismatch("historical baseline requires --seed 0 --workers 1")
        manifest_path = args.out_dir / "baseline_manifest.json"
        if manifest_path.exists():
            check_manifest(json.loads(manifest_path.read_text()))
            raise BaselineMismatch(
                "baseline manifest already exists; use --check-manifest"
            )
        prepare_inputs(
            args.input_dir,
            switchers_from=args.switchers_from,
            build_switchers=args.build_switchers,
        )
        files = snapshot_inputs(args.input_dir)
        summary = json.loads((args.input_dir / "walkforward_summary.json").read_text())
        result = reproduce(
            pd.read_parquet(args.input_dir / "pairs.parquet"),
            pd.read_parquet(args.input_dir / "switchers.parquet"),
            pd.read_parquet(args.input_dir / "league_factors.parquet"),
            summary,
        )
        manifest = {
            "schema_version": 1,
            "status": "passed",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "git_sha": subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=REPO, text=True
            ).strip(),
            "generator_sha256": sha256(Path(__file__)),
            "seed": args.seed,
            "workers": args.workers,
            "input_dir": str(args.input_dir.absolute()),
            "scientific_scope": "existing factor table and five walk-forward MAEs",
            "not_recomputed": [
                "original Proballers holdout record",
                "API holdout record, reliability and R-squared ceiling",
                "forecast sets, refusals and prediction intervals",
                "numeric submission-figure readbacks",
            ],
            "files": files,
            "reproduction": result,
        }
        # Detect an input modified by another process while the fits ran.
        check_manifest(manifest)
        args.out_dir.mkdir(parents=True, exist_ok=True)
        manifest_path.write_text(json.dumps(manifest, indent=2, allow_nan=False) + "\n")
        print(f"[baseline] PASS: {manifest_path}")
        return 0
    except (BaselineMismatch, FileNotFoundError) as exc:
        print(f"[baseline] STOP: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
