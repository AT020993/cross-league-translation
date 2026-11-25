# Amendment 22 to the SSAC27 full-paper pre-registration: the league-changes sensitivity with the stayer forecast also fitted only on earlier seasons (E33)

**Approval record.**

| | |
|---|---|
| Amends | `docs/research/sloan-full-paper-preregistration-2026-11-03.md`, as amended through Amendment 21. It adds one exploratory analysis, E33, beside sensitivity (7) of Amendment 14, and the words the paper may print for it. Everything else in those amendments holds |
| Written | 2026-11-19, **after the league-changes test (E30) was scored and all its sensitivities were seen**, and after render 45 of the paper said in its main text that the stayer forecast of sensitivity (7) uses all seasons. Before the generator of E33 was written, before any estimate of E33 was computed, and before any 2026-27 statistic was read |
| Approved by | Amir, "Yes", 2026-11-19, in answer to a question that named this amendment, its analysis E33, its push alone on its own branch and its squash-merge into `main`; and "Yes" to a second question that named its row in the public hash list. Earlier the same day he had answered "do your recommendations" to a recommendation to run this check if it could start by 21 November |
| Basis | committed and pushed **alone**, before the generator is written and before any outcome is read for this analysis. Nothing below may be relaxed after the run (METHOD.md §8) |

This amendment adds one analysis on outcomes that have already been read. **E33 is exploratory and is labelled so wherever it is printed.** It changes no registered result, sentence or case of E30.

## Why this exists, in plain words

The paper tests its league table on players who changed domestic league. One registered check, sensitivity (7), answers the worry that the table was fitted on the same seasons it is tested on: for league changes of 2020-21 to 2025-26 it refits the table only on arrivals before the season of each move. The slope is 0.79.

That check has one remaining overlap in time. Each league changer is compared with a forecast built on players who stayed in their league, and that stayer forecast is fitted once, on all seasons, including seasons after the move. Render 45 of the paper now says so. E33 closes the overlap: it fits the stayer forecast, too, only on seasons before each move, on the same league changes, and reports how much the slope moves.

The idea and a first draft of the protocol came from the Codex review of 19 November 2026. This amendment keeps its design and changes three things, each named in "Analysis": the bootstrap uses the player sample of E30, so that sensitivity (7) is reproduced exactly; the difference between the two slopes gets its own interval; and the sentences the paper may print are fixed here, before the run.

## What has already been seen (exposure disclosure)

* **E30 has been scored**, once (retained run `league-changes-score-01`, 18 November 2026): case "Clear"; slope 0.77 (95% interval 0.69 to 0.84) on 3,423 league changes by 1,649 players.
* **Sensitivity (7) is known**: slope 0.79 (interval 0.68 to 0.88) on 2,083 league changes. So are the other seven sensitivities, the leave-one-league-out slopes, the slopes by direction and the comparison with the 2015 table.
* **The outcomes that E33 uses have been read.** They are the column `rate_to` of the committed file of scored league changes. E33 reads no new outcome.
* **No estimate of E33 exists.** The Codex draft states that none was computed. The author of this amendment has fitted no stayer forecast on a subset of seasons. Only row counts were read to write this text (below).
* **No result of the frozen 2026-27 test exists**, and no 2026-27 statistic has been read.

## Pinned inputs

All under `docs/research/artifacts/sloan-fullpaper-league-changes-2026-11/`. Each sha256 was recomputed on 19 November 2026 and equals the value in the named receipt.

| File | Receipt | sha256 |
|---|---|---|
| `e30_frozen_league_changes.parquet` | `freeze-receipt.json` | `2df696debc8567d9468844384c259e2289d6d1d985d7cbe4c7930bd7bf85b722` |
| `e30_stayer_pairs.parquet` | `freeze-receipt.json` | `afdda9226c671e9ef774297097ad5507ed83a72d4d06d4a98cdc26f8fb0997b6` |
| `e30_scored_league_changes.parquet` | `score-receipt.json` | `03d5355dd4c8127b9130dc2c7bfd7c9d782e14cca7c1e9bc83ac2fc0a9dbfaa4` |
| `e30_summary.json` (the retained values that E33 must reproduce) | `score-receipt.json` | `f1df4c23899c959fc7458caff0e5f2ec8ae071517b29be491a41383f946319dc` |

Row counts read for this text (no outcome was read): 2,083 league changes carry a refitted table gap, in arrival seasons 2020 to 2025 (312, 360, 374, 363, 344, 330), by 1,165 players, with no repeated key. The stayer pairs whose outcome season is before each arrival season number 3,578, 4,491, 5,429, 6,331, 7,263 and 8,219. The players of all league changes and all stayer pairs together number 3,577.

