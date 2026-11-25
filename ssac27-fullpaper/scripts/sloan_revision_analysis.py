"""Registered Sloan extension; historical estimators/evidence stay immutable.

Threats: outcome selection (three populations/upstream ledger), chronology
(shared prior training), source drift (inventory refusal), crossed errors
(conditional multiway inference), silent loss (keyed reproduction).
"""

from __future__ import annotations

import argparse
import contextlib
import io
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
from scipy.stats import t  # noqa: E402
from threadpoolctl import threadpool_limits  # noqa: E402
from scripts import build_league_factors as blf  # noqa: E402
from scripts import compare_translation_designs as design  # noqa: E402
from scripts import revalidate_sloan_sources as previous  # noqa: E402
from scripts import sloan_source_adjudication as source  # noqa: E402
from scripts import validate_translation_holdout as holdout  # noqa: E402
from scripts.validate_translation_walkforward import _rtm_design  # noqa: E402
from scripts.translation_research_common import sha256_file  # noqa: E402

KEY = ["player_name", "season_dest"]
ARMS = (*design.ARMS, "history_only")
MODES = ("original", "evaluation_only", "expanded_training")
PROTOCOL = ROOT / "docs/research/sloan-revision-preregistration-2026-09-08.md"


def unique(frame, keys=KEY):
    if frame[keys].isna().any().any() or frame.duplicated(keys).any():
        raise ValueError(f"missing or duplicate keys: {keys}")


def key_list(frame):
    return frame.sort_values(KEY)[KEY].to_dict("records")


