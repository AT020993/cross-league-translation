#!/usr/bin/env python3
"""Render the E33 results note (Amendment 22) from committed outputs.

Reads only the committed outputs of scripts/sloan_fullpaper_league_changes_chrono.py
and writes docs/research/sloan-fullpaper-league-changes-chrono-2026-11-19.md.
No result is typed here: every value is formatted from those files. E33 is
EXPLORATORY: the outcomes it uses had been read by the scoring run of E30.
"""

# ruff: noqa: E501 -- table rows and sentences
from __future__ import annotations

if __name__ == "__main__":
    import sys as _sys
    from pathlib import Path as _Path

    _sys.path.insert(0, str(_Path(__file__).resolve().parents[1]))
    from src.research.execution import enter as _enter

    _enter(__file__)

import argparse
import csv
import json
from pathlib import Path

ARTIFACTS = Path(
    "docs/research/artifacts/sloan-fullpaper-league-changes-chrono-2026-11"
)
NOTE = Path("docs/research/sloan-fullpaper-league-changes-chrono-2026-11-19.md")
AMENDMENT = "docs/research/sloan-full-paper-preregistration-amendment-22-2026-11-19.md"
#: What happened, in order. These are records of events, not results.
EVENTS = (
    "Amendment 22 was written on 19 November 2026, after the league-changes test (E30) had been scored and its sensitivities seen. Amir accepted it; it was pushed alone (commit `1e69136a`, 18:28:29 UTC) and merged into `main` (pull request #3684, `22e3a414`).",
    "The generator and its tests on made-up frames were written after that push and committed (commit `3c4ddc27`). Before the commit, the gates that read no outcome were tried once outside a retained run; they passed.",
    "The gates were run as retained run `league-changes-chrono-gates-01` and their record committed (commit `f5b68ffc`). The run reads no rate of a league changer: of the scored file it reads the key, the season and the two leagues.",
    "The row of Amendment 22 was added to the public hash list (public commit `b183a0b`, tag `registration-hashes-2026-11-19a`, 19 November 2026, about 19:10 UTC; the tag was removed on 26 November 2026 with the other earlier tags, and the commit stands).",
    "E33 was then run once, as retained run `league-changes-chrono-01`. No rule was changed after the result was seen, and no other variant of the check was run.",
)
CASES = {
    "same": "Same: the interval of the slope lies above zero and the interval of the difference includes zero",
    "different_lower": "Different, lower: the interval of the difference lies below zero",
    "different_higher": "Different, higher: the interval of the difference lies above zero",
    "not_above_zero": "Not above zero: the interval of the slope includes zero",
}
GATE_NAMES = {
    "G33a_inputs": "G33a: every pinned file equals its sha256",
    "G33b_same_rows": "G33b: the same 2,083 rows; the frozen and the scored file agree row by row",
    "G33c_reproduction": "G33c: the code returns sensitivity (7) as retained, estimate and interval",
    "G33d_cutoff": "G33d: every stayer forecast uses only earlier outcome seasons",
    "G33e_planted_slope": "G33e: a planted slope of 1.0 on made-up outcomes is recovered",
}


#: The keys of a receipt as committed beside the outputs. The retained run's own receipt
#: lists every private script of the repository and local absolute paths; this form keeps
#: what identifies the run and is safe to publish (the form the E30 folder uses).
RECEIPT_KEYS = (
    "arguments",
    "code_files",
    "entrypoint",
    "generator_commit",
    "generator_sha256",
    "input_sha256",
    "inputs",
    "outputs",
    "returncode",
    "run_dir",
    "selections",
    "snapshot",
    "source_seasons",
    "status",
)


