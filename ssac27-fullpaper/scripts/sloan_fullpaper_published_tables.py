#!/usr/bin/env python3
"""Amendment 15 analyses: E31a (EXPLORATORY) and the E31c frozen arm.

Pre-registration: docs/research/sloan-full-paper-preregistration-2026-11-03.md
(commit f52e7c831) and its Amendment 15,
docs/research/sloan-full-paper-preregistration-amendment-15-2026-11-17.md
(commit 48f752c68, pushed alone on 2026-11-17, before this file existed).

One rule for every published league table. The published-table forecast is
the registered destination-aware forecast (``history_destination_slope``)
plus one term: a single coefficient times the published score of the player's
source league. The coefficient is fitted without penalty, walk-forward, on the
same training arrivals as every other arm. Nothing else is tuned.

* ``e31a`` (exploratory; the 674 arrivals of 2020-2025 were examined before
  any registration): the published-table forecast's error, and its paired
  differences in mean absolute error (EFF/36) from the destination-only
  forecast and from the league-aware forecast, unweighted and weighted by
  destination minutes, each with the registered two-way clustered 95%
  interval (player, destination club-season) and the 80%-power detectable
  difference.
* ``freeze`` (E31c, registered before the 2026-27 test is scored): the same
  forecast fitted on arrivals through 2025, exactly as the frozen arms were,
  written for the same 3,478 rows as a SECOND file. The pinned frozen file is
  read, never rewritten. No 2026-27 statistic is read: the inputs are the
  pinned pool-A tables (destination seasons through 2025), the pinned frozen
  file and the published table.
* ``attach_frozen_arm`` and ``e31c_readout`` are for the scoring run: the
  hash check, gate G31b and the registered read-out (error; paired differences
  from the destination-only and the league-aware forecasts).

E31b (the league changes) is computed in E30's single scoring run and is not
in this file.

Threats and their controls (all in this file): drift from the submitted
numbers (G0, scope gate); a walk-forward path that is not the registered one
(G31a: before the published-table term is added, the registered errors of the
destination-only and league-aware forecasts to the printed digits and to 1e-9
against the committed summary, and this file's own fit without the term equal
to the registered destination-only forecast on every arrival; its control
shifts one forecast column); a table that only looks informative (G31a's
registered negative control: published scores shuffled across leagues must
give a paired difference from destination-only whose interval includes zero);
a table file that is not the registered one (pin gate: the twelve committed
values against the values printed in Amendment 15, read from the amendment at
run time; its control changes one score); a frozen arm fitted on other rows or
by another path (frozen-arm gate: the committed fitters on the training
arrivals reproduce the pinned frozen forecasts of three arms on all 3,478
rows; its control shifts one column); a frozen file that is incomplete or
changed (G31b: 3,478 rows, the keys of the pinned file, no missing forecast;
its control flips one byte and must fail the hash check).
"""

# ruff: noqa: E501, E741 -- gate messages and licensed sentences; O is the offsets arm
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
import re
import sys
import tempfile

for _name in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_name, "1")
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from scripts import sloan_context_benchmarks as benchmark  # noqa: E402
from scripts import sloan_fullpaper_amend1_decisions as a1  # noqa: E402
from scripts import sloan_fullpaper_amend9 as e28  # noqa: E402
from scripts import sloan_fullpaper_common as common  # noqa: E402
from scripts import sloan_fullpaper_decisions as dec  # noqa: E402
from scripts.translation_research_common import sha256_file  # noqa: E402

KEY = common.KEY
OUTCOME = dec.OUTCOME
WEIGHT = e28.WEIGHT
SPEC = e28.SPEC
AMENDMENT = Path(
    "docs/research/sloan-full-paper-preregistration-amendment-15-2026-11-17.md"
)
AMENDMENT_COMMIT = "48f752c68487e7c426fbe9817052bcf51276de85"

H, D, O = dec.HISTORY, e28.D, dec.OFFSETS
#: One published table per run. A further table needs a dated addendum to
#: Amendment 15 that Amir accepts; nothing here admits one.
TABLE_ID = "vashro_2015"
P = f"published_table_{TABLE_ID}"
P_SHUFFLED = f"{P}_shuffled"
SCORE_FEATURE = "published_score_source_league"
TABLE_DIR = Path("docs/research/artifacts/sloan-fullpaper-published-tables-2026-11")
TABLE = TABLE_DIR / f"{TABLE_ID}_competition_scores.csv"
TABLE_COLUMNS = (
    "league",
    "name_as_printed",
    "rank_as_printed",
    "first_year_as_printed",
    "last_year_as_printed",
    "score",
)
#: Amendment 15, "Pinned inputs": the name each venue is printed under in the
#: amendment, and the repository's key for it. No value is typed here: the
#: twelve values are read from the amendment at run time (``pinned_scores``).
PRINTED_NAMES = {
    "Spain ACB": "spain-acb",
    "Italy": "italy-lba",
    "VTB United League": "vtb",
    "Adriatic league": "aba-league",
    "Turkey BSL": "turkey-bsl",
    "France Pro A": "france-pro-a",
    "Germany BBL": "germany-bbl",
    "Israel": "israel-bsl",
    "Greece": "greece-a1",
    "Lithuania": "lithuania-lkl",
    "EuroLeague": "euroleague",
    "EuroCup": "eurocup",
}
CONTINENTAL = tuple(dec.DESTINATIONS)
SOURCE_LEAGUES = tuple(
    sorted(v for v in PRINTED_NAMES.values() if v not in CONTINENTAL)
)
PIN_ROW = "| The 2015 table"

