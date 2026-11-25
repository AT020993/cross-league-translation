"""SSAC27 full paper, Amendment 22, analysis E33 (exploratory).

Sensitivity (7) of the league-changes test (E30, Amendment 14) refits the
league table only on arrivals before the season of each move, and compares
every league changer with a stayer forecast fitted once, on all seasons. E33
fits the stayer forecast, too, only on seasons before each move, on the same
2,083 league changes, and reports how much the slope moves.

Two subcommands:

* ``gates`` runs G33a (pinned inputs), G33b (the same rows), G33d (the cutoff)
  and G33e (a planted slope on made-up outcomes). It reads no league changer's
  rate in the destination season: of the scored file it reads the key, the
  season and the two leagues, nothing else.
* ``score`` is the single run. It repeats G33a, G33b and G33d, requires the
  committed record of ``gates``, then runs G33c (the same code path returns the
  estimate and both ends of the interval of sensitivity (7) to 1e-9) and only
  then computes E33.

The outcomes have been read before (by the scoring run of E30), so E33 is
exploratory. The generator of E30 is imported and not edited: the stayer design,
the least-squares solver, the slope and the percentile interval are its own
functions, and the bootstrap resamples the same players with the same stream.
"""

# ruff: noqa: E501 -- gate messages
from __future__ import annotations

if __name__ == "__main__":
    import sys as _sys
    from pathlib import Path as _Path

    _sys.path.insert(0, str(_Path(__file__).resolve().parents[1]))
    from src.research.execution import enter as _enter

    _enter(__file__)

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

from scripts import sloan_fullpaper_league_changes as lc  # noqa: E402
from scripts.translation_research_common import sha256_file  # noqa: E402

GateFailure = lc.GateFailure

AMENDMENT = Path(
    "docs/research/sloan-full-paper-preregistration-amendment-22-2026-11-19.md"
)
AMENDMENT_SHA = "4c234e20a8bf88dee7098ff3fe095de262d25a946413f4ff88fc0a908dad0ad0"
ARTIFACTS = Path("docs/research/artifacts/sloan-fullpaper-league-changes-2026-11")
#: Amendment 22, "Pinned inputs".
PINS = {
    "amendment_22": (AMENDMENT.as_posix(), AMENDMENT_SHA),
    "frozen": (
        (ARTIFACTS / "e30_frozen_league_changes.parquet").as_posix(),
        "2df696debc8567d9468844384c259e2289d6d1d985d7cbe4c7930bd7bf85b722",
    ),
    "stayers": (
        (ARTIFACTS / "e30_stayer_pairs.parquet").as_posix(),
        "afdda9226c671e9ef774297097ad5507ed83a72d4d06d4a98cdc26f8fb0997b6",
    ),
    "scored": (
        (ARTIFACTS / "e30_scored_league_changes.parquet").as_posix(),
        "03d5355dd4c8127b9130dc2c7bfd7c9d782e14cca7c1e9bc83ac2fc0a9dbfaa4",
    ),
    "e30_summary": (
        (ARTIFACTS / "e30_summary.json").as_posix(),
        "f1df4c23899c959fc7458caff0e5f2ec8ae071517b29be491a41383f946319dc",
    ),
}
#: Amendment 22, "Pinned inputs": the row counts read before the run.
SEASONS = tuple(range(2020, 2026))
EXPECTED_ROWS = 2083
EXPECTED_BY_SEASON = {2020: 312, 2021: 360, 2022: 374, 2023: 363, 2024: 344, 2025: 330}
EXPECTED_MOVERS = 1165
EXPECTED_TRAINING = {
    2020: 3578,
    2021: 4491,
    2022: 5429,
    2023: 6331,
    2024: 7263,
    2025: 8219,
}
EXPECTED_PLAYERS = 3577
N_BOOT = lc.N_BOOT
SEED = lc.SEED  # the stream of E30: numpy.random.default_rng([SEED, 0])
REPRODUCTION_TOLERANCE = 1e-9
PLANTED_TOLERANCE = 0.05
#: 80% power, two-sided 5%: 1.96 + 0.84.
DETECTABLE_FACTOR = 2.80
MADE_UP_SEED = [SEED, 33]

GATES_NAME = "e33_gates.json"
SUMMARY_NAME = "e33_summary.json"
SLOPES_NAME = "e33_slopes.csv"
SEASONS_NAME = "e33_by_season.csv"
JOIN_COLUMNS = ["season_to", "league_from", "league_to"]


