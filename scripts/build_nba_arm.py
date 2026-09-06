#!/usr/bin/env python
"""The NBA arm (ATI-2958): EuroLeague <-> NBA moves, scored as pre-registered.

Reads ``docs/research/preregistration-nba-arm-2026-09-03.md`` as its spec and
implements it literally. Nothing here is fitted to the season it scores: every
arm is refit on moves whose destination season is strictly earlier.

Inputs (both first-party, both gitignored):
  EuroLeague  data/raw/euroleague/<season>/boxscores   (EFF from components)
  NBA         data/raw/nba/player_season_totals_*.parquet, player_info.parquet
  identity    data/processed/player_bio.parquet (EuroLeague /people birthdates)
  domestic    the shipped league_factors.parquet, for the P2 chain only

Arms, exactly as pre-registered:
  B0   untranslated source per-36 EFF
  B1b  source x one constant per direction, fitted on prior moves
  B1c  the player's own prior-season source-league rates (>=2 seasons), no level term
  M    direction constant x RTM-shrunk source rate (w fitted on prior moves)

Run::

    BA_REPO=<primary> uv run python scripts/build_nba_arm.py --out-dir OUT
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import unicodedata
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(os.environ.get("BA_REPO", Path(__file__).resolve().parents[1]))
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

MIN_GAMES = 8
MIN_PRIOR_MOVES = 10
N_BOOT = 4000
SEED = 0
EL_SEASONS = range(2016, 2026)
NBA_SEASONS = range(2015, 2026)
SCORE_SEASONS = range(2017, 2026)
W_GRID = np.round(np.arange(0.0, 1.0001, 0.05), 2)


# ------------------------------------------------------------------- names --
def norm_key(name: str) -> str:
    s = (
        unicodedata.normalize("NFKD", str(name))
        .encode("ascii", "ignore")
        .decode()
        .upper()
    )
    s = re.sub(r"[^\w\s-]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return re.sub(r"\b(JR\.?|SR\.?|II|III|IV|V)$", "", s).strip()


def api_name_to_first_last(last_first: str) -> str:
    if "," not in last_first:
        return last_first.strip()
    last, first = last_first.split(",", 1)
    return f"{first.strip()} {last.strip()}"


def _minutes(s: pd.Series) -> pd.Series:
    mm = s.str.extract(r"^(\d+):(\d+)$")
    return mm[0].astype(float) + mm[1].astype(float) / 60.0


# ------------------------------------------------------------------- loads --
def load_euroleague() -> pd.DataFrame:
    """One row per (player, season): games, minutes, EFF, main team, person_code."""
    frames = []
    for s in EL_SEASONS:
        p = REPO / "data" / "raw" / "euroleague" / str(s) / "boxscores"
        if not p.exists():
            continue
        d = pd.read_parquet(p)
        d = d[
            (d.Player != "Total")
            & (d.Minutes != "DNP")
            & d.Minutes.str.match(r"^\d+:\d+$", na=False)
        ]
        fgm = d.FieldGoalsMade2 + d.FieldGoalsMade3
        fga = d.FieldGoalsAttempted2 + d.FieldGoalsAttempted3
        d = d.assign(
            season=s,
            minutes=_minutes(d.Minutes),
            eff=(
                d.Points
                + d.TotalRebounds
                + d.Assistances
                + d.Steals
                + d.BlocksFavour
                - (fga - fgm)
                - (d.FreeThrowsAttempted - d.FreeThrowsMade)
                - d.Turnovers
            ),
            person_code=d.Player_ID.str.strip().str.lstrip("P").str.zfill(6),
            key=d.Player.map(lambda x: norm_key(api_name_to_first_last(x))),
        )
        frames.append(d)
    g = pd.concat(frames, ignore_index=True)
    agg = (
        g.groupby(["key", "season"])
        .agg(
            games=("Gamecode", "nunique"),
            minutes=("minutes", "sum"),
            eff=("eff", "sum"),
            person_code=("person_code", "first"),
        )
        .reset_index()
    )
    team = g.groupby(["key", "season", "Team"]).minutes.sum().reset_index()
    team = team.sort_values("minutes", ascending=False).drop_duplicates(
        ["key", "season"]
    )
    agg = agg.merge(team[["key", "season", "Team"]], on=["key", "season"]).rename(
        columns={"Team": "team"}
    )
    agg["league"] = "euroleague"
    return agg


def load_nba() -> pd.DataFrame:
    frames = []
    for s in NBA_SEASONS:
        p = REPO / "data" / "raw" / "nba" / f"player_season_totals_{s}.parquet"
        if not p.exists():
            continue
        frames.append(pd.read_parquet(p))
    d = pd.concat(frames, ignore_index=True)
    d["eff"] = (
        d.PTS
        + d.REB
        + d.AST
        + d.STL
        + d.BLK
        - (d.FGA - d.FGM)
        - (d.FTA - d.FTM)
        - d.TOV
    )
    d["key"] = d.PLAYER_NAME.map(norm_key)
    agg = (
        d.groupby(["PLAYER_ID", "season"])
        .agg(
            key=("key", "first"),
            games=("GP", "sum"),
            minutes=("MIN", "sum"),
            eff=("eff", "sum"),
        )
        .reset_index()
    )
    team = d.sort_values("MIN", ascending=False).drop_duplicates(
        ["PLAYER_ID", "season"]
    )[["PLAYER_ID", "season", "TEAM_ABBREVIATION"]]
    agg = agg.merge(team, on=["PLAYER_ID", "season"]).rename(
        columns={"TEAM_ABBREVIATION": "team"}
    )
    agg["league"] = "nba"
    return agg


def identity_map(el: pd.DataFrame, nba: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """key -> (person_code, PLAYER_ID) where name AND birth year agree, plus counts."""
    bio = pd.read_parquet(REPO / "data" / "processed" / "player_bio.parquet")[
        ["person_code", "birth_date"]
    ]
    bio = bio.dropna(subset=["birth_date"])
    bio["el_birth_year"] = bio.birth_date.astype(str).str[:4].astype(int)
    info = pd.read_parquet(REPO / "data" / "raw" / "nba" / "player_info.parquet")
    info["nba_birth_year"] = pd.to_numeric(info.BIRTHDATE.str[:4], errors="coerce")
    el_keys = (
        el[["key", "person_code"]]
        .drop_duplicates("key")
        .merge(bio, on="person_code", how="left")
    )
    nba_keys = (
        nba[["key", "PLAYER_ID"]]
        .drop_duplicates("key")
        .merge(info[["PLAYER_ID", "nba_birth_year"]], on="PLAYER_ID", how="left")
    )
    both = el_keys.merge(nba_keys, on="key")
    counts = {
        "name_overlap": int(len(both)),
        "el_birth_missing": int(both.el_birth_year.isna().sum()),
        "nba_birth_missing": int(both.nba_birth_year.isna().sum()),
    }
    ok = both.dropna(subset=["el_birth_year", "nba_birth_year"])
    counts["birth_year_disagree"] = int((ok.el_birth_year != ok.nba_birth_year).sum())
    ok = ok[ok.el_birth_year == ok.nba_birth_year]
    counts["identities_confirmed"] = int(len(ok))
    counts["R_ID_refused"] = counts["name_overlap"] - counts["identities_confirmed"]
    return ok[["key", "person_code", "PLAYER_ID", "el_birth_year"]], counts


# ------------------------------------------------------------------- moves --
def build_moves(el: pd.DataFrame, nba: pd.DataFrame, ids: pd.DataFrame) -> pd.DataFrame:
    el = el[el.key.isin(ids.key)].copy()
    nba = nba[nba.key.isin(ids.key)].copy()
    for d in (el, nba):
        d["per36"] = 36 * d.eff / d.minutes
    q_el = el[el.games >= MIN_GAMES]
    q_nba = nba[nba.games >= MIN_GAMES]
    rows = []
    # EL season t -> NBA season t+1
    a = q_el.merge(
        q_nba.assign(season=q_nba.season - 1),
        on=["key", "season"],
        suffixes=("_src", "_dst"),
    )
    for r in a.itertuples(index=False):
        rows.append(
            (
                "EL_to_NBA",
                r.key,
                r.season,
                r.season + 1,
                r.per36_src,
                r.per36_dst,
                r.minutes_src,
                r.minutes_dst,
                r.team_dst,
                r.games_src,
                r.games_dst,
            )
        )
    # NBA season t-1 -> EL season t
    b = q_nba.merge(
        q_el.assign(season=q_el.season - 1),
        on=["key", "season"],
        suffixes=("_src", "_dst"),
    )
    for r in b.itertuples(index=False):
        rows.append(
            (
                "NBA_to_EL",
                r.key,
                r.season,
                r.season + 1,
                r.per36_src,
                r.per36_dst,
                r.minutes_src,
                r.minutes_dst,
                r.team_dst,
                r.games_src,
                r.games_dst,
            )
        )
    mv = pd.DataFrame(
        rows,
        columns=[
            "direction",
            "key",
            "season_src",
            "season_dst",
            "src",
            "dst",
            "min_src",
            "min_dst",
            "team_dst",
            "games_src",
            "games_dst",
        ],
    )
    mv = mv[(mv.src > 0) & np.isfinite(mv.src) & np.isfinite(mv.dst)]
    # prior source-league history (seasons strictly before the source season),
    # for B1c and M
    hist = pd.concat(
        [
            el[["key", "season", "per36", "games", "league"]],
            nba[["key", "season", "per36", "games", "league"]],
        ]
    )
    hist = hist[hist.games >= MIN_GAMES]
    prior_mean, prior_n = [], []
    for r in mv.itertuples(index=False):
        lg = "euroleague" if r.direction == "EL_to_NBA" else "nba"
        h = hist[
            (hist.key == r.key) & (hist.league == lg) & (hist.season < r.season_src)
        ]
        prior_mean.append(float(h.per36.mean()) if len(h) else np.nan)
        prior_n.append(int(len(h)))
    mv["prior_mean"] = prior_mean
    mv["prior_n"] = prior_n
    mv["cluster"] = (
        mv.direction + "|" + mv.season_dst.astype(str) + "|" + mv.team_dst.astype(str)
    )
    return mv.reset_index(drop=True)


# ---------------------------------------------------------------- estimate --
def exposure_weighted(sub: pd.DataFrame) -> float:
    w = np.minimum(sub.min_src, sub.min_dst)
    return float(np.sum(w * sub.dst / sub.src) / np.sum(w))


def ratio_of_sums(sub: pd.DataFrame) -> float:
    return float(sub.dst.sum() / sub.src.sum())


def mean_of_ratios(sub: pd.DataFrame) -> float:
    return float((sub.dst / sub.src).mean())


def fit_w(prior: pd.DataFrame, k: dict) -> float:
    """RTM shrinkage weight on the source rate, chosen on prior moves by MAE."""
    p = prior.dropna(subset=["prior_mean"])
    if len(p) < MIN_PRIOR_MOVES:
        return 1.0
    kk = p.direction.map(k)
    best, best_mae = 1.0, np.inf
    for w in W_GRID:
        pred = kk * (w * p.src + (1 - w) * p.prior_mean)
        mae = float(np.abs(pred - p.dst).mean())
        if mae < best_mae:
            best, best_mae = float(w), mae
    return best


ESTIMATORS = {
    "exposure_weighted": exposure_weighted,
    "ratio_of_sums": ratio_of_sums,
    "mean_of_ratios": mean_of_ratios,
}


def walk_forward(
    mv: pd.DataFrame, estimator: str = "exposure_weighted"
) -> tuple[pd.DataFrame, dict]:
    est = ESTIMATORS[estimator]
    scored = []
    fits = {}
    for S in SCORE_SEASONS:
        prior = mv[mv.season_dst < S]
        cur = mv[mv.season_dst == S].copy()
        if cur.empty:
            continue
        k = {}
        for d, sub in prior.groupby("direction"):
            if len(sub) >= MIN_PRIOR_MOVES:
                k[d] = est(sub)
        cur = cur[cur.direction.isin(k)]
        if cur.empty:
            continue
        w = fit_w(prior[prior.direction.isin(k)], k)
        kk = cur.direction.map(k)
        cur["B0"] = cur.src
        cur["B1b"] = kk * cur.src
        has_hist = cur.prior_n >= 2
        cur["B1c"] = np.where(has_hist, cur.prior_mean, cur.B1b)
        cur["R_H"] = ~has_hist
        cur["M"] = np.where(
            has_hist, kk * (w * cur.src + (1 - w) * cur.prior_mean), cur.B1b
        )
        fits[S] = {
            "k": k,
            "w": w,
            "n_prior": int(len(prior)),
            "n_scored": int(len(cur)),
        }
        scored.append(cur)
    return pd.concat(scored, ignore_index=True), fits


def paired_boot(
    a: np.ndarray,
    b: np.ndarray,
    clusters: np.ndarray,
    n_boot: int = N_BOOT,
    seed: int = SEED,
):
    """a and b are absolute errors; bootstrap the cluster mean of a - b."""
    rng = np.random.default_rng(seed)
    diff = a - b
    cl = pd.Series(diff).groupby(clusters).agg(["sum", "count"])
    sums, counts = cl["sum"].to_numpy(), cl["count"].to_numpy()
    n = len(sums)
    draws = np.empty(n_boot)
    for i in range(n_boot):
        idx = rng.integers(0, n, n)
        draws[i] = sums[idx].sum() / counts[idx].sum()
    return (
        float(diff.mean()),
        float(np.percentile(draws, 2.5)),
        float(np.percentile(draws, 97.5)),
    )


def metrics(sc: pd.DataFrame, col: str) -> dict:
    e = sc[col] - sc.dst
    ss_res = float((e**2).sum())
    ss_tot = float(((sc.dst - sc.dst.mean()) ** 2).sum())
    return {
        "mae": float(e.abs().mean()),
        "rmse": float(np.sqrt((e**2).mean())),
        "r2": 1 - ss_res / ss_tot,
        "bias": float(e.mean()),
    }


def contrast(sc: pd.DataFrame, better: str, worse: str) -> dict:
    """MAE saved by `better` over `worse`; positive = better wins."""
    ea = (sc[worse] - sc.dst).abs().to_numpy()
    eb = (sc[better] - sc.dst).abs().to_numpy()
    d, lo, hi = paired_boot(ea, eb, sc.cluster.to_numpy())
    return {"delta_mae": d, "ci": [lo, hi], "excludes_zero": bool(lo > 0 or hi < 0)}


# --------------------------------------------------------------------- main --
def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument(
        "--out-dir",
        type=Path,
        default=REPO / "data" / "processed" / "translation" / "nba_arm",
    )
    args = ap.parse_args(argv)
    args.out_dir.mkdir(parents=True, exist_ok=True)

    el, nba = load_euroleague(), load_nba()
    print(
        f"[corpus] euroleague player-seasons {len(el):,} (2016-2025); "
        f"nba player-seasons {len(nba):,} (2015-2025)"
    )
    ids, idc = identity_map(el, nba)
    print(f"[identity] {json.dumps(idc)}")
    # T10 season-label check on a known mover
    vz = ids[ids.key == "SASHA VEZENKOV"]
    if len(vz):
        e = el[(el.key == "SASHA VEZENKOV")].season.tolist()
        n = nba[(nba.key == "SASHA VEZENKOV")].season.tolist()
        print(
            f"[T10] Vezenkov EL seasons {sorted(e)} | NBA seasons {sorted(n)} "
            "-> expect EL 2022, NBA 2023, EL 2024"
        )
        assert 2023 in n and 2022 in e and 2024 in e, (
            "season-label convention differs between sources"
        )

    mv = build_moves(el, nba, ids)
    print(
        f"[moves] {len(mv)} moves at >={MIN_GAMES} games both sides: "
        + ", ".join(f"{d}={n}" for d, n in mv.direction.value_counts().items())
    )
    print(
        f"[moves] with >=2 prior source seasons: {int((mv.prior_n >= 2).sum())} "
        "(R-H otherwise, scored by the B1b path)"
    )
    mv.to_parquet(args.out_dir / "nba_moves.parquet", index=False)

    sc, fits = walk_forward(mv)
    print(
        f"[walk-forward] scored {len(sc)} moves across seasons "
        f"{sorted(sc.season_dst.unique().tolist())}, {sc.cluster.nunique()} clusters"
    )
    for S, f in fits.items():
        print(
            f"  {S}: k={ {d: round(v, 4) for d, v in f['k'].items()} } w={f['w']} "
            f"prior={f['n_prior']} scored={f['n_scored']}"
        )

    arms = {a: metrics(sc, a) for a in ["B0", "B1b", "B1c", "M"]}
    for a, m in arms.items():
        print(
            f"[arm] {a:4s} MAE={m['mae']:.4f} RMSE={m['rmse']:.4f} "
            f"R2={m['r2']:+.4f} bias={m['bias']:+.4f}"
        )
    c = {
        "B1b_vs_B0": contrast(sc, "B1b", "B0"),
        "M_vs_B0": contrast(sc, "M", "B0"),
        "B1c_vs_B1b": contrast(sc, "B1c", "B1b"),
        "M_vs_B1b": contrast(sc, "M", "B1b"),
        "M_vs_B1c": contrast(sc, "M", "B1c"),
    }
    for k, v in c.items():
        print(
            f"[contrast] {k}: delta={v['delta_mae']:+.4f} "
            f"CI [{v['ci'][0]:+.4f},{v['ci'][1]:+.4f}] "
            f"excludes_zero={v['excludes_zero']}"
        )

    # P1 as pre-registered
    p1a = (not c["B1c_vs_B1b"]["excludes_zero"]) or c["B1c_vs_B1b"][
        "delta_mae"
    ] > 0  # B1b does not beat B1c
    p1b = (
        c["M_vs_B1b"]["excludes_zero"]
        and c["M_vs_B1b"]["delta_mae"] > 0
        and c["M_vs_B1c"]["excludes_zero"]
        and c["M_vs_B1c"]["delta_mae"] > 0
    )
    g1_margin = 0.05 * arms["B0"]["mae"]
    g1 = (arms["B0"]["mae"] - arms["M"]["mae"] >= g1_margin) and c["M_vs_B0"][
        "excludes_zero"
    ]
    print(
        f"[P1] (a) multiplier does not beat RTM-alone: {p1a} | "
        f"(b) combined beats both: {p1b} -> P1 {'PASS' if p1b else 'FAIL'}"
    )
    print(f"[G1] M beats B0 by >=5% ({g1_margin:.4f}) with CI excluding 0: {g1}")
    # gate shown to fail (impossible margin)
    assert not ((arms["B0"]["mae"] - arms["M"]["mae"]) >= 0.5 * arms["B0"]["mae"]), (
        "impossible 50% margin passed"
    )
    print("[gate-fails] G1 at an impossible 50% margin: FAIL (as required)")

    # per direction
    per_dir = {}
    for d, sub in sc.groupby("direction"):
        per_dir[d] = {
            "n": int(len(sub)),
            **{a: metrics(sub, a) for a in ["B0", "B1b", "B1c", "M"]},
        }
        print(
            f"[direction] {d} n={len(sub)} MAE B0={per_dir[d]['B0']['mae']:.3f} "
            f"B1b={per_dir[d]['B1b']['mae']:.3f} B1c={per_dir[d]['B1c']['mae']:.3f} "
            f"M={per_dir[d]['M']['mae']:.3f}"
        )

    # T3: the five contrasts per direction, never averaged across directions
    per_dir_contrasts = {}
    for d, sub in sc.groupby("direction"):
        sub = sub.reset_index(drop=True)
        per_dir_contrasts[d] = {
            "n": int(len(sub)),
            "B1b_vs_B0": contrast(sub, "B1b", "B0"),
            "M_vs_B0": contrast(sub, "M", "B0"),
            "B1c_vs_B1b": contrast(sub, "B1c", "B1b"),
            "M_vs_B1b": contrast(sub, "M", "B1b"),
            "M_vs_B1c": contrast(sub, "M", "B1c"),
        }
        for kk_, v in per_dir_contrasts[d].items():
            if kk_ == "n":
                continue
            print(
                f"[T3 {d}] {kk_}: delta={v['delta_mae']:+.4f} "
                f"CI [{v['ci'][0]:+.4f},{v['ci'][1]:+.4f}] "
                f"excludes_zero={v['excludes_zero']}"
            )

    # T6 on the SCORED arms: is "worse than nothing" a weighting artifact?
    est_sens = {}
    for name in ESTIMATORS:
        sc_e, _ = walk_forward(mv, estimator=name)
        row = {a_: metrics(sc_e, a_)["mae"] for a_ in ["B0", "B1b", "B1c", "M"]}
        row["B1b_vs_B0"] = contrast(sc_e, "B1b", "B0")
        for d, sub in sc_e.groupby("direction"):
            row[f"{d}_B1b_mae"] = metrics(sub, "B1b")["mae"]
            row[f"{d}_B0_mae"] = metrics(sub, "B0")["mae"]
        est_sens[name] = row
        print(
            f"[T6 scored] {name}: B0={row['B0']:.4f} B1b={row['B1b']:.4f} "
            f"B1c={row['B1c']:.4f} M={row['M']:.4f} | B1b vs B0 "
            f"delta={row['B1b_vs_B0']['delta_mae']:+.4f} "
            f"CI [{row['B1b_vs_B0']['ci'][0]:+.4f},{row['B1b_vs_B0']['ci'][1]:+.4f}]"
        )

    # POST-HOC (not pre-registered, labelled): the direction ratio with the
    # player's prior-season MEAN as the source instead of his last season. If
    # it lands near 1.0 the "multiplier" was regression to the mean.
    posthoc = {}
    for d, sub in mv[mv.prior_n >= 2].groupby("direction"):
        w_ = np.minimum(sub.min_src, sub.min_dst)
        ratio_last = float(np.sum(w_ * sub.dst / sub.src) / np.sum(w_))
        ratio_prior = float(np.sum(w_ * sub.dst / sub.prior_mean) / np.sum(w_))
        rng_ = np.random.default_rng(SEED)
        idx = np.arange(len(sub))
        boots = []
        for _ in range(2000):
            b_ = rng_.choice(idx, len(idx))
            boots.append(
                float(
                    np.sum(w_.iloc[b_] * sub.dst.iloc[b_] / sub.prior_mean.iloc[b_])
                    / np.sum(w_.iloc[b_])
                )
            )
        posthoc[d] = {
            "n": int(len(sub)),
            "ratio_on_last_season": ratio_last,
            "ratio_on_prior_mean": ratio_prior,
            "ratio_on_prior_mean_ci": [
                float(np.percentile(boots, 2.5)),
                float(np.percentile(boots, 97.5)),
            ],
        }
        print(
            f"[post-hoc {d}] n={len(sub)} ratio dst/last-season={ratio_last:.4f} "
            f"vs dst/prior-mean={ratio_prior:.4f} "
            f"CI [{posthoc[d]['ratio_on_prior_mean_ci'][0]:.4f},"
            f"{posthoc[d]['ratio_on_prior_mean_ci'][1]:.4f}]"
        )

    # T7 age: birth years exist on both sides; split at 27 (Pelton's development peak)
    age = sc.merge(ids[["key", "el_birth_year"]], on="key", how="left")
    age["age_dst"] = age.season_dst - age.el_birth_year
    t7 = {}
    for name, mask in {
        "under_27": age.age_dst < 27,
        "27_plus": age.age_dst >= 27,
    }.items():
        sub = age[mask]
        t7[name] = {
            "n": int(len(sub)),
            **{a_: metrics(sub, a_)["mae"] for a_ in ["B0", "B1b", "B1c", "M"]},
        }
    print(f"[T7 age] {json.dumps(t7)}")

    # T1 selection: bias split by source season above own prior mean
    h = sc[sc.prior_n >= 2].copy()
    h["above"] = h.src > h.prior_mean
    t1 = {
        str(k): {
            "n": int(len(g)),
            "bias_M": float((g.M - g.dst).mean()),
            "bias_B1b": float((g.B1b - g.dst).mean()),
        }
        for k, g in h.groupby("above")
    }
    print(f"[T1] bias by source-season-above-own-prior: {json.dumps(t1)}")

    # T8 negative control: swap direction constants
    swapped = sc.copy()
    kmap = {"EL_to_NBA": "NBA_to_EL", "NBA_to_EL": "EL_to_NBA"}
    # rebuild B1b with the other direction's k per season
    swapped["B1b_swapped"] = np.nan
    for S, f in fits.items():
        m = swapped.season_dst == S
        for d in f["k"]:
            other = f["k"].get(kmap[d])
            if other is not None:
                swapped.loc[m & (swapped.direction == d), "B1b_swapped"] = (
                    other * swapped.loc[m & (swapped.direction == d), "src"]
                )
    sw = swapped.dropna(subset=["B1b_swapped"])
    mae_sw = float((sw.B1b_swapped - sw.dst).abs().mean())
    mae_ok = float((sw.B1b - sw.dst).abs().mean())
    print(
        f"[T8] swapped-direction constants: MAE {mae_sw:.4f} vs correct {mae_ok:.4f} "
        f"on {len(sw)} moves"
    )
    assert mae_sw > mae_ok, (
        "negative control failed: swapping the direction constants did not hurt"
    )
    # T8b: permute prior histories across players (200 reps) -- M's gain over
    # B1b must not be reached
    rng = np.random.default_rng(SEED)
    real_gain = arms["B1b"]["mae"] - arms["M"]["mae"]
    reached = 0
    null = []
    hh = sc[sc.prior_n >= 2]
    for _ in range(200):
        perm = hh.copy()
        perm["prior_mean"] = rng.permutation(perm.prior_mean.to_numpy())
        # recompute M with the season's w and k
        mvals = []
        for r in perm.itertuples(index=False):
            f = fits[r.season_dst]
            mvals.append(
                f["k"][r.direction] * (f["w"] * r.src + (1 - f["w"]) * r.prior_mean)
            )
        perm["M_perm"] = mvals
        gain = float(
            (perm.B1b - perm.dst).abs().mean() - (perm.M_perm - perm.dst).abs().mean()
        )
        null.append(gain)
        reached += gain >= real_gain
    print(
        f"[T8b] permuted histories: real gain {real_gain:+.4f}, "
        f"null mean {np.mean(null):+.4f}, p95 {np.percentile(null, 95):+.4f}, "
        f"reps reaching real {reached}/200"
    )

    # T4 sensitivities
    sens = {}
    for name, mask in {
        "ge15_games": (sc.games_src >= 15) & (sc.games_dst >= 15),
        "ge100_min": (sc.min_src >= 100) & (sc.min_dst >= 100),
    }.items():
        sub = sc[mask]
        sens[name] = {
            "n": int(len(sub)),
            **{a: metrics(sub, a)["mae"] for a in ["B0", "B1b", "B1c", "M"]},
        }
    print(f"[T4] {json.dumps(sens)}")
    # T6 estimator spread on the pooled direction constants (full sample, descriptive)
    t6 = {
        d: {
            "exposure_weighted": exposure_weighted(s),
            "ratio_of_sums": ratio_of_sums(s),
            "mean_of_ratios": mean_of_ratios(s),
            "n": int(len(s)),
        }
        for d, s in mv.groupby("direction")
    }
    print(f"[T6] full-sample direction factors by estimator: {json.dumps(t6)}")
    # T9 power: detectable delta at 80% power from the paired-difference SD
    e_b = (sc.B1b - sc.dst).abs() - (sc.M - sc.dst).abs()
    se = float(e_b.std(ddof=1) / np.sqrt(len(e_b)))
    print(
        f"[T9] paired-difference SE {se:.4f}; detectable |delta MAE| at 80% power "
        f"~ {2.8 * se:.4f} at n={len(sc)}"
    )

    # P2 composition (descriptive): players with domestic(t-1) -> EL(t) -> NBA(t+1)
    p2 = {
        "n": 0,
        "note": "requires the Proballers domestic side; computed if reachable",
    }
    try:
        from scripts import build_league_factors as blf

        # Pinned to the corpus the 2026-09-03 NBA-arm note was measured on;
        # the estimator defaults to the API destination since Amendment 4.
        games = blf.add_usage(blf.load_player_games(continental_source="proballers"))
        dom = games[
            ~games.league.isin(blf.CONTINENTAL) & ~games.league.isin(blf.NOT_A_SOURCE)
        ]
        dom["player_key"] = dom.player_name.map(norm_key)
        dagg = (
            dom.groupby(["player_key", "season", "league"])
            .agg(
                games=("game_id", "nunique"),
                minutes=("minutes", "sum"),
                pir=("pir", "sum"),
            )
            .reset_index()
        )
        dagg = dagg[dagg.games >= MIN_GAMES]
        dagg["per36"] = 36 * dagg.pir / dagg.minutes
        fac = pd.read_parquet(
            REPO / "data" / "processed" / "translation" / "league_factors.parquet"
        )
        fac = fac[
            (fac.stat == "pir")
            & (fac.era == "all")
            & (fac["sample"] == "all_pairs")
            & (fac.destination == "euroleague")
        ][["league", "factor"]]
        chain = (
            sc[sc.direction == "EL_to_NBA"]
            .merge(
                dagg.assign(season=dagg.season + 1).rename(
                    columns={"player_key": "key", "per36": "dom36"}
                ),
                left_on=["key", "season_src"],
                right_on=["key", "season"],
            )
            .merge(fac, on="league")
        )
        if len(chain):
            kk = chain.season_dst.map(lambda S: fits[S]["k"]["EL_to_NBA"])
            chain["chained"] = chain.dom36 * chain.factor * kk
            p2 = {
                "n": int(len(chain)),
                "mae_chained": float((chain.chained - chain.dst).abs().mean()),
                "mae_B0_domestic": float((chain.dom36 - chain.dst).abs().mean()),
                "mae_unchained_EL": float((chain.B1b - chain.dst).abs().mean()),
            }
            chain[
                ["key", "league", "season_src", "dom36", "src", "dst", "chained", "B1b"]
            ].to_csv(args.out_dir / "p2_chain.csv", index=False)
    except Exception as exc:  # noqa: BLE001 -- P2 is descriptive; a missing domestic side is reported, not fatal
        p2["error"] = str(exc)[:200]
    print(f"[P2] {json.dumps(p2)}")

    out = {
        "identity": idc,
        "moves": {
            "total": int(len(mv)),
            "by_direction": mv.direction.value_counts().to_dict(),
            "with_history": int((mv.prior_n >= 2).sum()),
        },
        "walk_forward": {
            "n_scored": int(len(sc)),
            "n_clusters": int(sc.cluster.nunique()),
            "fits": {str(k): v for k, v in fits.items()},
        },
        "arms": arms,
        "contrasts": c,
        "P1": {
            "a_multiplier_does_not_beat_rtm": bool(p1a),
            "b_combined_beats_both": bool(p1b),
            "verdict": "PASS" if p1b else "FAIL",
        },
        "G1": {"pass": bool(g1), "margin": g1_margin},
        "per_direction": per_dir,
        "T1_selection": t1,
        "T3_per_direction_contrasts": per_dir_contrasts,
        "T6_scored_by_estimator": est_sens,
        "posthoc_ratio_on_prior_mean": posthoc,
        "T7_age": t7,
        "T5_per_possession": "not run: the totals endpoint carries no possessions",
        "T4_sensitivity": sens,
        "T6_estimators": t6,
        "T8_swapped_mae": {"swapped": mae_sw, "correct": mae_ok, "n": int(len(sw))},
        "T8b_permuted_histories": {
            "real_gain": real_gain,
            "null_mean": float(np.mean(null)),
            "null_p95": float(np.percentile(null, 95)),
            "reached": int(reached),
        },
        "T9_power": {"se": se, "detectable_delta_80pct": 2.8 * se, "n": int(len(sc))},
        "P2": p2,
    }
    (args.out_dir / "nba_arm_summary.json").write_text(
        json.dumps(out, indent=1, default=float)
    )
    sc.to_parquet(args.out_dir / "nba_arm_scored.parquet", index=False)
    print(
        "[done] wrote nba_moves.parquet nba_arm_scored.parquet nba_arm_summary.json "
        f"to {args.out_dir}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
