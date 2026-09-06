# Retrospective held-out validation of the league translation factors — RESULT

**Ticket:** ATI-2799 · **Date:** 2026-08-17 · **Gate for:** ATI-2891's publish / do-not-publish decision

**Pre-registration:** `holdout-preregistration.md`, saved as an artifact **before** any validation fit
was run and not edited since. Every bar quoted below is from that file as written.

## Verdict: PARTIAL

| | verdict |
|---|---|
| **Arm A — held-out season (2024–25), the primary gate** | **FAIL on G4.** G1, G2, G3 pass; G4 fails |
| **Arm B — leave-one-league-out** | **PASS.** G5 and G6 both met, 10 of 10 leagues |
| **Overall, per the pre-registered verdict rule** | **PARTIAL** |

The factors clear the pre-registered margin against the untranslated baseline B0 decisively and
generalise to leagues never seen in the fit. They **fail G4**, which required beating *both* named
baselines: the model's MAE (3.3325) is 0.005 PIR/36 **worse** than B1b, a baseline that multiplies
last season's rate by a single constant 0.8655. That is a tie, not a loss, but G4 says "beats both"
and the model does not.

**One post-hoc finding is more consequential than the verdict, and it contradicts the ticket's own
premise:** the 22-cell per-league factor table buys **nothing measurable** over a single global
scalar. It is reported in its own section below.

---

## Specification

| Choice | This analysis | Alternatives printed |
|---|---|---|
| **Unit** | one (player, destination season) transfer into EuroLeague/EuroCup, ≥8 games each side | ≥5 and ≥15 destination games (T7) |
| **Population** | consecutive-season "switchers-in": no continental appearance at ≥8 games in season *t* | with incumbents (T4); same-season dual-tier pairs (T1) |
| **Estimator** | exposure-weighted, as shipped | ratio-of-sums, mean-of-ratios (T10) |
| **Factor column** | partially-pooled `factor`, tier-mean fallback where `reliable = False` | raw, ÷1.019 bias-corrected (T12) |
| **Aggregation key** | `player_name + season`; source/destination largest-minutes stint | collision-pruned (T6) |
| **Sample filter** | poland-plk refused entirely (43 rows); non-positive rates dropped (12 rows) | — |
| **Uncertainty** | cluster bootstrap on destination club-season, 4,000 draws, seed 0 | — |

**Reproducibility invariant, printed by the script:** the validation refits factors by importing the
shipped `scripts/build_league_factors.py` and reproduces the saved full re-fit on all 22 PIR/era=all
cells to **max |Δfactor| = 0.0 and max |Δse| = 0.0**. The validation is scoring the same estimator
the project publishes, not a reimplementation of it.

---

## The population, and why it is not the population the factors were fitted on

This is the finding the pre-registration declared in advance rather than discovering afterwards.

| step | rows |
|---|---|
| Consecutive-season source(*t*) → continental(*t+1*) rows | 3,902 |
| of those, already in a continental competition in season *t* (incumbents) | 2,650 |
| **true switchers-in** | **1,252** |
| scored in Arm A (destination season 2024 or 2025, poland-plk refused) | **231** |
| scored in Arm B (all seasons, poland-plk refused) | **1,209** |
| poland-plk rows refused rather than scored | 43 |
| rows dropped for a non-positive per-36 rate on either side | 12 |

**The factors are fitted on same-season dual-tier pairs and scored here on consecutive-season
transfers.** These are different populations, and the difference is not cosmetic: a transfer carries
the selection confound the dual-tier design exists to remove (players move *because* they improved or
declined), plus a year of aging the model cannot see, plus a club and role change. The spec is
explicit that consecutive-season switches are "secondary validation only" and "must never be pooled
into the primary estimate" (§4[1]).

**So the factors are being asked to do something they were not fitted to do — and the price is
measurable.** Threat control T1 scored the identical model on held-out **same-season** pairs:

| population | n | model MAE | model R² | B0 MAE | B0 R² |
|---|---|---|---|---|---|
| same-season dual-tier pairs (the fitted design) | 843 | 2.9433 | +0.3796 | 3.5837 | +0.0998 |
| consecutive-season transfers (what a GM actually asks) | 231 | 3.3325 | +0.3156 | 4.0449 | +0.0175 |

The population change costs **0.39 PIR/36 of MAE and 0.064 of R²** [via: T1]. That is the honest size
of the extrapolation, and it is smaller than one might fear — the factors degrade but do not collapse
when moved off their own design.

---

## Arm A — held-out season: fit ≤2023, score 2024–25

Factors refit on the 4,176 pairs with `season ≤ 2023` (vs 5,039 full), asserted in-script. All 231
scored rows have destination season ≥ 2024.

| predictor | n | MAE | RMSE | R² | mean over-prediction |
|---|---|---|---|---|---|
| **M — translation** | 231 | **3.3325** | 4.2655 | **+0.3156** | +0.9225 |
| B0 — raw source rate, untranslated | 231 | 4.0449 | 5.1108 | +0.0175 | +2.3072 |
| B1a — minutes scaling, **oracle** (given realised destination minutes) | 231 | 4.5422 | 9.4202 | −2.3381 | +0.1260 |
| B1b — minutes scaling, honest (k = 0.8655 fitted on ≤2023) | 231 | 3.3275 | 4.3366 | +0.2926 | −0.0895 |

### The gates, as pre-registered

| gate | bar | measured | verdict |
|---|---|---|---|
| **G1** | model MAE ≤ 0.95 × B0 MAE = 3.8427 | 3.3325 (17.6% better) | **PASS** |
| **G2** | paired cluster-bootstrap CI on the B0 gap excludes 0 | +0.7124, 95% CI [+0.4731, +0.9859], 67 clusters | **PASS** |
| **G3** | R² ≥ 0.20 | +0.3156 | **PASS** |
| **G4** | beats **both** B0 and B1b on MAE **and** R² | R² yes (0.3156 vs 0.2926); MAE **no** (3.3325 vs 3.3275) | **FAIL** |

**G4 is where the honest reading lives.** The model wins on R² and on RMSE, and loses on MAE by
0.005 PIR/36 — a margin the same bootstrap cannot distinguish from zero (ΔMAE −0.0050, 95% CI
[−0.2297, +0.2397]; corrected 2026-09-04, see the ATI-2955 addendum). It is a statistical tie against a one-constant baseline. Under METHOD.md §8 the
bar is not moved to admit it: G4 required "beats", the model does not beat, and G4 fails.

Note also that **B1a, the oracle baseline, is the worst predictor in the table** (R² = −2.34). Giving
a model the player's realised destination minutes and rescaling a per-36 rate by them actively
destroys the prediction — per-36 already normalises minutes, so B1a double-counts the role change. It
is reported because it was pre-registered, and it is a caution against "obvious" corrections.

---

## The finding that contradicts the ticket's premise: per-league resolution buys nothing

*Post-hoc. No gate rests on this section and no bar was changed by it. It exists because G4 failed
against a single-constant baseline, which makes the obvious question — what do 22 factors add over
one number? — unavoidable.*

Four nested predictors, each strictly coarser than the last, all scored on the same 231 rows:

| predictor | parameters | MAE | R² |
|---|---|---|---|
| Raw source rate (B0) | 0 | 4.0449 | +0.0175 |
| Minutes constant (B1b) | 1 | 3.3275 | +0.2926 |
| **One global translation factor** (0.8964, all of Europe) | **1** | **3.3889** | **+0.2705** |
| Two factors, one per destination competition | 2 | 3.4037 | +0.3012 |
| **22 per-league factors — the published model** | **22** | **3.3325** | **+0.3156** |

Paired cluster bootstraps on the MAE the model saves over each:

| comparison | ΔMAE | 95% CI | excludes 0? |
|---|---|---|---|
| model vs **B0** (the pre-registered gate) | **+0.7124** | [+0.4731, +0.9859] | **yes** |
| model vs one global factor | +0.0564 | [−0.1336, +0.2460] | no |
| model vs two per-destination factors | +0.0712 | [−0.0441, +0.1805] | no |
| model vs minutes constant B1b | −0.0050 | [−0.2297, +0.2397] † | no |

**Everything the translation buys out-of-sample on this population is the level shift, and one number
delivers it.** Going from 1 parameter to 22 moves MAE by 0.056 PIR/36 with an interval four times as
wide as the effect [via: P1_nested_predictors].

This contradicts the spec's framing directly. The spec argues per-league factors are the product —
*"He averaged 18 in Turkey" becomes "he projects to ~14.5 in EuroLeague"* — and §4[1] insists factors
be per-league and per-stat because "a single blended factor would hide that." On out-of-sample
transfer prediction, the single blended factor hides nothing that this test can detect.

### But the per-league ORDERING is real, which is exactly what Phase 0 licensed

The two results are compatible, and testing rather than asserting the reconciliation matters. Phase 0's
operating envelope says the estimator is trustworthy for **ranking** source leagues within a
destination, not for levels. If that is right, the fitted ordering should predict the realised
transfer ratio even though its magnitudes are too small to move MAE. It does:

| test | value |
|---|---|
| Spearman ρ, fitted factor vs realised 2024–25 ratio (mean of per-player ratios per cell), pooled within-destination deviations, 16 cells | **+0.644** (asymptotic p = 0.0071) † |
| permutation null, 10,000 draws, permuted within destination | P(ρ_null ≥ observed) = **0.0052**; null 95th pct +0.435; null mean −0.005 † |
| negative control: the same test on pre-permuted realised ratios, 20 draws | mean ρ −0.11, mean permutation p 0.60, 1 of 20 significant at 0.05 † |
| sensitivity to the cell-ratio definition (five definitions) | ρ from +0.635 (ratio of PIR sums) to +0.782 (median), all asymptotic p ≤ 0.008 † |
| EuroCup alone, 9 cells at n ≥ 5 | ρ = +0.583 (p = 0.099), Pearson r = +0.765 (p = 0.016) — *session-derived, no committed generator; not corrected* |
| EuroLeague alone, 7 cells at n ≥ 5 | ρ = +0.643 (p = 0.119), Pearson r = +0.589 (p = 0.164) — *session-derived, no committed generator; not corrected* |

† Corrected 2026-09-04 from the committed generator (ATI-2955 addendum below). The August values
were ρ = +0.688, permutation p = 0.0017, null 95th +0.424, from a session script whose cell-ratio
definition was not recorded.

**The per-league factors carry real, out-of-sample-verified information about which leagues translate
better — they just do not improve a point prediction enough to measure at n = 231** [via: P5,
permutation test, `plot_sloan_abstract_figures.ordering_test`]. That is the precise, defensible claim, and it is narrower than the spec's.

---

## Per source league, Arm A — including the failures

Every league is reported. `n < 20` is the pre-registered floor below which no verdict is issued.

