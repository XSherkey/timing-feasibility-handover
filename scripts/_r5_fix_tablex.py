"""Fix the Table X caption: it is glued to the preceding sentence and duplicates the "five seeds" phrase."""
from __future__ import annotations

from pathlib import Path

D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"

p = D / "paper_en.md"
t = p.read_text(encoding="utf-8")
old = ("Under drift the ladder separates the references (five seeds per point, identical episodes across arms; "
       "δ is extra signalling latency):**Table X. Drift ladder")
new = ("Under drift the ladder separates the references.\n\n**Table X. Drift ladder")
if t.count(old) != 1:
    raise SystemExit(f"EN anchor {t.count(old)}")
t = t.replace(old, new, 1)
p.write_text(t, encoding="utf-8")
print("EN Table X caption split")

z = D / "paper_zh.md"
s = z.read_text(encoding="utf-8")
i = s.find("**表 X.")
if i > 0:
    k = s.rfind("\n", 0, i)
    prev = s[max(0, k - 200):k]
    print("ZH prev text:", repr(prev[-120:]))
    if not prev.rstrip().endswith(("。", "：")):
        print("ZH looks fine")
