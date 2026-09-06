# PRE-REGISTRATION — 2026-27 prospective predictions

**Reconstructed and committed 2026-08-25. Ticket: ATI-2891. Status: proposed, not yet locked.**
Lock deadline **24 September 2026**, tip-off.

> **Read this paragraph before anything else.** A draft dated 2026-08-17 fixed the seven elements
> ATI-2891 requires, and `preregistration-2026-27-amendment-1-2026-08-21.md` and
> `preregistration-2026-27-amendment-2-2026-08-25.md` were both written against it. **That draft was
> never committed.** It is not in any git ref, on disk, in any worktree, in `_local/`, in any session
> scratchpad, or in Notion — searched 2026-08-25. This document reconstructs it. **It carries today's
> date, not the draft's**, and §0 below marks every section as either *recovered* — quoted verbatim
> inside a dated amendment, so its content is genuinely fixed as of that amendment's date — or
> *reconstructed*, meaning written on 2026-08-25 from ATI-2891, the sibling retrospective
> pre-registration, and the committed estimator code.
>
> Nothing here is fitted to 2026-27 outcomes, because none exist: the season has not been played.
> That is what makes reconstruction legitimate at all. It does **not** make the reconstructed
> sections as strong as the recovered ones, and §0 is the honest accounting of which is which.

## Specification

| Choice | This pre-registration | Alternatives considered |
|---|---|---|
| **Unit** | one (player, 2026-27 destination season) import arrival into EuroLeague or EuroCup | per club-season; per (player, competition) stint |
| **Population** | `kind == "import"` arrivals carrying a translatable prior league, per `src/data/signings.py` | all arrivals (rejected — `returning_to_club` roughly doubles the count); imports without a prior league (refused, not scored) |
| **Prediction basis** | per-league factor table **plus** regression to the mean, combined (Amendment 2 Change 2) | per-league alone (a tie against league-free RTM); one global scalar (separably worse) |
| **Level correction** | `K_LAG` refit on seasons strictly prior to the prediction season (Amendment 1 Change 2) | the locked 0.9473 (rejected — fitted partly on evaluation seasons) |
| **Baselines** | B0 untranslated, B1a oracle minutes, B1b honest one-constant, B1c league-free RTM | B0 alone (rejected — Amendment 1 Change 4) |
| **Uncertainty** | paired cluster bootstrap on destination club-season, 4,000 draws, seed 0 | i.i.d. bootstrap (rejected — players cluster by club-season) |
| **Interval** | `[point × 0.4986, point × 1.6392]`, **nominal 95%, realised 0.922** | factor-SE only (realised coverage 0.0952) |
| **Scored population** | a dated collection count, restated at lock (Amendment 2 Change 4) | a fixed ~69 (rejected — the list has moved 69 → 94 → 110 and is still growing) |

**Status of this document.** This is a PLAN. It states no 2026-27 result, because the season has not
started. Its executable form is `scripts/build_league_factors.py` (the estimator),
`scripts/validate_translation_holdout.py` and `scripts/validate_translation_walkforward.py` (the
evidence the bars rest on), and `scripts/collect_import_signings.py` (the player set).

---

## 0. Provenance of every section — recovered or reconstructed

METHOD.md §8 forbids moving a threshold after a result. It says nothing about a document that cannot
be read at all, because that failure was not anticipated. This table is the substitute: it lets a
reader see exactly which bars were fixed before the evidence and which were written afterwards.

