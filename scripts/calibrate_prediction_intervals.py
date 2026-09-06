"""Study C — prediction-interval families on rolling out-of-sample residuals.

Pre-registered in ``docs/research/prelock-program-preregistration-2026-09-04.md``
(ATI-2963). Reads the walk-forward's per-row file (``--rows-out``) and never
refits an arm: the point prediction under test is the ``per_league`` arm the
walk-forward already scores, and the question is only how wide an interval
around it should be, and of what shape.

    uv run python scripts/calibrate_prediction_intervals.py            # folds <= 2024
    uv run python scripts/calibrate_prediction_intervals.py --confirm-2025
    uv run python scripts/calibrate_prediction_intervals.py --lock-calibration
    uv run python scripts/calibrate_prediction_intervals.py --render

Families (all at alpha = 0.05):
  multiplier   [y_hat * 0.4986, y_hat * 1.6392] -- the committed interval (control)
  conformal    y_hat +- q_hat, q_hat the finite-sample (n+1) quantile of |y - y_hat|
  normalised   y_hat +- q_hat * sigma_hat(x), sigma_hat = exp(c0 + c1 y_hat + c2 log g)
  cqr          conformalised linear quantile regression on [y_hat, log g, reliable]

Rolling calibration: fold s is calibrated on the rows of folds < s only, so the
first evaluable fold is 2022 (two calibration folds behind it). Selection reads
folds 2022-2024; 2025 is the confirmation fold and is refused unless
``--confirm-2025`` is passed -- that flag exists so the commit that introduces
it can be dated after Amendment 8.

Metric: the Winkler interval score, a proper scoring rule for central
intervals -- width plus 2/alpha times the miss distance. Coverage alone cannot
separate families within +-0.02 at n ~ 440 (binomial SE ~ 0.011), which is
why the score, not coverage, selects.
"""

from __future__ import annotations

import argparse
import datetime
import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from src.data.translation_predictions import (  # noqa: E402
    INTERVAL_HIGH_MULT,
    INTERVAL_LOW_MULT,
)

ALPHA = 0.05
COVERAGE_BAND = (0.90, 0.98)
SELECTION_FOLDS = (2022, 2023, 2024)
CONFIRMATION_FOLD = 2025
FAMILIES = ("multiplier", "conformal", "normalised", "cqr")  # simplest first
POINT_ARM = "per_league"
N_BOOT = 2000
SEED = 0
RECENCY_HALF_LIFE = 1.0  # seasons; sensitivity only

ART_DIR = REPO_ROOT / "docs" / "research" / "artifacts" / "prelock-program-2026-09"
DEFAULT_ROWS = ART_DIR / "walkforward_rows.parquet"
DEFAULT_SUMMARY = ART_DIR / "intervals_summary.json"
DEFAULT_LOCK = ART_DIR / "interval_params_lock.json"
DEFAULT_NOTE = (
    REPO_ROOT / "docs" / "research" / "prediction-intervals-conformal-2026-09.md"
)


# ------------------------------------------------------------- primitives --
def conformal_quantile(scores: np.ndarray, alpha: float = ALPHA) -> float:
    """The split-conformal quantile with the finite-sample correction.

    ``ceil((n + 1)(1 - alpha)) / n`` of the empirical distribution; when that
    exceeds 1 (n too small) the interval is infinite, which is the honest
    answer rather than a silently under-covering one.
    """
    s = np.sort(np.asarray(scores, dtype=float))
    n = s.size
    if n == 0:
        return math.inf
    k = math.ceil((n + 1) * (1 - alpha))
    if k > n:
        return math.inf
    return float(s[k - 1])


def weighted_conformal_quantile(
    scores: np.ndarray, weights: np.ndarray, alpha: float = ALPHA
) -> float:
    """Recency-weighted variant (Tibshirani et al. 2019 form): the smallest s
    whose cumulative normalised weight reaches 1 - alpha, with a unit weight
    placed on +inf for the test point."""
    order = np.argsort(scores)
    s, w = np.asarray(scores, float)[order], np.asarray(weights, float)[order]
    total = w.sum() + w.max()  # the test point carries the largest weight seen
    cum = np.cumsum(w) / total
    idx = np.searchsorted(cum, 1 - alpha)
    return float(s[idx]) if idx < s.size else math.inf