# ---------------------------------------------------------------------------
# Rows (G33b).


def selected(frozen: pd.DataFrame) -> pd.DataFrame:
    """The league changes of sensitivity (7): a finite refitted gap."""
    rows = frozen.loc[np.isfinite(frozen.g_refit.to_numpy(float))]
    return rows.reset_index(drop=True)


def assert_rows(frozen: pd.DataFrame, scored_keys: pd.DataFrame) -> dict:
    """G33b. ``scored_keys``: the key, the season and the two leagues of the scored file."""
    for name, frame in (("frozen", frozen), ("scored", scored_keys)):
        if frame[lc.KEY].isna().any().any() or frame.duplicated(lc.KEY).any():
            raise GateFailure(f"the {name} file has a missing or repeated key")
    if len(frozen) != len(scored_keys):
        raise GateFailure(
            f"the frozen file has {len(frozen)} rows, the scored file {len(scored_keys)}"
        )
    joined = frozen[lc.KEY + JOIN_COLUMNS].merge(
        scored_keys[lc.KEY + JOIN_COLUMNS],
        on=lc.KEY,
        how="outer",
        suffixes=("", "_scored"),
        indicator=True,
        validate="one_to_one",
    )
    if not (joined["_merge"] == "both").all():
        raise GateFailure("the frozen and the scored file do not hold the same keys")
    for column in JOIN_COLUMNS:
        if not (joined[column] == joined[column + "_scored"]).all():
            raise GateFailure(f"the frozen and the scored file differ on {column}")
    rows = selected(frozen)
    by_season = {
        int(k): int(v) for k, v in rows.season_to.value_counts().sort_index().items()
    }
    if len(rows) != EXPECTED_ROWS or by_season != EXPECTED_BY_SEASON:
        raise GateFailure(
            f"the selected league changes number {len(rows)} ({by_season}), registered {EXPECTED_ROWS} ({EXPECTED_BY_SEASON})"
        )
    movers = int(rows.player_name.nunique())
    if movers != EXPECTED_MOVERS:
        raise GateFailure(
            f"{movers} players among the selected rows, registered {EXPECTED_MOVERS}"
        )
    return {
        "league_changes": len(rows),
        "by_arrival_season": by_season,
        "players": movers,
    }


# ---------------------------------------------------------------------------
# The cutoff (G33d).


def training_mask(stayer_season: np.ndarray, season: int, inclusive: bool = False):
    """Stayer pairs whose outcome season is before ``season``.

    ``inclusive`` exists only for the negative control of G33d.
    """
    season_to = np.asarray(stayer_season, int)
    return season_to <= season if inclusive else season_to < season


def assert_cutoff(stayer_season: np.ndarray, masks: dict) -> dict:
    """G33d: the latest outcome season used for arrival season t is before t."""
    season_to = np.asarray(stayer_season, int)
    record = {}
    for season, mask in masks.items():
        if not mask.any():
            raise GateFailure(f"no stayer pair before arrival season {season}")
        latest = int(season_to[mask].max())
        if latest >= season:
            raise GateFailure(
                f"the stayer forecast for arrival season {season} uses outcome season {latest}"
            )
        record[int(season)] = {
            "training_rows": int(mask.sum()),
            "latest_outcome_season": latest,
        }
    return record


def cutoff_masks(stayer_season: np.ndarray, inclusive: bool = False) -> dict:
    return {t: training_mask(stayer_season, t, inclusive) for t in SEASONS}


# ---------------------------------------------------------------------------
# Statistics.


def context(moves: pd.DataFrame, stayers: pd.DataFrame, outcome: np.ndarray) -> dict:
    """Arrays for the statistics. The players are those of E30: every league changer and every stayer."""
    players = pd.Index(
        np.unique(
            np.concatenate(
                [stayers.player_name.to_numpy(), moves.player_name.to_numpy()]
            )
        )
    )
    season = moves.season_to.to_numpy(int)
    use = np.isfinite(moves.g_refit.to_numpy(float))
    stayer_season = stayers.season_to.to_numpy(int)
    return {
        "n_players": len(players),
        "stayer_player": players.get_indexer(stayers.player_name),
        "move_player": players.get_indexer(moves.player_name),
        "SX": lc.design(stayers, league="league"),
        "Sy": stayers.rate_next.to_numpy(float),
        "MX": lc.design(moves),
        "My": np.asarray(outcome, float),
        "g_refit": np.nan_to_num(moves.g_refit.to_numpy(float)),
        "use": use.astype(float),
        "season": season,
        "season_rows": {t: use & (season == t) for t in SEASONS},
        "stayer_season": stayer_season,
        "training": cutoff_masks(stayer_season),
    }


