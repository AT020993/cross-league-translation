---
title: "{{meta:title}}"
track: "{{meta:track}}"
paper_id: "47"
---

## Abstract

European clubs recruit from domestic leagues whose box scores are not directly comparable. Production is measured by box-score efficiency per 36 minutes (EFF/36). The European League Equivalents, one number per source league, need only past arrivals: when career history equals the domestic rate, {{hook_short}}. {{e30_abstract}}On {{abs_arrivals}}, examined before registration and so exploratory, a translation factor adds nothing detectable on top of the league numbers: {{inc_674}}. {{e28_abs_gain}} for the 2020–2025 arrivals; {{e28_abs_older}}. Forecasts frozen on 3 November 2026, after the season began but before outcome inspection, {{p1_summary}}{{p1_s2_abstract}}.

## Why the question matters

A club comparing players from different domestic leagues must ask what a box score means in continental basketball. The established answer is a translation factor, an adjustment estimated from players observed in both competitions [@james1985; @davenport1996; @davenport1998; @desjardins2004; @bacon2021; @pelton2013; @pelton2014; @vashro2015; @leepage2021; @glazer2026]. Its apparent value depends on the benchmark it is tested against.

A forecast that knows the destination but not the source league underrates arrivals from {{under_names}} and overrates arrivals from {{over_names}} (Figure 2); **one number per source league** flattens that pattern. These are the **European League Equivalents** (Figure 1, {{eq_table}}): when career history equals the domestic rate, {{hook_short}}. {{e30_intro}}On top of the league numbers, a translation factor adds nothing detectable: {{inc_both}} (Figure 3).

![Figure 1. The European League Equivalents and their test. Left: domestic EFF/36 equivalent to 16 in Spain when career and domestic rates coincide (filled: EuroLeague; open: EuroCup; lines: 95% intervals; n: training arrivals, {{e9_seasons}}); leagues inside a tier are not distinguishable, which does not prove that they are equal.{{e30_fig1}}](figures/fig1_equivalents.png)

**What these results do not show.** The table is for comparing players, not for forecast levels: the forecasts run low, by {{lvl_off_abs}} EFF/36 on average for the league-aware forecast ({{lvl_w_abs}} weighted by playing time). A translation factor does help a forecast that ignores both leagues, by {{hist_gain}} EFF/36. Weighted by playing time, translation's gain over history is not clearly above zero ({{mw_hist}}, 95% interval {{mw_hist_lo}} to {{mw_hist_hi}}). On the arrivals of 2020–2025, {{e28_gd_sentence}}; {{e28_abs_older}}, and {{p1_s2_intro}}. {{p1_examined}}.

## Data and methods

### Players and outcome

The target is a player arriving in EuroLeague or EuroCup with at least eight domestic games the preceding season, eight continental games in the arrival season, and no regular continental role the preceding season. The {{n_anchor}} arrivals in destination seasons 2020–2025 comprise {{n_el}} EuroLeague and {{n_ec}} EuroCup players. Domestic statistics come from Proballers, continental ones from the EuroLeague API. The eight-game rule excludes {{n_short}} of {{n_all}} arrivals ({{short_share}}).

The outcome, EFF per 36 minutes, is points, rebounds, assists, steals and blocks minus missed shots and turnovers. It is the EuroLeague's Performance Index Rating without fouls drawn, fouls committed and shots rejected. One EFF/36 is one more point, rebound, assist, steal or block, or one fewer missed shot or turnover, per 36 minutes; a made two-point basket adds two. Points per 36, Game Score per 36 [@gamescore] and EFF per 100 on-court possessions [@kubatko2007] are checks. Mean absolute error (MAE) is primary.

### Forecasts and estimation

Each season uses only earlier seasons for fitting. Start with last season's domestic rate x, earlier career rate h and the flag a = 1[x > h]. Add destination, then one number for each source league. The translation feature z scales x by a league-pair rate ratio estimated from players observed in both competitions (Appendix L gives the formulas).

