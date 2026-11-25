#!/usr/bin/env python3
"""Analysis E34 (EXPLORATORY): two published league scales on the 180 older arrivals.

Pre-registration Amendment 23, rule 5
(docs/research/sloan-full-paper-preregistration-amendment-23-2026-11-22.md,
commit bf60fe302, pushed alone on 2026-11-22, before this file existed).

E28b compared the league-aware forecast with the destination-only forecast on
the 180 older arrivals (131 from the Adriatic league, 49 from Israel;
destination seasons 2008-09 to 2015-16). E34 repeats that comparison with a
published league scale in the place of the paper's league numbers, once for a
league table printed in 2015 and once for a league scale published in 2026,
by the one rule of Amendment 15 for a published-table forecast: the
destination-aware forecast plus one unpenalised coefficient times the scale's
value for the source league.

* The 2015 table: the frozen coefficients of E31c. Nothing is fitted.
* The 2026 scale: fitted on the registered training arrivals through 2025, by
  the code that fitted E31c (``sloan_fullpaper_published_tables.fit``).

For each scale S, unweighted and weighted by destination minutes, with the
intervals of E28 (two-way clustered, player and destination club-season) and
the difference detectable with 80% power:

    G_S = MAE(published-scale forecast) - MAE(source_ridge_10)
    T_S = MAE(history_destination_slope) - MAE(published-scale forecast)

Below zero, G_S says that the published scale was the more accurate, and T_S
that the destination-only forecast was. The same is printed by source league.

These readings were first made outside the registration (a review of the paper,
21 November 2026), and the rules for printing them were written after their
values had been seen. They are exploratory. E34 reads no 2026-27 statistic.

Gates, in the amendment's order. Before any contrast of E34 is computed:
G34a (every pinned file by its sha256; the ten committed values of the 2026
scale equal the ten the amendment prints; controls: a changed byte, one value
moved by 0.1), G34b (the 180 rows of E28b; the two committed E28b contrasts
against the destination-only forecast reproduced with their intervals to 1e-9;
control: one row removed) and G34c (the 2015-table forecasts are built from the
frozen E31c coefficients; the code that fits the 2026 scale, run on the 2015
table, returns those coefficients to 1e-9; control: one published value moved
by 0.01). On the computed contrasts, before anything is written: G34e (for
each scale and weighting G_S + T_S equals the committed E28b contrast to 1e-9;
control: the sign of one contrast reversed) and G34f (every G_S estimate and
interval end the amendment lists as seen, with the split by source league, to
the three printed decimals; control: the forecasts of one scale shifted by
0.1). If a gate fails the run stops and writes nothing for the paper.

Stop rule: E34 is run once, in one retained run. No further published scale,
sample or variant of this comparison is run for this paper.
"""

# ruff: noqa: E501, E741 -- gate messages; O is the offsets arm
from __future__ import annotations

if __name__ == "__main__":
    import sys as _sys
    from pathlib import Path as _Path

    _sys.path.insert(0, str(_Path(__file__).resolve().parents[1]))
    from src.research.execution import enter as _enter

    _enter(__file__)

import argparse
import copy
import json
import math
from pathlib import Path
import re
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from scripts import sloan_fullpaper_amend9 as e28  # noqa: E402
from scripts import sloan_fullpaper_common as common  # noqa: E402
from scripts import sloan_fullpaper_published_tables as published  # noqa: E402
from scripts.sloan_fullpaper_common import GateFailure, check_sha  # noqa: E402
from scripts.translation_research_common import sha256_file  # noqa: E402

