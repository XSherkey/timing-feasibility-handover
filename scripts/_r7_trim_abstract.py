"""R7 (v9) EN: trim the abstract under 250 words."""
from __future__ import annotations

from pathlib import Path

P = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本" / "paper_en.md"
t = P.read_text(encoding="utf-8")

edits = [
    ("We began with a faithful reproduction of one such system and ended with an audit of what its gains consist of.",
     "We reproduce one such system and audit what its gains consist of."),
    ("the passive log covers the informative band of advance space thinly",
     "the passive log covers the informative band thinly"),
    ("so within any budget a field study can afford the bound is effectively unidentifiable",
     "so within an affordable budget the bound is effectively unidentifiable"),
    ("We state the boundaries plainly:", "Boundaries are stated plainly:"),
    ("but loses 6–7 pp under 3.2 s of acquisition drift", "but loses 6–7 pp under 3.2 s of drift"),
]
for old, new in edits:
    if t.count(old) != 1:
        raise SystemExit("missing: " + old[:50])
    t = t.replace(old, new, 1)

P.write_text(t, encoding="utf-8")
a = t.find("## Abstract")
b = t.find("**Index Terms", a)
print("abstract words:", len(t[a:b].split()))
