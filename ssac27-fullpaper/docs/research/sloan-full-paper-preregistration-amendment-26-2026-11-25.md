# Amendment 26 to the SSAC27 full-paper pre-registration: the words of the paper once the frozen 2026-27 test was scored and found inconclusive, and two descriptive sentences from values the paper already prints

**Approval record.**

| | |
|---|---|
| Amends | `docs/research/sloan-full-paper-preregistration-2026-11-03.md`, as amended through Amendment 25. In the inconclusive state only, it replaces one clause of rule 1 of Amendment 13 (rule 1 below), one sentence of rule 9 of Amendment 19 (rule 2), the order and the tense of the section on the frozen test and its sentence on the cause (rule 3), the abstract ending that Amendment 8 fixes for that state (rule 9) and one sentence of rule 6 of Amendment 16 (rule 5). It adds to the Limitations entry on the frozen test (rule 4), to rule 12 of Amendment 19 (rules 6 and 7), to the note on Amendment 20 in Appendix N (rule 8) and to the readings of Amendments 3 and 9 (rules 10 and 11). Everything else in those amendments holds, among it rule 3 of Amendment 8: the contrasts are printed with the list and no licence sentence is used |
| Written | 2026-11-25, by Claude Science, **after the frozen 2026-27 test was scored, with its score record committed and every value in it known to the author**, and after two readers who saw only the paper had read it. What the author has seen is listed in the exposure disclosure |
| Approved by | Amir, "A: all rows 1–9 (Recommended)" and "a: league gaps grew, b: size of the gain", 2026-11-25, each in answer to a question that set out the options with their consequences and pointed to a table of the sentences before and after. Then "Yes", 2026-11-25, in answer to a question that named this amendment's file, its final text, its commit alone on the branch `sloan-fullpaper-amendment-26-2026-11-25` and its draft pull request into `main`. The question said that the Yes approves the final text and merges nothing. The merge and the row in the public hash list wait for his separate word |
| Basis | committed and pushed **alone**, before any code follows it |

**This amendment registers nothing in advance.** Every result it touches was known when it was written. It is the dated record of a change of wording, made in the open so that a reader can see what the paper said before and what it says now. It adds no analysis and no contrast, changes no number, and draws no conclusion from the frozen test.

## Why this exists, in plain words

The registrations fixed the paper's words for an inconclusive test before anyone knew how the test would end. On 25 November 2026 the test was scored once and the registered rule made it inconclusive: 7 newcomers without a frozen forecast may be players in the frozen file under another spelling, 7.4% of the 94 joined newcomers, above the 5% allowed in advance (Amendment 8, rule 3).

The paper was then rendered in that state, and two readers who saw nothing but the paper read it, one as a judge of the competition and one as an auditor of its consistency. Both ranked the same problem first. **The paper does not say what happened to the frozen test where it names the test.**

1. The first section and the conclusion say that the frozen test "carries a registered read-out" for what the source league adds. The read-out produced nothing a sentence may be written from, and a reader of the first page is not told.
2. The paragraph before the section on the frozen test ends: "the frozen 2026–27 test is the registered test on arrivals". It presents the test as the one that decides, three paragraphs before the reader learns that it could not.
3. The section on the frozen test gives the design first, in the present tense ("They are scored", "we do not expect"), and the outcome after it. It does not date the scoring, and it names the cause as "its required data or validity controls" where one control failed.
4. The abstract speaks of two tests in the same words. It says "In a test registered and frozen before its outcomes were read" of the league changes, and ends: "the registered test is inconclusive". A fast reader can take the test on league changes to be the inconclusive one.
5. In Appendix L, under a heading that says "no sentence is licensed", each weighted value is introduced by the reading "not clearly above zero when weighted by playing time", once for a value below zero.
6. Limitations, Related work and two passages of the appendix still speak of the test as something to come.

The readers also pointed to two facts that the paper's own tables show and its text does not say (rules 10 and 11). Both are unfavourable to the paper.

## What has already been seen (exposure disclosure)

