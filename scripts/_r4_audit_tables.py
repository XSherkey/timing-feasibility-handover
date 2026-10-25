"""Audit the built document: every table in order, with the caption paragraph that precedes it."""
from __future__ import annotations

from pathlib import Path

from docx import Document
from docx.table import Table
from docx.text.paragraph import Paragraph

D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"
doc = Document(D / "Paper_EN_v15.docx")

last_paras: list[str] = []
n = 0
for child in doc.element.body.iterchildren():
    tag = child.tag.split("}")[-1]
    if tag == "p":
        p = Paragraph(child, doc)
        txt = p.text.strip()
        if txt:
            last_paras.append(txt)
            last_paras = last_paras[-3:]
    elif tag == "tbl":
        n += 1
        tb = Table(child, doc)
        cap = next((x for x in reversed(last_paras) if x.startswith(("Table", "表"))), "(no caption)")
        print(f"T{n:02d} {len(tb.rows)}x{len(tb.columns)} | {cap[:95]}")
        last_paras = []
print("total tables:", n)
