import Mathlib

/-!
# Proposition 3 — Spearman–Brown, and how many games a reliable target needs

`spearmanBrown r₁ n = n r₁ / (1 + (n − 1) r₁)` is the reliability of the mean of
`n` exchangeable games each of reliability `r₁`; `gamesNeeded r₁ ρ` inverts it.

* `P3_spearmanBrown_of_variances` — derivation from the variance model
  `σ_T² / (σ_T² + σ_e²/n)` with `r₁ = σ_T² / (σ_T² + σ_e²)`.
* `P3_gamesNeeded_spearmanBrown` — the inverse identity `n(ρ_n) = n`.
* `P3_spearmanBrown_mono` — reliability is monotone in the number of games.
* `P3_spearmanBrown_lt_one` — and always strictly below `1`.
* `P3_games_for_070`, `P3_games_for_090` — the note's numbers at `r₁ = 0.105`:
  20 games for reliability 0.70, 77 for 0.90.
`n` is a real number (so `n ≥ 1` covers every natural number of games ≥ 1).
-/

namespace TranslationPropositions

/-- Spearman–Brown prophecy formula. -/
noncomputable def spearmanBrown (r₁ n : ℝ) : ℝ := n * r₁ / (1 + (n - 1) * r₁)

/-- Games needed for reliability `ρ` given per-game reliability `r₁`. -/
noncomputable def gamesNeeded (r₁ ρ : ℝ) : ℝ := ρ * (1 - r₁) / (r₁ * (1 - ρ))

lemma denom_pos {r₁ n : ℝ} (hr : 0 < r₁) (hr1 : r₁ < 1) (hn : 1 ≤ n) :
    0 < 1 + (n - 1) * r₁ := by
  nlinarith

/-- (iii) Derivation from the variance model: with true-score variance `vT` and
per-game noise variance `vE`, `r₁ = vT / (vT + vE)` and the `n`-game mean has
reliability `vT / (vT + vE / n)`. -/
theorem P3_spearmanBrown_of_variances {vT vE n : ℝ} (hT : 0 < vT) (hE : 0 < vE) (hn : 1 ≤ n) :
    spearmanBrown (vT / (vT + vE)) n = vT / (vT + vE / n) := by
  have h1 : vT + vE ≠ 0 := by positivity
  have h2 : n ≠ 0 := by positivity
  have h3 : vT + vE / n ≠ 0 := by positivity
  have h4 : 1 + (n - 1) * (vT / (vT + vE)) ≠ 0 := by
    have : 0 < vT / (vT + vE) := by positivity
    have : vT / (vT + vE) < 1 := by rw [div_lt_one (by positivity)]; linarith
    exact (denom_pos ‹0 < vT / (vT + vE)› ‹vT / (vT + vE) < 1› hn).ne'
  have h5 : n * vT + vE ≠ 0 := by positivity
  unfold spearmanBrown
  rw [div_eq_div_iff h4 h3]
  field_simp
  ring

lemma one_sub_spearmanBrown {r₁ n : ℝ} (hr : 0 < r₁) (hr1 : r₁ < 1) (hn : 1 ≤ n) :
    1 - spearmanBrown r₁ n = (1 - r₁) / (1 + (n - 1) * r₁) := by
  have hd := (denom_pos hr hr1 hn).ne'
  unfold spearmanBrown
  rw [eq_div_iff hd, sub_mul, div_mul_cancel₀ _ hd]
  ring

/-- (iv) Reliability is always strictly below one. -/
theorem P3_spearmanBrown_lt_one {r₁ n : ℝ} (hr : 0 < r₁) (hr1 : r₁ < 1) (hn : 1 ≤ n) :
    spearmanBrown r₁ n < 1 := by
  have h := one_sub_spearmanBrown hr hr1 hn
  have : 0 < (1 - r₁) / (1 + (n - 1) * r₁) := div_pos (by linarith) (denom_pos hr hr1 hn)
  linarith

/-- (i) Inverse identity: `gamesNeeded r₁ (spearmanBrown r₁ n) = n`. -/
theorem P3_gamesNeeded_spearmanBrown {r₁ n : ℝ} (hr : 0 < r₁) (hr1 : r₁ < 1) (hn : 1 ≤ n) :
    gamesNeeded r₁ (spearmanBrown r₁ n) = n := by
  have hd := (denom_pos hr hr1 hn).ne'
  unfold gamesNeeded
  rw [one_sub_spearmanBrown hr hr1 hn]
  unfold spearmanBrown
  have h1r : (1 - r₁) ≠ 0 := by linarith
  rw [div_eq_iff (mul_ne_zero hr.ne' (div_ne_zero h1r hd)), div_mul_eq_mul_div,
    ← mul_assoc, mul_comm n r₁, mul_assoc, mul_div_assoc, mul_div_assoc, mul_assoc]

/-- (ii) Monotonicity in the number of games. -/
theorem P3_spearmanBrown_mono {r₁ m n : ℝ} (hr : 0 < r₁) (hr1 : r₁ < 1) (hm : 1 ≤ m)
    (hmn : m ≤ n) : spearmanBrown r₁ m ≤ spearmanBrown r₁ n := by
  have hn : 1 ≤ n := hm.trans hmn
  unfold spearmanBrown
  rw [div_le_div_iff₀ (denom_pos hr hr1 hm) (denom_pos hr hr1 hn)]
  nlinarith [mul_nonneg (mul_nonneg hr.le (sub_nonneg.mpr hr1.le)) (sub_nonneg.mpr hmn)]

/-- The note's number: at `r₁ = 0.105`, reliability 0.70 needs between 19 and 20 games,
so 20 destination games. -/
theorem P3_games_for_070 :
    19 < gamesNeeded (105 / 1000) (70 / 100) ∧ gamesNeeded (105 / 1000) (70 / 100) < 20 := by
  unfold gamesNeeded
  constructor <;> norm_num

/-- And reliability 0.90 needs between 76 and 77 games — more than any European season. -/
theorem P3_games_for_090 :
    76 < gamesNeeded (105 / 1000) (90 / 100) ∧ gamesNeeded (105 / 1000) (90 / 100) < 77 := by
  unfold gamesNeeded
  constructor <;> norm_num

end TranslationPropositions
