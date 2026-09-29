# V10 numerical and exposure supplement

Generated from frozen v9 evidence and the registered v10 comparison. Exploratory; not independent confirmation.

## Original benchmark and error diagnostics

All tables below use 674 forecast keys common to all four factor pools and all registered scenarios. Positive differences favor adding adjustment. These corrected-source values differ slightly from the historical-input benchmarks in v8; the forecast keys are unchanged. For the corrected reference, MAE falls from 2.989 to 2.940: 0.049 EFF/36 (conditional 95% interval [-0.013, 0.111]), or 1.64% of baseline MAE.

| Model | MAE | RMSE | Bias | 90th abs. error |
| --- | --- | --- | --- | --- |
| History only | 3.096 | 3.953 | -0.369 | 6.426 |
| History + adjustment | 2.935 | 3.767 | -0.561 | 5.909 |
| History + destination | 2.991 | 3.830 | -0.439 | 6.272 |
| History + destination slope | 2.989 | 3.828 | -0.443 | 6.281 |
| Destination slope + adjustment | 2.940 | 3.777 | -0.579 | 6.022 |
| Source offsets (1) | 2.928 | 3.750 | -0.479 | 6.054 |
| Source offsets (1) + adjustment | 2.932 | 3.757 | -0.554 | 5.917 |
| Source offsets (10) | 2.924 | 3.746 | -0.472 | 6.063 |
| Source offsets (10) + adjustment | 2.926 | 3.752 | -0.557 | 5.916 |
| Source offsets (100) | 2.942 | 3.772 | -0.456 | 6.194 |
| Source offsets (100) + adjustment | 2.929 | 3.760 | -0.572 | 5.959 |

| Source-offset penalty | Additional MAE improvement | Conditional 95% interval |
| --- | --- | --- |
| 1 | -0.004 | [-0.026, 0.018] |
| 10 | -0.002 | [-0.028, 0.024] |
| 100 | 0.014 | [-0.030, 0.058] |

## Source-offset increments in every factor pool

| Factor pool | Penalty | Improvement | Player/club-season interval | Player/season interval |
| --- | --- | --- | --- | --- |
| A. Full corrected pool | 1 | -0.004 | [-0.026, 0.018] | [-0.015, 0.006] |
| A. Full corrected pool | 10 | -0.002 | [-0.028, 0.024] | [-0.017, 0.014] |
| A. Full corrected pool | 100 | 0.014 | [-0.030, 0.058] | [-0.023, 0.050] |
| B. Verified; full-season rates | 1 | -0.006 | [-0.011, -0.001] | [-0.015, 0.002] |
| B. Verified; full-season rates | 10 | -0.007 | [-0.012, -0.002] | [-0.013, 0.000] |
| B. Verified; full-season rates | 100 | -0.009 | [-0.017, -0.001] | [-0.016, -0.002] |
| C. Overlap keys; full-season rates | 1 | -0.006 | [-0.011, -0.001] | [-0.015, 0.002] |
| C. Overlap keys; full-season rates | 10 | -0.006 | [-0.012, -0.001] | [-0.014, 0.001] |
| C. Overlap keys; full-season rates | 100 | -0.008 | [-0.016, -0.000] | [-0.015, -0.001] |
| D. Overlap-window rates | 1 | -0.005 | [-0.017, 0.007] | [-0.020, 0.010] |
| D. Overlap-window rates | 10 | -0.005 | [-0.017, 0.007] | [-0.021, 0.011] |
| D. Overlap-window rates | 100 | -0.006 | [-0.021, 0.008] | [-0.029, 0.016] |

## Factor-pool transitions and original refits

| Factor pool | Pairs | Forecasts | Fallbacks | MAE improvement |
| --- | --- | --- | --- | --- |
| A: corrected full pool | 4074 | 674 | 108 | 0.049 |
| B: verified, full season | 1537 | 674 | 556 | -0.008 |
| C: overlap keys, full season | 1463 | 674 | 561 | -0.007 |
| D: overlap-window rates | 1463 | 674 | 561 | -0.005 |

| Step | Adjusted MAE reduction | Unchanged fallback contribution | Changed fallback contribution |
| --- | --- | --- | --- |
| A to B | -0.057 | -0.034 | -0.023 |
| B to C | 0.001 | 0.001 | 0.000 |
| C to D | 0.002 | 0.002 | 0.000 |

Moving from A to B changes adjusted-model MAE by 0.057; trimming C to D changes it by -0.002. The reference reversal is already present before common-window trimming. This locates the larger sensitivity in verified-population selection and estimation support jointly; it does not separate those two mechanisms.

The transition contributions sum to the step's total adjusted-model MAE change. Positive values mean lower error in the later pool. They describe which rows account for the change, not why those rows changed. Rounding can hide small contributions; the numerical companion retains full precision.

| Factor pool | Reference conditional interval | Season-omission range | Seed range |
| --- | --- | --- | --- |
| A: corrected full pool | [-0.013, 0.111] | [0.018, 0.049] | [0.049, 0.050] |
| B: verified, full season | [-0.022, 0.005] | [-0.015, -0.003] | [-0.009, -0.008] |
| C: overlap keys, full season | [-0.019, 0.005] | [-0.012, -0.002] | [-0.007, -0.007] |
| D: overlap-window rates | [-0.024, 0.013] | [-0.023, -0.001] | [-0.006, -0.005] |

## Original seasonal and destination errors

In the corrected reference, adjustment improves absolute error for 52.7% of forecasts, worsens it for 47.3% and ties for 0.0% (tolerance 1e-12). Mean signed error changes from -0.443 to -0.579; negative values indicate underprediction. Median absolute error changes from 2.481 to 2.450.

| Season / destination | n | MAE improvement | Contribution to total |
| --- | --- | --- | --- |
| 2020 | 134 | 0.044 | 0.009 |
| 2021 | 101 | 0.041 | 0.006 |
| 2022 | 106 | 0.162 | 0.026 |
| 2023 | 102 | 0.022 | 0.003 |
| 2024 | 104 | 0.076 | 0.012 |
| 2025 | 127 | -0.033 | -0.006 |
| eurocup | 480 | 0.053 | 0.038 |
| euroleague | 194 | 0.039 | 0.011 |

Season contributions sum to the overall improvement; destination contributions separately sum to it. They must not be summed across both partitions.

## Outcome-blind worked examples

**Bonzie Colson, destination season 2022 (median change).** turkey-bsl to euroleague; information cutoff: before destination season 2022. Source rate 21.538; earlier-history rate 22.347; factor 0.839; lag correction 0.936; translated feature 16.910. Fallback: False; reliable cell (75-pair rule): True.

