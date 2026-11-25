#!/usr/bin/env python3
"""Amendment 9 analysis: E28 (EXPLORATORY).

Pre-registration: docs/research/sloan-full-paper-preregistration-2026-11-03.md
(commit f52e7c831) and its Amendment 9,
docs/research/sloan-full-paper-preregistration-amendment-9-2026-11-16.md
(commit 3c915869c, pushed alone on 2026-11-16, before this file existed).
Destination seasons 2020-2025 were examined before any registration and the
older seasons were scored under Amendment 7, so every number here is
exploratory.

E28 -- what the league-aware forecast is worth against the plain baselines,
with intervals. Two paired differences in mean absolute error (EFF/36):
G_H = MAE(history only) - MAE(league-aware) and G_D = MAE(history +
destination) - MAE(league-aware), each unweighted and weighted by destination
minutes, each with the registered two-way clustered 95% interval (player,
destination club-season).

* E28a: the 674 benchmark arrivals of 2020-2025. Printed beside the results
  without a licence: both differences by destination competition and by
  destination season, and the 80%-power detectable effect of each.
* E28b: the older-seasons arrivals of Amendment 7 (E27), from the frozen
  older-season forecasts and the scored rows of the single E27 scoring run.
  Nothing is re-scored and no E27 rule changes. Both versions (with and
  without ACB) are computed here; only the version the paper prints under
  Amendment 7's permission rule goes into ``summary.json`` and the CSV tables.
  The other one is written to ``withheld/`` in the retained run and is never
  committed.
* E28c: the registered margin (2% of forecast error) and the registered
  head-to-head interval, each divided by the point estimate of G_D on the 674
  (arithmetic on registered numbers, descriptive).

No model is refitted: the forecasts are the committed walk-forward forecasts
of the registered arms.

Threats and their controls (all in this file): drift from the submitted
numbers (G0, scope gate); arms or a head-to-head that are not the registered
ones (G28a: the three registered errors to the printed digits and to 1e-9, the
registered head-to-head with its interval, the committed minutes-weighted
head-to-head and the equal-weight reduction of the weighted interval; its
negative control shifts one forecast column by 0.01); older rows that are not
the scored E27 rows or forecasts that are not the frozen ones (frozen-forecast
gate; G28b: the three printed comparisons of the Amendment 7 extract to 1e-9
before G_H and G_D are computed; its negative control shuffles the outcome
column); a withheld number reaching a committed file (leak gate with a
planted-value control). No 2026-27 statistic is read.
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
import sys

for _name in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_name, "1")
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from scripts import sloan_fullpaper_amend1_decisions as a1  # noqa: E402
from scripts import sloan_fullpaper_common as common  # noqa: E402
from scripts import sloan_fullpaper_decisions as dec  # noqa: E402
from scripts import sloan_fullpaper_older_seasons as e27  # noqa: E402
from scripts import sloan_fullpaper_older_seasons_paper as e27p  # noqa: E402
from scripts import sloan_fullpaper_recipes as recipes  # noqa: E402
from scripts import sloan_fullpaper_survivorship as surv  # noqa: E402
from scripts.translation_research_common import sha256_file  # noqa: E402

KEY = common.KEY
OUTCOME = dec.OUTCOME
WEIGHT = "minutes_dest"
SPEC = "player_club_season"
AMENDMENT = Path(
    "docs/research/sloan-full-paper-preregistration-amendment-9-2026-11-16.md"
)
AMENDMENT_COMMIT = "3c915869cbf2af11c2b383e5a0d8aabec0e75b70"

H, HT, O = dec.HISTORY, dec.HISTORY_T, dec.OFFSETS
D = "history_destination_slope"
ARMS = (H, D, O)
LABELS = {
    H: "history only (blind to both leagues)",
    D: "history + destination (blind to the source league)",
    O: "league-aware (one number per league)",
}
#: name -> (left, right): the difference is MAE(left) - MAE(right), positive favours right.
GAINS = {"G_H": (H, O), "G_D": (D, O)}
HEAD_TO_HEAD = (HT, O)
WEIGHTINGS = ("unweighted", "minutes_weighted")
#: Amendment 9, G28a: "3.096, 2.989, 2.924 to the printed digits".
PRINTED_MAE = {H: "3.096", D: "2.989", O: "2.924"}
#: Amendment 9, E28c: "the registered margin (2% of forecast error, 0.058 EFF/36)".
PRINTED_MARGIN = "0.058"
REPRO_TOLERANCE = 1e-9
EXACT_TOLERANCE = 1e-12
CONTROL_SHIFT = 0.01
SHUFFLE_SEED = 20261116

#: Committed files this analysis reads, each checked against its sha256.
COMMITTED = {
    "recipes": (
        "docs/research/artifacts/sloan-fullpaper-recipes-2026-11/summary.json",
        "e4d826741bd4f629c713216cd592e19ae7d2d2a89b77fad2cbe7ed350c51d030",
    ),
    "amend1": (
        "docs/research/artifacts/sloan-fullpaper-amend1-decisions-2026-11/summary.json",
        "94a1bb6576234d6f94bff9da12293799cca4ff71fa4d6589d7a30169e8935fe9",
    ),
    "e27_arrivals": (
        "docs/research/artifacts/sloan-fullpaper-older-seasons-2026-11/e27_arrivals.csv",
        "7356ba0bd35945ea8fb8a152d2d167c5dc1eb4d0f7849a08f627cf172ae3a800",
    ),
    "e27_summary": (
        "docs/research/artifacts/sloan-fullpaper-older-seasons-2026-11/e27_summary.json",
        "cf81c15dbc900b099fd887683a091b5d8ffcd6767eaab15fe588d8374fe5b53b",
    ),
}
#: Not pinned by hash: the extract and the flag change when the permission arrives.
E27_PAPER = Path(
    "docs/research/artifacts/sloan-fullpaper-older-seasons-paper-2026-11/e27_paper.json"
)
RELEASE = e27p.RELEASE
#: sha256 of the frozen older-season forecasts (Amendment 7, gate G27e).
FROZEN_SHA = "1d3e3bfb9d08b9d034668dac238e316cb96c4a548af689a3acf7435224df3027"
FROZEN_KEY = ["frozen_key", "league_dest"]
OLDER_ARMS = (H, HT, D, O, dec.OFFSETS_T)

EXPOSURE = {
    "seen_before_registration": [
        "the registered errors of the three forecasts on the 674 (3.096, 2.989, 2.924), so both point estimates by subtraction (0.172 and 0.065 EFF/36)",
        "the minutes-weighted errors of the history-only and league-aware forecasts on the 674 (Amendment 1, E17), so the weighted point estimate of G_H by subtraction",
        "every Amendment 7 comparison on the older seasons, in both versions, and the errors of the history-only and league-aware forecasts there (so G_H's point estimate by subtraction)",
        "that three readers of the paper asked for these intervals (review of 15 November)",
    ],
    "not_seen_before_this_run": [
        "any interval of G_H or G_D",
        "the minutes-weighted G_D, and the interval of the minutes-weighted G_H",
        "G_D on the older seasons, in either version",
        "either difference by destination competition or by destination season",
        "the per-arrival differences",
    ],
}
SECOND_READING = "The older-seasons outcomes were read once, in the single Amendment 7 scoring run; E28b is a second reading of them. No rule of that run is changed and nothing is re-scored."

#: The wording column of Amendment 9, "What the paper may say", verbatim.
WORDING = {
    (
        "G_H",
        "above_zero",
    ): "the league-aware forecast is more accurate than history alone by X EFF/36 (interval)",
    ("G_H", "includes_zero"): "not distinguishable from history alone at this n",
    (
        "G_D",
        "above_zero",
    ): "once the destination is known, knowing the source league improves the forecast by X EFF/36 (interval)",
    (
        "G_D",
        "includes_zero",
    ): "once the destination is known, the source league's contribution (X EFF/36) is not distinguishable from zero at this n",
    (
        "weighted",
        "includes_zero",
    ): "not clearly above zero when weighted by playing time",
    ("older", "above_zero"): "also on the older seasons",
    ("older", "includes_zero"): "not detectable on the older seasons at this n",
    ("E28c", "above_zero"): "the margin is X% of what the source league adds",
    (
        "E28c",
        "includes_zero",
    ): "the margin cannot be scaled against an effect that is itself not distinguishable from zero",
}
LEAD = {
    "G_H": "the league-aware forecast is more accurate than history alone",
    "G_D": "once the destination is known, knowing the source league improves the forecast",
}


class GateFailure(common.GateFailure):
    """A registered Amendment 9 gate did not hold."""


negative_control = a1.negative_control
max_abs = a1.max_abs
gate_max = a1.gate_max
passed = a1.passed
clean = a1.clean


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
def reading(ci95) -> str:
    if ci95 is None:
        return "not_estimable"
    if ci95[0] > 0:
        return "above_zero"
    if ci95[1] < 0:
        return "below_zero"
    return "includes_zero"


def gain(rows: pd.DataFrame, left: str, right: str, *, weighted: bool = False) -> dict:
    """Paired MAE(left) - MAE(right) with the registered two-way clustered interval.

    Unweighted: ``common.contrast`` (the registered estimator). Weighted by
    destination minutes: E14b's ``weighted_interval`` (the same estimator with
    weighted scores; identical when every weight is 1).
    """
    rows = rows.reset_index(drop=True)
    y = rows[OUTCOME].to_numpy(float)
    e_left = np.abs(rows[left].to_numpy(float) - y)
    e_right = np.abs(rows[right].to_numpy(float) - y)
    if weighted:
        w = rows[WEIGHT].to_numpy(float)
        block = surv.weighted_interval(
            e_left - e_right, w, rows.player_name, rows.cluster
        )
    else:
        w = np.ones(len(rows))
        block = common.contrast(rows, left, right)[SPEC]
    parent = float(np.sum(w * e_left) / np.sum(w))
    record = {
        "left": left,
        "right": right,
        "positive_favours": right,
        "weighting": "minutes_weighted" if weighted else "unweighted",
        "n": int(len(rows)),
        "mae_left": parent,
        "mae_right": float(np.sum(w * e_right) / np.sum(w)),
        "difference": block["difference"],
        "ci95": None,
        "se": None,
        "df": None,
        "p_two_sided": None,
        "detectable_80": None,
        "status": block["status"],
    }
    if block["status"] == "ok":
        stats = recipes.interval_stats(block, parent)
        record.update(
            ci95=stats["ci95"],
            se=stats["se"],
            df=stats["df"],
            p_two_sided=stats["p_two_sided"],
            detectable_80=stats["detectable_80"],
        )
    record["reading"] = reading(record["ci95"])
    return record


def gains(rows: pd.DataFrame) -> dict:
    """G_H and G_D, each unweighted and weighted by destination minutes."""
    return {
        name: {
            "left": left,
            "right": right,
            **{
                weighting: gain(rows, left, right, weighted=weighting != "unweighted")
                for weighting in WEIGHTINGS
            },
        }
        for name, (left, right) in GAINS.items()
    }


def flat(scope: str, blocks: dict) -> list:
    """One table row per difference and weighting."""
    out = []
    for name, block in blocks.items():
        for weighting in WEIGHTINGS:
            r = block[weighting]
            ci = r["ci95"] or [None, None]
            out.append(
                {
                    "scope": scope,
                    "difference_name": name,
                    "left": r["left"],
                    "right": r["right"],
                    "weighting": weighting,
                    "n": r["n"],
                    "mae_left": r["mae_left"],
                    "mae_right": r["mae_right"],
                    "difference": r["difference"],
                    "ci95_low": ci[0],
                    "ci95_high": ci[1],
                    "se": r["se"],
                    "df": r["df"],
                    "p_two_sided": r["p_two_sided"],
                    "detectable_80": r["detectable_80"],
                    "reading": r["reading"],
                }
            )
    return out


def arm_errors(rows: pd.DataFrame, arms=ARMS) -> dict:
    y = rows[OUTCOME].to_numpy(float)
    w = rows[WEIGHT].to_numpy(float)
    out = {}
    for arm in arms:
        e = np.abs(rows[arm].to_numpy(float) - y)
        out[arm] = {
            "unweighted": float(e.mean()),
            "minutes_weighted": float(np.sum(w * e) / np.sum(w)),
        }
    return out


def e28a(rows: pd.DataFrame) -> dict:
    """The 674: overall, by destination competition and by destination season."""
    scopes = {"all": rows}
    for d in dec.DESTINATIONS:
        scopes[f"destination:{d}"] = rows.loc[rows.league_dest.eq(d)]
    for s in sorted(int(v) for v in rows.season_dest.unique()):
        scopes[f"season:{s}"] = rows.loc[rows.season_dest.eq(s)]
    blocks = {scope: gains(part) for scope, part in scopes.items() if len(part)}
    table = [row for scope, block in blocks.items() for row in flat(scope, block)]
    return {
        "n": int(len(rows)),
        "mae": arm_errors(rows),
        "total_minutes": float(rows[WEIGHT].sum()),
        "contrasts": blocks["all"],
        "by_destination": {
            k.split(":", 1)[1]: v
            for k, v in blocks.items()
            if k.startswith("destination:")
        },
        "by_season": {
            k.split(":", 1)[1]: v for k, v in blocks.items() if k.startswith("season:")
        },
        "table": pd.DataFrame(table),
    }


# --------------------------------------------------------------- licences --
def eff(value: float) -> str:
    return f"{value:.3f}"


def span(ci95) -> str:
    return f"interval {ci95[0]:.3f} to {ci95[1]:.3f}"


def _unregistered(record: dict) -> dict:
    return {
        "reading": record["reading"],
        "registered_wording": None,
        "sentence": None,
        "note": "Amendment 9 registers no wording for this reading; it goes to Amir before any writing.",
    }


def licence_674(name: str, record: dict) -> dict:
    """Amendment 9, "What the paper may say": G_H and G_D on the 674, unweighted."""
    r = record["reading"]
    if r not in ("above_zero", "includes_zero"):
        return _unregistered(record)
    x = eff(record["difference"])
    if r == "above_zero":
        sentence = f"{LEAD[name]} by {x} EFF/36 ({span(record['ci95'])})"
    elif name == "G_H":
        sentence = WORDING[("G_H", "includes_zero")]
    else:
        sentence = f"once the destination is known, the source league's contribution ({x} EFF/36) is not distinguishable from zero at this n"
    return {
        "reading": r,
        "registered_wording": WORDING[(name, r)],
        "sentence": sentence,
    }


def licence_weighted(record: dict) -> dict:
    """Weighted versions: printed beside the unweighted values, one registered wording."""
    r = record["reading"]
    if r == "includes_zero":
        return {
            "reading": r,
            "registered_wording": WORDING[("weighted", "includes_zero")],
            "sentence": WORDING[("weighted", "includes_zero")],
        }
    if r == "above_zero":
        return {
            "reading": r,
            "registered_wording": None,
            "sentence": None,
            "note": "printed beside the unweighted value; no further wording is registered",
        }
    return _unregistered(record)


def licence_older(name: str, record: dict) -> dict:
    r = record["reading"]
    if r == "above_zero":
        sentence = f"{LEAD[name]} by {eff(record['difference'])} EFF/36 ({span(record['ci95'])}) also on the older seasons"
    elif r == "includes_zero":
        sentence = f"not detectable on the older seasons at this n (n = {record['n']})"
    else:
        return _unregistered(record)
    return {
        "reading": r,
        "registered_wording": WORDING[("older", r)],
        "sentence": sentence,
    }


def licences(blocks: dict, population: str) -> dict:
    first = licence_674 if population == "674" else licence_older
    return {
        name: {
            "unweighted": first(name, block["unweighted"]),
            "minutes_weighted": licence_weighted(block["minutes_weighted"]),
        }
        for name, block in blocks.items()
    }


def e28c(g_d: dict, margin: float, head: dict) -> dict:
    """The registered margin and head-to-head interval, each over G_D's point estimate."""
    point = g_d["difference"]
    r = g_d["reading"]
    share = margin / point
    out = {
        "g_d": point,
        "g_d_ci95": g_d["ci95"],
        "g_d_reading": r,
        "margin_eff36": margin,
        "margin_share_of_g_d": share,
        "head_to_head": {
            "left": HEAD_TO_HEAD[0],
            "right": HEAD_TO_HEAD[1],
            "ci95": list(head["ci95"]),
        },
        "head_to_head_ci95_share_of_g_d": [v / point for v in head["ci95"]],
        "descriptive": True,
    }
    if r == "above_zero":
        out["registered_wording"] = WORDING[("E28c", "above_zero")]
        out["sentence"] = (
            f"the margin is {100 * share:.0f}% of what the source league adds"
        )
    elif r == "includes_zero":
        out["registered_wording"] = WORDING[("E28c", "includes_zero")]
        out["sentence"] = WORDING[("E28c", "includes_zero")]
    else:
        out.update(_unregistered(g_d))
    return out


