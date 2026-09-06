# AMENDMENT 10 to the 2026-27 prospective pre-registration — a dynamic-ability arm scored BESIDE the primary (PROPOSED)

**Date: 2026-09-05. Status: ACCEPTED by Amir on 2026-09-05** (instruction "Do your recommendation",
given after reading the PARTIAL result; recorded here as the dated acceptance the Amendment 3 →
Amendment 4 pattern requires, in its own commit before any implementation landed). Nothing else in
this document changed at acceptance. Originally proposed the same day, as below. Written after the
pre-registered dynamic-ability test returned PARTIAL
(`translation-dynamic-ability-result-2026-09-05.md`; pre-registration a62be01e) and before the
pre-lock signings collection and before any 2026-27 game. Base document is
`preregistration-2026-27-predictions.md`. Prior amendments: `-amendment-1-2026-08-21.md` …
`-amendment-9-2026-09-04.md`. Lock day per Amendment 7 Change 1.

## Specification

| Choice | This amendment | Alternatives considered |
|---|---|---|
| **Scope** | add ONE secondary arm to the scored set: the dynamic (random-walk ability) model of `scripts/validate_translation_dynamic.py`, **point predictions only**, scored on the same population, at the same checkpoints, against the same realised outcomes as the primary | making it the basis (rejected — the gate returned PARTIAL; changing the basis on a PARTIAL is the move Amendment 9 refused for P1) · carrying an interval for it (rejected — the lock's conformal interval was calibrated on `per_league` residuals and does not transfer; no interval is claimed) |
| **What it changes** | §5 (the baselines / comparators) gains a row: `dynamic_ability`. §6 metrics unchanged. §8 success criteria **unchanged** — this arm has no criterion of its own; it is *reported* against the primary and against B0 with the same paired cluster bootstrap | a pre-registered criterion for the arm (rejected — at n ≈ 50 predictions its power against the primary is far below 0.5; a criterion that cannot pass is not a criterion, per the readiness-gate lesson) |
| **Constraint** | **No bar moves. No basis changes. No refusal rule changes.** The primary prediction, its interval, its baselines B0 / B1b / B1c, the population, the refusal codes and the checkpoint dates are exactly as Amendments 1–9 leave them | — |
| **Inputs the arm needs per import** | the player's full stint history in the corpus (joined by `pairing_key`, as `build_translation_predictions.py` already joins the source season), source league, destination competition, prediction season. All are available from the corpus and the prediction row (`person_code`, `name`, `origin_league`, `destination`, `source_season`) | — |
| **Traceability** | a committed generator writes `dynamic_predictions_<season>.json` beside `translation_predictions_<season>.json`, one row per scored import, keyed by `person_code` + `pairing_key`, produced from the same collection the primary uses and at the same lock time; the evaluator reads both | a column inside the primary artifact (rejected — the primary artifact's schema is under the pre-registration's own guards; a second file leaves it untouched) |

**Provenance, stated because a proposal that quotes numbers looks like one that computed them.** Every
figure below is read off `dynamic_summary.json` via the result note; none is new.

---

## Why propose it now, on a PARTIAL

The pre-registration said in advance: PASS or PARTIAL → propose this amendment; FAIL → file it as a
record only. It returned PARTIAL (Δ = +0.081, CI [−0.029, +0.182], n = 547), the likeliest outcome
at the stated power (~0.66 at the heuristic's gain). The retrospective rows are exhausted — they have
been read by the static study, the heuristic, and now this test — so **the prospective set is the
only place the question "does drift beat the two-stage basis?" can still be answered cleanly**, and
it can only be answered there if the arm's predictions are on record before tip-off.

## What is and is not claimed

* Claimed: the arm is a **declared comparator**, like B1c. Its predictions are locked with the
  primary's and scored at S1 and S2 beside them. Its result is reported with the same paired cluster
  bootstrap, and the publication may say whichever way it comes out.
* Not claimed: any success criterion for it; any change to how P1 or the primary's verdict is read;
  any interval. At n ≈ 50 predictions and the rehearsal's realised noise the arm's power against the
  primary is small; the honest sentence is "the dynamic arm was on record and here is what it did".

## What the generator must do before the lock (if accepted)

1. Extend `scripts/validate_translation_dynamic.py` with a `--predict <season> --signings <path>`
   mode that fits every component on seasons < the prediction season (the same code path the
   walk-forward uses for a fold) and writes `data/processed/predictions/dynamic_predictions_<season>.json`.
2. Emit exactly the primary artifact's population: an import the primary refuses is not scored by
   this arm either (the refusal codes are the population's, not the arm's).
3. Record `q`, `σ²`, `τ²`, `μ`, the fallback share and the flag states in the artifact header.
4. Extend the S1/S2 evaluator to read the second file and report the arm beside B1c.
5. Tests: the predict-mode population equals the primary artifact's `person_code` set; the
   components in the header match a fresh fit; no row of the prediction season enters the fit.

None of this is done here; **the amendment is a proposal and the lock pipeline is untouched.**

## Implementation — done 2026-09-05, after acceptance (same PR, later commits)

1. `scripts/validate_translation_dynamic.py --predict <season> --primary data/processed/predictions/translation_predictions_<season>.json --built-at <date>` writes `data/processed/predictions/dynamic_predictions_<season>.json`: one row per primary prediction (asserted equal by `person_code`), keyed by `person_code` + `pairing_key`, header carrying the primary's `status` / `built_at` / collection, the fitted components with every floor flag, the fallback share, and this amendment's path. No interval fields.
2. `scripts/evaluate_translation_predictions.py … --secondary data/processed/predictions/dynamic_predictions_<season>.json` adds arm `dynamic` to `metrics` and two contrasts (`dynamic` = model vs dynamic, `dynamic_vs_B0`); gates and verdict are untouched — a test asserts they are byte-identical with and without the flag; a secondary file missing any primary `person_code` is refused.
3. **Lock day (Amendment 7 Change 1 step 3 gains a step 3b):** immediately after the primary builder runs on the lock collection, run step 1 with the same `--built-at` on the artifact it just wrote, and commit both files together. S1/S2 evaluations pass `--secondary`.
4. Rehearsal (2025-26, primary artifact of 2026-09-04, 88 predictions, 68 scored at ≥8 games): dynamic MAE 3.480 vs model 3.476, model-vs-dynamic +0.004 CI [−0.317, +0.336] — a tie, read from `evaluate_translation_predictions.py --secondary` on `realised_outcomes_2025.json`; the rehearsal's FAIL verdict (Amendment 9) is unchanged by the flag. A rehearsal read, not evidence.
5. Draft artifacts committed beside the primary drafts: `dynamic_predictions_2026.json` (50 rows on the 2026-08-21 collection's primary, 0 fallbacks; q 2.69, σ² 127.3, τ² 21.1, μ 10.83) and `dynamic_predictions_2025.json` (88 rows, 0 fallbacks). Both say `draft`; the lock-day rebuild replaces the 2026 file.

## Sequence and deadline

Acceptance must be recorded before lock day (Amendment 7 Change 1: the first READY morning or
22 September). If it is not recorded by then, this amendment lapses for 2026-27 and the arm's next
clean test is the 2027 refit.

## What is NOT changed

Everything. §2 population, §3 refusals, §4 basis, §6 metrics, §7 power, §8 criteria, §9
checkpoints, §11 verdict rule, Amendments 1–9.

## Provenance

Source figures: `translation-dynamic-ability-result-2026-09-05.md` (`dynamic_summary.json`:
`selection.contrasts.dyn_vs_combined`, `verdict`). Pre-registration:
`translation-dynamic-ability-preregistration-2026-09-05.md` at a62be01e. Populated-inputs check:
`data/processed/predictions/translation_predictions_2026.json` row schema (read 2026-09-05).
