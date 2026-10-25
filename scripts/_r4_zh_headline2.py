"""R4 (v22) ZH mirror part 2: VI-B prose, VI-C numbers, Fig. 5 and Fig. 8 captions."""
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

# ---- VI-B ----------------------------------------------------------------
i = t.find("图 5 分解了文献式基线与全系统之间的差距")
j = t.find("\n\n", t.find("请读者在阅读其余部分时持有这一点。", i))
if j < 0:
    j = t.find("\n\n", t.find("请读者", i))
if i < 0 or j < 0:
    raise SystemExit("ZH VI-B block not found")
NEW = (
    f"图 5 分解了文献式基线与部署流水线之间的差距。五个柱子都在**同一协议**下测得——campaign 策略、"
    f"traffic seed 0、相同回合、十个策略种子——因此它们与表 II、表 VIII 的评估行可直接比较。\n\n"
    f"手工 PPO-MLP 基线（仅奖励）达 {m('ppomlp_none'):.1f}% ± {s('ppomlp_none'):.1f}%；同一条知识以奖励惩罚注入、"
    f"在最优系数 λ = 8 下达 {m('lam8'):.1f}% ± {s('lam8'):.1f}%；同一条知识作为决策盾施加到**基线自身**的策略上"
    f"达 {m('ppomlp_rule16'):.1f}% ± {s('ppomlp_rule16'):.1f}%；**挖出规则 campaign 臂**（16 s 盾、未加余量）达 "
    f"{m('almond_rule16'):.1f}% ± {s('almond_rule16'):.2f}%；一条无学习的**调好常数**（最高仰角候选 + 固定 18 s 提前量）"
    f"达 {m('maxel18'):.1f}%。作为参照，部署的探测标定算法（τ_used = 18 s）为 {m('almond_rule18'):.2f}% ± "
    f"{s('almond_rule18'):.2f}%。这四个名称——挖出规则 campaign 臂、部署的探测标定算法、调好的常数、oracle 盾——"
    f"在全文其余部分一致使用（第五节 D 的阈值台账）。\n\n"
    f"分解在单一协议内是纯算术：从纯奖励基线到挖出规则臂的总差距为 "
    f"{m('almond_rule16') - m('ppomlp_none'):.1f} pp，其中 {m('ppomlp_rule16') - m('ppomlp_none'):.1f} pp "
    f"来自把约束作为盾施加到**基线自身**的策略上，剩下 {m('almond_rule16') - m('ppomlp_rule16'):.1f} pp "
    f"才是全系统训练在带盾基线之上所加的一切。承重的是约束，不是学习器。由于本小节所有数字与表 II、III、VIII "
    f"来自同一批运行，此前关于\"campaign 协议与共同回合因子化混用\"的告诫已经解除：只剩一个协议需要对齐，"
    f"而这段文字用的就是它。")
t = t[:i] + NEW + t[j:]
done.append("viB")

# ---- Fig. 5 caption ------------------------------------------------------
i = t.find("**图 5.** 差距从何而来")
j = t.find("\n\n", i)
CAP5 = (f"**图 5.** 差距从何而来。极区 HSR，|lat| ≥ 70°，campaign 策略、traffic seed 0、相同回合，n = 10 个策略种子，"
        f"误差棒为 ±sd：纯奖励 PPO-MLP {m('ppomlp_none'):.1f}；同一条知识以最优系数（λ = 8）写入奖励 "
        f"{m('lam8'):.1f}；同一条知识作为盾施加到基线自身策略 {m('ppomlp_rule16'):.1f}；挖出规则 campaign 臂"
        f"（16 s 盾、未加余量）{m('almond_rule16'):.1f}；调好的常数（18 s、无学习）{m('maxel18'):.1f}。"
        f"部署的探测标定算法（τ_used = 18 s）为 {m('almond_rule18'):.2f} ± {s('almond_rule18'):.2f}。"
        f"五根柱来自同一协议，柱间差异因此不含协议成分；分解（24.1 pp 中 23.4 pp 来自约束）见第六节 B。")
t = t[:i] + CAP5 + t[j:]
done.append("fig5")

# ---- Fig. 8 caption ------------------------------------------------------
i = t.find("**图 8.** 六个参照系在同一根轴上")
j = t.find("\n\n", i)
CAP8 = (f"**图 8.** 六个参照系在同一根轴上（标称物理与 +2 s 建链漂移；campaign 策略、traffic seed 0、相同回合，"
        f"n = 10 个策略种子，误差棒 ±sd）：无知识（{mn('nominal','no_knowledge'):.1f} → {mn('plus2s','no_knowledge'):.1f}）、"
        f"奖励 λ = 8（{mn('nominal','reward_lam8'):.1f} → {mn('plus2s','reward_lam8'):.1f}）、"
        f"叙事推断的 16 s 规则（{mn('nominal','narrative_16s_rule'):.1f} → {mn('plus2s','narrative_16s_rule'):.1f}）、"
        f"调好的 18 s 常数（{mn('nominal','tuned_constant_18'):.1f} → {mn('plus2s','tuned_constant_18'):.1f}）、"
        f"部署的探测标定盾（{mn('nominal','deployed_probe_shield'):.1f} → {mn('plus2s','deployed_probe_shield'):.1f}）、"
        f"逐尝试 oracle（{mn('nominal','oracle'):.1f} → {mn('plus2s','oracle'):.1f}）。奖励注入最终**低于**无知识，"
        f"叙事规则损失 {mn('nominal','narrative_16s_rule') - mn('plus2s','narrative_16s_rule'):.1f} pp，"
        f"只有可重新测量的参照留在原位。")
t = t[:i] + CAP8 + t[j:]
done.append("fig8")

z.write_text(t, encoding="utf-8")
print("applied:", done)
