import json
import re
from pathlib import Path

D = Path(r"../From Human Intent to In-Orbit Action/IEEE_Trans_新版本")
en = (D / "paper_en.md").read_text(encoding="utf-8")
supp = (D / "supplementary/supp_en.md").read_text(encoding="utf-8")

print("=== 1. Table XII vs prose: 12/20 ?")
for m in re.finditer(r"12 of 20|12 \(coarser|coarser reading", en):
    print("  ", repr(en[max(0, m.start()-120):m.start()+120]))

print("\n=== 2. kappa sentence")
for m in re.finditer(r"0\.23", en):
    print("  ", repr(en[max(0, m.start()-160):m.start()+80]))

print("\n=== 3. G04 / G19 in D2")
for g in ("G04", "G19"):
    m = re.search(rf"\| {g} \|[^\n]*", supp)
    print("  ", m.group(0)[:150] if m else f"{g} not found")

print("\n=== 4. 8 s natural candidate in prose")
for m in re.finditer(r"8 s polar", en):
    print("  ", repr(en[max(0, m.start()-160):m.start()+160]))

print("\n=== 5. 'full λ grid behind Fig.'")
for m in re.finditer(r"λ grid behind", en):
    print("  ", repr(en[max(0, m.start()-80):m.start()+80]))

print("\n=== 6. Fig. 5 caption 'five bars'")
for m in re.finditer(r"five bars", en):
    print("  ", repr(en[max(0, m.start()-200):m.start()+120]))

print("\n=== 7. lambda=64 variance")
for m in re.finditer(r"17\.0|17\.3", en):
    print("  ", repr(en[max(0, m.start()-120):m.start()+80]))

print("\n=== 8. dangling table refs")
for tag in ("Table II", "Table IV", "Table VII", "Table VIII", "Table XI"):
    hits = [m.start() for m in re.finditer(re.escape(tag) + r"(?![IVX])", en)]
    print(f"  {tag}: {len(hits)}")
    for h in hits[:3]:
        print("      ", repr(en[max(0, h-90):h+60]))
