#!/usr/bin/env python
"""Restate the pre-registration §7 power table at the scored population.

Amendment 2 Change 3 published a power table "scaling each contrast's observed
pooled interval to the prospective set" and Amendment 2 Change 4 / Amendment 4
require it to be restated at the dated collection's count. No committed code
produced the original table (its B1b row, +0.2014, matches no field in
``walkforward_summary.json``), so this is the generator (METHOD.md §16): every
row names the JSON field it reads, and the arithmetic is the one the amendment
describes and nothing more.

Method, stated before the numbers::

    se_pooled  = (ci_hi - ci_lo) / (2 * 1.96)        # from the walk-forward CI
    se_n       = se_pooled * sqrt(n_pooled / n)      # scale to the prospective n
    power(n)   = P(Z > 1.96 - effect / se_n)         # one-sided at the 5% two-sided bar
    n_for_80   = n_pooled * ((1.96 + 0.8416) * se_pooled / effect) ** 2

Rows, and the walk-forward contrast each reads:

* beat B0 (untranslated)              ``pooled.delta_vs_b0`` / ``pooled.ci_b0``
* beat one global scalar              ``pooled.delta_vs_global`` / ``pooled.ci``
  — the walk-forward has no B1b arm; this is the nearest committed
  single-constant comparator and is labelled as such, not as B1b.
* combined beats B1c (RTM)            ``rtm_comparator.rtm_plus_league_vs_rtm``
* combined beats per-league alone     ``rtm_comparator.rtm_plus_league_vs_per_league``

Usage::

    uv run python scripts/restate_prediction_power.py \\
        --walkforward data/processed/translation/walkforward_summary.json \\
        --n 51 [--n ...] [--out data/processed/predictions/power_restated.json]
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

Z_ALPHA = 1.959964  # two-sided 5%
Z_POWER = 0.841621  # 80%


def _phi(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def power_at(effect: float, se_pooled: float, n_pooled: int, n: int) -> float:
    if effect <= 0 or se_pooled <= 0 or n <= 0:
        return float("nan")
    se_n = se_pooled * math.sqrt(n_pooled / n)
    return _phi(effect / se_n - Z_ALPHA)


def n_for_power(
    effect: float, se_pooled: float, n_pooled: int, target_z=Z_POWER
) -> int | None:
    if effect <= 0 or se_pooled <= 0:
        return None
    return int(math.ceil(n_pooled * ((Z_ALPHA + target_z) * se_pooled / effect) ** 2))


def p1_threshold(se_n: float, margin: float, b0_mae: float) -> float:
    """P1 as written (base document §8, Amendment 1 Change 4) has two clauses:
    the model's MAE must sit at or below B0's by the relative margin, AND the
    paired CI on the contrast must exclude zero. In contrast units
    (Δ = MAE_B0 − MAE_model) the margin clause is Δ ≥ margin·MAE_B0 and the CI
    clause is Δ ≥ 1.96·SE, so the test passes iff Δ̂ clears the larger."""
    return max(Z_ALPHA * se_n, margin * b0_mae)


def p1_power(
    effect: float,
    se_n: float,
    margin: float,
    b0_mae: float,
    tau2: float = 0.0,
) -> float:
    """P(Δ̂ ≥ threshold) with Δ̂ ~ N(effect, se_n² + tau2). tau2 = 0 is the
    conditional power the §7 table implied (this season's effect equals the
    pooled one); tau2 > 0 is predictive power, integrating over the
    between-season variance Study D measured (Amendment 9)."""
    if se_n <= 0:
        return float("nan")
    sd = math.sqrt(se_n**2 + max(tau2, 0.0))
    return 1.0 - _phi((p1_threshold(se_n, margin, b0_mae) - effect) / sd)


def se_inflation_from_rehearsal(
    rehearsals: list[dict], se_pooled: float, n_pooled: int
) -> dict:
    """Realised paired-bootstrap SE of the Δ-vs-B0 contrast on each rehearsal
    read, over the SE the §7 scaling predicts at that read's n."""
    ratios = {}
    for e in rehearsals:
        h = e["headline"]
        c = h["contrasts"]["B0"]
        realised = (c["ci_high"] - c["ci_low"]) / (2 * Z_ALPHA)
        scaled = se_pooled * math.sqrt(n_pooled / h["n_scored"])
        ratios[f"{e['as_of']} {e['population']['rule']}"] = realised / scaled
    return {
        "per_read": ratios,
        "max": max(ratios.values()) if ratios else 1.0,
        "source": "rehearsal_eval_*.json headline.contrasts.B0 vs se_pooled*sqrt(n_pooled/n_scored)",  # noqa: E501
    }


