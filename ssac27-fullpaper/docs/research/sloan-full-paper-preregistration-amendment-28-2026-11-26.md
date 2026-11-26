# Amendment 28 to the SSAC27 full-paper pre-registration: thirteen repaired sentences, four sentences that define the paper's terms, the figures redrawn in one style, and the Paper ID line

**Approval record.**

| | |
|---|---|
| Amends | `docs/research/sloan-full-paper-preregistration-2026-11-03.md`, as amended through Amendment 27. It repairs the wording of sentences that no registration fixes, adds four sentences of definition, lets the ten figures be redrawn without a change to any number or registered figure text, and fixes how the Paper ID line reads. It changes no registered sentence and removes none |
| Written | 2026-11-26, by Claude Science, **after every result of the paper was known to the author**, after the frozen 2026-27 test was scored (inconclusive), and after three readers had read the final paper (render 55). What the author has seen is listed in the exposure disclosure |
| Approved by | Amir, 2026-11-26, in answer to four questions: text repairs "Errors + 34 serious (Recommended)"; figures "All ten (Recommended)"; the Paper ID line "Paper ID: 47 (Recommended)"; length "Keep 13 pages (Recommended)". The full text of this file and its sha256 were shown to Amir before it was committed |
| Basis | committed and pushed **alone**, before the code that implements it |

**This amendment registers nothing in advance.** Every result it touches was known when it was written. It is the dated record of changes to wording and drawing, made in the open so that a reader can see when they were made and why. It adds no analysis and no contrast and changes no number.

## Why this exists, in plain words

Amir read the final paper in Word and asked for a review of all its text and for figures that are easier to read. Three readers who saw only the paper then read render 55 on 26 November 2026: one recomputed every number that can be checked from the paper itself, one read every sentence for language, and one read it as a conference judge. No headline number was wrong. They found two places where words and numbers disagree, a handful of pointers that lead to the wrong place, terms that the paper uses and never defines, and many sentences that need two readings.

Gate G19c of Amendment 19 keeps every sentence of the paper before the cut (render 39) in the paper. A repair to such a sentence therefore needs a dated record, and this is it. Most of the hard sentences that the readers listed are words that an earlier amendment fixes; those stay as they are, and the last rule lists them.

## What has already been seen (exposure disclosure)

* **The author has seen every result of the paper,** the whole score record of the frozen 2026-27 test and the record of E34.
* **The three readers saw the real paper with its real values** (render 55, the final render of 25 November 2026, and its ten figures). Their lists are kept with the session's records.
* **The repairs were drafted, and the paper composed with them, in a working copy before this file was written.** That is how the lists below were made: they are the sentence-by-sentence difference between render 55 and the composed paper. Nothing of it was committed to the repository or pushed before this file.
* **Nothing here is a test.** No outcome is read, no estimate is computed and no generator is run.

## The rules

### 1. Thirteen sentences of render 39 stand in a repaired form

Each sentence on the left is a kept sentence of gate G19c that no registration fixes. The paper prints the form on the right exactly once and no longer prints the sentence on the left. "[#]" stands for a citation and "#" for a table or appendix label, as in the fixture of gate G19c. No number changes.

