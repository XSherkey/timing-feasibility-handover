"""Fix the cross-reference produced by the rotation: the intro sentence must point at Fig. 1."""
from __future__ import annotations

from pathlib import Path

D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"
PAIRS = {
    "paper_en.md": ("Fig. 2 shows the shape of the answer we end up with",
                    "Fig. 1 shows the shape of the answer we end up with"),
    "paper_zh.md": ("图 2 给出我们最终得到的答案的形状", "图 1 给出我们最终得到的答案的形状"),
}
for name, (old, new) in PAIRS.items():
    p = D / name
    t = p.read_text(encoding="utf-8")
    if t.count(old) != 1:
        raise SystemExit(f"{name}: found {t.count(old)}")
    t = t.replace(old, new, 1)
    p.write_text(t, encoding="utf-8")
    print(name, "intro pointer fixed to Fig. 1")
