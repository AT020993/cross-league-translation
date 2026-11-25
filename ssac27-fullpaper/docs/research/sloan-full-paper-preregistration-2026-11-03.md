# Pre-registration — SSAC27 full paper: robustness, decision value and a 2026-27 frozen test

**Approval record.**

| | |
|---|---|
| Approved by | Amir |
| Date | 2026-11-03 |
| Basis | approved as written, before any implementation; nothing below may be relaxed after a result is seen (METHOD.md §8) |

This file is committed and pushed **alone**, before any implementation of the analyses it describes. The push timestamp of that commit is the record. Paper: *What Does League Translation Add? A Benchmark for European Basketball Forecasts*, SSAC27 Submission 47, abstract advanced 31 Oct 2026, full paper due 1 Dec 2026.

## Why this exists, in plain words

The submitted abstract found that translation factors cut forecast error by 5.2% against a forecast that knows only the player's history, but add nothing detectable once the forecast already knows which leagues the player is moving between. The full paper must turn that into something a club can use, and must answer the obvious objections: one recipe, one crude outcome, a EuroCup-heavy sample, six seasons, outcomes already seen, and no decision-level meaning. Each analysis below answers one of those.

## What has already been seen (exposure disclosure)

* **Destination seasons 2017–2025 are exposed.** Every v10 table was computed on them. All analyses on those seasons (E1–E9) are **exploratory**. The paper will say so.
* **Values I computed while planning (3 Nov), from exposed data:** the reproduction of v10 (below), the scorable size of an earlier window (2019 adds 138 forecasts; 2018 and 2017 cannot be scored), and the standard deviation of per-forecast paired error differences used in the power section. No new model, recipe, outcome or decision metric was computed.
* **Destination season 2026 (2026-27) is unexposed.** For planning I read only column names, row counts and game-date ranges of the 2026-27 EuroLeague/EuroCup files (EuroLeague 90 games to 30 Oct, EuroCup 80 games to 28 Oct). No player statistic from 2026-27 has been read. P1 is the only confirmatory analysis in this document.

## Reproduction gate (runs first; everything else depends on it)

The public companion `github.com/AT020993/cross-league-translation`, folder `ssac27-v10/data/`, holds the v10 inputs. Their sha256 equal those recorded in `docs/research/artifacts/sloan-v10-2026-09-20/analysis-manifest.json`:

| File | sha256 |
|---|---|
| `cohort.parquet` (identical in all four pools) | `c629f43e3194642d483701c3d07666252938d587e747c99dbb031a2346bf2abf` |
| `official_corrected/pairs.parquet` (pool A) | `d964727924630dbf32c1764daf1e536c81d58988218a230fea591c62c1a62f58` |
| `verified_same_club_full/pairs.parquet` (pool B) | `85ba5c9125e164c8eb7918c62680b969ff2f168bb2059cd3343bfecd10e5204d` |
| `overlap_keys_full/pairs.parquet` (pool C) | `80fa11a25642650783f38b7771147f311bc2d1f64deb7477d5037e324212a841` |
| `same_club/pairs.parquet` (pool D) | `43b1dca8192b6aaeed78a5b8c254853b528656a514f25d7fce96b55fb5f67881` |

**G0.** From these inputs, committed code must reproduce, on the 674 v10 target keys, every original-arm MAE and every cell-slope-arm MAE of pool A's reference scenario to absolute 1e-9 against `v10_summary.json`, and the history-only vs history+translation player/club-season interval to 1e-9. A planning run on 3 Nov met this at the 6-decimal level shown in the abstract verifier; the gate formalises it. **If G0 fails, nothing else runs.**

## Specification

