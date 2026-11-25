# Amendment 8 to the SSAC27 full-paper pre-registration: more read-outs from the frozen 2026–27 test, and its reading rules made explicit

**Approval record.**

| | |
|---|---|
| Amends | `docs/research/sloan-full-paper-preregistration-2026-11-03.md`, as amended on 2026-11-04, 2026-11-05, 2026-11-11 and 2026-11-12 (Amendments 1 to 7) |
| Written | 2026-11-16, before the frozen 2026–27 test is scored and before any 2026–27 player statistic has been read by any analysis in this project |
| Approved by | Amir, "Accept Amendment 8 as written and Accept Amendment 9 as written as long you think they are good", 2026-11-16. Two rules were then tightened before the push; see "Changes after the draft" at the end |
| Basis | committed and pushed **alone**, before any implementation and before 25 November 2026. Nothing below may be relaxed after a result is seen (METHOD.md §8) |

Everything in the 3 Nov pre-registration and in Amendments 1 to 7 stands. The three primary contrasts of the frozen test (P-a, P-b, P-c), its minimum of 60 newcomers, its licence and its failure rule are unchanged. This amendment **adds** five secondary read-outs to the frozen test and to its February re-score, and it writes down four reading rules that the 3 Nov text states in one line each.

## Why this exists, in plain words

The frozen 2026–27 test is the only part of the paper whose outcomes nobody has seen. As registered, it asks three questions, all about translation factors.

A review of the paper on 15 November by three independent readers found the same gap three times: the paper never tests its own product, the league-aware forecast, against the plain baselines on unseen data. It also has two standing qualifications (the forecasts run low; the gain shrinks when weighted by playing time) that rest only on seasons already examined.

The 2026–27 outcomes are still unread, so these questions can still be registered. That is what this amendment does. It also fixes, in advance, how each possible outcome of the test is worded, so that no wording is chosen after the result is known.

## What has already been seen (exposure disclosure)

* **Destination seasons 2017–2025 are exposed**, and so are the older seasons scored under Amendment 7. Every prediction below is informed by them.
* **The point estimates that S1 and S2 look for are already known on 2020–2025** by subtraction of printed errors: 3.096 − 2.924 = 0.172 EFF/36 (league-aware against history) and 2.989 − 2.924 = 0.065 (league-aware against a forecast that knows only the destination). On the older seasons the first is 2.862 − 2.830 = 0.032. Their intervals have not been computed.
* **The forecast level on 2020–2025 is known** (the league-aware forecast was 0.47 EFF/36 low; 1.43 low in 2025–26), and so is the cross-league ordering result (73.7% against 72.4%).
* **Nothing from 2026–27 has been read by any analysis.** The frozen forecast file (sha256 `f3530c1a5ac369c032a996756ced226a93aa2d9f71d2e63aab21694de3d55316`) was opened on 16 November for its column names and status flags only; it holds no 2026–27 statistic.
* **One incidental display, recorded here.** During a literature search on 15–16 November, a web-search result page showed current-season stat lines of three EuroLeague players, and the README of a public repository showed competition-level effects fitted on data that include part of 2026–27. These values were seen only by the literature-search process. They were not written to any repository file or analysis input, and they were not available to the process that wrote this amendment.

## Specification

| Field | Registered choice |
|---|---|
| Unit | One scored newcomer of the frozen test: player × destination competition, season 2026–27 |
| Population | Exactly the frozen test's population (3 Nov registration): v10 eligibility, continental games dated on or before 24 Nov 2026, files refreshed on or after 25 Nov. For the February re-score: Amendment 1's population (games on or before 15 Feb 2027) |
| Estimator | S1, S2: paired differences in mean absolute error, as for P-a to P-c. S3: mean signed error. S4: share of cross-league pairs ordered correctly. S5: the paired contrasts weighted by destination minutes |
| Null | Zero for S1, S2, S3 and S5; 50% for S4 |
| Filter | None beyond the frozen test's own rules. No newcomer is added, removed or joined by hand |
| Key | The frozen file's key (player × destination), joined as the 3 Nov registration specifies |
| Uncertainty | S1, S2, S5: the v10 two-way clustered 95% interval (player, destination club), as for P-a to P-c. S3, S4: the club cluster bootstrap of E18a and E10, unchanged |

## The five secondary read-outs

All five use the same frozen forecast file, the same scored newcomers and the same scoring run as P-a to P-c. They are computed once. **None of them can change the frozen test's registered verdict**, which depends on P-a, P-b and P-c alone.

Arms are named as in the frozen file: `history_only` (history), `history_destination_slope` (knows the destination, not the source league), `source_ridge_10` (the league-aware forecast), `scheduled_history` (history plus translation).

