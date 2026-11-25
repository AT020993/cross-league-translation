# Which skills travel: E15 of Amendment 1 (exploratory)

**Exploratory.** Destination seasons 2017–2025 were already inspected before this analysis was registered, so nothing here is a confirmatory test. The frozen 2026-27 test (P1) is untouched.

Registered in `docs/research/sloan-full-paper-preregistration-amendment-1-2026-11-04.md` (commit `f1a3453da`, sha256 `5e6554dfe2861c0be55a65deef6f9ea3cca95b9bd35fb6c27c4a5dd8d4c42776`). Generator `scripts/sloan_fullpaper_skills.py`; this note is written by `scripts/report_sloan_fullpaper_skills.py` from the committed run outputs in `docs/research/artifacts/sloan-fullpaper-skills-2026-11/`.

Retained run `research-runs/sloan-fullpaper/skills-01`: status `complete` (return code 0), generator sha256 `8ec2aca0f90db08d6751b960751beaf5780e072fa5bc0cdc0187754b76e42b1e`, 520 input files, source seasons 2015–2025; `out/summary.json` sha256 `7ccf69ba4ce5ece7550e7ef96438f606b20c97d559a43c767d9dd5e3a4ecf724`.

## In plain words

* **Same player, same season (E15a).** When a player plays in his domestic league and in the EuroLeague or EuroCup in the same season, he keeps the most of his offensive rebounds (retention 1.087, i.e. his continental rate is 1.087 times his domestic rate; ratio of sums 0.931) and the least of his points (0.926; ratio of sums 0.940). For 3 of the 9 per-36 components the interval includes 1 (no measurable change): defensive rebounds, steals, blocks.
* **Licensed comparisons.** 39 ordered pairs of components have non-overlapping intervals; each earns the registered sentence (listed below).
* **But the E15a ranking depends on the estimator (load-bearing).** The registered estimator averages per-player ratios; the ratio-of-sums check divides total rates. For 6 of 11 components their intervals do not overlap: offensive rebounds 1.087 vs 0.931, defensive rebounds 0.985 vs 0.932, steals 1.003 vs 0.916, blocks 0.995 vs 0.897, turnovers 1.043 vs 0.997, 3-point percentage 0.995 vs 0.977. Only 14 of the 39 licensed comparisons also hold under ratio of sums. Read the E15a sentences with this in mind (section 'Estimator sensitivity').
* **Arrivals (E15b).** Among the 674 arrivals, after correcting for how noisy one continental season is, the component whose domestic level carries over best is 3-point attempts (disattenuated r 0.891) and the one that carries over worst is steals (0.548).
* **Not measurable in one season.** Destination reliability is below the 0.40 floor for 3-point percentage (0.104), so its carry-over cannot be read.
* **'The' skill that travels.** No component earns it: no disattenuated interval lies above every other component's point estimate.
* **League offsets.** The λ10 source-league offsets, refitted per component, spread between 0.075 and 0.140 component SDs across the per-36 components.

## Specification

| Field | Registered choice (Amendment 1, E15) | How it is implemented here |
|---|---|---|
| Components | per 36: points, OREB, DREB, AST, STL, BLK, TOV, 3PA, FTA; secondary 3P%, FT% with ≥ 20 attempts both sides | cohort/pair totals; percentages need ≥ 20 attempts on both sides |
| E15a unit and population | pool-A factor-estimation pairs (same player, same season) | 4074 pairs, 1538 players |
| E15a estimator | exposure-weighted retention ratio, continental per-36 ÷ domestic per-36 | the factor table's `exposure_weighted` estimator: per-pair ratio weighted by the thinner side's minutes (attempts for percentages); a pair with a zero domestic count cannot form a ratio and is counted as excluded (gate G15a) |
| E15a interval | cluster bootstrap by player, 2,000 draws, seed 0 | 2000 draws, seed 0, one joint draw per subset for all components |
| E15a printed | by destination competition, and by source league where a league has ≥ 75 pairs | pooled, both destinations, and 10 source leagues (pooled over destinations; none below the floor) |
| E15b population | the 674 (pool A, R1) | 674 targets; percentages only where both sides have ≥ 20 attempts |
| E15b primary | source–destination correlation disattenuated by the destination split-half reliability (E6 method per component) | Pearson r ÷ √(Spearman–Brown reliability of odd/even destination appearances in date order, per-game continental box scores) |
| E15b printed | source-rate slope; λ10 source-offset spread in component SD units | the registered `source_ridge_10` model refitted on the 674 with the component in place of EFF (source rate, own history by the v10 rule, above-history flag, destination, destination × source, ridge-10 source offsets); slope = source-rate coefficient (EuroCup) and coefficient + interaction (EuroLeague); spread = SD of the fitted offsets ÷ SD of the destination component. The unadjusted OLS slope is also printed |
| E15b interval | registered default: cluster bootstrap over destination club-seasons, 2,000 draws, seed 0 | 201 club-seasons; reliability, correlation and fit recomputed in every draw, one joint draw for all components |
| Licences | E15a: two components whose intervals do not overlap; E15b descriptive with the 'the skill' rule | E15a on the pooled intervals, every ordered pair of the 11 components; E15b rule against all 10 other components |

