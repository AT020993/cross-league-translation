# Amendment 15 to the SSAC27 full-paper pre-registration: a published league table as a rival (E31), and named 2026-27 newcomers (E32)

**Approval record.**

| | |
|---|---|
| Amends | `docs/research/sloan-full-paper-preregistration-2026-11-03.md`, as amended through Amendment 14 |
| Written | 2026-11-17, before the analyses below were implemented |
| Approved by | Amir, "Yes, accept as written and push", 2026-11-17, in answer to a question that named this amendment and its push |
| Basis | committed and pushed **alone**, before any implementation. Nothing below may be relaxed after a result is seen (METHOD.md §8) |

Everything in the 3 Nov pre-registration and in Amendments 1 to 14 stands. This amendment **adds** two items: E31, exploratory on seen seasons and registered ahead of the frozen 2026-27 test and of E30; and E32, a table of frozen forecasts that computes no result. It changes no registered analysis, threshold, model, population or licence.

## Why this exists, in plain words

1. **The paper tests "translation factors" in general and names no published league adjustment.** A reader can fairly ask whose method is being tested, and whether the paper's own league table only wins a contest that its author set up. League-strength tables for European basketball have been published. One of them was printed in November 2015, before every season the paper scores, so it cannot have seen any of these outcomes.
2. **The paper's only worked example uses two invented players.** The forecasts for 2026-27 were frozen on 3 November. Printing them for named players, chosen by a rule that does not look at how they played, puts real cases in the paper without selecting on success.

## What has already been seen (exposure disclosure)

* **The 2015 table's values were read on 17 November** from the published article: Layne Vashro, "Deep Dives: Measuring Level of Competition Around the World", Nylon Calculus (FanSided), 6 November 2015. They are listed below. Its order agrees with Table 2 of the paper at the two ends (Spain highest, Lithuania lowest among the ten) and differs in the middle. No correlation, error or forecast was computed with them.
* **A second public table** (Gaussian Hoops, "league strength") was seen only as a search snippet with six values. Its site has not been opened. By its own description it is built on player moves of 2021-22 to 2025-26, so it overlaps the scored seasons.
* **Everything E31a uses on the 674 arrivals is exposed**; E31a is exploratory. The frozen 2026-27 test and the league changes of E30 are unread.
* **Two incidental displays on 17 November**, neither used: a count on the key columns of `data/processed/rapm/rapm.parquet` printed how many rows and reliable flags carry the 2026-27 label for three competitions, and the highest season label of `data/processed/player_roles.parquet` was seen (no player statistic, name or error was read); and during the literature search a repository README said its league effects are fitted through 2026-27 (values not copied), a web post showed a heading for 2026-27 projections (reading stopped there) and a search snippet showed 2026-27 projections for college newcomers in the United States.
* **No 2026-27 signing list or roster file was opened** to write this amendment.

## Pinned inputs

| Input | Pin |
|---|---|
| The 2015 table (standardised competition scores; 0 = the average venue, 1 = one standard deviation above it) | Spain ACB 1.52; Italy 1.12; VTB United League 0.87; Adriatic league 0.82; Turkey BSL 0.77; France Pro A 0.69; Germany BBL 0.65; Israel 0.52; Greece 0.43; Lithuania 0.33; EuroLeague 1.61; EuroCup 0.92. The twelve values are committed with the article's title, author, date, address and the date it was read; the article text itself is not copied into the repository |
| Frozen 2026-27 forecasts | `docs/research/artifacts/sloan-fullpaper-p1-freeze-2026-11/p1_frozen_forecasts.parquet`, as pinned on 3 November |
| Further published tables | admitted only by a dated addendum to this amendment, pushed alone before the table's arm is frozen, that lists the table's values, source, date and the seasons it was built on |

## Specification

| Field | Registered choice |
|---|---|
| Unit | E31a and E31c: one arrival (player × destination season). E31b: one league change, as in E30 |
| Population | E31a: the 674 benchmark arrivals of 2020-2025. E31b: the league changes of E30. E31c: the newcomers of the frozen 2026-27 test under its registered rules |
| Estimator | Paired differences in mean absolute error, EFF/36, between the forecast that uses the published table and (i) the forecast that knows only the destination, (ii) the league-aware forecast |
| Null | Zero for each paired difference |
| Filter | None beyond each population's registered rules |
| Key | The registered key of each population |
| Uncertainty | As registered for each population: two-way clustered 95% intervals (player, destination club-season) for arrivals; a bootstrap over players for league changes |

## Analysis

### The published-table forecast (one rule for every table)

The forecast is the registered destination-aware forecast (`history_destination_slope`) plus one term: a single coefficient times the published score of the player's source league. The coefficient is fitted without penalty, walk-forward, on the same training arrivals as every other arm. Nothing else about the table is tuned. This gives the table its best single-number use inside the paper's own forecast; the paper says that the table was built for a different purpose (the level of competition a prospect faced, for the NBA draft).

### E31a, the 674 (exploratory)

The published-table forecast's error on the 674, its paired difference from the destination-only forecast and from the league-aware forecast, unweighted and weighted by destination minutes, with intervals and the 80%-power detectable difference.

