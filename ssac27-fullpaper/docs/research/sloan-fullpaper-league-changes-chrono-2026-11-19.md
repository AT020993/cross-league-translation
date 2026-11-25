# SSAC27 full paper: the league-changes check with the stayer forecast fitted only on earlier seasons (E33)

Pre-registration: `docs/research/sloan-full-paper-preregistration-2026-11-03.md`, Amendment 22 (`docs/research/sloan-full-paper-preregistration-amendment-22-2026-11-19.md`, sha256 `4c234e20a8bf88dee7098ff3fe095de262d25a946413f4ff88fc0a908dad0ad0`). E33 is **exploratory**: the outcomes it uses had been read by the scoring run of E30. It changes no registered result, sentence or case of E30.

## Specification

| Field | Registered choice |
|---|---|
| Unit | One league change, as in Amendment 14. Each move has equal weight |
| Population | The 2,083 league changes of sensitivity (7) of E30: arrival seasons 2020 to 2025, with the table gap refitted only on arrivals before the season of the move; 1,165 players |
| Estimator | Step 1, for each arrival season t: ordinary least squares of the stayers' next-season rate on an intercept, x, h and a, on stayer pairs whose outcome season is before t. Step 2: ordinary least squares, with an intercept, of the league changers' unexplained change on the refitted gap |
| Null | Slope zero; for the difference from sensitivity (7): zero |
| Filter | Rows of the frozen file with a finite refitted gap |
| Key | `player_name` × `season_from`, the key of E30 |
| Uncertainty | The bootstrap of E30: 3,577 players resampled, 2,000 draws, seed 20261117, every stayer forecast refitted in every draw; percentile interval |

## Result

**Case: Same: the interval of the slope lies above zero and the interval of the difference includes zero.**

| Quantity | League changes | Slope | 95% interval |
|---|---|---|---|
| E33: stayer forecast fitted only on seasons before each move | 2,083 | 0.781 | 0.679 to 0.881 |
| Sensitivity (7), reproduced: stayer forecast fitted on all seasons | 2,083 | 0.786 | 0.684 to 0.885 |
| Difference, E33 minus sensitivity (7), in the same draws | 2,083 | −0.005 | −0.018 to 0.006 |
| E33 with one intercept per arrival season (secondary) | 2,083 | 0.780 | 0.679 to 0.879 |
| Sensitivity (7) with one intercept per arrival season (secondary) | 2,083 | 0.786 | 0.684 to 0.882 |

The standard deviation of the 2,000 differences is 0.0061; a difference of 0.017 would have been detected with 80% power (2.80 standard deviations). The interval of the difference comes from the same draws as the two slopes, so it does not rest on comparing two overlapping intervals.

## The stayer forecast by arrival season

| Arrival season | League changes | Players | Stayer pairs used | Latest stayer outcome season | Intercept | x | h | a |
|---|---|---|---|---|---|---|---|---|
| 2020 | 312 | 312 | 3,578 | 2019 | 4.144 | 0.626 | 0.114 | −0.521 |
| 2021 | 360 | 360 | 4,491 | 2020 | 4.306 | 0.644 | 0.097 | −0.757 |
| 2022 | 374 | 374 | 5,429 | 2021 | 4.422 | 0.622 | 0.108 | −0.809 |
| 2023 | 363 | 363 | 6,331 | 2022 | 4.212 | 0.630 | 0.112 | −0.787 |
| 2024 | 344 | 344 | 7,263 | 2023 | 4.139 | 0.647 | 0.104 | −0.858 |
| 2025 | 330 | 330 | 8,219 | 2024 | 4.063 | 0.647 | 0.110 | −0.834 |

## Gates

| Gate | Status | Negative control |
|---|---|---|
| G33a: every pinned file equals its sha256 | passed | one byte changed: rejected as required |
| G33b: the same 2,083 rows; the frozen and the scored file agree row by row | passed | row removed from frozen: rejected as required; row removed from scored: rejected as required |
| G33c: the code returns sensitivity (7) as retained, estimate and interval | passed | other seed: rejected as required |
| G33d: every stayer forecast uses only earlier outcome seasons | passed | season included: rejected as required |
| G33e: a planted slope of 1.0 on made-up outcomes is recovered | passed | gap shuffled across the made-up moves: interval −0.079 to 0.122, includes zero as required |

G33e in numbers: planted 1.0 came back as 1.029 (interval 0.931 to 1.122); planted 0.0 as −0.027 (interval −0.127 to 0.070). The made-up outcomes use a noise spread of 3.44 EFF/36, the residual spread of the stayer forecast.

## Order of events

1. Amendment 22 was written on 19 November 2026, after the league-changes test (E30) had been scored and its sensitivities seen. Amir accepted it; it was pushed alone (commit `1e69136a`, 18:28:29 UTC) and merged into `main` (pull request #3684, `22e3a414`).
2. The generator and its tests on made-up frames were written after that push and committed (commit `3c4ddc27`). Before the commit, the gates that read no outcome were tried once outside a retained run; they passed.
3. The gates were run as retained run `league-changes-chrono-gates-01` and their record committed (commit `f5b68ffc`). The run reads no rate of a league changer: of the scored file it reads the key, the season and the two leagues.
4. The row of Amendment 22 was added to the public hash list (public commit `b183a0b`, tag `registration-hashes-2026-11-19a`, 19 November 2026, about 19:10 UTC).
5. E33 was then run once, as retained run `league-changes-chrono-01`. No rule was changed after the result was seen, and no other variant of the check was run.

## What this does and does not show

* It removes the last overlap in time of sensitivity (7): neither the league table nor the stayer forecast of a league change uses a season at or after the move.
* It is a further reading of outcomes that had been read. It is exploratory and is labelled so wherever the paper prints it.
* It does not remove players who appear both among the arrivals that fit the table and among the league changers.
* Its interval holds the refitted table values fixed, as the interval of sensitivity (7) does.
* The limits of E30 stand: league changers are not a random sample, role and minutes change with a move, players are linked by name, and the box scores are the raw Proballers files.
