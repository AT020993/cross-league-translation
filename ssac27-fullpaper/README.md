# SSAC 2027 full paper: companion

*European League Equivalents: One Number per League, Tested on League Changes It Was Never Fitted To* (Submission 47, Amir Tahori).

This folder holds what the full paper needs: the paper as rendered, its template and renderer,
the pre-registration and its 27 amendments, the results notes, every committed result file of the
full-paper analyses, the analysis code as run, and the derived tables the results are recomputed
from. It was cut from the private research repository at commit `d4ce6f536aa9e6b6fa3986f123f596b6fa1d6985`.

## Two tools you can use without reading the paper

* **Convert a league season.** Open `converter/index.html` in a browser. It holds the fitted
  equation, the ten league numbers and the guide to how far a gap between two forecasts can be
  trusted, with a small calculator. It is one file and makes no network request. Every number on
  it is read from the result files in this folder when the cut is made.
* **Score your own league adjustment.** Put one number per league in a CSV (`league,score`) and run
  `python ssac27-fullpaper/scripts/sloan_fullpaper_score_league_table.py --table my_leagues.csv`.
  It scores your numbers on the paper's 674 arrivals by the rule the paper registered for a
  published league table: one fitted coefficient added to the destination-aware forecast, compared
  with that forecast and with the paper's league-aware forecast. The 2015 table the paper scores is
  `docs/research/artifacts/sloan-fullpaper-published-tables-2026-11/vashro_2015_competition_scores.csv`;
  running the tool on it gives the paper's numbers. Scores on 2020-2025 are exploratory: those
  outcomes are public.

## Check the paper in one command

From the repository root, in a fresh Python 3.13 environment:

```sh
python -m venv .venv && source .venv/bin/activate
python -m pip install -r requirements.txt
python reproduce.py --section fullpaper
```

Allow about ten minutes on a recent laptop; the run makes no network request. (On 24 November
2026 two runs of a copy made before the scored render took 5.8 and 7.6 minutes on a 10-CPU Mac
for all three sections of the repository; both stopped before the last step, which redraws the
figures.)
Its last lines are one line per step, each `ok`, `FAILED` or `not run`, and then
`FULL-PAPER REPRODUCTION PASSED`. If a step fails, its message is printed once above that list
and in full in `ssac27-fullpaper/recomputed/report.json`; the steps after it do not run.
Two packages in `requirements.txt`, `requests` and `beautifulsoup4`, are imported only by three
scripts that fetched public pages when the research was done (`adjudicate_sloan_acb_sources.py`,
`sloan_alias_evidence.py`, `sloan_fullpaper_registration_list.py`); the reproduction does not
call them.

## Where each item of the paper comes from

