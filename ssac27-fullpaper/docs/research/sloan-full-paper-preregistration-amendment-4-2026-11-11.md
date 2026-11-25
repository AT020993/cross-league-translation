# Amendment 4 to the SSAC27 full-paper pre-registration: is the league pattern about the source league or the destination?

**Approval record.**

| | |
|---|---|
| Amends | `docs/research/sloan-full-paper-preregistration-2026-11-03.md`, as amended on 2026-11-04, 2026-11-05 and 2026-11-11 (Amendments 1 to 3) |
| Written | 2026-11-11, after the Amendment 3 results (E18–E23) were read and before the analysis below was implemented |
| Approved by | Amir, "Accept as written", 2026-11-11 |
| Basis | committed and pushed **alone**, before any implementation. Nothing below may be relaxed after a result is seen (METHOD.md §8) |

Everything in the 3 Nov pre-registration and in Amendments 1 to 3 stands. This amendment **adds** one analysis, E24. It changes no registered analysis, threshold, model, population or licence.

## Why this exists, in plain words

The paper says a league-blind forecast misjudges some source leagues, and that the league table flattens that pattern (E11, E18). But the league-blind forecast (history only) is blind to **two** things: the source league and the destination competition. Amendment 3 showed that it overrates EuroLeague arrivals by 1.24 EFF/36 and underrates EuroCup arrivals by 1.02. Leagues send different shares of their players to each competition. So part of each league's "bias" may come from where its players go, not from where they come from.

The paper's subject is the source league. E24 asks whether the league pattern is still there, and whether the league table still flattens it, once the forecast already knows the destination.

## What has already been seen (exposure disclosure)

* **All destination seasons 2017–2025 remain exposed.** E24 is **exploratory**, and the paper will say so.
* **Seen before this amendment was written:**
  * every Amendment 3 result, including the history-only and league-aware signed errors overall, by destination, by season and by source league, and the spread of league biases for those two forecasts (0.92 and 0.32);
  * the registered forecast error of the destination-aware forecast on the 674 (MAE 2.989, Table 1 of the paper).
* **Not computed or seen:**
  * any signed error of the destination-aware forecast, overall or by source league;
  * its spread of league biases;
  * how each source league's arrivals split between the EuroLeague and the EuroCup.
* **Destination season 2026 (2026-27) stays unexposed.**

## Specification

| Field | Registered choice |
|---|---|
| Unit | As in the 3 Nov pre-registration: one forecast = player × destination season, one continental destination. |
| Population | The 674 v10 target keys (2020–2025), pool A, recipe R1. |
| Estimator | Mean signed error (forecast − actual EFF/36) of the destination-aware forecast, overall and by source league; re-based league biases; the spread of league biases and its contrasts with the history-only and league-aware forecasts. |
| Null | Signed error = 0; re-based league bias = 0; spread contrast = 0. |
| Filter | v10 eligibility; targets fixed before scoring. |
| Key | `player_name` × `season_dest`; pools = destination competition × destination season. |
| Uncertainty | As registered and as in E18: cluster bootstrap over destination club-seasons within pools, 2,000 draws, seed 0, the same draws as E11 and E18. Holm adjustment across the 10 leagues. |

## Analysis

### E24. League biases of a forecast that knows the destination but not the source league

* **Forecasts.** Three registered forecasts, all already computed on the 674:
  * H: history only (blind to both leagues);
  * D: history plus the destination, intercept and slope (the "+ destination" row of Table 1). It knows the destination and not the source league;
  * O: the league-aware forecast (offsets λ10), which knows both.
* **E24a, level.** Mean signed error of D on all 674, by destination and by season, with intervals.
* **E24b, league biases of D.** For each of the 10 source leagues: the mean signed error of D, and the same re-based (minus the mean signed error of all 674, inside each bootstrap draw). Holm adjustment across the 10 leagues of the re-based two-sided bootstrap p-values.
* **E24c, spread.** S = the arrival-weighted root mean square of the 10 re-based league biases, as in E18.
  * **Primary contrast:** S(D) − S(O). What the league table removes once the destination is already known.
  * **Secondary contrast:** S(H) − S(D). What knowing the destination alone removes.
* **Printed.** For each source league, the number and share of its arrivals that went to the EuroLeague.
* **Licenses.**
  * Primary interval above zero: "once the forecast knows the destination, the league table still flattens the league pattern".
  * Primary interval including zero: "once the forecast knows the destination, the league pattern is not detectably flatter with the league table at this n". The paper then does **not** say that the league table flattens the league pattern without adding this sentence beside it.
  * Secondary interval above zero: "part of the league pattern of a league-blind forecast reflects which competition a league's players join".
  * Per league, Holm-adjusted p < 0.05 on the re-based bias of D: "measured against the average arrival, a forecast that knows the destination but not the source league underrates (overrates) arrivals from L by X EFF/36". Otherwise: "not distinguishable at this n".
  * Whatever E24 shows, the paper states that the history-only forecast is blind to both the source league and the destination.

## Gates and negative controls

| Gate | Pass rule | Negative control |
|---|---|---|
| G24a | for H and O, the league errors, re-based biases, their intervals and the spreads reproduce the Amendment 3 E18 outputs to 1e-9 (same draws) | comparing D with the E18 values of H must fail |
| G24b | D's forecast error on the 674 reproduces the registered Table 1 value to 1e-9 | a shifted forecast must fail |

## Threats and their controls

| Threat | Control |
|---|---|
| Reused 2020–2025 outcomes | exploratory label; P1 and P1-late stay the confirmatory tests |
| A check added after seeing results | this amendment is dated after the E18 results and says so; the arm, the contrasts and the licences are fixed above |
| A null read as "no effect" | null licences are worded "not detectably … at this n"; the bootstrap standard error and the 80%-power detectable difference are printed |
| A result that weakens a paper claim | reported in the main text; the claim is reworded, never dropped silently; reported to Amir before any writing |

## Scope boundary

Nothing pinned changes. E24 is implemented in a new dated generator with a committed report script. The retained run goes to `/Users/amir/Projects/cv_basketball_archive/research-runs/sloan-fullpaper/` from committed code.

## Timeline

| Date | Step |
|---|---|
| 11 Nov | this amendment approved and pushed alone |
| by 13 Nov | E24 result |
| 19–20 Nov | paper re-rendered; analysis lock |
