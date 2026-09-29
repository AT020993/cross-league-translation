# Registered support-restriction diagnostic

## Specification

| Field | Declaration |
| --- | --- |
| Unit | Restricted pair sample on the same 674 forecast keys |
| Estimator | Two controls, 200 repetitions each; frozen fitting procedure |
| Uncertainty | Empirical restriction quantiles, not confidence intervals |
| Decision | Exploratory diagnosis; no randomized verification effect |

Median and empirical 2.5th/97.5th percentiles below. MAE and increments use source-offset penalty 10. Positive increment favors translation. All penalties, failures, full ranges and keyed outputs are retained.

| Pool/control | Nonfallback / 674 | MAE with translation | Translation increment | Complete repetitions |
| --- | --- | --- | --- | --- |
| full | 566 | 2.926 | -0.002 | reference |
| verified | 118 | 2.931 | -0.007 | reference |
| season_count | 91.0 [71.0, 114.0] | 2.929 [2.908, 2.948] | -0.005 [-0.024, 0.016] | 200/200 |
| cell_season_count | 112.0 [68.0, 118.0] | 2.930 [2.913, 2.961] | -0.006 [-0.037, 0.011] | 200/200 |

These restrictions are conditional on the observed pool and inherited estimator. Verified rows were not randomized. Values inside these ranges are attainable under the declared restriction; this does not establish that sample loss caused the observed verification result. Successful-repetition loss summaries are conditional if any target is incomplete.
