#!/usr/bin/env python3
"""E16: a flexible model on the 674 v10 anchor forecasts (SSAC27 full paper).

Pre-registration: docs/research/sloan-full-paper-preregistration-amendment-1-2026-11-04.md
(Amendment 1, commit f1a3453da, pushed 2026-11-04 before this file existed),
section E16, on top of docs/research/sloan-full-paper-preregistration-2026-11-03.md.
Everything here is EXPLORATORY: destination seasons 2020-2025 were inspected for
the submitted abstract.

* Features (registered): source per-36 components (points, offensive and
  defensive rebounds, assists, steals, blocks, turnovers, 3-point attempts,
  free-throw attempts); source minutes per game, games and usage; x, h, a (the
  v10 history design); age and age squared (E5b ages, centred at 26) with an
  indicator where missing; destination; source league one-hot; source-club
  domestic win share in the source season from Proballers game files; with or
  without the translated feature z.
* Models, hyperparameters fixed in the amendment: (i) HistGradientBoostingRegressor
  with the registered settings; (ii) ridge on standardised features, penalty 10 on
  every non-history term (history = intercept, x, h, a).
* Fitting: walk-forward exactly as v10, same training rows, one refit per
  destination season using earlier seasons only.
* Gate G16: source-club win share joins >= 90% of the 674. Negative control: a
  100% threshold on a deliberately broken join key must fail.
* Primary: MAE(offsets lambda10) - MAE(GBM, no z) on the 674, two-way clustered.
  Secondary: GBM vs GBM + z; ridge-full without vs with club win share; every
  model's share of reducible error removed (E6 floor).

Threats and controls (all in this file): drift from the submitted numbers (G0
re-run with its negative control); different training rows from v10 (per-season
training-key identity gate with a dropped-row negative control); a ridge that is
not the v10 history model on the history terms (reproduction check against
history_only to 1e-9); 2026-27 exposure (Proballers files are read only for the
cohort's source seasons, at most 2024); tuning (one fixed configuration, every
model and every contrast printed).
"""

# ruff: noqa: E501 -- gate messages and licensed sentences
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

from scripts import sloan_fullpaper_common as common  # noqa: E402
from scripts import sloan_fullpaper_robustness as robust  # noqa: E402
from scripts.translation_research_common import sha256_file  # noqa: E402

AMENDMENT = (
    ROOT / "docs/research/sloan-full-paper-preregistration-amendment-1-2026-11-04.md"
)
AMENDMENT_COMMIT = "f1a3453da"
KEY = common.KEY
OUTCOME = "pir_per36_dest"  # holds EFF/36 exactly (v10 naming)
EXPECTED_TARGETS = 674
N_BOOT = 2000
SEED = 0

#: Registered in Amendment 1, E16 (i). Never tuned.
HGB_PARAMS = {
    "loss": "absolute_error",
    "learning_rate": 0.05,
    "max_iter": 300,
    "max_leaf_nodes": 15,
    "min_samples_leaf": 20,
    "l2_regularization": 1.0,
    "early_stopping": False,
    "random_state": 0,
}
#: Registered in Amendment 1, E16 (ii).
RIDGE_PENALTY = 10.0
HISTORY_TERMS = ("x", "h", "a")  # plus the intercept: never penalised
#: The E15 component list, per 36 source minutes.
COMPONENTS = ("pts", "oreb", "dreb", "ast", "stl", "blk", "tov", "fg3a", "fta")
G16_THRESHOLD = 0.90
BROKEN_SUFFIX = "\x00broken-join-key"

#: E6 noise floor (EFF/36, normal model) from the committed robustness summary.
ROBUSTNESS_SUMMARY = Path(
    "docs/research/artifacts/sloan-fullpaper-robustness-2026-11-03/summary.json"
)
ROBUSTNESS_SUMMARY_SHA = (
    "ec2e2c10f44b801a1af099600841a73058872f9430b3aecfaf507a7fc32c91db"
)
PROBALLERS_TREES = ("proballers", "_inactive_leagues/proballers")
LAST_SOURCE_SEASON = 2024  # source of destination 2025; 2025-26 files never read

