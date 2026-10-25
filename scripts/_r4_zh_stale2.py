"""R4 (v22) ZH part 5: the three remaining Vietnamese-number paragraphs, with exact anchors."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / "almond-repro"
D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"
h = json.loads((ROOT / "results" / "routeA_r3" / "headline_consistent" / "summary.json").read_text(encoding="utf-8"))
A = h["arms"]
m = lambda k: A[k]["summary"]["mean"]
s = lambda k: A[k]["summary"]["sd"]
c = lambda k, key: 100.0 * A[k]["causes"].get(key, 0.0)

z = D / "paper_zh.md"
t = z.read_text(encoding="utf-8")
done = []


def rep(old, new, label):
    global t
    n = t.count(old)
    if n != 1:
        print(f"  MISS [{label}] {n}")
        return
    t = t.replace(old, new, 1)
    done.append(label)


rep("同一训练策略家族从无知识水平（冻结因子化无盾臂 67.5% ± 13.2%，表 C1；不挖掘 campaign 臂 78.9% ± 11.0%，表 II）爬到 λ = 8 处的 84.4% ± 6.8%——然后**反转**：81.8%（λ = 16）、81.2%（λ = 32）、74.5% ± 17.0%（λ = 64）。盾位于 93.6% ± 0.7%（campaign；冻结因子化上 93.3% ± 0.3%），比最优惩罚点高 9.2 pp，方差低一个量级。在 (HSR, S) 前沿上，盾不被任何惩罚点支配：它在可靠性（93.6 对 84.4）与北极带满足度（80.7 对 68.8）上同时更高。",
    f"同一训练策略家族从不挖掘知识的水平（{m('noforensics_none'):.1f}% ± {s('noforensics_none'):.1f}%，表 II）"
    f"爬到 λ = 8 处的 {m('lam8'):.1f}% ± {s('lam8'):.1f}%——然后**反转**：{m('lam16'):.1f}%（λ = 16）、"
    f"{m('lam32'):.1f}%（λ = 32）、{m('lam64'):.1f}% ± {s('lam64'):.1f}%（λ = 64）。部署的盾位于 "
    f"{m('almond_rule18'):.2f}% ± {s('almond_rule18'):.2f}%，比最优惩罚点高 "
    f"{m('almond_rule18') - m('lam8'):.1f} pp，方差低两个数量级。在 (HSR, S) 前沿上，盾不被任何惩罚点支配："
    f"它在可靠性（{m('almond_rule18'):.2f} 对 {m('lam8'):.1f}）与极区满足度"
    f"（{A['almond_rule18']['satisfaction_mean']:.1f} 对 {A['lam8']['satisfaction_mean']:.1f}）上同时更高。",
    "vic-body")

rep("因此 84.4% 是奖励通道上限的乐观估计。它支持的比较是一种上界比较，而结论在乐观偏差下依然成立：七个惩罚设定中最好的一个仍比盾低 9.2 pp。",
    f"因此 {m('lam8'):.1f}% 是奖励通道上限的乐观估计。它支持的比较是一种上界比较，而结论在乐观偏差下依然成立："
    f"七个惩罚设定中最好的一个仍比盾低 {m('almond_rule18') - m('lam8'):.1f} pp。", "vic-caveat")

rep("晚切换是唯一随臂显著变化的失效类：纯奖励基线为极区尝试的 22.1%，从不挖掘知识的同架构消融为 14.8%，全系统为 0.6%。窗口与路由失效几乎不动（全程约 2–4%）；盾用少量窗口违例换掉了它消除的晚切换，恰如式（3）所预言。",
    f"晚切换是唯一随臂显著变化的失效类：纯奖励基线为极区尝试的 {c('ppomlp_none','late_handover'):.1f}%，"
    f"从不挖掘知识的同架构消融为 {c('noforensics_none','late_handover'):.1f}%，挖出规则臂为 "
    f"{c('almond_rule16','late_handover'):.1f}%。窗口与路由失效在每行都不超过 "
    f"{c('almond_rule16','window_exceeded'):.1f}–{c('ppomlp_none','no_route'):.1f}%；盾用少量窗口违例"
    f"（{c('ppomlp_none','window_exceeded'):.1f}% → {c('almond_rule16','window_exceeded'):.1f}%）换掉了它消除的晚切换，"
    f"恰如式（3）所预言。", "zh-failure")

z.write_text(t, encoding="utf-8")
print("applied:", done)
