# ruff: noqa: E402, E501  -- the rendered result note carries long Markdown lines by design
"""v2 of the transfer forecast: player-level inputs and per-player intervals.

ATI-3074. Pre-registered in
``docs/research/translation-v2-player-features-preregistration-2026-09-14.md``
(proposed ``00aff73e4``, accepted ``6e7cbecef``, both before this file existed).
Comparator only: nothing here touches the locked 2026-27 set, its interval or
any of its gates, and no 2026-27 prediction is written.

What it does, in the pre-registration's order:

1. Rebuild the walk-forward folds exactly as
   ``scripts/validate_translation_walkforward.py`` does, and STOP unless the
   five shipped arm MAEs reproduce ``walkforward_summary.json`` to 1e-6.
2. Attach the declared covariates. Identity: the destination row's league
   ``Player_ID`` (the API box score carries it; the shipped corpus loader drops
   it, so it is re-read here) joined to the first-party ``player_bio.parquet``;
   a name fallback restricted to bio rows whose competitions and seasons
   include the destination; a key that matches two people is refused and that
   row falls back to v1.
3. Apply the source-club-strength availability gate (>= 90% of rows) on the
   covariate table BEFORE any fit.
4. Fit, per fold on seasons strictly before S: ``v2`` (the combined arm's OLS
   design plus the covariates) and ``v2_ridge`` (same design, penalty chosen by
   leave-one-season-out inside the training seasons). T1: the same code with
   the covariate block removed must reproduce the combined arm to 1e-6.
5. Intervals, rolling like Amendment 8: ``v2_mondrian`` (split conformal per
   history x minutes-per-game-tercile cell), ``v2_pooled``, and v1's
   registered construction (conformal on the per-league arm), which must
   reproduce ``intervals_summary.json`` before it is used as the bar.
6. Verdicts exactly as registered; write ``v2_summary.json``, the per-fold
   coefficient table and the result note.

Usage::

    uv run python scripts/validate_translation_v2.py
"""

from __future__ import annotations

# Input identity must be checked before scientific imports or output creation.
if __name__ == "__main__":
    import sys as _research_sys
    from pathlib import Path as _ResearchPath

    _research_sys.path.insert(0, str(_ResearchPath(__file__).resolve().parents[1]))
    from src.research.execution import enter as _enter_research

    _enter_research(__file__)


import argparse
import contextlib
import datetime
import glob
import io
import json
import math
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

import scripts.calibrate_prediction_intervals as cpi  # noqa: E402
import scripts.validate_translation_holdout as vh  # noqa: E402
import scripts.validate_translation_walkforward as wf  # noqa: E402
from src.data.corpus.euroleague_api import (  # noqa: E402
    drop_non_player_rows,
    pairing_key,
)
from src.utils.player_ids import person_code  # noqa: E402

PREREG = "docs/research/translation-v2-player-features-preregistration-2026-09-14.md"
PREREG_ACCEPTED = "6e7cbecef"
SELECTION_FOLDS = (2020, 2021, 2022, 2023, 2024)
CONFIRMATION_FOLD = 2025
INTERVAL_SELECTION_FOLDS = cpi.SELECTION_FOLDS  # 2022-2024, Amendment 8
ALPHA = cpi.ALPHA
BAND = cpi.COVERAGE_BAND  # (0.90, 0.98)
GROUP_BAND = (0.85, 0.99)
MIN_CELL = 30
CLUB_STRENGTH_GATE = 0.90
FALLBACK_FLAG = 0.20
MAE_TOL = 1e-6
T1_TOL = 1e-6
N_BOOT = 4000
SEED = 0
RIDGE_GRID = tuple(float(x) for x in np.logspace(-3, 3, 25))
AGE_CENTRE = 27.0
COMP_CODE = {"euroleague": "E", "eurocup": "U"}
POSITIONS = ("Guard", "Forward", "Center")

BIO_PATH = REPO / "data" / "processed" / "player_bio.parquet"
WF_SUMMARY = REPO / "data" / "processed" / "translation" / "walkforward_summary.json"
INTERVALS_SUMMARY = cpi.DEFAULT_SUMMARY
OUT_DIR = REPO / "docs" / "research" / "artifacts" / "translation-v2-2026-09"
NOTE = (
    REPO / "docs" / "research" / "translation-v2-player-features-result-2026-09-14.md"
)

#: The covariate block added to the combined arm's design, in column order.
BASE_COVARIATES = (
    "age_c",
    "age_c2",
    "height_c",
    "pos_forward",
    "pos_center",
    "mpg_src",
    "usage_src",
    "hist_1",
    "hist_2plus",
    "trajectory",
    "lag",
)
CLUB_COVARIATE = "club_diff_src"


# ------------------------------------------------------------------ identity --
def api_person_map(raw: pd.DataFrame) -> tuple[dict, set]:
    """(pairing_key, season, league, team) -> person code, from API box scores.

    ``raw`` carries ``Player``, ``Player_ID``, ``Team``, ``Season`` and a
    ``league`` column. A key that maps to two different person codes is a
    collision: it is returned in the second value and absent from the map, so
    no row can be given the wrong person.
    """
    df = raw[["Player", "Player_ID", "Team", "Season", "league"]].copy()
    df["key"] = df.Player.map(pairing_key)
    df["code"] = df.Player_ID.astype(str).map(person_code)
    df = df[df.key.notna()].drop_duplicates(["key", "Season", "league", "Team", "code"])
    grp = df.groupby(["key", "Season", "league", "Team"]).code.nunique()
    collisions = set(grp[grp > 1].index)
    ok = df.set_index(["key", "Season", "league", "Team"])
    mapping = {k: v for k, v in ok.code.items() if k not in collisions}
    return mapping, collisions


