"""Frozen support-policy amendment; no fitting or threshold selection.

Threats: reused outcomes, changed target keys, coerced unknown gates, current
rather than historical support, omitted-season leakage, and subset-only gains.
All 56 inventories and support predicates pass before any policy is scored.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from scripts import sloan_v10_slopes as frozen  # noqa: E402

benchmark, refit, diagnostics = frozen.benchmark, frozen.refit, frozen.diagnostics
sha256_file, dump, read_json = frozen.sha256_file, frozen.dump, frozen.read_json
KEY = frozen.KEY
VARIANTS = frozen.VARIANTS
PENALTIES = frozen.PENALTIES
FAMILIES = ("source_ridge", "cell_slope")
PARENTS = tuple(f"{family}_{p}" for family in FAMILIES for p in PENALTIES)
PREDICTIONS = tuple(a for p in PARENTS for a in (p, p + "_scheduled"))
SCENARIOS = refit.scenario_matrix(range(2016, 2026))
TARGET_N = 674
FROZEN_SUMMARY_SHA256 = (
    "58f2cdc5a032415de2b2331e7aaa8e9975914903daac156970edfe37a28dc638"
)
PROTOCOL = ROOT / "docs/research/sloan-v10-support-policy-preregistration-2026-09-20.md"
CODE_FILES = ("scripts/sloan_v10_support_policy.py", *frozen.CODE_FILES)
IDENTITY = [
    *KEY,
    "season_src",
    "league_src",
    "league_dest",
    "cluster",
    "pir_per36_dest",
]
FROZEN_FILES = (
    "features.parquet",
    "predictions.parquet",
    "fits.json",
    "reproduction.json",
)
FAILURE = (
    "the existing reliability gate is not demonstrated to select useful "
    "incremental translation on this target"
)


def genuine_bool(values, name):
    """Do not turn nulls, strings or numeric sentinels into a routing decision."""
    series = pd.Series(values)
    if (
        series.isna().any()
        or not series.map(lambda x: isinstance(x, (bool, np.bool_))).all()
    ):
        raise ValueError("not a genuine Boolean: " + name)
    return series.to_numpy(dtype=bool)


def _equal_frames(left, right, columns, label):
    try:
        pd.testing.assert_frame_equal(
            left.sort_values(KEY)[columns].reset_index(drop=True),
            right.sort_values(KEY)[columns].reset_index(drop=True),
            check_dtype=False,
            check_exact=True,
        )
    except (AssertionError, KeyError) as exc:
        raise ValueError(label + " changed") from exc


def _inventory(root, expected, recorded):
    if set(recorded) != set(expected):
        raise ValueError("incomplete frozen output inventory")
    for name, digest in recorded.items():
        refit._check(benchmark._safe_child(root, name), digest)


def verify_inputs(analysis, v9_run):
    """Verify hashes only; no model, metric or policy calculation."""
    analysis, v9_run = Path(analysis).resolve(), Path(v9_run).resolve()
    state = read_json(analysis / "status.json")
    if state.get("status") != "complete" or state.get("analysis_status") != "complete":
        raise ValueError("frozen v10 run is incomplete")
    refit._check(analysis / "summary.json", FROZEN_SUMMARY_SHA256)
    refit._check(analysis / "summary.json", state.get("summary_sha256"))
    summary = read_json(analysis / "summary.json")
    if summary.get("status") != "complete":
        raise ValueError("frozen v10 summary is incomplete")
    refit._check(analysis / "manifest.json", summary["manifest_sha256"])
    manifest = read_json(analysis / "manifest.json")
    for name in (
        "protocol_sha256",
        "code_hashes",
        "input_hashes",
        "v9_diagnostics_sha256",
        "v9_preparation_sha256",
    ):
        if summary[name] != manifest[name]:
            raise ValueError("frozen manifest binding mismatch: " + name)
    if (
        tuple(manifest["variants"]) != VARIANTS
        or manifest["scenarios"] != SCENARIOS
        or manifest["penalties"] != list(PENALTIES)
        or manifest["arms"] != list(frozen.ARMS)
        or set(summary["variants"]) != set(VARIANTS)
    ):
        raise ValueError("frozen scenario/arm definition changed")
    target_list = manifest["target_keys"]
    target = set(map(tuple, target_list))
    if (
        len(target) != TARGET_N
        or len(target_list) != TARGET_N
        or summary["target_n"] != TARGET_N
        or summary["common_n"] != TARGET_N
        or len(summary["common_keys"]) != TARGET_N
        or set(map(tuple, summary["common_keys"])) != target
    ):
        raise ValueError("frozen target key mismatch")
    if set(manifest["code_hashes"]) != set(frozen.CODE_FILES):
        raise ValueError("frozen code inventory changed")
    for name, digest in manifest["code_hashes"].items():
        refit._check(benchmark._safe_child(ROOT, name), digest)
    refit._check(frozen.PROTOCOL, manifest["protocol_sha256"])
    expected = {
        f"{v}/{s['name']}/{name}"
        for v in VARIANTS
        for s in SCENARIOS
        for name in FROZEN_FILES
    }
    _inventory(analysis, expected, summary["output_hashes"])
    # A relocated v9 capsule may preserve its model-inputs/full-refits siblings.
    sibling = v9_run.parent / "model-inputs"
    inputs = sibling if sibling.is_dir() else Path(manifest["inputs"]).resolve()
    upstream, upstream_hashes = frozen.verify_inputs(inputs, v9_run)
    if (
        upstream_hashes != manifest["input_hashes"]
        or upstream["scenarios"] != SCENARIOS
        or set(map(tuple, upstream["reference_keys"])) != target
    ):
        raise ValueError("upstream v9 binding mismatch")
    hashes = {
        **{
            f"v10/{n}": sha256_file(analysis / n)
            for n in ("manifest.json", "summary.json", "status.json")
        },
        **{f"v10/{n}": h for n, h in summary["output_hashes"].items()},
        **upstream_hashes,
    }
    return {
        "analysis": analysis,
        "v9_run": v9_run,
        "inputs": inputs,
        "target": target,
        "manifest": manifest,
        "input_hashes": hashes,
    }


def validate_support(rows, audit, scenario):
    """Check the full old cutoff history, then reconstruct the stored predicate."""
    gate = genuine_bool(rows.scheduled_reliable, "scheduled_reliable")
    fallback = genuine_bool(rows.scheduled_fallback, "scheduled_fallback")
    if not np.array_equal(gate, ~fallback):
        raise ValueError("reliability and fallback disagree")
    omitted = scenario["omitted_season"]
    for cutoff, by_design in audit["cutoffs"].items():
        season = int(cutoff)
        for kind in refit.design.DESIGNS:
            info = by_design[kind]
            if any(
                int(year) >= season or int(year) == omitted
                for year in info["factor_season_counts"]
            ):
                raise ValueError("future or omitted factor support")
            lag = pd.DataFrame(info["lag_keys"], columns=KEY)
            frozen.key_set(lag)
            if lag.season_dest.ge(season).any() or lag.season_dest.eq(omitted).any():
                raise ValueError("future or omitted lag support")
    result = rows.copy()
    result["scheduled_cell_present"] = False
    result["scheduled_n_pairs"] = pd.array([None] * len(result), dtype="Int64")
    result["scheduled_n_clusters"] = pd.array([None] * len(result), dtype="Int64")
    for season, group in result.groupby("season_dest", sort=True):
        info = audit["cutoffs"].get(str(int(season)), {}).get("scheduled")
        if info is None:
            raise ValueError("missing historical cutoff")
        cells = pd.DataFrame(info["cells"])
        if len(cells):
            if (
                cells[["league", "destination"]].isna().any().any()
                or cells.duplicated(["league", "destination"]).any()
            ):
                raise ValueError("missing or duplicate cutoff cell")
            reliable = genuine_bool(cells.reliable, "cell.reliable")
            collapsed = genuine_bool(cells.pooled_collapsed, "cell.pooled_collapsed")
            counts = cells[["n_pairs", "n_clusters"]].to_numpy(float)
            if (
                not np.isfinite(counts).all()
                or (counts < 0).any()
                or (counts != np.floor(counts)).any()
            ):
                raise ValueError("invalid historical support count")
            reconstructed = (
                (cells.n_pairs.to_numpy() >= 75)
                & np.isfinite(pd.to_numeric(cells.se, errors="raise").to_numpy(float))
                & ~collapsed
            )
            if not np.array_equal(reliable, reconstructed):
                raise ValueError("stored cell reliability disagrees with original rule")
            # JSON null factor becomes NaN, preserving the original lookup semantics.
            cells["factor"] = pd.to_numeric(cells.factor, errors="raise")
        _, old_fallback, old_gate = refit.design.lookup(cells, group)
        if not np.array_equal(
            old_gate, genuine_bool(group.scheduled_reliable, "gate")
        ) or not np.array_equal(
            old_fallback, genuine_bool(group.scheduled_fallback, "fallback")
        ):
            raise ValueError("stored reliability disagrees with historical cutoff")
        lookup = {(r.league, r.destination): r for r in cells.itertuples()}
        for i, row in group.iterrows():
            cell = lookup.get((row.league_src, row.league_dest))
            if cell is not None:
                result.loc[i, "scheduled_cell_present"] = True
                result.loc[i, "scheduled_n_pairs"] = int(cell.n_pairs)
                result.loc[i, "scheduled_n_clusters"] = int(cell.n_clusters)
    return result


def validate_rows(rows, target):
    if frozen.key_set(rows) != target or len(rows) != len(target):
        raise ValueError("forecast keys disagree with frozen target")
    for name in ("scheduled_reliable", "scheduled_fallback", "v10_scored"):
        values = genuine_bool(rows[name], name)
        if name == "v10_scored" and not values.all():
            raise ValueError("frozen target contains a refusal")
    for name in ("player_name", "league_src", "league_dest", "cluster"):
        if rows[name].isna().any() or rows[name].astype(str).eq("").any():
            raise ValueError("missing forecast identity/category")
    if not np.isfinite(rows[[*PREDICTIONS, "pir_per36_dest"]].to_numpy(float)).all():
        raise ValueError("nonfinite frozen prediction or unknown outcome")


def load_validated(context):
    """Validate every scenario before returning any rows for new calculations."""
    records, reference = {}, None
    for variant in VARIANTS:
        for scenario in SCENARIOS:
            name = scenario["name"]
            directory = context["analysis"] / variant / name
            rows = pd.read_parquet(directory / "predictions.parquet")
            validate_rows(rows, context["target"])
            old = pd.read_parquet(
                context["v9_run"] / variant / name / "predictions.parquet"
            )
            _equal_frames(
                rows,
                old,
                [
                    *IDENTITY,
                    "scheduled_reliable",
                    "scheduled_fallback",
                    *(a for a in PREDICTIONS if a.startswith("source_ridge_")),
                ],
                "old forecasts/outcomes",
            )
            if reference is None:
                reference = rows
            else:
                _equal_frames(rows, reference, IDENTITY, "common outcome/identity")
            receipt = read_json(directory / "reproduction.json")
            if (
                receipt["status"] != "reproduced"
                or receipt["n"] != len(rows)
                or receipt["arms"] != list(benchmark.ARMS)
                or receipt["folds"] != len(benchmark.SEASONS)
                or receipt["omitted_season"] != scenario["omitted_season"]
            ):
                raise ValueError("old-arm reproduction receipt mismatch")
            audit = read_json(context["v9_run"] / variant / name / "fits.json")
            checked = validate_support(rows, audit, scenario)
            records[variant, name] = checked.sort_values(KEY).reset_index(drop=True)
    return records


def route(rows):
    """Select existing forecasts using only the saved gate, never outcomes."""
    gate = genuine_bool(rows.scheduled_reliable, "scheduled_reliable")
    if not np.isfinite(rows[list(PREDICTIONS)].to_numpy(float)).all():
        raise ValueError("nonfinite routing input")
    output = rows.sort_values(KEY).reset_index(drop=True).copy()
    gate = genuine_bool(output.scheduled_reliable, "scheduled_reliable")
    for parent in PARENTS:
        output[parent + "_policy"] = np.where(
            gate, output[parent + "_scheduled"], output[parent]
        )
    return output


def contrast(rows, left, right):
    paired = benchmark.paired_contrast(rows, left, right)
    loss = np.abs(rows[left] - rows.pir_per36_dest) - np.abs(
        rows[right] - rows.pir_per36_dest
    )
    n = len(rows)
    counts = {
        "improved": int((loss > 0).sum()),
        "worsened": int((loss < 0).sum()),
        "tied": int((loss == 0).sum()),
    }
    if sum(counts.values()) != n:
        raise ValueError("paired loss shares do not conserve population")
    return {
        **paired,
        "n": n,
        "mean": float(loss.mean()) if n else None,
        "counts": counts,
        "shares": {k: v / n if n else None for k, v in counts.items()},
    }


def policy_report(rows, parent, *, partitions=True, strata=True):
    augmented, policy = parent + "_scheduled", parent + "_policy"
    gate = genuine_bool(rows.scheduled_reliable, "scheduled_reliable")
    arms = {"parent": parent, "augmented": augmented, "policy": policy}
    comparisons = {"parent": parent, "augmented": augmented}
    if parent.startswith("cell_slope_"):
        source = parent.replace("cell_slope_", "source_ridge_", 1)
        arms["source_offset"] = source
        comparisons["source_offset"] = source
    n = len(rows)
    result = {
        "status": "ok" if n else "empty",
        "n": n,
        "parent": parent,
        "augmented": augmented,
        "policy": policy,
        "routing": {"augmented": int(gate.sum()), "parent": int((~gate).sum())},
        "metrics": {
            label: diagnostics.errors(rows, arm) if n else None
            for label, arm in arms.items()
        },
        "contrasts": {
            label: contrast(rows, arm, policy) for label, arm in comparisons.items()
        },
    }
    if strata:
        d = np.abs(rows[parent] - rows.pir_per36_dest) - np.abs(
            rows[augmented] - rows.pir_per36_dest
        )
        groups = {}
        for label, mask in (("reliable", gate), ("unreliable", ~gate)):
            subset = rows.loc[mask]
            groups[label] = {
                "status": "ok" if len(subset) else "empty",
                "n": len(subset),
                "full_cohort_weight": len(subset) / n if n else None,
                "augmented_vs_parent": contrast(subset, parent, augmented),
                "parent_policy_contribution": float(d.loc[mask].sum() / n)
                if n and label == "reliable"
                else 0.0
                if n
                else None,
                "augmented_policy_contribution": float(-d.loc[mask].sum() / n)
                if n and label == "unreliable"
                else 0.0
                if n
                else None,
            }
        result["strata"] = groups
        if n:
            for name in ("parent", "augmented"):
                total = sum(g[name + "_policy_contribution"] for g in groups.values())
                if not np.isclose(
                    total, result["contrasts"][name]["mean"], atol=1e-12, rtol=1e-12
                ):
                    raise ValueError("weighted loss contributions do not reconcile")
    if partitions:
        for label, column in (
            ("by_season", "season_dest"),
            ("by_destination", "league_dest"),
        ):
            result[label] = {
                str(key): policy_report(group, parent, partitions=False, strata=False)
                for key, group in rows.groupby(column, sort=True)
            }
    return result


def scenario_report(rows):
    return {
        "n": len(rows),
        "routing": {
            "augmented": int(rows.scheduled_reliable.sum()),
            "parent": int((~rows.scheduled_reliable).sum()),
        },
        "policies": {p: policy_report(rows, p) for p in PARENTS},
    }


def scenario_ranges(scenarios):
    output = {}
    for parent in PARENTS:
        output[parent] = {}
        for label in scenarios["reference"]["policies"][parent]["contrasts"]:
            output[parent][label] = {}
            for group, names in (
                (
                    "estimation_omission",
                    [s["name"] for s in SCENARIOS if s["omitted_season"] is not None],
                ),
                (
                    "seed",
                    [s["name"] for s in SCENARIOS if s["name"].startswith("seed_")],
                ),
            ):
                values = {
                    name: scenarios[name]["policies"][parent]["contrasts"][label][
                        "mean"
                    ]
                    for name in names
                }
                output[parent][label][group] = {
                    "n": len(values),
                    "values": values,
                    "min": min(values.values()) if values else None,
                    "max": max(values.values()) if values else None,
                    "all_positive": all(v > 0 for v in values.values())
                    if values
                    else None,
                    "interpretation": (
                        "descriptive sensitivity, not a confidence interval"
                    ),
                }
    return output


def _passes(contrast_report):
    return (
        contrast_report["mean"] is not None
        and contrast_report["mean"] > 0
        and all(
            contrast_report[name]["status"] == "ok"
            and contrast_report[name]["ci95"] is not None
            and contrast_report[name]["ci95"][0] > 0
            for name in ("player_club_season", "player_season")
        )
    )


def verdict(variants):
    primary = variants[VARIANTS[0]]["scenarios"]
    base_pairs = [
        (family + "_10", c) for family in FAMILIES for c in ("parent", "augmented")
    ]
    slope_pair = ("cell_slope_10", "source_offset")

    def significant(pairs):
        return {
            p + "/" + c: _passes(primary["reference"]["policies"][p]["contrasts"][c])
            for p, c in pairs
        }

    def robust(pairs):
        checks = {}
        for p, c in pairs:
            report = primary["reference"]["policies"][p]
            # Destination zero is not a sign reversal in the accepted protocol.
            checks[p + "/" + c] = {
                "no_destination_reversal": bool(report["by_destination"])
                and all(
                    g["contrasts"][c]["mean"] is not None
                    and g["contrasts"][c]["mean"] >= 0
                    for g in report["by_destination"].values()
                ),
                "evaluation_season_deletions_positive": bool(
                    report["contrasts"][c]["leave_one_season_out"]
                )
                and all(
                    value is not None and value > 0
                    for value in report["contrasts"][c]["leave_one_season_out"].values()
                ),
                "estimation_and_seed_scenarios_positive": all(
                    result["policies"][p]["contrasts"][c]["mean"] > 0
                    for name, result in primary.items()
                    if name != "reference"
                ),
            }
        return checks

    def general(pairs):
        return {
            v: all(
                variants[v]["scenarios"]["reference"]["policies"][p]["contrasts"][c][
                    "mean"
                ]
                > 0
                for p, c in pairs
            )
            for v in VARIANTS[1:]
        }

    primary_checks = significant(base_pairs)
    slope_checks = significant([slope_pair])
    robustness = robust(base_pairs)
    slope_robustness = robust([slope_pair])
    cross_pool = general(base_pairs)
    slope_cross_pool = general([slope_pair])
    action = all(primary_checks.values())
    slope = action and all(slope_checks.values())
    robust_action = action and all(all(c.values()) for c in robustness.values())
    robust_slope = (
        slope
        and robust_action
        and all(all(c.values()) for c in slope_robustness.values())
    )
    return {
        "primary_pool": VARIANTS[0],
        "primary_penalty": 10,
        "actionable_improvement": action,
        "slope_superiority": slope,
        "robust_actionable_improvement": robust_action,
        "robust_slope_superiority": robust_slope,
        "cross_pool_generality": action
        and bool(cross_pool)
        and all(cross_pool.values()),
        "slope_cross_pool_generality": slope
        and bool(cross_pool)
        and all(cross_pool.values())
        and all(slope_cross_pool.values()),
        "primary_checks": primary_checks,
        "slope_superiority_checks": slope_checks,
        "robustness_checks": robustness,
        "slope_robustness_checks": slope_robustness,
        "cross_pool_checks": cross_pool,
        "slope_cross_pool_checks": slope_cross_pool,
        "interpretation": (
            "exploratory policy improvement under the registered primary checks"
            if action
            else FAILURE
        ),
        "conditional_on_frozen_fits": True,
        "independent_confirmation": False,
    }


def reference_rows(variants):
    return [
        {
            "pool": v,
            "pool_label": chr(65 + i),
            "family": family,
            "penalty": p,
            **variants[v]["scenarios"]["reference"]["policies"][f"{family}_{p}"],
        }
        for i, v in enumerate(VARIANTS)
        for family in FAMILIES
        for p in PENALTIES
    ]


def _num(value):
    return "undefined" if value is None else f"{value:.6f}"


def _ci(item, kind):
    interval = item[kind]["ci95"]
    return (
        "undefined (" + item[kind]["status"] + ")"
        if interval is None
        else ("[" + ", ".join(_num(v) for v in interval) + "]")
    )


def render_results(summary):
    lines = [
        "# Frozen factor-reliability routing policy",
        "",
        summary["verdict"]["interpretation"] + ".",
        "",
        "Exploratory amendment on reused outcomes. No new fits or identity joins. "
        "The September 12 operating lock, v9 and the original v10 run remain"
        " unchanged.",
        "",
        "## Specification",
        "",
        "| Field | Declaration |",
        "| --- | --- |",
        "| Unit | Paired player/destination-season forecast loss |",
        f"| Population | {summary['target_n']} unchanged keys "
        "in every saved scenario |",
        "| Estimator | Frozen Boolean reliability routes to augmented or "
        "separately fitted parent |",
        "| Null | Routing does not improve both always-parent and "
        "always-augmented forecasts |",
        "| Filter | Complete frozen target; no row deletion or zero imputation |",
        "| Key | player_name + season_dest |",
        "| Uncertainty | Conditional player/club-season and player/season "
        "intervals; separate sensitivity ranges |",
        "| Threats | Exposed outcomes, six seasons, retrospective "
        "corrections, sparse support and unresolved release scope |",
        "",
        "Primary display: pool A, penalty 10, both families. All other fixed"
        " cells remain visible. "
        "Reliability is the full historical predicate, not a count-only gate. "
        "Historical corrections do not establish real-time data availability.",
        "",
        "## Reference metrics",
        "",
        "| Pool | Parent | n | Augmented / parent routes | Parent MAE | "
        "Augmented MAE | Policy MAE | Policy RMSE | Bias | Median AE | P90 "
        "AE |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in summary["reference_rows"]:
        m = row["metrics"]
        values = [
            m["parent"]["mae"],
            m["augmented"]["mae"],
            m["policy"]["mae"],
            m["policy"]["rmse"],
            m["policy"]["bias"],
            m["policy"]["median_absolute_error"],
            m["policy"]["p90_absolute_error"],
        ]
        lines.append(
            f"| {row['pool_label']} | {row['parent']} | {row['n']} | "
            f"{row['routing']['augmented']} / {row['routing']['parent']} | "
            + " | ".join(map(_num, values))
            + " |"
        )
    lines.extend(
        [
            "",
            "## Reference paired contrasts",
            "",
            "Positive favors the policy. Intervals are conditional, not simultaneous "
            "or calibrated future-accuracy guarantees. Undefined intervals "
            "are inconclusive.",
            "",
            "| Pool | Policy parent | Comparator | Gain | Player/club-season"
            " 95% | Player/season 95% | Improved / worsened / tied |",
            "| --- | --- | --- | ---: | --- | --- | --- |",
        ]
    )
    for row in summary["reference_rows"]:
        for label, c in row["contrasts"].items():
            shares = " / ".join(
                _num(c["shares"][s]) for s in ("improved", "worsened", "tied")
            )
            lines.append(
                f"| {row['pool_label']} | {row['parent']} | {label} | "
                f"{_num(c['mean'])} | "
                f"{_ci(c, 'player_club_season')} | "
                f"{_ci(c, 'player_season')} | {shares} |"
            )
    lines.extend(
        [
            "",
            "## Support strata and loss reconciliation",
            "",
            "Augmented gain below is parent loss minus augmented loss. "
            "Contributions are weighted by full-cohort size, not subgroup MAEs. "
            "Empty groups remain explicit in summary.json.",
            "",
            "| Pool | Parent | Stratum | n | Augmented gain | Parent-policy "
            "contribution | Augmented-policy contribution |",
            "| --- | --- | --- | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in summary["reference_rows"]:
        for label, group in row["strata"].items():
            lines.append(
                f"| {row['pool_label']} | {row['parent']} | {label} | {group['n']} | "
                f"{_num(group['augmented_vs_parent']['mean'])} | "
                f"{_num(group['parent_policy_contribution'])} | "
                f"{_num(group['augmented_policy_contribution'])} |"
            )
    lines.extend(
        [
            "",
            "## Sensitivity ranges",
            "",
            "Evaluation-season deletion only removes loss rows. Estimation "
            "omissions and "
            "seed scenarios are the separately saved upstream refits; these "
            "ranges are not intervals.",
            "",
            "| Pool | Parent | Comparator | Evaluation deletion range | "
            "Estimation omission range | Seed range |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
    )
    for row in summary["reference_rows"]:
        ranges = summary["variants"][row["pool"]]["scenario_ranges"][row["parent"]]
        for label, c in row["contrasts"].items():
            deletion = list(c["leave_one_season_out"].values())
            span = (
                _num(min(deletion)) + " to " + _num(max(deletion))
                if deletion and all(v is not None for v in deletion)
                else "undefined"
            )
            pieces = [
                _num(ranges[label][g]["min"]) + " to " + _num(ranges[label][g]["max"])
                for g in ("estimation_omission", "seed")
            ]
            lines.append(
                f"| {row['pool_label']} | {row['parent']} | {label} | {span} | "
                + " | ".join(pieces)
                + " |"
            )
    lines.extend(
        [
            "",
            "## Registered claims",
            "",
            "| Claim | Passed |",
            "| --- | --- |",
            *[
                f"| {name} | {str(summary['verdict'][name]).lower()} |"
                for name in (
                    "actionable_improvement",
                    "slope_superiority",
                    "robust_actionable_improvement",
                    "robust_slope_superiority",
                    "cross_pool_generality",
                    "slope_cross_pool_generality",
                )
            ],
            "",
            "Every scenario, evaluation season and destination, including all metrics, "
            "interval statuses, shares, strata and evaluation-season "
            "deletions, is retained "
            "under variants in [summary.json](summary.json). Keyed routed "
            "forecasts remain "
            "under each pool/scenario. No outcome or unsupported identity was added.",
            "",
            "## Provenance",
            "",
            f"- Protocol SHA-256: {summary['protocol_sha256']}",
            f"- Frozen v10 summary SHA-256: {summary['v10_summary_sha256']}",
            f"- Manifest SHA-256: {summary['manifest_sha256']}",
            "- Input, output and imported scientific-code hashes are "
            "recorded in summary.json and manifest.json.",
            "- Internal replay is not source validation or independent "
            "statistical review. "
            "External messages, public release and submission require "
            "separate authorization.",
            "",
        ]
    )
    return "\n".join(lines)


def check_outputs(out, *, context=None, originals=None):
    """Hash-check and recompute reports from saved routed rows, without any fit."""
    out = Path(out)
    state, summary = read_json(out / "status.json"), read_json(out / "summary.json")
    if state.get("status") != "complete" or summary.get("status") != "complete":
        raise ValueError("policy package is incomplete")
    refit._check(out / "summary.json", state["summary_sha256"])
    refit._check(out / "manifest.json", summary["manifest_sha256"])
    manifest = read_json(out / "manifest.json")
    for name in (
        "protocol_sha256",
        "code_hashes",
        "input_hashes",
        "v10_summary_sha256",
    ):
        if summary[name] != manifest[name]:
            raise ValueError("policy manifest binding mismatch")
    if set(manifest["code_hashes"]) != set(CODE_FILES):
        raise ValueError("policy code inventory changed")
    if (
        manifest["penalties"] != list(PENALTIES)
        or manifest["families"] != list(FAMILIES)
        or manifest["gate"] != "frozen scheduled_reliable"
    ):
        raise ValueError("policy definition changed")
    for name, digest in manifest["code_hashes"].items():
        refit._check(benchmark._safe_child(ROOT, name), digest)
    refit._check(PROTOCOL, manifest["protocol_sha256"])
    if context is None:
        context = verify_inputs(manifest["analysis"], manifest["v9_run"])
    if originals is None:
        originals = load_validated(context)
    if context["input_hashes"] != manifest["input_hashes"]:
        raise ValueError("policy inputs changed")
    if (
        manifest["variants"] != list(VARIANTS)
        or manifest["scenarios"] != SCENARIOS
        or len(manifest["target_keys"]) != len(context["target"])
        or set(map(tuple, manifest["target_keys"])) != context["target"]
        or summary["target_n"] != len(context["target"])
        or summary["scenario_count"] != len(VARIANTS) * len(SCENARIOS)
        or set(summary["variants"]) != set(VARIANTS)
    ):
        raise ValueError("policy target/scenario inventory changed")
    expected = {
        f"{v}/{s['name']}/predictions.parquet" for v in VARIANTS for s in SCENARIOS
    } | {"results.md"}
    _inventory(out, expected, summary["output_hashes"])
    regenerated = {}
    for variant in VARIANTS:
        reports = {}
        for scenario in SCENARIOS:
            name = scenario["name"]
            rows = pd.read_parquet(out / variant / name / "predictions.parquet")
            validate_rows(rows, context["target"])
            expected_rows = route(originals[variant, name])
            _equal_frames(
                rows,
                expected_rows,
                list(expected_rows.columns),
                "saved routed forecasts",
            )
            if list(rows.columns) != list(expected_rows.columns):
                raise ValueError("routed forecast schema changed")
            reports[name] = scenario_report(rows)
        regenerated[variant] = {
            "scenarios": reports,
            "scenario_ranges": scenario_ranges(reports),
        }
    benchmark._equivalent(regenerated, summary["variants"])
    benchmark._equivalent(verdict(regenerated), summary["verdict"])
    benchmark._equivalent(reference_rows(regenerated), summary["reference_rows"])
    if render_results(summary) != (out / "results.md").read_text():
        raise ValueError("generated policy report changed")
    return {
        "status": "verified",
        "target_n": summary["target_n"],
        "scenarios": summary["scenario_count"],
    }


def run(analysis, v9_run, out):
    analysis, v9_run, out = map(lambda p: Path(p).resolve(), (analysis, v9_run, out))
    frozen._separate_output(
        out, (analysis, v9_run, frozen.DIAGNOSTICS.parent.resolve())
    )
    context = verify_inputs(analysis, v9_run)
    frozen._separate_output(out, (context["inputs"].resolve(),))
    code_hashes = {name: sha256_file(ROOT / name) for name in CODE_FILES}
    protocol_hash = sha256_file(PROTOCOL)
    # No policy calculation, metric or output mutation until every support check passes.
    records = load_validated(context)
    manifest = {
        "schema_version": 1,
        "analysis": str(analysis),
        "v9_run": str(v9_run),
        "model_inputs": str(context["inputs"]),
        "protocol_sha256": protocol_hash,
        "code_hashes": code_hashes,
        "input_hashes": context["input_hashes"],
        "v10_summary_sha256": FROZEN_SUMMARY_SHA256,
        "variants": list(VARIANTS),
        "scenarios": SCENARIOS,
        "target_keys": sorted(context["target"]),
        "penalties": list(PENALTIES),
        "families": list(FAMILIES),
        "gate": "frozen scheduled_reliable",
        "environment": {
            "python": sys.version,
            "numpy": np.__version__,
            "pandas": pd.__version__,
            "scipy": benchmark.scipy.__version__,
        },
        "exposure": "Already exposed historical outcomes; exploratory amendment",
    }
    out.mkdir(parents=True, exist_ok=True)
    dump(out / "manifest.json", manifest)
    dump(out / "status.json", {"status": "running"})
    try:
        variants, outputs = {}, {}
        for variant in VARIANTS:
            reports = {}
            for scenario in SCENARIOS:
                name = scenario["name"]
                routed = route(records[variant, name])
                path = out / variant / name / "predictions.parquet"
                path.parent.mkdir(parents=True, exist_ok=True)
                routed.to_parquet(path, index=False)
                outputs[str(path.relative_to(out))] = sha256_file(path)
                reports[name] = scenario_report(routed)
            variants[variant] = {
                "scenarios": reports,
                "scenario_ranges": scenario_ranges(reports),
            }
        # Catch mutation during the calculation without running old or new fits.
        current = verify_inputs(analysis, v9_run)
        if current["input_hashes"] != context["input_hashes"]:
            raise ValueError("frozen inputs changed during policy calculation")
        for name, digest in code_hashes.items():
            refit._check(ROOT / name, digest)
        refit._check(PROTOCOL, protocol_hash)
        summary = {
            "schema_version": 1,
            "status": "complete",
            "manifest_sha256": sha256_file(out / "manifest.json"),
            "protocol_sha256": protocol_hash,
            "code_hashes": code_hashes,
            "input_hashes": context["input_hashes"],
            "v10_summary_sha256": FROZEN_SUMMARY_SHA256,
            "target_n": len(context["target"]),
            "scenario_count": len(records),
            "variants": variants,
            "verdict": verdict(variants),
            "reference_rows": reference_rows(variants),
            "output_hashes": outputs,
        }
        (out / "results.md").write_text(render_results(summary))
        outputs["results.md"] = sha256_file(out / "results.md")
        dump(out / "summary.json", summary)
        dump(
            out / "status.json",
            {
                "status": "complete",
                "summary_sha256": sha256_file(out / "summary.json"),
            },
        )
        check_outputs(out, context=context, originals=records)
        return summary
    except Exception as exc:
        dump(
            out / "status.json",
            {"status": "failed", "error": f"{type(exc).__name__}: {exc}"},
        )
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--analysis", required=True, type=Path)
    parser.add_argument("--v9-run", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    summary = run(args.analysis, args.v9_run, args.out)
    print(
        json.dumps(
            {
                "status": summary["status"],
                "target_n": summary["target_n"],
                "verdict": summary["verdict"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
