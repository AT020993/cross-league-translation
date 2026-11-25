#!/usr/bin/env python3
"""E1 and E2 of the SSAC27 full paper: head-to-head and six translation recipes.

Pre-registration: docs/research/sloan-full-paper-preregistration-2026-11-03.md
(commit f52e7c831, pushed 2026-11-03T09:15:02Z), sections E1 and E2. All
results are exploratory: destination seasons 2020-2025 were already seen.

E1. C_H = MAE(history + translation) - MAE(source offsets lambda 10), on the
674 v10 targets, both interval specifications; the recovered share
S = [MAE(history) - MAE(offsets)] / [MAE(history) - MAE(history + translation)]
with a 2,000-draw cluster bootstrap over destination club-seasons (seed 0).
Penalties 1 and 100 are printed beside the primary 10.

E2. Six recipes R1-R6 change only the factor estimator or the pooling; each is
a ``fitter`` returning the v10 factor-table schema, so the lag, cutoffs,
lookup and regressions are the v10 code. Primary: the offsets-lambda-10
increment per recipe on the 674 (pool A), Holm across the six. Printed: the
full ladder, both interval specifications, absolute MAEs, support/fallback
counts, the 2%-of-parent-MAE margin statement, and pools B-D.

Threats: drift from the submitted numbers (R1 must reproduce G0 to 1e-9, with
an impossible-tolerance negative control); changing support across recipes
(the same 674 targets in every arm; an unscorable target is a failure, never a
drop); forking paths (every recipe, penalty, pool and interval printed;
lambda 10 fixed primary; Holm for the family claim); a null read as absence
(80%-power detectable effect beside every increment).
"""

# ruff: noqa: E501 -- pre-registered wording and table headers
from __future__ import annotations

if __name__ == "__main__":
    import sys as _sys
    from pathlib import Path as _Path

    _sys.path.insert(0, str(_Path(__file__).resolve().parents[1]))
    from src.research.execution import enter as _enter

    _enter(__file__)

import argparse
import functools
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
from scipy import stats  # noqa: E402

from scripts import build_league_factors as blf  # noqa: E402
from scripts import league_factor_pooling as lfp  # noqa: E402
from scripts import sloan_fullpaper_common as common  # noqa: E402
from scripts import translation_research_common as trc  # noqa: E402

MIN_PAIRS = 75  # the v10 reliability floor (fit_table)
MARGIN_SHARE = 0.02  # 2% of the parent model's MAE
ALPHA = 0.05
N_BOOT = 2000
SEED = 0
SPECS = ("player_club_season", "player_season")
PRIMARY_SPEC = "player_club_season"


# ---------------------------------------------------------------------------
# Recipes: each returns trc.TABLE_COLUMNS, the schema design.lookup reads.


def fit_unpooled(pairs: pd.DataFrame, *, n_boot: int = 2000, seed: int = 0):
    """R4: exposure-weighted raw cell factors, no pooling.

    A cell above the 75-pair floor with a finite bootstrap SE keeps its raw
    factor; every other row falls back to the destination mean, which stays the
    v10 one (precision-weighted mean of the raw cell factors).
    """
    table = trc.fit_table(pairs, n_boot=n_boot, seed=seed)
    if table.empty:
        return table
    table = table.copy()
    for _, idx in table.groupby("destination", sort=False).groups.items():
        block = table.loc[idx]
        factors, ses = block.factor_raw.to_numpy(float), block.se.to_numpy(float)
        ok = np.isfinite(factors) & np.isfinite(ses) & (ses > 0)
        grand = (
            float(np.sum(factors[ok] / ses[ok] ** 2) / np.sum(1 / ses[ok] ** 2))
            if ok.sum() >= 2
            else np.nan
        )
        table.loc[idx, "factor"] = factors
        table.loc[idx, "tier_mean"] = grand
        table.loc[idx, "tau"] = np.nan
        table.loc[idx, "pooled_collapsed"] = False
        table.loc[idx, "reliable"] = (
            block.n_pairs.to_numpy() >= MIN_PAIRS
        ) & np.isfinite(ses)
    for column in ("pooled_collapsed", "reliable"):
        table[column] = table[column].astype(bool)
    return table[trc.TABLE_COLUMNS]


