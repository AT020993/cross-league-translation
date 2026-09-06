# Prior-art sweep for the SSAC27 abstract — what changes the first sentence

**Date:** 2026-09-05 · **Status:** literature record, no computation · **Owed by:**
`docs/plans/sloan-ssac27-abstract-draft.md` ("a Google Scholar pass … is owed before the manuscript").
Every entry below has a URL that was opened on 2026-09-05; entries whose primary source could not be
fetched say so. Nothing is cited from memory.

## Specification

| Choice | This sweep | Alternatives considered |
|---|---|---|
| **Unit** | one prior work (paper, preprint, methodology page) | — |
| **Population** | six web searches run 2026-09-05 (hockey NHLe / Desjardins; basketball cross-league same-season; Euro-to-NBA projection; football league translation; dynamic ability / Kalman rating models; "league equivalencies" basketball) plus every primary page the results named, fetched where the host allowed it | Google Scholar (not available to the tooling used; owed as a second pass before the manuscript) |
| **Estimator** | none — a reading; each row records identification, RTM treatment, validation, public forecast, URL | — |
| **Null / bound** | the claim under test is the abstract's opening sentence ("every prior translation is a transfer study"); one counter-example falsifies it | — |
| **Sample filter** | entries with a URL opened today; a source that could not be fetched (403/404) is marked as read via search snippets | — |
| **Aggregation key** | (work, identification design) | — |
| **Uncertainty** | not applicable; the only quantitative content is other authors' reported figures, quoted with their source | — |

## The finding that matters

**The abstract v2's first sentence — "Every prior translation is a transfer study. This one is
not." — is false as written.** Hockey's *Network NHLe* (CJ Turtoro) estimates league equivalencies
from players who played in **two leagues in the same season**, and chains leagues without a direct
NHL link through connecting leagues (the same graph-connectivity idea as Proposition 4 ii).
Secondary sources describing it, opened today:

* HockeyStats.com methodology page — "using transitions between players who played in two leagues
  in the same year, avoiding multi-year development effects"; conversion factor = ratio of summed
  points per game; indirect paths multiplied; credited to CJ Turtoro.
  https://hockeystats.com/methodology/nhle
* Patrick Bacon, *NHL Equivalency and Prospect Projection Models, Part 2* (Towards Data Science /
  Medium; the TDS mirror returned 404 and the Medium page 403 on fetch, the search snippet was read):
  the classic model compares the same players' scoring in a league and in the NHL "typically in the
  same year or the year immediately after"; three limitations named, among them that development
  between year one and year two is "baked in".
  https://medium.com/data-science/nhl-equivalency-and-prospect-projection-models-building-the-nhl-equivalency-model-part-2-6f275a45e22
* **Turtoro's original post was located on 2026-09-06** (second sweep, below): CJ Turtoro,
  *Network NHLe (NNHLe)*, 2020-05-01, https://cj-turtoro.shinyapps.io/NNHLe-writeup/. In the
  author's words the pairing is form-triggered: "the players switching leagues mid-season are more
  likely to be either too good or too bad for their first league than their inter-season
  counterparts", and "these metrics should not be interpreted as indicators of 'league strength'".
  No regression to the mean anywhere; validation is MAE of 2000–09 predicting 2010–20 (NNHLe 0.054
  vs classic 0.057, "negligibly more accurate", but 130+ leagues). The primary source supports the
  scheduled-co-observation distinction in the author's own terms.

The classic method is Gabriel Desjardins' *League Equivalencies* (hockeyanalytics.com, undated,
early-2000s data): explicitly **consecutive-season** — "It is rare that a player plays significant
time in two leagues in the same year, but players often play in one league in one year and another
the next" — ratio of PPG in year two to year one, 40+ games each side, age-stratified; notes a
power-play-time confound and that younger players' development inflates the factor.
http://hockeyanalytics.com/Research_files/League_Equivalencies.pdf

## What survives, stated precisely

Hockey's same-season pairs are **call-ups and demotions**: a player appears in the AHL and the NHL
in one year *because* a team moved him, and the move is triggered by his performance — exactly the
conditioning on the source-season noise that Proposition 4(iii) names as the failure the design
cannot remove. In the European dual-tier structure the same **club** fields the same player in a
domestic league and a continental competition **by the schedule**, not by a performance-triggered
move. The novelty is therefore not "same season" but **scheduled co-observation**: the pairing
event is independent of the player's form. That sentence is defensible; the current one is not.

Two further things no entry below has: the **measured split between the league effect and
regression to the mean** on the same corpus, and a **pre-registered public forecast with refusals
and dated checkpoints**.

## Other entries for the prior-art table (all opened 2026-09-05)

