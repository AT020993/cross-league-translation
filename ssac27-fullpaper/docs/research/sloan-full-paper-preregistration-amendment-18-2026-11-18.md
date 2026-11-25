# Amendment 18 to the SSAC27 full-paper pre-registration: readings made explicit before the frozen 2026-27 test is scored, and before any named newcomer is printed

**Approval record.**

| | |
|---|---|
| Amends | `docs/research/sloan-full-paper-preregistration-2026-11-03.md`, as amended through Amendment 17. It makes explicit how the 3 Nov registration, Amendment 8 and Amendment 15 are read where their text left a choice open for the frozen 2026-27 test (P1) and for the named-newcomer tables (E32) |
| Written | 2026-11-18, after the frozen-test scorer was written and rehearsed on made-up outcomes, **before any 2026-27 statistic, roster or signing file was read and before the frozen test is scored** |
| Approved by | Amir, "Yes, accept as written; push, merge and hash", 2026-11-18, in answer to a question that named this amendment, its postponed-game rule, its push alone, its merge and its public hash rows |
| Basis | committed and pushed **alone**, before the 2026-27 files are refreshed on or after 25 November. Nothing below may be relaxed after a result is seen (METHOD.md §8) |

Everything in the 3 Nov pre-registration and in Amendments 1 to 17 stands. This amendment adds no analysis and no read-out.

## Why this exists, in plain words

Writing and rehearsing the scorer of the frozen test showed places where the registered rules can be read in two ways. A choice made silently in code is still a choice. Each one is written down here, with the reason, while no 2026-27 outcome exists. One of them matters more than the others: as the scorer was first written, a single postponed game would have made the whole frozen test "inconclusive". Rule 1 fixes how a postponed game is read.

## What has already been seen (exposure disclosure)

* **No 2026-27 statistic, roster or signing file has been read**, by a person or by code. The scorer was rehearsed on twelve made-up cases only (retained run `p1-rehearsal-02`).
* **The layout of the 2025-26 schedule file was read** (its column names, and that its `played` column is true in every row), to write rule 1. That file is a 2025-26 file and holds no 2026-27 game.
* **The league-changes test (E30) has been scored**, once, on 18 November 2026 (retained run `league-changes-score-01`): registered case "Clear", slope 0.77 (95% interval 0.69 to 0.84). **E31a and E31b exist** and both read "not distinguishable". None of these uses a 2026-27 outcome, and no rule below depends on them.
* **The 674 arrivals of 2020-2025 are fully seen**, as stated in every earlier registration. Rules 4 and 8 use committed values from them, as the 3 Nov registration and Amendment 8 already require.

## Specification

| Field | Registered choice |
|---|---|
| Unit | Unchanged: one newcomer (a player-season of 2026-27 in the EuroLeague or the EuroCup with a frozen forecast) |
| Population | Unchanged: destination season 2026 under the v10 eligibility rules, counting continental games dated on or before 24 November 2026. Rule 1 states how a postponed game is read |
| Estimator | Unchanged. No estimator is added |
| Null | Unchanged |
| Filter | Unchanged. Rule 3 states two details of the join rule of Amendment 8 |
| Key | Unchanged: the v10 name key |
| Uncertainty | Unchanged. Rule 4 states the two formulas behind numbers that are printed before any contrast |

## The readings (all fixed before any 2026-27 outcome exists)

### 1. A postponed game (3 Nov registration, "Population at scoring")

The registration counts "continental games dated on or before 24 Nov 2026". A game that the refreshed official schedule marks as **not played** was not played by that date: it is a postponed game, not a missing box score. It does not stop the scoring run. Every such game is listed in the score record with its game code, date and clubs, and the paper states how many there were.

A game that the schedule marks as **played** and that has no box score is a missing box score. It stops the run, as before. A round with no game at all among the games dated on or before 24 November stops the run, as before.

Reason: without this rule one postponed game would make the frozen test inconclusive, although nothing about the forecasts or the outcomes would be in doubt. The rule is fixed before the 2026-27 schedule is read, so it cannot be fitted to which games were postponed.

### 2. Which state wins (Amendment 8, the abstract endings)

When the test is both unclean (an unscorable target, or more than 5% possible lost targets, or a data check that cannot be repaired) and has fewer than 60 scored newcomers, its state is **inconclusive**. The paper states both facts. Reason: when the newcomers cannot be counted cleanly, their number cannot be read either.

### 3. Two details of the join rule (Amendment 8, rule 3)

* A player's **surname** is the last word of his name after the v10 name normaliser.
* The **5% bar** divides the possible lost targets by the newcomers who joined a frozen row, as the rule's words say ("of the joined newcomers"), and not by the scored newcomers.