| § | Content | Status | Where it is fixed |
|---|---|---|---|
| **§1** | Threat list | **RECONSTRUCTED** | Amendment 1 says "§1 threat list … unchanged" but never quotes it |
| **§2** | Player set and inclusion conditions | **RECONSTRUCTED** | named as unchanged, never quoted |
| **§3** | Refusal codes | **RECONSTRUCTED** | named as unchanged, never quoted |
| **§4** | Prediction basis, `K_LAG` rule, interval | **RECOVERED** | Amendment 1 Changes 2 and 3; Amendment 2 Change 2 |
| **§5** | Baselines B0 / B1a / B1b / B1c | **RECOVERED** | Amendment 1 Change 4; Amendment 2 Change 3; definitions in `translation-holdout-preregistration-2026-08-17.md` §3 |
| **§6** | Metrics and scoring rule | **RECONSTRUCTED** | named as unchanged, never quoted |
| **§7** | Scored population, power line | **RECOVERED** | Amendment 2 Change 4; Amendment 1 "Power" section |
| **§7b** | Figures | **UNRECOVERABLE** | referenced by Amendment 1 and never described anywhere. No figure in this document is load-bearing; see §7b |
| **§8** | Success criteria | **RECOVERED (margin), RECOVERED (its derivation, found 2026-09-06)** | Amendment 1 Change 4 quotes the 12.8% B0 margin and adds B1b. The derivation was found on 2026-09-06 in the 2026-08-17 22:57 UTC Linear comment on ATI-2891 (`df67e2e0-adcc-4fd0-8ab0-34e98d3c442e`) that posted the draft: *"Set at the study's own one-sided 80%-power MDE at n=69 — not the historical 17.9% … and not lower."* The same comment declared in advance that the worst walk-forward season (2025, 10.7%) falls below the margin, "so a 2026-27 resembling 2025 would fail this pre-registration." See §0.1 below |
| **§9** | Evaluation checkpoint dates | **RECONSTRUCTED** | named as unchanged, never quoted. Dates below are set on 2026-08-25 |
| **§10** | Corrections policy; §10.1 projected population | **RECOVERED (§10.1 figure), RECONSTRUCTED (policy)** | Amendment 1 quotes "~79 predictable / ~69 scored" as §10.1 |
| **§11** | Verdict rule | **RECOVERED (PARTIAL), RECONSTRUCTED (PASS / FAIL)** | Amendment 1 Change 1 quotes the PARTIAL branch verbatim; the PASS and FAIL wording is quoted nowhere |
| **§12** | Limitations | **RECONSTRUCTED** | named as unchanged, never quoted |

### §0.1 External timestamp of the 2026-08-17 draft — added 2026-09-06

The 2026-08-17 draft was never committed, but it was **posted**: Linear issue ATI-2891 carries a
7,754-character comment created **2026-08-17 22:57:31 UTC** (id `df67e2e0-adcc-4fd0-8ab0-34e98d3c442e`,
"Pre-registration drafted and ready to lock"). That comment fixes, with a timestamp independent of
this repository and four days before Amendment 1: the seven elements; the inclusion rule (five
mechanical conditions, no role filter); refusal codes R1–R4 with their rates (R1 42%); the interval
construction (point × [0.4986, 1.6392], realised coverage 95.9% on the corpus of the day); `K_LAG`
0.9473; the success margin **12.8% of B0's MAE at ≥10 destination games, end of season, set at the
one-sided 80%-power MDE at n = 69**; the checkpoints (lock 23 Sep 2026, mid-season 11 Jan 2027 as a
non-decision read, end-of-season 10 May 2027); the gate-fail branch in five parts; and the advance
declaration that a season like 2025 (10.7% over B0) would fail the margin. The sibling holdout
verdict was posted one minute earlier (ATI-2799, `11bd4fbf-4a94-4381-a832-40aa37997458`,
2026-08-17 22:56:54 UTC). Sections marked RECONSTRUCTED above remain reconstructed as *text*; where
the comment states a value, the value is independently dated 2026-08-17.

**The one place this matters most.** §8's primary margin — beat B0 by ≥12.8% of B0's MAE — is
recovered as a *number*, and since 2026-09-06 its derivation is recovered too (§0.1). It is retained unchanged, because lowering it
would relax a bar and raising it would be no more honest. A reader should treat the 12.8% as fixed
before the ATI-2799 outcome (Amendment 1, dated 2026-08-21, quotes it as pre-existing) but should
be shown the derivation as the comment states it, not a reconstruction of it. The comparable margin in the sibling document,
G1's 5%, does carry its derivation, and it is a *weaker* bar than this one.

---

## 1. Threats, and the control for each

METHOD.md §1: the control is written before the result and runs whether or not anyone remembers to
look. Controls marked **in-script** already exist as asserts in the named committed script.