def winkler(y: np.ndarray, lo: np.ndarray, hi: np.ndarray, alpha: float = ALPHA):
    """Winkler (1972) interval score per row. Lower is better; a hit costs the
    width, a miss costs the width plus 2/alpha times the distance."""
    y, lo, hi = (np.asarray(v, float) for v in (y, lo, hi))
    width = hi - lo
    below = np.clip(lo - y, 0, None)
    above = np.clip(y - hi, 0, None)
    return width + (2 / alpha) * (below + above)


def _design(df: pd.DataFrame) -> np.ndarray:
    g = np.log(np.clip(df.games_src.to_numpy(float), 1, None))
    return np.column_stack(
        [
            np.ones(len(df)),
            df[POINT_ARM].to_numpy(float),
            g,
            df.factor_reliable.to_numpy(float),
        ]
    )


# ---------------------------------------------------------------- families --
def fit_family(
    name: str, cal: pd.DataFrame, alpha: float = ALPHA, weights=None
) -> dict:
    """Fit one family on calibration rows; return the parameters needed to
    produce an interval for any row with the same columns."""
    y = cal.y.to_numpy(float)
    yhat = cal[POINT_ARM].to_numpy(float)
    if name == "multiplier":
        return {
            "family": name,
            "low_mult": INTERVAL_LOW_MULT,
            "high_mult": INTERVAL_HIGH_MULT,
        }
    if name == "conformal":
        scores = np.abs(y - yhat)
        q = (
            conformal_quantile(scores, alpha)
            if weights is None
            else weighted_conformal_quantile(scores, weights, alpha)
        )
        return {"family": name, "q_hat": q, "n_cal": int(len(cal))}
    if name == "normalised":
        X = _design(cal)[:, :3]  # intercept, y_hat, log games
        r = np.abs(y - yhat)
        # log|r| is undefined at r = 0; floor at 1e-3 PIR/36
        coef, *_ = np.linalg.lstsq(X, np.log(np.clip(r, 1e-3, None)), rcond=None)
        sigma = np.exp(X @ coef)
        scores = r / sigma
        q = (
            conformal_quantile(scores, alpha)
            if weights is None
            else weighted_conformal_quantile(scores, weights, alpha)
        )
        return {
            "family": name,
            "coef": [float(c) for c in coef],
            "q_hat": q,
            "n_cal": int(len(cal)),
        }
    if name == "cqr":
        from statsmodels.regression.quantile_regression import QuantReg

        X = _design(cal)
        lo_fit = QuantReg(y, X).fit(q=alpha / 2, max_iter=5000)
        hi_fit = QuantReg(y, X).fit(q=1 - alpha / 2, max_iter=5000)
        q_lo, q_hi = X @ lo_fit.params, X @ hi_fit.params
        scores = np.maximum(q_lo - y, y - q_hi)
        q = (
            conformal_quantile(scores, alpha)
            if weights is None
            else weighted_conformal_quantile(scores, weights, alpha)
        )
        return {
            "family": name,
            "beta_lo": [float(b) for b in lo_fit.params],
            "beta_hi": [float(b) for b in hi_fit.params],
            "q_hat": q,
            "n_cal": int(len(cal)),
        }
    raise ValueError(f"unknown family {name!r}")


