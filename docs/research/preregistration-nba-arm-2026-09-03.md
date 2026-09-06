# PRE-REGISTRATION — the NBA arm: EuroLeague ↔ NBA moves

**Date: 2026-09-03. Ticket: ATI-2958 (for ATI-2807, the SSAC27 abstract). Status: committed BEFORE any NBA statistic was fetched.** The only NBA fields read before this commit are player names and first/last active years (`commonallplayers`), used to count candidates. The git timestamp of this file precedes the fetch script's first run; both are in the same branch.

## Specification

| Choice | This pre-registration | Alternatives considered |
|---|---|---|
| **Question** | On real moves between EuroLeague and the NBA, does a league multiplier alone beat a league-free regression-to-the-mean model, and does adding the player's own history to the multiplier beat each? | per-league NBA factors (rejected: n forbids); a dual-participation design (does not exist — nobody plays both in one season) |
| **Unit** | one (player, move): a EuroLeague season *t* with ≥8 games and an NBA season *t+1* with ≥8 games (**EL→NBA**), or an NBA season *t−1* with ≥8 games and a EuroLeague season *t* with ≥8 games (**NBA→EL**). Seasons labelled by start year on both sides (NBA 2024-25 = 2024 = EuroLeague 2024-25) | ≥15 games each side (sensitivity T4); ≥100 minutes each side (sensitivity T4) |
| **Population** | EuroLeague side from the first-party API tree, seasons 2016–2025 (EFF from components, per `continental-source-check-2026-09-03.md`); NBA side from the NBA's stats endpoints, regular season, seasons 2015–2025. Identity = normalised name **and** birth year agree across the two first-party bio sources; otherwise refused (R-ID) | name only (rejected: the EuroLeague "Devin Booker" is not the NBA one) |
| **Metric** | per-36 EFF: PTS+REB+AST+STL+BLK − missed FG − missed FT − TOV, computed from components on both sides | per-possession EFF (sensitivity T5, pace differs ~15%); official PIR is not available for the NBA |
| **Estimator** | exposure-weighted ratio of destination to source per-36 EFF, weight = min(minutes on the two sides), one factor per direction; cluster bootstrap on destination team-season, 2,000 draws, seed 0 | ratio of sums, mean of ratios (printed, T6) |
| **Design** | walk-forward by destination season 2017–2025: every arm (direction factor, level constant, RTM coefficients) refit on moves with destination season strictly earlier; scored on the season | single pooled fit (rejected: leakage) |
| **Baselines** | **B0** untranslated source per-36; **B1b** source × one constant per direction fitted on prior seasons; **B1c** RTM: the player's own prior-season rates in the *source* league (≥2 prior seasons required, else falls to B1b), no league term; **M** the combination: direction factor × RTM-predicted source rate | — |
| **Uncertainty** | paired cluster bootstrap on destination team-season, 4,000 draws, seed 0 | — |

## Predictions, written down now

**P1 — the split (primary).** On pooled walk-forward moves in both directions:

* (a) **B1c (RTM alone) is not beaten by B1b (multiplier alone)** on MAE: the paired-bootstrap interval on MAE(B1b) − MAE(B1c) includes zero or is negative.
* (b) **M (multiplier × RTM) beats B1b and beats B1c**, both intervals excluding zero.

P1 **passes** if (b) holds. (a) is reported either way; if (a) fails — the multiplier alone beats RTM — that is reported as such and the domestic→EuroLeague result does not generalise to NBA moves. P1 mirrors `translation-walkforward-per-league-2026-08-21.md` addendum, on which the paper's headline rests; a second population showing the same shape is the evidence sought.

**P2 — composition (secondary, descriptive below n = 20).** For players observed domestic league (*t−1*, ≥8 games) → EuroLeague (*t*, ≥8) → NBA (*t+1*, ≥8): the chained prediction domestic × f(L→EL) × f(EL→NBA), with f(L→EL) from the shipped factor table and f(EL→NBA) from this arm's prior-season fit, against the realised NBA rate; reported as MAE beside B0 and beside the un-chained EL→NBA prediction. At n < 20 it is a table, not a claim.

**G1 — usefulness, same bar as ATI-2799.** M beats B0 by ≥5% of B0's MAE with a paired-bootstrap interval excluding zero. Reported, but P1 is the question.

**Refusals**, published with their code: **R-ID** name/birth-year disagreement; **R-N** fewer than 8 games on either side; **R-H** fewer than 2 prior source seasons (scored by B1b path, flagged); **R-G** G-League or two-way seasons are not NBA seasons and are excluded from both sides.

## Threats and the control for each

| # | Threat | Control |
|---|---|---|
| T1 | **Selection.** Players move after a good or bad season; this is the confounded design by construction | Not removable; it is the design being *tested*. Reported: model bias split by whether the source season exceeded the player's own prior mean, as in ATI-2799 T5 |
| T2 | **Identity.** Name collisions across leagues | name + birth year from two first-party sources; R-ID otherwise; count printed |
| T3 | **Direction asymmetry.** EL→NBA and NBA→EL are different populations (64 vs 163 candidates) | separate direction factors; pooled P1 plus each direction reported, no averaging across directions |
| T4 | **Minutes / survivorship.** NBA minutes for movers are often tiny; per-36 on 60 minutes is noise | ≥8 games primary; ≥15 games and ≥100 minutes sensitivities; the count censored by each floor printed |
| T5 | **Pace.** NBA per-minute possessions run ~15% above EuroLeague, inflating counting stats per 36 | per-36 primary (what every published translation uses); per-possession sensitivity if team possessions are available on both sides; both printed |
| T6 | **Estimator choice** | three estimators printed; spread vs the G1 margin |
| T7 | **Age.** Birth years exist on both sides here | sensitivity: RTM with an age term; primary stays age-free to match the domestic arm |
| T8 | **Shuffled league mapping.** Is the multiplier's contribution the direction, or one free parameter? | swap the two direction constants (negative control): M must get worse; 200 permutations of RTM histories across players: M's gain over B1b must not be reached |
| T9 | **Power.** n is a few hundred moves at best | before any negative claim, the detectable ΔMAE at 80% power at the realised n is printed; a null without that line does not ship (METHOD.md §7) |
| T10 | **Season-label mismatch** | NBA start year = EuroLeague start year asserted on a known mover (e.g. Vezenkov: EL 2022 → NBA 2023 → EL 2024) |

## Gates shown to fail

The walk-forward script runs G1 once at an impossible margin (50%) and asserts it fails; the shuffled-direction control is an in-script assert (METHOD.md §8 corollary).

## What may not change after the fetch

Anything in this document. If a threshold is wrong it is reported as wrong and scored anyway. Additions are dated amendments, as in the 2026-27 line.

## Scripts (to be committed in the same branch, after this file)

* `scripts/fetch_nba_player_seasons.py` — pulls per-season regular-season totals and birthdates for the candidate players from the NBA's stats endpoints into `data/raw/nba/` (gitignored; **NBA rows are never committed** — NBA.com Terms of Use §9). Prints counts only.
* `scripts/build_nba_arm.py` — pairs, identity, factors, walk-forward, P1/P2/G1, every threat control, and the readback block the note quotes.