| Item of the paper | Made by | From | Result file(s) | Check |
|---|---|---|---|---|
| Table of European League Equivalents (one number per league) | `scripts/sloan_fullpaper_amend1_decisions.py` (`exchange_table`) | the published v10 tables (`../ssac27-v10/data/`) and six pinned earlier results, which the reproduce script stages | `docs/research/artifacts/sloan-fullpaper-amend1-decisions-2026-11/exchange_rate_acb16.csv` | `python ssac27-fullpaper/scripts/reproduce_sloan_fullpaper_public.py --only equivalents` rebuilds it and prints its rows beside the committed ones (one to two minutes) |
| Figure `fig1_equivalents.png`: the Equivalents and their test on league changes | `scripts/sloan_fullpaper_paper_figures.py` (`fig_equivalents_and_moves`) | the Equivalents table, the arrivals per league, and the league pairs of the league-changes test | `docs/research/artifacts/sloan-fullpaper-amend1-decisions-2026-11/exchange_rate_acb16.csv`<br>`docs/research/artifacts/sloan-fullpaper-amend1-decisions-2026-11/e17_league_counts.csv`<br>`docs/research/artifacts/sloan-fullpaper-league-changes-2026-11/s_f_league_pairs.csv`<br>`docs/research/artifacts/sloan-fullpaper-league-changes-2026-11/summary.json` | the `figures` step of the full run draws it again and compares the file |
| Figure `fig4_bias.png`: where a forecast blind to the source league goes wrong | `scripts/sloan_fullpaper_paper_figures.py` (`fig_league_bias`) | the signed errors by league (E24, exploratory; carried, see below) | `docs/research/artifacts/sloan-fullpaper-amend4-2026-11/summary.json` | the `figures` step |
| Figure `fig_mechanism.png`: what translation adds once a forecast knows the leagues | `scripts/sloan_fullpaper_paper_figures.py` (`fig_mechanism`) | the forecast ladder (E1/E2) | `docs/research/artifacts/sloan-fullpaper-recipes-2026-11/summary.json` | the `recipes` step recomputes the ladder; the `figures` step redraws the figure |
| Figure `fig_frozen_test.png` (only once the frozen 2026-27 test is scored): its registered paired contrasts | `scripts/sloan_fullpaper_paper_figures.py` (`fig_frozen_test`) | the score record of the frozen test and the same contrasts on the arrivals of 2020-2025 | `docs/research/artifacts/sloan-fullpaper-p1-score-2026-11/score.json`<br>`docs/research/artifacts/sloan-fullpaper-recipes-2026-11/summary.json`<br>`docs/research/artifacts/sloan-fullpaper-amend9-2026-11/summary.json`<br>`docs/research/artifacts/sloan-fullpaper-published-tables-2026-11/summary.json` | the `figures` step; the score record is carried (scoring needs 2026-27 game files) |
| The test on league changes: the slope and its interval | `scripts/sloan_fullpaper_league_changes.py` | player-level league changes (not published); the slope is recomputed here from the 45 league pairs | `docs/research/artifacts/sloan-fullpaper-league-changes-2026-11/summary.json`<br>`docs/research/artifacts/sloan-fullpaper-league-changes-2026-11/e30_league_pairs.csv` | the `league changes` step recomputes the slope, and the slope without Spain, from the pair table |
| Any other number in the text | `scripts/render_sloan_fullpaper.py` | the committed result files | `docs/paper/ssac27/paper-numbers.json` | `paper-numbers.json` names, for every number, its line in the manuscript and the file and key it comes from; the `paper numbers` step re-reads each one |

## What is recomputed here and what is only hash-checked

A hash check shows that a file is the one the paper was written from. It does not show that the
result in it is right; only the rows marked **recomputed** do that.

| Analysis | Here | From what, or why not |
|---|---|---|
| G0, E1/E2: the submitted numbers, the forecast ladder, six translation recipes | **recomputed** | the published v10 tables |
| E7-E9: pairwise decisions, error bands, the league table | **recomputed** | the published v10 tables |
| E10-E12, E17 and the Equivalents table (Amendment 1) | **recomputed** | the published v10 tables and the results above |
| E14a-c: who the eight-game rule leaves out | **recomputed** | the 808-row tables of all arrivals |
| E15a-b: which skills travel | **recomputed** | the per-component tables of the 674 targets |
| The three vignettes | **recomputed** | the published v10 cohort table, the E16 forecasts and the Equivalents table |
| E27: the three comparisons of the older-seasons test | **recomputed** | the printed arrival rows |
| E30: the slope of the league-changes test, and the slope without Spain | **recomputed** | counts and mean residuals per league pair |
| E31a and E31c: the 2015 league table as a rival, and the second frozen forecast file | **recomputed** | the keyed forecasts and the pinned frozen file |
| The fitted equation: it gives back the Equivalents and the frozen 2026-27 forecasts (gate G30a) | **recomputed** | the committed coefficients and the committed forecasts |
| E3-E6: robustness (outcomes, destinations, seasons, ages, noise floor) | carried, hash-checked | needs per-game rows and ages, which are not published |
| E13, E25, E26: linkage and identity audits | carried, hash-checked | need birthdates and raw API rosters |
| E16: flexible models | carried, hash-checked | needs age features and game files |
| E18-E24 (Amendments 3 and 4; exploratory) | carried, hash-checked | their generator rebuilds season tables from raw game files, which are not published, so this script cannot re-run them |
| E27: freeze, linking and gates of the older-seasons test | carried, hash-checked | needs league-site box scores |
| E28, E29 (Amendments 9 and 11) | carried, hash-checked | need the older-season rows, which are not published |
| E30: the player-bootstrap intervals; E33 (Amendment 22; exploratory) | carried, hash-checked | need player-level league changes and stayer rows |
| E34 (Amendment 23, rule 5; exploratory): two published league scales on the older arrivals | carried, hash-checked | needs the older-season rows, which are not published |
| The 2026-27 freeze (rebuild from raw files) and its scoring | carried, hash-checked | need raw 2025-26 and 2026-27 game files; the frozen file is checked against the sha256 recorded at the freeze |

