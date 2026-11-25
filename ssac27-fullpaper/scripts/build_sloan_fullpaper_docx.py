"""Build the SSAC27 full-paper Word file from the rendered manuscript.

The conference template (scripts/templates/ssac27-word-template.docx, a byte copy of the conference file) is read,
never modified. Its body is replaced by the manuscript, written with the
template's own paragraph formatting: Cambria 11 pt body with 11 pt spacing
after, numbered 16 pt / 12 pt bold headings on the template's numbering list,
unnumbered References and Appendix headings, justified references, and
equations as OMML inside the template's borderless three-column equation
table, numbered with SEQ Eq fields, bookmarked and cross-referenced with REF
fields.

Only the standard library is used. Pandoc is called once to turn the LaTeX
equations into OMML.

Usage:
    python scripts/build_sloan_fullpaper_docx.py --manuscript M.md \
        --template scripts/templates/ssac27-word-template.docx --out paper.docx
"""

# ruff: noqa: E501 -- WordprocessingML strings
from __future__ import annotations

import argparse
import hashlib
import re
import struct
import subprocess
import tempfile
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape

TEXT_WIDTH = 9360  # twips: US Letter 12240 minus 1440 left and right margins
EMU_PER_TWIP = 635
UNNUMBERED = {"Abstract", "References", "Appendix"}

W_FONT = '<w:rFonts w:ascii="Cambria" w:hAnsi="Cambria"/>'
MATH_RPR = (
    '<w:rPr><w:rFonts w:ascii="Cambria Math" w:hAnsi="Cambria Math"/>'
    '<w:sz w:val="22"/><w:szCs w:val="22"/></w:rPr>'
)
TAB = '<w:tabs><w:tab w:val="left" w:pos="2304"/></w:tabs>'


class BuildError(RuntimeError):
    pass


# --------------------------------------------------------------------------- runs


def rpr(size=22, bold=False, italic=False, mono=False, extra=""):
    font = (
        W_FONT  # the template asks for Cambria throughout, so code spans stay Cambria
    )
    return (
        f"<w:rPr>{font}{'<w:b/>' if bold else ''}{'<w:i/>' if italic else ''}{extra}"
        f'<w:sz w:val="{size}"/><w:szCs w:val="{size}"/></w:rPr>'
    )


def run(text, size=22, bold=False, italic=False, mono=False):
    if not text:
        return ""
    return f'<w:r>{rpr(size, bold, italic, mono)}<w:t xml:space="preserve">{escape(text)}</w:t></w:r>'