HISTORY = common.PRIMARY_ARMS["history"]
HISTORY_T = common.PRIMARY_ARMS["history_translation"]
OFFSETS = common.PRIMARY_ARMS["offsets10"]
OFFSETS_T = common.PRIMARY_ARMS["offsets10_translation"]
REFERENCE_ARMS = (HISTORY, HISTORY_T, OFFSETS, OFFSETS_T)

#: arm -> (model, with z, with club win share)
ARMS = {
    "gbm": ("gbm", False, True),
    "gbm_z": ("gbm", True, True),
    "gbm_noclub": ("gbm", False, False),
    "gbm_noclub_z": ("gbm", True, False),
    "ridge": ("ridge", False, True),
    "ridge_z": ("ridge", True, True),
    "ridge_noclub": ("ridge", False, False),
    "ridge_noclub_z": ("ridge", True, False),
}
LABELS = {
    HISTORY: "history",
    HISTORY_T: "history + translation",
    OFFSETS: "offsets λ10 (league-aware)",
    OFFSETS_T: "offsets λ10 + translation",
    "gbm": "GBM, all features, no z",
    "gbm_z": "GBM, all features + z",
    "gbm_noclub": "GBM without club win share, no z",
    "gbm_noclub_z": "GBM without club win share, + z",
    "ridge": "ridge-full, no z",
    "ridge_z": "ridge-full + z",
    "ridge_noclub": "ridge without club win share, no z",
    "ridge_noclub_z": "ridge without club win share, + z",
}
#: name -> (left, right, role); positive favours right. With G16 passed.
CONTRASTS = {
    "primary_offsets10_vs_gbm": (OFFSETS, "gbm", "primary"),
    "gbm_translation_increment": ("gbm", "gbm_z", "secondary"),
    "ridge_club_increment": ("ridge_noclub", "ridge", "secondary"),
    "gbm_club_increment": ("gbm_noclub", "gbm", "printed"),
    "ridge_translation_increment": ("ridge", "ridge_z", "printed"),
    "offsets10_vs_ridge": (OFFSETS, "ridge", "printed"),
    "history_vs_gbm": (HISTORY, "gbm", "printed"),
    "history_vs_ridge": (HISTORY, "ridge", "printed"),
    "offsets10_translation_vs_gbm_z": (OFFSETS_T, "gbm_z", "printed"),
    "offsets10_translation_increment_reference": (OFFSETS, OFFSETS_T, "printed"),
}
#: The same, when G16 fails: the models run without club win share.
CONTRASTS_NO_CLUB = {
    "primary_offsets10_vs_gbm": (OFFSETS, "gbm_noclub", "primary"),
    "gbm_translation_increment": ("gbm_noclub", "gbm_noclub_z", "secondary"),
    "ridge_translation_increment": ("ridge_noclub", "ridge_noclub_z", "printed"),
    "offsets10_vs_ridge": (OFFSETS, "ridge_noclub", "printed"),
    "history_vs_gbm": (HISTORY, "gbm_noclub", "printed"),
    "history_vs_ridge": (HISTORY, "ridge_noclub", "printed"),
    "offsets10_translation_vs_gbm_z": (OFFSETS_T, "gbm_noclub_z", "printed"),
    "offsets10_translation_increment_reference": (OFFSETS, OFFSETS_T, "printed"),
}

#: The E2 sentence the recipes track earned (docs/research/sloan-fullpaper-recipes-2026-11-03.md).
E2_SENTENCE = "None of six standard recipes adds more than 2% accuracy once the forecast knows both leagues."
#: The league-aware model's share quoted in the registered E16 licence.
REGISTERED_LEAGUE_AWARE_SHARE_PCT = 18.8


class GateFailure(common.GateFailure):
    pass


def negative_control(check, *args, **kwargs) -> str:
    """A gate that cannot fail checks nothing (METHOD.md §8)."""
    try:
        check(*args, **kwargs)
    except common.GateFailure:
        return "rejected as required"
    raise GateFailure(f"negative control passed: {check.__name__}")


