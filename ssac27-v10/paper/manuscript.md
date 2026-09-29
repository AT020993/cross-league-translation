# What Does League Translation Add? A Benchmark for European Basketball Forecasts

Manuscript accompanying the SSAC 2027 abstract (29 September 2026).
The September 20 comparison and policy amendment are preserved; the separately registered September 28 restriction diagnostic is exploratory.
Rates and forecast errors use EFF per 36 minutes unless stated otherwise.

## Abstract

Clubs building EuroLeague and EuroCup rosters must compare players from different domestic leagues. Translation factors from players' same-season domestic and continental rates are widely used, but beating a league-blind forecast means little if a competition-aware one does as well. We ask what one translation recipe adds to competition-aware forecasts, and how stricter identity verification changes factor support. Proballers domestic and EuroLeague API continental records define 674 forecasts of box-score efficiency per 36 minutes (EFF/36): 194 EuroLeague and 480 EuroCup player-seasons (2020–2025) with at least eight domestic games one season and eight continental games the next, excluding last season's continental regulars. Translation is added to four nested baselines: player history; plus destination intercept and slope; plus source-league offsets; plus source-by-destination (cell) slopes, the offset and cell-slope terms ridge-penalized at 1, 10 and 100. Factors come from the full pool and three identity-verified variants. Gain is the reduction in mean absolute error (MAE) from adding translation. Intervals (95%), clustered by player and club-season (alternatively, player and season), omit refitting uncertainty. Forecasts use only earlier seasons; all comparisons score the same 674. Outcomes were inspected earlier and verification reconstructed afterward, so comparisons are retrospective and exploratory. In the full pool, adding translation to player history lowers MAE from 3.096 to 2.935 EFF/36 (gain 0.161, a 5.2% reduction; interval 0.077 to 0.246). With the destination known, the gain is 0.049 (1.6%; interval −0.013 to 0.111). With source leagues modeled, full-pool gains span −0.007 to 0.014, every interval including zero (Figure 1). With verified factors, gains over history shrink to 0.044–0.083 and every competition-aware gain is negative (−0.012 to −0.005); 10 of 18 correlated source-aware player/club-season intervals exclude zero, but only 2 player/season intervals (six seasons) do. Verification cuts estimation pairs from 4,074 to 1,537 and forecasts with a supported league-pair factor (rather than a fallback) from 566 of 674 (84.0%) to 118 (17.5%; 113 with overlap trimming; Figure 2). Across random 1,537-pair subsets, registered after this loss was seen, median supported forecasts are 91 (season-matched) and 112 (also league-pair-matched, maximum 118): comparable support loss is attainable without verification; season-matched subsets lose more EuroLeague support. Translation's value depends on the comparator: with full-pool factors, a 5.2% error reduction against a league-blind forecast, an uncertain 1.6% against a destination-aware one, and none detectable against source-aware ones; with verified factors, competition-aware point estimates are small and negative. Clubs and analysts should test translation factors against forecasts that know both leagues, on the same players, and report fallback use. Findings cover one recipe, the EFF/36 outcome and an appearance-qualified, EuroCup-heavy population; they establish neither equivalence nor general harm. Recruitment benefit remains untested.

## 1. When is the extra translation step worth using?

A club comparing domestic players for a continental roster must account for the
competitions in which their statistics were produced. That need does not establish
that a particular translation system improves its forecasts. The useful question
is whether an additional source of cross-league evidence improves on a forecast
that already knows the player's history and the source and destination leagues.

On the same 674 eligible forecasts, adding the paired feature reduces mean absolute error (MAE) by 0.161 EFF/36 against player history alone, but by 0.049 after the baseline includes destination context (conditional 95% interval [-0.013, 0.111]). Source-aware comparisons provide no robust incremental-superiority result. Stricter verification also shifts many forecasts from cell-specific factors to destination-mean fallbacks. Forecast coverage and factor support tell different stories.

Consider Bonzie Colson, with a 21.538 EFF/36 source rate in Turkey and a EuroLeague forecast for stored destination season 2022. The supported factor 0.839 and lag correction 0.936 produce a translated feature of 16.910. History alone forecasts 18.095; adding translation gives 16.358. Once destination context and source offsets are included (penalty 10), the change is smaller: 16.766 to 16.602. The observed rate is 18.969. This existing case was selected by the median absolute change in the destination-aware prediction, without using its outcome. It illustrates the calculation, not average accuracy or a recruitment recommendation. Features use information from earlier seasons; their raw-source availability at the historical forecast date is not established. The supplement retains the selection rule and a fallback example.

This is a benchmark result with a practical use: it changes the evidence an
analyst should request before adopting an extra translation feature. The paper
contributes a reproducible European example of how an apparent gain changes with
the benchmark's information, and a separate audit of the support lost under
stricter factor verification. It does not introduce league translation or show
that simpler models always win.

