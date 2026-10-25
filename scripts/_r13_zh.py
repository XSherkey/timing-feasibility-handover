"""R14 part 6: Chinese mirror of the protocol sentence, 0/0 scope, oracle headroom, Table Xb and D2."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from scipy import stats

ROOT = Path(__file__).resolve().parents[2] / "almond-repro"
D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"
lk = json.loads((ROOT / "results" / "routeA_r3" / "lockbox_consistent" / "summary.json").read_text(encoding="utf-8"))
gs = json.loads((ROOT / "results" / "routeA_r3" / "gate_systematic" / "summary.json").read_text(encoding="utf-8"))
I = lk["instances"]
INSTS = ["eval", "lb299.25", "lb306.25", "lb290.25"]
rng = np.random.default_rng(9)

z = D / "paper_zh.md"
t = z.read_text(encoding="utf-8")
done = []


def repz(old, new, label):
    global t
    n = t.count(old)
    if n != 1:
        print(f"  MISS [{label}] {n}: {old[:40]}")
        return
    t = t.replace(old, new, 1)
    done.append(label)


repz("**系统提示（原文，未改写）。**", "**完整 prompt（系统 + 用户，原文，未改写）。**", "label")

old = ("表 X 的每一行都由同一策略集、同一 traffic seed 与同一回合协议产生，行与行之间唯一变化的是孪生历元。")
new = ("表 X 的每一行都使用同一策略集、同一 traffic seed 与同一批回合，因此行与行之间的差异不是协议差异；"
       "但四列之间协议并不相同：第一列是 archival 评估窗口实例化（三项选择在其所报告的窗口上被评估），"
       "后三列是 three-way lockbox 实例（所有选择在验证窗口完成，该列窗口只被评分）。"
       "在后三列之内，唯一变化的是孪生历元。")
if t.count(old) == 1:
    t = t.replace(old, new, 1)
    done.append("same-protocol")
else:
    print("  same-protocol count", t.count(old))

old2 = "反事实回放门（0 误纳、0 误拒）"
new2 = "反事实回放门（在该 bank 上 0 误纳、0 误拒；三条中性候选按构造被拒，而非依判断拒绝）"
if t.count(old2) == 1:
    t = t.replace(old2, new2, 1)
    done.append("contrib-00")

old3 = "审计门在 26 条候选上既未误纳有害项、也未误拒好项"
new3 = "审计门在我们构造的 26 条候选 bank 上既未误纳有害项、也未误拒好项（中性项不计入，因门槛按构造拒绝它们）"
if t.count(old3) == 1:
    t = t.replace(old3, new3, 1)
    done.append("abstract-00")

# Table Xb in Chinese
rows = ["| 对比 | 均值差（pp） | 配对 95% CI | 精确 Wilcoxon p | TOST p（margin 1.0 pp） |",
        "|---|---|---|---|---|"]
for base, name in (("mined_16", "部署 − 挖掘 16 s"), ("ppomlp_mined_16", "部署 − PPO-MLP + 16 s"),
                   ("tuned_constant", "部署 − 调好常数"), ("reward_lam8", "部署 − 奖励 λ = 8")):
    vals = []
    for i in INSTS:
        d = np.array(I[i]["deployed_18"]["polar"]) - np.array(I[i][base]["polar"])
        boot = np.array([rng.choice(d, size=d.size, replace=True).mean() for _ in range(10000)])
        lo, hi = np.percentile(boot, [2.5, 97.5])
        pv = 1.0 if np.allclose(d, 0) else float(stats.wilcoxon(d, zero_method="wilcox").pvalue)
        vals.append((d.mean(), lo, hi, pv))
    tost = "< 0.001" if base == "tuned_constant" else "—"
    rows.append(f"| {name} | {np.mean([v[0] for v in vals]):+.2f} | "
                f"{min(v[1] for v in vals):+.2f} ~ {max(v[2] for v in vals):+.2f} | "
                f"≤ {max(v[3] for v in vals):.3f} | {tost} |")
STAT = ("**表 Xb. 表 X 四条排序的配对统计**（在十个策略种子上配对；区间为四个实例自助 95% CI 的并集范围，"
        "p 值为四个精确 Wilcoxon 检验中的最大值）。\n\n" + "\n".join(rows) + "\n")
anchor = "**表 X. Lockbox vs evaluation window" if "Lockbox vs evaluation window" in t else "**表 X."
i = t.find(anchor)
if i > 0:
    j = t.find("\n\n", i)
    # insert after the lockbox table block
    k = t.find("\n\n", t.find("| oracle 盾", i))
    t = t[:k] + "\n\n" + STAT + t[k:]
    done.append("ZH-Xb")

# ZH D2 narrower
bank = sorted(gs["bank"], key=lambda b: b["id"])
rows = ["| id | 增益（pp） | 判定 | 标签 | 谓词 |", "|---|---|---|---|---|"]
for b in bank:
    rows.append(f"| {b['id']} | {b['delta_short']:+.1f} | {'准入' if b['admit_short'] else '拒绝'} | {b['class']} | `{b['rule']}` |")
D2 = ("**表 D2. 完整的 26 条候选门银行。** 增益列是门真正使用的验证窗口重放增益；标签由评估窗口效应事后赋予、"
      "从不作为输入。三条中性候选按构造被拒（准入要求增益高于 5 pp），因此不计入误拒——误拒只在「有害对好」"
      "这一判定上定义。谓词按实际执行原样给出。**\n\n" + "\n".join(rows) + "\n")
i = t.find("**表 D2.")
if i > 0:
    j = t.find("\n\n", t.find("| G26 |", i))
    t = t[:i] + D2 + t[j:]
    done.append("ZH-D2")

z.write_text(t, encoding="utf-8")
print("applied:", done)
