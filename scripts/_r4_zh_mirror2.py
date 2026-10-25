"""R4 (v16) ZH: duplicate lockbox table, limitation 5, cluster-vs-probe note, nomenclature."""
from __future__ import annotations

from pathlib import Path

D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"
p = D / "paper_zh.md"
t = p.read_text(encoding="utf-8")
done = []

# 1. drop the duplicate lockbox table in VI-A
i = t.find("| 实例 | 全系统策略无盾 |")
if i > 0:
    j = t.find("\n\n", t.find("| −2 天（290.25）", i))
    if j < 0:
        j = t.find("\n\n", t.find("290.25", i))
    t = t[:i] + t[j + 2:]
    done.append("drop-dup-lockbox")

old = ("三个 lockbox 实例被评估——epoch_doy 299.25（+7 天）、306.25（+14 天）、290.25（−2 天）——"
       "臂包括冻结的全系统策略、PPO-MLP 基线与奖励惩罚臂，各臂分别处于无盾、挖掘 16 s 规则、"
       "验证标定的 τ_used = 18 s 盾、（全系统策略）调好的 18 s 常数之下（均值 ± 标准差；逐种子数值见封存产物）：")
new = ("三个 lockbox 实例被评估——epoch_doy 299.25（+7 天）、306.25（+14 天）、290.25（−2 天）——"
       "臂包括冻结的全系统策略、PPO-MLP 基线与奖励惩罚臂，各臂分别处于无盾、挖掘 16 s 规则、"
       "验证标定的 τ_used = 18 s 盾、（全系统策略）调好的 18 s 常数之下。结果见表 VIII："
       "该表所有臂使用同一策略集与同一 traffic seed，因此各行可直接比较。")
if t.count(old) == 1:
    t = t.replace(old, new, 1)
    done.append("viA-lead")

# 2. Limitation 5
i = t.find("5. **小样本效应。**")
if i > 0:
    j = t.find("\n", i)
    t = t[:i] + ("5. **样本量。** 跨意图转移现用十个训练种子（其中九个在意图 0 提交了规则）；漂移阶梯与余量扫描用十个策略种子；"
                 "探测辨识研究用五个策略种子，并在出现处注明。种子级行为仍高度异质（奖励惩罚臂 sd 达 17.9 pp），"
                 "这正是本文所有对比都取配对的原因。") + t[j:]
    done.append("lim5")

# 3. cluster-vs-probe note
mark = "（8,682 次被动尝试中仅 705 次落在 14–16 s 带内，而 37.7% 落在 6–8 s 桶）"
if t.count(mark) == 1:
    t = t.replace(mark, mark + "；后文引用的 10–18 s 簇自助区间是被动日志的**辨识**区间，不是主动探测的置信区间（见第五节 C）", 1)
    done.append("cluster-note")

# 4. nomenclature tau
old = "**τ_used = min(τ\\* + m, 24 s)**"
if t.count(old) == 1:
    t = t.replace(old, "**τ_used = min(τ∗ + m, 24 s)**", 1)
    done.append("nomen-tau")

p.write_text(t, encoding="utf-8")
print("applied:", done)
