"""R7 part 5: rebuild Table C3 from the per-seed deployed run and repair the caption spacing."""
from __future__ import annotations

import json
from pathlib import Path

D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"
ROOT = Path(__file__).resolve().parents[2] / "almond-repro"
c3 = json.loads((ROOT / "results" / "routeA_r3" / "c3_deployed" / "summary.json").read_text(encoding="utf-8"))
dm = json.loads((ROOT / "results" / "routeA_r3" / "drift_margin" / "summary.json").read_text(encoding="utf-8"))
TAGS = ["0", "+2", "+3.2", "+4.4"]
const = [dm["regimes"][r]["arms"]["const_fixed18"]["summary"]["mean"] for r in ("1.2", "3.2", "4.4", "5.6")]
probed = [dm["regimes"][r]["arms"]["const_probed"]["summary"]["mean"] for r in ("1.2", "3.2", "4.4", "5.6")]

p = D / "paper_en.md"
t = p.read_text(encoding="utf-8")

i = t.find("**Table C3. Drift response per seed")
j = t.find("\n\n", t.find("| τ_used = τ∗ + 2 |", i))
if i < 0 or j < 0:
    raise SystemExit("C3 not found")
rows = ["| seed | δ = 0 | δ = +2.0 s | δ = +3.2 s | δ = +4.4 s |", "|---|---|---|---|---|"]
for k in range(10):
    rows.append("| %d | %s |" % (k, " | ".join("%.2f" % c3[tag]["polar"][k] for tag in TAGS)))
rows.append("| mean ± sd | %s |" % " | ".join(
    "%.2f ± %.2f" % (c3[tag]["summary"]["mean"], c3[tag]["summary"]["sd"]) for tag in TAGS))
C3 = ("**Table C3. Per-seed drift response of the deployed arm (campaign policies + the 18 s shield, "
      "polar HSR at |lat| ≥ 70°, traffic seed 0, n = 10 policy seeds). The tuned constant and its re-probed "
      "counterpart are policy-independent and therefore appear as regime means rather than per seed: the fixed "
      "constant reads " + " / ".join("%.2f" % v for v in const) + ", the re-probed constant " +
      " / ".join("%.2f" % v for v in probed) + " at δ = 0/+2/+3.2/+4.4 s.**\n\n" + "\n".join(rows) + "\n")
t = t[:i] + C3 + t[j:]

# repair the missing blank line after the D1A / D1B captions
for tag in ("Table D1A.", "Table D1B."):
    k = t.find("**" + tag)
    if k > 0:
        nl = t.find("\n", k)
        if not t[nl + 1:nl + 2] == "\n":
            t = t[:nl + 1] + "\n" + t[nl + 1:]

p.write_text(t, encoding="utf-8")
print("C3 rebuilt")
print("\n".join(rows))
