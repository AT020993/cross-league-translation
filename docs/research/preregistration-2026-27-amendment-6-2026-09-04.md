# AMENDMENT 6 to the 2026-27 prospective pre-registration — source-season lag recorded (not refused), the estimator's measured-null constants re-pinned to a committed generator, the alternative pooler deferred

**Date: 2026-09-04. Tickets: ATI-2959 (Change 1), ATI-2890 (Changes 2 and 3), recorded on ATI-2891. Status: decided by Amir on 2026-09-04, the same day Amendment 5 was accepted; binding on the lock.** Base document is `preregistration-2026-27-predictions.md`. Prior amendments: `-amendment-1-2026-08-21.md` … `-amendment-5-2026-09-04.md`. Lock deadline **24 September 2026**, tip-off.

## Specification

| Choice | This amendment | Alternatives considered |
|---|---|---|
| **Scope** | three decisions taken after Amendment 5's acceptance: what the lock does about predictions whose source season is not the latest possible one; the two estimator constants whose cited source no longer exists; whether the pooler the predictions were built on is swapped before the lock | folding them into Amendment 5 (rejected — a document cannot be accepted and changed in the same edit) |
| **Evidence admitted** | `data/processed/predictions/source_season_staleness_2026.json` (`scripts/report_source_season_staleness.py`); `docs/research/artifacts/translation-estimator-synthetic-2026-09-04/summary_api.json` (`scripts/simulate_translation_estimator.py`); the rebuilt `translation_predictions_2026.json` diffed against its committed predecessor; `league_factors.parquet` before and after the re-pin | — |
| **Constraint** | no bar moved, no metric changed, no gate re-scored (`METHOD.md` §8). Change 1 adds a recorded field and a descriptive read, not a refusal rule. Change 2 moves a *comparison point* that no prediction field, no walk-forward arm, no holdout gate and no checkpoint gate reads; the proof is the diff, printed below | — |
| **Traceability** | every number names its generator and field (`METHOD.md` §13, §16) | — |

---

## Change 1 — Source-season staleness is recorded on every row and read at scoring; it is not a refusal (ATI-2959, option 2)

**What the base document permits.** §2's source-season rule takes a player's *latest qualifying* corpus season, and Amendment 4 made a completed earlier season qualify when the 2025-26 one is incomplete. Seven of the 50 predictions on the 2026-08-21 collection therefore rest on a source season before 2025-26 (Amendment 5, Change 3). The base document says nothing about how far back is too far.

**Options measured before deciding** (`scripts/report_source_season_staleness.py`, committed artifact `source_season_staleness_2026.json`):

| option | effect on the 2026-08-21 set | B0-criterion power (Amendment 5 table, scaled to n) |
|---|---|---|
| 1 — a new refusal R10 `SOURCE_SEASON_STALE` at `max_lag` 0 / 1 / 2 / 3 | refuses 7 / 5 / 4 / 4 of 50 | 0.500 / 0.518 / 0.527 / 0.527 (from 0.561 at n = 50) |
| **2 — score as-is, record the lag** | n stays 50; 7 rows carry lag > 0 | 0.561 |
| 3 — prefer the latest season when it holds ≥ 8 games | moves 0 of 7 rows (the sweep prints why for each) | — |

**Decision: option 2.** Option 1 pays power the set already lacks to remove an effect nobody has measured; option 3 is empty on this collection. The 2026-27 outcomes are the first data that can say whether a stale source season predicts worse, so the lock records the lag and the scoring reads it.

**Rule.** Every prediction and refusal row carries `source_season_lag = (season − 1) − source_season` (`None` where no corpus season exists). `src/data/translation_predictions.py::source_season_lag`; the field is in `PREDICTION_FIELDS` and `REFUSAL_FIELDS`, so the schema test pins it. On the 2026-08-21 collection: 7 predictions and 7 refusals carry lag > 0; 32 refusals (no corpus season) carry `None`. The seven predictions: SARIC, DARIO (turkey-bsl 2015, lag 10); CANCAR, VLATKO (spain-acb 2018, 7); GAZZOTTI, GIULIO (italy-lba 2018, 7); RICHARDSON, ALEXANDER (germany-bbl 2021, 4); EVANS, KEENAN (lithuania-lkl 2023, 2); ALLMAN, KYLE (turkey-bsl 2024, 1); KREISMONTAS, LUKAS (lithuania-lkl 2024, 1).

**Scoring read (secondary, descriptive, pre-registered here).** `scripts/evaluate_translation_predictions.py::mae_by_source_season_lag` reports model and B0 MAE on lag-0 rows against lag > 0 rows at every checkpoint, under `by_source_season_lag`. It is **not a gate** and does not enter the verdict; at n = 7 it can say whether stale rows miss by more, not by how much. A row without the field (none in this artifact) is reported as `unknown`, never pooled into lag 0. Test: `tests/test_scripts/test_evaluate_translation_predictions.py::test_the_checkpoint_splits_mae_by_source_season_lag_without_gating_on_it`.

**Rebuild check.** `scripts/build_translation_predictions.py --built-at 2026-09-04` on the same signings file: 50 predictions and 70 refusals, every top-level field and every row field byte-equal to the committed 2026-09-04 artifact except the new `source_season_lag`; `translation_factors_2026.csv` identical. The builder fits its own fold and reads neither constant in Change 2.

## Change 2 — `MEASURED_NULL` and `INTERVAL_CALIBRATION` are re-pinned to the committed 2026-09-04 study

