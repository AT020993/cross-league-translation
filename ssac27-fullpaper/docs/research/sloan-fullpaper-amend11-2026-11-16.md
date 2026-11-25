# SSAC27 full paper: Amendment 11 results (E29)

**DESCRIPTIVE.** Every outcome used here had been seen, and part of the table had been seen before registration (see below). E29 shows where the forecast missed. It does not show why, and this note states no cause. Every number below is formatted by `scripts/report_sloan_fullpaper_amend11.py` from committed run outputs; every quoted result sentence is the generator's registered wording.

Pre-registration: `docs/research/sloan-full-paper-preregistration-amendment-11-2026-11-16.md`, pushed alone before its generator existed.

## What E29 asks

E28 found that on the older arrivals the league table did not help. E29 shows where the forecast went wrong, league by league. For each source league it gives three averages: how far the league table moves the forecast, how far the forecast was from the outcome without the table, and how far with it. A negative error means the forecast was below what the arrivals delivered. The same three averages are given for the same leagues on the arrivals of 2020-2025, and for all arrivals of each period.

## Results in plain words

- The Adriatic league, older arrivals (n = 131): the league table lowered the forecast for arrivals from the Adriatic league by 0.68 EFF/36 on average. Without the table the forecast was 0.35 EFF/36 below the outcome (interval −1.00 to 0.30); with it, 1.04 EFF/36 below the outcome (interval −1.69 to −0.38).
- The Adriatic league, older arrivals (n = 131), weighted by destination minutes: the league table lowered the forecast for arrivals from the Adriatic league by 0.68 EFF/36 on average. Without the table the forecast was 0.73 EFF/36 below the outcome (interval −1.35 to −0.10); with it, 1.41 EFF/36 below the outcome (interval −2.04 to −0.78).
- The Adriatic league, arrivals of 2020-2025 (n = 70): the league table lowered the forecast for arrivals from the Adriatic league by 0.53 EFF/36 on average. Without the table the forecast was 0.47 EFF/36 above the outcome (interval −0.55 to 1.50); with it, 0.06 EFF/36 below the outcome (interval −1.15 to 1.04).
- The Adriatic league, arrivals of 2020-2025 (n = 70), weighted by destination minutes: the league table lowered the forecast for arrivals from the Adriatic league by 0.52 EFF/36 on average. Without the table the forecast was 0.06 EFF/36 above the outcome (interval −1.11 to 1.24); with it, 0.46 EFF/36 below the outcome (interval −1.69 to 0.77).
- Israel, older arrivals (n = 49): the league table lowered the forecast for arrivals from Israel by 0.37 EFF/36 on average. Without the table the forecast was 0.30 EFF/36 above the outcome (interval −0.36 to 0.96); with it, 0.07 EFF/36 below the outcome (interval −0.74 to 0.59).
- Israel, older arrivals (n = 49), weighted by destination minutes: the league table lowered the forecast for arrivals from Israel by 0.37 EFF/36 on average. Without the table the forecast was 0.17 EFF/36 below the outcome (interval −0.90 to 0.56); with it, 0.54 EFF/36 below the outcome (interval −1.27 to 0.19).
- Israel, arrivals of 2020-2025 (n = 49): the league table lowered the forecast for arrivals from Israel by 0.50 EFF/36 on average. Without the table the forecast was 0.01 EFF/36 above the outcome (interval −0.79 to 0.81); with it, 0.49 EFF/36 below the outcome (interval −1.28 to 0.31).
- Israel, arrivals of 2020-2025 (n = 49), weighted by destination minutes: the league table lowered the forecast for arrivals from Israel by 0.51 EFF/36 on average. Without the table the forecast was 0.09 EFF/36 below the outcome (interval −1.03 to 0.84); with it, 0.61 EFF/36 below the outcome (interval −1.53 to 0.32).
- All arrivals, older arrivals (n = 180): the league table lowered the forecast for all arrivals by 0.60 EFF/36 on average. Without the table the forecast was 0.18 EFF/36 below the outcome (interval −0.68 to 0.33); with it, 0.77 EFF/36 below the outcome (interval −1.28 to −0.26).
- All arrivals, older arrivals (n = 180), weighted by destination minutes: the league table lowered the forecast for all arrivals by 0.59 EFF/36 on average. Without the table the forecast was 0.57 EFF/36 below the outcome (interval −1.04 to −0.09); with it, 1.15 EFF/36 below the outcome (interval −1.63 to −0.68).
- All arrivals, arrivals of 2020-2025 (n = 674): the league table lowered the forecast for all arrivals by 0.03 EFF/36 on average. Without the table the forecast was 0.44 EFF/36 below the outcome (interval −0.78 to −0.10); with it, 0.47 EFF/36 below the outcome (interval −0.80 to −0.14).
- All arrivals, arrivals of 2020-2025 (n = 674), weighted by destination minutes: the league table raised the forecast for all arrivals by 0.01 EFF/36 on average. Without the table the forecast was 0.97 EFF/36 below the outcome (interval −1.29 to −0.64); with it, 0.96 EFF/36 below the outcome (interval −1.28 to −0.65).
- The Adriatic league, change between periods: −0.83 EFF/36 (interval −2.04 to 0.39; includes zero). The smallest change this comparison could detect with 80% power is 1.73.
- Israel, change between periods: +0.29 EFF/36 (interval −0.75 to 1.33; includes zero). The smallest change this comparison could detect with 80% power is 1.48.
- The unweighted change between periods does not exclude zero for any league, so the registered condition is not met. The paper may not write "consistent with league numbers that change over time"; it says that the table shows where the forecast missed and not why. The change weighted by destination minutes does not exclude zero for any league either.
- Rule applied: may be written only if the change between periods excludes zero for at least one league; read on the unweighted change (the stricter reading: the weighted change cannot license it alone).

