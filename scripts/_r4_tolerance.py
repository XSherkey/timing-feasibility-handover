"""R4 (v16) part 5: propagate the new tolerance (1.6 pp) and margin range into EN and ZH."""
from __future__ import annotations

from pathlib import Path

D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"

EN_OLD = ("the full-system policies' margin over the hand-crafted baseline is small (+0.9–1.2 pp, i.e. at or "
          "within the 1.2 pp tolerance defined in Section VI-A)")
EN_NEW = ("the full-system policies' margin over the hand-crafted baseline is small (+0.9–1.6 pp, i.e. at or "
          "within the 1.6 pp tolerance defined in Section VI-A)")

p = D / "paper_en.md"
t = p.read_text(encoding="utf-8")
n = t.count(EN_OLD)
t = t.replace(EN_OLD, EN_NEW)
p.write_text(t, encoding="utf-8")
print("EN replacements:", n)

ZH_PAIRS = [
    ("（+0.9–1.2 pp，即恰在第六节 A 定义的 1.2 pp 容差处或略超出）",
     "（+0.9–1.6 pp，即恰在第六节 A 定义的 1.6 pp 容差之内）"),
    ("全系统策略相对手工基线的领先**很小**——+0.9 至 +1.2 pp",
     "全系统策略相对手工基线的领先**很小**——+0.9 至 +1.6 pp"),
]
z = D / "paper_zh.md"
s = z.read_text(encoding="utf-8")
done = []
for old, new in ZH_PAIRS:
    if s.count(old) == 1:
        s = s.replace(old, new, 1)
        done.append(old[:30])
z.write_text(s, encoding="utf-8")
print("ZH replacements:", done)
