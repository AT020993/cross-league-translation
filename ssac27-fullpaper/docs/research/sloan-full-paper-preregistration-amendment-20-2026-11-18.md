# Amendment 20 to the SSAC27 full-paper pre-registration: five named pairs of newcomers in the main text, and one reading of the league-changes slope for a club

**Approval record.**

| | |
|---|---|
| Amends | `docs/research/sloan-full-paper-preregistration-2026-11-03.md`, as amended through Amendment 19. It adds to rules 2, 12 and 13 of Amendment 19, adds one clause to its rule 1, and replaces the second half of its rule 6, each named below. Everything else in those amendments holds |
| Written | 2026-11-18, **after the league-changes test (E30) was scored and after a second round of three blind mock readings (renders 39 and 40)**, and before any 2026-27 statistic was read. Every rule below was written with the E30 and E31 results in view |
| Approved by | Amir, "Yes, accept as written; push, merge and hash", 2026-11-18, in answer to a question that named this amendment, its five named pairs in the main text, its reading for a club, its push alone, its merge and its public hash row. He was offered a version without rule 1 |
| Basis | committed and pushed **alone**, before the text it governs is written into the paper. Nothing below may be relaxed after the frozen 2026-27 test is scored (METHOD.md §8) |

This amendment changes wording and placement. It adds no analysis and no number. The table of rule 1 is a cut of the registered E32 table, made by a rule that is fixed here.

## Why this exists, in plain words

Three new readers who did not know which version was newer read render 39 and render 40. All three preferred render 40, and all three called it borderline. Each said the same thing would change the call: the scored frozen 2026-27 test, shown with real named newcomers in the main text. Amendment 19, rule 12 puts the named newcomers in the appendix, with a pointer. This amendment lets the main text print a short named table, and fixes which rows it holds **before any 2026-27 number is read**, so that the rows cannot be chosen for how they turned out.

The readers also found three numbers close to 0.75 in the paper that mean different things: the registered reading ("about three quarters of its size"), the weight of the fitted equation (0.75), and the labelled reading per league-number gap (1.02). The advice to a club used the labelled reading, which was stated after the result. This amendment lets the advice to a club use the registered reading instead.

## What has already been seen (exposure disclosure)

* **E30 has been scored**, once (retained run `league-changes-score-01`, 18 November 2026): registered case "Clear"; slope 0.77 (95% interval 0.69 to 0.84); 0.57 (0.48 to 0.66) without Spain; 0.79 (0.68 to 0.88) with the table refitted only on earlier arrivals.
* **E31 exists**: the paper's league numbers and the 2015 table are "not distinguishable" on league changes and on the 674 arrivals.
* **Two rounds of blind mock readings exist** (renders 38 and 39; renders 39 and 40; both 18 November). They are opinions of simulated readers, not evidence about the result.
* **No result of the frozen 2026-27 test exists**, and no 2026-27 statistic, roster or signing file has been read. The E32 generator has been run on made-up data only. No row of an E32 table for real players exists.

## Specification

| Field | Registered choice |
|---|---|
| Unit | Unchanged |
| Population | Unchanged |
| Estimator | Unchanged. Rule 1 prints rows of the registered E32 table; it computes nothing |
| Null | Unchanged |
| Filter | Unchanged |
| Key | Unchanged |
| Uncertainty | Unchanged |

## The rules

### 1. Five named pairs in the main text (adds to Amendment 19, rule 12)

In every state of the frozen test in which the E32 tables are printed, the section on the frozen 2026-27 test prints one table in the main text, in addition to the pointer to the full E32 tables.

* **Which rows.** The first five pairs of the registered table "the calls the table changes" (Amendment 15; Amendment 18, rule 9): pairs of newcomers in the same competition and from different source leagues whose order is strictly reversed between the destination-only forecast and the league-aware forecast, taken over the two competitions together and ordered by the gap in the league-aware forecast, largest first. A tie at the fifth place is broken by the order of the committed E32 table. If fewer than five such pairs exist, all are printed and the paper says so; if none exists, the paper says that in one sentence.
* **What each row shows.** For each of the two players: name, competition, source league, last season's domestic rate, the destination-only forecast, the league-aware forecast, games played so far and what he has produced so far. One last column says which of the two has produced more so far.
* **What stands beside it.** The count of all such pairs, and in how many of the ten registered pairs the league-aware order is the one that holds so far, with the registered words "described and not tested" (Amendment 15). The paper draws no conclusion from the five pairs or from that count, in the main text, the abstract or the conclusion.
* **Selection never looks at the outcome.** The five pairs are chosen from frozen forecast columns only. They are printed whatever they show.
* Named players appear nowhere else in the main text. Before scoring the paper prints no named player (Amendment 15).

