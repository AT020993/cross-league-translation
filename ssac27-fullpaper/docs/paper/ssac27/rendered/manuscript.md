---
title: "European League Equivalents: One Number per League, Tested on League Changes It Was Never Fitted To"
track: "Basketball"
paper_id: "47"
---

## Abstract

European clubs recruit for EuroLeague and EuroCup from domestic leagues whose box scores are not directly comparable. This paper sets the established adjustment, a translation factor, against a plainer benchmark that needs only past arrivals: one number per source league. These are the European League Equivalents, in box-score efficiency per 36 minutes (EFF/36): when career history equals the domestic rate, 16 EFF/36 in Spain's ACB gives the same forecast as about 19 in Germany, Lithuania or VTB. In a test registered and frozen before its outcomes were read, 1,649 players who changed domestic league moved in the direction the table implies, at about three quarters of its size (slope 0.77, 95% interval 0.69 to 0.84). On these league changes and the 2020–2025 arrivals, the paper's league numbers and a league table printed in 2015 are not distinguishable; this paper adds that registered test and an interval for each league number. On those arrivals, examined before registration and so exploratory, a translation factor adds nothing detectable on top of the league numbers: −0.002 EFF/36 (95% interval −0.028 to 0.024). Once the destination is known, knowing the source league improves the forecast slightly for the 2020–2025 arrivals; on 180 older arrivals from two leagues it did not. Forecasts frozen on 3 November 2026, after the season began but before outcome inspection, were scored once on 2026–27 newcomers. That test, separate from the test on league changes, is inconclusive: 7 newcomers without a forecast may be in the frozen file under another spelling, more than the 5% of the 94 joined newcomers that was allowed in advance.

## Why the question matters

A club comparing players from different domestic leagues must ask what a box score means in continental basketball. The established answer is a translation factor, an adjustment between two competitions, typically estimated from players observed in both [1–10]. A bounded search in English found no public test in basketball that compares a forecast with and without a league adjustment on what players arriving in European competitions went on to do (Related work). This paper makes that comparison, scoring each pair of forecasts on the same players, and sets the translation factor against a plainer benchmark: one number per source league.

**The benchmark and its test.** A forecast that knows the destination but not the source league underrates arrivals from Spain and Italy and overrates arrivals from Germany (Figure 2); **one number per source league** flattens that pattern. These are the **European League Equivalents** (Figure 1, Table 1): when career history equals the domestic rate, 16 EFF/36 in Spain's ACB gives the same forecast as about 19 in Germany, Lithuania or VTB. In a test registered and frozen before its outcomes were read, 1,649 players who changed domestic league moved in the direction the table implies, at about three quarters of its size (slope 0.77, 95% interval 0.69 to 0.84). The slope is the average change in a mover's rate, beyond the forecast for a player who stays in his league, per unit of change that the EuroCup Equivalents predict; a slope of 1 would mean the table's size is exactly right. These players made 3,423 league changes; the slope is lowest without Spain (0.57), and 0.79 with the table refitted only on arrivals before the season of each move. With the ten table values redrawn as well, the slope's interval is 0.43 to 0.93 (an approximation, read for its width only).

**What a translation factor adds.** A translation factor does help a forecast that ignores both leagues, by 0.161 EFF/36. Weighted by playing time, translation's gain over history is not clearly above zero (0.098, 95% interval −0.003 to 0.198). On top of the league numbers, a translation factor adds nothing detectable: −0.002 EFF/36 (95% interval −0.028 to 0.024) on the arrivals of 2020–2025, and −0.015 (interval −0.031 to 0.002) on 180 older arrivals from seasons no model saw (the first is shown in Figure 3).

![Figure 1. The European League Equivalents and their test. Left: domestic EFF/36 equivalent to 16 in Spain when career and domestic rates coincide (filled: EuroLeague; open: EuroCup; lines: 95% intervals; n: training arrivals, 2017–2025); leagues inside a tier are not distinguishable, which does not prove that they are equal. Right: the 45 league pairs of the test on league changes: half the difference in mean unexplained change between opposite moves, against the predicted gap (orange: pairs with Spain). The line is the registered slope from all league changes with its 95% interval, drawn through the origin; it is not a fit to these points. The 45 points come from ten numbers and are not 45 independent tests.](figures/fig1_equivalents.png)

**What a club can do with the table.** Candidates from different leagues can be compared by entering each candidate's league number in the fitted equation (Table 1; the equation is given in the section *What a club can use*): of two EuroCup candidates who each averaged 16 EFF/36 last season and across their earlier careers, the one from Germany's BBL projects at 14.3 EFF/36 and the one from Spain's ACB at 16.3, a 2.02 EFF/36 gap that comes entirely from the two league numbers. The forecast for a single player has a typical 80% error band of ±4.8 EFF/36, wider than that gap, which argues for scouting alongside the comparison.

**What these results do not show.** The table is for comparing players, not for forecast levels: the forecasts fall below the outcomes, by 0.47 EFF/36 on average for the league-aware forecast, the one that uses the league numbers, and by 0.96 when weighted by playing time. On the arrivals of 2020–2025, once the destination is known, knowing the source league improves the forecast by 0.065 EFF/36 (interval 0.014 to 0.117), about 2% of the error of a forecast that knows only the destination; on 180 older arrivals from two leagues it did not improve the forecast, and the frozen 2026–27 test carried a registered read-out for this gain and is inconclusive. These seasons were examined before registration, so the evidence is exploratory.

## Data and methods

### Players and outcome

The unit of study is an arrival: a player who enters EuroLeague or EuroCup with at least eight domestic games in the preceding season, at least eight continental games in the arrival season, and no regular continental role in the preceding season. The 674 arrivals in destination seasons 2020–2025 comprise 194 EuroLeague and 480 EuroCup players. A season is named by the year in which it starts, so 2020–2025 stands for the six seasons 2020–21 to 2025–26. Domestic statistics come from Proballers, continental ones from the EuroLeague API. Without the rule of eight continental games there are 808 arrivals; the rule excludes 134 of them (16.6%), who played one to seven continental games.

The outcome, EFF per 36 minutes, is points, rebounds, assists, steals and blocks minus missed shots and turnovers. It is the EuroLeague's Performance Index Rating without fouls drawn, fouls committed and shots rejected. One EFF/36 is one more point, rebound, assist, steal or block, or one fewer missed shot or turnover, per 36 minutes; a made two-point basket adds two. Points per 36, Game Score per 36 [11] and EFF per 100 on-court possessions [12] serve as checks. The primary measure of accuracy is mean absolute error (MAE).

### Forecasts and estimation

The forecasts for each season are fitted on earlier seasons only; the fit behind Table 1 uses all 1,059 arrivals of 2017–2025 (the training arrivals). The first forecast uses last season's domestic rate x, the earlier career rate h and the flag a = 1[x > h]. The second adds the destination, and the third adds one number for each source league. We call these three the history-only, the destination-only and the league-aware forecast; each can be fitted without or with translation. The translation feature z scales x by a rate ratio for the source league and the destination, estimated from players observed in both in the same season (Appendix L gives the formulas).

