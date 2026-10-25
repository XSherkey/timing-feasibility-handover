"""R5 ZH: mirror the factorial-number unification and the strengthened drift conclusion."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / "almond-repro"
D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"
fc = json.loads((ROOT / "results" / "routeA_r3" / "factorial_consistent" / "summary.json").read_text(encoding="utf-8"))
lad = json.loads((ROOT / "results" / "routeA_r3" / "ladder_consistent" / "summary.json").read_text(encoding="utf-8"))
A = fc["arms"]
R = lad["regimes"]
mn = lambda reg, arm: R[reg][arm]["summary"]["mean"]
sp = lambda k: (min(A[k]["polar"]), max(A[k]["polar"]))
late16 = sum(A["rule16"]["late"]) / len(A["rule16"]["late"])

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


# abstract
rep("极区切换成功率从 67.5% ± 13.2% 提升到 92.4% ± 0.3%，再加上 2 s 的代价不对称余量后为 93.3% ± 0.3%",
    f"极区切换成功率从 {A['none']['summary']['mean']:.1f}% ± {A['none']['summary']['sd']:.1f}% 提升到 "
    f"{A['rule16']['summary']['mean']:.2f}% ± {A['rule16']['summary']['sd']:.2f}%，再加上 2 s 的代价不对称余量后为 "
    f"{A['rule18']['summary']['mean']:.2f}% ± {A['rule18']['summary']['sd']:.2f}%", "abstract")

# introduction
rep("均值从 67.5% ± 13.2% 升至 93.3% ± 0.3%（部署值 τ = 18 s；挖掘值 τ∗ = 16 s 规则为 92.4% ± 0.3%），逐种子散布从 49.8–90.0% 坍缩到 92.7–93.7%（图 2）",
    f"均值从 {A['none']['summary']['mean']:.1f}% ± {A['none']['summary']['sd']:.1f}% 升至 "
    f"{A['rule18']['summary']['mean']:.2f}% ± {A['rule18']['summary']['sd']:.2f}%（部署值 τ = 18 s；挖掘值 τ∗ = 16 s 规则为 "
    f"{A['rule16']['summary']['mean']:.2f}% ± {A['rule16']['summary']['sd']:.2f}%），逐种子散布从 "
    f"{sp('none')[0]:.1f}–{sp('none')[1]:.1f}% 坍缩到 {sp('rule18')[0]:.1f}–{sp('rule18')[1]:.1f}%（图 2）",
    "intro")

# VI-B factorial sentence
rep("τ = 16 s 时收缩到 92.43 ± 0.30（晚切换 0.87%）。部署 τ = 18 s 臂达到 93.31 ± 0.26、晚切换 0.00%，且**高于** τ = 20 s 消融（93.17 ± 0.26、晚切换 0.00%）",
    f"τ = 16 s 时收缩到 {A['rule16']['summary']['mean']:.2f} ± {A['rule16']['summary']['sd']:.2f}（晚切换 "
    f"{late16:.2f}%）。部署 τ = 18 s 臂达到 {A['rule18']['summary']['mean']:.2f} ± "
    f"{A['rule18']['summary']['sd']:.2f}、晚切换 0.00%，且**高于** τ = 20 s 消融（"
    f"{A['rule20']['summary']['mean']:.2f} ± {A['rule20']['summary']['sd']:.2f}、晚切换 0.00%）", "viB")

# V-D sentence
rep("实测结果：部署 τ = 18 s 臂达到 93.31% ± 0.26（逐种子横跨 1.07 pp，晚切换占比 0.00%，n = 10），且**高于** τ = 20 s 消融（93.17% ± 0.26）",
    f"实测结果：部署 τ = 18 s 臂达到 {A['rule18']['summary']['mean']:.2f}% ± "
    f"{A['rule18']['summary']['sd']:.2f}（逐种子横跨 {sp('rule18')[1] - sp('rule18')[0]:.1f} pp，晚切换占比 0.00%，n = 10），"
    f"且**高于** τ = 20 s 消融（{A['rule20']['summary']['mean']:.2f}% ± {A['rule20']['summary']['sd']:.2f}）",
    "vD")

# Prop 1 residual
rep("（部署 τ = 18 s 臂：16 s 时仍有 0.87%，18 s 时为 0.00%）",
    f"（部署 τ = 18 s 臂：16 s 时仍有 {late16:.2f}%，18 s 时为 0.00%）", "p1-1")
rep("而那 0.87% 的残余恰恰是部署算法要带 2 s 余量的原因",
    f"而那 {late16:.2f}% 的残余恰恰是部署算法要带 2 s 余量的原因", "p1-2")
rep("若取 ā = 16 s 则结论不成立",
    "若取 ā = 16 s 则结论不成立", "p1-noop")

# cross-protocol sentence
rep("归档检查点集的 τ = 16 s 臂（92.44 ± 0.07）与重测臂（92.43 ± 0.30）均值一致到 0.01 pp",
    f"τ = 16 s 臂在本文所有数字所用的同一协议下读数为 {A['rule16']['summary']['mean']:.2f} ± "
    f"{A['rule16']['summary']['sd']:.2f}", "cross-protocol")

# appendix C lead
i = t.find("测量于架构固定副本集")
if i > 0:
    j = t.find("\n\n", i)
    t = t[:i] + ("两张表与图 5、表 VIII 使用同一 campaign 策略、同一 traffic seed 与同一回合；重跑各臂可逐种子逐位复现。") + t[j:]
    done.append("appc")

# Fig. 2 caption
i = t.find("**图 2.**")
if i > 0:
    j = t.find("\n\n", i)
    CAP = (f"**图 2.** 盾吸收计时因子。十个 campaign 检查点、共同回合、traffic seed 0：无盾时横跨 "
           f"{sp('none')[0]:.1f}–{sp('none')[1]:.1f}%（sd {A['none']['summary']['sd']:.1f}）；τ = 16 s 时压缩到 "
           f"{sp('rule16')[0]:.1f}–{sp('rule16')[1]:.1f}%（sd {A['rule16']['summary']['sd']:.2f}）；部署 τ = 18 s 臂横跨 "
           f"{sp('rule18')[0]:.1f}–{sp('rule18')[1]:.1f}%（sd {A['rule18']['summary']['sd']:.2f}），并高于 τ = 20 s 消融"
           f"（{sp('rule20')[0]:.1f}–{sp('rule20')[1]:.1f}%，sd {A['rule20']['summary']['sd']:.2f}）；逐尝试 oracle 在每个种子上与 "
           f"τ = 18 s 重合。逐种子散布从 ±{A['none']['summary']['sd']:.1f} 坍缩到 ±{A['rule18']['summary']['sd']:.2f} pp。")
    t = t[:i] + CAP + t[j:]
    done.append("fig2")

# strengthened conclusion
rep("真正承重的是标定与准入：",
    f"两项测量把这一点说得更硬：按标称需求训练出的奖励惩罚不只是\"不迁移\"——在 +2 s 漂移下它落到**低于**"
    f"它本想超越的无知识策略（{mn('plus2s','reward_lam8'):.1f}% 对 {mn('plus2s','no_knowledge'):.1f}%），"
    f"因为它把容量花在了一个已经移动的下界上。真正承重的是标定与准入：", "abs-strengthen")

z.write_text(t, encoding="utf-8")
print("applied:", done)
