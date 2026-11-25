#!/usr/bin/env python3
"""SSAC27 E27: what the paper may print of the older-seasons test (Amendment 7).

Amendment 7 fixed, before any result existed, which version the paper prints: all
three leagues only if ACB's written permission has arrived by the analysis lock,
otherwise the version without ACB plus one sentence about the withheld one. This
script applies that rule. It reads the committed E27 outputs and
``docs/paper/ssac27/release.json`` and writes

* ``e27_paper.json``: the printed version's numbers, copied from the scoring run's
  outputs, and nothing else that depends on the leagues left out;
* ``e27_arrivals_printed.csv``: one row per printed arrival, with the columns the
  three comparisons need.

Nothing is estimated here that the scoring run did not write. The printed rows are
re-scored only to check that they reproduce the committed numbers (gate G27p).
The paper's renderer and the public companion read these two files; the full E27
folder stays out of the public cut.
"""

from __future__ import annotations

if __name__ == "__main__":
    import sys as _sys
    from pathlib import Path as _Path

    _sys.path.insert(0, str(_Path(__file__).resolve().parents[1]))
    from src.research.execution import enter as _enter

    _enter(__file__)

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd  # noqa: E402

from scripts import sloan_fullpaper_arrivals_audit as e26  # noqa: E402
from scripts import sloan_fullpaper_common as common  # noqa: E402
from scripts import sloan_fullpaper_older_seasons as e27  # noqa: E402
from scripts.translation_research_common import sha256_file  # noqa: E402

ARTIFACTS = Path("docs/research/artifacts/sloan-fullpaper-older-seasons-2026-11")
OUT = Path("docs/research/artifacts/sloan-fullpaper-older-seasons-paper-2026-11")
RELEASE = Path("docs/paper/ssac27/release.json")
FLAG = "acb_written_permission"
WITHHELD_LEAGUE = "acb"
SOURCE_FILES = (
    "e27_summary.json",
    "e27_comparisons.csv",
    "e27_arrivals.csv",
    "e27_freeze.json",
    "freeze-receipt.json",
    "score-stopped-receipt.json",
    "score-receipt.json",
)
ARMS = list(common.PRIMARY_ARMS.values())
#: Columns of the printed arrivals table: keys, the season aggregates behind each
#: forecast, the four forecasts and the outcome. No game row and no date.
COLUMNS = [
    "player_name",
    "printed_name",
    "league",
    "true_season_src",
    "club_src",
    "games_src",
    "minutes_src",
    "pir_per36_src",
    "prior_mean_pir36",
    "history_seasons",
    "rare_surname",
    "league_dest",
    "true_season_dest",
    "season_dest",
    "club_dest",
    "cluster",
    "club_confirmed",
    "games_dest",
    "minutes_dest",
    "pir_per36_dest",
    *ARMS,
]
TOLERANCE = 1e-12
SEED = 20261113


class GateFailure(RuntimeError):
    pass


def printed_version(release: dict) -> str:
    """Amendment 7, "Two versions, and which one is printed"."""
    if release.get(FLAG) not in (True, False):
        raise GateFailure(f"release.json must say {FLAG}: true or false")
    return "V-all" if release[FLAG] else "V-noACB"


def records(table: pd.DataFrame, version: str) -> dict:
    """subset -> comparison -> the committed record."""
    out: dict = {}
    for row in table.loc[table.version.eq(version)].itertuples():
        estimable = pd.notna(row.difference)
        out.setdefault(row.subset, {})[row.comparison] = {
            "n": int(row.n),
            "difference": float(row.difference) if estimable else None,
            "ci95": [float(row.ci_low), float(row.ci_high)] if estimable else None,
            "margin": float(row.margin) if estimable else None,
            "reading": row.reading,
        }
    return out


def agreement(summary: dict) -> dict:
    """Do the two versions give the same reading? Counted per registered comparison."""
    both = summary["primary"]
    same = [
        name
        for name in e26.COMPARISONS
        if both["V-all"][name]["reading"] == both["V-noACB"][name]["reading"]
    ]
    return {
        "comparisons": len(e26.COMPARISONS),
        "readings_agree": len(same),
        "agree_on": same,
    }


def reproduce_gate(rows: pd.DataFrame, printed: dict) -> dict:
    """G27p: the printed rows give the committed numbers of the printed version."""
    worst = 0.0
    subsets = {"all": rows, "rare surname": rows.loc[rows.rare_surname.astype(bool)]}
    for label, part in subsets.items():
        for got in e27.comparisons(part):
            ref = printed[label][got["comparison"]]
            if got["n"] != ref["n"] or got["reading"] != ref["reading"]:
                raise GateFailure(
                    f"G27p: {label}/{got['comparison']} does not reproduce"
                )
            gaps = [
                abs(got["difference"] - ref["difference"]),
                *(abs(a - b) for a, b in zip(got["ci95"], ref["ci95"], strict=True)),
                abs(got["margin"] - ref["margin"]),
            ]
            worst = max(worst, *gaps)
    if worst > TOLERANCE:
        raise GateFailure(
            f"G27p: printed rows differ from the scoring run by {worst:.2e}"
        )
    control = rows.assign(
        pir_per36_dest=rows.pir_per36_dest.sample(
            frac=1.0, random_state=SEED
        ).to_numpy()
    )
    shuffled = e27.comparisons(control)[0]
    if (
        abs(
            shuffled["difference"]
            - printed["all"][shuffled["comparison"]]["difference"]
        )
        <= TOLERANCE
    ):
        raise GateFailure(
            "G27p negative control: shuffled outcomes reproduced the result"
        )
    return {
        "status": "passed",
        "max_abs_gap": worst,
        "tolerance": TOLERANCE,
        "negative_control": "shuffled outcomes: rejected as required",
    }


