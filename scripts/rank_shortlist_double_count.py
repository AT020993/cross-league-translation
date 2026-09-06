"""Study B — the scout's shortlist: what the double-count costs in ranks.

Pre-registered in ``docs/research/translation-application-studies-preregistration-
2026-09-06.md``. On each walk-forward season, rank the cohort by predicted
EFF/36 under the multiplier-only arm (`per_league`) and the combined arm
(`rtm_plus_league`); take the top-K. Read (a) the mean realised EFF/36 of each
arm's top-K, (b) how many of the top-K finish outside the realised top-2K
("overpaid"), (c) the share of career-year players (`above_own_prior`) in each
top-K. Paired bootstrap over rows within season for (a) and (b); the
career-year flag permuted within season as the null for (c). Placebo:
`per_league` vs `one_global` (league resolution, no RTM term).

Reads ``walkforward_rows.parquet`` written by
``validate_translation_walkforward.py --rows-out`` (which now carries
`prior_mean_pir36` and `above_own_prior`) -- never refits a fold.

    uv run python scripts/rank_shortlist_double_count.py --rows ROWS --out-dir OUT
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
SEED = 0
N_BOOT = 2000
N_PERM = 200
KS = (10, 5, 20)  # 10 is primary
PRIMARY = ("per_league", "rtm_plus_league")
PLACEBO = ("one_global", "per_league")
_DEFAULT_ROWS = (
    REPO
    / "docs"
    / "research"
    / "artifacts"
    / "prelock-program-2026-09"
    / "walkforward_rows.parquet"
)
_DEFAULT_OUT = REPO / "docs" / "research" / "artifacts" / "application-studies-2026-09"


def top_k_stats(df: pd.DataFrame, arm: str, k: int) -> dict:
    """Mean realised y of the arm's top-k, the overpaid count, the career-year share."""
    order = np.argsort(-df[arm].to_numpy(float), kind="stable")[:k]
    y = df.y.to_numpy(float)
    realised_rank = np.argsort(np.argsort(-y, kind="stable"), kind="stable")
    flag = df.above_own_prior.to_numpy()
    top = order
    defined = np.array([f is not None and f == f for f in flag[top]], dtype=bool)
    share = (
        float(np.mean(flag[top][defined].astype(bool)))
        if defined.any()
        else float("nan")
    )
    return {
        "mean_realised": float(y[top].mean()),
        "overpaid": int((realised_rank[top] >= 2 * k).sum()),
        "career_year_share": share,
    }


def season_contrast(df: pd.DataFrame, a: str, b: str, k: int) -> dict:
    """b minus a on the three reads, with a paired row-bootstrap CI (rows resampled
    within the season, both arms recomputed on the same resample)."""
    sa, sb = top_k_stats(df, a, k), top_k_stats(df, b, k)
    rng = np.random.default_rng(SEED)
    n = len(df)
    d_mean, d_over = np.empty(N_BOOT), np.empty(N_BOOT)
    for i in range(N_BOOT):
        r = df.iloc[rng.integers(0, n, n)]
        ta, tb = top_k_stats(r, a, k), top_k_stats(r, b, k)
        d_mean[i] = tb["mean_realised"] - ta["mean_realised"]
        d_over[i] = tb["overpaid"] - ta["overpaid"]
    # career-year share under the null: the flag permuted within season
    rng2 = np.random.default_rng(SEED + 1)
    null_a, null_b = np.empty(N_PERM), np.empty(N_PERM)
    for i in range(N_PERM):
        p = df.copy()
        p["above_own_prior"] = rng2.permutation(p.above_own_prior.to_numpy())
        null_a[i] = top_k_stats(p, a, k)["career_year_share"]
        null_b[i] = top_k_stats(p, b, k)["career_year_share"]
    return {
        "a": a,
        "b": b,
        "k": k,
        "n": int(n),
        "stats_a": sa,
        "stats_b": sb,
        "delta_mean_realised_b_minus_a": sb["mean_realised"] - sa["mean_realised"],
        "delta_mean_realised_ci95": [
            float(np.percentile(d_mean, 2.5)),
            float(np.percentile(d_mean, 97.5)),
        ],
        "delta_overpaid_b_minus_a": sb["overpaid"] - sa["overpaid"],
        "delta_overpaid_ci95": [
            float(np.percentile(d_over, 2.5)),
            float(np.percentile(d_over, 97.5)),
        ],
        "career_share_null_a": [
            float(np.nanpercentile(null_a, 2.5)),
            float(np.nanpercentile(null_a, 97.5)),
        ],
        "career_share_null_b": [
            float(np.nanpercentile(null_b, 2.5)),
            float(np.nanpercentile(null_b, 97.5)),
        ],
    }