AMENDMENT = Path(
    "docs/research/sloan-full-paper-preregistration-amendment-23-2026-11-22.md"
)
AMENDMENT_COMMIT = "bf60fe3025a465bffdaf4f804047ac1c72f58879"
AMENDMENT_SHA256 = "8a440ef497d44aeb094f5c439f104ff753084a47576b1428bc881960bd4c1ad7"
_ART = Path("docs/research/artifacts")
#: The four files the amendment pins ("Pinned inputs (E34)").
PINS = {
    "e27_arrivals": (
        _ART / "sloan-fullpaper-older-seasons-2026-11/e27_arrivals.csv",
        "7356ba0bd35945ea8fb8a152d2d167c5dc1eb4d0f7849a08f627cf172ae3a800",
    ),
    "e27_arrivals_printed": (
        _ART / "sloan-fullpaper-older-seasons-paper-2026-11/e27_arrivals_printed.csv",
        "2b4bba1be27d5c66f4e632c39cc01d05dfeb6af8aedcf38473751948648f0936",
    ),
    "e31c_freeze": (
        _ART / "sloan-fullpaper-p1-freeze-2026-11/e31c_freeze.json",
        "a19589ecdf1ba1818d135b8eb87133992003ad7e31dd0cba1668937966750a82",
    ),
    "table_2015": (
        _ART
        / "sloan-fullpaper-published-tables-2026-11/vashro_2015_competition_scores.csv",
        "2c004c88d10c60f68dabb038330a9f8d282ba87f56b521cb6a87c59a26252d04",
    ),
}
#: Committed results this run is checked against or reads; each by its sha256.
COMMITTED = {
    "amend9": (
        _ART / "sloan-fullpaper-amend9-2026-11/summary.json",
        "da97930085208070b8ce8e24ba4a813d8c5225690992bd240f8189d5751a0b22",
    ),
    "equivalents": (
        _ART / "sloan-fullpaper-amend1-decisions-2026-11/exchange_rate_acb16.csv",
        "c8341a37947adcad882f90c9747ea6fee274723b367a0948bbfc50462fead2ca",
    ),
}
OUT_DIR = _ART / "sloan-fullpaper-published-scales-older-2026-11"
#: The ten values of the 2026 scale with the page's title, address and the days it was read.
SCALE_2026 = OUT_DIR / "gaussianhoops_2026_league_strength.json"
#: The page's own names of the ten source leagues -> the repository's league keys.
PAGE_NAMES = {
    "Spain ACB": "spain-acb",
    "France Pro A": "france-pro-a",
    "Italy Serie A": "italy-lba",
    "ABA Liga": "aba-league",
    "Israel Winner": "israel-bsl",
    "Greece GBL": "greece-a1",
    "Turkey BSL": "turkey-bsl",
    "Germany BBL": "germany-bbl",
    "VTB United League": "vtb",
    "Lithuania LKL": "lithuania-lkl",
}
SOURCE_LEAGUES = tuple(sorted(PAGE_NAMES.values()))
#: Where the amendment prints the ten values.
PIN_LEAD = "The ten values used, under the page's own names: "

H, D, O = e28.H, e28.D, e28.O
P_2015 = published.P
P_2026 = "published_scale_gaussianhoops_2026"
SCALES = {
    "table_2015": {
        "forecast": P_2015,
        "name": "a league table printed in 2015",
        "seen_label": "2015 table",
    },
    "scale_2026": {
        "forecast": P_2026,
        "name": "a league scale published in 2026",
        "seen_label": "2026 scale",
    },
}
WEIGHTINGS = e28.WEIGHTINGS  # ("unweighted", "minutes_weighted")
SEEN_WEIGHTING = {"none": "unweighted", "playing time": "minutes_weighted"}
OLDER_LEAGUES = {"aba": 131, "israel": 49}  # the version the paper prints
OLDER_SEASONS = (2008, 2015)  # destination seasons 2008-09 to 2015-16
REPRO_TOLERANCE = 1e-9
SEEN_TOLERANCE = 5e-4  # "to the three printed decimals"
#: The split by source league as the amendment lists it ("also seen"): G, and the interval
#: where the amendment gives one. Each number stands in the amendment's text; G34f checks that
#: before it compares.
SEEN_BY_LEAGUE = (
    ("aba", "table_2015", "unweighted", -0.093, (-0.178, -0.007)),
    ("aba", "scale_2026", "unweighted", -0.086, (-0.166, -0.006)),
    ("aba", "table_2015", "minutes_weighted", -0.140, None),
    ("aba", "scale_2026", "minutes_weighted", -0.132, None),
    ("israel", "table_2015", "unweighted", 0.016, (-0.039, 0.070)),
    ("israel", "scale_2026", "unweighted", 0.003, (-0.052, 0.057)),
    ("israel", "table_2015", "minutes_weighted", 0.060, (0.002, 0.119)),
    ("israel", "scale_2026", "minutes_weighted", -0.035, (-0.094, 0.025)),
)
LABEL = (
    "These readings were first made outside the registration, in a review of the paper, and the "
    "rules for printing them were written after their values had been seen; they are exploratory."
)

negative_control = published.negative_control
gate_max = published.gate_max
passed = published.passed