def reconstruct_cohort(agg):
    """Rebuild pre-outcome candidates and every observed continental season.

    Threshold stints BEFORE largest qualifying stint selection, preserving the
    inherited qualified-continental incumbency rule and historical tie handling.
    """
    unique(agg, ["player_name", "season", "league"])
    q = agg[(agg.games >= holdout.MIN_GAMES) & (agg.minutes > 0)]
    dest_all = agg[agg.league.isin(blf.CONTINENTAL)]
    source_all = agg[~agg.league.isin(blf.NOT_A_SOURCE)]
    dest = (
        q[q.league.isin(blf.CONTINENTAL)]
        .sort_values("minutes", ascending=False)
        .drop_duplicates(["player_name", "season"])
    )
    src = (
        q[~q.league.isin(blf.NOT_A_SOURCE)]
        .sort_values("minutes", ascending=False)
        .drop_duplicates(["player_name", "season"])
    )
    remaining = dest_all.merge(
        dest[["player_name", "season"]].assign(_qualified=True),
        on=["player_name", "season"],
        how="left",
        validate="m:1",
    )
    remaining = remaining[remaining._qualified.isna()].drop(columns="_qualified")
    remaining = remaining.sort_values("minutes", ascending=False).drop_duplicates(
        ["player_name", "season"]
    )
    observed = pd.concat([dest, remaining], ignore_index=True)
    s = src.assign(season_join=src.season + 1)
    ledger = observed.merge(
        s,
        left_on=["player_name", "season"],
        right_on=["player_name", "season_join"],
        suffixes=("_dest", "_src"),
        how="left",
        validate="1:1",
    )
    prev_cont = dest[["player_name", "season"]].assign(
        season_dest=lambda x: x.season + 1, was_cont=1
    )
    ledger = ledger.merge(
        prev_cont[[*KEY, "was_cont"]], on=KEY, how="left", validate="1:1"
    )
    ledger["was_cont"] = ledger.was_cont.fillna(0).astype(int)
    hist = (
        agg[agg.minutes > 0]
        .groupby(["player_name", "season"])[["pir", "minutes"]]
        .sum()
        .sort_index()
        .reset_index()
    )
    hist[["cum_pir", "cum_min"]] = hist.groupby("player_name")[
        ["pir", "minutes"]
    ].cumsum()
    hist["prior_mean_pir36"] = np.where(
        hist.cum_min > hist.minutes,
        36 * (hist.cum_pir - hist.pir) / (hist.cum_min - hist.minutes),
        np.nan,
    )
    ledger = ledger.merge(
        hist[["player_name", "season", "prior_mean_pir36"]].rename(
            columns={"season": "season_src"}
        ),
        on=["player_name", "season_src"],
        how="left",
        validate="m:1",
    )
    ledger["above_own_prior"] = ledger.pir_per36_src > ledger.prior_mean_pir36
    ledger["name_multi_league"] = (
        ledger.player_name.map(agg.groupby("player_name").league.nunique())
        .fillna(0)
        .astype(int)
    )
    ledger["name_multiclub_season"] = ledger.player_name.isin(
        agg.loc[agg.n_clubs > 1, "player_name"]
    )
    ledger["cluster"] = (
        ledger.season_dest.astype(str)
        + "|"
        + ledger.league_dest
        + "|"
        + ledger.club_dest
    )
    available = set(zip(source_all.player_name, source_all.season + 1))
    ledger["source_available"] = [tuple(k) in available for k in ledger[KEY].to_numpy()]
    ledger["destination_qualified"] = (
        (ledger.games_dest >= holdout.MIN_GAMES)
        & np.isfinite(ledger.minutes_dest)
        & (ledger.minutes_dest > 0)
    )
    ledger["source_qualified"] = ledger.season_src.notna()
    ledger["qualified_incumbent"] = ledger.was_cont.ne(0)
    ledger["registered_source_exclusion"] = ledger.league_src.isin(
        holdout.EXCLUDED_SOURCE
    )
    ledger["source_positive_finite"] = np.isfinite(ledger.pir_per36_src) & (
        ledger.pir_per36_src > 0
    )
    ledger["destination_finite"] = np.isfinite(ledger.pir_per36_dest)
    ledger["destination_positive"] = ledger.pir_per36_dest > 0
    ledger["first_exclusion"] = ""
    for flag, positive, reason in (
        ("destination_qualified", True, "destination_exposure"),
        ("source_available", True, "no_consecutive_domestic_source"),
        ("source_qualified", True, "source_exposure"),
        ("qualified_incumbent", False, "continental_incumbent"),
        ("registered_source_exclusion", False, "registered_source_exclusion"),
        ("source_positive_finite", True, "source_nonpositive_or_nonfinite"),
        ("destination_finite", True, "destination_nonfinite"),
    ):
        bad = ~ledger[flag] if positive else ledger[flag]
        ledger.loc[bad & ledger.first_exclusion.eq(""), "first_exclusion"] = reason
    ledger["expanded_eligible"] = ledger.first_exclusion.eq("")
    ledger["original_eligible"] = ledger.expanded_eligible & ledger.destination_positive
    ledger.loc[
        ledger.expanded_eligible & ~ledger.destination_positive, "first_exclusion"
    ] = "destination_nonpositive"
    unique(ledger)
    legacy = ledger[
        ledger.destination_qualified
        & ledger.source_qualified
        & (ledger.pir_per36_src > 0)
        & ledger.destination_positive
    ].copy()
    return ledger, legacy


def evaluation_features(study, rows):
    """Score extra rows; they never enter study factor, lag, or OLS fits."""
    result = rows.copy()
    for season, group in rows.groupby("season_dest", sort=True):
        earlier = study.cohorts[study.cohorts.season_dest < season]
        for arm, table in study.at(int(season)).items():
            mult, fallback, reliable = design.lookup(table, group)
            old_mult, _, _ = design.lookup(table, earlier)
            den = earlier.pir_per36_src.to_numpy() * old_mult
            valid = np.isfinite(den) & (den > 0)
            lag = (
                float(np.median(earlier.pir_per36_dest.to_numpy()[valid] / den[valid]))
                if valid.any()
                else np.nan
            )
            for name, value in (
                ("multiplier_value", mult),
                ("fallback", fallback),
                ("reliable", reliable),
                ("k", lag),
                ("translated", group.pir_per36_src.to_numpy() * mult * lag),
            ):
                result.loc[group.index, f"{arm}_{name}"] = value
            reason = np.where(~np.isfinite(mult), "no_finite_destination_tier", "")
            result.loc[group.index, f"{arm}_reason"] = np.where(
                np.isfinite(mult) & ~np.isfinite(lag), "no_prior_lag_outcomes", reason
            )
    result["feature_eligible"] = (
        np.logical_and.reduce(
            [np.isfinite(result[f"{d}_translated"]) for d in design.DESIGNS]
        )
        if len(result)
        else pd.Series(dtype=bool)
    )
    return result


