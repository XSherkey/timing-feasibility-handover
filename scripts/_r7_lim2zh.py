"""R8: the Chinese limitation-2 sentence with its exact wording."""
from __future__ import annotations

from pathlib import Path

D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"
z = D / "paper_zh.md"
s = z.read_text(encoding="utf-8")
old = "（+4.4 s 漂移下有一个种子探低一个网格步，91.1% 对 94.1%）"
new = ("（+4.4 s 漂移下，五个探测种子中有一个返回 20 s 而非 22 s，即低一个网格步，"
       "代价等同于表 V 中固定臂与重探臂之差）")
print("count", s.count(old))
if s.count(old) == 1:
    s = s.replace(old, new, 1)
old2 = "且 +4.4 s 漂移下有一个种子探低一个网格步（91.1% 对 94.1%）"
new2 = ("且 +4.4 s 漂移下，五个探测种子中有一个返回 20 s 而非 22 s（低一个网格步，"
        "代价等同于表 V 中固定臂与重探臂之差）")
print("count2", s.count(old2))
if s.count(old2) == 1:
    s = s.replace(old2, new2, 1)
z.write_text(s, encoding="utf-8")
print("done")
