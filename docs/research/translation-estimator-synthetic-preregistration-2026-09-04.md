# PRE-REGISTRATION — synthetic-data validation of the league translation estimator, with a committed generator

**Date: 2026-09-04. Ticket: ATI-2890. Status: committed BEFORE the generator's first full run.** The study this ticket asks for was run once already, on 2026-08-17, from a session script: its results are the constants `MEASURED_NULL` and `INTERVAL_CALIBRATION` in `scripts/build_league_factors.py`, the ATI-2904 change that replaced `differs_from_parity`, and a Linear comment. Neither the script nor its artifact (`translation_factor_audit.json`, untracked at the repo root on 2026-08-26) exists on disk today. Under METHOD.md §16 those constants are therefore cited, not re-derivable. This document fixes, before the run, what the committed generator will compute, on which corpus, and what counts as reconciling with the 2026-08-17 record.

## Specification

| Choice | This pre-registration | Alternatives considered |
|---|---|---|
| **Question** | Under a generative model calibrated to the corpus in force, does the shipped estimator (a) recover an injected league effect, (b) invent one under the null, (c) drift under a known quota confound, and (d) pool thin cells appropriately — and do (a)–(d) reproduce the 2026-08-17 record? | re-implementing the estimator inside the simulator (rejected by the ticket: "do not build a parallel estimator to test against") |
| **Estimator under test** | `scripts.build_league_factors.estimate_table` called on a synthetic pair table with the same 51-column schema `build_pairs` emits, with the module's `STATS` narrowed to `pir` and `ERAS` to `all` for the run (module globals, patched in the harness, printed); `partial_pool`, `cluster_bootstrap`, `ESTIMATORS` and `excludes_measured_null` reached through it. **Invariant:** the harness run on the real pairs must reproduce `league_factors.parquet` (pir / all / all_pairs) to 0.0 on `factor`, `se` and `ci_lo` before any synthetic study is scored | — |
| **Corpus shape template** | the API-side pairs on disk (`data/processed/translation/league_factor_pairs.parquet`, 4,074 pairs, poland-plk excluded — Amendment 5 Change 2): per (source, destination) cell, the real rows' `games_src`, `games_dest`, `minutes_src`, `minutes_dest`, `cluster`, `club_src` are resampled with replacement to the cell's real n. The 2026-08-17 study used the 14-league Proballers corpus; the Proballers-side pairs (`data/processed/translation_proballers_2026-08-21/league_factor_pairs.parquet`, 5,039) are run as a **second template** so the recorded constants are checked on the corpus they were measured on | ticket's stated shape (2,174 pairs, "144 down to 10", corr 0.464) — stale, from the pre-ATI-2826 Proballers corpus; re-derived from the artifact instead |
| **Generative model** (additive on the rate scale — the 2026-08-17 record found raw PIR/36 near-Gaussian, skew +0.15, and log PIR/36 skewed −1.3, so a log-scale generator would assume away the bias it is meant to find; re-measured here: skew +0.18 / −1.73) | per pair *i* in cell (*L*, *D*) with club-season cluster *c*: true rate `a_i ~ N(μ, σ_a²)`, truncated at 2 PIR/36; source observation `x_i = a_i + N(0, σ_g² / games_src_i)`; destination observation `y_i = f_LD · a_i · (1 + N(0, σ_r²)) + u_c + N(0, σ_g² / games_dest_i)`, `u_c ~ N(0, σ_u²)`; totals `pir = rate × minutes / 36` on each side so the ratio-of-sums estimator is well defined. `σ_g²` from the destination split-half reliability the holdout already measures (Spearman-Brown inverted to one game); `σ_a²` from `var(x)`; `σ_r²` and `σ_u²` solved from `corr(x, y)` and the between-cluster share of the residual. **Calibration is printed as a table of five moments, target vs simulated at f = the corpus mean ratio, and the run refuses if any moment is off by more than 5%** | log-normal rates (rejected, above); minutes-scaled noise instead of games-scaled (games is the unit the reliability was measured in) |
| **Studies** | **S2** null (`f = 1` everywhere); **S1** recovery at `f ∈ {0.70, 0.75, 0.80, 0.85, 0.90, 0.96}` and at the real pooled table as a heterogeneous truth (ordering recovery); **S3** quota: a share `q` of one league's players hold a domestic rate inflated by `(1 + δ)` above merit while their destination rate follows merit, `δ ∈ {0, 0.02, 0.05, 0.07, 0.10, 0.15, 0.20}`, `q = 0.45` (59 of 130 in the spec's Israeli split), at the Israeli cell's real n; **S4** pooling: ten cells per destination with true factors `N(tier mean, τ = 0.04)`, n per cell swept over `{10, 25, 50, 75, 100, 150, 250}`, plus the collapse study: the real-shaped block with one extra cell at `n ∈ {2, 3, 5, 7, 10, 20}` | — |
| **Replicates** | 200 for S2, 50 per grid point elsewhere, 100 for the collapse study; cluster bootstrap at 300 draws per cell (the estimator's default is 2,000; one S2 replicate set is re-run at 2,000 and the coverage difference printed — the record says ≤ 0.01) | — |
| **Seeds** | one master seed (0); every replicate derives its own `numpy` generator; the estimator's own per-cell seeding (`cell_seed`) is left untouched | — |
| **Reads** | per cell and pooled: bias `mean(factor_raw − f)`, RMSE, 95% cluster-bootstrap CI coverage of `f`, share within one SE; the same for `factor` (pooled); `excludes_measured_null` and a parity comparison (`ci` excludes 1.0) rejection rates under the null; τ̂ vs τ; shrinkage fraction; `P(|error| > 0.03)` and `> 0.05`; reliable-flag FPR/FNR at thresholds `{50, 75, 100, 150, 250}` against ±0.03 and ±0.05; `P(τ̂ = 0)` in the collapse study, under the shipped `partial_pool` and under the S4-comment alternative (τ² from floor-clearing cells only, every cell then shrunk) | — |

## Predictions, written down now (from the 2026-08-17 record; each is a reconciliation target, not a bar)

**P1 (S2).** The exposure-weighted primary is biased **up** under the null, `mean_of_ratios` more so, `ratio_of_sums` not: recorded 1.0181 / 1.0231 / 0.9998. Reconciled if the re-derived primary null lies in **[1.010, 1.030]** on the Proballers template and the sign pattern across the three estimators is the same. The bias is **flat in n** (recorded: 10 to 500): reconciled if the primary's null bias at n = 500 is within 0.005 of its value at n = 50.

**P2 (S2, decomposition).** Removing source-side noise removes most of the bias (recorded 88% noisy-denominator, 12% Jensen). Reconciled if the source-noise-off run cuts the primary's null bias by at least half. The noise-free run must return `f` exactly (harness negative control, asserted).

**P3 (S1).** RMSE falls as `n^{-1/2}` (recorded 0.075 at n = 10 → 0.019 at n = 500) and is insensitive to `f` across 0.70–0.96; 95% coverage is below nominal and **worsens** with n (recorded 0.86 pooled, 0.73 at n = 500). Reconciled if pooled coverage is in [0.80, 0.92] and coverage at n = 500 is lower than at n = 50.

**P4 (S1, ordering).** With the real pooled table as truth, the Spearman correlation between true and estimated factors within a destination exceeds 0.9 in the median replicate — the property the operating envelope rests on ("trustworthy for ranking").

**P5 (S3).** Quota contamination biases the factor **down** (the league looks harder to leave than it is); recorded −0.030 at the Israeli magnitude, slope about −0.36 per unit δ, near-linear. Reconciled if the slope is in [−0.5, −0.25].

**P6 (S4).** Pooling does not over-borrow: τ̂ within 0.01 of 0.04; shrinkage above 50% at n ≤ 10 and below 10% at n ≥ 250; thin cells' pooled RMSE below their raw RMSE. ±0.03 on the raw factor needs n ≥ 62 (recorded); the reliable flag at 75 does not separate trustworthy from untrustworthy against ±0.03 (recorded FPR 0.23 / FNR 0.47) — reconciled if FPR at 75 is above 0.15 against ±0.03 and below 0.10 against ±0.05.

**P7 (S4, collapse — new, not in the record).** One cell at n ≤ 5 in a real-shaped block drives `P(τ̂ = 0)` above 0.5 under the shipped pooler; the floor-clearing-cells alternative brings it below 0.1 on the same draws. **No change to the estimator is made in this branch whatever P7 returns** (METHOD.md §8): the finding is routed to a follow-up ticket with the numbers.

## Threats and the control for each

| # | Threat | Control |
|---|---|---|
| T1 | **The simulator validates its own assumptions.** Recovery under a model built to be recoverable proves little | Stated as the scope boundary in every output; the real-data placebo the repo already runs (`report_league_factors.py`, one competition split in two, truth 1.000) is printed beside S2 as the out-of-model check |
| T2 | **Harness ≠ estimator.** A simulator that re-implements the estimator tests the re-implementation | Invariant above: real pairs through the harness reproduce the shipped table to 0.0; the harness has no estimator code of its own |
| T3 | **Calibration drift.** A model that misses the corpus's moments answers a different question | five-moment table, target vs simulated, refuse at > 5% |
| T4 | **Generator scale.** A log-scale generator hides the ratio bias | additive on the rate scale; skew of rate and log-rate printed |
| T5 | **Seed luck.** One seed, one story | replicate counts above; every summary carries its Monte-Carlo SE |
| T6 | **Bootstrap depth.** 300 draws vs the estimator's 2,000 | one S2 set at 2,000, difference printed |
| T7 | **Truncation.** `a_i` truncated at 2 PIR/36 changes the mean | share truncated printed; below 1% or the truncation point is lowered and reported |
| T8 | **Corpus.** Two templates, two answers | both run; constants in code stay as they are until Amir reads both records |
| T9 | **Runtime shortcuts.** Narrowing `STATS`/`ERAS` might change a code path | the invariant in T2 runs through the same narrowed loops |

## Gates shown to fail

The harness asserts that a noise-free run returns `f` to 1e-9, that an injected `f = 0.8` is not reported as 1.0, and that the calibration check rejects a deliberately mis-scaled `σ_g` (an impossible tolerance) — METHOD.md §8 corollary.

## What may not change after the run

The predictions, thresholds and reconciliation bands above. The estimator (`build_league_factors.py`) is not edited in this branch; a recommendation from S4 becomes a follow-up ticket. `MEASURED_NULL` and `INTERVAL_CALIBRATION` are not edited in this branch; the note reports both records beside the constants and the decision to re-pin is Amir's.

## Scripts (committed in the same branch, after this file)

* `scripts/simulate_translation_estimator.py` — calibration, the four studies, the collapse study, the harness invariant and negative controls; writes `docs/research/artifacts/translation-estimator-synthetic-2026-09-04/summary.json` (one file per template) and renders the result note `translation-estimator-synthetic-validation-2026-09-04.md` from that JSON, so no number in the note is typed.
* `tests/test_scripts/test_simulate_translation_estimator.py` — the generator's moment calibration on a toy template, the noise-free recovery, the quota injection's direction, the collapse alternative's behaviour, and the note renderer's refusal to render a missing key.
