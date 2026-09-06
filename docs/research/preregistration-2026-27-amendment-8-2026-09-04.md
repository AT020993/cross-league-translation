# AMENDMENT 8 to the 2026-27 prospective pre-registration — the lock carries a split-conformal interval; no stat-specific secondary arm is carried

**Date: 2026-09-04. Tickets: ATI-2962 (Study B), ATI-2963 (Study C), recorded on ATI-2891. Status: committed before Study A's evaluator runs, as `prelock-program-preregistration-2026-09-04.md` §8 requires; the commit order is the proof.** Base document is `preregistration-2026-27-predictions.md`. Prior amendments: `-amendment-1-2026-08-21.md` … `-amendment-7-2026-09-04.md`. Lock deadline **24 September 2026**; lock day per Amendment 7 Change 1.

## Specification

| Choice | This amendment | Alternatives considered |
|---|---|---|
| **Scope** | two decisions the pre-lock program pre-registered for this amendment: which interval family the 2026-27 prediction set carries, and which stats (if any) get a secondary projection arm | deciding either after the rehearsal's evaluator has run (rejected — §8 of the program: the rehearsal informs no 2026-27 rule) |
| **Design** | interval: the family selected on folds ≤ 2024 by the program's Study C rule, recalibrated on folds ≤ 2025 for the lock; secondary arms: the program's Study B rule applied to folds ≤ 2024, then a scope decision on what the rule selected | keeping the base document's multiplier interval by default (rejected — a family that loses the pre-registered score to a simpler-to-justify one, with the multiplier as the control, has been measured; not adopting the winner would be moving a rule after the read) |
| **Evidence admitted** | `docs/research/artifacts/prelock-program-2026-09/intervals_summary.json` (Study C), `stat_translation_summary.json` (Study B), `interval_params_lock.json`, `interval_params_rehearsal_through_2024.json`, `power_rehearsal_2025.json`; every number below names its field | the 2025 fold (not admitted: it is the confirmation fold, read only after this amendment) |
| **Constraint** | the coverage gate S2 and its band [0.90, 0.98] are unchanged; the point projection, the refusals, K_LAG and every baseline are unchanged; no threshold moves (METHOD.md §8) | — |
| **Traceability** | generators are `scripts/calibrate_prediction_intervals.py` and `scripts/validate_stat_translation.py`, both committed with tests; the lock uses `scripts/build_translation_predictions.py --interval-params` | — |

---

## Change 1 — The interval the lock carries is split conformal, calibrated on folds ≤ 2025

**Selection, folds ≤ 2024** (`intervals_summary.json::pooled_selection_folds`; rolling calibration, scored folds 2022–2024, 312 rows; `selection.reason` = "lowest Winkler inside the band"):

| family | coverage | mean width (per-36 PIR) | Winkler ± SE |
|---|---:|---:|---:|
| multiplier (base document §4; the control) | 0.949 | 17.04 | 21.90 ± 1.51 |
| **split conformal** | **0.955** | **16.02** | **19.82 ± 1.28** |
| normalised (σ̂ from ŷ and games) | 0.949 | 16.30 | 20.26 ± 1.35 |
| conformalised quantile regression | 0.942 | 15.56 | 20.51 ± 1.42 |

All four sit inside the band. The tie threshold (best + one SE) is 21.10; the multiplier is outside it, so the tie rule that would have kept the simpler family does not apply. Negative controls (`negative_controls`): α = 0.5 gives coverage 0.554 and fails the band (the gate discriminates); calibrating on the scored fold gives 0.962 against the honest 0.955 (the leak over-covers, so the rolling read is not leaked).

**What the interval is.** For every row, `[projection − q̂, projection + q̂]`, where q̂ is the ⌈(n+1)(1−α)⌉/n-th order statistic of the absolute residuals |y − projection| on the calibration rows, α = 0.05. Under exchangeable residuals the marginal coverage is ≥ 0.95 in finite samples; the walk-forward read above is the empirical check. The half-width is the same for every row — the base document's interval scaled with the point, and Study C found no gain from doing so (the normalised family did not beat it).

**Parameters, both committed** (`scripts/calibrate_prediction_intervals.py --lock-calibration [--calibrate-through 2024]`):

| use | file | folds | n_cal | q̂ |
|---|---|---|---:|---:|
| **the 2026-27 lock** | `interval_params_lock.json` | 2020–2025 | 674 | 8.1298 |
| the 2025-26 rehearsal (Study A) | `interval_params_rehearsal_through_2024.json` | 2020–2024 | 547 | 7.7843 |

The rehearsal's interval stops at 2024 so its coverage read on 2025-26 is out of sample, exactly as the lock's will be on 2026-27. The lock's q̂ is fixed here and is not refit after any 2025-26 read.

**Amendment 7 Change 1, step 3, now reads:** `scripts/build_translation_predictions.py --signings <that artifact> --built-at <lock-date> --status locked --interval-params docs/research/artifacts/prelock-program-2026-09/interval_params_lock.json`. The artifact's `basis.interval` block records `kind: conformal`, the half-width, the calibration folds and the source file; a locked artifact whose `basis.interval.kind` is not `conformal` is not the pre-registered one.

**Base document §4 and Amendment 1 Change 3** (the multiplier `[point × 0.4986, point × 1.6392]`, "nominal 95%, realised 0.922") are superseded for the 2026-27 set. The S2 gate reads the conformal interval's coverage against the same band. The multiplier's coverage on the 2025 fold is reported beside the conformal's in Study C's confirmation table, as a control, not as a gate.

## Change 2 — No stat-specific secondary arm is carried by the lock