| Forecast information | Forecast EFF/36 |
| --- | --- |
| History only | 18.095 |
| History + adjustment | 16.358 |
| History + destination | 16.952 |
| History + destination slope | 16.864 |
| Destination slope + adjustment | 16.420 |
| Source offsets (1) | 16.772 |
| Source offsets (1) + adjustment | 16.642 |
| Source offsets (10) | 16.766 |
| Source offsets (10) + adjustment | 16.602 |
| Source offsets (100) | 16.781 |
| Source offsets (100) + adjustment | 16.482 |

Observed destination outcome, shown after selection: **18.969 EFF/36**.

**Nick Weiler-Babb, destination season 2020 (fallback median change).** germany-bbl to euroleague; information cutoff: before destination season 2020. Source rate 17.409; earlier-history rate unavailable; factor 0.841; lag correction 0.948; translated feature 13.873. Fallback: True; reliable cell (75-pair rule): False. History is missing; the regression history input falls back to the source rate.

| Forecast information | Forecast EFF/36 |
| --- | --- |
| History only | 15.505 |
| History + adjustment | 14.362 |
| History + destination | 14.584 |
| History + destination slope | 14.554 |
| Destination slope + adjustment | 14.316 |
| Source offsets (1) | 13.548 |
| Source offsets (1) + adjustment | 13.713 |
| Source offsets (10) | 13.675 |
| Source offsets (10) + adjustment | 13.795 |
| Source offsets (100) | 14.189 |
| Source offsets (100) + adjustment | 14.107 |

Observed destination outcome, shown after selection: **12.315 EFF/36**.

## Every new reference arm

### A. Full corrected pool

| Arm | MAE | RMSE | Bias | Median absolute error | 90th absolute error |
| --- | --- | --- | --- | --- | --- |
| cell_slope_1 | 3.017 | 3.841 | -0.440 | 2.496 | 6.190 |
| cell_slope_1_scheduled | 3.024 | 3.856 | -0.539 | 2.530 | 6.268 |
| cell_slope_10 | 2.993 | 3.818 | -0.453 | 2.463 | 6.139 |
| cell_slope_10_scheduled | 2.998 | 3.831 | -0.542 | 2.546 | 6.304 |
| cell_slope_100 | 2.957 | 3.780 | -0.460 | 2.444 | 6.091 |
| cell_slope_100_scheduled | 2.958 | 3.788 | -0.559 | 2.483 | 6.134 |

| Penalty | Primary interval | Player/season interval |
| --- | --- | --- |
| 1 | [-0.033, 0.019] | [-0.029, 0.015] |
| 10 | [-0.029, 0.019] | [-0.024, 0.014] |
| 100 | [-0.029, 0.027] | [-0.021, 0.020] |

| Penalty | Improved (%) | Worsened (%) | Tied (%) |
| --- | --- | --- | --- |
| 1 | 49.7 | 50.3 | 0.0 |
| 10 | 50.1 | 49.9 | 0.0 |
| 100 | 51.0 | 49.0 | 0.0 |

| Penalty | by season | n | Mean improvement | Contribution |
| --- | --- | --- | --- | --- |
| 1 | 2020 | 134 | -0.021 | -0.004 |
| 1 | 2021 | 101 | -0.039 | -0.006 |
| 1 | 2022 | 106 | 0.003 | 0.000 |
| 1 | 2023 | 102 | -0.002 | -0.000 |
| 1 | 2024 | 104 | 0.026 | 0.004 |
| 1 | 2025 | 127 | -0.006 | -0.001 |
| 10 | 2020 | 134 | -0.009 | -0.002 |
| 10 | 2021 | 101 | -0.037 | -0.006 |
| 10 | 2022 | 106 | 0.002 | 0.000 |
| 10 | 2023 | 102 | -0.007 | -0.001 |
| 10 | 2024 | 104 | 0.023 | 0.004 |
| 10 | 2025 | 127 | -0.004 | -0.001 |
| 100 | 2020 | 134 | 0.008 | 0.002 |
| 100 | 2021 | 101 | -0.033 | -0.005 |
| 100 | 2022 | 106 | 0.011 | 0.002 |
| 100 | 2023 | 102 | -0.016 | -0.002 |
| 100 | 2024 | 104 | 0.026 | 0.004 |
| 100 | 2025 | 127 | -0.005 | -0.001 |

| Penalty | by destination | n | Mean improvement | Contribution |
| --- | --- | --- | --- | --- |
| 1 | eurocup | 480 | -0.012 | -0.009 |
| 1 | euroleague | 194 | 0.006 | 0.002 |
| 10 | eurocup | 480 | -0.007 | -0.005 |
| 10 | euroleague | 194 | -0.001 | -0.000 |
| 100 | eurocup | 480 | -0.002 | -0.002 |
| 100 | euroleague | 194 | 0.003 | 0.001 |

### B. Verified; full-season rates

| Arm | MAE | RMSE | Bias | Median absolute error | 90th absolute error |
| --- | --- | --- | --- | --- | --- |
| cell_slope_1 | 3.017 | 3.841 | -0.440 | 2.496 | 6.190 |
| cell_slope_1_scheduled | 3.029 | 3.859 | -0.431 | 2.498 | 6.200 |
| cell_slope_10 | 2.993 | 3.818 | -0.453 | 2.463 | 6.139 |
| cell_slope_10_scheduled | 3.003 | 3.833 | -0.445 | 2.478 | 6.173 |
| cell_slope_100 | 2.957 | 3.780 | -0.460 | 2.444 | 6.091 |
| cell_slope_100_scheduled | 2.965 | 3.790 | -0.454 | 2.427 | 6.068 |

| Penalty | Primary interval | Player/season interval |
| --- | --- | --- |
| 1 | [-0.024, -0.001] | [-0.031, 0.006] |
| 10 | [-0.020, 0.000] | [-0.025, 0.004] |
| 100 | [-0.015, -0.001] | [-0.017, 0.002] |

| Penalty | Improved (%) | Worsened (%) | Tied (%) |
| --- | --- | --- | --- |
| 1 | 49.9 | 50.1 | 0.0 |
| 10 | 49.9 | 50.1 | 0.0 |
| 100 | 49.6 | 50.4 | 0.0 |

