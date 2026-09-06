# Pre-publication checklist for analysis

Derived from six errors made on 2026-08-10, three of which reached a committed
document. Every one was catchable before publishing.

**Scope:** any analysis whose numbers will be quoted — a research note, a Linear
issue, a claim in the Kremer brief, an answer in chat. If a number leaves the
scratchpad, this applies.

---

## The scoreboard that produced this

| Error | Caught by | When |
|---|---|---|
| "Stars lose more" was regression to the mean | own split-half control | **before publishing** |
| Assist join inflated 67,662 → 72,031 rows | an impossible printed number | **before publishing** |
| BSL TS% did not reproduce from raw | reviewer prompting | before it shipped |
| "Roles are a continuum" (wrong null + noisy sample) | **the user** | after publishing |
| Translation factors used an unjustified estimator | **the user** | after publishing |
| xPTS baseline pooled two competitions | same audit | after publishing |

The two self-caught cases share a structure: **the control existed before the
result did**, and **a printed quantity was impossible under correctness**.
Neither required insight in the moment.

---

## 1. Pre-register the threats, before running

Before writing analysis code, write the threat list at the top of the script:
not "what will I find" but **"what would make this wrong."** Then code a control
for each into the *same* script, so it runs whether or not you remember to look.

For this domain the recurring threats are:

- **Regression to the mean** — whenever groups are selected on a noisy variable.
  Control: split-half that replicates the *construction* (tier on one half,
  measure on the other), not just the data.
- **Part-whole artifacts** — the measured quantity is inside the outcome.
  Control: remove the component and re-measure.
- **Reliability floor** — a low correlation may mean "not persistent" or "not
  measurable". Control: within-sample split-half reliability, always reported
  next to any persistence figure.
- **System vs player** — does the trait survive a club/team change?
- **Survivorship** — who had to keep playing to enter the sample?
- **Denominator/unit** — is a "player-game" one row, or three across files?

## 2. A caveat must become a test, or the conclusion does not ship

**If you can write "X might be affecting this," you can test X.** Writing it as
a caveat and publishing anyway is the single highest-yield failure here: the
roles note contained the sentence *"at ≥10 games the extremes are low-minute
players whose rates are noise"* and died to exactly that.

Rule: every caveat in a draft is either (a) re-run without the suspect
condition, or (b) the conclusion is downgraded to "undetermined". A caveat is an
untested confound wearing a disclaimer.

## 3. Print the specification, not just the result

Most errors were **choices not noticed as choices**. Every analysis has a spec.
State it, and show one alternative for each line:

| Choice | Alternatives to print |
|---|---|
| **Estimator / weighting** | ratio-of-sums · exposure-weighted · mean-of-per-unit-ratios |
| **Null reference** | column-permutation · uniform box · PCA-aligned · none |
| **Sample filter** | the threshold, and the result one notch stricter |
| **Aggregation key** | every partition column — especially competition/season |
| **Unit** | what exactly is one row? |

**When two defensible choices disagree, the choice is load-bearing** and belongs
in the writeup. The translation factors moved from 0.902 to 0.939 on weighting
alone, which killed a headline claim.

## 4. Invariants that print

Cheap, mechanical, and they catch what reasoning misses. Add to every script:

- **Join rate** — assert it, do not eyeball it. `assert rate > 0.5`.
- **Row-count conservation** — an inner join that *grows* proves the key is not
  unique. This caught the missing `_competition` in one line.
- **Reconciliation** — derive a total two ways and compare
  (`2×fg_made + 3×fg3_made + ft_made == points`).
- **Calibration** — model mean vs actual mean (xPTS 1.086 vs 1.080).
- **Impossible values** — rates >1, negative counts, exact 0.500 AUC, exactly
  equal group means.

## 5. Symmetric scrutiny

**A negative result is an assertion and needs the same battery as a positive
one.** "There is no cluster structure" got one null; "assists travel worst" got
four controls. The bias runs toward waving through the claim that feels
conservative. It is not conservative — it is just a different claim.

## 6. What a confidence interval does not cover

