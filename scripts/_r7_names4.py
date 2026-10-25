"""R7 (v9) ZH: the two remaining numeric 'full system' spots in section VI-B."""
from __future__ import annotations

from pathlib import Path

P = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本" / "paper_zh.md"
t = P.read_text(encoding="utf-8")

PAIRS = [
    ("与产生 93.6% 全系统数字的协议相同",
     "与产生 93.6% 挖出规则 campaign 臂数字的协议相同"),
    ("基线家族在与图 3 全系统因子化完全相同的回合上重评估",
     "基线家族在与图 3 冻结策略因子化完全相同的回合上重评估"),
]
n = 0
for old, new in PAIRS:
    if t.count(old) == 1:
        t = t.replace(old, new, 1)
        n += 1
P.write_text(t, encoding="utf-8")
print("renamed", n)