Choices the amendment leaves open (weights for percentages, the form of the slope, the SD definition, the bootstrap for E15b) were fixed in the generator before the retained run. Two 20-draw mechanics checks were run during development and showed point estimates; between them the generator only gained the E6 split-half reproduction gate. No estimator, threshold, population or interval changed after those checks. After the retained run only this report changed: the reliability-floor flag, the estimator-sensitivity section, the figure and this paragraph. Every number comes from the unchanged outputs of the generator run.

## Gates

| Gate | Rule | Result | Negative control |
|---|---|---|---|
| G15a estimator | this module's estimator reproduces `fit_table` EFF factor_raw on all 20 cells to 1e-12 | passed (max diff 7.77e-16) | impossible tolerance: rejected as required |
| G3 history | rebuilt EFF history equals cohort `prior_mean_pir36` on 1371 rows to 1e-09 | passed (max diff 0.00e+00, 0 NaN mismatches) | impossible tolerance: rejected as required |
| E6 reconciliation | every target's per-game rows match cohort games, minutes and EFF | passed: 674/674 targets, 12008 player-games | games + 1: every target flagged as required |
| Component totals | per-game sums equal cohort destination totals for every component and exposure, to 1e-09 | passed (max diff 5.68e-14) | points + 1: rejected as required |
| E6 reproduction | this module's EFF odd/even/full rates equal E6 `split_half_table` | passed (max diff 0.00e+00) | impossible tolerance: rejected as required |

## E15a. Same player, same season: retention ratios

Retention = continental per-36 ÷ domestic per-36 (for percentages, continental % ÷ domestic %). Below 1: the player does less of it against continental opponents. 'Ratio of sums' (total continental rate ÷ total domestic rate) is a sensitivity check that keeps zero-domestic pairs; it earns no licence.

### Pooled (all pairs)

| Component | Retention | 95% CI | Pairs used | Zero-domestic excluded | Ratio of sums | 95% CI |
|---|---|---|---|---|---|---|
| points | 0.926 | [0.919, 0.933] | 4074 / 4074 | 0 | 0.940 | [0.930, 0.950] |
| offensive rebounds | 1.087 | [1.064, 1.109] | 4050 / 4074 | 24 | 0.931 | [0.908, 0.955] |
| defensive rebounds | 0.985 | [0.967, 1.008] | 4072 / 4074 | 2 | 0.932 | [0.920, 0.943] |
| assists | 0.931 | [0.918, 0.944] | 4068 / 4074 | 6 | 0.921 | [0.900, 0.942] |
| steals | 1.003 | [0.987, 1.019] | 4066 / 4074 | 8 | 0.916 | [0.902, 0.930] |
| blocks | 0.995 | [0.962, 1.029] | 3437 / 4074 | 637 | 0.897 | [0.864, 0.929] |
| turnovers | 1.043 | [1.031, 1.055] | 4071 / 4074 | 3 | 0.997 | [0.984, 1.011] |
| 3-point attempts | 0.951 | [0.936, 0.966] | 3773 / 4074 | 301 | 0.961 | [0.943, 0.978] |
| free-throw attempts | 0.935 | [0.919, 0.953] | 4062 / 4074 | 12 | 0.906 | [0.889, 0.923] |
| 3-point percentage | 0.995 | [0.987, 1.004] | 2759 / 2759 | 0 | 0.977 | [0.969, 0.986] |
| free-throw percentage | 1.007 | [1.002, 1.011] | 2517 / 2517 | 0 | 1.009 | [1.003, 1.014] |

### Estimator sensitivity (load-bearing)

The registered estimator is the factor table's: an average of each pair's own ratio (continental ÷ domestic), weighted by the thinner side's minutes. When a component is a small count per player (a few offensive rebounds, steals or blocks in a domestic sample), dividing by a small, noisy domestic count makes individual ratios large and pulls the average up; the ratio of sums divides totals and does not have this problem, but weights high-volume players more. The two agree for high-count components and disagree for low-count ones. This is the likely explanation, not a tested one. The amendment registers the per-pair estimator, so its licences stand as registered; the column 'Overlap' shows whether the two intervals overlap.

| Component | Per-pair (registered) | 95% CI | Ratio of sums | 95% CI | Difference | Overlap |
|---|---|---|---|---|---|---|
| points | 0.926 | [0.919, 0.933] | 0.940 | [0.930, 0.950] | -0.014 | yes |
| offensive rebounds | 1.087 | [1.064, 1.109] | 0.931 | [0.908, 0.955] | 0.156 | **no** |
| defensive rebounds | 0.985 | [0.967, 1.008] | 0.932 | [0.920, 0.943] | 0.053 | **no** |
| assists | 0.931 | [0.918, 0.944] | 0.921 | [0.900, 0.942] | 0.009 | yes |
| steals | 1.003 | [0.987, 1.019] | 0.916 | [0.902, 0.930] | 0.087 | **no** |
| blocks | 0.995 | [0.962, 1.029] | 0.897 | [0.864, 0.929] | 0.099 | **no** |
| turnovers | 1.043 | [1.031, 1.055] | 0.997 | [0.984, 1.011] | 0.045 | **no** |
| 3-point attempts | 0.951 | [0.936, 0.966] | 0.961 | [0.943, 0.978] | -0.010 | yes |
| free-throw attempts | 0.935 | [0.919, 0.953] | 0.906 | [0.889, 0.923] | 0.029 | yes |
| 3-point percentage | 0.995 | [0.987, 1.004] | 0.977 | [0.969, 0.986] | 0.018 | **no** |
| free-throw percentage | 1.007 | [1.002, 1.011] | 1.009 | [1.003, 1.014] | -0.002 | yes |

