#!/usr/bin/env python3
"""Recompute the SSAC27 full paper's results from the public companion's tables.

Run from the companion repository root (or anywhere; paths resolve from this file):

    python ssac27-fullpaper/scripts/reproduce_sloan_fullpaper_public.py

What it does, in order, and what each step proves:

1. Integrity. Every file of this section is hashed against ``MANIFEST.json`` at
   the repository root (when present), so a changed table cannot pass silently.
2. RECOMPUTED from published player-season tables (no game rows), compared with
   the committed results file by file (byte-identical, or numerically equal to
   1e-9 where a library version changes the last digit):
   * G0 -- the submitted v10 numbers (inside E1/E2 and E7-E9);
   * E1/E2 -- the forecast ladder and the six translation recipes, all pools;
   * E7/E8/E9 -- pairwise decisions, conformal intervals, the league table;
   * E10/E11/E12/E17 and the ACB-16 exchange-rate table (Amendment 1);
   * E14a/E14b/E14c -- who the eight-game rule leaves out, from the 808-row
     all-arrivals tables;
   * E15a/E15b -- which skills travel (retention, carry-over);
   * the three vignettes;
   * E27 -- the three comparisons of the older-seasons test (Amendment 7), on
     all printed arrivals and on rare surnames, from the printed arrival rows;
   * E31a -- the league table printed in 2015, scored as a rival (Amendment
     15), and E31c -- the second frozen forecast file built from it, rebuilt
     from the pinned frozen file and compared with the committed one;
   * the converter page, built again from the result files.
3. CARRIED, not recomputed, because they need inputs this repository does not
   publish (per-game rows, birthdates or ages, raw API files). Their files are
   hash-checked and the script says so: E3-E6 (robustness; E5b uses ages and E6
   splits games), E13 and E25 (linkage audits; birthdates), E16 (flexible models; ages),
   the P1 freeze's raw-input rebuild and the P1 scoring. E18-E24 (Amendments 3
   and 4, added on 11 November 2026) are also carried for now: their generators
   and outputs ship, but this script does not re-run them yet (the generator
   rebuilds season tables from raw game files, which are not published).
   E27's freeze, linking and gates are carried too (league-site box scores are
   not published); its printed comparisons are recomputed in step 2.
   E33 (Amendment 22; exploratory) is carried: it refits the stayer forecast
   per season from the player-level league changes and stayer rows, which are
   not published.
   E34 (Amendment 23, rule 5; exploratory) is carried: it scores two published
   league scales on the 180 older arrivals and needs the scored older-season
   rows, which are not published.
4. Paper numbers. The manuscript text is composed again from the committed
   results with the paper's own renderer and must equal the rendered manuscript
   byte for byte; every number in it is checked against the file and key named
   in ``docs/paper/ssac27/paper-numbers.json``.

5. Registrations. Every row of ``REGISTRATION_HASHES.md`` names a file of this
   section; the file is found and its sha256 must equal the one in the row. The
   report lists where each file is.

Exit status 0 only if every recomputed result matches and every number checks.
A report is written to ``recomputed/report.json`` under this section. The last
lines printed are one line per step (ok, FAILED or not run) and the verdict.

One item alone:

    python ssac27-fullpaper/scripts/reproduce_sloan_fullpaper_public.py --only equivalents
    python ssac27-fullpaper/scripts/reproduce_sloan_fullpaper_public.py --only registration

``--only equivalents`` rebuilds the table of European League Equivalents
(``exchange_rate_acb16.csv``) from the pinned inputs and prints its
rows beside the committed ones. ``--only registration`` checks the hash list.
"""

# ruff: noqa: E501 -- report strings
from __future__ import annotations

import argparse
import contextlib
import hashlib
import io
import json
import math
import os
import re
import shutil
import sys
import time
from pathlib import Path

for _name in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_name, "1")
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

ART = ROOT / "docs/research/artifacts"
TABLES = ART / "sloan-fullpaper-public-tables-2026-11"
P1_SCORE = ART / "sloan-fullpaper-p1-score-2026-11/score.json"
NUMBERS = ROOT / "docs/paper/ssac27/paper-numbers.json"
#: The registration hash list: at the root of the public companion, or the private copy.
REGISTRATION_LISTS = (
    ROOT.parent / "REGISTRATION_HASHES.md",
    ROOT / "docs/paper/ssac27/public-cut/REGISTRATION_HASHES.md",
)
REGISTRATION_ROW = re.compile(
    r"^\| .+ \| `([^`]+)` \| `([0-9a-f]{64})` \| `[0-9a-f]+` \| [0-9: -]+ \|$"
)
#: How much of a failure's text is printed; the whole text is in the report.
FAILURE_TEXT_LIMIT = 1500
#: The section directory name in the public companion (the exporter's FULLPAPER_DIR).
PUBLIC_SECTION = "ssac27-fullpaper"
TOLERANCE = 1e-9


