"""Patch step 4: the level-3 heading branch also has to flush the paragraph buffer."""
from __future__ import annotations

from pathlib import Path

D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"
p = D / "build_paper_docx.js"
s = p.read_text(encoding="utf-8")
old = "  if (/^###\\s+/.test(line)) {\n    children.push("
new = "  if (/^###\\s+/.test(line)) {\n    flushPara();\n    children.push("
if old not in s:
    raise SystemExit("level-3 heading branch not found")
s = s.replace(old, new, 1)
p.write_text(s, encoding="utf-8")
print("level-3 flush added")
