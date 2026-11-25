#!/usr/bin/env python3
"""Score the frozen 2026-27 test (P1) of the SSAC27 full paper, once.

Registrations (law for this file; nothing in them is relaxed here):

* docs/research/sloan-full-paper-preregistration-2026-11-03.md, section "P1"
  (population, three primary contrasts, the 60-newcomer minimum, the licence);
* Amendment 8 (16 Nov 2026): read-outs S1 to S5, the failure rule (rule 1),
  the wording rule (rule 2), the join rule and "inconclusive" (rule 3), what is
  printed below 60 newcomers (rule 4), the band half-widths and the gap guide
  (descriptive in November);
* Amendment 15 (17 Nov 2026), E31c: the published-table arm read out beside S1
  and S2, and the columns E32 needs in the scored rows;
* Amendment 18 (18 Nov 2026): the readings of the rules above where their text
  left a choice open (a postponed game, which state wins, two details of the
  join rule, two formulas, the refresh, the registration list, the band pin).
  The run checks that file's sha256 before anything else (gate G18c).

This entry point exists because ``scripts/sloan_fullpaper_prospective.py`` (the
freeze) is registered with a source-season envelope that ends at 2025: the
research harness would not stage a 2026-27 file for it. The scoring entry has
its own envelope (2026 only), so the freeze can still be re-run from its
receipt and can still never read 2026-27.

Order of a scoring run (asserted by tests):

1. Amendment 18 is checked by its sha256, then the pinned inputs are checked
   against hashes that are themselves committed;
2. the data gates run on the outcome files (season, freshness by content,
   schedule dates, schedule-to-box-score completeness, no missing round);
3. the newcomer ledger is built: every player who reaches eight games gets one
   row and one reason; nothing is dropped by a join;
4. the pre-read block (sample size, detectable effects, expected noise) is
   computed from rows that carry NO outcome column, printed and written;
5. only then is the first contrast computed.

Threats: a hash typed by hand (hashes come from the committed freeze record and
from constants printed in the registrations); a silent inner join (the ledger
and the unjoined list); a freshness gate that cannot fail (content timestamp,
with a run-time negative control); a missing round (completeness and round
gates); a null read as a contradiction (pre-read block before any contrast;
rule 1); rows that cannot be scored counted as scored (reason column; status
"inconclusive"); a rehearsal mistaken for the result (every rehearsal output
carries ``synthetic: true`` and the renderer refuses it).

``rehearse`` builds made-up 2026-27 outcome files from the frozen forecasts and
a seeded random generator and drives ``score`` through every state. It reads no
2026-27 statistic.
"""

# ruff: noqa: E501 -- gate messages and pre-registered wording
from __future__ import annotations

if __name__ == "__main__":
    import sys as _sys
    from pathlib import Path as _Path

    _sys.path.insert(0, str(_Path(__file__).resolve().parents[1]))
    from src.research.execution import enter as _enter

    _enter(__file__)

import argparse
import datetime as dt
import json
import math
import os
from pathlib import Path
import re
import sys
import unicodedata

for _name in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_name, "1")
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from scripts import calibrate_prediction_intervals as intervals  # noqa: E402
from scripts import sloan_fullpaper_amend1_decisions as a1  # noqa: E402
from scripts import sloan_fullpaper_amend3 as a3  # noqa: E402
from scripts import sloan_fullpaper_amend9 as a9  # noqa: E402
from scripts import sloan_fullpaper_common as common  # noqa: E402
from scripts import sloan_fullpaper_decisions as dec  # noqa: E402
from scripts import sloan_fullpaper_prospective as p1  # noqa: E402
from scripts import sloan_fullpaper_registration_list as registration  # noqa: E402
from scripts import validate_translation_holdout as holdout  # noqa: E402
from scripts.translation_research_common import sha256_file  # noqa: E402
from src.data.corpus import euroleague_api as api  # noqa: E402

KEY = common.KEY
OUTCOME = dec.OUTCOME
SEASON = p1.FREEZE_SEASON
DESTINATIONS = p1.DESTINATIONS
COMPETITION_CODE = {"euroleague": "E", "eurocup": "U"}
CUTOFF = p1.SCORING_GAME_CUTOFF
REFRESH_FROM = p1.SCORING_REFRESH_FROM
MIN_SCORED = p1.MIN_SCORED
PRIMARY = p1.PRIMARY_CONTRASTS
H, HT, O, OT = dec.HISTORY, dec.HISTORY_T, dec.OFFSETS, dec.OFFSETS_T  # noqa: E741
D = "history_destination_slope"
#: Amendment 8: S1 and S2. MAE(left) - MAE(right); positive favours the right-hand forecast.
SECONDARY = {"S1": (H, O), "S2": (D, O)}
#: Rule 4: "the mean absolute error of the four primary forecasts".
PRIMARY_ARMS = (H, HT, O, OT)
#: S3 is printed for the league-aware forecast and, beside it, for these two.
LEVEL_ARMS = (O, H, HT)
N_SECONDARY = 5
N_BOOT = dec.N_BOOT
BOOT_SEED = dec.SEED
POWER_Z = dec.POWER_Z
#: Rule 3: "more than 5% of the joined newcomers".
LOST_SHARE_MAX = 0.05
#: Rule 3 (b): "a full normalised name within two character edits of his".
MAX_EDITS = 2
STATUSES = ("scored", "not_adjudicable", "inconclusive")
#: Why a player who reached eight games is or is not scored (the ledger).
REASONS = (
    "scored",
    "incumbent",
    "unjoined",
    "source_rate_not_positive",
    "outcome_rate_not_positive",
    "forecast_missing",
)

# ---- the readings (Amendment 18, gate G18c) ----------------------------------
AMENDMENT_18 = Path(
    "docs/research/sloan-full-paper-preregistration-amendment-18-2026-11-18.md"
)
#: sha256 of Amendment 18 as accepted and pushed alone on 18 November 2026.
AMENDMENT_18_SHA = "d86fc9b79924c92629a95afc9852fc67339b23d3b2a85ece7d71abf943cd472e"

# ---- pinned, committed inputs ------------------------------------------------
FREEZE_DIR = Path("docs/research/artifacts/sloan-fullpaper-p1-freeze-2026-11")
FREEZE_RECORD = FREEZE_DIR / "freeze.json"
#: sha256 of the committed freeze record (also in provenance.json of the freeze).
FREEZE_RECORD_SHA = "07ca3c33278238d3d5d0a1626a8afaf8f2af186e7e74e5656b1476b47d35d67a"
#: The frozen file's sha256 as printed in Amendments 1, 7 and 8.
REGISTERED_FROZEN_SHA = (
    "f3530c1a5ac369c032a996756ced226a93aa2d9f71d2e63aab21694de3d55316"
)
#: Amendment 15, E31c: the published-table forecast frozen for the same 3,478
#: rows (commit 10ad0807), and the record written beside it by its freeze run.
PUBLISHED_ARM_FILE = FREEZE_DIR / "p1_frozen_published_table_forecasts.parquet"
PUBLISHED_ARM_RECORD = FREEZE_DIR / "e31c_freeze.json"
#: sha256 of that committed record; the record holds the forecast file's sha256.
PUBLISHED_ARM_RECORD_SHA = (
    "a19589ecdf1ba1818d135b8eb87133992003ad7e31dd0cba1668937966750a82"
)
#: The forecast column, which the record names as its ``arm``. Another table
#: needs a dated addendum to Amendment 15 before its arm is frozen.
PUBLISHED_ARM = "published_table_vashro_2015"
FROZEN_KEY = ["player_name", "league_dest"]
SCORER_DIR = Path("docs/research/artifacts/sloan-fullpaper-p1-scorer-2026-11")
BANDS_FILE = SCORER_DIR / "p1_band_half_widths.json"
#: Amendment 18, rule 8: the sha256 of the committed half-widths file.
BANDS_SHA = "0f384e20e17e2ecc2122f2ff4ddd9107c7cd72f57dd7f1d7e82ca5ed5c247963"
BAND_LEVELS = (0.80, 0.95)
SCORE_DIR = Path("docs/research/artifacts/sloan-fullpaper-p1-score-2026-11")
#: Committed files the pre-read block and the failure rule are computed from.
COMMITTED = {
    "protocol": (
        "docs/research/sloan-full-paper-preregistration-2026-11-03.md",
        "6c6002f9a96f954eeaac4082a02471bcd7017879df07e2a0630de07e345a5194",
    ),
    "recipes": (
        "docs/research/artifacts/sloan-fullpaper-recipes-2026-11/summary.json",
        "e4d826741bd4f629c713216cd592e19ae7d2d2a89b77fad2cbe7ed350c51d030",
    ),
    "e28": (
        "docs/research/artifacts/sloan-fullpaper-amend9-2026-11/summary.json",
        "da97930085208070b8ce8e24ba4a813d8c5225690992bd240f8189d5751a0b22",
    ),
    "e6": (
        "docs/research/artifacts/sloan-fullpaper-robustness-2026-11-03/summary.json",
        "ec2e2c10f44b801a1af099600841a73058872f9430b3aecfaf507a7fc32c91db",
    ),
    "anchor_674": (
        "docs/research/artifacts/sloan-fullpaper-public-tables-2026-11/e7_keyed_forecasts.csv",
        "83589795f00df04cdb272155697f6f9d55c8f7604e49ae3bc45e0e1aac04b8f6",
    ),
}
#: Rows of the registered power table (3 Nov) that belong to P-a, P-b and P-c.
POWER_ROWS = {
    "P-a": "history vs history + translation",
    "P-b": "history + translation vs offsets λ10",
    "P-c": "offsets λ10 vs + translation",
}
#: The 2020-2025 point estimate each primary contrast is read against (rule 1).
ANCHOR_PATHS = {
    "P-a": "results/A/R1/ladder/history_only->scheduled_history/player_club_season/difference",
    "P-b": "e1/head_to_head/lambda_10/player_club_season/difference",
    "P-c": "results/A/R1/ladder/source_ridge_10->source_ridge_10_scheduled/player_club_season/difference",
}
#: S1 and S2 are the E28 differences G_H and G_D on unseen forecasts.
E28_NAMES = {"S1": "G_H", "S2": "G_D"}
#: Amendment 6, rule 4: the generic words dropped before two club names are compared.
GENERIC_WORDS = frozenset(
    "BC BK KK CB SC SK AS FC CLUB BASKET BASKETBALL BASKETBOL BALONCESTO PALLACANESTRO".split()
)
JACCARD_MIN = 0.6
#: Data gates of the outcome files. Only these can be declared "cannot be
#: repaired by refreshing the files" (rule 3, last sentence).
DATA_GATES = (
    "season",
    "freshness",
    "schedule_dates",
    "boxscore_in_schedule",
    "completeness",
    "rounds",
    "people_list",
)
BOX_COLUMNS = (
    "Season",
    "Round",
    "Gamecode",
    "Player",
    "Team",
    "Minutes",
    "Points",
    "TotalRebounds",
    "Assistances",
    "Steals",
    "BlocksFavour",
    "Turnovers",
    "FoulsCommited",
    "FieldGoalsMade2",
    "FieldGoalsAttempted2",
    "FieldGoalsMade3",
    "FieldGoalsAttempted3",
    "FreeThrowsMade",
    "FreeThrowsAttempted",
    "OffensiveRebounds",
    "DefensiveRebounds",
    "Plusminus",
    "_scraped_at",
)
SCHEDULE_COLUMNS = (
    "Phase",
    "Round",
    "date",
    "gameCode",
    "hometeam",
    "awayteam",
    "played",
    "_scraped_at",
)
#: Amendment 18, rule 7: competition, season, name, previous team, club; no statistic.
PEOPLE_COLUMNS = registration.COLUMNS
#: Columns of the scored rows that E32 (Amendment 15) needs, in its order.
E32_COLUMNS = (
    "player_display_name",
    "league_dest",
    "league_src",
    "pir_per36_src",
    D,
    O,
    OUTCOME,
    "games_dest",
    "minutes_dest",
)
DESTINATION_COLUMNS = (
    "player_display_name",
    "club_dest",
    "games_dest",
    "minutes_dest",
    "pir_dest",
    OUTCOME,
    "cluster",
)
#: Columns of the ledger that hold or reveal a 2026-27 outcome. The pre-read
#: block is computed from a frame without them.
OUTCOME_COLUMNS = ("pir_dest", OUTCOME)


