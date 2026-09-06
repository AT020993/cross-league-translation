import TranslationPropositions.Moments

/-!
# Proposition 2 — the reliability of the target caps every model's R²

Finite (Cauchy–Schwarz) form.  Over the finite set `s` of scored player-seasons,
`f i` is any predictor's output, `T i` the player's true destination rate and
`e i` the game-sampling noise, so the observed target is `Y = T + e`.

The note's assumption `E[e | T, X] = 0` is used only through its two
consequences, orthogonality of the noise to the predictor and to the true score,
and those are the hypotheses here.

* `P2_raw_inner_bound` — inner-product form with `Σ f_i e_i = 0`:
  `(Σ f_i (T_i + e_i))² ≤ (Σ f_i²)(Σ T_i²)`.
* `P2_corrSq_le_reliability` — population-moment form: if `Cov(f, e) = 0` then
  `Corr(f, Y)² = Cov(f,Y)² / (Var f · Var Y) ≤ Var T / Var Y`.
* `P2_reliability_eq` — with `Cov(T, e) = 0` the ceiling is
  `Var T / (Var T + Var e)`, the reliability `ρ_Y`.
-/

open Finset

namespace TranslationPropositions

variable {ι : Type*} {s : Finset ι}

/-- Inner-product form of Proposition 2: noise orthogonal to the predictor. -/
theorem P2_raw_inner_bound (f T e : ι → ℝ) (hfe : ∑ i ∈ s, f i * e i = 0) :
    (∑ i ∈ s, f i * (T i + e i)) ^ 2 ≤ (∑ i ∈ s, f i ^ 2) * ∑ i ∈ s, T i ^ 2 := by
  have h : ∑ i ∈ s, f i * (T i + e i) = ∑ i ∈ s, f i * T i := by
    rw [← sub_eq_zero, ← sum_sub_distrib, ← hfe]
    exact sum_congr rfl fun i _ => by ring
  rw [h]
  exact sum_mul_sq_le_sq_mul_sq s f T

/-- Squared correlation of `f` with the observed target `Y = T + e`, in the form
`Cov(f, Y)² / (Var f · Var Y)`. -/
noncomputable def corrSq (s : Finset ι) (f Y : ι → ℝ) : ℝ :=
  cov s f Y ^ 2 / (var s f * var s Y)

/-- **Proposition 2.** If the noise is uncorrelated with the predictor,
`Corr(f, T + e)² ≤ Var T / Var (T + e)`. -/
theorem P2_corrSq_le_reliability (f T e : ι → ℝ) (hfe : cov s f e = 0)
    (hf : var s f ≠ 0) (hY : var s (T + e) ≠ 0) :
    corrSq s f (T + e) ≤ var s T / var s (T + e) := by
  have hf' : 0 < var s f := lt_of_le_of_ne (var_nonneg f) (Ne.symm hf)
  have hY' : 0 < var s (T + e) := lt_of_le_of_ne (var_nonneg _) (Ne.symm hY)
  unfold corrSq
  rw [cov_add_right, hfe, add_zero, ← div_div]
  apply div_le_div_of_nonneg_right _ hY'.le
  rw [div_le_iff₀ hf']
  linarith [cov_sq_le_var_mul_var (s := s) f T]

/-- With `Cov(T, e) = 0` the ceiling is the reliability `Var T / (Var T + Var e)`. -/
theorem P2_reliability_eq (T e : ι → ℝ) (hTe : cov s T e = 0) :
    var s T / var s (T + e) = var s T / (var s T + var s e) := by
  rw [var_add, hTe, mul_zero, add_zero]

/-- Combined statement: `Corr(f, Y)² ≤ ρ_Y = Var T / (Var T + Var e)`. -/
theorem P2_corrSq_le_rho (f T e : ι → ℝ) (hfe : cov s f e = 0) (hTe : cov s T e = 0)
    (hf : var s f ≠ 0) (hY : var s (T + e) ≠ 0) :
    corrSq s f (T + e) ≤ var s T / (var s T + var s e) := by
  rw [← P2_reliability_eq T e hTe]
  exact P2_corrSq_le_reliability f T e hfe hf hY

end TranslationPropositions
