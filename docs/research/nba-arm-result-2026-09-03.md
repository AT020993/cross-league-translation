# The NBA arm — RESULT: P1 failed as pre-registered, and what survives every cut

**Date:** 2026-09-03 · **Ticket:** ATI-2958 (for ATI-2807) · **Pre-registration:** `preregistration-nba-arm-2026-09-03.md`, committed at 23:30 local before any NBA statistic was fetched · **Generator:** `scripts/build_nba_arm.py` (inputs from `scripts/fetch_nba_player_seasons.py`)

**Verdict.** P1(b) — that a direction multiplier combined with the player's own history beats each alone — **fails**: the combination beats the multiplier but not the history (pooled Δ −0.20, CI [−0.57, +0.17], at a detection floor of 0.52). P1(a) holds: the multiplier alone does not beat history alone (history wins by +0.59, CI [+0.14, +1.05]). G1 fails. The pre-registration says a wrong prediction is reported and scored anyway; this is that report.

**What survives every estimator and both directions.** On EuroLeague↔NBA moves, the player's own multi-season mean is at least as good a predictor of his next season as a league multiplier applied to his last season, and the multiplier's error is concentrated exactly where the paper's thesis says it should be: for players coming off a season above their own average the multiplier over-predicts by **+3.99 EFF/36**, against **+0.68** for everyone else [data: T1]. In the scouting direction (EuroLeague → NBA), the combination is the best arm and beats history alone (+0.34, CI [+0.13, +0.58]) [via: T3].

**What does not survive.** The pooled headline "a multiplier is worse than no translation" (−0.52, CI [−0.96, −0.09]) holds under exposure weighting and mean-of-ratios and **vanishes under ratio-of-sums** (−0.08, CI [−0.39, +0.22]) [via: T6 scored]. It is a weighting artifact on a noisy NBA→EL sample, and it is not a claim of this note.

## Specification

**Question:** On real EuroLeague↔NBA moves, does a league multiplier alone beat a league-free regression-to-the-mean model, and does adding the player's own history to the multiplier beat each?

**Unit:** one (player, move): EuroLeague season *t* (≥8 games) → NBA *t+1* (≥8 games), or NBA *t−1* → EuroLeague *t*; seasons by start year on both sides (asserted on Vezenkov: EL 2022, NBA 2023, EL 2024).

| slot | value | alternative printed |
|---|---|---|
| population | EuroLeague first-party API tree 2016–2025; NBA stats endpoints regular season 2015–2025; identity = normalised name **and** birth year from two first-party bio sources | name only (rejected) |
| metric | per-36 EFF from components, both sides | per-possession: **not run** (the totals endpoint carries no possessions) |
| estimator | exposure-weighted direction factor on prior moves | ratio of sums, mean of ratios — **load-bearing**, see T6 |
| design | walk-forward by destination season 2018–2025; direction factor, level and RTM weight refit on moves with strictly earlier destination season, ≥10 prior moves per direction | — |
| arms | B0 untranslated · B1b source × direction constant · B1c the player's prior source-league mean (≥2 seasons; else B1b path, flagged R-H) · M constant × (w·source + (1−w)·prior mean), w on a 0.05 grid by MAE on prior moves | — |
| uncertainty | paired cluster bootstrap on destination team-season, 4,000 draws, seed 0 | — |

## Population

| step | count |
|---|---:|
| NBA players sharing a normalised name with a EuroLeague player | 293 |
| EuroLeague birth date missing (bios cover the `/people` roster) | 17 |
| birth year disagrees (the EuroLeague "Devin Booker" is not the NBA one, and one more) | 2 |
| **identities confirmed** | **274** (R-ID 19) |
| **moves at ≥8 games both sides** | **171**: NBA→EL 124, EL→NBA 47 |
| with ≥2 prior source seasons (B1c/M path) | 82 |
| scored in the walk-forward (≥10 prior moves in the direction) | 141 across 2018–2025, 110 clusters |

Direction factors refit each season: EL→NBA 0.876 → 0.896; NBA→EL 1.289 → 1.187, sliding as the early 30-move windows are diluted. Full-sample factors by estimator (T6): EL→NBA 0.898 / 0.895 / 0.918; NBA→EL **1.169 / 1.100 / 1.204** — a 0.10 spread on the NBA→EL side, ten times any domestic cell.

## Results, pooled (n = 141)

