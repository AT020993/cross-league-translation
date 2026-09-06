# Does per-league resolution buy anything? Walk-forward re-test — RESULT

**Answer: yes. ATI-2799's null was a power limit, not a property of the estimator.** Ticket: ATI-2891
(pre-registration revision). Prerequisite: ATI-2799, whose PARTIAL verdict stands unchanged.

## Specification

| Choice | This analysis | Alternatives printed |
|---|---|---|
| **Unit** | one (player, destination season) transfer into EuroLeague/EuroCup, >=8 games each side | — |
| **Population** | consecutive-season switchers-in, poland-plk refused, non-positive rates dropped | — |
| **Design** | walk-forward: for season *S*, factors **and** the level correction refit on seasons strictly `< S` | single held-out window (ATI-2799, n=231) |
| **Comparator** | one global exposure-weighted scalar from the same fit; **and a league-free regression-to-the-mean model** (added 2026-08-25, see the addendum) | untranslated B0; shuffled per-league assignment |
| **Level correction** | median realised ratio on prior cohorts only | K = 1 (no correction) |
| **Uncertainty** | paired cluster bootstrap on destination club-season, 4,000 draws, seed 0 | — |
| **Falsifier** | shuffled league→multiplier assignment, 200 reps | — |

**Reproducibility.** `scripts/validate_translation_walkforward.py`, run from repo defaults, prints
every figure below. The shuffled-factor control is an in-script `assert`, so the run fails rather
than reports if the null is ever matched.

---

## Why this was re-tested

ATI-2799 measured per-league factors against one global scalar on a single held-out window and could
not separate them: **+0.056 MAE, CI [-0.134, +0.246]**, n = 231. That was reported as "the 22-cell
table buys nothing measurable over one scalar," and it drove a recommendation to pre-register only a
global level plus the per-league *ordering*.

One window at n = 231 is thin for a difference of that size. The estimator is refittable at any
season boundary, so the question is answerable with more independent windows rather than more
assumptions.

## Design

For each destination season *S* in 2020–2025: refit the factor table on pairs from seasons strictly
before *S*, refit the level correction on newcomer cohorts strictly before *S*, then score *S*.
Nothing from *S* or later touches either fit. Six windows, no season informing its own prediction.

![walk-forward result]({{artifact:art_e7b53f1c-1319-40c8-8f8e-79441239ee40}})

## Result

| Season | n | K | Per-league MAE | One global MAE | B0 MAE | Delta | 95% CI | Separable |
|---|---|---|---|---|---|---|---|---|
| 2020 | 142 | 0.9368 | 3.5006 | 3.6689 | 4.2985 | +0.1683 | [+0.0241, +0.3323] | yes |
| 2021 | 112 | 0.9309 | 2.8949 | 3.1817 | 4.1891 | +0.2868 | [+0.1353, +0.4849] | yes |
| 2022 | 118 | 0.9285 | 2.8552 | 3.2923 | 3.2612 | +0.4371 | [+0.2460, +0.6176] | yes |
| 2023 | 116 | 0.9305 | 3.2310 | 3.4911 | 3.9135 | +0.2601 | [+0.0454, +0.4805] | yes |
| 2024 | 113 | 0.9313 | 2.7802 | 2.8794 | 3.8943 | +0.0992 | [-0.1124, +0.3668] | **no** |
| 2025 | 118 | 0.9304 | 3.5146 | 3.7603 | 4.1891 | +0.2458 | [+0.0719, +0.4270] | yes |

**Per-league resolution wins in 6 of 6 seasons** (sign test p = 0.0156) and the gap is
bootstrap-separable in **5 of 6**. Pooled across all six windows, n = 719 transfers in 203
destination club-season clusters:

| | MAE | R² |
|---|---|---|
| 22 per-league factors | **3.1459** | **+0.3597** |
| one global scalar | 3.3934 | +0.2682 |
| untranslated (B0) | 3.9676 | −0.0202 |

