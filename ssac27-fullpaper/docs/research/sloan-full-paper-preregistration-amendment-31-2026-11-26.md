# Amendment 31 to the SSAC27 full-paper pre-registration: four corrections to the account that Amendment 29 gives of the work of 26 November 2026

**Approval record.**

| | |
|---|---|
| Amends | Amendment 29 (`docs/research/sloan-full-paper-preregistration-amendment-29-2026-11-26.md`, pushed alone as `25aba6635`), in four places where it describes what was done, seen or said on 26 November 2026. **The paper does not change:** no sentence, number, figure or reference. Render 59 stands as it is, and the paper does not cite this file |
| Written | 2026-11-26, by Claude Science, **after every result of the paper was known to the author**, after Amendments 29 and 30 were pushed and implemented and the final render was made |
| Approved by | Amir, 2026-11-26. He was told of the three points of rules 1 to 3 and asked how to record them; his answer: "Short Amendment 31 (Recommended)". Rule 4 is of the same kind and was found while this file was written. The full text of this file and its sha256 were shown to Amir before it was committed |
| Basis | committed and pushed **alone**. No code implements it; the public hash list gains its row |

**This amendment registers nothing in advance.** It corrects a record. It adds no analysis, no contrast and no wording of the paper.

## Why this exists, in plain words

Amendment 29 was written from the reports of five readers. A background reviewer of the working session compares such reports with what the readers actually did. After Amendment 30 the author went through the reviewer's notes of the day and compared Amendment 29 with the readers' own records. In four places Amendment 29 says less, or more, than those records. None touches a result or a sentence of the paper. Amendments are not edited after their push, so the corrections stand here.

## The rules

### 1. What the reader of the Gaussian Hoops board displayed (exposure disclosure of Amendment 29, third point)

Amendment 29 says: "While searching the page's data he displayed two fragments of it (one count of games, no performance value of 2026-27)." The reader's own note says more, and it is the full account:

* While listing the keys of the page data he displayed the block `deckung`: for each group of players and each measure, the count of this season's scored players inside the board's projected range. These are values of 2026-27. He left them out of his note on purpose.
* In his first session he displayed two fragments of player records (one count of games).
* He looked, with a few lines of code, at whether the board's projected change for newcomers differs by the league they came from, using last season's values and the projections in the page data and no value of 2026-27. For each measure he compared the share of variance explained with and without 7 to 9 indicators of the source league, on 54 to 64 players. The share rose in every measure, as it must when regressors are added; no adjusted value and no test was computed. His note says that this "gave no clear answer" and draws nothing from it. The paper draws nothing from it.

All of this was done on 26 November 2026, after the frozen 2026-27 test was scored on 25 November 2026; Amendment 23, rule 4, and Amendment 24 allow the page to be read then. No value of 2026-27 from that page, and nothing from the reader's look at the projections, is used anywhere in the paper.

### 2. One more key in the page data of that board (rule 4 of Amendment 29, "What was found")

Besides the three unprinted fields that Amendment 29 names, the page data hold an unprinted key `fassung` ("version"). It names a version per measure: "naiv" for true shooting and field-goal percentage, "liga" for three-point percentage, "final" for the other five. The page code never uses it, no text explains it, and it carries no figure. It may mean that the site has versions of its projection that differ in how they use the league; the page does not say.

The key compares nothing and reports no accuracy. So the reading of Amendment 23, rule 4, that Amendment 29 records is unchanged, and so are the paper's sentences: the page data hold no pair of errors for one forecast with and without the league level, and "nothing on it compares the projection with and without the league level" (Appendix O) is true of the page and of its data. The literature ledger recorded the key on 26 November 2026. Amir had not been told of it when he chose "keep and disclose"; he was told afterwards, with this reading, and did not change the decision.

### 3. What the three blind readers were told ("Why this exists" of Amendment 29)

The instruction given to each of the three readers said of the two first pages: "They report the same study and the same numbers; they differ only in wording and order." That was not exact. The proposed page brings to the first page five numbers that the paper prints elsewhere (14.3, 16.3, the gap of 2.0 between them, ±4.8 and "about 2%") and one statement that the current page did not have (what the search did not find). The readers had both pages in front of them and named these additions in their reasons. Their preference and their scores are as Amendment 29 reports them; they were given under an instruction that understated the difference.

### 4. What the reader of the numbers checked ("Why this exists" of Amendment 29)

Amendment 29 says that one reader "checked every number against the paper itself and the committed result files". By his own record:

* of the 2,408 numbers that the paper's number manifest traces to a result file, he matched 1,925 to their source value by script and 165 through three tables; the other 318, which depend on several source values or on text records, he covered by arithmetic and reading and did not match one by one;
* of the 1,303 literal numbers (labels, dates, citation and cross-reference numbers, the reference list) he checked the cross-references and citation numbers; the numbers inside the reference list he did not check;
* the 138 typed constants he sorted by kind and named a source for each kind; he did not compare each with a file. The author went through the 49 distinct values on 26 November 2026. Those that state a quantity agree with a table of the paper, a registration or a committed file: the counts of the two audits, the values of E34 that stand in sentences, the minimum of 60 newcomers, the floor of 75 players for a pair, the upper rate of 35 for the fitted equation, the bound of 3.4%, the 100 to 150 newcomers of the power table, and 755 of 1,013. The rest are labels: tier numbers, the edges of bins, the 36 of the unit, "top 10", the 1 of an indicator. For one threshold ("Reliability below 0.40 makes the corrected value unreadable", caption of Table A4) the author found no registration; it is a rule of presentation;
* he recomputed no result from raw data; interval ends, p-values, bootstrap shares and power values were compared with the committed summary files.

"No result of the paper is wrong" in Amendment 29 rests on these checks and has these limits.

## Gates

| Gate | Pass rule | Negative control |
|---|---|---|
| G31a the amendment | the private copy of the public hash list holds this file's sha256, and the file equals it | a changed byte must fail |
| G31b the paper | the paper names no Amendment 31, and the committed manuscript is that of render 59 | none |

## Scope boundary: nothing pinned changes

No registered analysis, estimand, file, forecast, licence or gate is changed. No sentence of the paper changes. No generator is run and nothing is rendered.

## Specification

This amendment corrects a record. It defines no analysis.

| Field | Registered choice |
|---|---|
| Unit | Unchanged |
| Population | Unchanged |
| Estimator | Unchanged |
| Null | Unchanged |
| Filter | Unchanged |
| Key | Unchanged |
| Uncertainty | Unchanged |
