#!/usr/bin/env python3
"""Amendment 15, E32: named 2026-27 newcomers with their frozen forecasts.

Pre-registration: docs/research/sloan-full-paper-preregistration-2026-11-03.md
(commit f52e7c831) and its Amendment 15,
docs/research/sloan-full-paper-preregistration-amendment-15-2026-11-17.md
(commit 48f752c68, pushed alone on 2026-11-17, before this file existed).

E32 computes no result. It prints forecasts that were frozen on 3 November
2026 for named players, chosen by rules that never look at how they played.

* Who: every newcomer the scorer counts, per competition, ordered by the
  frozen league-aware forecast. The table prints the ten highest and the ten
  lowest in each competition, with source league, last season's domestic rate,
  the destination-only forecast, the league-aware forecast and, in the last
  column, what he has produced so far. If fewer than 60 newcomers are scored,
  all of them are printed and the summary says so.
* The calls the table changes: among those newcomers, every pair in the same
  competition and from different source leagues whose order differs between
  the destination-only forecast and the league-aware forecast. All such pairs
  are written; the ten with the largest gap in the league-aware forecast are
  marked as printed, and the count of all such pairs is reported.

How the selection is kept blind to the outcome (gate G32). From the scorer's
rows the selection takes the newcomers' keys and nothing else. Every forecast
comes from the pinned frozen file, after its hash check. ``select`` refuses a
frame that carries any column other than the frozen ones. The outcome is
joined to the selected rows afterwards and cannot add, drop or reorder a row.
Negative control, run every time: the outcome columns are deleted from the
scorer's rows, and then replaced by their reverse, and the selected rows must
be the same.

No 2026-27 statistic is read by this file except through the scorer's
scored-rows output, and that only after the frozen test has been scored.
"""

# ruff: noqa: E501, E741 -- gate messages; O is the offsets arm
from __future__ import annotations

if __name__ == "__main__":
    import sys as _sys
    from pathlib import Path as _Path

    _sys.path.insert(0, str(_Path(__file__).resolve().parents[1]))
    from src.research.execution import enter as _enter

    _enter(__file__)

import argparse
import datetime as dt
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

from scripts import sloan_fullpaper_amend1_decisions as a1  # noqa: E402
from scripts import sloan_fullpaper_common as common  # noqa: E402
from scripts.translation_research_common import sha256_file  # noqa: E402

AMENDMENT = Path(
    "docs/research/sloan-full-paper-preregistration-amendment-15-2026-11-17.md"
)
AMENDMENT_COMMIT = "48f752c68487e7c426fbe9817052bcf51276de85"
FROZEN = Path(
    "docs/research/artifacts/sloan-fullpaper-p1-freeze-2026-11/p1_frozen_forecasts.parquet"
)
#: The pinned frozen file of 3 November (public hash list, row 2).
FROZEN_SHA = "f3530c1a5ac369c032a996756ced226a93aa2d9f71d2e63aab21694de3d55316"
D, O = "history_destination_slope", "source_ridge_10"
KEY = ["player_name", "league_dest"]
#: Everything the selection may see: the key, and columns frozen on 3 November.
FROZEN_COLUMNS = ("player_name", "league_dest", "league_src", "pir_per36_src", D, O)
#: What a newcomer has produced so far, as the scorer writes it. Printed, never used to choose.
OUTCOME = "pir_per36_dest"
OUTCOME_COLUMNS = (OUTCOME, "games_dest", "minutes_dest")
#: Amendment 20, rule 1: the paper's main-text table also prints, for each player of a pair, last
#: season's domestic rate (a frozen column) and games played so far (outcome side). Both are
#: attached after the selection and gate G32, by ``attach_pair_details``; neither chooses a pair.
PAIR_SOURCE_RATE = "pir_per36_src"
PAIR_GAMES = "games_dest"
PAIR_DETAIL_COLUMNS = (
    f"{PAIR_SOURCE_RATE}_a",
    f"{PAIR_GAMES}_a",
    f"{PAIR_SOURCE_RATE}_b",
    f"{PAIR_GAMES}_b",
)
#: The scorer's flag for a newcomer whose seventeen frozen forecasts all exist.
SCORED_FLAG = "all_arms_forecast"
TOP = 10
PAIRS_PRINTED = 10
#: Amendment 15: "If fewer than 60 newcomers are scored, E32 prints all of them".
MIN_SCORED = 60
#: Amendment 15: "Before scoring the paper may print no named player." The
#: frozen test may not be scored before this date (pre-registration, P1).
NOT_BEFORE = dt.date(2026, 11, 25)
EXACT_TOLERANCE = 1e-12
PLAYER_COLUMNS = (
    "league_dest",
    "group",
    "rank_league_aware",
    "newcomers_in_competition",
    "player_name",
    "league_src",
    "pir_per36_src",
    D,
    O,
)
PAIR_COLUMNS = (
    "league_dest",
    "player_a",
    "league_src_a",
    f"{D}_a",
    f"{O}_a",
    "player_b",
    "league_src_b",
    f"{D}_b",
    f"{O}_b",
    "gap_league_aware",
    "gap_destination_only",
    "printed",
)