| # | Threat | Control |
|---|---|---|
| **T1** | **Population mismatch.** Factors are fitted on same-season dual-tier pairs; these are consecutive-season transfers | Measured, not asserted: the price is **0.39 PIR/36 of MAE and 0.064 of R²** (ATI-2799 T1). Quoted beside every 2026-27 result |
| **T2** | **Temporal leakage.** 2026-27 information entering any fit | Every arm — factor table, `K_LAG`, RTM coefficients — is fitted on seasons **strictly ≤ 2025**. In-script in `validate_translation_walkforward.py` |
| **T3** | **Name-matched prior league.** The arrival diff uses EuroLeague person ids, but the prior-league lookup is a name join into Proballers | Carries the ATI-2796 error rate. Every prediction is labelled with the provenance of its prior league; a wrong prior league is a wrong prediction and is **scored as one**, not excluded after the fact |
| **T4** | **Missing rosters read as zero.** Six EuroCup clubs return an empty 2026-27 roster upstream | Refusal code **R7**. Reported as *missing, not zero*, with the club codes named. `SigningsReport.clubs_with_empty_roster` keeps them separate by construction |
| **T5** | **Selection / regression to the mean.** Players move because they improved or declined | Partly *modelled* rather than merely controlled since Amendment 2: the combined arm includes RTM predictors from the player's own history. The residual is reported by splitting on whether the source-season rate exceeded the player's own prior-seasons mean |
| **T6** | **Name collision.** Proballers has no stable person id | Re-score excluding names appearing with ≥4 distinct leagues, and names appearing with >1 club inside one league-season |
| **T7** | **Survivorship.** Only players who earn ≥8 destination games are scored | Count the censored (refusal **R8**) at every checkpoint, and re-score at ≥5 and ≥15 games as a sensitivity |
| **T8** | **Reliability floor.** A low R² may mean "not predictable" | Ceiling **R² = 0.70** quoted beside every R². Every null carries `assert_powered_for_null` |
| **T9** | **Pooling collapse.** τ² = 0 returns one identical factor per block (ATI-2901) | Assert τ > 0 in every PIR block of every refit; a collapsed block's per-league reads are uninterpretable, not merely weak |
| **T10** | **Estimator choice is load-bearing** (METHOD.md §3/§6) | Re-score with `ratio_of_sums` and `mean_of_ratios`; if the spread exceeds the §8 margin, the verdict is declared estimator-dependent |
| **T11** | **The +0.019 null bias** (ATI-2904). The exposure-weighted estimator returns ~1.019 when the truth is 1.0 | Re-score with every factor divided by 1.019 and report whether the verdict changes. A verdict that flips is reported as fragile |
| **T12** | **In-season disruption** — mid-season transfer, injury, minutes collapse, coaching change | Handled by the rules in §2, fixed here in advance rather than chosen when the outcomes are visible |

## 2. The player set and the inclusion conditions

**Included.** One row per (person, 2026-27) where the person is an `import` arrival — never appeared
in that competition in any season we hold — into a EuroLeague or EuroCup club, and carries a prior
league present in the corpus. Classification is `src/data/signings.py`, whose four kinds
(`import`, `intra_league_move`, `returning_to_club`, `returning_to_league`) exist precisely because a
naive `current − previous` set difference calls all four new.

**Scored** at a checkpoint when the player has **≥8 games** in the destination competition by that
checkpoint. Below 8 he is censored, not failed (refusal **R8**).

**Prediction target.** Realised per-36 PIR in the destination competition, largest-minutes stint,
from the same box-score corpus the factors are built on.

**The four in-season disruptions, decided now:**

* **Mid-season transfer out of the destination** — scored on his destination-club stint only. A move
  to a third competition does not retroactively remove him from the set.
* **Injury** — scored regardless if he reaches ≥8 games; censored under R8 if he does not. Injury is
  never a reason to remove a player who *was* scored.
* **Minutes collapse** — scored regardless. Per-36 normalises minutes; a role collapse is a real
  prediction error and is counted as one.
* **Coaching change** — scored regardless, and named in §12 as an uncontrolled source of error.

## 3. Refusal codes

Refusals are a first-class output (ATI-2891 acceptance criterion 5). A prediction set with no
refusals means the refusal rule is not working. Every refused player is **published with his code**.

| Code | Meaning |
|---|---|
| **R1** `NO_PRIOR_LEAGUE` | An import whose prior league is not in the corpus. `translation_available == False` |
| **R2** `NOT_AN_IMPORT` | `intra_league_move`, `returning_to_club`, `returning_to_league`. Prior production is already continental and needs no translation |
| **R3** `SOURCE_REFUSED` | Prior league is `poland-plk` (its EuroLeague cell rests on n=7) or in the estimator's `NOT_A_SOURCE` set (`bcl`, `test`, and the two continental competitions) |
| **R4** `DEGENERATE_RATE` | Non-positive source per-36 rate — an undefined ratio |
| **R5** `INSUFFICIENT_SOURCE_GAMES` | Fewer than 8 games in the source league-season |
| **R6** `UNRELIABLE_CELL` | **Not a refusal — a labelled fallback.** `reliable = False` on the source→destination cell, so the tier mean is used, as the estimator's docstring requires. The prediction is published **labelled as a tier-mean fallback** |
| **R7** `ROSTER_MISSING` | The club's 2026-27 roster is absent upstream. **Missing, not zero** |
| **R8** `NOT_SCORED_YET` | Fewer than 8 destination games at this checkpoint. Censored, re-read at the next checkpoint |

