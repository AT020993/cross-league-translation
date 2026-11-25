#!/usr/bin/env python3
"""Pick the SSAC27 full-paper player vignettes by a rule fixed before any error is read.

Rule (stated in the paper): for each tier of the league table (the e9 EuroLeague tiers
in ``exchange_rate_acb16.csv``), take the destination-season-2025 (2025-26) EuroLeague
arrival with the most continental minutes. The domestic line comes from the public v10
cohort; the three forecasts come from the committed E16 walk-forward forecast file,
which carries the registered v10 arms. Nothing is chosen by forecast error.

Outputs (under --out): vignettes.csv, summary.json.
"""

from __future__ import annotations

if __name__ == "__main__":
    import sys as _sys
    from pathlib import Path as _Path

    _sys.path.insert(0, str(_Path(__file__).resolve().parents[1]))
    from src.research.execution import enter as _enter

    _enter(__file__)

import argparse
import hashlib
import json
from pathlib import Path

import pandas as pd

SEASON = 2025
DESTINATION = "euroleague"
KEY = ["player_name", "season_dest", "league_dest", "league_src"]
ARMS = ("history_only", "scheduled_history", "source_ridge_10")
#: Destination club codes of the EuroLeague API, spelled out for the reader.
CLUB_NAMES = {"PAM": "Valencia Basket", "ZAL": "Zalgiris Kaunas"}
RULE = (
    "for each tier of the league table (e9 EuroLeague tiers), the 2025-26 EuroLeague "
    "arrival with the most continental minutes; ties broken by player name"
)


def sha(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def pick(
    cohort: pd.DataFrame, forecasts: pd.DataFrame, tiers: pd.DataFrame
) -> pd.DataFrame:
    """Apply the rule. Raises if a target has no cohort row or a tier has no arrival."""
    rows = forecasts.merge(cohort, on=KEY, how="left", validate="1:1", indicator=True)
    if (rows["_merge"] != "both").any():
        raise ValueError("a forecast target has no cohort row")
    tier = (
        tiers.loc[tiers.destination == DESTINATION]
        .set_index("source_league")["e9_tier"]
        .astype(int)
    )
    rows = rows.loc[
        (rows.season_dest == SEASON) & (rows.league_dest == DESTINATION)
    ].copy()
    rows["tier"] = rows.league_src.map(tier)
    if rows.tier.isna().any():
        raise ValueError("an arrival's source league has no tier")
    rows = rows.sort_values(
        ["tier", "minutes_dest", "player_name"], ascending=[True, False, True]
    )
    chosen = rows.groupby("tier", sort=True).head(1)
    missing = sorted(set(tier.unique()) - set(chosen.tier))
    if missing:
        raise ValueError(f"no 2025-26 EuroLeague arrival in tier(s) {missing}")
    out = pd.DataFrame(
        {
            "tier": chosen.tier.astype(int),
            "player": chosen.player_name.str.title(),
            "league_src": chosen.league_src,
            "club_src": chosen.club_src,
            "club_dest": chosen.club_dest.map(lambda c: CLUB_NAMES.get(c, c)),
            "season_src": chosen.season_src.astype(int),
            "season_dest": chosen.season_dest.astype(int),
            "games_src": chosen.games_src.astype(int),
            "min_per_game_src": chosen.minutes_src / chosen.games_src,
            "eff36_src": chosen.pir_per36_src,
            "history_eff36": chosen.prior_mean_pir36,
            "above_own_history": chosen.above_own_prior.astype(bool),
            "games_dest": chosen.games_dest.astype(int),
            "min_per_game_dest": chosen.minutes_dest / chosen.games_dest,
            "minutes_dest": chosen.minutes_dest,
            "actual_eff36": chosen.pir_per36_dest,
            **{f"forecast_{arm}": chosen[arm] for arm in ARMS},
            "candidates_in_tier": chosen.tier.map(rows.groupby("tier").size()),
        }
    )
    return out.reset_index(drop=True)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--cohort", type=Path, required=True)
    parser.add_argument("--forecasts", type=Path, required=True)
    parser.add_argument("--tiers", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    cohort = pd.read_parquet(args.cohort)
    forecasts = pd.read_csv(args.forecasts)[[*KEY, *ARMS]]
    table = pick(cohort, forecasts, pd.read_csv(args.tiers))
    args.out.mkdir(parents=True, exist_ok=True)
    table.to_csv(args.out / "vignettes.csv", index=False)
    summary = {
        "rule": RULE,
        "season_dest": SEASON,
        "destination": DESTINATION,
        "arms": list(ARMS),
        "rows": len(table),
        "inputs": {
            "cohort": sha(args.cohort),
            "forecasts": sha(args.forecasts),
            "tiers": sha(args.tiers),
        },
        "outputs": {"vignettes.csv": sha(args.out / "vignettes.csv")},
    }
    (args.out / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n"
    )
    print(json.dumps({"rows": len(table), "players": table.player.tolist()}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