class GateFailure(common.GateFailure):
    """A registered Amendment 15 gate (G32) did not hold."""


negative_control = a1.negative_control
clean = a1.clean


# -------------------------------------------------------------- selection --
def newcomer_keys(scored_rows: pd.DataFrame) -> pd.DataFrame:
    """The keys of the newcomers the scorer counts. Nothing else leaves the scored rows."""
    missing = [c for c in (*KEY, SCORED_FLAG) if c not in scored_rows.columns]
    if missing:
        raise GateFailure(f"the scorer's rows lack {missing}")
    if not scored_rows[SCORED_FLAG].astype(bool).all():
        raise GateFailure(
            "a newcomer has no complete set of frozen forecasts; Amendment 15 does not say whether the scorer counts him"
        )
    keys = scored_rows[KEY].astype(str)
    if keys.duplicated().any():
        raise GateFailure("a newcomer appears twice in the scorer's rows")
    return keys.sort_values(KEY).reset_index(drop=True)


def frozen_view(frozen: pd.DataFrame, keys: pd.DataFrame) -> pd.DataFrame:
    """The newcomers' rows of the frozen file, frozen columns only."""
    view = keys.merge(frozen[list(FROZEN_COLUMNS)], on=KEY, how="left", validate="1:1")
    numbers = view[["pir_per36_src", D, O]].to_numpy(float)
    if view.league_src.isna().any() or not np.isfinite(numbers).all():
        raise GateFailure(
            "a newcomer is not in the frozen file, or has no frozen forecast"
        )
    return view


def assert_frozen_only(view: pd.DataFrame) -> None:
    """G32: the selection receives frozen forecast columns only."""
    extra = [c for c in view.columns if c not in FROZEN_COLUMNS]
    if extra or len(view.columns) != len(FROZEN_COLUMNS):
        raise GateFailure(
            f"G32: the selection step received columns that are not frozen: {extra or 'a missing frozen column'}"
        )


def ordered(view: pd.DataFrame) -> pd.DataFrame:
    """Per competition, by the frozen league-aware forecast (ties by name)."""
    out = view.sort_values(
        ["league_dest", O, "player_name"], ascending=[True, False, True]
    ).reset_index(drop=True)
    out["rank_league_aware"] = out.groupby("league_dest").cumcount() + 1
    out["newcomers_in_competition"] = out.groupby("league_dest").player_name.transform(
        "size"
    )
    return out


def select_players(
    view: pd.DataFrame, *, print_all: bool, top: int = TOP
) -> pd.DataFrame:
    """The ten highest and the ten lowest per competition, or everyone."""
    assert_frozen_only(view)
    rows = ordered(view)
    n, rank = rows.newcomers_in_competition, rows.rank_league_aware
    high, low = rank <= top, rank > n - top
    rows["group"] = np.select(
        [print_all | (n <= 2 * top), high, low],
        ["all", "highest", "lowest"],
        default="",
    )
    return rows.loc[rows.group.ne(""), list(PLAYER_COLUMNS)].reset_index(drop=True)


