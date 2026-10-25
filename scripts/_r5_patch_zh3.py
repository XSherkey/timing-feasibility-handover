"""R5 (v7) part 3 (ZH): the three remaining anchors with their exact Chinese text."""
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
    "| **全系统（挖掘 + 盾）** | **0.6%** | 3.6% | 2.3% | **93.6 ± 0.7** |",
    "| **挖出规则 campaign 臂（16 s、无余量）** | **0.6%** | 3.6% | 2.3% | **93.6 ± 0.7** |\n\n*注.* 此处的 0.6% 是 campaign 协议（训练期规则在环，十个种子）下的晚切换占比；冻结因子化对同一条 16 s 规则在共同回合上报告 0.87%（表 C1）。差异来自协议而非规则，且两个数字都不属于部署的 18 s 臂（0.00%）。",
    "table2-note",
)
rep(
    "τ_used = min( τ∗ + m, 24 s ),   m = 2 s.                                                       (4)",
    "τ_used = min(τ∗ + m, 24 s),    m = 2 s                                                         (4)",
    "eq4",
)
rep(
    "| 孪生 | 臂 | 无盾 | + 盾 | 盾后的主导失效类 |\n|---|---|---|---|---|\n| 缝关闭 | 全系统 | 70.9 | 96.1 | 窗口/路由 ≈ 4% |\n| 缝关闭 | PPO-MLP | 61.4 | 95.8 | 窗口/路由 ≈ 4% |\n| 馈电 3 时隙 | 全系统 | 54.2 | 79.4 | 无路由 ≈ 20% |\n| 馈电 3 时隙 | PPO-MLP | 54.7 | 79.9 | 无路由 ≈ 20% |",
    "| 孪生 | 臂（冻结检查点） | 无盾 | + 盾 | 盾后的主导失效类 |\n|---|---|---|---|---|\n| 缝关闭 | 全系统策略 | 70.9 | 96.1 | 窗口/路由 ≈ 4% |\n| 缝关闭 | PPO-MLP 策略 | 61.4 | 95.8 | 窗口/路由 ≈ 4% |\n| 馈电 3 时隙 | 全系统策略 | 54.2 | 79.4 | 无路由 ≈ 20% |\n| 馈电 3 时隙 | PPO-MLP 策略 | 54.7 | 79.9 | 无路由 ≈ 20% |",
    "table6-names",
)

P.write_text(t, encoding="utf-8")
print("ZH v7 part 3 applied")
