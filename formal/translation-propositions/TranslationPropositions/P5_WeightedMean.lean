import TranslationPropositions.Moments

/-!
# Proposition 5 — the sign of the estimator gap is the sign of one covariance

For weights `w_i > 0` and ratios `r_i` over a nonempty finite set `s`,

  `Σ w_i r_i / Σ w_i − mean(r) = Cov(w, r) / mean(w)`,

so the ratio-of-sums estimator exceeds the mean-of-ratios estimator exactly when the
weights covary positively with the ratios.
-/

open Finset

namespace TranslationPropositions

variable {ι : Type*} {s : Finset ι}

lemma sum_pos_of_pos (hs : s.Nonempty) {w : ι → ℝ} (hw : ∀ i ∈ s, 0 < w i) :
    0 < ∑ i ∈ s, w i :=
  sum_pos hw hs

lemma mean_pos_of_pos (hs : s.Nonempty) {w : ι → ℝ} (hw : ∀ i ∈ s, 0 < w i) :
    0 < mean s w :=
  div_pos (sum_pos_of_pos hs hw) (by exact_mod_cast hs.card_pos)

/-- **Proposition 5 (identity).** -/
theorem P5_weighted_gap_eq_cov_div_mean (hs : s.Nonempty) (w r : ι → ℝ)
    (hw : ∀ i ∈ s, 0 < w i) :
    (∑ i ∈ s, w i * r i) / (∑ i ∈ s, w i) - mean s r = cov s w r / mean s w := by
  have hn := card_ne_zero_of_nonempty hs
  have hW := (sum_pos_of_pos hs hw).ne'
  rw [cov_eq_mean_mul_sub hs]
  unfold mean
  field_simp

/-- **Proposition 5 (sign corollary).** The weighted mean is at least the plain mean iff
`Cov(w, r) ≥ 0`, and strictly below it iff `Cov(w, r) < 0`. -/
theorem P5_sign (hs : s.Nonempty) (w r : ι → ℝ) (hw : ∀ i ∈ s, 0 < w i) :
    (mean s r ≤ (∑ i ∈ s, w i * r i) / (∑ i ∈ s, w i) ↔ 0 ≤ cov s w r) ∧
    ((∑ i ∈ s, w i * r i) / (∑ i ∈ s, w i) < mean s r ↔ cov s w r < 0) := by
  have hm := mean_pos_of_pos hs hw
  have h := P5_weighted_gap_eq_cov_div_mean hs w r hw
  constructor
  · rw [← sub_nonneg, h]
    constructor
    · intro h0
      by_contra hc
      linarith [div_neg_of_neg_of_pos (not_le.mp hc) hm]
    · intro h0
      exact div_nonneg h0 hm.le
  · rw [← sub_neg, h]
    constructor
    · intro h0
      by_contra hc
      linarith [div_nonneg (not_lt.mp hc) hm.le]
    · intro h0
      exact div_neg_of_neg_of_pos h0 hm

end TranslationPropositions
