# Amendment 7 to the SSAC27 full-paper pre-registration: the frozen forecasts tested on older seasons (E27)

**Approval record.**

| | |
|---|---|
| Amends | `docs/research/sloan-full-paper-preregistration-2026-11-03.md`, as amended on 2026-11-04, 2026-11-05, 2026-11-11 and 2026-11-12 (Amendments 1 to 6) |
| Written | 2026-11-12, after a readiness check that read no outcome, and before the analysis below was implemented |
| Approved by | Amir, "Accept Amendment 7 as written", 2026-11-12 |
| Basis | committed and pushed **alone**, before any implementation. Nothing below may be relaxed after a result is seen (METHOD.md §8) |

Everything in the 3 Nov pre-registration and in Amendments 1 to 6 stands. This amendment **adds** one analysis, E27. It changes no registered analysis, threshold, model, population or licence.

## Why this exists, in plain words

Every result in the paper is scored on seasons 2020–2025, which had been examined before the analyses were registered. The one clean test, the frozen 2026–27 forecasts, will be small: below 60 newcomers by 24 November it is descriptive only.

Official box scores of three of the paper's ten source leagues (Spain's ACB, the ABA League, Israel's BSL) have now been downloaded for 2007–08 to 2014–15 (PR #3614). Players who arrived in the EuroLeague or EuroCup from those leagues in 2008–09 to 2015–16 are a second clean test: **no model in the paper was fitted on those seasons, and no analysis in this project has read how those players performed after they arrived.**

E27 forecasts those arrivals with the models exactly as they were frozen for the 2026–27 test, and then asks the paper's three questions again.

## What has already been seen (exposure disclosure)

* **All destination seasons 2017–2025 remain exposed.** Nothing in E27 is fitted or tuned on the older seasons.
* **Read in the readiness check (12 November):** for the three leagues, which seasons and how many games are on disk, whether minutes are present, how names are printed, and whether team points equal the sum of player points. For the EuroLeague and EuroCup 2007–2015: each player's code, name, club, games and minutes. From these, counts only: about 387 arrival candidates for destination seasons 2008–2015 (ACB 192, ABA 140, Israel 55; 136 EuroLeague, 251 EuroCup; 89 of them in destination season 2013, when the EuroCup's format grew) and 1,283 same-season pairs. Saved as `optionA-three-league-readiness-2026-11-12.md`.
* **Two checks were run while this amendment was drafted, on names and on already-seen seasons only.** (1) On the 674 (2020–2025), outcomes rebuilt from API season totals against the cohort outcomes: 661 of 673 arrivals joined by person code, correlation 0.9996. (2) On Israel, where full names exist on both sides: of 282 links made by initial plus surname, 9 join two different first names (3.2%, Wilson 95% interval 1.7% to 6.0%); among the 181 links with a rare surname (defined below), 0. These numbers set the linking rules and gates below.
* **Not computed or seen:** any performance statistic of any arrival candidate in his arrival season; any forecast for an older season; any error.
* **Two raw records were printed, and field completeness was computed.** During the feasibility check of 12 November, one EuroLeague and one EuroCup season record from 2010–11 were printed in full to learn the field names; each player had 4 games, so neither is an arrival (the rule needs 8). The share of records with all 14 box-score fields present was computed for every season 2007–2025. No average, total or ranking of any performance field was computed for a season before 2016.
* **The files that hold the outcomes are on disk.** They are pinned below by sha256 so that the order of events can be checked.

## Pinned inputs

