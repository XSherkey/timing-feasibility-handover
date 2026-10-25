"""Bring the Chinese lockbox table to the same eight columns as the English one."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / "almond-repro"
D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"
lk = json.loads((ROOT / "results" / "routeA_r3" / "lockbox_consistent" / "summary.json").read_text(encoding="utf-8"))
I = lk["instances"]
INSTS = ["eval", "lb299.25", "lb306.25", "lb290.25"]
LABEL = {"eval": "评估窗口 82–95%", "lb299.25": "lockbox +7 d（299.25）",
         "lb306.25": "lockbox +14 d（306.25）", "lb290.25": "lockbox −2 d（290.25）"}
COLS = [("no_shield", "无盾（全系统）"), ("mined_16", "挖出规则（16 s）"),
        ("deployed_18", "部署（τ_used = 18 s）"), ("tuned_constant", "调好的常数"),
        ("ppomlp_mined_16", "PPO-MLP + 挖掘 16 s"), ("reward_lam8", "奖励 λ = 8"),
        ("oracle", "oracle 盾")]
rows = ["| 实例 | " + " | ".join(lbl for _, lbl in COLS) + " |", "|" + "---|" * (len(COLS) + 1)]
for inst in INSTS:
    rows.append("| %s | %s |" % (LABEL[inst],
                                 " | ".join("%.2f" % I[inst][a]["summary"]["mean"] for a, _ in COLS)))

z = D / "paper_zh.md"
t = z.read_text(encoding="utf-8")
i = t.find("**表 IX. 三路完整 lockbox")
j = t.find("\n\n", t.find("| 实例 |", i))
if i < 0 or j < 0:
    raise SystemExit("ZH lockbox table not found")
T = ("**表 IX. 三路完整 lockbox（极区 HSR，|lat| ≥ 70°，campaign 策略、traffic seed 0，"
     "每个实例 n = 10 个策略种子；所有选择在验证窗口完成并在任何 lockbox rollout 之前冻结）。**\n\n"
     + "\n".join(rows) + "\n")
t = t[:i] + T + t[j:]
z.write_text(t, encoding="utf-8")
print("ZH lockbox table rebuilt with 8 columns")