| source league | n | model MAE | model R² | B0 MAE | beats B0 | MAE gain ±SE | detectable at 80% power | verdict |
|---|---|---|---|---|---|---|---|---|
| vtb | 8 | 3.755 | −1.767 | 6.681 | yes | +2.926 ± 0.652 | 1.826 | **no signal available (n < 20)** |
| aba-league | 21 | 3.868 | +0.460 | 5.233 | yes | +1.365 ± 0.490 | 1.371 | beats B0, gain at the floor |
| germany-bbl | 32 | 2.823 | −0.079 | 4.139 | yes | +1.317 ± 0.270 | 0.756 | **beats B0, powered** |
| turkey-bsl | 26 | 3.432 | +0.016 | 4.306 | yes | +0.874 ± 0.371 | 1.040 | beats B0, underpowered |
| france-pro-a | 23 | 3.129 | +0.484 | 3.578 | yes | +0.449 ± 0.331 | 0.928 | beats B0, underpowered |
| spain-acb | 34 | 3.806 | −0.095 | 4.252 | yes | +0.446 ± 0.244 | 0.684 | beats B0, underpowered |
| lithuania-lkl | 17 | 3.689 | −0.279 | 4.091 | yes | +0.402 ± 0.565 | 1.581 | **no signal available (n < 20)** |
| greece-a1 | 19 | 3.313 | +0.550 | 3.680 | yes | +0.367 ± 0.330 | 0.923 | **no signal available (n < 20)** |
| israel-bsl | 21 | 2.203 | +0.835 | 2.416 | yes | +0.213 ± 0.225 | 0.631 | beats B0, underpowered |
| italy-lba | 30 | 3.522 | +0.318 | 3.652 | yes | +0.130 ± 0.181 | 0.506 | beats B0, underpowered |

### Which leagues translate badly, and where there is no signal

* **No signal at all — three leagues:** `vtb` (n = 8), `lithuania-lkl` (n = 17), `greece-a1` (n = 19)
  are below the pre-registered n = 20 floor. No verdict is issued for them. vtb's spectacular
  apparent gain (+2.93 MAE) rests on **eight players** and should not be quoted.
* **`poland-plk` is refused outright**, not scored: 43 rows across both arms. Its euroleague factor
  cell rests on n = 7 pairs.
* **Four leagues have negative R² despite beating B0** — `vtb` (−1.767), `lithuania-lkl` (−0.279),
  `spain-acb` (−0.095), `germany-bbl` (−0.079); of these only spain-acb and germany-bbl clear the
  n = 20 verdict floor. Beating a bad baseline is not the same as explaining variance:
  in these leagues the model reduces average error but does no better than predicting the league's
  mean. `turkey-bsl` (+0.016) is effectively the same case.
* **`italy-lba` and `israel-bsl` translate with the smallest measurable benefit** (+0.130 and +0.213
  MAE). israel-bsl's R² of +0.835 is the highest in the table but on a population whose B0 error was
  already low (2.416) — the model adds almost nothing there.

### Power line — mandatory, per METHOD.md §7

Computed with the repo's own `assert_powered_for_null` and a paired cluster bootstrap.

> **Pooled Arm A: the model beats B0 by 0.712 PIR/36 at n = 231; the smallest gain detectable at 80%
> power on this sample is 0.371, so this result is powered.**
>
> **Per league, only 2 of 10 leagues' observed gains exceed their own detection floor** (germany-bbl,
> and vtb at n = 8 which has no verdict). **Among the 7 leagues that clear the n = 20 verdict floor,
> only 1 is powered.** For the rest: *no detectable effect at the n available; detecting the observed
> gain at 80% power requires* n = 457 (italy-lba), 184 (israel-bsl), 121 (greece-a1), 99
> (france-pro-a), 81 (spain-acb), 37 (turkey-bsl), 22 (aba-league). **The per-league breakdown is
> descriptive; it is not a set of ten independent findings.**

The gate was also shown to fail, per METHOD.md §8's corollary: `assert_powered_for_null` was called
at an impossible target (0.97) and correctly raised, reporting that reaching it would need n ≥ 268
destination games per player. A gate that only ever passes is indistinguishable from one that never
checks.

---

## Arm B — leave-one-league-out: do the factors generalise or memorise?

For each source league, factors were refit with **all of that league's pairs removed**, so the league
has no cell of its own and must fall back to the destination-tier mean. The script asserts the held-out
league has no cell.