Three tasks must remain distinct. Translating existing statistics asks what
production might have looked like in another environment. Forecasting asks what
will be observed subsequently, after changes in form, opportunity and context.
Recruitment requires an available candidate population, costs and a decision
objective. We study conditional future box-score rates among players who later
meet an appearance threshold. Our findings concern one exposure-weighted,
partially pooled, lag-corrected translation feature and the specified linear
forecast families, not every translation estimator or a causal league effect.

**Relation to prior work.** Lee and Page explicitly proposed simultaneous
domestic–continental and transfer observations as alternative evidence for
basketball correction factors [1]. Glazer compares same-season translation with
matched consecutive-season estimation of existing-statistic translations [2];
our simple transfer comparator is not a replication of that matched estimator.
Linked-player league adjustments and history-plus-translation forecasts also
appear in practitioner work [3,4]. International-player forecasting [14],
sparse longitudinal basketball histories [15], and separate playing-time and
rate forecasts [16] further establish that neither this problem nor its main
ingredients are new. Soccer work motivates persistence and information-matched
comparators [5,6], without providing validation of our basketball results.

The benchmark principle has precedent within basketball. Yeh, Rice and Dubin
found that ESPN's in-game forecasts improved on naive comparators without
demonstrating superiority over simple logistic models using score difference
and ESPN's pregame probability as the team-strength input [13]. Our contribution
applies that principle to paired cross-league information while holding forecast
targets fixed and making verification-related support changes visible. This
joint empirical comparison, rather than a new estimator, is the claim to assess.

## 2. The forecast population and its limits

The outcome is EFF per 36 minutes. EFF sums points, rebounds, assists, steals and
blocks, then subtracts missed field goals, missed free throws and turnovers.
Dividing by minutes and multiplying by 36 produces the rate. This measure differs
from official EuroLeague PIR and is neither possession-adjusted efficiency nor
salary value. Its units describe conditional box-score production; equal rate
errors need not have equal consequences for players receiving different minutes.

Domestic observations come from the existing Proballers corpus and continental
observations from the EuroLeague API. Factor-estimation pairs combine a player's
domestic and continental aggregates in one season. The historical join does not
require a shared club or overlapping appearance dates, and an aggregate can span
clubs. We therefore call these same-season pairs. Later restrictions verify
identity, club and overlapping appearances for selected factor pools; that
verification must not be attributed to the unrestricted historical pool.

The forecasting unit is a player-season with one retained continental destination,
EuroLeague or EuroCup. Eligibility requires a consecutive domestic source season, at
least eight games on both sides, positive minutes and EFF rates, and no qualifying
previous-season continental incumbency. Such a newcomer may have appeared in
continental competition earlier in his career and need not change clubs. The
primary comparison targets the 674 player-season forecasts shared by all specified comparisons for destination
seasons 2020–2025. Season labels retain the stored destination-season convention.
After the game and minute thresholds, the pipeline selects the largest-minutes
qualifying domestic source aggregate and continental destination aggregate per
player-season. It does not retain every possible player–competition pair.
Poland is excluded as a source under the historical protocol. The frozen
player-name/destination-season keys and original selections are retained;
the historical minutes sort has no explicit secondary tie rule.

The target contains 194 EuroLeague and 480 EuroCup forecasts. The pooled result consequently gives more weight to EuroCup; it is not a EuroLeague-only estimate.

This is an appearance-derived denominator, not a roster or signing census.
Records removed as Total, DNP or unparseable entries cannot establish outcomes
for players absent from usable appearances. Destination exposure requirements
exclude some unsuccessful arrivals relevant to recruitment. Zero-minute players
have no defined per-36 outcome, and missing records are never assigned a zero
rate. The earlier positive-destination-EFF sensitivity does not recover an
all-arrival population. Selective observation as athletes enter and leave
sport is an established problem in aging-curve research [19]; its modeled
imputation procedures do not supply our missing arrival frame. Exclusion flows, outcome-filter results and identity
adjudication are retained in the supplement.

## 3. The paired feature and historical information cutoffs

For a source–destination cell c, let x and y denote observed source and destination
rates, and let w be the smaller of the two minute totals. The raw factor is

`f_c = sum(w_i * y_i / x_i) / sum(w_i), with x_i > 0.`

It is an exposure-weighted mean of observed ratios among eligible players.
Denominator variation matters: a mean of individual ratios is a different
quantity from a ratio of aggregate means [7]. This factor does not automatically
identify a structural multiplier or an individual's counterfactual transfer
effect. Same-season observation does not hold role, health, opponents or minutes
constant.

The existing moment procedure partially pools cell estimates within destination.
A supported cell requires at least 75 pairs, a finite factor standard error
and no complete pooling collapse; lookup also requires a finite pooled factor.
Other cells use the destination-mean fallback, or refuse when it is unavailable.
The supplement specifies the moment equations and factor-bootstrap rules.
Pooling noisy sports observations has a long history [8]; its classical risk
guarantees do not transfer to this estimator or to mean absolute forecast error.
We assess the resulting forecasts, not a league-strength interpretation of the
factor itself.