*R² provenance (2026-09-04, ATI-2955).* When this note was written the script computed MAE only;
the R² column came from a session. `scripts/validate_translation_walkforward.py` now writes R² per
arm to `walkforward_summary.json: pooled.r2` (definition: `validate_translation_holdout.metrics`,
the same one the holdout gate uses), and the re-run on the Proballers corpus
(`--continental-source proballers`) reproduces every value above to four decimals; the B0 cell,
left blank in August, is filled from the same run. Read beside its ceiling, per pre-registration
§6: the Spearman-Brown ceiling on out-of-sample R² at the scored rows' mean destination exposure
(16.8 games) is **0.671** (`pooled.ceiling.ceiling_r2_at_mean_games`; destination split-half
r = 0.537 on 5,397 units), so the combined arm's +0.4227 is 63% of what the outcome's own
reliability allows.

* per-league vs one global scalar: **+0.2475, CI [+0.1701, +0.3283]** — excludes zero
* per-league vs B0: **+0.8217, CI [+0.6072, +1.0335]**

## The two controls, which is where this could have failed

**1. Is the gain the league mapping, or just dispersion in the multipliers?** Permuting the
league→multiplier assignment within each season, 200 reps: mean delta **-0.0881**, 95th percentile
**-0.0291**, and **0 of 200** shuffled draws reach the observed +0.2475. Shuffled factors are *worse*
than one global scalar. The gain is the mapping, not the spread.

**2. Does the gain depend on the level correction?** Re-running with K = 1 throughout:
**+0.1527, CI [+0.0662, +0.2464]** — still separable. The level correction improves absolute accuracy
(pooled MAE 3.3934 → 3.1459) but is **not** what creates the per-league advantage. This matters: it
means the finding is not an artifact of introducing a term ATI-2799 did not use.

## What ATI-2799 got right, and what it got wrong

**Right:** on its own single window the difference genuinely was not separable. The number was
correct and the confidence interval was honest.

**Wrong:** the interpretation. "Not separable at n = 231" was read as "buys nothing." Six independent
windows at comparable per-season n separate it cleanly, and 2024 — the season that fails here — is
the one closest to ATI-2799's window. **2024 is not a counter-example; it is the same power limit
reproduced.** Every season points the same way.

## Limitations, stated as limitations

1. **Within one season, this is still not measurable.** Every window has n ≈ 115–142, and one of six
   fails to separate. Any claim resting on a single season's transfers is underpowered — including
   the 2026-27 prospective set, which will be ~79 players. The pooled result is the claim; a
   one-season confirmation is not available and should not be promised.
2. **The level correction is refit, not fixed.** K ranged 0.9285–0.9368 across six independent fits —
   stable, but the locked pre-registration value of **0.9473 sits outside that range** and was fitted
   on 2016–2025, which includes the seasons ATI-2799 held out. Any prospective use should refit K on
   prior seasons only.
3. **This does not overturn the ATI-2799 gate.** G4 failed as specified, on the specified
   comparison, and nothing here re-scores it. What this changes is the *scope of the prospective
   claim*, not the retrospective verdict.
4. **Destination-level factors, not per-league, are the fallback.** Two per-destination tier means
   sit between the two extremes (pooled MAE 3.2352). If per-league resolution ever has to be dropped,
   that is the next rung, not one global number.
5. **poland-plk remains refused** and nothing here licenses a claim about it.

## What this licenses

**Supported:** per-league factors predict better than any single scalar, out-of-sample, on 719
transfers across six independent windows, and the advantage is attributable to the league mapping.

**Not supported:** that the advantage is detectable within any one season; that the locked K = 0.9473
is the right constant; any change to the ATI-2799 verdict.

## Recommendation to ATI-2891

**Keep the 22-cell per-league table as the prospective prediction basis.** The earlier recommendation
— pre-register the ordering plus one global level — was drawn from the single-window null and is
withdrawn. Pre-register per-league point predictions, with the level correction refit on seasons
strictly before 2026-27, and state explicitly that the ~79-player prospective set is powered to
confirm the *pooled* effect only.


---

## Addendum 2026-08-25 — the comparator this note originally lacked

