#!/usr/bin/env python3
"""Paper-number manifest for the SSAC27 full paper: every number in the rendered
manuscript, mapped to the committed file and key it comes from.

    python scripts/sloan_fullpaper_number_manifest.py build \
        --root . --out docs/paper/ssac27/paper-numbers.json
    python scripts/sloan_fullpaper_number_manifest.py verify \
        --root . --manifest docs/paper/ssac27/paper-numbers.json

How a number is traced (``build``), in order:

1. The renderer's inputs are loaded with the renderer's own loader and wrapped so
   every leaf the renderer reads is recorded.
2. Each read leaf is nudged (relative and additive steps) and the text is
   composed again with ``render_sloan_fullpaper.compose``; the number tokens that
   change depend on that leaf. Leaves holding the same value are also nudged
   together, because the renderer cross-checks copies of one number held in two
   files and refuses to compose when only one copy moves.
3. Lists and tables lose their last row, so a count the renderer derives from a
   table's length is traced to that table.
4. The pre-registered power table (a Markdown table in the protocol) is nudged
   cell by cell.
5. Tokens that are not data (citation numbers, section numbers, units such as
   EFF/36, season labels, the lambda grid, interval levels) are classed as
   literals by their context.
6. A token that is still untraced is matched by value against the read leaves,
   but only when it carries a decimal point or a percent sign and every
   matching leaf holds the same value.

Whatever is left is a number typed into the template or renderer (a protocol
constant such as the 2% margin, or a timestamp); those are listed as
``constant`` and counted as untraced.

``verify`` (run by the public companion's reproduce script) composes the text
again from the files on disk, requires it to equal the rendered manuscript byte
for byte, checks each input file's sha256, re-reads every traced key and requires
the recorded value, and requires every number token in the manuscript to be
listed. Any mismatch is an error.
"""

# ruff: noqa: E501 -- long context strings
from __future__ import annotations

if __name__ == "__main__":
    import sys as _sys
    from pathlib import Path as _Path

    _sys.path.insert(0, str(_Path(__file__).resolve().parents[1]))
    from src.research.execution import enter as _enter

    _enter(__file__)

import argparse
import collections
import difflib
import hashlib
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import render_sloan_fullpaper as rnd  # noqa: E402

MANUSCRIPT = Path("docs/paper/ssac27/rendered/manuscript.md")
NUM = re.compile(
    r"(?<![\w.])[+−-]?\d{1,3}(?:,\d{3})+(?:\.\d+)?%?|(?<![\w.,])[+−-]?\d+(?:\.\d+)?%?(?!\w)"
)
DELTAS = (3e-3, -3e-3, 1e-2, -1e-2, 5e-2, -5e-2, 0.2, -0.2)
ADDITIVE = (2e-3, -2e-3, 2e-2, -2e-2, 0.2, -0.2, 2.0, -2.0)
#: Equal-valued leaves nudged together; larger groups are coincidences (0, 674, ...).
GROUP_MAX = 6


def _rows(d, table, column, where):
    return [
        (table, (i, column))
        for i, row in enumerate(d[table])
        if all(row[k] in v for k, v in where.items())
    ]