A bootstrap CI covers **sampling error only**. It does not cover:

- estimator choice (published gap 0.074 [0.060, 0.088]; minutes-weighted 0.055,
  outside the interval)
- null choice
- sample-filter choice

If those are unexamined, the interval is narrower than the truth. Report a
sensitivity range alongside, or say the interval is conditional.

## 7. Pre-register POWER, not only threats

A reliability or correlation figure below a threshold has two readings: *the
effect is absent* or *the sample cannot see it*. Only one of them is a finding.

Before writing any negative claim, compute the achievable reliability at the
sample actually used. Spearman-Brown inverts cheaply: from an observed
split-half `r_obs` at `n_obs` observations per unit, per-observation reliability
is `r1 = r_obs / (n_obs - r_obs*(n_obs-1))`, and reliability at any other `n`
follows.

Worked case that produced this rule: pair synergy was reported as failing the
0.40 gate from a split-half run at 15 assists per arm. At that n the *achievable*
reliability was 0.211 — the gate could not have been cleared by any effect. The
honest claim was "not estimable at this sample size", with the requirement
stated: 38 assists per arm, which only 28 pairs in ten seasons of both
competitions reach.

Rule: **a null result carries a power line or it does not ship.** Phrase it as
"no detectable effect at n=X; reliability 0.40 requires n=Y".

Gate: `assert_powered_for_null(r_obs, n_obs, n_used)` raises when the ceiling is
below the threshold.

## 8. Never move a threshold to admit a failing run

If a fit or a metric lands just outside a gate, the permitted responses are: run
longer, pool to a coarser unit, reparameterise, or report the failure. Editing
the threshold — even by a rounding margin, even while calling the new value
"conventional" — invalidates every other gate in the analysis, because a reader
can no longer tell which thresholds were set before seeing results.

This is written from a violation: a convergence gate was loosened by exactly the
margin needed to pass a run that had failed it. Restoring the true threshold and
sampling longer earned the same conclusion honestly.

Corollary: **a gate must be shown to fail.** A gate that only ever passes is
indistinguishable from one that never checks. Every new gate gets a negative
control with an impossible threshold, and the negative control is part of the
verification record. `assert_gate_rejects` does this.

## 9. Covariate hygiene: outcome-conditioned and degenerate columns

Two failure modes that no amount of downstream care recovers from, because they
corrupt the model's inputs.

**Outcome-conditioned covariates.** The shots table's `FASTBREAK`,
`SECOND_CHANCE` and `POINTS_OFF_TURNOVER` flags are set on made shots at FG%
0.9996 — they are points-derived, not shot-context. Conditioning a shot-quality
model on them conditions on the outcome. Check: for every candidate flag, the
outcome rate among flagged rows. If it approaches 1, the column is a function of
the result. Gate: `assert_not_outcome_conditioned`.

The honest replacement is usually derivable: a transition flag built from the
second-resolution clock is defined on *misses* too (40.7% of flagged attempts),
which is exactly what the contaminated column could not do.

**Degenerate values.** Points per *assisted* shot is exactly 2 or 3, because an
assist only exists when the shot goes in. Any "assist quality" metric weighting
realised points therefore measures nothing but 3-point share. Value must come
from all attempts at a location, not from realised outcomes. Gate:
`assert_degenerate_value_absent`.

## 10. Unit inflation: when a better join is a worse one

Row-count conservation (§4) catches a join that grows. It does not catch a join
that grows *legitimately* while duplicating the events that derived units are
built from.

Signature: **more rows, fewer usable units.** Re-keying the assist join on a
seconds clock added 948 located assists (+0.7%) but pairs at 40+ assists fell
from 187 to 166. A duplicate check on the assist-event key found 23.2% of the
new rows duplicated a single assist versus 0% before. The rebuild was discarded.

Rule: after any re-key or join improvement, compare duplicate rate on the *event*
key and the count of derived units, not only total rows. If units shrink while
rows grow, the new rows are duplicates. Gate: `assert_units_not_inflated`.

