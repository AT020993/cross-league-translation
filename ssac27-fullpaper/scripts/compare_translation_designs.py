#!/usr/bin/env python3
"""Chronological scheduled versus mover research, isolated from operating fits."""

from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys

for _key in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[_key] = "1"
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from scripts.translation_research_common import fit_table  # noqa: E402
from scripts.validate_translation_holdout import EXCLUDED_SOURCE  # noqa: E402
from scripts.validate_translation_walkforward import _rtm_design  # noqa: E402

SEASONS = tuple(range(2020, 2026))
DESIGNS = ("scheduled", "transfer")
ARMS = tuple(f"{d}_{a}" for d in DESIGNS for a in ("multiplier", "history"))


def stable_seed(seed, *keys):
    return int.from_bytes(
        hashlib.sha256(json.dumps([seed, *keys]).encode()).digest()[:4], "little"
    )


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def dump_json(path, obj):
    def clean(x):
        if isinstance(x, dict):
            return {str(k): clean(v) for k, v in x.items()}
        if isinstance(x, (list, tuple)):
            return [clean(v) for v in x]
        if isinstance(x, np.generic):
            return clean(x.item())
        if isinstance(x, float) and not np.isfinite(x):
            return None
        return x

    Path(path).write_text(json.dumps(clean(obj), indent=2, allow_nan=False) + "\n")


def prepare(pairs, switchers):
    for frame, key in (
        (pairs, ["player_name", "season"]),
        (switchers, ["player_name", "season_dest"]),
    ):
        if frame.duplicated(key).any() or frame[key].isna().any().any():
            raise ValueError(f"duplicate or missing identity: {key}")
    sw = switchers.copy()
    sw["input_exclusion"] = ""
    checks = [
        (sw.was_cont != 0, "continental_incumbent"),
        (sw.league_src.isin(EXCLUDED_SOURCE), "registered_source_exclusion"),
        ((sw.pir_per36_src <= 0) | (sw.pir_per36_dest <= 0), "nonpositive_rate"),
        (
            ~np.isfinite(sw.pir_per36_src) | ~np.isfinite(sw.pir_per36_dest),
            "nonfinite_rate",
        ),
    ]
    for side in ("src", "dest"):
        if f"games_{side}" in sw:
            checks.append((sw[f"games_{side}"] < 8, f"{side}_game_floor"))
        checks.append(
            (
                ~np.isfinite(sw[f"minutes_{side}"]) | (sw[f"minutes_{side}"] <= 0),
                f"{side}_minutes",
            )
        )
    for mask, reason in checks:
        sw.loc[mask & sw.input_exclusion.eq(""), "input_exclusion"] = reason
    return pairs.copy(), sw[sw.input_exclusion.eq("")].copy().reset_index(drop=True), sw


def matched_tables(scheduled, transfer, cutoff, repetition, seed):
    selected, counts = [[], []], []
    groups = [
        dict(tuple(x.groupby(["league_src", "league_dest"], sort=True)))
        for x in (scheduled, transfer)
    ]
    for cell in sorted(set(groups[0]) | set(groups[1])):
        ns = [len(g[cell]) if cell in g else 0 for g in groups]
        n = min(ns)
        counts.append(
            {
                "source": cell[0],
                "destination": cell[1],
                "scheduled_n": ns[0],
                "transfer_n": ns[1],
                "retained_each": n,
            }
        )
        for i, group in enumerate(groups):
            if n:
                sub = (
                    group[cell]
                    .sort_values(["player_name", "season"])
                    .reset_index(drop=True)
                )
                rng = np.random.default_rng(
                    stable_seed(seed, "matched", cutoff, repetition, *cell, i)
                )
                selected[i].append(sub.iloc[rng.choice(len(sub), n, replace=False)])
    return [
        pd.concat(s, ignore_index=True) if s else base.iloc[:0].copy()
        for s, base in zip(selected, (scheduled, transfer))
    ], counts


def lookup(table, rows):
    tiers = (
        table.groupby("destination").tier_mean.first().to_dict() if len(table) else {}
    )
    cells = {(r.league, r.destination): r for r in table.itertuples()}
    values, fallback, reliable = [], [], []
    for r in rows.itertuples():
        cell = cells.get((r.league_src, r.league_dest))
        ok = cell is not None and bool(cell.reliable) and np.isfinite(cell.factor)
        values.append(cell.factor if ok else tiers.get(r.league_dest, np.nan))
        fallback.append(not ok)
        reliable.append(ok)
    return np.asarray(values, dtype=float), np.asarray(fallback), np.asarray(reliable)


