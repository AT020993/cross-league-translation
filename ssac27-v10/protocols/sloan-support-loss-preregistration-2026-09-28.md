# Sloan support loss: registered random-restriction diagnostic

Accepted under Amir's 28 September request to implement the paper review's
recommendations. Commit and push this document before writing the generator or
computing the experiment. All historical outcomes and the observed A-to-B support
loss are already known. This is exploratory mechanism diagnosis, not confirmation.
The September 20 numerical record, September 12 operating lock and September 26
opportunity forecasts remain immutable.

## Specification

| Field | Declaration |
| --- | --- |
| Unit | A restricted factor-pair sample and its complete 674-player-season forecast target |
| Population | Frozen corrected pool A (4,074 pairs), verified full-season subset B (1,537 pairs), original historical regression cohort and 674 evaluation keys |
| Estimator | Two fixed random-restriction controls, 200 repetitions each; inherited factor, pooling, lag and chronological regression procedures; source-offset and cell-slope families at penalties 1, 10, 100, with and without translation |
| Null | The observed verification-related change may be consistent with ordinary loss of estimation support; no randomized verification effect or equivalence hypothesis is identified |
| Filter | Unchanged original eligibility and exact original target and regression-training keys; no outcome-based sampling, new threshold or penalty selection |
| Key | Pair: player_name + season; forecast: player_name + season_dest; matching strata use factor season, source league and destination competition |
| Uncertainty | Monte Carlo variation over restrictions, conditional on observed inputs, inherited estimator and bootstrap seed; quantile ranges are not sampling confidence intervals or p-values |
| Threats | Outcome exposure, nonrandom verification, changed cell mix, finite Monte Carlo precision, dependence within players/clubs, rank/support loss, moving training masks, future leakage and incomplete artifacts |
| Decision | Explain how much of the observed loss is also seen under declared random restrictions, while retaining unexplained composition and measurement differences |

## Inputs and chronology

Use the retained v9 model-inputs and full-refits verified against the committed
v9 diagnostic and v10 summary. Require B to be an exact row-preserving subset of
A with unchanged rates and exposures, and the two historical cohorts to agree.
Verify the old code hashes and all relevant input/output manifests. Copy inputs
to a retained run archive, verify them before and after copying, and read only
that snapshot. Record exact source, protocol, code and runtime hashes.

Reproduce A and B reference factors, historical translated features, forecasts
and training keys before interpreting any new restriction. Use the original
2,000 factor-bootstrap draws and factor seed 0. Keep original row ordering for
factor fitting and chronological cutoff semantics. Historical regression rows
retain their own cutoff-specific translated feature. Only strictly earlier
factor seasons and destination outcomes may enter each fit.

## Fixed controls

For repetitions 0 through 199, sample without replacement from A:

1. **Season-count control:** within each factor season select exactly the number
   of B pairs in that season. This preserves the verified pool's temporal sample
   size while allowing its league-cell composition to vary.
2. **Cell-and-season-count control:** within each source league, destination
   competition and factor season select exactly B's count, including zero-count
   strata. This additionally preserves the observed competition-cell mix.

Use deterministic seeds derived by the existing stable_seed helper from base
28092026, control name and repetition. Sort groups and candidate pair keys before
sampling; restore A's original row order before fitting. Selection reads keys
and strata only, never rates, minutes, outcomes or verification status beyond
B's prescribed stratum counts. Include verified rows in the eligible sampling
pool; excluding them would introduce another intervention.

The controls target A-to-B, where most support loss occurs. Existing B-to-C and
C-to-D comparisons remain unchanged. Do not label the new diagnostic a repeat
of the older scheduled-versus-transfer matched-count study.

## Fitting and scoring

Refit the inherited translation procedure on each restricted pair set, including
pooling and each historical lag correction. Retain the original cohort, measured
history, outcome values and exact A-reference training keys at each forecast
cutoff. No required training or target row may disappear because a restricted
pool has less support. If a required feature is unavailable or a fit refuses,
record that failure; do not silently substitute a newly eligible training set.

Score all source-offset and cell-slope arms at each fixed penalty. For each arm,
require all 674 target forecasts for complete-target MAE. Preserve keyed forecasts,
coefficients, factor/lag support, training keys, sampled pair keys and exclusions.
Use the existing source-offset fit and slope fit helpers; do not alter their
penalty, scaling or feature conventions. Compare reference predictions at 1e-9
absolute tolerance. Primary reporting is source-offset penalty 10, matching the
previous support-policy primary; all other fixed arms remain visible.

Report counts of nonfallback, fallback and unavailable factors on the entire
674-row target, by destination and season as well as pooled. Report complete-target
MAE, its change relative to A, and the paired with/without-translation increment.
The B result is displayed beside each control distribution. Report completion
counts and every failed repetition. A failed repetition's complete-target loss
is unavailable, never zero. Conditional summaries of successful repetitions must
be explicitly labeled and cannot stand in for the full planned experiment.

## Interpretation and falsification

Report median, 2.5th/97.5th empirical quantiles and full range across the 200
restrictions, separately for each control. These describe artificial restrictions,
not independent basketball cohorts. Do not turn B's rank among them into a
randomization p-value: verification was not randomly assigned. If B lies within
a control range, say its result is also attainable under that declared restriction;
do not claim that sample loss explains it causally. A value outside a range does
not establish a verification effect either. No retrospective power or equivalence
margin will be invented.

The implementation must reject changed inputs, duplicate or missing keys,
non-nested B, altered B measurements, infeasible stratum counts, changed training
keys, future observations, incomplete repetition inventories and corrupt caches.
Negative controls use small synthetic inputs only. A full-pool identity control
must recover the reference; outcome changes cannot alter selected pair keys.
A second isolated execution from the retained inputs must reproduce numerical
outputs. Save incomplete and failed states explicitly. Do not reduce repetitions
or bootstrap depth because of observed results; a resource limit is an incomplete
experiment, not permission to change its scientific settings.

## Paper and release boundaries

Render the new diagnostic separately from the frozen v10 numerical tables. Add
its interpretation to the manuscript and supplement only after complete readback.
Keep the abstract's existing comparison population and adverse findings. Update
the two figures to show both recorded dependence specifications and forecast
support fractions; promote an existing outcome-blind example into the main text.

The current opportunity study evaluates minutes/appearance. It cannot validate
EFF/36 translation. Document a future confirmation contract requiring the exact
translation procedure, comparator, dated population, cutoff and unexposed outcomes;
no future forecast or result is created by this diagnostic. Do not silently
reinterpret the already locked operating forecasts as that confirmation.

Prepare a reviewed local reproduction/release inventory with explicit source
permissions and exclusions. Author authorization cannot substitute for third-party
redistribution rights. Do not publish unresolved source-derived data or claim a
code-only package satisfies Sloan's data requirement. Preserve the recorded
Proballers grant and identify the exact remaining scope questions.
