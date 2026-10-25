"""R4 (v22) ZH part 4: the remaining Chinese stale numbers (VI-C, VI-D, nomenclature, IV-A, ledger)."""
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


def rep(old, new, label):
    global t
    n = t.count(old)
    if n != 1:
        print(f"  MISS [{label}] {n}: {old[:60]}")
        return
    t = t.replace(old, new, 1)
    done.append(label)


# VI-C lambda numbers
rep("（67.5% ± 13.2% 在冻结因子化的无盾臂，表 C1；78.9% ± 11.0% 为不挖掘的 campaign 臂，表 II）爬到 λ = 8 处的 84.4% ± 6.8%——然后**反转**：81.8%（λ = 16）、81.2%（λ = 32）、74.5% ± 17.0%（λ = 64）。盾位于 93.6% ± 0.7%（campaign；冻结因子化 93.3% ± 0.3%），比最优惩罚点高 9.2 pp，方差小一个数量级。",
    f"（不挖掘的同架构臂 {m('noforensics_none'):.1f}% ± {s('noforensics_none'):.1f}%，表 II）爬到 λ = 8 处的 "
    f"{m('lam8'):.1f}% ± {s('lam8'):.1f}%——然后**反转**：{m('lam16'):.1f}%（λ = 16）、{m('lam32'):.1f}%（λ = 32）、"
    f"{m('lam64'):.1f}% ± {s('lam64'):.1f}%（λ = 64）。部署的盾位于 {m('almond_rule18'):.2f}% ± "
    f"{s('almond_rule18'):.2f}%，比最优惩罚点高 {m('almond_rule18') - m('lam8'):.1f} pp，方差小两个数量级"
    f"（{s('almond_rule18'):.2f} 对 {s('lam8'):.1f} pp）。", "vic-lambda")
rep("它同时具有更高的可靠性（93.6 对 84.4）与更高的极区满意度（80.7 对 68.8）",
    f"它同时具有更高的可靠性（{m('almond_rule18'):.2f} 对 {m('lam8'):.1f}）与更高的极区满意度"
    f"（{A['almond_rule18']['satisfaction_mean']:.1f} 对 {A['lam8']['satisfaction_mean']:.1f}）", "vic-frontier")
rep("所以 84.4% 是奖励通道上限的乐观估计。它支持的比较是上界比较，而结论在这种乐观下依然成立：七个惩罚设定中最好的一个仍比盾低 9.2 pp。",
    f"所以 {m('lam8'):.1f}% 是奖励通道上限的乐观估计。它支持的比较是上界比较，而结论在这种乐观下依然成立："
    f"七个惩罚设定中最好的一个仍比盾低 {m('almond_rule18') - m('lam8'):.1f} pp。", "vic-caveat")
rep("λ = 8 的策略从 84.4% 跌到 55.4%——跌到同一漂移阶梯上完全无知识策略的水平（54.6%；第六节 D 与图 8）。",
    f"λ = 8 的策略从 {mn('nominal','reward_lam8'):.1f}% 跌到 {mn('plus2s','reward_lam8'):.1f}%——**低于**同一阶梯上"
    f"完全无知识策略的水平（{mn('plus2s','no_knowledge'):.1f}%；第六节 D 与图 8）。按标称需求训练出的惩罚，"
    f"一旦需求移动就会主动伤害性能。", "vic-ladder")

