# Sloan v10: competition-slope comparison and candidate revision

Accepted under Amir's 20 September 2026 request to improve v9 for this Sloan cycle.
Commit and push this specification before implementing or running the comparison.
V9 and the September 12 operating forecast lock remain immutable. This amendment
reopens one comparator gap identified by reading the model equation and code; it
does not authorize an open-ended model search. All historical outcomes and v9
results are already exposed. This is exploratory research, not fresh confirmation.

## Specification

| Field | Declaration |
| --- | --- |
| Unit | Player/destination-season forecast |
| Population | V9's corrected newcomer cohort, six destination seasons 2020–2025, all four factor pools and all 56 saved scenarios |
| Estimator | Existing chronological history/destination model and source offsets, extended by penalized source-by-destination deviations in source-rate slope; with and without the saved translated feature |
| Null | Additional forecast benefit from translation remains undetermined after directly estimating competition-specific rate slopes |
| Filter | Exact saved chronological training keys, feature eligibility and reference forecast keys; no new outcome filter, subgroup selection or threshold tuning |
| Key | Existing unique player_name + season_dest; categories are source league and destination competition, not player identity |
| Uncertainty | Existing paired player/club-season and player/season conditional intervals; all saved omission and seed scenarios separately; no calibrated future interval or equivalence claim |
| Threats | Reused outcomes, changed support, sparse cells, scale-dependent penalties, altered historical features, future leakage, correlated contrasts and overinterpreting a design-span argument |
| Decision | Strengthen the comparative candidate with a mechanism-matched simple benchmark and clearer exposition, regardless of the direction of results |

## Why this comparison

The saved translated feature is z = x * m(source,destination,cutoff) * k(cutoff).
V9's simple source-aware competitor adds league offsets but not source-specific
rate slopes. It therefore does not directly challenge the multiplicative form of
translation. A source-by-destination slope benchmark addresses that concrete
limitation. It is not proposed because a new predictor is expected to win.

At one fixed cutoff, z belongs to the linear span of source-by-destination
indicators multiplied by x, if all required categories are represented. This is
an algebraic observation about a fixed feature map, not an empirical result or a
novel theorem. Historical training rows retain different cutoff-specific m and k.
Furthermore ridge penalties and the unpenalized z direction differ. Consequently
the observation proves neither redundancy over the training data nor equality of
forecasts. The comparison tests forecast value, not a causal information mechanism.

## Fixed model family

Keep unpenalized H=(1,x,prior-rate-with-source-fallback,above-prior flag), D and
D*x, where D identifies EuroLeague rather than EuroCup. Retain all source-league
indicator offsets of the v9 parent. Add one slope deviation for every observed
training source-by-destination cell: indicator(cell) * x/s_x, with s_x the
population standard deviation (ddof=0) of x over that training fold.

Scaling uses training rows only. Do not center x: these are pure rate slopes,
without implicitly adding cell-specific intercepts. All source offsets and cell
slopes receive the same ridge penalty lambda, separately fixed at 1, 10 and 100.
H, D, D*x and (in the augmented arm) z remain unpenalized. Fit using least-squares
identity augmentation, preserving the existing convention sum(squared residuals)
+ lambda * sum(squared penalized coefficients). The new slopes are scaled; their
penalty is not numerically interchangeable with an unscaled slope penalty.

Fit the six arms (three penalties, each with/without z). Report all, select none
using evaluation outcomes. Unseen source/cell contributions are zero and counted.
A nonpositive/nonfinite s_x or deficient unpenalized design refuses explicitly.
No new feature, penalty, training window, source pool, outcome filter or smoothing
choice may be added after observing these results without another pushed amendment.

## Frozen inputs and reproduction gate

Use the preserved v9 model-inputs and full-refits directories (or an exact verified
copy), bound to the committed v9 diagnostic artifact and its recorded refit-summary
hash. Verify the complete saved refit inventory and all four input variants.
Recover all historical translated features from the frozen cohort and saved
cutoff cells and lag constants. Do not estimate new factors or change the
2,000-draw upstream runs.

For every saved scenario, verify the exact training keys after the recorded
season omission, historical feature support, outcomes and original arm forecasts
to absolute tolerance 1e-9 before interpreting the new fits. Earlier training
features keep their own historical cutoff. Store all recovered feature tables,
training keys, coefficients, scale, categories, refusals and keyed forecasts.
Save code/protocol/input/output hashes and read back output before reporting.

Primary reporting uses the original 674 v9 common keys. Also report native support
and the intersection over every new arm and all 56 scenarios, with exclusions.
If original target rows become unscorable, label target comparison inconclusive;
do not silently replace the target by a favorable subset.

## Reporting and falsification

The main contrast at each fixed penalty and factor pool is MAE(slope benchmark)
minus MAE(slope benchmark + z); positive favors z. Retain all original v9 arms
and contrasts as historical context. Report MAE, RMSE, signed bias, median and
90th-percentile absolute error; conditional intervals; improved/worsened/tied
shares; every evaluation season and both destinations. Reference effects,
omission ranges and seed ranges are distinct quantities.

A claim of robust incremental superiority fails if a registered reference
contrast includes zero, any pool/penalty reference difference is nonpositive,
or the registered omission or seed sensitivities reverse its sign. Even favorable
results would remain conditional exploratory evidence, not independent
confirmation. Intervals across correlated arms are not simultaneous guarantees.
Do not select a favorable penalty, declare equivalence, invent a worthwhile
effect threshold, infer recruiting value or use null results to claim universal
uselessness. Source restrictions still mix composition and support.

Engineering negative controls must detect changed hashes, duplicate/missing
keys, altered saved forecasts, future-outcome leakage, training-scale/category
leakage, missing-versus-zero outcomes and omitted-year training re-entry.
Verify that the new family preserves the parent source-offset predictions when
slope terms are disabled, and that fixed-cutoff translation has the stated
design-span property without asserting fitted-prediction equivalence.

## Candidate, reproducibility and release

Create separate v10 abstract/manuscript/figures from generators; leave the v9
drafts, template, figures, artifacts and approval record unchanged. Reframe the
contribution around benchmark choice and factor support, accurately distinguish
prior translation work, show paired contrasts directly, and move operational
history to a supplement while retaining adverse findings and exposure history.
Do not present missing arrivals as zeros or silently combine the separate
appearance experiments with v9.

Provide a traceable claim table, a local reproduction command, a release-scope
inventory and a readable internal PDF. Verify links, numerical reconciliation,
word count, figures and rendered pages. Separate a reproducible local package
from a permission-cleared public repository. Existing permissions must be
preserved, with unresolved expanded-table/continental scope stated precisely.
No external reviewer is assumed; internal agent/code review is not external
human review. External messages, public release and submission need separate
authorization.
