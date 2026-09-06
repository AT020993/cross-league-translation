# AMENDMENT 1 to the 2026-27 prospective pre-registration

**Date: 2026-08-21. Ticket: ATI-2891. Status: proposed, not yet locked.** The base document is
`preregistration-2026-27-predictions.md` (drafted 2026-08-17, seven elements fixed). Lock deadline is
**24 September 2026**, tip-off.

## Specification

| Choice | This amendment | Alternatives considered |
|---|---|---|
| **Scope** | four numbered changes to the base document; everything not named here is unchanged | full rewrite (rejected — most of the document survived re-measurement) |
| **Evidence admitted** | ATI-2799 held-out gate (n=231) and the ATI-2891 walk-forward re-test (n=719, 6 windows) | ATI-2799 alone (insufficient — its key null was a power limit) |
| **Constraint** | no change may relax a bar or re-score a completed gate (`METHOD.md` §8) | — |
| **Traceability** | each change names the measurement that forces it and the document it lives in | — |

**Why an amendment and not an edit.** The base document's value is that its bars were fixed before
the outcome was known. Silently editing it would destroy exactly that. This is a dated, additive
amendment; the original stays as written.

---

## Change 1 — Define the PARTIAL branch. **This is the blocking one.**

**Problem.** §11 specifies `On PASS` and `On FAIL`. The ATI-2799 gate returned **neither**: five of
six sub-gates passed (G1, G2, G3, G5, G6) and **G4 failed** — the model tied a single-constant
baseline at −0.005 MAE, CI [−0.236, +0.230]. §11 has no branch for that, so as written this document
cannot be executed.

**Change.** Add to §11:

> **On PARTIAL** (the pooled MAE and generalisation gates pass; a baseline-superiority sub-gate
> fails or ties): **publish predictions, with the scope narrowed to the passing claims and the
> failing sub-gate named in the publication body — not a footnote.** The prediction set is built
> exactly as under PASS. The publication must state which sub-gate failed, its point estimate and
> interval, and what it implies the model cannot claim.

**Why publish rather than withhold.** A tie against a one-constant baseline bounds the *claim*, not
the *usefulness*: the model still beat untranslated production by 17.6% of MAE with a bootstrap
interval excluding zero, and still generalised to a league entirely absent from the fit (10 of 10).
Withholding on a tied sub-gate would suppress a result that passed every gate it was powered for.

**What it forbids.** No re-scoring of ATI-2799 to convert G4. The verdict is PARTIAL and the
publication says so.

---

## Change 2 — Refit the level correction on prior seasons only; **keep the per-league basis**

**Problem, part one.** §4 locks `K_LAG = 0.9473`, described as fitted on 2016-2025 newcomer cohorts.
ATI-2799 scored destination seasons 2024 and 2025 — **inside that window.** As locked, the constant
has seen the seasons it would be evaluated on.

**Change.** §4's constant becomes a **rule**:

> `K_LAG` is the median realised ratio of observed to predicted per-36 PIR, computed on newcomer
> cohorts from seasons **strictly before the prediction season**. For 2026-27 this is seasons
> ≤ 2025. The value is computed once, recorded here before tip-off, and never refit afterwards.

Measured across six independent refits (each using only prior seasons), by prediction season:

| 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|
| 0.9368 | 0.9309 | 0.9285 | 0.9305 | 0.9313 | 0.9304 |

Range **0.9285–0.9368**. The locked 0.9473 sits **outside** that range, consistent with it having
been fitted partly on the evaluation seasons.

**Problem, part two — and this reverses an earlier recommendation.** ATI-2799 found per-league
factors indistinguishable from one global scalar (+0.056 MAE, CI [−0.134, +0.246], n = 231) and I
recommended pre-registering the ordering plus one global level. **That recommendation is withdrawn.**
Re-tested walk-forward over six independent windows (`translation-walkforward-per-league-2026-08-21.md`):

| | MAE | R² |
|---|---|---|
| 22 per-league factors | **3.1459** | **+0.3597** |
| one global scalar | 3.3934 | +0.2682 |
| untranslated | 3.9676 | — |