def trim_receipt(full: dict, *, run_dir: str, generator_commit: str) -> dict:
    """The committed form of a retained run's receipt: no local path, no private file list.

    ``generator_commit`` is the commit of the tree the run was started from; it is not in
    the run's receipt and is checked by the caller against the receipt's code hashes.
    """
    entrypoint = full["entrypoint"]
    arguments = [
        Path(a).name if a.startswith("/") else a for a in map(str, full["arguments"])
    ]
    trimmed = {
        "arguments": arguments,
        "code_files": len(full["code"]),
        "entrypoint": entrypoint,
        "generator_commit": generator_commit,
        "generator_sha256": full["code"][entrypoint],
        "input_sha256": dict(sorted(full["inputs"].items())),
        "inputs": len(full["inputs"]),
        "outputs": dict(sorted(full["outputs"].items())),
        "returncode": full["returncode"],
        "run_dir": run_dir,
        "selections": list(full["selections"]),
        "snapshot": full["snapshot"],
        "source_seasons": list(full["source_seasons"]),
        "status": full["status"],
    }
    assert tuple(sorted(trimmed)) == RECEIPT_KEYS
    return trimmed


def num(x: float, digits: int = 3) -> str:
    return f"{x:.{digits}f}".replace("-", "−")


def span(ci, digits: int = 3) -> str:
    return f"{num(ci[0], digits)} to {num(ci[1], digits)}"


def table(header, rows) -> str:
    lines = ["| " + " | ".join(header) + " |", "|" + "---|" * len(header)]
    lines += ["| " + " | ".join(str(c) for c in row) + " |" for row in rows]
    return "\n".join(lines)


def controls(gate: dict) -> str:
    found = [
        f"{key.replace('negative_control_', '').replace('_', ' ')}: {value}"
        for key, value in gate.items()
        if key.startswith("negative_control") and isinstance(value, str)
    ]
    if "negative_control_shuffled_gap" in gate:
        found.append(
            "gap shuffled across the made-up moves: interval "
            + span(gate["negative_control_shuffled_gap"]["ci95"])
            + ", includes zero as required"
        )
    if "files" in gate:
        found.append(
            "one byte changed: "
            + ", ".join(
                sorted(
                    {f["negative_control_changed_byte"] for f in gate["files"].values()}
                )
            )
        )
    return "; ".join(found)