def fit_floor_clearing(pairs: pd.DataFrame, *, n_boot: int = 2000, seed: int = 0):
    """R5: exposure-weighted cells, tau^2 from floor-clearing cells (2026-09-29 pooler)."""
    table = trc.fit_table(pairs, n_boot=n_boot, seed=seed)
    if table.empty:
        return table
    pooled = lfp.repool_table(table, pooler="floor_clearing", min_pairs=MIN_PAIRS)
    return pooled[trc.TABLE_COLUMNS]


def fit_destination_only(pairs: pd.DataFrame, *, n_boot: int = 2000, seed: int = 0):
    """R6: one exposure-weighted factor per destination, no league-pair cells.

    Every source league seen in the window is written with the destination's
    factor (and an unseen one falls back to the same value through tier_mean),
    so the v10 lookup returns one number per destination.
    """
    pairs = pairs[pairs.season.between(2015, 2026)]
    rows = []
    for destination in blf.CONTINENTAL:
        sub = pairs[pairs.league_dest == destination]
        if sub.empty:
            continue
        draws = trc.bootstrap_draws(
            sub,
            estimator="exposure_weighted",
            n_boot=n_boot,
            seed=blf.cell_seed(seed, "all_pairs", "all", destination, "pir", "*"),
        )
        finite = draws[np.isfinite(draws)]
        se = lo = hi = np.nan
        if len(finite) >= max(2, n_boot // 2):
            se = float(finite.std(ddof=1))
            lo, hi = np.percentile(finite, [2.5, 97.5])
        factor = blf.ESTIMATORS["exposure_weighted"](sub, "pir")
        for source, cell in sub.groupby("league_src"):
            rows.append(
                dict(
                    league=source,
                    destination=destination,
                    factor_raw=factor,
                    factor=factor,
                    se=se,
                    ci_lo=lo,
                    ci_hi=hi,
                    n_pairs=len(cell),
                    n_clusters=cell.cluster.nunique(),
                    tier_mean=factor,
                    tau=np.nan,
                    reliable=bool(np.isfinite(factor)),
                    pooled_collapsed=False,
                    n_boot_valid=len(finite),
                    n_boot_invalid=n_boot - len(finite),
                    era="all",
                    stat="pir",
                    sample="all_pairs",
                )
            )
    return pd.DataFrame(rows, columns=trc.TABLE_COLUMNS)


RECIPES = {
    "R1": ("exposure-weighted mean of ratios, moment pooler (v10)", trc.fit_table),
    "R2": (
        "ratio of sums (NHLe/MLE-style), moment pooler",
        functools.partial(trc.fit_table, estimator="ratio_of_sums"),
    ),
    "R3": (
        "unweighted mean of ratios, moment pooler",
        functools.partial(trc.fit_table, estimator="mean_of_ratios"),
    ),
    "R4": ("exposure-weighted, no pooling (raw cell above 75 pairs)", fit_unpooled),
    "R5": (
        "exposure-weighted, floor-clearing tau^2 pooler (2026-09-29)",
        fit_floor_clearing,
    ),
    "R6": ("one exposure-weighted factor per destination", fit_destination_only),
}

#: (parent without translation, parent + translation), the v10 ladder.
LADDER = (
    ("history_only", "scheduled_history"),
    ("history_destination_slope", "history_destination_slope_scheduled"),
    *[(f"source_ridge_{p}", f"source_ridge_{p}_scheduled") for p in common.PENALTIES],
    *[(f"cell_slope_{p}", f"cell_slope_{p}_scheduled") for p in common.PENALTIES],
)
PRIMARY_INCREMENT = ("source_ridge_10", "source_ridge_10_scheduled")


# ---------------------------------------------------------------------------
# Statistics.


def arm_metrics(rows: pd.DataFrame, arm: str) -> dict:
    error = np.abs(rows[arm] - rows.pir_per36_dest).to_numpy(float)
    signed = (rows[arm] - rows.pir_per36_dest).to_numpy(float)
    return {
        "mae": float(error.mean()),
        "rmse": float(np.sqrt(np.mean(signed**2))),
        "median_abs_error": float(np.median(error)),
        "p90_abs_error": float(np.percentile(error, 90)),
    }


def interval_stats(block: dict, parent_mae: float) -> dict:
    """p-value, SE and 80%-power detectable effect for one interval spec."""
    se = float(np.sqrt(block["variance"]))
    df = int(block["degrees_of_freedom"])
    difference = float(block["difference"])
    statistic = difference / se if se > 0 else np.nan
    return {
        "n": int(block["n"]),
        "difference": difference,
        "ci95": [float(v) for v in block["ci95"]],
        "se": se,
        "df": df,
        "p_two_sided": float(2 * stats.t.sf(abs(statistic), df)),
        "detectable_80": float((stats.t.ppf(0.975, df) + stats.t.ppf(0.80, df)) * se),
        "pct_of_parent": 100 * difference / parent_mae,
        "upper_pct_of_parent": 100 * float(block["ci95"][1]) / parent_mae,
        "lower_pct_of_parent": 100 * float(block["ci95"][0]) / parent_mae,
    }


def contrast_summary(rows: pd.DataFrame, left: str, right: str) -> dict:
    """Paired MAE(left) - MAE(right), positive favours right, both specs."""
    raw = common.contrast(rows, left, right)
    parent = common.mae(rows, left)
    out = {"left": left, "right": right, "parent_mae": parent}
    for spec in SPECS:
        out[spec] = interval_stats(raw[spec], parent)
    out["equal_season_difference"] = raw["equal_season_difference"]
    out["leave_one_season_out"] = raw["leave_one_season_out"]
    out["seasons_favouring_right"] = int(
        sum(
            float(
                (
                    np.abs(g[left] - g.pir_per36_dest)
                    - np.abs(g[right] - g.pir_per36_dest)
                ).mean()
            )
            > 0
            for _, g in rows.groupby("season_dest")
        )
    )
    return out


def holm(pvalues: dict) -> dict:
    """Holm step-down adjusted p-values."""
    order = sorted(pvalues, key=pvalues.get)
    m, running, adjusted = len(order), 0.0, {}
    for rank, name in enumerate(order):
        running = max(running, min(1.0, (m - rank) * pvalues[name]))
        adjusted[name] = running
    return adjusted


def recovered_share(rows, offsets, *, n_boot=N_BOOT, seed=SEED) -> dict:
    """S = [MAE(h) - MAE(offsets)] / [MAE(h) - MAE(h + z)], club-season bootstrap."""
    arms = ("history_only", "scheduled_history", offsets)
    codes, clusters = pd.factorize(rows.cluster, sort=False)
    sums = np.column_stack(
        [
            np.bincount(
                codes,
                weights=np.abs(rows[a] - rows.pir_per36_dest),
                minlength=len(clusters),
            )
            for a in arms
        ]
    )
    counts = np.bincount(codes, minlength=len(clusters)).astype(float)

    def share(total, n):
        mae = total / n
        return (mae[..., 0] - mae[..., 2]) / (mae[..., 0] - mae[..., 1])

    point = float(share(sums.sum(axis=0), counts.sum()))
    rng = np.random.default_rng(seed)
    picked = rng.integers(0, len(clusters), (n_boot, len(clusters)))
    totals = sums[picked].sum(axis=1)
    n = counts[picked].sum(axis=1)[:, None]
    with np.errstate(divide="ignore", invalid="ignore"):
        draws = share(totals, n)
    denominators = totals[:, 0] / n[:, 0] - totals[:, 1] / n[:, 0]
    finite = draws[np.isfinite(draws)]
    lo, hi = np.percentile(finite, [2.5, 97.5])
    return {
        "offsets_arm": offsets,
        "point": point,
        "ci95_percentile": [float(lo), float(hi)],
        "share_of_draws_at_least_1": float(np.mean(finite >= 1)),
        "draws": n_boot,
        "finite_draws": int(len(finite)),
        "nonpositive_denominator_draws": int((denominators <= 0).sum()),
        "clusters": int(len(clusters)),
        "seed": seed,
    }


# ---------------------------------------------------------------------------
# Running one recipe through the v10 path.


def support_counts(rows: pd.DataFrame, diagnostics: dict) -> dict:
    """Cell support on the 674 targets and in each season's factor table."""
    per_season = {}
    for season, info in sorted(diagnostics.items()):
        if int(season) in common.ANCHOR_SEASONS:
            table = info["scheduled"]
            per_season[str(int(season))] = {
                "pairs": int(table["n_pairs"]),
                "reliable_cells": int(table["reliable_cells"]),
                "cells": len(table["cells"]),
            }
    return {
        "targets": len(rows),
        "targets_cell_factor": int(rows.scheduled_reliable.astype(bool).sum()),
        "targets_destination_fallback": int(rows.scheduled_fallback.astype(bool).sum()),
        "per_season_tables": per_season,
    }


def run_recipe(pairs, cohort, keys, fitter):
    features, diagnostics = common.build_features(pairs, cohort, fitter=fitter)
    rows, _ = common.forecast(features)
    try:
        targets = common.on_targets(rows, keys)
    except common.GateFailure as error:
        return None, {"status": "inconclusive", "reason": str(error)}
    result = {
        "status": "scored",
        "metrics": {arm: arm_metrics(targets, arm) for arm in common.ALL_ARMS},
        "ladder": {f"{a}->{b}": contrast_summary(targets, a, b) for a, b in LADDER},
        "head_to_head": {
            f"lambda_{p}": contrast_summary(
                targets, "scheduled_history", f"source_ridge_{p}"
            )
            for p in common.PENALTIES
        },
        "support": support_counts(targets, diagnostics),
    }
    return targets, result


def g0_for_r1(rows, root) -> dict:
    v9, v10_summary = common.load_references(root)
    diffs = common.g0_differences(rows, v9, v10_summary)
    try:
        common.assert_g0(diffs, tolerance=-1.0)
    except common.GateFailure:
        control = "rejected as required"
    else:
        raise common.GateFailure("G0 negative control passed an impossible tolerance")
    common.assert_g0(diffs)
    return {
        "status": "passed",
        "max_difference": max(diffs.values()),
        "negative_control": control,
    }


def family_verdict(recipes: dict, spec: str = PRIMARY_SPEC) -> dict:
    name = "->".join(PRIMARY_INCREMENT)
    increments = {r: v["ladder"][name][spec] for r, v in recipes.items()}
    adjusted = holm({r: v["p_two_sided"] for r, v in increments.items()})
    above = [
        r for r, v in increments.items() if adjusted[r] < ALPHA and v["difference"] > 0
    ]
    below_margin = {
        r: v["upper_pct_of_parent"] < 100 * MARGIN_SHARE for r, v in increments.items()
    }
    licensed = not above and all(below_margin.values())
    return {
        "spec": spec,
        "holm_adjusted_p": adjusted,
        "recipes_with_adjusted_increment_above_zero": above,
        "upper_bound_below_2pct_of_parent": below_margin,
        "licensed": licensed,
        "sentence": (
            "None of six standard recipes adds more than 2% accuracy once the forecast knows both leagues."
            if licensed
            else "The pre-registered sentence is not licensed: "
            + (
                f"recipes {above} have a Holm-adjusted increment above zero"
                if above
                else ""
            )
            + ("; " if above and not all(below_margin.values()) else "")
            + (
                f"recipes {[r for r, ok in below_margin.items() if not ok]} have an upper bound at or above 2% of the parent MAE"
                if not all(below_margin.values())
                else ""
            )
        ),
        "margin_note": "R1 margin statement is descriptive (the 2% margin was chosen after the R1 intervals were seen); R2-R6 are pre-specified.",
    }


def e1_verdict(head: dict, share: dict, spec: str = PRIMARY_SPEC) -> dict:
    block = head["lambda_10"][spec]
    lo, hi = block["ci95"]
    if lo > 0:
        sentence = (
            "The league-aware model is more accurate than history plus translation."
        )
    elif hi >= 0 and block["difference"] >= 0:
        sentence = (
            "A league-aware model matches translation's gain without the translation step "
            f"(recovered share {share['point']:.2f}, 95% bootstrap interval "
            f"{share['ci95_percentile'][0]:.2f} to {share['ci95_percentile'][1]:.2f})."
        )
    else:
        sentence = "The paper's positive headline is not supported and is withdrawn."
    return {"spec": spec, "sentence": sentence}


def flat_ladder(results: dict) -> pd.DataFrame:
    records = []
    for pool, recipes in results.items():
        for recipe, value in recipes.items():
            if value["status"] != "scored":
                records.append(
                    {"pool": pool, "recipe": recipe, "status": value["status"]}
                )
                continue
            for group in ("ladder", "head_to_head"):
                for name, c in value[group].items():
                    for spec in SPECS:
                        s = c[spec]
                        records.append(
                            {
                                "pool": pool,
                                "recipe": recipe,
                                "status": "scored",
                                "group": group,
                                "contrast": name,
                                "left": c["left"],
                                "right": c["right"],
                                "spec": spec,
                                "n": s["n"],
                                "mae_left": value["metrics"][c["left"]]["mae"],
                                "mae_right": value["metrics"][c["right"]]["mae"],
                                "difference": s["difference"],
                                "ci_low": s["ci95"][0],
                                "ci_high": s["ci95"][1],
                                "p_two_sided": s["p_two_sided"],
                                "detectable_80": s["detectable_80"],
                                "pct_of_parent": s["pct_of_parent"],
                                "upper_pct_of_parent": s["upper_pct_of_parent"],
                            }
                        )
    return pd.DataFrame(records)


def flat_metrics(results: dict) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"pool": pool, "recipe": recipe, "arm": arm, **m}
            for pool, recipes in results.items()
            for recipe, value in recipes.items()
            if value["status"] == "scored"
            for arm, m in value["metrics"].items()
        ]
    )


