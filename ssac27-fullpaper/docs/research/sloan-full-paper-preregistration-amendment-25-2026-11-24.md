# Amendment 25 to the SSAC27 full-paper pre-registration: how the scored frozen test is shown: one figure of its contrasts, the read-out of the league numbers where the paper promises it, the ordering sentence in the main text, and a sentence where an interval excludes the earlier estimate

**Approval record.**

| | |
|---|---|
| Amends | `docs/research/sloan-full-paper-preregistration-2026-11-03.md`, as amended through Amendment 24. It adds to rule 12 of Amendment 19 (rules 1 and 3 below). It adds one clause after the abstract ending that Amendment 8 fixes, and replaces, in the scored state only, one clause of rule 1 of Amendment 13 (rule 2). It adds one descriptive clause to the reading rules of Amendment 8 (rule 4). Everything else in those amendments holds, among it the abstract endings of Amendment 8, its rule for a failure to replicate, rule 7 of Amendment 13 and rule 1 of Amendment 20 |
| Written | 2026-11-24, by Claude Science, **before the scoring of the frozen 2026-27 test, while no score record of that test exists and its status is not known**, and **after blind readers had read the paper composed from rehearsal records with made-up outcomes**. What the author has seen is listed in the exposure disclosure |
| Approved by | Amir, "All four rules (Recommended)" and, for the table of five named pairs, "Leave as registered (Recommended)", 2026-11-24, each in answer to a question that set out the options with their consequences. Then "Yes", 2026-11-24, in answer to a question that named this amendment's file, its final text, its commit alone on the branch `sloan-fullpaper-amendment-25-2026-11-24` and its draft pull request into `main`. The question said that the Yes approves the final text and merges nothing. The merge and the row in the public hash list wait for his separate word |
| Basis | committed and pushed **alone**, before the frozen 2026-27 test is scored and before any code follows it. Nothing below may be relaxed after the frozen 2026-27 test is scored (METHOD.md §8) |

This amendment fixes how results that are already registered are shown. It adds no analysis, no contrast and no read-out, and it changes no registered verdict. **Every rule prints its content whatever the test shows**, and each was written without knowing what the test will show.

## Why this exists, in plain words

On 24 November 2026 the paper was composed in five states of the frozen test from the committed rehearsal records, whose outcomes are made up. Eleven blind readers read those copies as judges of the competition. They were told that the 2026-27 results were invented. What they agreed on:

1. **The scored paper shows its one prospective test only as sentences.** Every reader of a scored copy asked for one compact display of the registered contrasts. Three readers compared the section with and without a figure of the contrasts; all three preferred the figure.
2. **The paper promises a read-out and does not give it where it promises it.** The introduction and the conclusion say that the frozen test "carries a registered read-out" for what the source league adds once the destination is known (Amendment 13, rule 1). In a scored paper the result of that read-out stands only in the section on the test. The abstract's last sentence reports the three primary contrasts and is silent on it. With an invented failure of that read-out, readers called the abstract's silence hiding. With an invented success, they said that the abstract under-reports.
3. **The ordering read-out is announced in the main text and printed only in the appendix.** The main text says that two read-outs test the league numbers themselves. One of them, the ordering of cross-league pairs, is then printed in Appendix L only (Amendment 19, rule 12).
4. **An interval that excludes the earlier estimate is not mentioned unless the failure rule is met.** With invented results in which nothing was detectable, two intervals excluded their 2020-2025 estimates with the opposite sign, and the paper said only that "the pattern held". The failure rule of Amendment 8 was not met: for translation's gain over history it also asks for an interval that excludes zero, and it does not cover the secondary read-outs. The rule stands. The fact was not stated.

These are choices about a display of the frozen test. They are fixed here, before the test is scored.

## What has already been seen (exposure disclosure)