class Doc:
    """Holds numbering state shared by equations, cross-references and media."""

    def __init__(self, equations: dict[str, str]):
        self.equations = equations  # label -> OMML oMathPara
        self.eq_number: dict[str, int] = {}
        self.bookmark_id = 100
        self.media: list[tuple[str, bytes]] = []  # (part name, data)
        self.image_rels: list[tuple[str, str]] = []  # (rId, target)

    # inline markup: **bold**, *italic*, `code`, (@eq:label)
    def inline(self, text, size=22, bold=False, italic=False):
        out = []
        pattern = re.compile(
            r"(\*\*.+?\*\*|`[^`]+`|\(@eq:[a-z0-9_]+\)|(?<![\w*])\*[^*\s][^*]*?\*(?![\w*]))"
        )
        pos = 0
        for m in pattern.finditer(text):
            out.append(run(text[pos : m.start()], size, bold, italic))
            tok = m.group(0)
            if tok.startswith("**"):
                out.append(self.inline(tok[2:-2], size, True, italic))
            elif tok.startswith("`"):
                out.append(run(tok[1:-1], size - 2, bold, italic, mono=True))
            elif tok.startswith("(@eq:"):
                out.append(self.eq_ref(tok[5:-1], size))
            else:
                out.append(self.inline(tok[1:-1], size, bold, True))
            pos = m.end()
        out.append(run(text[pos:], size, bold, italic))
        return "".join(out)

    def eq_ref(self, label, size=22):
        if label not in self.eq_number:
            raise BuildError(
                f"reference to equation {label!r} before or without its definition"
            )
        n = self.eq_number[label]
        r = rpr(size)
        return (
            run("(", size) + f'<w:r>{r}<w:fldChar w:fldCharType="begin"/></w:r>'
            f'<w:r>{r}<w:instrText xml:space="preserve"> REF eq_{label} \\h  \\* MERGEFORMAT </w:instrText></w:r>'
            f'<w:r>{r}<w:fldChar w:fldCharType="separate"/></w:r>'
            f'<w:r>{r}<w:t>{n}</w:t></w:r><w:r>{r}<w:fldChar w:fldCharType="end"/></w:r>'
            + run(")", size)
        )

    # ----------------------------------------------------------------- blocks

    def para(
        self, inner, size=22, after=220, jc=None, ind="", keep_next=False, before=0
    ):
        jc_xml = f'<w:jc w:val="{jc}"/>' if jc else ""
        sp = (
            f'<w:spacing w:before="{before}" w:after="{after}"/>'
            if before
            else f'<w:spacing w:after="{after}"/>'
        )
        kn = "<w:keepNext/>" if keep_next else ""
        return f"<w:p><w:pPr>{kn}{TAB}{sp}{ind}{jc_xml}{rpr(size)}</w:pPr>{inner}</w:p>"

    def empty(self, size=22, keep_next=False):
        kn = "<w:keepNext/>" if keep_next else ""
        return f"<w:p><w:pPr>{kn}{TAB}{rpr(size)}</w:pPr></w:p>"

    def heading(self, level, text):
        if level == 0:
            size, ind = 32, ""
        else:
            size, ind = 24, f'<w:ind w:left="{450 if level == 1 else 540}"/>'
        if text in UNNUMBERED or level < 0:
            return (
                f"<w:p><w:pPr><w:keepNext/>{TAB}{rpr(32, bold=True)}</w:pPr>"
                f"{run(text, 32, bold=True)}</w:p>"
            )
        num = f'<w:numPr><w:ilvl w:val="{level}"/><w:numId w:val="1"/></w:numPr>'
        return (
            f'<w:p><w:pPr><w:pStyle w:val="ListParagraph"/><w:keepNext/>{num}{TAB}{ind}'
            f"{rpr(size, bold=True)}</w:pPr>{run(text, size, bold=True)}</w:p>"
        )

    def plain_subheading(self, text):
        return (
            f'<w:p><w:pPr><w:keepNext/>{TAB}<w:spacing w:before="120" w:after="120"/>{rpr(24, bold=True)}</w:pPr>'
            f"{run(text, 24, bold=True)}</w:p>"
        )

    def equation(self, label):
        if label in self.eq_number:
            raise BuildError(f"equation label {label!r} defined twice")
        if label not in self.equations:
            raise BuildError(f"no OMML for equation {label!r}")
        n = len(self.eq_number) + 1
        self.eq_number[label] = n
        bid = self.bookmark_id
        self.bookmark_id += 1
        r = rpr(22)
        cell_p = f'<w:pPr>{TAB}<w:spacing w:after="220"/>{{jc}}{r}</w:pPr>'
        none = '<w:{s} w:val="none" w:sz="0" w:space="0" w:color="auto"/>'
        borders = "".join(
            none.format(s=s)
            for s in ("top", "left", "bottom", "right", "insideH", "insideV")
        )
        number = (
            run("(") + f'<w:bookmarkStart w:id="{bid}" w:name="eq_{label}"/>'
            f'<w:r>{r}<w:fldChar w:fldCharType="begin"/></w:r>'
            f'<w:r>{r}<w:instrText xml:space="preserve"> SEQ Eq \\* MERGEFORMAT </w:instrText></w:r>'
            f'<w:r>{r}<w:fldChar w:fldCharType="separate"/></w:r>'
            f"<w:r>{rpr(22, extra='<w:noProof/>')}<w:t>{n}</w:t></w:r>"
            f'<w:r>{r}<w:fldChar w:fldCharType="end"/></w:r>'
            f'<w:bookmarkEnd w:id="{bid}"/>' + run(")")
        )
        return (
            f'<w:tbl><w:tblPr><w:tblStyle w:val="TableGrid"/><w:tblW w:w="0" w:type="auto"/>'
            f'<w:tblBorders>{borders}</w:tblBorders><w:tblLook w:val="04A0" w:firstRow="1" w:lastRow="0" '
            f'w:firstColumn="1" w:lastColumn="0" w:noHBand="0" w:noVBand="1"/></w:tblPr>'
            f'<w:tblGrid><w:gridCol w:w="895"/><w:gridCol w:w="7560"/><w:gridCol w:w="895"/></w:tblGrid>'
            f'<w:tr><w:trPr><w:cantSplit/><w:trHeight w:val="891"/></w:trPr>'
            f'<w:tc><w:tcPr><w:tcW w:w="895" w:type="dxa"/></w:tcPr><w:p>{cell_p.format(jc="")}</w:p></w:tc>'
            f'<w:tc><w:tcPr><w:tcW w:w="7560" w:type="dxa"/><w:vAlign w:val="center"/></w:tcPr>'
            f"<w:p>{cell_p.format(jc=chr(60) + 'w:jc w:val=' + chr(34) + 'center' + chr(34) + '/>')}"
            f"{self.equations[label]}</w:p></w:tc>"
            f'<w:tc><w:tcPr><w:tcW w:w="895" w:type="dxa"/><w:vAlign w:val="center"/></w:tcPr>'
            f"<w:p>{cell_p.format(jc=chr(60) + 'w:jc w:val=' + chr(34) + 'right' + chr(34) + '/>')}{number}</w:p></w:tc>"
            f"</w:tr></w:tbl>"
        )

    def table(self, rows: list[list[str]]):
        header, body = rows[0], rows[1:]
        ncol = len(header)
        if any(len(r) != ncol for r in body):
            raise BuildError(f"ragged table starting {header!r}")
        lengths = [
            max(len(re.sub(r"[*`]", "", r[c])) for r in rows) for c in range(ncol)
        ]
        weights = [max(8, min(n, 46)) for n in lengths]
        if header == [
            "Difference in MAE",
            "Weighting",
            "n",
            "MAE, first forecast",
            "MAE, league-aware",
            "Difference",
            "95% interval",
            "Detectable",
            "Reading",
        ]:
            # Table A16 needs space for signed differences and both interval bounds.
            weights = [15, 12, 5, 9, 10, 12, 16, 12, 9]
        widths = [int(TEXT_WIDTH * w / sum(weights)) for w in weights]
        widths[-1] += TEXT_WIDTH - sum(widths)
        line = '<w:{s} w:val="single" w:sz="{sz}" w:space="0" w:color="000000"/>'
        tbl_borders = (
            line.format(s="top", sz=8)
            + line.format(s="bottom", sz=8)
            + '<w:left w:val="nil"/><w:right w:val="nil"/><w:insideH w:val="nil"/><w:insideV w:val="nil"/>'
        )

        def cell(text, width, bold, first_col, header_row, keep_next=False):
            jc = "left" if first_col else "center"
            kn = "<w:keepNext/>" if keep_next or header_row else ""
            tc_b = (
                f"<w:tcBorders>{line.format(s='bottom', sz=4)}</w:tcBorders>"
                if header_row
                else ""
            )
            return (
                f'<w:tc><w:tcPr><w:tcW w:w="{width}" w:type="dxa"/>{tc_b}<w:vAlign w:val="center"/></w:tcPr>'
                f'<w:p><w:pPr>{kn}<w:spacing w:before="20" w:after="20"/><w:jc w:val="{jc}"/>{rpr(18)}</w:pPr>'
                f"{self.inline(text, 18, bold)}</w:p></w:tc>"
            )

        out = [
            f'<w:tbl><w:tblPr><w:tblW w:w="{TEXT_WIDTH}" w:type="dxa"/><w:tblBorders>{tbl_borders}</w:tblBorders>'
            f'<w:tblLayout w:type="fixed"/><w:tblCellMar><w:left w:w="60" w:type="dxa"/>'
            f'<w:right w:w="60" w:type="dxa"/></w:tblCellMar><w:tblLook w:val="0000"/></w:tblPr><w:tblGrid>'
        ]
        out += [f'<w:gridCol w:w="{w}"/>' for w in widths]
        out.append("</w:tblGrid>")
        out.append(
            "<w:tr><w:trPr><w:cantSplit/><w:tblHeader/></w:trPr>"
            + "".join(
                cell(h, widths[c], True, c == 0, True) for c, h in enumerate(header)
            )
            + "</w:tr>"
        )
        keep_table = len(rows) <= 5 or (len(rows) <= 12 and ncol <= 5)
        for row_index, r in enumerate(body):
            out.append(
                "<w:tr><w:trPr><w:cantSplit/></w:trPr>"
                + "".join(
                    cell(
                        t,
                        widths[c],
                        False,
                        c == 0,
                        False,
                        keep_table and row_index < len(body) - 1,
                    )
                    for c, t in enumerate(r)
                )
                + "</w:tr>"
            )
        out.append("</w:tbl>")
        return "".join(out) + self.para("", after=120)

    def image(self, path: Path, caption: str):
        data = path.read_bytes()
        if data[:8] != b"\x89PNG\r\n\x1a\n":
            raise BuildError(f"{path} is not a PNG")
        w_px, h_px = struct.unpack(">II", data[16:24])
        idx = len(self.media) + 1
        part = f"media/sloan_fig{idx}.png"
        rid = f"rIdFig{idx}"
        self.media.append((part, data))
        self.image_rels.append((rid, part))
        cx = TEXT_WIDTH * EMU_PER_TWIP
        cy = int(cx * h_px / w_px)
        pid = 1000 + idx
        drawing = (
            f'<w:r><w:drawing><wp:inline distT="0" distB="0" distL="0" distR="0">'
            f'<wp:extent cx="{cx}" cy="{cy}"/><wp:docPr id="{pid}" name="Figure {idx}"/>'
            f'<wp:cNvGraphicFramePr><a:graphicFrameLocks xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" noChangeAspect="1"/></wp:cNvGraphicFramePr>'
            f'<a:graphic xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">'
            f'<a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture">'
            f'<pic:pic xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture">'
            f'<pic:nvPicPr><pic:cNvPr id="{pid}" name="sloan_fig{idx}.png"/><pic:cNvPicPr/></pic:nvPicPr>'
            f'<pic:blipFill><a:blip r:embed="{rid}"/><a:stretch><a:fillRect/></a:stretch></pic:blipFill>'
            f'<pic:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="{cx}" cy="{cy}"/></a:xfrm>'
            f'<a:prstGeom prst="rect"><a:avLst/></a:prstGeom></pic:spPr></pic:pic></a:graphicData></a:graphic>'
            f"</wp:inline></w:drawing></w:r>"
        )
        return (
            f'<w:p><w:pPr><w:keepNext/><w:spacing w:before="120" w:after="60"/><w:jc w:val="center"/></w:pPr>{drawing}</w:p>',
            self.caption(caption),
        )

    def caption(self, text):
        m = re.match(r"((?:Table|Figure) [A-Z]?\d+\.)\s*(.*)", text, re.S)
        if not m:
            raise BuildError(f"caption without a Table/Figure label: {text[:40]!r}")
        return run(m.group(1) + " ", 20, bold=True) + self.inline(m.group(2), 20)