# ------------------------------------------------------ club win share --
def load_proballers(raw_root: Path, leagues, seasons):
    """Game results and per-player team rows, both Proballers trees, de-duplicated.

    The active and inactive trees overlap (one season each for spain-acb and
    bcl), so games are unique on (league, season, game_id) and player rows on
    (league, season, game_id, team, player_name).
    """
    games, stats, files = [], [], {}
    for tree in PROBALLERS_TREES:
        for league in leagues:
            for season in seasons:
                folder = Path(raw_root) / tree / league / str(season)
                g = folder / f"games_{league}_{season}.parquet"
                p = folder / f"player_stats_{league}_{season}.parquet"
                if not g.is_file():
                    continue
                files[str(g.relative_to(raw_root))] = sha256_file(g)
                frame = pd.read_parquet(
                    g,
                    columns=[
                        "game_id",
                        "home_team",
                        "away_team",
                        "home_score",
                        "away_score",
                    ],
                )
                frame["league"], frame["season"] = league, int(season)
                games.append(frame)
                if p.is_file():
                    files[str(p.relative_to(raw_root))] = sha256_file(p)
                    frame = pd.read_parquet(
                        p, columns=["game_id", "player_name", "team", "points"]
                    )
                    frame["league"], frame["season"] = league, int(season)
                    stats.append(frame)
    games = pd.concat(games, ignore_index=True)
    stats = pd.concat(stats, ignore_index=True)
    for frame in (games, stats):
        frame["game_id"] = frame.game_id.astype(str)
    games = games.drop_duplicates(["league", "season", "game_id"], keep="first")
    stats = stats.drop_duplicates(
        ["league", "season", "game_id", "team", "player_name"], keep="first"
    )
    return games.reset_index(drop=True), stats.reset_index(drop=True), files


def link_team_names(games: pd.DataFrame, stats: pd.DataFrame) -> pd.DataFrame:
    """Map each player-row team name to its game-file name, league-season by league-season.

    Player rows and game files spell clubs differently (sponsor names). For each
    game a player-row team takes the side (home or away) whose final score is
    closest to the sum of its players' points; the game-file name of that side is
    one vote. The plurality name is the link. A game-file name claimed by two
    player-row names is ambiguous and both links are dropped.
    """
    scope = ["league", "season", "game_id"]
    points = stats.groupby([*scope, "team"], as_index=False).points.sum()
    m = points.merge(
        games[[*scope, "home_team", "away_team", "home_score", "away_score"]], on=scope
    )
    to_home = (m.points - m.home_score).abs()
    to_away = (m.points - m.away_score).abs()
    m["games_name"] = np.where(
        to_home < to_away, m.home_team, np.where(to_away < to_home, m.away_team, None)
    )
    votes = (
        m.dropna(subset=["games_name"])
        .groupby(["league", "season", "team", "games_name"])
        .size()
        .rename("votes")
        .reset_index()
    )
    votes["games_voted"] = votes.groupby(["league", "season", "team"]).votes.transform(
        "sum"
    )
    best = votes.sort_values(
        ["league", "season", "team", "votes", "games_name"],
        ascending=[True, True, True, False, True],
    ).drop_duplicates(["league", "season", "team"])
    best["agreement"] = best.votes / best.games_voted
    claimed = best.groupby(["league", "season", "games_name"]).team.transform("size")
    best["ambiguous"] = claimed.gt(1)
    return best.reset_index(drop=True)


def team_records(games: pd.DataFrame) -> pd.DataFrame:
    """Wins and decided games per (league, season, game-file team); tied scores are not results."""
    decided = games.loc[games.home_score.ne(games.away_score)]
    sides = []
    for name, own, other in (
        ("home_team", "home_score", "away_score"),
        ("away_team", "away_score", "home_score"),
    ):
        sides.append(
            pd.DataFrame(
                {
                    "league": decided.league,
                    "season": decided.season,
                    "games_name": decided[name],
                    "win": decided[own] > decided[other],
                }
            )
        )
    both = pd.concat(sides, ignore_index=True)
    out = both.groupby(["league", "season", "games_name"], as_index=False).agg(
        club_games=("win", "size"), club_wins=("win", "sum")
    )
    out["club_win_share"] = out.club_wins / out.club_games
    return out