def run(root: Path, input_dir: Path, out: Path) -> dict:
    root = Path(root)
    _, v10_summary = common.load_references(root)
    keys = common.target_keys(v10_summary)
    results, rows_a = {}, []
    gates = {}
    for code, pool in common.POOLS.items():
        pairs, cohort = common.load_pool(input_dir, pool)
        results[code] = {}
        for recipe, (_, fitter) in RECIPES.items():
            targets, value = run_recipe(pairs, cohort, keys, fitter)
            if code == "A" and recipe == "R1":
                if targets is None:
                    raise common.GateFailure("R1 pool A is unscorable")
                gates["G0_R1"] = g0_for_r1(targets, root)
            if code == "A":
                if targets is None:
                    raise common.GateFailure(
                        f"{recipe} pool A is unscorable: {value['reason']}"
                    )
                rows_a.append(targets.assign(recipe=recipe))
            results[code][recipe] = value
            print(f"[recipes] pool {code} {recipe}: {value['status']}", flush=True)
    r1 = next(r for r in rows_a if r.recipe.iloc[0] == "R1")
    shares = {
        f"lambda_{p}": recovered_share(r1, f"source_ridge_{p}")
        for p in common.PENALTIES
    }
    e1 = {
        "head_to_head": results["A"]["R1"]["head_to_head"],
        "recovered_share": shares,
        "verdict": e1_verdict(results["A"]["R1"]["head_to_head"], shares["lambda_10"]),
        "mae": {
            arm: results["A"]["R1"]["metrics"][arm]["mae"]
            for arm in (
                "history_only",
                "scheduled_history",
                *[f"source_ridge_{p}" for p in common.PENALTIES],
            )
        },
    }
    family = {spec: family_verdict(results["A"], spec) for spec in SPECS}
    out = Path(out)
    out.mkdir(parents=True, exist_ok=False)
    summary = {
        "analysis": "E1 and E2 (exploratory; destination seasons 2020-2025 already seen)",
        "protocol_commit": common.PROTOCOL_COMMIT,
        "protocol_sha256": trc.sha256_file(root / common.PROTOCOL),
        "n_targets": len(keys),
        "pools": dict(common.POOLS),
        "recipes": {k: v[0] for k, v in RECIPES.items()},
        "primary_increment": list(PRIMARY_INCREMENT),
        "primary_spec": PRIMARY_SPEC,
        "margin_share_of_parent": MARGIN_SHARE,
        "gates": gates,
        "e1": e1,
        "e2_family": family,
        "results": results,
    }
    (out / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n"
    )
    flat_ladder(results).to_csv(out / "ladder.csv", index=False)
    flat_metrics(results).to_csv(out / "metrics.csv", index=False)
    keep = [
        *common.KEY,
        "recipe",
        "league_dest",
        "league_src",
        "cluster",
        "pir_per36_dest",
        "scheduled_translated",
        "scheduled_fallback",
        *common.ALL_ARMS,
    ]
    pd.concat(rows_a, ignore_index=True)[keep].to_parquet(
        out / "rows_pool_A.parquet", index=False
    )
    print(f"E1 {e1['verdict']['sentence']}")
    print(f"E2 {family[PRIMARY_SPEC]['sentence']}")
    return summary


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    run(Path.cwd(), args.input_dir, args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
