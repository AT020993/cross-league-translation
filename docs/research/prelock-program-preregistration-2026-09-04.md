# PRE-REGISTRATION — the pre-lock research program: dress rehearsal on 2025-26, stat-specific translation, conformal intervals, evidence synthesis

**Date: 2026-09-04. Decided by Amir 2026-09-04 ("do all these 4 ideas"). Tickets: ATI-2961 (A), ATI-2962 (B), ATI-2963 (C), ATI-2964 (D), parent ATI-2788, science lane. Status: pre-registered before any of the four generators exists; every rule below is fixed before the first run.** Base pre-registration: `preregistration-2026-27-predictions.md` and Amendments 1–7. Lock deadline **22 September 2026** (Amendment 7). Written per `docs/research/METHOD.md` §1, §7, §8, §13, §16.

## The rule the whole program lives under

**2025 (= the 2025-26 season) is the rehearsal season. It is excluded from every *selection* step, not only every *fit*.** Which interval family, which stats get a secondary arm, which pooling structure — chosen on walk-forward folds with destination season **≤ 2024**. The 2025 fold then confirms, once. The chosen thing is recalibrated on ≤ 2025 for the 2026-27 lock, exactly as `K_LAG` is. If the 2025 fold informed a choice, the rehearsal would be a re-score of a decision it helped make.

**The rehearsal's verdict changes no 2026-27 rule** (§8). Amendment 8 — which interval family and which secondary arms the 2026-27 lock carries — is written and committed **before** the rehearsal's evaluator runs. Sequence, enforced by commit order: Study C and Study B on ≤ 2024 folds → Amendment 8 → Study A's evaluator → lock.

Every new gate ships with a negative control at an impossible threshold (§8 corollary); every quoted number with a committed generator and a test (§16). Refused, and written here so nobody proposes it later: re-estimating factors or `K_LAG` on 2025 outcomes; using the rehearsal to tune anything; tree-based quantile models (uninterpretable, and 18 days); scoring the 28 September EuroCup gap record.

## Specification

