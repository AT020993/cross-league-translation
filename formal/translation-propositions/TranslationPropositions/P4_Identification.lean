import Mathlib

/-!
# Proposition 4 — what the same-season design identifies

`V` is the finite set of leagues and `G` the league graph: two leagues are
adjacent when some player-season is observed in both in the same season.  In the
two-way fixed-effects model `log rate = α_p + β_L + ε`, the within-pair difference
`β_dest − β_src` is observed on every edge, so a vector of league effects `β` is
*unidentified* exactly when it is in the kernel of the graph Laplacian
(`SimpleGraph.lapMatrix`): `Lap β = 0 ↔ β_i = β_j on every edge`.

* `P4_i_player_effect_cancels` — (i) the player term cancels in the difference.
* `P4_ii_ker_dim_eq_card_components` — (ii) `dim ker Lap = #components`
  (Mathlib's `card_connectedComponent_eq_finrank_ker_toLin'_lapMatrix`).
* `P4_ii_rank_add_components` — hence `rank Lap + #components = #leagues`.
* `P4_ii_connected_iff_ker_const` — `G` connected ↔ every `x` with `Lap x = 0` is
  constant, i.e. league effects are identified up to one additive constant.
-/

open Finset Matrix

namespace TranslationPropositions

/-- (i) Cancellation: in a same-season pair the player effect `α` drops out of the
log ratio, leaving `β_dest − β_src` plus the noise difference. -/
theorem P4_i_player_effect_cancels (α βdest βsrc εdest εsrc : ℝ) :
    (α + βdest + εdest) - (α + βsrc + εsrc) = (βdest - βsrc) + (εdest - εsrc) := by
  ring

variable {V : Type*} [Fintype V] [DecidableEq V] (G : SimpleGraph V) [DecidableRel G.Adj]

/-- (ii) The dimension of the Laplacian's kernel is the number of connected components. -/
theorem P4_ii_ker_dim_eq_card_components :
    Module.finrank ℝ (LinearMap.ker (Matrix.toLin' (G.lapMatrix ℝ)))
      = Fintype.card G.ConnectedComponent :=
  (G.card_connectedComponent_eq_finrank_ker_toLin'_lapMatrix).symm

/-- (ii) Rank form: `rank Lap = #leagues − #components`. -/
theorem P4_ii_rank_add_components :
    (G.lapMatrix ℝ).rank + Fintype.card G.ConnectedComponent = Fintype.card V := by
  rw [← P4_ii_ker_dim_eq_card_components, Matrix.rank, ← Matrix.toLin'_apply',
    LinearMap.finrank_range_add_finrank_ker, Module.finrank_fintype_fun_eq_card]

/-- Kernel vectors are exactly the functions constant on connected components. -/
theorem P4_ii_ker_iff_const_on_components (x : V → ℝ) :
    G.lapMatrix ℝ *ᵥ x = 0 ↔ ∀ i j, G.Reachable i j → x i = x j :=
  G.lapMatrix_mulVec_eq_zero_iff_forall_reachable

/-- **Proposition 4(ii).** League effects are identified up to one additive constant
(every kernel vector is constant) if and only if the league graph is connected. -/
theorem P4_ii_connected_iff_ker_const [Nonempty V] :
    G.Connected ↔ ∀ x : V → ℝ, G.lapMatrix ℝ *ᵥ x = 0 → ∀ i j, x i = x j := by
  constructor
  · intro hG x hx i j
    exact (G.lapMatrix_mulVec_eq_zero_iff_forall_reachable.mp hx) i j (hG.preconnected i j)
  · intro h
    refine ⟨fun i j => ?_⟩
    classical
    -- indicator of the connected component of `i`
    let x : V → ℝ := fun k => if G.Reachable i k then 1 else 0
    have hx : G.lapMatrix ℝ *ᵥ x = 0 := by
      rw [G.lapMatrix_mulVec_eq_zero_iff_forall_reachable]
      intro k l hkl
      simp only [x]
      by_cases hk : G.Reachable i k
      · rw [if_pos hk, if_pos (hk.trans hkl)]
      · rw [if_neg hk, if_neg (fun hl => hk (hl.trans hkl.symm))]
    have hij := h x hx i j
    simp only [x, if_pos (SimpleGraph.Reachable.refl (G := G) i)] at hij
    by_contra hne
    rw [if_neg hne] at hij
    norm_num at hij

end TranslationPropositions