For destination season s, factors and the median lag correction k use only
observations from seasons before s. The translated feature is `z = x * m * k`, where m is the
supported cell factor or its recorded fallback. Crucially, each earlier
regression-training row retains the translated feature constructed at that row's
own cutoff. Replacing it with a factor estimated using the test season's richer
history would change the information available during training.

Let h be 36 times total EFF divided by total minutes across all positive-minute
input competition aggregates strictly before the source season, with x as
fallback when history is missing. The history calculation does not reapply the
eight-game threshold. It therefore reflects previous competition mix as well as
player production. The above-history flag a is one when source
production exceeds available own history and zero otherwise. The common history
vector is `H = (1, x, h, a)`. Regression training uses earlier destination outcomes.
Each comparison preserves the saved chronological training keys, historical
features and forecast eligibility. Insufficient support or deficient required
design columns produce an explicit refusal rather than an unreported model
replacement.

Chronological construction excludes later-season observations within each fit.
Source corrections and verification classifications were reconstructed
retrospectively; their availability at each historical forecast date was not
verified. This replay therefore does not establish an as-operated historical
forecast. Chronology also does not erase prior inspection of these evaluation seasons. Earlier studies and v9
already exposed the outcomes; the new comparison is an explicitly exploratory
extension whose choices are fixed in the
registered specification.
Repeated model development on known outcomes remains a limitation [9].

## 4. Matching the benchmark to the feature's form

The original benchmark ladder adds destination competition to H, first as an
intercept D and then as an interaction `D*x`, where D identifies EuroLeague
rather than EuroCup. Source-aware arms also include penalized source-league
indicator offsets. Each relevant benchmark is evaluated with and without z.
These comparisons distinguish improvement over a league-blind history forecast
from improvement after simple competition context is already available.

An offset changes the prediction by the same amount at every source rate. A
translation factor instead scales that rate. Source offsets alone therefore do
not directly test whether a paired-data feature contributes more than an
ordinary source-specific slope. The extension retains the source-offset parent
and adds a slope deviation for each source–destination cell observed in the
training fold:

`q_c = indicator((source, destination) = c) * x / s_x,`

where `s_x` is the population standard deviation of source rate in that training
fold, using `ddof=0`. The rate is scaled but not centered. Centering would
implicitly add cell-specific intercept components, changing the intended pure
slope comparison. Test rows do not determine scales or categories. Unseen source
or cell contributions are zero and counted; a nonfinite or nonpositive training
scale refuses the fit.

The unpenalized terms are H, D and `D*x`, plus z in the augmented arm. Source
offsets and cell slopes share a ridge penalty lambda, separately fixed at 1, 10
and 100. The objective is the sum of squared training residuals plus lambda times
the sum of squared penalized coefficients, implemented by least-squares identity
augmentation. All six new arms are retained. No penalty is selected using the
evaluation outcomes, and its numerical value must be interpreted with the stated
scaling convention. Training minimizes squared error, whereas the primary
evaluation uses absolute error. This is a fixed modeling choice, not a claim
that the fitted coefficients minimize MAE; an MAE-targeted estimator would be
a separate comparison.

At a single cutoff, if all required categories are represented, multiplying x by
the cell-specific factor and lag correction yields a vector in the span of these
cell-slope features. This is an observation about the feature map, not a theorem
of predictive equivalence. Historical rows have different cutoff-specific
factors and lag corrections. The ridge penalties also differ from the
unpenalized z direction. The comparison consequently allows the paired feature
to supply useful temporal structure or regularization; it does not assume that
its information has been removed algebraically.

The regression slopes and paired feature also use different estimation evidence.
The former learn from the historical forecasting cohort, whereas the latter
draws on eligible same-season domestic–continental pairs. Matching functional
form does not equalize those auxiliary observations. The empirical question is
whether adding that historically updated feature improves forecasts beyond
directly estimated competition-specific scaling.

Shared and domain-specific feature components have a general precedent in
Daumé's domain adaptation method [17]. Our competition interactions apply that
familiar idea to the benchmark; they are not a new representation-learning
method or a claim that competitions share identical conditional outcomes.

## 5. Incremental accuracy on a fixed target

For each eligible forecast i, let d_i be absolute error without translation
minus absolute error with translation. The target is the arithmetic mean of d_i
over the frozen target rows: positive means lower error with translation.
Each player-season receives equal weight, regardless of minutes, club or salary;
seasons with more eligible rows contribute more. This is a conditional forecast
accuracy estimand, not total production or the value of a signing.

The historical comparisons establish the reference benchmark ladder. Absolute
MAEs are shown beside increments so that a feature cannot look useful merely
because its parent is poor:

| Baseline receiving translation | MAE without | MAE with | MAE improvement | Conditional 95% interval |
| --- | --- | --- | --- | --- |
| History only | 3.096 | 2.935 | 0.161 | [0.077, 0.246] |
| History + destination intercept and slope | 2.989 | 2.940 | 0.049 | [-0.013, 0.111] |
| + Source offsets; penalty 1 | 2.928 | 2.932 | -0.004 | [-0.026, 0.018] |
| + Source offsets; penalty 10 | 2.924 | 2.926 | -0.002 | [-0.028, 0.024] |
| + Source offsets; penalty 100 | 2.942 | 2.929 | 0.014 | [-0.030, 0.058] |

These are paired with/without-translation comparisons within each baseline, not differences between unrelated best-performing models. All three penalties are retained. The destination-slope comparison has MAE 2.989 without and 2.940 with translation. Its player-by-season sensitivity interval is [-0.020, 0.118]; only six season clusters are available. Here and below, improvements are computed from unrounded MAEs and can differ by 0.001 from the difference of the displayed MAEs.

The extension evaluates the incremental feature within each fixed slope model:

| Factor pool | Penalty | MAE without z | MAE with z | Improvement | Conditional 95% interval |
| --- | --- | --- | --- | --- | --- |
| A. Full corrected pool | 1 | 3.017 | 3.024 | -0.007 | [-0.033, 0.019] |
| A. Full corrected pool | 10 | 2.993 | 2.998 | -0.005 | [-0.029, 0.019] |
| A. Full corrected pool | 100 | 2.957 | 2.958 | -0.001 | [-0.029, 0.027] |
| B. Verified; full-season rates | 1 | 3.017 | 3.029 | -0.012 | [-0.024, -0.001] |
| B. Verified; full-season rates | 10 | 2.993 | 3.003 | -0.010 | [-0.020, 0.000] |
| B. Verified; full-season rates | 100 | 2.957 | 2.965 | -0.008 | [-0.015, -0.001] |
| C. Overlap keys; full-season rates | 1 | 3.017 | 3.029 | -0.012 | [-0.023, -0.001] |
| C. Overlap keys; full-season rates | 10 | 2.993 | 3.003 | -0.010 | [-0.019, 0.000] |
| C. Overlap keys; full-season rates | 100 | 2.957 | 2.965 | -0.007 | [-0.014, -0.001] |
| D. Overlap-window rates | 1 | 3.017 | 3.026 | -0.009 | [-0.022, 0.004] |
| D. Overlap-window rates | 10 | 2.993 | 3.001 | -0.008 | [-0.020, 0.005] |
| D. Overlap-window rates | 100 | 2.957 | 2.963 | -0.006 | [-0.018, 0.006] |

Robust incremental superiority is not established across the registered comparisons. Penalty values index sensitivity comparisons; none is selected as the winner. These correlated conditional intervals are not simultaneous guarantees. B at penalty 10 has upper bound +0.00001, displayed as 0.000, so that interval includes zero. C at penalty 10 has upper bound +0.00004, displayed as 0.000, so that interval includes zero.

| Penalty | Source offsets only: MAE | Offsets + cell slopes, no z: MAE |
| --- | --- | --- |
| 1 | 2.928 | 3.017 |
| 10 | 2.924 | 2.993 |
| 100 | 2.942 | 2.957 |

Matching the feature's multiplicative form does not make the richer baseline empirically preferable. These absolute errors describe the fixed comparisons; no penalty or model is promoted from evaluation performance.

Of the 12 reference contrasts, 12 point estimates favor omitting translation and 4 player/club-season intervals exclude zero in that direction. Every new reference player/season interval includes zero. Thus an adverse-effect inference also depends on the clustering specification; these results do not establish robust harm.

Outside the full pool, the original source-offset benchmark also favors omitting translation. Its increments by factor pool are:

| Factor pool | Penalty | Improvement | Player/club-season interval | Player/season interval |
| --- | --- | --- | --- | --- |
| A. Full corrected pool | 1 | -0.004 | [-0.026, 0.018] | [-0.015, 0.006] |
| A. Full corrected pool | 10 | -0.002 | [-0.028, 0.024] | [-0.017, 0.014] |
| A. Full corrected pool | 100 | 0.014 | [-0.030, 0.058] | [-0.023, 0.050] |
| B. Verified; full-season rates | 1 | -0.006 | [-0.011, -0.001] | [-0.015, 0.002] |
| B. Verified; full-season rates | 10 | -0.007 | [-0.012, -0.002] | [-0.013, 0.000] |
| B. Verified; full-season rates | 100 | -0.009 | [-0.017, -0.001] | [-0.016, -0.002] |
| C. Overlap keys; full-season rates | 1 | -0.006 | [-0.011, -0.001] | [-0.015, 0.002] |
| C. Overlap keys; full-season rates | 10 | -0.006 | [-0.012, -0.001] | [-0.014, 0.001] |
| C. Overlap keys; full-season rates | 100 | -0.008 | [-0.016, -0.000] | [-0.015, -0.001] |
| D. Overlap-window rates | 1 | -0.005 | [-0.017, 0.007] | [-0.020, 0.010] |
| D. Overlap-window rates | 10 | -0.005 | [-0.017, 0.007] | [-0.021, 0.011] |
| D. Overlap-window rates | 100 | -0.006 | [-0.021, 0.008] | [-0.029, 0.016] |

