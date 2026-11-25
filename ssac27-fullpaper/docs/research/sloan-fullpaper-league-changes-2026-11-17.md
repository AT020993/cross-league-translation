# SSAC27 full paper: the league table tested on players who changed domestic league (E30)

Pre-registration: `docs/research/sloan-full-paper-preregistration-2026-11-03.md`, Amendment 14 (`docs/research/sloan-full-paper-preregistration-amendment-14-2026-11-17.md`, sha256 `87471565393c01beb3ad4a5ce119fde74ac9d5c75fd96051944f16df5f476750`). E30 is a **registered** test: every rule, the code and the predictions were fixed before any rate after a league change was read.

**Status: scored.** The single scoring run read the frozen predictions by their sha256.

## Specification

| Field | Registered choice |
|---|---|
| Unit | One league change: a player's season t in domestic league A, followed by his season t+1 in a different domestic league B |
| Population | The ten source leagues of the paper. In each of the two seasons the player has at least 8 games and positive minutes in the league where he played the most minutes. Arrival seasons 2016 to 2025. 3,423 league changes by 1,649 players; every one of the 90 ordered league pairs holds at least 10 |
| Estimator | The slope of the unexplained change e on the change g that the league table predicts, by ordinary least squares over all league changes. e is the player's rate in league B minus the stayer forecast |
| Null | Slope zero. The registered direction is positive. A slope of one means the table has the right size |
| Filter | None beyond the population rules |
| Key | Proballers `player_name` × season |
| Uncertainty | 95% interval from a bootstrap that resamples players (2,000 draws) and refits the stayer forecast in every draw; and a permutation test that reassigns the ten table values among the ten leagues (10,000 draws) |

## Result

**Case: Clear.** Registered wording: "The league table, fitted only on first continental seasons, predicted what happened to 1,649 players who changed domestic league: slope 0.77 (95% interval 0.69 to 0.84), where 1 would mean the table's size is exactly right."

Size, registered wording: "about 0.77 of the size the table implies".

| Quantity | Value |
|---|---|
| League changes / players / stayer pairs | 3,423 / 1,649 / 9,057 |
| Primary slope b | 0.770 |
| 95% bootstrap interval | 0.692 to 0.844 |
| Bootstrap standard error | 0.039 |
| Permutation test: draws with a slope at least as large | 1 of 10,000 (p = 0.0001) |
| Slopes under random assignment of the ten values, middle 95% | −0.582 to 0.589 |
| Intercept of the line (mean unexplained change at g = 0) | +0.309 |
| Slope detectable with 80% power, 2.80 × bootstrap standard error (descriptive) | 0.109 |

## Secondary results

**S-a, error.** Mean absolute error of the stayer forecast on the league changers: 2.822 EFF/36. With the table's predicted change added: 2.694. Difference: +0.129 (interval 0.078 to 0.180); a positive difference means the table lowers the error.

**S-b, each league left out; S-c, each direction; S-d, the table's own uncertainty; S-e, sensitivities.**

