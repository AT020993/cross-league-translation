# Amendment 23 to the SSAC27 full-paper pre-registration: the unit in words, three terms of the equation side by side, where the forecasts run low, a narrower statement on prior work, two published league scales on the older arrivals (E34), and one appendix table of the frozen test

**Approval record.**

| | |
|---|---|
| Amends | `docs/research/sloan-full-paper-preregistration-2026-11-03.md`, as amended through Amendment 22. It adds to rule 2 of Amendment 19 and to the counting rule of Amendment 17 (rule 1 below); to Part A of Amendment 12 (rule 2); to Part B of Amendment 12 (rule 3). It replaces one clause of rule 6 of Amendment 16 (rule 4). It adds one exploratory analysis, E34, beside E28 of Amendment 9 and E31a of Amendment 15, and one line to Amendment 15's control for tables built on the scored seasons (rule 5). It names one appendix table of the frozen test (rule 6). Everything else in those amendments holds |
| Written | 2026-11-22, after the league-changes test (E30) and its sensitivities were scored, **after the comparisons of E34 had been computed outside the registration (21 November) and reproduced (22 November)**, and before the frozen 2026-27 test was scored. The author of this amendment had read no 2026-27 statistic. Claude Science read the draft the same day, and its changes are in this text; what it computed and read is listed in the exposure disclosure |
| Approved by | Amir, "Yes", 2026-11-22, in answer to a question that named this amendment's file, its final text, its commit alone on the branch `sloan-fullpaper-amendment-23-2026-11-22` and its draft pull request into `main`. The question said that the Yes approves the final text and merges nothing. Earlier the same day he wrote "pass A to S to the paper lane; ledger with the paper lane; Appendix N yes. Implement all your recommendations" and "you open the PR". The merge and the row in the public hash list wait for his separate word |
| Basis | committed and pushed **alone**, before the text it governs is written into the paper and before the generator of E34 is written. Nothing below may be relaxed after the frozen 2026-27 test is scored (METHOD.md §8) |

Rules 1 to 4 and 6 change wording and placement and add no analysis. Rule 2 allows one new number, which is arithmetic on two registered coefficients, and says so where it is printed. Rule 5 adds one analysis on outcomes that have already been read and whose values have already been seen. **E34 is exploratory and is labelled so wherever it is printed.** No rule lets the paper claim more than it claims today. Rules 4 and 5 make it claim less.

## Why this exists, in plain words

Between 20 and 22 November 2026 Codex reviewed the paper at Amir's request, and that review was then read critically. Most of what it proposed is not used. Six things from it are worth having, and none needs a new headline analysis.

1. **A reader who does not know the unit cannot read the abstract.** The abstract says "a 16 EFF/36" and defines nothing. Methods lists what the unit is made of and never says how large one unit is.
2. **The fitted equation holds three adjustments in one unit, and the paper sets only two of them side by side.** Beside the equation it gives the step for a season above the career rate (1.389) and the span of the ten league numbers (2.10). The destination term is of the same size and is not stated as a size.
3. **The paper says the forecasts run low and gives no cause.** The appendix already shows that the shortfall is clear for EuroCup arrivals and not for EuroLeague arrivals. The main text does not say so.
4. **The sentence on prior work is wider than what is public.** The paper says a bounded search "found no public test of such league adjustments on what European arrivals went on to do". The review named two analysts who report how player forecasts conditioned on a league level fared. One scored a forecast for players of 30 European leagues on two later seasons. The other publishes projections for EuroLeague players and says that it scores its calls on players who arrived in earlier seasons. In the text read so far neither compares its forecast with one that leaves the league level out, which is the comparison the paper makes. A reader who knows those pages would call the paper's sentence wrong.
5. **The review scored two published league scales on the 180 older arrivals, outside the registration.** Weighted by playing time both were more accurate there than the paper's league numbers. The paper says of one of them that it "is not scored here". The result exists and is unfavourable, so the paper reports it.
6. **The review proposed one table for Appendix L** that sets the frozen test's errors and gains side by side. It uses registered contrasts only. Naming it here fixes it before the test is scored.

## What has already been seen (exposure disclosure)