* **The author has seen the whole score record of the frozen 2026-27 test** (`docs/research/artifacts/sloan-fullpaper-p1-score-2026-11/score.json`, sha256 `f2c895bcf1cbdbba614b15986ccd3c3115164677ee47c73947786e44be2b4e22`): its status, the seven names, every contrast with its interval, the forecast level, the ordering of pairs and the coverage of the bands. Every interval of a paired contrast includes zero and includes its 2020-2025 estimate. The author rendered the paper from that record three times (retained runs `paper-render-48` to `paper-render-50`) and read it.
* **The rules below were written after two readers had read that paper.** They saw the real paper and its real values. Their lists are kept with the session's records.
* **The author corrected one passage after the scoring, before this amendment.** Appendix L of render 48 printed, in the inconclusive state, two sentences that Amendment 8 licenses for a scored test only. Since commit `7d0013c88` the same values are printed as values, "for the record only". No number changed. That correction applied a registered rule; rules 6 and 7 below go further than the registered words and are therefore registered here.
* **The values behind rules 10 and 11 are known and printed**: the ten league values of each yearly refit (Table A11 of the paper, Amendment 3), and the gain of the league-aware forecast over the destination-only forecast on the 674 arrivals of 2020-2025 with its values by competition (Table A19, Amendment 9).
* **The author knows what the exposure disclosures of Amendments 23 to 25 list.** E34 has not been run, and no Gaussian Hoops page has been read in full; the site refuses automated readers.
* **No 2026-27 statistic was read for this amendment** beyond the committed score record and the files of the registered scoring run.

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

"The inconclusive state" is the state in which the committed score record carries the status inconclusive. It is the state of the paper. Rules 1 to 9 apply in that state only; in every other state the paper stays as registered before this amendment. Rules 3, 4 and 9 give the words for the cause that occurred: possible lost targets above the registered share, with the contrasts printed. For the other causes of an inconclusive test (a data check that could not be repaired, a newcomer without a complete forecast, fewer than 60 newcomers beside an unclean join), which did not occur, the registered sentences on the cause stand, and the alternatives are given under each rule.

Every number in the sentences below is read from the committed score record or from a committed summary by the renderer. None is typed.

### 1. The read-out of the league numbers, where the paper names it (replaces, in the inconclusive state, the clause of Amendment 13, rule 1)

In the first section and in the conclusion, "the frozen 2026–27 test carries a registered read-out for this gain" becomes:

> the frozen 2026–27 test carried a registered read-out for this gain and is inconclusive

### 2. The two tests outside the fitted arrivals (replaces the last clause of the paragraph of Amendment 19, rule 9)

"Neither settles the other; the frozen 2026–27 test is the registered test on arrivals." becomes:

> Neither settles the other; the frozen 2026–27 test, the registered test on arrivals, is inconclusive (next section).

### 3. The section on the frozen test: the outcome first, then the design in the past tense

The section opens with the outcome. Its first paragraph:

> The test was scored once, on 25 November 2026, and is inconclusive. Of the 200 newcomers who had reached eight continental games, 94 had a frozen forecast under their name and 106 did not. A newcomer has no frozen forecast when he has no 2025–26 season in the frozen file, or when the two sources write his name differently; no name is joined by hand. 7 of the 106 may be players in the frozen file under another spelling: set against the 94 joined newcomers that is 7.4%, above the 5% we allowed in advance [Amendment 8]. No replication or equivalence conclusion is drawn.

The sentence "For the record only, on the 94 newcomers that could be scored, …" with the three primary contrasts, and "No sentence is licensed by these values (Appendix L).", follow in the same paragraph, word for word as registered. The sentence "The frozen test is inconclusive because its required data or validity controls did not pass" and the clause "the scoring record documents the unresolved controls" are not printed.

The second paragraph is the design, as registered, with the verbs of the November scoring in the past: "They were scored on continental games through 24 November 2026, for newcomers who reached eight games; below 60 newcomers the test would have been descriptive only." "As registered, we did not expect the first to be detectable in November: it looked for an effect near 0.065 EFF/36, its 2020–2025 estimate." "Appendix L gives the rule for a failure to replicate and what the test could detect." No other word of that paragraph changes. The paragraph on the re-score of February 2027 stands as registered, last.

For another cause: the first sentence reads "The scoring run was made once, on [date], and the test is inconclusive.", the registered sentences on that cause follow unchanged, and the second paragraph is the same.

### 4. Limitations (adds to the entry "Frozen test")

The entry begins with the outcome, before "Partial-season outcomes":

> **Frozen test.** Inconclusive: 7 newcomers without a frozen forecast may be in the frozen file under another spelling, 7.4% of the 94 joined, above the 5% allowed in advance.