def sha(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def v10_input_dir() -> Path:
    for cand in (
        ROOT.parent / "ssac27-v10/data",
        ROOT / "data/processed/sloan_v10_public",
    ):
        if (cand / "official_corrected/pairs.parquet").is_file():
            return cand
    raise SystemExit("v10 tables not found (expected ../ssac27-v10/data)")


class Mismatch(AssertionError):
    pass


def deep_diff(a, b, path="", tol=TOLERANCE, out=None):
    out = [] if out is None else out
    if isinstance(a, dict) and isinstance(b, dict):
        for k in sorted(set(a) | set(b), key=str):
            if k not in a or k not in b:
                out.append(
                    f"{path}/{k}: present only in {'committed' if k in b else 'recomputed'}"
                )
            else:
                deep_diff(a[k], b[k], f"{path}/{k}", tol, out)
    elif isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            out.append(f"{path}: length {len(a)} vs {len(b)}")
        else:
            for i, (x, y) in enumerate(zip(a, b)):
                deep_diff(x, y, f"{path}[{i}]", tol, out)
    elif (
        isinstance(a, (int, float))
        and isinstance(b, (int, float))
        and not isinstance(a, bool)
        and not isinstance(b, bool)
    ):
        if not (
            a == b
            or (math.isnan(a) and math.isnan(b))
            or abs(a - b) <= tol * max(1.0, abs(b))
        ):
            out.append(f"{path}: {a!r} vs {b!r}")
    elif a != b:
        out.append(f"{path}: {str(a)[:60]!r} vs {str(b)[:60]!r}")
    return out


def compare_file(new: Path, ref: Path) -> str:
    """'identical', 'equal within 1e-9', or raise."""
    if sha(new) == sha(ref):
        return "identical"
    if ref.suffix == ".json":
        diffs = deep_diff(json.loads(new.read_text()), json.loads(ref.read_text()))
    else:
        read = (
            (lambda p: pd.read_parquet(p))
            if ref.suffix == ".parquet"
            else (lambda p: pd.read_csv(p, float_precision="round_trip"))
        )
        x, y = read(new), read(ref)
        diffs = []
        if list(x.columns) != list(y.columns) or len(x) != len(y):
            diffs.append(f"shape/columns differ: {x.shape} vs {y.shape}")
        else:
            for c in y.columns:
                if pd.api.types.is_numeric_dtype(
                    y[c]
                ) and pd.api.types.is_numeric_dtype(x[c]):
                    a, b = x[c].to_numpy(float), y[c].to_numpy(float)
                    bad = ~(
                        (a == b)
                        | (np.isnan(a) & np.isnan(b))
                        | (np.abs(a - b) <= TOLERANCE * np.maximum(1.0, np.abs(b)))
                    )
                    if bad.any():
                        diffs.append(f"{c}: {int(bad.sum())} values differ")
                elif not x[c].astype(str).equals(y[c].astype(str)):
                    diffs.append(f"{c}: values differ")
    if diffs:
        raise Mismatch(
            f"{ref.relative_to(ROOT)} does not reproduce: " + "; ".join(diffs[:5])
        )
    return "equal within 1e-9"


def compare_block(name: str, mine, ref) -> str:
    diffs = deep_diff(json.loads(json.dumps(mine, default=float)), ref)
    if diffs:
        raise Mismatch(f"{name} does not reproduce: " + "; ".join(diffs[:5]))
    return "equal within 1e-9"


def quiet(fn, *args, **kwargs):
    with contextlib.redirect_stdout(io.StringIO()):
        return fn(*args, **kwargs)


# ------------------------------------------------------------------ steps
def step_integrity(report):
    manifest = ROOT.parent / "MANIFEST.json"
    if not manifest.is_file():
        if ROOT.name == PUBLIC_SECTION:
            raise Mismatch("MANIFEST.json is missing from the public companion")
        report["integrity"] = (
            "MANIFEST.json not found (running inside the private repository); skipped"
        )
        return
    files = json.loads(manifest.read_text())["files"]
    prefix = ROOT.name + "/"

    def generated(rel: str) -> bool:
        parts = rel.split("/")
        return (
            "recomputed" in parts or "__pycache__" in parts or parts[-1] == ".DS_Store"
        )

    listed = {rel for rel in files if rel.startswith(prefix) and not generated(rel)}
    if not listed:
        raise Mismatch(f"MANIFEST.json lists no files under {prefix}")
    bad = sorted(
        rel
        for rel in listed
        if not (ROOT.parent / rel).is_file() or sha(ROOT.parent / rel) != files[rel]
    )
    if bad:
        raise Mismatch(f"files changed since the cut: {bad[:5]}")
    on_disk = {
        str(p.relative_to(ROOT.parent))
        for p in ROOT.rglob("*")
        if p.is_file() and not generated(str(p.relative_to(ROOT.parent)))
    }
    extra = sorted(on_disk - listed)
    if extra:
        raise Mismatch(f"files not in MANIFEST.json: {extra[:5]}")
    report["integrity"] = f"{len(listed)} files of this section match MANIFEST.json"


def step_recipes(report, inputs, work):
    from scripts import sloan_fullpaper_recipes as rec

    out = work / "recipes"
    quiet(rec.run, ROOT, inputs, out)
    ref = ART / "sloan-fullpaper-recipes-2026-11"
    res = {
        f: compare_file(out / f, ref / f)
        for f in ("summary.json", "ladder.csv", "metrics.csv", "rows_pool_A.parquet")
    }
    g0 = json.loads((out / "summary.json").read_text())["gates"]["G0_R1"]
    if g0["status"] != "passed":
        raise Mismatch(f"G0 (the submitted v10 numbers) did not reproduce: {g0}")
    report["recomputed"]["G0 (submitted v10 numbers)"] = {
        "status": g0["status"],
        "max_difference": g0["max_difference"],
    }
    report["recomputed"]["E1/E2 recipes and ladder"] = res
    return out


def step_decisions(report, inputs, work):
    from scripts import sloan_fullpaper_common as common
    from scripts import sloan_fullpaper_decisions as dec

    keyed = pd.read_csv(TABLES / "e7_keyed_forecasts.csv", float_precision="round_trip")
    halves = keyed[dec.KEY + ["even_rate", "odd_rate", "even_games", "odd_games"]]
    rows, features, _ = quiet(common.anchor_rows, ROOT, inputs)
    decision = quiet(dec.e7, rows, halves)
    calibrated = quiet(dec.e8, rows)
    tiers = quiet(dec.e9, features)
    out = work / "decide"
    out.mkdir(parents=True)
    rebuilt = rows[
        dec.KEY + ["league_dest", "cluster", dec.OUTCOME, *dec.MODELS]
    ].merge(halves, on=dec.KEY, validate="1:1")
    rebuilt.to_csv(out / "e7_keyed_forecasts.csv", index=False)
    decision["per_pool"].to_csv(out / "e7_pools.csv", index=False)
    calibrated["table"].to_csv(out / "e8_conformal.csv", index=False)
    tiers["table"].to_csv(out / "e9_league_tiers_full.csv", index=False)
    dec.club_csv(tiers["table"]).to_csv(out / "e9_league_tiers_club.csv", index=False)
    ref = ART / "sloan-fullpaper-decisions-2026-11-03"
    committed = json.loads((ref / "summary.json").read_text())
    rel = dec.reliability(halves, rows)
    res = {
        "forecasts in e7_keyed_forecasts.csv": compare_file(
            out / "e7_keyed_forecasts.csv", TABLES / "e7_keyed_forecasts.csv"
        ),
        **{
            f: compare_file(out / f, ref / f)
            for f in (
                "e7_pools.csv",
                "e8_conformal.csv",
                "e9_league_tiers_full.csv",
                "e9_league_tiers_club.csv",
            )
        },
        "summary e7": compare_block(
            "e7",
            {
                "pooled": decision["pooled"],
                "reliability": rel,
                "share_of_reachable_ordering": dec.reachable(
                    decision["pooled"]["all"], rel
                ),
                "licensed_d2": dec.licensed_d2(decision["pooled"]["all"]),
            },
            committed["e7"],
        ),
        "summary e8": compare_block("e8", calibrated["results"], committed["e8"]),
        "summary e9": compare_block(
            "e9", {k: v for k, v in tiers.items() if k != "table"}, committed["e9"]
        ),
        "summary mae": compare_block(
            "mae", {arm: common.mae(rows, arm) for arm in dec.MODELS}, committed["mae"]
        ),
    }
    report["recomputed"]["E7/E8/E9 decisions, intervals, league table"] = res
    report["carried"]["E7 per-game split and box-score reconciliation"] = (
        "the odd/even halves come from per-game box scores; published as e7_keyed_forecasts.csv (player-season aggregates), not recomputed"
    )
    return out


def step_amend1(report, inputs, work, recipes_out, decide_out):
    from scripts import sloan_fullpaper_amend1_decisions as am

    # Amendment 1 pins the bytes of its six inputs (am.PRIOR_FILES). The steps
    # above have already compared each recomputed input with the committed file
    # (byte-identical, or equal within 1e-9 when library versions move the last
    # digit), so the committed files are passed on and the step is checked on
    # its own. Which recomputed inputs were byte-identical is reported.
    prior = work / "prior"
    sources = {
        "decide-02/e7_keyed_forecasts.csv": (
            TABLES / "e7_keyed_forecasts.csv",
            decide_out / "e7_keyed_forecasts.csv",
        ),
        "decide-02/e9_league_tiers_full.csv": (
            ART / "sloan-fullpaper-decisions-2026-11-03/e9_league_tiers_full.csv",
            decide_out / "e9_league_tiers_full.csv",
        ),
        "decide-02/summary.json": (
            ART / "sloan-fullpaper-decisions-2026-11-03/summary.json",
            None,
        ),
        "recipes-01/rows_pool_A.parquet": (
            ART / "sloan-fullpaper-recipes-2026-11/rows_pool_A.parquet",
            recipes_out / "rows_pool_A.parquet",
        ),
        "recipes-01/summary.json": (
            ART / "sloan-fullpaper-recipes-2026-11/summary.json",
            recipes_out / "summary.json",
        ),
        "robustness-02/summary.json": (
            ART / "sloan-fullpaper-robustness-2026-11-03/summary.json",
            None,
        ),
    }
    if set(sources) != set(am.PRIOR_FILES):
        raise Mismatch("Amendment 1 inputs changed; update the reproduction chain")
    chain = {}
    for rel, (committed, recomputed) in sources.items():
        if sha(committed) != am.PRIOR_FILES[rel]:
            raise Mismatch(
                f"{committed.relative_to(ROOT)} is not the pinned input {rel}"
            )
        dst = prior / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(committed, dst)
        chain[rel] = (
            "committed (carried summary)"
            if recomputed is None
            else "recomputed byte-identical"
            if sha(recomputed) == sha(committed)
            else "recomputed equal within 1e-9 (checked above); committed bytes used"
        )
    out = work / "amend1"
    quiet(am.run, ROOT, inputs, prior, out)
    ref = ART / "sloan-fullpaper-amend1-decisions-2026-11"
    files = sorted(p.name for p in out.iterdir())
    report["recomputed"]["E10/E11/E12/E17 and the ACB-16 exchange-rate table"] = {
        f: compare_file(out / f, ref / f) for f in files
    }
    report["amendment1_inputs"] = chain
    report["carried"]["E17 noise floor (input to E17)"] = (
        "read from the robustness summary (E6 needs per-game rows)"
    )


def stage_amend1_inputs(prior: Path) -> None:
    """The six pinned inputs of Amendment 1 (am.PRIOR_FILES), copied from the committed files."""
    from scripts import sloan_fullpaper_amend1_decisions as am

    committed = {
        "decide-02/e7_keyed_forecasts.csv": TABLES / "e7_keyed_forecasts.csv",
        "decide-02/e9_league_tiers_full.csv": ART
        / "sloan-fullpaper-decisions-2026-11-03/e9_league_tiers_full.csv",
        "decide-02/summary.json": ART
        / "sloan-fullpaper-decisions-2026-11-03/summary.json",
        "recipes-01/rows_pool_A.parquet": ART
        / "sloan-fullpaper-recipes-2026-11/rows_pool_A.parquet",
        "recipes-01/summary.json": ART / "sloan-fullpaper-recipes-2026-11/summary.json",
        "robustness-02/summary.json": ART
        / "sloan-fullpaper-robustness-2026-11-03/summary.json",
    }
    if set(committed) != set(am.PRIOR_FILES):
        raise Mismatch("Amendment 1 inputs changed; update the reproduction chain")
    for rel, src in committed.items():
        if sha(src) != am.PRIOR_FILES[rel]:
            raise Mismatch(f"{src.relative_to(ROOT)} is not the pinned input {rel}")
        dst = prior / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dst)


