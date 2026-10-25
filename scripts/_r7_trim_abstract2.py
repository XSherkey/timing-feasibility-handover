"""R7 (v9) EN: final abstract trim to <=250 words."""
from __future__ import annotations

from pathlib import Path

P = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本" / "paper_en.md"
t = P.read_text(encoding="utf-8")

PAIRS = [
    ("We therefore move such knowledge out of the reward and into the decision layer.",
     "We therefore move this knowledge from the reward into the decision layer."),
    ("applied to frozen policy weights and scored on identical episodes,",
     "applied to frozen weights on identical episodes,"),
]
for old, new in PAIRS:
    if t.count(old) != 1:
        raise SystemExit("missing: " + old[:60])
    t = t.replace(old, new, 1)

P.write_text(t, encoding="utf-8")
a = t.find("## Abstract")
b = t.find("**Index Terms", a)
print("abstract words:", len(t[a:b].split()))
