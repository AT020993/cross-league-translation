# Machine-checked propositions for the cross-league translation model

A small Lean 4 + Mathlib package that checks the five propositions of the research
note *Five propositions behind the cross-league translation model*
(`translation-propositions-2026-09-04.md`, shipped in the companion PR under `docs/research/`): the league-information
bound (law of total variance), the reliability ceiling (Cauchy–Schwarz), Spearman–Brown
and its inverse, identification of league effects up to a constant via connectivity of
the league graph (Laplacian kernel), and the weighted-mean gap identity.

`PROOF-PATH.md` maps every proposition to its theorem and records each deviation between
the Lean statement and the note's prose. Read it first.

## Layout

```
lean-toolchain                  leanprover/lean4:v4.33.1
lakefile.toml                   depends on Mathlib tag v4.33.1 (pinned in lake-manifest.json)
TranslationPropositions.lean    root module
TranslationPropositions/
  Moments.lean                  population mean / cov / var over a Finset, shared lemmas
  P1_TotalVariance.lean         Proposition 1
  P2_Reliability.lean           Proposition 2
  P3_SpearmanBrown.lean         Proposition 3
  P4_Identification.lean        Proposition 4 (i) and (ii)
  P5_WeightedMean.lean          Proposition 5
  FinalCheck.lean               #guard_msgs in #print axioms for all 22 theorems
```

## Checking it

Requires [elan](https://github.com/leanprover/elan) (installs the pinned Lean automatically)
and about 5 GB of disk for the Mathlib build cache.

```sh
cd formal/translation-propositions
lake exe cache get      # downloads prebuilt Mathlib .olean files (~2-3 min)
lake build              # ~30 s for this package once the cache is in place
```

`lake build` succeeding **is** the check: `FinalCheck.lean` contains, for every theorem,

```lean
/-- info: 'TranslationPropositions.P1_gain_le_between' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms TranslationPropositions.P1_gain_le_between
```

so the build fails if any theorem acquires `sorryAx`, a custom axiom, or `Lean.ofReduceBool`
(the `native_decide` axiom). To see the axiom report directly:

```sh
lake env lean TranslationPropositions/FinalCheck.lean   # silent when every guard passes
```

Without the cache, `lake build` compiles Mathlib from source (hours). The `.lake/` directory
holds build outputs and dependency checkouts and is git-ignored.