# ------------------------------------------------------------------ gates --
def g28a_differences(
    rows: pd.DataFrame,
    recipes_summary: dict,
    amend1_summary: dict,
    *,
    shift: float = 0.0,
    column: str = O,
) -> dict:
    """The registered errors, head-to-head and committed weighted head-to-head.

    ``shift`` moves one forecast column (the negative control).
    """
    if shift:
        rows = rows.assign(**{column: rows[column] + shift})
    worst = {}
    metrics = recipes_summary["results"]["A"]["R1"]["metrics"]
    for arm in ARMS:
        mine = common.mae(rows, arm)
        worst[f"mae:{arm}"] = abs(mine - metrics[arm]["mae"])
        worst[f"printed_mae:{arm}"] = (
            0.0 if f"{mine:.3f}" == PRINTED_MAE[arm] else math.inf
        )
    left, right = HEAD_TO_HEAD
    recorded = recipes_summary["e1"]["head_to_head"][f"lambda_{common.PRIMARY_PENALTY}"]
    if recorded["left"] != left or recorded["right"] != right:
        return {**worst, "head_to_head_arms": math.inf}
    got = common.contrast(rows, left, right)[SPEC]
    worst["head_to_head"] = abs(got["difference"] - recorded[SPEC]["difference"])
    worst["head_to_head_ci"] = max_abs(got["ci95"], recorded[SPEC]["ci95"])
    # the weighted estimator: E17's committed minutes-weighted head-to-head
    committed = amend1_summary["e17"]["minutes_weighted"]["contrasts"][
        a1.tag(left, right)
    ]["minutes_weighted"]
    mine = gain(rows, left, right, weighted=True)
    worst["weighted_head_to_head"] = abs(mine["difference"] - committed["difference"])
    worst["weighted_head_to_head_ci"] = max_abs(mine["ci95"], committed["ci95"])
    return worst


