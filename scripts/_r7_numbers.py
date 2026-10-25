"""R8 part 1: numbers that contradict the tables (92.4 vs 1.2 pp, lockbox ordering, drift loss, 24.0/24.1)."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / "almond-repro"
D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"
lk = json.loads((ROOT / "results" / "routeA_r3" / "lockbox_consistent" / "summary.json").read_text(encoding="utf-8"))
dm = json.loads((ROOT / "results" / "routeA_r3" / "drift_margin" / "summary.json").read_text(encoding="utf-8"))
I = lk["instances"]
INSTS = ["eval", "lb299.25", "lb306.25", "lb290.25"]
lm = lambda i, a: I[i][a]["summary"]["mean"]
gap_mined = [lm(i, "deployed_18") - lm(i, "mined_16") for i in INSTS]
gap_ppo = [lm(i, "deployed_18") - lm(i, "ppomlp_mined_16") for i in INSTS]
loss32 = dm["regimes"]["1.2"]["arms"]["const_fixed18"]["summary"]["mean"] - dm["regimes"]["4.4"]["arms"]["const_fixed18"]["summary"]["mean"]
loss44 = dm["regimes"]["1.2"]["arms"]["const_fixed18"]["summary"]["mean"] - dm["regimes"]["5.6"]["arms"]["const_fixed18"]["summary"]["mean"]

p = D / "paper_en.md"
t = p.read_text(encoding="utf-8")
done = []


def rep(old, new, label, count=1):
    global t
    n = t.count(old)
    if n != count:
        print(f"  MISS [{label}] {n} (want {count})")
        return
    t = t.replace(old, new)
    done.append(label)


# 1. 92.4 vs 1.2 pp (two places)
rep("The end-to-end campaign figure of the mined-rule campaign arm, 92.4% ± 0.07%, sits within ≈1.2 pp of the frozen τ = 16 s arm (Section VI-B).",
    "The end-to-end campaign figure of the mined-rule campaign arm, 92.44% ± 0.07%, coincides with the frozen "
    "τ = 16 s arm to 0.00 pp—they are the same rule measured the same way (Section VI-B).", "campaign-1")
rep("and their means agree within ≈1.2 pp;",
    "and their means agree to 0.00 pp;", "campaign-2")

# 2. the lockbox ordering summary
rep("the deployed arm is 1.4–2.1 pp above the mined 16 s rule and 2.3–3.4 pp above the same-rule PPO-MLP baseline",
    f"the deployed arm is {min(gap_mined):.2f}–{max(gap_mined):.2f} pp above the mined 16 s rule and "
    f"{min(gap_ppo):.2f}–{max(gap_ppo):.2f} pp above the same-rule PPO-MLP baseline", "ordering-summary")

# 3. the drift loss
rep("and the constant loses 6–7 pp where probe calibration",
    f"and the constant loses {loss32:.1f}–{loss44:.1f} pp where probe calibration", "drift-loss")

# 4. 24.0 vs 24.1
rep("the constraint is worth 23.4 of the 24.0 pp between the reward-only baseline and the shielded system",
    "the constraint is worth 23.4 of the 24.1 pp between the reward-only baseline and the shielded system",
    "gap-24")

p.write_text(t, encoding="utf-8")
print("applied:", done)
print("gaps:", [round(x, 2) for x in gap_mined], [round(x, 2) for x in gap_ppo], round(loss32, 2), round(loss44, 2))
