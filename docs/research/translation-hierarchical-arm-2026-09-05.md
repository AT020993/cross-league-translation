# Proposition 4's model fitted as ONE model: the hierarchical arm, scored walk-forward

**Date:** 2026-09-05 · **Status:** exploratory comparator, **not pre-registered**, no bar moved, the
lock untouched · **Generator:** `scripts/validate_translation_hierarchical.py` (default arguments;
`--continental-source api`) · **Tests:** `tests/test_scripts/test_validate_translation_hierarchical.py`
· **Machine-readable values:** `docs/research/artifacts/hierarchical-arm-2026-09-05/hierarchical_summary.json` (committed 2026-09-06; regenerated from the same script — the 2026-09-05 copy lived only in a gitignored directory) and
`hierarchical_rows.parquet` (regenerated, not committed — same rule as the rest of that directory).

**Answer.** No. The joint model — player random effect plus league fixed effect, the model
Proposition 4 writes down, fitted once instead of in two disconnected stages — is a cleaner
derivation and a worse predictor. On the same 674 walk-forward transfers the declared primary
scores **MAE 3.110** against the shipped two-stage combined arm's **2.942** (Δ = −0.168, 95% CI
[−0.278, −0.065], cluster bootstrap). It ties the per-league table (3.087) and the league-free
regression-to-the-mean (RTM) arm (3.116), and beats one global scalar (3.291). Two things it
teaches: **the per-league mapping is inert inside a random-intercept model** (shuffling the domestic
league effects does exactly as well, 55 of 200 permutations at or above the observed +0.014), and
**equal weight on a player's past seasons is the wrong prior** — the recency-weighted alternative is
the best arm in the study (2.851) and beats the shipped combined arm on the same bootstrap
(Δ = +0.091, CI [+0.024, +0.159]). That arm was chosen after the primary lost, with a half-life
nobody searched over, so it is a pre-registration candidate and not a claim; what it points at is a
dynamic (random-walk) ability model for the 2027 refit, not a better multiplier. The two-stage
pipeline stays.

## Specification