class GateFailure(p1.GateFailure):
    """A gate of the scoring run did not hold; nothing is scored."""

    def __init__(self, message: str, gate: str = "pinned_input"):
        super().__init__(message)
        self.gate = gate


def clean(value):
    """JSON-ready copy: numpy scalars to Python, non-finite floats to None."""
    if isinstance(value, dict):
        return {str(k): clean(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [clean(v) for v in value]
    if isinstance(value, (np.bool_, bool)):
        return bool(value)
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating, float)):
        return float(value) if math.isfinite(float(value)) else None
    if isinstance(value, (dt.date, dt.datetime, pd.Timestamp)):
        return value.isoformat()
    return value


def write_json(path: Path, payload) -> None:
    path.write_text(json.dumps(clean(payload), indent=2, sort_keys=True) + "\n")


def get(data: dict, path: str):
    node = data
    for part in path.split("/"):
        if not isinstance(node, dict) or part not in node:
            raise GateFailure(f"a committed summary lacks {path}")
        node = node[part]
    return node


# ---------------------------------------------------------------------------
# 1. Pinned inputs: every hash comes from a committed record.


def check_hash(path: Path, expected: str, what: str) -> str:
    """sha256 of ``path`` must equal ``expected``; a changed byte fails."""
    if not Path(path).is_file():
        raise GateFailure(f"{what}: {path} is missing")
    got = sha256_file(Path(path))
    if got != expected:
        raise GateFailure(f"{what}: sha256 {got} differs from the committed {expected}")
    return got


def hash_negative_control(path: Path, expected: str, what: str) -> str:
    """The hash gate must reject a hash that differs in one character."""
    wrong = ("0" if expected[0] != "0" else "1") + expected[1:]
    try:
        check_hash(path, wrong, what)
    except GateFailure:
        return "rejected as required"
    raise GateFailure(f"{what}: the hash gate accepted a wrong hash")


def check_readings(root: Path) -> dict:
    """Gate G18c: the readings were fixed before the scoring. Amendment 18 must
    be present with the sha256 under which it was accepted; a changed byte
    stops the run. This is the first thing a scoring run does."""
    path = Path(root) / AMENDMENT_18
    return {
        "amendment_18": {
            "path": AMENDMENT_18.as_posix(),
            "sha256": check_hash(path, AMENDMENT_18_SHA, "Amendment 18 (gate G18c)"),
            "negative_control": hash_negative_control(
                path, AMENDMENT_18_SHA, "Amendment 18 (gate G18c)"
            ),
            "status": "passed",
        }
    }


def load_freeze(root: Path) -> dict:
    """The frozen forecasts and the incumbency file, by the committed freeze record."""
    root = Path(root)
    check_hash(root / FREEZE_RECORD, FREEZE_RECORD_SHA, "freeze record")
    record = json.loads((root / FREEZE_RECORD).read_text())
    if record.get("forecast_sha256") != REGISTERED_FROZEN_SHA:
        raise GateFailure(
            "the freeze record's forecast hash differs from the hash printed in Amendments 1, 7 and 8"
        )
    frozen_path = root / FREEZE_DIR / record["forecast_file"]
    incumbency_path = root / FREEZE_DIR / record["incumbency_file"]
    gates = {
        "frozen_forecasts": {
            "path": (FREEZE_DIR / record["forecast_file"]).as_posix(),
            "sha256": check_hash(
                frozen_path, record["forecast_sha256"], "frozen forecasts"
            ),
            "source_of_expected_hash": FREEZE_RECORD.as_posix(),
            "negative_control": hash_negative_control(
                frozen_path, record["forecast_sha256"], "frozen forecasts"
            ),
            "status": "passed",
        },
        "incumbency": {
            "path": (FREEZE_DIR / record["incumbency_file"]).as_posix(),
            "sha256": check_hash(
                incumbency_path, record["incumbency_sha256"], "incumbency file"
            ),
            "source_of_expected_hash": FREEZE_RECORD.as_posix(),
            "negative_control": hash_negative_control(
                incumbency_path, record["incumbency_sha256"], "incumbency file"
            ),
            "status": "passed",
        },
    }
    frozen = pd.read_parquet(frozen_path)
    if len(frozen) != record["rows"] or frozen.duplicated(FROZEN_KEY).any():
        raise GateFailure(
            "the frozen file's rows or keys differ from the freeze record"
        )
    return {
        "record": record,
        "frozen": frozen,
        "incumbency": pd.read_parquet(incumbency_path),
        "gates": gates,
    }


def load_published_arm(root: Path, frozen: pd.DataFrame, *, override=None) -> dict:
    """Amendment 15, E31c: the second frozen file, when it was registered in time.

    Absent file: the read-out is reported as "not registered in time". Present
    file: the record beside it must be the committed one, the file's hash must
    equal the hash in that record (G31b: a changed byte fails), the file must
    hold exactly the pinned file's keys, and no forecast may be missing.
    ``override`` (rehearsal only) is a (parquet path, record path) pair of a
    made-up arm; the committed record's own hash is then not checked.
    """
    path, record_path = (
        (Path(root) / PUBLISHED_ARM_FILE, Path(root) / PUBLISHED_ARM_RECORD)
        if override is None
        else (Path(override[0]), Path(override[1]))
    )
    if not path.is_file():
        if record_path.is_file():
            raise GateFailure(
                "the published-table arm has a freeze record but no forecast file"
            )
        return {
            "status": "not_registered_in_time",
            "file": PUBLISHED_ARM_FILE.as_posix(),
        }
    if not record_path.is_file():
        raise GateFailure(
            f"the published-table arm is present without its committed freeze record {PUBLISHED_ARM_RECORD}"
        )
    if override is None:
        check_hash(
            record_path, PUBLISHED_ARM_RECORD_SHA, "published-table freeze record"
        )
    record = json.loads(record_path.read_text())
    expected = record.get("forecast_sha256")
    if not expected:
        raise GateFailure("the published-table arm's record holds no forecast_sha256")
    if record.get("arm") != PUBLISHED_ARM:
        raise GateFailure(
            f"the frozen arm is {record.get('arm')!r}, not {PUBLISHED_ARM!r}: another table needs a dated addendum"
        )
    got = check_hash(path, expected, "published-table arm")
    control = hash_negative_control(path, expected, "published-table arm")
    arm = pd.read_parquet(path)
    if PUBLISHED_ARM not in arm.columns or not set(FROZEN_KEY) <= set(arm.columns):
        raise GateFailure(
            "the published-table arm lacks its keys or its forecast column"
        )
    same_keys = len(arm) == len(frozen) and not arm.duplicated(FROZEN_KEY).any()
    if same_keys:
        merged = frozen[FROZEN_KEY].merge(arm[FROZEN_KEY], how="outer", indicator=True)
        same_keys = bool(merged._merge.eq("both").all())
    if not same_keys:
        raise GateFailure(
            "G31b: the published-table arm does not hold exactly the keys of the pinned frozen file"
        )
    if not np.isfinite(arm[PUBLISHED_ARM].to_numpy(float)).all():
        raise GateFailure("G31b: the published-table arm has a missing forecast")
    return {
        "status": "read",
        "file": PUBLISHED_ARM_FILE.as_posix(),
        "sha256": got,
        "source_of_expected_hash": PUBLISHED_ARM_RECORD.as_posix(),
        "record_sha256": sha256_file(record_path),
        "negative_control": control,
        "forecast_column": PUBLISHED_ARM,
        "rows": len(arm),
        "synthetic": override is not None,
        "frame": arm[FROZEN_KEY + [PUBLISHED_ARM]],
    }


def load_committed(root: Path) -> dict:
    """Committed 2020-2025 summaries, each checked against its sha256."""
    out = {"sha256": {}}
    for name, (relative, sha) in COMMITTED.items():
        path = Path(root) / relative
        check_hash(path, sha, f"committed input {name}")
        out["sha256"][relative] = sha
        if relative.endswith(".json"):
            out[name] = json.loads(path.read_text())
        elif relative.endswith(".csv"):
            out[name] = pd.read_csv(path)
        else:
            out[name] = path.read_text()
    return out


def power_rows(protocol: str) -> dict:
    """The registered power table: contrast -> (SD, detectable at n=100, at n=150)."""
    rows = {}
    pattern = re.compile(
        r"^\| (.+?) \| ([0-9.]+) \| [0-9.]+ \| ([0-9.]+) / ([0-9.]+) \|$"
    )
    for line in protocol.splitlines():
        m = pattern.match(line.strip())
        if m:
            rows[m.group(1)] = tuple(float(m.group(i)) for i in (2, 3, 4))
    missing = [name for name in POWER_ROWS.values() if name not in rows]
    if missing:
        raise GateFailure(f"registered power rows missing: {missing}")
    return rows


def detectable(sd: float, n: int) -> float:
    """80%-power detectable effect at two-sided 5% for n independent differences."""
    return float(POWER_Z * sd / math.sqrt(n)) if n > 0 else math.nan


def power_gate(rows: dict, tolerance: float = 0.001) -> dict:
    """The formula must give back the registered table at n = 100 and 150.

    The table prints three decimals from unrounded standard deviations, so the
    recomputation from the printed SD is checked to 0.001.
    """
    worst = 0.0
    for name in POWER_ROWS.values():
        sd, at100, at150 = rows[name]
        worst = max(
            worst, abs(detectable(sd, 100) - at100), abs(detectable(sd, 150) - at150)
        )
    if not worst <= tolerance:
        raise GateFailure(
            f"the detectable-effect formula misses the registered power table by {worst:.4f}"
        )
    return {"max_difference": worst, "tolerance": tolerance}


# ---- band half-widths (Amendment 8, "At the February re-score only") ---------


def band_half_widths(anchor: pd.DataFrame) -> dict:
    """Split-conformal quantiles of the league-aware forecast's absolute errors
    on all 674 arrivals of 2020-2025 (walk-forward forecasts, committed)."""
    if len(anchor) != 674 or anchor.duplicated(KEY).any():
        raise GateFailure("the committed 2020-2025 forecasts are not the 674 arrivals")
    scores = np.abs(anchor[OUTCOME].to_numpy(float) - anchor[O].to_numpy(float))
    return {
        f"{int(round(100 * level))}": float(
            intervals.conformal_quantile(scores, alpha=1 - level)
        )
        for level in BAND_LEVELS
    }


def bands(root: Path, out: Path) -> dict:
    """Compute the two half-widths and write the file that pins them by value."""
    committed = load_committed(root)
    widths = band_half_widths(committed["anchor_674"])
    result = {
        "analysis": "P1 band half-widths (Amendment 8)",
        "arm": O,
        "definition": "split-conformal quantile, ceil((n+1) x level) of n, of the absolute walk-forward errors of the league-aware forecast on the 674 arrivals of 2020-2025",
        "n": 674,
        "source": COMMITTED["anchor_674"][0],
        "source_sha256": COMMITTED["anchor_674"][1],
        "half_width_eff36": widths,
        "use": "added to and subtracted from the league-aware frozen forecast of a 2026-27 newcomer; read at the February re-score, descriptive in November",
    }
    out = Path(out)
    out.mkdir(parents=True, exist_ok=False)
    write_json(out / BANDS_FILE.name, result)
    print(f"band half-widths: {widths}")
    return result