Per-league wins in **6 of 6 seasons** (sign test p = 0.0156), pooled **+0.2475, CI [+0.1701,
+0.3283]**, n = 719. Two controls: permuting the league→multiplier assignment gives **0 of 200**
draws reaching the observed gain, and removing the level correction entirely still leaves it
separable (**+0.1527, CI [+0.0662, +0.2464]**), so the advantage is the league mapping and not the
new term.

**Change.** §4's prediction basis stays the **22-cell per-league table**. No change to the form.

---

## Change 3 — State the interval's realised coverage, do not call it 95%

**Problem.** §4 presents `[point × 0.4986, point × 1.6392]` as a 95% interval. ATI-2799 measured its
realised held-out coverage at **0.9221**.

**Change.** §4 keeps the construction — it is the right one, and the alternative is far worse (a
factor-SE-only interval covers **0.0952**) — but relabels it:

> Intervals are **nominal 95%, realised 0.922** on held-out transfers (ATI-2799 G7). Every published
> interval carries the realised figure. No channel describes them as 95% without it.

The locked secondary criterion "interval coverage in [0.90, 0.98]" is **unchanged** — 0.922 sits
inside it, so this is a labelling correction, not a moved bar.

---

## Change 4 — Add the one-constant baseline to the success criterion

**Problem.** §8's primary criterion is "beat B0 by ≥12.8% of B0's MAE." B0 is untranslated
production — the weak baseline. G4 is precisely where ATI-2799 tied, and pre-registering only the B0
margin would repeat the criticism the gate surfaced.

**Change.** §8 gains a **second primary criterion**:

> The model must also beat **B1b** — the source-season rate times a single constant fitted to
> minimise error on the scored set itself — on MAE, with a paired cluster-bootstrap interval
> excluding zero.

**Why this is a fair bar rather than a stretch.** On the pooled walk-forward the model beats B1b by
**+0.2014, CI [+0.1096, +0.3011]**, where B1b's constant is refitted per season *to the very players
being scored* — a deliberately oracle-advantaged comparator. The bar is set at a margin the model has
demonstrated out-of-sample, not an aspiration.

**Scoring.** Both primaries must pass for a PASS. B0 passing and B1b failing is a **PARTIAL** under
Change 1. This raises the bar; §8's existing 12.8% B0 margin is untouched.

---

## Power — the limit that must be published with the predictions

The prospective set is **~79 predictable / ~69 scored** players (base document §10.1). The
walk-forward establishes the per-league effect on **pooled** data; within any single season it is
**not** separable at this n — 2024 alone gives +0.0992, CI [−0.1124, +0.3668], and that season is the
closest analogue to a one-season prospective test.

**Consequence, to be stated in the publication:** the 2026-27 set can confirm or refute the *pooled*
translated-beats-untranslated claim at the §8 margin, and it **cannot** adjudicate per-league
resolution on its own. Promising otherwise would over-claim.

---

## What is NOT changed

Unchanged and still locked: §1 threat list; §2 player set and inclusion conditions; §3 refusal
codes; §5 baselines B0/B1 (with B1b **added**, not substituted); §6 metrics and scoring rule; §7
power line; §7b figures; §9 evaluation checkpoint dates; §10 corrections; §12 limitations. The §8
B0 margin of 12.8% is unchanged, as is the secondary coverage band.

## Provenance

| Change | Forced by | Where measured |
|---|---|---|
| 1 — PARTIAL branch | ATI-2799 returning a verdict §11 does not cover | `translation-holdout-validation-2026-08-17.md` |
| 2 — K refit rule | K fitted on 2016-2025, evaluated on 2024-25 | this amendment; six refits in the walk-forward |
| 2 — keep per-league | 6 of 6 seasons, pooled CI excludes zero, both controls hold | `translation-walkforward-per-league-2026-08-21.md` |
| 3 — realised coverage | G7 realised 0.9221 against a nominal 95% label | `translation-holdout-validation-2026-08-17.md` |
| 4 — B1b primary | G4 tie; model beats oracle B1b by +0.2014 pooled | this amendment |

Executable form: `scripts/validate_translation_holdout.py`, `scripts/validate_translation_walkforward.py`.