| Choice | This analysis | Alternatives printed |
|---|---|---|
| **Unit** | one (player, destination season) transfer scored by the walk-forward, n = 674 — exactly `scripts/validate_translation_walkforward.py`'s rows; the five shipped arm MAEs must reproduce `walkforward_summary.json` to 1e-6 or the script stops | — |
| **Model** | `log rate_{p,L,t} = α_p + β_L + ε`, `α_p ~ N(μ, τ²)`, `ε ~ N(0, σ²/games)` (P4 + P3) | additive scale (`hier_additive`) |
| **League effects β** | two-way fixed effects on the same-season dual-tier pairs with season < S, weights `min(minutes)`, EuroLeague pinned at 0 — the paper's identification | within-player demeaned WLS on every stint (`hier_joint_beta`, the confounded route) · β ≡ 0 (`hier_no_league`) · domestic β collapsed to their pair-weighted mean (`hier_tier_beta`) |
| **Player effect α_p** | posterior mean from every stint of p with season < S and ≥ 36 minutes: `μ + κ_p (r̄_p − μ)`, `κ_p = τ²/(τ² + σ²/W_p)`, `W_p` = Σ games; no history → the source stint alone | half-life one season on the weights (`hier_recency1`) |
| **Variance components** | σ² from within-player weighted spread; **τ² by DerSimonian–Laird** with precision `W_p/σ²`; μ precision-weighted | the naive form `Var_p(r̄_p) − mean_p(σ²/W_p)` (`--tau2-estimator naive`, the run-2 record — see *Standing*) |
| **Prediction** | `exp(E[α_p] + β_D)` — the lognormal median, the MAE-optimal point | `hier_plus_rtm`: the hierarchical prediction as one more column of the shipped RTM OLS |
| **Uncertainty** | paired cluster bootstrap on destination club-season, 4,000 draws, seed 0 (the validator's) | — |
| **Falsifier** | permute the domestic β within each fold, refit nothing else, re-score against `hier_tier_beta` (same level, no mapping), 200 reps | — |

**Reproducibility.** `python scripts/validate_translation_hierarchical.py` from repo defaults prints
every figure below and writes the two artifacts. It needs
`data/processed/translation/walkforward_summary.json` from a prior walk-forward run, because the
first thing it does is prove it is standing on the same rows. Repository state: branch off `main`
at 6ac8a7eaa.

## Standing — what was declared before the run, and the one thing changed after it

The primary arm (`hier`: pairs-β, equal season weights, log scale) was declared in the script's
`PRIMARY` constant before the first corpus run; everything else is a printed alternative. **One
estimator changed after run 2.** Run 1 crashed on an early cohort with no prior pairs (fixed:
cohorts with fewer than 100 prior pairs drop out of the `hier_plus_rtm` fit only). Run 2 completed
and the recency alternative returned MAE 4.15 with seasons at 5.0–6.0: its τ² had floored to 1e-6,
so every player was predicted at the grand mean. Cause: the naive moment estimator subtracts
`mean_p(σ²/W_p)`, and recency weights leave a few players with `W_p` near zero, so that mean
explodes. It was replaced by the DerSimonian–Laird form, which precision-weights the players, and a
printed `tau2_floored` flag was added so a collapse is never silent again (the T9 lesson). The
primary never floored under either form, **but its number moved**: the naive τ² was 0.31–0.33
(κ at the scored rows' mean exposure 0.82–0.86), the DL τ² is 0.110–0.120 (κ 0.63–0.69), and the
primary's MAE went from **3.012** (run 2, CI against the combined arm spanning zero) to **3.110**
(run 3, CI excluding zero). Both are from committed code (`--tau2-estimator naive|dl`); the
headline is the DL run because it is the standard estimator and the one that gives the recency arm
a fair reading, and the run-2 figure is stated here so nobody has to trust that choice. Under the
naive τ² the model shrank less than P3's reliability warrants (κ 0.85 against a destination-season
reliability of about 0.70 at 18 games); under DL it shrinks a little more than that (κ 0.65).

## Result — pooled over six walk-forward seasons, n = 674

| arm | MAE | R² | what it is |
|---|---|---|---|
| untranslated (B0) | 3.887 | −0.037 | shipped |
| one global scalar | 3.291 | +0.263 | shipped |
| per-league factors | 3.087 | +0.349 | shipped |
| RTM, no league | 3.116 | +0.341 | shipped |
| **RTM + per-league (combined)** | **2.942** | **+0.404** | shipped basis |
| **`hier` (primary)** | **3.110** | **+0.346** | this note |
| `hier_no_league` | 3.114 | +0.345 | decomposition: β ≡ 0 |
| `hier_tier_beta` | 3.124 | +0.345 | decomposition: level only |
| `hier_joint_beta` | 3.138 | +0.339 | alternative: β from all stints |
| `hier_additive` | 2.942 | +0.404 | alternative: additive scale |
| `hier_plus_rtm` | 2.961 | +0.400 | alternative: as an OLS column |
| `hier_recency1` | 2.851 | +0.436 | alternative: half-life one season |

Paired cluster-bootstrap contrasts (positive favours the first arm):

| contrast | Δ MAE | 95% CI | reads |
|---|---|---|---|
| `hier` vs combined | −0.168 | [−0.278, −0.065] | **the primary loses** |
| `hier` vs per-league | −0.024 | [−0.188, +0.139] | tie |
| `hier` vs RTM | +0.006 | [−0.122, +0.123] | tie |
| `hier` vs one global | +0.181 | [+0.014, +0.349] | wins |
| `hier` vs B0 | +0.776 | [+0.487, +1.089] | wins |
| `hier` vs `hier_no_league` | +0.004 | [−0.142, +0.150] | league identity adds nothing here |
| `hier` vs `hier_tier_beta` | +0.014 | [−0.025, +0.054] | the mapping adds nothing here |
| `hier_plus_rtm` vs combined | −0.020 | [−0.081, +0.043] | tie (fitted on fewer train rows: 385–932 per fold, `hier_plus_rtm_n_train`) |
| `hier_joint_beta` vs `hier` | −0.028 | [−0.063, +0.008] | the confounded β route is no better |
| `hier_additive` vs `hier` | +0.168 | [+0.102, +0.237] | additive scale beats log |
| `hier_recency1` vs `hier` | +0.260 | [+0.163, +0.354] | recency beats equal weights |
| `hier_recency1` vs combined | +0.091 | [+0.024, +0.159] | the post-hoc alternative beats the shipped basis |
| `hier_additive` vs combined | −0.000 | [−0.099, +0.096] | tie |

Per season (MAE; `n` and the `hier_plus_rtm` training rows beside it):

| season | n | combined | `hier` | `hier_recency1` | `hier_additive` | `hier_plus_rtm` (n train) |
|---|---|---|---|---|---|---|
| 2020 | 134 | 3.106 | 3.120 | 2.928 | 3.024 | 3.099 (385) |
| 2021 | 101 | 2.791 | 2.943 | 2.757 | 2.924 | 2.853 (519) |
| 2022 | 106 | 2.799 | 3.005 | 2.731 | 2.831 | 2.925 (620) |
| 2023 | 102 | 3.046 | 3.057 | 2.935 | 2.878 | 2.953 (726) |
| 2024 | 104 | 2.427 | 2.684 | 2.346 | 2.405 | 2.387 (828) |
| 2025 | 127 | 3.346 | 3.713 | 3.289 | 3.455 | 3.410 (932) |

Fitted components per fold (`fits`): μ 2.29–2.31 (log EFF/36 at the EuroLeague level, i.e. about
10.0), τ² 0.110–0.120, σ² per game 1.32–1.52, 4,040–6,197 players with history, no arm floored in
any fold. The pairs-β multipliers to EuroLeague in the 2025 fold run Spain 0.906 … ABA 0.761, the
P4 table.

## The two controls

**1. Is the per-league mapping doing anything inside this arm?** No. `hier` beats `hier_tier_beta`
(same domestic→continental level, every domestic β replaced by their pair-weighted mean) by
+0.014, and permuting the domestic β across leagues reaches that in **55 of 200** draws with a
shuffle mean of +0.0135 — the observed gain *is* the shuffle mean. The walk-forward's per-league
gain (+0.204 over one global, 0/200 shuffles) is real and is applied at full strength there, as a
multiplier on the source rate. Here the source league's β enters the player's history only through
`r̄_p − β_src`, is attenuated by κ ≈ 0.65 on the way to the prediction, and is partly absorbed by
μ. A random-intercept model uses league identity less than the two-stage pipeline does, and on
these transfers that costs it.

**2. Does the confounded β route help?** No: `hier_joint_beta` (β from every stint, so also from
consecutive-season moves) is −0.028 against the pairs route, CI spanning zero. The paper's
identification is not what the model is paying for.

## What this licenses

* **Supported:** the two-stage pipeline (per-league table, then RTM OLS on top) is not an
  approximation to a better joint model waiting to be fitted; the joint model as written loses to
  it out of sample, with the interval excluding zero. The paper can say the pipeline was tested
  against its own generative form and kept.
* **Supported, as a diagnostic, not a claim:** a career-constant player ability is the wrong prior.
  Down-weighting older seasons (half-life one) moves the arm from worst to best (+0.260, CI
  excluding zero), and the shipped RTM OLS — which sees the current season and the prior mean as
  separate columns — learns the same thing with two coefficients. The principled version is a
  **dynamic hierarchical model**, `α_{p,t} = α_{p,t−1} + η_t` (a random walk on ability, estimated
  by a Kalman smoother), which makes the recency weights a fitted innovation variance instead of a
  half-life someone picked. That is the named candidate for the 2027 refit (alongside the τ²
  pooler already deferred there, ATI-2960) and it is **not pre-registered by this note**.
* **Not licensed:** any change to the lock, the pre-registered gates, or the abstract. Nothing here
  re-scores `translation-holdout-validation-2026-08-17.md` or
  `translation-walkforward-per-league-2026-08-21.md`. `hier_recency1` beats the combined arm
  (+0.091, CI [+0.024, +0.159]) **and still licenses nothing**: it is one of four alternatives read
  after the primary lost, its half-life was fixed without a search, and a garden of four forking
  paths at n = 674 is exactly what a pre-registration exists to close. If it is to be a claim, it is
  declared first and scored on the 2026-27 set or the 2027 refit — the same route the RTM arm took
  (Amendment 2).

## Followed up the same day

The dynamic model this note names as the candidate was pre-registered
(`translation-dynamic-ability-preregistration-2026-09-05.md`, a62be01e) and measured
(`translation-dynamic-ability-result-2026-09-05.md`): PARTIAL — ahead of the combined arm by +0.081
on the selection folds with the CI spanning zero, and it reproduces `hier_recency1`'s gain with a
fitted innovation variance instead of a chosen half-life.

## Limitations, stated as limitations

* The recency half-life (one season) and the stint floor (36 minutes) were fixed before the run
  but not tuned; a different half-life would give a different number and no such search was made.
* The log scale needs a floor for scoreless stints (0.1 EFF/36); the additive alternative avoids it
  and beats the log primary by +0.168. Scale is a real choice and the additive form is the one to
  pre-register if this line is pursued.
* `hier_plus_rtm` is fitted on fewer training rows than the shipped combined arm (early cohorts
  have no prior pairs), so its tie is not like-for-like; `hier_plus_rtm_n_train` is printed per
  fold for that reason.
* `Var(ε) = σ²/games` treats every game as equally informative; minutes per game vary, and the
  per-game σ² of 1.3–1.5 on the log scale is inflated by low-minute games.
* The τ² estimator changed after run 2 (above). The reader who prefers the pre-change figure has it:
  3.012, and the flag that reproduces it.

## What this changes in the paper, and what it does not

Nothing in the abstract. In the manuscript, one sentence: the two-stage estimator was tested
against its own generative form fitted jointly and kept, because the joint form under-uses league
identity and over-trusts a player's distant past. The dynamic model is a stated direction, not a
result.

## Scripts

* `scripts/validate_translation_hierarchical.py` — rebuilds the six walk-forward folds through
  `validate_translation_walkforward.one_season` / `_fit_rtm_arms` / `fold_rows`, asserts the five
  arm MAEs against `walkforward_summary.json` (`itp.assert_reproduces_walkforward`), fits every
  arm on rows strictly before each scored season, writes `hierarchical_summary.json` and
  `hierarchical_rows.parquet`. `--tau2-estimator naive` reproduces run 2; `--skip-shuffle` omits
  the 200-rep control.
* `tests/test_scripts/test_validate_translation_hierarchical.py` — eleven synthetic-data tests,
  each mutation-verified: the variance components are recovered; DerSimonian–Laird survives players
  with near-zero weight where the naive form floors, and a flat population floors with the flag
  raised; β from pairs cancels player ability under selection; the joint β route agrees; shrinkage
  is regression to the mean at both extremes; the prediction is the lognormal median with the
  source-stint fallback; a stint in the scored season does not enter its own fit; the stint floor
  applies; `hier_tier_beta` keeps the level and removes the mapping; the naive estimator stays
  runnable; the primary is declared and disjoint from the alternatives.