def season_slope(g, e, w, season) -> float:
    """The slope with one intercept per arrival season (weighted, within season)."""
    g_in = np.zeros_like(g)
    e_in = np.zeros_like(e)
    for t in SEASONS:
        rows = (season == t) & (w > 0)
        total = w[rows].sum()
        if total <= 0:
            continue
        g_in[rows] = g[rows] - (w[rows] * g[rows]).sum() / total
        e_in[rows] = e[rows] - (w[rows] * e[rows]).sum() / total
    spread = (w * g_in**2).sum()
    return float((w * g_in * e_in).sum() / spread) if spread > 0 else np.nan


def pooled_statistics(ctx: dict, ws, wm) -> dict:
    """Sensitivity (7) as E30 computes it: the stayer forecast fitted on all seasons."""
    beta = lc.wls(ctx["SX"], ctx["Sy"], ws)
    e = ctx["My"] - ctx["MX"] @ beta
    w = wm * ctx["use"]
    return {
        "pooled": lc.wslope(ctx["g_refit"], e, w)[0],
        "pooled_season_intercepts": season_slope(ctx["g_refit"], e, w, ctx["season"]),
    }


def cutoff_statistics(ctx: dict, ws, wm, training: dict | None = None) -> dict:
    """E33: for each arrival season the stayer forecast is fitted on earlier outcome seasons only."""
    training = ctx["training"] if training is None else training
    e = np.zeros(len(ctx["My"]))
    for t in SEASONS:
        rows = ctx["season_rows"][t]
        fit = training[t]
        if ws[fit].sum() <= 0:
            raise GateFailure(f"a draw holds no stayer pair before arrival season {t}")
        beta = lc.wls(ctx["SX"][fit], ctx["Sy"][fit], ws[fit])
        e[rows] = ctx["My"][rows] - ctx["MX"][rows] @ beta
    w = wm * ctx["use"]
    return {
        "cutoff": lc.wslope(ctx["g_refit"], e, w)[0],
        "cutoff_season_intercepts": season_slope(ctx["g_refit"], e, w, ctx["season"]),
    }


def draws(ctx: dict, statistics, n_boot: int = N_BOOT, seed: int = SEED) -> dict:
    """The player bootstrap of E30: the same players, the same stream, every fit repeated."""
    rng = np.random.default_rng([seed, 0])
    n = ctx["n_players"]
    out: dict = {}
    for b in range(n_boot):
        counts = np.bincount(rng.integers(0, n, n), minlength=n).astype(float)
        stats = {}
        for function in statistics:
            stats.update(
                function(ctx, counts[ctx["stayer_player"]], counts[ctx["move_player"]])
            )
        for name, value in stats.items():
            if not np.isfinite(value):
                raise GateFailure(f"draw {b}: {name} is not a finite number")
            out.setdefault(name, np.full(n_boot, np.nan))[b] = value
    return out


def points(ctx: dict, statistics) -> dict:
    ones_s = np.ones(len(ctx["Sy"]))
    ones_m = np.ones(len(ctx["My"]))
    out = {}
    for function in statistics:
        out.update(function(ctx, ones_s, ones_m))
    return out


def entry(point: float, sample) -> dict:
    return {"estimate": float(point), "ci95": lc.interval(sample)}


# ---------------------------------------------------------------------------
# G33c: the same code path reproduces sensitivity (7).


def assert_reproduces(found: dict, retained: dict) -> None:
    pairs = [(found["estimate"], retained["estimate"])] + list(
        zip(found["ci95"], retained["ci95"])
    )
    for mine, theirs in pairs:
        if not abs(mine - theirs) < REPRODUCTION_TOLERANCE:
            raise GateFailure(
                f"sensitivity (7) is not reproduced: {mine!r} against the retained {theirs!r}"
            )