| File | sha256 |
|---|---|
| `data/raw/official_boxscores/aba/games.parquet` | `c11b7e8c9ef8b4f6261c271f4d9bf0828106c69900092a58dcd64b88c03b0eea` |
| `data/raw/official_boxscores/aba/player_boxscores.parquet` | `009c7e1611c6546058f4e66722b73cc29484830ef4016cdc313fcc15f20b3e1e` |
| `data/raw/official_boxscores/acb/games.parquet` | `9883aba851234e20988e73a0a0cfe0e3ccf4baa1cbdbf768c48b774c16a5eda4` |
| `data/raw/official_boxscores/acb/player_boxscores.parquet` | `344f7694dc17d356431ee219294da356574954bf3957589ad54aee01c6361808` |
| `data/raw/official_boxscores/israel/games.parquet` | `14b86022f51309a50519d5245bfab0ddf79982e89ec22dbf10ccfb7e5e1a0c3f` |
| `data/raw/official_boxscores/israel/player_boxscores.parquet` | `875a358225216de4fd28b5a56af7382e8fb3e000875aca64d283afab24920c58` |
| EuroLeague API season statistics, 18 files (`E2007`–`E2015`, `U2007`–`U2015`), as a sorted `sha256  name` manifest | `c42cf830ad31d7c739dd34aed8f37f7eb9b9c0efcf4b8458529ac0336047e50b` (sha256 of the manifest) |
| Frozen 2026–27 forecast file (P1) | `f3530c1a5ac369c032a996756ced226a93aa2d9f71d2e63aab21694de3d55316` |
| Pool-A pairs and cohort (v10) | `d964727924630dbf32c1764daf1e536c81d58988218a230fea591c62c1a62f58`, `c629f43e3194642d483701c3d07666252938d587e747c99dbb031a2346bf2abf` |

## Specification

| Field | Registered choice |
|---|---|
| Unit | One older arrival: player × destination season, with his domestic source season (the season before) and his continental destination season. |
| Population | Destination seasons 2008–2015 (2008–09 to 2015–16), all eight. Source league: ACB, ABA or Israel, at least 8 league games with minutes in the source season; where a player has two, the stint with more minutes. Destination: EuroLeague or EuroCup, at least 8 games. Not an arrival if he had 8 or more games in either continental competition the season before. These are the v10 rules. |
| Estimator | The three registered paired comparisons of mean absolute error in EFF/36: translation against history (`history_only` − `scheduled_history`); league-aware against history plus translation (`scheduled_history` − `source_ridge_10`); translation added to the league-aware forecast (`source_ridge_10` − `source_ridge_10_scheduled`). |
| Null | Zero difference for each paired comparison. |
| Filter | v10 eligibility as above; arrivals whose identity key is not unique are left out and counted (see Linking). |
| Key | EuroLeague API person code × destination season. |
| Uncertainty | As registered: two-way clustered 95% intervals (player, destination club-season). |

## Analysis

### Forecasts: frozen, not refitted

The older source seasons are forecast by the same code path that produced the frozen 2026–27 forecasts: translation factors from pool-A pairs up to 2025 (recipe R1), the lag from destinations up to 2025, and every arm trained on the feature-eligible arrivals up to 2025. **Only the source rows change.** Nothing is fitted, tuned or selected on any season before 2016. All 17 arms are computed; only the three comparisons above carry a licence.

* **Source line.** EFF per 36 minutes from the league's own box scores, with the paper's EFF formula. League games only (regular season and playoffs); cup games are left out. Games whose player points do not sum to the team score are left out and counted.
* **Career history.** As in v10: the player's minutes-weighted EFF/36 over all earlier seasons on disk. For older arrivals "on disk" means the three leagues from 2007–08 and the EuroLeague and EuroCup from 2007–08. A player with no earlier season is handled by the frozen code exactly as a 2026–27 candidate with none; nothing is filled in by hand.
* **Outcome.** EFF/36 in the destination season from the EuroLeague API season totals, same formula.

### Linking players (fixed before any outcome is joined)

ACB and ABA print an initial and a surname; Israel prints full names.

