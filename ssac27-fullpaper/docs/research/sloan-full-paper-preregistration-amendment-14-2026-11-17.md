# Amendment 14 to the SSAC27 full-paper pre-registration: the league table tested on players who changed domestic league (E30)

**Approval record.**

| | |
|---|---|
| Amends | `docs/research/sloan-full-paper-preregistration-2026-11-03.md`, as amended on 2026-11-04, 2026-11-05, 2026-11-11, 2026-11-12, 2026-11-16 and 2026-11-17 (Amendments 1 to 13) |
| Written | 2026-11-17, before the analysis below was implemented and before any outcome of a league change was read |
| Approved by | Amir, "Yes, accept as written and push", 2026-11-17, in answer to a question that named this amendment and its push |
| Basis | committed and pushed **alone**, before any implementation. Nothing below may be relaxed after a result is seen (METHOD.md §8) |

Everything in the 3 Nov pre-registration and in Amendments 1 to 13 stands. This amendment **adds** one analysis, E30. It changes no registered analysis, threshold, model, population or licence.

## Why this exists, in plain words

The paper's league table (the European League Equivalents, Table 2) says that the same forecast needs a higher domestic rate in some leagues than in others: a 16 EFF/36 in Spain's ACB reads like about a 19 in Germany. Every number in that table was fitted on one kind of event, a player's first EuroLeague or EuroCup season, on seasons that had been examined before registration. Its own worth is the least settled result in the paper (E28).

Players also move between the ten domestic leagues. If the table measures something about the leagues, it makes a prediction about those players that it was never fitted to: a player who moves from Spain to Germany should, on average, produce about that much more, and a player who moves the other way about that much less. E30 tests that prediction with every rule fixed first.

## What has already been seen (exposure disclosure)

* **No estimate or score of what happens after a league change was found in this project.** On 17 November 2,858 distinct code files on main and in every agent worktree were scanned by a script. Of the 55 that load box scores, link two seasons and compare leagues, 53 have a continental competition on one side and the other two were opened (same-season pairs; the registered arrivals). The stated purpose of every other match outside the product's question-answering code was read, and the scripts and notes closest to the subject were opened. Files were selected by pattern, so this is a structured read and not a line-by-line read of every file. What it found is listed here so a reader can judge.
* **The moves were counted in August.** Two design notes count "home-league changes" (2,250 and 2,332) and set the design aside in favour of same-season pairs. `scripts/audit_cross_league_identity.py` writes a table of counts per league pair; it holds no rates.
* **League-to-league numbers printed in September were model-implied** from same-season pairs ("not an observed domestic-to-domestic transfer experiment", zero direct pairs).
* **One pooled use.** A September comparator (`scripts/validate_translation_dynamic.py`) estimated a single year-to-year drift variance from consecutive seasons of all players, after removing league effects fitted on same-season pairs. League changers are among those players. It estimated nothing about league changes and printed nothing by league pair.
* **These seasons are inputs elsewhere.** A player's domestic seasons, including seasons after a league change, are the source rate and the career rate of the paper's forecasts whenever he later arrives in a continental competition. They have never been used as outcomes. The paper therefore says "never fitted to and never scored on", not "never seen".
* **Read on 17 November for this amendment, from inputs only:** the counts below under the registered rules; among players who stayed in their league, the slope of next season's rate on last season's rate (0.702) and the residual spread (3.52 EFF/36); and a planning simulation built from those two numbers, the counts and Table 2. No rate after a league change was summarised, plotted or related to the table.
* **Three simulated judges** advised this test on 17 November from a one-page description with the result left blank. Their reading is an opinion about the design.
* **Amir** was asked on 17 November whether anyone had analysed these outcomes outside the repository and answered "Not that I know of".
* **No 2026-27 statistic** has been read for this amendment.

## Pinned inputs

| Input | Pin |
|---|---|
| The league table | `docs/research/artifacts/sloan-fullpaper-amend1-decisions-2026-11/exchange_rate_acb16.csv`, sha256 `c8341a37947adcad882f90c9747ea6fee274723b367a0948bbfc50462fead2ca`; column `acb16_equivalent_eff36`, rows with destination `eurocup` |
| Yearly refits of the table (one sensitivity) | `docs/research/artifacts/sloan-fullpaper-amend3-2026-11/e19_equivalents_by_refit.csv`, sha256 `49814ea0b0a2d4d443e891c4104fe480749876b32585861405454e7ebf502481` |
| Domestic box scores | the Proballers `player_stats` files of the ten leagues, seasons 2015 to 2025, as loaded by `scripts/build_league_factors.py::load_player_games`; their sha256 values are recorded in the freeze run before any outcome is joined |