* **E30, E31 and E33 are known.** E30 was scored once (retained run `league-changes-score-01`, 18 November 2026): case "Clear"; slope 0.77 (95% interval 0.69 to 0.84).
* **Everything about the 674 arrivals and the 180 older arrivals that the paper prints is known**, including E28b: on the older arrivals the league-aware forecast against the destination-only forecast is −0.067 EFF/36 (interval −0.144 to 0.010) and −0.129 weighted by playing time (interval −0.209 to −0.048).
* **The values of E34 have been seen.** Codex ran the comparison on 21 November 2026 under a protocol of its own (commit `10956edebf6720fa71024f8b64e65fb1c2c1086a`, 03:09 +02:00). It committed the fitted coefficients (commit `ab9c3b3fe48244b7e2b48e3ed68f56593fe5fcd7`, 03:33) before the results on the older arrivals (commit `0379d9c5f9d8df85b35e655932fd1b9b186f4f9d`, 03:38). None of these commits is on `main`, and the protocol carries no approval of Amir's. The values are listed under "The values of E34 as seen" below.
* **The author of this amendment reproduced those values on 22 November** from the committed printed extract of the older arrivals and the coefficients Codex saved. The league-aware forecast rebuilt from the coefficients equals the committed forecast column to 1.4e-14. The four estimates and the two unweighted intervals agree with the table below, with the repository's interval function. Claude Science reproduced the weighted intervals and the detectable differences the same day (next point).
* **Claude Science read the draft of this amendment on 22 November 2026** and computed the following from committed files. It rebuilt the three forecasts as the author did and reproduced every value of the table below and of the split by source league (estimates, intervals and detectable differences, both weightings) with the registered interval function of E28, to 1e-15; Codex's run had called the repository's own interval functions. It reproduced the two registered E28b contrasts, counted the clusters (166 players, 95 destination club-seasons, 94 degrees of freedom) and the effective number of arrivals under the minutes weights (144.5 of 180). It compared Codex's fit of the 2015 table with the frozen E31c coefficients (largest difference 2.7e-14). It computed one quantity from forecasts alone, reading no outcome: how far each league term moves a forecast away from the destination-only forecast. For Adriatic arrivals the forecast is lower by 0.68 EFF/36 with the paper's league number, by 0.10 with the 2015 table and by 0.14 with the 2026 scale; for arrivals from Israel by 0.37, 0.56 and 0.18. No rule below uses that quantity and nothing from it is printed. It computed no interval of T_S and did not run E34. The same day it read, from the pages themselves, the German Basketball Analytics post of 8 July 2025 in full (text and charts) and the text of that analyst's posts of 11 May 2026 and 30 July 2026; all three were published before the 2026-27 season. It opened no Gaussian Hoops page. On 22 November it read no 2026-27 statistic. In its literature search of 15 November 2026 a search result had shown it a snippet with three statistic lines of current EuroLeague players; it recorded this that day and used none of them.
* **The point estimates of the second contrast of E34 follow by arithmetic** from errors already seen. With T = error of the destination-only forecast minus error of the published-scale forecast: about −0.004 (2015 table) and −0.005 (2026 scale); weighted, about −0.047 and −0.025. Below zero means that the published scale did worse than the destination alone. **Their intervals have not been computed.**
* **A fourth forecast of Codex's run is not part of E34.** It adds penalised league offsets to the 2026 scale. On the 180 arrivals its error differs from that of the paper's own forecast by less than 0.001 EFF/36, so it carries no further information.
* **Arithmetic on the yearly refits, computed on 22 November and not used.** From the committed file of Equivalents by refit, the author computed the spread of the ten league values in each refit, with and without the pull of the penalty. No rule below uses it and nothing from it is printed.
* **The analysts' pages of rule 4 were read on 22 November as captured text**, through a fetch tool and not in a browser: two German Basketball Analytics posts, and the Gaussian Hoops projections overview, its board for the 2026-27 EuroLeague and its methodology page. The text that reached the author held no table, chart or record card, and no statistic of a 2026-27 game.
* **A public page with statistics of the 2026-27 season exists.** The Gaussian Hoops board for the 2026-27 EuroLeague sets its projections beside what players have done so far this season. None of those values was in the text that reached the author. Codex's review links that board and the overview as read on 21 November 2026; what it saw there is not recorded.
* **Codex's other studies of 20 to 22 November** (about twenty, on the examined seasons) were read as reported. None is used by this amendment.
* **No result of the frozen 2026-27 test exists**, and the author of this amendment has read no 2026-27 statistic. Codex's run used the registration list of 12 September 2026 (names and clubs, no statistic), which the registered lock of that date already holds.

## The values of E34 as seen

G is the error of the published-scale forecast minus the error of the league-aware forecast, in EFF/36, on the 180 older arrivals. Below zero, the published scale was more accurate than the paper's league numbers.

