#!/usr/bin/env python3
"""Amendment 4 analysis: E24 (EXPLORATORY).

Pre-registration: docs/research/sloan-full-paper-preregistration-2026-11-03.md
(commit f52e7c831) and its Amendment 4,
docs/research/sloan-full-paper-preregistration-amendment-4-2026-11-11.md
(commit 5ab52fac1, pushed alone 2026-11-11 19:31 UTC, before this file
existed and after the Amendment 3 results had been read). Destination seasons
2020-2025 were exposed, so every number here is exploratory.

E24 -- league biases of a forecast that knows the destination but not the
source league. Three registered forecasts on the 674: H (history only, blind to
both leagues), D (history + destination intercept and slope) and O (offsets
l10, the league-aware forecast). E24a: mean signed error of D overall, by
destination and by season. E24b: D's signed error by source league, raw and
re-based (minus the all-arrival mean inside each bootstrap draw), Holm across
the 10 leagues on the re-based p-values. E24c: the spread S (arrival-weighted
RMS of the re-based league biases) and the contrasts S(D) - S(O) (primary) and
S(H) - S(D) (secondary). Printed: each league's share of arrivals that went to
the EuroLeague. The bootstrap is E11's and E18's (destination club-seasons
within pools, 2,000 draws, seed 0, same draw order).

Threats and their controls (all in this file): drift from the submitted numbers
(G0); a changed target set (scope gate); forecasts that differ from the E7 and
E1 runs (reproduction gate); league statistics that are not E18's (G24a: for H
and O every point, interval and spread reproduces the Amendment 3 run; its
negative control compares D with H's values); a destination-aware forecast
that is not Table 1's (G24b, with a shifted-forecast control). No 2026-27 data
is read.
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
from scripts import sloan_fullpaper_amend3 as a3  # noqa: E402
from scripts import sloan_fullpaper_common as common  # noqa: E402
from scripts import sloan_fullpaper_decisions as dec  # noqa: E402
from scripts import sloan_fullpaper_recipes as recipes  # noqa: E402
from scripts.translation_research_common import sha256_file  # noqa: E402

KEY = common.KEY
OUTCOME = dec.OUTCOME
N_BOOT = 2000
SEED = 0
AMENDMENT = Path(
    "docs/research/sloan-full-paper-preregistration-amendment-4-2026-11-11.md"
)
AMENDMENT_COMMIT = "5ab52fac1a3116859e77391572afa34489cf2e1e"

H, O = dec.HISTORY, dec.OFFSETS
D = "history_destination_slope"
ARMS = (H, D, O)
LABELS = {
    H: "history only (blind to both leagues)",
    D: "history + destination (blind to the source league)",
    O: "league-aware (one number per league)",
}
#: (left, right): the contrast is S(left) - S(right).
PRIMARY = (D, O)
SECONDARY = (H, D)
E18_ARMS = (H, O)
REPRO_TOLERANCE = 1e-9
HOLM_ALPHA = 0.05

PRIOR_FILES = {
    "decide-02/e7_keyed_forecasts.csv": "83589795f00df04cdb272155697f6f9d55c8f7604e49ae3bc45e0e1aac04b8f6",
    "recipes-01/rows_pool_A.parquet": "ce4f91e0ef854b684522efcf7d736b7c48a074277ac83a1fad016be7f7006eb3",
    "amend3-02/summary.json": "b777176293837d76d5a29f3aa102a1c3990a53462b98a7452dd6940adc8853c2",
    "amend3-02/e18_league_rebased.csv": "d304d1232eef54f50b73a64cf0b795631acbf7cebbe61040a7023687f2f406ec",
}

EXPOSURE = {
    "seen_before_registration": [
        "every Amendment 3 result, including history-only and league-aware signed errors overall, by destination, by season and by source league, and their spreads",
        "the registered MAE of the destination-aware forecast on the 674",
    ],
    "not_seen_before_this_run": [
        "any signed error of the destination-aware forecast",
        "its spread of league biases",
        "the split of each league's arrivals between the two competitions",
    ],
}


class GateFailure(common.GateFailure):
    """A registered Amendment 4 gate did not hold."""


interval = dec.interval
power_line = dec.power_line
negative_control = a1.negative_control
max_abs = a1.max_abs
gate_max = a1.gate_max
passed = a1.passed
clean = a1.clean


def load_prior(prior_dir: Path) -> dict:
    out = {}
    for name, expected in PRIOR_FILES.items():
        path = Path(prior_dir) / name
        common.check_sha(path, expected)
        if name.endswith(".json"):
            out[name] = json.loads(path.read_text())
        elif name.endswith(".parquet"):
            out[name] = pd.read_parquet(path)
        else:
            out[name] = pd.read_csv(path)
    return out


def e24(rows: pd.DataFrame, leagues: list, *, n_boot=N_BOOT, seed=SEED) -> dict:
    """Level, league biases and spreads for H, D and O on E18's bootstrap draws."""
    frame, pool_groups = a3.pool_frame(rows)
    signed = {arm: (frame[arm] - frame[OUTCOME]).to_numpy(float) for arm in ARMS}
    codes = pd.Categorical(frame.league_src, categories=leagues).codes
    if (codes < 0).any():
        raise GateFailure("a target's source league is outside the league list")
    m = len(leagues)
    dest = frame.league_dest.to_numpy(object)
    season = frame.season_dest.to_numpy(int)
    scopes = {"all": np.ones(len(frame), bool)}
    for d in dec.DESTINATIONS:
        if (dest == d).any():
            scopes[f"destination:{d}"] = dest == d
    for s in sorted(set(season)):
        scopes[f"season:{s}"] = season == s

    def evaluate(idx):
        n = np.bincount(codes[idx], minlength=m).astype(float)
        out = {}
        for arm, s in signed.items():
            v = s[idx]
            overall = float(v.mean())
            with np.errstate(invalid="ignore", divide="ignore"):
                league = np.bincount(codes[idx], weights=v, minlength=m) / n
            out[arm] = {
                "level": {
                    name: float(v[mask[idx]].mean()) if mask[idx].any() else math.nan
                    for name, mask in scopes.items()
                },
                "league": league,
                "rebased": league - overall,
                "spread": a3.spread(np.nan_to_num(league - overall), n),
            }
        return out

    point = evaluate(np.arange(len(frame)))
    rng = np.random.default_rng(seed)
    draws = [evaluate(a3.pool_draw(pool_groups, rng)) for _ in range(n_boot)]

    level_rows = []
    for arm in ARMS:
        for name, mask in scopes.items():
            d = np.array([x[arm]["level"][name] for x in draws])
            lo, hi = interval(d)
            level_rows.append(
                {
                    "arm": arm,
                    "label": LABELS[arm],
                    "scope": name,
                    "n": int(mask.sum()),
                    "mean_signed_error": point[arm]["level"][name],
                    "ci95_low": lo,
                    "ci95_high": hi,
                }
            )
    league_rows, pvalues = [], {}
    n_point = np.bincount(codes, minlength=m)
    for k, league in enumerate(leagues):
        row = {"source_league": league, "arrivals": int(n_point[k])}
        for arm in ARMS:
            raw = np.array([x[arm]["league"][k] for x in draws])
            reb = np.array([x[arm]["rebased"][k] for x in draws])
            row[f"signed_error_{arm}"] = float(point[arm]["league"][k])
            row[f"raw_ci95_low_{arm}"], row[f"raw_ci95_high_{arm}"] = interval(raw)
            row[f"rebased_{arm}"] = float(point[arm]["rebased"][k])
            row[f"rebased_ci95_low_{arm}"], row[f"rebased_ci95_high_{arm}"] = interval(
                reb
            )
            row[f"rebased_p_bootstrap_{arm}"] = a1.bootstrap_p(reb)
            row[f"rebased_mde_80_{arm}"] = power_line(reb)["mde_80"]
        pvalues[league] = row[f"rebased_p_bootstrap_{D}"]
        league_rows.append(row)
    adjusted = recipes.holm(pvalues)
    for row in league_rows:
        row[f"rebased_p_holm_{D}"] = adjusted[row["source_league"]]
        row.update(league_licence(row))
    spreads = {}
    for arm in ARMS:
        d = np.array([x[arm]["spread"] for x in draws])
        spreads[arm] = {"point": point[arm]["spread"], "ci95": interval(d)}
    contrasts = {}
    for name, (left, right) in (("primary", PRIMARY), ("secondary", SECONDARY)):
        d = np.array([x[left]["spread"] - x[right]["spread"] for x in draws])
        contrasts[name] = {
            "definition": f"S({left}) - S({right})",
            "point": point[left]["spread"] - point[right]["spread"],
            "ci95": interval(d),
            **power_line(d),
        }
        contrasts[name].update(contrast_licence(name, contrasts[name]))
    return {
        "level": pd.DataFrame(level_rows),
        "leagues": pd.DataFrame(league_rows),
        "spread": spreads,
        "contrasts": contrasts,
        "holm_family": "destination-aware re-based bootstrap two-sided p, 10 source leagues",
    }


