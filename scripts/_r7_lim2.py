"""R8 final: Limitation 2 no longer quotes a per-seed number that the unified run does not reproduce."""
from __future__ import annotations

from pathlib import Path

D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"

p = D / "paper_en.md"
t = p.read_text(encoding="utf-8")
old = ("one seed at +4.4 s drift probes one grid step low (91.1% vs 94.1%)")
new = ("at +4.4 s drift one of the five probe seeds returns 20 s instead of 22 s, i.e. one grid step low, "
       "which would cost it the difference between the fixed and the re-probed arm of Table V")
if t.count(old) == 1:
    t = t.replace(old, new, 1)
    p.write_text(t, encoding="utf-8")
    print("EN limitation 2 fixed")
else:
    print("EN count", t.count(old))

z = D / "paper_zh.md"
s = z.read_text(encoding="utf-8")
oldz = "在 +4.4 s 漂移下有一个种子探低一个网格步（91.1% 对 94.1%）"
if s.count(oldz) == 1:
    s = s.replace(oldz, "在 +4.4 s 漂移下，五个探测种子中有一个返回 20 s 而非 22 s，即低一个网格步，"
                        "代价等同于表 V 中固定臂与重探臂之差", 1)
    z.write_text(s, encoding="utf-8")
    print("ZH limitation 2 fixed")
else:
    print("ZH count", s.count(oldz))