## The registrations

`../REGISTRATION_HASHES.md` lists the pre-registration, its amendments and the frozen forecast
files by file name and sha256. The files themselves are in this folder: the documents under
`docs/research/`, the frozen files under `docs/research/artifacts/`. To check every row:

```sh
python ssac27-fullpaper/scripts/reproduce_sloan_fullpaper_public.py --only registration
```

It finds each named file, compares its sha256 with the row and writes where each file is to
`ssac27-fullpaper/recomputed/report.json`. The heading of that list names the paper by the title
it had when the list was first published (16 November 2026); rows and notes of the list are only
ever added, never edited, so the heading stays. The paper's title was fixed later by a registered
rule (Amendment 16) and is the one at the top of this page. When each document was first public
is shown by the commit history of the list, not by this check.

## The steps of the full run

`ssac27-fullpaper/scripts/reproduce_sloan_fullpaper_public.py` does five things.

1. **Integrity.** Every file of this folder is checked against `../MANIFEST.json`.
2. **Recomputes** from the published player-season tables (no game rows) and compares with the
   committed results, file by file: the submitted v10 numbers (G0), the forecast ladder and the
   six translation recipes (E1/E2), the pairwise decisions, intervals and league table (E7-E9),
   cross-league pairs, bias by league, the career-year coefficient, the table completions and the
   ACB-16 exchange-rate table (E10-E12, E17), who the eight-game rule leaves out (E14a-c), which
   skills travel (E15a-b), the three vignettes, the 2015 published league table scored as a rival
   (E31a), and the second frozen forecast file built from it (E31c). Bootstrap intervals use the
   registered seeds. For the domestic league changes (E30), counts and mean residuals for each
   direction of each league pair reproduce the headline slope and the slope excluding Spain.
   The comparison uses a fitted intercept and weights each direction by its number of moves.
   The converter page is built again and must equal the one in this folder.
3. **Carries**, without recomputing, the analyses that need inputs this repository does not
   publish, and checks their files' hashes: E3-E6 (per-game splits; E5b uses ages), E13 (the
   linkage audit uses birthdates and raw API rosters), E16 (age features), and the 2026-27 freeze's
   rebuild from raw files. The frozen forecast file is checked against the hash recorded at the
   freeze (3 November 2026, 10:55 UTC). The E30 player-bootstrap intervals are checked against
   the retained slope table. Repeating that bootstrap requires player-level moves and stayer rows.
   E33 (Amendment 22; exploratory), which fits the stayer forecast only on earlier seasons,
   needs the same rows and is carried in the same way. E34 (Amendment 23; exploratory), two
   published league scales on the 180 older arrivals, needs the older-season rows and is carried.
4. **Checks every number in the paper.** The manuscript is composed again from the result files with
   the paper's own renderer and must match `docs/paper/ssac27/rendered/manuscript.md` byte for byte.
   `docs/paper/ssac27/paper-numbers.json` maps each number in the text to the file and key it comes
   from; each key is re-read. Numbers typed into the text (protocol constants such as the 2% margin,
   timestamps) are listed as constants.
5. **Checks the registrations.** Every row of `../REGISTRATION_HASHES.md` is checked against the
   file it names (see above).

The 2026-27 frozen test: scored once, and **inconclusive** by its registered rules (the field `status` of `score.json`; `pre-read.json` gives the reason). The score record is included and checked. The paper prints its values for the record and draws no conclusion from them; the files that exist only for a scored test (its figure and the tables of named newcomers) are not in this cut.

## Inputs

The v10 tables are read from `../ssac27-v10/data/` (unchanged since the abstract). The tables
added for the full paper are listed below with their row counts. Every table is a per-season
aggregate (one row per player-season, player-season pair or club-season); none is a game.