| Penalty | by season | n | Mean improvement | Contribution |
| --- | --- | --- | --- | --- |
| 1 | 2020 | 134 | -0.034 | -0.007 |
| 1 | 2021 | 101 | -0.007 | -0.001 |
| 1 | 2022 | 106 | -0.032 | -0.005 |
| 1 | 2023 | 102 | -0.000 | -0.000 |
| 1 | 2024 | 104 | -0.002 | -0.000 |
| 1 | 2025 | 127 | 0.003 | 0.001 |
| 10 | 2020 | 134 | -0.027 | -0.005 |
| 10 | 2021 | 101 | -0.005 | -0.001 |
| 10 | 2022 | 106 | -0.025 | -0.004 |
| 10 | 2023 | 102 | -0.001 | -0.000 |
| 10 | 2024 | 104 | -0.002 | -0.000 |
| 10 | 2025 | 127 | 0.002 | 0.000 |
| 100 | 2020 | 134 | -0.017 | -0.003 |
| 100 | 2021 | 101 | -0.003 | -0.000 |
| 100 | 2022 | 106 | -0.020 | -0.003 |
| 100 | 2023 | 102 | -0.003 | -0.001 |
| 100 | 2024 | 104 | -0.004 | -0.001 |
| 100 | 2025 | 127 | 0.001 | 0.000 |

| Penalty | by destination | n | Mean improvement | Contribution |
| --- | --- | --- | --- | --- |
| 1 | eurocup | 480 | -0.006 | -0.004 |
| 1 | euroleague | 194 | -0.029 | -0.008 |
| 10 | eurocup | 480 | -0.004 | -0.003 |
| 10 | euroleague | 194 | -0.026 | -0.007 |
| 100 | eurocup | 480 | -0.002 | -0.001 |
| 100 | euroleague | 194 | -0.023 | -0.006 |

### C. Overlap keys; full-season rates

| Arm | MAE | RMSE | Bias | Median absolute error | 90th absolute error |
| --- | --- | --- | --- | --- | --- |
| cell_slope_1 | 3.017 | 3.841 | -0.440 | 2.496 | 6.190 |
| cell_slope_1_scheduled | 3.029 | 3.858 | -0.430 | 2.501 | 6.197 |
| cell_slope_10 | 2.993 | 3.818 | -0.453 | 2.463 | 6.139 |
| cell_slope_10_scheduled | 3.003 | 3.832 | -0.443 | 2.475 | 6.166 |
| cell_slope_100 | 2.957 | 3.780 | -0.460 | 2.444 | 6.091 |
| cell_slope_100_scheduled | 2.965 | 3.789 | -0.453 | 2.426 | 6.079 |

| Penalty | Primary interval | Player/season interval |
| --- | --- | --- |
| 1 | [-0.023, -0.001] | [-0.030, 0.006] |
| 10 | [-0.019, 0.000] | [-0.024, 0.005] |
| 100 | [-0.014, -0.001] | [-0.017, 0.002] |

| Penalty | Improved (%) | Worsened (%) | Tied (%) |
| --- | --- | --- | --- |
| 1 | 49.6 | 50.4 | 0.0 |
| 10 | 50.3 | 49.7 | 0.0 |
| 100 | 49.7 | 50.3 | 0.0 |

| Penalty | by season | n | Mean improvement | Contribution |
| --- | --- | --- | --- | --- |
| 1 | 2020 | 134 | -0.032 | -0.006 |
| 1 | 2021 | 101 | -0.007 | -0.001 |
| 1 | 2022 | 106 | -0.032 | -0.005 |
| 1 | 2023 | 102 | 0.000 | 0.000 |
| 1 | 2024 | 104 | -0.002 | -0.000 |
| 1 | 2025 | 127 | 0.003 | 0.001 |
| 10 | 2020 | 134 | -0.025 | -0.005 |
| 10 | 2021 | 101 | -0.005 | -0.001 |
| 10 | 2022 | 106 | -0.026 | -0.004 |
| 10 | 2023 | 102 | -0.000 | -0.000 |
| 10 | 2024 | 104 | -0.001 | -0.000 |
| 10 | 2025 | 127 | 0.002 | 0.000 |
| 100 | 2020 | 134 | -0.015 | -0.003 |
| 100 | 2021 | 101 | -0.003 | -0.000 |
| 100 | 2022 | 106 | -0.022 | -0.003 |
| 100 | 2023 | 102 | -0.002 | -0.000 |
| 100 | 2024 | 104 | -0.003 | -0.000 |
| 100 | 2025 | 127 | 0.001 | 0.000 |

| Penalty | by destination | n | Mean improvement | Contribution |
| --- | --- | --- | --- | --- |
| 1 | eurocup | 480 | -0.006 | -0.004 |
| 1 | euroleague | 194 | -0.027 | -0.008 |
| 10 | eurocup | 480 | -0.004 | -0.003 |
| 10 | euroleague | 194 | -0.023 | -0.007 |
| 100 | eurocup | 480 | -0.002 | -0.001 |
| 100 | euroleague | 194 | -0.021 | -0.006 |

### D. Overlap-window rates

| Arm | MAE | RMSE | Bias | Median absolute error | 90th absolute error |
| --- | --- | --- | --- | --- | --- |
| cell_slope_1 | 3.017 | 3.841 | -0.440 | 2.496 | 6.190 |
| cell_slope_1_scheduled | 3.026 | 3.853 | -0.433 | 2.486 | 6.179 |
| cell_slope_10 | 2.993 | 3.818 | -0.453 | 2.463 | 6.139 |
| cell_slope_10_scheduled | 3.001 | 3.829 | -0.447 | 2.457 | 6.194 |
| cell_slope_100 | 2.957 | 3.780 | -0.460 | 2.444 | 6.091 |
| cell_slope_100_scheduled | 2.963 | 3.789 | -0.455 | 2.413 | 6.117 |

| Penalty | Primary interval | Player/season interval |
| --- | --- | --- |
| 1 | [-0.022, 0.004] | [-0.027, 0.008] |
| 10 | [-0.020, 0.005] | [-0.025, 0.009] |
| 100 | [-0.018, 0.006] | [-0.022, 0.010] |

| Penalty | Improved (%) | Worsened (%) | Tied (%) |
| --- | --- | --- | --- |
| 1 | 52.5 | 47.5 | 0.0 |
| 10 | 52.1 | 47.9 | 0.0 |
| 100 | 52.8 | 47.2 | 0.0 |