Both are the readings that flag more players, so neither makes a clean result easier to reach.

### 4. Two formulas for numbers printed before any contrast (3 Nov, "Power" and "Outcome"; Amendment 8)

* **Detectable effect of S1 and S2 at n newcomers:** the detectable effect of the same contrast on the 674 arrivals, as committed for E28, multiplied by the square root of 674 / n.
* **Expected noise at the realised game counts:** E6 gives the noise spread of a full-season EFF/36 on the 674. Noise variance is taken to fall in proportion to games played, so the per-game variance is E6's variance divided by the mean of 1 / games over the 674, and the expected noise for the newcomers is that per-game variance times the mean of 1 / games over the newcomers. The formula must give back E6's value at the 674's own game counts, or the run stops.

### 5. Three outcomes the wording tables did not cover (Amendment 8, "What the paper may say")

Each of these goes to Amir before any writing, and each is then printed in the main text in these words:

| Read-out | Interval | Wording |
|---|---|---|
| S1 | wholly below zero | "On unseen 2026–27 forecasts the league-aware forecast was less accurate than history alone (X EFF/36, interval): a failure of the league-aware forecast on 2026–27." |
| S2 | wholly below zero | "Once the destination was known, knowing the source league made the 2026–27 forecasts less accurate (X EFF/36, interval): a failure of the league-aware forecast on 2026–27." |
| S4 | wholly below 50% | "On unseen 2026–27 forecasts the league-aware forecast ordered X% of cross-league pairs correctly (interval), fewer than a coin flip would: a failure of its ordering on 2026–27." |

The partial-season caveat of Amendment 8 is printed beside each, as registered.

### 6. The refresh (3 Nov, "Population at scoring")

"Refreshed on or after 25 Nov" means that every row of the four outcome files (box scores and schedules of the two competitions) carries a refresh time on or after 25 November 2026, 00:00 UTC. A refresh that appends new games and keeps older rows with older refresh times does not pass.

### 7. The list of registered players (Amendment 8, rule 3)

The list that names each newcomer's club and previous club is the 2026-27 registration list of the EuroLeague API, in the layout of the list pinned for E26 (competition, season, name, previous team, club; no statistic). It is written by a committed script, fetched on or after 25 November, and its sha256 is written into the score record.

### 8. The error bands (Amendment 8, "At the February re-score only")

The two half-widths that Amendment 8 required to be committed before 25 November are committed in `docs/research/artifacts/sloan-fullpaper-p1-scorer-2026-11/p1_band_half_widths.json` (sha256 `0f384e20e17e2ecc2122f2ff4ddd9107c7cd72f57dd7f1d7e82ca5ed5c247963`): 4.661601 EFF/36 for the 80% band and 7.253359 EFF/36 for the 95% band. The scoring run recomputes them and stops if they differ.

### 9. The named-newcomer tables (Amendment 15, E32)

* "The ten pairs with the largest forecast gap" are ten pairs over the two competitions together. Every such pair is in the committed table, and the paper prints their count.
* The order of a pair "differs" when it is strictly reversed between the destination-only forecast and the league-aware forecast. A tie in either forecast is not a difference.
* A competition with twenty scored newcomers or fewer is printed whole, once, and not as "ten highest" and "ten lowest".
* Ties in a forecast are ordered by name.

None of these uses an outcome.

## Gates

* **G18a.** The scorer implements rule 1. **Negative controls** on made-up schedules: a game marked played with no box score must stop the run; a game marked not played with no box score must pass and must appear in the score record's list of postponed games.
* **G18b.** The renderer prints the three sentences of rule 5 for made-up records with those intervals, and refuses to render such a record without them.
* **G18c.** The score record names this amendment by its sha256, so the order "readings fixed, then scored" can be checked from the files. **Negative control:** a changed byte in this file must stop the scoring run.

## Threats and their controls

| Threat | Control |
|---|---|
| Readings chosen to help the result | every rule is fixed while no 2026-27 statistic has been read; the score record pins this file (G18c) |
| A rule that hides missing data (rule 1) | only a game the official schedule itself marks as not played passes; a played game without a box score and a missing round still stop the run; every postponed game is listed and counted in the paper |
| Wording invented after a bad result (rule 5) | the three sentences are fixed now and each goes to Amir before any writing |

## Scope boundary: nothing pinned changes

No forecast, frozen file, population rule, threshold, contrast, interval method or registered sentence is changed. The scoring date, the 60-newcomer floor, the 5% bar and the failure rule of Amendment 8 stand.