B (player/season) at penalty 10 has upper bound +0.00009, displayed as 0.000, so that interval includes zero. C (player/club-season) at penalty 100 has upper bound -0.00026, displayed as -0.000, so that interval excludes zero.

Across the three verified pools, all 18 source-aware increments (source offsets and cell slopes, each at three penalties) are negative, from -0.012 to -0.005 (each at most 0.4% of its parent MAE in magnitude). Of these, 10 player/club-season intervals exclude zero (6 source-offset and 4 cell-slope), whereas 2 player/season intervals do. The full pool has no interval excluding zero under either specification. These adverse differences are small and depend on the clustering specification; they do not establish general harm.

Every comparison evaluates the same original 674 player-season forecasts.
Native support and the intersection across every new arm and scenario are
reported separately, with exclusions. If a target row becomes unscorable, the
target comparison is inconclusive; an easier surviving subset cannot silently
replace it.

Uncertainty and magnitude are both necessary to interpret these contrasts.
Intervals spanning zero leave the direction undetermined and do not establish
equivalence. A small point estimate alone cannot establish either practical
value or negligibility because no justified recruitment-specific worthwhile
effect threshold is available. All registered penalties and factor pools remain
visible, including adverse differences. The robustness assessment also retains
the omission and seed sensitivities rather than promoting the most favorable
reference result.

## 6. Verification changes the factor pool and its support

Four ordered factor pools separate parts of the source restriction. A retains
the full corrected pool. B keeps full-season measurements for players passing
verified same-club identity and appearance-date checks, before overlap trimming.
C retains those measurements on exactly the keys eligible for the overlap-window
analysis. D replaces the measurements on those keys with common-window
aggregates, requiring eight games in each competition after trimming. The
forecasting target stays fixed across the sequence.

| Factor pool | Estimation pairs | Scored forecasts | Supported (nonfallback) forecasts | Factor fallbacks |
| --- | --- | --- | --- | --- |
| A. Full corrected pool | 4074 | 674 | 566 | 108/674 |
| B. Verified; full-season rates | 1537 | 674 | 118 | 556/674 |
| C. Overlap keys; full-season rates | 1463 | 674 | 113 | 561/674 |
| D. Overlap-window rates | 1463 | 674 | 113 | 561/674 |

The exclusion ledger records 2,440 factor-pair records with unverified identity and 97 multi-club pairs before overlap eligibility, then 70 pairs below the post-trim game requirement and 4 invalid-minute cases. Unverified does not mean incorrect. This is principally a verification-and-support sensitivity, not an experiment on changing clubs. Fallback is a factor-estimation policy; it is distinct from a refused forecast or an unknown appearance outcome.

### Registered restriction diagnostic (28 September)

After observing the support loss, we registered 200 random restrictions per control. Both reduce A to B's 1,537 pairs: one matches counts within each season; the other matches source league, destination competition and season counts. Sampling uses identities and strata, not outcomes. Each restriction refits the original factors and historical lags with 2,000 bootstrap draws, retaining the original regression-training keys and 674 forecast targets. Both original references reproduce before scoring. All 400 repetitions score every target in all 12 arms, with no unavailable factors. These are exploratory, conditional restrictions.

Median and empirical 2.5th/97.5th percentiles below. MAE and increments use source-offset penalty 10. Positive increment favors translation. All penalties, failures, full ranges and keyed outputs are retained.

| Pool/control | Supported (nonfallback) / 674 | MAE with translation | Translation increment | Complete repetitions |
| --- | --- | --- | --- | --- |
| Full corrected pool | 566 | 2.926 | -0.002 | reference |
| Verified pool | 118 | 2.931 | -0.007 | reference |
| Season counts | 91.0 [71.0, 114.0] | 2.929 [2.908, 2.948] | -0.005 [-0.024, 0.016] | 200/200 |
| Cell and season counts | 112.0 [68.0, 118.0] | 2.930 [2.913, 2.961] | -0.006 [-0.037, 0.011] | 200/200 |

These restrictions are conditional on the observed pool and inherited estimator. Verified rows were not randomized. Values inside these ranges are attainable under the declared restriction; this does not establish that sample loss caused the observed verification result. Successful-repetition loss summaries are conditional if any target is incomplete.