# ------------------------------------------------------------------- markdown


def parse_front_matter(text):
    m = re.match(r"---\n(.*?)\n---\n", text, re.S)
    if not m:
        raise BuildError("manuscript has no front matter")
    meta = dict(re.findall(r'^(\w+):\s*"(.*)"\s*$', m.group(1), re.M))
    for key in ("title", "track", "paper_id"):
        if not meta.get(key):
            raise BuildError(f"front matter missing {key}")
    return meta, text[m.end() :]


EQ_RE = re.compile(r"^\$\$(.+?)\$\$\s*\{#eq:([a-z0-9_]+)\}\s*$")
IMG_RE = re.compile(r"^!\[(.+)\]\((.+?\.png)\)\s*$")


def latex_equations(body):
    return [
        (m.group(2), m.group(1))
        for line in body.splitlines()
        if (m := EQ_RE.match(line.strip()))
    ]


def omml_from_pandoc(equations, pandoc="pandoc"):
    """Return {label: <m:oMathPara> xml} using one pandoc conversion."""
    if not equations:
        return {}
    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / "eq.md"
        out = Path(tmp) / "eq.docx"
        src.write_text(
            "\n\n".join(f"$${tex}$$" for _, tex in equations) + "\n", encoding="utf-8"
        )
        subprocess.run([pandoc, str(src), "-o", str(out)], check=True)
        with zipfile.ZipFile(out) as z:
            xml = z.read("word/document.xml").decode("utf-8")
    paras = re.findall(r"<m:oMathPara>.*?</m:oMathPara>", xml, re.S)
    if len(paras) != len(equations):
        raise BuildError(f"pandoc returned {len(paras)} equations for {len(equations)}")

    def size_run(m):
        r = m.group(0)
        if "<w:rPr>" in r:
            return r
        if r.startswith("<m:r><m:rPr>"):
            cut = r.index("</m:rPr>") + len("</m:rPr>")
            return r[:cut] + MATH_RPR + r[cut:]
        return "<m:r>" + MATH_RPR + r[len("<m:r>") :]

    def size_runs(p):
        return re.sub(r"<m:r>.*?</m:r>", size_run, p, flags=re.S)

    return {label: size_runs(p) for (label, _), p in zip(equations, paras)}