def club_win_share(
    cohort: pd.DataFrame, links: pd.DataFrame, records: pd.DataFrame, *, suffix=""
) -> pd.DataFrame:
    """Source-club domestic win share for every cohort row; NaN where it does not join."""
    usable = links.loc[~links.ambiguous]
    table = usable.merge(records, on=["league", "season", "games_name"], how="inner")
    table = table.rename(
        columns={"league": "league_src", "season": "join_season", "team": "join_club"}
    )
    rows = cohort[[*KEY, "league_src", "season_src", "club_src"]].copy()
    rows["join_club"] = rows.club_src.astype(str) + suffix
    rows["join_season"] = rows.season_src.astype(int)
    out = rows.merge(
        table,
        on=["league_src", "join_season", "join_club"],
        how="left",
        validate="m:1",
    )
    return out[
        [
            *KEY,
            "league_src",
            "season_src",
            "club_src",
            "games_name",
            "votes",
            "games_voted",
            "agreement",
            "club_games",
            "club_wins",
            "club_win_share",
        ]
    ]


def coverage(shares: pd.DataFrame, keys: pd.DataFrame) -> dict:
    on = keys.merge(shares, on=KEY, how="left", validate="1:1")
    joined = np.isfinite(on.club_win_share.to_numpy(dtype=float))
    return {
        "targets": len(on),
        "joined": int(joined.sum()),
        "share": float(joined.mean()),
        "unjoined": on.loc[~joined, [*KEY, "league_src", "season_src", "club_src"]]
        .astype(str)
        .to_dict("records"),
    }


def assert_g16(share: float, threshold: float = G16_THRESHOLD) -> None:
    if not share >= threshold:
        raise GateFailure(f"G16 failed: club win share joins {share:.4f} < {threshold}")


# ------------------------------------------------------------ features --
def feature_table(features: pd.DataFrame, ages: pd.DataFrame, shares: pd.DataFrame):
    """v10 feature rows plus the E16 columns, keyed 1:1."""
    out = features.merge(
        ages[[*KEY, "age_c26", "age_c26_sq"]], on=KEY, how="left", validate="1:1"
    ).merge(shares[[*KEY, "club_win_share"]], on=KEY, how="left", validate="1:1")
    if len(out) != len(features):
        raise GateFailure("E16 feature join changed the row count")
    return out


def design(rows: pd.DataFrame, leagues, *, z: bool, club: bool, club_indicator: bool):
    """The registered E16 design; history terms are x, h, a exactly as v10's _rtm_design."""
    minutes = rows.minutes_src.to_numpy(dtype=float)
    prior = rows.prior_mean_pir36.to_numpy(dtype=float)
    x = rows.pir_per36_src.to_numpy(dtype=float)
    cols = {
        "x": x,
        "h": np.where(np.isnan(prior), x, prior),
        "a": rows.above_own_prior.fillna(0).to_numpy(dtype=float),
    }
    for c in COMPONENTS:
        cols[f"{c}36_src"] = 36.0 * rows[f"{c}_src"].to_numpy(dtype=float) / minutes
    cols["min_per_game_src"] = rows.min_per_game_src.to_numpy(dtype=float)
    cols["games_src"] = rows.games_src.to_numpy(dtype=float)
    cols["usage_src"] = rows.usage_src.to_numpy(dtype=float)
    age = rows.age_c26.to_numpy(dtype=float)
    missing = ~np.isfinite(age)
    cols["age_c26"] = np.where(missing, 0.0, age)
    cols["age_c26_sq"] = np.where(missing, 0.0, rows.age_c26_sq.to_numpy(dtype=float))
    cols["age_missing"] = missing.astype(float)
    cols["destination_euroleague"] = rows.league_dest.eq("euroleague").to_numpy(float)
    for league in leagues:
        cols[f"source:{league}"] = rows.league_src.eq(league).to_numpy(dtype=float)
    if club:
        share = rows.club_win_share.to_numpy(dtype=float)
        absent = ~np.isfinite(share)
        cols["club_win_share"] = np.where(absent, 0.5, share)
        if club_indicator:
            cols["club_win_share_missing"] = absent.astype(float)
    if z:
        cols["z"] = rows.scheduled_translated.to_numpy(dtype=float)
    frame = pd.DataFrame(cols, index=rows.index)
    if not np.isfinite(frame.to_numpy()).all():
        raise ValueError("nonfinite E16 design value")
    return frame