def name_fallback_map(bio: pd.DataFrame) -> dict:
    """(pairing_key, competition code, season) -> person code, or None on collision.

    Restricted to bio rows whose ``competitions`` and ``seasons_seen`` include
    the destination, as registered. ``None`` marks a key that matches two
    people: the caller refuses it.
    """
    out: dict = {}
    for r in bio.itertuples():
        key = pairing_key(r.player_name)
        if key is None:
            continue
        comps = str(r.competitions or "").split(",")
        seasons = [s for s in str(r.seasons_seen or "").split(",") if s.strip()]
        for c in comps:
            for s in seasons:
                k = (key, c.strip(), int(s))
                if k in out and out[k] != r.person_code:
                    out[k] = None
                else:
                    out.setdefault(k, r.person_code)
    return out


def attach_identity(
    rows: pd.DataFrame, person_map: dict, collisions: set, name_map: dict
) -> pd.DataFrame:
    """Person code per destination row, with how it was found."""
    codes, how = [], []
    for r in rows.itertuples():
        k = (r.player_name, int(r.season_dest), r.league_dest, r.club_dest)
        if k in person_map:
            codes.append(person_map[k])
            how.append("person_code")
            continue
        if k in collisions:
            codes.append(None)
            how.append("refused_collision")
            continue
        nk = (r.player_name, COMP_CODE.get(r.league_dest, ""), int(r.season_dest))
        if nk in name_map:
            code = name_map[nk]
            codes.append(code)
            how.append("name_fallback" if code is not None else "refused_collision")
        else:
            codes.append(None)
            how.append("unmatched")
    out = rows.copy()
    out["person_code"] = codes
    out["id_how"] = how
    return out


# ---------------------------------------------------------------- covariates --
def history_counts(agg_all: pd.DataFrame) -> dict:
    """player -> sorted seasons with minutes, any league."""
    h = agg_all[agg_all.minutes > 0][["player_name", "season"]].drop_duplicates()
    return h.groupby("player_name").season.apply(lambda s: sorted(s)).to_dict()


def club_strength(games_tables: pd.DataFrame) -> dict:
    """(league, season, team) -> point differential per game, domestic games."""
    g = games_tables.dropna(subset=["home_score", "away_score"])
    home = pd.DataFrame(
        {
            "league": g.league,
            "season": g.season,
            "team": g.home_team,
            "diff": g.home_score - g.away_score,
        }
    )
    away = pd.DataFrame(
        {
            "league": g.league,
            "season": g.season,
            "team": g.away_team,
            "diff": g.away_score - g.home_score,
        }
    )
    both = pd.concat([home, away], ignore_index=True)
    return both.groupby(["league", "season", "team"])["diff"].mean().to_dict()


def build_covariates(
    rows: pd.DataFrame, bio: pd.DataFrame, hist: dict, club: dict
) -> pd.DataFrame:
    """The registered covariates, known before the destination season.

    Bio fields are NaN when the row has no person code or the bio lacks them;
    such a row is on the v1 fallback. Height is centred within position later,
    on training rows only, so no scored row informs its own centring.
    """
    b = bio.set_index("person_code")
    out = rows.copy()
    birth = pd.to_datetime(out.person_code.map(b.birth_date.to_dict()), errors="coerce")
    ref = pd.to_datetime(out.season_dest.astype(int).astype(str) + "-10-01")
    age = (ref - birth).dt.days / 365.25
    out["age"] = age
    out["age_c"] = age - AGE_CENTRE
    out["age_c2"] = out.age_c**2
    out["height_cm"] = out.person_code.map(b.height_cm.to_dict())
    out["position"] = out.person_code.map(b.position.to_dict())
    out["pos_forward"] = (out.position == "Forward").astype(float)
    out["pos_center"] = (out.position == "Center").astype(float)
    out.loc[out.position.isna(), ["pos_forward", "pos_center"]] = np.nan
    out["mpg_src"] = out.minutes_src / out.games_src
    out["usage_src"] = out.usage_src.astype(float)
    n_hist = [
        sum(1 for s in hist.get(p, []) if s < int(ss))
        for p, ss in zip(out.player_name, out.season_src)
    ]
    out["n_hist"] = n_hist
    out["hist_1"] = (out.n_hist == 1).astype(float)
    out["hist_2plus"] = (out.n_hist >= 2).astype(float)
    prior = out.prior_mean_pir36.astype(float)
    out["trajectory"] = np.where(prior.notna(), out.pir_per36_src - prior, 0.0)
    out["lag"] = (out.season_dest.astype(int) - 1) - out.season_src.astype(int)
    out[CLUB_COVARIATE] = [
        club.get((lg, int(s), t), np.nan)
        for lg, s, t in zip(out.league_src, out.season_src, out.club_src)
    ]
    out["has_bio"] = out.age.notna() & out.height_cm.notna() & out.position.notna()
    return out


def club_gate(cov: pd.DataFrame) -> dict:
    share = float(cov[CLUB_COVARIATE].notna().mean())
    return {
        "share_available": share,
        "threshold": CLUB_STRENGTH_GATE,
        "included": bool(share >= CLUB_STRENGTH_GATE),
    }


# --------------------------------------------------------------------- fits --
def _centre_height(train: pd.DataFrame, df: pd.DataFrame) -> np.ndarray:
    means = train.groupby("position").height_cm.mean().to_dict()
    return df.height_cm.to_numpy(float) - df.position.map(means).to_numpy(float)


