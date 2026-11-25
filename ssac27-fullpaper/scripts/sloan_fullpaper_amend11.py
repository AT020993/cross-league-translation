#!/usr/bin/env python3
"""Amendment 11 analysis: E29 (DESCRIPTIVE; every outcome already seen).

Pre-registration: docs/research/sloan-full-paper-preregistration-2026-11-03.md
(commit f52e7c831) and its Amendment 11,
docs/research/sloan-full-paper-preregistration-amendment-11-2026-11-16.md
(commit 40f0d278b, pushed alone on 2026-11-16, before this file existed).

E29 -- where the league table missed on the older arrivals. For each source
league of the printed older-seasons version, and for all arrivals, in two
populations (the older-seasons arrivals of Amendment 7 and the 674 benchmark
arrivals of 2020-2025), three means in EFF/36:

* the move: league-aware forecast minus destination-only forecast;
* the error without the table: destination-only forecast minus outcome;
* the error with the table: league-aware forecast minus outcome;

each unweighted and weighted by destination minutes, each with the registered
two-way clustered 95% interval (player, destination club-season). E29c: per
source league, the change between periods in the error without the table
(older minus 2020-2025), the two samples treated as independent, standard
errors combined in quadrature, the smaller of the two degrees of freedom.

No model is refitted and nothing is re-scored. E29 describes where the forecast
missed; it states no cause. Both versions of the older-seasons test are
computed here. Only the version the paper prints under Amendment 7's permission
rule goes into ``summary.json`` and the CSV tables; everything that depends on
the other version, including the rows of its extra league in both populations,
is written to ``withheld/`` in the retained run and is never committed.

Threats and their controls (all in this file): older rows that are not E28's
(G29a, first: the four committed E28b differences to 1e-9; its negative control
shuffles the outcome column); forecasts on the 674 that are not the committed
ones (G0, scope, G29b: the committed errors of the two forecasts and the
committed G_D with its interval; its negative control shifts one forecast
column by 0.01); league rows that do not partition a population or a move that
is not the difference of the two errors (G29c; its negative control drops one
league's rows); a league of one period matched to the wrong league of the other
(league-map gate); a withheld number in a file that may be committed (G29d,
with a planted value). No 2026-27 statistic is read.
"""

# ruff: noqa: E501, E741 -- gate messages and registered sentences; O is the offsets arm
from __future__ import annotations

if __name__ == "__main__":
    import sys as _sys
    from pathlib import Path as _Path

    _sys.path.insert(0, str(_Path(__file__).resolve().parents[1]))
    from src.research.execution import enter as _enter

    _enter(__file__)

import argparse
import json
import math
import os
from pathlib import Path
import sys

for _name in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_name, "1")
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from scipy import stats  # noqa: E402

from scripts import sloan_context_benchmarks as benchmark  # noqa: E402
from scripts import sloan_fullpaper_amend9 as e28  # noqa: E402
from scripts import sloan_fullpaper_common as common  # noqa: E402
from scripts import sloan_fullpaper_decisions as dec  # noqa: E402
from scripts import sloan_fullpaper_older_seasons as e27  # noqa: E402
from scripts import sloan_fullpaper_older_seasons_paper as e27p  # noqa: E402
from scripts import sloan_fullpaper_recipes as recipes  # noqa: E402
from scripts import sloan_fullpaper_survivorship as surv  # noqa: E402
from scripts.translation_research_common import sha256_file  # noqa: E402

OUTCOME = e28.OUTCOME
WEIGHT = e28.WEIGHT
WEIGHTINGS = e28.WEIGHTINGS
D, O = e28.D, e28.O
AMENDMENT = Path(
    "docs/research/sloan-full-paper-preregistration-amendment-11-2026-11-16.md"
)
AMENDMENT_COMMIT = "40f0d278befde5488ed69311bdb8a4241bc0bb64"
#: quantity -> (minuend, subtrahend): the per-arrival value is the first minus the second.
QUANTITIES = {
    "move": (O, D),
    "error_without_table": (D, OUTCOME),
    "error_with_table": (O, OUTCOME),
}
ERRORS = ("error_without_table", "error_with_table")
ALL = "all"
OLDER_SEASONS = (2008, 2015)
REPRO_TOLERANCE = 1e-9
CONTROL_SHIFT = e28.CONTROL_SHIFT
SHUFFLE_SEED = 20261117