def interval(params: dict, rows: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    """Apply fitted parameters to rows -> (lo, hi)."""
    yhat = rows[POINT_ARM].to_numpy(float)
    fam = params["family"]
    if fam == "multiplier":
        return yhat * params["low_mult"], yhat * params["high_mult"]
    if fam == "conformal":
        return yhat - params["q_hat"], yhat + params["q_hat"]
    if fam == "normalised":
        X = _design(rows)[:, :3]
        sigma = np.exp(X @ np.asarray(params["coef"]))
        return yhat - params["q_hat"] * sigma, yhat + params["q_hat"] * sigma
    if fam == "cqr":
        X = _design(rows)
        lo = X @ np.asarray(params["beta_lo"]) - params["q_hat"]
        hi = X @ np.asarray(params["beta_hi"]) + params["q_hat"]
        return lo, hi
    raise ValueError(fam)


def score_rows(y, lo, hi, alpha: float = ALPHA) -> dict:
    y, lo, hi = (np.asarray(v, float) for v in (y, lo, hi))
    hit = (y >= lo) & (y <= hi)
    return {
        "n": int(y.size),
        "coverage": float(hit.mean()) if y.size else float("nan"),
        "mean_width": float(np.mean(hi - lo)) if y.size else float("nan"),
        "winkler": float(np.mean(winkler(y, lo, hi, alpha)))
        if y.size
        else float("nan"),
    }


# ------------------------------------------------------------- the study --
def rolling(
    rows: pd.DataFrame, folds, families=FAMILIES, alpha=ALPHA, *, weighted=False
):
    """Calibrate each family on folds < s, score on fold s. Returns per-fold
    scored frames and a per-(family, fold) metrics table."""
    per_row = []
    metrics = []
    for s in folds:
        cal = rows[rows.season < s]
        test = rows[rows.season == s]
        if cal.empty or test.empty:
            continue
        w = None
        if weighted:
            w = 0.5 ** ((s - cal.season.to_numpy(float)) / RECENCY_HALF_LIFE)
        for fam in families:
            params = fit_family(fam, cal, alpha, weights=w)
            lo, hi = interval(params, test)
            m = score_rows(test.y, lo, hi, alpha)
            metrics.append({"family": fam, "fold": int(s), **m})
            per_row.append(
                pd.DataFrame(
                    {
                        "family": fam,
                        "fold": int(s),
                        "cluster": test.cluster.to_numpy(),
                        "y": test.y.to_numpy(float),
                        "lo": lo,
                        "hi": hi,
                    }
                )
            )
    return pd.concat(per_row, ignore_index=True), pd.DataFrame(metrics)


def pooled(per_row: pd.DataFrame, alpha=ALPHA, n_boot=N_BOOT, seed=SEED) -> dict:
    """Pooled coverage / width / Winkler per family with a cluster-bootstrap SE
    on the Winkler score (clusters = fold|club-season)."""
    out = {}
    rng = np.random.default_rng(seed)
    for fam, g in per_row.groupby("family"):
        m = score_rows(g.y, g.lo, g.hi, alpha)
        w = winkler(g.y.to_numpy(), g.lo.to_numpy(), g.hi.to_numpy(), alpha)
        cl = (g.fold.astype(str) + "|" + g.cluster.astype(str)).to_numpy()
        uniq = np.unique(cl)
        idx_by = {c: np.flatnonzero(cl == c) for c in uniq}
        draws = np.empty(n_boot)
        for i in range(n_boot):
            pick = rng.choice(uniq, uniq.size, replace=True)
            idx = np.concatenate([idx_by[c] for c in pick])
            draws[i] = w[idx].mean()
        m["winkler_se"] = float(draws.std(ddof=1))
        m["coverage_se_binomial"] = float(
            math.sqrt(m["coverage"] * (1 - m["coverage"]) / m["n"])
        )
        out[fam] = m
    return out


def select(pooled_metrics: dict, band=COVERAGE_BAND, families=FAMILIES) -> dict:
    """Lowest pooled Winkler among families inside the coverage band; ties
    within one SE of the best keep the simpler family (order of FAMILIES)."""
    eligible = [
        f for f in families if band[0] <= pooled_metrics[f]["coverage"] <= band[1]
    ]
    if not eligible:
        return {
            "selected": None,
            "eligible": [],
            "reason": "no family inside the coverage band",
        }
    best = min(eligible, key=lambda f: pooled_metrics[f]["winkler"])
    thresh = pooled_metrics[best]["winkler"] + pooled_metrics[best]["winkler_se"]
    for f in families:  # simplest first
        if f in eligible and pooled_metrics[f]["winkler"] <= thresh:
            return {
                "selected": f,
                "eligible": eligible,
                "best_by_score": best,
                "tie_threshold": thresh,
                "reason": "lowest Winkler inside the band"
                if f == best
                else f"within one SE of {best}; simpler family kept",
            }
    return {"selected": best, "eligible": eligible, "best_by_score": best}


def negative_controls(rows: pd.DataFrame, folds) -> dict:
    """Two gates that must FAIL (METHOD.md §8 corollary)."""
    # 1. alpha = 0.5 must land far below the band
    _, m_half = rolling(rows, folds, ("conformal",), alpha=0.5)
    cov_half = float(m_half.coverage.mean())
    # 2. leak signature: calibrated on the rows it is scored on
    leaked, honest = [], []
    for s in folds:
        test = rows[rows.season == s]
        cal = rows[rows.season < s]
        if test.empty or cal.empty:
            continue
        p_leak = fit_family("conformal", test)
        lo, hi = interval(p_leak, test)
        leaked.append(score_rows(test.y, lo, hi)["coverage"])
        p_hon = fit_family("conformal", cal)
        lo, hi = interval(p_hon, test)
        honest.append(score_rows(test.y, lo, hi)["coverage"])
    return {
        "alpha_0.5_coverage": cov_half,
        "alpha_0.5_fails_band": bool(cov_half < COVERAGE_BAND[0]),
        "leaked_calibration_coverage": float(np.mean(leaked)),
        "honest_calibration_coverage": float(np.mean(honest)),
        "leak_over_covers": bool(np.mean(leaked) >= np.mean(honest)),
    }


def run(rows: pd.DataFrame, *, confirm_2025: bool) -> dict:
    rows = rows.dropna(subset=[POINT_ARM, "y"]).copy()
    per_row, metrics = rolling(rows, SELECTION_FOLDS)
    pooled_sel = pooled(per_row)
    choice = select(pooled_sel)
    _, metrics_w = rolling(
        rows, SELECTION_FOLDS, ("conformal", "normalised"), weighted=True
    )
    controls = negative_controls(rows, SELECTION_FOLDS)
    if not (controls["alpha_0.5_fails_band"] and controls["leak_over_covers"]):
        raise AssertionError(f"negative controls did not fire: {controls}")
    summary = {
        "built_at": datetime.date.today().isoformat(),
        "alpha": ALPHA,
        "coverage_band": list(COVERAGE_BAND),
        "point_arm": POINT_ARM,
        "selection_folds": list(SELECTION_FOLDS),
        "n_rows_by_fold": {
            int(s): int((rows.season == s).sum()) for s in sorted(rows.season.unique())
        },
        "per_fold": metrics.to_dict("records"),
        "pooled_selection_folds": pooled_sel,
        "selection": choice,
        "recency_weighted_sensitivity": metrics_w.to_dict("records"),
        "negative_controls": controls,
        "multiplier_defect": {
            "note": "a multiplicative interval scales with the point; width at y_hat=1 vs 15",  # noqa: E501
            "width_at_1": float(INTERVAL_HIGH_MULT - INTERVAL_LOW_MULT),
            "width_at_15": float(15 * (INTERVAL_HIGH_MULT - INTERVAL_LOW_MULT)),
        },
    }
    if confirm_2025:
        per_row_c, metrics_c = rolling(rows, (CONFIRMATION_FOLD,))
        summary["confirmation_2025"] = {
            "per_family": metrics_c.to_dict("records"),
            "selected_family": choice["selected"],
            "selected_family_read": next(
                (
                    m
                    for m in metrics_c.to_dict("records")
                    if m["family"] == choice["selected"]
                ),
                None,
            ),
        }
    return summary


def lock_calibration(
    rows: pd.DataFrame, family: str, through: int = CONFIRMATION_FOLD
) -> dict:
    """Fit the selected family on every fold <= `through`.

    The 2026-27 lock uses every fold through 2025. The 2025 dress rehearsal
    must NOT: its interval is calibrated through 2024 so the rehearsal's
    coverage read is out of sample, exactly as the lock's will be.
    """
    cal = rows[rows.season <= through].dropna(subset=[POINT_ARM, "y"])
    params = fit_family(family, cal)
    params["calibration_folds"] = sorted(int(s) for s in cal.season.unique())
    params["alpha"] = ALPHA
    params["built_at"] = datetime.date.today().isoformat()
    return params


# ------------------------------------------------------------------ render --


def confirmation_reading(c: dict, band=COVERAGE_BAND) -> str:
    """The sentence under the 2025 table, read off the numbers: does the
    selected family hold its band and its edge over the multiplier control on
    the fold the selection never saw, and which family happened to score best
    there (reported; the selection was made on <= 2024 and does not move)."""
    r = c["selected_family_read"]
    by = {m["family"]: m for m in c["per_family"]}
    in_band = band[0] <= r["coverage"] <= band[1]
    control = by.get("multiplier")
    best = min(c["per_family"], key=lambda m: m["winkler"])
    parts = [
        f"Reading, from the table: on the 2025 fold the selected family's coverage {r['coverage']:.3f} "  # noqa: E501
        + ("sits inside" if in_band else "falls outside")
        + f" the [{band[0]:.2f}, {band[1]:.2f}] band"
    ]
    if control is not None:
        edge = control["winkler"] - r["winkler"]
        parts.append(
            f"its Winkler {'beats' if edge > 0 else 'does not beat'} the multiplier control by {edge:+.2f} "  # noqa: E501
            f"({r['winkler']:.2f} against {control['winkler']:.2f})"
        )
    parts.append(
        f"the lowest 2025 Winkler is {best['family']}'s ({best['winkler']:.2f})"
        + (
            "; the selection was made on folds <= 2024 and does not move on one fold's read"  # noqa: E501
            if best["family"] != r["family"]
            else ""
        )
    )
    return "; ".join(parts) + "."


def render(summary: dict) -> str:
    def f(x, d=3):
        return (
            "—"
            if x is None or (isinstance(x, float) and math.isnan(x))
            else f"{x:.{d}f}"
        )

    L = [
        "# Prediction intervals for the translation projections — four families on rolling out-of-sample residuals",  # noqa: E501
        "",
        f"**Generated {summary['built_at']} by `scripts/calibrate_prediction_intervals.py` from `walkforward_rows.parquet`; every number below is read from `intervals_summary.json`. Study C of `prelock-program-preregistration-2026-09-04.md` (ATI-2963).**",  # noqa: E501
        "",
        "## Specification",
        "",
        "| Choice | This study | Alternative considered |",
        "|---|---|---|",
        f"| **Unit** | one walk-forward test row (player × destination season), point arm `{summary['point_arm']}` | — |",  # noqa: E501
        f"| **Calibration** | rolling: fold s on rows of folds < s; selection folds {summary['selection_folds']} | pooled calibration (rejected — leaks the fold into its own interval) |",  # noqa: E501
        f"| **Selection** | lowest pooled Winkler score inside the coverage band {summary['coverage_band']}; ties within one cluster-bootstrap SE keep the simpler family | coverage alone (rejected — binomial SE ≈ 0.011 cannot separate families within ±0.02) |",  # noqa: E501
        "| **Null / controls** | α = 0.5 must fail the band; calibration on the scored rows must over-cover | — |",  # noqa: E501
        "",
        "## Pooled, selection folds",
        "",
        "| family | n | coverage (SE) | mean width | Winkler (SE) |",
        "|---|---:|---:|---:|---:|",
    ]
    for fam, m in summary["pooled_selection_folds"].items():
        L.append(
            f"| {fam} | {m['n']} | {f(m['coverage'])} ({f(m['coverage_se_binomial'])}) | {f(m['mean_width'], 2)} | {f(m['winkler'], 2)} ({f(m['winkler_se'], 2)}) |"  # noqa: E501
        )
    sel = summary["selection"]
    L += [
        "",
        f"**Selected: `{sel['selected']}`** — {sel.get('reason', '')}. Eligible (inside the band): {', '.join(sel['eligible']) or 'none'}.",  # noqa: E501
        "",
        "## Per fold",
        "",
        "| family | fold | n | coverage | mean width | Winkler |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for m in summary["per_fold"]:
        L.append(
            f"| {m['family']} | {m['fold']} | {m['n']} | {f(m['coverage'])} | {f(m['mean_width'], 2)} | {f(m['winkler'], 2)} |"  # noqa: E501
        )
    nc = summary["negative_controls"]
    L += [
        "",
        "## Invariants and negative controls",
        "",
        f"* α = 0.5 conformal coverage {f(nc['alpha_0.5_coverage'])} — fails the band: {nc['alpha_0.5_fails_band']}.",  # noqa: E501
        f"* Calibrating on the rows being scored covers {f(nc['leaked_calibration_coverage'])} vs {f(nc['honest_calibration_coverage'])} honest — the leak signature fires: {nc['leak_over_covers']}.",  # noqa: E501
        f"* The multiplier interval is {f(summary['multiplier_defect']['width_at_1'], 2)} wide at a projection of 1 and {f(summary['multiplier_defect']['width_at_15'], 2)} at 15: its width is a property of the point, not of the error.",  # noqa: E501
        "",
        "## Recency-weighted sensitivity (half-life one season)",
        "",
        "| family | fold | coverage | Winkler |",
        "|---|---:|---:|---:|",
    ]
    for m in summary["recency_weighted_sensitivity"]:
        L.append(
            f"| {m['family']} | {m['fold']} | {f(m['coverage'])} | {f(m['winkler'], 2)} |"  # noqa: E501
        )
    if "confirmation_2025" in summary:
        c = summary["confirmation_2025"]
        L += [
            "",
            "## Confirmation fold 2025 (read once, after Amendment 8)",
            "",
            "| family | n | coverage | mean width | Winkler |",
            "|---|---:|---:|---:|---:|",
        ]
        for m in c["per_family"]:
            L.append(
                f"| {m['family']} | {m['n']} | {f(m['coverage'])} | {f(m['mean_width'], 2)} | {f(m['winkler'], 2)} |"  # noqa: E501
            )
        r = c["selected_family_read"]
        if r:
            L.append("")
            L.append(
                f"Selected family `{c['selected_family']}` on 2025: coverage {f(r['coverage'])}, Winkler {f(r['winkler'], 2)}."  # noqa: E501
            )
            L.append("")
            L.append(confirmation_reading(c))
    else:
        L += [
            "",
            "## Confirmation fold 2025",
            "",
            "Not read. This artifact was produced before Amendment 8; the 2025 fold is scored once, afterwards, with `--confirm-2025`.",  # noqa: E501
        ]
    L += [
        "",
        "## What this licenses",
        "",
        f"The interval family the lock should carry is `{sel['selected']}`, chosen on folds the 2026-27 fit never sees by a proper scoring rule, with the committed multiplier interval as the control. It licenses no claim about the point predictions.",  # noqa: E501
        "",
        "## Scripts",
        "",
        "* `scripts/calibrate_prediction_intervals.py` — everything above; `--render` rewrites this note from the artifact.",  # noqa: E501
        "* `scripts/validate_translation_walkforward.py --rows-out` — the rows.",
    ]
    return "\n".join(L) + "\n"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--rows", type=Path, default=DEFAULT_ROWS)
    ap.add_argument("--summary", type=Path, default=DEFAULT_SUMMARY)
    ap.add_argument(
        "--confirm-2025",
        action="store_true",
        help="score the 2025 fold (after Amendment 8)",
    )
    ap.add_argument(
        "--lock-calibration",
        action="store_true",
        help="fit the selected family on folds <= 2025 and write interval_params_lock.json",  # noqa: E501
    )
    ap.add_argument("--lock-out", type=Path, default=DEFAULT_LOCK)
    ap.add_argument(
        "--calibrate-through",
        type=int,
        default=CONFIRMATION_FOLD,
        help="last fold the lock calibration reads (2024 for the 2025 rehearsal)",
    )
    ap.add_argument(
        "--render", action="store_true", help="rewrite the note from the summary"
    )
    ap.add_argument("--note", type=Path, default=DEFAULT_NOTE)
    args = ap.parse_args(argv)

    if args.render and not (args.confirm_2025 or args.lock_calibration):
        summary = json.loads(args.summary.read_text())
        args.note.write_text(render(summary))
        print(f"[render] wrote {args.note}")
        return 0

    rows = pd.read_parquet(args.rows)
    summary = run(rows, confirm_2025=args.confirm_2025)
    args.summary.parent.mkdir(parents=True, exist_ok=True)
    args.summary.write_text(json.dumps(summary, indent=1, default=float) + "\n")
    sel = summary["selection"]
    print(f"[select] {sel}")
    for fam, m in summary["pooled_selection_folds"].items():
        print(
            f"[pooled] {fam:11s} cov={m['coverage']:.3f} width={m['mean_width']:.2f} winkler={m['winkler']:.2f} ± {m['winkler_se']:.2f}"  # noqa: E501
        )
    if args.lock_calibration:
        if not sel["selected"]:
            raise SystemExit("no family selected; nothing to lock")
        params = lock_calibration(rows, sel["selected"], args.calibrate_through)
        args.lock_out.write_text(json.dumps(params, indent=1, default=float) + "\n")
        print(
            f"[lock] {sel['selected']} calibrated on folds {params['calibration_folds']} → {args.lock_out}"  # noqa: E501
        )
    if args.render:
        args.note.write_text(render(summary))
        print(f"[render] wrote {args.note}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
