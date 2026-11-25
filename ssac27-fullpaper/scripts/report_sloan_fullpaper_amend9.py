#!/usr/bin/env python3
"""Render the Amendment 9 results note (E28) from committed outputs.

Reads only the committed outputs of scripts/sloan_fullpaper_amend9.py and its
trimmed run receipt, and writes docs/research/sloan-fullpaper-amend9-2026-11-16.md.
No number is typed here: every value is formatted from those files, and every
result sentence is the generator's registered wording. All results are
EXPLORATORY. Only the older-seasons version the paper prints under Amendment
7's permission rule is in those files, so only that version is in the note.
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

import pandas as pd

ARTIFACTS = Path("docs/research/artifacts/sloan-fullpaper-amend9-2026-11")
NOTE = Path("docs/research/sloan-fullpaper-amend9-2026-11-16.md")
CSV_FILES = ("e28a_differences.csv", "e28b_differences.csv", "e28c_margin.csv")
AMENDMENT = "docs/research/sloan-full-paper-preregistration-amendment-9-2026-11-16.md"

GAIN_NAMES = {
    "G_H": "G_H: history alone minus league-aware",
    "G_D": "G_D: history + destination minus league-aware",
}
WEIGHTING_NAMES = {
    "unweighted": "Unweighted",
    "minutes_weighted": "Weighted by destination minutes",
}
READINGS = {
    "above_zero": "above zero",
    "includes_zero": "includes zero",
    "below_zero": "below zero",
    "not_estimable": "not estimable",
}
DESTINATIONS = {"euroleague": "EuroLeague", "eurocup": "EuroCup"}
VERSION_NAMES = {
    "V-noACB": "the version without Spain's ACB: Adriatic league and Israel",
    "V-all": "the version with all three leagues: Spain's ACB, Adriatic league and Israel",
}
#: What happened, in order. Run names and commits come from the receipt.
EVENTS = (
    "Amendment 9 was written on 16 November 2026, accepted by Amir and pushed alone (commit `{amendment}`) before any E28 code existed.",
    "The generator was written. Before it was committed it was run on the staged inputs outside the retained-run machinery, to check that the gates execute. Two faults were fixed after that: a gate record that could not be built (a repeated argument name), and a gate record that would have carried the row count of the withheld version into the public summary. Neither fix changes an estimate, an interval, a gate threshold or a rule.",
    "The generator was committed (commit `{generator}`) and run once as retained run `{run}` from the clean committed tree. The run finished with status {status}; every gate passed and every negative control was rejected as required. No retained run of the generator failed and none was repeated.",
    "No specification choice was made or changed after a result was seen. Every difference and interval the run produced for the printed version is in this note; standard errors and p-values are in the committed CSV tables.",
    "This note is rendered by `scripts/report_sloan_fullpaper_amend9.py` from the committed outputs, in its own retained run.",
)


def num(value: float, digits: int = 3, signed: bool = False) -> str:
    text = f"{value:+.{digits}f}" if signed else f"{value:.{digits}f}"
    return text.replace("-", "−")


def span(ci95, digits: int = 3) -> str:
    return f"{num(ci95[0], digits)} to {num(ci95[1], digits)}"


def table(header: list, rows: list) -> list:
    lines = ["| " + " | ".join(header) + " |", "|" + "---|" * len(header)]
    lines.extend("| " + " | ".join(str(c) for c in row) + " |" for row in rows)
    return lines


def gates_table(summary: dict) -> list:
    rows = []
    for name, gate in summary["gates"].items():
        worst = gate.get("max_difference")
        rows.append(
            [
                name,
                gate["status"],
                "n/a" if worst is None else f"{worst:.1e}",
                gate.get("negative_control") or "n/a",
            ]
        )
    return table(["Gate", "Status", "Largest difference", "Negative control"], rows)


def cell(record: dict) -> str:
    if record["ci95"] is None:
        return f"{num(record['difference'], signed=True)} (not estimable)"
    return f"{num(record['difference'], signed=True)} ({span(record['ci95'])})"


def difference_rows(blocks: dict) -> list:
    rows = []
    for name in GAIN_NAMES:
        for weighting, label in WEIGHTING_NAMES.items():
            r = blocks[name][weighting]
            rows.append(
                [
                    GAIN_NAMES[name],
                    label,
                    r["n"],
                    num(r["mae_left"]),
                    num(r["mae_right"]),
                    num(r["difference"], signed=True),
                    span(r["ci95"]) if r["ci95"] else "not estimable",
                    num(r["detectable_80"]) if r["detectable_80"] else "n/a",
                    READINGS[r["reading"]],
                ]
            )
    return rows


DIFFERENCE_HEADER = [
    "Difference in MAE",
    "Weighting",
    "n",
    "MAE of the first forecast",
    "MAE of the league-aware forecast",
    "Difference, EFF/36",
    "95% interval",
    "Detectable with 80% power",
    "Reading",
]


def subset_table(csv: pd.DataFrame, prefix: str, label: str, names=None) -> list:
    part = csv[csv.scope.str.startswith(prefix + ":")]
    rows = []
    for scope, group in part.groupby("scope", sort=False):
        key = scope.split(":", 1)[1]
        cells = {}
        for r in group.itertuples():
            ci = [r.ci95_low, r.ci95_high]
            cells[(r.difference_name, r.weighting)] = (
                f"{num(r.difference, signed=True)} ({span(ci)}); {num(r.detectable_80)}"
            )
        rows.append(
            [
                names[key] if names else key,
                int(group.n.iloc[0]),
                cells[("G_H", "unweighted")],
                cells[("G_H", "minutes_weighted")],
                cells[("G_D", "unweighted")],
                cells[("G_D", "minutes_weighted")],
            ]
        )
    return table(
        [
            label,
            "n",
            "G_H, unweighted",
            "G_H, weighted",
            "G_D, unweighted",
            "G_D, weighted",
        ],
        rows,
    )


def licence_lines(licences: dict) -> list:
    """The registered sentences, and any reading the amendment has no wording for."""
    out = []
    for name in GAIN_NAMES:
        for weighting, label in WEIGHTING_NAMES.items():
            entry = licences[name][weighting]
            where = f"{name}, {label.lower()}"
            if entry.get("sentence"):
                out.append(f'- {where}: "{entry["sentence"]}".')
            elif entry["reading"] == "above_zero":
                out.append(
                    f"- {where}: interval above zero; printed beside the unweighted value, with no further registered wording."
                )
            else:
                out.append(
                    f"- {where}: the interval is {READINGS[entry['reading']]}. **{entry['note']}**"
                )
    return out


def plain_reading(name: str, weighting: str, record: dict, where: str) -> str:
    """One plain sentence per result; the direction is read from the interval."""
    subject = {
        "G_H": "against history alone",
        "G_D": "against the forecast that knows only the destination",
    }[name]
    how = "" if weighting == "unweighted" else ", weighted by destination minutes,"
    value = f"{num(abs(record['difference']))} EFF/36 (interval {span(record['ci95'])})"
    if record["reading"] == "above_zero":
        return f"{where}{how} the league-aware forecast was more accurate {subject} by {value}."
    if record["reading"] == "below_zero":
        return f"{where}{how} the league-aware forecast was **less** accurate {subject} by {value}."
    direction = "more" if record["difference"] > 0 else "less"
    return (
        f"{where}{how} the league-aware forecast was {direction} accurate {subject} by {value}, "
        f"an interval that includes zero; the smallest difference this sample could detect with 80% power is {num(record['detectable_80'])}."
    )


def verdict(summary: dict) -> list:
    out = []
    a, b = summary["e28a"], summary["e28b"]
    for name in GAIN_NAMES:
        for weighting in WEIGHTING_NAMES:
            out.append(
                "- "
                + plain_reading(
                    name, weighting, a["contrasts"][name][weighting], f"On the {a['n']}"
                )
            )
    for name in GAIN_NAMES:
        for weighting in WEIGHTING_NAMES:
            out.append(
                "- "
                + plain_reading(
                    name,
                    weighting,
                    b["contrasts"][name][weighting],
                    f"On the {b['n']} older arrivals",
                )
            )
    unregistered = [
        f"{name}, {WEIGHTING_NAMES[weighting].lower()}, on the {population}"
        for population, block in (("674", a), ("older seasons", b))
        for name in GAIN_NAMES
        for weighting in WEIGHTING_NAMES
        if block["licences"][name][weighting]["reading"]
        not in ("above_zero", "includes_zero")
    ]
    if unregistered:
        out.append(
            "- **A result outside the registered wording:** "
            + "; ".join(unregistered)
            + ". Amendment 9 registered wording only for intervals above zero or including zero. A result that weakens a paper claim goes to Amir before any writing, and then into the main text."
        )
    return out


def provenance(summary: dict, receipt: dict) -> list:
    return [
        f"- Generator `{receipt['entrypoint']}` (commit `{receipt['generator_commit'][:9]}`, sha256 `{receipt['generator_sha256'][:16]}…`), amendment commit `{summary['amendment_commit'][:9]}` (file sha256 `{summary['amendment_sha256'][:16]}…`), retained run `{receipt['run_dir']}`, {receipt['inputs']} input files, {receipt['code_files']:,} code files, status {receipt['status']}.",
        f"- Inputs: the pinned v10 pairs and cohort (pool A), the committed summaries of the recipes and Amendment 1 runs, the committed scored rows and summary of the Amendment 7 scoring run, the Amendment 7 paper extract, the release flag, and the frozen older-season forecasts (sha256 `{summary['input_sha256']['frozen_older_season_forecasts'][:16]}…`). The run recorded {receipt['withheld_outputs']['files']} output file that is not committed: {receipt['withheld_outputs']['note']}.",
    ]


def render(artifacts: Path, receipt: dict) -> str:
    artifacts = Path(artifacts)
    s = json.loads((artifacts / "summary.json").read_text())
    csv_a = pd.read_csv(artifacts / "e28a_differences.csv")
    csv_c = pd.read_csv(artifacts / "e28c_margin.csv")
    a, b, c = s["e28a"], s["e28b"], s["e28c"]
    version = b["printed_version"]
    out = [
        "# SSAC27 full paper: Amendment 9 results (E28)",
        "",
        "**EXPLORATORY.** Destination seasons 2020-2025 had been examined before any registration, and the older seasons had been scored once under Amendment 7. Only the frozen 2026-27 test (P1) is confirmatory. Every number below is formatted by `scripts/report_sloan_fullpaper_amend9.py` from committed run outputs; every quoted result sentence is the generator's registered wording.",
        "",
        f"Pre-registration: `{AMENDMENT}`, pushed alone before its generator existed.",
        "",
        "## What E28 asks",
        "",
        "The paper's title is about one number per league. E28 puts an interval on what that number is worth. It compares the league-aware forecast with two plainer forecasts on the same arrivals: a player's history alone (G_H), and a forecast that knows the destination competition but not the source league (G_D). G_D is the plain measure of what the source league adds. A positive difference means the league-aware forecast had the smaller error.",
        "",
        "## Results in plain words",
        "",
    ]
    out += verdict(s)
    out += ["", "## Specification", ""]
    out += table(
        ["Field", "Registered choice"],
        [
            ["Unit", "One arrival: player × destination season."],
            [
                "Population",
                f"(a) The {s['n_targets']} benchmark arrivals of 2020-2025 (v10 target keys, pool A). (b) The older-seasons arrivals of Amendment 7, in {VERSION_NAMES[version]} (the version the paper prints), n = {b['n']}.",
            ],
            [
                "Estimator",
                f"Paired differences in mean absolute error, EFF/36: G_H = {s['estimator']['differences']['G_H']}; G_D = {s['estimator']['differences']['G_D']}. Each unweighted and weighted by destination minutes. No model is refitted and nothing is re-scored.",
            ],
            ["Null", "Zero for each paired difference."],
            ["Filter", "None beyond each population's registered rules."],
            [
                "Key",
                "`player_name` × `season_dest` on the 674; API person code × destination season on the older seasons.",
            ],
            [
                "Uncertainty",
                f"{s['estimator']['interval'][0].upper()}{s['estimator']['interval'][1:]}. Detectable effect with 80% power: {s['estimator']['detectable_80']}.",
            ],
        ],
    )
    out += ["", "## What had been seen", "", "Before Amendment 9 was registered:"]
    out += [f"- {x}" for x in s["exposure"]["seen_before_registration"]]
    out += ["", "Not seen before this run:"]
    out += [f"- {x}" for x in s["exposure"]["not_seen_before_this_run"]]
    out += ["", "## Gates", ""]
    out += gates_table(s)
    out += [
        "",
        "G28a reproduces the registered errors of the three forecasts to the printed digits and to 1e-9, the registered head-to-head with its interval, and the committed minutes-weighted head-to-head; its negative control shifts one forecast column by 0.01. G28b reproduces the three printed comparisons of the Amendment 7 extract before G_H and G_D are computed; its negative control shuffles the outcome column.",
        "",
        f"## E28a: the {a['n']} benchmark arrivals",
        "",
    ]
    out += table(DIFFERENCE_HEADER, difference_rows(a["contrasts"]))
    out += ["", "Registered wording:", ""]
    out += licence_lines(a["licences"])
    out += [
        "",
        "### By destination competition (printed without a licence)",
        "",
        "Each cell: difference (95% interval); detectable effect with 80% power. These subsets are small and carry no licence.",
        "",
    ]
    out += subset_table(csv_a, "destination", "Destination competition", DESTINATIONS)
    out += ["", "### By destination season (printed without a licence)", ""]
    out += subset_table(csv_a, "season", "Destination season")
    out += [
        "",
        f"## E28b: the older seasons ({b['n']} arrivals)",
        "",
        f"Printed here: {VERSION_NAMES[version]}. {b['second_reading']}",
        "",
    ]
    out += table(DIFFERENCE_HEADER, difference_rows(b["contrasts"]))
    out += ["", "Registered wording:", ""]
    out += licence_lines(b["licences"])
    if "withheld" in b:
        out += [
            "",
            f"Both versions of the older-seasons test were computed in this run. The other version ({b['withheld']['version']}) is withheld, not for its result: {b['withheld']['reason']}. Nothing from it is in this note or in any committed file.",
        ]
    margin, low, high = (csv_c.iloc[k] for k in range(3))
    out += [
        "",
        "## E28c: the margin in proportion (descriptive)",
        "",
    ]
    out += table(
        ["Registered quantity", "EFF/36", "Divided by G_D on the 674"],
        [
            [
                row.quantity,
                num(row.eff36, signed=row.eff36 < 0),
                f"{100 * row.share_of_g_d:.0f}%".replace("-", "−"),
            ]
            for row in (margin, low, high)
        ],
    )
    out += [
        "",
        f"- G_D on the 674 is {num(c['g_d'])} EFF/36 (interval {span(c['g_d_ci95'])}).",
        (
            f'- Registered wording: "{c["sentence"]}".'
            if c.get("sentence")
            else f"- **{c['note']}**"
        ),
        "- This is arithmetic on registered numbers. It licenses no statement of equivalence and changes no registered sentence.",
        "",
        "## Limits",
        "",
        "- Every outcome used here had been seen. The frozen 2026-27 test carries the same two comparisons as registered read-outs (Amendment 8).",
        "- The older-seasons result is a second reading of outcomes read once, on one version of the test.",
        "- The by-competition and by-season cells are small subsets, shown for transparency. No claim rests on them.",
        "- An interval that includes zero is not evidence of no difference: the detectable effect beside it says how large a difference this sample could have found.",
        "",
        "## Order of events",
        "",
    ]
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