| Choice | This program | Alternatives considered |
|---|---|---|
| **Unit** | Study A: one 2025-26 import (signing); B and C: one walk-forward test row (player × destination season), clusters = destination club-season; D: one walk-forward season | pair-level only (rejected — the pipeline's refusals, censoring and interval are what the lock exercises, and no pair-level study runs them) |
| **Estimator, gates, bars** | unchanged: `build_league_factors.py` (Amendment 6 constants), `K_LAG` strictly-prior median, G-gates and P/S criteria as committed | — |
| **Shared code change** | `validate_translation_walkforward.py --rows-out <path>` writes every fold's test rows with every arm's prediction, the multiplier, `k_lag`, reliability flag, source games and the cluster; B, C and D read that file, never a re-implementation | each study refitting its own folds (rejected — three fits that can drift apart) |
| **Selection folds / confirmation fold / lock calibration** | ≤ 2024 / 2025 / ≤ 2025 | — |

---

## Study A — Dress rehearsal on 2025-26: the locked pipeline, end to end, on realised outcomes

**Question.** Run the exact pipeline the lock will run — roster-diff collector → prediction builder with refusals → evaluator with censoring, gates and interval coverage — on the 2025-26 imports, with everything fitted on seasons ≤ 2024, and score it on the league's own 2025-26 box scores. What does it return?

**Generators (new).** `scripts/build_realised_outcomes.py --season 2025 [--as-of YYYY-MM-DD]`: reads `data/raw/{euroleague,eurocup}/2025/boxscores` and `games` metadata (`Date`, `Round`), keys players by person code (box-score `Player_ID` = `"P" + code`, stripped of the prefix and padding; one test pins a known pair), and writes one row per person: `person_code`, `games`, `minutes`, `club_season` (largest-minutes club), `pir_per36` (EFF from components, the corpus definition), the per-36 counting stats Study B needs, and `first_round` (first appearance). `--as-of` counts only games dated on or before it. The collector (`--season 2025 --collected-at <date>`), the builder (`--season 2025`) and the evaluator are the committed ones, unchanged.

**Population.** A 2025-26 roster fetched today is the end-of-season roster; the lock's is preseason. **Primary population: imports whose `first_round` ≤ 3.** Full roster as sensitivity; the midseason share is stated. Known and accepted: R9 refuses 2024 source seasons in leagues whose field shrank (france-pro-a 2024 reads 240 of a 306 maximum), by the floor's own design (Amendment 5 Change 1).

**Reads (all reported; none gates the lock).** The evaluator's own output at `--as-of 2026-01-31` (mid-season) and `2026-06-30` (end): P1 (beats B0 by the margin, paired CI), P2 (beats the oracle constant B1b), S1 (beats RTM), S2 (coverage in [0.90, 0.98]), R8 censoring counts at ≥ 5 / ≥ 8 / ≥ 15 games, `by_source_season_lag`, verdict. Beside it: the same reads restricted to the primary population.

**Threats, named now.** T-A1 end-of-season roster (handled by `first_round`). T-A2 the 2025 fold is already the walk-forward's last window at pair level — this is not new evidence about the *factors*, it is evidence about the *pipeline*; the note says so. T-A3 name join: the builder joins signings to corpus rows by `pairing_key`; unmatched imports are refused R-codes and counted, never silently dropped. T-A4 EuroCup 2025-26 destination completeness on the API side is asserted (Amendment 5 table), not assumed.

**Power.** The rehearsal n is whatever the 2025 collection yields; the P1 power is read off the Amendment 5 table at that n **before** the evaluator runs and printed in the note. At n ≈ 110 it is 0.88; at 50, 0.56. A miss at low n is "the season could not adjudicate", exactly as the base document reads a 2026-27 PARTIAL.

## Study B — Stat-specific translation: is league difficulty one number or a profile?

**Question.** Do per-stat translation factors beat the PIR factor applied uniformly, stat by stat, out of sample? And is the league × stat factor table well described by a rank-one structure — one "league difficulty" number plus one "stat sensitivity" number — or is translation genuinely stat-specific?

**Two families, pre-registered separately.** Both sides of the corpus carry `points, offensive_rebounds, defensive_rebounds, assists, steals, blocks, turnovers, fouls, ft_attempted, fg3_attempted, fg3_made, fg_attempted, fg_made` (read from the merged corpus columns 2026-09-04).

* **Counting family (per-36, multiplicative — the shipped estimator unchanged):** points, offensive rebounds, defensive rebounds, assists, steals, blocks, turnovers, fouls, free-throw attempts. Nine factor tables via `STATS`, each with its own T9 (τ > 0 per block) read, because steal and block cells will be thin.
* **Rate family (additive on a link scale, same walk-forward):** true-shooting percentage `PTS / (2·(FGA + 0.44·FTA))` on the logit scale; three-point attempt rate `3PA / FGA` on the logit scale; assist-to-turnover ratio on the log scale; free-throw rate `FTA / FGA` on the log scale. A rate factor is the exposure-weighted mean *difference* on the link scale (the same cluster bootstrap, the same pooling), and the prediction is the inverse link. Rates below a pre-registered denominator floor (FGA ≥ 50 in the source season) are excluded from the fit; the count excluded is printed.

**Arms per stat, on the walk-forward rows.** (i) per-stat factor; (ii) the PIR factor applied uniformly; (iii) B0, the untranslated source rate. Reads: MAE and paired cluster-bootstrap Δ(ii − i) with 95% CI; R² against the reliability ceiling per stat; per-fold and pooled over folds ≤ 2024, then the 2025 fold once.

**The rank-one test (B2).** Fit `log f[league, stat] = α[league] + β[stat] + ε` by weighted least squares (weights = pair counts) on the reliable cells of the counting family; compare leave-one-cell-out prediction error of (a) the additive model, (b) the per-cell estimate, (c) the destination tier mean. If (a) beats (b) on thin cells, "league difficulty" is one number and thin cells can borrow across stats; if (b) beats (a), translation is stat-specific and the profile claim is the finding. The interaction share `1 − SS_resid/SS_total` is reported with a permutation null (stats relabelled within league, 500 draws).

**Selection rule for a 2026-27 secondary arm (Amendment 8).** A stat gets a secondary projection arm iff, on folds ≤ 2024 pooled, the per-stat factor beats the uniform-PIR factor with the paired CI excluding zero **and** every block's τ > 0 in every fold. Everything else is reported and not projected.

**Threats.** T-B1 multiplicity: nine counting stats plus four rates plus B2 is fourteen reads; every CI is reported raw and a Holm-adjusted flag beside it. T-B2 thin cells and τ = 0 (T9 per stat). T-B3 per-36 counting stats depend on minutes; a role change moves them independently of league — the usage-corrected sensitivity of the base document (`--usage-cut`) is run once per family. T-B4 rate denominators: a rate on 12 attempts is noise; the floor above, with its excluded count printed. **Power:** per-stat cells share the pairs of the PIR table, so the per-cell reliability floor is the PIR one; the rate family's floor is stated from split-half reliability at the corpus's median FGA per season before any read.

## Study C — Conformal prediction intervals, calibrated on out-of-sample residuals

**Question.** Which interval family gives the published coverage at the narrowest width, judged by a proper scoring rule, on residuals the model never fitted?

**Finding to state first.** The current interval is `[point × 0.4986, point × 1.6392]`. A multiplicative interval scales with the point, so a low projection carries a narrow interval by construction — the smallest 2026-27 projection (8.86) carries [4.42, 14.52] while a projection near zero would carry a near-empty interval. No 2026-27 row is below 3 PIR/36 today (0 of 50), so this is a structural defect, not a live one; it is why every candidate below scores *absolute* or *normalised* residuals, never relative ones.

**Candidates, all calibrated rolling: fold s uses residuals from folds < s only, so evaluation starts at 2022.**

1. **Multiplier interval** as committed (the control).
2. **Split conformal, absolute:** score `|y − ŷ|`; interval `ŷ ± q̂` with `q̂` the finite-sample-corrected `(1−α)` quantile of calibration scores (`⌈(n+1)(1−α)⌉/n`).
3. **Split conformal, normalised:** score `|y − ŷ| / σ̂(x)`, `σ̂(x) = exp(c₀ + c₁·ŷ + c₂·log(games_src))` fitted by least squares on log absolute residuals of the calibration folds; interval `ŷ ± q̂·σ̂(x)`.
4. **Conformalised quantile regression (CQR):** linear quantile regression (`statsmodels.QuantReg`) of `y` on `[ŷ, log games_src, factor_reliable]` at α/2 and 1−α/2 on the calibration folds, then the CQR correction `q̂` on the conformity scores `max(q̂_lo − y, y − q̂_hi)`.

α = 0.05 throughout; the publication label stays "nominal 95%, realised X" (Amendment 1 Change 3). Exchangeability across seasons is the assumption; season drift is the threat, so coverage is reported per fold, and the weighted-conformal variant (weights ∝ recency) is a sensitivity, not a candidate.

**Metrics.** Coverage, mean width, and the **Winkler interval score** `W = (u − l) + (2/α)·(l − y)·1[y < l] + (2/α)·(y − u)·1[y > u]` per fold and pooled. **Selection rule (Amendment 8):** the family with the lowest pooled Winkler score on folds ≤ 2024 among families whose pooled coverage sits inside the committed [0.90, 0.98] band. Ties within one pooled-bootstrap SE keep the simpler family (order 1 < 2 < 3 < 4). The 2025 fold is then scored once with the selected family, and the family is recalibrated on folds ≤ 2025 for the lock.

**Negative controls.** A family calibrated with α = 0.5 must fail the band; a family fed residuals from the *training* rows must over-cover relative to the honest calibration (the leak signature). Both printed.

**Power.** Coverage SE at pooled n ≈ 440 rows (folds 2022–2024) is about 0.011 at 0.95, so families within ±0.02 coverage are not separable on coverage — that is why the Winkler score, not coverage, selects.

## Study D — Evidence synthesis across seasons, and the pre-registered forecast for 2026-27

**Question.** Across the walk-forward seasons, what is the pooled effect of per-league translation over each baseline, how heterogeneous is it between seasons, and what does the model predict the 2026-27 season will show?

**Generator (new).** `scripts/synthesize_translation_evidence.py` reads the walk-forward rows and, per season, computes Δ MAE (B0 − per-league; one-global − per-league; RTM − RTM+league) with the paired cluster-bootstrap SE, then pools with a **random-effects model estimated by REML with the Hartung-Knapp-Sidik-Jonkman adjustment** (k = 6 seasons; DerSimonian-Laird beside it as the sensitivity). It reports the pooled effect with its HKSJ CI, τ² and I², and the **95% prediction interval for a new season** — that interval, committed before tip-off, is the forecast for what 2026-27 will return. The 2026-27 checkpoint result is later added as the seventh season, never as a replacement.

**Threats.** T-D1 seasons share training data (fold s trains on everything before s), so the between-season estimates are not independent — stated, and the pooled CI is read as descriptive of the walk-forward, not as an independent-replications CI. T-D2 k = 6 makes τ² poorly identified; the prediction interval is wide by construction and is reported as such. **Negative control:** feeding six zero effects with their SEs must return a pooled effect whose CI covers zero and a prediction interval that covers zero. **Power:** with k = 6 the HKSJ CI is the honest one; the number of seasons needed to halve the prediction-interval width is printed.

**What Study D licenses.** A sentence of the form: "over six held-out seasons the per-league model beat the untranslated baseline by X MAE (HKSJ 95% CI [..]); a new season is expected to fall in [..]." The 2026-27 result is then a point inside or outside a pre-registered interval, which is a stronger test than a single-season pass/fail.

---

## Sequence and what each study may not do

| Order | Step | May not |
|---|---|---|
| 1 | this document + four tickets | — |
| 2 | walk-forward `--rows-out`; outcomes builder + tests | change any arm |
| 3 | Study C on folds ≤ 2024 | read the 2025 fold |
| 4 | Study B on folds ≤ 2024 | read the 2025 fold; add a stat not listed above |
| 5 | Study D | — |
| 6 | **Amendment 8**: interval family and secondary arms for 2026-27, by 15 September | be written after step 7 |
| 7 | Study A: collection, build, evaluator on 2025-26 | inform any 2026-27 rule |
| 8 | lock, 22 September (Amendment 7) | — |

## Scripts

* `scripts/validate_translation_walkforward.py` — `--rows-out` (to be added, step 2).
* `scripts/build_realised_outcomes.py` — Study A (to be written, step 2).
* `scripts/validate_stat_translation.py` — Study B (to be written, step 4).
* `scripts/calibrate_prediction_intervals.py` — Study C (to be written, step 3).
* `scripts/synthesize_translation_evidence.py` — Study D (to be written, step 5).
* Each ships with tests under `tests/test_scripts/` and writes its summary JSON under `docs/research/artifacts/prelock-program-2026-09/`; the result notes are rendered from those artifacts.