$$\hat y = \beta_0+\beta_1 x+\beta_2 h+\beta_3 a + D(\gamma_0+\gamma_1 x)+\sum_{\ell}\delta_\ell\,\mathbf 1[\text{source}=\ell]\;\;(+\,\theta z)$$ {#eq:model}

D = 1 for a EuroLeague destination and 0 for EuroCup; δ is the source-league offset, the league number of the title. The ten league numbers are the conversion table (Table 1); a league's Equivalent restates its league number as the domestic EFF/36 that gives the same continental forecast as 16 in Spain's ACB when career history equals the domestic rate, once for a EuroLeague arrival and once for a EuroCup arrival. Ridge penalties λ = 1, 10 and 100 were fixed in advance, with λ = 10 primary.

### Comparisons and uncertainty

Every comparison uses the same players. Translation's gain is the paired reduction in absolute error [13, 14]:

$$\bar d=\frac{1}{n}\sum_{i=1}^{n}\Big(|e_i^{\text{without}}|-|e_i^{\text{with}}|\Big)$$ {#eq:gain}

Positive values favour translation. Intervals are 95%; arrival comparisons use player and club-season clustering [15] or a club-season bootstrap [16]. Printed differences are computed from unrounded values, so they can differ in the last digit from the difference of two printed numbers.

The analyses beyond the submitted abstract were registered before execution [17–27] (later registrations are cited where their analyses appear), except the few items marked as unregistered or descriptive where they appear. The 2020–2025 outcomes had already been examined, so registration does not make those results confirmatory [28]. We distinguish them from three tests whose outcomes no analysis had read when their rules were fixed: league changes, older seasons and 2026–27. The first page's wording and the reading of the slope per league-number gap were settled after the league-changes result (Appendix N).

## Results

### The test on league changes

Players also move between the ten domestic leagues. For a move from A to B, the table predicts B's Equivalent minus A's (EuroCup values). A strong season can precede both a move and a return toward a player's usual production. To account for that drift, we fit a forecast on players who stayed, using last season's rate, the earlier career rate and whether last season exceeded it. For each mover we subtract this forecast from his rate in the new league. We regress that residual on the predicted change, with an intercept and one observation per move; that slope is the one primary result. The test covers 3,423 league changes by 1,649 players. The season in the new league is called the arrival season of a league change; these arrival seasons run from 2016–17 to 2025–26. Every rule was registered before any outcome of a league change was read [29, 30]; the predictions were frozen and their hash published on 17 November 2026, and the outcomes were joined once, on 18 November 2026 (Appendix M).

The league table, fitted only on first continental seasons, predicted what happened to 1,649 players who changed domestic league: slope 0.77 (95% interval 0.69 to 0.84), where 1 would mean the table's size is exactly right. That is about 0.77 of the size the table implies. The interval comes from a bootstrap that resamples players and refits the stayer forecast in every draw. A random assignment of the ten league values to the ten leagues gave a slope at least as large in 1 of 10,000 draws. Adding the table's predicted change to the stayer forecast lowers its error on the league changers from 2.822 to 2.694 EFF/36 (difference 0.129, interval 0.078 to 0.180).

**What was unseen.** The table was not fitted to these league changes and not scored on them before this test. But the same seasons are inputs to the paper's forecasts, so the test and the fitted data overlap in time. One registered sensitivity removes that overlap in time: for the 2,083 league changes of 2020–21 to 2025–26, with the table refitted only on arrivals before the season of the move, the slope is 0.79 (interval 0.68 to 0.88). Only the league table uses this cutoff. The comparison forecast for players who stay pools stayer outcomes across all seasons. With the stayer forecast also fitted only on seasons before each move, the slope on the same 2,083 league changes is 0.78 (interval 0.68 to 0.88), not distinguishable from that sensitivity (difference −0.005, interval −0.018 to 0.006; a difference of 0.017 would have been detected with 80% power), which is not the same as equal. This check was added after the result of the league-changes test was seen and is exploratory [31]. The slope is an average relation over all league changes. The result is not a statement about league strength as such, says nothing about any single pair of leagues and is not a statement of equivalence. Players who change league are not a random sample, role and minutes change with a move, and players are linked across leagues by name; a wrong link pulls the slope towards zero in expectation if mismatches pair outcomes independently of the predicted change. Systematic mismatches can bias the slope in either direction. The box scores of this test are raw Proballers files, not the corrected corpus of the 674 arrivals.

**What the size means.** An Equivalent gap is the gap between two league numbers (Table 1) divided by 0.752, the weight of the fitted equation on a domestic rate when career history equals it (0.660 + 0.092 for a EuroCup arrival: a coefficient, not a measurement). Per EFF/36 of gap between two league numbers, a league changer's rate therefore moved by 1.02 EFF/36 (interval 0.92 to 1.12). This is arithmetic on the registered slope, stated after the result, and not a registered reading [32]; the registered reading, about 0.77 of the size the table implies, stands, and neither is a statement about league strength, about a single pair of leagues or about equivalence. The Equivalents are larger because they answer another question: which domestic line gives the same continental forecast, not what the same player produces in another league.

**Other registered checks (Table A24).** Leaving one league out at a time, the slope runs from 0.57 (without Spain; interval 0.48 to 0.66) to 0.88, and all ten intervals lie above zero. The sign is the same in both directions: 0.83 (interval 0.62 to 1.04) for moves to a league with a higher Equivalent and 0.63 (interval 0.44 to 0.81) for moves to a lower one. With the ten table values redrawn as well, the interval widens to 0.43 to 0.93 (an approximation, read for its width only; it does not decide the case [30]).

**A published league table on the same players.** A scale of competitions printed in 2015 for the NBA draft [8] can be scored the same way. On the 2,763 league changes of arrival seasons from 2018–19, with one coefficient per scale fitted on earlier league changes, the stayer forecast has a mean absolute error of 2.770 EFF/36 alone, 2.625 with the Equivalents and 2.642 with the 2015 table: a difference of +0.016 (interval −0.021 to 0.054), not distinguishable. On the 674 arrivals of 2020–2025 (exploratory [33]), the paper's league numbers and a league table printed in 2015 are not distinguishable (0.026, interval −0.008 to 0.060; a difference of 0.048 would have been detected with 80% power); the weighted value is 0.037 (interval −0.003 to 0.077). On neither sample can the two be told apart, which is not the same as equal. A third comparison, on the 180 older arrivals, is exploratory; there the 2015 table was the more accurate when weighted by playing time (see the arrivals of 2008–2015). What this paper adds to such a table can be checked here: the registered test on league changes, an interval for each league number (Table 1), one fitted equation for both competitions, and a refit before each season (Appendix H). Appendix M sets the 2015 table against the destination-only forecast.

### The European League Equivalents flatten the league pattern

League by league, a forecast that knows the destination but not the source league underrates arrivals from Spain and Italy and overrates arrivals from Germany, measured against the average arrival (Figure 2). Once the forecast knows the destination, the league table still flattens the league pattern. The spread of league biases falls from 0.93 to 0.32 EFF/36; sampling noise inflates both levels, so we read the difference, whose interval lies above zero (the interval is in Appendix K). The league table does not remove all bias.

![Figure 2. League biases of a forecast that does not know the source league, and how far one number per league flattens them. Each league's mean signed error (forecast minus actual EFF/36) minus that of all arrivals, with 95% cluster-bootstrap intervals; leagues in the order of Table 1. Grey: a forecast that knows the destination but not the source league. Blue: the league-aware forecast. Asterisk: grey bias detectable after Holm adjustment across the ten leagues; for France, Lithuania and VTB United League the grey interval excludes zero only before that adjustment. For Italy the league-aware interval still excludes zero.](figures/fig4_bias.png)

**What the league numbers are worth.** On the same 674 arrivals of 2020–2025, the league-aware forecast is more accurate than history alone by 0.172 EFF/36 (interval 0.096 to 0.248), and once the destination is known, knowing the source league improves the forecast by 0.065 EFF/36 (interval 0.014 to 0.117). Weighted by playing time the gain is 0.136 against history alone (interval 0.046 to 0.226) and 0.073 against the destination-only forecast (interval 0.010 to 0.136). All four are exploratory: added after a review of the paper, on seasons already examined. They did not carry back to older arrivals (below). For the two unweighted gains only the intervals are new, since those point estimates could be read off Table A20 [26] (by competition and season: Table A22). In size, the gain over the destination-only forecast is about 2% of that forecast's mean absolute error (2.989 EFF/36). By competition it is 0.119 (interval 0.007 to 0.230) for the 194 EuroLeague arrivals and 0.044 (interval −0.013 to 0.101) for the 480 EuroCup arrivals. The two values by competition carry no registered reading, and their difference was not tested [34].

**Why the average gain is small.** The largest detectable league bias is 1.17 EFF/36 (Spain), but the mean absolute error of the forecasts is 2.924, so moving one forecast by a league's bias changes its error little. Against the history-only forecast, the league table changes 8.5% of cross-league comparisons and is right on 57.7% of them (interval 52.4% to 63.1%).

**The forecasts fall below the outcomes.** On average the league-aware forecast is 0.47 EFF/36 below what arrivals delivered (interval −0.78 to −0.18), most in the latest season. Weighted by playing time, the league-aware forecast is 0.96 EFF/36 below what arrivals delivered (interval −1.28 to −0.65), and the forecast that knows only the destination shares this (−0.97, interval −1.29 to −0.64); this interval is two-way clustered, where the first is a cluster bootstrap [35]. The other forecasts share the shortfall (Appendix K; Table A10), so same-player comparisons stand, but forecast levels need care in decisions. For EuroCup arrivals the league-aware forecast is 0.65 EFF/36 below what they delivered (interval −1.04 to −0.30; 480 arrivals); for EuroLeague arrivals the interval includes zero (−0.03, interval −0.51 to 0.44; 194 arrivals). The two intervals overlap, and the difference between them was not tested. We claim no cause.

### A translation factor adds nothing detectable on top of the league numbers

Translation reduces history-only MAE from 3.096 to 2.935 EFF/36 (a gain of 0.161, 5.2%; interval 0.077 to 0.246). Adding the destination leaves a translation gain of 0.049 (interval −0.013 to 0.111); adding the league numbers leaves −0.002 (interval −0.028 to 0.024; a difference of 0.037 would have been detected with 80% power). Figure 3 shows these results, and Table A20 has every row.

![Figure 3. Forecast error with and without translation, and what translation adds once a forecast knows the leagues. Left: forecast error (MAE, EFF/36) on the same 674 arrivals without (grey) and with (blue) the translation feature; the label gives both values. Right: the gain from translation with its 95% interval, clustered by player and destination club-season.](figures/fig_mechanism.png)

Translation's increment on top of the league numbers is close to a built-in comparison: the translation term is the domestic rate times a factor for each source league and destination, all of which the league-aware forecast already holds, so a small increment is partly expected. It shows that the factor adds nothing detectable once a forecast has the league numbers, not which kind of league information is the better one.

The comparison that is not built in sets the league-aware forecast without translation against history with translation: the advantage for the league-aware forecast is +0.011 EFF/36 (interval −0.027 to 0.049; a difference of 0.054 would have been detected with 80% power). The interval spans zero; the data do not establish superiority.

Both the head-to-head interval and translation's incremental interval lie inside ±0.058 EFF/36, 2% of forecast error [36]. That margin was registered for translation's increment, after the submitted recipe's interval had been seen, so it is descriptive for the submitted recipe, the one behind the results above, and for the head-to-head. Put against the gain from knowing the source league, the margin is 89% of what the source league adds (descriptive), so "inside the margin" is a coarse statement on that scale (Appendix J discusses the margin).

**Other outcomes, seasons and richer models.** The same pattern appears on three other outcomes and in most seasons; this is described, not tested. Appendix J reports it, with the six factor recipes, the pair slopes and the share of translation's gain that league context recovers. A flexible model with 30 features does no better than one number per league (Appendix E: Table A5); that model was fixed and untuned, so this does not bound what a tuned model could do.

**Weighting by playing time.** Weighted by destination minutes, translation's gain over history falls to 0.098 (interval −0.003 to 0.198), which spans zero, while the league-aware forecast keeps a small point-estimate advantage (+0.038) and the increment stays small (−0.017; Table A21). The unweighted analysis is primary and does not demonstrate equal benefit for starters and fringe players.

### Modest ranking gains, no demonstrated shortlist gain

For pairs of arrivals from different source leagues, the league-aware forecast orders 73.7% correctly, a 1.32 percentage-point gain over history (95% interval 0.39 to 2.28). Pairs share players and are not independent observations. For the predicted top 10 per competition and season, none of the registered differences is detectable (Appendix H). The ranking improvement is modest, and neither shortlist quality nor financial value has been demonstrated. Appendix H restates this as the share of comparisons that the league table changes, and reports the within-league and translation checks.

### The same frozen models on arrivals of 2008–2015

The same frozen models were also scored on seasons none of them saw [24]: 180 arrivals of 2008–09 to 2015–16 from the ABA League (131) and Israel's Winner League (49), built from the leagues' own box scores. The forecasts were fixed and their hash committed and pushed before any outcome was joined, and they were scored once. Translation's gain over history is not detectable at this n: +0.001 EFF/36 (95% interval −0.146 to 0.149). Between the league-aware forecast and history plus translation no difference is detected, but the interval is wider than the margin (+0.031, interval −0.017 to 0.079; margin 0.057), so the test cannot show a match at this n. Translation adds nothing detectable on seasons no model saw: −0.015 on top of the league-aware forecast (interval −0.031 to 0.002). Where it can be measured (Israel), a link by initial and surname joins two different players in 3.2% of links (9 of 282; interval 1.7% to 6.0%). On the 121 arrivals with a rare surname, where the name link is safest, two of the three readings are the same, and the interval of translation's increment just excludes zero, on the side of leaving translation out (Appendix Table A15). A version that includes Spain's ACB was computed in the same runs; it is withheld until ACB's written permission arrives, not for its result, and its readings agree with these on one of the three comparisons. The test covers two of the ten leagues (Limitations; Appendix I).

**The league numbers on these arrivals.** A further comparison, added after the first scoring, sets the league-aware forecast against the two plainer forecasts on these 180 arrivals [26]. Against history alone the gain is not detectable on the older seasons at this n (+0.033, interval −0.099 to 0.164; n = 180); it is not clearly above zero when weighted by playing time (−0.118, interval −0.276 to 0.039). Against the forecast that knows only the destination the gain is not detectable on the older seasons at this n (−0.067, interval −0.144 to 0.010; n = 180); weighted by playing time, the league-aware forecast was less accurate than the forecast that knows only the destination by 0.129 EFF/36 (interval −0.209 to −0.048). In plain words, on these arrivals the league table did not help, and weighted by playing time it did worse than knowing the destination alone. This is a second reading of outcomes that had been read once, and it is exploratory; the wording for the last result was fixed after it was seen [37]. Appendix Table A17 gives all four results and what each could detect.

Two published league scales were also scored on these arrivals; for each, the comparison with the paper's league numbers is shown in the weighting less favourable to the paper, and Appendix I gives both (Table A18). Unweighted, a league table printed in 2015 [8] added nothing detectable to the destination-only forecast (−0.004, interval −0.046 to 0.039; a gain of 0.061 would have been detected with 80% power); weighted by playing time it was more accurate than the paper's league numbers by 0.082 EFF/36 (interval 0.011 to 0.152). Unweighted, a league scale published in 2026 [38] added nothing detectable to the destination-only forecast (−0.005, interval −0.027 to 0.018; a gain of 0.032 would have been detected with 80% power). Weighted by playing time, with it the forecast was less accurate than with the destination alone by 0.025 EFF/36 (interval 0.001 to 0.049). Weighted by playing time it was more accurate than the paper's league numbers by 0.104 EFF/36 (interval 0.040 to 0.167). These readings were first made outside the registration, in a review of the paper, and the rules for printing them were written after their values had been seen; they are exploratory [39].

**Where the forecast missed.** On the older arrivals the league table lowered the forecast for arrivals from the Adriatic league by 0.68 EFF/36; without the table the forecast was 0.35 EFF/36 (interval −1.00 to 0.30) below what they delivered, and with it 1.04 (interval −1.69 to −0.38) [27]. This shows where the forecast missed; it cannot separate a change in league strength from a change in which players clubs signed, in the data source or in the level of the forecasts (descriptive; Appendix Table A19).

**Two tests outside the fitted arrivals.** The test on league changes covers ten leagues and 3,423 changes, 2016–17 to 2025–26. Its outcomes are domestic, from Proballers box scores, and it was registered before any outcome was read. It is evidence that the table's gaps appear when players change league, in seasons the table was fitted on. The test on older arrivals covers two leagues and 180 arrivals, 2008–09 to 2015–16. Its outcomes are continental, its domestic box scores are the leagues' own, and its league-number comparison was added after the first scoring. It is the only evidence on an earlier period, where the league numbers did not improve the forecast. Neither settles the other; the frozen 2026–27 test, the registered test on arrivals, is inconclusive (next section).

### The outcome-blinded 2026–27 test

The test was scored once, on 25 November 2026, and is inconclusive. Of the 200 newcomers who had reached eight continental games, 94 had a frozen forecast under their name and 106 did not. A newcomer has no frozen forecast when he has no 2025–26 season in the frozen file, or when the two sources write his name differently; no name is joined by hand. 7 of the 106 may be players in the frozen file under another spelling: set against the 94 joined newcomers that is 7.4%, above the 5% we allowed in advance [25]. No replication or equivalence conclusion is drawn. For the record only, on the 94 newcomers that could be scored, translation's gain over history was +0.098 EFF/36 (95% interval [−0.086, 0.281]); the league-aware forecast against history plus translation was −0.040 EFF/36 (95% interval [−0.125, 0.044]); translation's increment over the league-aware forecast was +0.010 EFF/36 (95% interval [−0.015, 0.035]). No sentence is licensed by these values (Appendix L).

We froze forecasts from every model for all 2025–26 domestic player-seasons, for both competitions (3,478 rows, each with the forecasts of every model), and committed and pushed them on 3 November 2026, 10:55 UTC, after the season had begun but before any 2026–27 statistic was read [17]. They were scored on continental games through 24 November 2026, for newcomers who reached eight games; below 60 newcomers the test would have been descriptive only. The registered directions were that translation helps against history, that the league-aware forecast is at least as good as history plus translation, and that translation adds nothing to it. Five secondary read-outs were registered on 16 November 2026, after the freeze and before scoring [25]. Two of them test the league numbers themselves: the league-aware forecast against the forecast that knows only the destination, and the ordering of cross-league pairs. As registered, we did not expect the first to be detectable in November: it looked for an effect near 0.065 EFF/36, its 2020–2025 estimate. Equivalence is never claimed from this test. A read-out of a forecast built on a league table printed in 2015 [8], frozen in a second file, was registered on 17 November 2026 [33]; Appendix L prints it. A newcomer is a player with at least eight continental games by 24 November 2026 and no qualifying continental season in 2025–26 (at least eight games); he has a frozen forecast only if he played 2025–26 in one of the ten leagues. Appendix L gives the rule for a failure to replicate and what the test could detect.

For the conference presentation, the same frozen file will be re-scored on games through 15 February 2027, a re-score registered before any 2026–27 statistic was read [18]; it is reported beside this test, never in place of it.

## What a club can use

**European League Equivalents.** Table 1 lists, for each source league, the domestic EFF/36 that gives the same continental forecast as 16 in Spain's ACB when career history equals the domestic rate (Figure 1). The league numbers describe players selected for continental recruitment, not pure league strength. In every yearly refit, every tier-3 league needed a higher domestic rate than every tier-1 league. The refits share most of their data, so this describes stability, not independent validation (Appendix H: Figure A3, Table A11). The order was stable; the size of the gaps was not. For EuroLeague arrivals the nine other leagues stood on average 1.2 EFF/36 above Spain's 16 in the refit that forecast 2020–21 and 2.4 in the refit that forecast 2025–26, against 2.0 in the full fit of Table 1. The cause was not examined [34].

Table 1. European League Equivalents: the domestic EFF/36 that the league-aware forecast (no translation, fitted on every season through 2025) treats like a 16 in Spain's ACB when career history equals that rate, with 95% cluster-bootstrap intervals. *League number*: the league's term δ in the fitted equation, in forecast EFF/36 against the league average, with its interval. Leagues inside a tier are not distinguishable, and the order inside a tier is not a ranking. The equivalents are read off the registered model and are not themselves a registered estimand.

| Tier | Source league | League number | Equivalent, EuroLeague | Equivalent, EuroCup |
|---|---|---|---|---|
| 1 | Spain (ACB) | +1.20 [0.63, 1.74] | 16 (reference) | 16 (reference) |
| 1 | France (Pro A) | +1.12 [0.47, 1.75] | 16.1 [14.8, 17.4] | 16.1 [14.9, 17.3] |
| 1 | Italy (LBA) | +0.71 [0.19, 1.28] | 16.7 [15.5, 17.9] | 16.7 [15.6, 17.7] |
| 2 | Greece (A1) | +0.36 [−0.39, 1.07] | 17.3 [15.9, 18.7] | 17.1 [15.9, 18.4] |
| 2 | Turkey (BSL) | −0.07 [−0.59, 0.48] | 17.9 [16.7, 19.2] | 17.7 [16.6, 18.7] |
| 2 | Israel (Winner League) | −0.22 [−0.84, 0.37] | 18.2 [16.8, 19.7] | 17.9 [16.7, 19.1] |
| 3 | Adriatic (ABA) | −0.51 [−1.23, 0.19] | 18.6 [17.1, 20.2] | 18.3 [17.0, 19.6] |
| 3 | Germany (BBL) | −0.83 [−1.30, −0.38] | 19.1 [17.9, 20.4] | 18.7 [17.7, 19.7] |
| 3 | VTB United League | −0.87 [−1.54, −0.20] | 19.1 [17.8, 20.5] | 18.7 [17.6, 19.8] |
| 3 | Lithuania (LKL) | −0.90 [−1.51, −0.28] | 19.2 [17.8, 20.7] | 18.8 [17.7, 20.0] |

**Which gap to use.** To read a domestic line before a EuroLeague or EuroCup arrival, use the Equivalents as printed. When a player changed domestic league, his rate moved on average by about three quarters of the gap between the two leagues' Equivalents (slope 0.77, interval 0.69 to 0.84; 0.57 without Spain, interval 0.48 to 0.66): measured against the forecast for a player who stays in his league, it was higher when he went to the league with the higher Equivalent and lower when he went the other way [40]. This is an average over the 3,423 league changes of the test, not a statement about one pair of leagues or one player.

**The league numbers as an equation.** The equivalents are read off one fitted equation, the league-aware forecast of Equation (@eq:model) with its coefficients estimated on every season through 2025 [35]:

$$\hat y = 3.103 + 0.660\,x + 0.092\,h - 1.389\,a + \delta_\ell + D\,\big(-0.358 - 0.092\,x\big)$$ {#eq:fitted}

Here x is last season's domestic EFF/36 and h the career rate before it (all earlier games on record; h = x for a player with no earlier season); a = 1 when x is above h, D = 1 for a EuroLeague destination and δ is the league number of Table 1. The step a takes 1.389 EFF/36 off the forecast of a player whose last season was above his career rate; the ten league numbers span 2.10. At a domestic rate of 16 the destination term is −1.83 EFF/36: the forecast for a EuroLeague arrival minus that for a EuroCup arrival. It is arithmetic on the fitted coefficients, it grows with the domestic rate, and it is a point value with no interval [39]. These are three terms of one fitted forecast, and at that rate each is smaller than the average miss of a single forecast (2.924 EFF/36; typical 80% band ±4.8). The destination term is the same for two candidates of one club who have the same domestic rate, so it bears on the level of a forecast and not on the comparison of two such candidates. The Equivalents are stated for the profile where the step is zero (x = h). A gap between two leagues is unchanged when both candidates carry the step, and not when only one does. The equation is for EuroLeague and EuroCup arrivals from these ten leagues, and the limits stated above apply to it: the forecasts fall below the outcomes on average, the league numbers did not carry back to the older arrivals of two leagues, and they describe the players clubs sign from a league, not league strength. Appendix L gives the full definitions and the rounding bound.

**Two recruits with the same production.** Two EuroCup candidates each averaged 16 EFF/36 last season and across their earlier careers. The German BBL recruit projects at 14.3 EFF/36 and the Spanish ACB recruit at 16.3. The 2.02 EFF/36 gap comes entirely from the league terms. The typical 80% individual error band is ±4.8 EFF/36. On film, ask which player could sustain his production in the minutes and role the club can offer. Appendix L shows how to compare recruits with different histories.

**How far to trust a forecast gap.** Forecast gaps of at least 1 EFF/36 were right at least 60% of the time. Forecast gaps of at least 3 EFF/36 were right at least 70% of the time. These shares rest on 18,069 and 10,448 pairs from the examined seasons and describe the whole forecast. The gap also includes player history and destination, so this is not the isolated benefit of the league adjustment (Appendix H: Table A14, Figure A4). It describes selected arrivals retrospectively and requires validation before use on a new candidate pool.

**Individual uncertainty.** Walk-forward conformal intervals [41, 42] for the league-aware forecast cover 82.6% of 540 arrivals at the nominal 80% level (about ±4.8 EFF/36); seasonal coverage ranges from 74.0% to 90.4% and is lowest in 2025–26. These wide intervals argue for scouting alongside statistical comparisons (Appendix H; cases in Appendix G).

**Arrivals with few games.** The 134 of 808 arrivals with fewer than eight games had a median continental EFF/36 of 12.0, compared with 15.1 among qualifiers (Tables A6–A7). A club using the rate forecast still needs a view on playing time.

## Related work

One number per league is an old idea: baseball's major-league equivalents and hockey's league equivalencies put leagues on one scale [1, 4, 5], and projection across leagues in basketball predates this study [43, 44]. Analysts have published league scales that cover European basketball [8, 45, 46]; the first is scored here. Glazer estimates G League-to-NBA translation factors by matching similar players and a difference-in-differences estimator [10]. The Gaussian Hoops scale, fitted on league changes among other moves, gives one strength value per league [38]; it is not scored on the arrivals of 2020–2025 or on the league changes, because it is built on those seasons; it is not a registered arm and is not read out on the frozen test [33]; one exploratory reading on the older arrivals is in Results and Appendix I [39]. Two analysts report how forecasts that use a league level fared, one for players of 30 European leagues [47] and one for EuroLeague players [48]; neither reports its forecast without the league level (Appendix O). A bounded search in English found no public test in basketball that compares a forecast with and without a league adjustment on what players arriving in European competitions went on to do. This paper offers a named league table for European basketball arrivals, the same-player benchmark of translation factors against it, and its test on league changes; its test on frozen forecasts is inconclusive. Appendix O gives this section in full.

## Limitations

**Exploratory seasons.** The 2020–2025 outcomes had been examined before these analyses, so those results are exploratory despite pre-registration. **Sample.** The sample is predominantly EuroCup (480 of 674 arrivals), requires eight continental games, and consists of players whom clubs chose to sign, so the league numbers describe those choices as much as league strength; the Equivalents hold along the profile where career history equals the domestic rate. **League changes.** The changes were about 0.77 of the size the Equivalents imply (interval 0.69 to 0.84 with the table held fixed; 0.43 to 0.93 with its values redrawn); the slope is lowest without Spain (0.57, interval 0.48 to 0.66). Players who change league are not a random sample, and the box scores are not the corrected corpus of the 674 arrivals.

**Forecast level.** On average the league-aware forecast is 0.47 EFF/36 below what arrivals delivered, most in the latest season; weighted by playing time, the league-aware forecast is 0.96 EFF/36 below what arrivals delivered; we do not know the cause, and the frozen 2026–27 forecasts may share it. **Weighting.** Weighted by minutes, translation's gain over history is not clearly above zero, on the main sample and on a wider one (Table A21). **Carry-over.** The gain from the league table on arrivals of 2020–2025 did not carry back to the 180 arrivals of 2008–09 to 2015–16 from the ABA League and Israel's Winner League.

**Linkage.** Players are joined across sources by name. After the second registered sample of 300 estimation pairs, at most 3.4% of unverified estimation pairs are identity mismatches (Appendix A). By fixed rules, 4 of the 674 forecast arrivals are classed as identity mismatches; 578 are confirmed by independent evidence, 87 rest on the name across a change of club, and 5 are unresolved. The three comparisons read the same without the arrivals classed wrong (Table A21). Career histories and training arrivals were not audited. Name joins can also miss genuine arrivals, which a mismatch audit does not measure.

**Frozen test.** Inconclusive: 7 newcomers without a frozen forecast may be in the frozen file under another spelling, 7.4% of the 94 joined, above the 5% allowed in advance. Partial-season outcomes; for five of the ten source leagues (France, Turkey, Lithuania, VTB and the ABA League) the 2025–26 domestic data stop between 26 December 2025 and 8 January 2026, and 250 Spanish ACB rows lack official stat corrections. **Older-seasons test.** The test covers two of the ten leagues and uses the leagues' own box scores, where the benchmark uses Proballers. The league numbers were estimated about ten years later, and the league-aware forecast is 0.77 EFF/36 below the outcomes. For 33.3% of arrivals no earlier season is on record, which can favour translation against history, and names are linked by initial, surname and the first three letters of the first name. A pass there is not proof for today's leagues, and a miss is not proof against them.

**What the intervals leave out.** The paired comparisons on arrivals take the fitted forecasts as given, so their intervals leave out the uncertainty of refitting the models. For league changes, the primary interval refits the stayer forecast with the league table held fixed. Table A24 also shows how the interval changes when the league values vary.

## Conclusion

On arrivals of 2020–2025 a forecast that ignores the source league misjudges whole leagues, and one number per league flattens that pattern. The European League Equivalents present those numbers as a table: when career history equals the domestic rate, 16 EFF/36 in Spain's ACB gives the same forecast as about 19 in Germany, Lithuania or VTB. In a test registered and frozen before its outcomes were read, 1,649 players who changed domestic league moved in the direction the table implies, at about three quarters of its size (slope 0.77, 95% interval 0.69 to 0.84). These players made 3,423 league changes. On top of the league numbers a translation factor adds nothing detectable: −0.002 EFF/36 (95% interval −0.028 to 0.024) on the arrivals of 2020–2025, and −0.015 (interval −0.031 to 0.002) on 180 older arrivals from seasons no model saw. The league numbers need only past arrivals (1,059 here), not the 4,074 same-season pairs that translation factors need. On arrivals of 2020–2025, once the destination is known, knowing the source league improves the forecast by 0.065 EFF/36 (interval 0.014 to 0.117); on 180 older arrivals from two leagues it did not, so the league numbers are not shown to hold across periods (the frozen 2026–27 test carried a registered read-out for this gain and is inconclusive). These seasons were examined before registration, so the evidence is exploratory; the ranking gain is modest and no top-10 gain was demonstrated. Forecasts frozen on 3 November 2026, after the season began but before outcome inspection, were scored once on 2026–27 newcomers. That test, separate from the test on league changes, is inconclusive: 7 newcomers without a forecast may be in the frozen file under another spelling, more than the 5% of the 94 joined newcomers that was allowed in advance.

## Data and code

The full-paper companion is available at https://github.com/AT020993/cross-league-translation: the code, the per-season tables and the result summaries behind every number, with one command that recomputes the main comparisons and checks the other analyses by hash. Per-game files of the data providers, box scores from the league websites and birthdates are not redistributed (rights and personal data). The full-paper reproduction command calculates the league-change slope, including the check without Spain, from counts and mean residuals for each direction of each league pair. It checks the saved player-bootstrap interval against the retained results. Repeating the bootstrap requires the player-level moves and stayer data to refit the comparison model. The paper-number manifest verifies manuscript regeneration, input hashes and saved values. This checks saved outputs; it does not independently recompute analyses from raw inputs. Domestic statistics are credited to Proballers and continental statistics to the EuroLeague API; the older-seasons test uses box scores from the websites of the ABA League and Israel's Winner League. Rights in the underlying data remain with those sources.

## References

[1] James, B. (1985). *The Bill James Baseball Abstract 1985*. New York: Ballantine Books.

[2] Davenport, C. (1996). Davenport Translations. *Baseball Prospectus 1996*. https://legacy.baseballprospectus.com/other/bp1996/dtessay.html

[3] Davenport, C. (1998, January 30). DTs vs. MLEs – A Validation Study. *Baseball Prospectus*. https://www.baseballprospectus.com/news/article/49/dts-vs-mles-a-validation-study/

[4] Desjardins, G. (2004). League Equivalencies. HockeyAnalytics.com. http://hockeyanalytics.com/Research_files/League_Equivalencies.pdf

[5] Bacon, P. (2021). NHL Equivalency (NHLe) and Prospect Projection Models (describing C. J. Turtoro's Network NHLe). HockeyStats.com. https://hockeystats.com/methodology/nhle

[6] Pelton, K. (2013, October 9). What is SCHOENE? *ESPN*. https://www.espn.com/nba/story/_/id/9797404/explaining-schoene-projection-system

[7] Pelton, K. (2014, June 10). Projecting top 10 int'l prospects. *ESPN*. https://www.espn.com/nba/draft2014/story/_/id/11064231/clint-capela-leads-projection-top-10-international-prospects-2014-nba-draft

[8] Vashro, L. (2015, November 6). Deep Dives: Measuring Level of Competition Around the World. *Nylon Calculus (FanSided)*. https://fansided.com/2015/11/06/deep-dives-measuring-level-of-competition-around-the-world/

[9] Lee, D.-J., and Page, G. L. (2021). Big Data in Sports: Predictive Models for Basketball Player's Performance. *Mathematics in Industry Reports* (ESGI 131). https://doi.org/10.33774/miir-2021-h4x62

[10] Glazer, A. K. (2026). Nuthin' But A G League: Estimating league translation factors. *Journal of Sports Analytics*, 12. https://doi.org/10.1177/22150218261428808

[11] Sports Reference. Glossary: Game Score (GmSc), a formula created by John Hollinger. https://www.sports-reference.com/cbb/about/glossary.html (accessed November 2026)

[12] Kubatko, J., Oliver, D., Pelton, K., and Rosenbaum, D. T. (2007). A Starting Point for Analyzing Basketball Statistics. *Journal of Quantitative Analysis in Sports*, 3(3). https://doi.org/10.2202/1559-0410.1070

[13] Diebold, F. X., and Mariano, R. S. (1995). Comparing Predictive Accuracy. *Journal of Business & Economic Statistics*, 13(3), 253–263. https://doi.org/10.1080/07350015.1995.10524599

[14] Gneiting, T. (2011). Making and Evaluating Point Forecasts. *Journal of the American Statistical Association*, 106(494), 746–762. https://doi.org/10.1198/jasa.2011.r10138

[15] Cameron, A. C., Gelbach, J. B., and Miller, D. L. (2011). Robust Inference With Multiway Clustering. *Journal of Business & Economic Statistics*, 29(2), 238–249. https://doi.org/10.1198/jbes.2010.07136

[16] Cameron, A. C., Gelbach, J. B., and Miller, D. L. (2008). Bootstrap-Based Improvements for Inference with Clustered Errors. *Review of Economics and Statistics*, 90(3), 414–427. https://doi.org/10.1162/rest.90.3.414

[17] Pre-registration of the full-paper analyses and the 2026–27 frozen test (2026). Pushed 3 November 2026, 09:15 UTC, before implementation. Full-paper companion materials (release status in Data and code), https://github.com/AT020993/cross-league-translation

[18] Pre-registration Amendment 1: analyses E10–E17 and the February 2027 re-score of the frozen test (2026). Commit f1a3453, 4 November 2026, 22:06 UTC, before implementation. Full-paper companion materials (release status in Data and code), https://github.com/AT020993/cross-league-translation

[19] Pre-registration Amendment 2: the stint rule for the survivorship analysis E14 (2026). Commit 41efa97, 5 November 2026, 06:49 UTC, before the E14 re-run. Full-paper companion materials (release status in Data and code), https://github.com/AT020993/cross-league-translation

[20] Pre-registration Amendment 3: analyses E18–E23 (forecast level, table stability, forecast gaps, error bands by league, the above-average-season discount) (2026). Commit caf0902, 11 November 2026, 16:06 UTC, before implementation. Full-paper companion materials (release status in Data and code), https://github.com/AT020993/cross-league-translation

[21] Pre-registration Amendment 4: analysis E24 (league biases of a forecast that knows the destination but not the source league) (2026). Commit 5ab52fa, 11 November 2026, 19:31 UTC, before implementation and after the Amendment 3 results. Full-paper companion materials (release status in Data and code), https://github.com/AT020993/cross-league-translation

[22] Pre-registration Amendment 5: analysis E25 (a second, larger identity-linkage audit) (2026). Commit be61514, 12 November 2026, 14:49 UTC, before implementation and after the first audit's result. Full-paper companion materials (release status in Data and code), https://github.com/AT020993/cross-league-translation

[23] Pre-registration Amendment 6: analysis E26 (an identity audit of the forecast arrivals) (2026). Commit 245bafa, 12 November 2026, 18:25 UTC, before implementation and after both linkage audits' results. Full-paper companion materials (release status in Data and code), https://github.com/AT020993/cross-league-translation

[24] Pre-registration Amendment 7: analysis E27 (the frozen forecasts tested on older seasons) (2026). Commit e884afe, 12 November 2026, 22:01 UTC, before implementation and before any outcome of an older arrival was read. Full-paper companion materials (release status in Data and code), https://github.com/AT020993/cross-league-translation

[25] Pre-registration Amendment 8: more read-outs from the frozen 2026–27 test, and its reading rules made explicit (2026). Commit afcfeff, 16 November 2026, 15:59 UTC, before implementation and before the test was scored. Full-paper companion materials (release status in Data and code), https://github.com/AT020993/cross-league-translation

[26] Pre-registration Amendment 9: analysis E28 (the league-aware forecast against the plain baselines, with intervals) (2026). Commit 3c91586, 16 November 2026, 16:01 UTC, before implementation; exploratory, on seasons already examined. Full-paper companion materials (release status in Data and code), https://github.com/AT020993/cross-league-translation

[27] Pre-registration Amendment 11: analysis E29 (where the league table missed on the older arrivals) (2026). Commit 40f0d27, 16 November 2026, 21:22 UTC, before implementation; descriptive, on outcomes already read. Full-paper companion materials (release status in Data and code), https://github.com/AT020993/cross-league-translation

[28] Cawley, G. C., and Talbot, N. L. C. (2010). On Over-fitting in Model Selection and Subsequent Selection Bias in Performance Evaluation. *Journal of Machine Learning Research*, 11, 2079–2107. https://jmlr.org/papers/v11/cawley10a.html

[29] Pre-registration Amendment 14: analysis E30 (the league table tested on players who changed domestic league) (2026). Commit ae99909, pushed 17 November 2026, 17:08 UTC, before implementation and before any outcome of a league change was read. Full-paper companion materials (release status in Data and code), https://github.com/AT020993/cross-league-translation

[30] Pre-registration Amendment 17: readings of Amendments 14 to 16 made explicit, and two corrections (2026). Commit d6ab516, pushed 17 November 2026, 20:28 UTC, before the predictions of analysis E30 were frozen and before any of its outcomes was joined or read; one rule (which weighting decides the sentences about the 2015 table on the arrivals of 2020–2025) was written after that result was seen and says so. Full-paper companion materials (release status in Data and code), https://github.com/AT020993/cross-league-translation

[31] Pre-registration Amendment 22: analysis E33 (the league-changes sensitivity with the stayer forecast also fitted only on earlier seasons) (2026). Commit 1e69136, pushed 19 November 2026, 18:28 UTC, after the test of analysis E30 was scored and its sensitivities were seen, before the generator of E33 was written and before any estimate of E33 was computed; E33 is exploratory. Full-paper companion materials (release status in Data and code), https://github.com/AT020993/cross-league-translation

[32] Pre-registration Amendment 19: a shorter paper, the wording of its first page and one labelled reading of a registered slope (2026). Commit e377464, pushed 18 November 2026, 12:25 UTC, after the test of analysis E30 was scored and after three blind mock readings of the paper, before the text it governs was written and before the scoring of the frozen 2026–27 test. Full-paper companion materials (release status in Data and code), https://github.com/AT020993/cross-league-translation

[33] Pre-registration Amendment 15: analysis E31 (a published league table as a rival) and E32 (named 2026–27 newcomers with their frozen forecasts) (2026). Commit 48f752c, pushed 17 November 2026, 17:09 UTC, before implementation; E31 on the arrivals of 2020–2025 is exploratory. Full-paper companion materials (release status in Data and code), https://github.com/AT020993/cross-league-translation

[34] Pre-registration Amendment 26: the words of the paper once the frozen 2026–27 test was scored and found inconclusive, and two descriptive sentences from values the paper already prints (2026). Commit c96b283, pushed 25 November 2026, 07:53 UTC, after the scoring of the frozen 2026–27 test, with every value of its score record known; it registers nothing in advance, adds no analysis and changes no number. Full-paper companion materials (release status in Data and code), https://github.com/AT020993/cross-league-translation

[35] Pre-registration Amendment 12: the league numbers as an equation, and the forecast level weighted by playing time (2026). Commit 89be8fd, 17 November 2026, 08:48 UTC, before the text was written; it adds no analysis and fixes how committed numbers are printed. Full-paper companion materials (release status in Data and code), https://github.com/AT020993/cross-league-translation

[36] Lakens, D. (2017). Equivalence Tests: A Practical Primer for t Tests, Correlations, and Meta-Analyses. *Social Psychological and Personality Science*, 8(4), 355–362. https://doi.org/10.1177/1948550617697177

[37] Pre-registration Amendment 10: wording for a reading of E28 that Amendment 9 did not foresee (2026). Commit 205207e, 16 November 2026, 20:18 UTC, written after the E28 result and before any sentence about it entered the paper. Full-paper companion materials (release status in Data and code), https://github.com/AT020993/cross-league-translation

[38] Köchling, P. (2026). League strength: Europe vs. NCAA Power 5. *Gaussian Hoops*. https://www.gaussianhoops.com/projections/league-strength/ (accessed 18 November 2026)

[39] Pre-registration Amendment 23: the unit in words, three terms of the equation side by side, where the forecasts run low, a narrower statement on prior work, two published league scales on the older arrivals (analysis E34) and one appendix table of the frozen test (2026). Commit bf60fe3, pushed 22 November 2026, 12:46 UTC, after the test of analysis E30 was scored, after the comparisons of analysis E34 had been computed outside the registration, and before the scoring of the frozen 2026–27 test; E34 is exploratory. Full-paper companion materials (release status in Data and code), https://github.com/AT020993/cross-league-translation

[40] Pre-registration Amendment 20: five named pairs of newcomers in the main text, and one reading of the league-changes slope for a club (2026). Commit 0e8cd21, pushed 18 November 2026, 16:30 UTC, after the test of analysis E30 was scored and after two rounds of blind mock readings of the paper, before the text it governs was written and before the scoring of the frozen 2026–27 test. Full-paper companion materials (release status in Data and code), https://github.com/AT020993/cross-league-translation

[41] Lei, J., G'Sell, M., Rinaldo, A., Tibshirani, R. J., and Wasserman, L. (2018). Distribution-Free Predictive Inference for Regression. *Journal of the American Statistical Association*, 113(523), 1094–1111. https://doi.org/10.1080/01621459.2017.1307116

[42] Barber, R. F., Candès, E. J., Ramdas, A., and Tibshirani, R. J. (2023). Conformal prediction beyond exchangeability. *The Annals of Statistics*, 51(2), 816–845. https://doi.org/10.1214/23-AOS2276

[43] Salador, K. (2011). Forecasting Performance of International Players in the NBA. MIT Sloan Sports Analytics Conference. http://www.sloansportsconference.com/wp-content/uploads/2011/08/Forecasting-Performance-of-International-Players-in-the-NBA.pdf (archived: https://web.archive.org/web/20170811130958/http://www.sloansportsconference.com/wp-content/uploads/2011/08/Forecasting-Performance-of-International-Players-in-the-NBA.pdf)

[44] Berger, T., and Daumann, F. (2021). Increasing the shot at a quality draft-decision – A Bayesian approach to improve predicting three-point accuracy translation in the NBA Draft. MIT Sloan Sports Analytics Conference. https://www.sloansportsconference.com/research-papers/increasing-the-shot-at-a-quality-draft-decision-a-bayesian-approach-to-improve-predicting-three-point-accuracy-translation-in-the-nba-draft

[45] German Basketball Analytics (2025, June 1). Ranking all Major European Basketball Leagues. https://germanbasketballanalytics.substack.com/p/ranking-all-major-european-basketball (accessed 17 November 2026)

[46] Bustamante-Sánchez, Á. (2026). league-translator (code repository, created 4 November 2026). https://github.com/alvaro-bustamante/league-translator (accessed 17 November 2026)

[47] German Basketball Analytics (2025, July 8). Predicting Player Performance in European Basketball using Machine Learning. https://germanbasketballanalytics.substack.com/p/predicting-player-performance-in (accessed 22 November 2026)

[48] Köchling, P. (2026). Basketball projections: expected vs. actual, and EuroLeague 2026–27 player projections: expected vs. actual. *Gaussian Hoops*. https://www.gaussianhoops.com/projections/ and https://www.gaussianhoops.com/projections/euroleague/ (accessed 25 November 2026 and 26 November 2026)

[49] Kendall, M. G. (1938). A New Measure of Rank Correlation. *Biometrika*, 30(1–2), 81–93. https://doi.org/10.1093/biomet/30.1-2.81

[50] Spearman, C. (1910). Correlation calculated from faulty data. *British Journal of Psychology*, 3(3), 271–295; Brown, W. (1910). Some experimental results in the correlation of mental abilities. *British Journal of Psychology*, 3(3), 296–322. https://doi.org/10.1111/j.2044-8295.1910.tb00206.x and https://doi.org/10.1111/j.2044-8295.1910.tb00207.x

[51] Holm, S. (1979). A Simple Sequentially Rejective Multiple Test Procedure. *Scandinavian Journal of Statistics*, 6, 65–70. https://www.jstor.org/stable/4615733

[52] Elmachtoub, A. N., and Grigas, P. (2022). Smart "Predict, then Optimize". *Management Science*, 68(1), 9–26. https://doi.org/10.1287/mnsc.2020.3922

[53] Efron, B., and Morris, C. (1975). Data Analysis Using Stein's Estimator and Its Generalizations. *Journal of the American Statistical Association*, 70(350), 311–319. https://doi.org/10.1080/01621459.1975.10479864

[54] Pre-registration Amendment 18: readings made explicit before the frozen 2026–27 test is scored, and before any named newcomer is printed (2026). Commit 74794bf, pushed 18 November 2026, 09:01 UTC, before the scoring of that test. Full-paper companion materials (release status in Data and code), https://github.com/AT020993/cross-league-translation

[55] Pre-registration Amendment 13: the order of the claims on the first page (2026). Commit 6ea7402, 17 November 2026, 09:55 UTC, before the text was written (commit e03d142 of the same day added a specification table and changed no rule); it adds no analysis and no number. Full-paper companion materials (release status in Data and code), https://github.com/AT020993/cross-league-translation

[56] Pre-registration Amendment 16: the paper built around its league table, and the rules of its first page (2026). Commit d5f721c, pushed 17 November 2026, 17:09 UTC, before that text was written; it adds no analysis and no number. Full-paper companion materials (release status in Data and code), https://github.com/AT020993/cross-league-translation

[57] Pre-registration Amendment 21: the conclusion without the word "matches", and the wider interval of the league-changes slope on the first page (2026). Commit 5d1d931, pushed 18 November 2026, 22:01 UTC, after the test of analysis E30 was scored and after three rounds of blind mock readings of the paper, before the text it governs was written and before the scoring of the frozen 2026–27 test. Full-paper companion materials (release status in Data and code), https://github.com/AT020993/cross-league-translation

[58] Pre-registration Amendment 27: one sentence that points from the comparison with a published league table to its exploratory reading on the older arrivals (2026). Commit 38574fb, pushed 25 November 2026, 12:12 UTC, after E34 was run, with its values known (commit 60b03c5 of the same day added a specification table and changed nothing above it); it registers nothing in advance, adds no analysis and changes no number. Full-paper companion materials (release status in Data and code), https://github.com/AT020993/cross-league-translation

[59] Pre-registration Amendment 28: thirteen repaired sentences, four sentences that define the paper's terms, the figures redrawn in one style, and the Paper ID line (2026). Commit e9fd7dc, pushed 26 November 2026, 09:00 UTC, after every result was known; it registers nothing in advance, adds no analysis and changes no number. Full-paper companion materials (release status in Data and code), https://github.com/AT020993/cross-league-translation

[60] Pre-registration Amendment 29: the first page reworded after a blind comparison of two first pages, further sentences repaired or added, and two values of a registered read-out printed (2026). Commit 25aba66, pushed 26 November 2026, 18:13 UTC, after every result was known; it registers nothing in advance, adds no analysis and changes no result. Full-paper companion materials (release status in Data and code), https://github.com/AT020993/cross-league-translation

[61] Pre-registration Amendment 30: eighteen corrections after the changes of Amendment 29, made after a fresh reader had checked them against the rest of the paper (2026). Commit 5376608, pushed 26 November 2026, 19:30 UTC, after every result was known; it registers nothing in advance, adds no analysis and changes no result. Full-paper companion materials (release status in Data and code), https://github.com/AT020993/cross-league-translation

[62] Pre-registration Amendment 32: twenty-seven passages reworded for register, the appendix tables numbered in the order in which they stand, and values printed on three figures (2026). Commit 25ae7e3, pushed 27 November 2026, 14:59 UTC, after every result was known; it registers nothing in advance, adds no analysis and changes no result. Full-paper companion materials (release status in Data and code), https://github.com/AT020993/cross-league-translation

[63] Pre-registration Amendment 24: when the pages that show current-season statistics are read if the frozen test ends inconclusive (2026). Commit 8175f92, pushed 22 November 2026, 20:01 UTC, before the scoring of the frozen 2026–27 test; it adds no analysis and no number. Full-paper companion materials (release status in Data and code), https://github.com/AT020993/cross-league-translation

[64] Myrte, M., Buzzalino, S., and Aymerich, T. (2026). Scouting Anyone: Probabilistic Player Archetypes for Any League. MIT Sloan Sports Analytics Conference (poster). https://www.sloansportsconference.com/research-papers/scouting-anyone-probabilistic-player-archetypes-for-any-league

[65] Dinsdale, D., and Gallagher, J. (2022). Transfer Portal: Accurately Forecasting the Impact of a Player Transfer in Soccer. arXiv preprint arXiv:2201.11533. https://arxiv.org/abs/2201.11533

[66] Shaikh, M. A. (2026). Hierarchical Bayesian modeling of cross-league performance translation in elite football. *Journal of Sports Analytics*, 12. https://doi.org/10.1177/22150218261481583

[67] Shaikh, M. A. (2026). A Machine Learning Framework for Cross-League Per-90 Statistic Translation in Elite Football: A Comparative Model Zoo with Conformal Prediction. SportRxiv preprint. https://doi.org/10.51224/sportrxiv.959

[68] Yeh, C.-K., Rice, G., and Dubin, J. A. (2022). Evaluating Real-Time Probabilistic Forecasts With Application to National Basketball Association Outcome Prediction. *The American Statistician*, 76(3), 214–223. https://doi.org/10.1080/00031305.2021.1967781

## Appendix

### A. Identity verification and factor support

The submitted abstract also reported what happens when the factor-estimation pairs are restricted to players whose identity, club and appearance dates could be verified. Verification cuts estimation pairs from 4,074 to 1,537, and forecasts with a supported league-pair factor (rather than the destination average) from 566 of 674 (84.0%) to 118 (17.5%; 113 with overlap trimming). With verified factors the gain over history shrinks to 0.044–0.083, and every increment over a forecast that knows both leagues is negative, at each of the three penalties and with pair-specific slopes (−0.012 to −0.005; Table A1 shows the primary penalty). Random restrictions of the full pool to the same number of pairs, registered after this loss was seen, keep a median of 91 (season-matched) and 112 (also league-pair-matched, maximum 118) supported forecasts. Comparable support loss is therefore attainable without verification; this diagnostic does not establish that sample loss caused the verification result. Table A1 repeats the head-to-head on the verified pools: there the league-aware forecast is more accurate than history plus translation, and most translated features fall back to the destination average.

Table A1. The submitted recipe on the verified factor pools (EFF/36, 95% intervals).

| Factor pool | Gain vs history | Increment vs league-aware | League-aware vs history + translation | Forecasts on fallback |
|---|---|---|---|---|
| Verified identity, full season | +0.076 [0.018, 0.134] | −0.007 [−0.012, −0.002] | +0.096 [0.046, 0.146] | 556 |
| Verified, overlap keys | +0.083 [0.023, 0.143] | −0.006 [−0.012, −0.001] | +0.089 [0.038, 0.140] | 561 |
| Verified, overlap-window rates | +0.044 [−0.000, 0.088] | −0.005 [−0.017, 0.007] | +0.128 [0.067, 0.189] | 561 |

The Amendment 1 audit drew 100 of the 2,537 unverified estimation pairs with a fixed seed and classed each by rules fixed before any class was computed (name, birthdate, shared-roster club identity, schedule feasibility). Rule-based classes: 98 confirmed, 1 unresolved, 1 wrong; after a recorded hand review of the unresolved pair: 99 confirmed, 0 unresolved, 1 wrong (Wilson 95% interval for the wrong share 0.2% to 5.4%).

Because that upper bound sat just above the registered 5% bar, Amendment 5 [22] added a second look: a fresh sample of 300 pairs from the 2,437 not drawn before, with the same checks and rules. Of these, 296 were confirmed, 0 unresolved and 4 wrong (Wilson 95% interval 0.5% to 3.4%); pooled with the first sample, 5 of 400 (interval 0.5% to 2.9%). Of the 4 wrong pairs, 2 are contradicted by club or schedule records, and 2 are contradicted only by birthdate while the club and schedule checks agree; they stay wrong because the rule was fixed in advance. The bound quoted in Limitations is the larger of the new-sample and pooled bounds, the new sample had to pass on its own because this was a second look, and no third look is allowed. Both audits are exploratory and cover estimation pairs, not forecast arrivals.

Amendment 6 [23] therefore audited the forecast arrivals themselves: all 674, by rules fixed in advance and with no hand review. An arrival is confirmed when independent evidence links the domestic record to the continental player: the two birthdates agree (322 arrivals); the same player appears in continental play in the source season (76) or is still at the source club a year later (140), each checked as in the first audit; or the previous club in the competition's own registration list is the source club (442). An arrival can meet several of these conditions. The last rule is a text match and passed its registered check: it matched 445 of 674 arrivals, against 2 after a seeded shuffle of the lists. Of these 445, 442 are confirmed arrivals (the count given above); the other 3 are classed wrong on other evidence. An arrival is wrong when the two birthdates disagree, when club or schedule records contradict the link, or when two registered players stand behind the destination record. Result: 578 confirmed, 4 wrong, 5 unresolved, and 87 name only: the destination player is one identified person and no namesake is visible, but nothing independent links him to the source record. Without the wrong arrivals the three comparisons keep their readings (Table A21). They also keep them without the unresolved (n = 665) and on confirmed arrivals alone (n = 578: translation vs history +0.170 [0.079, 0.261], league-aware vs history + translation +0.005 [−0.038, 0.048], translation added +0.002 [−0.025, 0.028]), a stricter subset that is not a typical sample of signings. The audit cannot see a namesake who left the covered leagues, removes arrivals from scoring without refitting any model, and does not cover career histories or training arrivals. It is exploratory.

### B. Results by outcome

Table A2. Translation's gain and increments by outcome (outcome units per 36 minutes, or per 100 possessions; 95% intervals). Reliability is the full-season split-half reliability of the outcome.

| Outcome | Reliability | Gain vs history | Increment vs destination-only | Increment vs league-aware (λ = 10) |
|---|---|---|---|---|
| EFF/36 | 0.69 | +0.161 [0.077, 0.246] | +0.049 [−0.013, 0.111] | −0.002 [−0.028, 0.024] |
| Points/36 | 0.77 | +0.109 [0.031, 0.186] | −0.002 [−0.033, 0.029] | −0.010 [−0.024, 0.004] |
| Game Score/36 | 0.66 | +0.147 [0.086, 0.208] | +0.045 [0.011, 0.079] | −0.002 [−0.009, 0.004] |
| EFF per 100 possessions | 0.67 | +0.155 [0.071, 0.238] | +0.069 [−0.001, 0.139] | −0.003 [−0.031, 0.026] |

### C. Robustness forest

![Figure A1. What translation adds once the forecast knows both leagues, across factor recipes, outcomes, competitions, seasons and age-aware models, as a percentage of the league-aware forecast's error (league numbers, λ = 10). Points: estimates; bars: 95% intervals. The shaded band marks ±2%, the registered margin (descriptive for the submitted recipe, the first row, whose interval had been seen). The boosted model (Appendix E, Table A5; discussed in Appendix J) is not in this panel; its upper bound is above 2%.](figures/figA1_robustness.png)

### D. Which skills travel

Table A3. Same-season retention (continental rate ÷ domestic rate for the same player in the same season; below 1 = he does less of it against continental opponents). The registered estimator averages each pair's ratio, weighted by the smaller of the player's two minute totals (attempts for percentages); the ratio of sums is an unregistered sensitivity check. Of the 39 registered comparisons whose registered intervals do not overlap, 14 keep the same order with intervals that do not overlap under the ratio of sums.

| Component | Retention, registered [95% CI] | Ratio of sums [95% CI] | Pairs used |
|---|---|---|---|
| points | 0.926 [0.919, 0.933] | 0.940 [0.930, 0.950] | 4,074 |
| offensive rebounds | 1.087 [1.064, 1.109] | 0.931 [0.908, 0.955] | 4,050 |
| defensive rebounds | 0.985 [0.967, 1.008] | 0.932 [0.920, 0.943] | 4,072 |
| assists | 0.931 [0.918, 0.944] | 0.921 [0.900, 0.942] | 4,068 |
| steals | 1.003 [0.987, 1.019] | 0.916 [0.902, 0.930] | 4,066 |
| blocks | 0.995 [0.962, 1.029] | 0.897 [0.864, 0.929] | 3,437 |
| turnovers | 1.043 [1.031, 1.055] | 0.997 [0.984, 1.011] | 4,071 |
| 3-point attempts | 0.951 [0.936, 0.966] | 0.961 [0.943, 0.978] | 3,773 |
| free-throw attempts | 0.935 [0.919, 0.953] | 0.906 [0.889, 0.923] | 4,062 |
| 3-point percentage | 0.995 [0.987, 1.004] | 0.977 [0.969, 0.986] | 2,759 |
| free-throw percentage | 1.007 [1.002, 1.011] | 1.009 [1.003, 1.014] | 2,517 |

Table A4. Carry-over for arrivals: correlation of domestic and continental rates, the destination reliability of one continental season, and the correlation corrected for that noise (disattenuated). Reliability below 0.40 makes the corrected value unreadable.

| Component | n | Raw r | Reliability | Disattenuated r [95% CI] |
|---|---|---|---|---|
| points | 674 | 0.58 | 0.77 | 0.66 [0.60, 0.72] |
| offensive rebounds | 674 | 0.80 | 0.82 | 0.89 [0.84, 0.93] |
| defensive rebounds | 674 | 0.72 | 0.76 | 0.82 [0.77, 0.87] |
| assists | 674 | 0.81 | 0.90 | 0.85 [0.82, 0.88] |
| steals | 674 | 0.37 | 0.45 | 0.55 [0.44, 0.68] |
| blocks | 674 | 0.77 | 0.85 | 0.83 [0.79, 0.88] |
| turnovers | 674 | 0.54 | 0.63 | 0.68 [0.62, 0.75] |
| 3-point attempts | 674 | 0.86 | 0.94 | 0.89 [0.87, 0.91] |
| free-throw attempts | 674 | 0.56 | 0.67 | 0.68 [0.62, 0.74] |
| 3-point percentage | 411 | 0.24 | 0.10 | 0.74 [0.36, 2.82] (unreadable) |
| free-throw percentage | 378 | 0.61 | 0.66 | 0.75 [0.67, 0.84] |

### E. Flexible model and survivorship

Table A5. The flexible-model comparison (Amendment 1, E16): walk-forward MAE (EFF/36) on the same 674 arrivals and the estimated reducible-error share under the normal-noise reference (Appendix J), with 95% cluster-bootstrap intervals. The boosted model uses fixed hyperparameters (no tuning) and 30 features. One number per league against the boosted model: MAE difference −0.108 (interval −0.222 to 0.005; negative = boosted model worse). The source club's win share adds +0.002 to the ridge model (interval −0.022 to 0.025).

| Forecast | MAE | Avoidable error removed [95% CI] |
|---|---|---|
| History only | 3.096 | 0% (reference) |
| History + translation | 2.935 | 17.6% [9.5%, 26.6%] |
| One number per league (λ = 10) | 2.924 | 18.8% [11.6%, 27.2%] |
| One number per league + translation | 2.926 | 18.6% [9.9%, 28.4%] |
| Ridge, all 30 features | 2.943 | 16.8% [6.5%, 26.6%] |
| Ridge, all 30 features + translation | 2.943 | 16.8% [6.3%, 26.8%] |
| Boosted trees, all 30 features | 3.032 | 7.0% [−5.0%, 17.8%] |
| Boosted trees, all 30 features + translation | 3.006 | 9.9% [−1.7%, 21.0%] |

Table A6. Who the eight-game rule leaves out (Amendments 1 and 2, E14): medians.

| Arrivals | n | Domestic EFF/36 | Domestic min/game | Continental games | Continental min/game | Continental EFF/36 |
|---|---|---|---|---|---|---|
| 8+ continental games (benchmark) | 674 | 17.4 | 23.5 | 17 | 19.2 | 15.1 |
| 1–7 continental games | 134 | 16.3 | 21.7 | 5 | 13.5 | 12.0 |

Table A7. Forecasting playing time: MAE for the share of team minutes (1 = every minute), all 808 arrivals. The league-aware forecast's gain over history alone is 0.0152 (95% interval 0.0109 to 0.0194).

| Forecast | MAE |
|---|---|
| History only | 0.1247 |
| History + translation | 0.1243 |
| History + destination | 0.1110 |
| League-aware (one number per league, λ = 10) | 0.1095 |
| League-aware + translation | 0.1092 |

### F. Reproducibility

The full-paper analyses were pre-registered and the document pushed before any code was written (3 November 2026, 09:15 UTC) [17]. Amendment 1 (analyses E10–E17 and the February re-score; commit f1a3453, 4 November 2026, 22:06 UTC) [18], Amendment 2 (the survivorship stint rule; commit 41efa97, 5 November 2026, 06:49 UTC) [19], Amendment 3 (analyses E18–E23; commit caf0902, 11 November 2026, 16:06 UTC) [20], Amendment 4 (analysis E24; commit 5ab52fa, 11 November 2026, 19:31 UTC) [21], Amendment 5 (analysis E25; commit be61514, 12 November 2026, 14:49 UTC) [22], Amendment 6 (analysis E26; commit 245bafa, 12 November 2026, 18:25 UTC) [23] and Amendment 7 (analysis E27; commit e884afe, 12 November 2026, 22:01 UTC) [24] were each pushed alone, before the analyses they govern were run. Amendment 4 was written after the Amendment 3 results had been read, Amendment 5 after the first audit's result, Amendment 6 after both audits' results and Amendment 7 before any outcome of an older arrival was read; each says so. Later amendments that the paper cites are listed in the references. A gate reproduces every submitted number from the public data to within 10⁻⁹ before any new analysis runs. Every table and figure in this paper is generated by a committed script from saved results of retained runs; the repository records input, code and output hashes for each. The 2026–27 forecasts were frozen on 3 November 2026, 10:55 UTC, file sha256 `f3530c1a5ac369c0…`. The player vignettes were chosen by a rule fixed before any error was read.

### G. Illustration: three 2025–26 arrivals

This box illustrates how the forecasts read for individual players; it is not evidence for them. The rule was fixed before any forecast error was read: for each tier of Table 1, take the 2025–26 EuroLeague arrival with the most continental minutes (ties broken by player name). Minutes are played after arrival, so the rule selects on playing time and therefore on success. All three outperformed every forecast (one of them by less than the rounding of the table), and the league-aware forecast was closer than history alone in none of the three. A single forecast can miss by about ±4.8 EFF/36 at 80% (Individual uncertainty), which is why one season of box scores says less than a scouting report about one player.

Table A8. Three 2025–26 EuroLeague arrivals, one per tier of Table 1, each the arrival with the most continental minutes in his tier. Domestic EFF/36 in 2024–25, with career EFF/36 in brackets († = source season above his own history; none = no earlier season in the data). Forecasts are walk-forward, made before the season.

| Player | Move | Domestic (career) | History only | + translation | League-aware | Actual |
|---|---|---|---|---|---|---|
| Kameron Taylor | Unicaja Malaga, Spain (ACB) → Valencia Basket (tier 1) | 22.1 (19.3) † | 17.1 | 17.2 | 16.7 | 20.1 (40 games) |
| Omari Moore | Darussafaka, Turkey (BSL) → Valencia Basket (tier 2) | 18.2 (none) | 16.2 | 14.5 | 14.6 | 16.2 (43 games) |
| Azuolas Tubelis | Rytas Vilnius, Lithuania (LKL) → Zalgiris Kaunas (tier 3) | 23.0 (24.0) | 19.5 | 16.4 | 17.0 | 21.2 (42 games) |

### H. Forecast level, league biases, table stability and error bands

These tables come from Amendments 3 and 4 [20, 21]. All are exploratory.

Table A9. League biases (forecast minus actual EFF/36) by source league, with 95% cluster-bootstrap intervals. *Registered, against zero*: the history-only forecast's mean signed error as first registered (asterisk: detectable after Holm adjustment). The three *re-based* columns subtract the mean signed error of all arrivals, so they show each league against the average arrival; asterisks mark Holm-adjusted p < 0.05 across the ten leagues, tested for the first two forecasts. *History only* is blind to both leagues; *history + destination* knows the destination but not the source league; *league-aware* knows both.

| Source league | Arrivals | To EuroLeague | Registered, against zero | History only, re-based | History + destination, re-based | League-aware, re-based |
|---|---|---|---|---|---|---|
| Spain (ACB) | 108 | 41% | −1.30 * | −0.93 [−1.64, −0.22] | −1.17 [−1.84, −0.53] * | −0.17 [−0.83, 0.46] |
| France (Pro A) | 70 | 24% | −1.54 | −1.17 [−2.17, −0.17] | −1.11 [−2.10, −0.17] | −0.19 [−1.17, 0.75] |
| Italy (LBA) | 77 | 25% | −1.48 * | −1.11 [−1.73, −0.47] * | −1.04 [−1.70, −0.41] * | −0.66 [−1.31, −0.04] |
| Greece (A1) | 30 | 13% | −0.83 | −0.46 [−1.66, 0.70] | −0.24 [−1.46, 0.86] | +0.01 [−1.14, 1.14] |
| Turkey (BSL) | 108 | 29% | −0.03 | +0.34 [−0.35, 1.06] | +0.33 [−0.37, 1.01] | +0.21 [−0.48, 0.88] |
| Israel (Winner League) | 49 | 29% | +0.03 | +0.40 [−0.46, 1.27] | +0.45 [−0.31, 1.21] | −0.02 [−0.78, 0.72] |
| Germany (BBL) | 87 | 25% | +0.44 | +0.81 [0.14, 1.58] | +0.91 [0.26, 1.60] * | +0.04 [−0.59, 0.72] |
| Adriatic (ABA) | 70 | 27% | +0.48 | +0.85 [−0.28, 1.74] | +0.92 [−0.10, 1.73] | +0.42 [−0.67, 1.27] |
| Lithuania (LKL) | 48 | 17% | +0.50 | +0.87 [0.07, 1.78] | +1.05 [0.19, 1.95] | +0.20 [−0.70, 1.15] |
| VTB United League | 27 | 59% | +1.66 | +2.03 [0.62, 3.38] | +1.48 [0.07, 2.79] | +0.67 [−0.75, 2.03] |

Table A10. Mean signed error (forecast minus actual EFF/36) of three forecasts, with 95% cluster-bootstrap intervals. Below zero, the forecast expected less than arrivals delivered.

| Arrivals | n | History only | History + destination | League-aware |
|---|---|---|---|---|
| All arrivals | 674 | −0.37 [−0.69, −0.05] | −0.44 [−0.76, −0.14] | −0.47 [−0.78, −0.18] |
| EuroLeague | 194 | +1.24 [0.76, 1.71] | −0.04 [−0.53, 0.45] | −0.03 [−0.51, 0.44] |
| EuroCup | 480 | −1.02 [−1.45, −0.65] | −0.61 [−1.02, −0.24] | −0.65 [−1.04, −0.30] |
| Season 2020–21 | 134 | +0.10 [−0.58, 0.77] | +0.01 [−0.65, 0.67] | +0.01 [−0.64, 0.64] |
| Season 2021–22 | 101 | +0.48 [−0.20, 1.20] | +0.32 [−0.33, 0.99] | +0.21 [−0.48, 0.94] |
| Season 2022–23 | 106 | −0.87 [−1.56, −0.09] | −0.90 [−1.54, −0.18] | −0.85 [−1.45, −0.19] |
| Season 2023–24 | 102 | −0.45 [−1.70, 0.61] | −0.50 [−1.72, 0.54] | −0.58 [−1.73, 0.43] |
| Season 2024–25 | 104 | −0.15 [−0.92, 0.54] | −0.11 [−0.91, 0.60] | −0.10 [−0.86, 0.57] |
| Season 2025–26 | 127 | −1.24 [−1.92, −0.63] | −1.37 [−2.03, −0.78] | −1.43 [−2.09, −0.82] |

Table A11. The equivalent of an ACB 16 for EuroLeague arrivals in each yearly refit (the fit that forecast that season, using earlier seasons only) and in the full fit. The refits share most of their data: the table describes stability and is not a test.

| Source league | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | Full fit |
|---|---|---|---|---|---|---|---|
| Spain (ACB) | 16.0 | 16.0 | 16.0 | 16.0 | 16.0 | 16.0 | 16.0 |
| France (Pro A) | 15.5 | 15.9 | 16.4 | 16.6 | 16.5 | 16.5 | 16.1 |
| Italy (LBA) | 16.5 | 16.6 | 17.0 | 17.6 | 17.5 | 17.1 | 16.7 |
| Greece (A1) | 16.6 | 16.8 | 17.0 | 17.4 | 17.7 | 17.6 | 17.3 |
| Turkey (BSL) | 17.1 | 17.1 | 17.7 | 18.2 | 18.4 | 18.3 | 17.9 |
| Israel (Winner League) | 17.6 | 18.1 | 18.1 | 18.6 | 18.8 | 18.5 | 18.2 |
| Adriatic (ABA) | 17.1 | 18.2 | 18.7 | 18.8 | 19.0 | 19.0 | 18.6 |
| Germany (BBL) | 18.2 | 18.4 | 18.7 | 19.4 | 19.6 | 19.4 | 19.1 |
| VTB United League | 17.6 | 18.6 | 19.1 | 19.7 | 19.8 | 19.7 | 19.1 |
| Lithuania (LKL) | 18.6 | 18.1 | 18.3 | 19.0 | 19.7 | 19.5 | 19.2 |

The mean distance of the nine other leagues from Spain's 16, in the refit that forecast 2020–21, the refit that forecast 2025–26 and the full fit: 1.2, 2.4 and 2.0 EFF/36 for EuroLeague arrivals; 1.2, 2.1 and 1.8 for EuroCup arrivals. Table A11 prints the refits for EuroLeague arrivals; those for EuroCup arrivals are drawn in Figure A3, and their values are in the table of refits released with the paper. These describe the values of the refits and were added after they were seen; the cause was not examined [34].

Table A12. Error-band coverage by source league for the league-aware forecast, seasons 2021–2025, with Wilson 95% intervals.

| Source league | Arrivals | 80% bands | 95% bands |
|---|---|---|---|
| France (Pro A) | 50 | 76.0% [62.6%, 85.7%] | 90.0% [78.6%, 95.7%] |
| Spain (ACB) | 88 | 78.4% [68.7%, 85.7%] | 93.2% [85.9%, 96.8%] |
| Lithuania (LKL) | 39 | 79.5% [64.5%, 89.2%] | 100.0% [91.0%, 100.0%] |
| Turkey (BSL) | 86 | 80.2% [70.6%, 87.3%] | 94.2% [87.1%, 97.5%] |
| Adriatic (ABA) | 49 | 81.6% [68.6%, 90.0%] | 95.9% [86.3%, 98.9%] |
| Italy (LBA) | 66 | 84.8% [74.3%, 91.6%] | 93.9% [85.4%, 97.6%] |
| VTB United League | 14 | 85.7% [60.1%, 96.0%] | 100.0% [78.5%, 100.0%] |
| Germany (BBL) | 79 | 86.1% [76.8%, 92.0%] | 97.5% [91.2%, 99.3%] |
| Israel (Winner League) | 44 | 90.9% [78.8%, 96.4%] | 97.7% [88.2%, 99.6%] |
| Greece (A1) | 25 | 92.0% [75.0%, 97.8%] | 96.0% [80.5%, 99.3%] |

Table A13. The above-average-season term. The jump is the source rate minus the earlier career rate when positive. The registered model keeps the flag alone; the other rows are sensitivity checks and are not used for any forecast in this paper.

| Coefficient | Full fit through 2025 | 95% interval | Range over six refits |
|---|---|---|---|
| Registered model: flag | −1.39 | see Appendix K | negative in every refit (Appendix K) |
| Flag, with the jump added | −1.27 | [−1.83, −0.63] | −1.39 to −1.01 |
| Jump, per EFF/36 above history | +0.23 | [0.07, 0.41] | 0.15 to 0.36 |
| Jump replacing the flag | +0.28 | [0.10, 0.46] | 0.20 to 0.40 |

Walk-forward, the registered model misses by 2.924 EFF/36, against 2.909 with the jump added (difference +0.015, interval −0.013 to 0.044) and 2.905 with the jump replacing the flag (difference +0.019, interval −0.033 to 0.071). Neither difference is detectable, and the registered model is kept, as Amendment 3 requires.

**How rankings were compared.** Within each competition and season, we compare every pair of arrivals [49]. For pairs of arrivals from different source leagues, the league-aware forecast orders 73.7% correctly versus 72.4% for history alone: a 1.32 percentage-point gain (interval 0.39 to 2.28) over 19,668 pairs, which share players and are not independent observations (Figure A2); within one source league the gain is +0.04 (−0.77 to 0.89). Translation added to the league-aware forecast changes 2.6% of all rankings and is right on 54.4% of those changes (interval 46.0% to 63.9%), not distinguishable from a coin flip. For the predicted top 10 per competition and season, none of the registered differences is detectable. The ranking improvement is modest, and neither shortlist quality nor financial value has been demonstrated.

**Stability and close calls.** From one summer to the next a league's equivalent moved by a median of 0.25 EFF/36 (at most 1.10). Tiers follow the rule registered before the analysis [17]: leagues are sorted within a destination by the forecast for a domestic and career rate of 16 (Table A23), highest first, and a league starts a new tier when the top league of the current tier exceeds it in at least 90% of bootstrap draws; otherwise it joins that tier. Adriatic (ABA), Israel (Winner League) and Italy (LBA) are close calls between tiers (bootstrap shares within 0.05 of the 0.90 cut-off). **The ordering result restated.** Counted as changed comparisons, the league table changes 8.5% of cross-league comparisons and is right on 57.7% of them (interval 52.4% to 63.1%); this restates the ordering result of the main text and is not new evidence. The predicted top 10 per competition and season achieved 19.31 EFF/36 under history, 19.47 with translation, 19.41 with the league numbers and 19.53 with both; none of the registered differences is detectable.

![Figure A2. Top: change in ordering accuracy versus history alone, for pairs from different or the same source league (blue: the league-aware forecast; grey: history plus translation). Bottom: accuracy among rankings changed by adding translation to the league-aware forecast (blue) and to history alone (grey) (50% = coin flip). Lines: 95% cluster-bootstrap intervals.](figures/fig3_decisions.png)

![Figure A3. The Equivalents in each yearly refit. Each line is one source league: the domestic EFF/36 that gives the same continental forecast as 16 in Spain's ACB when the table is refitted on the arrivals before each destination season, for EuroLeague arrivals (left) and EuroCup arrivals (right). Colour: the league's tier in the full fit. Dashed line: Spain's ACB, the reference. The refits share most of their data, so the figure describes stability and is not independent validation.](figures/fig_stability.png)

**The gap guide and the error bands.** Table A14 holds the guide to forecast gaps of the main text, and Figure A4 draws it beside the same guide for history alone. For scale on the ordering result, a forecaster who knew every player's true rate would order 82.1% of cross-league pairs (interval 80.0% to 83.9%; normal-noise model), so most of the remaining gap stays open. At the 95% level the conformal intervals cover 95.2% of arrivals (about ±7.4 EFF/36); Figure A5 shows the 80% coverage by source league and by season.

Table A14. How far to trust a forecast gap. Over every pair of arrivals in the same competition and season (22,365 pairs), the share in which the player with the higher league-aware forecast had the higher realised EFF/36, by the size of the gap between the two forecasts (95% cluster-bootstrap intervals; bins fixed in advance).

| Forecast gap (EFF/36) | Pairs | Higher forecast was better | … cross-league pairs only |
|---|---|---|---|
| 0 to 1 | 4,296 | 54.5% [52.0%, 56.7%] | 54.6% |
| 1 to 2 | 4,033 | 63.0% [60.5%, 66.0%] | 63.3% |
| 2 to 3 | 3,588 | 70.9% [68.2%, 74.8%] | 71.4% |
| 3 to 4 | 2,955 | 78.0% [74.6%, 81.4%] | 78.8% |
| 4 to 6 | 4,030 | 85.1% [82.1%, 88.3%] | 85.2% |
| 6 or more | 3,463 | 93.3% [90.4%, 95.9%] | 93.3% |

![Figure A4. How far to trust a forecast gap. Share of pairs of arrivals, in the same competition and season, in which the player with the higher forecast had the higher realised EFF/36, by the size of the gap between the two forecasts. Blue: the league-aware forecast (the values of Table A14). Grey: history alone. Lines: 95% cluster-bootstrap intervals. Pairs share players and are not independent observations.](figures/fig_gap_guide.png)

![Figure A5. Coverage of the 80% error bands. Share of arrivals whose outcome fell inside the walk-forward 80% band of the league-aware forecast, by source league (left; lines: 95% Wilson intervals) and by destination season (right). Dashed line: the nominal 80%.](figures/fig_bands.png)

### I. The older-seasons test

Analysis E27 [24] scores the frozen models on arrivals from the ABA League and Israel's Winner League in destination seasons 2008–09 to 2015–16. **Order of events.** A freeze run wrote one forecast for every eligible source player-season and both destinations and joined no outcome. The file's sha256 (`1d3e3bfb9d08b9d0…`) was committed and pushed. A first scoring run then stopped on a programming error before any error, comparison or output existed (it wrote 0 files); no rule was changed, and the second scoring run is the only one that read outcomes. **Gates.** In the freeze run, the same code reproduced the frozen 2026–27 forecasts (3,478 rows, 17 forecasts each) to within 10⁻⁹. Outcomes rebuilt from the API's season totals joined 661 of the 674 benchmark arrivals and correlated 0.9996 with the benchmark outcomes, with the three readings unchanged. On Israel, where full first names exist on both sides, the linking code reproduced its registered measurement: 9 of 282 links made by initial and surname join different first names, and 0 of 181 among rare surnames. Each gate has a negative control that failed as required. **Source games.** Source rates use only league games in which the players' points add up to the final score; that left out 2 of 1,498 in the ABA League and 45 of 1,382 in Israel's Winner League. **Linking.** A source player-season is linked to a EuroLeague API person when initial plus surname is unique on both sides and the first three letters of the first names agree. In the ABA League, 510 of 1,365 source player-seasons are linked and 18 are dropped because the first names differ; in Israel's Winner League, 199 of 1,034 source player-seasons are linked and 9 are dropped because the first names differ. **Arrivals.** The eligibility rules are those of the benchmark. Of the 180 arrivals, 60 went to the EuroLeague and 120 to the EuroCup; 67.2% have a rare surname and 33.3% no earlier season on disk. A version that includes Spain's ACB was computed in the same runs and is withheld until ACB's written permission arrives; nothing in this appendix depends on it.

Table A15. The three comparisons on the older arrivals (EFF/36, 95% intervals clustered by player and destination club-season; positive favours translation in the first and third columns and the league-aware forecast in the second). Only the first row supports a registered statement; a null on any other row reads "not detectable at this n".

| Arrivals | n | Translation vs history | League-aware vs history + translation | Translation added to league-aware |
|---|---|---|---|---|
| All arrivals (the registered test) | 180 | +0.001 [−0.146, 0.149] | +0.031 [−0.017, 0.079] | −0.015 [−0.031, 0.002] |
| Rare surnames (registered sensitivity) | 121 | +0.037 [−0.142, 0.216] | +0.049 [−0.008, 0.105] | −0.0196 [−0.0388, −0.0003] |
| With an earlier season on disk | 120 | −0.038 [−0.205, 0.128] | +0.013 [−0.043, 0.070] | −0.013 [−0.032, 0.007] |
| Continental club is the source club | 53 | −0.221 [−0.423, −0.020] | +0.019 [−0.040, 0.077] | −0.016 [−0.039, 0.006] |
| Source: Adriatic (ABA) | 131 | +0.000 [−0.167, 0.168] | +0.033 [−0.011, 0.078] | −0.016 [−0.034, 0.003] |
| Source: Israel (Winner League) | 49 | +0.005 [−0.300, 0.310] | +0.026 [−0.110, 0.162] | −0.011 [−0.047, 0.025] |
| Destination: EuroLeague | 60 | +0.191 [−0.219, 0.600] | +0.035 [−0.042, 0.111] | −0.022 [−0.053, 0.009] |
| Destination: EuroCup | 120 | −0.0933 [−0.1871, 0.0005] | +0.030 [−0.032, 0.091] | −0.011 [−0.029, 0.007] |

Table A16. Forecast level on the older arrivals: mean absolute error and mean error (forecast minus actual EFF/36; below zero, the forecast expected less than arrivals delivered), and arrivals by destination season.

| Forecast | MAE | Mean error |
|---|---|---|
| History only | 2.862 | −0.005 |
| History + translation | 2.861 | −0.718 |
| League-aware (one number per league) | 2.830 | −0.774 |
| League-aware + translation | 2.844 | −0.811 |

| Destination season | 2008–09 | 2009–10 | 2010–11 | 2011–12 | 2012–13 | 2013–14 | 2014–15 | 2015–16 |
|---|---|---|---|---|---|---|---|---|
| Arrivals | 12 | 12 | 24 | 26 | 24 | 52 | 17 | 13 |

These models were fitted using later seasons, so this is a backward transfer test with outcomes withheld during forecast generation, not a historical simulation of what a club could have known then. The small set of source leagues and wide intervals limit external validation.

Table A17. The league-aware forecast against the two plainer forecasts on the older arrivals (E28, exploratory; a second reading of outcomes read once). Differences in MAE, EFF/36; positive favours the league-aware forecast; 95% intervals clustered by player and destination club-season. *Detectable*: the smallest difference this sample could detect with 80% power.

| Difference in MAE | Weighting | n | MAE, first forecast | MAE, league-aware | Difference | 95% interval | Detectable | Reading |
|---|---|---|---|---|---|---|---|---|
| History alone minus league-aware | Unweighted | 180 | 2.862 | 2.830 | +0.033 | [−0.099, 0.164] | 0.188 | includes zero |
| History alone minus league-aware | Weighted by minutes | 180 | 2.630 | 2.749 | −0.118 | [−0.276, 0.039] | 0.225 | includes zero |
| History + destination minus league-aware | Unweighted | 180 | 2.763 | 2.830 | −0.067 | [−0.144, 0.010] | 0.110 | includes zero |
| History + destination minus league-aware | Weighted by minutes | 180 | 2.620 | 2.749 | −0.129 | [−0.209, −0.048] | 0.114 | below zero |

Table A18. Two published league scales in the place of the paper's league numbers on the older arrivals (E34, exploratory). Each scale enters the destination-only forecast as one coefficient times its value for the source league. For the 2015 table [8] the forecast's coefficients are those frozen for the 2026–27 test; for the 2026 scale [38] they are fitted on the paper's training arrivals through 2025. Errors and differences are mean absolute errors in EFF/36. *G*: the error with the published scale minus the error of the league-aware forecast; below zero, the published scale was the more accurate. *T*: the error of the destination-only forecast minus the error with the published scale; below zero, the destination-only forecast was the more accurate. The column *Difference* holds G or T, as the row says. 95% intervals clustered by player and destination club-season. *Detectable*: the smallest difference this sample could detect with 80% power. The split by source league is described and not tested. These readings were first made outside the registration, in a review of the paper, and the rules for printing them were written after their values had been seen; they are exploratory [39].

| Arrivals | Published scale | Compared with | Weighting | MAE, published scale | MAE, compared forecast | Difference | 95% interval | Detectable |
|---|---|---|---|---|---|---|---|---|
| All 180 | 2015 table | league numbers (G) | Unweighted | 2.766 | 2.830 | −0.063 | [−0.128, 0.002] | 0.093 |
| All 180 | 2015 table | league numbers (G) | Weighted by playing time | 2.667 | 2.749 | −0.082 | [−0.152, −0.011] | 0.101 |
| All 180 | 2015 table | destination only (T) | Unweighted | 2.766 | 2.763 | −0.004 | [−0.046, 0.039] | 0.061 |
| All 180 | 2015 table | destination only (T) | Weighted by playing time | 2.667 | 2.620 | −0.047 | [−0.097, 0.003] | 0.071 |
| All 180 | 2026 scale | league numbers (G) | Unweighted | 2.768 | 2.830 | −0.062 | [−0.122, −0.002] | 0.086 |
| All 180 | 2026 scale | league numbers (G) | Weighted by playing time | 2.645 | 2.749 | −0.104 | [−0.167, −0.040] | 0.091 |
| All 180 | 2026 scale | destination only (T) | Unweighted | 2.768 | 2.763 | −0.005 | [−0.027, 0.018] | 0.032 |
| All 180 | 2026 scale | destination only (T) | Weighted by playing time | 2.645 | 2.620 | −0.025 | [−0.049, −0.001] | 0.034 |
| Adriatic league (131) | 2015 table | league numbers (G) | Unweighted | 2.948 | 3.041 | −0.093 | [−0.178, −0.007] | — |
| Adriatic league (131) | 2015 table | league numbers (G) | Weighted by playing time | 2.884 | 3.024 | −0.140 | [−0.233, −0.047] | — |
| Adriatic league (131) | 2015 table | destination only (T) | Unweighted | 2.948 | 2.952 | +0.004 | [−0.016, 0.023] | — |
| Adriatic league (131) | 2015 table | destination only (T) | Weighted by playing time | 2.884 | 2.881 | −0.003 | [−0.024, 0.017] | — |
| Adriatic league (131) | 2026 scale | league numbers (G) | Unweighted | 2.954 | 3.041 | −0.086 | [−0.166, −0.006] | — |
| Adriatic league (131) | 2026 scale | league numbers (G) | Weighted by playing time | 2.892 | 3.024 | −0.132 | [−0.219, −0.045] | — |
| Adriatic league (131) | 2026 scale | destination only (T) | Unweighted | 2.954 | 2.952 | −0.003 | [−0.028, 0.022] | — |
| Adriatic league (131) | 2026 scale | destination only (T) | Weighted by playing time | 2.892 | 2.881 | −0.011 | [−0.037, 0.015] | — |
| Israel (49) | 2015 table | league numbers (G) | Unweighted | 2.281 | 2.265 | +0.016 | [−0.039, 0.070] | — |
| Israel (49) | 2015 table | league numbers (G) | Weighted by playing time | 2.137 | 2.077 | +0.060 | [0.002, 0.119] | — |
| Israel (49) | 2015 table | destination only (T) | Unweighted | 2.281 | 2.258 | −0.023 | [−0.181, 0.135] | — |
| Israel (49) | 2015 table | destination only (T) | Weighted by playing time | 2.137 | 1.983 | −0.154 | [−0.320, 0.011] | — |
| Israel (49) | 2026 scale | league numbers (G) | Unweighted | 2.268 | 2.265 | +0.003 | [−0.052, 0.057] | — |
| Israel (49) | 2026 scale | league numbers (G) | Weighted by playing time | 2.042 | 2.077 | −0.035 | [−0.094, 0.025] | — |
| Israel (49) | 2026 scale | destination only (T) | Unweighted | 2.268 | 2.258 | −0.010 | [−0.067, 0.047] | — |
| Israel (49) | 2026 scale | destination only (T) | Weighted by playing time | 2.042 | 1.983 | −0.059 | [−0.115, −0.003] | — |

The 2015 table was printed in November 2015, during the last of these seasons, and may have been built on them; the paper cannot tell how far. The 2026 scale is built on moves of 2021–22 to 2025–26, as the paper's league numbers are fitted on arrivals of 2017 to 2025. The intervals treat the fitted forecasts as fixed and describe arrivals from these two leagues; each league term is one constant per league, so they say nothing about other leagues. Both published scales place the Adriatic league fourth of the ten source leagues, and the paper's league numbers place it seventh; the paper reads neither as league strength.

Table A19. Where the league table missed (E29, descriptive; a further reading of outcomes already read). *Move*: the league-aware forecast minus the forecast that knows only the destination. *Error*: forecast minus outcome; below zero, the forecast was below what arrivals delivered. Means in EFF/36 with 95% intervals clustered by player and destination club-season.

| Source league | Arrivals of | Weighting | n | Move made by the league table | Error without the table | Error with the table |
|---|---|---|---|---|---|---|
| The Adriatic league | 2008–2015 | Unweighted | 131 | −0.68 [−0.69, −0.67] | −0.35 [−1.00, 0.30] | −1.04 [−1.69, −0.38] |
| The Adriatic league | 2008–2015 | Weighted by minutes | 131 | −0.68 [−0.69, −0.67] | −0.73 [−1.35, −0.10] | −1.41 [−2.04, −0.78] |
| The Adriatic league | 2020–2025 | Unweighted | 70 | −0.53 [−0.65, −0.41] | +0.47 [−0.55, 1.50] | −0.06 [−1.15, 1.04] |
| The Adriatic league | 2020–2025 | Weighted by minutes | 70 | −0.52 [−0.65, −0.40] | +0.06 [−1.11, 1.24] | −0.46 [−1.69, 0.77] |
| Israel | 2008–2015 | Unweighted | 49 | −0.37 [−0.39, −0.36] | +0.30 [−0.36, 0.96] | −0.07 [−0.74, 0.59] |
| Israel | 2008–2015 | Weighted by minutes | 49 | −0.37 [−0.38, −0.35] | −0.17 [−0.90, 0.56] | −0.54 [−1.27, 0.19] |
| Israel | 2020–2025 | Unweighted | 49 | −0.50 [−0.54, −0.45] | +0.01 [−0.79, 0.81] | −0.49 [−1.28, 0.31] |
| Israel | 2020–2025 | Weighted by minutes | 49 | −0.51 [−0.56, −0.46] | −0.09 [−1.03, 0.84] | −0.61 [−1.53, 0.32] |
| All arrivals | 2008–2015 | Unweighted | 180 | −0.60 [−0.63, −0.57] | −0.18 [−0.68, 0.33] | −0.77 [−1.28, −0.26] |
| All arrivals | 2008–2015 | Weighted by minutes | 180 | −0.59 [−0.62, −0.55] | −0.57 [−1.04, −0.09] | −1.15 [−1.63, −0.68] |
| All arrivals | 2020–2025 | Unweighted | 674 | −0.03 [−0.11, 0.05] | −0.44 [−0.78, −0.10] | −0.47 [−0.80, −0.14] |
| All arrivals | 2020–2025 | Weighted by minutes | 674 | +0.01 [−0.08, 0.09] | −0.97 [−1.29, −0.64] | −0.96 [−1.28, −0.65] |

Between the two periods the error without the table changed as follows (older arrivals minus arrivals of 2020–2025): for arrivals from the Adriatic league the change between the two periods is not distinguishable from zero at this n (−0.83 EFF/36, interval −2.04 to 0.39) (weighted by minutes: −0.79, interval −2.13 to 0.55); for arrivals from Israel the change between the two periods is not distinguishable from zero at this n (+0.29 EFF/36, interval −0.75 to 1.33) (weighted by minutes: −0.08, interval −1.26 to 1.11). Three limits apply. (1) On the older arrivals the forecasts come from the model fitted on every season through 2025. On the arrivals of 2020–2025 each forecast comes from a model fitted on earlier seasons only. (2) The older source statistics come from the leagues' own box scores. The source statistics of 2020–2025 come from a different provider. (3) A mean error also carries the general level of the forecasts in that period. The rows for all arrivals are printed so that a reader can see that level. This shows where the forecast missed; it cannot separate a change in league strength from a change in which players clubs signed, in the data source or in the level of the forecasts.

The change between the two periods is not distinguishable from zero for either league at these n, so the table shows where the forecast missed and not why.

### J. Conditional noise reference and model comparisons

Absolute MAE is the primary scale throughout the paper. Odd/even games imply full-season reliability 0.69 for EFF/36 [50]. Under a stationary player-rate and normal-noise approximation, the estimated full-season noise reference is 2.183 EFF/36; a direct odd/even calculation gives 2.047. Subtracting each reference from the history-only MAE gives a conditional denominator for the share of error removed. Translation's gain is 17.6% on the normal reference (Figure A6) and 15.4% on the direct reference. These estimates depend on the noise model, playing-time exposure and within-season stability. They are not a universal irreducible error bound or evidence that other features cannot help.

**How much of the reducible error is removed.** One season of EFF/36 is a noisy measurement, so no forecast can reach zero error. Against a normal-noise reference of 2.183 EFF/36, the league-aware forecast removes 18.8% of the error that history alone leaves above the reference, and history plus translation removes 17.6% (Figure A6). These shares depend on the noise model and are not a bound on what other features could add.

![Figure A6. Estimated reducible-error share under the normal-noise reference (2.183 EFF/36), relative to history only. Grey: without translation; blue: with translation. Lines: cluster-bootstrap intervals where available. The denominator is conditional on the noise assumptions; the plot compares only the fitted configurations.](figures/fig2_avoidable.png)

**The ladder in full, and the margin.** Table A20 gives every row of the ladder. Pair-specific slopes perform worse here (MAE 2.993 versus 2.924), consistent with, but not proof of, overfitting. League context recovers 107% of translation's gain (interval 85% to 148%). Values above 100% arise because the league-aware point estimate is slightly better, not because the gain is known precisely. The 2% margin (for EFF/36, ±0.058) is pre-specified for the five other recipes and, as 2% of each outcome's own error, for the other outcomes; ±0.058 EFF/36 is 36% of the original translation gain. Across six factor recipes, the largest upper bound on translation's increment is 0.025 EFF/36 (Appendix C, Figure A1). On each of the three other outcomes (points, Game Score and EFF per 100 possessions) translation gains over history, and the upper bound of what it adds to the league-aware forecast stays below 2% of error (Appendix B). Season by season, translation's gain over history is positive in 6 of 6 seasons, and the league-aware forecast is ahead of history plus translation in 5 of 6; these are point estimates, described and not tested.

Table A20. The full ladder; Figure 3 draws the rows for history only, + destination and the primary league numbers (λ = 10). Forecast error (MAE, EFF/36) on the same 674 arrivals, without and with the translation feature. Gain = MAE without − MAE with; positive favours translation; 95% intervals clustered by player and destination club-season.

| Forecast knows… | MAE without | MAE with | Gain from translation [95% CI] |
|---|---|---|---|
| History only | 3.096 | 2.935 | +0.161 [0.077, 0.246] |
| + destination (intercept and slope) | 2.989 | 2.940 | +0.049 [−0.013, 0.111] |
| + one number per league, λ = 1 | 2.928 | 2.932 | −0.004 [−0.026, 0.018] |
| + one number per league, λ = 10 (primary) | 2.924 | 2.926 | −0.002 [−0.028, 0.024] |
| + one number per league, λ = 100 | 2.942 | 2.929 | +0.014 [−0.030, 0.058] |
| + pair-specific slopes, λ = 10 | 2.993 | 2.998 | −0.005 [−0.029, 0.019] |

Table A21. The same three comparisons on every check (95% intervals clustered by player and destination club-season). *Translation vs history*: translation's gain against a league-blind forecast. *League-aware vs history + translation*: positive means one number per league (λ = 10) without translation is more accurate. *Translation added*: what translation adds once the forecast knows both leagues.

| Check | n | Translation vs history | League-aware vs history + translation | Translation added to league-aware |
|---|---|---|---|---|
| Main benchmark, EFF/36 | 674 | +0.161 [0.077, 0.246] | +0.011 [−0.027, 0.049] | −0.002 [−0.028, 0.024] |
| Points/36 | 674 | +0.109 [0.031, 0.186] | +0.036 [−0.004, 0.075] | −0.010 [−0.024, 0.004] |
| Game Score/36 | 674 | +0.147 [0.086, 0.208] | +0.023 [−0.008, 0.054] | −0.002 [−0.009, 0.004] |
| EFF per 100 possessions | 674 | +0.155 [0.071, 0.238] | +0.010 [−0.043, 0.063] | −0.003 [−0.031, 0.026] |
| Seven seasons, 2019–2025 | 812 | +0.142 [0.070, 0.214] | +0.013 [−0.022, 0.047] | −0.005 [−0.031, 0.022] |
| Age-aware forecasts | 673 | +0.161 [0.076, 0.247] | +0.011 [−0.028, 0.051] | −0.004 [−0.032, 0.024] |
| EuroLeague arrivals only | 194 | +0.169 [−0.057, 0.395] | +0.072 [−0.011, 0.154] | −0.006 [−0.058, 0.046] |
| EuroCup arrivals only | 480 | +0.158 [0.079, 0.236] | −0.014 [−0.055, 0.028] | −0.000 [−0.030, 0.030] |
| Weighted by destination minutes | 674 | +0.098 [−0.003, 0.198] | +0.038 [−0.004, 0.081] | −0.017 [−0.045, 0.011] |
| At least 3 games and 60 minutes | 720 | +0.122 [0.043, 0.201] | +0.013 [−0.023, 0.050] | −0.001 [−0.025, 0.023] |
| … weighted by destination minutes | 720 | +0.087 [−0.010, 0.185] | +0.038 [−0.003, 0.079] | −0.017 [−0.044, 0.011] |
| Without arrivals classed as identity mismatches | 670 | +0.167 [0.081, 0.252] | +0.009 [−0.029, 0.047] | −0.001 [−0.027, 0.025] |

Table A22. The league-aware forecast against the two plainer forecasts on the benchmark arrivals of 2020–2025 (E28, exploratory). Each cell: difference in MAE, EFF/36 (positive favours the league-aware forecast), its 95% interval clustered by player and destination club-season, and after the semicolon the smallest difference that subset could detect with 80% power. Only the first row carries registered wording; the subsets are small and are shown for transparency.

| Arrivals | n | vs history alone | vs history alone, weighted by minutes | vs destination-only | vs destination-only, weighted by minutes |
|---|---|---|---|---|---|
| All arrivals | 674 | +0.172 [0.096, 0.248]; 0.108 | +0.136 [0.046, 0.226]; 0.128 | +0.065 [0.014, 0.117]; 0.073 | +0.073 [0.010, 0.136]; 0.091 |
| EuroLeague arrivals only | 194 | +0.241 [0.051, 0.431]; 0.271 | +0.034 [−0.181, 0.250]; 0.307 | +0.119 [0.007, 0.230]; 0.159 | +0.149 [0.016, 0.283]; 0.190 |
| EuroCup arrivals only | 480 | +0.144 [0.070, 0.218]; 0.106 | +0.186 [0.104, 0.268]; 0.117 | +0.044 [−0.013, 0.101]; 0.082 | +0.035 [−0.034, 0.105]; 0.099 |
| Destination season 2020–21 | 134 | +0.185 [0.033, 0.336]; 0.215 | +0.201 [0.031, 0.370]; 0.241 | +0.048 [−0.047, 0.144]; 0.135 | +0.086 [−0.018, 0.190]; 0.147 |
| Destination season 2021–22 | 101 | +0.111 [−0.093, 0.314]; 0.289 | +0.121 [−0.125, 0.367]; 0.349 | +0.018 [−0.119, 0.154]; 0.193 | +0.054 [−0.110, 0.217]; 0.233 |
| Destination season 2022–23 | 106 | +0.344 [0.183, 0.505]; 0.228 | +0.323 [0.139, 0.507]; 0.261 | +0.176 [0.054, 0.299]; 0.174 | +0.206 [0.067, 0.344]; 0.196 |
| Destination season 2023–24 | 102 | +0.195 [−0.028, 0.418]; 0.316 | +0.131 [−0.123, 0.386]; 0.361 | +0.082 [−0.046, 0.210]; 0.181 | +0.092 [−0.058, 0.242]; 0.212 |
| Destination season 2024–25 | 104 | +0.151 [−0.082, 0.384]; 0.331 | +0.076 [−0.182, 0.334]; 0.366 | +0.108 [−0.033, 0.248]; 0.199 | +0.084 [−0.087, 0.255]; 0.243 |
| Destination season 2025–26 | 127 | +0.063 [−0.118, 0.244]; 0.257 | −0.024 [−0.248, 0.200]; 0.318 | −0.019 [−0.159, 0.121]; 0.198 | −0.060 [−0.247, 0.126]; 0.264 |

Figure A1 reports nominal intervals for all six recipes; every recipe improves on history alone (0.103–0.161 EFF/36). The smallest Holm-adjusted p-value for an increment is 1.00 [51].

On Game Score/36 a forecast that knows only the destination still gains from translation (0.045 Game Score/36, interval 0.011 to 0.079): source-league adjustment matters. The EuroLeague gain over history is 0.169 (interval −0.057 to 0.395); the competitions do not differ detectably in that gain (p = 0.93) or in what translation adds to the league-aware forecast (p = 0.85). Table A21 gives the three comparisons for each competition; both head-to-head intervals include zero. On 720 arrivals with at least three games and 60 minutes the pattern holds unweighted, but the minutes-weighted gain over history spans zero (0.087, interval −0.010 to 0.185), so the registered claim for this check does not hold. On all 808 arrivals, knowing the leagues also predicts how much a signing will play, mostly from knowing the destination (Table A7).

A ridge model using the full domestic box-score profile, minutes, usage, age, leagues and source-club win share misses by 2.943; the fixed, untuned boosted-tree configuration misses by 3.032, against 2.924 for the league-aware forecast. These specific configurations did not improve MAE. They do not establish a performance ceiling for richer or tuned models. Translation's upper interval bound in boosted trees is 2.66% of error, above the 2% margin; in ridge it is 0.26% (Table A5). Each share is the upper end of the interval of translation's increment (0.081 EFF/36 for the boosted trees, 0.008 for the ridge) divided by the error of the same model without translation, both unrounded; Table A5 prints those errors and not these intervals.

### K. Bias, indicator specification, descriptive skills and an evaluation checklist

**The forecasts run low.** On average the league-aware forecast is 0.47 EFF/36 below what arrivals delivered (interval −0.78 to −0.18): −0.65 for EuroCup arrivals and −0.03 for EuroLeague arrivals. The shortfall is largest in the latest season, 2025–26 (−1.43), when the 80% error bands also covered least (74.0%) and EuroCup arrivals produced 1.18 EFF/36 more than EuroCup arrivals of earlier seasons (all EuroCup players: 0.27 more); we describe this and claim no cause. The other forecasts share the shortfall (Appendix Table A10), so the comparisons between them stand.

**League biases.** Figure 2 shows each league's error against the average arrival for a forecast that knows the destination but not the source league. That is the fair comparison, because a forecast blind to both leagues also misjudges the two competitions. **Measured against the average arrival, that forecast underrates arrivals from Spain by 1.17 and Italy by 1.04 EFF/36 and overrates arrivals from Germany by 0.91.** Once the forecast knows the destination, the league table still flattens the league pattern. The spread of league biases falls from 0.93 to 0.32 EFF/36 (difference 0.61, interval 0.29 to 0.63); knowing the destination alone does not flatten it (difference −0.01, interval −0.10 to 0.08). The first estimate sits at the top of its interval because resampling adds noise to a root mean square and so inflates the smaller spread most: the league-aware spread itself sits at the bottom of its own interval, 0.29 to 0.75. Three caveats apply. France points the same way (−1.11), but its bias is not detectable after the adjustment for testing ten leagues. With the forecast blind to both leagues, only Italy's bias is detectable after that adjustment (Appendix Table A9 shows every version, including the first-registered errors). And Italy stays underrated by the league-aware forecast itself (−0.66, interval −1.31 to −0.04).

**Above-history indicator.** The sentence registered for this result reads: **Holding his domestic rate and history fixed, a player signed after a season above his own history is forecast 1.39 EFF/36 lower.** That wording needs a clarification. The flag a = 1[x > h] is determined by domestic rate and history, so it cannot vary while both remain fixed. The coefficient (−1.39 EFF/36) is a step in the fitted forecast at x = h, not an identified timing penalty. The interval is −1.93 to −0.75, and the estimate is negative in all 6 season-by-season refits. The indicator is common: 63% of signings followed an above-average season, against 53% of all comparable domestic player-seasons. The coefficient is model-dependent. The data do not show the discount growing with the size of the jump. The estimate points the other way (+0.23 EFF/36 per point of jump, interval 0.07 to 0.41; Appendix Table A13): the fitted indicator association weakens for the largest jumps. That direction was not registered, so it is a pattern to test, not a finding.

**Which skills travel (descriptive).** Salador [43] and Berger and Daumann [44] asked which skills translate to the NBA; Appendix D asks it of European arrivals, descriptively. The comparisons that survive both ways of averaging ratios say one thing: *the same player keeps more of his turnovers than his points when he faces continental opponents* (retention: turnovers 1.043, points 0.926; Figure A7). These ratios describe the selected players; they do not establish causal skill transfer. These are 14 of 39 registered comparisons; the other 25 depend on the estimator.

![Figure A7. What the same player keeps, skill by skill. For players observed in a domestic league and a continental competition in the same season, the continental rate of each box-score line as a share of the domestic rate, using the registered, exposure-weighted average of player ratios (filled) and the ratio of sums, an unregistered sensitivity check (open). Lines: 95% bootstrap intervals. Table A3 gives both estimators. Descriptive: the ratios describe selected players and do not establish causal skill transfer (Appendix D gives the counts).](figures/fig_skills.png)

**A checklist for evaluating a new feature.** For evaluation, score any extra feature against a strong simple benchmark on identical players; report cross-league ranking changes and their correctness, minutes weighting, fallback frequency, and season-specific calibration. This follows the decision-focused principle of measuring the decisions a model supports [52].

### L. Reference forecasts and supporting data

Table A23. Reference forecasts and support. *Forecast*: the forecast continental EFF/36 for an arrival with domestic and career EFF/36 of 16. *Factor pairs*: same-season players behind the translation factors, which the league-aware forecast does not use.

| Source league | Forecast, EuroLeague | Forecast, EuroCup | Factor pairs |
|---|---|---|---|
| Spain (ACB) | 14.5 | 16.3 | 813 |
| France (Pro A) | 14.4 | 16.3 | 378 |
| Italy (LBA) | 14.0 | 15.8 | 439 |
| Greece (A1) | 13.7 | 15.5 | 266 |
| Turkey (BSL) | 13.2 | 15.1 | 494 |
| Israel (Winner League) | 13.1 | 14.9 | 190 |
| Adriatic (ABA) | 12.8 | 14.6 | 472 |
| Germany (BBL) | 12.5 | 14.3 | 441 |
| VTB United League | 12.4 | 14.3 | 314 |
| Lithuania (LKL) | 12.4 | 14.2 | 267 |

The equivalents in Table 1 are descriptive transforms of the fitted model, not separately registered estimands.

Printed differences are computed from unrounded values, so they can differ in the last digit from the difference of two printed numbers. Intervals are 95%, clustered by player and destination club-season [15]; bootstrap intervals resample club-seasons [16].

**Forecast specification.** A translation factor for a source league and a destination is the average ratio of destination to source EFF/36 among players observed in both competitions in the same season, partially pooled within destination; the translation feature z multiplies the source rate x by it (the formulas follow). Each season uses only earlier seasons for fitting. The benchmark ladder adds destination and source-league information to source rate x, earlier career rate h and the deterministic flag a = 1[x > h]: see Equation (@eq:model) of the main text.

**How the translation factor is built.** For source league ℓ and destination c, the raw factor averages destination-to-source rate ratios among players observed in both competitions in the same season:

$$f_{\ell c}=\frac{\sum_i w_i\,y_i/x_i}{\sum_i w_i}$$ {#eq:factor}

Here x and y are source and destination EFF/36; w is the smaller minute total. Factors are partially pooled within destination [53]. Pairs with fewer than 75 players fall back to the destination mean. The feature uses the pooled or fallback factor m and an arrival-based lag correction k:

$$z = x\cdot m_{\ell c}\cdot k$$ {#eq:feature}

The translation term is unpenalised; this changes the bias–variance tradeoff and gives no guaranteed advantage in out-of-sample MAE. The league numbers need past arrivals (1,059 here), without the additional 4,074 same-season pairs used to estimate translation factors. A forecast computed from the coefficients of the fitted equation as printed in the main text is within 0.02 EFF/36 of the model's own forecast for rates up to 35.

**The fitted equation of the main text, in full.** Here x is last season's domestic EFF/36, in the league where the player had the most minutes. h is the career rate before it: the EFF/36 of all his games on record in earlier seasons taken together (total EFF over total minutes), domestic and continental, with no minimum number of games. a = 1 when x is above h, D = 1 for a EuroLeague destination and δ is the league number of Table 1. For a player with no earlier season, set h = x. The step a is common: 63% of signings followed an above-average season, against 53% of all comparable domestic player-seasons. Both shares are counted among players with an earlier season on record: 561 of the 895 training arrivals who have one, and 53% of the 13,825 domestic player-seasons that have one. Appendix K explains why it is a step in the fitted forecast and not a penalty for timing. The equation is for EuroLeague and EuroCup arrivals from these ten leagues, and the limits above travel with it: the forecasts run low, the league numbers did not carry back to the older arrivals of two leagues, and they describe the players clubs sign from a league, not league strength. The Equivalents compare leagues along one profile. This comparison changes domestic rate and history together; for a player whose career history differs from his domestic rate the conversion differs. The model is additive, so a league's gap to Spain, its equivalent minus 16, applies at every level along this reference profile.

**A worked example with two invented candidates.** Candidate A plays in Germany: 20 EFF/36 last season against a career rate of 17. Candidate B plays in Spain: 16 against a career rate of 16. Both are weighed for a EuroCup club. History alone forecasts A at 15.9 and B at 14.8, and so ranks A first by 1.1. Equation (@eq:fitted) forecasts A at 15.7 and B at 16.3, and so ranks B first by 0.7. Table A14 says how far to trust a gap of that size: when two candidates' forecasts differed by 0 to 1 EFF/36, the higher-forecast player turned out better in 54.5% of pairs. The league numbers change the order here; the gap is below the 1 EFF/36 from which forecast gaps were right at least 60% of the time, so it is a weak reason to prefer candidate B. Each forecast also carries the error band described above. The example is an illustration with invented players; it recommends no signing.

**What the frozen test could detect.** The gain over history varies about 3 times more from player to player than translation's increment, which is why its detectable effect is the larger one. Before scoring, the registration expected that at 100–150 newcomers the test could detect an increment of about 0.075–0.092 EFF/36, and a gain over history of 0.244–0.298, which is larger than the 0.161 in Table A20, so that a null there would have meant "not detectable", not a contradiction. 94 newcomers were scored; the detectable effects recomputed at that number are printed below. These figures are optimistic, because the outcomes cover only part of a season. A contrast fails to replicate if its interval excludes its 2020–2025 estimate and its own estimate has the opposite sign; for the gain over history its interval must also exclude zero [25]. The rule was not applied, because the test is inconclusive. How a postponed game, an unclean join and three outcomes without earlier wording are read was fixed on 18 November 2026, before scoring [54].

**Who was scored.** By 24 November 2026, 200 players had reached eight continental games without a qualifying 2025–26 continental season. 94 have a frozen forecast under their name and 106 do not; those are listed by name, club and previous club in the scoring files, and no name was joined by hand. 7 of them may be players in the frozen file under another spelling (MITROU - LONG, ELIJAH of ARI, close to ELIJAH MITROU-LONG in the frozen file; NOTAE, JD of MAN, close to J D NOTAE in the frozen file; KING, JORDAN of LEM, close to JORDAN JAMES KING in the frozen file; PIPES JR, SHAWN of BOS, close to P J PIPES in the frozen file; SMITH, STEFAN of NIN, close to STEF SMITH in the frozen file; CROCKETT JR, TJ of RTK, close to T J CROCKETT in the frozen file; BALCEROWSKI, OLEK of BAR, close to ALEKSANDER BALCEROWSKI in the frozen file): 7.4% of the joined newcomers, against a limit of 5% registered in advance [25]. That count is a lower bound. 0 joined newcomers were left out because last season's domestic rate was not positive, 0 because the 2026–27 rate was not positive, and 0 because a forecast was missing. 94 newcomers were scored.

**Printed before any contrast was read.** At 94 newcomers the detectable effects were 0.308 EFF/36 for translation's gain over history, 0.151 for the league-aware forecast against history plus translation, 0.095 for translation's increment, 0.289 for the league-aware forecast against history alone and 0.196 for the league-aware forecast against the destination-only forecast; all are optimistic for part-season outcomes. The newcomers had played a median of 8 games. At their game counts the expected noise in one newcomer's EFF/36 is 3.692 (standard deviation), against 2.736 for a full season of the 2020–2025 arrivals.

**The contrasts on the newcomers that could be scored (no sentence is licensed).** Unweighted, weighted by destination minutes, and for the 62 newcomers whose source league has a complete 2025–26 season (the registered sensitivity): Translation's gain over history, +0.098 EFF/36 (95% interval [−0.086, 0.281]); weighted by playing time, +0.106 EFF/36 (95% interval [−0.087, 0.300]); complete-source leagues only, +0.083 EFF/36 (95% interval [−0.109, 0.274]). The league-aware forecast against history plus translation, −0.040 EFF/36 (95% interval [−0.125, 0.044]); weighted by playing time, −0.042 EFF/36 (95% interval [−0.130, 0.045]); complete-source leagues only, −0.027 EFF/36 (95% interval [−0.155, 0.102]). Translation's increment over the league-aware forecast, +0.010 EFF/36 (95% interval [−0.015, 0.035]); weighted by playing time, +0.012 EFF/36 (95% interval [−0.014, 0.038]); complete-source leagues only, +0.016 EFF/36 (95% interval [−0.008, 0.040]). The league-aware forecast against history alone, +0.057 EFF/36 (95% interval [−0.134, 0.249]); weighted by playing time, +0.064 EFF/36 (95% interval [−0.139, 0.267]); complete-source leagues only, +0.056 EFF/36 (95% interval [−0.161, 0.273]). The league-aware forecast against the forecast that knows only the destination, +0.060 EFF/36 (95% interval [−0.109, 0.228]); weighted by playing time, +0.068 EFF/36 (95% interval [−0.107, 0.243]); complete-source leagues only, +0.119 EFF/36 (95% interval [−0.100, 0.337]). The read-out of the forecast built on a league table printed in 2015, registered on 17 November 2026 with a second frozen file [33], exists unweighted only, on the 94 scored newcomers: the forecast built on the 2015 table against the forecast that knows only the destination, +0.056 EFF/36 (95% interval [−0.037, 0.149]); the league-aware forecast against the forecast built on the 2015 table, +0.003 EFF/36 (95% interval [−0.107, 0.114]). In every contrast of this paragraph a value above zero favours the forecast named first (for translation's gain and translation's increment, the forecast with translation).

**Forecast level and ordering, for the record only.** Mean of forecast minus outcome: league-aware −1.202 EFF/36 (95% interval [−1.938, −0.428]); history −1.224 EFF/36 (95% interval [−1.957, −0.508]); history plus translation −1.030 EFF/36 (95% interval [−1.756, −0.283]). Share of cross-league pairs ordered correctly: league-aware forecast 68.4% (95% interval 61.9% to 75.3%; 2,574 pairs); history alone 68.9%; difference −0.5 points (95% interval −2.8 to +2.1). On pairs from the same source league the league-aware forecast ordered 68.8% correctly and history alone 69.0% (429 pairs).

**Registered for the February re-score, descriptive here.** The 80% and 95% error bands (half-widths 4.66 and 7.25 EFF/36, fixed before scoring from the errors on all arrivals of 2020–2025; they are single bands and differ from the averages over yearly bands given for the examined seasons) contained 76.6% and 90.4% of the scored newcomers. Share of pairs in which the higher league-aware forecast had the higher outcome, by forecast gap: 0 to 1 EFF/36, 49.1% of 534 pairs; 1 to 2 EFF/36, 57.2% of 446 pairs; 2 to 3 EFF/36, 66.5% of 462 pairs; 3 to 4 EFF/36, 73.3% of 415 pairs; 4 to 6 EFF/36, 74.6% of 622 pairs; 6 or more EFF/36, 88.5% of 524 pairs. No statement is licensed by these values in November [25].

### M. The test on league changes and the 2015 table

**The design in numbers.** The test covers 3,423 league changes by 1,649 players. The stayer forecast, fitted on 9,057 pairs of seasons of players who stayed in their league, is 4.012 + 0.653 x + 0.109 h − 0.836 a, with x, h and a as in the fitted equation of the main text, and a residual spread of 3.44 EFF/36. Its inputs come from 155 box-score files; every interval comes from 2,000 bootstrap draws that resample players and refit the stayer forecast. In 10,000 random assignments of the ten league values, the middle 95% of slopes ran from −0.582 to 0.589. The fitted line's intercept, the mean unexplained change when the table predicts none, is +0.309 EFF/36. A slope of 0.11 would have been detected with 80% power (descriptive). The mean unexplained change is +1.346 (interval 1.158 to 1.533) for moves to a league with a higher Equivalent and −0.755 (interval −0.940 to −0.566) for moves to a lower one.

**Order of events.** Amendment 14, which registers the test, was pushed alone on 17 November 2026, 17:08 UTC, before any code for it existed; Amendment 17, which fixes how its rules are read, on 17 November 2026, 20:28 UTC. The frozen predictions were pushed on 17 November 2026, 21:51 UTC, and the sha256 of the frozen file was added to the public hash list on 17 November 2026, 22:03 UTC. The outcomes were joined once, in one retained scoring run on 18 November 2026, which read the frozen file by its sha256. The same season can be the outcome of one league change and the starting point of the next, so the files could not be sealed from each other; what was fixed in advance is every rule, the code and the frozen predictions.

**The checks in full.** Table A24 lists every registered slope, with the interval of each direction and the eight registered sensitivities. The label of S-e (3) is the registered one: it counts four leagues and says January 2026. The 2025–26 files of five leagues stop between 26 December 2025 and 8 January 2026 (Limitations); the fifth is the ABA League. S-e (3) leaves out every league change of 2025–26, so its slope does not depend on that count. When the ten table values are redrawn as well, each from its committed interval, redrawing adds noise to the predicted change, so the centre of that interval sits low by construction; it is read for its width only [30]. With one intercept per arrival season in place of the single intercept, the slope is 0.78 (interval 0.68 to 0.88) with the stayer forecast fitted only on seasons before each move and 0.79 (interval 0.68 to 0.88) with it fitted on all seasons (a check added after the result, exploratory [31]; Table A24 prints both beside the slopes with the single intercept).

Table A24. The test on league changes: every registered slope. The slope of the unexplained change on the change the table predicts, with 95% bootstrap intervals (players resampled, the stayer forecast refitted in every draw). S-b: one league left out; S-c: one direction; S-d: the table's own uncertainty; S-e: the eight sensitivities. E33: one check added after the result was seen, and the same two slopes with one intercept per arrival season [31].

| Result | What | League changes | Slope | 95% interval |
|---|---|---|---|---|
| Primary | all league changes | 3,423 | 0.770 | 0.692 to 0.844 |
| S-b | without Adriatic (ABA) | 2,869 | 0.791 | 0.706 to 0.870 |
| S-b | without France (Pro A) | 2,606 | 0.881 | 0.787 to 0.973 |
| S-b | without Germany (BBL) | 2,646 | 0.759 | 0.667 to 0.851 |
| S-b | without Greece (A1) | 2,873 | 0.785 | 0.706 to 0.862 |
| S-b | without Israel (Winner League) | 2,906 | 0.744 | 0.665 to 0.821 |
| S-b | without Italy (LBA) | 2,614 | 0.793 | 0.702 to 0.876 |
| S-b | without Lithuania (LKL) | 3,021 | 0.724 | 0.643 to 0.807 |
| S-b | without Spain (ACB) | 2,484 | 0.571 | 0.477 to 0.665 |
| S-b | without Turkey (BSL) | 2,519 | 0.801 | 0.718 to 0.880 |
| S-b | without VTB United League | 2,846 | 0.804 | 0.714 to 0.889 |
| S-c | moves to a league with a higher Equivalent | 1,609 | 0.826 | 0.619 to 1.039 |
| S-c | moves to a league with a lower Equivalent | 1,814 | 0.626 | 0.440 to 0.813 |
| S-d | the ten table values redrawn as well (approximation; width only) | 3,423 | 0.770 | 0.434 to 0.930 |
| S-e (1) | without league changes where either season has a second domestic league with 8 or more games | 2,976 | 0.776 | 0.696 to 0.850 |
| S-e (2) | arrival seasons 2020 to 2025 only | 2,083 | 0.771 | 0.675 to 0.863 |
| S-e (3) | arrival seasons 2016 to 2024 only (four leagues' 2025–26 files stop in January 2026) | 3,093 | 0.786 | 0.704 to 0.864 |
| S-e (4) | the stayer forecast with one intercept per league of origin | 3,423 | 0.771 | 0.687 to 0.854 |
| S-e (5) | the EuroLeague equivalents in place of the EuroCup ones | 3,423 | 0.675 | 0.607 to 0.741 |
| S-e (6) | at least 15 games in both seasons | 2,265 | 0.759 | 0.679 to 0.841 |
| S-e (7) | arrival seasons 2020 to 2025, the table refitted only on arrivals before that season | 2,083 | 0.786 | 0.684 to 0.885 |
| S-e (8) | league pairs with fewer than 30 moves in the two directions together left out | 3,375 | 0.768 | 0.690 to 0.842 |
| E33 | S-e (7) with the stayer forecast also fitted only on seasons before each move (added after the result; exploratory) | 2,083 | 0.781 | 0.679 to 0.881 |
| E33 | E33 with one intercept per arrival season in place of the single intercept | 2,083 | 0.780 | 0.679 to 0.879 |
| E33 | S-e (7) with one intercept per arrival season in place of the single intercept | 2,083 | 0.786 | 0.684 to 0.882 |

Table A25. Two league scales on the same league changes (E31b). Mean absolute error (EFF/36) on the 2,763 league changes of arrival seasons from 2018, with 95% bootstrap intervals. *Coefficient*: the one coefficient of the scale, fitted through the origin on league changes of earlier seasons; the value shown is the one used for the last scored season.

| Forecast | MAE | 95% interval | Coefficient | 95% interval |
|---|---|---|---|---|
| Stayer forecast alone | 2.770 | 2.681 to 2.857 | n/a | n/a |
| Stayer forecast + the Equivalents | 2.625 | 2.542 to 2.707 | +0.774 | 0.692 to 0.853 |
| Stayer forecast + the 2015 table | 2.642 | 2.562 to 2.725 | −2.210 | −2.469 to −1.942 |

The two coefficients have opposite signs because the scales run in opposite directions: the 2015 table gives Spain its highest score among the ten leagues, and the Equivalents give it their lowest value.

**The 2015 table against a forecast that knows only the destination (exploratory).** The 2015 table was built for a different purpose: the level of competition a prospect faced, for the NBA draft. On the 674 arrivals of 2020–2025, a league table printed in 2015 improves a destination-aware forecast by 0.039 EFF/36 (interval 0.002 to 0.077); the weighted value is 0.036 (interval −0.010 to 0.082), not clearly above zero when weighted by playing time. The unweighted analysis decides these sentences, as in every other comparison of the paper; for this one that rule was settled after the result was seen [30]. Table A26 gives every value.

Table A26. A league table printed in 2015 on the 674 arrivals of 2020–2025 (E31a, exploratory). Paired differences in mean absolute error (EFF/36); a positive difference favours the second forecast of the row. Intervals are 95%, clustered by player and destination club-season. *Detectable*: the difference that would have been detected with 80% power.

| Comparison | Weighting | MAE, first | MAE, second | Difference | 95% interval | Detectable |
|---|---|---|---|---|---|---|
| Destination-only forecast minus the 2015-table forecast | unweighted | 2.989 | 2.950 | +0.039 | 0.002 to 0.077 | 0.054 |
| Destination-only forecast minus the 2015-table forecast | weighted by playing time | 2.829 | 2.793 | +0.036 | −0.010 to 0.082 | 0.066 |
| 2015-table forecast minus the league-aware forecast | unweighted | 2.950 | 2.924 | +0.026 | −0.008 to 0.060 | 0.048 |
| 2015-table forecast minus the league-aware forecast | weighted by playing time | 2.793 | 2.756 | +0.037 | −0.003 to 0.077 | 0.057 |

### N. Notes on registration

**Order and wording of the first page.** The order in which the abstract, the introduction and the conclusion state these results was fixed on 17 November 2026, after a review of the paper and before that text was written [55, 56]. It was changed on 18 November 2026: the first page says less, and several passages moved to the appendix, without any registered sentence leaving the paper [32]. The title was fixed on 17 November 2026 for each possible result of the league-changes test, before that test was run [56]; the registration of 3 November 2026 and the public hash list carry earlier titles of this paper. The first page's wording and the reading of the slope per league-number gap were settled after the league-changes result [32]. Five named pairs of newcomers in the main text once the frozen test is scored, and further wording, were allowed on 18 November 2026, before scoring [40]. The pairs and the tables of named newcomers are not printed, because the test is inconclusive. The conclusion's wording of translation's increment, and the interval with the table values redrawn on the first page, were settled later the same day [57]. Further text was allowed on 22 November 2026, after the results on the examined seasons were known and before the scoring of the frozen test: the unit in words, the destination term beside the fitted equation, the forecast level by competition, a narrower statement on prior work and two published league scales on the older arrivals [39]. After the frozen test was scored and found inconclusive, the sentences that name it were rewritten on 25 November 2026 to state that outcome, and two descriptive sentences were added from values the paper already printed; the registration of that day prints each sentence before and after [34].

**A study taken from a review of the paper.** E34 is the only study this paper reports from the further studies that a review of the paper ran, outside the registration, on seasons already examined; the others are not used. One sentence in the main text that points from the comparison with the 2015 table to this reading was added on 25 November 2026, after the reading had been made [58].

**Repairs of wording and drawing.** On 26 November 2026, after three readers had read the final paper, thirteen sentences were repaired, four sentences that define the paper's terms were added and the figures were redrawn in one style; no number and no registered sentence changed [59].

**A second round of repairs, and the first page.** On 26 November 2026, after five readers had read the final paper again and three blind readers had compared two first pages, the first page was reworded, further sentences were repaired or added, and the two values of a registered read-out of the frozen test were printed in Appendix L; no result changed, and each changed sentence is listed with its old and new words [60]. A fresh reader then checked these changes against the rest of the paper, and eighteen places were corrected the same day [61]. On 27 November 2026 twenty-seven passages were reworded for register, the appendix tables were numbered in the order in which they stand and values were printed on three figures; no result and no registered reading changed, and each reworded passage is listed with its old and new words [62]. Amendments 28, 29, 30 and 32 together list every change made to the text of the paper since the version of 25 November 2026.

**A display recorded before scoring.** In the literature search of 15 November 2026 a web-search result page showed three current-season statistic lines of EuroLeague players, none of which was written to a repository file or used in an analysis [25, 39]; the registrations written from 17 November 2026 to 19 November 2026 that state that no 2026–27 statistic had been read do not mention this display. Further displays, none of them used, are recorded in the registrations of 16 November 2026 and 17 November 2026 [25, 33]. A review of the paper cites, as read on 21 November 2026, a public page that shows current-season statistics; what it saw is not recorded [39]. On 22 November 2026, before scoring, a further registration fixed that the two pages which show current-season statistics are read in full once the score record of the frozen test is committed, whatever its status [63].

### O. Related work in detail

One number per league is an old idea: baseball's major-league equivalents and hockey's league equivalencies put leagues on one scale [1, 4, 5]. The estimator here is a ridge regression. Projection across leagues in basketball also predates this study. Salador regressed NBA outcomes on international statistics and league indicators [43]; Berger and Daumann shrank college shooting percentages before projection [44]. Analysts have published league scales that cover European basketball: a scale of competitions around the world, built from shared players for the NBA draft [8]; a ranking of European leagues from how far clubs' ratings fall between domestic and European play [45]; and a code repository that fits league effects for Spanish and European competitions from players seen in more than one of them [46]. Glazer estimates G League-to-NBA translation factors by matching similar players and a difference-in-differences estimator [10]. A further public scale gives one strength value per league and is fitted on players who moved, between leagues from one season to the next and between a national league and a European cup in the same season (2021–22 to 2025–26); it measures points, rebounds and assists per 36 minutes, adjusted for pace, and reports its own consistency checks [38]. That scale is fitted on league changes, among other moves; the Equivalents are fitted only on first continental seasons and were then tested on domestic league changes, under rules registered beforehand. That scale is not scored on the arrivals of 2020–2025 or on the league changes, because it is built on those seasons; it is not a registered arm and is not read out on the frozen test [33]. One exploratory reading on the older arrivals is in Results and Appendix I [39]. A Sloan poster builds player archetypes that can be applied in any league, including leagues without advanced data; it describes styles, not levels [64]. German Basketball Analytics forecasts next-season estimated plus-minus for players of 30 European leagues, with the levels of the current and the next league among its inputs [47]. The forecast was fitted on seasons through 2022 and scored on 2023 and 2024, on all players with two consecutive seasons together (an error of about ±1 and R² 0.70). The scored players are not arrivals as such: the page names four players who moved to another league or level as examples and reports no result for players who moved between leagues as a group. It reports no accuracy without the league levels and no baseline. Gaussian Hoops projects, for each EuroLeague player of 2026–27, a direction and a range for measures of shooting, rebounding and assists, from earlier players who made the same kind of move at the same level of league [48]. Its calls of direction were scored on EuroLeague players of earlier seasons: it reports 75% of the calls of its 2025–26 board as right (755 of 1,013) and, for true shooting percentage, 76% across 84 players who had arrived in the EuroLeague; the board states that it was tuned on 2023–24 to 2025–26. Part of the scored players are arrivals: the board keeps its record for newcomers apart from those for returning and staying players, and each record counts calls of direction, not an error in the units of a measure. To a visitor it shows no forecast without the league level and no baseline. Its page data, which the page does not print, hold for each group of players and each measure an error of the projection beside an error of a reference that the page code calls guessing; the page does not define that reference, and nothing on it compares the projection with and without the league level. A bounded search in English found no public test in basketball that compares a forecast with and without a league adjustment on what players arriving in European competitions went on to do. Soccer transfer models use player, team and league features [65]; there, ridge and boosting models with a league indicator can match hierarchical translation [66], and regression models with league identifiers beat naive and pair-average baselines on average, though not on every statistic [67]. Same-target comparison against strong simple alternatives is established practice [13, 14, 68]. This paper offers a named league table for European basketball arrivals, the same-player benchmark of translation factors against it, and its test on league changes; its test on frozen forecasts is inconclusive.

Glazer presents the G League-to-NBA factors as estimates of how a player's existing statistics would have looked in the other league, not as forecasts, and scores none of them on later players [10].

How the search was done. The search behind the sentence "found no public test in basketball" was run on 15 November 2026 and 17 November 2026, in English only. It queried three indexes of scholarly work (OpenAlex, Crossref and arXiv), followed the citations around the closest papers for one step, and used web searches for analysts' pages. It worked from abstracts and public pages and is not a systematic review. On 18 November 2026 the sentence in its earlier, wider form was checked again against the Gaussian Hoops page, which reports its own consistency checks [38]: those are checks of the scale against itself, not a test on what arriving players went on to do. A review of the paper then named further pages of two analysts; the first was read in full on 22 November 2026 [47]; of the second, the overview and the board in its view for true shooting percentage were read on 25 November 2026, and the page source of the board, with the accuracy record of every view and the folded panel on how to read the board, on 26 November 2026; its player rows were not read one by one, so the reading that was registered as "in full" (Appendix N) is complete for the page's text and code and not for each player's row [48]. The sentence is a statement about this search, not proof that no such test exists.
