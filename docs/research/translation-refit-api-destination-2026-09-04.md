# The translation basis re-fitted on the EuroLeague API destination side — RESULT

**Date:** 2026-09-04 · **Ticket:** ATI-2957 (executes Amendment 4, decided by Amir 2026-09-03) · **Generators:** `scripts/build_league_factors.py`, `scripts/compare_factor_tables.py`, `scripts/validate_translation_walkforward.py`, `scripts/validate_translation_holdout.py`, `scripts/build_translation_predictions.py`, `scripts/restate_prediction_power.py`, `scripts/plot_sloan_abstract_figures.py`, `scripts/report_league_factors.py` — all with `--continental-source api` (the default since this change).

**Answer.** With the continental side of every pair read from the league's own box scores, the factor table reproduces the Proballers-side table on every reliable cell (max |Δ| 0.026, 19 of 19 within ±0.03), the EuroLeague ordering is unchanged, and the walk-forward, level correction and RTM arms move by amounts inside their own intervals. What the switch actually buys is the thing it was done for: a complete 2025-26 destination season under the walk-forward's last window and under every 2026-27 realised outcome. The 2026-08-17 holdout verdict is **not** re-scored; the same script on this corpus is reported beside it as a second record. The 2026-27 set on the 2026-08-21 collection now refuses 33 of 91 arrivals that reached the source-season rules under R9 (`SOURCE_SEASON_INCOMPLETE`, floor 0.9, Amendment 5).

## Specification

**Question:** Do the translation factors, the walk-forward contrasts and the 2026-27 prediction basis survive replacing the Proballers copy of EuroLeague/EuroCup with the first-party API box scores, and what does the R9 refusal cost the prospective set?

**Unit:** one (player, season) pair with ≥8 games in a Proballers domestic league and ≥8 games in EuroLeague or EuroCup in the same season — the estimator's unit, unchanged; for the validators, one (player, destination season) transfer into a continental competition.

| slot | value | alternative printed |
|---|---|---|
| estimator | `build_league_factors.py` unchanged: exposure-weighted primary, 2,000 cluster-bootstrap draws on (season × destination club), seed 0, `min_pairs` 75, partial pooling to the destination-tier mean | `ratio_of_sums` and `mean_of_ratios` beside it in the artifact, as always |
| null | for the table comparison, the ±0.03 the factors note advertises per reliable cell (a replication tolerance, not a significance test); for the walk-forward, the shuffled-league null the script asserts against | the Proballers cell's own bootstrap SE (cells within 1 SE / 2 SE also printed) |
| sample_filter | destination seasons 2016–2025 (the API holds no 2015-16); every other filter identical to the Proballers-side run | the Proballers-side table includes 2015 — the pair loss is counted |
| key | `pairing_key` on BOTH sides: diacritics stripped, generational suffix dropped, API `LAST, FIRST` reordered | raw Proballers names (`--continental-source proballers`), which reproduces the 2026-08-21 table |
| destination metric | EFF from API components (PTS+REB+AST+STL+BLK − missed FG − missed FT − TOV), the formula the Proballers `pir` column carries | `Valuation` (official PIR) is refused in code; the cross-source check's negative control measured what it does (−0.041) |
| R9 floor | `source_completeness < 0.9`, denominator = max distinct games over 2022–2024 per league; written down in Amendment 5 before the run | the six-league list Amendment 4 names, used only to flag R9 rows that fall outside it |

## Invariants