def load_bands(root: Path, anchor: pd.DataFrame, tolerance: float = 1e-12) -> dict:
    """The pinned half-widths; the run refuses if a recomputation differs.

    Amendment 18, rule 8: the file is the one committed with sha256
    ``BANDS_SHA``; the scoring run recomputes the two values and stops if they
    differ. ``tolerance`` exists for the negative control only."""
    path = Path(root) / BANDS_FILE
    if not path.is_file():
        raise GateFailure(f"the pinned band half-widths {BANDS_FILE} are not committed")
    check_hash(path, BANDS_SHA, "band half-widths (Amendment 18, rule 8)")
    pinned = json.loads(path.read_text())["half_width_eff36"]
    now = band_half_widths(anchor)
    if set(pinned) != set(now) or any(
        not abs(float(pinned[k]) - now[k]) <= tolerance for k in now
    ):
        raise GateFailure(
            f"the band half-widths differ from the pinned values: {now} against {pinned}"
        )
    return {
        "file": BANDS_FILE.as_posix(),
        "sha256": sha256_file(path),
        "half_width_eff36": {k: float(v) for k, v in pinned.items()},
        "status": "passed",
    }


# ---------------------------------------------------------------------------
# 2. Data gates on the outcome files.


def _require(frame: pd.DataFrame, columns, what: str, gate: str) -> None:
    missing = [c for c in columns if c not in frame.columns]
    if missing:
        raise GateFailure(f"{what} lacks columns {missing}", gate)


def gate_season(box: pd.DataFrame, league: str) -> dict:
    """Every box-score row belongs to stored season 2026 (2026-27)."""
    _require(box, BOX_COLUMNS, f"{league} box scores", "season")
    if not len(box):
        raise GateFailure(f"{league} box scores hold no row", "season")
    seasons = sorted({int(s) for s in box.Season.unique()})
    if seasons != [SEASON]:
        raise GateFailure(
            f"{league} box scores hold seasons {seasons}, not only {SEASON}", "season"
        )
    return {"seasons": seasons, "rows": len(box)}


def scraped_range(frame: pd.DataFrame, what: str):
    stamps = pd.to_datetime(frame["_scraped_at"], utc=True, errors="coerce")
    if stamps.isna().any():
        raise GateFailure(
            f"{what}: {int(stamps.isna().sum())} rows carry no readable refresh time",
            "freshness",
        )
    return stamps.min(), stamps.max()


def gate_freshness(frames: dict, refreshed_from: dt.date = REFRESH_FROM) -> dict:
    """Content, not file time: every row's ``_scraped_at`` is on or after 25 Nov.

    Amendment 18, rule 6: "refreshed on or after 25 Nov" means that every row
    of the four outcome files carries a refresh time on or after 25 November
    2026, 00:00 UTC. A refresh that appends new games and keeps older rows with
    older refresh times does not pass.

    A retained run copies its inputs, so a file's modification time is the time
    of the copy. The refresh time the scraper writes into each row is not.
    """
    out = {}
    for what, frame in frames.items():
        _require(frame, ("_scraped_at",), what, "freshness")
        if not len(frame):
            raise GateFailure(f"{what} holds no row", "freshness")
        first, last = scraped_range(frame, what)
        if first.date() < refreshed_from:
            raise GateFailure(
                f"{what} was refreshed on {first.date()} (UTC), before {refreshed_from}",
                "freshness",
            )
        out[what] = {"refreshed_first": first, "refreshed_last": last}
    return out


def schedule_dates(schedule: pd.DataFrame, league: str) -> pd.DataFrame:
    _require(schedule, SCHEDULE_COLUMNS, f"{league} schedule", "schedule_dates")
    dates = pd.to_datetime(schedule.date, format="%b %d, %Y", errors="coerce").dt.date
    if dates.isna().any():
        raise GateFailure(
            f"{league} schedule: {int(dates.isna().sum())} game dates cannot be read",
            "schedule_dates",
        )
    out = schedule.assign(_date=dates)
    if out.gameCode.duplicated().any():
        raise GateFailure(f"{league} schedule lists a game twice", "schedule_dates")
    return out


def gate_schedule(
    box: pd.DataFrame, schedule: pd.DataFrame, league: str, cutoff: dt.date = CUTOFF
) -> dict:
    """Schedule against box scores, both ways, and no missing round.

    * every box-score game is in the schedule (so it has a date);
    * every scheduled game dated on or before the cutoff that the schedule
      marks as played has a box score: a missing box score stops the run;
    * Amendment 18, rule 1: a game dated on or before the cutoff that the
      refreshed schedule marks as NOT played is a postponed game. It does not
      stop the run. It is listed with its game code, date and clubs, and
      counted. Only an explicit ``played == False`` is read as not played;
    * the rounds among the games dated on or before the cutoff are 1..R within
      each phase, with no gap: a round with no game at all stops the run.
    """
    dated = schedule_dates(schedule, league)
    in_box = set(box.Gamecode.unique())
    unknown = sorted(in_box - set(dated.gameCode))
    if unknown:
        raise GateFailure(
            f"{league}: {len(unknown)} box-score games are missing from the schedule, e.g. {unknown[:5]}",
            "boxscore_in_schedule",
        )
    due = dated.loc[dated._date <= cutoff]
    if not len(due):
        raise GateFailure(
            f"{league} schedule holds no game dated on or before {cutoff}",
            "completeness",
        )
    without_box = due.loc[~due.gameCode.isin(in_box)]
    not_played = without_box.played.map(
        lambda v: isinstance(v, (bool, np.bool_)) and not v
    )
    missing, postponed = without_box.loc[~not_played], without_box.loc[not_played]
    if len(missing):
        raise GateFailure(
            f"{league}: {len(missing)} games dated on or before {cutoff} are marked played and have no box score "
            f"(game codes {sorted(missing.gameCode)[:8]})",
            "completeness",
        )
    postponed_games = [
        {
            "competition": league,
            "game_code": int(r["gameCode"]),
            "date": r["_date"].isoformat(),
            "phase": str(r["Phase"]),
            "round": int(r["Round"]),
            "home": str(r["hometeam"]),
            "away": str(r["awayteam"]),
        }
        for r in postponed.sort_values(["_date", "gameCode"]).to_dict("records")
    ]
    anomalies = []
    for phase, group in due.groupby("Phase", sort=True):
        rounds = sorted(int(r) for r in group.Round.unique())
        gaps = sorted(set(range(1, max(rounds) + 1)) - set(rounds))
        if gaps:
            raise GateFailure(
                f"{league} phase {phase}: rounds {gaps} are missing among games dated on or before {cutoff}",
                "rounds",
            )
        counts = group.groupby("Round").size()
        usual = int(counts.mode().iloc[0])
        anomalies += [
            {"phase": str(phase), "round": int(r), "games": int(n), "usual": usual}
            for r, n in counts.items()
            if int(n) != usual
        ]
    return {
        "games_scheduled_by_cutoff": len(due),
        "games_with_box_score_by_cutoff": len(due) - len(postponed_games),
        "games_postponed": len(postponed_games),
        "postponed_games": postponed_games,
        "games_after_cutoff_in_box_scores": int(
            (dated.loc[dated.gameCode.isin(in_box), "_date"] > cutoff).sum()
        ),
        "last_game_date_by_cutoff": max(due._date),
        "rounds_by_cutoff": int(due.Round.nunique()),
        "round_count_anomalies": anomalies,
    }


def gate_negative_controls(frames: dict, boxes: dict, schedules: dict) -> dict:
    """Each data gate must reject a broken copy of the very files it passed."""
    out = {}
    try:
        gate_freshness(frames, refreshed_from=dt.date.max)
    except GateFailure:
        out["freshness"] = "rejected as required (impossible refresh date)"
    else:
        raise GateFailure("the freshness gate accepted an impossible refresh date")
    league = DESTINATIONS[0]
    box, schedule = boxes[league], schedules[league]
    dated = schedule_dates(schedule, league)
    # a game that is due, has a box score and is not itself postponed
    due = dated.loc[(dated._date <= CUTOFF) & dated.gameCode.isin(set(box.Gamecode))]
    if not len(due):
        raise GateFailure(f"{league}: no game with a box score to run the controls on")
    victim = due.gameCode.iloc[0]
    try:
        gate_schedule(box.loc[box.Gamecode.ne(victim)], schedule, league)
    except GateFailure as failure:
        if failure.gate != "completeness":
            raise
        out["completeness"] = "rejected as required (one game's box score removed)"
    else:
        raise GateFailure("the completeness gate accepted a missing box score")
    # Gate G18a, second control: the same game marked not played must pass and
    # must appear in the list of postponed games.
    marked = schedule.assign(
        played=schedule.played.where(schedule.gameCode.ne(victim), False)
    )
    before = gate_schedule(box, schedule, league)["games_postponed"]
    listed = gate_schedule(box.loc[box.Gamecode.ne(victim)], marked, league)
    if listed["games_postponed"] != before + 1 or int(victim) not in {
        g["game_code"] for g in listed["postponed_games"]
    }:
        raise GateFailure("a game marked not played was not listed as postponed")
    out["postponed"] = "passed and listed as required (the same game marked not played)"
    last = dated.loc[dated._date <= CUTOFF, "Round"].max()
    if last >= 3:
        middle = int(last) - 1
        try:
            keep = dated.loc[dated.Round.ne(middle)]
            gate_schedule(
                box.loc[box.Gamecode.isin(keep.gameCode)],
                schedule.loc[schedule.Round.ne(middle)],
                league,
            )
        except GateFailure as failure:
            if failure.gate != "rounds":
                raise
            out["rounds"] = "rejected as required (one round removed from both files)"
        else:
            raise GateFailure("the round gate accepted a missing round")
    return out


def people_records(paths, gate: str = "people_list") -> list:
    """Amendment 18, rule 7: each list was written by the committed script and
    fetched on or after 25 November; its sha256 goes into the score record."""
    out = []
    for path in paths:
        try:
            record = registration.check_record(Path(path))
        except registration.Refused as refused:
            raise GateFailure(f"registration list: {refused}", gate) from refused
        out.append(
            {
                "path": str(path),
                "role": "API registration list",
                "sha256": record["sha256"],
                "rows": record["rows"],
                "fetched_at_utc": record["fetched_at_utc"],
                "record_file": record["record_file"],
                "record_sha256": record["record_sha256"],
                "written_by": record.get("script"),
            }
        )
    if not out:
        raise GateFailure("no API registration list was given", gate)
    return out


def load_people(paths, gate: str = "people_list") -> pd.DataFrame:
    """The EuroLeague API registration list for 2026-27: names, clubs, previous
    teams, in the layout of E26's list. It holds no statistic (Amendment 8,
    rule 3; Amendment 18, rule 7)."""
    frames = []
    for path in paths:
        frame = pd.read_csv(path, dtype=str, keep_default_na=False)
        _require(frame, PEOPLE_COLUMNS, f"people list {Path(path).name}", gate)
        frames.append(frame)
    if not frames:
        raise GateFailure("no API people list was given", gate)
    people = pd.concat(frames, ignore_index=True)
    people = people.loc[people.season.astype(int).eq(SEASON)].copy()
    people["player_name"] = people.name.map(api.pairing_key)
    codes = set(COMPETITION_CODE.values())
    people = people.loc[people.comp.isin(codes) & people.player_name.notna()]
    missing = sorted(codes - set(people.comp))
    if missing:
        raise GateFailure(
            f"the API people list has no {SEASON} row for competitions {missing}", gate
        )
    return people.reset_index(drop=True)


