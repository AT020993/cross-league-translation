# PRE-REGISTRATION — a dynamic (random-walk) player ability inside the translation model

**Date: 2026-09-05. Status: pre-registered, written BEFORE the generator exists and before any run.**
Follows `translation-hierarchical-arm-2026-09-05.md` (the static random-intercept model lost to the
shipped two-stage arm; its recency-weighted alternative was the best arm read post hoc). Committed
and pushed alone; the result note records this document's commit SHA as its repository state.

**What this test can and cannot confirm — read first.** Every one of the 674 walk-forward rows has
already been seen twice: the static study chose the *additive scale* on them (it beat the log scale
+0.168, CI excluding zero) and found that *recency matters* on them (a half-life-one heuristic beat
the shipped combined arm +0.091, CI [+0.024, +0.159], read after the primary lost). This
pre-registration therefore confirms only what those reads did **not** tune: whether a **random-walk
ability with a fitted innovation variance** reproduces the heuristic's gain without anyone choosing a
half-life. The 2025 fold has been seen by the heuristic too, so it is read once as a confirmation
block and cannot launder the selection. **The only clean test is the 2026-27 prospective set**, and
Amendment 10 (proposed with the result) is what would admit this arm there — as a secondary arm,
scored beside the primary, never as the basis.

## Specification