| check | detail | |
|---|---|---|
| API rows that are not player-games dropped | 134,241 raw → 103,767 player-games (Total, DNP, unparseable minutes); 0 points-reconciliation mismatches (`league_factors_checks.json: continental_side.api`) | ok |
| Proballers-side corpus reproduces | `--continental-source proballers` gives 5,039 pairs, the pinned count; the holdout script asserts it | ok |
| API-side pair count pinned | 4,074 (poland-plk excluded; 4,137 with it), asserted by the holdout script (`EXPECTED_PAIRS["api"]`) | ok |
| pooling did not collapse | `pir` absent from `league_factors_checks.json: pooling.collapsed_stats` (140 collapsed rows, all assists/blocks/points/steals as on the Proballers side); walk-forward folds: `walkforward_summary.json: folds_with_collapsed_block` — see Finding 0 and Finding 2 | ok |
| pairs in seasons the API does not hold | 603 of the Proballers-side pairs have a 2015 destination season (`league_factor_table_deltas.json: n_pairs_only_in_reference_seasons`) | stated |
| the comparison can fail | `compare_factor_tables.py` exits 1 on any reliable cell over tolerance; unit test flips the verdict on tolerance alone | ok |
| R9 fires and stays silent on the right inputs | six parametrised cases incl. AT-the-floor and no-measurement (`test_r9_fires_below_the_floor_and_before_r5`) | ok |

## Finding 0 — one n = 2 cell collapsed the EuroLeague block, and the refused league is excluded from the fit

The first API-side fit returned every EuroLeague PIR cell as `reliable = false` with one identical factor, 0.8518: poland-plk → EuroLeague holds n = 2 pairs on the API side (n = 7 on Proballers) with bootstrap SE 0.212, and τ² = var(factors) − mean(SE²) for the block went to zero (the ATI-2901 mechanism; the source check had predicted exactly this for the 2016–2025 restriction). Without that cell the block's τ is about 0.04 — the same order as the Proballers-side 0.040. poland-plk is refused as a source by the pre-registration (§2, R3), so it is dropped before pairing whenever the destination side is the API (`build_league_factors.API_SIDE_EXCLUDED_SOURCES`, recorded in the checks JSON; Amendment 5 Change 2). The Proballers-side corpus is untouched and still reproduces. The fragility — a below-floor cell deciding the pooling of floor-clearing cells — is an estimator property, recorded on ATI-2955, not changed here.

## Finding 1 — the factor table reproduces cell by cell

`stat=pir, era=all, sample=all_pairs`, Proballers-side (2026-08-21 table, 2015–2025) vs API-side (2016–2025). Δ = API − Proballers. Read from `league_factor_table_deltas.csv`.

| cell | pairs (PB) | pairs (API) | factor (PB) | factor (API) | Δ | Δ / SE(PB) | reliable PB / API |
|---|---:|---:|---:|---:|---:|---:|---|
| spain-acb → eurocup | 420 | 326 | 1.051 | 1.036 | -0.0149 | -1.00 | yes / yes |
| italy-lba → eurocup | 319 | 256 | 0.975 | 0.960 | -0.0150 | -1.06 | yes / yes |
| france-pro-a → eurocup | 253 | 205 | 0.966 | 0.966 | +0.0007 | +0.04 | yes / yes |
| vtb → eurocup | 216 | 142 | 0.963 | 0.937 | -0.0264 | -1.47 | yes / yes |
| greece-a1 → eurocup | 109 | 53 | 0.958 | 0.981 | +0.0229 | +1.27 | yes / no |
| israel-bsl → eurocup | 92 | 77 | 0.952 | 0.965 | +0.0134 | +0.38 | yes / yes |
| turkey-bsl → eurocup | 286 | 221 | 0.949 | 0.940 | -0.0090 | -0.76 | yes / yes |
| germany-bbl → eurocup | 299 | 230 | 0.930 | 0.936 | +0.0063 | +0.44 | yes / yes |
| aba-league → eurocup | 318 | 289 | 0.917 | 0.905 | -0.0122 | -0.68 | yes / yes |
| lithuania-lkl → eurocup | 170 | 148 | 0.899 | 0.892 | -0.0072 | -0.52 | yes / yes |
| poland-plk → eurocup | 76 | — | 0.813 | — | — | — | yes / — |
| spain-acb → euroleague | 566 | 487 | 0.912 | 0.919 | +0.0072 | +0.99 | yes / yes |
| italy-lba → euroleague | 203 | 183 | 0.872 | 0.879 | +0.0073 | +0.47 | yes / yes |
| turkey-bsl → euroleague | 329 | 273 | 0.844 | 0.837 | -0.0068 | -0.70 | yes / yes |
| france-pro-a → euroleague | 187 | 173 | 0.842 | 0.846 | +0.0044 | +0.37 | yes / yes |
| israel-bsl → euroleague | 139 | 113 | 0.829 | 0.833 | +0.0032 | +0.21 | yes / yes |
| poland-plk → euroleague | 7 | — | 0.828 | — | — | — | no / — |
| vtb → euroleague | 221 | 172 | 0.823 | 0.827 | +0.0042 | +0.43 | yes / yes |
| aba-league → euroleague | 210 | 183 | 0.808 | 0.796 | -0.0115 | -0.60 | yes / yes |
| germany-bbl → euroleague | 239 | 211 | 0.803 | 0.812 | +0.0090 | +0.77 | yes / yes |
| greece-a1 → euroleague | 246 | 213 | 0.797 | 0.801 | +0.0047 | +0.37 | yes / yes |
| lithuania-lkl → euroleague | 134 | 119 | 0.787 | 0.795 | +0.0086 | +0.51 | yes / yes |

