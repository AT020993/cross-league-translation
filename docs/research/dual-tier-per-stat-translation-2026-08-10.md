# What travels between leagues: per-stat translation factors

**Date:** 2026-08-10 (corrected same day)
**Corpus:** `data/raw/proballers/*/*/player_stats_*.parquet` — 389,845 player-games
**Sample:** 2,212 same-season dual-tier pairs (≥8 games each side)

> ## RE-DERIVED 2026-08-26 — the numbers reproduce, the headline does not survive (ATI-2914)
>
> The non-reproducibility notice that stood here from 2026-08-18 is **discharged**.
> `scripts/build_perstat_translation.py` re-derives this page from the corpus on
> disk, in two arms, and the restricted arm rebuilds the 2026-08-10 corpus exactly
> (389,843 player-games against the 389,845 this note's spec states, delta 2; 2,212
> pairs, matching the pair count below to the unit).
>
> **1. The published table reproduces to four decimals.** Points 0.9395, rebounds
> 0.9361, assists 0.8806, PIR 0.8955 — the "minutes-weighted" column of the
> CORRECTION below, recovered exactly. Nothing on this page was invented.
>
> **2. But it was produced by `ratio_of_sums`, not the estimator §11 names.** The
> Estimator sensitivity table below labels the headline `exposure_weighted`. In the
> committed code's taxonomy that is a different estimator — a per-pair ratio
> weighted by the *thinner* side's minutes — and it returns assists **0.8735**, not
> 0.8806. The 0.8806 column is `ratio_of_sums`. §11's third row, labelled
> `ratio_of_sums` (0.8544 / 0.9283 / 0.9021), is in fact the original unweighted
> estimator the CORRECTION retracted — the "as published" column, under a wrong name.
> Only `mean_of_ratios` was labelled correctly. **§11 is corrected in place below.**
>
> **3. The primary estimator was never run on 2026-08-10, and it reverses a
> retraction.** On the same 2,212 pairs, `exposure_weighted` gives rebounds
> **0.9485** against points **0.9238** — a +0.025 gap. The CORRECTION below retracts
> "rebounding travels best" as an artifact of estimator choice, on the strength of
> `rebounds − points = −0.003` under `ratio_of_sums`. Under the estimator the
> committed code treats as primary, that retraction does not hold. Two of three
> estimators put rebounds top. **Neither claim is safe to quote.**
>
> **4. On the current corpus the finding collapses.** ATI-2895 added three leagues
> and ATI-2897 un-broke `greece-a1`, which had been scraping as a silent zero. The
> sample goes 2,212 → 5,039 pairs, and assists move **0.8735 → 0.9338** (+0.060)
> under the primary, or 0.8806 → 0.9224 (+0.042) under the published estimator.
> Current-corpus primary factors are points 0.9288, rebounds 0.9470, assists 0.9338,
> PIR 0.8965 — **assists now sit above points**, not 6 points below. "Assists are the
> outlier", and the commercial reading that a playmaker's assists should be
> discounted twice as hard as the rest of his line, **do not survive the larger
> corpus.** Under the published estimator the gap survives but shrinks by ~3.5x, to
> 0.017.
>
> **5. The bias caveat was attached to the wrong estimator.** The +0.0181 upward
> bias (ATI-2890) is `exposure_weighted`'s. These numbers are `ratio_of_sums`, whose
> null is 0.9998 on a placebo with exposure independent of talent — but which
> carries **+0.036** at this corpus's measured talent/minutes coupling, *worse* than
> the primary's. So the direction of the original caveat holds and its magnitude was
> understated, for a different reason than stated.
>
> **What is safe to quote from this page:** the method, the identification strategy,
> and the restricted-arm reproduction as a historical record. **Not** the assist
> discount, and not "rebounding travels best" or its retraction. Current-corpus
> figures are in `data/processed/translation/perstat_translation.json`; the
> per-league factors with intervals are in
> `docs/research/league-translation-factors-2026-08-15.md`, which supersedes this
> note for anything client-facing.

