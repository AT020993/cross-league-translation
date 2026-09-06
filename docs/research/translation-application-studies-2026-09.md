# Application studies for the manuscript — RESULTS: pairing versus form, the scout's shortlist, lifted refusals, the league graph

**Generated 2026-09-06 by `scripts/render_application_studies_note.py` from
`docs/research/artifacts/application-studies-2026-09/` (`pairing_vs_form.json`, `shortlist_ranks.json`,
`lifted_refusals.json`) and `docs/plans/figures/sloan_fig3_readback.json`; every number below is read from
those files. Pre-registration: `translation-application-studies-preregistration-2026-09-06.md`. Nothing here
touches the 2026-27 lock or its gates; every result is manuscript material either way. Amendment 1 (2026-09-06) lifts the pre-registration's abstract scope for Studies A and D only — `translation-application-studies-preregistration-2026-09-06.md` §Amendment 1.**

## Specification

| Choice | This note | Alternatives considered |
|---|---|---|
| **Unit** | A: one domestic player-season at a dual-competition club (n = 5,358, 456 club-seasons); B: one walk-forward season and its top-K shortlist (674 rows, 674 with a prior flag); C: one 2025-26 arrival whose refusal was lifted (R9: 48; R5: 0 — every R5 row has no corpus source row, so nothing to lift); D: one league / one league pair | as pre-registered |
| **Estimator** | A: Cohen's d, cluster bootstrap on domestic club-season, within-club permutation null; B: top-K mean realised EFF/36, overpaid count, career-year share, paired row-bootstrap within season; C: two-sample cluster bootstrap on MAE (destination club); D: two-way fixed effects, effective-resistance SE | — |
| **Null / bar** | as pre-registered (A: \|d\| < 0.10 with CI inside ±0.20; B: ≥ 4/6 seasons and pooled CI excluding zero; C: lifted MAE exceeds accepted with CI excluding zero) | — |
| **Sample filter** | A: players with a prior rate; B: rows with a finite combined prediction; C: `first_round ≤ 3`, R8 censor at ≥ 8 destination games | — |
| **Aggregation key** | A: `player_name + season`; B: season; C: `person_code`; D: league | — |
| **Uncertainty** | 2,000 bootstrap draws, seed 0; 200 permutation draws | — |

## Study A — Is the pairing independent of form?

**Read, primary arm (floor 8 continental games, both destinations): `independent of form at this resolution (|d| < 0.10, CI inside ±0.20)`.**

| quantity | paired | unpaired | Cohen's d | 95% cluster CI | within-club permutation, share of \|d\| at or beyond | null p95 of \|d\| |
|---|---:|---:|---:|---|---:|---:|
| form: source-season deviation from own prior (EFF/36) | +0.61 | +0.20 | **+0.091** | [+0.016, +0.167] | 0.10 | 0.097 |
| level: own prior rate (EFF/36) | 16.96 | 14.78 | **+0.446** | [+0.376, +0.515] | 0.00 | 0.246 |

Two things are true at once and both are reported. The pre-registered bar reads *independent at this
resolution* (d below 0.10, CI inside ±0.20), and the within-club permutation null — which holds each club-season's
mix fixed — puts the observed form d inside its 95th percentile (0.10 of null
draws at or beyond it). The cluster-bootstrap CI nevertheless excludes zero: coaches allocate continental minutes
to players in form by a small amount, about 0.41 EFF/36 of deviation from own prior.
Selection on **ability** is five times larger (d +0.45) and is what Proposition 4(i) cancels. The
manuscript sentence this licenses: *the pairing is independent of ability by construction and nearly independent
of form (d = 0.09, within-club permutation p = 0.10), against d = 0.45 on ability;
the residual form selection is the term the regression-to-the-mean arm repairs (Proposition 4(iii)).*

Sensitivity (all arms; the floor and the destination set move d between 0.06 and 0.11 — the read straddles the
bar, which is why the sentence above quotes the number, not the verdict):