| | value |
|---|---:|
| reliable cells in both tables | 19 of 22 |
| max / median \|Δ\| over those cells | 0.0264 (vtb → EuroCup) / 0.0073 |
| mean Δ | -0.0018 |
| cells within ±0.03 | **19 of 19** |
| cells within 1 SE / 2 SE of the Proballers cell | 16 / 19 |
| Spearman ρ of the ordering, EuroLeague / EuroCup | 0.952 / 0.883 |
| reliable in one table only | 2 (poland-plk → EuroCup, excluded from the fit; greece-a1 → EuroCup, 109 → 53 pairs, now below the 75-pair floor and served from the tier mean) |
| pairs | 5,039 → 4,074; 603 Proballers-side pairs have a 2015 destination season the API does not hold |

## Finding 2 — walk-forward, level correction and RTM arms

`validate_translation_walkforward.py` (default corpus). Read from `walkforward_summary.json` and `walkforward_per_season.csv`.

Corpus: 4,074 pairs; newcomer cohorts across all seasons 1,371 rows; pooled n = **674** transfers in 201 destination club-season clusters (Proballers side: 719 in 203). No fold collapsed a PIR block (`folds_with_collapsed_block: []`; τ per fold in the table).

| season | n | K | τ EL / EC | per-league MAE | one global MAE | B0 MAE | Δ vs global [95% CI] | separable | beats B0 |
|---|---:|---:|---|---:|---:|---:|---|---|---|
| 2020 | 134 | 0.9477 | 0.053 / 0.040 | 3.3762 | 3.5068 | 4.2269 | +0.1306 [+0.0002, +0.2727] | yes | yes |
| 2021 | 101 | 0.9393 | 0.054 / 0.041 | 2.8728 | 3.1354 | 4.1388 | +0.2625 [+0.1121, +0.4415] | yes | yes |
| 2022 | 106 | 0.9361 | 0.050 / 0.028 | 2.9578 | 3.3428 | 3.3336 | +0.3850 [+0.2161, +0.5495] | yes | **no** |
| 2023 | 102 | 0.9365 | 0.048 / 0.043 | 3.3179 | 3.5403 | 4.0596 | +0.2224 [-0.0114, +0.4681] | **no** | yes |
| 2024 | 104 | 0.9382 | 0.046 / 0.047 | 2.5499 | 2.6491 | 3.7853 | +0.0992 [-0.1115, +0.3533] | **no** | yes |
| 2025 | 127 | 0.9363 | 0.042 / 0.045 | 3.3122 | 3.4684 | 3.7319 | +0.1562 [-0.0025, +0.3142] | **no** | **no** |

Per-league beats one global scalar in **6 of 6** seasons, separable in **3 of 6** (Proballers side: 6 of 6 and 5 of 6). The 2025 window now sits on a complete destination season (n = 127 vs 118) and its own B0 contrast does not separate (`beats_b0: false`) — on the Proballers side that window was scored against a half-season of realised outcomes. The level correction refit strictly prior runs 0.9361–0.9477 (Proballers side 0.9285–0.9368).