#: Committed files this analysis reads, each checked against its sha256.
COMMITTED = {
    "e27_arrivals": e28.COMMITTED["e27_arrivals"],
    "e27_summary": e28.COMMITTED["e27_summary"],
    "e28": (
        "docs/research/artifacts/sloan-fullpaper-amend9-2026-11/summary.json",
        "da97930085208070b8ce8e24ba4a813d8c5225690992bd240f8189d5751a0b22",
    ),
    "e24_level": (
        "docs/research/artifacts/sloan-fullpaper-amend4-2026-11/e24_level.csv",
        "4aa5483cfcde4c0fafb8f2feba19a7faf6fc6f9370e1351f9f1fa26fd6435e4c",
    ),
    "e24_leagues": (
        "docs/research/artifacts/sloan-fullpaper-amend4-2026-11/e24_league_bias.csv",
        "f9bbcddc250fe488aaedfebf7a572b568cccb28bb14cf82f76123428a27c28ad",
    ),
}
E27_PAPER = e28.E27_PAPER
RELEASE = e28.RELEASE
FROZEN_SHA = e28.FROZEN_SHA

#: Names used in sentences ("arrivals from L").
LEAGUE_NAMES = {
    "aba": "the Adriatic league",
    "israel": "Israel",
    "acb": "Spain's ACB",
}

EXPOSURE = {
    "seen_before_registration": [
        "every outcome E29 uses",
        "on the older arrivals, in one unregistered look after the E28 result (disclosed in Amendment 10), for the version without Spain's ACB: by source league, the number of arrivals, the mean move made by the league table, the mean error of the destination-only and of the league-aware forecast, and G_D unweighted and weighted by minutes; the same by destination competition, and G_D by destination season",
        "on the arrivals of 2020-2025: the paper's league-bias figure and table (each league's error measured against the average arrival), and the yearly refits of each league's equivalent",
    ],
    "on_file_before_registration": [
        "the committed Amendment 4 output (E24) holds, for every source league of the 674, the mean error of the destination-only and of the league-aware forecast not centred on the average arrival, with bootstrap intervals. E29b's unweighted point estimates of the two errors on the 674 are therefore not new numbers, although Amendment 11 lists them as not seen in E29's form. This run reproduces them as a check",
    ],
    "not_seen_before_this_run": [
        "any two-way clustered interval for the quantities of E29",
        "their versions weighted by destination minutes",
        "the change between the two periods",
        "any per-league number of the withheld version of the older-seasons test",
    ],
}
FURTHER_READING = "The older-seasons outcomes were read in the single Amendment 7 scoring run and again in E28; E29 is a further reading of them. No rule of that run is changed and nothing is re-scored."

#: Amendment 11, "What the paper may say" and the rules below it, verbatim.
WORDING = {
    "league": "on the older arrivals the league table lowered [raised] the forecast for arrivals from L by X EFF/36; without the table the forecast was Y EFF/36 (interval) below [above] what they delivered, and with it Z (interval)",
    "change_excludes_zero": "against the forecast that knows only the destination, arrivals from L did better [worse] in 2008–2015 than in 2020–2025 by X EFF/36 (interval)",
    "change_includes_zero": "for arrivals from L the change between the two periods is not distinguishable from zero at this n (X EFF/36, interval)",
    "caveat": "this shows where the forecast missed; it cannot separate a change in league strength from a change in which players clubs signed, in the data source or in the level of the forecasts",
    "consistent_with": "Consistent with league numbers that change over time",
    "otherwise": "the table shows where the forecast missed and not why",
}
LIMITS = (
    "On the older arrivals the forecasts come from the model fitted on every season through 2025. On the arrivals of 2020–2025 each forecast comes from a model fitted on earlier seasons only.",
    "The older source statistics come from the leagues' own box scores. The source statistics of 2020–2025 come from a different provider.",
    "A mean error also carries the general level of the forecasts in that period. The rows for all arrivals are printed so that a reader can see that level.",
)


class GateFailure(common.GateFailure):
    """A registered Amendment 11 gate did not hold."""


negative_control = e28.negative_control
max_abs = e28.max_abs
gate_max = e28.gate_max
passed = e28.passed
clean = e28.clean
multiway_interval = benchmark.previous.multiway_interval


def load_committed(root: Path) -> dict:
    out = {}
    for name, (relative, expected) in COMMITTED.items():
        path = Path(root) / relative
        common.check_sha(path, expected)
        out[name] = (
            json.loads(path.read_text())
            if relative.endswith(".json")
            else pd.read_csv(path, dtype={"player_name": str})
        )
    return out


# ------------------------------------------------------------- statistics --
def mean_interval(values, rows: pd.DataFrame, *, weighted: bool = False) -> dict:
    """A mean with the registered two-way clustered interval (player, club-season).

    Unweighted: the registered ``multiway_interval``. Weighted by destination
    minutes: E14b's ``weighted_interval`` (identical when every weight is 1).
    """
    values = np.asarray(values, dtype=float)
    if weighted:
        w = rows[WEIGHT].to_numpy(float)
        block = surv.weighted_interval(values, w, rows.player_name, rows.cluster)
    else:
        block = multiway_interval(values, rows.player_name, rows.cluster)
    record = {
        "n": int(len(values)),
        "mean": block["difference"],
        "ci95": None,
        "se": None,
        "df": None,
        "status": block["status"],
    }
    if block["status"] == "ok":
        detail = recipes.interval_stats(block, 1.0)
        record.update(ci95=detail["ci95"], se=detail["se"], df=detail["df"])
    record["reading"] = e28.reading(record["ci95"])
    return record


