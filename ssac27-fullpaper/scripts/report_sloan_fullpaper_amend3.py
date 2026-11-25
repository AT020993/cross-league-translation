#!/usr/bin/env python3
"""Render the Amendment 3 and 4 results note (E18-E24) from committed outputs.

Reads only the committed outputs of scripts/sloan_fullpaper_amend3.py and
scripts/sloan_fullpaper_amend4.py and their trimmed run receipts, and writes
docs/research/sloan-fullpaper-amend3-amend4-2026-11-11.md. No number is typed
here: every value is formatted from those files, and every result sentence is
the generator's licensed sentence. All results are EXPLORATORY.
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

import numpy as np
import pandas as pd

ARTIFACTS3 = Path("docs/research/artifacts/sloan-fullpaper-amend3-2026-11")
ARTIFACTS4 = Path("docs/research/artifacts/sloan-fullpaper-amend4-2026-11")
NOTE = Path("docs/research/sloan-fullpaper-amend3-amend4-2026-11-11.md")
CSV_FILES3 = (
    "e18_level.csv",
    "e18_league_rebased.csv",
    "e18_drift.csv",
    "e19_equivalents_by_refit.csv",
    "e19_stability.csv",
    "e19_tier_check.csv",
    "e20_gap_bins.csv",
    "e21_league_table_flips.csv",
    "e22_coverage_by_league.csv",
    "e23_refits.csv",
)
CSV_FILES4 = ("e24_level.csv", "e24_league_bias.csv", "e24_destination_mix.csv")

H, HT, O, D = (  # noqa: E741
    "history_only",
    "scheduled_history",
    "source_ridge_10",
    "history_destination_slope",
)
ARM_NAMES = {
    H: "History only (blind to both leagues)",
    HT: "History + translation",
    D: "History + destination (blind to the source league)",
    O: "League-aware (one number per league)",
}
LEAGUES = {
    "spain-acb": "Spain (ACB)",
    "france-pro-a": "France (Pro A)",
    "italy-lba": "Italy (LBA)",
    "greece-a1": "Greece (A1)",
    "turkey-bsl": "Turkey (BSL)",
    "israel-bsl": "Israel (Winner League)",
    "aba-league": "Adriatic (ABA)",
    "germany-bbl": "Germany (BBL)",
    "vtb": "VTB United League",
    "lithuania-lkl": "Lithuania (LKL)",
}
PAIR_NAMES = {
    "all": "All pairs",
    "cross": "Different source leagues",
    "same": "Same source league",
}


def num(value: float, digits: int = 2, signed: bool = False) -> str:
    return f"{value:+.{digits}f}" if signed else f"{value:.{digits}f}"


def span(low: float, high: float, digits: int = 2) -> str:
    return f"{low:.{digits}f} to {high:.{digits}f}"


def pct(value: float, digits: int = 1) -> str:
    return f"{100 * value:.{digits}f}%"


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


def level_cell(level: pd.DataFrame, arm: str, scope: str) -> str:
    row = level.loc[level.arm.eq(arm) & level.scope.eq(scope)].iloc[0]
    return f"{num(row.mean_signed_error, signed=True)} ({span(row.ci95_low, row.ci95_high)})"


def section_e18(s3: dict, a3: Path, s4: dict, a4: Path) -> list:
    level3 = pd.read_csv(a3 / "e18_level.csv")
    level4 = pd.read_csv(a4 / "e24_level.csv")
    seasons = sorted(
        int(x.split(":")[1]) for x in level3.scope.unique() if x.startswith("season:")
    )
    last = f"season:{seasons[-1]}"
    out = ["## E18 and E24a. The level of the forecasts", ""]
    out.append(
        "Mean signed error, forecast minus actual EFF/36, with 95% cluster-bootstrap intervals. Below zero, the forecast expected less than arrivals delivered."
    )
    out.append("")
    rows = []
    for arm, level in ((H, level3), (HT, level3), (D, level4), (O, level3)):
        rows.append(
            [
                ARM_NAMES[arm],
                level_cell(level, arm, "all"),
                level_cell(level, arm, "destination:euroleague"),
                level_cell(level, arm, "destination:eurocup"),
                level_cell(level, arm, last),
            ]
        )
    out += table(
        [
            "Forecast",
            "All arrivals",
            "EuroLeague",
            "EuroCup",
            f"Destination season {seasons[-1]}",
        ],
        rows,
    )
    out.append("")
    for line in s3["e18"]["level_licence"]:
        out.append(f"- {line['sentence']}")
    out += ["", "League-aware forecast by destination season:", ""]
    rows = []
    for season in seasons:
        row = level3.loc[level3.arm.eq(O) & level3.scope.eq(f"season:{season}")].iloc[0]
        rows.append([season, int(row.n), level_cell(level3, O, f"season:{season}")])
    out += table(
        ["Destination season", "Arrivals", "Mean signed error (95% interval)"], rows
    )
    drift = pd.read_csv(a3 / "e18_drift.csv")
    out += [
        "",
        "### E18c. Continental EFF/36 by competition and season (descriptive)",
        "",
    ]
    out.append(
        '"Minus earlier seasons" compares a season with the mean of all earlier seasons from 2017, the level a walk-forward refit had seen. This table licenses description only, and no statement about cause.'
    )
    out.append("")
    rows = []
    for r in drift.itertuples():
        rows.append(
            [
                r.competition,
                int(r.season),
                int(r.arrivals),
                num(r.arrivals_mean_eff36),
                "n/a"
                if np.isnan(r.arrivals_minus_earlier)
                else num(r.arrivals_minus_earlier, signed=True),
                int(r.player_seasons),
                num(r.all_players_mean_eff36),
                "n/a"
                if np.isnan(r.all_players_minus_earlier)
                else num(r.all_players_minus_earlier, signed=True),
            ]
        )
    out += table(
        [
            "Competition",
            "Season",
            "Arrivals",
            "Arrivals: mean",
            "minus earlier seasons",
            "All player-seasons with 8+ games",
            "All: mean",
            "minus earlier seasons",
        ],
        rows,
    )
    return out


def section_leagues(s3: dict, a3: Path, s4: dict, a4: Path) -> list:
    e18 = pd.read_csv(a3 / "e18_league_rebased.csv").set_index("source_league")
    e24 = pd.read_csv(a4 / "e24_league_bias.csv").set_index("source_league")
    mix = pd.read_csv(a4 / "e24_destination_mix.csv").set_index("source_league")
    out = ["## E18b and E24. League biases measured against the average arrival", ""]
    out.append(
        "Each league's mean signed error minus the mean signed error of all 674 arrivals, computed inside every bootstrap draw. Holm-adjusted p-values are across the 10 leagues, separately for the history-only forecast (E18b) and the destination-aware forecast (E24b)."
    )
    out.append("")
    rows = []
    for league in e18.sort_values(f"rebased_{H}").index:
        a, b = e18.loc[league], e24.loc[league]
        rows.append(
            [
                LEAGUES[league],
                int(a.arrivals),
                pct(mix.loc[league, "euroleague_share"], 0),
                f"{num(a[f'rebased_{H}'], signed=True)} ({span(a[f'rebased_ci95_low_{H}'], a[f'rebased_ci95_high_{H}'])})",
                num(a[f"rebased_p_holm_{H}"], 3),
                f"{num(b[f'rebased_{D}'], signed=True)} ({span(b[f'rebased_ci95_low_{D}'], b[f'rebased_ci95_high_{D}'])})",
                num(b[f"rebased_p_holm_{D}"], 3),
                f"{num(a[f'rebased_{O}'], signed=True)} ({span(a[f'rebased_ci95_low_{O}'], a[f'rebased_ci95_high_{O}'])})",
            ]
        )
    out += table(
        [
            "Source league",
            "Arrivals",
            "Share to EuroLeague",
            "History only",
            "Holm p",
            "History + destination",
            "Holm p",
            "League-aware",
        ],
        rows,
    )
    out += ["", "Licensed league sentences:", ""]
    for frame in (e18, e24):
        for r in frame.loc[frame.licence.eq("licensed")].itertuples():
            out.append(f"- {r.sentence}")
    out += [
        "",
        "Spread of the league biases (arrival-weighted root mean square of the 10 re-based biases; inflated by sampling noise in every arm, so the contrasts are read, not the levels):",
        "",
    ]
    spread3, spread4 = s3["e18"]["spread"], s4["e24"]["spread"]
    rows = [
        [ARM_NAMES[H], num(spread3[H]["point"]), span(*spread3[H]["ci95"])],
        [ARM_NAMES[D], num(spread4[D]["point"]), span(*spread4[D]["ci95"])],
        [ARM_NAMES[O], num(spread3[O]["point"]), span(*spread3[O]["ci95"])],
    ]
    out += table(["Forecast", "Spread", "95% interval"], rows)
    out.append("")
    c18 = s3["e18"]["spread_contrast"]
    primary, secondary = (
        s4["e24"]["contrasts"]["primary"],
        s4["e24"]["contrasts"]["secondary"],
    )
    rows = [
        [
            "E18: history only minus league-aware",
            num(c18["point"]),
            span(*c18["ci95"]),
            num(c18["mde_80"]),
            c18["sentence"],
        ],
        [
            "E24 primary: history + destination minus league-aware",
            num(primary["point"]),
            span(*primary["ci95"]),
            num(primary["mde_80"]),
            primary["sentence"],
        ],
        [
            "E24 secondary: history only minus history + destination",
            num(secondary["point"]),
            span(*secondary["ci95"]),
            num(secondary["mde_80"]),
            secondary["sentence"],
        ],
    ]
    out += table(
        [
            "Contrast",
            "Difference",
            "95% interval",
            "Detectable at 80% power",
            "Registered verdict",
        ],
        rows,
    )
    return out


def section_e19(s3: dict, a3: Path) -> list:
    summary = s3["e19"]["summary"]
    table19 = pd.read_csv(a3 / "e19_equivalents_by_refit.csv")
    out = [
        "## E19. Stability of the European League Equivalents across the yearly refits",
        "",
    ]
    out.append(
        f"- {summary['sentence']} ({summary['tier3_higher']} of {summary['comparisons']} comparisons; {summary['tier3_higher_without_thin_cells']} of {summary['comparisons_without_thin_cells']} without cells under 10 training arrivals.)"
    )
    out.append(f"- {summary['movement_sentence']}")
    out.append(
        "- The refits share most of their training data. This describes stability and is not a test."
    )
    for dest in ("euroleague", "eurocup"):
        sub = table19.loc[table19.destination.eq(dest)]
        fits = list(dict.fromkeys(sub.fit))
        wide = sub.pivot(
            index="source_league", columns="fit", values="acb16_equivalent_eff36"
        )
        order = wide[fits[-1]].sort_values().index
        out += ["", f"Equivalent of an ACB 16, {dest} arrivals:", ""]
        out += table(
            ["Source league", *fits],
            [
                [LEAGUES[league], *[num(wide.loc[league, f], 1) for f in fits]]
                for league in order
            ],
        )
    return out


def section_e20_e21(s3: dict, a3: Path) -> list:
    bins = pd.read_csv(a3 / "e20_gap_bins.csv")
    licence = s3["e20"]["licence"]
    out = ["## E20. How large a forecast gap can be trusted", ""]
    out.append(
        "Share of pairs (same competition and season) in which the arrival with the higher forecast had the higher realised EFF/36, by the size of the gap between the two forecasts."
    )
    out.append("")
    rows = []
    primary = bins.loc[bins.arm.eq(O) & bins.pair_type.eq("all")].sort_values("bin")
    cross = bins.loc[bins.arm.eq(O) & bins.pair_type.eq("cross")].set_index("bin")
    blind = bins.loc[bins.arm.eq(H) & bins.pair_type.eq("all")].set_index("bin")
    for r in primary.itertuples():
        rows.append(
            [
                r.gap_eff36,
                f"{r.pairs:,}",
                f"{pct(r.share_correct)} ({pct(r.ci95_low)} to {pct(r.ci95_high)})",
                f"{pct(cross.loc[r.bin, 'share_correct'])} ({int(cross.loc[r.bin, 'pairs']):,} pairs)",
                f"{pct(blind.loc[r.bin, 'share_correct'])} ({int(blind.loc[r.bin, 'pairs']):,} pairs)",
            ]
        )
    out += table(
        [
            "Forecast gap, EFF/36",
            "Pairs",
            "League-aware forecast: right (95% interval)",
            "Cross-league pairs only",
            "History-only forecast",
        ],
        rows,
    )
    out.append("")
    for block in licence["trust"].values():
        out.append(f"- {block['sentence']}")
    out.append(f"- {licence['coin_flip_below_1']['sentence']}")
    flips = pd.read_csv(a3 / "e21_league_table_flips.csv")
    out += ["", "## E21. How often the league table changes a ranking", ""]
    rows = [
        [
            PAIR_NAMES[r.pair_type],
            f"{r.pairs:,}",
            pct(r.flip_share),
            f"{pct(r.right_share)} ({pct(r.right_share_ci95_low)} to {pct(r.right_share_ci95_high)})",
        ]
        for r in flips.itertuples()
    ]
    out += table(
        [
            "Pairs",
            "Number",
            "Orderings the league table changes",
            "Changes that were right (95% interval)",
        ],
        rows,
    )
    out += [
        "",
        f"- {s3['e21']['licence']['sentence']}",
        f"- Note: {s3['e21']['licence']['note']}.",
    ]
    return out


def section_e22(s3: dict, a3: Path) -> list:
    cover = pd.read_csv(a3 / "e22_coverage_by_league.csv")
    out = ["## E22. Error-band coverage by source league", ""]
    out.append(
        "Registered E8 walk-forward conformal bands for the league-aware forecast, test seasons 2021-2025, with Wilson 95% intervals."
    )
    out.append("")
    low = cover.loc[np.isclose(cover.level, 0.80)].set_index("source_league")
    high = cover.loc[np.isclose(cover.level, 0.95)].set_index("source_league")
    rows = []
    for league in low.sort_values("coverage").index:
        a, b = low.loc[league], high.loc[league]
        rows.append(
            [
                LEAGUES[league],
                int(a.n),
                f"{pct(a.coverage)} ({pct(a.wilson95_low)} to {pct(a.wilson95_high)})",
                f"{pct(b.coverage)} ({pct(b.wilson95_low)} to {pct(b.wilson95_high)})",
            ]
        )
    out += table(
        ["Source league", "Arrivals", "80% bands: coverage", "95% bands: coverage"],
        rows,
    )
    licence = s3["e22"]["licence"]
    out += ["", f"- {licence['range_sentence']}", f"- {licence['sentence']}"]
    by_season = s3["e22"]["by_season"]["0.80"]
    out.append(
        "- 80% coverage by destination season: "
        + ", ".join(
            f"{k}: {pct(v['coverage'])} (n = {v['n']})" for k, v in by_season.items()
        )
        + "."
    )
    return out


def section_e23(s3: dict) -> list:
    a, b = s3["e23"]["a"], s3["e23"]["b"]
    m1, m2, wf = a["M1"], a["M2"], a["walk_forward_contrasts"]
    out = ["## E23. The above-average-season discount", ""]
    out.append(
        "M0 is the registered league-aware model (a flag for a source season above the player's earlier career rate). M1 adds the size of the jump, u = max(0, source rate minus earlier career rate). M2 replaces the flag with the jump. M0 stays the paper's model whatever is shown here."
    )
    out.append("")
    rows = [
        [
            "M0, flag",
            num(a["M0"]["flag"], signed=True),
            "registered in E12",
            "registered in E12",
        ],
        [
            "M1, flag",
            num(m1["flag"], signed=True),
            span(*m1["flag_ci95"]),
            ", ".join(num(x, signed=True) for x in m1["walk_forward_flag"]),
        ],
        [
            "M1, jump (per EFF/36 above history)",
            num(m1["jump"], 3, signed=True),
            span(*m1["jump_ci95"], 3),
            ", ".join(num(x, signed=True) for x in m1["walk_forward_jump"]),
        ],
        [
            "M2, jump (per EFF/36 above history)",
            num(m2["jump"], 3, signed=True),
            span(*m2["jump_ci95"], 3),
            ", ".join(num(x, signed=True) for x in m2["walk_forward_jump"]),
        ],
    ]
    out += table(
        [
            "Coefficient",
            "Full fit through 2025",
            "95% interval",
            "Six walk-forward refits",
        ],
        rows,
    )
    out.append("")
    rows = [
        [
            name,
            num(block["mae_variant"], 3),
            num(block["mae_m0"], 3),
            f"{num(block['difference_positive_favours_variant'], 3, signed=True)} ({span(*block['ci95'], 3)})",
        ]
        for name, block in wf.items()
    ]
    out += table(
        [
            "Variant",
            "Walk-forward MAE on the 674",
            "M0",
            "M0 minus variant (95% interval)",
        ],
        rows,
    )
    jump = a["jump_among_flagged"]
    out += [
        "",
        f"- Registered verdict: {a['licence']['sentence']}",
        f"- The M1 jump coefficient is negative in {m1['walk_forward_negative']} of {len(m1['walk_forward_jump'])} refits.",
        f"- Among the {jump['n']} flagged training arrivals the median jump is {num(jump['median'])} EFF/36 (90th percentile {num(jump['p90'])}).",
        "",
        "### E23b. How common such signings are",
        "",
    ]
    arrivals, population, diff = (
        b["arrivals"],
        b["population"],
        b["difference_arrivals_minus_population"],
    )
    rows = [
        [
            "Training arrivals with a history",
            f"{arrivals['with_history']:,}",
            f"{pct(arrivals['share'])} ({pct(arrivals['ci95'][0])} to {pct(arrivals['ci95'][1])})",
        ],
        [
            "All comparable domestic player-seasons",
            f"{population['player_seasons_with_history']:,}",
            f"{pct(population['share'])} ({pct(population['ci95'][0])} to {pct(population['ci95'][1])})",
        ],
    ]
    out += table(
        [
            "Population",
            "Player-seasons",
            "Share after an above-average season (95% interval)",
        ],
        rows,
    )
    out += [
        "",
        f"- Difference: {num(100 * diff['point'], 1)} percentage points ({span(100 * diff['ci95'][0], 100 * diff['ci95'][1], 1)}).",
        f"- {b['licence']['sentence']}",
        f"- Comparison population: source seasons {population['source_seasons'][0]}-{population['source_seasons'][-1]}, {population['players']:,} players; {population['resampling']}.",
    ]
    return out


def provenance(label: str, summary: dict, receipt: dict) -> list:
    return [
        f"- **{label}:** generator `{receipt['entrypoint']}` (commit `{receipt['generator_commit'][:9]}`, sha256 `{receipt['generator_sha256'][:16]}…`), amendment commit `{summary['amendment_commit'][:9]}` (file sha256 `{summary['amendment_sha256'][:16]}…`), retained run `{receipt['run_dir']}`, {summary['n_boot']:,} bootstrap draws, seed {summary['seed']}, {receipt['inputs']} input files, {receipt['code_files']:,} code files, status {receipt['status']}."
    ]


def render(a3: Path, receipt3: dict, a4: Path, receipt4: dict) -> str:
    s3 = json.loads((Path(a3) / "summary.json").read_text())
    s4 = json.loads((Path(a4) / "summary.json").read_text())
    a3, a4 = Path(a3), Path(a4)
    out = [
        "# SSAC27 full paper: Amendment 3 and 4 results (E18-E24)",
        "",
        "**EXPLORATORY.** Destination seasons 2020-2025 had been examined before these analyses. Only the frozen 2026-27 test (P1) is confirmatory. Every number below is formatted by `scripts/report_sloan_fullpaper_amend3.py` from committed run outputs; every result sentence is the generator's registered wording.",
        "",
        "Pre-registrations: `docs/research/sloan-full-paper-preregistration-amendment-3-2026-11-11.md` and `docs/research/sloan-full-paper-preregistration-amendment-4-2026-11-11.md`, each pushed alone before its generator existed.",
        "",
        "## Specification",
        "",
    ]
    out += table(
        ["Field", "Registered choice"],
        [
            [
                "Unit",
                "One forecast = player × destination season, one continental destination. E20 and E21 use pairs of forecasts within a pool. E23b's comparison uses domestic player-seasons.",
            ],
            [
                "Population",
                f"The {s3['n_targets']} v10 target keys (2020-2025), pool A, recipe R1. E19 and E23 also use the {s3['e23']['a']['training_forecasts']:,} e9 training arrivals and the six walk-forward training sets. E22 uses the E8 test seasons 2021-2025.",
            ],
            [
                "Estimator",
                "E18, E24: mean signed error, overall and re-based by source league; spread of league biases. E19: the ACB-16 equivalent per league and refit. E20: share of pairs ordered correctly by forecast-gap bin. E21: flip share and right share. E22: band coverage by league. E23: coefficient on the jump above history; share of arrivals flagged.",
            ],
            [
                "Null",
                "Signed error = 0; re-based bias = 0; spread contrast = 0; right share = 0.5; coverage = nominal; coefficient = 0; paired MAE difference = 0. E19 and E20 are descriptive.",
            ],
            ["Filter", "v10 eligibility; targets fixed before scoring."],
            [
                "Key",
                "`player_name` × `season_dest`; pools = destination competition × destination season.",
            ],
            [
                "Uncertainty",
                f"Cluster bootstrap over destination club-seasons, {s3['n_boot']:,} draws, seed {s3['seed']}; two-way clustered intervals for paired MAE contrasts; Wilson 95% intervals for coverage by league; Holm across the 10 leagues.",
            ],
        ],
    )
    out += ["", "## What had been seen", ""]
    out.append("Before Amendment 3 was registered:")
    out += [f"- {x}" for x in s3["exposure"]["seen_before_registration_2026-11-11"]]
    out.append("")
    out.append("After Amendment 3 was registered and before its run:")
    out += [f"- {x}" for x in s3["exposure"]["seen_after_registration_before_this_run"]]
    out.append("")
    out.append("Before Amendment 4 was registered:")
    out += [f"- {x}" for x in s4["exposure"]["seen_before_registration"]]
    out += ["", "## Gates", "", "Amendment 3 run:", ""]
    out += gates_table(s3)
    out += ["", "Amendment 4 run:", ""]
    out += gates_table(s4)
    out.append("")
    for part in (
        section_e18(s3, a3, s4, a4),
        section_leagues(s3, a3, s4, a4),
        section_e19(s3, a3),
        section_e20_e21(s3, a3),
        section_e22(s3, a3),
        section_e23(s3),
    ):
        out += part
        out.append("")
    out += ["## Reproduction", ""]
    out += provenance("Amendment 3", s3, receipt3)
    out += provenance("Amendment 4", s4, receipt4)
    return "\n".join(out) + "\n"


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--artifacts3", type=Path, required=True)
    parser.add_argument("--artifacts4", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    receipt3 = json.loads((args.artifacts3 / "generator-receipt.json").read_text())
    receipt4 = json.loads((args.artifacts4 / "generator-receipt.json").read_text())
    note = render(args.artifacts3, receipt3, args.artifacts4, receipt4)
    args.out.mkdir(parents=True, exist_ok=False)
    (args.out / NOTE.name).write_text(note)
    print(f"{NOTE.name}: {len(note.splitlines())} lines")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
