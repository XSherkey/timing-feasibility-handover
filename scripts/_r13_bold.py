"""R14 part 7: fully bold the three captions that still carry a mid-caption bold break."""
from __future__ import annotations

from pathlib import Path

D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"

for name, starts in (("paper_en.md", ["**Table Xb. Paired statistics", "**Table XII. Annotation", "**Table D2. The full"]),
                     ("paper_zh.md", ["**表 Xb.", "**表 XII.", "**表 D2."])):
    p = D / name
    t = p.read_text(encoding="utf-8")
    n = 0
    for s in starts:
        i = t.find(s)
        if i < 0:
            print("  missing:", name, s)
            continue
        j = t.find("\n\n", i)
        line = t[i:j]
        if line.rstrip().endswith("**"):
            continue
        t = t[:i] + line.rstrip() + "**" + t[j:]
        n += 1
    p.write_text(t, encoding="utf-8")
    print(name, "captions bolded:", n)