| Result | What | League changes | Slope | 95% interval |
|---|---|---|---|---|
| primary | all league changes | 3,423 | 0.770 | 0.692 to 0.844 |
| S-b | without aba-league | 2,869 | 0.791 | 0.706 to 0.870 |
| S-b | without france-pro-a | 2,606 | 0.881 | 0.787 to 0.973 |
| S-b | without germany-bbl | 2,646 | 0.759 | 0.667 to 0.851 |
| S-b | without greece-a1 | 2,873 | 0.785 | 0.706 to 0.862 |
| S-b | without israel-bsl | 2,906 | 0.744 | 0.665 to 0.821 |
| S-b | without italy-lba | 2,614 | 0.793 | 0.702 to 0.876 |
| S-b | without lithuania-lkl | 3,021 | 0.724 | 0.643 to 0.807 |
| S-b | without spain-acb | 2,484 | 0.571 | 0.477 to 0.665 |
| S-b | without turkey-bsl | 2,519 | 0.801 | 0.718 to 0.880 |
| S-b | without vtb | 2,846 | 0.804 | 0.714 to 0.889 |
| S-c | moves to a higher equivalent (g > 0) | 1,609 | 0.826 | 0.619 to 1.039 |
| S-c | moves to a lower equivalent (g < 0) | 1,814 | 0.626 | 0.440 to 0.813 |
| S-d | the ten table values redrawn as well (approximation) | 3,423 | 0.770 | 0.434 to 0.930 |
| S-e (1) | without league changes where either season has a second domestic league with 8 or more games | 2,976 | 0.776 | 0.696 to 0.850 |
| S-e (2) | arrival seasons 2020 to 2025 only | 2,083 | 0.771 | 0.675 to 0.863 |
| S-e (3) | arrival seasons 2016 to 2024 only (four leagues' 2025-26 files stop in January 2026) | 3,093 | 0.786 | 0.704 to 0.864 |
| S-e (4) | the stayer forecast with one intercept per league of origin | 3,423 | 0.771 | 0.687 to 0.854 |
| S-e (5) | the EuroLeague equivalents in place of the EuroCup ones | 3,423 | 0.675 | 0.607 to 0.741 |
| S-e (6) | at least 15 games in both seasons | 2,265 | 0.759 | 0.679 to 0.841 |
| S-e (7) | arrival seasons 2020 to 2025, the table refitted only on arrivals before that season | 2,083 | 0.786 | 0.684 to 0.885 |
| S-e (8) | league pairs with fewer than 30 moves in the two directions together left out | 3,375 | 0.768 | 0.690 to 0.842 |

**S-c, mean unexplained change by direction.** Moves to a league with a higher equivalent: +1.346 EFF/36 (interval 1.158 to 1.533). Moves to a league with a lower equivalent: −0.755 (interval −0.940 to −0.566). The slope has the same sign in the two directions.

**S-d** is an approximation: each table value redrawn from a normal distribution with standard deviation (upper - lower) / 3.92 of its committed interval, independently; the committed files hold intervals and not the bootstrap draws. Redrawing the table adds noise to the predicted change, which pulls a slope towards zero, so this interval sits lower than the primary one.

**S-f, the picture.** The 45 points come from ten numbers and are not 45 independent tests. Half the difference between the two directions, per league pair, against the predicted change:

| Lower equivalent | Higher equivalent | Predicted change | Moves up | Moves down | Half difference |
|---|---|---|---|---|---|
| Spain | France | 0.11 | 50 | 90 | +1.13 |
| Spain | Italy | 0.65 | 56 | 66 | +1.42 |
| Spain | Greece | 1.11 | 43 | 33 | +1.88 |
| Spain | Turkey | 1.68 | 72 | 82 | +1.63 |
| Spain | Israel | 1.89 | 24 | 21 | +3.11 |
| Spain | Adriatic league | 2.27 | 48 | 55 | +2.18 |
| Spain | Germany | 2.69 | 54 | 81 | +2.68 |
| Spain | VTB United League | 2.74 | 37 | 50 | +2.62 |
| Spain | Lithuania | 2.79 | 37 | 40 | +2.96 |
| France | Italy | 0.55 | 49 | 64 | +0.07 |
| France | Greece | 1.00 | 35 | 33 | +0.22 |
| France | Turkey | 1.57 | 56 | 62 | +0.27 |
| France | Israel | 1.78 | 55 | 36 | +1.44 |
| France | Adriatic league | 2.16 | 33 | 29 | +0.03 |
| France | Germany | 2.58 | 47 | 77 | +1.43 |
| France | VTB United League | 2.64 | 30 | 33 | +1.07 |
| France | Lithuania | 2.68 | 18 | 20 | +3.00 |
| Italy | Greece | 0.46 | 37 | 30 | +0.48 |
| Italy | Turkey | 1.03 | 76 | 65 | −0.09 |
| Italy | Israel | 1.23 | 34 | 34 | +1.14 |
| Italy | Adriatic league | 1.61 | 35 | 27 | +0.88 |
| Italy | Germany | 2.04 | 47 | 66 | +1.58 |
| Italy | VTB United League | 2.09 | 38 | 46 | +1.25 |
| Italy | Lithuania | 2.13 | 15 | 24 | +1.66 |
| Greece | Turkey | 0.57 | 35 | 39 | −1.16 |
| Greece | Israel | 0.78 | 23 | 32 | +0.74 |
| Greece | Adriatic league | 1.16 | 30 | 27 | +0.59 |
| Greece | Germany | 1.58 | 30 | 30 | +0.80 |
| Greece | VTB United League | 1.63 | 23 | 28 | +0.47 |
| Greece | Lithuania | 1.68 | 18 | 24 | +1.61 |
| Turkey | Israel | 0.21 | 34 | 55 | +0.94 |
| Turkey | Adriatic league | 0.59 | 39 | 50 | +0.78 |
| Turkey | Germany | 1.01 | 34 | 62 | +1.28 |
| Turkey | VTB United League | 1.06 | 38 | 57 | +0.60 |
| Turkey | Lithuania | 1.11 | 22 | 26 | +0.94 |
| Israel | Adriatic league | 0.38 | 14 | 11 | −1.01 |
| Israel | Germany | 0.80 | 31 | 37 | +0.79 |
| Israel | VTB United League | 0.86 | 28 | 25 | +0.02 |
| Israel | Lithuania | 0.90 | 10 | 13 | +1.60 |
| Adriatic league | Germany | 0.42 | 34 | 32 | +0.53 |
| Adriatic league | VTB United League | 0.48 | 33 | 23 | −0.18 |
| Adriatic league | Lithuania | 0.52 | 17 | 17 | +1.36 |
| Germany | VTB United League | 0.05 | 32 | 19 | −0.92 |
| Germany | Lithuania | 0.10 | 37 | 27 | −0.15 |
| VTB United League | Lithuania | 0.04 | 21 | 16 | +1.08 |

## E31b: the 2015 published table on the same league changes (Amendment 15)

Scored league changes: 2,763 (arrival seasons from 2018). Registered wording: "not distinguishable".

| Forecast | Mean absolute error | 95% interval | Coefficient used for 2025 arrivals | 95% interval |
|---|---|---|---|---|
| Stayer forecast alone | 2.770 | 2.681 to 2.857 | n/a | n/a |
| Stayer forecast + the paper's equivalents | 2.625 | 2.542 to 2.707 | +0.774 | 0.692 to 0.853 |
| Stayer forecast + the 2015 table | 2.642 | 2.562 to 2.725 | −2.210 | −2.469 to −1.942 |

Error of the 2015 table minus error of the paper's equivalents: +0.016 EFF/36 (interval −0.021 to 0.054). "Not distinguishable" is not "the same".

## What is frozen

- `e30_frozen_league_changes.parquet`: 3,423 rows, one per league change. sha256 `2df696debc8567d9468844384c259e2289d6d1d985d7cbe4c7930bd7bf85b722`.
- `e30_stayer_pairs.parquet`: 9,057 pairs of seasons of players who stayed in their league, with their rate in the second season. sha256 `afdda9226c671e9ef774297097ad5507ed83a72d4d06d4a98cdc26f8fb0997b6`. The stayer forecast is fitted on this file.
- The frozen file holds no rate of any league changer in his destination season. The next season's rate is attached to stayers only.

| Column | Meaning |
|---|---|
| `player_name` | the key: the Proballers player name |
| `season_from` | season t, in league A (stored as the year the season starts) |
| `season_to` | season t+1, in league B |
| `league_from` | league A |
| `league_to` | league B |
| `games_from` | games in league A in season t |
| `minutes_from` | minutes in league A in season t |
| `x` | last season's rate: EFF/36 in league A in season t |
| `h_recorded` | career rate before season t (all earlier games on record); empty if there is none |
| `h` | the career rate used: h_recorded, or x where there is none |
| `a` | 1 if x is above h, else 0 |
| `g` | the change the league table predicts: EuroCup equivalent of B minus that of A |
| `stayer_forecast` | what the same season predicts for a player who stayed |
| `g_euroleague` | g with the EuroLeague equivalents (sensitivity 5) |
| `g_refit` | g with the table refitted only on arrivals before season t+1; arrivals of 2020 to 2025 (sensitivity 7) |
| `stayer_forecast_origin` | the stayer forecast with one intercept per league of origin (sensitivity 4) |
| `second_league` | true if either season has a second domestic league with 8 or more games (sensitivity 1) |
| `both_seasons_15_games` | true if both seasons have at least 15 games (sensitivity 6) |
| `pair_moves` | league changes between these two leagues, both directions together (sensitivity 8) |

**The stayer forecast** (ordinary least squares on the stayer pairs):

next season's rate = 4.012 + 0.653 × x + 0.109 × h − 0.836 × a, with a leftover spread of 3.44 EFF/36 (n = 9,057).

**The predicted change g** runs from −2.79 to 2.79 EFF/36 across the league changes, with a standard deviation of 1.57. No league change has g = 0.

**Counts** (all equal to the counts printed in Amendment 14):

| Quantity | Found | Registered |
|---|---|---|
| League changes | 3,423 | 3,423 |
| Stayer pairs | 9,057 | 9,057 |
| League changes arriving 2020 to 2025 | 2,083 | 2,083 |
| Ordered league pairs with at least one league change | 90 | 90 |
| Players who changed league at least once | 1,649 | 1,649 |
| League changes where either season has a second domestic league with 8+ games | 447 | 447 |

The smallest ordered league pair holds 10 league changes. 780 league changes have no earlier season on record, so h = x and a = 0 for them.

League changes by arrival season: 2016: 318, 2017: 342, 2018: 352, 2019: 328, 2020: 312, 2021: 360, 2022: 374, 2023: 363, 2024: 344, 2025: 330.

Rows behind each sensitivity that removes league changes: (1) 2,976; (2) 2,083; (3) 3,093; (6) 2,265; (7) 2,083; (8) 3,375.

## Which function produced each input

| Quantity | Produced by |
|---|---|
| Box scores | scripts/build_league_factors.py::load_player_games('proballers'), then add_usage |
| Games, minutes, EFF and EFF/36 per player, league and season | scripts/sloan_fullpaper_prospective.py::aggregates (the second return value of scripts/validate_translation_holdout.py::build_switchers) |
| x, last season's rate | scripts/sloan_fullpaper_prospective.py::source_player_seasons, column pir_per36_src |
| h, the career rate before it | scripts/sloan_fullpaper_prospective.py::source_player_seasons, column prior_mean_pir36; h := x where it is missing |
| a, the flag for a season above the career rate | scripts/sloan_fullpaper_prospective.py::source_player_seasons, column above_own_prior |
| The ten-league population | eligible_sources (this file) marks stints outside the ten leagues as not eligible before source_player_seasons is called; their games still count in h |
| g, the change the table predicts | league_table (this file) on the pinned exchange_rate_acb16.csv, column acb16_equivalent_eff36, rows with destination eurocup |
| The stayer forecast | fit_stayers (this file): ordinary least squares of next season's rate on intercept, x, h and a, on players who stayed |

## Gates and negative controls

| Gate | Result | Negative control |
|---|---|---|
| G17a readings fixed before the freeze | passed: the freeze record names Amendment 17 by its sha256 `d2072f085a0cbb3381cfde3eb72eac47adbdd7185948037b0a3aad9df84350ae`, and the freeze refuses to run on any other file | a changed byte in Amendment 17: rejected as required |
| G30a inputs | passed: 4 pinned files equal their sha256; 155 box-score files hashed | a changed byte: rejected as required |
| G30b same population | passed: 3,423 league changes and 9,057 stayer pairs, as registered | a games floor of 9 gives 3,291 and 8,813: rejected as required |
| G30c planted slope (made-up data) | passed: planted 1.0 came back as 0.987 (interval 0.962 to 1.012); planted 0.0 gave −0.013 (interval −0.038 to 0.012, includes zero) | league labels shuffled: +0.001 (interval −0.029 to 0.031, includes zero as required) |
| G30d no slope where none can exist | passed: a made-up change given at random to 9,057 stayer pairs gives +0.022 (interval −0.023 to 0.065) | the same change added to their rates gives 1.022 (interval 0.977 to 1.065, excludes zero as required) |
| G30e frozen before scored | passed: the scoring run read the file with sha256 `2df696debc8567d9468844384c259e2289d6d1d985d7cbe4c7930bd7bf85b722` | a changed byte: rejected as required |

G30c used 20,000 made-up players (15,987 made-up league changes, 43,386 made-up stayer pairs), seed 20261117, 2,000 bootstrap draws.

## Where the registration needed a reading

Each point below was handled in the way that changes least. None was chosen after an outcome was seen.

These readings, and the readings of the wording table, were then registered as Amendment 17 (`docs/research/sloan-full-paper-preregistration-amendment-17-2026-11-17.md`, sha256 `d2072f085a0cbb3381cfde3eb72eac47adbdd7185948037b0a3aad9df84350ae`), accepted by Amir and pushed alone before the freeze. The freeze record names that file (gate G17a).

1. **Which seasons count.** The amendment calls the population rule "the repository's source-season rule". That function, used as it is, lets a larger stint in Poland take the place of a stint in one of the ten leagues and then drops the player-season. It gives 3,381 league changes and 9,031 stayer pairs. The counts registered on 17 November (3,423 and 9,057) take the ten leagues first, and gate G30b fixes those counts. The generator follows the registered counts: a stint outside the ten leagues cannot be a source season, and its games still count in the career rate. 101 player-seasons are in the registered population and not in the function's own output; on the other 20,142 the two agree exactly on league, x, h and a.
2. **Which games feed the career rate h.** The amendment pins the box scores "of the ten leagues" and also says that h follows the paper's definition, all games on record in earlier seasons. The paper's definition includes continental games. The generator follows the definition: h uses every game the loader reads (14 competitions, the ten leagues plus Poland, the Champions League and the Proballers EuroLeague and EuroCup rows). All 155 files are hashed in the freeze record.
3. **Not the paper's corrected corpus.** The amendment fixes the key (the raw Proballers name) and the loader. The paper's 674 arrivals use a corrected corpus with official continental box scores and a name key that merges spellings. x, h and a here come from the same functions on the raw Proballers corpus.
4. **Gate G30c and the freeze.** The freeze code may compute no slope. G30c therefore runs in its own step (`gates`), on made-up players only, before the freeze; the freeze refuses to run without its passed record. The amendment does not fix the size or the noise of the made-up data. Both were fixed in the code, with one seed, before the first run: 20,000 made-up players, noise of player effect 1.0 and row noise 2.3 EFF/36.
5. **Where G30d runs.** G30d needs the real predicted changes and the stayers' rates, and it computes a slope. It runs at the start of the scoring run, before any outcome of a league changer is joined, and stops the run if it fails.
6. **Intervals.** Every interval comes from the one registered bootstrap (players resampled, the stayer forecast refitted in every draw; percentile limits). This includes the error difference S-a, which the amendment calls "clustered by player".
7. **Subsets keep the stayer forecast.** The leave-one-league-out slopes and sensitivities 1, 2, 3, 6 and 8 remove league changes only. The stayer forecast is still fitted on all stayers. Sensitivity 6 keeps league changes with at least 15 games in both seasons of the registered population; it does not re-select seasons with a floor of 15.
8. **S-d is one-sided by construction.** Redrawing the ten table values adds noise to the predicted change, and noise in a predictor pulls a slope towards zero. The S-d interval is therefore wider than the primary one and sits lower. It is printed as registered and labelled an approximation.
9. **N in the Clear sentence** is the number of players who changed league at least once (1,649), not the number of league changes (3,423).
10. **E31b.** Each scale's coefficient is fitted by least squares through the origin (the forecast is the stayer forecast plus one coefficient times the scale's difference, with no further constant), on league changes that arrived in earlier seasons.