EQUIVALENTS = "exchange_rate_acb16.csv"


def step_equivalents(report, inputs, work):
    """The table of European League Equivalents alone, rebuilt from the pinned inputs of
    Amendment 1 (the committed files, whose sha256 that amendment's script pins) and the
    published v10 tables, compared with the committed table and printed beside it."""
    from scripts import sloan_fullpaper_amend1_decisions as am

    prior, out = work / "prior", work / "amend1"
    stage_amend1_inputs(prior)
    quiet(am.run, ROOT, inputs, prior, out)
    ref = ART / "sloan-fullpaper-amend1-decisions-2026-11" / EQUIVALENTS
    verdict = compare_file(out / EQUIVALENTS, ref)
    mine = pd.read_csv(out / EQUIVALENTS, float_precision="round_trip")
    theirs = pd.read_csv(ref, float_precision="round_trip")
    report["recomputed"]["The table of European League Equivalents"] = {
        EQUIVALENTS: verdict
    }
    lines = [
        f"Table of European League Equivalents, rebuilt: {out / EQUIVALENTS}",
        f"committed: {ref.relative_to(ROOT)} ({verdict})",
        f"{'destination':<12}{'source league':<18}{'rebuilt':>9}{'95% interval':>20}{'committed':>11}{'95% interval':>20}",
    ]
    for (_, a), (_, b) in zip(mine.iterrows(), theirs.iterrows()):
        lines.append(
            f"{a.destination:<12}{a.source_league:<18}{a.acb16_equivalent_eff36:>9.3f}"
            f"{f'[{a.ci95_low:.3f}, {a.ci95_high:.3f}]':>20}{b.acb16_equivalent_eff36:>11.3f}"
            f"{f'[{b.ci95_low:.3f}, {b.ci95_high:.3f}]':>20}"
        )
    lines.append(
        "Each value: the domestic EFF/36 in that league that the league-aware forecast treats like "
        "a 16 in Spain's ACB, for an arrival in that competition."
    )
    report["equivalents_table"] = lines


