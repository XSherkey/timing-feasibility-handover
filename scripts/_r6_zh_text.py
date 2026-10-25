"""R7 ZH part 3: text mirrors — Eq (1), nomenclature, protocols, non-monotone lambda, misc wording."""
from __future__ import annotations

import json
from pathlib import Path

D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"
ROOT = Path(__file__).resolve().parents[2] / "almond-repro"
h = json.loads((ROOT / "results" / "routeA_r3" / "headline_consistent" / "summary.json").read_text(encoding="utf-8"))
A = h["arms"]
m = lambda k: A[k]["summary"]["mean"]
s = lambda k: A[k]["summary"]["sd"]

z = D / "paper_zh.md"
t = z.read_text(encoding="utf-8")
done = []


def rep(old, new, label):
    global t
    n = t.count(old)
    if n != 1:
        print(f"  MISS [{label}] {n}: {old[:50]}")
        return
    t = t.replace(old, new, 1)
    done.append(label)


# Eq (1)
i = t.find("success   ⇔")
if i > 0:
    j = t.find("\n", i)
    t = t[:i] + "success   iff   route  and  a ≥ T_z  and  a ≤ V_z  and  elevation ≥ mask,             (1)" + t[j:]
    done.append("eq1")

# nomenclature escaped asterisk
rep("**τ\\*** 是", "**τ∗** 是", "nomen-tau")

# never exercise (two places)
rep("*被动日志从不触及的运营知识，必须离开奖励层、进入决策层*",
    "*被动日志覆盖得太薄、无法辨识的运营知识，必须离开奖励层、进入决策层*", "never-1")

# non-monotone lambda
i = t.find("同一训练策略家族从不挖掘知识的水平")
if i > 0:
    j = t.find("。部署的盾位于", i)
    t = (t[:i] + f"响应**并不单调，弱惩罚会主动伤害**：相对同架构的无惩罚臂（{m('noforensics_none'):.1f}% ± "
         f"{s('noforensics_none'):.1f}%），λ = 0.3 与 0.5 *损失* "
         f"{m('noforensics_none') - m('lam0.3'):.1f} 与 {m('noforensics_none') - m('lam0.5'):.1f} pp"
         f"（{m('lam0.3'):.1f}% 与 {m('lam0.5'):.1f}%）；曲线直到 λ = 2 才重新越过无惩罚水平（{m('lam2'):.1f}%），"
         f"在 λ = 8 达峰（{m('lam8'):.1f}% ± {s('lam8'):.1f}%），随后反转：{m('lam16'):.1f}%（λ = 16）、"
         f"{m('lam32'):.1f}%（λ = 32）、{m('lam64'):.1f}% ± {s('lam64'):.1f}%（λ = 64）" + t[j:])
    done.append("nonmonotone")

# kappa wording
rep("而与机械量规的 κ 为 0，因为该量规没有方差",
    "而与机械量规的 κ 是*未定义*而非 0——机械量规准入了每一条提案，没有可与操作判断相关的方差", "kappa")

# A8 arithmetic
rep("在标称物理下与盾的差在 0.02 pp 以内（bootstrap 95% CI [-0.06, 0.00]）",
    "在标称物理下与盾的差在 0.03 pp 以内（bootstrap 95% CI [-0.06, 0.00]）", "a8")

# six provenance variants
t = t.replace("七个来源变体落在全流水线的 0.11 pp 以内", "六个来源变体落在全流水线的 0.11 pp 以内")

# VI-D doubled constant
rep("（93.33% 对带盾的 93.36%；该控制器本身为 93.36%，见表 IV）",
    "（该常数 93.33%，部署盾在同一批回合上 93.36%，见表 IV）", "vid-constant")

# conclusion never-exercise
rep("*被动日志从不触及的运营知识*", "*被动日志覆盖得太薄、无法辨识的运营知识*", "never-2")

z.write_text(t, encoding="utf-8")
print("applied:", done)
