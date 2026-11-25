# ruff: noqa: E402
"""Registered immutable official correction and complete input reconstruction.

Threats: source drift, partial decisions, two-point schema, lost identities,
season leakage, name collisions and silent row loss. Raw files never change.
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
import io
import json
from pathlib import Path
import sys
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from scripts import adjudicate_sloan_acb_sources as acb  # noqa: E402
from scripts import sloan_source_adjudication as old  # noqa: E402
from scripts import revalidate_sloan_sources as previous  # noqa: E402
from scripts import build_league_factors as blf  # noqa: E402
from scripts import validate_translation_holdout as holdout  # noqa: E402
from scripts import sloan_revision_analysis as revision  # noqa: E402
from src.data.corpus import euroleague_api as api  # noqa: E402

PROTOCOL = (
    ROOT / "docs/research/sloan-evidence-completion-preregistration-2026-09-17.md"
)
KEY = ["game_id", "player_name", "league", "team", "season"]


def eff(frame):
    return (
        frame.points
        + frame.rebounds
        + frame.assists
        + frame.steals
        + frame.blocks
        - (frame.fg_attempted - frame.fg_made)
        - (frame.fg3_attempted - frame.fg3_made)
        - (frame.ft_attempted - frame.ft_made)
        - frame.turnovers
    )


def apply_decisions(frame, decisions, diagnosis):
    out = frame.copy()
    expected = {
        (r["game_id"], r["player_name"], r["team"], r["field"])
        for r in diagnosis["field_disagreements"]
    }
    seen, ledger, touched = [], [], []
    out["official_person_id"] = pd.Series(None, index=out.index, dtype="object")
    out["identity_status"] = "NAME_ONLY_UNVERIFIED"
    for decision in decisions:
        key = tuple(decision[k] for k in ("game_id", "player_name", "team", "field"))
        if key not in expected or key in seen:
            raise ValueError("unexpected or duplicate correction key")
        seen.append(key)
        pending = decision.get("status") == "IDENTITY_REVIEW_REQUIRED"
        if not pending and (
            decision.get("identity_status")
            not in ("EXACT_OFFICIAL_NAME", "VERIFIED_PROVIDER_ID_DOB")
            or decision.get("status")
            not in ("RESOLVED", "RESOLVED_NEITHER", "REPRESENTATION_ONLY")
        ):
            raise ValueError("unresolved correction identity or value")
        field, value = decision["field"], decision.get("official_value")
        if field not in old.REQUIRED_STATS or (
            not pending and (value is None or not np.isfinite(value))
        ):
            raise ValueError("unsupported or nonfinite official correction")
        saved = decision["saved_values"]
        seasons = frozenset(int(v["season"]) for v in saved)
        if len(seasons) != 1:
            raise ValueError("correction spans seasons")
        season = next(iter(seasons))
        mask = (
            out.game_id.astype(str).eq(decision["game_id"])
            & out.player_name.eq(decision["player_name"])
            & out.team.eq(decision["team"])
            & out.league.eq("spain-acb")
            & out.season.eq(season)
        )
        selected = out.loc[mask]
        if len(selected) != len(saved):
            raise ValueError("correction source rows missing or duplicated")
        for s in saved:
            rows = selected.loc[
                selected._source_file.eq(s["_source_file"])
                & selected._priority.eq(s["_priority"])
            ]
            if len(rows) != 1 or not np.isclose(
                float(rows[field].iloc[0]), float(s["value"]), atol=1e-12, rtol=0
            ):
                raise ValueError("saved field value/source mismatch")
        if pending:
            out.loc[mask, "identity_status"] = "UNRESOLVED_ALIAS_QUARANTINE"
            continue
        prior = out.loc[mask, field].copy()
        out.loc[mask, field] = value
        out.loc[mask, "official_person_id"] = "acb:" + decision["official_id"]
        out.loc[mask, "identity_status"] = "OFFICIAL_FIXTURE_ONLY"
        touched.extend(out.index[mask].tolist())
        for idx, before in prior.items():
            ledger.append(
                {
                    **out.loc[idx, KEY].to_dict(),
                    "raw_row_id": int(out.loc[idx, "_raw_row_id"]),
                    "field": field,
                    "before": float(before),
                    "after": float(value),
                    "changed": bool(float(before) != float(value)),
                    "official_person_id": "acb:" + decision["official_id"],
                    "decision_status": decision["status"],
                }
            )
    if frozenset(seen) != expected:
        raise ValueError("missing frozen correction decisions")
    idx = sorted(frozenset(touched))
    values = eff(out.loc[idx])
    if not np.allclose(values, out.loc[idx, "pir"], atol=1e-12, rtol=0):
        raise ValueError("corrected EFF does not reconcile to component counts")
    out.loc[idx, "pir"] = values
    if not np.array_equal(
        (
            2 * out.loc[idx, "fg_made"]
            + 3 * out.loc[idx, "fg3_made"]
            + out.loc[idx, "ft_made"]
        ).to_numpy(),
        out.loc[idx, "points"].to_numpy(),
    ):
        raise ValueError("corrected points do not reconcile")
    if not np.array_equal(
        (
            out.loc[idx, "offensive_rebounds"] + out.loc[idx, "defensive_rebounds"]
        ).to_numpy(),
        out.loc[idx, "rebounds"].to_numpy(),
    ):
        raise ValueError("corrected rebounds do not reconcile")
    return out, ledger


def collision_scopes(diagnosis, decisions=()):
    collisions = {
        (r["normalized_name"], int(row["season"]))
        for r in diagnosis["identity_collisions"]
        for row in r["rows"]
    }
    pending = {
        (blf.pairing_key(r["player_name"]), int(v["season"]))
        for r in decisions
        if r["status"] == "IDENTITY_REVIEW_REQUIRED"
        for v in r["saved_values"]
    }
    return sorted(collisions | pending)


def normalize_games(frame, scopes):
    """Retain raw names/source IDs before the unchanged analytical normalization."""
    raw = frame.drop(
        columns=[c for c in frame if c.startswith("_")], errors="ignore"
    ).copy()
    raw["raw_player_name"], raw["raw_team"] = raw.player_name, raw.team
    original = api.to_proballers_schema

    def preserve(source):
        result = original(source)
        source = source.reset_index(drop=True)
        result["raw_player_name"] = source.Player
        result["raw_team"] = source.Team
        if "Player_ID" not in source:
            raise ValueError("API player ID unavailable")
        result["official_person_id"] = "euroleague:" + source.Player_ID.astype(str)
        result["identity_status"] = "SOURCE_ID_ONLY_NO_CROSSWALK"
        return result

    api.to_proballers_schema = preserve
    try:
        games = blf._swap_in_api_destination(raw)
    finally:
        api.to_proballers_schema = original
    # Quarantine excludes player records, not their full-team contributions.
    games = blf.add_usage(games)
    scope_index = pd.MultiIndex.from_tuples(scopes, names=["player_name", "season"])
    bad = pd.MultiIndex.from_frame(games[["player_name", "season"]]).isin(scope_index)
    excluded = games.loc[bad].copy()
    excluded["exclusion_reason"] = "incomplete_cross_source_person_season_mapping"
    kept = games.loc[~bad].copy()
    if len(kept) + len(excluded) != len(games):
        raise ValueError("identity quarantine does not conserve rows")
    kept["analytical_identity_status"] = "HISTORICAL_NAME_KEY_NOT_VERIFIED_PERSON"
    return kept.reset_index(drop=True), excluded.reset_index(drop=True)


def model_inputs(games):
    pairs = blf.build_pairs(games, min_games=holdout.MIN_GAMES).reset_index(drop=True)
    with contextlib.redirect_stdout(io.StringIO()):
        switchers, agg = holdout.build_switchers(games)
    ledger, _ = revision.reconstruct_cohort(agg)
    cohort = ledger.loc[ledger.original_eligible].reset_index(drop=True)
    revision.unique(cohort)
    return pairs, switchers.reset_index(drop=True), cohort, ledger


def keyed_compare(left, right, keys, columns):
    if left.duplicated(keys).any() or right.duplicated(keys).any():
        raise ValueError("nonunique isolation comparison keys")
    a = left.sort_values(keys)[keys + columns].reset_index(drop=True)
    b = right.sort_values(keys)[keys + columns].reset_index(drop=True)
    pd.testing.assert_frame_equal(
        a, b, check_dtype=False, check_exact=False, atol=1e-9, rtol=0
    )
    return dict(status="PASS", rows=len(a), columns=columns)


def run(raw_root, decisions_dir, output):
    output = Path(output)
    if output.exists() and any(output.iterdir()):
        raise ValueError("output must be new or empty")
    prep = json.loads((acb.SOURCE / "preparation_manifest.json").read_text())
    previous.verify_inventory(prep["api_inputs"])
    for record in prep["raw_inputs"]:
        if acb.sha(Path(record["source_file"]).read_bytes()) != record["sha256"]:
            raise ValueError("frozen raw input changed")
    raw, inventory = old.load_raw(Path(raw_root))
    if {r["source_file"]: r["sha256"] for r in inventory} != {
        r["source_file"]: r["sha256"] for r in prep["raw_inputs"]
    }:
        raise ValueError("raw inventory differs from frozen source population")
    diagnosis = json.loads((acb.SOURCE / "source_diagnosis.json").read_text())
    evidence = json.loads((acb.SOURCE / "official_minute_evidence.json").read_text())
    repaired, minute_rows = old._repair_minutes(old._prepare(raw), diagnosis, evidence)
    decisions_dir = Path(decisions_dir)
    summary = json.loads((decisions_dir / "summary.json").read_text())
    if summary["decisions_sha256"] != acb.sha(
        (decisions_dir / "decisions.json").read_bytes()
    ) or summary["diagnosis_sha256"] != acb.sha(
        (acb.SOURCE / "source_diagnosis.json").read_bytes()
    ):
        raise ValueError("adjudication hash mismatch")
    decisions = json.loads((decisions_dir / "decisions.json").read_text())
    corrected, changes = apply_decisions(repaired, decisions, diagnosis)
    duplicate = corrected.duplicated(old.TEAM_KEY)
    dropped_duplicates = corrected.loc[
        duplicate, [*KEY, "_source_file", "_raw_row_id"]
    ].copy()
    corrected = corrected.loc[~duplicate].copy()
    control = repaired.loc[~duplicate].copy()
    scopes = collision_scopes(diagnosis, decisions)
    games, excluded = normalize_games(corrected, scopes)
    before, _ = normalize_games(control, scopes)
    pairs, switchers, cohort, cohort_ledger = model_inputs(games)
    before_pairs, _, before_cohort, _ = model_inputs(before)
    # Current 2025 corrections are isolated from the older minute repair and
    # identical scoped quarantine; this is not equality to raw baseline.
    pair_cols = [c for c in before_pairs if c not in ["player_name", "season"]]
    pair_check = keyed_compare(
        before_pairs.loc[before_pairs.season < 2025],
        pairs.loc[pairs.season < 2025],
        ["player_name", "season"],
        pair_cols,
    )
    feature_cols = [
        "season_src",
        "league_src",
        "pir_per36_src",
        "prior_mean_pir36",
        "above_own_prior",
    ]
    cohort_check = keyed_compare(
        before_cohort.loc[before_cohort.season_dest <= 2025],
        cohort.loc[cohort.season_dest <= 2025],
        revision.KEY,
        feature_cols,
    )
    output.mkdir(parents=True, exist_ok=True)
    frames = {
        "games.parquet": games,
        "pairs.parquet": pairs,
        "switchers.parquet": switchers,
        "cohort.parquet": cohort,
        "cohort_ledger.parquet": cohort_ledger,
        "identity_exclusions.parquet": excluded,
        "source_duplicates.parquet": dropped_duplicates,
        "field_changes.parquet": pd.DataFrame(changes),
    }
    for name, frame in frames.items():
        frame.to_parquet(output / name, index=False)
    result = dict(
        schema_version=1,
        status="prepared",
        variant="official_corrected",
        reference_variant=None,
        files={name: acb.sha((output / name).read_bytes()) for name in frames},
        protocol_sha256=acb.sha(PROTOCOL.read_bytes()),
        code_sha256=acb.sha(Path(__file__).read_bytes()),
        source_manifest_sha256=acb.sha(
            (acb.SOURCE / "preparation_manifest.json").read_bytes()
        ),
        adjudication_summary_sha256=acb.sha(
            (decisions_dir / "summary.json").read_bytes()
        ),
        counts=dict(
            raw_rows=len(raw),
            deduplicated_rows=len(corrected),
            canonical_games=len(games),
            source_duplicates=len(dropped_duplicates),
            identity_excluded=len(excluded),
            corrected_field_copies=len(changes),
            changed_field_copies=sum(r["changed"] for r in changes),
            earlier_minute_repairs=len(minute_rows),
            pairs=len(pairs),
            cohort=len(cohort),
            unresolved_fields=sum(
                r["status"] == "IDENTITY_REVIEW_REQUIRED" for r in decisions
            ),
        ),
        earlier_minute_evidence_sha256=acb.sha(
            (acb.SOURCE / "official_minute_evidence.json").read_bytes()
        ),
        quarantine_scopes=[dict(player_name=n, season=s) for n, s in scopes],
        isolation=dict(
            comparator=(
                "Earlier minute repair and scoped identity exclusion fixed; "
                "current 2025 official values vary"
            ),
            factor_pairs_before_2025=pair_check,
            forecast_inputs_through_2025=cohort_check,
        ),
        identity_limit=(
            "Fixture ACB IDs retained as evidence. Analytical names remain "
            "historical keys except incomplete ambiguous name/season "
            "scopes excluded. No universal verified-person or same-club claim."
        ),
        raw_files_modified=False,
        lock_modified=False,
    )
    previous.verify_inventory(prep["api_inputs"])
    for record in inventory:
        if acb.sha(Path(record["source_file"]).read_bytes()) != record["sha256"]:
            raise ValueError("raw input changed during correction")
    acb.dump(output / "variant.json", result)
    print(json.dumps(result["counts"]))
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--raw-root", type=Path, required=True)
    p.add_argument("--decisions-dir", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    a = p.parse_args()
    run(a.raw_root, a.decisions_dir, a.out)


if __name__ == "__main__":
    main()