| Published scale | Weighting | G | 95% interval | Detectable with 80% power |
|---|---|---|---|---|
| 2015 table | none | −0.063 | −0.128 to 0.002 | 0.093 |
| 2015 table | playing time | −0.082 | −0.152 to −0.011 | 0.101 |
| 2026 scale | none | −0.062 | −0.122 to −0.002 | 0.086 |
| 2026 scale | playing time | −0.104 | −0.167 to −0.040 | 0.091 |

By source league, also seen. For the 131 arrivals from the Adriatic league G is −0.093 (−0.178 to −0.007) for the 2015 table and −0.086 (−0.166 to −0.006) for the 2026 scale; weighted, −0.140 and −0.132, both intervals below zero. For the 49 arrivals from Israel G is +0.016 (−0.039 to 0.070) and +0.003 (−0.052 to 0.057); weighted, +0.060 (0.002 to 0.119) for the 2015 table and −0.035 (−0.094 to 0.025) for the 2026 scale.

## Pinned inputs (E34)

Each sha256 was computed on 22 November 2026 from the committed file. The first two files are on main; the last two are on the branch sloan-fullpaper-ele-integration (commit 815333b9) and not yet on main.

| File | sha256 |
|---|---|
| `docs/research/artifacts/sloan-fullpaper-older-seasons-2026-11/e27_arrivals.csv` (scored older arrivals with every registered forecast) | `7356ba0bd35945ea8fb8a152d2d167c5dc1eb4d0f7849a08f627cf172ae3a800` |
| `docs/research/artifacts/sloan-fullpaper-older-seasons-paper-2026-11/e27_arrivals_printed.csv` (the 180 printed rows) | `2b4bba1be27d5c66f4e632c39cc01d05dfeb6af8aedcf38473751948648f0936` |
| `docs/research/artifacts/sloan-fullpaper-p1-freeze-2026-11/e31c_freeze.json` (the frozen coefficients of the 2015-table forecast) | `a19589ecdf1ba1818d135b8eb87133992003ad7e31dd0cba1668937966750a82` |
| `docs/research/artifacts/sloan-fullpaper-published-tables-2026-11/vashro_2015_competition_scores.csv` | `2c004c88d10c60f68dabb038330a9f8d282ba87f56b521cb6a87c59a26252d04` |

**The 2026 scale.** Gaussian Hoops, "League strength", https://www.gaussianhoops.com/projections/league-strength/, read on 21 November 2026; the day it was first published is not known. By its own description it is built on 12,117 player moves of 2021-22 to 2025-26 and measures points, rebounds and assists per 36 minutes, adjusted for pace. The ten values used, under the page's own names: Spain ACB 110.6; France Pro A 105.9; Italy Serie A 104.9; ABA Liga (the Adriatic league) 103.3; Israel Winner 103.0; Greece GBL 102.3; Turkey BSL 102.2; Germany BBL 100.1; VTB United League 99.3; Lithuania LKL 97.9. These are the values Codex's protocol records from the page on 21 November, and captured text of the page on 22 November shows the same ten. They are committed with the page's title, address and the date read; the page text is not copied into the repository. Before the run the page is read again, and the record says whether it still shows these values. E34 uses the values listed here either way.

**This table is admitted after the fact.** Amendment 15 admits a further published table only by a dated addendum pushed before the table's arm is frozen. No addendum was pushed before Codex's run. This section is that addendum, made after the arm was fitted and scored on the older arrivals, and the paper says so wherever E34 is printed.

## Specification

| Field | Registered choice |
|---|---|
| Unit | E34: one arrival (player × destination season). Rules 1 to 4 and 6: unchanged |
| Population | E34: the 180 older arrivals of E27 and E28b in the version the paper prints (131 from the Adriatic league, 49 from Israel; destination seasons 2008-09 to 2015-16) |
| Estimator | E34, for each of the two published scales S: G_S = MAE(published-scale forecast) − MAE(`source_ridge_10`), and T_S = MAE(`history_destination_slope`) − MAE(published-scale forecast); EFF/36; each unweighted and weighted by destination minutes. The published-scale forecast is the one rule of Amendment 15: the destination-aware forecast plus one unpenalised coefficient times the scale's value for the source league, fitted on the registered training arrivals through 2025 |
| Null | Zero for each paired difference |
| Filter | None beyond the registered rules of the older-seasons test |
| Key | The registered key of the older-seasons test (player × destination season), one row per key |
| Uncertainty | As in E28 (Amendment 9): two-way clustered 95% intervals (player, destination club-season), Student t with the smaller number of clusters minus one as degrees of freedom; beside every "not distinguishable", the difference that would have been detected with 80% power |