def values_of(rows: pd.DataFrame, quantity: str) -> np.ndarray:
    first, second = QUANTITIES[quantity]
    return rows[first].to_numpy(float) - rows[second].to_numpy(float)


def row_means(rows: pd.DataFrame) -> dict:
    """The three means of one table row, unweighted and weighted."""
    rows = rows.reset_index(drop=True)
    return {
        quantity: {
            weighting: mean_interval(
                values_of(rows, quantity), rows, weighted=weighting != "unweighted"
            )
            for weighting in WEIGHTINGS
        }
        for quantity in QUANTITIES
    }


def population_table(rows: pd.DataFrame, column: str, leagues: dict) -> dict:
    """``leagues`` maps a row key to that league's name in ``column``; plus all arrivals."""
    out = {}
    for key, name in leagues.items():
        part = rows.loc[rows[column].eq(name)]
        out[key] = {"league": name, "n": int(len(part)), "means": row_means(part)}
    out[ALL] = {"league": None, "n": int(len(rows)), "means": row_means(rows)}
    return out


def change(older: dict, recent: dict) -> dict:
    """Older minus 2020-2025: independent samples, SEs in quadrature, the smaller df."""
    record = {
        "n_older": older["n"],
        "n_benchmark": recent["n"],
        "older": older["mean"],
        "benchmark": recent["mean"],
        "change": older["mean"] - recent["mean"],
        "ci95": None,
        "se": None,
        "df": None,
        "detectable_80": None,
        "reading": "not_estimable",
    }
    if older["ci95"] is None or recent["ci95"] is None:
        return record
    se = math.hypot(older["se"], recent["se"])
    df = int(min(older["df"], recent["df"]))
    half = float(stats.t.ppf(0.975, df) * se)
    low, high = record["change"] - half, record["change"] + half
    record.update(
        ci95=[low, high],
        se=se,
        df=df,
        detectable_80=float((stats.t.ppf(0.975, df) + stats.t.ppf(0.80, df)) * se),
        reading="includes_zero" if low <= 0 <= high else "excludes_zero",
    )
    return record


def changes(older: dict, recent: dict, leagues) -> dict:
    """E29c for each league: the change in the error without the table."""
    return {
        key: {
            weighting: change(
                older[key]["means"]["error_without_table"][weighting],
                recent[key]["means"]["error_without_table"][weighting],
            )
            for weighting in WEIGHTINGS
        }
        for key in leagues
    }


# --------------------------------------------------------------- licences --
def two(value: float) -> str:
    return f"{value:.2f}"


def span(ci95) -> str:
    return f"interval {ci95[0]:.2f} to {ci95[1]:.2f}"


def side(value: float) -> str:
    return "below" if value < 0 else "above"


def league_sentence(name: str, means: dict, weighting: str) -> dict:
    """Amendment 11, row 1: the move and the two errors for one league, older arrivals."""
    move = means["move"][weighting]
    without = means["error_without_table"][weighting]
    with_ = means["error_with_table"][weighting]
    if without["ci95"] is None or with_["ci95"] is None:
        return {
            "registered_wording": WORDING["league"],
            "sentence": None,
            "note": "an interval is not estimable at this n; no sentence is rendered",
        }
    verb = "lowered" if move["mean"] < 0 else "raised"
    sentence = (
        f"on the older arrivals the league table {verb} the forecast for arrivals from {name} by {two(abs(move['mean']))} EFF/36; "
        f"without the table the forecast was {two(abs(without['mean']))} EFF/36 ({span(without['ci95'])}) {side(without['mean'])} what they delivered, "
        f"and with it {two(abs(with_['mean']))} ({span(with_['ci95'])})"
    )
    if side(with_["mean"]) != side(without["mean"]):
        sentence += f" {side(with_['mean'])}"
    return {"registered_wording": WORDING["league"], "sentence": sentence}


def change_sentence(name: str, record: dict) -> dict:
    """Amendment 11, rows 2 and 3: the change between periods for one league."""
    if record["reading"] == "excludes_zero":
        how = "better" if record["change"] < 0 else "worse"
        return {
            "reading": record["reading"],
            "registered_wording": WORDING["change_excludes_zero"],
            "sentence": f"against the forecast that knows only the destination, arrivals from {name} did {how} in 2008–2015 than in 2020–2025 by {two(abs(record['change']))} EFF/36 ({span(record['ci95'])})",
        }
    if record["reading"] == "includes_zero":
        return {
            "reading": record["reading"],
            "registered_wording": WORDING["change_includes_zero"],
            "sentence": f"for arrivals from {name} the change between the two periods is not distinguishable from zero at this n ({record['change']:+.2f} EFF/36, {span(record['ci95'])})",
        }
    return {
        "reading": record["reading"],
        "registered_wording": None,
        "sentence": None,
        "note": "the change is not estimable at this n; no sentence is rendered",
    }


