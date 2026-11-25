#!/usr/bin/env python3
"""Render the Amendment 11 results note (E29) from committed outputs.

Reads only the committed outputs of scripts/sloan_fullpaper_amend11.py and its
trimmed run receipt, and writes docs/research/sloan-fullpaper-amend11-2026-11-16.md.
No number is typed here: every value is formatted from those files, and every
quoted result sentence is the generator's registered wording. E29 is
DESCRIPTIVE: it shows where the forecast missed and states no cause. Only the
older-seasons version the paper prints under Amendment 7's permission rule is
in those files, so only that version is in the note.
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
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts import report_sloan_fullpaper_amend9 as e28_report  # noqa: E402

ARTIFACTS = Path("docs/research/artifacts/sloan-fullpaper-amend11-2026-11")
NOTE = Path("docs/research/sloan-fullpaper-amend11-2026-11-16.md")
CSV_FILES = ("e29_means.csv", "e29_change.csv")
AMENDMENT = "docs/research/sloan-full-paper-preregistration-amendment-11-2026-11-16.md"

table = e28_report.table
gates_table = e28_report.gates_table
WEIGHTING_NAMES = e28_report.WEIGHTING_NAMES
VERSION_NAMES = e28_report.VERSION_NAMES
QUANTITY_NAMES = {
    "move": "Move made by the league table",
    "error_without_table": "Error without the table",
    "error_with_table": "Error with the table",
}
ALL = "all"
ALL_NAME = "All arrivals"
READINGS = {
    "includes_zero": "includes zero",
    "excludes_zero": "excludes zero",
    "not_estimable": "not estimable",
}
#: What happened, in order. Run names and commits come from the receipt.
EVENTS = (
    "Amendment 11 was written on 16 November 2026, approved by Amir and pushed alone (commit `{amendment}`) before any E29 code existed.",
    "The generator and its unit tests (synthetic data) were written. Before the generator was committed it was run once on the staged inputs outside the retained-run machinery, to check that the gates execute. From that run only the gate records (status, largest difference, the number of arrivals per printed league), the output file and column names and the absence of withheld values in the public files were read; no mean, interval or change was read. The generator was not changed after it.",
    "The generator was committed (commit `{generator}`) and run once as retained run `{run}` from the clean committed tree. The run finished with status {status}; every gate passed and every negative control was rejected as required. No retained run of the generator failed and none was repeated.",
    "No specification choice was made or changed after a result was seen. Every mean, interval and change the run produced for the printed version is in this note; standard errors are in the committed CSV tables.",
    "This note is rendered by `scripts/report_sloan_fullpaper_amend11.py` from the committed outputs, in its own retained run.",
)


def num(value: float, signed: bool = True) -> str:
    return e28_report.num(value, 2, signed)


def span(ci95) -> str:
    return e28_report.span(ci95, 2)


def cell(record: dict) -> str:
    if record["ci95"] is None:
        return f"{num(record['mean'])} (not estimable)"
    return f"{num(record['mean'])} ({span(record['ci95'])})"


def row_name(key: str, leagues: dict) -> str:
    name = ALL_NAME if key == ALL else leagues[key]
    return name[0].upper() + name[1:]


def means_table(rows: dict, leagues: dict, weighting: str) -> list:
    body = [
        [
            row_name(key, leagues),
            row["n"],
            *(cell(row["means"][q][weighting]) for q in QUANTITY_NAMES),
        ]
        for key, row in ((k, rows[k]) for k in (*leagues, ALL))
    ]
    return table(["Source league", "n", *QUANTITY_NAMES.values()], body)


def population_section(rows: dict, leagues: dict) -> list:
    out = []
    for weighting, label in WEIGHTING_NAMES.items():
        out += [f"{label}:", ""]
        out += means_table(rows, leagues, weighting)
        out.append("")
    return out


def change_table(block: dict, leagues: dict) -> list:
    body = []
    for key in leagues:
        for weighting, label in WEIGHTING_NAMES.items():
            r = block[key][weighting]
            body.append(
                [
                    row_name(key, leagues),
                    label,
                    r["n_older"],
                    r["n_benchmark"],
                    num(r["older"]),
                    num(r["benchmark"]),
                    num(r["change"]),
                    span(r["ci95"]) if r["ci95"] else "not estimable",
                    r["df"] if r["df"] is not None else "n/a",
                    num(r["detectable_80"], False) if r["detectable_80"] else "n/a",
                    READINGS[r["reading"]],
                ]
            )
    return table(
        [
            "Source league",
            "Weighting",
            "n, older",
            "n, 2020-2025",
            "Error without the table, older",
            "Error without the table, 2020-2025",
            "Change (older minus 2020-2025)",
            "95% interval",
            "df",
            "Detectable with 80% power",
            "Reading",
        ],
        body,
    )


def sentence_lines(block: dict, leagues: dict) -> list:
    out = []
    for key in leagues:
        for weighting, label in WEIGHTING_NAMES.items():
            entry = block[key][weighting]
            where = f"{row_name(key, leagues)}, {label.lower()}"
            if entry.get("sentence"):
                out.append(f'- {where}: "{entry["sentence"]}".')
            else:
                out.append(f"- {where}: {entry['note']}.")
    return out


def error_phrase(record: dict) -> str:
    """A signed mean error in plain words, with its interval."""
    where = "below" if record["mean"] < 0 else "above"
    return f"{num(abs(record['mean']), False)} EFF/36 {where} the outcome (interval {span(record['ci95'])})"


def plain_league(key: str, leagues: dict, older: dict, recent: dict) -> list:
    out = []
    for label, rows in (("older arrivals", older), ("arrivals of 2020-2025", recent)):
        m = rows[key]["means"]
        for weighting, how in (
            ("unweighted", ""),
            ("minutes_weighted", ", weighted by destination minutes"),
        ):
            move = m["move"][weighting]["mean"]
            verb = "lowered" if move < 0 else "raised"
            subject = "all arrivals" if key == ALL else f"arrivals from {leagues[key]}"
            out.append(
                f"- {row_name(key, leagues)}, {label} (n = {rows[key]['n']}){how}: the league table {verb} the forecast for {subject} by {num(abs(move), False)} EFF/36 on average. "
                f"Without the table the forecast was {error_phrase(m['error_without_table'][weighting])}; with it, {error_phrase(m['error_with_table'][weighting])}."
            )
    return out


def condition_lines(licences: dict) -> list:
    c = licences["consistent_with"]
    weighted = (
        "The change weighted by destination minutes excludes zero for at least one league, but that alone does not meet the condition."
        if c["condition_met_minutes_weighted"] and not c["condition_met"]
        else "The change weighted by destination minutes excludes zero for at least one league as well."
        if c["condition_met_minutes_weighted"]
        else "The change weighted by destination minutes does not exclude zero for any league either."
    )
    if c["condition_met"]:
        first = f'The unweighted change between periods excludes zero for at least one league, so the registered condition is met and the paper may write: "{c["registered_wording"]}".'
    else:
        first = f'The unweighted change between periods does not exclude zero for any league, so the registered condition is not met. The paper may not write "consistent with league numbers that change over time"; it says that {c["registered_wording"]}.'
    return [f"- {first} {weighted}", f"- Rule applied: {c['rule']}."]


def provenance(summary: dict, receipt: dict) -> list:
    return [
        f"- Generator `{receipt['entrypoint']}` (commit `{receipt['generator_commit'][:9]}`, sha256 `{receipt['generator_sha256'][:16]}…`), amendment commit `{summary['amendment_commit'][:9]}` (file sha256 `{summary['amendment_sha256'][:16]}…`), retained run `{receipt['run_dir']}`, {receipt['inputs']} input files, {receipt['code_files']:,} code files, status {receipt['status']}.",
        f"- Inputs: the pinned v10 pairs and cohort (pool A), the committed scored rows and summary of the Amendment 7 scoring run, the Amendment 7 paper extract, the committed E28 summary, the committed Amendment 4 tables, the release flag, and the frozen older-season forecasts (sha256 `{summary['input_sha256']['frozen_older_season_forecasts'][:16]}…`). The run recorded {receipt['withheld_outputs']['files']} output file that is not committed: {receipt['withheld_outputs']['note']}.",
    ]


def render(artifacts: Path, receipt: dict) -> str:
    s = json.loads((Path(artifacts) / "summary.json").read_text())
    leagues = s["leagues"]
    older, recent, change = s["e29a"]["rows"], s["e29b"]["rows"], s["e29c"]["rows"]
    lic = s["licences"]
    q = s["estimator"]["quantities"]
    out = [
        "# SSAC27 full paper: Amendment 11 results (E29)",
        "",
        "**DESCRIPTIVE.** Every outcome used here had been seen, and part of the table had been seen before registration (see below). E29 shows where the forecast missed. It does not show why, and this note states no cause. Every number below is formatted by `scripts/report_sloan_fullpaper_amend11.py` from committed run outputs; every quoted result sentence is the generator's registered wording.",
        "",
        f"Pre-registration: `{AMENDMENT}`, pushed alone before its generator existed.",
        "",
        "## What E29 asks",
        "",
        "E28 found that on the older arrivals the league table did not help. E29 shows where the forecast went wrong, league by league. For each source league it gives three averages: how far the league table moves the forecast, how far the forecast was from the outcome without the table, and how far with it. A negative error means the forecast was below what the arrivals delivered. The same three averages are given for the same leagues on the arrivals of 2020-2025, and for all arrivals of each period.",
        "",
        "## Results in plain words",
        "",
    ]
    for key in (*leagues, ALL):
        out += plain_league(key, leagues, older, recent)
    for key in leagues:
        r = change[key]["unweighted"]
        if r["ci95"]:
            out.append(
                f"- {row_name(key, leagues)}, change between periods: {num(r['change'])} EFF/36 (interval {span(r['ci95'])}; {READINGS[r['reading']]}). The smallest change this comparison could detect with 80% power is {num(r['detectable_80'], False)}."
            )
    out += condition_lines(lic)
    out += ["", "## Specification", ""]
    out += table(
        ["Field", "Registered choice"],
        [
            ["Unit", "One arrival: player × destination season."],
            [
                "Population",
                f"(a) The older-seasons arrivals of Amendment 7, in {VERSION_NAMES[s['printed_version']]} (the version the paper prints), n = {s['e29a']['n']}. (b) The {s['e29b']['n']} benchmark arrivals of 2020-2025. Rows: each source league of the printed older version, and all arrivals of each population.",
            ],
            [
                "Estimator",
                f"Per source league and population, three means in EFF/36: the move ({q['move']}); the error without the table ({q['error_without_table']}); the error with the table ({q['error_with_table']}). Each unweighted and weighted by destination minutes. Per source league, the change between periods: {s['estimator']['change']}. No model is refitted and nothing is re-scored.",
            ],
            ["Null", "Zero for each mean error and for the change between periods."],
            ["Filter", "None beyond each population's registered rules."],
            [
                "Key",
                "`player_name` × `season_dest` on the 674; API person code × destination season on the older seasons.",
            ],
            [
                "Uncertainty",
                f"{s['estimator']['interval'][0].upper()}{s['estimator']['interval'][1:]}. For the change between periods the two samples are treated as independent. Detectable effect with 80% power: {s['estimator']['detectable_80']}.",
            ],
        ],
    )
    out += ["", "## What had been seen", "", "Seen before Amendment 11 was registered:"]
    out += [f"- {x}" for x in s["exposure"]["seen_before_registration"]]
    out += ["", "Already on file before registration:"]
    out += [f"- {x}." for x in s["exposure"]["on_file_before_registration"]]
    out += ["", "Not seen before this run:"]
    out += [f"- {x}" for x in s["exposure"]["not_seen_before_this_run"]]
    out += ["", s["further_reading"], "", "## Three limits printed with the table", ""]
    out += [f"{k}. {limit}" for k, limit in enumerate(lic["limits"], 1)]
    out += ["", "## Gates", ""]
    out += gates_table(s)
    out += [
        "",
        "G29a comes first: it reproduces the four committed E28b differences on the older arrivals before anything else is computed; its negative control shuffles the outcome column. G29b reproduces the committed errors of the two forecasts and the committed G_D with its interval on the 674; its negative control shifts one forecast column by 0.01. G29c checks, in each population, that the league means weighted by their numbers of arrivals add up to the mean of all arrivals and that the move equals the error with the table minus the error without it; its negative control drops one league's rows. G29d checks that no number of the withheld version is in the summary or in either table; its negative control plants one. The other gates are additions: the submitted numbers (G0, scope), the frozen forecasts, the Amendment 7 comparisons, the explicit league names of the two populations, and the committed Amendment 4 means on the 674.",
        "",
        f"## E29a: the older arrivals ({s['e29a']['n']} arrivals)",
        "",
        f"Printed here: {VERSION_NAMES[s['printed_version']]}. {s['further_reading']} Each cell: mean in EFF/36 (95% interval).",
        "",
    ]
    out += population_section(older, leagues)
    out += [
        f"## E29b: the arrivals of 2020-2025 ({s['e29b']['n']} arrivals)",
        "",
        "The same leagues, from the committed walk-forward forecasts. Each cell: mean in EFF/36 (95% interval).",
        "",
    ]
    out += population_section(recent, leagues)
    out += ["## E29c: the change between periods", ""]
    out += change_table(change, leagues)
    out += ["", "## Registered sentences", "", "Each league on the older arrivals:", ""]
    out += sentence_lines(lic["leagues"], leagues)
    out += ["", "The change between periods:", ""]
    out += sentence_lines(lic["change"], leagues)
    out += ["", "What the paper may add:", ""]
    out += condition_lines(lic)
    out += [
        f'- The caveat that travels with every one of these sentences: "{lic["caveat"]}".',
        f"- {lic['no_cause']}",
    ]
    if "withheld" in s:
        out += [
            "",
            f"Both versions of the older-seasons test were computed in this run. Everything that depends on the other version ({s['withheld']['version']}), including the rows of its extra league in both populations, is withheld, not for its result: {s['withheld']['reason']}. Nothing from it is in this note or in any committed file.",
        ]
    out += ["", "## Order of events", ""]
    facts = {
        "amendment": s["amendment_commit"][:9],
        "generator": receipt["generator_commit"][:9],
        "run": receipt["run_dir"],
        "status": receipt["status"],
    }
    out += [f"{k}. {event.format(**facts)}" for k, event in enumerate(EVENTS, 1)]
    out += ["", "## Reproduction", ""]
    out += provenance(s, receipt)
    return "\n".join(out) + "\n"


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--artifacts", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    receipt = json.loads((args.artifacts / "generator-receipt.json").read_text())
    note = render(args.artifacts, receipt)
    args.out.mkdir(parents=True, exist_ok=False)
    (args.out / NOTE.name).write_text(note)
    print(f"{NOTE.name}: {len(note.splitlines())} lines")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