def build_body(body, doc: Doc, fig_root: Path):
    blocks = re.split(r"\n\s*\n", body.strip())
    out = []
    in_appendix = in_references = False
    for block in blocks:
        lines = [ln for ln in block.splitlines() if ln.strip()]
        first = lines[0].strip()
        if first.startswith("## "):
            title = first[3:].strip()
            in_appendix = title == "Appendix"
            in_references = title == "References"
            heading = doc.heading(0, title)
            if title in ("References", "Appendix"):
                heading = heading.replace("<w:pPr>", "<w:pPr><w:pageBreakBefore/>", 1)
            out.append(heading)
            out.append(doc.empty(keep_next=True))
            rest = lines[1:]
            if rest:
                raise BuildError(f"text directly under heading {title!r}")
            continue
        if first.startswith("### "):
            title = first[4:].strip()
            out.append(
                doc.plain_subheading(title) if in_appendix else doc.heading(1, title)
            )
            continue
        if first.startswith("#### "):
            out.append(doc.heading(2, first[5:].strip()))
            continue
        if first.startswith("|"):
            rows = [
                [c.strip() for c in ln.strip().strip("|").split("|")] for ln in lines
            ]
            if len(rows) < 3 or not set("".join(rows[1])) <= set("-: "):
                raise BuildError(f"malformed table: {first[:60]!r}")
            out.append(doc.table([rows[0]] + rows[2:]))
            continue
        if (m := EQ_RE.match(first)) and len(lines) == 1:
            out.append(doc.equation(m.group(2)))
            continue
        if (m := IMG_RE.match(first)) and len(lines) == 1:
            path = fig_root / m.group(2)
            if not path.exists():
                raise BuildError(f"figure not found: {path}")
            drawing_p, cap = doc.image(path, m.group(1))
            out.append(drawing_p)
            out.append(doc.para(cap, size=20, after=240))
            continue
        if all(re.match(r"\d+\.\s", ln.strip()) for ln in lines):
            for ln in lines:
                num, text = ln.strip().split(" ", 1)
                out.append(
                    doc.para(
                        run(num + "\t") + doc.inline(text),
                        after=120,
                        ind='<w:ind w:left="720" w:hanging="360"/>',
                    )
                )
            out[-1] = out[-1].replace('w:after="120"', 'w:after="220"', 1)
            continue
        text = " ".join(ln.strip() for ln in lines)
        if in_references:
            if not re.match(r"\[\d+\]\s", text):
                raise BuildError(f"reference without [n]: {text[:40]!r}")
            out.append(
                doc.para(
                    doc.inline(text),
                    jc="both",
                    after=120,
                    ind='<w:keepLines/><w:ind w:left="432" w:hanging="432"/>',
                )
            )
            continue
        if re.match(r"Table [A-Z]?\d+\.", text):
            out.append(doc.para(doc.caption(text), size=20, after=80, keep_next=True))
            continue
        out.append(doc.para(doc.inline(text)))
    return "".join(out)


