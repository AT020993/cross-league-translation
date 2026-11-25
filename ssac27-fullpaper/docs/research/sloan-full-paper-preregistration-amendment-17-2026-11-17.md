# Amendment 17 to the SSAC27 full-paper pre-registration: readings made explicit before the league-changes test is frozen, and two corrections

**Approval record.**

| | |
|---|---|
| Amends | `docs/research/sloan-full-paper-preregistration-2026-11-03.md`, as amended through Amendment 16. It makes explicit how Amendments 14, 15 and 16 are read where their text left a choice open, and corrects one sentence of Amendment 14 |
| Written | 2026-11-17, after the E30 generator was written and tested on made-up data, **before the freeze run and before any outcome of a league change was joined or read**. Rule 9 (one sentence about E31a) was written **after** the E31a result was seen, and says so |
| Approved by | Amir, "Yes, accept as written; push, merge and hash", 2026-11-17, in answer to a question that named this amendment, its push alone, its merge and its public hash row |
| Basis | committed and pushed **alone**, before the freeze run of E30. Nothing below may be relaxed after a result is seen (METHOD.md §8) |

Everything in the 3 Nov pre-registration and in Amendments 1 to 16 stands. This amendment adds no analysis.

## Why this exists, in plain words

Writing the code for the league-changes test showed places where Amendment 14 can be read in two ways, and writing the new first page showed the same for Amendment 16. A choice made silently in code is still a choice. Each one is written down here, with the reason, while no outcome of a league change exists. Two things are different in kind and are marked: a correction of a sentence in Amendment 14 that described a check too strongly, and one reading rule for E31a that is settled after its result was seen.

## What has already been seen (exposure disclosure)

* **No outcome of a league change has been joined, summarised or read.** The generator has been run on made-up data, and its freeze path has been run dry on the real box scores (inputs and stayers only): 3,423 league changes and 9,057 stayer pairs, as registered; a stayer forecast of 4.012 + 0.653 x + 0.109 h − 0.836 a with a residual spread of 3.44 EFF/36; a trial of gate G30d on stayers (slope 0.022, interval −0.023 to 0.065). None of these is from a retained run.
* **The E31a result exists** (retained run `e31a-01`, 17 November): errors 2.989, 2.950 and 2.924 EFF/36 for the destination-only forecast, the 2015-table forecast and the league-aware forecast; the 2015 table against destination-only +0.039 (0.002 to 0.077) unweighted and +0.036 (−0.010 to 0.082) weighted by minutes; the league-aware forecast against the 2015 table +0.026 (−0.008 to 0.060) and +0.037 (−0.003 to 0.077). Rule 9 was written with these in view.
* **No result of the frozen 2026-27 test exists**, and no 2026-27 statistic was read.

## Specification

| Field | Registered choice |
|---|---|
| Unit | As in Amendments 14 and 15: one league change (E30, E31b); one arrival (E31a, E31c) |
| Population | Unchanged. Rule 1 states which reading of Amendment 14's population gives the registered counts |
| Estimator | Unchanged. No estimator is added |
| Null | Unchanged |
| Filter | Unchanged |
| Key | Unchanged: Proballers `player_name` × season for league changes |
| Uncertainty | Unchanged. Rule 5 states that every E30 interval comes from the one registered bootstrap |

## The readings (rules 1 to 8 are fixed before any league-change outcome exists)

### 1. Which seasons count (Amendment 14, population)

A player-season counts when the player has at least 8 games and positive minutes in one of the **ten source leagues**, and his league for that season is the one of those ten with the most minutes. A larger stint outside the ten (Poland, a continental competition) does not remove the season. This is the reading that gives the registered counts of gate G30b (3,423 and 9,057). The repository's source-season function used unchanged, which lets a larger Polish stint displace the season, gives 3,381 and 9,031 and is not the registered population; the difference is 101 player-seasons.

### 2. The corpus and the career rate (Amendment 14, pinned inputs)

The box scores are everything `scripts/build_league_factors.py::load_player_games("proballers")` reads: 155 files, seasons 2015 to 2025, raw Proballers names. The career rate h uses every game in that corpus in seasons before the starting season, as the paper defines it (the ten leagues, Poland, the Champions League and the Proballers copies of the EuroLeague and EuroCup). Every one of the 155 files is hashed in the freeze record. The paper says that this corpus is not the corrected corpus of the 674 arrivals.

### 3. Gates (Amendment 14, G30c and G30d)

G30c runs in its own step on made-up players only (20,000 made-up players, 15,987 made-up league changes, seed 20261117, fixed before its first run), and the freeze refuses to run without its passed record. The made-up sample is larger than the real one so that the gate tests the code and not chance. G30d needs the real predicted changes and computes a slope, so it runs at the start of the scoring run, before any outcome is joined, and stops the run if it fails.

### 4. N in the registered sentence (Amendment 14, wording)

In "predicted what happened to N players who changed domestic league", N is the number of players (1,649 in the dry count). The number of league changes is stated beside it.

### 5. Intervals and subsets (Amendment 14, S-a to S-f)

