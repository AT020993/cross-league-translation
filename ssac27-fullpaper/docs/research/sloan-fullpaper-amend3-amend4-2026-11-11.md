# SSAC27 full paper: Amendment 3 and 4 results (E18-E24)

**EXPLORATORY.** Destination seasons 2020-2025 had been examined before these analyses. Only the frozen 2026-27 test (P1) is confirmatory. Every number below is formatted by `scripts/report_sloan_fullpaper_amend3.py` from committed run outputs; every result sentence is the generator's registered wording.

Pre-registrations: `docs/research/sloan-full-paper-preregistration-amendment-3-2026-11-11.md` and `docs/research/sloan-full-paper-preregistration-amendment-4-2026-11-11.md`, each pushed alone before its generator existed.

## Specification

| Field | Registered choice |
|---|---|
| Unit | One forecast = player × destination season, one continental destination. E20 and E21 use pairs of forecasts within a pool. E23b's comparison uses domestic player-seasons. |
| Population | The 674 v10 target keys (2020-2025), pool A, recipe R1. E19 and E23 also use the 1,059 e9 training arrivals and the six walk-forward training sets. E22 uses the E8 test seasons 2021-2025. |
| Estimator | E18, E24: mean signed error, overall and re-based by source league; spread of league biases. E19: the ACB-16 equivalent per league and refit. E20: share of pairs ordered correctly by forecast-gap bin. E21: flip share and right share. E22: band coverage by league. E23: coefficient on the jump above history; share of arrivals flagged. |
| Null | Signed error = 0; re-based bias = 0; spread contrast = 0; right share = 0.5; coverage = nominal; coefficient = 0; paired MAE difference = 0. E19 and E20 are descriptive. |
| Filter | v10 eligibility; targets fixed before scoring. |
| Key | `player_name` × `season_dest`; pools = destination competition × destination season. |
| Uncertainty | Cluster bootstrap over destination club-seasons, 2,000 draws, seed 0; two-way clustered intervals for paired MAE contrasts; Wilson 95% intervals for coverage by league; Holm across the 10 leagues. |

## What had been seen

Before Amendment 3 was registered:
- mean signed error on the 674 for history-only and offsets l10, with intervals
- offsets l10 signed error by destination and by season; history-only by season
- the registered E11 signed errors by league and arithmetic on them
- all-pairs flip share and right share of offsets l10 against history-only
- the registered E8 coverage by season
- the distribution of forecast gaps under offsets l10 (no outcome used)

After Amendment 3 was registered and before its run:
- the count of above-own-history flags on the 674 targets (359 of 582 with a history), printed while loading the inputs during implementation

Before Amendment 4 was registered:
- every Amendment 3 result, including history-only and league-aware signed errors overall, by destination, by season and by source league, and their spreads
- the registered MAE of the destination-aware forecast on the 674

## Gates

Amendment 3 run:

| Gate | Status | Largest difference | Negative control |
|---|---|---|---|
| E19_tiers | passed | n/a | n/a |
| E23_jump_matches_flag | passed | n/a | rejected as required |
| E23b_arrivals_in_population | passed | n/a | rejected as required |
| G0 | passed | 1.3e-15 | rejected as required |
| G18 | passed | 2.2e-16 | rejected as required |
| G19 | passed | 3.6e-15 | rejected as required |
| G20 | passed | 0.0e+00 | rejected as required |
| G21 | passed | 5.8e-17 | rejected as required |
| G22 | passed | 0.0e+00 | rejected as required |
| G23 | passed | 0.0e+00 | rejected as required |
| prior_rule | passed | n/a | rejected as required |
| reproduction | passed | 3.6e-15 | rejected as required |
| scope | passed | n/a | rejected as required |

Amendment 4 run:

| Gate | Status | Largest difference | Negative control |
|---|---|---|---|
| G0 | passed | 1.3e-15 | rejected as required |
| G24a | passed | 2.2e-16 | rejected as required |
| G24b | passed | 0.0e+00 | rejected as required |
| reproduction | passed | 3.6e-15 | rejected as required |
| scope | passed | n/a | rejected as required |

## E18 and E24a. The level of the forecasts

Mean signed error, forecast minus actual EFF/36, with 95% cluster-bootstrap intervals. Below zero, the forecast expected less than arrivals delivered.

| Forecast | All arrivals | EuroLeague | EuroCup | Destination season 2025 |
|---|---|---|---|---|
| History only (blind to both leagues) | -0.37 (-0.69 to -0.05) | +1.24 (0.76 to 1.71) | -1.02 (-1.45 to -0.65) | -1.24 (-1.92 to -0.63) |
| History + translation | -0.56 (-0.86 to -0.27) | -0.21 (-0.70 to 0.26) | -0.70 (-1.08 to -0.36) | -1.49 (-2.14 to -0.90) |
| History + destination (blind to the source league) | -0.44 (-0.76 to -0.14) | -0.04 (-0.53 to 0.45) | -0.61 (-1.02 to -0.24) | -1.37 (-2.03 to -0.78) |
| League-aware (one number per league) | -0.47 (-0.78 to -0.18) | -0.03 (-0.51 to 0.44) | -0.65 (-1.04 to -0.30) | -1.43 (-2.09 to -0.82) |

- On average the history forecast is 0.37 EFF/36 below what arrivals delivered.
- On average the history + translation forecast is 0.56 EFF/36 below what arrivals delivered.
- On average the offsets λ10 forecast is 0.47 EFF/36 below what arrivals delivered.

League-aware forecast by destination season:

| Destination season | Arrivals | Mean signed error (95% interval) |
|---|---|---|
| 2020 | 134 | +0.01 (-0.64 to 0.64) |
| 2021 | 101 | +0.21 (-0.48 to 0.94) |
| 2022 | 106 | -0.85 (-1.45 to -0.19) |
| 2023 | 102 | -0.58 (-1.73 to 0.43) |
| 2024 | 104 | -0.10 (-0.86 to 0.57) |
| 2025 | 127 | -1.43 (-2.09 to -0.82) |

### E18c. Continental EFF/36 by competition and season (descriptive)

"Minus earlier seasons" compares a season with the mean of all earlier seasons from 2017, the level a walk-forward refit had seen. This table licenses description only, and no statement about cause.

| Competition | Season | Arrivals | Arrivals: mean | minus earlier seasons | All player-seasons with 8+ games | All: mean | minus earlier seasons |
|---|---|---|---|---|---|---|---|
| eurocup | 2017 | 108 | 14.64 | n/a | 253 | 14.80 | n/a |
| eurocup | 2018 | 81 | 14.66 | +0.02 | 255 | 14.89 | +0.08 |
| eurocup | 2019 | 114 | 14.51 | -0.13 | 247 | 14.75 | -0.09 |
| eurocup | 2020 | 96 | 15.03 | +0.44 | 247 | 14.85 | +0.04 |
| eurocup | 2021 | 66 | 14.71 | +0.01 | 231 | 15.17 | +0.34 |
| eurocup | 2022 | 79 | 15.62 | +0.92 | 230 | 15.51 | +0.62 |
| eurocup | 2023 | 73 | 15.39 | +0.56 | 233 | 15.56 | +0.58 |
| eurocup | 2024 | 77 | 15.45 | +0.55 | 230 | 15.41 | +0.34 |
| eurocup | 2025 | 89 | 16.14 | +1.18 | 240 | 15.38 | +0.27 |
| euroleague | 2017 | 31 | 14.58 | n/a | 219 | 14.90 | n/a |
| euroleague | 2018 | 27 | 14.53 | -0.06 | 214 | 15.26 | +0.36 |
| euroleague | 2019 | 24 | 15.06 | +0.51 | 242 | 14.82 | -0.25 |
| euroleague | 2020 | 38 | 12.77 | -1.94 | 257 | 14.54 | -0.45 |
| euroleague | 2021 | 35 | 14.09 | +0.00 | 247 | 14.07 | -0.79 |
| euroleague | 2022 | 27 | 14.46 | +0.37 | 246 | 15.05 | +0.35 |
| euroleague | 2023 | 29 | 14.34 | +0.19 | 252 | 15.15 | +0.40 |
| euroleague | 2024 | 27 | 14.96 | +0.78 | 252 | 15.69 | +0.87 |
| euroleague | 2025 | 38 | 15.87 | +1.61 | 291 | 16.07 | +1.13 |