def extract(artifacts: Path, release: dict) -> tuple[dict, pd.DataFrame]:
    summary = json.loads((artifacts / "e27_summary.json").read_text())
    freeze = json.loads((artifacts / "e27_freeze.json").read_text())
    table = pd.read_csv(artifacts / "e27_comparisons.csv")
    arrivals = pd.read_csv(artifacts / "e27_arrivals.csv", dtype={"player_name": str})
    receipts = {
        k: json.loads((artifacts / f"{k}-receipt.json").read_text())
        for k in ("freeze", "score-stopped", "score")
    }
    if summary["forecast_sha256"] != freeze["forecast_sha256"]:
        raise GateFailure("the scoring run did not read the frozen file")
    version = printed_version(release)
    leagues = e27.VERSIONS[version]
    if (WITHHELD_LEAGUE in leagues) != bool(release[FLAG]):
        raise GateFailure("the printed version does not follow the permission flag")
    printed = records(table, version)
    meta = summary["versions"][version]
    rows = arrivals.loc[arrivals.league.isin(leagues), COLUMNS].reset_index(drop=True)
    if len(rows) != meta["n"]:
        raise GateFailure("the printed rows are not the printed version's arrivals")
    gates = {
        **{k: {kk: vv for kk, vv in g.items()} for k, g in freeze["gates"].items()},
        **summary["gates"],
        "G27p_printed_rows_reproduce": reproduce_gate(rows, printed),
    }
    out = {
        "analysis": "E27 paper extract",
        "amendment_commit": summary["amendment_commit"],
        "amendment_sha256": summary["amendment_sha256"],
        "forecast_sha256": summary["forecast_sha256"],
        FLAG: bool(release[FLAG]),
        "printed_version": version,
        "leagues": sorted(leagues),
        "sources": {name: sha256_file(artifacts / name) for name in SOURCE_FILES},
        "runs": {
            "freeze": receipts["freeze"]["status"],
            "score_stopped": {
                "status": receipts["score-stopped"]["status"],
                "output_files": len(receipts["score-stopped"]["outputs"]),
            },
            "score": receipts["score"]["status"],
            "outcomes_joined_at_freeze": freeze["outcomes_joined"],
        },
        "gates": gates,
        "n": meta["n"],
        "by_league": {k: int(v) for k, v in meta["by_league"].items()},
        "by_destination": {k: int(v) for k, v in meta["by_destination"].items()},
        "by_season": {str(int(float(k))): int(v) for k, v in meta["by_season"].items()},
        "shares": {
            "without_history": meta["share_without_history"],
            "rare_surname": meta["share_rare_surname"],
            "club_confirmed": meta["share_club_confirmed"],
        },
        "mae": meta["mae"],
        "mean_error": meta["mean_error"],
        "comparisons": printed,
        "linking": {
            lg: {
                "league_games": freeze["by_league"][lg]["league_games"],
                "games_not_reconciled": freeze["by_league"][lg]["games_not_reconciled"],
                "source_player_seasons": freeze["by_league"][lg][
                    "source_player_seasons"
                ],
                "linked": freeze["by_league"][lg]["linked"],
                "first_name_differs": freeze["by_league"][lg]["link_status"][
                    "first name differs"
                ],
            }
            for lg in sorted(leagues)
        },
    }
    if release[FLAG]:
        other = "V-noACB"
        out["selection"] = summary["selection"]
        out["frozen_rows"] = freeze["rows"]
        out["without_acb"] = {
            "n": summary["versions"][other]["n"],
            "comparisons": records(table, other)["all"],
            "mean_error": summary["versions"][other]["mean_error"],
        }
    else:
        out["withheld"] = {
            "version": "V-all",
            "computed_in_the_same_runs": True,
            "reason": "ACB's written permission had not arrived",
            **agreement(summary),
        }
    return out, rows


def leak_check(out: dict, rows: pd.DataFrame) -> None:
    """Without permission, nothing from the withheld league may be written."""
    if out[FLAG]:
        return
    text = json.dumps(out)
    if f'"{WITHHELD_LEAGUE}"' in text or "league: " + WITHHELD_LEAGUE in text:
        raise GateFailure("the extract names the withheld league's results")
    if rows.league.eq(WITHHELD_LEAGUE).any():
        raise GateFailure("the printed rows include the withheld league")
    if any(k in out for k in ("selection", "frozen_rows", "without_acb")):
        raise GateFailure("the extract carries counts that include the withheld league")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--artifacts", type=Path, default=ARTIFACTS)
    parser.add_argument("--release", type=Path, default=RELEASE)
    parser.add_argument("--out", type=Path, default=OUT)
    args = parser.parse_args(argv)
    out, rows = extract(args.artifacts, json.loads(args.release.read_text()))
    leak_check(out, rows)
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "e27_paper.json").write_text(
        json.dumps(out, indent=2, sort_keys=True) + "\n"
    )
    rows.to_csv(args.out / "e27_arrivals_printed.csv", index=False)
    print(json.dumps({"printed_version": out["printed_version"], "n": out["n"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