def equal_weight_difference(rows: pd.DataFrame) -> dict:
    """With every weight 1 the weighted interval is the registered one."""
    worst = {}
    rows = rows.reset_index(drop=True)
    for name, (left, right) in GAINS.items():
        ref = common.contrast(rows, left, right)[SPEC]
        d = a1.paired_difference(rows, left, right)
        got = surv.weighted_interval(d, None, rows.player_name, rows.cluster)
        worst[name] = max(
            abs(got["difference"] - ref["difference"]),
            max_abs(got["ci95"], ref["ci95"]),
        )
    return worst


def frozen_difference(
    scored: pd.DataFrame, frozen: pd.DataFrame, *, shift: float = 0.0
) -> dict:
    """Every scored row's forecasts are the frozen file's forecasts."""
    reference = frozen.rename(columns={"player_name": "frozen_key"})[
        [*FROZEN_KEY, *OLDER_ARMS]
    ]
    merged = scored[[*FROZEN_KEY, *OLDER_ARMS]].merge(
        reference, on=FROZEN_KEY, how="left", validate="1:1", suffixes=("", "_frozen")
    )
    worst = {}
    for arm in OLDER_ARMS:
        theirs = merged[f"{arm}_frozen"].to_numpy(float)
        if not np.isfinite(theirs).all():
            return {"rows_not_in_the_frozen_file": math.inf}
        mine = merged[arm].to_numpy(float) + (shift if arm == O else 0.0)
        worst[arm] = float(np.max(np.abs(mine - theirs)))
    return worst