def consistent_with(change_block: dict) -> dict:
    """The registered condition: the change excludes zero for at least one league."""
    met = {
        weighting: any(
            block[weighting]["reading"] == "excludes_zero"
            for block in change_block.values()
        )
        for weighting in WEIGHTINGS
    }
    return {
        "rule": "may be written only if the change between periods excludes zero for at least one league; read on the unweighted change (the stricter reading: the weighted change cannot license it alone)",
        "condition_met": met["unweighted"],
        "condition_met_minutes_weighted": met["minutes_weighted"],
        "registered_wording": WORDING["consistent_with"]
        if met["unweighted"]
        else WORDING["otherwise"],
    }


def licences(older: dict, change_block: dict, leagues) -> dict:
    return {
        "leagues": {
            key: {
                weighting: league_sentence(
                    LEAGUE_NAMES[key], older[key]["means"], weighting
                )
                for weighting in WEIGHTINGS
            }
            for key in leagues
        },
        "change": {
            key: {
                weighting: change_sentence(
                    LEAGUE_NAMES[key], change_block[key][weighting]
                )
                for weighting in WEIGHTINGS
            }
            for key in leagues
        },
        "consistent_with": consistent_with(change_block),
    }


# ------------------------------------------------------------------ gates --
def g29a_differences(part: pd.DataFrame, committed: dict, *, shuffle=None) -> dict:
    """The four E28b differences (G_H, G_D; unweighted, weighted) with their intervals.

    ``committed`` is E28b's ``contrasts`` block. ``shuffle`` (a seed) permutes
    the outcome column across rows (the negative control).
    """
    part = part.reset_index(drop=True)
    if shuffle is not None:
        part = part.assign(
            **{OUTCOME: part[OUTCOME].sample(frac=1.0, random_state=shuffle).to_numpy()}
        )
    got = e28.gains(part)
    worst = {}
    for name in e28.GAINS:
        for weighting in WEIGHTINGS:
            mine, ref = got[name][weighting], committed[name][weighting]
            if mine["n"] != ref["n"] or mine["ci95"] is None:
                worst[f"{name}:{weighting}:n_or_estimable"] = math.inf
                continue
            worst[f"{name}:{weighting}:difference"] = abs(
                mine["difference"] - ref["difference"]
            )
            worst[f"{name}:{weighting}:ci95"] = max_abs(mine["ci95"], ref["ci95"])
    return worst


def g29b_differences(
    rows: pd.DataFrame, committed: dict, *, shift: float = 0.0, column: str = O
) -> dict:
    """On the 674: the committed errors of the two forecasts and G_D with its interval.

    ``committed`` is E28a's block. ``shift`` moves one forecast column (the
    negative control).
    """
    if shift:
        rows = rows.assign(**{column: rows[column] + shift})
    worst = {}
    errors = e28.arm_errors(rows, (D, O))
    for arm in (D, O):
        for weighting in WEIGHTINGS:
            worst[f"mae:{arm}:{weighting}"] = abs(
                errors[arm][weighting] - committed["mae"][arm][weighting]
            )
    for weighting in WEIGHTINGS:
        mine = e28.gain(rows, D, O, weighted=weighting != "unweighted")
        ref = committed["contrasts"]["G_D"][weighting]
        worst[f"G_D:{weighting}:difference"] = abs(
            mine["difference"] - ref["difference"]
        )
        worst[f"G_D:{weighting}:ci95"] = max_abs(mine["ci95"], ref["ci95"])
    return worst