## The rules

### 1. The unit in words (adds to Amendment 19, rule 2; implements the counting rule of Amendment 17)

* **Abstract.** Between the sentence on the problem and the Equivalents line, the abstract may carry one sentence: "Production is measured by box-score efficiency per 36 minutes (EFF/36)." Nothing else in the abstract changes.
* **Counting.** Amendment 17 says that the unit does not count as a number. The 36 of "per 36 minutes" is the unit's own number. The renderer's counter removes exactly the words "per 36 minutes", as it already removes "EFF/36", and nothing else. The limit stays nine in every state of the frozen test.
* **Methods.** After the sentence that defines the outcome, the paper may add: "One EFF/36 is one more point, rebound, assist, steal or block, or one fewer missed shot or turnover, per 36 minutes; a made two-point basket adds two." This restates the registered definition of the outcome and is no estimate.

### 2. Three terms of the equation, side by side (adds to Amendment 12, Part A)

Beside the fitted equation, the club section may set three of its terms side by side, each in forecast EFF/36, in one passage or in a table of three rows:

| Term | Today's value | Status |
|---|---|---|
| The ten league numbers, highest minus lowest | 2.10 | printed today |
| The destination term at the reference rate of Table 1: the forecast of a 16 EFF/36 line for a EuroLeague arrival minus that for a EuroCup arrival | −1.83 | **new**: the sum of two registered coefficients, one of them times 16 |
| The step for a last season above the career rate | −1.389 | printed today |

Beside them stand two numbers the paper already prints: the average miss of one forecast (2.924) and the typical 80% band (±4.8).

* **Label.** Where the destination term is printed, the same sentence or the next says that it is arithmetic on the fitted coefficients, that it is stated at a domestic rate of 16, that it grows with the domestic rate, and that it is a point value with no interval.
* **What the paper may say.** That these are three terms of one fitted forecast; that at the reference rate each is smaller than the average miss of a single forecast; that the destination term is the same for two candidates of one club who have the same domestic rate, so that it bears on the level of a forecast and not on the comparison of two such candidates.
* **Not allowed.** A flat rule ("take 1.4 off"); a recommendation to sign anyone; a cause for any term; a reading of any term as league strength or as a player's quality; any statement that one term matters more than another. The step stays a term of the model. The registered result on above-average seasons (E12), the wording rule of 11 November ("a pattern to test, not a finding" for how it changes with the size of the jump) and the limits beside the equation (Amendment 12) stand. The rule for the step that Amendment 13 left unstarted is not started here.
* **The three sentences on the step** that render 44 added beside the equation as plain edits stay in the passage: its size beside the span; the Equivalents hold where the step is zero; a gap between two leagues is unchanged when both candidates carry the step, and not when only one does.

### 3. Where the forecasts run low (adds to Amendment 12, Part B)

In the Results paragraph on the forecast level, after the registered sentences and before "We claim no cause", the paper may add the two values by competition of the committed table of signed errors (E18a, Amendment 3; Table A10), each with its interval, in these words. A value whose interval lies below zero: "for [EuroCup] arrivals the league-aware forecast is X EFF/36 below what they delivered (interval; n arrivals)". A value whose interval includes zero: "for [EuroLeague] arrivals the interval includes zero (X, interval; n arrivals)". The same sentence or the next says: "The difference between the two was not tested." When the two intervals overlap, as they do today, it says instead: "The two intervals overlap, and the difference between them was not tested."

Both values, both intervals and both counts are committed and stand in Appendix H today (−0.65, −1.04 to −0.30, 480 arrivals; −0.03, −0.51 to 0.44, 194 arrivals). No number is new. The values are descriptive (Amendment 3), and the paper does not call either of them a test. The paper still gives no cause (Amendment 12). The registered sentences on the forecast level stay word for word, and Limitations is unchanged.

### 4. A narrower statement on prior work (replaces the last clause of Amendment 16, rule 6, second point)

The paper may say that analysts and vendors publish or advertise league adjustments, with the sources, as before. In place of "no public test of them on European arrivals was found in a bounded search" it says two things:

* **What was found.** For each analyst's page that reports how a player forecast conditioned on a league level fared, with its source: what the page forecasts, on which players and seasons the forecast was scored, whether those players are arrivals, and whether the page reports the forecast's accuracy with and without the league level.
* **What was not found.** "A bounded search in English found no public test in basketball that compares a forecast with and without a league adjustment on what players arriving in European competitions went on to do."