# ------------------------------------------------------------------ inputs --
def minus(text: str) -> float:
    """A number as the amendment prints it (with a true minus sign)."""
    return float(text.replace("−", "-").replace("+", ""))


def pinned_2026(amendment_text: str) -> dict:
    """The ten values the amendment prints, keyed by repository league."""
    if amendment_text.count(PIN_LEAD) != 1:
        raise GateFailure(
            "the amendment does not list the ten values of the 2026 scale once"
        )
    listed = amendment_text.split(PIN_LEAD, 1)[1].split(". These are the values", 1)[0]
    out = {}
    for entry in listed.split(";"):
        entry = re.sub(r"\s*\(the Adriatic league\)", "", entry)
        match = re.fullmatch(r"\s*(.+?)\s+(\d+\.\d)\s*", entry)
        if not match or match.group(1) not in PAGE_NAMES:
            raise GateFailure(f"unreadable pinned entry in the amendment: {entry!r}")
        league = PAGE_NAMES[match.group(1)]
        if league in out:
            raise GateFailure(f"the amendment pins {league} twice")
        out[league] = float(match.group(2))
    if set(out) != set(SOURCE_LEAGUES):
        raise GateFailure("the amendment does not pin all ten source leagues")
    return out


def load_scale_2026(path: Path) -> tuple[dict, dict]:
    """The committed record of the 2026 scale: (values by repository league, the record)."""
    record = json.loads(Path(path).read_text())
    values = record.get("values")
    if not isinstance(values, dict) or set(values) != set(PAGE_NAMES):
        raise GateFailure(
            f"{path}: the ten values are not listed under the page's names"
        )
    scores = {PAGE_NAMES[name]: float(value) for name, value in values.items()}
    if not all(math.isfinite(v) for v in scores.values()):
        raise GateFailure(f"{path}: a value is not a number")
    for field in ("publisher", "title", "address", "read_on", "read_again"):
        if not record.get(field):
            raise GateFailure(f"{path}: the record lacks {field!r}")
    again = record["read_again"]
    for field in ("on", "by", "shows_the_same_ten_values"):
        if again.get(field) in (None, ""):
            raise GateFailure(
                "the page of the 2026 scale was not read again before the run "
                f"(Amendment 23, pinned inputs): {field!r} is empty"
            )
    return scores, record


def scale_differences(scores: dict, pinned: dict, *, shift: float = 0.0) -> dict:
    """|committed - registered| per league; ``shift`` moves one value (the control)."""
    if set(scores) != set(pinned):
        return {"leagues": math.inf}
    first = sorted(scores)[0]
    return {
        f"value:{k}": abs(scores[k] + (shift if k == first else 0.0) - pinned[k])
        for k in sorted(scores)
    }


