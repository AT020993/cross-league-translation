#!/usr/bin/env python3
"""Render the SSAC27 full paper (Submission 47) from committed research results.

Every number in the manuscript is computed here from committed summaries of the
pre-registered full-paper analyses (the 3 Nov pre-registration and Amendments 1
and 2) and the pinned v9/v10 records; no number is typed into the template.
The renderer refuses to write if any placeholder or citation key is unresolved,
if a sentence title or claim in the text is false for the committed numbers,
and `--final` additionally refuses while the 2026-27 frozen test is unscored.

Outputs (under --out): manuscript.md, the figures (figures/*.png),
render-manifest.json and, with --docx, the Word file.

Amendment 16 (17 November 2026): the title, the abstract, the second paragraph of
the introduction and the conclusion follow the case of E30, the test of the league
table on players who changed domestic league (Amendment 14). The E30 summary is
optional: while it is absent the case is "not run", the second title is used and
the paper says nothing about league changes. Gate G16a is ``check_first_page``.
"""

# ruff: noqa: E501 -- manuscript prose and reference strings
from __future__ import annotations

if __name__ == "__main__":
    import sys as _sys
    from pathlib import Path as _Path

    _sys.path.insert(0, str(_Path(__file__).resolve().parents[1]))
    from src.research.execution import enter as _enter

    _enter(__file__)

import argparse
import csv
import datetime
import hashlib
import json
import math
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import sloan_fullpaper_paper_figures as paper_figures  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.config.seasons import season_label as display_season  # noqa: E402

TEMPLATE = Path("docs/paper/ssac27/manuscript.template.md")
#: Amendment 16, rule 2: the two registered titles. The submitted title was
#: "What Does League Translation Add? A Benchmark for European Basketball Forecasts".
TITLE_TESTED = "European League Equivalents: One Number per League, Tested on League Changes It Was Never Fitted To"
TITLE_ADDS = (
    "European League Equivalents: What One Number per League Adds to European Basketball Forecasts, "
    "and What Translation Factors Add on Top"
)
#: The title while E30 is not run; ``compose`` selects the title by the E30 case.
TITLE = TITLE_ADDS
ART = "docs/research/artifacts/"
SOURCES = {
    "recipes": Path(ART + "sloan-fullpaper-recipes-2026-11/summary.json"),
    "robust": Path(ART + "sloan-fullpaper-robustness-2026-11-03/summary.json"),
    "decide": Path(ART + "sloan-fullpaper-decisions-2026-11-03/summary.json"),
    "freeze": Path(ART + "sloan-fullpaper-p1-freeze-2026-11/freeze.json"),
    "v9": Path(ART + "sloan-v9-2026-09-19/diagnostics.json"),
    "v10": Path(ART + "sloan-v10-2026-09-20/summary.json"),
    "prep": Path(ART + "sloan-v9-2026-09-19/preparation.json"),
    "support": Path(ART + "sloan-support-loss-2026-09-28/readback.json"),
    "amend": Path(ART + "sloan-fullpaper-amend1-decisions-2026-11/summary.json"),
    "skills": Path(ART + "sloan-fullpaper-skills-2026-11/summary.json"),
    "flex": Path(ART + "sloan-fullpaper-flexible-2026-11/summary.json"),
    "audit": Path(ART + "sloan-fullpaper-linkage-audit-2026-11/e13_summary.json"),
    "surv": Path(ART + "sloan-fullpaper-survivorship-2026-11/summary.json"),
    "vign_summary": Path(
        ART + "sloan-fullpaper-paper-v2-2026-11/vignettes_summary.json"
    ),
    "release": Path("docs/paper/ssac27/release.json"),
    "amend3": Path(ART + "sloan-fullpaper-amend3-2026-11/summary.json"),
    "amend4": Path(ART + "sloan-fullpaper-amend4-2026-11/summary.json"),
    "audit25": Path(ART + "sloan-fullpaper-linkage-audit-e25-2026-11/e25_summary.json"),
    "audit26": Path(ART + "sloan-fullpaper-arrivals-audit-2026-11/e26_summary.json"),
    "older": Path(ART + "sloan-fullpaper-older-seasons-paper-2026-11/e27_paper.json"),
    "amend9": Path(ART + "sloan-fullpaper-amend9-2026-11/summary.json"),
    "amend11": Path(ART + "sloan-fullpaper-amend11-2026-11/summary.json"),
    # Amendment 23, rule 4 (gate G23d): the analysts' pages on prior work, each with the date
    # of its full read and what it reports. It decides which sentences on prior work are printed.
    "prior_work": Path("docs/paper/ssac27/prior-work-record.json"),
}
TABLES = {
    "tiers": Path(
        ART + "sloan-fullpaper-decisions-2026-11-03/e9_league_tiers_full.csv"
    ),
    "conformal": Path(ART + "sloan-fullpaper-decisions-2026-11-03/e8_conformal.csv"),
    "exchange": Path(
        ART + "sloan-fullpaper-amend1-decisions-2026-11/exchange_rate_acb16.csv"
    ),
    "e11": Path(
        ART + "sloan-fullpaper-amend1-decisions-2026-11/e11_signed_error_by_league.csv"
    ),
    "counts": Path(
        ART + "sloan-fullpaper-amend1-decisions-2026-11/e17_league_counts.csv"
    ),
    "pairs": Path(ART + "sloan-fullpaper-amend1-decisions-2026-11/e10_pair_types.csv"),
    "retention": Path(ART + "sloan-fullpaper-skills-2026-11/e15a_retention.csv"),
    "licences": Path(ART + "sloan-fullpaper-skills-2026-11/e15a_licences.csv"),
    "carryover": Path(ART + "sloan-fullpaper-skills-2026-11/e15b_carryover.csv"),
    "vignettes": Path(ART + "sloan-fullpaper-paper-v2-2026-11/vignettes.csv"),
    "refits": Path(ART + "sloan-fullpaper-amend3-2026-11/e19_equivalents_by_refit.csv"),
}
TEXTS = {
    "prereg": Path("docs/research/sloan-full-paper-preregistration-2026-11-03.md"),
    # Amendment 7 registers the measured weakness of the name link that the paper states
    # beside the E27 result; the renderer checks its computed value against these words.
    "amend7_text": Path(
        "docs/research/sloan-full-paper-preregistration-amendment-7-2026-11-12.md"
    ),
}
#: The P1 scoring output; absent until the 2026-27 games through 24 Nov are scored.
P1_SCORE_CANDIDATES = (
    Path(ART + "sloan-fullpaper-p1-score-2026-11/score.json"),
    Path(ART + "sloan-fullpaper-p1-score-2026-11/summary.json"),
)
#: E32 (Amendment 15; Amendment 18, rule 9): the named-newcomer tables, written after scoring by
#: scripts/sloan_fullpaper_named_newcomers.py. Absent until then.
E32_CANDIDATES = (
    Path(ART + "sloan-fullpaper-p1-score-2026-11/e32_newcomers.csv"),
    Path(ART + "sloan-fullpaper-named-newcomers-2026-11/e32_newcomers.csv"),
)
#: Amendment 20 (accepted by Amir on 18 November 2026; commit 0e8cd21, pushed alone): five named
#: pairs in the main text once the frozen test is scored, the registered reading in the club
#: section, and four further wordings. ``{"amendment_20": False}`` in the loaded inputs renders the
#: paper as Amendments 1 to 19 alone would; tests use it. No loaded file sets it.
AMENDMENT_20 = True
#: The E32 table of changed pairs and its summary stand beside the table of named newcomers.
E32_PAIRS_NAME = "e32_changed_pairs.csv"
E32_SUMMARY_NAME = "summary.json"
#: The paper prints the E32 tables (Appendix L) once they are committed and the frozen test is
#: scored. A test can set this to False to check the refusal that stood before they were built.
E32_READY = True
#: The first appendix table of E32; the tables before it keep their numbers.
E32_FIRST_TABLE = 26
#: E30 (Amendment 14): the league table tested on players who changed domestic league.
#: Absent until the Moves lane commits it; absence means "E30 not run".
E30_DIR = ART + "sloan-fullpaper-league-changes-2026-11/"
E30_SUMMARY = Path(E30_DIR + "summary.json")
#: The full scored record: the secondary results S-a to S-f and E31b (Amendment 15).
E30_FULL = Path(E30_DIR + "e30_summary.json")
#: The league-pair table behind the second panel of Figure 1 (Amendment 14, S-f).
E30_PAIRS = Path(E30_DIR + "s_f_league_pairs.csv")
#: E31a (Amendment 15, exploratory): a league table printed in 2015 on the arrivals of 2020-2025.
E31_SUMMARY = Path(ART + "sloan-fullpaper-published-tables-2026-11/summary.json")
#: Inputs that exist only once their analysis is committed (see ``optional_inputs``).
#: The freeze record of E30: its registered constants name the arrival seasons (Amendment 19).
E30_FREEZE = Path(E30_DIR + "e30_freeze.json")
#: E33 (Amendment 22, exploratory): sensitivity (7) of E30 with the stayer forecast also
#: fitted only on seasons before each move. Absent until its single run is committed.
E33_SUMMARY = Path(
    ART + "sloan-fullpaper-league-changes-chrono-2026-11/e33_summary.json"
)
AMENDMENT_22_SHA256 = "4c234e20a8bf88dee7098ff3fe095de262d25a946413f4ff88fc0a908dad0ad0"
#: Amendment 23 (approved by Amir on 22 November 2026; commit bf60fe3, pushed alone; merged into
#: main as 17b99e5): rules 1 to 4 and 6 fix wording and placement and one appendix table of the
#: frozen test; rule 5 (the exploratory analysis E34) is not printed by this renderer yet.
AMENDMENT_23_SHA256 = "8a440ef497d44aeb094f5c439f104ff753084a47576b1428bc881960bd4c1ad7"
#: Amendment 24 (approved by Amir on 22 November 2026; commit 8175f92, pushed alone; merged into
#: main as 0df0d47): one phrase of Amendment 23, rule 4, made explicit before the frozen test is
#: scored. For the order of reading, that test "has been scored" once its score record is
#: committed, whatever status the record carries. It adds no analysis and no number.
AMENDMENT_24_SHA256 = "f0caf0fdc8e97e01f27906d19f6bf68d6b1271c2c3d158ee29b753445751b9c8"
#: Amendment 25 (approved by Amir on 24 November 2026; commit d4aa4bc, pushed alone; merged into
#: main as 4f5c682): how the scored frozen test is shown. One figure of its registered paired
#: contrasts, the read-out of the league numbers (S2) in the abstract, the introduction and the
#: conclusion, the ordering sentences (S4) in the main text, and a clause where an interval
#: excludes the 2020-2025 estimate. It adds no analysis; in every state that is not scored
#: nothing of it is printed.
AMENDMENT_25_SHA256 = "03f36baf84869b57cd26de76f2b8e5d0f695eac2253828f6fd7840c7e0191e68"
#: E34 (Amendment 23, rule 5; exploratory): two published league scales on the older arrivals.
#: Absent until its one retained run is committed; absence means "nothing of E34 is printed".
E34_DIR = ART + "sloan-fullpaper-published-scales-older-2026-11/"
E34_SUMMARY = Path(E34_DIR + "summary.json")
E34_SCALE_RECORD = Path(E34_DIR + "gaussianhoops_2026_league_strength.json")
OPTIONAL_SOURCES = {
    "e34": E34_SUMMARY,
    "e30": E30_SUMMARY,
    "e30_full": E30_FULL,
    "e30_freeze": E30_FREEZE,
    "e31": E31_SUMMARY,
    "e33": E33_SUMMARY,
}
OPTIONAL_TABLES = {"e30_pairs": E30_PAIRS}
E30_NOT_RUN = "not_run"
E30_CASES = (
    "clear",
    "positive_named_limit",
    "positive_not_separable",
    "null",
    "against",
)
#: The case names of the scored record (scripts/sloan_fullpaper_league_changes.py::CASE_CODES).
E30_CASE_NAMES = {
    "clear": "Clear",
    "positive_named_limit": "Positive, with a named limit",
    "positive_not_separable": "Positive, not separable from chance",
    "null": "Null",
    "against": "Against",
}
#: Cases that take the first title and license "tested on league changes it was never fitted to".
E30_TESTED = ("clear", "positive_named_limit")
#: Gate G16a: with these cases the abstract may not contain the words below.
E30_NO_TEST_WORDS = ("null", "against", E30_NOT_RUN)
G16A_BANNED = ("tested", "validated", "never fitted to")
#: Amendment 14's wording for the Null case names this slope ("a slope of 0.11 would have been
#: detected with 80% power under the planning assumptions"). It is a constant of the registration.
E30_PLANNING_SLOPE = "0.11"
E30_ALPHA = 0.05
#: The secondary results S-a to S-f of E30 must be printed (Amendment 14). They are: in Results
#: (``e30_section``), in Appendix M (``e30_appendix``) and in the right panel of Figure 1.
#: While this is False a render with an E30 summary is refused by ``--final``.
E30_SECONDARY_READY = True
#: Amendment 16, rule 4, as Amendment 17 reads it ("Counting numbers in the abstract"): the
#: abstract carries at most eight numbers, and at most nine in the two cases of E30 that
#: Amendment 17 names (see ``abstract_limit``).
ABSTRACT_MAX_NUMBERS = 8
ABSTRACT_MAX_NUMBERS_E30 = 9

META = {
    "title": TITLE,
    "track": "Basketball",
    "repo_url": "https://github.com/AT020993/cross-league-translation",
    "freeze_time": "3 November 2026, 10:55 UTC",
    "prereg_time": "3 November 2026, 09:15 UTC",
    "amend1_time": "4 November 2026, 22:06 UTC",
    "amend2_time": "5 November 2026, 06:49 UTC",
    "amend3_time": "11 November 2026, 16:06 UTC",
    "amend4_time": "11 November 2026, 19:31 UTC",
    "amend5_time": "12 November 2026, 14:49 UTC",
    "amend6_time": "12 November 2026, 18:25 UTC",
    "amend7_time": "12 November 2026, 22:01 UTC",
    # E30 (Amendments 14 and 17): push times from the repository's activity log
    "amend14_time": "17 November 2026, 17:08 UTC",
    "amend17_time": "17 November 2026, 20:28 UTC",
    "e30_freeze_time": "17 November 2026, 21:51 UTC",
    "e30_hash_time": "17 November 2026, 22:03 UTC",
    "e30_freeze_day": "17 November 2026",
    "e30_score_day": "18 November 2026",
    "p1_cutoff": "24 November 2026",
    "p1_late_cutoff": "15 February 2027",
}
POOLS = (
    "official_corrected",
    "verified_same_club_full",
    "overlap_keys_full",
    "same_club",
)
LEAGUE_NAMES = paper_figures.LEAGUE_NAMES
RECIPE_NAMES = {
    "R1": "Exposure-weighted ratios, pooled (submitted)",
    "R2": "Ratio of totals (MLE/NHLe style), pooled",
    "R3": "Unweighted ratios, pooled",
    "R4": "Exposure-weighted ratios, no pooling",
    "R5": "Exposure-weighted ratios, alternative pooling",
    "R6": "One factor per destination",
}
OUTCOME_NAMES = {
    "O1": "EFF/36",
    "O2": "Points/36",
    "O3": "Game Score/36",
    "O4": "EFF per 100 possessions",
}
#: The registered P1 directions and their 2020-2025 anchor contrasts.
P1_CONTRASTS = {
    "P-a": ("translation's gain over history", "history_gain"),
    "P-b": ("the league-aware forecast against history plus translation", "c_h"),
    "P-c": ("translation's increment over the league-aware forecast", "inc10"),
}


class ClaimError(ValueError):
    """A sentence in the template would be false for the committed numbers."""


# ---------------------------------------------------------------- references
#: key -> formatted reference. Numbered by order of first citation in the text.
#:
#: How an entry, and the text, dates a registration against the frozen 2026-27 test:
#: * "before any 2026–27 statistic was read" is said only of what was registered before
#:   15 November 2026 (the freeze of 3 November, Amendment 1). In the literature search of that
#:   day a web-search result page showed three current-season statistic lines of EuroLeague
#:   players (Amendment 8, exposure disclosure; Amendment 23). Seven sentences said it of
#:   18 November until Amir's decision of 22 November 2026 ("Correct them and disclose");
#:   Appendix N of the template now says what was displayed, and points to the other displays
#:   on record. Claude Science checked the wording the same day.
#: * A later registration is dated "before scoring", "before the scoring of" the test: words
#:   that also hold in a paper whose test "could not be scored cleanly". The entry of
#:   Amendment 8 says "before the test was scored" and stays as it is: it is a sentence of
#:   render 39, which gate G19c of Amendment 19 keeps.
REFERENCES = {
    "james1985": "James, B. (1985). *The Bill James Baseball Abstract 1985*. New York: Ballantine Books.",
    "davenport1996": "Davenport, C. (1996). Davenport Translations. *Baseball Prospectus 1996*. https://legacy.baseballprospectus.com/other/bp1996/dtessay.html",
    "davenport1998": "Davenport, C. (1998, January 30). DTs vs. MLEs – A Validation Study. *Baseball Prospectus*. https://www.baseballprospectus.com/news/article/49/dts-vs-mles-a-validation-study/",
    "desjardins2004": "Desjardins, G. (2004). League Equivalencies. HockeyAnalytics.com. http://hockeyanalytics.com/Research_files/League_Equivalencies.pdf",
    "bacon2021": "Bacon, P. (2021). NHL Equivalency (NHLe) and Prospect Projection Models (describing C. J. Turtoro's Network NHLe). HockeyStats.com. https://hockeystats.com/methodology/nhle",
    "pelton2013": "Pelton, K. (2013, October 9). What is SCHOENE? *ESPN*. https://www.espn.com/nba/story/_/id/9797404/explaining-schoene-projection-system",
    "pelton2014": "Pelton, K. (2014, June 10). Projecting top 10 int'l prospects. *ESPN*. https://www.espn.com/nba/draft2014/story/_/id/11064231/clint-capela-leads-projection-top-10-international-prospects-2014-nba-draft",
    "vashro2015": "Vashro, L. (2015, November 6). Deep Dives: Measuring Level of Competition Around the World. *Nylon Calculus (FanSided)*. https://fansided.com/2015/11/06/deep-dives-measuring-level-of-competition-around-the-world/",
    "leepage2021": "Lee, D.-J., and Page, G. L. (2021). Big Data in Sports: Predictive Models for Basketball Player's Performance. *Mathematics in Industry Reports* (ESGI 131). https://doi.org/10.33774/miir-2021-h4x62",
    "glazer2026": "Glazer, A. K. (2026). Nuthin' But A G League: Estimating league translation factors. *Journal of Sports Analytics*, 12. https://doi.org/10.1177/22150218261428808",
    "salador2011": "Salador, K. (2011). Forecasting Performance of International Players in the NBA. MIT Sloan Sports Analytics Conference. http://www.sloansportsconference.com/wp-content/uploads/2011/08/Forecasting-Performance-of-International-Players-in-the-NBA.pdf (archived: https://web.archive.org/web/20170811130958/http://www.sloansportsconference.com/wp-content/uploads/2011/08/Forecasting-Performance-of-International-Players-in-the-NBA.pdf)",
    "dinsdale2022": "Dinsdale, D., and Gallagher, J. (2022). Transfer Portal: Accurately Forecasting the Impact of a Player Transfer in Soccer. arXiv preprint arXiv:2201.11533. https://arxiv.org/abs/2201.11533",
    "shaikh2026": "Shaikh, M. A. (2026). Hierarchical Bayesian modeling of cross-league performance translation in elite football. *Journal of Sports Analytics*, 12. https://doi.org/10.1177/22150218261481583",
    "shaikh2026b": "Shaikh, M. A. (2026). A Machine Learning Framework for Cross-League Per-90 Statistic Translation in Elite Football: A Comparative Model Zoo with Conformal Prediction. SportRxiv preprint. https://doi.org/10.51224/sportrxiv.959",
    "yeh2022": "Yeh, C.-K., Rice, G., and Dubin, J. A. (2022). Evaluating Real-Time Probabilistic Forecasts With Application to National Basketball Association Outcome Prediction. *The American Statistician*, 76(3), 214–223. https://doi.org/10.1080/00031305.2021.1967781",
    "diebold1995": "Diebold, F. X., and Mariano, R. S. (1995). Comparing Predictive Accuracy. *Journal of Business & Economic Statistics*, 13(3), 253–263. https://doi.org/10.1080/07350015.1995.10524599",
    "gneiting2011": "Gneiting, T. (2011). Making and Evaluating Point Forecasts. *Journal of the American Statistical Association*, 106(494), 746–762. https://doi.org/10.1198/jasa.2011.r10138",
    "gamescore": "Sports Reference. Glossary: Game Score (GmSc), a formula created by John Hollinger. https://www.sports-reference.com/cbb/about/glossary.html (accessed November 2026)",
    "kubatko2007": "Kubatko, J., Oliver, D., Pelton, K., and Rosenbaum, D. T. (2007). A Starting Point for Analyzing Basketball Statistics. *Journal of Quantitative Analysis in Sports*, 3(3). https://doi.org/10.2202/1559-0410.1070",
    "spearman1910": "Spearman, C. (1910). Correlation calculated from faulty data. *British Journal of Psychology*, 3(3), 271–295; Brown, W. (1910). Some experimental results in the correlation of mental abilities. *British Journal of Psychology*, 3(3), 296–322. https://doi.org/10.1111/j.2044-8295.1910.tb00206.x and https://doi.org/10.1111/j.2044-8295.1910.tb00207.x",
    "efron1975": "Efron, B., and Morris, C. (1975). Data Analysis Using Stein's Estimator and Its Generalizations. *Journal of the American Statistical Association*, 70(350), 311–319. https://doi.org/10.1080/01621459.1975.10479864",
    "cameron2011": "Cameron, A. C., Gelbach, J. B., and Miller, D. L. (2011). Robust Inference With Multiway Clustering. *Journal of Business & Economic Statistics*, 29(2), 238–249. https://doi.org/10.1198/jbes.2010.07136",
    "cameron2008": "Cameron, A. C., Gelbach, J. B., and Miller, D. L. (2008). Bootstrap-Based Improvements for Inference with Clustered Errors. *Review of Economics and Statistics*, 90(3), 414–427. https://doi.org/10.1162/rest.90.3.414",
    "cawley2010": "Cawley, G. C., and Talbot, N. L. C. (2010). On Over-fitting in Model Selection and Subsequent Selection Bias in Performance Evaluation. *Journal of Machine Learning Research*, 11, 2079–2107. https://jmlr.org/papers/v11/cawley10a.html",
    "holm1979": "Holm, S. (1979). A Simple Sequentially Rejective Multiple Test Procedure. *Scandinavian Journal of Statistics*, 6, 65–70. https://www.jstor.org/stable/4615733",
    "lakens2017": "Lakens, D. (2017). Equivalence Tests: A Practical Primer for t Tests, Correlations, and Meta-Analyses. *Social Psychological and Personality Science*, 8(4), 355–362. https://doi.org/10.1177/1948550617697177",
    "kendall1938": "Kendall, M. G. (1938). A New Measure of Rank Correlation. *Biometrika*, 30(1–2), 81–93. https://doi.org/10.1093/biomet/30.1-2.81",
    "lei2018": "Lei, J., G'Sell, M., Rinaldo, A., Tibshirani, R. J., and Wasserman, L. (2018). Distribution-Free Predictive Inference for Regression. *Journal of the American Statistical Association*, 113(523), 1094–1111. https://doi.org/10.1080/01621459.2017.1307116",
    "barber2023": "Barber, R. F., Candès, E. J., Ramdas, A., and Tibshirani, R. J. (2023). Conformal prediction beyond exchangeability. *The Annals of Statistics*, 51(2), 816–845. https://doi.org/10.1214/23-AOS2276",
    "elmachtoub2022": 'Elmachtoub, A. N., and Grigas, P. (2022). Smart "Predict, then Optimize". *Management Science*, 68(1), 9–26. https://doi.org/10.1287/mnsc.2020.3922',
    "prereg": "Pre-registration of the full-paper analyses and the 2026–27 frozen test (2026). Pushed 3 November 2026, 09:15 UTC, before implementation. Full-paper companion materials (release status in Data and code), https://github.com/AT020993/cross-league-translation",
    "amend1": "Pre-registration Amendment 1: analyses E10–E17 and the February 2027 re-score of the frozen test (2026). Commit f1a3453, 4 November 2026, 22:06 UTC, before implementation. Full-paper companion materials (release status in Data and code), https://github.com/AT020993/cross-league-translation",
    "amend2": "Pre-registration Amendment 2: the stint rule for the survivorship analysis E14 (2026). Commit 41efa97, 5 November 2026, 06:49 UTC, before the E14 re-run. Full-paper companion materials (release status in Data and code), https://github.com/AT020993/cross-league-translation",
    "amend3": "Pre-registration Amendment 3: analyses E18–E23 (forecast level, table stability, forecast gaps, error bands by league, the above-average-season discount) (2026). Commit caf0902, 11 November 2026, 16:06 UTC, before implementation. Full-paper companion materials (release status in Data and code), https://github.com/AT020993/cross-league-translation",
    "amend4": "Pre-registration Amendment 4: analysis E24 (league biases of a forecast that knows the destination but not the source league) (2026). Commit 5ab52fa, 11 November 2026, 19:31 UTC, before implementation and after the Amendment 3 results. Full-paper companion materials (release status in Data and code), https://github.com/AT020993/cross-league-translation",
    "amend5": "Pre-registration Amendment 5: analysis E25 (a second, larger identity-linkage audit) (2026). Commit be61514, 12 November 2026, 14:49 UTC, before implementation and after the first audit's result. Full-paper companion materials (release status in Data and code), https://github.com/AT020993/cross-league-translation",
    "amend6": "Pre-registration Amendment 6: analysis E26 (an identity audit of the forecast arrivals) (2026). Commit 245bafa, 12 November 2026, 18:25 UTC, before implementation and after both linkage audits' results. Full-paper companion materials (release status in Data and code), https://github.com/AT020993/cross-league-translation",
    "amend7": "Pre-registration Amendment 7: analysis E27 (the frozen forecasts tested on older seasons) (2026). Commit e884afe, 12 November 2026, 22:01 UTC, before implementation and before any outcome of an older arrival was read. Full-paper companion materials (release status in Data and code), https://github.com/AT020993/cross-league-translation",
    "amend8": "Pre-registration Amendment 8: more read-outs from the frozen 2026–27 test, and its reading rules made explicit (2026). Commit afcfeff, 16 November 2026, 15:59 UTC, before implementation and before the test was scored. Full-paper companion materials (release status in Data and code), https://github.com/AT020993/cross-league-translation",
    "amend9": "Pre-registration Amendment 9: analysis E28 (the league-aware forecast against the plain baselines, with intervals) (2026). Commit 3c91586, 16 November 2026, 16:01 UTC, before implementation; exploratory, on seasons already examined. Full-paper companion materials (release status in Data and code), https://github.com/AT020993/cross-league-translation",
    "amend10": "Pre-registration Amendment 10: wording for a reading of E28 that Amendment 9 did not foresee (2026). Commit 205207e, 16 November 2026, 20:18 UTC, written after the E28 result and before any sentence about it entered the paper. Full-paper companion materials (release status in Data and code), https://github.com/AT020993/cross-league-translation",
    "amend11": "Pre-registration Amendment 11: analysis E29 (where the league table missed on the older arrivals) (2026). Commit 40f0d27, 16 November 2026, 21:22 UTC, before implementation; descriptive, on outcomes already read. Full-paper companion materials (release status in Data and code), https://github.com/AT020993/cross-league-translation",
    "amend12": "Pre-registration Amendment 12: the league numbers as an equation, and the forecast level weighted by playing time (2026). Commit 89be8fd, 17 November 2026, 08:48 UTC, before the text was written; it adds no analysis and fixes how committed numbers are printed. Full-paper companion materials (release status in Data and code), https://github.com/AT020993/cross-league-translation",
    "amend13": "Pre-registration Amendment 13: the order of the claims on the first page (2026). Commit 6ea7402, 17 November 2026, 09:55 UTC, before the text was written (commit e03d142 of the same day added a specification table and changed no rule); it adds no analysis and no number. Full-paper companion materials (release status in Data and code), https://github.com/AT020993/cross-league-translation",
    "amend18": "Pre-registration Amendment 18: readings made explicit before the frozen 2026–27 test is scored, and before any named newcomer is printed (2026). Commit 74794bf, pushed 18 November 2026, 09:01 UTC, before the scoring of that test. Full-paper companion materials (release status in Data and code), https://github.com/AT020993/cross-league-translation",
    "amend19": "Pre-registration Amendment 19: a shorter paper, the wording of its first page and one labelled reading of a registered slope (2026). Commit e377464, pushed 18 November 2026, 12:25 UTC, after the test of analysis E30 was scored and after three blind mock readings of the paper, before the text it governs was written and before the scoring of the frozen 2026–27 test. Full-paper companion materials (release status in Data and code), https://github.com/AT020993/cross-league-translation",
    "amend16": "Pre-registration Amendment 16: the paper built around its league table, and the rules of its first page (2026). Commit d5f721c, pushed 17 November 2026, 17:09 UTC, before that text was written; it adds no analysis and no number. Full-paper companion materials (release status in Data and code), https://github.com/AT020993/cross-league-translation",
    "gba2025": "German Basketball Analytics (2025, June 1). Ranking all Major European Basketball Leagues. https://germanbasketballanalytics.substack.com/p/ranking-all-major-european-basketball (accessed 17 November 2026)",
    "bustamante2026": "Bustamante-Sánchez, Á. (2026). league-translator (code repository, created 4 November 2026). https://github.com/alvaro-bustamante/league-translator (accessed 17 November 2026)",
    "gaussianhoops2026": "Köchling, P. (2026). League strength: Europe vs. NCAA Power 5. *Gaussian Hoops*. https://www.gaussianhoops.com/projections/league-strength/ (accessed 18 November 2026)",
    "myrte2026": "Myrte, M., Buzzalino, S., and Aymerich, T. (2026). Scouting Anyone: Probabilistic Player Archetypes for Any League. MIT Sloan Sports Analytics Conference (poster). https://www.sloansportsconference.com/research-papers/scouting-anyone-probabilistic-player-archetypes-for-any-league",
    "berger2021": "Berger, T., and Daumann, F. (2021). Increasing the shot at a quality draft-decision – A Bayesian approach to improve predicting three-point accuracy translation in the NBA Draft. MIT Sloan Sports Analytics Conference. https://www.sloansportsconference.com/research-papers/increasing-the-shot-at-a-quality-draft-decision-a-bayesian-approach-to-improve-predicting-three-point-accuracy-translation-in-the-nba-draft",
}

#: Cited only where the text cites them: while E30 is not run the paper says nothing about
#: league changes (Amendment 16, rule 3), and that includes its reference list.
OPTIONAL_REFERENCES = {
    "amend20": "Pre-registration Amendment 20: five named pairs of newcomers in the main text, and one reading of the league-changes slope for a club (2026). Commit 0e8cd21, pushed 18 November 2026, 16:30 UTC, after the test of analysis E30 was scored and after two rounds of blind mock readings of the paper, before the text it governs was written and before the scoring of the frozen 2026–27 test. Full-paper companion materials (release status in Data and code), https://github.com/AT020993/cross-league-translation",
    "amend21": 'Pre-registration Amendment 21: the conclusion without the word "matches", and the wider interval of the league-changes slope on the first page (2026). Commit 5d1d931, pushed 18 November 2026, 22:01 UTC, after the test of analysis E30 was scored and after three rounds of blind mock readings of the paper, before the text it governs was written and before the scoring of the frozen 2026–27 test. Full-paper companion materials (release status in Data and code), https://github.com/AT020993/cross-league-translation',
    "amend22": "Pre-registration Amendment 22: analysis E33 (the league-changes sensitivity with the stayer forecast also fitted only on earlier seasons) (2026). Commit 1e69136, pushed 19 November 2026, 18:28 UTC, after the test of analysis E30 was scored and its sensitivities were seen, before the generator of E33 was written and before any estimate of E33 was computed; E33 is exploratory. Full-paper companion materials (release status in Data and code), https://github.com/AT020993/cross-league-translation",
    "amend23": "Pre-registration Amendment 23: the unit in words, three terms of the equation side by side, where the forecasts run low, a narrower statement on prior work, two published league scales on the older arrivals (analysis E34) and one appendix table of the frozen test (2026). Commit bf60fe3, pushed 22 November 2026, 12:46 UTC, after the test of analysis E30 was scored, after the comparisons of analysis E34 had been computed outside the registration, and before the scoring of the frozen 2026–27 test; E34 is exploratory. Full-paper companion materials (release status in Data and code), https://github.com/AT020993/cross-league-translation",
    "amend24": "Pre-registration Amendment 24: when the pages that show current-season statistics are read if the frozen test ends inconclusive (2026). Commit 8175f92, pushed 22 November 2026, 20:01 UTC, before the scoring of the frozen 2026–27 test; it adds no analysis and no number. Full-paper companion materials (release status in Data and code), https://github.com/AT020993/cross-league-translation",
    "amend25": "Pre-registration Amendment 25: how the scored frozen test is shown: one figure of its contrasts, the read-out of the league numbers where the paper promises it, the ordering sentence in the main text, and a sentence where an interval excludes the earlier estimate (2026). Commit d4aa4bc, pushed 24 November 2026, 08:51 UTC, before the scoring of the frozen 2026–27 test and after blind readers had read the paper composed from rehearsal records with made-up outcomes; it adds no analysis and changes no verdict. Full-paper companion materials (release status in Data and code), https://github.com/AT020993/cross-league-translation",
    "amend27": "Pre-registration Amendment 27: one sentence that points from the comparison with a published league table to its exploratory reading on the older arrivals (2026). Commit 38574fb, pushed 25 November 2026, 12:12 UTC, after E34 was run, with its values known (commit 60b03c5 of the same day added a specification table and changed nothing above it); it registers nothing in advance, adds no analysis and changes no number. Full-paper companion materials (release status in Data and code), https://github.com/AT020993/cross-league-translation",
    "amend32": "Pre-registration Amendment 32: twenty-seven passages reworded for register, the appendix tables numbered in the order in which they stand, and values printed on three figures (2026). Commit 25ae7e3, pushed 27 November 2026, 14:59 UTC, after every result was known; it registers nothing in advance, adds no analysis and changes no result. Full-paper companion materials (release status in Data and code), https://github.com/AT020993/cross-league-translation",
    "amend30": "Pre-registration Amendment 30: eighteen corrections after the changes of Amendment 29, made after a fresh reader had checked them against the rest of the paper (2026). Commit 5376608, pushed 26 November 2026, 19:30 UTC, after every result was known; it registers nothing in advance, adds no analysis and changes no result. Full-paper companion materials (release status in Data and code), https://github.com/AT020993/cross-league-translation",
    "amend29": "Pre-registration Amendment 29: the first page reworded after a blind comparison of two first pages, further sentences repaired or added, and two values of a registered read-out printed (2026). Commit 25aba66, pushed 26 November 2026, 18:13 UTC, after every result was known; it registers nothing in advance, adds no analysis and changes no result. Full-paper companion materials (release status in Data and code), https://github.com/AT020993/cross-league-translation",
    "amend28": "Pre-registration Amendment 28: thirteen repaired sentences, four sentences that define the paper's terms, the figures redrawn in one style, and the Paper ID line (2026). Commit e9fd7dc, pushed 26 November 2026, 09:00 UTC, after every result was known; it registers nothing in advance, adds no analysis and changes no number. Full-paper companion materials (release status in Data and code), https://github.com/AT020993/cross-league-translation",
    "amend26": "Pre-registration Amendment 26: the words of the paper once the frozen 2026–27 test was scored and found inconclusive, and two descriptive sentences from values the paper already prints (2026). Commit c96b283, pushed 25 November 2026, 07:53 UTC, after the scoring of the frozen 2026–27 test, with every value of its score record known; it registers nothing in advance, adds no analysis and changes no number. Full-paper companion materials (release status in Data and code), https://github.com/AT020993/cross-league-translation",
    "amend14": "Pre-registration Amendment 14: analysis E30 (the league table tested on players who changed domestic league) (2026). Commit ae99909, pushed 17 November 2026, 17:08 UTC, before implementation and before any outcome of a league change was read. Full-paper companion materials (release status in Data and code), https://github.com/AT020993/cross-league-translation",
    "amend15": "Pre-registration Amendment 15: analysis E31 (a published league table as a rival) and E32 (named 2026–27 newcomers with their frozen forecasts) (2026). Commit 48f752c, pushed 17 November 2026, 17:09 UTC, before implementation; E31 on the arrivals of 2020–2025 is exploratory. Full-paper companion materials (release status in Data and code), https://github.com/AT020993/cross-league-translation",
    "amend17": "Pre-registration Amendment 17: readings of Amendments 14 to 16 made explicit, and two corrections (2026). Commit d6ab516, pushed 17 November 2026, 20:28 UTC, before the predictions of analysis E30 were frozen and before any of its outcomes was joined or read; one rule (which weighting decides the sentences about the 2015 table on the arrivals of 2020–2025) was written after that result was seen and says so. Full-paper companion materials (release status in Data and code), https://github.com/AT020993/cross-league-translation",
}

#: Related work (Amendment 16, rule 6). The last sentence says what the paper offers and is
#: chosen by the E30 case (``offer_sentence``); the paper says "the first" of nothing and does
#: not say that clubs use translation factors.
#: The same section in full, printed as Appendix O.
RELATED_FULL = """One number per league is an old idea: baseball's major-league equivalents and hockey's league equivalencies put leagues on one scale [@james1985; @desjardins2004; @bacon2021]. The estimator here is a ridge regression. Projection across leagues in basketball also predates this study. Salador regressed NBA outcomes on international statistics and league indicators [@salador2011]; Berger and Daumann shrank college shooting percentages before projection [@berger2021]. Analysts have published league scales that cover European basketball: a scale of competitions around the world, built from shared players for the NBA draft [@vashro2015]; a ranking of European leagues from how far clubs' ratings fall between domestic and European play [@gba2025]; and a code repository that fits league effects for Spanish and European competitions from players seen in more than one of them [@bustamante2026]. Glazer estimates G League-to-NBA translation factors by matching similar players and a difference-in-differences estimator [@glazer2026]. A further public scale gives one strength value per league and is fitted on players who moved, between leagues from one season to the next and between a national league and a European cup in the same season (2021–22 to 2025–26); it measures points, rebounds and assists per 36 minutes, adjusted for pace, and reports its own consistency checks [@gaussianhoops2026]. {{rival_fit_sentence}} That scale is not scored here: it is built on seasons the paper scores, so it could only be scored on the frozen 2026–27 test, and it is not a registered arm [@amend15]. A Sloan poster builds player archetypes that can be applied in any league, including leagues without advanced data; it describes styles, not levels [@myrte2026]. In a bounded search in English we found no public test of such league adjustments on what European arrivals went on to do. Soccer transfer models use player, team and league features [@dinsdale2022]; there, ridge and boosting models with a league indicator can match hierarchical translation [@shaikh2026], and regression models with league identifiers beat naive and pair-average baselines on average, though not on every statistic [@shaikh2026b]. Same-target comparison against strong simple alternatives is established practice [@diebold1995; @gneiting2011; @yeh2022]. {{offer_sentence}}"""
#: What the closest basketball paper leaves open, printed under Appendix O after the section in
#: full (Amir, 20 November 2026: "Glazer: 1"). Checked against the full article; the record is in
#: docs/plans/sloan-ssac27-literature-evidence.md ("Glazer (2026) read in full"). It says what the
#: article says of itself; it does not say that its factors fail as forecasts.
RELATED_GLAZER = """Glazer presents the G League-to-NBA factors as estimates of how a player's existing statistics would have looked in the other league, not as forecasts, and scores none of them on later players [@glazer2026]."""

#: How the "bounded search" of Related work was done, printed under Appendix O (Amir, 19 November
#: 2026). Every statement is in docs/plans/sloan-ssac27-literature-evidence.md ("Record of the
#: bounded search"). RELATED_FULL and RELATED are not changed.
RELATED_SEARCH = """How the search was done. The search behind the sentence "we found no public test" was run on 15 November 2026 and 17 November 2026, in English only. It queried three indexes of scholarly work (OpenAlex, Crossref and arXiv), followed the citations around the closest papers for one step, and used web searches for analysts' pages. It worked from abstracts and public pages and is not a systematic review. On 18 November 2026 the sentence was checked again against the Gaussian Hoops page, which reports its own consistency checks [@gaussianhoops2026]: those are checks of the scale against itself, not a test on what arriving players went on to do. The sentence is a statement about this search, not proof that no such test exists."""
RELATED = """One number per league is an old idea: baseball's major-league equivalents and hockey's league equivalencies put leagues on one scale [@james1985; @desjardins2004; @bacon2021], and projection across leagues in basketball predates this study [@salador2011; @berger2021]. Analysts have published league scales that cover European basketball [@vashro2015; @gba2025; @bustamante2026]; the first is scored here. Glazer estimates G League-to-NBA translation factors by matching similar players and a difference-in-differences estimator [@glazer2026]. The Gaussian Hoops scale{{rival_clause}} gives one strength value per league [@gaussianhoops2026]; it is not scored here, because it is built on seasons the paper scores and is not a registered arm [@amend15]. A bounded search in English found no public test of such league adjustments on what European arrivals went on to do. {{offer_sentence}} Appendix O gives this section in full."""

#: Amendment 23, rule 4: a narrower statement on prior work. The three constants above hold the
#: sentence Amendment 16 licensed, and the paper keeps it until the record of rule 4
#: (``SOURCES["prior_work"]``) gives, for every named page, the date of its full read and what it
#: reports (gate G23d). Then ``prior_work_blocks`` puts the two statements of rule 4 in its place.
PRIOR_WORK_OLD_SHORT = "A bounded search in English found no public test of such league adjustments on what European arrivals went on to do."
PRIOR_WORK_OLD_FULL = "In a bounded search in English we found no public test of such league adjustments on what European arrivals went on to do."
PRIOR_WORK_OLD_QUOTE = '"we found no public test"'
#: Gate G23d: the words by which the old sentence is recognised in any part of the paper.
PRIOR_WORK_OLD_MARK = "found no public test of such league adjustments"
#: "What was not found": the sentence Amendment 23, rule 4, registers, word for word.
PRIOR_WORK_NOT_FOUND = "A bounded search in English found no public test in basketball that compares a forecast with and without a league adjustment on what players arriving in European competitions went on to do."
PRIOR_WORK_NEW_MARK = "found no public test in basketball"
PRIOR_WORK_NEW_QUOTE = '"found no public test in basketball"'
#: "What was found", short form (the frame of the amendment's example, written for two pages).
PRIOR_WORK_FOUND_MARK = "report how forecasts that use a league level fared"
PRIOR_WORK_FOUND_SHORT = (
    "Two analysts report how forecasts that use a league level fared, one for {first} and one for "
    "{second}; neither reports its forecast without the league level (Appendix O)."
)
#: "How the search was done" gains this sentence before its last one (rule 4: the paragraph "adds
#: the dates on which the further pages were read and that a review named them"). The paper
#: already cites another page of each of the two analysts, so the pages are further ones and
#: the analysts are not.
PRIOR_WORK_READ = "A review of the paper then named further pages of two analysts; they were read in full on {first} and on {second}."
#: Amendment 29, rule 4: where the full read of a page was completed by a later reading, the
#: paragraph says what was read on which day and what was not read (the record's "read_further").
PRIOR_WORK_READ_FURTHER = "A review of the paper then named further pages of two analysts; the first was read in full on {first}; of the second, {second}."
#: The same paragraph says that the sentence was checked again on 18 November 2026. Once its
#: first sentence quotes the narrower statement, which dates from 22 November, that check is a
#: check of the sentence as it stood then.
PRIOR_WORK_CHECK_OLD = "On 18 November 2026 the sentence was checked again against"
PRIOR_WORK_CHECK_NEW = "On 18 November 2026 the sentence in its earlier, wider form was checked again against"
PRIOR_WORK_SEARCH_LAST = (
    "The sentence is a statement about this search, not proof that no such test exists."
)
#: The two states of the statement on prior work.
PRIOR_WORK_KEPT, PRIOR_WORK_NARROWED = "kept", "narrowed"
#: Rule 4, "Order of reading", as Amendment 24, rule 1, makes it explicit (gate G24a): the
#: frozen 2026-27 test "has been scored" once the registered scoring run of November 2026 has
#: written its score record and that record is committed, whatever status the record carries.
#: These are the three statuses of a score record (Amendment 8). The record of rule 4 may date
#: the full read of a page that shows statistics of that season beside a score record of any of
#: them, and never while there is no score record. ``E32_STATES`` is another rule and does not
#: follow: Amendment 24 changes no rule on what an inconclusive paper prints of the frozen test.
PRIOR_WORK_READ_STATES = ("scored", "not_adjudicable", "inconclusive")
#: Amendment 24, rule 2: the one sentence Appendix N may carry, in every status, word for word.
#: It stands at the end of the paragraph on what was displayed before scoring, after the
#: sentence on a page that shows current-season statistics.
ORDER_OF_READING_NOTE = (
    "On 22 November 2026, before scoring, a further registration fixed that the two pages which show "
    "current-season statistics are read in full once the score record of the frozen test is committed, "
    "whatever its status [@amend24]."
)
#: The words by which that sentence is recognised in any part of the paper (gate G24b).
ORDER_OF_READING_MARK = "a further registration fixed"
#: What the record gives for a page that has been read in full: what the page forecasts, on which
#: players and seasons the forecast was scored, whether those players are arrivals, and whether the
#: page reports the forecast's accuracy with and without the league level (rule 4, "What was found").
PRIOR_WORK_REPORTS = ("forecasts", "scored_on", "arrivals", "with_and_without")
PRIOR_WORK_COMPARES = "compares_with_and_without_league_level"
#: The short form says that neither analyst reports its forecast without the league level. The
#: record answers that for each page, for any players; the answer above is the narrower one of
#: the condition of rule 4 (basketball players arriving in or playing in European competitions).
PRIOR_WORK_WITHOUT = "reports_accuracy_without_league_level"
#: In a text of the record every number is a named leaf of the record ("{name}"), so that the
#: number manifest traces it to the record. What may be typed: a date, a year, a season label.
PRIOR_WORK_NAMED = re.compile(r"\{[a-z0-9_]+\}")
PRIOR_WORK_LABEL = re.compile(
    r"\b\d{1,2} [A-Z][a-z]+ \d{4}\b|\b(?:19|20)\d{2}(?:[–-]\d{2,4})?\b"
)


# ---------------------------------------------------------------- helpers
def get(data: dict, path: str):
    node = data
    for part in path.split("/"):
        if not isinstance(node, dict) or part not in node:
            raise KeyError(f"missing path: {path}")
        node = node[part]
    return node


def num(x: float, digits: int = 3, sign: bool = False) -> str:
    text = f"{x:+.{digits}f}" if sign else f"{x:.{digits}f}"
    return text.replace("-", "−")


def pct(x: float, digits: int = 1) -> str:
    return f"{100 * x:.{digits}f}%".replace("-", "−")


def pp(x: float, digits: int = 1, sign: bool = True) -> str:
    """A proportion difference in percentage points."""
    return num(100 * x, digits, sign=sign)


def interval(ci, digits: int = 3) -> str:
    return f"[{num(ci[0], digits)}, {num(ci[1], digits)}]"


def cell(c: dict, digits: int = 3) -> str:
    """'+0.161 [0.077, 0.246]' from a contrast with a player_club_season interval."""
    ci = c["player_club_season"]["ci95"] if "player_club_season" in c else c["ci95"]
    return f"{num(c['difference'], digits, sign=True)} {interval(ci, digits)}"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def league(text: str) -> str:
    """Replace league codes in a committed sentence by their display names."""
    for code, name in sorted(LEAGUE_NAMES.items(), key=lambda kv: -len(kv[0])):
        text = text.replace(code, name)
    return text


def p1_file(root: Path):
    for p in P1_SCORE_CANDIDATES:
        if (root / p).is_file():
            return p
    return None


def e30_file(root: Path):
    """The committed E30 summary, or None while E30 is not run."""
    return E30_SUMMARY if (root / E30_SUMMARY).is_file() else None


def optional_inputs(root: Path) -> dict:
    """The E30 and E31 inputs that exist under ``root``: name -> path."""
    found = {}
    if (root / E30_SUMMARY).is_file():
        found["e30"] = E30_SUMMARY
        for name, path in (
            ("e30_full", E30_FULL),
            ("e30_freeze", E30_FREEZE),
            ("e30_pairs", E30_PAIRS),
        ):
            if (root / path).is_file():
                found[name] = path
        if (root / E33_SUMMARY).is_file():
            found["e33"] = E33_SUMMARY
    if (root / E31_SUMMARY).is_file():
        found["e31"] = E31_SUMMARY
    if (root / E34_SUMMARY).is_file():
        found["e34"] = E34_SUMMARY
    # E32 (Amendments 15, 18 and 20): present only after the frozen test is scored
    for candidate in E32_CANDIDATES:
        if (root / candidate).is_file():
            found["e32_newcomers"] = candidate
            for name, file in (
                ("e32_pairs", E32_PAIRS_NAME),
                ("e32_summary", E32_SUMMARY_NAME),
            ):
                if (root / candidate.with_name(file)).is_file():
                    found[name] = candidate.with_name(file)
            break
    return found


def load(root: Path) -> dict:
    data = {k: json.loads((root / p).read_text()) for k, p in SOURCES.items()}
    for k, p in TABLES.items():
        with (root / p).open() as handle:
            data[k] = list(csv.DictReader(handle))
    for k, p in TEXTS.items():
        data[k] = (root / p).read_text()
    score = p1_file(root)
    data["p1"] = json.loads((root / score).read_text()) if score else None
    optional = optional_inputs(root)
    for name in OPTIONAL_SOURCES:
        data[name] = (
            json.loads((root / optional[name]).read_text())
            if name in optional
            else None
        )
    data["e30_pairs"] = None
    if "e30_pairs" in optional:
        with (root / E30_PAIRS).open() as handle:
            data["e30_pairs"] = list(csv.DictReader(handle))
    if data["e30"] is not None:
        if data["e30_full"] is None:
            raise ClaimError("E30: summary.json is committed without the full record")
        if sha(root / E30_FULL) != data["e30"].get("source_sha256"):
            raise ClaimError(
                "E30: summary.json was not copied from the committed full record"
            )
        e30_check(data["e30"], data["e30_full"])
        if prints_first_page_words(data):
            league_number_check(data)  # gate G19a (Amendment 19)
        if data["e33"] is not None:
            e33_check(data["e33"], data["e30_full"])  # Amendment 22
    data["e32_tables"] = next(
        (str(p) for p in E32_CANDIDATES if (root / p).is_file()), None
    )
    data["e32_pairs"], data["e32_summary"], data["e32_players"] = None, None, None
    if data["e32_tables"]:
        folder = root / Path(data["e32_tables"]).parent
        with (root / data["e32_tables"]).open() as handle:
            data["e32_players"] = list(csv.DictReader(handle))
        if (folder / E32_PAIRS_NAME).is_file():
            with (folder / E32_PAIRS_NAME).open() as handle:
                data["e32_pairs"] = list(csv.DictReader(handle))
            data["e32_summary"] = json.loads((folder / E32_SUMMARY_NAME).read_text())
    older_counts_add_up(data["older"])
    destination_term_check(data)  # gate G23b (Amendment 23, rule 2)
    p1_scorecard_check(data["p1"])  # gate G23e (Amendment 23, rule 6)
    e34_check(data, root)  # the record of E34 (Amendment 23, rule 5)
    # the record of Amendment 23, rule 4: one a sentence may be written from, and no page read
    # in full before rule 4 allows it (gate G24a, Amendment 24)
    prior_work_order_check(data)
    return data


def older_counts_add_up(o: dict) -> None:
    """E27: the extract on disk must count the same arrivals every way it counts them.

    Checked when the file is loaded, not when the text is composed: the number
    manifest traces a number by changing one value at a time, which a check
    inside compose() would refuse.
    """
    n = o["n"]
    counts = {
        "by league": sum(o["by_league"].values()),
        "by destination": sum(o["by_destination"].values()),
        "by season": sum(o["by_season"].values()),
        **{f"comparison {k}": c["n"] for k, c in o["comparisons"]["all"].items()},
    }
    wrong = sorted(k for k, v in counts.items() if v != n)
    if wrong:
        raise ClaimError(f"the E27 arrivals do not add up to {n}: {', '.join(wrong)}")


def power_table(prereg: str) -> dict:
    """The pre-registered P1 power rows: contrast -> (SD, MDE at n=100, MDE at n=150)."""
    rows = {}
    pattern = re.compile(
        r"^\| (.+?) \| ([0-9.]+) \| [0-9.]+ \| ([0-9.]+) / ([0-9.]+) \|$"
    )
    for line in prereg.splitlines():
        m = pattern.match(line.strip())
        if m:
            rows[m.group(1)] = tuple(float(m.group(i)) for i in (2, 3, 4))
    for need in ("history vs history + translation", "offsets λ10 vs + translation"):
        if need not in rows:
            raise KeyError(f"pre-registered power row missing: {need}")
    return rows


def pair_value(d, pair_type, quantity, models):
    for r in d["pairs"]:
        if (
            r["scope"] == "all_pools"
            and r["pair_type"] == pair_type
            and r["quantity"] == quantity
            and r["models"] == models
        ):
            return {
                "point": float(r["point"]),
                "ci95": [float(r["ci95_low"]), float(r["ci95_high"])],
                "pairs": int(r["pairs"]),
            }
    raise KeyError(f"no e10 row {pair_type}/{quantity}/{models}")


def e9_seasons(d) -> str:
    """Training seasons of the e9 league-table fit, checked against the per-league counts."""
    e9 = get(d["decide"], "e9")
    n = sum(int(row["e9_training"]) for row in d["counts"])
    if n != e9["training_forecasts"]:
        raise ClaimError(
            f"per-league training n sums to {n}, not {e9['training_forecasts']}"
        )
    seasons = sorted(e9["training_seasons"])
    return f"{seasons[0]}–{seasons[-1]}"


def robust_licences(d) -> tuple[list, list]:
    """E15a licences split by whether the ratio-of-sums intervals are also disjoint (the skills report's rule)."""
    pooled = {
        r["component"]: r
        for r in d["retention"]
        if r["subset_type"] == "pooled" and r["subset"] == "all"
    }
    robust, sensitive = [], []
    for lic in d["licences"]:
        hi, lo = pooled[lic["higher"]], pooled[lic["lower"]]
        disjoint = float(hi["ratio_of_sums_ci_low"]) > float(
            lo["ratio_of_sums_ci_high"]
        )
        (robust if disjoint else sensitive).append((lic["higher"], lic["lower"]))
    return robust, sensitive


# ---------------------------------------------------------------- facts
def facts(d: dict) -> dict:  # noqa: C901 -- one guarded fact per placeholder
    r, rb, dc, am = d["recipes"], d["robust"], d["decide"], d["amend"]
    fx, au, sv, sk = d["flex"], d["audit"], d["surv"], d["skills"]
    a = "results/A/R1"
    m = lambda arm: get(r, f"{a}/metrics/{arm}/mae")  # noqa: E731
    lad = lambda c: get(r, f"{a}/ladder/{c}/player_club_season")  # noqa: E731
    hist, dest = (
        lad("history_only->scheduled_history"),
        lad("history_destination_slope->history_destination_slope_scheduled"),
    )
    inc10 = lad("source_ridge_10->source_ridge_10_scheduled")
    h2h = get(r, "e1/head_to_head/lambda_10/player_club_season")
    floor = get(rb, "e6/outcomes/O1/floor_normal")
    direct_floor = get(rb, "e6/outcomes/O1/floor_half_vs_half_odd_even")
    if not 0 <= direct_floor < m("history_only"):
        raise ClaimError("direct noise reference must lie below history MAE")
    e4 = lambda dst, c: get(rb, f"e4/anchor/{dst}/contrasts/{c}")  # noqa: E731
    gm = get(rb, "e3/O3/contrasts/destination_increment/player_club_season")
    pv = get(dc, "e7/pooled/all/values")
    conf = [row for row in d["conformal"] if row["arm"] == "source_ridge_10"]
    seasons80 = [
        float(row["coverage"])
        for row in conf
        if row["level"] == "0.8" and row["scope"].startswith("season ")
    ]

    def pooled(lvl):
        return next(
            row for row in conf if row["level"] == lvl and row["scope"] == "pooled"
        )

    hw = lambda lvl: get(dc, f"e8/source_ridge_10@{lvl}/calibration")  # noqa: E731
    mean_hw = lambda lvl: sum(v["half_width"] for v in hw(lvl).values()) / len(hw(lvl))  # noqa: E731
    recipes = list(get(r, "recipes"))
    rec_hist = [
        get(
            r,
            f"results/A/{k}/ladder/history_only->scheduled_history/player_club_season/difference",
        )
        for k in recipes
    ]
    rec_lo = [
        get(
            r,
            f"results/A/{k}/ladder/history_only->scheduled_history/player_club_season/ci95",
        )[0]
        for k in recipes
    ]
    if min(rec_lo) <= 0:
        raise ClaimError(
            "'every recipe helps against history, all intervals above zero' is false"
        )
    d1 = [
        pv[f"d1:{arm}"]["point"]
        for arm in (
            "history_only",
            "scheduled_history",
            "source_ridge_10",
            "source_ridge_10_scheduled",
        )
    ]
    right = pv["right_share:source_ridge_10__source_ridge_10_scheduled"]
    righth = pv["right_share:history_only__scheduled_history"]
    tiers = [row for row in d["tiers"] if row["league_dest"] == "euroleague"]
    close = sorted(
        LEAGUE_NAMES[row["league_src"]]
        for row in tiers
        if row["share_previous_tier_top_higher"]
        and abs(float(row["share_previous_tier_top_higher"]) - 0.90) < 0.05
    )
    # E17: head-to-head at all three penalties, avoidable shares, margins, minutes weighting
    hh = get(am, "e17/head_to_head")
    red = {
        row["arm"]: row["share_of_reducible_removed"]
        for row in get(am, "e17/reducible/rows")
    }
    if abs(get(am, "e17/reducible/floor") - floor) > 1e-12:
        raise ClaimError("E17 noise floor differs from the robustness floor")
    margins = [
        row
        for row in get(am, "e17/recipe_margins/rows")
        if row["spec"] == "player_club_season"
    ]
    top = max(margins, key=lambda row: row["upper_bound_eff36"])
    mw = get(am, "e17/minutes_weighted/contrasts")
    mwc = lambda k: mw[k]["minutes_weighted"]  # noqa: E731
    if (
        mw["history_only__scheduled_history"]["unweighted"]["difference"]
        != hist["difference"]
    ):
        raise ClaimError("E17 unweighted history gain differs from Table 1")
    # exchange rates
    ex = {
        (row["source_league"], row["destination"]): float(row["acb16_equivalent_eff36"])
        for row in d["exchange"]
    }
    for lg in ("germany-bbl", "lithuania-lkl", "vtb"):
        for dst in ("euroleague", "eurocup"):
            if not 18.5 <= ex[(lg, dst)] < 19.5:
                raise ClaimError(
                    f"'about a 19' is false for {lg} {dst}: {ex[(lg, dst)]:.2f}"
                )
    for lg in ("france-pro-a", "italy-lba"):
        for dst in ("euroleague", "eurocup"):
            if not abs(ex[(lg, dst)] - 16) < 1:
                raise ClaimError(f"'within one point of Spain' is false for {lg} {dst}")
    hook_short = "16 EFF/36 in Spain's ACB gives the same forecast as about 19 in Germany, Lithuania or VTB"
    hook_long = (
        f"For a player whose career history matches his domestic line, a 16 EFF/36 in Spain's ACB forecasts like a "
        f"{ex[('germany-bbl', 'euroleague')]:.1f} in Germany's BBL, a {ex[('lithuania-lkl', 'euroleague')]:.1f} in Lithuania's LKL "
        f"and a {ex[('vtb', 'euroleague')]:.1f} in the VTB League for a EuroLeague arrival "
        f"({ex[('germany-bbl', 'eurocup')]:.1f}, {ex[('lithuania-lkl', 'eurocup')]:.1f} and {ex[('vtb', 'eurocup')]:.1f} for EuroCup), "
        "while France's Pro A and Italy's LBA sit within one point of Spain."
    )
    # E10 cross- and same-league pairs
    xd = lambda q, mdl: pair_value(d, "cross", q, mdl)  # noqa: E731
    sd = lambda q, mdl: pair_value(d, "same", q, mdl)  # noqa: E731
    x_gain = xd("d1diff", "history_only__source_ridge_10")
    s_gain = sd("d1diff", "history_only__source_ridge_10")
    x_flip = xd("flip_share", "source_ridge_10__source_ridge_10_scheduled")
    x_right = xd("right_share", "source_ridge_10__source_ridge_10_scheduled")
    if get(am, "e10/licence/verdict") != "above_zero" or x_gain["ci95"][0] <= 0:
        raise ClaimError("the E10 cross-league licence is not earned")
    if (
        not right["ci95"][0] <= 0.5 <= right["ci95"][1]
        or not x_right["ci95"][0] <= 0.5 <= x_right["ci95"][1]
    ):
        raise ClaimError("'not distinguishable from a coin flip' is false")
    # E11 bias by league
    e11 = {row["source_league"]: row for row in d["e11"]}
    lic = sorted(k for k, row in e11.items() if row["licence"] == "bias")
    if lic != ["italy-lba", "spain-acb"]:
        raise ClaimError(f"licensed bias leagues changed: {lic}")
    if (
        e11["spain-acb"]["league_aware_covers_zero"] != "True"
        or e11["italy-lba"]["league_aware_covers_zero"] != "False"
    ):
        raise ClaimError("the league-aware reading of the ACB/Italy bias changed")
    others = [
        float(row["p_holm_history_only"]) for k, row in e11.items() if k not in lic
    ]
    f11 = lambda k, c: float(e11[k][c])  # noqa: E731
    # E12 career year
    e12 = get(am, "e12/arms/source_ridge_10")
    refits = [w["beta_a"] for w in e12["walk_forward"]]
    if not get(am, "e12/licence/licensed") or max(refits) >= 0:
        raise ClaimError("the E12 career-year licence is not earned")
    # E16 flexible model
    fc = get(fx, "contrasts")
    prim = fc["primary_offsets10_vs_gbm"]
    if (
        prim["positive_favours"] != "gbm"
        or prim["player_club_season"]["verdict"] != "spans_zero"
    ):
        raise ClaimError("the E16 primary reading changed")
    fred = get(fx, "reducible/models")
    # E13 audit
    e13 = get(au, "e13")
    if e13["licences"]["upper_below_5pct"] or e13["licences"]["point_at_least_10pct"]:
        raise ClaimError("an E13 licence state changed; rewrite the audit paragraph")
    # E25: the second audit (Amendment 5). The linkage sentence quotes its bound.
    e25 = get(d["audit25"], "e25")
    lic25 = e25["licence"]
    if not lic25["bound_earned"] or lic25["point_at_least_10pct"]:
        raise ClaimError("the E25 licence state changed; rewrite the linkage sentence")
    if lic25["third_look_allowed"] or get(d["audit25"], "e13_frame_pairs") != get(
        au, "frame_pairs"
    ):
        raise ClaimError("E25 is not the registered second look at the E13 frame")
    audit25_x = f"{lic25['x_pct']:.1f}%"
    if (
        f"at most {audit25_x} of unverified estimation pairs are identity mismatches"
        != lic25["licensed_sentence"]
    ):
        raise ClaimError("the composed E25 sentence is not the licensed one")
    if 100 * max(lic25["upper_new"], lic25["upper_pooled"]) > lic25["x_pct"]:
        raise ClaimError("the quoted E25 bound is below an upper bound")
    # E26: the identity audit of the forecast arrivals (Amendment 6).
    e26 = d["audit26"]
    lic26, n26 = e26["licences"], e26["class_counts"]
    if (
        lic26["report_to_amir_before_writing"]
        or lic26["wrong_share_at_least_5pct"]
        or not lic26["s1_all_readings_hold"]
    ):
        raise ClaimError(
            "the E26 licence state changed; rewrite the arrivals sentences"
        )
    if not lic26["previous_team_evidence_used"] or any(
        g["status"] != "passed" for g in e26["gates"].values()
    ):
        raise ClaimError(
            "an E26 gate did not pass; Appendix A describes evidence that was not used"
        )
    if e26["n_arrivals"] != get(rb, "e3/O1/contrasts/history_gain")["n"]:
        raise ClaimError("E26 is not a census of the benchmark arrivals")
    arr_count_sentence = (
        f"By fixed rules, {n26['WRONG']} of the {e26['n_arrivals']} forecast arrivals are classed as identity "
        f"mismatches; {n26['CONFIRMED']} are confirmed by independent evidence, {n26['NAME ONLY']} rest on the name "
        f"across a change of club, and {n26['UNRESOLVED']} are unresolved."
    )
    if arr_count_sentence != lic26["count_sentence"]:
        raise ClaimError("the composed E26 count sentence is not the licensed one")
    if (
        lic26["s1_sentence"]
        != "the three comparisons read the same without the arrivals classed wrong"
    ):
        raise ClaimError("the E26 S1 sentence is not the licensed one")
    # E14 survivorship
    e14a, e14b, e14c = get(sv, "e14a"), get(sv, "e14b"), get(sv, "e14c")
    wide = e14b["wide_3_games_60_minutes"]
    if e14b["licence"]["holds"] or e14b["licence"]["failing_contrasts"] != [
        "history_gain"
    ]:
        raise ClaimError("the E14b licence state changed")
    if not e14c["licence"]["holds"]:
        raise ClaimError("the E14c licence is not earned")
    tc = e14c["all_arrivals_1_plus"]["contrasts"]
    tl = e14c["all_arrivals_1_plus"]["ladder"]
    prof = e14a["profile"]
    # E15 skills
    carry = {row["component"]: row for row in d["carryover"]}
    ret = {
        row["component"]: float(row["retention"])
        for row in d["retention"]
        if row["subset_type"] == "pooled" and row["subset"] == "all"
    }
    robust, sensitive = robust_licences(d)
    if any(lic["earned"] for lic in get(sk, "e15b/licences")):
        raise ClaimError(
            "an E15b 'skill that travels' licence was earned; the paper says none was"
        )
    claimed = [
        (h, low) for h in ("tov", "fg3_pct", "ft_pct") for low in ("pts", "ast", "fta")
    ]
    if not set(claimed) <= set(robust) or ("tov", "pts") not in robust:
        raise ClaimError(
            "a skills sentence names a comparison that is not estimator-robust"
        )
    if any(h in ("oreb", "dreb", "stl", "blk") for h, _ in robust):
        raise ClaimError(
            "a rebound/steal/block comparison became robust; rewrite the skills paragraph"
        )
    order = sorted(carry, key=lambda k: -float(carry[k]["r_disattenuated"]))
    readable = [k for k in order if float(carry[k]["reliability"]) >= 0.40]
    if readable[:2] != ["fg3a", "oreb"] or readable[-2:] != ["pts", "stl"]:
        raise ClaimError(f"carry-over order changed: {readable}")
    if float(carry["fg3_pct"]["reliability"]) >= 0.40:
        raise ClaimError(
            "3-point percentage is now readable; rewrite the skills paragraph"
        )
    cr = lambda k: f"{float(carry[k]['r_disattenuated']):.2f}"  # noqa: E731
    # shortlist quality
    rq = {
        arm: pv[f"realised:10:{arm}"]["point"]
        for arm in (
            "history_only",
            "scheduled_history",
            "source_ridge_10",
            "source_ridge_10_scheduled",
        )
    }
    rq_band = max(
        max(abs(x) for x in v["ci95"])
        for k, v in pv.items()
        if k.startswith("realised_diff:10:")
    )
    if any(
        not v["ci95"][0] <= 0 <= v["ci95"][1]
        for k, v in pv.items()
        if k.startswith("realised_diff:10:")
    ):
        raise ClaimError("a top-10 difference became detectable")
    # vignettes
    vg = d["vignettes"]
    closer = sum(
        abs(float(v["forecast_source_ridge_10"]) - float(v["actual_eff36"]))
        < abs(float(v["forecast_history_only"]) - float(v["actual_eff36"]))
        for v in vg
    )
    arms = (
        "forecast_history_only",
        "forecast_scheduled_history",
        "forecast_source_ridge_10",
    )
    beat_all = all(
        float(v["actual_eff36"]) > max(float(v[a]) for a in arms) for v in vg
    )
    words = {0: "none", 1: "one", 2: "two", 3: "all three"}
    closer_text = f"the league-aware forecast was closer than history alone in {words.get(closer, str(closer))} of the {words.get(len(vg), str(len(vg))).replace('all ', '')}"
    # a table printed to one decimal can show an outcome level with a forecast it exceeds
    ties = sum(
        round(float(v["actual_eff36"]), 1) <= max(round(float(v[a]), 1) for a in arms)
        for v in vg
    )
    tie_note = (
        f" ({words[ties].replace('all ', '')} of them by less than the rounding of the table)"
        if ties
        else ""
    )
    vignette_sentence = (
        f"All three outperformed every forecast{tie_note}, and {closer_text}."
        if beat_all and len(vg) == 3
        else f"In this box {closer_text}."
    )
    f = {
        "hook_short": hook_short,
        "e9_seasons": e9_seasons(d),
        "hook_long": hook_long,
        "n_anchor": f"{get(r, 'n_targets')}",
        "n_el": f"{get(rb, 'e4/anchor/difference_test_history_gain/n_el')}",
        "n_ec": f"{get(rb, 'e4/anchor/difference_test_history_gain/n_ec')}",
        "mae_hist": num(m("history_only")),
        "mae_hist_z": num(m("scheduled_history")),
        "mae_off10": num(m("source_ridge_10")),
        "mae_off10_z": num(m("source_ridge_10_scheduled")),
        "mae_cell10": num(m("cell_slope_10")),
        "hist_gain": num(hist["difference"]),
        "hist_gain_pct": pct(hist["difference"] / m("history_only")),
        "hist_gain_lo": num(hist["ci95"][0]),
        "hist_gain_hi": num(hist["ci95"][1]),
        "d_dest": num(dest["difference"]),
        "dest_lo": num(dest["ci95"][0]),
        "dest_hi": num(dest["ci95"][1]),
        "d_inc10": num(inc10["difference"]),
        "inc10_lo": num(inc10["ci95"][0]),
        "inc10_hi": num(inc10["ci95"][1]),
        "ch": num(h2h["difference"], sign=True),
        "ch_lo": num(h2h["ci95"][0]),
        "ch_hi": num(h2h["ci95"][1]),
        "ch_mde": num(h2h["detectable_80"]),
        "rel_eff": f"{get(rb, 'e6/outcomes/O1/spearman_brown_reliability'):.2f}",
        "floor_eff": f"{floor:.3f}",
        "floor_direct": num(direct_floor),
        "av_hz_direct": pct(hist["difference"] / (m("history_only") - direct_floor)),
        "reducible_hist": num(m("history_only") - floor),
        "recipe_hist_min": num(min(rec_hist)),
        "recipe_hist_max": num(max(rec_hist)),
        "holm_min": f"{min(get(r, 'e2_family/player_club_season/holm_adjusted_p').values()):.2f}",
        "el_hist_gain": num(e4("euroleague", "history_gain")["difference"]),
        "el_hist_lo": num(
            e4("euroleague", "history_gain")["player_club_season"]["ci95"][0]
        ),
        "el_hist_hi": num(
            e4("euroleague", "history_gain")["player_club_season"]["ci95"][1]
        ),
        "dest_diff_p": f"{get(rb, 'e4/anchor/difference_test_offsets10/player_club_season/p_two_sided'):.2f}",
        "dest_diff_hist_p": f"{get(rb, 'e4/anchor/difference_test_history_gain/player_club_season/p_two_sided'):.2f}",
        "gmsc_dest": num(get(rb, "e3/O3/contrasts/destination_increment/difference")),
        "gmsc_dest_lo": num(gm["ci95"][0]),
        "gmsc_dest_hi": num(gm["ci95"][1]),
        "d1_min": pct(min(d1), 0),
        "d1_max": pct(max(d1), 0),
        "d1_bound": pct(
            get(dc, "e7/reliability/normal_model_true_rate_vs_full_season_concordance"),
            0,
        ),
        "d2_flip_pct": pct(
            pv["flip_share:source_ridge_10__source_ridge_10_scheduled"]["point"]
        ),
        "d2_right_pct": pct(right["point"]),
        "d2_right_lo": pct(right["ci95"][0]),
        "d2_right_hi": pct(right["ci95"][1]),
        "d2h_flip_pct": pct(pv["flip_share:history_only__scheduled_history"]["point"]),
        "d2h_right_pct": pct(righth["point"]),
        "e8_cov80": pct(float(pooled("0.8")["coverage"])),
        "e8_n": f"{int(float(pooled('0.8')['n'])):,}",
        "e8_cov95": pct(float(pooled("0.95")["coverage"])),
        "e8_hw80": f"{mean_hw('0.80'):.1f}",
        "e8_hw95": f"{mean_hw('0.95'):.1f}",
        "e8_cov80_min": pct(min(seasons80)),
        "e8_cov80_max": pct(max(seasons80)),
        "tiers_close": ", ".join(close[:-1]) + f" and {close[-1]}"
        if len(close) > 1
        else "".join(close),
        "n_tiers": f"{len({row['tier'] for row in tiers})}",
        "games_mean": f"{2 * get(dc, 'e7/reliability/mean_games_per_half'):.0f}",
        "acb_rows": f"{get(d['freeze'], 'rows_with_disputed_acb_fields')}",
        # E17
        "S_pct": pct(hh["lambda_10"]["recovered_share"]["point"], 0),
        "S_lo_pct": pct(hh["lambda_10"]["recovered_share"]["ci95_percentile"][0], 0),
        "S_hi_pct": pct(hh["lambda_10"]["recovered_share"]["ci95_percentile"][1], 0),
        "S1_pct": pct(hh["lambda_1"]["recovered_share"]["point"], 0),
        "S100_pct": pct(hh["lambda_100"]["recovered_share"]["point"], 0),
        "av_hz": pct(red["scheduled_history"]),
        "av_off": pct(red["source_ridge_10"]),
        "av_left": pct(1 - red["source_ridge_10"], 0),
        "margin_eff": num(top["margin_2pct_eff36"]),
        "margin_share": pct(top["margin_share_of_history_gain_r1"], 0),
        "max_upper_eff": num(top["upper_bound_eff36"]),
        "max_upper_share": pct(top["upper_share_of_history_gain_r1"]),
        "mw_hist": num(mwc("history_only__scheduled_history")["difference"]),
        "mw_hist_lo": num(mwc("history_only__scheduled_history")["ci95"][0]),
        "mw_hist_hi": num(mwc("history_only__scheduled_history")["ci95"][1]),
        "mw_ch": num(
            mwc("scheduled_history__source_ridge_10")["difference"], sign=True
        ),
        "mw_ch_lo": num(mwc("scheduled_history__source_ridge_10")["ci95"][0]),
        "mw_ch_hi": num(mwc("scheduled_history__source_ridge_10")["ci95"][1]),
        "mw_inc": num(mwc("source_ridge_10__source_ridge_10_scheduled")["difference"]),
        "mw_inc_lo": num(mwc("source_ridge_10__source_ridge_10_scheduled")["ci95"][0]),
        "mw_inc_hi": num(mwc("source_ridge_10__source_ridge_10_scheduled")["ci95"][1]),
        # E10
        "e10_sentence": get(am, "e10/licence/sentence"),
        "x_d1_hist": pct(xd("d1", "history_only")["point"]),
        "x_d1_off": pct(xd("d1", "source_ridge_10")["point"]),
        "x_gain": pp(x_gain["point"], 2, sign=False),
        "x_gain_lo": pp(x_gain["ci95"][0], 2, sign=False),
        "x_gain_hi": pp(x_gain["ci95"][1], 2, sign=False),
        "x_pairs": f"{x_gain['pairs']:,}",
        "s_gain": pp(s_gain["point"], 2),
        "s_gain_lo": pp(s_gain["ci95"][0], 2, sign=False),
        "s_gain_hi": pp(s_gain["ci95"][1], 2, sign=False),
        "s_pairs": f"{s_gain['pairs']:,}",
        "x_flip": pct(x_flip["point"]),
        "x_right": pct(x_right["point"]),
        "x_right_lo": pct(x_right["ci95"][0]),
        "x_right_hi": pct(x_right["ci95"][1]),
        # E11
        "e11_acb": league(e11["spain-acb"]["sentence"]),
        "e11_ita": league(e11["italy-lba"]["sentence"]),
        "acb_bias_abs": num(-f11("spain-acb", "signed_error_history_only"), 2),
        "ita_bias_abs": num(-f11("italy-lba", "signed_error_history_only"), 2),
        "acb_aware": num(f11("spain-acb", "signed_error_source_ridge_10"), 2),
        "acb_aware_lo": num(f11("spain-acb", "ci95_low_source_ridge_10"), 2),
        "acb_aware_hi": num(f11("spain-acb", "ci95_high_source_ridge_10"), 2),
        "ita_aware": num(f11("italy-lba", "signed_error_source_ridge_10"), 2),
        "ita_aware_lo": num(f11("italy-lba", "ci95_low_source_ridge_10"), 2),
        "ita_aware_hi": num(f11("italy-lba", "ci95_high_source_ridge_10"), 2),
        "n_other_leagues": f"{len(others)}",
        "other_holm_min": f"{min(others):.3f}",
        # E12
        # Composed from the number so the paper-number manifest can trace it; a
        # test requires it to equal the registered sentence word for word. The
        # template follows it with a clarification: the flag is determined by
        # rate and history, so the coefficient is a step at x = h.
        "e12_sentence": (
            "Holding his domestic rate and history fixed, a player signed after a "
            "season above his own history is forecast "
            f"{num(-e12['beta_a'], 2)} EFF/36 lower."
        ),
        "beta_a": num(e12["beta_a"], 2),
        "beta_a_abs": num(-e12["beta_a"], 1),
        "beta_a_lo": num(e12["ci95"][0], 2),
        "beta_a_hi": num(e12["ci95"][1], 2),
        "beta_refits": f"{len(refits)}",
        "beta_refit_lo": num(min(refits), 2),
        "beta_refit_hi": num(max(refits), 2),
        # shortlist
        "rq_hist": f"{rq['history_only']:.2f}",
        "rq_hz": f"{rq['scheduled_history']:.2f}",
        "rq_off": f"{rq['source_ridge_10']:.2f}",
        "rq_offz": f"{rq['source_ridge_10_scheduled']:.2f}",
        "rq_band": f"{rq_band:.2f}",
        # E16
        "gbm_features": f"{get(fx, 'n_features_primary')}",
        "mae_gbm": num(get(fx, "metrics/gbm/mae")),
        "gbm_diff": num(prim["difference"], sign=True),
        "gbm_diff_lo": num(prim["player_club_season"]["ci95"][0]),
        "gbm_diff_hi": num(prim["player_club_season"]["ci95"][1]),
        "av_gbm": pct(fred["gbm"]["share_of_reducible_removed"]),
        "flex_primary": get(fx, "licensed/primary"),
        "club_inc": num(fc["ridge_club_increment"]["difference"], sign=True),
        "club_inc_lo": num(fc["ridge_club_increment"]["player_club_season"]["ci95"][0]),
        "club_inc_hi": num(fc["ridge_club_increment"]["player_club_season"]["ci95"][1]),
        "gbm_z": num(fc["gbm_translation_increment"]["difference"]),
        "gbm_z_lo": num(
            fc["gbm_translation_increment"]["player_club_season"]["ci95"][0]
        ),
        "gbm_z_hi": num(
            fc["gbm_translation_increment"]["player_club_season"]["ci95"][1]
        ),
        "ridge_z_hi": num(
            fc["ridge_translation_increment"]["player_club_season"]["ci95"][1]
        ),
        "gbm_z_upper": f"{fc['gbm_translation_increment']['player_club_season']['upper_pct_of_parent_mae']:.2f}%",
        "ridge_z_upper": f"{fc['ridge_translation_increment']['player_club_season']['upper_pct_of_parent_mae']:.2f}%",
        # E13
        "audit_n": f"{e13['n']}",
        "audit_frame": f"{get(au, 'frame_pairs'):,}",
        "audit_wrong": f"{e13['final_counts']['WRONG']}",
        "audit_wrong_pct": pct(e13["wrong_share"]),
        "audit_lo": pct(e13["wrong_wilson95"][0]),
        "audit_hi": pct(e13["wrong_wilson95"][1]),
        # E25
        "audit25_n": f"{e25['new']['n']}",
        "audit25_wrong": f"{e25['new']['wrong']}",
        "audit25_x": audit25_x,
        # E26
        "arr_count_sentence": arr_count_sentence,
        "arr_s1_sentence": lic26["s1_sentence"][0].upper() + lic26["s1_sentence"][1:],
        # E14
        "n_short": f"{e14a['n_short_1_to_7']}",
        "short_cont_rate": num(prof["short_1_to_7"]["destination_eff36"]["median"], 1),
        "anchor_cont_rate": num(
            prof["anchor_8_plus"]["destination_eff36"]["median"], 1
        ),
        "short_share": pct(e14a["short_share_of_all_arrivals"]),
        "n_all": f"{e14b['all_arrivals_1_plus']['n']}",
        "short_src_mpg": f"{prof['short_1_to_7']['source_min_per_game']['median']:.1f}",
        "anchor_src_mpg": f"{prof['anchor_8_plus']['source_min_per_game']['median']:.1f}",
        "short_dest_games": f"{prof['short_1_to_7']['destination_games']['median']:.0f}",
        "n_wide": f"{wide['n']}",
        "w_mw_hist": num(
            wide["minutes_weighted"]["contrasts"]["history_gain"]["difference"]
        ),
        "w_mw_hist_lo": num(
            wide["minutes_weighted"]["contrasts"]["history_gain"]["player_club_season"][
                "ci95"
            ][0]
        ),
        "w_mw_hist_hi": num(
            wide["minutes_weighted"]["contrasts"]["history_gain"]["player_club_season"][
                "ci95"
            ][1]
        ),
        "t_sentence": e14c["licence"]["sentence"],
        "t_hist": num(tl["history_only"]["mae"]),
        "t_off": num(tl["source_ridge_10"]["mae"]),
        "t_gain": num(tc["offsets10_gain_over_history"]["difference"], 4),
        "t_gain_lo": num(
            tc["offsets10_gain_over_history"]["player_club_season"]["ci95"][0], 4
        ),
        "t_gain_hi": num(
            tc["offsets10_gain_over_history"]["player_club_season"]["ci95"][1], 4
        ),
        "t_dest": num(tc["destination_gain_over_history"]["difference"], 4),
        # E15
        "c_fg3a": cr("fg3a"),
        "c_oreb": cr("oreb"),
        "c_pts": cr("pts"),
        "c_stl": cr("stl"),
        "rel_fg3pct": f"{float(carry['fg3_pct']['reliability']):.2f}",
        "ret_tov": f"{ret['tov']:.3f}",
        "ret_ftpct": f"{ret['ft_pct']:.3f}",
        "ret_fg3pct": f"{ret['fg3_pct']:.3f}",
        "ret_pts": f"{ret['pts']:.3f}",
        "ret_ast": f"{ret['ast']:.3f}",
        "ret_fta": f"{ret['fta']:.3f}",
        "n_robust": f"{len(robust)}",
        "n_lic": f"{len(robust) + len(sensitive)}",
        "n_sensitive": f"{len(sensitive)}",
        "vignette_sentence": vignette_sentence,
    }
    for lam, key in ((1, "ch1"), (100, "ch100")):
        c = hh[f"lambda_{lam}"]["c_h"]
        f[key] = num(c["difference"], sign=True)
        f[key + "_lo"] = num(c["ci95"][0])
        f[key + "_hi"] = num(c["ci95"][1])
        if not c["ci95"][0] <= 0 <= c["ci95"][1]:
            raise ClaimError(f"'every interval spans zero' is false at lambda {lam}")
    if not h2h["ci95"][0] <= 0 <= h2h["ci95"][1]:
        raise ClaimError("'every interval spans zero' is false at lambda 10")
    best = max(red.values())
    if red["source_ridge_10"] != best or any(
        fred[k]["share_of_reducible_removed"] > best for k in fred
    ):
        raise ClaimError("'no richer forecast removes more' is false")
    margin = top["margin_2pct_eff36"]
    for name, ci in (
        ("translation's increment", inc10["ci95"]),
        ("the head-to-head", h2h["ci95"]),
    ):
        if not (-margin < ci[0] and ci[1] < margin):
            raise ClaimError(f"'inside the pre-registered margin' is false for {name}")
    ridge30 = get(fx, "metrics/ridge/mae")
    if min(ridge30, get(fx, "metrics/gbm/mae")) < m("source_ridge_10"):
        raise ClaimError("'richer 30-feature models do no better' is false")
    f["mae_ridge30"] = num(ridge30)
    f["n_train"] = f"{get(dc, 'e9/training_forecasts'):,}"
    f["n_factor_pairs"] = f"{sum(int(row['factor_pairs']) for row in d['counts']):,}"
    f.update(facts_v3(d))
    for k, v in META.items():
        f[f"meta:{k}"] = v
    return f


# ------------------------------------------------- facts: Amendments 3 and 4
A3_H, A3_D, A3_O = "history_only", "history_destination_slope", "source_ridge_10"


def short_league(code: str) -> str:
    """'Spain' from 'Spain (ACB)'; names without a bracket stay whole."""
    return LEAGUE_NAMES[code].split(" (")[0]


def join_names(names: list) -> str:
    names = list(names)
    if not names:
        raise ClaimError("an empty list of leagues in a sentence")
    return names[0] if len(names) == 1 else ", ".join(names[:-1]) + f" and {names[-1]}"


def excludes_zero(low: float, high: float) -> bool:
    return low > 0 or high < 0


def facts_v3(d: dict) -> dict:  # noqa: C901 -- one guarded fact per placeholder
    """Placeholders for E18-E24. Every sentence in the template that depends on a
    verdict is guarded here: if the committed numbers stop licensing it, ClaimError."""
    a3, a4 = d["amend3"], d["amend4"]
    e18, e24 = get(a3, "e18"), get(a4, "e24")
    lvl = {(r["arm"], r["scope"]): r for r in e18["level"]}
    lvl4 = {(r["arm"], r["scope"]): r for r in e24["level"]}
    off = lvl[(A3_O, "all")]
    if not off["ci95_high"] < 0:
        raise ClaimError("'the league-aware forecast runs low' is not licensed")
    seasons = sorted(
        int(s.split(":")[1])
        for arm, s in lvl
        if arm == A3_O and s.startswith("season:")
    )
    last = seasons[-1]
    by_season = {s: lvl[(A3_O, f"season:{s}")]["mean_signed_error"] for s in seasons}
    if min(by_season, key=by_season.get) != last:
        raise ClaimError("'the shortfall is largest in the latest season' is false")
    cover = get(a3, "e22/by_season/0.80")
    cov_last = cover[str(last)]["coverage"]
    if cov_last != min(v["coverage"] for v in cover.values()):
        raise ClaimError("'coverage is lowest in the latest season' is false")
    registered_min = min(
        float(row["coverage"])
        for row in d["conformal"]
        if row["arm"] == A3_O
        and row["level"] == "0.8"
        and row["scope"].startswith("season ")
    )
    if abs(cov_last - registered_min) > 1e-12:
        raise ClaimError("E22 season coverage differs from the registered E8 table")
    shared = [lvl[(A3_H, "all")], lvl4[(A3_D, "all")], off]
    if not all(r["ci95_high"] < 0 for r in shared):
        raise ClaimError("'the other forecasts share the shortfall' is false")
    if not (
        lvl[(A3_H, "destination:euroleague")]["ci95_low"] > 0
        and lvl[(A3_H, "destination:eurocup")]["ci95_high"] < 0
    ):
        raise ClaimError(
            "'a forecast blind to both leagues overrates EuroLeague and underrates EuroCup arrivals' is false"
        )
    drift = {(r["competition"], int(r["season"])): r for r in e18["drift"]}
    ec = drift[("eurocup", last)]
    if not (ec["arrivals_minus_earlier"] > 0 and ec["all_players_minus_earlier"] > 0):
        raise ClaimError(
            "the EuroCup drift sentence needs both series above earlier seasons"
        )

    # league biases: E24 (destination-aware comparator), E18b (history only)
    l18 = {r["source_league"]: r for r in e18["leagues"]}
    l24 = {r["source_league"]: r for r in e24["leagues"]}
    licensed = [r for r in e24["leagues"] if r["licence"] == "licensed"]
    under = sorted(
        (r for r in licensed if r[f"rebased_{A3_D}"] < 0),
        key=lambda r: r[f"rebased_{A3_D}"],
    )
    over = sorted(
        (r for r in licensed if r[f"rebased_{A3_D}"] > 0),
        key=lambda r: -r[f"rebased_{A3_D}"],
    )
    if not under or not over:
        raise ClaimError(
            "the league-bias sentences name underrated and overrated leagues"
        )
    by = lambda rows: join_names(  # noqa: E731
        [
            f"{short_league(r['source_league'])} by {num(abs(r[f'rebased_{A3_D}']), 2)}"
            for r in rows
        ]
    )
    h_only = [r["source_league"] for r in e18["leagues"] if r["licence"] == "licensed"]
    if len(h_only) != 1:
        raise ClaimError(
            "'only one league passes with the history-only forecast' is false"
        )
    primary, secondary = get(e24, "contrasts/primary"), get(e24, "contrasts/secondary")
    if not primary["licensed"] or not get(e18, "spread_contrast/licensed"):
        raise ClaimError(
            "'the league table flattens the league pattern' is not licensed"
        )
    if secondary["licensed"] or not secondary["ci95"][0] <= 0 <= secondary["ci95"][1]:
        raise ClaimError(
            "'the destination alone does not flatten the pattern' is false"
        )
    left = [
        code
        for code, r in l18.items()
        if excludes_zero(r[f"rebased_ci95_low_{A3_O}"], r[f"rebased_ci95_high_{A3_O}"])
    ]
    if len(left) != 1:
        raise ClaimError(
            "'one league stays misjudged by the league-aware forecast' is false"
        )
    rest = l18[left[0]]
    if not rest[f"rebased_{A3_O}"] < 0:
        raise ClaimError(
            "'stays underrated' is false for the league the table does not clear"
        )
    fra = l24["france-pro-a"]
    if fra["licence"] == "licensed" or not excludes_zero(
        fra[f"rebased_ci95_low_{A3_D}"], fra[f"rebased_ci95_high_{A3_D}"]
    ):
        raise ClaimError("the France clause no longer describes the E24 table")

    # E19, E20, E21, E22
    e19 = get(a3, "e19/summary")
    if e19["tier3_higher"] != e19["comparisons"]:
        raise ClaimError("'in every yearly refit' is false")
    eq = {
        (r["destination"], r["source_league"]): float(r["acb16_equivalent_eff36"])
        for r in d["exchange"]
    }
    gap_el = eq[("euroleague", "germany-bbl")] - 16.0
    gap_ec = eq[("eurocup", "germany-bbl")] - 16.0
    bins = {
        r["bin"]: r
        for r in get(a3, "e20/bins")
        if r["arm"] == A3_O and r["pair_type"] == "all"
    }
    shares = [bins[k]["share_correct"] for k in sorted(bins)]
    if shares != sorted(shares):
        raise ClaimError("'accuracy rises with the forecast gap' is false")
    trust = get(a3, "e20/licence/trust")
    if not (trust["0.60"]["licensed"] and trust["0.70"]["licensed"]):
        raise ClaimError("the gap thresholds are not licensed")
    fc = {
        row["league_src"]: float(row["forecast"])
        for row in d["tiers"]
        if row["league_dest"] == "euroleague"
    }
    league_gap = fc["spain-acb"] - fc["germany-bbl"]
    # The text places this gap on the border between the 1-2 and 2-3 bins and
    # reads it as "about two times in three".
    if abs(league_gap - 2.0) >= 0.25:
        raise ClaimError("the Spain-Germany forecast gap is not about 2.0")
    if not bins[1]["share_correct"] <= 2 / 3 <= bins[2]["share_correct"]:
        raise ClaimError("'about two times in three' is not between the two bins")
    blind = {
        r["bin"]: r
        for r in get(a3, "e20/bins")
        if r["arm"] == A3_H and r["pair_type"] == "all"
    }
    top = max(bins)
    if not bins[top]["pairs"] > blind[top]["pairs"]:
        raise ClaimError(
            "'the league-aware forecast produces more large gaps' is false"
        )
    if (
        max(abs(bins[k]["share_correct"] - blind[k]["share_correct"]) for k in bins)
        > 0.02
    ):
        raise ClaimError("'about as reliable at each gap size' is false")
    flips = {r["pair_type"]: r for r in get(a3, "e21/flips")}
    if not get(a3, "e21/licence/licensed"):
        raise ClaimError("the league-table flip sentence is not licensed")
    e22 = get(a3, "e22/licence")
    cov80 = [r for r in get(a3, "e22/leagues") if abs(r["level"] - 0.80) < 1e-9]
    if e22["leagues_off_nominal"]:
        raise ClaimError("a league's band coverage is off nominal: name it in the text")

    # E23
    a, b = get(a3, "e23/a"), get(a3, "e23/b")
    m1 = a["M1"]
    if a["licence"]["licensed"]:
        raise ClaimError("E23 now licenses 'the discount grows': rewrite the paragraph")
    fades = m1["jump_ci95"][0] > 0 and all(x > 0 for x in m1["walk_forward_jump"])
    if not fades:
        raise ClaimError("'the discount fades as the jump grows' is not supported")
    for block in a["walk_forward_contrasts"].values():
        if not block["ci95"][0] <= 0 <= block["ci95"][1]:
            raise ClaimError("'neither variant forecasts detectably better' is false")
    if not b["licence"]["licensed"]:
        raise ClaimError(
            "the 'signings follow above-average seasons' sentence is not licensed"
        )
    median = a["jump_among_flagged"]["median"]
    if not m1["flag"] + m1["jump"] * median < 0:
        raise ClaimError("'a discount at the median jump' is false")
    if get(a3, "e20/licence/coin_flip_below_1/licensed"):
        raise ClaimError("gaps below 1 are now a coin flip: rewrite the gap paragraph")
    diff = b["difference_arrivals_minus_population"]
    return {
        # E18a level
        "lvl_off_abs": num(abs(off["mean_signed_error"]), 2),
        "lvl_off_lo": num(off["ci95_low"], 2),
        "lvl_off_hi": num(off["ci95_high"], 2),
        "lvl_off_ec": num(lvl[(A3_O, "destination:eurocup")]["mean_signed_error"], 2),
        "lvl_off_el": num(
            lvl[(A3_O, "destination:euroleague")]["mean_signed_error"], 2
        ),
        "lvl_last": num(by_season[last], 2),
        "lvl_last_season": season_label(last),
        "cov_last": pct(cov_last),
        "drift_ec_arr": num(ec["arrivals_minus_earlier"], 2),
        "drift_ec_all": num(ec["all_players_minus_earlier"], 2),
        "lvl_d_abs": num(abs(lvl4[(A3_D, "all")]["mean_signed_error"]), 2),
        # E24 / E18b league biases
        "under_names": join_names([short_league(r["source_league"]) for r in under]),
        "over_names": join_names([short_league(r["source_league"]) for r in over]),
        "under_by": by(under),
        "under_top_by": by(under[:1]),
        "over_by": by(over),
        "h_only_name": short_league(h_only[0]),
        "spread_h": num(get(e18, f"spread/{A3_H}/point"), 2),
        "spread_d": num(get(e24, f"spread/{A3_D}/point"), 2),
        "spread_o": num(get(e24, f"spread/{A3_O}/point"), 2),
        "spread_o_lo": num(get(e24, f"spread/{A3_O}/ci95")[0], 2),
        "spread_o_hi": num(get(e24, f"spread/{A3_O}/ci95")[1], 2),
        "fig2_notes": fig2_notes(e24),
        "spread_gain": num(primary["point"], 2),
        "spread_gain_lo": num(primary["ci95"][0], 2),
        "spread_gain_hi": num(primary["ci95"][1], 2),
        "spread_dest": num(secondary["point"], 2),
        "spread_dest_lo": num(secondary["ci95"][0], 2),
        "spread_dest_hi": num(secondary["ci95"][1], 2),
        "e24_primary": primary["sentence"],
        "left_name": short_league(left[0]),
        "left_val": num(rest[f"rebased_{A3_O}"], 2),
        "left_lo": num(rest[f"rebased_ci95_low_{A3_O}"], 2),
        "left_hi": num(rest[f"rebased_ci95_high_{A3_O}"], 2),
        "fra_d": num(fra[f"rebased_{A3_D}"], 2),
        "fra_holm": f"{fra[f'rebased_p_holm_{A3_D}']:.2f}",
        "n_fra": f"{fra['arrivals']}",
        # E19
        "e19_sentence": e19["sentence"],
        "e19_move": (
            "From one summer to the next a league's equivalent moved by a median of "
            f"{num(e19['median_consecutive_change'], 2)} EFF/36 "
            f"(at most {num(e19['max_consecutive_change'], 2)})."
        ),
        "gap_bbl_el": num(gap_el, 1),
        "gap_bbl_ec": num(gap_ec, 1),
        "bbl22_acb": num(22.0 - gap_el, 1),
        # E20
        "gap01": pct(bins[0]["share_correct"]),
        "gap12": pct(bins[1]["share_correct"]),
        "gap23": pct(bins[2]["share_correct"]),
        "gap6": pct(bins[top]["share_correct"]),
        "league_gap_fc": num(league_gap, 1),
        "gap_coin": get(a3, "e20/licence/coin_flip_below_1/sentence"),
        "trust60": trust["0.60"]["sentence"],
        "trust70": trust["0.70"]["sentence"],
        "gap_pairs_off": f"{bins[top]['pairs']:,}",
        "gap_pairs_hist": f"{blind[top]['pairs']:,}",
        # E21
        "e21_sentence": (
            f"the league table changes {pct(flips['cross']['flip_share'])} of "
            "cross-league comparisons and is right on "
            f"{pct(flips['cross']['right_share'])} of them"
        ),
        "lt_right_lo": pct(flips["cross"]["right_share_ci95_low"]),
        "lt_right_hi": pct(flips["cross"]["right_share_ci95_high"]),
        # E22
        "e22_range": (
            f"By source league, the {pct(cov80[0]['level'], 0)} bands contained "
            f"between {pct(min(r['coverage'] for r in cov80))} and "
            f"{pct(max(r['coverage'] for r in cov80))} of arrivals."
        ),
        "e22_sentence": (
            "No league's coverage was distinguishable from "
            f"{pct(cov80[0]['level'], 0)} at these sample sizes "
            f"(n from {min(r['n'] for r in cov80)} to {max(r['n'] for r in cov80)})"
        ),
        # E23
        "e23_sentence": a["licence"]["sentence"],
        "jump_coef": num(m1["jump"], 2, sign=True),
        "jump_lo": num(m1["jump_ci95"][0], 2),
        "jump_hi": num(m1["jump_ci95"][1], 2),
        "jump_refits": f"{len(m1['walk_forward_jump'])}",
        "jump_median": num(median, 1),
        "jump_net_median": num(abs(m1["flag"] + m1["jump"] * median), 1),
        "e23b_sentence": (
            f"{pct(b['arrivals']['share'], 0)} of signings followed an above-average "
            f"season, against {pct(b['population']['share'], 0)} of all comparable "
            "domestic player-seasons."
        ),
        # Amendment 29, rule 2: the base of both shares, said once, in Appendix L
        "e23b_base": (
            "Both shares are counted among players with an earlier season on record: "
            f"{b['arrivals']['flagged']:,} of the {b['arrivals']['with_history']:,} training arrivals who have one, and "
            f"{pct(b['population']['share'], 0)} of the {b['population']['player_seasons_with_history']:,} domestic "
            "player-seasons that have one."
        ),
        "share_diff": num(100 * diff["point"], 1),
        "share_diff_lo": num(100 * diff["ci95"][0], 1),
        "share_diff_hi": num(100 * diff["ci95"][1], 1),
    }


# ---------------------------------------------------------------- tables
def md_table(header, rows) -> str:
    out = [
        "| " + " | ".join(header) + " |",
        "|" + "|".join(["---"] * len(header)) + "|",
    ]
    out += ["| " + " | ".join(row) + " |" for row in rows]
    return "\n".join(out)


LADDER_MAIN = (
    "History only",
    "+ destination (intercept and slope)",
    "+ one number per league, λ = 10 (primary)",
)


def table_ladder(d, full: bool = False) -> str:
    """Table 1 (main text): the three rows Figure 3 draws. ``full``: every row, as Table A24
    (Amendment 19, rule 11)."""
    r = d["recipes"]
    a = "results/A/R1"
    rows = []
    for label, left, right in (
        ("History only", "history_only", "scheduled_history"),
        (
            "+ destination (intercept and slope)",
            "history_destination_slope",
            "history_destination_slope_scheduled",
        ),
        (
            "+ one number per league, λ = 1",
            "source_ridge_1",
            "source_ridge_1_scheduled",
        ),
        (
            "+ one number per league, λ = 10 (primary)",
            "source_ridge_10",
            "source_ridge_10_scheduled",
        ),
        (
            "+ one number per league, λ = 100",
            "source_ridge_100",
            "source_ridge_100_scheduled",
        ),
        ("+ pair-specific slopes, λ = 10", "cell_slope_10", "cell_slope_10_scheduled"),
    ):
        c = get(r, f"{a}/ladder/{left}->{right}/player_club_season")
        rows.append(
            [
                label,
                num(get(r, f"{a}/metrics/{left}/mae")),
                num(get(r, f"{a}/metrics/{right}/mae")),
                f"{num(c['difference'], sign=True)} {interval(c['ci95'])}",
            ]
        )
    head = (
        "Table A24. The full ladder; Figure 3 draws the rows for history only, + destination and the primary "
        "league numbers (λ = 10). Forecast error"
        if full
        else "Table 1. Forecast error"
    )
    cap = (
        f"{head} (MAE, EFF/36) on the same {get(r, 'n_targets')} arrivals, without and with the "
        "translation feature. Gain = MAE without − MAE with; positive favours translation; 95% intervals clustered by "
        "player and destination club-season."
    )
    if not full:
        cap += " Table A24 has every row."
        rows = [row for row in rows if row[0] in LADDER_MAIN]
        if len(rows) != len(LADDER_MAIN):
            raise ClaimError("Table 1 lost a row")
    return (
        cap
        + "\n\n"
        + md_table(
            [
                "Forecast knows…",
                "MAE without",
                "MAE with",
                "Gain from translation [95% CI]",
            ],
            rows,
        )
    )


def e26_subset(a26: dict, subset: str) -> dict:
    """The three E26b comparisons on one subset, keyed by comparison, as cell() reads them."""
    out = {}
    for row in a26["comparisons"]:
        if row["subset"] == subset:
            out[row["comparison"]] = {
                "n": row["n"],
                "difference": row["difference"],
                "ci95": [row["ci_low"], row["ci_high"]],
                "holds": row["registered_reading_holds"],
            }
    if set(out) != {"history_gain", "e1_head_to_head", "offsets10_increment"}:
        raise ClaimError(f"E26 subset {subset} does not carry the three comparisons")
    return out


def table_checks(d) -> str:
    rb, am, sv = d["robust"], d["amend"], d["surv"]
    rows = []

    def add(label, n, gain, ch, inc):
        rows.append([label, f"{n}", cell(gain), cell(ch), cell(inc)])

    def check_sides(c, left, right):
        if c["left"] != left or not c["right"].startswith(right):
            raise ClaimError(f"contrast direction changed: {c['left']} -> {c['right']}")
        return c

    for o in ("O1", "O2", "O3", "O4"):
        c = lambda k: get(rb, f"e3/{o}/contrasts/{k}")  # noqa: E731
        label = "Main benchmark, EFF/36" if o == "O1" else OUTCOME_NAMES[o]
        add(
            label,
            c("history_gain")["n"],
            c("history_gain"),
            check_sides(c("e1_head_to_head"), "scheduled_history", "source_ridge_10"),
            c("offsets10_increment"),
        )
    for path, label in (
        ("e5/extended", "Seven seasons, 2019–2025"),
        ("e5b/with_age", "Age-aware forecasts"),
    ):
        c = lambda k: get(rb, f"{path}/contrasts/{k}")  # noqa: E731
        add(
            label,
            c("history_gain")["n"],
            c("history_gain"),
            check_sides(c("e1_head_to_head"), "scheduled_history", "source_ridge_10"),
            c("offsets10_increment"),
        )
    for dst, label in (
        ("euroleague", "EuroLeague arrivals only"),
        ("eurocup", "EuroCup arrivals only"),
    ):
        c = lambda k: get(rb, f"e4/anchor/{dst}/contrasts/{k}")  # noqa: E731
        ch = check_sides(c("e1_head_to_head"), "scheduled_history", "source_ridge_10")
        lo, hi = ch["player_club_season"]["ci95"]
        if not lo <= 0 <= hi:
            raise ClaimError(
                f"the {dst} head-to-head interval excludes zero; Appendix J's sentence needs new wording"
            )
        add(
            label,
            c("history_gain")["n"],
            c("history_gain"),
            ch,
            c("offsets10_increment"),
        )
    mw = get(am, "e17/minutes_weighted/contrasts")
    add(
        "Weighted by destination minutes",
        mw["history_only__scheduled_history"]["minutes_weighted"]["n"],
        mw["history_only__scheduled_history"]["minutes_weighted"],
        mw["scheduled_history__source_ridge_10"]["minutes_weighted"],
        mw["source_ridge_10__source_ridge_10_scheduled"]["minutes_weighted"],
    )
    wide = get(sv, "e14b/wide_3_games_60_minutes")
    for kind, label in (
        ("unweighted", "At least 3 games and 60 minutes"),
        ("minutes_weighted", "… weighted by destination minutes"),
    ):
        c = wide[kind]["contrasts"]
        add(
            label,
            wide["n"],
            c["history_gain"],
            check_sides(c["e1_head_to_head"], "scheduled_history", "source_ridge_10"),
            c["offsets10_increment"],
        )
    a26 = d["audit26"]
    if not a26["licences"]["s1_all_readings_hold"]:
        raise ClaimError(
            "the E26 S1 readings changed; Table A18's row needs new wording"
        )
    s1 = e26_subset(a26, "S1")
    add(
        "Without arrivals classed as identity mismatches",
        s1["history_gain"]["n"],
        s1["history_gain"],
        s1["e1_head_to_head"],
        s1["offsets10_increment"],
    )
    cap = (
        "Table A18. The same three comparisons on every check (95% intervals clustered by player and destination "
        "club-season). *Translation vs history*: translation's gain against a league-blind forecast. "
        "*League-aware vs history + translation*: positive means one number per league (λ = 10) without translation "
        "is more accurate. *Translation added*: what translation adds once the forecast knows both leagues."
    )
    return (
        cap
        + "\n\n"
        + md_table(
            [
                "Check",
                "n",
                "Translation vs history",
                "League-aware vs history + translation",
                "Translation added to league-aware",
            ],
            rows,
        )
    )


def equivalent_rows(d) -> list:
    """One row per source league, ordered by tier and equivalent."""
    by = {}
    for row in d["exchange"]:
        by.setdefault(row["source_league"], {})[row["destination"]] = row
    counts = {row["source_league"]: row for row in d["counts"]}
    order = sorted(
        by,
        key=lambda k: (
            int(by[k]["euroleague"]["e9_tier"]),
            float(by[k]["euroleague"]["acb16_equivalent_eff36"]),
        ),
    )
    rows = []
    for k in order:
        el, ec = by[k]["euroleague"], by[k]["eurocup"]
        if el["e9_tier"] != ec["e9_tier"]:
            raise ClaimError(f"{k}: tiers differ between competitions")

        def eq(row):
            if row["source_league"] == "spain-acb":
                return "16 (reference)"
            return f"{float(row['acb16_equivalent_eff36']):.1f} [{float(row['ci95_low']):.1f}, {float(row['ci95_high']):.1f}]"

        rows.append(
            [
                el["e9_tier"],
                LEAGUE_NAMES[k],
                eq(el),
                eq(ec),
                f"{float(el['e9_forecast_eff36']):.1f}",
                f"{float(ec['e9_forecast_eff36']):.1f}",
                counts[k]["e9_training"],
                counts[k]["factor_pairs"],
            ]
        )
    return rows


def amendment_20(d) -> bool:
    """Whether the wording of Amendment 20 is in force (a test may switch it off; no loaded file can)."""
    return bool(d.get("amendment_20", AMENDMENT_20))


def eq_table(d) -> str:
    """The label of the Equivalents table. The three rows of the old Table 1 are drawn by Figure 3
    and printed in Table A24, so the Equivalents table is the first table of the main text, unless
    the table of named pairs of the frozen-test section (Amendment 20, rule 1) stands before it."""
    return "Table 2" if named_pairs_printed(d) and d["e32_pairs"] else "Table 1"


def fig2_notes(e24: dict) -> str:
    """Two clauses for the caption of Figure 2, each checked against the committed E24 rows: a
    league whose league-aware interval still excludes zero, and a league whose bias under the
    forecast blind to the source league excludes zero before the Holm adjustment and not after."""
    rows = e24["leagues"]
    still = [
        r
        for r in rows
        if r[f"rebased_ci95_low_{A3_O}"] > 0 or r[f"rebased_ci95_high_{A3_O}"] < 0
    ]
    unadjusted = [
        r
        for r in rows
        if r["licence"] != "licensed"
        and (r[f"rebased_ci95_low_{A3_D}"] > 0 or r[f"rebased_ci95_high_{A3_D}"] < 0)
        and r[f"rebased_p_holm_{A3_D}"] >= 0.05
    ]
    text = ""
    if unadjusted:
        names = join_names([short_league(r["source_league"]) for r in unadjusted])
        text += (
            f"; for {names} the grey interval excludes zero only before that adjustment"
        )
    text += "."
    if still:
        names = join_names([short_league(r["source_league"]) for r in still])
        text += f" For {names} the league-aware interval still excludes zero."
    return text


def equivalents_order(d) -> list:
    """The league codes in the order of the Equivalents table and of Figure 1: by tier, then by
    the EuroLeague Equivalent."""
    rows = [r for r in d["exchange"] if r["destination"] == "euroleague"]
    rows.sort(key=lambda r: (int(r["e9_tier"]), float(r["acb16_equivalent_eff36"])))
    return [r["source_league"] for r in rows]


def table_equivalents(d) -> str:
    """The Equivalents table of the main text (``eq_table`` gives its label)."""
    cap = (
        f"{eq_table(d)}. European League Equivalents: the domestic EFF/36 that the league-aware forecast (no translation, "
        "fitted on every season through 2025) treats like a 16 in Spain's ACB when career history equals that "
        "rate, with 95% cluster-bootstrap intervals. *League number*: the league's term δ in the fitted equation, "
        "in forecast EFF/36 against the league average, with its interval. Leagues inside a tier are not "
        "distinguishable, and the order inside a tier is not a ranking. The equivalents are read off the registered "
        "model and are not themselves a registered estimand."
    )
    numbers = {LEAGUE_NAMES[k]: v for k, v in league_numbers(d).items()}
    return (
        cap
        + "\n\n"
        + md_table(
            [
                "Tier",
                "Source league",
                "League number",
                "Equivalent, EuroLeague",
                "Equivalent, EuroCup",
            ],
            [
                [row[0], row[1], numbers[row[1]], row[2], row[3]]
                for row in equivalent_rows(d)
            ],
        )
    )


def table_equivalents_support(d) -> str:
    """Table A20 (Appendix L): reference forecasts and the data behind the factors."""
    cap = (
        "Table A20. Reference forecasts and support. *Forecast*: the forecast continental EFF/36 for an arrival "
        "with domestic and career EFF/36 of 16. *Factor pairs*: same-season players behind the translation "
        "factors, which the league-aware forecast does not use."
    )
    return (
        cap
        + "\n\n"
        + md_table(
            [
                "Source league",
                "Forecast, EuroLeague",
                "Forecast, EuroCup",
                "Factor pairs",
            ],
            [[row[1], row[4], row[5], row[7]] for row in equivalent_rows(d)],
        )
    )


#: Appendix G: the player vignettes, an illustration only (rule fixed before any error was read).
VIGNETTE_BOX = """### G. Illustration: three 2025–26 arrivals

This box illustrates how the forecasts read for individual players; it is not evidence for them. The rule was fixed before any forecast error was read: for each tier of {{eq_table}}, take the 2025–26 EuroLeague arrival with the most continental minutes (ties broken by player name). Minutes are played after arrival, so the rule selects on playing time and therefore on success. {{vignette_sentence}} A single forecast can miss by about ±{{e8_hw80}} EFF/36 at 80% (Individual uncertainty), which is why one season of box scores says less than a scouting report about one player.

{{table:vignettes}}"""


def table_vignettes(d) -> str:
    rows = []
    for v in d["vignettes"]:
        if (v["season_src"], v["season_dest"]) != ("2024", "2025"):
            raise ClaimError("Table A8 caption names 2024-25 and 2025-26 seasons")
        hist_txt = f"{float(v['history_eff36']):.1f}" if v["history_eff36"] else "none"
        rows.append(
            [
                v["player"],
                f"{v['club_src']}, {LEAGUE_NAMES[v['league_src']]} → {v['club_dest']} (tier {v['tier']})",
                f"{float(v['eff36_src']):.1f} ({hist_txt}){' †' if v['above_own_history'] == 'True' else ''}",
                f"{float(v['forecast_history_only']):.1f}",
                f"{float(v['forecast_scheduled_history']):.1f}",
                f"{float(v['forecast_source_ridge_10']):.1f}",
                f"{float(v['actual_eff36']):.1f} ({v['games_dest']} games)",
            ]
        )
    cap = (
        "Table A8. Three 2025–26 EuroLeague arrivals, one per tier of {{eq_table}}, each the arrival with the most "
        "continental minutes in his tier. Domestic EFF/36 in 2024–25, with career EFF/36 in brackets "
        "(† = source season above his own history; none = no earlier season in the data). Forecasts are walk-forward, made before the season."
    )
    return (
        cap
        + "\n\n"
        + md_table(
            [
                "Player",
                "Move",
                "Domestic (career)",
                "History only",
                "+ translation",
                "League-aware",
                "Actual",
            ],
            rows,
        )
    )


# ---------------------------------------------------------------- P1
#: Amendment 8, "What the paper may say": the registered words of each read-out.
P1_WORDING = {
    (
        "S1",
        "above_zero",
    ): "on unseen 2026–27 forecasts the league-aware forecast was more accurate than history alone, by X EFF/36",
    (
        "S2",
        "above_zero",
    ): "once the destination was known, knowing the source league improved the 2026–27 forecasts by X EFF/36",
    ("S1", "includes_zero"): "not detectable at this n",
    ("S2", "includes_zero"): "not detectable at this n",
    (
        "S3",
        "below_zero",
    ): "the frozen forecasts ran X EFF/36 below what newcomers delivered",
    ("S3", "includes_zero"): "no level error was detectable at this n",
    (
        "S3",
        "above_zero",
    ): "the frozen forecasts ran X EFF/36 above what newcomers delivered",
    (
        "S4",
        "above_half",
    ): "on unseen 2026–27 forecasts the league-aware forecast ordered X% of cross-league pairs correctly",
    ("S4", "includes_half"): "not distinguishable from a coin flip at this n",
    ("S5", "includes_zero"): "not clearly above zero when weighted by playing time",
    ("P-b", "includes_zero"): "no difference detected at this n",
    # Amendment 18, rule 5: the three outcomes the earlier tables did not cover.
    # "X" is the estimate and "interval" its 95% interval; no other word changes.
    (
        "S1",
        "below_zero",
    ): "On unseen 2026–27 forecasts the league-aware forecast was less accurate than history alone (X EFF/36, interval): a failure of the league-aware forecast on 2026–27.",
    (
        "S2",
        "below_zero",
    ): "Once the destination was known, knowing the source league made the 2026–27 forecasts less accurate (X EFF/36, interval): a failure of the league-aware forecast on 2026–27.",
    (
        "S4",
        "below_half",
    ): "On unseen 2026–27 forecasts the league-aware forecast ordered X% of cross-league pairs correctly (interval), fewer than a coin flip would: a failure of its ordering on 2026–27.",
}
#: Amendment 18, rule 5: the read-outs with a registered failure sentence.
P1_RULE5 = {"S1": "below_zero", "S2": "below_zero", "S4": "below_half"}
#: Amendment 8's partial-season caveat, printed beside each of those sentences.
P1_CAVEAT = (
    "This read-out covers only newcomers who reached eight games early, over few games; "
    "it is repeated at the February re-score."
)
P1_SECONDARY = {
    "S1": "the league-aware forecast against history alone",
    "S2": "the league-aware forecast against the forecast that knows only the destination",
}
P1_ARM_NAMES = {
    "history_only": "history",
    "scheduled_history": "history plus translation",
    "source_ridge_10": "league-aware",
    "source_ridge_10_scheduled": "league-aware plus translation",
}
P1_GATE_NAMES = {
    "season": "the files hold another season",
    "freshness": "the files were not refreshed after the last counted game",
    "schedule_dates": "game dates could not be read",
    "boxscore_in_schedule": "a box score had no scheduled game",
    "completeness": "a scheduled game had no box score",
    "rounds": "a round of games was missing",
    "people_list": "the registration list could not be used",
}
#: What a score record must hold before a sentence is written from it.
P1_REQUIRED = {
    "scored": (
        "n_scored",
        "min_n",
        "all",
        "verdicts",
        "anchor",
        "mae",
        "secondary",
        "complete_source",
        "published_table_arm",
        "pre_read",
        "join",
        "february_only_descriptive",
        "postponed_games",
        "rule_5_sentences",
        "escalate_to_amir_before_writing",
    ),
    "not_adjudicable": (
        "n_scored",
        "min_n",
        "descriptive",
        "pre_read",
        "join",
        "postponed_games",
    ),
    "inconclusive": ("status_reasons", "contrasts_printed"),
}


# ---------------------------------------------------------------- Amendment 25
# How the scored frozen test is shown (registered 24 November 2026, before scoring). Everything
# below is printed in the scored state only, whatever the test shows; in every other state the
# paper stays as it was registered before Amendment 25.
#: Rule 1, the fallback: set to False only if the figure cannot be built by the submission.
#: Appendix N then carries ``P1_FIGURE_NOT_PRINTED``, whatever the test showed.
P1_FIGURE_READY = True
P1_FIGURE_FILE = "fig_frozen_test.png"
#: The figure stands after the three figures of the main text that precede the frozen-test section.
P1_FIGURE_NUMBER = 4
P1_FIGURE_NOT_PRINTED = "A figure of the frozen test's contrasts was registered on 24 November 2026 and is not printed."
#: Rule 1, the caption, word for word; N and the cutoff are filled in.
P1_FIGURE_CAPTION = (
    "The frozen 2026–27 test: every registered paired contrast in forecast error, on the {n} newcomers "
    "scored by {cutoff}. Dark: the paired difference in mean absolute error (EFF/36) with its 95% interval; "
    "the intervals are unadjusted. Light: the same contrast on the arrivals of 2020–2025, which were examined "
    "before registration. Band: differences too small to detect at this n with 80% power. Right of zero, the "
    "first-named forecast was the more accurate. The fourth row is the sum of the first two. Every row is "
    "drawn whatever it shows."
)
P1_FIGURE_CAPTION_MARK = "every registered paired contrast in forecast error"
P1_FIGURE_POINTER = "Figure {number} shows every registered paired contrast beside its 2020–2025 estimate."
#: Rule 1, the rows in their registered order: (key, block, the two forecasts, first-named first).
P1_FIGURE_ROWS = (
    ("P-a", "primary", "History plus translation\nagainst history alone"),
    ("P-b", "primary", "League-aware forecast\nagainst history plus translation"),
    (
        "P-c",
        "primary",
        "League-aware forecast plus translation\nagainst the league-aware forecast",
    ),
    ("S1", "secondary", "League-aware forecast\nagainst history alone"),
    ("S2", "secondary", "League-aware forecast\nagainst the destination-only forecast"),
    (
        "table_vs_destination_only",
        "secondary",
        "2015-table forecast\nagainst the destination-only forecast",
    ),
    (
        "league_aware_vs_table",
        "secondary",
        "League-aware forecast\nagainst the 2015-table forecast",
    ),
)
P1_FIGURE_TABLE_ROWS = ("table_vs_destination_only", "league_aware_vs_table")
P1_FIGURE_BLOCKS = {
    "primary": "Primary contrasts (registered 3 November 2026)",
    "secondary": "Secondary read-outs (registered 16 and 17 November 2026)",
}
#: Rule 1, the reading beside each row, in fixed words.
P1_FIGURE_READINGS = {
    "above_zero": "above zero",
    "includes_zero": "not detectable at this n",
    "below_zero": "below zero",
}
P1_FIGURE_FAILED = "failed to replicate"
#: Rule 4: the five contrasts that have an estimate on the arrivals of 2020-2025, and the clause.
P1_EARLIER_KEYS = ("P-a", "P-b", "P-c", "S1", "S2")
P1_EARLIER_CLAUSE = "its interval excludes the 2020–2025 estimate ({x})"
P1_EARLIER_MARK = "ts interval excludes the 2020–2025 estimate ("
#: Rule 2: the clause of Amendment 13, rule 1, that stands until the test is scored, and the words
#: for an interval of S2 that includes zero (the other two cases are the registered sentences of
#: Amendment 8 and of Amendment 18, rule 5, in ``P1_WORDING``).
P1_S2_PROMISE = "the frozen 2026–27 test carries a registered read-out for this gain"
P1_S2_NOT_DETECTABLE = "what knowing the source league adds once the destination is known was not detectable at this n"
#: The sentence that follows the read-out of the league numbers in the first section and in the
#: conclusion. It is in no registration. Until the test is scored it reads as it always has. In
#: the scored state the clause before it ends on the frozen 2026-27 test (Amendment 25, rule 2),
#: and five of five blind readers of made-up scored copies took "These seasons" to include that
#: test, which reads the frozen test as exploratory. The scored form names the two results that
#: are exploratory and why. Amir decided on 24 November 2026, before scoring, that the scored paper
#: names them; an independent review the same evening found the first wording ("The 2020–2025 and
#: older arrivals were examined before registration") too broad, because the older arrivals were
#: first read in a blind test, and the wording below replaced it, also before scoring. It follows
#: no outcome.
P1_EXAMINED = (
    "These seasons were examined before registration, so the evidence is exploratory"
)
P1_EXAMINED_SCORED = (
    "The 2020–2025 arrivals were examined before registration and the older arrivals had been read once "
    "before this comparison, so those two results are exploratory"
)
P1_S2_LESS_ACCURATE = (
    "knowing the source league made the 2026–27 forecasts less accurate"
)
P1_S2_POWER = "a gain of {d} EFF/36 would have been detected with 80% power"
P1_S2_FAILURE = "a failure of the league-aware forecast on 2026–27"
#: Appendix N of a scored paper: what Amendment 25 fixed, and when. In every other state nothing
#: of the amendment is printed, this sentence and its reference included.
AMEND25_NOTE = (
    "How the scored frozen test is shown was fixed on 24 November 2026, before scoring and after blind readers "
    "had read copies of the paper with made-up results: one figure of its registered contrasts, the read-out "
    "of the league numbers in the abstract, the introduction and the conclusion, the ordering of cross-league "
    "pairs in the main text, and words that say when an interval excludes the 2020–2025 estimate [@amend25]."
)
AMEND25_MARK = "How the scored frozen test is shown was fixed"


def p1_scored(d) -> bool:
    return p1_check(d) == "scored"


def p1_earlier(d) -> dict:
    """The paired contrasts of the frozen test on the arrivals of 2020-2025, each with its
    committed interval (Amendment 25, rules 1 and 4).

    P-a, P-b and P-c are the anchors of the score record (``p1_anchor``); S1 and S2 are the values
    Amendment 8 names (E28a: G_H and G_D). A row of the 2015 table has an earlier estimate only
    if the committed E31a summary holds the same paired contrast, with the same two arms, on
    those arrivals."""
    r, lad = d["recipes"], "results/A/R1/ladder"
    gains = e28(d)["e28a"]["contrasts"]
    out = {
        "P-a": get(r, f"{lad}/history_only->scheduled_history/player_club_season"),
        "P-b": get(r, "e1/head_to_head/lambda_10/player_club_season"),
        "P-c": get(
            r, f"{lad}/source_ridge_10->source_ridge_10_scheduled/player_club_season"
        ),
        "S1": gains["G_H"]["unweighted"],
        "S2": gains["G_D"]["unweighted"],
    }
    e31a = (d.get("e31") or {}).get("e31a")
    arm = (d.get("p1") or {}).get("published_table_arm") or {}
    if e31a is not None and arm.get("status") == "read":
        for key, name in zip(P1_FIGURE_TABLE_ROWS, ("T_D", "T_O")):
            c = e31a["contrasts"][name]
            if (c["left"], c["right"]) == (arm[key]["left"], arm[key]["right"]):
                out[key] = c["unweighted"]
    return {
        k: {"difference": v["difference"], "ci95": list(v["ci95"])}
        for k, v in out.items()
    }


def p1_contrast(p: dict, key: str) -> dict:
    """One paired contrast of the score record by its key."""
    if key in p["all"]:
        return p["all"][key]
    if key in ("S1", "S2"):
        return p["secondary"][key]
    return p["published_table_arm"][key]


def p1_excludes_earlier(d) -> dict:
    """Amendment 25, rule 4: for each of the five contrasts, the clause that its 2026-27
    interval excludes the 2020-2025 estimate, or nothing.

    The clause describes. It is said in either direction and whether or not the failure rule of
    Amendment 8 is met, and it changes no verdict. It is not repeated for a primary contrast
    whose registered failure sentence already says that the interval excluded the estimate."""
    p, earlier = d["p1"], p1_earlier(d)
    out = {}
    for key in P1_EARLIER_KEYS:
        lo, hi = p1_ci(p1_contrast(p, key))
        ref = earlier[key]["difference"]
        said = p["verdicts"].get(key) == "fails"
        out[key] = (
            "" if lo <= ref <= hi or said else P1_EARLIER_CLAUSE.format(x=num(ref))
        )
    return out


def p1_s2_words(p: dict, abstract: bool = False) -> str:
    """Amendment 25, rule 2: the reading of S2 in the registered words of its case (Amendment 8;
    Amendment 18, rule 5), as a clause. In the abstract the bracket of the case "includes zero"
    holds only the detectable gain."""
    c = p["secondary"]["S2"]
    reading = c["reading"]
    lo, hi = p1_ci(c)
    span = f"95% interval {num(lo)} to {num(hi)}"
    if reading == "above_zero":
        return (
            P1_WORDING[("S2", reading)].replace("X", num(abs(c["difference"])))
            + f" ({span})"
        )
    if reading == "below_zero":
        text = P1_WORDING[("S2", reading)].replace(
            "X EFF/36, interval", f"{num(c['difference'], sign=True)} EFF/36, {span}"
        )
        return text[0].lower() + text[1:].rstrip(".")
    if reading != "includes_zero":
        raise ClaimError("P1: S2 has no interval")
    power = P1_S2_POWER.format(
        d=num(p["pre_read"]["detectable_effects"]["S2"]["detectable_80"])
    )
    bracket = (
        power
        if abstract
        else f"{num(c['difference'], sign=True)} EFF/36, {span}; {power}"
    )
    return f"{P1_S2_NOT_DETECTABLE} ({bracket})"


# ---------------------------------------------------------------- Amendment 26
#: Amendment 26 (25 November 2026, after the scoring): the words of the paper once the frozen test
#: was scored and found inconclusive. Rules 1 to 9 apply in the inconclusive state only; rules 10
#: and 11 are two descriptive sentences from values the paper already prints, in every state.
#: The amendment as approved by Amir and pushed alone (commit c96b283e5, 25 November 2026, 07:53 UTC).
AMENDMENT_26_SHA256 = "cd090c0131148f20d8152dd0136b9002b3b324c310005458e9c0cd98173ac16c"
#: Rule 1: the clause of Amendment 13, rule 1, in the inconclusive state.
P1_S2_INCONCLUSIVE = "the frozen 2026–27 test carried a registered read-out for this gain and is inconclusive"
#: Rule 2: the end of the paragraph on the two tests (Amendment 19, rule 9), before and after.
TWO_TESTS_END = "Neither settles the other; the frozen 2026–27 test is the registered test on arrivals."
TWO_TESTS_END_INCONCLUSIVE = (
    "Neither settles the other; the frozen 2026–27 test, the registered test on arrivals, is inconclusive "
    "(next section)."
)
#: Rule 3: the verbs of the November scoring in the past (each old wording occurs once).
P1_PAST_TENSE = (
    (
        "They are scored on continental games through",
        "They were scored on continental games through",
    ),
    (
        "for newcomers who reach eight games; below 60 newcomers the test is descriptive only.",
        "for newcomers who reached eight games; below 60 newcomers the test would have been descriptive only.",
    ),
    (
        "As registered, we do not expect the first to be detectable in November: it looks for an effect near",
        "As registered, we did not expect the first to be detectable in November: it looked for an effect near",
    ),
)
#: Rule 5: the end of the sentence of Amendment 16, rule 6, before and after.
OFFER_TESTS = "tests on league changes and on frozen forecasts"
OFFER_TESTS_INCONCLUSIVE = (
    "test on league changes; its test on frozen forecasts is inconclusive"
)
#: Rule 6: the label of a weighted value in the paragraph "no sentence is licensed".
P1_WEIGHTED_LABEL = "weighted by playing time"
#: Rule 7: the heading of the paragraph in Appendix L, before and after.
P1_DETECT_HEAD = "**What the frozen test can detect.**"
P1_DETECT_HEAD_PAST = "**What the frozen test could detect.**"
P1_RULE_NOT_APPLIED = "The rule was not applied, because the test is inconclusive."
#: Rule 8: the sentence after the note on Amendment 20 in Appendix N.
P1_PAIRS_NOT_PRINTED = "The pairs and the tables of named newcomers are not printed, because the test is inconclusive."
#: Rule 9: the ending of Amendment 8 for the inconclusive state.
P1_SUMMARY_INCONCLUSIVE_OLD = (
    "could not be scored cleanly, so the registered test is inconclusive"
)
#: Appendix N: what Amendment 26 changed (the note is the renderer's; the amendment is cited).
AMEND26_NOTE = (
    "After the frozen test was scored and found inconclusive, the sentences that name it were rewritten on "
    "25 November 2026 to state that outcome, and two descriptive sentences were added from values the paper "
    "already printed; the registration of that day prints each sentence before and after [@amend26]."
)
AMEND26_NOTE_PENDING = "Two descriptive sentences were added on 25 November 2026 from values the paper already printed [@amend26]."
#: Rule 10 and rule 11: the caveats that stand with the two descriptive sentences (gate G26f).
GAPS_GREW_MARK = "The order was stable; the size of the gaps was not."
GAPS_GREW_CAVEAT = "The cause was not examined"
GAIN_SIZE_MARK = "In size, the gain over the destination-only forecast is about"
GAIN_SIZE_CAVEATS = ("carry no registered reading", "their difference was not tested")
#: Gate G26d: registered readings that may not stand beside the contrasts printed for the record.
P1_READING_WORDS = (
    "not clearly above zero",
    "not detectable",
    "detectable at this n",
    "held",
    "failed",
    "improves",
    "more accurate",
)


def p1_is_inconclusive(d) -> bool:
    return p1_check(d) == "inconclusive"


def p1_lost_targets_cause(p: dict) -> bool:
    """The cause that occurred: possible lost targets above the registered share, with the
    contrasts printed, and no other cause of an inconclusive test beside it."""
    return bool(
        not p.get("failed_gate")
        and p["join"]["above_threshold"]
        and p.get("contrasts_printed")
        and not p.get("n_unscorable")
        and p["n_scored"] >= p["min_n"]
    )


def p1_limits(d) -> str:
    """Rule 4: the Limitations entry on the frozen test begins with the outcome."""
    if not p1_is_inconclusive(d):
        return ""
    p = d["p1"]
    if not p1_lost_targets_cause(p):
        return "Inconclusive; the section on the test gives the cause. "
    j = p["join"]
    return (
        f"Inconclusive: {j['possible_lost_targets']} newcomers without a frozen forecast may be in the frozen "
        f"file under another spelling, {pct(j['possible_lost_share_of_joined'])} of the {j['joined']} joined, "
        f"above the {pct(j['threshold'], 0)} allowed in advance. "
    )


def refit_season(fit: str) -> str:
    """'2020–21' from 'refit for 2020' (the destination season that refit forecast)."""
    return season_label(int(fit.rsplit(" ", 1)[1]))


def refit_gap_means(d) -> dict:
    """Rule 10: the mean distance of the other leagues from Spain's value, by destination, in the
    first yearly refit, the last yearly refit and the full fit (the committed table of refits)."""
    fits = list(dict.fromkeys(row["fit"] for row in d["refits"]))
    first, last, full = fits[0], fits[-2], fits[-1]
    if not (
        first.startswith("refit for ")
        and last.startswith("refit for ")
        and full.startswith("full fit")
    ):
        raise ClaimError(
            "the table of refits is not six yearly refits and the full fit"
        )
    out = {"seasons": (refit_season(first), refit_season(last))}
    for destination in ("euroleague", "eurocup"):
        means = []
        for fit in (first, last, full):
            values = {
                row["source_league"]: float(row["acb16_equivalent_eff36"])
                for row in d["refits"]
                if row["destination"] == destination and row["fit"] == fit
            }
            others = [
                v - values["spain-acb"] for k, v in values.items() if k != "spain-acb"
            ]
            if len(others) != 9:
                raise ClaimError(
                    "the table of refits does not hold ten source leagues in every fit"
                )
            means.append(sum(others) / len(others))
        out[destination] = means
    return out


def gaps_grew(d) -> dict:
    """Rule 10: the league gaps grew from refit to refit; the sentence of the main text and the
    sentence beside Table A11. A description of printed values; the cause is not examined."""
    g = refit_gap_means(d)
    (s0, s1), el, ec = g["seasons"], g["euroleague"], g["eurocup"]
    if not el[1] > el[0]:
        raise ClaimError(
            "rule 10 of Amendment 26 describes gaps that grew; they did not: this goes to Amir"
        )
    main = (
        f" {GAPS_GREW_MARK} For EuroLeague arrivals the nine other leagues stood on average {num(el[0], 1)} "
        f"EFF/36 above Spain's 16 in the refit that forecast {s0} and {num(el[1], 1)} in the refit that forecast "
        f"{s1}, against {num(el[2], 1)} in the full fit of {{{{eq_table}}}}. {GAPS_GREW_CAVEAT} [@amend26]."
    )
    beside = (
        "\n\nThe mean distance of the nine other leagues from Spain's 16, in the refit that forecast "
        f"{s0}, the refit that forecast {s1} and the full fit: {num(el[0], 1)}, {num(el[1], 1)} and "
        f"{num(el[2], 1)} EFF/36 for EuroLeague arrivals; {num(ec[0], 1)}, {num(ec[1], 1)} and {num(ec[2], 1)} "
        "for EuroCup arrivals. Table A11 prints the refits for EuroLeague arrivals; those for EuroCup arrivals "
        "are drawn in Figure A3, and their values are in the table of refits released with the paper. "
        "These describe the values of the refits and were added after they were seen; "
        "the cause was not examined [@amend26]."
    )
    return {"gaps_grew": main, "gaps_grew_beside": beside}


def gain_share_clause(d) -> str:
    """Amendment 29, rule 1: the size of what the source league adds, on the first page, as the
    share that Results prints (rule 11 of Amendment 26)."""
    g = e28(d)["e28a"]["contrasts"]["G_D"]["unweighted"]
    share = round(100 * g["difference"] / g["mae_left"])
    return (
        f", about {share}% of the error of a forecast that knows only the destination"
    )


def gain_size(d) -> str:
    """Rule 11: the size of what the source league adds, and the gain by competition as values."""
    a = e28(d)["e28a"]
    g = a["contrasts"]["G_D"]["unweighted"]
    share = round(100 * g["difference"] / g["mae_left"])
    parts = []
    for key, name in (("euroleague", "EuroLeague"), ("eurocup", "EuroCup")):
        c = a["by_destination"][key]["G_D"]["unweighted"]
        parts.append(
            f"{num(c['difference'])} ({e28_span(c)}) for the {c['n']} {name} arrivals"
        )
    return (
        f" {GAIN_SIZE_MARK} {share}% of that forecast's mean absolute error ({num(g['mae_left'])} EFF/36). "
        f"By competition it is {parts[0]} and {parts[1]}. The two values by competition "
        f"{GAIN_SIZE_CAVEATS[0]}, and {GAIN_SIZE_CAVEATS[1]} [@amend26]."
    )


def amend26_note(d) -> str:
    return " " + (AMEND26_NOTE if p1_is_inconclusive(d) else AMEND26_NOTE_PENDING)


def p1_s2_blocks(d) -> dict:
    """Amendment 25, rule 2: S2 where the paper promises it. Until the test is scored, and in
    every state that is not scored, the introduction and the conclusion keep the clause of
    Amendment 13, rule 1, and the abstract ends as Amendment 8 fixes."""
    if not p1_scored(d):
        # Amendment 26, rule 1: in the inconclusive state the clause states the outcome
        promise = P1_S2_INCONCLUSIVE if p1_is_inconclusive(d) else P1_S2_PROMISE
        return {
            "p1_s2_abstract": "",
            "p1_s2_intro": promise,
            "p1_s2_conclusion": f" ({promise})",
            "p1_examined": P1_EXAMINED,
        }
    p = d["p1"]
    lead = f"on the {p['n_scored']} newcomers of the frozen 2026–27 test, "
    return {
        "p1_s2_abstract": "; " + p1_s2_words(p, abstract=True),
        "p1_s2_intro": lead + p1_s2_words(p),
        "p1_s2_conclusion": "; " + lead + p1_s2_words(p),
        "p1_examined": P1_EXAMINED_SCORED,
    }


def p1_figure_printed(d) -> bool:
    """Amendment 25, rule 1: the figure is printed in the scored state and in no other."""
    return P1_FIGURE_READY and p1_scored(d)


def p1_figure_rows(d) -> list:
    """Amendment 25, rule 1: the rows of the figure, in their registered order, each with every
    value and every word the figure prints.

    Nothing is computed: estimates, intervals and detectable differences are read from the score
    record (for the first five rows the detectable differences printed before any contrast was
    read, which the text also prints), the earlier estimates from committed summaries."""
    p, earlier = d["p1"], p1_earlier(d)
    pre, arm = p["pre_read"]["detectable_effects"], p["published_table_arm"]
    if arm["status"] not in ("read", "not_registered_in_time"):
        raise ClaimError(
            f"P1: unknown state of the published-table forecast: {arm['status']}"
        )
    rows = []
    for key, block, label in P1_FIGURE_ROWS:
        if key in P1_FIGURE_TABLE_ROWS:
            if arm["status"] != "read":
                continue
            c = arm[key]
            detectable = c["detectable_80"]
        else:
            c = p1_contrast(p, key)
            detectable = pre[key]["detectable_80"]
        lo, hi = p1_ci(c)
        reading = (
            "above_zero" if lo > 0 else "below_zero" if hi < 0 else "includes_zero"
        )
        words = (
            P1_FIGURE_FAILED
            if p["verdicts"].get(key) == "fails"
            else P1_FIGURE_READINGS[reading]
        )
        rows.append(
            {
                "key": key,
                "block": block,
                "label": label,
                "difference": c["difference"],
                "ci95": [lo, hi],
                "detectable": detectable,
                "earlier": earlier.get(key),
                "text": f"{num(c['difference'], sign=True)} {interval([lo, hi])}",
                "reading": words,
            }
        )
    return rows


#: Appendix L of a scored paper with the figure: what its bands are. The first five rows have a
#: detectable effect printed before any contrast was read; the two rows against the 2015 table
#: have none, so their band is the detectable difference of the scored contrast itself.
P1_FIGURE_BANDS = (
    "**The bands of Figure {n}.** On {rows} the band is the detectable effect above, printed before any "
    "contrast was read."
)
P1_FIGURE_BANDS_TABLE = (
    " The two rows against the 2015 table have no such value; their band is the detectable difference at "
    "the standard error of the scored contrast."
)


def p1_figure_bands(p: dict) -> str:
    table = p["published_table_arm"]["status"] == "read"
    text = P1_FIGURE_BANDS.format(
        n=P1_FIGURE_NUMBER, rows="the first five rows" if table else "every row"
    )
    return text + (P1_FIGURE_BANDS_TABLE if table else "")


def p1_figure_block(d) -> str:
    """Amendment 25, rule 1: the figure of the registered paired contrasts, with its caption."""
    if not p1_figure_printed(d):
        return ""
    caption = P1_FIGURE_CAPTION.format(n=d["p1"]["n_scored"], cutoff=META["p1_cutoff"])
    return f"![Figure {P1_FIGURE_NUMBER}. {caption}](figures/{P1_FIGURE_FILE})"


def amend25_note(d) -> str:
    """Appendix N of a scored paper: what Amendment 25 fixed; and, without the figure, the
    sentence rule 1 registers for that case. In every other state: nothing."""
    if not p1_scored(d):
        return ""
    note = " " + AMEND25_NOTE
    if not P1_FIGURE_READY:
        note += " " + P1_FIGURE_NOT_PRINTED
    return note


def p1_anchor(d) -> dict:
    """The 2020-2025 point estimates the P1 contrasts are read against."""
    r = d["recipes"]
    a = "results/A/R1/ladder"
    return {
        "history_gain": get(
            r, f"{a}/history_only->scheduled_history/player_club_season/difference"
        ),
        "c_h": get(r, "e1/head_to_head/lambda_10/player_club_season/difference"),
        "inc10": get(
            r,
            f"{a}/source_ridge_10->source_ridge_10_scheduled/player_club_season/difference",
        ),
    }


def p1_ci(c: dict):
    return c["ci95"] if c.get("ci95") is not None else c["player_club_season"]["ci95"]


def p1_verdicts(p: dict, anchor: dict) -> dict:
    """Amendment 8, rule 1: a contrast fails to replicate when its interval excludes the
    anchor's point estimate, its own estimate has the opposite sign and, for P-a, its
    interval also excludes zero (the 3 Nov registration: a P-a interval that spans zero
    is "not detectable at this n, never a contradiction of the anchor")."""
    out = {}
    block = p["all"]
    for key, (_, which) in P1_CONTRASTS.items():
        c = block[key]
        lo, hi = p1_ci(c)
        ref = anchor[which]
        opposite = (c["difference"] > 0) != (ref > 0)
        fails = not lo <= ref <= hi and opposite
        if key == "P-a":
            fails = fails and not lo <= 0 <= hi
        out[key] = "fails" if fails else "consistent"
    return out


def p1_check(d) -> str:
    """The state of the frozen test, after refusing a record no sentence may be written from."""
    p = d["p1"]
    if p is None:
        return "pending"
    status = p.get("status")
    if status == "pending":
        return status
    if status not in P1_REQUIRED:
        raise ClaimError(f"unknown P1 status: {status}")
    if p.get("synthetic") and not d.get("p1_rehearsal"):
        raise ClaimError(
            "P1: this score record is a rehearsal on made-up outcomes (synthetic: true)"
        )
    missing = [k for k in P1_REQUIRED[status] if k not in p]
    if missing:
        raise ClaimError(f"P1: the score record lacks {missing}")
    if status == "scored":
        if (
            p["n_scored"] < p["min_n"]
            or p.get("n_unscorable")
            or p["join"]["above_threshold"]
        ):
            raise ClaimError(
                "P1: a record that breaks a registered rule is marked scored"
            )
        anchor = p1_anchor(d)
        for key, (_, which) in P1_CONTRASTS.items():
            if abs(p["anchor"][key] - anchor[which]) > 1e-12:
                raise ClaimError(
                    f"P1: the scorer read {key} against another 2020-2025 estimate"
                )
        if p1_verdicts(p, anchor) != p["verdicts"]:
            raise ClaimError(
                "P1: the scorer's verdicts differ from the registered rule"
            )
        if p["secondary"]["count"] != 5:
            raise ClaimError("P1: five secondary read-outs are registered")
        p1_rule5_check(p)
    return status


def p1_rule5_keys(p: dict) -> list:
    """Amendment 18, rule 5, read from the intervals themselves: S1 or S2 wholly
    below zero, cross-league ordering (S4) wholly below 50%."""
    s = p["secondary"]
    out = [key for key in ("S1", "S2") if p1_ci(s[key])[1] < 0]
    span = s["S4"]["cross"]["league_aware"].get("ci95")
    if span is not None and span[1] < 0.5:
        out.append("S4")
    return out


def p1_rule5_check(p: dict) -> list:
    """Gate G18b, on the record: a record whose intervals trigger a registered
    failure sentence must say so itself, and must have sent it to Amir first."""
    keys = p1_rule5_keys(p)
    s = p["secondary"]
    for key, label in P1_RULE5.items():
        got = (
            s[key]["reading"]
            if key != "S4"
            else s[key]["cross"]["league_aware"]["reading"]
        )
        if (got == label) != (key in keys):
            raise ClaimError(
                f"P1: the record's reading of {key} ({got}) does not match its interval "
                "(Amendment 18, rule 5)"
            )
    if sorted(p["rule_5_sentences"]) != sorted(keys):
        raise ClaimError(
            f"P1: the record lists the registered failure sentences {p['rule_5_sentences']}, "
            f"its intervals require {keys} (Amendment 18, rule 5)"
        )
    for key in keys:
        if not any(
            note.startswith(f"{key} is below") and "Amendment 18, rule 5" in note
            for note in p["escalate_to_amir_before_writing"]
        ):
            raise ClaimError(
                f"P1: the failure sentence for {key} goes to Amir before any writing, and the "
                "record does not show that it did (Amendment 18, rule 5)"
            )
    return keys


def p1_rule5_sentence(key: str, p: dict) -> str:
    """One of the three sentences of Amendment 18, rule 5, in its registered
    words, in bold, with the partial-season caveat directly beside it."""
    if key == "S4":
        own = p["secondary"]["S4"]["cross"]["league_aware"]
        span = f"95% interval {pct(own['ci95'][0])} to {pct(own['ci95'][1])}"
        text = (
            P1_WORDING[("S4", "below_half")]
            .replace("X%", pct(own["share_correct"]))
            .replace("(interval)", f"({span})")
        )
    else:
        c = p["secondary"][key]
        text = P1_WORDING[(key, "below_zero")].replace(
            "X EFF/36, interval",
            f"{num(c['difference'], sign=True)} EFF/36, 95% interval {interval(p1_ci(c))}",
        )
    return f"**{text}** {P1_CAVEAT}"


def p1_postponed(p: dict) -> str:
    """Amendment 18, rule 1: the paper states how many games were postponed."""
    block = p.get("postponed_games")
    if block is None:
        return ""
    n = block["count"]
    if n != len(block["games"]):
        raise ClaimError("P1: the count of postponed games differs from their list")
    if not n:
        return ""
    one = n == 1
    return (
        f"{n} scheduled {'game' if one else 'games'} dated on or before {META['p1_cutoff']} "
        f"{'was' if one else 'were'} marked as not played in the refreshed schedule. "
        f"{'It is a postponed game' if one else 'They are postponed games'}, not "
        f"{'a missing box score' if one else 'missing box scores'}: "
        f"{'it is' if one else 'they are'} listed in the scoring record and not counted, "
        "a reading registered before scoring."
    )


def p1_summary(d) -> str:
    """The abstract's ending for each state of the frozen test, as fixed by Amendment 8."""
    status = p1_check(d)
    p = d["p1"]
    if status == "pending":
        return "await the registered partial-season test"
    if status == "inconclusive":
        # Amendment 26, rule 9: for the cause that occurred, in a paper that prints the test on
        # league changes; otherwise the ending of Amendment 8
        if p1_lost_targets_cause(p) and e30_case(d) in E30_TESTED:
            j = p["join"]
            return (
                "were scored once on 2026–27 newcomers. That test, separate from the test on league changes, is "
                f"inconclusive: {j['possible_lost_targets']} newcomers without a forecast may be in the frozen "
                f"file under another spelling, more than the {pct(j['threshold'], 0)} of the {j['joined']} joined "
                "newcomers that was allowed in advance"
            )
        return P1_SUMMARY_INCONCLUSIVE_OLD
    if status == "not_adjudicable":
        return (
            f"yielded {p['n_scored']} eligible newcomers, fewer than the {p['min_n']} required, "
            "so the registered test is not adjudicable"
        )
    failed = [P1_CONTRASTS[k][0] for k, v in p["verdicts"].items() if v == "fails"]
    head = f"were scored on {p['n_scored']} newcomers: "
    if failed:
        return head + " and ".join(failed) + " failed to replicate"
    return (
        head + "the pattern held on unseen 2026–27 forecasts, within this test's power"
    )


def p1_cell(c: dict) -> str:
    return (
        f"{num(c['difference'], sign=True)} EFF/36 (95% interval {interval(p1_ci(c))})"
    )


def p1_primary_parts(p: dict, verdict: dict, earlier: dict | None = None) -> list:
    """Amendment 8, rule 2: detectable only if the interval excludes zero; a head-to-head
    estimate below zero that spans zero is "no difference detected at this n"."""
    parts = []
    for key, (name, _) in P1_CONTRASTS.items():
        c = p["all"][key]
        lo, hi = p1_ci(c)
        note = ""
        if lo <= 0 <= hi:
            note = ", not detectable at this n"
            if key == "P-b" and c["difference"] < 0 and verdict[key] != "fails":
                note = ", " + P1_WORDING[("P-b", "includes_zero")]
        if earlier and earlier.get(key):
            # Amendment 25, rule 4
            note += f", and {earlier[key]}"
        parts.append(f"{name} was {p1_cell(c)}{note}")
    return parts


def p1_not_detectable(name: str, c: dict, n: int, mde: float) -> str:
    return (
        f"{name[0].upper() + name[1:]} ({num(c['difference'], sign=True)} EFF/36, 95% interval "
        f"{interval(p1_ci(c))}) was not detectable at this n ({n} newcomers; detectable effect {num(mde)} EFF/36)."
    )


def p1_gain_sentence(key: str, p: dict) -> str:
    """S1 or S2 in the words Amendment 8 registers for its interval."""
    c = p["secondary"][key]
    reading = c["reading"]
    x, ci = num(abs(c["difference"])), interval(p1_ci(c))
    if reading == "includes_zero":
        mde = p["pre_read"]["detectable_effects"][key]["detectable_80"]
        return p1_not_detectable(P1_SECONDARY[key], c, p["n_scored"], mde)
    if reading == "above_zero":
        text = P1_WORDING[(key, reading)].replace("X", x)
        return f"{text[0].upper() + text[1:]} (95% interval {ci})."
    if reading != "below_zero":
        raise ClaimError(f"P1: {key} has no interval")
    return p1_rule5_sentence(key, p)


def p1_table_sentences(p: dict) -> str:
    """Amendment 15, E31c: the published-table forecast beside S1 and S2, in Amendment 8's words."""
    arm = p["published_table_arm"]
    if arm["status"] == "not_registered_in_time":
        return (
            "The forecast built on a published league table (Amendment 15) was not registered in time "
            "for this test, so it is not read out."
        )
    if arm["status"] != "read":
        raise ClaimError(
            f"P1: unknown state of the published-table forecast: {arm['status']}"
        )
    n, out = p["n_scored"], []
    for key, name, better, worse in (
        (
            "table_vs_destination_only",
            "a league table printed in 2015 against the forecast that knows only the destination",
            "On unseen 2026–27 forecasts a league table printed in 2015 improved the forecast that knows only the destination",
            "On unseen 2026–27 forecasts a league table printed in 2015 made the forecast that knows only the destination less accurate",
        ),
        (
            "league_aware_vs_table",
            "the league-aware forecast against the forecast built on the 2015 table",
            "On unseen 2026–27 forecasts the league-aware forecast was more accurate than the forecast built on the 2015 table",
            "On unseen 2026–27 forecasts the forecast built on the 2015 table was more accurate than the league-aware forecast",
        ),
    ):
        c = arm[key]
        x, ci = num(abs(c["difference"])), interval(p1_ci(c))
        if c["reading"] == "includes_zero":
            out.append(p1_not_detectable(name, c, n, c["detectable_80"]))
        elif c["reading"] == "above_zero":
            out.append(f"{better}, by {x} EFF/36 (95% interval {ci}).")
        elif c["reading"] == "below_zero":
            out.append(
                f"**{worse} ({num(c['difference'], sign=True)} EFF/36, 95% interval {ci}).**"
            )
        else:
            raise ClaimError("P1: the published-table read-out has no interval")
    return " ".join(out)


def p1_level_sentence(p: dict) -> str:
    c = p["secondary"]["S3"]["source_ridge_10"]
    reading, ci = c["reading"], interval(c["ci95"])
    if reading == "includes_zero":
        text = P1_WORDING[("S3", reading)]
        return f"{text[0].upper() + text[1:]} ({num(c['mean_signed_error'], sign=True)} EFF/36, 95% interval {ci})."
    text = P1_WORDING[("S3", reading)].replace("X", num(abs(c["mean_signed_error"])))
    return f"{text[0].upper() + text[1:]} (95% interval {ci})."


#: The end of the comparison with history when its interval includes zero.
P1_ORDER_NOT_DETECTABLE = ") was not detectable at this n."
#: Where the registered sentence on cross-league ordering ends and the comparison with history begins.
P1_ORDER_SPLIT = " History alone ordered"


def p1_order_sentence(p: dict) -> str:
    s4 = p["secondary"]["S4"]["cross"]
    own, diff = s4["league_aware"], s4["league_aware_minus_history"]
    span = f"95% interval {pct(own['ci95'][0])} to {pct(own['ci95'][1])}; {s4['unequal_pairs']:,} pairs"
    if own["reading"] == "above_half":
        text = P1_WORDING[("S4", "above_half")].replace("X%", pct(own["share_correct"]))
        first = f"{text[0].upper() + text[1:]} ({span})."
    elif own["reading"] == "includes_half":
        first = (
            f"The league-aware forecast's ordering of cross-league pairs ({pct(own['share_correct'])} correct; {span}) "
            f"was {P1_WORDING[('S4', 'includes_half')]}."
        )
    elif own["reading"] == "below_half":
        first = (
            f"{p1_rule5_sentence('S4', p)} The count is over {s4['unequal_pairs']:,} "
            "cross-league pairs."
        )
    else:
        raise ClaimError("P1: cross-league ordering has no interval")
    gap = f"{pp(diff['difference'])} points, 95% interval {pp(diff['ci95'][0])} to {pp(diff['ci95'][1])}"
    second = (
        f"History alone ordered {pct(s4['history']['share_correct'])}; the difference ({gap}) was not detectable at this n."
        if diff["reading"] == "includes_zero"
        else f"History alone ordered {pct(s4['history']['share_correct'])}, a difference of {gap}."
    )
    return first + " " + second


#: Appendix L when the frozen test is not scored and its contrasts are printed for the record.
P1_LEVEL_ORDER_RECORD = "**Forecast level and ordering, for the record only.**"


def p1_order_values(p: dict) -> str:
    """The ordering of cross-league pairs as values, with no sentence of Amendment 8 or 18."""
    s4 = p["secondary"]["S4"]["cross"]
    own, diff = s4["league_aware"], s4["league_aware_minus_history"]
    return (
        f"Share of cross-league pairs ordered correctly: league-aware forecast {pct(own['share_correct'])} "
        f"(95% interval {pct(own['ci95'][0])} to {pct(own['ci95'][1])}; {s4['unequal_pairs']:,} pairs); "
        f"history alone {pct(s4['history']['share_correct'])}; difference {pp(diff['difference'])} points "
        f"(95% interval {pp(diff['ci95'][0])} to {pp(diff['ci95'][1])})."
    )


def p1_e32_pointer(d) -> str:
    """Amendment 19, rule 12: the pointer to the named-newcomer tables (E32). It prints nothing
    while the frozen test is pending and while no E32 table file exists; E32 is built after
    scoring."""
    if not e32_printed(d):
        return ""
    if not E32_READY:
        raise ClaimError(
            "E32: the named-newcomer tables are committed, but the paper does not print them yet "
            "(Amendment 19, rule 12)"
        )
    e32_check(d)
    return e32_pointer_text(d)


def p1_table_sentence(p: dict) -> str:
    """Amendment 19, rule 12: the published-table read-out in one sentence of the main text
    (Amendment 15, E31c, in Amendment 8's words for each of its two differences)."""
    text = p1_table_sentences(p)
    parts = re.split(r"(?<=[.!?*])\s+(?=[A-Z*])", text)
    if len(parts) == 1:
        return text
    if len(parts) != 2:
        raise ClaimError("P1: the published-table read-out is not two differences")
    first, second = parts
    first = first[:-3] + "**" if first.endswith(".**") else first.rstrip(".")
    second = second if second.startswith("**") else second[0].lower() + second[1:]
    return f"{first}; {second}"


def p1_order_appendix(p: dict) -> str:
    """Appendix L (Amendment 19, rule 12): the ordering read-out. A failure sentence of Amendment 18,
    rule 5, is printed once, in the main text; here only the comparison with history follows it."""
    text = p1_order_sentence(p)
    if "S4" not in p1_rule5_keys(p):
        return text
    if P1_ORDER_SPLIT not in text:
        raise ClaimError("P1: the ordering read-out lost its comparison with history")
    return (
        "The registered sentence on the ordering of cross-league pairs is in the main text."
        + P1_ORDER_SPLIT
        + text.split(P1_ORDER_SPLIT, 1)[1]
    )


def p1_gain_with_earlier(key: str, p: dict, clause: str) -> str:
    """S1 or S2 in its registered words, with the clause of Amendment 25, rule 4, where the
    interval excludes the 2020-2025 estimate. A sentence of Amendment 18, rule 5, stays word for
    word with its caveat beside it; the clause then follows as a sentence of its own."""
    sentence = p1_gain_sentence(key, p)
    if not clause:
        return sentence
    if key in p1_rule5_keys(p):
        return f"{sentence} {clause[0].upper() + clause[1:]}."
    if not sentence.endswith("."):
        raise ClaimError(f"P1: the sentence of {key} does not end in a full stop")
    return f"{sentence[:-1]}; {clause}."


def p1_secondary(p: dict, earlier: dict | None = None) -> str:
    """The main text after scoring (Amendment 19, rule 12): S1 and S2 in the registered words, any
    sentence of Amendment 18, rule 5, and the published-table read-out in one sentence.
    Amendment 25, rule 3, adds the sentences on the ordering of cross-league pairs (S4) that
    Appendix L prints. S3, S5 and the complete-source sensitivity are printed in Appendix L."""
    earlier = earlier or {}
    parts = [
        "Five secondary read-outs were registered for this test [@amend8; @amend18]; their intervals are "
        "unadjusted 95% intervals.",
        p1_gain_with_earlier("S1", p, earlier.get("S1", "")),
        p1_gain_with_earlier("S2", p, earlier.get("S2", "")),
        # Amendment 25, rule 3: the ordering read-out in the registered words of its case, with
        # the comparison with history (a failure sentence of Amendment 18, rule 5, stands here
        # as before, with its count)
        p1_order_sentence(p),
    ]
    parts.append(p1_table_sentence(p))
    parts.append(
        "Appendix L gives the forecast errors and paired gains side by side, the forecast level, the ordering "
        "of pairs, every contrast weighted by playing time and the complete-source sensitivity. "
        "These outcomes cover only newcomers who reached eight "
        "games early, over few games; a level error or a weak ordering in November may reflect that, and all "
        "five read-outs are repeated at the February re-score."
    )
    return " ".join(parts)


def p1_inconclusive(p: dict) -> str:
    """The first paragraph of the section on the frozen test in the inconclusive state: the
    outcome, with the day of the one scoring run (Amendment 26, rule 3), then the cause in the
    registered words, then the contrasts for the record (Amendment 8, rule 3)."""
    day = long_date(p["scored_on"])
    if p1_lost_targets_cause(p):
        j = p["join"]
        out = [
            f"The test was scored once, on {day}, and is inconclusive. Of the "
            f"{j['newcomers_reaching_eight_games']} newcomers who had reached eight continental games, "
            f"{j['joined']} had a frozen forecast under their name and {j['unjoined']} did not. A newcomer has no "
            "frozen forecast when he has no 2025–26 season in the frozen file, or when the two sources write his "
            f"name differently; no name is joined by hand. {j['possible_lost_targets']} of the {j['unjoined']} "
            "may be players in the frozen file under another spelling: set against the "
            f"{j['joined']} joined newcomers that is {pct(j['possible_lost_share_of_joined'])}, above the "
            f"{pct(j['threshold'], 0)} we allowed in advance [@amend8]. No replication or equivalence conclusion "
            "is drawn."
        ]
    else:
        out = [
            f"The scoring run was made once, on {day}, and the test is inconclusive. No replication or "
            "equivalence conclusion is drawn."
        ]
    if p.get("failed_gate"):
        if p["failed_gate"] not in P1_GATE_NAMES:
            raise ClaimError(f"P1: unknown data gate: {p['failed_gate']}")
        out.append(
            f"A data check failed ({P1_GATE_NAMES[p['failed_gate']]}) and could not be repaired by refreshing the files, "
            "so no contrast was computed."
        )
        return " ".join(out)
    j = p["join"]
    if j["above_threshold"] and not p1_lost_targets_cause(p):
        out.append(
            f"Of the {j['unjoined']} newcomers with no frozen forecast under their name, {j['possible_lost_targets']} may be "
            f"players in the frozen file under another spelling: {pct(j['possible_lost_share_of_joined'])} of the "
            f"{j['joined']} joined newcomers, above the {pct(j['threshold'], 0)} we allowed in advance."
        )
    if p.get("n_unscorable"):
        out.append(
            f"{p['n_unscorable']} joined newcomers had no complete frozen forecast."
        )
    if p["n_scored"] < p["min_n"]:
        # Amendment 18, rule 2: unclean and too few is inconclusive; both facts
        out.append(
            f"In addition, only {p['n_scored']} newcomers could be scored, fewer than the "
            f"{p['min_n']} we required in advance. The state is inconclusive: when the newcomers "
            "cannot be counted cleanly, their number cannot be read either."
        )
    if p["contrasts_printed"]:
        parts = [
            f"{name} was {p1_cell(p['all'][key])}"
            for key, (name, _) in P1_CONTRASTS.items()
        ]
        out.append(
            f"For the record only, on the {p['n_scored']} newcomers that could be scored, "
            + "; ".join(parts)
            + ". No sentence is licensed by these values (Appendix L)."
        )
    if "postponed_games" not in p:
        raise ClaimError("P1: the score record lacks ['postponed_games']")
    if p1_postponed(p):
        out.append(p1_postponed(p))
    return " ".join(out)


def p1_descriptive(p: dict) -> str:
    """Amendment 8, rule 4: n, median games and the error of the four primary forecasts."""
    d = p["descriptive"]
    if not d["n"]:
        return "No contrast, interval or secondary read-out is computed."
    errors = ", ".join(
        f"{num(d['mae'][arm])} ({name})" for arm, name in P1_ARM_NAMES.items()
    )
    return (
        f"Their median number of games was {d['median_games']:g}. The mean absolute error of the four primary "
        f"forecasts was {errors} EFF/36. No contrast, interval or secondary read-out is computed."
    )


def p1_power_note(d) -> str:
    """The detail of the frozen test's power and of its scoring, printed in Appendix L."""
    power = power_table(d["prereg"])
    sd_h, h100, h150 = power["history vs history + translation"]
    sd_i, i100, i150 = power["offsets λ10 vs + translation"]
    base = (
        f"{P1_DETECT_HEAD} The gain over history varies about "
        f"{sd_h / sd_i:.0f} times more from player to player than translation's increment, which is why its "
        "detectable effect is the larger one. The realised number of newcomers and a recomputed detectable "
        "effect are reported with the result. At 100–150 newcomers the test can detect an increment of about "
        f"{i150:.3f}–{i100:.3f} EFF/36, and a gain over history of {h150:.3f}–{h100:.3f}, which is larger than the "
        f'{num(p1_anchor(d)["history_gain"])} in Table A24, so a null there would mean "not detectable", not a '
        "contradiction. These figures are optimistic, because the outcomes cover only part of a season. A contrast "
        "fails to replicate if its interval excludes its 2020–2025 estimate and its own estimate has the opposite "
        "sign; for the gain over history its interval must also exclude zero [@amend8]. How a postponed game, an "
        "unclean join and three outcomes without earlier wording are read was fixed on 18 November 2026, before "
        "scoring [@amend18]."
    )
    status = p1_check(d)
    p = d["p1"]
    if status == "inconclusive":
        # Amendment 26, rule 7: the plan is printed as what it was
        scored = (
            f"{p['pre_read']['n_scored']} newcomers were scored; the detectable effects recomputed at that "
            "number are printed below."
            if p.get("pre_read", {}).get("n_scored")
            else "The scoring run computed no contrast."
        )
        base = (
            f"{P1_DETECT_HEAD_PAST} The gain over history varies about "
            f"{sd_h / sd_i:.0f} times more from player to player than translation's increment, which is why its "
            "detectable effect is the larger one. Before scoring, the registration expected that at 100–150 "
            f"newcomers the test could detect an increment of about {i150:.3f}–{i100:.3f} EFF/36, and a gain over "
            f"history of {h150:.3f}–{h100:.3f}, which is larger than the "
            f'{num(p1_anchor(d)["history_gain"])} in Table A24, so that a null there would have meant "not '
            f'detectable", not a contradiction. {scored} These figures are optimistic, because the outcomes cover '
            "only part of a season. A contrast fails to replicate if its interval excludes its 2020–2025 estimate "
            "and its own estimate has the opposite sign; for the gain over history its interval must also exclude "
            f"zero [@amend8]. {P1_RULE_NOT_APPLIED} How a postponed game, an unclean join and three outcomes "
            "without earlier wording are read was fixed on 18 November 2026, before scoring [@amend18]."
        )
    if status == "pending" or "pre_read" not in p:
        return base
    return "\n\n".join([base, *p1_scoring_detail(p, status), *e32_appendix(d)])


#: The arms of the scorecard of the frozen test (Amendment 23, rule 6): the destination-only
#: forecast, the 2015-table forecast and the league-aware forecast.
P1_SCORECARD_DESTINATION = "history_destination_slope"
P1_SCORECARD_TABLE = "published_table_vashro_2015"
P1_SCORECARD_AWARE = "source_ridge_10"
G23E_REFUSAL = "G23e (Amendment 23, rule 6): the paired scorecard needs matching newcomers, arms and errors"


def p1_scorecard_contrasts(p: dict) -> list:
    """The registered contrasts the scorecard prints, each with the two arms it must name:
    (contrast, left arm, right arm). S2 of Amendment 8, and the two read-outs of E31c when the
    read-out of the 2015 table was registered in time."""
    published = p["published_table_arm"]
    contrasts = [(p["secondary"]["S2"], P1_SCORECARD_DESTINATION, P1_SCORECARD_AWARE)]
    if published["status"] == "read":
        contrasts += [
            (
                published["table_vs_destination_only"],
                P1_SCORECARD_DESTINATION,
                P1_SCORECARD_TABLE,
            ),
            (
                published["league_aware_vs_table"],
                P1_SCORECARD_TABLE,
                P1_SCORECARD_AWARE,
            ),
        ]
    elif published["status"] != "not_registered_in_time":
        raise ClaimError("P1: unknown registration state for the 2015 forecast")
    return contrasts


def p1_scorecard_errors(p: dict) -> dict:
    """The arm errors of the scorecard: arm -> unweighted mean absolute error on the scored newcomers."""
    errors = {
        arm: p["mae"][arm] for arm in (P1_SCORECARD_DESTINATION, P1_SCORECARD_AWARE)
    }
    if p["published_table_arm"]["status"] == "read":
        errors[P1_SCORECARD_TABLE] = p["published_table_arm"]["mae"]
    return errors


def p1_scorecard_arms_check(p: dict) -> None:
    """Gate G23e, the arms: every contrast of the scorecard names its two arms and is unweighted."""
    for c, left, right in p1_scorecard_contrasts(p):
        if (c["left"], c["right"]) != (left, right) or c["weighting"] != "unweighted":
            raise ClaimError(G23E_REFUSAL)


def p1_scorecard_check(p: dict | None) -> None:
    """Gate G23e (Amendment 23, rule 6): the scorecard is printed only if the count of newcomers,
    the two arms and the two errors of each contrast agree with the score record.

    Checked when the score record is loaded, for a record whose scorecard is printed. The count
    and the errors are not checked again when the text is composed: the number manifest traces a
    number by changing one value at a time, and a check of one value of the record against
    another inside compose() refuses every such change, so that the gains and errors of the
    frozen test would be listed as numbers typed in the renderer. The arms are names, which no
    such change touches; they are also checked where the table is built.
    """
    if p is None or p.get("status") != "scored" or not p.get("contrasts_printed"):
        return
    try:
        p1_scorecard_arms_check(p)
        n, errors = p["n_scored"], p1_scorecard_errors(p)
        for c, left, right in p1_scorecard_contrasts(p):
            if (
                c["n"] != n
                or not math.isclose(c["mae_left"], errors[left], abs_tol=1e-10)
                or not math.isclose(c["mae_right"], errors[right], abs_tol=1e-10)
                or not math.isclose(
                    c["difference"], errors[left] - errors[right], abs_tol=1e-10
                )
            ):
                raise ClaimError(G23E_REFUSAL)
    except (KeyError, TypeError) as error:
        raise ClaimError(
            f"G23e (Amendment 23, rule 6): the score record lacks what the scorecard reads ({error!r})"
        ) from error


def p1_forecast_scorecard(p: dict) -> str:
    """Appendix L, the table Amendment 23, rule 6, names "Frozen forecast scorecard".

    Every gain is a registered contrast (S2 of Amendment 8; the two read-outs of E31c) and every
    error is the arm error behind one of them; the table computes no statistic and selects no row.
    Gate G23e: it is printed only if the count of newcomers, the two arms and the two errors of
    each contrast agree with the score record (``p1_scorecard_check``, run when the score record
    is loaded; the arms are checked here as well).
    """
    p1_scorecard_arms_check(p)
    n, errors = p["n_scored"], p1_scorecard_errors(p)
    published = p["published_table_arm"]

    def gain(c):
        return f"{num(c['difference'], sign=True)} {interval(p1_ci(c))}"

    header = ["Forecast", "Mean absolute error", "Gain over destination only"]
    rows = [["Destination only", num(errors[P1_SCORECARD_DESTINATION]), "—"]]
    aware_row = [
        "League-aware",
        num(errors[P1_SCORECARD_AWARE]),
        gain(p["secondary"]["S2"]),
    ]
    if published["status"] == "read":
        header.append("Gain over 2015 table")
        rows[0].append("—")
        rows.append(
            [
                "2015 table",
                num(errors[P1_SCORECARD_TABLE]),
                gain(published["table_vs_destination_only"]),
                "—",
            ]
        )
        aware_row.append(gain(published["league_aware_vs_table"]))
    rows.append(aware_row)
    caption = (
        f"**Frozen forecast scorecard.** The same {n:,} eligible newcomers contribute to each error "
        "and paired gain (EFF/36); the errors and gains are unweighted. A positive gain means the row forecast "
        "reduced mean absolute error. Brackets give unadjusted 95% intervals for paired differences."
    )
    if published["status"] == "not_registered_in_time":
        caption += " The 2015 forecast was not registered in time."
    return caption + "\n\n" + md_table(header, rows)


def p1_scoring_detail(p: dict, status: str) -> list:
    """Appendix L after scoring: who was scored, what could be detected, every read-out."""
    j, pre = p["join"], p["pre_read"]
    counts = pre["counts_by_reason"]
    out = []
    lost = p.get("possible_lost_targets", [])
    names = (
        " ("
        + "; ".join(
            f"{r['player_display_name']} of {r['club']}, close to {r['frozen_name']} in the frozen file"
            for r in lost
        )
        + ")"
        if lost
        else ""
    )
    out.append(
        f"**Who was scored.** By {META['p1_cutoff']}, {j['newcomers_reaching_eight_games']} players had reached eight "
        f"continental games without a qualifying 2025–26 continental season. {j['joined']} have a frozen forecast "
        f"under their name and {j['unjoined']} do not; those are listed by name, club and previous club in the "
        f"scoring files, and no name was joined by hand. {j['possible_lost_targets']} of them may be players in the "
        f"frozen file under another spelling{names}: {pct(j['possible_lost_share_of_joined'])} of the joined newcomers, "
        f"against a limit of {pct(j['threshold'], 0)} registered in advance [@amend8]. That count is a lower bound. "
        f"{counts['source_rate_not_positive']} joined newcomers were left out because last season's domestic "
        f"rate was not positive, {counts['outcome_rate_not_positive']} because the 2026–27 rate was not positive, "
        f"and {counts['forecast_missing']} because a forecast was missing. {pre['n_scored']} newcomers were scored."
    )
    e, noise = pre["detectable_effects"], pre["expected_noise"]
    if pre["n_scored"]:
        out.append(
            "**Printed before any contrast was read.** "
            f"At {pre['n_scored']} newcomers the detectable effects were {num(e['P-a']['detectable_80'])} EFF/36 for "
            f"translation's gain over history, {num(e['P-b']['detectable_80'])} for the league-aware forecast against "
            f"history plus translation, {num(e['P-c']['detectable_80'])} for translation's increment, "
            f"{num(e['S1']['detectable_80'])} for the league-aware forecast against history alone and "
            f"{num(e['S2']['detectable_80'])} for the league-aware forecast against the destination-only forecast; "
            "all are optimistic for part-season outcomes. The newcomers had played a median of "
            f"{pre['games']['median']:g} games. At their game counts the expected noise in one newcomer's EFF/36 is "
            f"{num(noise['at_realised_games']['noise_sd'])} (standard deviation), against "
            f"{num(noise['full_season_674']['noise_sd'])} for a full season of the 2020–2025 arrivals."
        )
    if status == "not_adjudicable" or not p.get("contrasts_printed"):
        return out
    if status == "scored":
        if P1_FIGURE_READY:
            out.append(p1_figure_bands(p))
        out.append(p1_forecast_scorecard(p))
    s, comp = p["secondary"], p["complete_source"]
    rows = []
    for key, name in (
        *((k, v[0]) for k, v in P1_CONTRASTS.items()),
        *P1_SECONDARY.items(),
    ):
        plain = p["all"][key] if key in p["all"] else s[key]
        weighted = s["S5"][key]
        # Amendment 26, rule 6: where no sentence is licensed the weighted value carries a label,
        # not the registered reading "not clearly above zero when weighted by playing time"
        lead = (
            P1_WORDING[("S5", "includes_zero")]
            if weighted["reading"] == "includes_zero" and status == "scored"
            else P1_WEIGHTED_LABEL
        )
        rows.append(
            f"{name}, {p1_cell(plain)}; {lead}, {p1_cell(weighted)}; "
            f"complete-source leagues only, {p1_cell(comp[key])}"
        )
    label = (
        "**Every contrast, three ways.**"
        if status == "scored"
        else "**The contrasts on the newcomers that could be scored (no sentence is licensed).**"
    )
    out.append(
        f"{label} Unweighted, weighted by destination minutes, and for the {comp['n']} newcomers whose source "
        "league has a complete 2025–26 season (the registered sensitivity): "
        + ". ".join(r[0].upper() + r[1:] for r in rows)
        + "."
        + p1_table_values(p, status)
    )
    level = s["S3"]
    same = s["S4"]["same"]
    # Amendment 8, rule 3: in a state that is not scored "no licence sentence is used". The
    # sentences of S3 and S4 ("the frozen forecasts ran X below what newcomers delivered", "ordered
    # X% of cross-league pairs correctly", "not detectable at this n") are licence sentences, so
    # there the same values are printed as values. Until 25 November 2026 this paragraph printed
    # the sentences in every state; found in the read of the real, inconclusive paper.
    if status == "scored":
        head = f"**Forecast level and ordering, in full.** {p1_level_sentence(p)} {p1_order_appendix(p)} "
        ordering = ""
    else:
        head = P1_LEVEL_ORDER_RECORD + " "
        ordering = " " + p1_order_values(p)
    out.append(
        head
        + "Mean of forecast minus outcome: "
        + "; ".join(
            f"{P1_ARM_NAMES[arm]} {num(level[arm]['mean_signed_error'], sign=True)} EFF/36 (95% interval {interval(level[arm]['ci95'])})"
            for arm in ("source_ridge_10", "history_only", "scheduled_history")
        )
        + f".{ordering} On pairs from the same source league the league-aware forecast ordered {pct(same['league_aware']['share_correct'])} "
        f"correctly and history alone {pct(same['history']['share_correct'])} ({same['unequal_pairs']:,} pairs)."
    )
    feb = p["february_only_descriptive"]
    cover = feb["band_coverage"]
    bins = "; ".join(
        f"{g['gap_eff36']} EFF/36, {pct(g['share_correct'])} of {g['pairs']:,} pairs"
        for g in feb["gap_guide"]
        if g["pairs"]
    )
    out.append(
        "**Registered for the February re-score, descriptive here.** The "
        f"{pct(cover['80']['nominal'], 0)} and {pct(cover['95']['nominal'], 0)} error bands (half-widths "
        f"{num(cover['80']['half_width'], 2)} and {num(cover['95']['half_width'], 2)} EFF/36, fixed before scoring "
        "from the errors on all arrivals of 2020–2025; they are single bands and differ from the averages over yearly "
        "bands given for the examined seasons) "
        f"contained {pct(cover['80']['coverage'])} and {pct(cover['95']['coverage'])} of the scored newcomers. "
        f"Share of pairs in which the higher league-aware forecast had the higher outcome, by forecast gap: {bins}. "
        "No statement is licensed by these values in November [@amend8]."
    )
    return out


P1_DESIGN_POINTER = (
    "Appendix L gives the rule for a failure to replicate and what the test can detect."
)
P1_DESIGN_POINTER_PAST = "Appendix L gives the rule for a failure to replicate and what the test could detect."


def p1_design(d) -> str:
    """The failure rule and what the test can detect, in the main text while the test is pending
    (Amendment 19, rule 11: they MAY move, with a pointer). Once the test is scored, Amendment 19,
    rule 12, prints the power figures and the failure rule's text in Appendix L, so the main text
    then keeps the pointer; the registered verdict says there what a non-failure means."""
    if p1_check(d) == "inconclusive":
        return P1_DESIGN_POINTER_PAST  # Amendment 26, rule 3
    if p1_check(d) != "pending":
        return P1_DESIGN_POINTER
    power = power_table(d["prereg"])
    _, h100, h150 = power["history vs history + translation"]
    _, i100, i150 = power["offsets λ10 vs + translation"]
    return (
        f"At 100–150 newcomers the test can detect an increment of about {i150:.3f}–{i100:.3f} EFF/36 and a gain "
        f"over history of {h150:.3f}–{h100:.3f}; the second is larger than the "
        f'{num(p1_anchor(d)["history_gain"])} it looks for, so a null there would mean "not detectable", and '
        "both figures are optimistic for a part-season. A contrast fails to replicate if its interval excludes "
        "its 2020–2025 estimate and its own estimate has the opposite sign; for the gain over history its "
        "interval must also exclude zero [@amend8]. A test that does not fail will be reported as a pattern that "
        "held within this test's power, not as equivalence or as confirmation of each direction (Appendix L)."
    )


#: Amendment 29, rule 3: the read-out of the 2015 table on the frozen test (Amendment 15, E31c) is
#: named in the main text and its two values are printed in Appendix L, as values, in a state that
#: is not scored (in the scored state the registered sentences and the scorecard carry them).
P1_TABLE_FILE_NOTE = (
    "A read-out of a forecast built on a league table printed in 2015 [@vashro2015], frozen in a second "
    "file, was registered on 17 November 2026 [@amend15]; Appendix L prints it."
)
#: Amendment 29, rule 2: who a newcomer is, said once in the main text.
P1_NEWCOMER_DEFINITION = (
    f"A newcomer is a player with at least eight continental games by {META['p1_cutoff']} and no qualifying "
    "continental season in 2025–26 (at least eight games); he has a frozen forecast only if he played 2025–26 in one of the ten leagues."
)
P1_TABLE_VALUE_NAMES = (
    (
        "table_vs_destination_only",
        "the forecast built on the 2015 table against the forecast that knows only the destination",
    ),
    (
        "league_aware_vs_table",
        "the league-aware forecast against the forecast built on the 2015 table",
    ),
)
#: Amendment 30: the forecast that a value above zero favours, by the score record: the one the
#: paper names first in each contrast of the paragraph.
P1_TABLE_VALUE_FIRST = {
    "table_vs_destination_only": "published_table_vashro_2015",
    "league_aware_vs_table": "source_ridge_10",
}
P1_CONTRAST_FIRST = {
    ("all", "P-a"): "scheduled_history",
    ("all", "P-b"): "source_ridge_10",
    ("all", "P-c"): "source_ridge_10_scheduled",
    ("secondary", "S1"): "source_ridge_10",
    ("secondary", "S2"): "source_ridge_10",
}


def p1_table_values(p: dict, status: str) -> str:
    """Amendment 29, rule 3: the two read-outs of Amendment 15 (E31c), printed as values beside the
    other contrasts where no sentence is licensed. Amendment 15: 'every number is reported whatever
    it shows'."""
    arm = p["published_table_arm"]
    if status == "scored" or arm["status"] != "read":
        return ""
    for key, _ in P1_TABLE_VALUE_NAMES:
        c = arm[key]
        if c.get("weighting") != "unweighted" or c["n"] != p["n_scored"]:
            raise ClaimError(
                f"P1: the read-out {key} is not the unweighted one on the scored newcomers"
            )
        # Amendment 30: the sign is said in words, so it is checked on the record
        if c.get("positive_favours") != P1_TABLE_VALUE_FIRST[key]:
            raise ClaimError(
                f"P1: a value above zero of the read-out {key} does not favour the forecast named first"
            )
    for (block, key), first in P1_CONTRAST_FIRST.items():
        if p[block][key].get("positive_favours") != first:
            raise ClaimError(
                f"P1: a value above zero of {key} does not favour the forecast named first"
            )
    cells = "; ".join(
        f"{name}, {p1_cell(arm[key])}" for key, name in P1_TABLE_VALUE_NAMES
    )
    return (
        " The read-out of the forecast built on a league table printed in 2015, registered on 17 November 2026 "
        f"with a second frozen file [@amend15], exists unweighted only, on the {p['n_scored']} scored newcomers: "
        f"{cells}. In every contrast of this paragraph a value above zero favours the forecast named first (for "
        "translation's gain and translation's increment, the forecast with translation)."
    )


def p1_section(d) -> str:
    status = p1_check(d)
    fz = d["freeze"]
    rows = get(fz, "rows") if isinstance(fz.get("rows"), int) else fz.get("n_rows")
    base = (
        "We froze forecasts from every model for all 2025–26 domestic player-seasons, for both "
        f"competitions ({rows:,} rows, each with the forecasts of every model), and committed and pushed them on {META['freeze_time']}, "
        "after the season had begun but before any 2026–27 statistic was read [@prereg]. "
        f"They are scored on continental games through {META['p1_cutoff']}, for newcomers who reach "
        "eight games; below 60 newcomers the test is descriptive only. The registered directions were that translation "
        "helps against history, that the league-aware forecast is at least as good as history plus translation, and "
        "that translation adds nothing to it. Five secondary read-outs were registered "
        "on 16 November 2026, after the freeze and before scoring [@amend8]. Two of them test the league numbers "
        "themselves: the league-aware forecast against the forecast that knows only the destination, and the "
        "ordering of cross-league pairs. As registered, we do not expect the first to be detectable in November: "
        f"it looks for an effect near {e28_674(d)['e28_gd']} EFF/36, its 2020–2025 estimate. Equivalence is never "
        "claimed from this test. "
        + P1_TABLE_FILE_NOTE
        + " "
        + P1_NEWCOMER_DEFINITION
        + " "
        + p1_design(d)
    )
    late = (
        "For the conference presentation, the same frozen file will be re-scored on games through "
        f"{META['p1_late_cutoff']}, a re-score registered before any 2026–27 statistic was read [@amend1]; it is "
        "reported beside this test, never in place of it."
    )
    p = d["p1"]
    if status == "pending":
        result = "**[P1 RESULTS PENDING: scoring is scheduled from 25 November 2026.]**"
    elif status == "inconclusive":
        # Amendment 26, rule 3: the outcome first, then the design with the verbs of the November
        # scoring in the past, then the re-score of February
        for old, new in P1_PAST_TENSE:
            if base.count(old) != 1:
                raise ClaimError(
                    f"Amendment 26, rule 3: the design paragraph lacks '{old}'"
                )
            base = base.replace(old, new)
        return "\n\n".join([p1_inconclusive(p), base, late])
    elif status == "not_adjudicable":
        result = (
            f"By {META['p1_cutoff']} only {p['n_scored']} newcomers had reached eight continental games, fewer than the "
            f"{p['min_n']} we required in advance. The frozen test is therefore not adjudicable at this date: we report "
            "its size and do not read its contrasts. "
            + p1_descriptive(p)
            + (" " + p1_postponed(p) if p1_postponed(p) else "")
            + (" " + p1_e32_pointer(d) if p1_e32_pointer(d) else "")
        )
    else:
        verdict = p["verdicts"]
        failed = [k for k, v in verdict.items() if v == "fails"]
        tail = (
            "None triggers the registered failure-to-replicate rule: **the pattern held on unseen 2026-27 forecasts, "
            "within this test's power.** This does not establish equivalence or confirm each direction; "
            "intervals spanning zero remain inconclusive about that direction."
            if not failed
            else "Failure to replicate: "
            + ", ".join(P1_CONTRASTS[k][0] for k in failed)
            + " excluded the 2020–2025 estimate in the opposite direction. We report this prominently and do not "
            "read the 2020–2025 result as confirmed."
        )
        earlier = p1_excludes_earlier(d)  # Amendment 25, rule 4
        result = (
            f"On {p['n_scored']} newcomers scored by {META['p1_cutoff']}, "
            + "; ".join(p1_primary_parts(p, verdict, earlier))
            + ". "
            + tail
            + (" " + p1_postponed(p) if p1_postponed(p) else "")
            + (
                " " + P1_FIGURE_POINTER.format(number=P1_FIGURE_NUMBER)
                if p1_figure_printed(d)
                else ""
            )
            + "\n\n"
            + p1_secondary(p, earlier)
            + (" " + p1_e32_pointer(d) if p1_e32_pointer(d) else "")
        )
        # Gate G18b, on the text: a record that triggers a registered failure
        # sentence is never rendered without that sentence and its caveat.
        for key in p1_rule5_keys(p):
            if p1_rule5_sentence(key, p) not in result:
                raise ClaimError(
                    f"P1: the sentence registered for {key} below its bar is missing from "
                    "the text (Amendment 18, rule 5)"
                )
    named = named_pairs_block(d)  # Amendment 20, rule 1 (and gate G20b)
    figure = p1_figure_block(
        d
    )  # Amendment 25, rule 1: before the table of five named pairs
    return "\n\n".join(
        [base, result, *([figure] if figure else []), *([named] if named else []), late]
    )


# ---------------------------------------------------------------- appendix
def appendix(d) -> str:
    v9, v10, prep, sup = d["v9"], d["v10"], d["prep"], d["support"]
    n = v10["target_n"]

    def ref(pool, src="v9"):
        return (v9 if src == "v9" else v10)["variants"][pool]["scenarios"]["reference"]

    fb = {p: ref(p)["fallbacks"] for p in POOLS}
    seasonm = sup["controls"]["season_count"]["support"]["nonfallback"]
    cellm = sup["controls"]["cell_season_count"]["support"]["nonfallback"]
    hist_v = [
        ref(p)["contrasts"]["original_vs_history_only"]["player_club_season"][
            "difference"
        ]
        for p in POOLS[1:]
    ]
    aware = []
    for p in POOLS[1:]:
        aware += [
            ref(p)["contrasts"][f"source_ridge_{k}_increment"]["player_club_season"][
                "difference"
            ]
            for k in (1, 10, 100)
        ]
        aware += [
            ref(p, "v10")["contrasts"][f"cell_slope_{k}_increment"][
                "player_club_season"
            ]["difference"]
            for k in (1, 10, 100)
        ]
    r = d["recipes"]
    pool_rows = []
    for pool, name in (
        ("B", "Verified identity, full season"),
        ("C", "Verified, overlap keys"),
        ("D", "Verified, overlap-window rates"),
    ):
        i = get(
            r,
            f"results/{pool}/R1/ladder/source_ridge_10->source_ridge_10_scheduled/player_club_season",
        )
        h = get(
            r,
            f"results/{pool}/R1/ladder/history_only->scheduled_history/player_club_season",
        )
        c = (
            get(r, f"results/{pool}/R1/head_to_head/lambda_10/player_club_season")
            if "head_to_head" in get(r, f"results/{pool}/R1")
            else None
        )
        pool_rows.append(
            [
                name,
                f"{num(h['difference'], sign=True)} {interval(h['ci95'])}",
                f"{num(i['difference'], sign=True)} {interval(i['ci95'])}",
                f"{num(c['difference'], sign=True)} {interval(c['ci95'])}"
                if c
                else "—",
                f"{get(r, f'results/{pool}/R1/support/targets_destination_fallback')}",
            ]
        )
    rb = d["robust"]
    out_rows = []
    for o in ("O1", "O2", "O3", "O4"):
        c = lambda name: get(rb, f"e3/{o}/contrasts/{name}")  # noqa: E731
        out_rows.append(
            [
                OUTCOME_NAMES[o],
                f"{get(rb, f'e6/outcomes/{o}/spearman_brown_reliability'):.2f}",
                f"{num(c('history_gain')['difference'], sign=True)} {interval(c('history_gain')['player_club_season']['ci95'])}",
                f"{num(c('destination_increment')['difference'], sign=True)} {interval(c('destination_increment')['player_club_season']['ci95'])}",
                f"{num(c('offsets10_increment')['difference'], sign=True)} {interval(c('offsets10_increment')['player_club_season']['ci95'])}",
            ]
        )
    a_text = (
        "### A. Identity verification and factor support\n\n"
        f"The submitted abstract also reported what happens when the factor-estimation pairs are restricted to players whose identity, club and appearance dates could be verified. Verification cuts estimation pairs from {prep['counts']['official_corrected']:,} to {prep['counts']['verified_same_club_full']:,}, and forecasts with a supported league-pair factor (rather than the destination average) from {n - fb['official_corrected']} of {n} ({pct((n - fb['official_corrected']) / n)}) to {n - fb['verified_same_club_full']} ({pct((n - fb['verified_same_club_full']) / n)}; {n - fb['overlap_keys_full']} with overlap trimming). "
        f"With verified factors the gain over history shrinks to {num(min(hist_v))}–{num(max(hist_v))}, and every increment over a forecast that knows both leagues is negative, at each of the three penalties and with pair-specific slopes ({num(min(aware))} to {num(max(aware))}; Table A1 shows the primary penalty). "
        f"Random restrictions of the full pool to the same number of pairs, registered after this loss was seen, keep a median of {seasonm['median']:.0f} (season-matched) and {cellm['median']:.0f} (also league-pair-matched, maximum {cellm['maximum']:.0f}) supported forecasts. Comparable support loss is therefore attainable without verification; this diagnostic does not establish that sample loss caused the verification result. "
        "Table A1 repeats the head-to-head on the verified pools: there the league-aware forecast is more accurate than history plus translation, and most translated features fall back to the destination average.\n\n"
        "Table A1. The submitted recipe on the verified factor pools (EFF/36, 95% intervals).\n\n"
        + md_table(
            [
                "Factor pool",
                "Gain vs history",
                "Increment vs league-aware",
                "League-aware vs history + translation",
                "Forecasts on fallback",
            ],
            pool_rows,
        )
    )
    b_text = (
        "\n\n### B. Results by outcome\n\nTable A2. Translation's gain and increments by outcome (outcome units per 36 minutes, or per 100 possessions; 95% intervals). Reliability is the full-season split-half reliability of the outcome.\n\n"
        + md_table(
            [
                "Outcome",
                "Reliability",
                "Gain vs history",
                "Increment vs destination-only",
                "Increment vs league-aware (λ = 10)",
            ],
            out_rows,
        )
    )
    au = get(d["audit"], "e13")
    a_text += (
        f"\n\nThe Amendment 1 audit drew {au['n']} of the {get(d['audit'], 'frame_pairs'):,} unverified estimation pairs with a "
        f"fixed seed and classed each by rules fixed before any class was computed (name, birthdate, shared-roster club "
        f"identity, schedule feasibility). Rule-based classes: {au['rule_counts']['CONFIRMED']} confirmed, "
        f"{au['rule_counts']['UNRESOLVED']} unresolved, {au['rule_counts']['WRONG']} wrong; after a recorded hand review of the "
        f"unresolved pair: {au['final_counts']['CONFIRMED']} confirmed, {au['final_counts']['UNRESOLVED']} unresolved, "
        f"{au['final_counts']['WRONG']} wrong (Wilson 95% interval for the wrong share {pct(au['wrong_wilson95'][0])} to "
        f"{pct(au['wrong_wilson95'][1])})."
    )
    a25 = d["audit25"]
    n25, p25, k25 = (get(a25, f"e25/{k}") for k in ("new", "pooled", "descriptive"))
    a_text += (
        f"\n\nBecause that upper bound sat just above the registered 5% bar, Amendment 5 [@amend5] added a second look: a "
        f"fresh sample of {n25['n']} pairs from the {get(a25, 'frame_pairs'):,} not drawn before, with the same checks and "
        f"rules. Of these, {n25['confirmed']} were confirmed, {n25['unresolved']} unresolved and {n25['wrong']} wrong "
        f"(Wilson 95% interval {pct(n25['wrong_wilson95'][0])} to {pct(n25['wrong_wilson95'][1])}); pooled with the first "
        f"sample, {p25['wrong']} of {p25['n']} (interval {pct(p25['wrong_wilson95'][0])} to {pct(p25['wrong_wilson95'][1])}). "
        f"Of the {n25['wrong']} wrong pairs, {k25['wrong_other']} are contradicted by club or schedule records, and "
        f"{k25['wrong_birthdate_only']} are contradicted only by birthdate while the club and schedule checks agree; they "
        "stay wrong because the rule was fixed in advance. The bound quoted in Limitations is the larger of the new-sample and pooled bounds, the new sample had to "
        "pass on its own because this was a second look, and no third look is allowed. Both audits are exploratory and cover "
        "estimation pairs, not forecast arrivals."
    )
    a26 = d["audit26"]
    n26, by26, g26 = (
        a26["class_counts"],
        a26["confirmed_by"],
        get(a26, "gates/G26d_previous_team"),
    )
    s2, s3 = e26_subset(a26, "S2"), e26_subset(a26, "S3")
    if not all(c["holds"] is True for sub in (s2, s3) for c in sub.values()):
        raise ClaimError(
            "an E26 reading on S2 or S3 changed; reword it as not detectable at that n"
        )
    a_text += (
        f"\n\nAmendment 6 [@amend6] therefore audited the forecast arrivals themselves: all {a26['n_arrivals']}, by rules "
        "fixed in advance and with no hand review. An arrival is confirmed when independent evidence links the domestic "
        f"record to the continental player: the two birthdates agree ({by26['birthdate agrees']} arrivals); the same player "
        f"appears in continental play in the source season ({by26['source-season bridge']}) or is still at the source club a "
        f"year later ({by26['stayed at the source club']}), each checked as in the first audit; or the previous club in the "
        f"competition's own registration list is the source club ({by26['previous team matches a source club']}). An arrival "
        f"can meet several of these conditions. The last rule is a text match and passed its registered check: it matched {g26['matches']} of "
        f"{g26['n']} arrivals, against {g26['matches_after_shuffle']} after a seeded shuffle of the lists. Of these "
        f"{g26['matches']}, {by26['previous team matches a source club']} are confirmed arrivals (the count given above); "
        f"the other {g26['matches'] - by26['previous team matches a source club']} are classed wrong on other evidence. "
        "An arrival is wrong "
        "when the two birthdates disagree, when club or schedule records contradict the link, or when two registered "
        f"players stand behind the destination record. Result: {n26['CONFIRMED']} confirmed, {n26['WRONG']} wrong, {n26['UNRESOLVED']} unresolved, and "
        f"{n26['NAME ONLY']} name only: the destination player is one identified person and no namesake is visible, but "
        "nothing independent links him to the source record. Without the wrong arrivals the three comparisons keep their "
        f"readings (Table A18). They also keep them without the unresolved (n = {s2['history_gain']['n']}) and on confirmed "
        f"arrivals alone (n = {s3['history_gain']['n']}: translation vs history {cell(s3['history_gain'])}, league-aware vs "
        f"history + translation {cell(s3['e1_head_to_head'])}, translation added {cell(s3['offsets10_increment'])}), a "
        "stricter subset that is not a typical sample of signings. The audit cannot see a namesake who left the covered "
        "leagues, removes arrivals from scoring without refitting any model, and does not cover career histories or "
        "training arrivals. It is exploratory."
    )
    c_text = (
        "\n\n### C. Robustness forest\n\n"
        "![Figure A1. What translation adds once the forecast knows both leagues, across factor recipes, outcomes, "
        "competitions, seasons and age-aware models, as a percentage of the league-aware forecast's error "
        "(league numbers, λ = 10). Points: estimates; bars: 95% intervals. The shaded band marks ±2%, the registered "
        "margin (descriptive for the submitted recipe, the first row, whose interval had been seen). The boosted model (Appendix E, Table A5; discussed in Appendix J) is not in this panel; its upper bound is above 2%.](figures/figA1_robustness.png)"
    )
    pooled = [
        row
        for row in d["retention"]
        if row["subset_type"] == "pooled" and row["subset"] == "all"
    ]
    ret_rows = [
        [
            row["label"],
            f"{float(row['retention']):.3f} [{float(row['ci_low']):.3f}, {float(row['ci_high']):.3f}]",
            f"{float(row['ratio_of_sums']):.3f} [{float(row['ratio_of_sums_ci_low']):.3f}, {float(row['ratio_of_sums_ci_high']):.3f}]",
            f"{int(row['n_used']):,}",
        ]
        for row in pooled
    ]
    car_rows = [
        [
            row["label"],
            row["n"],
            f"{float(row['r']):.2f}",
            f"{float(row['reliability']):.2f}",
            f"{float(row['r_disattenuated']):.2f} [{float(row['r_disattenuated_ci_low']):.2f}, {float(row['r_disattenuated_ci_high']):.2f}]"
            + (" (unreadable)" if float(row["reliability"]) < 0.40 else ""),
        ]
        for row in d["carryover"]
    ]
    robust, sensitive = robust_licences(d)
    d_text = (
        "\n\n### D. Which skills travel\n\n"
        "Table A3. Same-season retention (continental rate ÷ domestic rate for the same player in the same season; "
        "below 1 = he does less of it against continental opponents). The registered estimator averages each pair's "
        "ratio, weighted by the smaller of the player's two minute totals (attempts for percentages); the ratio of sums is an unregistered "
        f"sensitivity check. Of the {len(robust) + len(sensitive)} registered comparisons whose registered intervals do not "
        f"overlap, {len(robust)} keep the same order with intervals that do not overlap under the ratio of sums.\n\n"
        + md_table(
            [
                "Component",
                "Retention, registered [95% CI]",
                "Ratio of sums [95% CI]",
                "Pairs used",
            ],
            ret_rows,
        )
        + "\n\nTable A4. Carry-over for arrivals: correlation of domestic and continental rates, the destination "
        "reliability of one continental season, and the correlation corrected for that noise (disattenuated). "
        "Reliability below 0.40 makes the corrected value unreadable.\n\n"
        + md_table(
            ["Component", "n", "Raw r", "Reliability", "Disattenuated r [95% CI]"],
            car_rows,
        )
    )
    fx, sv = d["flex"], d["surv"]
    labels = get(fx, "labels")
    fred = get(fx, "reducible/models")
    flex_rows = []
    names = {
        "history_only": "History only",
        "scheduled_history": "History + translation",
        "source_ridge_10": "One number per league (λ = 10)",
        "source_ridge_10_scheduled": "One number per league + translation",
        "ridge": "Ridge, all 30 features",
        "ridge_z": "Ridge, all 30 features + translation",
        "gbm": "Boosted trees, all 30 features",
        "gbm_z": "Boosted trees, all 30 features + translation",
    }
    if get(fx, "n_features_primary") != 30 or not all(
        a in labels for a in ("gbm", "gbm_z", "ridge", "ridge_z")
    ):
        raise ClaimError("Table A5 names 30-feature models")
    for arm, name in names.items():
        mae = fred[arm]["mae"]
        flex_rows.append(
            [
                name,
                num(mae),
                "0% (reference)"
                if arm == "history_only"
                else f"{pct(fred[arm]['share_of_reducible_removed'])} [{pct(fred[arm]['ci95_percentile'][0])}, {pct(fred[arm]['ci95_percentile'][1])}]",
            ]
        )
    prof = get(sv, "e14a/profile")
    prof_rows = []
    for key, label in (
        ("anchor_8_plus", "8+ continental games (benchmark)"),
        ("short_1_to_7", "1–7 continental games"),
    ):
        p = prof[key]
        prof_rows.append(
            [
                label,
                f"{p['n']}",
                f"{p['source_eff36']['median']:.1f}",
                f"{p['source_min_per_game']['median']:.1f}",
                f"{p['destination_games']['median']:.0f}",
                f"{p['destination_min_per_game']['median']:.1f}",
                f"{p['destination_eff36']['median']:.1f}",
            ]
        )
    tl = get(sv, "e14c/all_arrivals_1_plus/ladder")
    t_gain = get(sv, "e14c/all_arrivals_1_plus/contrasts/offsets10_gain_over_history")
    t_rows = [
        [name, num(tl[arm]["mae"], 4)]
        for arm, name in (
            ("history_only", "History only"),
            ("scheduled_history", "History + translation"),
            ("history_destination", "History + destination"),
            ("source_ridge_10", "League-aware (one number per league, λ = 10)"),
            ("source_ridge_10_scheduled", "League-aware + translation"),
        )
    ]
    e_text = (
        "\n\n### E. Flexible model and survivorship\n\n"
        "Table A5. The flexible-model comparison (Amendment 1, E16): walk-forward MAE (EFF/36) on the same "
        f"{get(fx, 'n_targets')} arrivals and the estimated reducible-error share under the normal-noise reference (Appendix J), with 95% cluster-bootstrap intervals. "
        f"The boosted model uses fixed hyperparameters (no tuning) and {get(fx, 'n_features_primary')} features. "
        "One number per league against the boosted model: MAE difference {{gbm_diff}} (interval {{gbm_diff_lo}} to "
        "{{gbm_diff_hi}}; negative = boosted model worse). The source club's win share adds {{club_inc}} to the ridge "
        "model (interval {{club_inc_lo}} to {{club_inc_hi}}).\n\n"
        + md_table(["Forecast", "MAE", "Avoidable error removed [95% CI]"], flex_rows)
        + "\n\nTable A6. Who the eight-game rule leaves out (Amendments 1 and 2, E14): medians.\n\n"
        + md_table(
            [
                "Arrivals",
                "n",
                "Domestic EFF/36",
                "Domestic min/game",
                "Continental games",
                "Continental min/game",
                "Continental EFF/36",
            ],
            prof_rows,
        )
        + f"\n\nTable A7. Forecasting playing time: MAE for the share of team minutes (1 = every minute), all {get(sv, 'e14b/all_arrivals_1_plus/n')} arrivals. The league-aware forecast's gain over history alone is {num(t_gain['difference'], 4)} (95% interval {num(t_gain['player_club_season']['ci95'][0], 4)} to {num(t_gain['player_club_season']['ci95'][1], 4)}).\n\n"
        + md_table(["Forecast", "MAE"], t_rows)
    )
    f_text = (
        "\n\n### F. Reproducibility\n\n"
        f"The full-paper analyses were pre-registered and the document pushed before any code was written ({META['prereg_time']}) [@prereg]. "
        f"Amendment 1 (analyses E10–E17 and the February re-score; commit {get(d['amend'], 'amendment_commit')[:7]}, {META['amend1_time']}) [@amend1], "
        f"Amendment 2 (the survivorship stint rule; commit {get(sv, 'amendment_2_commit')[:7]}, {META['amend2_time']}) [@amend2], "
        f"Amendment 3 (analyses E18–E23; commit {get(d['amend3'], 'amendment_commit')[:7]}, {META['amend3_time']}) [@amend3], "
        f"Amendment 4 (analysis E24; commit {get(d['amend4'], 'amendment_commit')[:7]}, {META['amend4_time']}) [@amend4], "
        f"Amendment 5 (analysis E25; commit {get(d['audit25'], 'amendment_commit')[:7]}, {META['amend5_time']}) [@amend5], "
        f"Amendment 6 (analysis E26; commit {get(d['audit26'], 'amendment_commit')[:7]}, {META['amend6_time']}) [@amend6] "
        f"and Amendment 7 (analysis E27; commit {get(d['older'], 'amendment_commit')[:7]}, {META['amend7_time']}) [@amend7] "
        "were each pushed alone, before the analyses they govern were run. Amendment 4 was written after the Amendment 3 results had been read, Amendment 5 after the first audit's result, Amendment 6 after both audits' results and Amendment 7 before any outcome of an older arrival was read; each says so. Later amendments that the paper cites are listed in the references. A gate reproduces every submitted number from the public data to within 10⁻⁹ before any new analysis runs. "
        "Every table and figure in this paper is generated by a committed script from saved results of retained runs; the repository records input, code and output hashes for each. "
        f"The 2026–27 forecasts were frozen on {META['freeze_time']}, file sha256 `{d['freeze'].get('forecast_sha256', d['freeze'].get('sha256', ''))[:16]}…`. "
        "The player vignettes were chosen by a rule fixed before any error was read."
    )
    return a_text + b_text + c_text + d_text + e_text + f_text


# ---------------------------------------------------- tables: Amendments 3, 4
def table_gaps(d) -> str:
    """Table A25 (Appendix H): ordering accuracy by size of the forecast gap (E20)."""
    rows = sorted(
        (r for r in get(d["amend3"], "e20/bins") if r["arm"] == A3_O),
        key=lambda r: r["bin"],
    )
    primary = [r for r in rows if r["pair_type"] == "all"]
    cross = {r["bin"]: r for r in rows if r["pair_type"] == "cross"}
    total = sum(r["pairs"] for r in primary)
    body = [
        [
            r["gap_eff36"],
            f"{r['pairs']:,}",
            f"{pct(r['share_correct'])} [{pct(r['ci95_low'])}, {pct(r['ci95_high'])}]",
            pct(cross[r["bin"]]["share_correct"]),
        ]
        for r in primary
    ]
    caption = (
        "Table A25. How far to trust a forecast gap. Over every pair of arrivals in the same competition and season "
        f"({total:,} pairs), the share in which the player with the higher league-aware forecast had the higher realised "
        "EFF/36, by the size of the gap between the two forecasts (95% cluster-bootstrap intervals; bins fixed in advance)."
    )
    return (
        caption
        + "\n\n"
        + md_table(
            [
                "Forecast gap (EFF/36)",
                "Pairs",
                "Higher forecast was better",
                "… cross-league pairs only",
            ],
            body,
        )
    )


def appendix_v3(d) -> str:
    """Appendix H: Tables A9-A12 for Amendments 3 and 4."""
    a3, a4 = d["amend3"], d["amend4"]
    e18, e24 = get(a3, "e18"), get(a4, "e24")
    l18 = {r["source_league"]: r for r in e18["leagues"]}
    l24 = {r["source_league"]: r for r in e24["leagues"]}
    e11 = {row["source_league"]: row for row in d["e11"]}
    mix = {r["source_league"]: r for r in e24["destination_mix"]}
    reb = lambda r, arm: (  # noqa: E731
        f"{num(r[f'rebased_{arm}'], 2, sign=True)} [{num(r[f'rebased_ci95_low_{arm}'], 2)}, {num(r[f'rebased_ci95_high_{arm}'], 2)}]"
    )
    star = lambda r, arm: " *" if r.get(f"rebased_p_holm_{arm}", 1.0) < 0.05 else ""  # noqa: E731
    order = sorted(l24, key=lambda code: l24[code][f"rebased_{A3_D}"])
    bias_rows = [
        [
            LEAGUE_NAMES[code],
            f"{l24[code]['arrivals']}",
            pct(mix[code]["euroleague_share"], 0),
            num(float(e11[code]["signed_error_history_only"]), 2, sign=True)
            + (" *" if e11[code]["licence"] == "bias" else ""),
            reb(l18[code], A3_H) + star(l18[code], A3_H),
            reb(l24[code], A3_D) + star(l24[code], A3_D),
            reb(l18[code], A3_O),
        ]
        for code in order
    ]
    lvl = {(r["arm"], r["scope"]): r for r in e18["level"]}
    lvl4 = {(r["arm"], r["scope"]): r for r in e24["level"]}
    scopes = [s for arm, s in lvl if arm == A3_O]

    def name(s):
        if s == "all":
            return "All arrivals"
        kind, value = s.split(":")
        if kind == "destination":
            return {"euroleague": "EuroLeague", "eurocup": "EuroCup"}[value]
        return f"Season {value}–{str(int(value) + 1)[-2:]}"

    lev = lambda r: (  # noqa: E731
        f"{num(r['mean_signed_error'], 2, sign=True)} [{num(r['ci95_low'], 2)}, {num(r['ci95_high'], 2)}]"
    )
    level_rows = [
        [
            name(s),
            f"{lvl[(A3_O, s)]['n']}",
            lev(lvl[(A3_H, s)]),
            lev(lvl4[(A3_D, s)]),
            lev(lvl[(A3_O, s)]),
        ]
        for s in scopes
    ]
    fits = list(dict.fromkeys(row["fit"] for row in d["refits"]))
    wide = {
        (row["source_league"], row["fit"]): float(row["acb16_equivalent_eff36"])
        for row in d["refits"]
        if row["destination"] == "euroleague"
    }
    leagues = sorted(l24, key=lambda code: wide[(code, fits[-1])])
    head = [
        f.replace("refit for ", "").replace("full fit through 2025", "Full fit")
        for f in fits
    ]
    refit_rows = [
        [LEAGUE_NAMES[code], *[num(wide[(code, f)], 1) for f in fits]]
        for code in leagues
    ]
    cover = {
        (r["source_league"], round(r["level"], 2)): r for r in get(a3, "e22/leagues")
    }

    def cov(r):
        return f"{pct(r['coverage'])} [{pct(r['wilson95_low'])}, {pct(r['wilson95_high'])}]"

    cover_rows = [
        [
            LEAGUE_NAMES[code],
            f"{cover[(code, 0.8)]['n']}",
            cov(cover[(code, 0.8)]),
            cov(cover[(code, 0.95)]),
        ]
        for code in sorted(l24, key=lambda code: cover[(code, 0.8)]["coverage"])
    ]
    a = get(a3, "e23/a")
    m1, m2 = a["M1"], a["M2"]
    span = lambda ci, digits=2: f"[{num(ci[0], digits)}, {num(ci[1], digits)}]"  # noqa: E731
    e23_rows = [
        [
            "Registered model: flag",
            num(a["M0"]["flag"], 2, sign=True),
            "see Appendix K",
            "negative in every refit (Appendix K)",
        ],
        [
            "Flag, with the jump added",
            num(m1["flag"], 2, sign=True),
            span(m1["flag_ci95"]),
            f"{num(min(m1['walk_forward_flag']), 2)} to {num(max(m1['walk_forward_flag']), 2)}",
        ],
        [
            "Jump, per EFF/36 above history",
            num(m1["jump"], 2, sign=True),
            span(m1["jump_ci95"]),
            f"{num(min(m1['walk_forward_jump']), 2)} to {num(max(m1['walk_forward_jump']), 2)}",
        ],
        [
            "Jump replacing the flag",
            num(m2["jump"], 2, sign=True),
            span(m2["jump_ci95"]),
            f"{num(min(m2['walk_forward_jump']), 2)} to {num(max(m2['walk_forward_jump']), 2)}",
        ],
    ]
    return (
        "### H. Forecast level, league biases, table stability and error bands\n\n"
        "These tables come from Amendments 3 and 4 [@amend3; @amend4]. All are exploratory.\n\n"
        "Table A9. League biases (forecast minus actual EFF/36) by source league, with 95% cluster-bootstrap intervals. "
        "*Registered, against zero*: the history-only forecast's mean signed error as first registered (asterisk: detectable after Holm adjustment). "
        "The three *re-based* columns subtract the mean signed error of all arrivals, so they show each league against the average arrival; "
        "asterisks mark Holm-adjusted p < 0.05 across the ten leagues, tested for the first two forecasts. "
        "*History only* is blind to both leagues; *history + destination* knows the destination but not the source league; *league-aware* knows both.\n\n"
        + md_table(
            [
                "Source league",
                "Arrivals",
                "To EuroLeague",
                "Registered, against zero",
                "History only, re-based",
                "History + destination, re-based",
                "League-aware, re-based",
            ],
            bias_rows,
        )
        + "\n\nTable A10. Mean signed error (forecast minus actual EFF/36) of three forecasts, with 95% cluster-bootstrap intervals. Below zero, the forecast expected less than arrivals delivered.\n\n"
        + md_table(
            ["Arrivals", "n", "History only", "History + destination", "League-aware"],
            level_rows,
        )
        + "\n\nTable A11. The equivalent of an ACB 16 for EuroLeague arrivals in each yearly refit (the fit that forecast that season, using earlier seasons only) and in the full fit. "
        "The refits share most of their data: the table describes stability and is not a test.\n\n"
        + md_table(["Source league", *head], refit_rows)
        + gaps_grew(d)["gaps_grew_beside"]  # Amendment 26, rule 10
        + "\n\nTable A12. Error-band coverage by source league for the league-aware forecast, seasons 2021–2025, with Wilson 95% intervals.\n\n"
        + md_table(["Source league", "Arrivals", "80% bands", "95% bands"], cover_rows)
        + "\n\nTable A13. The above-average-season term. The jump is the source rate minus the earlier career rate when positive. "
        "The registered model keeps the flag alone; the other rows are sensitivity checks and are not used for any forecast in this paper.\n\n"
        + md_table(
            [
                "Coefficient",
                "Full fit through 2025",
                "95% interval",
                "Range over six refits",
            ],
            e23_rows,
        )
        + "\n\n"
        + e23_contrast_note(a)
    )


def e23_contrast_note(a: dict) -> str:
    """Amendment 3: a forecasting gain from the jump is reported as exploratory, not adopted."""
    wf = a["walk_forward_contrasts"]
    parts = []
    for key, label in (
        ("M1", "with the jump added"),
        ("M2", "with the jump replacing the flag"),
    ):
        c = wf[key]
        lo, hi = c["ci95"]
        if not lo <= 0 <= hi:
            raise ClaimError(
                f"the {key} forecasting contrast is detectable; Table A13's note needs new wording"
            )
        parts.append(
            f"{num(c['mae_variant'])} {label} (difference {num(c['difference_positive_favours_variant'], sign=True)}, "
            f"interval {num(lo)} to {num(hi)})"
        )
    return (
        "Walk-forward, the registered model misses by "
        f"{num(wf['M1']['mae_m0'])} EFF/36, against "
        + " and ".join(parts)
        + ". Neither difference is detectable, "
        "and the registered model is kept, as Amendment 3 requires."
    )


# ------------------------------------------------ E27: the older-seasons test
#: Amendment 7. The extract (scripts/sloan_fullpaper_older_seasons_paper.py) holds
#: only the version the paper may print: all three leagues if ACB's written
#: permission has arrived (docs/paper/ssac27/release.json), else without ACB.
OLDER_PROSE = {
    "acb": "Spain's ACB",
    "aba": "the ABA League",
    "israel": "Israel's Winner League",
}
OLDER_ROW = {"acb": "spain-acb", "aba": "aba-league", "israel": "israel-bsl"}
OLDER_ORDER = ("acb", "aba", "israel")
OLDER_COMPARISONS = ("history_gain", "e1_head_to_head", "offsets10_increment")
OLDER_ARMS = {
    "history_only": "History only",
    "scheduled_history": "History + translation",
    "source_ridge_10": "League-aware (one number per league)",
    "source_ridge_10_scheduled": "League-aware + translation",
}
OLDER_WORDS = {0: "none", 1: "one", 2: "two", 3: "three"}
INSIDE, WIDER = (
    "includes zero, inside the margin",
    "includes zero, wider than the margin",
)


def older(d) -> dict:
    """The E27 extract, after the checks every E27 sentence relies on."""
    o, flag = d["older"], "acb_written_permission"
    if o[flag] is not d["release"].get(flag) or o[flag] not in (True, False):
        raise ClaimError(
            "the E27 extract was made under another ACB permission state; re-run the extract"
        )
    if (
        o["printed_version"] != ("V-all" if o[flag] else "V-noACB")
        or ("acb" in o["leagues"]) != o[flag]
    ):
        raise ClaimError("the printed E27 version does not follow Amendment 7's rule")
    if not o[flag] and ("without_acb" in o or "selection" in o or "withheld" not in o):
        raise ClaimError("the E27 extract carries ACB results without permission")
    if any(g["status"] != "passed" for g in o["gates"].values()):
        raise ClaimError(
            "an E27 gate did not pass; the older-seasons test may not be printed"
        )
    runs = o["runs"]
    if (
        runs["freeze"] != "complete"
        or runs["score"] != "complete"
        or runs["outcomes_joined_at_freeze"] is not False
    ):
        raise ClaimError("the E27 order of events is not the registered one")
    if runs["score_stopped"] != {"status": "failed", "output_files": 0}:
        raise ClaimError("the stopped E27 scoring run is described as writing nothing")
    if set(o["by_league"]) != set(o["leagues"]):
        raise ClaimError("the E27 arrivals are not counted for the printed leagues")
    return o


def older_span(c: dict) -> str:
    return f"{num(c['ci95'][0])} to {num(c['ci95'][1])}"


def older_cell(c: dict) -> str:
    if c["difference"] is None:
        return "not estimable"
    # an interval end that rounds to a signed zero is printed with one more digit
    digits = 4 if any(0 < abs(x) < 0.0005 for x in c["ci95"]) else 3
    return f"{num(c['difference'], digits, sign=True)} {interval(c['ci95'], digits)}"


def older_leagues(o: dict, counts: bool = True) -> str:
    return join_names(
        [
            OLDER_PROSE[k] + (f" ({o['by_league'][k]})" if counts else "")
            for k in OLDER_ORDER
            if k in o["leagues"]
        ]
    )


def older_readings(o: dict) -> list:
    """One sentence per registered comparison, in Amendment 7's licensed words."""
    c = o["comparisons"]["all"]
    gain, e1, inc = (c[k] for k in OLDER_COMPARISONS)
    if gain["reading"] == "above zero":
        s1 = f"Translation's gain over history holds on seasons no model saw: {num(gain['difference'], sign=True)} EFF/36 (95% interval {older_span(gain)})."
    elif gain["reading"] == "includes zero":
        s1 = f"Translation's gain over history is not detectable at this n: {num(gain['difference'], sign=True)} EFF/36 (95% interval {older_span(gain)})."
    else:
        raise ClaimError(
            "E27: the gain over history failed on older seasons; this goes to Amir first"
        )
    margin = num(e1["margin"])
    if e1["reading"] == INSIDE:
        s2 = f"One number per league matches translation on seasons no model saw: the head-to-head difference is {num(e1['difference'], sign=True)} (interval {older_span(e1)}), inside the margin of {margin}."
    elif e1["reading"] == WIDER:
        s2 = f"Between the league-aware forecast and history plus translation no difference is detected, but the interval is wider than the margin ({num(e1['difference'], sign=True)}, interval {older_span(e1)}; margin {margin}), so the test cannot show a match at this n."
    else:
        raise ClaimError(
            "E27: the head-to-head excludes zero on older seasons; this goes to Amir first"
        )
    if inc["reading"] == INSIDE:
        s3 = f"Translation adds nothing detectable on seasons no model saw: {num(inc['difference'], sign=True)} on top of the league-aware forecast (interval {older_span(inc)})."
    elif inc["reading"] == WIDER:
        s3 = f"For translation added to the league-aware forecast no difference is detected, but the interval is wider than the margin ({num(inc['difference'], sign=True)}, interval {older_span(inc)})."
    else:
        raise ClaimError(
            "E27: translation's increment excludes zero on older seasons; reword with its direction"
        )
    return [s1, s2, s3]


def older_rare(o: dict) -> str:
    """The registered rare-surname sensitivity, printed beside the main result."""
    whole, rare = o["comparisons"]["all"], o["comparisons"]["rare surname"]
    n = rare[OLDER_COMPARISONS[0]]["n"]
    notes = []
    for k, label in zip(
        OLDER_COMPARISONS,
        (
            "the gain over history",
            "the head-to-head difference",
            "translation's increment",
        ),
        strict=True,
    ):
        a, b = whole[k]["reading"], rare[k]["reading"]
        if a == b:
            continue
        same_side = (whole[k]["difference"] > 0) == (rare[k]["difference"] > 0)
        if b in ("includes zero", WIDER):
            notes.append(f"{label} is not detectable at this n")
        elif b.startswith("excludes zero") and same_side and a in (INSIDE, WIDER):
            side = (
                "leaving translation out"
                if rare[k]["difference"] < 0
                else "adding translation"
            )
            notes.append(
                f"the interval of {label} just excludes zero, on the side of {side}"
            )
        else:
            raise ClaimError(
                f"E27: {k} changes on rare surnames; this goes to Amir first"
            )
    if not notes:
        tail = "the three readings are the same"
    else:
        kept = OLDER_WORDS[len(OLDER_COMPARISONS) - len(notes)]
        tail = (
            f"{kept} of the three readings {'is' if kept == 'one' else 'are'} the same, and "
            + " and ".join(notes)
        )
    return f"On the {n} arrivals with a rare surname, where the name link is safest, {tail} (Appendix Table A14)."


def wilson95(k: int, n: int) -> tuple:
    """The Wilson 95% interval of a share k of n."""
    z = 1.959963984540054
    share = k / n
    scale = 1 + z * z / n
    centre = (share + z * z / (2 * n)) / scale
    half = z * (share * (1 - share) / n + z * z / (4 * n * n)) ** 0.5 / scale
    return centre - half, centre + half


def older_link_weakness(d) -> str:
    """Amendment 7, "Measured weakness": where it can be measured (Israel), how often a link by
    initial and surname joins two different players. "The paper states this beside the E27
    result." The counts come from the committed gate record; the share and its interval are
    computed here and must be the ones the amendment registered."""
    k, n = older(d)["gates"]["G27d_linking"]["measured"]["all"]
    low, high = wilson95(k, n)
    measured = f"{pct(k / n)} of links ({k} of {n}; interval {pct(low)} to {pct(high)})"
    if measured not in d["amend7_text"]:
        raise ClaimError(
            "E27: the measured weakness of the name link is not the one Amendment 7 registered"
        )
    return (
        "Where it can be measured (Israel), a link by initial and surname joins two different players in "
        f"{measured}."
    )


def older_section(d) -> str:
    o = older(d)
    intro = (
        f"The same frozen models were also scored on seasons none of them saw [@amend7]: {o['n']} arrivals of 2008–09 "
        f"to 2015–16 from {older_leagues(o)}, built from the leagues' own box scores. The forecasts were fixed and "
        "their hash committed and pushed before any outcome was joined, and they were scored once."
    )
    if o["acb_written_permission"]:
        acb = o["comparisons"]["league: acb"]["history_gain"]
        if acb["reading"] != "above zero" or any(
            o["comparisons"][f"league: {k}"]["history_gain"]["reading"]
            != "includes zero"
            for k in ("aba", "israel")
        ):
            raise ClaimError(
                "E27: the gain over history is no longer carried by ACB arrivals alone"
            )
        extra = "By league, the gain over history comes from the ACB arrivals alone."
    else:
        w = o["withheld"]
        if (
            w["comparisons"] != len(OLDER_COMPARISONS)
            or not w["computed_in_the_same_runs"]
        ):
            raise ClaimError(
                "E27: the withheld version is not described by the extract"
            )
        extra = (
            "A version that includes Spain's ACB was computed in the same runs; it is withheld until ACB's written "
            f"permission arrives, not for its result, and its readings agree with these on "
            f"{OLDER_WORDS[w['readings_agree']]} of the {OLDER_WORDS[w['comparisons']]} comparisons."
        )
    scope = f"The test covers {OLDER_WORDS[len(o['leagues'])]} of the ten leagues (Limitations; Appendix I)."
    return " ".join(
        [
            intro,
            *older_readings(o),
            older_link_weakness(d),
            older_rare(o),
            extra,
            scope,
        ]
    )


def older_limits(d) -> str:
    o = older(d)
    low = o["mean_error"]["source_ridge_10"]
    if low >= 0:
        raise ClaimError(
            "E27: the league-aware forecast did not run low on older seasons"
        )
    text = (
        f"**Older-seasons test.** The test covers {OLDER_WORDS[len(o['leagues'])]} of the ten leagues and uses the "
        "leagues' own box scores, where the benchmark uses Proballers. The league numbers were estimated about ten "
        f"years later, and the league-aware forecast is {num(-low, 2)} EFF/36 below the outcomes. For "
        f"{pct(o['shares']['without_history'])} of arrivals no earlier season is on record, which can favour "
        "translation against history, and names are linked by initial, surname and the first three letters of the "
        "first name. A pass there is not proof for today's leagues, and a miss is not proof "
        "against them."
    )
    if o["acb_written_permission"]:
        by = {k: o["comparisons"][f"league: {k}"]["history_gain"] for k in OLDER_ORDER}
        rest = o["without_acb"]
        e1 = rest["comparisons"]["e1_head_to_head"]
        gain = rest["comparisons"]["history_gain"]
        if gain["reading"] != "includes zero" or e1["reading"] != WIDER:
            raise ClaimError(
                "E27: the readings without ACB changed; rewrite the Limitations sentence"
            )
        text += (
            f" Its gain over history comes from the ACB arrivals alone ({older_cell(by['acb'])}, n = {by['acb']['n']}); "
            f"for the ABA League and Israel it is {num(by['aba']['difference'], sign=True)} and "
            f"{num(by['israel']['difference'], sign=True)}, not detectable at those n. Without ACB (n = {rest['n']}) "
            f"the gain is {older_cell(gain)} and the head-to-head interval is wider than the margin "
            f"({older_cell(e1)}). This split is descriptive."
        )
    return text


def older_credit(d) -> str:
    o = older(d)
    return f"the older-seasons test uses box scores from the websites of {older_leagues(o, counts=False)}"


def appendix_older(d) -> str:
    """Appendix I: Tables A14 and A15 for Amendment 7 (E27)."""
    o = older(d)
    g = o["gates"]
    same, outcome, link = (
        g["G27b_same_models"],
        g["G27c_same_outcome"],
        g["G27d_linking"],
    )
    if same["max_abs_gap"] > same["tolerance"] or same["tolerance"] != 1e-9:
        raise ClaimError(
            "E27: the frozen path no longer reproduces the published forecasts"
        )
    if not all(outcome["readings_hold"].values()):
        raise ClaimError("E27: a registered reading changed on the rebuilt outcomes")
    all_, rare_ = link["measured"]["all"], link["measured"]["rare_surname"]
    links = "In " + "; in ".join(
        f"{OLDER_PROSE[k]}, {v['linked']:,} of {v['source_player_seasons']:,} source player-seasons are linked and "
        f"{v['first_name_differs']} are dropped because the first names differ"
        for k in OLDER_ORDER
        if (v := o["linking"].get(k))
    )
    left_out = join_names(
        [
            f"{v['games_not_reconciled'] or 'none'} of {v['league_games']:,} in {OLDER_PROSE[k]}"
            for k in OLDER_ORDER
            if (v := o["linking"].get(k))
        ]
    )
    c = o["comparisons"]
    labels = [
        ("all", "All arrivals (the registered test)"),
        ("rare surname", "Rare surnames (registered sensitivity)"),
        ("with career history", "With an earlier season on disk"),
        ("club confirmed", "Continental club is the source club"),
        *[
            (f"league: {k}", f"Source: {LEAGUE_NAMES[OLDER_ROW[k]]}")
            for k in OLDER_ORDER
            if k in o["leagues"]
        ],
        ("destination: euroleague", "Destination: EuroLeague"),
        ("destination: eurocup", "Destination: EuroCup"),
    ]
    rows = [
        [
            label,
            f"{c[key][OLDER_COMPARISONS[0]]['n']}",
            *[older_cell(c[key][k]) for k in OLDER_COMPARISONS],
        ]
        for key, label in labels
    ]
    if o["acb_written_permission"]:
        rest = o["without_acb"]
        rows.append(
            [
                "Without ACB",
                f"{rest['n']}",
                *[older_cell(rest["comparisons"][k]) for k in OLDER_COMPARISONS],
            ]
        )
        withheld = ""
    else:
        withheld = (
            " A version that includes Spain's ACB was computed in the same runs and is withheld until ACB's written "
            "permission arrives; nothing in this appendix depends on it."
        )
    level = [
        [name, num(o["mae"][arm]), num(o["mean_error"][arm], sign=True)]
        for arm, name in OLDER_ARMS.items()
    ]
    seasons = sorted(o["by_season"])
    return (
        "### I. The older-seasons test\n\n"
        f"Analysis E27 [@amend7] scores the frozen models on arrivals from {older_leagues(o, counts=False)} in destination "
        "seasons 2008–09 to 2015–16. **Order of events.** A freeze run wrote one forecast for every eligible source "
        "player-season and both destinations and joined no outcome. The file's sha256 "
        f"(`{o['forecast_sha256'][:16]}…`) was committed and pushed. A first scoring run then stopped on a programming "
        f"error before any error, comparison or output existed (it wrote {o['runs']['score_stopped']['output_files']} "
        "files); no rule was changed, and the second scoring run is the only one that read outcomes. **Gates.** In the "
        f"freeze run, the same code reproduced the frozen 2026–27 forecasts ({same['rows']:,} rows, {same['arms']} forecasts "
        f"each) to within 10⁻⁹. Outcomes rebuilt from the API's season totals joined {outcome['joined']} of the "
        f"{outcome['n']} benchmark arrivals and correlated {num(outcome['correlation'], 4)} with the benchmark outcomes, with "
        "the three readings unchanged. On Israel, where full first names exist on both sides, the linking code reproduced "
        f"its registered measurement: {all_[0]} of {all_[1]} links made by initial and surname join different first names, "
        f"and {rare_[0]} of {rare_[1]} among rare surnames. Each gate has a negative control that failed as required. "
        "**Source games.** Source rates use only league games in which the players' points add up to the final score; "
        f"that left out {left_out}. "
        "**Linking.** A source player-season is linked to a EuroLeague API person when initial plus surname is unique "
        f"on both sides and the first three letters of the first names agree. {links}. **Arrivals.** The eligibility "
        f"rules are those of the benchmark. Of the {o['n']} arrivals, {o['by_destination']['euroleague']} went to the "
        f"EuroLeague and {o['by_destination']['eurocup']} to the EuroCup; {pct(o['shares']['rare_surname'])} have a rare "
        f"surname and {pct(o['shares']['without_history'])} no earlier season on disk."
        + withheld
        + "\n\nTable A14. The three comparisons on the older arrivals (EFF/36, 95% intervals clustered by player and "
        "destination club-season; positive favours translation in the first and third columns and the league-aware "
        'forecast in the second). Only the first row supports a registered statement; a null on any other row reads "not detectable '
        'at this n".\n\n'
        + md_table(
            [
                "Arrivals",
                "n",
                "Translation vs history",
                "League-aware vs history + translation",
                "Translation added to league-aware",
            ],
            rows,
        )
        + "\n\nTable A15. Forecast level on the older arrivals: mean absolute error and mean error (forecast minus actual "
        "EFF/36; below zero, the forecast expected less than arrivals delivered), and arrivals by destination season.\n\n"
        + md_table(["Forecast", "MAE", "Mean error"], level)
        + "\n\n"
        + md_table(
            ["Destination season", *[f"{s}–{str(int(s) + 1)[2:]}" for s in seasons]],
            [["Arrivals", *[f"{o['by_season'][s]}" for s in seasons]]],
        )
    )


# ---------------------------------------------------------------- the club tool and the weighted level (Amendment 12)
#: The two invented candidates, fixed in Amendment 12: (source league, domestic rate, career rate).
EXAMPLE = {"A": ("germany-bbl", 20.0, 17.0), "B": ("spain-acb", 16.0, 16.0)}
EXAMPLE_DESTINATION = "eurocup"
EXAMPLE_PLACE = {"germany-bbl": "Germany", "spain-acb": "Spain"}
#: The printed equation is checked for domestic and career rates up to this value.
EQ_MAX_RATE = 35
EQ_DIGITS = 3
OFFSET = "source_offset:"


def league_aware_forecast(
    co: dict, x: float, h: float, league: str, euroleague: bool, digits=None
) -> float:
    """The registered league-aware model (E9 full fit); ``digits`` rounds every coefficient first."""

    def c(key):
        return co[key] if digits is None else round(co[key], digits)

    out = (
        c("intercept") + c("source_rate") * x + c("prior_rate") * h + c(OFFSET + league)
    )
    if x > h:
        out += c("above_prior")
    if euroleague:
        out += c("destination_euroleague") + c("destination_x_source") * x
    return out


def history_forecast(co: dict, x: float, h: float) -> float:
    """The registered history-only model (E12 full fit)."""
    return (
        co["intercept"]
        + co["source_rate"] * x
        + co["prior_rate"] * h
        + (co["above_prior"] if x > h else 0.0)
    )


# ---------------------------------------------------------------- Amendment 23, rule 2: the destination term
#: Gate G23b: how far the term may lie from the difference of the committed reference forecasts.
G23B_TOLERANCE = 1e-9
#: Rule 2, "Label": the four statements that stand in the sentence that prints the destination
#: term or in the next one; "{rate}" is the reference rate of Table 1.
DESTINATION_TERM_LABEL = (
    "arithmetic on the fitted coefficients",
    "a domestic rate of {rate}",
    "grows with the domestic rate",
    "a point value with no interval",
)
#: The words by which a printing of the term is recognised (with its value in the same sentence).
DESTINATION_TERM_MARK = "destination term"


def reference_rate(d) -> float:
    """The domestic rate at which Table 1 is stated: the reference line of the decisions generator."""
    return float(get(d["decide"], "e9_reference_player/source_eff36"))


def destination_term(d) -> float:
    """Amendment 23, rule 2: the destination term of the fitted equation at the reference rate of
    Table 1, the forecast of that line for a EuroLeague arrival minus that for a EuroCup arrival.
    It is the sum of two registered coefficients, one of them times the rate; gate G23b
    (``destination_term_check``) runs when the files are loaded."""
    co = get(d["decide"], "e9/coefficients")
    return co["destination_euroleague"] + co["destination_x_source"] * reference_rate(d)


def destination_term_check(d) -> None:
    """Gate G23b, the arithmetic. The term is printed only if, for each of the ten leagues, it
    equals the committed reference forecast for a EuroLeague arrival minus that for a EuroCup
    arrival (absolute difference below 1e-9).

    Checked when the files are loaded, not when the text is composed: the number manifest traces
    a number by changing one value at a time, which a check inside compose() would refuse.
    """
    term, rate = destination_term(d), reference_rate(d)
    forecasts: dict = {}
    for row in d["tiers"]:
        if float(row["pir_per36_src"]) != rate:
            raise ClaimError(
                "G23b: a committed reference forecast is not stated at the reference rate of Table 1"
            )
        line = (row["pir_per36_src"], row["prior_mean_pir36"], row["above_own_prior"])
        forecasts.setdefault(row["league_src"], {}).setdefault(line, {})[
            row["league_dest"]
        ] = float(row["forecast"])
    complete = (
        len(d["tiers"]) == 2 * len(LEAGUE_NAMES)
        and set(forecasts) == set(LEAGUE_NAMES)
        and all(
            len(lines) == 1
            and set(next(iter(lines.values()))) == {"euroleague", "eurocup"}
            for lines in forecasts.values()
        )
    )
    if not complete:
        raise ClaimError(
            "G23b: the committed reference forecasts do not give each of the ten leagues one line "
            "for a EuroLeague arrival and the same line for a EuroCup arrival"
        )
    for code in sorted(forecasts):
        pair = next(iter(forecasts[code].values()))
        gap = pair["euroleague"] - pair["eurocup"]
        if not abs(gap - term) < G23B_TOLERANCE:
            raise ClaimError(
                f"G23b: for {code} the committed reference forecasts differ by {gap:.9f} between a EuroLeague "
                f"and a EuroCup arrival, not by the destination term {term:.9f}"
            )


def rounding_bound(
    co: dict, digits: int = EQ_DIGITS, max_rate: float = EQ_MAX_RATE
) -> float:
    """The most the equation with rounded coefficients can differ from the model, from rounding alone."""

    def e(key):
        return abs(co[key] - round(co[key], digits))

    return (
        e("intercept")
        + max_rate * (e("source_rate") + e("prior_rate") + e("destination_x_source"))
        + e("above_prior")
        + e("destination_euroleague")
        + max(e(k) for k in co if k.startswith(OFFSET))
    )


def equation_gaps(d, co: dict, frozen_path: Path) -> dict:
    """Gate G30a: the largest gap between the equation and each set of committed forecasts.

    A player with no earlier season is forecast with his career rate set to his
    domestic rate, as in the frozen file.
    """
    import pandas as pd

    reference = max(
        abs(
            league_aware_forecast(
                co,
                float(r["pir_per36_src"]),
                float(r["prior_mean_pir36"]),
                r["league_src"],
                r["league_dest"] == "euroleague",
            )
            - float(r["forecast"])
        )
        for r in d["tiers"]
    )

    def equivalent(league, el):
        # the domestic rate (career rate equal to it) that forecasts like a 16 in Spain's ACB
        target = league_aware_forecast(co, 16.0, 16.0, "spain-acb", el)
        at0 = league_aware_forecast(co, 0.0, 0.0, league, el)
        at1 = league_aware_forecast(co, 1.0, 1.0, league, el)
        return (target - at0) / (at1 - at0)

    equivalents = max(
        abs(
            equivalent(r["source_league"], r["destination"] == "euroleague")
            - float(r["acb16_equivalent_eff36"])
        )
        for r in d["exchange"]
    )
    frozen_rows = pd.read_parquet(frozen_path)
    frozen = 0.0
    for r in frozen_rows.itertuples():
        h = r.pir_per36_src if pd.isna(r.prior_mean_pir36) else r.prior_mean_pir36
        mine = league_aware_forecast(
            co, r.pir_per36_src, h, r.league_src, r.league_dest == "euroleague"
        )
        frozen = max(frozen, abs(mine - r.source_ridge_10))
    return {
        "reference": reference,
        "equivalents": equivalents,
        "frozen": frozen,
        "reference_rows": len(d["tiers"]),
        "equivalent_rows": len(d["exchange"]),
        "rows": len(frozen_rows),
    }


def league_numbers(d) -> dict:
    """Each league's number with its committed interval, from the E9 tier table."""
    out = {}
    for row in d["tiers"]:
        if row["league_dest"] == "euroleague":
            out[row["league_src"]] = (
                f"{num(float(row['adjustment_vs_league_average']), 2, sign=True)} "
                f"{interval([float(row['adjustment_ci95_low']), float(row['adjustment_ci95_high'])], 2)}"
            )
    return out


def club_tool(d) -> dict:
    """Amendment 12, part A: the fitted equation, its rounding bound and the worked example."""
    co = get(d["decide"], "e9/coefficients")
    hist = get(d["amend"], "e12/arms/history_only/coefficients_full_fit")
    if len([k for k in co if k.startswith(OFFSET)]) != len(LEAGUE_NAMES):
        raise ClaimError(
            "the equation does not carry one number for each league of the paper"
        )

    def term(key, symbol="", first=False):
        v = round(co[key], EQ_DIGITS)
        body = f"{abs(v):.{EQ_DIGITS}f}{symbol}"
        if first:
            return body if v >= 0 else f"-{body}"
        return f" + {body}" if v >= 0 else f" - {body}"

    equation = (
        r"$$\hat y = "
        + term("intercept", first=True)
        + term("source_rate", r"\,x")
        + term("prior_rate", r"\,h")
        + term("above_prior", r"\,a")
        + r" + \delta_\ell + D\,\big("
        + term("destination_euroleague", first=True)
        + term("destination_x_source", r"\,x")
        + r"\big)$$ {#eq:fitted}"
    )
    bound = math.ceil(100 * rounding_bound(co)) / 100
    el = EXAMPLE_DESTINATION == "euroleague"
    fc = {
        k: league_aware_forecast(co, x, h, lg, el) for k, (lg, x, h) in EXAMPLE.items()
    }
    fh = {k: history_forecast(hist, x, h) for k, (lg, x, h) in EXAMPLE.items()}

    def first(values):
        return max(values, key=values.get)

    def gap(values):
        return abs(values["A"] - values["B"])

    a3 = d["amend3"]
    edges, sentences = get(a3, "e20/bin_edges"), get(a3, "e20/licence/bin_sentences")
    lows = [low for low in edges if low is not None][: len(sentences)]
    if len(lows) != len(sentences) or lows != sorted(lows) or lows[0] != 0:
        raise ClaimError(
            "the forecast-gap guide has changed shape; the worked example needs new wording"
        )
    index = max(i for i, low in enumerate(lows) if gap(fc) >= low)
    trust = get(a3, "e20/licence/trust/0.60")
    if not trust["licensed"]:
        raise ClaimError("the 60% gap threshold is not licensed")
    order = (
        "The league numbers change the order here"
        if first(fc) != first(fh)
        else f"Both forecasts rank candidate {first(fc)} first"
    )
    weak = (
        f"the gap is below the {num(trust['from_gap'], 0)} EFF/36 from which forecast gaps were right at least "
        f"60% of the time, so it is a weak reason to prefer candidate {first(fc)}"
        if gap(fc) < trust["from_gap"]
        else "the gap is in the range where forecast gaps were right at least 60% of the time"
    )
    (lg_a, x_a, h_a), (lg_b, x_b, h_b) = EXAMPLE["A"], EXAMPLE["B"]
    dest = "EuroLeague" if el else "EuroCup"
    example = (
        "**A worked example with two invented candidates.** Candidate A plays in "
        f"{EXAMPLE_PLACE[lg_a]}: {num(x_a, 0)} EFF/36 last season against a career rate of {num(h_a, 0)}. Candidate B "
        f"plays in {EXAMPLE_PLACE[lg_b]}: {num(x_b, 0)} against a career rate of {num(h_b, 0)}. Both are weighed for a "
        f"{dest} club. History alone forecasts A at {num(fh['A'], 1)} and B at {num(fh['B'], 1)}, and so ranks "
        f"{first(fh)} first by {num(gap(fh), 1)}. Equation (@eq:fitted) forecasts A at {num(fc['A'], 1)} and B at "
        f"{num(fc['B'], 1)}, and so ranks {first(fc)} first by {num(gap(fc), 1)}. Table A25 says how far to trust a gap "
        f"of that size: {sentences[index][0].lower()}{sentences[index][1:]} {order}; {weak}. Each forecast also "
        "carries the error band described above. The example is an illustration with invented players; it "
        "recommends no signing."
    )
    guide = {
        row["bin"]: row
        for row in get(a3, "e20/bins")
        if row["arm"] == A3_O and row["pair_type"] == "all"
    }
    if len(guide) != len(sentences):
        raise ClaimError("the forecast-gap guide has one row for each of its sentences")
    # the step term a: its size beside the league numbers, and what it does to a league gap
    step = co["above_prior"]
    numbers = [
        float(row["adjustment_vs_league_average"])
        for row in d["tiers"]
        if row["league_dest"] == "euroleague"
    ]
    if not step < 0 or len(numbers) != len(LEAGUE_NAMES):
        raise ClaimError(
            "the sentences on the step term need a negative step and ten league numbers"
        )
    # Amendment 23, rule 2: the destination term beside the two other terms, with its label, and
    # beside them the average miss of one forecast and the typical 80% band. The three sentences
    # that render 44 added on the step stay: its size beside the span; the Equivalents hold where
    # the step is zero; what the step does to a gap between two leagues.
    term, rate, spread = (
        destination_term(d),
        reference_rate(d),
        max(numbers) - min(numbers),
    )
    miss = get(d["recipes"], "results/A/R1/metrics/source_ridge_10/mae")
    if not (term < 0 and co["destination_x_source"] < 0):
        raise ClaimError(
            "Amendment 23, rule 2: the sentences on the destination term are written for a term below zero "
            "that grows with the domestic rate"
        )
    if not max(abs(step), abs(term), spread) < miss:
        raise ClaimError(
            "Amendment 23, rule 2: a term of the equation is not smaller than the average miss of a single "
            "forecast; that sentence is withdrawn and goes to Amir first"
        )
    eq_step = (
        f"The step a takes {num(abs(step), EQ_DIGITS)} EFF/36 off the forecast of a player whose last season was "
        f"above his career rate; the ten league numbers span {num(spread, 2)}. At a domestic rate of {rate:g} "
        f"the destination term is {num(term, 2)} EFF/36: the forecast for a EuroLeague arrival minus that for a "
        "EuroCup arrival. It is arithmetic on the fitted coefficients, it grows with the domestic rate, and it is a "
        "point value with no interval [@amend23]. These are three terms of one fitted forecast, and at that "
        "rate each is smaller than the average miss of a single forecast ({{mae_off10}} EFF/36; typical "
        "80% band ±{{e8_hw80}}). The destination term is the same for two candidates of one club who have the same "
        "domestic rate, so it bears on the level of a forecast and not on the comparison of two such candidates. "
        "The Equivalents "
        "are stated for the profile where the step is zero (x = h). A gap between two leagues is unchanged when both "
        "candidates carry the step, and not when only one does."
    )
    trust_pairs = {
        level: sum(
            row["pairs"] for row in guide.values() if row["gap_low"] >= rule["from_gap"]
        )
        for level, rule in get(a3, "e20/licence/trust").items()
    }
    trust_counts = (
        f"These shares rest on {trust_pairs['0.60']:,} and {trust_pairs['0.70']:,} pairs from the examined "
        "seasons and describe the whole forecast."
    )
    # The Table A20 reference profile isolates the source-league term.
    germany = league_aware_forecast(co, 16.0, 16.0, "germany-bbl", False)
    spain = league_aware_forecast(co, 16.0, 16.0, "spain-acb", False)
    short = (
        "**Two recruits with the same production.** Two EuroCup candidates each averaged 16 EFF/36 "
        "last season and across their earlier careers. The German BBL recruit projects at "
        f"{num(germany, 1)} EFF/36 and the Spanish ACB recruit at {num(spain, 1)}. The "
        f"{num(spain - germany, 2)} EFF/36 gap comes entirely from the league terms. "
        "The typical 80% individual error band is ±{{e8_hw80}} EFF/36. On film, ask which player "
        "could sustain his production in the minutes and role the club can offer."
    )
    return {
        "eq_fitted": equation,
        "eq_bound": num(bound, 2),
        "eq_max_rate": f"{EQ_MAX_RATE}",
        "club_example": example,
        "club_example_short": short,
        # Amendment 29, rule 1: the same example on the first page, with the error band beside the gap
        "club_first_page": (
            f"{FIRST_PAGE_CLUB_HEAD} Candidates from different leagues can be compared by entering each candidate's league "
            "number in the fitted equation ({{eq_table}}; the equation is given in the section *What a club can use*): of two "
            "EuroCup candidates who each averaged 16 EFF/36 last season and across their earlier careers, the one from "
            f"Germany's BBL projects at {num(germany, 1)} EFF/36 and the one from Spain's ACB at {num(spain, 1)}, a "
            f"{num(spain - germany, 2)} EFF/36 gap that comes entirely from the two league numbers. "
            "The forecast for a single player has a typical 80% error band of ±{{e8_hw80}} EFF/36, "
            "wider than that gap, which argues for scouting alongside the comparison."
        ),
        "eq_step": eq_step,
        "trust_counts": trust_counts,
    }


def weighted_level(d) -> dict:
    """Amendment 12, part B: the forecast level weighted by playing time, from the E29 rows for all arrivals."""
    means = e29(d)["e29b"]["rows"]["all"]["means"]
    with_table, without = (
        means[k]["minutes_weighted"]
        for k in ("error_with_table", "error_without_table")
    )
    if not (with_table["ci95"][1] < 0 and without["ci95"][1] < 0):
        raise ClaimError(
            "the weighted forecast level is no longer below zero; the sentence is withdrawn and goes to Amir first"
        )

    def span(c):
        return f"interval {num(c['ci95'][0], 2)} to {num(c['ci95'][1], 2)}"

    return {
        "lvl_w_sentence": (
            f"Weighted by playing time, the league-aware forecast is {num(-with_table['mean'], 2)} EFF/36 below "
            f"what arrivals delivered ({span(with_table)}), and the forecast that knows only the destination shares "
            f"this ({num(without['mean'], 2)}, {span(without)})"
        ),
        "lvl_w_abs": num(-with_table["mean"], 2),
    }


# ---------------------------------------------------------------- Amendment 13: the order of the first page
def both_periods(d) -> dict:
    """Translation's increment on top of the league-aware forecast, on 2020-2025 and on the older arrivals.

    Amendment 13, rule 2: the sentence is allowed only while both intervals include zero.
    """
    inc = get(
        d["recipes"],
        "results/A/R1/ladder/source_ridge_10->source_ridge_10_scheduled/player_club_season",
    )
    o = older(d)
    old = o["comparisons"]["all"]["offsets10_increment"]
    if not inc["ci95"][0] < 0 < inc["ci95"][1] or old["reading"] not in (INSIDE, WIDER):
        raise ClaimError(
            "Amendment 13: translation's increment excludes zero in one period; the 'both periods' "
            "sentence is withdrawn and the first page goes to Amir first"
        )
    older_part = f"{num(old['difference'], sign=True)} (interval {older_span(old)})"
    part_674 = f"{num(inc['difference'])} EFF/36 (95% interval {num(inc['ci95'][0])} to {num(inc['ci95'][1])})"
    return {
        "inc_674": part_674,
        "inc_both": (
            f"{part_674} "
            f"on the arrivals of 2020–2025, and {older_part} on {o['n']} older arrivals from seasons no model saw"
        ),
        "inc_older": older_part,
        "older_n": f"{o['n']}",
    }


# ---------------------------------------------------------------- Amendment 16: the first page by the case of E30
def e30_limit_leagues(e: dict) -> list:
    """The leagues named as a limit (Amendment 14, S-b; Amendment 17, rule 7), as codes."""
    limit = e.get("limit_league")
    if not limit:
        return []
    return [limit] if isinstance(limit, str) else list(limit)


def e30_check(e: dict, full: dict) -> None:
    """The leaves the first page is built from equal the full scored record they were copied from,
    and the case the record names is the one Amendment 14's rule gives for its ten
    leave-one-league-out intervals. Run when the files are loaded."""
    primary = full["primary"]
    copies = (
        ("slope", primary["estimate"]),
        ("ci_low", primary["ci95"][0]),
        ("ci_high", primary["ci95"][1]),
        ("perm_p", primary["permutation"]["p"]),
        ("n_players", full["n_players"]),
        ("n_moves", full["n_league_changes"]),
    )
    for key, value in copies:
        if e[key] != value:
            raise ClaimError(
                f"E30: {key} differs between summary.json and the full record"
            )
    if E30_CASE_NAMES.get(e["case"]) != full["case"]["case"]:
        raise ClaimError(
            "E30: the case differs between summary.json and the full record"
        )
    left_out = full["S_b"]
    if set(left_out) != set(LEAGUE_NAMES):
        raise ClaimError("E30: S-b must leave each of the ten leagues out once")
    not_above = sorted(k for k, v in left_out.items() if v["ci95"][0] <= 0)
    if not_above != sorted(e30_limit_leagues(e)):
        raise ClaimError(
            "E30: the leagues named as a limit are not those whose leave-one-out interval "
            "fails to lie above zero"
        )
    below = sorted(k for k, v in left_out.items() if v["ci95"][1] < 0)
    if below != sorted(e.get("limit_league_below_zero") or []):
        raise ClaimError(
            "E30: the leagues whose leave-one-out interval lies below zero differ"
        )


def e30_case(d) -> str:
    """The registered case of E30, checked against the case rule of Amendment 14.

    The summary names its case; the rule is applied again here to the numeric leaves
    (slope interval, permutation share, the league named as a limit), and a summary whose
    case and numbers disagree is refused.
    """
    e = d.get("e30")
    if e is None:
        return E30_NOT_RUN
    case = e["case"]
    if case not in E30_CASES:
        raise ClaimError(f"unknown E30 case: {case}")
    low, high, p = e["ci_low"], e["ci_high"], e["perm_p"]
    if not low <= e["slope"] <= high:
        raise ClaimError("E30: the slope lies outside its own interval")
    if high < 0:
        rule = "against"
    elif low <= 0:
        rule = "null"
    elif p >= E30_ALPHA:
        rule = "positive_not_separable"
    elif e30_limit_leagues(e):
        rule = "positive_named_limit"
    else:
        rule = "clear"
    if rule != case:
        raise ClaimError(
            f"E30: the summary says '{case}' but Amendment 14's rule gives '{rule}' for its numbers"
        )
    return case


def title_for(case: str) -> str:
    """Amendment 16, rule 2."""
    return TITLE_TESTED if case in E30_TESTED else TITLE_ADDS


def abstract_limit(d) -> int:
    """Amendment 17, "Counting numbers in the abstract": eight numbers, and nine in the two
    cases of E30 the amendment names ("Clear" with an interval below 1; "Positive, with a
    named limit")."""
    case = e30_case(d)
    if case == "positive_named_limit" or (case == "clear" and d["e30"]["ci_high"] < 1):
        return ABSTRACT_MAX_NUMBERS_E30
    return ABSTRACT_MAX_NUMBERS


def signed(x: float, digits: int = 3) -> str:
    """'+ 0.109' or '− 0.836': a coefficient written as a term of an equation."""
    return f"{'−' if x < 0 else '+'} {num(abs(x), digits)}"


def span(ci, digits: int = 3) -> str:
    """'interval 0.692 to 0.844'."""
    return f"interval {num(ci[0], digits)} to {num(ci[1], digits)}"


def e30_full(d) -> dict:
    """The full scored record of E30; Amendment 14 has every number reported, so the paper is
    not composed from the first-page leaves alone."""
    full = d.get("e30_full")
    if full is None:
        raise ClaimError(
            "E30: the full scored record (S-a to S-f, E31b) is missing; the paper prints "
            "every secondary result"
        )
    return full


def e30_sentence(d) -> str:
    """The sentence Amendment 14 registers for the case, composed from the summary's numeric leaves."""
    case, e = e30_case(d), d.get("e30")
    if case == E30_NOT_RUN:
        return ""
    slope = num(e["slope"], 2)
    span95 = f"95% interval {num(e['ci_low'], 2)} to {num(e['ci_high'], 2)}"
    if case in E30_TESTED:
        if "n_players" not in e:
            raise ClaimError(
                "E30: the registered sentence counts players ('N players who changed domestic league'); "
                "the summary gives no n_players, and the number of league changes is not that count"
            )
        text = (
            "The league table, fitted only on first continental seasons, predicted what happened to "
            f"{e['n_players']:,} players who changed domestic league: slope {slope} ({span95}), where 1 would "
            "mean the table's size is exactly right."
        )
        if e["ci_low"] <= 1 <= e["ci_high"]:
            text += " This is consistent with the table's size."
        elif e["ci_high"] < 1:
            text += f" That is about {slope} of the size the table implies."
        else:
            # Amendment 17, rule 7: the interval lies wholly above 1
            text += " That is larger than the table implies."
        if case == "positive_named_limit":
            below = list(e.get("limit_league_below_zero") or [])
            touching = [k for k in e30_limit_leagues(e) if k not in below]
            if touching:
                names = join_names([short_league(k) for k in touching])
                text += f" Without {names} the interval includes zero."
            for code in below:
                # Amendment 17, rule 7: a leave-one-league-out interval wholly below zero
                ci = e30_full(d)["S_b"][code]["ci95"]
                if not ci[1] < 0:
                    raise ClaimError(
                        f"E30: the interval without {code} does not lie below zero"
                    )
                text += (
                    f" Without {short_league(code)} the slope is below zero "
                    f"(95% interval {num(ci[0], 2)} to {num(ci[1], 2)})."
                )
        return text
    if case == "positive_not_separable":
        return (
            f"On players who changed domestic league the table gave a positive slope ({slope}, {span95}) that a "
            f"random assignment of the ten league values produces in {pct(e['perm_p'])} of draws; with ten "
            "leagues the test cannot tell the table's order from chance."
        )
    if case == "null":
        return (
            "The league table did not predict what happened to players who changed domestic league "
            f"(slope {slope}, {span95}; a slope of {E30_PLANNING_SLOPE} would have been detected with 80% power "
            "under the planning assumptions)."
        )
    return (
        f"Players who changed league moved against the table (slope {slope}, {span95})."
    )


E30_NO_CAUSE = (
    "We claim no cause: the design does not separate a table that describes whom clubs recruit from "
    "changes of role, from error in the table, or from wrong name links."
)
#: Amendment 14, "What the paper may say": what a Clear result does not license.
E30_NOT_LICENSED = (
    "The result is not a statement about league strength as such, says nothing about any single pair of "
    "leagues and is not a statement of equivalence."
)
#: Amendment 14, "Limits stated in advance", and Amendment 17, rule 2 (the corpus).
E30_SELECTION = (
    "Players who change league are not a random sample, role and minutes change with a move, and players "
    "are linked across leagues by name"
)
E31_TABLE = "a league table printed in 2015"
E31_PAIR = f"the paper's league numbers and {E31_TABLE}"


# ---------------------------------------------------------------- Amendment 19: a shorter paper; one labelled reading
#: Amendment 19, rule 5: the label that stands with every printing of the reading (gate G19b).
READING_LABEL = "arithmetic on the registered slope, stated after the result, and not a registered reading"
#: Amendment 19, rule 8: the label of the registered sensitivity whose table is refitted on earlier arrivals.
S7_LABEL = re.compile(
    r"arrival seasons (\d{4}) to (\d{4}), the table refitted only on arrivals before that season"
)
#: The sensitivity that uses the EuroLeague Equivalents (gate G19a, check iii).
S5_WORD = "EuroLeague"


def season_label(start: int) -> str:
    """'2016–17' from 2016."""
    return display_season(start).replace("-", "–")


def e30_seasons(d) -> str:
    """The arrival seasons of the league changes, from the freeze record's registered constants."""
    record = d.get("e30_freeze")
    if record is None:
        raise ClaimError(
            "E30: the freeze record that names the arrival seasons is missing"
        )
    low, high = get(record, "registered_constants/arrival_seasons")
    return f"{season_label(low)} to {season_label(high)}"


def prints_first_page_words(d) -> bool:
    """Amendment 19, rule 1: the plainer words are for a Clear result whose interval lies below 1."""
    return e30_case(d) == "clear" and d["e30"]["ci_high"] < 1


def league_number_weights(d) -> dict:
    """Amendment 19, rule 5: the weight the fitted equation gives a domestic rate when career
    history equals it (the coefficient of the domestic rate plus that of the career rate, for a
    EuroCup arrival; the EuroLeague term added for a EuroLeague arrival)."""
    co = get(d["decide"], "e9/coefficients")
    eurocup = co["source_rate"] + co["prior_rate"]
    return {"eurocup": eurocup, "euroleague": eurocup + co["destination_x_source"]}


def league_number_reading(d) -> dict:
    """Amendment 19, rule 5: the registered slope and its interval divided by the EuroCup weight.
    Arithmetic only; gate G19a (``league_number_check``) runs when the files are loaded."""
    e, w = d["e30"], league_number_weights(d)
    per = [v / w["eurocup"] for v in (e["slope"], e["ci_low"], e["ci_high"])]
    return {"weights": w, "per": per, "includes_one": per[1] <= 1 <= per[2]}


def league_number_check(d) -> None:
    """Gate G19a. The reading is printed only if (i) the ratio of forecast gap to Equivalent gap
    is the same for all ten leagues, (ii) it equals the weight of rule 5, and (iii) the registered
    sensitivity with the EuroLeague Equivalents, divided by its own weight, gives the same value."""
    weights = league_number_weights(d)
    for dest, want in weights.items():
        rows = [r for r in d["exchange"] if r["destination"] == dest]
        refs = [r for r in rows if r["source_league"] == "spain-acb"]
        if len(rows) != len(LEAGUE_NAMES) or len(refs) != 1:
            raise ClaimError(
                f"G19a: the Equivalents of {dest} do not cover the ten leagues once"
            )
        ref = refs[0]
        base = float(ref["acb16_equivalent_eff36"])
        for r in rows:
            if r is ref:
                continue
            gap = float(r["acb16_equivalent_eff36"]) - base
            if gap == 0:
                raise ClaimError(
                    f"G19a: {r['source_league']} has no Equivalent gap for {dest}"
                )
            ratio = (
                float(ref["e9_forecast_eff36"]) - float(r["e9_forecast_eff36"])
            ) / gap
            if abs(ratio - want) > 1e-6:
                raise ClaimError(
                    f"G19a: for {r['source_league']} ({dest}) the forecast gap is {ratio:.6f} of the "
                    f"Equivalent gap, not the equation's weight {want:.6f}"
                )
    e, s5 = d["e30"], e30_full(d)["S_e"]["5"]
    if S5_WORD not in s5["label"]:
        raise ClaimError(
            "G19a: sensitivity 5 is not the one with the EuroLeague Equivalents"
        )
    main = [v / weights["eurocup"] for v in (e["slope"], e["ci_low"], e["ci_high"])]
    other = [v / weights["euroleague"] for v in (s5["estimate"], *s5["ci95"])]
    if max(abs(a - b) for a, b in zip(main, other)) > 1e-6:
        raise ClaimError(
            "G19a: the EuroLeague Equivalents give a different slope per unit of league number"
        )


def e30_fraction(e: dict) -> str:
    """Amendment 19, rule 1: 'about three quarters' only while the slope is at least 0.70 and below 0.80."""
    if 0.70 <= e["slope"] < 0.80:
        return "about three quarters of its size"
    return f"about {num(e['slope'], 2)} of its size"


def e30_statement(d) -> str:
    """Amendment 19, rule 1: the words of the first page for a Clear result whose interval lies below 1."""
    e = d["e30"]
    return (
        f"{e['n_players']:,} players who changed domestic league moved in the direction the table implies, "
        f"at {e30_fraction(e)} (slope {num(e['slope'], 2)}, 95% interval {num(e['ci_low'], 2)} to "
        f"{num(e['ci_high'], 2)})"
    )


E30_FROZEN_FIRST = "In a test registered and frozen before its outcomes were read, "


def e30_lowest(d):
    s_b = e30_full(d)["S_b"]
    code = min(s_b, key=lambda k: s_b[k]["estimate"])
    return code, s_b[code]


#: How the interval of the slope is computed, in the words of Amendment 14 (Uncertainty).
E30_INTERVAL = "The interval comes from a bootstrap that resamples players and refits the stayer forecast in every draw."


def e30_meaning(d) -> str:
    """Results: the reading of Amendment 19, rule 5, in its shortest form: the reading once, its
    label, what it is not, and why the Equivalents are larger. The weight is a coefficient of the
    fitted equation and is said to be one."""
    reading = league_number_reading(d)
    per, w = reading["per"], reading["weights"]
    co = get(d["decide"], "e9/coefficients")
    parts = (num(co["source_rate"], 3), num(co["prior_rate"], 3), num(w["eurocup"], 3))
    if round(round(co["source_rate"], 3) + round(co["prior_rate"], 3), 3) != round(
        w["eurocup"], 3
    ):
        raise ClaimError(
            "the printed coefficients do not add up to the printed weight; reword the passage"
        )
    return (
        f"**What the size means.** An Equivalent gap is the gap between two league numbers ({eq_table(d)}) "
        f"divided by {parts[2]}, the weight of the fitted equation on a domestic rate when career history equals "
        f"it ({parts[0]} + {parts[1]} for a EuroCup arrival: a coefficient, not a measurement). Per EFF/36 of gap "
        "between two league numbers, a league changer's rate therefore moved by "
        f"{num(per[0], 2)} EFF/36 (interval {num(per[1], 2)} to {num(per[2], 2)}). This is {READING_LABEL} "
        f"[@amend19]; the registered reading, about {num(d['e30']['slope'], 2)} of the size the table implies, "
        "stands, and neither is a statement "
        "about league strength, about a single pair of leagues or about equivalence. The Equivalents are larger "
        "because they answer another "
        "question: which domestic line gives the same continental forecast, not what the same player produces in "
        "another league."
    )


# ---------------------------------------------------------------- Amendment 22: E33 (exploratory)
#: Amendment 22, "What the paper may say": the label that follows the sentence in every case.
E33_LABEL = (
    "This check was added after the result of the league-changes test was seen and is exploratory "
    "[@amend22]."
)
#: Amendment 22: words the paper does not use for E33.
E33_FORBIDDEN = ("confirms", "robust", "validated", "unchanged", "equivalent")
#: Amendment 22: the cases whose text may be written without a further decision.
E33_PRINTABLE = ("same", "different_higher")


def e33_case(r: dict) -> str:
    """The case of Amendment 22, recomputed from the committed numbers."""
    low = r["cutoff"]["ci95"][0]
    d_low, d_high = r["difference"]["ci95"]
    if low <= 0:
        return "not_above_zero"
    if d_low <= 0 <= d_high:
        return "same"
    return "different_lower" if d_high < 0 else "different_higher"


def e33_check(r: dict, full: dict) -> None:
    """E33 is printed only as registered: the amendment, the rows, gate G33c and the case."""
    if get(r, "amendment_22/sha256") != AMENDMENT_22_SHA256:
        raise ClaimError("E33: the run was not made under the registered Amendment 22")
    s7 = full["S_e"]["7"]
    pooled = r["pooled"]
    same = [abs(pooled["estimate"] - s7["estimate"])] + [
        abs(a - b) for a, b in zip(pooled["ci95"], s7["ci95"])
    ]
    if r["league_changes"] != s7["league_changes"] or max(same) >= 1e-9:
        raise ClaimError(
            "E33: sensitivity (7) is not reproduced on the same rows (G33c)"
        )
    if get(r, "gates/G33c_reproduction/status") != "passed":
        raise ClaimError("E33: gate G33c is not recorded as passed")
    if r["case"] != e33_case(r):
        raise ClaimError("E33: the recorded case is not the case of its numbers")
    if r["case"] not in E33_PRINTABLE:
        raise ClaimError(
            f"E33: the case '{r['case']}' goes to Amir before any text is written (Amendment 22)"
        )


def e33_sentence(d) -> str:
    """Results, after the sentence on sensitivity (7): the registered wording of the case."""
    r = d.get("e33")
    if r is None:
        return ""
    c, diff = r["cutoff"], r["difference"]
    lead = (
        "With the stayer forecast also fitted only on seasons before each move, the slope on the same "
        f"{r['league_changes']:,} league changes is {num(c['estimate'], 2)} ({span(c['ci95'], 2)})"
    )
    if r["case"] == "same":
        body = (
            f"{lead}, not distinguishable from that sensitivity (difference {num(diff['estimate'])}, "
            f"{span(diff['ci95'])}; a difference of {num(diff['detectable_80'])} would have been detected "
            "with 80% power), which is not the same as equal."
        )
    elif r["case"] == "different_higher":
        body = f"{lead}, higher than that sensitivity by {num(abs(diff['estimate']))} ({span(diff['ci95'])})."
    else:  # refused in ``load``; kept so that no other wording can be printed
        raise ClaimError("E33: this case has no text without Amir's decision")
    return f"{body} {E33_LABEL} "


def e33_appendix_sentence(d) -> str:
    """Appendix M: the secondary result of Amendment 22, in one sentence."""
    r = d.get("e33")
    if r is None:
        return ""
    by = r["season_intercepts"]
    return (
        " With one intercept per arrival season in place of the single intercept, the slope is "
        f"{num(by['cutoff']['estimate'], 2)} ({span(by['cutoff']['ci95'], 2)}) with the stayer forecast fitted only "
        f"on seasons before each move and {num(by['pooled']['estimate'], 2)} ({span(by['pooled']['ci95'], 2)}) with "
        "it fitted on all seasons (a check added after the result, exploratory [@amend22]; Table A21 "
        "prints both beside the slopes with the single intercept)."
    )


def e30_unseen(d) -> str:
    """Results: what was unseen (Amendment 19, rules 4 and 8), what the result licenses and the
    limits stated in advance."""
    case, full = e30_case(d), e30_full(d)
    s7 = full["S_e"]["7"]
    match = S7_LABEL.search(s7["label"])
    if match is None:
        raise ClaimError(
            "E30: sensitivity 7 is not the table refitted only on earlier arrivals (Amendment 19, rule 8)"
        )
    first, last = int(match.group(1)), int(match.group(2))
    if case in E30_TESTED:
        rider = f"The slope is an average relation over all league changes. {E30_NOT_LICENSED}"
    elif case == "positive_not_separable":
        rider = "We read it as a positive sign that this test cannot confirm."
    else:
        rider = E30_NO_CAUSE
    return (
        "**What was unseen.** The table was not fitted to these league changes and not scored on them before "
        "this test. But the same seasons are inputs to the paper's forecasts, so the test and the fitted data "
        "overlap in time. "
        f"One registered sensitivity removes that overlap in time: for the {s7['league_changes']:,} league changes of {season_label(first)} to "
        f"{season_label(last)}, with the table refitted only on arrivals before the season of the move, the "
        f"slope is {num(s7['estimate'], 2)} ({span(s7['ci95'], 2)}). Only the league table uses this cutoff. "
        "The comparison forecast for players who stay pools stayer outcomes across all seasons. "
        f"{e33_sentence(d)}{rider} {E30_SELECTION}; a wrong link pulls the slope towards zero "
        "in expectation if mismatches pair outcomes independently of the predicted change. Systematic "
        "mismatches can bias the slope in either direction. The box scores of this test are raw "
        "Proballers files, not the corrected "
        f"corpus of the {get(d['recipes'], 'n_targets')} arrivals."
    )


# ---------------------------------------------------------------- Amendment 15: a published league table (E31)
def e31_reading(ci) -> str:
    return "above_zero" if ci[0] > 0 else "below_zero" if ci[1] < 0 else "includes_zero"


def e31a(d):
    """E31a: the 2015 table on the arrivals of 2020-2025 (exploratory), or None when not committed.

    Each committed reading is recomputed from its interval; the unweighted analysis decides the
    sentence (Amendment 17, rule 9)."""
    s = d.get("e31")
    if s is None:
        return None
    if s.get("exploratory") is not True:
        raise ClaimError("E31a is exploratory and must be committed as such")
    out = {}
    for key in ("T_D", "T_O"):
        contrast = get(s, f"e31a/contrasts/{key}")
        for weighting in ("unweighted", "minutes_weighted"):
            row = contrast[weighting]
            if e31_reading(row["ci95"]) != row["reading"]:
                raise ClaimError(
                    f"E31a: the reading of {key} ({weighting}) is not that of its interval"
                )
        out[key] = contrast
    if out["T_O"]["unweighted"]["reading"] == "below_zero":
        raise ClaimError(
            "E31a: the 2015 table is more accurate than the paper's league numbers; Amendment 15 sends "
            "that to Amir before any writing"
        )
    if out["T_D"]["unweighted"]["reading"] == "below_zero":
        raise ClaimError(
            "E31a: Amendment 15 registers no wording for a 2015 table that worsens the forecast"
        )
    return out


def e31b(d):
    """E31b: the two scales on the league changes of E30, or None while E30 is not run."""
    if e30_case(d) == E30_NOT_RUN:
        return None
    b = e30_full(d)["E31b"]
    ci = b["difference_published_minus_paper"]["ci95"]
    reading = e31_reading(ci)
    if (reading == "includes_zero") != (b["reading"] == "not distinguishable"):
        raise ClaimError("E31b: the committed reading is not that of its interval")
    if reading == "below_zero":
        raise ClaimError(
            "E31b: the 2015 table predicted league changes better; Amendment 15 sends that to Amir "
            "before any writing"
        )
    return {**b, "paper_reading": reading}


def e31_clause(d) -> str:
    """The one clause of the first page (Amendment 16, rule 3): only for "not distinguishable"."""
    a, b = e31a(d), e31b(d)
    where = []
    if b is not None and b["paper_reading"] == "includes_zero":
        where.append("these league changes")
    if a is not None and a["T_O"]["unweighted"]["reading"] == "includes_zero":
        where.append("the 2020–2025 arrivals")
    if not where:
        return ""
    return f"On {' and '.join(where)}, {E31_PAIR} are not distinguishable. "


def e31_section(d) -> str:
    """Results (Amendment 19, rule 7): the paper's league numbers against the 2015 table, on league
    changes (E31b) and on the arrivals (E31a), each with its interval, the detectable difference
    and the weighted value; one sentence on what this paper adds that a reader can check here."""
    a, b = e31a(d), e31b(d)
    if a is None and b is None:
        return ""
    purpose = get(d["e31"], "table/purpose") if d.get("e31") else ""
    lead = "**A published league table on the same players.** A scale of competitions printed in 2015"
    if "NBA draft" in purpose:
        lead += " for the NBA draft"
    parts = [lead + " [@vashro2015] can be scored the same way."]
    equal = []
    if b is not None:
        diff = b["difference_published_minus_paper"]
        paper, published = b["scales"]["paper"], b["scales"]["published"]
        text = (
            f"On the {b['scored_league_changes']:,} league changes of arrival seasons from "
            f"{season_label(b['first_scored_arrival_season'])}, with one coefficient per scale fitted on "
            "earlier league changes, the stayer forecast has a mean absolute error of "
            f"{num(b['mae_stayer_forecast']['estimate'])} EFF/36 alone, {num(paper['mae']['estimate'])} with "
            f"the Equivalents and {num(published['mae']['estimate'])} with the 2015 table"
        )
        if b["paper_reading"] == "includes_zero":
            text += f": a difference of {num(diff['estimate'], sign=True)} ({span(diff['ci95'])}), not distinguishable."
            equal.append("league changes")
        else:
            text += (
                f". The paper's equivalents predicted league changes better by {num(diff['estimate'])} "
                f"({span(diff['ci95'])})."
            )
        parts.append(text)
    if a is not None:
        ou, ow = a["T_O"]["unweighted"], a["T_O"]["minutes_weighted"]
        n = get(d["e31"], "n_targets")
        if ou["reading"] == "above_zero":
            text = (
                f"On the {n} arrivals of 2020–2025 (exploratory [@amend15]), the paper's league numbers are more "
                f"accurate than the 2015 table by {num(ou['difference'])} EFF/36 ({span(ou['ci95'])}); the "
                f"weighted value is {num(ow['difference'])} ({span(ow['ci95'])})"
            )
            if ow["reading"] == "includes_zero":
                text += ", not clearly above zero when weighted by playing time"
            text += "."
        else:
            text = (
                f"On the {n} arrivals of 2020–2025 (exploratory [@amend15]), {E31_PAIR} are not distinguishable "
                f"({num(ou['difference'])}, {span(ou['ci95'])}; a difference of {num(ou['detectable_80'])} "
                f"would have been detected with 80% power); the weighted value is {num(ow['difference'])} "
                f"({span(ow['ci95'])})."
            )
            equal.append("arrivals")
        parts.append(text)
    if len(equal) == 2:
        parts.append(E31_NEITHER)
    elif equal:
        parts.append("Not distinguishable is not the same as equal.")
    # Amendment 27, rule 1: the pointer to the exploratory reading on the older arrivals (E34)
    if pointer := e34_pointer(d):
        if len(equal) != 2:
            raise ClaimError(
                'G27b: the sentence of Amendment 27 follows "On neither sample can the two be told apart", '
                "which this paper does not print: this goes to Amir"
            )
        parts.append(pointer)
    adds = [
        f"an interval for each league number ({eq_table(d)})",
        "one fitted equation for both competitions",
        "a refit before each season (Appendix H)",
    ]
    if e30_case(d) != E30_NOT_RUN:
        adds.insert(0, "the registered test on league changes")
    parts.append(
        "What this paper adds to such a table can be checked here: "
        + ", ".join(adds[:-1])
        + f", and {adds[-1]}. Appendix M sets the 2015 table against the "
        "destination-only forecast."
    )
    return " ".join(parts) + "\n\n"


# ---------------------------------------------------------------- Amendment 14: the test on league changes (E30)
def e30_redrawn_mark(d) -> str:
    """'0.43 to 0.93': the interval of the slope with the ten table values redrawn (S-d)."""
    low, high = e30_full(d)["S_d"]["ci95"]
    return f"{num(low, 2)} to {num(high, 2)}"


def e30_redrawn_intro(d) -> str:
    """Amendment 21, rule 2: the introduction gives the interval of the slope with the ten table
    values redrawn, named as such and as an approximation. It is read for its width only and does
    not decide the case (Amendment 17, rule 6); it does not enter the abstract."""
    return (
        f"With the ten table values redrawn as well, the slope's interval is {e30_redrawn_mark(d)} "
        "(an approximation, read for its width only)."
    )


def e30_secondary(d) -> dict:
    """S-a to S-d as sentences, each read from the full scored record (Amendment 14: every
    number is reported whatever it shows; Amendment 19, rule 11: the lowest leave-one-league-out
    slope, the both-directions statement and the redrawn-table interval stay in the main text,
    the direction intervals and the eight sensitivities are in Table A21)."""
    full, e = e30_full(d), d["e30"]
    s_a = full["S_a"]
    lo, hi = s_a["difference"]["ci95"]
    verb = "lowers" if lo > 0 else "raises" if hi < 0 else "changes"
    error = (
        f"Adding the table's predicted change to the stayer forecast {verb} its error on the league changers "
        f"from {num(s_a['mae_stayer_forecast'])} to {num(s_a['mae_stayer_forecast_plus_g'])} EFF/36 "
        f"(difference {num(s_a['difference']['estimate'])}, {span(s_a['difference']['ci95'])})"
    )
    error += "." if verb != "changes" else "; the difference is not detectable."
    s_b = full["S_b"]
    lowest = min(s_b, key=lambda k: s_b[k]["estimate"])
    highest = max(s_b, key=lambda k: s_b[k]["estimate"])
    if not s_b[lowest]["estimate"] < e["slope"]:
        raise ClaimError(
            "E30: no league's removal lowers the slope; rewrite the S-b sentence"
        )
    left_out = (
        f"Leaving one league out at a time, the slope runs from {num(s_b[lowest]['estimate'], 2)} (without "
        f"{short_league(lowest)}; {span(s_b[lowest]['ci95'], 2)}) to {num(s_b[highest]['estimate'], 2)}"
    )
    not_above = [k for k in s_b if s_b[k]["ci95"][0] <= 0]
    if not_above:
        names = join_names([short_league(k) for k in sorted(not_above)])
        left_out += f"; without {names} the interval does not lie above zero."
    else:
        left_out += ", and all ten intervals lie above zero."
    s_c = full["S_c"]
    up, down = s_c["to_higher_equivalent"], s_c["to_lower_equivalent"]
    opposite = (up["slope"]["estimate"] > 0) != (down["slope"]["estimate"] > 0)
    if opposite != s_c["opposite_signs"]:
        raise ClaimError("E30: S-c's sign reading is not that of its two slopes")
    if opposite:
        # Amendment 14: said beside the primary result, with both intervals
        direction = (
            "The slope has opposite signs in the two directions: "
            f"{num(up['slope']['estimate'], 2)} ({span(up['slope']['ci95'], 2)}) for moves to a league with a "
            f"higher Equivalent and {num(down['slope']['estimate'], 2)} ({span(down['slope']['ci95'], 2)}) for "
            "moves to a lower one."
        )
    else:
        direction = (
            f"The sign is the same in both directions: {num(up['slope']['estimate'], 2)} "
            f"({span(up['slope']['ci95'], 2)}) for moves to a league with a higher Equivalent and "
            f"{num(down['slope']['estimate'], 2)} ({span(down['slope']['ci95'], 2)}) for moves to a lower one."
        )
    s_d = full["S_d"]
    wider = s_d["ci95"][0] <= e["ci_low"] and s_d["ci95"][1] >= e["ci_high"]
    redrawn = (
        f"With the ten table values redrawn as well, the interval {'widens to' if wider else 'runs from'} "
        f"{num(s_d['ci95'][0], 2)} to {num(s_d['ci95'][1], 2)} (an approximation, read for its width only; it "
        "does not decide the case [@amend17])."
    )
    if len(full["S_e"]) != 8:
        raise ClaimError("E30: eight sensitivities are registered")
    return {
        "error": error,
        "left_out": left_out,
        "direction": direction,
        "opposite": opposite,
        "redrawn": redrawn,
        "lowest": lowest,
    }


def e30_count(d) -> str:
    """Amendment 17, rule 4: N counts players; the number of league changes is stated beside it."""
    return f"These players made {d['e30']['n_moves']:,} league changes."


def e30_section(d) -> str:
    """Results: the set-up, the registered sentence of the case with what stands beside it, the
    reading of Amendment 19 (rule 5) where it is printed, what was unseen (rules 4 and 8), and
    the registered checks that stay in the main text (rule 11)."""
    e, full = d["e30"], e30_full(d)
    sentence, s = e30_sentence(d), e30_secondary(d)
    permutation = full["primary"]["permutation"]
    chance = (
        "A random assignment of the ten league values to the ten leagues gave a slope at least as large in "
        f"{permutation['draws_with_slope_at_least_as_large']:,} of {permutation['draws']:,} draws."
    )
    setup = (
        "Players also move between the ten domestic leagues. For a move from A to B, the table "
        "predicts B's Equivalent minus A's (EuroCup values). A strong season can precede both a move "
        "and a return toward a player's usual production. To account for that drift, we fit a forecast on players "
        "who stayed, using last season's rate, the earlier career rate and whether last season exceeded it. For "
        "each mover we subtract this forecast from his rate in the new league. We regress that residual on the "
        "predicted change, with an intercept and one observation per move; that slope is the one primary result. "
        "The test covers "
        f"{e['n_moves']:,} league changes by {e['n_players']:,} players. The season in the new league is called the arrival season of a league change; these arrival seasons run from {e30_seasons(d)}. Every "
        "rule was registered before any outcome of a league change was read [@amend14; @amend17]; the "
        f"predictions were frozen and their hash published on {META['e30_freeze_day']}, and the outcomes were "
        f"joined once, on {META['e30_score_day']} (Appendix M)."
    )
    result = [sentence, E30_INTERVAL, chance]
    if s["opposite"]:
        result.append(s["direction"])  # Amendment 14: said beside the primary result
    result.append(s["error"])
    # what was unseen stands directly after the primary result (Amendment 19, rule 8: "beside")
    paragraphs = [setup, " ".join(result), e30_unseen(d)]
    if prints_first_page_words(d):
        paragraphs.append(e30_meaning(d))
    checks = [s["left_out"]]
    if not s["opposite"]:
        checks.append(s["direction"])
    checks.append(s["redrawn"])
    paragraphs.append("**Other registered checks (Table A21).** " + " ".join(checks))
    return "### The test on league changes\n\n" + "\n\n".join(paragraphs) + "\n\n"


def e30_limits(d) -> str:
    """Limitations: the limits of E30, once."""
    case, e = e30_case(d), d["e30"]
    sentence = e30_sentence(d)
    if case in ("null", "against"):
        return f"**League changes.** {sentence} {E30_NO_CAUSE} "
    s = e30_secondary(d)
    full = e30_full(d)
    s_b = full["S_b"][s["lowest"]]
    lowest = (
        f"the slope is lowest without {short_league(s['lowest'])} ({num(s_b['estimate'], 2)}, "
        f"{span(s_b['ci95'], 2)})"
    )
    tail = (
        "Players who change league are not a random sample, and the box scores are not the corrected corpus "
        f"of the {get(d['recipes'], 'n_targets')} arrivals."
    )
    if case in E30_TESTED and e["ci_high"] < 1:
        return (
            f"**League changes.** The changes were about {num(e['slope'], 2)} of the size the Equivalents imply "
            f"(interval {num(e['ci_low'], 2)} to {num(e['ci_high'], 2)} with the table held fixed; "
            f"{num(full['S_d']['ci95'][0], 2)} to {num(full['S_d']['ci95'][1], 2)} with its values redrawn); "
            f"{lowest}. {tail} "
        )
    parts = []
    if case in E30_TESTED and e["ci_low"] > 1:
        parts.append(
            f"On players who changed domestic league the slope's interval lies above 1 ({num(e['ci_low'], 2)} "
            f"to {num(e['ci_high'], 2)}): the changes were larger than the table implies."
        )
    elif case == "positive_not_separable":
        parts.append(sentence)
    parts.append(lowest[0].upper() + lowest[1:] + ".")
    parts.append(tail)
    return "**League changes.** " + " ".join(parts) + " "


def two_tests(d) -> str:
    """Amendment 19, rule 9: the league-changes test and the older-arrivals test side by side,
    by their facts; what each is evidence for; neither settles the other."""
    if e30_case(d) not in E30_TESTED:
        return ""
    e, o = d["e30"], older(d)
    if "it did not" not in e28_older(d)["e28_abs_older"]:
        raise ClaimError(
            "the older-arrivals reading changed; the paragraph on the two tests needs new wording"
        )
    return (
        "**Two tests outside the fitted arrivals.** The test on league changes covers ten leagues and "
        f"{e['n_moves']:,} changes, {e30_seasons(d)}. Its outcomes are domestic, from Proballers box scores, and it "
        "was registered before any outcome was read. It is evidence that the table's gaps appear when players "
        "change league, in seasons the table was fitted on. The test on older arrivals covers "
        f"{OLDER_WORDS[len(o['leagues'])]} leagues and {o['n']} arrivals, 2008–09 to 2015–16. Its outcomes are "
        "continental, its domestic box scores are the leagues' own, and its league-number comparison was added "
        "after the first scoring. It is the only evidence on an earlier period, where the league numbers did not "
        "improve the forecast. "
        # Amendment 26, rule 2: in the inconclusive state the clause states the outcome
        + (TWO_TESTS_END_INCONCLUSIVE if p1_is_inconclusive(d) else TWO_TESTS_END)
        + "\n\n"
    )


def club_rule(d) -> str:
    """The club section's short paragraph on which gap to use (Amendment 19, rule 6, says "may").
    Under Amendments 1 to 19 it gives the first sentence and points to the test on league changes;
    the reading of rule 5 is printed once, in Results. The registered reading for a club is the
    draft Amendment 20, rule 2, and is switched off."""
    if e30_case(d) == E30_NOT_RUN or not prints_first_page_words(d):
        return ""
    first = (
        "**Which gap to use.** To read a domestic line before a EuroLeague or EuroCup arrival, use the "
        "Equivalents as printed."
    )
    if amendment_20(d):
        return f"{first} {club_registered_reading(d)}\n\n"
    return (
        f"{first} What happened to players who changed domestic league is in Results (the test on league "
        "changes).\n\n"
    )


def e31_appendix(d) -> str:
    """Appendix M (Amendment 19, rule 7): the 2015 table against the destination-only forecast, its
    weighted value and the statement that its wording rule was settled after the result."""
    a = e31a(d)
    if a is None:
        return ""
    du, dw = a["T_D"]["unweighted"], a["T_D"]["minutes_weighted"]
    if du["reading"] == "above_zero":
        first = (
            f"{E31_TABLE} improves a destination-aware forecast by {num(du['difference'])} EFF/36 "
            f"({span(du['ci95'])}); the weighted value is {num(dw['difference'])} ({span(dw['ci95'])})"
        )
        if dw["reading"] == "includes_zero":
            first += ", not clearly above zero when weighted by playing time"
    else:
        first = (
            f"{E31_TABLE} adds nothing detectable to a destination-aware forecast ({num(du['difference'])}, "
            f"{span(du['ci95'])}; weighted by playing time, {num(dw['difference'])}, {span(dw['ci95'])})"
        )
    return (
        "**The 2015 table against a forecast that knows only the destination (exploratory).** "
        f"{get(d['e31'], 'table/purpose')} On the {get(d['e31'], 'n_targets')} arrivals of 2020–2025, {first}. "
        "The unweighted analysis decides these sentences, as in every other comparison of the paper; for this "
        "one that rule was settled after the result was seen [@amend17]. Table A23 gives every value."
    )


def table_e30(d) -> str:
    """Table A21 (Appendix M): every slope of E30, S-b to S-e."""
    full, e = e30_full(d), d["e30"]

    def row(result, what, n, estimate, ci):
        return [result, what, f"{n:,}", num(estimate), f"{num(ci[0])} to {num(ci[1])}"]

    rows = [
        row(
            "Primary",
            "all league changes",
            e["n_moves"],
            e["slope"],
            [e["ci_low"], e["ci_high"]],
        )
    ]
    for code in sorted(full["S_b"], key=lambda k: LEAGUE_NAMES[k]):
        v = full["S_b"][code]
        rows.append(
            row(
                "S-b",
                f"without {LEAGUE_NAMES[code]}",
                v["league_changes"],
                v["estimate"],
                v["ci95"],
            )
        )
    for key, label in (
        ("to_higher_equivalent", "moves to a league with a higher Equivalent"),
        ("to_lower_equivalent", "moves to a league with a lower Equivalent"),
    ):
        v = full["S_c"][key]
        rows.append(
            row(
                "S-c",
                label,
                v["league_changes"],
                v["slope"]["estimate"],
                v["slope"]["ci95"],
            )
        )
    rows.append(
        row(
            "S-d",
            "the ten table values redrawn as well (approximation; width only)",
            e["n_moves"],
            e["slope"],
            full["S_d"]["ci95"],
        )
    )
    for key in sorted(full["S_e"], key=int):
        v = full["S_e"][key]
        rows.append(
            row(
                f"S-e ({key})",
                v["label"].replace("-", "–"),
                v["league_changes"],
                v["estimate"],
                v["ci95"],
            )
        )
    cap = (
        "Table A21. The test on league changes: every registered slope. The slope of the unexplained change on "
        "the change the table predicts, with 95% bootstrap intervals (players resampled, the stayer forecast "
        "refitted in every draw). S-b: one league left out; S-c: one direction; S-d: the table's own "
        "uncertainty; S-e: the eight sensitivities."
    )
    r = d.get("e33")
    if r is not None:
        rows.append(
            row(
                "E33",
                "S-e (7) with the stayer forecast also fitted only on seasons before each move "
                "(added after the result; exploratory)",
                r["league_changes"],
                r["cutoff"]["estimate"],
                r["cutoff"]["ci95"],
            )
        )
        # Amendment 22: the secondary result, with one intercept per arrival season under both
        # stayer forecasts, is "printed with their intervals in the appendix table"
        by = r["season_intercepts"]
        for what, key in (
            (
                "E33 with one intercept per arrival season in place of the single intercept",
                "cutoff",
            ),
            (
                "S-e (7) with one intercept per arrival season in place of the single intercept",
                "pooled",
            ),
        ):
            rows.append(
                row(
                    "E33",
                    what,
                    r["league_changes"],
                    by[key]["estimate"],
                    by[key]["ci95"],
                )
            )
        cap += (
            " E33: one check added after the result was seen, and the same two slopes with one "
            "intercept per arrival season [@amend22]."
        )
    return (
        cap
        + "\n\n"
        + md_table(["Result", "What", "League changes", "Slope", "95% interval"], rows)
    )


def table_e31b(d) -> str:
    """Table A22 (Appendix M): the two scales on league changes (E31b)."""
    b = e31b(d)

    def ci(c):
        return f"{num(c['ci95'][0])} to {num(c['ci95'][1])}"

    rows = [
        [
            "Stayer forecast alone",
            num(b["mae_stayer_forecast"]["estimate"]),
            ci(b["mae_stayer_forecast"]),
            "n/a",
            "n/a",
        ]
    ]
    for key, label in (
        ("paper", "Stayer forecast + the Equivalents"),
        ("published", "Stayer forecast + the 2015 table"),
    ):
        scale = b["scales"][key]
        last = max(scale["coefficient_by_scored_season"], key=int)
        coefficient = scale["coefficient_by_scored_season"][last]
        rows.append(
            [
                label,
                num(scale["mae"]["estimate"]),
                ci(scale["mae"]),
                num(coefficient["estimate"], sign=True),
                ci(coefficient),
            ]
        )
    cap = (
        f"Table A22. Two league scales on the same league changes (E31b). Mean absolute error (EFF/36) on the "
        f"{b['scored_league_changes']:,} league changes of arrival seasons from {b['first_scored_arrival_season']}, "
        "with 95% bootstrap intervals. *Coefficient*: the one coefficient of the scale, fitted through the "
        "origin on league changes of earlier seasons; the value shown is the one used for the last scored season."
    )
    return (
        cap
        + "\n\n"
        + md_table(
            ["Forecast", "MAE", "95% interval", "Coefficient", "95% interval"], rows
        )
    )


def table_e31a(d) -> str:
    """Table A23 (Appendix M): the 2015 table on the arrivals of 2020-2025 (E31a, exploratory)."""
    a = e31a(d)
    names = {
        "T_D": "Destination-only forecast minus the 2015-table forecast",
        "T_O": "2015-table forecast minus the league-aware forecast",
    }
    rows = []
    for key in ("T_D", "T_O"):
        for weighting, label in (
            ("unweighted", "unweighted"),
            ("minutes_weighted", "weighted by playing time"),
        ):
            r = a[key][weighting]
            rows.append(
                [
                    names[key],
                    label,
                    num(r["mae_left"]),
                    num(r["mae_right"]),
                    num(r["difference"], sign=True),
                    f"{num(r['ci95'][0])} to {num(r['ci95'][1])}",
                    num(r["detectable_80"]),
                ]
            )
    cap = (
        f"Table A23. A league table printed in 2015 on the {get(d['e31'], 'n_targets')} arrivals of 2020–2025 "
        "(E31a, exploratory). Paired differences in mean absolute error (EFF/36); a positive difference favours "
        "the second forecast of the row. Intervals are 95%, clustered by player and destination club-season. "
        "*Detectable*: the difference that would have been detected with 80% power."
    )
    return (
        cap
        + "\n\n"
        + md_table(
            [
                "Comparison",
                "Weighting",
                "MAE, first",
                "MAE, second",
                "Difference",
                "95% interval",
                "Detectable",
            ],
            rows,
        )
    )


def e30_appendix(d) -> str:
    """Appendix M: the design numbers, the order of events and the tables of E30 and E31."""
    parts = []
    if e30_case(d) != E30_NOT_RUN:
        full, e = e30_full(d), d["e30"]
        primary, model = full["primary"], full["stayer_model"]
        c = model["coefficients"]
        quantiles = primary["permutation"]["permuted_slope_quantiles"]
        up, down = (
            full["S_c"]["to_higher_equivalent"],
            full["S_c"]["to_lower_equivalent"],
        )
        parts.append(
            f"**The design in numbers.** The test covers {e['n_moves']:,} league changes by {e['n_players']:,} "
            f"players. The stayer forecast, fitted on {model['n']:,} pairs of seasons of players who stayed in "
            f"their league, is {num(c['intercept'])} {signed(c['x'])} x {signed(c['h'])} h {signed(c['a'])} a, "
            f"with x, h and a as in the fitted "
            f"equation of the main text, and a residual spread of {num(model['residual_sd'], 2)} EFF/36. Its "
            f"inputs come from {full['corpus']['files']} box-score files; every interval comes from "
            f"{full['bootstrap_draws']:,} bootstrap draws that resample players and refit the stayer forecast. In "
            f"{primary['permutation']['draws']:,} random assignments of the ten league values, the middle 95% of "
            f"slopes ran from {num(quantiles['2.5'])} to {num(quantiles['97.5'])}. The fitted line's intercept, "
            f"the mean unexplained change when the table predicts none, is {num(primary['intercept'], sign=True)} "
            f"EFF/36. A slope of {num(primary['detectable_slope_80'], 2)} would have been detected with 80% power "
            "(descriptive). The mean unexplained change is "
            f"{num(up['mean_e']['estimate'], sign=True)} ({span(up['mean_e']['ci95'])}) for moves to a league with "
            f"a higher Equivalent and {num(down['mean_e']['estimate'], sign=True)} ({span(down['mean_e']['ci95'])}) "
            "for moves to a lower one."
        )
        parts.append(
            "**Order of events.** Amendment 14, which registers the test, was pushed alone on "
            f"{META['amend14_time']}, before any code for it existed; Amendment 17, which fixes how its rules are "
            f"read, on {META['amend17_time']}. The frozen predictions were pushed on {META['e30_freeze_time']}, "
            f"and the sha256 of the frozen file was added to the public hash list on {META['e30_hash_time']}. The "
            f"outcomes were joined once, in one retained scoring run on {META['e30_score_day']}, which read the "
            "frozen file by its sha256. The same season can be the outcome of one league change and the starting "
            "point of the next, so the files could not be sealed from each other; what was fixed in advance is "
            "every rule, the code and the frozen predictions."
        )
        parts.append(
            "**The checks in full.** Table A21 lists every registered slope, with the interval of each "
            "direction and the eight registered sensitivities. The label of S-e (3) is the registered one: it counts "
            "four leagues and says January 2026. The 2025–26 files of five leagues stop between 26 December 2025 and "
            "8 January 2026 (Limitations); the fifth is the ABA League. S-e (3) "
            "leaves out every league change of 2025–26, so its slope does not depend on that count. When the ten table values are redrawn as well, "
            "each from its committed interval, redrawing adds noise to the predicted change, so the centre of "
            "that interval sits low by construction; it is read for its width only [@amend17]."
            + e33_appendix_sentence(d)
        )
        parts += [table_e30(d), table_e31b(d)]
        b = e31b(d)
        paper, published = b["scales"]["paper"], b["scales"]["published"]
        if d.get("e31") is not None:
            scores = get(d["e31"], "table/scores_used")
            eurocup = {
                r["source_league"]: float(r["acb16_equivalent_eff36"])
                for r in d["exchange"]
                if r["destination"] == "eurocup"
            }
            last = max(paper["coefficient_by_scored_season"], key=int)
            signs = (
                paper["coefficient_by_scored_season"][last]["estimate"] > 0
                and published["coefficient_by_scored_season"][last]["estimate"] < 0
            )
            if signs and max(scores, key=scores.get) == min(eurocup, key=eurocup.get):
                parts.append(
                    "The two coefficients have opposite signs because the scales run in opposite directions: the "
                    f"2015 table gives {short_league(max(scores, key=scores.get))} its highest score among the ten "
                    "leagues, and the Equivalents give it their lowest value."
                )
    if e31a(d) is not None:
        parts += [e31_appendix(d), table_e31a(d)]
    if not parts:
        return ""
    title = (
        "### M. The test on league changes and the 2015 table"
        if e30_case(d) != E30_NOT_RUN
        else "### M. A league table printed in 2015"
    )
    return "\n\n" + title + "\n\n" + "\n\n".join(parts)


def e30_blocks(d) -> dict:
    """What the first page, Results, the club section, Limitations and the appendix say about league
    changes and about the published table, for the case.

    While E30 is not run the paper says nothing about league changes (Amendment 16, rule 3). A Clear
    result whose interval lies below 1 is stated on the first page in the words of Amendment 19,
    rule 1; every other case keeps the registered wording of the case.
    """
    case = e30_case(d)
    offer = (
        "This paper offers a named league table for European basketball arrivals, the same-player benchmark "
        "of translation factors against it, and its {tests}."
    )
    clause = e31_clause(d)
    if clause and amendment_20(d):
        # Amendment 20, rule 5: the list of Amendment 19, rule 7, with no number
        adds = [
            "an interval for each league number",
            "one fitted equation for both competitions",
        ]
        if case != E30_NOT_RUN:
            adds.insert(0, "a registered test on league changes")
        if case != E30_NOT_RUN:
            # Amendment 29, rule 1: the abstract names the two additions that the first page shows
            clause = clause.rstrip().rstrip(".") + f"; {FIRST_PAGE_ADDS}. "
        else:
            clause = (
                clause.rstrip().rstrip(".")
                + f"; this paper adds {', '.join(adds)} and a refit before each season. "
            )
    # Related work: a public scale that is FITTED on players who changed league. While E30 is not
    # run the paper says nothing about league changes (Amendment 16, rule 3).
    fitted = "The Equivalents are fitted only on first continental seasons"
    shared = {
        "mover_interval_scope": (
            "For league changes, the primary interval refits the stayer forecast with the league table held fixed. "
            "Table A21 also shows how the interval changes when the league values vary."
            if case != E30_NOT_RUN
            else ""
        ),
        "e31_section": e31_section(d),
        "e30_appendix": e30_appendix(d),
        "two_tests": two_tests(d),
        # the abstract's status clause points back at the 2015 clause when there is one
        "abs_arrivals": "those arrivals" if clause else "the 2020–2025 arrivals",
        "club_rule": club_rule(d),
        # Amendment 20, rule 6: the heading of the Results section on translation
        "translation_heading": "A translation factor adds nothing detectable on top of the league numbers"
        if amendment_20(d)
        else "Simple league context matches the measured translation gain",
        "amend20_note": (
            " Five named pairs of newcomers in the main text once the frozen test is scored, and "
            "further wording, were allowed on 18 November 2026, before scoring [@amend20]."
            # Amendment 26, rule 8
            + (f" {P1_PAIRS_NOT_PRINTED}" if p1_is_inconclusive(d) else "")
        )
        if amendment_20(d)
        else "",
        "rival_fit_sentence": (
            f"{fitted}."
            if case == E30_NOT_RUN
            else "That scale is fitted on league changes, among other moves; "
            f"{fitted[0].lower() + fitted[1:]} and were then tested on domestic league changes, under rules "
            "registered beforehand."
        ),
        # the short Related work names what that scale is fitted on, where the paper speaks of league changes
        "rival_clause": ""
        if case == E30_NOT_RUN
        else ", fitted on league changes among other moves,",
        # "no analysis had read", not "were unread": Appendix N says that statistic lines of the
        # season were displayed in a literature search, and the registration of 16 November 2026
        # words it so ("before any 2026–27 player statistic has been read by any analysis").
        # Claude Science's check and Amir's decision of 22 November 2026.
        "methods_unread": (
            "We distinguish them from the outcome-blinded older-seasons test and the 2026–27 test."
            if case == E30_NOT_RUN
            else "We distinguish them from three tests whose outcomes no analysis had read when their rules were "
            "fixed: league changes, older seasons and 2026–27."
        ),
        "amend19_note": (
            "The wording of the first page was settled on 18 November 2026 [@amend19]."
            if case == E30_NOT_RUN
            else "The first page's wording and the reading of the slope per league-number gap were settled after "
            "the league-changes result [@amend19]."
        ),
        # the same disclosure in the main text (Methods), with the pointer to the note
        "methods_settled": (
            "The wording of the first page was settled on 18 November 2026 (Appendix N)."
            if case == E30_NOT_RUN
            else "The first page's wording and the reading of the slope per league-number gap were settled after "
            "the league-changes result (Appendix N)."
        ),
        # Amendment 21: where the paper cites it
        "amend21_note": (
            " The conclusion's wording of translation's increment was settled later the same day [@amend21]."
            if case == E30_NOT_RUN
            else " The conclusion's wording of translation's increment, and the interval with the table values "
            "redrawn on the first page, were settled later the same day [@amend21]."
        ),
    }
    if case == E30_NOT_RUN:
        return {
            "e30_abstract": clause,
            "e30_intro": "",
            "e30_conclusion": "",
            "e30_limits": "",
            "e30_section": "",
            "e30_fig1": "",
            "offer_sentence": offer.format(tests="test on frozen forecasts"),
            **shared,
        }
    sentence = e30_sentence(d)
    count = e30_count(d)
    tested = case in E30_TESTED
    n_pairs = len(d["e30_pairs"]) if d.get("e30_pairs") else 0
    if n_pairs and float(d["e30_pairs"][0]["predicted_change"]) < 0:
        raise ClaimError(
            "E30: a league pair is drawn from the lower to the higher Equivalent"
        )
    if prints_first_page_words(d):
        # Amendment 19, rules 1 and 2
        statement = E30_FROZEN_FIRST + e30_statement(d) + "."
        code, low = e30_lowest(d)
        abstract = statement + " "
        if clause.count(" and ") == 1 and "these league changes" in clause:
            abstract += (
                "A league table printed in 2015 is not distinguishable from it, there or on the 2020–2025 "
                "arrivals. "
            )
        else:
            abstract += clause
        refit = ""
        if amendment_20(d):
            s7 = e30_full(d)["S_e"]["7"]
            if S7_LABEL.search(s7["label"]) is None:
                raise ClaimError(
                    "E30: sensitivity 7 is not the table refitted only on earlier arrivals"
                )
            refit = (
                f", and {num(s7['estimate'], 2)} with the table refitted only on arrivals before the season "
                "of each move"
            )
        intro = (
            f"{statement} {FIRST_PAGE_SLOPE} {count[:-1]}; the slope is lowest without {short_league(code)} "
            f"({num(low['estimate'], 2)}){refit}. {e30_redrawn_intro(d)} "
        )
        conclusion = f"{statement} {count} "
    else:
        abstract = f"{sentence} {clause}"
        # the published table enters the first page in one clause, in the abstract only
        # (Amendment 16, rule 3); the introduction and the conclusion leave it to Results
        intro = f"{sentence} {count} " + (
            "The table was not fitted to these league changes and not scored on them before this test, "
            "though the same seasons are inputs to the paper's forecasts. "
            if tested
            else ""
        )
        conclusion = f"{sentence} {count} "
    marked = short_league(e30_lowest(d)[0])
    return {
        "e30_abstract": abstract,
        # Amendment 29, rule 1: the paragraph ends with these sentences
        "e30_intro": " " + intro.rstrip(),
        "e30_conclusion": conclusion,
        "e30_limits": e30_limits(d).rstrip(),
        "e30_section": e30_section(d),
        "e30_fig1": (
            f" Right: the {n_pairs} league pairs of the test on league changes: half the difference in mean "
            "unexplained change between opposite moves, against "
            f"the predicted gap (orange: pairs with {marked}). The line is the registered slope from all "
            "league changes with its 95% interval, drawn through the origin; it is not a fit to these points. "
            f"The {n_pairs} points come from ten numbers and are not {n_pairs} independent tests."
            if n_pairs
            else ""
        ),
        # Amendment 26, rule 5: in the inconclusive state the sentence states the outcome
        "offer_sentence": offer.format(
            tests=OFFER_TESTS_INCONCLUSIVE if p1_is_inconclusive(d) else OFFER_TESTS
        ),
        **shared,
    }


ABSTRACT_INTERVAL = re.compile(
    r"(?:95% )?interval [+−-]?\d+(?:\.\d+)? to [+−-]?\d+(?:\.\d+)?"
)
#: The unit in words (Amendment 23, rule 1; gate G23a): the 36 of "per 36 minutes" is the unit's
#: own number. The counter removes exactly these words, as it removes "EFF/36", and nothing else.
ABSTRACT_UNIT_WORDS = "per 36 minutes"
ABSTRACT_LABEL = re.compile(
    r"\b\d{1,2} [A-Z][a-z]+ \d{4}\b|\b(?:19|20)\d{2}(?:–\d{2,4})?\b|EFF/36"
    rf"|\b{ABSTRACT_UNIT_WORDS}\b"
)
ABSTRACT_NUMBER = re.compile(r"[+−-]?\d[\d,]*(?:\.\d+)?%?")


def abstract_numbers(abstract: str) -> dict:
    """The numbers of the abstract, counted by the rule Amendment 17 registers.

    "A number is an estimate, a count or a league-rate value; an interval counts together
    with its estimate; dates, season labels and the unit do not count." Implemented as: every
    numeric token written in digits, after removing intervals ("interval a to b", with or
    without its level), dates, season and year labels and the unit: EFF/36 and, since
    Amendment 23, rule 1, exactly the words "per 36 minutes". ``tokens`` is the
    stricter count that also counts each interval bound and the interval level; it is
    printed in the render manifest and decides nothing.
    """
    labels_out = ABSTRACT_LABEL.sub(" ", abstract)
    quantities = ABSTRACT_NUMBER.findall(ABSTRACT_INTERVAL.sub(" ", labels_out))
    return {
        "quantities": len(quantities),
        "tokens": len(ABSTRACT_NUMBER.findall(labels_out)),
        "listed": quantities,
    }


HOOK = "gives the same forecast as about 19"
HOOK_CONDITION = "career history equals the domestic rate"
SELF_CLAIMS = re.compile(
    r"rather than a new estimator|clubs (?:already |now |routinely )?use (?:league )?translation|"
    r"\b(?:the|a) first (?:same-|pre-registered|public|test of|benchmark|league table|paper|study)|"
    r"\bfor the first time\b",
    re.IGNORECASE,
)
LEAGUE_CHANGE_WORDS = re.compile(
    r"league changes?\b|changed (?:domestic )?league|league changers?|domestic moves?\b",
    re.IGNORECASE,
)


def check_abstract_numbers(abstract: str, limit: int = ABSTRACT_MAX_NUMBERS) -> dict:
    """Gate G17b (Amendment 17): refuse an abstract that carries more numbers than its limit."""
    counts = abstract_numbers(abstract)
    if counts["quantities"] > limit:
        raise ClaimError(
            f"Amendment 16, rule 4 (counted as Amendment 17 registers): the abstract carries "
            f"{counts['quantities']} numbers ({counts['listed']}); at most {limit} are allowed"
        )
    return counts


def check_first_page(text: str, case: str, limit: int = ABSTRACT_MAX_NUMBERS) -> dict:
    """Gates of Amendment 16 on the composed text; returns the abstract's number counts.

    G16a: the title is the one registered for the case, and with a Null or Against result, or
    with E30 not run, the abstract does not contain "tested", "validated" or "never fitted to".
    Also: rule 1 (the Equivalents line carries its condition in the same sentence or the next),
    rule 2 (no "never saw"), rule 3 (nothing about league changes while E30 is not run),
    rule 4 (the abstract's numbers, counted and limited as Amendment 17 registers; gate G17b)
    and rule 6 (what the paper says of itself).
    """
    # stated again here, not taken from title_for(): the gate must not share the selector's logic
    registered = (
        TITLE_TESTED if case in ("clear", "positive_named_limit") else TITLE_ADDS
    )
    if text.splitlines()[1] != f'title: "{registered}"':
        raise ClaimError(
            f"G16a: the title is not the one Amendment 16 registers for the case '{case}'"
        )
    abstract = text.split("## Abstract")[1].split("\n## ")[0]
    if case in E30_NO_TEST_WORDS:
        found = [w for w in G16A_BANNED if w in abstract.lower()]
        if found:
            raise ClaimError(
                f"G16a: the abstract contains {found} while the E30 case is '{case}'"
            )
    if "never saw" in text.lower():
        raise ClaimError(
            "Amendment 16, rule 2: the words 'never saw' are not used anywhere"
        )
    if case == E30_NOT_RUN and (hit := LEAGUE_CHANGE_WORDS.search(text)):
        raise ClaimError(
            f"Amendment 16, rule 3: E30 is not run, yet the paper mentions '{hit.group(0)}'"
        )
    if hit := SELF_CLAIMS.search(text):
        raise ClaimError(
            f"Amendment 16, rule 6: the paper may not say '{hit.group(0)}'"
        )
    body = main_text(text)
    for name in ("Abstract", "Figure 1."):
        if "European League Equivalents" not in (
            abstract
            if name == "Abstract"
            else next(ln for ln in body.splitlines() if ln.startswith("![Figure 1."))
        ):
            raise ClaimError(
                f"Amendment 16, rule 1: 'European League Equivalents' is missing from {name}"
            )
    sentences = re.split(r"(?<=[.!?])\s+", body)
    for i, sentence in enumerate(sentences):
        if HOOK in sentence:
            nearby = (
                sentence + " " + (sentences[i + 1] if i + 1 < len(sentences) else "")
            )
            if HOOK_CONDITION not in nearby:
                raise ClaimError(
                    "Amendment 16, rule 1: the Equivalents line appears without its condition "
                    f"('when {HOOK_CONDITION}') in the same sentence or the next"
                )
    return check_abstract_numbers(abstract, limit)


# ---------------------------------------------------------------- Amendment 19: gates G19b and G19c
def sentences_of(text: str) -> list:
    return [s for s in re.split(r"(?<=[.!?])\s+", text) if s]


def section_of(text: str, name: str) -> str:
    """One level-2 section of the paper before the references."""
    return main_text(text).split(f"\n## {name}\n")[1].split("\n## ")[0]


def reading_marks(d) -> list:
    """The phrases that print the reading of Amendment 19, rule 5 (gate G19b)."""
    marks = [
        "about as large as the gaps between league numbers",
        "by about the gap between the two league numbers",
    ]
    if d.get("e30") is not None:
        per = league_number_reading(d)["per"]
        marks.append(f"moved by {num(per[0], 2)} EFF/36")
    return marks


# ---------------------------------------------------------------- Amendment 20: named pairs, the club's reading
#: Amendment 20, rule 1: how many pairs the main text prints.
NAMED_PAIRS = 5
NUMBER_WORDS = {
    1: "one",
    2: "two",
    3: "three",
    4: "four",
    5: "five",
    6: "six",
    7: "seven",
    8: "eight",
    9: "nine",
    10: "ten",
}
E32_D, E32_O = "history_destination_slope", "source_ridge_10"
#: The columns the selection of rule 1 may see: the key and columns frozen on 3 November 2026.
E32_PAIR_FROZEN = (
    "league_dest",
    "player_a",
    "league_src_a",
    "pir_per36_src_a",
    f"{E32_D}_a",
    f"{E32_O}_a",
    "player_b",
    "league_src_b",
    "pir_per36_src_b",
    f"{E32_D}_b",
    f"{E32_O}_b",
    "gap_league_aware",
    "gap_destination_only",
)
#: What each newcomer has done so far: printed, never used to choose a row.
E32_PAIR_OUTCOME = (
    "games_dest_a",
    "pir_per36_dest_a",
    "games_dest_b",
    "pir_per36_dest_b",
)
NAMED_TABLE_MARK = "of 2026–27 newcomers whose order the league numbers reverse"
COMPETITIONS = {"euroleague": "EuroLeague", "eurocup": "EuroCup"}
#: The phrase that prints the registered reading for a club (Amendment 20, rule 2; gate G20c).
CLUB_READING_MARK = "of the gap between the two leagues' Equivalents"


# ---------------------------------------------------------------- E32: the named-newcomer tables
#: Amendment 15 (E32) and Amendment 18, rule 9: how many newcomers and pairs the tables print.
E32_TOP = 10
E32_PAIRS_PRINTED = 10
#: The states of the frozen test in which the E32 tables are printed: scored, and not adjudicable
#: (Amendment 15: "If fewer than 60 newcomers are scored, E32 prints all of them and the paper
#: says so"). Before scoring no named player is printed. For an inconclusive test no registration
#: says whether named newcomers are printed, so committed E32 tables are refused there.
E32_STATES = ("scored", "not_adjudicable")
E32_SUMMARY_KEYS = (
    "n_newcomers",
    "print_all",
    "players_printed",
    "pairs_whose_order_differs",
    "pairs_printed",
    "printed_pairs_where_the_league_aware_order_held",
    "printed_pairs_tied_in_the_outcome",
    "gates",
)
E32_OUTCOME = "pir_per36_dest"


def e32_printed(d) -> bool:
    """Whether the paper prints the E32 tables: the tables are committed and the frozen test is
    scored, or not adjudicable for fewer newcomers than registered."""
    if not d.get("e32_tables") or d.get("p1") is None:
        return False
    status = p1_check(d)
    if status == "inconclusive":
        raise ClaimError(
            "E32: the named-newcomer tables are committed, and the frozen test is inconclusive; no "
            "registration says whether named newcomers are printed in that state"
        )
    return status in E32_STATES


def e32_by_competition(players: list) -> list:
    """The rows of the table of named newcomers, per competition, EuroLeague first."""
    out = []
    for code in COMPETITIONS:
        rows = [r for r in players if r["league_dest"] == code]
        if rows:
            out.append((code, rows))
    if sum(len(rows) for _, rows in out) != len(players):
        raise ClaimError("E32: a named newcomer is in neither competition")
    return out


def e32_check(d) -> None:
    """What must hold before a named newcomer is printed (Amendment 15, E32; Amendment 18,
    rule 9): the two tables and their summary are committed together, gate G32 passed, the
    tables were built from the scored rows of the committed score record, and each table has
    the registered rows in the registered order."""
    players, pairs, summary = (
        d.get("e32_players"),
        d.get("e32_pairs"),
        d.get("e32_summary"),
    )
    if players is None or pairs is None or summary is None:
        raise ClaimError(
            "E32: the two tables and their summary must be committed together"
        )
    if any(k not in summary for k in E32_SUMMARY_KEYS):
        raise ClaimError(
            "E32: the summary beside the pair table is not the E32 summary"
        )
    if summary.get("synthetic") and not d.get("p1_rehearsal"):
        raise ClaimError(
            "E32: these tables are a rehearsal on made-up players (synthetic: true)"
        )
    if summary["gates"].get("G32", {}).get("status") != "passed":
        raise ClaimError(
            "E32: gate G32 (rows chosen from frozen forecasts only) did not pass"
        )
    p, status = d["p1"], p1_check(d)
    if not d.get("p1_rehearsal"):
        if summary.get("scored_rows_sha256") != p.get("scored_rows", {}).get(
            "sha256"
        ) or int(summary["n_newcomers"]) != int(p["n_scored"]):
            raise ClaimError(
                "E32: the tables were not built from the scored rows of the committed score record"
            )
    if bool(summary["print_all"]) != (status == "not_adjudicable"):
        raise ClaimError(
            "E32: 'all newcomers are printed' must hold exactly when fewer newcomers than registered were scored"
        )
    if int(summary["players_printed"]) != len(players) or int(
        summary["pairs_whose_order_differs"]
    ) != len(pairs):
        raise ClaimError("E32: the summary does not count the rows of its tables")
    printed = [r for r in pairs if r["printed"] == "True"]
    if (
        len(printed) != int(summary["pairs_printed"])
        or len(printed) != min(E32_PAIRS_PRINTED, len(pairs))
        or pairs[: len(printed)] != printed
    ):
        raise ClaimError(
            "E32: the printed pairs are not the first ten rows of the table of changed pairs"
        )
    total = 0
    for _, rows in e32_by_competition(players):
        sizes = {int(r["newcomers_in_competition"]) for r in rows}
        if len(sizes) != 1:
            raise ClaimError("E32: a competition has two counts of newcomers")
        n = sizes.pop()
        total += n
        whole = summary["print_all"] or n <= 2 * E32_TOP
        ranks = (
            list(range(1, n + 1))
            if whole
            else [*range(1, E32_TOP + 1), *range(n - E32_TOP + 1, n + 1)]
        )
        groups = ["all"] * n if whole else ["highest"] * E32_TOP + ["lowest"] * E32_TOP
        forecasts = [float(r[E32_O]) for r in rows]
        if (
            [int(r["rank_league_aware"]) for r in rows] != ranks
            or [r["group"] for r in rows] != groups
            or any(b > a for a, b in zip(forecasts, forecasts[1:]))
        ):
            raise ClaimError(
                "E32: a table of named newcomers is not the ten highest and the ten lowest by the frozen "
                "league-aware forecast (or the whole competition)"
            )
    if total != int(summary["n_newcomers"]):
        raise ClaimError("E32: the competitions do not add up to the newcomers scored")


def e32_pointer_text(d) -> str:
    """The main-text pointer to the named-newcomer tables (Amendment 19, rule 12)."""
    if p1_check(d) == "not_adjudicable":
        return (
            f"Fewer than {d['p1']['min_n']} newcomers were scored, so all of them are named with their frozen "
            "forecasts in Appendix L (E32) [@amend15]."
        )
    return "The newcomers are named with their frozen forecasts in Appendix L (E32) [@amend15]."


def e32_appendix(d) -> list:
    """Appendix L: the two registered tables of E32 (Amendment 15; Amendment 18, rule 9). The
    ten highest and the ten lowest newcomers per competition by the frozen league-aware forecast,
    or the whole competition when it has twenty or fewer; and the ten changed pairs with the count
    of all such pairs. Nothing is computed. What a newcomer has produced so far is the last column
    and chose no row."""
    if not e32_printed(d):
        return []
    e32_check(d)
    players, pairs, summary = d["e32_players"], d["e32_pairs"], d["e32_summary"]
    competitions = e32_by_competition(players)
    first = E32_FIRST_TABLE
    last = first + len(competitions) - 1
    names = (
        f"Tables A{first} and A{last} name" if last > first else f"Table A{first} names"
    )
    said = (
        f" Fewer than {d['p1']['min_n']} newcomers were scored, so all of them are printed."
        if summary["print_all"]
        else ""
    )
    out = [
        f"**Named newcomers with their frozen forecasts (E32).** {names} newcomers of 2026–27 with the "
        f"forecasts that were frozen on {META['freeze_time'].split(',')[0]} [@amend15; @amend18]. In each "
        "competition the newcomers are ordered by the frozen league-aware forecast, ties by name; the tables "
        "print the ten highest and the ten lowest, and a competition with twenty newcomers or fewer whole."
        f"{said} Every row was chosen from frozen forecast columns only. What a newcomer has produced so far "
        f"(EFF/36 on continental games through {META['p1_cutoff']}) is the last column; it chose no row, and "
        "E32 computes no result."
    ]
    header = [
        "Rank",
        "Newcomer",
        "Source league",
        "Domestic rate, last season",
        "Forecast, destination only",
        "Forecast, league-aware",
        "Produced so far",
    ]
    for k, (code, rows) in enumerate(competitions, start=first):
        n = int(rows[0]["newcomers_in_competition"])
        which = (
            f"all {n}"
            if len(rows) == n
            else f"the ten highest and the ten lowest of {n}"
        )
        cap = (
            f"Table A{k}. {COMPETITIONS[code]} newcomers of 2026–27 by the frozen league-aware forecast (E32): "
            f"{which}. Rates and forecasts are EFF/36."
        )
        body = [
            [
                r["rank_league_aware"],
                r["player_name"],
                LEAGUE_NAMES[r["league_src"]],
                num(float(r["pir_per36_src"]), 1),
                num(float(r[E32_D]), 1),
                num(float(r[E32_O]), 1),
                num(float(r[E32_OUTCOME]), 1),
            ]
            for r in rows
        ]
        out.append(cap + "\n\n" + md_table(header, body))
    total = len(pairs)
    reverse = (
        "Among these newcomers, pairs in the same competition and from different source leagues whose order is "
        "strictly reversed between the destination-only forecast and the league-aware forecast are the calls "
        "the table changes; a tie in either forecast is not a reversal [@amend18]."
    )
    if total == 0:
        out.append(
            f"**The calls the table changes (E32).** {reverse} No such pair exists."
        )
        return out
    printed = [r for r in pairs if r["printed"] == "True"]
    held = int(summary["printed_pairs_where_the_league_aware_order_held"])
    tied = int(summary["printed_pairs_tied_in_the_outcome"])
    k = last + 1
    shown = (
        f"the {NUMBER_WORDS[len(printed)]} with the largest gap in the league-aware forecast, over both "
        "competitions together"
        if total > len(printed)
        else "all of them"
    )
    out.append(
        f"**The calls the table changes (E32).** {reverse} There {'is' if total == 1 else 'are'} {total} such "
        f"pair{'s' if total != 1 else ''}. Table A{k} prints {shown}. In {held} of the {len(printed)} printed "
        f"pair{'s' if len(printed) != 1 else ''} the league-aware order is the one that holds so far"
        + (f" ({tied} tied)" if tied else "")
        + ": described and not tested [@amend15]."
    )
    cap = (
        f"Table A{k}. The calls the table changes (E32): pairs of newcomers ordered by the gap in the "
        "league-aware forecast, largest first. In each pair the first player is the one the league-aware "
        "forecast puts higher. Forecasts and rates are EFF/36."
    )
    body = []
    for i, r in enumerate(printed, start=1):
        for side in ("a", "b"):
            body.append(
                [
                    str(i),
                    COMPETITIONS[r["league_dest"]],
                    r[f"player_{side}"],
                    LEAGUE_NAMES[r[f"league_src_{side}"]],
                    num(float(r[f"{E32_D}_{side}"]), 1),
                    num(float(r[f"{E32_O}_{side}"]), 1),
                    num(float(r[f"{E32_OUTCOME}_{side}"]), 1),
                ]
            )
    out.append(
        cap
        + "\n\n"
        + md_table(
            [
                "Pair",
                "Competition",
                "Newcomer",
                "Source league",
                "Forecast, destination only",
                "Forecast, league-aware",
                "Produced so far",
            ],
            body,
        )
    )
    return out


def named_pairs_printed(d) -> bool:
    """Whether the main text prints the table of five named pairs (Amendment 20, rule 1): when
    the amendment is in force, in every state in which the E32 tables are printed."""
    return amendment_20(d) and d.get("e32_pairs") is not None and e32_printed(d)


def named_pairs_selection(rows: list) -> list:
    """Gate G20a: the pairs of the main-text table are the first five rows of the committed E32
    table of changed pairs. This step receives the frozen columns only: the outcome columns are
    dropped before anything is chosen, and the registered order of the table is checked."""
    try:
        view = [{k: r[k] for k in E32_PAIR_FROZEN} for r in rows]
    except KeyError as exc:
        raise ClaimError(
            f"E32: the table of changed pairs lacks the column {exc} that Amendment 20, rule 1, prints"
        ) from None
    gaps = [float(r["gap_league_aware"]) for r in view]
    if any(b > a for a, b in zip(gaps, gaps[1:])):
        raise ClaimError(
            "G20a: the E32 table of changed pairs is not ordered by the gap in the league-aware forecast"
        )
    for r in view:
        reversed_ = float(r["gap_league_aware"]) > 0 > float(r["gap_destination_only"])
        if not reversed_ or r["league_src_a"] == r["league_src_b"]:
            raise ClaimError(
                "G20a: a row of the E32 table is not a pair from different source leagues whose order the "
                "league numbers reverse"
            )
    return view[:NAMED_PAIRS]


def named_pairs_block(d) -> str:
    """Amendment 20, rule 1: the first five of the registered pairs, each player with his frozen
    forecasts and what he has done so far, and beside it the count for all registered pairs,
    described and not tested. Nothing is computed and no conclusion is drawn."""
    if (d.get("e32_pairs") is not None or d.get("e32_tables")) and (
        d.get("p1") is None or p1_check(d) == "pending"
    ):
        raise ClaimError(
            "G20b: an E32 table of named newcomers exists and the frozen test has no score record"
        )
    if not named_pairs_printed(d):
        return ""
    e32_check(d)
    rows, summary = d["e32_pairs"], d["e32_summary"]
    cite = "[@amend15; @amend20]"
    total = len(rows)
    if total == 0:
        return (
            "No pair of 2026–27 newcomers in the same competition and from different source leagues has its "
            f"order reversed by the league numbers (E32) {cite}."
        )
    chosen = named_pairs_selection(rows)
    registered, held = (
        int(summary["pairs_printed"]),
        int(summary["printed_pairs_where_the_league_aware_order_held"]),
    )
    tied = int(summary["printed_pairs_tied_in_the_outcome"])
    body = []
    for i, (frozen, full) in enumerate(zip(chosen, rows), start=1):
        try:
            out = {k: full[k] for k in E32_PAIR_OUTCOME}
        except KeyError as exc:
            raise ClaimError(
                f"E32: the table of changed pairs lacks the column {exc} that Amendment 20, rule 1, prints"
            ) from None
        ya, yb = float(out["pir_per36_dest_a"]), float(out["pir_per36_dest_b"])
        more = (
            frozen["player_a"] if ya > yb else frozen["player_b"] if yb > ya else "tie"
        )
        for side, last in (("a", more), ("b", "")):
            body.append(
                [
                    str(i),
                    frozen[f"player_{side}"],
                    COMPETITIONS[frozen["league_dest"]],
                    LEAGUE_NAMES[frozen[f"league_src_{side}"]],
                    num(float(frozen[f"pir_per36_src_{side}"]), 1),
                    num(float(frozen[f"{E32_D}_{side}"]), 1),
                    num(float(frozen[f"{E32_O}_{side}"]), 1),
                    str(int(float(out[f"games_dest_{side}"]))),
                    num(float(out[f"pir_per36_dest_{side}"]), 1),
                    last,
                ]
            )
    shown = len(chosen)
    which = (
        f"The first {NUMBER_WORDS[shown]} of the {total} pairs"
        if total > shown
        else f"All {NUMBER_WORDS[shown]} pairs"
        if shown > 1
        else "The one pair"
    )
    cap = (
        f"Table 1. {which} {NAMED_TABLE_MARK} (E32): same competition, different source leagues, ordered by "
        "the gap in the league-aware forecast. The rows were fixed by frozen forecasts only and are printed "
        "whatever they show. Rates and forecasts are EFF/36."
    )
    table = md_table(
        [
            "Pair",
            "Newcomer",
            "Competition",
            "Source league",
            "Domestic rate, last season",
            "Forecast, destination only",
            "Forecast, league-aware",
            "Games so far",
            "Produced so far",
            "Produced more so far",
        ],
        body,
    )
    few = (
        f" Fewer than {NUMBER_WORDS[NAMED_PAIRS]} such pairs exist, so all are printed."
        if total < NAMED_PAIRS
        else ""
    )
    count = (
        f"The league numbers reverse the order of {total} such pair{'s' if total != 1 else ''}.{few} In {held} "
        f"of the {registered} registered pair{'s' if registered != 1 else ''} the league-aware order is the one "
        "that holds so far"
        + (f" ({tied} tied)" if tied else "")
        + f": described and not tested {cite}. No conclusion is drawn from these pairs or from that count."
    )
    return cap + "\n\n" + table + "\n\n" + count


def named_rows_in(text: str) -> list:
    """The newcomers named in the main-text table, in its order (gate G20a)."""
    lines = main_text(text).split("\n")
    start = next((i for i, ln in enumerate(lines) if NAMED_TABLE_MARK in ln), None)
    if start is None:
        return []
    names = []
    for ln in lines[start + 1 :]:
        if ln.startswith("|"):
            cells = [c.strip() for c in ln.strip("|").split("|")]
            if cells[0].isdigit():
                names.append(cells[1])
        elif names:
            break
    return names


def club_registered_reading(d) -> str:
    """Amendment 20, rule 2: the registered reading for a player who changes domestic league, with
    the lowest leave-one-league-out slope and its league in the same sentence."""
    e = d["e30"]
    code, low = e30_lowest(d)
    if not e["slope"] > 0:
        raise ClaimError(
            "the direction stated in the club section needs a positive slope"
        )
    share = (
        "about three quarters"
        if 0.70 <= e["slope"] < 0.80
        else f"about {num(e['slope'], 2)}"
    )
    return (
        f"When a player changed domestic league, his rate moved on average by {share} "
        f"{CLUB_READING_MARK} (slope {num(e['slope'], 2)}, interval {num(e['ci_low'], 2)} to "
        f"{num(e['ci_high'], 2)}; {num(low['estimate'], 2)} without {short_league(code)}, "
        f"{span(low['ci95'], 2)}): measured against the forecast for a player who stays in his league, it was higher "
        f"when he went to the league with the higher Equivalent and lower when he went the other way [@amend20]. This is an average over the {e['n_moves']:,} league changes of "
        "the test, not a statement about one pair of leagues or one player."
    )


def figure_1_notes(d):
    """Amendment 20, rule 4: the lowest leave-one-league-out slope, printed beside the group the
    panel marks, and the slope with the table refitted only on earlier arrivals. No other number."""
    if not amendment_20(d):
        return None
    s7 = e30_full(d)["S_e"]["7"]
    if S7_LABEL.search(s7["label"]) is None:
        raise ClaimError(
            "E30: sensitivity 7 is not the table refitted only on earlier arrivals"
        )
    return {
        "lowest": e30_lowest(d)[1]["estimate"],
        "refit": s7["estimate"],
        # Amendment 21, rule 2: printed as text, named as such, never drawn as a band
        "redrawn": list(e30_full(d)["S_d"]["ci95"]),
    }


def check_g20(text: str, d) -> None:
    """Gates G20a to G20c (Amendment 20), on the composed text.

    G20a: the main-text table holds the first five pairs of the committed E32 table, in its
    order, and names no newcomer anywhere else in the main text. G20b: no named table without a
    score record of the frozen test. G20c: the club section holds at most one of the two
    readings of the league-changes slope (the label of the other is checked by gate G19b)."""
    printed = named_pairs_printed(d)
    main = main_text(text)
    if NAMED_TABLE_MARK in text and not printed:
        if d.get("p1") is None or p1_check(d) == "pending":
            raise ClaimError(
                "G20b: a table of named newcomers is printed and the frozen test has no score record"
            )
        raise ClaimError(
            "G20a: a table of named newcomers is printed without the committed E32 table and Amendment 20"
        )
    if printed and d["e32_pairs"]:
        want = [
            name
            for r in named_pairs_selection(d["e32_pairs"])
            for name in (r["player_a"], r["player_b"])
        ]
        if named_rows_in(text) != want:
            raise ClaimError(
                "G20a: the named table of the main text does not hold the first five pairs of the committed "
                "E32 table, in its order"
            )
        outside = "\n".join(ln for ln in main.split("\n") if not ln.startswith("|"))
        named = sorted({n for n in want if n in outside})
        if named:
            raise ClaimError(
                f"G20a: a named newcomer appears in the main text outside the table: {named[:3]}"
            )
    if "\n## What a club can use\n" in main:
        club = section_of(text, "What a club can use")
        labelled = d.get("e30") is not None and any(m in club for m in reading_marks(d))
        registered = CLUB_READING_MARK in club
        if labelled and registered:
            raise ClaimError(
                "G20c: the club section holds both readings of the league-changes slope; it prints one"
            )
        if registered and not amendment_20(d):
            raise ClaimError(
                "G20c: the registered reading for a club is the wording of Amendment 20"
            )


def check_g19b(text: str, d) -> None:
    """Gate G19b (Amendment 19). For a Clear result whose interval lies below 1: the registered
    sentence of Amendment 14 appears exactly once in the paper, in Results, and the statement of
    rule 1 once in each of the abstract, the introduction and the conclusion. In every case: the
    label of rule 5 stands, in the same sentence or the next, with every printing of that reading,
    and the reading is printed only where rule 5 allows it."""
    case = e30_case(d)
    plain = case != E30_NOT_RUN and prints_first_page_words(d)
    if plain:
        registered = e30_sentence(d)
        if text.count(registered) != 1 or registered not in section_of(text, "Results"):
            raise ClaimError(
                "G19b: the registered sentence of Amendment 14 must appear exactly once, in Results"
            )
        statement = e30_statement(d)
        for name in ("Abstract", "Why the question matters", "Conclusion"):
            if section_of(text, name).count(statement) != 1:
                raise ClaimError(
                    f"G19b: the statement of Amendment 19, rule 1, must appear exactly once in '{name}'"
                )
    marks = reading_marks(d)
    sentences = sentences_of(text)
    for i, sentence in enumerate(sentences):
        if not any(mark in sentence for mark in marks):
            continue
        if not plain:
            raise ClaimError(
                "G19b: the reading of Amendment 19, rule 5, is printed for a case it is not written for"
            )
        nearby = sentence + " " + (sentences[i + 1] if i + 1 < len(sentences) else "")
        if READING_LABEL not in nearby:
            raise ClaimError(
                "G19b: the reading of Amendment 19, rule 5, is printed without its label "
                f"('{READING_LABEL}') in the same sentence or the next"
            )
    for name in ("Abstract",):
        if any(mark in section_of(text, name) for mark in marks):
            raise ClaimError(
                "G19b: the reading of rule 5 is not printed in the abstract"
            )
    if any(mark in text.splitlines()[1] for mark in marks):
        raise ClaimError("G19b: the reading of rule 5 is not printed in the title")


#: Gate G19c: registered wording that stays in the MAIN TEXT (Amendment 19, rule 11, "may not
#: move"), as (label, key of the composed block or fact). Each is checked sentence by sentence.
G19C_MAIN_BLOCKS = (
    ("the older-arrivals readings (Amendment 7)", "older_section"),
    ("the league numbers on the older arrivals (Amendment 10)", "e28_older_block"),
    ("where the forecast missed on the older arrivals (Amendment 11)", "e29_main"),
    (
        "what the league numbers are worth, against history (Amendment 9)",
        "e28_gh_sentence",
    ),
    (
        "what the league numbers are worth, once the destination is known (Amendment 9)",
        "e28_gd_sentence",
    ),
    (
        "what the league numbers are worth, weighted (Amendment 9)",
        "e28_weighted_sentence",
    ),
    ("the forecast level weighted by playing time (Amendment 12)", "lvl_w_sentence"),
    (
        "the margin against what the source league adds (Amendment 13, rule 3)",
        "e28c_sentence",
    ),
)
#: ... and fixed sentences of the template, as (label, text with facts to fill).
G19C_MAIN_TEXTS = (
    (
        "the forecast level (Amendment 3)",
        "On average the league-aware forecast is {lvl_off_abs} EFF/36 below what arrivals delivered",
    ),
    (
        "the registered equivalence statement with its margin (Amendment 13, rule 3)",
        "Both the head-to-head interval and translation's incremental interval lie inside ±{margin_eff} EFF/36",
    ),
    (
        "the margin was set after the interval was seen (Amendment 13, rule 3)",
        "That margin was registered for translation's increment, after the submitted recipe's interval had been seen",
    ),
    (
        "the limits beside the equation (Amendment 12)",
        "the limits stated above apply to it: the forecasts fall below the outcomes on average, the league numbers did not carry back to the "
        "older arrivals of two leagues, and they describe the players clubs sign from a league, not league strength",
    ),
)
#: ... and registered wording that stays in the PAPER (main text or appendix).
G19C_PAPER_TEXTS = (
    (
        "the playing-time reading of translation's gain (Amendment 13, rule 4)",
        "Weighted by playing time, translation's gain over history is not clearly above zero",
    ),
)
#: Amendment 21, rule 1: the conclusion states translation's increment as the first page does.
#: The sentence it replaces (Amendment 13, rule 3) may not come back (gate G21a).
CONCLUSION_INCREMENT = (
    "On top of the league numbers a translation factor adds nothing detectable"
)
OLD_CONCLUSION_CLAIM = "matches the measured benefit of translation factors"
EQUIVALENCE_STATEMENT = (
    "Both the head-to-head interval and translation's incremental interval lie inside ±"
)
EQUIVALENCE_DISCLOSURE = "That margin was registered for translation's increment, after the submitted recipe's interval had been seen"


def check_g21(text: str, d) -> None:
    """Gates G21a and G21b (Amendment 21), on the composed text.

    G21a: the word "matches" does not occur in the abstract, the introduction or the conclusion,
    and the registered equivalence statement with its margin, and the fact that the margin was
    set after the interval was seen, stand in Results. G21b: wherever the interval of the slope
    with the table values redrawn is printed in the introduction or with Figure 1, the same
    sentence names it as such; it is never called the 95% interval of the slope and it does not
    enter the abstract."""
    for name in ("Abstract", "Why the question matters", "Conclusion"):
        if re.search(r"\bmatches\b", section_of(text, name)):
            raise ClaimError(
                f"G21a: the word 'matches' stands in '{name}' (Amendment 21, rule 1)"
            )
    if OLD_CONCLUSION_CLAIM in text:
        raise ClaimError(
            "G21a: the conclusion's sentence that Amendment 21 replaced is in the paper"
        )
    results = section_of(text, "Results")
    statement = re.search(
        re.escape(EQUIVALENCE_STATEMENT) + r"\d+\.\d+ EFF/36, 2% of forecast error",
        results,
    )
    if statement is None or EQUIVALENCE_DISCLOSURE not in results:
        raise ClaimError(
            "G21a: the registered equivalence statement with its margin is missing from Results"
        )
    if "margin" in section_of(text, "Conclusion"):
        raise ClaimError("G21a: the conclusion carries the margin")
    if e30_case(d) == E30_NOT_RUN:
        return
    mark = e30_redrawn_mark(d)
    if mark in section_of(text, "Abstract"):
        raise ClaimError(
            "G21b: the interval with the table values redrawn is in the abstract"
        )
    if f"95% interval {mark}" in text or f"95% interval of {mark}" in text:
        raise ClaimError(
            "G21b: the interval with the table values redrawn is printed as the 95% interval of the slope"
        )
    first_page = section_of(text, "Why the question matters")
    for sentence in sentences_of(first_page):
        if mark in sentence and "redrawn" not in sentence:
            raise ClaimError(
                "G21b: the interval with the table values redrawn is printed on the first page without its name"
            )


# ---------------------------------------------------------------- Amendment 23: rules 1 to 4 and gates G23a to G23d
# ---------------------------------------------------------------- Amendment 29, rule 1: the first page
#: What the first page says after a blind comparison of two first pages (26 November 2026).
FIRST_PAGE_TESTS = (
    "This paper sets the established adjustment, a translation factor, against a plainer benchmark that "
    "needs only past arrivals: one number per source league."
)
FIRST_PAGE_UNIT = "These are the European League Equivalents, in box-score efficiency per 36 minutes (EFF/36):"
FIRST_PAGE_ADDS = (
    "this paper adds that registered test and an interval for each league number"
)
FIRST_PAGE_COMPARISON = (
    "This paper makes that comparison, scoring each pair of forecasts on the same players, and sets the "
    "translation factor against a plainer benchmark: one number per source league."
)
FIRST_PAGE_COMPARISON_ALONE = (
    "This paper compares forecasts with and without a league adjustment, scoring each pair on the same players, "
    "and sets the translation factor against a plainer benchmark: one number per source league."
)
FIRST_PAGE_SLOPE = (
    "The slope is the average change in a mover's rate, beyond the forecast for a player who stays in his league, "
    "per unit of change that the EuroCup Equivalents predict; a slope of 1 would mean the table's size is exactly right."
)
FIRST_PAGE_HEADS = (
    "**The benchmark and its test.**",
    "**What a translation factor adds.**",
)
FIRST_PAGE_CLUB_HEAD = "**What a club can do with the table.**"


def first_page_new(d) -> str:
    """What is new, in the introduction: the registered statement of what the search did not find
    (Amendment 23, rule 4), printed a second time with a pointer, and what this paper does."""
    if prior_work_state(d) != PRIOR_WORK_NARROWED:
        return FIRST_PAGE_COMPARISON_ALONE
    return f"{PRIOR_WORK_NOT_FOUND[:-1]} (Related work). {FIRST_PAGE_COMPARISON}"


#: Rule 1: the one sentence the abstract may carry on the unit, between the sentence on the
#: problem and the Equivalents line. The words "per 36 minutes" stand nowhere else in the abstract.
ABSTRACT_UNIT_SENTENCE = (
    "Production is measured by box-score efficiency per 36 minutes (EFF/36)."
)
#: Rule 3: the competitions of the committed table of signed errors, in the order they are printed.
LEVEL_COMPETITIONS = (("eurocup", "EuroCup"), ("euroleague", "EuroLeague"))
LEVEL_NOT_TESTED = "The difference between the two was not tested."
LEVEL_OVERLAP_NOT_TESTED = (
    "The two intervals overlap, and the difference between them was not tested."
)
#: A clause of rule 3, in either of its two wordings (gate G23c).
LEVEL_CLAUSE = re.compile(
    r"\b[Ff]or (EuroCup|EuroLeague) arrivals (?:the league-aware forecast is|the interval includes zero)"
)
LEVEL_PARAGRAPH = "**The forecasts fall below the outcomes.**"
LEVEL_NO_CAUSE = "We claim no cause."
MONTH_NAMES = (
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
)
CITATION_KEY = re.compile(r"[a-z0-9]+")


#: The one form of a day in the record of rule 4 and in the score record of the frozen test.
ISO_DAY = re.compile(r"\d{4}-\d{2}-\d{2}")


def iso_day(value) -> datetime.date:
    """The day written as YYYY-MM-DD. Any other form raises ValueError, also one that the
    standard library reads (20261122): the order of reading (rule 4) compares days, and two
    forms of one day do not compare."""
    if not isinstance(value, str) or ISO_DAY.fullmatch(value) is None:
        raise ValueError(f"not a day in the form YYYY-MM-DD: {value!r}")
    return datetime.date.fromisoformat(value)


def long_date(iso: str) -> str:
    """'22 November 2026' from '2026-11-22'."""
    day = iso_day(iso)
    return f"{day.day} {MONTH_NAMES[day.month - 1]} {day.year}"


def level_by_competition(d) -> dict:
    """Rule 3: the committed rows of signed errors of the league-aware forecast by competition
    (E18a, Amendment 3; the rows of Table A10)."""
    rows = {(r["arm"], r["scope"]): r for r in get(d["amend3"], "e18")["level"]}
    return {code: rows[(A3_O, f"destination:{code}")] for code, _ in LEVEL_COMPETITIONS}


def level_clause(name: str, row: dict) -> str:
    """Rule 3: one competition in the words registered for the case of its interval."""
    low, high = row["ci95_low"], row["ci95_high"]
    tail = f"interval {num(low, 2)} to {num(high, 2)}; {row['n']} arrivals"
    if high < 0:
        return (
            f"for {name} arrivals the league-aware forecast is {num(abs(row['mean_signed_error']), 2)} EFF/36 "
            f"below what they delivered ({tail})"
        )
    if low <= 0:
        return f"for {name} arrivals the interval includes zero ({num(row['mean_signed_error'], 2)}, {tail})"
    raise ClaimError(
        f"Amendment 23, rule 3: no wording is registered for a forecast level whose interval lies above zero "
        f"({name} arrivals); this goes to Amir first"
    )


def level_not_tested(d) -> str:
    """Rule 3: the sentence on the difference, by whether the two intervals overlap."""
    first, second = level_by_competition(d).values()
    overlap = max(first["ci95_low"], second["ci95_low"]) <= min(
        first["ci95_high"], second["ci95_high"]
    )
    return LEVEL_OVERLAP_NOT_TESTED if overlap else LEVEL_NOT_TESTED


def level_sentences(d) -> str:
    """Rule 3: where the forecasts run low, printed before "We claim no cause". The values are
    descriptive (Amendment 3); the paper calls neither a test and gives no cause."""
    rows = level_by_competition(d)
    clauses = "; ".join(
        level_clause(name, rows[code]) for code, name in LEVEL_COMPETITIONS
    )
    return f"{clauses[0].upper() + clauses[1:]}. {level_not_tested(d)}"


def prior_work_pages(d) -> list:
    """The pages of the record of rule 4, after refusing a record no sentence may be written from."""
    pages = d["prior_work"].get("pages")
    if not isinstance(pages, list) or not pages:
        raise ClaimError("G23d: the record of rule 4 names no page")
    keys = []
    for page in pages:
        missing = [
            k
            for k in (
                "citation",
                "analyst",
                "urls",
                "read_in_full",
                "read_in_full_only_after_scoring",
            )
            if k not in page
        ]
        if missing:
            raise ClaimError(f"G23d: a page of the record of rule 4 lacks {missing}")
        key = page["citation"]
        if (
            not isinstance(key, str)
            or CITATION_KEY.fullmatch(key) is None
            or key in keys
            or key in REFERENCES
            or key in OPTIONAL_REFERENCES
        ):
            raise ClaimError(
                f"G23d: '{key}' is not a citation key of its own in the record of rule 4"
            )
        keys.append(key)
        if not isinstance(page["read_in_full_only_after_scoring"], bool):
            raise ClaimError(
                f"G23d: the record of rule 4 does not say when the {page['analyst']} pages may be read in full"
            )
        if page["read_in_full"] is not None:
            try:
                long_date(page["read_in_full"])
            except ValueError as error:
                raise ClaimError(
                    f"G23d: the date of the full read of the {page['analyst']} pages is not a date "
                    "in the form YYYY-MM-DD"
                ) from error
        reports = page.get("reports")
        texts = [page.get("short")]
        if isinstance(reports, dict):
            texts += [reports.get(k) for k in PRIOR_WORK_REPORTS]
        for text in texts:
            if not isinstance(text, str):
                continue
            if hit := LEAGUE_CHANGE_WORDS.search(text):
                raise ClaimError(
                    f"Amendment 23, rule 4: the record's text on the {page['analyst']} pages uses "
                    f"'{hit.group(0)}', words the paper keeps for its own test on league changes "
                    "(Amendment 16, rule 3); the page is described in other words"
                )
            bare = PRIOR_WORK_LABEL.sub(" ", PRIOR_WORK_NAMED.sub(" ", text))
            if typed := re.search(r"\d[\d.,]*%?", bare):
                raise ClaimError(
                    f"Amendment 23, rule 4: the record's text on the {page['analyst']} pages types the "
                    f"number '{typed.group(0)}'; a number that is not a date, a year or a season label is "
                    "named under 'numbers', so that the number manifest traces it to the record"
                )
    return pages


def prior_work_order_check(d) -> None:
    """Gate G24a: Amendment 23, rule 4, "Order of reading", as Amendment 24 makes it explicit.

    A page that shows statistics of the 2026-27 season, or leads to one, is read in full only
    after the frozen 2026-27 test has been scored, and that test has been scored once the
    registered scoring run of November 2026 has written its score record and the record is
    committed, whatever status it carries: scored, not adjudicable or inconclusive (Amendment 24,
    rule 1). So the record of rule 4 may date the full read of such a page only beside a score
    record of that test and not before the day of scoring. Both days are written as YYYY-MM-DD
    and compared as days, and a score record that gives no day of scoring is refused beside a
    dated read (Amendment 24, rule 3). A scoring attempt that stopped at a gate wrote no score
    record: the read waits for the record.

    The renderer reads the files of the tree it runs in. A retained run is made from committed
    files only, so the score record it finds there is a committed one.

    Checked when the committed files are loaded, like the other checks that compare one
    committed file with another: a text composed from changed inputs (a test of another state,
    the number manifest) is not what the rule is about.
    """
    record = d["p1"]
    status = None if record is None else record.get("status")
    for page in prior_work_pages(d):
        read = page["read_in_full"]
        if not page["read_in_full_only_after_scoring"] or read is None:
            continue
        if status not in PRIOR_WORK_READ_STATES:
            state = (
                "has no score record"
                if record is None
                else f"has a record whose status ({status!r}) is not one a score record carries"
            )
            raise ClaimError(
                f"G24a, the order of reading (Amendment 23, rule 4; Amendment 24): the record dates a full read "
                f"of the {page['analyst']} pages, which are read in full only once the score record of the frozen "
                f"2026-27 test is committed; that test {state}"
            )
        try:
            scored_on = iso_day(record.get("scored_on"))
        except ValueError as error:
            raise ClaimError(
                f"G24a, the order of reading (Amendment 23, rule 4; Amendment 24): the record dates a full read "
                f"of the {page['analyst']} pages, and the score record of the frozen 2026-27 test gives no day of "
                "scoring to set it against"
            ) from error
        if iso_day(read) < scored_on:
            raise ClaimError(
                f"G24a, the order of reading (Amendment 23, rule 4; Amendment 24): the record dates the full read "
                f"of the {page['analyst']} pages on {read}, before the day of the score record of the frozen "
                f"2026-27 test ({scored_on.isoformat()})"
            )


def prior_work_page_ready(page) -> bool:
    """Gate G23d: the record gives the date of the page's full read and what the page reports."""
    reports = page.get("reports")
    return (
        page["read_in_full"] is not None
        and isinstance(reports, dict)
        and all(
            isinstance(reports.get(k), str) and reports[k].strip()
            for k in PRIOR_WORK_REPORTS
        )
        and isinstance(reports.get(PRIOR_WORK_COMPARES), bool)
        and isinstance(reports.get(PRIOR_WORK_WITHOUT), bool)
        and all(
            isinstance(page.get(k), str) and page[k].strip()
            for k in ("short", "reference", "ledger_heading")
        )
    )


def prior_work_state(d) -> str:
    """Which statement on prior work the paper prints (Amendment 23, rule 4; gate G23d).

    "kept": the sentence the paper has, while the record lacks the date of a full read or what a
    page reports. "narrowed": the two statements of rule 4, once every named page has both. A
    record that holds a comparison with and without a league level is refused in either state:
    the sentence under "What was not found" is then not printed and Amir is told before any
    writing. The order of reading that rule 4 sets is checked on the committed files when they
    are loaded (``prior_work_order_check``, gate G24a). The state does not depend on the status
    of the frozen test: the condition of rule 4 applies in every status (Amendment 24, rule 2).
    """
    pages = prior_work_pages(d)
    for page in pages:
        reports = page.get("reports")
        if isinstance(reports, dict) and reports.get(PRIOR_WORK_COMPARES) is True:
            raise ClaimError(
                f"G23d: the record of rule 4 holds a comparison with and without a league level "
                f'({page["analyst"]}); the sentence under "What was not found" is not printed, the page is '
                "described as what it is, and Amir is told before any writing"
            )
    if all(prior_work_page_ready(page) for page in pages):
        return PRIOR_WORK_NARROWED
    return PRIOR_WORK_KEPT


def prior_work_fill(page, text: str) -> str:
    """A text of the record with its numbers, each read as a leaf of its own so that the number
    manifest can trace it."""
    numbers = page.get("numbers") or {}
    try:
        return text.format(**{name: numbers[name] for name in numbers})
    except (KeyError, IndexError, ValueError) as error:
        raise ClaimError(
            f"G23d: a text of the record of rule 4 ({page['analyst']}) names a number the record does not hold"
        ) from error


def prior_work_page_text(page) -> str:
    """Appendix O, "What was found" in full: what the page forecasts, with its source; on which
    players and seasons the forecast was scored; whether those players are arrivals; and whether
    the page reports the forecast's accuracy with and without the league level."""
    reports = page["reports"]
    parts = [
        f"{page['analyst']} {reports['forecasts'].rstrip('.')} [@{page['citation']}]",
        *(reports[k] for k in PRIOR_WORK_REPORTS[1:]),
    ]
    return " ".join(prior_work_fill(page, part).rstrip(".") + "." for part in parts)


def replace_once(text: str, old: str, new: str) -> str:
    if text.count(old) != 1:
        raise ClaimError(
            f"Amendment 23, rule 4: '{old[:60]}' must stand exactly once in the text it is replaced in"
        )
    return text.replace(old, new)


def prior_work_blocks(d) -> dict:
    """Related work, Appendix O and the note on the search, in the state the record of rule 4 gives."""
    blocks = {
        "section:related": RELATED,
        "related_full": RELATED_FULL,
        "related_search": RELATED_SEARCH,
    }
    if prior_work_state(d) == PRIOR_WORK_KEPT:
        return blocks
    pages = prior_work_pages(d)
    if len(pages) != 2:
        raise ClaimError(
            "Amendment 23, rule 4: the short form is worded for two analysts' pages; with another number "
            "the wording goes to Amir first"
        )
    without = [page["analyst"] for page in pages if page["reports"][PRIOR_WORK_WITHOUT]]
    if without:
        raise ClaimError(
            "Amendment 23, rule 4: the short form says that neither analyst reports its forecast without the "
            f"league level, and the record says that {' and '.join(without)} does; the wording goes to "
            "Amir first"
        )

    def cited(page, value: str) -> str:
        return f"{value} [@{page['citation']}]"

    found = PRIOR_WORK_FOUND_SHORT.format(
        first=cited(pages[0], prior_work_fill(pages[0], pages[0]["short"])),
        second=cited(pages[1], prior_work_fill(pages[1], pages[1]["short"])),
    )
    if "read_further" in pages[1]:
        read = PRIOR_WORK_READ_FURTHER.format(
            first=cited(pages[0], long_date(pages[0]["read_in_full"])),
            second=cited(pages[1], prior_work_further(pages[1])["statement"]),
        )
    else:
        read = PRIOR_WORK_READ.format(
            first=cited(pages[0], long_date(pages[0]["read_in_full"])),
            second=cited(pages[1], long_date(pages[1]["read_in_full"])),
        )
    full = " ".join(prior_work_page_text(page) for page in pages)
    search = replace_once(RELATED_SEARCH, PRIOR_WORK_OLD_QUOTE, PRIOR_WORK_NEW_QUOTE)
    search = replace_once(search, PRIOR_WORK_CHECK_OLD, PRIOR_WORK_CHECK_NEW)
    return {
        "section:related": replace_once(
            RELATED, PRIOR_WORK_OLD_SHORT, f"{found} {PRIOR_WORK_NOT_FOUND}"
        ),
        "related_full": replace_once(
            RELATED_FULL, PRIOR_WORK_OLD_FULL, f"{full} {PRIOR_WORK_NOT_FOUND}"
        ),
        "related_search": replace_once(
            search, PRIOR_WORK_SEARCH_LAST, f"{read} {PRIOR_WORK_SEARCH_LAST}"
        ),
    }


def prior_work_further(page) -> dict:
    """Amendment 29, rule 4: the later reading that completes a full read. Its statement names both
    days (``{first}`` and ``{later}``) and types no number; that the later day lies after the
    first is checked on the committed record (the test of Amendment 29)."""
    further = page["read_further"]
    try:
        first, later = long_date(page["read_in_full"]), long_date(further["date"])
    except (KeyError, TypeError, ValueError) as error:
        raise ClaimError(
            f"G23d: the later reading of the {page['analyst']} pages has no date in the form YYYY-MM-DD"
        ) from error
    statement = further.get("statement")
    if (
        not isinstance(statement, str)
        or statement.count("{first}") != 1
        or statement.count("{later}") != 1
        or re.search(r"\d", statement)
    ):
        raise ClaimError(
            f"G23d: the later reading of the {page['analyst']} pages does not state both days of reading, "
            "or types a number"
        )
    return {**further, "statement": statement.format(first=first, later=later)}


def prior_work_references(d) -> dict:
    """The references of the pages of rule 4, cited only once their sentences are printed. The
    date of access is the date of the full read."""
    if prior_work_state(d) != PRIOR_WORK_NARROWED:
        return {}
    references = {}
    for page in prior_work_pages(d):
        read = long_date(page["read_in_full"])
        if "read_further" in page:
            read += f" and {long_date(prior_work_further(page)['date'])}"
        references[page["citation"]] = f"{page['reference'].rstrip()} (accessed {read})"
    return references


# ---------------------------------------------------------------- Amendment 23, rule 5: E34
#: The amendment that registers E34, by its sha256 (the generator records the one it read).
E34_AMENDMENT_SHA256 = (
    "8a440ef497d44aeb094f5c439f104ff753084a47576b1428bc881960bd4c1ad7"
)
E34_GATES = ("G34a", "G34b", "G34c", "G34e", "G34f")
#: [S] of rule 5, each with its reference; the last entry is the name in the appendix table.
E34_SCALES = (
    ("table_2015", "a league table printed in 2015", "vashro2015", "2015 table"),
    (
        "scale_2026",
        "a league scale published in 2026",
        "gaussianhoops2026",
        "2026 scale",
    ),
)
E34_WEIGHTS = (
    ("unweighted", "Unweighted"),
    ("minutes_weighted", "Weighted by playing time"),
)
E34_SAMPLES = (("aba", "Adriatic league"), ("israel", "Israel"))
#: Rule 5, word for word: the label that stands wherever E34 is printed.
E34_LABEL = (
    "These readings were first made outside the registration, in a review of the paper, and the rules for "
    "printing them were written after their values had been seen; they are exploratory [@amend23]."
)
E34_LABEL_MARK = "These readings were first made outside the registration"
#: The first sentence of the passage in Results (rule 5, "Every number is printed whatever it shows").
E34_INTRO = (
    "Two published league scales were also scored on these arrivals; for each, the comparison with the "
    "paper's league numbers is shown in the weighting less favourable to the paper, and Appendix I gives both"
)
E34_MARK = "Two published league scales were also scored on these arrivals"
#: Rule 5, word for word: the sentence of Appendix N.
E34_NOTE = (
    "E34 is the only study this paper reports from the further studies that a review of the paper ran, "
    "outside the registration, on seasons already examined; the others are not used."
)
#: Rule 5, "Four facts printed beside the table". The ranks are checked against the record.
E34_FACTS = (
    "The 2015 table was printed in November 2015, during the last of these seasons, and may have been built on "
    "them; the paper cannot tell how far. The 2026 scale is built on moves of 2021–22 to 2025–26, as the paper's "
    "league numbers are fitted on arrivals of 2017 to 2025. The intervals treat the fitted forecasts as fixed and "
    "describe arrivals from these two leagues; each league term is one constant per league, so they say nothing "
    "about other leagues. Both published scales place the Adriatic league fourth of the ten source leagues, and "
    "the paper's league numbers place it seventh; the paper reads neither as league strength."
)
E34_RANKS = {"table_2015": 4, "scale_2026": 4, "paper_league_numbers": [7], "of": 10}
#: Rule 5: the sentence that the 2026 scale "is not scored here", and what replaces it.
E34_RELATED_OLD = "it is not scored here, because it is built on seasons the paper scores and is not a registered arm [@amend15]."
E34_RELATED_NEW = (
    "it is not scored on the arrivals of 2020–2025 or on the league changes, because it is built on those "
    "seasons; it is not a registered arm and is not read out on the frozen test [@amend15]; one exploratory "
    "reading on the older arrivals is in Results and Appendix I [@amend23]."
)
E34_RELATED_FULL_OLD = (
    "That scale is not scored here: it is built on seasons the paper scores, so it could only be scored on "
    "the frozen 2026–27 test, and it is not a registered arm [@amend15]."
)
E34_RELATED_FULL_NEW = (
    "That scale is not scored on the arrivals of 2020–2025 or on the league changes, because it is built on "
    "those seasons; it is not a registered arm and is not read out on the frozen test [@amend15]. One "
    "exploratory reading on the older arrivals is in Results and Appendix I [@amend23]."
)
E34_NOT_SCORED_MARK = "not scored here"
#: Rule 5: words the paper does not use for E34.
E34_BANNED = ("confirms", "validates", "robust", "equivalent")
E34_STRENGTH_ALLOWED = "the paper reads neither as league strength"


def e34_refuse(why: str):
    raise ClaimError(
        f"E34 (Amendment 23, rule 5): {why}; nothing of E34 is printed and Amir is told"
    )


def e34_case(ci) -> str:
    return "above_zero" if ci[0] > 0 else "below_zero" if ci[1] < 0 else "includes_zero"


def e34_check(d, root: Path | None = None) -> None:
    """The record of E34 is one this paper may print: every gate of the run passed with its
    control, the rows and the E28b contrast are the committed ones (G_S + T_S equals the committed
    E28b contrast, gate G34e), and every reading is the case of its interval. With ``root``: the
    record was computed from the committed E28 summary and the committed record of the 2026 scale."""
    s = d.get("e34")
    if s is None:
        return
    try:
        if (
            s["analysis"] != "E34"
            or s["exploratory"] is not True
            or s["reads_2026_27_statistics"] is not False
        ):
            e34_refuse("the summary is not the exploratory record of E34")
        if s["amendment"]["sha256"] != E34_AMENDMENT_SHA256:
            e34_refuse("the summary was not computed under Amendment 23 as pushed")
        for name in E34_GATES:
            gate = s["gates"].get(name, {})
            if (
                gate.get("status") != "passed"
                or gate.get("negative_control") != "rejected as required"
            ):
                e34_refuse(f"gate {name} is not recorded as passed with its control")
        e28b = d["amend9"]["e28b"]
        if s["n"] != e28b["n"] or s["n"] != older(d)["n"]:
            e34_refuse("the summary is not on the older arrivals the paper prints")
        blocks = [("all", s["n"], s["contrasts"])] + [
            (code, s["by_league_n"][code], s["by_league"][code])
            for code, _ in E34_SAMPLES
        ]
        if sum(n for _, n, _ in blocks[1:]) != s["n"] or set(s["by_league"]) != {
            code for code, _ in E34_SAMPLES
        }:
            e34_refuse("the split by source league does not add up to the arrivals")
        for sample, n, block in blocks:
            for scale, *_ in E34_SCALES:
                for w, _ in E34_WEIGHTS:
                    for contrast in ("G", "T"):
                        r = block[scale][contrast][w]
                        if (
                            r["n"] != n
                            or r["reading"] != e34_case(r["ci95"])
                            or not r["ci95"][0] <= r["difference"] <= r["ci95"][1]
                            or not r["detectable_80"] > 0
                        ):
                            e34_refuse(
                                f"a reading of the summary does not hold together ({sample}, {scale}, "
                                f"{contrast}, {w})"
                            )
        for scale, *_ in E34_SCALES:
            for w, _ in E34_WEIGHTS:
                c = s["contrasts"][scale]
                gap = abs(
                    c["G"][w]["difference"]
                    + c["T"][w]["difference"]
                    - e28b["contrasts"]["G_D"][w]["difference"]
                )
                if not gap <= 1e-9:
                    e34_refuse(
                        f"G_S + T_S is not the committed E28b contrast ({scale}, {w}; gate G34e)"
                    )
        if s["ranks"]["adriatic"] != E34_RANKS:
            e34_refuse(
                "the ranks of the Adriatic league are not the ones rule 5 states (fourth, fourth, seventh)"
            )
        if root is not None:
            for name, path in (
                ("amend9", SOURCES["amend9"]),
                ("scale_2026", E34_SCALE_RECORD),
            ):
                if s["inputs"][name]["sha256"] != sha(root / path):
                    e34_refuse(
                        f"the summary was not computed from the committed file '{name}'"
                    )
    except (KeyError, TypeError) as error:
        e34_refuse(f"the summary lacks what the paper reads ({error!r})")


def e34_reversed(r: dict) -> str:
    """The interval of a difference printed as its size ("the interval is reversed with it")."""
    return f"interval {num(-r['ci95'][1])} to {num(-r['ci95'][0])}"


def e34_t_clause(r: dict, subject: str) -> str:
    """T_S, the published-scale forecast against the destination-only forecast (rule 5's words)."""
    if r["reading"] == "above_zero":
        return f"{subject} improved the destination-only forecast by {num(r['difference'])} EFF/36 ({e28_span(r)})"
    if r["reading"] == "includes_zero":
        return (
            f"{subject} added nothing detectable to the destination-only forecast "
            f"({num(r['difference'], sign=True)}, {e28_span(r)}; a gain of {num(r['detectable_80'])} would have "
            "been detected with 80% power)"
        )
    return (
        f"with {subject} the forecast was less accurate than with the destination alone by "
        f"{num(-r['difference'])} EFF/36 ({e34_reversed(r)})"
    )


def e34_g_clause(r: dict, name: str) -> str:
    """G_S, the league-aware forecast against the published-scale forecast (rule 5's words)."""
    if r["reading"] == "above_zero":
        return (
            f"the paper's league numbers were more accurate than {name} by {num(r['difference'])} EFF/36 "
            f"({e28_span(r)})"
        )
    if r["reading"] == "includes_zero":
        return (
            f"the paper's league numbers and {name} are not distinguishable ({num(r['difference'], sign=True)}, "
            f"{e28_span(r)}; a difference of {num(r['detectable_80'])} would have been detected with 80% power)"
        )
    return (
        f"it was more accurate than the paper's league numbers by {num(-r['difference'])} EFF/36 "
        f"({e34_reversed(r)})"
    )


def e34_less_favourable(c: dict) -> str:
    """The weighting whose estimate of G_S is the less favourable to the paper's league numbers
    (below zero, the published scale was the more accurate)."""
    return min((w for w, _ in E34_WEIGHTS), key=lambda w: c["G"][w]["difference"])


def e34_printed_readings(s: dict) -> list:
    """What the passage in Results prints: (scale, contrast, weighting, clause), in order."""
    out = []
    for scale, name, key, _ in E34_SCALES:
        c = s["contrasts"][scale]
        out.append(
            (
                scale,
                "T",
                "unweighted",
                e34_t_clause(c["T"]["unweighted"], f"{name} [@{key}]"),
            )
        )
        if c["T"]["minutes_weighted"]["reading"] != c["T"]["unweighted"]["reading"]:
            out.append(
                (
                    scale,
                    "T",
                    "minutes_weighted",
                    e34_t_clause(c["T"]["minutes_weighted"], "it"),
                )
            )
        w = e34_less_favourable(c)
        out.append((scale, "G", w, e34_g_clause(c["G"][w], name)))
    return out


def e34_weighting_words(weighting: str, clause: str, first: bool) -> str:
    """Each clause names its weighting."""
    if weighting == "unweighted":
        return ("Unweighted, " if first else "unweighted, ") + clause
    if clause.startswith("it was more accurate"):
        return "weighted by playing time " + clause  # as in rule 5's example
    return "weighted by playing time, " + clause


def e34_table_number(blocks: dict) -> int:
    """The table of E34 takes the next free number, so no existing table is renumbered."""
    used = [
        int(n) for text in blocks.values() for n in re.findall(r"Table A(\d+)\. ", text)
    ]
    return max(used + [E32_FIRST_TABLE - 1]) + 1


def e34_main(s: dict, k: int) -> str:
    """The passage in Results, after the paragraph on the league numbers (rule 5)."""
    sentences = []
    for scale, *_ in E34_SCALES:
        parts = [
            e34_weighting_words(w, clause, first=i == 0)
            for i, (_, _, w, clause) in enumerate(
                r for r in e34_printed_readings(s) if r[0] == scale
            )
        ]
        # Amendment 29, rule 2: three readings of one scale are three sentences (the registered
        # clauses keep their words; only the joins change)
        if len(parts) > 2:
            sentences.append(" ".join(p[0].upper() + p[1:] + "." for p in parts))
        else:
            sentences.append("; ".join(parts) + ".")
    return " ".join([f"{E34_INTRO} (Table A{k}).", *sentences, E34_LABEL])


def table_e34(s: dict, k: int) -> str:
    """Appendix I: every reading of E34, the error of each forecast and the split by source league."""
    rows = []
    samples = [(f"All {s['n']}", s["contrasts"], True)] + [
        (f"{label} ({s['by_league_n'][code]})", s["by_league"][code], False)
        for code, label in E34_SAMPLES
    ]
    for sample, block, tested in samples:
        for scale, _, _, short in E34_SCALES:
            for contrast, against in (
                ("G", "league numbers (G)"),
                ("T", "destination only (T)"),
            ):
                for w, label in E34_WEIGHTS:
                    r = block[scale][contrast][w]
                    own, other = (
                        (r["mae_left"], r["mae_right"])
                        if contrast == "G"
                        else (r["mae_right"], r["mae_left"])
                    )
                    rows.append(
                        [
                            sample,
                            short,
                            against,
                            label,
                            num(own),
                            num(other),
                            num(r["difference"], sign=True),
                            interval(r["ci95"]),
                            num(r["detectable_80"]) if tested else "—",
                        ]
                    )
    caption = (
        f"Table A{k}. Two published league scales in the place of the paper's league numbers on the older "
        "arrivals (E34, exploratory). Each scale enters the destination-only forecast as one coefficient times "
        "its value for the source league. For the 2015 table [@vashro2015] the forecast's coefficients are those "
        "frozen for the 2026–27 test; for the 2026 scale [@gaussianhoops2026] they are fitted on the paper's "
        "training arrivals through 2025. Errors and differences are mean absolute errors in EFF/36. *G*: the "
        "error with the published scale "
        "minus the error of the league-aware forecast; below zero, the published scale was the more accurate. "
        "*T*: the error of the destination-only forecast minus the error with the published scale; below zero, "
        "the destination-only forecast was the more accurate. The column *Difference* holds G or T, as the row says. "
        "95% intervals clustered by player and destination "
        "club-season. *Detectable*: the smallest difference this sample could detect with 80% power. The split by "
        f"source league is described and not tested. {E34_LABEL}"
    )
    return (
        caption
        + "\n\n"
        + md_table(
            [
                "Arrivals",
                "Published scale",
                "Compared with",
                "Weighting",
                "MAE, published scale",
                "MAE, compared forecast",
                "Difference",
                "95% interval",
                "Detectable",
            ],
            rows,
        )
        + "\n\n"
        + E34_FACTS
    )


# ---------------------------------------------------------------- Amendment 27
#: Amendment 27 (25 November 2026, after E34 was run): one sentence in the paragraph "A published
#: league table on the same players" that points to the exploratory reading on the older arrivals.
#: It registers nothing in advance.
#: The file as it stands (with the Specification block appended in a second commit, 60b03c561).
AMENDMENT_27_SHA256 = "57162dff30fbb46be1a5722783f060c3138b6f351d0e1f74ca96c2557bf2660d"
#: The file as first pushed alone (commit 38574fb8d): everything above "## Specification".
AMENDMENT_27_FIRST_SHA256 = (
    "38b09ec34a6f6748c42475e09f086f617a84def85d64f15749c0249ed177a688"
)
#: Rule 1: the sentence follows this one, which stays word for word.
E31_NEITHER = (
    "On neither sample can the two be told apart, which is not the same as equal."
)
E34_POINTER = (
    "A third comparison, on the {n} older arrivals, is exploratory; there the 2015 table was the more "
    "accurate when weighted by playing time (see the arrivals of 2008–2015)."
)
E34_POINTER_MARK = "A third comparison, on the"
#: Rule 2: Appendix N, after its sentence on E34.
AMEND27_NOTE = (
    "One sentence in the main text that points from the comparison with the 2015 table to this reading was "
    "added on 25 November 2026, after the reading had been made [@amend27]."
)
AMEND27_NOTE_MARK = (
    "One sentence in the main text that points from the comparison with the 2015 table"
)


def e34_pointer(d) -> str:
    """Rule 1 of Amendment 27: printed only with E34, and only in the case that occurred (the
    interval of G_S for the 2015 table lies below zero when weighted by playing time, and does
    not lie above zero unweighted). In any other case the wording goes to Amir."""
    s = d.get("e34")
    if s is None:
        return ""
    g = s["contrasts"]["table_2015"]["G"]
    weighted, plain = g["minutes_weighted"]["ci95"], g["unweighted"]["ci95"]
    if not (weighted[1] < 0 and not plain[0] > 0):
        raise ClaimError(
            "G27b: the sentence of Amendment 27 is written for one case (the 2015 table the more accurate "
            "on the older arrivals when weighted by playing time); the record of E34 is in another: this "
            "goes to Amir"
        )
    return E34_POINTER.format(n=s["n"])


def check_g27(text: str, d) -> None:
    """Gates G27b to G27d of Amendment 27, on the composed text (G27a: the test of the file)."""
    pointer = e34_pointer(d)
    marks = text.count(E34_POINTER_MARK)
    notes = text.count(AMEND27_NOTE_MARK)
    if not pointer:
        if marks or notes:
            raise ClaimError(
                "G27b: the sentence of Amendment 27 is printed only with the passage of E34"
            )
        return
    main = main_text(text)
    paragraph = [p for p in main.split("\n\n") if E31_NEITHER in p]
    if (
        marks != 1
        or len(paragraph) != 1
        or f"{E31_NEITHER} {pointer}" not in paragraph[0]
        or not paragraph[0].startswith(
            "**A published league table on the same players.**"
        )
        or E34_MARK not in main
    ):
        raise ClaimError(
            'G27b: the sentence of Amendment 27 stands once, directly after "On neither sample can the two '
            'be told apart, which is not the same as equal.", in the paragraph on the published league '
            "table, and only with the passage of E34"
        )
    if notes != 1 or AMEND27_NOTE_MARK not in appendix_of(text, "N"):
        raise ClaimError(
            "G27c: Appendix N says when the sentence of Amendment 27 was added, with its reference"
        )
    if text.count(E31_NEITHER) != 1:
        raise ClaimError(
            'G27d: "On neither sample can the two be told apart" stays word for word, once'
        )


# ---------------------------------------------------------------- Amendment 28: repairs of wording and drawing
#: Gate G28a: the amendment as registered (the test of the file compares it with this value).
AMENDMENT_28 = Path(
    "docs/research/sloan-full-paper-preregistration-amendment-28-2026-11-26.md"
)
AMENDMENT_28_SHA256 = "d481986f0fd347d6e1c80ad0b1ff366acd54eaad14649c2eb1f7df26ecdf2e9d"
#: Rule 6: one sentence in Appendix N, in every state.
AMEND28_NOTE = (
    "On 26 November 2026, after three readers had read the final paper, thirteen sentences were repaired, "
    "four sentences that define the paper's terms were added and the figures were redrawn in one style; no "
    "number and no registered sentence changed [@amend28]."
)
AMEND28_NOTE_MARK = "after three readers had read the final paper"
#: Rule 3: the four added sentences, by their first words.
AMEND28_DEFINITIONS = (
    "A season is named by the year in which it starts",
    "We call these three the history-only, the destination-only and the league-aware forecast",
    "The ten league numbers are the conversion table",
    "Tiers follow the rule registered before the analysis",
)


def check_g28(text: str, d) -> None:
    """Gate G28c of Amendment 28, on the composed text: Appendix N says when the wording was repaired,
    with its reference, and each of the four definitions stands once (G28a: the test of the file; G28b:
    the fixture of gate G19c; G28d and G28e: tests against render 55)."""
    if text.count(AMEND28_NOTE_MARK) != 1 or AMEND28_NOTE_MARK not in appendix_of(
        text, "N"
    ):
        raise ClaimError(
            "G28c: Appendix N says when the wording was repaired, with the reference to Amendment 28"
        )
    for words in AMEND28_DEFINITIONS:
        if text.count(words) != 1:
            raise ClaimError(
                f"G28: the definition of Amendment 28, rule 3, stands once: '{words}'"
            )


# ---------------------------------------------------------------- Amendment 29: the first page, further repairs
#: Gate G29a: the amendment as registered (the test of the file compares it with this value).
AMENDMENT_29 = Path(
    "docs/research/sloan-full-paper-preregistration-amendment-29-2026-11-26.md"
)
AMENDMENT_29_SHA256 = "e49f2c09f25f7b7f2b673697e65c93895b240f7504bc07501d5d34f7306ea9e3"
#: Amendment 30 (26 November 2026): corrections to the changes of Amendment 29, made after a fresh
#: reader had checked them against the rest of the paper. Gate G30a: the file as registered.
AMENDMENT_30 = Path(
    "docs/research/sloan-full-paper-preregistration-amendment-30-2026-11-26.md"
)
AMENDMENT_30_SHA256 = "0bc7d691790fe9337db56bc56fc01ef617772f19657dee322d540d684401ab7a"
#: Its rule 3: the close of the paragraph of Amendment 29 in Appendix N (gate G30b).
#: Amendment 32 (27 November 2026): twenty-seven passages reworded for register, the appendix
#: tables numbered in the order in which they stand, values printed on three figures. Gate G32a:
#: the file as registered.
AMENDMENT_32 = Path(
    "docs/research/sloan-full-paper-preregistration-amendment-32-2026-11-27.md"
)
AMENDMENT_32_SHA256 = "8daea8c78fb94403444410c7001f6e7e2ffcda295ce6d9e526df15842b2acb4f"
#: Its rule 3: one sentence in Appendix N, and the closing sentence of Amendment 30 with this
#: amendment in its list (gate G32b).
AMEND32_NOTE = (
    "On 27 November 2026 twenty-seven passages were reworded for register, the appendix tables were numbered in "
    "the order in which they stand and values were printed on three figures; no result and no registered reading "
    "changed, and each reworded passage is listed with its old and new words [@amend32]. Amendments 28, 29, 30 "
    "and 32 together list every change made to the text of the paper since the version of 25 November 2026."
)
AMEND32_NOTE_MARK = "twenty-seven passages were reworded for register"
AMEND30_NOTE = (
    "A fresh reader then checked these changes against the rest of the paper, and eighteen places were corrected "
    "the same day [@amend30]. " + AMEND32_NOTE
)
AMEND30_NOTE_MARK = (
    "A fresh reader then checked these changes against the rest of the paper"
)
#: Rule 6: one paragraph in Appendix N, in every state.
AMEND29_HEAD = "**A second round of repairs, and the first page.**"
AMEND29_NOTE = (
    "On 26 November 2026, after five readers had read the final paper again and three blind readers had "
    "compared two first pages, the first page was reworded, further sentences were repaired or added, and the "
    "two values of a registered read-out of the frozen test were printed in Appendix L; no result changed, and "
    "each changed sentence is listed with its old and new words [@amend29]. "
    + AMEND30_NOTE
)
AMEND29_NOTE_MARK = "after five readers had read the final paper again"
FIRST_PAGE_BAND = re.compile(
    r"a (\d+\.\d+) EFF/36 gap that comes entirely from the two league numbers\. The forecast for a single player "
    r"has a typical 80% error band of ±(\d+\.\d+) EFF/36, wider than that gap"
)


def check_g29(text: str, d) -> None:
    """Gates G29b and G29c of Amendment 29, on the composed text (G29a: the test of the file; G29d:
    the fixture of gate G19c). G29b: Appendix N says what was changed, with both references. G29c:
    the first page carries each sentence of rule 1 once, and the error band it prints beside the
    gap of the two recruits is the wider of the two."""
    if text.count(AMEND29_NOTE_MARK) != 1 or AMEND29_NOTE_MARK not in appendix_of(
        text, "N"
    ):
        raise ClaimError(
            "G29b: Appendix N says what the second round changed, with the reference to Amendment 29"
        )
    abstract, first = (
        section_of(text, "Abstract"),
        section_of(text, "Why the question matters"),
    )
    for where, name, words in (
        (abstract, "abstract", FIRST_PAGE_TESTS),
        (abstract, "abstract", FIRST_PAGE_UNIT),
        (first, "introduction", FIRST_PAGE_HEADS[0]),
        (first, "introduction", FIRST_PAGE_HEADS[1]),
        (first, "introduction", FIRST_PAGE_CLUB_HEAD),
    ):
        if where.count(words) != 1:
            raise ClaimError(
                f"G29c: the {name} carries once: '{words}' (Amendment 29, rule 1)"
            )
    if text.count(AMEND30_NOTE_MARK) != 1 or AMEND30_NOTE_MARK not in appendix_of(
        text, "N"
    ):
        raise ClaimError(
            "G30b: Appendix N says that the changes of Amendment 29 were checked and corrected, with the "
            "reference to Amendment 30"
        )
    band = FIRST_PAGE_BAND.search(first)
    if band is None or not float(band.group(2)) > float(band.group(1)):
        raise ClaimError(
            "G29c: the first page prints the error band of one forecast beside the gap of the two recruits "
            "and calls it the wider; it is not"
        )


def check_g32(text: str) -> None:
    """Gate G32b of Amendment 32, on the composed text: Appendix N says what was changed on 27
    November 2026, with the reference, and the list of amendments that hold every change since
    25 November names this one (G32a: the test of the file; G32c: the test of the list; G32d:
    ``printed``; G32e: the tests of the figures)."""
    if text.count(AMEND32_NOTE_MARK) != 1 or AMEND32_NOTE_MARK not in appendix_of(
        text, "N"
    ):
        raise ClaimError(
            "G32b: Appendix N says what was reworded and renumbered, with the reference to Amendment 32"
        )
    if "Amendments 28, 29 and 30 together" in text or (
        text.count("Amendments 28, 29, 30 and 32 together list every change") != 1
    ):
        raise ClaimError(
            "G32b: the amendments that list every change since 25 November 2026 are 28, 29, 30 and 32"
        )


def e34_blocks(d, blocks: dict) -> dict:
    """What E34 adds to the paper (Amendment 23, rule 5): nothing until its run is committed."""
    s = d.get("e34")
    if s is None:
        return {"e34_main": "", "table:e34": "", "e34_note": ""}
    e34_check(d)
    out = {}
    for key, old, new in (
        ("section:related", E34_RELATED_OLD, E34_RELATED_NEW),
        ("related_full", E34_RELATED_FULL_OLD, E34_RELATED_FULL_NEW),
    ):
        if blocks[key].count(old) != 1:
            e34_refuse(
                'the sentence that the 2026 scale "is not scored here" is not where rule 5 replaces it'
            )
        out[key] = blocks[key].replace(old, new)
    k = e34_table_number(blocks)
    out["e34_main"] = e34_main(s, k) + "\n\n"
    out["table:e34"] = table_e34(s, k) + "\n\n"
    out["e34_note"] = (
        "\n\n**A study taken from a review of the paper.** "
        + E34_NOTE
        + (" " + AMEND27_NOTE if e34_pointer(d) else "")
    )
    return out


def check_g34(text: str, d, blocks: dict) -> None:  # noqa: C901 -- one gate with its controls
    """Gate G34d (Amendment 23), on the composed text before its citations are numbered.

    The label of rule 5 stands with every printing of an E34 number: in the paragraph of the
    passage in Results and in the caption of the table, and no interval of E34 stands in any other
    paragraph. The passage prints for each scale the less favourable weighting of G_S and names
    the weighting of every reading. The sentence of Appendix N stands whenever E34 is printed. The
    words rule 5 excludes are in neither block, and the sentence that the 2026 scale "is not
    scored here" is in no part of the paper. Without the record of E34 nothing of it is printed."""
    s = d.get("e34")
    marks = (E34_MARK, E34_LABEL_MARK, E34_NOTE, "(E34, exploratory)")
    if s is None:
        if any(mark in text for mark in marks):
            raise ClaimError("G34d: E34 is printed without its committed record")
        return
    paragraphs = text.split("\n\n")
    passage = [p for p in paragraphs if p.startswith(E34_MARK)]
    table = [
        p for p in paragraphs if "(E34, exploratory)" in p and p.startswith("Table A")
    ]
    older_part = main_text(text).split(
        "\n### The same frozen models on arrivals of 2008–2015\n"
    )
    if len(passage) != 1 or len(table) != 1 or len(older_part) != 2:
        raise ClaimError(
            "G34d: the passage and the table of E34 each stand once in the paper"
        )
    section = older_part[1].split("\n### ")[0]
    if passage[0] not in section or section.index(passage[0]) < section.index(
        blocks["e28_older_block"]
    ):
        raise ClaimError(
            "G34d: the passage of E34 stands in the section on the arrivals of 2008–2015, after the "
            "paragraph on the league numbers"
        )
    for name, block in (
        ("passage in Results", passage[0]),
        ("table in Appendix I", table[0]),
    ):
        if E34_LABEL not in block:
            raise ClaimError(
                f"G34d: an E34 number is printed without the label of rule 5 ({name})"
            )
        lowered = block.lower()
        for word in E34_BANNED:
            if word in lowered:
                raise ClaimError(
                    f"G34d: '{word}' is not a word the paper uses for E34 ({name})"
                )
    if text.count(E34_FACTS) != 1:
        raise ClaimError(
            "G34d: the four facts of rule 5 stand once, beside the table of E34"
        )
    for block in (passage[0], table[0], E34_FACTS):
        if "strength" in block.replace(E34_STRENGTH_ALLOWED, ""):
            raise ClaimError(
                "G34d: the paper does not say that a scale measures league strength"
            )
    # every interval of E34, in either orientation, stands only under the label
    spans = set()
    for block in [s["contrasts"]] + [s["by_league"][code] for code, _ in E34_SAMPLES]:
        for scale, *_ in E34_SCALES:
            for contrast in ("G", "T"):
                for w, _ in E34_WEIGHTS:
                    r = block[scale][contrast][w]
                    spans |= {e28_span(r), e34_reversed(r), interval(r["ci95"])}
    for p in paragraphs:
        if p in (passage[0], table[0]) or p.startswith("| "):
            continue
        if any(span in p for span in spans):
            raise ClaimError(
                "G34d: an E34 number is printed without the label of rule 5"
            )
    # the passage: the less favourable weighting of G_S, and every reading with its weighting
    clauses = re.split(r"; |(?<=\.) ", strip_citations(passage[0]))
    for scale, name, _, _ in E34_SCALES:
        c = s["contrasts"][scale]
        # computed here, not taken from the function that writes the passage
        worst, other = sorted(
            (w for w, _ in E34_WEIGHTS), key=lambda w: c["G"][w]["difference"]
        )
        printed = {
            w: any(
                span in passage[0]
                for span in (e28_span(c["G"][w]), e34_reversed(c["G"][w]))
            )
            for w in (worst, other)
        }
        if not printed[worst]:
            raise ClaimError(
                f"G34d: the passage does not print the less favourable weighting of G_S for {name}"
            )
        for contrast in ("G", "T"):
            for w, _ in E34_WEIGHTS:
                r = c[contrast][w]
                for clause in clauses:
                    if e28_span(r) in clause or e34_reversed(r) in clause:
                        named = (
                            re.search(r"\b[Uu]nweighted\b", clause)
                            if w == "unweighted"
                            # Amendment 29, rule 2: the reading may open a sentence of its own
                            else re.search(r"\b[Ww]eighted by playing time", clause)
                        )
                        if not named:
                            raise ClaimError(
                                "G34d: an E34 reading is printed without the name of its weighting"
                            )
    if not re.search(
        r"less favourable to the paper.*Appendix I gives both", passage[0]
    ):
        raise ClaimError(
            "G34d: the passage does not say that the reading shown for G_S is the less favourable of "
            "the two weightings and that both are in Appendix I"
        )
    if E34_NOTE not in appendix_of(text, "N"):
        raise ClaimError("G34d: the sentence of Appendix N on E34 is missing")
    if (
        E34_NOT_SCORED_MARK in text
        or text.count(E34_RELATED_NEW) != 1
        or (text.count(E34_RELATED_FULL_NEW) != 1)
    ):
        raise ClaimError(
            'G34d: the sentence that the 2026 scale "is not scored here" is replaced in Related work '
            "and in Appendix O"
        )


def amend23_note(d, scorecard: bool) -> str:
    """Appendix N: what Amendment 23 added to the text, naming only what this paper prints."""
    items = [
        "the unit in words",
        "the destination term beside the fitted equation",
        "the forecast level by competition",
    ]
    if prior_work_state(d) == PRIOR_WORK_NARROWED:
        items.append("a narrower statement on prior work")
    if scorecard:
        items.append("the scorecard of the frozen test in Appendix L")
    if d.get("e34") is not None:
        items.append("two published league scales on the older arrivals")
    return (
        " Further text was allowed on 22 November 2026, after the results on the examined seasons were known "
        f"and before the scoring of the frozen test: {', '.join(items[:-1])} and {items[-1]} [@amend23]."
    )


def check_g23(text: str, d) -> None:  # noqa: C901 -- four gates of one amendment, kept together
    """Gates G23a to G23d (Amendment 23), on the composed text. G23e is ``p1_scorecard_check`` and
    the arithmetic of G23b is ``destination_term_check``; both run when the files are loaded.

    G23a: the words the counter removes, "per 36 minutes", stand in the abstract only in the one
    sentence of rule 1 (the limit itself is gate G17b, in ``check_first_page``). G23b: wherever
    the destination term is printed, its label stands in the same sentence or the next, and the
    term is in neither the title, the abstract nor the conclusion. G23c: the words on the
    forecast level by competition follow the case of each committed interval, "was not tested"
    stands in the same sentence or the next, and neither value is called detectable or not
    detectable. G23d: the new sentences on prior work are printed only in the state the record
    of rule 4 gives, and the old and the new sentence never stand together."""
    abstract = section_of(text, "Abstract")
    # Amendment 29, rule 1: the unit stands in the Equivalents line (FIRST_PAGE_UNIT) in place of
    # the sentence of Amendment 23, rule 1; either form, once
    unit_forms = abstract.count(ABSTRACT_UNIT_SENTENCE) + abstract.count(
        FIRST_PAGE_UNIT
    )
    if abstract.count(ABSTRACT_UNIT_WORDS) != unit_forms:
        raise ClaimError(
            f"G23a: the words '{ABSTRACT_UNIT_WORDS}' stand in the abstract outside the sentence of "
            "Amendment 23, rule 1, or the line of Amendment 29, rule 1"
        )
    if unit_forms > 1:
        raise ClaimError("G23a: the abstract carries the sentence on the unit once")
    sentences = sentences_of(text)

    def nearby(i: int) -> str:
        return sentences[i] + " " + (sentences[i + 1] if i + 1 < len(sentences) else "")

    # G23b: the label of the destination term
    value = num(abs(destination_term(d)), 2)
    label = [
        part.format(rate=f"{reference_rate(d):g}") for part in DESTINATION_TERM_LABEL
    ]

    def prints_term(passage: str) -> bool:
        return DESTINATION_TERM_MARK in passage and value in passage

    for i, sentence in enumerate(sentences):
        if not prints_term(sentence):
            continue
        absent = [part for part in label if part not in nearby(i)]
        if absent:
            raise ClaimError(
                f"G23b: the destination term is printed without its label ({absent}) in the same sentence "
                "or the next"
            )
    for name in ("Abstract", "Conclusion"):
        if any(prints_term(s) for s in sentences_of(section_of(text, name))):
            raise ClaimError(f"G23b: the destination term is printed in '{name}'")
    if prints_term(text.splitlines()[1]):
        raise ClaimError("G23b: the destination term is printed in the title")
    # G23c: the forecast level by competition
    rows = level_by_competition(d)
    codes = {name: code for code, name in LEVEL_COMPETITIONS}
    wanted_tail = level_not_tested(d)
    printed = 0
    for i, sentence in enumerate(sentences):
        hits = list(LEVEL_CLAUSE.finditer(sentence))
        if not hits:
            continue
        printed += len(hits)
        for hit in hits:
            name = hit.group(1)
            wanted = level_clause(name, rows[codes[name]])
            if wanted[1:] not in sentence:
                raise ClaimError(
                    f"G23c: the words on {name} arrivals do not follow the committed interval of the forecast "
                    f"level; registered: '{wanted}'"
                )
        if "was not tested" not in nearby(i) or wanted_tail not in nearby(i):
            raise ClaimError(
                f"G23c: the forecast level by competition is printed without '{wanted_tail}' in the same "
                "sentence or the next"
            )
        if "detectable" in nearby(i):
            raise ClaimError(
                "G23c: a forecast level by competition is called detectable or not detectable"
            )
    if printed:
        paragraphs = [
            p
            for p in section_of(text, "Results").split("\n\n")
            if LEVEL_CLAUSE.search(p)
        ]
        placed = (
            len(paragraphs) == 1
            and printed == len(LEVEL_CLAUSE.findall(paragraphs[0]))
            and paragraphs[0].startswith(LEVEL_PARAGRAPH)
            and LEVEL_NO_CAUSE in paragraphs[0]
            and paragraphs[0].index(LEVEL_NO_CAUSE)
            > max(m.start() for m in LEVEL_CLAUSE.finditer(paragraphs[0]))
        )
        if not placed:
            raise ClaimError(
                "G23c: the forecast level by competition stands in Results, in the paragraph on the forecast "
                f"level, before '{LEVEL_NO_CAUSE}'"
            )
        if "detectable" in paragraphs[0]:
            raise ClaimError(
                "G23c: the paragraph on the forecast level calls a value detectable or not detectable"
            )
    # G23d: prior work. The record is read first: one that holds a comparison with and without a
    # league level is refused whatever the text says. (A full read dated before it was allowed is
    # refused where the files are loaded, by ``prior_work_order_check``.)
    state = prior_work_state(d)
    old, new = PRIOR_WORK_OLD_MARK in text, PRIOR_WORK_NEW_MARK in text
    if old and new:
        raise ClaimError(
            "G23d: the paper holds both the old and the new sentence on prior work"
        )
    if state == PRIOR_WORK_KEPT and (new or PRIOR_WORK_FOUND_MARK in text):
        raise ClaimError(
            "G23d: the new sentences on prior work are printed while the record of rule 4 lacks the date of a "
            "full read or what a page reports"
        )
    if state == PRIOR_WORK_NARROWED and old:
        raise ClaimError(
            "G23d: the record of rule 4 is complete, yet the old sentence on prior work is in the paper"
        )


def appendix_of(text: str, letter: str) -> str:
    """One lettered appendix of the composed paper."""
    heading = f"\n### {letter}. "
    if text.count(heading) != 1:
        raise ClaimError(f"the paper has no single Appendix {letter}")
    return text.split(heading)[1].split("\n### ")[0]


def check_g24(text: str, d) -> None:
    """Gate G24b (Amendment 24, rule 2), on the composed text.

    The condition of rule 4 and gate G23d of Amendment 23 apply in every status of the frozen
    test, word for word, so this check does not ask for the status. With every named page read
    in full and no comparison in the record, the two statements of rule 4 are printed, in
    Related work and in Appendix O (that the old sentence is then in no part of the paper is
    gate G23d). Appendix N carries the one sentence that Amendment 24 allows it, word for word
    and once, with the reference of that amendment.

    Two parts of the gate are tests (tests/test_scripts/test_sloan_fullpaper_amend24.py): that
    the texts which state the status of the frozen test are the same with the pages read and
    unread, and the negative controls. Gate G24a is ``prior_work_order_check``.
    """
    if prior_work_state(d) == PRIOR_WORK_NARROWED:
        related, full = section_of(text, "Related work"), appendix_of(text, "O")
        printed = (
            related.count(PRIOR_WORK_FOUND_MARK) == 1
            and related.count(PRIOR_WORK_NOT_FOUND) == 1
            and full.count(PRIOR_WORK_NOT_FOUND) == 1
        )
        if not printed:
            raise ClaimError(
                "G24b: the record of rule 4 is complete, and the two statements of Amendment 23, rule 4, are "
                "not both printed in Related work and in Appendix O"
            )
    words = ORDER_OF_READING_NOTE.split(" [@")[0]
    cited = re.search(re.escape(words) + r" \[(\d+)\]\.", appendix_of(text, "N"))
    if (
        cited is None
        or text.count(words) != 1
        or text.count(ORDER_OF_READING_MARK) != 1
        or f"[{cited.group(1)}] Pre-registration Amendment 24:" not in text
    ):
        raise ClaimError(
            "G24b: Appendix N carries the sentence of Amendment 24, rule 2, once and word for word, with the "
            "reference of that amendment"
        )


def check_g26(text: str, d) -> None:  # noqa: C901 -- six gates of one amendment, kept together
    """Gates G26a to G26f (Amendment 26), on the composed text. G26a is checked with G25b.

    G26b: in the inconclusive state the section on the frozen test begins with the sentence that
    dates the one scoring run and gives the outcome, before the design, and the design paragraph
    holds no verb of a scoring still to come. G26c: the paper holds none of the wordings written
    for a test still to come; the Limitations entry begins with the outcome; the sentence of rule
    8 stands in Appendix N. G26d: no registered reading stands in the paragraph of the contrasts
    printed for the record. G26e: the abstract and the conclusion end with the sentences of rule
    9 (for the cause that occurred). G26f: the two descriptive sentences stand once each, in the
    paragraphs named, with their caveats. In every other state none of the words of rules 1 to 9
    is printed.
    """
    main = main_text(text)
    # G26f, in every state
    club = [
        p.strip()
        for p in section_of(text, "What a club can use").split("\n\n")
        if GAPS_GREW_MARK in p
    ]
    worth = [p.strip() for p in main.split("\n\n") if GAIN_SIZE_MARK in p]
    if (
        text.count(GAPS_GREW_MARK) != 1
        or len(club) != 1
        or not club[0].startswith("**European League Equivalents.**")
        or GAPS_GREW_CAVEAT not in club[0].split(GAPS_GREW_MARK)[1]
    ):
        raise ClaimError(
            "G26f: the sentence on the gaps that grew stands once, in the paragraph on the Equivalents, "
            "with 'The cause was not examined' (Amendment 26, rule 10)"
        )
    if (
        text.count(GAIN_SIZE_MARK) != 1
        or len(worth) != 1
        or not worth[0].startswith("**What the league numbers are worth.**")
        or any(c not in worth[0].split(GAIN_SIZE_MARK)[1] for c in GAIN_SIZE_CAVEATS)
        or "EuroLeague arrivals" not in worth[0].split(GAIN_SIZE_MARK)[1]
        or "EuroCup arrivals" not in worth[0].split(GAIN_SIZE_MARK)[1]
    ):
        raise ClaimError(
            "G26f: the sentence on the size of the gain stands once, in the paragraph on what the league "
            "numbers are worth, with both competitions and both caveats (Amendment 26, rule 11)"
        )
    section = (
        main.split("\n### The outcome-blinded 2026–27 test\n")[1]
        .split("\n## ")[0]
        .strip()
    )
    limits = [
        p
        for p in section_of(text, "Limitations").split("\n\n")
        if p.startswith("**Frozen test.**")
    ]
    after_scoring = (
        P1_S2_INCONCLUSIVE,
        TWO_TESTS_END_INCONCLUSIVE,
        OFFER_TESTS_INCONCLUSIVE,
        P1_DETECT_HEAD_PAST,
        P1_RULE_NOT_APPLIED,
        P1_PAIRS_NOT_PRINTED,
        "That test, separate from the test on league changes, is inconclusive",
        "**Frozen test.** Inconclusive",
        *(new for _, new in P1_PAST_TENSE),
        P1_DESIGN_POINTER_PAST,
    )
    if not p1_is_inconclusive(d):
        if hits := [w for w in after_scoring if w in text]:
            raise ClaimError(
                f"G26: words of Amendment 26, rules 1 to 9, are printed outside the inconclusive state: {hits[:2]}"
            )
        return
    p = d["p1"]
    # G26b
    opening = (
        "The test was scored once, on "
        if p1_lost_targets_cause(p)
        else "The scoring run was made once, on "
    ) + long_date(p["scored_on"])
    if not section.startswith(opening) or section.index(
        "We froze forecasts"
    ) < section.index("inconclusive"):
        raise ClaimError(
            "G26b: the section on the frozen test begins with the day of the scoring and its outcome, before "
            "the design (Amendment 26, rule 3)"
        )
    for old in (*(old for old, _ in P1_PAST_TENSE), P1_DESIGN_POINTER):
        if old in text:
            raise ClaimError(
                f"G26b: the design of the frozen test is in the past tense; found '{old}'"
            )
    if p1_lost_targets_cause(p):
        j, first = p["join"], section.split("\n\n")[0]
        for value in (
            f"Of the {j['newcomers_reaching_eight_games']} newcomers",
            f"{j['joined']} had a frozen forecast under their name and {j['unjoined']} did not",
            f"{j['possible_lost_targets']} of the {j['unjoined']} may be",
            f"the {j['joined']} joined newcomers that is {pct(j['possible_lost_share_of_joined'])}, above the "
            f"{pct(j['threshold'], 0)} we allowed in advance",
        ):
            if value not in first:
                raise ClaimError(
                    f"G26b: the outcome does not carry the score record's '{value}'"
                )
    # G26c
    old_wordings = (
        TWO_TESTS_END.split("; ")[1].rstrip("."),
        OFFER_TESTS.replace("tests ", ""),
        P1_DETECT_HEAD.strip("*").rstrip("."),
        "its required data or validity controls did not pass",
    )
    if p1_lost_targets_cause(p) and e30_case(d) in E30_TESTED:
        old_wordings += (P1_SUMMARY_INCONCLUSIVE_OLD.split(",")[0],)
    if hits := [w for w in old_wordings if w in text]:
        raise ClaimError(
            f"G26c: the paper still carries wording written for a frozen test still to come: {hits[:2]}"
        )
    if len(limits) != 1 or not limits[0].startswith("**Frozen test.** Inconclusive"):
        raise ClaimError(
            "G26c: the Limitations entry on the frozen test begins with its outcome"
        )
    if amendment_20(d) and P1_PAIRS_NOT_PRINTED not in appendix_of(text, "N"):
        raise ClaimError(
            "G26c: Appendix N says that the named pairs are not printed (Amendment 26, rule 8)"
        )
    # G26d
    record = [p_ for p_ in text.split("\n\n") if "(no sentence is licensed).**" in p_]
    for paragraph in record:
        if hits := [w for w in P1_READING_WORDS if w in paragraph]:
            raise ClaimError(
                f"G26d: a registered reading stands beside the contrasts printed for the record: {hits[:2]}"
            )
    if p.get("contrasts_printed") and len(record) != 1:
        raise ClaimError(
            "G26d: the contrasts for the record stand once, under 'no sentence is licensed'"
        )
    # G26e
    if p1_lost_targets_cause(p) and e30_case(d) in E30_TESTED:
        j = p["join"]
        ending = (
            "were scored once on 2026–27 newcomers. That test, separate from the test on league changes, is "
            f"inconclusive: {j['possible_lost_targets']} newcomers without a forecast may be in the frozen file "
            f"under another spelling, more than the {pct(j['threshold'], 0)} of the {j['joined']} joined newcomers "
            "that was allowed in advance."
        )
        abstract = text.split("## Abstract")[1].split("\n## ")[0].strip()
        conclusion = section_of(text, "Conclusion").strip()
        if not abstract.endswith(ending) or not conclusion.endswith(ending):
            raise ClaimError(
                "G26e: the abstract and the conclusion end with the sentences of Amendment 26, rule 9"
            )


def check_examined(text: str, d) -> None:
    """The sentence that says which evidence is exploratory names the earlier arrivals in a scored
    paper and stands as it always has in every other state: twice, in the first section and in the
    conclusion. (No registration fixes this sentence; see ``P1_EXAMINED``.)"""
    main = text.split("## References")[0]
    want, other = (
        (P1_EXAMINED_SCORED, P1_EXAMINED)
        if p1_scored(d)
        else (P1_EXAMINED, P1_EXAMINED_SCORED)
    )
    if main.count(want) != 2 or other in text:
        raise ClaimError(
            "the sentence on what was examined before registration is not the one for this state "
            "of the frozen test, in the first section and in the conclusion"
        )


def check_g25(text: str, d) -> None:  # noqa: C901 -- four gates of one amendment, kept together
    """Gates G25a to G25d (Amendment 25), on the composed text.

    G25a: the figure of the registered paired contrasts stands in the main text of a scored paper,
    once, with its registered caption, before the table of five named pairs, and in no other
    state; a scored paper without it carries the sentence of rule 1 in Appendix N. That every
    number in the figure is the score record's is tested on ``p1_figure_rows``
    (tests/test_scripts/test_sloan_fullpaper_amend25.py).
    G25b: in a scored paper the abstract, the introduction and the conclusion each carry the words
    of the case the score record gives for S2, and the clause of Amendment 13, rule 1, is in no
    part of the paper; in every other state that clause stands in both places.
    G25c: in a scored paper the main text holds the sentences on the ordering of cross-league pairs.
    G25d: the clause of rule 4 stands in the main text if and only if the interval of the score
    record excludes the 2020-2025 estimate.
    """
    main, note = main_text(text), appendix_of(text, "N")
    scored = p1_scored(d)
    embeds = text.count(f"](figures/{P1_FIGURE_FILE})")
    if not scored:
        if AMEND25_MARK in text or "Pre-registration Amendment 25:" in text:
            raise ClaimError(
                "G25: nothing of Amendment 25 is printed in a paper whose frozen test is not scored, "
                "its note in Appendix N and its reference included"
            )
        if embeds or P1_FIGURE_CAPTION_MARK in text or P1_FIGURE_NOT_PRINTED in text:
            raise ClaimError(
                "G25a: the figure of the frozen test's contrasts is printed in the scored state only"
            )
        # Amendment 26, rule 1 (gate G26a): in the inconclusive state the clause states the outcome
        promise, other = (
            (P1_S2_INCONCLUSIVE, P1_S2_PROMISE)
            if p1_is_inconclusive(d)
            else (P1_S2_PROMISE, P1_S2_INCONCLUSIVE)
        )
        if (
            main.count(promise) != 2
            or promise not in section_of(text, "Why the question matters")
            or promise not in section_of(text, "Conclusion")
            or other in text
        ):
            raise ClaimError(
                "G25b and G26a: until the frozen test is scored the introduction and the conclusion say that "
                "it carries a registered read-out for this gain (Amendment 13, rule 1); once it is "
                "inconclusive they say that it carried one and is inconclusive (Amendment 26, rule 1)"
            )
        late = (
            P1_EARLIER_MARK,
            P1_S2_NOT_DETECTABLE,
            P1_WORDING[("S2", "above_zero")].split(" by X")[0],
            P1_S2_LESS_ACCURATE,
            P1_FIGURE_POINTER.split("} ")[1],
            P1_FIGURE_BANDS.split("{")[0],
            P1_EXAMINED_SCORED,
        )
        if (
            any(words in text for words in late)
            or "newcomers of the frozen 2026–27 test," in main
            or P1_ORDER_SPLIT.strip() in main
        ):
            raise ClaimError(
                "G25: a sentence of Amendment 25 is printed in a paper whose frozen test is not scored"
            )
        return
    words = AMEND25_NOTE.split(" [@")[0]
    cited = re.search(re.escape(words) + r" \[(\d+)\]\.", note)
    if (
        cited is None
        or text.count(AMEND25_MARK) != 1
        or f"[{cited.group(1)}] Pre-registration Amendment 25:" not in text
    ):
        raise ClaimError(
            "G25: Appendix N of a scored paper says once what Amendment 25 fixed, with the reference "
            "of that amendment"
        )
    p = d["p1"]
    section = main.split("### The outcome-blinded 2026–27 test")[1].split("\n## ")[0]
    # G25a
    if P1_FIGURE_READY:
        block = p1_figure_block(d)
        numbers = [int(n) for n in re.findall(r"^!\[Figure (\d+)\.", main, re.M)]
        if (
            embeds != 1
            or section.count(block) != 1
            or numbers != list(range(1, len(numbers) + 1))
            or P1_FIGURE_NOT_PRINTED in text
        ):
            raise ClaimError(
                "G25a: a scored paper prints the figure of the registered paired contrasts once, in the "
                "section on the frozen test, with its registered caption"
            )
        if "\nTable " in section and section.index(block) > section.index("\nTable "):
            raise ClaimError(
                "G25a: the figure stands before the table of five named pairs"
            )
        ordering = p1_order_sentence(p)  # that it is there at all is G25c
        if (
            ordering in section and section.index(block) < section.index(ordering)
        ) or appendix_of(text, "L").count(p1_figure_bands(p)) != 1:
            raise ClaimError(
                "G25a: the figure stands after the paragraphs that report its contrasts, and Appendix L "
                "says what its bands are"
            )
    elif (
        embeds
        or P1_FIGURE_CAPTION_MARK in text
        or note.count(P1_FIGURE_NOT_PRINTED) != 1
    ):
        raise ClaimError(
            "G25a: a scored paper without the figure says in Appendix N that it was registered and is "
            "not printed"
        )
    # G25b
    if P1_S2_PROMISE in text:
        raise ClaimError(
            'G25b: a scored paper still says that the frozen test "carries a registered read-out for this gain"'
        )
    short, full = p1_s2_words(p, abstract=True), p1_s2_words(p)
    abstract = text.split("## Abstract")[1].split("\n## ")[0]
    cases = {
        "above_zero": P1_WORDING[("S2", "above_zero")].split(" by X")[0],
        "includes_zero": P1_S2_NOT_DETECTABLE,
        "below_zero": P1_S2_LESS_ACCURATE,
    }
    # the case is read here from the interval itself, not taken from p1_s2_words(): the gate
    # must not share the selector's logic
    low, high = p1_ci(p["secondary"]["S2"])
    case = "above_zero" if low > 0 else "below_zero" if high < 0 else "includes_zero"
    lead = f"on the {p['n_scored']} newcomers of the frozen 2026–27 test, "
    for part, expected, name in (
        (abstract, short, "abstract"),
        (section_of(text, "Why the question matters"), lead + full, "introduction"),
        (section_of(text, "Conclusion"), lead + full, "conclusion"),
    ):
        if (
            part.count(expected) != 1
            or part.count(cases[case]) != 1
            or sum(part.count(c) for c in cases.values()) != 1
            or (case == "below_zero" and P1_S2_FAILURE not in part)
        ):
            raise ClaimError(
                f"G25b: the {name} carries the read-out of the league numbers once, in the words of the "
                "case the score record gives (Amendment 25, rule 2)"
            )
    # G25c
    # the three values of the read-out are looked for themselves, so that sentences which
    # lost them do not pass
    order = p["secondary"]["S4"]["cross"]
    low, high = order["league_aware"]["ci95"]
    share_case = (
        "above_half" if low > 0.5 else "below_half" if high < 0.5 else "includes_half"
    )
    low, high = order["league_aware_minus_history"]["ci95"]
    gap_spans_zero = low <= 0 <= high
    if (
        order["league_aware"]["reading"] != share_case
        or (order["league_aware_minus_history"]["reading"] == "includes_zero")
        != gap_spans_zero
        or (P1_ORDER_NOT_DETECTABLE in p1_order_sentence(p)) != gap_spans_zero
    ):
        raise ClaimError(
            "G25c: the reading of the ordering of cross-league pairs differs from the intervals of the "
            "score record"
        )
    values = (
        f"ordered {pct(order['league_aware']['share_correct'])} of cross-league pairs"
        if order["league_aware"]["reading"] != "includes_half"
        else f"({pct(order['league_aware']['share_correct'])} correct;",
        f"{order['unequal_pairs']:,} ",
        f"History alone ordered {pct(order['history']['share_correct'])}",
    )
    if (
        p1_order_sentence(p) not in section
        or p1_order_appendix(p) not in appendix_of(text, "L")
        or any(value not in section for value in values)
    ):
        raise ClaimError(
            "G25c: the sentences on the ordering of cross-league pairs are in the main text of a scored "
            "paper, and Appendix L keeps them"
        )
    # G25d
    # stated again here, from the anchors of the score record and the committed summary of
    # E28a, not taken from p1_excludes_earlier(): the gate must not share the logic of the text
    gains = d["amend9"]["e28a"]["contrasts"]
    estimates = {
        **{key: p["anchor"][key] for key in P1_CONTRASTS},
        "S1": gains["G_H"]["unweighted"]["difference"],
        "S2": gains["G_D"]["unweighted"]["difference"],
    }
    expected = []
    for key, estimate in estimates.items():
        low, high = p1_ci(p1_contrast(p, key))
        if (estimate < low or estimate > high) and p["verdicts"].get(key) != "fails":
            expected.append(f"{P1_EARLIER_MARK}{num(estimate)})")
    if main.count(P1_EARLIER_MARK) != len(expected) or any(
        section.count(c) != expected.count(c) for c in expected
    ):
        raise ClaimError(
            "G25d: the clause on the 2020-2025 estimate stands if and only if the interval of the score "
            "record excludes that estimate (Amendment 25, rule 4)"
        )


def strip_citations(text: str) -> str:
    return re.sub(r"\s*\[@[a-z0-9]+(?:;\s*@[a-z0-9]+)*\]", "", text)


def check_g19c(text: str, d, blocks: dict, f: dict) -> None:
    """Gate G19c (Amendment 19), on the composed text before its citations are numbered: every
    item of rule 11's "may not move" list is in the main text, and the registered wording the
    renderer composes is in the paper. The sentence-by-sentence comparison with render 39 is a
    test (tests/test_scripts/test_sloan_fullpaper_amend19.py)."""
    body, whole = strip_citations(main_text(text)), strip_citations(text)
    main = body.split("\n## Data and code\n")[0]

    def need(label, wanted, where, place):
        for sentence in sentences_of(strip_citations(wanted)):
            if sentence.rstrip(".") not in where:
                raise ClaimError(
                    f"G19c: {label} is missing from {place}: '{sentence[:90]}'"
                )

    for label, key in G19C_MAIN_BLOCKS:
        need(label, blocks[key] if key in blocks else f[key], main, "the main text")
    for label, wanted in G19C_MAIN_TEXTS:
        need(label, wanted.format(**f), main, "the main text")
    for label, wanted in G19C_PAPER_TEXTS:
        need(label, wanted, whole, "the paper")
    for name in ("Why the question matters", "Limitations"):
        if G19C_PAPER_TEXTS[0][1].split(",", 1)[1].strip() not in section_of(
            text, name
        ) and ("not clearly above zero" not in section_of(text, name)):
            raise ClaimError(
                f"G19c: the playing-time reading (Amendment 13, rule 4) is missing from '{name}'"
            )
    # Amendment 7, "Measured weakness": stated beside the E27 result, in its paragraph
    beside = [
        p
        for p in main.split("\n\n")
        if p.startswith("The same frozen models were also scored")
    ]
    need(
        "the measured weakness of the name link (Amendment 7: beside the E27 result)",
        older_link_weakness(d),
        beside[0] if beside else "",
        "the paragraph of the E27 result",
    )
    for part in ("trust60", "trust70"):
        need(
            "the forecast-gap guide's sentence (Amendment 3, E20)",
            f[part],
            main,
            "the main text",
        )
    if e30_case(d) != E30_NOT_RUN:
        s = e30_secondary(d)
        for key in ("left_out", "direction", "redrawn"):
            need(
                "the lowest leave-one-league-out slope, the both-directions statement and the "
                "redrawn-table interval of E30 (Amendment 19, rule 11)",
                s[key],
                main,
                "the main text",
            )
        need(
            "the registered sentence of E30 (Amendment 14)",
            e30_sentence(d),
            main,
            "the main text",
        )
    a = e31a(d)
    if a is not None:
        need(
            "the 2015 table against the destination-only forecast (Amendment 19, rule 7)",
            e31_appendix(d),
            whole,
            "the paper",
        )


# ---------------------------------------------------------------- Amendment 16, rule 8: why the average gain is small
def small_gain(d) -> dict:
    """Committed numbers for the passage on why a league bias of about one EFF/36 buys a small
    average gain. Nothing is estimated here: the largest detectable league bias (E24), the league-aware
    forecast's error (Table 1) and the guards that keep the passage's comparisons true."""
    blind = f"rebased_{A3_D}"
    leagues = get(d["amend4"], "e24/leagues")
    detectable = [r for r in leagues if r["licence"] == "licensed"]
    if not detectable:
        raise ClaimError("no league bias is detectable; rewrite the passage")
    top = max(detectable, key=lambda r: abs(r[blind]))
    smaller = sum(abs(r[blind]) < abs(top[blind]) for r in leagues if r is not top)
    if 2 * smaller <= len(leagues) - 1:
        raise ClaimError("'most leagues have a smaller bias' is false")
    mae = get(d["recipes"], "results/A/R1/metrics/source_ridge_10/mae")
    if not mae > 2 * abs(top[blind]):
        raise ClaimError(
            "'more than twice that bias' is false for the league-aware forecast's error"
        )
    if not get(d["amend3"], "e21/licence/licensed"):
        raise ClaimError("the league-table flip sentence is not licensed")
    return {
        "bias_top": num(abs(top[blind]), 2),
        "bias_top_name": short_league(top["source_league"]),
    }


# ---------------------------------------------------------------- registered results moved into the main text
def promoted(d) -> dict:
    """Results that were registered and committed before 16 November and sat in the appendix or the notes."""
    rb, r = d["robust"], d["recipes"]
    k = get(rb, "e3_pattern_holds_k_of_3/player_club_season")
    if k != 3:
        raise ClaimError(
            "the pattern no longer holds on 3 of 3 other outcomes; reword the sentence"
        )
    seasons = get(rb, "e5/anchor/contrasts")
    gain, head = seasons["history_gain"], seasons["e1_head_to_head"]
    if gain["positive_seasons"] != gain["n_seasons"]:
        raise ClaimError(
            "translation's gain over history is no longer positive in every season"
        )
    ceiling = get(
        d["amend"], "e10/pooled/all_pools/cross/values/ceiling_true_rate_normal_model"
    )
    hist = pair_value(d, "cross", "d1", "history_only")["point"]
    aware = pair_value(d, "cross", "d1", "source_ridge_10")["point"]
    if not ceiling["point"] - aware > aware - hist > 0:
        raise ClaimError("'most of the remaining gap stays open' is false")
    primary = get(d["flex"], "licensed/primary")
    if "does no better than one number per league" not in primary:
        raise ClaimError("the registered sentence on richer models changed")
    names = join_names(
        [
            OUTCOME_NAMES[o].replace("/36", "").replace("Points", "points")
            for o in ("O2", "O3", "O4")
        ]
    )
    return {
        "e3_sentence": (
            f"On each of the {OLDER_WORDS[k]} other outcomes ({names}) translation gains over history, and the upper bound of "
            "what it adds to the league-aware forecast stays below 2% of error (Appendix B)."
        ),
        "e5_sentence": (
            f"Season by season, translation's gain over history is positive in {gain['positive_seasons']} of "
            f"{gain['n_seasons']} seasons, and the league-aware forecast is ahead of history plus translation in "
            f"{head['positive_seasons']} of {head['n_seasons']}; these are point estimates, described and not tested."
        ),
        "flex_primary": primary,
        # the registered sentence without its full stop, so that its limit can stand in the same sentence
        "flex_clause": primary.rstrip("."),
        "x_ceiling": pct(ceiling["point"]),
        "x_ceiling_lo": pct(ceiling["ci95"][0]),
        "x_ceiling_hi": pct(ceiling["ci95"][1]),
        "inc10_mde": num(
            get(
                r,
                "results/A/R1/ladder/source_ridge_10->source_ridge_10_scheduled/player_club_season/detectable_80",
            )
        ),
    }


# ---------------------------------------------------------------- E28 (Amendments 9 and 10)
E28_AGAINST = {
    "G_H": "history alone",
    "G_D": "the forecast that knows only the destination",
}
E28_LABEL = {
    "G_H": "History alone minus league-aware",
    "G_D": "History + destination minus league-aware",
}
E28_WEIGHTS = (
    ("unweighted", "Unweighted"),
    ("minutes_weighted", "Weighted by minutes"),
)
E28_READINGS = {
    "above_zero": "above zero",
    "includes_zero": "includes zero",
    "below_zero": "below zero",
}


def e28(d) -> dict:
    """The E28 summary, after the checks every E28 sentence relies on."""
    a, o = d["amend9"], older(d)
    if a.get("exploratory") is not True:
        raise ClaimError("E28 is exploratory; its summary must say so")
    for name, gate in a["gates"].items():
        if (
            gate["status"] != "passed"
            or gate["negative_control"] != "rejected as required"
        ):
            raise ClaimError(f"E28 gate {name} did not pass; E28 may not be printed")
    b = a["e28b"]
    if (
        b["acb_written_permission"] is not o["acb_written_permission"]
        or b["version"] != o["printed_version"]
        or b["printed_version"] != o["printed_version"]
        or sorted(b["leagues"]) != sorted(o["leagues"])
    ):
        raise ClaimError(
            "the E28 summary was made for another version of the older-seasons test; "
            "re-run it, and keep the readings without ACB in the main text (Amendment 10)"
        )
    for block in (a["e28a"], b):
        for name in E28_AGAINST:
            for weighting, _ in E28_WEIGHTS:
                c = block["contrasts"][name][weighting]
                low, high = c["ci95"]
                reading = (
                    "above_zero"
                    if low > 0
                    else "below_zero"
                    if high < 0
                    else "includes_zero"
                )
                if c["status"] != "ok" or c["reading"] != reading:
                    raise ClaimError(
                        f"E28 {name} {weighting}: reading and interval disagree"
                    )
    return a


def e28_span(c: dict) -> str:
    return f"interval {num(c['ci95'][0])} to {num(c['ci95'][1])}"


def e28_cell(c: dict) -> str:
    return f"{num(c['difference'], sign=True)} {interval(c['ci95'])}"


def e28_674(d) -> dict:
    """The sentences Amendment 9 registers for the 674, chosen by each interval."""
    a = e28(d)
    c = a["e28a"]["contrasts"]
    g_h, g_d = c["G_H"]["unweighted"], c["G_D"]["unweighted"]
    if g_h["reading"] == "above_zero":
        s_h = (
            "the league-aware forecast is more accurate than history alone by "
            f"{num(g_h['difference'])} EFF/36 ({e28_span(g_h)})"
        )
    elif g_h["reading"] == "includes_zero":
        s_h = "the league-aware forecast is not distinguishable from history alone at this n"
    else:
        raise ClaimError(
            "E28: the league-aware forecast lost to history alone; this goes to Amir first"
        )
    if g_d["reading"] != "above_zero":
        raise ClaimError(
            "E28: the source league's contribution is not above zero on the 674; "
            "this qualifies the headline and goes to Amir first (Amendment 9)"
        )
    s_d = (
        "once the destination is known, knowing the source league improves the forecast by "
        f"{num(g_d['difference'])} EFF/36 ({e28_span(g_d)})"
    )
    parts = []
    for name, label in (
        ("G_H", "against history alone"),
        ("G_D", "against the destination-only forecast"),
    ):
        w = c[name]["minutes_weighted"]
        if w["reading"] == "above_zero":
            parts.append(f"{num(w['difference'])} {label} ({e28_span(w)})")
        elif w["reading"] == "includes_zero":
            parts.append(
                f"{label} it is not clearly above zero when weighted by playing time "
                f"({num(w['difference'], sign=True)}, {e28_span(w)})"
            )
        else:
            raise ClaimError(
                f"E28 {name}: the weighted gain is below zero on the 674; this goes to Amir first"
            )
    weighted = "Weighted by playing time the gain is " + " and ".join(parts) + "."
    e = a["e28c"]
    share = f"{round(100 * e['margin_share_of_g_d'])}%"
    margin = f"the margin is {share} of what the source league adds"
    if e["g_d_reading"] != "above_zero":
        raise ClaimError(
            "E28c: the margin cannot be scaled against a gain that is not above zero"
        )
    return {
        # Amendment 16, rule 4: the abstract states this gain in words; its estimate stays in Results
        "e28_abs_gain": "Once the destination is known, knowing the source league improves the forecast",
        "e28_gh_sentence": s_h,
        "e28_gd_sentence": s_d,
        "e28_weighted_sentence": weighted,
        "e28c_sentence": margin,
        "e28_gd": num(g_d["difference"]),
    }


def e28_older_sentence(name: str, weighting: str, c: dict) -> str:
    """One older-seasons reading in the words of Amendments 9 and 10."""
    against, value = (
        E28_AGAINST[name],
        f"{num(c['difference'], sign=True)}, {e28_span(c)}",
    )
    weighted = weighting == "minutes_weighted"
    if c["reading"] == "above_zero":
        if weighted:
            return f"weighted by playing time the gain holds also on the older seasons ({value})"
        return f"against {against} the gain holds also on the older seasons ({value})"
    if c["reading"] == "includes_zero":
        if weighted:
            return (
                f"it is not clearly above zero when weighted by playing time ({value})"
            )
        return (
            f"against {against} the gain is not detectable on the older seasons at this n "
            f"({value}; n = {c['n']})"
        )
    less = (
        f"the league-aware forecast was less accurate than {against} by "
        f"{num(-c['difference'])} EFF/36 ({e28_span(c)})"
    )
    return f"weighted by playing time, {less}" if weighted else less


def e28_older(d) -> dict:
    """The older-seasons readings of E28 and the clauses that summarise them."""
    a, o = e28(d), older(d)
    c = a["e28b"]["contrasts"]
    readings = {(n, w): c[n][w]["reading"] for n in E28_AGAINST for w, _ in E28_WEIGHTS}
    worse = c["G_D"]["minutes_weighted"]
    if "above_zero" in readings.values() or worse["reading"] != "below_zero":
        raise ClaimError(
            "E28: the older-seasons readings are no longer 'did not help, and worse when "
            "weighted'; rewrite the abstract, Limitations and conclusion clauses with Amir"
        )
    if any(
        r == "below_zero"
        for k, r in readings.items()
        if k != ("G_D", "minutes_weighted")
    ):
        raise ClaimError(
            "E28: another older-seasons reading is below zero; rewrite the summary with Amir"
        )
    leagues, count = older_leagues(o, counts=False), OLDER_WORDS[len(o["leagues"])]

    def pair(name):
        first, second = (
            e28_older_sentence(name, w, c[name][w]) for w, _ in E28_WEIGHTS
        )
        return first[0].upper() + first[1:] + "; " + second + "."

    block = (
        "**The league numbers on these arrivals.** A further comparison, added after the first scoring, sets the "
        f"league-aware forecast against the two plainer forecasts on these {o['n']} arrivals [@amend9]. "
        f"{pair('G_H')} {pair('G_D')} In plain words, on these arrivals the league table did not help, and weighted "
        "by playing time it did worse than knowing the destination alone. This is a second reading of outcomes that "
        "had been read once, and it is exploratory; the wording for the last result was fixed after it was seen "
        "[@amend10]."
    )
    return {
        "e28_older_block": block,
        "e28_abs_older": f"on {o['n']} older arrivals from {count} leagues it did not",
        # (the introduction names what it did not do: there the clause follows the size of the gain)
        "e28_intro_older": f"on {o['n']} older arrivals from {count} leagues it did not improve the forecast",
        "e28_limits": (
            "**Carry-over.** The gain from the league table on arrivals of 2020–2025 did not carry back to the "
            f"{o['n']} arrivals of 2008–09 to 2015–16 from {leagues}."
        ),
        "e28_conclusion": (
            f"on {o['n']} older arrivals from {count} leagues it did not, so the league numbers are not shown "
            "to hold across periods"
        ),
    }


def table_e28_older(d) -> str:
    a = e28(d)
    b = a["e28b"]
    rows = []
    for name in E28_AGAINST:
        for weighting, label in E28_WEIGHTS:
            c = b["contrasts"][name][weighting]
            rows.append(
                [
                    E28_LABEL[name],
                    label,
                    f"{c['n']}",
                    num(c["mae_left"]),
                    num(c["mae_right"]),
                    num(c["difference"], sign=True),
                    interval(c["ci95"]),
                    num(c["detectable_80"]),
                    E28_READINGS[c["reading"]],
                ]
            )
    return (
        "Table A16. The league-aware forecast against the two plainer forecasts on the older arrivals (E28, "
        "exploratory; a second reading of outcomes read once). Differences in MAE, EFF/36; positive favours the "
        "league-aware forecast; 95% intervals clustered by player and destination club-season. *Detectable*: the "
        "smallest difference this sample could detect with 80% power.\n\n"
        + md_table(
            [
                "Difference in MAE",
                "Weighting",
                "n",
                "MAE, first forecast",
                "MAE, league-aware",
                "Difference",
                "95% interval",
                "Detectable",
                "Reading",
            ],
            rows,
        )
    )


def table_e28_674(d) -> str:
    a = e28(d)["e28a"]
    scopes = [("All arrivals", a["contrasts"])]
    scopes += [
        (
            f"{'EuroLeague' if k == 'euroleague' else 'EuroCup'} arrivals only",
            a["by_destination"][k],
        )
        for k in ("euroleague", "eurocup")
    ]
    scopes += [
        (f"Destination season {s}–{str(int(s) + 1)[2:]}", a["by_season"][s])
        for s in sorted(a["by_season"])
    ]
    rows = []
    for label, block in scopes:
        cells = [
            f"{e28_cell(block[n][w])}; {num(block[n][w]['detectable_80'])}"
            for n in E28_AGAINST
            for w, _ in E28_WEIGHTS
        ]
        rows.append([label, f"{block['G_H']['unweighted']['n']}", *cells])
    return (
        "Table A19. The league-aware forecast against the two plainer forecasts on the benchmark arrivals of 2020–2025 (E28, "
        "exploratory). Each cell: difference in MAE, EFF/36 (positive favours the league-aware forecast), its 95% "
        "interval clustered by player and destination club-season, and after the semicolon the smallest difference "
        "that subset could detect with 80% power. Only the first row carries registered wording; the subsets are "
        "small and are shown for transparency.\n\n"
        + md_table(
            [
                "Arrivals",
                "n",
                "vs history alone",
                "vs history alone, weighted by minutes",
                "vs destination-only",
                "vs destination-only, weighted by minutes",
            ],
            rows,
        )
    )


# ---------------------------------------------------------------- E29 (Amendment 11)
E29_MEANS = ("move", "error_without_table", "error_with_table")
E29_MINUS = re.compile(r"(?<![\w.])-(?=\d)")


def e29(d) -> dict:
    """The E29 summary, after the checks every E29 sentence relies on."""
    a, o = d["amend11"], older(d)
    if a.get("descriptive") is not True:
        raise ClaimError("E29 is descriptive; its summary must say so")
    for name, gate in a["gates"].items():
        if (
            gate["status"] != "passed"
            or gate["negative_control"] != "rejected as required"
        ):
            raise ClaimError(f"E29 gate {name} did not pass; E29 may not be printed")
    if (
        a["acb_written_permission"] is not o["acb_written_permission"]
        or a["printed_version"] != o["printed_version"]
        or set(a["leagues"]) != set(o["leagues"])
        or set(a["e29a"]["rows"]) != {*o["leagues"], "all"}
        or set(a["e29b"]["rows"]) != {*o["leagues"], "all"}
        or set(a["e29c"]["rows"]) != set(o["leagues"])
    ):
        raise ClaimError(
            "the E29 summary was made for another version of the older-seasons test; re-run it"
        )
    return a


def e29_text(sentence: str) -> str:
    """A generator sentence with the paper's minus sign."""
    return E29_MINUS.sub("−", sentence)


def e29_cell(c: dict) -> str:
    return f"{num(c['mean'], 2, sign=True)} {interval(c['ci95'], 2)}"


def e29_league_sentence(a: dict, key: str, weighting: str) -> str:
    """Amendment 11's sentence for one league on the older arrivals, from the committed means."""
    means = a["e29a"]["rows"][key]["means"]
    move, without, with_ = (means[m][weighting] for m in E29_MEANS)

    def side(c):
        return "below" if c["mean"] < 0 else "above"

    def value(c):
        return f"{num(abs(c['mean']), 2)}{{unit}} (interval {num(c['ci95'][0], 2)} to {num(c['ci95'][1], 2)})"

    verb = "lowered" if move["mean"] < 0 else "raised"
    tail = "" if side(with_) == side(without) else f" {side(with_)}"
    return (
        f"on the older arrivals the league table {verb} the forecast for arrivals from {a['leagues'][key]} by "
        f"{num(abs(move['mean']), 2)} EFF/36; without the table the forecast was "
        f"{value(without).format(unit=' EFF/36')} {side(without)} what they delivered, and with it "
        f"{value(with_).format(unit='')}{tail}"
    )


def e29_change_sentence(a: dict, key: str, weighting: str) -> str:
    """Amendment 11's sentence for the change between periods; only the null reading is wired."""
    c = a["e29c"]["rows"][key][weighting]
    low, high = c["ci95"]
    if c["reading"] != "includes_zero" or not low <= 0 <= high:
        raise ClaimError(
            "E29: a change between periods excludes zero; the wording changes and goes to Amir first"
        )
    return (
        f"for arrivals from {a['leagues'][key]} the change between the two periods is not distinguishable from "
        f"zero at this n ({num(c['change'], 2, sign=True)} EFF/36, interval {num(low, 2)} to {num(high, 2)})"
    )


def e29_main(d) -> dict:
    """The one main-text sentence of Amendment 11, with the caveat that travels with it."""
    a = e29(d)
    lic = a["licences"]
    met = lic["consistent_with"]
    if met["condition_met"]:
        raise ClaimError(
            "E29: a change between periods excludes zero; the wording changes and goes to Amir first"
        )
    for key in a["leagues"]:
        e29_change_sentence(a, key, "unweighted")
    if (
        met["registered_wording"]
        != "the table shows where the forecast missed and not why"
    ):
        raise ClaimError("E29: the registered fallback wording changed")
    # the league with the most older arrivals carries the main-text sentence; every league is in Table A17
    lead = max(a["leagues"], key=lambda k: a["e29a"]["rows"][k]["n"])
    sentence = e29_league_sentence(a, lead, "unweighted")
    caveat = lic["caveat"]
    if not caveat.startswith(
        "this shows where the forecast missed; it cannot separate"
    ):
        raise ClaimError("E29: the caveat is not the registered one")
    count = OLDER_WORDS[len(a["leagues"])]
    either = (
        "either league" if len(a["leagues"]) == 2 else f"any of the {count} leagues"
    )
    return {
        "e29_main": (
            f"**Where the forecast missed.** {sentence[0].upper()}{sentence[1:]} [@amend11]. "
            f"{caveat[0].upper()}{caveat[1:]} (descriptive; Appendix Table A17)."
        ),
        "e29_change_note": (
            f"The change between the two periods is not distinguishable from zero for {either} at these n, "
            f"so {met['registered_wording']}."
        ),
    }


def table_e29(d) -> str:
    a = e29(d)
    lic = a["licences"]
    order = [k for k in OLDER_ORDER if k in a["leagues"]] + ["all"]
    rows = []
    for key in order:
        name = (
            "All arrivals"
            if key == "all"
            else a["leagues"][key][0].upper() + a["leagues"][key][1:]
        )
        for block, period in ((a["e29a"], "2008–2015"), (a["e29b"], "2020–2025")):
            r = block["rows"][key]
            for weighting, label in E28_WEIGHTS:
                rows.append(
                    [
                        name,
                        period,
                        label,
                        f"{r['n']}",
                        *[e29_cell(r["means"][m][weighting]) for m in E29_MEANS],
                    ]
                )
    changes = []
    for key in order[:-1]:
        c = a["e29c"]["rows"][key]["minutes_weighted"]
        changes.append(
            e29_change_sentence(a, key, "unweighted")
            + f" (weighted by minutes: {num(c['change'], 2, sign=True)}, interval {num(c['ci95'][0], 2)} to "
            f"{num(c['ci95'][1], 2)})"
        )
    change_text = "; ".join(changes)
    limits = " ".join(f"({i}) {text}" for i, text in enumerate(lic["limits"], 1))
    caveat = lic["caveat"]
    return (
        "Table A17. Where the league table missed (E29, descriptive; a further reading of outcomes already read). "
        "*Move*: the league-aware forecast minus the forecast that knows only the destination. *Error*: forecast "
        "minus outcome; below zero, the forecast was below what arrivals delivered. Means in EFF/36 with 95% "
        "intervals clustered by player and destination club-season.\n\n"
        + md_table(
            [
                "Source league",
                "Arrivals of",
                "Weighting",
                "n",
                "Move made by the league table",
                "Error without the table",
                "Error with the table",
            ],
            rows,
        )
        + "\n\nBetween the two periods the error without the table changed as follows (older arrivals minus arrivals "
        f"of 2020–2025): {change_text}. Three limits apply. {limits} "
        f"{caveat[0].upper()}{caveat[1:]}."
    )


# ---------------------------------------------------------------- figures
def figures(d, out: Path) -> dict:
    out.mkdir(parents=True, exist_ok=True)
    a3 = d["amend3"]
    if d.get("e30") is not None and d.get("e30_pairs"):
        code, _ = e30_lowest(d)
        fig1 = paper_figures.fig_equivalents_and_moves(
            d["exchange"],
            d["counts"],
            d["e30_pairs"],
            d["e30"],
            out,
            marked=(code, short_league(code)),
            notes=figure_1_notes(d),
        )
    else:
        fig1 = paper_figures.fig_equivalents(d["exchange"], d["counts"], out)
    frozen = (
        {
            # Amendment 25, rule 1: in the scored state only
            "fig_frozen_test": paper_figures.fig_frozen_test(
                p1_figure_rows(d),
                P1_FIGURE_BLOCKS,
                d["p1"]["n_scored"],
                out,
                P1_FIGURE_FILE,
            )
        }
        if p1_figure_printed(d)
        else {}
    )
    return {
        **frozen,
        "fig1": fig1,
        "fig_mechanism": paper_figures.fig_mechanism(d["recipes"], out),
        "fig_stability": paper_figures.fig_stability(
            d["refits"], d["exchange"], get(a3, "e19/summary"), out
        ),
        "fig_gap_guide": paper_figures.fig_gap_guide(get(a3, "e20"), out),
        "fig_bands": paper_figures.fig_bands(get(a3, "e22"), out),
        "fig_skills": paper_figures.fig_skills(d["retention"], out),
        "fig2": paper_figures.fig_avoidable(
            get(d["amend"], "e17/reducible/rows"), get(d["flex"], "reducible"), out
        ),
        "fig3": paper_figures.fig_decisions(d["pairs"], out),
        "fig4": paper_figures.fig_league_bias(
            get(d["amend4"], "e24/leagues"), out, league_order=equivalents_order(d)
        ),
        "figA1": paper_figures.fig_robustness(
            d["recipes"], d["robust"], RECIPE_NAMES, OUTCOME_NAMES, out
        ),
    }


# ---------------------------------------------------------------- render
PLACEHOLDER = re.compile(r"\{\{([A-Za-z0-9_:]+)\}\}")
CITATION = re.compile(r"\[(@[a-z0-9]+(?:;\s*@[a-z0-9]+)*)\]")
REPO_PATH = re.compile(r"(?<![\w/.])(?:docs|scripts|src|tests|data)/[\w./-]+")


def number_citations(text: str, references: dict | None = None):
    references = REFERENCES if references is None else references
    order = []

    def repl(match):
        keys = [k.strip()[1:] for k in match.group(1).split(";")]
        for k in keys:
            if k not in references:
                raise KeyError(f"unknown citation key: {k}")
            if k not in order:
                order.append(k)
        nums = sorted({order.index(k) + 1 for k in keys})
        runs, start = [], nums[0]
        for prev, cur in zip(nums, nums[1:] + [None]):
            if cur != prev + 1:
                runs.append(
                    str(start)
                    if start == prev
                    else (
                        f"{start}, {prev}" if prev == start + 1 else f"{start}–{prev}"
                    )
                )
                start = cur
        return "[" + ", ".join(runs) + "]"

    text = CITATION.sub(repl, text)
    refs = "\n\n".join(f"[{i}] {references[k]}" for i, k in enumerate(order, 1))
    return text, refs, order


def main_text(text: str) -> str:
    """Abstract through Data and code: everything before the references."""
    body = text.split("\n---\n", 2)[-1]
    return body.split("## References")[0]


#: What the public package does not carry, and why (docs/paper/ssac27/PUBLIC_CUT.md).
RELEASE_WITHHELD = (
    "Per-game files of the data providers, box scores from the league websites and birthdates {verb} "
    "redistributed (rights and personal data)."
)


def release_section(d) -> str:
    """Distinguish the released v10 cut from the full-paper package."""
    if d["release"].get("public_cut_updated") is True:
        availability = (
            f"The full-paper companion is available at {META['repo_url']}: the code, the per-season tables "
            "and the result summaries behind every number, with one command that recomputes the main "
            "comparisons and checks the other analyses by hash. "
            + RELEASE_WITHHELD.format(verb="are not")
        )
    else:
        availability = (
            f"The public companion at {META['repo_url']} contains only the earlier v10 cut. "
            "The full-paper package has not yet been released. It will be released with the paper: the code, "
            "the per-season tables and the result summaries behind every number, with one command that "
            "recomputes the main comparisons and checks the other analyses by hash. "
            + RELEASE_WITHHELD.format(verb="will not be")
        )
    if e30_case(d) != E30_NOT_RUN:
        availability += (
            " The full-paper reproduction command calculates the league-change slope, including the "
            "check without Spain, from counts and mean residuals for each direction of each league pair. "
            "It checks the saved player-bootstrap interval against the retained results. Repeating the "
            "bootstrap requires the player-level moves and stayer data to refit the comparison model."
        )
    return availability + (
        " The paper-number manifest verifies manuscript regeneration, input hashes and saved values. "
        "This checks saved outputs; it does not independently recompute analyses from raw inputs."
    )


def check_final(d) -> None:
    """Require a terminal P1 report and released full-paper companion."""
    reasons = []
    status = d["p1"]["status"] if d["p1"] else "pending"
    if status == "pending":
        reasons.append("the 2026-27 frozen test is not scored yet")
    elif status not in {"scored", "not_adjudicable", "inconclusive"}:
        reasons.append(f"unknown P1 status: {status}")
    if d["release"].get("public_cut_updated") is not True:
        reasons.append(
            "the public companion repository does not yet hold the full-paper cut"
        )
    if d.get("e30") is not None and not E30_SECONDARY_READY:
        reasons.append("the secondary results of E30 (S-a to S-f) are not printed yet")
    if reasons:
        raise SystemExit("--final refused: " + "; ".join(reasons))


DOCX_TEMPLATE = Path("scripts/templates/ssac27-word-template.docx")
DOCX_NAME = "ssac27-paper-47.docx"


def compose(d: dict, template: str) -> tuple[str, list]:
    """The manuscript text from loaded inputs: pure, no files written.

    The public companion re-runs this to check every number in the paper
    (scripts/sloan_fullpaper_number_manifest.py).
    """
    f = facts(d)
    case = e30_case(d)
    f["meta:title"] = title_for(case)
    f["eq_table"] = eq_table(d)
    references = dict(REFERENCES)
    blocks = {
        "table:ladder": table_ladder(d),
        "table:ladder_full": table_ladder(d, full=True),
        "table:checks": table_checks(d),
        "table:equivalents": table_equivalents(d),
        "table:equivalents_support": table_equivalents_support(d),
        "section:vignettes": VIGNETTE_BOX.replace(
            "{{table:vignettes}}", table_vignettes(d)
        ),
        "p1_section": p1_section(d),
        "p1_power_note": p1_power_note(d),
        "p1_summary": p1_summary(d),
        "release_section": release_section(d),
        # Amendment 23, rule 4: Related work, Appendix O and the note on the search follow the
        # record of prior work (gate G23d)
        **prior_work_blocks(d),
        "related_glazer": RELATED_GLAZER,
        **e30_blocks(d),
        **small_gain(d),
        "section:appendix": appendix(d),
        "table:gaps": table_gaps(d),
        "section:amend34": appendix_v3(d),
        "older_section": older_section(d),
        "older_limits": older_limits(d),
        "older_credit": older_credit(d),
        "section:older": appendix_older(d),
        "table:e28_older": table_e28_older(d),
        "table:e28_674": table_e28_674(d),
        **e28_674(d),
        **e28_older(d),
        "table:e29": table_e29(d),
        **e29_main(d),
        **club_tool(d),
        **weighted_level(d),
        **promoted(d),
        **both_periods(d),
        # Amendment 23, rule 3: where the forecasts run low, by competition (gate G23c)
        "lvl_by_competition": level_sentences(d),
    }
    # Amendment 26: the Limitations entry (rule 4), the two descriptive sentences (rules 10 and
    # 11) and the note in Appendix N
    blocks["p1_limits"] = p1_limits(d)
    blocks["gaps_grew"] = gaps_grew(d)["gaps_grew"]
    blocks["gain_size"] = gain_size(d)
    blocks["gain_share_clause"] = gain_share_clause(d)
    blocks["first_page_new"] = first_page_new(d)
    blocks["amend26_note"] = amend26_note(d)
    # Amendment 23, rule 5: E34, once its one retained run is committed (gate G34d)
    blocks.update(e34_blocks(d, blocks))
    blocks["amend23_note"] = amend23_note(
        d, scorecard="**Frozen forecast scorecard.**" in blocks["p1_power_note"]
    )
    # Amendment 24, rule 2: one sentence in Appendix N, in every status (gate G24b)
    blocks["amend24_note"] = " " + ORDER_OF_READING_NOTE
    # Amendment 28, rule 6: one sentence in Appendix N, in every state (gate G28c)
    blocks["amend28_note"] = "**Repairs of wording and drawing.** " + AMEND28_NOTE
    # Amendment 29, rule 6: one paragraph in Appendix N, in every state (gate G29b)
    blocks["amend29_note"] = f"{AMEND29_HEAD} {AMEND29_NOTE}"
    # Amendment 25: S2 where the paper promises it (rule 2), and the note in Appendix N
    blocks.update(p1_s2_blocks(d))
    blocks["amend25_note"] = amend25_note(d)
    text = template
    for key, value in blocks.items():
        text = text.replace("{{" + key + "}}", value)
    text = PLACEHOLDER.sub(
        lambda m: f[m.group(1)] if m.group(1) in f else m.group(0), text
    )
    missing = sorted(set(PLACEHOLDER.findall(text)) - {"section:references"})
    if missing:
        raise KeyError(f"unresolved placeholders: {missing}")
    for key, reference in {**OPTIONAL_REFERENCES, **prior_work_references(d)}.items():
        if re.search(rf"@{key}\b", text):
            references[key] = reference
    check_g19c(text, d, blocks, f)
    check_g34(text, d, blocks)
    text, refs, order = number_citations(text, references)
    text = text.replace("{{section:references}}", refs)
    if PLACEHOLDER.search(text) or "{{" in text:
        raise KeyError("unresolved placeholder after references")
    if unused := sorted(set(references) - set(order)):
        raise KeyError(f"references never cited: {unused}")
    if hits := REPO_PATH.findall(text):
        raise ClaimError(f"repo-relative paths in the paper: {hits[:5]}")
    if re.search(r"no better than a coin flip", text, re.IGNORECASE):
        raise ClaimError("use 'not distinguishable from a coin flip'")
    check_first_page(text, case, abstract_limit(d))
    check_g19b(text, d)
    check_g20(text, d)
    check_g21(text, d)
    check_g23(text, d)
    check_g24(text, d)
    check_g25(text, d)
    check_g26(text, d)
    check_g27(text, d)
    check_g28(text, d)
    check_g29(text, d)
    check_g32(text)
    check_examined(text, d)
    return text, order


#: A label that names appendix tables: "Table A5", "Tables A6–A7", "Tables A21 and A22".
TABLE_LABELS = re.compile(r"\bTables? A\d+(?:(?:–|, | and )A\d+)*")
#: The caption line of an appendix table.
TABLE_CAPTION = re.compile(r"^Table A(\d+)\.", re.M)


def table_numbers_in_order(text: str) -> dict:
    """Amendment 32: the printed number of each appendix table, by the order in which the tables
    stand. Keys are the numbers the registrations and the gates use (the numbers a table got when
    it was added); values are the numbers the paper prints."""
    order = [int(n) for n in TABLE_CAPTION.findall(text)]
    if len(order) != len(set(order)):
        raise ClaimError("two appendix tables carry one number")
    return {old: new for new, old in enumerate(order, 1)}


def printed(text: str) -> str:
    """The composed text as the paper prints it: the appendix tables numbered in the order in
    which they stand (Amendment 32). Only the numbers in table labels change. ``compose`` and its
    gates keep the numbers the registrations use; the manuscript, the Word file and the number
    manifest take the text from here."""
    numbers = table_numbers_in_order(text)

    def relabel(match):
        label = match.group(0)
        named = [int(n) for n in re.findall(r"A(\d+)", label)]
        if missing := [n for n in named if n not in numbers]:
            raise ClaimError(
                f"'{label}' names a table the appendix does not hold: {missing}"
            )
        new = [numbers[n] for n in named]
        # a range ("Tables A6–A7") must name the same tables after the numbering
        if "–" in label and new[-1] - new[0] != named[-1] - named[0]:
            raise ClaimError(
                f"'{label}' is not the same range once the tables are in order"
            )
        return re.sub(r"A(\d+)", lambda m: f"A{numbers[int(m.group(1))]}", label)

    out = TABLE_LABELS.sub(relabel, text)
    captions = [int(n) for n in TABLE_CAPTION.findall(out)]
    if captions != list(range(1, len(captions) + 1)):
        raise ClaimError(f"the appendix tables are not numbered in order: {captions}")
    if out.count("\n") != text.count("\n") or len(out.split()) != len(text.split()):
        raise ClaimError(
            "numbering the tables in order changed more than table numbers"
        )
    return out


def render(
    root: Path,
    out: Path,
    *,
    final: bool = False,
    docx: bool = False,
    pandoc: str = "pandoc",
) -> dict:
    d = load(root)
    if final:
        check_final(d)
    text, order = compose(d, (root / TEMPLATE).read_text())
    text = printed(text)
    out.mkdir(parents=True, exist_ok=True)
    # figures first: if one cannot be drawn, no manuscript that embeds it is left in the folder
    figs = figures(d, out / "figures")
    (out / "manuscript.md").write_text(text)
    words = len(main_text(text).split())
    abstract = text.split("## Abstract")[1].split("\n## ")[0]
    manifest = {
        "e30_case": e30_case(d),
        "title": title_for(e30_case(d)),
        "abstract_numbers": {
            **abstract_numbers(abstract),
            "limit": abstract_limit(d),
            "rule": "Amendment 17: an estimate, a count or a league-rate value; an interval "
            "counts with its estimate; dates, season labels and the unit do not count",
        },
        "figures_main_text": len(
            re.findall(r"^!\[Figure \d+\.", main_text(text), re.M)
        ),
        "inputs": {
            str(p): sha(root / p)
            for p in [*SOURCES.values(), *TABLES.values(), *TEXTS.values(), TEMPLATE]
        },
        "p1_scored": d["p1"] is not None and d["p1"]["status"] == "scored",
        "p1_status": d["p1"]["status"] if d["p1"] else "pending",
        "references": order,
        "outputs": {
            "manuscript.md": sha(out / "manuscript.md"),
            **{k: sha(v) for k, v in figs.items()},
        },
        "words_main_text": words,
    }
    if p := p1_file(root):
        manifest["inputs"][str(p)] = sha(root / p)
    for path in optional_inputs(root).values():
        manifest["inputs"][str(path)] = sha(root / path)
    if docx:
        from build_sloan_fullpaper_docx import build

        info = build(
            out / "manuscript.md", root / DOCX_TEMPLATE, out / DOCX_NAME, pandoc
        )
        manifest["inputs"][str(DOCX_TEMPLATE)] = sha(root / DOCX_TEMPLATE)
        manifest["outputs"][DOCX_NAME] = info["sha256"]
        manifest["docx"] = {
            k: info[k] for k in ("pandoc", "equations", "figures", "tables")
        }
    (out / "render-manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    )
    return manifest


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument(
        "--root",
        type=Path,
        default=Path.cwd(),
        help="tree holding the committed inputs (default: current directory)",
    )
    parser.add_argument("--final", action="store_true")
    parser.add_argument(
        "--docx",
        action="store_true",
        help="also build the Word file from the conference template",
    )
    parser.add_argument(
        "--pandoc",
        default="pandoc",
        help="pandoc executable used for the OMML equations",
    )
    args = parser.parse_args(argv)
    manifest = render(
        args.root, args.out, final=args.final, docx=args.docx, pandoc=args.pandoc
    )
    print(json.dumps({k: manifest[k] for k in ("p1_status", "words_main_text")}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
