# The corpus "PIR" is EFF, the destination side reproduces from the EuroLeague API, and 2025-26 is half-scraped — RESULT

**Date:** 2026-09-03 · **Ticket:** ATI-2807 (Sloan abstract), spawning ATI-2955 (label corrections) and ATI-2956 (scrape outage) · **Generator:** `scripts/compare_continental_sources.py`

Three findings from one question: *can the destination side of every translation pair be read from the league's own API instead of Proballers?*

1. **Every `pir` value in the Proballers corpus is EFF, not PIR** — the NBA efficiency formula (PTS+REB+AST+STL+BLK − missed FG − missed FT − TOV) in 100% of rows in 12 of 14 leagues, 99.99% and 99.35% in the other two (every remaining row within 1). The EuroLeague API's `Valuation` is full PIR (EFF + fouls received − fouls committed − blocks against) in 100% of rows. The scraper's header synonym set treats eff/pir/valuation/index as one column, and every note in the translation line, the pre-registration and the abstract draft has called the column PIR. **The numbers stand; the label is wrong everywhere.**
2. **With the same formula on both sides, the API-sourced destination reproduces the Proballers factors:** raw factor within one bootstrap SE on 18 of 19 cells at the 75-pair floor, all 19 within two, median |Δ| 0.005, EuroLeague ordering identical (ρ = 1.0). Player-season EFF/36 agrees at r = 0.991 on 4,364 matched player-seasons. The paper's destination outcomes can be first-party.
3. **The Proballers 2025-26 season is roughly half missing in eight leagues,** including both destination competitions: the daily scrape last wrote a game between 26 December 2025 and 9 January 2026, and proballers.com returns HTTP 403 to every automated fetch today. Every large residual disagreement in finding 2 is a 2025 game-count gap. The morning pipeline's own cross-validation has printed `euroleague 2025: 208 of 402 (51.7%)` daily and concluded "EXCELLENT".

## Specification

**Question:** Do the per-league translation factors survive replacing the continental (destination) side of each pair with first-party EuroLeague API box scores, and what is the `pir` column actually measuring?

**Unit:** one (player, season) pair observed with ≥8 games in a source league and ≥8 games in EuroLeague or EuroCup in the same season — the estimator's own unit, unchanged.

| slot | value | alternative printed |
|---|---|---|
| estimator | `scripts/build_league_factors.py` imported unchanged: `add_usage` → `build_pairs` → `estimate_table`, exposure-weighted primary, 2,000 cluster-bootstrap draws, seed 0, `min_pairs` 75 | raw (unpooled) factor beside the pooled one, because pooling collapsed in the restricted run (see Threats) |
| null | not applicable for finding 2 (a replication, not an effect); for finding 1 the null is "pir ≠ EFF", tested row by row | — |
| sample_filter | seasons 2016–2025 on all three corpora (the API holds no 2015-16); `stat=pir, era=all, sample=all_pairs` cells only | the shipped table includes 2015 |
| key | normalised `player_name + season`: diacritics stripped, generational suffix dropped, API `LAST, FIRST` reordered | Proballers raw names (the `PB` corpus), to isolate what normalisation alone does |
| corpora | **PB** Proballers both sides · **PB-norm** same with normalised names · **API** Proballers domestic + API continental, EFF computed from API components | **API-PIR** (negative control): API continental with official PIR, which must *move* the factors |
| destination metric | EFF on both sides, because that is what Proballers' `pir` column is | official PIR on the API side, as the negative control |

## Invariants

| check | detail | |
|---|---|---|
| API points reconcile | `2·FG2M + 3·FG3M + FTM == Points` on 103,767 of 103,767 rows after dropping 'Total' and DNP rows | ok |
| Proballers points reconcile | `2·fg_made + 3·fg3_made + ft_made == points` on 100% of rows in all 14 leagues — `fg_made`/`fg_attempted` are **two-point** figures | ok |
| API Valuation == PIR formula | 100% of rows | ok |
| name normalisation is inert on its own | PB → PB-norm moves every factor by ≤ 0.0001 and the pair count 4,436 → 4,437 | ok |
| negative control fires | official PIR on the destination side shifts the 19 raw factors by **−0.041** on average; the script asserts < −0.02 | ok |