| work | identification | RTM separated? | validation | public forecast | URL |
|---|---|---|---|---|---|
| Desjardins, *League Equivalencies* (hockey, classic NHLe) | consecutive-season movers, 40+ GP each side | no (notes age development inflates factors) | in-sample; a five-player Sharks anecdote | no | hockeyanalytics.com PDF above |
| Turtoro, *Network NHLe* (hockey) | **same-season** two-league players (call-ups); network paths for unlinked leagues | no | not stated in the sources read | no | hockeystats.com page above |
| Bacon, prospect projection model (hockey, 2020s) | classic NHLe re-estimated; adds age curves | not stated | not stated in the snippet | no | Medium link above |
| Shaikh, *Hierarchical Bayesian Modeling of Cross-League Performance Translation in Elite Football* (SportRxiv, posted 2026-07-01) | **transfers**: 174 attacking/midfield + 106 defensive moves across the Big Five | not discussed | two held-out transfer cohorts (n=45, n=35), 90% HDIs with near-nominal coverage | no | https://sportrxiv.org/index.php/server/preprint/view/953 |
| Shaikh, *A Machine Learning Framework for Cross-League Per-90 Statistic Translation in Elite Football* (SportRxiv, posted 2026-07-09) | matched player bridges (transfers) 2017/18–2023/24, log-ratio of per-90 rates | not discussed | held-out test set, conformal 90% intervals, coverage 0.932 | no | https://sportrxiv.org/index.php/server/preprint/view/959 |
| McIntosh & Beckmann, *Modelling player performance after potential transfers between leagues* (Hudl Performance Insights 2025) | **no transfer data at all**: physical/athletic metrics by league and position | n/a | not read (pp. 1–4 only) | no | https://static.hudl.com/craft/performance-insights-research-stage/2025/Modelling-player-performance-after-potential-transfers-between-leagues-Richard-McIntosh-Tobias-Beckmann.docx.pdf |
| *Translating Talent: A Cross-League Plus-Minus Approach in Soccer* (2025; ResearchGate page 403 on fetch, read via search snippets) | league adjustment coefficients inside a RAPM/EPM regression (Gemini Plus-Minus) | no | correlation with market value | no | https://www.researchgate.net/publication/395665209_Translating_Talent_A_Cross-League_Plus-Minus_Approach_in_Soccer |
| Cattelan, Varin & Firth, *Dynamic Bradley–Terry modelling of sports tournaments* (JRSS-C 2013); Glickman 1999; Knorr-Held 2000 | not translation: **random-walk ability with an (extended) Kalman filter** — the model class of `translation-dynamic-ability-*` | n/a | — | — | https://rss.onlinelibrary.wiley.com/doi/full/10.1111/j.1467-9876.2012.01046.x |

The basketball hits (EuroLeague national-vs-foreign comparisons, PLOS ONE 2019 NBA-vs-EuroLeague
trends, the 2025 IJPAS domestic-vs-Eurobasket scoring comparison whose page returned 403) are
descriptive comparisons, not translation estimates, and are already covered by the draft's table.

## Second sweep, 2026-09-06 — the football and Australian-football analogues the first sweep did not query

Six further searches (football domestic-vs-Champions-League co-observation; rugby; cricket franchise
leagues; NHL equivalency in the academic literature; league-effect vs regression-to-the-mean
separation; recent SSAC finalists). Every URL opened on 2026-09-06.