def reproduction_gate(
    ctx: dict, retained: dict, n_boot: int = N_BOOT, seed: int = SEED
):
    """(record, the pooled draws). The interval must change with the seed, or the comparison is empty."""
    point = points(ctx, [pooled_statistics])
    sample = draws(ctx, [pooled_statistics], n_boot, seed)
    found = entry(point["pooled"], sample["pooled"])
    assert_reproduces(found, retained)
    other = draws(ctx, [pooled_statistics], n_boot, seed + 1)
    control = lc.negative_control(
        assert_reproduces, entry(point["pooled"], other["pooled"]), retained
    )
    record = {
        "status": "passed",
        "found": found,
        "retained": {"estimate": retained["estimate"], "ci95": list(retained["ci95"])},
        "tolerance": REPRODUCTION_TOLERANCE,
        "negative_control_other_seed": control,
    }
    return record, point, sample


# ---------------------------------------------------------------------------
# G33e: a planted slope on made-up outcomes.


def made_up_outcome(ctx: dict, slope: float, noise_sd: float, rng) -> np.ndarray:
    """The cutoff stayer forecast + slope x g_refit + noise, for the selected rows."""
    ones = np.ones(len(ctx["Sy"]))
    outcome = np.zeros(len(ctx["My"]))
    for t in SEASONS:
        fit = ctx["training"][t]
        beta = lc.wls(ctx["SX"][fit], ctx["Sy"][fit], ones[fit])
        rows = ctx["season_rows"][t]
        outcome[rows] = ctx["MX"][rows] @ beta
    use = ctx["use"] > 0
    outcome[use] += slope * ctx["g_refit"][use] + rng.normal(
        0.0, noise_sd, int(use.sum())
    )
    return outcome


def cutoff_result(ctx: dict, n_boot: int, seed: int) -> dict:
    point = points(ctx, [cutoff_statistics])
    sample = draws(ctx, [cutoff_statistics], n_boot, seed)
    result = entry(point["cutoff"], sample["cutoff"])
    return {"slope": result["estimate"], "ci95": result["ci95"]}


def planted_gate(moves, stayers, n_boot: int = N_BOOT, seed: int = SEED) -> dict:
    """G33e, with its negative control. No real outcome of a league changer is used."""
    rng = np.random.default_rng(MADE_UP_SEED)
    blank = context(moves, stayers, np.zeros(len(moves)))
    noise_sd = lc.fit_stayers(stayers)["residual_sd"]
    one = dict(blank, My=made_up_outcome(blank, 1.0, noise_sd, rng))
    zero = dict(blank, My=made_up_outcome(blank, 0.0, noise_sd, rng))
    planted_one = cutoff_result(one, n_boot, seed)
    lc.assert_planted_slope(planted_one, PLANTED_TOLERANCE)
    planted_zero = cutoff_result(zero, n_boot, seed)
    lc.assert_includes_zero(planted_zero)
    # negative control: the refitted gaps shuffled across the made-up moves
    use = blank["use"] > 0
    shuffled = blank["g_refit"].copy()
    shuffled[use] = rng.permutation(shuffled[use])
    control = cutoff_result(dict(one, g_refit=shuffled), n_boot, seed)
    lc.assert_includes_zero(control)
    return {
        "status": "passed",
        "noise_sd": noise_sd,
        "planted_slope_one": planted_one,
        "planted_slope_zero": planted_zero,
        "negative_control_shuffled_gap": control,
        "tolerance": PLANTED_TOLERANCE,
    }


# ---------------------------------------------------------------------------
# The gates that need no outcome.


def load_inputs(root: Path):
    frozen = pd.read_parquet(root / PINS["frozen"][0])
    stayers = pd.read_parquet(root / PINS["stayers"][0])
    scored_keys = pd.read_parquet(
        root / PINS["scored"][0], columns=lc.KEY + JOIN_COLUMNS
    )
    return frozen, stayers, scored_keys