class Study:
    def __init__(
        self, pairs, cohorts, *, seed=0, n_boot=2000, repetition=None, fitter=fit_table
    ):
        self.pairs, self.cohorts = pairs, cohorts
        self.movers = cohorts.assign(season=cohorts.season_dest)
        self.seed, self.n_boot, self.repetition, self.fitter = (
            seed,
            n_boot,
            repetition,
            fitter,
        )
        self.tables, self.diagnostics = {}, {}

    def at(self, cutoff):
        if cutoff in self.tables:
            return self.tables[cutoff]
        sources = [
            self.pairs[self.pairs.season < cutoff],
            self.movers[self.movers.season < cutoff],
        ]
        counts = []
        if self.repetition is not None:
            sources, counts = matched_tables(
                *sources, cutoff, self.repetition, self.seed
            )
        tables, audit = {}, {"matched_counts": counts}
        for design, source in zip(DESIGNS, sources):
            table = self.fitter(source, n_boot=self.n_boot, seed=self.seed)
            tables[design] = table
            audit[design] = {
                "n_pairs": len(source),
                "reliable_cells": int(table.reliable.sum()),
                "cells": table.to_dict("records"),
            }
        self.tables[cutoff], self.diagnostics[cutoff] = tables, audit
        return tables

    def features(self):
        """Each row's factors and lag exclude its own and future outcomes."""
        rows = self.cohorts.copy()
        for design in DESIGNS:
            rows[f"{design}_translated"] = np.nan
            rows[f"{design}_reason"] = ""
            rows[f"{design}_fallback"] = False
            rows[f"{design}_reliable"] = False
        for season, group in rows.groupby("season_dest", sort=True):
            earlier = self.cohorts[self.cohorts.season_dest < season]
            for design, table in self.at(int(season)).items():
                m, fallback, reliable = lookup(table, group)
                old_m, _, _ = lookup(table, earlier)
                den = earlier.pir_per36_src.to_numpy() * old_m
                valid = np.isfinite(den) & (den > 0)
                k = (
                    float(
                        np.median(earlier.pir_per36_dest.to_numpy()[valid] / den[valid])
                    )
                    if valid.any()
                    else np.nan
                )
                for name, value in (
                    ("multiplier_value", m),
                    ("fallback", fallback),
                    ("reliable", reliable),
                    ("k", k),
                    ("translated", group.pir_per36_src.to_numpy() * m * k),
                ):
                    rows.loc[group.index, f"{design}_{name}"] = value
                reason = np.where(~np.isfinite(m), "no_finite_destination_tier", "")
                reason = np.where(
                    np.isfinite(m) & ~np.isfinite(k), "no_prior_lag_outcomes", reason
                )
                rows.loc[group.index, f"{design}_reason"] = reason
                self.diagnostics[int(season)][design].update(
                    lag_eligible=int(valid.sum()),
                    lag_excluded=int(len(earlier) - valid.sum()),
                    k=k,
                )
        rows["feature_eligible"] = np.logical_and.reduce(
            [np.isfinite(rows[f"{d}_translated"]) for d in DESIGNS]
        )
        return rows

    def run(self, seasons=SEASONS):
        feature = self.features()
        output, folds = [], []
        for season in seasons:
            train_all = feature[feature.season_dest < season]
            train = train_all[train_all.feature_eligible]
            test = feature[feature.season_dest == season].copy()
            audit = {
                "season": season,
                "input_train": len(train_all),
                "usable_train": len(train),
                "input_test": len(test),
                "feature_eligible_test": int(test.feature_eligible.sum()),
                "train_exclusions": {
                    d: train_all[f"{d}_reason"].value_counts().to_dict()
                    for d in DESIGNS
                },
            }
            for design in DESIGNS:
                test[f"{design}_multiplier"] = test[f"{design}_translated"]
                test[f"{design}_history"] = np.nan
                x = _rtm_design(train, train[f"{design}_translated"].to_numpy())
                rank = int(np.linalg.matrix_rank(x)) if len(x) else 0
                status = (
                    "ok"
                    if len(train) >= x.shape[1] and rank == x.shape[1]
                    else "insufficient_training"
                    if len(train) < x.shape[1]
                    else "rank_deficient"
                )
                audit[design] = {"rank": rank, "columns": x.shape[1], "status": status}
                if status == "ok":
                    beta = np.linalg.lstsq(
                        x, train.pir_per36_dest.to_numpy(), rcond=None
                    )[0]
                    ok = test.feature_eligible
                    test.loc[ok, f"{design}_history"] = (
                        _rtm_design(
                            test[ok], test.loc[ok, f"{design}_translated"].to_numpy()
                        )
                        @ beta
                    )
                    audit[design]["coefficients"] = beta.tolist()
                test[f"{design}_history_reason"] = test[f"{design}_reason"]
                if status != "ok":
                    empty_reason = test[f"{design}_history_reason"].eq("")
                    test.loc[empty_reason, f"{design}_history_reason"] = status
                audit[design]["tier_fallback_test"] = int(
                    test[f"{design}_fallback"].sum()
                )
            test["scored"] = np.isfinite(test[list(ARMS)]).all(axis=1)
            audit.update(
                scored=int(test.scored.sum()), excluded=int((~test.scored).sum())
            )
            test["scoring_exclusion"] = test["scheduled_history_reason"].where(
                test["scheduled_history_reason"].ne(""), test["transfer_history_reason"]
            )
            if ((~test.scored) & test.scoring_exclusion.eq("")).any():
                raise ValueError("unexplained nonfinite outer prediction")
            test["common_cell_support"] = (
                test.scheduled_reliable & test.transfer_reliable
            )
            output.append(test)
            folds.append(audit)
        return pd.concat(output, ignore_index=True), {
            "folds": folds,
            "cutoffs": self.diagnostics,
        }


