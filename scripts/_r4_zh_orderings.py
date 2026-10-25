"""R4 (v22) ZH part 3: regenerate the ordering paragraph and purge the rest of the stale numbers."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / "almond-repro"
D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"
lk = json.loads((ROOT / "results" / "routeA_r3" / "lockbox_consistent" / "summary.json").read_text(encoding="utf-8"))
h = json.loads((ROOT / "results" / "routeA_r3" / "headline_consistent" / "summary.json").read_text(encoding="utf-8"))
lad = json.loads((ROOT / "results" / "routeA_r3" / "ladder_consistent" / "summary.json").read_text(encoding="utf-8"))
A = h["arms"]
m = lambda k: A[k]["summary"]["mean"]
s = lambda k: A[k]["summary"]["sd"]
c = lambda k, key: 100.0 * A[k]["causes"].get(key, 0.0)
I = lk["instances"]
lm = lambda inst, arm: I[inst][arm]["summary"]["mean"]
INSTS = ["eval", "lb299.25", "lb306.25", "lb290.25"]
R = lad["regimes"]
mn = lambda reg, arm: R[reg][arm]["summary"]["mean"]

fmt = lambda vals, p=2: "/".join(f"{v:.{p}f}" for v in vals)
gain_lo = min(lm(i, "deployed_18") - lm(i, "no_shield") for i in INSTS)
gain_hi = max(lm(i, "deployed_18") - lm(i, "no_shield") for i in INSTS)
same_rule = [lm(i, "mined_16") - lm(i, "ppomlp_mined_16") for i in INSTS]
deploy_gap = [lm(i, "deployed_18") - lm(i, "ppomlp_mined_16") for i in INSTS]
lam_gap = [lm(i, "deployed_18") - lm(i, "reward_lam8") for i in INSTS]
const_gap = [abs(lm(i, "deployed_18") - lm(i, "tuned_constant")) for i in INSTS]

z = D / "paper_zh.md"
t = z.read_text(encoding="utf-8")
done = []

# ---- ordering paragraph ---------------------------------------------------
i = t.find("检验四条排序，每条都给出显式配对")
j = t.find("\n\n", t.find("系统的价值不在于更强的控制器，而在于约束本身", i))
if i < 0 or j < 0:
    raise SystemExit(f"ZH ordering paragraph not found ({i},{j})")
PARA = (
    "检验四条排序，每条都给出显式配对，且下面每个数字都读自表 VIII——同一策略集、同一 traffic seed、同一回合协议。"
    f"(i) **同一策略族内**，盾在同一批回合上优于无盾：全系统策略 "
    f"{fmt([lm(i,'deployed_18') for i in INSTS])} 对 {fmt([lm(i,'no_shield') for i in INSTS])}，"
    f"PPO-MLP {fmt([lm(i,'ppomlp_mined_16') for i in INSTS])} 对 "
    f"{fmt([lm(i,'ppomlp_no_shield') for i in INSTS])}——部署算法带来 {gain_lo:.1f}–{gain_hi:.1f} pp 的提升。"
    "(ii) **同一规则下的控制器族对比**（同口径配对）：全系统+挖掘 16 s 对 PPO-MLP+挖掘 16 s，即 "
    f"{fmt([lm(i,'mined_16') for i in INSTS])} 对 {fmt([lm(i,'ppomlp_mined_16') for i in INSTS])}"
    f"（{'、'.join('%+.2f' % x for x in same_rule)} pp）。两个策略族仍难以区分，与第六节 B 在原回合上的报告一致。"
    "(iii) 部署算法对基线在其自身最优规则下："
    f"{fmt([lm(i,'deployed_18') for i in INSTS])} 对 {fmt([lm(i,'ppomlp_mined_16') for i in INSTS])}，"
    f"差距为 {'、'.join('%.2f' % x for x in deploy_gap)} pp，故申明容差为 **≤ {max(deploy_gap):.1f} pp**。"
    "(iv) 决策层盾对最优奖励惩罚："
    f"{fmt([lm(i,'deployed_18') for i in INSTS])} 对 {fmt([lm(i,'reward_lam8') for i in INSTS])}，即 "
    f"{min(lam_gap):.1f}–{max(lam_gap):.1f} pp。"
    "另有两点须与排序同时给出。**无盾**情形并不利于全系统策略：PPO-MLP 无盾为 "
    f"{fmt([lm(i,'ppomlp_no_shield') for i in INSTS])}，全系统无盾为 {fmt([lm(i,'no_shield') for i in INSTS])}，"
    "因此在这一轴上我们不为学习到的控制器主张任何优势。部署算法与调好的常数在四个实例上相差不超过 "
    f"{max(const_gap):.2f} pp——本文把这当作平局报告，而不是胜负。")
t = t[:i] + PARA + t[j:]
done.append("orderings")

z.write_text(t, encoding="utf-8")
print("applied:", done)