def fit_ridge(train_x: pd.DataFrame, y, test_x: pd.DataFrame, penalty=RIDGE_PENALTY):
    """Ridge on training-standardised columns; intercept and HISTORY_TERMS unpenalised.

    The penalty is applied as in the v10 source offsets: sqrt(penalty) rows
    appended to the least-squares system (sum of squares + penalty * ||beta||^2).
    A column constant in the training rows carries no information and is dropped.
    """
    mean = train_x.mean(axis=0)
    sd = train_x.std(axis=0, ddof=0)
    keep = (sd > 0).to_numpy()
    names = list(train_x.columns[keep])

    def standardise(frame):
        return ((frame[names] - mean[names]) / sd[names]).to_numpy(dtype=float)

    x = np.column_stack([np.ones(len(train_x)), standardise(train_x)])
    z = np.column_stack([np.ones(len(test_x)), standardise(test_x)])
    penalised = np.array([False] + [n not in HISTORY_TERMS for n in names])
    regulariser = np.zeros((int(penalised.sum()), x.shape[1]))
    regulariser[np.arange(regulariser.shape[0]), np.flatnonzero(penalised)] = np.sqrt(
        penalty
    )
    beta = np.linalg.lstsq(
        np.vstack([x, regulariser]),
        np.r_[np.asarray(y, dtype=float), np.zeros(regulariser.shape[0])],
        rcond=None,
    )[0]
    prediction = z @ beta
    if not np.isfinite(prediction).all():
        raise ValueError("nonfinite ridge prediction")
    return prediction, {"coefficients": dict(zip(["intercept", *names], beta.tolist()))}


def fit_gbm(train_x: pd.DataFrame, y, test_x: pd.DataFrame):
    from sklearn.ensemble import HistGradientBoostingRegressor

    model = HistGradientBoostingRegressor(**HGB_PARAMS)
    model.fit(train_x.to_numpy(dtype=float), np.asarray(y, dtype=float))
    prediction = model.predict(test_x.to_numpy(dtype=float))
    if not np.isfinite(prediction).all():
        raise ValueError("nonfinite GBM prediction")
    return prediction, {"n_iter": int(model.n_iter_)}


def training_rows(table: pd.DataFrame, season: int) -> pd.DataFrame:
    """v10's training rows for one destination season: earlier seasons, feature-eligible."""
    return table.loc[table.season_dest.lt(season) & table.feature_eligible].sort_values(
        KEY
    )


def walk_forward(table: pd.DataFrame, arms, *, seasons=common.ANCHOR_SEASONS):
    """One refit per destination season on v10's training rows."""
    club_indicator = bool(table.club_win_share.isna().any())
    out, training = [], {}
    for season in seasons:
        train = training_rows(table, season)
        test = table.loc[
            table.season_dest.eq(season) & table.feature_eligible
        ].sort_values(KEY)
        leagues = sorted(train.league_src.unique())
        y = train[OUTCOME].to_numpy(dtype=float)
        predicted = test[KEY].copy()
        info = {
            "train_keys": [
                [str(p), int(s)] for p, s in zip(train.player_name, train.season_dest)
            ],
            "train_rows": len(train),
            "test_rows": len(test),
            "source_categories": leagues,
            "arms": {},
        }
        for arm in arms:
            model, z, club = ARMS[arm]
            tx = design(train, leagues, z=z, club=club, club_indicator=club_indicator)
            vx = design(test, leagues, z=z, club=club, club_indicator=club_indicator)
            fit = fit_gbm if model == "gbm" else fit_ridge
            predicted[arm], detail = fit(tx, y, vx)
            info["arms"][arm] = {"features": list(tx.columns), **detail}
        training[str(season)] = info
        out.append(predicted)
    return pd.concat(out, ignore_index=True), training


def assert_training_rows(training: dict, folds: list) -> None:
    """E16 trains on exactly v10's training keys in every destination season."""
    for fold in folds:
        mine = {(k[0], int(k[1])) for k in training[str(fold["season"])]["train_keys"]}
        v10 = {(k["player_name"], int(k["season_dest"])) for k in fold["train_keys"]}
        if mine != v10:
            raise GateFailure(
                f"training rows differ from v10 in {fold['season']}: {len(mine ^ v10)} keys"
            )