def league_licence(row: dict) -> dict:
    value = row[f"rebased_{D}"]
    if row[f"rebased_p_holm_{D}"] < HOLM_ALPHA:
        verb = "underrates" if value < 0 else "overrates"
        return {
            "licence": "licensed",
            "sentence": (
                "Measured against the average arrival, a forecast that knows the destination but not "
                f"the source league {verb} arrivals from {row['source_league']} by {abs(value):.2f} EFF/36."
            ),
        }
    return {
        "licence": "not_distinguishable",
        "sentence": f"{row['source_league']}: not distinguishable at this n.",
    }


def contrast_licence(name: str, block: dict) -> dict:
    above = bool(block["ci95"][0] > 0)
    if name == "primary":
        sentence = (
            "Once the forecast knows the destination, the league table still flattens the league pattern."
            if above
            else "Once the forecast knows the destination, the league pattern is not detectably flatter with the league table at this n."
        )
    else:
        sentence = (
            "Part of the league pattern of a league-blind forecast reflects which competition a league's players join."
            if above
            else "Knowing the destination alone does not detectably flatten the league pattern at this n."
        )
    return {"licensed": above, "sentence": sentence}


def destination_mix(rows: pd.DataFrame) -> pd.DataFrame:
    """Each source league's arrivals by destination competition."""
    table = (
        rows.groupby("league_src")
        .agg(
            arrivals=("league_dest", "size"),
            euroleague=("league_dest", lambda s: int((s == "euroleague").sum())),
        )
        .reset_index()
        .rename(columns={"league_src": "source_league"})
    )
    table["eurocup"] = table.arrivals - table.euroleague
    table["euroleague_share"] = table.euroleague / table.arrivals
    return table


