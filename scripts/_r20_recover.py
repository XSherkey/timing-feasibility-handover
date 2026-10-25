"""R20 part 7: restore the Introduction heading, and rebuild the lost appendices A-E from the archived supplement."""
from __future__ import annotations

import re
from pathlib import Path

from docx import Document

D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"
HIST = D / "_history"
SUPP = D / "supplementary" / "supp_en.md"

# ---------------------------------------------------------------- 1. intro heading
p = D / "paper_en.md"
t = p.read_text(encoding="utf-8")
if "## I. Introduction" not in t:
    anchor = "Low-earth-orbit constellations hand over several times an hour"
    i = t.find(anchor)
    t = t[:i] + "## I. Introduction\n\n" + t[i:]
    p.write_text(t, encoding="utf-8")
    print("Introduction heading restored")

# ---------------------------------------------------------------- 2. recover A-E
arch = sorted(HIST.glob("supp_en_*.docx"))
if not arch:
    raise SystemExit("no archived supplement")
doc = Document(str(arch[-1]))
print("recovering from", arch[-1].name)

# walk the body in order, rendering paragraphs and tables as markdown
from docx.table import Table
from docx.text.paragraph import Paragraph


def iter_block_items(parent):
    body = parent.element.body
    for child in body.iterchildren():
        if child.tag.endswith("}p"):
            yield Paragraph(child, parent)
        elif child.tag.endswith("}tbl"):
            yield Table(child, parent)


out = []
for block in iter_block_items(doc):
    if isinstance(block, Paragraph):
        txt = block.text.strip()
        if not txt:
            continue
        style = block.style.name if block.style is not None else ""
        if style.startswith("Heading 1"):
            out.append("\n## " + txt + "\n")
        elif style.startswith("Heading 2"):
            out.append("\n### " + txt + "\n")
        else:
            out.append(txt + "\n")
    else:
        rows = []
        for r in block.rows:
            cells = [c.text.strip().replace("\n", " ") for c in r.cells]
            rows.append("| " + " | ".join(cells) + " |")
        if rows:
            head = rows[0]
            ncol = head.count("|") - 1
            rows.insert(1, "|" + "---|" * ncol)
            out.append("\n" + "\n".join(rows) + "\n")

recovered = "\n".join(out)
print("recovered chars:", len(recovered))
print("headings:", re.findall(r"^## .*", recovered, flags=re.M))

s = SUPP.read_text(encoding="utf-8")
s = s.replace("## I. Introduction\n", "")
SUPP.write_text(recovered.strip() + "\n\n" + s.strip() + "\n", encoding="utf-8")
print("supplement rebuilt, chars:", len(SUPP.read_text(encoding='utf-8')))