* **Key.** ACB and ABA: first initial + surname, accents and punctuation removed. Israel: the same, and the first three letters of the first name must also agree with the API name.
* **If a league's saved game pages carry full first names,** they are parsed and the Israeli rule is used for that league too. This is settled and recorded in the freeze run, before any outcome is joined.
* **Unique on both sides.** A domestic player-season is linked to an API person only if one player has that key in the league that season and one API person has it in the destination season across both competitions. Other candidates are left out and counted.
* Continental seasons of one player are joined by the API person code, not by name.
* **Measured weakness.** Where it can be measured (Israel, initials only), the initial-plus-surname key joins two different players in 3.2% of links (9 of 282; interval 1.7% to 6.0%). The paper states this beside the E27 result.
* **Rare-surname subset** (registered sensitivity): arrivals whose surname belongs to exactly one API person in 2007–2016 and to exactly one key in the source league's files. On Israel this subset had 0 wrong links in 181 (upper bound 2.1%). It keeps about 248 of the 387 candidates.
* **Club-confirmed** (reported, not a filter): the arrival's continental club matches his source club by the text rule of Amendment 6.

### Two versions, and which one is printed

Both versions are computed in the same runs.

* **V-all:** ACB, ABA and Israel (about 387 candidates).
* **V-noACB:** ABA and Israel only (about 195 candidates).

Amir is waiting for ACB's permission to use its data. **The paper prints V-all only if that permission has arrived in writing by the analysis lock. Otherwise it prints V-noACB**, and says in one sentence that a version including ACB was computed and is withheld for permission, not for its result, and whether its three readings agree with the printed ones. This rule is fixed now, before any result exists, so the choice cannot depend on the result.

### Order of events

1. **Freeze run.** Builds the older source rows and links, and writes one forecast file for every eligible source player-season and both destinations, with its sha256. It computes no error.
2. The forecast file's sha256 is committed and pushed.
3. **Scoring run.** Reads the frozen file, refuses to run if its sha256 differs, joins the outcomes, selects the arrivals and computes the comparisons. One scoring run; it is not repeated with changed rules.

### Readings and licences

The margin is 2% of the league-aware forecast's error on the scored arrivals, as registered.

| Comparison | Interval | What the paper may say |
|---|---|---|
| Translation against history | above zero | "translation's gain over history holds on seasons no model saw" |
| | includes zero | "not detectable at this n", with n |
| | below zero | a failure on older seasons; reported to Amir before any writing, then in the main text |
| League-aware against history plus translation | includes zero and inside the margin | "one number per league matches translation on seasons no model saw" |
| | includes zero, wider than the margin | "no difference detected; the interval is wider than the margin", with n |
| | excludes zero in favour of translation | contradicts the headline on older seasons; reported to Amir before any writing, then in the main text |
| | excludes zero in favour of the league-aware forecast | reported as such |
| Translation added to the league-aware forecast | includes zero and inside the margin | "translation adds nothing detectable on seasons no model saw" |
| | otherwise | as in the row above, with the direction stated |

* **The result is reported whatever it is.** If the scoring run happens, the printed version goes into the paper's main text.
* **Rare-surname subset.** The three comparisons are printed on it beside the main result. If a reading that holds on all arrivals fails there, it is worded "not detectable at this n" with n, never as a reversal, unless the point estimate changes sign with an interval that excludes zero; that case goes to Amir before any writing.
* **Printed without a licence (descriptive):** each arm's mean error (a forecast-level check, because league strength may have drifted in ten years); the three comparisons by source league, by destination and on club-confirmed arrivals; the share of arrivals with no career history on disk, and the comparisons on arrivals that have one.
* **What n can show (projection from the 674, stated in advance).** An interval must lie wholly inside the margin (about 0.058) to earn a "no difference" reading. If the older seasons gave the 674's point estimates:
  * V-all, n ≈ 387: translation against history +0.05 to +0.27; league-aware against history plus translation −0.04 to +0.06; translation added −0.04 to +0.03. The first comparison would be above zero and the third inside the margin. **The second would be at the edge** (upper end about 0.061); it may end as "no difference detected; the interval is wider than the margin".
  * Rare-surname subset of V-all, n ≈ 248: translation against history +0.02 to +0.30; league-aware against history plus translation −0.05 to +0.07; translation added −0.04 to +0.04.
  * V-noACB, n ≈ 195: translation against history +0.00 to +0.32; league-aware against history plus translation −0.06 to +0.08; translation added −0.05 to +0.05.
  * So V-noACB and the rare-surname subset cannot show "inside the margin" for the second comparison and are at the edge for the first. Their nulls are worded "not detectable at this n". Older outcomes are noisier, so real intervals will be somewhat wider than these.

