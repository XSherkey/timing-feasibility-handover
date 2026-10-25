"""R7: A8 delta cell, contribution 2 numbers, and the ZH gate cross-reference."""
from __future__ import annotations

import json
from pathlib import Path

D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"
ROOT = Path(__file__).resolve().parents[2] / "almond-repro"

en = D / "paper_en.md"
t = en.read_text(encoding="utf-8")
n1 = t.count("| 93.33 | -0.02 | 91.67 |")
t = t.replace("| 93.33 | -0.02 | 91.67 |", "| 93.33 | -0.03 | 91.67 |")
en.write_text(t, encoding="utf-8")
print("EN A8 cell replaced:", n1)

zh = D / "paper_zh.md"
s = zh.read_text(encoding="utf-8")
n2 = s.count("| 93.33 | −0.02 | 91.67 |")
s = s.replace("| 93.33 | −0.02 | 91.67 |", "| 93.33 | −0.03 | 91.67 |")
# ZH gate cross-reference in VI-E
old = "门不是装饰。"
if s.count(old) == 1:
    s = s.replace(old, "门不是装饰（26 条候选的完整银行汇总于表 X）。", 1)
    print("ZH gate ref added")
zh.write_text(s, encoding="utf-8")
print("ZH A8 cell replaced:", n2)

# contribution 2: check for stale cross-intent numbers in both
for name, tok in (("paper_en.md", "Cross-intent"), ("paper_zh.md", "跨意图")):
    p = D / name
    tx = p.read_text(encoding="utf-8")
    i = tx.find("2. **")
    j = tx.find("\n3. **", i)
    print("----", name, "contribution 2 head:")
    print(tx[i:i + 400].replace("\n", " "))
