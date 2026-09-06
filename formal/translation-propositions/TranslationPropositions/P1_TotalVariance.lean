import Mathlib

/-!
# Proposition 1 — league identity bounds what any league-only predictor can gain

Finite-population form of the law of total variance.  Index set `ι` = the
player-season pairs, `c i` = the league cell of pair `i`, `R i` = its realised
translation ratio.  A *league-only predictor* is any `g : C → ℝ` read through
the cell labelling, `g (c i)`.  Uniform weights (every pair counts once).

* `P1_cellMean_optimal`: the cell-mean predictor has the smallest sum of squared
  errors among all league-only predictors (so among them the oracle is
  `E[R | L]`).
* `P1_gain_le_between`: for **any** league-only predictor `g`, the gain in sum of
  squares over the constant predictor `mean R` is at most the between-cell sum
  of squares `Σ (E[R|L_i] − E[R])²`, i.e. `n · Var(E[R | L])`.
* `P1_gap_eq_between`: for the cell means the bound is attained exactly.
Dividing by `n` turns every statement into the MSE form used in the note.
-/

open Finset

namespace TranslationPropositions

variable {ι C : Type*} [Fintype ι] [DecidableEq C]

/-- Indices in league cell `k`. -/
def cell (c : ι → C) (k : C) : Finset ι := univ.filter (fun i => c i = k)

/-- The within-cell mean `E[R | L = k]` (`0` for an empty cell, which never occurs
as `c i`). -/
noncomputable def cellMean (c : ι → C) (R : ι → ℝ) (k : C) : ℝ :=
  (∑ i ∈ cell c k, R i) / (cell c k).card

/-- The grand mean `E[R]` with uniform weights. -/
noncomputable def gmean (R : ι → ℝ) : ℝ := (∑ i, R i) / Fintype.card ι

lemma sum_cell_sub_cellMean (c : ι → C) (R : ι → ℝ) (k : C) :
    ∑ i ∈ cell c k, (R i - cellMean c R k) = 0 := by
  rw [sum_sub_distrib, sum_const, nsmul_eq_mul, cellMean]
  rcases (cell c k).eq_empty_or_nonempty with h | h
  · simp [h]
  · have : ((cell c k).card : ℝ) ≠ 0 := by exact_mod_cast h.card_pos.ne'
    field_simp
    ring

variable [Fintype C]

/-- The residual `R − E[R | L]` is orthogonal to every function of the cell
(`E[R − E[R|L] | L] = 0`). -/
lemma sum_residual_mul (c : ι → C) (R : ι → ℝ) (h : C → ℝ) :
    ∑ i, (R i - cellMean c R (c i)) * h (c i) = 0 := by
  rw [← Finset.sum_fiberwise univ c]
  apply sum_eq_zero
  intro k _
  have hc : ∀ i ∈ cell c k, (R i - cellMean c R (c i)) * h (c i)
      = (R i - cellMean c R k) * h k := by
    intro i hi
    have : c i = k := (mem_filter.mp hi).2
    rw [this]
  change ∑ i ∈ cell c k, _ = 0
  rw [sum_congr rfl hc, ← sum_mul, sum_cell_sub_cellMean, zero_mul]

/-- Pythagoras / law of total variance for a league-only predictor `g`:
`Σ (R − g(L))² = Σ (R − E[R|L])² + Σ (E[R|L] − g(L))²`. -/
theorem P1_sq_decomposition (c : ι → C) (R : ι → ℝ) (g : C → ℝ) :
    ∑ i, (R i - g (c i)) ^ 2
      = ∑ i, (R i - cellMean c R (c i)) ^ 2 + ∑ i, (cellMean c R (c i) - g (c i)) ^ 2 := by
  have h := sum_residual_mul c R (fun k => cellMean c R k - g k)
  have e : ∀ i, (R i - g (c i)) ^ 2
      = (R i - cellMean c R (c i)) ^ 2 + (cellMean c R (c i) - g (c i)) ^ 2
        + 2 * ((R i - cellMean c R (c i)) * (cellMean c R (c i) - g (c i))) := fun i => by ring
  rw [sum_congr rfl fun i _ => e i, sum_add_distrib, sum_add_distrib, ← mul_sum, h]
  ring

/-- The cell means are the best league-only predictor (least squares). -/
theorem P1_cellMean_optimal (c : ι → C) (R : ι → ℝ) (g : C → ℝ) :
    ∑ i, (R i - cellMean c R (c i)) ^ 2 ≤ ∑ i, (R i - g (c i)) ^ 2 := by
  rw [P1_sq_decomposition c R g]
  exact le_add_of_nonneg_right (sum_nonneg fun i _ => sq_nonneg _)

/-- The gain of the cell-mean predictor over the constant predictor is exactly the
between-cell sum of squares `Σ (E[R|L_i] − E[R])² = n · Var(E[R|L])`. -/
theorem P1_gap_eq_between (c : ι → C) (R : ι → ℝ) :
    ∑ i, (R i - gmean R) ^ 2 - ∑ i, (R i - cellMean c R (c i)) ^ 2
      = ∑ i, (cellMean c R (c i) - gmean R) ^ 2 := by
  rw [P1_sq_decomposition c R (fun _ => gmean R)]
  ring

/-- **Proposition 1.** No league-only predictor gains more over the constant than the
between-cell sum of squares: `SS(const) − SS(g(L)) ≤ Σ (E[R|L_i] − E[R])²`. -/
theorem P1_gain_le_between (c : ι → C) (R : ι → ℝ) (g : C → ℝ) :
    ∑ i, (R i - gmean R) ^ 2 - ∑ i, (R i - g (c i)) ^ 2
      ≤ ∑ i, (cellMean c R (c i) - gmean R) ^ 2 := by
  rw [← P1_gap_eq_between c R]
  linarith [P1_cellMean_optimal c R g]

/-- MSE form with `η² := between / total`: `MSE(const) − MSE(g) ≤ η² · Var(R)` when
`Var(R) ≠ 0`. -/
theorem P1_gain_le_etaSq_mul_total (c : ι → C) (R : ι → ℝ) (g : C → ℝ)
    (htot : ∑ i, (R i - gmean R) ^ 2 ≠ 0) :
    (∑ i, (R i - gmean R) ^ 2 - ∑ i, (R i - g (c i)) ^ 2) / Fintype.card ι
      ≤ ((∑ i, (cellMean c R (c i) - gmean R) ^ 2) / (∑ i, (R i - gmean R) ^ 2))
          * ((∑ i, (R i - gmean R) ^ 2) / Fintype.card ι) := by
  rw [div_mul_div_comm, mul_comm (∑ i, (cellMean c R (c i) - gmean R) ^ 2),
    mul_div_mul_left _ _ htot]
  exact div_le_div_of_nonneg_right (P1_gain_le_between c R g) (Nat.cast_nonneg _)

end TranslationPropositions
