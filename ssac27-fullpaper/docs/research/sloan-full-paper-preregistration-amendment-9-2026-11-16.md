# Amendment 9 to the SSAC27 full-paper pre-registration: the league-aware forecast against the plain baselines, with intervals (E28)

**Approval record.**

| | |
|---|---|
| Amends | `docs/research/sloan-full-paper-preregistration-2026-11-03.md`, as amended on 2026-11-04, 2026-11-05, 2026-11-11, 2026-11-12 and 2026-11-16 (Amendments 1 to 8) |
| Written | 2026-11-16, before the analysis below was implemented |
| Approved by | Amir, "Accept Amendment 8 as written and Accept Amendment 9 as written as long you think they are good", 2026-11-16. One sentence on the older seasons was added before the push; see "Changes after the draft" at the end |
| Basis | committed and pushed **alone**, before any implementation. Nothing below may be relaxed after a result is seen (METHOD.md §8) |

Everything in the 3 Nov pre-registration and in Amendments 1 to 8 stands. This amendment **adds** one exploratory analysis, E28. It changes no registered analysis, threshold, model, population or licence.

## Why this exists, in plain words

The paper's title is about one number per league. Its tables test translation factors against that number, but they never put an interval on what the number itself is worth. A reader must subtract two printed errors to find it.

E28 reports two comparisons with their uncertainty: the league-aware forecast against a player's history alone, and against a forecast that already knows the destination competition. The second is the plain measure of what the source league adds.

## What has already been seen (exposure disclosure)

* **Everything E28 uses is exposed.** The seasons 2020–2025 were examined before any registration, and the older seasons were scored under Amendment 7. E28 is therefore **exploratory**, and the paper labels it so.
* **Both point estimates are already known** by subtraction of printed errors: 3.096 − 2.924 = 0.172 EFF/36 against history, and 2.989 − 2.924 = 0.065 against the destination-aware forecast. On the older seasons printed in the paper the first is 2.862 − 2.830 = 0.032. **What is new is only their intervals**, their playing-time-weighted versions and the second comparison on the older seasons.
* **The analysis was prompted by a review of the paper** (15 November) in which three independent readers each asked for these intervals. It was not prompted by a look at the per-arrival differences, which have not been computed.

## Specification

| Field | Registered choice |
|---|---|
| Unit | One arrival: player × destination season |
| Population | (a) The 674 benchmark arrivals of 2020–2025. (b) The older-seasons arrivals, in the version the paper prints under Amendment 7's permission rule |
| Estimator | Paired differences in mean absolute error, EFF/36: G_H = MAE(`history_only`) − MAE(`source_ridge_10`); G_D = MAE(`history_destination_slope`) − MAE(`source_ridge_10`). Each unweighted and weighted by destination minutes |
| Null | Zero for each paired difference |
| Filter | None beyond each population's registered rules |
| Key | The registered key of each population (player × destination season) |
| Uncertainty | As registered: two-way clustered 95% intervals (player, destination club-season) |

## Analysis

* **E28a, the 674.** G_H and G_D with intervals, unweighted and weighted by destination minutes. Printed beside them without a licence: both by destination competition and by destination season, and the 80%-power detectable effect of each.
* **E28b, the older seasons.** G_H and G_D on the scored older arrivals, from the frozen older-season forecasts and the scored rows of the single Amendment 7 scoring run. No rule of that run is changed and nothing is re-scored. This is a second reading of outcomes that have been read once; the paper says so in the same sentence as the result. Both versions of the older-seasons test (with and without Spain's ACB) are computed in the same run, as under Amendment 7; the version the paper does not print is withheld under Amendment 7's permission rule, not for its result.
* **E28c, the margin in proportion.** The registered margin (2% of forecast error, 0.058 EFF/36) and the registered head-to-head interval, each divided by the point estimate of G_D on the 674. This is arithmetic on registered numbers and is descriptive.

No model is refitted. Forecasts are the committed walk-forward forecasts of the registered arms.

### What the paper may say

| Result | Interval | Wording |
|---|---|---|
| G_H on the 674 | above zero | "the league-aware forecast is more accurate than history alone by X EFF/36 (interval)" |
| | includes zero | "not distinguishable from history alone at this n" |
| G_D on the 674 | above zero | "once the destination is known, knowing the source league improves the forecast by X EFF/36 (interval)" |
| | includes zero | "once the destination is known, the source league's contribution (X EFF/36) is not distinguishable from zero at this n" |
| Weighted versions | any | printed beside the unweighted values; a weighted interval that includes zero is worded "not clearly above zero when weighted by playing time" |
| Older seasons | above zero | "… also on the older seasons" |
| | includes zero | "not detectable on the older seasons at this n", with n |
| E28c | n/a | "the margin is X% of what the source league adds"; if G_D's interval includes zero, the paper says that the margin cannot be scaled against an effect that is itself not distinguishable from zero |

* **Every number is reported whatever it shows**, in the main text for the 674 and in the older-seasons section for the older arrivals, labelled exploratory.
* **If G_D's interval on the 674 includes zero**, this qualifies the paper's headline. It goes to Amir before any writing, and then into the main text and the Limitations.
* E28 licenses no statement of equivalence and changes no registered sentence.

## Gates and negative controls

* **G28a.** From the committed inputs, the code reproduces the registered errors of the three arms (3.096, 2.989, 2.924 to the printed digits, and to 1e-9 against the committed summary) and the registered head-to-head contrast with its interval to 1e-9. **Negative control:** the same gate with one forecast column shifted by 0.01 must fail.
* **G28b.** On the older seasons, the code reproduces the three printed comparisons of the Amendment 7 extract to 1e-9 before it computes G_H and G_D. **Negative control:** the same gate on a row-shuffled outcome column must fail.

## Threats and their controls

| Threat | Control |
|---|---|
| Reused outcomes | exploratory label on every E28 number; the frozen 2026–27 test carries the same two comparisons as registered read-outs (Amendment 8, S1 and S2) |
| A comparison chosen because its answer is known to be favourable | the point estimates are disclosed above; both comparisons, both weightings and both populations are printed |
| Second reading of the older-seasons outcomes | stated with the result; no rule of the Amendment 7 run is changed |
| A result that weakens a paper claim | reported to Amir before any writing, then in the main text |

## Scope boundary: nothing pinned changes

No registered analysis, file, forecast or licence is changed. E28 is implemented in a new dated generator with a committed report script, run as a retained run from committed code.

## Changes after the draft

The draft that Amir read on 16 November had no sentence on the two versions of the older-seasons test. The sentence in E28b that both versions are computed and one is withheld under Amendment 7's rule was added before the push and before any implementation.