def registration_list() -> Path | None:
    return next((p for p in REGISTRATION_LISTS if p.is_file()), None)


def step_registration(report):
    """Every row of the registration hash list names a file of this section with that sha256.

    The list gives file names without folders; this step finds each file under ``docs/`` and
    reports where it is. It proves that the documents here are the registered ones. When each
    was first made public is proved by the commit history of the hash list itself, not here."""
    listing = registration_list()
    if listing is None:
        if ROOT.name == PUBLIC_SECTION:
            raise Mismatch(
                "REGISTRATION_HASHES.md is missing from the public companion"
            )
        report["registration"] = "REGISTRATION_HASHES.md not found; skipped"
        return
    rows = [
        m.groups()
        for line in listing.read_text().splitlines()
        if (m := REGISTRATION_ROW.match(line))
    ]
    if not rows:
        raise Mismatch(f"{listing.name} has no rows")
    by_name: dict = {}
    for path in (ROOT / "docs").rglob("*"):
        if path.is_file():
            by_name.setdefault(path.name, []).append(path)
    found, gaps = {}, []
    for name, want in rows:
        hit = next((p for p in by_name.get(name, []) if sha(p) == want), None)
        if hit is None:
            gaps.append(
                f"{name}: "
                + (
                    "a file of this name is here, with another sha256"
                    if name in by_name
                    else "no file of this name is here"
                )
            )
        else:
            found[name] = str(hit.relative_to(ROOT))
    if gaps:
        raise Mismatch(
            f"{len(gaps)} of {len(rows)} rows of {listing.name} do not check: "
            + "; ".join(gaps[:5])
        )
    report["registration"] = (
        f"{len(rows)} rows of {listing.name}: every named file is in this section with the "
        "sha256 the list records"
    )
    report["registration_files"] = found


def step_survivorship(report):
    from scripts import sloan_fullpaper_survivorship as sv

    S = ART / "sloan-fullpaper-survivorship-2026-11"
    ref = json.loads((S / "summary.json").read_text())
    scored = pd.read_parquet(S / "e14_eff_rows.parquet")
    counts = {}
    eff = sv.scored_rows(scored, "eff_all_arrivals", counts)
    populations = {
        "anchor_8_plus": eff.loc[eff.games_dest >= sv.V10_FLOOR],
        "wide_3_games_60_minutes": eff.loc[
            (eff.games_dest >= sv.WIDE_GAMES) & (eff.minutes_dest >= sv.WIDE_MINUTES)
        ],
        "all_arrivals_1_plus": eff,
    }
    e14b, flat = {"scoring": counts}, []
    for name, frame in populations.items():
        frame = frame.reset_index(drop=True)
        descriptive = name == "all_arrivals_1_plus"
        block = {"n": len(frame), "descriptive": descriptive}
        for weighting in ("minutes_weighted",) if descriptive else sv.WEIGHTINGS:
            weight = "minutes_dest" if weighting == "minutes_weighted" else None
            contrasts = {
                c: sv.contrast_block(frame, *pair, weight=weight)
                for c, pair in sv.HEADLINE.items()
            }
            block[weighting] = {
                "ladder": sv.ladder(frame, weight=weight),
                "contrasts": contrasts,
                "pattern": {s: sv.headline_pattern(contrasts, s) for s in sv.SPECS},
            }
            flat += sv.flat_contrasts("E14b", name, weighting, contrasts)
        e14b[name] = block
    e14b["licence"] = sv.e14b_licence(e14b["wide_3_games_60_minutes"])
    share = pd.read_parquet(S / "e14c_share_rows.parquet").rename(
        columns={
            "share_src_xT": "pir_per36_src",
            "share_prior_hT": "prior_mean_pir36",
            "share_above_prior_aT": "above_own_prior",
            "share_dest_T": "pir_per36_dest",
        }
    )
    t_counts = {}
    t_all = sv.scored_rows(share, "t_all_arrivals", t_counts)
    t_anchor = t_all.loc[t_all.games_dest >= sv.V10_FLOOR].reset_index(drop=True)
    e14c = {"scoring": t_counts}
    for name, frame in (("all_arrivals_1_plus", t_all), ("anchor_8_plus", t_anchor)):
        contrasts = {
            c: sv.contrast_block(frame, *pair) for c, pair in sv.T_CONTRASTS.items()
        }
        e14c[name] = {
            "n": len(frame),
            "mean_T": float(frame.pir_per36_dest.mean()),
            "sd_T": float(frame.pir_per36_dest.std(ddof=1)),
            "ladder": sv.ladder(frame),
            "contrasts": contrasts,
        }
        flat += sv.flat_contrasts("E14c", name, "unweighted", contrasts)
    e14c["licence"] = sv.e14c_licence(
        e14c["all_arrivals_1_plus"]["contrasts"][sv.T_PRIMARY]
    )
    e14c["rotation"] = sv.rotation(t_all)
    e14c["rotation_anchor_8_plus"] = sv.rotation(t_anchor)
    work = Path(os.environ["SLOAN_REPRO_WORK"]) / "survivorship"
    work.mkdir(parents=True)
    pd.DataFrame(flat).to_csv(work / "e14_contrasts.csv", index=False)
    pd.DataFrame(
        [
            {"source_league": s, **v}
            for s, v in e14c["rotation"]["by_source_league"].items()
        ]
    ).to_csv(work / "e14c_rotation_by_source.csv", index=False)
    pd.DataFrame(sv.clean(sv.e14a(scored))["counts"]).to_csv(
        work / "e14a_counts.csv", index=False
    )
    report["recomputed"]["E14a/E14b/E14c survivorship and playing time"] = {
        "summary e14a": compare_block("e14a", sv.clean(sv.e14a(scored)), ref["e14a"]),
        "summary e14b": compare_block("e14b", sv.clean(e14b), ref["e14b"]),
        "summary e14c": compare_block(
            "e14c", sv.clean(e14c), {k: v for k, v in ref["e14c"].items() if k in e14c}
        ),
        **{
            f: compare_file(work / f, S / f)
            for f in (
                "e14_contrasts.csv",
                "e14c_rotation_by_source.csv",
                "e14a_counts.csv",
            )
        },
    }
    report["carried"]["E14 arrivals rebuild, G14 gate and exclusion counts"] = (
        "rebuilt from per-game files; the 808-row tables they produced are published and the analyses above are recomputed from them"
    )


