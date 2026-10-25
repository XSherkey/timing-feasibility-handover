"""R7 part 6: Table C3 becomes a per-seed before/after table, which is where the variation lives."""
from __future__ import annotations

import json
from pathlib import Path

D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"
ROOT = Path(__file__).resolve().parents[2] / "almond-repro"
fc = json.loads((ROOT / "results" / "routeA_r3" / "factorial_consistent" / "summary.json").read_text(encoding="utf-8"))
c3 = json.loads((ROOT / "results" / "routeA_r3" / "c3_deployed" / "summary.json").read_text(encoding="utf-8"))
dm = json.loads((ROOT / "results" / "routeA_r3" / "drift_margin" / "summary.json").read_text(encoding="utf-8"))
A = fc["arms"]
TAGS = ["0", "+2", "+3.2", "+4.4"]
const = [dm["regimes"][r]["arms"]["const_fixed18"]["summary"]["mean"] for r in ("1.2", "3.2", "4.4", "5.6")]
probed = [dm["regimes"][r]["arms"]["const_probed"]["summary"]["mean"] for r in ("1.2", "3.2", "4.4", "5.6")]

p = D / "paper_en.md"
t = p.read_text(encoding="utf-8")
i = t.find("**Table C3.")
j = t.find("\n\n", t.find("| mean ± sd |", i))
if i < 0 or j < 0:
    raise SystemExit("C3 not found")
rows = ["| seed | no shield | τ = 16 s | deployed (τ = 18 s) | +2.0 s drift | +3.2 s drift | +4.4 s drift | gain (no shield → deployed) |",
        "|---|---|---|---|---|---|---|---|"]
for k in range(10):
    none = A["none"]["polar"][k]
    dep = c3["0"]["polar"][k]
    rows.append("| %d | %.1f | %.1f | %.2f | %.2f | %.2f | %.2f | +%.1f |" % (
        k, none, A["rule16"]["polar"][k], dep,
        c3["+2"]["polar"][k], c3["+3.2"]["polar"][k], c3["+4.4"]["polar"][k], dep - none))
rows.append("| mean ± sd | %.1f ± %.1f | %.2f ± %.2f | %.2f ± %.2f | %.2f ± %.2f | %.2f ± %.2f | %.2f ± %.2f | — |" % (
    A["none"]["summary"]["mean"], A["none"]["summary"]["sd"],
    A["rule16"]["summary"]["mean"], A["rule16"]["summary"]["sd"],
    c3["0"]["summary"]["mean"], c3["0"]["summary"]["sd"],
    c3["+2"]["summary"]["mean"], c3["+2"]["summary"]["sd"],
    c3["+3.2"]["summary"]["mean"], c3["+3.2"]["summary"]["sd"],
    c3["+4.4"]["summary"]["mean"], c3["+4.4"]["summary"]["sd"]))
C3 = ("**Table C3. Per-seed drift response (polar HSR at |lat| ≥ 70°, campaign policies, traffic seed 0, "
      "n = 10 policy seeds). The shield columns are near-identical for several seeds because the constraint, "
      "not the policy, determines the outcome inside the band once it is applied—the remaining spread "
      "(sd 0.05, two seeds at 93.45–93.47) is selection quality, and it is the same spread that Fig. 2 shows. "
      "The tuned constant is policy-independent and appears as regime means only: fixed 18 s reads " +
      " / ".join("%.2f" % v for v in const) + ", re-probed reads " +
      " / ".join("%.2f" % v for v in probed) + " at δ = 0/+2/+3.2/+4.4 s.**\n\n" + "\n".join(rows) + "\n")
t = t[:i] + C3 + t[j:]
p.write_text(t, encoding="utf-8")
print("C3 rebuilt")