# VI-D ladder listing
rep("无知识（74.5 → 54.6）、奖励 λ = 8（84.4 → 55.4）、LLM 叙事推断的 16 s 规则（92.5 → 85.1，因为其幅值不跟随物理）、调好的 18 s 常数（93.3 → 92.4）、部署的探测标定 τ_used = 18 s 盾（93.4 → 92.5）、逐尝试 oracle（93.4 → 93.4）",
    f"无知识（{mn('nominal','no_knowledge'):.1f} → {mn('plus2s','no_knowledge'):.1f}）、奖励 λ = 8"
    f"（{mn('nominal','reward_lam8'):.1f} → {mn('plus2s','reward_lam8'):.1f}）、LLM 叙事推断的 16 s 规则"
    f"（{mn('nominal','narrative_16s_rule'):.1f} → {mn('plus2s','narrative_16s_rule'):.1f}，因为其幅值不跟随物理）、"
    f"调好的 18 s 常数（{mn('nominal','tuned_constant_18'):.1f} → {mn('plus2s','tuned_constant_18'):.1f}）、"
    f"部署的探测标定 τ_used = 18 s 盾（{mn('nominal','deployed_probe_shield'):.1f} → "
    f"{mn('plus2s','deployed_probe_shield'):.1f}）、逐尝试 oracle（{mn('nominal','oracle'):.1f} → "
    f"{mn('plus2s','oracle'):.1f}）", "vid-ladder")

# nomenclature
rep("**挖出规则 campaign 臂**为 16 s 规则、不加余量（campaign 93.6%）",
    f"**挖出规则 campaign 臂**为 16 s 规则、不加余量（{m('almond_rule16'):.1f}%，|lat| ≥ 70°）", "nom1")
rep("**部署的探测标定算法**为同一条规则取 τ_used = 18 s（共同回合 93.31%）",
    f"**部署的探测标定算法**为同一条规则取 τ_used = 18 s（{m('almond_rule18'):.2f}%，|lat| ≥ 70°）", "nom2")
rep("**调好的常数**为最高仰角控制器 + 固定 18 s 提前量、无学习（94.0%）",
    f"**调好的常数**为最高仰角控制器 + 固定 18 s 提前量、无学习（{m('maxel18'):.1f}%）", "nom3")
rep("**oracle 盾**把每次尝试钳到其真实需求（上界参照，93.31%）",
    f"**oracle 盾**把每次尝试钳到其真实需求（上界参照，{m('oracle'):.2f}%）", "nom4")
rep("在标称物理下与挖出规则 campaign 臂持平（94.0% 对 93.6%）",
    f"在标称物理下与挖出规则 campaign 臂持平（{m('maxel18'):.2f}% 对 {m('almond_rule16'):.2f}%）", "intro-const")

# IV-A range and epsilon tail
rep("从纯奖励 campaign 臂的 22.1% 降到挖出规则 campaign 臂的 0.6%",
    f"从纯奖励 campaign 臂的 {c('ppomlp_none','late_handover'):.1f}% 降到挖出规则 campaign 臂的 "
    f"{c('almond_rule16','late_handover'):.1f}%", "iva-range")
rep("实测带盾后的晚切换占比为 0.6%（对 ε = 5%）",
    f"实测带盾后的晚切换占比为 {c('almond_rule16','late_handover'):.1f}%（对 ε = 5%）", "eps-tail")

# failure attribution (VI-B in ZH)
rep("晚切换是唯一随臂显著变化的失效类：纯奖励基线为极区尝试的 22.1%，从不挖掘知识的同架构消融为 14.8%，全系统为 0.6%。窗口与路由失效几乎不动（全程约 2–4%）；盾用少量窗口违例换掉了它所移除的晚切换，正是式 (3) 的预言。",
    f"晚切换是唯一随臂显著变化的失效类：纯奖励基线为极区尝试的 {c('ppomlp_none','late_handover'):.1f}%，"
    f"从不挖掘知识的同架构消融为 {c('noforensics_none','late_handover'):.1f}%，挖出规则臂为 "
    f"{c('almond_rule16','late_handover'):.1f}%。窗口与路由失效在每行都不超过 "
    f"{c('almond_rule16','window_exceeded'):.1f}–{c('ppomlp_none','no_route'):.1f}%；盾用少量窗口违例"
    f"（{c('ppomlp_none','window_exceeded'):.1f}% → {c('almond_rule16','window_exceeded'):.1f}%）换掉了它所移除的晚切换，"
    f"正是式 (3) 的预言。", "zh-failure")

z.write_text(t, encoding="utf-8")
print("applied:", done)
