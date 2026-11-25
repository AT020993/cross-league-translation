# Amendment 6 to the SSAC27 full-paper pre-registration: an identity audit of the 674 forecast arrivals (E26)

**Approval record.**

| | |
|---|---|
| Amends | `docs/research/sloan-full-paper-preregistration-2026-11-03.md`, as amended on 2026-11-04, 2026-11-05, 2026-11-11 and 2026-11-12 (Amendments 1 to 5) |
| Written | 2026-11-12, after the E25 result was read and before the analysis below was implemented |
| Approved by | Amir, "Accept Amendment 6 as written", 2026-11-12 |
| Basis | committed and pushed **alone**, before any implementation. Nothing below may be relaxed after a result is seen (METHOD.md §8) |

Everything in the 3 Nov pre-registration and in Amendments 1 to 5 stands. This amendment **adds** one analysis, E26. It changes no registered analysis, threshold, model, population or licence. It is not a third look at the estimation pairs: E13 and E25 audited the pairs behind the translation factors; E26 audits a different set of records, the forecast arrivals.

## Why this exists, in plain words

Every headline number in the paper is scored on 674 arrivals. Each arrival joins two records by the player's name: his domestic season (the source) and his EuroLeague or EuroCup season a year later (the destination). E25 found that about 1 name join in 100 among the estimation pairs is wrong, and that some of those are two different players who share a name. The arrivals use the same name key and have never been checked. The paper now says so in Limitations.

E26 checks all 674, by fixed rules and with no hand decisions, and then asks the question that matters for the paper: do the three main comparisons read the same when the arrivals classed wrong are left out?

## What has already been seen (exposure disclosure)

* **All destination seasons 2017–2025 remain exposed.** E26 is **exploratory**, and the paper will say so.
* **Seen before this amendment was written:** every published result on the 674; the E13 and E25 audits of the estimation pairs, including their wrong pairs.
* **Not computed or seen:** any identity check on any arrival; any comparison of an arrival's source club with the EuroLeague API's "previous team" field.
* **One file was already downloaded.** The EuroLeague API player lists for 2020–21 to 2025–26 (both competitions) were downloaded on 12 November for an unrelated count of G League arrivals. One record was read to learn the field names. No comparison with any source record was made. That file, without birthdates, is the pinned input below (sha256 `753aebcbfb0c724eb1819da0abb4f21e80f18cb50a1ddee18bfb966ede1c3e3c`).

## Specification

| Field | Registered choice |
|---|---|
| Unit | One forecast arrival: player × destination season, with his domestic source record (league, club or clubs, the season before) and his continental destination record. |
| Population | The 674 v10 target keys (destination seasons 2020–2025), pool A. A census: every arrival is classed, none is sampled or dropped. |
| Estimator | E26a: the number and share of arrivals in each class (CONFIRMED, NAME ONLY, WRONG, UNRESOLVED). E26b: the three registered paired comparisons (translation against history; league-aware against history plus translation; translation added to the league-aware forecast, λ = 10) re-scored on subsets defined by the classes. Models are not refitted. |
| Null | E26a: none (counts from a census). E26b: zero difference for each paired comparison. |
| Filter | v10 eligibility; targets fixed before scoring. Subsets are defined only by the E26a classes. |
| Key | `player_name` × `season_dest`. |
| Uncertainty | E26a: exact counts; no interval, because nothing is sampled. E26b: as registered, two-way clustered 95% intervals (player, destination club-season). |

## Analysis

### E26a. Classing each arrival

**Evidence**, all from raw files and the pinned API list:

1. **Birthdate.** The E13 rule, applied across the two seasons: the API birthdate of the destination player against the Proballers profile birthdate of the source record's name, where each side has exactly one.
2. **Source-season bridge.** If the same API person also has continental box-score rows in the source season, the imported E13 check is run on that same-season pair (his domestic source record against his continental club that season).
3. **Destination-season check.** The imported E13 check is run between the destination record and every domestic record under the same name key in the destination season. "Stayed" means one of those domestic records is in the source league at a source club.
4. **Previous team.** The API lists each player's previous team for the destination season. It matches a source club when, after upper-casing, removing accents and punctuation and dropping the generic words `BC BK KK CB SC SK AS FC CLUB BASKET BASKETBALL BASKETBOL BALONCESTO PALLACANESTRO`, either all words of the shorter name are among the words of the longer one, or the two word sets have a Jaccard overlap of at least 0.6. The API list is joined to the destination record by name key, season and competition.

**Classes**, applied mechanically in this order. There is no hand review.

* **WRONG** if any of:
  * the birthdates contradict;
  * the source-season bridge is classed WRONG by the E13 rules;
  * the player "stayed" and the E13 check classes that domestic record WRONG against the destination player (a different man with this name is still playing at the source club);
  * two API persons stand behind the name key in the destination record.
