# What Does League Translation Add? A Benchmark for European Basketball Forecasts

Companion material for the SSAC 2027 research-paper abstract (basketball track, submitted
29 September 2026). Everything the abstract reports can be checked from the files here.

## Check the abstract in one command

```sh
python verify_abstract_numbers.py
```

The script needs only the Python 3.10+ standard library. It recomputes all 16 reported
quantities from `results/`, prints each value next to the text it supports, and exits with an
error if any value no longer matches `paper/abstract.md`.

## Contents

| Path | What it holds |
| --- | --- |
| `paper/abstract.md`, `paper/figures/` | The submitted abstract and its two figures |
| `paper/manuscript.md`, `paper/supplement.md` | Full manuscript and numerical supplement |
| `data/<pool>/pairs.parquet` | Factor-estimation pairs: one row per player-season observed in a domestic league and in EuroLeague or EuroCup in the same season |
| `data/<pool>/cohort.parquet` | The forecasting cohort for destination seasons 2016–2025: source-season and destination-season aggregates, history features and eligibility flags. Earlier seasons provide training history; the scored target (674 player-seasons, destination seasons 2020–2025) is defined in manuscript section 2 |
| `data/pair_flow.parquet` | How each of the 4,074 full-pool pairs moves through the verification and overlap filters |
| `results/` | Saved outputs behind every number: paired contrasts, intervals, support counts, the random-restriction diagnostic and the reliability-policy readback, plus a claim map from each abstract number to its field |
| `protocols/` | The pre-specified analysis plans for the slope comparison, the reliability policy and the restriction diagnostic |
| `code/` | The analysis and rendering code as run |

## Factor pools

The same 674 forecasts are scored in every comparison. Only the pairs used to estimate league
factors change.

| Pool | Pairs | Definition |
| --- | --- | --- |
| A. Full pool | 4,074 | All corrected same-season domestic-continental pairs |
| B. Verified; full-season rates | 1,537 | Pairs whose player identity, club and appearance dates are verified |
| C. Verified; overlap keys | 1,463 | B restricted to pairs eligible for the overlap-window analysis |
| D. Verified; overlap-window rates | 1,463 | C with rates recomputed over the overlapping appearance window |

## Data

All tables hold per-season aggregates, one row per player-season and competition. There are no
game-level rows or game dates. Domestic-league statistics come from **proballers.com**, and
EuroLeague and EuroCup statistics come from the **EuroLeague API**. Rights in the underlying data
remain with those sources. See `../DATA_TERMS.md` for the terms under which the derived tables
are shared.

## Reproduction scope

`results/` contains the saved outputs of the full analysis, and `verify_abstract_numbers.py`
checks the abstract against them. The code in `code/` is the analysis as run. A complete numerical
replay re-estimates every regression from 56 saved upstream factor refits (about 240 MB) and
refits 400 random restrictions (about 1.1 GB). Those intermediate files are not included here
because of their size, and are available on request.

## Scope of the findings

The seasons were inspected in earlier work, so every comparison is retrospective and
exploratory. The findings concern one translation recipe, the EFF/36 outcome and players who met
the appearance thresholds, a population that is EuroCup-heavy. They establish neither equivalence
nor general harm. Recruitment benefit remains untested.

Code is MIT-licensed (`../LICENSE`).
