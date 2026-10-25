"""R4 (v22) ZH mirror: Tables II/III, VI-B, VI-C, Fig. 5 and Fig. 8 captions."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / "almond-repro"
D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"
h = json.loads((ROOT / "results" / "routeA_r3" / "headline_consistent" / "summary.json").read_text(encoding="utf-8"))
lad = json.loads((ROOT / "results" / "routeA_r3" / "ladder_consistent" / "summary.json").read_text(encoding="utf-8"))
A = h["arms"]
m = lambda k: A[k]["summary"]["mean"]
s = lambda k: A[k]["summary"]["sd"]
c = lambda k, key: 100.0 * A[k]["causes"].get(key, 0.0)
R = lad["regimes"]
mn = lambda reg, arm: R[reg][arm]["summary"]["mean"]

z = D / "paper_zh.md"
t = z.read_text(encoding="utf-8")
done = []

# ---- Table II ------------------------------------------------------------
i = t.find("**表 II.")
if i < 0:
    raise SystemExit("ZH Table II not found")
j = t.find("\n\n", t.find("| **挖出规则 campaign 臂", i)) if t.find("| **挖出规则 campaign 臂", i) > 0 else t.find("\n\n", t.find("|", i + 10))
T2 = ("**表 II. 失效归因，极区带（占尝试比例；站点 |lat| ≥ 70°，campaign 策略、traffic seed 0、共同回合，n = 10）。**\n\n"
      "| 臂 | 晚切换（%） | 窗口超限（%） | 无路由（%） | 极区 HSR（%） |\n|---|---|---|---|---|\n"
      f"| PPO-MLP（仅奖励） | {c('ppomlp_none','late_handover'):.1f} | {c('ppomlp_none','window_exceeded'):.1f} | "
      f"{c('ppomlp_none','no_route'):.1f} | {m('ppomlp_none'):.1f} ± {s('ppomlp_none'):.1f} |\n"
      f"| 同架构、不挖掘 | {c('noforensics_none','late_handover'):.1f} | {c('noforensics_none','window_exceeded'):.1f} | "
      f"{c('noforensics_none','no_route'):.1f} | {m('noforensics_none'):.1f} ± {s('noforensics_none'):.1f} |\n"
      f"| **挖出规则 campaign 臂（16 s）** | **{c('almond_rule16','late_handover'):.1f}** | "
      f"{c('almond_rule16','window_exceeded'):.1f} | {c('almond_rule16','no_route'):.1f} | "
      f"**{m('almond_rule16'):.1f} ± {s('almond_rule16'):.2f}** |\n")
t = t[:i] + T2 + t[j:]
done.append("table2")

# ---- Table III -----------------------------------------------------------
i = t.find("**表 III.")
if i < 0:
    raise SystemExit("ZH Table III not found")
j = t.find("\n\n", t.find("| S |", i))
lams = ["0.3", "0.5", "2", "8", "16", "32", "64"]
T3 = ("**表 III. 惩罚剂量-反应（极区 HSR 与满意度 S，mean ± sd，n = 10；极区取 |lat| ≥ 70°，campaign 策略、"
      "traffic seed 0；盾列即表 VIII 的部署探测标定算法）。**\n\n"
      "| λ | " + " | ".join(lams) + " | 盾（部署） |\n"
      "|" + "---|" * (len(lams) + 2) + "\n"
      "| HSR | " + " | ".join(f"{m('lam'+k):.1f}" for k in lams) + f" | **{m('almond_rule18'):.2f}** |\n"
      "| sd | " + " | ".join(f"{s('lam'+k):.1f}" for k in lams) + f" | {s('almond_rule18'):.2f} |\n"
      "| S | " + " | ".join(f"{A['lam'+k]['satisfaction_mean']:.1f}" for k in lams) +
      f" | {A['almond_rule18']['satisfaction_mean']:.1f} |\n")
t = t[:i] + T3 + t[j:]
done.append("table3")

z.write_text(t, encoding="utf-8")
print("ZH tables updated:", done)