Every E30 interval, including S-a, comes from the one registered bootstrap (players resampled, the stayer forecast refitted in every draw, percentile limits). Leave-one-league-out and sensitivities 1, 2, 3, 6 and 8 remove league changes only and keep the stayer forecast fitted on all stayers. Sensitivity 6 keeps league changes with at least 15 games in both seasons; it does not re-select seasons with a floor of 15.

### 6. S-d is read for its width (Amendment 14, S-d)

Redrawing the ten table values adds noise to the predicted change, and noise in a predictor pulls a slope towards zero. On made-up outcomes with a planted slope of 1, S-d gave an interval of about 0.60 to 1.04. The paper therefore reports S-d as a measure of how much the table's own uncertainty widens the interval, says in the same sentence that its centre sits low by construction, and does not use S-d to decide the case.

### 7. Two outcomes the wording table did not cover (Amendment 14, wording)

* **The interval lies wholly above 1** (with the Clear or the named-limit rule met): the sentence ends "larger than the table implies".
* **A leave-one-league-out interval lies wholly below zero:** the case is "Positive, with a named limit", and the limit reads "without [league] the slope is below zero (interval)". It goes to Amir before any writing.

### 8. E31b and E31c (Amendment 15)

In E31b each scale's coefficient is fitted through the origin (no difference between leagues, no predicted change), on league changes of earlier arrival seasons. The second frozen file of E31c is `docs/research/artifacts/sloan-fullpaper-p1-freeze-2026-11/p1_frozen_published_table_forecasts.parquet` (sha256 `4890fa1943a1e1ed40b0e3086a10274536aa315bf4eed8f4449d1815c98c8199`, commit `10ad0807`, first push 2026-11-17 19:34:38 UTC, written with no 2026-27 statistic read).

## One reading settled after its result was seen

### 9. Which weighting the E31a sentences follow (Amendment 15, wording)

Amendment 15 asks for E31a unweighted and weighted by destination minutes and gives one wording per reading, but does not say which weighting a sentence follows when the two differ. They differ for one contrast: the 2015 table against the destination-only forecast is above zero unweighted and includes zero weighted. **This rule is written after that result was seen.** It applies the paper's standing rule, fixed on 3 November and used for every other comparison: the unweighted analysis is primary and decides the sentence; the weighted value is printed beside it, and a weighted interval that includes zero is worded "not clearly above zero when weighted by playing time" (the wording of Amendment 9). The paper states in the same paragraph that this reading was settled after the result. Under this rule the sentence reads that the 2015 table improves a destination-aware forecast; under the other weighting it would read that it adds nothing detectable.

## Two corrections

### 10. A sentence of Amendment 14 described a check too strongly

Amendment 14 says that of the 55 code files that load box scores, link two seasons and compare leagues, "53 have a continental competition on one side and the other two were opened (same-season pairs; the registered arrivals)". What was checked is narrower: the 53 **mention** a continental competition somewhere in the file (a keyword count; four of them only one to three times, and by their stated purpose those four work on the registered arrivals). Of the two files opened, one is a simulation study on generated rows scored on the arrival cohort and the other formats the printed extract of the older-seasons test. The finding of the check is unchanged: no estimate or score of what happens after a league change was found. Amendment 14 is not edited; this is the correction of record.

### 11. An approval that was relayed wrongly

On 17 November a lane's copy of the 155 box-score files into its scratch working copy ran on a note from the lead agent that was meant for a different step. No result was computed from it outside dry runs of the freeze path, nothing was pushed, and Amir approved the copy afterwards when asked directly. It is recorded here because the freeze run takes its inputs from those copies.

## Counting numbers in the abstract (Amendment 16, rule 4)

Rule 4 of Amendment 16 allows "at most eight numbers" without saying what counts. **A number is an estimate, a count or a league-rate value; an interval counts together with its estimate; dates, season labels and the unit do not count.** Under this rule the abstract with E30 not run holds four. Two E30 cases ("Clear" with an interval below 1, and "Positive, with a named limit") would hold nine once the frozen test is scored. For those two cases the limit is nine. This is fixed before any result of E30 or of the frozen test exists.

## Gates

* **G17a.** The freeze record of E30 names this amendment by its sha256, so the order "readings fixed, then frozen" can be checked from the files. **Negative control:** a changed byte in this file must fail the freeze's pin check.
* **G17b.** The renderer's abstract counter implements the counting rule above and refuses an abstract over its limit. **Negative control:** a made-up abstract with one number more must be refused.

## Threats and their controls

| Threat | Control |
|---|---|
| Readings chosen to help the result | rules 1 to 8 and the counting rule are fixed while no league-change outcome and no frozen-test result exists; the freeze record pins this file |
| A reading chosen after a result (rule 9) | marked as such here and in the paper; it applies a rule fixed on 3 November; both weightings are printed |
| A registration that overstates a check | rule 10 states what was checked; the earlier file is not edited |

## Scope boundary: nothing pinned changes

No analysis, threshold, model, population count, forecast or registered sentence is changed. The registered counts, the case rules and the stop rule of Amendment 14 stand.
