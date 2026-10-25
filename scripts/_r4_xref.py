"""Final cross-reference fix: the drift ladder lives in VI-D, not VI-G."""
from __future__ import annotations

from pathlib import Path

D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"

p = D / "paper_en.md"
t = p.read_text(encoding="utf-8")
old = "on the identical drift ladder (54.6%; Section VI-G)"
new = "on the identical drift ladder (54.6%; Section VI-D and Fig. 8)"
if t.count(old) == 1:
    t = t.replace(old, new, 1)
    p.write_text(t, encoding="utf-8")
    print("EN cross-ref fixed")
else:
    print("EN cross-ref count:", t.count(old))

z = D / "paper_zh.md"
s = z.read_text(encoding="utf-8")
old2 = "（54.6%；第六节 G）"
new2 = "（54.6%；第六节 D 与图 8）"
if s.count(old2) == 1:
    s = s.replace(old2, new2, 1)
    z.write_text(s, encoding="utf-8")
    print("ZH cross-ref fixed")
else:
    print("ZH cross-ref count:", s.count(old2))
