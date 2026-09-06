# DECISION — which publication branch the 2026-27 pre-registration takes

**Date: 2026-08-27. Ticket: ATI-2923. Status: recorded, binding on the lock.**
Base document: `preregistration-2026-27-predictions.md`. Lock deadline **24 September 2026**, tip-off.

**Branch taken: PARTIAL → publish the predictions, with the scope narrowed to the passing claims and
G4 named in the publication body.**

> **This document changes nothing.** It is a dated record of which of §11's three already-committed
> branches applies, written while the record still costs something to make — before the pre-lock
> signings collection exists (ATI-2917, blocked upstream) and before any 2026-27 game is played. It
> adds no bar, moves no bar, and re-scores nothing. A decision recorded only in a ticket tracker has
> no timestamp a reader outside this project can verify, which is the whole reason the
> pre-registration lives in git; this closes that gap and nothing else.

## Specification

| Choice | This document | Alternatives considered |
|---|---|---|
| **Unit** | one decision: which §11 branch the ATI-2799 verdict selects | one decision per sub-gate (rejected — §11 branches on the verdict, not gate-by-gate) |
| **Population** | the six pre-registered gates G1–G6 of `translation-holdout-preregistration-2026-08-17.md` | the walk-forward re-test as a co-primary (rejected — Amendment 1 admits it as evidence, not as a gate) |
| **Estimator** | **none — no computation is performed here.** Every figure below is read off `translation-holdout-validation-2026-08-17.md` | recomputing from `scripts/validate_translation_holdout.py` (rejected — re-running a completed gate is exactly what METHOD.md §8 forbids, and ATI-2923 puts it out of scope) |
| **Null reference** | not applicable; no claim is tested here | — |
| **Sample filter** | not applicable; no rows are selected here | — |
| **Aggregation key** | not applicable | — |
| **Uncertainty** | intervals quoted are the source document's paired cluster bootstrap on destination club-season, 4,000 draws, seed 0 | — |

**Provenance, stated because a decision note that quotes numbers looks like a note that computed
them.** No number in this document is new. Each is quoted from the validation record with its sign,
interval and comparator intact; none is rounded, re-derived, or restated in a different unit. The
executable form of every figure is `scripts/validate_translation_holdout.py`, whose output is
`translation-holdout-validation-2026-08-17.md`.

---

## 1. What the gate returned

Reproduced bit-identically on 2026-08-21.

| gate | bar | measured | verdict |
|---|---|---|---|
| G1 | model MAE ≤ 0.95 × B0 MAE = 3.8427 | 3.3325 — 17.6% better | **PASS** |
| G2 | paired cluster-bootstrap CI on the B0 gap excludes 0 | +0.7124, 95% CI [+0.4731, +0.9859] | **PASS** |
| G3 | R² ≥ 0.20 | +0.3156 | **PASS** |
| **G4** | beats **both** B0 and B1b on MAE **and** R² | R² yes (0.3156 vs 0.2926); MAE **no** (3.3325 vs 3.3275) | **FAIL** |
| G5 | LOLO MAE ≤ 0.95 × B0 MAE = 3.6758 | 3.2898; ΔMAE +0.5795 [+0.4825, +0.6799] | **PASS** |
| G6 | ≥75% of leagues with n ≥ 20 beat B0 | 10 of 10 | **PASS** |

**G4 fails as a tie, not a loss.** ΔMAE **−0.0050, 95% CI ~~[−0.2359, +0.2297]~~ [−0.2297, +0.2397]** *(interval corrected 2026-09-04 to the committed generator, ATI-2955; point estimate unchanged, still spans zero)* against B1b — a
baseline that multiplies last season's rate by the single constant **0.8655**. The model wins R²
(0.3156 vs 0.2926) and RMSE (4.2655 vs 4.3366). **The bar was not moved and G4 is not re-scored**
(METHOD.md §8).

> **Addendum 2026-09-04 (Amendment 5 accepted; ATI-2955 / ATI-2957).** The same script on the
> API-side corpus the lock now uses returns a G4 point *pass*: ΔMAE **+0.0429** against B1b, with the
> committed paired cluster bootstrap giving **95% CI [−0.1331, +0.2224]** — an interval that spans
> zero, so the same bootstrap cannot separate it from a tie. It is a second record beside the
> 2026-08-17 verdict, not a re-score, and it does not move this branch: both records say the
> per-league model and one fitted constant are not separable on MAE at n = 231. Source:
> `translation-refit-api-destination-2026-09-04.md` Finding 3; `validation_summary.json:
> armA_g4_b1b`.

## 2. The branch, and where it was already fixed

§11 of the base document carries three branches, not two. The PARTIAL branch was added by
`preregistration-2026-27-amendment-1-2026-08-21.md` Change 1 and reads:

> **On PARTIAL** (the pooled MAE and generalisation gates pass; a baseline-superiority sub-gate
> fails or ties): **publish predictions, with the scope narrowed to the passing claims and the
> failing sub-gate named in the publication body — not a footnote.** The prediction set is built
> exactly as under PASS. The publication must state which sub-gate failed, its point estimate and
> interval, and what it implies the model cannot claim.