| file | rows | what it is |
|---|---:|---|
| `docs/research/artifacts/sloan-fullpaper-amend1-decisions-2026-11/e10_pair_types.csv` | 126 | committed result table |
| `docs/research/artifacts/sloan-fullpaper-amend1-decisions-2026-11/e10_pools.csv` | 12 | committed result table |
| `docs/research/artifacts/sloan-fullpaper-amend1-decisions-2026-11/e11_signed_error_by_league.csv` | 10 | committed result table |
| `docs/research/artifacts/sloan-fullpaper-amend1-decisions-2026-11/e12_career_year.csv` | 14 | committed result table |
| `docs/research/artifacts/sloan-fullpaper-amend1-decisions-2026-11/e17_league_counts.csv` | 10 | committed result table |
| `docs/research/artifacts/sloan-fullpaper-amend1-decisions-2026-11/e17_recipe_margins.csv` | 12 | committed result table |
| `docs/research/artifacts/sloan-fullpaper-amend1-decisions-2026-11/e17_reducible.csv` | 17 | committed result table |
| `docs/research/artifacts/sloan-fullpaper-amend1-decisions-2026-11/exchange_rate_acb16.csv` | 20 | committed result table |
| `docs/research/artifacts/sloan-fullpaper-amend11-2026-11/e29_change.csv` | 4 | committed result table |
| `docs/research/artifacts/sloan-fullpaper-amend11-2026-11/e29_means.csv` | 36 | committed result table |
| `docs/research/artifacts/sloan-fullpaper-amend3-2026-11/e18_drift.csv` | 18 | committed result table |
| `docs/research/artifacts/sloan-fullpaper-amend3-2026-11/e18_league_rebased.csv` | 10 | committed result table |
| `docs/research/artifacts/sloan-fullpaper-amend3-2026-11/e18_level.csv` | 27 | committed result table |
| `docs/research/artifacts/sloan-fullpaper-amend3-2026-11/e19_equivalents_by_refit.csv` | 140 | committed result table |
| `docs/research/artifacts/sloan-fullpaper-amend3-2026-11/e19_stability.csv` | 20 | committed result table |
| `docs/research/artifacts/sloan-fullpaper-amend3-2026-11/e19_tier_check.csv` | 144 | committed result table |
| `docs/research/artifacts/sloan-fullpaper-amend3-2026-11/e20_gap_bins.csv` | 36 | committed result table |
| `docs/research/artifacts/sloan-fullpaper-amend3-2026-11/e21_league_table_flips.csv` | 3 | committed result table |
| `docs/research/artifacts/sloan-fullpaper-amend3-2026-11/e22_coverage_by_league.csv` | 20 | committed result table |
| `docs/research/artifacts/sloan-fullpaper-amend3-2026-11/e23_refits.csv` | 6 | committed result table |
| `docs/research/artifacts/sloan-fullpaper-amend4-2026-11/e24_destination_mix.csv` | 10 | committed result table |
| `docs/research/artifacts/sloan-fullpaper-amend4-2026-11/e24_league_bias.csv` | 10 | committed result table |
| `docs/research/artifacts/sloan-fullpaper-amend4-2026-11/e24_level.csv` | 27 | committed result table |
| `docs/research/artifacts/sloan-fullpaper-amend9-2026-11/e28a_differences.csv` | 36 | committed result table |
| `docs/research/artifacts/sloan-fullpaper-amend9-2026-11/e28b_differences.csv` | 4 | committed result table |
| `docs/research/artifacts/sloan-fullpaper-amend9-2026-11/e28c_margin.csv` | 4 | committed result table |
| `docs/research/artifacts/sloan-fullpaper-arrivals-audit-2026-11/e26_arrivals.csv` | 674 | committed result table |
| `docs/research/artifacts/sloan-fullpaper-arrivals-audit-2026-11/e26_by_destination.csv` | 2 | committed result table |
| `docs/research/artifacts/sloan-fullpaper-arrivals-audit-2026-11/e26_by_league.csv` | 10 | committed result table |
| `docs/research/artifacts/sloan-fullpaper-arrivals-audit-2026-11/e26_by_season.csv` | 6 | committed result table |
| `docs/research/artifacts/sloan-fullpaper-arrivals-audit-2026-11/e26_comparisons.csv` | 12 | committed result table |
| `docs/research/artifacts/sloan-fullpaper-decisions-2026-11-03/e7_pools.csv` | 12 | committed result table |
| `docs/research/artifacts/sloan-fullpaper-decisions-2026-11-03/e8_conformal.csv` | 32 | committed result table |
| `docs/research/artifacts/sloan-fullpaper-decisions-2026-11-03/e9_league_tiers_club.csv` | 20 | committed result table |
| `docs/research/artifacts/sloan-fullpaper-decisions-2026-11-03/e9_league_tiers_full.csv` | 20 | committed result table |
| `docs/research/artifacts/sloan-fullpaper-flexible-2026-11/e16_club_win_share.csv` | 1,371 | source club-season domestic win share per arrival (E16) |
| `docs/research/artifacts/sloan-fullpaper-flexible-2026-11/e16_forecasts.csv` | 674 | 674 targets: E16 model forecasts (age column removed) |
| `docs/research/artifacts/sloan-fullpaper-flexible-2026-11/e16_models.csv` | 12 | committed result table |
| `docs/research/artifacts/sloan-fullpaper-league-changes-2026-11/e30_frozen_league_changes.parquet` | 3,423 | 3,423 changes of domestic league: the predictions frozen before any outcome was joined (E30, Amendment 14); no rate of the season after the change |
| `docs/research/artifacts/sloan-fullpaper-league-changes-2026-11/e30_league_pairs.csv` | 45 | the 45 league pairs of E30: predicted and observed change per pair |
| `docs/research/artifacts/sloan-fullpaper-league-changes-2026-11/e30_slopes.csv` | 22 | E30: the registered slope, its sensitivities and the leave-one-league-out slopes |
| `docs/research/artifacts/sloan-fullpaper-league-changes-2026-11/e31b_scales.csv` | 16 | E31b: the 2015 published table and the paper's table on the same league changes |
| `docs/research/artifacts/sloan-fullpaper-league-changes-2026-11/s_f_league_pairs.csv` | 45 | the league-pair table the paper prints (E30, read-out S-f) |
| `docs/research/artifacts/sloan-fullpaper-league-changes-chrono-2026-11/e33_by_season.csv` | 6 | E33: per arrival season, the league changes, the stayer rows the forecast was fitted on, the latest outcome season used and the fitted coefficients |
| `docs/research/artifacts/sloan-fullpaper-league-changes-chrono-2026-11/e33_slopes.csv` | 5 | E33 (Amendment 22, exploratory): the slope with the stayer forecast fitted only on earlier seasons, sensitivity (7) of E30 reproduced, their paired difference and the two slopes with season intercepts |
| `docs/research/artifacts/sloan-fullpaper-linkage-audit-2026-11/e13_audit_pairs.csv` | 100 | the 100 audited pairs: keys, classes, non-birthdate evidence |
| `docs/research/artifacts/sloan-fullpaper-linkage-audit-2026-11/e13_drawn_keys.csv` | 100 | committed result table |
| `docs/research/artifacts/sloan-fullpaper-linkage-audit-2026-11/e13_hand_review.csv` | 1 | committed result table |
| `docs/research/artifacts/sloan-fullpaper-linkage-audit-2026-11/e13_unresolved_evidence.csv` | 4 | committed result table |
| `docs/research/artifacts/sloan-fullpaper-linkage-audit-e25-2026-11/e25_audit_pairs.csv` | 300 | committed result table |
| `docs/research/artifacts/sloan-fullpaper-linkage-audit-e25-2026-11/e25_by_league.csv` | 10 | committed result table |
| `docs/research/artifacts/sloan-fullpaper-linkage-audit-e25-2026-11/e25_by_season.csv` | 10 | committed result table |
| `docs/research/artifacts/sloan-fullpaper-linkage-audit-e25-2026-11/e25_drawn_keys.csv` | 300 | committed result table |
| `docs/research/artifacts/sloan-fullpaper-linkage-audit-e25-2026-11/e25_hand_review.csv` | 0 | committed result table |
| `docs/research/artifacts/sloan-fullpaper-linkage-audit-e25-2026-11/e25_unresolved_evidence.csv` | 0 | committed result table |
| `docs/research/artifacts/sloan-fullpaper-older-seasons-paper-2026-11/e27_arrivals_printed.csv` | 180 | committed result table |
| `docs/research/artifacts/sloan-fullpaper-p1-freeze-2026-11/p1_frozen_forecasts.parquet` | 3,478 | the 2026-27 frozen forecasts (P1), unchanged |
| `docs/research/artifacts/sloan-fullpaper-p1-freeze-2026-11/p1_frozen_published_table_forecasts.parquet` | 3,478 | the same 2026-27 rows: the frozen forecast that uses the 2015 published league table (E31c, Amendment 15) |
| `docs/research/artifacts/sloan-fullpaper-p1-freeze-2026-11/p1_incumbency_2025_continental.parquet` | 656 | 2025-26 continental player-seasons used for the P1 incumbency rule |
| `docs/research/artifacts/sloan-fullpaper-p1-score-2026-11/p1_newcomer_ledger.csv` | 427 | committed result table |
| `docs/research/artifacts/sloan-fullpaper-p1-score-2026-11/p1_scored_rows.parquet` | 94 | committed result table |
| `docs/research/artifacts/sloan-fullpaper-p1-score-2026-11/p1_unjoined_newcomers.csv` | 106 | committed result table |
| `docs/research/artifacts/sloan-fullpaper-paper-v2-2026-11/vignettes.csv` | 3 | committed result table |
| `docs/research/artifacts/sloan-fullpaper-public-tables-2026-11/e15b_component_priors.parquet` | 674 | 674 targets: career rate before the source season, per component (E15b) |
| `docs/research/artifacts/sloan-fullpaper-public-tables-2026-11/e15b_split_halves.csv` | 674 | 674 targets: odd/even/full rates per box-score component (E15b reliabilities) |
| `docs/research/artifacts/sloan-fullpaper-public-tables-2026-11/e6_split_half_players.csv` | 674 | 674 targets: odd/even halves and minutes for the four outcomes (E6) |
| `docs/research/artifacts/sloan-fullpaper-public-tables-2026-11/e7_keyed_forecasts.csv` | 674 | 674 targets: four forecasts and the odd/even-game EFF/36 halves (E7, E10 ceiling) |
| `docs/research/artifacts/sloan-fullpaper-published-scales-older-2026-11/e34_readings.csv` | 24 | E34 (Amendment 23, exploratory): every reading of the two published league scales on the 180 older arrivals, by contrast, weighting and source league (no player rows) |
| `docs/research/artifacts/sloan-fullpaper-published-tables-2026-11/e31a_coefficients.csv` | 6 | committed result table |
| `docs/research/artifacts/sloan-fullpaper-published-tables-2026-11/e31a_differences.csv` | 4 | committed result table |
| `docs/research/artifacts/sloan-fullpaper-published-tables-2026-11/e31a_keyed_forecasts.csv` | 674 | 674 targets: destination-only, league-aware and 2015-table forecasts, with the outcome and destination minutes (E31a) |
| `docs/research/artifacts/sloan-fullpaper-published-tables-2026-11/vashro_2015_competition_scores.csv` | 12 | the twelve values of the league table printed in November 2015, with their source (not player data) |
| `docs/research/artifacts/sloan-fullpaper-recipes-2026-11/ladder.csv` | 528 | committed result table |
| `docs/research/artifacts/sloan-fullpaper-recipes-2026-11/metrics.csv` | 408 | committed result table |
| `docs/research/artifacts/sloan-fullpaper-recipes-2026-11/rows_pool_A.parquet` | 4,044 | 674 targets x 6 recipes: ladder forecasts (E1/E2) |
| `docs/research/artifacts/sloan-fullpaper-robustness-2026-11-03/headline_contrasts.csv` | 198 | committed result table |
| `docs/research/artifacts/sloan-fullpaper-skills-2026-11/e15a_licences.csv` | 39 | committed result table |
| `docs/research/artifacts/sloan-fullpaper-skills-2026-11/e15a_retention.csv` | 143 | committed result table |
| `docs/research/artifacts/sloan-fullpaper-skills-2026-11/e15b_carryover.csv` | 11 | committed result table |
| `docs/research/artifacts/sloan-fullpaper-skills-2026-11/e15b_source_offsets.csv` | 110 | committed result table |
| `docs/research/artifacts/sloan-fullpaper-skills-2026-11/skills_travel_figure.csv` | 11 | committed result table |
| `docs/research/artifacts/sloan-fullpaper-survivorship-2026-11/e14_contrasts.csv` | 70 | committed result table |
| `docs/research/artifacts/sloan-fullpaper-survivorship-2026-11/e14_eff_rows.parquet` | 808 | all 808 arrivals with >= 1 appearance: forecasts and outcome (E14b) |
| `docs/research/artifacts/sloan-fullpaper-survivorship-2026-11/e14_exclusions_by_band.csv` | 15 | committed result table |
| `docs/research/artifacts/sloan-fullpaper-survivorship-2026-11/e14a_counts.csv` | 39 | committed result table |
| `docs/research/artifacts/sloan-fullpaper-survivorship-2026-11/e14c_rotation_by_source.csv` | 10 | committed result table |
| `docs/research/artifacts/sloan-fullpaper-survivorship-2026-11/e14c_share_rows.parquet` | 808 | the same 808 arrivals: playing-time share forecasts (E14c) |
| `docs/research/artifacts/sloan-fullpaper-survivorship-2026-11/survivorship-01/g14_missing_anchor_stints.csv` | 2 | committed result table |