**Why.** Both constants in `scripts/build_league_factors.py` cited "ATI-2890 synthetic validation, 2026-08-17". That study's script and artifact exist on no disk or mirror (ATI-2890, PR #2064); the numbers were quoted, not re-derivable, which `METHOD.md` §16 forbids. The study was re-derived with a committed generator on both corpora (`docs/research/translation-estimator-synthetic-validation-2026-09-04.md`), and the API template — the destination side Amendment 5 fixed — is the source of record.

| constant | 2026-08-17 value (lost artifact) | 2026-09-04 value (`summary_api.json` field) | Proballers template, for the record |
|---|---:|---:|---:|
| `MEASURED_NULL["exposure_weighted"]` (primary) | 1.0181 | **1.0287** (`s2.null_by_estimator.exposure_weighted.mean`, MC SE 0.0022) | 1.0268 |
| `MEASURED_NULL["ratio_of_sums"]` | 0.9998 | **0.9995** | 1.0002 |
| `MEASURED_NULL["mean_of_ratios"]` | 1.0231 | **1.0431** | 1.0301 |
| `INTERVAL_CALIBRATION["realised_pooled"]` | 0.86 | **0.77** (`s1.pooled_coverage_95.mean`) | 0.74 |
| `INTERVAL_CALIBRATION["realised_at_n_500"]` | 0.73 | **0.65** (`s1.by_n_at_0.85.500.coverage_95.mean`) | 0.64 |

**What reads them, and the proof nothing pre-registered moved.** `MEASURED_NULL[PRIMARY]` is the comparison point of the descriptive flag `excludes_measured_null` in `league_factors.parquet`, and both constants are echoed in `league_factors_checks.json: external_validity`. Nothing else reads them: the prediction builder reads `reliable` (a pair-count floor), the walk-forward and the holdout compare arms on MAE / R², and the checkpoint evaluator has no reference to either. After the re-pin, `scripts/build_league_factors.py --continental-source api` was re-run: all 1,440 rows keep byte-identical `factor`, `factor_raw`, `se`, `ci_lo`, `ci_hi`, `n_pairs`, `reliable`, `tau` and `tier_mean`; only `excludes_measured_null` moves, on 66 rows (52 intervals whose upper end sits between the two nulls now read as excluding it, 14 whose lower end does now read as covering it), and `league_factors_checks.json` differs only in the two echoed constants. On the 20 headline PIR / all-pairs / all-era cells the lock reads, **no flag moved** (49 of the 60 PIR all-pairs cells across the three eras carry the flag, from 50; the one flip is spain-acb → EuroCup, 2020–2025 era, whose interval [1.024, 1.107] now straddles the null). The holdout script re-run on the same corpus (`scripts/validate_translation_holdout.py --continental-source api`) returns a `validation_summary.json` and `validation_metrics.csv` identical to the 2026-09-04 second record apart from timestamps — the G4 contrast is still +0.0429 [−0.1331, +0.2224]. The Proballers-side table (`data/processed/translation_proballers_2026-08-21/`) is left as the 2026-08-21 record; its flag column was computed against the old null and says so here.

**What the re-pin changes in reading.** A factor's interval must now clear 1.0287, not 1.0181, before the parquet describes it as excluding the estimator's own null; the interval label is "77% realised coverage, 65% at n = 500", not 86 / 73. Both are more conservative than before. The synthetic note's S2 table keeps the 2026-08-17 column labelled as a lost artifact, and its `excludes_measured_null` column is annotated as computed against the null pinned at run time.

## Change 3 — The floor-clearing τ² pooler is deferred to the 2027 refit (ATI-2960)

The synthetic study found that one cell of n ≤ 5 pairs below the 75-pair floor collapses a real-shaped block's partial pooling to the tier mean with probability 0.10–0.13 under the shipped `partial_pool` on the API template (0.15–0.20 on the Proballers template; 0.2–0.6 on the API template when that cell's SE ≥ 0.2), and 0.01–0.03 (API) / 0.00–0.01 (Proballers) under an alternative that estimates τ² from floor-clearing cells only (`summary_<template>.json: s4.collapse.<n>.p_tau_zero_shipped`, `.p_tau_zero_alt`). **The alternative is not adopted before the lock.** The 2026-27 predictions are built on the shipped pooler; swapping it now would change pre-registered numbers for a gain the study measured as marginal on the floor-clearing cells' pooled RMSE (API template, n ≤ 5: 0.0321–0.0322 shipped vs 0.0298–0.0302 alternative; `s4.collapse.<n>.rmse_pooled_shipped_clearing` / `.rmse_pooled_alt_clearing`). It is filed as ATI-2960 for the 2027 refit, where it can be compared on realised 2026-27 outcomes.

---

## Provenance

| Item | Where it is fixed |
|---|---|
| lag field and its rule | `src/data/translation_predictions.py::source_season_lag`, `PREDICTION_FIELDS`, `REFUSAL_FIELDS`; `tests/test_data/test_translation_predictions.py` (schema) |
| staleness options measured | `scripts/report_source_season_staleness.py` → `data/processed/predictions/source_season_staleness_2026.json` |
| scoring split | `scripts/evaluate_translation_predictions.py::mae_by_source_season_lag` |
| re-pinned constants and their tests | `scripts/build_league_factors.py::MEASURED_NULL`, `::INTERVAL_CALIBRATION`; `tests/test_scripts/test_build_league_factors.py` |
| the study they are read from | `scripts/simulate_translation_estimator.py` → `docs/research/artifacts/translation-estimator-synthetic-2026-09-04/summary_api.json` |
| prediction set after Change 1 | `data/processed/predictions/translation_predictions_2026.json` (`built_at: 2026-09-04`, `status: draft`) |
| deferred pooler | ATI-2960 |
