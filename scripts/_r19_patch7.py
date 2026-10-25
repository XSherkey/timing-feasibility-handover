"""R19 part 7: no column rule, and tables with five columns or more go full width."""
from __future__ import annotations

from pathlib import Path

D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"
p = D / "build_paper_docx.js"
s = p.read_text(encoding="utf-8")

s = s.replace("...(cols > 1 ? { column: { count: cols, space: 360 } } : {}),",
              "...(cols > 1 ? { column: { count: cols, space: 360, separate: false } } : {}),", 1)
s = s.replace("const wide = nCols >= 6;", "const wide = nCols >= 5;", 1)
p.write_text(s, encoding="utf-8")
print("patched: separate=false, wide threshold 5")

# the abstract prefix must sit on the abstract paragraph, not on the nomenclature
for name, prefix, anchor in (
    ("paper_en.md", "**Abstract—** ", "Handover reliability in low Earth orbit"),
    ("paper_zh.md", "**摘要——** ", "低轨星座的切换可靠性"),
):
    f = D / name
    t = f.read_text(encoding="utf-8")
    t = t.replace(prefix, "", 1) if t.count(prefix) > 1 else t
    i = t.find(anchor)
    if i > 0 and not t[max(0, i - len(prefix)):i].endswith(prefix.strip()):
        t = t[:i] + prefix + t[i:]
        f.write_text(t, encoding="utf-8")
        print(name, "abstract prefix re-placed")