LABELS = {
    D: "history + destination (blind to the source league)",
    O: "league-aware (the paper's one number per league)",
    P: "history + destination + one coefficient times the 2015 table's score of the source league",
}
#: name -> (left, right): the difference is MAE(left) - MAE(right), positive favours right.
CONTRASTS = {"T_D": (D, P), "T_O": (P, O)}
CONTRAST_LABELS = {
    "T_D": "published table against destination-only",
    "T_O": "league-aware against published table",
}
WEIGHTINGS = e28.WEIGHTINGS
#: Amendment 15, G31a: "the registered errors of the destination-only forecast
#: (2.989) and of the league-aware forecast (2.924) to the printed digits".
PRINTED_MAE = {D: "2.989", O: "2.924"}
REPRO_TOLERANCE = 1e-9
EXACT_TOLERANCE = 1e-12
CONTROL_SHIFT = 0.01
SHUFFLE_SEED = 20261117
RECIPES_SUMMARY = e28.COMMITTED["recipes"]

# ---- E31c
FREEZE_DIR = Path("docs/research/artifacts/sloan-fullpaper-p1-freeze-2026-11")
FROZEN = FREEZE_DIR / "p1_frozen_forecasts.parquet"
FREEZE_RECORD = FREEZE_DIR / "freeze.json"
#: The pinned frozen file of 3 November (public hash list, row 2).
FROZEN_SHA = "f3530c1a5ac369c032a996756ced226a93aa2d9f71d2e63aab21694de3d55316"
FROZEN_ROWS = 3478
FROZEN_KEY = ["player_name", "league_dest"]
FROZEN_GATE_ARMS = (H, D, O)
LAST_TRAINING_SEASON = 2025
E31C_FILE = "p1_frozen_published_table_forecasts.parquet"
E31C_RECORD = "e31c_freeze.json"
E31C_COLUMNS = (
    "player_name",
    "season_src",
    "league_src",
    "season_dest",
    "league_dest",
    SCORE_FEATURE,
    P,
    f"{P}_status",
)

EXPOSURE = {
    "seen_before_registration": [
        "the twelve values of the 2015 table, read on 17 November 2026 from the published article; its order agrees with Table 2 of the paper at the two ends and differs in the middle",
        "everything E31a uses on the 674 arrivals (outcomes, forecasts and errors of the registered arms), so E31a is exploratory",
    ],
    "not_seen_before_this_run": [
        "any correlation, error or forecast computed with the 2015 table",
        "any outcome of the frozen 2026-27 test or of the league changes of E30",
    ],
}

#: The wording column of Amendment 15, "What the paper may say", verbatim.
WORDING = {
    (
        "T_D",
        "above_zero",
    ): "a league table printed in 2015 improves a destination-aware forecast by X EFF/36 (interval)",
    (
        "T_D",
        "includes_zero",
    ): "a league table printed in 2015 adds nothing detectable to a destination-aware forecast (X, interval)",
    (
        "T_O",
        "above_zero",
    ): "the paper's league numbers are more accurate than the 2015 table by X EFF/36 (interval)",
    (
        "T_O",
        "includes_zero",
    ): "the paper's league numbers and a league table printed in 2015 are not distinguishable (X, interval; a difference of D would have been detected with 80% power)",
    (
        "T_O",
        "below_zero",
    ): "a league table printed in 2015 is more accurate than the paper's league numbers by X EFF/36 (interval)",
}
TO_AMIR = "It goes to Amir before any writing."
NOT_THE_SAME = '"Not distinguishable" is not "the same": the detectable difference is stated beside it and no equivalence is claimed.'
PURPOSE = "The 2015 table was built for a different purpose: the level of competition a prospect faced, for the NBA draft."


class GateFailure(common.GateFailure):
    """A registered Amendment 15 gate did not hold."""


negative_control = a1.negative_control
max_abs = a1.max_abs
gate_max = a1.gate_max
passed = a1.passed
clean = a1.clean
reading = e28.reading
gain = e28.gain
eff = e28.eff
span = e28.span


