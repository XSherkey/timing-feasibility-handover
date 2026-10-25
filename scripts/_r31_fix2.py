"""R31 part 2: force the three remaining captions into a single bold span."""
from __future__ import annotations

import re
from pathlib import Path

D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"
main = D / "paper_en.md"
supp_path = D / "supplementary" / "supp_en.md"


def fix_caption(path: Path, start: str) -> bool:
    txt = path.read_text(encoding="utf-8")
    i = txt.find(start)
    if i < 0:
        print("  missing:", start[:34])
        return False
    j = txt.find("\n\n", i)
    block = txt[i:j]
    clean = block.replace("*", "").strip()
    new = "**" + clean + "**"
    txt = txt[:i] + new + txt[j:]
    path.write_text(txt, encoding="utf-8")
    print(f"  fixed {start[:34]} | stars now {new.count('*')}")
    return True


fix_caption(main, "**Table VIII. Where the variance lives")
fix_caption(supp_path, "**Table H2. Drift response")
fix_caption(supp_path, "**Table J1. Annotation of the twenty proposals")

# verify
for p in (main, supp_path):
    txt = p.read_text(encoding="utf-8")
    for m in re.finditer(r"\*\*Table [A-Za-z0-9]+\.", txt):
        j = txt.find("\n\n", m.start())
        cap = txt[m.start():j]
        if cap.count("*") != 4:
            print("  still odd:", p.name, cap[:60], cap.count("*"))
print("check done")