| floor | destinations | n | paired | d (form) | 95% CI | permutation share | d (level) | read |
|---:|---|---:|---:|---:|---|---:|---:|---|
| 5 | both | 5,867 | 4,054 | +0.102 | [+0.036, +0.171] | 0.10 | +0.412 | selection on form measured: d is the selection size |
| 5 | euroleague_only | 3,114 | 2,072 | +0.066 | [-0.026, +0.159] | 0.11 | +0.521 | independent of form at this resolution |
| 8 | both | 5,358 | 3,799 | +0.091 | [+0.016, +0.167] | 0.10 | +0.446 | independent of form at this resolution |
| 8 | euroleague_only | 2,927 | 1,996 | +0.107 | [+0.014, +0.205] | 0.03 | +0.530 | selection on form measured: d is the selection size |
| 15 | both | 4,233 | 2,830 | +0.106 | [+0.026, +0.189] | 0.01 | +0.463 | selection on form measured: d is the selection size |
| 15 | euroleague_only | 2,540 | 1,804 | +0.061 | [-0.052, +0.182] | 0.10 | +0.549 | independent of form at this resolution |

The estimator pairs 4,074 player-seasons at this floor; the primary arm's 3,799 paired
rows are those with a prior rate (debutants excluded from A only, T-A2).

## Study B — The scout's shortlist

**Verdict (k = 10, pre-registered): `NOT SEPARABLE at this n: the ranking read does not separate; report the MAE decomposition only`.**

| K | combined − multiplier, mean realised EFF/36 of the top-K (pooled over seasons) | seasons combined wins | career-year share, multiplier / combined | overpaid, multiplier / combined (sum) | placebo: per-league − one global |
|---:|---|---:|---|---|---|
| k10 | +0.614 [-0.567, +1.431] | 5/6 | 0.68 / 0.47 | 21 / 17 | -0.076 [-0.689, +1.181] |
| k5 | +0.083 [-1.631, +2.001] | 4/6 | 0.60 / 0.33 | 13 / 12 | -0.051 [-1.191, +1.975] |
| k20 | -0.020 [-0.320, +0.513] | 4/6 | 0.65 / 0.48 | 30 / 30 | +0.701 [+0.084, +1.030] |

Per season, k = 10:

| season | n | multiplier top-10, realised | combined top-10, realised | Δ (95% CI) | overpaid m / c | career-year share m / c |
|---:|---:|---:|---:|---|---|---|
| 2020 | 134 | 20.22 | 21.08 | +0.86 [-0.732, +1.922] | 5 / 4 | 0.90 / 0.80 |
| 2021 | 101 | 18.97 | 19.93 | +0.96 [-1.296, +3.134] | 3 / 2 | 0.70 / 0.20 |
| 2022 | 106 | 21.59 | 21.59 | +0.00 [-1.168, +1.491] | 3 / 3 | 0.50 / 0.50 |
| 2023 | 102 | 20.49 | 21.38 | +0.88 [-4.112, +4.341] | 4 / 2 | 0.70 / 0.40 |
| 2024 | 104 | 20.31 | 21.12 | +0.81 [-0.578, +2.967] | 3 / 3 | 0.50 / 0.20 |
| 2025 | 127 | 23.90 | 24.08 | +0.18 [-1.761, +2.760] | 3 / 3 | 0.80 / 0.70 |

Reading. The multiplier-only shortlist carries a career-year share of 0.68 against
0.47 for the combined arm; the combined top-10 realises
+0.61 EFF/36 more per player (CI [-0.567, +1.431]), winning
5 of 6 seasons. The placebo contrast (league resolution without the RTM term) moves
the same read by -0.08 (CI [-0.689, +1.181]).

## Study C — Refusals as a finding