# ---------------------------------------------------------------------------
# 3. The newcomer ledger: one row and one reason per player, nothing dropped.


def destination_games(
    box: pd.DataFrame, schedule: pd.DataFrame, league: str, cutoff: dt.date = CUTOFF
) -> pd.DataFrame:
    """Player-games of games dated on or before the cutoff, corpus schema."""
    dated = schedule_dates(schedule, league)
    merged = box.merge(
        dated[["gameCode", "_date"]].rename(columns={"gameCode": "Gamecode"}),
        on="Gamecode",
        how="left",
        validate="m:1",
    )
    if merged._date.isna().any():
        raise GateFailure(
            "box-score games missing from the schedule", "boxscore_in_schedule"
        )
    kept = merged.loc[merged._date <= cutoff].drop(columns="_date")
    kept = api.drop_non_player_rows(kept.assign(league=league))
    out = api.to_proballers_schema(kept)
    out["display_name"] = out.player_name.astype(str)
    out["player_name"] = out.player_name.map(api.pairing_key)
    return out[out.player_name.notna()].reset_index(drop=True)


def destination_aggregates(games: pd.DataFrame) -> pd.DataFrame:
    return (
        games.groupby(["player_name", "league"])
        .agg(
            games=("game_id", "nunique"),
            minutes=("minutes", "sum"),
            pir=("pir", "sum"),
            club=("team", lambda s: s.value_counts().idxmax()),
            display_name=("display_name", lambda s: s.value_counts().idxmax()),
        )
        .reset_index()
    )


def ledger(frozen: pd.DataFrame, destination_agg, previous_agg) -> pd.DataFrame:
    """Every player who reaches eight continental games, with why he is or is
    not scored. v10 eligibility, in this order:

    * ``incumbent``: a qualifying (>= 8 games, positive minutes) 2025-26
      continental stint;
    * ``unjoined``: no frozen row under his name for this competition;
    * ``source_rate_not_positive`` / ``outcome_rate_not_positive``: the v10
      rule that both rates are positive;
    * ``forecast_missing``: a frozen row without every forecast. This is an
      unscorable target: it makes the test inconclusive;
    * ``scored``.

    The largest-minutes qualifying stint is the target, as in v10.
    """
    q = destination_agg[
        (destination_agg.games >= holdout.MIN_GAMES) & (destination_agg.minutes > 0)
    ]
    dest = q.sort_values(
        ["minutes", "league"], ascending=[False, True], kind="mergesort"
    ).drop_duplicates("player_name")
    prev = previous_agg[
        (previous_agg.games >= holdout.MIN_GAMES) & (previous_agg.minutes > 0)
    ]
    dest = dest.rename(
        columns={
            "league": "league_dest",
            "games": "games_dest",
            "minutes": "minutes_dest",
            "pir": "pir_dest",
            "club": "club_dest",
            "display_name": "player_display_name",
        }
    )
    dest[OUTCOME] = 36 * dest.pir_dest / dest.minutes_dest
    rows = dest.merge(
        frozen, on=FROZEN_KEY, how="left", validate="1:1", indicator="_join"
    )
    if len(rows) != len(dest):
        raise GateFailure("the join changed the number of newcomers")
    joined = rows._join.eq("both")
    incumbent = rows.player_name.isin(prev.player_name)
    arms = [a for a in (*common.ALL_ARMS, PUBLISHED_ARM) if a in rows.columns]
    forecast = (
        np.isfinite(
            rows[arms].apply(pd.to_numeric, errors="coerce").to_numpy(float)
        ).all(axis=1)
        & rows.all_arms_forecast.eq(True).to_numpy()
    )
    source_ok = rows.source_positive_finite.eq(True).to_numpy()
    outcome = rows[OUTCOME].to_numpy(float)
    outcome_ok = np.isfinite(outcome) & (outcome > 0)
    rows["reason"] = np.select(
        [incumbent, ~joined, ~source_ok, ~outcome_ok, ~forecast],
        [
            "incumbent",
            "unjoined",
            "source_rate_not_positive",
            "outcome_rate_not_positive",
            "forecast_missing",
        ],
        default="scored",
    )
    rows["season_dest"] = SEASON
    rows["cluster"] = f"{SEASON}|" + rows.league_dest + "|" + rows.club_dest.astype(str)
    return (
        rows.drop(columns="_join")
        .sort_values(["league_dest", "player_name"])
        .reset_index(drop=True)
    )


# ---- the join rule (Amendment 8, rule 3) -------------------------------------


def club_words(name: object) -> frozenset:
    """Amendment 6's text rule: upper case, no accents or punctuation, generic words dropped."""
    if not isinstance(name, str):
        return frozenset()
    text = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    words = re.sub(r"[^A-Z0-9]", " ", text.upper()).split()
    return frozenset(w for w in words if w not in GENERIC_WORDS)


def clubs_match(a: object, b: object) -> bool:
    """All words of the shorter name are in the longer one, or Jaccard >= 0.6."""
    x, y = club_words(a), club_words(b)
    if not x or not y:
        return False
    short, long_ = (x, y) if len(x) <= len(y) else (y, x)
    if short <= long_:
        return True
    return len(x & y) / len(x | y) >= JACCARD_MIN


def surname(key: str) -> str:
    """Amendment 18, rule 3: a player's surname is the last word of his name
    after the v10 name normaliser (which has already dropped suffixes)."""
    return key.split()[-1] if key else ""


def edits(a: str, b: str, limit: int = MAX_EDITS) -> int:
    """Levenshtein distance, cut off above ``limit`` (returns limit + 1)."""
    if abs(len(a) - len(b)) > limit:
        return limit + 1
    previous = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        current = [i]
        for j, cb in enumerate(b, 1):
            current.append(
                min(previous[j] + 1, current[j - 1] + 1, previous[j - 1] + (ca != cb))
            )
        if min(current) > limit:
            return limit + 1
        previous = current
    return previous[-1]


def join_audit(rows: pd.DataFrame, frozen: pd.DataFrame, people: pd.DataFrame):
    """List every unjoined newcomer and mark the possible lost targets.

    No name is joined by hand. An unjoined newcomer is a possible lost target
    if a frozen row has (a) his surname and a 2025-26 club that matches his
    API previous club by Amendment 6's text rule, or (b) a full name key within
    two character edits of his. The count is a lower bound (rule 3).

    Amendment 18, rule 3: the 5% bar divides the possible lost targets by the
    newcomers who joined a frozen row ("of the joined newcomers"), not by the
    scored newcomers.
    """
    names = frozen.drop_duplicates("player_name")[["player_name", "club_src"]]
    keys = names.player_name.tolist()
    by_surname: dict = {}
    for key, club in zip(keys, names.club_src):
        by_surname.setdefault(surname(key), []).append((key, club))
    previous = {
        (comp, key): sorted({t for t in group.last_team if t})
        for (comp, key), group in people.groupby(["comp", "player_name"])
    }
    listed = set(previous)
    unjoined = rows.loc[rows.reason.eq("unjoined")]
    out = []
    for r in unjoined.itertuples():
        comp = COMPETITION_CODE[r.league_dest]
        teams = previous.get((comp, r.player_name), [])
        rule, match, match_club = "", "", ""
        for key, club in by_surname.get(surname(r.player_name), []):
            if any(clubs_match(t, club) for t in teams):
                rule, match, match_club = (
                    "a: same surname, previous club matches",
                    key,
                    club,
                )
                break
        if not rule:
            best = min(
                ((edits(r.player_name, key), key) for key in keys), default=(99, "")
            )
            if best[0] <= MAX_EDITS:
                rule, match = f"b: name within {best[0]} character edits", best[1]
                match_club = names.loc[names.player_name.eq(best[1]), "club_src"].iloc[
                    0
                ]
        out.append(
            {
                "player_display_name": r.player_display_name,
                "player_name": r.player_name,
                "competition": r.league_dest,
                "club": r.club_dest,
                "previous_club": "; ".join(teams) if teams else "",
                "in_api_people_list": (comp, r.player_name) in listed,
                "games": int(r.games_dest),
                "possible_lost_target": bool(rule),
                "rule": rule,
                "frozen_name": match,
                "frozen_club": match_club,
            }
        )
    table = pd.DataFrame(
        out,
        columns=[
            "player_display_name",
            "player_name",
            "competition",
            "club",
            "previous_club",
            "in_api_people_list",
            "games",
            "possible_lost_target",
            "rule",
            "frozen_name",
            "frozen_club",
        ],
    )
    reached = rows.loc[~rows.reason.eq("incumbent")]
    joined = int((~reached.reason.eq("unjoined")).sum())
    lost = int(table.possible_lost_target.sum()) if len(table) else 0
    in_list = [
        (COMPETITION_CODE[league], key) in listed
        for league, key in zip(reached.league_dest, reached.player_name)
    ]
    if len(reached) and not any(in_list):
        raise GateFailure(
            "the API people list names none of the players who reached eight games",
            "people_list",
        )
    share = lost / joined if joined else (math.inf if lost else 0.0)
    summary = {
        "newcomers_reaching_eight_games": len(reached),
        "joined": joined,
        "unjoined": len(table),
        "possible_lost_targets": lost,
        "possible_lost_share_of_joined": share,
        "threshold": LOST_SHARE_MAX,
        "above_threshold": bool(share > LOST_SHARE_MAX),
        "share_found_in_api_people_list": float(np.mean(in_list)) if in_list else None,
        "unjoined_found_in_api_people_list": int(table.in_api_people_list.sum())
        if len(table)
        else 0,
        "rule": "Amendment 8, rule 3: (a) same surname and a 2025-26 club matching the API previous club by Amendment 6's text rule, or (b) a full name key within two character edits; a lower bound",
    }
    return table, summary


# ---------------------------------------------------------------------------
# 4. The pre-read block: printed and written before any contrast is read.


def expected_noise(games, committed: dict, tolerance: float = 1e-9) -> dict:
    """E6's noise at the realised game counts (3 Nov, "Outcome").

    Amendment 18, rule 4: the per-game variance is E6's variance divided by the
    mean of 1 / games over the 674, and the expected noise for the newcomers is
    that per-game variance times the mean of 1 / games over the newcomers. The
    formula must give back E6's value at the 674's own game counts, or the run
    stops.

    E6 gives the noise SD of a full-season EFF/36 on the 674 (normal model).
    Noise variance falls in proportion to games played, so the 674's noise
    variance is v x mean(1 / games) for a per-game variance v. The same v at
    the newcomers' game counts gives their expected noise.
    """
    e6 = get(committed["e6"], "e6/outcomes/O1")
    anchor = committed["anchor_674"]
    anchor_games = (anchor.even_games + anchor.odd_games).to_numpy(float)
    per_game = e6["noise_sd_normal"] ** 2 / float(np.mean(1 / anchor_games))
    games = np.asarray(games, float)

    def at(g):
        sd = float(np.sqrt(per_game * np.mean(1 / np.asarray(g, float))))
        return {"noise_sd": sd, "noise_floor_mae": float(np.sqrt(2 / np.pi) * sd)}

    check = at(anchor_games)
    if not abs(check["noise_sd"] - e6["noise_sd_normal"]) <= tolerance:
        raise GateFailure(
            "the noise formula does not give back E6 at the 674's own games"
        )
    return {
        "source": "E6 split-half, EFF/36, normal model (robustness summary), scaled by games played",
        "full_season_674": {
            "noise_sd": e6["noise_sd_normal"],
            "noise_floor_mae": e6["floor_normal"],
            "median_games": float(np.median(anchor_games)),
            "spearman_brown_reliability": e6["spearman_brown_reliability"],
        },
        "at_realised_games": at(games) if len(games) else None,
        "gate": "the formula reproduces E6's noise SD at the 674's own game counts (1e-9); a tolerance of -1 is rejected",
    }


