import re
from pathlib import Path

D = Path(r"../From Human Intent to In-Orbit Action/IEEE_Trans_新版本")
t = (D / "paper_en.md").read_text(encoding="utf-8")

print("=== subsection letters (Section VI) ===")
inside = t[t.find("## VI."):t.find("## VII.")]
print(" ".join(m.group(1) for m in re.finditer(r"^### ([A-O])\.", inside, flags=re.M)))

print("\n=== tables in document order ===")
for m in re.finditer(r"\*\*Table ([A-Z0-9]+)\.", t):
    print(" ", m.group(1), end="")
print()

print("\n=== stale strings ===")
for s in ("Table Vb", "Table Vc", "Table Vd", "recovers the pre-drift", "survives a change of physics",
          "learnable, calibratable and auditable", "−1.5, −3.1", "12 of 20", "four of the six"):
    print(f"  {t.count(s):2d}  {s}")

print("\n=== abstract sentences ===")
i = t.find("**Abstract—**")
j = t.find("**Index Terms—**")
print(t[i:j].strip()[:1400])