def g24a_differences(
    result: dict, e18_table: pd.DataFrame, e18_summary: dict, mine=None
) -> dict:
    """For H and O every E18 point, interval and spread is reproduced (same draws).

    `mine` maps an E18 arm to the E24 arm compared with it; the negative control
    compares D with H's values.
    """
    mine = mine or {arm: arm for arm in E18_ARMS}
    got = result["leagues"].set_index("source_league")
    want = e18_table.set_index("source_league")
    if set(got.index) != set(want.index):
        return {"league_set": math.inf}
    want = want.loc[got.index]
    worst = {}
    for theirs, ours in mine.items():
        for stem in (
            "signed_error_",
            "raw_ci95_low_",
            "raw_ci95_high_",
            "rebased_",
            "rebased_ci95_low_",
            "rebased_ci95_high_",
        ):
            worst[f"{stem}{theirs}"] = max_abs(
                got[f"{stem}{ours}"], want[f"{stem}{theirs}"]
            )
        recorded = e18_summary["e18"]["spread"][theirs]
        worst[f"spread:{theirs}"] = abs(
            result["spread"][ours]["point"] - recorded["point"]
        )
        worst[f"spread_ci:{theirs}"] = max_abs(
            result["spread"][ours]["ci95"], recorded["ci95"]
        )
    return worst


def g24b_difference(rows: pd.DataFrame, v9: dict, shift: float = 0.0) -> dict:
    """D's MAE on the 674 equals the registered Table 1 value."""
    reference = v9["variants"]["official_corrected"]["scenarios"]["reference"]
    recorded = reference["metrics"][D]["mae"]
    mine = float(np.mean(np.abs(rows[D] + shift - rows[OUTCOME])))
    return {"mae": abs(mine - recorded)}


