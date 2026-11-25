#!/usr/bin/env python3
"""Derived player-season tables for the public companion: E7, E10, E15b inputs.

The public cut of github.com/AT020993/cross-league-translation (section
ssac27-fullpaper/) recomputes the full-paper results from published tables. Three
of the analyses read one step that needs per-game box scores, which are not
published: the odd/even split of each target's destination games (E7 and E10's
reliability ceiling, E15b's component reliabilities) and each target's career
history for every box-score component (E15b). This generator writes those steps'
outputs as player-season aggregates, so the public code can run from them:

* ``e7_keyed_forecasts.csv`` -- the decisions run's keyed table (674 targets:
  four forecasts and the odd/even EFF/36 halves); republished byte for byte.
* ``e15b_split_halves.csv`` -- the skills run's odd/even/full rates per
  component (674 targets); republished byte for byte.
* ``e6_split_half_players.csv`` -- the robustness run's odd/even halves for the
  four outcomes (674 targets); republished byte for byte.
* ``e15b_component_priors.parquet`` -- NEW: each target's career rate before the
  source season for every E15 component, by the v10 ``prior_mean_pir36`` rule
  (``sloan_fullpaper_skills.component_history``), rebuilt from the frozen raw
  inventory. Gate G3: the EFF version equals the published cohort's
  ``prior_mean_pir36`` exactly, with an impossible-tolerance negative control.

No row is a game; no column is a date, an age or a birthdate.

Threats: a republished file that is not the retained-run output (sha256 pins to
the run receipts), a history rule that drifted from v10 (G3), three split-half
tables that disagree with each other (EFF halves must agree across all three).
"""

from __future__ import annotations

if __name__ == "__main__":
    import sys as _sys
    from pathlib import Path as _Path

    _sys.path.insert(0, str(_Path(__file__).resolve().parents[1]))
    from src.research.execution import enter as _enter

    _enter(__file__)

import argparse
import contextlib
import io
import json
import shutil
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts import sloan_fullpaper_common as common  # noqa: E402
from scripts import sloan_fullpaper_robustness as robust  # noqa: E402
from scripts import sloan_fullpaper_skills as skills  # noqa: E402
from scripts.translation_research_common import sha256_file  # noqa: E402

KEY = common.KEY
#: Retained-run outputs republished unchanged: name -> (run, sha256 in its receipt).
REPUBLISHED = {
    "e7_keyed_forecasts.csv": (
        "decide-02",
        "83589795f00df04cdb272155697f6f9d55c8f7604e49ae3bc45e0e1aac04b8f6",
    ),
    "e15b_split_halves.csv": (
        "skills-01",
        "1b6d67041593a8ae12444a93f0f746e7144b3127372b4c692fdc48af4fcb7d63",
    ),
    "e6_split_half_players.csv": (
        "robustness-02",
        "e2e48b84ce60c218d155c9dea55543e914d9fb84b8c499d2258d48e5e33e038a",
    ),
}
PRIORS = "e15b_component_priors.parquet"
HALF_TOLERANCE = 1e-9


class GateFailure(AssertionError):
    """A gate of this generator did not hold."""


def component_priors(targets: pd.DataFrame, agg: pd.DataFrame) -> pd.DataFrame:
    table = targets[KEY].copy()
    for code in skills.COMPONENTS:
        table[f"prior_{code}"] = robust.attach_history(
            targets, skills.component_history(agg, code)
        )
    return table


def assert_g3(g3: dict, tolerance: float = 0.0) -> None:
    if g3["nan_pattern_mismatches"] or not g3["max_abs_difference"] <= tolerance:
        raise GateFailure(f"G3 failed: {g3}")


def half_agreement(e7: pd.DataFrame, e15: pd.DataFrame, e6: pd.DataFrame) -> dict:
    """EFF/36 odd and even halves in the three tables, per target."""
    m = (
        e7[[*KEY, "odd_rate", "even_rate"]]
        .merge(e15[[*KEY, "pir_odd", "pir_even"]], on=KEY, validate="1:1")
        .merge(e6[[*KEY, "O1_odd", "O1_even"]], on=KEY, validate="1:1")
    )
    out = {"targets": int(len(m))}
    for part, a, b, c in (
        ("odd", "odd_rate", "pir_odd", "O1_odd"),
        ("even", "even_rate", "pir_even", "O1_even"),
    ):
        out[f"{part}_e7_vs_e15b"] = _max_gap(m[a], m[b])
        out[f"{part}_e15b_vs_e6"] = _max_gap(m[b], m[c])
    return out


