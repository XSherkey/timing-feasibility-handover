"""R11 part 5: blank lines must flush the paragraph buffer (they currently merge whole paragraphs)."""
from __future__ import annotations

from pathlib import Path

D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"

# ---- builder: flush on blank lines ---------------------------------------
b = D / "build_paper_docx.js"
s = b.read_text(encoding="utf-8")
old = '  if (/^\\s*---+\\s*$/.test(line) || !line.trim()) {\n    i++;\n    continue;\n  }'
new = '  if (/^\\s*---+\\s*$/.test(line) || !line.trim()) {\n    flushPara();\n    i++;\n    continue;\n  }'
if old not in s:
    raise SystemExit("blank-line branch not found")
s = s.replace(old, new, 1)
b.write_text(s, encoding="utf-8")
print("builder flushes on blank lines")

# ---- the stale lambda gap ------------------------------------------------
p = D / "paper_en.md"
t = p.read_text(encoding="utf-8")
n = t.count("peaks 9.2 pp below the decision-layer injection")
t = t.replace("peaks 9.2 pp below the decision-layer injection", "peaks 10.4 pp below the decision-layer injection")
p.write_text(t, encoding="utf-8")
print("EN 9.2 -> 10.4 replacements:", n)

z = D / "paper_zh.md"
u = z.read_text(encoding="utf-8")
m = u.count("低 9.2 pp")
u = u.replace("低 9.2 pp", "低 10.4 pp")
z.write_text(u, encoding="utf-8")
print("ZH 9.2 -> 10.4 replacements:", m)