| Penalty | by season | n | Mean improvement | Contribution |
| --- | --- | --- | --- | --- |
| 1 | 2020 | 134 | -0.024 | -0.005 |
| 1 | 2021 | 101 | 0.002 | 0.000 |
| 1 | 2022 | 106 | 0.017 | 0.003 |
| 1 | 2023 | 102 | -0.011 | -0.002 |
| 1 | 2024 | 104 | -0.029 | -0.004 |
| 1 | 2025 | 127 | -0.007 | -0.001 |
| 10 | 2020 | 134 | -0.022 | -0.004 |
| 10 | 2021 | 101 | 0.002 | 0.000 |
| 10 | 2022 | 106 | 0.019 | 0.003 |
| 10 | 2023 | 102 | -0.016 | -0.002 |
| 10 | 2024 | 104 | -0.025 | -0.004 |
| 10 | 2025 | 127 | -0.003 | -0.001 |
| 100 | 2020 | 134 | -0.016 | -0.003 |
| 100 | 2021 | 101 | 0.003 | 0.000 |
| 100 | 2022 | 106 | 0.018 | 0.003 |
| 100 | 2023 | 102 | -0.017 | -0.003 |
| 100 | 2024 | 104 | -0.023 | -0.003 |
| 100 | 2025 | 127 | 0.000 | 0.000 |

| Penalty | by destination | n | Mean improvement | Contribution |
| --- | --- | --- | --- | --- |
| 1 | eurocup | 480 | 0.007 | 0.005 |
| 1 | euroleague | 194 | -0.050 | -0.014 |
| 10 | eurocup | 480 | 0.008 | 0.006 |
| 10 | euroleague | 194 | -0.046 | -0.013 |
| 100 | eurocup | 480 | 0.008 | 0.005 |
| 100 | euroleague | 194 | -0.039 | -0.011 |

## All new refit sensitivities

| Pool | Penalty | Omission range | Seed range |
| --- | --- | --- | --- |
| A. Full corrected pool | 1 | [-0.029, 0.006] | [-0.007, -0.006] |
| A. Full corrected pool | 10 | [-0.025, 0.004] | [-0.005, -0.005] |
| A. Full corrected pool | 100 | [-0.016, 0.002] | [-0.001, -0.000] |
| B. Verified; full-season rates | 1 | [-0.026, -0.002] | [-0.013, -0.012] |
| B. Verified; full-season rates | 10 | [-0.023, -0.002] | [-0.010, -0.010] |
| B. Verified; full-season rates | 100 | [-0.017, -0.002] | [-0.008, -0.008] |
| C. Overlap keys; full-season rates | 1 | [-0.021, -0.002] | [-0.012, -0.012] |
| C. Overlap keys; full-season rates | 10 | [-0.019, -0.001] | [-0.010, -0.009] |
| C. Overlap keys; full-season rates | 100 | [-0.014, -0.002] | [-0.008, -0.007] |
| D. Overlap-window rates | 1 | [-0.027, 0.001] | [-0.009, -0.009] |
| D. Overlap-window rates | 10 | [-0.017, 0.005] | [-0.008, -0.008] |
| D. Overlap-window rates | 100 | [-0.009, 0.004] | [-0.006, -0.006] |

## Native support and exclusions for every scenario

Within-scenario native support is the intersection across the six new arms. Common support intersects the original target across all 56 scenarios and six arms. Per-arm native metrics and counts are retained in the complete numerical summary.

### A. Full corrected pool

| Scenario | Native | Common | Missing target | Unscored target | Unseen source | Unseen cell | Refusals |
| --- | --- | --- | --- | --- | --- | --- | --- |
| reference | 674 | 674 | 0 | 0 | 0 | 0 | none |
| omit_2016 | 674 | 674 | 0 | 0 | 0 | 0 | none |
| omit_2017 | 674 | 674 | 0 | 0 | 0 | 0 | none |
| omit_2018 | 674 | 674 | 0 | 0 | 0 | 0 | none |
| omit_2019 | 674 | 674 | 0 | 0 | 0 | 0 | none |
| omit_2020 | 674 | 674 | 0 | 0 | 0 | 0 | none |
| omit_2021 | 674 | 674 | 0 | 0 | 0 | 0 | none |
| omit_2022 | 674 | 674 | 0 | 0 | 0 | 0 | none |
| omit_2023 | 674 | 674 | 0 | 0 | 0 | 0 | none |
| omit_2024 | 674 | 674 | 0 | 0 | 0 | 0 | none |
| seed_1 | 674 | 674 | 0 | 0 | 0 | 0 | none |
| seed_2 | 674 | 674 | 0 | 0 | 0 | 0 | none |
| seed_3 | 674 | 674 | 0 | 0 | 0 | 0 | none |
| seed_4 | 674 | 674 | 0 | 0 | 0 | 0 | none |

### B. Verified; full-season rates

| Scenario | Native | Common | Missing target | Unscored target | Unseen source | Unseen cell | Refusals |
| --- | --- | --- | --- | --- | --- | --- | --- |
| reference | 674 | 674 | 0 | 0 | 0 | 0 | none |
| omit_2016 | 674 | 674 | 0 | 0 | 0 | 0 | none |
| omit_2017 | 674 | 674 | 0 | 0 | 0 | 0 | none |
| omit_2018 | 674 | 674 | 0 | 0 | 0 | 0 | none |
| omit_2019 | 674 | 674 | 0 | 0 | 0 | 0 | none |
| omit_2020 | 674 | 674 | 0 | 0 | 0 | 0 | none |
| omit_2021 | 674 | 674 | 0 | 0 | 0 | 0 | none |
| omit_2022 | 674 | 674 | 0 | 0 | 0 | 0 | none |
| omit_2023 | 674 | 674 | 0 | 0 | 0 | 0 | none |
| omit_2024 | 674 | 674 | 0 | 0 | 0 | 0 | none |
| seed_1 | 674 | 674 | 0 | 0 | 0 | 0 | none |
| seed_2 | 674 | 674 | 0 | 0 | 0 | 0 | none |
| seed_3 | 674 | 674 | 0 | 0 | 0 | 0 | none |
| seed_4 | 674 | 674 | 0 | 0 | 0 | 0 | none |

### C. Overlap keys; full-season rates

