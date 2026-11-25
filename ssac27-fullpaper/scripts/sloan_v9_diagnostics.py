"""Registered overlap and error diagnostics; no model or threshold selection.

Threats: changed evidence, nonnested populations, positional joins, hidden refusals,
outcome-selected examples, and error contributions that do not conserve totals.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts import sloan_full_refit as refit  # noqa: E402
from scripts import sloan_context_benchmarks as benchmark  # noqa: E402
from scripts.translation_research_common import sha256_file  # noqa: E402

PROTOCOL = ROOT / "docs/research/sloan-v9-diagnostics-preregistration-2026-09-19.md"
VARIANTS = (
    "official_corrected",
    "verified_same_club_full",
    "overlap_keys_full",
    "same_club",
)
PAIR_KEY = ["player_name", "season"]
BASE = "history_destination_slope"
ADJUSTED = BASE + "_scheduled"
CONTRASTS = {
    "destination": (BASE, ADJUSTED),
    **{
        f"source_{p}": (f"source_ridge_{p}", f"source_ridge_{p}_scheduled")
        for p in benchmark.PENALTIES
    },
}
PRETRIM = frozenset(
    (
        "included",
        "no_common_window",
        "fewer_than_eight_after_trimming",
        "invalid_appearance_minutes",
    )
)


def dump(path, obj):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(
        json.dumps(obj, indent=2, sort_keys=True, allow_nan=False) + "\n"
    )


def keys(frame, columns):
    if frame[columns].isna().any().any() or frame.duplicated(columns).any():
        raise ValueError("missing or duplicate keys")
    return set(map(tuple, frame[columns].to_numpy()))


def restrict(frame, wanted, columns):
    keys(frame, columns)
    return frame.loc[[tuple(k) in wanted for k in frame[columns].to_numpy()]].copy()


def build_pools(corrected, overlap, flow):
    all_keys, overlap_keys = keys(corrected, PAIR_KEY), keys(overlap, PAIR_KEY)
    if keys(flow, PAIR_KEY) != all_keys:
        raise ValueError("flow does not conserve original pair keys")
    included = flow.loc[flow.status.eq("included")]
    if keys(included, PAIR_KEY) != overlap_keys:
        raise ValueError("overlap keys differ from accepted evidence")
    verified = flow.loc[flow.status.isin(PRETRIM)]
    evidence = ["person_code", "club_code", "window_start", "window_end"]
    if verified[evidence].isna().any().any():
        raise ValueError("pretrim evidence is incomplete")
    verified_keys = keys(verified, PAIR_KEY)
    if not overlap_keys <= verified_keys <= all_keys:
        raise ValueError("factor pools are not nested")
    return {
        "official_corrected": corrected.copy(),
        "verified_same_club_full": restrict(corrected, verified_keys, PAIR_KEY),
        "overlap_keys_full": restrict(corrected, overlap_keys, PAIR_KEY),
        "same_club": overlap.copy(),
    }


def prepare(completion, out):
    completion, out = Path(completion), Path(out)
    if out.exists() and any(out.iterdir()):
        raise ValueError("output must be new or empty")
    original = completion / "model-inputs"
    corrected, cohort, a_meta = refit.load_variant(original / "official_corrected")
    overlap, d_cohort, d_meta = refit.load_variant(original / "same_club")
    pd.testing.assert_frame_equal(cohort, d_cohort)
    flow_path = original / "same_club/pair_flow.parquet"
    flow = pd.read_parquet(flow_path)
    pools = build_pools(corrected, overlap, flow)
    refit.verify(completion / "full-refits-new")
    inputs = {
        str(original / name / "variant.json"): sha256_file(
            original / name / "variant.json"
        )
        for name in ("official_corrected", "same_club")
    }
    inputs[str(flow_path)] = sha256_file(flow_path)
    for name, frame in pools.items():
        target = out / name
        target.mkdir(parents=True)
        frame.to_parquet(target / "pairs.parquet", index=False)
        shutil.copyfile(
            original / "official_corrected/cohort.parquet", target / "cohort.parquet"
        )
        dump(
            target / "variant.json",
            {
                "schema_version": 1,
                "status": "prepared",
                "variant": name,
                "reference_variant": None,
                "files": {
                    file: sha256_file(target / file)
                    for file in ("pairs.parquet", "cohort.parquet")
                },
                "protocol_sha256": sha256_file(PROTOCOL),
                "generator_sha256": sha256_file(Path(__file__)),
                "source_metadata": {"corrected": a_meta, "overlap": d_meta},
                "source_hashes": inputs,
                "pairs": len(frame),
            },
        )
    flow.to_parquet(out / "pair_flow.parquet", index=False)
    dump(
        out / "preparation.json",
        {
            "status": "prepared",
            "counts": {k: len(v) for k, v in pools.items()},
            "rejection_counts": flow.status.value_counts().sort_index().to_dict(),
            "source_hashes": inputs,
            "protocol_sha256": sha256_file(PROTOCOL),
            "code_sha256": sha256_file(Path(__file__)),
            "pair_flow_sha256": sha256_file(out / "pair_flow.parquet"),
        },
    )
    return {k: len(v) for k, v in pools.items()}


def errors(rows, arm):
    e = rows[arm].to_numpy(float) - rows.pir_per36_dest.to_numpy(float)
    if not len(e) or not np.isfinite(e).all():
        raise ValueError("empty or nonfinite error population")
    return {
        "n": len(e),
        "bias": float(e.mean()),
        "mae": float(np.abs(e).mean()),
        "rmse": float(np.sqrt(np.square(e).mean())),
        "median_absolute_error": float(np.median(np.abs(e))),
        "p90_absolute_error": float(np.quantile(np.abs(e), 0.9)),
    }


def paired(rows, baseline=BASE, adjusted=ADJUSTED):
    delta = (rows[baseline] - rows.pir_per36_dest).abs() - (
        rows[adjusted] - rows.pir_per36_dest
    ).abs()
    n = len(rows)
    if not n or not np.isfinite(delta).all():
        raise ValueError("empty or nonfinite paired population")
    return {
        "n": n,
        "mean_improvement": float(delta.mean()),
        "improved": float((delta > 1e-12).mean()),
        "worsened": float((delta < -1e-12).mean()),
        "tied": float((delta.abs() <= 1e-12).mean()),
        "relative_mae_improvement": float(delta.mean() / errors(rows, baseline)["mae"])
        if errors(rows, baseline)["mae"]
        else None,
    }


def breakdown(rows, column, baseline=BASE, adjusted=ADJUSTED):
    result = {}
    for name, group in rows.groupby(column, dropna=False, sort=True):
        result[str(name)] = {
            **paired(group, baseline, adjusted),
            "contribution_to_total": float(
                (
                    (group[baseline] - group.pir_per36_dest).abs()
                    - (group[adjusted] - group.pir_per36_dest).abs()
                ).sum()
                / len(rows)
            ),
            "baseline": errors(group, baseline),
            "adjusted": errors(group, adjusted),
        }
    if not np.isclose(
        sum(v["contribution_to_total"] for v in result.values()),
        paired(rows, baseline, adjusted)["mean_improvement"],
        atol=1e-12,
    ):
        raise ValueError("subgroup contributions do not reconcile")
    return result


def example(rows, fallback_only=False):
    # This selector deliberately cannot access the observed outcome.
    columns = [*refit.KEY, BASE, ADJUSTED, "scheduled_fallback"]
    eligible = rows[columns].copy()
    keys(eligible, refit.KEY)
    if fallback_only:
        eligible = eligible.loc[eligible.scheduled_fallback]
    if eligible.empty:
        return None
    change = (eligible[ADJUSTED] - eligible[BASE]).abs()
    eligible["distance"] = (change - change.median()).abs()
    chosen = eligible.sort_values(["distance", *refit.KEY], kind="stable").iloc[0]
    return {
        k: int(chosen[k]) if k == "season_dest" else str(chosen[k]) for k in refit.KEY
    }


def transitions(left, right):
    keys(left, refit.KEY)
    if keys(left, refit.KEY) != keys(right, refit.KEY):
        raise ValueError("transition forecast keys differ")
    merged = left.merge(right, on=refit.KEY, validate="1:1", suffixes=("_a", "_b"))
    if not np.allclose(
        merged.pir_per36_dest_a, merged.pir_per36_dest_b, atol=0, rtol=0
    ):
        raise ValueError("transition outcomes differ")
    change = (merged[ADJUSTED + "_a"] - merged.pir_per36_dest_a).abs() - (
        merged[ADJUSTED + "_b"] - merged.pir_per36_dest_b
    ).abs()
    result = {}
    for a in (False, True):
        for b in (False, True):
            selected = merged.scheduled_fallback_a.eq(
                a
            ) & merged.scheduled_fallback_b.eq(b)
            result[f"{int(a)}_to_{int(b)}"] = {
                "n": int(selected.sum()),
                "contribution_to_total": float(
                    change.loc[selected].sum() / len(merged)
                ),
                "mean_error_reduction": float(change.loc[selected].mean())
                if selected.any()
                else None,
            }
    if not np.isclose(
        sum(v["contribution_to_total"] for v in result.values()),
        change.mean(),
        atol=1e-12,
    ):
        raise ValueError("transition contributions do not reconcile")
    return {
        "n": len(merged),
        "adjusted_mae_reduction": float(change.mean()),
        "groups": result,
    }


def diagnose(run_dir, completion, out):
    run_dir, completion, out = map(Path, (run_dir, completion, out))
    if out.exists() and any(out.iterdir()):
        raise ValueError("output must be new or empty")
    refit.verify(run_dir)
    refit.verify(completion / "full-refits-new")
    manifest = json.loads((run_dir / "manifest.json").read_text())
    if tuple(manifest["variants"]) != VARIANTS:
        raise ValueError("unexpected variants")
    rows = {}
    for name in VARIANTS:
        for scenario in manifest["scenarios"]:
            label = scenario["name"]
            frame = pd.read_parquet(run_dir / name / label / "predictions.parquet")
            keys(frame, refit.KEY)
            rows[name, label] = frame
    reference_gates = {}
    for name in ("official_corrected", "same_club"):
        expected = pd.read_parquet(
            completion / "full-refits-new" / name / "reference/predictions.parquet"
        )
        observed = rows[name, "reference"]
        refit.source.keyed_equal(observed, expected, refit.KEY)
        reference_gates[name] = {
            "status": "reproduced",
            "tolerance": 1e-9,
            "reference_sha256": sha256_file(
                completion / "full-refits-new" / name / "reference/predictions.parquet"
            ),
        }
    target = set(map(tuple, manifest["reference_keys"]))
    common = target.intersection(
        *(keys(r.loc[r.scored], refit.KEY) for r in rows.values())
    )
    if not common:
        raise ValueError("empty common forecast support")
    summaries, references = {}, {}
    for name in VARIANTS:
        scenarios = {}
        for scenario in manifest["scenarios"]:
            label = scenario["name"]
            full = rows[name, label]
            selected = restrict(full, common, refit.KEY)
            scenarios[label] = {
                "n": len(selected),
                "native_n": int(full.scored.sum()),
                "target_unscored": len(target - keys(full.loc[full.scored], refit.KEY)),
                "refusals": full.scoring_exclusion.value_counts().to_dict(),
                "fallbacks": int(selected.scheduled_fallback.sum()),
                "metrics": {arm: errors(selected, arm) for arm in benchmark.ARMS},
                "contrasts": benchmark.summarize(selected, breakdown=False)[
                    "contrasts"
                ],
            }
        selected = restrict(rows[name, "reference"], common, refit.KEY)
        references[name] = selected
        summaries[name] = {
            "scenarios": scenarios,
            "paired": {c: paired(selected, *arms) for c, arms in CONTRASTS.items()},
            "by_season": {
                c: breakdown(selected, "season_dest", *arms)
                for c, arms in CONTRASTS.items()
            },
            "by_destination": {
                c: breakdown(selected, "league_dest", *arms)
                for c, arms in CONTRASTS.items()
            },
        }
    examples = []
    selected = references["official_corrected"]
    for mode in (False, True):
        chosen = example(selected, mode)
        if chosen is None:
            continue
        row = selected.loc[
            selected.player_name.eq(chosen["player_name"])
            & selected.season_dest.eq(chosen["season_dest"])
        ].iloc[0]
        fields = [
            *refit.KEY,
            "season_src",
            "league_src",
            "league_dest",
            "pir_per36_src",
            "prior_mean_pir36",
            "scheduled_multiplier_value",
            "scheduled_k",
            "scheduled_translated",
            "scheduled_fallback",
            "scheduled_reliable",
            "scheduled_reason",
            *benchmark.ARMS,
            "pir_per36_dest",
        ]
        clean = json.loads(row[fields].to_json())
        examples.append(
            {
                "selection": "fallback_median_change" if mode else "median_change",
                "information_cutoff": (
                    "before destination season " + str(chosen["season_dest"])
                ),
                "values": clean,
            }
        )
    result = {
        "status": "complete",
        "protocol_sha256": sha256_file(PROTOCOL),
        "generator_sha256": sha256_file(Path(__file__)),
        "refit_summary_sha256": sha256_file(run_dir / "summary.json"),
        "reference_reproduction": reference_gates,
        "common_n": len(common),
        "common_keys": sorted(common),
        "variants": summaries,
        "examples": examples,
        "transitions": {
            f"{a}__{b}": transitions(references[a], references[b])
            for a, b in zip(VARIANTS[:-1], VARIANTS[1:], strict=True)
        },
    }
    dump(out / "diagnostics.json", result)
    dump(
        out / "status.json",
        {
            "status": "complete",
            "diagnostics_sha256": sha256_file(out / "diagnostics.json"),
        },
    )
    return {"common_n": len(common), "reference_reproduction": reference_gates}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("prepare", "diagnose"))
    parser.add_argument("--completion", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--run-dir", type=Path)
    args = parser.parse_args()
    result = (
        prepare(args.completion, args.out)
        if args.command == "prepare"
        else diagnose(args.run_dir, args.completion, args.out)
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
