# Amendment 11 to the SSAC27 full-paper pre-registration: where the league table missed on the older arrivals (E29)

**Approval record.**

| | |
|---|---|
| Amends | `docs/research/sloan-full-paper-preregistration-2026-11-03.md`, as amended on 2026-11-04, 2026-11-05, 2026-11-11, 2026-11-12 and 2026-11-16 (Amendments 1 to 10) |
| Written | 2026-11-16, before the analysis below was implemented |
| Approved by | Amir, "merge Amendment 10 and add the drift table", 2026-11-16. He was offered the table as a small descriptive appendix table with one sentence in the main text, at a cost of half a day, with the risk named: two leagues, and numbers that had partly been seen |
| Basis | committed and pushed **alone**, before any implementation. Nothing below may be relaxed after a result is seen (METHOD.md §8) |

Everything in the 3 Nov pre-registration and in Amendments 1 to 10 stands. This amendment **adds** one descriptive analysis, E29. It changes no registered analysis, threshold, model, population or licence.

## Why this exists, in plain words

E28 found that on the 180 older arrivals the league table did not help, and that weighted by playing time it did worse than knowing the destination alone (Amendments 9 and 10). A club reader will ask where the forecast went wrong.

E29 answers that question with one table. For each source league it shows three things: how far the league table moves the forecast, how far the forecast was from the outcome without the table, and how far with it. It shows them for the older arrivals and, for the same leagues, for the arrivals of 2020–2025.

E29 describes **where** the forecast missed. It does not show **why**.

## What has already been seen (exposure disclosure)

* **Every outcome E29 uses is exposed.** E29 is descriptive, and the paper labels it so.
* **Seen on the older arrivals, in one unregistered look after the E28 result** (disclosed in Amendment 10), for the version without Spain's ACB:
  * by source league: the number of arrivals, the mean move of the forecast made by the league table, the mean error of the destination-only forecast and of the league-aware forecast, and G_D unweighted and weighted by minutes;
  * the same by destination competition, and G_D by destination season.
  * In short: the table lowered the forecast for Adriatic arrivals by about 0.7 EFF/36 and for Israeli arrivals by about 0.4; without the table the Adriatic forecast was already about 0.35 too low and the Israeli forecast about 0.3 too high.
* **Seen on the arrivals of 2020–2025:** the paper's league-bias figure and table (each league's error measured against the average arrival), and the yearly refits of each league's equivalent.
* **Not seen:** any interval for the quantities below; their versions weighted by minutes; the three quantities by source league on the arrivals of 2020–2025 as E29 defines them (not centred on the average arrival); the change between the two periods; and any per-league number of the withheld version of the older-seasons test.
* **The analysis was prompted by the E28 result**, not by a look at the change between periods.

## Specification

| Field | Registered choice |
|---|---|
| Unit | One arrival: player × destination season |
| Population | (a) The older-seasons arrivals in the version the paper prints under Amendment 7's permission rule. (b) The 674 benchmark arrivals of 2020–2025. Rows: each source league of the printed older version, and all arrivals of each population |
| Estimator | Per source league and population: the mean **move**, forecast of `source_ridge_10` minus forecast of `history_destination_slope`; the mean **error without the table**, forecast of `history_destination_slope` minus outcome; the mean **error with the table**, forecast of `source_ridge_10` minus outcome. All in EFF/36, each unweighted and weighted by destination minutes. Per source league: the **change between periods**, the mean error without the table on the older arrivals minus the same on the arrivals of 2020–2025 |
| Null | Zero for each mean error and for the change between periods |
| Filter | None beyond each population's registered rules |
| Key | The registered key of each population (player × destination season) |
| Uncertainty | Two-way clustered 95% intervals (player, destination club-season), as registered. For the change between periods the two samples are treated as independent and the standard errors are combined in quadrature, with the smaller of the two degrees of freedom |

## Analysis

