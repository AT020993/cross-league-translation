# AMENDMENT 9 to the 2026-27 prospective pre-registration — P1 stays as written; its power is restated for both clauses, at the rehearsal's realised noise, and over the between-season variance; how a FAIL is read is fixed now

**Date: 2026-09-04. Recorded on ATI-2891 (Studies A and D, ATI-2961 / ATI-2964). Status: decided by Amir on 2026-09-04 (option "A" — keep the primary as written and state its true odds — over option "B", which would have re-based the primary on the pooled seven-season effect). Written after the 2025-26 dress rehearsal returned FAIL and before any 2026-27 data exists.** Base document is `preregistration-2026-27-predictions.md`. Prior amendments: `-amendment-1-2026-08-21.md` … `-amendment-8-2026-09-04.md`. Lock day per Amendment 7 Change 1.

## Specification

| Choice | This amendment | Alternatives considered |
|---|---|---|
| **Scope** | (1) the §7 power statement for P1, restated for the test as §8 actually defines it and at the noise the rehearsal measured; (2) how the publication reads a 2026-27 FAIL, fixed before the data; (3) what the mid-season S2 read is for | re-basing the primary claim on the pooled seven-season effect and Study D's forecast interval (option B — rejected by Amir: it is a change of primary made after a failed rehearsal, and a reader would read it as moving the goalposts however it was reasoned) |
| **Design** | the same normal-approximation power the Amendment 5 table used, with the threshold taken as the larger of the two P1 clauses, the SE inflated by the rehearsal's realised-over-scaled ratio, and, in a second column, integrated over the REML between-season variance from Study D | a simulation-based power (rejected — it would need a model of the season the pre-registration does not have; the closed form makes every input a named artifact field) |
| **Evidence admitted** | `data/processed/translation/walkforward_summary.json` (`pooled.delta_vs_b0`, `pooled.mae_b0`, `pooled.ci_b0`, `n_pooled`); the four rehearsal payloads `docs/research/artifacts/prelock-program-2026-09/rehearsal_eval_*.json`; `evidence_synthesis_summary.json` (`contrasts.per_league_vs_b0.reml_hksj.tau2`) | — |
| **Constraint** | **No threshold moves.** The 12.8 % margin, the paired-CI clause, the [0.90, 0.98] coverage band, the checkpoint dates (§9) and every verdict rule (§11) are unchanged. This amendment changes what the publication *says about* P1's odds and how it *reports* the outcome, nothing about how the outcome is computed | — |
| **Traceability** | `scripts/restate_prediction_power.py --p1-as-written` → `data/processed/predictions/power_p1_as_written_2026.json`; tests in `tests/test_scripts/test_restate_prediction_power.py` | — |

---

## Why now: the rehearsal found that the committed power line describes a weaker test than P1

