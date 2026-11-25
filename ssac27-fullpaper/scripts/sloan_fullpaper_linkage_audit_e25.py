#!/usr/bin/env python3
"""E25: a second, larger identity-linkage audit of the unverified estimation pairs.

Pre-registration: docs/research/sloan-full-paper-preregistration-amendment-5-2026-11-12.md
(commit be615140b, pushed alone 2026-11-12, before this file existed).
EXPLORATORY, and a SECOND LOOK: E13 (Amendment 1) audited 100 pairs, found 1
WRONG (Wilson 95% upper bound 5.4%) and earned no licence. E25 was added after
that result was read.

* Frame: the E13 frame (pool-A pairs absent from verified pool B, 2,537) minus
  the 100 pairs drawn in E13: 2,437 pairs.
* Sample: 300 pairs, simple random sample without replacement,
  numpy.random.default_rng(20261112), frame sorted by the E13 key. The drawn
  keys are written to the run output BEFORE any raw record is read
  (``--stage draw`` stops there).
* Checks, classes and thresholds: exactly E13's. Every check is the imported
  E13 function; this file holds only the frame, the draw, the gates and the
  summaries. The E13 generator is pinned by sha256.
* Hand review only for rule-UNRESOLVED pairs (the E13 rule, enforced by the
  imported ``apply_hand_review``).
* Licence: the bound is earned only if the Wilson 95% upper bound is below 5%
  on the new 300 AND on the pooled 400. The quoted X is the larger of the two,
  rounded up to one decimal. No third look.

Threats and their controls (all in this file): a second look taken because the
first one missed (fresh disjoint sample that must pass on its own, G25b); a
draw chosen after looking (keys written first, G25a, with a different-seed
negative control); rules that drifted from E13 (generator sha pin, and G25c:
the E13 100 re-audited here must reproduce the committed E13 rule classes pair
for pair, with a changed-threshold negative control).
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
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import pandas as pd  # noqa: E402

from scripts import sloan_fullpaper_common as common  # noqa: E402
from scripts import sloan_fullpaper_linkage_audit as e13  # noqa: E402
from scripts.translation_research_common import sha256_file  # noqa: E402

AMENDMENT = (
    ROOT / "docs/research/sloan-full-paper-preregistration-amendment-5-2026-11-12.md"
)
AMENDMENT_COMMIT = "be615140b"
E13_GENERATOR = ROOT / "scripts/sloan_fullpaper_linkage_audit.py"
E13_GENERATOR_SHA = "8fb91e66c881a5addff6dc5f50a6ebcda5777e5caf19543603c55dedb0e1e91a"
E13_DIR = ROOT / "docs/research/artifacts/sloan-fullpaper-linkage-audit-2026-11"
E13_KEYS_SHA = "b19d70139ba62e2da8a8ae1ad43a3bf475a06d9cbb2df711e23661ea41ba604d"
E13_AUDIT_SHA = "c9b08c04d4db0359e2af433d596acab882625b3fb4d89c56b75f1ff96cfcfacc"
KEY = e13.E13_KEY
SEED = 20261112
CONTROL_SEED = SEED + 1
SAMPLE_N = 300
EXPECTED_E13_FRAME = 2537
EXPECTED_FRAME = 2437
UPPER_LICENCE = e13.UPPER_LICENCE
REPORT_TO_AMIR = e13.REPORT_TO_AMIR
STATUS_COLUMNS = ("name_status", "dob_status", "club_status", "schedule_status")
LICENCES = {
    "bound_earned": "at most X% of unverified estimation pairs are identity mismatches",
    "bound_not_earned": "the bound was not earned in either look",
    "point_at_least_10pct": "reported to Amir before any writing, as a data-quality finding that touches every factor",
}
GateFailure = e13.GateFailure


def check_e13_generator() -> str:
    """The E13 rules are used as registered: the generator file must be the pinned one."""
    got = sha256_file(E13_GENERATOR)
    if got != E13_GENERATOR_SHA:
        raise GateFailure(
            "the E13 generator differs from the one registered in Amendment 5"
        )
    return got


def load_e13_keys(e13_dir: Path) -> pd.DataFrame:
    path = Path(e13_dir) / "e13_drawn_keys.csv"
    common.check_sha(path, E13_KEYS_SHA)
    keys = pd.read_csv(path)
    if len(keys) != e13.SAMPLE_N or keys.duplicated(KEY).any():
        raise GateFailure("the committed E13 keys are not the unique 100")
    return keys


def build_frame(e13_frame: pd.DataFrame, e13_keys: pd.DataFrame) -> pd.DataFrame:
    """The E13 frame minus the E13 sample, order kept (sorted E13 key)."""
    if len(e13_frame) != EXPECTED_E13_FRAME:
        raise GateFailure(
            f"the E13 frame has {len(e13_frame)} pairs, not {EXPECTED_E13_FRAME}"
        )
    left = e13_frame[KEY].astype(str)
    right = e13_keys[KEY].astype(str).drop_duplicates()
    merged = left.merge(right, on=KEY, how="left", indicator=True)
    if len(merged) != len(e13_frame):
        raise GateFailure("frame anti-join changed the row count")
    keep = merged["_merge"].eq("left_only").to_numpy()
    if int((~keep).sum()) != len(e13_keys):
        raise GateFailure("an E13 key is missing from the E13 frame")
    frame = e13_frame.loc[keep, KEY].reset_index(drop=True)
    if len(frame) != EXPECTED_FRAME:
        raise GateFailure(f"the E25 frame has {len(frame)} pairs, not {EXPECTED_FRAME}")
    return frame


def assert_disjoint(sample: pd.DataFrame, e13_keys: pd.DataFrame) -> None:
    """G25b: no drawn key may be among the E13 100."""
    overlap = (
        sample[KEY].astype(str).merge(e13_keys[KEY].astype(str), on=KEY, how="inner")
    )
    if len(overlap):
        raise GateFailure(f"G25b: {len(overlap)} drawn keys are among the E13 sample")


def draw_gates(
    frame: pd.DataFrame,
    written: pd.DataFrame,
    e13_frame: pd.DataFrame,
    e13_keys: pd.DataFrame,
) -> dict:
    """G25a (redraw reproduces; another seed must not) and G25b (disjoint from E13)."""
    e13.assert_draw_reproduces(frame, written, SEED)
    try:
        e13.assert_draw_reproduces(frame, written, CONTROL_SEED)
    except GateFailure:
        control_a = "rejected as required"
    else:
        raise GateFailure(
            f"G25a negative control: seed {CONTROL_SEED} gave the same sample"
        )
    control_sample = e13.draw(frame, seed=CONTROL_SEED, n=len(written))
    shared = len(
        written[KEY]
        .astype(str)
        .merge(control_sample[KEY].astype(str), on=KEY, how="inner")
    )
    assert_disjoint(written, e13_keys)
    # Negative control: the E13 draw from the full E13 frame IS the E13 sample,
    # so the disjointness check must refuse it.
    e13_again = e13.draw(e13_frame, seed=e13.SEED, n=e13.SAMPLE_N)
    e13.assert_draw_reproduces(e13_frame, e13_keys, e13.SEED)
    try:
        assert_disjoint(e13_again, e13_keys)
    except GateFailure:
        control_b = "rejected as required"
    else:
        raise GateFailure(
            "G25b negative control: the E13 redraw passed the disjointness check"
        )
    return {
        "G25a_draw": {
            "status": "passed",
            "redraw_seed": SEED,
            "redraw_reproduces": True,
            "negative_control_seed": CONTROL_SEED,
            "negative_control": control_a,
            "negative_control_overlap_keys": int(shared),
        },
        "G25b_disjoint": {
            "status": "passed",
            "overlap_with_e13_sample": 0,
            "negative_control": control_b,
            "negative_control_overlap_keys": int(e13.SAMPLE_N),
        },
    }


def write_draw(input_dir: Path, e13_dir: Path, out: Path):
    """Frame, draw and draw gates; keys hit the disk before anything else is read."""
    generator_sha = check_e13_generator()
    pool_a = e13.load_pairs(input_dir, e13.POOL_A)
    pool_b = e13.load_pairs(input_dir, e13.POOL_B)
    e13_frame = e13.build_frame(pool_a, pool_b)
    e13_keys = load_e13_keys(e13_dir)
    frame = build_frame(e13_frame, e13_keys)
    sample = e13.draw(frame, seed=SEED, n=SAMPLE_N)
    out.mkdir(parents=True, exist_ok=False)
    keys_path = out / "e25_drawn_keys.csv"
    sample.to_csv(keys_path, index=False)
    written = pd.read_csv(keys_path)
    gates = draw_gates(frame, written, e13_frame, e13_keys)
    record = {
        "analysis": "E25",
        "exploratory": True,
        "second_look": True,
        "amendment_commit": AMENDMENT_COMMIT,
        "amendment_sha256": sha256_file(AMENDMENT),
        "e13_generator_sha256": generator_sha,
        "input_sha256": {
            e13.POOL_A: common.PAIRS_SHA[e13.POOL_A],
            e13.POOL_B: common.PAIRS_SHA[e13.POOL_B],
            "e13_drawn_keys.csv": E13_KEYS_SHA,
        },
        "key": KEY,
        "frame_order": "the E13 frame order (sorted by the E13 key, stable) with the E13 sample removed",
        "pool_a_pairs": int(len(pool_a)),
        "pool_b_pairs": int(len(pool_b)),
        "e13_frame_pairs": int(len(e13_frame)),
        "e13_sample_n": int(len(e13_keys)),
        "frame_pairs": int(len(frame)),
        "seed": SEED,
        "sample_n": int(len(sample)),
        "drawn_keys_file": keys_path.name,
        "drawn_keys_sha256": sha256_file(keys_path),
        "gates": gates,
    }
    (out / "e25_draw.json").write_text(
        json.dumps(record, indent=2, sort_keys=True) + "\n"
    )
    return written, e13_keys, record


# ------------------------------------------------------------------ checks --


def load_raw(raw_root: Path, bio_path: Path) -> dict:
    cont, used_c = e13.load_continental(raw_root)
    dom, used_d = e13.load_domestic(raw_root)
    pb_map, el_map, used_b = e13.load_birthdates(raw_root, bio_path)
    return {
        "cont": cont,
        "dom": dom,
        "pb_map": pb_map,
        "el_map": el_map,
        "used": {"continental": used_c, "domestic": used_d, "profiles": used_b},
    }


def check_sample(pairs: pd.DataFrame, written: pd.DataFrame, raw: dict):
    """The E13 checks (imported) on one written sample. Same loop as E13's ``audit_sample``."""
    sample = written.merge(pairs, on=KEY, how="left", validate="1:1")
    if sample.games_src.isna().any():
        raise GateFailure("a drawn key is missing from pool A")
    records, pack = [], []
    for pair in sample.itertuples(index=False):
        rec = {c: getattr(pair, c) for c in ["draw_order", "frame_row", *KEY]}
        rec.update(
            e13.check_pair(pair, raw["cont"], raw["dom"], raw["pb_map"], raw["el_map"])
        )
        records.append(rec)
        if rec["rule_class"] == "UNRESOLVED":
            pack.extend(e13.evidence_pack(pair, raw["cont"], raw["dom"]))
    return pd.DataFrame(records), pd.DataFrame(pack)


