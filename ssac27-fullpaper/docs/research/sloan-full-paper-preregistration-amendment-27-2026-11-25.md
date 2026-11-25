# Amendment 27 to the SSAC27 full-paper pre-registration: one sentence that points from the comparison with a published league table to its exploratory reading on the older arrivals

**Approval record.**

| | |
|---|---|
| Amends | `docs/research/sloan-full-paper-preregistration-2026-11-03.md`, as amended through Amendment 26. It adds one place to the list of Amendment 23, rule 5 ("What the paper may say") where the paper speaks of E34: one sentence in the main-text paragraph "A published league table on the same players", with a note in Appendix N. It replaces no sentence and removes none |
| Written | 2026-11-25, by Claude Science, **after E34 was run, with its record committed (commit `7726fb27e`) and every value in it known to the author**, after the frozen 2026-27 test was scored, and after a reader who saw only the paper (render 53) had read it. What the author has seen is listed in the exposure disclosure |
| Approved by | Amir, "Add it, with the direction (Recommended)", 2026-11-25, in answer to a question that gave the result of E34 with its values, the reader's observation, the sentence of rule 1 word for word and two alternatives (a pointer without the direction; no sentence), and that said the sentence needs a short dated Amendment 27, written after the result, that registers nothing in advance |
| Basis | committed and pushed **alone**, before any code follows it |

**This amendment registers nothing in advance.** Every result it touches was known when it was written. It is the dated record of one added sentence, made in the open so that a reader can see when the sentence was written and why. It adds no analysis and no contrast and changes no number.

## Why this exists, in plain words

The paper compares its league numbers with a league table printed in 2015 on three samples. Two comparisons were fixed by Amendment 15 before they were run: on league changes (E31b, registered before the league changes were read) and on the 674 arrivals of 2020-2025 (E31a, exploratory). On both, the two cannot be told apart, and the paragraph "A published league table on the same players" ends its account with "On neither sample can the two be told apart, which is not the same as equal." The third comparison is E34, on the 180 older arrivals. It is exploratory, it is printed two sections later, and it went against the paper: weighted by playing time, the 2015 table was the more accurate.

A reader who saw only the paper found every sentence true as written and pointed to one gap: a reader of that paragraph, or of the abstract, is not told that a third comparison exists and went the other way. Amendment 23 names the places where E34 is printed and this paragraph is not among them. This amendment adds it, with one sentence that prints no number.

## What has already been seen (exposure disclosure)

* **The author has seen the whole record of E34** (`docs/research/artifacts/sloan-fullpaper-published-scales-older-2026-11/summary.json`, sha256 `99eb29cc3e2ee2871fa1b631bdd18a5d5c5138db8be2c92ada5374b2e8859097`, from the one retained run of 25 November 2026). For the 2015 table against the paper's league numbers on the 180 older arrivals, the error with the table minus the error of the league-aware forecast is -0.063 EFF/36 unweighted (95% interval -0.128 to 0.002) and -0.082 weighted by playing time (-0.152 to -0.011). Amendment 23 had listed the same values as seen on 22 November 2026.
* **The author has seen the whole score record of the frozen 2026-27 test** and every result of the paper.
* **The sentence was written after a reader had read the paper with E34 in it** (render 53, 25 November 2026). The reader saw the real paper and its real values. His list is kept with the session's records. His other observations are listed under "Not part of this amendment".
* **Amir chose the sentence with the result of E34 before him.** The question put to him printed the two weighted values of E34 with their intervals.

## The rule

### 1. One sentence in "A published league table on the same players" (adds to Amendment 23, rule 5, "Main text")

After the sentence "On neither sample can the two be told apart, which is not the same as equal.", the paper prints:

> A third comparison, on the 180 older arrivals, is exploratory; there the 2015 table was the more accurate when weighted by playing time (see the arrivals of 2008–2015).