| Scenario | Native | Common | Missing target | Unscored target | Unseen source | Unseen cell | Refusals |
| --- | --- | --- | --- | --- | --- | --- | --- |
| reference | 674 | 674 | 0 | 0 | 0 | 0 | none |
| omit_2016 | 674 | 674 | 0 | 0 | 0 | 0 | none |
| omit_2017 | 674 | 674 | 0 | 0 | 0 | 0 | none |
| omit_2018 | 674 | 674 | 0 | 0 | 0 | 0 | none |
| omit_2019 | 674 | 674 | 0 | 0 | 0 | 0 | none |
| omit_2020 | 674 | 674 | 0 | 0 | 0 | 0 | none |
| omit_2021 | 674 | 674 | 0 | 0 | 0 | 0 | none |
| omit_2022 | 674 | 674 | 0 | 0 | 0 | 0 | none |
| omit_2023 | 674 | 674 | 0 | 0 | 0 | 0 | none |
| omit_2024 | 674 | 674 | 0 | 0 | 0 | 0 | none |
| seed_1 | 674 | 674 | 0 | 0 | 0 | 0 | none |
| seed_2 | 674 | 674 | 0 | 0 | 0 | 0 | none |
| seed_3 | 674 | 674 | 0 | 0 | 0 | 0 | none |
| seed_4 | 674 | 674 | 0 | 0 | 0 | 0 | none |

### D. Overlap-window rates

| Scenario | Native | Common | Missing target | Unscored target | Unseen source | Unseen cell | Refusals |
| --- | --- | --- | --- | --- | --- | --- | --- |
| reference | 674 | 674 | 0 | 0 | 0 | 0 | none |
| omit_2016 | 674 | 674 | 0 | 0 | 0 | 0 | none |
| omit_2017 | 674 | 674 | 0 | 0 | 0 | 0 | none |
| omit_2018 | 674 | 674 | 0 | 0 | 0 | 0 | none |
| omit_2019 | 674 | 674 | 0 | 0 | 0 | 0 | none |
| omit_2020 | 674 | 674 | 0 | 0 | 0 | 0 | none |
| omit_2021 | 674 | 674 | 0 | 0 | 0 | 0 | none |
| omit_2022 | 674 | 674 | 0 | 0 | 0 | 0 | none |
| omit_2023 | 674 | 674 | 0 | 0 | 0 | 0 | none |
| omit_2024 | 674 | 674 | 0 | 0 | 0 | 0 | none |
| seed_1 | 674 | 674 | 0 | 0 | 0 | 0 | none |
| seed_2 | 674 | 674 | 0 | 0 | 0 | 0 | none |
| seed_3 | 674 | 674 | 0 | 0 | 0 | 0 | none |
| seed_4 | 674 | 674 | 0 | 0 | 0 | 0 | none |

Unseen-category counts sum forecast rows across evaluation folds, separately for each arm; all six arms agree. Counts are not pooled across arms. The complete fit records retain training scale, categories and training keys.

## Primary reliability-policy readback

| Family (penalty 10) | Parent MAE | Policy MAE | Improvement | Conditional 95% interval |
| --- | --- | --- | --- | --- |
| Source offsets | 2.924 | 2.922 | 0.002 | [-0.024, 0.028] |
| Offsets + cell slopes | 2.993 | 2.994 | -0.001 | [-0.024, 0.022] |

These are the amendment's prespecified primary full-pool comparisons, not a selected best penalty. Positive favors the policy. Intervals use player/recorded-club-season dependence; the player/season alternatives also include zero. The linked policy report retains comparisons with always using translation and every sensitivity. Values are read from the saved direct policy readback; no policy is refitted here.

## Implementation details for the frozen comparison

This appendix documents the existing implementation; it changes no estimator,
cutoff, cohort, penalty or result. Source references are repository-relative.

### Selection, history and the lag multiplier

The unique forecast key is player name and destination season. After requiring
at least eight games and positive minutes, the original pipeline sorts
competition aggregates by minutes descending and retains one qualifying
continental destination and domestic source per player-season. There is no
explicit secondary tie key. The frozen selected keys are preserved; no claim is
made that minute ties occurred. The destination is EuroLeague or EuroCup and
the historical source protocol excludes Poland. A qualifying previous-season
appearance in either continental competition excludes a newcomer; an older
continental appearance does not. See `sloan_revision_analysis.py:reconstruct_cohort`
and `validate_translation_holdout.py:build_switchers` for the inherited rules.

Prior history h pools EFF and minutes across all positive-minute input
competition aggregates strictly before the source season, without reapplying
the eight-game threshold: h = 36 * sum(EFF) / sum(minutes). Consequently,
history reflects the player's historical competition mix. Missing history
uses the source rate x.

At destination cutoff t, the lag multiplier is
`k_t = median(y_i / (x_i * m_t(c_i)))` over earlier destination seasons i,
with finite positive denominators. The same cutoff-t factor table is used
for every denominator in this lag calculation. In contrast, each regression
training row retains the translated feature constructed at its own historical
cutoff, `z_i = x_i * m_(t_i)(c_i) * k_(t_i)`.
Missing usable factors or an empty valid lag sample causes refusal.
See `sloan_full_refit.py:refit_features`; no later factor table replaces a historical
regression feature.

### Partial pooling and factor support

Within a destination, retain finite raw cell factors f_c with finite positive
standard errors s_c. The existing moment estimator is:

`mu = sum(f_c / s_c^2) / sum(1 / s_c^2)`

`tau^2 = max(0, sample_variance(f_c, ddof=1) - mean(s_c^2))`

`pooled_c = mu + [tau^2 / (tau^2 + s_c^2)] * (f_c - mu)`

With fewer than two valid cells, the procedure returns raw factors and
unavailable mu and tau. The implementation's returned tau is the square root
of the between-cell variance. This is the exact inherited method, not an
assertion that it is optimal or that the resulting factors have a causal meaning.

Standard errors use the sample standard deviation of finite factor-bootstrap
draws, requiring at least half of the 2,000 draws (and at least two) to be finite.
Resampling groups are destination competition/club/season within a
source–destination cell, preserving observations within a sampled group.
Supported lookup requires at least 75 pairs, a finite standard error, no
complete pooling collapse and a finite pooled factor. Otherwise the destination
mean is used if finite; absence of a usable destination mean produces refusal.
The collapse predicate identifies poolable cells when finite tau is exactly
zero; it does not introduce a newly chosen shrinkage threshold. See
`build_league_factors.py:partial_pool`, `pooled_collapsed`,
`translation_research_common.py:fit_table` and
`compare_translation_designs.py:lookup`.

The main table's pool counts are complete inventories. At each cutoff, only
eligible earlier-season pairs contribute. Nonfallback and fallback counts
refer to forecast rows; a nonfallback count does not certify individual
counterfactual validity, role equivalence or player-outcome calibration.

### Paired-loss uncertainty and what it conditions on

For each target row, d_i is the baseline absolute error minus augmented absolute
error. Let r_i = d_i - mean(d). For grouping A with G_A groups,