## 11. Attribution: whose property is a residual?

An interaction term is the most inviting place for a main effect to hide. A pair,
lineup or interaction residual should not cluster on either constituent alone —
if it does, the marginals failed to absorb them.

Test: variance share of the residual by each constituent grouping, against a
permutation null at the same group sizes. Pair "synergy" clustered by SHOOTER at
0.373 against a null 95th percentile of 0.344, while passer (0.185) and
team-season (0.288) were within chance. Removing **both** constituents' means
dropped the reliability from 0.503 to 0.348 — that adjustment does not isolate
the shooter, so the evidence that the residual is *shooter* identity is the
permutation test above, not the reliability drop. A full-power role-level
decomposition then put it beyond doubt: 98.8% shooter, 0.2% passer, 1.9%
interaction.

Two supporting checks, both cheap: a residual that should be two-sided but is
87% positive is a systematic bias, not an effect; and an extreme case that
decomposes into a recognisable play type (a guard feeding a centre at the rim) is
structure, not chemistry. Gate: `residual_ownership`.

## 12. Magnitude in context, on one scale

An effect size alone is uninterpretable and easy to oversell. Report every effect
beside comparators **in the same unit**, and state what it is worth over a
realistic exposure.

Standing yardstick for this project, expected points per shot:

| quantity | 1 SD |
|---|---|
| Spread across court areas (rim 1.549 vs short mid-range 0.717) | **0.832** |
| Passer creation quality | 0.037 |
| Reliable pair-specific effect | 0.033 |

Choosing where a shot comes from matters ~25x more than who is paired with whom.
Creation quality's 0.037 is 4.8 points per season at the median 130 assists —
real, and small. Say so.

Figures obey the same rule: never place quantities from different scales on one
axis. A panel mixing log-rate SDs (0.186, 0.690) with points-per-shot values
(0.033, 0.037) made them look comparable when they are not. Gate:
`magnitude_in_context`.

## 13. Verify from the file, never from a printed table

A published claim that two players each held stable loadings across three clubs
was wrong for one of them — generalised from a truncated console print while the
data sat loaded in memory. Querying the artifact produced *better* examples than
the one that was wrong.

Rule: any identifier, count, or numeric value that enters prose is read back from
the saved artifact at the time of writing. Console output is for deciding the
next step, not for quoting.

## 14. A metric that survives its gates still needs its dependencies stated

Creation quality passed reliability (0.669), the mover test (86% retention), and
orthogonality to the obvious baselines — then turned out to correlate +0.655 with
the passer's *team* shot-location value. 43% of it is the roster.

That is not a failure of the metric; it is a property of it, and it changes how
the number may be used: comparing two passers on different rosters partly
compares their teammates. Before a metric is reused, ask what else it is a
function of, and test the most plausible candidate. Passing gates licenses the
number, not every interpretation of it.

## 15. Ground the prose, not only the numbers

Sections 1–14 check whether a *number* is right. They do not check whether the
*sentence about the number* is right, and that is where this project's errors
actually live.

Of five errors caught on 2026-08-11/12, **four were correct computations
described wrongly**:

| written | true |
|---|---|
| "assists sit one row **before** the made shot" | the code read the row before the *assist*; the feed logs the basket first |
| "Lessort and Fall each across **three** clubs" | Fall appears at two |
| "**every** helper verified" | eleven of twelve were run |
| "removing **shooter** means dropped reliability 0.503 → 0.348" | both constituents' means were removed; the permutation test is what identifies the shooter |

The last one propagated into five artifacts — including this document — because
prose was copied rather than re-derived from the code. None of the numeric gates
could see it: every number in the sentence was correct.

**Rule: a sentence that asserts a cause names the control that supports it.**

    Corner-3 creation retains only 54% across a club change [via: mover_test].

`[via: name]`, `[control: name]` and `[data: name]` are accepted. The syntax is
deliberately ugly so an uncited causal claim is visible in review.