* **It is printed only with E34.** The sentence stands when, and only when, the record of E34 is committed and the paper prints the passage of E34 in the section on the arrivals of 2008-2015.
* **It is written for the case that occurred.** The sentence is printed only if, in the committed record, the interval of G_S for the 2015 table weighted by playing time lies below zero, and the same interval unweighted does not lie above zero. In any other case the renderer refuses, nothing is printed in this paragraph, and the wording goes to Amir. The record is that of the one run of E34, so the case cannot change.
* **It prints no number of E34.** "180" is the count of the arrivals. The estimate, its interval and the label of Amendment 23 ("These readings were first made outside the registration ...") stand where rule 5 of Amendment 23 puts them, in the section the sentence points to and in Appendix I. The sentence carries the word "exploratory" and the pointer.
* **It names the weighting.** The unweighted interval includes zero (-0.128 to 0.002), and the sentence does not speak for it.
* **Nothing else in the paragraph changes.** The registered sentences of E31a and E31b and the sentence "On neither sample can the two be told apart, which is not the same as equal." stay word for word. "Neither sample" still means the two samples named before it.
* **Not changed:** the abstract, the title, Figure 1, the first section, the conclusion, Limitations, and the passage of E34 itself. Amendment 23, rule 5 says that E34 does not change them, and that stands.

### 2. Appendix N (adds to the note on Amendment 23)

Wherever the sentence of rule 1 is printed, Appendix N carries, after its sentence on E34: "One sentence in the main text that points from the comparison with the 2015 table to this reading was added on 25 November 2026, after the reading had been made [Amendment 27]." The reference to this amendment says that it was written after E34 was run, with its values known, and that it registers nothing in advance.

## Gates

| Gate | Pass rule | Negative control |
|---|---|---|
| G27a the amendment | the renderer holds this file's sha256 and the file equals it | a changed byte must fail |
| G27b the sentence | the sentence of rule 1 stands exactly once, in the paragraph "A published league table on the same players", directly after "which is not the same as equal."; it stands only when the passage of E34 is printed; it is printed only in the case named in rule 1 | a paper without the record of E34 must not hold the sentence; a record whose weighted interval for the 2015 table includes zero must be refused; a text with the sentence in another paragraph must be refused |
| G27c the note | the sentence of rule 2 and the reference to this amendment stand when, and only when, the sentence of rule 1 is printed | a text with the sentence of rule 1 and no note must be refused |
| G27d nothing else moves | the registered sentences of the paragraph and the passage of E34 are word for word those of the paper before this amendment; the abstract and the conclusion are byte-identical to those of the paper before it | a text in which "On neither sample can the two be told apart" is changed must be refused |

## Threats and their controls

| Threat | Control |
|---|---|
| A sentence added after a result is read as a registered reading | this file says, in its title lines, in the reference the paper prints and in Appendix N, that it was written after E34 was run and registers nothing |
| The unfavourable result softened | the sentence gives the direction and names the weighting in which the interval excludes zero; it does not add "only" or a reason |
| The result overstated | the sentence says "exploratory", names the weighting and prints no size; the unweighted reading, whose interval includes zero, is in the passage and in Table A26 |
| An E34 statement without its label | the sentence prints no estimate or interval; it points to the section where the label stands (gate G34d of Amendment 23 is unchanged) |

## Not part of this amendment

* **No other sentence is added to the first page.** The abstract says that the paper's league numbers and the 2015 table are not distinguishable "on these league changes and the 2020–2025 arrivals"; it names its two samples and is not changed.
* **A repair made in the same pass, to words that no registration fixes.** The caption of Table A26 said "for the 2015 table with the coefficients frozen for the 2026–27 test, and for the 2026 scale fitted on the same training arrivals through 2025", which can be read as if the scale itself were fitted there. It now says that the forecast's coefficients are the frozen ones for the 2015 table and are fitted on the paper's training arrivals through 2025 for the 2026 scale. No number changes.
* **Observations of the same reader that are not taken up.** That the sentence of Amendment 10 prints a negative interval beside a positive size while the sentences of E34 print the interval reversed (both are registered words); that "one exploratory reading" in Related work stands for several printed readings (registered words of Amendment 23); and pointers and counts listed in the paper's handoff notes.

## Scope boundary: nothing pinned changes

No registered analysis, estimate, interval, threshold, forecast or frozen file is changed. No registered sentence is changed or removed. No generator is edited and nothing is run. E34 is not run again (Amendment 23, stop rule).

## Specification

This block was added in a second commit on 25 November 2026, because every research note in this repository must carry one. Everything above this heading is, byte for byte, the file pushed alone as commit `38574fb8d` (sha256 `38b09ec34a6f6748c42475e09f086f617a84def85d64f15749c0249ed177a688`). The block registers nothing new.

| Field | Registered choice |
|---|---|
| Unit | Unchanged |
| Population | Unchanged |
| Estimator | Unchanged |
| Null | Unchanged |
| Filter | Unchanged |
| Key | Unchanged |
| Uncertainty | Unchanged |
