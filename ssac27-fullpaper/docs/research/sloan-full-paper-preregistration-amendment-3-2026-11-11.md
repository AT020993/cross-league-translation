# Amendment 3 to the SSAC27 full-paper pre-registration: forecast level, table stability, forecast gaps, error bands by league and the above-average-season discount

**Approval record.**

| | |
|---|---|
| Amends | `docs/research/sloan-full-paper-preregistration-2026-11-03.md`, as amended on 2026-11-04 (Amendment 1) and 2026-11-05 (Amendment 2) |
| Written | 2026-11-11, after the 11 Nov review of paper v2 and before any analysis below was implemented |
| Approved by | Amir, "Accept as written", 2026-11-11 |
| Basis | committed and pushed **alone**, before any implementation. Nothing below may be relaxed after a result is seen (METHOD.md §8) |

Everything in the 3 Nov pre-registration and in Amendments 1 and 2 stands. This amendment **adds** analyses E18–E23. It changes no registered analysis, threshold, model, population or licence. The frozen 2026-27 test (P1) and its February re-score (P1-late) are unchanged.

## Why this exists, in plain words

The 11 Nov review of paper v2 found six gaps a Sloan judge is likely to press on:

1. Both forecasts expect less than arrivals deliver on average, and the paper does not say so. Figure 4 shows it.
2. The European League Equivalents come from one fit. The paper does not show how much the table moves from one summer to the next.
3. The decision result is small (73.7% against 72.4% of cross-league pairs). The paper does not tell a club how large a forecast gap must be before it can be trusted.
4. The paper reports how often translation changes a ranking and how often the change is right, but not the same two numbers for the league table itself.
5. The paper promises "an error band for every forecast" but checks coverage only overall, by competition and by season.
6. The rule of thumb for an above-average season is a flat discount that starts the moment a player is above his history. The paper does not show whether the discount grows with the size of the jump, or how common such signings are.

Each analysis below answers one of these.

## What has already been seen (exposure disclosure)

* **All destination seasons 2017–2025 remain exposed.** E18–E23 are **exploratory**, and the paper will say so.
* **Values seen on 11 Nov while reviewing the paper**, all computed from the committed public table `e7_keyed_forecasts.csv` or read from committed result files:
  * the mean signed error (forecast − actual EFF/36) on all 674 arrivals: history-only −0.37 (interval −0.74 to −0.02), offsets λ10 −0.47 (−0.80 to −0.15);
  * the same for offsets λ10 by destination (EuroCup −0.65, EuroLeague −0.03) and by season 2020–2025 (+0.01, +0.21, −0.85, −0.58, −0.10, −1.43), and for history-only by season (+0.10, +0.48, −0.87, −0.45, −0.15, −1.24);
  * the registered E11 signed errors by source league, and arithmetic on them (Spain and Italy minus the all-arrival mean: about −0.9 and −1.1);
  * over all within-pool pairs, the share of orderings that offsets λ10 changes against history-only (7.6%) and the share of those changes that are right (57.6%, interval 52.0% to 63.6%);
  * the registered E8 coverage by season (80% bands: 74.0% in 2025);
  * the distribution of **forecast** gaps between paired arrivals under offsets λ10 (no outcome was used): bin counts 4,296 / 4,033 / 3,588 / 2,955 / 4,030 / 3,463 for the bins fixed in E20.
* **Not computed or seen:**
  * any interval for a re-based league bias, or any measure of the spread of league biases;
  * any season-by-season level of continental EFF/36 outside the 674;
  * any league equivalent from a walk-forward refit;
  * any ordering accuracy by forecast gap;
  * any cross-league or same-league split of the league table's ranking changes;
  * any error-band coverage by source league;
  * any coefficient on the size of the jump above history, or any count of flagged arrivals.
* **Destination season 2026 (2026-27) stays unexposed.**

## Specification