Destination-specific comparisons are less uniform. EuroLeague's verified pool retains 68/194 nonfallback forecasts; season-count restrictions retain a median 35 (full range 21–49), whereas cell-and-season restrictions retain a median 68 (full range 55–68). The verified count is outside the first range and inside the second. This remains a conditional diagnostic, not a causal verification effect. The supplement reports every season and destination, with each original stratum denominator retained.


A-to-B changes verified-population composition and estimation support together.
B-to-C adds overlap and trimmed-exposure eligibility selection. C-to-D changes
measurements on fixed factor-pair keys. These comparisons locate sensitivity
within the sequence but do not isolate causal effects of club continuity,
common roles or fallback. B retains full-season eligibility and does not certify
every minute value; appearance-date overlap is not a contract record. Available
identity evidence may itself select players with better surviving documentation.

The slope comparison uses all 56 preserved upstream scenarios. These include the
reference, individual estimation-season omissions and separate seed runs for
each factor pool. Upstream runs retained 2,000 factor-bootstrap draws. The new
analysis recovers their saved historical features and fits the additional
regressions; it does not estimate another set of league factors. Before scoring,
the original-arm forecasts and training keys must reproduce within the
registered numerical tolerance.

Every omission and seed range is retained in the supplement; neither is a confidence interval.

Season omissions remove direct factor, lag and regression-estimation
contributions; historical player covariates remain fixed and can still contain
information from the omitted season. Omission ranges therefore describe the
registered refit operation, not complete deletion of that season from every
measurement. Seed ranges describe a different perturbation and are reported
separately.

Conditional uncertainty uses paired forecast losses with player/recorded
destination-competition–club–season and player/season dependence specifications.
The recorded club is the most frequent team label within the competition-season
aggregate; multi-club records are not assigned to every contributing club. Multiway clustering addresses specified
shared groups [10]; it does not include every source of uncertainty. The intervals
condition on fitted predictions, are not simultaneous guarantees across the
correlated arms, and are distinct from refit ranges or future prediction
intervals. Only six destination seasons are evaluated, limiting the information
available about transport across time. The supplement gives the cluster variance,
Student-t degrees of freedom and unavailable-inference rules. No equivalence
margin or prospective power calculation supports an absence-of-value claim.

## 7. What an analyst can take from the comparison

Consider an analyst deciding whether to add the paired feature to an existing
forecast used to prioritize video review. This is a proposed use, not a tested
club intervention. The present evidence supports a specific evaluation sequence:

| Analyst's question | What this comparison supplies | What remains unknown |
| --- | --- | --- |
| Does the feature add to the information already available? | Paired losses against history, destination and source-aware forecasts on identical targets | Performance of the club's own comparator on a new cohort |
| Is a forecast supported by that player's source–destination cell? | Separate counts for nonfallback factors, destination-mean fallbacks and scored forecasts | Validity of the factor for an individual role or future opportunity |
| Does factor reliability tell us when to use translation? | A complete-cohort test of the inherited routing rule | A validated rule that improves future decisions |
| Does the output improve recruitment or own-roster planning? | A limited conditional-rate benchmark and explicit refusal boundaries | Candidate availability, minutes, role fit, costs and decision benefit |

A club should not infer that two candidates with similar point forecasts are
interchangeable, use a factor interval as a player-outcome interval, or treat a
refusal as evidence of poor ability. The paper supplies no calibrated
individual uncertainty with which to justify those uses.

A separate exploratory amendment asks whether the existing factor-reliability
rule can select when translation is useful. Negative transfer and selective use
of source information are established research problems [20]; this is a test of
an inherited rule, not a new routing method. The protocol was pushed before
implementation and calculation, after the original outcomes were exposed.
For every frozen target, the policy uses the augmented forecast when the full
historical reliability predicate holds and the separately fitted parent
otherwise. It scores the complete cohort, rather than selecting an easy subset.

The policy supplement
retains both model families, every fixed penalty, pool and scenario, as well as
comparisons with always using the parent and always using translation.

| Family (penalty 10) | Parent MAE | Policy MAE | Improvement | Conditional 95% interval |
| --- | --- | --- | --- | --- |
| Source offsets | 2.924 | 2.922 | 0.002 | [-0.024, 0.028] |
| Offsets + cell slopes | 2.993 | 2.994 | -0.001 | [-0.024, 0.022] |

These are the amendment's prespecified primary full-pool comparisons, not a selected best penalty. Positive favors the policy. Intervals use player/recorded-club-season dependence; the player/season alternatives also include zero. The linked policy report retains comparisons with always using translation and every sensitivity. Values are read from the saved direct policy readback; no policy is refitted here.

The registered primary comparisons did not establish improvement: the offset
policy has only a small, uncertain MAE gain, while the slope policy has higher
point MAE than its parent and the source-offset benchmark. Their conditional
intervals include zero under both dependence specifications. Destination and
sensitivity reversals also prevent the stronger robustness claim. The existing
reliability gate is not demonstrated to select useful incremental translation
on this target. This result does not prove equivalence or general harm from
translation, and it does not authorize changing the operating forecast.