#: Amendment 7, "Measured weakness": the renderer computes the share and its Wilson 95% interval
#: from the committed counts and refuses to compose unless they are the registered ones, so a
#: nudged count cannot be rendered; the five numbers are traced through that guard.
_LINK_WEAKNESS = (
    lambda d: [("older", ("gates", "G27d_linking", "measured", "all"))],
    "renderer refuses unless the share and the Wilson 95% interval computed from the committed counts "
    "(9 of 282 links) are the ones Amendment 7 registered: 3.2%, interval 1.7% to 6.0%",
)
#: Numbers typed in the template or renderer that the renderer itself guards
#: against a committed file (it refuses to compose if the guard fails), or that
#: the value match cannot place uniquely. Each rule: token, a context pattern,
#: the guarding keys, and what the guard checks.
GUARDED = (
    (
        "16",
        r"(a|an ACB|for a|of|minus) 16\b|16 EFF/36 in Spain|16 in Spain|Spain's 16\b",
        lambda d: (
            _rows(
                d,
                "exchange",
                "acb16_equivalent_eff36",
                {"source_league": ("spain-acb",)},
            )
            + [("decide", ("e9_reference_player", "source_eff36"))]
        ),
        "reference rate of the equivalents table (decisions generator constant E9_SOURCE_RATE); the ACB rows of the table equal it",
    ),
    (
        "19",
        # (Amendment 32 words the line "gives the same forecast as about 19")
        r"about a 19|as about 19\b",
        lambda d: _rows(
            d,
            "exchange",
            "acb16_equivalent_eff36",
            {"source_league": ("germany-bbl", "lithuania-lkl", "vtb")},
        ),
        "renderer refuses unless every BBL, LKL and VTB equivalent lies in [18.5, 19.5)",
    ),
    (
        "30",
        r"30[- ]feature|30 features",
        lambda d: [("flex", ("n_features_primary",))],
        "renderer refuses unless n_features_primary == 30",
    ),
    (
        "39",
        r"(?i)of (the )?39 registered",
        lambda d: [("licences", ("<rows>",))],
        "number of registered E15a comparisons = rows of e15a_licences.csv",
    ),
    (
        "1,059",
        r"past arrivals \(1,059 here\)|\(1,059 past arrivals",
        lambda d: [("decide", ("e9", "training_forecasts"))],
        "renderer refuses unless the per-league training counts of the equivalents table sum to it",
    ),
    (
        "0",
        r"it wrote 0 files",
        lambda d: [("older", ("runs", "score_stopped", "output_files"))],
        "renderer refuses unless the stopped E27 scoring run wrote no output file",
    ),
    (
        "10",
        r"to within 10⁻⁹\. Outcomes rebuilt",
        lambda d: [("older", ("gates", "G27b_same_models", "tolerance"))],
        "renderer refuses unless the E27 same-models gate's tolerance is 1e-9 and its largest gap is below it",
    ),
    ("3.2%", r"different players in 3\.2% of links", *_LINK_WEAKNESS),
    (
        "9",
        r"links \(9 of 282; interval|measurement: 9 of 282 links",
        *_LINK_WEAKNESS,
    ),
    (
        "282",
        r"links \(9 of 282; interval|measurement: 9 of 282 links",
        *_LINK_WEAKNESS,
    ),
    ("1.7%", r"9 of 282; interval 1\.7% to 6\.0%", *_LINK_WEAKNESS),
    ("6.0%", r"9 of 282; interval 1\.7% to 6\.0%", *_LINK_WEAKNESS),
    # Traced by a joint nudge while few loaded values equal the count; a scored paper loads more
    # values and the joint nudge is then skipped (GROUP_MAX), so the guard names the two keys.
    (
        "6",
        r"gain over history is positive in 6 of 6 seasons",
        lambda d: [
            (
                "robust",
                ("e5", "anchor", "contrasts", "history_gain", "positive_seasons"),
            ),
            ("robust", ("e5", "anchor", "contrasts", "history_gain", "n_seasons")),
        ],
        "renderer refuses unless translation's gain over history is positive in every season (positive_seasons == n_seasons)",
    ),
    (
        "TIER",
        r"^\| \d \| ",
        None,
        "tier column of the equivalents table = e9_tier of that source league's rows",
    ),
    (
        "BIAS",
        r"(Spain \(ACB\)|Italy \(LBA\)) by \d+\.\d\d",
        None,
        "minus the history-only signed error for that league (e11 table), 2 decimals",
    ),
)