def changed_pairs(view: pd.DataFrame, *, printed: int = PAIRS_PRINTED):
    """Same competition, different source leagues, order reversed by the league table."""
    assert_frozen_only(view)
    pairs, counts = [], {}
    for league, part in view.groupby("league_dest", sort=True):
        part = part.sort_values("player_name").reset_index(drop=True)
        i, j = np.triu_indices(len(part), k=1)
        cross = part.league_src.to_numpy()[i] != part.league_src.to_numpy()[j]
        i, j = i[cross], j[cross]
        d = part[D].to_numpy(float)[i] - part[D].to_numpy(float)[j]
        o = part[O].to_numpy(float)[i] - part[O].to_numpy(float)[j]
        reversed_ = d * o < 0
        counts[str(league)] = {
            "newcomers": int(len(part)),
            "cross_league_pairs": int(len(i)),
            "order_differs": int(reversed_.sum()),
            "tied_in_either_forecast": int((d * o == 0).sum()),
        }
        for a, b, gap_o, gap_d in zip(
            i[reversed_], j[reversed_], o[reversed_], d[reversed_]
        ):
            if gap_o < 0:  # player_a is the one the league-aware forecast puts higher
                a, b, gap_o, gap_d = b, a, -gap_o, -gap_d
            first, second = part.iloc[a], part.iloc[b]
            pairs.append(
                {
                    "league_dest": league,
                    "player_a": first.player_name,
                    "league_src_a": first.league_src,
                    f"{D}_a": first[D],
                    f"{O}_a": first[O],
                    "player_b": second.player_name,
                    "league_src_b": second.league_src,
                    f"{D}_b": second[D],
                    f"{O}_b": second[O],
                    "gap_league_aware": gap_o,
                    "gap_destination_only": gap_d,
                }
            )
    table = pd.DataFrame(pairs, columns=[c for c in PAIR_COLUMNS if c != "printed"])
    table = table.sort_values(
        ["gap_league_aware", "league_dest", "player_a", "player_b"],
        ascending=[False, True, True, True],
    ).reset_index(drop=True)
    table["printed"] = table.index < printed
    return table[list(PAIR_COLUMNS)], counts


def select(scored_rows: pd.DataFrame, frozen: pd.DataFrame) -> dict:
    """The whole selection. Only the newcomers' keys are taken from the scored rows."""
    keys = newcomer_keys(scored_rows)
    view = frozen_view(frozen, keys)
    print_all = len(keys) < MIN_SCORED
    players = select_players(view, print_all=print_all)
    pairs, counts = changed_pairs(view)
    return {
        "n_newcomers": int(len(keys)),
        "print_all": bool(print_all),
        "players": players,
        "pairs": pairs,
        "counts": counts,
    }


def same_selection(first: dict, second: dict) -> None:
    for name in ("players", "pairs"):
        if not first[name].equals(second[name]):
            raise GateFailure(
                f"G32: the selected {name} changed with the outcome column"
            )
    if first["counts"] != second["counts"] or first["print_all"] != second["print_all"]:
        raise GateFailure("G32: the selection counts changed with the outcome column")


def g32(scored_rows: pd.DataFrame, frozen: pd.DataFrame, selection: dict) -> dict:
    """The registered negative control: delete the outcome, and reverse it."""
    present = [c for c in OUTCOME_COLUMNS if c in scored_rows.columns]
    same_selection(selection, select(scored_rows.drop(columns=present), frozen))
    reversed_rows = scored_rows.copy()
    for column in present:
        reversed_rows[column] = scored_rows[column].to_numpy()[::-1]
    same_selection(selection, select(reversed_rows, frozen))
    return {
        "status": "passed",
        "outcome_columns_deleted": present,
        "same_rows_without_the_outcome": True,
        "same_rows_with_the_outcome_reversed": True,
        "negative_control": negative_control(
            assert_frozen_only,
            frozen_view(frozen, newcomer_keys(scored_rows)).assign(**{OUTCOME: 0.0}),
        ),
    }


