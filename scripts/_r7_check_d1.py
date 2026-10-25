"""D1A/D1B verification for the 4-column layout (bucket | attempts | a+b+c=attempts | share)."""
from __future__ import annotations

import re
import sys
from pathlib import Path

from docx import Document

D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"
name = sys.argv[1] if len(sys.argv) > 1 else "Paper_EN_v50.docx"
doc = Document(D / name)
pat = re.compile(r"([\d,]+)\s*\+\s*([\d,]+)\s*\+\s*([\d,]+)\s*=\s*([\d,]+)")

for i, tb in enumerate(doc.tables, 1):
    head = [c.text.strip() for c in tb.rows[0].cells]
    if len(head) != 4 or "=" not in head[2]:
        continue
    total, s, bad = None, 0, 0
    for r in tb.rows[1:]:
        cells = [c.text.strip() for c in r.cells]
        m = pat.search(cells[2].replace("\u00a0", " "))
        if not m:
            print("  cannot parse:", cells)
            bad += 1
            continue
        a, b, c_, t = (int(x.replace(",", "")) for x in m.groups())
        att = int(cells[1].replace(",", ""))
        ok = (a + b + c_ == t == att)
        if not ok:
            bad += 1
        if cells[0].lower().startswith(("total", "合计")):
            total = att
        else:
            s += att
        print(f"  {cells[0]:10s} {att:6d}  {a}+{b}+{c_}={t}  {'OK' if ok else 'MISMATCH'}  share {cells[3]}")
    print(f"panel {i}: rows sum {s:,} vs total {total:,} -> {'OK' if s == total else 'MISMATCH'}; bad rows {bad}")