## Limits stated in advance (Amendment 14)

- Players who change league are not a random sample. The stayer forecast removes only the drift that last season's rate, the career rate and the flag can explain. Age is not in these files.
- Minutes and role change with a move. EFF/36 is a rate, but it is not free of role.
- Players are linked across leagues by name. A wrong link joins two different players and pulls the slope towards zero.
- The table is fitted on players whom clubs sign into continental play. A league change is a different event.
- The table was fitted on arrivals of 2017 to 2025, the same years as most of the league changes. Sensitivity 7 uses only earlier arrivals.

## Order of events

1. Amendment 14 was written on 17 November 2026, accepted by Amir and pushed alone before any E30 code existed.
2. The generator was written and tested on made-up data only. Before it was committed, its freeze path was run on the staged inputs outside the retained-run machinery, to check that the gates execute; that path reads no rate after a league change. The analysis code was rehearsed on made-up outcomes only. Gate G30d was tried on the stayer pairs in the same way, with the registered seed and with other seeds to see that its interval behaves; it involves no league changer's outcome.
3. Gate G30c ran on made-up data as retained run `league-changes-gates-01` (generator commit `9eac352fd`, status complete).
4. Amendment 17, which registers the readings listed above, was accepted by Amir and pushed alone on 17 November 2026, before the freeze. The generator was then changed to pin it (gate G17a) and to carry its two added wordings; that change was tested on made-up data only.
5. The freeze ran as retained run `league-changes-freeze-01` (generator commit `bcbd24fe1`, status complete). It joined no outcome.
6. The single scoring run was retained run `league-changes-score-01` (generator commit `7b61a7807`, status complete). It read the frozen file by its sha256.
7. This note is rendered by `scripts/report_sloan_fullpaper_league_changes.py` from the committed outputs.