| source league | n | held-out MAE | held-out R² | own-factor MAE | own-factor R² | B0 MAE | beats B0 |
|---|---|---|---|---|---|---|---|
| spain-acb | 195 | 3.200 | +0.132 | 3.472 | +0.034 | 3.673 | yes |
| turkey-bsl | 186 | 3.228 | +0.336 | 3.221 | +0.339 | 3.892 | yes |
| italy-lba | 159 | 3.118 | +0.179 | 3.204 | +0.135 | 3.517 | yes |
| germany-bbl | 155 | 3.387 | +0.268 | 3.177 | +0.359 | 4.100 | yes |
| france-pro-a | 131 | 3.104 | +0.280 | 3.117 | +0.271 | 3.388 | yes |
| aba-league | 103 | 3.765 | +0.216 | 3.580 | +0.306 | 4.301 | yes |
| israel-bsl | 80 | 2.769 | +0.534 | 2.723 | +0.557 | 3.609 | yes |
| greece-a1 | 69 | 3.369 | +0.383 | 3.307 | +0.411 | 3.942 | yes |
| lithuania-lkl | 69 | 3.572 | −0.003 | 3.190 | +0.210 | 4.174 | yes |
| vtb | 62 | 3.825 | +0.134 | 3.770 | +0.161 | 4.960 | yes |
| **pooled** | **1,209** | **3.2898** | **+0.2713** | — | — | 3.8693 | **yes** |

| gate | bar | measured | verdict |
|---|---|---|---|
| **G5** | LOLO MAE ≤ 0.95 × B0 MAE = 3.6758 | 3.2898; ΔMAE +0.5795, 95% CI [+0.4825, +0.6799] | **PASS** |
| **G6** | ≥75% of leagues with n ≥ 20 beat B0 | **10 of 10 = 100%** | **PASS** |

**No memorisation.** Every league beats B0 with its own pairs entirely removed from the fit, and for
three of the ten — `spain-acb`, `italy-lba` and `france-pro-a` — the held-out prediction is *better*
on MAE than the own-factor one. That last
detail is the same story as the nested-predictor result seen from the other side: the tier mean —
one number, 0.880 to 0.903 depending on which league was dropped — is doing most of the work, so
removing a league's own factor costs little and can even help by removing a noisy cell.

**Arm A and Arm B are different verdicts and are not averaged.** Arm B is a clean PASS. Arm A fails
one of four gates.

---

## Interval calibration (G7) — reported, not bounded

| interval | coverage | mean half-width |
|---|---|---|
| pre-registered stated 95% (factor SE ⊕ residual SD 3.947) | **0.9221** | ~7.74 PIR/36 |
| factor SE only | **0.0952** | 0.61 PIR/36 |

Both are failures in different directions, and the pre-registration counted over- and under-coverage
equally.

* The stated interval **under-covers modestly (0.922 vs 0.950)**. Phase 0's synthetic study predicted
  ~0.86 from the estimator's own interval behaviour. **The observed 0.922 is better than that
  expectation** — because this interval is dominated by the residual SD, not by the factor SE, so the
  estimator's known interval pathology is largely swamped. Reported as a confirmation-in-direction,
  not a new finding.
* **The interval is too wide to act on.** A ±7.7 PIR/36 band on a quantity whose population SD is
  about 5 spans essentially the whole league. A true 95% interval on this population needs
  ±8.5 PIR/36 (the empirical 95th percentile of |error|).
* **The factor-SE-only interval covers 9.5% of outcomes.** Almost none of a transfer prediction's
  error comes from uncertainty in the factor. Quoting "±0.03 on the factor" as if it bounded a player
  projection overstates the precision by roughly an order of magnitude.

---

## Ceiling — what is attainable, re-measured on the current corpus

Re-measured rather than inherited, per the task instruction.

| quantity | inherited (stale corpus) | **re-measured (current corpus)** |
|---|---|---|
| destination-side split-half r | 0.541 | **0.5373** (n = 5,397 player-league-seasons, mean 9.59 games/arm) |
| Spearman-Brown reliability = max attainable R² | 0.702 | **0.6990** |

The inherited figure reproduces. **R² = 0.699 is the ceiling for any model** of single-season
continental PIR/36; the residual is measurement noise in the outcome, not missing model.