| Choice | This pre-registration | Alternative printed (not selectable) |
|---|---|---|
| **Unit** | one forecast = player × destination season, one retained continental destination (EuroLeague or EuroCup), selection rules exactly as v10 (largest-minutes source and destination aggregates, ≥ 8 games both sides, no qualifying previous-season continental appearance, Poland excluded as source) | — |
| **Population** | **Anchor:** the 674 v10 target keys, destination seasons 2020–2025. **Extended (E5):** the same rules for 2019–2025, 812 forecasts. **Prospective (P1):** destination season 2026 under the same rules, data lock below | anchor and extended are always both printed |
| **Estimator** | paired mean absolute error difference, d̄ = mean(|e_without| − |e_with|); positive favours the second-named model. Forecast families exactly as v10: history H = (1, x, h, a); + destination intercept and slope; + penalised source offsets (λ = 1, 10, 100); + penalised cell slopes; each with and without the translated feature z | absolute MAE levels, RMSE, median and 90th-percentile error, printed beside every increment |
| **Null** | d̄ = 0 for each paired contrast | a margin statement: the 95% upper bound of a gain expressed as a % of the parent model's MAE |
| **Filter** | the v10 eligibility rules; 674 / 812 / P1 targets fixed before scoring; an unscorable target makes the comparison inconclusive, never silently dropped | complete-source-league subset (P1); EuroLeague-only and EuroCup-only (E4) |
| **Key** | `player_name` × `season_dest`; scoring partitions are destination competition × destination season | — |
| **Uncertainty** | v10's two-way clustered interval (player and recorded destination club-season; Student t with min(G)−1 df), and the player × destination-season alternative; intervals condition on fitted forecasts | cluster bootstrap over destination club-seasons, 2,000 draws, seed 0, for ratios and decision metrics |

**Primary penalty.** λ = 10 is the primary source-offset and cell-slope penalty everywhere, as in v10. λ = 1 and 100 are always printed and never selected.

## Analyses

Each analysis states its primary quantity, what result licenses which sentence, and its threat controls. "Exploratory" applies to E1–E9.

### E1. Head-to-head: is a league-aware model without translation as good as translation?

* **Primary.** C_H = MAE(history + translation) − MAE(source offsets λ10, no translation), on the 674. Positive favours the league-aware model.
* **Secondary.** Recovered share S = [MAE(history) − MAE(source offsets λ10)] / [MAE(history) − MAE(history + translation)], with a cluster-bootstrap percentile interval. S ≥ 1 means league context alone recovers all of translation's gain over history.
* **Licenses.** Interval of C_H above zero: "the league-aware model is more accurate than history plus translation". Interval spanning zero with point ≥ 0: "matches translation's gain without the translation step", plus the S interval. Interval below zero: the paper's positive headline is not supported and is withdrawn.

### E2. More than one translation recipe

Six recipes, each producing z through the same lag correction and cutoff rules as v10. Only the factor estimator or pooling changes:

| Code | Factor estimator | Pooling within destination |
|---|---|---|
| R1 | exposure-weighted mean of ratios (v10) | moment estimator (v10) |
| R2 | ratio of sums (the NHLe / MLE-style aggregate ratio) | moment estimator |
| R3 | unweighted mean of ratios | moment estimator |
| R4 | exposure-weighted | none (raw cell factor above the 75-pair floor, destination mean otherwise) |
| R5 | exposure-weighted | floor-clearing τ² (the 2026-09-29 fit's pooler) |
| R6 | one factor per destination (no league-pair cells) | — |

* **Primary.** For each recipe, the source-offset λ10 increment (offsets vs offsets + z_R) on the 674, pool A. Holm adjustment across the six recipes for the family claim "some recipe adds accuracy beyond the league-aware model".
* **Printed for every recipe.** The full ladder (history, destination slope, offsets λ1/10/100, cell slopes λ1/10/100), both cluster specifications, absolute MAEs, support/fallback counts.
* **Licenses.** No Holm-adjusted increment above zero, and every recipe's upper bound below 2% of its parent MAE: "none of six standard recipes adds more than 2% accuracy once the forecast knows both leagues". A recipe with an adjusted interval above zero is reported as the paper's most important qualification.
* **Margin disclosure.** The 2% margin was chosen on 3 Nov after the R1 (v10) intervals had been seen. For R1 the margin statement is therefore descriptive. For R2–R6, all new outcomes (E3) and P1 it is pre-specified.

### E3. Other outcomes

The whole pipeline (pairs, factors, lag, history, regressions) is rebuilt for each outcome, from the same aggregates:

| Code | Outcome per player-season | Formula |
|---|---|---|
| O1 | EFF/36 (v10) | 36 × EFF / minutes |
| O2 | points/36 | 36 × PTS / minutes |
| O3 | Game Score/36 (Hollinger) | 36 × (PTS + 0.4 FGM − 0.7 FGA − 0.4 (FTA − FTM) + 0.7 OREB + 0.3 DREB + STL + 0.7 AST + 0.7 BLK − 0.4 PF − TOV) / minutes |
| O4 | EFF per 100 on-court possessions | 100 × EFF / (team possessions × minutes / (team minutes / 5)) |

Official PIR is **not** computable: the aggregates carry no fouls drawn or blocks against. History h for O2–O4 is rebuilt from the corpus by the same rule as v10's `prior_mean_pir36`. **Gate G3:** the rebuilt O1 history must equal the cohort's `prior_mean_pir36` on all 1,371 rows (absolute 1e-9), or E3 is not run.

* **Primary.** For each outcome: (a) the history vs history + translation gain, and (b) the source-offset λ10 increment, on the 674. Every effect is also printed as a % of the parent MAE and in outcome SD units, so outcomes are compared on one scale (METHOD.md §12).
* **Licenses.** "The pattern holds on k of 3 other outcomes", where a holding pattern means (a) interval above zero and (b) upper bound below 2% of the parent MAE.

### E4. EuroLeague and EuroCup separately

The ladder and E1 are run for each destination separately (194 EuroLeague, 480 EuroCup on the anchor; 218 / 594 on the extended window), with both interval specifications. A two-sided test of the destination difference in the λ10 increment is printed. Small EuroLeague samples get a power line, not a "no effect" verdict.

### E5. Seven seasons instead of six

* The full ladder, E1 and E2-R1 on 2019–2025 (812 forecasts; 2019 has 138, of which 60.1% use fallback factors at the v10 rules). 2017 and 2018 cannot be scored: no training rows for 2017, and a rank-deficient design for 2018 (139 training rows).
* Per-season direction counts for every primary contrast.
* Leave-one-evaluation-season-out ranges for every primary contrast (not confidence intervals).
* The anchor (674) remains the reference. The extended window is reported as a robustness check.

### E5b. Age-aware baseline

Age at the destination season's 1 October, from first-party birthdates, enters every baseline as (age − 26) and (age − 26)², unpenalised. The E1 and λ10 increments are repeated. **Gate:** if birthdates cover fewer than 95% of the 674 targets, E5b is reported as not adjudicable, with the coverage count.

### E6. How much error is even reducible (outcome-reliability ceiling)

From per-game EuroLeague/EuroCup box scores, split each target's destination games into odd and even appearances in date order. Compute the split-half correlation of EFF/36 (and O2–O4) across the 674, Spearman-Brown it to full-season length, and derive the noise floor: the MAE a forecaster who knew each player's true rate would still incur. The floor is computed under a normal noise model and by direct half-vs-half simulation, and both are printed. Every MAE and gain in the paper is then stated as "X of a reducible Y". **Gate:** half-season game counts are reconciled to the cohort's `games_dest` for every target, with exceptions listed.

### E7. Decision terms

Pools are destination competition × season (12 on the anchor). Models compared: history, history + translation, offsets λ10, offsets λ10 + translation.

* **D1, pairwise ordering accuracy.** Over all within-pool player pairs with unequal outcomes: the share ordered correctly by the forecast. Contrasts: history + translation vs offsets λ10, and offsets λ10 vs offsets λ10 + translation.
* **D2, what translation changes.** For offsets λ10 vs offsets λ10 + translation: the share of within-pool pairs whose predicted order flips, and, among flipped pairs, the share where the translation model is right (null 0.5). **This is the primary decision metric:** "adding translation changes X% of head-to-head comparisons and is right on Y% of those".
* **D3, shortlist overlap.** Top-5 and top-10 per pool: Jaccard overlap between with/without-translation models and between history + translation and offsets λ10 (no outcome needed). The mean realised outcome of each top-k is printed descriptively, with a power line, because the September shortlist study found this read not separable at this n.
* **Uncertainty.** Cluster bootstrap over destination club-seasons within pool, 2,000 draws, seed 0.
* **Reference.** Split-half (E6) pairwise ordering accuracy, as the ceiling for D1.

### E8. Calibrated forecast intervals for the recommended model

Split-conformal intervals on absolute residuals for offsets λ10 and for history + translation. For season s, calibration uses scored residuals of anchor seasons < s only, so evaluation covers 2021–2025. Nominal 80% and 95%. Printed: empirical coverage (cluster-bootstrap CI), mean width, and Winkler (interval) score, by destination and pooled. This is a descriptive property of the recommended model. There is no accept/reject bar, because the operating product's intervals are governed separately (combined-arm pre-registration, 2026-10-16) and are untouched.

### E9. A league adjustment table a club can use

Fit offsets λ10 (no translation) on all scorable training rows through destination season 2025. Report, per source league × destination, the forecast destination EFF/36 for a player with source EFF/36 = 16 and history = 16, with a cluster-bootstrap interval (destination club-seasons, 2,000 draws).

* **Tiers, by this rule fixed now.** Sort leagues by point estimate within destination. Start a tier at the top league. Add the next league to the current tier unless the bootstrap share of draws in which the tier's top league exceeds it is ≥ 0.90; otherwise start a new tier.
* **Reporting.** Tiers, not ranks. Adjacent leagues inside a tier are explicitly described as not distinguishable.

### P1. 2026-27 frozen-forecast test (confirmatory, unexposed)

* **Freeze.** Models are trained on destination seasons ≤ 2025 and factors on pairs ≤ 2025, with the v10 code path for recipe R1 and the four primary arms (history; history + translation; offsets λ10; offsets λ10 + translation), plus the full ladder. Forecasts are produced for **every** 2025-26 domestic player-season on disk with ≥ 8 games and positive minutes (Poland excluded), for **both** destinations. They do not depend on who later qualifies. The forecast file, its sha256 and the generating commit are committed and pushed **before any 2026-27 player statistic is read**, no later than **10 Nov 2026**. If the freeze is late, P1 is reported with the actual freeze time.
* **Source data.** 2025-26 domestic data on disk are complete for Spain ACB, Germany BBL, Greece A1, Italy LBA and Israel BSL. They stop in early January 2026 for Turkey BSL, France Pro A, VTB and Lithuania LKL, because Proballers collection is off (ATI-2956) and no licensed source exists. The source rate is the rate over the games on disk, flagged per row. No collection is attempted.
* **Population at scoring.** Destination season 2026 under the v10 eligibility rules, counting continental games dated **on or before 24 Nov 2026**, from EuroLeague API files refreshed on or after 25 Nov. Their sha256 is recorded.
* **Outcome.** EFF/36 over those games: a partial-season outcome, stated as such. Its expected noise is reported from the E6 split-half at the realised game count.
* **Primary contrasts, directions predicted now.**

| Contrast | Predicted |
|---|---|
| P-a: history vs history + translation | positive (translation helps against a league-blind forecast) |
| P-b: history + translation vs offsets λ10 | ≥ 0 (league-aware at least as good) |
| P-c: offsets λ10 vs offsets λ10 + translation | near 0 |

* **Sensitivity (pre-registered).** The same contrasts restricted to newcomers whose source league is complete-season.
* **Uncertainty.** v10's two-way clustered interval (player, destination club).
* **Minimum n.** If fewer than 60 newcomers qualify, P1 is **not adjudicable** and reported descriptively.
* **Licenses.** P-a, P-b and P-c consistent with the anchor: "the pattern held on unseen 2026-27 forecasts, within this test's power". Any contrast whose interval excludes the anchor's point estimate in the opposite direction: reported prominently as a failure to replicate. **Equivalence is never claimed from P1.**

## Power (from exposed 2020–2025 paired differences; planning only)

Standard deviation of per-forecast paired absolute-error differences on the 674 (pool A):

| Contrast | SD of d_i | Naive SE at n = 674 | 80%-power detectable effect at n = 100 / 150 |
|---|---|---|---|
| history vs history + translation | 1.066 | 0.041 | 0.298 / 0.244 |
| destination slope vs + translation | 0.792 | 0.031 | 0.222 / 0.181 |
| offsets λ10 vs + translation | 0.328 | 0.013 | 0.092 / 0.075 |
| history + translation vs offsets λ10 | 0.522 | 0.020 | 0.146 / 0.119 |
| cell slopes λ10 vs + translation | 0.309 | 0.012 | 0.086 / 0.071 |

**Consequence for P1, stated now.** At the expected 100–150 newcomers, P1 can detect a λ10 increment of about 0.08–0.09 EFF/36, but not a history-vs-translation gain of the anchor's size (0.161). A P1 interval for P-a that spans zero is therefore **"not detectable at this n"**, never a contradiction of the anchor. Partial-season outcomes make these figures optimistic. The realised n and a recomputed detectable effect are printed before any P1 contrast is read.

## Threats and their controls

| Threat | Control (in the same generator) |
|---|---|
| Reused outcomes on 2017–2025 | exploratory label on E1–E9; P1 frozen and pushed before outcomes |
| Garden of forking paths across recipes/outcomes/penalties | every recipe, outcome, penalty and pool printed; λ10 fixed primary; Holm across recipes for the family claim |
| Unpenalised z vs penalised offsets tilts toward translation | stated; it strengthens any null; E2 adds no tuning |
| Changing support across recipes | same 674 targets in every arm; refusals counted, never dropped |
| History rebuild drift (E3) | G3 exact-equality gate |
| Partial-season source rates (P1) | per-row flag; complete-source sensitivity |
| Identity mismatches in P1 joins | the v10 name normaliser and identity rules, with join rates asserted and unmatched names listed |
| Gate that never fails | each new gate has an impossible-threshold negative control (METHOD.md §8) |
| A result contradicting the submitted abstract | reported to Amir **before** any writing; the submitted claim is never silently dropped |

## Scope boundary: nothing pinned changes

Untouched: the frozen v9 files, every `docs/plans/sloan-*` file, `docs/research/artifacts/sloan-v10-*`, `scripts/build_league_factors.py`, `scripts/sloan_v10_slopes.py`, `scripts/sloan_full_refit.py` and every other v10-hashed script, the 12 Sept operating lock and its predictions, and the 26 Sept prospective minutes study. New work imports those modules and adds new dated generators under `scripts/sloan_fullpaper_*.py`. Retained runs go to directories outside the repo via `--research-run`, from committed code.

## Planned generators

| Generator | Analyses |
|---|---|
| `scripts/sloan_fullpaper_common.py` | input loading and hash checks, G0 |
| `scripts/sloan_fullpaper_recipes.py` | E1, E2 |
| `scripts/sloan_fullpaper_robustness.py` | E3, E4, E5, E5b, E6 |
| `scripts/sloan_fullpaper_decisions.py` | E7, E8, E9 |
| `scripts/sloan_fullpaper_prospective.py` | P1 freeze and scoring |
| one committed report script per result note | — |

## Timeline

| Date | Step |
|---|---|
| 3–4 Nov | this pre-registration approved and pushed |
| by 10 Nov | P1 forecasts frozen and pushed; G0 passed |
| by 20 Nov | E1–E9 results notes |
| 25–26 Nov | P1 scored |
| by 1 Dec | full paper submitted |