def _max_gap(x: pd.Series, y: pd.Series) -> float:
    """Largest |x - y|; a value missing on one side only is an infinite gap."""
    gap = np.abs(x - y).to_numpy(dtype=float, copy=True)
    gap[x.isna().to_numpy() != y.isna().to_numpy()] = np.inf
    return float(np.nanmax(gap)) if len(gap) else 0.0


def no_private_columns(frame: pd.DataFrame) -> list:
    bad = [
        c
        for c in frame.columns
        if any(t in c.lower() for t in ("date", "birth", "dob", "game_id"))
        or c.lower() == "age"
        or c.lower().startswith("age_")
    ]
    return bad


def run(input_dir: Path, prior_dir: Path, raw_root: Path, out: Path) -> dict:
    _, v10_summary = common.load_references(ROOT)
    _, cohort = common.load_pool(input_dir, "official_corrected")
    keys = common.target_keys(v10_summary)
    targets = keys.merge(cohort, on=KEY, how="left", validate="1:1")
    summary: dict = {
        "analysis": "public derived tables for the full-paper public cut",
        "inputs": {"cohort_sha256": common.COHORT_SHA},
        "republished": {},
    }
    out.mkdir(parents=True, exist_ok=False)
    frames = {}
    for name, (run_name, expected) in REPUBLISHED.items():
        path = Path(prior_dir) / run_name / name
        actual = sha256_file(path)
        if actual != expected:
            raise GateFailure(
                f"{name}: sha256 {actual} is not the {run_name} receipt's {expected}"
            )
        shutil.copyfile(path, out / name)
        frame = pd.read_csv(path, float_precision="round_trip")
        if len(frame) != len(keys) or frame[KEY].duplicated().any():
            raise GateFailure(f"{name}: not one row per target")
        if bad := no_private_columns(frame):
            raise GateFailure(f"{name}: private columns {bad}")
        frames[name] = frame
        summary["republished"][name] = {
            "run": run_name,
            "sha256": actual,
            "rows": int(len(frame)),
            "columns": list(frame.columns),
        }
    agreement = half_agreement(
        frames["e7_keyed_forecasts.csv"],
        frames["e15b_split_halves.csv"],
        frames["e6_split_half_players.csv"],
    )
    worst = max(v for k, v in agreement.items() if k != "targets")
    summary["half_agreement"] = {**agreement, "tolerance": HALF_TOLERANCE}
    if not worst <= HALF_TOLERANCE:
        raise GateFailure(f"EFF halves disagree across tables by {worst}")

    with contextlib.redirect_stdout(io.StringIO()):
        _, agg, rebuild = robust.rebuild_games(raw_root)
    summary["corpus_rebuild"] = rebuild
    g3 = robust.g3_difference(
        cohort, robust.attach_history(cohort, skills.component_history(agg, "pir"))
    )
    try:
        assert_g3(g3, tolerance=-1.0)
    except GateFailure:
        control = "rejected as required"
    else:
        raise GateFailure("G3 negative control passed an impossible tolerance")
    assert_g3(g3)
    summary["g3"] = {**g3, "status": "passed", "negative_control": control}
    priors = component_priors(targets, agg)
    if bad := no_private_columns(priors):
        raise GateFailure(f"priors: private columns {bad}")
    priors.to_parquet(out / PRIORS, index=False)
    summary["priors"] = {
        "file": PRIORS,
        "rows": int(len(priors)),
        "columns": list(priors.columns),
        "missing_history": {
            c: int(priors[f"prior_{c}"].isna().sum()) for c in skills.COMPONENTS
        },
        "sha256": sha256_file(out / PRIORS),
    }
    (out / "summary.json").write_text(
        json.dumps(robust.clean(summary), indent=2, sort_keys=True, allow_nan=False)
        + "\n"
    )
    return summary


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument("--prior-dir", type=Path, required=True)
    parser.add_argument("--raw-root", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    summary = run(args.input_dir, args.prior_dir, args.raw_root, args.out)
    print(
        json.dumps(
            {"g3": summary["g3"]["status"], "half_agreement": summary["half_agreement"]}
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