### 2. The reading a club is given for a change of domestic league (replaces the second half of Amendment 19, rule 6)

For a player who changes domestic league, the club section may give the **registered** reading in place of the reading of Amendment 19, rule 5: on average his rate moved by about three quarters of the gap between the two leagues' Equivalents (the registered slope, with the lowest leave-one-league-out slope and its league in the same sentence or the next). "About three quarters" follows the condition of Amendment 19, rule 1. The paragraph still says that this is an average over the league changes of the test and not a statement about one pair of leagues or one player.

The club section prints one of the two readings, not both. The reading of Amendment 19, rule 5 may then stand once, in Results, with its label and its limits unchanged.

### 3. The sensitivity that removes overlap in time, in the introduction (adds to Amendment 19, rule 1)

The introduction may add, beside the lowest leave-one-league-out slope, the registered sensitivity of Amendment 19, rule 8 in one clause: its slope, and the words that the table was refitted only on arrivals before the season of each move. Its interval, its number of league changes and its seasons stay in Results. It does not enter the abstract.

### 4. Figure 1 (adds to Amendment 19, rule 13)

The right panel may also print the lowest leave-one-league-out slope beside the group it marks, and the slope of the sensitivity of rule 3. It prints no other number and names no single pair.

### 5. The abstract's clause on the 2015 table (adds to Amendment 19, rule 2)

The clause on the 2015 table keeps the words "not distinguishable". The same sentence may go on to say what this paper adds, limited to the list of Amendment 19, rule 7 (the registered test on league changes, an interval for each league number, one fitted equation for both competitions, a refit before each season), with no number. The paper never says its own table is better. The limit of nine numbers in the abstract stays.

### 6. The heading of the Results section on translation

The heading may read "A translation factor adds nothing detectable on top of the league numbers", the words of the first page, in place of "Simple league context matches the measured translation gain". The registered equivalence statement, its margin and the fact that the margin was set after the interval was seen stay in the main text unchanged (Amendment 13, rule 3; Amendment 19, rule 11).

## Gates

* **G20a.** The five pairs of rule 1 are the first five rows of the committed E32 table of changed pairs, and the step that selects them does not receive the outcome column. **Negative control:** a test in which the outcome column is deleted must give the same five pairs in the same order; a main-text table whose rows are not those five is refused by the renderer.
* **G20b.** The renderer refuses a named table when no score record of the frozen test exists. **Negative control:** a render in the pending state with a named table is refused.
* **G20c.** The club section holds at most one of the two readings, and the reading of Amendment 19, rule 5 carries its label wherever it is printed. **Negative control:** a text with both readings in the club section is refused.

## Threats and their controls

| Threat | Control |
|---|---|
| Named players chosen because they turned out well | the rows are fixed now, by frozen forecasts only (G20a), before any 2026-27 statistic is read; they are printed whatever they show |
| Five pairs read as evidence | the count for all ten registered pairs stands beside the table with the words "described and not tested"; the paper draws no conclusion from them |
| The advice to a club rests on a reading stated after the result | rule 2 lets the club section use the registered reading, with the lowest leave-one-league-out slope beside it |
| The first page gains a flattering number | rule 3 adds a registered sensitivity that was fixed before E30 was scored; the lowest leave-one-league-out slope stays beside it |

## Scope boundary: nothing pinned changes

No analysis, estimate, interval, threshold, forecast, frozen file or registered sentence is changed. Amendment 19, rule 12 stands for everything else: a failure to replicate, a not-adjudicable or an inconclusive state, and any sentence of Amendment 18, rule 5, stay in the main text and in the abstract ending as registered. The E32 tables of Amendments 15 and 18 are printed in full in the appendix as before.
