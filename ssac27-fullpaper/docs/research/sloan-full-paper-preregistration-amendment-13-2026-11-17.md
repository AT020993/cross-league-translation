# Amendment 13 to the SSAC27 full-paper pre-registration: the order of the claims on the first page

**Approval record.**

| | |
|---|---|
| Amends | `docs/research/sloan-full-paper-preregistration-2026-11-03.md`, as amended on 2026-11-04, 2026-11-05, 2026-11-11, 2026-11-12, 2026-11-16 and 2026-11-17 (Amendments 1 to 12) |
| Written | 2026-11-17, before the paper text below was written |
| Approved by | Amir. On 17 November he chose "A. Order by strength" from three options put to him after a review of the paper by three simulated judges |
| Basis | committed and pushed **alone**, before any implementation. Nothing below may be relaxed after a result is seen (METHOD.md §8) |

Everything in the 3 Nov pre-registration and in Amendments 1 to 12 stands. This amendment adds **no analysis and no number**. It fixes the order in which the paper's abstract, introduction and conclusion state claims that are already committed, and the words allowed for one of them. It changes no registered analysis, threshold, model, population or licence, and no registered sentence.

## Why this exists, in plain words

1. **The first page leads with the paper's least secure number.** Since 16 November the abstract and the introduction lead with what the league numbers are worth: 0.065 EFF/36 once the destination is known (E28, Amendment 9). That comparison is exploratory. Its estimate is below the smallest difference the sample detects with 80% power (0.073). Its interval includes zero for EuroCup arrivals alone and in five of six seasons. On the 180 older arrivals it did not repeat, and weighted by playing time it reversed.
2. **One comparison read the same on 2020–2025 and on the older seasons.** Translation's increment on top of the league-aware forecast is not distinguishable from zero in both: −0.002 (interval −0.028 to 0.024) on the 674 arrivals, and −0.015 (interval −0.031 to 0.002) on the 180 older arrivals, whose forecasts were fixed before any outcome was joined. It is the only one of the three registered comparisons of Amendment 7 with the same reading in both periods.
3. **A reader should meet the claims in the order of their support.** Three simulated judges read the paper of retained run `paper-render-33` on 17 November. All three wrote that the lead number is the weakest in the paper; two named a re-ordering as the most valuable change. Their reading is an opinion about presentation and is not evidence. The reasons in points 1 and 2 are in committed results and do not depend on it.
4. **The frozen 2026-27 test already has a read-out for the league numbers, and the main text does not say so.** Amendment 8 registered read-outs S1 to S5 on 16 November, before scoring. The main text names only the three registered directions about translation.

## What has already been seen (exposure disclosure)

* **Every number this amendment orders** is committed and printed in the paper of `paper-render-33`: E7 and E9 (3 November), E27 (13 November), E28 (16 November).
* **The judges' reports.** I read all three before writing this. They saw the manuscript and its five figures and nothing else.
* **The version of the older-seasons test that includes Spain's ACB** is computed and withheld (Amendment 7). I checked its *reading* for translation's increment before writing rule 2 below, because a sentence about "both periods" must not depend on which version is printed. The reading is the same in both versions (interval includes zero, inside the margin). No number of the withheld version is used or printed.
* **No 2026-27 statistic** has been read.

## Specification

| Field | Registered choice |
|---|---|
| Unit | One arrival: player × destination season |
| Population | The 674 benchmark arrivals of 2020–2025, and the older-seasons arrivals in the printed version (180) |
| Estimator | None is computed. The ordered claims use results already committed: the league biases (E24, E18b), the League Equivalents (E9), translation's increment on top of the league-aware forecast as a paired difference in mean absolute error (E7, E27), and G_D of Amendment 9 (E28) |
| Null | Zero for each paired difference |
| Filter | None beyond each population's registered rules |
| Key | The registered key of each population |
| Uncertainty | The 95% intervals already committed for each result. Nothing is computed again |

## The rules

### 1. Order on the first page

In the abstract, in the second paragraph of the introduction and in the conclusion, the claims come in this order:

| Order | Claim | Source |
|---|---|---|
| First | A forecast that does not know the source league misjudges whole leagues, and one number per league flattens that pattern; the League Equivalents line | E24, E18b, E9 |
| Second | Once a forecast has the league numbers, translation's increment is not distinguishable from zero, on 2020–2025 and on the older seasons | E7, E27 |
| Third | What the league numbers are themselves worth on 2020–2025, with its status | E28 |

The third claim is stated once in each of these places. Amendment 10's rule 3 holds unchanged: the seasons are named, and the same paragraph gives the older-seasons reading. In the introduction and in the conclusion the same paragraph also says that the frozen 2026-27 test has a registered read-out for this gain (Amendment 8, S2).

### 2. The words for "both periods"

The paper may say that a result held, or read the same, in both periods **only for translation's increment on top of the league-aware forecast**, and only in this form: the 2020–2025 estimate with its interval, then the older-seasons estimate with its interval and the number of older arrivals, described as "not distinguishable from zero", "adds nothing detectable" or "no detectable gain".

