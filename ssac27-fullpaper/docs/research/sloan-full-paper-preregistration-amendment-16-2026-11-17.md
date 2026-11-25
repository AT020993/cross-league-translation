# Amendment 16 to the SSAC27 full-paper pre-registration: the paper is built around its league table; first-page rules for each outcome of E30

**Approval record.**

| | |
|---|---|
| Amends | `docs/research/sloan-full-paper-preregistration-2026-11-03.md`, as amended through Amendment 15. It replaces rule 1 and rule 4 of Amendment 13 (the order of the first page; what leaves the abstract). Every other rule of Amendment 13 holds |
| Written | 2026-11-17, before E30 was implemented and before any text below was written into the paper |
| Approved by | Amir, "Yes, accept as written and push", 2026-11-17, in answer to a question that named this amendment and its push |
| Basis | committed and pushed **alone**. Nothing below may be relaxed after a result is seen (METHOD.md §8) |

This amendment adds no analysis and computes nothing. It fixes how the paper presents results that are committed, and results of E30, E31 and the frozen test that do not exist yet.

## Why this exists, in plain words

1. **The paper leads with a test of someone else's method.** Three rounds of simulated judges (nine readings) rated its novelty the same, whatever the order of the first page. A comparison on 17 November with 24 Sloan basketball papers that advanced in 2019-2026 found that 23 lead with a new thing to use and none leads with an evaluation (one reader, first two pages, Figure 1 and conclusion of each; provisional). The paper has such a thing, its league table, and presents it in the fifth section.
2. **The first page must be fixed before the new result is known.** E30 can come out clear, limited, null or against the table. If the wording were chosen afterwards, a reader could not tell a finding from a framing. So the first page for every outcome is fixed here.
3. **The question of the submitted abstract stays.** What league translation adds, tested on the same players against forecasts that already know the leagues, remains a full section with every submitted number.

## What has already been seen (exposure disclosure)

* **Every committed result this amendment orders** is printed in the paper of retained run `paper-render-38`.
* **No result of E30, E31 or the frozen 2026-27 test exists.**
* **The judges' reports and the comparison with advancing papers** were read before this was written. They are opinions and a provisional survey, not evidence about basketball.

## Specification

| Field | Registered choice |
|---|---|
| Unit | One arrival (player × destination season) for committed results; one league change for E30 |
| Population | The populations of the results being ordered: the 674 arrivals of 2020-2025, the 180 older arrivals in the printed version, the league changes of E30, the frozen 2026-27 newcomers |
| Estimator | None is computed. The ordered claims use committed results (E24, E18, E9, E7, E27, E28) and the registered results of E30, E31 and Amendment 8 |
| Null | As registered for each result |
| Filter | None beyond each population's registered rules |
| Key | The registered key of each population |
| Uncertainty | The intervals committed or registered for each result. Nothing is computed again |

## The rules

### 1. The name

The league table is called the **European League Equivalents** in the title or subtitle, the abstract, Figure 1 and the section that presents it. "League numbers" remains the plain term for the ten fitted terms. Wherever the line "a 16 in Spain's ACB reads like about a 19 in Germany, Lithuania or VTB" appears, the same sentence or the next carries the condition "when career history equals the domestic rate".

### 2. The title

The title names the league table and keeps the submitted question in view. It is chosen from these two forms by the case of E30 (Amendment 14):

| E30 case | Title |
|---|---|
| Clear; Positive with a named limit | "European League Equivalents: One Number per League, Tested on League Changes It Was Never Fitted To" |
| Positive but not separable from chance; Null; Against; or E30 not run | "European League Equivalents: What One Number per League Adds to European Basketball Forecasts, and What Translation Factors Add on Top" |

The words "never saw" are not used anywhere: seasons after a league change are inputs to the paper's forecasts.

### 3. Order on the first page

In the abstract, the second paragraph of the introduction and the conclusion, the claims come in this order:

