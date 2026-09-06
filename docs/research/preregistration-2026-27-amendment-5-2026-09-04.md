# AMENDMENT 5 to the 2026-27 prospective pre-registration — Amendment 4 executed: the R9 floor, the re-fitted basis, and the power table restated

**Date: 2026-09-04. Ticket: ATI-2957 (implements Amendment 4, decided by Amir 2026-09-03). Status: ACCEPTED by Amir on 2026-09-04, recorded on ATI-2891; binding on the lock.** ~~PROPOSED — acceptance pending on ATI-2891.~~ Two things here were not pre-authorised by Amendment 4 and needed Amir's acceptance under the same convention Amendment 3 followed: the numeric R9 floor (Change 1, which the ticket delegated) and the exclusion of poland-plk from the API-side fit (Change 2). Both are accepted as written; no number in this document changed at acceptance. **The artifacts stay `draft`:** acceptance is not the lock, and the pre-lock signings collection does not yet exist (ATI-2917, readiness NOT READY on 2026-09-04). Amendment 6 (`-amendment-6-2026-09-04.md`) records what was decided on the same day and is not part of this acceptance. Base document is `preregistration-2026-27-predictions.md`. Prior amendments: `-amendment-1-2026-08-21.md`, `-amendment-2-2026-08-25.md`, `-amendment-3-2026-09-03.md`, `-amendment-4-2026-09-03.md`. Lock deadline **24 September 2026**, tip-off.

## Specification

| Choice | This amendment | Alternatives considered |
|---|---|---|
| **Scope** | records what Amendment 4 left to execution and did not fix: the numeric floor behind refusal R9, the corpus the prediction basis is now fitted on and what that re-fit produced, and the §7 power table restated at the R9-reduced count | leaving the floor in code only (rejected — a §3 refusal rule with an unrecorded threshold is a threshold nobody can see was set before the count was known) |
| **Evidence admitted** | the games-per-league-season completeness table printed by `scripts/build_translation_predictions.py`; `data/processed/translation/league_factor_table_deltas.json` from `scripts/compare_factor_tables.py`; `walkforward_summary.json` and `validation_summary.json` from the two validators run with `--continental-source api`; `data/processed/predictions/translation_predictions_2026.json` and `power_restated_2026.json` | — |
| **Constraint** | no bar moved, no metric changed, no gate re-scored (`METHOD.md` §8). The floor is a *new* threshold for a *new* refusal code introduced by Amendment 4; it was written into code and this document before the first run that used it, and the run's count was read after | — |
| **Traceability** | every number below names the generator and the field it was read from (`METHOD.md` §13, §16) | — |

---

## Change 1 — The R9 floor is 0.9, written down before the first run

**Definition (Amendment 3 Change 2, unchanged).** `source_completeness` = distinct games the corpus holds for the player's source league-season ÷ the league's **maximum** distinct-game count over seasons 2022, 2023 and 2024. The denominator is printed with every prediction and refusal.

**Rule.** R9 `SOURCE_SEASON_INCOMPLETE` fires when `source_completeness < 0.9`. It is checked before R5. The code constant is `SOURCE_COMPLETENESS_FLOOR` in `src/data/translation_predictions.py`; a test pins the value.

**Why 0.9, measured before the run.** On the corpus as it stood on 2026-09-04, season 2025 (= 2025-26) reads:

| source league | games held 2025 | last game held | complete-season denominator | completeness |
|---|---:|---|---:|---:|
| lithuania-lkl | 59 | 2026-01-04 | 198 | 0.298 |
| france-pro-a | 109 | 2025-12-26 | 306 | 0.356 |
| vtb | 105 | 2026-01-08 | 268 | 0.392 |
| aba-league | 103 | 2026-01-05 | 240 | 0.429 |
| turkey-bsl | 104 | 2026-01-03 | 240 | 0.433 |
| poland-plk | 114 | 2026-01-09 | 240 | 0.475 |
| italy-lba | 224 | 2026-05-10 | 240 | 0.933 |
| israel-bsl | 182 | 2026-05-29 | 192 | 0.948 |
| greece-a1 | 156 | 2026-04-25 | 162 | 0.963 |
| germany-bbl | 306 | 2026-05-10 | 306 | 1.000 |
| spain-acb | 306 | 2026-05-31 | 306 | 1.000 |

The six leagues whose collection stopped in the first week of January 2026 sit at 0.30–0.48; every league scraped through May sits at 0.93–1.00. Any floor between 0.48 and 0.93 separates them; 0.9 is taken because it is the round value nearest the complete side, so a league that is *nearly* complete is not refused by a hair. (Table read from the `R9 floor` block the builder prints; the same figures are in `basis.source_completeness.complete_season_games_by_league` of the prediction artifact.)