def fit_predictions(train_features, evaluation, seasons=design.SEASONS):
    """Fit all arms using exactly one shared set of earlier matrix rows."""
    unique(train_features)
    unique(evaluation)
    output, folds = [], []
    for season in seasons:
        train = train_features[
            (train_features.season_dest < season) & train_features.feature_eligible
        ]
        test = evaluation[evaluation.season_dest == season].copy()
        audit = {"season": int(season), "train_keys": key_list(train), "arms": {}}
        statuses = []
        for arm in ("history_only", "scheduled_history", "transfer_history"):
            feature = None if arm == "history_only" else arm.removesuffix("_history")
            x = _rtm_design(
                train,
                None if feature is None else train[f"{feature}_translated"].to_numpy(),
            )
            rank = int(np.linalg.matrix_rank(x)) if len(x) else 0
            status = (
                "ok"
                if len(train) >= x.shape[1] and rank == x.shape[1]
                else (
                    "insufficient_training"
                    if len(train) < x.shape[1]
                    else "rank_deficient"
                )
            )
            statuses.append(status)
            test[arm] = np.nan
            info = {"rank": rank, "columns": x.shape[1], "status": status}
            if status == "ok":
                beta = np.linalg.lstsq(x, train.pir_per36_dest.to_numpy(), rcond=None)[
                    0
                ]
                ok = test.feature_eligible
                z = _rtm_design(
                    test[ok],
                    None
                    if feature is None
                    else test.loc[ok, f"{feature}_translated"].to_numpy(),
                )
                test.loc[ok, arm] = z @ beta
                info["coefficients"] = beta.tolist()
            audit["arms"][arm] = info
        for d in design.DESIGNS:
            test[f"{d}_multiplier"] = test[f"{d}_translated"]
        test["scored"] = np.isfinite(test[list(ARMS)]).all(axis=1)
        test["scoring_exclusion"] = ""
        for d in design.DESIGNS:
            mask = test.scoring_exclusion.eq("") & test[f"{d}_reason"].ne("")
            test.loc[mask, "scoring_exclusion"] = test.loc[mask, f"{d}_reason"]
        for status in statuses:
            if status != "ok":
                test.loc[test.scoring_exclusion.eq(""), "scoring_exclusion"] = status
        if ((~test.scored) & test.scoring_exclusion.eq("")).any():
            raise ValueError("unexplained unscorable prediction")
        test["common_cell_support"] = test.scheduled_reliable & test.transfer_reliable
        audit["scoring_keys"] = key_list(test[test.scored])
        audit["scoring_exclusions"] = test.scoring_exclusion.value_counts().to_dict()
        output.append(test)
        folds.append(audit)
    return pd.concat(output, ignore_index=True), folds