## E18b and E24. League biases measured against the average arrival

Each league's mean signed error minus the mean signed error of all 674 arrivals, computed inside every bootstrap draw. Holm-adjusted p-values are across the 10 leagues, separately for the history-only forecast (E18b) and the destination-aware forecast (E24b).

| Source league | Arrivals | Share to EuroLeague | History only | Holm p | History + destination | Holm p | League-aware |
|---|---|---|---|---|---|---|---|
| France (Pro A) | 70 | 24% | -1.17 (-2.17 to -0.17) | 0.162 | -1.11 (-2.10 to -0.17) | 0.150 | -0.19 (-1.17 to 0.75) |
| Italy (LBA) | 77 | 25% | -1.11 (-1.73 to -0.47) | 0.020 | -1.04 (-1.70 to -0.41) | 0.036 | -0.66 (-1.31 to -0.04) |
| Spain (ACB) | 108 | 41% | -0.93 (-1.64 to -0.22) | 0.063 | -1.17 (-1.84 to -0.53) | 0.010 | -0.17 (-0.83 to 0.46) |
| Greece (A1) | 30 | 13% | -0.46 (-1.66 to 0.70) | 1.000 | -0.24 (-1.46 to 0.86) | 0.723 | +0.01 (-1.14 to 1.14) |
| Turkey (BSL) | 108 | 29% | +0.34 (-0.35 to 1.06) | 1.000 | +0.33 (-0.37 to 1.01) | 0.723 | +0.21 (-0.48 to 0.88) |
| Israel (Winner League) | 49 | 29% | +0.40 (-0.46 to 1.27) | 1.000 | +0.45 (-0.31 to 1.21) | 0.723 | -0.02 (-0.78 to 0.72) |
| Germany (BBL) | 87 | 25% | +0.81 (0.14 to 1.58) | 0.133 | +0.91 (0.26 to 1.60) | 0.048 | +0.04 (-0.59 to 0.72) |
| Adriatic (ABA) | 70 | 27% | +0.85 (-0.28 to 1.74) | 0.496 | +0.92 (-0.10 to 1.73) | 0.280 | +0.42 (-0.67 to 1.27) |
| Lithuania (LKL) | 48 | 17% | +0.87 (0.07 to 1.78) | 0.170 | +1.05 (0.19 to 1.95) | 0.126 | +0.20 (-0.70 to 1.15) |
| VTB United League | 27 | 59% | +2.03 (0.62 to 3.38) | 0.064 | +1.48 (0.07 to 2.79) | 0.175 | +0.67 (-0.75 to 2.03) |

Licensed league sentences:

- Measured against the average arrival, a league-blind forecast underrates arrivals from italy-lba by 1.11 EFF/36.
- Measured against the average arrival, a forecast that knows the destination but not the source league overrates arrivals from germany-bbl by 0.91 EFF/36.
- Measured against the average arrival, a forecast that knows the destination but not the source league underrates arrivals from italy-lba by 1.04 EFF/36.
- Measured against the average arrival, a forecast that knows the destination but not the source league underrates arrivals from spain-acb by 1.17 EFF/36.