`V_A = [G_A / (G_A - 1)] * sum_g[(sum_(i in g) r_i)^2] / n^2.`

Apply the same expression to grouping B and their intersections.
The variance is `V = V_A + V_B - V_(A intersection B)`.
The reported interval is
`mean(d) +/- t_(0.975, min(G_A, G_B)-1) * sqrt(V)`.
Fewer than two clusters in a component, or a nonpositive/nonfinite combined
variance, makes the interval unavailable; it is not clipped to zero.

The saved full-pool reference has 674 rows, 601 player groups, 201 recorded destination-competition/club/season groups and 674 intersection groups; the primary degrees of freedom are 200. The player/season alternative has 6 season groups and 5 degrees of freedom.

The first grouping is player. The primary second grouping is recorded
destination competition/club/season. The club label is the most frequent
recorded team within the aggregate; multi-club aggregates are not represented
with all club memberships. The alternative second grouping is destination
season. These are specified approximations to dependence, not exhaustive
uncertainty models. See `sloan_revision_analysis.py:multiway_interval` and
`sloan_context_benchmarks.py:paired_contrast`.

These intervals condition on fitted predictions and the selected target.
They do not propagate complete upstream estimation, retrospective source
correction, model selection or future cohort uncertainty. They are neither
simultaneous intervals for every correlated comparison nor player prediction
intervals. The omission and seed ranges perturb specified parts of estimation;
they are not substitutes for those missing uncertainty components. No practical
equivalence margin or prospective power calculation was supplied, so failure
to establish superiority does not establish negligible value.

### Training and scoring objectives

Regression coefficients minimize squared residuals, plus the declared ridge
penalty where applicable. The primary score is equal-row MAE. Thus the compared
procedures are not claimed to be MAE-optimal estimators. Source-rate scaling and
categories come only from each training fold; penalties remain 1, 10 and 100
without choosing a winner from evaluation losses. Forecast masks are fixed
across arms and scenarios. For this target, conclusions apply to this feature
recipe and these regression families; quantile regression, alternative ratio
estimators, age/role-rich models and externally informed priors have not been
exhausted.


### Registered restriction diagnostic (28 September)

After observing the support loss, we registered 200 random restrictions per control. Both reduce A to B's 1,537 pairs: one matches counts within each season; the other matches source league, destination competition and season counts. Sampling uses identities and strata, not outcomes. Each restriction refits the original factors and historical lags with 2,000 bootstrap draws, retaining the original regression-training keys and 674 forecast targets. Both original references reproduce before scoring. All 400 repetitions score every target in all 12 arms, with no unavailable factors. These are exploratory, conditional restrictions.

Median and empirical 2.5th/97.5th percentiles below. MAE and increments use source-offset penalty 10. Positive increment favors translation. All penalties, failures, full ranges and keyed outputs are retained.

| Pool/control | Supported (nonfallback) / 674 | MAE with translation | Translation increment | Complete repetitions |
| --- | --- | --- | --- | --- |
| Full corrected pool | 566 | 2.926 | -0.002 | reference |
| Verified pool | 118 | 2.931 | -0.007 | reference |
| Season counts | 91.0 [71.0, 114.0] | 2.929 [2.908, 2.948] | -0.005 [-0.024, 0.016] | 200/200 |
| Cell and season counts | 112.0 [68.0, 118.0] | 2.930 [2.913, 2.961] | -0.006 [-0.037, 0.011] | 200/200 |

These restrictions are conditional on the observed pool and inherited estimator. Verified rows were not randomized. Values inside these ranges are attainable under the declared restriction; this does not establish that sample loss caused the observed verification result. Successful-repetition loss summaries are conditional if any target is incomplete.

Destination-specific comparisons are less uniform. EuroLeague's verified pool retains 68/194 nonfallback forecasts; season-count restrictions retain a median 35 (full range 21–49), whereas cell-and-season restrictions retain a median 68 (full range 55–68). The verified count is outside the first range and inside the second. This remains a conditional diagnostic, not a causal verification effect. The supplement reports every season and destination, with each original stratum denominator retained.


## Restriction support by season and destination

Counts are median; empirical 2.5th/97.5th percentiles; full range. These are conditional restriction ranges, not confidence intervals. Every stratum retains its original forecast denominator in all 200 repetitions per control. Nonfallback, fallback and unavailable counts are shown separately.

### season count

#### By season

| Stratum | Target n | Category | Full pool | Verified pool | Restriction count: median; quantiles; full range |
| --- | --- | --- | --- | --- | --- |
| 2020 | 134 | nonfallback | 103 | 6 | 0.0; [0.0, 0.0]; full [0.0, 0.0] |
| 2020 | 134 | fallback | 31 | 128 | 134.0; [134.0, 134.0]; full [134.0, 134.0] |
| 2020 | 134 | unavailable | 0 | 0 | 0.0; [0.0, 0.0]; full [0.0, 0.0] |
| 2021 | 101 | nonfallback | 74 | 7 | 0.0; [0.0, 7.0]; full [0.0, 7.0] |
| 2021 | 101 | fallback | 27 | 94 | 101.0; [94.0, 101.0]; full [94.0, 101.0] |
| 2021 | 101 | unavailable | 0 | 0 | 0.0; [0.0, 0.0]; full [0.0, 0.0] |
| 2022 | 106 | nonfallback | 92 | 24 | 10.0; [0.0, 24.0]; full [0.0, 24.0] |
| 2022 | 106 | fallback | 14 | 82 | 96.0; [82.0, 106.0]; full [82.0, 106.0] |
| 2022 | 106 | unavailable | 0 | 0 | 0.0; [0.0, 0.0]; full [0.0, 0.0] |
| 2023 | 102 | nonfallback | 97 | 19 | 14.0; [8.0, 21.0]; full [8.0, 29.0] |
| 2023 | 102 | fallback | 5 | 83 | 88.0; [81.0, 94.0]; full [73.0, 94.0] |
| 2023 | 102 | unavailable | 0 | 0 | 0.0; [0.0, 0.0]; full [0.0, 0.0] |
| 2024 | 104 | nonfallback | 87 | 24 | 24.0; [16.0, 34.0]; full [9.0, 36.0] |
| 2024 | 104 | fallback | 17 | 80 | 80.0; [70.0, 88.0]; full [68.0, 95.0] |
| 2024 | 104 | unavailable | 0 | 0 | 0.0; [0.0, 0.0]; full [0.0, 0.0] |
| 2025 | 127 | nonfallback | 113 | 38 | 42.0; [31.0, 61.0]; full [13.0, 65.0] |
| 2025 | 127 | fallback | 14 | 89 | 85.0; [66.0, 96.0]; full [62.0, 114.0] |
| 2025 | 127 | unavailable | 0 | 0 | 0.0; [0.0, 0.0]; full [0.0, 0.0] |