| Field | Registered choice |
|---|---|
| Unit | As in the 3 Nov pre-registration: one forecast = player × destination season, one continental destination. E20 and E21 use pairs of forecasts within a pool. E23b's comparison uses domestic player-seasons. |
| Population | Anchor: the 674 v10 target keys (2020–2025), pool A, recipe R1. E19 and E23 also use the e9 training rows (1,059 arrivals, destination seasons 2017–2025) and the six walk-forward training sets (385, 519, 620, 726, 828, 932 arrivals). E22 uses the E8 test seasons 2021–2025 (540 arrivals). |
| Estimator | E18: mean signed error, overall and re-based by source league. E19: the ACB-16 equivalent of each league in each walk-forward refit. E20: share of pairs ordered correctly, by size of the forecast gap. E21: flip share and right share of the league table against history-only. E22: error-band coverage by source league. E23: the coefficient on the size of the jump above history; the share of arrivals flagged. |
| Null | Signed error = 0; re-based league bias = 0; right share = 0.5; coverage = nominal; coefficient = 0; paired MAE difference = 0. E19 and E20 are descriptive and have no null. |
| Filter | v10 eligibility; targets fixed before scoring; unscorable targets are counted, never silently dropped. |
| Key | `player_name` × `season_dest`; pools = destination competition × destination season. |
| Uncertainty | As registered: cluster bootstrap over destination club-seasons, 2,000 draws, seed 0, for signed errors, decision metrics and coefficients; two-way clustered intervals (player, destination club-season) for paired MAE contrasts; Wilson 95% intervals for coverage by league. Holm adjustment where a family claim is stated. |

## Analyses

### E18. The level of the forecasts, and league biases measured against it

Arms: history-only, history + translation, offsets λ10 (the league-aware forecast).

* **E18a, level.** Mean signed error (forecast − actual EFF/36) on all 674, by destination competition and by destination season, with cluster-bootstrap intervals.
* **E18b, re-based league bias.** For each of the 10 source leagues: the league's mean signed error minus the mean signed error of all 674 arrivals, computed inside each bootstrap draw.
  * Primary arm: history-only. Holm adjustment across the 10 leagues.
  * Printed beside it: the same for offsets λ10.
  * **Spread.** S = the arrival-weighted root mean square of the 10 re-based league biases. The contrast is S(history-only) − S(offsets λ10), with a bootstrap interval.
* **E18c, where the under-forecast comes from (descriptive).** By destination competition and season 2017–2025:
  * the mean continental EFF/36 of benchmark arrivals (training rows and targets);
  * the mean continental EFF/36 of all continental player-seasons with at least eight games, from the documented corpus rebuild path used in E14.

  If the second series cannot be built from that path without new inputs, it is dropped and the note says so.
* **Licenses.**
  * E18a interval below zero: "on average the forecast is X EFF/36 below what arrivals delivered", for each arm, in the main text and in Limitations. The by-season and by-competition values are always printed.
  * E18b, Holm-adjusted p < 0.05: "measured against the average arrival, a league-blind forecast underrates (overrates) arrivals from L by X EFF/36". Otherwise: "not distinguishable at this n".
  * Spread contrast interval above zero: "the league table flattens the league pattern". Otherwise that sentence is not used.
  * E18c licenses description only ("the under-forecast is concentrated in …"; "arrivals' continental EFF/36 rose by X between …"). It licenses no statement about cause.
  * The registered E11 numbers stay in the paper as registered; E18b is shown beside them.

### E19. Does the European League Equivalents table hold from one summer to the next?

* **Fits.** The offsets λ10 model in each of the six walk-forward refits used to forecast seasons 2020–2025, and the full fit through 2025. No new model is fitted; these are the registered refits.
* **Quantity.** For every league, destination and fit: the domestic EFF/36 that forecasts like a 16 in Spain's ACB, computed exactly as for the published table. Printed with the number of training arrivals from that league in that fit.
* **Summaries.**
  * Per league and destination: the lowest and highest equivalent across the six refits, and the largest change between consecutive refits.
  * Across leagues: the median and the maximum of those consecutive changes.
  * **Tier check.** Tiers are those of the published table (tier 1: Spain, France, Italy; tier 3: Adriatic, Germany, VTB, Lithuania). For each of the 12 tier-1 × tier-3 league pairs, each destination and each refit (144 comparisons): is the tier-3 equivalent higher than the tier-1 equivalent?
  * A cell whose league has fewer than 10 training arrivals in a refit is flagged. The tier count is printed with and without flagged cells.