def multiway_interval(differences, first, second):
    """Conditional intercept-only CGM CR1; invalid inference is explicit."""
    d = np.asarray(differences, dtype=float)
    first, second = (
        pd.Series(first).reset_index(drop=True),
        pd.Series(second).reset_index(drop=True),
    )
    result = {
        "n": len(d),
        "difference": float(d.mean()) if len(d) else None,
        "ci95": None,
        "status": "not_estimable",
        "conditional_on_fits": True,
    }
    if len(first) != len(d) or len(second) != len(d):
        raise ValueError("cluster length mismatch")
    if not len(d):
        return {**result, "reason": "empty_population"}
    if not np.isfinite(d).all() or first.isna().any() or second.isna().any():
        return {**result, "reason": "nonfinite_difference_or_missing_cluster"}
    if first.astype(str).eq("").any() or second.astype(str).eq("").any():
        return {**result, "reason": "missing_cluster"}
    residual, components = d - d.mean(), {}
    for name, values in (
        ("first", first),
        ("second", second),
        ("intersection", pd.Series(list(zip(first, second)))),
    ):
        codes, ids = pd.factorize(values, sort=False)
        g, counts = len(ids), np.bincount(codes)
        totals = np.bincount(codes, weights=residual)
        components[name] = {
            "clusters": g,
            "max_cluster_size": int(counts.max()),
            "variance": float(g / (g - 1) * (totals @ totals) / len(d) ** 2)
            if g > 1
            else None,
        }
    result["components"] = components
    if any(c["clusters"] < 2 for c in components.values()):
        return {**result, "reason": "fewer_than_two_clusters"}
    variance = (
        components["first"]["variance"]
        + components["second"]["variance"]
        - components["intersection"]["variance"]
    )
    df = min(components["first"]["clusters"], components["second"]["clusters"]) - 1
    result.update(variance=variance, degrees_of_freedom=df)
    if not np.isfinite(variance) or variance <= 0:
        return {**result, "reason": "nonpositive_or_nonfinite_variance"}
    halfwidth = float(t.ppf(0.975, df) * np.sqrt(variance))
    return {
        **result,
        "status": "ok",
        "ci95": [float(d.mean() - halfwidth), float(d.mean() + halfwidth)],
    }


def arm_metrics(rows):
    return {
        arm: {
            "n": len(rows),
            "mae": float(np.abs(rows[arm] - rows.pir_per36_dest).mean()),
            "rmse": float(np.sqrt(np.square(rows[arm] - rows.pir_per36_dest).mean())),
            "bias": float((rows[arm] - rows.pir_per36_dest).mean()),
        }
        for arm in ARMS
    }


def summarize(rows):
    rows = rows[rows.scored]
    contrasts = {}
    for name, other in (
        ("history_increment", "history_only"),
        ("scheduled_vs_transfer", "transfer_history"),
    ):
        difference = np.abs(rows[other] - rows.pir_per36_dest) - np.abs(
            rows.scheduled_history - rows.pir_per36_dest
        )
        per_season = {
            str(int(s)): {
                "n": len(g),
                "difference": float(difference.loc[g.index].mean()),
            }
            for s, g in rows.groupby("season_dest")
        }
        contrasts[name] = {
            "player_club_season": multiway_interval(
                difference, rows.player_name, rows.cluster
            ),
            "player_season": {
                **multiway_interval(difference, rows.player_name, rows.season_dest),
                "few_season_clusters": True,
            },
            "per_season": per_season,
            "equal_season_difference": float(
                np.mean([v["difference"] for v in per_season.values()])
            )
            if per_season
            else None,
            "leave_one_season_out": {
                str(int(s)): float(difference[rows.season_dest.ne(s)].mean())
                for s in sorted(rows.season_dest.unique())
            },
        }
    return {
        "n": len(rows),
        "metrics": arm_metrics(rows),
        "contrasts": contrasts,
        "per_season_metrics": {
            str(int(s)): arm_metrics(g) for s, g in rows.groupby("season_dest")
        },
    }