def step_skills(report, inputs):
    from scripts import sloan_fullpaper_common as common
    from scripts import sloan_fullpaper_robustness as robust
    from scripts import sloan_fullpaper_skills as sk

    K = ART / "sloan-fullpaper-skills-2026-11"
    ref = json.loads((K / "summary.json").read_text())
    pairs, cohort = common.load_pool(inputs, "official_corrected")
    _, v10_summary = common.load_references(ROOT)
    keys = common.target_keys(v10_summary)
    targets = keys.merge(cohort, on=common.KEY, how="left", validate="1:1")
    work = Path(os.environ["SLOAN_REPRO_WORK"]) / "skills"
    work.mkdir(parents=True)
    a = quiet(sk.e15a, pairs)
    a.to_csv(work / "e15a_retention.csv", index=False)
    sk.e15a_licences(a).to_csv(work / "e15a_licences.csv", index=False)
    g15a = max(sk.g15a_differences(pairs).values())
    priors_table = pd.read_parquet(TABLES / "e15b_component_priors.parquet")
    joined = targets[common.KEY].merge(
        priors_table, on=common.KEY, how="left", validate="1:1"
    )
    priors = {c: joined[f"prior_{c}"].to_numpy(float) for c in sk.COMPONENTS}
    halves = pd.read_csv(TABLES / "e15b_split_halves.csv", float_precision="round_trip")
    b, offsets, boot = quiet(sk.e15b, targets, halves, priors)
    b.to_csv(work / "e15b_carryover.csv", index=False)
    offsets.to_csv(work / "e15b_source_offsets.csv", index=False)
    sk.figure_table(a, b).to_csv(work / "skills_travel_figure.csv", index=False)
    mine = {
        "targets": len(targets),
        "bootstrap": boot,
        "history_missing": {c: int(np.isnan(p).sum()) for c, p in priors.items()},
        "licences": sk.e15b_licences(b),
        "rule": sk.E15B_RULE,
    }
    report["recomputed"]["E15a/E15b which skills travel"] = {
        "G15a max difference": g15a,
        **{
            f: compare_file(work / f, K / f)
            for f in (
                "e15a_retention.csv",
                "e15a_licences.csv",
                "e15b_carryover.csv",
                "e15b_source_offsets.csv",
                "skills_travel_figure.csv",
            )
        },
        "summary e15b": compare_block("e15b", robust.clean(mine), ref["e15b"]),
    }
    report["carried"]["E15 corpus rebuild, G3 and box-score totals"] = (
        "need per-game rows; the split halves and career histories they produce are published (public-tables)"
    )


def step_vignettes(report, inputs, work):
    from scripts import sloan_fullpaper_vignettes as vg

    V = ART / "sloan-fullpaper-paper-v2-2026-11"
    out = work / "vignettes"
    quiet(
        vg.main,
        [
            "--cohort",
            str(inputs / "official_corrected/cohort.parquet"),
            "--forecasts",
            str(ART / "sloan-fullpaper-flexible-2026-11/e16_forecasts.csv"),
            "--tiers",
            str(
                ART / "sloan-fullpaper-amend1-decisions-2026-11/exchange_rate_acb16.csv"
            ),
            "--out",
            str(out),
        ],
    )
    mine = json.loads((out / "summary.json").read_text())
    ref = json.loads((V / "vignettes_summary.json").read_text())
    for blob in (mine, ref):
        blob.get("inputs", {}).pop("forecasts", None)
    report["recomputed"]["Vignettes (three 2025-26 arrivals)"] = {
        "vignettes.csv": compare_file(out / "vignettes.csv", V / "vignettes.csv"),
        "vignettes_summary.json (forecasts-file hash excluded: the published e16_forecasts.csv has its age column removed)": compare_block(
            "vignettes", mine, ref
        ),
    }


OLDER = ART / "sloan-fullpaper-older-seasons-paper-2026-11"


def step_older(report):
    """E27: re-score the printed arrival rows and compare with the printed numbers."""
    from scripts import sloan_fullpaper_older_seasons_paper as extract

    paper = json.loads((OLDER / "e27_paper.json").read_text())
    rows = pd.read_csv(OLDER / "e27_arrivals_printed.csv", dtype={"player_name": str})
    if len(rows) != paper["n"] or set(rows.league) != set(paper["leagues"]):
        raise Mismatch("E27: the printed rows are not the printed version's arrivals")
    gate = extract.reproduce_gate(rows, paper["comparisons"])
    report["recomputed"][
        f"E27 older-seasons test (Amendment 7; version {paper['printed_version']}, {paper['n']} arrivals)"
    ] = {
        "three comparisons, all arrivals and rare surnames": f"equal within {extract.TOLERANCE:g} (largest gap {gate['max_abs_gap']:.1e}); shuffled outcomes rejected"
    }