Spread of the league biases (arrival-weighted root mean square of the 10 re-based biases; inflated by sampling noise in every arm, so the contrasts are read, not the levels):

| Forecast | Spread | 95% interval |
|---|---|---|
| History only (blind to both leagues) | 0.92 | 0.71 to 1.28 |
| History + destination (blind to the source league) | 0.93 | 0.75 to 1.27 |
| League-aware (one number per league) | 0.32 | 0.29 to 0.75 |

| Contrast | Difference | 95% interval | Detectable at 80% power | Registered verdict |
|---|---|---|---|---|
| E18: history only minus league-aware | 0.59 | 0.28 to 0.65 | 0.26 | The league table flattens the league pattern. |
| E24 primary: history + destination minus league-aware | 0.61 | 0.29 to 0.63 | 0.24 | Once the forecast knows the destination, the league table still flattens the league pattern. |
| E24 secondary: history only minus history + destination | -0.01 | -0.10 to 0.08 | 0.13 | Knowing the destination alone does not detectably flatten the league pattern at this n. |

## E19. Stability of the European League Equivalents across the yearly refits

- In every yearly refit, every tier-3 league needed a higher domestic rate than every tier-1 league. (144 of 144 comparisons; 144 of 144 without cells under 10 training arrivals.)
- From one summer to the next a league's equivalent moved by a median of 0.25 EFF/36 (at most 1.10).
- The refits share most of their training data. This describes stability and is not a test.

Equivalent of an ACB 16, euroleague arrivals:

| Source league | refit for 2020 | refit for 2021 | refit for 2022 | refit for 2023 | refit for 2024 | refit for 2025 | full fit through 2025 |
|---|---|---|---|---|---|---|---|
| Spain (ACB) | 16.0 | 16.0 | 16.0 | 16.0 | 16.0 | 16.0 | 16.0 |
| France (Pro A) | 15.5 | 15.9 | 16.4 | 16.6 | 16.5 | 16.5 | 16.1 |
| Italy (LBA) | 16.5 | 16.6 | 17.0 | 17.6 | 17.5 | 17.1 | 16.7 |
| Greece (A1) | 16.6 | 16.8 | 17.0 | 17.4 | 17.7 | 17.6 | 17.3 |
| Turkey (BSL) | 17.1 | 17.1 | 17.7 | 18.2 | 18.4 | 18.3 | 17.9 |
| Israel (Winner League) | 17.6 | 18.1 | 18.1 | 18.6 | 18.8 | 18.5 | 18.2 |
| Adriatic (ABA) | 17.1 | 18.2 | 18.7 | 18.8 | 19.0 | 19.0 | 18.6 |
| Germany (BBL) | 18.2 | 18.4 | 18.7 | 19.4 | 19.6 | 19.4 | 19.1 |
| VTB United League | 17.6 | 18.6 | 19.1 | 19.7 | 19.8 | 19.7 | 19.1 |
| Lithuania (LKL) | 18.6 | 18.1 | 18.3 | 19.0 | 19.7 | 19.5 | 19.2 |

Equivalent of an ACB 16, eurocup arrivals:

| Source league | refit for 2020 | refit for 2021 | refit for 2022 | refit for 2023 | refit for 2024 | refit for 2025 | full fit through 2025 |
|---|---|---|---|---|---|---|---|
| Spain (ACB) | 16.0 | 16.0 | 16.0 | 16.0 | 16.0 | 16.0 | 16.0 |
| France (Pro A) | 15.5 | 15.9 | 16.4 | 16.6 | 16.4 | 16.5 | 16.1 |
| Italy (LBA) | 16.5 | 16.6 | 16.9 | 17.4 | 17.2 | 16.9 | 16.7 |
| Greece (A1) | 16.6 | 16.8 | 16.9 | 17.2 | 17.4 | 17.4 | 17.1 |
| Turkey (BSL) | 17.1 | 17.1 | 17.5 | 17.9 | 18.0 | 18.0 | 17.7 |
| Israel (Winner League) | 17.7 | 18.1 | 18.0 | 18.3 | 18.3 | 18.1 | 17.9 |
| Adriatic (ABA) | 17.1 | 18.2 | 18.4 | 18.4 | 18.5 | 18.6 | 18.3 |
| Germany (BBL) | 18.2 | 18.4 | 18.5 | 18.9 | 19.0 | 18.9 | 18.7 |
| VTB United League | 17.6 | 18.6 | 18.8 | 19.2 | 19.1 | 19.1 | 18.7 |
| Lithuania (LKL) | 18.6 | 18.0 | 18.1 | 18.6 | 19.1 | 19.0 | 18.8 |

