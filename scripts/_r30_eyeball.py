import re
from pathlib import Path

t = Path(r"../From Human Intent to In-Orbit Action/IEEE_Trans_新版本/paper_en.md").read_text(encoding="utf-8")
seen = 0
for m in re.finditer(r"Table[s]? [IVX]+", t):
    ctx = t[max(0, m.start() - 150):m.start() + 120].replace("\n", " ")
    print("...", ctx, "\n")
    seen += 1
    if seen >= 18:
        break