For another cause: "**Frozen test.** Inconclusive; the section on the test gives the cause."

### 5. Related work and Appendix O (replaces, in the inconclusive state, the end of the sentence of Amendment 16, rule 6)

"…, and its tests on league changes and on frozen forecasts." becomes:

> …, and its test on league changes; its test on frozen forecasts is inconclusive.

### 6. Appendix L: the contrasts printed for the record carry no reading word (adds to Amendment 19, rule 12)

In a state that is not scored, the paragraph "The contrasts on the newcomers that could be scored (no sentence is licensed)" introduces each weighted value with the label "weighted by playing time". The words "not clearly above zero when weighted by playing time" are a registered reading (Amendment 8) and are not used in that paragraph. No value changes.

### 7. Appendix L: what the test could detect (adds to Amendment 19, rule 12)

The paragraph that was written as a plan is printed as what it was. Its heading becomes "What the frozen test could detect." The sentence "The realised number of newcomers and a recomputed detectable effect are reported with the result." and the sentence that follows it become:

> Before scoring, the registration expected that at 100–150 newcomers the test could detect an increment of about 0.075–0.092 EFF/36, and a gain over history of 0.244–0.298, which is larger than the 0.161 in Table A24, so that a null there would have meant "not detectable", not a contradiction. 94 newcomers were scored; the detectable effects recomputed at that number are printed below.

After the rule for a failure to replicate, which stands word for word, one sentence is added: "The rule was not applied, because the test is inconclusive."

### 8. Appendix N: the named pairs (adds to the note on Amendment 20)

After "Five named pairs of newcomers in the main text once the frozen test is scored, and further wording, were allowed on 18 November 2026, before scoring [Amendment 20].":

> The pairs and the tables of named newcomers are not printed, because the test is inconclusive.

### 9. The last sentence of the abstract and of the conclusion (replaces, in the inconclusive state, the ending of Amendment 8)

"Forecasts frozen on 3 November 2026, after the season began but before outcome inspection, could not be scored cleanly, so the registered test is inconclusive." becomes:

> Forecasts frozen on 3 November 2026, after the season began but before outcome inspection, were scored once on 2026–27 newcomers. That test, separate from the test on league changes, is inconclusive: 7 newcomers without a forecast may be in the frozen file under another spelling, more than the 5% of the 94 joined newcomers that was allowed in advance.

The abstract stays within its limit of nine numbers (Amendment 17). For another cause, or in a paper that does not print the test on league changes, the ending of Amendment 8 stands.

### 10. The league gaps grew from refit to refit (adds to the reading of Amendment 3, E19)

The paper says that in every yearly refit every tier-3 league needed a higher domestic rate than every tier-1 league, and that this describes stability. Table A11 also shows that the gaps to Spain grew. In the section "What a club can use", after the sentence that ends "(Appendix H: Figure A3, Table A11).":

> The order was stable; the size of the gaps was not. For EuroLeague arrivals the nine other leagues stood on average 1.2 EFF/36 above Spain's 16 in the refit that forecast 2020–21 and 2.4 in the refit that forecast 2025–26, against 2.0 in the full fit of Table 1. The cause was not examined.

Appendix H, beside Table A11, repeats the three means and gives them for EuroCup arrivals (1.2, 2.1 and 1.8). The means are computed by the renderer from the committed table of refits; the values above are the ones it gives today. This is a description of printed values, written after they were seen. It is not a test and licenses no statement about why the gaps grew.

### 11. The size of what the source league adds (adds to the reading of Amendment 9, E28a)

At the end of the paragraph "What the league numbers are worth":

> In size, the gain over the destination-only forecast is about 2% of that forecast's mean absolute error (2.989 EFF/36). By competition it is 0.119 (interval 0.007 to 0.230) for the 194 EuroLeague arrivals and 0.044 (interval −0.013 to 0.101) for the 480 EuroCup arrivals. The two values by competition carry no registered reading, and their difference was not tested.

Amendment 9 prints the values by competition "without a licence", in Table A19. They stay without one: the sentence gives them as values and says so. Both competitions are printed, whatever they show.

## Gates