`Analysis.conclude()` enforces this: it refuses a conclusion containing an
attributional sentence with no citation, or one citing a control that was never
registered. Purely descriptive sentences ("reliability is 0.669") need no
citation — reporting a quantity is not claiming a cause. `ungrounded_allowed`
exempts a claim restating someone else's published finding, and nothing else.

Two companion checks in `src/research/claims.py`:

- `assert_numbers_traceable` — a numeric literal in prose must match some value
  the analysis computed. A bag-of-values check: it catches a number that appears
  nowhere in the results.
- `assert_entity_claims` — checks the *(entity, value)* pair, which the above
  cannot: "Fall across 3 clubs" passes a bag-of-values check because some other
  player has 3.

**Per-entity claims belong in a table, one entity per row.** Building this check
established why. Prose naming several entities and several numbers is not
parseable — "Lessort and Zizic span five clubs each, Hall and Jones three, Fall
and Oturu two" is *correct* and an unscoped checker flagged it four times. A gate
that fails on true sentences gets switched off. So the checker adjudicates table
rows and single-entity sentences, and merely *reports* ambiguous prose for a
human to read. That is also exactly the fix applied to the offending report: the
prose generalisation was replaced by a table with per-player counts, which is
checkable against the data rather than against a previous sentence.

**Range and rank claims are the residual hole.** Two errors on 2026-08-12 passed
every check above: "assisted share 0.90 vs **0.29-0.52** elsewhere" when the true
maximum of that comparison set was 0.710, and a figure titled "corners rank
**top-2 on all three**" when one of the three designs ranked them 3rd and 4th.
Neither is an attribution, so §15's citation rule is silent; every literal in
both appears somewhere in the results, so `assert_numbers_traceable` is silent.
The error is in what the number is claimed to *summarise*, and both understate
the data in the flattering direction.

`assert_summary_claims` recomputes them from the set:

```python
assert_summary_claims([
    {"kind": "range", "stated": (0.294, 0.710), "values": share[~corner],
     "what": "non-corner assisted share"},
    {"kind": "rank", "stated": 4, "of": system_a, "subset": corner,
     "what": "corners on the mover test"},
])
```

Rule: **a range or rank in prose is recomputed from the set it summarises at the
time of writing** — never carried over from an earlier draft, and never widened
or narrowed to fit the sentence. A figure title asserting a rank is the same
claim and gets the same check (§1.4 of the figure rules already requires the
title be true of every category on the axis).

**Corollary to §13.** "Verify from the file, never from a printed table" covers
values. Extend it to attributions: *which control produced this number* is a
checkable claim about the code, and it must be checked against the code, not
against a previous sentence describing the code.

## 16. A published number must come from a committed generator

On 2026-08-18 a role-features note opened: *"Every number here was measured on
the corpus on disk by `scripts/build_pbp_role_features.py` and
`scripts/build_lineup_features.py`."* Its headline table — the `0.581 → 0.915`
that was the entire case for changing the production role basis — is computed by
neither. `grep -rn adjusted_rand scripts/` returns nothing.

Three things in that one note were declared and never executed: an
`assert_not_outcome_conditioned` import that is never called, `gate_novelty`
(Gate C, one of the three gates the feature selection rests on) defined and
never called, and the bootstrap harness absent entirely. sklearn's only
appearance in the file is inside the uncalled function. All of it reads as
rigorous; none of it runs.

The earlier note in the same line was worse, and said so — it closes with a
`## Scripts` section reading `Scratchpad:` and naming three generators. All
three are now gone, including the one that built a feature basis the later note
depends on. That is why the later table cannot be reproduced today at any price:
the missing input is the output of a script a committed document recorded as
disposable.

Rule: **a number that enters a committed document is produced by code committed
in the same change.** Not a notebook, not a scratchpad file, not a REPL. If the
analysis was exploratory, the generator still lands — a script that reruns and
prints the table is the minimum, and it is cheap beside re-deriving a lost
basis. A note may name a generator it does not own (another repo, a one-off
probe), but then it may not quote that generator's numbers as measured.

