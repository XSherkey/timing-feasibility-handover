"""R21 part 3: move Table VII (12-row alternative-physics grid) to the supplement; the numbers stay in the text."""
from __future__ import annotations

import re
from pathlib import Path

D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"
p = D / "paper_en.md"
supp_path = D / "supplementary" / "supp_en.md"
t = p.read_text(encoding="utf-8")
supp = supp_path.read_text(encoding="utf-8")

caps_before = len(re.findall(r"^\*\*Table ", t, flags=re.M))

i = t.find("**Table VII.")
if i < 0:
    raise SystemExit("Table VII not found")
end_row = t.find("| feeder 3 slots | PPO-MLP | tau_used = 18 s | 70.0 |", i)
j = t.find("\n\n", end_row)
block = t[i:j]

t = t[:i] + ("*Grid.* The full 12-row grid behind this paragraph is Table L1 of the supplementary material.\n") + t[j:]
# make the paragraph point at it
old = "Both outcomes are what the theory predicts:"
new = "Both outcomes are what the theory predicts:"
if old in t:
    t = t.replace(old, "The twelve rows are in Table L1 of the supplementary material. " + old, 1)

supp = supp.rstrip() + "\n\n## Appendix L. Alternative-physics grid\n\n" + block.replace(
    "**Table VII.", "**Table L1.") + "\n"

t = re.sub(r"\n{3,}", "\n\n", t)
p.write_text(t, encoding="utf-8")
supp_path.write_text(supp, encoding="utf-8")
caps_after = len(re.findall(r"^\*\*Table ", t, flags=re.M))
print("tables in main:", caps_before, "->", caps_after)
print("supp tables:", len(re.findall(r"^\*\*Table ", supp, flags=re.M)))
