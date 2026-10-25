"""R4 (v16): rebuild the Chinese Table VIII with the consistent numbers."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / "almond-repro"
D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"
d = json.loads((ROOT / "results" / "routeA_r3" / "lockbox_consistent" / "summary.json").read_text(encoding="utf-8"))

ORDER = ["mined_16", "deployed_18", "tuned_constant", "ppomlp_mined_16", "reward_lam8", "oracle"]
LABEL = {"eval": "评估窗口 82–95%", "lb299.25": "lockbox +7 d（299.25）",
         "lb306.25": "lockbox +14 d（306.25）", "lb290.25": "lockbox −2 d（290.25）"}
rows = ["| 实例 | 挖出规则（16 s） | 部署（τ_used = 18 s） | 调好的常数 | PPO-MLP + 挖掘 16 s | 奖励 λ = 8 | oracle 盾 |",
        "|---|---|---|---|---|---|---|"]
for inst in ("eval", "lb299.25", "lb306.25", "lb290.25"):
    cell = d["instances"][inst]
    rows.append("| %s | %s |" % (LABEL[inst], " | ".join("%.2f" % cell[a]["summary"]["mean"] for a in ORDER)))

T8 = ("**表 VIII. 三路完整 lockbox（极区 HSR，|lat| ≥ 70°，campaign 策略、traffic seed 0，"
      "每个实例 n = 10 个策略种子；所有选择在验证窗口完成并在任何 lockbox rollout 之前冻结）。**\n\n"
      + "\n".join(rows) + "\n\n"
      "表 VIII 的每一行都由同一策略集、同一 traffic seed 与同一回合协议产生，行与行之间唯一变化的是孪生历元。"
      "这一点很重要：本表的早期版本把架构固定副本集（表 C2 的因子化使用的那一套，其部署臂在评估窗口读数为 93.31）"
      "与逐个种子变化的 traffic seed 混在一起，两套协议在同一臂上相差约 1 pp，比历元平移本身的效应还大。"
      "因此表 VIII 只报告 campaign 策略，评估窗口那一行就是与 lockbox 各行比较的参照。\n\n"
      "四条排序在换窗后全部存活：盾在每个实例上都优于无盾（部署臂比挖掘 16 s 规则高 1.4–2.1 pp，"
      "比同规则 PPO-MLP 基线高 2.3–3.4 pp）；部署臂与调好的常数在四个实例上都相差不超过 0.03 pp"
      "（93.36 对 93.33、91.67 对 91.67、93.03 对 93.06、92.91 对 92.91）——这正是本文报告的平局而非胜负；"
      "而决策层盾比最优奖励惩罚高 9.4–11.0 pp。\n")

z = D / "paper_zh.md"
s = z.read_text(encoding="utf-8")
i = s.find("**表 VIII.")
if i < 0:
    raise SystemExit("ZH table VIII caption not found")
j = s.find("\n\n### J.", i)
if j < 0:
    raise SystemExit("ZH section J not found")
s = s[:i] + T8 + s[j:]
z.write_text(s, encoding="utf-8")
print("ZH Table VIII rebuilt")
