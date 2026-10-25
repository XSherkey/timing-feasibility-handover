"""Audit a built docx: table order + arithmetic of the D1A/D1B panels."""
from __future__ import annotations

import re
import sys
from pathlib import Path

from docx import Document
from docx.table import Table
from docx.text.paragraph import Paragraph

D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"
name = sys.argv[1] if len(sys.argv) > 1 else "Paper_EN_v16.docx"
doc = Document(D / name)

last: list[str] = []
n = 0
print("=" * 78)
print(name)
for child in doc.element.body.iterchildren():
    tag = child.tag.split("}")[-1]
    if tag == "p":
        txt = Paragraph(child, doc).text.strip()
        if txt:
            last.append(txt)
            last = last[-3:]
    elif tag == "tbl":
        n += 1
        tb = Table(child, doc)
        cap = next((x for x in reversed(last) if x.startswith(("Table", "表"))), "(no caption)")
        print(f"T{n:02d} {len(tb.rows)}x{len(tb.columns)} | {cap[:88]}")
        last = []
print("total tables:", n)

print("\n--- D1 panels: arithmetic check ---")
for i, tb in enumerate(doc.tables, 1):
    head = [c.text.strip() for c in tb.rows[0].cells]
    if len(head) != 6 or not ("attempts" in head[1].lower() or "尝试" in head[1]):
        continue
    print(f"panel {i}: {head}")
    total = None
    rows = []
    for r in tb.rows[1:]:
        cells = [c.text.strip().replace(",", "") for c in r.cells]
        if cells[0].lower().startswith(("total", "合计")):
            total = int(cells[1])
            continue
        try:
            rows.append((cells[0], int(cells[1]), int(cells[2]), int(cells[3]), int(cells[4]), cells[5]))
        except ValueError:
            print("   unparseable row:", cells)
    s = sum(x[1] for x in rows)
    ok_sum = (total == s)
    print(f"   rows sum = {s} | declared total = {total} | {'OK' if ok_sum else 'MISMATCH'}")
    for label, att, ex, ce, co, share in rows:
        good = (att == ex + ce + co)
        pct = float(share.rstrip('%')) / 100 if share.rstrip('%').replace('.', '', 1).replace('%', '').isdigit() or True else 0
        calc = att / s if s else 0
        print(f"   {label:>7} attempts {att:5d} = {ex:5d}+{ce:5d}+{co:5d} {'OK' if good else 'BAD'}"
              f" | share {share} vs {100*calc:.1f}%")
