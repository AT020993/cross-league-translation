# AMENDMENT 3 to the 2026-27 prospective pre-registration

**Date: 2026-09-03. Ticket: ATI-2891 (via ATI-2807 / ATI-2955 / ATI-2956). Status: ACCEPTED by Amir on 2026-09-03 (recorded in `preregistration-2026-27-amendment-4-2026-09-03.md` Change 1); not yet locked.** Base document is `preregistration-2026-27-predictions.md`. Prior amendments are `-amendment-1-2026-08-21.md` and `-amendment-2-2026-08-25.md`. Lock deadline **24 September 2026**, tip-off.

## Specification

| Choice | This amendment | Alternatives considered |
|---|---|---|
| **Scope** | two changes forced by measurements taken on 2026-09-03: the prediction target's *name*, and a disclosure about the *completeness* of the source seasons | editing the base document in place (rejected — every amendment is dated for the same reason as the last two) |
| **Evidence admitted** | `continental-source-check-2026-09-03.md` (`scripts/compare_continental_sources.py`) and the games-per-season audit recorded on ATI-2956 | — |
| **Constraint** | no bar moved, no metric added or dropped, no gate re-scored (`METHOD.md` §8); nothing here is fitted to a 2026-27 outcome because none exists | — |
| **Traceability** | each change names the measurement that forces it | — |

**Why a third amendment.** Amendments 1 and 2 are dated 21 and 25 August. Two things were measured on 3 September that neither could have known: the metric the corpus calls PIR is not PIR, and the 2025-26 season those amendments treat as complete is half-scraped in eight leagues.

---

## Change 1 — The prediction target is EFF, not PIR (label correction, no bar moved)

**Measurement.** The Proballers `pir` column equals the NBA efficiency formula — PTS + REB + AST + STL + BLK − missed FG − missed FT − TOV — on 100% of rows in twelve leagues and 99.99% / 99.35% in the other two (every remaining row within 1). EuroLeague's published PIR adds fouls received and subtracts fouls committed and blocks against; the API's `Valuation` matches that formula on 100% of rows and matches EFF on 28.7%. The scraper folds `eff/pir/valuation/index` headers into one column named `pir`.

**Change.** Everywhere the base document and Amendments 1–2 say "per-36 PIR", read **"per-36 EFF (efficiency: PTS + REB + AST + STL + BLK − missed FG − missed FT − TOV)"**. This applies to §2 (prediction target), §4 (prediction basis and interval), §5 (baselines B0–B1c, all in the same unit), §6 (metrics) and §7 (power, quoted in the same unit). The column name `pir` in every script and artifact is unchanged; only its meaning in prose is corrected.

**What does not change.** Every number. Factors, gates, intervals, K_LAG, the RTM coefficients and the power table were all computed on the same column on both sides of every pair; a ratio of EFF to EFF is what was pre-registered, under the wrong name. No threshold moves. The ±8 interval, the 0.922 realised coverage and the 12.8% margin are in EFF/36 and were always in EFF/36.

**Why this is an amendment and not a re-score.** The metric is the same column the gates were run on. Renaming it after the fact is exactly the kind of correction METHOD.md's *Applying corrections* rule asks for: in place, retraction visible, downstream artifacts updated (ATI-2955).

## Change 2 — Source-season completeness is a declared property of every prediction and refusal

**Measurement.** The daily Proballers scrape last wrote a game between 26 December 2025 and 9 January 2026 for aba-league, eurocup, euroleague, france-pro-a, lithuania-lkl, poland-plk, turkey-bsl and vtb (ATI-2956). Season 2025 holds 40–65% of a full season in those leagues. germany-bbl, greece-a1, italy-lba (ATI-2895, scraped in full in August), israel-bsl, spain-acb and bcl are complete.

**Consequence for the pre-registered set.** An import's source season is 2025-26 in his domestic league. For six of the eleven source leagues that season is a partial season in the corpus. Two of the pre-registered rules interact with that directly:

* **R5 `INSUFFICIENT_SOURCE_GAMES`** (fewer than 8 source games) will refuse players who played a full season upstream but hold fewer than 8 games *in the corpus*. That is a refusal caused by the corpus, not by the player.
* **B0, and therefore every criterion in §8,** is the untranslated source rate. A half-season rate is a noisier B0. This makes the pre-registered test *harder to pass*, not easier, so no bar is affected; but a reader must be able to see it.

**Change.** Every published prediction and every refusal carries three fields for the player's source league-season: **`source_games_held`** (distinct games in the corpus), **`source_last_game`** (the latest game date in the corpus), and **`source_completeness`** = `source_games_held` ÷ the **maximum** distinct-game count that league holds in any of seasons 2022, 2023 and 2024, with that denominator printed. The maximum, not the 2024 count, because a single prior season is not a safe yardstick on the corpus's own numbers: greece-a1 2024 holds 132 games ending 23 March (itself partial), france-pro-a went 306 → 240 and germany-bbl 272 → 306 between seasons as league sizes changed. A ratio above 1 is possible when a league grew and is reported as is. R5 refusals are additionally labelled **`R5c`** when the player's source league is one of the eight named above, so that a refusal caused by the corpus is distinguishable from one caused by the player. Neither label changes who is scored or how.

**What this amendment does not do.** It does not fill the gap. Completing 2025-26 for the two continental competitions is available today from the EuroLeague API, and `continental-source-check-2026-09-03.md` shows the factors reproduce from it; completing the six domestic leagues depends on Proballers (permission requested 2026-09-03) or another source. Whether the destination side is switched to the API before the lock is a separate, dated decision to be recorded on ATI-2891 — it changes the *input corpus*, not any rule here, and the note gives the measured cost of the switch (raw factors within one SE on 18 of 19 cells).

---

## Provenance

| Item | Where it is fixed |
|---|---|
| `pir == EFF` per league; API `Valuation == PIR` | `scripts/compare_continental_sources.py --reconcile-only`; `continental-source-check-2026-09-03.md` finding 1 |
| factors reproduce from the API destination side | same script, `--dest-metric eff`; finding 2 |
| games per league-season, last scraped date | ATI-2956 (audit run 2026-09-03 against `data/raw/proballers/*/2025/`) |
| the rules this amends | `preregistration-2026-27-predictions.md` §2, §3 (R5), §4–§7 |
