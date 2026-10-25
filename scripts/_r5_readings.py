"""R5: rewrite the ladder readings paragraph with the unified numbers."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / "almond-repro"
D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"
lad = json.loads((ROOT / "results" / "routeA_r3" / "ladder_consistent" / "summary.json").read_text(encoding="utf-8"))
dm = json.loads((ROOT / "results" / "routeA_r3" / "drift_margin" / "summary.json").read_text(encoding="utf-8"))
R = lad["regimes"]
mn = lambda reg, arm: R[reg][arm]["summary"]["mean"]
deployed = {r: dm["regimes"][r]["arms"]["shield_fixed18"]["summary"]["mean"] for r in dm["regimes"]}
REG = ["1.2", "3.2", "4.4", "5.6"]
gaps = [mn(t, "oracle") - deployed[k] for t, k in zip(["nominal", "plus2s", "plus3p2s", "plus4p4s"], REG)]
oracle_sd = max(R[t]["oracle"]["summary"]["sd"] for t in ("nominal", "plus2s", "plus3p2s", "plus4p4s"))
lam_vs_none = [(t, mn(t, "reward_lam8") - mn(t, "no_knowledge")) for t in ("nominal", "plus2s", "plus3p2s", "plus4p4s")]

p = D / "paper_en.md"
t = p.read_text(encoding="utf-8")
i = t.find("Three readings. First,")
if i < 0:
    raise SystemExit("readings paragraph not found")
j = t.find("\n\n", t.find("policy around it was not,\" a distinction no other arm in this paper can make.", i))
NEW = (f"Three readings. First, the oracle is drift-immune by construction—{mn('nominal','oracle'):.2f} on every "
       f"grid point (sd {oracle_sd:.2f} across all ladder cells)—because it reads each attempt's realized "
       f"requirement. Second, the gap between the fixed threshold and the oracle opens only under drift "
       f"({', '.join('%.2f' % g for g in gaps)} pp at δ = 0/+2/+3.2/+4.4 s): that gap is the measured price of a "
       f"*fixed* threshold, and it is exactly what per-regime re-probing (Section VI-D) is designed to close. "
       f"Third, the ladder localizes the remaining loss to the ceiling: at nominal physics none of it is "
       f"estimation error (the deployed arm equals the oracle); it is target/window/routing—so a stronger "
       f"*controller* is what would be needed to close it, and Sections VI-B and VI-A measure how little the "
       f"current ones differ. A fourth reading belongs beside them, because it is the paper's sharpest negative "
       f"result: the reward-penalty arm falls *below* the no-knowledge policies at every drift level "
       f"({', '.join('%+.1f' % d for _, d in lam_vs_none)} pp), so a penalty trained on the nominal requirement is "
       f"worse than no knowledge once the requirement moves. The oracle is an upper reference, not a deployable "
       f"controller—the ladder presumes the realized requirement—but it separates \"the estimate was wrong\" from "
       f"\"the constraint was right and the policy around it was not,\" a distinction no other arm in this paper "
       f"can make.")
t = t[:i] + NEW + t[j:]
p.write_text(t, encoding="utf-8")
print("readings rewritten; gaps:", [round(g, 2) for g in gaps])
print("lam vs none:", [(a, round(b, 2)) for a, b in lam_vs_none])
