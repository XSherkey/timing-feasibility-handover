"""Restore the Table D1B body that the previous edit removed, taking the numbers from the archived v50 docx."""
from __future__ import annotations

import re
from pathlib import Path

from docx import Document

D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"
hist = sorted((D / "_history").glob("Paper_EN_v50_*.docx"))[-1]
doc = Document(hist)
d1b = None
for tb in doc.tables:
    head = [c.text.strip() for c in tb.rows[0].cells]
    if len(head) == 4 and "=" in head[2] and len(tb.rows) == 9:
        d1b = tb
if d1b is None:
    raise SystemExit("D1B not found in the archive")

rows = ["| advance bucket (s) | attempts | exact + right-censored + competing = attempts | share of attempts |",
        "| --- | --- | --- | --- |"]
for r in d1b.rows[1:]:
    c = [x.text.strip() for x in r.cells]
    if c[0].lower().startswith("total"):
        rows.append(f"| **total** | **{c[1]}** | {c[2]} | **100%** |")
    else:
        rows.append(f"| {c[0]} | {c[1]} | {c[2]} | {c[3]} |")
TABLE = "\n".join(rows)

p = D / "paper_en.md"
t = p.read_text(encoding="utf-8")
i = t.find("**Table D1B. Rule-applied logs")
if i < 0:
    raise SystemExit("D1B caption not found")
nl = t.find("\n", i)
# insert caption + blank + table + blank, keeping the existing note after
t = t[:nl + 1] + "\n" + TABLE + "\n\n" + t[nl + 2:]
p.write_text(t, encoding="utf-8")
print("D1B restored")
print(TABLE)
