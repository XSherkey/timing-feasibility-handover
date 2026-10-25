"""Write the manual annotation of the twenty proposals (author-side, rubric in Appendix E).

Verdicts
  accept : a domain expert could deploy the rule as proposed
  revise : the predicate is well-formed but would need a scope or magnitude change before deployment
  reject : the predicate targets the wrong failure mode or is not executable
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
P = ROOT / "results" / "routeA_r3" / "llm_proposals" / "proposals.csv"
rows = list(csv.DictReader(open(P, encoding="utf-8")))

# verdict, reason, evidence
ANN = {
    "1": ("accept", "polar scope plus a short-advance guard covers the failures shown",
          "narratives: advance 6 s, acquisition 8.0-9.8 s, lat 64-72"),
    "2": ("accept", "same structure, scope tightened to 64 deg", "3 of 4 failures at lat >= 64"),
    "3": ("revise", "magnitude 10 s is below the 8.9 s acquisition observed in this narrative plus margin; no 2 s cost-asymmetric margin",
          "acquisition up to 8.9 s; window_exceeded also present"),
    "4": ("accept", "ordering of atoms is irrelevant; scope and guard are right", "same evidence as item 1"),
    "5": ("accept", "polar scope with a short-advance guard", "failures at lat 64-72"),
    "6": ("revise", "elevation_deg < 40 excludes failures at 46.9, 45.4 and 50.2 deg in the same narrative",
          "2 of 4 failures above the elevation cut"),
    "7": ("revise", "plane_change == 1 keeps only half of the failures", "2 of 4 failures have plane change 0"),
    "8": ("revise", "no latitude scope: raises the lead globally, including regions with no failures",
          "failures span lat -1 to 72"),
    "9": ("revise", "no latitude scope; global floor of 12 s", "same as item 8"),
    "10": ("revise", "no short-advance guard and a magnitude of 16 s applied to every polar attempt; over-protective",
           "acquisition 3.7-15.7 s"),
    "11": ("revise", "plane_change == 1 again halves the covered failures", "2 of 4 failures have plane change 0"),
    "12": ("revise", "global scope; a no_route failure is present that no lead floor can fix",
           "one no_route in the narrative"),
    "13": ("revise", "global scope with a 16 s floor", "failures span lat -1 to 70"),
    "14": ("revise", "global scope", "same as item 13"),
    "15": ("revise", "magnitude 18 s with no guard: above the observed plateau, trades window violations",
           "acquisition up to 15.8 s"),
    "16": ("revise", "remaining_visibility_s > 0 is always true; it adds nothing to the predicate",
           "the atom is redundant"),
    "17": ("revise", "global scope and a 10 s floor, marginal against a 9.7 s acquisition",
           "acquisition up to 9.7 s"),
    "18": ("revise", "global scope", "failures span lat 42-64"),
    "19": ("revise", "magnitude 20 s applied to every polar attempt; no guard",
           "acquisition up to 15.8 s"),
    "20": ("revise", "global scope", "failures span lat 1-70"),
}

out = []
for r in rows:
    rule = json.loads(r["p1_rule"]) if r["p1_rule"] else {}
    v, why, ev = ANN[r["narrative_id"]]
    out.append(dict(narrative_id=r["narrative_id"], verdict=v, reason=why, evidence=ev,
                    effect=rule.get("effect"), atoms=json.dumps(rule.get("atoms")),
                    magnitude=r.get("p2_magnitude")))
dst = ROOT / "results" / "routeA_r3" / "llm_proposals" / "annotation_human.csv"
with dst.open("w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=list(out[0].keys()))
    w.writeheader()
    w.writerows(out)
print("wrote", dst)
from collections import Counter
print(Counter(o["verdict"] for o in out))