The Amendment 5 table (and the rehearsal's own `power_rehearsal_2025.json`) computes `P(Z > 1.96 − effect/se_n)`: the power of the paired-CI clause alone. P1 as written (§8, Amendment 1 Change 4) is two clauses **and**-ed: the model's MAE at or below B0's by 12.8 %, **and** the paired CI excluding zero. The rehearsal (Study A) returned FAIL at every read with a realised contrast SE 1.19–1.33 × the one the table's scaling predicts, and Study D measured a between-season variance the table ignores. Three things to restate, one at a time.

## Change 1 — P1's power, restated

**Method** (`power_p1_as_written_2026.json::p1_as_written.method`). In contrast units Δ = MAE_B0 − MAE_model, the margin clause is Δ ≥ 0.128 · MAE_B0 = 0.497 and the CI clause is Δ ≥ 1.96 · SE_n; the test passes iff Δ̂ clears the larger. Power = 1 − Φ((threshold − effect) / √(SE_n² + τ²)), with effect +0.800 (`pooled.delta_vs_b0`), SE_n = SE_pooled · √(674 / n) (SE_pooled 0.103 from `pooled.ci_b0`), the inflated column multiplying SE_n by **1.33** (the largest realised/scaled ratio across the four rehearsal reads: 1.22, 1.19, 1.33, 1.29), and the predictive column adding **τ² = 0.0806** (Study D, REML).

| n | SE scaled | binding clause | power, CI clause only (the Amendment 5 table) | power, both clauses | both clauses, inflated SE | both clauses, inflated, predictive |
|---:|---:|---|---:|---:|---:|---:|
| 50 (Amendment 5's R9-reduced count) | 0.379 | CI | 0.56 | 0.56 | **0.35** | **0.37** |
| 66 (the rehearsal's primary population) | 0.329 | CI | 0.68 | 0.68 | 0.45 | 0.45 |
| 88 (the rehearsal's predicted count) | 0.285 | CI | 0.80 | 0.80 | 0.56 | 0.55 |
| 110 (Amendment 2's original count) | 0.255 | CI | 0.88 | 0.88 | 0.65 | 0.62 |

**Three readings, in order of what they change.**

1. **The clause gap changes no number at any plausible n.** The CI clause binds everywhere in the table; the margin clause would bind only above n ≈ 111, where 1.96 · SE_n drops under 0.497. The rehearsal's note was right that the power line covered one clause, and wrong to imply that the second clause lowered the figure. It does not, at these counts.
2. **The realised noise does.** At the rehearsal's inflation the CI-clause power at n = 50 is 0.35, not 0.56; at n = 88 it is 0.56, not 0.80. The rehearsal's SE ran a third above the scaled one on every read, and there is no reason a preseason 2026-27 collection will be quieter than an end-of-season 2025-26 one.
3. **Between-season variance moves the figure toward a coin flip from either side.** Integrating over τ² pulls power toward 0.5: up at n = 50 (0.35 → 0.37), down at n = 88 (0.56 → 0.55). That is the honest predictive statement: a season's own effect is drawn from a distribution whose 95 % interval spans roughly zero to +1.7, and the rehearsal's +0.38 sat inside it.

**The published power statement for 2026-27 is therefore:** *at the locked count the chance that a correct model passes P1 as written is about one in three at 50 players and just over one in two at 88, read off the rehearsal's noise and the six-season heterogeneity; a FAIL is the expected outcome about as often as a PASS.* The Amendment 5 sentence "only the B0 criterion is adequately powered" is superseded: no criterion is adequately powered by a single season at these counts.

## Change 2 — How a 2026-27 FAIL is read, fixed before the data

§11 stands: on FAIL, the negative result is published, not the projections. This amendment fixes what sits **beside** it, so that the reading is not chosen when the outcome is visible:

1. **The pooled seven-season update.** `scripts/synthesize_translation_evidence.py --add-season` appends 2026-27 as the seventh season; the publication reports the updated pooled Δ vs B0 with its HKSJ interval and the updated τ². This is the evidence about the *factors*; the single-season gate is the prospective test of the *pipeline*. Both are printed; neither replaces the other.
2. **Inside or outside the forecast.** Whether the 2026-27 Δ vs B0 falls inside the pre-committed prediction interval [−0.086, +1.712] (`evidence_synthesis_summary.json`) is stated in one sentence beside the verdict. Inside-and-FAIL reads "an ordinary below-average season for a working model"; outside-below reads "the model did worse than any season the walk-forward saw" and is the genuine negative result.
3. **The rehearsal's own reading is the template.** The FAIL on 2025-26 reproduced the walk-forward's 2025 fold (+11.2 % vs B0, under the margin, at pair level); the same fold-beside-read comparison is made for 2026-27 once the season exists.

None of this is a change of primary. P1 is the pre-registered success criterion, its verdict is computed exactly as before, and a FAIL is called a FAIL. What is fixed here is that the publication carries the power statement of Change 1 next to the verdict, and the two reads above next to it, so a reader can tell "small season" from "wrong model".

## Change 3 — The mid-season S2 read is a monitoring read

The rehearsal covered 0.88 at 31 January and 0.94 at 30 June with the same half-width. The conformal half-width is calibrated on full-season rows; at a mid-season checkpoint the scored players have fewer games, their per-36 outcome is noisier, and a fixed half-width under-covers (Study C rejected the games-scaled family on full-season data, correctly for the season-end read). §9 already makes the two checkpoints the same population observed twice. This amendment states, before 31 January 2027: an S2 miss at the mid-season read is **reported and expected**, and the S2 gate that enters the §11 verdict is the **end-of-season** read. P1, P2 and S1 are read at both checkpoints as §9 says.

---

## Provenance

| Item | Where it is fixed |
|---|---|
| power table, both clauses, inflation, τ² | `scripts/restate_prediction_power.py --p1-as-written --rehearsal … --evidence-synthesis …` → `data/processed/predictions/power_p1_as_written_2026.json` (`p1_as_written.at_n.<n>.*`, `.se_inflation_detail`, `.tau2`) |
| effect, MAE_B0, SE_pooled, n_pooled | `data/processed/translation/walkforward_summary.json::pooled.{delta_vs_b0, mae_b0, ci_b0}`, `n_pooled` |
| SE inflation ratios | the four `rehearsal_eval_*.json` payloads, `headline.contrasts.B0` and `headline.n_scored` |
| τ² and the forecast interval | `docs/research/artifacts/prelock-program-2026-09/evidence_synthesis_summary.json::contrasts.per_league_vs_b0.reml_hksj.{tau2, prediction_interval}` |
| the seventh-season update | `scripts/synthesize_translation_evidence.py --add-season` |
| the rehearsal's reading | `docs/research/dress-rehearsal-2025-26-2026-09.md`, rendered by `scripts/render_rehearsal_note.py` |