def step_equation(report):
    """Amendment 12, gate G30a: the equation printed in the paper is the model behind the forecasts."""
    import render_sloan_fullpaper as rnd

    d = rnd.load(ROOT)
    co = rnd.get(d["decide"], "e9/coefficients")
    frozen = ART / "sloan-fullpaper-p1-freeze-2026-11/p1_frozen_forecasts.parquet"
    gaps = rnd.equation_gaps(d, co, frozen)
    worst = max(gaps["reference"], gaps["equivalents"], gaps["frozen"])
    if worst > TOLERANCE:
        raise Mismatch(
            f"the printed equation is not the model: largest gap {worst:.1e}"
        )
    control = rnd.equation_gaps(
        d, {**co, "source_rate": co["source_rate"] + 0.01}, frozen
    )
    if (
        min(control["reference"], control["equivalents"], control["frozen"])
        <= TOLERANCE
    ):
        raise Mismatch("the equation gate did not reject a shifted coefficient")
    report["recomputed"][
        "The fitted equation of the league-aware forecast (Amendment 12, gate G30a)"
    ] = {
        "equation against committed forecasts": (
            f"{gaps['reference_rows']} reference forecasts, {gaps['equivalent_rows']} League Equivalents and "
            f"{gaps['rows']:,} frozen 2026-27 forecasts equal within {TOLERANCE:g} (largest gap {worst:.1e}); "
            "a coefficient shifted by 0.01 rejected"
        )
    }


def step_league_changes(report):
    """Rebuild E30's centred, move-weighted slope from signed pair-direction means."""
    directory = ART / "sloan-fullpaper-league-changes-2026-11"
    pairs = pd.read_csv(directory / "e30_league_pairs.csv")
    retained = json.loads((directory / "e30_summary.json").read_text())
    slopes = pd.read_csv(directory / "e30_slopes.csv").set_index("label")

    def check(label, subset, reference):
        # All moves in one direction share a predictor. Aggregation therefore
        # preserves both the centred cross-product and the predictor variance.
        x = np.concatenate((subset.predicted_change, -subset.predicted_change))
        y = np.concatenate((subset.mean_e_to_higher, subset.mean_e_to_lower))
        counts = np.concatenate((subset.n_up, subset.n_down))
        used = counts > 0
        x, y, w = x[used], y[used], counts[used]
        centred = x - np.average(x, weights=w)
        slope = np.sum(w * centred * (y - np.average(y, weights=w))) / np.sum(
            w * centred**2
        )
        result = {"slope": float(slope), "moves": int(w.sum())}
        compare_block(
            label,
            result,
            {"slope": reference["estimate"], "moves": reference["league_changes"]},
        )
        interval = slopes.loc[label, ["ci95_low", "ci95_high"]].tolist()
        compare_block(label + " retained interval", interval, reference["ci95"])
        report["recomputed"][f"E30 {label} from directional aggregates"] = result
        report["carried"][f"E30 {label} player-bootstrap interval"] = {
            "ci95": interval,
            "status": "Retained interval checked against the slope table; resampling players and refitting the stayer model require the withheld rows.",
        }

    check("all league changes", pairs, retained["primary"])
    spain = "spain-acb"
    without = pairs[
        (pairs.league_lower_equivalent != spain)
        & (pairs.league_higher_equivalent != spain)
    ]
    check("without " + spain, without, retained["S_b"][spain])


def step_published_table(report, inputs, work):
    """Amendment 15: E31a and the E31c frozen arm, recomputed from published files."""
    from scripts import sloan_fullpaper_published_tables as pt

    ref = ROOT / pt.TABLE_DIR
    table = ROOT / pt.TABLE
    out = work / "published_table"
    quiet(pt.run_e31a, ROOT, inputs, table, out)
    report["recomputed"][
        "E31a: a league table printed in 2015 as a rival (Amendment 15; exploratory)"
    ] = {
        name: compare_file(out / name, ref / name)
        for name in (
            "summary.json",
            "e31a_differences.csv",
            "e31a_coefficients.csv",
            "e31a_keyed_forecasts.csv",
        )
    }
    # E31c: the second frozen file is rebuilt from the pinned frozen file, the
    # published player-season tables and the published league table
    freeze_dir = ROOT / pt.FREEZE_DIR
    record = json.loads((freeze_dir / pt.E31C_RECORD).read_text())
    if sha(freeze_dir / pt.E31C_FILE) != record["forecast_sha256"]:
        raise Mismatch(
            "the frozen published-table forecasts do not match the sha256 recorded at their freeze"
        )
    frozen_out = work / "published_table_freeze"
    quiet(pt.run_freeze, ROOT, inputs, table, frozen_out)
    report["recomputed"][
        "E31c: the 2015-table forecast frozen for the 2026-27 test (Amendment 15)"
    ] = {
        pt.E31C_FILE: compare_file(
            frozen_out / pt.E31C_FILE, freeze_dir / pt.E31C_FILE
        ),
        "freeze_hash_check": f"the committed file equals the sha256 recorded in {pt.E31C_RECORD}",
    }
    page = ROOT / "converter/index.html"
    if page.is_file():
        import sloan_fullpaper_converter_page as converter

        if converter.build(ROOT) != page.read_text():
            raise Mismatch(
                "converter/index.html is not what the committed result files give"
            )
        report["recomputed"][
            "The converter page (equation, league numbers, gap guide)"
        ] = {"converter/index.html": "identical to a fresh build from the result files"}