### By destination competition

| Component | EuroCup (1947 pairs) | 95% CI | EuroLeague (2127 pairs) | 95% CI |
|---|---|---|---|---|
| points | 0.975 | [0.966, 0.984] | 0.891 | [0.882, 0.900] |
| offensive rebounds | 1.060 | [1.034, 1.087] | 1.106 | [1.076, 1.138] |
| defensive rebounds | 1.045 | [1.017, 1.077] | 0.943 | [0.916, 0.976] |
| assists | 1.010 | [0.991, 1.031] | 0.874 | [0.859, 0.889] |
| steals | 1.065 | [1.041, 1.090] | 0.958 | [0.937, 0.981] |
| blocks | 1.070 | [1.012, 1.127] | 0.941 | [0.901, 0.982] |
| turnovers | 1.105 | [1.088, 1.121] | 0.999 | [0.984, 1.014] |
| 3-point attempts | 0.973 | [0.954, 0.992] | 0.935 | [0.916, 0.957] |
| free-throw attempts | 1.033 | [1.011, 1.056] | 0.866 | [0.846, 0.887] |
| 3-point percentage | 1.011 | [0.998, 1.025] | 0.984 | [0.973, 0.996] |
| free-throw percentage | 1.008 | [1.001, 1.016] | 1.005 | [1.000, 1.011] |

### By source league (≥ 75 pairs; both destinations pooled)

| Component | ABA (472) | France (378) | Germany (441) | Greece (266) | Israel (190) | Italy (439) | Lithuania (267) | Spain (813) | Turkey (494) | VTB (314) |
|---|---|---|---|---|---|---|---|---|---|---|
| points | 0.908 [0.888, 0.929] | 0.935 [0.915, 0.957] | 0.909 [0.889, 0.930] | 0.900 [0.872, 0.931] | 0.917 [0.887, 0.946] | 0.952 [0.933, 0.973] | 0.902 [0.877, 0.929] | 0.949 [0.937, 0.962] | 0.925 [0.908, 0.943] | 0.905 [0.887, 0.924] |
| offensive rebounds | 1.238 [1.142, 1.344] n=471 | 1.061 [1.005, 1.119] n=376 | 0.968 [0.901, 1.043] n=439 | 1.093 [1.007, 1.181] n=264 | 1.055 [0.967, 1.149] n=188 | 1.051 [0.987, 1.113] n=436 | 1.103 [1.030, 1.191] n=265 | 1.089 [1.052, 1.127] n=807 | 1.087 [1.035, 1.146] n=491 | 1.138 [1.069, 1.210] n=313 |
| defensive rebounds | 0.948 [0.927, 0.970] | 0.952 [0.928, 0.978] n=377 | 1.378 [1.225, 1.558] | 0.848 [0.823, 0.872] | 0.876 [0.845, 0.910] | 0.915 [0.893, 0.938] | 0.949 [0.918, 0.982] n=266 | 0.968 [0.952, 0.985] | 0.928 [0.905, 0.953] | 0.957 [0.921, 0.999] |
| assists | 0.842 [0.808, 0.880] | 0.894 [0.865, 0.924] n=377 | 0.906 [0.877, 0.937] n=440 | 0.793 [0.753, 0.836] | 0.869 [0.831, 0.907] | 1.016 [0.976, 1.059] n=438 | 0.798 [0.767, 0.832] n=266 | 1.107 [1.080, 1.137] n=812 | 0.855 [0.831, 0.881] n=493 | 0.863 [0.829, 0.903] |
| steals | 0.935 [0.893, 0.981] n=471 | 1.105 [1.054, 1.161] | 0.964 [0.925, 1.007] | 0.975 [0.922, 1.034] n=265 | 1.032 [0.974, 1.092] | 1.080 [1.033, 1.129] | 0.867 [0.811, 0.925] n=266 | 0.991 [0.959, 1.025] n=811 | 1.037 [0.989, 1.086] n=493 | 1.019 [0.960, 1.082] n=312 |
| blocks | 0.826 [0.748, 0.905] n=397 | 1.044 [0.937, 1.154] n=322 | 0.889 [0.786, 1.001] n=391 | 0.980 [0.861, 1.117] n=214 | 0.900 [0.796, 1.009] n=163 | 1.122 [1.017, 1.239] n=366 | 0.964 [0.843, 1.105] n=228 | 0.975 [0.905, 1.049] n=677 | 1.125 [1.040, 1.217] n=412 | 1.102 [0.967, 1.262] n=267 |
| turnovers | 1.089 [1.052, 1.126] n=471 | 0.977 [0.941, 1.014] | 1.023 [0.992, 1.054] | 1.031 [0.984, 1.086] | 0.982 [0.935, 1.032] | 1.055 [1.019, 1.092] | 1.096 [1.054, 1.138] n=266 | 1.036 [1.012, 1.060] n=812 | 1.067 [1.031, 1.106] | 1.063 [1.019, 1.111] |
| 3-point attempts | 0.915 [0.877, 0.956] n=426 | 0.932 [0.897, 0.969] n=345 | 1.007 [0.957, 1.070] n=422 | 0.927 [0.880, 0.970] n=245 | 0.952 [0.873, 1.052] n=177 | 0.976 [0.941, 1.015] n=410 | 0.912 [0.862, 0.961] n=247 | 0.942 [0.914, 0.968] n=756 | 0.925 [0.893, 0.955] n=458 | 1.027 [0.955, 1.130] n=287 |
| free-throw attempts | 0.951 [0.901, 1.003] n=471 | 0.921 [0.868, 0.980] | 0.807 [0.775, 0.840] n=440 | 0.980 [0.918, 1.048] | 0.921 [0.865, 0.978] | 0.979 [0.938, 1.024] n=437 | 0.993 [0.938, 1.058] | 0.938 [0.909, 0.973] n=808 | 1.014 [0.967, 1.073] n=491 | 0.847 [0.795, 0.906] |
| 3-point percentage | 0.963 [0.934, 0.991] n=295 | 0.996 [0.965, 1.029] n=267 | 1.004 [0.979, 1.030] n=305 | 0.958 [0.922, 0.996] n=188 | 1.018 [0.971, 1.069] n=118 | 0.998 [0.971, 1.024] n=298 | 0.975 [0.943, 1.006] n=173 | 1.013 [0.994, 1.035] n=578 | 0.989 [0.965, 1.013] n=324 | 1.005 [0.973, 1.036] n=213 |
| free-throw percentage | 0.983 [0.968, 0.997] n=255 | 1.007 [0.992, 1.022] n=239 | 1.008 [0.995, 1.021] n=266 | 1.016 [0.994, 1.038] n=179 | 1.022 [1.002, 1.043] n=128 | 1.008 [0.995, 1.023] n=265 | 1.016 [1.001, 1.033] n=171 | 1.004 [0.996, 1.012] n=537 | 1.012 [0.996, 1.027] n=290 | 1.003 [0.987, 1.017] n=187 |

