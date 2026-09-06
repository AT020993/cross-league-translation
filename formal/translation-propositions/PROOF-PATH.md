# Proof path: from the research note to the Lean theorems

Companion to the research note *Five propositions behind the cross-league translation
model* (`translation-propositions-2026-09-04.md`, shipped in the companion PR under
`docs/research/`).
This file maps each proposition in the note to the Lean 4 / Mathlib theorem that
machine-checks it, states exactly what was proved, and lists every place where the
Lean statement differs from the note's prose.

Toolchain: Lean `v4.33.1`, Mathlib tag `v4.33.1` (commit `0df444a360`).
Every theorem below passes `#print axioms` with exactly
`[propext, Classical.choice, Quot.sound]` — see `TranslationPropositions/FinalCheck.lean`,
which fails the build if that ever changes. There is no `sorry`, no `axiom`, and no
`native_decide` anywhere in the package.

Two conventions used throughout:

* **Finite population, not measure theory.** The note writes expectations `E[·]` and
  population moments `Var`, `Cov`. The Lean statements are over a finite index set
  (the player-season pairs) with uniform weights, so `E[X] = (Σ xᵢ)/n`. That is the
  setting the note's numbers are computed in ("`Var` and `Cov` are population
  moments (divide by n)"), so nothing is lost; it also avoids Mathlib's measure-theoretic
  conditional expectation, which would add machinery without adding content.
