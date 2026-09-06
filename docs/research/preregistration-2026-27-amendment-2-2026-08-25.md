# AMENDMENT 2 to the 2026-27 prospective pre-registration

**Date: 2026-08-25. Ticket: ATI-2891. Status: proposed, not yet locked.** Base document is
`preregistration-2026-27-predictions.md` (2026-08-17). Prior amendment is
`preregistration-2026-27-amendment-1-2026-08-21.md`. Lock deadline **24 September 2026**, tip-off.

## Specification

| Choice | This amendment | Alternatives considered |
|---|---|---|
| **Scope** | records the decision on Amendment 1 Change 1, and adds three changes forced by measurements taken after Amendment 1 was drafted | editing Amendment 1 in place (rejected — its value is that its content is dated) |
| **Evidence admitted** | the RTM comparator merged 2026-08-25 (`validate_translation_walkforward.py`, n=719, 6 windows) and the 2026-08-25 signings re-collection | Amendment 1's evidence alone (insufficient — it predates the RTM arm) |
| **Constraint** | no bar relaxed, no completed gate re-scored (`METHOD.md` §8); every change is declared before any 2026-27 outcome exists | — |
| **Traceability** | each change names the measurement that forces it | — |

**Why a second amendment.** Amendment 1 is dated 2026-08-21. Two things have been measured since:
a regression-to-the-mean comparator that changes what the per-league table can claim, and a signings
re-collection that moves the scored population again. Editing Amendment 1 would make it look as
though those were known when it was written. They were not.

**On the legitimacy of changing the estimator now.** Change 2 below alters the prediction basis after
seeing which arm wins out-of-sample. That is only acceptable because **no 2026-27 outcome exists
yet** — the season has not been played, so nothing here is fitted to the data it will be scored on.
The evidence is dated, the arm is declared in advance, and its non-pre-registered origin is stated in
Change 2 itself. Under `METHOD.md` §8 this is an amendment, not a re-score.

---

## Change 1 — The PARTIAL branch is DECIDED: publish, scope narrowed

**Decision recorded 2026-08-25.** Amendment 1 Change 1 is **accepted as written**. The
`On PARTIAL` branch enters §11 verbatim as drafted there:

> **On PARTIAL** (the pooled MAE and generalisation gates pass; a baseline-superiority sub-gate
> fails or ties): publish predictions, with the scope narrowed to the passing claims and the
> failing sub-gate named in the publication body — not a footnote.

**What this settles.** The ATI-2799 verdict stands at PARTIAL: G1/G2/G3/G5/G6 pass, G4 ties a
single-constant baseline at −0.005 MAE, CI ~~[−0.236, +0.230]~~ [−0.230, +0.240] *(corrected 2026-09-04, ATI-2955)*. G4 is **not** re-scored, and the
publication names it. §11 is now executable.

---

## Change 2 — The prediction basis becomes per-league **plus** regression to the mean

**Problem.** Amendment 1 Change 2 kept the 22-cell per-league table, justified by it beating one
global scalar by +0.2475, CI [+0.1701, +0.3283], 6 of 6 seasons. That justification is now known to
rest on the weaker of two available comparators. Only about **4% of the variance in realised
translation ratios is between leagues**; the rest is player-to-player within a league. Against a
model that predicts regression to the mean from a player's own history and uses **no league
information at all**, the per-league table does not separate:

*Provenance note added 2026-09-05, no bar moved: the "about 4%" was measured on the
Proballers-destination corpus. On the API-destination corpus (Amendment 4 default) the between-league
share is 8.7% of the pairs' ratio variance and 14.5% of the scored transfers'
(`translation-propositions-2026-09-04.md`, P1). The motivation for this Change is unchanged: the
majority of the variance is within a league either way.*

| arm | MAE | R² |
|---|---|---|
| untranslated (B0) | 3.9676 | — |
| one global scalar | 3.3934 | +0.2682 |
| 22 per-league factors | 3.1459 | +0.3597 |
| RTM only, no league identity | 3.1616 | +0.3537 |
| **RTM + per-league** | **2.9550** | **+0.4227** |

*Provenance note added 2026-09-04 (ATI-2955), no value changed: the R² column above had no
committed generator when this amendment was written. `scripts/validate_translation_walkforward.py`
now writes it (`walkforward_summary.json: pooled.r2`) and the Proballers-corpus re-run reproduces
all four values; the ceiling beside them is 0.671 (`pooled.ceiling`). Recorded in
`translation-walkforward-per-league-2026-08-21.md`.*

Pooled paired cluster bootstrap, n = 719 in 203 clusters:

| contrast | delta | 95% CI | |
|---|---|---|---|
| per-league vs one global scalar | +0.2475 | [+0.1701, +0.3283] | separates |
| **per-league vs RTM** | **+0.0157** | **[−0.1051, +0.1361]** | **tie** |
| RTM + per-league vs RTM | +0.2066 | [+0.1393, +0.2786] | separates |
| RTM + per-league vs per-league | +0.1909 | [+0.0958, +0.2876] | separates |

**Change.** §4's prediction basis becomes the **combined arm**: the 22-cell per-league table
**together with** regression-to-the-mean predictors fitted on seasons strictly prior to the
prediction season. Per-league resolution is **not withdrawn** — its justification changes from
"beats one constant" to "adds to regression to the mean", and it is retained because it demonstrably
does add (+0.2066, interval excluding zero).

