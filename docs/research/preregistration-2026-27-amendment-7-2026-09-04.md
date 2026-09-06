# AMENDMENT 7 to the 2026-27 prospective pre-registration — the lock-day rule: one collection on the first READY day or on 22 September, the population labelled a floor where the registry is under-published, and a leak-free EuroCup gap record

**Date: 2026-09-04. Ticket: ATI-2917, recorded on ATI-2891. Status: decided by Amir on 2026-09-04 ("ok do it", on the recommendation below); binding on the lock.** Base document is `preregistration-2026-27-predictions.md`. Prior amendments: `-amendment-1-2026-08-21.md` … `-amendment-6-2026-09-04.md`. Lock deadline **24 September 2026**, EuroLeague tip-off. EuroCup tips off **29 September 2026** (`api-live.euroleague.net/v2/competitions/U/seasons/U2026/games`, first scheduled date; EuroLeague's first date from the same endpoint is 2026-09-24).

## Specification

| Choice | This amendment | Alternatives considered |
|---|---|---|
| **Scope** | what happens on the lock day if the league's roster registry has not caught up: which day, which collection, what the population is called, and how the gap is measured | leaving it to the day (rejected — a population rule chosen while looking at the count is the thing pre-registration exists to prevent, METHOD.md §8) |
| **Design** | **one** `--competition both` collection on a single lock day; the scored population is that collection, labelled a floor where under-registered | a staggered lock — EuroLeague on 22 Sept, EuroCup on 28 Sept, each before its own first game (rejected, three reasons: it needs a merge script stitching two diffs into one artifact, new code and tests two weeks out; it re-reads the base document's single tip-off deadline after the fact; and at the registry's measured pace it still lands on a floor). Club websites as the population source (rejected — see Change 4) |
| **Evidence admitted** | the daily readiness log (`logs/signings_readiness.log`); the per-club record `data/processed/signings/roster_coverage_<date>.json` written by `scripts/check_signings_readiness.py --per-club-out` on every run (this amendment adds it); the league schedule endpoint for tip-off dates; three club websites, hand-observed, motivation only | — |
| **Constraint** | no bar moved, no metric changed, no gate re-scored. The collector's roster-plausibility bar (`SigningsReport.MIN_PLAUSIBLE_MEAN_ROSTER = 8.0` people/club) is unchanged; Change 2 states the one condition under which its override is permitted and what the artifact must then say | — |
| **Traceability** | every number names the generator and the field (`METHOD.md` §13, §16) | — |

---

## Why now: the registry lags the clubs, and it lags past the lock

**What the gate sees.** The readiness job (`com.basketball-analysis.signings-readiness`, 09:15 daily) asks the league API for every club's roster in both competitions and clears when both sit at ≥ 8.0 people/club. Since 2026-08-26 (the day its own defect was fixed, #2031) it has returned NOT READY every morning:

| date | EuroLeague, 20 clubs | EuroCup, 32 clubs | previous season |
|---|---:|---:|---|
| 2026-09-01 | 281 (14.1/club) | 194 (6.1/club) | 383 (19.1) / 358 (17.9) |
| 2026-09-02 | 279 (13.9) | 194 (6.1) | same |
| 2026-09-03 | 280 (14.0) | 196 (6.1) | same |
| 2026-09-04 | 279 (13.9) | 197 (6.2) | same |

(`logs/signings_readiness.log`, the four most recent verdicts.) Four people in four days. **The per-club record for 2026-09-04** (`roster_coverage_2026-09-04.json`, taken in the afternoon; the 09:15 log row above read 197): EuroLeague 20 clubs, 279 people, 13.9/club, 0 empty, 0 below 8 (none); EuroCup 32 clubs, 198 people, 6.2/club, 14 clubs at 8 or more, 18 below 8, of which 5 with nobody registered (BOS, BOU, BUD, LJU, TTK); fetch failures 0 in both, so every club answered and the thinness is upstream (fields `competitions.<label>.clubs_empty_current`, `.clubs_below_bar_current`, `.fetch_failures`).

**What the clubs say.** Three of the EuroCup clubs the registry lists with nobody were read on their own websites on 2026-09-04. Hand-observed, in a browser, recorded here as motivation only — no analysis reads this table:

| club (code) | URL | observed | players listed on the site | in the registry |
|---|---|---|---:|---:|
| Bosna Sarajevo (BOS) | kkbosna.ba | 2026-09-04 | 17 | 0 |
| Türk Telekom Ankara (TTK) | turktelekombasketbol.com.tr/a-takim-oyunculari/ | 2026-09-04 | 13 | 0 |
| JL Bourg (BOU) | jlbourg-basket.com | 2026-09-04 | roster page not reached; eight 2026-27 signings announced 30 May–22 June, preseason games played from 27 Aug | 0 |

The gap is registration, not unsigned teams. Nothing on our side moves the registry, and at four people in four days EuroCup will not reach 8.0/club by the lock. EuroLeague sits above the bar and is still under-registered (13.9 against 19.1 a season ago), so the floor label in Change 3 applies to both competitions, not to EuroCup alone.

## Change 1 — Lock day: the first READY morning, or 22 September, whichever comes first

**Rule.** The pre-lock collection is made **once**, on the first morning the readiness job returns READY, or on **22 September 2026** if it has not by then. It is never redone: a READY on the 23rd changes nothing. 22 September leaves two days to build, review, commit and merge before the 24 September tip-off; a collection on the 23rd that hits a throttled sweep would have no retry.

**Sequence on the lock day, written down now** (every step is an existing committed script):

1. `bash scripts/check_signings_readiness.sh` has run at 09:15 and left `data/processed/signings/roster_coverage_<lock-date>.json`. Read its verdict and `fetch_failures` before anything else.
2. `scripts/collect_import_signings.py --competition both --collected-at <lock-date> --known-empty-clubs <list> --provenance "pre-lock collection, Amendment 7"` — `<list>` is `competitions.eurocup.clubs_empty_current` ∪ `competitions.euroleague.clubs_empty_current` from that morning's record, **not** the 2026-08-21 six.
3. `scripts/build_translation_predictions.py --signings <that artifact> --built-at <lock-date> --status locked`. *[Added 2026-09-04 by Amendment 8 Change 1: plus `--interval-params docs/research/artifacts/prelock-program-2026-09/interval_params_lock.json`.]*
4. `scripts/restate_prediction_power.py` at the locked count.
5. Commit the three artifacts (`roster_coverage_<lock-date>.json`, the signings artifact, `translation_predictions_2026.json` with `status: locked`, `power_restated_2026.json`) in one PR, merged the same day.

## Change 2 — The fallback day: when the collector's guard may be overridden, and what the artifact must then say

The collector refuses a snapshot under 8.0 people/club (`SigningsReport.implausible_snapshots`) because a throttled sweep otherwise prints an incomplete diff that reads as complete. That guard is right and stays. On the fallback day it will fire on EuroCup, and the discriminator between "throttled" and "unpublished" is the readiness record:

**Rule.** `--allow-thin-rosters` is permitted on the lock day **only if** that morning's readiness verdict is **NOT_READY** (not DEGRADED) **and** `fetch_failures == 0` in every competition of `roster_coverage_<lock-date>.json` — every club answered, and what it answered is thin. Under any other reading the sweep is re-run after the pacing delay, and if it still degrades the collection waits a day (there is one day of slack). The artifact's `provenance` string must name this amendment and the record it was checked against.

**Rows from thin clubs stay in.** A player registered to an under-published club is a verified registration; dropping him because his club's count is low would choose the population by looking at the data (METHOD.md §8). The club is labelled under-registered in the record; the row is scored.

## Change 3 — The population is a floor, and the publication says so with a number

The base document's §7 rule already makes the population "a dated collection count, restated at lock". This amendment fixes what that count is *called* when the registry is under-published: **a floor**. The publication states, beside the count, for each competition: clubs in the field, clubs with nobody registered on the lock day, clubs below 8 people, and the previous season's mean per club — all read from `roster_coverage_<lock-date>.json` (`competitions.<label>.clubs_empty_current`, `.clubs_below_bar_current`, `.mean_current`, `.mean_previous`). No power figure is scaled to a count the registry has not produced.

## Change 4 — A leak-free EuroCup gap record: collected, committed, never scored

**Rule.** On **28 September 2026**, the day before EuroCup's first game, a second, EuroCup-only collection is made: `scripts/collect_import_signings.py --competition U --collected-at 2026-09-28 --provenance "EuroCup gap record, Amendment 7 Change 4 — NOT the scored population"`, with that morning's readiness record beside it. It is committed as a dated artifact and **never merged into, scored with, or substituted for** the locked set. Its one use is to state in the publication, by name and count, which EuroCup imports the lock missed because the registry had not caught up. It is leak-free by construction: no EuroCup game has been played when it is taken.

**Why not club websites as the source.** They were considered on 2026-09-04 and are the wrong instrument for the population: the base document's import definition is a first-party roster diff keyed by the league's person code (on a club's 2026-27 roster, not on it in 2025-26); club sites give names in five alphabets, no person codes, and no previous-season roster to diff against, so "import" would become a judgement made club by club across fifty-two hand-read pages with no committed generator — the defect ATI-2917 was filed to remove. Türk Telekom's page shows the trap concretely: it lists ALLMAN, KYLE, who is already in the draft prediction set, and nothing on the page says which competition he arrived from or whether he is an import under the rule. Club sites remain admissible as motivation (the table above) and as a lock-day cross-check the publication may quote as prose.

**If Amir later wants the 28 September players scored,** that is a separate amendment defining a secondary population with its own power statement; this one does not open that door.

## Change 5 — The per-club record is generated, daily

`scripts/check_signings_readiness.py --per-club-out <path>` writes, from the same sweep that produces the verdict (no extra requests), a dated JSON with per club and competition the current and previous-season roster count and whether the fetch failed, plus the totals the verdict was computed from; it refuses to write totals that disagree with the detail. The wrapper `check_signings_readiness.sh` passes `--per-club-out data/processed/signings/roster_coverage_$(date +%F).json` on every run, so the lock day's file exists before anyone decides anything. Tests: `tests/test_scripts/test_check_signings_readiness.py::test_the_coverage_record_*`, `::test_measure_records_per_club_counts_and_marks_the_failed_fetch`, `::test_the_wrapper_writes_the_dated_per_club_record`. The 2026-09-04 record is committed with this amendment as the first instance.

---

## Provenance

| Item | Where it is fixed |
|---|---|
| lock day and sequence | this document, Change 1; scripts named there are all committed |
| override condition | Change 2; `scripts/collect_import_signings.py --allow-thin-rosters`, `SigningsReport.MIN_PLAUSIBLE_MEAN_ROSTER` |
| floor fields | `scripts/check_signings_readiness.py::coverage_payload` → `data/processed/signings/roster_coverage_<date>.json` |
| gap record | Change 4; `scripts/collect_import_signings.py --competition U` |
| tip-off dates | `api-live.euroleague.net/v2/competitions/{E,U}/seasons/{E,U}2026/games`, first `date` |
| daily verdicts | `logs/signings_readiness.log`; job `com.basketball-analysis.signings-readiness` |
| club-site observations | the table above, hand-observed 2026-09-04; not an input to any script |