def contrast(rows, suffix="history", cluster="cluster", *, seed=0, n_boot=4000):
    if rows.empty:
        return {"n": 0, "difference": None, "ci95": None}
    y = rows.pir_per36_dest.to_numpy()
    difference = np.abs(rows[f"transfer_{suffix}"].to_numpy() - y) - np.abs(
        rows[f"scheduled_{suffix}"].to_numpy() - y
    )
    ids, inverse = np.unique(rows[cluster].astype(str), return_inverse=True)
    totals, counts = np.bincount(inverse, weights=difference), np.bincount(inverse)
    rng = np.random.default_rng(stable_seed(seed, suffix, cluster))
    draws = np.empty(n_boot)
    for i in range(n_boot):
        ix = rng.integers(0, len(ids), len(ids))
        draws[i] = totals[ix].sum() / counts[ix].sum()
    return {
        "n": len(rows),
        "n_clusters": len(ids),
        "difference": float(difference.mean()),
        "ci95": np.quantile(draws, [0.025, 0.975]).tolist() if len(ids) > 1 else None,
    }


def metrics(rows):
    return {
        a: {
            "mae": float(np.abs(rows[a] - rows.pir_per36_dest).mean()),
            "rmse": float(np.sqrt(np.square(rows[a] - rows.pir_per36_dest).mean())),
            "bias": float((rows[a] - rows.pir_per36_dest).mean()),
            "n": len(rows),
        }
        for a in ARMS
    }


def summarize(rows, seed=0):
    scored = rows[rows.scored]
    club, player = (
        contrast(scored, seed=seed),
        contrast(scored, cluster="player_name", seed=seed),
    )
    cis = [club["ci95"], player["ci95"]]
    verdict = (
        "superiority"
        if all(ci and ci[0] > 0 for ci in cis)
        else "sensitivity_disagreement"
        if all(cis) and ((cis[0][0] > 0) != (cis[1][0] > 0))
        else "inconclusive"
    )
    return {
        "metrics": metrics(scored),
        "primary_club_season": club,
        "primary_player": player,
        "verdict": verdict,
        "multiplier_contrast": contrast(scored, "multiplier", seed=seed),
        "per_season": {int(s): metrics(g) for s, g in scored.groupby("season_dest")},
        "above_prior": metrics(
            scored[scored.above_own_prior.fillna(False).astype(bool)]
        ),
        "common_cell_support": metrics(scored[scored.common_cell_support]),
        "input_outer": len(rows),
        "scored": len(scored),
        "excluded": len(rows) - len(scored),
    }


def provenance(input_dir, seed):
    sources = [
        Path(__file__),
        *[
            Path(__file__).with_name(x)
            for x in (
                "translation_research_common.py",
                "build_league_factors.py",
                "validate_translation_walkforward.py",
                "validate_translation_holdout.py",
            )
        ],
    ]
    return {
        "inputs": {
            p.name: digest(p) for p in sorted(input_dir.iterdir()) if p.is_file()
        },
        "code": {p.name: digest(p) for p in sources},
        "seed": seed,
        "seasons": list(SEASONS),
        "repetitions": 200,
        "factor_bootstrap": 2000,
        "contrast_bootstrap": 4000,
        "min_pairs": 75,
    }