Identity check: the study's accepted set is the rehearsal's committed set (88 predictions,
max projection gap 0.0e+00). Refusals before lifting: {"R1": 94, "scorable": 88, "R9": 48, "R5": 100, "R2": 176, "R3": 10}.
Lifting rule: R9 always; R5 at ≥ 3 source games — **no R5 row qualifies**, because every R5 arrival has no qualifying
corpus source row at all (`source_games` = 0), so R5 is a coverage fact about the corpus, not a liftable rule.
Population: full-season first_round <= 3; scored at 2026-06-30 with the R8 censor at 8 games.

| group | scored | censored (R8) | MAE model | MAE B0 | MAE B1c | conformal coverage |
|---|---:|---:|---:|---:|---:|---:|
| accepted | 58 | 8 | 3.438 | 3.830 | 3.401 | 0.931 |
| lifted_R5 | 0 | 0 | — | — | — | — |
| lifted_R9 | 34 | 1 | 3.397 | 3.655 | 3.345 | 0.941 |
| lifted_all | 34 | 1 | 3.397 | 3.655 | 3.345 | 0.941 |

| contrast | MAE lifted − accepted | 95% CI (two-sample cluster bootstrap) | read |
|---|---:|---|---|
| lifted_R9 | -0.040 | [-1.053, +1.122] | not separable: the code refuses coverage for nothing this test can measure |
| lifted_all | -0.040 | [-1.053, +1.122] | not separable: the code refuses coverage for nothing this test can measure |

Reading. The R9 rule (source league-season under 90% complete) refused 48 arrivals on the 2025-26 set;
predicted anyway from their half-observed source seasons, 34 of them scored with MAE
3.397 against 3.438 for the accepted set, and coverage 0.941. The
pre-registered prediction (lifted R9 carries larger error) **fails**: the contrast is not separable. That is reported as
what it is — a refusal that costs coverage for nothing this test can measure — and it is a candidate for the **2027
refit**, never for the 2026-27 lock, whose refusal rules are fixed (Amendment 5). The caveat stands: n = 34, and the
CI is a full ±1 EFF/36 wide.

## Study D — The league graph

`docs/plans/figures/sloan_fig3_league_graph.png` (readback `sloan_fig3_readback.json`): 12 leagues,
90 implied domestic-to-domestic contrasts, of which **64** have an effective-resistance SE below
0.02 on the log scale; reciprocity holds to 2.2e-16. The full matrix is
`sloan_fig3_implied_factors.csv`. Every domestic league is bridged only through the two continental competitions
(Proposition 4(ii)); an implied factor between two leagues that never meet carries the two-way model's assumptions
(multiplicative, no interaction) and the cluster caveat of `league-translation-factors-2026-08-15.md`.

## What this licenses

* **A:** the design sentence, with its number: nearly independent of form (d ≈ 0.09), independent of ability by construction (d ≈ 0.45 cancels).
* **B:** see the verdict line; a PASS licenses the shortlist sentence for the manuscript's §7, a NOT SEPARABLE licenses only the MAE decomposition.
* **C:** a negative result, reported with the same battery: R9 does not discriminate on 2025-26 at n = 34; R5 is not liftable.
* **D:** a figure and a table, descriptive.
* **Not licensed:** any change to the lock, the refusal rules, or the gates. The abstract: Studies A and D enter the abstract v4 under Amendment 1 (2026-09-06) of the pre-registration, quoted at their numbers; B and C stay manuscript-only.

## Scripts

`scripts/measure_pairing_vs_form.py` (A), `scripts/rank_shortlist_double_count.py` (B; reads `walkforward_rows.parquet`
regenerated with `prior_mean_pir36` / `above_own_prior`), `scripts/score_lifted_refusals.py` (C; asserts identity with the
committed 2025 set), `scripts/plot_league_graph.py` (D; reads `propositions.json: P4_identification.implied_all_pairs`),
`scripts/render_application_studies_note.py` (this note). Tests: `tests/test_scripts/test_application_studies.py`.
The pre-registration named Study A's script `test_pairing_vs_form.py`; it is `measure_pairing_vs_form.py` so pytest
never collects it — a filename, not a bar.