def render(artifacts: Path) -> str:
    r = json.loads((artifacts / "e33_summary.json").read_text())
    with (artifacts / "e33_by_season.csv").open() as handle:
        seasons = list(csv.DictReader(handle))
    c, pooled, d = r["cutoff"], r["pooled"], r["difference"]
    by = r["season_intercepts"]
    planted = r["gates"]["G33e_planted_slope"]
    amendment = r["amendment_22"]
    parts = [
        "# SSAC27 full paper: the league-changes check with the stayer forecast fitted only on earlier seasons (E33)",
        f"Pre-registration: `docs/research/sloan-full-paper-preregistration-2026-11-03.md`, Amendment 22 (`{amendment['path']}`, sha256 `{amendment['sha256']}`). "
        "E33 is **exploratory**: the outcomes it uses had been read by the scoring run of E30. It changes no registered result, sentence or case of E30.",
        "## Specification",
        table(
            ["Field", "Registered choice"],
            [
                [
                    "Unit",
                    "One league change, as in Amendment 14. Each move has equal weight",
                ],
                [
                    "Population",
                    f"The {r['league_changes']:,} league changes of sensitivity (7) of E30: arrival seasons 2020 to 2025, with the table gap refitted only on arrivals before the season of the move; {r['players']:,} players",
                ],
                [
                    "Estimator",
                    "Step 1, for each arrival season t: ordinary least squares of the stayers' next-season rate on an intercept, x, h and a, on stayer pairs whose outcome season is before t. Step 2: ordinary least squares, with an intercept, of the league changers' unexplained change on the refitted gap",
                ],
                ["Null", "Slope zero; for the difference from sensitivity (7): zero"],
                ["Filter", "Rows of the frozen file with a finite refitted gap"],
                ["Key", "`player_name` × `season_from`, the key of E30"],
                [
                    "Uncertainty",
                    f"The bootstrap of E30: {r['players_resampled']:,} players resampled, {r['bootstrap_draws']:,} draws, seed {r['seed']}, every stayer forecast refitted in every draw; percentile interval",
                ],
            ],
        ),
        "## Result",
        f"**Case: {CASES[r['case']]}.**",
        table(
            ["Quantity", "League changes", "Slope", "95% interval"],
            [
                [
                    "E33: stayer forecast fitted only on seasons before each move",
                    f"{r['league_changes']:,}",
                    num(c["estimate"]),
                    span(c["ci95"]),
                ],
                [
                    "Sensitivity (7), reproduced: stayer forecast fitted on all seasons",
                    f"{r['league_changes']:,}",
                    num(pooled["estimate"]),
                    span(pooled["ci95"]),
                ],
                [
                    "Difference, E33 minus sensitivity (7), in the same draws",
                    f"{r['league_changes']:,}",
                    num(d["estimate"]),
                    span(d["ci95"]),
                ],
                [
                    "E33 with one intercept per arrival season (secondary)",
                    f"{r['league_changes']:,}",
                    num(by["cutoff"]["estimate"]),
                    span(by["cutoff"]["ci95"]),
                ],
                [
                    "Sensitivity (7) with one intercept per arrival season (secondary)",
                    f"{r['league_changes']:,}",
                    num(by["pooled"]["estimate"]),
                    span(by["pooled"]["ci95"]),
                ],
            ],
        ),
        f"The standard deviation of the {r['bootstrap_draws']:,} differences is {num(d['sd'], 4)}; a difference of {num(d['detectable_80'])} would have been detected with 80% power (2.80 standard deviations). "
        "The interval of the difference comes from the same draws as the two slopes, so it does not rest on comparing two overlapping intervals.",
        "## The stayer forecast by arrival season",
        table(
            [
                "Arrival season",
                "League changes",
                "Players",
                "Stayer pairs used",
                "Latest stayer outcome season",
                "Intercept",
                "x",
                "h",
                "a",
            ],
            [
                [
                    row["arrival_season"],
                    row["league_changes"],
                    row["players"],
                    f"{int(row['stayer_training_rows']):,}",
                    row["latest_stayer_outcome_season"],
                    num(float(row["intercept"])),
                    num(float(row["x"])),
                    num(float(row["h"])),
                    num(float(row["a"])),
                ]
                for row in seasons
            ],
        ),
        "## Gates",
        table(
            ["Gate", "Status", "Negative control"],
            [
                [
                    GATE_NAMES[name],
                    r["gates"][name]["status"],
                    controls(r["gates"][name]),
                ]
                for name in GATE_NAMES
            ],
        ),
        f"G33e in numbers: planted 1.0 came back as {num(planted['planted_slope_one']['slope'])} (interval {span(planted['planted_slope_one']['ci95'])}); "
        f"planted 0.0 as {num(planted['planted_slope_zero']['slope'])} (interval {span(planted['planted_slope_zero']['ci95'])}). The made-up outcomes use a noise spread of {num(planted['noise_sd'], 2)} EFF/36, the residual spread of the stayer forecast.",
        "## Order of events",
        "\n".join(f"{i}. {event}" for i, event in enumerate(EVENTS, 1)),
        "## What this does and does not show",
        "\n".join(
            [
                "* It removes the last overlap in time of sensitivity (7): neither the league table nor the stayer forecast of a league change uses a season at or after the move.",
                "* It is a further reading of outcomes that had been read. It is exploratory and is labelled so wherever the paper prints it.",
                "* It does not remove players who appear both among the arrivals that fit the table and among the league changers.",
                "* Its interval holds the refitted table values fixed, as the interval of sensitivity (7) does.",
                "* The limits of E30 stand: league changers are not a random sample, role and minutes change with a move, players are linked by name, and the box scores are the raw Proballers files.",
            ]
        ),
    ]
    return "\n\n".join(parts) + "\n"


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--artifacts", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    note = render(args.artifacts)
    args.out.mkdir(parents=True, exist_ok=False)
    (args.out / NOTE.name).write_text(note)
    print(f"{NOTE.name}: {len(note.splitlines())} lines")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