P1_LABEL = "P1 freeze (2026-27 forecasts built from raw 2025-26 files)"
CARRIED_FILES = {
    "E3-E6 robustness (outcomes, destinations, seasons, E5b ages, E6 noise floor)": [
        "sloan-fullpaper-robustness-2026-11-03/summary.json",
        "sloan-fullpaper-robustness-2026-11-03/headline_contrasts.csv",
    ],
    "E13 linkage audit of 100 pairs (birthdates and raw API rosters)": [
        "sloan-fullpaper-linkage-audit-2026-11/e13_summary.json",
        "sloan-fullpaper-linkage-audit-2026-11/e13_drawn_keys.csv",
    ],
    "E25 second linkage audit of 300 pairs (Amendment 5; birthdates and raw API rosters; exploratory)": [
        "sloan-fullpaper-linkage-audit-e25-2026-11/e25_summary.json",
        "sloan-fullpaper-linkage-audit-e25-2026-11/e25_drawn_keys.csv",
    ],
    "E26 identity audit of the 674 forecast arrivals (Amendment 6; birthdates, raw game files and API lists; exploratory)": [
        "sloan-fullpaper-arrivals-audit-2026-11/e26_summary.json",
        "sloan-fullpaper-arrivals-audit-2026-11/e26_arrivals.csv",
        "sloan-fullpaper-arrivals-audit-2026-11/e26_comparisons.csv",
    ],
    "E27 older-seasons test: freeze, linking and gates (Amendment 7; league-site box scores)": [
        "sloan-fullpaper-older-seasons-paper-2026-11/e27_paper.json",
        "sloan-fullpaper-older-seasons-paper-2026-11/e27_arrivals_printed.csv",
    ],
    "E16 flexible models (age features, Proballers game files)": [
        "sloan-fullpaper-flexible-2026-11/summary.json",
        "sloan-fullpaper-flexible-2026-11/e16_models.csv",
        "sloan-fullpaper-flexible-2026-11/e16_club_win_share.csv",
    ],
    "E18-E23 (Amendment 3: forecast level, league biases, stability, gap guide, coverage, timing; exploratory)": [
        "sloan-fullpaper-amend3-2026-11/summary.json",
        "sloan-fullpaper-amend3-2026-11/e19_equivalents_by_refit.csv",
        "sloan-fullpaper-amend3-2026-11/e18_league_rebased.csv",
        "sloan-fullpaper-amend3-2026-11/e20_gap_bins.csv",
    ],
    "E24 (Amendment 4: league biases against a destination-aware forecast; exploratory)": [
        "sloan-fullpaper-amend4-2026-11/summary.json",
        "sloan-fullpaper-amend4-2026-11/e24_league_bias.csv",
    ],
    "E28 (Amendment 9: the league-aware forecast against the plain baselines; needs the older-season rows, which are not published; exploratory)": [
        "sloan-fullpaper-amend9-2026-11/summary.json",
        "sloan-fullpaper-amend9-2026-11/e28a_differences.csv",
        "sloan-fullpaper-amend9-2026-11/e28b_differences.csv",
        "sloan-fullpaper-amend9-2026-11/e28c_margin.csv",
    ],
    "E29 (Amendment 11: where the league table missed on the older arrivals; needs the older-season rows; descriptive)": [
        "sloan-fullpaper-amend11-2026-11/summary.json",
        "sloan-fullpaper-amend11-2026-11/e29_means.csv",
        "sloan-fullpaper-amend11-2026-11/e29_change.csv",
    ],
    "E33 (Amendment 22: the league changes with the stayer forecast fitted only on earlier seasons; needs the player-level league changes and stayer rows, which are not published; exploratory)": [
        "sloan-fullpaper-league-changes-chrono-2026-11/e33_summary.json",
        "sloan-fullpaper-league-changes-chrono-2026-11/e33_slopes.csv",
        "sloan-fullpaper-league-changes-chrono-2026-11/e33_by_season.csv",
        "sloan-fullpaper-league-changes-chrono-2026-11/e33_gates.json",
    ],
    "E34 (Amendment 23, rule 5: two published league scales on the older arrivals; needs the older-season rows, which are not published; exploratory)": [
        "sloan-fullpaper-published-scales-older-2026-11/summary.json",
        "sloan-fullpaper-published-scales-older-2026-11/e34_readings.csv",
        "sloan-fullpaper-published-scales-older-2026-11/gaussianhoops_2026_league_strength.json",
    ],
    P1_LABEL: [
        "sloan-fullpaper-p1-freeze-2026-11/freeze.json",
        "sloan-fullpaper-p1-freeze-2026-11/p1_frozen_forecasts.parquet",
    ],
}


def step_carried(report):
    import sloan_fullpaper_number_manifest as nm

    numbers = json.loads(NUMBERS.read_text())
    pinned = {f["path"]: f["sha256"] for f in numbers["files"].values()}
    for label, files in CARRIED_FILES.items():
        rows = {}
        for rel in files:
            path = ART / rel
            h = sha(path)
            ref = pinned.get(f"docs/research/artifacts/{rel}")
            if ref is not None and not nm.file_matches(
                ROOT, f"docs/research/artifacts/{rel}", ref
            ):
                raise Mismatch(f"{rel}: sha256 differs from the paper-number manifest")
            rows[rel] = f"sha256 {h[:16]}" + (" = paper-number manifest" if ref else "")
        report["carried"][label] = {
            "files": rows,
            "status": (
                "carried, not recomputed (sha256 checked by the integrity step, "
                "and against the paper-number manifest where it pins the file)"
            ),
        }
    freeze = json.loads(
        (ART / "sloan-fullpaper-p1-freeze-2026-11/freeze.json").read_text()
    )
    got = sha(ART / "sloan-fullpaper-p1-freeze-2026-11/p1_frozen_forecasts.parquet")
    if got != freeze["forecast_sha256"]:
        raise Mismatch(
            "P1 frozen forecasts do not match the sha256 recorded at the freeze"
        )
    inc = sha(
        ART / "sloan-fullpaper-p1-freeze-2026-11/p1_incumbency_2025_continental.parquet"
    )
    if inc != freeze["incumbency_sha256"]:
        raise Mismatch("P1 incumbency file does not match the freeze")
    report["carried"][P1_LABEL]["freeze_hash_check"] = (
        "p1_frozen_forecasts.parquet and the incumbency file equal the sha256 values recorded in freeze.json on 3 November 2026"
    )
    if P1_SCORE.is_file():
        score = json.loads(P1_SCORE.read_text())
        ref = pinned.get(str(P1_SCORE.relative_to(ROOT)))
        # the public copy names its five input files from data/raw/ on; REDACTIONS.json
        # records the sha256 of the committed record and of the copy here
        if ref is None or not nm.file_matches(
            ROOT, str(P1_SCORE.relative_to(ROOT)), ref
        ):
            raise Mismatch(
                "P1 score.json is not the file the paper-number manifest checks"
            )
        report["p1"] = (
            f"scored: status {score.get('status')}, n_scored {score.get('n_scored')}; score.json hash-checked (scoring needs 2026-27 raw files, so it is carried)"
        )
    else:
        report["p1"] = (
            "P1 pending: the 2026-27 frozen test has not been scored yet (no score.json in this cut)"
        )