G1, G2, G3 (pooled MAE) and G5, G6 (generalisation) pass; G4, a baseline-superiority sub-gate, ties.
**The verdict selects PARTIAL, and PARTIAL says publish.** No discretion is exercised here beyond
reading the rule against the verdict.

**Why publishing is the defensible reading and not the convenient one.** A tie on one
baseline-superiority sub-gate bounds the *claim*, not the *usefulness*. What survives is specific:
translation beats untranslated production out-of-sample by 17.6% of MAE with an interval excluding
zero; the factors generalise to a league entirely absent from the fit, 10 of 10; and the per-league
ordering predicts realised transfer outcomes at ~~ρ = +0.688, permutation p = 0.0017~~ ρ = +0.644, permutation p = 0.0052 *(corrected 2026-09-04, ATI-2955; +0.635 to +0.782 across five cell-ratio definitions)*. Withholding on a
−0.005 margin the study's own bootstrap cannot separate from zero would suppress every gate the study
*was* powered for.

## 3. What the publication must therefore carry, in the body

1. **G4 failed.** The model ties a one-constant baseline on MAE (−0.005, CI ~~[−0.236, +0.230]~~ [−0.230, +0.240], corrected 2026-09-04) while
   beating it on R² and RMSE. *Added 2026-09-04:* the API-side second record's G4 point pass
   (+0.043, CI [−0.133, +0.222]) is reported beside it as the same tie the other way, never as a
   pass.
2. **Per-league resolution does not earn itself on point prediction.** 22 factors versus a single
   global scalar: ΔMAE **+0.0564, CI [−0.1336, +0.2460]** — indistinguishable from no improvement.
   This is the sharper negative and it is *not* G4. It must not be omitted on the grounds that only
   G4 was a formal gate.
3. **The full nested ladder, not only the win over B0** — raw rate (0 params, MAE 4.0449) → minutes
   constant B1b (1, 3.3275) → one global translation factor (1, 3.3889) → two per-destination factors
   (2, 3.4037) → the published 22-factor table (22, 3.3325). A reader should be able to see directly
   that we match a constant on MAE while beating it on R² and RMSE. A validation section that shows
   only wins reads as marketing and gets discounted entirely.
4. **What the per-league table is for:** ranking which leagues translate better, not point levels.
5. **Only germany-bbl** clears both the n ≥ 20 verdict floor and its own 80%-power detection floor.
   The per-league breakdown is descriptive; it is not ten independent findings.
6. **Intervals of roughly ±8 PIR/36**, never the ±0.03 factor SE — the factor-SE-only interval covers
   **9.5%** of outcomes, overstating precision by about an order of magnitude.

## 4. The post-hoc element, disclosed rather than argued away

**The bars are clean.** No threshold moved. §8's 12.8% B0 margin is untouched; Amendment 1 Change 4
*raised* the bar by adding B1b as a second primary; G4 was not re-scored. METHOD.md §8 governs
thresholds and none moved.

**The branch is not.** The gate ran 2026-08-17. Amendment 1 is dated 2026-08-21 and exists precisely
because the gate returned a verdict §11 did not cover. **The publish-versus-withhold rule for a tie
was therefore written with the tie already in hand.**

This is a real limitation and belongs beside the verdict in the publication, not in a methods
appendix. A pre-registration can be clean on every bar and still post-hoc on its verdict *rule*, and
a reader who discovers that unaided is entitled to discount everything else in the document.

**Rule adopted for the next pre-registration:** enumerate a branch for **ties and split arms**, not
only pass and fail. A binary rule over a continuous margin has an undefined middle by construction,
and the middle is where results land. Both pre-registrations in this line defined PARTIAL — and they
defined it *differently*: the holdout document as "Arm A passes and Arm B fails, or the converse",
the predictions document as "a baseline-superiority sub-gate fails or ties". Two documents using one
word for two conditions is how the gap opened.

## 5. What this does not decide

* The player set. The pre-lock collection is blocked upstream on EuroCup roster publication
  (ATI-2917); the readiness gate measured cleanly on 2026-08-27 and returned NOT READY.
* Any threshold, margin, metric or baseline. All remain as committed.
* The holdout pre-registration, which is not amended.

## Related documents

* `preregistration-2026-27-predictions.md` — the base document; §11 is the operative rule.
* `preregistration-2026-27-amendment-1-2026-08-21.md` — Change 1 defines the PARTIAL branch.
* `preregistration-2026-27-amendment-2-2026-08-25.md` — prediction basis and the dated-count rule.
* `translation-holdout-preregistration-2026-08-17.md` — the gates G1–G6 as written before the fit.
* `translation-holdout-validation-2026-08-17.md` — the verdict every figure above is quoted from.
* `translation-walkforward-per-league-2026-08-21.md` — the evidence admitted by Amendment 1.
* `METHOD.md` — §8 (never move a threshold), and the corrections rule this document follows.
