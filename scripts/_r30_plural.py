"""R30 part 3: fix the two plural table references the singular renumbering missed."""
from __future__ import annotations

import re
from pathlib import Path

p = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本" / "paper_en.md"
t = p.read_text(encoding="utf-8")

fixes = [
    ("Tables IXb and IXc select on the validation window", "Tables V and VI select on the validation window"),
    ("the lockbox columns of Tables IX and X report three-way numbers",
     "the lockbox columns of Tables IV and VII report three-way numbers"),
]
for old, new in fixes:
    n = t.count(old)
    print(f"{n}  {old[:48]}")
    t = t.replace(old, new, 1)

p.write_text(t, encoding="utf-8")

left = re.findall(r"Tables? (?:IXb|IXc|IX|Xb|X)(?![A-Za-z])", t)
print("leftover plural refs:", left)
