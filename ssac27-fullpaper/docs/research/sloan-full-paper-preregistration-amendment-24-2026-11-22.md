# Amendment 24 to the SSAC27 full-paper pre-registration: when the pages that show current-season statistics are read if the frozen test ends inconclusive

**Approval record.**

| | |
|---|---|
| Amends | `docs/research/sloan-full-paper-preregistration-2026-11-03.md`, as amended through Amendment 23. It makes explicit one phrase of rule 4 of Amendment 23 ("Order of reading"). Everything else in Amendment 23 and in the earlier registrations holds |
| Written | 2026-11-22, by Claude Science, **before the scoring of the frozen 2026-27 test, while no score record of that test exists and its status is not known**. What the author has seen is listed in the exposure disclosure |
| Approved by | Amir, "do your recommendation", 2026-11-22, in answer to three options set out with their consequences: this amendment, written before scoring; no change; or a decision on the day of scoring if the case arises. Then "Yes", 2026-11-22, in answer to a question that named this amendment's file, its final text, its commit alone on the branch `sloan-fullpaper-amendment-24-2026-11-22` and its draft pull request into `main`. The question said that the Yes approves the final text and merges nothing. The merge and the row in the public hash list wait for his separate word |
| Basis | committed and pushed **alone**, before the frozen 2026-27 test is scored and before any code follows it. Nothing below may be relaxed after the frozen 2026-27 test is scored (METHOD.md §8) |

This amendment makes one reading explicit. It adds no analysis and no number, and it changes no registered sentence. It does not let the paper claim more than it claims today. In one state of the frozen test it lets the paper print the narrower statement on prior work that Amendment 23 already fixed.

## Why this exists, in plain words

Amendment 23, rule 4, replaces the paper's sentence on prior work with a narrower one. The narrower sentence may be printed only after two Gaussian Hoops pages have been read in full. One of them shows statistics of the current season, so rule 4 says that both are read in full "only after the frozen 2026-27 test has been scored".

The frozen test can end in three ways (Amendment 8): scored, not adjudicable, or inconclusive. An inconclusive test is one that "could not be scored cleanly". Rule 4 does not say whether such a test "has been scored".

