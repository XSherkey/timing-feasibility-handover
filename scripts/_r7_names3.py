"""R7 (v9): the last numeric 'full system' spots in section VI-B (EN and ZH)."""
from __future__ import annotations

from pathlib import Path

D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"

EN = [
    ("the same protocol that produces the 93.6% full-system figure, and the basis of bar 1 of Fig. 2",
     "the same protocol that produces the 93.6% mined-rule campaign arm figure, and the basis of bar 1 of Fig. 2"),
    ("the baseline family re-evaluated on the identical episodes used for the full-system factorial of Fig. 3",
     "the baseline family re-evaluated on the identical episodes used for the frozen-policy factorial of Fig. 3"),
    ("92.43 for the full-system arm), leaving ≈0.6 pp",
     "92.43 for the mined-rule arm), leaving ≈0.6 pp"),
]
ZH = [
    ("产生 93.6% 全系统数字的同一协议", "产生 93.6% 挖出规则 campaign 臂数字的同一协议"),
    ("在同一批回合上对基线族重评，是图 3 全系统因子化的基础", "在同一批回合上对基线族重评，是图 3 冻结策略因子化的基础"),
    ("带盾 91.8，全系统臂 92.43）", "带盾 91.8，挖出规则臂 92.43）"),
]

for name, pairs in (("paper_en.md", EN), ("paper_zh.md", ZH)):
    p = D / name
    t = p.read_text(encoding="utf-8")
    n = 0
    for old, new in pairs:
        if t.count(old) == 1:
            t = t.replace(old, new, 1)
            n += 1
        else:
            print("  (skip, count", t.count(old), ")", old[:45])
    p.write_text(t, encoding="utf-8")
    print(name, "renamed", n)
