# AMENDMENT 11 to the 2026-27 prospective pre-registration — the publication may cite two exploratory BOUNDS, labelled as such (ACCEPTED)

**Date: 2026-09-06. Status: ACCEPTED by Amir on 2026-09-06** (instruction "do these 3 recommendations now", the first of which was to accept this amendment; recorded here as the dated acceptance, in its own commit, after the abstract v3 that cites the bound was merged as #2075 with the amendment still PROPOSED — the citation stood under the fallback rule below until this line). Nothing else in this document changed at acceptance. Originally proposed the same day, as below.
Written before the pre-lock signings collection and before any 2026-27 game. Base document is
`preregistration-2026-27-predictions.md`. Prior amendments: `-amendment-1-2026-08-21.md` …
`-amendment-10-2026-09-05.md`. Lock day per Amendment 7 Change 1; step 3b per Amendment 10.

## Specification

| Choice | This amendment | Alternatives considered |
|---|---|---|
| **Scope** | permits the publication (abstract, figures, manuscript) to cite two quantities from the exploratory note `translation-propositions-2026-09-04.md`: (i) the **league-only oracle bound** — the in-sample least-squares cell multiplier on the 674 scored walk-forward transfers, R² 0.381 / MAE 2.996 / MSE 14.79 — and (ii) the **reliability ceiling** of the destination-season target, ρ_Y ≈ 0.68–0.70 at the scored rows' exposure (Propositions 1–3) | keep both out of the publication until the 2027 refit (rejected: the oracle is the sharp form of the per-league-ties-a-constant null and answers the referee's first question); cite them without an amendment (rejected: the note itself says METHOD.md requires a dated additive amendment before an exploratory quantity enters the publication) |
| **What it changes** | nothing in §1–§12 of the base document. It adds a **labelling rule** for the publication: the oracle is drawn hatched and named a ceiling, never compared to an arm as if it were one; every R² quoted beside it is also quoted as a share of the reliability ceiling; both carry the word *exploratory* or *post hoc* in the sentence that cites them | — |
| **Constraint** | **No bar moves. No basis changes. No refusal rule changes.** The primary prediction, its interval, its baselines, the population, the refusal codes, the checkpoint dates and the verdict rule are exactly as Amendments 1–10 leave them. Neither bound is a success criterion for the 2026-27 set | — |
| **Traceability** | `scripts/instantiate_translation_propositions.py --out-dir <dir>` writes `propositions.json`; the committed copy is `docs/research/artifacts/translation-propositions-2026-09-04/propositions.json` (regenerated 2026-09-06 to a committed path because the 2026-09-04 artifact was written to a scratch directory that no longer exists — the fifth instance of that failure in this line). Fields: `P1_nested_predictors` (oracle), `P2_reliability` (ceiling), `P4_identification`. The figure generator reads the oracle from that file, never from a typed constant | — |

**Provenance, stated because a proposal that quotes numbers looks like one that computed them.** Every
figure above is read off the note; the regenerated artifact is diffed against the note in the PR that
carries this amendment, and any difference is recorded there before this amendment is accepted.

---

## Why an amendment, for two numbers that are not gates

The propositions note is exploratory: it was written after the walk-forward record, on the same 674
rows, and its own "Standing" paragraph says a dated additive amendment is owed before the league-only
oracle is cited in publication. This is that amendment. The value of the two bounds is that they turn
two empirical nulls into stated limits — *no predictor of the form source × league multiplier can
reach R² 0.381 on these transfers; the reliability of a single continental season caps every model
near 0.70* — and a limit stated with its derivation is more useful to a reader than a null stated
without one.

## What is and is not claimed

* Claimed: the two bounds are properties of the scored rows, computed by a committed generator, and
  are cited as ceilings.
* Not claimed: that any arm's distance from either bound is a pre-registered result; that the oracle
  is attainable out of sample; that the ceiling is a property of the estimator rather than of the
  target's game count (Proposition 3 gives the games needed).
* Not changed: the pre-registered holdout record (`translation-holdout-validation-2026-08-17.md`),
  the walk-forward record, the lock-day sequence, the evaluator.

## Acceptance

Acceptance is recorded by Amir as a dated line in this file's status paragraph, in its own commit,
before the abstract that cites the bounds is submitted. If not accepted, the abstract carries the
reliability ceiling only (it is in the 2026-08-17 holdout record, §Ceiling, and needs no amendment)
and the oracle stays manuscript material.