def history_reproduction(table: pd.DataFrame, anchor: pd.DataFrame) -> float:
    """The ridge fitter on (1, x, h, a) alone must equal v10 history_only."""
    worst = 0.0
    cols = list(HISTORY_TERMS)
    indexed = table.set_index(KEY)
    for season in common.ANCHOR_SEASONS:
        train = training_rows(table, season)
        test = anchor.loc[anchor.season_dest.eq(season)].sort_values(KEY)
        rows = indexed.loc[pd.MultiIndex.from_frame(test[KEY])].reset_index()
        tx = design(train, [], z=False, club=False, club_indicator=False)[cols]
        vx = design(rows, [], z=False, club=False, club_indicator=False)[cols]
        prediction, _ = fit_ridge(tx, train[OUTCOME], vx)
        worst = max(worst, float(np.max(np.abs(prediction - test[HISTORY].to_numpy()))))
    return worst


# ---------------------------------------------------------- estimators --
def reducible_shares(
    rows: pd.DataFrame, arms, floor: float, *, n_boot=N_BOOT, seed=SEED
) -> dict:
    """Share of reducible error removed: [MAE(history) - MAE(m)] / [MAE(history) - floor].

    The floor is fixed (E6); the interval resamples destination club-seasons
    (2,000 draws, seed 0), one common set of draws for every model.
    """
    codes, clusters = pd.factorize(rows.cluster, sort=False)
    sizes = np.bincount(codes, minlength=len(clusters)).astype(float)
    errors = {
        a: np.abs(rows[a] - rows[OUTCOME]).to_numpy(dtype=float)
        for a in dict.fromkeys((HISTORY, *arms))
    }
    sums = {
        a: np.bincount(codes, weights=e, minlength=len(clusters))
        for a, e in errors.items()
    }
    rng = np.random.default_rng(seed)
    picked = rng.integers(0, len(clusters), (n_boot, len(clusters)))
    n = sizes[picked].sum(axis=1)
    hist = sums[HISTORY][picked].sum(axis=1) / n
    mh = float(errors[HISTORY].mean())
    out = {}
    for a in arms:
        m = float(errors[a].mean())
        draws = (hist - sums[a][picked].sum(axis=1) / n) / (hist - floor)
        out[a] = {
            "mae": m,
            "mae_minus_floor": m - floor,
            "share_of_reducible_removed": (mh - m) / (mh - floor),
            "ci95_percentile": [
                float(np.quantile(draws, 0.025)),
                float(np.quantile(draws, 0.975)),
            ],
        }
    return {
        "floor": floor,
        "history_mae": mh,
        "reducible": mh - floor,
        "clusters": len(clusters),
        "n_boot": n_boot,
        "seed": seed,
        "models": out,
    }


def licensed_primary(
    record: dict, shares: dict, n_features: int, primary_arm: str
) -> str:
    """The registered E16 primary licence (two-way clustered interval)."""
    ci = record["player_club_season"]["ci95"]
    if ci is None:
        return "no E16 sentence: the primary interval is not estimable"
    if ci[0] > 0:
        x = 100 * shares["models"][primary_arm]["share_of_reducible_removed"]
        return (
            f"A richer model removes {x:.1f}% of avoidable error, against "
            f"{REGISTERED_LEAGUE_AWARE_SHARE_PCT}% for the league-aware model."
        )
    if ci[1] >= 0:
        return f"A flexible model with {n_features} features does no better than one number per league."
    return (
        "no E16 sentence licensed: the flexible model is less accurate than the "
        "league-aware model (interval below zero)"
    )


def licensed_translation(record: dict) -> str:
    ci = record["player_club_season"]["ci95"]
    if ci is not None and ci[0] <= 0 <= ci[1]:
        return E2_SENTENCE[:-1] + ", and a flexible model."
    return "no extension of the E2 sentence is licensed (the translation increment interval excludes zero)"