Pooled contrasts, paired cluster bootstrap, 4,000 draws, seed 0 (`walkforward_summary.json`):

| contrast | Δ MAE | 95% CI | | Proballers side (2026-08-21 note) |
|---|---:|---|---|---|
| per-league vs B0 | +0.7999 | [+0.6042, +1.0083] | separates | +0.8217 |
| per-league vs one global scalar | +0.2042 | [+0.1274, +0.2799] | separates | +0.2475 [+0.1701, +0.3283] |
| per-league vs RTM (league-free) | +0.0298 | [-0.1017, +0.1526] | **tie** | +0.0157 [−0.1051, +0.1361], tie |
| RTM + per-league vs RTM | +0.1745 | [+0.1087, +0.2408] | separates | +0.2066 [+0.1393, +0.2786] |
| RTM + per-league vs per-league | +0.1447 | [+0.0400, +0.2533] | separates | +0.1909 [+0.0958, +0.2876] |

Pooled R² per arm, read beside its ceiling (`pooled.r2`, `pooled.ceiling`; added 2026-09-04 under ATI-2955 item 1 — the arm's R² had no generator before):

| arm | R² (API side) | R² (Proballers side, 2026-08-21 note) |
|---|---:|---:|
| untranslated (B0) | −0.0366 | −0.0202 |
| one global scalar | +0.2627 | +0.2682 |
| 22 per-league factors | +0.3491 | +0.3597 |
| RTM only, no league identity | +0.3409 | +0.3537 |
| RTM + per-league | +0.4044 | +0.4227 |
| Spearman-Brown ceiling at the scored rows' mean destination exposure | 0.676 (17.8 games) | 0.671 (16.8 games) |

MAE ladder, pooled: B0 3.8865 → one global 3.2908 → per-league 3.0866 → RTM 3.1164 → RTM + per-league 2.9419. Controls: shuffled league→multiplier assignment beats the real Δ in **0 of 200** reps (p95 -0.0154); shuffled mapping inside the refit combined arm reaches the real gain in **0 of 200** (real +0.1745, shuffled p95 +0.0359); with K = 1 the per-league gain is +0.1285 [+0.0403, +0.2176].

**Reading.** Every contrast keeps its sign and its separation status; the point values sit inside the Proballers-side intervals. The decomposition the abstract rests on — league identity ties RTM alone, and only the combination beats each — is unchanged.

## Finding 3 — the holdout script on this corpus, as a second record

*The 2026-08-17 verdict (PARTIAL: G1/G2/G3/G5/G6 pass, G4 ties) is the record of the pre-registered gate and stands. This is the same script on the Amendment-4 corpus, reported beside it. It re-scores nothing.*

`validate_translation_holdout.py` on the API-side corpus (4,074 pairs; internal refit reproduces the saved table to 0.0 on 20 cells). Read from `validation_summary.json`.

| | 2026-08-17 record (Proballers side, pre-registered gate) | 2026-09-04 second record (API side) |
|---|---|---|
| Arm A population (fit ≤ 2023, score 2024–25) | n = 231 | n = 231 |
| model MAE / RMSE / R² | 3.3325 / 4.2655 / +0.3156 | 3.0360 / 3.9827 / +0.3696 |
| B0 MAE / R² | 4.0449 / +0.0175 | 3.7560 / +0.0870 |
| B1b (k = minutes ratio on ≤ 2023 switchers) MAE / R² | 3.3275 / +0.2926, k = 0.8655 | 3.0789 / +0.3271, k = 0.8928 |
| G2: B0 − model MAE [95% CI] | +0.7124 [+0.4731, +0.9859] | +0.7199 [+0.4625, +0.9965] |
| B1b − model MAE [95% CI], paired cluster bootstrap (`armA_g4_b1b`, added 2026-09-04 under ATI-2955) | −0.0050 [−0.2297, +0.2397], 67 clusters | +0.0429 [−0.1331, +0.2224], 66 clusters |
| G1 / G2 / G3 | pass / pass / pass | True / True / True |
| **G4** (beats both B0 and B1b on MAE **and** R²) | **FAIL** — MAE 3.3325 vs 3.3275, a tie | pass — MAE 3.0360 vs 3.0789, R² +0.3696 vs +0.3271 |
| Arm B leave-one-league-out, pooled Δ vs B0 [CI] | +0.5795 [+0.4825, +0.6799], n = 1,209 | +0.6726 [+0.5653, +0.7872], n = 1,371 |
| G5 / G6 (share of leagues n ≥ 20 beating B0) | pass / 10 of 10 | True / 1.000 |
| G7 realised coverage of the stated-95% interval / factor-SE-only | 0.922 / 0.0952 | 0.9351 / 0.1515 |
| reliability ceiling (Spearman-Brown) | 0.699 | 0.7076 |
| script verdict | **PARTIAL** | **PASS** |

**How to read the second column.** The script's verdict on the API-side corpus is PASS: the model's MAE is +0.0429 below the one-constant baseline's where the Proballers-side record had it +0.0050 above. **This does not change the pre-registered verdict.** The gate was run on 2026-08-17 on the corpus that existed then, returned PARTIAL, and the publication branch was decided on that verdict on 2026-08-27 (`preregistration-2026-27-publication-branch-decision-2026-08-27.md`). Amendment 4 Change 2 states that the holdout is not re-scored and the re-fitted numbers are reported beside it; METHOD.md §8 forbids reading a corpus change that turns a tie into a pass as a pass. The honest description is: on the 2024–25 destination seasons as the league's own box scores record them, the per-league model and a single fitted constant sit 0.043 EFF/36 apart on MAE, with the sign the other way from the 2026-08-17 record. The script now computes the paired interval on the model-vs-B1b contrast (ATI-2955 item 3, closed 2026-09-04): **+0.0429, 95% CI [−0.1331, +0.2224]** — it spans zero, so the second record's G4 "pass" is a point comparison that the same bootstrap cannot separate from a tie, exactly as the 2026-08-17 FAIL was a tie the other way. Both records say the same thing at the inferential level: the per-league model and one fitted constant are not separable on MAE at n = 231. The publication carries the pre-registered PARTIAL and may cite this record as what the same script returns on the corpus the lock uses, no more.

Two things did move for a reason worth stating: the Arm A population is n = 231 on both corpora, but not the same 231 — the walk-forward's per-season counts on the same population definition are 113 + 118 (Proballers side, `translation-walkforward-per-league-2026-08-21.md`) against 104 + 127 here (`walkforward_per_season.csv`), so the 2024 window lost nine transfers and the now-complete 2025 window gained nine; and G7's realised coverage rose from 0.922 to 0.935 — the interval multipliers in the prediction schema (0.4986, 1.6392; Amendment 1 Change 3) still carry the 0.922 label, because that is the pre-registered figure and the label is not restated.

## Finding 4 — the 2026-27 set with R9

`build_translation_predictions.py --signings import_signings_2026_both_competitions.json --built-at 2026-09-04` (collection `collected_at: 2026-08-21`; `status: draft` — the pre-lock collection does not exist yet). 88 of 120 arrivals joined a corpus source season through `pairing_key`. `K_LAG` = **0.9367** from 1,371 newcomer-cohort rows in seasons ≤ 2025 (Proballers side: 0.9304). Read from `translation_predictions_2026.json`.

| | count |
|---|---:|
| arrivals in the collection | 120 |
| **predicted** | **50** (40 combined arm, 10 per-league only; 1 on a tier-mean fallback, R6) |
| refused | 70 |
| R1 no prior league in the corpus | 26 |
| R3 refused source (poland-plk) | 3 |
| R5 fewer than 8 source games | 8 |
| **R9 source season incomplete** | **33** |

Predicted, by source league: spain-acb 20, germany-bbl 9, italy-lba 9, israel-bsl 4, greece-a1 4, turkey-bsl 2, lithuania-lkl 2.

R9 by source league-season, with the last game the corpus holds beside it (the discriminator between a collection stop and a league-size artifact of the three-season-maximum denominator):

| source league | season | last game held | completeness | R9 |
|---|---:|---|---:|---:|
| aba-league | 2023 | 2024-04-08 | 0.758 | 2 |
| aba-league | 2025 | 2026-01-05 | 0.429 | 5 |
| france-pro-a | 2024 | 2025-05-17 | 0.784 | 1 |
| france-pro-a | 2025 | 2025-12-26 | 0.356 | 13 |
| germany-bbl | 2024 | 2025-05-11 | 0.889 | 1 |
| lithuania-lkl | 2025 | 2026-01-04 | 0.298 | 3 |
| turkey-bsl | 2025 | 2026-01-03 | 0.433 | 7 |
| vtb | 2025 | 2026-01-08 | 0.392 | 1 |

29 of the 33 R9 rows are 2025-26 seasons of the six leagues Amendment 4 names — collection stops in the first week of January 2026. **4 are not:** DJURISIC, NIKOLA (aba-league 2023, last game 2024-04-08, 0.758); SMART, JAVONTE (aba-league 2023, last game 2024-04-08, 0.758); CALATHES, NICK (france-pro-a 2024, last game 2025-05-17, 0.784); AMAIZE, ROBIN (germany-bbl 2024, last game 2025-05-11, 0.889). Each is a season that ran to its end (last game in April or May) but holds fewer games than the league's three-season maximum because the league was smaller that year. They are R9 under the rule as written and stay so (§8); Amendment 5 Change 1 states this limit of the denominator, and the artifact carries the last-game date so a reader can tell the two cases apart.

Amendment 4 estimated 43 R9 refusals of 94 scorable imports by `prior_league` on this collection; the executed count is 33 because R9 measures the player's *latest qualifying corpus season*, which for a player whose 2025-26 domestic season holds fewer than 8 games in the corpus is an earlier, complete season. **Seven predictions therefore rest on a source season before 2025-26:** SARIC, DARIO (turkey-bsl 2015); ALLMAN, KYLE (turkey-bsl 2024); CANCAR, VLATKO (spain-acb 2018); KREISMONTAS, LUKAS (lithuania-lkl 2024); EVANS, KEENAN (lithuania-lkl 2023); RICHARDSON, ALEXANDER (germany-bbl 2021); GAZZOTTI, GIULIO (italy-lba 2018). The pre-registration's source-season rule (§2: the latest qualifying domestic season) permits this and says nothing about staleness; it is reported here as a limitation and is not changed before the lock. Every row carries `source_season`, so the 24 September set can be read with it.

## Finding 5 — the §7 power table at the R9-reduced count

`restate_prediction_power.py --walkforward walkforward_summary.json --n 50 --n 110` (`power_restated_2026.json`). Method: pooled SE from each contrast's walk-forward CI, scaled by √(n_pooled / n); power at the two-sided 5% bar; n for 80%.

| criterion | field | pooled effect | power at n=50 | power at n=110 | n for 80% |
|---|---|---|---|---|---|
| beat B0 (untranslated source rate) *(primary)* | `pooled.delta_vs_b0` | +0.7999 [+0.6042, +1.0083] | 0.56 | 0.88 | 88 |
| beat one global scalar (nearest committed single-constant comparator; NOT B1b) *(primary (B1b proxy))* | `pooled.delta_vs_global` | +0.2042 [+0.1274, +0.2799] | 0.30 | 0.56 | 192 |
| combined beats B1c (RTM, league-free) *(secondary)* | `rtm_comparator.rtm_plus_league_vs_rtm` | +0.1745 [+0.1087, +0.2408] | 0.29 | 0.55 | 198 |
| combined beats per-league alone *(secondary)* | `rtm_comparator.rtm_plus_league_vs_per_league` | +0.1447 [+0.0400, +0.2533] | 0.11 | 0.19 | 749 |

At the R9-reduced count of 50, **even the B0 criterion is under-powered** (0.56; Amendment 2 had 0.84 at n = 110). The prospective set as it stands on the 2026-08-21 collection can confirm the pooled B0 effect with slightly better than even odds and cannot adjudicate anything else; the walk-forward (n = 674) carries the B1b-proxy and B1c claims. The figure is restated at the pre-lock collection.

## Threats and controls

| threat | control |
|---|---|
| the two sources measure different things | EFF from components on the API side; `Valuation` refused in code; row-by-row reconciliation in `continental-source-check-2026-09-03.md` finding 1 |
| name normalisation, not the source, moves the factors | measured inert on the Proballers-only corpus (≤ 0.0001 per factor, same note); the same key is applied to both sides here |
| a corpus change lets a bar move | no threshold, metric or gate touched; the holdout verdict is not re-scored; the R9 floor was written before the run and is pinned by a test |
| the floor was chosen after seeing the R9 count | Amendment 5 Change 1 dates the floor and tabulates the completeness figures it was chosen on; the R9 count was read afterwards |
| the denominator conflates league size with collection stops | R9 rows outside the six Amendment 4 leagues are printed by the builder and counted in Amendment 5 Change 3 |
| the comparison could not fail | exit-1 verdict, unit-tested to flip on tolerance |

## Limitations

- The API holds no 2015-16; 603 Proballers-side pairs have no counterpart and every era=all cell is now 2016–2025.
- The domestic side is still Proballers, and six domestic 2025-26 seasons remain half-scraped; R9 refuses on them, it does not fill them.
- The second holdout record is on a corpus whose 2025 destination season is complete where the first record's was not; the two Arm A populations therefore differ in n, and that is a difference of corpus, not of model.

## What this licenses

- **Supported:** the 2026-27 lock uses the API-side factor table (`data/processed/predictions/translation_factors_2026.csv`), the API-side `K_LAG`, and R9 at the 0.9 floor.
- **Supported:** every number the abstract quotes from the factors, walk-forward and prediction set is re-read from this run (`docs/plans/sloan-ssac27-abstract-draft.md` §Sources).
- **Not supported:** any change to the ATI-2799 verdict; any claim about the six refused leagues' 2025-26 seasons.

## Scripts

`scripts/build_league_factors.py` (default `--continental-source api`) writes `data/processed/translation/league_factors.parquet` and `league_factors_checks.json`; `scripts/compare_factor_tables.py --reference data/processed/translation_proballers_2026-08-21 --candidate data/processed/translation` writes `league_factor_table_deltas.{json,csv}`; `scripts/validate_translation_walkforward.py` and `scripts/validate_translation_holdout.py` (both default `api`) write their summaries beside them; `scripts/build_translation_predictions.py --signings data/processed/signings/import_signings_2026_both_competitions.json --out data/processed/predictions --built-at 2026-09-04` writes the prediction set and the factor CSV; `scripts/restate_prediction_power.py` writes `power_restated_2026.json`; `scripts/plot_sloan_abstract_figures.py` regenerates `docs/plans/figures/`; `scripts/report_league_factors.py` regenerates the factors note. The Proballers-side artifacts are preserved on disk under `data/processed/translation_proballers_2026-08-21/` (gitignored, like the directory it copies) and reproduce from `--continental-source proballers`.

## Conclusion

Read from the league's own box scores, the destination side reproduces the factor table on all 19 reliable cells within ±0.03 (max 0.026) with the EuroLeague ordering intact [data: `league_factor_table_deltas.json`], once the pre-registered refused league is kept out of a fit whose n = 2 cell would otherwise collapse the block [control: Finding 0]. The walk-forward keeps every contrast's sign and separation on 674 transfers — per-league beats one constant, ties league-free RTM, and only the combination beats each [data: `walkforward_summary.json`]. The same holdout script returns PASS on this corpus where the pre-registered run returned PARTIAL; the pre-registered verdict stands and this is reported beside it, not in place of it [Finding 3]. The 2026-27 set on the 2026-08-21 collection is 50 predictions and 70 refusals, 33 of them R9 at the 0.9 floor written down before the run, which leaves the B0 criterion at 0.56 power [Findings 4, 5]. The out-of-sample ordering test the abstract quotes weakens on this corpus (ρ = +0.562, permutation p = 0.0154, 16 cells; +0.53 to +0.77 across five definitions) and is restated in the abstract at that value.
