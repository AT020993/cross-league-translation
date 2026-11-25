#!/usr/bin/env python3
"""Score your own league adjustment on the paper's 674 arrivals.

    python scripts/sloan_fullpaper_score_league_table.py --table my_leagues.csv --out my_score

``my_leagues.csv`` needs two columns, ``league`` and ``score``: one number for
each of the ten source leagues (keys below). Any scale works, higher or lower:
the number enters through one fitted coefficient, so only its pattern across
leagues matters.

    aba-league, france-pro-a, germany-bbl, greece-a1, israel-bsl,
    italy-lba, lithuania-lkl, spain-acb, turkey-bsl, vtb

What it does is exactly the rule the paper registered for a published league
table (Amendment 15, E31a), applied to your numbers:

1. It rebuilds the paper's forecasts from the published player-season tables
   and checks that the registered errors come out (the destination-only and
   the league-aware forecast). If they do not, it stops.
2. Your forecast is the registered destination-aware forecast plus one
   coefficient times your number for the player's source league. The
   coefficient is fitted without penalty, for each destination season on the
   arrivals of earlier seasons only.
3. It reports your forecast's mean absolute error (EFF/36) on the 674 arrivals
   of 2020-2025, and two paired differences with the registered two-way
   clustered 95% interval and the 80%-power detectable difference, unweighted
   and weighted by destination minutes: against the forecast that knows only
   the destination, and against the paper's league-aware forecast.
4. As a check on your numbers it repeats step 2 with your numbers shuffled
   across leagues. That difference should include zero.

Read the result with care. The outcomes of 2020-2025 are public, so a league
table built with those seasons has already seen them. Every score from this
script is exploratory. An interval that includes zero does not show that two
tables are the same; the detectable difference printed beside it says how
large a difference these 674 arrivals could have found.
"""

# ruff: noqa: E501, E741 -- messages; O is the offsets arm
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys

for _name in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_name, "1")
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from scripts import sloan_fullpaper_common as common  # noqa: E402
from scripts import sloan_fullpaper_decisions as dec  # noqa: E402
from scripts import sloan_fullpaper_published_tables as pt  # noqa: E402
from scripts.translation_research_common import sha256_file  # noqa: E402

D, O = pt.D, pt.O
YOURS = "your_table"
YOURS_SHUFFLED = "your_table_shuffled"
CONTRASTS = {
    "yours_against_destination_only": (D, YOURS),
    "league_aware_against_yours": (YOURS, O),
}
POSITIVE_MEANS = {
    "yours_against_destination_only": "positive: your numbers lower the error of the destination-only forecast",
    "league_aware_against_yours": "positive: your forecast has the larger error than the paper's league-aware forecast",
}
CAUTION = (
    "Exploratory. The outcomes of 2020-2025 are public: a league table built with those seasons has seen them. "
    "An interval that includes zero does not show that two tables are the same."
)


def input_dir(explicit: Path | None = None) -> Path:
    """The published pool-A tables: next to this section in the public repository."""
    candidates = (
        [explicit]
        if explicit
        else [
            ROOT.parent / "ssac27-v10/data",
            ROOT / common.INPUT_DIR,
        ]
    )
    for path in candidates:
        if path and (Path(path) / "official_corrected/pairs.parquet").is_file():
            return Path(path)
    raise SystemExit(
        "player-season tables not found; pass --input-dir (the folder that holds official_corrected/)"
    )


def load_scores(path: Path) -> dict:
    """One finite number per source league; other rows are ignored and listed."""
    frame = pd.read_csv(path)
    if not {"league", "score"} <= set(frame.columns):
        raise SystemExit(f"{path}: needs the columns 'league' and 'score'")
    frame = frame.assign(league=frame.league.astype(str).str.strip())
    if frame.league.duplicated().any():
        raise SystemExit(f"{path}: a league appears twice")
    values = pd.to_numeric(frame.score, errors="coerce")
    scores = dict(zip(frame.league, values.astype(float)))
    missing = [
        k for k in pt.SOURCE_LEAGUES if k not in scores or not np.isfinite(scores[k])
    ]
    if missing:
        raise SystemExit(
            f"{path}: no number for {missing}; the ten keys are {list(pt.SOURCE_LEAGUES)}"
        )
    if len({scores[k] for k in pt.SOURCE_LEAGUES}) < 2:
        raise SystemExit(
            f"{path}: every league has the same number, so there is nothing to score"
        )
    return {k: scores[k] for k in pt.SOURCE_LEAGUES}