| model | out-of-sample R² | share of the 0.699 ceiling |
|---|---|---|
| Raw source rate (B0) | +0.0175 | 2.5% |
| Minutes constant (B1b) | +0.2926 | 41.9% |
| **Translated model, transfers** | **+0.3156** | **45.1%** |
| Translated model, same-season pairs | +0.3796 | 54.3% |

The prior benchmark of 0.380 out-of-sample R² on the stale corpus is **not reproduced on transfers**
(0.3156) but **is reproduced almost exactly on the same-season population** (0.3796). That is
consistent with the prior benchmark having been measured on the dual-tier pairs rather than on
transfers. The reliability requirement is stated in games: reaching reliability 0.70 needs **20
destination games per player, which only 43 of the 231 scored players have**.

---

## Threat controls — every one pre-registered, every one run

| # | threat | result | changes the verdict? |
|---|---|---|---|
| **T1** | population mismatch | same-season MAE 2.9433 / R² +0.3796 vs transfers 3.3325 / +0.3156 — costs 0.39 MAE | no; quantifies the extrapolation |
| **T2** | temporal leakage | asserted: fit max season 2023, 4,176 < 5,039 pairs, all scored rows ≥ 2024 | no leakage |
| **T3** | player leakage | 77 of 231 scored players also appear in the fit pairs; excluding them: MAE 3.185, R² +0.4135 (vs B0 3.7521 / +0.1808) at n = 154 — **better**, not worse | no |
| **T4** | incumbent contamination | adding 529 incumbents (n = 760): MAE 3.0844, R² +0.3167 vs B0 3.8795 / −0.0337 | no; incumbents are easier |
| **T5** | selection / regression to the mean | above own prior (n = 130): model bias **+2.12**, B0 **+3.75**; below own prior (n = 101): model **−0.62**, B0 +0.45. 35 rows had no prior season | **no, but see below** |
| **T6** | name collision | pruning collision-prone names (n = 77): MAE 3.1577, R² +0.4119 vs B0 3.6064 | no |
| **T7** | survivorship | 273 destination league-seasons at 1–7 games in 2024–25 are invisible to the metric. At ≥15 games (n = 105): MAE 2.9873, R² +0.2665 | no; the ≥5 arm is vacuous, since the population already requires ≥8 |
| **T8** | reliability floor | ceiling 0.699 re-measured; `assert_powered_for_null` run per league; negative control raised at target 0.97 | no |
| **T9** | pooling collapse | τ > 0 in **every** block of **every** refit (full, Arm A, all 10 LOLO refits) — no τ²=0 collapse on PIR | no |
| **T10** | estimator choice | ratio-of-sums 3.3140, mean-of-ratios 3.2873, primary 3.3325. Spread 0.0452 < G1 margin 0.2022 — **not load-bearing** | no |
| **T11** | degenerate denominator | 12 rows with a non-positive rate on either side, excluded | no |
| **T12** | known +0.019 null bias | factors ÷ 1.019: MAE 3.2583, R² +0.3403 — **better**, and G1 still passes. Verdict **not fragile** to the known bias | no |

**T5 is the one control that qualifies the result rather than confirming it.** The model
over-predicts players whose source season beat their own prior seasons by **+2.12 PIR/36** and
under-predicts the others by **−0.62**. B0 is worse on both arms (+3.75, +0.45), so the translation
absorbs about 43% of the selection bias — but it does not remove it. **The residual is
regression-to-the-mean in the source season, which no league factor can correct**, and it is why the
same monotone pattern appears across source-rate quartiles: mean over-prediction runs −1.02, +1.18,
+0.98, **+2.55** from the lowest to the highest quartile. The model's error is largest exactly where
a club's interest is highest — the player coming off a big season.

The same asymmetry shows up by destination: EuroLeague transfers (n = 63) carry a model
over-prediction of **+1.52** against EuroCup's +0.70. The harder destination is the more optimistic
prediction.

---

## Limitations, stated as limitations

Per METHOD.md, these are scope bounds this data cannot discharge, not caveats awaiting a test.

