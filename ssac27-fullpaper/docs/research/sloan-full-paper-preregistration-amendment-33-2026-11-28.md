# Amendment 33 to the SSAC27 full-paper pre-registration: the paper is printed under the title of the submitted abstract

**Approval record.**

| | |
|---|---|
| Amends | Amendment 16, rule 2 (the title, chosen from two forms by the result of the league-changes test) and the words "the title or subtitle" of its rule 1; the sentences of Amendment 19 ("The title keeps …", "The title rule of Amendment 16 stands") and of Amendment 29 ("The title stays as Amendment 16, rule 2, fixes it") that rest on that rule; Amendment 29, rule 2a, repair 3 (one sentence of the methods); Amendment 30, rule 1, number 15 (what Appendix N says of the title); and the closing sentence of Appendix N that Amendment 30, rule 3, and Amendment 32, rule 3, fix. Amendment 16 says of its rules "Nothing below may be relaxed after a result is seen", and its table of threats gives "titles, order and wording fixed here for every case" as the control against framing chosen after the result. For the title, and only for the title, this amendment departs from both, after every result: it takes the name of the league table and the words on the test out of the title and adds no claim to it. It changes no result, no interval and no count, removes no label, limit or unfavourable reading, and moves nothing between the main text and the appendix |
| Written | 2026-11-28, by Claude Science, **after every result of the paper was known to the author**, after the paper with the registered title (render 60) was merged and published, and before the paper with this title was rendered for the record, merged or published |
| Approved by | Amir, 2026-11-28. On 27 November he had kept the registered title (Amendment 32 records that answer). On 28 November he asked whether the paper could carry the title of the submitted abstract. He was shown what that would change, the comparison of titles reported below and the cost: a registered rule on the title set aside after the results, a title that the simulated readers did not favour, and about half a day of work. He answered "Keep current (Recommended)" a second time. Later that day, after he had seen that the submission form asks for the title of the paper, he decided that the paper carries the title under which the abstract was submitted, so that the conference receives the title it knows. The three passages of rule 2 and the sha256 of this file were shown to Amir before it was committed |
| Basis | committed and pushed **alone**, before the code that implements it |

**This amendment registers nothing in advance.** Every result of the paper was known when it was written. It is the dated record of a change of title made after the results, and of three passages that follow from it. It adds no analysis and no contrast.

## Why this exists, in plain words

The abstract of this paper was submitted on 29 September 2026 under the title "What Does League Translation Add? A Benchmark for European Basketball Forecasts", and the registration of 3 November 2026 carries that title. On 17 November 2026, before the league-changes test was run, Amendment 16 fixed a title for each possible result of that test. The test came out "Clear", and the paper has since carried the title registered for that case: "European League Equivalents: One Number per League, Tested on League Changes It Was Never Fitted To".

The author now returns to the submitted title. The reason is not a result. The submission form of the conference asks for the title of the paper, and the author wants the full paper to arrive under the title of the abstract that was invited. No rule of the competition that requires this was found; none that allows a different title was found either.

A title chosen after the results is exactly what Amendment 16 was written to prevent, so the change is recorded here and in the paper. Two things limit the harm that a title chosen after the results can do. The submitted title was fixed on 29 September 2026, with the results of the abstract known and before any analysis of the full paper was registered. And it claims less than the title it replaces: it asks a question, and it names neither the league table nor the test on league changes.

The change has a cost for the reader. The first page leads with the league table and its test, as Amendments 16, 19 and 29 fix it, and that order is not changed. The second sentence of the abstract states the comparison that the title asks about, and the sixth gives the answer.

## What has already been seen (exposure disclosure)

* **Every result of the paper**, including the league-changes test (slope 0.77, case "Clear") and the frozen 2026–27 test (inconclusive).
* **A comparison of titles by simulated readers** (27 November 2026; calls to a language model, sixteen for each title; not people). Amendment 32 reports it in two sentences. The values below are reported here for the first time; they come from the working files of that session, which are not part of the repository, so they cannot be checked from the public package. Nine candidates were rated; six of them, the registered title among them, were also ranked against each other by sixteen further readers who had read the abstract. The submitted title itself was not among the nine candidates. The closest candidate, "What Do Translation Factors Add? The European League Equivalents as a Benchmark for Basketball Forecasts", had an average rank of 4.69 of 6 and was no reader's first choice; the registered title had an average rank of 1.38 and was the first choice of ten of sixteen. Clarity at first read was 4.62 against 5.50 on a scale of 7; interest was 5.12 for both. This comparison speaks for the registered title. The author decided against it for the reason given above.
* **The public record.** The public companion repository carried the registered title from 25 November 2026 to the day of this amendment (its README, its release text and the rendered paper). Those commits stay in its history.
* **A trial text.** Before this file was pushed, the paper was composed once with the submitted title and the passages of rule 2, outside the record, and compared with render 60. A fresh reader (a call to a language model, not a person) read that text and this file.