def changed_byte_control(path: Path, expected: str) -> str:
    """G34a's control: a changed byte must fail the hash check."""
    data = bytearray(Path(path).read_bytes())
    data[len(data) // 2] ^= 0x01
    with tempfile.TemporaryDirectory() as tmp:
        changed = Path(tmp) / Path(path).name
        changed.write_bytes(bytes(data))
        return negative_control(check_sha, changed, expected)


def older_rows(scored: pd.DataFrame, printed: pd.DataFrame) -> pd.DataFrame:
    """The 180 older arrivals of E28b in the version the paper prints, in a fixed order."""
    part = scored.loc[scored.league.isin(list(OLDER_LEAGUES))].copy()
    part = part.sort_values(["league", "player_name", "league_dest"]).reset_index(
        drop=True
    )
    counts = part.league.value_counts().to_dict()
    seasons = (int(part.true_season_dest.min()), int(part.true_season_dest.max()))
    if counts != OLDER_LEAGUES or seasons != OLDER_SEASONS:
        raise GateFailure(
            f"G34b: the selected rows are {counts}, seasons {seasons}; registered: "
            f"{OLDER_LEAGUES}, seasons {OLDER_SEASONS}"
        )
    keys = ["player_name", "league_dest"]
    same = (
        part[keys]
        .astype(str)
        .merge(printed[keys].astype(str), on=keys, how="outer", indicator=True)
    )
    if len(printed) != len(part) or not same._merge.eq("both").all():
        raise GateFailure("G34b: the selected rows are not the rows the paper prints")
    if not (np.isfinite(part[e28.WEIGHT]) & (part[e28.WEIGHT] > 0)).all():
        raise GateFailure("an older arrival has no positive destination minutes")
    return part


def e28b_differences(part: pd.DataFrame, committed: dict) -> dict:
    """|recomputed - committed| for the two E28b contrasts against the destination-only
    forecast (unweighted and weighted), estimate and interval ends."""
    out = {}
    for weighting in WEIGHTINGS:
        ours = e28.gain(part, D, O, weighted=weighting != "unweighted")
        theirs = committed[weighting]
        if ours["n"] != theirs["n"] or ours["ci95"] is None:
            return {f"{weighting}:rows": math.inf}
        out[f"{weighting}:difference"] = abs(ours["difference"] - theirs["difference"])
        for i, end in enumerate(("low", "high")):
            out[f"{weighting}:{end}"] = abs(ours["ci95"][i] - theirs["ci95"][i])
    return out


# -------------------------------------------------------------- forecasts --
def frozen_coefficients(freeze: dict, design_names: list) -> np.ndarray:
    """The seven frozen coefficients of the 2015-table forecast (E31c), in the order of the
    registered design (``design_names``: its columns, the published score last)."""
    fit = freeze["fit"]
    if (
        fit.get("features") != list(design_names)
        or fit.get("status") != "ok"
        or len(fit.get("coefficients", [])) != len(design_names)
    ):
        raise GateFailure("the E31c freeze record does not hold the registered design")
    return np.array(fit["coefficients"], dtype=float)


def forecast_from(
    rows: pd.DataFrame, scores: dict, coefficients: np.ndarray
) -> np.ndarray:
    """The published-scale forecast: the registered design times fixed coefficients."""
    x, names = published.design(rows, scores)
    if len(names) != len(coefficients):
        raise GateFailure("the coefficients do not match the registered design")
    prediction = x @ coefficients
    if not np.isfinite(prediction).all():
        raise GateFailure("a published-scale forecast is not finite")
    return prediction


def refit_differences(
    train: pd.DataFrame, scores_2015: dict, frozen: np.ndarray, *, shift: float = 0.0
) -> dict:
    """G34c: the fitting code on the 2015 table against the frozen E31c coefficients;
    ``shift`` moves one published value (the control)."""
    scores = dict(scores_2015)
    first = sorted(k for k in scores if k in SOURCE_LEAGUES)[0]
    scores[first] += shift
    _, info = published.fit(train, train.head(1), scores)
    if info["status"] != "ok":
        return {"fit": math.inf}
    return {
        f"coefficient:{name}": abs(a - b)
        for name, a, b in zip(info["features"], info["coefficients"], frozen)
    }


# ------------------------------------------------------------ the contrasts --
def readings(rows: pd.DataFrame, forecast: str) -> dict:
    """G_S and T_S for one scale, each unweighted and weighted, in the Specification's signs."""
    return {
        "G": {
            w: e28.gain(rows, forecast, O, weighted=w != "unweighted")
            for w in WEIGHTINGS
        },
        "T": {
            w: e28.gain(rows, D, forecast, weighted=w != "unweighted")
            for w in WEIGHTINGS
        },
    }


def all_readings(part: pd.DataFrame) -> tuple[dict, dict]:
    """Both scales on all 180 arrivals, and the same by source league."""
    blocks = {scale: readings(part, spec["forecast"]) for scale, spec in SCALES.items()}
    by_league = {
        league: {
            scale: readings(part.loc[part.league.eq(league)], spec["forecast"])
            for scale, spec in SCALES.items()
        }
        for league in OLDER_LEAGUES
    }
    return blocks, by_league


def identity_differences(
    blocks: dict, committed: dict, *, reverse: bool = False
) -> dict:
    """G34e: G_S + T_S against the committed E28b contrast; ``reverse`` flips one sign (the control)."""
    out = {}
    for i, (scale, block) in enumerate(sorted(blocks.items())):
        for w in WEIGHTINGS:
            g = block["G"][w]["difference"]
            if reverse and i == 0 and w == WEIGHTINGS[0]:
                g = -g
            out[f"{scale}:{w}"] = abs(
                g + block["T"][w]["difference"] - committed[w]["difference"]
            )
    return out


def seen_values(amendment_text: str) -> list:
    """The table "The values of E34 as seen": (scale, weighting, G, low, high)."""
    section = amendment_text.split("## The values of E34 as seen", 1)[1].split(
        "\n## ", 1
    )[0]
    labels = {v["seen_label"]: k for k, v in SCALES.items()}
    out = []
    for line in section.splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) != 5 or cells[0] not in labels:
            continue
        low, high = cells[3].split(" to ")
        out.append(
            (
                labels[cells[0]],
                SEEN_WEIGHTING[cells[1]],
                minus(cells[2]),
                minus(low),
                minus(high),
            )
        )
    if len(out) != 4:
        raise GateFailure("the amendment does not list four values of E34 as seen")
    for league, _, _, g, ci in SEEN_BY_LEAGUE:
        for value in (g, *(ci or ())):
            printed = f"{abs(value):.3f}"
            if printed not in section:
                raise GateFailure(
                    f"G34f: {printed} ({league}) is not in the amendment's list of values seen"
                )
    return out


