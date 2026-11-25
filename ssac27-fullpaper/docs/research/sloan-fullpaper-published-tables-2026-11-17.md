# SSAC27 full paper: Amendment 15 results (E31a, and the E31c freeze)

**EXPLORATORY.** Destination seasons 2020-2025 had been examined before any registration. Only the frozen 2026-27 test is confirmatory. Every number below is formatted by `scripts/report_sloan_fullpaper_published_tables.py` from the committed outputs of `scripts/sloan_fullpaper_published_tables.py`; none is typed.

Pre-registration: `docs/research/sloan-full-paper-preregistration-amendment-15-2026-11-17.md`, pushed alone before its generator existed.

## What E31a asks

The paper builds its own table of one number per league. A league table for the same leagues was printed in November 2015, before every season the paper scores. E31a asks what that outside table is worth inside the paper's own forecast, on the same 674 arrivals. One rule, fixed before any score: take the forecast that knows the destination but not the source league, and add one coefficient times the 2015 table's score of the source league. The coefficient is fitted without penalty, on earlier arrivals only, like every other forecast. The 2015 table was built for a different purpose: the level of competition a prospect faced, for the NBA draft.

## Results in plain words (exploratory)

- On the 674 arrivals, unweighted, adding the 2015 table to the destination-aware forecast lowered its error: +0.039 EFF/36 (interval 0.002 to 0.077; positive means the 2015 table lowers the error).
- On the 674 arrivals, weighted by destination minutes, adding the 2015 table to the destination-aware forecast changed its error by +0.036 EFF/36 (interval −0.010 to 0.082; positive means the 2015 table lowers the error), an interval that includes zero. The smallest difference this sample could detect with 80% power is 0.066.
- On the 674 arrivals, unweighted, the forecast with the 2015 table and the forecast with the paper's league numbers are not distinguishable: the difference in error is +0.026 EFF/36 (interval −0.008 to 0.060; positive means the 2015 table has the larger error), an interval that includes zero. The smallest difference this sample could detect with 80% power is 0.048.
- On the 674 arrivals, weighted by destination minutes, the forecast with the 2015 table and the forecast with the paper's league numbers are not distinguishable: the difference in error is +0.037 EFF/36 (interval −0.003 to 0.077; positive means the 2015 table has the larger error), an interval that includes zero. The smallest difference this sample could detect with 80% power is 0.057.

Both weightings are printed for every difference. This note does not choose which weighting a sentence of the paper follows.

## Open points

- **Not decided here; it goes to Amir before any writing:** the two weightings read differently for T_D; Amendment 15 does not say which weighting the registered sentence follows.
- In the line above, T_D is the destination-only forecast against the 2015 table, and T_O is the 2015 table against the paper's league numbers.

## Specification

| Field | Registered choice |
|---|---|
| Unit | One arrival: player × destination season. |
| Population | The 674 benchmark arrivals of 2020-2025 (v10 target keys, pool A). |
| Estimator | Paired differences in mean absolute error, EFF/36: MAE(history_destination_slope) - MAE(published_table_vashro_2015); MAE(published_table_vashro_2015) - MAE(source_ridge_10). Each unweighted and weighted by destination minutes. The published-table forecast: history_destination_slope plus one unpenalised coefficient times the published score of the source league, fitted walk-forward on the training arrivals of every other arm. |
| Null | Zero for each paired difference. |
| Filter | None beyond the population's registered rules. |
| Key | `player_name` × `season_dest`. |
| Uncertainty | Two-way clustered 95% interval (player, destination club-season), Student t with min(clusters) - 1 degrees of freedom. Detectable difference with 80% power: (t(0.975, df) + t(0.80, df)) x SE, the registered formula of the recipes track. |

## What had been seen

Before this run:
- the twelve values of the 2015 table, read on 17 November 2026 from the published article; its order agrees with Table 2 of the paper at the two ends and differs in the middle
- everything E31a uses on the 674 arrivals (outcomes, forecasts and errors of the registered arms), so E31a is exploratory

Not seen before this run:
- any correlation, error or forecast computed with the 2015 table
- any outcome of the frozen 2026-27 test or of the league changes of E30

## The 2015 table

The twelve values are in `docs/research/artifacts/sloan-fullpaper-published-tables-2026-11/vashro_2015_competition_scores.csv` (sha256 `2c004c88d10c60f68dabb038330a9f8d282ba87f56b521cb6a87c59a26252d04`), with the article's title, author, date and address in the folder's README. The run checked them against the values printed in Amendment 15. The years are the first and last year the article prints for each competition. The last year printed is 2016; how the article labels its seasons was not checked here.

