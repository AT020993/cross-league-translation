# PRE-REGISTRATION — retrospective held-out validation of the league translation factors

**Written and saved as an artifact before any validation fit is run.** Ticket: ATI-2799. Gate for
ATI-2891's publish / do-not-publish decision.

## Provenance and timestamps — added 2026-09-06, nothing below this block changed

A reader who clones the repository cannot date this document from git alone, so the record is
stated here rather than left to be discovered.

| Record | Timestamp (UTC) | What it fixes |
|---|---|---|
| This file's first commit (`5b86acfab`, PR #2023, squash-merged) | 2026-08-25 06:11 | the text as it stands, including the Specification block added 2026-08-21 |
| PR #2023 opened (`gh pr view 2023`) | 2026-08-24 17:48 | the same text, one day earlier |
| Linear ATI-2799, verdict comment `11bd4fbf-4a94-4381-a832-40aa37997458` | **2026-08-17 22:56** | the earliest independently timestamped record of the gates G1–G6, their bars, the threat list T1–T12 **and the result**, in one comment. It states that "the gate margin, threat list (T1-T12) and metric definitions were written and saved before fitting anything, and no threshold was moved afterwards" |
| Linear ATI-2891, pre-registration comment `df67e2e0-adcc-4fd0-8ab0-34e98d3c442e` | 2026-08-17 22:57 | the sibling prospective pre-registration, one minute later, already citing this arm's verdict as PARTIAL |

**What this licenses, stated exactly.** The claim "written and saved before any validation fit is
run" rests on the session record and on the verdict comment's own statement of it. There is **no
independent timestamp of the gates that precedes the result**: the earliest external record of the
bars is the comment that also reports the verdict. A reader is entitled to read the holdout gates as
fixed-by-2026-08-17-22:56 and no earlier. What *is* independently verifiable is that no threshold
moved afterwards: the constants in `scripts/validate_translation_holdout.py` (`G1_RATIO`, `G3_R2`,
`G6_SHARE`, `PER_LEAGUE_N_FLOOR`, `EXCLUDED_SOURCE`) are pinned by
`tests/test_scripts/test_validate_translation_holdout.py::test_pre_registered_bars_are_unchanged`,
and the 2026-08-21 re-run reproduced the verdict bit-identically (ATI-2799 comment
`4e1222d6-e505-415b-bb8c-2e65b1609ca1`). The rule adopted for every later pre-registration in this
line — its own commit, pushed before the generator runs — exists because of this gap.

## Specification

*Added 2026-08-21 to satisfy `tests/test_docs/test_research_notes_have_method_block.py` when this
document was committed to the repo. Nothing below was changed from the 2026-08-17 pre-registration —
this block only restates, in the METHOD.md table form, choices already fixed in the sections that
follow. The bars, threats and exclusions are as originally written and no threshold was moved.*

| Choice | This pre-registration | Alternatives to be printed |
|---|---|---|
| **Unit** | one (player, destination season) transfer into EuroLeague/EuroCup, >=8 games each side | >=5 and >=15 destination games (T7) |
| **Population** | consecutive-season "switchers-in": no continental appearance at >=8 games in season *t* | with incumbents (T4); same-season dual-tier pairs (T1) |
| **Estimator** | exposure-weighted, as shipped | ratio-of-sums, mean-of-ratios (T10) |
| **Factor column** | partially-pooled `factor`, tier-mean fallback where `reliable = False` | raw, /1.019 bias-corrected (T12) |
| **Aggregation key** | `player_name + season`; source/destination largest-minutes stint | collision-pruned (T6) |
| **Sample filter** | poland-plk refused entirely; non-positive rates dropped | -- |
| **Uncertainty** | cluster bootstrap on destination club-season, seed 0 | -- |

**Status of this document.** This is a PLAN, written and saved before the estimator was fitted or any
transfer scored. It therefore states no measured result, and its Specification block describes the
design to be executed rather than a computation performed. The measurements are in
`translation-holdout-validation-2026-08-17.md`; the executable form is
`scripts/validate_translation_holdout.py`, whose pre-registered constants (`G1_RATIO`, `G3_R2`,
`G6_SHARE`, `PER_LEAGUE_N_FLOOR`, `EXCLUDED_SOURCE`) are the bars below expressed as code.

---

**Date:** 2026-08-17 · **Binds:** `docs/superpowers/specs/2026-08-04-player-translation-projection-design.md`
§3, §4[3] (margin pre-registered before the run) and `docs/research/METHOD.md` §1 (threats before
code), §7 (power line), §8 (never move a threshold).