def outcome_free_gates(root: Path, frozen, stayers, scored_keys) -> dict:
    record = {"G33a_inputs": lc.pin_gate(root, PINS)}
    rows = assert_rows(frozen, scored_keys)
    record["G33b_same_rows"] = {
        "status": "passed",
        **rows,
        "negative_control_row_removed_from_frozen": lc.negative_control(
            assert_rows, frozen.iloc[1:], scored_keys
        ),
        "negative_control_row_removed_from_scored": lc.negative_control(
            assert_rows, frozen, scored_keys.iloc[1:]
        ),
    }
    stayer_season = stayers.season_to.to_numpy(int)
    seasons = assert_cutoff(stayer_season, cutoff_masks(stayer_season))
    training = {t: seasons[t]["training_rows"] for t in SEASONS}
    if training != EXPECTED_TRAINING:
        raise GateFailure(f"training rows {training}, registered {EXPECTED_TRAINING}")
    players = len(set(stayers.player_name) | set(frozen.player_name))
    if players != EXPECTED_PLAYERS:
        raise GateFailure(f"{players} players, registered {EXPECTED_PLAYERS}")
    record["G33d_cutoff"] = {
        "status": "passed",
        "by_arrival_season": seasons,
        "players_resampled": players,
        "negative_control_season_included": lc.negative_control(
            assert_cutoff, stayer_season, cutoff_masks(stayer_season, inclusive=True)
        ),
    }
    return record


def gates(root: Path, out: Path, n_boot: int = N_BOOT) -> dict:
    """G33a, G33b, G33d and G33e. No rate of a league changer in the destination season is read."""
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    frozen, stayers, scored_keys = load_inputs(Path(root))
    record = outcome_free_gates(Path(root), frozen, stayers, scored_keys)
    record["G33e_planted_slope"] = planted_gate(frozen, stayers, n_boot)
    record.update(
        {
            "analysis": "E33",
            "amendment_22": {"path": AMENDMENT.as_posix(), "sha256": AMENDMENT_SHA},
            "status": "passed",
            "outcomes_read": "none: of the scored file only the key, the season and the two leagues",
            "bootstrap_draws": n_boot,
            "seed": SEED,
        }
    )
    lc.write_json(out / GATES_NAME, record)
    return record


# ---------------------------------------------------------------------------
# The single run.


def classify(cutoff: dict, difference: dict) -> str:
    """Amendment 22, 'What the paper may say'."""
    low = cutoff["ci95"][0]
    d_low, d_high = difference["ci95"]
    if low <= 0:
        return "not_above_zero"
    if d_low <= 0 <= d_high:
        return "same"
    return "different_lower" if d_high < 0 else "different_higher"


def analyse(
    frozen, stayers, scored, retained: dict, n_boot: int = N_BOOT, seed: int = SEED
) -> dict:
    """G33c, then E33. ``scored`` carries ``rate_to``; it is joined one to one on the key."""
    moves = frozen.merge(
        scored[lc.KEY + ["rate_to"]], on=lc.KEY, how="left", validate="one_to_one"
    )
    if not (moves[lc.KEY].to_numpy() == frozen[lc.KEY].to_numpy()).all():
        raise GateFailure("the join changed the order of the frozen rows")
    use = np.isfinite(moves.g_refit.to_numpy(float))
    if not np.isfinite(moves.rate_to.to_numpy(float)[use]).all():
        raise GateFailure("an outcome of a selected league change is missing")
    ctx = context(moves, stayers, np.nan_to_num(moves.rate_to.to_numpy(float)))
    # G33c first: nothing of E33 is computed unless sensitivity (7) is reproduced
    reproduction, pooled_point, pooled_draws = reproduction_gate(
        ctx, retained, n_boot, seed
    )
    point = points(ctx, [cutoff_statistics])
    sample = draws(ctx, [cutoff_statistics], n_boot, seed)
    cutoff = entry(point["cutoff"], sample["cutoff"])
    d = sample["cutoff"] - pooled_draws["pooled"]
    difference = entry(point["cutoff"] - pooled_point["pooled"], d)
    difference["sd"] = float(np.std(d, ddof=1))
    difference["detectable_80"] = DETECTABLE_FACTOR * difference["sd"]
    ones = np.ones(len(ctx["Sy"]))
    by_season = []
    for t in SEASONS:
        fit = ctx["training"][t]
        beta = lc.wls(ctx["SX"][fit], ctx["Sy"][fit], ones[fit])
        rows = ctx["season_rows"][t]
        by_season.append(
            {
                "arrival_season": t,
                "league_changes": int(rows.sum()),
                "players": int(moves.player_name[rows].nunique()),
                "stayer_training_rows": int(fit.sum()),
                "latest_stayer_outcome_season": int(ctx["stayer_season"][fit].max()),
                **dict(zip(lc.STAYER_TERMS, beta.tolist())),
            }
        )
    return {
        "analysis": "E33",
        "status": "exploratory: the outcomes had been read by the scoring run of E30",
        "league_changes": int(use.sum()),
        "players": int(moves.player_name[use].nunique()),
        "players_resampled": ctx["n_players"],
        "stayer_pairs": int(len(stayers)),
        "bootstrap_draws": n_boot,
        "seed": seed,
        "G33c_reproduction": reproduction,
        "cutoff": cutoff,
        "pooled": reproduction["found"],
        "difference": difference,
        "season_intercepts": {
            "cutoff": entry(
                point["cutoff_season_intercepts"], sample["cutoff_season_intercepts"]
            ),
            "pooled": entry(
                pooled_point["pooled_season_intercepts"],
                pooled_draws["pooled_season_intercepts"],
            ),
        },
        "case": classify(cutoff, difference),
        "by_arrival_season": by_season,
    }


