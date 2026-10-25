"""R4 (v16) ZH mirror of the table/prose fixes."""
from __future__ import annotations

from pathlib import Path

D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"
p = D / "paper_zh.md"
t = p.read_text(encoding="utf-8")
done = []


def cut_replace(start_marker: str, end_marker_search: str, new_block: str, label: str) -> None:
    global t
    i = t.find(start_marker)
    if i < 0:
        raise SystemExit(f"[{label}] start not found")
    j = t.find("\n\n", t.find(end_marker_search, i))
    if j < 0:
        raise SystemExit(f"[{label}] end not found")
    t = t[:i] + new_block + t[j:]
    done.append(label)


# ---- Table IV (n = 10) ---------------------------------------------------
T4 = """**表 IV. 漂移响应（极区 HSR，mean ± sd，n = 10 个策略种子、traffic seed 0，极区取 |lat| ≥ 70°；两行常数控制器与策略无关，故 sd = 0.00）。**

| 额外建链时延 | 0 | +2.0 s | +3.2 s | +4.4 s |
|---|---|---|---|---|
| 调好的常数，固定 18 s | 93.33 | 92.39 | 85.98 | 83.56 |
| 常数在验证窗口重探 + 2 s 余量 | 93.33 | 93.20 | 93.20 | 93.20 |
| 带盾策略，固定 18 s 规则 | 93.36 ± 0.05 | 92.42 ± 0.05 | 86.01 ± 0.06 | 83.47 ± 0.34 |
| 带盾策略，阈值重探 + 2 s 余量 | 93.36 ± 0.05 | 93.23 ± 0.05 | 93.23 ± 0.05 | 93.23 ± 0.05 |
| 逐种子探测 τ∗（五个策略种子） | 16 (5/5) | 18 (5/5) | 20 (5/5) | 22 (4/5), 20 (1/5) |"""
cut_replace("**表 IV. 漂移响应", "| 逐种子探测 τ∗", T4, "table4")

# ---- VI-G prose + Table VI ----------------------------------------------
G = """**替代物理。** 两个扰动孪生检验结论是否为单一配置的产物（表 VI）。关闭极区缝惩罚后，盾把两个策略族都提升到 95.5%（全系统策略自 67.7%、PPO-MLP 自 78.1%）；盾前晚切换主导（28.5% 与 18.3% 的尝试），盾后降为 0.0%。馈电容量降为每网关 3 时隙后，同一条盾只把两族提升到 69.5–70.0%（自 39.1% 与 46.4%），因为 `no_route` 以 26–30% 的尝试占比成为主导失效类——计时可行性被修复，路由容量成为瓶颈。两个结果都是理论的预言：盾修复可行性因子，修复后的天花板由下一个失效类决定。我们认为，一个失效模式可预言的方法，比失效模式仅是不在测试集中的方法更可用。

**表 VI. 替代物理（极区 HSR，五个策略种子的均值；极区取 |lat| ≥ 70°；冻结策略；带盾臂施加式 (4)，τ_used = 18 s）。**

| 孪生 | 策略 | 臂 | 极区 HSR（%） | 晚切换占比（%） | 窗口超限（%） | 无路由（%） |
|---|---|---|---|---|---|---|
| 关闭缝 | 全系统 | 无盾 | 67.7 | 28.5 | 3.8 | 0.0 |
| 关闭缝 | 全系统 | 挖掘 16 s | 94.6 | 1.0 | 4.4 | 0.0 |
| 关闭缝 | 全系统 | τ_used = 18 s | 95.5 | 0.0 | 4.5 | 0.0 |
| 关闭缝 | PPO-MLP | 无盾 | 78.1 | 18.3 | 3.6 | 0.0 |
| 关闭缝 | PPO-MLP | 挖掘 16 s | 94.5 | 1.1 | 4.4 | 0.0 |
| 关闭缝 | PPO-MLP | τ_used = 18 s | 95.5 | 0.0 | 4.5 | 0.0 |
| 馈电 3 时隙 | 全系统 | 无盾 | 39.1 | 28.0 | 2.5 | 30.4 |
| 馈电 3 时隙 | 全系统 | 挖掘 16 s | 66.3 | 3.4 | 3.5 | 26.8 |
| 馈电 3 时隙 | 全系统 | τ_used = 18 s | 69.5 | 0.0 | 3.7 | 26.8 |
| 馈电 3 时隙 | PPO-MLP | 无盾 | 46.4 | 23.3 | 2.2 | 28.1 |
| 馈电 3 时隙 | PPO-MLP | 挖掘 16 s | 67.7 | 2.6 | 3.7 | 26.0 |
| 馈电 3 时隙 | PPO-MLP | τ_used = 18 s | 70.0 | 0.0 | 3.7 | 26.3 |"""
i = t.find("**替代物理。**")
j = t.find("**探测成本与极限。**")
if i < 0 or j < 0:
    raise SystemExit("ZH VI-G block not found")
t = t[:i] + G + "\n\n" + t[j:]
done.append("vi-G")

# ---- Table IV trailing sentence ----------------------------------------
old = "最后一格是命题 4 的不可辨识性极限，可见于单个表格单元：+4.4 s 时五个种子中有一个探到 20 s 而非 22 s，落在 91.1%，而该点最优为 94.1%。"
new = "最后一行是命题 4 的不可辨识性极限，可见于单个表格单元：在五种子探测研究中，+4.4 s 时有一个种子返回 20 s 而非 22 s。漂移阶梯本身使用该档的中位数（22 s），因此重探臂在该档守住 93.2%；若部署时信任那个偏离的探测，就会掉一个网格步。"
if t.count(old) == 1:
    t = t.replace(old, new, 1)
    done.append("t4-note")

# ---- arms count --------------------------------------------------------
old = "表 VII 给出九个臂。"
new = "表 VII 给出八个单意图臂；第九个 A6（每意图新建图谱）只在多意图协议中与 A0 不同，因此与跨意图实验一并报告于第六节 F。"
if t.count(old) == 1:
    t = t.replace(old, new, 1)
    done.append("arms")

# ---- pre-registered ----------------------------------------------------
old = "报告以 1.0 pp 为预注册 margin 的双单侧检验（TOST）"
new = "报告以 1.0 pp 为**事先指定** margin 的双单侧检验（TOST）"
if t.count(old) == 1:
    t = t.replace(old, new, 1)
    done.append("tost")

p.write_text(t, encoding="utf-8")
print("applied:", done)
