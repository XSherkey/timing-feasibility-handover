"""R4 (v6) part 2 for the Chinese manuscript: the remaining anchors."""
from __future__ import annotations

from pathlib import Path

P = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本" / "paper_zh.md"
t = P.read_text(encoding="utf-8")


def rep(old: str, new: str, label: str) -> None:
    global t
    n = t.count(old)
    if n != 1:
        raise SystemExit(f"[{label}] expected 1, found {n}")
    t = t.replace(old, new, 1)
    print("ok", label)


rep(
    "(ii) **带盾全系统对带盾 PPO-MLP**：92.93 对 91.89、94.80 对 93.62、94.24 对 93.04。",
    "(ii) **同一规则下的控制器族对比**（这才是同口径配对）：全系统+挖掘 16 s 对 PPO-MLP+挖掘 16 s，即 92.33 对 91.89、94.37 对 93.62、93.62 对 93.04（+0.44、+0.75、+0.58 pp）。而「部署系统对基线」是另一个问题，须另行标注：全系统+τ_used = 18 s 对 PPO-MLP+挖掘 16 s，即 92.93 对 91.89、94.80 对 93.62、94.24 对 93.04。上一版把后者称作「带盾全系统对带盾 PPO-MLP」，因两臂阈值不同而有歧义。",
    "pairing",
)
rep(
    "幅值由删失失败的 Kaplan–Meier 估计恢复，并在部署策略上以等渗拟合主动探测确定，再包裹代价不对称的 2 s 余量。",
    "删失日志的 Kaplan–Meier 估计只作为诊断性一致性检查、而非部署阈值的来源；幅值由在部署策略上以等渗拟合执行的主动探测确定，再包裹代价不对称的 2 s 余量。",
    "contribution2",
)
rep(
    "因此结果数据的信息区域只被稀薄覆盖（22,807 次极区尝试中的 67 次）——这是一种**有效**支撑失败，由命题 2 形式化；",
    "因此对结果数据而言，信息区域（交点正下方那条带）的覆盖比策略实际操作的区域薄两个数量级（22,807 次近极区尝试中仅 67 次落在该带内）；在任何一项实地研究付得起的样本预算下，该下界因而实际上不可从这条数据流识别——这是命题 2 所形式化的**给定样本预算下的有效支撑失败**，而非信息论意义上的不可能；",
    "intro-strong",
)
rep(
    "全系统（挖掘约束 + 盾）达 93.6% ± 0.7%",
    "**挖出规则 campaign 臂**（16 s 盾、未加余量）达 93.6% ± 0.7%",
    "table2-name",
)
rep(
    "在全部受测运行中未误拒系统自身的好提案（+0.4 pp）",
    "并在五次运行中未对系统自身的好提案造成可测税负（+0.37 pp，属描述性陈述，而非「从不误拒」的保证）",
    "abstract-04",
)
rep(
    "故容差为 **1.2 pp**",
    "故容差为 **≤ 1.20 pp**",
    "tolerance",
)
rep(
    "**表 C1′. 部署阈值补齐与 oracle 参照，极区 HSR（%）逐种子，共同回合。**",
    "**表 C2. 部署阈值补齐与 oracle 参照，极区 HSR（%）逐种子，共同回合。**",
    "table-c2",
)
rep(
    "**表 C2. 漂移响应逐种子，极区 HSR（%）：固定 18 s 常数 / 探测标定（括号内为 τ∗），共同回合。**",
    "**表 C3. 漂移响应逐种子，极区 HSR（%）：固定 18 s 常数 / 探测标定（括号内为 τ∗），共同回合。**",
    "table-c3",
)
rep(
    "它很薄，非空：14–16 s 桶有 67 次尝试）",
    "它很薄，非空：14–16 s 桶有 67 次尝试，而 16–18 s 桶有 20,771 次）",
    "d1-text",
)
rep(
    "p95 = 15.81 s，at risk 1,040）；",
    "p95 = 15.81 s，at risk 1,040；第四节 C 引用的 15.80 s 是 |lat| ≥ 70° 带，0.01 s 之差来自带定义）；",
    "p95-band",
)

P.write_text(t, encoding="utf-8")
print("ZH v6 edits (part 2) applied")