## Finding 1 — what the `pir` column is

Per league, share of rows where `pir` equals the EFF formula, both trees, all seasons:

| league | rows | pir == EFF | within 1 of EFF |
|---|---:|---:|---:|
| turkey-bsl | 48,041 | 0.9935 | 0.9935 |
| germany-bbl | 64,595 | 0.9999 | 1.0000 |
| every other league (12) | 34,213 – 71,886 each | 1.0000 | 1.0000 |

EFF minus fouls committed matches 13–21% of rows (chance agreement when fouls are zero); nothing else fits. On the API side, `Valuation` equals EFF on only 28.7% of rows and the PIR formula on 100%. The per-game gap is small — API mean PIR 7.69 vs EFF 7.92 — but it is systematic, and it is exactly the −0.041 the negative control measures once it reaches a ratio.

**Consequence.** The translation factors are ratios of EFF to EFF; nothing in them changes. What changes is every sentence that says PIR: the factors note, the holdout note, the pre-registration's prediction target, `docs/gotchas/data-libraries.md`, the scraper docstring, and the abstract draft (corrected in this change). The correction is a label, made in place with the retraction visible, and it moves no threshold (METHOD.md §8). Amendment 3 to the pre-registration carries it. **PIR is a defined, published EuroLeague statistic; a referee who computes it from the API and finds a different number would be right.**

## Finding 2 — the destination side reproduces from the API

Player-season agreement on the destination side, ≥8 games, same normalised key:

| | value |
|---|---:|
| qualifying player-seasons, Proballers / API | 4,725 / 4,785 |
| matched | 4,364 (92.4% of Proballers) |
| unmatched: Proballers-only / API-only | 361 / 421 |
| EFF/36 correlation on matched | **0.9911** |
| mean difference (API − Proballers), MAE | −0.04, 0.26 EFF/36 |
| games-per-season difference, MAE | 1.06 |

Factors, `stat=pir, era=all, sample=all_pairs`, seasons 2016–2025, cells with ≥75 pairs in both corpora (19 of 22):