## Specification

| Field | Registered choice |
|---|---|
| Unit | One league change: a player's season t in domestic league A, followed by his season t+1 in a different domestic league B |
| Population | The ten source leagues of the paper. In each of the two seasons the player has at least 8 games and positive minutes in the league where he played the most minutes that season (the repository's source-season rule). Arrival seasons 2016 to 2025. Counted on 17 November: 3,423 league changes by 1,649 players; every one of the 90 ordered league pairs holds at least 10 |
| Estimator | The slope of the unexplained change on the change the league table predicts (defined below), by ordinary least squares over all league changes |
| Null | Slope zero. The registered direction is positive. A slope of one means the table has the right size |
| Filter | None beyond the population rules |
| Key | Proballers `player_name` × season, the key of `validate_translation_holdout.build_switchers` |
| Uncertainty | 95% interval from a bootstrap that resamples players (2,000 draws) and refits the stayer forecast in every draw; and a permutation test that reassigns the ten table values among the ten leagues (10,000 draws) |

## Analysis

### The prediction (fixed numbers)

For a move from league A to league B the table predicts a change of g = equivalent(B) − equivalent(A), in EFF/36, using the committed EuroCup equivalents. The values are pinned above. Across the counted moves g runs from about −2.8 to about 2.8 with a standard deviation of about 1.56.

### The comparison forecast (a player who stays)

Players move up after good seasons and down after poor ones, and both groups then drift back towards their usual level. Comparing the two directions of a move adds these two drifts together; it does not cancel them. E30 therefore measures every league changer against what the same season would predict for a player who stayed.

* **Stayer forecast.** Fitted by ordinary least squares on players who stayed in the same league (counted: 9,057 pairs of seasons), with the inputs of the paper's forecast: last season's rate x, the career rate h before it (h := x if none), and the flag a = 1[x > h]. Rates are EFF/36 as in the paper; h follows the paper's definition (all games on record in earlier seasons).
* **Unexplained change.** For each league changer, e = (his rate in league B in season t+1) − (the stayer forecast from his season in league A).
* **Primary result.** The slope of e on g. With the table fixed, a slope above zero says the table's order and direction carry over; a slope near one says its size does.

### Order of events

1. This amendment is pushed alone.
2. The generator is written and tested on made-up outcomes only (gate G30c).
3. **Freeze.** One retained run writes, for every league change, its key, the two leagues, x, h, a, g and the stayer forecast. The file's sha256 is committed, pushed and added to the public hash list.
4. **Score, once.** A second retained run reads the frozen file by its hash, joins the rates in league B, and computes everything below.

The same season can be the outcome of one move and the starting point of the next, so these files cannot be sealed from each other. What is fixed in advance is every rule, the code and the frozen predictions.

### Secondary results (all printed)

* **S-a, error.** Paired difference in mean absolute error on the league changers between the stayer forecast and the stayer forecast plus g, with a 95% interval clustered by player.
* **S-b, each league left out.** The slope recomputed ten times, each time without every move that touches one league.
* **S-c, each direction.** The slope separately for moves with g > 0 and with g < 0, and the mean of e in each group.
* **S-d, the table's own uncertainty.** The interval of the slope when the ten table values are also redrawn, each from a normal distribution with the spread of its committed interval. The committed files hold intervals and not the bootstrap draws, so this is an approximation and is labelled so.
* **S-e, sensitivities,** each a slope with its interval: (1) without league changes where either season has a second domestic league with 8 or more games (counted: 447); (2) arrival seasons 2020 to 2025 only (counted: 2,083); (3) arrival seasons 2016 to 2024 only, because four leagues' 2025-26 files stop in January 2026; (4) the stayer forecast with one intercept per league of origin; (5) the EuroLeague equivalents in place of the EuroCup ones; (6) at least 15 games in both seasons; (7) for arrival seasons 2020 to 2025, the table refitted only on arrivals before that season (the committed yearly refits); (8) league pairs with fewer than 30 moves in the two directions together left out.
* **S-f, the picture.** For each of the 45 league pairs, the mean of e for moves from the league with the lower equivalent to the league with the higher one, minus the mean for the opposite direction, divided by two, against g, with the number of moves in each direction. The 45 points come from ten numbers and are not 45 independent tests; the caption says so.

### What the paper may say

Let the primary slope be b with bootstrap interval [lo, hi], and p the permutation share of draws with a slope at least as large.

| Case | Rule | Wording |
|---|---|---|
| Clear | lo > 0 and p < 0.05 and every one of the ten leave-one-league-out intervals has its lower end above zero | "The league table, fitted only on first continental seasons, predicted what happened to N players who changed domestic league: slope b (interval), where 1 would mean the table's size is exactly right." If the interval includes 1: "consistent with the table's size". If hi < 1: "about b of the size the table implies" |
| Positive, with a named limit | lo > 0 and p < 0.05, but a leave-one-league-out interval includes zero | the Clear sentence, followed in the same paragraph by "without [league] the interval includes zero" |
| Positive, not separable from chance | lo > 0 and p ≥ 0.05 | "a positive slope (b, interval) that a random assignment of the ten league values produces in p of draws; with ten leagues the test cannot tell the table's order from chance" |
| Null | lo ≤ 0 ≤ hi | "the league table did not predict what happened to players who changed domestic league (slope b, interval; a slope of 0.11 would have been detected with 80% power under the planning assumptions)" |
| Against | hi < 0 | "players who changed league moved against the table (slope b, interval)" |

* **Every number is reported whatever it shows**, in the main text, with the results of S-a to S-f in the main text or an appendix table.
* **A Null or Against result qualifies the paper's league table.** It goes to Amir before any writing, and then into the abstract, the main text and Limitations. The paper claims no cause for it: the design does not separate a table that describes whom clubs recruit from changes of role, from error in the table, or from wrong name links.
* **A Clear result licenses no statement about league strength as such**, no statement about any single pair of leagues, and no statement of equivalence. It licenses the sentence above and the description "tested on league changes it was never fitted to and never scored on".
* **S-c is read with the result.** If the slope has opposite signs in the two directions, the paper says so beside the primary result.
* E30 changes no registered sentence about the 674 arrivals, the older arrivals or the frozen 2026-27 test.

## Limits stated in advance

* Players who change league are not a random sample, and the stayer forecast removes only the drift that last season's rate, the career rate and the flag can explain. Age is not available in these files.
* Minutes and role change with a move. EFF/36 is a rate, but it is not free of role.
* Players are linked across leagues by name. A wrong link joins two different players and pulls the slope towards zero.
* The table is fitted on the players clubs sign into continental play, with career history equal to the domestic rate. A league change is a different event.
* The table was fitted on arrivals of 2017 to 2025, the same years as most of the moves. Sensitivity (7) uses only earlier arrivals.

## Gates and negative controls

| Gate | Pass rule | Negative control |
|---|---|---|
| G30a inputs | every pinned file equals its sha256 | a changed byte must fail |
| G30b same population | under the registered rules the generator finds 3,423 league changes and 9,057 stayer pairs; any other count stops the run and is reported before an outcome is joined | a games floor of 9 must give a different count |
| G30c the code recovers a planted slope | on made-up outcomes built as stayer forecast + 1.0 × g + noise, the generator returns a slope within 0.05 of 1.0; with 0.0 × g, an interval that includes zero | league labels shuffled across the made-up moves must give an interval that includes zero |
| G30d no slope where none can exist | a made-up "predicted change", drawn from the real g values and assigned at random to stayers, gives a slope whose interval includes zero | the same made-up change added to the stayers' rates must give an interval that excludes zero |
| G30e frozen before scored | the scoring run reads the prediction file whose sha256 was pushed | a changed byte must fail |

If G30a, G30b or G30c fails, E30 stops and Amir is told; no outcome is joined.

## Threats and their controls

| Threat | Control |
|---|---|
| Regression to the mean differs by direction of the move | the stayer forecast; S-c by direction; sensitivity (4) |
| Ten leagues, not thousands of independent tests | the permutation test is part of the Clear rule; S-b; the caption of S-f |
| One league carries the result | S-b, with the league named in the wording |
| Wrong name links | sensitivities (1) and (6); the direction of the bias is stated |
| A partial last season | sensitivity (3) |
| Choosing the reading after the result | the wording table above; one primary result; the frozen file |
| A favourable design chosen with knowledge of outcomes | the exposure disclosure; the code read of 17 November; the frozen predictions |
| A result that weakens a paper claim | reported to Amir before any writing, then in the abstract, the main text and Limitations |

## Stop rule

The freeze run with G30a to G30c passing must exist by the evening of 20 November 2026 and the single scoring run by 21 November. If not, E30 is not run for this submission, and the paper says nothing about league changes.

## Scope boundary: nothing pinned changes

No registered analysis, file, forecast or licence is changed. A test on newcomers to the Basketball Champions League is not part of this amendment. E30 is implemented in a new dated generator with a committed report script, run as retained runs from committed code. Its outputs hold player-season rows derived from the same Proballers files as the paper's public tables and follow the same public-data rules.