Cells show retention [95% CI]; `n=` marks cells where fewer than all pairs could form a ratio (zero domestic count or the attempt floor).

### E15a licences earned

Registered licence: two components whose E15a intervals do not overlap earn "the same player keeps more of his C1 than his C2 when he faces continental opponents".

| Higher | Lower | Higher CI low | Lower CI high | Also disjoint under ratio of sums? | Sentence earned |
|---|---|---|---|---|---|
| offensive rebounds | points | 1.064 | 0.933 | **no** | "the same player keeps more of his offensive rebounds than his points when he faces continental opponents" |
| offensive rebounds | defensive rebounds | 1.064 | 1.008 | **no** | "the same player keeps more of his offensive rebounds than his defensive rebounds when he faces continental opponents" |
| offensive rebounds | assists | 1.064 | 0.944 | **no** | "the same player keeps more of his offensive rebounds than his assists when he faces continental opponents" |
| offensive rebounds | steals | 1.064 | 1.019 | **no** | "the same player keeps more of his offensive rebounds than his steals when he faces continental opponents" |
| offensive rebounds | blocks | 1.064 | 1.029 | **no** | "the same player keeps more of his offensive rebounds than his blocks when he faces continental opponents" |
| offensive rebounds | turnovers | 1.064 | 1.055 | **no** | "the same player keeps more of his offensive rebounds than his turnovers when he faces continental opponents" |
| offensive rebounds | 3-point attempts | 1.064 | 0.966 | **no** | "the same player keeps more of his offensive rebounds than his 3-point attempts when he faces continental opponents" |
| offensive rebounds | free-throw attempts | 1.064 | 0.953 | **no** | "the same player keeps more of his offensive rebounds than his free-throw attempts when he faces continental opponents" |
| offensive rebounds | 3-point percentage | 1.064 | 1.004 | **no** | "the same player keeps more of his offensive rebounds than his 3-point percentage when he faces continental opponents" |
| offensive rebounds | free-throw percentage | 1.064 | 1.011 | **no** | "the same player keeps more of his offensive rebounds than his free-throw percentage when he faces continental opponents" |
| defensive rebounds | points | 0.967 | 0.933 | **no** | "the same player keeps more of his defensive rebounds than his points when he faces continental opponents" |
| defensive rebounds | assists | 0.967 | 0.944 | **no** | "the same player keeps more of his defensive rebounds than his assists when he faces continental opponents" |
| defensive rebounds | 3-point attempts | 0.967 | 0.966 | **no** | "the same player keeps more of his defensive rebounds than his 3-point attempts when he faces continental opponents" |
| defensive rebounds | free-throw attempts | 0.967 | 0.953 | **no** | "the same player keeps more of his defensive rebounds than his free-throw attempts when he faces continental opponents" |
| steals | points | 0.987 | 0.933 | **no** | "the same player keeps more of his steals than his points when he faces continental opponents" |
| steals | assists | 0.987 | 0.944 | **no** | "the same player keeps more of his steals than his assists when he faces continental opponents" |
| steals | 3-point attempts | 0.987 | 0.966 | **no** | "the same player keeps more of his steals than his 3-point attempts when he faces continental opponents" |
| steals | free-throw attempts | 0.987 | 0.953 | **no** | "the same player keeps more of his steals than his free-throw attempts when he faces continental opponents" |
| blocks | points | 0.962 | 0.933 | **no** | "the same player keeps more of his blocks than his points when he faces continental opponents" |
| blocks | assists | 0.962 | 0.944 | **no** | "the same player keeps more of his blocks than his assists when he faces continental opponents" |
| blocks | free-throw attempts | 0.962 | 0.953 | **no** | "the same player keeps more of his blocks than his free-throw attempts when he faces continental opponents" |
| turnovers | points | 1.031 | 0.933 | yes | "the same player keeps more of his turnovers than his points when he faces continental opponents" |
| turnovers | defensive rebounds | 1.031 | 1.008 | yes | "the same player keeps more of his turnovers than his defensive rebounds when he faces continental opponents" |
| turnovers | assists | 1.031 | 0.944 | yes | "the same player keeps more of his turnovers than his assists when he faces continental opponents" |
| turnovers | steals | 1.031 | 1.019 | yes | "the same player keeps more of his turnovers than his steals when he faces continental opponents" |
| turnovers | blocks | 1.031 | 1.029 | yes | "the same player keeps more of his turnovers than his blocks when he faces continental opponents" |
| turnovers | 3-point attempts | 1.031 | 0.966 | yes | "the same player keeps more of his turnovers than his 3-point attempts when he faces continental opponents" |
| turnovers | free-throw attempts | 1.031 | 0.953 | yes | "the same player keeps more of his turnovers than his free-throw attempts when he faces continental opponents" |
| turnovers | 3-point percentage | 1.031 | 1.004 | **no** | "the same player keeps more of his turnovers than his 3-point percentage when he faces continental opponents" |
| turnovers | free-throw percentage | 1.031 | 1.011 | **no** | "the same player keeps more of his turnovers than his free-throw percentage when he faces continental opponents" |
| 3-point attempts | points | 0.936 | 0.933 | **no** | "the same player keeps more of his 3-point attempts than his points when he faces continental opponents" |
| 3-point percentage | points | 0.987 | 0.933 | yes | "the same player keeps more of his 3-point percentage than his points when he faces continental opponents" |
| 3-point percentage | assists | 0.987 | 0.944 | yes | "the same player keeps more of his 3-point percentage than his assists when he faces continental opponents" |
| 3-point percentage | 3-point attempts | 0.987 | 0.966 | **no** | "the same player keeps more of his 3-point percentage than his 3-point attempts when he faces continental opponents" |
| 3-point percentage | free-throw attempts | 0.987 | 0.953 | yes | "the same player keeps more of his 3-point percentage than his free-throw attempts when he faces continental opponents" |
| free-throw percentage | points | 1.002 | 0.933 | yes | "the same player keeps more of his free-throw percentage than his points when he faces continental opponents" |
| free-throw percentage | assists | 1.002 | 0.944 | yes | "the same player keeps more of his free-throw percentage than his assists when he faces continental opponents" |
| free-throw percentage | 3-point attempts | 1.002 | 0.966 | yes | "the same player keeps more of his free-throw percentage than his 3-point attempts when he faces continental opponents" |
| free-throw percentage | free-throw attempts | 1.002 | 0.953 | yes | "the same player keeps more of his free-throw percentage than his free-throw attempts when he faces continental opponents" |