## Specification

| Field | Registered choice |
|---|---|
| Unit | One arrival: player × destination season. |
| Population | (a) The older-seasons arrivals of Amendment 7, in the version without Spain's ACB: Adriatic league and Israel (the version the paper prints), n = 180. (b) The 674 benchmark arrivals of 2020-2025. Rows: each source league of the printed older version, and all arrivals of each population. |
| Estimator | Per source league and population, three means in EFF/36: the move (league-aware forecast minus destination-only forecast); the error without the table (destination-only forecast minus outcome); the error with the table (league-aware forecast minus outcome). Each unweighted and weighted by destination minutes. Per source league, the change between periods: error without the table, older arrivals minus arrivals of 2020-2025; the two samples treated as independent, standard errors combined in quadrature, the smaller of the two degrees of freedom. No model is refitted and nothing is re-scored. |
| Null | Zero for each mean error and for the change between periods. |
| Filter | None beyond each population's registered rules. |
| Key | `player_name` × `season_dest` on the 674; API person code × destination season on the older seasons. |
| Uncertainty | Two-way clustered 95% interval (player, destination club-season), Student t with min(clusters) - 1 degrees of freedom. For the change between periods the two samples are treated as independent. Detectable effect with 80% power: (t(0.975, df) + t(0.80, df)) x SE. |

## What had been seen

Seen before Amendment 11 was registered:
- every outcome E29 uses
- on the older arrivals, in one unregistered look after the E28 result (disclosed in Amendment 10), for the version without Spain's ACB: by source league, the number of arrivals, the mean move made by the league table, the mean error of the destination-only and of the league-aware forecast, and G_D unweighted and weighted by minutes; the same by destination competition, and G_D by destination season
- on the arrivals of 2020-2025: the paper's league-bias figure and table (each league's error measured against the average arrival), and the yearly refits of each league's equivalent

Already on file before registration:
- the committed Amendment 4 output (E24) holds, for every source league of the 674, the mean error of the destination-only and of the league-aware forecast not centred on the average arrival, with bootstrap intervals. E29b's unweighted point estimates of the two errors on the 674 are therefore not new numbers, although Amendment 11 lists them as not seen in E29's form. This run reproduces them as a check.

Not seen before this run:
- any two-way clustered interval for the quantities of E29
- their versions weighted by destination minutes
- the change between the two periods
- any per-league number of the withheld version of the older-seasons test

The older-seasons outcomes were read in the single Amendment 7 scoring run and again in E28; E29 is a further reading of them. No rule of that run is changed and nothing is re-scored.

## Three limits printed with the table

1. On the older arrivals the forecasts come from the model fitted on every season through 2025. On the arrivals of 2020–2025 each forecast comes from a model fitted on earlier seasons only.
2. The older source statistics come from the leagues' own box scores. The source statistics of 2020–2025 come from a different provider.
3. A mean error also carries the general level of the forecasts in that period. The rows for all arrivals are printed so that a reader can see that level.

## Gates

| Gate | Status | Largest difference | Negative control |
|---|---|---|---|
| E24_cross_check | passed | 2.8e-16 | rejected as required |
| G0 | passed | 1.3e-15 | rejected as required |
| G29a | passed | 0.0e+00 | rejected as required |
| G29b | passed | 0.0e+00 | rejected as required |
| G29c | passed | 6.7e-16 | rejected as required |
| G29d | passed | n/a | rejected as required |
| frozen_forecasts | passed | 3.6e-15 | rejected as required |
| league_map | passed | n/a | rejected as required |
| scope | passed | n/a | rejected as required |
| scoring_run | passed | 1.8e-16 | rejected as required |