#: E32 (Amendments 15, 18 and 20): the tables of named newcomers, present only once the frozen
#: test is scored. Loaded name -> the name ``rnd.optional_inputs`` lists the file under. Without
#: these every cell of the E32 tables would be listed as a number typed in the renderer.
E32_TRACED = {
    "e32_players": "e32_newcomers",
    "e32_pairs": "e32_pairs",
    "e32_summary": "e32_summary",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def published_as(root: Path) -> dict:
    """In the public cut: path -> (sha256 of the committed file, sha256 of the file as published)
    for each file that was changed on the way out of the private repository (REDACTIONS.json of
    the cut). Empty in the private repository, where no such record exists."""
    record = Path(root) / "REDACTIONS.json"
    if not record.is_file():
        return {}
    return {
        path: (f["source_sha256"], f["published_sha256"])
        for path, f in json.loads(record.read_text())["files"].items()
    }


def file_matches(root: Path, path: str, want: str) -> bool:
    """The file is the one whose sha256 is ``want``: byte for byte, or, in the public cut, the
    recorded published form of the committed file with that sha256."""
    got = sha256(Path(root) / path)
    if got == want:
        return True
    source, published = published_as(root).get(str(path), (None, None))
    return source == want and published == got


def source_files(root: Path) -> dict:
    files = {k: str(p) for k, p in rnd.SOURCES.items()}
    files.update({k: str(p) for k, p in rnd.TABLES.items()})
    files.update({k: str(p) for k, p in rnd.TEXTS.items()})
    p1 = rnd.p1_file(root)
    if p1 is not None:
        files["p1"] = str(p1)
    # E30 (Amendment 14) and E31 (Amendment 15): present once their analyses are committed
    files.update({k: str(p) for k, p in rnd.optional_inputs(root).items()})
    # E32: the renderer loads the table of named newcomers under another name
    for loaded, listed in E32_TRACED.items():
        if listed in files:
            files[loaded] = files[listed]
    files["template"] = str(rnd.TEMPLATE)
    return files


def composed(d: dict, template: str) -> tuple[str, list]:
    """The text as the paper prints it: composed, then the appendix tables numbered in order."""
    text, order = rnd.compose(d, template)
    return rnd.printed(text), order


def traced_sources() -> set:
    """The loaded inputs whose leaves are traced: every JSON summary and CSV table."""
    return (
        set(rnd.SOURCES)
        | set(rnd.TABLES)
        | set(rnd.OPTIONAL_SOURCES)
        | set(rnd.OPTIONAL_TABLES)
        | {"p1"}
        | set(E32_TRACED)
    )


def tokens(text: str) -> list:
    out = []
    for ln, line in enumerate(text.split("\n"), 1):
        for m in NUM.finditer(line):
            out.append((ln, m.start(), m.group()))
    return out


def token_changes(a_text: str, b_text: str):
    a_lines, b_lines = a_text.split("\n"), b_text.split("\n")
    if len(a_lines) != len(b_lines):
        return None
    changed = set()
    for ln, (a, b) in enumerate(zip(a_lines, b_lines), 1):
        if a == b:
            continue
        ta = [(m.start(), m.group()) for m in NUM.finditer(a)]
        tb = [(m.start(), m.group()) for m in NUM.finditer(b)]
        sm = difflib.SequenceMatcher(
            a=[x for _, x in ta], b=[x for _, x in tb], autojunk=False
        )
        for op, i1, i2, _, _ in sm.get_opcodes():
            if op != "equal":
                for i in range(i1, i2):
                    changed.add((ln, ta[i][0], ta[i][1]))
    return changed


# ------------------------------------------------------------ access tracing
class _Trace:
    reads: set = set()


class TDict(dict):
    __slots__ = ("_s", "_p")

    def __getitem__(self, k):
        v = super().__getitem__(k)
        if not isinstance(v, (TDict, TList)):
            _Trace.reads.add((self._s, self._p + (k,)))
        else:
            _Trace.reads.add((self._s, self._p + (k, "*")))
        return v

    def get(self, k, default=None):
        return self[k] if k in self else default

    def items(self):
        return [(k, self[k]) for k in super().keys()]

    def values(self):
        return [self[k] for k in super().keys()]

    def __iter__(self):
        return iter(list(super().keys()))


class TList(list):
    __slots__ = ("_s", "_p")

    def __getitem__(self, i):
        v = super().__getitem__(i)
        if isinstance(i, slice):
            for j in range(*i.indices(len(self))):
                self[j]
            return v
        j = i if i >= 0 else len(self) + i
        if not isinstance(v, (TDict, TList)):
            _Trace.reads.add((self._s, self._p + (j,)))
        else:
            _Trace.reads.add((self._s, self._p + (j, "*")))
        return v

    def __iter__(self):
        for i in range(len(self)):
            yield self[i]


def wrap(o, s, p=()):
    if isinstance(o, dict):
        t = TDict()
        t._s, t._p = s, p
        for k, v in o.items():
            dict.__setitem__(t, k, wrap(v, s, p + (k,)))
        return t
    if isinstance(o, list):
        t = TList(wrap(v, s, p + (i,)) for i, v in enumerate(o))
        t._s, t._p = s, p
        return t
    return o


def getv(d: dict, src: str, path):
    node = d[src]
    for k in path:
        node = node[k]
    return node


def setv(d: dict, src: str, path, value) -> None:
    node = d[src]
    for k in path[:-1]:
        node = node[k]
    node[path[-1]] = value


def nudged(v, step: float, additive: bool):
    """A changed copy of a numeric leaf (numbers, or numeric strings from CSV)."""
    if isinstance(v, bool) or v is None:
        return None
    if isinstance(v, str):
        text = v.strip()
        if re.fullmatch(r"-?\d+", text):
            n = int(text)
            return str(
                n + int(round(max(3, abs(n) * abs(step) * 5))) * (1 if step > 0 else -1)
            )
        try:
            x = float(text)
        except ValueError:
            return None
        return repr(x + step if additive else x * (1 + step) + (step if x == 0 else 0))
    if isinstance(v, int):
        return v + int(round(max(3, abs(v) * abs(step) * 5))) * (1 if step > 0 else -1)
    if isinstance(v, float):
        return v + step if additive else v * (1 + step) + (step if v == 0 else 0)
    return None


def as_number(v):
    if isinstance(v, bool) or v is None:
        return None
    if isinstance(v, (int, float)):
        return float(v)
    try:
        return float(str(v))
    except ValueError:
        return None


# ------------------------------------------------------------ literal classes
def literal_kind(lines, sections, ln, col, tok):
    line = lines[ln - 1]
    pre, post = line[:col], line[col + len(tok) :]
    if sections[ln - 1] == "References":
        return "reference list (bibliographic)"
    if line.startswith(("paper_id:", "title:", "track:")) or ln <= 6:
        return "front matter"
    if "$$" in line or re.search(
        r"\\[a-z]+\{|_\{|\^\{", line[max(0, col - 15) : col + 15]
    ):
        return "equation"
    if re.search(r"\[[\d,\s–]*$", pre) and re.match(r"[\d,\s–]*\]", post):
        return "citation number"
    if re.search(r"(Section|Sections|Figure|Table|Appendix|Equation|Fig\.)\s*$", pre):
        return "cross-reference number"
    if col == 0 and re.match(r"^\d+\.\s", line):
        return "list number"
    if re.search(r"(EFF/|per )$", pre):
        return "unit (EFF/36, per 36, per 100)"
    if tok in ("1", "10", "100") and "λ" in line[max(0, col - 40) : col]:
        return "penalty label (lambda grid, pre-registered)"
    # 200x too: the older-seasons test (E27) scores destination seasons 2008-2015
    if re.fullmatch(r"20[012]\d", tok) or (
        re.search(r"20[012]\d–$", pre) and re.fullmatch(r"\d\d|20\d\d", tok)
    ):
        return "season or year label"
    # the same label written with a hyphen in a registered sentence ("2026-27"); an ISO date
    # ("2026-11-17") is not one: the second number must be the next year and end the label
    if (
        (m := re.search(r"(20[012]\d)-$", pre))
        and tok == rnd.display_season(int(m.group(1)))[-2:]
        and not post.startswith("-")
    ):
        return "season or year label"
    if (
        re.search(
            r"\d{1,2} (January|February|March|April|May|June|July|August|September|October|November|December) 20\d\d,? \d\d:$",
            pre + ":",
        )
        or re.fullmatch(r"\d\d", tok)
        and re.search(r"\d\d:$", pre)
        or re.match(r":\d\d UTC", post)
    ):
        return "timestamp (renderer META)"
    if re.match(
        r" (January|February|March|April|May|June|July|August|September|October|November|December) 20\d\d",
        post,
    ):
        return "calendar date (renderer META)"
    if tok == "95%" or (
        tok == "80%"
        and ("power" in post[:12] or "band" in post[:12] or "coverage" in post[:12])
    ):
        return "interval or power level"
    if tok == "3" and re.match(r"-point", post):
        return "label (3-point)"
    # E30 (Amendment 14): the reference value of the registered sentence, and the numbered
    # sensitivities with the labels the scored record gives them
    if tok == "1" and (
        re.match(r" would mean the table's size", post)
        or re.search(r"interval lies (below|above) $", pre)
    ):
        return "reference value of the registered sentence (a slope of 1)"
    if (
        line.startswith("| S-e (")
        and col < [i for i, c in enumerate(line) if c == "|"][2]
    ):
        return "sensitivity number and label (text of the scored record)"
    if re.search(r"Amendments? $|Amendments 1 and $", pre):
        return "amendment number"
    return None


def tier_sources(d: dict, line: str) -> list:
    names = {v: k for k, v in rnd.LEAGUE_NAMES.items()}
    cell = line.split("|")[2].strip()
    code = next(
        (
            c
            for n, c in sorted(names.items(), key=lambda kv: -len(kv[0]))
            if cell.startswith(n)
        ),
        None,
    )
    return _rows(d, "exchange", "e9_tier", {"source_league": (code,)}) if code else []


#: E32 counts printed in sentences and captions. The renderer's ``e32_check`` refuses to compose
#: when one of them is changed, so they cannot be traced by a nudge. Each rule: a pattern whose
#: LAST group is the number, the guarding keys (given the loaded inputs and the match), and
#: what the renderer checks.
E32_COUNTS = (
    (
        r"(?:The first five of the|reverse the order of|There are) (\d[\d,]*) "
        r"(?:pairs of 2026–27 newcomers|such pairs)",
        lambda d, m: [("e32_summary", ("pairs_whose_order_differs",))],
        "renderer refuses unless this count of the E32 summary equals the rows of the committed table of changed pairs",
    ),
    (
        r"of the (\d+) (?:registered|printed) pairs the league-aware order",
        lambda d, m: [("e32_summary", ("pairs_printed",))],
        "renderer refuses unless this count equals the printed rows, the first rows of the committed table of changed pairs",
    ),
    (
        r"(EuroLeague|EuroCup) newcomers of 2026–27 by the frozen league-aware forecast \(E32\): "
        r"(?:all|the ten highest and the ten lowest of) (\d+)\.",
        lambda d, m: _rows(
            d,
            "e32_players",
            "newcomers_in_competition",
            {"league_dest": (m.group(1).lower(),)},
        ),
        "renderer refuses unless a competition has one count of newcomers and the competitions add up to the newcomers scored",
    ),
)
E32_RANK_GUARD = (
    "rank of the newcomer by the frozen league-aware forecast (rank_league_aware of his row); "
    "renderer refuses unless the ranks are the registered ones in the registered order"
)
#: The four rate cells of a row of a table of named newcomers: cell -> column of the table.
E32_ROW_COLUMNS = {
    3: "pir_per36_src",
    4: "history_destination_slope",
    5: "source_ridge_10",
    6: "pir_per36_dest",
}
E32_CELL_GUARD = (
    "this newcomer's value in the committed table of named newcomers, matched within his row; "
    "renderer refuses a change of a forecast that would alter the registered order"
)
E32_PAIR_GUARD = (
    "number of the pair = its row in the committed table of changed pairs, which is ordered by this "
    "gap; renderer refuses unless the printed pairs are the first rows of that table"
)


def e32_rule(tok: str, line: str, col: int, d: dict):
    """The guard for an E32 count, rank or pair number, or None. Only with the E32 tables loaded."""
    players, pairs = d.get("e32_players"), d.get("e32_pairs")
    if not players or pairs is None or d.get("e32_summary") is None:
        return None
    for pattern, keys, guard in E32_COUNTS:
        for m in re.finditer(pattern, line):
            if m.start(m.lastindex) == col and m.group(m.lastindex) == tok:
                return (tok, pattern, lambda d, m=m, keys=keys: keys(d, m), guard)
    if not line.startswith("| "):
        return None
    cells = [c.strip() for c in line.strip().strip("|").split("|")]
    if len(cells) < 3:
        return None
    printed = {r["player_name"] for r in players}
    in_pairs = {r[k] for r in pairs for k in ("player_a", "player_b")}
    competitions = ("EuroLeague", "EuroCup")
    cell = line[:col].count("|") - 1  # which cell of the row the token is in
    if cell == 0 and tok == cells[0]:
        if cells[1] in in_pairs and cells[2] in competitions:
            return _e32_pair(tok, cells[1], pairs)  # the main-text table of pairs
        if cells[1] in competitions and cells[2] in in_pairs:
            return _e32_pair(tok, cells[2], pairs)  # the appendix table of pairs
    if cells[1] not in printed or cells[2] in competitions or len(cells) != 7:
        return None
    # a row of a table of named newcomers: rank, name, source league and four rates
    rows = [
        i
        for i, r in enumerate(players)
        if r["player_name"] == cells[1] and r["rank_league_aware"] == cells[0]
    ]
    if len(rows) != 1:
        return None
    if cell == 0 and tok == cells[0]:
        keys = [("e32_players", (rows[0], "rank_league_aware"))]
        return (tok, "E32 rank", lambda d, keys=keys: keys, E32_RANK_GUARD)
    column = E32_ROW_COLUMNS.get(cell)
    if column and tok == cells[cell] == rnd.num(float(players[rows[0]][column]), 1):
        # reached only when a nudge of this cell was refused (it would have changed the
        # registered order) and the value alone does not name one cell
        keys = [("e32_players", (rows[0], column))]
        return (tok, "E32 cell", lambda d, keys=keys: keys, E32_CELL_GUARD)
    return None


def _e32_pair(tok: str, name: str, pairs: list):
    k = int(tok) - 1
    if not 0 <= k < len(pairs) or name not in (
        pairs[k]["player_a"],
        pairs[k]["player_b"],
    ):
        return None
    return (
        tok,
        "E32 pair",
        lambda d, k=k: [("e32_pairs", (k, "gap_league_aware"))],
        E32_PAIR_GUARD,
    )


def guarded_rule(tok: str, line: str, col: int, d: dict | None = None):
    """The guard rule for a typed number, or None. ``d`` (the loaded inputs) lets a rule check
    that its row is the kind of row it is for; without it the context patterns alone decide."""
    if d is not None and (rule := e32_rule(tok, line, col, d)) is not None:
        return rule
    for rule in GUARDED:
        if rule[0] == "TIER":
            if col == 2 and re.match(rule[1], line) and re.fullmatch(r"\d", tok):
                if d is not None and not tier_sources(d, line):
                    # not a row of the equivalents table (e.g. a rank in an E32 table)
                    continue
                return (
                    tok,
                    rule[1],
                    lambda d, line=line: tier_sources(d, line),
                    rule[3],
                )
            continue
        if rule[0] == "BIAS":
            for m in re.finditer(rule[1], line):
                if m.end() - len(tok) == col:
                    code = (
                        "spain-acb" if m.group(1).startswith("Spain") else "italy-lba"
                    )
                    return (
                        tok,
                        rule[1],
                        lambda d, code=code: _rows(
                            d,
                            "e11",
                            "signed_error_history_only",
                            {"source_league": (code,)},
                        ),
                        rule[3],
                    )
            continue
        if tok != rule[0]:
            continue
        for m in re.finditer(rule[1], line):
            if m.start() <= col < m.end():
                return rule
    return None


def source_entry(base: dict, files: dict, name: str, path, method: str) -> dict:
    entry = {
        "name": name,
        "file": files.get(name, name),
        "key": list(path),
        "method": method,
    }
    if path and path[-1] == "<rows>":
        entry["rows"] = len(getv(base, name, path[:-1]))
    elif name != "prereg":
        entry["value"] = getv(base, name, path)
    return entry


# ------------------------------------------------------------ build
def build(root: Path) -> dict:  # noqa: C901 -- one pass per tracing method, kept together
    root = Path(root)
    files = source_files(root)
    base = rnd.load(root)
    template = (root / rnd.TEMPLATE).read_text()
    text, _ = composed(base, template)
    manuscript = (root / MANUSCRIPT).read_text()
    if text != manuscript:
        raise SystemExit(
            "compose() does not reproduce the committed manuscript; re-render first"
        )
    lines = text.split("\n")
    sections, cur = [], "(front)"
    for line in lines:
        if line.startswith("#"):
            cur = line.strip("# ").strip()
        sections.append(cur)
    toks = tokens(text)

    # 1. trace reads
    wrapped = {k: (wrap(v, k) if k in traced_sources() else v) for k, v in base.items()}
    _Trace.reads = set()
    if composed(wrapped, template)[0] != text:
        raise SystemExit("traced compose differs")
    leaves = sorted({(s, p) for s, p in _Trace.reads if p[-1] != "*"}, key=str)
    containers = sorted({(s, p[:-1]) for s, p in _Trace.reads if p[-1] == "*"}, key=str)
    containers += [(s, ()) for s in sorted({s for s, _ in _Trace.reads})]

    dep = collections.defaultdict(set)  # token -> {(src, path, method)}
    claim_guarded = set()

    def attempt(mutations, label):
        saved = [(s, p, getv(base, s, p)) for s, p, _ in mutations]
        try:
            for s, p, v in mutations:
                setv(base, s, p, v)
            out = composed(base, template)[0]
        except rnd.ClaimError:
            return "claim"
        except Exception:  # noqa: BLE001 -- a nudge that breaks a lookup traces nothing
            return "error"
        finally:
            for s, p, v in saved:
                setv(base, s, p, v)
        return token_changes(text, out)

    # 2a. single leaves
    for s, p in leaves:
        v = getv(base, s, p)
        for additive, steps in ((False, DELTAS), (True, ADDITIVE)):
            for step in steps:
                nv = nudged(v, step, additive)
                if nv is None:
                    break
                res = attempt([(s, p, nv)], "single")
                if res == "claim":
                    claim_guarded.add((s, p))
                elif isinstance(res, set):
                    for tk in res:
                        dep[tk].add((s, p, "nudge"))
    # 2b. equal-valued groups (cross-checked copies)
    groups = collections.defaultdict(list)
    for s, p in leaves:
        x = as_number(getv(base, s, p))
        if x is not None and x == x:
            groups[float(f"{x:.9g}")].append((s, p))
    for members in groups.values():
        if not 2 <= len(members) <= GROUP_MAX:
            continue
        for additive, steps in ((False, DELTAS), (True, ADDITIVE)):
            for step in steps:
                muts = []
                for s, p in members:
                    nv = nudged(getv(base, s, p), step, additive)
                    if nv is None:
                        break
                    muts.append((s, p, nv))
                else:
                    res = attempt(muts, "group")
                    if isinstance(res, set):
                        for tk in res:
                            for s, p in members:
                                dep[tk].add((s, p, "nudge (cross-checked copies)"))
    # 3. table and list lengths
    for s, p in containers:
        node = getv(base, s, p)
        if not isinstance(node, list) or len(node) < 2:
            continue
        removed = node.pop()
        try:
            out = composed(base, template)[0]
            res = token_changes(text, out)
        except Exception:  # noqa: BLE001
            res = None
        finally:
            node.append(removed)
        for tk in res or ():
            dep[tk].add((s, tuple(p) + ("<rows>",), "row count"))
    # 4. the pre-registered power table (Markdown)
    prereg = base["prereg"]
    pattern = re.compile(
        r"^\| (.+?) \| ([0-9.]+) \| ([0-9.]+) \| ([0-9.]+) / ([0-9.]+) \|$"
    )
    for i, line in enumerate(prereg.split("\n")):
        m = pattern.match(line.strip())
        if not m:
            continue
        for g in range(2, 6):
            new_line = line.replace(
                m.group(g), str(round(float(m.group(g)) * 1.37 + 0.011, 3)), 1
            )
            base["prereg"] = prereg.replace(line, new_line, 1)
            try:
                res = token_changes(text, composed(base, template)[0])
            except Exception:  # noqa: BLE001
                res = None
            finally:
                base["prereg"] = prereg
            for tk in res or ():
                dep[tk].add(("prereg", ("power_table", m.group(1), g - 2), "nudge"))
    # 5-6. literals, then guarded value matching
    reads = {}
    for s, p in leaves:
        x = as_number(getv(base, s, p))
        if x is not None and x == x and abs(x) != float("inf"):
            reads[(s, p)] = x
    formats = {}
    for key, x in reads.items():
        for digits in range(4):
            for sign in (False, True):
                formats.setdefault(rnd.num(x, digits, sign=sign), []).append(key)
                formats.setdefault(rnd.num(abs(x), digits, sign=sign), []).append(key)
                formats.setdefault(rnd.pp(x, digits, sign=sign), []).append(key)
            formats.setdefault(rnd.pct(x, digits), []).append(key)
        if float(x).is_integer():
            formats.setdefault(f"{int(x):,}", []).append(key)

    entries = []
    for ln, col, tok in toks:
        e = {
            "line": ln,
            "col": col,
            "token": tok,
            "context": lines[ln - 1][max(0, col - 50) : col + len(tok) + 30],
        }
        if (ln, col, tok) in dep:
            src = sorted(dep[(ln, col, tok)], key=str)
            e["status"] = "traced"
            e["sources"] = [source_entry(base, files, s, p, how) for s, p, how in src]
        elif (rule := guarded_rule(tok, lines[ln - 1], col, base)) is not None:
            e["status"] = "traced"
            e["guard"] = rule[3]
            e["sources"] = [
                source_entry(base, files, s, p, "guarded typed number")
                for s, p in rule[2](base)
            ]
        elif kind := literal_kind(lines, sections, ln, col, tok):
            e["status"], e["kind"] = "literal", kind
        elif (
            ("." in tok or "%" in tok)
            and len(re.sub(r"\D", "", tok)) >= 2
            and not re.search(r"0%?$", tok)
            and tok in formats
        ):
            cands = sorted(set(formats[tok]), key=str)
            if len({float(f"{reads[c]:.9g}") for c in cands}) == 1:
                e["status"] = "traced"
                e["sources"] = [
                    {
                        "name": s,
                        "file": files[s],
                        "key": list(p),
                        "method": "value match",
                        "value": getv(base, s, p),
                    }
                    for s, p in cands
                ]
            else:
                e["status"], e["kind"] = (
                    "constant",
                    "typed in template or renderer (ambiguous value match rejected)",
                )
        else:
            e["status"], e["kind"] = "constant", "typed in template or renderer"
        entries.append(e)
    counts = collections.Counter(e["status"] for e in entries)
    return {
        "manuscript": str(MANUSCRIPT),
        "manuscript_sha256": sha256(root / MANUSCRIPT),
        "files": {
            name: {"path": path, "sha256": sha256(root / path)}
            for name, path in files.items()
        },
        "counts": dict(counts),
        "claim_guarded_leaves": len(claim_guarded),
        "numbers": entries,
    }


# ------------------------------------------------------------ verify
class ManifestMismatch(AssertionError):
    pass


def verify(root: Path, manifest: dict, manuscript_path: Path | None = None) -> dict:
    root = Path(root)
    manuscript_path = Path(manuscript_path or root / manifest["manuscript"])
    problems = []
    if sha256(manuscript_path) != manifest["manuscript_sha256"]:
        problems.append(
            "manuscript sha256 differs from the one in the paper-number manifest (paper-numbers.json)"
        )
    for name, f in manifest["files"].items():
        if not file_matches(root, f["path"], f["sha256"]):
            problems.append(
                f"{f['path']}: sha256 differs from the one in the paper-number manifest (paper-numbers.json)"
            )
    d = rnd.load(root)
    text, _ = composed(d, (root / rnd.TEMPLATE).read_text())
    if text != manuscript_path.read_text():
        problems.append("re-composed manuscript differs from the rendered manuscript")
    lines = text.split("\n")
    listed = {(e["line"], e["col"], e["token"]) for e in manifest["numbers"]}
    found = set(tokens(text))
    if found != listed:
        problems.append(
            f"number tokens differ: {len(found - listed)} unlisted, {len(listed - found)} missing"
        )
    checked = 0
    for e in manifest["numbers"]:
        line = lines[e["line"] - 1] if e["line"] <= len(lines) else ""
        if line[e["col"] : e["col"] + len(e["token"])] != e["token"]:
            problems.append(
                f"line {e['line']}: token {e['token']!r} not at column {e['col']}"
            )
        for s in e.get("sources", []):
            key = tuple(s["key"])
            if s["name"] == "prereg":
                rows = rnd.power_table(d["prereg"])
                if key[1] not in rows:
                    problems.append(f"power-table row missing: {key[1]}")
                continue
            try:
                if key and key[-1] == "<rows>":
                    got = len(getv(d, s["name"], key[:-1]))
                    want = s["rows"]
                else:
                    got, want = getv(d, s["name"], key), s["value"]
            except (KeyError, IndexError, TypeError):
                problems.append(f"{s['file']}: key {list(key)} not found")
                continue
            if got != want:
                problems.append(
                    f"{s['file']}: key {list(key)} = {got!r}, manifest {want!r}"
                )
            checked += 1
    if problems:
        raise ManifestMismatch("\n".join(problems[:40]))
    counts = collections.Counter(e["status"] for e in manifest["numbers"])
    return {"tokens": len(listed), "keys_checked": checked, **counts}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build")
    b.add_argument("--root", type=Path, default=Path("."))
    b.add_argument("--out", type=Path, required=True)
    v = sub.add_parser("verify")
    v.add_argument("--root", type=Path, default=Path("."))
    v.add_argument("--manifest", type=Path, required=True)
    v.add_argument("--manuscript", type=Path)
    args = ap.parse_args(argv)
    if args.cmd == "build":
        m = build(args.root)
        args.out.write_text(
            json.dumps(m, indent=1, ensure_ascii=False, sort_keys=False) + "\n"
        )
        print(json.dumps(m["counts"]))
        return 0
    m = json.loads(args.manifest.read_text())
    print(json.dumps(verify(args.root, m, args.manuscript)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