## 4. The prediction basis

**Recovered, and as amended.** Per player, a projected destination per-36 PIR **with an interval** —
never a point estimate alone.

**The arm.** Amendment 2 Change 2: the 22-cell per-league factor table **together with**
regression-to-the-mean predictors fitted on seasons strictly prior to the prediction season.
Per-league resolution is retained because it demonstrably adds to RTM (+0.2066, CI [+0.1393,
+0.2786]), not because it beats one constant.

**Per-player method, declared in advance.** A player is scored through the combined arm when he has
**at least two qualifying corpus seasons** (a source season plus prior history), and through
per-league factors alone otherwise. **The publication must label which method scored each player.**

**The level correction.** Amendment 1 Change 2:

> `K_LAG` is the median realised ratio of observed to predicted per-36 PIR, computed on newcomer
> cohorts from seasons **strictly before the prediction season**. For 2026-27 this is seasons
> ≤ 2025. The value is computed once, recorded here before tip-off, and never refit afterwards.

The six prior-season-only refits ran 0.9285–0.9368. The originally locked 0.9473 sits outside that
range, consistent with having been fitted partly on evaluation seasons; it is not used.

**The interval.** Amendment 1 Change 3:

> Intervals are **nominal 95%, realised 0.922** on held-out transfers (ATI-2799 G7). Every published
> interval carries the realised figure. No channel describes them as 95% without it.

Construction is `[point × 0.4986, point × 1.6392]`. It is kept because the alternative is far worse —
a factor-SE-only interval realises 0.0952 coverage.

**The RTM arm's status.** It is **not pre-registered**. It was added to a shipped analysis after its
result was seen, and the walk-forward note carries a dated addendum saying so. It is admitted as a
declared-in-advance amendment, legitimate only because no 2026-27 outcome exists to fit to.

## 5. The baselines

All predict destination per-36 PIR on the same rows.

| Name | Prediction |
|---|---|
| **M** — the model | the combined arm of §4 |
| **B0** — untranslated | `pir_per36_src(t)` |
| **B1a** — minutes scaling, **oracle** | `B0 × (min_per_game_dest / min_per_game_src)`, given realised destination minutes the model never sees |
| **B1b** — minutes scaling, honest | `B0 × k`, one constant fitted to minimise error on the scored set itself |
| **B1c** — regression to the mean | the player's own prior-season and source-season rates, coefficients fitted on seasons strictly before the prediction season, **no league information** |

B1a is reported because it was pre-registered and because it is a caution: on ATI-2799 it was the
**worst** predictor in the table (R² = −2.34). Per-36 already normalises minutes, so rescaling by
them double-counts the role change.

B1c is the strongest available league-free comparator and enters as a **secondary** criterion, for
the power reason in §8.

## 6. Metrics and the scoring rule

* **MAE** and **R²** on realised destination per-36 PIR, both against every baseline in §5.
* **Interval coverage** — the fraction of outcomes inside the published interval. **Over-coverage and
  under-coverage are both failures**; an interval too wide is as uninformative as one too narrow.
* **Uncertainty** — paired cluster bootstrap resampled on **destination club-season**, 4,000 draws,
  seed 0. Players on one club in one season are not independent observations.
* **Ceiling** — destination split-half reliability implies **R² = 0.70** as the maximum attainable on
  single-season continental PIR/36. It is quoted beside every R².
* **Power line, mandatory** (METHOD.md §7). Every negative is phrased as "no detectable effect at
  n=X; detecting Y requires n=Z", via `assert_powered_for_null`.

No metric in this list may be added, dropped or reweighted after the first 2026-27 game.

## 7. The scored population, and the power it has

**Recovered.** Amendment 2 Change 4 replaced a fixed count with a rule:

> The scored population is the count of `kind == "import"` arrivals carrying a translatable prior
> league, **as of a dated collection recorded in the publication**. The publication states its own
> collection date and count, and the power figures below are restated at that count.

The list has moved **69 → 94 → 110** and is still growing. The committed dated collections are in
`data/processed/signings/`, produced by `scripts/collect_import_signings.py --competition both`
(ATI-2917). The 110 is not yet one of them: it predates the pre-lock collection, which upstream
publication has so far blocked. The bar is the dated rule above, not this illustrative count.

**Power, at the illustrative n = 110** (Amendment 2 Change 3, scaling each pooled interval):

| Criterion | Pooled effect | Power at n=110 | n for 80% |
|---|---|---|---|
| beat **B0** untranslated | +0.8217 | **0.84** | 99 |
| beat **B1b** oracle one-constant *(primary)* | +0.2014 | **0.36** | 332 |
| combined beats **B1c** RTM *(secondary)* | +0.2066 | **0.62** | 167 |
| league adds to RTM | +0.1909 | **0.33** | 371 |

> **Only the B0 criterion is adequately powered by the 2026-27 set.** B1b has roughly **36%** power at
> n = 110, so a single prospective season returns **PARTIAL by construction more often than not**, and
> a PARTIAL on B1b must not be read as the model having failed — it is the season being too small to
> adjudicate. The pooled walk-forward evidence (n = 719) is what carries the B1b and B1c claims; the
> prospective set tests B0.

**And the limit Amendment 1 already fixed:** the 2026-27 set **cannot** adjudicate per-league
resolution on its own. Within any single season it is not separable at this n — 2024 alone gave
+0.0992, CI [−0.1124, +0.3668]. Promising otherwise would over-claim.

### 7b. Figures

Amendment 1 lists "§7b figures" among what it leaves unchanged. **Nothing anywhere describes what
they were, and they are not reconstructed.** No figure in this document is load-bearing: every claim
is carried by a table with its interval. Any figure in the publication is illustration, and is
generated from a committed artifact at publication time.

## 8. The success criteria

**Two primaries. Both must pass for a PASS.**

1. **Beat B0** — untranslated production — by **≥12.8% of B0's MAE**, with a paired cluster-bootstrap
   interval excluding zero. *Recovered from Amendment 1; its derivation is not recorded and is not
   invented here — see §0.*
2. **Beat B1b** — source rate times a single constant fitted to minimise error on the scored set
   itself — on MAE, with a paired cluster-bootstrap interval excluding zero. *Amendment 1 Change 4.
   The bar is a margin the model has demonstrated out-of-sample (+0.2014, CI [+0.1096, +0.3011])
   against a deliberately oracle-advantaged comparator, not an aspiration.*

**Secondary criteria.**

* **Beat B1c** — the league-free RTM model. Secondary rather than primary because the prospective set
  has ~62% power for it (§7).
* **Interval coverage in [0.90, 0.98]**, read against the realised 0.922 label of §4.

**No threshold in this section may be edited after the first 2026-27 game is played**, including by a
rounding margin and including while calling the new value conventional (METHOD.md §8).

## 9. Evaluation checkpoints

Fixed on 2026-08-25, before tip-off. Both reads run the same script with no further design decisions
(ATI-2891 acceptance criterion 4).

| Checkpoint | Date | Scored population |
|---|---|---|
| **Mid-season read** | **2027-01-31** | every scored player at ≥8 destination games by that date; the rest reported under R8 |
| **End-of-season read** | **2027-06-30** | every scored player at ≥8 destination games in 2026-27 |

The end-of-season read is additionally reported at **≥5 and ≥15** games as the T7 survivorship
sensitivity. The ≥8 figure is the headline at both checkpoints; the threshold does not change between
them, so the two reads are the same population observed twice.

## 10. Corrections

* **No revisions after tip-off.** Not to the player set, not to the projections, not to the metrics,
  not to the success margins. If something is found wrong, it is documented as wrong **and scored
  anyway**.
* **A correction is made in place, with the retraction visible** (METHOD.md). A silently edited number
  is worse than a wrong one.
* **Being publicly wrong is an acceptable outcome.** Pre-registered and wrong is more credible than
  never testable.

### 10.1 Projected population, as originally stated

The 2026-08-17 draft projected **~79 predictable / ~69 scored** players. Both figures are superseded
by the dated-count rule of §7 and are recorded here only because Amendment 1 quotes them.

## 11. The verdict rule