## E20. How large a forecast gap can be trusted

Share of pairs (same competition and season) in which the arrival with the higher forecast had the higher realised EFF/36, by the size of the gap between the two forecasts.

| Forecast gap, EFF/36 | Pairs | League-aware forecast: right (95% interval) | Cross-league pairs only | History-only forecast |
|---|---|---|---|---|
| 0 to 1 | 4,296 | 54.5% (52.0% to 56.7%) | 54.6% (3,751 pairs) | 55.2% (4,642 pairs) |
| 1 to 2 | 4,033 | 63.0% (60.5% to 66.0%) | 63.3% (3,500 pairs) | 62.6% (4,378 pairs) |
| 2 to 3 | 3,588 | 70.9% (68.2% to 74.8%) | 71.4% (3,144 pairs) | 70.8% (3,802 pairs) |
| 3 to 4 | 2,955 | 78.0% (74.6% to 81.4%) | 78.8% (2,598 pairs) | 77.7% (3,024 pairs) |
| 4 to 6 | 4,030 | 85.1% (82.1% to 88.3%) | 85.2% (3,563 pairs) | 85.2% (3,789 pairs) |
| 6 or more | 3,463 | 93.3% (90.4% to 95.9%) | 93.3% (3,112 pairs) | 93.8% (2,730 pairs) |

- Forecast gaps of at least 1 EFF/36 were right at least 60% of the time.
- Forecast gaps of at least 3 EFF/36 were right at least 70% of the time.
- Even forecast gaps below 1 EFF/36 were right more often than a coin flip (54.5%).

## E21. How often the league table changes a ranking

| Pairs | Number | Orderings the league table changes | Changes that were right (95% interval) |
|---|---|---|---|
| All pairs | 22,365 | 7.6% | 57.6% (52.3% to 63.0%) |
| Different source leagues | 19,668 | 8.5% | 57.7% (52.4% to 63.1%) |
| Same source league | 2,697 | 1.0% | 51.9% (20.0% to 83.9%) |

- The league table changes 8.5% of cross-league comparisons and is right on 57.7% of them.
- Note: E21 re-expresses E10's gain (gain = flip share x (2 x right share - 1)); it adds no new evidence.

## E22. Error-band coverage by source league

Registered E8 walk-forward conformal bands for the league-aware forecast, test seasons 2021-2025, with Wilson 95% intervals.

| Source league | Arrivals | 80% bands: coverage | 95% bands: coverage |
|---|---|---|---|
| France (Pro A) | 50 | 76.0% (62.6% to 85.7%) | 90.0% (78.6% to 95.7%) |
| Spain (ACB) | 88 | 78.4% (68.7% to 85.7%) | 93.2% (85.9% to 96.8%) |
| Lithuania (LKL) | 39 | 79.5% (64.5% to 89.2%) | 100.0% (91.0% to 100.0%) |
| Turkey (BSL) | 86 | 80.2% (70.6% to 87.3%) | 94.2% (87.1% to 97.5%) |
| Adriatic (ABA) | 49 | 81.6% (68.6% to 90.0%) | 95.9% (86.3% to 98.9%) |
| Italy (LBA) | 66 | 84.8% (74.3% to 91.6%) | 93.9% (85.4% to 97.6%) |
| VTB United League | 14 | 85.7% (60.1% to 96.0%) | 100.0% (78.5% to 100.0%) |
| Germany (BBL) | 79 | 86.1% (76.8% to 92.0%) | 97.5% (91.2% to 99.3%) |
| Israel (Winner League) | 44 | 90.9% (78.8% to 96.4%) | 97.7% (88.2% to 99.6%) |
| Greece (A1) | 25 | 92.0% (75.0% to 97.8%) | 96.0% (80.5% to 99.3%) |