| | value |
|---|---:|
| pairs, PB / API | 4,436 / 4,137 |
| raw |Δfactor|: median / max | 0.0050 / 0.0325 |
| raw mean Δ (API − PB) | −0.0016 |
| cells within 1 SE / 2 SE (of the PB cell's cluster-bootstrap SE) | **18 / 19** and 19 / 19 |
| ordering, Spearman ρ, EuroLeague / EuroCup | **1.00** / 0.87 |
| negative control: raw mean Δ with official PIR on the API side | **−0.041** |

The one cell outside 1 SE is vtb → EuroCup (−0.0325, −1.49 SE); Greece → EuroCup (+0.025) has 53 API pairs and sits below the floor. Per-cell values are in `continental_source_check_cells.csv` from the run.

**What the residual is.** The 7.6% of Proballers player-seasons with no API match and the game-count gaps are almost entirely season 2025: every one of the eight largest per-player disagreements is a 2025 row where the API holds 1.5–2.5× the games (Hazer 17 vs 33, Fournier 17 vs 39). That is finding 3, not a source disagreement. The 300 fewer pairs in the API corpus are the same thing seen from the pairing side — with 2025 destination seasons complete, more 2025 domestic sides exist to pair with only in Proballers, which is itself half-scraped.

## Finding 3 — 2025-26 is half-scraped, and the pipeline said so every day

Distinct games in the Proballers corpus, seasons 2024 vs 2025, and the last 2025 game written:

| league | 2024 | 2025 | last 2025 game | API 2025 |
|---|---:|---:|---|---:|
| euroleague | 330 | 207 | 2026-01-09 | 402 |
| eurocup | 196 | 130 | 2026-01-07 | 195 |
| aba-league | 240 | 103 | 2026-01-05 | — |
| france-pro-a | 240 | 109 | 2025-12-26 | — |
| lithuania-lkl | 180 | 59 | 2026-01-04 | — |
| poland-plk | 240 | 114 | 2026-01-09 | — |
| turkey-bsl | 239 | 104 | 2026-01-03 | — |
| vtb | 264 | 105 | 2026-01-08 | — |
| germany-bbl, greece-a1, italy-lba | — | complete | May 2026 | scraped in full by ATI-2895 in August |
| israel-bsl, spain-acb, bcl | — | complete | May 2026 | — |

`curl` to a Proballers schedule page returns 403 today under a browser and a python-requests user agent. The morning pipeline's cross-validation report (`logs/morning_pipeline_2026-09-03.log`) prints `euroleague | 2025 | 208 | 402 | 51.7%` and `eurocup | 2025 | 130 | 195 | 60.0%` and then *"Data quality is EXCELLENT. Both sources largely agree."* — its recommendation reads score accuracy, not match rate. Filed as ATI-2956 with the contamination list; the short version is that the 2026-27 prediction set's *source* seasons are half-seasons for six domestic leagues, and must not be locked without either completing them or printing per-league completeness beside every prediction.

## Threats and controls

| threat | control |
|---|---|
| name normalisation changes the pairing, not the source | PB vs PB-norm: max |Δfactor| 0.0001, pairs 4,436 vs 4,437 — inert |
| metric definition differs between sources | tested row-by-row on both sides (finding 1); the like-for-like corpus uses EFF on both; the mixed corpus is the negative control and moves the factors by −0.041 |
| the comparison could not fail | negative control asserted in-script (`ctrl_shift < -0.02`) |
| game-count mismatch drives the residual | the eight largest disagreements are all 2025 rows with 1.5–2.5× the games on the API side; quantified in finding 3 rather than left as a caveat |
| pooling collapse hides a per-league difference | restricting to 2016–2025 leaves poland-plk → EuroLeague at n = 2 with SE 0.21, which zeroes τ for the whole EuroLeague block (method-of-moments τ² = var(factors) − mean(SE²)); the note therefore compares **raw** factors. The shipped table (era=all, with 2015) has τ = 0.040 / 0.062 and is not collapsed. The fragility — one thin cell can collapse a block because the 75-pair refusal runs *after* pooling — is recorded on ATI-2955, not fixed here |
| API rows that are not player-games | per-team 'Total' rows and DNP rows dropped: 134,241 → 103,767; points reconciliation 0 mismatches after |

## Limitations

- The API holds no 2015-16, so the comparison is on 2016–2025; the shipped factors include 2015.
- 361 Proballers player-seasons (7.6%) have no API match under this key. They are not resolved here; the 2025 game-count gap accounts for the largest, and the rest are name-form differences the normaliser does not cover.
- Domestic leagues have no first-party alternative in this corpus; finding 2 licenses the destination side only.

## What this licenses

- **Supported:** the destination side of every pair can be read from the EuroLeague API with EFF computed from components, and the factors reproduce within one SE on 18 of 19 cells with the ordering intact. The paper's outcome variable can be first-party.
- **Supported:** the corpus metric is EFF; every "PIR" label in the translation line is a mislabel of a correct number.
- **Not supported:** anything computed on Proballers 2025-26 for the eight blocked leagues as a full season.
- **Not tested:** whether EFF translates differently from PIR. Nothing here compares the two as targets.

## Scripts

`scripts/compare_continental_sources.py --dest-metric eff` prints every figure above and writes `continental_source_check_cells.csv`, `continental_source_check.json` and `pir_column_reconciliation_by_league.csv` to `--out-dir`. `--dest-metric pir` is the negative control's corpus; `--reconcile-only` prints finding 1 and stops. The estimator is imported from `scripts/build_league_factors.py` and not modified.

## Conclusion

The Proballers `pir` column is the NBA efficiency formula on every row of every league [control: reconcile_pir_column], so the translation factors are ratios of EFF and every PIR label in this line is wrong while every number stands. Read from the EuroLeague API with the same formula, the destination side reproduces the factors within one bootstrap SE on 18 of 19 cells [control: negative_control]. The residual disagreement is the scrape, not the source: Proballers stopped writing games for eight leagues in the first week of January 2026 [data: games_per_season_by_league].