**Corollary: a function defined and never called is indistinguishable from one
that runs.** Before citing a gate, grep for its *call site*, not its definition.
§2 requires a caveat to become a test; this requires a method to become a call.

**Enforced** by `tests/test_docs/test_research_notes_have_committed_generators.py`,
which refuses a new note that declares its generators as scratchpad. It cannot
verify that every quoted number is reproducible — nothing can — so it refuses the
*admission* instead, which is the form the failure has actually taken here three
times.

---

## 17. A verification claim is a claim about an environment

Sections 1-16 govern numbers and the sentences about them. This one governs the
sentence *"verified"* — because a check inherits the trust of the environment it
ran in, and that environment is rarely stated.

**The measured case.** cv_basketball PR #87 stated "2183 tests pass", with the
pre-existing failures separated out by re-running on a stashed clean tree. Both
halves were true on the machine that ran them. CI went red on three tests anyway:
`scripts/generate_model_manifest.py` reads an ONNX graph's external-data location
via `import onnx`; `onnx` was declared only in the `train` extra; CI installs
`uv sync --extra dev`. The author's `.venv` had `train` synced from earlier work,
so the suite could not fail there no matter how many times it was re-run. Stashing
the diff varied the *code* and held the *environment* fixed — and the environment
was the variable.

Rule: **when a claim is "it passes", the environment is part of the claim.** State
which one, and make it the environment that will judge the work, not the one you
happen to be sitting in. Re-running the same command in the same shell is
repetition, not replication; it raises confidence in nothing except that the
command is deterministic.

The generalisation beyond dependency extras: anything a development machine
accumulates and a fresh one does not — installed packages, fetched LFS content,
extracted frames under a gitignored path, a cached artifact, an exported
environment variable — is a hidden term in every green run. Before "verified",
ask which of those the check is standing on, and whether the judge has it.

**And the failure this one hid is worth its own rule.** `_external_weights`
wrapped its graph read in `except Exception: pass` with a fallback to the sibling
`<stem>.onnx.data` name. That fallback is correct for "this graph records no
external data" and wrong for "I could not read this graph" — and `ImportError` is
an `Exception` like any other, so a missing package silently became a confident
wrong path, and a perfectly loadable model was recorded as having **no weights**.
That is the exact defect the module was written to fix, reintroduced through its
own error handler.

Rule: **a fallback must not merge "nothing to find" with "could not look".** The
two justify different downstream behaviour, and a catch broad enough to cover the
second while claiming the first is how an unavailable input turns into a published
value. This is §2's logic applied to code, and §16's one layer down: there a
method was defined and never called; here a failure path was caught and never
distinguished. An unhandled condition wearing a `try` is still an unhandled
condition.

## 18. Record only what the artifact can answer

Sections 16 and 17 police how a claim was produced and where it was checked. This
one polices the claim's *subject*: whether the thing being recorded is knowable
from the material in front of the observer at all.

**The measured case.** A court-labelling campaign asked an operator to place
"keypoint 0 — LEFT end, LOWER sideline on screen" on a broadcast frame. The
sideline half is answerable: it was verified in 100% of sampled poses. The end
half is not. It means court x=0, and **no single frame establishes which end of
the court it shows** — the two ends are near mirror images and the camera does
not say which it is pointed at. The operator was being asked to assert something
the picture cannot settle, and reported exactly that: *"I don't understand what
each label means in the video I see."*

What happened next is the part worth keeping. The pre-fill that seeded the corpus
resolved the unanswerable question by **defaulting** it: all 51 corners were filed
at the left end and none at the right. It also got a second, answerable property
wrong in the majority of frames while nobody was checking. The error class is
worth 14-28 m of court, and it was invisible because a defaulted value looks
exactly like a determined one once written down.

Rule: **record only what the observer can verify from the artifact. A fact the
artifact cannot establish is deferred, never defaulted.** Deferring is cheap — a
later stage with more evidence can resolve it, and in this case a declared
per-broadcast bit does. A default is expensive precisely because it is invisible:
it enters the record at full confidence and nothing downstream can tell it apart
from a measurement.