- By source league, the 80% bands contained between 76.0% and 92.0% of arrivals.
- No league's coverage was distinguishable from 80% at these sample sizes (n from 14 to 88).
- 80% coverage by destination season: 2021: 89.1% (n = 101), 2022: 82.1% (n = 106), 2023: 79.4% (n = 102), 2024: 90.4% (n = 104), 2025: 74.0% (n = 127).

## E23. The above-average-season discount

M0 is the registered league-aware model (a flag for a source season above the player's earlier career rate). M1 adds the size of the jump, u = max(0, source rate minus earlier career rate). M2 replaces the flag with the jump. M0 stays the paper's model whatever is shown here.

| Coefficient | Full fit through 2025 | 95% interval | Six walk-forward refits |
|---|---|---|---|
| M0, flag | -1.39 | registered in E12 | registered in E12 |
| M1, flag | -1.27 | -1.83 to -0.63 | -1.37, -1.23, -1.01, -1.25, -1.34, -1.39 |
| M1, jump (per EFF/36 above history) | +0.232 | 0.066 to 0.405 | +0.17, +0.17, +0.15, +0.20, +0.36, +0.26 |
| M2, jump (per EFF/36 above history) | +0.282 | 0.097 to 0.461 | +0.21, +0.20, +0.20, +0.24, +0.40, +0.31 |

| Variant | Walk-forward MAE on the 674 | M0 | M0 minus variant (95% interval) |
|---|---|---|---|
| M1 | 2.909 | 2.924 | +0.015 (-0.013 to 0.044) |
| M2 | 2.905 | 2.924 | +0.019 (-0.033 to 0.071) |

- Registered verdict: The data do not show the discount growing with the size of the jump.
- The M1 jump coefficient is negative in 0 of 6 refits.
- Among the 561 flagged training arrivals the median jump is 2.76 EFF/36 (90th percentile 6.77).

### E23b. How common such signings are

| Population | Player-seasons | Share after an above-average season (95% interval) |
|---|---|---|
| Training arrivals with a history | 895 | 62.7% (59.4% to 65.9%) |
| All comparable domestic player-seasons | 13,825 | 53.1% (52.2% to 54.0%) |

- Difference: 9.6 percentage points (6.2 to 13.0).
- 63% of signings followed an above-average season, against 53% of all comparable domestic player-seasons.
- Comparison population: source seasons 2016-2024, 4,068 players; players with replacement (a player contributes several seasons), generator seed + 1.

## Reproduction

- **Amendment 3:** generator `scripts/sloan_fullpaper_amend3.py` (commit `0ef110cdc`, sha256 `d7de5367a04fff5d…`), amendment commit `caf090288` (file sha256 `3c56752d05a537fc…`), retained run `research-runs/sloan-fullpaper/amend3-02`, 2,000 bootstrap draws, seed 0, 518 input files, 2,539 code files, status complete.
- **Amendment 4:** generator `scripts/sloan_fullpaper_amend4.py` (commit `e65c91983`, sha256 `423bfdbbb7a6931d…`), amendment commit `5ab52fac1` (file sha256 `16c68731112fa64a…`), retained run `research-runs/sloan-fullpaper/amend4-01`, 2,000 bootstrap draws, seed 0, 10 input files, 2,540 code files, status complete.