* The sentence is allowed only while both intervals include zero. If either excludes zero in the committed files (for example after a change of the printed version under Amendment 7), the sentence is withdrawn and the case goes to Amir.
* The paper does **not** say that the league numbers "match" translation in both periods. On the older seasons the registered head-to-head reading is that the test cannot show a match at that n.
* The paper does **not** say that the gain from the league numbers held in both periods. It did not.
* The older-seasons test covers two of the ten leagues, and the sentence or its paragraph says "180 older arrivals" (the number and the leagues of the printed version), never "older seasons" without the count.

### 3. The margin on the first page

The abstract and the introduction state translation's increment by its estimate and interval. They do not carry the claim by the word "matches" or by the ±2% margin. The registered equivalence statement, its margin, the fact that the margin was set after the interval was seen, and the E28c sentence (the margin as a share of what the source league adds) stay where they are in Results. The conclusion keeps its sentence with "matches the measured benefit of translation factors", scoped to the arrivals of 2020–2025 as it is now.

### 4. What leaves the abstract

To make room and to keep one claim per sentence, these leave the abstract and stay in Results unchanged: translation's gain against history alone (3.096 to 2.935), Italy's league bias, the shares of cross-league pairs ordered correctly, and the top-10 clause.

The sentence "Weighted by playing time, translation's gain over history is not clearly above zero" qualifies the gain against history. It leaves the abstract together with the statement it qualifies. It stays in the introduction and in Limitations, word for word. **This reverses a standing decision from the first week of November**, made when the abstract led with that gain (that the qualification is visible in the abstract); Amir is told so in the report on this change and can restore the sentence.

The abstract keeps: the sentence that these seasons were examined before registration, the older-seasons clause of Amendment 10, the clause that the league numbers need only past arrivals, and the frozen-test sentence with the ending fixed by Amendment 8.

### 5. The limits, each in its required places

The older-seasons reading of the league numbers appears in the abstract, the introduction (inside the sentence on the gain), Results, the club section, Limitations and the conclusion. The introduction's separate qualification on it is removed, because the gain sentence now carries it. The introduction's paragraph of qualifications keeps its other two: the forecast level, with the weighted level that Amendment 12 places there, and the minutes-weighted reading of translation's gain. No limit is removed from Results, the club section, Limitations or the appendix.

### 6. The frozen-test paragraph names the secondary read-outs

The paragraph on the 2026-27 test says that five secondary read-outs were registered on 16 November, after the freeze and before scoring, and that two of them test the league numbers themselves: the league-aware forecast against the forecast that knows only the destination (S2), and the ordering of cross-league pairs (S4). It repeats what Amendment 8 states: neither S1 nor S2 is expected to be detectable in November. It gives the 2020–2025 estimate that S2 looks for, from the committed E28 output. No read-out is added or changed.

### 7. After the frozen test is scored

The abstract's last sentence follows Amendment 8. The order of the first page does not change automatically with the result. If a registered contrast fails to replicate, or if the interval of S2 excludes zero in either direction, the first page goes to Amir before any rewriting.

## A clarification of Amendment 12

Amendment 12's table of threats describes the gap guide's reading for small forecast gaps as "close to a coin flip". The registered E20 sentence governs: for gaps below 1 EFF/36 the higher forecast was the better player in 54.5% of pairs (interval 52.0% to 56.7%), which is distinguishable from a coin flip. The paper prints the registered sentence and does not use the looser phrase. This was already so in `paper-render-33`.

## Not part of this amendment

* No new analysis, read-out, model, sample or figure. Figures stay byte-identical.
* No change to the title.
* The two further candidates raised by the judges (a rule for the step in the fitted equation; ordering accuracy for tier-1 against tier-3 pairs) are not started. Each would need Amir's pick and its own dated amendment.

## Threats and their controls

| Threat | Control |
|---|---|
| Re-ordering after a review reads as choosing the story after the fact | the order is fixed by a rule stated here (support on outcome-blinded arrivals first, exploratory last); every claim keeps its number, interval and label; nothing is removed from Results or Limitations |
| "Both periods" stretched to claims that did not hold | rule 2 lists what may and may not be said; the renderer refuses the sentence if an interval excludes zero |
| The older test read as broad confirmation | the count of arrivals and the two leagues stay in the sentence or its paragraph; Limitations is unchanged |
| A shorter abstract that hides a limit | the abstract keeps the exploratory sentence and the older-seasons clause; the reversal of the earlier decision is disclosed to Amir |
| The S2 read-out presented as a coming confirmation | the paragraph says it is not expected to be detectable; equivalence is never claimed from the frozen test |
| The withheld version contradicting the sentence | its reading was checked (same reading); no withheld number is printed; rule 2 withdraws the sentence if the printed version's interval excludes zero |

## Scope boundary: nothing pinned changes

No registered analysis, file, forecast or licence is changed. No model is refitted and no outcome is read. Every number in the re-ordered text is already in a committed file and in the number manifest.

## Change record

* **17 November 2026, first push:** commit `6ea7402`, 09:55:27 UTC, sha256 `472eff24264dabdf01b21558ae377902d43ba246487b18cd4d83a77edb7be7c2`. The paper text was written after this push.
* **17 November 2026, second commit:** the Specification table above and this record were added, because the repository's check for research notes requires a Specification block and the first version had none. The table restates what the text already said (the populations, the results that are ordered, and that nothing is computed). No rule, wording or threat was changed, added or removed. This second commit was made after the paper text had been drafted.
