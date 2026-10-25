"""D1A/D1B verification for the 7-column layout (with the explicit sum column)."""
from __future__ import annotations

import sys
from pathlib import Path

from docx import Document

D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"
name = sys.argv[1] if len(sys.argv) > 1 else "Paper_EN_v42.docx"
doc = Document(D / name)

for i, tb in enumerate(doc.tables, 1):
    head = [c.text.strip() for c in tb.rows[0].cells]
    if len(head) != 7 or not (head[1].lower().startswith("attempts") or head[1].startswith("尝试")):
        continue
    total = None
    ok = True
    for r in tb.rows[1:]:
        cells = [c.text.strip().replace(",", "") for c in r.cells]
        try:
            att = int(cells[1])
        except ValueError:
            print("  unparsed:", cells)
            ok = False
            continue
        exc, cen, comp = (int(c) for c in cells[2:5])
        sig = int(cells[6])
        flag = "OK" if (exc + cen + comp == att == sig) else "MISMATCH"
        if flag != "OK":
            ok = False
        if cells[0].lower().startswith(("total", "合计")):
            total = att
        print(f"  {cells[0]:8s} {att:6d} = {exc:5d} + {cen:5d} + {comp:4d} = {sig:6d}  {flag}  share {cells[5]}")
    s = sum(int(r.cells[1].text.strip().replace(",", "")) for r in tb.rows[1:]
            if not r.cells[0].text.strip().lower().startswith(("total", "合计")))
    print(f"panel {i}: rows sum {s} vs total {total} -> {'OK' if s == total else 'MISMATCH'}; all rows {ok}")
