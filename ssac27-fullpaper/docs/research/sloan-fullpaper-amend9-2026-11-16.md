# SSAC27 full paper: Amendment 9 results (E28)

**EXPLORATORY.** Destination seasons 2020-2025 had been examined before any registration, and the older seasons had been scored once under Amendment 7. Only the frozen 2026-27 test (P1) is confirmatory. Every number below is formatted by `scripts/report_sloan_fullpaper_amend9.py` from committed run outputs; every quoted result sentence is the generator's registered wording.

Pre-registration: `docs/research/sloan-full-paper-preregistration-amendment-9-2026-11-16.md`, pushed alone before its generator existed.

## What E28 asks

The paper's title is about one number per league. E28 puts an interval on what that number is worth. It compares the league-aware forecast with two plainer forecasts on the same arrivals: a player's history alone (G_H), and a forecast that knows the destination competition but not the source league (G_D). G_D is the plain measure of what the source league adds. A positive difference means the league-aware forecast had the smaller error.

## Results in plain words

- On the 674 the league-aware forecast was more accurate against history alone by 0.172 EFF/36 (interval 0.096 to 0.248).
- On the 674, weighted by destination minutes, the league-aware forecast was more accurate against history alone by 0.136 EFF/36 (interval 0.046 to 0.226).
- On the 674 the league-aware forecast was more accurate against the forecast that knows only the destination by 0.065 EFF/36 (interval 0.014 to 0.117).
- On the 674, weighted by destination minutes, the league-aware forecast was more accurate against the forecast that knows only the destination by 0.073 EFF/36 (interval 0.010 to 0.136).
- On the 180 older arrivals the league-aware forecast was more accurate against history alone by 0.033 EFF/36 (interval −0.099 to 0.164), an interval that includes zero; the smallest difference this sample could detect with 80% power is 0.188.
- On the 180 older arrivals, weighted by destination minutes, the league-aware forecast was less accurate against history alone by 0.118 EFF/36 (interval −0.276 to 0.039), an interval that includes zero; the smallest difference this sample could detect with 80% power is 0.225.
- On the 180 older arrivals the league-aware forecast was less accurate against the forecast that knows only the destination by 0.067 EFF/36 (interval −0.144 to 0.010), an interval that includes zero; the smallest difference this sample could detect with 80% power is 0.110.
- On the 180 older arrivals, weighted by destination minutes, the league-aware forecast was **less** accurate against the forecast that knows only the destination by 0.129 EFF/36 (interval −0.209 to −0.048).
- **A result outside the registered wording:** G_D, weighted by destination minutes, on the older seasons. Amendment 9 registered wording only for intervals above zero or including zero. A result that weakens a paper claim goes to Amir before any writing, and then into the main text.

## Specification

| Field | Registered choice |
|---|---|
| Unit | One arrival: player × destination season. |
| Population | (a) The 674 benchmark arrivals of 2020-2025 (v10 target keys, pool A). (b) The older-seasons arrivals of Amendment 7, in the version without Spain's ACB: Adriatic league and Israel (the version the paper prints), n = 180. |
| Estimator | Paired differences in mean absolute error, EFF/36: G_H = MAE(history_only) - MAE(source_ridge_10); G_D = MAE(history_destination_slope) - MAE(source_ridge_10). Each unweighted and weighted by destination minutes. No model is refitted and nothing is re-scored. |
| Null | Zero for each paired difference. |
| Filter | None beyond each population's registered rules. |
| Key | `player_name` × `season_dest` on the 674; API person code × destination season on the older seasons. |
| Uncertainty | Two-way clustered 95% interval (player, destination club-season), Student t with min(clusters) - 1 degrees of freedom. Detectable effect with 80% power: (t(0.975, df) + t(0.80, df)) x SE, the registered formula of the recipes track. |

## What had been seen