## Specification

| Field | Registered choice |
|---|---|
| Unit | One league change, as in Amendment 14. Each move has equal weight. A player can have several moves |
| Population | The 2,083 league changes of sensitivity (7): arrival seasons 2020 to 2025, with the table gap `g_refit` refitted only on arrivals before the season of the move. No other row is used in the second step |
| Estimator | Step 1, for each arrival season t: ordinary least squares of the stayers' next-season rate on an intercept, x, h and a, on stayer pairs whose outcome season is before t. Step 2: ordinary least squares, with an intercept, of the league changers' unexplained change on `g_refit`, over the 2,083 moves together |
| Null | Slope zero; the registered direction is positive. For the difference from sensitivity (7): zero |
| Filter | Rows of the frozen file with a finite `g_refit`. The league, games, partial-season and missing-history rules of the frozen file are kept as they are |
| Key | `player_name` × `season_from`, the key of E30. The scored file is joined to the frozen file one to one on it |
| Uncertainty | The bootstrap of E30: players resampled (2,000 draws, generator `numpy.random.default_rng([20261117, 0])`), over the same 3,577 players, every stayer forecast refitted in every draw; percentile interval, 2.5 and 97.5 |

## Analysis

### Step 1: the stayer forecast with a cutoff

For each arrival season t from 2020 to 2025, fit the stayer forecast of Amendment 14 (next-season rate on an intercept, last season's rate x, the earlier career rate h and the flag a = 1[x > h]) on the stayer pairs whose outcome season is **before** t. Apply the fit of season t to the league changers who arrive in t. The unexplained change is e = (rate in the new league) − (this forecast). The inputs x, h and a are taken from the frozen file; only `rate_to` comes from the scored file.

### Step 2: the slope

**E33, the one result.** The slope b of e on `g_refit`, with an intercept, over the 2,083 league changes. This is sensitivity (7) with one thing changed: the seasons the stayer forecast may use.

### The difference, in the same draws

In every bootstrap draw the generator also refits the stayer forecast on all seasons and recomputes sensitivity (7) on the same resampled players. The difference d = b − (sensitivity (7)) is taken draw by draw, and its 95% interval is the percentile interval of those 2,000 differences. Two intervals that overlap say little about a difference; this interval says it directly.

**What the difference could detect.** 2.80 times the standard deviation of the 2,000 differences (80% power, two-sided 5%). It is printed beside any statement that the two slopes are not distinguishable.

### One secondary result (appendix only)

A stayer forecast fitted only on earlier seasons can sit too high or too low in a later season as a whole. To show whether any difference is such a shift in level, the second step is repeated with one intercept per arrival season in place of the single intercept, under both stayer forecasts. Both slopes are printed with their intervals in the appendix table, whatever they show. They decide nothing.

### Changes from the Codex draft

1. **The bootstrap resamples the players of E30** (all 3,577), not only the players who have a selected move or an eligible stayer row. With the same players and the same generator stream, the draws of sensitivity (7) are the draws of the scoring run, so its estimate and its interval must come out equal to the retained values. That is gate G33c.
2. **The difference has its own interval** (above).
3. **The sentences are fixed before the run** (below).

## What was expected, written before the run

The stayer forecast has four coefficients and its smallest training set holds 3,578 pairs. The author expects the slope to move by less than 0.05 in either direction. This is an expectation, not a result, and nothing below depends on it.

## What the paper may say

Let b be the E33 slope with interval [L, U], and d the difference from sensitivity (7) with interval [dL, dU] and detectable difference m.

| Case | Rule | Wording, printed after the sentence on sensitivity (7) |
|---|---|---|
| Same | L > 0 and dL ≤ 0 ≤ dU | "With the stayer forecast also fitted only on seasons before each move, the slope on the same N league changes is b (interval L to U), not distinguishable from that sensitivity (difference d, interval dL to dU; a difference of m would have been detected with 80% power), which is not the same as equal." |
| Different | L > 0 and the interval of d excludes zero | "With the stayer forecast also fitted only on seasons before each move, the slope on the same N league changes is b (interval L to U), lower [higher] than that sensitivity by \|d\| (interval dL to dU)." |
| Not above zero | L ≤ 0 | "With the stayer forecast also fitted only on seasons before each move, the slope on the same N league changes is not clearly above zero (b, interval L to U)." |

In every case the same sentence or the next says: "This check was added after the result of the league-changes test was seen and is exploratory [Amendment 22]."

* **The number is printed whatever it shows**, in the main text, in Results, in the paragraph "What was unseen".
* **Words the paper does not use for E33:** "confirms", "robust", "validated", "unchanged", "equivalent". The case Same licenses "not distinguishable", with the detectable difference beside it.
* **Placement.** Results, as above. One row in the appendix table of the league-changes slopes, labelled as added after the result. One sentence in Appendix M with the two slopes of the secondary result. E33 does not enter the abstract, the title, Figure 1 or the conclusion.
* **The first page.** In the case Same, and in the case Different with a higher slope, the first page is unchanged: the paper does not strengthen its first page from an exploratory check. In the case Different with a lower slope, and in the case Not above zero, **Amir is told before any text is written**; the Results sentence is printed as registered here; the introduction's clause on sensitivity (7) adds "(b when the stayer forecast is also fitted only on earlier seasons)"; and the paragraph "League changes" in Limitations gives the same number. Any further change to the abstract, Figure 1 or the conclusion is Amir's decision and needs a further amendment.
* E33 changes no registered sentence about E30, the 674 arrivals, the older arrivals or the frozen 2026-27 test. The registered case of E30 ("Clear") and its sentence stand in every case.

## Limits stated in advance

* E33 is a further reading of outcomes that have been read. It is exploratory.
* It removes overlap in time. It does not remove players who appear both among the arrivals that fit the table and among the league changers, and the paper does not say that it does (Amendment 19, rule 8).
* The interval holds the refitted table values fixed, as the interval of sensitivity (7) does.
* The stayer forecast for the first season, 2020-21, rests on four seasons of stayers; for the last on nine.
* The limits of E30 stand: league changers are not a random sample, role and minutes change with a move, players are linked by name, and the box scores are the raw Proballers files.

## Gates and negative controls

| Gate | Pass rule | Negative control |
|---|---|---|
| G33a inputs | every pinned file equals its sha256 | a changed byte must fail |
| G33b same rows | the join of the frozen and the scored file is one to one on the key; the selected rows number 2,083 in six arrival seasons with the counts above; the frozen and the scored file agree on season and leagues for every row | a row removed from either file must fail |
| G33c the code reproduces the registered sensitivity | with the stayer forecast fitted on all seasons, the generator returns the estimate and both ends of the interval of sensitivity (7) equal to the retained values (absolute difference below 10⁻⁹) | with another seed the ends of the interval must differ |
| G33d the cutoff holds | for every arrival season t, the latest outcome season among the stayer pairs used in its fit is before t; recorded per season | a fit that includes season t must be refused |
| G33e the code recovers a planted slope | on made-up outcomes built as the cutoff stayer forecast + 1.0 × `g_refit` + noise, the slope is within 0.05 of 1.0; with 0.0 × `g_refit` the interval includes zero | `g_refit` shuffled across the made-up moves must give an interval that includes zero |

G33a, G33b, G33d and G33e are run before the real outcomes are used. If any gate fails, E33 stops, nothing is printed in the paper, and Amir is told.

## Threats and their controls

| Threat | Control |
|---|---|
| A flattering check chosen after the result | the check was proposed because of a limit the paper already states; the rows, the estimator, the bootstrap and the sentences for every case are fixed here before any estimate; it is labelled exploratory wherever printed and kept off the first page unless it weakens the result |
| The comparison of two procedures is made by eye | the difference has its own interval from the same draws, and the detectable difference is printed |
| A code difference, not the cutoff, moves the slope | G33c: the same code path reproduces sensitivity (7) to 10⁻⁹ |
| A leak of later seasons into the stayer forecast | G33d, with its negative control |
| A level shift of an out-of-time forecast mistaken for a slope | the secondary result with one intercept per arrival season, printed under both stayer forecasts |
| Wrong name links; selection into moves; a partial last season | unchanged from E30 and stated as limits; they act on both slopes alike |
| A second run after a disappointing first | the stop rule |

## Stop rule

E33 is run once, in one retained run, from a committed generator that reads only the pinned files. A failed run is kept and reported; it is not repeated with other rules. No further variant of this check (other seasons, other cutoffs, other stayer forecasts) is run for this paper.

## Scope boundary: nothing pinned changes

No registered analysis, estimate, interval, threshold, forecast, frozen file or sentence is changed. The generator of E30 is not edited. The public reproduction command does not recompute E33, because the scored rows and the stayer pairs are not published; it checks the E33 files by hash. Amendment 19, rule 12 stands for the frozen test.