Related work carries both in short form and Appendix O in full. The paragraph "How the search was done" adds the dates on which the further pages were read and that a review named them.

**The pages named so far, as read on 22 November in captured text.**

| Page | What the captured text says | What it does not show |
|---|---|---|
| German Basketball Analytics, "Predicting Player Performance in European Basketball using Machine Learning", 8 July 2025, https://germanbasketballanalytics.substack.com/p/predicting-player-performance-in | It forecasts next-season estimated plus-minus for players of 30 European leagues. The level of the current league and of the next league are inputs. It uses players with two consecutive seasons, was fitted on seasons through 2022 and scored on 2023 and 2024, for all those players together (an error of about ±1 and R² 0.70). It gives four named players who changed league or level as examples. It lists the two league levels third and fourth among its eight most influential inputs | accuracy without the league levels; any baseline; results for players who changed league, as a group |
| Gaussian Hoops, projections overview, https://www.gaussianhoops.com/projections/, updated 22 November 2026, and its board for the 2026-27 EuroLeague, https://www.gaussianhoops.com/projections/euroleague/ | It projects eight metrics for each player from earlier players who made "the same kind of move", at the "same level of league". The overview says that across its 2025-26 EuroLeague board 75% of its up-or-down calls turned out right. The board says that its calls are scored on "players who arrived in earlier seasons" | which players the 75% covers and how many; any baseline; a projection without the league level. The board's tables and record cards were not in the captured text |

Two further pages were read and are not counted. German Basketball Analytics' post of 11 May 2026 on college players who move to Europe forecasts with the level of the league as an input and reports no accuracy figure. Its post of 30 July 2026 on a forward-looking metric corrects a player's statistics for league strength when he transfers and reports no accuracy figure. The post of 8 July 2025 was read in full, text and charts, by Claude Science on 22 November 2026, and its row above stands.

**With that reading, Related work would say:** "Two analysts report how forecasts that use a league level fared, one for players of 30 European leagues [n] and one for EuroLeague players [n]; neither reports its forecast without the league level (Appendix O). A bounded search in English found no public test in basketball that compares a forecast with and without a league adjustment on what players arriving in European competitions went on to do." The sentences are written from the ledger and change if the full read shows otherwise.

**Condition.** The new sentences are printed only after each page has been read in full and entered in the literature ledger (`docs/plans/sloan-ssac27-literature-evidence.md`) with the date read. The sentence under "What was not found" is printed only if the ledger records no source that reports, for basketball players arriving in or playing in European competitions, the accuracy of a player forecast with and without its league level, or beside a forecast that does not know which league a player came from. The sentence names basketball and the destination because Appendix O already cites a football study that compares regression models with league identifiers against naive and pair-average baselines on transfers between European leagues; that sentence of Appendix O stays as it is. If a page does report that, the sentence is not printed, the page is described as what it is, and Amir is told before any writing. Until the ledger entries exist the paper keeps the sentence it has.

**Order of reading.** The Gaussian Hoops board for the 2026-27 EuroLeague shows statistics of the current season, and the overview leads to it. Both are read in full only after the frozen 2026-27 test has been scored, and then at once, so that the final render can carry the new sentences. Until then they are read only as captured text without tables, as on 22 November. The German Basketball Analytics post dates from July 2025 and may be read in full at any time.

The paper still says "the first" of nothing (Amendment 16, rule 6), and its statement of what it offers is unchanged.

### 5. Two published league scales on the older arrivals (E34; adds to Amendment 15)

**The analysis.** E28b compared the league-aware forecast with the destination-only forecast on the 180 older arrivals. E34 repeats that comparison with a published league scale in the place of the paper's league numbers, once for the 2015 table and once for the 2026 scale, by the one rule of Amendment 15 for a published-table forecast. For the 2015 table the coefficients are the frozen ones of E31c and nothing is fitted. For the 2026 scale the forecast is fitted on the same registered training arrivals through 2025, by the same code. E34 then reports G_S and T_S of the Specification, unweighted and weighted by playing time, with intervals and detectable differences, and the same by source league. E34 reads no 2026-27 statistic. It may be run before or after the frozen test is scored, because its rules are fixed here.

