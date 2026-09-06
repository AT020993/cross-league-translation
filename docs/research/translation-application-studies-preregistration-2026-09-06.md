# PRE-REGISTRATION — four application studies for the manuscript: pairing versus form, the scout's shortlist, refusals as a finding, the league graph

**Date: 2026-09-06. Decided by Amir 2026-09-06 ("do all these recommendations"). Status: pre-registered before any of the four generators exists; this commit is pushed before the implementation branch is opened.** Base documents: `preregistration-2026-27-predictions.md` (Amendments 1–11), `translation-propositions-2026-09-04.md`, `prelock-program-preregistration-2026-09-04.md`. Nothing below touches the 2026-27 lock, its gates, its basis, or the abstract v3; every result is manuscript material.

## The rule the program lives under

**No study here re-scores a gate or moves a bar.** Studies A–C are descriptive reads with a pre-stated prediction each; Study D is a figure. A study whose prediction fails is reported with the same battery as one that passes (METHOD.md §5). Every quoted number will have a committed generator and a test (§16), and every generator asserts it reproduces the walk-forward's five arm MAEs before computing anything (the existing `assert_reproduces_walkforward` gate).

## Specification

| Choice | This program | Alternatives considered |
|---|---|---|
| **Unit** | A: one domestic player-season at a dual-competition club; B: one walk-forward season cohort (2020–2025) and, inside it, one shortlist of size K; C: one 2025-26 refused import whose refusal can be lifted (R5, R9); D: one league (node) and one league pair (edge or implied contrast) | pair-level for A (rejected — pairs are the *outcome* of the selection under test) |
| **Population** | A: every `(player, season)` with ≥ 8 domestic games whose domestic club fielded at least one paired player that season (the club is in both competitions), API corpus, 2016–2025; B: the 674 pooled walk-forward rows; C: the 2025-26 signings collection of 2026-09-04, refusals R5 with ≥ 3 source games and R9; D: the 12 leagues that carry pairs | A: all domestic player-seasons (rejected — a player at a domestic-only club cannot be paired, so the comparison would measure club membership, not form) |
| **Estimator** | A: standardised mean difference (Cohen's d) of the source-season deviation from the player's own prior rate, paired vs unpaired, with a cluster bootstrap on domestic club-season; B: mean realised EFF/36 of the top-K by each arm, and the share of "career-year" players (`above_own_prior`) in each top-K; paired bootstrap over rows within season; C: MAE of the lifted rows under the same basis, against the accepted set's MAE at the same checkpoint, paired cluster bootstrap on destination club; D: two-way fixed effects on log rates with effective-resistance standard errors (Proposition 4) | — |
| **Null / bar** | A: `|d| < 0.10` with the 95% cluster-bootstrap CI inside (−0.20, +0.20) reads *pairing independent of form at this resolution*; otherwise the measured d IS the selection size and is reported as such; B: the combined arm's top-10 realises a higher mean EFF than the multiplier-only top-10 in ≥ 4 of 6 seasons AND the pooled paired difference's CI excludes zero; C: lifted-refusal MAE exceeds the accepted set's MAE with a CI excluding zero (the refusal codes discriminate); a CI spanning zero means the refusal costs coverage for nothing measurable and is reported as that; D: none — descriptive | — |
| **Sample filter** | A: players with a prior rate (any earlier season, any league); B: rows with `above_own_prior` defined; C: R5 rows need ≥ 3 source games (a 1–2 game source rate is a degenerate measurement, not a lifted refusal); R1, R2, R3, R7 are not liftable and are counted, not scored | — |
| **Aggregation key** | A: `player_name + season`, cluster = domestic club-season; B: season; C: `person_code`, cluster = destination club; D: league | — |
| **Uncertainty** | cluster bootstrap 2,000 draws, seed 0, throughout; B additionally permutes the `above_own_prior` flag within season (200 draws) as the null for the career-year share | — |
| **Traceability** | new scripts: `scripts/test_pairing_vs_form.py` (A), `scripts/rank_shortlist_double_count.py` (B), `scripts/score_lifted_refusals.py` (C), `scripts/plot_league_graph.py` (D). Shared, additive changes: `validate_translation_walkforward.fold_rows` carries `prior_mean_pir36` and `above_own_prior` (nothing above reads them; the five arm MAEs are asserted unchanged); `instantiate_translation_propositions.py` adds `P4_identification.implied_all_pairs` (every league pair's implied factor, R_eff SE and CI). Outputs under `docs/research/artifacts/application-studies-2026-09/` | — |

---

## Study A — Is the pairing independent of form? (the identification claim, tested)

**Question.** The abstract says the same club fields the same player at two levels *by schedule*, so the pairing is independent of form. The club's entry is by schedule; a player's minutes in each competition are a coach's choice, and the ≥ 8-games floor on both sides selects on those minutes. Does a player's *form* — his source-season rate relative to his own prior — predict whether he is paired?

**Design.** For every domestic player-season at a club that is in both competitions that season: `paired` = reached ≥ 8 games on a continental side (the `build_pairs` rule, unchanged); `deviation` = `pir_per36_src − prior_rate` (`prior_seasons_rate`, minutes-weighted over all strictly earlier seasons, any league). Report: mean deviation paired vs unpaired, Cohen's d with cluster-bootstrap CI (domestic club-season), and the same for `prior_rate` itself (level).

**Predictions, stated now.** (i) Level differs strongly (paired players are better; d on `prior_rate` > 0.5) — that is selection on ability, which Proposition 4(i) cancels and which is *harmless* to the design. (ii) Deviation differs weakly or not at all: `|d| < 0.10`. If (ii) fails, the measured d is the size of the selection the design cannot remove, it is reported beside Proposition 4(iii)'s −0.122 level shift, and the manuscript's sentence becomes "the pairing is independent of ability by construction and of form up to d = …".

**Controls.** Negative: permute `paired` within domestic club-season (200 draws) — the observed d must sit inside the permutation distribution for (ii) to be read as null, and outside it for (i). Positive: (i) itself. Sensitivity: the floor at ≥ 5 and ≥ 15 continental games; excluding EuroCup; per destination.

**Threats.** T-A1 minutes are shared, so a heavy continental load lowers domestic games — the domestic ≥ 8 floor is kept on both groups. T-A2 `prior_rate` requires an earlier season; debutants are excluded from A only. T-A3 name key (ATI-2796). T-A4 a club that enters a continental competition mid-corpus is in the population only in seasons it fielded a paired player.

**Power.** Thousands of unpaired and ~4,000 paired player-seasons; d = 0.10 is detectable at far above 80%. The bar is a resolution statement, not a power limit.

## Study B — The scout's shortlist: what the double-count costs in ranks

**Question.** Translate the mechanism (a multiplier over-predicts a career year) into the object a front office uses: a ranked shortlist. On each walk-forward season, rank the cohort by predicted EFF/36 under the multiplier-only arm (`per_league`) and under the combined arm (`rtm_plus_league`). Take the top-K (K = 10 primary; 5 and 20 as sensitivity).

**Reads.** Per season and pooled: (a) mean realised EFF/36 of each arm's top-K (the scout's payoff); (b) the number of the arm's top-K that finish outside the realised top-2K ("overpaid"); (c) the share of `above_own_prior` players in each top-K. Paired bootstrap over rows within season (2,000 draws) for (a) and (b); the `above_own_prior` flag permuted within season (200 draws) as the null for (c).

**Predictions, stated now.** The combined top-10 realises a higher mean EFF than the multiplier-only top-10 in ≥ 4 of 6 seasons and the pooled paired difference's CI excludes zero; the multiplier-only top-10 carries a higher career-year share than the combined top-10 and than the permutation null. If the pooled CI spans zero, the ranking read does not separate at this n and the manuscript reports the MAE decomposition only.

**Placebo.** The same reads for `per_league` vs `one_global`: two arms that differ in league resolution, not in the RTM term; expected to separate little on (c).

**Threats.** T-B1 top-K statistics are order statistics with heavy tails at n ≈ 100–134 per season; the pooled read is the claim. T-B2 K interacts with cohort size; K = 10 is ~8% of a cohort. T-B3 rows lacking a prior (`above_own_prior` undefined) are excluded from (c) only.

## Study C — Refusals as a finding: would the refused have carried larger errors?

**Question.** The 2025-26 rehearsal set refuses 428 of 516 arrivals. For the two codes that refuse a *scorable* row on a data-quality rule — R5 (source season below the 8-game floor) and R9 (source league-season under 90% complete) — predict the player anyway with the same basis, and score him at 2026-06-30 against the realised outcome, beside the accepted set.

**Design.** `scripts/score_lifted_refusals.py` imports the builder's functions and re-runs the classification with R5 (at ≥ 3 source games) and R9 lifted; every other code stands. It must not import a modified builder: the lock's `build_translation_predictions.py` is untouched, and the study asserts that its own accepted set is byte-identical to the rehearsal's 88 predictions. Scoring reuses `evaluate_translation_predictions.score_checkpoint` with the R8 censor at ≥ 8 destination games.

**Reads.** MAE of the lifted R5 rows, the lifted R9 rows, and the accepted set, with paired cluster-bootstrap contrasts (destination club); coverage of the accepted set's conformal half-width applied to the lifted rows; n scored / censored per code.

**Predictions, stated now.** Lifted R9 MAE exceeds the accepted MAE with a CI excluding zero (a half-scraped source season is a worse input). Lifted R5 MAE exceeds the accepted MAE (a 3–7 game source rate is noise). If either CI spans zero, the code refuses coverage for nothing this test can measure; that is reported as a candidate for the 2027 refit (never for the 2026-27 lock, whose refusal rules are fixed).

**Threats.** T-C1 small n (48 R9, ≤ 100 R5 before the ≥ 3-game filter and the R8 censor); the CI is the read, not the point. T-C2 lifted R9 rows use a source season that is itself half-observed — that is the quantity under test, not a confound. T-C3 the accepted set is end-of-season 2025-26 roster; the same `first_round ≤ 3` population filter is applied to both groups.

## Study D — The league graph as a figure and a product

**What.** `scripts/plot_league_graph.py` draws the weighted league graph (nodes = 12 leagues; edge width = exposure-weighted pairs; node label = two-way fixed-effect multiplier vs EuroLeague) and beside it the implied domestic-to-domestic factor matrix with effective-resistance 95% CIs, read from `propositions.json: P4_identification.implied_all_pairs`. Descriptive; every number comes from the Proposition 4 fit already on record, extended from three named moves to all 45 domestic pairs.

**Reads.** The full implied matrix; which implied contrasts have an R_eff SE below 0.02 on the log scale (well-bridged) and which do not; the two continental nodes' betweenness (they are the only bridges).

**Threats.** T-D1 an implied factor between two leagues that never meet carries the two-way model's assumptions (multiplicative, no interaction); stated on the figure. T-D2 adjacent rows are not separable — the cluster caveat from `league-translation-factors-2026-08-15.md` is carried over.

---

## What this program does not change

The 2026-27 lock (Amendment 7 sequence, step 3b), its refusal rules, gates and interval; the abstract v3; the holdout and walk-forward records; the propositions note's existing numbers (the new field is additive and the existing fields are asserted unchanged on regeneration).

## Scripts

To be written under the traceability row above; each ships with mutation-checked tests. Results note: `translation-application-studies-2026-09.md`, rendered from the artifacts.

---

## Amendment 1 — the abstract scope is lifted for Studies A and D (2026-09-06, ACCEPTED by Amir)

**Date: 2026-09-06. Status: ACCEPTED by Amir 2026-09-06 ("approve v4, do the amendment and regenerate the figures"). Its own commit, pushed before the figure change that implements it.**

**What changes.** The header and §"What this program does not change" say nothing here touches the abstract. That line is lifted for two of the four studies, in the abstract v4 (`docs/plans/sloan-ssac27-abstract-draft.md` §Abstract v4, approved the same day as the submission text):

* **Study A** licenses one Methods sentence, quoted at its number and not its verdict, because the primary arm straddles the pre-registered bar (d = 0.09 [0.02, 0.17] against the |d| < 0.10 bar; sensitivity 0.06–0.11 across floors and destination sets): *"Paired players are stronger (d=0.45), which the within-player ratio cancels; the pairing is nearly independent of form (d=0.09, within-club permutation p=0.10)."* Source: `docs/research/artifacts/application-studies-2026-09/pairing_vs_form.json`, primary arm (floor 8, both destinations).
* **Study D** licenses one Results clause, an implied domestic-to-domestic factor whose interval is in the source table: *"a Spanish-league box score is worth 1.18× in Lithuania"* — `docs/plans/figures/sloan_fig3_implied_factors.csv` row `spain-acb,lithuania-lkl`, 1.180, CI [1.140, 1.221], `direct_pairs` 0. The graph panel of `sloan_fig3_league_graph.png` becomes panel (a) of the abstract's Figure 1.

**What does not change.** Studies B (NOT SEPARABLE at k = 10) and C (the lifted-R9 contrast is not separable) stay manuscript-only, as their verdict lines already say; nothing in this amendment lets a study that failed its bar into the abstract. No number in any artifact changes. The 2026-27 lock, its gates, its basis and its refusal rules are untouched.

**Why an amendment.** The scope line was a guard against choosing, after the results, which of four studies to show. The two admitted are the design check and the descriptive figure, both reported at their numbers; the two excluded are the ones with a pass/fail bar that did not pass. Lifting the line silently would defeat the guard; lifting it in a dated commit keeps it.

**Two further decisions taken the same day for the abstract v4, recorded here once** (they concern the abstract, not this program): the prospective sentence drops its power clause (0.35–0.56 at n = 50–88, `power_p1_as_written_2026.json`) because v4 makes no accuracy promise — the power stays in `preregistration-2026-27-predictions.md` Amendment 9 and the manuscript §10; and the opening hook is the NBA arm, which the companion repository cannot recompute (no NBA rows, ToU §9) — accepted, with the export README naming the public source and the fetch step so a reviewer can rebuild it from their own pull.