## E15b. Arrivals: does the domestic level carry over?

r is the plain correlation between a player's domestic per-36 in the source season and his continental per-36 in the arrival season. One continental season is noisy, so r is divided by √(destination reliability), the split-half reliability of that component; √reliability is the ceiling r could reach if the domestic level predicted the true continental level perfectly. Only destination noise is corrected (as registered), so the disattenuated r is still pulled down by source-season noise.

| Component | n | r | 95% CI | Split-half r | Reliability | Ceiling √rel | Disattenuated r | 95% CI |
|---|---|---|---|---|---|---|---|---|
| points | 674 | 0.576 | [0.517, 0.628] | 0.622 | 0.767 [0.724, 0.802] | 0.876 | 0.657 | [0.595, 0.717] |
| offensive rebounds | 674 | 0.803 | [0.763, 0.839] | 0.695 | 0.820 [0.782, 0.853] | 0.905 | 0.887 | [0.843, 0.925] |
| defensive rebounds | 674 | 0.717 | [0.671, 0.759] | 0.614 | 0.761 [0.712, 0.803] | 0.872 | 0.822 | [0.774, 0.867] |
| assists | 674 | 0.809 | [0.774, 0.838] | 0.825 | 0.904 [0.888, 0.920] | 0.951 | 0.850 | [0.816, 0.880] |
| steals | 674 | 0.366 | [0.294, 0.437] | 0.288 | 0.447 [0.328, 0.544] | 0.669 | 0.548 | [0.440, 0.682] |
| blocks | 674 | 0.769 | [0.724, 0.812] | 0.740 | 0.850 [0.808, 0.885] | 0.922 | 0.834 | [0.786, 0.882] |
| turnovers | 674 | 0.543 | [0.491, 0.590] | 0.465 | 0.634 [0.565, 0.699] | 0.797 | 0.681 | [0.618, 0.745] |
| 3-point attempts | 674 | 0.862 | [0.841, 0.881] | 0.881 | 0.937 [0.926, 0.947] | 0.968 | 0.891 | [0.869, 0.910] |
| free-throw attempts | 674 | 0.561 | [0.505, 0.611] | 0.508 | 0.674 [0.615, 0.724] | 0.821 | 0.683 | [0.618, 0.743] |
| 3-point percentage | 411 | 0.239 | [0.142, 0.336] | 0.055 | 0.104 [-0.111, 0.274] | 0.322 | 0.744 | [0.361, 2.823] |
| free-throw percentage | 378 | 0.611 | [0.542, 0.672] | 0.489 | 0.657 [0.563, 0.736] | 0.810 | 0.753 | [0.671, 0.838] |