def pooled_contrast(rows: pd.DataFrame, a: str, b: str, k: int) -> dict:
    """Seasons as the unit: the mean over seasons of each per-season delta, with
    a bootstrap that resamples rows within every season jointly."""
    seasons = [int(s) for s in sorted(rows.season.unique())]
    per = {s: season_contrast(rows[rows.season == s], a, b, k) for s in seasons}
    rng = np.random.default_rng(SEED + 2)
    draws = np.empty(N_BOOT)
    by = {s: rows[rows.season == s].reset_index(drop=True) for s in seasons}
    for i in range(N_BOOT):
        acc = 0.0
        for s in seasons:
            d = by[s]
            r = d.iloc[rng.integers(0, len(d), len(d))]
            acc += (
                top_k_stats(r, b, k)["mean_realised"]
                - top_k_stats(r, a, k)["mean_realised"]
            )
        draws[i] = acc / len(seasons)
    wins = sum(per[s]["delta_mean_realised_b_minus_a"] > 0 for s in seasons)
    pooled_delta = float(
        np.mean([per[s]["delta_mean_realised_b_minus_a"] for s in seasons])
    )
    ci = [float(np.percentile(draws, 2.5)), float(np.percentile(draws, 97.5))]
    share_a = float(
        np.nanmean([per[s]["stats_a"]["career_year_share"] for s in seasons])
    )
    share_b = float(
        np.nanmean([per[s]["stats_b"]["career_year_share"] for s in seasons])
    )
    return {
        "a": a,
        "b": b,
        "k": k,
        "seasons": seasons,
        "per_season": per,
        "seasons_b_beats_a_on_mean_realised": int(wins),
        "pooled_delta_mean_realised_b_minus_a": pooled_delta,
        "pooled_ci95": ci,
        "pooled_career_year_share_a": share_a,
        "pooled_career_year_share_b": share_b,
        "pooled_overpaid_a": int(sum(per[s]["stats_a"]["overpaid"] for s in seasons)),
        "pooled_overpaid_b": int(sum(per[s]["stats_b"]["overpaid"] for s in seasons)),
    }


def verdict(primary: dict) -> str:
    wins_ok = primary["seasons_b_beats_a_on_mean_realised"] >= 4
    ci_ok = primary["pooled_ci95"][0] > 0
    share_ok = (
        primary["pooled_career_year_share_a"] > primary["pooled_career_year_share_b"]
    )
    if wins_ok and ci_ok and share_ok:
        return "PASS: combined top-10 realises more, in >=4/6 seasons, CI excludes zero, and carries fewer career-year players"  # noqa: E501
    if wins_ok and ci_ok:
        return (
            "PARTIAL: payoff separates; career-year share does not order as predicted"
        )
    return "NOT SEPARABLE at this n: the ranking read does not separate; report the MAE decomposition only"  # noqa: E501


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--rows", type=Path, default=_DEFAULT_ROWS)
    ap.add_argument("--out-dir", type=Path, default=_DEFAULT_OUT)
    args = ap.parse_args(argv)
    args.out_dir.mkdir(parents=True, exist_ok=True)

    rows = pd.read_parquet(args.rows)
    for col in ("above_own_prior", "per_league", "rtm_plus_league", "one_global", "y"):
        assert col in rows, (
            f"{col} missing from {args.rows}; regenerate with --rows-out"
        )
    rows = rows[np.isfinite(rows.rtm_plus_league)].reset_index(drop=True)
    n_defined = int(rows.above_own_prior.notna().sum())

    results = {}
    for k in KS:
        results[f"k{k}"] = {
            "primary": pooled_contrast(rows, *PRIMARY, k),
            "placebo": pooled_contrast(rows, *PLACEBO, k),
        }
        p = results[f"k{k}"]["primary"]
        print(
            f"[B] k={k}: combined - multiplier mean realised {p['pooled_delta_mean_realised_b_minus_a']:+.3f} "  # noqa: E501
            f"CI [{p['pooled_ci95'][0]:+.3f}, {p['pooled_ci95'][1]:+.3f}], "
            f"seasons won {p['seasons_b_beats_a_on_mean_realised']}/6, "
            f"career-year share multiplier {p['pooled_career_year_share_a']:.2f} vs combined "  # noqa: E501
            f"{p['pooled_career_year_share_b']:.2f}, overpaid {p['pooled_overpaid_a']} vs {p['pooled_overpaid_b']}"  # noqa: E501
        )
    payload = {
        "study": "B_shortlist_ranks",
        "preregistration": "translation-application-studies-preregistration-2026-09-06.md",  # noqa: E501
        "rows_source": str(args.rows.relative_to(REPO))
        if args.rows.is_relative_to(REPO)
        else str(args.rows),
        "n_rows": int(len(rows)),
        "n_rows_with_prior_flag": n_defined,
        "results": results,
        "verdict": verdict(results["k10"]["primary"]),
    }
    (args.out_dir / "shortlist_ranks.json").write_text(
        json.dumps(payload, indent=1, default=float)
    )
    print(f"[verdict] {payload['verdict']}")
    print(f"[done] wrote shortlist_ranks.json to {args.out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