def pre_read(rows: pd.DataFrame, audit: dict, committed: dict, arm_status: str) -> dict:
    """Sample size, detectable effects and expected noise. No outcome is read:
    the frame passed in must not carry an outcome column."""
    leaked = [c for c in OUTCOME_COLUMNS if c in rows.columns]
    if leaked:
        raise GateFailure(f"the pre-read block was given outcome columns {leaked}")
    scored = rows.loc[rows.reason.eq("scored")]
    n = len(scored)
    power = power_rows(committed["protocol"])
    gate = power_gate(power)
    effects = {}
    for name, row in POWER_ROWS.items():
        sd = power[row][0]
        effects[name] = {
            "sd_2020_2025": sd,
            "detectable_80": detectable(sd, n),
            "method": "registered power table (3 Nov): 2.80 x SD / sqrt(n)",
        }
    for name, e28 in E28_NAMES.items():
        record = get(committed["e28"], f"e28a/contrasts/{e28}/unweighted")
        effects[name] = {
            "estimate_2020_2025": record["difference"],
            "detectable_80_at_674": record["detectable_80"],
            "detectable_80": record["detectable_80"] * math.sqrt(record["n"] / n)
            if n
            else math.nan,
            "method": "E28's clustered detectable effect on the 674, scaled by sqrt(674 / n) (Amendment 18, rule 4)",
        }
    games = scored.games_dest.to_numpy(float)
    block = {
        "printed_before_any_contrast": True,
        "counts_by_reason": {k: int(rows.reason.eq(k).sum()) for k in REASONS},
        "n_scored": n,
        "n_unscorable": int(rows.reason.eq("forecast_missing").sum()),
        "min_n": MIN_SCORED,
        "n_scored_by_competition": {
            k: int(v) for k, v in scored.league_dest.value_counts().sort_index().items()
        },
        "n_complete_source": int(scored.source_complete_season.astype(bool).sum())
        if n
        else 0,
        "games": {
            "median": float(np.median(games)) if n else None,
            "min": float(games.min()) if n else None,
            "max": float(games.max()) if n else None,
        },
        "minutes_median": float(scored.minutes_dest.median()) if n else None,
        "destination_clubs": int(scored.cluster.nunique()),
        "join": audit,
        "detectable_effects": effects,
        "power_table_gate": gate,
        "expected_noise": expected_noise(games, committed),
        "published_table_arm": arm_status,
        "caveat": "partial-season outcomes make these detectable effects optimistic (3 Nov registration)",
    }
    return block


def print_pre_read(block: dict) -> None:
    print("=== PRE-READ (printed before any 2026-27 contrast is read) ===")
    print(f"newcomers by reason: {block['counts_by_reason']}")
    print(
        f"scored n = {block['n_scored']} (minimum {block['min_n']}); unscorable = {block['n_unscorable']}; "
        f"by competition {block['n_scored_by_competition']}; median games {block['games']['median']}"
    )
    j = block["join"]
    print(
        f"join: {j['joined']} joined, {j['unjoined']} unjoined, {j['possible_lost_targets']} possible lost targets "
        f"({j['possible_lost_share_of_joined']:.1%} of joined; limit {j['threshold']:.0%})"
    )
    for name, e in block["detectable_effects"].items():
        print(
            f"detectable effect {name}: {e['detectable_80']:.3f} EFF/36 ({e['method']})"
        )
    noise = block["expected_noise"]["at_realised_games"]
    if noise:
        print(
            f"expected outcome noise at the realised games: SD {noise['noise_sd']:.3f}, floor {noise['noise_floor_mae']:.3f} EFF/36"
        )
    print(f"published-table arm: {block['published_table_arm']}")
    if "postponed_games" in block:
        print(
            f"postponed games listed (Amendment 18, rule 1): {block['postponed_games']}"
        )
    print("=== END PRE-READ ===", flush=True)


# ---------------------------------------------------------------------------
# 5. Contrasts and read-outs (never called before the pre-read block is written).


def contrast_record(
    rows: pd.DataFrame, left: str, right: str, *, weighted=False
) -> dict:
    """Paired MAE(left) - MAE(right) with the v10 two-way clustered interval
    (player, destination club). ``player_club_season`` repeats the estimate in
    the layout of the 2020-2025 summaries."""
    if len(rows) < 2:
        return {
            "left": left,
            "right": right,
            "positive_favours": right,
            "weighting": "minutes_weighted" if weighted else "unweighted",
            "n": len(rows),
            "difference": None,
            "ci95": None,
            "status": "not_estimable",
            "reading": "not_estimable",
        }
    record = a9.gain(rows, left, right, weighted=weighted)
    record["player_club_season"] = {
        "difference": record["difference"],
        "ci95": record["ci95"],
    }
    return record


def primary_block(rows: pd.DataFrame) -> dict:
    return {
        "n": len(rows),
        **{name: contrast_record(rows, *pair) for name, pair in PRIMARY.items()},
    }


def verdicts(block: dict, anchor: dict) -> dict:
    """Amendment 8, rule 1. A primary contrast fails to replicate when (i) its
    95% interval excludes its 2020-2025 point estimate, (ii) its own estimate
    has the opposite sign and (iii), for P-a, its interval also excludes zero."""
    out = {}
    for name in PRIMARY:
        c = block[name]
        if c["ci95"] is None:
            out[name] = "not_estimable"
            continue
        lo, hi = c["ci95"]
        ref = anchor[name]
        fails = (not lo <= ref <= hi) and ((c["difference"] > 0) != (ref > 0))
        if name == "P-a":
            fails = fails and not lo <= 0 <= hi
        out[name] = "fails" if fails else "consistent"
    return out


def _draws(n_boot) -> int:
    """The registered 2,000 draws unless a test passes a smaller number."""
    return N_BOOT if n_boot is None else int(n_boot)


def _bootstrap(rows: pd.DataFrame, statistic, *, n_boot=None, seed=BOOT_SEED):
    """E18a's bootstrap: destination club-seasons resampled within each
    competition, 2,000 draws, seed 0. ``statistic(frame, positions)`` -> dict."""
    frame, pool_groups = a3.pool_frame(rows)
    point = statistic(frame, np.arange(len(frame)))
    rng = np.random.default_rng(seed)
    draws = [
        statistic(frame, a3.pool_draw(pool_groups, rng)) for _ in range(_draws(n_boot))
    ]
    return point, draws


def _side(ci95, null: float = 0.0) -> str:
    if ci95[0] > null:
        return "above"
    if ci95[1] < null:
        return "below"
    return "includes"


def forecast_level(rows: pd.DataFrame, *, n_boot=None, seed=BOOT_SEED) -> dict:
    """S3: mean of forecast - actual EFF/36, with E18a's club bootstrap."""
    arms = [a for a in LEVEL_ARMS]

    def statistic(frame, idx):
        y = frame[OUTCOME].to_numpy(float)[idx]
        return {a: float(np.mean(frame[a].to_numpy(float)[idx] - y)) for a in arms}

    point, draws = _bootstrap(rows, statistic, n_boot=n_boot, seed=seed)
    out = {}
    for arm in arms:
        d = np.array([x[arm] for x in draws])
        ci = dec.interval(d)
        out[arm] = {
            "mean_signed_error": point[arm],
            "ci95": ci,
            "n": len(rows),
            **dec.power_line(d),
            "reading": _side(ci) + "_zero",
        }
    return out


def _pools(rows: pd.DataFrame, arms) -> list:
    return [
        {
            "y": frame[OUTCOME].to_numpy(float),
            "p": {arm: frame[arm].to_numpy(float) for arm in arms},
            "src": frame.league_src.to_numpy(object),
            "groups": dec.cluster_index(frame),
            "n": len(frame),
        }
        for _, frame in dec.pools(rows)
    ]


def ordering(rows: pd.DataFrame, *, n_boot=None, seed=BOOT_SEED) -> dict:
    """S4: within each competition, among pairs with unequal outcomes, the
    share in which the higher forecast had the higher outcome; cross-league and
    same-league pairs; E10's bootstrap."""
    data = _pools(rows, dec.MODELS)

    def evaluate(index_sets) -> dict:
        total: dict = {}
        for d, idx in zip(data, index_sets):
            zeros = np.zeros(len(idx))
            c = a1.typed_pair_counts(
                d["y"][idx],
                {a: p[idx] for a, p in d["p"].items()},
                idx,
                d["src"][idx],
                zeros,
                zeros,
            )
            for name, value in c.items():
                total[name] = total.get(name, 0.0) + value
        return total

    def share(c, kind, arm):
        return a3.ratio(c[f"{kind}|correct:{arm}"], c[f"{kind}|unequal"])

    point = evaluate([np.arange(d["n"]) for d in data])
    rng = np.random.default_rng(seed)
    draws = [
        evaluate([dec.cluster_draw(d["groups"], rng) for d in data])
        for _ in range(_draws(n_boot))
    ]
    out = {}
    for kind in a1.PAIR_TYPES:
        block = {
            "pairs": int(point[f"{kind}|pairs"]),
            "unequal_pairs": int(point[f"{kind}|unequal"]),
        }
        for label, arm in (("league_aware", O), ("history", H)):
            d = np.array([share(x, kind, arm) for x in draws])
            ci = dec.interval(d) if np.isfinite(d).any() else None
            block[label] = {
                "share_correct": share(point, kind, arm),
                "ci95": ci,
                "reading": _side(ci, 0.5) + "_half" if ci else "not_estimable",
            }
        d = np.array([share(x, kind, O) - share(x, kind, H) for x in draws])
        ci = dec.interval(d) if np.isfinite(d).any() else None
        block["league_aware_minus_history"] = {
            "difference": share(point, kind, O) - share(point, kind, H),
            "ci95": ci,
            "reading": _side(ci) + "_zero" if ci else "not_estimable",
        }
        out[kind] = block
    return out


def band_coverage(rows: pd.DataFrame, widths: dict, *, n_boot=None, seed=BOOT_SEED):
    """Descriptive in November: the share of scored newcomers inside each band."""

    def statistic(frame, idx):
        error = np.abs(frame[OUTCOME].to_numpy(float) - frame[O].to_numpy(float))[idx]
        return {k: float(np.mean(error <= w)) for k, w in widths.items()}

    point, draws = _bootstrap(rows, statistic, n_boot=n_boot, seed=seed)
    return {
        k: {
            "nominal": int(k) / 100,
            "half_width": widths[k],
            "coverage": point[k],
            "ci95": dec.interval(np.array([x[k] for x in draws])),
            "n": len(rows),
        }
        for k in widths
    }


