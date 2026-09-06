"""Study A — is the pairing independent of form?

Pre-registered in ``docs/research/translation-application-studies-preregistration-
2026-09-06.md``. The abstract says the same club fields the same player at two
levels *by schedule*; the club's entry is by schedule, a player's minutes in
each competition are a coach's choice, and the >=8-games floor on both sides
selects on those minutes. This script asks whether a player's FORM -- his
source-season rate relative to his own prior -- predicts whether he is paired.

Population: every domestic player-season (>=8 games) at a club that fielded at
least one paired player that season. Exposure: reached the floor on a
continental side (the estimator's `build_pairs` rule). Read: Cohen's d of the
deviation from own prior, paired vs unpaired, with a cluster bootstrap on the
domestic club-season and a within-cluster permutation null; the same d on the
prior rate itself (level) is the positive control -- selection on ability is
expected and is what Proposition 4(i) cancels.

Bar (pre-registered): |d| < 0.10 with the 95% CI inside (-0.20, +0.20) reads
"independent of form at this resolution"; otherwise d IS the selection size.

    uv run python scripts/measure_pairing_vs_form.py --out-dir OUT
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

import scripts.build_league_factors as blf  # noqa: E402
import scripts.instantiate_translation_propositions as itp  # noqa: E402
import scripts.validate_translation_holdout as vh  # noqa: E402

SEED = 0
N_BOOT = 2000
N_PERM = 200
MIN_DOMESTIC_GAMES = 8
FLOORS = (5, 8, 15)  # continental games needed to count as paired; 8 is primary
D_BAR = 0.10
D_CI_BAND = 0.20
_DEFAULT_OUT = REPO / "docs" / "research" / "artifacts" / "application-studies-2026-09"


# ------------------------------------------------------------------ tables --
def stint_table(games: pd.DataFrame) -> pd.DataFrame:
    """One row per (player, season, league): games, minutes, EFF, modal club."""
    agg = (
        games[games.minutes > 0]
        .groupby(["player_name", "season", "league"])
        .agg(
            games=("game_id", "nunique"),
            minutes=("minutes", "sum"),
            pir=("pir", "sum"),
            club=("team", lambda s: s.value_counts().idxmax()),
        )
        .reset_index()
    )
    agg["pir_per36"] = 36 * agg.pir / agg.minutes
    return agg


def _largest_stint(df: pd.DataFrame) -> pd.DataFrame:
    return df.sort_values("minutes", ascending=False).drop_duplicates(
        ["player_name", "season"]
    )


def domestic_sides(agg: pd.DataFrame, *, min_games: int = MIN_DOMESTIC_GAMES):
    d = agg[
        ~agg.league.isin(blf.CONTINENTAL)
        & ~agg.league.isin(blf.NOT_A_SOURCE)
        & (agg.games >= min_games)
    ]
    return _largest_stint(d)


def continental_sides(agg: pd.DataFrame, *, floor: int, destinations) -> pd.DataFrame:
    c = agg[agg.league.isin(list(destinations)) & (agg.games >= floor)]
    return _largest_stint(c)


def population(dom: pd.DataFrame, cont: pd.DataFrame) -> pd.DataFrame:
    """Domestic player-seasons at dual-competition clubs, flagged `paired`.

    A club is dual-competition in a season if at least one of ITS domestic
    players reached the continental floor that season. A player at a
    domestic-only club cannot be paired, so he is not in the population: the
    comparison is form within the same club-season, never club membership.
    """
    key = ["player_name", "season"]
    paired_keys = cont[key].drop_duplicates().assign(paired=1)
    d = dom.merge(paired_keys, on=key, how="left")
    d["paired"] = d.paired.fillna(0).astype(int)
    d["cluster"] = d.season.astype(str) + "|" + d.league + "|" + d.club
    dual = set(d.loc[d.paired == 1, "cluster"])
    return d[d.cluster.isin(dual)].reset_index(drop=True)


def with_prior(pop: pd.DataFrame, prior: pd.DataFrame) -> pd.DataFrame:
    p = pop.merge(prior, on=["player_name", "season"], how="left")
    p = p[p.prior_rate.notna()].copy()
    p["deviation"] = p.pir_per36 - p.prior_rate
    return p.reset_index(drop=True)


# ------------------------------------------------------------------- stats --
def cohens_d(x: np.ndarray, g: np.ndarray) -> float:
    """(mean where g==1 - mean where g==0) / pooled SD."""
    x, g = np.asarray(x, float), np.asarray(g).astype(bool)
    a, b = x[g], x[~g]
    if len(a) < 2 or len(b) < 2:
        return float("nan")
    s2 = ((len(a) - 1) * a.var(ddof=1) + (len(b) - 1) * b.var(ddof=1)) / (
        len(a) + len(b) - 2
    )
    return float((a.mean() - b.mean()) / np.sqrt(s2)) if s2 > 0 else float("nan")


def cluster_bootstrap_d(
    df: pd.DataFrame, col: str, *, n_boot: int = N_BOOT, seed: int = SEED
) -> tuple[float, float]:
    rng = np.random.default_rng(seed)
    clusters = df.cluster.to_numpy()
    keys = np.unique(clusters)
    members = {k: np.flatnonzero(clusters == k) for k in keys}
    x, g = df[col].to_numpy(float), df.paired.to_numpy()
    draws = np.empty(n_boot)
    for i in range(n_boot):
        pick = np.concatenate([members[k] for k in rng.choice(keys, len(keys))])
        draws[i] = cohens_d(x[pick], g[pick])
    return float(np.nanpercentile(draws, 2.5)), float(np.nanpercentile(draws, 97.5))


def permutation_d(
    df: pd.DataFrame, col: str, *, n_perm: int = N_PERM, seed: int = SEED
) -> np.ndarray:
    """Null: `paired` permuted WITHIN club-season, so the club mix is held."""
    rng = np.random.default_rng(seed + 1)
    x = df[col].to_numpy(float)
    g = df.paired.to_numpy().copy()
    groups = df.groupby("cluster").indices
    out = np.empty(n_perm)
    for i in range(n_perm):
        gp = g.copy()
        for idx in groups.values():
            if len(idx) > 1:
                gp[idx] = rng.permutation(gp[idx])
        out[i] = cohens_d(x, gp)
    return out


def read(d: float, ci: tuple[float, float]) -> str:
    if not np.isfinite(d):
        return "undefined"
    if abs(d) < D_BAR and -D_CI_BAND < ci[0] and ci[1] < D_CI_BAND:
        return "independent of form at this resolution (|d| < 0.10, CI inside ±0.20)"
    return "selection on form measured: d is the selection size"


def run_arm(pop: pd.DataFrame, label: str) -> dict:
    out: dict = {"arm": label, "n": int(len(pop)), "n_paired": int(pop.paired.sum())}
    out["n_clusters"] = int(pop.cluster.nunique())
    for col, name in (("deviation", "form"), ("prior_rate", "level")):
        d = cohens_d(pop[col], pop.paired)
        ci = cluster_bootstrap_d(pop, col)
        perm = permutation_d(pop, col)
        out[name] = {
            "mean_paired": float(pop.loc[pop.paired == 1, col].mean()),
            "mean_unpaired": float(pop.loc[pop.paired == 0, col].mean()),
            "cohens_d": d,
            "ci95_cluster": list(ci),
            "permutation_null_mean": float(np.nanmean(perm)),
            "permutation_null_p95_abs": float(np.nanpercentile(np.abs(perm), 95)),
            "share_of_null_draws_at_or_beyond": float(np.mean(np.abs(perm) >= abs(d))),
        }
    out["form"]["read"] = read(
        out["form"]["cohens_d"], tuple(out["form"]["ci95_cluster"])
    )
    return out


# -------------------------------------------------------------------- main --
def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out-dir", type=Path, default=_DEFAULT_OUT)
    ap.add_argument(
        "--continental-source",
        choices=blf.CONTINENTAL_SOURCES,
        default=blf.DEFAULT_CONTINENTAL_SOURCE,
    )
    args = ap.parse_args(argv)
    args.out_dir.mkdir(parents=True, exist_ok=True)

    games, pairs = vh.load_corpus(args.continental_source)
    agg = stint_table(games)
    prior = itp.prior_seasons_rate(games)
    dom = domestic_sides(agg)

    arms = []
    for floor in FLOORS:
        for dest_label, dests in (
            ("both", tuple(blf.CONTINENTAL)),
            ("euroleague_only", ("euroleague",)),
        ):
            cont = continental_sides(agg, floor=floor, destinations=dests)
            pop = with_prior(population(dom, cont), prior)
            arm = run_arm(pop, f"floor={floor}|{dest_label}")
            arm.update({"floor": floor, "destinations": dest_label})
            arm["primary"] = floor == MIN_DOMESTIC_GAMES and dest_label == "both"
            arms.append(arm)
            print(
                f"[A] {arm['arm']}: n={arm['n']} paired={arm['n_paired']} "
                f"d_form={arm['form']['cohens_d']:+.3f} "
                f"CI [{arm['form']['ci95_cluster'][0]:+.3f}, "
                f"{arm['form']['ci95_cluster'][1]:+.3f}] "
                f"d_level={arm['level']['cohens_d']:+.3f} -> {arm['form']['read']}"
            )

    primary = next(a for a in arms if a["primary"])
    # the primary population must reproduce the estimator's pair count at
    # the same floor (up to the prior-rate filter, which drops debutants)
    n_pairs_est = int(len(pairs))
    payload = {
        "study": "A_pairing_vs_form",
        "preregistration": "translation-application-studies-preregistration-2026-09-06.md",  # noqa: E501
        "continental_source": args.continental_source,
        "bar": {"d_abs_lt": D_BAR, "ci_within": D_CI_BAND},
        "n_pairs_estimator": n_pairs_est,
        "primary": primary,
        "arms": arms,
        "verdict": primary["form"]["read"],
    }
    (args.out_dir / "pairing_vs_form.json").write_text(json.dumps(payload, indent=1))
    print(f"[done] wrote pairing_vs_form.json to {args.out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