#### By destination

| Stratum | Target n | Category | Full pool | Verified pool | Restriction count: median; quantiles; full range |
| --- | --- | --- | --- | --- | --- |
| eurocup | 480 | nonfallback | 407 | 50 | 56.0; [35.0, 81.0]; full [23.0, 94.0] |
| eurocup | 480 | fallback | 73 | 430 | 424.0; [399.0, 445.0]; full [386.0, 457.0] |
| eurocup | 480 | unavailable | 0 | 0 | 0.0; [0.0, 0.0]; full [0.0, 0.0] |
| euroleague | 194 | nonfallback | 159 | 68 | 35.0; [25.0, 42.0]; full [21.0, 49.0] |
| euroleague | 194 | fallback | 35 | 126 | 159.0; [152.0, 169.0]; full [145.0, 173.0] |
| euroleague | 194 | unavailable | 0 | 0 | 0.0; [0.0, 0.0]; full [0.0, 0.0] |

### cell season count

#### By season

| Stratum | Target n | Category | Full pool | Verified pool | Restriction count: median; quantiles; full range |
| --- | --- | --- | --- | --- | --- |
| 2020 | 134 | nonfallback | 103 | 6 | 6.0; [0.0, 6.0]; full [0.0, 6.0] |
| 2020 | 134 | fallback | 31 | 128 | 128.0; [128.0, 134.0]; full [128.0, 134.0] |
| 2020 | 134 | unavailable | 0 | 0 | 0.0; [0.0, 0.0]; full [0.0, 0.0] |
| 2021 | 101 | nonfallback | 74 | 7 | 7.0; [6.8, 7.0]; full [0.0, 7.0] |
| 2021 | 101 | fallback | 27 | 94 | 94.0; [94.0, 94.2]; full [94.0, 101.0] |
| 2021 | 101 | unavailable | 0 | 0 | 0.0; [0.0, 0.0]; full [0.0, 0.0] |
| 2022 | 106 | nonfallback | 92 | 24 | 24.0; [10.0, 24.0]; full [10.0, 24.0] |
| 2022 | 106 | fallback | 14 | 82 | 82.0; [82.0, 96.0]; full [82.0, 96.0] |
| 2022 | 106 | unavailable | 0 | 0 | 0.0; [0.0, 0.0]; full [0.0, 0.0] |
| 2023 | 102 | nonfallback | 97 | 19 | 19.0; [13.0, 19.0]; full [13.0, 19.0] |
| 2023 | 102 | fallback | 5 | 83 | 83.0; [83.0, 89.0]; full [83.0, 89.0] |
| 2023 | 102 | unavailable | 0 | 0 | 0.0; [0.0, 0.0]; full [0.0, 0.0] |
| 2024 | 104 | nonfallback | 87 | 24 | 24.0; [12.0, 24.0]; full [12.0, 24.0] |
| 2024 | 104 | fallback | 17 | 80 | 80.0; [80.0, 92.0]; full [80.0, 92.0] |
| 2024 | 104 | unavailable | 0 | 0 | 0.0; [0.0, 0.0]; full [0.0, 0.0] |
| 2025 | 127 | nonfallback | 113 | 38 | 38.0; [20.0, 38.0]; full [20.0, 38.0] |
| 2025 | 127 | fallback | 14 | 89 | 89.0; [89.0, 107.0]; full [89.0, 107.0] |
| 2025 | 127 | unavailable | 0 | 0 | 0.0; [0.0, 0.0]; full [0.0, 0.0] |

#### By destination

| Stratum | Target n | Category | Full pool | Verified pool | Restriction count: median; quantiles; full range |
| --- | --- | --- | --- | --- | --- |
| eurocup | 480 | nonfallback | 407 | 50 | 44.0; [0.0, 50.0]; full [0.0, 50.0] |
| eurocup | 480 | fallback | 73 | 430 | 436.0; [430.0, 480.0]; full [430.0, 480.0] |
| eurocup | 480 | unavailable | 0 | 0 | 0.0; [0.0, 0.0]; full [0.0, 0.0] |
| euroleague | 194 | nonfallback | 159 | 68 | 68.0; [62.0, 68.0]; full [55.0, 68.0] |
| euroleague | 194 | fallback | 35 | 126 | 126.0; [126.0, 132.0]; full [126.0, 139.0] |
| euroleague | 194 | unavailable | 0 | 0 | 0.0; [0.0, 0.0]; full [0.0, 0.0] |


## Every restriction arm and support range

Values are median; empirical 2.5th/97.5th percentiles; full range. They are not confidence intervals. All 200 repetitions per control are complete.

### season count

| Support category | Median; quantiles; full range |
| --- | --- |
| nonfallback | 91.000; [70.950, 114.025]; full [48.000, 129.000] |
| fallback | 583.000; [559.975, 603.050]; full [545.000, 626.000] |
| unavailable | 0.000; [0.000, 0.000]; full [0.000, 0.000] |

| Arm | MAE | MAE change from full pool |
| --- | --- | --- |
| source_ridge_1 | 2.928; [2.928, 2.928]; full [2.928, 2.928] | 0.000; [0.000, 0.000]; full [0.000, 0.000] |
| source_ridge_1_scheduled | 2.933; [2.910, 2.952]; full [2.899, 3.001] | 0.001; [-0.022, 0.020]; full [-0.033, 0.069] |
| source_ridge_10 | 2.924; [2.924, 2.924]; full [2.924, 2.924] | 0.000; [0.000, 0.000]; full [0.000, 0.000] |
| source_ridge_10_scheduled | 2.929; [2.908, 2.948]; full [2.897, 3.000] | 0.003; [-0.017, 0.022]; full [-0.029, 0.074] |
| source_ridge_100 | 2.942; [2.942, 2.942]; full [2.942, 2.942] | 0.000; [0.000, 0.000]; full [0.000, 0.000] |
| source_ridge_100_scheduled | 2.948; [2.936, 2.965]; full [2.922, 3.023] | 0.020; [0.007, 0.036]; full [-0.006, 0.094] |
| cell_slope_1 | 3.017; [3.017, 3.017]; full [3.017, 3.017] | 0.000; [0.000, 0.000]; full [0.000, 0.000] |
| cell_slope_1_scheduled | 3.026; [3.002, 3.049]; full [2.990, 3.116] | 0.002; [-0.022, 0.025]; full [-0.034, 0.092] |
| cell_slope_10 | 2.993; [2.993, 2.993]; full [2.993, 2.993] | 0.000; [0.000, 0.000]; full [0.000, 0.000] |
| cell_slope_10_scheduled | 3.000; [2.977, 3.025]; full [2.966, 3.056] | 0.002; [-0.021, 0.027]; full [-0.032, 0.058] |
| cell_slope_100 | 2.957; [2.957, 2.957]; full [2.957, 2.957] | 0.000; [0.000, 0.000]; full [0.000, 0.000] |
| cell_slope_100_scheduled | 2.962; [2.943, 2.981]; full [2.932, 3.013] | 0.004; [-0.015, 0.023]; full [-0.026, 0.055] |

