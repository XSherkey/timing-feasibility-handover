"""D1A/D1B arithmetic check straight from the built docx (robust version)."""
from __future__ import annotations

import sys
from pathlib import Path

from docx import Document

D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"
name = sys.argv[1] if len(sys.argv) > 1 else "Paper_EN_v17.docx"
doc = Document(D / name)

for i, tb in enumerate(doc.tables, 1):
    head = [c.text.strip() for c in tb.rows[0].cells]
    if len(head) != 6 or not ("attempts" in head[1].lower() or "尝试" in head[1]):
        continue
    rows, total = [], None
    for r in tb.rows[1:]:
        cells = [c.text.strip().replace(",", "") for c in r.cells]
        if cells[0].lower().startswith(("total", "合计")):
            total = int(cells[1])
            continue
        try:
            rows.append((cells[0], int(cells[1]), int(cells[2]), int(cells[3]), int(cells[4]), cells[5]))
        except ValueError:
            print("  unparsed row:", cells)
    s = sum(x[1] for x in rows)
    print(f"panel {i}: rows={len(rows)} sum={s} total={total} {'OK' if total == s else 'MISMATCH'}")
    for label, att, ex, ce, co, share in rows:
        calc = 100.0 * att / s
        print("   %-7s %5d = %5d + %5d + %4d %s | share %s vs %.1f%%"
              % (label, att, ex, ce, co, "OK" if att == ex + ce + co else "BAD", share, calc))
