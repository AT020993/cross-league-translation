#!/usr/bin/env python3
"""Render the Amendment 14 results note (E30, league changes) from committed outputs.

Reads only the committed outputs of scripts/sloan_fullpaper_league_changes.py
and the trimmed receipts of its retained runs, and writes
docs/research/sloan-fullpaper-league-changes-2026-11-17.md. No number is typed
here: every value is formatted from those files, and every result sentence is
the generator's registered wording. Before the scoring run exists the note
describes the frozen predictions only and says that no outcome was joined.
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

ARTIFACTS = Path("docs/research/artifacts/sloan-fullpaper-league-changes-2026-11")
NOTE = Path("docs/research/sloan-fullpaper-league-changes-2026-11-17.md")
GENERATOR = "scripts/sloan_fullpaper_league_changes.py"
GATES = "e30_made_up_gates.json"
FREEZE = "e30_freeze.json"
SUMMARY = "e30_summary.json"
RECEIPTS = {
    "gates": "gates-receipt.json",
    "freeze": "freeze-receipt.json",
    "score": "score-receipt.json",
}
SCORE_TABLES = ("e30_slopes.csv", "e30_league_pairs.csv", "e31b_scales.csv")

LEAGUE_NAMES = {
    "aba-league": "Adriatic league",
    "france-pro-a": "France",
    "germany-bbl": "Germany",
    "greece-a1": "Greece",
    "israel-bsl": "Israel",
    "italy-lba": "Italy",
    "lithuania-lkl": "Lithuania",
    "spain-acb": "Spain",
    "turkey-bsl": "Turkey",
    "vtb": "VTB United League",
}
COLUMNS = {
    "player_name": "the key: the Proballers player name",
    "season_from": "season t, in league A (stored as the year the season starts)",
    "season_to": "season t+1, in league B",
    "league_from": "league A",
    "league_to": "league B",
    "games_from": "games in league A in season t",
    "minutes_from": "minutes in league A in season t",
    "x": "last season's rate: EFF/36 in league A in season t",
    "h_recorded": "career rate before season t (all earlier games on record); empty if there is none",
    "h": "the career rate used: h_recorded, or x where there is none",
    "a": "1 if x is above h, else 0",
    "g": "the change the league table predicts: EuroCup equivalent of B minus that of A",
    "stayer_forecast": "what the same season predicts for a player who stayed",
    "g_euroleague": "g with the EuroLeague equivalents (sensitivity 5)",
    "g_refit": "g with the table refitted only on arrivals before season t+1; arrivals of 2020 to 2025 (sensitivity 7)",
    "stayer_forecast_origin": "the stayer forecast with one intercept per league of origin (sensitivity 4)",
    "second_league": "true if either season has a second domestic league with 8 or more games (sensitivity 1)",
    "both_seasons_15_games": "true if both seasons have at least 15 games (sensitivity 6)",
    "pair_moves": "league changes between these two leagues, both directions together (sensitivity 8)",
}
#: Places where the registration needed a reading. Numbers are filled from the freeze record.
READINGS = (
    "**Which seasons count.** The amendment calls the population rule \"the repository's source-season rule\". That function, used as it is, lets a larger stint in Poland take the place of a stint in one of the ten leagues and then drops the player-season. It gives {unmodified_moves} league changes and {unmodified_stayers} stayer pairs. The counts registered on 17 November ({moves} and {stayers}) take the ten leagues first, and gate G30b fixes those counts. The generator follows the registered counts: a stint outside the ten leagues cannot be a source season, and its games still count in the career rate. {only_registered} player-seasons are in the registered population and not in the function's own output; on the other {compared} the two agree exactly on league, x, h and a.",
    "**Which games feed the career rate h.** The amendment pins the box scores \"of the ten leagues\" and also says that h follows the paper's definition, all games on record in earlier seasons. The paper's definition includes continental games. The generator follows the definition: h uses every game the loader reads ({leagues} competitions, the ten leagues plus Poland, the Champions League and the Proballers EuroLeague and EuroCup rows). All {files} files are hashed in the freeze record.",
    "**Not the paper's corrected corpus.** The amendment fixes the key (the raw Proballers name) and the loader. The paper's 674 arrivals use a corrected corpus with official continental box scores and a name key that merges spellings. x, h and a here come from the same functions on the raw Proballers corpus.",
    "**Gate G30c and the freeze.** The freeze code may compute no slope. G30c therefore runs in its own step (`gates`), on made-up players only, before the freeze; the freeze refuses to run without its passed record. The amendment does not fix the size or the noise of the made-up data. Both were fixed in the code, with one seed, before the first run: {made_up_players} made-up players, noise of {noise}.",
    "**Where G30d runs.** G30d needs the real predicted changes and the stayers' rates, and it computes a slope. It runs at the start of the scoring run, before any outcome of a league changer is joined, and stops the run if it fails.",
    '**Intervals.** Every interval comes from the one registered bootstrap (players resampled, the stayer forecast refitted in every draw; percentile limits). This includes the error difference S-a, which the amendment calls "clustered by player".',
    "**Subsets keep the stayer forecast.** The leave-one-league-out slopes and sensitivities 1, 2, 3, 6 and 8 remove league changes only. The stayer forecast is still fitted on all stayers. Sensitivity 6 keeps league changes with at least 15 games in both seasons of the registered population; it does not re-select seasons with a floor of 15.",
    "**S-d is one-sided by construction.** Redrawing the ten table values adds noise to the predicted change, and noise in a predictor pulls a slope towards zero. The S-d interval is therefore wider than the primary one and sits lower. It is printed as registered and labelled an approximation.",
    "**N in the Clear sentence** is the number of players who changed league at least once ({players}), not the number of league changes ({moves}).",
    "**E31b.** Each scale's coefficient is fitted by least squares through the origin (the forecast is the stayer forecast plus one coefficient times the scale's difference, with no further constant), on league changes that arrived in earlier seasons.",
)


def num(value: float, digits: int = 3, signed: bool = False) -> str:
    text = f"{value:+.{digits}f}" if signed else f"{value:.{digits}f}"
    return text.replace("-", "−")


def count(value: int) -> str:
    return f"{int(value):,}"


def span(ci95, digits: int = 3) -> str:
    return f"{num(ci95[0], digits)} to {num(ci95[1], digits)}"


def table(header: list, rows: list) -> list:
    lines = ["| " + " | ".join(header) + " |", "|" + "---|" * len(header)]
    lines.extend("| " + " | ".join(str(c) for c in row) + " |" for row in rows)
    return lines


def load(artifacts: Path) -> dict:
    artifacts = Path(artifacts)
    data = {
        "gates": json.loads((artifacts / GATES).read_text()),
        "freeze": json.loads((artifacts / FREEZE).read_text()),
        "receipts": {
            name: json.loads((artifacts / file).read_text())
            for name, file in RECEIPTS.items()
            if (artifacts / file).is_file()
        },
        "summary": None,
    }
    if (artifacts / SUMMARY).is_file():
        data["summary"] = json.loads((artifacts / SUMMARY).read_text())
        data["slopes"] = pd.read_csv(artifacts / "e30_slopes.csv")
        data["pairs"] = pd.read_csv(artifacts / "e30_league_pairs.csv")
    return data


def specification(freeze: dict) -> list:
    counts = freeze["counts"]
    constants = freeze["registered_constants"]
    first, last = constants["arrival_seasons"]
    rows = [
        [
            "Unit",
            "One league change: a player's season t in domestic league A, followed by his season t+1 in a different domestic league B",
        ],
        [
            "Population",
            f"The ten source leagues of the paper. In each of the two seasons the player has at least {constants['games_floor']} games and positive minutes in the league where he played the most minutes. Arrival seasons {first} to {last}. {count(counts['league_changes'])} league changes by {count(counts['players'])} players; every one of the {counts['ordered_league_pairs']} ordered league pairs holds at least {counts['smallest_ordered_pair']}",
        ],
        [
            "Estimator",
            "The slope of the unexplained change e on the change g that the league table predicts, by ordinary least squares over all league changes. e is the player's rate in league B minus the stayer forecast",
        ],
        [
            "Null",
            "Slope zero. The registered direction is positive. A slope of one means the table has the right size",
        ],
        ["Filter", "None beyond the population rules"],
        ["Key", "Proballers `player_name` × season"],
        [
            "Uncertainty",
            f"95% interval from a bootstrap that resamples players ({count(constants['bootstrap_draws'])} draws) and refits the stayer forecast in every draw; and a permutation test that reassigns the ten table values among the ten leagues ({count(constants['permutation_draws'])} draws)",
        ],
    ]
    return table(["Field", "Registered choice"], rows)


def gate_lines(freeze: dict, gates: dict, summary: dict | None) -> list:
    g = freeze["gates"]
    b = g["G30b"]
    control = b["negative_control"]
    one, zero, shuffled = (
        gates[k]
        for k in (
            "planted_slope_one",
            "planted_slope_zero",
            "negative_control_shuffled_leagues",
        )
    )
    pins = g["G30a"]["files"]
    rows = []
    if "G17a" in g:
        rows.append(
            [
                "G17a readings fixed before the freeze",
                f"{g['G17a']['status']}: the freeze record names Amendment 17 by its sha256 `{g['G17a']['sha256']}`, and the freeze refuses to run on any other file",
                f"a changed byte in Amendment 17: {g['G17a']['negative_control_changed_byte']}",
            ]
        )
    rows += [
        [
            "G30a inputs",
            f"passed: {len(pins)} pinned files equal their sha256; {freeze['inputs']['corpus']['files']} box-score files hashed",
            "a changed byte: "
            + "; ".join(
                sorted({v["negative_control_changed_byte"] for v in pins.values()})
            ),
        ],
        [
            "G30b same population",
            f"{b['status']}: {count(b['found']['league_changes'])} league changes and {count(b['found']['stayer_pairs'])} stayer pairs, as registered",
            f"a games floor of {control['games_floor']} gives {count(control['found']['league_changes'])} and {count(control['found']['stayer_pairs'])}: {control['result']}",
        ],
        [
            "G30c planted slope (made-up data)",
            f"{gates['status']}: planted 1.0 came back as {num(one['slope'])} (interval {span(one['ci95'])}); planted 0.0 gave {num(zero['slope'], signed=True)} (interval {span(zero['ci95'])}, includes zero)",
            f"league labels shuffled: {num(shuffled['slope'], signed=True)} (interval {span(shuffled['ci95'])}, includes zero as required)",
        ],
    ]
    if summary is None:
        rows.append(
            [
                "G30d no slope where none can exist",
                "runs at the start of the scoring run, before any outcome is joined",
                "the made-up change added to the stayers' rates",
            ]
        )
        rows.append(
            [
                "G30e frozen before scored",
                "runs at the start of the scoring run: the file is read by the sha256 above",
                "a changed byte",
            ]
        )
    else:
        d = summary["gates"]["G30d"]
        plain, added = (
            d["made_up_change_on_stayers"],
            d["negative_control_change_added_to_rates"],
        )
        rows.append(
            [
                "G30d no slope where none can exist",
                f"{d['status']}: a made-up change given at random to {count(d['stayer_pairs'])} stayer pairs gives {num(plain['slope'], signed=True)} (interval {span(plain['ci95'])})",
                f"the same change added to their rates gives {num(added['slope'])} (interval {span(added['ci95'])}, excludes zero as required)",
            ]
        )
        e = summary["gates"]["G30e"]
        rows.append(
            [
                "G30e frozen before scored",
                f"{e['status']}: the scoring run read the file with sha256 `{e['sha256']}`",
                f"a changed byte: {e['negative_control_changed_byte']}",
            ]
        )
    return table(["Gate", "Result", "Negative control"], rows)


def frozen_section(freeze: dict) -> list:
    files = freeze["files"]
    model = freeze["stayer_model"]
    c = model["coefficients"]
    g = freeze["predicted_change"]
    counts = freeze["counts"]
    sens = freeze["sensitivity_rows"]
    out = [
        "## What is frozen",
        "",
        f"- `{files['frozen']['name']}`: {count(files['frozen']['rows'])} rows, one per league change. sha256 `{files['frozen']['sha256']}`.",
        f"- `{files['stayers']['name']}`: {count(files['stayers']['rows'])} pairs of seasons of players who stayed in their league, with their rate in the second season. sha256 `{files['stayers']['sha256']}`. The stayer forecast is fitted on this file.",
        "- The frozen file holds no rate of any league changer in his destination season. The next season's rate is attached to stayers only.",
        "",
    ]
    out += table(
        ["Column", "Meaning"],
        [[f"`{k}`", COLUMNS[k]] for k in files["frozen"]["columns"]],
    )
    out += [
        "",
        "**The stayer forecast** (ordinary least squares on the stayer pairs):",
        "",
        f"next season's rate = {num(c['intercept'])} + {num(c['x'])} × x + {num(c['h'])} × h {num(c['a'], signed=True).replace('+', '+ ').replace('−', '− ')} × a, with a leftover spread of {num(model['residual_sd'], 2)} EFF/36 (n = {count(model['n'])}).",
        "",
        f"**The predicted change g** runs from {num(g['min'], 2)} to {num(g['max'], 2)} EFF/36 across the league changes, with a standard deviation of {num(g['sd'], 2)}. No league change has g = 0.",
        "",
        "**Counts** (all equal to the counts printed in Amendment 14):",
        "",
    ]
    counted = freeze["gates"]["G30b"]["counted_on_17_november"]
    names = {
        "players": "Players who changed league at least once",
        "ordered_league_pairs": "Ordered league pairs with at least one league change",
        "second_league_either_season": "League changes where either season has a second domestic league with 8+ games",
        "arrivals_2020_2025": "League changes arriving 2020 to 2025",
    }
    rows = [
        [
            "League changes",
            count(counts["league_changes"]),
            count(freeze["gates"]["G30b"]["registered"]["league_changes"]),
        ],
        [
            "Stayer pairs",
            count(counts["stayer_pairs"]),
            count(freeze["gates"]["G30b"]["registered"]["stayer_pairs"]),
        ],
    ]
    rows += [
        [names[k], count(v["found"]), count(v["registered"])]
        for k, v in counted.items()
    ]
    out += table(["Quantity", "Found", "Registered"], rows)
    out += [
        "",
        f"The smallest ordered league pair holds {counts['smallest_ordered_pair']} league changes. {count(freeze['no_earlier_season'])} league changes have no earlier season on record, so h = x and a = 0 for them.",
        "",
        "League changes by arrival season: "
        + ", ".join(
            f"{season}: {n}"
            for season, n in sorted(counts["by_arrival_season"].items())
        )
        + ".",
        "",
        "Rows behind each sensitivity that removes league changes: "
        + f"(1) {count(sens['1_no_second_league'])}; (2) {count(sens['2_arrivals_2020_2025'])}; (3) {count(sens['3_arrivals_2016_2024'])}; (6) {count(sens['6_both_seasons_15_games'])}; (7) {count(sens['7_refitted_table'])}; (8) {count(sens['8_pairs_with_30_moves'])}.",
    ]
    return out


def function_lines(freeze: dict) -> list:
    labels = {
        "corpus": "Box scores",
        "aggregates": "Games, minutes, EFF and EFF/36 per player, league and season",
        "x": "x, last season's rate",
        "h": "h, the career rate before it",
        "a": "a, the flag for a season above the career rate",
        "population": "The ten-league population",
        "g": "g, the change the table predicts",
        "stayer_forecast": "The stayer forecast",
    }
    return table(
        ["Quantity", "Produced by"],
        [
            [label, freeze["functions"][k].replace("|", "/")]
            for k, label in labels.items()
        ],
    )


def reading_lines(freeze: dict, gates: dict) -> list:
    repository = freeze["gates"]["repository_values"]
    facts = {
        "unmodified_moves": count(
            repository["counts_under_the_unmodified_repository_rule"]["league_changes"]
        ),
        "unmodified_stayers": count(
            repository["counts_under_the_unmodified_repository_rule"]["stayer_pairs"]
        ),
        "moves": count(freeze["counts"]["league_changes"]),
        "stayers": count(freeze["counts"]["stayer_pairs"]),
        "players": count(freeze["counts"]["players"]),
        "only_registered": count(repository["rows_only_in_the_registered_population"]),
        "compared": count(repository["rows_compared"]),
        "leagues": len(freeze["inputs"]["corpus"]["leagues"]),
        "files": freeze["inputs"]["corpus"]["files"],
        "made_up_players": count(gates["made_up"]["players"]),
        "noise": gates["made_up"]["noise_sd"],
    }
    return [f"{k}. {text.format(**facts)}" for k, text in enumerate(READINGS, 1)]


def result_lines(data: dict) -> list:
    s = data["summary"]
    p = s["primary"]
    perm = p["permutation"]
    case = s["case"]
    out = [
        "## Result",
        "",
        f'**Case: {case["case"]}.** Registered wording: "{case["sentence"]}"',
        "",
    ]
    if case["size_reading"]:
        out += [f'Size, registered wording: "{case["size_reading"]}".', ""]
    if case["unregistered"]:
        out += [
            f"**Not covered by the registered wording:** {'; '.join(case['unregistered'])}.",
            "",
        ]
    if case["to_amir_before_writing"]:
        out += [
            "**This result qualifies the paper's league table. It goes to Amir before any writing.** The paper claims no cause for it.",
            "",
        ]
    out += table(
        ["Quantity", "Value"],
        [
            [
                "League changes / players / stayer pairs",
                f"{count(s['league_changes'])} / {count(s['players'])} / {count(s['stayer_pairs'])}",
            ],
            ["Primary slope b", num(p["estimate"])],
            ["95% bootstrap interval", span(p["ci95"])],
            ["Bootstrap standard error", num(p["bootstrap_se"])],
            [
                "Permutation test: draws with a slope at least as large",
                f"{count(perm['draws_with_slope_at_least_as_large'])} of {count(perm['draws'])} (p = {num(perm['p'], 4)})",
            ],
            [
                "Slopes under random assignment of the ten values, middle 95%",
                f"{num(perm['permuted_slope_quantiles']['2.5'])} to {num(perm['permuted_slope_quantiles']['97.5'])}",
            ],
            [
                "Intercept of the line (mean unexplained change at g = 0)",
                num(p["intercept"], signed=True),
            ],
            [
                "Slope detectable with 80% power, 2.80 × bootstrap standard error (descriptive)",
                num(p["detectable_slope_80"]),
            ],
        ],
    )
    a = s["S_a"]
    out += [
        "",
        "## Secondary results",
        "",
        f"**S-a, error.** Mean absolute error of the stayer forecast on the league changers: {num(a['mae_stayer_forecast'])} EFF/36. With the table's predicted change added: {num(a['mae_stayer_forecast_plus_g'])}. Difference: {num(a['difference']['estimate'], signed=True)} (interval {span(a['difference']['ci95'])}); a positive difference means the table lowers the error.",
        "",
        "**S-b, each league left out; S-c, each direction; S-d, the table's own uncertainty; S-e, sensitivities.**",
        "",
    ]
    out += table(
        ["Result", "What", "League changes", "Slope", "95% interval"],
        [
            [
                r.result,
                r.label,
                count(r.league_changes),
                num(r.slope),
                span([r.ci95_low, r.ci95_high]),
            ]
            for r in data["slopes"].itertuples()
        ],
    )
    c = s["S_c"]
    up, down = c["to_higher_equivalent"], c["to_lower_equivalent"]
    out += [
        "",
        f"**S-c, mean unexplained change by direction.** Moves to a league with a higher equivalent: {num(up['mean_e']['estimate'], signed=True)} EFF/36 (interval {span(up['mean_e']['ci95'])}). Moves to a league with a lower equivalent: {num(down['mean_e']['estimate'], signed=True)} (interval {span(down['mean_e']['ci95'])}). "
        + (
            "**The slope has opposite signs in the two directions.**"
            if c["opposite_signs"]
            else "The slope has the same sign in the two directions."
        ),
        "",
        f"**S-d** is an approximation: {s['S_d']['approximation']}. Redrawing the table adds noise to the predicted change, which pulls a slope towards zero, so this interval sits lower than the primary one.",
        "",
        f"**S-f, the picture.** {s['S_f_caption']} Half the difference between the two directions, per league pair, against the predicted change:",
        "",
    ]
    out += table(
        [
            "Lower equivalent",
            "Higher equivalent",
            "Predicted change",
            "Moves up",
            "Moves down",
            "Half difference",
        ],
        [
            [
                LEAGUE_NAMES[r.league_lower_equivalent],
                LEAGUE_NAMES[r.league_higher_equivalent],
                num(r.predicted_change, 2),
                r.moves_to_higher,
                r.moves_to_lower,
                num(r.half_difference, 2, signed=True)
                if pd.notna(r.half_difference)
                else "n/a",
            ]
            for r in data["pairs"].itertuples()
        ],
    )
    e = s["E31b"]
    d = e["difference_published_minus_paper"]
    last = str(
        max(int(k) for k in e["scales"]["paper"]["coefficient_by_scored_season"])
    )
    out += [
        "",
        "## E31b: the 2015 published table on the same league changes (Amendment 15)",
        "",
        f'Scored league changes: {count(e["scored_league_changes"])} (arrival seasons from {e["first_scored_arrival_season"]}). Registered wording: "{e["reading"]}".',
        "",
    ]
    out += table(
        [
            "Forecast",
            "Mean absolute error",
            "95% interval",
            f"Coefficient used for {last} arrivals",
            "95% interval",
        ],
        [
            [
                "Stayer forecast alone",
                num(e["mae_stayer_forecast"]["estimate"]),
                span(e["mae_stayer_forecast"]["ci95"]),
                "n/a",
                "n/a",
            ]
        ]
        + [
            [
                label,
                num(e["scales"][name]["mae"]["estimate"]),
                span(e["scales"][name]["mae"]["ci95"]),
                num(
                    e["scales"][name]["coefficient_by_scored_season"][last]["estimate"],
                    signed=True,
                ),
                span(e["scales"][name]["coefficient_by_scored_season"][last]["ci95"]),
            ]
            for name, label in (
                ("paper", "Stayer forecast + the paper's equivalents"),
                ("published", "Stayer forecast + the 2015 table"),
            )
        ],
    )
    out += [
        "",
        f'Error of the 2015 table minus error of the paper\'s equivalents: {num(d["estimate"], signed=True)} EFF/36 (interval {span(d["ci95"])}). "Not distinguishable" is not "the same".',
    ]
    if e["to_amir_before_writing"]:
        out += [
            "",
            "**The 2015 table is at least as accurate as the paper's league numbers here. This goes to Amir before any writing.**",
        ]
    return out


def events(data: dict) -> list:
    receipts = data["receipts"]
    lines = [
        "Amendment 14 was written on 17 November 2026, accepted by Amir and pushed alone before any E30 code existed.",
        "The generator was written and tested on made-up data only. Before it was committed, its freeze path was run on the staged inputs outside the retained-run machinery, to check that the gates execute; that path reads no rate after a league change. The analysis code was rehearsed on made-up outcomes only. Gate G30d was tried on the stayer pairs in the same way, with the registered seed and with other seeds to see that its interval behaves; it involves no league changer's outcome.",
    ]
    if "gates" in receipts:
        r = receipts["gates"]
        lines.append(
            f"Gate G30c ran on made-up data as retained run `{r['run_dir']}` (generator commit `{r['generator_commit'][:9]}`, status {r['status']})."
        )
    if "amendment_17" in data["freeze"]:
        lines.append(
            "Amendment 17, which registers the readings listed above, was accepted by Amir and pushed alone on 17 November 2026, before the freeze. The generator was then changed to pin it (gate G17a) and to carry its two added wordings; that change was tested on made-up data only."
        )
    if "freeze" in receipts:
        r = receipts["freeze"]
        lines.append(
            f"The freeze ran as retained run `{r['run_dir']}` (generator commit `{r['generator_commit'][:9]}`, status {r['status']}). It joined no outcome."
        )
    if "score" in receipts:
        r = receipts["score"]
        lines.append(
            f"The single scoring run was retained run `{r['run_dir']}` (generator commit `{r['generator_commit'][:9]}`, status {r['status']}). It read the frozen file by its sha256."
        )
    else:
        lines.append(
            "The scoring run has not been made. No rate of a league changer in his destination season has been joined, summarised or looked at."
        )
    lines.append(
        "This note is rendered by `scripts/report_sloan_fullpaper_league_changes.py` from the committed outputs."
    )
    return [f"{k}. {line}" for k, line in enumerate(lines, 1)]


def render(artifacts: Path) -> str:
    data = load(artifacts)
    freeze, gates, summary = data["freeze"], data["gates"], data["summary"]
    scored = summary is not None
    out = [
        "# SSAC27 full paper: the league table tested on players who changed domestic league (E30)",
        "",
        "Pre-registration: `docs/research/sloan-full-paper-preregistration-2026-11-03.md`, Amendment 14 (`"
        + freeze["amendment"]["path"]
        + "`, sha256 `"
        + freeze["amendment"]["sha256"]
        + "`). E30 is a **registered** test: every rule, the code and the predictions were fixed before any rate after a league change was read.",
        "",
        (
            "**Status: scored.** The single scoring run read the frozen predictions by their sha256."
            if scored
            else "**Status: frozen, not scored.** The predictions for every league change are frozen and hashed. No outcome has been joined. This note holds no result."
        ),
        "",
        "## Specification",
        "",
    ]
    out += specification(freeze)
    out += [""]
    if scored:
        out += result_lines(data) + [""]
    out += frozen_section(freeze)
    out += ["", "## Which function produced each input", ""]
    out += function_lines(freeze)
    out += ["", "## Gates and negative controls", ""]
    out += gate_lines(freeze, gates, summary)
    out += [
        "",
        f"G30c used {count(gates['made_up']['players'])} made-up players ({count(gates['made_up']['league_changes'])} made-up league changes, {count(gates['made_up']['stayer_pairs'])} made-up stayer pairs), seed {gates['seed']}, {count(gates['bootstrap_draws'])} bootstrap draws.",
        "",
        "## Where the registration needed a reading",
        "",
        "Each point below was handled in the way that changes least. None was chosen after an outcome was seen.",
        "",
    ]
    if "amendment_17" in freeze:
        seventeen = freeze["amendment_17"]
        out += [
            f"These readings, and the readings of the wording table, were then registered as Amendment 17 (`{seventeen['path']}`, sha256 `{seventeen['sha256']}`), accepted by Amir and pushed alone before the freeze. The freeze record names that file (gate G17a).",
            "",
        ]
    out += reading_lines(freeze, gates)
    out += [
        "",
        "## Limits stated in advance (Amendment 14)",
        "",
        "- Players who change league are not a random sample. The stayer forecast removes only the drift that last season's rate, the career rate and the flag can explain. Age is not in these files.",
        "- Minutes and role change with a move. EFF/36 is a rate, but it is not free of role.",
        "- Players are linked across leagues by name. A wrong link joins two different players and pulls the slope towards zero.",
        "- The table is fitted on players whom clubs sign into continental play. A league change is a different event.",
        "- The table was fitted on arrivals of 2017 to 2025, the same years as most of the league changes. Sensitivity 7 uses only earlier arrivals.",
        "",
        "## Order of events",
        "",
    ]
    out += events(data)
    out += ["", "## Reproduction", ""]
    for name, label in (
        ("gates", "Made-up gates"),
        ("freeze", "Freeze"),
        ("score", "Score"),
    ):
        r = data["receipts"].get(name)
        if r is None:
            continue
        out.append(
            f"- **{label}:** `{GENERATOR} {name}`, retained run `{r['run_dir']}`, generator commit `{r['generator_commit']}`, generator sha256 `{r['generator_sha256']}`, {r['inputs']} input files, source seasons {r['source_seasons'][0]} to {r['source_seasons'][-1]}."
        )
        out += [
            f"  - `{path}`: `{sha}`"
            for path, sha in sorted(r["outputs"].items())
            if path.startswith("out/")
        ]
    out.append(
        "- Pinned inputs: "
        + "; ".join(
            f"`{v['path']}` (`{v['sha256'][:12]}…`)"
            for v in freeze["inputs"]["pinned"].values()
        )
        + f". The sha256 of each of the {freeze['inputs']['corpus']['files']} box-score files is in `{FREEZE}`."
    )
    return "\n".join(out) + "\n"


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
