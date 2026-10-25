"""QA for v8: residual numbers, ledger naming, table bodies and captions."""
from __future__ import annotations

import re
from pathlib import Path

from docx import Document

D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"

BAD = ["67 of 22,807", "count is 67", "67 attempts out of", "two orders of magnitude",
       "action support misses", "Full-system campaign figure", "per-advance counts in Table D1",
       "min_advance:16@latitude_abs_deg=68"]

for f in ("Paper_EN_v8.docx", "Paper_ZH_v8.docx"):
    doc = Document(D / f)
    text = "\n".join(p.text for p in doc.paragraphs)
    print("=" * 72)
    print(f, "| paras", len(doc.paragraphs), "| tables", len(doc.tables))
    for b in BAD:
        n = text.count(b)
        if n:
            print("   RESIDUAL:", repr(b), n)
    # appendix C captions and the table that follows each
    caps = [p.text.strip()[:60] for p in doc.paragraphs if re.match(r"^(Table C\d|表 C\d)", p.text.strip())]
    print("   appendix-C captions:", caps)
    # count table bodies after each caption by walking the body elements
    print("   D1A/D1B present:",
          "D1A" in text and "D1B" in text)
    print("   'full system' occurrences in paragraphs:", text.count("full system"),
          "| '全系统':", text.count("全系统"))
