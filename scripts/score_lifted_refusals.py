"""Study C — refusals as a finding: would the refused have carried larger errors?

Pre-registered in ``docs/research/translation-application-studies-preregistration-
2026-09-06.md``. For the two refusal codes that decline a *scorable* row on a
data-quality rule -- R5 (source season below the 8-game floor) and R9 (source
league-season under 90% complete) -- predict the player anyway with the SAME
basis the rehearsal used, and score him at 2026-06-30 against the realised
outcome, beside the accepted set.

The lock's builder is untouched: this script imports its functions, re-runs the
classification with a lifting rule of its own, and asserts that its accepted
set is identical to the rehearsal's committed prediction set before scoring
anything. R5 is lifted only at >= 3 source games (a 1-2 game rate is a
degenerate measurement, not a lifted refusal). R1, R2, R3, R4, R7 are never
lifted and are counted.

    uv run python scripts/score_lifted_refusals.py --signings S --predictions P \\
        --outcomes O --interval-params I --out-dir OUT
"""

from __future__ import annotations

import argparse
import datetime
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

import scripts.build_league_factors as blf  # noqa: E402
import scripts.build_translation_predictions as btp  # noqa: E402
import scripts.evaluate_translation_predictions as ev  # noqa: E402
import scripts.validate_translation_holdout as vh  # noqa: E402
import scripts.validate_translation_walkforward as wf  # noqa: E402
from src.data.translation_predictions import (  # noqa: E402
    COMBINED_ARM,
    MIN_SEASONS_FOR_COMBINED_ARM,
    PER_LEAGUE_ONLY,
    RefusedCandidate,
    ScorableCandidate,
    build_prediction_set,
    classify_refusal,
)

SEED = 0
N_BOOT = 2000
LIFTABLE = ("R5", "R9")
R5_MIN_GAMES = 3
MIN_DEST_GAMES = 8
FIRST_ROUND_MAX = 3
_DEFAULT_OUT = REPO / "docs" / "research" / "artifacts" / "application-studies-2026-09"


def lifted_code(code: str | None, source_games: int | None) -> str | None:
    """The code that stands after lifting: R9 always, R5 only at >= 3 games.

    Returns ``None`` when the row becomes scorable. Every other code stands.
    """
    if code == "R9":
        return None
    if code == "R5" and source_games is not None and source_games >= R5_MIN_GAMES:
        return None
    return code


def two_sample_cluster_bootstrap(
    y_a, p_a, c_a, y_b, p_b, c_b, *, n_boot: int = N_BOOT, seed: int = SEED
) -> tuple[float, float, float]:
    """MAE(b) - MAE(a): each group's clusters resampled independently."""

    def mae_draw(rng, y, p, c):
        y, p, c = np.asarray(y, float), np.asarray(p, float), np.asarray(c)
        keys = np.unique(c)
        members = {k: np.flatnonzero(c == k) for k in keys}
        pick = np.concatenate([members[k] for k in rng.choice(keys, len(keys))])
        return float(np.abs(y[pick] - p[pick]).mean())

    rng = np.random.default_rng(seed)
    d = np.array(
        [
            mae_draw(rng, y_b, p_b, c_b) - mae_draw(rng, y_a, p_a, c_a)
            for _ in range(n_boot)
        ]
    )
    point = float(np.abs(np.asarray(y_b) - np.asarray(p_b)).mean()) - float(
        np.abs(np.asarray(y_a) - np.asarray(p_a)).mean()
    )
    return point, float(np.percentile(d, 2.5)), float(np.percentile(d, 97.5))