**What Amendment 15 said, and what changes.** Amendment 15's control for a table built on the scored seasons reads: "such a table is scored on the frozen test only, and the paper says so". The 2026 scale is built on moves of 2021-22 to 2025-26. It is still not scored on the 674 arrivals or on the league changes. The older arrivals are of 2008-09 to 2015-16, seasons that scale was not built on, and this rule allows its exploratory reading there. It is not read out on the frozen 2026-27 test (see "Recorded, not used").

**What the paper may say.**

| Contrast | Interval | Wording |
|---|---|---|
| G_S, the league-aware forecast against the published-scale forecast | above zero | "the paper's league numbers were more accurate than [S] by X EFF/36 (interval)" |
| | includes zero | "the paper's league numbers and [S] are not distinguishable (X, interval; a difference of D would have been detected with 80% power)" |
| | below zero | "[S] was more accurate than the paper's league numbers by X EFF/36 (interval)" |
| T_S, the published-scale forecast against the destination-only forecast | above zero | "[S] improved the destination-only forecast by X EFF/36 (interval)" |
| | includes zero | "[S] added nothing detectable to the destination-only forecast (X, interval; a gain of D would have been detected with 80% power)" |
| | below zero | "with [S] the forecast was less accurate than with the destination alone by X EFF/36 (interval)" |

[S] is "a league table printed in 2015" or "a league scale published in 2026", each with its reference.

* **Signs.** In the rows "above zero", X is the difference as the Specification defines it. In the rows "below zero", X is the size of the difference and the interval is reversed with it. In the rows "includes zero", X and the interval keep the sign of the Specification, and the sentence or the table header says what a value below zero means: for G_S, that the published scale was the more accurate; for T_S, that the destination-only forecast was.
* **Label, in the same sentence or the next, wherever E34 is printed:** "These readings were first made outside the registration, in a review of the paper, and the rules for printing them were written after their values had been seen; they are exploratory [Amendment 23]."
* **Main text.** A short passage in the section on the arrivals of 2008-2015, after the paragraph on the league numbers, which stays word for word. For each scale they print the unweighted reading of T_S, and the reading of G_S whose estimate is the less favourable to the paper's league numbers of the two weightings, named as unweighted or weighted, each in the words above, and they point to the appendix table. If the weighted reading of T_S falls in another case than the unweighted one, it is printed too. Each clause names its weighting. The passage says once that the reading shown for G_S is the less favourable of the two weightings and that both are in Appendix I.
* **Appendix I.** One table with every reading: both scales, both contrasts, both weightings, the error of each forecast, and the split by source league. The split is described and not tested. The table takes the next free number, so no existing table is renumbered.
* **Four facts printed beside the table.** The 2015 table was printed in November 2015, during the last of these seasons, and may have been built on them; the paper cannot tell how far. The 2026 scale is built on moves of 2021-22 to 2025-26, as the paper's league numbers are fitted on arrivals of 2017 to 2025. The intervals treat the fitted forecasts as fixed and describe arrivals from these two leagues; each league term is one constant per league, so they say nothing about other leagues. Both published scales place the Adriatic league fourth of the ten source leagues, and the paper's league numbers place it seventh; the generator computes both ranks from the pinned scale values and the committed league numbers, and the paper reads neither as league strength.
* **Related work and Appendix O.** The sentence that the 2026 scale "is not scored here" is replaced: the scale is not scored on the arrivals of 2020-2025 or on the league changes, because it is built on those seasons; it is not a registered arm and is not read out on the frozen test; one exploratory reading on the older arrivals is in Results and Appendix I.
* **Appendix N.** Wherever the paper prints E34, Appendix N carries one sentence: "E34 is the only study this paper reports from the further studies that a review of the paper ran, outside the registration, on seasons already examined; the others are not used."
* **Words the paper does not use for E34:** "confirms", "validates", "robust", "equivalent", and any statement that a scale measures league strength.
* **Not changed by E34:** the abstract, the title, Figure 1, the conclusion, Limitations, and every registered sentence on the older arrivals. The clause "on 180 older arrivals from two leagues it did not help" already carries the result that matters, and E34 does not soften it.
* **Every number is printed whatever it shows.** With the values seen, and if both intervals of T_S include zero, the main text would read: "Two published league scales were also scored on these arrivals; for each, the comparison with the paper's league numbers is shown in the weighting less favourable to the paper, and Appendix I gives both. Unweighted, a league table printed in 2015 [8] added nothing detectable to the destination-only forecast (X, interval; a gain of D would have been detected with 80% power); weighted by playing time it was more accurate than the paper's league numbers by 0.082 EFF/36 (interval 0.011 to 0.152). Unweighted, a league scale published in 2026 [44] added nothing detectable to the destination-only forecast (X, interval; a gain of D would have been detected with 80% power); weighted by playing time it was more accurate than the paper's league numbers by 0.104 EFF/36 (interval 0.040 to 0.167). These readings were first made outside the registration, in a review of the paper, and the rules for printing them were written after their values had been seen; they are exploratory [Amendment 23]." The two clauses on the destination-only forecast depend on intervals that have not been computed and follow the case rule.