## Reproduction

- **Made-up gates:** `scripts/sloan_fullpaper_league_changes.py gates`, retained run `league-changes-gates-01`, generator commit `9eac352fdef540ca14f4215e629865299c33e3d7`, generator sha256 `a22cdb9d5da211e53f0a173333345ad277a7318e5c4d9b5124d2f9a4e6f79069`, 1 input files, source seasons 2015 to 2025.
  - `out/e30_made_up_gates.json`: `3c3754257d6abaa5199da0cd932dab2cd21198a164a18962c842cbfc9e889e28`
- **Freeze:** `scripts/sloan_fullpaper_league_changes.py freeze`, retained run `league-changes-freeze-01`, generator commit `bcbd24fe1cc81b1bea1a8a3a41d7e3ab6849d4b1`, generator sha256 `9939c2b943b60f7c5d24e31d5313e96176a9be028e66de2255ed26cc72fbdcc2`, 160 input files, source seasons 2015 to 2025.
  - `out/e30_freeze.json`: `93233c2b8b0765fa5309477763ab790684677f9ab92146eef5a3c10dc7429c56`
  - `out/e30_frozen_league_changes.parquet`: `2df696debc8567d9468844384c259e2289d6d1d985d7cbe4c7930bd7bf85b722`
  - `out/e30_stayer_pairs.parquet`: `afdda9226c671e9ef774297097ad5507ed83a72d4d06d4a98cdc26f8fb0997b6`
