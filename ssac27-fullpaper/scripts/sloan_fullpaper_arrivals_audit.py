#!/usr/bin/env python3
"""E26: a rule-based identity audit of the 674 forecast arrivals.

Pre-registration: docs/research/sloan-full-paper-preregistration-amendment-6-2026-11-12.md
(commit 245bafa4b, pushed alone 2026-11-12, before this file existed).
EXPLORATORY. Not a third look at the estimation pairs (E13, E25): the unit here
is a forecast arrival, a domestic source season joined by name to a continental
destination season one year later.

* E26a. Every one of the 674 arrivals is classed CONFIRMED, NAME ONLY, WRONG or
  UNRESOLVED by fixed rules, with no hand review. Evidence: birthdates (the E13
  rule across the two seasons); the imported E13 same-season check in the source
  season (when the same API person has continental rows there) and in the
  destination season (against every domestic record of the name key); and the
  EuroLeague API's "previous team" matched to a source club by a fixed text rule.
* E26b. The three registered paired comparisons are re-scored on subsets defined
  by the classes (S1 without WRONG, S2 without WRONG and UNRESOLVED, S3 CONFIRMED
  only). Forecasts are the ones already fitted; nothing is refitted. The classes
  are written to disk before any subset is scored.

Threats and their controls (all in this file): rules bent toward a clean result
(every rule fixed in the amendment, no hand review); a weak text match passed
off as confirmation (G26d: the match share must be at least twice the share
after a seeded shuffle, or the evidence is not used); different forecasts or
rules than registered (G26b reproduces the committed contrasts on all 674 to
1e-9; G26c reproduces the E13 sample pair for pair; each with a negative
control); a changed input (G26a sha256 pins).
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
import re
import sys
import unicodedata
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from scripts import sloan_fullpaper_common as common  # noqa: E402
from scripts import sloan_fullpaper_linkage_audit as e13  # noqa: E402
from scripts import sloan_fullpaper_linkage_audit_e25 as e25  # noqa: E402
from scripts import sloan_fullpaper_robustness as robust  # noqa: E402
from scripts import sloan_same_club as same_club  # noqa: E402
from scripts.translation_research_common import sha256_file  # noqa: E402
from src.data.corpus import euroleague_api as api  # noqa: E402

AMENDMENT = (
    ROOT / "docs/research/sloan-full-paper-preregistration-amendment-6-2026-11-12.md"
)
AMENDMENT_COMMIT = "245bafa4b"
ARTIFACTS = ROOT / "docs/research/artifacts/sloan-fullpaper-arrivals-audit-2026-11"
PEOPLE = ARTIFACTS / "inputs/euroleague_api_people_last_team_2020_2025.csv"
PEOPLE_SHA = "753aebcbfb0c724eb1819da0abb4f21e80f18cb50a1ddee18bfb966ede1c3e3c"
REGISTERED = (
    ROOT / "docs/research/artifacts/sloan-fullpaper-robustness-2026-11-03/summary.json"
)
REGISTERED_SHA = "ec2e2c10f44b801a1af099600841a73058872f9430b3aecfaf507a7fc32c91db"
KEY = ["player_name", "season_dest"]
N_ARRIVALS = 674
CLASSES = ("CONFIRMED", "NAME ONLY", "WRONG", "UNRESOLVED")
COMPETITION_CODE = {"euroleague": "E", "eurocup": "U"}
GENERIC_WORDS = frozenset(
    "BC BK KK CB SC SK AS FC CLUB BASKET BASKETBALL BASKETBOL BALONCESTO PALLACANESTRO".split()
)
JACCARD_MIN = 0.6
SHUFFLE_SEED = 20261113
SHUFFLE_RATIO = 2.0
MARGIN_SHARE = 0.02
REPORT_WRONG_SHARE = 0.05
TOLERANCE = 1e-9
MIN_SUBSET = (
    30  # below this a clustered interval is not attempted; printed as not estimable
)
COMPARISONS = {
    "history_gain": "translation against history",
    "e1_head_to_head": "league-aware against history plus translation",
    "offsets10_increment": "translation added to the league-aware forecast",
}
SUBSETS = {
    "all": "all 674 arrivals",
    "S1": "without WRONG (primary)",
    "S2": "without WRONG and UNRESOLVED",
    "S3": "CONFIRMED only",
}
GateFailure = e13.GateFailure


# ------------------------------------------------------- previous-team rule --


def club_words(name: object) -> frozenset:
    """Upper-case, no accents or punctuation, generic words dropped."""
    if not isinstance(name, str):
        return frozenset()
    text = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    words = re.sub(r"[^A-Z0-9]", " ", text.upper()).split()
    return frozenset(w for w in words if w not in GENERIC_WORDS)


def clubs_match(a: object, b: object) -> bool:
    """All words of the shorter name are in the longer one, or Jaccard >= 0.6."""
    x, y = club_words(a), club_words(b)
    if not x or not y:
        return False
    short, long_ = (x, y) if len(x) <= len(y) else (y, x)
    if short <= long_:
        return True
    return len(x & y) / len(x | y) >= JACCARD_MIN


def previous_team_matches(last_teams: list, source_clubs: list) -> bool:
    return any(clubs_match(t, c) for t in last_teams for c in source_clubs)


def previous_team_gate(last_teams: list, source_clubs: list) -> dict:
    """G26d: the real match share against a seeded shuffle of the previous teams."""
    if clubs_match("HAPOEL TEL AVIV", "MACCABI TEL AVIV"):
        raise GateFailure("G26d: two Tel Aviv clubs match")
    if not clubs_match("GRAVELINES", "BCM GRAVELINES DUNKERQUE"):
        raise GateFailure("G26d: Gravelines does not match its long name")
    n = len(source_clubs)
    real = sum(
        previous_team_matches(t, c)
        for t, c in zip(last_teams, source_clubs, strict=True)
    )
    order = np.random.default_rng(SHUFFLE_SEED).permutation(n)
    shuffled = sum(
        previous_team_matches(last_teams[int(j)], c)
        for j, c in zip(order, source_clubs, strict=True)
    )
    used = bool(real > 0 and real >= SHUFFLE_RATIO * shuffled)
    return {
        "status": "passed" if used else "failed: previous-team evidence not used",
        "evidence_used": used,
        "matches": int(real),
        "matches_after_shuffle": int(shuffled),
        "n": int(n),
        "share": real / n if n else None,
        "share_after_shuffle": shuffled / n if n else None,
        "required_ratio": SHUFFLE_RATIO,
        "shuffle_seed": SHUFFLE_SEED,
        "unit_controls": "passed",
    }


# ------------------------------------------------------------------ inputs --


def load_people(path: Path) -> pd.DataFrame:
    common.check_sha(path, PEOPLE_SHA)
    people = pd.read_csv(path, dtype=str, keep_default_na=False)
    people["key"] = people.name.map(api.pairing_key)
    people["season"] = people.season.astype(int)
    return people


def arrivals_frame(cohort: pd.DataFrame, keys: pd.DataFrame) -> pd.DataFrame:
    cols = [
        *KEY,
        "league_dest",
        "club_dest",
        "games_dest",
        "season_src",
        "league_src",
        "club_src",
        "games_src",
    ]
    frame = keys.merge(cohort[cols], on=KEY, how="left", validate="1:1")
    if len(frame) != N_ARRIVALS or frame.league_src.isna().any():
        raise GateFailure("the 674 target keys do not join one-to-one to the cohort")
    if not frame.season_src.astype(int).eq(frame.season_dest.astype(int) - 1).all():
        raise GateFailure("a source season is not the season before the destination")
    return frame.sort_values(KEY, kind="mergesort").reset_index(drop=True)


# ---------------------------------------------------------------- evidence --


def birthdate_status(persons: list, source_names: list, raw: dict) -> str:
    """The E13 birthdate rule across the two seasons: one birthdate on each side."""
    dob_c = sorted({raw["el_map"].get(p) for p in persons} - {None})
    profiles = sorted(
        {
            raw["pb_map"][n]
            for n in map(same_club.strict_name, source_names)
            if n in raw["pb_map"]
        }
    )
    if len(dob_c) == 1 and len(profiles) == 1:
        return "agrees" if profiles[0][1] == dob_c[0] else "contradicts"
    if len(dob_c) > 1 or len(profiles) > 1:
        return "multiple"
    return "not_available"


def same_season_check(key, season, dom_league, comp, raw) -> dict:
    """The imported E13 check on one same-season pair of the name key."""
    cont, dom = raw["cont"], raw["dom"]
    c_rows = cont.loc[cont.season.eq(season) & cont.key.eq(key) & cont.league.eq(comp)]
    d_rows = dom.loc[
        dom.season.eq(season) & dom.key.eq(key) & dom.league.eq(dom_league)
    ]
    pair = SimpleNamespace(
        player_name=key,
        season=season,
        league_src=dom_league,
        league_dest=comp,
        games_dest=int(c_rows.game_id.nunique()),
        games_src=int(d_rows.game_id.nunique()),
        club_dest=";".join(sorted(c_rows.club.unique())),
        club_src=";".join(sorted(d_rows.club.unique())),
    )
    return e13.check_pair(pair, cont, dom, raw["pb_map"], raw["el_map"])


def evidence(row, raw: dict, people: pd.DataFrame) -> dict:
    """Every piece of registered evidence for one arrival. No class is set here."""
    cont, dom = raw["cont"], raw["dom"]
    key, t, s = row.player_name, int(row.season_dest), int(row.season_src)
    dest = cont.loc[
        cont.season.eq(t) & cont.key.eq(key) & cont.league.eq(row.league_dest)
    ]
    src = dom.loc[dom.season.eq(s) & dom.key.eq(key) & dom.league.eq(row.league_src)]
    persons = sorted(dest.person.unique())
    source_clubs = sorted(src.club.unique())
    rec = {
        "games_dest_found": int(dest.game_id.nunique()),
        "games_src_found": int(src.game_id.nunique()),
        "api_persons": ";".join(persons),
        "n_api_persons": len(persons),
        "source_clubs": "; ".join(source_clubs),
        "dob_status": birthdate_status(persons, list(src.raw_name.unique()), raw),
    }
    # Source-season bridge: the same API person in continental play that season.
    bridge = cont.loc[cont.season.eq(s) & cont.key.eq(key) & cont.person.isin(persons)]
    other = cont.loc[cont.season.eq(s) & cont.key.eq(key) & ~cont.person.isin(persons)]
    bridge_classes = {
        comp: same_season_check(key, s, row.league_src, comp, raw)["rule_class"]
        for comp in sorted(bridge.league.unique())
    }
    rec["bridge_classes"] = "; ".join(f"{k}={v}" for k, v in bridge_classes.items())
    rec["bridge_status"] = (
        "none"
        if not bridge_classes
        else "WRONG"
        if "WRONG" in bridge_classes.values()
        else "CONFIRMED"
        if "CONFIRMED" in bridge_classes.values()
        else "UNRESOLVED"
    )
    rec["other_api_person_in_source_season"] = bool(len(other))
    # Destination-season check against every domestic record of the name key.
    dom_t = dom.loc[dom.season.eq(t) & dom.key.eq(key)]
    dest_classes = {
        league: same_season_check(key, t, league, row.league_dest, raw)["rule_class"]
        for league in sorted(dom_t.league.unique())
    }
    rec["dest_classes"] = "; ".join(f"{k}={v}" for k, v in dest_classes.items())
    rec["dest_domestic_clubs"] = "; ".join(
        f"{league}|{club}:{group.game_id.nunique()}g"
        for (league, club), group in dom_t.groupby(["league", "club"], sort=True)
    )
    stayed_clubs = set(dom_t.loc[dom_t.league.eq(row.league_src), "club"]) & set(
        source_clubs
    )
    rec["stayed"] = bool(stayed_clubs)
    rec["stayed_class"] = dest_classes.get(row.league_src, "") if stayed_clubs else ""
    rec["dest_confirmed_any"] = "CONFIRMED" in dest_classes.values()
    rec["dest_wrong_any"] = "WRONG" in dest_classes.values()
    # Previous team named by the API for the destination season.
    listed = people.loc[
        people.key.eq(key)
        & people.season.eq(t)
        & people.comp.eq(COMPETITION_CODE[row.league_dest])
    ]
    last_teams = sorted({x for x in listed.last_team if x.strip()})
    rec["previous_teams"] = "; ".join(last_teams)
    rec["previous_team_listed"] = bool(last_teams)
    rec["previous_team_match"] = previous_team_matches(last_teams, source_clubs)
    rec["_last_teams"], rec["_source_clubs"] = last_teams, source_clubs
    return rec


def classify(rec: dict, previous_team_used: bool) -> tuple[str, str]:
    """The registered classes (Amendment 6, E26a), in the registered order."""
    wrong = [
        label
        for label, hit in (
            ("birthdate contradicts", rec["dob_status"] == "contradicts"),
            ("source-season bridge is WRONG", rec["bridge_status"] == "WRONG"),
            (
                "a different player of this name is still at the source club",
                rec["stayed"] and rec["stayed_class"] == "WRONG",
            ),
            ("two API persons behind the destination record", rec["n_api_persons"] > 1),
        )
        if hit
    ]
    if wrong:
        return "WRONG", "; ".join(wrong)
    confirmed = [
        label
        for label, hit in (
            ("birthdate agrees", rec["dob_status"] == "agrees"),
            ("source-season bridge", rec["bridge_status"] == "CONFIRMED"),
            (
                "stayed at the source club",
                rec["stayed"] and rec["stayed_class"] == "CONFIRMED",
            ),
            (
                "previous team matches a source club",
                previous_team_used and rec["previous_team_match"],
            ),
        )
        if hit
    ]
    if confirmed:
        return "CONFIRMED", "; ".join(confirmed)
    if rec["dest_confirmed_any"] and not rec["dest_wrong_any"]:
        return (
            "NAME ONLY",
            "destination player identified; no second player of this name visible",
        )
    return "UNRESOLVED", "no registered evidence either way"


def audit(
    frame: pd.DataFrame, raw: dict, people: pd.DataFrame
) -> tuple[pd.DataFrame, dict]:
    records = [evidence(row, raw, people) for row in frame.itertuples(index=False)]
    gate = previous_team_gate(
        [r["_last_teams"] for r in records], [r["_source_clubs"] for r in records]
    )
    out = frame.copy()
    for column in (k for k in records[0] if not k.startswith("_")):
        out[column] = [r[column] for r in records]
    classes = [classify(r, gate["evidence_used"]) for r in records]
    out["audit_class"] = [c for c, _ in classes]
    out["audit_reason"] = [r for _, r in classes]
    return out, gate


# ------------------------------------------------------------- comparisons --


def comparison(rows: pd.DataFrame, name: str, sd: float) -> dict:
    left, right = robust.CONTRASTS[name]
    if len(rows) < MIN_SUBSET:
        return {
            "comparison": name,
            "label": COMPARISONS[name],
            "n": int(len(rows)),
            "difference": None,
            "ci95": None,
            "margin": None,
            "registered_reading_holds": None,
        }
    record = robust.contrast_record(rows, left, right, sd)
    interval = record["player_club_season"]["ci95"]
    margin = MARGIN_SHARE * float(
        np.mean(np.abs(rows[common.PRIMARY_ARMS["offsets10"]] - rows.pir_per36_dest))
    )
    if interval is None:
        reading = None
    elif name == "history_gain":
        reading = bool(interval[0] > 0)
    else:
        reading = bool(
            interval[0] <= 0 <= interval[1]
            and -margin < interval[0]
            and interval[1] < margin
        )
    return {
        "comparison": name,
        "label": COMPARISONS[name],
        "n": int(len(rows)),
        "difference": record["difference"],
        "ci95": interval,
        "margin": margin,
        "registered_reading_holds": reading,
    }


def registered_gate(rows: pd.DataFrame, registered: dict, sd: float) -> dict:
    """G26b: the committed contrasts on all 674, and a shifted-forecast control."""

    def worst(frame):
        gaps = []
        for name in COMPARISONS:
            got, want = comparison(frame, name, sd), registered[name]
            gaps.append(abs(got["difference"] - want["difference"]))
            gaps += [
                abs(a - b)
                for a, b in zip(
                    got["ci95"], want["player_club_season"]["ci95"], strict=True
                )
            ]
        return max(gaps)

    gap = worst(rows)
    if not gap <= TOLERANCE:
        raise GateFailure(
            f"G26b: the committed contrasts are not reproduced (max gap {gap:.3g})"
        )
    shifted = rows.copy()
    shifted[common.PRIMARY_ARMS["history_translation"]] += 0.1
    if worst(shifted) <= TOLERANCE:
        raise GateFailure(
            "G26b negative control: a shifted forecast reproduced the committed contrasts"
        )
    return {
        "status": "passed",
        "max_abs_gap": gap,
        "tolerance": TOLERANCE,
        "negative_control": "rejected as required",
    }


def subset_masks(classes: pd.Series) -> dict:
    return {
        "all": pd.Series(True, index=classes.index),
        "S1": classes.ne("WRONG"),
        "S2": ~classes.isin(["WRONG", "UNRESOLVED"]),
        "S3": classes.eq("CONFIRMED"),
    }


def licences(counts: dict, table: pd.DataFrame, gate_d: dict) -> dict:
    n = sum(counts.values())
    s1 = table.loc[table.subset.eq("S1")]
    holds = bool(
        s1.registered_reading_holds.notna().all() and s1.registered_reading_holds.all()
    )
    return {
        "count_sentence": (
            f"By fixed rules, {counts['WRONG']} of the {n} forecast arrivals are classed as identity mismatches; "
            f"{counts['CONFIRMED']} are confirmed by independent evidence, {counts['NAME ONLY']} rest on the name "
            f"across a change of club, and {counts['UNRESOLVED']} are unresolved."
        ),
        "s1_all_readings_hold": holds,
        "s1_sentence": "the three comparisons read the same without the arrivals classed wrong"
        if holds
        else None,
        "s1_failed_readings": sorted(
            s1.loc[
                s1.registered_reading_holds.isna()
                | s1.registered_reading_holds.eq(False),
                "comparison",
            ]  # noqa: E712
        ),
        "wrong_share": counts["WRONG"] / n,
        "wrong_share_at_least_5pct": bool(counts["WRONG"] / n >= REPORT_WRONG_SHARE),
        "previous_team_evidence_used": gate_d["evidence_used"],
        "report_to_amir_before_writing": bool(
            (not holds) or counts["WRONG"] / n >= REPORT_WRONG_SHARE
        ),
    }


def by_group(final: pd.DataFrame, column: str) -> pd.DataFrame:
    table = final.groupby([column, "audit_class"]).size().unstack(fill_value=0)
    table = table.reindex(columns=list(CLASSES), fill_value=0)
    table.insert(0, "n", table.sum(axis=1))
    return table.reset_index()


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument("--raw-root", type=Path, required=True)
    parser.add_argument("--bio", type=Path, required=True)
    parser.add_argument("--people", type=Path, default=PEOPLE)
    parser.add_argument("--e13-dir", type=Path, default=e25.E13_DIR)
    parser.add_argument("--registered", type=Path, default=REGISTERED)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    args.out.mkdir(parents=True, exist_ok=False)

    # G26a inputs (pairs and cohort are sha-checked inside load_pool).
    e25.check_e13_generator()
    people = load_people(args.people)
    common.check_sha(args.registered, REGISTERED_SHA)
    registered = json.loads(args.registered.read_text())["e3"]["O1"]["contrasts"]
    pairs, cohort = common.load_pool(args.input_dir, "official_corrected")
    _, v10_summary = common.load_references(ROOT)
    keys = common.target_keys(v10_summary)
    frame = arrivals_frame(cohort, keys)
    control = args.out / "_g26a_control.csv"
    data = args.people.read_bytes()
    control.write_bytes(data[:-1] + (b"0" if data[-1:] != b"0" else b"1"))
    try:
        common.check_sha(control, PEOPLE_SHA)
    except common.GateFailure:
        input_control = "rejected as required"
    else:
        raise GateFailure("G26a negative control: a changed API list passed")
    finally:
        control.unlink()

    # E26a: classes first, written before any subset is scored.
    raw = e25.load_raw(args.raw_root, args.bio)
    gate_c, _ = e25.same_rules_gate(
        pairs, e25.load_e13_keys(args.e13_dir), args.e13_dir, raw
    )
    final, gate_d = audit(frame, raw, people)
    final.to_csv(args.out / "e26_arrivals.csv", index=False)
    for column, name in (
        ("league_src", "league"),
        ("league_dest", "destination"),
        ("season_dest", "season"),
    ):
        by_group(final, column).to_csv(args.out / f"e26_by_{name}.csv", index=False)
    counts = {c: int(final.audit_class.eq(c).sum()) for c in CLASSES}

    # E26b: the registered comparisons on subsets defined by the classes.
    rows, _, _ = common.anchor_rows(ROOT, args.input_dir)
    rows = rows.merge(final[[*KEY, "audit_class"]], on=KEY, how="left", validate="1:1")
    if len(rows) != N_ARRIVALS or rows.audit_class.isna().any():
        raise GateFailure("the scored rows do not carry one class each")
    sd = float(json.loads(args.registered.read_text())["e3"]["O1"]["outcome_sd"])
    gate_b = registered_gate(rows, registered, sd)
    table = []
    for subset, mask in subset_masks(rows.audit_class).items():
        part = rows.loc[mask].reset_index(drop=True)
        for name in COMPARISONS:
            table.append(
                {
                    "subset": subset,
                    "subset_label": SUBSETS[subset],
                    **comparison(part, name, sd),
                }
            )
    table = pd.DataFrame(table)
    out_table = table.assign(
        ci_low=[c[0] if c else None for c in table.ci95],
        ci_high=[c[1] if c else None for c in table.ci95],
    ).drop(columns="ci95")
    out_table.to_csv(args.out / "e26_comparisons.csv", index=False)

    confirmed = final.loc[final.audit_class.eq("CONFIRMED"), "audit_reason"]
    summary = {
        "analysis": "E26",
        "exploratory": True,
        "amendment_commit": AMENDMENT_COMMIT,
        "amendment_sha256": sha256_file(AMENDMENT),
        "n_arrivals": int(len(final)),
        "class_counts": counts,
        "class_shares": {c: counts[c] / len(final) for c in CLASSES},
        "confirmed_by": {
            label: int(confirmed.str.contains(label, regex=False).sum())
            for label in (
                "birthdate agrees",
                "source-season bridge",
                "stayed at the source club",
                "previous team matches a source club",
            )
        },
        "stayed": int(final.stayed.sum()),
        "moved": int((~final.stayed).sum()),
        "check_counts": {
            "dob_status": final.dob_status.value_counts().sort_index().to_dict(),
            "bridge_status": final.bridge_status.value_counts().sort_index().to_dict(),
            "previous_team_listed": int(final.previous_team_listed.sum()),
            "previous_team_match": int(final.previous_team_match.sum()),
            "other_api_person_in_source_season": int(
                final.other_api_person_in_source_season.sum()
            ),
        },
        "reconciliation": {
            "dest_games_match": int(final.games_dest_found.eq(final.games_dest).sum()),
            "src_games_match": int(final.games_src_found.eq(final.games_src).sum()),
            "n": int(len(final)),
        },
        "gates": {
            "G26a_inputs": {
                "status": "passed",
                "negative_control": input_control,
                "people_sha256": PEOPLE_SHA,
            },
            "G26b_same_forecasts": gate_b,
            "G26c_same_rules": gate_c,
            "G26d_previous_team": gate_d,
        },
        "comparisons": json.loads(out_table.to_json(orient="records")),
        "licences": licences(counts, table, gate_d),
        "raw_inputs": raw["used"],
        "rules": {
            "generic_words": sorted(GENERIC_WORDS),
            "jaccard_min": JACCARD_MIN,
            "margin_share": MARGIN_SHARE,
            "report_wrong_share": REPORT_WRONG_SHARE,
        },
    }
    (args.out / "e26_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True, default=str) + "\n"
    )
    print(
        f"E26 classes {counts}; previous-team evidence used: {gate_d['evidence_used']} "
        f"({gate_d['matches']} matches, {gate_d['matches_after_shuffle']} after shuffle); "
        f"S1 readings hold: {summary['licences']['s1_all_readings_hold']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