def step_numbers(report):
    import sloan_fullpaper_number_manifest as nm

    manifest = json.loads(NUMBERS.read_text())
    res = nm.verify(ROOT, manifest)
    report["paper_numbers"] = {
        **res,
        "untraced_constants": [
            {"line": e["line"], "token": e["token"], "context": e["context"]}
            for e in manifest["numbers"]
            if e["status"] == "constant"
        ],
    }


def step_figures(report, work):
    """Figures are re-drawn and compared; a mismatch is reported, not fatal (fonts)."""
    import render_sloan_fullpaper as rnd

    paper_figures = rnd.paper_figures

    out = work / "render"
    # the author's render refuses a figure whose text reaches the edge of the image; here the
    # figures are only compared, and this machine's fonts may be wider than the author's
    paper_figures.EDGE_CHECKS = False
    try:
        quiet(rnd.render, ROOT, out)
    finally:
        paper_figures.EDGE_CHECKS = True
    ref = ROOT / "docs/paper/ssac27/rendered"
    report["figures"] = {
        p.name: (
            "identical"
            if sha(p) == sha(ref / "figures" / p.name)
            else "differs (re-drawn; check visually)"
        )
        for p in sorted((out / "figures").glob("*.png"))
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--work", type=Path, default=ROOT / "recomputed")
    ap.add_argument("--skip-figures", action="store_true")
    ap.add_argument(
        "--only",
        choices=("equivalents", "registration"),
        help="one item alone: the table of League Equivalents, or the registration hash list",
    )
    args = ap.parse_args(argv)
    if args.work.exists():
        shutil.rmtree(args.work)
    args.work.mkdir(parents=True)
    os.environ["SLOAN_REPRO_WORK"] = str(args.work)
    # the check of the registration list reads no table
    inputs = None if args.only == "registration" else v10_input_dir()
    report = {"inputs": str(inputs), "recomputed": {}, "carried": {}, "timings_s": {}}
    steps = [
        ("integrity", lambda: step_integrity(report)),
        (
            "recipes",
            lambda: report.__setitem__(
                "_recipes", step_recipes(report, inputs, args.work)
            ),
        ),
        (
            "decisions",
            lambda: report.__setitem__(
                "_decide", step_decisions(report, inputs, args.work)
            ),
        ),
        (
            "amendment1",
            lambda: step_amend1(
                report, inputs, args.work, report["_recipes"], report["_decide"]
            ),
        ),
        ("survivorship", lambda: step_survivorship(report)),
        ("skills", lambda: step_skills(report, inputs)),
        ("vignettes", lambda: step_vignettes(report, inputs, args.work)),
        ("older seasons", lambda: step_older(report)),
        (
            "published league table",
            lambda: step_published_table(report, inputs, args.work),
        ),
        ("league changes", lambda: step_league_changes(report)),
        ("equation", lambda: step_equation(report)),
        ("carried", lambda: step_carried(report)),
        ("registration hashes", lambda: step_registration(report)),
        ("paper numbers", lambda: step_numbers(report)),
    ]
    if not args.skip_figures:
        steps.append(("figures", lambda: step_figures(report, args.work)))
    if args.only == "equivalents":
        steps = [
            ("integrity", lambda: step_integrity(report)),
            (
                "equivalents table",
                lambda: step_equivalents(report, inputs, args.work),
            ),
        ]
    elif args.only == "registration":
        steps = [
            ("integrity", lambda: step_integrity(report)),
            ("registration hashes", lambda: step_registration(report)),
        ]
    failed, failed_step, outcome = None, None, {}
    for name, fn in steps:
        t = time.time()
        print(f"[{name}] ...", flush=True)
        try:
            fn()
        except Exception as error:  # noqa: BLE001 -- recorded and reported
            failed, failed_step = f"{name}: {type(error).__name__}: {error}", name
            outcome[name] = "FAILED"
            print(f"[{name}] FAILED", flush=True)
            break
        report["timings_s"][name] = round(time.time() - t, 1)
        outcome[name] = f"ok ({report['timings_s'][name]} s)"
        print(f"[{name}] {outcome[name]}", flush=True)
    report["steps"] = {name: outcome.get(name, "not run") for name, _ in steps}
    report.pop("_recipes", None)
    report.pop("_decide", None)
    report["status"] = "failed" if failed else "passed"
    report["failure"] = failed
    (args.work / "report.json").write_text(
        json.dumps(report, indent=2, default=str) + "\n"
    )
    if report["recomputed"]:
        print("\nRECOMPUTED from published tables:")
    for k, v in report["recomputed"].items():
        print(
            f"  {k}: "
            + ", ".join(
                sorted({str(x) for x in (v.values() if isinstance(v, dict) else [v])})
            )[:160]
        )
    if report["carried"]:
        print("CARRIED (hash-checked, not recomputed):")
    for k in report["carried"]:
        print(f"  {k}")
    if "p1" in report:
        print(report["p1"])
    if "paper_numbers" in report:
        pn = report["paper_numbers"]
        print(
            f"Paper numbers: {pn['tokens']} number tokens; {pn.get('traced', 0)} traced to a file and key ({pn['keys_checked']} keys re-read), {pn.get('literal', 0)} literals, {pn.get('constant', 0)} typed constants"
        )
    if "figures" in report:
        print("Figures: " + ", ".join(f"{k} {v}" for k, v in report["figures"].items()))
    if "registration" in report:
        print("Registrations: " + report["registration"])
    for line in report.get("equivalents_table", []):
        print(line)
    if failed:
        # the failure's text once, capped; the whole text is in the report
        text = (
            failed
            if len(failed) <= FAILURE_TEXT_LIMIT
            else (
                failed[:FAILURE_TEXT_LIMIT]
                + f" ... [{len(failed) - FAILURE_TEXT_LIMIT:,} more characters in "
                + f'{args.work / "report.json"}, under "failure"]'
            )
        )
        print(f"\nFAILURE in step {text}")
    print("\nSteps:")
    for name, result in report["steps"].items():
        print(f"  {name:<24} {result}")
    what = (
        "FULL-PAPER REPRODUCTION"
        if args.only is None
        else f"CHECK OF {args.only.upper()}"
    )
    if failed:
        after = [n for n, r in report["steps"].items() if r == "not run"]
        print(
            f'\n{what} FAILED at step "{failed_step}"'
            + (f"; {len(after)} later step(s) did not run" if after else "")
        )
    else:
        print(f"\n{what} PASSED")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