def g29c_differences(
    rows: pd.DataFrame, column: str, table: dict, *, drop=None
) -> dict:
    """League means add up to the all-arrivals mean; the move is the errors' difference.

    Recomputed from the rows for every league of ``column`` (weights: numbers of
    arrivals, or minutes for the weighted means), and compared with the means
    reported in ``table``. ``drop`` leaves one league out of the sum (the
    negative control).
    """
    worst = {}
    names = sorted(rows[column].unique())
    reported = {v["league"]: v["means"] for k, v in table.items() if k != ALL}
    for weighting in WEIGHTINGS:
        w = (
            np.ones(len(rows))
            if weighting == "unweighted"
            else rows[WEIGHT].to_numpy(float)
        )
        values = {q: values_of(rows, q) for q in QUANTITIES}
        overall = {q: float(np.sum(w * v) / np.sum(w)) for q, v in values.items()}
        total = dict.fromkeys(QUANTITIES, 0.0)
        for index, name in enumerate(names):
            mask = rows[column].eq(name).to_numpy()
            mean = {
                q: float(np.sum(w[mask] * v[mask]) / np.sum(w[mask]))
                for q, v in values.items()
            }
            worst[f"move:{weighting}:{index}"] = abs(
                mean["move"] - (mean["error_with_table"] - mean["error_without_table"])
            )
            for q in QUANTITIES:
                if name in reported:
                    worst[f"reported:{weighting}:{q}:{index}"] = abs(
                        reported[name][q][weighting]["mean"] - mean[q]
                    )
                if name != drop:
                    total[q] += float(np.sum(w[mask])) * mean[q]
        for q in QUANTITIES:
            worst[f"adds_up:{weighting}:{q}"] = abs(
                total[q] / float(np.sum(w)) - overall[q]
            )
            worst[f"reported:{weighting}:{q}:all"] = abs(
                table[ALL]["means"][q][weighting]["mean"] - overall[q]
            )
        worst[f"move:{weighting}:all"] = abs(
            overall["move"]
            - (overall["error_with_table"] - overall["error_without_table"])
        )
    return worst


def league_map(part: pd.DataFrame, rows: pd.DataFrame, leagues) -> dict:
    """Each league of the older version, named explicitly in the 674, with rows in both."""
    if set(part.league) != set(leagues):
        raise GateFailure("league-map gate: the older rows hold other leagues")
    seasons = part.season_dest.astype(float)
    if not seasons.between(*OLDER_SEASONS).all():
        raise GateFailure("league-map gate: an older arrival is outside 2008-2015")
    out = {}
    for key in leagues:
        name = e27.LEAGUES.get(key)
        if name is None or key not in LEAGUE_NAMES:
            raise GateFailure(f"league-map gate: no registered name for {key}")
        older = part.loc[part.league.eq(key)]
        recent = rows.loc[rows.league_src.eq(name)]
        if not len(older) or not len(recent):
            raise GateFailure(f"league-map gate: {key} has no rows in one population")
        if set(older.league_src) != {name}:
            raise GateFailure(f"league-map gate: {key} is not {name} in the older rows")
        out[key] = {
            "benchmark_league": name,
            "older": int(len(older)),
            "benchmark": int(len(recent)),
        }
    return out


def e24_differences(table: dict, level: pd.DataFrame, by_league: pd.DataFrame) -> dict:
    """The 674 rows against the committed Amendment 4 means (unweighted points)."""
    worst = {}
    arms = {"error_without_table": D, "error_with_table": O}
    for quantity, arm in arms.items():
        recorded = level.loc[level.arm.eq(arm) & level.scope.eq("all")]
        if len(recorded) != 1:
            return {"e24_level_rows": math.inf}
        worst[f"{quantity}:all"] = abs(
            table[ALL]["means"][quantity]["unweighted"]["mean"]
            - float(recorded.mean_signed_error.iloc[0])
        )
        for index, (key, row) in enumerate(table.items()):
            if key == ALL:
                continue
            recorded = by_league.loc[by_league.source_league.eq(row["league"])]
            if len(recorded) != 1 or int(recorded.arrivals.iloc[0]) != row["n"]:
                worst[f"{quantity}:{index}:rows"] = math.inf
                continue
            worst[f"{quantity}:{index}"] = abs(
                row["means"][quantity]["unweighted"]["mean"]
                - float(recorded[f"signed_error_{arm}"].iloc[0])
            )
    return worst


def assert_no_leak(summary: dict, files: dict, leagues, withheld: dict | None) -> int:
    """G29d: E28's leak gate over the summary and the text of every table."""
    if withheld is None:
        return 0
    rows = {
        key
        for block in ("e29a", "e29b", "e29c")
        for key in summary[block]["rows"]
        if key != ALL
    }
    if rows != set(leagues):
        raise GateFailure("G29d: a table carries a row outside the printed leagues")
    public = {
        "e28b": {"withheld": summary["withheld"], "leagues": sorted(leagues)},
        "summary": summary,
        "files": files,
    }
    return e28.assert_no_leak(public, {"contrasts": withheld})


def table_rows(population: str, table: dict) -> list:
    out = []
    for key, row in table.items():
        for quantity in QUANTITIES:
            for weighting in WEIGHTINGS:
                r = row["means"][quantity][weighting]
                ci = r["ci95"] or [None, None]
                out.append(
                    {
                        "population": population,
                        "row": key,
                        "league": row["league"],
                        "quantity": quantity,
                        "weighting": weighting,
                        "n": r["n"],
                        "mean": r["mean"],
                        "ci95_low": ci[0],
                        "ci95_high": ci[1],
                        "se": r["se"],
                        "df": r["df"],
                        "reading": r["reading"],
                    }
                )
    return out