| Repair | Sentence of render 39 | Repaired form | Reason |
|---|---|---|---|
| 1 | European clubs recruit from domestic leagues whose box scores are not directly comparable. | European clubs recruit for EuroLeague and EuroCup from domestic leagues whose box scores are not directly comparable. | The abstract never named the two competitions, yet spoke of arrivals, of the destination and of league changes (language review of 26 November 2026). |
| 2 | The target is a player arriving in EuroLeague or EuroCup with at least eight domestic games the preceding season, eight continental games in the arrival season, and no regular continental role the preceding season. | The unit of study is an arrival: a player who enters EuroLeague or EuroCup with at least eight domestic games in the preceding season, at least eight continental games in the arrival season, and no regular continental role in the preceding season. | The paper's key term 'arrival' was never defined as a term (language review of 26 November 2026). |
| 3 | The analyses beyond the submitted abstract were registered before execution [#], except the few items marked as unregistered or descriptive where they appear. | The analyses beyond the submitted abstract were registered before execution [#] (later registrations are cited where their analyses appear), except the few items marked as unregistered or descriptive where they appear. | The citation range ends at Amendment 11; the clause says where the later registrations are cited (fact check of 26 November 2026, F22). |
| 4 | We froze forecasts from every model for all 2025–26 domestic player-seasons, for both competitions (3,478 forecasts), and committed and pushed them on 3 November 2026, 10:55 UTC, after the season had begun but before any 2026–27 statistic was read [#]. | We froze forecasts from every model for all 2025–26 domestic player-seasons, for both competitions (3,478 rows, each with the forecasts of every model), and committed and pushed them on 3 November 2026, 10:55 UTC, after the season had begun but before any 2026–27 statistic was read [#]. | The main text said 3,478 forecasts and Appendix I said 3,478 rows with the forecasts of 17 models each; the count is of rows (fact check, F01). |
| 5 | This comparison changes domestic rate and history together; with history held fixed the conversion differs. | This comparison changes domestic rate and history together; for a player whose career history differs from his domestic rate the conversion differs. | 'With history held fixed' is a form of a phrase the paper does not use in its own voice (Amendment 12); the new words say the same condition. |
| 6 | **Frozen test.** Partial-season outcomes; for four source leagues (and ABA) domestic data stop in January 2026, and 250 Spanish ACB rows lack official stat corrections. | Partial-season outcomes; for five of the ten source leagues (France, Turkey, Lithuania, VTB and the ABA League) the 2025–26 domestic data stop in early January 2026, and 250 Spanish ACB rows lack official stat corrections. | 'Four source leagues (and ABA)' could not be read: the ABA League is a source league. The registration of 3 November 2026 names the four leagues and the recipes report adds the ABA League (fact check, F08). |
| 7 | **Intervals** leave out refitting uncertainty. | **What the intervals leave out.** The paired comparisons on arrivals take the fitted forecasts as given, so their intervals leave out the uncertainty of refitting the models. | Two bold fragments became one sentence that says what the intervals leave out. |
| 8 | An arrival can have several. | An arrival can meet several of these conditions. | 'Can have several' had no noun. |
| 9 | The boosted model in Appendix # is not in this panel; its upper bound is above 2%.](figures/figA1_robustness.png) | The boosted model (Appendix #, Table #; discussed in Appendix #) is not in this panel; its upper bound is above 2%.](figures/figA1_robustness.png) | The boosted model's table is in Appendix E (Table A5); Appendix J discusses it (fact check, F04). |
| 10 | Of the 39 registered comparisons whose registered intervals do not overlap, 14 also do not overlap under the ratio of sums. | Of the 39 registered comparisons whose registered intervals do not overlap, 14 keep the same order with intervals that do not overlap under the ratio of sums. | The count is of comparisons that keep the same order with intervals that do not overlap under the ratio of sums; 'also do not overlap' fits 19 pairs, not 14 (fact check, F02). The number is unchanged. |
| 11 | France points the same way (−1.11) but does not survive the adjustment for testing ten leagues. | France points the same way (−1.11), but its bias is not detectable after the adjustment for testing ten leagues. | 'Does not survive the adjustment' is jargon; the new words say what the adjustment decides. |
| 12 | With the forecast blind to both leagues, only Italy does (Appendix Table # shows every version, including the first-registered errors). | With the forecast blind to both leagues, only Italy's bias is detectable after that adjustment (Appendix Table # shows every version, including the first-registered errors). | 'Only Italy does' had its verb two clauses back. |
| 13 | And Italy stays underrated by the league table itself (−0.66, interval −1.31 to −0.04). | And Italy stays underrated by the league-aware forecast itself (−0.66, interval −1.31 to −0.04). | The forecast that underrates Italy is the league-aware forecast; 'the league table itself' named the table for the forecast. |

Repair 6 changes a later form of Amendment 26, rule 4. That rule fixes the entry's first sentence (the outcome of the frozen test); the sentence repaired here is the one that follows it, "as a sentence of its own", and it still begins with "Partial-season outcomes;". The four leagues are named in the registration of 3 November 2026 ("They stop in early January 2026 for Turkey BSL, France Pro A, VTB and Lithuania LKL") and the fifth in the recipes report of the same day ("ABA League 2025-26 data also stop in early January 2026"). Table A21 keeps the registered label of sensitivity S-e (3), which speaks of the four.

### 2. Nine places in text written after render 39

These sentences are not among the kept sentences of render 39, and no registration fixes their words. Their numbers are unchanged.

| Place | Before | After | Reason |
|---|---|---|---|
| First section, second paragraph | The slope measures the average change beyond a stayer's forecast per unit of change predicted by the EuroCup equivalents. | The slope is the average change in a mover's rate, beyond the forecast for a player who stays in his league, per unit of change that the EuroCup Equivalents predict. | 'A stayer's forecast' and 'the EuroCup equivalents' were used before they were explained. |
| First section, second paragraph | … on 180 older arrivals from seasons no model saw (Figure 3). | … on 180 older arrivals from seasons no model saw (Figure 3 draws the first). | Figure 3 shows the arrivals of 2020–2025 only (fact check, F03). |
| First section, paragraph of cautions | … on average for the league-aware forecast (0.96 weighted by playing time). | … on average for the league-aware forecast, the one that uses the league numbers (0.96 weighted by playing time). | First use of 'league-aware forecast', which the main text did not define. |
| Results, 'What was unseen' | The table was not fitted to these league changes and not scored on them before this test; the same seasons are inputs to the paper's forecasts. | The table was not fitted to these league changes and not scored on them before this test. But the same seasons are inputs to the paper's forecasts, so the test and the fitted data overlap in time. | The second clause is a caveat and read like a continuation; the next sentence speaks of 'that overlap in time', which had not been stated. The words fixed by Amendment 19, rule 4, stand. |
| Results, the margin | … is a coarse statement on that scale (Appendix J). | … is a coarse statement on that scale (Appendix J discusses the margin). | Appendix J does not hold this comparison; it discusses the margin (fact check, F14). |
| Results, 'Two tests outside the fitted arrivals' | League changes: ten leagues, 3,423 changes, 2016–17 to 2025–26, domestic outcomes (Proballers box scores), registered before any outcome was read: evidence that the table's gaps show up when players change league, in seasons the table was fitted on. Older arrivals: two leagues, 180 arrivals, 2008–09 to 2015–16, continental outcomes (the leagues' own box scores), the league-number comparison added after the first scoring: the only evidence on an earlier period, where the league numbers did not help. | The test on league changes covers ten leagues and 3,423 changes, 2016–17 to 2025–26. Its outcomes are domestic, from Proballers box scores, and it was registered before any outcome was read. It is evidence that the table's gaps show up when players change league, in seasons the table was fitted on. The test on older arrivals covers two leagues and 180 arrivals, 2008–09 to 2015–16. Its outcomes are continental, its domestic box scores are the leagues' own, and its league-number comparison was added after the first scoring. It is the only evidence on an earlier period, where the league numbers did not help. | Two verbless lists with two colons each became sentences. The old words could be read as if the continental outcomes came from the domestic leagues' box scores. The facts are those of Amendment 19, rule 9, and the closing sentence is unchanged. |
| Limitations, last paragraph | **Arrival forecast errors.** Paired comparisons condition on the fitted arrival forecasts. | **What the intervals leave out.** The paired comparisons on arrivals take the fitted forecasts as given, so their intervals leave out the uncertainty of refitting the models. | Statistics shorthand; with repair 7 of rule 1 the two fragments are one sentence. |
| Appendix K, 'League biases' | Three caveats. | Three caveats apply. | A fragment. |
| Appendix L | With the coefficients of the fitted equation as printed in the main text, the result is within 0.02 EFF/36 of the model for rates up to 35. | A forecast computed from the coefficients of the fitted equation as printed in the main text is within 0.02 EFF/36 of the model's own forecast for rates up to 35. | 'The result' had nothing to refer to. |

### 3. Four added sentences that define the paper's terms

| Place | Sentence |
|---|---|
| Data and methods, 'Players and outcome' | A season is named by the year in which it starts, so 2020–2025 stands for the six seasons 2020–21 to 2025–26. |
| Data and methods, 'Forecasts and estimation' | We call these three the history-only, the destination-only and the league-aware forecast; each can be fitted without or with translation. |
| Data and methods, 'Forecasts and estimation' | The ten league numbers are the conversion table (Table #); a league's Equivalent restates its league number as the domestic EFF/36 that forecasts like a 16 in Spain's ACB. |
| Appendix H, 'Stability and close calls' | Tiers follow the rule registered before the analysis [#]: leagues are sorted by point estimate within a destination, and a league starts a new tier when the top league of the current tier exceeds it in at least 90% of bootstrap draws; otherwise it joins that tier. |

The first three define terms that the paper uses from its first page on: how a span of seasons is written, the names of the three forecasts, and the difference between a league number and an Equivalent. The fourth states the tier rule in the words of the registration of 3 November 2026; until now the paper used tiers in Figure 1, Table 1, Table A8 and Figure A3 and nowhere said how they are formed. None of the four states a result.

### 4. The figures

All ten figures of the paper may be redrawn in one style, under these limits:

* **No number, caption or data changes.** Every caption stays word for word, with one exception: the last sentence of the caption of Figure A1 is repair 9 of rule 1. Every figure draws the values it drew before, from the same committed files.
* **Printed values are plotted values.** A figure may print beside a mark the value that the mark draws, read from the same committed file and rounded as the paper rounds it. A figure computes nothing that is not in a committed file (Amendment 16, rule 7).
* **Figure 1 keeps every word.** Its titles, legend lines and notes are fixed by Amendments 14, 16, 17, 19, 20 and 21 and are not touched; only typeface, text size, colour and the size of marks change.
* **One word changes in a legend.** The legend of Figure A7 said "ratio of totals"; its caption and Table A3 say "ratio of sums", and the legend now says the same.
* **Added information.** Figure 2: the two plotted values beside each row, a cue on each side of zero for the meaning of the sign, and the three leagues of the registered licence in bold (the asterisk stays). Figure A3: each line named at its right end. Figure A4: the six shares of the league-aware forecast and the number of pairs in each bin. Figures A1, A2 and A5: each plotted estimate printed. Figure A7: the two rows that its title names in full colour, the others lighter. Figure A1: the 2% margin drawn as a pale band with dashed edges.
* **The typeface** is Source Sans Pro (SIL Open Font License 1.1), shipped with the code so that the figures are the same on every machine.
* **Sizes.** Every figure stays 6.5 inches wide. Four become slightly taller to hold the added text: Figure 2 (3.0 in), Figure A3 (3.0 in), Figure A4 (2.8 in) and Figure A6 (2.6 in).
* **The figure of the frozen test** is not printed in the inconclusive state (Amendment 25) and is not changed.

### 5. The Paper ID line

Under the title the conference template has the lines "Paper Track" and "Paper ID". The Word file prints "Basketball" and "Paper ID: 47" (before: "47").

### 6. Appendix N and the reference

Appendix N carries, as a paragraph of its own with the label "Repairs of wording and drawing", one sentence: "On 26 November 2026, after three readers had read the final paper, thirteen sentences were repaired, four sentences that define the paper's terms were added and the figures were redrawn in one style; no number and no registered sentence changed [Amendment 28]." The reference to this amendment says that it was written after every result was known and that it registers nothing in advance.

### 7. What stays as it is

* **Registered and decided words stay.** The readers also listed sentences whose words an earlier amendment fixes or an earlier decision settled, among them: "need only past arrivals" in the abstract (decision of 12 November 2026; Amendment 21, rule 1); "joined newcomers" (Amendment 26); "the interval is wider than the margin" (Amendment 7); "not clearly above zero when weighted by playing time" beside a negative estimate (Amendment 10); the sentences of E33 and E34 (Amendments 22, 23 and 25); "What the size means" (Amendment 19, rule 5); "this interval is two-way clustered, where the first is a cluster bootstrap" (Amendment 12); the sentence on changed comparisons (Amendments 3 and 16); and the "built-in comparison" (text decision of 17 November 2026). They are printed as they stand. Each prints its numbers beside its words, so a reader can check the words against them.
* **The length stays.** Amendment 19, rule 11, says what may not move to the appendix, and "no unfavourable reading leaves the main text". The blocks that a reader would move are on that list. Nothing moves.
* **Open points that the paper does not settle** are listed in the review report kept with the session's records: two counts of one linking rule in Appendix A (442 arrivals confirmed by it, 445 matched by it), the base of the measured name-link weakness (282 links), the median of the yearly moves of the Equivalents (0.25, from unrounded values of both competitions), values that are stated once with no table behind them, and the order of the appendix table numbers.

## Gates

| Gate | Pass rule | Negative control |
|---|---|---|
| G28a the amendment | the renderer holds this file's sha256 and the file equals it | a changed byte must fail |
| G28b the repairs | each repaired form of rule 1 stands in the paper exactly once and its sentence of render 39 does not; the fixture of gate G19c lists the thirteen, each with this amendment's repair number and its reason | a paper that holds a sentence of render 39 beside its repaired form must fail; a fourteenth entry must fail |
| G28c the note | the sentence of rule 6 and the reference to this amendment stand in Appendix N | a text without the note must be refused |
| G28d nothing registered moves | the abstract differs from that of render 55 by repair 1 only, and the conclusion is byte for byte that of render 55; every test of Amendments 7 to 27 that compares the paper with registered words passes unchanged | a second changed sentence in the abstract must fail |
| G28e the figures | every caption is word for word that of render 55, except the sentence of repair 9; the figure tests of Amendments 16, 19, 20, 21 and 25 pass; no drawn text leaves its figure or is cut at the edge | a figure with a changed caption must fail |

The hashes of the papers in the states of the frozen test that are not scored (the fixture of Amendment 25) are replaced, as that fixture's rule foresees for a later registration; the earlier values are kept in it.

## Threats and their controls

| Threat | Control |
|---|---|
| A repair changes what a sentence claims | each repair is listed with both forms; no number changes; registered words are not touched (rule 7, gate G28d) |
| A redrawn figure shows other values | the figures read the same committed files; printed values are the plotted ones; the claim checks of the figure code are unchanged (gate G28e) |
| Wording changed after results is read as registered wording | this file says in its title lines, in the reference the paper prints and in Appendix N that it was written after every result was known and registers nothing |
| An unfavourable reading softened or moved | no registered sentence changes and nothing moves between main text and appendix (rule 7) |

## Scope boundary: nothing pinned changes

No registered analysis, estimate, interval, threshold, forecast or frozen file is changed. No registered sentence is changed or removed. No generator is edited and nothing is run. E34 is not run again (Amendment 23, stop rule). The score record of the frozen test is not edited.

## Specification

This amendment changes wording and drawing only. The block is here because every research note in this repository carries one; it registers nothing new.

| Field | Registered choice |
|---|---|
| Unit | Unchanged |
| Population | Unchanged |
| Estimator | Unchanged |
| Null | Unchanged |
| Filter | Unchanged |
| Key | Unchanged |
| Uncertainty | Unchanged |