def frozen_forecast_difference(scored_rows: pd.DataFrame, frozen: pd.DataFrame) -> dict:
    """Where the scorer's rows carry the two forecasts, they are the frozen ones."""
    merged = scored_rows[
        [*KEY, *[c for c in (D, O) if c in scored_rows.columns]]
    ].merge(
        frozen[[*KEY, D, O]],
        on=KEY,
        how="left",
        suffixes=("", "_frozen"),
        validate="1:1",
    )
    return {
        arm: a1.max_abs(merged[arm], merged[f"{arm}_frozen"])
        for arm in (D, O)
        if arm in scored_rows.columns
    }


# ---------------------------------------------- after the selection: print --
def attach_outcomes(players: pd.DataFrame, scored_rows: pd.DataFrame) -> pd.DataFrame:
    """Add what each selected newcomer has produced so far, as the last columns."""
    extra = [c for c in OUTCOME_COLUMNS if c in scored_rows.columns]
    out = players.merge(scored_rows[[*KEY, *extra]], on=KEY, how="left", validate="1:1")
    if len(out) != len(players) or not out[list(PLAYER_COLUMNS)].equals(players):
        raise GateFailure("G32: attaching the outcome changed the selected rows")
    return out[[*PLAYER_COLUMNS, *[c for c in extra if c != OUTCOME], OUTCOME]]


def attach_pair_outcomes(
    pairs: pd.DataFrame, scored_rows: pd.DataFrame
) -> pd.DataFrame:
    """For each pair, both outcomes so far and whether the league-aware order held."""
    y = scored_rows.set_index(KEY)[OUTCOME]
    out = pairs.copy()
    for side in ("a", "b"):
        index = pd.MultiIndex.from_frame(
            out[[f"player_{side}", "league_dest"]].rename(
                columns={f"player_{side}": "player_name"}
            )
        )
        out[f"{OUTCOME}_{side}"] = y.reindex(index).to_numpy(float)
    gap = out[f"{OUTCOME}_a"] - out[f"{OUTCOME}_b"]
    out["league_aware_order_held"] = np.where(gap == 0, None, gap > 0)
    if not out[list(PAIR_COLUMNS)].equals(pairs):
        raise GateFailure("G32: attaching the outcome changed the selected pairs")
    return out


def attach_pair_details(
    pairs: pd.DataFrame, scored_rows: pd.DataFrame, frozen: pd.DataFrame
) -> pd.DataFrame:
    """Amendment 20, rule 1: for both players of every pair, last season's domestic rate (from
    the frozen file) and games played so far (from the scorer's rows), as the last columns.

    Runs after the selection, after gate G32 and after ``attach_pair_outcomes``. It reads the
    pairs it is given and cannot add, drop or reorder one."""
    if PAIR_GAMES not in scored_rows.columns:
        raise GateFailure(
            f"the scorer's rows lack {PAIR_GAMES}, which Amendment 20, rule 1, prints"
        )
    rate = frozen.set_index(KEY)[PAIR_SOURCE_RATE]
    games = scored_rows.set_index(KEY)[PAIR_GAMES]
    out = pairs.copy()
    for side in ("a", "b"):
        index = pd.MultiIndex.from_frame(
            out[[f"player_{side}", "league_dest"]].rename(
                columns={f"player_{side}": "player_name"}
            )
        )
        out[f"{PAIR_SOURCE_RATE}_{side}"] = rate.reindex(index).to_numpy(float)
        played = games.reindex(index).to_numpy(float)
        if not (
            np.isfinite(played).all()
            and np.isfinite(out[f"{PAIR_SOURCE_RATE}_{side}"]).all()
        ):
            raise GateFailure(
                "a player of a pair has no frozen source rate or no games count"
            )
        out[f"{PAIR_GAMES}_{side}"] = played.astype(int)
    if not out[list(pairs.columns)].equals(pairs):
        raise GateFailure("G32: attaching the pair details changed the selected pairs")
    return out[[*pairs.columns, *PAIR_DETAIL_COLUMNS]]