def gap_guide(rows: pd.DataFrame, *, n_boot=None, seed=BOOT_SEED) -> list:
    """Descriptive in November: E20's bins on all pairs of scored newcomers in
    the same competition, league-aware forecast."""
    data = _pools(rows, (H, O))

    def evaluate(index_sets) -> dict:
        total: dict = {}
        for d, idx in zip(data, index_sets):
            c = a3.gap_counts(
                d["y"][idx], {a: p[idx] for a, p in d["p"].items()}, idx, d["src"][idx]
            )
            for name, value in c.items():
                total[name] = total.get(name, 0.0) + value
        return total

    point = evaluate([np.arange(d["n"]) for d in data])
    rng = np.random.default_rng(seed)
    draws = [
        evaluate([dec.cluster_draw(d["groups"], rng) for d in data])
        for _ in range(_draws(n_boot))
    ]
    out = []
    for k, label in enumerate(a3.BIN_LABELS):
        pairs = point[f"all|pairs:{O}:{k}"]
        d = np.array(
            [
                a3.ratio(x[f"all|correct:{O}:{k}"], x[f"all|pairs:{O}:{k}"])
                for x in draws
            ]
        )
        out.append(
            {
                "gap_eff36": label,
                "pairs": int(pairs),
                "share_correct": a3.ratio(point[f"all|correct:{O}:{k}"], pairs),
                "ci95": dec.interval(d) if np.isfinite(d).any() else None,
            }
        )
    return out


def read_outs(rows: pd.DataFrame, committed: dict, widths: dict, arm: dict) -> dict:
    """Everything computed from outcomes, in one pass, on the scored rows."""
    complete = rows.loc[rows.source_complete_season.astype(bool)]
    anchor = {
        name: get(committed["recipes"], path) for name, path in ANCHOR_PATHS.items()
    }
    result = {
        "mae": {a: common.mae(rows, a) for a in common.ALL_ARMS},
        "all": primary_block(rows),
        "anchor": anchor,
    }
    result["verdicts"] = verdicts(result["all"], anchor)
    secondary = {
        "count": N_SECONDARY,
        "intervals": "unadjusted 95% intervals",
        **{name: contrast_record(rows, *pair) for name, pair in SECONDARY.items()},
        "S3": forecast_level(rows),
        "S4": ordering(rows),
        "S5": {
            name: contrast_record(rows, *pair, weighted=True)
            for name, pair in {**PRIMARY, **SECONDARY}.items()
        },
    }
    result["secondary"] = secondary
    result["complete_source"] = {
        "n": len(complete),
        "definition": "newcomers whose source league has a complete 2025-26 season",
        **{
            name: contrast_record(complete, *pair)
            for name, pair in {**PRIMARY, **SECONDARY}.items()
        },
    }
    if arm["status"] == "read":
        result["published_table_arm"] = {
            "status": "read",
            "mae": common.mae(rows, PUBLISHED_ARM),
            "table_vs_destination_only": contrast_record(rows, D, PUBLISHED_ARM),
            "league_aware_vs_table": contrast_record(rows, PUBLISHED_ARM, O),
            "note": "read out beside S1 and S2 (Amendment 15, E31c); no difference is expected to be detectable in November",
        }
    else:
        result["published_table_arm"] = {"status": "not_registered_in_time"}
    result["february_only_descriptive"] = {
        "note": "registered for the February re-score; in November these are descriptive and license no statement (Amendment 8)",
        "band_coverage": band_coverage(rows, widths),
        "gap_guide": gap_guide(rows),
    }
    return result


def escalations(result: dict) -> list:
    """Results the registrations send to Amir before any writing."""
    out = [
        f"primary contrast {name} failed to replicate (Amendment 8, rule 1)"
        for name, v in result["verdicts"].items()
        if v == "fails"
    ]
    s = result["secondary"]
    for name in SECONDARY:
        if s[name]["reading"] == "below_zero":
            out.append(
                f"{name} is below zero with an interval that excludes zero: the registered "
                "failure sentence goes to Amir before any writing (Amendment 18, rule 5)"
            )
    if s["S2"]["reading"] in ("above_zero", "below_zero"):
        out.append(
            "the interval of S2 excludes zero: the first page goes to Amir before any rewriting (Amendment 13, section 7)"
        )
    if s["S4"]["cross"]["league_aware"]["reading"] == "below_half":
        out.append(
            "S4 is below 50% with an interval that excludes 50% (cross-league ordering): the registered "
            "failure sentence goes to Amir before any writing (Amendment 18, rule 5)"
        )
    arm = result["published_table_arm"]
    if (
        arm["status"] == "read"
        and arm["league_aware_vs_table"]["reading"] == "below_zero"
    ):
        out.append(
            "the published table was more accurate than the league-aware forecast on 2026-27 (Amendment 15)"
        )
    return out


def rule_5_sentences(result: dict) -> list:
    """Amendment 18, rule 5: the read-outs whose registered failure sentence
    the paper must print (S1 or S2 wholly below zero, S4 wholly below 50%).
    Each is also in ``escalations``: it goes to Amir before any writing."""
    s = result["secondary"]
    out = [name for name in SECONDARY if s[name]["reading"] == "below_zero"]
    if s["S4"]["cross"]["league_aware"]["reading"] == "below_half":
        out.append("S4")
    return out


# ---------------------------------------------------------------------------
# 6. Status: scored / not adjudicable / inconclusive. "Pending" is the absence
#    of a score record and is the renderer's state, never written here.


def decide(n_scored: int, n_unscorable: int, audit: dict, estimable: bool):
    """Fail closed. Amendment 18, rule 2: when the test is both unclean (an
    unscorable target, more than 5% possible lost targets, or a data check that
    cannot be repaired) and has fewer than 60 scored newcomers, its state is
    ``inconclusive``: when the newcomers cannot be counted cleanly, their
    number cannot be read either. The record carries both facts."""
    reasons = []
    if n_unscorable:
        reasons.append(
            f"{n_unscorable} joined newcomers have no complete frozen forecast (an unscorable target, 3 Nov registration)"
        )
    if audit["above_threshold"]:
        reasons.append(
            f"{audit['possible_lost_targets']} possible lost targets are {audit['possible_lost_share_of_joined']:.1%} "
            f"of the {audit['joined']} joined newcomers, above the registered {LOST_SHARE_MAX:.0%} (Amendment 8, rule 3)"
        )
    if n_scored >= MIN_SCORED and not estimable:
        reasons.append("a primary interval is not estimable on the scored newcomers")
    if reasons:
        if n_scored < MIN_SCORED:
            reasons.append(
                f"{n_scored} newcomers could be scored, fewer than the {MIN_SCORED} required (Amendment 18, rule 2)"
            )
        return "inconclusive", reasons
    if n_scored < MIN_SCORED:
        return "not_adjudicable", [
            f"{n_scored} newcomers qualify, fewer than the {MIN_SCORED} required (3 Nov registration)"
        ]
    return "scored", []


def descriptive(scored: pd.DataFrame) -> dict:
    """Rule 4: the number of newcomers, their median number of games and the
    mean absolute error of the four primary forecasts. Nothing else."""
    return {
        "n": len(scored),
        "median_games": float(scored.games_dest.median()) if len(scored) else None,
        "mae": {a: common.mae(scored, a) for a in PRIMARY_ARMS}
        if len(scored)
        else None,
        "note": "no contrast, no interval and no secondary read-out is computed (Amendment 8, rule 4)",
    }


def _file_record(path: Path, role: str, frame: pd.DataFrame) -> dict:
    record = {
        "path": str(path),
        "role": role,
        "sha256": sha256_file(Path(path)),
        "rows": len(frame),
    }
    if "_scraped_at" in frame.columns and len(frame):
        first, last = scraped_range(frame, role)
        record.update(refreshed_first=first, refreshed_last=last)
    return record


