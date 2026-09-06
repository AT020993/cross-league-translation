import Mathlib

/-!
# Population moments over a finite index set

Shared definitions for Propositions 2 and 5 of the research note
`translation-propositions-2026-09-04.md`.  All moments are *population*
moments (divide by `n`, the number of indices), exactly as in the note.
`s` is the finite set of player-season pairs (or games, or cells) the moment
is taken over.  When `s` is empty every quantity is `0` by Lean's convention
`x / 0 = 0`; every theorem that needs `s` nonempty says so.
-/

open Finset

namespace TranslationPropositions

variable {ι : Type*} (s : Finset ι)

/-- Population mean `mean(r) = (Σ_{i ∈ s} r_i) / n`. -/
noncomputable def mean (r : ι → ℝ) : ℝ := (∑ i ∈ s, r i) / s.card

/-- Population covariance `Cov(w, r) = (Σ (w_i − mean w)(r_i − mean r)) / n`. -/
noncomputable def cov (w r : ι → ℝ) : ℝ :=
  (∑ i ∈ s, (w i - mean s w) * (r i - mean s r)) / s.card

/-- Population variance `Var(r) = (Σ (r_i − mean r)²) / n`. -/
noncomputable def var (r : ι → ℝ) : ℝ := (∑ i ∈ s, (r i - mean s r) ^ 2) / s.card

variable {s}

lemma card_ne_zero_of_nonempty (hs : s.Nonempty) : (s.card : ℝ) ≠ 0 := by
  exact_mod_cast hs.card_pos.ne'

lemma mean_add (f g : ι → ℝ) : mean s (f + g) = mean s f + mean s g := by
  unfold mean
  rw [← add_div, ← sum_add_distrib]
  rfl

lemma var_nonneg (r : ι → ℝ) : 0 ≤ var s r :=
  div_nonneg (sum_nonneg fun _ _ => sq_nonneg _) (Nat.cast_nonneg _)

lemma var_eq_cov_self (r : ι → ℝ) : var s r = cov s r r := by
  unfold var cov
  congr 1
  exact sum_congr rfl fun i _ => by ring

/-- Bilinearity in the second slot. -/
lemma cov_add_right (f g h : ι → ℝ) : cov s f (g + h) = cov s f g + cov s f h := by
  unfold cov
  rw [mean_add, ← add_div, ← sum_add_distrib]
  congr 1
  exact sum_congr rfl fun i _ => by simp only [Pi.add_apply]; ring

lemma cov_comm (f g : ι → ℝ) : cov s f g = cov s g f := by
  unfold cov
  congr 1
  exact sum_congr rfl fun i _ => by ring

/-- `Var(g + h) = Var g + 2 Cov(g, h) + Var h`. -/
lemma var_add (g h : ι → ℝ) : var s (g + h) = var s g + 2 * cov s g h + var s h := by
  unfold var cov
  rw [mean_add, mul_div_assoc', ← add_div, ← add_div, mul_sum, ← sum_add_distrib,
    ← sum_add_distrib]
  congr 1
  exact sum_congr rfl fun i _ => by simp only [Pi.add_apply]; ring

/-- **Cauchy–Schwarz for population moments**: `Cov(f, g)² ≤ Var f · Var g`. -/
lemma cov_sq_le_var_mul_var (f g : ι → ℝ) : cov s f g ^ 2 ≤ var s f * var s g := by
  unfold cov var
  rw [div_pow, div_mul_div_comm, ← sq]
  exact div_le_div_of_nonneg_right (sum_mul_sq_le_sq_mul_sq s _ _) (sq_nonneg _)

/-- `Cov(w, r) = mean(w·r) − mean w · mean r` (the two-line proof in the note). -/
lemma cov_eq_mean_mul_sub (hs : s.Nonempty) (w r : ι → ℝ) :
    cov s w r = (∑ i ∈ s, w i * r i) / s.card - mean s w * mean s r := by
  have hn := card_ne_zero_of_nonempty hs
  unfold cov mean
  have key : ∑ i ∈ s, (w i - (∑ j ∈ s, w j) / s.card) * (r i - (∑ j ∈ s, r j) / s.card)
      = ∑ i ∈ s, w i * r i - (∑ j ∈ s, w j) * (∑ j ∈ s, r j) / s.card := by
    have h1 : ∀ i ∈ s, (w i - (∑ j ∈ s, w j) / s.card) * (r i - (∑ j ∈ s, r j) / s.card)
        = w i * r i - ((∑ j ∈ s, r j) / s.card) * w i - ((∑ j ∈ s, w j) / s.card) * r i
          + ((∑ j ∈ s, w j) / s.card) * ((∑ j ∈ s, r j) / s.card) := fun i _ => by ring
    rw [sum_congr rfl h1, sum_add_distrib, sum_sub_distrib, sum_sub_distrib, ← mul_sum, ← mul_sum,
      sum_const, nsmul_eq_mul]
    field_simp
    ring
  rw [key]
  field_simp

end TranslationPropositions