* **On PASS** *(reconstructed)* — both §8 primaries met, with intervals excluding zero. Publish the
  predictions and the full scored set, including refusals, with the realised interval coverage stated.
* **On PARTIAL** *(recovered verbatim, Amendment 1 Change 1, accepted as written on 2026-08-25)* —

  > the pooled MAE and generalisation gates pass; a baseline-superiority sub-gate fails or ties:
  > **publish predictions, with the scope narrowed to the passing claims and the failing sub-gate
  > named in the publication body — not a footnote.** The prediction set is built exactly as under
  > PASS. The publication must state which sub-gate failed, its point estimate and interval, and what
  > it implies the model cannot claim.

* **On FAIL** *(reconstructed)* — the B0 primary is missed. **Publish the negative result.** A model
  that does not beat untranslated production is a finding, and ATI-2891 names publishing it as the
  specified output. Do not publish projections.

**The ATI-2799 gate returned PARTIAL** — G1, G2, G3, G5, G6 pass; G4 ties a single-constant baseline
at −0.005 MAE, CI ~~[−0.236, +0.230]~~ [−0.230, +0.240] *(interval corrected 2026-09-04 to the committed generator's paired bootstrap, ATI-2955; the tie stands)*. **G4 is not re-scored.** The publication names it in the body.

## 12. Limitations

Not caveats. METHOD.md's distinction: a caveat is a testable confound and becomes a test (§1); a
limitation is a scope bound nothing in this data can discharge.

* **No birthdates, so no aging adjustment** (ATI-2766). A transfer spans a year of aging the model
  cannot see. This is a permanent component of the error, not a bug.
* **No pace or opponent-strength adjustment** inside the factor.
* **The nationality-quota confound is not controlled.** Domestic leagues carry quotas that
  EuroLeague does not; the estimator's own docstring says so, and the Israeli magnitude (−0.030) is
  larger than that cell's bootstrap SE.
* **Coaching and system change are not modelled**, only declared (§2).
* **`differs_from_parity` is used nowhere**, here or downstream. Its false-positive rate was measured
  at 13–33% against a nominal 5% (ATI-2904). It is descriptive only.
* **Prior leagues are name-matched.** The arrival diff itself is id-joined and clean; the step that
  looks a player up in the Proballers corpus is not.
* **This document is a reconstruction.** The 2026-08-17 draft cannot be produced, so a reader cannot
  verify that the reconstructed sections match it. The recovered sections can be checked against the
  amendments; the reconstructed ones can only be judged on their own terms.

## Scripts

Every number in this document comes from one of these, all committed:

* `scripts/build_league_factors.py` — the estimator and the 22-cell factor table.
* `scripts/validate_translation_holdout.py` — the ATI-2799 held-out gate (n=231), source of the G1–G8
  results, the realised interval coverage, and the T1 population-change price.
* `scripts/validate_translation_walkforward.py` — the six-window walk-forward (n=719), source of every
  pooled contrast and of the RTM arms.
* `scripts/collect_import_signings.py` — the arrival diff, including the both-competition mode that
  produces the shape this document reads (committed 2026-08-25, ATI-2917; it did not exist when this
  section was first written). The committed 2026-08-21 artifact in `data/processed/signings/`
  predates it and was produced by an uncommitted session script. **The pre-lock collection has not
  been made**: EuroCup's 2026-27 rosters are still half-published upstream, and the collector's
  roster-plausibility guard has refused every attempt. The 110 (68 EuroLeague / 42 EuroCup) figure
  quoted in Amendment 2 therefore descends from a measurement that guard rejected, so 42 is a floor
  rather than a count. No bar in this document depends on it — §7 is a rule, not a number, and the
  binding population is the dated pre-lock collection.

## Provenance

| Item | Where it is fixed |
|---|---|
| The seven required elements | ATI-2891 |
| PARTIAL branch, `K_LAG` rule, coverage relabelling, B1b primary | `preregistration-2026-27-amendment-1-2026-08-21.md` |
| Combined arm, B1c, declared power, dated population rule | `preregistration-2026-27-amendment-2-2026-08-25.md` |
| G1–G8 results, realised coverage, T1 price | `translation-holdout-validation-2026-08-17.md` |
| Every pooled contrast and the RTM arms | `translation-walkforward-per-league-2026-08-21.md` |
| Unit, population, estimator, threat and limitation conventions | `translation-holdout-preregistration-2026-08-17.md` |