| work | identification | RTM separated? | validation | public forecast | URL |
|---|---|---|---|---|---|
| **Hvattum, *Offensive and Defensive Plus–Minus Player Ratings for Soccer*, Applied Sciences 10(20):7345, 2020** | >52,000 matches 2008–2017 including **5,142 UEFA Champions League / Europa League fixtures** beside twelve domestic leagues in the same seasons; per-league quality components β^COMP averaged over the competitions a player has appeared in. **Scheduled same-season co-observation is present and identifying by construction, as an unremarked by-product**: league quality is a nuisance parameter, identification runs at segment/goal level, selection and RTM are not discussed; the paper concedes the league components "seem to counter the effects of the home field advantage" and are much smaller than it | no | in-sample; no held-out transfer test | no | https://pdfs.semanticscholar.org/7bba/436d26cc68b8250692132851c8c0e848fc75.pdf |
| Sæbø & Hvattum, *Evaluating the efficiency of the association football transfer market using regression based player ratings*, NIK 2015 | 14 competitions incl. UCL/UEL pooled, 20,217 matches 2009–2014; no league-strength parameter described — league quality absorbed into player ratings partly through European fixtures | no | transfer-fee modelling | no | https://www.ntnu.no/ojs/index.php/nikt/article/download/5265/4741/20471 |
| Kharrat, López Peña & McHale, *Plus-Minus Player Ratings for Soccer*, arXiv:1706.04943 (2017) | eleven **domestic** leagues only; one coefficient per league identified from "players traveling between leagues" (transfers); a 6-game adaptation rule | no (ridge shrinkage only) | in-sample | no | https://arxiv.org/abs/1706.04943 |
| **Matteo, Carey, Ruddy & Varley, *Modelling the effect of competition tier on player involvement and impact in Australian Football*, IJPAS 26(3):557, 2025** | AFL and its Tier-2 reserve leagues 2015–2023, 4,806 players; Bayesian mixed models with a **career-long player random effect** and a league fixed effect. The same player is observed in both tiers within a season — but "AFL clubs can freely move their AFL listed players into T2 game day teams", i.e. the move is a **selection decision**, the failure mode Proposition 4(iii) names. Nearest academic analogue | no | not a forecast | no | https://www.tandfonline.com/doi/full/10.1080/24748668.2025.2524663 |
| Yi et al., *Technical performance of Big-Five players in the UEFA Champions League*, Frontiers in Psychology 2019 | UCL performance only, grouped by the player's domestic league; the same player's domestic box score is **not** paired (the authors name that as the limitation) | n/a | descriptive | no | https://www.frontiersin.org/journals/psychology/articles/10.3389/fpsyg.2019.02738/full |
| CricViz / Wilde, *Evaluating Different Standards of T20 Cricket* (2020) | ~4,500 players across franchise T20 leagues whose windows are contract-scheduled within one year — a partial analogue of scheduled co-observation; no disclosed model, no intervals | no | none | no | https://cricviz.com/evaluating-different-standards-of-t20-cricket/ |
| Vashro, *Measuring Level of Competition Around the World* (Nylon Calculus 2015); Rissotto, *Ranking the Top Basketball Leagues in the World* (No Ceilings 2026) | basketball, transfer-based bridging over movers (NBA-centric regression; FIC/40 differentials, SRS-style solve); both concede selection on movers | no | none | no | https://fansided.com/2015/11/06/deep-dives-measuring-level-of-competition-around-the-world/ · https://www.noceilingsnba.com/p/ranking-the-top-basketball-leagues |
| Fangraphs Library, *League Equivalencies*; Johnson, *Major League Equivalencies* (Seamheads 2008); Fangraphs, *The Projection Rundown* (Marcel/ZiPS/Oliver) | baseball MLEs from mid-season transactions; projection systems apply park/league adjustment and regression to the mean **sequentially**, never jointly estimated; Fangraphs names the "players repeating levels" inflation as an unresolved issue | named, not estimated | in-sample | annual, not pre-registered | https://library.fangraphs.com/principles/league-equivalencies/ · https://seamheads.com/2008/01/19/major-league-equivalencies/ |

**What the second sweep changes.** "Nobody has used scheduled same-season co-observation" would be
false: Hvattum's plus-minus league coefficients are identified in part by domestic and Champions
League fixtures in the same seasons. What survives, stated precisely: **this is the first use of
scheduled co-observation as the identification design, at player level, with transfers held out
for validation, and the first estimate in any sport of the split between the league effect and
regression to the mean on one corpus.** No work found in any sport estimates that split; the
baseball systems apply the two steps in sequence and the football preprints use domestic transfers
as a baseline. Rugby returned nothing on translation. No peer-reviewed NHL-equivalency paper was
found. SSAC finalists 2024–2026 (opened: 2025 winner Uribe et al., penalty-kick location; 2026
finalist list) show causal/counterfactual framing and a decision-support application sentence;
none of the descriptions opened mentions pre-registration or refusals.

Not opened (recorded so nobody cites them as read): Bacon Parts 1 and 3 (403), Desjardins' Behind
the Net post, the Baseball-Fever MLE thread (Cloudflare), Hvattum's 2019 review full text, Gómez et
al. 2025 full text (abstract only), the SSAC 2026 winner (not on the official page).

## What this changes in the abstract

1. v2's opening sentence is replaced. Proposed: *"Cross-league translation has always been
   estimated from players who moved — between seasons (baseball's equivalencies, football's transfer
   models) or within one (hockey's call-ups). A move is triggered by form. We use a structure in which
   the same club fields the same player at two levels by schedule, so the pairing is independent of
   his form."* (word count to be re-checked; v2 sits at 497.)
2. The prior-art table gains the hockey rows and the two 2026 football preprints.
3. The claim "nobody in that line has (1) an identification that is not a transfer" becomes
   "an identification in which the pairing is not triggered by performance".

## What this does not change

No number, no gate, no lock. The dynamic-ability arm's model class has textbook precedent
(Glickman, Knorr-Held, Cattelan et al.), which the result note should cite as such rather than
present the random walk as new.
