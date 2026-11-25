#!/usr/bin/env python3
"""Render the Amendment 15 results note (E31a, and the E31c freeze record) from committed outputs.

Reads only the committed outputs of scripts/sloan_fullpaper_published_tables.py
(the E31a summary and tables, the published table itself, the E31c freeze
record) and their trimmed run receipts, and writes
docs/research/sloan-fullpaper-published-tables-2026-11-17.md. No number is
typed here: every value is formatted from those files, and every registered
sentence is the generator's. E31a is EXPLORATORY. Both weightings are printed
for every difference; this script does not choose which one a sentence of the
paper follows.
"""

# ruff: noqa: E501, E741 -- table rows and sentences; O is the offsets arm
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

ARTIFACTS = Path("docs/research/artifacts/sloan-fullpaper-published-tables-2026-11")
FREEZE = Path("docs/research/artifacts/sloan-fullpaper-p1-freeze-2026-11")
NOTE = Path("docs/research/sloan-fullpaper-published-tables-2026-11-17.md")
TABLE_FILE = "vashro_2015_competition_scores.csv"
CSV_FILES = (
    "e31a_differences.csv",
    "e31a_coefficients.csv",
    "e31a_keyed_forecasts.csv",
)
E31C_RECORD = "e31c_freeze.json"
E31C_RECEIPT = "e31c-generator-receipt.json"
AMENDMENT = "docs/research/sloan-full-paper-preregistration-amendment-15-2026-11-17.md"
D, O, P = "history_destination_slope", "source_ridge_10", "published_table_vashro_2015"

