"""Recompute every number in the SSAC 2027 abstract from the published result files.

Run from this folder with Python 3.10+ (standard library only):

    python verify_abstract_numbers.py

Each line prints the value as it appears in the abstract and the unrounded value
behind it. The script exits with an error if any displayed value no longer matches.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
RESULTS = HERE / "results"
POOLS = ("official_corrected", "verified_same_club_full", "overlap_keys_full", "same_club")
PENALTIES = (1, 10, 100)
CLUSTERINGS = ("player_club_season", "player_season")

v9 = json.loads((RESULTS / "v9_diagnostics.json").read_text())
prep = json.loads((RESULTS / "v9_preparation.json").read_text())
v10 = json.loads((RESULTS / "v10_summary.json").read_text())
support = json.loads((RESULTS / "support_restriction_readback.json").read_text())
abstract = (HERE / "paper" / "abstract.md").read_text()

failures = []
checked = []


def show(label, text, value):
    ok = text in abstract
    checked.append(label)
    if not ok:
        failures.append(label)
    print(f"{'OK ' if ok else 'BAD'} {label}: '{text}' (value {value})")


def ref(pool, source="v9"):
    data = v9 if source == "v9" else v10
    return data["variants"][pool]["scenarios"]["reference"]


def fmt(x):
    return f"{x:.3f}".replace("-", "−")


n = v10["target_n"]
dest = v9["variants"]["official_corrected"]["by_destination"]["destination"]
show("forecasts", f"{n} forecasts", n)
show("EuroLeague / EuroCup", f"{dest['euroleague']['n']} EuroLeague and {dest['eurocup']['n']} EuroCup", (dest["euroleague"]["n"], dest["eurocup"]["n"]))

a = ref("official_corrected")
hist = a["contrasts"]["original_vs_history_only"]["player_club_season"]
show("history MAE", f"from {a['metrics']['history_only']['mae']:.3f} to {a['metrics']['scheduled_history']['mae']:.3f}", (a["metrics"]["history_only"]["mae"], a["metrics"]["scheduled_history"]["mae"]))
show("history gain", f"gain {hist['difference']:.3f}, a {100 * hist['difference'] / a['metrics']['history_only']['mae']:.1f}% reduction", hist["difference"])
show("history interval", f"interval {fmt(hist['ci95'][0])} to {fmt(hist['ci95'][1])}", hist["ci95"])
dst = a["contrasts"]["destination_increment"]["player_club_season"]
show("destination gain", f"the gain is {dst['difference']:.3f} ({100 * dst['difference'] / a['metrics']['history_destination_slope']['mae']:.1f}%", dst["difference"])
show("destination interval", f"interval {fmt(dst['ci95'][0])} to {fmt(dst['ci95'][1])}", dst["ci95"])


def source_aware(pool):
    offsets = [ref(pool)["contrasts"][f"source_ridge_{p}_increment"] for p in PENALTIES]
    slopes = [ref(pool, "v10")["contrasts"][f"cell_slope_{p}_increment"] for p in PENALTIES]
    return offsets + slopes


full = source_aware("official_corrected")
full_gains = [c["player_club_season"]["difference"] for c in full]
assert all(c[k]["ci95"][0] <= 0 <= c[k]["ci95"][1] for c in full for k in CLUSTERINGS)
show("full-pool source-aware span", f"span {fmt(min(full_gains))} to {fmt(max(full_gains))}", (min(full_gains), max(full_gains)))

verified = [c for pool in POOLS[1:] for c in source_aware(pool)]
history_verified = [ref(p)["contrasts"]["original_vs_history_only"]["player_club_season"]["difference"] for p in POOLS[1:]]
destination_verified = [ref(p)["contrasts"]["destination_increment"]["player_club_season"]["difference"] for p in POOLS[1:]]
show("verified history gains", f"shrink to {min(history_verified):.3f}–{max(history_verified):.3f}", history_verified)
aware = [c["player_club_season"]["difference"] for c in verified] + destination_verified
assert all(g < 0 for g in aware)
show("verified competition-aware range", f"negative ({fmt(min(aware))} to {fmt(max(aware))})", (min(aware), max(aware)))
adverse = {k: sum(c[k]["ci95"][1] < 0 for c in verified) for k in CLUSTERINGS}
show("adverse player/club-season", f"{adverse['player_club_season']} of {len(verified)} correlated", adverse["player_club_season"])
show("adverse player/season", f"only {adverse['player_season']} player/season", adverse["player_season"])

fallbacks = {p: ref(p)["fallbacks"] for p in POOLS}
show("pairs", f"from {prep['counts']['official_corrected']:,} to {prep['counts']['verified_same_club_full']:,}", (prep["counts"]["official_corrected"], prep["counts"]["verified_same_club_full"]))
show("supported full pool", f"from {n - fallbacks['official_corrected']} of {n} ({100 * (n - fallbacks['official_corrected']) / n:.1f}%)", n - fallbacks["official_corrected"])
show("supported verified pool", f"to {n - fallbacks['verified_same_club_full']} ({100 * (n - fallbacks['verified_same_club_full']) / n:.1f}%; {n - fallbacks['overlap_keys_full']} with overlap trimming", (n - fallbacks["verified_same_club_full"], n - fallbacks["overlap_keys_full"]))
controls = support["controls"]
season = controls["season_count"]["support"]["nonfallback"]
cell = controls["cell_season_count"]["support"]["nonfallback"]
show("restriction medians", f"are {season['median']:.0f} (season-matched) and {cell['median']:.0f} (also league-pair-matched, maximum {cell['maximum']:.0f})", (season["median"], cell["median"], cell["maximum"]))

print()
if failures:
    sys.exit(f"{len(failures)} displayed value(s) do not match: {', '.join(failures)}")
print(f"All {len(checked)} checks match the abstract.")