def score(
    root: Path,
    boxscores,
    schedules,
    people,
    out: Path,
    *,
    unrepairable: tuple | None = None,
    rehearsal: str | None = None,
    clock: dt.date | None = None,
    published_arm_override=None,
) -> dict:
    """One scoring run. ``boxscores``/``schedules``: one path per competition,
    in DESTINATIONS order; ``people``: the API people list(s) for 2026-27.

    ``unrepairable`` = (gate name, reason): a data gate that fails and, in a
    person's judgement, cannot be repaired by refreshing the files. The test is
    then recorded as inconclusive and no contrast is computed. Naming a gate
    that passes is refused.

    ``rehearsal``, ``clock`` and ``published_arm_override`` exist for the
    synthetic rehearsal only; the command line never sets them for ``score``.
    """
    root, out = Path(root), Path(out)
    readings = check_readings(root)  # gate G18c, before anything else
    if rehearsal is None and (clock is not None or published_arm_override is not None):
        raise GateFailure("the clock and the published-arm override are rehearsal-only")
    today = clock if rehearsal is not None else dt.date.today()
    if today < REFRESH_FROM:
        raise GateFailure("P1 may not be scored before 25 Nov 2026", "date")
    if rehearsal is None and (root / SCORE_DIR / "score.json").is_file():
        raise GateFailure(
            f"{SCORE_DIR}/score.json exists: the frozen test is scored once and is not repeated"
        )
    if unrepairable is not None and unrepairable[0] not in DATA_GATES:
        raise GateFailure(f"only a data gate {DATA_GATES} can be declared unrepairable")
    out.mkdir(parents=True, exist_ok=False)
    order = ["readings"]
    base = {
        "analysis": "P1 score",
        "readings": readings,
        "schema": 2,
        "synthetic": rehearsal is not None,
        "rehearsal_scenario": rehearsal,
        "cutoff": CUTOFF,
        "files_refreshed_on_or_after": REFRESH_FROM,
        "scored_on": today,
        "min_n": MIN_SCORED,
        "registrations": [
            "docs/research/sloan-full-paper-preregistration-2026-11-03.md",
            "docs/research/sloan-full-paper-preregistration-amendment-8-2026-11-16.md",
            "docs/research/sloan-full-paper-preregistration-amendment-15-2026-11-17.md",
            AMENDMENT_18.as_posix(),
        ],
    }

    # 1. pinned inputs
    freeze = load_freeze(root)
    committed = load_committed(root)
    band_pin = load_bands(root, committed["anchor_674"])
    arm = load_published_arm(root, freeze["frozen"], override=published_arm_override)
    frozen = freeze["frozen"]
    if arm["status"] == "read":
        frozen = frozen.merge(
            arm.pop("frame"), on=FROZEN_KEY, how="left", validate="1:1"
        )
    base["pinned"] = {
        **freeze["gates"],
        "freeze_record": {
            "path": FREEZE_RECORD.as_posix(),
            "sha256": FREEZE_RECORD_SHA,
        },
        "band_half_widths": band_pin,
        "published_table_arm": arm,
        "committed_2020_2025": committed["sha256"],
    }
    order.append("pinned_inputs")

    # 2. data gates
    try:
        boxes = {
            lg: pd.read_parquet(p)
            for lg, p in zip(DESTINATIONS, boxscores, strict=True)
        }
        scheds = {
            lg: pd.read_parquet(p)
            for lg, p in zip(DESTINATIONS, schedules, strict=True)
        }
        files = [
            *[
                _file_record(p, f"{lg} box scores", boxes[lg])
                for lg, p in zip(DESTINATIONS, boxscores)
            ],
            *[
                _file_record(p, f"{lg} schedule", scheds[lg])
                for lg, p in zip(DESTINATIONS, schedules)
            ],
        ]
        gates = {"season": {lg: gate_season(boxes[lg], lg) for lg in DESTINATIONS}}
        frames = {
            **{f"{lg} box scores": boxes[lg] for lg in DESTINATIONS},
            **{f"{lg} schedule": scheds[lg] for lg in DESTINATIONS},
        }
        gates["freshness"] = gate_freshness(frames)
        gates["schedule"] = {
            lg: gate_schedule(boxes[lg], scheds[lg], lg) for lg in DESTINATIONS
        }
        gates["negative_controls"] = gate_negative_controls(frames, boxes, scheds)
        files += people_records(people)
        people_frame = load_people(people)
        games = pd.concat(
            [destination_games(boxes[lg], scheds[lg], lg) for lg in DESTINATIONS],
            ignore_index=True,
        )
        rows = ledger(frozen, destination_aggregates(games), freeze["incumbency"])
        unjoined, audit = join_audit(rows, frozen, people_frame)
    except GateFailure as failure:
        failed = getattr(failure, "gate", "pinned_input")
        record = {**base, "gate": failed, "message": str(failure)}
        if unrepairable is None or failed not in DATA_GATES:
            write_json(out / "gate-failure.json", record)
            raise
        if unrepairable[0] != failed:
            write_json(out / "gate-failure.json", record)
            raise GateFailure(
                f"the gate that failed is {failed}, not the one declared unrepairable ({unrepairable[0]}): {failure}",
                failed,
            ) from failure
        result = {
            **base,
            "status": "inconclusive",
            "status_reasons": [
                f"the data gate '{failed}' failed and cannot be repaired by refreshing the files: {unrepairable[1]}",
                str(failure),
            ],
            "failed_gate": failed,
            "contrasts_printed": False,
            "order": [*order, "data_gate_failed"],
        }
        write_json(out / "score.json", result)
        print(f"P1 status: inconclusive (data gate {failed})")
        return result
    if unrepairable is not None:
        raise GateFailure(
            f"the gate declared unrepairable ({unrepairable[0]}) passed; nothing is recorded"
        )
    order.append("data_gates")
    base["files"] = files
    base["gates"] = gates
    postponed = [
        g for lg in DESTINATIONS for g in gates["schedule"][lg]["postponed_games"]
    ]
    base["postponed_games"] = {
        "count": len(postponed),
        "games": postponed,
        "rule": "Amendment 18, rule 1: a game dated on or before the cutoff that the schedule marks as not played is postponed; it is listed and counted and does not stop the run",
    }

    # 3. the ledger and the unjoined list are written before anything is read
    scored = rows.loc[rows.reason.eq("scored")].reset_index(drop=True)
    rows.drop(columns=[c for c in common.ALL_ARMS if c in rows.columns]).to_csv(
        out / "p1_newcomer_ledger.csv", index=False
    )
    unjoined.to_csv(out / "p1_unjoined_newcomers.csv", index=False)
    order.append("ledger")

    # 4. pre-read: no outcome column reaches it
    block = pre_read(
        rows.drop(columns=list(OUTCOME_COLUMNS)), audit, committed, arm["status"]
    )
    block["postponed_games"] = len(postponed)
    write_json(out / "pre-read.json", {**base, "pre_read": block})
    print_pre_read(block)
    order.append("pre_read")

    # 5. only now: status and, when licensed, the contrasts
    n_scored, n_unscorable = len(scored), int(rows.reason.eq("forecast_missing").sum())
    result = {
        **base,
        "n_newcomers": int(rows.reason.isin(["scored", "forecast_missing"]).sum()),
        "n_scored": n_scored,
        "n_unscorable": n_unscorable,
        "counts_by_reason": block["counts_by_reason"],
        "join": audit,
        "possible_lost_targets": unjoined.loc[unjoined.possible_lost_target].to_dict(
            "records"
        )
        if len(unjoined)
        else [],
        "pre_read": block,
    }
    estimable = True
    if n_scored >= MIN_SCORED:
        outcome = read_outs(scored, committed, band_pin["half_width_eff36"], arm)
        order.append("contrasts")
        estimable = all(v != "not_estimable" for v in outcome["verdicts"].values())
        result.update(outcome)
        result["contrasts_printed"] = True
    else:
        result["contrasts_printed"] = False
    status, reasons = decide(n_scored, n_unscorable, audit, estimable)
    result["status"], result["status_reasons"] = status, reasons
    if status == "not_adjudicable" or (
        status == "inconclusive" and n_scored < MIN_SCORED
    ):
        result["descriptive"] = descriptive(scored)
    if status == "scored":
        result["escalate_to_amir_before_writing"] = escalations(result)
        result["rule_5_sentences"] = rule_5_sentences(result)
    elif "verdicts" in result:
        # inconclusive: the contrasts are printed with the list, never licensed
        result["verdicts_not_licensed"] = result.pop("verdicts")
        result["escalate_to_amir_before_writing"] = []
    path = out / "p1_scored_rows.parquet"
    scored.to_parquet(path, index=False)
    result["scored_rows"] = {
        "file": path.name,
        "sha256": sha256_file(path),
        "rows": len(scored),
        "columns": list(scored.columns),
        "e32_columns": list(E32_COLUMNS),
    }
    for name in (
        "p1_newcomer_ledger.csv",
        "p1_unjoined_newcomers.csv",
        "pre-read.json",
    ):
        result.setdefault("other_files", {})[name] = sha256_file(out / name)
    result["order"] = order
    write_json(out / "score.json", result)
    print(f"P1 status: {status}; scored n = {n_scored}; reasons: {reasons}")
    for line in result.get("escalate_to_amir_before_writing", []):
        print(f"TO AMIR BEFORE ANY WRITING: {line}")
    return result


# ---------------------------------------------------------------------------
# 7. Rehearsal on made-up outcome files. No 2026-27 statistic is read: the
#    "outcomes" are a frozen forecast plus seeded random noise.

SYNTHETIC_CLOCK = dt.date(2026, 11, 25)
SYNTHETIC_START = dt.date(2026, 9, 30)
SYNTHETIC_ROUND_DAYS = 5
SYNTHETIC_ROUNDS = 13  # twelve dated by 24 Nov, one after it
SYNTHETIC_CLUBS = 20
SYNTHETIC_MINUTES = 20
SYNTHETIC_STAT_COLUMNS = (
    "Points",
    "FieldGoalsMade2",
    "FieldGoalsAttempted2",
    "FieldGoalsMade3",
    "FieldGoalsAttempted3",
    "FreeThrowsMade",
    "FreeThrowsAttempted",
    "OffensiveRebounds",
    "DefensiveRebounds",
    "TotalRebounds",
    "Assistances",
    "Steals",
    "Turnovers",
    "BlocksFavour",
    "BlocksAgainst",
    "FoulsCommited",
    "FoulsReceived",
    "Valuation",
    "Plusminus",
)
#: scenario -> (builder options, expected outcome). An expected outcome is a
#: status, or "gate:<name>" when the run must refuse.
SCENARIOS = {
    "planted_effect": ({"truth": O, "noise_sd": 1.0, "altered": 3}, "scored"),
    "no_effect": ({"truth": "average", "noise_sd": 4.0}, "scored"),
    "coin_flip": ({"truth": "noise", "noise_sd": 4.0}, "scored"),
    "level_high": ({"truth": O, "noise_sd": 1.0, "shift": -1.5}, "scored"),
    "failure": ({"truth": H, "noise_sd": 0.3}, "scored"),
    "ordering_reversed": ({"truth": "reversed", "noise_sd": 1.0}, "scored"),
    "postponed_game": ({"truth": O, "noise_sd": 1.0, "postpone": 2}, "scored"),
    "below_60": ({"truth": O, "noise_sd": 1.0, "n": 41}, "not_adjudicable"),
    "lost_targets": ({"truth": O, "noise_sd": 1.0, "altered": 12}, "inconclusive"),
    "unclean_and_below_60": (
        {"truth": O, "noise_sd": 1.0, "n": 41, "altered": 6},
        "inconclusive",
    ),
    "stale_files": (
        {"truth": O, "noise_sd": 1.0, "scraped_at": "2026-11-20T06:00:00+00:00"},
        "gate:freshness",
    ),
    "missing_box_score": (
        {"truth": O, "noise_sd": 1.0, "drop_box_game": True},
        "gate:completeness",
    ),
    "missing_round": ({"truth": O, "noise_sd": 1.0, "drop_round": 6}, "gate:rounds"),
    "stale_registration_list": (
        {"truth": O, "noise_sd": 1.0, "people_fetched_at": "2026-11-24T20:00:00+00:00"},
        "gate:people_list",
    ),
    "missing_round_unrepairable": (
        {
            "truth": O,
            "noise_sd": 1.0,
            "drop_round": 6,
            "unrepairable": (
                "rounds",
                "rehearsal: the round is declared lost at the source",
            ),
        },
        "inconclusive",
    ),
}


#: What a scenario must show beyond its state. A rehearsal fails if one is absent.
SCENARIO_FACTS = {
    "failure": {"S1": "below_zero", "S2": "below_zero"},
    "ordering_reversed": {"S4": "below_half"},
    "postponed_game": {"postponed_games": 2},
    "planted_effect": {"published_table_arm": "read", "postponed_games": 0},
    "unclean_and_below_60": {"below_minimum": True},
}


def _api_name(key: str) -> str:
    """'AAMIR SIMMS' -> 'SIMMS, AAMIR' (the API's LAST, FIRST form)."""
    words = key.split()
    return f"{words[-1]}, {' '.join(words[:-1])}" if len(words) > 1 else key


def _altered(key: str, how: str) -> str:
    """A lost target: (b) one letter of the surname changed, or (a) another first name."""
    words = key.split()
    if how == "a":
        return f"{words[-1]}, ZYXWVUT"
    last = words[-1]
    last = last[:-1] + ("Q" if last[-1] != "Q" else "X")
    return f"{last}, {' '.join(words[:-1])}"