| Order | Claim | Source |
|---|---|---|
| First | The problem and the product: a forecast that does not know the source league misjudges whole leagues; one number per league flattens that; the Equivalents line with its condition | E24, E18b, E9 |
| Second | The test on league changes, in the registered wording of its case, whatever the case | E30 |
| Third | Once a forecast has the league numbers, a translation factor adds nothing detectable, on 2020-2025 and on the 180 older arrivals (rule 2 of Amendment 13 holds) | E7, E27 |
| Fourth | What the league numbers are worth on the arrivals of 2020-2025, once, with its seasons, the older-arrivals reading (Amendment 10) and the registered read-out S2 | E28 |
| Fifth | Status and the frozen test: these seasons were examined before registration; the frozen-test sentence with the ending fixed by Amendment 8 | — |

* **If E30 is Null or Against**, the second claim is stated as plainly as a Clear one would be, in the abstract, the introduction, the conclusion and Limitations. The abstract then does not call the table "tested" or "validated".
* **If E30 is not run** (Amendment 14's stop rule), the second claim is omitted and the paper says nothing about league changes.
* **The published table** (E31) is stated in Results. It enters the abstract in one clause only if its registered wording is "more accurate than the paper's league numbers" or "not distinguishable", because either changes what a reader should take from the table.

### 4. What the abstract carries

The abstract carries at most eight numbers, each with its unit, and one sentence of status. It keeps: the Equivalents line with its condition; the E30 sentence; translation's increment on 2020-2025 with its interval; the clause on the 180 older arrivals required by Amendment 10; the sentence that these seasons were examined before registration; and the frozen-test sentence. Everything else stays in Results, word for word where a registration fixes the words.

### 5. Limits

Each standing qualification is stated in the introduction or Results at the result it limits, and once in Limitations: the forecasts run low (E18a, Amendment 3); weighted by playing time, translation's gain over history is not clearly above zero; the gain from the league numbers did not carry back to the older arrivals (Amendment 10); the table describes the players clubs sign and holds along the profile where career history equals the domestic rate. No registered sentence is removed. The introduction no longer carries a separate paragraph of cautions.

### 6. What the paper says about itself

* The sentence in Related work that the contribution is "the European basketball benchmark ... rather than a new estimator or league-network method" is replaced by a plain statement of what is offered: a named league table for European basketball arrivals, the same-player benchmark of translation factors against it, and its tests on league changes and on frozen forecasts. The paper still says that one number per league is an old idea from baseball and hockey and that the estimator is a ridge regression.
* The paper does not say that clubs use translation factors. It may say that analysts and vendors publish or advertise league adjustments, with the sources, and that no public test of them on European arrivals was found in a bounded search.
* The paper says "the first" of nothing.

### 7. Real names and figures

* The two invented candidates stay as the explanation of how to use the table. Named players appear only under E32 (Amendment 15), after scoring.
* The main text may carry up to ten figures. Every added figure plots committed or registered values; a figure adds no number that is not in a committed summary. The detail of the six factor recipes, the flexible model and the pair-ordering figure may move to the appendix with a pointer, except sentences that a registration places in the main text.

### 8. Explaining the size of the gain

The paper adds a short passage, from committed numbers only, on why a league bias of about one EFF/36 buys a small average gain: individual forecast error is several times larger than any league number, so most forecasts change little, and the league numbers matter where two candidates from different leagues are compared (the table changes 8.5% of cross-league comparisons and is right on 57.7% of them, E21). The passage states no new estimate.

## Gates

* **G16a.** The renderer selects the title and the E30 sentence from the committed E30 summary by the case rule of Amendment 14, and refuses to render if the abstract contains "tested", "validated" or "never fitted to" while the case is Null, Against or not run. **Negative control:** a test with a made-up Null summary and the Clear title must fail.
* **G16b.** The tests that pin registered sentences (E12, E18a, Amendment 7, Amendment 10, the frozen-test endings) pass unchanged.

## Threats and their controls

| Threat | Control |
|---|---|
| Framing chosen after the result | titles, order and wording fixed here for every case |
| A null hidden behind a product name | rule 3: a Null or Against result is on the first page; gate G16a |
| Cautions lost in the move to Limitations | rule 5; gate G16b |
| A stronger claim about the table than the evidence | rule 1 (condition), rule 6, and the licences of Amendment 14 |

## Scope boundary: nothing pinned changes

No analysis, number, figure value or registered sentence is changed by this amendment. Amendment 13's rules 2, 3 and 5 onward hold.