Everything below is fixed. Nothing in this file may be edited after the first performance number is
computed. Results are reported against it as written, including if it fails.

---

## 0. What has been computed so far, and what has not

Computed before writing this file — **sample description only, no performance metric of any kind**:

| quantity | value |
|---|---|
| corpus | 681,888 player-games, 14 leagues, seasons 2015–2025 |
| player-league-seasons at ≥8 games | 31,002 |
| raw source(t) → continental(t+1) rows | 4,020 |
| of those, already in that destination in season t (incumbents) | 2,187 |
| of those, in **any** continental competition in season t | 2,706 |
| **true switchers-in** (no continental appearance in season t) | **1,314** |
| switchers-in with destination season 2024 or 2025 | 257 |
| switchers-in with destination season ≤2023 | 1,057 |
| switchers with source PIR/36 ≤ 0 (degenerate denominator) | 0 |
| switchers with destination PIR/36 ≤ 0 | 2 |

No MAE, R², coverage or per-league error has been computed. The bars below are therefore set blind
to the outcome.

## 1. The population question, declared before the fit rather than discovered in it

The factors are fitted on the **same-season dual-tier natural experiment**: one player, one season,
producing in a domestic league and a continental competition simultaneously. The player is his own
control, which is the entire methodological argument of the spec (§0, §3).

**This validation scores a different population.** A transfer is consecutive-season, and it carries
exactly the selection confound the dual-tier design exists to remove — players move *because* they
improved or declined, and a year passes in which they age, change club, change role and change
coach. The spec is explicit that consecutive-season switches are "secondary validation only" and
"must never be pooled into the primary estimate" (§4[1]).

So the factors are being asked to do something they were not fitted to do. That is the honest
description of this gate, and it is declared here, in advance, as a **property of the test** rather
than as an excuse available afterwards. It has a consequence for interpretation which is also fixed
now: a failure on this population does not by itself falsify the factors, and a pass on it is
stronger evidence than a pass on the fitted population would be. Both readings are pre-committed.

To make the cost of the population change measurable rather than arguable, threat T1 below scores
the identical model on a held-out slice of the **fitted** population as a paired arm.

## 2. Populations, exactly

**Primary scored population — "switchers-in":** one row per (player, destination season) where the
player recorded ≥8 games in a source league in season *t*, ≥8 games in EuroLeague or EuroCup in
season *t+1*, and **no** EuroLeague or EuroCup appearance at ≥8 games in season *t*. Largest-minutes
stint per side, as in the estimator's `build_pairs`. Key is `player_name + season` (Proballers has no
stable person id — see threat T6).

**Excluded by declaration:** `poland-plk`, in any form, both destinations. Phase 0 established its
euroleague cell rests on n=7. Its 14 held-out rows are counted and reported as refused, not scored.
Sources are the estimator's own `NOT_A_SOURCE` definition (bcl, test, and the two continental
competitions are never a source).

**Outcome:** destination per-36 PIR in season *t+1*, from the same box-score corpus.

## 3. The model and the two required baselines

All three predict destination PIR/36 for the same rows.

| name | prediction |
|---|---|
| **M** — translation | `pir_per36_src(t) × factor(source league → destination, stat=pir, era=all, sample=all_pairs)` |
| **B0** — raw, untranslated | `pir_per36_src(t)` |
| **B1a** — naive minutes scaling, oracle | `B0 × (min_per_game_dest(t+1) / min_per_game_src(t))` |
| **B1b** — naive minutes scaling, honest | `B0 × k`, where `k` is the mean destination/source minutes-per-game ratio fitted on the ≤2023 switchers |

B1a is given the player's **realised** destination minutes, which M does not get. It is reported as
an oracle-advantaged baseline and labelled as such; B1b is the version answerable at decision time.
Both are reported. Per-36 already normalises minutes, so a minutes-scaled per-36 prediction is a
claim about role change, not an arithmetic correction — which is why the honest and oracle forms are
separated rather than blended.

`factor` is the partially-pooled column, with fallback to `tier_mean` where `reliable = False`, which
is what the estimator's docstring requires consumers to do.

## 4. The two arms

**Arm A — held-out season (spec §4[3]).** Factors refit from scratch on pairs with `season ≤ 2023`
only, using the shipped `scripts/build_league_factors.py` estimator code unmodified. Scored on
switchers with destination season 2024 or 2025. n = 257 before the poland-plk exclusion.