def front_matter(meta, doc: Doc):
    def centred(text, size, bold=False):
        return f'<w:p><w:pPr>{TAB}<w:jc w:val="center"/>{rpr(size, bold)}</w:pPr>{run(text, size, bold)}</w:p>'

    return (
        centred(meta["title"], 36, True)
        + centred("", 28)
        + centred(meta["track"], 28)
        + centred(meta["paper_id"], 28)
        + f'<w:p><w:pPr>{TAB}<w:jc w:val="both"/>{rpr(22)}</w:pPr></w:p>'
    )


# ---------------------------------------------------------------------- package


def build(manuscript: Path, template: Path, out: Path, pandoc="pandoc") -> dict:
    meta, body = parse_front_matter(manuscript.read_text(encoding="utf-8"))
    doc = Doc(omml_from_pandoc(latex_equations(body), pandoc))
    content = front_matter(meta, doc) + build_body(body, doc, manuscript.parent)
    if unused := set(doc.equations) - set(doc.eq_number):
        raise BuildError(f"equations never placed: {sorted(unused)}")

    with zipfile.ZipFile(template) as zin:
        parts = {name: zin.read(name) for name in zin.namelist()}
    xml = parts["word/document.xml"].decode("utf-8")
    start = xml.index("<w:body>") + len("<w:body>")
    sect = xml.rindex("<w:sectPr")
    xml = xml[:start] + content + xml[sect:]
    if 'xmlns:wp="' not in xml[:3000] or 'xmlns:m="' not in xml[:3000]:
        raise BuildError("template root lacks wp or m namespace")
    parts["word/document.xml"] = xml.encode("utf-8")

    rels = parts["word/_rels/document.xml.rels"].decode("utf-8")
    img_type = (
        "http://schemas.openxmlformats.org/officeDocument/2006/relationships/image"
    )
    new_rels = "".join(
        f'<Relationship Id="{rid}" Type="{img_type}" Target="{tgt}"/>'
        for rid, tgt in doc.image_rels
    )
    # the template's example hyperlink (rId8) is no longer referenced; keeping it is harmless
    parts["word/_rels/document.xml.rels"] = rels.replace(
        "</Relationships>", new_rels + "</Relationships>"
    ).encode()
    for part, data in doc.media:
        parts[f"word/{part}"] = data

    core = parts["docProps/core.xml"].decode("utf-8")
    core = re.sub(
        r"<dc:title>.*?</dc:title>",
        f"<dc:title>{escape(meta['title'])}</dc:title>",
        core,
    )
    core = re.sub(r"<dc:creator>.*?</dc:creator>", "<dc:creator></dc:creator>", core)
    core = re.sub(
        r"<cp:lastModifiedBy>.*?</cp:lastModifiedBy>",
        "<cp:lastModifiedBy></cp:lastModifiedBy>",
        core,
    )
    parts["docProps/core.xml"] = core.encode("utf-8")

    out.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zout:
        order = ["[Content_Types].xml"] + [
            n for n in parts if n != "[Content_Types].xml"
        ]
        for name in order:
            zout.writestr(name, parts[name])
    version = subprocess.run(
        [pandoc, "--version"], capture_output=True, text=True, check=True
    ).stdout.splitlines()[0]
    return {
        "pandoc": version,
        "output": str(out),
        "sha256": hashlib.sha256(out.read_bytes()).hexdigest(),
        "equations": doc.eq_number,
        "figures": len(doc.media),
        "tables": content.count("<w:tblGrid>") - len(doc.eq_number),
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--manuscript", type=Path, required=True)
    ap.add_argument(
        "--template",
        type=Path,
        default=Path("scripts/templates/ssac27-word-template.docx"),
    )
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--pandoc", default="pandoc")
    args = ap.parse_args(argv)
    info = build(args.manuscript, args.template, args.out, args.pandoc)
    print(info)


if __name__ == "__main__":
    main()