def add_model_support(ledger, rows, mode):
    """Complete a disjoint per-mode observed-appearance flow with model support."""
    unique(rows)
    support = rows.set_index(KEY)
    keys = [tuple(k) for k in ledger[KEY].to_numpy()]
    ledger[f"{mode}_model_support"] = [bool(support.scored.get(k, False)) for k in keys]
    reason = ledger.first_exclusion.copy()
    if mode != "original":
        reason = reason.mask(reason.eq("destination_nonpositive"), "")
    for index, key in zip(ledger.index, keys):
        if reason.loc[index] != "":
            continue
        if ledger.loc[index, "season_dest"] not in design.SEASONS:
            reason.loc[index] = "outside_outer_seasons"
        elif key not in support.index:
            raise ValueError("eligible outer row absent from model-support ledger")
        elif support.loc[key, "scored"]:
            reason.loc[index] = "scored"
        else:
            exclusion = support.loc[key, "scoring_exclusion"]
            if not exclusion:
                raise ValueError("unexplained model-support exclusion")
            reason.loc[index] = "model_support:" + exclusion
    ledger[f"{mode}_first_exclusion"] = reason


def verify_hash(path, expected):
    if not Path(path).is_file() or sha256_file(Path(path)) != expected:
        raise ValueError(f"protected input changed or missing: {path}")


def current_raw_paths(raw_root):
    return {
        str(path.resolve())
        for pattern in blf._RAW_GLOBS
        for path in raw_root.glob(pattern.removeprefix("data/raw/"))
        if "proballers/test/" not in path.as_posix()
    }


def verify_source_run(source_run):
    manifest = json.loads((source_run / "preparation_manifest.json").read_text())
    if manifest.get("status") != "prepared" or set(manifest["variants"]) != set(
        source.VARIANTS
    ):
        raise ValueError("incomplete historical preparation")
    previous.verify_inventory(manifest["raw_inputs"] + manifest["api_inputs"])
    for name, expected in manifest["code"].items():
        verify_hash(ROOT / name, expected)
    verify_hash(
        source_run / "official_minute_evidence.json", manifest["evidence_sha256"]
    )
    verify_hash(
        source_run / "protected_baseline_manifest.json",
        manifest["baseline_manifest_sha256"],
    )
    for variant, info in manifest["variants"].items():
        if info["status"] != "prepared":
            raise ValueError(f"unprepared variant: {variant}")
        for name, expected in info["hashes"].items():
            verify_hash(source_run / "inputs" / variant / name, expected)
    return manifest