## What is not here, and why

* `docs/paper/ssac27/rendered/input-receipt.json`: the render run's receipt lists every private script path and local absolute paths; render-manifest.json carries the input and output hashes
* `docs/research/artifacts/sloan-fullpaper-paper-v2-2026-11/vignettes-generator-receipt.json`: the vignettes run's receipt lists private script and launchd job names, _local/ inputs and /private/tmp paths (Amir, 2026-11-11: leave it out); the vignettes' outputs and summary ship
* `scripts/templates/ssac27-word-template.docx`: the conference's Word template is not ours to redistribute; the text and figures are published, the .docx is built locally
* `data/raw/`: raw EuroLeague/EuroCup API files and Proballers game files (per-game rows)
* `data/processed/player_bio.parquet`: birthdates (first-party bio table)
* `e5b_ages.parquet / e5b_age_rows.parquet (robustness-02)`: continuous ages; E5b is carried from the committed summary
* `e16 age feature (age_c26)`: continuous age; removed from e16_forecasts.csv, E16 carried from the committed summary
* `e13 dob_cont / dob_dom and birthdates quoted in evidence text`: birthdates; the audit's keys, classes and non-birthdate evidence are published
* `e25 dob_cont / dob_dom and birthdates quoted in the E25 note`: birthdates; as for E13
* `docs/research/artifacts/sloan-fullpaper-older-seasons-2026-11/`: E27 (Amendment 7): the full outputs hold results and rows derived from ACB, which may not be published before ACB's written permission. What the paper prints ships instead, from sloan-fullpaper-older-seasons-paper-2026-11/ (made by scripts/sloan_fullpaper_older_seasons_paper.py under the permission flag in release.json)
* `docs/research/sloan-fullpaper-older-seasons-2026-11-13.md`: the E27 results note prints both versions, including the one with ACB
* `docs/research/artifacts/sloan-fullpaper-optionA-probe-2026-11/`: working notes of the 12 November feasibility probe for more source data (candidate sites, local paths, page dates); no result in the paper comes from it
* `docs/research/artifacts/sloan-fullpaper-arrivals-audit-2026-11/inputs/`: the EuroLeague/EuroCup API registration lists pinned by Amendment 6 (a raw API extract, like data/raw/); the E26 classes, the compared club strings and the summary ship, and Amendment 6 records the list's sha256
* `anchor/feature/row parquets left in retained runs (g0, robustness, survivorship e14 feature frames, p1 incumbency rebuild inputs)`: player-level working files the tracks deliberately did not commit
* `docs/research/artifacts/sloan-fullpaper-league-changes-2026-11/e30_scored_league_changes.parquet`: the scored rows of the league-changes test (E30): one row per change of domestic league (3,423 rows), with the player's name, his rates before the change and his rate after it; not released with this cut. The E30 results are in e30_summary.json, e30_slopes.csv and the league-pair tables, and the frozen predictions are in e30_frozen_league_changes.parquet
* `docs/research/artifacts/sloan-fullpaper-league-changes-2026-11/e30_stayer_pairs.parquet`: the stayer file of the league-changes test (E30): one row per pair of seasons of a player who stayed in his league (9,057 rows), with his name and his rate in both seasons; not released with this cut. e30_freeze.json records its sha256

10 files were changed on the way out; `REDACTIONS.json` lists each with both
hashes: an age column was removed from `e16_forecasts.csv`, the two birthdate columns from the
linkage-audit pair table, and birthdates quoted in text (the audit's evidence in two CSVs, its
results note, and one report string in `scripts/adjudicate_sloan_acb_sources.py`) were replaced
by `[birthdate withheld]`.

The Word file of the paper is built locally with the conference template, which is not ours to
share; the Markdown manuscript and the figures here are its content.

Code is MIT-licensed (`../LICENSE`); data terms are in `../DATA_TERMS.md`.