*Added after the fact. The measurements above are unchanged and reproduce exactly;
what changes is which of them can carry a published claim.*

This note compared 22 per-league factors against **one global scalar**. That is
the wrong baseline. Only about **4% of the variance in realised translation
ratios is between leagues** — 96% is player-to-player within a league — so the
honest comparator is a model that predicts regression to the mean from a player's
own history and uses **no league information at all**.

*Correction 2026-09-05, no value in the tables changed.* The 4% was measured on the
Proballers-destination corpus. On the API-destination corpus the lock uses it is **8.7% on the
same-season pairs and 14.5% on the scored transfers** (`translation-propositions-2026-09-04.md`,
P1, committed generator `scripts/instantiate_translation_propositions.py`). The qualitative claim
— most of the variance is within a league — stands; the number to quote is the current one.

Added as a fourth and fifth arm to `scripts/validate_translation_walkforward.py`,
fitted on the identical walk-forward folds (RTM coefficients, factor table and
level correction all refit on seasons strictly before each scored season):

| arm | MAE | R² |
|---|---|---|
| untranslated (B0) | 3.9676 | −0.0202 |
| one global scalar | 3.3934 | +0.2682 |
| 22 per-league factors | 3.1459 | +0.3597 |
| RTM only, no league identity | 3.1616 | +0.3537 |
| **RTM + per-league** | **2.9550** | **+0.4227** |

*(R² column reproduced 2026-09-04 by the committed generator, ceiling 0.671 — see the provenance
note under the Result table.)*

Paired cluster bootstrap on destination club-season, n = 719 in 203 clusters:

| contrast | delta | 95% CI | |
|---|---|---|---|
| per-league vs one global scalar | +0.2475 | [+0.1701, +0.3283] | separates |
| **per-league vs RTM** | **+0.0157** | **[−0.1051, +0.1361]** | **tie** |
| RTM + per-league vs RTM | +0.2066 | [+0.1393, +0.2786] | separates |
| RTM + per-league vs per-league | +0.1909 | [+0.0958, +0.2876] | separates |

**What this changes.** The +0.2475 headline above is real, but it is measured
against a comparator that carries no player information. Against RTM the 22-cell
table does **not** separate. A referee who runs that arm — and it is the obvious
arm to run, given the 4% figure — would find the central claim of this note
unsupported as stated.

**What survives is stronger.** League identity and regression to the mean are
complementary, not competing: the combined arm beats each alone, both intervals
excluding zero. The defensible claim is therefore *league identity carries real
transferable signal, but roughly half the recoverable signal is regression to the
mean, so league adjustment used alone double-counts a player's career year.*

**Falsification, both new controls in-script as asserts.** Permuting the
league→multiplier assignment and **refitting** the combined arm: 200 reps, real
gain +0.2066, shuffled mean +0.0119, p95 +0.0329, **0 reps reaching the real
gain**. So the joint gain is the mapping, not the extra degree of freedom. The
original shuffled control also still holds (mean −0.0881, p95 −0.0291, 0/200).

**Status.** The RTM arm is **not pre-registered** — it was added to a shipped
analysis after seeing its result. It is now a scripted, tested, asserted arm
rather than a session finding, but Amendment 1's basis paragraph should record
that per-league resolution was tested against RTM and **holds only jointly**.
Per-league is not withdrawn; its justification changes.

---

## Addendum 2026-09-04 — the destination side moved to the EuroLeague API (Amendment 4)

*Nothing above is re-scored. Every number in this note was measured with the
Proballers copy of EuroLeague/EuroCup on the destination side, and
`scripts/validate_translation_walkforward.py --continental-source proballers`
reproduces it.* Since Amendment 4 (ATI-2957) the script's default reads the
destination side from the league's API, whose 2025-26 season is complete where
the Proballers copy held roughly half of it. The walk-forward re-run on that
corpus — including the 2025 window now sitting on a complete destination season
— is recorded in `translation-refit-api-destination-2026-09-04.md`, beside this
one, not in place of it.
