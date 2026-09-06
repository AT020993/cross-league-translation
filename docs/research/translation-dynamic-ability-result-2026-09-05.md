# Dynamic (random-walk) player ability — RESULT of the pre-registered test

**Date:** 2026-09-05 · **Pre-registration:** `translation-dynamic-ability-preregistration-2026-09-05.md`,
committed and pushed at `a62be01e` (13:18 +03:00) before the generator existed · **Generator:**
`scripts/validate_translation_dynamic.py` (default arguments; `--continental-source api`) · **Tests:**
`tests/test_scripts/test_validate_translation_dynamic.py` · **Machine-readable values:**
`docs/research/artifacts/dynamic-ability-2026-09-05/dynamic_summary.json` (committed 2026-09-06; the 2026-09-05 copy lived only in a gitignored directory and the gate reproduces: Δ +0.081, CI [−0.029, +0.182], PARTIAL), `dynamic_rows.parquet` (regenerated, not committed).
Every number below is read from that JSON. Repository state at the run: branch
`feature/dynamic-ability-arm` at `a62be01e` plus the uncommitted generator (committed in the same PR).

**Verdict: PARTIAL, as the pre-registration predicted.** On the pooled selection folds 2020–2024
(n = 547) the dynamic arm scores **MAE 2.767** against the shipped two-stage combined arm's
**2.848**: Δ = **+0.081**, 95% cluster-bootstrap CI **[−0.029, +0.182]**. The point favours the
dynamic arm; the interval spans zero. The 2025 confirmation fold, read once, points the same way and
is also not separable (Δ = +0.134, CI [−0.089, +0.359]). The filter is correct (T1 passed to 7e-15).
**What the test confirms is the structure: the fitted random walk reproduces the recency heuristic's
gain without anyone choosing a half-life** (dyn vs `hier_recency1`: −0.018, CI [−0.082, +0.040]).
What it does not do is separate itself from the shipped basis at this n — which is exactly why the
2026-27 prospective set is the test that matters, and why Amendment 10 (proposed beside this note)
asks to score it there as a secondary arm.

## Specification — as pre-registered, nothing changed after the run

Identical to the pre-registration's table: additive scale; β from same-season pairs (two-way fixed
effects, EuroLeague pinned at 0); σ² from two stints of one player in one season; `q` from consecutive
observed seasons with the gap scaling; (μ, τ²) by DerSimonian–Laird on first seasons; Kalman filter
per player, random-walk forecast; debutants fall back to the shrunken source stint; predictions
unclipped; stints under 36 minutes dropped. One run. No hyperparameter touched any scored row.

## Fitted components (per fold, `fits`)

| fold | q (rate²/season) | σ² per game | τ² | μ | fallback share | negative predictions | any floor |
|---|---|---|---|---|---|---|---|
| 2020 | 3.48 | 120.9 | 20.1 | 10.87 | 0.000 | 0 | none |
| 2021 | 3.19 | 125.0 | 20.8 | 10.69 | 0.000 | 0 | none |
| 2022 | 3.37 | 123.1 | 21.0 | 10.59 | 0.000 | 0 | none |
| 2023 | 3.06 | 123.8 | 21.0 | 10.61 | 0.000 | 0 | none |
| 2024 | 2.92 | 124.5 | 21.0 | 10.64 | 0.000 | 0 | none |
| 2025 | 2.82 | 126.5 | 20.9 | 10.76 | 0.008 | 0 | none |

Reading the components in one sentence: a season of 18 games carries sampling variance
σ²/18 ≈ 6.9, ability drifts by q ≈ 3 per season, and abilities spread with τ² ≈ 21 across players —
so one season's evidence is worth about three seasons of drift, and a season four years old is
nearly uninformative about today's ability. That is the quantitative form of "a career-constant
ability is the wrong prior" from the hierarchical note, and it is why the equal-weight static arm
loses ground that the dynamic arm recovers.

## Result — selection folds 2020–2024, n = 547