def score(root: Path, inputs: Path, table: Path, out: Path | None = None) -> dict:
    root = Path(root)
    scores = load_scores(table)
    relative, expected = pt.RECIPES_SUMMARY
    common.check_sha(root / relative, expected)
    recipes_summary = json.loads((root / relative).read_text())
    rows, features, _ = common.anchor_rows(root, inputs)
    dec.assert_scope(rows)
    reproduced, _ = pt.walk_forward(features, None, name="reproduced")
    worst = pt.g31a_differences(rows, recipes_summary, reproduced)
    pt.gate_max("the paper's registered errors", worst, pt.REPRO_TOLERANCE)

    forecast, folds = pt.walk_forward(features, scores, name=YOURS)
    rows = pt.attach(rows, forecast, YOURS)
    blocks = pt.contrasts(rows, CONTRASTS)
    shuffle = pt.shuffled_scores(scores)
    shuffled_forecast, _ = pt.walk_forward(features, shuffle, name=YOURS_SHUFFLED)
    shuffled = pt.contrasts(
        pt.attach(rows, shuffled_forecast, YOURS_SHUFFLED),
        {"shuffled": (D, YOURS_SHUFFLED)},
    )["shuffled"]
    result = {
        "what": "A league table scored by the registered rule of Amendment 15 (E31a) on the paper's 674 arrivals",
        "caution": CAUTION,
        "table_file": str(table),
        "table_sha256": sha256_file(table),
        "scores_used": scores,
        "n": int(len(rows)),
        "paper_errors_reproduced": {
            "largest_difference": max(worst.values()),
            "tolerance": pt.REPRO_TOLERANCE,
        },
        "mae": pt.arm_errors(rows, (D, YOURS, O)),
        "contrasts": blocks,
        "positive_means": POSITIVE_MEANS,
        "coefficient_by_destination_season": [
            {
                k: fold.get(k)
                for k in ("season", "train_n", "test_n", "status", "score_coefficient")
            }
            for fold in folds
        ],
        "shuffled_check": {
            "what": "your numbers permuted so that no league keeps its own; the difference from the destination-only forecast should include zero",
            "seed": pt.SHUFFLE_SEED,
            **{
                w: {k: shuffled[w][k] for k in ("difference", "ci95", "reading")}
                for w in pt.WEIGHTINGS
            },
        },
    }
    if out is not None:
        out = Path(out)
        out.mkdir(parents=True, exist_ok=False)
        (out / "score.json").write_text(
            json.dumps(pt.clean(result), indent=2, sort_keys=True) + "\n"
        )
        pd.DataFrame(
            [
                {**row, "positive_means": POSITIVE_MEANS[row["difference_name"]]}
                for row in pt.e28.flat("the 674 arrivals of 2020-2025", blocks)
            ]
        ).to_csv(out / "differences.csv", index=False)
        rows[
            [*pt.KEY, "league_dest", "league_src", pt.WEIGHT, pt.OUTCOME, D, O, YOURS]
        ].sort_values(pt.KEY).to_csv(out / "keyed_forecasts.csv", index=False)
    return result


def describe(result: dict) -> str:
    """The result in plain lines."""
    lines = [
        f"Scored on {result['n']} arrivals of 2020-2025 (EFF/36, mean absolute error; lower is better).",
        "",
        f"{'forecast':<44}{'unweighted':>12}{'by minutes':>12}",
    ]
    names = {
        D: "knows the destination only",
        YOURS: "destination + your league numbers",
        O: "the paper's league-aware forecast",
    }
    for arm, name in names.items():
        lines.append(
            f"{name:<44}{result['mae'][arm]['unweighted']:>12.3f}{result['mae'][arm]['minutes_weighted']:>12.3f}"
        )
    lines.append("")
    for name, block in result["contrasts"].items():
        lines.append(POSITIVE_MEANS[name])
        for w in pt.WEIGHTINGS:
            r = block[w]
            lines.append(
                f"  {w:<17} {r['difference']:+.3f}  (95% interval {r['ci95'][0]:+.3f} to {r['ci95'][1]:+.3f}; "
                f"{r['reading'].replace('_', ' ')}; detectable with 80% power: {r['detectable_80']:.3f})"
            )
    check = result["shuffled_check"]
    lines += [
        "",
        "Check, your numbers shuffled across leagues (should include zero): "
        + "; ".join(
            f"{w} {check[w]['difference']:+.3f} ({check[w]['reading'].replace('_', ' ')})"
            for w in pt.WEIGHTINGS
        ),
        "",
        result["caution"],
    ]
    return "\n".join(lines)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--table", type=Path, required=True, help="CSV with columns league, score"
    )
    parser.add_argument(
        "--input-dir",
        type=Path,
        help="folder holding official_corrected/ (default: the published tables)",
    )
    parser.add_argument(
        "--out",
        type=Path,
        help="new folder for score.json, differences.csv and keyed_forecasts.csv",
    )
    args = parser.parse_args(argv)
    result = score(ROOT, input_dir(args.input_dir), args.table, args.out)
    print(describe(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