| | Read-out | Definition | Predicted now |
|---|---|---|---|
| S1 | League-aware against history | MAE(`history_only`) − MAE(`source_ridge_10`) | positive |
| S2 | What the source league adds once the destination is known | MAE(`history_destination_slope`) − MAE(`source_ridge_10`) | at or above zero |
| S3 | Forecast level | mean of forecast − actual EFF/36 for `source_ridge_10`; printed beside it for `history_only` and `scheduled_history` | below zero (the forecasts run low) |
| S4 | Cross-league ordering | within each destination competition, among pairs of newcomers from different source leagues with unequal outcomes: the share in which the higher `source_ridge_10` forecast had the higher outcome. Printed beside it: the same share for `history_only`, their difference, and both on same-league pairs | above 50% |
| S5 | Playing-time weighting | P-a, P-b, P-c, S1 and S2 with each newcomer weighted by his destination minutes in the scored games | no prediction; printed beside the unweighted values |

### What the paper may say

| Read-out | Interval | Wording |
|---|---|---|
| S1 | above zero | "on unseen 2026–27 forecasts the league-aware forecast was more accurate than history alone, by X EFF/36" |
| | includes zero | "not detectable at this n", with n and the detectable effect |
| | below zero | reported prominently as a failure of the league-aware forecast on 2026–27; to Amir before any writing |
| S2 | above zero | "once the destination was known, knowing the source league improved the 2026–27 forecasts by X EFF/36" |
| | includes zero | "not detectable at this n", with n and the detectable effect |
| | below zero | reported prominently; to Amir before any writing |
| S3 | below zero | "the frozen forecasts ran X EFF/36 below what newcomers delivered" |
| | includes zero | "no level error was detectable at this n", with the interval |
| | above zero | "the frozen forecasts ran X EFF/36 above what newcomers delivered" |
| S4 | above 50% | "on unseen 2026–27 forecasts the league-aware forecast ordered X% of cross-league pairs correctly" |
| | includes 50% | "not distinguishable from a coin flip at this n", reported in the main text |
| | difference from history | always printed with its interval; described only as "not detectable at this n" unless its interval excludes zero |
| S5 | any | each weighted contrast is printed beside its unweighted value with its interval. The unweighted contrasts stay primary. No new sentence is licensed; a weighted interval that includes zero is described as "not clearly above zero when weighted by playing time" |

* **Everything is reported whatever it shows**, in the paper's frozen-test section or its appendix, with the number of secondary read-outs stated (five). Intervals are unadjusted 95% intervals; the paper says so.
* **Equivalence is never claimed from the frozen test**, as registered. This holds for the secondary read-outs too.
* **Stated now, so that a null is read correctly.** The registered power table gives a detectable effect of 0.298 to 0.244 EFF/36 at 100 to 150 newcomers for history against history plus translation. S1 compares two forecasts of similar kind and looks for an effect near 0.17; S2 looks for an effect near 0.07. We therefore expect that neither will be detectable in November. Pair ordering among 100 to 150 newcomers can be read to within roughly five percentage points, enough to tell skill from a coin flip but not to detect a gain of the size seen on 2020–2025 (1.32 points). The scoring run prints the detectable effect of S1 and S2, computed from the 2020–2025 paired differences, before any 2026–27 contrast is read.
* **Partial-season caveat, registered now.** Outcomes through 24 November cover only newcomers who reach eight games early, over few games. A level error (S3) or a weak ordering (S4) in November may reflect that. The paper prints the November values as registered and repeats all five read-outs at the February re-score, beside them.

### At the February re-score only

Two further read-outs are registered for the re-score on games through 15 February 2027, where outcomes are closer to a full season. In November they are printed as descriptive and license no statement.

* **Error-band coverage.** The 80% and 95% bands for a 2026–27 forecast are the league-aware forecast plus or minus the split-conformal quantile of its absolute walk-forward errors on all 674 arrivals of 2020–2025. The two half-widths are computed from the committed forecasts and committed to the repository before 25 November. Read-out: the share of scored newcomers inside each band, with a club cluster bootstrap interval. Wording: "the 80% bands contained X% of 2026–27 newcomers"; if the interval excludes 80%, the paper says the bands were too narrow or too wide.
* **Forecast-gap guide.** The registered E20 bins (0 to 1, 1 to 2, 2 to 3, 3 to 4, 4 to 6, 6 or more EFF/36) applied to all pairs of scored newcomers in the same competition: the share in which the higher league-aware forecast had the higher outcome, per bin, with pair counts and club cluster bootstrap intervals. Wording follows E20's registered sentences, with "on 2026–27 newcomers" added.

## Reading rules made explicit

The 3 Nov registration states each of these in one line. They are written out here so that the scoring code and the paper apply one rule, fixed before the result.