| arm | MAE | R² | what it is |
|---|---|---|---|
| untranslated (B0) | 3.922 | −0.104 | shipped |
| one global scalar | 3.250 | +0.254 | shipped |
| per-league factors | 3.034 | +0.341 | shipped |
| RTM, no league | 3.045 | +0.341 | shipped |
| **RTM + per-league (combined) — the bar** | **2.848** | **+0.413** | shipped basis |
| `hier_additive` (static, same scale) | 2.823 | +0.418 | static comparator |
| `dyn_q0` (T1 check) | 2.831 | +0.415 | filter with q = 0 |
| `dyn_tier_beta` | 2.837 | +0.404 | decomposition: level only |
| `dyn_log` | 2.805 | +0.424 | alternative |
| `dyn_q_double` | 2.798 | +0.415 | alternative |
| **`dyn` (primary)** | **2.767** | **+0.429** | **this note** |
| `dyn_q_half` | 2.758 | +0.434 | alternative |
| `hier_recency1` (the heuristic) | 2.749 | +0.448 | static comparator |

Pre-registered contrasts (positive favours the first arm):

| contrast | Δ MAE | 95% CI | reads |
|---|---|---|---|
| **`dyn` vs combined (the gate)** | **+0.081** | **[−0.029, +0.182]** | **PARTIAL** |
| `dyn` vs `hier_recency1` | −0.018 | [−0.082, +0.040] | the fitted structure matches the heuristic |
| `dyn` vs `hier_additive` | +0.056 | [−0.041, +0.145] | drift over a static ability: not separable here |
| `dyn` vs per-league | +0.267 | [+0.157, +0.375] | wins |
| `dyn` vs `dyn_tier_beta` | +0.070 | [+0.019, +0.121] | **the mapping is live in this arm** |
| `dyn_log` vs `dyn` | −0.038 | [−0.125, +0.054] | log no better (additive stands) |
| `dyn_q_half` vs `dyn` | +0.009 | [−0.017, +0.037] | q insensitive downward |
| `dyn_q_double` vs `dyn` | −0.031 | [−0.060, −0.003] | doubling q hurts |

## Confirmation fold 2025 — read once, never pooled (n = 127)

| arm | MAE | R² |
|---|---|---|
| combined (the bar) | 3.346 | +0.348 |
| `hier_additive` | 3.455 | +0.327 |
| `hier_recency1` | 3.289 | +0.368 |
| **`dyn`** | **3.211** | **+0.392** |
| `dyn_tier_beta` | 3.174 | +0.402 |
| `dyn_log` | 3.456 | +0.315 |

| contrast | Δ MAE | 95% CI |
|---|---|---|
| `dyn` vs combined | +0.134 | [−0.089, +0.359] |
| `dyn` vs `hier_recency1` | +0.078 | [−0.036, +0.186] |
| `dyn` vs `hier_additive` | +0.244 | [+0.059, +0.412] |
| `dyn` vs `dyn_tier_beta` | −0.037 | [−0.152, +0.076] |
| `dyn_log` vs `dyn` | −0.245 | [−0.393, −0.106] |

Same direction as the selection folds on every contrast that matters; the 2025 fold has n = 127
and separates nothing except "drift beats static" and "additive beats log". Per season (MAE):

| season | n | combined | `dyn` | `hier_recency1` | `hier_additive` |
|---|---|---|---|---|---|
| 2020 | 134 | 3.106 | 2.923 | 2.928 | 3.024 |
| 2021 | 101 | 2.791 | 2.853 | 2.757 | 2.924 |
| 2022 | 106 | 2.799 | 2.649 | 2.731 | 2.831 |
| 2023 | 102 | 3.046 | 2.940 | 2.935 | 2.878 |
| 2024 | 104 | 2.427 | 2.435 | 2.346 | 2.405 |
| 2025 | 127 | 3.346 | 3.211 | 3.289 | 3.455 |

The dynamic arm is ahead of the combined arm in four of six seasons and behind in two (2021,
2024, both by under 0.07). That is the shape a +0.08 pooled gain at this noise produces.

## The pre-registered threats, answered