def synthetic_files(
    frozen: pd.DataFrame,
    incumbency: pd.DataFrame,
    *,
    seed: int = 20261117,
    n: int = 130,
    truth: str = O,
    noise_sd: float = 1.0,
    shift: float = 0.0,
    altered: int = 0,
    rookies: int = 20,
    incumbents: int = 10,
    below_floor: int = 15,
    nonpositive: int = 2,
    scraped_at: str = "2026-11-25T06:00:00+00:00",
    drop_round: int | None = None,
    drop_box_game: bool = False,
    postpone: int = 0,
    people_fetched_at: str = "2026-11-25T07:00:00+00:00",
    **_ignored,
) -> dict:
    """Made-up box scores, schedules and a people list in the API's layout.

    A newcomer's made-up EFF/36 is the frozen forecast named by ``truth`` (or
    the average of the five main forecasts, or, for "noise", a constant that
    ignores every forecast, or, for "reversed", 26 minus the league-aware
    forecast) plus ``shift`` plus normal noise. Every stat line is points only,
    so EFF equals points. ``postpone`` games of the first competition are
    marked not played and lose their box scores (Amendment 18, rule 1).
    """
    rng = np.random.default_rng(seed)
    qualifying = incumbency[
        (incumbency.games >= holdout.MIN_GAMES) & (incumbency.minutes > 0)
    ]
    was_continental = set(qualifying.player_name)
    one = frozen.loc[frozen.league_dest.eq(DESTINATIONS[0])].set_index("player_name")
    fresh = sorted(
        k
        for k in one.index[one.source_positive_finite.astype(bool)]
        if k not in was_continental
    )
    stayed = sorted(k for k in one.index if k in was_continental)
    picks = list(rng.permutation(fresh)[: n + altered + nonpositive + below_floor])
    roles = (
        ["newcomer"] * n
        + ["altered"] * altered
        + ["nonpositive"] * nonpositive
        + ["below_floor"] * below_floor
    )
    players = [{"key": k, "role": r} for k, r in zip(picks, roles, strict=True)]
    players += [
        {"key": k, "role": "incumbent"} for k in rng.permutation(stayed)[:incumbents]
    ]
    players += [
        {"key": f"ZED SYNTHROOKIE{i:03d}", "role": "rookie"} for i in range(rookies)
    ]
    lookup = frozen.set_index(FROZEN_KEY)
    boxes = {league: [] for league in DESTINATIONS}
    people = []
    stamp = scraped_at
    for i, player in enumerate(players):
        league = DESTINATIONS[0] if i % 5 < 2 else DESTINATIONS[1]
        comp = COMPETITION_CODE[league]
        club = i % SYNTHETIC_CLUBS
        key, role = player["key"], player["role"]
        row = lookup.loc[(key, league)] if role != "rookie" else None
        if role == "rookie":
            rate, name, last_team = (
                float(rng.normal(12, 3)),
                _api_name(key),
                "SYNTHETIC ACADEMY",
            )
        else:
            if truth == "noise":
                centre = 13.0
            elif truth == "reversed":
                centre = 26.0 - float(row[O])
            elif truth == "average":
                centre = float(np.mean([row[a] for a in (H, HT, D, O, OT)]))
            else:
                centre = float(row[truth])
            rate = centre + shift + float(rng.normal(0, noise_sd))
            name, last_team = _api_name(key), str(row.club_src)
            if role == "altered":
                name = _altered(key, "a" if i % 2 else "b")
        rate = max(rate, 1.0)
        n_games = 5 if role == "below_floor" else int(rng.integers(8, 13))
        total = int(round(rate * SYNTHETIC_MINUTES * n_games / 36))
        points = [total // n_games + (g < total % n_games) for g in range(n_games)]
        for g in range(SYNTHETIC_ROUNDS):
            if g >= n_games and g != SYNTHETIC_ROUNDS - 1:
                continue
            line = dict.fromkeys(SYNTHETIC_STAT_COLUMNS, 0)
            line["Points"] = points[g] if g < n_games else 40
            if role == "nonpositive":
                line.update(Points=0, Turnovers=2)
            boxes[league].append(
                {
                    "Season": SEASON,
                    "Phase": "RS",
                    "Round": g + 1,
                    "Gamecode": g * (SYNTHETIC_CLUBS // 2)
                    + club % (SYNTHETIC_CLUBS // 2)
                    + 1,
                    "Home": int(club < SYNTHETIC_CLUBS // 2),
                    "Player_ID": f"SYN{i:05d}",
                    "IsStarter": 1,
                    "IsPlaying": 1,
                    "Team": f"S{comp}{club:02d}",
                    "Dorsal": str(i % 99),
                    "Player": name,
                    "Minutes": f"{SYNTHETIC_MINUTES}:00",
                    **line,
                    "_competition": comp,
                    "_scraped_at": stamp,
                }
            )
        people.append(
            {
                "comp": comp,
                "season": str(SEASON),
                "code": f"SYN{i:05d}",
                "name": name,
                "country": "",
                "last_team": last_team,
                "club": f"S{comp}{club:02d}",
                "type": "J",
            }
        )
    schedules = {}
    half = SYNTHETIC_CLUBS // 2
    for league in DESTINATIONS:
        comp = COMPETITION_CODE[league]
        box = pd.DataFrame(boxes[league])
        extra = box.iloc[[0, 1]].assign(Player=["Total", "DNP, SYNTHETIC"])
        extra.loc[extra.index[1], "Minutes"] = "DNP"
        box = pd.concat([box, extra], ignore_index=True)
        games = []
        for g in range(SYNTHETIC_ROUNDS):
            day = SYNTHETIC_START + dt.timedelta(days=SYNTHETIC_ROUND_DAYS * g)
            for k in range(half):
                code = g * half + k + 1
                games.append(
                    {
                        "Phase": "RS",
                        "Round": g + 1,
                        "date": day.strftime("%b %d, %Y"),
                        "time": "20:00",
                        "gameCode": code,
                        "gamecode": f"{comp}{SEASON}_{code}",
                        "group": "",
                        "hometeam": f"SYNTHETIC CLUB {comp}{k:02d}",
                        "homecode": f"S{comp}{k:02d}",
                        "homescore": 80,
                        "awayteam": f"SYNTHETIC CLUB {comp}{k + half:02d}",
                        "awaycode": f"S{comp}{k + half:02d}",
                        "awayscore": 75,
                        "played": True,
                        "_competition": comp,
                        "_scraped_at": stamp,
                    }
                )
        schedule = pd.DataFrame(games)
        schedule = schedule.loc[schedule.gameCode.isin(box.Gamecode)].reset_index(
            drop=True
        )
        if drop_round is not None:
            schedule = schedule.loc[schedule.Round.ne(drop_round)].reset_index(
                drop=True
            )
            box = box.loc[box.Round.ne(drop_round)].reset_index(drop=True)
        if drop_box_game and league == DESTINATIONS[0]:
            box = box.loc[box.Gamecode.ne(int(schedule.gameCode.iloc[0]))].reset_index(
                drop=True
            )
        if postpone and league == DESTINATIONS[0]:
            # games of round 3 onwards, one per round: marked not played, no box score
            victims = [
                int(schedule.loc[schedule.Round.eq(3 + k), "gameCode"].iloc[0])
                for k in range(postpone)
            ]
            schedule.loc[schedule.gameCode.isin(victims), "played"] = False
            box = box.loc[~box.Gamecode.isin(victims)].reset_index(drop=True)
        boxes[league], schedules[league] = box, schedule
    return {
        "boxscores": boxes,
        "schedules": schedules,
        "people": pd.DataFrame(people)[list(PEOPLE_COLUMNS)],
        "people_fetched_at": people_fetched_at,
    }


def write_synthetic(files: dict, folder: Path) -> dict:
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    paths = {
        "boxscores": [],
        "schedules": [],
        "people": [folder / "SYNTHETIC_people.csv"],
    }
    for league in DESTINATIONS:
        for kind in ("boxscores", "schedules"):
            path = folder / f"SYNTHETIC_{league}_{kind}.parquet"
            files[kind][league].to_parquet(path, index=False)
            paths[kind].append(path)
    # the list goes through the committed builder's writer, so the rehearsal
    # reads the layout and the record of the real list (Amendment 18, rule 7)
    people = files["people"]
    registration.write_list(
        people.to_dict("records"),
        paths["people"][0],
        fetched_at=dt.datetime.fromisoformat(files["people_fetched_at"]),
        clubs=people.groupby("comp").club.nunique().to_dict(),
    )
    return paths


def synthetic_published_arm(frozen: pd.DataFrame, folder: Path):
    """A made-up second frozen file: halfway between the destination-only and
    the league-aware forecast. For the rehearsal of E31c only."""
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    arm = frozen[FROZEN_KEY].copy()
    arm[PUBLISHED_ARM] = (frozen[D] + 0.5 * (frozen[O] - frozen[D])).to_numpy()
    path = folder / ("SYNTHETIC_" + PUBLISHED_ARM_FILE.name)
    arm.to_parquet(path, index=False)
    record = folder / ("SYNTHETIC_" + PUBLISHED_ARM_RECORD.name)
    write_json(
        record,
        {
            "arm": PUBLISHED_ARM,
            "forecast_file": path.name,
            "forecast_sha256": sha256_file(path),
            "rows": len(arm),
            "synthetic": True,
        },
    )
    return path, record


def rehearse(root: Path, out: Path, scenarios=None) -> dict:
    """Drive ``score`` through every state on made-up files; fail if a state
    is not the expected one."""
    root, out = Path(root), Path(out)
    check_readings(root)
    out.mkdir(parents=True, exist_ok=False)
    freeze = load_freeze(root)
    summary = []
    for name, (options, expected) in (scenarios or SCENARIOS).items():
        folder = out / name
        files = synthetic_files(freeze["frozen"], freeze["incumbency"], **options)
        paths = write_synthetic(files, folder / "inputs")
        override = (
            synthetic_published_arm(freeze["frozen"], folder / "inputs")
            if options.get("published_arm")
            else None
        )
        row = {
            "scenario": name,
            "expected": expected,
            "options": {k: str(v) for k, v in options.items()},
        }
        try:
            result = score(
                root,
                paths["boxscores"],
                paths["schedules"],
                paths["people"],
                folder / "score",
                unrepairable=options.get("unrepairable"),
                rehearsal=name,
                clock=SYNTHETIC_CLOCK,
                published_arm_override=override,
            )
            row.update(
                got=result["status"],
                status_reasons=result["status_reasons"],
                n_scored=result.get("n_scored"),
                postponed_games=result.get("postponed_games", {}).get("count"),
            )
            for key in (
                "verdicts",
                "verdicts_not_licensed",
                "escalate_to_amir_before_writing",
            ):
                if key in result:
                    row[key] = result[key]
            if result.get("contrasts_printed"):
                row["readings"] = {
                    **{k: result["secondary"][k]["reading"] for k in SECONDARY},
                    "S3": result["secondary"]["S3"][O]["reading"],
                    "S4": result["secondary"]["S4"]["cross"]["league_aware"]["reading"],
                    "published_table_arm": result["published_table_arm"]["status"],
                }
        except GateFailure as failure:
            row.update(got=f"gate:{failure.gate}", message=str(failure))
        seen = {
            **row.get("readings", {}),
            "postponed_games": row.get("postponed_games"),
            "below_minimum": row.get("n_scored") is not None
            and row["n_scored"] < MIN_SCORED,
        }
        row["facts"] = {
            key: {"expected": want, "got": seen.get(key)}
            for key, want in SCENARIO_FACTS.get(name, {}).items()
        }
        row["as_expected"] = row["got"] == expected and all(
            fact["expected"] == fact["got"] for fact in row["facts"].values()
        )
        summary.append(row)
        print(f"rehearsal {name}: expected {expected}, got {row['got']}", flush=True)
    record = {
        "analysis": "P1 scorer rehearsal",
        "synthetic": True,
        "note": "made-up outcome files; no 2026-27 statistic was read",
        "clock": SYNTHETIC_CLOCK,
        "scenarios": summary,
        "all_as_expected": all(r["as_expected"] for r in summary),
    }
    write_json(out / "rehearsal.json", record)
    if not record["all_as_expected"]:
        wrong = [r["scenario"] for r in summary if not r["as_expected"]]
        raise GateFailure(f"rehearsal scenarios not as expected: {wrong}")
    return record


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path, default=ROOT)
    sub = parser.add_subparsers(dest="command", required=True)
    s = sub.add_parser("score", help="the one scoring run, from 25 Nov 2026")
    s.add_argument(
        "--boxscores",
        type=Path,
        nargs=2,
        required=True,
        metavar=("EUROLEAGUE", "EUROCUP"),
    )
    s.add_argument(
        "--schedules",
        type=Path,
        nargs=2,
        required=True,
        metavar=("EUROLEAGUE", "EUROCUP"),
    )
    s.add_argument("--people", type=Path, nargs="+", required=True)
    s.add_argument("--out", type=Path, required=True)
    s.add_argument("--unrepairable-gate", choices=DATA_GATES)
    s.add_argument("--unrepairable-reason")
    b = sub.add_parser(
        "bands", help="compute the band half-widths that are pinned by value"
    )
    b.add_argument("--out", type=Path, required=True)
    r = sub.add_parser("rehearse", help="made-up outcome files through every state")
    r.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "bands":
            bands(args.root, args.out)
        elif args.command == "rehearse":
            rehearse(args.root, args.out)
        else:
            if bool(args.unrepairable_gate) != bool(args.unrepairable_reason):
                parser.error(
                    "--unrepairable-gate and --unrepairable-reason go together"
                )
            unrepairable = (
                (args.unrepairable_gate, args.unrepairable_reason)
                if args.unrepairable_gate
                else None
            )
            score(
                args.root,
                args.boxscores,
                args.schedules,
                args.people,
                args.out,
                unrepairable=unrepairable,
            )
    except GateFailure as failure:
        print(
            f"GATE FAILURE [{getattr(failure, 'gate', 'gate')}]: {failure}",
            file=sys.stderr,
        )
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
