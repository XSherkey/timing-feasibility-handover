"""R11 part 6: Fig. 3 and Fig. 7 shared the same caption; Fig. 3 is the drift figure."""
from __future__ import annotations

import json
from pathlib import Path

D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"
ROOT = Path(__file__).resolve().parents[2] / "almond-repro"
dm = json.loads((ROOT / "results" / "routeA_r3" / "drift_margin" / "summary.json").read_text(encoding="utf-8"))
R = dm["regimes"]
fx = [R[r]["arms"]["const_fixed18"]["summary"]["mean"] for r in ("1.2", "3.2", "4.4", "5.6")]
rp = [R[r]["arms"]["const_probed"]["summary"]["mean"] for r in ("1.2", "3.2", "4.4", "5.6")]

p = D / "paper_en.md"
t = p.read_text(encoding="utf-8")
i = t.find("**Fig. 3.** Reward injection is a dose-response")
if i < 0:
    raise SystemExit("Fig. 3 caption not found")
j = t.find("\n\n", i)
CAP = (f"**Fig. 3.** The tuned constant's failure boundary, and what re-probing buys. Polar HSR against extra "
       f"acquisition latency (campaign policies, traffic seed 0, n = 10 policy seeds, shaded band ±sd): the fixed "
       f"18 s constant (red) reads " + " / ".join("%.2f" % v for v in fx) + f" at δ = 0/+2/+3.2/+4.4 s, i.e. it "
       f"holds for about 2 s of drift and then loses {fx[0] - fx[2]:.1f} pp at +3.2 s and {fx[0] - fx[3]:.1f} pp at "
       f"+4.4 s, while the same controller with the threshold re-probed on each physics (blue, τ∗ = 16/18/20/22 s "
       f"plus the 2 s margin) reads " + " / ".join("%.2f" % v for v in rp) + ". The constant is not weak at nominal "
       f"physics; it is fixed, and a fixed threshold is a fact about the physics at tuning time.")
t = t[:i] + CAP + t[j:]
p.write_text(t, encoding="utf-8")
print("EN Fig. 3 caption restored (drift)")
print(CAP[:200])