# ------------------------------------------------------------------ table --
def pinned_scores(amendment_text: str) -> dict:
    """The twelve values printed in Amendment 15, keyed by repository league."""
    rows = [line for line in amendment_text.splitlines() if line.startswith(PIN_ROW)]
    if len(rows) != 1:
        raise GateFailure("the amendment has no single row pinning the 2015 table")
    cell = rows[0].split("|")[2]
    values = cell.split(". The twelve values", 1)[0]
    out = {}
    for entry in values.split(";"):
        match = re.fullmatch(r"\s*(.+?)\s+(-?\d+\.\d+)\s*", entry)
        if not match or match.group(1) not in PRINTED_NAMES:
            raise GateFailure(f"unreadable pinned entry in the amendment: {entry!r}")
        league = PRINTED_NAMES[match.group(1)]
        if league in out:
            raise GateFailure(f"the amendment pins {league} twice")
        out[league] = float(match.group(2))
    if set(out) != set(PRINTED_NAMES.values()):
        raise GateFailure("the amendment does not pin all twelve venues")
    return out


def load_table(path: Path) -> pd.DataFrame:
    """The committed published table: twelve rows, one per venue, in the fixed shape."""
    frame = pd.read_csv(path)
    if tuple(frame.columns) != TABLE_COLUMNS:
        raise GateFailure(
            f"{path}: columns {list(frame.columns)} are not {list(TABLE_COLUMNS)}"
        )
    if len(frame) != len(PRINTED_NAMES) or frame.league.duplicated().any():
        raise GateFailure(f"{path}: expected {len(PRINTED_NAMES)} rows, one per venue")
    if set(frame.league) != set(PRINTED_NAMES.values()):
        odd = sorted(set(frame.league) ^ set(PRINTED_NAMES.values()))
        raise GateFailure(f"{path}: league keys differ from the repository's: {odd}")
    scores = pd.to_numeric(frame.score, errors="coerce").to_numpy(float)
    if not np.isfinite(scores).all():
        raise GateFailure(f"{path}: a score is missing or not a number")
    return frame.assign(score=scores)


def table_scores(table: pd.DataFrame) -> dict:
    return {str(k): float(v) for k, v in zip(table.league, table.score)}


def pin_differences(scores: dict, pinned: dict, *, shift: float = 0.0) -> dict:
    """|committed - registered| per venue; ``shift`` moves one score (the control)."""
    if set(scores) != set(pinned):
        return {"venues": math.inf}
    first = sorted(scores)[0]
    return {
        f"score:{k}": abs(scores[k] + (shift if k == first else 0.0) - pinned[k])
        for k in sorted(scores)
    }


def shuffled_scores(scores: dict, seed: int = SHUFFLE_SEED) -> dict:
    """The ten source-league scores permuted so that no league keeps its own."""
    leagues = [k for k in sorted(scores) if k in SOURCE_LEAGUES]
    values = [scores[k] for k in leagues]
    if len(set(values)) < 2:
        raise GateFailure(
            "the published scores cannot be shuffled: fewer than two values"
        )
    rng = np.random.default_rng(seed)
    for _ in range(10_000):
        order = rng.permutation(len(leagues))
        if all(values[j] != values[i] for i, j in enumerate(order)):
            return {**scores, **{k: values[j] for k, j in zip(leagues, order)}}
    raise GateFailure("no permutation moves every league's score")


# --------------------------------------------------------------- forecast --
def design(rows: pd.DataFrame, scores: dict | None = None):
    """The registered destination-aware design, plus the published score if given."""
    x, names = benchmark.model_matrix(rows, D)
    if scores is None:
        return x, list(names)
    unknown = sorted(set(rows.league_src) - set(scores))
    if unknown:
        raise GateFailure(f"no published score for source league(s): {unknown}")
    s = rows.league_src.map(scores).to_numpy(float)
    return np.column_stack([x, s]), [*names, SCORE_FEATURE]


def fit(train: pd.DataFrame, test: pd.DataFrame, scores: dict | None = None):
    """Ordinary least squares, no penalty; no test outcome enters the fit.

    With ``scores=None`` this is the registered ``history_destination_slope``
    (the same design and the same solver as ``benchmark.fit_model``).
    """
    x, names = design(train, scores)
    z, _ = design(test, scores)
    if not np.isfinite(x).all() or not np.isfinite(z).all():
        raise ValueError("nonfinite model input")
    rank = int(np.linalg.matrix_rank(x)) if len(x) else 0
    info = {
        "status": "ok",
        "train_n": int(len(train)),
        "unpenalized_rank": rank,
        "unpenalized_columns": int(x.shape[1]),
        "features": names,
    }
    if len(train) < x.shape[1] or rank != x.shape[1]:
        info["status"] = (
            "insufficient_training" if len(train) < x.shape[1] else "rank_deficient"
        )
        return np.full(len(test), np.nan), info
    outcome = train[OUTCOME].to_numpy(float)
    if not np.isfinite(outcome).all():
        raise ValueError("nonfinite training outcome")
    beta = np.linalg.lstsq(x, outcome, rcond=None)[0]
    prediction = z @ beta
    if not np.isfinite(prediction).all():
        raise ValueError("nonfinite fitted prediction")
    info["coefficients"] = beta.tolist()
    if scores is not None:
        info["score_coefficient"] = float(beta[names.index(SCORE_FEATURE)])
    return prediction, info