def seen_differences(blocks: dict, by_league: dict, seen: list) -> dict:
    """G34f: every G_S the amendment lists as seen, overall and by source league."""

    def g(block, scale, w):
        r = block[scale]["G"][w]
        return r["difference"], r["ci95"]

    out = {}
    for scale, w, value, low, high in seen:
        estimate, ci = g(blocks, scale, w)
        out[f"all:{scale}:{w}:G"] = abs(estimate - value)
        out[f"all:{scale}:{w}:low"] = abs(ci[0] - low)
        out[f"all:{scale}:{w}:high"] = abs(ci[1] - high)
    for league, scale, w, value, interval in SEEN_BY_LEAGUE:
        estimate, ci = g(by_league[league], scale, w)
        out[f"{league}:{scale}:{w}:G"] = abs(estimate - value)
        if interval is None:
            # the amendment says only "both intervals below zero"
            out[f"{league}:{scale}:{w}:below_zero"] = 0.0 if ci[1] < 0 else math.inf
        else:
            out[f"{league}:{scale}:{w}:low"] = abs(ci[0] - interval[0])
            out[f"{league}:{scale}:{w}:high"] = abs(ci[1] - interval[1])
    return out


def league_ranks(
    scores_2015: dict, scores_2026: dict, equivalents: pd.DataFrame
) -> dict:
    """Where each scale places the Adriatic league among the ten source leagues, strongest
    first. A published scale: the higher value is the stronger league. The paper's league
    numbers: the lower Equivalent (the domestic rate that forecasts like a 16 in Spain) is the
    league whose rate is worth more."""

    def rank(values: dict, *, high_first: bool) -> dict:
        order = sorted(
            values, key=lambda k: (-values[k] if high_first else values[k], k)
        )
        return {league: i + 1 for i, league in enumerate(order)}

    out = {
        "table_2015": rank(
            {k: scores_2015[k] for k in SOURCE_LEAGUES}, high_first=True
        ),
        "scale_2026": rank(
            {k: scores_2026[k] for k in SOURCE_LEAGUES}, high_first=True
        ),
    }
    paper = {}
    for destination, block in equivalents.groupby("destination"):
        values = dict(
            zip(block.source_league, block.acb16_equivalent_eff36.astype(float))
        )
        if set(values) != set(SOURCE_LEAGUES):
            raise GateFailure(
                "the committed Equivalents do not cover the ten source leagues"
            )
        paper[str(destination)] = rank(values, high_first=False)
    out["paper_league_numbers"] = paper
    out["adriatic"] = {
        "table_2015": out["table_2015"]["aba-league"],
        "scale_2026": out["scale_2026"]["aba-league"],
        "paper_league_numbers": sorted({r["aba-league"] for r in paper.values()}),
        "of": len(SOURCE_LEAGUES),
    }
    return out


def flat(scope: str, blocks: dict) -> list:
    """One row per reading, for the appendix table."""
    rows = []
    for scale, block in blocks.items():
        for contrast in ("G", "T"):
            for w in WEIGHTINGS:
                r = block[contrast][w]
                rows.append(
                    {
                        "sample": scope,
                        "scale": scale,
                        "contrast": f"{contrast}_S",
                        "weighting": w,
                        "n": r["n"],
                        "left": r["left"],
                        "right": r["right"],
                        "mae_left": r["mae_left"],
                        "mae_right": r["mae_right"],
                        "difference": r["difference"],
                        "ci95_low": r["ci95"][0] if r["ci95"] else None,
                        "ci95_high": r["ci95"][1] if r["ci95"] else None,
                        "detectable_80": r["detectable_80"],
                        "df": r["df"],
                        "reading": r["reading"],
                    }
                )
    return rows


