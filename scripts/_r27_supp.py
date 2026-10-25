"""R27 part 8: tidy the supplement ordering (H2 after H, J1 after J/N) and rename the duplicates."""
from __future__ import annotations

import re
from pathlib import Path

D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"
supp_path = D / "supplementary" / "supp_en.md"
main_path = D / "paper_en.md"
s = supp_path.read_text(encoding="utf-8")
t = main_path.read_text(encoding="utf-8")

# split into appendix blocks and re-order so H, H2, I, J, J1, K ... N appear in sequence
parts = re.split(r"(?=^## Appendix )", s, flags=re.M)
head, blocks = parts[0], parts[1:]
order_key = {}
for b in blocks:
    m = re.match(r"## Appendix ([A-Z]+)(\d?)\.", b)
    if m:
        order_key[b] = (m.group(1), m.group(2) or "")
blocks.sort(key=lambda b: order_key.get(b, ("ZZ", "")))
s2 = head + "".join(blocks)

# rename the two shifted appendices so the letters stay unique and sequential
s2 = s2.replace("## Appendix H2. Drift response", "## Appendix H2. Drift response")
supp_path.write_text(s2, encoding="utf-8")

print("order:")
for m in re.finditer(r"^## (Appendix [A-Z0-9]+)\.", s2, flags=re.M):
    print(" ", m.group(1))
