"""Full cross-check of v84 before submission."""
from __future__ import annotations

import re
from pathlib import Path

D = Path(r"../From Human Intent to In-Orbit Action/IEEE_Trans_新版本")
t = (D / "paper_en.md").read_text(encoding="utf-8")
s = (D / "supplementary/supp_en.md").read_text(encoding="utf-8")

print("=== MAIN ===")
caps = re.findall(r"\*\*Table ([IVX]+)\.", t)
print("table captions:", caps)
figs = re.findall(r"\*\*Fig\. (\d)\.\*\*", t)
print("figure captions:", figs)
eqs = re.findall(r"\((\d)\)\s*$", t, flags=re.M)
print("equation labels:", eqs)
print("subsection letters VI:", " ".join(re.findall(r"^### ([A-O])\.", t[t.find("## VI."):t.find("## VII.")], flags=re.M)))
print("section headings:", re.findall(r"^## ([IVX]+)\.", t, flags=re.M))

refs_tbl = sorted(set(re.findall(r"Table ([IVX]+)(?![A-Za-z])", t)))
print("table refs used:", refs_tbl, "| unresolved:", [r for r in refs_tbl if r not in caps])
print("supp table refs:", sorted(set(re.findall(r"Table ([A-Z]\d+[A-Z]?)", t))))

bad = {
    "old table labels": ["Table IX", "Table Xb", "Table IXb", "Table IXc"],
    "old strings": ["four caps", "|Δ| ≤ 1.0", "Every comparison in this paper is paired", "Section VI-K",
                    "value of the loop", "feeder capacity reduced to three slots", "recovers the pre-drift",
                    "survives a change of physics", "+6.2 to +21.6"],
}
for grp, pats in bad.items():
    for p in pats:
        n = len(re.findall(re.escape(p) + r"(?![A-Za-z])", t)) if p.startswith("Table") else t.count(p)
        if n:
            print(f"  !! {grp}: {p!r} x{n}")
print("stale check done")

print("\n=== SUPPLEMENT ===")
print("appendices:", re.findall(r"^## Appendix ([A-Z]\d*)", s, flags=re.M))
print("supp tables:", re.findall(r"\*\*Table ([A-Z]\d+[A-Z]?)\.", s))
d2 = s[s.find("**Table D2."):]
print("D2 header:", d2.splitlines()[2][:120] if len(d2.splitlines()) > 2 else d2[:120])
print("D2 rows:", d2.count("| G"))
print("H2 body rows:", s.count("| tuned constant, fixed 18 s |"))
for pat in ("Section VI-L", "Table V ", "rule (4)", "(3) contains none"):
    n = s.count(pat)
    if n:
        print(f"  !! supp stale: {pat!r} x{n}")
print("supp stale check done")

print("\n=== ABSTRACT NUMBERS ===")
i = t.find("**Abstract—**")
j = t.find("**Index Terms—**")
print(t[i:j].strip()[-700:])