Average absolute error is the main comparison, not a complete description of
the forecasts. The supplement retains signed
bias, RMSE, median and tail error, improvement shares, every evaluation season
and destination, and the worked forecast examples. These diagnostics remain
descriptive. An improvement share is not the fraction of successful signings;
neither a favorable subgroup nor a selected example confirms a new use case.

Recruitment value requires a further step: a defined decision, feasible options
and the cost of a wrong choice [11]. The present appearance-qualified rate
forecast does not supply those ingredients. Equally, factor-estimation intervals
are not calibrated player-outcome intervals. A future uncertainty forecast would
need evaluation of width and misses together rather than coverage alone [12].
A useful next evaluation would freeze one actual decision before its outcomes:
for example, which eligible players deserve a fixed number of scouting hours.
Define the candidate set, information date, comparator and cost of missed or
wasted reviews with the club; preserve missing outcomes and refusals. Evaluate
the decision rule on an unexposed cohort, alongside the rate forecast among
players with a defined rate. Own-roster planning would require a separately
defined population and opportunity outcome. This is a proposed next study,
not an executed pilot or a newly accepted protocol.

## 8. Reproducibility, remaining limits and conclusion

The numerical package records input, protocol and code hashes, historical feature
tables, training keys, coefficients, scales, categories, exclusions and keyed
predictions. Generated tables and figures are linked to those outputs. The
supplement provides the full diagnostic tables;
the evidence and release guide records
the reproduction command, claim traceability and release-scope inventory. A local
reproduction package and a permission-cleared public repository are distinct
deliverables.

Unknown identities and unresolved source conflicts remain explicit. The existing
conflicting birth-date identity stays quarantined in its affected season, and
numerical reproduction does not independently repeat raw identity adjudication.
The recorded Proballers permission is preserved without extending it to
unresolved continental or expanded-table release scopes. These restrictions
limit the public package independently of the statistical results.

Adverse preceding evidence is retained in the supplement: the protected holdout
is PARTIAL, the equal-count scheduled-versus-transfer sensitivity reversed its
original direction, and structural-multiplier simulations undercovered a
different estimand. None is repaired merely by adding an expanded benchmark.
The all-arrival denominator remains unverified. The separate appearance studies
and September operating forecast lock do not confirm this research pipeline;
their populations and procedures must not be combined with these results.

The benchmark is not a complete player model. Age-dependent development,
position, role, injuries and team context are not comprehensively benchmarked
here. Prior work's use of longitudinal histories and age [15,16,18] makes these
substantive omissions, not evidence that translation compensates for them.
Testing such extensions requires a separate design and outcome-blind selection. None would, by itself,
identify performance for an unenumerated population of arrivals.

Robust incremental superiority is not established across the registered comparisons. The evidence supports three reporting practices: compare against competition-aware forecasts, separate factor support from forecast coverage, and evaluate a reliability rule by its forecast losses rather than its name. These are lessons for evaluating this additional modeling step, not proof that translation is unnecessary. Demonstrating club value requires an unexposed, decision-specific evaluation; further tuning on these seasons cannot provide it.

![Paired gains from adding translation](figures/sloan_v10_benchmark_increments.png)

*Figure 1. Paired MAE improvements after adding translation to each specified baseline, full corrected pool. Positive favors translation. Solid whiskers: conditional 95% intervals clustered by player and club-season; dashed: clustered by player and season (six seasons). Hollow markers: the solid interval includes zero. The three offset penalties and three slope penalties are all retained.*

![Verification and estimation support](figures/sloan_v10_verification_support.png)

*Figure 2. Factor-pool support and the increment beyond source offsets plus cell slopes. Bars partition the fixed forecast target into forecasts with a supported (nonfallback) league-pair factor and destination-mean fallbacks; annotations show separate estimation-pair counts, and triangles under pool B mark the median supported counts (season-matched and league-pair-matched) in the registered random restrictions to the same number of pairs. Pool labels in both figures abbreviate A-D; B-D use verified identities. The right panel shows the cell-slope family; source-offset increments by pool are tabulated in Section 5. No forecasts are refused. Solid and dashed whiskers and hollow markers follow Figure 1; both interval types condition on fitted forecasts and omit upstream refitting uncertainty. Restrictions change composition and support together; unverified does not mean incorrect.*

## Future confirmation requires the same prediction task

The 2026–27 opportunity study predicts minutes and appearances; it cannot
confirm an EFF/36 translation increment. The September 12 operating lock also
uses a different fitting and selection procedure. Neither is relabeled here.