- **Score:** `scripts/sloan_fullpaper_league_changes.py score`, retained run `league-changes-score-01`, generator commit `7b61a780787bb7051153d6b1082f8c7292f9938a`, generator sha256 `9939c2b943b60f7c5d24e31d5313e96176a9be028e66de2255ed26cc72fbdcc2`, 167 input files, source seasons 2015 to 2025.
  - `out/e30_league_pairs.csv`: `61273e448d8e22bd45a8435cfca07af2d7475b33ebcfe2da9aa5706011c35740`
  - `out/e30_scored_league_changes.parquet`: `03d5355dd4c8127b9130dc2c7bfd7c9d782e14cca7c1e9bc83ac2fc0a9dbfaa4`
  - `out/e30_slopes.csv`: `f02c77c0285a77aa7e2a69cbf8bb4a86b771a7a3f0d999d08510ffb736d7861d`
  - `out/e30_summary.json`: `f1df4c23899c959fc7458caff0e5f2ec8ae071517b29be491a41383f946319dc`
  - `out/e31b_scales.csv`: `79d86dc802ed8b1b500a4d1a78ff309f58e4512ec5274dc5bd774866f33e09ab`
  - `out/s_f_league_pairs.csv`: `61273e448d8e22bd45a8435cfca07af2d7475b33ebcfe2da9aa5706011c35740`
  - `out/summary.json`: `738c800d81a697a1d44ef0398ea37f33c10c790205e2f6dca7e3e2ff9edcef47`
- Pinned inputs: `docs/research/sloan-full-paper-preregistration-amendment-14-2026-11-17.md` (`87471565393c…`); `docs/research/sloan-full-paper-preregistration-amendment-17-2026-11-17.md` (`d2072f085a0c…`); `docs/research/artifacts/sloan-fullpaper-amend1-decisions-2026-11/exchange_rate_acb16.csv` (`c8341a37947a…`); `docs/research/artifacts/sloan-fullpaper-amend3-2026-11/e19_equivalents_by_refit.csv` (`49814ea0b0a2…`). The sha256 of each of the 155 box-score files is in `e30_freeze.json`.
