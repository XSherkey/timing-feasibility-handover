import json
import re
from pathlib import Path

D = Path(r"../From Human Intent to In-Orbit Action/IEEE_Trans_新版本")
en = (D / "paper_en.md").read_text(encoding="utf-8")
supp = (D / "supplementary/supp_en.md").read_text(encoding="utf-8")

checks = [
    ("text[[ artifact", "text[["),
    ("prove invites", "prove invites"),
    ("prose invites", "prose invites"),
    ("tau_star underscore", "τ_*"),
    ("+3,2 typo", "+3,2"),
    ("VI.CONCLUSION run-together", "VI.CONCLUSION"),
    ("±d (not sd)", "±d "),
    ("Table II residual in main", "**Table II."),
    ("Table XI reference in main", "Table XI"),
    ("|λ| ≤ 70°", "|λ| ≤ 70°"),
    ("|lat| ≥ 70°", "|lat| ≥ 70°"),
    ("Table IX caption", "**Table IX."),
    ("Table I caption count", "**Table I."),
    ("eq3 string", "P_D( late under"),
    ("0/+2/+3/+4.4", "0/+2/+3/"),
    ("1.5 pp without minus", "8 s polar minimum 1.5 pp"),
]
print("=== main ===")
for label, pat in checks:
    print(f"{en.count(pat):3d}  {label}")

print("\n=== supplement ===")
for label, pat in [("Table H1 body row", "| 0 | 93.36 |"), ("Table C1 seed 9", "| 9 |"), ("SYSTEM (P1)", "SYSTEM (P1)")]:
    print(f"{supp.count(pat):3d}  {label}")

# reference numbering
nums = [int(m.group(1)) for m in re.finditer(r"^\[(\d+)\]", en, flags=re.M)]
print("\nrefs:", len(nums), "missing:", [i for i in range(1, 44) if i not in nums])

# Table IX rows
i = en.find("**Table IX.")
j = en.find("\n\n", en.find("| A8", i)) if i > 0 else -1
block = en[i:j] if i > 0 and j > i else ""
print("\nTable IX arms:", re.findall(r"^\| (A\d)", block, flags=re.M))

# kappa source of truth
p = Path(r"../almond-repro/results/routeA_r3/llm_proposals/agreement.json")
if p.exists():
    print("\nagreement.json:", json.dumps(json.loads(p.read_text(encoding="utf-8")), indent=1)[:1200])
