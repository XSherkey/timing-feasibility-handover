"""R7 ZH part 5: the 'never exercise' phrasing appears as '从不试探' in the ZH text."""
from __future__ import annotations

from pathlib import Path

D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"
z = D / "paper_zh.md"
t = z.read_text(encoding="utf-8")
old = "去解释为什么被动日志无法钉死一个训练策略从不试探的计时约束"
new = "去解释为什么被动日志无法钉死一个训练策略几乎不触及的计时约束（8,682 次尝试中仅 705 次落在信息带内）"
print("count", t.count(old))
if t.count(old) == 1:
    t = t.replace(old, new, 1)
    z.write_text(t, encoding="utf-8")
    print("fixed")
