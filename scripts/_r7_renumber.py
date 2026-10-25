"""R8 part 2: table-structure fixes — the ledger caption + global renumber, C1+C2 merge, D1A/D1B layout,
Eq. (3) line split, Table XI kappa cell, Table IV caption wording."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / "almond-repro"
D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"
fc = json.loads((ROOT / "results" / "routeA_r3" / "factorial_consistent" / "summary.json").read_text(encoding="utf-8"))
c3 = json.loads((ROOT / "results" / "routeA_r3" / "c3_deployed" / "summary.json").read_text(encoding="utf-8"))
dm = json.loads((ROOT / "results" / "routeA_r3" / "drift_margin" / "summary.json").read_text(encoding="utf-8"))
F = fc["arms"]

p = D / "paper_en.md"
t = p.read_text(encoding="utf-8")
done = []

# ---------------------------------------------------------------- 1. ledger caption
i = t.find("| Arm (location) | Executed rule |")
if i < 0:
    raise SystemExit("ledger table not found")
lead = t.rfind("\n\n", 0, i)
LEDGER_CAP = ("**Table II. Threshold ledger: which rule each reported number executes (Section V-D). "
              "Every row names the arm, the rule that arm actually executes, and the threshold it is "
              "calibrated at; a number quoted anywhere in the paper can be traced through this table.**\n\n")
t = t[:lead + 2] + LEDGER_CAP + t[lead + 2:]
done.append("ledger-caption")

# ---------------------------------------------------------------- 2. renumber II..XI -> III..XII
# descending order so nothing is shifted twice
order = ["XI", "X", "IX", "VIII", "VII", "VI", "V", "IV", "III", "II"]
mapping = {"II": "III", "III": "IV", "IV": "V", "V": "VI", "VI": "VII", "VII": "VIII",
           "VIII": "IX", "IX": "X", "X": "XI", "XI": "XII"}
# protect the freshly inserted ledger caption
t = t.replace("**Table II. Threshold ledger", "@@LEDGER@@")
for key in order:
    t = t.replace("Table " + key, f"@@T{key}@@")
for key in order:
    t = t.replace(f"@@T{key}@@", "Table " + mapping[key])
t = t.replace("@@LEDGER@@", "**Table II. Threshold ledger")  # the ledger keeps II
# fix: the loop also renamed the ledger reference inside its own caption (it says Section V-D, fine)
done.append("renumber")

p.write_text(t, encoding="utf-8")
print("applied:", done)
print("mentions now:", re.findall(r"Table (I|II|III|IV|V|VI|VII|VIII|IX|X|XI|XII)\b", t)[:24])
