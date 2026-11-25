#!/usr/bin/env python3
"""Build the static converter page of the public companion (no number is typed).

    python scripts/sloan_fullpaper_converter_page.py --out converter/index.html

The page holds three things a club analyst can use without running any code:
the fitted equation of the league-aware forecast, the ten league numbers (the
European League Equivalents), and the guide to how far a gap between two
forecasts can be trusted. Every number on the page is read, when the page is
built, from three committed result files:

* the equation's coefficients: ``e9/coefficients`` in the decisions summary
  (the model behind the frozen 2026-27 forecasts; Amendment 12, gate G30a);
* the equivalents: ``exchange_rate_acb16.csv`` (Amendment 1);
* the gap guide: ``e20`` in the Amendment 3 summary.

The page is one self-contained HTML file: no network request, no library. Its
small calculator applies the same equation in the reader's browser.
"""

# ruff: noqa: E501 -- page text
from __future__ import annotations

import argparse
import hashlib
import html
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
ART = "docs/research/artifacts"
COEFFICIENTS = f"{ART}/sloan-fullpaper-decisions-2026-11-03/summary.json"
EQUIVALENTS = f"{ART}/sloan-fullpaper-amend1-decisions-2026-11/exchange_rate_acb16.csv"
GAP_GUIDE = f"{ART}/sloan-fullpaper-amend3-2026-11/summary.json"
SOURCES = (COEFFICIENTS, EQUIVALENTS, GAP_GUIDE)
ARM = "source_ridge_10"
OFFSET = "source_offset:"
TERMS = (
    "intercept",
    "source_rate",
    "prior_rate",
    "above_prior",
    "destination_euroleague",
    "destination_x_source",
)
#: Display names (text only). Turkey and Israel are never both called "BSL".
LEAGUES = {
    "aba-league": "Adriatic league (ABA)",
    "france-pro-a": "France (Pro A)",
    "germany-bbl": "Germany (BBL)",
    "greece-a1": "Greece (A1)",
    "israel-bsl": "Israel (Premier League)",
    "italy-lba": "Italy (LBA)",
    "lithuania-lkl": "Lithuania (LKL)",
    "spain-acb": "Spain (ACB)",
    "turkey-bsl": "Turkey (BSL)",
    "vtb": "VTB United League",
}
DESTINATIONS = {"euroleague": "EuroLeague", "eurocup": "EuroCup"}
REFERENCE = "spain-acb"