## The rules

### 1. The title

The paper is printed under the title of the submitted abstract, whatever the case of the league-changes test and the status of the frozen test:

> What Does League Translation Add? A Benchmark for European Basketball Forecasts

Amendment 16, rule 2, is replaced for the printed paper. The renderer still selects the title that Amendment 16 registers for the case, and gate G16a still checks that selection and still refuses the words "tested", "validated" and "never fitted to" in the abstract when the case does not license them. The last step of a render then puts the submitted title in the place of the selected one (gate G33b). The title registered for the result stays in the paper, in the passage of Appendix N that names it (rule 2, number 2).

Amendment 16, rule 1, asks that the league table be called the European League Equivalents "in the title or subtitle, the abstract, Figure 1 and the section that presents it". The title no longer carries the name. The abstract, Figure 1 and the section keep it, and every other rule of Amendment 16 holds as later amendments left it: the condition beside the Equivalents line, the ban on the words "never saw", the order of the first page and the limit on the abstract's numbers.

The rules that keep a reading out of the title (Amendment 19, rule 5; Amendment 22, "What the paper may say"; Amendment 23, rule 2, as its table of threats states it) hold for the submitted title: it states no finding and prints no number.

### 2. Three passages that follow from the title

`[#]` stands for a citation number.

| # | Place | Before | After | Reason | Earlier registration |
|---|---|---|---|---|---|
| 1 | Data and methods, under the equation | D = 1 for a EuroLeague destination and 0 for EuroCup; δ is the source-league offset, the league number of the title. | D = 1 for a EuroLeague destination and 0 for EuroCup; δ is the source-league offset, this paper's league number. | The title no longer has the words "One Number per League" | Amendment 29, rule 2a, repair 3 |
| 2 | Appendix N, "Order and wording of the first page" | The title was fixed on 17 November 2026 for each possible result of the league-changes test, before that test was run [#]; the registration of 3 November 2026 and the public hash list carry earlier titles of this paper. | The title is that of the submitted abstract and of the registration of 3 November 2026. On 17 November 2026 a title was fixed for each possible result of the league-changes test, before that test was run; for the result obtained it was "European League Equivalents: One Number per League, Tested on League Changes It Was Never Fitted To" [#]. On 28 November 2026, after every result was known, the paper returned to the submitted title, which names neither the league table nor that test [#]. The heading of the public hash list carries a third title, older than that of 17 November 2026. | The old sentence would be false: the paper would say that it carries a title fixed before the test. The new passage says which title was registered, that it was replaced, when, and in which direction | Amendment 30, rule 1, number 15 |
| 3 | Appendix N, close of "A second round of repairs, and the first page" | Amendments 28, 29, 30 and 32 together list every change made to the text of the paper since the version of 25 November 2026. | Amendments 28, 29, 30, 32 and 33 together list every change made to the text of the paper since the version of 25 November 2026. | This amendment changes the text | Amendment 30, rule 3; Amendment 32, rule 3 |

The passage of number 2 stands where the sentence it replaces stood, directly after "It was changed on 18 November 2026: …" (Amendment 30, rule 1, number 15). It names the title that Amendment 16 registers for the case of the league-changes test; the table shows it for the result obtained (Clear). A paper composed for another result names, in the same clause, the title that Amendment 16 registers for that result. A paper composed while that test is not run says "while that test is not run it is" in place of "for the result obtained it was", and so keeps the words of the first title out of the paper, as Amendment 16, rule 3, asks.

### 3. The reference

The reference list gains one entry, cited in the passage of number 2:

> Pre-registration Amendment 33: the paper is printed under the title of the submitted abstract, and one sentence of the methods and two passages of Appendix N follow it (2026). Commit [the commit of this file], pushed 28 November 2026, [time] UTC, after every result was known; it registers nothing in advance, adds no analysis and changes no result. Full-paper companion materials (release status in Data and code), [the address of the public repository].

The citation numbers after it move up by one.

### 4. What does not change

* **Every number of the paper.** No value, interval or count is touched. The number tokens of the text equal those of render 60 apart from citation numbers, the new reference and the dates and amendment number that the passages of rule 2 print.
* **The abstract, the introduction, the conclusion, every figure, every caption and every table.** The second sentence of the abstract already states the comparison that the submitted title asks about: the paper "sets the established adjustment, a translation factor, against a plainer benchmark".
* **The name European League Equivalents** in the abstract, Figure 1, Table 1 and the text.
* **The numbers of the appendix tables** as Amendment 32 prints them.
* **The registrations.** No earlier file is edited. The heading of the public hash list keeps the title it has carried since 16 November 2026 ("One Number per League: What Translation Factors Add to European Basketball Forecasts"); a sentence appended to its last note, with the row of this amendment, names the title of the paper.
* **The statements of earlier amendments that the title does not change** (Amendments 13, 23, 27, 29, 30 and 32; in Amendment 32: "leaves the title as it is", "The title does not change", "The paper's title is unchanged"). They were true of those amendments and of the paper at their dates. This amendment changes the title one day after the last of them.

## Gates

| Gate | Pass rule | Negative control |
|---|---|---|
| G33a the amendment | the renderer holds this file's sha256 and the file equals it | a changed byte must fail |
| G33b the title | the composed text carries the title that Amendment 16 registers for the case (gate G16a, unchanged); the printed paper carries the submitted title in its place, whatever the case and the status of the tests, and differs from the composed text in that line and in the table numbers of Amendment 32 only; the Word file and the public README take the title from the printed paper | a composed text whose title line is neither registered title must be refused; so must a printed text whose title line is not the submitted title, or that differs from the composed text in any other line by more than a table number |
| G33c the passages | each "after" of rule 2 stands once in the paper and no sentence of a "before" stands; the passage of number 2 stands in Appendix N directly after "It was changed on 18 November 2026: …", with the references to Amendment 16 and to this amendment; the main text does not say "of the title" | a paper that still says "The title was fixed on 17 November 2026 …" must be refused, and so must one with the closing list of Amendment 32 |

The gates of the earlier amendments hold with the new forms. Gate G19c counts the kept sentence of render 39 on the league number as kept in the form that this amendment lists; so do gate G29d for the form of Amendment 29 and gate G30c for the sentence of Amendment 30, number 15. Gate G32b reads the closing list with this amendment in it. Gate G32d (only table numbers differ between the composed and the printed text) is read on the text below the title line. The checks that the title carries neither the reading of Amendment 19, rule 5, nor the destination term of Amendment 23, rule 2, are run on the submitted title as well (part of gate G33b).

## Threats and their controls

| Threat | Control |
|---|---|
| A title chosen after the results claims more than the registered one | the title is the one submitted on 29 September 2026, before the full paper's analyses were registered; it asks a question and names neither the league table nor the test; Appendix N prints the registered title and says that it was replaced after every result was known |
| The paper still speaks as if it carried the registered title | the two sentences that did so are replaced (rule 2, numbers 1 and 2); a fresh reader (a call to a language model, not a person) read the text of a trial paper for other such places before this file was pushed and found none; the rows of the appendix tables were searched by code and no figure image was read; gate G33c refuses "of the title" in the main text and the old sentence of Appendix N |
| The change of title is read as a registered decision | this file says, in its first lines and in the reference the paper prints, that it was written after every result was known and registers nothing; Appendix N says that the title was changed after every result was known |
| The change of title is taken for one that readers preferred | this file reports that the simulated readers ranked the registered title first and a title close to the submitted one fifth of six, by average rank |
| Two titles circulate for one paper | the public README, the release text and the Word file take the title from the printed paper; the public history keeps the earlier commits, and Appendix N names both titles |

## Scope boundary: nothing pinned changes

No registered analysis, estimand, file, forecast, licence or gate of a result is changed. No generator is run. The score record of the frozen 2026-27 test is not touched. No figure is redrawn. Nothing moves between the main text and the appendix.

## Specification

This amendment changes the title under which the paper is printed and three passages of its text. It defines no new analysis.

| Field | Registered choice |
|---|---|
| Unit | Unchanged |
| Population | Unchanged |
| Estimator | Unchanged |
| Null | Unchanged |
| Filter | Unchanged |
| Key | Unchanged |
| Uncertainty | Unchanged |
