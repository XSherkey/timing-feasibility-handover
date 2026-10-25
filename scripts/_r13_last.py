"""R14 final: remove the residual clause that still says only the epoch changes."""
from __future__ import annotations

from pathlib import Path

D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"

p = D / "paper_en.md"
t = p.read_text(encoding="utf-8")
old = ("the isolation arms of Table IX and the lockbox rows here—now uses the same campaign policies, the same "
       "traffic seed and the same episode protocol; the only thing that changes between rows of Table X is the "
       "twin epoch itself.")
new = ("the isolation arms of Table IX and the lockbox rows here—now uses the same campaign policies, the same "
       "traffic seed and the same episodes. What changes across Table X is the protocol (archival versus "
       "three-way) and, inside the three lockbox columns, the twin epoch.")
print("EN count", t.count(old))
if t.count(old) == 1:
    t = t.replace(old, new, 1)
    p.write_text(t, encoding="utf-8")

z = D / "paper_zh.md"
s = z.read_text(encoding="utf-8")
oldz = "在后三列之内，唯一变化的是孪生历元。"
newz = "在后三列之内，唯一变化的是孪生历元；跨列变化的是协议本身。"
if s.count(oldz) >= 1:
    s = s.replace(oldz, newz)
    z.write_text(s, encoding="utf-8")
    print("ZH updated")