def change_rows(block: dict) -> list:
    out = []
    for key, by_weighting in block.items():
        for weighting in WEIGHTINGS:
            r = by_weighting[weighting]
            ci = r["ci95"] or [None, None]
            out.append(
                {
                    "row": key,
                    "weighting": weighting,
                    "n_older": r["n_older"],
                    "n_benchmark": r["n_benchmark"],
                    "error_without_table_older": r["older"],
                    "error_without_table_benchmark": r["benchmark"],
                    "change": r["change"],
                    "ci95_low": ci[0],
                    "ci95_high": ci[1],
                    "se": r["se"],
                    "df": r["df"],
                    "detectable_80": r["detectable_80"],
                    "reading": r["reading"],
                }
            )
    return out


def g29a_gate(part: pd.DataFrame, e28_contrasts: dict) -> dict:
    """G29a for one version of the older-seasons test."""
    worst = g29a_differences(part, e28_contrasts)
    return passed(
        gate_max("G29a", worst, REPRO_TOLERANCE),
        negative_control(
            gate_max,
            "G29a",
            g29a_differences(part, e28_contrasts, shuffle=SHUFFLE_SEED),
            REPRO_TOLERANCE,
        ),
        tolerance=REPRO_TOLERANCE,
        control_input="the outcome column shuffled across rows",
    )


def version_gates(part: pd.DataFrame, frozen: pd.DataFrame, scoring: dict) -> dict:
    """After G29a: the frozen-forecast and scoring-run checks for one version."""
    gates = {}
    wf = e28.frozen_difference(part, frozen)
    gates["frozen_forecasts"] = passed(
        gate_max("frozen-forecast gate", wf, e28.EXACT_TOLERANCE),
        negative_control(
            gate_max,
            "frozen-forecast gate",
            e28.frozen_difference(part, frozen, shift=CONTROL_SHIFT),
            e28.EXACT_TOLERANCE,
        ),
        tolerance=e28.EXACT_TOLERANCE,
    )
    ws = e28.g28b_differences(part, scoring)
    gates["scoring_run"] = passed(
        gate_max("scoring-run gate", ws, REPRO_TOLERANCE),
        negative_control(
            gate_max,
            "scoring-run gate",
            e28.g28b_differences(part, scoring, shuffle=SHUFFLE_SEED),
            REPRO_TOLERANCE,
        ),
        tolerance=REPRO_TOLERANCE,
    )
    return gates


def identity_gate(populations: list) -> dict:
    """G29c over (rows, league column, table) of each population."""
    worst, control = {}, {}
    for index, (rows, column, table) in enumerate(populations):
        for k, v in g29c_differences(rows, column, table).items():
            worst[f"{index}:{k}"] = v
        dropped = sorted(rows[column].unique())[0]
        for k, v in g29c_differences(rows, column, table, drop=dropped).items():
            control[f"{index}:{k}"] = v
    return passed(
        gate_max("G29c", worst, REPRO_TOLERANCE),
        negative_control(gate_max, "G29c", control, REPRO_TOLERANCE),
        tolerance=REPRO_TOLERANCE,
        control_input="one league's rows dropped from the sum",
    )