**The corollary, and without it the rule rots into an excuse.** The obligation is
to look for a determinant *first*. Deferring is what you do after you have failed
to determine, not instead of trying. In the same corpus I ruled that 25
single-corner frames could not be resolved, because the corner's own position
spans nearly the full frame width and settles nothing. That ruling was wrong for
three of them: they contain a halfway-line crossing, the halfway line is exactly
14 m from either baseline, and the arithmetic settles the end. A second look
found a determinant where the first had declared none.

So the sequence is: try to determine; if you cannot, say so in the record itself;
never fill the gap with the most likely value. And when a design must express
"undetermined", give it a representation — a null with a stated reason, a refusal,
a separate field. A schema with nowhere to say "I could not tell" *forces* the
default, and then the defect is in the schema rather than in the person.

**Corollary to §16.** A committed generator is not enough if what it generates
includes a guess. The seeding script here was uncommitted *and* defaulting; the
fix was both to commit it and to make it record 22 of 51 corners as undetermined
rather than inventing an answer for them.

---

## The gate

**Do not write the conclusion paragraph until the sensitivity table exists.**

Writing the claim first makes every subsequent check a threat to work already
done. Running the checks first makes them the input to what the claim should be.

## The guard — this is enforced, not advised

`src/research` implements the rules above as code that raises, and
`tests/test_docs/test_research_notes_have_method_block.py` makes the output
mandatory: **a research note without a `## Specification` block fails the guard
lane.** The grandfather list covers notes predating the guard and may only
shrink.

```python
from src.research import Analysis

an = Analysis(
    question="Do assists translate worse than other box stats?",
    unit="one player-season with >=8 games in BOTH a continental and a domestic league",
    threats=["estimator_choice", "name_collision", "survivorship", "sample_filter"],
)
an.spec(estimator="exposure-weighted", null="n/a (paired design)",
        sample_filter=">=8 games each side", key="player_name + season")

an.check_join_frames("pairs", left=cont, joined=pairs)   # raises on fan-out
an.estimate("assist_factor", {                            # requires >=2
    "ratio_of_sums": ..., "exposure_weighted": ..., "mean_of_ratios": ...,
}, ci_halfwidth=hw)                                       # flags LOAD-BEARING

an.caveat("the >=8 game threshold may admit noisy seasons")
an.caveat_tested("the >=8 game threshold may admit noisy seasons",
                 result="re-ran at >=15: 0.867 vs 0.881, unchanged")

print(an.report())      # raises unless every threat and caveat is closed
an.conclude("...", direction="effect")   # 'null' demands >=2 null references
```

What it refuses: an unaddressed declared threat, an untested caveat, a
single-estimator quantity, a "no effect" claim on fewer than two null
references, a conclusion written before a report, a join that grows, and
hand-closing a threat that has a computable helper.

**`caveat()` is for a testable confound, not a scope limit.** "The tails may be
noisy" is a caveat — re-run without them. "Not pace-adjusted, because we have no
pace data" is a *limitation*: it belongs in prose, because opening it as a
caveat creates an obligation nothing can discharge. Confusing the two turns the
guard into an obstacle instead of a check.

**Adoption proof.** `dual-tier-per-stat-translation-2026-08-10.md` is ported. Its
block flags **all three** factors LOAD-BEARING — the estimator spread exceeds the
bootstrap interval for every stat. Run on the first pass, that line is what would
have stopped the wrong headline.

That note is also the sharpest illustration of what this guard does *not* cover,
which is why it keeps its place here rather than being swapped for a cleaner
example. Its specification block is exemplary and every threat is closed — and
its four generators were never committed and are now gone (§16, ATI-2913). A
note can pass every check on this page and still be unreproducible, because
these checks read what the note *says*, not what produced it. §16 is the only
one that looks at the code, and it can only refuse a silent omission.

## Applying corrections

When a published number is wrong: correct it **in place with the retraction
visible**, rename the file if its name asserts the wrong thing, and update every
downstream artifact — Linear issue, brief, memory. A correction that leaves the
original claim reachable has not been made.