def run(root: Path, input_dir: Path, prior_dir: Path, out: Path, n_boot=N_BOOT):
    root = Path(root)
    prior = load_prior(prior_dir)
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
    keyed = prior["decide-02/e7_keyed_forecasts.csv"]
    r_rows = prior["recipes-01/rows_pool_A.parquet"]
    worst = a1.reproduction_difference(rows, keyed, r_rows.loc[r_rows.recipe.eq("R1")])
    gates["reproduction"] = passed(
        gate_max("reproduction gate", worst, REPRO_TOLERANCE),
        negative_control(gate_max, "reproduction gate", worst, -1.0),
        tolerance=REPRO_TOLERANCE,
    )
    leagues = a1.assert_leagues(rows)
    wb = g24b_difference(rows, v9)
    gates["G24b"] = passed(
        gate_max("G24b", wb, REPRO_TOLERANCE),
        negative_control(
            gate_max, "G24b", g24b_difference(rows, v9, shift=0.1), REPRO_TOLERANCE
        ),
    )

    result = e24(rows, leagues, n_boot=n_boot)
    e18_table = prior["amend3-02/e18_league_rebased.csv"]
    e18_summary = prior["amend3-02/summary.json"]
    if n_boot != e18_summary["n_boot"]:
        raise GateFailure("G24a needs the Amendment 3 draw count")
    wa = g24a_differences(result, e18_table, e18_summary)
    control = g24a_differences(result, e18_table, e18_summary, mine={H: D})
    gates["G24a"] = passed(
        gate_max("G24a", wa, REPRO_TOLERANCE),
        negative_control(gate_max, "G24a", control, REPRO_TOLERANCE),
        checked=sorted(wa),
    )
    recorded = e18_summary["e18"]["spread_contrast"]
    mix = destination_mix(rows)

    out = Path(out)
    out.mkdir(parents=True, exist_ok=False)
    result["level"].to_csv(out / "e24_level.csv", index=False)
    result["leagues"].to_csv(out / "e24_league_bias.csv", index=False)
    mix.to_csv(out / "e24_destination_mix.csv", index=False)
    summary = {
        "analysis": "Amendment 4: E24 (exploratory; destination seasons 2020-2025 already seen)",
        "exploratory": True,
        "protocol_commit": common.PROTOCOL_COMMIT,
        "protocol_sha256": sha256_file(root / common.PROTOCOL),
        "amendment_commit": AMENDMENT_COMMIT,
        "amendment_sha256": sha256_file(root / AMENDMENT),
        "input_sha256": {
            "pairs": common.PAIRS_SHA["official_corrected"],
            "cohort": common.COHORT_SHA,
            **PRIOR_FILES,
        },
        "exposure": EXPOSURE,
        "n_boot": n_boot,
        "seed": SEED,
        "n_targets": int(len(rows)),
        "models": LABELS,
        "gates": gates,
        "e24": {
            "level": result["level"].to_dict(orient="records"),
            "leagues": result["leagues"].to_dict(orient="records"),
            "holm_family": result["holm_family"],
            "spread": result["spread"],
            "contrasts": result["contrasts"],
            "e18_contrast_history_minus_league_aware": {
                "point": recorded["point"],
                "ci95": recorded["ci95"],
                "source": "Amendment 3 run amend3-02 (E18)",
            },
            "destination_mix": mix.to_dict(orient="records"),
        },
    }
    (out / "summary.json").write_text(
        json.dumps(clean(summary), indent=2, sort_keys=True) + "\n"
    )
    return summary


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument(
        "--prior-dir",
        type=Path,
        required=True,
        help="staged outputs of retained runs decide-02, recipes-01 and amend3-02",
    )
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--n-boot", type=int, default=N_BOOT)
    args = parser.parse_args(argv)
    summary = run(Path.cwd(), args.input_dir, args.prior_dir, args.out, args.n_boot)
    for block in summary["e24"]["contrasts"].values():
        print(block["sentence"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