$$\hat y = \beta_0+\beta_1 x+\beta_2 h+\beta_3 a + D(\gamma_0+\gamma_1 x)+\sum_{\ell}\delta_\ell\,\mathbf 1[\text{source}=\ell]\;\;(+\,\theta z)$$ {#eq:model}

D marks destination; δ is the source-league offset, the league number of the title. Ridge penalties λ = 1, 10 and 100 were fixed in advance, with λ = 10 primary.

### Comparisons and uncertainty

Every comparison uses the same players. Translation's gain is the paired reduction in absolute error [@diebold1995; @gneiting2011]:

$$\bar d=\frac{1}{n}\sum_{i=1}^{n}\Big(|e_i^{\text{without}}|-|e_i^{\text{with}}|\Big)$$ {#eq:gain}

Positive values favour translation. Intervals are 95%; arrival comparisons use player and club-season clustering [@cameron2011] or a club-season bootstrap [@cameron2008].

The analyses beyond the submitted abstract were registered before execution [@prereg; @amend1; @amend2; @amend3; @amend4; @amend5; @amend6; @amend7; @amend8; @amend9; @amend11], except the few items marked as unregistered or descriptive where they appear. The 2020–2025 outcomes had already been examined, so registration does not make those results confirmatory [@cawley2010]. {{methods_unread}} {{methods_settled}}

## Results

{{e30_section}}{{e31_section}}### The European League Equivalents flatten the league pattern

League by league, a forecast that knows the destination but not the source league underrates arrivals from {{under_names}} and overrates arrivals from {{over_names}}, measured against the average arrival (Figure 2). {{e24_primary}} The spread of league biases falls from {{spread_d}} to {{spread_o}} EFF/36; sampling noise inflates both levels, so we read the difference, whose interval lies above zero (the interval is in Appendix K). The league table does not remove all bias.

![Figure 2. Where a forecast blind to the source league goes wrong, and how far one number per league flattens it. Each league's mean signed error (forecast minus actual EFF/36) minus that of all arrivals, with 95% cluster-bootstrap intervals; leagues in the order of {{eq_table}}. Grey: a forecast that knows the destination but not the source league. Blue: the league-aware forecast. Asterisk: grey bias detectable after Holm adjustment across the ten leagues{{fig2_notes}}](figures/fig4_bias.png)

**What the league numbers are worth.** On the same {{n_anchor}} arrivals of 2020–2025, {{e28_gh_sentence}}, and {{e28_gd_sentence}}. {{e28_weighted_sentence}} Both are exploratory: added after a review of the paper, on seasons already examined, and only the intervals are new, since the point estimates could be read off Table A24 [@amend9] (by competition and season: Table A19). They did not carry back to older arrivals (below).{{gain_size}}

**Why the average gain is small.** The largest detectable league bias is {{bias_top}} EFF/36 ({{bias_top_name}}), but a single forecast misses by {{mae_off10}} on average, so moving it by a league's bias changes its error little. Against the history-only forecast, {{e21_sentence}} (interval {{lt_right_lo}} to {{lt_right_hi}}).

**The forecasts run low.** On average the league-aware forecast is {{lvl_off_abs}} EFF/36 below what arrivals delivered (interval {{lvl_off_lo}} to {{lvl_off_hi}}), most in the latest season. {{lvl_w_sentence}}; this interval is two-way clustered, where the first is a cluster bootstrap [@amend12]. The other forecasts share the shortfall (Appendix K; Table A10), so same-player comparisons stand, but forecast levels need care in decisions. {{lvl_by_competition}} We claim no cause.

### {{translation_heading}}

Translation reduces history-only MAE from {{mae_hist}} to {{mae_hist_z}} EFF/36 (a gain of {{hist_gain}}, {{hist_gain_pct}}; interval {{hist_gain_lo}} to {{hist_gain_hi}}). Adding destination leaves a translation gain of {{d_dest}} ({{dest_lo}} to {{dest_hi}}); adding the league numbers leaves {{d_inc10}} ({{inc10_lo}} to {{inc10_hi}}; a difference of {{inc10_mde}} would have been detected with 80% power; Figure 3; Table A24 has every row).

![Figure 3. Why translation looks useful, and what it adds once a forecast knows the leagues. Left: forecast error (MAE, EFF/36) on the same {{n_anchor}} arrivals without (grey) and with (blue) the translation feature; the label gives both values. Right: the gain from translation with its 95% interval, clustered by player and destination club-season.](figures/fig_mechanism.png)

Translation's increment on top of the league numbers is close to a built-in comparison: the translation term is the domestic rate times a factor for each source league and destination, all of which the league-aware forecast already holds, so a small increment is partly expected. It shows that the factor adds nothing detectable once a forecast has the league numbers, not which kind of league information is the better one.

The comparison that is not built in sets the league-aware forecast without translation against history with translation: the advantage for the league-aware forecast is {{ch}} EFF/36 (interval {{ch_lo}} to {{ch_hi}}; a difference of {{ch_mde}} would have been detected with 80% power). The interval spans zero; the data do not establish superiority.

Both the head-to-head interval and translation's incremental interval lie inside ±{{margin_eff}} EFF/36, 2% of forecast error [@lakens2017]. That margin was registered for translation's increment, after the submitted recipe's interval had been seen, so it is descriptive for the submitted recipe and for the head-to-head. Put against the gain from knowing the source league, {{e28c_sentence}} (descriptive), so "inside the margin" is a coarse statement on that scale (Appendix J).

**Other outcomes, seasons and richer models.** The same pattern appears on three other outcomes and in most seasons (described, not tested; Appendix J, with the six factor recipes, the pair slopes and the share of translation's gain that league context recovers). {{flex_clause}} (Appendix E: Table A5); that model was fixed and untuned, so this does not bound what a tuned model could do.

**Playing time changes the emphasis.** Weighted by destination minutes, translation's gain over history falls to {{mw_hist}} (interval {{mw_hist_lo}} to {{mw_hist_hi}}), which spans zero, while the league-aware forecast keeps a small point-estimate advantage ({{mw_ch}}) and the increment stays small ({{mw_inc}}) (Table A18); the unweighted analysis is primary and does not demonstrate equal benefit for starters and fringe players.

### Modest ranking gains, no demonstrated shortlist gain

Across source leagues the league-aware forecast orders {{x_d1_off}} of pairs correctly, a {{x_gain}} percentage-point gain over history (95% interval {{x_gain_lo}} to {{x_gain_hi}}). Pairs share players and are not independent observations. For the predicted top 10 per competition and season, none of the registered differences is detectable (Appendix H). The ranking improvement is modest, and neither shortlist quality nor financial value has been demonstrated. Appendix H restates this as the share of comparisons that the league table changes, and reports the within-league and translation checks.

### The same frozen models on arrivals of 2008–2015

{{older_section}}

{{e28_older_block}} Appendix Table A16 gives all four results and what each could detect.

{{e34_main}}{{e29_main}}

{{two_tests}}### The outcome-blinded 2026–27 test

{{p1_section}}

## What a club can use

**European League Equivalents.** {{eq_table}} gives, for each source league, the domestic EFF/36 that forecasts like a 16 in Spain's ACB when career history equals the domestic rate (Figure 1). The league numbers describe players selected for continental recruitment, not pure league strength. {{e19_sentence}} The refits share most of their data, so this describes stability, not independent validation (Appendix H: Figure A3, Table A11).{{gaps_grew}}

{{table:equivalents}}

{{club_rule}}**The league numbers as an equation.** The equivalents are read off one fitted equation, the league-aware forecast of Equation (@eq:model) with its coefficients estimated on every season through 2025 [@amend12]:

{{eq_fitted}}

Here x is last season's domestic EFF/36 and h the career rate before it (all earlier games on record; h = x for a player with no earlier season); a = 1 when x is above h, D = 1 for a EuroLeague destination and δ is the league number of {{eq_table}}. {{eq_step}} The equation is for EuroLeague and EuroCup arrivals from these ten leagues, and the limits above travel with it: the forecasts run low, the league numbers did not carry back to the older arrivals of two leagues, and they describe the players clubs sign from a league, not league strength. Appendix L: full definitions and rounding bound.

{{club_example_short}} Appendix L shows how to compare recruits with different histories.

**How far to trust a forecast gap.** {{trust60}} {{trust70}} {{trust_counts}} The gap also includes player history and destination, so this is not the isolated benefit of the league adjustment (Appendix H: Table A25, Figure A4). It describes selected arrivals retrospectively and requires validation before use on a new candidate pool.

**Individual uncertainty.** Walk-forward conformal intervals [@lei2018; @barber2023] for the league-aware forecast cover {{e8_cov80}} of {{e8_n}} arrivals at the nominal 80% level (about ±{{e8_hw80}} EFF/36); seasonal coverage ranges from {{e8_cov80_min}} to {{e8_cov80_max}} and is lowest in {{lvl_last_season}}. These wide intervals argue for scouting alongside statistical comparisons (Appendix H; cases in Appendix G).

**Who gets to play?** The {{n_short}} of {{n_all}} arrivals with fewer than eight games had a median continental EFF/36 of {{short_cont_rate}}, compared with {{anchor_cont_rate}} among qualifiers (Tables A6–A7). A club using the rate forecast still needs a view on playing time.

## Related work

{{section:related}}

## Limitations

**Exploratory seasons.** The 2020–2025 outcomes had been examined before these analyses, so those results are exploratory despite pre-registration. **Sample.** It is EuroCup-heavy ({{n_ec}} of {{n_anchor}} arrivals), requires eight continental games, and holds players clubs chose to sign, so the league numbers describe those choices as much as league strength; the Equivalents hold along the profile where career history equals the domestic rate. {{e30_limits}}

**Forecast level.** On average the league-aware forecast is {{lvl_off_abs}} EFF/36 below what arrivals delivered, most in the latest season; weighted by playing time, the league-aware forecast is {{lvl_w_abs}} EFF/36 below what arrivals delivered; we do not know the cause, and the frozen 2026–27 forecasts may share it. **Weighting.** Weighted by minutes, translation's gain over history is not clearly above zero, on the main sample and on a wider one (Table A18). {{e28_limits}}

**Linkage.** Players are joined across sources by name. After the second registered sample of {{audit25_n}} estimation pairs, at most {{audit25_x}} of unverified estimation pairs are identity mismatches (Appendix A). {{arr_count_sentence}} {{arr_s1_sentence}} (Table A18). Career histories and training arrivals were not audited. Name joins can also miss genuine arrivals, which a mismatch audit does not measure.

**Frozen test.** {{p1_limits}}Partial-season outcomes; for four source leagues (and ABA) domestic data stop in January 2026, and {{acb_rows}} Spanish ACB rows lack official stat corrections. {{older_limits}}

**Arrival forecast errors.** Paired comparisons condition on the fitted arrival forecasts. **Intervals** leave out refitting uncertainty. {{mover_interval_scope}}

## Conclusion

On arrivals of 2020–2025 a forecast that ignores the source league misjudges whole leagues, and one number per league flattens that pattern. The European League Equivalents print those numbers as a table: when career history equals the domestic rate, {{hook_short}}. {{e30_conclusion}}On top of the league numbers a translation factor adds nothing detectable: {{inc_both}}. The league numbers need only past arrivals ({{n_train}} here), not the {{n_factor_pairs}} same-season pairs that translation factors need. On arrivals of 2020–2025, {{e28_gd_sentence}}; {{e28_conclusion}}{{p1_s2_conclusion}}. {{p1_examined}}; the ranking gain is modest and no top-10 gain was demonstrated. Forecasts frozen on 3 November 2026, after the season began but before outcome inspection, {{p1_summary}}.

## Data and code

{{release_section}} Domestic statistics are credited to Proballers and continental statistics to the EuroLeague API; {{older_credit}}. Rights in the underlying data remain with those sources.

## References

{{section:references}}

## Appendix

{{section:appendix}}

{{section:vignettes}}

{{section:amend34}}

**How rankings were compared.** Within each competition and season, we compare every pair of arrivals [@kendall1938]. Across source leagues, the league-aware forecast orders {{x_d1_off}} of pairs correctly versus {{x_d1_hist}} for history alone: a {{x_gain}} percentage-point gain (interval {{x_gain_lo}} to {{x_gain_hi}}) over {{x_pairs}} pairs, which share players and are not independent observations (Figure A2); within one source league the gain is {{s_gain}} ({{s_gain_lo}} to {{s_gain_hi}}). Translation added to the league-aware forecast changes {{d2_flip_pct}} of all rankings and is right on {{d2_right_pct}} of those changes (interval {{d2_right_lo}} to {{d2_right_hi}}), not distinguishable from a coin flip. For the predicted top 10 per competition and season, none of the registered differences is detectable. The ranking improvement is modest, and neither shortlist quality nor financial value has been demonstrated.

**Stability and close calls.** {{e19_move}} {{tiers_close}} are close calls between tiers (bootstrap shares within 0.05 of the 0.90 cut-off). **The ordering result restated.** Counted as changed comparisons, {{e21_sentence}} (interval {{lt_right_lo}} to {{lt_right_hi}}); this restates the ordering result of the main text and is not new evidence. The predicted top 10 per competition and season achieved {{rq_hist}} EFF/36 under history, {{rq_hz}} with translation, {{rq_off}} with the league numbers and {{rq_offz}} with both; none of the registered differences is detectable.

![Figure A2. Top: change in ordering accuracy versus history alone, for pairs from different or the same source league. Bottom: accuracy among rankings changed by adding translation to the league-aware forecast (50% = coin flip). Lines: 95% cluster-bootstrap intervals.](figures/fig3_decisions.png)

![Figure A3. The Equivalents in each yearly refit. Each line is one source league: the domestic EFF/36 that forecasts like a 16 in Spain's ACB when the table is refitted on the arrivals before each destination season, for EuroLeague arrivals (left) and EuroCup arrivals (right). Colour: the league's tier in the full fit. Dashed line: Spain's ACB, the reference. The refits share most of their data, so the figure describes stability and is not independent validation.](figures/fig_stability.png)

**The gap guide and the error bands.** Table A25 holds the guide to forecast gaps of the main text, and Figure A4 draws it beside the same guide for history alone. For scale on the ordering result, a forecaster who knew every player's true rate would order {{x_ceiling}} of cross-league pairs (interval {{x_ceiling_lo}} to {{x_ceiling_hi}}; normal-noise model), so most of the remaining gap stays open. At the 95% level the conformal intervals cover {{e8_cov95}} of arrivals (about ±{{e8_hw95}} EFF/36); Figure A5 shows the 80% coverage by source league and by season.

{{table:gaps}}

![Figure A4. How far to trust a forecast gap. Share of pairs of arrivals, in the same competition and season, in which the player with the higher forecast had the higher realised EFF/36, by the size of the gap between the two forecasts. Blue: the league-aware forecast (the values of Table A25). Grey: history alone. Lines: 95% cluster-bootstrap intervals. Pairs share players and are not independent observations.](figures/fig_gap_guide.png)

![Figure A5. Coverage of the 80% error bands. Share of arrivals whose outcome fell inside the walk-forward 80% band of the league-aware forecast, by source league (left; lines: 95% Wilson intervals) and by destination season (right). Dashed line: the nominal 80%.](figures/fig_bands.png)

{{section:older}}

These models were fitted using later seasons, so this is a backward transfer test with outcomes withheld during forecast generation, not a historical simulation of what a club could have known then. The small set of source leagues and wide intervals limit external validation.

{{table:e28_older}}

{{table:e34}}{{table:e29}}

{{e29_change_note}}

### J. Conditional noise reference and model comparisons

Absolute MAE is the primary scale throughout the paper. Odd/even games imply full-season reliability {{rel_eff}} for EFF/36 [@spearman1910]. Under a stationary player-rate and normal-noise approximation, the estimated full-season noise reference is {{floor_eff}} EFF/36; a direct odd/even calculation gives {{floor_direct}}. Subtracting each reference from the history-only MAE gives a conditional denominator for the share of error removed. Translation's gain is {{av_hz}} on the normal reference (Figure A6) and {{av_hz_direct}} on the direct reference. These estimates depend on the noise model, playing-time exposure and within-season stability. They are not a universal irreducible error bound or evidence that other features cannot help.

**How much of the reducible error is removed.** One season of EFF/36 is a noisy measurement, so no forecast can reach zero error. Against a normal-noise reference of {{floor_eff}} EFF/36, the league-aware forecast removes {{av_off}} of the error that history alone leaves above the reference, and history plus translation removes {{av_hz}} (Figure A6). These shares depend on the noise model and are not a bound on what other features could add.

![Figure A6. Estimated reducible-error share under the normal-noise reference ({{floor_eff}} EFF/36), relative to history only. Grey: without translation; blue: with translation. Lines: cluster-bootstrap intervals where available. The denominator is conditional on the noise assumptions; the plot compares only the fitted configurations.](figures/fig2_avoidable.png)

**The ladder in full, and the margin.** Table A24 gives every row of the ladder. Pair-specific slopes perform worse here (MAE {{mae_cell10}} versus {{mae_off10}}), consistent with, but not proof of, overfitting. League context recovers {{S_pct}} of translation's gain (interval {{S_lo_pct}} to {{S_hi_pct}}). Values above 100% arise because the league-aware point estimate is slightly better, not because the gain is known precisely. The ±{{margin_eff}} EFF/36 margin is pre-specified for the five other recipes and the other outcomes; it is {{margin_share}} of the original translation gain. Across six factor recipes, the largest upper bound on translation's increment is {{max_upper_eff}} EFF/36 (Figure A1). {{e3_sentence}} {{e5_sentence}}

{{table:ladder_full}}

{{table:checks}}

{{table:e28_674}}

Figure A1 reports nominal intervals for all six recipes; every recipe improves on history alone ({{recipe_hist_min}}–{{recipe_hist_max}} EFF/36). The smallest Holm-adjusted p-value for an increment is {{holm_min}} [@holm1979].

On Game Score/36 a forecast that knows only the destination still gains from translation ({{gmsc_dest}} Game Score/36, interval {{gmsc_dest_lo}} to {{gmsc_dest_hi}}): source-league adjustment matters. The EuroLeague gain over history is {{el_hist_gain}} (interval {{el_hist_lo}} to {{el_hist_hi}}); the competitions do not differ detectably in that gain (p = {{dest_diff_hist_p}}) or in what translation adds to the league-aware forecast (p = {{dest_diff_p}}). Table A18 gives the three comparisons for each competition; both head-to-head intervals include zero. On {{n_wide}} arrivals with at least three games and 60 minutes the pattern holds unweighted, but the minutes-weighted gain over history spans zero ({{w_mw_hist}}, interval {{w_mw_hist_lo}} to {{w_mw_hist_hi}}), so the registered claim for this check does not hold. On all {{n_all}} arrivals, {{t_sentence}}, mostly from knowing the destination (Table A7).

A ridge model using the full domestic box-score profile, minutes, usage, age, leagues and source-club win share misses by {{mae_ridge30}}; the fixed, untuned boosted-tree configuration misses by {{mae_gbm}}, against {{mae_off10}} for the league-aware forecast. These specific configurations did not improve MAE. They do not establish a performance ceiling for richer or tuned models. Translation's upper interval bound in boosted trees is {{gbm_z_upper}} of error, above the 2% margin; in ridge it is {{ridge_z_upper}} (Table A5).

### K. Bias, indicator specification, descriptive skills and an evaluation checklist

**The forecasts run low.** On average the league-aware forecast is {{lvl_off_abs}} EFF/36 below what arrivals delivered (interval {{lvl_off_lo}} to {{lvl_off_hi}}): {{lvl_off_ec}} for EuroCup arrivals and {{lvl_off_el}} for EuroLeague arrivals. The shortfall is largest in the latest season, {{lvl_last_season}} ({{lvl_last}}), when the 80% error bands also covered least ({{cov_last}}) and EuroCup arrivals produced {{drift_ec_arr}} EFF/36 more than arrivals of earlier seasons (all EuroCup players: {{drift_ec_all}} more); we describe this and claim no cause. The other forecasts share the shortfall (Appendix Table A10), so the comparisons between them stand.

**League biases.** Figure 2 shows each league's error against the average arrival for a forecast that knows the destination but not the source league. That is the fair comparison, because a forecast blind to both leagues also misjudges the two competitions. **Measured against the average arrival, that forecast underrates arrivals from {{under_by}} EFF/36 and overrates arrivals from {{over_by}}.** {{e24_primary}} The spread of league biases falls from {{spread_d}} to {{spread_o}} EFF/36 (difference {{spread_gain}}, interval {{spread_gain_lo}} to {{spread_gain_hi}}); knowing the destination alone does not flatten it (difference {{spread_dest}}, interval {{spread_dest_lo}} to {{spread_dest_hi}}). The first estimate sits at the top of its interval because resampling adds noise to a root mean square and so inflates the smaller spread most: the league-aware spread itself sits at the bottom of its own interval, {{spread_o_lo}} to {{spread_o_hi}}. Three caveats. France points the same way ({{fra_d}}) but does not survive the adjustment for testing ten leagues. With the forecast blind to both leagues, only {{h_only_name}} does (Appendix Table A9 shows every version, including the first-registered errors). And {{left_name}} stays underrated by the league table itself ({{left_val}}, interval {{left_lo}} to {{left_hi}}).

**Above-history indicator.** The sentence registered for this result reads: **{{e12_sentence}}** That wording needs a clarification. The flag a = 1[x > h] is determined by domestic rate and history, so it cannot vary while both remain fixed. The coefficient ({{beta_a}} EFF/36) is a step in the fitted forecast at x = h, not an identified timing penalty. The interval is {{beta_a_lo}} to {{beta_a_hi}}, and the estimate is negative in all {{beta_refits}} season-by-season refits. The indicator is common: {{e23b_sentence}} The coefficient is model-dependent. {{e23_sentence}} The estimate points the other way ({{jump_coef}} EFF/36 per point of jump, interval {{jump_lo}} to {{jump_hi}}; Appendix Table A13): the fitted indicator association weakens for the largest jumps. That direction was not registered, so it is a pattern to test, not a finding.

**Which skills travel (descriptive).** Salador [@salador2011] and Berger and Daumann [@berger2021] asked which skills translate to the NBA; Appendix D asks it of European arrivals, descriptively. The comparisons that survive both ways of averaging ratios say one thing: *the same player keeps more of his turnovers than his points when he faces continental opponents* (retention: turnovers {{ret_tov}}, points {{ret_pts}}; Figure A7). These ratios describe the selected players; they do not establish causal skill transfer. These are {{n_robust}} of {{n_lic}} registered comparisons; the other {{n_sensitive}} depend on the estimator.

![Figure A7. What the same player keeps, skill by skill. For players observed in a domestic league and a continental competition in the same season, the continental rate of each box-score line as a share of the domestic rate, using the registered, exposure-weighted average of player ratios (filled) and the ratio of sums, an unregistered sensitivity check (open). Lines: 95% bootstrap intervals. Table A3 gives both estimators. Descriptive: the ratios describe selected players and do not establish causal skill transfer (Appendix D gives the counts).](figures/fig_skills.png)

**A checklist for evaluating a new feature.** For evaluation, score any extra feature against a strong simple benchmark on identical players; report cross-league ranking changes and their correctness, minutes weighting, fallback frequency, and season-specific calibration. This follows the decision-focused principle of measuring the decisions a model supports [@elmachtoub2022].

### L. Reference forecasts and supporting data

{{table:equivalents_support}}

The equivalents in {{eq_table}} are descriptive transforms of the fitted model, not separately registered estimands.

Printed differences are computed from unrounded values, so they can differ in the last digit from the difference of two printed numbers. Intervals are 95%, clustered by player and destination club-season [@cameron2011]; bootstrap intervals resample club-seasons [@cameron2008].

**Forecast specification.** A translation factor for a source league and a destination is the average ratio of destination to source EFF/36 among players observed in both competitions in the same season, partially pooled within destination; the translation feature z multiplies the source rate x by it (the formulas follow). Each season uses only earlier seasons for fitting. The benchmark ladder adds destination and source-league information to source rate x, earlier career rate h and the deterministic flag a = 1[x > h]: see Equation (@eq:model) of the main text.

**How the translation factor is built.** For source league ℓ and destination c, the raw factor averages destination-to-source rate ratios among players observed in both competitions in the same season:

$$f_{\ell c}=\frac{\sum_i w_i\,y_i/x_i}{\sum_i w_i}$$ {#eq:factor}

Here x and y are source and destination EFF/36; w is the smaller minute total. Factors are partially pooled within destination [@efron1975]. Pairs with fewer than 75 players fall back to the destination mean. The feature uses the pooled or fallback factor m and an arrival-based lag correction k:

$$z = x\cdot m_{\ell c}\cdot k$$ {#eq:feature}

The translation term is unpenalised; this changes the bias–variance tradeoff and gives no guaranteed advantage in out-of-sample MAE. The league numbers need past arrivals ({{n_train}} here), without the additional {{n_factor_pairs}} same-season pairs used to estimate translation factors. With the coefficients of the fitted equation as printed in the main text, the result is within {{eq_bound}} EFF/36 of the model for rates up to {{eq_max_rate}}.

**The fitted equation of the main text, in full.** Here x is last season's domestic EFF/36, in the league where the player had the most minutes. h is the career rate before it: the EFF/36 of all his games on record in earlier seasons taken together (total EFF over total minutes), domestic and continental, with no minimum number of games. a = 1 when x is above h, D = 1 for a EuroLeague destination and δ is the league number of {{eq_table}}. For a player with no earlier season, set h = x. The step a is common: {{e23b_sentence}} Appendix K explains why it is a step in the fitted forecast and not a penalty for timing. The equation is for EuroLeague and EuroCup arrivals from these ten leagues, and the limits above travel with it: the forecasts run low, the league numbers did not carry back to the older arrivals of two leagues, and they describe the players clubs sign from a league, not league strength. The Equivalents compare leagues along one profile. This comparison changes domestic rate and history together; with history held fixed the conversion differs. The model is additive, so a league's gap to Spain, its equivalent minus 16, applies at every level along this reference profile.

{{club_example}}

{{p1_power_note}}{{e30_appendix}}

### N. Notes on registration

**Order and wording of the first page.** The order in which the abstract, the introduction and the conclusion state these results was fixed on 17 November 2026, after a review of the paper and before that text was written [@amend13; @amend16]. It was changed on 18 November 2026: the first page says less, and several passages moved to the appendix, without any registered sentence leaving the paper [@amend19]. {{amend19_note}}{{amend20_note}}{{amend21_note}}{{amend23_note}}{{amend25_note}}{{amend26_note}}{{e34_note}}

**A display recorded before scoring.** In the literature search of 15 November 2026 a web-search result page showed three current-season statistic lines of EuroLeague players, none of which was written to a repository file or used in an analysis [@amend8; @amend23]; the registrations written from 17 November 2026 to 19 November 2026 that state that no 2026–27 statistic had been read do not mention this display. Further displays, none of them used, are recorded in the registrations of 16 November 2026 and 17 November 2026 [@amend8; @amend15]. A review of the paper cites, as read on 21 November 2026, a public page that shows current-season statistics; what it saw is not recorded [@amend23].{{amend24_note}}

### O. Related work in detail

{{related_full}}

{{related_glazer}}

{{related_search}}
