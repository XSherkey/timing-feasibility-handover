"""R12 part 3: fold the protocol note inside the caption's bold span so the parser sees one caption."""
from __future__ import annotations

import re
from pathlib import Path

D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"
p = D / "paper_en.md"
t = p.read_text(encoding="utf-8")

pat = re.compile(r"\*\*(Table (?:III|IV|V|VI|VII|VIII|IX)\..*?)\*\*\s*\*\*Protocol: ([^*]+)\*\*")
n = 0


def fix(m):
    global n
    n += 1
    return f"**{m.group(1)} Protocol: {m.group(2)}.**"


t = pat.sub(fix, t)
p.write_text(t, encoding="utf-8")
print("captions rewritten:", n)
for k in ("**Table III.", "**Table IX."):
    i = t.find(k)
    print(repr(t[i:i + 200]))