def _source_col(c: str) -> str:
    """The column a covariate is computed from (height is centred at fit time)."""
    return "height_cm" if c == "height_c" else c


def design(
    df: pd.DataFrame, league_col: np.ndarray, covariates: tuple, train: pd.DataFrame
) -> np.ndarray:
    """The combined arm's design (``wf._rtm_design``) plus the covariate block."""
    base = wf._rtm_design(df, league_col)
    if not covariates:
        return base
    cols = []
    for c in covariates:
        if c == "height_c":
            cols.append(_centre_height(train, df))
        else:
            cols.append(df[c].to_numpy(float))
    return np.column_stack([base, *cols])


def ols(X: np.ndarray, y: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    resid = y - X @ beta
    dof = max(len(y) - np.linalg.matrix_rank(X), 1)
    s2 = float(resid @ resid) / dof
    cov = s2 * np.linalg.pinv(X.T @ X)
    return beta, np.sqrt(np.clip(np.diag(cov), 0, None))


def ridge(X: np.ndarray, y: np.ndarray, lam: float) -> np.ndarray:
    """Ridge on standardised non-intercept columns; the intercept is free."""
    mu = X[:, 1:].mean(axis=0)
    sd = X[:, 1:].std(axis=0)
    sd[sd == 0] = 1.0
    Z = (X[:, 1:] - mu) / sd
    yc = y - y.mean()
    p = Z.shape[1]
    b = np.linalg.solve(Z.T @ Z + lam * np.eye(p), Z.T @ yc)
    coef = b / sd
    intercept = y.mean() - mu @ coef
    return np.concatenate([[intercept], coef])


def choose_lambda(train: pd.DataFrame, X: np.ndarray, y: np.ndarray) -> float:
    """Leave-one-season-out inside the training seasons only."""
    seasons = train.season_dest.to_numpy()
    best, best_mae = RIDGE_GRID[0], math.inf
    for lam in RIDGE_GRID:
        errs = []
        for s in np.unique(seasons):
            tr, te = seasons != s, seasons == s
            if tr.sum() < X.shape[1] + 2 or te.sum() == 0:
                continue
            beta = ridge(X[tr], y[tr], lam)
            errs.append(np.abs(X[te] @ beta - y[te]))
        if errs:
            m = float(np.concatenate(errs).mean())
            if m < best_mae:
                best, best_mae = lam, m
    return best


def fit_fold(fold: dict, covariates: tuple) -> dict:
    """v2 and v2_ridge for one fold; v1 fallback on rows without a bio.

    Fitted on rows strictly before the fold's season. ``train_rows`` and
    ``test_rows`` must carry the covariates (see :func:`build_covariates`).
    """
    train, test = fold["train_rows"], fold["test_rows"]
    season = fold["season"]
    assert (train.season_dest < season).all(), "a scored-season row entered a fit"
    mult_fn, k = fold["multiplier_fn"], fold["k_lag"]
    tr_league = train.pir_per36_src.to_numpy(float) * mult_fn(train) * k
    te_league = test.pir_per36_src.to_numpy(float) * mult_fn(test) * k

    # T1: the extended code path with the covariate block removed, fitted on
    # the same rows as the shipped combined arm, must reproduce it.
    X0 = design(train, tr_league, (), train)
    b0, _ = ols(X0, train.pir_per36_dest.to_numpy(float))
    t1_pred = design(test, te_league, (), train) @ b0

    ok_tr = train.has_bio.to_numpy(bool).copy()
    for c in covariates:
        ok_tr &= train[_source_col(c)].notna().to_numpy()
    tr = train[ok_tr]
    Xtr = design(tr, tr_league[ok_tr], covariates, tr)
    ytr = tr.pir_per36_dest.to_numpy(float)
    beta, se = ols(Xtr, ytr)
    lam = choose_lambda(tr, Xtr, ytr)
    beta_r = ridge(Xtr, ytr, lam)

    ok_te = test.has_bio.to_numpy(bool).copy()
    for c in covariates:
        ok_te &= test[_source_col(c)].notna().to_numpy()
    v1 = fold["rtm_arms"]["rtm_plus_league"]
    Xte = design(test, te_league, covariates, tr)
    v2 = np.where(ok_te, Xte @ beta, v1)
    v2_ridge = np.where(ok_te, Xte @ beta_r, v1)
    names = ["intercept", "src", "prior", "above_own_prior", "league_translated"]
    return {
        "t1_pred": t1_pred,
        "v2": v2,
        "v2_ridge": v2_ridge,
        "on_fallback": ~ok_te,
        "coef": pd.DataFrame(
            {
                "season": season,
                "term": names + list(covariates),
                "coef": beta,
                "se": se,
                "coef_ridge": beta_r,
            }
        ),
        "lambda": lam,
        "n_train_fit": int(ok_tr.sum()),
        "n_train_all": int(len(train)),
    }


# ----------------------------------------------------------------- intervals --
def history_group(df: pd.DataFrame) -> np.ndarray:
    return np.where(df.prior_mean_pir36.notna(), "2+", "1")


def mondrian_cells(cal: pd.DataFrame, test: pd.DataFrame) -> tuple:
    """Cell labels for calibration and test rows; small cells merge upward."""
    cuts = np.quantile(cal.mpg_src.to_numpy(float), [1 / 3, 2 / 3])

    def tercile(df):
        m = df.mpg_src.to_numpy(float)
        return np.where(m <= cuts[0], "low", np.where(m <= cuts[1], "mid", "high"))

    def label(df):
        return np.char.add(np.char.add(history_group(df).astype(str), "|"), tercile(df))

    cal_lab, test_lab = label(cal), label(test)
    counts = pd.Series(cal_lab).value_counts()
    small = {c for c, n in counts.items() if n < MIN_CELL}
    hist_cal, hist_test = history_group(cal), history_group(test)
    cal_lab = np.where(np.isin(cal_lab, list(small)), hist_cal, cal_lab)
    test_lab = np.where(
        np.isin(test_lab, list(small)) | ~np.isin(test_lab, list(counts.index)),
        hist_test,
        test_lab,
    )
    return cal_lab, test_lab, cuts, sorted(small)


def mondrian_interval(cal: pd.DataFrame, test: pd.DataFrame, point: str) -> dict:
    """Split conformal per cell. A merged cell is calibrated on every row of
    its history group, so a label never meets an empty calibration set."""
    cal_lab, test_lab, cuts, merged = mondrian_cells(cal, test)
    scores = np.abs(cal.y.to_numpy(float) - cal[point].to_numpy(float))
    cal_hist = history_group(cal)
    q = {}
    for c in np.unique(np.concatenate([cal_lab, test_lab])):
        mask = (cal_hist == c) if "|" not in c else (cal_lab == c)
        s = scores[mask]
        q[c] = cpi.conformal_quantile(s, ALPHA) if s.size else math.inf
    half = np.array([q[c] for c in test_lab])
    yhat = test[point].to_numpy(float)
    return {
        "lo": yhat - half,
        "hi": yhat + half,
        "cell": test_lab,
        "q": {k: float(v) for k, v in q.items()},
        "cuts": [float(x) for x in cuts],
        "merged": merged,
        "n_cal": {str(k): int(v) for k, v in pd.Series(cal_lab).value_counts().items()},
    }


def pooled_interval(cal: pd.DataFrame, test: pd.DataFrame, point: str) -> dict:
    q = cpi.conformal_quantile(
        np.abs(cal.y.to_numpy(float) - cal[point].to_numpy(float)), ALPHA
    )
    yhat = test[point].to_numpy(float)
    return {"lo": yhat - q, "hi": yhat + q, "q": float(q)}


def rolling_intervals(rows: pd.DataFrame, folds) -> pd.DataFrame:
    """Each fold s calibrated on residuals of folds < s (Amendment 8)."""
    out = []
    for s in folds:
        cal, test = rows[rows.season < s], rows[rows.season == s]
        if cal.empty or test.empty:
            continue
        mon = mondrian_interval(cal, test, "v2")
        pool = pooled_interval(cal, test, "v2")
        v1 = pooled_interval(cal, test, "per_league")
        for arm, iv in (
            ("v2_mondrian", mon),
            ("v2_pooled", pool),
            ("v1_registered", v1),
        ):
            out.append(
                pd.DataFrame(
                    {
                        "arm": arm,
                        "fold": int(s),
                        "cluster": test.cluster.to_numpy(),
                        "cell": mon["cell"],
                        "history": history_group(test),
                        "y": test.y.to_numpy(float),
                        "lo": iv["lo"],
                        "hi": iv["hi"],
                    }
                )
            )
    return pd.concat(out, ignore_index=True)


def interval_metrics(per_row: pd.DataFrame) -> dict:
    """Pooled coverage, width and Winkler with cluster-bootstrap SE per arm."""
    pooled = per_row.rename(columns={"arm": "family"})
    return cpi.pooled(pooled[["family", "fold", "cluster", "y", "lo", "hi"]])


def paired_winkler(per_row: pd.DataFrame, a: str, b: str) -> dict:
    """Winkler(b) - Winkler(a) with a paired cluster bootstrap; + favours a."""
    ra = per_row[per_row.arm == a].reset_index(drop=True)
    rb = per_row[per_row.arm == b].reset_index(drop=True)
    wa = cpi.winkler(ra.y, ra.lo, ra.hi, ALPHA)
    wb = cpi.winkler(rb.y, rb.lo, rb.hi, ALPHA)
    cl = (ra.fold.astype(str) + "|" + ra.cluster.astype(str)).to_numpy()
    uniq = np.unique(cl)
    idx_by = {c: np.flatnonzero(cl == c) for c in uniq}
    rng = np.random.default_rng(SEED)
    draws = np.empty(N_BOOT)
    for i in range(N_BOOT):
        pick = rng.choice(uniq, uniq.size, replace=True)
        idx = np.concatenate([idx_by[c] for c in pick])
        draws[i] = wb[idx].mean() - wa[idx].mean()
    return {
        "delta": float(wb.mean() - wa.mean()),
        "ci": [float(np.percentile(draws, 2.5)), float(np.percentile(draws, 97.5))],
        "se": float(draws.std(ddof=1)),
    }


def group_table(per_row: pd.DataFrame, arm: str) -> list[dict]:
    g = per_row[per_row.arm == arm]
    out = []
    for key, col in (("cell", "cell"), ("history", "history")):
        for c, part in g.groupby(col):
            hit = (part.y >= part.lo) & (part.y <= part.hi)
            out.append(
                {
                    "by": key,
                    "group": str(c),
                    "n": int(len(part)),
                    "coverage": float(hit.mean()),
                    "mean_width": float((part.hi - part.lo).mean()),
                }
            )
    return out


# --------------------------------------------------------------------- run --
def reproduce_or_stop(frame: pd.DataFrame, summary: dict) -> dict:
    expected = {
        "per_league": summary["pooled"]["mae_per_league"],
        "one_global": summary["pooled"]["mae_one_global"],
        "b0": summary["pooled"]["mae_b0"],
        "rtm": summary["rtm_comparator"]["mae_rtm"],
        "rtm_plus_league": summary["rtm_comparator"]["mae_rtm_plus_league"],
    }
    if len(frame) != summary["n_pooled"]:
        raise SystemExit(
            f"walk-forward rows {len(frame)} != {summary['n_pooled']} in the summary"
        )
    got = {a: float(np.abs(frame[a] - frame.y).mean()) for a in expected}
    for a, v in expected.items():
        if abs(got[a] - v) >= MAE_TOL:
            raise SystemExit(
                f"{a} MAE {got[a]:.8f} does not reproduce the shipped {v:.8f}; "
                "the folds have drifted, stop"
            )
    return got


#: The registered labels cover a CI excluding zero either way and a positive
#: point with a CI spanning zero. A negative point with a CI spanning zero is
#: not one of them; it is printed as what it is rather than rounded into one.
NO_GAIN = "NO GAIN (point favours v1, CI spans zero; not a registered label)"


def point_verdict(delta: float, lo: float, hi: float, t1_ok: bool) -> str:
    if not t1_ok:
        return "FAIL"
    if lo > 0:
        return "PASS"
    if hi < 0:
        return "FAIL"
    return "PARTIAL" if delta > 0 else NO_GAIN


def interval_verdict(m: dict, paired: dict, groups: list[dict]) -> tuple[str, dict]:
    v2, v1 = m["v2_mondrian"], m["v1_registered"]
    beats = (v1["winkler"] - v2["winkler"]) > v1["winkler_se"]
    in_band = BAND[0] <= v2["coverage"] <= BAND[1]
    cells = [g for g in groups if g["by"] == "cell"]
    groups_ok = all(GROUP_BAND[0] <= g["coverage"] <= GROUP_BAND[1] for g in cells)
    checks = {
        "winkler_gain": float(v1["winkler"] - v2["winkler"]),
        "one_se_of_v1": float(v1["winkler_se"]),
        "beats_by_more_than_one_se": bool(beats),
        "pooled_coverage_in_band": bool(in_band),
        "every_cell_in_group_band": bool(groups_ok),
        "paired_winkler": paired,
    }
    return ("PASS" if beats and in_band and groups_ok else "FAIL"), checks


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--out-dir", type=Path, default=OUT_DIR)
    ap.add_argument("--note", type=Path, default=NOTE)
    args = ap.parse_args(argv)
    args.out_dir.mkdir(parents=True, exist_ok=True)

    # ---- 1. folds, reproduced -------------------------------------------------
    with contextlib.redirect_stdout(io.StringIO()):
        games, pairs = vh.load_corpus("api")
        switch, agg_all = vh.build_switchers(games)
    cohorts = switch[switch.was_cont == 0]
    cohorts = cohorts[~cohorts.league_src.isin(vh.EXCLUDED_SOURCE)]
    cohorts = cohorts[cohorts.pir_per36_src > 0].copy()
    fits = [wf.one_season(pairs, cohorts, s) for s in wf.SEASONS]
    for f in fits:
        f["rtm_arms"] = wf._fit_rtm_arms(f)
    frame = pd.concat([wf.fold_rows(f) for f in fits], ignore_index=True)
    got = reproduce_or_stop(frame, json.loads(WF_SUMMARY.read_text()))
    print(f"[reproduce] five shipped arm MAEs match to {MAE_TOL}: {got}")

    # ---- 2. identity and covariates ---------------------------------------------
    raw = []
    for comp in ("euroleague", "eurocup"):
        for p in sorted(
            glob.glob(str(REPO / "data" / "raw" / comp / "*" / "boxscores"))
        ):
            d = pd.read_parquet(p)
            d["league"] = comp
            raw.append(d)
    raw = drop_non_player_rows(pd.concat(raw, ignore_index=True))
    person_map, collisions = api_person_map(raw)
    bio = pd.read_parquet(BIO_PATH)
    name_map = name_fallback_map(bio)
    hist = history_counts(agg_all)
    gpaths = sorted(
        glob.glob(
            str(REPO / "data" / "raw" / "proballers" / "*" / "*" / "games_*.parquet")
        )
        + glob.glob(
            str(
                REPO
                / "data"
                / "raw"
                / "_inactive_leagues"
                / "proballers"
                / "*"
                / "*"
                / "games_*.parquet"
            )
        )
    )
    gtab = pd.concat([pd.read_parquet(p) for p in gpaths], ignore_index=True)
    gtab = gtab.drop_duplicates(["game_id", "league"])
    club = club_strength(gtab)

    all_rows = pd.concat([f["test_rows"] for f in fits] + [cohorts], ignore_index=False)
    all_rows = all_rows[~all_rows.index.duplicated()]
    ident = attach_identity(all_rows, person_map, collisions, name_map)
    cov = build_covariates(ident, bio, hist, club)
    scored_idx = pd.concat([f["test_rows"] for f in fits]).index
    scored = cov.loc[scored_idx]
    id_counts = scored.id_how.value_counts().to_dict()
    print(f"[identity] scored rows: {id_counts}; bio found {scored.has_bio.mean():.3f}")

    # ---- 3. source-club-strength gate, before any fit ---------------------------
    gate = club_gate(scored)
    print(
        f"[gate] source-club strength available on {gate['share_available']:.3f} "
        f"of scored rows; threshold {CLUB_STRENGTH_GATE}; "
        f"{'INCLUDED' if gate['included'] else 'DROPPED'}"
    )
    covariates = BASE_COVARIATES + ((CLUB_COVARIATE,) if gate["included"] else ())
    lag_values = sorted(scored.lag.dropna().unique().tolist())
    print(f"[lag] source-season lag values on walk-forward rows: {lag_values}")

    # ---- 4. fits ------------------------------------------------------------------
    coef_tables, per_fold = [], []
    for f in fits:
        f["train_rows"] = cov.loc[f["train_rows"].index]
        f["test_rows"] = cov.loc[f["test_rows"].index]
        r = fit_fold(f, covariates)
        f["v2_fit"] = r
        coef_tables.append(r["coef"])
        per_fold.append(
            {
                "season": f["season"],
                "n": f["n"],
                "fallback_share": float(r["on_fallback"].mean()),
                "fallback_flag": bool(r["on_fallback"].mean() > FALLBACK_FLAG),
                "lambda": r["lambda"],
                "n_train_fit": r["n_train_fit"],
                "n_train_all": r["n_train_all"],
            }
        )
    t1_gap = max(
        float(np.max(np.abs(f["v2_fit"]["t1_pred"] - f["rtm_arms"]["rtm_plus_league"])))
        for f in fits
    )
    t1_ok = t1_gap < T1_TOL
    print(
        f"[T1] covariate block removed vs combined arm: max gap {t1_gap:.2e} ok={t1_ok}"
    )
    if not t1_ok:
        print("[T1] FAILED: the extended design does not reproduce the combined arm")

    frame["v2"] = np.concatenate([f["v2_fit"]["v2"] for f in fits])
    frame["v2_ridge"] = np.concatenate([f["v2_fit"]["v2_ridge"] for f in fits])
    frame["on_fallback"] = np.concatenate([f["v2_fit"]["on_fallback"] for f in fits])
    frame["mpg_src"] = np.concatenate(
        [f["test_rows"].mpg_src.to_numpy(float) for f in fits]
    )
    frame["cluster_full"] = frame.season.astype(str) + "|" + frame.cluster.astype(str)

    # ---- point contrasts -------------------------------------------------------
    def block(mask: np.ndarray) -> dict:
        s = frame[mask]
        y, cl = s.y.to_numpy(), s.cluster_full.to_numpy()

        def contrast(a, b):
            d, lo, hi = wf.paired_cluster_bootstrap(
                s[a].to_numpy(), s[b].to_numpy(), y, cl
            )
            return {"delta": d, "ci": [lo, hi]}

        arms = (
            "v2",
            "v2_ridge",
            "rtm_plus_league",
            "per_league",
            "one_global",
            "b0",
            "rtm",
        )
        return {
            "n": int(len(s)),
            "metrics": {a: vh.metrics(y, s[a].to_numpy()) for a in arms},
            "v2_vs_combined": contrast("v2", "rtm_plus_league"),
            "v2_ridge_vs_v2": contrast("v2_ridge", "v2"),
            "v2_vs_one_global": contrast("v2", "one_global"),
            "v2_vs_b0": contrast("v2", "b0"),
            "fallback_share": float(s.on_fallback.mean()),
        }

    sel = frame.season.isin(SELECTION_FOLDS).to_numpy()
    conf = (frame.season == CONFIRMATION_FOLD).to_numpy()
    selection = block(sel)
    confirmation = block(conf)
    c = selection["v2_vs_combined"]
    verdict_point = point_verdict(c["delta"], c["ci"][0], c["ci"][1], t1_ok)
    print(
        f"[point] selection folds n={selection['n']}: MAE combined "
        f"{selection['metrics']['rtm_plus_league']['mae']:.4f} v2 "
        f"{selection['metrics']['v2']['mae']:.4f} delta {c['delta']:+.4f} "
        f"CI [{c['ci'][0]:+.4f}, {c['ci'][1]:+.4f}] -> {verdict_point}"
    )

    games_dest_mean = float(
        np.concatenate(
            [
                f["test_rows"].games_dest.to_numpy()
                for f in fits
                if f["season"] in SELECTION_FOLDS
            ]
        ).mean()
    )
    ceiling = wf.r2_ceiling(games, games_dest_mean)

    # ---- 5. intervals ------------------------------------------------------------
    iv_rows = frame.copy()
    per_row = rolling_intervals(iv_rows, INTERVAL_SELECTION_FOLDS)
    iv_metrics = interval_metrics(per_row)
    reg = json.loads(INTERVALS_SUMMARY.read_text())
    reg_conf = reg["pooled_selection_folds"]["conformal"]
    if abs(iv_metrics["v1_registered"]["winkler"] - reg_conf["winkler"]) >= 1e-6 or (
        iv_metrics["v1_registered"]["n"] != reg_conf["n"]
    ):
        raise SystemExit(
            "v1's registered interval does not reproduce intervals_summary.json: "
            f"{iv_metrics['v1_registered']['winkler']} vs {reg_conf['winkler']}"
        )
    groups = group_table(per_row, "v2_mondrian")
    groups_v1 = group_table(per_row, "v1_registered")
    paired = paired_winkler(per_row, "v2_mondrian", "v1_registered")
    verdict_interval, iv_checks = interval_verdict(iv_metrics, paired, groups)
    print(
        f"[interval] Winkler v1 {iv_metrics['v1_registered']['winkler']:.3f} "
        f"(SE {iv_metrics['v1_registered']['winkler_se']:.3f}) mondrian "
        f"{iv_metrics['v2_mondrian']['winkler']:.3f} pooled "
        f"{iv_metrics['v2_pooled']['winkler']:.3f}; coverage mondrian "
        f"{iv_metrics['v2_mondrian']['coverage']:.3f} -> {verdict_interval}"
    )
    conf_iv = rolling_intervals(iv_rows, (CONFIRMATION_FOLD,))
    conf_iv_metrics = interval_metrics(conf_iv)
    conf_groups = group_table(conf_iv, "v2_mondrian")

    coef = pd.concat(coef_tables, ignore_index=True)
    coef.to_csv(args.out_dir / "v2_coefficients.csv", index=False)
    head = subprocess.run(
        ["git", "-C", str(REPO), "rev-parse", "HEAD"], capture_output=True, text=True
    ).stdout.strip()
    summary = {
        "preregistration": PREREG,
        "preregistration_accepted_commit": PREREG_ACCEPTED,
        "repository_head_at_run": head,
        "run_date": datetime.date.today().isoformat(),
        "reproduced_shipped_maes": got,
        "identity": {
            "scored_rows_by_method": {str(k): int(v) for k, v in id_counts.items()},
            "bio_found_share": float(scored.has_bio.mean()),
            "api_key_collisions": int(len(collisions)),
        },
        "club_strength_gate": gate,
        "covariates": list(covariates),
        "lag_values_on_walkforward_rows": lag_values,
        "t1": {"max_gap": t1_gap, "ok": bool(t1_ok)},
        "per_fold": per_fold,
        "selection": selection,
        "confirmation_2025": confirmation,
        "point_verdict": verdict_point,
        "r2_ceiling": ceiling,
        "interval": {
            "selection_folds": list(INTERVAL_SELECTION_FOLDS),
            "pooled": iv_metrics,
            "groups_v2_mondrian": groups,
            "groups_v1_registered": groups_v1,
            "checks": iv_checks,
            "confirmation_2025": {
                "pooled": conf_iv_metrics,
                "groups_v2_mondrian": conf_groups,
            },
        },
        "interval_verdict": verdict_interval,
    }
    (args.out_dir / "v2_summary.json").write_text(
        json.dumps(summary, indent=1, default=float) + "\n"
    )
    args.note.write_text(render_note(summary, coef), encoding="utf-8")
    print(f"[done] wrote {args.out_dir / 'v2_summary.json'} and {args.note}")
    return 0


# -------------------------------------------------------------------- note --
def _f(x, d=3):
    return (
        "n/a" if x is None or (isinstance(x, float) and math.isnan(x)) else f"{x:.{d}f}"
    )


def _ci(c, d=3):
    return f"[{c[0]:+.{d}f}, {c[1]:+.{d}f}]"


def render_note(s: dict, coef: pd.DataFrame) -> str:
    sel, conf = s["selection"], s["confirmation_2025"]
    ceil = s["r2_ceiling"]["ceiling_r2_at_mean_games"]
    c = sel["v2_vs_combined"]
    iv = s["interval"]["pooled"]
    ck = s["interval"]["checks"]
    lines = [
        "# RESULT — v2 of the transfer forecast: player-level inputs and per-player intervals",
        "",
        f"**Date: {s['run_date']}. Ticket: ATI-3074.** Pre-registration "
        f"`{s['preregistration']}` (accepted `{s['preregistration_accepted_commit']}`), "
        f"run at repository state `{s['repository_head_at_run'][:9]}` by "
        "`scripts/validate_translation_v2.py`. Every number below is a field of "
        "`docs/research/artifacts/translation-v2-2026-09/v2_summary.json`.",
        "",
        f"**Point verdict: {s['point_verdict']}. Interval verdict: {s['interval_verdict']}.**",
        "",
        "## Specification",
        "",
        "| Choice | This study | Alternatives printed |",
        "|---|---|---|",
        "| **Unit** | one (player, destination season) walk-forward transfer; the five shipped arm MAEs reproduce `walkforward_summary.json` to 1e-6 | — |",
        f"| **Population** | selection folds 2020–2024 pooled (n = {sel['n']}); 2025 read once (n = {conf['n']}) | — |",
        "| **Estimator** | combined arm's OLS design plus "
        + ", ".join(f"`{x}`" for x in s["covariates"])
        + ", per fold on seasons < S | `v2_ridge` (LOSO penalty inside training seasons) |",
        "| **Null** | the combined arm (`rtm_plus_league`) on the same rows | one global multiplier, B0 |",
        "| **Filter** | rows without a first-party bio get v1's prediction; no imputation | — |",
        "| **Key** | league `Player_ID` → `player_bio.parquet`; name fallback restricted to destination competition and season; collisions refused | — |",
        "| **Uncertainty** | paired cluster bootstrap on destination club-season, 4,000 draws, seed 0 | — |",
        "",
        "## Point",
        "",
        "| arm | MAE | R² (ceiling) |",
        "|---|---:|---:|",
    ]
    for a in (
        "v2",
        "v2_ridge",
        "rtm_plus_league",
        "per_league",
        "rtm",
        "one_global",
        "b0",
    ):
        m = sel["metrics"][a]
        lines.append(f"| {a} | {_f(m['mae'])} | {_f(m['r2'])} ({_f(ceil, 2)}) |")
    lines += [
        "",
        f"MAE(combined) − MAE(v2) = **{c['delta']:+.3f} {_ci(c['ci'])}** on the "
        f"selection folds. Registered reading: PASS needs the CI to exclude zero; "
        f"the verdict is **{s['point_verdict']}**.",
        "",
        f"Secondary: v2_ridge vs v2 {sel['v2_ridge_vs_v2']['delta']:+.3f} "
        f"{_ci(sel['v2_ridge_vs_v2']['ci'])} (positive favours ridge); v2 vs one "
        f"global {sel['v2_vs_one_global']['delta']:+.3f} "
        f"{_ci(sel['v2_vs_one_global']['ci'])}; v2 vs B0 "
        f"{sel['v2_vs_b0']['delta']:+.3f} {_ci(sel['v2_vs_b0']['ci'])}.",
        "",
        f"**2025 confirmation (read once, not pooled):** n = {conf['n']}, "
        f"MAE(combined) − MAE(v2) = {conf['v2_vs_combined']['delta']:+.3f} "
        f"{_ci(conf['v2_vs_combined']['ci'])}.",
        "",
        "### Identity, fallback and the gate",
        "",
        f"- Scored rows by identity route: {s['identity']['scored_rows_by_method']}; "
        f"first-party bio found for {_f(s['identity']['bio_found_share'])} of scored rows.",
        f"- Source-club strength available on {_f(s['club_strength_gate']['share_available'])} "
        f"of scored rows against a 0.90 gate: "
        f"**{'included' if s['club_strength_gate']['included'] else 'dropped'}**, "
        "decided on the covariate table before any fit.",
        f"- Source-season lag takes the values {s['lag_values_on_walkforward_rows']} on the "
        "walk-forward rows: a transfer is built from the season just before, so the "
        "covariate is constant there, its coefficient cannot be estimated, and it moves "
        "no prediction. Recorded as a limitation, not dropped.",
        f"- T1 (covariate block removed reproduces the combined arm): max gap "
        f"{s['t1']['max_gap']:.1e}, {'ok' if s['t1']['ok'] else 'FAILED'}.",
        "",
        "| fold | n | on v1 fallback | flagged (>20%) | ridge λ | training rows fitted / all |",
        "|---:|---:|---:|---|---:|---:|",
    ]
    for p in s["per_fold"]:
        lines.append(
            f"| {p['season']} | {p['n']} | {_f(p['fallback_share'])} | "
            f"{'yes' if p['fallback_flag'] else 'no'} | {p['lambda']:.3g} | "
            f"{p['n_train_fit']} / {p['n_train_all']} |"
        )
    lines += [
        "",
        "### What the model learned (OLS coefficients, SE in brackets)",
        "",
    ]
    terms = [t for t in coef.term.unique()]
    seasons = sorted(coef.season.unique())
    lines.append("| term | " + " | ".join(str(x) for x in seasons) + " |")
    lines.append("|---|" + "---:|" * len(seasons))
    for t in terms:
        cells = []
        for se in seasons:
            r = coef[(coef.term == t) & (coef.season == se)]
            cells.append(
                f"{r.coef.iloc[0]:+.3f} ({r.se.iloc[0]:.3f})" if len(r) else ""
            )
        lines.append(f"| {t} | " + " | ".join(cells) + " |")
    lines += [
        "",
        "## Interval (selection folds 2022–2024, its own verdict)",
        "",
        "| arm | n | coverage | mean width | Winkler (SE) |",
        "|---|---:|---:|---:|---:|",
    ]
    for a in ("v1_registered", "v2_pooled", "v2_mondrian"):
        m = iv[a]
        lines.append(
            f"| {a} | {m['n']} | {_f(m['coverage'])} | {_f(m['mean_width'], 2)} | "
            f"{_f(m['winkler'], 2)} ({_f(m['winkler_se'], 2)}) |"
        )
    lines += [
        "",
        f"`v1_registered` reproduces `intervals_summary.json`'s conformal row. Mondrian gain "
        f"over v1: {ck['winkler_gain']:+.3f} against one SE of v1's Winkler "
        f"({ck['one_se_of_v1']:.3f}); paired Winkler(v1) − Winkler(mondrian) "
        f"{ck['paired_winkler']['delta']:+.3f} {_ci(ck['paired_winkler']['ci'])}. "
        f"Pooled coverage in [0.90, 0.98]: {ck['pooled_coverage_in_band']}. Every cell "
        f"in [0.85, 0.99]: {ck['every_cell_in_group_band']}. **Verdict: {s['interval_verdict']}.** "
        "The groups were chosen after a coverage table read on these rows "
        "(disclosed in the pre-registration), so this is weaker evidence than the point result.",
        "",
        "| group (Mondrian cell or history) | n | coverage | mean width |",
        "|---|---:|---:|---:|",
    ]
    for g in s["interval"]["groups_v2_mondrian"]:
        lines.append(
            f"| {g['by']}: {g['group']} | {g['n']} | {_f(g['coverage'])} | {_f(g['mean_width'], 2)} |"
        )
    cm = s["interval"]["confirmation_2025"]["pooled"]
    lines += [
        "",
        "**2025 confirmation (read once):** "
        + "; ".join(
            f"{a} coverage {_f(cm[a]['coverage'])}, width {_f(cm[a]['mean_width'], 2)}, "
            f"Winkler {_f(cm[a]['winkler'], 2)}"
            for a in ("v1_registered", "v2_pooled", "v2_mondrian")
        )
        + ".",
        "",
        "## What this licenses",
        "",
        "Per the pre-registration: a point PASS makes v2 the candidate basis for club reads "
        "and the 2027-28 lock under its own pre-registration; PARTIAL or FAIL is published "
        "beside the release and v1 is released alone. An interval PASS licenses per-player "
        "intervals on v2 artifacts only. Nothing here changes the locked 2026-27 set, and no "
        "2026-27 v2 prediction has been written.",
        "",
        "## Scripts",
        "",
        "- `scripts/validate_translation_v2.py` → `v2_summary.json`, `v2_coefficients.csv`, this note.",
        "- `tests/test_scripts/test_validate_translation_v2.py`.",
        "",
    ]
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())