def g28b_differences(part: pd.DataFrame, printed: dict, *, shuffle=None) -> dict:
    """The three Amendment 7 comparisons, recomputed on the scored rows.

    ``printed`` maps each comparison to its committed record. ``shuffle`` (a
    seed) permutes the outcome column across rows (the negative control).
    """
    part = part.reset_index(drop=True)
    if shuffle is not None:
        part = part.assign(
            **{OUTCOME: part[OUTCOME].sample(frac=1.0, random_state=shuffle).to_numpy()}
        )
    worst = {}
    got = {r["comparison"]: r for r in e27.comparisons(part)}
    if set(got) != set(printed):
        return {"comparison_set": math.inf}
    for name, mine in got.items():
        ref = printed[name]
        if mine["n"] != ref["n"] or mine["ci95"] is None or ref["ci95"] is None:
            worst[f"{name}:n_or_estimable"] = math.inf
            continue
        worst[f"{name}:difference"] = abs(mine["difference"] - ref["difference"])
        worst[f"{name}:ci95"] = max_abs(mine["ci95"], ref["ci95"])
        worst[f"{name}:margin"] = abs(mine["margin"] - ref["margin"])
    return worst


def older_block(part: pd.DataFrame, version: str) -> dict:
    blocks = gains(part)
    return {
        "version": version,
        "leagues": sorted(e27.VERSIONS[version]),
        "n": int(len(part)),
        "mae": arm_errors(part),
        "total_minutes": float(part[WEIGHT].sum()),
        "contrasts": blocks,
        "licences": licences(blocks, "older"),
    }