def training_rows(features: pd.DataFrame, season: int) -> pd.DataFrame:
    """The training arrivals of every arm at destination ``season``."""
    return features.loc[
        features.season_dest.lt(season) & features.feature_eligible
    ].sort_values(KEY)


def walk_forward(
    features: pd.DataFrame,
    scores: dict | None,
    *,
    name: str = P,
    seasons=common.ANCHOR_SEASONS,
):
    """One fit per destination season on earlier arrivals (as ``common.forecast``)."""
    out, folds = [], []
    for season in seasons:
        train = training_rows(features, season)
        test = features.loc[features.season_dest.eq(season)].sort_values(KEY)
        support = test.feature_eligible.astype(bool)
        block = test[KEY].copy()
        block[name] = np.nan
        info = {"status": "feature_refusal"}
        if support.any():
            prediction, info = fit(train, test.loc[support], scores)
            block.loc[support.to_numpy(), name] = prediction
        folds.append({"season": int(season), "test_n": int(len(test)), **info})
        out.append(block)
    return pd.concat(out, ignore_index=True), folds


def attach(rows: pd.DataFrame, forecasts: pd.DataFrame, name: str) -> pd.DataFrame:
    """Join a forecast to the fixed targets; an unscorable target is a failure."""
    merged = rows.merge(forecasts[[*KEY, name]], on=KEY, how="left", validate="1:1")
    if not np.isfinite(merged[name].to_numpy(float)).all():
        raise GateFailure(
            f"{int(merged[name].isna().sum())} targets have no {name} forecast"
        )
    return merged


# ------------------------------------------------------------- statistics --
def arm_errors(rows: pd.DataFrame, arms) -> dict:
    return e28.arm_errors(rows, arms)


def contrasts(rows: pd.DataFrame, pairs=None) -> dict:
    pairs = CONTRASTS if pairs is None else pairs
    return {
        name: {
            "left": left,
            "right": right,
            **{
                w: gain(rows, left, right, weighted=w != "unweighted")
                for w in WEIGHTINGS
            },
        }
        for name, (left, right) in pairs.items()
    }


def flat(blocks: dict) -> list:
    return [
        {**row, "contrast": CONTRAST_LABELS.get(row["difference_name"], "")}
        for row in e28.flat("the 674 arrivals of 2020-2025", blocks)
    ]


# --------------------------------------------------------------- licences --
def _unregistered(record: dict) -> dict:
    return {
        "reading": record["reading"],
        "registered_wording": None,
        "sentence": None,
        "note": f"Amendment 15 registers no wording for this reading. {TO_AMIR}",
    }


def licence(name: str, record: dict) -> dict:
    """Amendment 15, "What the paper may say", applied to one difference."""
    r = record["reading"]
    if (name, r) not in WORDING:
        return _unregistered(record)
    x, ci = record["difference"], record["ci95"]
    out = {"reading": r, "registered_wording": WORDING[(name, r)]}
    if name == "T_D" and r == "above_zero":
        out["sentence"] = (
            f"a league table printed in 2015 improves a destination-aware forecast by {eff(x)} EFF/36 ({span(ci)})"
        )
    elif name == "T_D":
        out["sentence"] = (
            f"a league table printed in 2015 adds nothing detectable to a destination-aware forecast ({eff(x)}, {span(ci)})"
        )
    elif r == "above_zero":
        out["sentence"] = (
            f"the paper's league numbers are more accurate than the 2015 table by {eff(x)} EFF/36 ({span(ci)})"
        )
    elif r == "includes_zero":
        out["sentence"] = (
            f"the paper's league numbers and a league table printed in 2015 are not distinguishable ({eff(x)}, {span(ci)}; "
            f"a difference of {eff(record['detectable_80'])} would have been detected with 80% power)"
        )
        out["note"] = NOT_THE_SAME
    else:
        out["sentence"] = (
            f"a league table printed in 2015 is more accurate than the paper's league numbers by {eff(-x)} EFF/36 ({span([-ci[1], -ci[0]])})"
        )
        out["note"] = TO_AMIR
    return out


def licences(blocks: dict) -> dict:
    """The registered wording filled for each difference and each weighting.

    Amendment 15 lists both weightings under E31a and one wording per interval
    reading. It does not say which weighting a sentence follows; that choice is
    not made here (``escalation`` reports a disagreement).
    """
    return {
        name: {w: licence(name, block[w]) for w in WEIGHTINGS}
        for name, block in blocks.items()
    }