def p1_as_written(
    summary: dict,
    ns: list[int],
    margin: float,
    *,
    se_inflation: float = 1.0,
    tau2: float = 0.0,
) -> dict:
    """The P1 row restated for both clauses, at the scaled SE and at the
    rehearsal-inflated SE, conditional and predictive."""
    p = summary["pooled"]
    effect = float(p["delta_vs_b0"])
    b0_mae = float(p["mae_b0"])
    se_pooled = float((p["ci_b0"][1] - p["ci_b0"][0]) / (2 * Z_ALPHA))
    n_pooled = int(summary["n_pooled"])
    rows = {}
    for n in ns:
        se_n = se_pooled * math.sqrt(n_pooled / n)
        se_infl = se_n * se_inflation
        rows[str(n)] = {
            "se_scaled": se_n,
            "se_inflated": se_infl,
            "threshold_ci_clause_scaled": Z_ALPHA * se_n,
            "threshold_margin_clause": margin * b0_mae,
            "binding_clause_scaled": (
                "CI" if Z_ALPHA * se_n >= margin * b0_mae else "margin"
            ),
            "power_ci_clause_only_scaled": power_at(effect, se_pooled, n_pooled, n),
            "power_two_clause_scaled": p1_power(effect, se_n, margin, b0_mae),
            "power_two_clause_inflated": p1_power(effect, se_infl, margin, b0_mae),
            "power_two_clause_inflated_predictive": p1_power(
                effect, se_infl, margin, b0_mae, tau2
            ),
        }
    return {
        "criterion": "P1 as written: beat B0 by the relative margin AND paired CI excludes zero",  # noqa: E501
        "field": "pooled.delta_vs_b0 / pooled.mae_b0 / pooled.ci_b0",
        "effect": effect,
        "b0_mae": b0_mae,
        "margin": margin,
        "margin_in_contrast_units": margin * b0_mae,
        "se_pooled": se_pooled,
        "se_inflation": se_inflation,
        "tau2": tau2,
        "method": (
            "threshold = max(1.96*se_n, margin*MAE_B0); power = 1 - Phi((threshold - effect) / sqrt(se_n^2 + tau2)); "  # noqa: E501
            "se_n = se_pooled*sqrt(n_pooled/n) [*se_inflation]; tau2 = 0 conditional, tau2 = Study D REML between-season variance predictive"  # noqa: E501
        ),
        "at_n": rows,
    }


def contrasts(summary: dict) -> list[dict]:
    p, r = summary["pooled"], summary["rtm_comparator"]
    rows = [
        (
            "beat B0 (untranslated source rate)",
            "primary",
            "pooled.delta_vs_b0",
            p["delta_vs_b0"],
            p["ci_b0"],
        ),
        (
            "beat one global scalar (nearest committed single-constant "
            "comparator; NOT B1b)",
            "primary (B1b proxy)",
            "pooled.delta_vs_global",
            p["delta_vs_global"],
            p["ci"],
        ),
        (
            "combined beats B1c (RTM, league-free)",
            "secondary",
            "rtm_comparator.rtm_plus_league_vs_rtm",
            r["rtm_plus_league_vs_rtm"]["delta"],
            r["rtm_plus_league_vs_rtm"]["ci"],
        ),
        (
            "combined beats per-league alone",
            "secondary",
            "rtm_comparator.rtm_plus_league_vs_per_league",
            r["rtm_plus_league_vs_per_league"]["delta"],
            r["rtm_plus_league_vs_per_league"]["ci"],
        ),
    ]
    return [
        {
            "criterion": c,
            "status": st,
            "field": f,
            "effect": float(d),
            "ci": [float(ci[0]), float(ci[1])],
            "se_pooled": float((ci[1] - ci[0]) / (2 * Z_ALPHA)),
        }
        for c, st, f, d, ci in rows
    ]


