"""R7 part 2: the three anchors that differ slightly (line breaks) from the first pass."""
from __future__ import annotations

from pathlib import Path

D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"
p = D / "paper_en.md"
t = p.read_text(encoding="utf-8")
done = []


def rep(old, new, label):
    global t
    n = t.count(old)
    if n != 1:
        print(f"  MISS [{label}] {n}")
        return
    t = t.replace(old, new, 1)
    done.append(label)


rep("*operational knowledge that passive logs never exercise must leave the reward layer and enter the decision layer, and any quantity measured f",
    "*operational knowledge that passive logs cover too thinly to identify must leave the reward layer and enter "
    "the decision layer, and any quantity measured f", "never-2")

rep("the end-to-end campaign figure (93.6 ± 0.7, Fig. 5) and the frozen τ = 16 s arm measure the same committed rule under two protocols—",
    "the end-to-end campaign figure (92.44 ± 0.07, Fig. 5) and the frozen τ = 16 s arm measure the same committed "
    "rule under one protocol—", "campaign-figure")

rep("seven provenance variants land within 0.11 pp of the full pipeline, and a highest-elevation controller who",
    "six provenance variants land within 0.11 pp of the full pipeline, and a highest-elevation controller who",
    "six-1")

p.write_text(t, encoding="utf-8")
print("applied:", done)