| Gate | Pass rule | Negative control |
|---|---|---|
| G26a the read-out | in the inconclusive state the clause of rule 1 stands in the first section and in the conclusion, and "carries a registered read-out for this gain" is in no part of the paper; in every other state that is not scored the clause of Amendment 13 stands | an inconclusive paper with the old clause must be refused; a pending paper with the new clause must be refused |
| G26b the section | in the inconclusive state the section on the frozen test begins with the sentence that dates the scoring and gives the outcome, before the design; the counts, the share, the limit and the date equal the score record; the design paragraph holds neither "They are scored" nor "we do not expect" | a section that begins with the design must be refused; with one count of the record changed, the sentence must change |
| G26c the outcome wherever the test is named | in the inconclusive state the paper holds none of: "is the registered test on arrivals", "on league changes and on frozen forecasts", "could not be scored cleanly", "What the frozen test can detect"; the Limitations entry "Frozen test" begins with "Inconclusive"; the sentence of rule 8 stands in Appendix N | a text with any one of the old wordings must be refused; a Limitations entry without the outcome must be refused |
| G26d no reading word under "no sentence is licensed" | in a state that is not scored, the paragraph of the contrasts printed for the record holds no registered reading: not "not clearly above zero", "not detectable", "detectable at this n", "held", "failed", "improves" or "more accurate" | a paragraph with "not clearly above zero" must be refused |
| G26e the abstract | in the inconclusive state with possible lost targets above the share, the abstract and the conclusion end with the sentences of rule 9, their numbers equal the score record, and the abstract holds at most nine numbers | an abstract with the ending of Amendment 8 must be refused; an abstract one number over its limit must be refused |
| G26f the two descriptive sentences | the sentences of rules 10 and 11 stand once each, in the paragraphs named; their values are computed from the committed table of refits and the committed E28 summary; rule 10 carries "The cause was not examined" and rule 11 carries "no registered reading" and "was not tested" | with one refit value changed the means must change; a text without either caveat must be refused; a text that prints one competition without the other must be refused |

If a gate fails, the paper is not rendered and Amir is told.

## Threats and their controls

| Threat | Control |
|---|---|
| Wording chosen after the result to make an inconclusive test read better | every rule either states the outcome or removes a word that reads as a verdict; no rule adds a favourable statement about the frozen test; the values printed for the record and the words "No sentence is licensed by these values" are unchanged |
| A conclusion drawn from the frozen test through the new words | rules 1 to 9 use the registered facts of the join (counts, share, limit, date) and no contrast; gate G26d refuses a reading word beside the contrasts |
| The registered words lost from view | this amendment prints each sentence before and after; the earlier renders (48 to 50) are retained runs; the score record is not edited |
| Descriptive sentences picked because they flatter the paper | rule 10 says that the paper's gaps were not stable in size; rule 11 gives the gain as about 2% of the error and prints both competitions, one of which has an interval that includes zero |
| The seven names treated as known lost targets | the sentences say "may be"; no name is joined by hand; the record's words are "possible lost targets" and its count is a lower bound |
| The abstract growing past its limit | gate G26e; the limit of nine numbers (Amendment 17) is unchanged |

## Not part of this amendment

* **No number, interval, verdict or status changes**, and the score record is not edited. No name is joined by hand, and no second scoring run is made.
* **The frozen test stays inconclusive.** Nothing here reads its contrasts.
* **The re-score of February 2027** stays as registered (Amendments 1 and 8). This amendment says nothing new about it.
* **E34 and the narrower statement on prior work** (Amendment 23, rules 4 and 5) are not changed. Both wait for the pages to be read.
* **The sentence of Amendment 24 in Appendix N** on the order of reading is not changed.
* **No section is moved and no registered sentence on the examined seasons is rewritten.** The readers' wider proposals (the table before the results, a new order of the results, fewer references to registrations) are not taken up for this paper.
* **Repairs made in the same render that touch no registered sentence**: the two slopes of E33 with one intercept per season enter Table A21, where Amendment 22 says they are printed; the caption of Table A24 names the rows that Figure 3 draws; one sentence beside Table A8 says that one outcome exceeds its forecast by less than the table's rounding; Appendix A says which increments its range covers; and three small slips (a pointer of Appendix L to itself, one number printed without its comma, one apostrophe).

## Scope boundary: nothing pinned changes

No registered analysis, estimate, interval, threshold, verdict, forecast or frozen file is changed. No generator of an analysis is edited by this amendment. The frozen 2026-27 forecasts and the score record are read only as committed.