Draws with a non-positive reliability give no disattenuated r and are left out of that interval: valid draws 3-point percentage (1688 of 2000).

**Below the project's interpretable reliability floor (0.40, `src/research/gates.py`):** 3-point percentage (reliability 0.104 [-0.111, 0.274]). One continental season does not measure this component reliably, so its disattenuated r is not interpretable and is reported for completeness only.

### Slopes and league offsets (λ10 model refitted per component)

| Component | Unadjusted slope | 95% CI | λ10 source-rate slope, EuroCup | 95% CI | EuroLeague | 95% CI | Offset spread (SD units) | 95% CI |
|---|---|---|---|---|---|---|---|---|
| points | 0.634 | [0.560, 0.708] | 0.704 | [0.559, 0.832] | 0.486 | [0.325, 0.647] | 0.139 | [0.113, 0.215] |
| offensive rebounds | 0.812 | [0.760, 0.862] | 0.687 | [0.557, 0.801] | 0.709 | [0.553, 0.850] | 0.075 | [0.062, 0.138] |
| defensive rebounds | 0.715 | [0.657, 0.773] | 0.576 | [0.396, 0.716] | 0.471 | [0.284, 0.611] | 0.110 | [0.084, 0.178] |
| assists | 0.783 | [0.727, 0.840] | 0.601 | [0.466, 0.731] | 0.483 | [0.352, 0.619] | 0.105 | [0.082, 0.152] |
| steals | 0.408 | [0.328, 0.490] | 0.291 | [0.174, 0.417] | 0.225 | [0.060, 0.415] | 0.140 | [0.112, 0.220] |
| blocks | 0.756 | [0.659, 0.861] | 0.646 | [0.388, 0.846] | 0.511 | [0.215, 0.701] | 0.079 | [0.060, 0.136] |
| turnovers | 0.640 | [0.567, 0.718] | 0.706 | [0.523, 0.820] | 0.610 | [0.432, 0.754] | 0.101 | [0.080, 0.194] |
| 3-point attempts | 0.861 | [0.822, 0.899] | 0.716 | [0.578, 0.819] | 0.661 | [0.484, 0.785] | 0.077 | [0.061, 0.127] |
| free-throw attempts | 0.571 | [0.492, 0.647] | 0.699 | [0.527, 0.821] | 0.491 | [0.355, 0.609] | 0.099 | [0.084, 0.184] |
| 3-point percentage | 0.286 | [0.168, 0.409] | 0.228 | [0.032, 0.427] | 0.270 | [0.041, 0.483] | 0.134 | [0.114, 0.245] |
| free-throw percentage | 0.653 | [0.567, 0.737] | 0.338 | [0.142, 0.538] | 0.346 | [0.068, 0.579] | 0.094 | [0.080, 0.180] |

The slope is the change in continental per-36 for one more unit of domestic per-36, holding the player's own earlier history and the source league fixed. Targets with no earlier season fall back to their source rate as history (v10 rule): 92 of 674 for the per-36 components.