| arm | MAE | RMSE | R² | bias |
|---|---:|---:|---:|---:|
| B0 untranslated | 3.761 | 4.956 | −0.130 | −0.55 |
| B1b multiplier | 4.279 | 5.375 | −0.329 | **+1.47** |
| B1c own history | **3.686** | 4.683 | −0.009 | −0.36 |
| M combined | 3.886 | 5.042 | −0.170 | +1.24 |

| contrast (MAE saved by the first) | Δ | 95% CI | separates |
|---|---:|---|---|
| B1b vs B0 | −0.518 | [−0.959, −0.088] | yes, the wrong way — **but see T6** |
| M vs B0 (G1) | −0.125 | [−0.675, +0.417] | no → **G1 FAIL** |
| B1c vs B1b (P1a) | +0.593 | [+0.138, +1.051] | yes → **P1(a) holds** |
| M vs B1b | +0.393 | [+0.034, +0.752] | yes |
| M vs B1c (P1b) | −0.199 | [−0.574, +0.171] | no → **P1(b) FAILS**; detectable Δ at 80% power is 0.52, so this contrast cannot see an effect of the size in question [via: T9] |

Every R² is negative: no arm explains variance in the realised rate on this population. The move population is the confounded one by construction (T1), and these are per-36 rates on NBA minutes that are often small.

## T3 — per direction, never averaged

| contrast | EL→NBA (n = 37) | NBA→EL (n = 104) |
|---|---|---|
| MAE B0 / B1b / B1c / M | 3.97 / 3.53 / 3.65 / **3.31** | **3.69** / 4.55 / 3.70 / 4.09 |
| B1b vs B0 | +0.45 [−0.10, +0.98] | **−0.86 [−1.39, −0.30]** |
| B1c vs B1b | −0.12 [−0.75, +0.44] | **+0.85 [+0.29, +1.43]** |
| M vs B1b | +0.22 [−0.43, +0.82] | **+0.46 [+0.04, +0.87]** |
| M vs B1c | **+0.34 [+0.13, +0.58]** | −0.39 [−0.86, +0.11] |

Two different stories. **Scouting direction (EL→NBA):** the multiplier helps and the combination is the best arm, beating history alone with an interval that excludes zero; the other contrasts do not separate at n = 37. **Return direction (NBA→EL):** the multiplier hurts, history beats it, and the combination recovers about half the damage. The pooled verdict is 74% the second story.

## T6 — the pooled "worse than nothing" is estimator-dependent

| estimator for the direction constant | B0 | B1b | B1c | M | B1b vs B0 |
|---|---:|---:|---:|---:|---|
| exposure-weighted (primary) | 3.761 | 4.279 | 3.686 | 3.886 | −0.52 [−0.96, −0.09] |
| **ratio of sums** | 3.761 | 3.846 | 3.594 | **3.554** | −0.08 [−0.39, +0.22] |
| mean of ratios | 3.761 | 4.564 | 3.726 | 4.179 | −0.80 [−1.33, −0.30] |

Under ratio of sums the multiplier ties B0 and the combination becomes the best arm. The estimator spread exceeds every contrast in the pooled table, so **estimator choice is load-bearing and the pooled B1b-vs-B0 verdict is not reported as a finding** (METHOD.md §3, §6). What holds under all three: B1c ≥ B1b, and M ≥ B1b.

## T1 — where the multiplier's error lives (pre-registered descriptive)

| source season vs the player's own prior mean | n | bias, multiplier B1b | bias, combined M |
|---|---:|---:|---:|
| above own prior mean (career year) | 47 | **+3.99** | +1.61 |
| at or below | 35 | +0.68 | +2.95 |

The multiplier over-predicts a player coming off a career year by four points of EFF/36 and everyone else by less than one. That is the double-counting the paper describes, measured on NBA moves. The combined arm halves it for career-year players and pays for it on the others, which is what a single shrinkage weight on a 30-to-140-move fit looks like.

## Post-hoc, labelled — is the multiplier regression to the mean in disguise?

Refit the direction ratio with the player's **prior-season mean** as the source instead of his last season (players with ≥2 prior seasons):

| direction | n | ratio on last season | ratio on prior mean | CI |
|---|---:|---:|---:|---|
| EL→NBA | 14 | 0.831 | 0.907 | [0.831, 1.005] |
| NBA→EL | 68 | 1.102 | **1.114** | [1.057, 1.171] |