**The rule, applied** (`stat_translation_summary.json::pooled`, folds 2020–2024, 547 counting / 508 rate rows; Δ = MAE(PIR pipeline) − MAE(stat's own factor), paired cluster bootstrap):

| stat | Δ [95% CI] | raw p | Holm (13 tests) | block collapsed in a fold | rule |
|---|---:|---:|---|---|---|
| fouls | +0.328 [+0.251, +0.406] | < 0.001 | yes | yes (4 of 5 folds) | **refused** — τ > 0 clause |
| ft_attempted | +0.048 [+0.028, +0.068] | < 0.001 | yes | no | selected |
| ast_to | +0.012 [+0.002, +0.023] | 0.020 | no | no | selected |
| points | −0.055 [−0.103, −0.006] | 0.028 | no | yes | PIR pipeline better |
| defensive_rebounds | −0.102 [−0.151, −0.052] | < 0.001 | yes | no | PIR pipeline better |
| the other eight | CI covers zero | — | no | — | null |

(`secondary_arm_candidates` = `["ast_to", "ft_attempted"]`.)

**Decision: neither selected stat is projected by the 2026-27 lock.** This is a scope decision, stated as one, not a re-reading of the rule:

1. No committed generator produces a stat projection for a signings list. The rule was written to *select*; building, testing and pre-registering a projection arm for two stats before the lock is new code two weeks out, and a "secondary arm" named in an amendment with no generator is the METHOD.md §16 failure this program was written to avoid.
2. The gains are small in the unit a reader can use: 4% of the MAE for free-throw attempts, 2% for assist-to-turnover, on stats for which no projection is published or scored by any gate.
3. AST/TO passes the raw-CI clause and fails Holm across the 13 tests; on its own it is the weakest of the three.

The two candidates are recorded here for a post-season follow-up. Any secondary arm for 2026-27 would need its own amendment with a generator, tests and a power line; none is planned before the lock, and Amendment 9, if written, does not open that door for a stat whose name is not in the table above.

## Change 3 — What Study B found, for the record (motivation, not a rule)

* **League difficulty is a profile, not one number.** The league × stat factor table's additive (rank-one) share is 0.344 against a within-league permutation null of mean 0.115, 95th percentile 0.156 (`rank_one.additive_share_full`, `.permutation_null_share`). On reliable cells the per-cell estimate predicts the other half better (0.056) than the additive fit (0.086) or the tier mean (0.071).
* **Where the cells are thin, the tier mean wins** (0.071 against per-cell 0.117 and additive 0.093 on the 30 thin cells of 200). That is the shipped pooling's fallback. Cross-stat borrowing does not beat it, so ATI-2960 (deferred by Amendment 6) receives no support from this study.
* **For points and defensive rebounds the PIR pipeline beats the stat's own factor** with the CI excluding zero. Per-stat cells are noisier than PIR's, not more informative; the profile finding does not translate into prediction for the two stats that matter most.
* **Fouls is the one stat the pipeline gets wrong.** Its own factor beats the PIR pipeline by 0.33 on an MAE of 1.03, and B0 (no translation) beats the PIR pipeline too (1.09 against 1.34): fouls do not shrink when a player moves up, and applying PIR's factor to them is worse than doing nothing. The rule refused it (its EuroLeague block collapsed in four of five folds), and the refusal stands. It is the finding to carry into the paper, with the refusal beside it.

## Change 4 — Sequence from here, and what the rehearsal may and may not do

1. This amendment is committed. Then, and only then: `scripts/calibrate_prediction_intervals.py --confirm-2025` and `scripts/validate_stat_translation.py --confirm-2025` score the 2025 fold once each, with the families and arms fixed above.
2. `scripts/build_translation_predictions.py --season 2025 --interval-params …/interval_params_rehearsal_through_2024.json` builds the rehearsal set (status `draft`); the evaluator runs on it at `--as-of 2026-01-31` and `2026-06-30`, on the full predicted set and on the primary population (`--first-round-max 3 --full-outcomes …/realised_outcomes_2025.json`).
3. The power line is already committed (`power_rehearsal_2025.json`, `scripts/restate_prediction_power.py --n 88 --n 66`): P1 power 0.80 at the 88 predicted, 0.68 at the 66 in the primary population. A miss on P2/S1 at this n is the season being too small to adjudicate, exactly as the base document reads a 2026-27 PARTIAL.
4. The rehearsal's verdict changes nothing in this amendment or any earlier one. A defect it exposes in the *pipeline* (a crash, a join, a censor count) is fixed and recorded; a number it returns is reported.

---

## Provenance

| Item | Where it is fixed |
|---|---|
| selection table, negative controls | `scripts/calibrate_prediction_intervals.py` → `docs/research/artifacts/prelock-program-2026-09/intervals_summary.json` (`pooled_selection_folds`, `selection`, `negative_controls`); note `docs/research/prediction-intervals-conformal-2026-09.md` |
| lock and rehearsal parameters | `--lock-calibration [--calibrate-through 2024]` → `interval_params_lock.json`, `interval_params_rehearsal_through_2024.json` (`q_hat`, `n_cal`, `calibration_folds`) |
| interval construction in the artifact | `src/data/translation_predictions.py::IntervalSpec`; `scripts/build_translation_predictions.py --interval-params`; test `test_a_conformal_interval_spec_gives_every_row_the_same_half_width` |
| Study B table | `scripts/validate_stat_translation.py` → `stat_translation_summary.json` (`pooled.<stat>`, `secondary_arm_candidates`, `rank_one`); note `docs/research/stat-specific-translation-2026-09.md` |
| power at the rehearsal n | `scripts/restate_prediction_power.py` → `power_rehearsal_2025.json` |
| evaluator population filter | `scripts/evaluate_translation_predictions.py --first-round-max --full-outcomes` |