**Changes from Codex's run.**

1. The 2015-table forecast uses the frozen coefficients of E31c. Codex refitted them; its coefficient on the table equals the frozen one to 2e-15, and all seven coefficients to 3e-14.
2. The contrast T_S against the destination-only forecast is added, as in E31a. Codex compared the published scales with the paper's forecast only.
3. The intervals are those of E28, from the registered function, which Codex's run also called.
4. The sentences are fixed here, by case.
5. Codex's fourth forecast is left out (see the exposure disclosure).

### 6. The scorecard of the frozen test in Appendix L (adds to Amendment 19, rule 12)

In the scored states Appendix L may print one table, "Frozen forecast scorecard". Its rows are the destination-only forecast, the 2015-table forecast (when its read-out was registered in time) and the league-aware forecast. Its columns are the mean absolute error on the scored newcomers, the paired gain over the destination-only forecast and the paired gain over the 2015-table forecast, each gain with the interval of its registered read-out.

Every gain is a registered contrast: S2 of Amendment 8 and the two read-outs of E31c (Amendment 15). Every error is the arm error behind one of them. The table computes no statistic and selects no row. Its caption says that the errors and gains are unweighted and gives the number of newcomers. It stays in Appendix L in every state, with one clause of pointer in the main text; rule 12 of Amendment 19 is otherwise unchanged. The table was proposed on 20 November 2026 and is fixed here before the frozen test is scored. Its code is already written on the unmerged draft branch of pull request #3696; nothing has been rendered from it.

## Gates

| Gate | Pass rule | Negative control |
|---|---|---|
| G23a the abstract's count | the counter removes "per 36 minutes" and nothing else new; the abstract stays within its limit | a made-up abstract with "in 36 games" must count that 36; a made-up abstract one number over its limit must be refused |
| G23b the destination term | the renderer computes the term from the committed coefficients and prints it only if, for each of the ten leagues, it equals the committed reference forecast for a EuroLeague arrival minus that for a EuroCup arrival (absolute difference below 1e-9), and the label of rule 2 stands in the same sentence or the next | with one coefficient shifted by 0.01 the renderer must refuse; a text with the term and no label must be refused |
| G23c the forecast level by competition | both values and intervals are read from the committed table; the words follow the case of each interval; "was not tested" stands in the same sentence or the next | a text that says "includes zero" for a value whose interval lies below zero must be refused; a text that calls either value "detectable" or "not detectable" must be refused |
| G23d prior work | the new sentences are printed only if the record of rule 4 gives, for every named page, the date of its full read and what it reports; the sentence under "What was not found" is printed only if that record holds no comparison with and without a league level for basketball players in European competitions; once the new sentences are printed, the old one ("found no public test of such league adjustments") is in no part of the paper | a record with one date missing must leave the old sentence in place; a record with one such comparison must stop the sentence under "What was not found"; a text with both the old and the new sentence must be refused |
| G23e the scorecard | the table is printed only if the count of newcomers, the two arms and the two errors of each contrast agree with the score record | a score record whose S2 names another arm must be refused |
| G34a inputs | every pinned file equals its sha256; the ten values of the 2026 scale are read from a committed file and equal the ten listed in this amendment | a changed byte must fail; one of the ten values moved by 0.1 must fail |
| G34b the same rows | the selected rows are the 180 of E28b (131 and 49; seasons 2008-09 to 2015-16); before any published scale is used, the generator reproduces the two committed E28b contrasts against the destination-only forecast, with their intervals, to 1e-9 | with one row removed the reproduction must fail |
| G34c the published-scale forecast | the 2015-table forecasts are built from the frozen E31c coefficients; the code that fits the 2026 scale, run on the 2015 table, returns those coefficients to 1e-9 | with one published value moved by 0.01 the check must fail |
| G34d the label | the label of rule 5 stands with every printing of an E34 number; the main text prints for each scale the less favourable weighting of G_S and names the weighting of every reading; the sentence of Appendix N stands whenever E34 is printed | a text with an E34 number and no label must be refused; a text that prints the more favourable weighting alone must be refused; a text with an E34 reading whose weighting is not named must be refused |
| G34e the identity | for each scale and each weighting, G_S + T_S equals the committed E28b contrast to 1e-9 | with the sign of one contrast reversed the check must fail |
| G34f the values seen | every G_S estimate and interval end of "The values of E34 as seen", with the split by source league, is reproduced to the three printed decimals | with the forecasts of one scale shifted by 0.1 the check must fail |