| Parent arm | Translation increment |
| --- | --- |
| source_ridge_1 | -0.005; [-0.024, 0.018]; full [-0.073, 0.029] |
| source_ridge_10 | -0.005; [-0.024, 0.016]; full [-0.076, 0.027] |
| source_ridge_100 | -0.006; [-0.023, 0.006]; full [-0.081, 0.020] |
| cell_slope_1 | -0.009; [-0.032, 0.015]; full [-0.099, 0.027] |
| cell_slope_10 | -0.007; [-0.032, 0.016]; full [-0.063, 0.027] |
| cell_slope_100 | -0.005; [-0.024, 0.014]; full [-0.055, 0.025] |

### cell season count

| Support category | Median; quantiles; full range |
| --- | --- |
| nonfallback | 112.000; [68.000, 118.000]; full [62.000, 118.000] |
| fallback | 562.000; [556.000, 606.000]; full [556.000, 612.000] |
| unavailable | 0.000; [0.000, 0.000]; full [0.000, 0.000] |

| Arm | MAE | MAE change from full pool |
| --- | --- | --- |
| source_ridge_1 | 2.928; [2.928, 2.928]; full [2.928, 2.928] | 0.000; [0.000, 0.000]; full [0.000, 0.000] |
| source_ridge_1_scheduled | 2.935; [2.915, 2.963]; full [2.906, 3.038] | 0.003; [-0.018, 0.031]; full [-0.026, 0.106] |
| source_ridge_10 | 2.924; [2.924, 2.924]; full [2.924, 2.924] | 0.000; [0.000, 0.000]; full [0.000, 0.000] |
| source_ridge_10_scheduled | 2.930; [2.913, 2.961]; full [2.904, 3.039] | 0.005; [-0.012, 0.035]; full [-0.021, 0.114] |
| source_ridge_100 | 2.942; [2.942, 2.942]; full [2.942, 2.942] | 0.000; [0.000, 0.000]; full [0.000, 0.000] |
| source_ridge_100_scheduled | 2.950; [2.939, 2.995]; full [2.930, 3.084] | 0.021; [0.011, 0.067]; full [0.001, 0.155] |
| cell_slope_1 | 3.017; [3.017, 3.017]; full [3.017, 3.017] | 0.000; [0.000, 0.000]; full [0.000, 0.000] |
| cell_slope_1_scheduled | 3.028; [3.002, 3.095]; full [2.996, 3.175] | 0.004; [-0.022, 0.071]; full [-0.028, 0.151] |
| cell_slope_10 | 2.993; [2.993, 2.993]; full [2.993, 2.993] | 0.000; [0.000, 0.000]; full [0.000, 0.000] |
| cell_slope_10_scheduled | 3.002; [2.976, 3.066]; full [2.967, 3.138] | 0.004; [-0.022, 0.068]; full [-0.031, 0.140] |
| cell_slope_100 | 2.957; [2.957, 2.957]; full [2.957, 2.957] | 0.000; [0.000, 0.000]; full [0.000, 0.000] |
| cell_slope_100_scheduled | 2.965; [2.946, 3.020]; full [2.938, 3.085] | 0.007; [-0.012, 0.062]; full [-0.020, 0.127] |

| Parent arm | Translation increment |
| --- | --- |
| source_ridge_1 | -0.007; [-0.035, 0.013]; full [-0.110, 0.022] |
| source_ridge_10 | -0.006; [-0.037, 0.011]; full [-0.115, 0.020] |
| source_ridge_100 | -0.007; [-0.053, 0.003]; full [-0.142, 0.012] |
| cell_slope_1 | -0.011; [-0.078, 0.015]; full [-0.158, 0.021] |
| cell_slope_10 | -0.009; [-0.074, 0.016]; full [-0.145, 0.026] |
| cell_slope_100 | -0.007; [-0.063, 0.011]; full [-0.127, 0.019] |

The verified pool retains 118 nonfallback forecasts. Full random-restriction ranges are 48–129 for season counts and 62–118 for cell-and-season counts. Thus comparably low support is attainable by reducing the original estimation pool. This does not establish that sample loss caused the observed A-to-B result, nor remove nonrandom verification and composition effects.

## Exposure and adverse evidence retained

All six destination seasons were inspected in earlier model development. Chronological fitting does not undo that exposure. V9's 56 runs comprise four pools multiplied by one reference, nine single-season omissions and four alternative seeds; they are sensitivity runs, not independent replications. V10 reuses their upstream factor estimates and refits the new regressions. Omissions exclude direct estimation labels, while fixed historical player measurements may retain information from the omitted season.

The original protected holdout remains PARTIAL. The equal-count scheduled-versus-transfer sensitivity reversed the earlier direction. Structural-multiplier simulations showed undercoverage for a different estimand. Four provisional aliases were verified; a conflicting birth-date identity remains quarantined in its affected season. Unknown identities and rounding-only discrepancies remain explicit. Neither aggregate numerical reproduction nor a conditional interval resolves raw-source validity or redistribution rights.

The observed-appearance denominator excludes some unsuccessful arrivals. No-appearance records are not assigned zero EFF/36; the rate is undefined at zero minutes. Removing the positive-destination-EFF filter added no outer evaluation rows, so it does not validate the all-arrival denominator. The separate appearance-calibration/audit experiments are not evidence for this forecast model.

The September 12 operating forecast lock is unchanged. It uses a different training/arm-selection pipeline and first scores on January 31, 2027, after the conditional December 4 invited-paper deadline. It cannot retrospectively confirm this candidate. No external scout or statistician review has occurred; the author has no assumed reviewer contacts. Final author approval, data-release scope, public repository delivery and submission are separate pending actions.

V9 source and audit record · V10 protocol · Release guide.
