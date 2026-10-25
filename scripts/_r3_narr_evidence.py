"""Per-narrative evidence for the manual annotation: what the 4 attempts in each narrative show."""
from __future__ import annotations

import csv
import json
import re

rows = list(csv.DictReader(open("results/routeA_r3/llm_proposals/proposals.csv", encoding="utf-8")))
for r in rows:
    narr = r["narrative"]
    adv = [float(x) for x in re.findall(r"handover advance ([\d.]+) s", narr)]
    acq = [float(x) for x in re.findall(r"acquisition took ([\d.]+) s", narr)]
    lat = [float(x) for x in re.findall(r"\(lat (-?[\d.]+) deg", narr)]
    el = [float(x) for x in re.findall(r"elevation ([\d.]+) deg", narr)]
    causes = re.findall(r"error code: (\w+)", narr)
    rule = json.loads(r["p1_rule"])
    print("%2s adv=%s acq=%s lat=%s el=%s causes=%s | mag=%s | %s" % (
        r["narrative_id"], adv, acq, lat, el, sorted(set(causes)),
        r.get("p2_magnitude"), json.dumps(rule.get("atoms"))))