def sha256(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load(root: Path) -> dict:
    root = Path(root)
    co = json.loads((root / COEFFICIENTS).read_text())["e9"]["coefficients"]
    leagues = sorted(k[len(OFFSET) :] for k in co if k.startswith(OFFSET))
    if set(leagues) != set(LEAGUES) or not set(TERMS) <= set(co):
        raise ValueError(
            "the committed coefficients are not the ten-league model this page prints"
        )
    exchange = pd.read_csv(root / EQUIVALENTS)
    if set(exchange.source_league) != set(LEAGUES) or set(exchange.destination) != set(
        DESTINATIONS
    ):
        raise ValueError(
            "the committed equivalents do not cover ten leagues and two destinations"
        )
    reference = exchange.loc[
        exchange.source_league.eq(REFERENCE), "acb16_equivalent_eff36"
    ]
    e20 = json.loads((root / GAP_GUIDE).read_text())["e20"]
    bins = sorted(
        (r for r in e20["bins"] if r["arm"] == ARM),
        key=lambda r: (r["pair_type"], r["bin"]),
    )
    return {
        "coefficients": {k: float(v) for k, v in co.items()},
        "leagues": leagues,
        "reference_rate": float(reference.iloc[0]),
        "equivalents": [
            {
                "destination": r.destination,
                "league": r.source_league,
                "equivalent": float(r.acb16_equivalent_eff36),
                "low": float(r.ci95_low),
                "high": float(r.ci95_high),
                "tier": int(r.e9_tier),
                "training_forecasts": int(r.training_forecasts),
            }
            for r in exchange.itertuples()
        ],
        "how_to_read": str(exchange.how_to_read.iloc[0]),
        "bins": [
            {
                k: r[k]
                for k in (
                    "pair_type",
                    "bin",
                    "gap_eff36",
                    "gap_low",
                    "gap_high",
                    "pairs",
                    "share_correct",
                    "ci95_low",
                    "ci95_high",
                )
            }
            for r in bins
        ],
        "trust": [
            t["sentence"] for t in e20["licence"]["trust"].values() if t["licensed"]
        ],
        "sources": {rel: sha256(root / rel) for rel in SOURCES},
    }


def forecast(
    co: dict, x: float, h: float | None, league: str, euroleague: bool
) -> float:
    """The fitted equation. ``h`` is the career rate; a player with no earlier season has h = x."""
    h = x if h is None else h
    out = (
        co["intercept"]
        + co["source_rate"] * x
        + co["prior_rate"] * h
        + co[OFFSET + league]
    )
    if x > h:
        out += co["above_prior"]
    if euroleague:
        out += co["destination_euroleague"] + co["destination_x_source"] * x
    return out


def equivalent(co: dict, league: str, euroleague: bool, rate: float) -> float:
    """The domestic rate (career rate equal to it) that forecasts like ``rate`` in the reference league."""
    target = forecast(co, rate, rate, REFERENCE, euroleague)
    at0, at1 = (
        forecast(co, 0.0, 0.0, league, euroleague),
        forecast(co, 1.0, 1.0, league, euroleague),
    )
    return (target - at0) / (at1 - at0)


def gap_bin(bins: list, gap: float) -> dict:
    rows = [r for r in bins if r["pair_type"] == "all"]
    return max(
        (r for r in rows if abs(gap) >= r["gap_low"]), key=lambda r: r["gap_low"]
    )


def f(value: float, digits: int = 3, signed: bool = False) -> str:
    text = f"{value:+.{digits}f}" if signed else f"{value:.{digits}f}"
    return text.replace("-", "−")


def pct(value: float) -> str:
    return f"{100 * value:.1f}%"


def _table(header: list, rows: list) -> str:
    head = "".join(f"<th>{html.escape(str(c))}</th>" for c in header)
    body = "".join(
        "<tr>" + "".join(f"<td>{html.escape(str(c))}</td>" for c in row) + "</tr>"
        for row in rows
    )
    return f"<table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>"


def check_rows(data: dict) -> list:
    """Worked values, computed here, so a reader can check the calculator."""
    co, rate = data["coefficients"], data["reference_rate"]
    cases = [
        (lg, rate, None, dest)
        for lg in ("spain-acb", "germany-bbl", "lithuania-lkl")
        for dest in DESTINATIONS
    ]
    return [
        [
            LEAGUES[lg],
            f(x, 1),
            "same as last season",
            DESTINATIONS[dest],
            f(forecast(co, x, h, lg, dest == "euroleague"), 2),
        ]
        for lg, x, h, dest in cases
    ]


SCRIPT = """
const DATA = JSON.parse(document.getElementById('data').textContent);
function forecast(x, h, league, euroleague) {
  const c = DATA.coefficients;
  if (h === null || Number.isNaN(h)) { h = x; }
  let out = c['intercept'] + c['source_rate'] * x + c['prior_rate'] * h + c['source_offset:' + league];
  if (x > h) { out += c['above_prior']; }
  if (euroleague) { out += c['destination_euroleague'] + c['destination_x_source'] * x; }
  return out;
}
function gapBin(gap) {
  const rows = DATA.bins.filter(r => r.pair_type === 'all' && Math.abs(gap) >= r.gap_low);
  return rows.reduce((a, b) => (b.gap_low > a.gap_low ? b : a));
}
function read(id) { const v = document.getElementById(id).value; return v === '' ? null : parseFloat(v); }
function update() {
  const el = document.getElementById('dest').value === 'euroleague';
  const out = [];
  for (const who of ['a', 'b']) {
    const x = read('x_' + who);
    if (x === null || Number.isNaN(x)) { out.push(null); document.getElementById('f_' + who).textContent = 'enter a rate'; continue; }
    const value = forecast(x, read('h_' + who), document.getElementById('lg_' + who).value, el);
    out.push(value);
    document.getElementById('f_' + who).textContent = value.toFixed(1) + ' EFF/36';
  }
  const note = document.getElementById('gap');
  if (out[0] === null || out[1] === null) { note.textContent = 'Enter both candidates to compare them.'; return; }
  const gap = out[0] - out[1];
  const row = gapBin(gap);
  const first = gap >= 0 ? 'A' : 'B';
  note.textContent = 'The forecast puts candidate ' + first + ' ahead by ' + Math.abs(gap).toFixed(1) +
    ' EFF/36. Among past pairs whose forecasts differed by ' + row.gap_eff36 + ' EFF/36, the player with the higher forecast turned out better in ' +
    (100 * row.share_correct).toFixed(1) + '% of pairs (interval ' + (100 * row.ci95_low).toFixed(1) + '% to ' + (100 * row.ci95_high).toFixed(1) + '%).';
}
document.querySelectorAll('input, select').forEach(e => e.addEventListener('input', update));
update();
"""

STYLE = """
body { font-family: Georgia, 'Times New Roman', serif; max-width: 52rem; margin: 2rem auto; padding: 0 1rem; line-height: 1.5; color: #111; }
h1 { font-size: 1.6rem; } h2 { font-size: 1.2rem; margin-top: 2rem; }
table { border-collapse: collapse; margin: 0.8rem 0; font-size: 0.92rem; }
th, td { border: 1px solid #999; padding: 0.25rem 0.55rem; text-align: left; }
th { background: #eee; }
.eq { font-family: 'Courier New', monospace; background: #f6f6f6; padding: 0.6rem; overflow-x: auto; }
.calc label { display: inline-block; margin: 0.2rem 0.8rem 0.2rem 0; }
.calc input { width: 5rem; } .out { font-weight: bold; }
.small { font-size: 0.85rem; color: #333; }
"""


def build(root: Path = ROOT) -> str:
    data = load(root)
    co = data["coefficients"]
    options = "".join(
        f'<option value="{k}">{html.escape(v)}</option>' for k, v in LEAGUES.items()
    )

    def candidate(who: str) -> str:
        return (
            f"<p><strong>Candidate {who.upper()}</strong> "
            f'<label>league <select id="lg_{who}">{options}</select></label>'
            f'<label>last season, EFF/36 <input id="x_{who}" type="number" step="0.1"></label>'
            f'<label>career rate before it (leave empty if none) <input id="h_{who}" type="number" step="0.1"></label>'
            f'forecast: <span class="out" id="f_{who}"></span></p>'
        )

    by = {(r["destination"], r["league"]): r for r in data["equivalents"]}
    order = sorted(LEAGUES, key=lambda k: by[("euroleague", k)]["equivalent"])
    league_rows = [
        [
            LEAGUES[k],
            f(co[OFFSET + k], 2, signed=True),
            *[
                f"{f(by[(d, k)]['equivalent'], 1)} ({f(by[(d, k)]['low'], 1)} to {f(by[(d, k)]['high'], 1)})"
                for d in DESTINATIONS
            ],
            by[("euroleague", k)]["tier"],
        ]
        for k in order
    ]
    cross = {r["bin"]: r for r in data["bins"] if r["pair_type"] == "cross"}
    gap_rows = [
        [
            r["gap_eff36"],
            f"{r['pairs']:,}",
            f"{pct(r['share_correct'])} ({pct(r['ci95_low'])} to {pct(r['ci95_high'])})",
            pct(cross[r["bin"]]["share_correct"]),
        ]
        for r in data["bins"]
        if r["pair_type"] == "all"
    ]
    total = sum(r["pairs"] for r in data["bins"] if r["pair_type"] == "all")
    rate = f(data["reference_rate"], 0)
    parts = [
        "<!doctype html>",
        '<html lang="en"><head><meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        "<title>European League Equivalents: converter</title>",
        f"<style>{STYLE}</style></head><body>",
        "<h1>European League Equivalents: converter</h1>",
        "<p>Companion to Paper ID 47, MIT Sloan Sports Analytics Conference 2027. This page puts a domestic season in one of ten European leagues on one scale, and forecasts a first season in the EuroLeague or the EuroCup. Every number on it is read from the paper's committed result files when the page is built. None is typed.</p>",
        "<h2>1. The forecast, as one equation</h2>",
        "<p>EFF/36 is the efficiency rating per 36 minutes. <em>x</em> is last season's domestic EFF/36, in the league where the player had the most minutes. <em>h</em> is his career rate before that season: all earlier games on record taken together. A player with no earlier season has <em>h</em> = <em>x</em>.</p>",
        '<p class="eq">forecast = '
        + f"{f(co['intercept'])} + {f(co['source_rate'])}·x + {f(co['prior_rate'])}·h + league number"
        + f"<br>&nbsp;&nbsp;{f(co['above_prior'], signed=True)} if x is above h"
        + f"<br>&nbsp;&nbsp;{f(co['destination_euroleague'], signed=True)} {f(co['destination_x_source'], signed=True)}·x if the destination is the EuroLeague</p>",
        "<p>The league number is the second column of the table in section 2. The calculator below uses the coefficients at full precision.</p>",
        '<div class="calc">',
        f'<p><label>Destination <select id="dest">{"".join(f"<option value={k!r}>{v}</option>" for k, v in DESTINATIONS.items())}</select></label></p>',
        candidate("a"),
        candidate("b"),
        '<p id="gap"></p></div>',
        "<p>Values to check the calculator against (computed when the page was built):</p>",
        _table(
            [
                "League",
                "Last season, EFF/36",
                "Career rate",
                "Destination",
                "Forecast, EFF/36",
            ],
            check_rows(data),
        ),
        "<h2>2. The ten league numbers</h2>",
        f"<p>The league number is added to the forecast. The equivalent is the domestic EFF/36 in that league that forecasts like a {rate} in Spain's ACB, for a player whose career history matches his domestic line. Intervals are 95%. Leagues inside a tier are not distinguishable.</p>",
        _table(
            [
                "League",
                "League number, EFF/36",
                *[f"Equivalent of {rate} in Spain, {v}" for v in DESTINATIONS.values()],
                "Tier",
            ],
            league_rows,
        ),
        f'<p class="small">{html.escape(data["how_to_read"])}</p>',
        "<h2>3. How far to trust a gap between two forecasts</h2>",
        f"<p>Over every pair of arrivals in the same competition and season ({total:,} pairs), the share in which the player with the higher forecast had the higher realised EFF/36, by the size of the gap between the two forecasts.</p>",
        _table(
            [
                "Gap between the two forecasts, EFF/36",
                "Pairs",
                "Higher forecast turned out better (95% interval)",
                "The same, pairs from different leagues",
            ],
            gap_rows,
        ),
        "".join(f"<p>{html.escape(s)}</p>" for s in data["trust"]),
        "<p>This is not the isolated benefit of the league adjustment: the gap also includes player history and destination. It describes the arrivals the paper scores.</p>",
        "<h2>Where the numbers come from</h2>",
        _table(
            ["File", "sha256"],
            [[rel, digest] for rel, digest in data["sources"].items()],
        ),
        '<p class="small">Built by <code>scripts/sloan_fullpaper_converter_page.py</code>. The page makes no network request.</p>',
        f'<script type="application/json" id="data">{json.dumps(data, sort_keys=True)}</script>',
        f"<script>{SCRIPT}</script>",
        "</body></html>",
    ]
    return "\n".join(parts) + "\n"


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(build(ROOT))
    print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
