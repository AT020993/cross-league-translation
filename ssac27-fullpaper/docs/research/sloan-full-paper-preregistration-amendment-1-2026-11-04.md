# Amendment 1 to the SSAC27 full-paper pre-registration: decision value across leagues, survivorship, skills, a flexible model and a linkage audit

**Approval record.**

| | |
|---|---|
| Amends | `docs/research/sloan-full-paper-preregistration-2026-11-03.md` (approved 2026-11-03, pushed 09:15 UTC) |
| Written | 2026-11-04, after the 4 Nov critical review of the full-paper draft and before any analysis below was implemented |
| Approved by | Amir, "Accept as written", 2026-11-04 |
| Basis | committed and pushed **alone**, before any implementation. Nothing below may be relaxed after a result is seen (METHOD.md §8) |

Everything in the 3 Nov pre-registration stands. This amendment **adds** analyses E10–E17 and a late re-score of the frozen 2026-27 test (P1-late). It changes no registered analysis, threshold, model, population or licence.

## Why this exists, in plain words

The 4 Nov review of the draft found five gaps a Sloan judge is likely to press on:

1. Ranking accuracy barely moves with any league adjustment (E7: 72.1% history-only, 73.3% league-aware). Same-league pairs may dilute the one comparison where league adjustment can matter.
2. The paper does not show *which* leagues' players a league-blind forecast gets wrong.
3. The sample keeps only arrivals who played 8 continental games, so benched signings are missing, and playing time is never forecast.
4. It is not known which box-score skills carry over between leagues, or whether a richer model leaves the conclusion unchanged.
5. The identity linkage behind the 4,074 factor-estimation pairs has no measured error rate.

Each analysis below answers one of these.

## What has already been seen (exposure disclosure)

* **All destination seasons 2017–2025 remain exposed.** E10–E17 are **exploratory**, and the paper will say so.
* **Values seen while writing this amendment (4 Nov), all from files produced under the 3 Nov pre-registration:**
  * E7 pairwise ordering accuracy over all within-pool pairs, and realised top-k outcomes;
  * the e9 full-fit coefficients, including the coefficient on "source season above own history" (−1.39) and the source-rate slope (0.66);
  * arithmetic on those coefficients: the domestic EFF/36 that matches an ACB 16, by league.
* **Not computed or seen:**
  * any cross-league or same-league split of pairs;
  * any per-league signed error;
  * any per-season career-year coefficient;
  * any statistic of arrivals with fewer than 8 continental games;
  * any per-component quantity;
  * any flexible-model fit;
  * any linkage check.
* **Destination season 2026 (2026-27) stays unexposed.** P1 is unchanged. P1-late (below) is registered before any 2026-27 player statistic has been read.

## Specification

| Field | Registered choice |
|---|---|
| **Unit** | As in the 3 Nov pre-registration: one forecast = player × destination season, one continental destination. Exceptions: E13's unit is one factor-estimation pair (player × season, domestic and continental record); E15's same-season part uses the factor-estimation pairs. |
| **Population** | Anchor: the 674 v10 target keys (2020–2025), pool A, recipe R1, unless stated. E14 adds the **all-arrivals** population: v10 rules with the destination game floor lowered to ≥1 appearance with positive minutes. E13 uses the pool-A pairs not present in the verified pool B. |
| **Estimator** | E10: pairwise ordering accuracy on cross-league pairs. E11: mean signed error by source league. E12: the regression coefficient on the above-own-history flag. E13: the share of audited pairs that are wrong matches. E14: the registered paired MAE contrasts on wider populations, plus MAE gains on a playing-time outcome. E15: same-season retention ratios and arrival carry-over correlations per box-score component. E16: paired MAE differences between fixed-hyperparameter flexible models and the λ10 league-aware model. E17: completions of registered tables. |
| **Null** | Zero difference for each paired contrast; ordering accuracy difference = 0; signed error = 0; coefficient = 0; for E13, no null (a rate with an interval). |
| **Filter** | v10 eligibility, except E14's game floor as stated; targets fixed before scoring; unscorable targets are counted, never silently dropped. |
| **Key** | `player_name` × `season_dest`; pools = destination competition × destination season; E13 key = `player_name` × `season` × competition pair. |
| **Uncertainty** | As registered: two-way clustered intervals (player, destination club-season) for MAE contrasts; cluster bootstrap over destination club-seasons, 2,000 draws, seed 0, for ratios, decision metrics, signed errors and coefficients; Wilson 95% interval for the E13 rate. Holm adjustment where a family claim is stated. |

