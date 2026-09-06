# AMENDMENT 4 to the 2026-27 prospective pre-registration — three decisions recorded

**Date: 2026-09-03. Ticket: ATI-2891. Status: decided by Amir on 2026-09-03; binding on the lock.** Base document is `preregistration-2026-27-predictions.md`. Prior amendments: `-amendment-1-2026-08-21.md`, `-amendment-2-2026-08-25.md`, `-amendment-3-2026-09-03.md`. Lock deadline **24 September 2026**, tip-off.

## Specification

| Choice | This amendment | Alternatives considered |
|---|---|---|
| **Scope** | records three decisions taken on 2026-09-03 after Amendment 3 was proposed: its acceptance, the input corpus for the destination side, and the treatment of six source leagues whose 2025-26 season is incomplete in the corpus | leaving decisions 2 and 3 as ticket comments (rejected — a decision only in a ticket tracker has no verifiable timestamp; same reasoning as the 2026-08-27 branch decision) |
| **Evidence admitted** | `continental-source-check-2026-09-03.md`; the games-per-season audit on ATI-2956; the 2026-08-21 signings collection for the illustrative count in Change 3 | — |
| **Constraint** | no bar moved, no metric changed, no gate re-scored (`METHOD.md` §8). Change 2 changes an *input*, Change 3 changes *who is refused* and adds a refusal code; neither touches §6 or §8 | — |
| **Traceability** | each change names the measurement and the decision record behind it | — |

---

## Change 1 — Amendment 3 is ACCEPTED

Amir accepted Amendment 3 on 2026-09-03 ("accept Amendment 3", recorded on ATI-2891). Its two changes are now operative: the prediction target is **EFF/36**, and every prediction and refusal carries `source_games_held`, `source_last_game` and `source_completeness`.

## Change 2 — The destination side is read from the EuroLeague API

**Decision.** "We use the EuroLeague API for the EuroLeague and EuroCup side of the model." The continental side of every player-season pair — the destination side of the factors, the level correction, the RTM comparator and the realised outcome that every 2026-27 prediction is scored against — is read from the league's first-party API box scores, with EFF computed from components, instead of from the Proballers copy.

**Why now.** The Proballers copy of 2025-26 holds 207 of 402 EuroLeague games and 130 of 195 EuroCup games (ATI-2956). The API is complete, first-party, and reproduces the shipped factors within one bootstrap SE on 18 of 19 cells with the EuroLeague ordering intact when the metric is like-for-like (`continental-source-check-2026-09-03.md`, finding 2).

**What it changes.** The input corpus. The estimator, the gates and every rule in §2–§11 are unchanged. Because the corpus changes, the **factor table, the walk-forward and K_LAG are re-fitted on it before the lock**, and the note and abstract numbers that depend on them are re-read from the new run. The ATI-2799 holdout verdict is not re-scored; it stands as the record of the gate on the corpus it was run on, and the re-fitted numbers are reported beside it, not in place of it.

**What it does not change.** The domestic side of every pair remains Proballers. The paper's outcome variable becomes first-party; its predictor does not.

## Change 3 — Six source leagues are refused for the 2026-27 set

**Decision.** "We won't use those leagues now." The six leagues whose 2025-26 season is incomplete in the corpus — **france-pro-a, turkey-bsl, aba-league, vtb, lithuania-lkl, poland-plk** — are not used as source leagues for the 2026-27 prediction set. Their factors remain in the table (fitted on 2015–2024 full seasons plus the partial 2025); what is refused is a *2026-27 prediction* whose source season is one of those league-seasons.

**New refusal code.** **R9 `SOURCE_SEASON_INCOMPLETE`** — the player's source league-season holds fewer games in the corpus than the league's complete-season count (the Amendment 3 denominator), because collection stopped. Published with the code, `source_games_held` and `source_last_game`, like every other refusal. R9 is checked before R5, so a player from one of these leagues is refused as R9 whether or not he also falls under the 8-game floor.

**What it costs, stated now.** On the 2026-08-21 collection, **43 of 94 scorable imports (46%) come from these six leagues** — 27 of 52 EuroLeague arrivals and 16 of 42 EuroCup arrivals — leaving **51 predictions** (25 EuroLeague, 26 EuroCup) plus the refusals. The figure is restated at the pre-lock collection. The power table in §7 is restated at that count; at n ≈ 51 only the B0 criterion retains meaningful power, and the pre-registration already says a single prospective season cannot adjudicate B1b or per-league resolution.

**Reversal condition, stated now.** If a licensed or otherwise authorised source completes those six league-seasons before the lock, R9 does not fire for them and they are scored under the ordinary rules. After the lock nothing changes (§10).

---

## Provenance

| Item | Where it is fixed |
|---|---|
| Amendment 3 acceptance; decisions 2 and 3 | Amir, 2026-09-03, recorded on ATI-2891 and ATI-2807 |
| destination-side reproduction from the API | `scripts/compare_continental_sources.py --dest-metric eff`; `continental-source-check-2026-09-03.md` |
| games per league-season 2025 | ATI-2956 |
| 43 of 94 | `data/processed/signings/import_signings_2026_both_competitions.json` (`collected_at: 2026-08-21`), `kind == "import"` and `translation_available`, grouped by `prior_league` |