* **E29a, the older arrivals.** The three means with intervals, by source league and for all printed arrivals.
* **E29b, the arrivals of 2020–2025.** The same three means for the same source leagues and for all 674 arrivals, from the committed walk-forward forecasts.
* **E29c, the change between periods.** For each source league, the change in the mean error without the table, with its interval.

No model is refitted and nothing is re-scored. The older arrivals come from the frozen older-season forecasts and the scored rows of the single Amendment 7 scoring run. This is a further reading of outcomes that have been read; the paper says so.

Both versions of the older-seasons test are computed in the same run, as under Amendments 7 and 9. Every number that depends on the withheld version, including the row of its extra league, is withheld under Amendment 7's permission rule, not for its result.

### Three limits the paper states with the table

1. On the older arrivals the forecasts come from the model fitted on every season through 2025. On the arrivals of 2020–2025 each forecast comes from a model fitted on earlier seasons only.
2. The older source statistics come from the leagues' own box scores. The source statistics of 2020–2025 come from a different provider.
3. A mean error also carries the general level of the forecasts in that period. The rows for all arrivals are printed so that a reader can see that level.

### What the paper may say

| Result | Interval | Wording |
|---|---|---|
| Move, and the two errors, for one league on the older arrivals | any | "on the older arrivals the league table lowered [raised] the forecast for arrivals from L by X EFF/36; without the table the forecast was Y EFF/36 (interval) below [above] what they delivered, and with it Z (interval)" |
| Change between periods for one league | excludes zero | "against the forecast that knows only the destination, arrivals from L did better [worse] in 2008–2015 than in 2020–2025 by X EFF/36 (interval)" |
| | includes zero | "for arrivals from L the change between the two periods is not distinguishable from zero at this n (X EFF/36, interval)" |

* **The caveat travels with the result.** Next to any of these sentences the paper says: this shows where the forecast missed; it cannot separate a change in league strength from a change in which players clubs signed, in the data source or in the level of the forecasts.
* **"Consistent with league numbers that change over time"** may be written only if the change between periods excludes zero for at least one league. Otherwise the paper says that the table shows where the forecast missed and not why.
* **No statement of cause.** The paper does not write that a league was stronger or weaker in either period, and does not write "because".
* The registered table of yearly refits may be cited beside E29. It is already in the paper and nothing in it is computed again.
* **Placement.** The table goes in the appendix section on the older-seasons test, labelled descriptive. One sentence goes in the main-text subsection on the older seasons, after the E28 readings fixed by Amendment 10.
* **Every number is reported whatever it shows**, for every source league of the printed version.

## Gates and negative controls

* **G29a.** On the older arrivals, the code reproduces the four committed E28b differences (G_H and G_D, unweighted and weighted) to 1e-9 before it computes anything else. **Negative control:** the same gate on a row-shuffled outcome column must fail.
* **G29b.** On the 674, the code reproduces the committed errors of the two forecasts and the committed G_D with its interval to 1e-9. **Negative control:** the same gate with one forecast column shifted by 0.01 must fail.
* **G29c.** In each population the mean errors by source league, weighted by their numbers of arrivals, add up to the mean error of all arrivals, and the move equals the error with the table minus the error without it, both to 1e-9. **Negative control:** the same gate with one league's rows dropped must fail.
* **G29d.** No number of the withheld version appears in any committed output. **Negative control:** a planted withheld value must be caught.

## Threats and their controls

| Threat | Control |
|---|---|
| Reused outcomes, and quantities partly seen | descriptive label; the disclosure above; every league and both weightings printed |
| A cause read into a description | the caveat travels with the result; no statement of cause; "consistent with" only under the registered condition |
| The two periods differ in more than time | the three limits above are printed with the table |
| Small samples per league | intervals on every mean; the change between periods uses the smaller degrees of freedom |
| A withheld number leaking through a per-league row | G29d |

## Scope boundary: nothing pinned changes

No registered analysis, file, forecast or licence is changed. E29 is implemented in a new dated generator with a committed report script, run as a retained run from committed code. The readings of E28 and their wording (Amendments 9 and 10) stand as they are.