| League key | Name as printed | Years as printed | Score | Use in E31 |
|---|---|---|---|---|
| `spain-acb` | Spanish ACB | 2002 to 2016 | 1.52 | source league |
| `italy-lba` | Italian Lega Basket Serie A | 2002 to 2016 | 1.12 | source league |
| `vtb` | VTB United League | 2012 to 2016 | 0.87 | source league |
| `aba-league` | Adriatic League Liga ABA | 2002 to 2016 | 0.82 | source league |
| `turkey-bsl` | Turkish BSL | 2012 to 2016 | 0.77 | source league |
| `france-pro-a` | French LNB Pro A | 2003 to 2016 | 0.69 | source league |
| `germany-bbl` | German BBL | 2012 to 2016 | 0.65 | source league |
| `israel-bsl` | Israeli BSL | 2012 to 2016 | 0.52 | source league |
| `greece-a1` | Greek HEBA A1 | 2002 to 2016 | 0.43 | source league |
| `lithuania-lkl` | Lithuanian LKL | 2012 to 2016 | 0.33 | source league |
| `euroleague` | Euroleague | 2002 to 2016 | 1.61 | destination competition; its score is not used |
| `eurocup` | Eurocup | 2003 to 2016 | 0.92 | destination competition; its score is not used |

## Gates

| Gate | Status | Largest difference | Negative control |
|---|---|---|---|
| G0 | passed | 1.3e-15 | rejected as required |
| G31a | passed | 0.0e+00 | rejected as required |
| scope | passed | n/a | rejected as required |
| table_pin | passed | 0.0e+00 | rejected as required |

G0 and the scope gate are the paper's standing checks. G31a ran before the published-table term was added: the registered errors of the destination-only and league-aware forecasts were reproduced to the printed digits and to 1e-09 against the committed summary, and this generator's own fit without the term equals the registered destination-only forecast on every arrival. Its control: the destination-only forecast column shifted by 0.01. The table-pin gate compares the 12 committed values with Amendment 15; its control moves one score.

**G31a's registered negative control.** With the ten source-league scores shuffled so that no league keeps its own (seed 20261117), the difference from the destination-only forecast was −0.009 (interval −0.020 to 0.003) unweighted and −0.010 (interval −0.024 to 0.003) weighted by destination minutes. Both intervals include zero, as the gate requires.

## E31a: the 674 benchmark arrivals (exploratory)

Mean absolute error of the three forecasts, EFF/36:

| Forecast | Arm | Unweighted | Weighted by destination minutes |
|---|---|---|---|
| Knows the destination, not the source league | `history_destination_slope` | 2.989 | 2.829 |
| The same, plus the 2015 table's score of the source league | `published_table_vashro_2015` | 2.950 | 2.793 |
| League-aware: the paper's one number per league | `source_ridge_10` | 2.924 | 2.756 |

Paired differences:

| Difference in MAE | Weighting | n | Difference, EFF/36 | 95% interval | Detectable with 80% power | Reading |
|---|---|---|---|---|---|---|
| Destination-only minus 2015 table (positive means the 2015 table lowers the error) | Unweighted | 674 | +0.039 | 0.002 to 0.077 | 0.054 | above zero |
| Destination-only minus 2015 table (positive means the 2015 table lowers the error) | Weighted by destination minutes | 674 | +0.036 | −0.010 to 0.082 | 0.066 | includes zero |
| 2015 table minus the paper's league numbers (positive means the 2015 table has the larger error) | Unweighted | 674 | +0.026 | −0.008 to 0.060 | 0.048 | includes zero |
| 2015 table minus the paper's league numbers (positive means the 2015 table has the larger error) | Weighted by destination minutes | 674 | +0.037 | −0.003 to 0.077 | 0.057 | includes zero |

Registered wording of Amendment 15, filled for each difference and each weighting:

- Destination-only minus 2015 table, unweighted: "a league table printed in 2015 improves a destination-aware forecast by 0.039 EFF/36 (interval 0.002 to 0.077)".
- Destination-only minus 2015 table, weighted by destination minutes: "a league table printed in 2015 adds nothing detectable to a destination-aware forecast (0.036, interval -0.010 to 0.082)".
- 2015 table minus the paper's league numbers, unweighted: "the paper's league numbers and a league table printed in 2015 are not distinguishable (0.026, interval -0.008 to 0.060; a difference of 0.048 would have been detected with 80% power)". "Not distinguishable" is not "the same": the detectable difference is stated beside it and no equivalence is claimed.
- 2015 table minus the paper's league numbers, weighted by destination minutes: "the paper's league numbers and a league table printed in 2015 are not distinguishable (0.037, interval -0.003 to 0.077; a difference of 0.057 would have been detected with 80% power)". "Not distinguishable" is not "the same": the detectable difference is stated beside it and no equivalence is claimed.

### The fitted coefficient

One coefficient per destination season, fitted on arrivals of earlier seasons. It is in EFF/36 per point of the 2015 score.

