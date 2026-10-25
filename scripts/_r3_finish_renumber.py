"""Finish the figure renumbering: ZH pass (tolerant), and drop the predecessor gate in the builder."""
from __future__ import annotations

import re
from pathlib import Path

D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"
MAP = {3: 1, 5: 2, 9: 3, 1: 4, 2: 5, 7: 6, 4: 7, 6: 8, 8: 9}

p = D / "paper_zh.md"
t = p.read_text(encoding="utf-8")
if "@@F" in t:
    raise SystemExit("tokens already present in ZH; clean up first")
t = re.sub(r"图\s*(\d+)",
           lambda m: f"@@F{m.group(1)}@@" if int(m.group(1)) in MAP else m.group(0), t)
t = re.sub(r"@@F(\d+)@@",
           lambda m: f"图 {MAP[int(m.group(1))]}" if int(m.group(1)) in MAP else m.group(0), t)
p.write_text(t, encoding="utf-8")
print("ZH renumbered")

js = D / "build_paper_docx.js"
s = js.read_text(encoding="utf-8")
old = """  const ready = (num) => {
    for (let k = 1; k < num; k++) if (!insertedFigs.has(k)) return false;
    return true;
  };"""
new = """  // figures are numbered in first-citation order now, so the predecessor gate is
  // unnecessary; keeping it let one unreferenced figure block the whole queue and
  // pushed every later figure past the references.
  const ready = (_num) => true;"""
if s.count(old) != 1:
    raise SystemExit("gate block not found")
s = s.replace(old, new, 1)
js.write_text(s, encoding="utf-8")
print("builder gate disabled")
