"""R5: rebuild the oracle-ladder table (Section VI-G) on the unified protocol, with a caption."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / "almond-repro"
D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"
lad = json.loads((ROOT / "results" / "routeA_r3" / "ladder_consistent" / "summary.json").read_text(encoding="utf-8"))
dm = json.loads((ROOT / "results" / "routeA_r3" / "drift_margin" / "summary.json").read_text(encoding="utf-8"))
R = lad["regimes"]
mn = lambda reg, arm: R[reg][arm]["summary"]["mean"]
# tuned constant and deployed (fixed) come from the drift_margin run, which covers all four regimes
const = {r: dm["regimes"][r]["arms"]["const_fixed18"]["summary"]["mean"] for r in dm["regimes"]}
deployed = {r: dm["regimes"][r]["arms"]["shield_fixed18"]["summary"]["mean"] for r in dm["regimes"]}
REGS = [("1.2", "0"), ("3.2", "+2.0 s"), ("4.4", "+3.2 s"), ("5.6", "+4.4 s")]
LAD = {"1.2": "nominal", "3.2": "plus2s", "4.4": "plus3p2s", "5.6": "plus4p4s"}

p = D / "paper_en.md"
t = p.read_text(encoding="utf-8")
start = t.find("| δ | oracle |")
if start < 0:
    raise SystemExit("ladder table not found")
# walk back to the paragraph that introduces the table
intro = t.rfind("\n\n", 0, start)
end = t.find("\n\n", t.find("|", t.find("| +4.4 s", start)))
rows = ["| δ | oracle | τ = 18 s (fixed) | 16 s rule (as a shield) | tuned 18 s constant | reward λ = 8 | no knowledge |",
        "|---|---|---|---|---|---|---|"]
for key, lab in REGS:
    tag = LAD[key]
    rows.append("| %s | %.2f | %.2f | %.2f | %.2f | %.2f | %.2f |" % (
        lab, mn(tag, "oracle"), deployed[key], mn(tag, "narrative_16s_rule"), const[key],
        mn(tag, "reward_lam8"), mn(tag, "no_knowledge")))
CAP = ("**Table X. Drift ladder (polar HSR, |lat| ≥ 70°, campaign policies, traffic seed 0, identical episodes, "
       "ten policy seeds per grid point; δ is extra acquisition signalling latency).**\n\n" + "\n".join(rows) + "\n")
t = t[:intro] + CAP + t[end:]
p.write_text(t, encoding="utf-8")
print("ladder table rebuilt with caption")
print("\n".join(rows))