* **No score record of the frozen 2026-27 test exists**, and no result of that test exists. The scorer refuses to run before 25 November 2026.
* **The rules below were written after reading how invented results read.** The rehearsal records are committed test fixtures (`tests/fixtures/sloan_p1_rehearsal/`, marked `synthetic: true`); their outcomes and the newcomer names beside them are made up, and no file of the 2026-27 season was read to make them. The readers saw invented favourable, null and unfavourable results, an invented inconclusive state and an invented state with fewer than 60 newcomers. The complaints behind rules 2 and 4 came from the unfavourable and the null copies as much as from the favourable one.
* **A draft of the figure of rule 1 was drawn on those made-up records** and shown to six of the readers. Nothing has been drawn on a real outcome.
* **The author knows what the exposure disclosures of Amendments 23 and 24 list**: E30, E31 and E33; what the paper prints about the 674 arrivals and the 180 older arrivals; the values of G of E34. The author has computed no interval of T of E34 and has not run E34.
* **On 24 November 2026 the author read no 2026-27 statistic and opened no Gaussian Hoops page.** The displays of current-season statistics on record are those of Amendments 8, 15, 23 and 24. The same day the author ran the paper's tests, the exporter of the public files and their reproduction script on copies of committed files, and read from them only pass and fail lines and the texts composed from the rehearsal records.
* **The 2020-2025 values that rule 4 compares with are known**, as they have been since the registrations that name them: 0.161, 0.011 and −0.002 EFF/36 for the three primary contrasts (the anchors of the score record), 0.172 for the league-aware forecast against history alone and 0.065 for the league-aware forecast against the destination-only forecast (Amendment 8).

## Specification

| Field | Registered choice |
|---|---|
| Unit | Unchanged |
| Population | Unchanged |
| Estimator | Unchanged |
| Null | Unchanged |
| Filter | Unchanged |
| Key | Unchanged |
| Uncertainty | Unchanged |

## The rules

"The scored state" below is the state in which the score record carries the status scored. In every other state (no score record, not adjudicable, inconclusive) nothing in this amendment is printed and the paper stays as registered before it.

### 1. One figure of the registered paired contrasts (adds to Amendment 19, rule 12)

In the scored state the section on the frozen 2026-27 test prints one figure in the main text, after the paragraphs that report the contrasts and before the table of five named pairs. It takes the next free figure number of the main text.

* **Rows, in this order, in two labelled blocks.**
  * "Primary contrasts (registered 3 November 2026)": history plus translation against history alone (P-a); the league-aware forecast against history plus translation (P-b); the league-aware forecast plus translation against the league-aware forecast (P-c).
  * "Secondary read-outs (registered 16 and 17 November 2026)": the league-aware forecast against history alone (S1); the league-aware forecast against the destination-only forecast (S2); and, when the read-out of the 2015 table was registered in time (Amendment 15), the 2015-table forecast against the destination-only forecast and the league-aware forecast against the 2015-table forecast.
* **What each row shows.** The unweighted paired difference in mean absolute error on the scored newcomers, in EFF/36, with the 95% interval of its registered read-out, both from the score record, on one linear axis with a line at zero. Right of zero, the first-named forecast was the more accurate. Around zero on each row, a band marks the differences that are too small to detect at this number of newcomers with 80% power, from the score record.
* **The earlier estimate.** Under each of the first five rows, a second, lighter marker gives the same contrast on the arrivals of 2020-2025: the anchors of the score record for P-a, P-b and P-c, and the values Amendment 8 names for S1 and S2, each with its committed interval where the paper prints one. The legend calls them exploratory. A row of the 2015 table carries such a marker only if a committed summary holds the same paired contrast on those arrivals.
* **Beside each row, as text.** The estimate, the interval, and the reading in fixed words: "above zero", "not detectable at this n" or "below zero"; for a primary contrast that meets the failure rule of Amendment 8, "failed to replicate".
* **Caption, in these words, with the count filled in:** "The frozen 2026–27 test: every registered paired contrast in forecast error, on the N newcomers scored by 24 November 2026. Dark: the paired difference in mean absolute error (EFF/36) with its 95% interval; the intervals are unadjusted. Light: the same contrast on the arrivals of 2020–2025, which were examined before registration. Band: differences too small to detect at this n with 80% power. Right of zero, the first-named forecast was the more accurate. The fourth row is the sum of the first two. Every row is drawn whatever it shows."
* **Not allowed.** A title or a caption clause that states a finding; a dropped, added or reordered row; a broken or rescaled axis for single rows; a second panel; any mark chosen after the result. The forecast level (S3), the ordering of pairs (S4) and the contrasts weighted by playing time (S5) are not drawn: they are in other units or other weights, and they stay where they are printed.
* **If the figure cannot be built by the submission.** The paper is then submitted without it, and Appendix N says: "A figure of the frozen test's contrasts was registered on 24 November 2026 and is not printed." This sentence is printed whatever the test showed.

