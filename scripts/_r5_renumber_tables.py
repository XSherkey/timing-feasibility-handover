"""Renumber the ladder table into its citation position: X->VII, VII->VIII, VIII->IX, IX->X."""
from __future__ import annotations

import re
from pathlib import Path

D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"
MAP = {"VII": "VIII", "VIII": "IX", "IX": "X", "X": "VII"}
ORDER = ["VIII", "IX", "X", "VII"]  # longest-first so VIII is not eaten by VII

for name, prefix in (("paper_en.md", "Table "), ("paper_zh.md", "表 ")):
    p = D / name
    t = p.read_text(encoding="utf-8")
    if "@@T" in t:
        raise SystemExit(f"{name}: leftover tokens")
    for key in ORDER:
        t = t.replace(prefix + key, f"@@T{key}@@")
    for key in ORDER:
        t = t.replace(f"@@T{key}@@", prefix + MAP[key])
    p.write_text(t, encoding="utf-8")
    print(name, "renumbered")

# sanity: print every caption/mention order in the English body
t = (D / "paper_en.md").read_text(encoding="utf-8")
cut = t.find("## References")
seq = [m.group(1) for m in re.finditer(r"Table (I|II|III|IV|V|VI|VII|VIII|IX|X)\b", t[:cut])]
print("EN table mention order:", seq[:40])
