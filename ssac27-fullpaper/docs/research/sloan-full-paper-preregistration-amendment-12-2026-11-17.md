# Amendment 12 to the SSAC27 full-paper pre-registration: the league numbers as a usable equation, and the forecast level weighted by playing time

**Approval record.**

| | |
|---|---|
| Amends | `docs/research/sloan-full-paper-preregistration-2026-11-03.md`, as amended on 2026-11-04, 2026-11-05, 2026-11-11, 2026-11-12 and 2026-11-16 (Amendments 1 to 11) |
| Written | 2026-11-17, before the paper text below was written |
| Approved by | Amir. On 16 November: "Go with your recommendations", which included a usable League Equivalents table with an equation or lookup grid and a worked two-candidate example. On 17 November: "add the weighted level" |
| Basis | committed and pushed **alone**, before any implementation. Nothing below may be relaxed after a result is seen (METHOD.md §8) |

Everything in the 3 Nov pre-registration and in Amendments 1 to 11 stands. This amendment adds **no analysis**. It fixes how two sets of already committed numbers are printed. It changes no registered analysis, threshold, model, population or licence.

## Why this exists, in plain words

1. **The paper's title promises one number per league, and the paper never prints those numbers.** It prints what they imply (the League Equivalents). A club cannot apply the model to its own candidates without the fitted equation. The coefficients have been in the committed output of the registered analysis E9 since 3 November.
2. **The paper says the forecasts run 0.47 EFF/36 low. Weighted by playing time they run about twice as low.** The run for Amendment 11 printed this in its rows for all arrivals. A club cares most about players who play, so the main text should say it.

## What has already been seen (exposure disclosure)

* **The coefficients.** Registered and committed on 3 November (E9), unchanged since.
* **A check made on 17 November before this amendment was written.** The coefficients were put into the model equation and compared with committed forecasts: the 20 reference forecasts of E9, the 20 League Equivalents, and the 3,478 frozen 2026-27 forecasts. All agree to 1e-9. This read forecasts only. No outcome was read, and no 2026-27 statistic.
* **The worked example.** Its two invented candidates are fixed below. Their forecasts were computed once during that check: history alone ranks candidate A first, and the league-aware forecast ranks candidate B first by less than 1 EFF/36. The example was chosen to show a disagreement; that is its purpose, and the paper says that the candidates are invented.
* **The weighted forecast level.** Seen in the Amendment 11 results (E29, rows for all arrivals): −0.96 EFF/36 for the league-aware forecast and −0.97 for the forecast that knows only the destination, both with intervals below zero.

## Specification

| Field | Registered choice |
|---|---|
| Unit | One arrival: player × destination season |
| Population | The training arrivals of the registered full fit (E9) for the equation; the 674 benchmark arrivals for the weighted forecast level |
| Estimator | None new. The equation is the registered league-aware model (`source_ridge_10`, full fit through 2025) with its committed coefficients. The weighted forecast level is the committed E29 mean error for all arrivals, weighted by destination minutes |
| Null | None; both items are descriptive |
| Filter | None beyond each population's registered rules |
| Key | The registered key of each population (player × destination season) |
| Uncertainty | For each league number, the committed 95% cluster-bootstrap interval of E9. For the weighted forecast level, the committed two-way clustered 95% interval of E29 |

## Part A: the league numbers as an equation (descriptive)

### What the paper prints

* **The equation**, with the committed coefficients rounded to three decimals:
  forecast = intercept + b1 × domestic rate + b2 × career rate + b3 × [domestic rate above career rate] + league number + EuroLeague × (c0 + c1 × domestic rate).
* **The ten league numbers**, one per source league, each with its committed interval, as a column of the League Equivalents table.
* **The rule for a player with no earlier season:** his career rate is set to his domestic rate, as in the frozen forecasts.
* **How far the rounded equation can be from the model:** the largest possible difference for domestic and career rates between 0 and 35 EFF/36, computed from the rounding errors alone.
* **A worked example with two invented candidates**, fixed here:
  * Candidate A: Germany (BBL), domestic rate 20, career rate 17.
  * Candidate B: Spain (ACB), domestic rate 16, career rate 16.
  * Destination: EuroCup.
  * Printed for each: the forecast of history alone (registered full fit of `history_only`, committed in E12) and the league-aware forecast, the gap between the two candidates under each, and the reading of that gap from the registered forecast-gap guide (E20) and the registered error bands (E8).
* A lookup grid of forecasts may be added in the appendix. It is computed from the same equation and nothing else.

### What the paper may say

* That the equation **is** the registered model, and that the League Equivalents are read off it.
* For the example, only what the registered guides license: which candidate each forecast ranks first, the size of the gap, the share of gaps of that size that were right (E20), and the width of the error band (E8).
* **Not allowed:** a recommendation to sign either candidate; any statement that a league number measures league strength (the registered wording stays: the numbers describe the players clubs sign from a league); any use of the equation outside EuroLeague and EuroCup arrivals from the ten leagues.
* The limits already in the paper are repeated beside the equation: the forecasts run low, the league numbers did not carry back to the older arrivals of two leagues (E28), and individual error bands are wide.

### Gates and negative controls

* **G30a.** The equation with the committed coefficients reproduces the 20 reference forecasts of E9, the 20 committed League Equivalents and all 3,478 frozen 2026-27 forecasts to 1e-9. **Negative control:** the same check with one coefficient shifted by 0.01 must fail.
* **G30b.** The printed bound on the rounding difference is recomputed from the printed coefficients. **Negative control:** the same check with a coefficient rounded to one decimal must exceed the printed bound.

## Part B: the forecast level weighted by playing time (descriptive)

### What the paper prints

| Result | Wording |
|---|---|
| Weighted mean error of the league-aware forecast on the 674, interval below zero | "weighted by playing time, the league-aware forecast is X EFF/36 below what arrivals delivered (interval)" |
| The same for the forecast that knows only the destination | "the forecast that knows only the destination shares this (X, interval)" |
| Either interval includes zero | not expected; if the committed numbers change, the sentence is withdrawn and the case goes to Amir |

* **Placement.** Beside the registered sentence on the forecast level (Amendment 3, E18a), which stays word for word: in the Results paragraph on forecast levels, in Limitations, and in the introduction's qualification.
* **The interval's method is named.** The registered unweighted sentence uses a cluster-bootstrap interval; this one uses a two-way clustered interval. The paper says so where it prints both.
* **No cause is given.** The paper does not say why the shortfall is larger for players who play more.
* The comparisons between forecasts are unaffected: every forecast shares the shortfall, and the paper already says so.

## Not part of this amendment

The same paper revision moves several results that are already registered and committed from the appendix into the main text, and replaces internal terms with plain words. That changes placement and wording only. No number is added by it, and every registered sentence stays word for word.

## Threats and their controls

| Threat | Control |
|---|---|
| The equation read as a measure of league strength | the registered caveat is printed beside it; the wording above |
| A printed equation that is not the model | G30a, including the frozen forecasts |
| Rounded coefficients giving a different answer | G30b and the printed bound |
| An example chosen to flatter the league table | the candidates are fixed here; the paper prints the gap guide's reading, which is close to a coin flip for small gaps |
| The weighted level quoted without its limits | descriptive label; interval method named; no cause |

## Scope boundary: nothing pinned changes

No registered analysis, file, forecast or licence is changed. No model is refitted and no outcome is read. The frozen 2026-27 forecasts are read only to check that the printed equation reproduces them.