## Analyses

### E10. Does league adjustment help when candidates come from different leagues?

Pools and models are as in E7: destination competition × season; history, history + translation, offsets λ10, offsets λ10 + translation.

* **Pairs.** Within-pool pairs with unequal outcomes are split into **cross-league** pairs (different source leagues) and **same-league** pairs. Both are always printed.
* **Primary.** On cross-league pairs: D1(offsets λ10) − D1(history), the gain in ordering accuracy from knowing the leagues.
* **Secondary.** On cross-league pairs:
  * D1(history + translation) − D1(history);
  * D1(offsets λ10) − D1(history + translation);
  * D2 for offsets λ10 vs offsets λ10 + translation (flip share, and right share among flips, null 0.5).
* **Printed.** The same metrics on same-league pairs. Cross-league and same-league pair counts per pool. The E6 true-rate concordance on each pair type as the ceiling.
* **Licenses.**
  * Primary interval above zero: "between candidates from different leagues, the league-aware forecast orders X% of pairs correctly against Y% for history alone".
  * Interval spanning zero: "league adjustment does not detectably improve cross-league ordering at this n". This is reported in the main text, not the appendix.

### E11. Who gets overrated: signed error by source league

* **Primary.** For each of the 10 source leagues, the mean signed error (forecast − actual EFF/36) of the history-only forecast on the 674, with a cluster-bootstrap interval.
* **Printed beside it.** The same for history + translation and offsets λ10, the number of arrivals per league, and the mean actual and forecast levels.
* **Family claim.** Holm adjustment across the 10 leagues of the history-only bootstrap two-sided p-values.
* **Licenses.**
  * "A league-blind forecast overrates arrivals from L by X EFF/36" (or underrates) only for leagues whose Holm-adjusted p < 0.05.
  * "The league-aware forecast removes that bias" only if the same league's offsets λ10 interval covers zero.
  * Otherwise: "not distinguishable at this n".

### E12. The career-year effect

