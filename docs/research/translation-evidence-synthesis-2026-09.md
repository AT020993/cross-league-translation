# Evidence synthesis across walk-forward seasons — and the pre-registered forecast for 2026-27

**Generated 2026-09-04 by `scripts/synthesize_translation_evidence.py` from `walkforward_rows.parquet`; every number is read from `evidence_synthesis_summary.json`. Study D of `prelock-program-preregistration-2026-09-04.md` (ATI-2964).**

## Specification

| Choice | This study | Alternative considered |
|---|---|---|
| **Unit** | one walk-forward season; effect = MAE(comparator) − MAE(model), paired cluster-bootstrap SE | pooled rows (already reported by the walk-forward; hides between-season heterogeneity) |
| **Pooling** | random effects, τ² by REML, Hartung-Knapp-Sidik-Jonkman CI | DerSimonian-Laird with a normal CI (reported as sensitivity) |
| **Forecast** | 95% prediction interval for a new season, t on k − 2 df | the pooled CI (wrong object — it is about the mean, not the next season) |
| **Null** | six zero effects with the real SEs must pool to intervals covering zero | — |

## Per season

| contrast | season | n | Δ MAE | SE |
|---|---:|---:|---:|---:|
| per_league_vs_b0 | 2020 | 134 | +0.8507 | 0.2321 |
| per_league_vs_b0 | 2021 | 101 | +1.2659 | 0.2599 |
| per_league_vs_b0 | 2022 | 106 | +0.3758 | 0.2755 |
| per_league_vs_b0 | 2023 | 102 | +0.7417 | 0.2607 |
| per_league_vs_b0 | 2024 | 104 | +1.2355 | 0.2540 |
| per_league_vs_b0 | 2025 | 127 | +0.4197 | 0.2272 |
| per_league_vs_one_global | 2020 | 134 | +0.1306 | 0.0683 |
| per_league_vs_one_global | 2021 | 101 | +0.2625 | 0.0832 |
| per_league_vs_one_global | 2022 | 106 | +0.3850 | 0.0865 |
| per_league_vs_one_global | 2023 | 102 | +0.2224 | 0.1213 |
| per_league_vs_one_global | 2024 | 104 | +0.0992 | 0.1190 |
| per_league_vs_one_global | 2025 | 127 | +0.1562 | 0.0821 |
| rtm_plus_league_vs_rtm | 2020 | 134 | +0.1699 | 0.0630 |
| rtm_plus_league_vs_rtm | 2021 | 101 | +0.1596 | 0.0837 |
| rtm_plus_league_vs_rtm | 2022 | 106 | +0.3283 | 0.0744 |
| rtm_plus_league_vs_rtm | 2023 | 102 | +0.1686 | 0.1037 |
| rtm_plus_league_vs_rtm | 2024 | 104 | +0.1638 | 0.1024 |
| rtm_plus_league_vs_rtm | 2025 | 127 | +0.0764 | 0.0777 |

## Pooled, and the forecast for a new season

| contrast | k | pooled Δ (REML+HKSJ 95% CI) | τ | I² | **prediction interval, new season** | DL sensitivity | seasons to halve the PI |
|---|---:|---|---:|---:|---|---|---:|
| per_league_vs_b0 | 6 | +0.8130 [+0.4132, +1.2128] | 0.2840 | 0.56 | **[-0.0859, +1.7120]** | +0.8130 [+0.5099, +1.1161] | — |
| per_league_vs_one_global | 6 | +0.2109 [+0.0960, +0.3257] | 0.0622 | 0.30 | **[-0.0017, +0.4234]** | +0.2107 [+0.1251, +0.2964] | — |
| rtm_plus_league_vs_rtm | 6 | +0.1810 [+0.0839, +0.2780] | 0.0438 | 0.15 | **[+0.0203, +0.3416]** | +0.1812 [+0.1109, +0.2516] | — |

## Invariants

* Zero-effect control: CI [-0.2622, +0.2622] covers zero: True; prediction interval covers zero: True.

## Threats

* folds share training data (fold s trains on every season before s): the pooled CI is descriptive of the walk-forward, not an independent-replications CI
* k = 6 leaves tau^2 poorly identified; the prediction interval is wide by construction

## What this licenses

Over 6 held-out seasons the per-league model beat the untranslated baseline by +0.8130 MAE (HKSJ 95% CI [+0.4132, +1.2128]); a new season is expected to fall in [-0.0859, +1.7120]. The 2026-27 result is a point inside or outside that interval — a stronger test than a single-season pass/fail. The other two contrasts are read the same way from the table; where a prediction interval crosses zero, a new season is NOT expected to separate the arms.

## Scripts

* `scripts/synthesize_translation_evidence.py` — everything above; `--render` rewrites this note from the artifact.
* `scripts/validate_translation_walkforward.py --rows-out` — the rows.