def restate(summary: dict, ns: list[int]) -> dict:
    n_pooled = int(summary["n_pooled"])
    rows = []
    for c in contrasts(summary):
        row = dict(c)
        row["power_at_n"] = {
            str(n): round(power_at(c["effect"], c["se_pooled"], n_pooled, n), 3)
            for n in ns
        }
        row["n_for_80pct"] = n_for_power(c["effect"], c["se_pooled"], n_pooled)
        rows.append(row)
    return {
        "method": (
            "se_pooled = CI width / (2*1.96); se_n = se_pooled * sqrt(n_pooled/n); "
            "power = Phi(effect/se_n - 1.96); n_for_80 = n_pooled * "
            "((1.96 + 0.8416) * se_pooled / effect)^2"
        ),
        "walkforward_n_pooled": n_pooled,
        "walkforward_continental_source": summary.get("continental_source"),
        "prospective_n": ns,
        "rows": rows,
    }


def render_p1(block: dict) -> str:
    L = [
        f"P1 as written (margin {block['margin']:.1%} of MAE_B0 = {block['margin_in_contrast_units']:.3f} in contrast units; effect {block['effect']:+.3f}; SE inflation ×{block['se_inflation']:.2f}; τ² {block['tau2']:.4f})",  # noqa: E501
        "| n | SE scaled | binding clause | power CI-only (§7 table) | power two-clause | two-clause, inflated SE | two-clause, inflated, predictive |",  # noqa: E501
        "|---:|---:|---|---:|---:|---:|---:|",
    ]
    for n, r in block["at_n"].items():
        L.append(
            f"| {n} | {r['se_scaled']:.3f} | {r['binding_clause_scaled']} | {r['power_ci_clause_only_scaled']:.2f} | {r['power_two_clause_scaled']:.2f} | {r['power_two_clause_inflated']:.2f} | {r['power_two_clause_inflated_predictive']:.2f} |"  # noqa: E501
        )
    return "\n".join(L)


def render(table: dict) -> str:
    ns = table["prospective_n"]
    head = (
        "| criterion | field | pooled effect | "
        + " | ".join(f"power at n={n}" for n in ns)
        + " | n for 80% |"
    )
    sep = "|" + "---|" * (4 + len(ns))
    lines = [head, sep]
    for r in table["rows"]:
        lines.append(
            f"| {r['criterion']} *({r['status']})* | `{r['field']}` | "
            f"{r['effect']:+.4f} [{r['ci'][0]:+.4f}, {r['ci'][1]:+.4f}] | "
            + " | ".join(f"{r['power_at_n'][str(n)]:.2f}" for n in ns)
            + f" | {r['n_for_80pct']} |"
        )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--walkforward", type=Path, required=True)
    ap.add_argument("--n", type=int, action="append", required=True)
    ap.add_argument("--out", type=Path, default=None)
    ap.add_argument(
        "--p1-as-written",
        action="store_true",
        help="add the two-clause P1 block (Amendment 9)",
    )
    ap.add_argument(
        "--margin",
        type=float,
        default=None,
        help="B0 margin; default: the evaluator's B0_MARGIN",
    )  # noqa: E501
    ap.add_argument(
        "--rehearsal",
        type=Path,
        action="append",
        default=[],
        help="rehearsal evaluator payload(s); the max realised/scaled SE ratio inflates the SE",  # noqa: E501
    )
    ap.add_argument(
        "--evidence-synthesis",
        type=Path,
        default=None,
        help="Study D summary; its per_league_vs_b0 REML tau^2 gives the predictive power",  # noqa: E501
    )
    args = ap.parse_args(argv)
    summary = json.loads(args.walkforward.read_text())
    table = restate(summary, args.n)
    print(render(table))
    if args.p1_as_written:
        if args.margin is None:
            from scripts.evaluate_translation_predictions import B0_MARGIN

            args.margin = B0_MARGIN
        p = summary["pooled"]
        se_pooled = float((p["ci_b0"][1] - p["ci_b0"][0]) / (2 * Z_ALPHA))
        infl = se_inflation_from_rehearsal(
            [json.loads(r.read_text()) for r in args.rehearsal],
            se_pooled,
            int(summary["n_pooled"]),
        )
        tau2 = 0.0
        if args.evidence_synthesis is not None:
            syn = json.loads(args.evidence_synthesis.read_text())
            tau2 = float(syn["contrasts"]["per_league_vs_b0"]["reml_hksj"]["tau2"])
        block = p1_as_written(
            summary, args.n, args.margin, se_inflation=infl["max"], tau2=tau2
        )
        block["se_inflation_detail"] = infl
        block["tau2_source"] = (
            str(args.evidence_synthesis) if args.evidence_synthesis else "none (0)"
        )
        table["p1_as_written"] = block
        print()
        print(render_p1(block))
    print("\n[json]", json.dumps(table, indent=1))
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(table, indent=1))
        print(f"[done] wrote {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
