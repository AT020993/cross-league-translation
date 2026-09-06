# Prediction intervals for the translation projections — four families on rolling out-of-sample residuals

**Generated 2026-09-04 by `scripts/calibrate_prediction_intervals.py` from `walkforward_rows.parquet`; every number below is read from `intervals_summary.json`. Study C of `prelock-program-preregistration-2026-09-04.md` (ATI-2963).**

## Specification

| Choice | This study | Alternative considered |
|---|---|---|
| **Unit** | one walk-forward test row (player × destination season), point arm `per_league` | — |
| **Calibration** | rolling: fold s on rows of folds < s; selection folds [2022, 2023, 2024] | pooled calibration (rejected — leaks the fold into its own interval) |
| **Selection** | lowest pooled Winkler score inside the coverage band [0.9, 0.98]; ties within one cluster-bootstrap SE keep the simpler family | coverage alone (rejected — binomial SE ≈ 0.011 cannot separate families within ±0.02) |
| **Null / controls** | α = 0.5 must fail the band; calibration on the scored rows must over-cover | — |

## Pooled, selection folds

| family | n | coverage (SE) | mean width | Winkler (SE) |
|---|---:|---:|---:|---:|
| conformal | 312 | 0.955 (0.012) | 16.02 | 19.82 (1.28) |
| cqr | 312 | 0.942 (0.013) | 15.56 | 20.51 (1.42) |
| multiplier | 312 | 0.949 (0.012) | 17.03 | 21.90 (1.51) |
| normalised | 312 | 0.949 (0.012) | 16.30 | 20.26 (1.35) |

**Selected: `conformal`** — lowest Winkler inside the band. Eligible (inside the band): multiplier, conformal, normalised, cqr.

## Per fold

| family | fold | n | coverage | mean width | Winkler |
|---|---:|---:|---:|---:|---:|
| multiplier | 2022 | 106 | 0.943 | 16.58 | 20.23 |
| conformal | 2022 | 106 | 0.972 | 16.48 | 17.29 |
| normalised | 2022 | 106 | 0.962 | 16.32 | 17.99 |
| cqr | 2022 | 106 | 0.925 | 16.14 | 20.11 |
| multiplier | 2023 | 102 | 0.951 | 16.61 | 22.27 |
| conformal | 2023 | 102 | 0.922 | 15.30 | 20.68 |
| normalised | 2023 | 102 | 0.902 | 15.79 | 21.40 |
| cqr | 2023 | 102 | 0.941 | 15.24 | 21.18 |
| multiplier | 2024 | 104 | 0.952 | 17.91 | 23.25 |
| conformal | 2024 | 104 | 0.971 | 16.26 | 21.55 |
| normalised | 2024 | 104 | 0.981 | 16.79 | 21.46 |
| cqr | 2024 | 104 | 0.962 | 15.30 | 20.26 |

## Invariants and negative controls

* α = 0.5 conformal coverage 0.554 — fails the band: True.
* Calibrating on the rows being scored covers 0.962 vs 0.955 honest — the leak signature fires: True.
* The multiplier interval is 1.14 wide at a projection of 1 and 17.11 at 15: its width is a property of the point, not of the error.

## Recency-weighted sensitivity (half-life one season)

| family | fold | coverage | Winkler |
|---|---:|---:|---:|
| conformal | 2022 | 0.972 | 17.25 |
| normalised | 2022 | 0.962 | 18.09 |
| conformal | 2023 | 0.912 | 20.99 |
| normalised | 2023 | 0.902 | 21.40 |
| conformal | 2024 | 0.971 | 21.71 |
| normalised | 2024 | 0.981 | 21.91 |

## Confirmation fold 2025 (read once, after Amendment 8)

| family | n | coverage | mean width | Winkler |
|---|---:|---:|---:|---:|
| multiplier | 127 | 0.929 | 17.09 | 21.11 |
| conformal | 127 | 0.929 | 15.57 | 19.97 |
| normalised | 127 | 0.937 | 15.74 | 19.99 |
| cqr | 127 | 0.945 | 16.00 | 19.58 |

Selected family `conformal` on 2025: coverage 0.929, Winkler 19.97.

Reading, from the table: on the 2025 fold the selected family's coverage 0.929 sits inside the [0.90, 0.98] band; its Winkler beats the multiplier control by +1.14 (19.97 against 21.11); the lowest 2025 Winkler is cqr's (19.58); the selection was made on folds <= 2024 and does not move on one fold's read.

## What this licenses

The interval family the lock should carry is `conformal`, chosen on folds the 2026-27 fit never sees by a proper scoring rule, with the committed multiplier interval as the control. It licenses no claim about the point predictions.

## Scripts

* `scripts/calibrate_prediction_intervals.py` — everything above; `--render` rewrites this note from the artifact.
* `scripts/validate_translation_walkforward.py --rows-out` — the rows.
