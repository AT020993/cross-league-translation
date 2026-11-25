# Amendment 5 to the SSAC27 full-paper pre-registration: a larger identity-linkage audit (E25)

**Approval record.**

| | |
|---|---|
| Amends | `docs/research/sloan-full-paper-preregistration-2026-11-03.md`, as amended on 2026-11-04, 2026-11-05 and 2026-11-11 (Amendments 1 to 4) |
| Written | 2026-11-12, after the E13 audit result was read and before the analysis below was implemented |
| Approved by | Amir, "Yes, accept as written", 2026-11-12 |
| Basis | committed and pushed **alone**, before any implementation. Nothing below may be relaxed after a result is seen (METHOD.md §8) |

Everything in the 3 Nov pre-registration and in Amendments 1 to 4 stands. This amendment **adds** one analysis, E25. It changes no registered analysis, threshold, model, population or licence. The E13 result (1 wrong of 100, Wilson 95% interval 0.2% to 5.4%, no licence earned) stays in the record exactly as reported.

## Why this exists, in plain words

The league factors are built from 4,074 player pairs joined by name. 1,537 were verified one by one. Of the other 2,537 we checked a random 100 (E13). One was classed as wrong, so the best estimate is 1%, but with only 100 checked the upper bound is 5.4%. The registered bar for saying "at most X% are mismatches" is an upper bound below 5%. The audit missed it by sample size, not by a bad result.

E25 checks a **new** random sample of 300 pairs, with the same checks and the same rules, so that the paper can either state a bound or say plainly that it still cannot.

## What has already been seen (exposure disclosure)

* **Seen before this amendment was written:** the full E13 result, the records of its 100 sampled pairs, and the one WRONG pair (two birthdates ten days apart; club and schedule checks raise no objection).
* **Not computed or seen:** any identity check on any of the other 2,437 unverified pairs.
* **This is a second look.** The decision to audit more pairs was taken because the first look narrowly missed the bar. A second look taken for that reason raises the chance of passing by luck. The controls are: the new sample is drawn fresh and must pass **on its own**; the size is fixed here; there is no third look for this paper (see Licences).
* E25 is **exploratory**, like E13, and the paper will say so.

## Specification

| Field | Registered choice |
|---|---|
| Unit | One factor-estimation pair: player × season, his domestic (source) record and his continental (destination) record. As in E13. |
| Population | The E13 frame (pool-A pairs absent from verified pool B, 2,537) **minus the 100 pairs drawn in E13**: 2,437 pairs. |
| Estimator | Share of audited pairs classed WRONG: (a) on the new 300; (b) pooled over the E13 100 and the new 300 (400); (c) the E13 100, unchanged, printed beside them. |
| Null | None (a rate with an interval). |
| Filter | None beyond the frame. Every drawn pair is classed; none is dropped or replaced. |
| Key | `player_name` × `season` × `league_src` × `league_dest` (the E13 key). |
| Uncertainty | Wilson 95% interval, as in E13. The UNRESOLVED share is always printed, and so is the bound with every UNRESOLVED pair counted as WRONG. |

## Analysis

### E25. A second, larger identity-linkage sample

* **Sample.** 300 pairs, simple random sample without replacement from the 2,437, frame sorted by the E13 key, `numpy.random.default_rng(20261112)`. Drawn by a committed generator **before any record is inspected**; the drawn keys are written to a retained run first, as in E13.
* **Checks, classes and thresholds.** Exactly those of E13 as implemented in `scripts/sloan_fullpaper_linkage_audit.py` (sha256 `8fb91e66c881a5addff6dc5f50a6ebcda5777e5caf19543603c55dedb0e1e91a`): normalised name, birthdate where both sides carry one, club consistency (same club: at least 3 shared players and at least 50%; different: at most 1), schedule feasibility; classes CONFIRMED, WRONG, UNRESOLVED by the E13 rules. The E13 functions are imported, not rewritten.
* **Hand review.** Rule-based classes first. Hand review may only move an UNRESOLVED pair to CONFIRMED or WRONG, with the evidence recorded per pair. A rule-based WRONG or CONFIRMED is never changed by hand (as in E13, where the birthdate case stayed WRONG).
* **Printed, descriptive only.**
  * WRONG pairs whose only contradiction is a birthdate while the club and schedule checks agree.
  * WRONG and UNRESOLVED counts by source league and by season.
  * How many pairs carry a birthdate on both sides (in E13: 9 of 100), so the reader sees that most confirmations rest on name plus club.
* **Licences.**
  * **Bound earned** only if the Wilson upper bound is below 5% on the new 300 **and** on the pooled 400. In numbers: at most 7 WRONG among the new 300. The paper may then say "at most X% of unverified estimation pairs are identity mismatches", where X is the **larger** of the two upper bounds, and it reports the E13 result beside it.
  * **Bound not earned:** the paper keeps its limitation sentence with the new numbers, and says the bound was not earned in either look.
  * **Point estimate of 10% or more** on the new 300 or the pooled 400: a data-quality finding that touches every factor; reported to Amir before any writing.
  * **No third look.** Whatever E25 shows, the audit is not extended again for this paper.

## Power, stated before the result

If the true mismatch rate among the 2,437 is 1%, the bound is earned with probability 0.99; at 1.5%, 0.92; at 2%, 0.75; at 3%, 0.31; at 4%, 0.07 (hypergeometric, at most 7 WRONG in 300). A failure to earn the bound is therefore informative only against rates of about 2% or less; the paper will not read it as evidence of a high rate.

## Gates and negative controls

| Gate | Pass rule | Negative control |
|---|---|---|
| G25a draw | drawn keys written before inspection; a redraw with seed 20261112 reproduces them | seed 20261113 must give a different sample |
| G25b disjoint | no drawn key is among the E13 100 | a draw from the full 2,537 with the E13 seed must overlap the E13 100 (it reproduces them) |
| G25c same rules | the E25 generator, run on the E13 100, reproduces the E13 rule-based classes pair for pair | a changed club threshold must fail the comparison |
| Input pins | pool A and pool B pairs sha256 equal the v10 manifest; frame = A − B − E13 sample = 2,437 | — |

## Threats and their controls

| Threat | Control |
|---|---|
| A second look taken because the first one missed | fresh sample; must pass on its own and pooled; larger bound quoted; size fixed; no third look |
| Hand review tilting the result | rule-based classes first; hand review only for UNRESOLVED; evidence recorded per pair; the bound with UNRESOLVED counted as WRONG is printed |
| Few birthdates on both sides | unchanged from E13 and stated in the paper: a confirmation mostly means name plus club, not a birthdate match |
| A result that weakens a paper claim | reported in the main text; reported to Amir before any writing |

## Scope boundary

Nothing pinned changes. No forecast, factor or paper number depends on E25 except the linkage sentence in Limitations. E25 audits the factor-estimation pairs only; it does not audit the 674 forecast arrivals. E25 is implemented in a new dated generator with a committed report script. Retained runs go to `/Users/amir/Projects/cv_basketball_archive/research-runs/sloan-fullpaper/` from committed code.

## Timeline

| Date | Step |
|---|---|
| 12 Nov | this amendment approved and pushed alone |
| by 14 Nov | E25 result |
| 19–20 Nov | paper re-rendered; analysis lock |