* **No birthdates**, so no aging adjustment (ATI-2766). A transfer spans a year of aging the model
  cannot see; this is a permanent component of Arm A's error and part of why the transfer population
  costs 0.39 MAE against the same-season population.
* **No pace or opponent-strength adjustment** inside the factor.
* **The quota confound is not controlled** in the factors validated here — the estimator's own
  docstring says so. Phase 0 measured its Israeli magnitude at −0.030, larger than that cell's
  bootstrap SE. israel-bsl is a product league, and its factor carries a ~0.03 systematic on top of
  ~0.015 statistical.
* **`differs_from_parity` was not used anywhere in this validation** (Phase 0: false-positive rate
  13–33% against a nominal 5%). It remains descriptive only.
* **poland-plk cannot be validated** — 43 refused rows and a source cell of n = 7.

---

## What this licenses, and what it does not

Phase 0's operating envelope stands; this validation narrows it rather than widening it.

**Supported by this run:**
1. Translated projections beat untranslated production out-of-sample on real transfers by 17.6% of
   MAE, and the gap is bootstrap-separable from zero [via: G1, G2].
2. The factors generalise to a league entirely absent from the fit — 10 of 10 leagues, pooled ΔMAE
   +0.58 [+0.48, +0.68] [via: Arm B].
3. The per-league **ordering** of translation difficulty predicts realised transfer outcomes
   (ρ = +0.644, permutation p = 0.0052; corrected 2026-09-04) [via: P5, ordering_test].
4. Reaching ~45% of the attainable R² ceiling of 0.699 on a single-season, no-aging, no-pace model.

**Not supported:**
1. That per-league factors improve a point projection over a single global scalar. Measured at
   +0.056 MAE, CI [−0.134, +0.246] — **indistinguishable from no improvement.**
2. That translation beats a naive minutes-scaled baseline. It ties (−0.005, CI [−0.236, +0.230]).
3. Any per-league performance claim other than germany-bbl's. Nine of ten leagues are underpowered
   or below the verdict floor.
4. Any published interval read as 95%, and any player-level interval narrower than about ±8 PIR/36.
5. Anything about poland-plk.

## Figures

![What the per-league factors buy]({{artifact:art_20c9e87f-9be7-4437-968f-df52bca08c56}})

**Figure 1.** (a) MAE of five nested predictors on the same 231 held-out transfers, from raw
production through to the published 22-factor table. (b) The MAE each comparator concedes to the
model, with 95% CIs from a paired bootstrap over 67 destination club-season clusters. Only the gap
over B0 — the pre-registered gate — separates from zero.

![Per-league performance and generalisation]({{artifact:art_6710ab90-c250-46c1-b939-9b3681c4c230}})

**Figure 2.** (a) Per-source-league MAE gain over B0 in Arm A, with each league's own 80%-power
detection floor. Leagues marked * are below the pre-registered n = 20 verdict floor and receive no
verdict. (b) Arm B: MAE with the league's own factor, with the league entirely held out of the fit,
and with no translation at all. n is the count of scored transfers per league.

![Ranking validity, calibration and the ceiling]({{artifact:art_7852d614-5e3c-4586-bc56-8d06bd8027bd}})

**Figure 3.** (a) Fitted factor against realised 2024–25 transfer ratio, cells with n ≥ 5; the
ordering is recovered (pooled within-destination ρ = +0.644, permutation p = 0.0052; corrected
2026-09-04) even though the levels do not improve MAE. (b) Mean over-prediction by source-season quartile: both the model and B0
over-predict the best source seasons, the signature of regression to the mean that no league factor
can remove. (c) Out-of-sample R² against the re-measured reliability ceiling of 0.699.

## Verification record