def run(
    root: Path,
    input_dir: Path,
    frozen_path: Path,
    withheld_e28b: Path | None,
    out: Path,
) -> dict:
    root = Path(root)
    committed = load_committed(root)
    common.check_sha(frozen_path, FROZEN_SHA)
    release = json.loads((root / RELEASE).read_text())
    paper = json.loads((root / E27_PAPER).read_text())
    printed = e27p.printed_version(release)
    flag = bool(release[e27p.FLAG])
    e28_older = committed["e28"]["e28b"]
    if (
        paper["printed_version"] != printed
        or paper[e27p.FLAG] != flag
        or paper["sources"]["e27_arrivals.csv"] != COMMITTED["e27_arrivals"][1]
        or e28_older["printed_version"] != printed
        or e28_older[e27p.FLAG] != flag
    ):
        raise GateFailure(
            "the committed E27 extract or E28 output does not belong to this flag"
        )
    other = next(v for v in e27.VERSIONS if v != printed)
    e28_contrasts = {printed: e28_older["contrasts"]}
    if flag:
        e28_contrasts[other] = e28_older["other_version"]["contrasts"]
    else:
        if withheld_e28b is None:
            raise GateFailure(
                "G29a needs the withheld E28b record of the retained E28 run"
            )
        record = json.loads(Path(withheld_e28b).read_text())
        if record["version"] != other:
            raise GateFailure("G29a: the withheld E28b record is another version")
        e28_contrasts[other] = record["contrasts"]
    scored = committed["e27_arrivals"]
    frozen = pd.read_parquet(frozen_path)
    parts = {
        version: scored.loc[scored.league.isin(leagues)].reset_index(drop=True)
        for version, leagues in e27.VERSIONS.items()
    }
    # ---- G29a comes first: nothing else is computed before it holds
    older_gates = {}
    for version, part in parts.items():
        if len(part) != committed["e27_summary"]["versions"][version]["n"]:
            raise GateFailure("the scored rows are not the scoring run's arrivals")
        if not (np.isfinite(part[WEIGHT]) & (part[WEIGHT] > 0)).all():
            raise GateFailure("an older arrival has no positive destination minutes")
        older_gates[version] = {"G29a": g29a_gate(part, e28_contrasts[version])}
    gates = {"G29a": older_gates[printed]["G29a"]}
    for version, part in parts.items():
        older_gates[version].update(
            version_gates(part, frozen, committed["e27_summary"]["primary"][version])
        )

    # ---- the 674
    v9, v10_summary = common.load_references(root)
    rows, _, _ = common.anchor_rows(root, input_dir)
    diffs = common.g0_differences(rows, v9, v10_summary)
    g0_control = negative_control(common.assert_g0, diffs, tolerance=-1.0)
    common.assert_g0(diffs)
    gates["G0"] = passed(max(diffs.values()), g0_control, tolerance=common.G0_TOLERANCE)
    gates["scope"] = {
        "status": "passed",
        **dec.assert_scope(rows),
        "negative_control": negative_control(
            dec.assert_scope, rows, expected_targets=dec.EXPECTED_TARGETS + 1
        ),
    }
    if not (np.isfinite(rows[WEIGHT]) & (rows[WEIGHT] > 0)).all():
        raise GateFailure("a benchmark arrival has no positive destination minutes")
    wb = g29b_differences(rows, committed["e28"]["e28a"])
    gates["G29b"] = passed(
        gate_max("G29b", wb, REPRO_TOLERANCE),
        negative_control(
            gate_max,
            "G29b",
            g29b_differences(rows, committed["e28"]["e28a"], shift=CONTROL_SHIFT),
            REPRO_TOLERANCE,
        ),
        tolerance=REPRO_TOLERANCE,
        control_input=f"the league-aware forecast column shifted by {CONTROL_SHIFT}",
    )
    gates["frozen_forecasts"] = older_gates[printed]["frozen_forecasts"]
    gates["scoring_run"] = older_gates[printed]["scoring_run"]

    # ---- league names of the two populations, mapped explicitly
    maps = {}
    for version, leagues in e27.VERSIONS.items():
        maps[version] = league_map(parts[version], rows, leagues)
    gates["league_map"] = {
        "status": "passed",
        "leagues": maps[printed],
        "older_seasons": list(OLDER_SEASONS),
        "negative_control": negative_control(
            league_map, parts[printed], rows, (*e27.VERSIONS[printed], "nowhere")
        ),
    }

    # ---- E29a, E29b, E29c for each version
    result = {}
    for version, leagues in e27.VERSIONS.items():
        older = population_table(parts[version], "league", {k: k for k in leagues})
        recent = population_table(
            rows, "league_src", {k: e27.LEAGUES[k] for k in leagues}
        )
        block = changes(older, recent, leagues)
        result[version] = {
            "older": older,
            "benchmark": recent,
            "change": block,
            "licences": licences(older, block, leagues),
            "G29c": identity_gate(
                [(parts[version], "league", older), (rows, "league_src", recent)]
            ),
            "E24": e24_differences(
                recent, committed["e24_level"], committed["e24_leagues"]
            ),
        }
    mine = result[printed]
    gates["G29c"] = mine["G29c"]
    gates["E24_cross_check"] = passed(
        gate_max("E24 cross-check", mine["E24"], REPRO_TOLERANCE),
        negative_control(gate_max, "E24 cross-check", mine["E24"], -1.0),
        tolerance=REPRO_TOLERANCE,
    )
    leagues = e27.VERSIONS[printed]
    extra = [k for k in e27.VERSIONS[other] if k not in leagues]
    summary = {
        "analysis": "Amendment 11: E29 (descriptive; every outcome already seen)",
        "descriptive": True,
        "exploratory": True,
        "protocol_commit": common.PROTOCOL_COMMIT,
        "protocol_sha256": sha256_file(root / common.PROTOCOL),
        "amendment_commit": AMENDMENT_COMMIT,
        "amendment_sha256": sha256_file(root / AMENDMENT),
        "input_sha256": {
            "pairs": common.PAIRS_SHA["official_corrected"],
            "cohort": common.COHORT_SHA,
            "frozen_older_season_forecasts": FROZEN_SHA,
            **{relative: sha for relative, sha in COMMITTED.values()},
            E27_PAPER.as_posix(): sha256_file(root / E27_PAPER),
            RELEASE.as_posix(): sha256_file(root / RELEASE),
        },
        "exposure": EXPOSURE,
        "further_reading": FURTHER_READING,
        "printed_version": printed,
        e27p.FLAG: flag,
        "leagues": {k: LEAGUE_NAMES[k] for k in leagues},
        "estimator": {
            "quantities": {
                "move": "league-aware forecast minus destination-only forecast",
                "error_without_table": "destination-only forecast minus outcome",
                "error_with_table": "league-aware forecast minus outcome",
            },
            "arms": {"destination_only": D, "league_aware": O},
            "interval": "two-way clustered 95% interval (player, destination club-season), Student t with min(clusters) - 1 degrees of freedom",
            "weights": "destination minutes (minutes_dest)",
            "change": "error without the table, older arrivals minus arrivals of 2020-2025; the two samples treated as independent, standard errors combined in quadrature, the smaller of the two degrees of freedom",
            "detectable_80": "(t(0.975, df) + t(0.80, df)) x SE",
        },
        "gates": gates,
        "e29a": {"n": int(len(parts[printed])), "rows": mine["older"]},
        "e29b": {"n": int(len(rows)), "rows": mine["benchmark"]},
        "e29c": {"rows": mine["change"]},
        "licences": {
            **mine["licences"],
            "caveat": WORDING["caveat"],
            "limits": list(LIMITS),
            "no_cause": "The paper does not write that a league was stronger or weaker in either period, and does not write 'because'.",
        },
    }
    summary["sentences"] = [
        entry["unweighted"]["sentence"]
        for block in ("leagues", "change")
        for entry in mine["licences"][block].values()
        if entry["unweighted"].get("sentence")
    ]
    withheld = None
    if flag:
        summary["other_version"] = {
            "version": other,
            "e29a": {"n": int(len(parts[other])), "rows": result[other]["older"]},
            "e29b": {"n": int(len(rows)), "rows": result[other]["benchmark"]},
            "e29c": {"rows": result[other]["change"]},
            "licences": result[other]["licences"],
        }
        gates["other_version"] = {
            "status": "passed",
            **{k: v for k, v in older_gates[other].items()},
            "G29c": result[other]["G29c"],
            "negative_control": "rejected as required",
        }
    else:
        summary["withheld"] = {
            "version": other,
            "computed_in_the_same_run": True,
            "reason": "ACB's written permission had not arrived (Amendment 7's permission rule)",
        }
        theirs = result[other]
        withheld = {
            "version": other,
            "n": int(len(parts[other])),
            "league_map": {k: maps[other][k] for k in extra},
            "older_all_arrivals": theirs["older"][ALL],
            "extra_leagues": {
                k: {
                    "older": theirs["older"][k],
                    "benchmark": theirs["benchmark"][k],
                    "change": theirs["change"][k],
                    "licences": {
                        "league": theirs["licences"]["leagues"][k],
                        "change": theirs["licences"]["change"][k],
                    },
                }
                for k in extra
            },
            "consistent_with": theirs["licences"]["consistent_with"],
        }
    files = {
        "e29_means.csv": pd.DataFrame(
            table_rows(f"older arrivals ({printed})", mine["older"])
            + table_rows("arrivals of 2020-2025", mine["benchmark"])
        ).to_csv(index=False),
        "e29_change.csv": pd.DataFrame(change_rows(mine["change"])).to_csv(index=False),
    }
    planted = None
    if withheld is not None:
        value = withheld["older_all_arrivals"]["means"]["error_without_table"][
            "unweighted"
        ]["mean"]
        planted = negative_control(
            assert_no_leak,
            summary,
            {**files, "planted": repr(value)},
            leagues,
            withheld,
        )
    gates["G29d"] = {
        "status": "passed",
        "values_checked": assert_no_leak(summary, files, leagues, withheld),
        "files_checked": ["summary.json", *sorted(files)],
        "negative_control": planted,
    }

    out = Path(out)
    out.mkdir(parents=True, exist_ok=False)
    for name, text in files.items():
        (out / name).write_text(text)
    (out / "summary.json").write_text(
        json.dumps(clean(summary), indent=2, sort_keys=True) + "\n"
    )
    if withheld is not None:
        withheld["gates"] = {
            **older_gates[other],
            "G29c": result[other]["G29c"],
            "E24_cross_check_max_difference": max(result[other]["E24"].values()),
        }
        (out / "withheld").mkdir()
        (out / "withheld" / "e29_withheld_version.json").write_text(
            json.dumps(clean(withheld), indent=2, sort_keys=True) + "\n"
        )
    return summary


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument(
        "--frozen",
        type=Path,
        required=True,
        help="the frozen older-season forecasts of the Amendment 7 freeze run",
    )
    parser.add_argument(
        "--withheld-e28b",
        type=Path,
        default=None,
        help="the withheld-version record of the retained E28 run (needed while the permission flag is false)",
    )
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    summary = run(Path.cwd(), args.input_dir, args.frozen, args.withheld_e28b, args.out)
    for sentence in summary["sentences"]:
        print(sentence)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