def score_group(preds: list[dict], outcomes: dict, label: str) -> dict:
    """Scored rows for one group: MAE, R8 censor count, conformal coverage."""
    scored, censored = [], 0
    for p in preds:
        o = outcomes.get(p["person_code"])
        if o is None or o["games"] < MIN_DEST_GAMES:
            censored += 1
            continue
        scored.append((p, o))
    if not scored:
        return {"label": label, "n_scored": 0, "n_censored_R8": censored}
    y = np.array([o["pir_per36"] for _, o in scored], float)
    m = np.array([p["projection"] for p, _ in scored], float)
    b0 = np.array([p["baseline_b0"] for p, _ in scored], float)
    b1c = np.array([p["baseline_b1c"] for p, _ in scored], float)
    cov = np.mean(
        [(p["interval_low"] <= o["pir_per36"] <= p["interval_high"]) for p, o in scored]
    )
    return {
        "label": label,
        "n_scored": int(len(scored)),
        "n_censored_R8": censored,
        "mae_model": float(np.abs(y - m).mean()),
        "mae_b0": float(np.abs(y - b0).mean()),
        "mae_b1c": float(np.abs(y - b1c).mean()),
        "coverage": float(cov),
        "_y": y.tolist(),
        "_m": m.tolist(),
        "_c": [o["club_season"] for _, o in scored],
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--signings", type=Path, required=True)
    ap.add_argument(
        "--predictions", type=Path, required=True, help="the rehearsal's committed set"
    )
    ap.add_argument(
        "--outcomes", type=Path, required=True, help="end-of-season realised outcomes"
    )
    ap.add_argument("--interval-params", type=Path, required=True)
    ap.add_argument("--season", type=int, default=2025)
    ap.add_argument("--out-dir", type=Path, default=_DEFAULT_OUT)
    ap.add_argument(
        "--continental-source",
        choices=blf.CONTINENTAL_SOURCES,
        default=blf.DEFAULT_CONTINENTAL_SOURCE,
    )
    args = ap.parse_args(argv)
    args.out_dir.mkdir(parents=True, exist_ok=True)

    signings = json.loads(args.signings.read_text())
    committed = json.loads(args.predictions.read_text())
    outcomes_raw = json.loads(args.outcomes.read_text())

    games, pairs = vh.load_corpus(args.continental_source)
    switch, _ = vh.build_switchers(games)
    cohorts = switch[switch.was_cont == 0]
    cohorts = cohorts[~cohorts.league_src.isin(vh.EXCLUDED_SOURCE)]
    cohorts = cohorts[cohorts.pir_per36_src > 0]
    fold = wf.one_season(pairs, cohorts, args.season)
    src = btp.source_season_rows(games, args.season).set_index("player_name")
    missing_clubs = {
        c
        for block in signings["competitions"].values()
        for c in block.get("clubs_with_empty_roster", [])
    }
    comp = btp.completeness_lookup(btp.source_season_completeness(games))

    accepted_rows, lifted_rows, refused, counts = [], [], [], {}
    for a in signings["arrivals"]:
        key = btp.pairing_key(a["name"])
        s = src.loc[key] if key in src.index else None
        source = None if s is None else comp.get((str(s.league_src), int(s.season_src)))
        games_src = 0 if s is None else int(s.games_src)
        code = classify_refusal(
            kind=a["kind"],
            prior_league=a.get("prior_league"),
            source_games=games_src,
            source_rate=None if s is None else float(s.pir_per36_src),
            roster_missing=a["club_code"] in missing_clubs,
            source_completeness=None if source is None else source.completeness,
        )
        counts[code or "scorable"] = counts.get(code or "scorable", 0) + 1
        after = lifted_code(code, games_src)
        row = None if s is None else {**a, **s.to_dict(), "source_row": source}
        if code is None:
            accepted_rows.append(row)
        elif after is None and row is not None:
            lifted_rows.append({**row, "lifted_from": code})
        else:
            refused.append(
                RefusedCandidate(
                    person_code=a["person_code"],
                    name=a["name"],
                    competition=a["competition"],
                    club_code=a["club_code"],
                    code=code,
                    source=source,
                )
            )

    def project(rows: list[dict]) -> list[ScorableCandidate]:
        if not rows:
            return []
        cand = pd.DataFrame(rows)
        cand["league_dest"] = cand.competition
        mult = fold["multiplier_fn"](cand)
        per_league = cand.pir_per36_src.to_numpy(dtype=float) * mult * fold["k_lag"]
        combined, rtm_only = btp._rtm_predictions(fold, cand)
        use_combined = (
            cand.n_domestic_seasons.to_numpy() >= MIN_SEASONS_FOR_COMBINED_ARM
        )
        projection = np.where(use_combined, combined, per_league)
        reliable = btp.reliable_lookup(fold)
        return [
            ScorableCandidate(
                person_code=r.person_code,
                name=r.name,
                competition=r.competition,
                club_code=r.club_code,
                origin_league=r.league_src,
                destination=r.league_dest,
                pir_per36_src=float(r.pir_per36_src),
                prior_mean_pir36=(
                    None if pd.isna(r.prior_mean_pir36) else float(r.prior_mean_pir36)
                ),
                factor=float(mult[i]),
                factor_reliable=bool(
                    reliable.get((r.league_src, r.league_dest), False)
                ),
                scoring_method=COMBINED_ARM if use_combined[i] else PER_LEAGUE_ONLY,
                projection=float(projection[i]),
                baseline_b1c=float(rtm_only[i]),
                source=r.source_row,
            )
            for i, r in enumerate(cand.itertuples())
        ]

    interval = btp.interval_spec(args.interval_params)
    built_at = datetime.date.today().isoformat()

    def payload_for(scorable):
        return build_prediction_set(
            scorable,
            refused,
            season=args.season,
            collected_at=signings["collected_at"],
            built_at=built_at,
            k_lag=float(fold["k_lag"]),
            source_collection=args.signings.name,
            status="draft",
            continental_source=args.continental_source,
            interval=interval,
        )

    accepted = payload_for(project(accepted_rows))["predictions"]
    # the identity check: the accepted set IS the rehearsal's committed set
    mine = {p["person_code"]: p["projection"] for p in accepted}
    theirs = {p["person_code"]: p["projection"] for p in committed["predictions"]}
    assert set(mine) == set(theirs), (
        f"accepted set differs from the committed set: {len(set(mine) ^ set(theirs))} codes"  # noqa: E501
    )
    max_gap = max(abs(mine[c] - theirs[c]) for c in mine)
    assert max_gap < 1e-6, (
        f"accepted projections differ from the committed set by {max_gap}"
    )

    lifted_all = project(lifted_rows)
    lifted_payload = payload_for(lifted_all)["predictions"] if lifted_all else []
    lifted_from = {r["person_code"]: r["lifted_from"] for r in lifted_rows}
    for p in lifted_payload:
        p["lifted_from"] = lifted_from[p["person_code"]]

    full = ev.load_outcomes(outcomes_raw)
    acc_pop, pop_note = ev.restrict_population(accepted, full, FIRST_ROUND_MAX)
    lifted_pop, _ = ev.restrict_population(lifted_payload, full, FIRST_ROUND_MAX)

    groups = {"accepted": score_group(acc_pop, full, "accepted")}
    for code in LIFTABLE:
        sub = [p for p in lifted_pop if p["lifted_from"] == code]
        groups[f"lifted_{code}"] = score_group(sub, full, f"lifted_{code}")
    groups["lifted_all"] = score_group(lifted_pop, full, "lifted_all")

    contrasts = {}
    a = groups["accepted"]
    for name, g in groups.items():
        if name == "accepted" or g["n_scored"] < 5:
            continue
        pt, lo, hi = two_sample_cluster_bootstrap(
            a["_y"], a["_m"], a["_c"], g["_y"], g["_m"], g["_c"]
        )
        contrasts[name] = {
            "mae_lifted_minus_accepted": pt,
            "ci95": [lo, hi],
            "excludes_zero": lo > 0 or hi < 0,
            "read": (
                "the refusal discriminates: lifted rows carry larger error"
                if lo > 0
                else "not separable: the code refuses coverage for nothing this test can measure"  # noqa: E501
            ),
        }
    for g in groups.values():
        for k in ("_y", "_m", "_c"):
            g.pop(k, None)

    payload = {
        "study": "C_lifted_refusals",
        "preregistration": "translation-application-studies-preregistration-2026-09-06.md",  # noqa: E501
        "season": args.season,
        "committed_set": args.predictions.name,
        "identity_check": {"n_accepted": len(accepted), "max_projection_gap": max_gap},
        "refusal_counts_before_lifting": counts,
        "lifting_rule": {"R9": "always", "R5": f"at >= {R5_MIN_GAMES} source games"},
        "n_lifted": {
            c: sum(1 for r in lifted_rows if r["lifted_from"] == c) for c in LIFTABLE
        },
        "population_rule": pop_note,
        "groups": groups,
        "contrasts": contrasts,
    }
    (args.out_dir / "lifted_refusals.json").write_text(
        json.dumps(payload, indent=1, default=float)
    )
    for name, g in groups.items():
        print(
            f"[C] {name}: scored {g.get('n_scored')} censored {g.get('n_censored_R8')} "
            f"MAE {g.get('mae_model', float('nan')):.3f} coverage {g.get('coverage', float('nan')):.3f}"  # noqa: E501
        )
    for name, c in contrasts.items():
        print(
            f"[C] {name} - accepted: {c['mae_lifted_minus_accepted']:+.3f} CI {c['ci95']} -> {c['read']}"  # noqa: E501
        )
    print(f"[done] wrote lifted_refusals.json to {args.out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