ARM_NAMES = {
    D: "Knows the destination, not the source league",
    P: "The same, plus the 2015 table's score of the source league",
    O: "League-aware: the paper's one number per league",
}
CONTRAST_NAMES = {
    "T_D": "Destination-only minus 2015 table",
    "T_O": "2015 table minus the paper's league numbers",
}
POSITIVE_MEANS = {
    "T_D": "positive means the 2015 table lowers the error",
    "T_O": "positive means the 2015 table has the larger error",
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
#: What happened, in order. Run names and commits come from the receipts.
EVENTS = (
    "Amendment 15 was written on 17 November 2026, accepted by Amir and pushed alone (commit `{amendment}`) before any E31 code existed. It lists the twelve values of the 2015 table.",
    "The generator was written and tested on a made-up league table and synthetic arrivals. Before it was committed, its reproduction gates were run on the real inputs outside the retained-run machinery, without any league table, to check that they execute: the registered errors and the pinned frozen forecasts were reproduced. No forecast, error or correlation was computed with the 2015 table before the retained run.",
    "The file with the twelve published values was committed separately, after Amir approved that step. The generator reads it and refuses to run unless its values equal the values printed in Amendment 15.",
    "The generator was run once on the 674 arrivals as retained run `{run}` (code commit `{generator}`). The run finished with status {status}; every gate passed and every negative control was rejected as required. No retained run failed and none was repeated.",
    "The forecasts and the four differences were then recomputed with separate code from the pinned inputs and the table file. They agree with the committed outputs.",
    "No specification choice was made or changed after a result was seen. Every difference and interval the run produced is in this note; standard errors and p-values are in the committed CSV table.",
    "This note is rendered by `scripts/report_sloan_fullpaper_published_tables.py` from the committed outputs, in its own retained run.",
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


def gates_table(gates: dict) -> list:
    rows = []
    for name, gate in gates.items():
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


def error_rows(mae: dict) -> list:
    return [
        [
            ARM_NAMES[arm],
            f"`{arm}`",
            num(mae[arm]["unweighted"]),
            num(mae[arm]["minutes_weighted"]),
        ]
        for arm in (D, P, O)
    ]


def difference_rows(blocks: dict) -> list:
    rows = []
    for name, label in CONTRAST_NAMES.items():
        for weighting, how in WEIGHTING_NAMES.items():
            r = blocks[name][weighting]
            rows.append(
                [
                    f"{label} ({POSITIVE_MEANS[name]})",
                    how,
                    r["n"],
                    num(r["difference"], signed=True),
                    span(r["ci95"]) if r["ci95"] else "not estimable",
                    num(r["detectable_80"]) if r["detectable_80"] else "n/a",
                    READINGS[r["reading"]],
                ]
            )
    return rows


def plain_reading(name: str, weighting: str, record: dict, n: int) -> str:
    """One plain sentence per difference and weighting; the reading comes from the interval."""
    how = (
        "unweighted" if weighting == "unweighted" else "weighted by destination minutes"
    )
    where = f"On the {n} arrivals, {how},"
    value = f"{num(record['difference'], signed=True)} EFF/36 (interval {span(record['ci95'])}; {POSITIVE_MEANS[name]})"
    power = f"The smallest difference this sample could detect with 80% power is {num(record['detectable_80'])}."
    reading = record["reading"]
    if name == "T_D":
        if reading == "above_zero":
            return f"{where} adding the 2015 table to the destination-aware forecast lowered its error: {value}."
        if reading == "below_zero":
            return f"{where} adding the 2015 table to the destination-aware forecast **raised** its error: {value}."
        return f"{where} adding the 2015 table to the destination-aware forecast changed its error by {value}, an interval that includes zero. {power}"
    if reading == "above_zero":
        return f"{where} the forecast with the 2015 table had the larger error than the forecast with the paper's league numbers: {value}."
    if reading == "below_zero":
        return f"{where} the forecast with the 2015 table had the **smaller** error than the forecast with the paper's league numbers: {value}."
    return f"{where} the forecast with the 2015 table and the forecast with the paper's league numbers are not distinguishable: the difference in error is {value}, an interval that includes zero. {power}"


def verdict(e: dict) -> list:
    return [
        "- " + plain_reading(name, weighting, e["contrasts"][name][weighting], e["n"])
        for name in CONTRAST_NAMES
        for weighting in WEIGHTING_NAMES
    ]


def licence_lines(licences: dict) -> list:
    out = []
    for name in CONTRAST_NAMES:
        for weighting, label in WEIGHTING_NAMES.items():
            entry = licences[name][weighting]
            where = f"{CONTRAST_NAMES[name]}, {label.lower()}"
            if entry.get("sentence"):
                extra = f" {entry['note']}" if entry.get("note") else ""
                out.append(f'- {where}: "{entry["sentence"]}".{extra}')
            else:
                out.append(
                    f"- {where}: the interval is {READINGS[entry['reading']]}. **{entry['note']}**"
                )
    return out


def open_points(escalation: dict) -> list:
    if not escalation["reasons"]:
        return ["- None from this run."]
    out = [
        f"- **Not decided here; it goes to Amir before any writing:** {reason}."
        for reason in escalation["reasons"]
    ]
    if any("T_D" in reason or "T_O" in reason for reason in escalation["reasons"]):
        out.append(
            "- In the line above, T_D is the destination-only forecast against the 2015 table, and T_O is the 2015 table against the paper's league numbers."
        )
    return out


def score_rows(scores: pd.DataFrame, used: dict) -> list:
    rows = []
    for r in scores.itertuples():
        rows.append(
            [
                f"`{r.league}`",
                r.name_as_printed,
                f"{int(r.first_year_as_printed)} to {int(r.last_year_as_printed)}",
                num(float(r.score), 2),
                "source league"
                if r.league in used
                else "destination competition; its score is not used",
            ]
        )
    return rows


def render(artifacts: Path, freeze: Path, receipt: dict, freeze_receipt: dict) -> str:
    artifacts, freeze = Path(artifacts), Path(freeze)
    s = json.loads((artifacts / "summary.json").read_text())
    scores = pd.read_csv(artifacts / TABLE_FILE)
    folds = pd.read_csv(artifacts / "e31a_coefficients.csv")
    c = json.loads((freeze / E31C_RECORD).read_text())
    e, g = s["e31a"], s["gates"]
    control = g["G31a"]["registered_negative_control"]
    last_years = " and ".join(
        str(int(y)) for y in sorted(set(scores.last_year_as_printed))
    )
    out = [
        "# SSAC27 full paper: Amendment 15 results (E31a, and the E31c freeze)",
        "",
        "**EXPLORATORY.** Destination seasons 2020-2025 had been examined before any registration. Only the frozen 2026-27 test is confirmatory. Every number below is formatted by `scripts/report_sloan_fullpaper_published_tables.py` from the committed outputs of `scripts/sloan_fullpaper_published_tables.py`; none is typed.",
        "",
        f"Pre-registration: `{AMENDMENT}`, pushed alone before its generator existed.",
        "",
        "## What E31a asks",
        "",
        f"The paper builds its own table of one number per league. A league table for the same leagues was printed in November 2015, before every season the paper scores. E31a asks what that outside table is worth inside the paper's own forecast, on the same {e['n']} arrivals. One rule, fixed before any score: take the forecast that knows the destination but not the source league, and add one coefficient times the 2015 table's score of the source league. The coefficient is fitted without penalty, on earlier arrivals only, like every other forecast. {s['table']['purpose']}",
        "",
        "## Results in plain words (exploratory)",
        "",
    ]
    out += verdict(e)
    out += [
        "",
        "Both weightings are printed for every difference. This note does not choose which weighting a sentence of the paper follows.",
        "",
        "## Open points",
        "",
    ]
    out += open_points(e["escalation"])
    out += ["", "## Specification", ""]
    out += table(
        ["Field", "Registered choice"],
        [
            ["Unit", "One arrival: player × destination season."],
            [
                "Population",
                f"The {s['n_targets']} benchmark arrivals of 2020-2025 (v10 target keys, pool A).",
            ],
            [
                "Estimator",
                f"Paired differences in mean absolute error, EFF/36: {s['estimator']['differences']['T_D']}; {s['estimator']['differences']['T_O']}. Each unweighted and weighted by destination minutes. The published-table forecast: {s['estimator']['forecast']}.",
            ],
            ["Null", "Zero for each paired difference."],
            ["Filter", "None beyond the population's registered rules."],
            ["Key", "`player_name` × `season_dest`."],
            [
                "Uncertainty",
                f"{s['estimator']['interval'][0].upper()}{s['estimator']['interval'][1:]}. Detectable difference with 80% power: {s['estimator']['detectable_80']}.",
            ],
        ],
    )
    out += ["", "## What had been seen", "", "Before this run:"]
    out += [f"- {x}" for x in s["exposure"]["seen_before_registration"]]
    out += ["", "Not seen before this run:"]
    out += [f"- {x}" for x in s["exposure"]["not_seen_before_this_run"]]
    out += [
        "",
        "## The 2015 table",
        "",
        f"The twelve values are in `{s['table']['file']}` (sha256 `{s['table']['sha256']}`), with the article's title, author, date and address in the folder's README. The run checked them against the values printed in Amendment 15. The years are the first and last year the article prints for each competition. The last year printed is {last_years}; how the article labels its seasons was not checked here.",
        "",
    ]
    out += table(
        ["League key", "Name as printed", "Years as printed", "Score", "Use in E31"],
        score_rows(scores, s["table"]["scores_used"]),
    )
    out += ["", "## Gates", ""]
    out += gates_table(g)
    out += [
        "",
        f"G0 and the scope gate are the paper's standing checks. G31a ran before the published-table term was added: the registered errors of the destination-only and league-aware forecasts were reproduced to the printed digits and to {g['G31a']['tolerance']:.0e} against the committed summary, and this generator's own fit without the term equals the registered destination-only forecast on every arrival. Its control: {g['G31a']['control_input']}. The table-pin gate compares the {g['table_pin']['venues']} committed values with Amendment 15; its control moves one score.",
        "",
        f"**G31a's registered negative control.** With the ten source-league scores shuffled so that no league keeps its own (seed {control['seed']}), the difference from the destination-only forecast was {num(control['unweighted']['difference'], signed=True)} (interval {span(control['unweighted']['ci95'])}) unweighted and {num(control['minutes_weighted']['difference'], signed=True)} (interval {span(control['minutes_weighted']['ci95'])}) weighted by destination minutes. Both intervals include zero, as the gate requires.",
        "",
        f"## E31a: the {e['n']} benchmark arrivals (exploratory)",
        "",
        "Mean absolute error of the three forecasts, EFF/36:",
        "",
    ]
    out += table(
        ["Forecast", "Arm", "Unweighted", "Weighted by destination minutes"],
        error_rows(e["mae"]),
    )
    out += ["", "Paired differences:", ""]
    out += table(
        [
            "Difference in MAE",
            "Weighting",
            "n",
            "Difference, EFF/36",
            "95% interval",
            "Detectable with 80% power",
            "Reading",
        ],
        difference_rows(e["contrasts"]),
    )
    out += [
        "",
        "Registered wording of Amendment 15, filled for each difference and each weighting:",
        "",
    ]
    out += licence_lines(e["licences"])
    out += [
        "",
        "### The fitted coefficient",
        "",
        "One coefficient per destination season, fitted on arrivals of earlier seasons. It is in EFF/36 per point of the 2015 score.",
        "",
    ]
    out += table(
        ["Destination season", "Training arrivals", "Arrivals forecast", "Coefficient"],
        [
            [
                int(r.season),
                int(r.train_n),
                int(r.test_n),
                num(r.score_coefficient, signed=True),
            ]
            for r in folds.itertuples()
        ],
    )
    out += [
        "",
        "## E31c: the same forecast, frozen for the 2026-27 test",
        "",
        f"The published-table forecast was fitted on the {c['training_rows']:,} arrivals through {c['last_training_destination_season']}, exactly as the frozen forecasts of 3 November were, and written for the same {c['rows']:,} rows as a second file. The pinned file was read and not rewritten. No 2026-27 statistic was read.",
        "",
    ]
    out += table(
        ["Item", "Value"],
        [
            ["File", f"`{FREEZE.as_posix()}/{c['forecast_file']}`"],
            ["sha256", f"`{c['forecast_sha256']}`"],
            ["Rows", f"{c['rows']:,}"],
            [
                "Pinned frozen file (unchanged)",
                f"`{c['pinned_frozen_file']}`, sha256 `{c['pinned_frozen_sha256']}`",
            ],
            [
                "Coefficient of the 2015 score",
                num(c["fit"]["score_coefficient"], signed=True),
            ],
            [
                "Retained run",
                f"`{freeze_receipt['run_dir']}`, code commit `{freeze_receipt['generator_commit'][:9]}`, status {freeze_receipt['status']}",
            ],
        ],
    )
    out += [""]
    out += gates_table(c["gates"])
    out += [
        "",
        f"The frozen-arm gate refits three pinned frozen forecasts with the committed fitters on the same training arrivals and compares them on all {c['gates']['frozen_arms']['rows']:,} rows. G31b counts rows, keys and missing forecasts against the pinned file; its negative control flips one byte of the written file, and the hash check must refuse it. At scoring this file is read out beside the registered read-outs of Amendment 8: its error, and its paired differences from the destination-only and the league-aware forecasts. As for the second read-out of Amendment 8, no difference is expected to be detectable in November.",
        "",
        "## Limits",
        "",
        "- Every outcome E31a uses had been seen. The frozen 2026-27 test carries the same comparison (E31c), and the league changes of E30 carry a comparison of the two scales on equal terms (E31b).",
        '- "Not distinguishable" is not "the same". The detectable difference is printed beside each interval, and no equivalence is claimed.',
        "- The 2015 table enters through one fitted coefficient. That gives it its best single-number use inside the paper's own forecast; it does not test the table for the purpose it was built for.",
        "- The two differences share the same arrivals and the same destination-aware forecast, so they are not independent pieces of evidence.",
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
    out += [
        "",
        "## Reproduction",
        "",
        f"- Generator `{receipt['entrypoint']}` (commit `{receipt['generator_commit'][:9]}`, sha256 `{receipt['generator_sha256'][:16]}…`), amendment commit `{s['amendment_commit'][:9]}` (file sha256 `{s['amendment_sha256'][:16]}…`), retained runs `{receipt['run_dir']}` (E31a) and `{freeze_receipt['run_dir']}` (E31c).",
        f"- Inputs: the pinned v10 pairs and cohort (pool A), the committed summary of the recipes run, the published table, and for E31c the pinned frozen file and its freeze record. Their sha256 values are in `{ARTIFACTS.as_posix()}/generator-receipt.json` and `{FREEZE.as_posix()}/{E31C_RECEIPT}`.",
        f"- Outputs: `summary.json`, {', '.join(f'`{name}`' for name in CSV_FILES)} in `{ARTIFACTS.as_posix()}/`.",
    ]
    return "\n".join(out) + "\n"


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--artifacts", type=Path, required=True)
    parser.add_argument("--freeze", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    receipt = json.loads((args.artifacts / "generator-receipt.json").read_text())
    freeze_receipt = json.loads((args.freeze / E31C_RECEIPT).read_text())
    note = render(args.artifacts, args.freeze, receipt, freeze_receipt)
    args.out.mkdir(parents=True, exist_ok=False)
    (args.out / NOTE.name).write_text(note)
    print(f"{NOTE.name}: {len(note.splitlines())} lines")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