**What the floor does NOT discriminate, stated now.** The denominator is a three-season maximum, so a season that was complete but *smaller* also reads below 1: france-pro-a 2024 holds 240 of a 306 maximum (0.78) because the league went from 18 to 16 clubs, and germany-bbl 2024 holds 272 of 306 (0.89). A player whose latest qualifying source season is 2024 in one of those leagues is refused R9 for a season that was not a collection stop. The builder prints every R9 row whose league-season is outside the six Amendment 4 names, so such rows are visible; the floor is not moved to accommodate them (§8), and the count is stated in Change 3.

**R5c is subsumed.** Amendment 3 labelled an R5 refusal `R5c` when the source league was one of the eight leagues whose scrape stopped. Because R9 is checked before R5, a player from an incomplete league-season is refused R9 whether or not he also holds fewer than 8 games, and no R5 can any longer be caused by the corpus. The label is therefore not emitted; the information it carried travels on every row as `source_completeness`.

## Change 2 — The prediction basis is fitted on the API destination side

Amendment 4 Change 2 moved the continental side of every pair to the EuroLeague API. This records what that produced. `scripts/build_league_factors.py`, `validate_translation_walkforward.py`, `validate_translation_holdout.py` and `build_translation_predictions.py` all take `--continental-source {api,proballers}`; `api` is the default and `proballers` reproduces every number in the notes dated before 2026-09-04. Both sides of every pair are keyed through one name normaliser (`src.data.corpus.euroleague_api.pairing_key`).

**poland-plk is excluded from the API-side fit before pairing.** The first API-side fit (2026-09-04, 01:06) produced a EuroLeague PIR block in which every one of eleven cells read `reliable = false` with the identical pooled factor 0.852: the poland-plk → EuroLeague cell, n = 7 on the Proballers side, holds **n = 2** with a bootstrap SE of 0.21 on the API side, and the method-of-moments τ² = var(factors) − mean(SE²) went to zero for the block, so partial pooling collapsed ten leagues' factors onto the tier mean (ATI-2901 mechanism). poland-plk is refused as a source league by the base document (§2; §3 R3, "its EuroLeague cell rests on n = 7"), so dropping it from the fit changes nothing the pre-registration scores; it is done in code as `API_SIDE_EXCLUDED_SOURCES`, printed by every run and recorded in `league_factors_checks.json: continental_side.excluded_sources`. The `proballers` corpus keeps the league so the 2026-08-21 table still reproduces. The estimator fragility this exposed — a below-floor cell participates in the pooling that decides whether floor-clearing cells keep their per-league dimension — is recorded on ATI-2955 and not fixed here (§8: no method change to admit a run). The walk-forward now records τ per destination per fold and names any collapsed block (`walkforward_summary.json: folds_with_collapsed_block`), because its per-league arm is a two-constant arm in any fold where a block collapses and the script had been silencing that warning.

| quantity | Proballers-side (2026-08-21) | API-side (2026-09-04) | generator / field |
|---|---:|---:|---|
| dual-tier pairs | 5,039 | 4,074 | `league_factors_checks.json: n_pairs` |
| pairs whose destination season is 2015 (API holds none) | 603 | 0 | `league_factor_table_deltas.json: n_pairs_only_in_reference_seasons` |
| reliable `pir/all/all_pairs` cells, both tables | — | 19 | `league_factor_table_deltas.json: cells_reliable_both` |
| max / median \|Δ factor\| on those cells | — | 0.0264 / 0.0073 | same: `max_abs_delta_reliable`, `median_abs_delta_reliable` |
| cells within ±0.03 | — | 19 of 19 | same: `cells_within_tolerance` |
| EuroLeague ordering, Spearman ρ old vs new | — | 0.952 | same: `ordering_spearman.euroleague` |
| K_LAG for 2026-27 (median realised ratio, seasons ≤ 2025) | 0.9304 | 0.9367 | `translation_predictions_2026.json: basis.k_lag` |
| walk-forward pooled n | 719 | 674 | `walkforward_summary.json: n_pooled` |
| per-league vs one global scalar, pooled Δ MAE [95% CI] | +0.2475 [+0.1701, +0.3283] | +0.2042 [+0.1274, +0.2799] | `walkforward_summary.json: pooled.delta_vs_global / ci` |
| RTM + per-league vs RTM | +0.2066 [+0.1393, +0.2786] | +0.1745 [+0.1087, +0.2408] | `rtm_comparator.rtm_plus_league_vs_rtm` |

The full re-fit record, including the second holdout run reported beside the 2026-08-17 verdict, is `docs/research/translation-refit-api-destination-2026-09-04.md`.

## Change 3 — The 2026-27 set on the 2026-08-21 collection, with R9

Built with `scripts/build_translation_predictions.py --built-at 2026-09-04` on `import_signings_2026_both_competitions.json` (`collected_at: 2026-08-21`; the pre-lock collection does not yet exist — the artifact says `draft`). Counts read from `translation_predictions_2026.json: counts`:

| | count |
|---|---:|
| arrivals in the collection | 120 |
| predicted | 50 |
| of which combined arm / per-league only | 40 / 10 |
| refused, total | 70 |
| **R9** `SOURCE_SEASON_INCOMPLETE` | **33** (29 on 2025-26 seasons of the six leagues, 4 on earlier complete-but-smaller seasons) |
| R9 rows on a season that ran to its end (league-size artifacts of the denominator) | 4: DJURISIC, NIKOLA (aba-league 2023, last game 2024-04-08, 0.758); SMART, JAVONTE (aba-league 2023, last game 2024-04-08, 0.758); CALATHES, NICK (france-pro-a 2024, last game 2025-05-17, 0.784); AMAIZE, ROBIN (germany-bbl 2024, last game 2025-05-11, 0.889) |
| R1 / R2 / R3 / R4 / R5 / R7 | 26 / 0 / 3 / 0 / 8 / 0 |

Amendment 4 estimated 43 R9 refusals of 94 scorable imports on this collection by `prior_league` alone; the executed count is 33 because R9 measures a player's *latest qualifying corpus season*, which for a player whose 2025-26 domestic season holds fewer than 8 games is an earlier, complete season. Seven predictions consequently rest on a source season before 2025-26 (SARIC, DARIO (turkey-bsl 2015); ALLMAN, KYLE (turkey-bsl 2024); CANCAR, VLATKO (spain-acb 2018); KREISMONTAS, LUKAS (lithuania-lkl 2024); EVANS, KEENAN (lithuania-lkl 2023); RICHARDSON, ALEXANDER (germany-bbl 2021); GAZZOTTI, GIULIO (italy-lba 2018)); the base document's source-season rule permits this, says nothing about staleness, and is not changed before the lock — it is recorded as a limitation, and every row carries `source_season`. The figure is restated at the pre-lock collection.

## Change 4 — The §7 power table, restated at the R9-reduced count

Generated by `scripts/restate_prediction_power.py` (the Amendment 2 table had no generator; its B1b row, +0.2014, matches no walk-forward field and is superseded). Each row names the `walkforward_summary.json` field it scales; the walk-forward has no B1b arm, so the one-global-scalar contrast stands in and is labelled as a proxy, not as B1b.

| criterion | field | pooled effect | power at n=50 | power at n=110 | n for 80% |
|---|---|---|---|---|---|
| beat B0 (untranslated source rate) *(primary)* | `pooled.delta_vs_b0` | +0.7999 [+0.6042, +1.0083] | 0.56 | 0.88 | 88 |
| beat one global scalar (nearest committed single-constant comparator; NOT B1b) *(primary (B1b proxy))* | `pooled.delta_vs_global` | +0.2042 [+0.1274, +0.2799] | 0.30 | 0.56 | 192 |
| combined beats B1c (RTM, league-free) *(secondary)* | `rtm_comparator.rtm_plus_league_vs_rtm` | +0.1745 [+0.1087, +0.2408] | 0.29 | 0.55 | 198 |
| combined beats per-league alone *(secondary)* | `rtm_comparator.rtm_plus_league_vs_per_league` | +0.1447 [+0.0400, +0.2533] | 0.11 | 0.19 | 749 |

At n = 50 the B0 criterion itself has power 0.56 (0.88 at n = 110). The pre-registration's power statement is therefore weaker than Amendment 4 anticipated ("only the B0 criterion retains meaningful power"): on this collection the prospective set confirms the pooled B0 effect with slightly better than even odds.

> Read exactly as Amendment 2 read it: **only the B0 criterion is adequately powered by the 2026-27 set**, and at the R9-reduced count less so than at 110. A PARTIAL on any other criterion is the season being too small to adjudicate, not the model failing. The pooled walk-forward evidence carries those claims; the prospective set tests B0.

---

## Provenance

| Item | Where it is fixed |
|---|---|
| the floor and its pinning test | `src/data/translation_predictions.py::SOURCE_COMPLETENESS_FLOOR`; `tests/test_data/test_translation_predictions.py::test_the_r9_floor_is_pinned_and_written_down` |
| completeness per league-season | `scripts/build_translation_predictions.py::source_season_completeness`, printed by every run |
| factor-table deltas | `scripts/compare_factor_tables.py` → `data/processed/translation/league_factor_table_deltas.json` |
| re-fit, walk-forward, second holdout record | `docs/research/translation-refit-api-destination-2026-09-04.md` |
| prediction set and factor cells the lock uses | `data/processed/predictions/translation_predictions_2026.json`, `translation_factors_2026.csv` |
| power table | `scripts/restate_prediction_power.py` → `data/processed/predictions/power_restated_2026.json` |
