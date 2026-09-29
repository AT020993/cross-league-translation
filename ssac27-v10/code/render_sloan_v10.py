# ruff: noqa: E402, E501 -- research prose templates are intentionally readable
"""Render the registered v10 comparison without changing the preserved v9 candidate.

Refuse incomplete evidence, changed fingerprints, missing target forecasts, and
unfilled manuscript tokens. All numerical text and plots read saved artifacts;
this module neither estimates factors nor fits forecasting models.
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
import json
import re
import shutil
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts import render_sloan_v9 as old  # noqa: E402
from scripts.translation_research_common import sha256_file  # noqa: E402

TITLE = (
    "What Does League Translation Add? A Benchmark for European Basketball Forecasts"
)
TEMPLATE = ROOT / "docs/plans/sloan-ssac27-manuscript-v10-template.md"
PROTOCOL = (
    ROOT / "docs/research/sloan-v10-slope-comparison-preregistration-2026-09-20.md"
)
POLICY_READBACK = (
    ROOT
    / "docs/research/artifacts/sloan-v10-support-policy-2026-09-20/primary-readback.json"
)
METHODS_TEMPLATE = ROOT / "docs/plans/sloan-ssac27-v10-methods-template.md"
V9 = ROOT / "docs/research/artifacts/sloan-v9-2026-09-19"
FIGURES = ("sloan_v10_benchmark_increments.png", "sloan_v10_verification_support.png")
PENALTIES = (1, 10, 100)
WORDS = {3: "three", 4: "four", 6: "six"}
CLUSTER_NAMES = {
    "player_club_season": "player/club-season",
    "player_season": "player/season",
}
PRESENTATION_DATE = "29 September 2026"
VARIANTS = old.d.VARIANTS
LABELS = {
    "official_corrected": "A. Full corrected pool",
    "verified_same_club_full": "B. Verified; full-season rates",
    "overlap_keys_full": "C. Overlap keys; full-season rates",
    "same_club": "D. Overlap-window rates",
}
FIGURE_LABELS = {
    "official_corrected": "A. Full pool",
    "verified_same_club_full": "B. Verified; full-season rates",
    "overlap_keys_full": "C. Verified; overlap keys",
    "same_club": "D. Verified; overlap-window rates",
}
num, interval, table = old.number, old.interval, old.table


def read(path):
    return json.loads(Path(path).read_text())


def check(path, digest):
    if not Path(path).is_file() or sha256_file(Path(path)) != digest:
        raise ValueError(f"fingerprint mismatch: {path}")


def load(analysis):
    analysis = Path(analysis)
    status = read(analysis / "status.json")
    if status.get("status") != "complete":
        raise ValueError("incomplete v10 evidence")
    check(analysis / "summary.json", status["summary_sha256"])
    new = read(analysis / "summary.json")
    if new.get("status") != "complete" or new["common_n"] != new["target_n"]:
        raise ValueError("incomplete original target: candidate rendering refused")
    check(PROTOCOL, new["protocol_sha256"])
    for name, digest in new["code_hashes"].items():
        check(ROOT / name, digest)
    manifest = read(V9 / "render_manifest.json")
    check(V9 / "diagnostics.json", manifest["diagnostics_sha256"])
    check(V9 / "preparation.json", manifest["preparation_sha256"])
    check(V9 / "diagnostics.json", new["v9_diagnostics_sha256"])
    check(V9 / "preparation.json", new["v9_preparation_sha256"])
    prior, prep = read(V9 / "diagnostics.json"), read(V9 / "preparation.json")
    if new["target_n"] != prior["common_n"] or tuple(sorted(new["variants"])) != tuple(
        sorted(VARIANTS)
    ):
        raise ValueError("v9 target or factor pools changed")
    for v in VARIANTS:
        if tuple(sorted(new["variants"][v]["scenarios"])) != tuple(
            sorted(prior["variants"][v]["scenarios"])
        ):
            raise ValueError("missing registered scenarios")
        for scenario in new["variants"][v]["scenarios"].values():
            if (
                scenario["n"] != new["target_n"]
                or scenario["target_unscored"]
                or scenario["target_missing"]
            ):
                raise ValueError("incomplete target scenario")
            for p in PENALTIES:
                c = scenario["contrasts"][f"cell_slope_{p}_increment"]
                if (
                    c["left"] != f"cell_slope_{p}"
                    or c["right"] != f"cell_slope_{p}_scheduled"
                ):
                    raise ValueError("contrast labels changed")
                value = (
                    scenario["metrics"][c["left"]]["mae"]
                    - scenario["metrics"][c["right"]]["mae"]
                )
                if not np.isclose(
                    value, c["player_club_season"]["difference"], atol=1e-9, rtol=0
                ):
                    raise ValueError("metric/contrast inconsistency")
    return new, prior, prep


def contrast(record, penalty, cluster="player_club_season"):
    return record["contrasts"][f"cell_slope_{penalty}_increment"][cluster]


def limits(variant, penalty, prefix):
    vals = [
        contrast(r, penalty)["difference"]
        for name, r in variant["scenarios"].items()
        if name.startswith(prefix)
    ]
    if not vals or not np.isfinite(vals).all():
        raise ValueError("missing refit sensitivity")
    return [min(vals), max(vals)]


def robust(new):
    for v in new["variants"].values():
        for p in PENALTIES:
            for clustering in ("player_club_season", "player_season"):
                c = contrast(v["scenarios"]["reference"], p, clustering)
                ci = c["ci95"]
                if (
                    ci is None
                    or len(ci) != 2
                    or not np.isfinite(ci).all()
                    or ci[0] > ci[1]
                    or ci[0] <= 0
                    or not np.isfinite(c["difference"])
                    or c["difference"] <= 0
                ):
                    return False
            if any(limits(v, p, prefix)[0] <= 0 for prefix in ("omit_", "seed_")):
                return False
    return True


def increments(prior, new, cluster="player_club_season"):
    r = prior["variants"]["official_corrected"]["scenarios"]["reference"]
    n = new["variants"]["official_corrected"]["scenarios"]["reference"]
    return [
        (
            "History only",
            r["contrasts"]["original_vs_history_only"][cluster],
        ),
        (
            "History + destination intercept and slope",
            r["contrasts"]["destination_increment"][cluster],
        ),
        *[
            (
                f"+ Source offsets; penalty {p}",
                r["contrasts"][f"source_ridge_{p}_increment"][cluster],
            )
            for p in PENALTIES
        ],
        *[
            (f"+ Offsets and cell slopes; penalty {p}", contrast(n, p, cluster))
            for p in PENALTIES
        ],
    ]


def restriction_text():
    diagnostic_path = (
        ROOT / "docs/research/artifacts/sloan-support-loss-2026-09-28/readback.json"
    )
    diagnostic = ""
    if not diagnostic_path.exists():
        raise ValueError("missing registered support diagnostic")
    if diagnostic_path.exists():
        from scripts.sloan_support_loss import report_text
        from scripts.sloan_support_loss_review import stratified_text

        state = read(diagnostic_path.parent / "status.json")
        if state.get("status") != "complete":
            raise ValueError("incomplete support diagnostic")
        check(diagnostic_path, state["readback_sha256"])
        d = read(diagnostic_path)
        if d.get("status") != "complete" or d.get("repetition_count") != 400:
            raise ValueError("incomplete support-restriction readback")
        if any(
            r["incomplete_targets"]
            or r["repetitions"] != 200
            or any(m["available"] != 200 for m in r["mae"].values())
            or r["support"]["unavailable"]["maximum"] != 0
            for r in d["controls"].values()
        ):
            raise ValueError("incomplete restriction target or factor support")
        check(diagnostic_path.parent / "results.md", d["results_sha256"])
        if report_text(d) != (diagnostic_path.parent / "results.md").read_text():
            raise ValueError("support diagnostic report disagrees with readback")
        check(
            ROOT / "docs/research/sloan-support-loss-preregistration-2026-09-28.md",
            d["protocol_sha256"],
        )
        check(ROOT / "scripts/sloan_support_loss.py", d["generator_sha256"])
        check(ROOT / "scripts/sloan_support_loss_review.py", d["verifier_sha256"])
        check(
            diagnostic_path.parent / "stratified-support.md",
            d["stratified_report_sha256"],
        )
        if (
            stratified_text(d)
            != (diagnostic_path.parent / "stratified-support.md").read_text()
        ):
            raise ValueError("stratified support report disagrees with readback")
        diagnostic = (
            "### Registered restriction diagnostic (28 September)\n\n"
            "After observing the support loss, we registered 200 random restrictions per control. "
            "Both reduce A to B's 1,537 pairs: one matches counts within each season; the other matches "
            "source league, destination competition and season counts. Sampling uses identities and strata, "
            "not outcomes. Each restriction refits the original factors and historical lags with 2,000 "
            "bootstrap draws, retaining the original regression-training keys and 674 forecast targets. "
            "Both original references reproduce before scoring. All 400 repetitions score every target "
            "in all 12 arms, with no unavailable factors. These are exploratory, conditional restrictions.\n\n"
            "Median and empirical"
        )
        diagnostic += report_text(d).split("Median and empirical", 1)[1]
        diagnostic = (
            diagnostic.replace("| cell_season_count |", "| Cell and season counts |")
            .replace("| season_count |", "| Season counts |")
            .replace("| full |", "| Full corrected pool |")
            .replace("| verified |", "| Verified pool |")
            .replace("| Nonfallback / 674 |", "| Supported (nonfallback) / 674 |")
        )
    el = d["references"]["verified"]["by_destination"]["euroleague"]
    season_el = d["controls"]["season_count"]["by_destination"]["euroleague"][
        "nonfallback"
    ]
    cell_el = d["controls"]["cell_season_count"]["by_destination"]["euroleague"][
        "nonfallback"
    ]
    diagnostic += (
        f"\nDestination-specific comparisons are less uniform. EuroLeague's verified pool retains "
        f"{el['nonfallback']}/{el['n']} nonfallback forecasts; season-count restrictions retain "
        f"a median {season_el['median']:.0f} (full range {season_el['minimum']:.0f}–{season_el['maximum']:.0f}), "
        f"whereas cell-and-season restrictions retain a median {cell_el['median']:.0f} "
        f"(full range {cell_el['minimum']:.0f}–{cell_el['maximum']:.0f}). "
        "The verified count is outside the first range and inside the second. This remains "
        "a conditional diagnostic, not a causal verification effect. The supplement reports "
        "every season and destination, with each original stratum denominator retained.\n"
    )
    details = stratified_text(d) + "\n\n"
    if diagnostic:

        def spread(value):
            return f"{num(value['median'])}; {interval([value['q025'], value['q975']])}; full {interval([value['minimum'], value['maximum']])}"

        details += "## Every restriction arm and support range\n\nValues are median; empirical 2.5th/97.5th percentiles; full range. They are not confidence intervals. All 200 repetitions per control are complete.\n\n"
        for control, record in d["controls"].items():
            details += f"### {control.replace('_', ' ')}\n\n"
            details += (
                table(
                    ["Support category", "Median; quantiles; full range"],
                    [[k, spread(v)] for k, v in record["support"].items()],
                )
                + "\n\n"
            )
            details += (
                table(
                    ["Arm", "MAE", "MAE change from full pool"],
                    [
                        [
                            arm,
                            spread(record["mae"][arm]),
                            spread(record["change_from_full"][arm]),
                        ]
                        for arm in record["mae"]
                    ],
                )
                + "\n\n"
            )
            details += (
                table(
                    ["Parent arm", "Translation increment"],
                    [[arm, spread(v)] for arm, v in record["increments"].items()],
                )
                + "\n\n"
            )
        nonfallback = d["controls"]
        diagnostic_reading = (
            f"The verified pool retains {d['references']['verified']['support']['nonfallback']} nonfallback forecasts. "
            f"Full random-restriction ranges are {int(nonfallback['season_count']['support']['nonfallback']['minimum'])}–{int(nonfallback['season_count']['support']['nonfallback']['maximum'])} "
            f"for season counts and {int(nonfallback['cell_season_count']['support']['nonfallback']['minimum'])}–{int(nonfallback['cell_season_count']['support']['nonfallback']['maximum'])} "
            "for cell-and-season counts. Thus comparably low support is attainable by reducing the original estimation pool. "
            "This does not establish that sample loss caused the observed A-to-B result, nor remove nonrandom verification and composition effects."
        )
        details += diagnostic_reading + "\n\n"

    return diagnostic, details


def abstract_paragraphs(new, prior, prep, restriction, destinations, supported):
    """Build the submission paragraphs, refusing any claim the saved evidence no longer supports."""
    counts = restriction["controls"]
    n = new["target_n"]
    a = prior["variants"]["official_corrected"]["scenarios"]["reference"]
    nr = new["variants"]["official_corrected"]["scenarios"]["reference"]
    primary = [
        contrast(new["variants"][v]["scenarios"]["reference"], p)
        for v in VARIANTS
        for p in PENALTIES
    ]
    alternative = [
        contrast(new["variants"][v]["scenarios"]["reference"], p, "player_season")
        for v in VARIANTS
        for p in PENALTIES
    ]
    if any(c["ci95"] is None for c in primary + alternative):
        raise ValueError("missing slope interval")
    # The 29 September abstract states each claim only if the saved evidence still
    # supports it; a changed artifact refuses the render instead of the wording drifting.
    if supported:
        raise ValueError("abstract wording assumes no robust incremental superiority")
    history = a["contrasts"]["original_vs_history_only"]["player_club_season"]
    destination = a["contrasts"]["destination_increment"]["player_club_season"]
    history_mae = a["metrics"]["history_only"]["mae"]
    destination_mae = a["metrics"][old.d.BASE]["mae"]
    if not np.isclose(
        history_mae - a["metrics"]["scheduled_history"]["mae"],
        history["difference"],
        atol=1e-9,
        rtol=0,
    ):
        raise ValueError("history metric/contrast inconsistency")
    if history["ci95"][0] <= 0:
        raise ValueError("abstract wording assumes a clear gain over history alone")
    if not destination["ci95"][0] <= 0 <= destination["ci95"][1]:
        raise ValueError("abstract wording assumes an uncertain destination gain")
    source_aware = {
        v: [
            prior["variants"][v]["scenarios"]["reference"]["contrasts"][
                f"source_ridge_{p}_increment"
            ]
            for p in PENALTIES
        ]
        + [
            new["variants"][v]["scenarios"]["reference"]["contrasts"][
                f"cell_slope_{p}_increment"
            ]
            for p in PENALTIES
        ]
        for v in VARIANTS
    }
    clusterings = ("player_club_season", "player_season")
    for records in source_aware.values():
        for c in records:
            for k in clusterings:
                if c[k]["ci95"] is None or c[k]["ci95"][0] > 0:
                    raise ValueError(
                        "source-aware wording assumes no favorable interval"
                    )
    full_aware = source_aware[VARIANTS[0]]
    if not all(
        c[k]["ci95"][0] <= 0 <= c[k]["ci95"][1] for c in full_aware for k in clusterings
    ):
        raise ValueError("abstract wording assumes full-pool intervals include zero")
    full_gains = [c["player_club_season"]["difference"] for c in full_aware]
    verified_aware = [c for v in VARIANTS[1:] for c in source_aware[v]]
    verified_gains = [c["player_club_season"]["difference"] for c in verified_aware]
    if not all(g < 0 for g in verified_gains):
        raise ValueError(
            "abstract wording assumes every verified-pool gain is negative"
        )
    verified_adverse = {
        k: sum(c[k]["ci95"][1] < 0 for c in verified_aware) for k in clusterings
    }
    if not all(
        nr["metrics"][f"cell_slope_{p}"]["mae"]
        > a["metrics"][f"source_ridge_{p}"]["mae"]
        for p in PENALTIES
    ):
        raise ValueError("abstract wording assumes slope baselines trail offsets")
    verified_pool = "verified_same_club_full"
    full_supported = n - a["fallbacks"]
    verified_supported = (
        n - prior["variants"][verified_pool]["scenarios"]["reference"]["fallbacks"]
    )
    season_median = int(counts["season_count"]["support"]["nonfallback"]["median"])
    cell_median = int(counts["cell_season_count"]["support"]["nonfallback"]["median"])
    if (
        verified_supported
        != restriction["references"]["verified"]["support"]["nonfallback"]
        or not season_median < verified_supported
    ):
        raise ValueError("abstract restriction wording no longer matches the readback")
    cell_record = counts["cell_season_count"]["support"]["nonfallback"]
    if cell_record["maximum"] > verified_supported:
        raise ValueError("abstract wording assumes the cell-matched control is capped")
    trimmed = {
        n - prior["variants"][v]["scenarios"]["reference"]["fallbacks"]
        for v in ("overlap_keys_full", "same_club")
    }
    if len(trimmed) != 1:
        raise ValueError("abstract wording assumes one overlap-trimmed support count")
    trimmed_supported = trimmed.pop()
    league = restriction["references"]["verified"]["by_destination"]["euroleague"]
    league_season = counts["season_count"]["by_destination"]["euroleague"][
        "nonfallback"
    ]
    league_cell = counts["cell_season_count"]["by_destination"]["euroleague"][
        "nonfallback"
    ]
    if not (
        league["nonfallback"] > league_season["maximum"]
        and league_cell["minimum"] <= league["nonfallback"] <= league_cell["maximum"]
    ):
        raise ValueError("abstract EuroLeague restriction exception no longer holds")
    verified_contrasts = {
        v: prior["variants"][v]["scenarios"]["reference"]["contrasts"]
        for v in VARIANTS[1:]
    }
    verified_history = [
        c["original_vs_history_only"]["player_club_season"]["difference"]
        for c in verified_contrasts.values()
    ]
    verified_destination = [
        c["destination_increment"]["player_club_season"]
        for c in verified_contrasts.values()
    ]
    if not all(g > 0 for g in verified_history):
        raise ValueError(
            "abstract wording assumes verified-pool history gains stay positive"
        )
    if not all(
        c["difference"] < 0 and c["ci95"][0] <= 0 <= c["ci95"][1]
        for c in verified_destination
    ):
        raise ValueError(
            "abstract wording assumes negative, uncertain verified destination gains"
        )
    competition_aware = verified_gains + [c["difference"] for c in verified_destination]
    seasons = sorted(
        int(s)
        for s in prior["variants"]["official_corrected"]["by_season"]["destination"]
    )

    def gain(value):
        return num(value).replace("-", "\u2212")

    def span(bounds):
        return f"{gain(bounds[0])} to {gain(bounds[1])}"

    def share(count, base):
        return f"{100 * count / base:.1f}%"

    history_share = share(history["difference"], history_mae)
    destination_share = share(destination["difference"], destination_mae)
    pairs_full = prep["counts"]["official_corrected"]
    pairs_verified = prep["counts"][verified_pool]
    paragraphs = [
        "**Introduction.** Clubs building EuroLeague and EuroCup rosters must compare players from different domestic leagues. "
        "Translation factors from players' same-season domestic and continental rates are widely used, "
        "but beating a league-blind forecast means little if a competition-aware one does as well. "
        "We ask what one translation recipe adds to competition-aware forecasts, and how stricter identity verification changes factor support.",
        f"**Methods.** Proballers domestic and EuroLeague API continental records define {n} forecasts of box-score efficiency per 36 minutes (EFF/36): "
        f"{destinations['euroleague']['n']} EuroLeague and {destinations['eurocup']['n']} EuroCup player-seasons ({seasons[0]}–{seasons[-1]}) "
        "with at least eight domestic games one season and eight continental games the next, excluding last season's continental regulars. "
        "Translation is added to four nested baselines: player history; plus destination intercept and slope; plus source-league offsets; "
        "plus source-by-destination (cell) slopes, the offset and cell-slope terms ridge-penalized at "
        f"{', '.join(str(p) for p in PENALTIES[:-1])} and {PENALTIES[-1]}. "
        f"Factors come from the full pool and {WORDS[len(VARIANTS) - 1]} identity-verified variants. "
        "Gain is the reduction in mean absolute error (MAE) from adding translation. "
        "Intervals (95%), clustered by player and club-season (alternatively, player and season), omit refitting uncertainty. "
        f"Forecasts use only earlier seasons; all comparisons score the same {n}. "
        "Outcomes were inspected earlier and verification reconstructed afterward, so comparisons are retrospective and exploratory.",
        f"**Results.** In the full pool, adding translation to player history lowers MAE from {num(history_mae)} to "
        f"{num(a['metrics']['scheduled_history']['mae'])} EFF/36 (gain {gain(history['difference'])}, a {history_share} reduction; "
        f"interval {span(history['ci95'])}). "
        f"With the destination known, the gain is {gain(destination['difference'])} ({destination_share}; "
        f"interval {span(destination['ci95'])}). "
        f"With source leagues modeled, full-pool gains span {gain(min(full_gains))} to {gain(max(full_gains))}, "
        "every interval including zero (Figure 1). "
        f"With verified factors, gains over history shrink to {num(min(verified_history))}–{num(max(verified_history))} "
        f"and every competition-aware gain is negative ({gain(min(competition_aware))} to {gain(max(competition_aware))}); "
        f"{verified_adverse['player_club_season']} of {len(verified_aware)} correlated source-aware player/club-season intervals exclude zero, "
        f"but only {verified_adverse['player_season']} player/season intervals ({WORDS.get(len(seasons), len(seasons))} seasons) do. "
        f"Verification cuts estimation pairs from {pairs_full:,} to {pairs_verified:,} and forecasts with a supported league-pair factor "
        f"(rather than a fallback) from {full_supported} of {n} ({share(full_supported, n)}) to {verified_supported} "
        f"({share(verified_supported, n)}; {trimmed_supported} with overlap trimming; Figure 2). "
        f"Across random {pairs_verified:,}-pair subsets, registered after this loss was seen, median supported forecasts are {season_median} (season-matched) "
        f"and {cell_median} (also league-pair-matched, maximum {verified_supported}): comparable support loss is attainable without verification; "
        "season-matched subsets lose more EuroLeague support.",
        "**Conclusion.** Translation's value depends on the comparator: with full-pool factors, "
        f"a {history_share} error reduction against a league-blind forecast, an uncertain {destination_share} against a destination-aware one, "
        "and none detectable against source-aware ones; with verified factors, competition-aware point estimates are small and negative. "
        "Clubs and analysts should test translation factors against forecasts that know both leagues, on the same players, "
        "and report fallback use. "
        "Findings cover one recipe, the EFF/36 outcome and an appearance-qualified, EuroCup-heavy population; "
        "they establish neither equivalence nor general harm. Recruitment benefit remains untested.",
    ]
    verified_parent_mae = [
        record["metrics"][f"{arm}_{p}"]["mae"]
        for v in VARIANTS[1:]
        for arm, record in (
            ("source_ridge", prior["variants"][v]["scenarios"]["reference"]),
            ("cell_slope", new["variants"][v]["scenarios"]["reference"]),
        )
        for p in PENALTIES
    ]
    evidence = {
        "verified_parent_mae": verified_parent_mae,
        "source_aware": source_aware,
        "clusterings": clusterings,
        "verified_aware": verified_aware,
        "verified_gains": verified_gains,
        "verified_adverse": verified_adverse,
    }
    return paragraphs, evidence


def near_zero_note(entries):
    """Explain interval bounds that display as 0.000 at three decimals."""
    notes = []
    for label, p, ci in entries:
        for side, bound in zip(("lower", "upper"), ci, strict=True):
            if bound != 0 and abs(bound) < 0.0005:
                verdict = "includes" if ci[0] <= 0 <= ci[1] else "excludes"
                notes.append(
                    f"{label} at penalty {p} has {side} bound {bound:+.5f}, displayed as {num(bound)}, "
                    f"so that interval {verdict} zero."
                )
    return " ".join(notes)


def offset_results(new, evidence):
    """Source-offset increments in every pool, plus notes for near-zero printed bounds."""
    source_aware = evidence["source_aware"]
    clusterings = evidence["clusterings"]
    verified_aware = evidence["verified_aware"]
    verified_gains = evidence["verified_gains"]
    verified_adverse = evidence["verified_adverse"]
    offsets = {v: source_aware[v][: len(PENALTIES)] for v in VARIANTS}
    offset_rows = [
        [
            LABELS[v],
            p,
            num(c["player_club_season"]["difference"]),
            interval(c["player_club_season"]["ci95"]),
            interval(c["player_season"]["ci95"]),
        ]
        for v in VARIANTS
        for p, c in zip(PENALTIES, offsets[v], strict=True)
    ]
    offset_adverse = {
        k: sum(c[k]["ci95"][1] < 0 for v in VARIANTS[1:] for c in offsets[v])
        for k in clusterings
    }
    largest_share = max(
        abs(g) / m
        for g, m in zip(verified_gains, evidence["verified_parent_mae"], strict=True)
    )
    offset_note = near_zero_note(
        [
            (f"{LABELS[v].split('.')[0]} ({CLUSTER_NAMES[k]})", p, c[k]["ci95"])
            for v in VARIANTS
            for p, c in zip(PENALTIES, offsets[v], strict=True)
            for k in clusterings
        ]
    )
    pools = WORDS[len(VARIANTS) - 1]
    text = (
        "\n\nOutside the full pool, the original source-offset benchmark also favors omitting translation. "
        "Its increments by factor pool are:\n\n"
        + table(
            [
                "Factor pool",
                "Penalty",
                "Improvement",
                "Player/club-season interval",
                "Player/season interval",
            ],
            offset_rows,
        )
        + ("\n\n" + offset_note if offset_note else "")
        + f"\n\nAcross the {pools} verified pools, all {len(verified_aware)} source-aware increments "
        f"(source offsets and cell slopes, each at {WORDS[len(PENALTIES)]} penalties) are negative, from "
        f"{num(min(verified_gains))} to {num(max(verified_gains))} (each at most {100 * largest_share:.1f}% of its "
        f"parent MAE in magnitude). Of these, {verified_adverse['player_club_season']} player/club-season intervals exclude zero "
        f"({offset_adverse['player_club_season']} source-offset and "
        f"{verified_adverse['player_club_season'] - offset_adverse['player_club_season']} cell-slope), whereas "
        f"{verified_adverse['player_season']} player/season intervals do. The full pool has no interval excluding zero "
        "under either specification. These adverse differences are small and depend on the clustering "
        "specification; they do not establish general harm."
    )
    rounding = (
        "Here and below, improvements are computed from unrounded MAEs and can differ by 0.001 "
        "from the difference of the displayed MAEs."
    )
    slope_note = " ".join(
        part
        for part in (
            near_zero_note(
                [
                    (
                        LABELS[v].split(".")[0],
                        p,
                        contrast(new["variants"][v]["scenarios"]["reference"], p)[
                            "ci95"
                        ],
                    )
                    for v in VARIANTS
                    for p in PENALTIES
                ]
            ),
        )
        if part
    )
    return offset_rows, text, rounding, slope_note


def texts(new, prior, prep):
    diagnostic, diagnostic_details = restriction_text()
    restriction = read(
        ROOT / "docs/research/artifacts/sloan-support-loss-2026-09-28/readback.json"
    )
    counts = restriction["controls"]
    n = new["target_n"]
    a = prior["variants"]["official_corrected"]["scenarios"]["reference"]
    nr = new["variants"]["official_corrected"]["scenarios"]["reference"]
    full = [contrast(nr, p) for p in PENALTIES]
    supported = robust(new)
    conclusion = (
        "The registered checks support a positive retrospective increment across the specified comparisons, conditional on these exposed data."
        if supported
        else "Robust incremental superiority is not established across the registered comparisons."
    )
    destinations = prior["variants"]["official_corrected"]["by_destination"][
        "destination"
    ]
    if sum(group["n"] for group in destinations.values()) != n:
        raise ValueError("destination counts do not conserve the forecast target")
    if not destinations["eurocup"]["n"] > destinations["euroleague"]["n"]:
        raise ValueError("abstract wording assumes a EuroCup-heavy target")
    paragraphs, evidence = abstract_paragraphs(
        new, prior, prep, restriction, destinations, supported
    )
    block = "**" + TITLE + "**\n\n" + "\n\n".join(paragraphs)
    words = len(block.split())
    if words >= 500:
        raise ValueError("title-inclusive abstract limit exceeded")
    abstract = (
        "# SSAC27 abstract — candidate v10\n\n"
        "Internal review candidate; not submitted or approved for release. V9 remains unchanged. "
        "Generated by scripts/render_sloan_v10.py.\n\n"
        "## Abstract v10 — SUBMISSION TEXT (author approval pending)\n\n"
        + block
        + f"\n\n*{words} words including title and section labels; whitespace count. {PRESENTATION_DATE} presentation revision; abstract rewritten for readers and verified-pool source-offset results added; original comparison unchanged.*\n\n"
        "## Figures\n\n"
        + "\n".join(f"{i}. figures/{f}" for i, f in enumerate(FIGURES, 1))
        + "\n\n[Manuscript](sloan-ssac27-manuscript-v10.md) · [Supplement](sloan-ssac27-v10-supplement.md) · "
        "[Evidence and release guide](sloan-v10-evidence-and-release-guide.md).\n"
    )
    benchmark = table(
        [
            "Baseline receiving translation",
            "MAE without",
            "MAE with",
            "MAE improvement",
            "Conditional 95% interval",
        ],
        [
            [
                label,
                num(a["metrics"][left]["mae"]),
                num(a["metrics"][right]["mae"]),
                num(c["difference"]),
                interval(c["ci95"]),
            ]
            for (label, c), (left, right) in zip(
                increments(prior, new)[:5],
                [
                    ("history_only", "scheduled_history"),
                    (old.d.BASE, old.d.ADJUSTED),
                    *[
                        (f"source_ridge_{p}", f"source_ridge_{p}_scheduled")
                        for p in PENALTIES
                    ],
                ],
                strict=True,
            )
        ],
    )
    benchmark += (
        "\n\nThese are paired with/without-translation comparisons within each baseline, "
        "not differences between unrelated best-performing models. All three penalties are retained. "
        f"The destination-slope comparison has MAE {num(a['metrics'][old.d.BASE]['mae'])} without and "
        f"{num(a['metrics'][old.d.ADJUSTED]['mae'])} with translation. Its player-by-season sensitivity interval is "
        f"{interval(a['contrasts']['destination_increment']['player_season']['ci95'])}; only six season clusters are available."
    )
    slope = table(
        [
            "Factor pool",
            "Penalty",
            "MAE without z",
            "MAE with z",
            "Improvement",
            "Conditional 95% interval",
        ],
        [
            [
                LABELS[v],
                p,
                num(
                    new["variants"][v]["scenarios"]["reference"]["metrics"][
                        f"cell_slope_{p}"
                    ]["mae"]
                ),
                num(
                    new["variants"][v]["scenarios"]["reference"]["metrics"][
                        f"cell_slope_{p}_scheduled"
                    ]["mae"]
                ),
                num(
                    contrast(new["variants"][v]["scenarios"]["reference"], p)[
                        "difference"
                    ]
                ),
                interval(
                    contrast(new["variants"][v]["scenarios"]["reference"], p)["ci95"]
                ),
            ]
            for v in VARIANTS
            for p in PENALTIES
        ],
    )
    slope += (
        "\n\n"
        + conclusion
        + " Penalty values index sensitivity comparisons; none is selected as the winner. These correlated conditional intervals are not simultaneous guarantees."
        + " {{SLOPE_NOTE}}"
    )
    slope += "\n\n" + table(
        ["Penalty", "Source offsets only: MAE", "Offsets + cell slopes, no z: MAE"],
        [
            [
                p,
                num(a["metrics"][f"source_ridge_{p}"]["mae"]),
                num(nr["metrics"][f"cell_slope_{p}"]["mae"]),
            ]
            for p in PENALTIES
        ],
    )
    slope += "\n\nMatching the feature's multiplicative form does not make the richer baseline empirically preferable. These absolute errors describe the fixed comparisons; no penalty or model is promoted from evaluation performance."
    all_reference = [new["variants"][v]["scenarios"]["reference"] for v in VARIANTS]
    reference_values = [contrast(r, p) for r in all_reference for p in PENALTIES]
    negative = sum(c["difference"] < 0 for c in reference_values)
    adverse_intervals = sum(
        c["ci95"] is not None and c["ci95"][1] < 0 for c in reference_values
    )
    slope += (
        f"\n\nOf the {len(reference_values)} reference contrasts, {negative} point estimates "
        f"favor omitting translation and {adverse_intervals} player/club-season intervals "
        "exclude zero in that direction."
    )
    if adverse_intervals:
        if all(
            contrast(r, p, "player_season")["ci95"] is not None
            and contrast(r, p, "player_season")["ci95"][0]
            <= 0
            <= contrast(r, p, "player_season")["ci95"][1]
            for r in all_reference
            for p in PENALTIES
        ):
            slope += " Every new reference player/season interval includes zero. Thus an adverse-effect inference also depends on the clustering specification; these results do not establish robust harm."
    offset_rows, offset_text, rounding, slope_note = offset_results(new, evidence)
    slope += offset_text
    slope = slope.replace("{{SLOPE_NOTE}}", slope_note)
    benchmark += " " + rounding
    support = table(
        [
            "Factor pool",
            "Estimation pairs",
            "Scored forecasts",
            "Supported (nonfallback) forecasts",
            "Factor fallbacks",
        ],
        [
            [
                LABELS[v],
                prep["counts"][v],
                n,
                n - prior["variants"][v]["scenarios"]["reference"]["fallbacks"],
                f"{prior['variants'][v]['scenarios']['reference']['fallbacks']}/{n}",
            ]
            for v in VARIANTS
        ],
    )
    rejects = prep["rejection_counts"]
    support += (
        f"\n\nThe exclusion ledger records {rejects['unverified_identity']:,} factor-pair records with unverified identity and "
        f"{rejects['multiple_clubs']} multi-club pairs before overlap eligibility, then "
        f"{rejects['fewer_than_eight_after_trimming']} pairs below the post-trim game requirement and "
        f"{rejects['invalid_appearance_minutes']} invalid-minute cases. Unverified does not mean incorrect. "
        "This is principally a verification-and-support sensitivity, not an experiment on changing clubs. "
        "Fallback is a factor-estimation policy; it is distinct from a refused forecast or an unknown appearance outcome."
    )
    refits = table(
        ["Pool", "Penalty", "Omission range", "Seed range"],
        [
            [
                LABELS[v],
                p,
                interval(limits(new["variants"][v], p, "omit_")),
                interval(limits(new["variants"][v], p, "seed_")),
            ]
            for v in VARIANTS
            for p in PENALTIES
        ],
    )
    figures = (
        f"![Paired gains from adding translation](figures/{FIGURES[0]})\n\n"
        "*Figure 1. Paired MAE improvements after adding translation to each specified baseline, "
        "full corrected pool. Positive favors translation. Solid whiskers: conditional 95% intervals clustered by player and club-season; dashed: clustered by player and season (six seasons). Hollow markers: the solid interval includes zero. "
        "The three offset penalties and three slope penalties are all retained.*\n\n"
        f"![Verification and estimation support](figures/{FIGURES[1]})\n\n"
        "*Figure 2. Factor-pool support and the increment beyond source offsets plus cell slopes. "
        "Bars partition the fixed forecast target into forecasts with a supported (nonfallback) league-pair factor and destination-mean fallbacks; annotations show separate estimation-pair counts, and triangles under pool B mark the median supported counts (season-matched and league-pair-matched) in the registered random restrictions to the same number of pairs. Pool labels in both figures abbreviate A-D; B-D use verified identities. The right panel shows the cell-slope family; source-offset increments by pool are tabulated in Section 5. No forecasts are refused. "
        "Solid and dashed whiskers and hollow markers follow Figure 1; both interval types condition on fitted forecasts and omit upstream refitting uncertainty. Restrictions change composition and support together; unverified does not mean incorrect.*"
    )
    policy = read(POLICY_READBACK)
    required_policy_checks = {
        "summary_status_complete",
        "summary_manifest_hash_bindings_match",
        "unchanged_primary_input_columns",
        "routing_exact",
        "primary_metrics_and_shares_match",
        "contribution_reconciliation",
        "all_56_parquet_row_counts_674",
        "all_saved_output_hashes_match",
    }
    if (
        policy["n"] != n
        or set(policy["checks"]) != required_policy_checks
        or not all(value is True for value in policy["checks"].values())
    ):
        raise ValueError("incomplete policy readback")
    check(
        ROOT / "docs/research/artifacts/sloan-v10-2026-09-20/summary.json",
        policy["frozen_v10_summary_sha256"],
    )
    policy_rows = []
    for label, arm, reference in (
        ("Source offsets", "source_ridge_10", a),
        ("Offsets + cell slopes", "cell_slope_10", nr),
    ):
        record = policy["primary"][arm]
        parent_mae = record["metrics"]["parent"]["mae"]
        policy_mae = record["metrics"]["policy"]["mae"]
        gain = record["contrasts"]["parent"]
        for bounds in gain["saved_intervals"].values():
            if (
                len(bounds) != 2
                or not np.isfinite(bounds).all()
                or not bounds[0] <= 0 <= bounds[1]
            ):
                raise ValueError(
                    "policy interval does not support the frozen conclusion"
                )
        if set(gain["saved_intervals"]) != {"player_club_season", "player_season"}:
            raise ValueError("incomplete policy intervals")
        if not np.isclose(
            parent_mae, reference["metrics"][arm]["mae"], atol=1e-9, rtol=0
        ) or not np.isclose(parent_mae - policy_mae, gain["mean"], atol=1e-9, rtol=0):
            raise ValueError("policy/parent metric inconsistency")
        policy_rows.append(
            [
                label,
                num(parent_mae),
                num(policy_mae),
                num(gain["mean"]),
                interval(gain["saved_intervals"]["player_club_season"]),
            ]
        )
    policy_results = table(
        [
            "Family (penalty 10)",
            "Parent MAE",
            "Policy MAE",
            "Improvement",
            "Conditional 95% interval",
        ],
        policy_rows,
    )
    policy_results += "\n\nThese are the amendment's prespecified primary full-pool comparisons, not a selected best penalty. Positive favors the policy. Intervals use player/recorded-club-season dependence; the player/season alternatives also include zero. The linked policy report retains comparisons with always using translation and every sensitivity. Values are read from the saved direct policy readback; no policy is refitted here."
    cluster = full[0]
    season_cluster = contrast(nr, PENALTIES[0], "player_season")
    methods = METHODS_TEMPLATE.read_text().replace(
        "{{CLUSTER_COUNTS}}",
        f"The saved full-pool reference has {n} rows, {cluster['components']['first']['clusters']} player groups, "
        f"{cluster['components']['second']['clusters']} recorded destination-competition/club/season groups and "
        f"{cluster['components']['intersection']['clusters']} intersection groups; the primary degrees of freedom are "
        f"{cluster['degrees_of_freedom']}. The player/season alternative has "
        f"{season_cluster['components']['second']['clusters']} season groups and {season_cluster['degrees_of_freedom']} degrees of freedom.",
    )
    if "{{" in methods:
        raise ValueError("unfilled methods token")
    e = next(
        e["values"] for e in prior["examples"] if e["selection"] == "median_change"
    )
    worked = (
        f"Consider {e['player_name'].title()}, with a {num(e['pir_per36_src'])} EFF/36 source rate in Turkey "
        f"and a EuroLeague forecast for stored destination season {int(e['season_dest'])}. "
        f"The supported factor {num(e['scheduled_multiplier_value'])} and lag correction {num(e['scheduled_k'])} "
        f"produce a translated feature of {num(e['scheduled_translated'])}. History alone forecasts "
        f"{num(e['history_only'])}; adding translation gives {num(e['scheduled_history'])}. Once destination "
        f"context and source offsets are included (penalty 10), the change is smaller: "
        f"{num(e['source_ridge_10'])} to {num(e['source_ridge_10_scheduled'])}. The observed rate is "
        f"{num(e['pir_per36_dest'])}. This existing case was selected by the median absolute change in the "
        "destination-aware prediction, without using its outcome. It illustrates the calculation, not average "
        "accuracy or a recruitment recommendation. Features use information from earlier seasons; their raw-source "
        "availability at the historical forecast date is not established. The supplement retains the selection rule "
        "and a fallback example."
    )
    replacements = {
        "WORKED_EXAMPLE": worked,
        "SUPPORT_DIAGNOSTIC": diagnostic,
        "MAIN_FINDING": f"On the same {n} eligible forecasts, adding the paired feature reduces mean absolute error (MAE) by "
        f"{num(a['contrasts']['original_vs_history_only']['player_club_season']['difference'])} EFF/36 against player history alone, "
        f"but by {num(old.primary(a)['difference'])} after the baseline includes destination context "
        f"(conditional 95% interval {interval(old.primary(a)['ci95'])}). "
        "Source-aware comparisons provide no robust incremental-superiority result. Stricter verification also shifts many forecasts "
        "from cell-specific factors to destination-mean fallbacks. Forecast coverage and factor support tell different stories.",
        "COHORT_COMPOSITION": f"The target contains {destinations['euroleague']['n']} EuroLeague and {destinations['eurocup']['n']} EuroCup forecasts. The pooled result consequently gives more weight to EuroCup; it is not a EuroLeague-only estimate.",
        "ABSTRACT_PROSE": " ".join(
            re.sub(r"\*\*\w+\.\*\* ", "", p) for p in paragraphs
        ),
        "BENCHMARK_RESULTS": benchmark,
        "SLOPE_RESULTS": slope,
        "SUPPORT_RESULTS": support,
        "POLICY_RESULTS": policy_results,
        "REFIT_RESULTS": refits,
        "CONCLUSION": conclusion
        + " The evidence supports three reporting practices: compare against competition-aware forecasts, separate factor support from forecast coverage, and evaluate a reliability rule by its forecast losses rather than its name. These are lessons for evaluating this additional modeling step, not proof that translation is unnecessary. Demonstrating club value requires an unexposed, decision-specific evaluation; further tuning on these seasons cannot provide it.",
        "FIGURES": figures,
    }
    manuscript = TEMPLATE.read_text()
    for name, value in replacements.items():
        manuscript = manuscript.replace("{{" + name + "}}", value)
    if re.search(r"\{\{[A-Z_]+\}\}", manuscript):
        raise ValueError("unfilled manuscript token")
    manuscript = "\n".join(line.rstrip() for line in manuscript.splitlines()) + "\n"
    _, _, _, parts = old.texts(prior, prep)
    supplement = (
        "# V10 numerical and exposure supplement\n\n"
        "Generated from frozen v9 evidence and the registered v10 comparison. Exploratory; not independent confirmation.\n\n"
        "## Original benchmark and error diagnostics\n\n"
        + parts["BENCHMARK_RESULTS"]
        + "\n\n## Source-offset increments in every factor pool\n\n"
        + table(
            [
                "Factor pool",
                "Penalty",
                "Improvement",
                "Player/club-season interval",
                "Player/season interval",
            ],
            offset_rows,
        )
        + "\n\n## Factor-pool transitions and original refits\n\n"
        + parts["OVERLAP_RESULTS"]
        + "\n\n"
        + parts["REFIT_RESULTS"]
        + "\n\n## Original seasonal and destination errors\n\n"
        + parts["ERROR_RESULTS"]
        + "\n\n## Outcome-blind worked examples\n\n"
        + parts["EXAMPLES"]
        + "\n\n## Every new reference arm\n\n"
    )
    for v in VARIANTS:
        r = new["variants"][v]["scenarios"]["reference"]
        supplement += (
            "### "
            + LABELS[v]
            + "\n\n"
            + table(
                [
                    "Arm",
                    "MAE",
                    "RMSE",
                    "Bias",
                    "Median absolute error",
                    "90th absolute error",
                ],
                [
                    [
                        arm,
                        *[
                            num(m[key])
                            for key in (
                                "mae",
                                "rmse",
                                "bias",
                                "median_absolute_error",
                                "p90_absolute_error",
                            )
                        ],
                    ]
                    for arm, m in r["metrics"].items()
                ],
            )
            + "\n\n"
        )
        supplement += (
            table(
                ["Penalty", "Primary interval", "Player/season interval"],
                [
                    [
                        p,
                        interval(contrast(r, p)["ci95"]),
                        interval(contrast(r, p, "player_season")["ci95"]),
                    ]
                    for p in PENALTIES
                ],
            )
            + "\n\n"
        )
        supplement += (
            table(
                ["Penalty", "Improved (%)", "Worsened (%)", "Tied (%)"],
                [
                    [
                        p,
                        *[
                            f"{100 * r['paired'][f'cell_slope_{p}_increment'][key]:.1f}"
                            for key in ("improved", "worsened", "tied")
                        ],
                    ]
                    for p in PENALTIES
                ],
            )
            + "\n\n"
        )
        for partition in ("by_season", "by_destination"):
            rows = []
            for p in PENALTIES:
                groups = new["variants"][v][partition][f"cell_slope_{p}_increment"]
                for name, val in groups.items():
                    rows.append(
                        [
                            p,
                            name,
                            val["n"],
                            num(val["mean_improvement"]),
                            num(val["contribution_to_total"]),
                        ]
                    )
            supplement += (
                table(
                    [
                        "Penalty",
                        partition.replace("_", " "),
                        "n",
                        "Mean improvement",
                        "Contribution",
                    ],
                    rows,
                )
                + "\n\n"
            )
    supplement += "## All new refit sensitivities\n\n" + refits + "\n\n"
    supplement += "## Native support and exclusions for every scenario\n\nWithin-scenario native support is the intersection across the six new arms. Common support intersects the original target across all 56 scenarios and six arms. Per-arm native metrics and counts are retained in the complete numerical summary.\n\n"
    for v in VARIANTS:
        support_rows = []
        for name, r in new["variants"][v]["scenarios"].items():
            unseen = []
            for field in ("unseen_source_rows", "unseen_cell_rows"):
                counts = [
                    sum(
                        f["arms"][f"cell_slope_{p}{suffix}"][field]
                        for f in r["fold_support"]
                    )
                    for p in PENALTIES
                    for suffix in ("", "_scheduled")
                ]
                if len(frozenset(counts)) != 1:
                    raise ValueError("unseen category counts differ across arms")
                unseen.append(counts[0])
            refusals = (
                "; ".join(
                    f"{reason}: {count}"
                    for reason, count in r["refusals"].items()
                    if reason
                )
                or "none"
            )
            support_rows.append(
                [
                    name,
                    r["native_n"],
                    r["common_n"],
                    r["target_missing"],
                    r["target_unscored"],
                    *unseen,
                    refusals,
                ]
            )
        supplement += (
            "### "
            + LABELS[v]
            + "\n\n"
            + table(
                [
                    "Scenario",
                    "Native",
                    "Common",
                    "Missing target",
                    "Unscored target",
                    "Unseen source",
                    "Unseen cell",
                    "Refusals",
                ],
                support_rows,
            )
            + "\n\n"
        )
    supplement += "Unseen-category counts sum forecast rows across evaluation folds, separately for each arm; all six arms agree. Counts are not pooled across arms. The complete fit records retain training scale, categories and training keys.\n\n"
    supplement += "## Primary reliability-policy readback\n\n" + policy_results + "\n\n"
    supplement += methods + "\n\n"
    supplement += diagnostic + "\n\n"
    supplement += diagnostic_details
    supplement += (
        "## Exposure and adverse evidence retained\n\n"
        "All six destination seasons were inspected in earlier model development. Chronological fitting does not undo that exposure. "
        "V9's 56 runs comprise four pools multiplied by one reference, nine single-season omissions and four alternative seeds; "
        "they are sensitivity runs, not independent replications. V10 reuses their upstream factor estimates and refits the new regressions. "
        "Omissions exclude direct estimation labels, while fixed historical player measurements may retain information from the omitted season.\n\n"
        "The original protected holdout remains PARTIAL. The equal-count scheduled-versus-transfer sensitivity reversed the earlier direction. "
        "Structural-multiplier simulations showed undercoverage for a different estimand. Four provisional aliases were verified; a conflicting "
        "birth-date identity remains quarantined in its affected season. Unknown identities and rounding-only discrepancies remain explicit. "
        "Neither aggregate numerical reproduction nor a conditional interval resolves raw-source validity or redistribution rights.\n\n"
        "The observed-appearance denominator excludes some unsuccessful arrivals. No-appearance records are not assigned zero EFF/36; "
        "the rate is undefined at zero minutes. Removing the positive-destination-EFF filter added no outer evaluation rows, so it does not "
        "validate the all-arrival denominator. The separate appearance-calibration/audit experiments are not evidence for this forecast model.\n\n"
        "The September 12 operating forecast lock is unchanged. It uses a different training/arm-selection pipeline and first scores "
        "on January 31, 2027, after the conditional December 4 invited-paper deadline. It cannot retrospectively confirm this candidate. "
        "No external scout or statistician review has occurred; the author has no assumed reviewer contacts. Final author approval, "
        "data-release scope, public repository delivery and submission are separate pending actions.\n\n"
        "[V9 source and audit record](sloan-ssac27-manuscript-draft.md) · "
        "[V10 protocol](../research/sloan-v10-slope-comparison-preregistration-2026-09-20.md) · "
        "[Release guide](sloan-v10-evidence-and-release-guide.md).\n"
    )
    return abstract, manuscript, supplement, words, replacements


def figures(new, prior, prep, out):
    from matplotlib.lines import Line2D
    from matplotlib.patches import Patch

    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 12,
            "axes.spines.top": False,
            "axes.spines.right": False,
        }
    )

    def gain(value):
        return num(value).replace("-", "\u2212")

    def includes_zero(ci):
        return ci is not None and ci[0] <= 0 <= ci[1]

    def marker(axis, x, y, color, ci, size, label=None, shape="o"):
        # Hollow: the primary interval includes zero; filled: it excludes zero.
        axis.scatter(
            x,
            y,
            s=size,
            marker=shape,
            facecolors="white" if includes_zero(ci) else color,
            edgecolors=color,
            linewidths=1.6,
            zorder=3,
            label=label,
        )

    cluster_legend = [
        Line2D(
            [0],
            [0],
            color="#334b60",
            lw=2,
            label="95% CI, clustered by player and club-season",
        ),
        Line2D(
            [0],
            [0],
            color="#334b60",
            lw=1.6,
            linestyle="--",
            label="95% CI, clustered by player and season (6 seasons)",
        ),
        Line2D(
            [0],
            [0],
            marker="o",
            ls="",
            markerfacecolor="white",
            markeredgecolor="#334b60",
            label="Hollow marker: solid interval includes zero",
        ),
    ]
    rows = increments(prior, new)
    alternative = increments(prior, new, "player_season")
    fig, ax = plt.subplots(figsize=(10.5, 6.6), layout="constrained")
    extent = [
        x for _, c in rows + alternative for x in (c["ci95"] or [c["difference"]])
    ]
    lo, hi = min(0, min(extent)), max(0, max(extent))
    width = max(hi - lo, 0.02)
    for i, ((label, c), (_, alt)) in enumerate(zip(rows, alternative, strict=True)):
        color = "#16677c" if i >= 5 else "#4b5866"
        for ci, offset, style in ((c["ci95"], -0.08, "-"), (alt["ci95"], 0.08, "--")):
            if ci is not None:
                ax.plot(ci, [i + offset] * 2, color=color, lw=2, linestyle=style)
        marker(ax, c["difference"], i, color, c["ci95"], 46)
        ax.text(hi + 0.04 * width, i, gain(c["difference"]), va="center", fontsize=12)
    ax.axvline(0, color="#89949e", lw=1)
    for boundary in (1.5, 4.5):
        ax.axhline(boundary, color="#dce2e8", lw=1)
    ax.set_yticks(np.arange(len(rows)), [r[0] for r in rows])
    ax.set_ylim(len(rows) - 0.4, -0.65)
    ax.set_xlim(lo - 0.07 * width, hi + 0.2 * width)
    ax.set_xlabel(
        "Gain from adding translation (EFF/36): MAE without \u2212 MAE with\npositive favors translation"
    )
    ax.set_title(
        "Translation's gain depends on the baseline it is added to\n"
        f"Full pool; the same {new['target_n']} forecasts in every comparison",
        loc="left",
        pad=12,
        fontweight="bold",
        fontsize=13,
    )
    ax.legend(
        handles=cluster_legend,
        loc="center",
        bbox_to_anchor=(0.58, 0.15),
        fontsize=10.5,
        frameon=False,
    )
    ax.grid(axis="x", color="#e8edf0", lw=0.7)
    ax.set_axisbelow(True)
    fig.savefig(out / FIGURES[0], dpi=200)
    plt.close(fig)

    fig, axes = plt.subplots(
        1,
        2,
        figsize=(11.5, 6.6),
        gridspec_kw={"width_ratios": [1.0, 1.1]},
        layout="constrained",
    )
    n = new["target_n"]
    y = np.arange(4)
    fallbacks = [
        prior["variants"][v]["scenarios"]["reference"]["fallbacks"] for v in VARIANTS
    ]
    supported = np.array([n - f for f in fallbacks])
    axes[0].barh(y, supported / n, color="#16677c", height=0.46)
    axes[0].barh(
        y, np.array(fallbacks) / n, left=supported / n, color="#d5dee3", height=0.46
    )
    axes[0].set_yticks(y, [FIGURE_LABELS[v] for v in VARIANTS], fontsize=11.5)
    for i, v in enumerate(VARIANTS):
        axes[0].text(
            0.012,
            i - 0.34,
            f"{supported[i]}/{n} supported ({100 * supported[i] / n:.1f}%); {prep['counts'][v]:,} pairs",
            fontsize=10.5,
            va="center",
        )
    restriction = read(
        ROOT / "docs/research/artifacts/sloan-support-loss-2026-09-28/readback.json"
    )
    verified_row = VARIANTS.index("verified_same_club_full")
    medians = [
        restriction["controls"][key]["support"]["nonfallback"]["median"]
        for key in ("season_count", "cell_season_count")
    ]
    axes[0].scatter(
        [median / n for median in medians],
        [verified_row + 0.31] * len(medians),
        marker="^",
        s=46,
        color="#1b1f24",
        zorder=3,
    )
    axes[0].text(
        0.24,
        verified_row,
        f"\u25b2 random {prep['counts']['verified_same_club_full']:,}-pair subsets,\n"
        f"median {medians[0]:.0f} (season-matched)\nor {medians[1]:.0f} (league-pair-matched)",
        fontsize=9,
        va="center",
        color="#1b1f24",
    )
    axes[0].set_xlim(0, 1)
    axes[0].set_xticks([0, 0.25, 0.5, 0.75, 1], ["0%", "25%", "50%", "75%", "100%"])
    axes[0].set_title(
        "Supported league-pair factors",
        loc="left",
        fontweight="bold",
        fontsize=12.5,
    )
    axes[0].set_xlabel(f"Share of the {n} forecasts (none refused)")
    axes[0].legend(
        handles=[
            Patch(color="#16677c", label="Supported league-pair factor"),
            Patch(color="#d5dee3", label="Destination-average fallback"),
        ],
        loc="lower center",
        fontsize=10.5,
        frameon=False,
    )
    colors = ("#12687d", "#ae6734", "#72578d")
    penalty_legend = []
    shapes = ("o", "s", "^")
    for p, offset, color, shape in zip(
        PENALTIES, (-0.23, 0, 0.23), colors, shapes, strict=True
    ):
        penalty_legend.append(
            Line2D([0], [0], marker=shape, ls="", color=color, label=f"Penalty {p}")
        )
        for i, v in enumerate(VARIANTS):
            r = new["variants"][v]["scenarios"]["reference"]
            c = contrast(r, p)
            alt = contrast(r, p, "player_season")
            for ci, delta, style in (
                (c["ci95"], -0.04, "-"),
                (alt["ci95"], 0.04, "--"),
            ):
                if ci is not None:
                    axes[1].plot(
                        ci,
                        [i + offset + delta] * 2,
                        color=color,
                        lw=1.6,
                        linestyle=style,
                    )
            marker(
                axes[1], c["difference"], i + offset, color, c["ci95"], 52, shape=shape
            )
    axes[1].axvline(0, color="#89949e", lw=1)
    axes[1].set_yticks(y, [""] * 4)
    axes[1].set_title(
        "Gain beyond offsets and cell slopes\n(cell-slope family only)",
        loc="left",
        fontweight="bold",
        fontsize=12.5,
    )
    axes[1].set_xlabel("Gain (EFF/36); positive favors translation")
    axes[1].legend(
        handles=penalty_legend + cluster_legend,
        loc="lower left",
        fontsize=9.5,
        ncol=1,
        frameon=False,
    )
    for ax in axes:
        ax.set_ylim(5.1, -0.65)
        ax.grid(axis="x", color="#e8edf0", lw=0.7)
        ax.set_axisbelow(True)
    fig.suptitle(
        f"Supported forecasts: {100 * supported[0] / n:.1f}% with the full pool, "
        f"{100 * supported[verified_row] / n:.1f}% or less with verified pools; all {n} remain scored",
        fontsize=14,
        fontweight="bold",
    )
    fig.savefig(out / FIGURES[1], dpi=200)
    plt.close(fig)


def render(analysis, out, update=False):
    out = Path(out)
    if out.exists() and any(out.iterdir()):
        raise ValueError("output must be new or empty")
    new, prior, prep = load(analysis)
    abstract, manuscript, supplement, words, parts = texts(new, prior, prep)
    out.mkdir(parents=True, exist_ok=True)
    for filename, content in (
        ("abstract.md", abstract),
        ("manuscript.md", manuscript),
        ("supplement.md", supplement),
    ):
        (out / filename).write_text(content)
    block = abstract.split(
        "## Abstract v10 — SUBMISSION TEXT (author approval pending)\n\n", 1
    )[1].split(f"\n\n*{words} words", 1)[0]
    (out / "submission-text.txt").write_text(block.replace("**", "") + "\n")
    review = (
        "# Abstract review: "
        + TITLE
        + "\n\nInternal candidate v10; not submitted.\n\n"
        + block.split("\n\n", 1)[1]
        + "\n\n"
        + parts["FIGURES"]
        + "\n"
    )
    (out / "abstract-review.md").write_text(review)
    # The upload copy carries no review labels; figure labels stay bare so captions
    # cannot push a strict reader's word count past the abstract limit.
    submission = (
        "# "
        + TITLE
        + "\n\n"
        + block.split("\n\n", 1)[1]
        + "\n\n"
        + "\n\n".join(
            f"![Figure {i}](figures/{name})\n\n*Figure {i}.*"
            for i, name in enumerate(FIGURES, 1)
        )
        + "\n"
    )
    (out / "submission.md").write_text(submission)
    specification = table(
        ["Specification", "Definition"],
        [
            ["Unit", "Player-destination-season forecast"],
            ["Population", "Frozen 674-forecast v9 appearance-qualified target"],
            [
                "Estimator",
                "Six fixed slope regression arms across 56 frozen upstream scenarios",
            ],
            ["Null", "Translation has no robust incremental predictive benefit"],
            ["Filter", "Frozen v9 eligibility; unknowns and refusals retained"],
            ["Key", "Exact frozen player, destination and season keys"],
            [
                "Uncertainty",
                "Conditional player/club-season and player/season intervals; fixed omission and seed sensitivity",
            ],
            [
                "Threats",
                "Reused outcomes, selected appearances, upstream-factor uncertainty, unresolved release rights",
            ],
        ],
    )
    results = "# V10 registered comparison results\n\n" + specification
    for heading, key in (
        ("Existing benchmark", "BENCHMARK_RESULTS"),
        ("Registered cell-slope comparison", "SLOPE_RESULTS"),
        ("Support and unknowns", "SUPPORT_RESULTS"),
        ("Inherited reliability policy", "POLICY_RESULTS"),
        ("Frozen upstream scenario sensitivity", "REFIT_RESULTS"),
        ("Interpretation", "CONCLUSION"),
    ):
        results += f"\n\n## {heading}\n\n" + parts[key]
    (out / "results.md").write_text(results + "\n")
    figure_dir = out / "figures"
    figure_dir.mkdir()
    figures(new, prior, prep, figure_dir)
    # Source paths identify the numerical evidence behind every main result block.
    claims = {
        "abstract_history": "v9:variants.official_corrected.scenarios.reference.contrasts.original_vs_history_only",
        "abstract_destination": "v9:variants.official_corrected.scenarios.reference.contrasts.destination_increment",
        "slope_table": "v10:variants.<pool>.scenarios.reference.metrics / contrasts.cell_slope_<penalty>_increment",
        "support_table": "v9:preparation.counts / variants.<pool>.scenarios.reference.fallbacks; v10:target_n",
        "rejection_counts": "v9:preparation.rejection_counts",
        "refit_table": "v10:variants.<pool>.scenarios.omit_* / seed_*.contrasts.cell_slope_<penalty>_increment",
        "policy_primary": "support-policy:primary-readback.json primary.<source_ridge_10|cell_slope_10>.metrics / contrasts.parent",
        "cluster_counts": "v10:variants.official_corrected.scenarios.reference.contrasts.cell_slope_1_increment.<clustering>.components / degrees_of_freedom",
        "cohort_composition": "v9:variants.official_corrected.by_destination.destination.<competition>.n",
        "worked_example": "v9:examples[selection=median_change].values; unchanged selection",
        "support_restriction": "support-loss:readback.json references / controls; 400 registered restrictions",
        "absolute_benchmarks": "v9:variants.official_corrected.scenarios.reference.metrics.<arm>.mae",
        "nonfallback_counts": "v10:target_n minus v9:variants.<pool>.scenarios.reference.fallbacks",
        "abstract_relative_gains": "v9:official_corrected reference contrasts.<original_vs_history_only|destination_increment>.player_club_season.difference divided by metrics.<history_only|history_destination_slope>.mae",
        "abstract_full_pool_source_aware": "v9:official_corrected reference contrasts.source_ridge_<penalty>_increment and v10:official_corrected reference contrasts.cell_slope_<penalty>_increment; min/max difference, both clusterings include zero",
        "abstract_verified_pools": "v9:<verified pools> reference contrasts.source_ridge_<penalty>_increment and v10:<verified pools> reference contrasts.cell_slope_<penalty>_increment; 18 differences, counts of ci95 upper bounds below zero per clustering",
        "abstract_support_pool_b": "v9:preparation.counts.<official_corrected|verified_same_club_full> and target_n minus variants.<pool>.scenarios.reference.fallbacks; equals support-loss:readback.json references.verified.support.nonfallback",
        "abstract_restriction_medians": "support-loss:readback.json controls.<season_count|cell_season_count>.support.nonfallback.median and repetitions",
        "abstract_seasons": "v9:variants.official_corrected.by_season.destination keys (stored destination-season labels)",
        "abstract_verified_history": "v9:variants.<verified pools>.scenarios.reference.contrasts.original_vs_history_only.player_club_season.difference; min/max, all positive",
        "abstract_verified_destination": "v9:variants.<verified pools>.scenarios.reference.contrasts.destination_increment.player_club_season; all differences negative and intervals include zero; joined with abstract_verified_pools for the competition-aware range",
        "abstract_overlap_trimmed_support": "v10:target_n minus v9:variants.<overlap_keys_full|same_club>.scenarios.reference.fallbacks; must be equal",
        "abstract_restriction_cap": "support-loss:readback.json controls.cell_season_count.support.nonfallback.maximum <= references.verified.support.nonfallback",
        "abstract_euroleague_exception": "support-loss:readback.json references.verified.by_destination.euroleague.nonfallback above controls.season_count.by_destination.euroleague.nonfallback.maximum and within controls.cell_season_count range",
        "offset_pool_table": "v9:variants.<pool>.scenarios.reference.contrasts.source_ridge_<penalty>_increment.<clustering>; parent MAE share uses metrics.source_ridge_<penalty> and v10 metrics.cell_slope_<penalty>",
        "all_numbers": "Numbers are saved-artifact lookups, displayed differences, complementary support counts or min/max over the complete registered scenario family; rounding is for display.",
    }
    (out / "claim-map.json").write_text(
        json.dumps(claims, indent=2, sort_keys=True) + "\n"
    )
    manifest = {
        "status": "complete",
        "candidate_version": "v10",
        "abstract_words": words,
        "generator_sha256": sha256_file(Path(__file__)),
        "template_sha256": sha256_file(TEMPLATE),
        "methods_template_sha256": sha256_file(METHODS_TEMPLATE),
        "policy_readback_sha256": sha256_file(POLICY_READBACK),
        "protocol_sha256": sha256_file(PROTOCOL),
        "v10_summary_sha256": sha256_file(Path(analysis) / "summary.json"),
        "v9_diagnostics_sha256": sha256_file(V9 / "diagnostics.json"),
        "v9_preparation_sha256": sha256_file(V9 / "preparation.json"),
        "robust_incremental_superiority": robust(new),
        "presentation_date": PRESENTATION_DATE,
        "support_restriction_readback_sha256": sha256_file(
            ROOT / "docs/research/artifacts/sloan-support-loss-2026-09-28/readback.json"
        )
        if (
            ROOT / "docs/research/artifacts/sloan-support-loss-2026-09-28/readback.json"
        ).exists()
        else None,
        "public_release_authorized": False,
        "outputs": {
            p.relative_to(out).as_posix(): sha256_file(p)
            for p in out.rglob("*")
            if p.is_file()
        },
    }
    (out / "render_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    )
    if update:
        plans = ROOT / "docs/plans"
        for source, name in (
            ("abstract.md", "sloan-ssac27-abstract-v10.md"),
            ("manuscript.md", "sloan-ssac27-manuscript-v10.md"),
            ("supplement.md", "sloan-ssac27-v10-supplement.md"),
            ("submission.md", "sloan-ssac27-abstract-v10-submission.md"),
        ):
            shutil.copyfile(out / source, plans / name)
        for name in FIGURES:
            shutil.copyfile(figure_dir / name, plans / "figures" / name)
    return manifest


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--analysis", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--update-candidate", action="store_true")
    a = p.parse_args()
    result = render(a.analysis, a.out, a.update_candidate)
    print(
        json.dumps(
            {"status": result["status"], "abstract_words": result["abstract_words"]}
        )
    )


if __name__ == "__main__":
    main()
