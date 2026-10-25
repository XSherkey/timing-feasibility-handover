"""R4 (v16): align the Table VIII commentary with the rebuilt numbers, and mirror the table into ZH."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / "almond-repro"
D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"

# ---------- EN: the sentence describing the orderings ----------------------
p = D / "paper_en.md"
t = p.read_text(encoding="utf-8")
old = ("All four orderings survive the change of window: shielded beats unshielded; the deployed algorithm is at or above "
       "the same-rule baseline; it lies within the ≤1.20 pp tolerance of the tuned constant; and the decision-layer "
       "shield beats the best reward penalty by 9–11 pp.")
new = ("All four orderings survive the change of window. Shielded beats unshielded in every instance: the deployed "
       "arm is 1.4–2.1 pp above the mined 16 s rule and 2.3–3.4 pp above the same-rule PPO-MLP baseline. The "
       "deployed arm and the tuned constant are within 0.03 pp of each other in all four instances (93.36 vs "
       "93.33, 91.67 vs 91.67, 93.03 vs 93.06, 92.91 vs 92.91)—the competition that the paper reports as a tie "
       "rather than a win. And the decision-layer shield beats the best reward penalty by 9.4–11.0 pp.")
if t.count(old) != 1:
    raise SystemExit(f"EN ordering sentence found {t.count(old)}")
t = t.replace(old, new, 1)
p.write_text(t, encoding="utf-8")
print("EN ordering sentence updated")

# ---------- ZH: Table VIII + commentary ------------------------------------
d = json.loads((ROOT / "results" / "routeA_r3" / "lockbox_consistent" / "summary.json").read_text(encoding="utf-8"))
ORDER = ["mined_16", "deployed_18", "tuned_constant", "ppomlp_mined_16", "reward_lam8", "oracle"]
LABEL = {"eval": "评估窗口 82–95%", "lb299.25": "lockbox +7 天（299.25）",
         "lb306.25": "lockbox +14 天（306.25）", "lb290.25": "lockbox −2 天（290.25）"}
rows = ["| 实例 | 挖出规则（16 s） | 部署（τ_used = 18 s） | 调好的常数 | PPO-MLP + 挖掘 16 s | 奖励 λ = 8 | oracle 盾 |",
        "|---|---|---|---|---|---|---|"]
for inst in ("eval", "lb299.25", "lb306.25", "lb290.25"):
    cell = d["instances"][inst]
    rows.append("| %s | %s |" % (LABEL[inst], " | ".join("%.2f" % cell[a]["summary"]["mean"] for a in ORDER)))
T8 = ("**表 VIII. 三路完整 lockbox（极区 HSR，|lat| ≥ 70°，campaign 策略、traffic seed 0，"
      "每个实例 n = 10 个策略种子；所有选择在验证窗口完成并在任何 lockbox rollout 之前冻结）。**\n\n"
      + "\n".join(rows) + "\n")

z = D / "paper_zh.md"
s = z.read_text(encoding="utf-8")
i = s.find("**表 VIII.")
j = s.find("\n\n", s.find("| lockbox −2 天", i))
if i < 0 or j < 0:
    raise SystemExit("ZH Table VIII block not found")
s = s[:i] + T8 + s[j:]
z.write_text(s, encoding="utf-8")
print("ZH Table VIII rebuilt")
print("\n".join(rows))