| Choice | This study | Alternatives printed |
|---|---|---|
| **Unit** | one (player, destination season) transfer scored by the walk-forward — the validator's rows, reproduced to 1e-6 against `walkforward_summary.json` or the script stops | — |
| **Population for the gate** | selection folds **2020–2024 pooled** (n ≈ 547) | confirmation fold **2025** (n = 127), read once, reported as its own block, **never pooled** into the gate |
| **Model** | `rate_{p,L,t} = α_{p,t} + β_L + ε`, `α_{p,t} = α_{p,t−1} + η_t`, `η ~ N(0, q · gap)`, `ε ~ N(0, σ²/games)`, `α_{p,first} ~ N(μ, τ²)`; **additive scale** (chosen on the static study's evidence, see above) | log scale with a 0.1 floor (`dyn_log`) |
| **League effects β** | two-way fixed effects on the same-season dual-tier pairs with season < S, weights `min(minutes)`, EuroLeague pinned at 0, additive differences | — (the confounded all-stints route is already known not to help; not re-tested) |
| **σ²** | from the same-season pairs: two stints in one season share `α_{p,t}`, so `E[(r₁ − r₂)²] = σ²(1/W₁ + 1/W₂)`; `r` = league-adjusted rate, `W` = games | — |
| **q (innovation variance)** | method of moments on consecutive observed seasons of the same player: `E[(Δr̄)²] = q · gap + σ²(1/W_t + 1/W_{t−1})`, `gap` = seasons between them; floored at 1e-6 with a printed `q_floored` flag | `q = 0` (must recover the static additive arm to within tolerance — a **filter-correctness check**, pre-registered); `q` doubled and halved (sensitivity) |
| **μ, τ²** | DerSimonian–Laird on each player's first observed season, precision `W/σ²` | — |
| **Filter / forecast** | Kalman filter per player over seasons < S (several stints in one season are several observations of the same `α_{p,t}`); forecast `E[α_{p,S}] = E[α_{p,S−1} \| data]`, variance grown by `q · gap`; prediction `ŷ = E[α_{p,S}] + β_D`; a debutant (no stint before S) falls back to the source stint shrunk toward μ, declared | — |
| **Comparators on the same rows** | the shipped combined arm (`rtm_plus_league`) — **the bar**; `hier_additive` (static, same scale); `hier_recency1` (the heuristic); per-league, RTM, one global, B0 | — |
| **Uncertainty** | paired cluster bootstrap on destination club-season, 4,000 draws, seed 0 (the validator's) | — |
| **Falsifier** | shuffled domestic β within each fold, 200 reps, against the tier-β decomposition (`dyn_tier_beta`); reported, not asserted | — |

**Estimator hygiene, declared.** Stints under 36 minutes are dropped (as in the static study).
Additive predictions are **not** clipped at zero; a negative prediction is scored as is and counted
(`n_negative_predictions` printed). Every floor (σ², q, τ²) prints a flag; a floored component is
reported, never silently used. `q` is estimated once per fold on rows strictly before the scored
season, like every other component. **No hyperparameter is tuned on any scored row.**

## Threats, and the control for each

| # | threat | control |
|---|---|---|
| T1 | the filter is wrong (a coding error, not a modelling one) | `q = 0` must reproduce the static additive hierarchical arm's predictions to within 0.05 MAE on the same rows; the script prints the gap |
| T2 | `q` absorbs league mis-adjustment rather than ability drift | `q` is estimated on league-adjusted residuals; the `dyn_tier_beta` arm shows how much the mapping contributes |
| T3 | recency gain is a 2024–2025 artefact (two weak seasons for the static arm) | per-fold table; the gate is pooled 2020–2024, the 2025 block is separate |
| T4 | the additive scale predicts negative rates for weak players | counted and printed; scored as is |
| T5 | selection on these rows (additive, "recency matters") flatters the arm | stated above; the arm's claim is limited to *structure*, and the clean test is prospective |
| T6 | a debutant fallback dominates a fold | share of rows on the fallback printed per fold |
| T7 | a floored variance component | flags printed per fold and per arm |

## Success criteria — the bar is the combined arm's MAE on the same rows, never a fixed number

On the pooled selection folds 2020–2024, paired cluster bootstrap of `MAE(combined) − MAE(dyn)`:

* **PASS** — the dynamic arm beats the combined arm and the 95% CI excludes zero.
* **PARTIAL** — the point estimate favours the dynamic arm and the CI spans zero.
* **FAIL** — the combined arm wins with the CI excluding zero, **or** T1 fails (the filter does not
  recover the static arm at `q = 0`), whichever is read first.

Secondary reads, reported, no verdict: `dyn` vs `hier_recency1` (does the fitted structure reproduce
the heuristic's gain?); `dyn` vs `hier_additive` (what does drift buy over a static ability?); the
2025 confirmation block on the same contrasts.

## Power, stated before the run

The heuristic-vs-combined contrast at n = 674 had a bootstrap half-width of 0.068 (SE ≈ 0.035). On
n ≈ 547 selection rows the SE is about 0.038. With a two-sided α of 0.05:

| true Δ (MAE) | power |
|---|---|
| 0.05 | ≈ 0.26 |
| 0.09 (the heuristic's observed gain) | ≈ 0.66 |
| 0.12 | ≈ 0.88 |

So a PARTIAL is the likeliest outcome if the true gain is what the heuristic showed, and a PARTIAL is
what this document predicts. That is not a reason to move the bar (METHOD.md §8); it is the reason
the prospective set matters.

## What each verdict licenses

* **PASS or PARTIAL:** propose Amendment 10 — the dynamic arm as a **secondary arm scored beside the
  primary on the 2026-27 set**, point predictions only (the lock's conformal interval was calibrated
  on `per_league` residuals and does not transfer), produced by this generator from the corpus
  (players joined by `pairing_key`, as `build_translation_predictions.py` does). No bar, no basis
  change, needs Amir's acceptance. The abstract is unchanged on every branch.
* **FAIL:** the same battery, the same note, and the amendment is filed as a record of what was
  tried and why it is not carried.

## Scripts (to be written after this document is committed)

* `scripts/validate_translation_dynamic.py` — the generator; writes `dynamic_summary.json` and
  `dynamic_rows.parquet` to `data/processed/translation/`.
* `tests/test_scripts/test_validate_translation_dynamic.py` — synthetic tests, each
  mutation-verified: σ² from shared-season stints; `q` from consecutive differences with the gap
  scaling; the Kalman update and forecast against the closed form on one player; `q = 0` equals the
  static posterior; no row from the scored season enters its fit; the debutant fallback; the
  additive prediction is unclipped.

## Provenance

Written 2026-09-05 from `translation-hierarchical-arm-2026-09-05.md` (`hierarchical_summary.json`
of run 4: `hier_additive_vs_hier` +0.168 [+0.102, +0.237]; `hier_recency1_vs_rtm_plus_league`
+0.091 [+0.024, +0.159]) and `translation-propositions-2026-09-04.md` P3–P4. No corpus computation
was performed for this document.
