# V10 amendment: does factor reliability justify using translation?

Dated 20 September 2026. Accepted for implementation under the user's instruction
to continue v10. Commit and push this protocol before implementation or calculation.
This is an exploratory amendment on already exposed outcomes, not independent
confirmation. Preserve v9, the original v10 run and the September 12 forecast lock.

## Specification

| Field | Declaration |
| --- | --- |
| Unit | Paired forecast loss for a frozen player/destination-season key |
| Population | All 674 original common keys, destination seasons 2020–2025, in all 56 saved scenarios across four factor pools |
| Estimator | Deterministic routing of existing predictions; no fitting, threshold search or model selection |
| Null | The existing reliability gate does not establish improvement over both always-parent and always-augmented forecasts on the complete target |
| Filter | Existing exposure-qualified target; finite predictions and a genuine Boolean gate required for every key; no outcome-dependent exclusions |
| Key | Frozen forecast key as defined in the saved scripts; protocol/input/code hashes |
| Uncertainty | Existing conditional player/club-season and player/season paired-loss intervals; separate omission and seed ranges |
| Threats | Reused outcomes, six seasons, sparse support, documentation selection, conditional inference, unresolved release scope |
| Decision | Test one inherited gate, retain failures; routing is not forecast abstention or recruitment utility |

## Motivation and exposure

The completed slope comparison reports all 12 reference translation increments
as negative. The separate appearance-study audit-budget direction missed its
primary gate. These adverse results are known before this amendment.

Consensus Deep search and SciSpace public paper/citation search supplied literature
leads, followed by primary-source checks. Yeh, Rice and Dubin (2022,
https://doi.org/10.1080/00031305.2021.1967781) already show why informed simple
basketball benchmarks can erase apparent superiority. Zaoui, Denis and Hebiri
(2020, https://proceedings.neurips.cc/paper/2020/hash/e8219d4c93f6c55c6b10fe6bfe997c6c-Abstract.html)
study regression with rejection; their squared-loss variance rule is not a
guarantee for our counts, MAE or fallback. This application claims no new method.

V9 already decomposes pool-to-pool losses by fallback transitions. This amendment
instead routes to the separately fitted parent when the cell is unreliable. The
existing augmented model already substitutes a tier-mean factor in those cases;
the proposed policy uses the parent prediction and still scores every row.

## Frozen inputs and policy

Use the existing sloan-v10-2026-09-20/run-01 under
<local path removed>
Its summary SHA-256 is
58f2cdc5a032415de2b2331e7aaa8e9975914903daac156970edfe37a28dc638.
Verify its complete manifest, summary/status, prediction inventory and recorded
code/protocol hashes. Bind new outputs to them; never overwrite that run.

For every pool, scenario and penalty in {1, 10, 100}, retain both parent families:
source_ridge_<penalty> and cell_slope_<penalty>. Augmented arms append
_scheduled. With the frozen Boolean g_i = scheduled_reliable_i, use

prediction_policy_i = g_i * augmented_i + (1-g_i) * parent_i.

Reliability requires more than 75 pairs: finite standard error, noncollapsed
pooling, a present cell and a finite factor also matter. Use the exact stored
gate and verify it against scheduled_fallback and the original historical
cutoff-cell lookup. Null is not false. Reject future or omitted support under
the original cutoff rules. No labels or current errors enter the gate. Historical corrections and verification
classifications are retrospective; season-lagged replay does not prove that
these corrected measurements were actually available at the historical date.

No alternative threshold or learned gate is permitted. The primary display is
pool A, penalty 10 (the middle of the original fixed grid), for both families.
All pools and penalties remain visible. This choice follows exposure to the
original global results and is not independent of that development history.

## Reporting and falsification

Positive contrasts favor the policy:

1. MAE(always parent) minus MAE(policy).
2. MAE(always augmented) minus MAE(policy).
3. For slope policies, MAE(always source-offset parent at the same penalty)
   minus MAE(slope policy), protecting against improving a weaker comparator.

Report MAE, RMSE, signed bias, median and 90th-percentile absolute errors;
counts routed to each arm; improved/worsened/tied shares for each named contrast; both dependence
intervals; every evaluation season/destination and saved scenario. Within
reliable/unreliable groups report augmented-versus-parent paired increments and
counts. Weighted contributions must reconcile to whole-cohort effects. These
groups are descriptive, not causal effects or a new best subgroup. Empty groups
and undefined intervals remain explicit/inconclusive.

Actionable improvement requires positive primary contrasts 1 and 2 for BOTH
families, with lower limits above zero under BOTH dependence specifications.
Calling the slope policy a better forecaster additionally requires contrast 3
to pass the same criterion. Lower absolute error on a selected subset is not
evidence for this claim. A zero-spanning interval is undetermined, not equivalence.

A stronger robustness claim additionally fails if either destination reverses
the relevant primary contrast, any leave-one-evaluation-season-out paired mean
is nonpositive, or a recorded estimation-omission/seed scenario reverses its
sign or equals zero. Include contrast 3 in robustness only for a slope-superiority
claim. Evaluation-season deletion removes loss rows; report it separately from
upstream refits. Cross-pool generality requires positive reference contrasts in
B, C and D too. These demanding descriptive gates are not simultaneous inference;
correlated comparisons are not independent replications.

On failure, report: **the existing reliability gate is not demonstrated to select
useful incremental translation on this target**. Retain the failed policy and
all cells. Do not tune a replacement in this task. Favorable results remain
exploratory and cannot change the operating forecast lock.

## Checks and delivery

Require exact 674-key agreement in every scenario, no duplicate/missing keys,
unchanged outcomes, finite predictions, genuine Boolean gates and original
support agreement. Reject altered hashes and future/omitted support. Synthetic
negative controls cover tampered hashes, null gates, wrong keys and leakage;
check all-true/all-false gates, row-order invariance and exact loss reconciliation.
Use existing uncertainty functions without replacing invalid intervals by zero.

Implement a separate generator scripts/sloan_v10_support_policy.py and focused
tests; commit implementation before the first real-data calculation. Save
protocol/input/code/output hashes, keyed routed forecasts, summary and generated
results in a new directory. Locally replay these outputs. Generate manuscript
changes through its template/renderer and link the new supplement. Unknown
appearances remain unknown; no new denominator is created. Internal agent checks
are not external statistical review. External messages, public release and
submission still require separate authorization.