def _numbers(value) -> list:
    if isinstance(value, dict):
        return [x for v in value.values() for x in _numbers(v)]
    if isinstance(value, (list, tuple)):
        return [x for v in value for x in _numbers(v)]
    if isinstance(value, (float, np.floating)) and math.isfinite(value):
        return [float(value)]
    return []


def assert_no_leak(public: dict, withheld: dict | None) -> int:
    """No statistic of the withheld version appears in what may be committed."""
    if withheld is None:
        return 0
    stub = public["e28b"]["withheld"]
    if set(stub) != {"version", "computed_in_the_same_run", "reason"}:
        raise GateFailure("leak gate: the withheld stub carries more than its name")
    if e27p.WITHHELD_LEAGUE in public["e28b"]["leagues"]:
        raise GateFailure("leak gate: the printed version includes the withheld league")
    text = json.dumps(clean(public))
    secret = {
        repr(v)
        for key in ("mae", "total_minutes", "contrasts")
        for v in _numbers(withheld.get(key, {}))
        if v != int(v)
    }
    leaked = sorted(s for s in secret if s in text)
    if leaked:
        raise GateFailure(
            f"leak gate: {len(leaked)} withheld values appear in the public summary"
        )
    return len(secret)


def run(root: Path, input_dir: Path, frozen_path: Path, out: Path) -> dict:
    root = Path(root)
    committed = load_committed(root)
    common.check_sha(frozen_path, FROZEN_SHA)
    release = json.loads((root / RELEASE).read_text())
    paper = json.loads((root / E27_PAPER).read_text())
    v9, v10_summary = common.load_references(root)
    rows, _, _ = common.anchor_rows(root, input_dir)
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
    wa = {
        **g28a_differences(rows, committed["recipes"], committed["amend1"]),
        **{f"equal_weights:{k}": v for k, v in equal_weight_difference(rows).items()},
    }
    control = g28a_differences(
        rows, committed["recipes"], committed["amend1"], shift=CONTROL_SHIFT
    )
    gates["G28a"] = passed(
        gate_max("G28a", wa, REPRO_TOLERANCE),
        negative_control(gate_max, "G28a", control, REPRO_TOLERANCE),
        tolerance=REPRO_TOLERANCE,
        checked=sorted(wa),
        control_input=f"the league-aware forecast column shifted by {CONTROL_SHIFT}",
    )

    # ---- E28a and E28c: the 674
    a = e28a(rows)
    a["licences"] = licences(a["contrasts"], "674")
    margin = recipes.MARGIN_SHARE * common.mae(rows, O)
    registered_margin = next(
        r["margin_2pct_eff36"]
        for r in committed["amend1"]["e17"]["recipe_margins"]["rows"]
        if r["recipe"] == "R1" and r["spec"] == SPEC
    )
    wm = {
        "margin": abs(margin - registered_margin),
        "printed_margin": 0.0 if f"{margin:.3f}" == PRINTED_MARGIN else math.inf,
    }
    gates["E28c_margin"] = passed(
        gate_max("E28c margin gate", wm, REPRO_TOLERANCE),
        negative_control(gate_max, "E28c margin gate", wm, -1.0),
        tolerance=REPRO_TOLERANCE,
    )
    head = committed["recipes"]["e1"]["head_to_head"][
        f"lambda_{common.PRIMARY_PENALTY}"
    ][SPEC]
    c = e28c(a["contrasts"]["G_D"]["unweighted"], margin, head)

    # ---- E28b: the older seasons, both versions in this run
    scored = committed["e27_arrivals"]
    frozen = pd.read_parquet(frozen_path)
    printed_version = e27p.printed_version(release)
    flag = bool(release[e27p.FLAG])
    if (
        paper["printed_version"] != printed_version
        or paper[e27p.FLAG] != flag
        or paper["sources"]["e27_arrivals.csv"] != COMMITTED["e27_arrivals"][1]
        or paper["sources"]["e27_summary.json"] != COMMITTED["e27_summary"][1]
    ):
        raise GateFailure(
            "G28b: the Amendment 7 extract does not belong to these rows and this flag"
        )
    parts = {
        version: scored.loc[scored.league.isin(leagues)].reset_index(drop=True)
        for version, leagues in e27.VERSIONS.items()
    }
    if not all(
        (np.isfinite(p[WEIGHT]) & (p[WEIGHT] > 0)).all() for p in parts.values()
    ):
        raise GateFailure("an older arrival has no positive destination minutes")
    older, older_gates, frozen_gates = {}, {}, {}
    for version, part in parts.items():
        wf = frozen_difference(part, frozen)
        frozen_gates[version] = passed(
            gate_max("frozen-forecast gate", wf, EXACT_TOLERANCE),
            negative_control(
                gate_max,
                "frozen-forecast gate",
                frozen_difference(part, frozen, shift=CONTROL_SHIFT),
                EXACT_TOLERANCE,
            ),
            tolerance=EXACT_TOLERANCE,
        )
        if len(part) != committed["e27_summary"]["versions"][version]["n"]:
            raise GateFailure(
                "G28b: the scored rows are not the scoring run's arrivals"
            )
        references = {"scoring_run": committed["e27_summary"]["primary"][version]}
        if version == printed_version:
            references["extract"] = paper["comparisons"]["all"]
        wb = {
            f"{source}:{k}": v
            for source, ref in references.items()
            for k, v in g28b_differences(part, ref).items()
        }
        shuffled = {
            f"{source}:{k}": v
            for source, ref in references.items()
            for k, v in g28b_differences(part, ref, shuffle=SHUFFLE_SEED).items()
        }
        older_gates[version] = passed(
            gate_max("G28b", wb, REPRO_TOLERANCE),
            negative_control(gate_max, "G28b", shuffled, REPRO_TOLERANCE),
            tolerance=REPRO_TOLERANCE,
            checked=sorted(wb),
            control_input="the outcome column shuffled across rows",
        )
        # only after the gate: G_H and G_D
        older[version] = older_block(part, version)
    gates["frozen_forecasts"] = frozen_gates[printed_version]
    gates["G28b"] = older_gates[printed_version]
    other_version = next(v for v in e27.VERSIONS if v != printed_version)
    b = {
        "printed_version": printed_version,
        e27p.FLAG: flag,
        "second_reading": SECOND_READING,
        **older[printed_version],
    }
    withheld = None
    if flag:
        b["other_version"] = older[other_version]
        gates["frozen_forecasts_other_version"] = frozen_gates[other_version]
        gates["G28b_other_version"] = older_gates[other_version]
    else:
        b["withheld"] = {
            "version": other_version,
            "computed_in_the_same_run": True,
            "reason": "ACB's written permission had not arrived (Amendment 7's permission rule)",
        }
        withheld = {
            **older[other_version],
            "gates": {
                "frozen_forecasts": frozen_gates[other_version],
                "G28b": older_gates[other_version],
            },
        }

    sentences = [
        entry["sentence"]
        for block in (a["licences"], b["licences"])
        for name in GAINS
        for entry in block[name].values()
        if entry.get("sentence")
    ]
    if c.get("sentence"):
        sentences.append(c["sentence"])
    table_a = a.pop("table")
    table_b = pd.DataFrame(flat(f"older seasons ({printed_version})", b["contrasts"]))
    if flag:
        other_rows = flat(
            f"older seasons ({other_version})", older[other_version]["contrasts"]
        )
        table_b = pd.concat([table_b, pd.DataFrame(other_rows)], ignore_index=True)
    summary = {
        "analysis": "Amendment 9: E28 (exploratory; destination seasons 2020-2025 and the older seasons already seen)",
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
        "n_targets": int(len(rows)),
        "models": LABELS,
        "estimator": {
            "differences": {
                k: f"MAE({left}) - MAE({right})" for k, (left, right) in GAINS.items()
            },
            "interval": "two-way clustered 95% interval (player, destination club-season), Student t with min(clusters) - 1 degrees of freedom",
            "weights": "destination minutes (minutes_dest)",
            "detectable_80": "(t(0.975, df) + t(0.80, df)) x SE, the registered formula of the recipes track",
        },
        "gates": gates,
        "e28a": a,
        "e28b": b,
        "e28c": c,
        "sentences": sentences,
    }
    planted = None
    if withheld is not None:
        # negative control: a withheld value planted in the public record must be caught
        value = withheld["contrasts"]["G_D"]["unweighted"]["difference"]
        planted = negative_control(
            assert_no_leak, {**summary, "planted": value}, withheld
        )
    gates["no_withheld_value"] = {
        "status": "passed",
        "values_checked": assert_no_leak(summary, withheld),
        "negative_control": planted,
    }

    out = Path(out)
    out.mkdir(parents=True, exist_ok=False)
    table_a.to_csv(out / "e28a_differences.csv", index=False)
    table_b.to_csv(out / "e28b_differences.csv", index=False)
    low, high = c["head_to_head"]["ci95"]
    share_low, share_high = c["head_to_head_ci95_share_of_g_d"]
    pd.DataFrame(
        [
            {
                "quantity": "registered margin (2% of forecast error)",
                "eff36": c["margin_eff36"],
                "share_of_g_d": c["margin_share_of_g_d"],
            },
            {
                "quantity": "registered head-to-head interval, lower end",
                "eff36": low,
                "share_of_g_d": share_low,
            },
            {
                "quantity": "registered head-to-head interval, upper end",
                "eff36": high,
                "share_of_g_d": share_high,
            },
            {
                "quantity": "G_D on the 674 (point estimate)",
                "eff36": c["g_d"],
                "share_of_g_d": 1.0,
            },
        ]
    ).to_csv(out / "e28c_margin.csv", index=False)
    (out / "summary.json").write_text(
        json.dumps(clean(summary), indent=2, sort_keys=True) + "\n"
    )
    if withheld is not None:
        (out / "withheld").mkdir()
        (out / "withheld" / "e28b_withheld_version.json").write_text(
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
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    summary = run(Path.cwd(), args.input_dir, args.frozen, args.out)
    for sentence in summary["sentences"]:
        print(sentence)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
