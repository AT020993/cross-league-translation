import TranslationPropositions.P1_TotalVariance
import TranslationPropositions.P2_Reliability
import TranslationPropositions.P3_SpearmanBrown
import TranslationPropositions.P4_Identification
import TranslationPropositions.P5_WeightedMean

/-!
# Final check: axioms used by every theorem

Each `#guard_msgs` block fails the build unless `#print axioms` reports exactly the
three standard axioms of Lean/Mathlib (`propext`, `Classical.choice`, `Quot.sound`).
No `sorry`, no `axiom`, no `native_decide` can pass this file.
-/

open TranslationPropositions

-- P1_TotalVariance
/-- info: 'TranslationPropositions.P1_sq_decomposition' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms TranslationPropositions.P1_sq_decomposition

/-- info: 'TranslationPropositions.P1_cellMean_optimal' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms TranslationPropositions.P1_cellMean_optimal

/-- info: 'TranslationPropositions.P1_gap_eq_between' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms TranslationPropositions.P1_gap_eq_between

/-- info: 'TranslationPropositions.P1_gain_le_between' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms TranslationPropositions.P1_gain_le_between

/-- info: 'TranslationPropositions.P1_gain_le_etaSq_mul_total' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms TranslationPropositions.P1_gain_le_etaSq_mul_total

-- P2_Reliability
/-- info: 'TranslationPropositions.P2_raw_inner_bound' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms TranslationPropositions.P2_raw_inner_bound

/-- info: 'TranslationPropositions.P2_corrSq_le_reliability' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms TranslationPropositions.P2_corrSq_le_reliability

/-- info: 'TranslationPropositions.P2_reliability_eq' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms TranslationPropositions.P2_reliability_eq

/-- info: 'TranslationPropositions.P2_corrSq_le_rho' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms TranslationPropositions.P2_corrSq_le_rho

-- P3_SpearmanBrown
/-- info: 'TranslationPropositions.P3_spearmanBrown_of_variances' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms TranslationPropositions.P3_spearmanBrown_of_variances

/-- info: 'TranslationPropositions.P3_gamesNeeded_spearmanBrown' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms TranslationPropositions.P3_gamesNeeded_spearmanBrown

/-- info: 'TranslationPropositions.P3_spearmanBrown_mono' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms TranslationPropositions.P3_spearmanBrown_mono

/-- info: 'TranslationPropositions.P3_spearmanBrown_lt_one' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms TranslationPropositions.P3_spearmanBrown_lt_one

/-- info: 'TranslationPropositions.P3_games_for_070' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms TranslationPropositions.P3_games_for_070

/-- info: 'TranslationPropositions.P3_games_for_090' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms TranslationPropositions.P3_games_for_090

-- P4_Identification
/-- info: 'TranslationPropositions.P4_i_player_effect_cancels' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms TranslationPropositions.P4_i_player_effect_cancels

/-- info: 'TranslationPropositions.P4_ii_ker_dim_eq_card_components' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms TranslationPropositions.P4_ii_ker_dim_eq_card_components

/-- info: 'TranslationPropositions.P4_ii_rank_add_components' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms TranslationPropositions.P4_ii_rank_add_components

/-- info: 'TranslationPropositions.P4_ii_ker_iff_const_on_components' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms TranslationPropositions.P4_ii_ker_iff_const_on_components

/-- info: 'TranslationPropositions.P4_ii_connected_iff_ker_const' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms TranslationPropositions.P4_ii_connected_iff_ker_const

-- P5_WeightedMean
/-- info: 'TranslationPropositions.P5_weighted_gap_eq_cov_div_mean' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms TranslationPropositions.P5_weighted_gap_eq_cov_div_mean

/-- info: 'TranslationPropositions.P5_sign' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms TranslationPropositions.P5_sign