| Destination season | Training arrivals | Arrivals forecast | Coefficient |
|---|---|---|---|
| 2020 | 385 | 134 | +1.252 |
| 2021 | 519 | 101 | +1.255 |
| 2022 | 620 | 106 | +1.354 |
| 2023 | 726 | 102 | +1.615 |
| 2024 | 828 | 104 | +1.817 |
| 2025 | 932 | 127 | +1.773 |

## E31c: the same forecast, frozen for the 2026-27 test

The published-table forecast was fitted on the 1,059 arrivals through 2025, exactly as the frozen forecasts of 3 November were, and written for the same 3,478 rows as a second file. The pinned file was read and not rewritten. No 2026-27 statistic was read.

| Item | Value |
|---|---|
| File | `docs/research/artifacts/sloan-fullpaper-p1-freeze-2026-11/p1_frozen_published_table_forecasts.parquet` |
| sha256 | `4890fa1943a1e1ed40b0e3086a10274536aa315bf4eed8f4449d1815c98c8199` |
| Rows | 3,478 |
| Pinned frozen file (unchanged) | `docs/research/artifacts/sloan-fullpaper-p1-freeze-2026-11/p1_frozen_forecasts.parquet`, sha256 `f3530c1a5ac369c032a996756ced226a93aa2d9f71d2e63aab21694de3d55316` |
| Coefficient of the 2015 score | +1.610 |
| Retained run | `research-runs/sloan-fullpaper/e31c-freeze-01`, code commit `303953fe9`, status complete |

| Gate | Status | Largest difference | Negative control |
|---|---|---|---|
| G31b | passed | 0.0e+00 | rejected as required |
| frozen_arms | passed | 0.0e+00 | rejected as required |
| table_pin | passed | 0.0e+00 | rejected as required |

The frozen-arm gate refits three pinned frozen forecasts with the committed fitters on the same training arrivals and compares them on all 3,478 rows. G31b counts rows, keys and missing forecasts against the pinned file; its negative control flips one byte of the written file, and the hash check must refuse it. At scoring this file is read out beside the registered read-outs of Amendment 8: its error, and its paired differences from the destination-only and the league-aware forecasts. As for the second read-out of Amendment 8, no difference is expected to be detectable in November.

## Limits

- Every outcome E31a uses had been seen. The frozen 2026-27 test carries the same comparison (E31c), and the league changes of E30 carry a comparison of the two scales on equal terms (E31b).
- "Not distinguishable" is not "the same". The detectable difference is printed beside each interval, and no equivalence is claimed.
- The 2015 table enters through one fitted coefficient. That gives it its best single-number use inside the paper's own forecast; it does not test the table for the purpose it was built for.
- The two differences share the same arrivals and the same destination-aware forecast, so they are not independent pieces of evidence.

## Order of events

1. Amendment 15 was written on 17 November 2026, accepted by Amir and pushed alone (commit `48f752c68`) before any E31 code existed. It lists the twelve values of the 2015 table.
2. The generator was written and tested on a made-up league table and synthetic arrivals. Before it was committed, its reproduction gates were run on the real inputs outside the retained-run machinery, without any league table, to check that they execute: the registered errors and the pinned frozen forecasts were reproduced. No forecast, error or correlation was computed with the 2015 table before the retained run.
3. The file with the twelve published values was committed separately, after Amir approved that step. The generator reads it and refuses to run unless its values equal the values printed in Amendment 15.
4. The generator was run once on the 674 arrivals as retained run `research-runs/sloan-fullpaper/e31a-01` (code commit `303953fe9`). The run finished with status complete; every gate passed and every negative control was rejected as required. No retained run failed and none was repeated.
5. The forecasts and the four differences were then recomputed with separate code from the pinned inputs and the table file. They agree with the committed outputs.
6. No specification choice was made or changed after a result was seen. Every difference and interval the run produced is in this note; standard errors and p-values are in the committed CSV table.
7. This note is rendered by `scripts/report_sloan_fullpaper_published_tables.py` from the committed outputs, in its own retained run.

## Reproduction

- Generator `scripts/sloan_fullpaper_published_tables.py` (commit `303953fe9`, sha256 `70c6cbbbf82f147c…`), amendment commit `48f752c68` (file sha256 `f078841abdd37dbc…`), retained runs `research-runs/sloan-fullpaper/e31a-01` (E31a) and `research-runs/sloan-fullpaper/e31c-freeze-01` (E31c).
- Inputs: the pinned v10 pairs and cohort (pool A), the committed summary of the recipes run, the published table, and for E31c the pinned frozen file and its freeze record. Their sha256 values are in `docs/research/artifacts/sloan-fullpaper-published-tables-2026-11/generator-receipt.json` and `docs/research/artifacts/sloan-fullpaper-p1-freeze-2026-11/e31c-generator-receipt.json`.
- Outputs: `summary.json`, `e31a_differences.csv`, `e31a_coefficients.csv`, `e31a_keyed_forecasts.csv` in `docs/research/artifacts/sloan-fullpaper-published-tables-2026-11/`.