* **Licenses.**
  * All comparisons hold: "in every yearly refit, every tier-3 league needed a higher domestic rate than every tier-1 league".
  * Otherwise: "in X of 144 comparisons". No stronger sentence.
  * "From one summer to the next a league's equivalent moved by a median of X (at most Y)" is always printed.
  * The refits share most of their training data, so E19 describes stability. It is not a test and the paper will say so.

### E20. How large a forecast gap can be trusted?

* **Pairs.** Within-pool pairs with unequal outcomes, as in E7 and E10 (22,365 pairs).
* **Gap.** The absolute difference between the two arrivals' forecasts under the arm being scored.
* **Bins, fixed here:** [0, 1), [1, 2), [2, 3), [3, 4), [4, 6) and 6 or more EFF/36. They were chosen from the distribution of forecast gaps alone.
* **Primary.** Under offsets λ10, for each bin: the share of pairs in which the arrival with the higher forecast had the higher realised EFF/36, with a cluster-bootstrap interval.
* **Printed.** The same for history-only and history + translation; the same on cross-league pairs only; pair counts per bin.
* **Figure.** Raw bin shares with intervals. If the shares are not monotone, a pool-adjacent-violators line is drawn over them and the raw shares stay in the table.
* **Licenses.**
  * For every bin, always printed: "when two candidates' forecasts differed by a to b EFF/36, the higher-forecast player turned out better in X% of pairs".
  * "A forecast gap below 1 EFF/36 is not distinguishable from a coin flip" only if that bin's interval includes 50%.
  * "Forecast gaps of at least g were right at least 60% (70%) of the time" names the lowest bin from which every bin's interval lower bound is at or above 60% (70%). If no bin qualifies, the paper says so.
  * The league gap between tier 1 and tier 3 for the same domestic line (about 2 forecast points) may be placed on the figure as a reference mark. It is a description, not a result.

### E21. How often the league table changes a ranking, and how often it is right

* **Metric.** D2 as registered in E7, for history-only against offsets λ10: the share of pairs whose order changes (flip share) and the share of those changes that agree with the realised order (right share, null 0.5).
* **Primary.** Cross-league pairs. **Printed:** all pairs and same-league pairs.
* **Licenses.**
  * Cross-league right-share interval above 50%: "the league table changes X% of cross-league comparisons and is right on Y% of them".
  * Interval including 50%: "the league table's ranking changes are not distinguishable from a coin flip at this n", reported in the main text.
* E21 re-expresses E10's gain (gain = flip share × (2 × right share − 1)). It adds no new evidence and the paper will not present it as such.

### E22. Do the error bands hold for every league?

* **Intervals.** The registered E8 walk-forward conformal bands for offsets λ10, at 80% and 95%, test seasons 2021–2025. No new interval method is fitted.
* **Primary.** Coverage by source league (10 leagues) at 80%, with Wilson 95% intervals and the number of arrivals. **Printed:** the same at 95%.
* **Licenses.**
  * Always printed: "by source league, the 80% bands contained between X% and Y% of arrivals".
  * Every league's interval contains 80%: "no league's coverage was distinguishable from 80% at these sample sizes (n from a to b)". This is a statement about detectability, not about equality.
  * Any league whose interval excludes 80% is named in the main text.
  * The 2025 season's coverage (74.0%) is reported in the text next to the E18a level for that season.

### E23. The above-average-season discount: does it grow with the jump, and how common is it?

* **Jump.** u = max(0, source rate − earlier career rate), in EFF/36, for players with a history. The registered flag a equals 1 exactly when u > 0.
* **Models.** All three are the offsets λ10 model with only the history terms changed. As in the registered model, only the league offsets are penalised.
  * M0: the registered model (flag a).
  * M1: flag a plus u.
  * M2: u without the flag.