G34a, G34b and G34c are run before the contrasts of E34 are computed. G34e and G34f are run on the computed contrasts before anything is written for the paper. If any gate fails, E34 stops, nothing of it is printed, and Amir is told.

## Threats and their controls

| Threat | Control |
|---|---|
| A table admitted after its scores are known (Amendment 15) | it happened, and it is disclosed: the admission is made here after the fact and the label says "outside the registration"; the result is unfavourable to the paper and is printed in the main text; the 2026 scale is not admitted to any other sample |
| An unfavourable reading softened or kept out of sight | sentences by case; the main text prints the less favourable weighting (G34d); the appendix table prints every reading |
| The 2015 table read as a fair forecast of seasons it may have been built on | the two facts on the scales' dates stand beside the table |
| A new number added after the result (rule 2) | it is the sum of two registered coefficients at the reference rate, checked against committed forecasts (G23b), labelled where printed, and kept out of the abstract, the title and the conclusion |
| The step read as a discount rule | rule 2's "Not allowed" list; the wording rule of 11 November stands |
| The location of the shortfall read as its cause | "the difference between them was not tested"; no cause is given (G23c) |
| A claim about prior work made from captured page text | the condition of rule 4: each page is read in full and entered in the ledger before printing, and the sentence under "What was not found" depends on what the ledger records (G23d) |
| Statistics of the 2026-27 season seen on a publisher's page before the frozen test is scored | the order of reading in rule 4: the Gaussian Hoops boards are read in full only after the scoring |
| A gate changed so that a text passes | the counter changes for one named phrase only, under the registered counting rule, with a negative control (G23a) |
| A display of the frozen test chosen after its result | rule 6 is fixed before the frozen test is scored, uses registered contrasts only and selects no row |

## Recorded, not used

On 21 November 2026 Codex's run wrote forecasts of the 2026 scale for the 3,478 rows of the frozen file. Its execution record says that it read no prospective outcome. Two hashes are recorded so that a later amendment could register a read-out of that arm on the frozen test. None is registered here, and none is run at the scoring of November 2026.

| File at commit `ab9c3b3fe48244b7e2b48e3ed68f56593fe5fcd7` | sha256 |
|---|---|
| `docs/research/artifacts/sloan-contemporary-table-2026-11/models.json` | `7184b2335389cbe21602b24ba499963b2e92067e01e9ecacaf6153d07f0a80cd` |
| `docs/research/artifacts/sloan-contemporary-table-2026-11/envelope.csv` | `9bb1ce3ce86950891808691a6e8ef178cbdc6b0efa4f1fc523a925df1e2ca99e` |

## Not part of this amendment

* **Nothing moves and nothing is cut.** No sentence that a registration fixes is moved or removed. The order of the first page and its paragraph of cautions stand (Amendment 19, rule 3), the list of what may not move stands (Amendment 19, rule 11), and Amir's decision of 20 November 2026 ("Length: leave", no block moves to the appendix) stands. The rules above add about 340 words to the main text.
* **No sentence on why the gaps between leagues widened across the yearly refits.** The arithmetic named in the exposure disclosure is not printed.
* **None of Codex's other studies** is used, and none of the further read-outs it proposed for the frozen test is run at the November scoring.
* **Wording corrections queued on 22 November** (the caption of Figure A7, the condition on wrong name links, one sentence on what the slope measures, an axis label of Figure 1) are free text that no registration fixes. They claim less or explain a term and need no rule.

## Stop rule (E34)

E34 is run once, in one retained run, from a committed generator that reads only the pinned inputs and the registered training arrivals. A failed run is kept and reported. No further published scale, sample or variant of this comparison is run for this paper.

## Scope boundary: nothing pinned changes

No registered analysis, estimate, interval, threshold, forecast or frozen file is changed. Two sentences that earlier amendments licensed are replaced by narrower ones (rules 4 and 5); no other registered sentence changes. No generator of an earlier analysis is edited. The frozen 2026-27 forecasts are not read by any rule above. Amendment 19, rule 12 stands for the frozen test, with the one table of rule 6 named in Appendix L.