**Arm B — leave-one-league-out.** For each source league L, factors refit with **all of L's pairs
removed**, so L has no cell of its own and the model must fall back to the destination-tier mean.
Scored on all of L's switchers, all seasons. This is the operationalisation of "generalise rather
than memorise": if the tier mean does nearly as well as L's own factor, the per-league factors are
not carrying league-specific information; if it does much worse, they are — and the question becomes
whether that information generalises to a league never seen, which is what this arm measures.

Arm B deliberately does not restrict the season window: it isolates league memorisation, not
temporal generalisation, and mixing the two would make a failure unattributable.

## 5. The bars

Set before any performance number exists. **Primary gate is Arm A against B0**, per spec §4[3].

| row | bar |
|---|---|
| **G1** pooled Arm A MAE | model MAE ≤ **0.95 × B0 MAE** (≥5% relative improvement) |
| **G2** paired bootstrap 95% CI on (B0 MAE − model MAE), resampled by destination club-season cluster | **excludes 0** |
| **G3** pooled Arm A R² | **≥ 0.20** |
| **G4** model beats **both** B0 and B1b on MAE and on R² | required |
| **G5** Arm B pooled MAE | ≤ **0.95 × B0 MAE** on the same rows |
| **G6** Arm B per-league, among leagues with n ≥ 20 | model beats B0 in **≥ 75%** of them |
| **G7** stated 95% prediction-interval coverage | **reported**, not bounded — see §6 |
| **G8** per-league Arm A breakdown | **reported for every league**, with a power line on every league that fails |

**Where these numbers come from, so a reader can see they are not reverse-engineered.**

*G1 = 5%.* The spec's in-sample back-test on 1,701 moves gave MAE 3.02 vs 4.08 naive — 26% better,
and explicitly labelled "encouraging, not passing". The measured mean cross-tier PIR/36 gap is
−13.9%, so pure removal of that level shift should buy well over 5% on MAE. A 5% bar therefore
demands the factors retain roughly a fifth of the in-sample gain out-of-sample on a harder
population. It is a deliberately modest bar because G2 carries the statistical teeth: a small
improvement that a cluster bootstrap cannot separate from zero fails regardless of G1.

*G3 = 0.20.* The bar must exceed the best model that uses **no factor at all** — source rate alone
scored R² = 0.129 on the stale corpus — with headroom for the corpus change. It sits below the
0.380 the same model class reached on the stale corpus, so it is not a bar tuned to a known result,
and far below the reliability ceiling in §6.

*G5, G6 = the same margin, 75%.* Arm B must clear the same margin as Arm A or the factors beat the
baseline only where they have seen the league. 75% of leagues with n ≥ 20 is a majority plus margin;
requiring all of them would let one thin league veto a real effect, and requiring a bare majority
would let a coin flip pass.

*n ≥ 20 floor for a per-league verdict.* Fixed now, before per-league counts are looked at in
anything but total. Below 20 the league is reported as **no signal available** with its power line,
never as a failure.

### Verdict rule, declared in advance

* **PASS** — G1–G6 all met.
* **FAIL** — G1, G2 or G3 missed. Publishing the negative is the specified output (ATI-2891).
* **PARTIAL** — Arm A passes (G1–G4) and Arm B fails (G5 or G6), or the converse. These are
  different verdicts and are reported separately, never averaged into one.

A miss is reported as a miss. No threshold in this table may be edited after the first measurement,
including by a rounding margin and including while calling the new value conventional (METHOD.md §8).

## 6. Interval calibration and the ceiling — both expectations fixed now

**Stated 95% prediction interval:** `pred ± 1.96 × sqrt((pir_per36_src × se_factor)² + σ_resid²)`,
where `se_factor` is the cell's cluster-bootstrap SE and `σ_resid` is the residual SD from the
≤2023 switchers. Coverage is reported with **over-coverage and under-coverage both counted as
failures**, because an interval that is too wide is as uninformative as one that is too narrow.

**Expected coverage is ~0.86, not 0.95.** Phase 0's synthetic study measured the estimator's nominal
95% intervals at ~86% actual, falling to 0.73 at n=500 — the interval narrows around a bias that
does not move. Observing under-coverage here is therefore a **confirmation of a known property, not
a new finding**, and will be reported as such. Coverage materially *above* 0.95 would be the
surprise.

**Ceiling.** Destination-side split-half reliability is re-measured on the current corpus (odd/even
destination games, Spearman-Brown), and the implied maximum attainable R² is quoted beside every
result. The inherited figure is split-half r = 0.541 → reliability 0.702, i.e. **R² = 0.70 is the
ceiling for any model** on single-season continental PIR/36. It is re-measured rather than inherited;
the re-measured value is what the results are read against.