# --------------------------------------------------------------------- run --
def run(root: Path, input_dir: Path, out: Path) -> dict:
    root = Path(root)
    gates = {}

    # ---- G34a: pinned inputs, before anything is read from them
    check_sha(root / AMENDMENT, AMENDMENT_SHA256)
    for name, (relative, expected) in {**PINS, **COMMITTED}.items():
        check_sha(root / relative, expected)
    amendment_text = (root / AMENDMENT).read_text()
    scores_2026, scale_record = load_scale_2026(root / SCALE_2026)
    pinned = pinned_2026(amendment_text)
    worst = scale_differences(scores_2026, pinned)
    gates["G34a"] = passed(
        gate_max("G34a (the ten values of the 2026 scale)", worst, 1e-12),
        negative_control(
            gate_max, "G34a", scale_differences(scores_2026, pinned, shift=0.1), 1e-12
        ),
        tolerance=1e-12,
        pinned_files={name: expected for name, (_, expected) in PINS.items()},
        changed_byte=changed_byte_control(
            root / PINS["e27_arrivals"][0], PINS["e27_arrivals"][1]
        ),
        control_input="one of the ten values moved by 0.1; one byte of a pinned file changed",
    )

    # ---- G34b: the same rows, and E28b reproduced before any published scale is used
    scored = pd.read_csv(root / PINS["e27_arrivals"][0], dtype={"player_name": str})
    printed = pd.read_csv(
        root / PINS["e27_arrivals_printed"][0], dtype={"player_name": str}
    )
    part = older_rows(scored, printed)
    committed = json.loads((root / COMMITTED["amend9"][0]).read_text())["e28b"]
    if committed["n"] != len(part) or sorted(committed["leagues"]) != sorted(
        OLDER_LEAGUES
    ):
        raise GateFailure("G34b: the committed E28b block is not on these 180 arrivals")
    e28b = committed["contrasts"]["G_D"]
    gates["G34b"] = passed(
        gate_max("G34b", e28b_differences(part, e28b), REPRO_TOLERANCE),
        negative_control(
            gate_max, "G34b", e28b_differences(part.iloc[1:], e28b), REPRO_TOLERANCE
        ),
        tolerance=REPRO_TOLERANCE,
        rows=int(len(part)),
        by_league=part.league.value_counts().to_dict(),
        destination_seasons=list(OLDER_SEASONS),
        control_input="one row removed",
    )

    # ---- G34c: the published-scale forecasts
    table = published.load_table(root / PINS["table_2015"][0])
    scores_2015 = published.table_scores(table)
    freeze = json.loads((root / PINS["e31c_freeze"][0]).read_text())
    frozen = frozen_coefficients(freeze, published.design(part.head(1), scores_2015)[1])
    for name in (
        "pairs",
        "cohort",
    ):  # the registered training arrivals, by the freeze record
        check_sha(
            Path(input_dir) / "official_corrected" / f"{name}.parquet",
            freeze[f"{name}_sha256"],
        )
    pairs, cohort = common.load_pool(input_dir, "official_corrected")
    features, _ = common.build_features(pairs, cohort)
    train = published.frozen_training(features)
    if len(train) != freeze["training_rows"]:
        raise GateFailure(
            f"{len(train)} training arrivals, the E31c freeze record has {freeze['training_rows']}"
        )
    gates["G34c"] = passed(
        gate_max(
            "G34c", refit_differences(train, scores_2015, frozen), REPRO_TOLERANCE
        ),
        negative_control(
            gate_max,
            "G34c",
            refit_differences(train, scores_2015, frozen, shift=0.01),
            REPRO_TOLERANCE,
        ),
        tolerance=REPRO_TOLERANCE,
        training_rows=int(len(train)),
        control_input="one published value of the 2015 table moved by 0.01",
    )
    part[P_2015] = forecast_from(part, scores_2015, frozen)
    _, fit_2026 = published.fit(train, train.head(1), scores_2026)
    if fit_2026["status"] != "ok":
        raise GateFailure(
            f"the 2026-scale forecast could not be fitted: {fit_2026['status']}"
        )
    part[P_2026] = forecast_from(part, scores_2026, np.array(fit_2026["coefficients"]))

    # ---- only now the contrasts of E34
    blocks, by_league = all_readings(part)
    gates["G34e"] = passed(
        gate_max("G34e", identity_differences(blocks, e28b), REPRO_TOLERANCE),
        negative_control(
            gate_max,
            "G34e",
            identity_differences(blocks, e28b, reverse=True),
            REPRO_TOLERANCE,
        ),
        tolerance=REPRO_TOLERANCE,
        control_input="the sign of one contrast reversed",
    )
    seen = seen_values(amendment_text)
    shifted = all_readings(part.assign(**{P_2015: part[P_2015] + 0.1}))
    gates["G34f"] = passed(
        gate_max("G34f", seen_differences(blocks, by_league, seen), SEEN_TOLERANCE),
        negative_control(
            gate_max, "G34f", seen_differences(*shifted, seen), SEEN_TOLERANCE
        ),
        tolerance=SEEN_TOLERANCE,
        checked=len(seen_differences(blocks, by_league, seen)),
        control_input="the forecasts of one scale shifted by 0.1",
    )

    equivalents = pd.read_csv(root / COMMITTED["equivalents"][0])
    arms = (D, O, P_2015, P_2026)
    summary = {
        "analysis": "E34",
        "exploratory": True,
        "label": LABEL,
        "amendment": {
            "path": AMENDMENT.as_posix(),
            "commit": AMENDMENT_COMMIT,
            "sha256": AMENDMENT_SHA256,
        },
        "reads_2026_27_statistics": False,
        "stop_rule": "run once, in one retained run; no further published scale, sample or variant",
        "n": int(len(part)),
        "by_league_n": part.league.value_counts().to_dict(),
        "destination_seasons": list(OLDER_SEASONS),
        "clusters": {
            "players": int(part.player_name.nunique()),
            "destination_club_seasons": int(part.cluster.nunique()),
        },
        "total_minutes": float(part[e28.WEIGHT].sum()),
        "forecasts": {
            "destination_only": D,
            "league_aware": O,
            "table_2015": P_2015,
            "scale_2026": P_2026,
        },
        "mae": {
            arm: {
                "unweighted": float(np.abs(part[arm] - part[e28.OUTCOME]).mean()),
                "minutes_weighted": float(
                    np.average(
                        np.abs(part[arm] - part[e28.OUTCOME]), weights=part[e28.WEIGHT]
                    )
                ),
            }
            for arm in arms
        },
        "scales": {
            "table_2015": {
                "name": SCALES["table_2015"]["name"],
                "values": {k: scores_2015[k] for k in SOURCE_LEAGUES},
                "coefficients": dict(zip(freeze["fit"]["features"], frozen.tolist())),
                "fitted_here": False,
                "source": "the frozen coefficients of E31c",
            },
            "scale_2026": {
                "name": SCALES["scale_2026"]["name"],
                "values": {k: scores_2026[k] for k in SOURCE_LEAGUES},
                "coefficients": dict(
                    zip(fit_2026["features"], fit_2026["coefficients"])
                ),
                "fitted_here": True,
                "train_n": fit_2026["train_n"],
                "source": "fitted on the registered training arrivals through 2025, by the code of E31c",
                "page": {
                    k: scale_record[k]
                    for k in ("publisher", "title", "address", "read_on", "read_again")
                },
            },
        },
        "contrasts": blocks,
        "by_league": by_league,
        "e28b": copy.deepcopy(e28b),
        "ranks": league_ranks(scores_2015, scores_2026, equivalents),
        "gates": gates,
        "inputs": {
            **{
                name: {"path": rel.as_posix(), "sha256": sha}
                for name, (rel, sha) in PINS.items()
            },
            **{
                name: {"path": rel.as_posix(), "sha256": sha}
                for name, (rel, sha) in COMMITTED.items()
            },
            "scale_2026": {
                "path": SCALE_2026.as_posix(),
                "sha256": sha256_file(root / SCALE_2026),
            },
            "pairs_sha256": freeze["pairs_sha256"],
            "cohort_sha256": freeze["cohort_sha256"],
        },
    }
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    table_rows = flat("all", blocks)
    for league in OLDER_LEAGUES:
        table_rows += flat(league, by_league[league])
    pd.DataFrame(table_rows).to_csv(out / "e34_readings.csv", index=False)
    (out / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True, allow_nan=False) + "\n"
    )
    return summary


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    summary = run(Path.cwd(), args.input_dir, args.out)
    for name, gate in summary["gates"].items():
        print(
            f"{name}: {gate['status']} (max difference {gate['max_difference']:.3g}; control {gate['negative_control']})"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