The code written for rule 4 (draft pull request #3696, commit `56ad093`, not merged, nothing rendered from it) takes the careful reading. It accepts a dated full read of those pages beside a record that says scored or not adjudicable, and refuses one beside a record that says inconclusive. Its handoff note says that no registration covers the case and that it goes to Amir.

Under that reading an inconclusive paper would leave the two pages unread and keep the old sentence: a bounded search "found no public test of such league adjustments on what European arrivals went on to do". Amendment 23 says of that sentence that it is wider than what is public and that a reader who knows those pages would call it wrong. The paper would print a sentence that its own registration has called too wide.

This amendment fixes the reading now, while nobody knows how the test will end.

## What has already been seen (exposure disclosure)

* **No score record of the frozen 2026-27 test exists**, and no result of that test exists. The scorer refuses to run before 25 November 2026. The rule below is written without knowing which of the three statuses the record will carry.
* **The author knows what the exposure disclosure of Amendment 23 lists**, among it: E30, E31 and E33; what the paper prints about the 674 arrivals and the 180 older arrivals; and the values of G of E34. The author has computed no interval of T of E34 and has not run E34.
* **What the author did on 22 November 2026 after Amendment 23 was pushed.** It read the code and tests of draft pull request #3696 and ran the paper's test set on a copy of that branch. Those tests use rehearsal score records with made-up outcomes. It read no 2026-27 statistic and opened no Gaussian Hoops page that day.
* **Displays of current-season statistics on record.** In the author's literature search of 15 November 2026 a web-search result showed three current-season statistic lines of EuroLeague players. None was used. Further displays, none of them used, are recorded in Amendment 8 (16 November 2026) and Amendment 15 (17 November 2026).
* **One correction to Amendment 23.** Amendment 23 says of the display of 15 November: "it recorded this that day". That is one day off. The searches of that session ran on 15 November 2026 between 10:58 and 11:31 UTC. The display was first written down on 16 November 2026 at 15:27 UTC, and Amendment 8 of that day records it. Amendment 23 is not edited; this line is the correction.
* **Who has read the Gaussian Hoops pages so far.** The literature ledger records that the league-strength page was read on 18 November 2026 by the lead agent; Amendment 23 records that Codex read it on 21 November 2026. The projections overview, the board for the 2026-27 EuroLeague and the methodology page were read on 22 November 2026 by the author of Amendment 23, as captured text without tables. Codex's review links the overview and the board as read on 21 November 2026; what it saw there is not recorded (Amendment 23).

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

### 1. What "has been scored" means in the order of reading (makes explicit Amendment 23, rule 4, "Order of reading")

For the order of reading, the frozen 2026-27 test **has been scored** once the registered scoring run of November 2026 has written its score record and that record is committed. This holds whatever status the record carries: scored, not adjudicable or inconclusive.

From the day of that record on, the Gaussian Hoops projections overview and its board for the 2026-27 EuroLeague are read in full, at once, in each of the three statuses. They are then entered in the literature ledger with the date read, as rule 4 of Amendment 23 says.

While no score record is committed, the two pages are not read in full. A scoring attempt that stops at a gate and writes no score record is not a scoring in this sense: the files are refreshed, the run is made again, and the read waits for the record.

Reasons.

* The order of reading exists so that nobody working on the paper sees statistics of the 2026-27 season before the November scoring is over. It is over when the score record exists, in every status. The scorer writes one record and refuses to run again once that record exists, so an inconclusive record is as final as a scored one.
* The alternative leaves an inconclusive paper with a sentence on prior work that Amendment 23 calls too wide.
* The reading is fixed before any score record exists, so it cannot be fitted to the status.

### 2. What an inconclusive paper prints (Amendment 23, rule 4, unchanged)

The condition of rule 4 and gate G23d of Amendment 23 apply in every status, word for word. The narrower statements are printed only after each named page has been read in full and entered in the ledger with its date. The sentence under "What was not found" is printed only if the ledger records no comparison of a forecast with and without a league level for basketball players in European competitions. If a page does report such a comparison, the sentence is not printed and Amir is told before any writing.

Nothing else about an inconclusive paper changes. The abstract ends as Amendment 8 fixes ("could not be scored cleanly, so the registered test is inconclusive"), no licence sentence is used, and every rule on what such a paper prints of the frozen test stands as registered.

Appendix N may carry one sentence, in every status: "On 22 November 2026, before scoring, a further registration fixed that the two pages which show current-season statistics are read in full once the score record of the frozen test is committed, whatever its status [Amendment 24]."

### 3. The order of the two days stands

In every status, a full read of those two pages that is dated before the day of the score record is refused. A score record that gives no day of scoring is refused beside a dated read. Both days are written as YYYY-MM-DD and compared as days.

## Gates

| Gate | Pass rule | Negative control |
|---|---|---|
| G24a the order of reading | the renderer accepts a dated full read of a page that is marked as read in full only after scoring when, and only when, a committed score record stands beside it and the day of the read is not before the day of that record; it does so in each of the three statuses | a dated read with no score record must be refused; a dated read one day before the day of scoring must be refused in each of the three statuses; a score record without a day of scoring must be refused beside a dated read |
| G24b the inconclusive paper | in an inconclusive paper with both pages read in full and no comparison in the record, the two statements of Amendment 23, rule 4, are printed and the old sentence is in no part of the paper; the texts that state the status of the frozen test are the same as with the pages unread | in an inconclusive paper a record with one date missing must leave the old sentence in place; a record with one comparison must stop the sentence under "What was not found" |

## Threats and their controls

| Threat | Control |
|---|---|
| A reading chosen after the status of the test is known | the rule is committed and pushed before any score record exists |
| Statistics of the 2026-27 season seen before the scoring | the two pages are read in full only beside a committed score record and not before its day (G24a); a stopped attempt without a record does not count |
| A record that is inconclusive because a data gate could not be repaired prints no contrast, so the full read would then be the paper's first reading of current-season statistics beyond the displays on record | the November record is final and the scorer refuses a second run; the frozen forecasts are pinned by hash; the ledger gives the date of the read; no rule may be relaxed after scoring |
| In every status the full read comes before the re-score of February 2027 | this follows from Amendment 23, rule 4, and is not new here; the rules of the re-score are fixed by Amendments 1, 8 and 18, the frozen forecasts are pinned by hash, and the ledger gives the date of the read, so a reader of the re-score can see the order |
| The narrower statement on prior work used to draw attention from an inconclusive test | the texts that state the status of the test are unchanged (rule 2); the statement on prior work claims less than the sentence it replaces |
| A paper that keeps a sentence its own registration calls too wide | rule 1 removes that case |

## Not part of this amendment

* No rule on the frozen test, its statuses, its contrasts, its read-outs or its re-score is changed.
* No rule of Amendment 23 other than the meaning of one phrase in "Order of reading" is touched. E34 is not affected.
* The German Basketball Analytics post of 8 July 2025 was read in full on 22 November 2026, as Amendment 23 allows at any time.

## Scope boundary: nothing pinned changes

No registered analysis, estimate, interval, threshold, forecast, frozen file or registered sentence is changed. No generator is edited by this amendment. The frozen 2026-27 forecasts are not read by any rule above.