* **Division by zero is zero** (Lean's convention). Every theorem that needs a
  nonzero denominator states it as a hypothesis (`s.Nonempty`, `Var f ≠ 0`, …).

Shared definitions (`TranslationPropositions/Moments.lean`): `mean s r`, `cov s w r`,
`var s r` over a `Finset s`, all dividing by `s.card`; lemmas `cov_add_right`,
`var_add`, `cov_sq_le_var_mul_var` (Cauchy–Schwarz for moments, from Mathlib's
`Finset.sum_mul_sq_le_sq_mul_sq`), `cov_eq_mean_mul_sub` (`Cov = mean(wr) − mean w · mean r`).

---

## Proposition 1 — league identity bounds what any league-only predictor can gain

File `TranslationPropositions/P1_TotalVariance.lean`. Index type `ι` (pairs), cell type
`C` (league cells), labelling `c : ι → C`, ratios `R : ι → ℝ`, any league-only predictor
`g : C → ℝ`. `cellMean c R k = E[R | L = k]`, `gmean R = E[R]`.

| Lean theorem | What it says |
|---|---|
| `P1_sq_decomposition` | `Σ (Rᵢ − g(cᵢ))² = Σ (Rᵢ − E[R∣Lᵢ])² + Σ (E[R∣Lᵢ] − g(cᵢ))²` — the cross term vanishes (`sum_residual_mul`, the finite form of `E[R − E[R∣L] ∣ L] = 0`). |
| `P1_cellMean_optimal` | `Σ (Rᵢ − E[R∣Lᵢ])² ≤ Σ (Rᵢ − g(cᵢ))²` for **every** `g`: the cell means are the least-squares oracle among league-only predictors. |
| `P1_gap_eq_between` | `Σ (Rᵢ − E[R])² − Σ (Rᵢ − E[R∣Lᵢ])² = Σ (E[R∣Lᵢ] − E[R])²` — the gain of the cell-mean predictor over the constant is exactly the between-cell sum of squares (`n · Var(E[R∣L])`). |
| `P1_gain_le_between` | **The proposition:** `SS(const) − SS(g(L)) ≤ Σ (E[R∣Lᵢ] − E[R])²` for every `g`, with equality for `g = E[R∣L]` (by the previous line). |
| `P1_gain_le_etaSq_mul_total` | MSE form: `(SS(const) − SS(g))/n ≤ η² · (SS(const)/n)` with `η² := between / total`, when `total ≠ 0`. This is the note's `MSE(constant) − MSE(g(L)) ≤ η² · Var(R)`. |

Deviations from the note: none in content. The note's proof cites `MeasureTheory.condExp`;
the Lean proof is the elementary finite-population version (fibrewise sums via
`Finset.sum_fiberwise`), which is the setting in which η² = 8.7 % / 14.5 % was measured.
An empty cell has `cellMean = 0` by convention; it never occurs as `c i`, so it never
enters a sum.

## Proposition 2 — the reliability of the target caps every model's R²

File `TranslationPropositions/P2_Reliability.lean`. `f` = predictor output, `T` = true rate,
`e` = game-sampling noise, observed target `Y = T + e`, over a `Finset s`.

| Lean theorem | What it says |
|---|---|
| `P2_raw_inner_bound` | Inner-product form: if `Σ fᵢ eᵢ = 0` then `(Σ fᵢ (Tᵢ + eᵢ))² ≤ (Σ fᵢ²)(Σ Tᵢ²)`. |
| `P2_corrSq_le_reliability` | **The proposition:** if `Cov(f, e) = 0`, `Var f ≠ 0`, `Var Y ≠ 0`, then `Corr(f, Y)² := Cov(f,Y)²/(Var f · Var Y) ≤ Var T / Var Y`. |
| `P2_reliability_eq` | If `Cov(T, e) = 0` then `Var T / Var Y = Var T / (Var T + Var e)` — the ceiling is the reliability `ρ_Y`. |
| `P2_corrSq_le_rho` | The two combined: `Corr(f, Y)² ≤ Var T / (Var T + Var e)`. |

Deviations from the note:

1. The note assumes `E[e | T, X] = 0` (mean-independence of the noise from the true score
   and from every predictor input). The Lean theorems assume only the two consequences that
   the proof actually uses: `Cov(f, e) = 0` (noise uncorrelated with the predictor) and,
   for the `ρ_Y` form, `Cov(T, e) = 0`. This is a **weaker hypothesis**, so the Lean
   statement is stronger than the note's; the note's assumption implies it.
2. The note's last sentence, "for a calibrated predictor `R² = Corr²`; in general
   `R² ≤ Corr²`", is a statement about the definition of out-of-sample R² and is **not
   formalised**. What is proved is the bound on `Corr²`, which is the quantity the note
   tabulates (`Corr² / ρ_Y` column).
3. `Corr²` is written as `Cov²/(Var f · Var Y)` rather than via a square root; the two are
   equal when the variances are positive, which is assumed.

## Proposition 3 — Spearman–Brown

File `TranslationPropositions/P3_SpearmanBrown.lean`.
`spearmanBrown r₁ n = n r₁ / (1 + (n − 1) r₁)`, `gamesNeeded r₁ ρ = ρ(1 − r₁)/(r₁(1 − ρ))`.
Throughout `0 < r₁ < 1` and `n ≥ 1`, with `n : ℝ` (so every natural `n ≥ 1` is covered).

| Lean theorem | What it says |
|---|---|
| `P3_spearmanBrown_of_variances` | (iii) derivation: with true-score variance `vT > 0` and noise variance `vE > 0`, `spearmanBrown (vT/(vT+vE)) n = vT / (vT + vE/n)` — the variance model `σ_T²/(σ_T² + σ_e²/n)`. |
| `P3_gamesNeeded_spearmanBrown` | (i) inverse identity: `gamesNeeded r₁ (spearmanBrown r₁ n) = n`. |
| `P3_spearmanBrown_mono` | (ii) monotone in `n`: `1 ≤ m ≤ n → spearmanBrown r₁ m ≤ spearmanBrown r₁ n`. |
| `P3_spearmanBrown_lt_one` | reliability of a finite number of games is strictly below 1. |
| `P3_games_for_070` | at `r₁ = 0.105`: `19 < gamesNeeded < 20`, i.e. 20 games for reliability 0.70 (the note's table). |
| `P3_games_for_090` | at `r₁ = 0.105`: `76 < gamesNeeded < 77`, i.e. 77 games for reliability 0.90. |

Deviations from the note: the exchangeability model itself (`Yᵢ = T + eᵢ` with independent
equal-variance noise, so `Var(ē_n) = σ_e²/n`) is **taken as the input** to
`P3_spearmanBrown_of_variances` — the theorem starts from the variances `vT`, `vE/n`, it does
not derive `Var(ē_n) = σ_e²/n` from independence. The note's empirical check of the
assumption is, of course, not a theorem. The numeric theorems use `r₁ = 0.105` (the
corpus-wide inversion), not the fitted `0.112`.

## Proposition 4 — what the same-season design identifies

File `TranslationPropositions/P4_Identification.lean`. `V` = leagues (finite, decidable
equality), `G : SimpleGraph V` the league graph (adjacent ⇔ some same-season pair links them),
`G.lapMatrix ℝ` Mathlib's graph Laplacian.

| Lean theorem | What it says |
|---|---|
| `P4_i_player_effect_cancels` | (i) `(α + β_dest + ε_dest) − (α + β_src + ε_src) = (β_dest − β_src) + (ε_dest − ε_src)`. |
| `P4_ii_ker_dim_eq_card_components` | (ii) `dim ker(Lap) = #connected components` — Mathlib's `SimpleGraph.card_connectedComponent_eq_finrank_ker_toLin'_lapMatrix`, restated. |
| `P4_ii_rank_add_components` | (ii) `rank(Lap) + #components = #leagues`, i.e. `rank Lap = n − c` (rank–nullity). |
| `P4_ii_ker_iff_const_on_components` | `Lap x = 0 ↔ x` is constant on every connected component (Mathlib's `lapMatrix_mulVec_eq_zero_iff_forall_reachable`). |
| `P4_ii_connected_iff_ker_const` | **The proposition:** for nonempty `V`, `G` connected ↔ every `x` with `Lap x = 0` is constant — league effects are identified up to exactly one additive constant iff the league graph is connected. |

Deviations from the note:

1. The note's Laplacian is the **exposure-weighted** `Xᵀ W X` of the pair-incidence matrix;
   Mathlib's `lapMatrix` is the **unweighted** Laplacian of the simple graph (one edge per
   linked pair of leagues). The kernel is the same — a vector is in the kernel of either
   matrix iff it is constant on every connected component, and this depends only on which
   edges exist, not on their positive weights — so the identification statement is
   unchanged; but the weighted rank identity is not literally what was checked.
2. Part (iii) of the note (a level shift from conditioning on `ε_src`) is a statement about
   conditional expectations under a selection event and is **not formalised**; it is the
   measured `−0.122` in the note, not a theorem candidate.
3. (i) is a one-line ring identity; it is included because the note calls it part of the
   proposition, not because it needs a machine.

## Proposition 5 — the sign of the estimator gap is the sign of one covariance

File `TranslationPropositions/P5_WeightedMean.lean`. Nonempty `Finset s`, weights `w` with
`wᵢ > 0` on `s`, ratios `r`.

| Lean theorem | What it says |
|---|---|
| `P5_weighted_gap_eq_cov_div_mean` | **The proposition:** `Σ wᵢ rᵢ / Σ wᵢ − mean r = Cov(w, r) / mean w`. |
| `P5_sign` | Sign corollary: `mean r ≤ Σwr/Σw ↔ 0 ≤ Cov(w, r)` and `Σwr/Σw < mean r ↔ Cov(w, r) < 0`. |

Deviations from the note: none. `Cov` is the population covariance (divide by `n`), exactly
as in the note; the two-line proof (`Σ wᵢ rᵢ / n = Cov(w, r) + mean(w) mean(r)`) is
`cov_eq_mean_mul_sub` in `Moments.lean`.

---

## Summary of what is and is not machine-checked

Checked (22 theorems, standard axioms only): P1 in full (bound, attainment, MSE form);
P2's correlation ceiling under uncorrelated noise, and its `ρ_Y` form; P3's formula,
derivation from variances, inverse, monotonicity, `< 1`, and the two numeric game counts;
P4(i) and P4(ii) (kernel dimension, rank, connectivity ↔ identification up to a constant);
P5's identity and sign corollary.

Not checked, by design: the definition-level remark `R² ≤ Corr²` (P2); the exchangeability
→ `σ_e²/n` step (P3, taken as input); P4(iii), the selection level shift, which is an
empirical quantity; the weighted (as opposed to unweighted) Laplacian in P4(ii).