Per-league offsets in component SD units (positive: arrivals from that league do better than the model's league-blind prediction), with 95% CI:

| Component | ABA | France | Germany | Greece | Israel | Italy | Lithuania | Spain | Turkey | VTB |
|---|---|---|---|---|---|---|---|---|---|---|
| points | -0.13 [-0.27, 0.04] | 0.17 [0.01, 0.32] | -0.11 [-0.23, 0.01] | 0.02 [-0.14, 0.22] | -0.12 [-0.23, 0.00] | 0.20 [0.06, 0.33] | -0.04 [-0.24, 0.13] | 0.17 [0.04, 0.29] | 0.01 [-0.12, 0.14] | -0.18 [-0.43, 0.06] |
| offensive rebounds | -0.01 [-0.15, 0.14] | 0.17 [0.05, 0.30] | -0.12 [-0.22, -0.02] | 0.03 [-0.11, 0.14] | 0.02 [-0.09, 0.13] | -0.05 [-0.14, 0.04] | -0.03 [-0.17, 0.11] | -0.06 [-0.15, 0.03] | 0.04 [-0.07, 0.15] | 0.01 [-0.14, 0.18] |
| defensive rebounds | -0.08 [-0.20, 0.05] | 0.20 [0.07, 0.34] | -0.05 [-0.16, 0.07] | 0.03 [-0.13, 0.20] | -0.09 [-0.26, 0.08] | -0.01 [-0.14, 0.12] | -0.00 [-0.13, 0.12] | 0.17 [0.06, 0.29] | -0.03 [-0.14, 0.08] | -0.14 [-0.29, -0.00] |
| assists | -0.09 [-0.20, 0.02] | -0.04 [-0.15, 0.07] | -0.02 [-0.13, 0.08] | 0.04 [-0.04, 0.12] | -0.07 [-0.19, 0.06] | 0.11 [0.04, 0.18] | -0.14 [-0.22, -0.04] | 0.22 [0.11, 0.33] | -0.01 [-0.09, 0.07] | -0.00 [-0.14, 0.15] |
| steals | -0.22 [-0.37, -0.05] | 0.07 [-0.09, 0.23] | 0.10 [-0.03, 0.24] | -0.22 [-0.37, -0.02] | 0.04 [-0.14, 0.23] | 0.16 [0.02, 0.31] | -0.15 [-0.36, 0.03] | 0.09 [-0.06, 0.27] | 0.05 [-0.09, 0.19] | 0.06 [-0.20, 0.31] |
| blocks | -0.15 [-0.27, -0.01] | 0.09 [-0.02, 0.20] | -0.09 [-0.18, -0.00] | 0.01 [-0.14, 0.19] | -0.01 [-0.16, 0.12] | 0.11 [0.01, 0.21] | -0.02 [-0.12, 0.11] | -0.01 [-0.09, 0.07] | 0.03 [-0.05, 0.13] | 0.05 [-0.07, 0.17] |
| turnovers | -0.23 [-0.40, -0.03] | 0.03 [-0.12, 0.20] | -0.03 [-0.20, 0.15] | 0.01 [-0.14, 0.14] | -0.11 [-0.27, 0.09] | 0.11 [-0.02, 0.23] | -0.00 [-0.23, 0.24] | 0.08 [-0.07, 0.22] | 0.06 [-0.08, 0.21] | 0.07 [-0.16, 0.32] |
| 3-point attempts | -0.10 [-0.18, -0.03] | 0.09 [-0.03, 0.19] | -0.04 [-0.13, 0.05] | 0.01 [-0.12, 0.17] | -0.15 [-0.25, -0.04] | 0.07 [-0.02, 0.16] | -0.01 [-0.14, 0.10] | 0.08 [-0.01, 0.17] | 0.02 [-0.05, 0.09] | 0.03 [-0.09, 0.16] |
| free-throw attempts | -0.05 [-0.23, 0.16] | 0.07 [-0.05, 0.22] | -0.17 [-0.29, -0.03] | -0.02 [-0.22, 0.19] | -0.06 [-0.21, 0.09] | 0.15 [0.02, 0.27] | 0.11 [-0.09, 0.32] | -0.00 [-0.13, 0.12] | 0.06 [-0.05, 0.18] | -0.09 [-0.34, 0.15] |
| 3-point percentage | -0.10 [-0.28, 0.11] | 0.22 [-0.00, 0.41] | -0.11 [-0.30, 0.08] | -0.08 [-0.36, 0.25] | -0.17 [-0.42, 0.11] | 0.04 [-0.23, 0.30] | 0.10 [-0.12, 0.31] | 0.20 [0.02, 0.37] | -0.03 [-0.23, 0.18] | -0.07 [-0.32, 0.16] |
| free-throw percentage | 0.03 [-0.13, 0.17] | -0.03 [-0.25, 0.16] | 0.08 [-0.12, 0.26] | 0.19 [0.03, 0.34] | 0.07 [-0.08, 0.22] | -0.11 [-0.29, 0.07] | -0.10 [-0.28, 0.11] | -0.00 [-0.15, 0.15] | -0.05 [-0.19, 0.08] | -0.08 [-0.28, 0.12] |

Arrivals per source league among the 674: ABA 70, France 70, Germany 87, Greece 30, Israel 49, Italy 77, Lithuania 48, Spain 108, Turkey 108, VTB 27.

### E15b licence

Registered rule: E15b is descriptive. No single component is called "the" skill that travels unless its disattenuated correlation interval is above every other component's point estimate.

| Component | Disattenuated CI low | Highest other point estimate | Called 'the' skill? |
|---|---|---|---|
| points | 0.595 | 0.891 | no |
| offensive rebounds | 0.843 | 0.891 | no |
| defensive rebounds | 0.774 | 0.891 | no |
| assists | 0.816 | 0.891 | no |
| steals | 0.440 | 0.891 | no |
| blocks | 0.786 | 0.891 | no |
| turnovers | 0.618 | 0.891 | no |
| 3-point attempts | 0.869 | 0.887 | no |
| free-throw attempts | 0.618 | 0.891 | no |
| 3-point percentage | 0.361 | 0.891 | no |
| free-throw percentage | 0.671 | 0.891 | no |

## Sentences this note licenses

All are exploratory (Amendment 1).

* E15a: "the same player keeps more of his offensive rebounds than his points when he faces continental opponents" (estimator-sensitive: not disjoint under ratio of sums).
* E15a: "the same player keeps more of his offensive rebounds than his defensive rebounds when he faces continental opponents" (estimator-sensitive: not disjoint under ratio of sums).
* E15a: "the same player keeps more of his offensive rebounds than his assists when he faces continental opponents" (estimator-sensitive: not disjoint under ratio of sums).
* E15a: "the same player keeps more of his offensive rebounds than his steals when he faces continental opponents" (estimator-sensitive: not disjoint under ratio of sums).
* E15a: "the same player keeps more of his offensive rebounds than his blocks when he faces continental opponents" (estimator-sensitive: not disjoint under ratio of sums).
* E15a: "the same player keeps more of his offensive rebounds than his turnovers when he faces continental opponents" (estimator-sensitive: not disjoint under ratio of sums).
* E15a: "the same player keeps more of his offensive rebounds than his 3-point attempts when he faces continental opponents" (estimator-sensitive: not disjoint under ratio of sums).
* E15a: "the same player keeps more of his offensive rebounds than his free-throw attempts when he faces continental opponents" (estimator-sensitive: not disjoint under ratio of sums).
* E15a: "the same player keeps more of his offensive rebounds than his 3-point percentage when he faces continental opponents" (estimator-sensitive: not disjoint under ratio of sums).
* E15a: "the same player keeps more of his offensive rebounds than his free-throw percentage when he faces continental opponents" (estimator-sensitive: not disjoint under ratio of sums).
* E15a: "the same player keeps more of his defensive rebounds than his points when he faces continental opponents" (estimator-sensitive: not disjoint under ratio of sums).
* E15a: "the same player keeps more of his defensive rebounds than his assists when he faces continental opponents" (estimator-sensitive: not disjoint under ratio of sums).
* E15a: "the same player keeps more of his defensive rebounds than his 3-point attempts when he faces continental opponents" (estimator-sensitive: not disjoint under ratio of sums).
* E15a: "the same player keeps more of his defensive rebounds than his free-throw attempts when he faces continental opponents" (estimator-sensitive: not disjoint under ratio of sums).
* E15a: "the same player keeps more of his steals than his points when he faces continental opponents" (estimator-sensitive: not disjoint under ratio of sums).
* E15a: "the same player keeps more of his steals than his assists when he faces continental opponents" (estimator-sensitive: not disjoint under ratio of sums).
* E15a: "the same player keeps more of his steals than his 3-point attempts when he faces continental opponents" (estimator-sensitive: not disjoint under ratio of sums).
* E15a: "the same player keeps more of his steals than his free-throw attempts when he faces continental opponents" (estimator-sensitive: not disjoint under ratio of sums).
* E15a: "the same player keeps more of his blocks than his points when he faces continental opponents" (estimator-sensitive: not disjoint under ratio of sums).
* E15a: "the same player keeps more of his blocks than his assists when he faces continental opponents" (estimator-sensitive: not disjoint under ratio of sums).
* E15a: "the same player keeps more of his blocks than his free-throw attempts when he faces continental opponents" (estimator-sensitive: not disjoint under ratio of sums).
* E15a: "the same player keeps more of his turnovers than his points when he faces continental opponents" (also holds under ratio of sums).
* E15a: "the same player keeps more of his turnovers than his defensive rebounds when he faces continental opponents" (also holds under ratio of sums).
* E15a: "the same player keeps more of his turnovers than his assists when he faces continental opponents" (also holds under ratio of sums).
* E15a: "the same player keeps more of his turnovers than his steals when he faces continental opponents" (also holds under ratio of sums).
* E15a: "the same player keeps more of his turnovers than his blocks when he faces continental opponents" (also holds under ratio of sums).
* E15a: "the same player keeps more of his turnovers than his 3-point attempts when he faces continental opponents" (also holds under ratio of sums).
* E15a: "the same player keeps more of his turnovers than his free-throw attempts when he faces continental opponents" (also holds under ratio of sums).
* E15a: "the same player keeps more of his turnovers than his 3-point percentage when he faces continental opponents" (estimator-sensitive: not disjoint under ratio of sums).
* E15a: "the same player keeps more of his turnovers than his free-throw percentage when he faces continental opponents" (estimator-sensitive: not disjoint under ratio of sums).
* E15a: "the same player keeps more of his 3-point attempts than his points when he faces continental opponents" (estimator-sensitive: not disjoint under ratio of sums).
* E15a: "the same player keeps more of his 3-point percentage than his points when he faces continental opponents" (also holds under ratio of sums).
* E15a: "the same player keeps more of his 3-point percentage than his assists when he faces continental opponents" (also holds under ratio of sums).
* E15a: "the same player keeps more of his 3-point percentage than his 3-point attempts when he faces continental opponents" (estimator-sensitive: not disjoint under ratio of sums).
* E15a: "the same player keeps more of his 3-point percentage than his free-throw attempts when he faces continental opponents" (also holds under ratio of sums).
* E15a: "the same player keeps more of his free-throw percentage than his points when he faces continental opponents" (also holds under ratio of sums).
* E15a: "the same player keeps more of his free-throw percentage than his assists when he faces continental opponents" (also holds under ratio of sums).
* E15a: "the same player keeps more of his free-throw percentage than his 3-point attempts when he faces continental opponents" (also holds under ratio of sums).
* E15a: "the same player keeps more of his free-throw percentage than his free-throw attempts when he faces continental opponents" (also holds under ratio of sums).
* E15b: descriptive only; no component is called "the" skill that travels.

## Caveats

* Blocks: 637 pairs had zero domestic blocks and cannot form a ratio; the ratio-of-sums column keeps them.
* 3-point attempts: 301 pairs had zero domestic attempts and are excluded the same way.
* E15a pairs are players who played both competitions in the same season; they are not a random sample of players, and the ratio describes those players.
* The percentages rest on smaller samples (≥ 20 attempts both sides: 3-point percentage n=411, free-throw percentage n=378). Destination reliability below the 0.40 floor: 3-point percentage.
* The λ10 fits here are single full fits on the 674 (descriptive), not walk-forward forecasts; no forecasting claim follows from them.

## Files

In `docs/research/artifacts/sloan-fullpaper-skills-2026-11/`:

* `summary.json`: gates, counts, licences.
* `e15a_retention.csv`: every E15a ratio (pooled, destination, source league) with intervals and counts.
* `e15a_licences.csv`: disjoint pooled pairs and the sentence each earns.
* `e15b_carryover.csv`: every E15b quantity with intervals.
* `e15b_source_offsets.csv`: λ10 offsets per component and source league.
* `skills_travel_figure.csv`: one row per component, ready for the 'which skills travel' chart.
* `generator-receipt.json`: provenance of the retained run.

Tests: `tests/test_scripts/test_sloan_fullpaper_skills.py`.