def slope_rows(result: dict) -> pd.DataFrame:
    rows = [
        ("E33: stayer forecast fitted only on earlier seasons", result["cutoff"]),
        (
            "sensitivity (7) reproduced: stayer forecast fitted on all seasons",
            result["pooled"],
        ),
        ("difference, E33 minus sensitivity (7), same draws", result["difference"]),
        (
            "E33 with one intercept per arrival season",
            result["season_intercepts"]["cutoff"],
        ),
        (
            "sensitivity (7) with one intercept per arrival season",
            result["season_intercepts"]["pooled"],
        ),
    ]
    return pd.DataFrame(
        [
            {
                "label": label,
                "league_changes": result["league_changes"],
                "estimate": item["estimate"],
                "ci95_low": item["ci95"][0],
                "ci95_high": item["ci95"][1],
            }
            for label, item in rows
        ]
    )


def score(root: Path, gates_path: Path, out: Path, n_boot: int = N_BOOT) -> dict:
    root, out = Path(root), Path(out)
    out.mkdir(parents=True, exist_ok=True)
    gate_record = json.loads(Path(gates_path).read_text())
    if gate_record.get("status") != "passed" or gate_record.get("analysis") != "E33":
        raise GateFailure("the record of the gates subcommand does not say 'passed'")
    if gate_record["amendment_22"]["sha256"] != AMENDMENT_SHA:
        raise GateFailure("the gates were run under another text of Amendment 22")
    frozen, stayers, scored_keys = load_inputs(root)
    record = outcome_free_gates(root, frozen, stayers, scored_keys)
    retained = json.loads((root / PINS["e30_summary"][0]).read_text())["S_e"]["7"]
    if retained["league_changes"] != EXPECTED_ROWS:
        raise GateFailure("the retained sensitivity (7) is not on the registered rows")
    scored = pd.read_parquet(root / PINS["scored"][0], columns=lc.KEY + ["rate_to"])
    result = analyse(frozen, stayers, scored, retained, n_boot)
    result.update(
        {
            "amendment_22": {"path": AMENDMENT.as_posix(), "sha256": AMENDMENT_SHA},
            "inputs": {
                name: {"path": path, "sha256": sha}
                for name, (path, sha) in PINS.items()
            },
            "gates_record_sha256": sha256_file(gates_path),
            "gates": {
                **record,
                "G33c_reproduction": result.pop("G33c_reproduction"),
                "G33e_planted_slope": gate_record["G33e_planted_slope"],
            },
        }
    )
    lc.write_json(out / SUMMARY_NAME, result)
    slope_rows(result).to_csv(out / SLOPES_NAME, index=False)
    pd.DataFrame(result["by_arrival_season"]).to_csv(out / SEASONS_NAME, index=False)
    return result


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    commands = parser.add_subparsers(dest="command", required=True)
    made_up = commands.add_parser(
        "gates", help="G33a, G33b, G33d, G33e; no outcome read"
    )
    made_up.add_argument("--out", type=Path, required=True)
    scoring = commands.add_parser("score", help="the single run: G33c, then E33")
    scoring.add_argument("--gates", type=Path, required=True)
    scoring.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    root = Path.cwd()
    if args.command == "gates":
        record = gates(root, args.out)
        print(
            f"E33 gates {record['status']}: planted 1.0 -> {record['G33e_planted_slope']['planted_slope_one']['slope']:.4f}"
        )
    else:
        result = score(root, args.gates, args.out)
        print(f"E33 case: {result['case']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