### 2. The read-out of the league numbers where the paper promises it (adds one clause after the abstract ending of Amendment 8; replaces, in the scored state, one clause of Amendment 13, rule 1)

S2 is the registered read-out of what the source league adds once the destination is known (Amendment 8). In the scored state its reading is given in three more places, in the registered words of its case (Amendment 8, "What the paper may say"; Amendment 18, rule 5), with X the estimate, the 95% interval, and D the difference detectable with 80% power:

| Interval of S2 | Words |
|---|---|
| above zero | "once the destination was known, knowing the source league improved the 2026–27 forecasts by X EFF/36 (95% interval)" |
| includes zero | "what knowing the source league adds once the destination is known was not detectable at this n (X EFF/36, 95% interval; a gain of D EFF/36 would have been detected with 80% power)" |
| below zero | "once the destination was known, knowing the source league made the 2026–27 forecasts less accurate (X EFF/36, 95% interval): a failure of the league-aware forecast on 2026–27" |

* **Abstract.** The frozen-test sentence keeps the ending that Amendment 8 fixes, word for word, and continues after a semicolon with the words of the case. In the case "includes zero" the bracket of the abstract holds only "a gain of D EFF/36 would have been detected with 80% power". Each case adds one number as Amendment 17 counts, and the limit of nine numbers stays (Amendment 19, rule 2).
* **Introduction and conclusion.** The clause that the frozen 2026-27 test "carries a registered read-out for this gain" (Amendment 13, rule 1) is replaced, in the same place, by "on the N newcomers of the frozen 2026–27 test," followed by the words of the case.
* **What does not change.** The registered verdict and the abstract ending of Amendment 8. Rule 7 of Amendment 13: if a registered contrast fails to replicate, or if the interval of S2 excludes zero in either direction, the first page goes to Amir before any rewriting; this rule fixes the least that is printed in either case and licenses no other rewriting. The sentence that S2 is not expected to be detectable in November stays in the section on the test. The paper says in that section, as it does today, that the intervals of the secondary read-outs are unadjusted.

### 3. The ordering read-out in the main text (adds to Amendment 19, rule 12)

In the scored state the paragraph on the secondary read-outs prints the sentences on the ordering of cross-league pairs (S4) that Appendix L prints, word for word: the share the league-aware forecast ordered correctly, in the registered words of its case, with its interval and the number of pairs; and the share for history alone with the difference and its interval, described as "not detectable at this n" unless its interval excludes zero (Amendment 8; Amendment 18, rule 5). Appendix L keeps them. The forecast level (S3) and the weighted contrasts (S5) stay in Appendix L.

### 4. A sentence where an interval excludes the earlier estimate (adds to Amendment 8, "Reading rules made explicit")