G29a comes first: it reproduces the four committed E28b differences on the older arrivals before anything else is computed; its negative control shuffles the outcome column. G29b reproduces the committed errors of the two forecasts and the committed G_D with its interval on the 674; its negative control shifts one forecast column by 0.01. G29c checks, in each population, that the league means weighted by their numbers of arrivals add up to the mean of all arrivals and that the move equals the error with the table minus the error without it; its negative control drops one league's rows. G29d checks that no number of the withheld version is in the summary or in either table; its negative control plants one. The other gates are additions: the submitted numbers (G0, scope), the frozen forecasts, the Amendment 7 comparisons, the explicit league names of the two populations, and the committed Amendment 4 means on the 674.

## E29a: the older arrivals (180 arrivals)

Printed here: the version without Spain's ACB: Adriatic league and Israel. The older-seasons outcomes were read in the single Amendment 7 scoring run and again in E28; E29 is a further reading of them. No rule of that run is changed and nothing is re-scored. Each cell: mean in EFF/36 (95% interval).

Unweighted:

| Source league | n | Move made by the league table | Error without the table | Error with the table |
|---|---|---|---|---|
| The Adriatic league | 131 | −0.68 (−0.69 to −0.67) | −0.35 (−1.00 to 0.30) | −1.04 (−1.69 to −0.38) |
| Israel | 49 | −0.37 (−0.39 to −0.36) | +0.30 (−0.36 to 0.96) | −0.07 (−0.74 to 0.59) |
| All arrivals | 180 | −0.60 (−0.63 to −0.57) | −0.18 (−0.68 to 0.33) | −0.77 (−1.28 to −0.26) |

Weighted by destination minutes:

| Source league | n | Move made by the league table | Error without the table | Error with the table |
|---|---|---|---|---|
| The Adriatic league | 131 | −0.68 (−0.69 to −0.67) | −0.73 (−1.35 to −0.10) | −1.41 (−2.04 to −0.78) |
| Israel | 49 | −0.37 (−0.38 to −0.35) | −0.17 (−0.90 to 0.56) | −0.54 (−1.27 to 0.19) |
| All arrivals | 180 | −0.59 (−0.62 to −0.55) | −0.57 (−1.04 to −0.09) | −1.15 (−1.63 to −0.68) |

## E29b: the arrivals of 2020-2025 (674 arrivals)

The same leagues, from the committed walk-forward forecasts. Each cell: mean in EFF/36 (95% interval).

Unweighted:

| Source league | n | Move made by the league table | Error without the table | Error with the table |
|---|---|---|---|---|
| The Adriatic league | 70 | −0.53 (−0.65 to −0.41) | +0.47 (−0.55 to 1.50) | −0.06 (−1.15 to 1.04) |
| Israel | 49 | −0.50 (−0.54 to −0.45) | +0.01 (−0.79 to 0.81) | −0.49 (−1.28 to 0.31) |
| All arrivals | 674 | −0.03 (−0.11 to 0.05) | −0.44 (−0.78 to −0.10) | −0.47 (−0.80 to −0.14) |

Weighted by destination minutes:

| Source league | n | Move made by the league table | Error without the table | Error with the table |
|---|---|---|---|---|
| The Adriatic league | 70 | −0.52 (−0.65 to −0.40) | +0.06 (−1.11 to 1.24) | −0.46 (−1.69 to 0.77) |
| Israel | 49 | −0.51 (−0.56 to −0.46) | −0.09 (−1.03 to 0.84) | −0.61 (−1.53 to 0.32) |
| All arrivals | 674 | +0.01 (−0.08 to 0.09) | −0.97 (−1.29 to −0.64) | −0.96 (−1.28 to −0.65) |

## E29c: the change between periods

| Source league | Weighting | n, older | n, 2020-2025 | Error without the table, older | Error without the table, 2020-2025 | Change (older minus 2020-2025) | 95% interval | df | Detectable with 80% power | Reading |
|---|---|---|---|---|---|---|---|---|---|---|
| The Adriatic league | Unweighted | 131 | 70 | −0.35 | +0.47 | −0.83 | −2.04 to 0.39 | 35 | 1.73 | includes zero |
| The Adriatic league | Weighted by destination minutes | 131 | 70 | −0.73 | +0.06 | −0.79 | −2.13 to 0.55 | 35 | 1.90 | includes zero |
| Israel | Unweighted | 49 | 49 | +0.30 | +0.01 | +0.29 | −0.75 to 1.33 | 30 | 1.48 | includes zero |
| Israel | Weighted by destination minutes | 49 | 49 | −0.17 | −0.09 | −0.08 | −1.26 to 1.11 | 30 | 1.68 | includes zero |

## Registered sentences

Each league on the older arrivals:

- The Adriatic league, unweighted: "on the older arrivals the league table lowered the forecast for arrivals from the Adriatic league by 0.68 EFF/36; without the table the forecast was 0.35 EFF/36 (interval -1.00 to 0.30) below what they delivered, and with it 1.04 (interval -1.69 to -0.38)".
- The Adriatic league, weighted by destination minutes: "on the older arrivals the league table lowered the forecast for arrivals from the Adriatic league by 0.68 EFF/36; without the table the forecast was 0.73 EFF/36 (interval -1.35 to -0.10) below what they delivered, and with it 1.41 (interval -2.04 to -0.78)".
- Israel, unweighted: "on the older arrivals the league table lowered the forecast for arrivals from Israel by 0.37 EFF/36; without the table the forecast was 0.30 EFF/36 (interval -0.36 to 0.96) above what they delivered, and with it 0.07 (interval -0.74 to 0.59) below".
- Israel, weighted by destination minutes: "on the older arrivals the league table lowered the forecast for arrivals from Israel by 0.37 EFF/36; without the table the forecast was 0.17 EFF/36 (interval -0.90 to 0.56) below what they delivered, and with it 0.54 (interval -1.27 to 0.19)".

The change between periods:

- The Adriatic league, unweighted: "for arrivals from the Adriatic league the change between the two periods is not distinguishable from zero at this n (-0.83 EFF/36, interval -2.04 to 0.39)".
- The Adriatic league, weighted by destination minutes: "for arrivals from the Adriatic league the change between the two periods is not distinguishable from zero at this n (-0.79 EFF/36, interval -2.13 to 0.55)".
- Israel, unweighted: "for arrivals from Israel the change between the two periods is not distinguishable from zero at this n (+0.29 EFF/36, interval -0.75 to 1.33)".
- Israel, weighted by destination minutes: "for arrivals from Israel the change between the two periods is not distinguishable from zero at this n (-0.08 EFF/36, interval -1.26 to 1.11)".

What the paper may add:

- The unweighted change between periods does not exclude zero for any league, so the registered condition is not met. The paper may not write "consistent with league numbers that change over time"; it says that the table shows where the forecast missed and not why. The change weighted by destination minutes does not exclude zero for any league either.
- Rule applied: may be written only if the change between periods excludes zero for at least one league; read on the unweighted change (the stricter reading: the weighted change cannot license it alone).
- The caveat that travels with every one of these sentences: "this shows where the forecast missed; it cannot separate a change in league strength from a change in which players clubs signed, in the data source or in the level of the forecasts".
- The paper does not write that a league was stronger or weaker in either period, and does not write 'because'.

Both versions of the older-seasons test were computed in this run. Everything that depends on the other version (V-all), including the rows of its extra league in both populations, is withheld, not for its result: ACB's written permission had not arrived (Amendment 7's permission rule). Nothing from it is in this note or in any committed file.

## Order of events

1. Amendment 11 was written on 16 November 2026, approved by Amir and pushed alone (commit `40f0d278b`) before any E29 code existed.
2. The generator and its unit tests (synthetic data) were written. Before the generator was committed it was run once on the staged inputs outside the retained-run machinery, to check that the gates execute. From that run only the gate records (status, largest difference, the number of arrivals per printed league), the output file and column names and the absence of withheld values in the public files were read; no mean, interval or change was read. The generator was not changed after it.
3. The generator was committed (commit `bdb945d1b`) and run once as retained run `research-runs/sloan-fullpaper/amend11-01` from the clean committed tree. The run finished with status complete; every gate passed and every negative control was rejected as required. No retained run of the generator failed and none was repeated.
4. No specification choice was made or changed after a result was seen. Every mean, interval and change the run produced for the printed version is in this note; standard errors are in the committed CSV tables.
5. This note is rendered by `scripts/report_sloan_fullpaper_amend11.py` from the committed outputs, in its own retained run.

## Reproduction

- Generator `scripts/sloan_fullpaper_amend11.py` (commit `bdb945d1b`, sha256 `189234664cdc7bf9…`), amendment commit `40f0d278b` (file sha256 `63d20a7dbf51b5bd…`), retained run `research-runs/sloan-fullpaper/amend11-01`, 15 input files, 2,577 code files, status complete.
- Inputs: the pinned v10 pairs and cohort (pool A), the committed scored rows and summary of the Amendment 7 scoring run, the Amendment 7 paper extract, the committed E28 summary, the committed Amendment 4 tables, the release flag, and the frozen older-season forecasts (sha256 `1d3e3bfb9d08b9d0…`). The run recorded 1 output file that is not committed: everything that depends on the older-seasons version the paper does not print, including the rows of its extra league in both populations, stays in the retained run (Amendment 7's permission rule); its file and hash are not committed.