Before Amendment 9 was registered:
- the registered errors of the three forecasts on the 674 (3.096, 2.989, 2.924), so both point estimates by subtraction (0.172 and 0.065 EFF/36)
- the minutes-weighted errors of the history-only and league-aware forecasts on the 674 (Amendment 1, E17), so the weighted point estimate of G_H by subtraction
- every Amendment 7 comparison on the older seasons, in both versions, and the errors of the history-only and league-aware forecasts there (so G_H's point estimate by subtraction)
- that three readers of the paper asked for these intervals (review of 15 November)

Not seen before this run:
- any interval of G_H or G_D
- the minutes-weighted G_D, and the interval of the minutes-weighted G_H
- G_D on the older seasons, in either version
- either difference by destination competition or by destination season
- the per-arrival differences

## Gates

| Gate | Status | Largest difference | Negative control |
|---|---|---|---|
| E28c_margin | passed | 0.0e+00 | rejected as required |
| G0 | passed | 1.3e-15 | rejected as required |
| G28a | passed | 0.0e+00 | rejected as required |
| G28b | passed | 2.2e-16 | rejected as required |
| frozen_forecasts | passed | 3.6e-15 | rejected as required |
| no_withheld_value | passed | n/a | rejected as required |
| scope | passed | n/a | rejected as required |

G28a reproduces the registered errors of the three forecasts to the printed digits and to 1e-9, the registered head-to-head with its interval, and the committed minutes-weighted head-to-head; its negative control shifts one forecast column by 0.01. G28b reproduces the three printed comparisons of the Amendment 7 extract before G_H and G_D are computed; its negative control shuffles the outcome column.

## E28a: the 674 benchmark arrivals

| Difference in MAE | Weighting | n | MAE of the first forecast | MAE of the league-aware forecast | Difference, EFF/36 | 95% interval | Detectable with 80% power | Reading |
|---|---|---|---|---|---|---|---|---|
| G_H: history alone minus league-aware | Unweighted | 674 | 3.096 | 2.924 | +0.172 | 0.096 to 0.248 | 0.108 | above zero |
| G_H: history alone minus league-aware | Weighted by destination minutes | 674 | 2.892 | 2.756 | +0.136 | 0.046 to 0.226 | 0.128 | above zero |
| G_D: history + destination minus league-aware | Unweighted | 674 | 2.989 | 2.924 | +0.065 | 0.014 to 0.117 | 0.073 | above zero |
| G_D: history + destination minus league-aware | Weighted by destination minutes | 674 | 2.829 | 2.756 | +0.073 | 0.010 to 0.136 | 0.091 | above zero |

Registered wording:

- G_H, unweighted: "the league-aware forecast is more accurate than history alone by 0.172 EFF/36 (interval 0.096 to 0.248)".
- G_H, weighted by destination minutes: interval above zero; printed beside the unweighted value, with no further registered wording.
- G_D, unweighted: "once the destination is known, knowing the source league improves the forecast by 0.065 EFF/36 (interval 0.014 to 0.117)".
- G_D, weighted by destination minutes: interval above zero; printed beside the unweighted value, with no further registered wording.

### By destination competition (printed without a licence)

Each cell: difference (95% interval); detectable effect with 80% power. These subsets are small and carry no licence.

| Destination competition | n | G_H, unweighted | G_H, weighted | G_D, unweighted | G_D, weighted |
|---|---|---|---|---|---|
| EuroLeague | 194 | +0.241 (0.051 to 0.431); 0.271 | +0.034 (−0.181 to 0.250); 0.307 | +0.119 (0.007 to 0.230); 0.159 | +0.149 (0.016 to 0.283); 0.190 |
| EuroCup | 480 | +0.144 (0.070 to 0.218); 0.106 | +0.186 (0.104 to 0.268); 0.117 | +0.044 (−0.013 to 0.101); 0.082 | +0.035 (−0.034 to 0.105); 0.099 |

### By destination season (printed without a licence)

| Destination season | n | G_H, unweighted | G_H, weighted | G_D, unweighted | G_D, weighted |
|---|---|---|---|---|---|
| 2020 | 134 | +0.185 (0.033 to 0.336); 0.215 | +0.201 (0.031 to 0.370); 0.241 | +0.048 (−0.047 to 0.144); 0.135 | +0.086 (−0.018 to 0.190); 0.147 |
| 2021 | 101 | +0.111 (−0.093 to 0.314); 0.289 | +0.121 (−0.125 to 0.367); 0.349 | +0.018 (−0.119 to 0.154); 0.193 | +0.054 (−0.110 to 0.217); 0.233 |
| 2022 | 106 | +0.344 (0.183 to 0.505); 0.228 | +0.323 (0.139 to 0.507); 0.261 | +0.176 (0.054 to 0.299); 0.174 | +0.206 (0.067 to 0.344); 0.196 |
| 2023 | 102 | +0.195 (−0.028 to 0.418); 0.316 | +0.131 (−0.123 to 0.386); 0.361 | +0.082 (−0.046 to 0.210); 0.181 | +0.092 (−0.058 to 0.242); 0.212 |
| 2024 | 104 | +0.151 (−0.082 to 0.384); 0.331 | +0.076 (−0.182 to 0.334); 0.366 | +0.108 (−0.033 to 0.248); 0.199 | +0.084 (−0.087 to 0.255); 0.243 |
| 2025 | 127 | +0.063 (−0.118 to 0.244); 0.257 | −0.024 (−0.248 to 0.200); 0.318 | −0.019 (−0.159 to 0.121); 0.198 | −0.060 (−0.247 to 0.126); 0.264 |

## E28b: the older seasons (180 arrivals)

Printed here: the version without Spain's ACB: Adriatic league and Israel. The older-seasons outcomes were read once, in the single Amendment 7 scoring run; E28b is a second reading of them. No rule of that run is changed and nothing is re-scored.

| Difference in MAE | Weighting | n | MAE of the first forecast | MAE of the league-aware forecast | Difference, EFF/36 | 95% interval | Detectable with 80% power | Reading |
|---|---|---|---|---|---|---|---|---|
| G_H: history alone minus league-aware | Unweighted | 180 | 2.862 | 2.830 | +0.033 | −0.099 to 0.164 | 0.188 | includes zero |
| G_H: history alone minus league-aware | Weighted by destination minutes | 180 | 2.630 | 2.749 | −0.118 | −0.276 to 0.039 | 0.225 | includes zero |
| G_D: history + destination minus league-aware | Unweighted | 180 | 2.763 | 2.830 | −0.067 | −0.144 to 0.010 | 0.110 | includes zero |
| G_D: history + destination minus league-aware | Weighted by destination minutes | 180 | 2.620 | 2.749 | −0.129 | −0.209 to −0.048 | 0.114 | below zero |

Registered wording:

- G_H, unweighted: "not detectable on the older seasons at this n (n = 180)".
- G_H, weighted by destination minutes: "not clearly above zero when weighted by playing time".
- G_D, unweighted: "not detectable on the older seasons at this n (n = 180)".
- G_D, weighted by destination minutes: the interval is below zero. **Amendment 9 registers no wording for this reading; it goes to Amir before any writing.**

Both versions of the older-seasons test were computed in this run. The other version (V-all) is withheld, not for its result: ACB's written permission had not arrived (Amendment 7's permission rule). Nothing from it is in this note or in any committed file.