* **E23a, primary.** The coefficient on u in M1, full fit through 2025, with a cluster-bootstrap interval, and its value in each of the six walk-forward refits.
* **Printed.** The flag coefficient in M1; the coefficient on u in M2; paired walk-forward MAE contrasts M1 − M0 and M2 − M0 on the 674.
* **E23b, how common.** Among e9 training arrivals with a history: the share with a = 1, with a cluster-bootstrap interval. Comparison: the same share among all domestic player-seasons of the ten leagues that meet the domestic eight-game rule and have a history, in the same source seasons, built with the feature code that produced the frozen P1 file. If that table cannot be built without new inputs, only the arrival share is reported.
* **Licenses.**
  * u coefficient in M1 below zero (interval) **and** the same sign in all six refits: "the discount grows by X EFF/36 for each point above his history", and the rule of thumb is restated with it.
  * Otherwise: "the data do not show the discount growing with the size of the jump", and the rule of thumb stays the registered flag.
  * E23b difference (arrivals − all comparable player-seasons) interval above zero: "X% of signings followed an above-average season, against Y% of all comparable domestic player-seasons". Otherwise only the arrival share is described.
  * **M0 stays the paper's league-aware model whatever E23 shows.** M1 and M2 are never used for the equivalents table, the benchmark or P1. A walk-forward gain for M1 or M2 is reported as exploratory and not adopted.

## Gates and negative controls

| Gate | Pass rule | Negative control |
|---|---|---|
| G18 | the arrival-weighted mean of the registered E11 league errors reproduces the E18a overall mean to 1e-9, for each arm | dropping one league from the average must fail |
| G19 | the full-fit equivalents reproduce `exchange_rate_acb16.csv` to 1e-9, and the per-refit flag coefficients reproduce the six E12 values to 1e-9 | a refit with the season cut moved by one must fail |
| G20 | the bins partition all 22,365 pairs, and accuracy pooled over bins reproduces the registered E7 value for each arm to 1e-12 | dropping one bin must fail |
| G21 | flip share × (2 × right share − 1) equals the registered E10 gain to 1e-12 on each pair type | swapping in the history + translation arm must fail |
| G22 | coverage pooled over leagues reproduces the registered E8 pooled coverage to 1e-12 at both levels | dropping one league must fail |
| G23 | M0 reproduces the e9 full-fit coefficients and the walk-forward MAE on the 674 to 1e-9 | a design without the flag column must fail |

## Threats and their controls

| Threat | Control |
|---|---|
| Reused 2020–2025 outcomes | exploratory label on E18–E23; P1 and P1-late stay the confirmatory tests |
| Values already seen on 11 Nov | listed above; E18a and the all-pairs part of E21 are therefore descriptive, and the paper will not call them tests |
| Forking paths | bins, tiers, arms, models and league families are fixed above; every bin, league, refit and model is printed |
| A new model replacing a registered one | M1 and M2 are sensitivity checks only; M0 stays the league-aware model everywhere |
| A null read as "no effect" | every null licence above is worded as "not distinguishable at this n", with n printed |
| A result contradicting a submitted claim | reported to Amir **before** any writing; the submitted claim is never silently dropped |

## Reporting commitments

* Every analysis above is reported in the paper (main text or appendix) whatever it shows.
* E18a goes in the main text and in Limitations whatever its size.
* If E19 shows a league changing tier between refits, the paper names the league.

## Scope boundary

Nothing pinned changes. The v9 and v10 files, the 3 Nov and Amendment 1 generators and their retained runs, the P1 freeze, and every `docs/plans/sloan-*` file stay untouched. E18–E23 are implemented in new dated generators with one committed report script per results note. Retained runs go to `/Users/amir/Projects/cv_basketball_archive/research-runs/sloan-fullpaper/` from committed code.

## Timeline

| Date | Step |
|---|---|
| 11 Nov | this amendment approved and pushed alone |
| by 18 Nov | E18–E23 results notes |
| 19–20 Nov | paper re-rendered; analysis lock |
| 25–26 Nov | P1 scored (unchanged) |
| 1 Dec | full paper submitted |
