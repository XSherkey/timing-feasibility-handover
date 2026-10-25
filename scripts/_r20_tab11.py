"""R20 part 10: restore Table XI from the archived source."""
from __future__ import annotations

from pathlib import Path

D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"
HIST = D / "_history"
src = sorted(HIST.glob("paper_en_v59_*.md"))[-1]
t0 = src.read_text(encoding="utf-8")

i = t0.find("**Table XI.")
if i < 0:
    raise SystemExit("Table XI not in archive")
j = t0.find("\n\n", t0.find("|", t0.find("|", i) + 2))
if j < 0:
    j = t0.find("\n\n", i)
block = t0[i:j]
print("recovered block:\n", block[:600])

p = D / "paper_en.md"
t = p.read_text(encoding="utf-8")
if "**Table XI." in t:
    raise SystemExit("already present")
# insert at the end of Section VI-E, just before VI-F
k = t.find("### F. One constraint, four intents")
if k < 0:
    raise SystemExit("VI-F not found")
t = t[:k] + block + "\n\n" + t[k:]
p.write_text(t, encoding="utf-8")
print("Table XI restored")