### E31b, the league changes (registered before they are read)

On the league changes of E30, two scales are compared on equal terms: the paper's equivalents and the 2015 table. For each scale, the stayer forecast plus one coefficient times the scale's difference between the two leagues, with the coefficient fitted on league changes that arrived in earlier seasons (first scored arrival season: 2018). Reported: each scale's fitted coefficient, each forecast's error, and their paired difference with an interval. E31b is computed in E30's single scoring run and uses its frozen file.

### E31c, the frozen 2026-27 test (registered before scoring)

The published-table forecast is fitted on arrivals through 2025, exactly as the frozen arms were, and written for the same 3,478 rows. The file's sha256 is committed, pushed and added to the public hash list before 25 November. At scoring it is read out beside S1 and S2 of Amendment 8: its error, and its paired differences from the destination-only and the league-aware forecasts. As for S2, no difference is expected to be detectable in November.

### E32, named newcomers with their frozen forecasts

E32 computes no result. It prints frozen forecasts for named players.

* **Who.** After the frozen test is scored: every newcomer the scorer counts (its registered rules), per competition, ordered by the frozen league-aware forecast; the table prints the ten highest and the ten lowest in each competition, with source league, last season's domestic rate, the destination-only forecast, the league-aware forecast and, in the last column, what he has produced so far.
* **The calls the table changes.** Among those newcomers, every pair in the same competition and from different source leagues whose order differs between the destination-only forecast and the league-aware forecast; the paper prints the ten pairs with the largest forecast gap in the league-aware forecast, and the count of all such pairs.
* **Selection never looks at the outcome.** The rules above use frozen forecasts only. The outcome column is printed, never used to choose a row.
* **Before scoring** the paper may print no named player. If fewer than 60 newcomers are scored, E32 prints all of them and the paper says so.

### What the paper may say

| Result | Interval | Wording |
|---|---|---|
| E31a, published table against destination-only | above zero | "a league table printed in 2015 improves a destination-aware forecast by X EFF/36 (interval)" |
| | includes zero | "a league table printed in 2015 adds nothing detectable to a destination-aware forecast (X, interval)" |
| E31a, league-aware against published table | above zero | "the paper's league numbers are more accurate than the 2015 table by X EFF/36 (interval)" |
| | includes zero | "the paper's league numbers and a league table printed in 2015 are not distinguishable (X, interval; a difference of D would have been detected with 80% power)" |
| | below zero | "a league table printed in 2015 is more accurate than the paper's league numbers by X EFF/36 (interval)"; to Amir before any writing |
| E31b | any | each scale's coefficient and error, and "not distinguishable", "the paper's equivalents predicted league changes better by X (interval)" or the reverse |
| E31c | any | the registered frozen-test wording of Amendment 8, applied to these read-outs |
| E32 | n/a | the two tables, the count of changed pairs and, once outcomes exist, in how many of the printed pairs the league-aware order was the right one, described and not tested |

* **Every number is reported whatever it shows.** E31a is labelled exploratory wherever it appears.
* **"Not distinguishable" is not "the same".** The paper states the detectable difference beside it and claims no equivalence.
* **A result in which the 2015 table is at least as accurate as the paper's league numbers** changes what the paper may claim for its own table. It goes to Amir before any writing. The licensed message is then that a simple league table is what matters and that a table printed ten years earlier does the job.

## Gates and negative controls

* **G31a.** Before it adds the published-table term, the generator reproduces the registered errors of the destination-only forecast (2.989) and of the league-aware forecast (2.924) to the printed digits, and to 1e-9 against the committed summary. **Negative control:** published scores shuffled across leagues must give a paired difference from destination-only whose interval includes zero.
* **G31b.** The frozen E31c file has 3,478 rows with the keys of the pinned frozen file and no missing forecast. **Negative control:** a changed byte must fail the hash check at scoring.
* **G32.** Every row of an E32 table is selected by a rule that takes frozen forecast columns only; the generator's selection step does not receive the outcome column. **Negative control:** a test in which the outcome column is deleted must give the same selected rows.

## Threats and their controls

| Threat | Control |
|---|---|
| The author's table wins the author's contest | a rival printed in 2015; one mapping rule fixed here; the same fitting freedom on the league changes (E31b); the frozen test (E31c) |
| The mapping rule is chosen to make the rival look weak | one coefficient, fitted like every other arm; the rule is fixed before any score |
| Tables admitted after their scores are known | further tables only by a dated addendum pushed before freezing |
| A table built on the scored seasons | such a table is scored on the frozen test only, and the paper says so |
| Named players chosen for good outcomes | E32's rules use frozen forecasts only; gate G32 |
| A result that weakens a paper claim | reported to Amir before any writing, then in the main text |

## Scope boundary: nothing pinned changes

No registered analysis, file, forecast or licence is changed. The frozen file of 3 November is not rewritten; E31c adds a second file. Published league scores are not player data; each is stored with its source and date. Names in E32 are of professional players in public competitions and come with player-season values only (no birthdate, no per-game row), as the public-data rules require.