**No.** The NBA→EL level shift is about +11% and survives removing the last-season selection; it is a real difference in what these players produce in the two leagues, not only regression. The EL→NBA ratio moves toward 1 but n = 14. The thesis is *both*, not *either*: the multiplier is real, and applied to a career year it double-counts.

## Other pre-registered controls

| # | control | result |
|---|---|---|
| T4 | ≥15 games each side (n = 92): B0 3.34 / B1b 3.88 / B1c **3.04** / M 3.22; ≥100 minutes (n = 123): 3.37 / 4.06 / 3.43 / 3.64 | ordering unchanged |
| T7 | age at destination < 27 (n = 68): B0 best 3.66; ≥ 27 (n = 73): **B1c best 3.29** | history beats everything for veterans; nothing beats the raw rate for the young — consistent with development the RTM term cannot see |
| T8 | swapped direction constants: MAE 4.94 vs 4.28 | negative control fires |
| T8b | 200 permutations of prior histories: real gain +0.39, null mean −0.06, p95 +0.30, **5 of 200 reach the real gain** | the history term's contribution is the player's own history, p ≈ 0.025 |
| T9 | paired-difference SE 0.185; detectable ΔMAE at 80% power **0.52** at n = 141 | every null above carries this floor |
| T10 | Vezenkov EL [2017–2022, 2024, 2025], NBA [2023] | season-label convention agrees (one Sacramento season, correct) |
| P2 | domestic(*t−1*) → EL(*t*) → NBA(*t+1*), n = 29: chained MAE 3.74; domestic rate untranslated 5.20; EuroLeague season × factor 3.53 | the chain beats the raw domestic rate and does not beat using the EuroLeague season directly; **table, not claim** (`p2_chain.csv`) |
| T5 | per-possession | **not run** — the endpoint used carries no possessions; a limitation of this run |

## Limitations

- The move population is selected by construction; nothing here removes that, and the note does not claim to.
- NBA per-36 rates for movers rest on small minutes; the ≥100-minute cut keeps 123 of 141 and does not change the ordering.
- G-League and two-way seasons are excluded by the ≥8 NBA games floor only where they left no NBA line; a player with 8 NBA games and 40 G-League games is scored on the 8.
- 17 EuroLeague players have no first-party birth date and were refused rather than name-matched.

## What this licenses

- **Supported:** on EuroLeague↔NBA moves, the player's own multi-season mean is at least as good as a direction multiplier on his last season, under every estimator and in both directions [via: T3, T6]; the multiplier's error concentrates on career-year players (+3.99 vs +0.68) [data: T1]; in the scouting direction the combination beats history alone [via: T3].
- **Not supported:** that a multiplier is worse than no translation (estimator-dependent); that the combination beats history pooled (underpowered, CI spans 0); that the NBA→EL multiplier is pure regression to the mean (it is not: +11% survives).
- **Failed as pre-registered:** P1(b) and G1. Reported, not re-scored.

## Scripts

`scripts/fetch_nba_player_seasons.py` (NBA rows land gitignored; never committed — NBA.com ToU §9) and `scripts/build_nba_arm.py`, which prints every number above and writes `nba_arm_summary.json`, `nba_arm_scored.parquet`, `nba_moves.parquet` and `p2_chain.csv`. **Committed copy of the summary (added 2026-09-06):** `docs/research/artifacts/nba-arm-2026-09-03/nba_arm_summary.json` — re-run 2026-09-06 to a committed path because the 2026-09-03 run wrote to a scratch directory that no longer exists; P1 FAIL, B1c vs B1b +0.593 [+0.138, +1.051], M vs B1c −0.199 [−0.574, +0.171], T1 +3.99 / +0.68, EL→NBA M vs B1c +0.337 [+0.130, +0.581], T9 detectable Δ 0.518 — every figure above reproduces. The per-player parquets stay uncommitted (NBA rows).

## Conclusion

The pre-registered prediction that combining a league multiplier with a player's own history would beat each alone failed on EuroLeague↔NBA moves [via: P1]. What held is narrower and more useful: the player's own history is never worse than the multiplier [via: T3, T6], the multiplier's error is four times larger for players coming off a career year [data: T1], and in the direction a scout cares about the combination is the best arm [via: T3]. The multiplier itself is real — an NBA→EuroLeague level shift of about eleven percent survives removing the career-year selection [via: posthoc] — which is why applying it to a career year double-counts.