For each of the five contrasts that have an estimate on the arrivals of 2020-2025 (P-a, P-b, P-c, S1, S2): if the 95% interval of the 2026-27 contrast excludes that estimate, the main text says so in the sentence that reports the contrast or in the next, in these words: "its interval excludes the 2020–2025 estimate (X)". This is said whether the 2026-27 estimate is the larger or the smaller one, and whether or not the failure rule is met. If the interval does not exclude the estimate, the clause is not printed. Where the registered sentence on a failure to replicate already says that the interval excluded the 2020-2025 estimate, the clause is not repeated for that contrast. The estimates are the anchors of the score record for P-a, P-b and P-c and, for S1 and S2, the values Amendment 8 names, taken from the committed errors on those arrivals.

The clause describes. It changes no verdict: a contrast fails to replicate under the three conditions of Amendment 8 and under no others, and the registered sentence for three consistent contrasts stays word for word.

## Gates

| Gate | Pass rule | Negative control |
|---|---|---|
| G25a the figure | the figure is printed in the scored state and in no other; it is built by code from the score record and committed summaries; its rows, their order, the text beside each row and the caption are those of rule 1; every number printed in it equals the score record | a scored paper without the figure (and without the sentence of Appendix N) must be refused; a paper in any other state with the figure must be refused; with one contrast of the record changed, the text beside its row must change |
| G25b the read-out of the league numbers | in the scored state the abstract, the introduction and the conclusion each carry the words of the case that the score record gives for S2, and "carries a registered read-out for this gain" is in no part of the paper; the abstract stays within nine numbers | a scored paper with the old clause must be refused; a text whose words are those of another case than the record's must be refused; an abstract one number over its limit must be refused |
| G25c the ordering sentences | in the scored state the main text holds the S4 sentences of Appendix L, word for word | a scored paper without them in the main text must be refused |
| G25d the earlier estimate | for each of the five contrasts, the clause of rule 4 stands in the main text if and only if the interval of the score record excludes the committed 2020-2025 estimate | a record whose interval excludes the estimate, with a text that lacks the clause, must be refused; a record whose interval includes it, with a text that has the clause, must be refused |

## Threats and their controls

| Threat | Control |
|---|---|
| A display of the frozen test chosen after its result | every rule is committed and pushed before any score record exists, and prints its content in every case |
| Rules shaped by invented results that happened to look one way | the readers saw invented favourable, null and unfavourable results; each rule prints the unfavourable case as prominently as the favourable one, and the words for the unfavourable cases are those already registered |
| A favourable secondary read-out lifted into the abstract | S2 is the read-out the paper already names on its first page; its words were registered on 16 and 18 November; it enters the abstract in every case, and its failure enters in the registered words "a failure of the league-aware forecast on 2026–27"; the section keeps "unadjusted" and the sentence that S2 is not expected to be detectable in November |
| A figure that lets wide intervals read as support | the band of undetectable differences on every row; the fixed words "not detectable at this n"; no title that states a finding |
| A figure that hides a contrast | every paired contrast in EFF/36 that the main text reports is a row; no row may be dropped; S3, S4 and S5 are named in the rule as not drawn, with the reason |
| The verdict softened or hardened by rule 4 | the clause is descriptive and symmetric; the failure rule and the registered verdict sentences are unchanged |
| The figure dropped because the result is weak | the figure is printed in the scored state whatever it shows; if it cannot be built, Appendix N says that it was registered and is not printed |
| More work than the days after the scoring allow | rules 2 to 4 are sentences composed from the score record; the figure has the fallback of rule 1 |

## Not part of this amendment

* **The table of five named pairs stays as Amendment 20 registers it.** Readers of the rehearsal copies found that it hurt the section as executed; they saw made-up names. Amir chose to leave it. The figure of rule 1 stands before it.
* **The abstract endings of Amendment 8 and the words "the pattern held"** are not changed.
* **Nothing changes in the states that are not scored.**
* **No sentence on the forecast level (S3) moves to the main text.**

## Scope boundary: nothing pinned changes

No registered analysis, estimate, interval, threshold, verdict, forecast or frozen file is changed. No generator of an analysis is edited by this amendment. The frozen 2026-27 forecasts are not read by any rule above before the registered scoring run.