* **CONFIRMED** if not WRONG and any of:
  * the birthdates agree;
  * the source-season bridge is CONFIRMED;
  * the player "stayed" and the E13 check confirms that domestic record;
  * the API's previous team matches a source club.
* **NAME ONLY** if neither of the above, the E13 check confirms the destination player against a domestic record of the same name that season, and no domestic record of that name is classed WRONG against him. The destination player is one identified person, no second player of that name is visible, and the link across his change of club rests on the name.
* **UNRESOLVED** otherwise.

**Printed:** the four class counts overall and by source league, destination and season; for each CONFIRMED arrival, which evidence confirmed it; for each WRONG arrival, the rule and the evidence; the previous-team strings beside the source clubs they were compared with.

### E26b. Do the comparisons depend on the arrivals classed wrong?

* **Subsets.** S1 (primary): the 674 without WRONG. S2: without WRONG and UNRESOLVED. S3: CONFIRMED only.
* **Comparisons.** On each subset, the three registered paired comparisons with their intervals, using the forecasts already fitted. The margin is 2% of the league-aware forecast's error on that subset, as registered.
* **Readings.** (i) translation's gain over history: interval above zero; (ii) league-aware against history plus translation: interval includes zero and lies inside the margin; (iii) translation added to the league-aware forecast: interval includes zero and lies inside the margin.

### Licences

* **E26a count.** "By fixed rules, K of the 674 forecast arrivals are classed as identity mismatches; C are confirmed by independent evidence, N rest on the name across a change of club, and U are unresolved." Always stated, whatever the counts.
* **E26b, S1.** All three readings hold: "the three comparisons read the same without the arrivals classed wrong." Any reading fails: reported to Amir before any writing; the paper states which reading changed and reports both versions.
* **E26b, S2 and S3.** Printed as sensitivity checks. A reading that fails on a smaller subset is worded "not detectable at this n" with the subset's size, never as a reversal, unless the point estimate changes sign with an interval that excludes zero; that case goes to Amir before any writing.
* **WRONG share of 5% or more:** a data-quality finding; reported to Amir before any writing.
* **S3 is not a replacement estimate.** Players confirmed because they stayed at their club are not typical signings. The paper may cite S3 only as a robustness check.

## Limits stated in advance

* **What the rules can and cannot detect.** A wrong join is detected when the two birthdates disagree, or when a second player of the same name is visible in the records at the relevant time. A namesake who left the covered leagues is invisible. NAME ONLY marks exactly that region, and its size is reported.
* **No refit.** The models were fitted on training arrivals that are not audited here. E26b removes arrivals from scoring only.
* **Career history is not audited.** The history feature joins a player's earlier seasons by the same name key.
* **The previous-team rule is a text match.** It can miss a true match (sponsor names) and can, rarely, match two clubs from one city. The compared strings are printed.

## Gates and negative controls

| Gate | Pass rule | Negative control |
|---|---|---|
| G26a inputs | pool-A pairs and cohort equal their v10 sha256; the API list equals the sha256 above; the 674 keys join one-to-one | a changed byte in the API list must fail |
| G26b same forecasts | on all 674, the three comparisons reproduce the committed registered values to 1e-9 | a shifted forecast must fail |
| G26c same rules | the E13 sample, re-audited through this generator, reproduces the committed E13 results pair for pair | a changed club threshold must fail |
| G26d previous-team rule is not vacuous | the share of arrivals whose previous team matches a source club is at least twice the share after the previous-team strings are shuffled across arrivals (seed 20261113). If not, the previous-team evidence is **not used** for CONFIRMED, and the paper says so | "HAPOEL TEL AVIV" against "MACCABI TEL AVIV" must not match; "GRAVELINES" against "BCM GRAVELINES DUNKERQUE" must match |

## Threats and their controls

| Threat | Control |
|---|---|
| Reused 2020–2025 outcomes | exploratory label; P1 and P1-late stay the confirmatory tests |
| Rules bent toward a clean result | every rule and threshold is fixed above; no hand review; classes are computed before any subset is scored |
| A weak check passed off as confirmation | NAME ONLY is a separate class and is reported; G26d can switch the previous-team evidence off |
| A null read as "no effect" | subset nulls are worded "not detectable at this n" with n |
| A result that weakens a paper claim | reported in the main text; reported to Amir before any writing |

## Scope boundary

Nothing pinned changes. E26 is implemented in a new dated generator with a committed report script. Retained runs go to the project's run archive from committed code. The pinned API list holds names, clubs and previous teams only; birthdates were not kept.

## Timeline

| Date | Step |
|---|---|
| 12 Nov | this amendment approved and pushed alone |
| within one working day | E26 result |
| 19–20 Nov | paper re-rendered; analysis lock |
