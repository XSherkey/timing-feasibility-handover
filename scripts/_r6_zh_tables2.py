"""R7 ZH part 6: re-apply Table III, Table IX and the gate table (the earlier run aborted before writing)."""
from __future__ import annotations

import json
from pathlib import Path

D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"
ROOT = Path(__file__).resolve().parents[2] / "almond-repro"
h = json.loads((ROOT / "results" / "routeA_r3" / "headline_consistent" / "summary.json").read_text(encoding="utf-8"))
lk = json.loads((ROOT / "results" / "routeA_r3" / "lockbox_consistent" / "summary.json").read_text(encoding="utf-8"))
gs = json.loads((ROOT / "results" / "routeA_r3" / "gate_systematic" / "summary.json").read_text(encoding="utf-8"))
A, I = h["arms"], lk["instances"]

z = D / "paper_zh.md"
t = z.read_text(encoding="utf-8")
done = []

# ---- Table III -----------------------------------------------------------
i = t.find("**表 III.")
j = t.find("\n\n", t.find("| S |", i))
lams = ["0.3", "0.5", "2", "8", "16", "32", "64"]
T3 = ("**表 III. 惩罚剂量-反应（极区 HSR 与满意度 S，mean ± sd，n = 10；极区取 |lat| ≥ 70°，campaign 策略、"
      "traffic seed 0；盾列即表 IX 的部署探测标定算法）。**\n\n"
      "| λ | 0（无） | 0.3 | 0.5 | 2 | 8 | 16 | 32 | 64 | 盾 |\n"
      "|" + "---|" * 10 + "\n"
      f"| HSR | {A['noforensics_none']['summary']['mean']:.1f} | " +
      " | ".join(f"{A['lam'+k]['summary']['mean']:.1f}" for k in lams) +
      f" | **{A['almond_rule18']['summary']['mean']:.2f}** |\n"
      "| sd | " + f"{A['noforensics_none']['summary']['sd']:.1f} | " +
      " | ".join(f"{A['lam'+k]['summary']['sd']:.1f}" for k in lams) +
      f" | {A['almond_rule18']['summary']['sd']:.2f} |\n"
      "| S | " + f"{A['noforensics_none']['satisfaction_mean']:.1f} | " +
      " | ".join(f"{A['lam'+k]['satisfaction_mean']:.1f}" for k in lams) +
      f" | {A['almond_rule18']['satisfaction_mean']:.1f} |\n")
t = t[:i] + T3 + t[j:]
done.append("table3")

# ---- Table IX ------------------------------------------------------------
i = t.find("**表 IX.")
j = t.find("\n\n", t.find("| lockbox −2", i))
COLS = [("no_shield", "无盾（全）"), ("ppomlp_no_shield", "无盾（PPO）"), ("mined_16", "挖掘 16 s"),
        ("deployed_18", "部署 τ = 18 s"), ("tuned_constant", "调好常数"),
        ("ppomlp_mined_16", "PPO + 16 s"), ("reward_lam8", "奖励 λ = 8"), ("oracle", "oracle")]
LAB = {"eval": "评估窗口 82–95%（archival）", "lb299.25": "lockbox +7 d（three-way）",
       "lb306.25": "lockbox +14 d（three-way）", "lb290.25": "lockbox −2 d（three-way）"}
rows = ["| 实例 | " + " | ".join(l for _, l in COLS) + " |", "|" + "---|" * (len(COLS) + 1)]
for inst in ("eval", "lb299.25", "lb306.25", "lb290.25"):
    rows.append("| %s | %s |" % (LAB[inst], " | ".join("%.2f" % I[inst][a]["summary"]["mean"] for a, _ in COLS)))
T9 = ("**表 IX. 三路完整 lockbox（极区 HSR，|lat| ≥ 70°，campaign 策略、traffic seed 0，"
      "每个实例 n = 10 个策略种子）。**\n\n" + "\n".join(rows) + "\n")
t = t[:i] + T9 + t[j:]
done.append("table9")

# ---- gate table ----------------------------------------------------------
conf = gs["gate"]["short"]["confusion"]
G = gs["gate"]["short"]
i = t.find("**表 XI.")
if i < 0:
    raise SystemExit("ZH annotation table not found")
GATE = ("**表 X. 26 条候选上的审计门（与各候选在评估窗口上的实测效应做混淆矩阵；准入要求重放增益高于 5 pp "
        "且下界为正）。**\n\n"
        "| 候选类别 | 准入 | 拒绝 | 合计 |\n|---|---|---|---|\n"
        f"| 有害（实测效应 < 0） | {conf['harmful']['admit']} | {conf['harmful']['reject']} | "
        f"{conf['harmful']['admit'] + conf['harmful']['reject']} |\n"
        f"| 中性（0 ≤ 效应 < 5 pp） | {conf['neutral']['admit']} | {conf['neutral']['reject']} | "
        f"{conf['neutral']['admit'] + conf['neutral']['reject']} |\n"
        f"| 好（效应 ≥ 5 pp） | {conf['good']['admit']} | {conf['good']['reject']} | "
        f"{conf['good']['admit'] + conf['good']['reject']} |\n"
        f"| **合计** | **{G['n_admitted']}** | **{26 - G['n_admitted']}** | **26** |\n\n"
        f"两个重放预算下误纳 {G['false_accept']:.0%}、误拒 {G['false_reject']:.0%}。门开时准入集合把极区 HSR "
        f"平均提升 {G['hsr_gate_on_pp']:.1f} pp（每个准入候选 {G['mean_delta_admitted_pp']:.1f} pp）；"
        f"门关且放入最差准入候选时，同一测量读数为 {G['hsr_gate_off_worst_pp']:.1f} pp。\n\n")
t = t[:i] + GATE + t[i:]
done.append("gate")

z.write_text(t, encoding="utf-8")
print("applied:", done)