def load_cache(rowpath, reportpath, donepath):
    expected = json.loads(donepath.read_text())
    if (
        not rowpath.exists()
        or not reportpath.exists()
        or expected != {"rows": digest(rowpath), "report": digest(reportpath)}
    ):
        raise ValueError(f"incomplete or corrupt cache entry {donepath.stem}")
    return pd.read_parquet(rowpath), json.loads(reportpath.read_text())


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--workers", type=int, default=1)
    args = parser.parse_args(argv)
    if args.workers != 1:
        parser.error("this implementation supports --workers 1 only")
    args.out_dir.mkdir(parents=True, exist_ok=True)
    prov = provenance(args.input_dir, args.seed)
    cache_key = hashlib.sha256(json.dumps(prov, sort_keys=True).encode()).hexdigest()[
        :16
    ]
    cache = args.out_dir / "design_comparison_cache" / cache_key
    cache.mkdir(parents=True, exist_ok=True)
    manifest = cache / "provenance.json"
    if manifest.exists() and json.loads(manifest.read_text()) != prov:
        raise ValueError("cache provenance mismatch; use a fresh output directory")
    dump_json(manifest, prov)
    pairs, cohort, raw = prepare(
        pd.read_parquet(args.input_dir / "pairs.parquet"),
        pd.read_parquet(args.input_dir / "switchers.parquet"),
    )
    expected_keys = set(
        zip(
            cohort.loc[cohort.season_dest.isin(SEASONS), "player_name"],
            cohort.loc[cohort.season_dest.isin(SEASONS), "season_dest"],
        )
    )
    runs = []
    for repetition in [None, *range(200)]:
        tag = "full" if repetition is None else f"{repetition:03d}"
        rowpath, reportpath, donepath = [
            cache / f"{tag}.{ext}" for ext in ("parquet", "json", "done.json")
        ]
        if donepath.exists():
            rows, report = load_cache(rowpath, reportpath, donepath)
        else:
            rows, report = Study(
                pairs, cohort, seed=args.seed, repetition=repetition
            ).run()
            report["summary"] = summarize(rows, args.seed)
            rows.to_parquet(rowpath, index=False)
            dump_json(reportpath, report)
            dump_json(donepath, {"rows": digest(rowpath), "report": digest(reportpath)})
        if (
            sorted(rows.season_dest.unique()) != list(SEASONS)
            or rows.duplicated(["player_name", "season_dest"]).any()
        ):
            raise ValueError(f"incomplete row keys for {tag}")
        if set(zip(rows.player_name, rows.season_dest)) != expected_keys:
            raise ValueError(f"incomplete population keys for {tag}")
        print(f"Study B {tag}: scored={int(rows.scored.sum())}/{len(rows)}", flush=True)
        if repetition is None:
            rows.to_parquet(
                args.out_dir / "design_comparison_rows.parquet", index=False
            )
            full = report
        else:
            runs.append(rows.assign(repetition=repetition))
    downsamples = pd.concat(runs, ignore_index=True)
    if downsamples.repetition.nunique() != 200:
        raise ValueError("incomplete matched-count repetitions")
    downsamples.to_parquet(
        args.out_dir / "design_comparison_downsamples.parquet", index=False
    )
    contrasts = []
    for rep, group in downsamples.groupby("repetition"):
        g = group[group.scored]
        contrasts.append(
            {
                "repetition": int(rep),
                "n": len(g),
                "difference": float(
                    (
                        np.abs(g.transfer_history - g.pir_per36_dest)
                        - np.abs(g.scheduled_history - g.pir_per36_dest)
                    ).mean()
                ),
            }
        )
    summary = {
        "complete": True,
        "provenance": prov,
        "input_exclusions": raw.input_exclusion.value_counts().to_dict(),
        **full,
        "matched_repetitions": contrasts,
        "matched_spread_is_not_ci": True,
        "interval_target": (
            "paired prediction MAE difference; raw factor intervals "
            "do not calibrate pooled factors"
        ),
        "lag_definition": (
            "median earlier outcome / (source rate times "
            "cutoff-specific factor); multiplier arms include lag correction"
        ),
    }
    dump_json(args.out_dir / "design_comparison_summary.json", summary)
    s = full["summary"]
    note = (
        "# Scheduled versus historical-transfer estimation\n\n"
        f"All four arms use {s['scored']} identical scored newcomer rows; "
        f"{s['excluded']} outer rows are excluded. Verdict: **{s['verdict']}**.\n\n"
        "Primary contrast MAE(transfer + history) minus "
        f"MAE(scheduled + history): {s['primary_club_season']['difference']}. "
        f"Club-season interval: {s['primary_club_season']['ci95']}; "
        f"player interval: {s['primary_player']['ci95']}.\n\n"
        "The 200 matched-count runs retain the 75-pair floor at every inner "
        "and outer cutoff. Their overlapping spread is descriptive, not a "
        "confidence interval. Startup missing tiers, unavailable lag corrections, "
        "rank deficiencies and pooling collapses are retained in JSON and rows. "
        "Raw factor intervals concern raw factors, not pooled points. This "
        "exploratory retrospective comparison makes no equivalence claim.\n"
    )
    (args.out_dir / "design_comparison_note.md").write_text(note)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