def run(
    root: Path, scored_path: Path, score_record: Path, out: Path, *, today=None
) -> dict:
    root = Path(root)
    today = today or dt.date.today()
    if today < NOT_BEFORE:
        raise GateFailure(
            "E32 may not print a named player before the frozen test is scored (25 Nov 2026)"
        )
    record = json.loads(Path(score_record).read_text())
    common.check_sha(root / FROZEN, FROZEN_SHA)
    frozen = pd.read_parquet(root / FROZEN)
    scored_rows = pd.read_parquet(scored_path)
    wf = frozen_forecast_difference(scored_rows, frozen)
    if wf:
        a1.gate_max("the scorer's rows carry the frozen forecasts", wf, EXACT_TOLERANCE)
    selection = select(scored_rows, frozen)
    gates = {
        "frozen_file": {"status": "passed", "sha256": FROZEN_SHA},
        "scored_rows_carry_the_frozen_forecasts": {
            "status": "passed"
            if wf
            else "not checked: the scorer's rows carry neither forecast column",
            "max_difference": max(wf.values()) if wf else None,
        },
        "G32": g32(scored_rows, frozen, selection),
    }
    # ---- only after the selection and its gate: the outcome is attached
    players = attach_outcomes(selection["players"], scored_rows)
    pairs = attach_pair_outcomes(selection["pairs"], scored_rows)
    pairs = attach_pair_details(pairs, scored_rows, frozen)
    printed = pairs.loc[pairs.printed]
    held = printed.league_aware_order_held
    summary = {
        "analysis": "Amendment 15: E32, named 2026-27 newcomers with their frozen forecasts (no result is computed)",
        "amendment_commit": AMENDMENT_COMMIT,
        "amendment_sha256": sha256_file(root / AMENDMENT),
        "frozen_forecasts_sha256": FROZEN_SHA,
        "scored_rows_sha256": sha256_file(scored_path),
        "score_record_sha256": sha256_file(score_record),
        "score_status": record.get("status"),
        "n_newcomers": selection["n_newcomers"],
        "print_all": selection["print_all"],
        "print_all_rule": f"fewer than {MIN_SCORED} newcomers scored: all are printed",
        "players_printed": int(len(players)),
        "by_competition": selection["counts"],
        "pairs_whose_order_differs": int(len(pairs)),
        "pairs_printed": int(len(printed)),
        "printed_pairs_where_the_league_aware_order_held": int((held == True).sum()),  # noqa: E712 -- object column of True/False/None
        "printed_pairs_tied_in_the_outcome": int(held.isna().sum()),
        "described_not_tested": "The count of printed pairs in which the league-aware order held is a description. No test is run on it.",
        "selection_rule": {
            "players": f"per competition, ordered by the frozen league-aware forecast ({O}); the {TOP} highest and the {TOP} lowest; ties by name; a competition with {2 * TOP} newcomers or fewer is printed whole",
            "pairs": f"same competition, different source leagues, order reversed between {D} and {O}; sorted by the gap in {O}; the {PAIRS_PRINTED} largest are marked printed, over both competitions together",
            "inputs": list(FROZEN_COLUMNS),
        },
        "gates": gates,
    }
    out = Path(out)
    out.mkdir(parents=True, exist_ok=False)
    players.to_csv(out / "e32_newcomers.csv", index=False)
    pairs.to_csv(out / "e32_changed_pairs.csv", index=False)
    (out / "summary.json").write_text(
        json.dumps(clean(summary), indent=2, sort_keys=True) + "\n"
    )
    return summary


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--scored-rows",
        type=Path,
        required=True,
        help="the scorer's p1_scored_rows.parquet",
    )
    parser.add_argument(
        "--score-record",
        type=Path,
        required=True,
        help="the scorer's committed score.json",
    )
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    summary = run(Path.cwd(), args.scored_rows, args.score_record, args.out)
    print(
        f"E32: {summary['n_newcomers']} newcomers, {summary['players_printed']} printed, "
        f"{summary['pairs_whose_order_differs']} pairs whose order differs"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