The coefficient β_a on the flag a = 1[source season above the player's own history] in the offsets λ10 model.

* **Primary.** β_a in the full fit through 2025 (the e9 fit), with a cluster-bootstrap interval (destination club-seasons, 2,000 draws, seed 0).
* **Stability.** β_a in each walk-forward refit used to forecast seasons 2020–2025 (six values). β_a is also printed for the history-only model.
* **Licenses.**
  * Interval below zero **and** the same sign in all six refits: "holding his domestic rate and history fixed, a player signed after a season above his own history is forecast X EFF/36 lower".
  * Otherwise: "the career-year coefficient is not stable enough to report as a finding". It is then described only as a model term.

### E13. Identity-linkage audit

* **Frame.** The pool-A factor-estimation pairs (4,074) whose key is absent from verified pool B (`verified_same_club_full`).
* **Sample.** 100 pairs, simple random sample, `numpy.random.default_rng(20261104)`, drawn by the committed generator **before any record is inspected**. The drawn keys are written to the run output first.
* **Checks per pair**, from raw EuroLeague API and Proballers files:
  * normalised name agreement;
  * birthdate agreement, where both sides carry one;
  * club consistency (the domestic club is the continental club, or a documented mid-season move);
  * schedule feasibility (no domestic and continental games on the same date for different clubs).
* **Classes.**
  * **CONFIRMED:** name agrees, plus birthdate or club agrees, and no contradiction.
  * **WRONG:** a contradicting birthdate, or an infeasible schedule, or a different person shown by club and date records.
  * **UNRESOLVED:** otherwise.

  Rule-based classification runs first. The remaining UNRESOLVED cases are reviewed by hand. Every decision and its evidence is written to a per-pair CSV.
* **Primary.** WRONG share with a Wilson 95% interval. The UNRESOLVED share is always printed.
* **Licenses.**
  * Upper bound below 5%: "at most X% of unverified estimation pairs are identity mismatches".
  * Point estimate ≥ 10%: reported to Amir **before any writing**, as a data-quality finding that touches every factor.

### E14. Survivorship and playing time

* **Rebuild.** The all-arrivals population for destination seasons 2020–2025 uses the documented corpus rebuild path:
  `load_raw` → `_repair_minutes` → TEAM_KEY dedupe → `normalize_games` with the two quarantine scopes → `holdout.build_switchers`.

  The only change is that the destination game floor is lowered to ≥ 1 appearance with positive minutes. Training rows are **unchanged** from v10; only the evaluation population widens.
* **Gate G14.** Rows with ≥ 8 destination games must reproduce the 674 anchor keys exactly, and their `pir_per36_dest` to 1e-9. **Negative control:** the same gate with the floor at 9 must fail.
* **E14a, who is missing.**
  * The count of arrivals with 1–7 continental games, by destination and source league.
  * Their source EFF/36, source minutes per game, and destination minutes and games, against the 674.
* **E14b, wider evaluation populations.** The three registered headline contrasts on the population with ≥ 3 games and ≥ 60 minutes. The contrasts are:
  * history vs history + translation;
  * E1 C_H;
  * offsets λ10 vs offsets λ10 + translation.

  Each is printed unweighted and **minutes-weighted** (weights = destination minutes), with two-way clustered intervals. The ≥ 1-game population is printed minutes-weighted only, as descriptive.
* **E14c, playing-time outcome.**
  * **Outcome.** T = 5 × minutes_dest / team_minutes_dest, the share of a full-time slot, on the all-arrivals population.
  * **Models.** The same ladder (history, + destination, + offsets λ1/10/100) with the source share x_T and, if buildable by the `prior_mean_pir36` rule, a career prior h_T.
  * **Feature added.** The EFF/36 translated feature z, added to each.
  * **Primary.** MAE gain of offsets λ10 over history for T.
  * **Secondary.** The increment of z in the offsets λ10 model for T.
  * **Printed.** The rotation rate (≥ 15 minutes per game and ≥ 8 games) by source league.
* **Licenses.**
  * E14b holds the registered licence pattern on the wider population: "the result is not an artefact of the 8-game rule".
  * Otherwise the failing contrast is reported as the paper's main qualification, and flagged to Amir.
  * E14c primary interval above zero: "knowing the leagues also predicts how much a signing will play".

### E15. Which skills travel

Components per 36 minutes: points, offensive rebounds, defensive rebounds, assists, steals, blocks, turnovers, 3-point attempts, free-throw attempts. Secondary, with attempt floors of ≥ 20 on both sides: 3P%, FT%.

* **E15a, same player, same season.**
  * **Primary.** For each component, the exposure-weighted retention ratio (continental per-36 ÷ domestic per-36) over the pool-A factor-estimation pairs.
  * **Interval.** Cluster bootstrap by player, 2,000 draws, seed 0.
  * **Printed.** By destination competition, and by source league where a league has ≥ 75 pairs.
* **E15b, arrivals.**
  * **Primary.** For each component on the 674: the source–destination correlation, disattenuated by the destination split-half reliability (E6 method applied to the component).
  * **Printed.** The source-rate slope, and the λ10 source-offset spread in component SD units.
* **Licenses.**
  * Two components whose E15a intervals do not overlap: "the same player keeps more of his C1 than his C2 when he faces continental opponents".
  * E15b is descriptive. No single component is called "the" skill that travels unless its disattenuated correlation interval is above every other component's point estimate.

### E16. A flexible model

* **Features.**
  * Source per-36 components (the E15 list);
  * source minutes per game, games and usage;
  * x, h, a;
  * age and age² (E5b ages; an indicator where missing);
  * destination;
  * source league (one-hot);
  * **source-club domestic win share** in the source season, from Proballers game files;
  * with or without the translated feature z.
* **Models, hyperparameters fixed now, no tuning.**
  * (i) `HistGradientBoostingRegressor(loss="absolute_error", learning_rate=0.05, max_iter=300, max_leaf_nodes=15, min_samples_leaf=20, l2_regularization=1.0, early_stopping=False, random_state=0)`;
  * (ii) ridge on standardised versions of the same features, penalty 10 on all non-history terms.
* **Fitting.** Walk-forward exactly as v10: same training rows, refitted for each destination season using earlier seasons only.
* **Gate G16.** Source-club win share must join for ≥ 90% of the 674. Otherwise the club-quality contrast is not adjudicable (coverage printed), and the models run without it.
* **Primary.** MAE(offsets λ10) − MAE(GBM, no z) on the 674, with a two-way clustered interval.
* **Secondary.**
  * GBM no z vs GBM + z (translation increment in a flexible model);
  * ridge-full without vs with club win share (club-quality increment);
  * each model's share of reducible error removed (E6 floor).
* **Licenses.**
  * Primary interval above zero: "a richer model removes X% of avoidable error, against 18.8% for the league-aware model".
  * Interval spanning zero: "a flexible model with N features does no better than one number per league".
  * Translation increment interval spanning zero: the registered E2 sentence extends to "and a flexible model".

### E17. Completions of registered tables (descriptive)

1. E1 C_H and S at λ = 1 and 100, with the registered intervals.
2. Minutes-weighted MAE for the four primary arms, and the three headline contrasts on the 674.
3. Every Table 1 MAE also as a share of reducible error (E6 floor, 2.18).
4. Per source league: number of arrivals in the e9 training rows and in the 674, and number of factor-estimation pairs.
5. The 2% margin and every recipe's upper bound, in EFF/36 and as a share of the history-vs-translation gain.

### P1-late. Re-scoring the frozen 2026-27 forecasts in February

* **Forecasts.** The frozen file `p1_frozen_forecasts.parquet` (sha256 `f3530c1a5ac369c032a996756ced226a93aa2d9f71d2e63aab21694de3d55316`), unchanged.
* **Population and rules.** Exactly P1's, counting continental games dated **on or before 15 Feb 2027**, from files refreshed on or after 16 Feb.
* **Contrasts.** P-a, P-b, P-c, the complete-source sensitivity, the minimum-n rule and the licences, all as in P1.
* **Reporting.** P1 (24 Nov) is the paper's frozen test. P1-late is reported in the conference presentation and the public repository, beside P1, never in place of it. If they disagree, both are shown.

## Gates and negative controls

| Gate | Pass rule | Negative control |
|---|---|---|
| G14 | ≥ 8-game rows reproduce the 674 keys and outcomes to 1e-9 | floor = 9 must fail |
| G16 | club win share joins ≥ 90% of the 674 | a 100% threshold on a deliberately broken join key must fail |
| E13 draw | sampled keys written before inspection; redraw with the seed reproduces them | a different seed must give a different sample |

## Threats and their controls

| Threat | Control |
|---|---|
| Reused 2020–2025 outcomes | exploratory label on E10–E17; P1 and P1-late stay the confirmatory tests |
| Forking paths in new splits | the cross-league/same-league split, the 10 leagues, all components and all models are printed; hyperparameters fixed above |
| Flexible-model tuning | none allowed; one fixed configuration |
| Hand review in E13 | rule-based classes first; hand decisions recorded with evidence per pair |
| A result contradicting a submitted claim | reported to Amir **before** any writing; the submitted claim is never silently dropped |

## Scope boundary

Nothing pinned changes. The v9 and v10 files, the 3 Nov generators and their retained runs, the P1 freeze, and every `docs/plans/sloan-*` file stay untouched. New dated generators:

| Generator | Analyses |
|---|---|
| `scripts/sloan_fullpaper_amend1_decisions.py` | E10, E11, E12, E17 |
| `scripts/sloan_fullpaper_survivorship.py` | E14 |
| `scripts/sloan_fullpaper_skills.py` | E15 |
| `scripts/sloan_fullpaper_flexible.py` | E16 |
| `scripts/sloan_fullpaper_linkage_audit.py` | E13 |
| one committed report script per results note | — |

Retained runs go to `/Users/amir/Projects/cv_basketball_archive/research-runs/sloan-fullpaper/` from committed code.

## Timeline

| Date | Step |
|---|---|
| 4 Nov | this amendment approved and pushed alone |
| by 15 Nov | E10–E17 results notes |
| 25–26 Nov | P1 scored (unchanged) |
| 1 Dec | full paper submitted |
| after 16 Feb 2027 | P1-late scored for the presentation |