def escalation(blocks: dict) -> dict:
    """What must go to Amir before any writing (Amendment 15)."""
    reasons = []
    for w in WEIGHTINGS:
        t_o, t_d = blocks["T_O"][w], blocks["T_D"][w]
        if t_o["difference"] is not None and t_o["difference"] <= 0:
            reasons.append(
                f"{w}: the 2015 table is at least as accurate as the paper's league numbers (MAE {eff(t_o['mae_left'])} against {eff(t_o['mae_right'])})"
            )
        if t_o["reading"] == "below_zero":
            reasons.append(
                f"{w}: the interval of the league-aware forecast against the 2015 table lies below zero"
            )
        if t_d["reading"] not in ("above_zero", "includes_zero"):
            reasons.append(
                f"{w}: no wording is registered for this reading of the 2015 table against destination-only ({t_d['reading']})"
            )
    differ = sorted(
        name
        for name, block in blocks.items()
        if len({block[w]["reading"] for w in WEIGHTINGS}) > 1
    )
    if differ:
        reasons.append(
            "the two weightings read differently for "
            + ", ".join(differ)
            + "; Amendment 15 does not say which weighting the registered sentence follows"
        )
    return {
        "to_amir_before_any_writing": bool(reasons),
        "reasons": reasons,
        "rule": "A result in which the 2015 table is at least as accurate as the paper's league numbers goes to Amir before any writing (Amendment 15); read here on the point estimates, for either weighting.",
    }


# ------------------------------------------------------------------ gates --
def g31a_differences(
    rows: pd.DataFrame,
    recipes_summary: dict,
    reproduced: pd.DataFrame,
    *,
    shift: float = 0.0,
) -> dict:
    """The registered errors, and this file's fit without the published term.

    ``shift`` moves the destination-only forecast column (the control).
    """
    if shift:
        rows = rows.assign(**{D: rows[D] + shift})
    metrics = recipes_summary["results"]["A"]["R1"]["metrics"]
    worst = {}
    for arm in (D, O):
        mine = common.mae(rows, arm)
        worst[f"mae:{arm}"] = abs(mine - metrics[arm]["mae"])
        worst[f"printed_mae:{arm}"] = (
            0.0 if f"{mine:.3f}" == PRINTED_MAE[arm] else math.inf
        )
    merged = rows[[*KEY, D]].merge(
        reproduced[[*KEY, "reproduced"]], on=KEY, how="left", validate="1:1"
    )
    worst["own_fit_without_the_term"] = max_abs(merged[D], merged["reproduced"])
    return worst


def assert_includes_zero(records: dict) -> None:
    """G31a's registered negative control: shuffled scores add nothing detectable."""
    bad = [w for w in WEIGHTINGS if records[w]["reading"] != "includes_zero"]
    if bad:
        raise GateFailure(
            "G31a negative control: with published scores shuffled across leagues the paired difference "
            f"from destination-only does not include zero ({', '.join(bad)})"
        )


def frozen_training(features: pd.DataFrame) -> pd.DataFrame:
    """Arrivals through 2025: the rows every frozen arm was trained on."""
    if int(features.season_dest.max()) > LAST_TRAINING_SEASON:
        raise GateFailure("training inputs reach past destination 2025")
    return training_rows(features, LAST_TRAINING_SEASON + 1)


def frozen_arm_differences(
    train: pd.DataFrame, frozen: pd.DataFrame, *, shift: float = 0.0
) -> dict:
    """The committed fitters on ``train`` against the pinned frozen forecasts."""
    worst = {}
    for arm in FROZEN_GATE_ARMS:
        prediction, info = benchmark.fit_model(train, frozen, arm)
        if info["status"] != "ok":
            return {f"status:{arm}": math.inf}
        pinned = frozen[arm].to_numpy(float) + (shift if arm == D else 0.0)
        worst[f"frozen:{arm}"] = max_abs(prediction, pinned)
    prediction, info = fit(train, frozen, None)
    worst["own_fit_without_the_term"] = (
        max_abs(prediction, frozen[D].to_numpy(float) + shift)
        if info["status"] == "ok"
        else math.inf
    )
    return worst


def g31b_differences(arm: pd.DataFrame, frozen: pd.DataFrame) -> dict:
    """Counts that must all be zero: rows, keys, order and missing forecasts."""
    worst = {
        "rows_expected": float(abs(len(arm) - FROZEN_ROWS)),
        "rows_pinned_file": float(abs(len(arm) - len(frozen))),
        "duplicate_keys": float(arm.duplicated(FROZEN_KEY).sum()),
        "missing_forecasts": float((~np.isfinite(arm[P].to_numpy(float))).sum()),
    }
    if len(arm) == len(frozen):
        same = (
            arm[FROZEN_KEY].reset_index(drop=True).astype(str)
            == frozen[FROZEN_KEY].reset_index(drop=True).astype(str)
        ).all(axis=1)
        worst["keys_differ_from_pinned_file"] = float((~same).sum())
    else:
        worst["keys_differ_from_pinned_file"] = math.inf
    return worst


