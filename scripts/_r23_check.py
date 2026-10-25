import re
from pathlib import Path

D = Path(r"../From Human Intent to In-Orbit Action/IEEE_Trans_新版本")
t = (D / "paper_en.md").read_text(encoding="utf-8")

pats = ["remaining_visibility_deg", "remaining_visibility_s", "-0.00", "+0.00",
        "T_2", "3,2", "{2, 3.2, 4.4}", "deepseek-flash", "deepseek- f", "mtimes", "mmes",
        "lat | ≥ 70°>", "probed τ*", "Paired statistics"]
for p in pats:
    print(f"{t.count(p):3d}  {p}")

print("\n--- Table IX A3 rule ---")
i = t.find("**Table IX.")
j = t.find("\n\n", t.find("| A8", i))
for line in t[i:j].splitlines():
    if line.startswith("| A3") or line.startswith("| A8"):
        print(line[:220])

print("\n--- Table V header ---")
i = t.find("**Table V.")
print(t[i:i+260])

print("\n--- Paired statistics occurrences ---")
for m in re.finditer("Paired statistics", t):
    print(repr(t[max(0, m.start() - 90):m.start() + 60]))

print("\n--- Table X captions ---")
for m in re.finditer(r"\*\*Table X\.", t):
    print(repr(t[m.start():m.start() + 110]))
