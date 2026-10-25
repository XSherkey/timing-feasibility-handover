"""R5 ZH part 2: rebuild Tables C1-C3 and fix the remaining factorial references."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2] / "almond-repro"
D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"
fc = json.loads((ROOT / "results" / "routeA_r3" / "factorial_consistent" / "summary.json").read_text(encoding="utf-8"))
dm = json.loads((ROOT / "results" / "routeA_r3" / "drift_margin" / "summary.json").read_text(encoding="utf-8"))
A = fc["arms"]
late16 = sum(A["rule16"]["late"]) / len(A["rule16"]["late"])

z = D / "paper_zh.md"
t = z.read_text(encoding="utf-8")
done = []

# ---- Table C1 -------------------------------------------------------------
i = t.find("**表 C1.")
j = t.find("\n\n", t.find("| 晚切换占比", i))
rows = ["| 种子 | 无盾 | τ = 16 s（挖掘 τ∗） | τ = 20 s（消融） |", "|---|---|---|---|"]
for k in range(10):
    rows.append(f"| {k} | {A['none']['polar'][k]:.1f} | {A['rule16']['polar'][k]:.1f} | {A['rule20']['polar'][k]:.1f} |")
rows.append(f"| 均值 ± 标准差 | {A['none']['summary']['mean']:.1f} ± {A['none']['summary']['sd']:.1f} | "
            f"{A['rule16']['summary']['mean']:.2f} ± {A['rule16']['summary']['sd']:.2f} | "
            f"{A['rule20']['summary']['mean']:.2f} ± {A['rule20']['summary']['sd']:.2f} |")
rows.append(f"| 晚切换占比 | {min(A['none']['late']):.1f}–{max(A['none']['late']):.1f}%（均值 {np.mean(A['none']['late']):.1f}%） | "
            f"{min(A['rule16']['late']):.2f}–{max(A['rule16']['late']):.2f}%（均值 {np.mean(A['rule16']['late']):.2f}%） | — |")
C1 = ("**表 C1. 冻结策略因子化（campaign 检查点），极区 HSR（%）逐种子（|lat| ≥ 70°、traffic seed 0、共同回合）。**\n\n"
      + "\n".join(rows) + "\n")
t = t[:i] + C1 + t[j:]
done.append("C1")

# ---- Table C2 -------------------------------------------------------------
i = t.find("**表 C2.")
j = t.find("\n\n", t.find("| 晚切换占比", i))
rows = ["| 种子 | τ = 16 s | **τ = 18 s（部署 τ_used）** | τ = 20 s | oracle |", "|---|---|---|---|---|"]
for k in range(10):
    rows.append(f"| {k} | {A['rule16']['polar'][k]:.1f} | {A['rule18']['polar'][k]:.1f} | "
                f"{A['rule20']['polar'][k]:.1f} | {A['oracle']['polar'][k]:.1f} |")
rows.append(f"| 均值 ± 标准差 | {A['rule16']['summary']['mean']:.2f} ± {A['rule16']['summary']['sd']:.2f} | "
            f"**{A['rule18']['summary']['mean']:.2f} ± {A['rule18']['summary']['sd']:.2f}** | "
            f"{A['rule20']['summary']['mean']:.2f} ± {A['rule20']['summary']['sd']:.2f} | "
            f"{A['oracle']['summary']['mean']:.2f} ± {A['oracle']['summary']['sd']:.2f} |")
rows.append(f"| 晚切换占比 | {np.mean(A['rule16']['late']):.2f}% | **0.00%** | 0.00% | 0.00% |")
C2 = ("**表 C2. 部署阈值补齐与 oracle 参照，极区 HSR（%）逐种子（|lat| ≥ 70°、traffic seed 0、共同回合）。**\n\n"
      + "\n".join(rows) + "\n")
t = t[:i] + C2 + t[j:]
done.append("C2")

# ---- remaining references -------------------------------------------------
pairs = [
    ("oracle 臂在每一颗种子上都与 τ = 18 s 相等（93.31 ± 0.26）",
     f"oracle 臂在每一颗种子上都与 τ = 18 s 相等（{A['oracle']['summary']['mean']:.2f} ± {A['oracle']['summary']['sd']:.2f}）"),
    ("冻结因子化上，oracle 臂返回 93.31% ± 0.26（晚切换占比 0.00%）",
     f"冻结因子化上，oracle 臂返回 {A['oracle']['summary']['mean']:.2f}% ± {A['oracle']['summary']['sd']:.2f}（晚切换占比 0.00%）"),
    ("若用 ā = 16 s，就需要那 0.87% 残余为零，而它不是",
     f"若用 ā = 16 s，就需要那 {late16:.2f}% 残余为零，而它不是"),
    ("*注.* 此处的 0.6% 是 campaign 协议（训练期规则在环，十个种子）下的晚切换占比；冻结因子化对同一条 16 s 规则在共同回合上报告 0.87%（表 C1）。差异来自协议而非规则，且两个数字都不属于部署的 18 s 臂（0.00%）。",
     f"*注.* 这些占比与 HSR 列来自与图 5、表 VIII 评估行相同的十次运行：campaign 策略、traffic seed 0、相同回合。晚切换是约束所移除的失效类；窗口与路由失效在最好与最差臂之间移动不到一个点。"),
]
for old, new in pairs:
    if t.count(old) == 1:
        t = t.replace(old, new, 1)
        done.append(old[:26])
    else:
        print("  MISS:", t.count(old), old[:50])

# provenance note
old = "这一点很重要：本表的早期版本把架构固定副本集（表 C2 的因子化使用的那一套，其部署臂在评估窗口读数为 93.31）与逐个种子变化的 traffic seed 混在一起，两套协议在同一臂上相差约 1 pp，比历元平移本身的效应还大。因此表 VIII 只报告 campaign 策略，评估窗口那一行就是与 lockbox 各行比较的参照。"
new = "本文每一张表——附录 C 的因子化、图 5 的 headline 柱、表 VII 的隔离臂、以及这里的 lockbox 各行——现在都使用同一 campaign 策略、同一 traffic seed 与同一回合协议；表 VIII 各行之间唯一变化的就是孪生历元本身。"
if t.count(old) == 1:
    t = t.replace(old, new, 1)
    done.append("provenance")

z.write_text(t, encoding="utf-8")
print("applied:", done)