> ## CORRECTION — the estimator was never justified, and it mattered
>
> This file first reported factors as **ratio of summed per-36 rates**, which
> weights every player-pair equally regardless of minutes played. That is one of
> three defensible estimators and it was chosen without comment or a sensitivity
> check — the same trap this session filed as ATI-2842 against a different
> surface.
>
> | stat | as published | minutes-weighted |
> |---|---|---|
> | points | 0.902 | **0.939** |
> | rebounds | 0.928 | **0.936** |
> | assists | 0.854 | **0.881** |
> | PIR | 0.855 | **0.895** |
>
> **One headline claim does not survive.** "Rebounding travels best" was an
> artifact of the estimator: minutes-weighted, `rebounds − points = −0.003
> [−0.018, +0.012]` — indistinguishable. The claim that *assists travel worst*
> survives strongly and is the finding.
>
> The published CI of [0.060, 0.088] on the rebound-assist gap was a **sampling**
> interval conditional on one estimator. It does not cover the estimator choice,
> and the minutes-weighted point estimate of 0.055 falls outside it.
>
> Everything below is minutes-weighted. The unweighted figures are kept as a
> sensitivity, not deleted.

---

## The finding

> **Superseded — see items 3 and 4 of the notice at the top.** On the current
> corpus assists travel at 93% and sit *above* points; this sentence describes the
> 2026-08-10 corpus under one of three estimators. Kept as filed because the
> retraction has to stay visible next to what it retracts (METHOD.md, "Applying
> corrections").

**Everything travels at about 93–94% except playmaking, which travels at 88%.**

Same player, same season, one side continental (EuroLeague/EuroCup) and one side
domestic — so the player is his own control:

| Stat | Factor | 95% CI | Loses |
|---|---|---|---|
| Blocks/36 | 0.944 | [0.909, 0.979] | 5.6% |
| Points/36 | 0.939 | [0.930, 0.949] | 6.1% |
| Rebounds/36 | 0.936 | [0.924, 0.948] | 6.4% |
| Steals/36 | 0.929 | [0.912, 0.946] | 7.1% |
| **Assists/36** | **0.881** | **[0.864, 0.896]** | **11.9%** |
| PIR/36 | 0.895 | [0.887, 0.904] | 10.5% |

The gaps that matter, 2,000 bootstrap resamples:

| contrast | gap | 95% CI | p(gap ≤ 0) |
|---|---|---|---|
| points − assists | **+0.059** | [+0.040, +0.078] | <0.0001 |
| rebounds − assists | **+0.055** | [+0.036, +0.076] | <0.0001 |
| rebounds − points | −0.003 | [−0.018, +0.012] | — |

Assists are the outlier. Nothing else separates.

The commercial reading: a domestic playmaker's assists should be discounted
about **twice as hard** as everything else in his line. A single blended
"he'll lose ~10%" hides that.

> **Do not quote the paragraph above.** Re-derived 2026-08-26 on the full corpus,
> the assist discount is not twice anything: assists 0.9338, points 0.9288,
> rebounds 0.9470 under the primary estimator. The blended "he'll lose ~10%" this
> paragraph argues against is closer to right than the split it proposes.

---

*The block below is emitted by `src.research.Analysis.report()` (`docs/research/METHOD.md`). Note that **every** factor comes back LOAD-BEARING — the estimator spread exceeds the bootstrap interval for all three. Run on the first pass, this is what would have stopped the original headline.*

## Specification

**Question:** Do assists translate worse than other box stats when a player steps from a domestic league up to continental basketball?

**Unit:** one player-season with >=8 games in BOTH a continental (EuroLeague/EuroCup) and a domestic league — the player is his own control

| slot | value |
|---|---|
| estimator | exposure-weighted (minutes) — see sensitivity below |
| null | n/a: paired within-player design, no null reference needed |
| sample_filter | >=8 games each side |
| key | player_name + season  (Proballers has no stable person id) |
| unit | one player-season with >=8 games in BOTH a continental (EuroLeague/EuroCup) and a domestic league — the player is his own control |
| corpus | data/raw/proballers/*/*/player_stats_*.parquet, 389,845 player-games |
| pir_source | coalesce(pir, plus_minus) — ATI-2826 workaround, validated 3 ways |

## Estimator sensitivity

**Corrected 2026-08-26 (ATI-2914).** The table as filed attached the wrong
estimator names to two of the three columns — see item 2 of the notice at the top.
Re-derived by `scripts/build_perstat_translation.py --arm both`; names below are
the ones `scripts/build_league_factors.py::ESTIMATORS` actually uses.

**Restricted arm** — the 2026-08-10 corpus rebuilt (389,843 player-games, 2,212
pairs, 10 leagues). This is the reproduction:

| stat | `exposure_weighted` (PRIMARY) | `mean_of_ratios` | `ratio_of_sums` | spread |
|---|---|---|---|---|
| points | 0.9238 | 0.9126 | **0.9395** | 0.0269 |
| rebounds | 0.9485 | 0.9494 | **0.9361** | 0.0133 |
| assists | 0.8735 | 0.8943 | **0.8806** | 0.0208 |
| PIR | 0.8827 | 0.8873 | **0.8955** | 0.0128 |

Bold is the column this page published. Every factor is still **LOAD-BEARING** —
the estimator spread exceeds the bootstrap interval for all four, which is the
whole reason the estimator name mattered.

**Current arm** — the corpus as it stands (681,888 player-games, 5,039 pairs, 14
leagues). Not a reproduction; a new measurement:

| stat | `exposure_weighted` (PRIMARY) | `mean_of_ratios` | `ratio_of_sums` | spread |
|---|---|---|---|---|
| points | 0.9288 | 0.9233 | 0.9395 | 0.0161 |
| rebounds | 0.9470 | 0.9472 | 0.9327 | 0.0146 |
| assists | 0.9338 | 0.9500 | 0.9224 | 0.0276 |
| PIR | 0.8965 | 0.8973 | 0.9038 | 0.0073 |

**Restricted → current, primary estimator, corpus growth alone:** points +0.0050,
rebounds −0.0016, assists **+0.0602**, PIR +0.0138. The movement is almost entirely
in assists, and it is the size of the original finding.

Blocks and steals appear in the results table above but were **not** re-derived —
the generator reports the four stats this note leads with. Treat the blocks and
steals rows as un-rechecked.

## Threats and controls

| threat | control |
|---|---|
| estimator_choice | 3 estimators compared on 'points_factor' |
| name_collision | 287 of 2212 pairs (13.0%) involve a name used by >1 club in one league-season; excluding them moves the assist factor by 0.0011 |
| survivorship | entry requires >=8 games in both competitions in the same season; players who played only one side are absent by construction |
| sample_filter | >=15 games each side leaves 1220 pairs and moves the assist factor by 0.013 |

## Caveats, tested

| caveat | what happened |
|---|---|
| the >=8 game threshold may admit noisy low-minute seasons | re-ran at >=15 games each side (1220 pairs): assist factor 0.867 vs 0.881 — conclusion unchanged |

---

## Reproduction against the spec

| Measure | Continental | Domestic | Spec §3 |
|---|---|---|---|
| Pairs | 2,212 | | 2,174 (2,223 re-derived 10 Aug) |
| Points/36 | 13.78 | 15.28 | 14.02 / 15.44 |
| PIR/36 | 15.11 | 17.66 | 15.26 / 17.72 |

Within 2% on the pair count and within 0.2 on both rate columns. The PIR/36
cross-tier correlation comes out **0.649** against the spec's 0.464 — higher
because the spec's figure used only the ~739 pairs where PIR survived the parser
bug, and this run recovers the full corpus (below).

---

## Refutation battery

### 1. Opportunity — assists need a made field goal · PARTIAL HIT

If the team simply makes fewer shots in the harder league, assists fall
mechanically and there is no playmaking story.

| | Factor |
|---|---|
| Assists/36 | 0.881 |
| Made FG/36 | 0.943 |
| **Assists per made FG** | **0.934** |

*(This control was computed from summed raw counts, a proper aggregate, so it is
unaffected by the estimator correction.)*

**Roughly half of the assist loss is opportunity**, not playmaking. The residual
per-opportunity loss is real but the naive version overstates it. **Say the
adjusted version.**

### 2. Scorekeeping convention · REFUTED

If the gap were a convention artifact it would be a fixed offset unrelated to
league strength. Across the seven domestic leagues with n ≥ 40:

**corr(league PIR factor, league assist factor) = 0.715** (0.741 unweighted).

| League | n | PIR | Assists | Rebounds |
|---|---|---|---|---|
| spain-acb | 66 | 0.952 | 1.071 | 0.973 |
| france-pro-a | 445 | 0.922 | 0.898 | 0.947 |
| turkey-bsl | 628 | 0.903 | 0.880 | 0.929 |
| israel-bsl | 236 | 0.894 | 0.855 | 0.905 |
| vtb | 443 | 0.888 | 0.869 | 0.942 |
| lithuania-lkl | 311 | 0.848 | 0.850 | 0.946 |
| poland-plk | 83 | 0.791 | 0.839 | 0.917 |

The ordering reproduces the consensus league hierarchy — an unplanned external
validity check that passes under both estimators.

**Do not quote the ACB row.** An assist factor above 1.0 on n=66 is implausible,
and ACB has a known assist-ordering defect in its scraper (ATI-2837).

### 3. Replication · HOLDS, with a REVERSAL in the current season

Assists travel worse than **both** points and rebounds in **10 of 11 seasons**.
The exception is **2025-26, where the effect reverses**: assists 0.960 against
points 0.935 and rebounds 0.937.

*(The first version reported 2025-26 as a dead tie. Under the corrected
estimator it is a reversal — a stronger caveat, not a weaker one.)*

**If asked whether it is still true this year, the answer is no — this season it
runs the other way.** One season of 223 pairs is thin, but say it first.

### 4. Robustness checks that came back clean

- **Name collisions.** 439 names appear for more than one club within a single
  league-season; 287 pairs (13.0%) involve one. Excluding them moves every
  factor by ≤0.001.
- **Multi-stint players.** The pair builder keeps the largest-minutes domestic
  stint. Only 22 pairs (1.0%) discard a second qualifying stint.

---

## Data notes

**The PIR parser bug (ATI-2826) is still open and was worked around, not
avoided.** `pir` is null on ~48% of the corpus because the scraper wrote PIR
into `plus_minus`. The workaround `coalesce(pir, plus_minus)` was validated
directly rather than by heuristic — reconstructing PIR from box components gives:

| Test | corr |
|---|---|
| `pir` present: approx vs `pir` | 0.984 |
| same files: approx vs `plus_minus` | 0.316 |
| `pir` null: approx vs `plus_minus` | 0.960 |

Three-way separation, 189,808 rows recovered.

**`fg_made` / `fg_attempted` are two-pointers only**; threes are in `fg3_*`
(ATI-2842).

**Not pace-adjusted.** Pace differences scale all stats roughly together, so the
relative ordering survives, but the absolute factors carry a pace component.

## Scripts

`scripts/build_perstat_translation.py --arm both` → stdout plus
`data/processed/translation/perstat_translation.json`. It imports the pairing key,
the `>=8` games floor and all three estimators from
`scripts/build_league_factors.py` rather than restating them, so the only thing it
adds is the pooling: one factor per stat across every pair, which is what this note
reports. `--arm restricted` asserts the rebuilt corpus size and refuses to run if
it drifts, so a "reproduction" cannot silently become a measurement of something
else.

The four generators this section originally named were written in a session and
never committed; they are gone, and the record of that is in the notice at the top
of this file rather than here. What matters now is that the numbers above no longer
depend on them. METHOD.md §16 exists so that this does not recur.