def assert_same_rules(reaudit: pd.DataFrame, committed: pd.DataFrame) -> None:
    """G25c: the E13 100 re-audited here must equal the committed E13 rule results."""
    cols = [*KEY, *STATUS_COLUMNS, "rule_class"]
    left = reaudit[cols].astype(str).sort_values(KEY).reset_index(drop=True)
    right = committed[cols].astype(str).sort_values(KEY).reset_index(drop=True)
    if not left.equals(right):
        diff = (
            int((left != right).any(axis=1).sum()) if left.shape == right.shape else -1
        )
        raise GateFailure(
            f"G25c: the E13 rule results are not reproduced ({diff} pairs differ)"
        )


def same_rules_gate(
    pairs: pd.DataFrame, e13_keys: pd.DataFrame, e13_dir: Path, raw: dict
) -> tuple[dict, pd.DataFrame]:
    path = Path(e13_dir) / "e13_audit_pairs.csv"
    common.check_sha(path, E13_AUDIT_SHA)
    committed = pd.read_csv(path, keep_default_na=False)
    reaudit, _ = check_sample(pairs, e13_keys, raw)
    assert_same_rules(reaudit, committed)
    # Negative control: with an impossible same-club threshold no club can agree,
    # so the rule results must change and the comparison must refuse them.
    saved = e13.SAME_MIN_SHARED
    e13.SAME_MIN_SHARED = 10**6
    try:
        broken, _ = check_sample(pairs, e13_keys, raw)
    finally:
        e13.SAME_MIN_SHARED = saved
    try:
        assert_same_rules(broken, committed)
    except GateFailure:
        control = "rejected as required"
    else:
        raise GateFailure(
            "G25c negative control: a changed club threshold passed the comparison"
        )
    changed = int(
        broken.sort_values(KEY)
        .rule_class.astype(str)
        .reset_index(drop=True)
        .ne(committed.sort_values(KEY).rule_class.astype(str).reset_index(drop=True))
        .sum()
    )
    return {
        "status": "passed",
        "pairs_reproduced": int(len(reaudit)),
        "negative_control": control,
        "negative_control_changed_classes": changed,
    }, committed