| check | result |
|---|---|
| pre-registration saved as an artifact before any fit | yes — `holdout-preregistration.md`, unedited since |
| validation reproduces the shipped estimator | max |Δfactor| = 0.0, max |Δse| = 0.0 on all 22 PIR/era=all cells |
| corpus invariant | 5,039 dual-tier pairs asserted; PIR 0.0000% null |
| temporal leakage asserted absent | fit max season 2023; all scored rows ≥ 2024 |
| every pre-registered threat T1–T12 run | yes, all printed in `validation_run_log.txt` |
| power gate shown to fail (METHOD.md §8 corollary) | `assert_powered_for_null` raised at target 0.97 |
| numeric literals in this note traceable to computed values | `assert_numbers_traceable` passes |
| range/rank claims recomputed from their sets at time of writing | yes — three prose claims were corrected by that recomputation |
| threshold edited to admit a failing run | **no** |

## Recommendation to ATI-2891

**Publish, with the scope corrected to what was measured.** The gate is PARTIAL, not PASS, and
METHOD.md §8 forbids re-tuning to convert it. But the negative components are specific and
publishable, and two of them are more useful than a clean pass would have been: the per-league table
does not earn its resolution on point prediction, while the per-league *ordering* is real and
externally verified. A prospective pre-registration should therefore predict **rankings and a single
translated level with a ±8 PIR/36 interval**, not 22 per-league point factors quoted to ±0.03.

If ATI-2891 requires a PASS to publish, the answer is that it does not have one.

---

## Addendum 2026-09-04 — three numbers corrected to their committed generators (ATI-2955)

Under METHOD.md §16 every number in this note must come from code committed with it. Three did
not, and two of them change on re-derivation. All three now have a generator, run on the same
Proballers-side corpus this note was measured on (`--continental-source proballers`, 5,039 pairs),
and every other figure in the note reproduced unchanged in the same run.

| quantity | as written (August) | from the committed generator (2026-09-04) | generator / field |
|---|---|---|---|
| G4 tie interval, ΔMAE model vs B1b | −0.0050, 95% CI [−0.2359, +0.2297] | −0.0050, 95% CI **[−0.2297, +0.2397]**, 67 clusters | `validate_translation_holdout.py` → `validation_summary.json: armA_g4_b1b` (paired cluster bootstrap, 4,000 draws, seed 0 — the same procedure as G2) |
| ordering ρ, 16 cells | +0.688, permutation p = 0.0017, null 95th +0.424 | **+0.644**, permutation p = **0.0052**, null 95th +0.435 | `plot_sloan_abstract_figures.py --in-dir <this run>` → `sloan_readback.json: ordering` (mean of per-player ratios per cell; within-destination permutation) |
| ordering ρ, definition sensitivity | — | +0.635 to +0.782 across five definitions, all p ≤ 0.008 | same → `ordering_definition_sensitivity` |
| ordering test, negative control | — | mean permutation p 0.60 on pre-permuted ratios (20 draws); null mean −0.005 | same → `ordering_negative_control`; an in-script assert fails the run if the gate cannot reject |

**What changes and what does not.** The point estimate of the G4 gap is identical; the interval
moves by 0.01 at each end and still spans zero, so G4 stays the tie it was and is not re-scored.
The ordering ρ is 0.044 lower than written and its permutation p three times larger; the claim
the note makes on it — the fitted ordering predicts realised outcomes out of sample — holds at
every one of five cell-ratio definitions, and the August value sits inside that range. The
August ρ came from a session script whose definition was not recorded; none of the five
committed definitions reproduces it, so it is retracted rather than reconciled. The EuroCup-only
and EuroLeague-only rows have no generator either and are left as written but labelled.

## Addendum 2026-09-04 — a second record on the API destination side (Amendment 4)

*The verdict above is the record of the pre-registered gate on the corpus it
was run on and is NOT re-scored (Amendment 4 Change 2; METHOD.md §8).*
`scripts/validate_translation_holdout.py --continental-source proballers`
reproduces it. The same script run with the default `api` destination side —
the corpus the 2026-27 lock uses — is reported as a second, separate record in
`translation-refit-api-destination-2026-09-04.md`.