A valid confirmation must freeze the exact factor, pooling, lag, history,
eligibility and regression code before its evaluation outcomes are inspected.
Date the player population and information cutoff, retain all penalties and
prespecify the source-offset penalty-10 comparison as primary, with matched
with/without-translation forecasts for each target. The outcome remains
EFF/36 over a declared destination window; later minutes, source corrections
and identities cannot enter the forecast snapshot. Commit predictions,
exclusions, refusals, source hashes and scoring code before unblinding.

A roster population differs from this appearance-qualified target: retain a
separate arrival and opportunity ledger. Zero minutes means undefined EFF/36,
not zero efficiency; report that denominator separately. Choose a decision-relevant
worthwhile effect and uncertainty procedure before unblinding, or report
magnitude and uncertainty without an equivalence claim. No new confirmation
forecasts or unexposed results are created in this revision.

## References

1. Lee, D.-J., and Page, G. L. (2021; report of ESGI 2017). *Big Data in Sports:
   Predictive Models for Basketball Player's Performance*. Working paper.
   https://doi.org/10.33774/miir-2021-h4x62.
2. Glazer, A. K. (2026). *Nuthin' But A G League: Estimating league translation
   factors*. Journal of Sports Analytics. https://doi.org/10.1177/22150218261428808.
3. Vashro, L. (2015). *Measuring Level of Competition Around the World*.
   https://fansided.com/2015/11/06/deep-dives-measuring-level-of-competition-around-the-world/.
4. Pelton, K. (2013). *What is SCHOENE?*
   https://www.espn.com/nba/story/_/id/9797404/explaining-schoene-projection-system.
5. Dinsdale, D., and Gallagher, J. (2022). *Transfer Portal: Accurately Forecasting
   the Impact of a Player Transfer in Soccer*. Preprint.
   https://arxiv.org/abs/2201.11533.
6. Shaikh, M. A. (2026). *Hierarchical Bayesian modeling of cross-league performance
   translation in elite football*. https://doi.org/10.1177/22150218261481583.
7. Franz, V. H. (2007). *Ratios: A Short Guide to Confidence Limits and Proper Use*.
   https://arxiv.org/abs/0710.2024.
8. Efron, B., and Morris, C. (1975). *Data Analysis Using Stein's Estimator and
   Its Generalizations*. https://doi.org/10.1080/01621459.1975.10479864.
9. Cawley, G. C., and Talbot, N. L. C. (2010). *On Over-fitting in Model Selection
   and Subsequent Selection Bias in Performance Evaluation*. JMLR, 11, 2079–2107.
   https://jmlr.org/papers/v11/cawley10a.html.
10. Cameron, A. C., Gelbach, J. B., and Miller, D. L. (2011). *Robust Inference
    With Multiway Clustering*. https://doi.org/10.1198/jbes.2010.07136.
11. Elmachtoub, A. N., and Grigas, P. (2022). *Smart "Predict, then Optimize"*.
    https://doi.org/10.1287/mnsc.2020.3922.
12. Gneiting, T., and Raftery, A. E. (2007). *Strictly Proper Scoring Rules,
    Prediction, and Estimation*. https://doi.org/10.1198/016214506000001437.
13. Yeh, C.-K., Rice, G., and Dubin, J. A. (2022). *Evaluating Real-Time
    Probabilistic Forecasts With Application to National Basketball Association
    Outcome Prediction*. https://doi.org/10.1080/00031305.2021.1967781.
14. Salador, K. (2011). *Forecasting Performance of International Players in the
    NBA*. MIT Sloan Sports Analytics Conference. Original-paper mirror; official
    PDF unavailable at retrieval.
    https://paperzz.com/doc/7227688/forecasting-performance-of-international-players-in-the-nba.
15. Vinué, G., and Epifanio, I. (2019). *Forecasting basketball players' performance
    using sparse functional data*. https://doi.org/10.1002/sam.11436.
16. Demsyn-Jones, R. (2019). *Misadventures in Monte Carlo*.
    https://doi.org/10.3233/JSA-170220.
17. Daumé III, H. (2007). *Frustratingly Easy Domain Adaptation*. ACL.
    https://aclanthology.org/P07-1033/.
18. Vaci, N., Cocić, D., Gula, B., and Bilalić, M. (2019). *Large data and
    Bayesian modeling—aging curves of NBA players*. Behavior Research Methods.
    https://doi.org/10.3758/s13428-018-1183-8.
19. Schuckers, M., Lopez, M., and Macdonald, B. (2023). *Estimation of player
    aging curves using regression and imputation*. Annals of Operations Research.
    https://doi.org/10.1007/s10479-022-05127-y.

20. Wang, Z., Dai, Z., Póczos, B., and Carbonell, J. (2019).
    *Characterizing and Avoiding Negative Transfer*. CVPR.
    https://arxiv.org/abs/1811.09751.

The literature ledger records retrieval and
claim boundaries for the existing references. External empirical results have
not been independently reproduced in this study.
The literature development record
adds the new source comparisons, access limitations and implications for this
revision.