# --------------------------------------------------------------- summaries --


def ceil_pct1(share: float) -> float:
    """A share as a percentage rounded UP to one decimal (for an 'at most' sentence)."""
    return math.ceil(share * 1000 - 1e-9) / 10


def rate(final_class: pd.Series) -> dict:
    n = int(len(final_class))
    wrong = int(final_class.eq("WRONG").sum())
    unresolved = int(final_class.eq("UNRESOLVED").sum())
    low, high = e13.wilson(wrong, n)
    low_s, high_s = e13.wilson(wrong + unresolved, n)
    return {
        "n": n,
        "wrong": wrong,
        "unresolved": unresolved,
        "confirmed": int(final_class.eq("CONFIRMED").sum()),
        "wrong_share": wrong / n,
        "wrong_wilson95": [low, high],
        "unresolved_share": unresolved / n,
        "unresolved_as_wrong_wilson95": [low_s, high_s],
    }


def licence(new: dict, pooled: dict, hand_reviewed: bool) -> dict:
    upper_new, upper_pooled = new["wrong_wilson95"][1], pooled["wrong_wilson95"][1]
    earned = bool(
        hand_reviewed and upper_new < UPPER_LICENCE and upper_pooled < UPPER_LICENCE
    )
    x = ceil_pct1(max(upper_new, upper_pooled))
    report = bool(
        new["wrong_share"] >= REPORT_TO_AMIR or pooled["wrong_share"] >= REPORT_TO_AMIR
    )
    return {
        "hand_review_applied": bool(hand_reviewed),
        "upper_new": upper_new,
        "upper_pooled": upper_pooled,
        "new_below_5pct": bool(upper_new < UPPER_LICENCE),
        "pooled_below_5pct": bool(upper_pooled < UPPER_LICENCE),
        "bound_earned": earned,
        "x_pct": x if earned else None,
        "licensed_sentence": LICENCES["bound_earned"].replace("X%", f"{x:.1f}%")
        if earned
        else None,
        "point_at_least_10pct": report,
        "third_look_allowed": False,
    }


