"""R4 (v16) part 4: rebuild Table VIII with the no-shield arm and regenerate every number in the
four-orderings paragraph from the same JSON, so the text cannot drift from the table again."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / "almond-repro"
D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"
d = json.loads((ROOT / "results" / "routeA_r3" / "lockbox_consistent" / "summary.json").read_text(encoding="utf-8"))
I = d["instances"]
INSTS = ["eval", "lb299.25", "lb306.25", "lb290.25"]
LABEL = {"eval": "evaluation window 82–95%", "lb299.25": "lockbox +7 d (299.25)",
         "lb306.25": "lockbox +14 d (306.25)", "lb290.25": "lockbox −2 d (290.25)"}


def m(inst: str, arm: str) -> float:
    return I[inst][arm]["summary"]["mean"]


COLS = [("no_shield", "no shield (full-system)"), ("mined_16", "mined rule (16 s)"),
        ("deployed_18", "deployed (τ_used = 18 s)"), ("tuned_constant", "tuned constant"),
        ("ppomlp_mined_16", "PPO-MLP + mined 16 s"), ("reward_lam8", "reward λ = 8"),
        ("oracle", "oracle shield")]
rows = ["| instance | " + " | ".join(lbl for _, lbl in COLS) + " |",
        "|" + "---|" * (len(COLS) + 1)]
for inst in INSTS:
    rows.append("| %s | %s |" % (LABEL[inst], " | ".join("%.2f" % m(inst, a) for a, _ in COLS)))
TABLE = ("**Table VIII. Full three-way lockbox (polar HSR, |lat| ≥ 70°, campaign policies, traffic seed 0, "
         "n = 10 policy seeds per instance; every selection made on the validation window and frozen "
         "before any lockbox rollout).**\n\n" + "\n".join(rows) + "\n")

p = D / "paper_en.md"
t = p.read_text(encoding="utf-8")
start = t.find("**Table VIII. Full three-way lockbox")
end = t.find("\n\n", t.find("| lockbox −2 d", start))
if start < 0 or end < 0:
    raise SystemExit("Table VIII block not found")
t = t[:start] + TABLE + t[end:]

# ---- the four-orderings paragraph, regenerated -----------------------------
gain_lo = min(m(i, "deployed_18") - m(i, "no_shield") for i in INSTS)
gain_hi = max(m(i, "deployed_18") - m(i, "no_shield") for i in INSTS)
same_rule = [m(i, "mined_16") - m(i, "ppomlp_mined_16") for i in INSTS]
deploy_gap = [m(i, "deployed_18") - m(i, "ppomlp_mined_16") for i in INSTS]
lam_gap = [m(i, "deployed_18") - m(i, "reward_lam8") for i in INSTS]
const_gap = [abs(m(i, "deployed_18") - m(i, "tuned_constant")) for i in INSTS]
unsh_full = [m(i, "no_shield") for i in INSTS]
unsh_ppo = [m(i, "ppomlp_no_shield") for i in INSTS]

fmt = lambda xs, p=2: "/".join(f"{x:.{p}f}" for x in xs)
PARA = (
    "Four orderings are tested, each with an explicit pairing, and every number below is read from "
    "Table VIII—one policy set, one traffic seed, one episode protocol. "
    "(i) *Within a policy family*, the shield beats no shield on identical episodes: full-system "
    f"{fmt([m(i,'deployed_18') for i in INSTS])} against {fmt(unsh_full)}, and PPO-MLP "
    f"{fmt([m(i,'ppomlp_mined_16') for i in INSTS])} against {fmt(unsh_ppo)}—a gain of "
    f"{gain_lo:.1f}–{gain_hi:.1f} pp for the deployed algorithm. "
    "(ii) *Controller families under the same rule*—the apples-to-apples pairing: full + mined 16 s vs "
    f"PPO-MLP + mined 16 s, i.e. {fmt([m(i,'mined_16') for i in INSTS])} vs "
    f"{fmt([m(i,'ppomlp_mined_16') for i in INSTS])} "
    f"({', '.join('%+.2f' % x for x in same_rule)} pp). The families remain hard to tell apart, exactly "
    "as Section VI-B reports on the original episodes. "
    "(iii) The deployed algorithm against the baseline under its own best rule: "
    f"{fmt([m(i,'deployed_18') for i in INSTS])} vs {fmt([m(i,'ppomlp_mined_16') for i in INSTS])}, "
    f"gaps of {', '.join('%.2f' % x for x in deploy_gap)} pp, so the stated tolerance is "
    f"**≤ {max(deploy_gap):.1f} pp**. "
    "(iv) The decision-layer shield against the best reward penalty: "
    f"{fmt([m(i,'deployed_18') for i in INSTS])} vs {fmt([m(i,'reward_lam8') for i in INSTS])}, i.e. "
    f"{min(lam_gap):.1f}–{max(lam_gap):.1f} pp. "
    "Two further facts belong with the orderings. The *unshielded* comparison does not favour the "
    f"full-system policies: PPO-MLP without a shield reads {fmt(unsh_ppo)} against {fmt(unsh_full)}, so "
    "we claim nothing for the learned controller on that axis. And the deployed algorithm and the tuned "
    f"constant stay within {max(const_gap):.2f} pp of each other in all four instances—the competition "
    "this paper reports as a tie, not a win.")

s = t.find("Four orderings are tested, each with an explicit pairing.")
e = t.find("\n\n", t.find("Subject to that reading, the headline numbers are independent", s))
if s < 0 or e < 0:
    raise SystemExit("orderings paragraph not found")
t = t[:s] + PARA + t[e:]
p.write_text(t, encoding="utf-8")
print("Table VIII + orderings regenerated")
print(f"gain {gain_lo:.2f}-{gain_hi:.2f} | same-rule {same_rule} | deploy gap {deploy_gap} | lam {lam_gap} | const {const_gap}")
