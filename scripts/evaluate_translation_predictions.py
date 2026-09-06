#!/usr/bin/env python
"""Score the locked 2026-27 predictions at a checkpoint (ATI-2891).

§9 fixes two reads -- 2027-01-31 and 2027-06-30 -- and acceptance criterion 4
requires this to run end-to-end on synthetic or partial data **before** tip-off,
so the first real checkpoint is not also the first time it executes.

Every bar below is a named constant lifted from the pre-registration, in the
same style as `validate_translation_holdout.py`'s `G1_RATIO`. None of them may
be edited after the first 2026-27 game is played, including by a rounding
margin and including while calling the new value conventional (METHOD.md §8).

Usage::

    uv run python scripts/evaluate_translation_predictions.py \\
        --predictions <translation_predictions_2026.json> \\
        --outcomes <realised.json> --as-of 2027-01-31
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from scripts.collect_import_signings import write_payload  # noqa: E402

# --------------------------------------------------------------- the bars --
#: §8 primary 1. RELATIVE to B0's MAE, not an absolute PIR/36 margin.
B0_MARGIN = 0.128

#: §8 secondary. Over-coverage and under-coverage are BOTH failures (§6): an
#: interval too wide is as uninformative as one too narrow, and a one-sided
#: check would let a model pass by publishing intervals that contain everything.
COVERAGE_BAND = (0.90, 0.98)

#: §2/§9. Headline threshold; the end-of-season read also reports these two as
#: the T7 survivorship sensitivity.
MIN_DEST_GAMES = 8
SENSITIVITY_GAMES = (5, 15)

#: §6. Players on one club in one season are not independent observations.
N_BOOT = 4000
SEED = 0

#: §6. Destination split-half reliability implies this maximum attainable R².
R2_CEILING = 0.70

_PRIMARY_GATES = ("P1_beats_b0", "P2_beats_b1b")
_SECONDARY_GATES = ("S1_beats_b1c", "S2_coverage_in_band")


def beats_by_margin(*, model_mae: float, baseline_mae: float, margin: float) -> bool:
    """Does the model beat the baseline by at least `margin` OF the baseline?

    §8 states the bar as a share of B0's MAE. An absolute margin would be a far
    weaker bar at these error levels, and the two only coincide by accident.
    """
    return model_mae <= baseline_mae * (1 - margin)


def interval_coverage(rows) -> dict:
    """Realised coverage of the published intervals, and whether it is in band.

    `rows` is an iterable of (observed, interval_low, interval_high).
    """
    rows = list(rows)
    if not rows:
        raise ValueError("no rows: coverage of an empty set is not 0, it is undefined")
    hits = sum(1 for y, lo, hi in rows if lo <= y <= hi)
    covered = hits / len(rows)
    lo_band, hi_band = COVERAGE_BAND
    return {
        "n": len(rows),
        "covered": covered,
        "in_band": lo_band <= covered <= hi_band,
        "band": list(COVERAGE_BAND),
    }


def verdict(gates: dict) -> str:
    """§11's rule, as written.

    Reads every gate by name so a missing one raises rather than defaulting --
    defaulting a missing primary to True would publish a PASS nobody measured.
    """
    primaries = [gates[g] for g in _PRIMARY_GATES]
    for g in _SECONDARY_GATES:
        gates[g]  # noqa: B018 - presence check; secondaries never move the verdict

    if not gates["P1_beats_b0"]:
        # §11 On FAIL: publish the negative result, not projections.
        return "FAIL"
    if all(primaries):
        return "PASS"
    # §11 On PARTIAL: a baseline-superiority sub-gate failed or tied. §7 warns
    # this is the most likely 2026-27 outcome by construction -- B1b has ~36%
    # power at n=110 -- and that it must not be read as the model failing.
    return "PARTIAL"


def paired_cluster_bootstrap(y, pa, pb, clusters, *, n_boot=N_BOOT, seed=SEED):
    """Delta in MAE (b - a) with a 95% CI, resampled on destination club-season."""
    y, pa, pb = np.asarray(y, float), np.asarray(pa, float), np.asarray(pb, float)
    clusters = np.asarray(clusters)
    uniq = np.unique(clusters)
    idx = {c: np.flatnonzero(clusters == c) for c in uniq}
    rng = np.random.default_rng(seed)
    deltas = np.empty(n_boot)
    for b in range(n_boot):
        pick = rng.choice(uniq, size=len(uniq), replace=True)
        rows = np.concatenate([idx[c] for c in pick])
        deltas[b] = np.mean(np.abs(pb[rows] - y[rows])) - np.mean(
            np.abs(pa[rows] - y[rows])
        )
    point = float(np.mean(np.abs(pb - y)) - np.mean(np.abs(pa - y)))
    lo, hi = np.percentile(deltas, [2.5, 97.5])
    return point, float(lo), float(hi)


def _mae(y, p) -> float:
    return float(np.mean(np.abs(np.asarray(p, float) - np.asarray(y, float))))


def _r2(y, p) -> float:
    y, p = np.asarray(y, float), np.asarray(p, float)
    sst = float(np.sum((y - y.mean()) ** 2))
    return float(1 - np.sum((y - p) ** 2) / sst) if sst > 0 else float("nan")


def mae_by_source_season_lag(scored: list[tuple[dict, dict]], arms: dict) -> dict:
    """Amendment 6: model and B0 MAE on rows whose source season is the latest
    possible one (lag 0) against rows that reach further back (lag > 0).

    Descriptive only — no gate reads it. The lagged group is small (7 of 50 on
    the 2026-08-21 collection), so the read says whether stale rows miss by
    more, not by how much. Rows built before the field existed land in
    ``unknown`` rather than being silently pooled with lag 0.
    """
    groups: dict[str, list[int]] = {"lag_0": [], "lag_gt_0": [], "unknown": []}
    for i, (p, _) in enumerate(scored):
        lag = p.get("source_season_lag")
        key = "unknown" if lag is None else ("lag_0" if lag == 0 else "lag_gt_0")
        groups[key].append(i)
    y = np.asarray([o["pir_per36"] for _, o in scored], float)
    out = {}
    for key, idx in groups.items():
        if not idx:
            out[key] = {"n": 0}
            continue
        sel = np.asarray(idx)
        out[key] = {
            "n": len(idx),
            "model_mae": _mae(y[sel], np.asarray(arms["model"], float)[sel]),
            "b0_mae": _mae(y[sel], np.asarray(arms["B0"], float)[sel]),
        }
    return out


def load_outcomes(raw) -> dict:
    """Index an outcomes file by person_code.

    Accepts the bare list the pre-registration described and the payload
    ``build_realised_outcomes.py`` writes (``{"outcomes": [...]}`` under a
    header of counts). The header counts are the record; they are not altered.
    """
    if isinstance(raw, dict):
        raw = raw["outcomes"]
    return {o["person_code"]: o for o in raw}


def restrict_population(
    predictions: list[dict], full_outcomes: dict, first_round_max: int
) -> tuple[list[dict], dict]:
    """Keep the predictions whose player's FULL-SEASON outcome row has
    ``first_round <= first_round_max`` (Amendment 5's primary population).

    The filter is applied to the prediction list, never to the outcomes an
    as-of checkpoint scores against: filtering outcomes would turn every
    mid-season arrival into an R8 censor and inflate that count.
    """
    keep = {
        code
        for code, o in full_outcomes.items()
        if o.get("first_round") is not None and o["first_round"] <= first_round_max
    }
    kept = [p for p in predictions if p["person_code"] in keep]
    return kept, {
        "rule": f"full-season first_round <= {first_round_max}",
        "n_before": len(predictions),
        "n_after": len(kept),
        "n_dropped_later_arrivals": len(predictions) - len(kept),
    }


def load_secondary(raw: dict, predictions: list[dict]) -> dict:
    """person_code -> the dynamic arm's point prediction (Amendment 10).

    Every primary row must have a secondary row: the amendment fixes the two
    populations as identical, so a missing code is an error, never a drop.
    """
    sec = {r["person_code"]: float(r["projection_dynamic"]) for r in raw["predictions"]}
    missing = [p["person_code"] for p in predictions if p["person_code"] not in sec]
    if missing:
        raise ValueError(
            f"secondary arm lacks {len(missing)} of the primary's person_codes "
            f"(first: {missing[:3]}) -- Amendment 10 requires identical populations"
        )
    return sec


def score_checkpoint(
    predictions: list[dict],
    outcomes: dict,
    min_games: int,
    secondary: dict | None = None,
) -> dict:
    """Score every prediction whose player has reached `min_games`.

    Players below the threshold are CENSORED under refusal R8 and counted, not
    dropped silently: §7's survivorship threat is only measurable if the
    unscored are reported alongside the scored.

    `secondary` (Amendment 10) adds the dynamic-ability arm to `metrics` and
    two contrasts; it touches no gate and cannot move the verdict.
    """
    scored, censored = [], []
    for p in predictions:
        o = outcomes.get(p["person_code"])
        if o is None or o["games"] < min_games:
            censored.append(p["person_code"])
            continue
        scored.append((p, o))

    if not scored:
        raise ValueError(
            f"no player reached {min_games} destination games at this "
            "checkpoint. That is a censored read, not a result."
        )

    y = [o["pir_per36"] for _, o in scored]
    clusters = [o["club_season"] for _, o in scored]
    arms = {
        "model": [p["projection"] for p, _ in scored],
        "B0": [p["baseline_b0"] for p, _ in scored],
        "B1c": [p["baseline_b1c"] for p, _ in scored],
    }
    # §5: B1b's constant is fitted to minimise error on the scored set itself,
    # so it cannot exist until the outcomes do. That oracle advantage is
    # deliberate and is why beating it is the demanding primary.
    src = np.asarray(arms["B0"], float)
    k = float(np.sum(src * np.asarray(y, float)) / np.sum(src * src))
    arms["B1b"] = list(src * k)
    if secondary is not None:
        arms["dynamic"] = [secondary[p["person_code"]] for p, _ in scored]

    metrics = {
        name: {"mae": _mae(y, p), "r2": _r2(y, p), "n": len(y)}
        for name, p in arms.items()
    }
    contrasts = {
        name: dict(
            zip(
                ("delta", "ci_low", "ci_high"),
                paired_cluster_bootstrap(y, arms["model"], arms[name], clusters),
            )
        )
        for name in ("B0", "B1b", "B1c")
    }
    if secondary is not None:
        # reported beside B1c, never gated: model vs dynamic, and dynamic vs B0
        contrasts["dynamic"] = dict(
            zip(
                ("delta", "ci_low", "ci_high"),
                paired_cluster_bootstrap(y, arms["model"], arms["dynamic"], clusters),
            )
        )
        contrasts["dynamic_vs_B0"] = dict(
            zip(
                ("delta", "ci_low", "ci_high"),
                paired_cluster_bootstrap(y, arms["dynamic"], arms["B0"], clusters),
            )
        )
    coverage = interval_coverage(
        (o["pir_per36"], p["interval_low"], p["interval_high"]) for p, o in scored
    )
    by_lag = mae_by_source_season_lag(scored, arms)

    gates = {
        "P1_beats_b0": beats_by_margin(
            model_mae=metrics["model"]["mae"],
            baseline_mae=metrics["B0"]["mae"],
            margin=B0_MARGIN,
        )
        and contrasts["B0"]["ci_low"] > 0,
        "P2_beats_b1b": metrics["model"]["mae"] < metrics["B1b"]["mae"]
        and contrasts["B1b"]["ci_low"] > 0,
        "S1_beats_b1c": metrics["model"]["mae"] < metrics["B1c"]["mae"]
        and contrasts["B1c"]["ci_low"] > 0,
        "S2_coverage_in_band": coverage["in_band"],
        "b1b_k": k,
    }
    verdict_gates = {g: gates[g] for g in (*_PRIMARY_GATES, *_SECONDARY_GATES)}
    return {
        "min_games": min_games,
        "n_scored": len(scored),
        "n_censored_R8": len(censored),
        "metrics": metrics,
        "r2_ceiling": R2_CEILING,
        "contrasts": contrasts,
        "coverage": coverage,
        "by_source_season_lag": by_lag,
        "gates": gates,
        "verdict": verdict(verdict_gates),
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--predictions", type=Path, required=True)
    ap.add_argument("--outcomes", type=Path, required=True)
    ap.add_argument("--as-of", required=True, help="checkpoint date, YYYY-MM-DD")
    ap.add_argument("--out", type=Path, default=None)
    ap.add_argument(
        "--first-round-max",
        type=int,
        default=None,
        help="restrict to players whose FULL-season first RS round is <= N "
        "(Amendment 5 primary population; needs --full-outcomes)",
    )
    ap.add_argument(
        "--full-outcomes",
        type=Path,
        default=None,
        help="uncensored full-season outcomes file the population filter reads",
    )
    ap.add_argument(
        "--secondary",
        type=Path,
        default=None,
        help="dynamic_predictions_<season>.json (Amendment 10): scored beside the "
        "primary as arm `dynamic`; no gate, cannot move the verdict",
    )
    args = ap.parse_args(argv)

    pred = json.loads(args.predictions.read_text())
    outcomes = load_outcomes(json.loads(args.outcomes.read_text()))
    population = {"rule": "every predicted player", "n": len(pred["predictions"])}
    if args.first_round_max is not None:
        if args.full_outcomes is None:
            ap.error("--first-round-max needs --full-outcomes")
        full = load_outcomes(json.loads(args.full_outcomes.read_text()))
        pred["predictions"], population = restrict_population(
            pred["predictions"], full, args.first_round_max
        )
        print(f"population: {population}")

    if pred["status"] != "locked":
        print(
            f"WARNING: scoring a '{pred['status']}' prediction set. Only a "
            "LOCKED set scores as evidence; anything else is a rehearsal.",
            file=sys.stderr,
        )

    secondary = None
    if args.secondary is not None:
        sec_raw = json.loads(args.secondary.read_text())
        if sec_raw.get("status") != pred["status"]:
            print(
                f"WARNING: secondary status '{sec_raw.get('status')}' differs from the "
                f"primary's '{pred['status']}'",
                file=sys.stderr,
            )
        secondary = load_secondary(sec_raw, pred["predictions"])

    head = score_checkpoint(pred["predictions"], outcomes, MIN_DEST_GAMES, secondary)
    sensitivity = {}
    for g in SENSITIVITY_GAMES:
        try:
            sensitivity[str(g)] = score_checkpoint(
                pred["predictions"], outcomes, g, secondary
            )
        except ValueError as exc:  # a censored read is reported, not fatal
            sensitivity[str(g)] = {"censored": str(exc)}

    m = head["metrics"]
    print(f"=== checkpoint {args.as_of}: {head['verdict']} ===")
    print(f"scored {head['n_scored']}, censored (R8) {head['n_censored_R8']}")
    for name, v in m.items():
        print(f"  {name:6s} MAE {v['mae']:.4f}  R2 {v['r2']:+.4f}")
    print(f"  R2 ceiling {R2_CEILING} (destination split-half reliability)")
    for name, c in head["contrasts"].items():
        print(
            f"  vs {name:4s} delta {c['delta']:+.4f} "
            f"CI [{c['ci_low']:+.4f}, {c['ci_high']:+.4f}]"
        )
    cov = head["coverage"]
    print(
        f"  interval coverage {cov['covered']:.3f} in band {cov['band']}: "
        f"{cov['in_band']} (over- and under-coverage both fail)"
    )
    for g in (*_PRIMARY_GATES, *_SECONDARY_GATES):
        print(f"  {g}: {head['gates'][g]}")

    if head["verdict"] == "PARTIAL":
        print(
            "\nPARTIAL: §7 states this is the most likely 2026-27 outcome by "
            "construction -- B1b carries ~36% power at this n. It is the season "
            "being too small to adjudicate, NOT the model having failed. §11 "
            "requires publishing with the scope narrowed to the passing claims "
            "and the failing sub-gate named in the body, not a footnote."
        )

    if secondary is not None:
        print(
            "  Amendment 10 secondary arm `dynamic` (reported, not gated): "
            f"MAE {m['dynamic']['mae']:.4f}; model vs dynamic "
            f"{head['contrasts']['dynamic']['delta']:+.4f} "
            f"[{head['contrasts']['dynamic']['ci_low']:+.4f}, "
            f"{head['contrasts']['dynamic']['ci_high']:+.4f}]"
        )
    payload = {
        "as_of": args.as_of,
        "prediction_status": pred["status"],
        "secondary_arm": None if args.secondary is None else str(args.secondary.name),
        "prediction_built_at": pred["built_at"],
        "population": population,
        "headline": head,
        "survivorship_sensitivity": sensitivity,
    }
    if args.out:
        print(f"\nWrote {write_payload(payload, args.out)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
