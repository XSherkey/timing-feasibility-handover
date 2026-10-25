"""Swap the two table labels so the gate table (Section VI-E) is X and the annotation table (VI-L) is XI."""
from __future__ import annotations

import re
from pathlib import Path

D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"
for name, pre in (("paper_en.md", "Table "), ("paper_zh.md", "表 ")):
    p = D / name
    t = p.read_text(encoding="utf-8")
    t = t.replace(pre + "XI", "@@XI@@").replace(pre + "X", "@@X@@")
    t = t.replace("@@XI@@", pre + "X").replace("@@X@@", pre + "XI")
    p.write_text(t, encoding="utf-8")
    print(name, "swapped")