1. **Failure to replicate, and "consistent with the anchor".** The 3 Nov registration says two things: a contrast whose interval "excludes the anchor's point estimate in the opposite direction" is a failure to replicate, and a P-a interval that spans zero is "not detectable at this n, never a contradiction of the anchor". Read together, a primary contrast **fails to replicate** when (i) its 95% interval excludes its 2020–2025 point estimate, (ii) its own point estimate has the opposite sign, and (iii) for P-a, its interval also excludes zero. The three contrasts are consistent with the anchor when none fails.
2. **Wording of a single contrast.** A contrast is called detectable only if its interval excludes zero. A head-to-head estimate (P-b) below zero whose interval includes zero and does not meet rule 1 is worded "no difference detected at this n"; the phrase "at least as good" is then not used for 2026–27. If all three contrasts are consistent, the registered sentence is used: "the pattern held on unseen 2026–27 forecasts, within this test's power", followed by the statement that equivalence is not established.
3. **Joins and "inconclusive".** No name is joined by hand. Every newcomer who reaches eight games and is not joined to a frozen row is listed by name, club and previous club (the registration field of the EuroLeague API, which holds no statistic). An unjoined newcomer is a **possible lost target** if a row of the frozen file has either (a) the same surname after the v10 name normaliser and a 2025–26 club that matches his previous club by the text rule of Amendment 6, or (b) a full normalised name within two character edits of his. If possible lost targets number more than 5% of the joined newcomers (the bar already registered for identity mismatches), the test's status is **inconclusive**: the contrasts on the joined newcomers are printed with the list, and no licence sentence is used. At or below 5%, the test is scored, and the list and its count are printed in the appendix. This rule can miss a lost target whose name and club are both written differently, so the count is a lower bound; the full list of unjoined newcomers is published so that it can be checked. The status is also "inconclusive" if a required data gate fails and cannot be repaired by refreshing the files.
4. **Below 60 newcomers.** "Reported descriptively" means: the number of newcomers, their median number of games, and the mean absolute error of the four primary forecasts. No contrast, no interval and no secondary read-out is computed.

The registered complete-source sensitivity (newcomers whose source league has a complete 2025–26 season) is printed for P-a to P-c, S1 and S2 in the appendix.

### The abstract sentence, fixed now

The abstract's sentence on the frozen test states the freeze date and that the freeze came after the season began but before outcomes were inspected. It ends in exactly one of these ways:

| Status | Ending |
|---|---|
| scored, all three consistent | "were scored on N newcomers: the pattern held on unseen 2026–27 forecasts, within this test's power." |
| scored, at least one failure | "were scored on N newcomers: [the contrast or contrasts] failed to replicate." |
| not adjudicable | "yielded N eligible newcomers, fewer than the 60 required, so the registered test is not adjudicable." |
| inconclusive | "could not be scored cleanly, so the registered test is inconclusive." |

## Gates and negative controls

* The scoring run reproduces P-a, P-b and P-c exactly as it would without this amendment; the secondary read-outs are added to its output and change none of its primary numbers. A test asserts this on synthetic data.
* The join rule (rule 3) ships with a negative control: a synthetic file in which more than 5% of names are altered by one character must produce the status "inconclusive".
* The failure rule (rule 1) is tested on synthetic contrasts, including a P-a estimate below zero whose interval spans zero, which must read "consistent".
* The band half-widths are pinned by value in a committed file before 25 November; the scoring run refuses to run if they differ.
* All four statuses are rehearsed end to end on synthetic 2026–27 files before 24 November. No 2026–27 statistic is used in the rehearsal.

## Threats and their controls

| Threat | Control |
|---|---|
| Read-outs chosen after seeing 2026–27 results | this amendment is pushed alone before 25 November; its hash is added to the public hash list |
| Many read-outs, one of them "significant" by chance | the verdict rests on P-a to P-c only; all five secondary read-outs are printed with unadjusted intervals and counted in the text |
| A null read as a contradiction | detectable effects are printed before any contrast is read; expected non-detection of S1 and S2 is stated above |
| Partial-season outcomes | caveat registered above; every read-out repeated in February and shown beside November |
| A result that weakens a paper claim | reported to Amir before any writing, then in the main text |

## Scope boundary: nothing pinned changes

The frozen forecast file, the freeze record, the scoring population, the three primary contrasts, the 60-newcomer minimum and the failure rule are untouched. No model is refitted. The 2020–2025 results, the older-seasons test and every earlier amendment are unchanged.

## Changes after the draft

The draft that Amir read on 16 November differed from this text in two rules. Both changes were made before the push and before any implementation, and neither depends on any result.

* **Rule 1.** The draft required only conditions (i) and (ii). Condition (iii) was added because the 3 Nov registration states that a P-a interval spanning zero is never a contradiction; without it, the rule would have called such a result a failure.
* **Rule 3.** The draft counted an unjoined newcomer as a possible lost target if a frozen row shared his surname and first initial. Two different players often share a surname and an initial, so that rule could have produced the status "inconclusive" by coincidence. The surname must now be backed by a matching previous club.

The sentence on the abstract was reworded to fix the ending only, and the exposure note says "repository file or analysis input" where the draft said "project file".