def changed_byte_control(path: Path, expected: str) -> str:
    """G31b's negative control: a changed byte must fail the hash check."""
    data = bytearray(Path(path).read_bytes())
    data[len(data) // 2] ^= 0x01
    with tempfile.TemporaryDirectory() as tmp:
        copy = Path(tmp) / Path(path).name
        copy.write_bytes(bytes(data))
        return negative_control(common.check_sha, copy, expected)


# ------------------------------------------------------------------- E31a --
def run_e31a(root: Path, input_dir: Path, table_path: Path, out: Path) -> dict:
    root = Path(root)
    relative, expected = RECIPES_SUMMARY
    common.check_sha(root / relative, expected)
    recipes_summary = json.loads((root / relative).read_text())
    v9, v10_summary = common.load_references(root)
    rows, features, _ = common.anchor_rows(root, input_dir)
    gates = {}

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

    # ---- G31a, first part: before the published-table term is added
    reproduced, _ = walk_forward(features, None, name="reproduced")
    wa = g31a_differences(rows, recipes_summary, reproduced)
    control = g31a_differences(rows, recipes_summary, reproduced, shift=CONTROL_SHIFT)
    gates["G31a"] = passed(
        gate_max("G31a", wa, REPRO_TOLERANCE),
        negative_control(gate_max, "G31a", control, REPRO_TOLERANCE),
        tolerance=REPRO_TOLERANCE,
        checked=sorted(wa),
        control_input=f"the destination-only forecast column shifted by {CONTROL_SHIFT}",
    )

    # ---- only now the table: its shape, and the values registered in Amendment 15
    table = load_table(table_path)
    scores = table_scores(table)
    pinned = pinned_scores((root / AMENDMENT).read_text())
    wp = pin_differences(scores, pinned)
    gates["table_pin"] = passed(
        gate_max("table pin", wp, EXACT_TOLERANCE),
        negative_control(
            gate_max,
            "table pin",
            pin_differences(scores, pinned, shift=CONTROL_SHIFT),
            EXACT_TOLERANCE,
        ),
        tolerance=EXACT_TOLERANCE,
        venues=len(wp),
        control_input=f"one committed score moved by {CONTROL_SHIFT}",
    )
    unknown = sorted(set(features.league_src) - set(SOURCE_LEAGUES))
    if unknown:
        raise GateFailure(f"arrivals from a league the table does not cover: {unknown}")

    # ---- G31a, registered negative control: scores shuffled across leagues
    shuffle = shuffled_scores(scores)
    shuffled_forecast, _ = walk_forward(features, shuffle, name=P_SHUFFLED)
    shuffled_rows = attach(rows, shuffled_forecast, P_SHUFFLED)
    shuffled = contrasts(shuffled_rows, {"shuffled": (D, P_SHUFFLED)})["shuffled"]
    assert_includes_zero(shuffled)
    gates["G31a"]["registered_negative_control"] = {
        "status": "passed",
        "input": "the ten source-league scores permuted so that no league keeps its own",
        "seed": SHUFFLE_SEED,
        "shuffled_scores": {k: shuffle[k] for k in SOURCE_LEAGUES},
        **{
            w: {k: shuffled[w][k] for k in ("difference", "ci95", "reading")}
            for w in WEIGHTINGS
        },
        "control_of_the_control": negative_control(
            assert_includes_zero,
            {w: {"reading": "above_zero"} for w in WEIGHTINGS},
        ),
    }

    # ---- E31a: the published-table forecast on the 674
    forecast, folds = walk_forward(features, scores)
    rows = attach(rows, forecast, P)
    blocks = contrasts(rows)
    licensed = licences(blocks)
    escalate = escalation(blocks)
    table_rows = pd.DataFrame(flat(blocks))
    sentences = [
        entry["sentence"]
        for name in CONTRASTS
        for entry in licensed[name].values()
        if entry.get("sentence")
    ]
    summary = {
        "analysis": "Amendment 15: E31a (exploratory; destination seasons 2020-2025 already seen)",
        "exploratory": True,
        "protocol_commit": common.PROTOCOL_COMMIT,
        "protocol_sha256": sha256_file(root / common.PROTOCOL),
        "amendment_commit": AMENDMENT_COMMIT,
        "amendment_sha256": sha256_file(root / AMENDMENT),
        "input_sha256": {
            "pairs": common.PAIRS_SHA["official_corrected"],
            "cohort": common.COHORT_SHA,
            relative: expected,
            TABLE.as_posix(): sha256_file(table_path),
        },
        "table": {
            "id": TABLE_ID,
            "file": TABLE.as_posix(),
            "sha256": sha256_file(table_path),
            "scores_used": {k: scores[k] for k in SOURCE_LEAGUES},
            "purpose": PURPOSE,
        },
        "exposure": EXPOSURE,
        "n_targets": int(len(rows)),
        "models": LABELS,
        "estimator": {
            "forecast": f"{D} plus one unpenalised coefficient times the published score of the source league, fitted walk-forward on the training arrivals of every other arm",
            "differences": {
                k: f"MAE({left}) - MAE({right})"
                for k, (left, right) in CONTRASTS.items()
            },
            "interval": "two-way clustered 95% interval (player, destination club-season), Student t with min(clusters) - 1 degrees of freedom",
            "weights": "destination minutes (minutes_dest)",
            "detectable_80": "(t(0.975, df) + t(0.80, df)) x SE, the registered formula of the recipes track",
        },
        "gates": gates,
        "e31a": {
            "n": int(len(rows)),
            "mae": arm_errors(rows, (D, O, P)),
            "total_minutes": float(rows[WEIGHT].sum()),
            "contrasts": blocks,
            "licences": licensed,
            "escalation": escalate,
            "folds": [
                {
                    k: fold.get(k)
                    for k in (
                        "season",
                        "train_n",
                        "test_n",
                        "status",
                        "score_coefficient",
                    )
                }
                for fold in folds
            ],
        },
        "sentences": sentences,
    }
    out = Path(out)
    out.mkdir(parents=True, exist_ok=False)
    table_rows.to_csv(out / "e31a_differences.csv", index=False)
    pd.DataFrame(summary["e31a"]["folds"]).to_csv(
        out / "e31a_coefficients.csv", index=False
    )
    rows[[*KEY, "league_src", "cluster", WEIGHT, OUTCOME, D, O, P]].sort_values(
        KEY
    ).to_csv(out / "e31a_keyed_forecasts.csv", index=False)
    (out / "summary.json").write_text(
        json.dumps(clean(summary), indent=2, sort_keys=True) + "\n"
    )
    return summary


# ------------------------------------------------------------------- E31c --
def frozen_arm(train: pd.DataFrame, frozen: pd.DataFrame, scores: dict):
    """The published-table forecast for every pinned frozen row, in its order."""
    support = frozen.feature_eligible.astype(bool).to_numpy()
    prediction = np.full(len(frozen), np.nan)
    info = {"status": "feature_refusal"}
    if support.any():
        prediction[support], info = fit(train, frozen.loc[support], scores)
    arm = frozen[
        ["player_name", "season_src", "league_src", "season_dest", "league_dest"]
    ].copy()
    arm[SCORE_FEATURE] = frozen.league_src.map(scores).to_numpy(float)
    arm[P] = prediction
    arm[f"{P}_status"] = np.where(support, info["status"], "feature_refusal")
    return arm[list(E31C_COLUMNS)].reset_index(drop=True), info


def run_freeze(root: Path, input_dir: Path, table_path: Path, out: Path) -> dict:
    root = Path(root)
    frozen_path = root / FROZEN
    common.check_sha(frozen_path, FROZEN_SHA)
    record = json.loads((root / FREEZE_RECORD).read_text())
    if record["forecast_sha256"] != FROZEN_SHA or record["rows"] != FROZEN_ROWS:
        raise GateFailure("the freeze record does not describe the pinned frozen file")
    frozen = pd.read_parquet(frozen_path)
    if len(frozen) != FROZEN_ROWS or frozen.duplicated(FROZEN_KEY).any():
        raise GateFailure("the pinned frozen file is not 3,478 unique rows")
    pairs, cohort = common.load_pool(input_dir, "official_corrected")
    if int(pairs.season.max()) > LAST_TRAINING_SEASON:
        raise GateFailure("training inputs reach past destination 2025")
    features, _ = common.build_features(pairs, cohort)
    train = frozen_training(features)
    if len(train) != record["training_rows"]:
        raise GateFailure(
            f"{len(train)} training arrivals, the freeze record has {record['training_rows']}"
        )
    gates = {}
    wf = frozen_arm_differences(train, frozen)
    gates["frozen_arms"] = passed(
        gate_max("frozen-arm gate", wf, REPRO_TOLERANCE),
        negative_control(
            gate_max,
            "frozen-arm gate",
            frozen_arm_differences(train, frozen, shift=CONTROL_SHIFT),
            REPRO_TOLERANCE,
        ),
        tolerance=REPRO_TOLERANCE,
        checked=sorted(wf),
        rows=int(len(frozen)),
        control_input=f"the pinned destination-only forecast column shifted by {CONTROL_SHIFT}",
    )
    # ---- only now the table
    table = load_table(table_path)
    scores = table_scores(table)
    pinned = pinned_scores((root / AMENDMENT).read_text())
    wp = pin_differences(scores, pinned)
    gates["table_pin"] = passed(
        gate_max("table pin", wp, EXACT_TOLERANCE),
        negative_control(
            gate_max,
            "table pin",
            pin_differences(scores, pinned, shift=CONTROL_SHIFT),
            EXACT_TOLERANCE,
        ),
        tolerance=EXACT_TOLERANCE,
        venues=len(wp),
        control_input=f"one committed score moved by {CONTROL_SHIFT}",
    )
    arm, info = frozen_arm(train, frozen, scores)
    wb = g31b_differences(arm, frozen)
    gate_max("G31b", wb, 0.0)
    out = Path(out)
    out.mkdir(parents=True, exist_ok=False)
    path = out / E31C_FILE
    arm.to_parquet(path, index=False)
    digest = sha256_file(path)
    reread = pd.read_parquet(path)
    gate_max("G31b (file as written)", g31b_differences(reread, frozen), 0.0)
    gates["G31b"] = passed(
        max(wb.values()),
        changed_byte_control(path, digest),
        tolerance=0.0,
        checked=sorted(wb),
        control_input="one byte of the written file flipped; the hash check must refuse it",
        control_of_the_counts=negative_control(
            gate_max, "G31b", g31b_differences(arm.iloc[:-1], frozen), 0.0
        ),
    )
    if sha256_file(frozen_path) != FROZEN_SHA:
        raise GateFailure("the pinned frozen file changed during the run")
    result = {
        "analysis": "Amendment 15: E31c, the published-table forecast frozen for the 2026-27 test",
        "status": "frozen",
        "protocol_commit": common.PROTOCOL_COMMIT,
        "amendment_commit": AMENDMENT_COMMIT,
        "amendment_sha256": sha256_file(root / AMENDMENT),
        "generating_commit": _manifest_commit(root),
        "arm": P,
        "forecast_file": E31C_FILE,
        "forecast_sha256": digest,
        "rows": int(len(arm)),
        "key": FROZEN_KEY,
        "pinned_frozen_file": FROZEN.as_posix(),
        "pinned_frozen_sha256": FROZEN_SHA,
        "pinned_frozen_file_rewritten": False,
        "table": {
            "id": TABLE_ID,
            "file": TABLE.as_posix(),
            "sha256": sha256_file(table_path),
        },
        "training_rows": int(len(train)),
        "last_training_destination_season": LAST_TRAINING_SEASON,
        "fit": {
            k: info.get(k)
            for k in (
                "status",
                "train_n",
                "features",
                "coefficients",
                "score_coefficient",
            )
        },
        "pairs_sha256": common.PAIRS_SHA["official_corrected"],
        "cohort_sha256": common.COHORT_SHA,
        "reads_2026_27_statistics": False,
        "gates": gates,
    }
    (out / E31C_RECORD).write_text(
        json.dumps(clean(result), indent=2, sort_keys=True) + "\n"
    )
    print(f"E31c frozen: {len(arm)} rows; sha256 {digest}")
    return result


def _manifest_commit(root: Path) -> str | None:
    path = Path(root) / "MANIFEST.json"
    if path.is_file():
        return json.loads(path.read_text()).get("commit")
    return None


# ------------------------------------------------- E31c at the scoring run --
def read_frozen_arm(
    path: Path, expected_sha: str, frozen: pd.DataFrame
) -> pd.DataFrame:
    """The frozen published-table forecasts, after the hash check and G31b."""
    common.check_sha(Path(path), expected_sha)
    arm = pd.read_parquet(path)
    gate_max("G31b", g31b_differences(arm, frozen), 0.0)
    return arm


def attach_frozen_arm(scored_rows: pd.DataFrame, arm: pd.DataFrame) -> pd.DataFrame:
    """Join the frozen arm to the scorer's newcomer rows; none may be lost."""
    merged = scored_rows.merge(
        arm[[*FROZEN_KEY, P]], on=FROZEN_KEY, how="left", validate="1:1"
    )
    if not np.isfinite(merged[P].to_numpy(float)).all():
        raise GateFailure("a scored newcomer has no frozen published-table forecast")
    return merged


def e31c_readout(rows: pd.DataFrame) -> dict:
    """Amendment 15, E31c: error, and the two paired differences, on scored rows.

    ``rows``: the scorer's newcomer rows with the frozen arm attached. The
    reading rules are those of Amendment 8 and belong to the scoring run.
    """
    return {
        "n": int(len(rows)),
        "mae": arm_errors(rows, (D, O, P)),
        "contrasts": contrasts(rows),
        "expectation": "As for S2 of Amendment 8, no difference is expected to be detectable in November.",
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("e31a", "freeze"):
        s = sub.add_parser(name)
        s.add_argument("--input-dir", type=Path, required=True)
        s.add_argument(
            "--table", type=Path, required=True, help=f"the committed {TABLE.name}"
        )
        s.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.command == "e31a":
        summary = run_e31a(Path.cwd(), args.input_dir, args.table, args.out)
        for sentence in summary["sentences"]:
            print(sentence)
        if summary["e31a"]["escalation"]["to_amir_before_any_writing"]:
            print(
                "TO AMIR BEFORE ANY WRITING:",
                *summary["e31a"]["escalation"]["reasons"],
                sep="\n  ",
            )
    else:
        run_freeze(Path.cwd(), args.input_dir, args.table, args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