## Limits stated in advance

* **Three of ten leagues.** They supply 227 of the 674 benchmark arrivals. E27 says nothing about the other seven.
* **A weaker name key.** Initial plus surname can join two different players: about 3 links in 100 where it can be measured. A wrong link gives every forecast the wrong player's line, so it adds noise to all arms alike and pulls the comparisons toward zero. The rare-surname subset is the check.
* **Less career history.** Nothing before 2007–08 and nothing from the other seven leagues is on disk, so the history-only forecast knows less about older arrivals than about the 674. This can make translation's gain over history look larger. The share of arrivals without history is printed.
* **Ten years of drift.** The league numbers were estimated on 2017–2025. A miss on 2008–2015 can mean the numbers do not carry back that far, not that they are wrong today. The paper will say this in either direction: a pass is not proof for today's leagues either.
* **A different source of box scores.** The 674 use Proballers for domestic statistics; E27 uses the leagues' own sites. No season is covered by both, so the two cannot be compared directly.
* **Older outcomes are noisier** (fewer continental games per player).

## Gates and negative controls

| Gate | Pass rule | Negative control |
|---|---|---|
| G27a inputs | every pinned file equals its sha256 | a changed byte must fail |
| G27b same models | given the 2025–26 source rows, the generator reproduces the published frozen 2026–27 forecasts on every arm to 1e-9 | a shifted factor must fail |
| G27c same outcome | on the 674, at least 95% of arrivals join to the API season totals by person code; among them the rebuilt outcomes correlate at 0.99 or more with the cohort outcomes, and the three registered comparisons keep their registered readings when scored against them | outcomes shuffled across players must fail |
| G27d the linking code is the one measured | run on Israel with initials only, the committed linking code reproduces the two measurements above (9 of 282; 0 of 181) | surnames shuffled across players must give fewer than a tenth of the links |
| G27e frozen before scored | the scoring run reads the forecast file whose sha256 was pushed | a changed byte must fail |

If G27b, G27c or G27d fails, E27 stops and Amir is told; no outcome of an older arrival is joined.

## Threats and their controls

| Threat | Control |
|---|---|
| Models tuned on the test seasons | forecasts come from the frozen path; G27b; nothing is fitted before 2016 |
| Forecasts changed after outcomes were seen | freeze run, pushed sha256, G27e |
| Choosing the version by its result | the printing rule above depends only on ACB's permission |
| Rules bent toward a clean result | population, key, filters and readings are fixed above; one scoring run |
| A null read as "no effect" | nulls are worded "not detectable at this n", with n and the projected half-widths |
| A result that weakens a paper claim | reported to Amir before any writing, then in the main text |

## Stop rule

If the freeze run has not completed with G27a to G27d passing by the evening of 17 November, E27 is not in the 1 December paper. It then moves to the February presentation under this same amendment, and the paper does not mention it.

## Scope boundary

Nothing pinned changes. E27 is implemented in a new dated generator with a committed report script. Retained runs go to the project's run archive from committed code. The public companion repository carries no box score and no game row from the league sites; it carries nothing derived from ACB unless ACB's permission has arrived.

## Timeline

| Date | Step |
|---|---|
| 12 Nov | this amendment approved and pushed alone |
| 13–16 Nov | adapter, linking, gates |
| by 17 Nov | freeze run; sha256 pushed |
| 18 Nov | scoring run; result to Amir |
| 19–20 Nov | paper re-rendered; analysis lock |