| # | threat | what happened |
|---|---|---|
| T1 | the filter is wrong | **passed**: with the static arm's (μ, τ², σ²) and q = 0 the filter reproduces the static posterior to 7.1e-15 on every fold (in-script assert); with its own components, `dyn_q0` sits 0.002 MAE from `hier_additive` pooled, within the pre-registered 0.05 |
| T2 | `q` absorbs league mis-adjustment | `dyn` beats `dyn_tier_beta` by +0.070 [+0.019, +0.121] and **0 of 200** shuffled mappings reach it (shuffle mean −0.057): the per-league mapping contributes in this arm, unlike in the static random-intercept model, where it was inert. The Kalman gain on a season is high (for a first season at 18 games, τ²/(τ² + σ²/18) ≈ 21/(21 + 6.9) ≈ 0.75 from the components above), so the source-league adjustment is carried into the forecast at most of its strength |
| T3 | a 2024–2025 artefact | the gain is in 2020, 2022, 2023 and 2025; 2021 and 2024 go the other way by small amounts |
| T4 | negative additive predictions | **0** in every fold |
| T5 | selection on these rows | stands as stated; the 2026-27 set is the clean test |
| T6 | debutant fallback dominates | 0.0% of rows in 2020–2024, 0.8% in 2025 |
| T7 | a floored component | none, in any fold or arm |

## What this licenses

* **Supported:** a random walk on ability with a **fitted** innovation variance reproduces the gain
  the hand-picked half-life showed, on the same rows, with no free choice. The recency finding of
  the hierarchical note is therefore a property of the corpus, not of one heuristic.
* **Supported:** the additive scale stands (log is no better on selection and clearly worse on 2025),
  and doubling `q` hurts while halving it does not — the fitted `q` sits near the flat part.
* **Not licensed:** replacing the shipped basis. The gate returned PARTIAL. The pre-registration
  said a PARTIAL proposes **Amendment 10 — the dynamic arm as a secondary arm scored beside the
  primary on the 2026-27 set, point predictions only, no bar, no basis change, needs Amir's
  acceptance.** That amendment is filed beside this note as PROPOSED.
* **Not licensed:** any change to the abstract. One manuscript sentence: the two-stage pipeline was
  tested against a joint dynamic-ability model, which was ahead but not separable on 674
  retrospective transfers and is scored prospectively on the 2026-27 imports.

## Limitations, stated as limitations

* Power: ~0.66 at the heuristic's gain, as pre-registered; a PARTIAL was the likeliest outcome and it
  is what happened. Nothing here is a reason to move the bar.
* The rows were seen before by the static study; the additive scale and "recency matters" were
  chosen on them. The pre-registration says which claims that contaminates (T5).
* `q` is a single corpus-wide constant; ability drift surely differs by age, and an age-dependent
  `q` is a natural extension that is **not** part of the pre-registered model.
* The lock's conformal interval was calibrated on `per_league` residuals; no interval is claimed for
  the dynamic arm, and Amendment 10 asks for point predictions only.
* σ² per game (≈124 in rate² units) is estimated from players with two stints in one season; those
  players may be noisier than average (mid-season movers), which would make σ² slightly high and
  the filter slightly conservative.

## Scripts

* `scripts/validate_translation_dynamic.py` — everything above; rebuilds the validator's six folds
  through `validate_translation_hierarchical.build_folds`, asserts the five shipped arm MAEs against
  `walkforward_summary.json`, fits every component on rows strictly before each scored season,
  writes `dynamic_summary.json` and `dynamic_rows.parquet`. `--skip-shuffle` omits the 200-rep
  control.
* `tests/test_scripts/test_validate_translation_dynamic.py` — nine synthetic tests, each
  mutation-verified (mutation applied, confirmed red, reverted): component recovery from random-walk
  data; σ² pairs stints of one player-season only; `q` scales with the gap; the vectorised filter
  equals the scalar recursion and grows by `q`; `q = 0` with the static components equals the static
  posterior; no scored-season row enters its fit; the debutant fallback shrinks and is flagged;
  additive predictions are unclipped; the verdict rule matches the pre-registration.