# ------------------------------------------------------------------ run --
def run(input_dir: Path, raw_root: Path, bio_path: Path, out: Path, *, n_boot=N_BOOT):
    root = Path.cwd()
    v9, v10_summary = common.load_references(root)
    anchor, features, folds = common.anchor_rows(root, input_dir)
    diffs = common.g0_differences(anchor, v9, v10_summary)
    g0_control = negative_control(common.assert_g0, diffs, tolerance=-1.0)
    common.assert_g0(diffs)
    keys = common.target_keys(v10_summary)
    if len(anchor) != EXPECTED_TARGETS:
        raise GateFailure("anchor is not the 674 v10 targets")

    common.check_sha(root / ROBUSTNESS_SUMMARY, ROBUSTNESS_SUMMARY_SHA)
    e6 = json.loads((root / ROBUSTNESS_SUMMARY).read_text())["e6"]
    floor = float(e6["outcomes"]["O1"]["floor_normal"])

    _, cohort = common.load_pool(input_dir)
    bio = pd.read_parquet(bio_path)
    ages = robust.ages(cohort, raw_root, bio)

    seasons = sorted(int(s) for s in cohort.season_src.dropna().unique())
    if max(seasons) > LAST_SOURCE_SEASON:
        raise GateFailure("a cohort source season is later than 2024")
    leagues = sorted(cohort.league_src.unique())
    games, stats, files = load_proballers(raw_root, leagues, seasons)
    links = link_team_names(games, stats)
    records = team_records(games)
    shares = club_win_share(cohort, links, records)
    g16 = coverage(shares, keys)
    broken = coverage(
        club_win_share(cohort, links, records, suffix=BROKEN_SUFFIX), keys
    )
    g16_control = negative_control(assert_g16, broken["share"], threshold=1.0)
    try:
        assert_g16(g16["share"])
        g16_status = "passed"
    except GateFailure:
        g16_status = "failed"
    exact = cohort[[*KEY, "league_src", "season_src", "club_src"]].merge(
        records.rename(
            columns={
                "games_name": "club_src",
                "season": "season_src",
                "league": "league_src",
            }
        ),
        on=["league_src", "season_src", "club_src"],
        how="left",
    )
    exact_cov = coverage(exact, keys)["share"]

    table = feature_table(features, ages, shares)
    arms = [a for a, (_, _, club) in ARMS.items() if g16_status == "passed" or not club]
    reproduction = history_reproduction(table, anchor)
    if not reproduction <= 1e-9:
        raise GateFailure(
            f"ridge fitter does not reproduce history_only ({reproduction})"
        )
    predictions, training = walk_forward(table, arms)
    first = str(folds[0]["season"])
    dropped = {**training, first: {"train_keys": training[first]["train_keys"][1:]}}
    training_control = negative_control(assert_training_rows, dropped, folds)
    assert_training_rows(training, folds)

    rows = keys.merge(anchor, on=KEY, how="left", validate="1:1").merge(
        predictions, on=KEY, how="left", validate="1:1"
    )
    rows = rows.merge(
        table[[*KEY, "age_c26", "club_win_share"]], on=KEY, validate="1:1"
    )
    if not np.isfinite(rows[[*arms, *REFERENCE_ARMS, OUTCOME]].to_numpy(float)).all():
        raise GateFailure("an E16 target forecast is unscorable")

    sd = float(rows[OUTCOME].std(ddof=1))
    spec = CONTRASTS if g16_status == "passed" else CONTRASTS_NO_CLUB
    contrasts = {
        name: {**robust.contrast_record(rows, left, right, sd), "role": role}
        for name, (left, right, role) in spec.items()
    }
    primary_arm = spec["primary_offsets10_vs_gbm"][1]
    models = [*REFERENCE_ARMS, *arms]
    share = reducible_shares(rows, models, floor, n_boot=n_boot)
    last = str(common.ANCHOR_SEASONS[-1])
    n_features = len(training[last]["arms"][primary_arm]["features"])

    from sklearn import __version__ as sklearn_version

    summary = {
        "analysis": "E16",
        "exploratory": True,
        "amendment": str(AMENDMENT.relative_to(ROOT)),
        "amendment_commit": AMENDMENT_COMMIT,
        "amendment_sha256": sha256_file(AMENDMENT),
        "protocol_commit": common.PROTOCOL_COMMIT,
        "input_sha256": {
            "pairs": common.PAIRS_SHA["official_corrected"],
            "cohort": common.COHORT_SHA,
            "robustness_summary": ROBUSTNESS_SUMMARY_SHA,
            "player_bio": sha256_file(bio_path),
        },
        "proballers_files": len(files),
        "proballers_seasons": seasons,
        "sklearn_version": sklearn_version,
        "hgb_params": HGB_PARAMS,
        "ridge_penalty": RIDGE_PENALTY,
        "ridge_unpenalised": ["intercept", *HISTORY_TERMS],
        "n_boot": n_boot,
        "seed": SEED,
        "n_targets": len(rows),
        "outcome_sd": sd,
        "labels": {a: LABELS[a] for a in models},
        "arms_run": arms,
        "primary_arm": primary_arm,
        "n_features_primary": n_features,
        "n_features_primary_by_season": {
            s: len(t["arms"][primary_arm]["features"]) for s, t in training.items()
        },
        "features_by_arm_last_season": {
            a: training[last]["arms"][a]["features"] for a in arms
        },
        "training": {
            s: {
                "train_rows": t["train_rows"],
                "test_rows": t["test_rows"],
                "source_categories": t["source_categories"],
                "gbm_iterations": {
                    a: d["n_iter"] for a, d in t["arms"].items() if "n_iter" in d
                },
            }
            for s, t in training.items()
        },
        "gates": {
            "G0": {
                "status": "passed",
                "max_difference": max(diffs.values()),
                "tolerance": common.G0_TOLERANCE,
                "negative_control": g0_control,
            },
            "G16": {
                "status": g16_status,
                "threshold": G16_THRESHOLD,
                "targets": g16["targets"],
                "joined": g16["joined"],
                "coverage": g16["share"],
                "unjoined": g16["unjoined"],
                "negative_control": g16_control,
                "negative_control_coverage": broken["share"],
                "exact_name_join_coverage_printed": exact_cov,
                "cohort_rows_joined": int(np.isfinite(shares.club_win_share).sum()),
                "cohort_rows": len(shares),
                "min_link_agreement_on_targets": float(
                    keys.merge(shares, on=KEY).agreement.min()
                ),
                "ambiguous_links_dropped": int(links.ambiguous.sum()),
                "tied_games_excluded": int(games.home_score.eq(games.away_score).sum()),
            },
            "training_rows_identity": {
                "status": "passed",
                "negative_control": training_control,
            },
            "ridge_history_reproduction": {
                "status": "passed",
                "max_difference": reproduction,
                "tolerance": 1e-9,
            },
        },
        "metrics": {a: robust.arm_metrics(rows, a) for a in models},
        "contrasts": contrasts,
        "reducible": share,
        "licensed": {
            "primary": licensed_primary(
                contrasts["primary_offsets10_vs_gbm"], share, n_features, primary_arm
            ),
            "translation": licensed_translation(contrasts["gbm_translation_increment"]),
            "club_quality": "no licence registered: the club-quality increment is printed only",
            "league_aware_share_pct_measured": 100
            * share["models"][OFFSETS]["share_of_reducible_removed"],
            "league_aware_share_pct_registered": REGISTERED_LEAGUE_AWARE_SHARE_PCT,
        },
    }
    if g16_status != "passed":
        summary["licensed"]["club_quality"] = (
            "not adjudicable: G16 failed (coverage printed); models ran without club win share"
        )

    out.mkdir(parents=True, exist_ok=False)
    keep = [*KEY, "league_dest", "league_src", "cluster", OUTCOME, *REFERENCE_ARMS]
    rows[[*keep, *arms, "age_c26", "club_win_share"]].to_csv(
        out / "e16_forecasts.csv", index=False
    )
    shares.to_csv(out / "e16_club_win_share.csv", index=False)
    pd.DataFrame(
        [
            {
                "model": a,
                "label": LABELS[a],
                **summary["metrics"][a],
                "share_of_reducible_removed": share["models"][a][
                    "share_of_reducible_removed"
                ],
                "share_ci_low": share["models"][a]["ci95_percentile"][0],
                "share_ci_high": share["models"][a]["ci95_percentile"][1],
            }
            for a in models
        ]
    ).to_csv(out / "e16_models.csv", index=False)
    (out / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True, default=float) + "\n"
    )
    return summary


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument(
        "--raw-root",
        type=Path,
        required=True,
        help="a data/raw directory with proballers, _inactive_leagues/proballers and {euroleague,eurocup}/<season>/boxscores",
    )
    parser.add_argument("--bio", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--n-boot", type=int, default=N_BOOT)
    args = parser.parse_args(argv)
    summary = run(args.input_dir, args.raw_root, args.bio, args.out, n_boot=args.n_boot)
    print(summary["licensed"]["primary"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