def run(source_run, out_dir):
    source_run, out_dir = Path(source_run).resolve(), Path(out_dir).resolve()
    if source_run == out_dir or source_run in out_dir.parents:
        raise ValueError("revision output must be outside protected source run")
    out_dir.mkdir(parents=True, exist_ok=True)
    status_path = out_dir / "status.json"
    design.dump_json(status_path, {"status": "running"})
    try:
        manifest = verify_source_run(source_run)
        code_hashes = {
            str(Path(__file__).relative_to(ROOT)): sha256_file(Path(__file__)),
            **previous.code_fingerprints(),
        }
        inputs = {
            str(source_run / "preparation_manifest.json"): sha256_file(
                source_run / "preparation_manifest.json"
            ),
            str(PROTOCOL): sha256_file(PROTOCOL),
        }
        for variant in source.VARIANTS:
            for name in ("adjudication.json", "pairs.parquet", "switchers.parquet"):
                path = source_run / "inputs" / variant / name
                inputs[str(path)] = sha256_file(path)
            path = source_run / "results" / variant / "chronological_rows.parquet"
            inputs[str(path)] = sha256_file(path)
        raw, inventory = source.load_raw(ROOT / "data/raw")

        def inventory_map(records):
            return {str(Path(r["source_file"]).resolve()): r["sha256"] for r in records}

        if inventory_map(inventory) != inventory_map(manifest["raw_inputs"]):
            raise ValueError("current raw inventory differs from registered inventory")
        if inventory_map(previous.api_inventory()) != inventory_map(
            manifest["api_inputs"]
        ):
            raise ValueError("current API inventory differs from registered inventory")
        evidence = json.loads(
            (source_run / "official_minute_evidence.json").read_text()
        )
        all_rows, report, outputs = {}, {}, {}
        for variant in source.VARIANTS:
            print(f"[revision] reconstruct {variant}", flush=True)
            canonical, adjudication = source.apply_variant(
                raw, variant, evidence=evidence
            )
            if adjudication.get("status") != "complete":
                raise ValueError(f"incomplete adjudication: {variant}")
            saved_adjudication = json.loads(
                (source_run / "inputs" / variant / "adjudication.json").read_text()
            )
            if adjudication != saved_adjudication:
                raise ValueError(f"adjudication changed: {variant}")
            games = canonical.drop(columns=[c for c in canonical if c.startswith("_")])
            if float(games.pir.isna().mean()) > 0.001:
                raise ValueError("inherited null efficiency refusal")
            games = blf._swap_in_api_destination(games)
            games = games[
                ~games.player_name.isin(
                    adjudication.get("ambiguous_normalized_names", [])
                )
            ]
            games = blf.add_usage(games)
            with contextlib.redirect_stdout(io.StringIO()):
                old, agg = holdout.build_switchers(games)
            ledger, recovered = reconstruct_cohort(agg)
            saved = pd.read_parquet(
                source_run / "inputs" / variant / "switchers.parquet"
            )
            reproduction = {
                "raw_switchers": previous.keyed_equal(old, saved, KEY),
                "reconstructed_positive": previous.keyed_equal(recovered, saved, KEY),
            }
            pairs = pd.read_parquet(source_run / "inputs" / variant / "pairs.parquet")
            rebuilt_pairs = blf.build_pairs(games, min_games=holdout.MIN_GAMES)
            reproduction["pairs"] = previous.keyed_equal(
                rebuilt_pairs, pairs, ["player_name", "season"]
            )
            original = ledger[ledger.original_eligible].copy().reset_index(drop=True)
            _, prepared, _ = design.prepare(pairs, saved)
            reproduction["original_eligibility"] = previous.keyed_equal(
                original[saved.columns], prepared[saved.columns], KEY
            )
            expanded = ledger[ledger.expanded_eligible].copy().reset_index(drop=True)
            study = design.Study(pairs, original, seed=0, n_boot=2000)
            original_feature = study.features()
            evaluation_feature = evaluation_features(study, expanded)
            expanded_study = design.Study(pairs, expanded, seed=0, n_boot=2000)
            expanded_feature = expanded_study.features()
            report[variant] = {"reproduction": reproduction, "modes": {}}
            for mode, train, evaluation in (
                ("original", original_feature, original_feature),
                ("evaluation_only", original_feature, evaluation_feature),
                ("expanded_training", expanded_feature, expanded_feature),
            ):
                rows, folds = fit_predictions(train, evaluation)
                rows["variant"], rows["mode"] = variant, mode
                if mode == "original":
                    expected = pd.read_parquet(
                        source_run / "results" / variant / "chronological_rows.parquet"
                    )
                    cols = [*KEY, "pir_per36_dest", *design.ARMS, "scored"]
                    reproduction["strict_predictions"] = previous.keyed_equal(
                        rows[cols], expected[cols], KEY
                    )
                rows["added_nonpositive"] = rows.pir_per36_dest <= 0
                all_rows[(variant, mode)] = rows
                report[variant]["modes"][mode] = {
                    "native": summarize(rows),
                    "added_only": summarize(rows[rows.added_nonpositive]),
                    "original_common": summarize(rows[~rows.added_nonpositive]),
                }
                mode_dir = out_dir / variant / mode
                mode_dir.mkdir(parents=True, exist_ok=True)
                row_path, fold_path = (
                    mode_dir / "predictions.parquet",
                    mode_dir / "folds.json",
                )
                rows.to_parquet(row_path, index=False)
                design.dump_json(
                    fold_path,
                    {
                        "folds": folds,
                        "cutoffs": expanded_study.diagnostics
                        if mode == "expanded_training"
                        else study.diagnostics,
                    },
                )
                for path in (row_path, fold_path):
                    outputs[str(path.relative_to(out_dir))] = sha256_file(path)
                add_model_support(ledger, rows, mode)
            # An original-common comparison uses the exact intersection of
            # scored original-positive keys across all three training modes.
            original_common = set.intersection(
                *[
                    set(
                        map(
                            tuple,
                            all_rows[(variant, m)]
                            .loc[lambda x: x.scored & ~x.added_nonpositive, KEY]
                            .to_numpy(),
                        )
                    )
                    for m in MODES
                ]
            )
            for mode in MODES:
                rows = all_rows[(variant, mode)]
                selected = rows[
                    [tuple(k) in original_common for k in rows[KEY].to_numpy()]
                ]
                report[variant]["modes"][mode]["original_common"] = summarize(selected)
            outer = ledger[ledger.season_dest.isin(design.SEASONS)]
            report[variant]["flow"] = {
                "all_observed": len(ledger),
                "outer_observed": len(outer),
                "first_exclusion": outer.first_exclusion.replace(
                    "", "eligible_before_model"
                )
                .value_counts()
                .to_dict(),
                "mode_first_exclusion": {
                    mode: outer[f"{mode}_first_exclusion"].value_counts().to_dict()
                    for mode in MODES
                },
                "flags": {
                    c: int(outer[c].sum()) for c in ledger if ledger[c].dtype == bool
                },
                "denominator": "observed continental player-seasons, not all signings",
            }
            if sum(report[variant]["flow"]["first_exclusion"].values()) != len(outer):
                raise ValueError("cohort flow does not conserve denominator")
            ledger_path = out_dir / variant / "cohort_ledger.parquet"
            ledger.to_parquet(ledger_path, index=False)
            outputs[str(ledger_path.relative_to(out_dir))] = sha256_file(ledger_path)
        common_report = {}
        for mode in MODES:
            keys = set.intersection(
                *[
                    set(
                        map(
                            tuple,
                            all_rows[(v, mode)].loc[lambda x: x.scored, KEY].to_numpy(),
                        )
                    )
                    for v in source.VARIANTS
                ]
            )
            common_report[mode] = {"n": len(keys), "variants": {}}
            for variant in source.VARIANTS:
                rows = all_rows[(variant, mode)]
                selected = rows[[tuple(k) in keys for k in rows[KEY].to_numpy()]]
                common_report[mode]["variants"][variant] = summarize(selected)
        for path, expected in inputs.items():
            verify_hash(path, expected)
        verify_source_run(source_run)
        if current_raw_paths(ROOT / "data/raw") != set(
            inventory_map(manifest["raw_inputs"])
        ):
            raise ValueError("raw inventory file set changed during revision")
        if inventory_map(previous.api_inventory()) != inventory_map(
            manifest["api_inputs"]
        ):
            raise ValueError("API inventory changed during revision")
        for name, expected in code_hashes.items():
            verify_hash(ROOT / name, expected)
        summary = {
            "schema_version": 1,
            "status": "complete",
            "protocol": str(PROTOCOL),
            "seed": 0,
            "factor_bootstrap": 2000,
            "source_run": str(source_run),
            "input_hashes": inputs,
            "historical_inventory": manifest,
            "code_hashes": code_hashes,
            "output_hashes": outputs,
            "variants": report,
            "cross_variant_common": common_report,
            "original_common_definition": (
                "Scored positive-outcome key intersection across all three modes"
            ),
            "limitations": (
                "Conditional fixed-forecast inference; six season clusters; "
                "no full refitting uncertainty; observed appearances exclude "
                "unobserved signings."
            ),
        }
        design.dump_json(out_dir / "summary.json", summary)
        design.dump_json(
            status_path,
            {
                "status": "complete",
                "summary_sha256": sha256_file(out_dir / "summary.json"),
            },
        )
        return summary
    except Exception as exc:
        design.dump_json(
            status_path, {"status": "failed", "error": f"{type(exc).__name__}: {exc}"}
        )
        raise


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-run", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args(argv)
    with threadpool_limits(limits=1):
        run(args.source_run, args.out_dir)


if __name__ == "__main__":
    main()