**Power line, mandatory (METHOD.md §7).** Every negative — pooled or per-league — is phrased as "no
detectable effect at n=X; detecting Y requires n=Z", computed with the repo's own
`assert_powered_for_null(r_obs, n_obs, n_used)` from `src/research/gates.py`. A per-league low number
without a power line does not ship.

## 7. Threats, and the control for each — coded into the same script

METHOD.md §1: each control runs whether or not I remember to look, and each prints.

| # | threat | control, in the same script |
|---|---|---|
| **T1** | **Population mismatch** — factors fitted on same-season pairs, scored on consecutive-season transfers | Score the identical model on held-out **same-season** dual-tier pairs (2024–25) as a paired arm. Report both. The gap between them is the price of the population change, measured rather than asserted |
| **T2** | **Temporal leakage** — 2024–25 information entering the ≤2023 fit | Assert `pairs.season.max() ≤ 2023` in the Arm A fit; assert every scored row has `season_dest ≥ 2024`; assert the refit pair count is strictly less than 5,039 |
| **T3** | **Player leakage** — the same player in both the fit pairs and the scored transfers | Count the overlap on `player_name`, and re-run Arm A excluding every overlapping player. Report both |
| **T4** | **Incumbent contamination** — players already playing in the destination are not switchers | Excluded by construction; re-run **with** incumbents included as a sensitivity and report the direction of the change |
| **T5** | **Selection / regression to the mean** — players move because they improved or declined | Split switchers on whether their source-season rate exceeded their own prior-seasons mean, and report model and B0 error in each half separately. Report the sign of B0's bias |
| **T6** | **Name collision** — no stable person id | Re-run excluding names appearing with ≥4 distinct leagues in the corpus, and names appearing with >1 club inside one league-season |
| **T7** | **Survivorship** — only players who earned ≥8 destination games are visible | Count switchers with 1–7 destination games (invisible to the metric), and re-run the gate at ≥5 and ≥15 games |
| **T8** | **Reliability floor** — a low R² may mean "not predictable", not "model bad" | Destination split-half reliability, re-measured; ceiling quoted beside every R²; `assert_powered_for_null` on every null |
| **T9** | **Pooling collapse** — Phase 0 found τ²=0 blocks returning one identical factor for every league | Assert `τ > 0` in both PIR blocks of every refit; report any block where it collapses, and treat a collapsed block's per-league verdicts as uninterpretable |
| **T10** | **Estimator choice is load-bearing** (METHOD.md §3/§6) | Re-run the whole of Arm A with `ratio_of_sums` and `mean_of_ratios` factors; report the MAE spread across the three. If the spread exceeds the G1 margin, the gate verdict is declared estimator-dependent |
| **T11** | **Degenerate denominator** — src rate 0 makes a ratio undefined | Count and exclude; already measured at 0 of 1,314 source and 2 destination rows |
| **T12** | **The known +0.019 null bias** — Phase 0 showed the exposure-weighted estimator returns ~1.019 when the truth is 1.0, flat in n | Re-score Arm A with every factor divided by 1.019, and report whether the gate verdict changes. A verdict that flips under a known-magnitude bias correction is reported as fragile |

## 8. Limitations — stated as limitations, not opened as caveats

METHOD.md's distinction: a caveat is a testable confound and becomes a test; a limitation is a scope
bound nothing in this data can discharge. These are limitations.

* **No birthdates**, so no aging adjustment (ATI-2766). A transfer spans a year of aging that the
  model cannot see, and this is a permanent component of Arm A's error.
* **No pace or opponent-strength adjustment** inside the factor.
* **The quota confound is not controlled** in the factors being validated — the estimator's own
  docstring says so. Phase 0 measured its Israeli magnitude at −0.030, larger than that cell's
  bootstrap SE, so israel-bsl carries a systematic the interval does not cover.
* **`differs_from_parity` is not used anywhere in this validation.** Phase 0 measured its
  false-positive rate at 13–33% against a nominal 5%. It is descriptive only.

## 9. What is being claimed, and what is not

Phase 0's operating envelope stands and this validation cannot widen it: the estimator is
trustworthy for **ranking** source leagues within a destination and for point factors at n ≥ 75
quoted to ±0.05. It is not trustworthy for any claim that a factor differs from 1.0, for absolute
levels tighter than ±0.05, or for treating a published 95% interval as 95%. A PASS here licenses the
claim that translated projections beat untranslated production out-of-sample by the pre-registered
margin — nothing more.