## E28c: the margin in proportion (descriptive)

| Registered quantity | EFF/36 | Divided by G_D on the 674 |
|---|---|---|
| registered margin (2% of forecast error) | 0.058 | 89% |
| registered head-to-head interval, lower end | −0.027 | −42% |
| registered head-to-head interval, upper end | 0.049 | 75% |

- G_D on the 674 is 0.065 EFF/36 (interval 0.014 to 0.117).
- Registered wording: "the margin is 89% of what the source league adds".
- This is arithmetic on registered numbers. It licenses no statement of equivalence and changes no registered sentence.

## Limits

- Every outcome used here had been seen. The frozen 2026-27 test carries the same two comparisons as registered read-outs (Amendment 8).
- The older-seasons result is a second reading of outcomes read once, on one version of the test.
- The by-competition and by-season cells are small subsets, shown for transparency. No claim rests on them.
- An interval that includes zero is not evidence of no difference: the detectable effect beside it says how large a difference this sample could have found.

## Order of events

1. Amendment 9 was written on 16 November 2026, accepted by Amir and pushed alone (commit `3c915869c`) before any E28 code existed.
2. The generator was written. Before it was committed it was run on the staged inputs outside the retained-run machinery, to check that the gates execute. Two faults were fixed after that: a gate record that could not be built (a repeated argument name), and a gate record that would have carried the row count of the withheld version into the public summary. Neither fix changes an estimate, an interval, a gate threshold or a rule.
3. The generator was committed (commit `043285f7c`) and run once as retained run `research-runs/sloan-fullpaper/amend9-01` from the clean committed tree. The run finished with status complete; every gate passed and every negative control was rejected as required. No retained run of the generator failed and none was repeated.
4. No specification choice was made or changed after a result was seen. Every difference and interval the run produced for the printed version is in this note; standard errors and p-values are in the committed CSV tables.
5. This note is rendered by `scripts/report_sloan_fullpaper_amend9.py` from the committed outputs, in its own retained run.

## Reproduction

- Generator `scripts/sloan_fullpaper_amend9.py` (commit `043285f7c`, sha256 `35a5376769b06c12…`), amendment commit `3c915869c` (file sha256 `6dc8356d56538dcd…`), retained run `research-runs/sloan-fullpaper/amend9-01`, 13 input files, 2,575 code files, status complete.
- Inputs: the pinned v10 pairs and cohort (pool A), the committed summaries of the recipes and Amendment 1 runs, the committed scored rows and summary of the Amendment 7 scoring run, the Amendment 7 paper extract, the release flag, and the frozen older-season forecasts (sha256 `1d3e3bfb9d08b9d0…`). The run recorded 1 output file that is not committed: the older-seasons version the paper does not print stays in the retained run (Amendment 7's permission rule); its file and hash are not committed.