def descriptive(final: pd.DataFrame) -> dict:
    both = final.dob_status.isin(["agrees", "contradicts"])
    wrong = final.final_class.eq("WRONG")
    birthdate_only = (
        wrong
        & final.dob_status.eq("contradicts")
        & final.club_status.eq("agrees")
        & final.schedule_status.eq("feasible")
    )
    return {
        "both_birthdates": int(both.sum()),
        "wrong_birthdate_only": int(birthdate_only.sum()),
        "wrong_other": int((wrong & ~birthdate_only).sum()),
    }


def by_group(final: pd.DataFrame, column: str) -> pd.DataFrame:
    table = (
        final.assign(
            wrong=final.final_class.eq("WRONG"),
            unresolved=final.final_class.eq("UNRESOLVED"),
            rule_unresolved=final.rule_class.eq("UNRESOLVED"),
        )
        .groupby(column)
        .agg(
            n=("final_class", "size"),
            wrong=("wrong", "sum"),
            unresolved=("unresolved", "sum"),
            rule_unresolved=("rule_unresolved", "sum"),
        )
        .reset_index()
    )
    return table.astype(
        {"n": int, "wrong": int, "unresolved": int, "rule_unresolved": int}
    )


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument("--e13-dir", type=Path, default=E13_DIR)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--stage", choices=("draw", "audit"), default="audit")
    parser.add_argument("--raw-root", type=Path)
    parser.add_argument("--bio", type=Path)
    parser.add_argument("--hand-review", type=Path)
    args = parser.parse_args(argv)
    written, e13_keys, record = write_draw(args.input_dir, args.e13_dir, args.out)
    gates = record["gates"]
    print(
        f"E25 frame {record['frame_pairs']} (E13 frame {record['e13_frame_pairs']} minus "
        f"{record['e13_sample_n']}); drew {len(written)} keys (seed {SEED}); "
        f"G25a {gates['G25a_draw']['status']}, G25b {gates['G25b_disjoint']['status']}"
    )
    if args.stage == "draw":
        return 0
    if args.raw_root is None or args.bio is None:
        parser.error("--stage audit needs --raw-root and --bio")
    pairs = pd.read_parquet(Path(args.input_dir) / e13.POOL_A / "pairs.parquet")
    raw = load_raw(args.raw_root, args.bio)
    gate_c, committed = same_rules_gate(pairs, e13_keys, args.e13_dir, raw)
    audit, pack = check_sample(pairs, written, raw)
    review = None
    if args.hand_review is not None:
        review = pd.read_csv(args.hand_review, dtype=str, keep_default_na=False)
    final = e13.apply_hand_review(audit, review)
    final.to_csv(args.out / "e25_audit_pairs.csv", index=False)
    pack.to_csv(args.out / "e25_unresolved_evidence.csv", index=False)
    by_group(final, "league_src").to_csv(args.out / "e25_by_league.csv", index=False)
    by_group(final, "season").to_csv(args.out / "e25_by_season.csv", index=False)
    new = rate(final.final_class)
    first = rate(committed.final_class)
    pooled = rate(
        pd.concat([committed.final_class, final.final_class], ignore_index=True)
    )
    record["gates"]["G25c_same_rules"] = gate_c
    record.update(
        stage="audit",
        class_rules=e13.CLASS_RULES,
        club_identity_rule={
            "same_min_shared": e13.SAME_MIN_SHARED,
            "same_min_share": e13.SAME_MIN_SHARE,
            "different_max_shared": e13.DIFFERENT_MAX_SHARED,
        },
        licences_registered=LICENCES,
        hand_review_file=(
            None
            if args.hand_review is None
            else {
                "name": args.hand_review.name,
                "sha256": sha256_file(args.hand_review),
            }
        ),
        reconciliation={
            "dest_games_match": int(
                audit.games_dest_found.eq(audit.games_dest_pair).sum()
            ),
            "src_games_match": int(
                audit.games_src_found.eq(audit.games_src_pair).sum()
            ),
            "n": int(len(audit)),
        },
        raw_inputs=raw["used"],
        unresolved_evidence_rows=int(len(pack)),
        check_status_counts={
            col: audit[col].value_counts().sort_index().to_dict()
            for col in STATUS_COLUMNS
        },
        rule_counts={c: int(final.rule_class.eq(c).sum()) for c in e13.CLASSES},
        e25={
            "new": new,
            "e13": first,
            "pooled": pooled,
            "licence": licence(new, pooled, hand_reviewed=review is not None),
            "descriptive": descriptive(final),
        },
    )
    (args.out / "e25_summary.json").write_text(
        json.dumps(record, indent=2, sort_keys=True, default=str) + "\n"
    )
    lic = record["e25"]["licence"]
    print(
        f"E25 rule classes {record['rule_counts']}; new WRONG {new['wrong']}/{new['n']} "
        f"(Wilson 95% upper {new['wrong_wilson95'][1]:.4f}), UNRESOLVED {new['unresolved']}; "
        f"pooled WRONG {pooled['wrong']}/{pooled['n']} (upper {pooled['wrong_wilson95'][1]:.4f}); "
        f"bound earned: {lic['bound_earned']}; hand review "
        f"{'applied' if lic['hand_review_applied'] else 'NOT applied'}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