**Per-player method, declared in advance.** A player is scored through the combined arm when he has
**at least two qualifying corpus seasons** (a source season plus prior history); otherwise through
per-league factors alone. On the 2026-08-25 collection that is **90 of 110 scorable (81.8%)**
combined and 20 per-league-only. **The publication must label which method scored each player.**

**Status disclosure.** The RTM arm is **not pre-registered**. It was added to a shipped analysis
after its result was seen, and the walk-forward note carries a dated addendum saying so. It is
admitted here as a declared-in-advance amendment, not as a pre-registered prediction.

**Falsification already run.** Permuting the league→multiplier assignment and **refitting** the
combined arm reaches the observed gain in **0 of 200** reps, so the joint gain is the league mapping
and not the extra degree of freedom. Both this control and the combined-vs-RTM contrast are in-script
asserts, so a run that stops satisfying them fails rather than reports.

---

## Change 3 — Add B1c, and state the power each primary criterion actually has

**Problem.** Amendment 1 Change 4 made **B1b** — source rate times a constant fitted to the scored
set itself — a *second primary criterion*. That is the right direction, but the prospective set is
not powered for it, and nothing in Amendment 1 says so.

**Change, part one.** §5 gains a third baseline:

> **B1c** — regression to the mean: the player's own prior-season rate and source-season rate,
> with coefficients fitted on seasons strictly before the prediction season and no league
> information. This is the strongest available league-free comparator.

B1c beating is a **secondary** criterion, not a primary, for the power reason below.

**Change, part two — the power statement, which must be published with the predictions.** Scaling
each contrast's observed pooled interval to the prospective set:

| criterion | pooled effect | power at n=110 | n for 80% |
|---|---|---|---|
| beat **B0** untranslated | +0.8217 | **0.84** | 99 |
| beat **B1b** oracle one-constant *(primary, Amd. 1)* | +0.2014 | **0.36** | 332 |
| combined beats **B1c** RTM *(secondary, new)* | +0.2066 | **0.62** | 167 |
| league adds to RTM | +0.1909 | **0.33** | 371 |

> **Only the B0 criterion is adequately powered by the 2026-27 set.** B1b, made a second primary by
> Amendment 1, has roughly **36%** power at n = 110. A single prospective season therefore returns
> **PARTIAL by construction more often than not**, and a PARTIAL verdict on B1b must not be read as
> the model having failed — it is the season being too small to adjudicate. The pooled walk-forward
> evidence (n = 719) is what carries the B1b and B1c claims; the prospective set tests B0.

**Neither bar is relaxed.** B1b stays a primary at the margin Amendment 1 set. What changes is that
its power is declared, so a foreseeable PARTIAL is not mistaken for a negative result.

---

## Change 4 — State the scored population as a dated count, not a fixed number

**Problem.** The base document §7/§10.1 projects **~69** scored players. Amendment 1 repeats it. The
recollected list has since gone **69 → 94 → 110**, and it is still growing: EuroLeague imports alone
grew 64 → 80 between 21 and 25 August.

**Change.** §7's power line becomes a dated rule:

> The scored population is the count of `kind == "import"` arrivals carrying a translatable prior
> league, **as of a dated collection recorded in the publication**. As of 2026-08-25 it is **110**
> (68 EuroLeague, 42 EuroCup). The publication states its own collection date and count, and the
> power figures in Change 3 are restated at that count.

**Two data caveats that travel with the count.** Both are properties of the input, not of the model:

1. **Six EuroCup clubs (BCR, BOU, BUD, LJU, MCO, TTK) have no published 2026-27 roster.** The
   endpoint returns success with an empty list while their 2025 rosters return 35–47 people. Their
   signings are **missing, not zero**, and the publication must say so rather than reporting them as
   clubs that signed nobody.
2. **Only `kind == "import"` is a scoreable new arrival.** `returning_to_club` counts are retained
   players; scoring them as arrivals inflates the report roughly twofold.

---

## What is NOT changed

Unchanged and still locked: §1 threat list; §2 player set and inclusion conditions; §3 refusal codes;
§6 metrics and scoring rule; §7b figures; §9 evaluation checkpoint dates; §10 corrections; §12
limitations. From Amendment 1: the K_LAG prior-seasons-only rule (Change 2), the realised-coverage
relabelling at 0.922 (Change 3), and the §8 B0 margin of 12.8% and B1b primary (Change 4) all stand.
No bar in either document is relaxed here.

## Provenance

| Change | Forced by | Where measured |
|---|---|---|
| 1 — PARTIAL decided | a judgement call §11 could not resolve; decision taken 2026-08-25 | Amendment 1 Change 1 |
| 2 — basis becomes combined | per-league ties a league-free RTM model (+0.0157, CI spans zero) | `translation-walkforward-per-league-2026-08-21.md` addendum; `scripts/validate_translation_walkforward.py` |
| 3 — B1c + declared power | B1b made primary at 36% prospective power | this amendment, scaling the pooled intervals |
| 4 — dated population count | scored set moved 69 → 94 → 110 and is still growing | `collect_import_signings.py`, collection 2026-08-25 |

Executable form: `scripts/validate_translation_holdout.py`,
`scripts/validate_translation_walkforward.py`, `scripts/collect_import_signings.py`.
