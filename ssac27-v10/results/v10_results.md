# V10 registered comparison results

| Specification | Definition |
| --- | --- |
| Unit | Player-destination-season forecast |
| Population | Frozen 674-forecast v9 appearance-qualified target |
| Estimator | Six fixed slope regression arms across 56 frozen upstream scenarios |
| Null | Translation has no robust incremental predictive benefit |
| Filter | Frozen v9 eligibility; unknowns and refusals retained |
| Key | Exact frozen player, destination and season keys |
| Uncertainty | Conditional player/club-season and player/season intervals; fixed omission and seed sensitivity |
| Threats | Reused outcomes, selected appearances, upstream-factor uncertainty, unresolved release rights |

## Existing benchmark

| Baseline receiving translation | MAE improvement | Conditional 95% interval |
| --- | --- | --- |
| History only | 0.161 | [0.077, 0.246] |
| History + destination slope | 0.049 | [-0.013, 0.111] |
| + Source offsets; penalty 1 | -0.004 | [-0.026, 0.018] |
| + Source offsets; penalty 10 | -0.002 | [-0.028, 0.024] |
| + Source offsets; penalty 100 | 0.014 | [-0.030, 0.058] |

These are paired with/without-translation comparisons within each baseline, not differences between unrelated best-performing models. All three penalties are retained. The destination-slope comparison has MAE 2.989 without and 2.940 with translation. Its player-by-season sensitivity interval is [-0.020, 0.118]; only six season clusters are available.

## Registered cell-slope comparison

| Factor pool | Penalty | MAE without z | MAE with z | Improvement | Conditional 95% interval |
| --- | --- | --- | --- | --- | --- |
| A. Full corrected pool | 1 | 3.017 | 3.024 | -0.007 | [-0.033, 0.019] |
| A. Full corrected pool | 10 | 2.993 | 2.998 | -0.005 | [-0.029, 0.019] |
| A. Full corrected pool | 100 | 2.957 | 2.958 | -0.001 | [-0.029, 0.027] |
| B. Verified; full-season rates | 1 | 3.017 | 3.029 | -0.012 | [-0.024, -0.001] |
| B. Verified; full-season rates | 10 | 2.993 | 3.003 | -0.010 | [-0.020, 0.000] |
| B. Verified; full-season rates | 100 | 2.957 | 2.965 | -0.008 | [-0.015, -0.001] |
| C. Overlap keys; full-season rates | 1 | 3.017 | 3.029 | -0.012 | [-0.023, -0.001] |
| C. Overlap keys; full-season rates | 10 | 2.993 | 3.003 | -0.010 | [-0.019, 0.000] |
| C. Overlap keys; full-season rates | 100 | 2.957 | 2.965 | -0.007 | [-0.014, -0.001] |
| D. Overlap-window rates | 1 | 3.017 | 3.026 | -0.009 | [-0.022, 0.004] |
| D. Overlap-window rates | 10 | 2.993 | 3.001 | -0.008 | [-0.020, 0.005] |
| D. Overlap-window rates | 100 | 2.957 | 2.963 | -0.006 | [-0.018, 0.006] |

Robust incremental superiority is not established across the registered comparisons. Penalty values index sensitivity comparisons; none is selected as the winner. These correlated conditional intervals are not simultaneous guarantees.

| Penalty | Source offsets only: MAE | Offsets + cell slopes, no z: MAE |
| --- | --- | --- |
| 1 | 2.928 | 3.017 |
| 10 | 2.924 | 2.993 |
| 100 | 2.942 | 2.957 |

Matching the feature's multiplicative form does not make the richer baseline empirically preferable. These absolute errors describe the fixed comparisons; no penalty or model is promoted from evaluation performance.

Of the 12 reference contrasts, 12 point estimates favor omitting translation and 4 player/club-season intervals exclude zero in that direction. Every new reference player/season interval includes zero. Thus an adverse-effect inference also depends on the clustering specification; these results do not establish robust harm.

## Support and unknowns

| Factor pool | Estimation pairs | Scored forecasts | Factor fallbacks |
| --- | --- | --- | --- |
| A. Full corrected pool | 4074 | 674 | 108 |
| B. Verified; full-season rates | 1537 | 674 | 556 |
| C. Overlap keys; full-season rates | 1463 | 674 | 561 |
| D. Overlap-window rates | 1463 | 674 | 561 |

The exclusion ledger records 2,440 factor-pair records with unverified identity and 97 multi-club pairs before overlap eligibility, then 70 pairs below the post-trim game requirement and 4 invalid-minute cases. Unverified does not mean incorrect. This is principally a verification-and-support sensitivity, not an experiment on changing clubs. Fallback is a factor-estimation policy; it is distinct from a refused forecast or an unknown appearance outcome.

## Frozen upstream scenario sensitivity

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

## Interpretation

Robust incremental superiority is not established across the registered comparisons.
