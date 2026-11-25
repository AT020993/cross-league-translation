"""Recompute the headline tables from the two derived tables and assert
them against the committed summaries.

    python reproduce.py

Recomputed here (from pairs.parquet + switchers.parquet, no game rows):
  * the 20-cell factor table (pir / era all / all_pairs) -- against
    data/processed/translation/league_factors.parquet
  * the six walk-forward folds and the five arm MAEs -- against
    data/processed/translation/walkforward_summary.json
Read from committed JSON, NOT recomputable without game rows:
  * the destination split-half reliability and the R^2 ceiling (Propositions 2-3)
  * the holdout's leave-one-league-out arm and its per-league table
  * the synthetic-validation study and the conformal calibration
"""
from __future__ import annotations

import contextlib
import io
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

import scripts.validate_translation_holdout as vh  # noqa: E402
import scripts.validate_translation_walkforward as wf  # noqa: E402

DATA = ROOT / "data" / "processed" / "translation"


def main() -> int:
    pairs = pd.read_parquet(DATA / "pairs.parquet")
    switch = pd.read_parquet(DATA / "switchers.parquet")
    print(f"pairs {len(pairs)} rows, switchers {len(switch)} rows (unfiltered)")

    # 1. factor table
    with contextlib.redirect_stdout(io.StringIO()):
        tbl = vh.fit_factors(pairs, label="reproduce")
    ref = pd.read_parquet(DATA / "league_factors.parquet")
    ref = ref[(ref.stat == "pir") & (ref.era == "all") & (ref["sample"] == "all_pairs")]
    m = tbl.merge(ref, on=["league", "destination"], suffixes=("", "_ref"))
    gap = float(np.max(np.abs(m.factor - m.factor_ref)))
    print(f"factor table: {len(m)} cells, max |factor - committed| = {gap:.2e}")
    assert gap < 1e-9, "factor table does not reproduce"

    # 2. walk-forward folds
    cohorts = switch[switch.was_cont == 0]
    cohorts = cohorts[~cohorts.league_src.isin(vh.EXCLUDED_SOURCE)]
    cohorts = cohorts[cohorts.pir_per36_src > 0]
    fits = [wf.one_season(pairs, cohorts, s) for s in wf.SEASONS]
    for f in fits:
        f["rtm_arms"] = wf._fit_rtm_arms(f)
    rows = pd.concat([wf.fold_rows(f) for f in fits], ignore_index=True)
    rows = rows[np.isfinite(rows.per_league)]
    summary = json.loads((DATA / "walkforward_summary.json").read_text())
    expected = {
        "per_league": summary["pooled"]["mae_per_league"],
        "one_global": summary["pooled"]["mae_one_global"],
        "b0": summary["pooled"]["mae_b0"],
        "rtm": summary["rtm_comparator"]["mae_rtm"],
        "rtm_plus_league": summary["rtm_comparator"]["mae_rtm_plus_league"],
    }
    for arm, exp in expected.items():
        got = float(np.abs(rows[arm] - rows.y).mean())
        print(f"walk-forward {arm:16s} MAE {got:.6f} (committed {exp:.6f})")
        assert abs(got - exp) < 1e-6, f"{arm} does not reproduce"
    print(f"walk-forward rows {len(rows)} (committed {summary['n_pooled']})")
    assert len(rows) == summary["n_pooled"]
    print("OK: factor table and walk-forward ladder reproduce from the derived tables")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
