"""R6 (v8): the Chinese counterparts of the sixth-round fixes."""
from __future__ import annotations

from pathlib import Path

P = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本" / "paper_zh.md"
t = P.read_text(encoding="utf-8")
done = []


def rep(old: str, new: str, label: str) -> None:
    global t
    n = t.count(old)
    if n != 1:
        raise SystemExit(f"[{label}] expected 1, found {n}")
    t = t.replace(old, new, 1)
    done.append(label)


rep(
    "当动作支撑集不覆盖信息区域时，被动日志的结果无法识别可行性下界（命题 2）",
    "当信息区域的有效支撑在给定样本预算下不足时，被动日志的结果无法识别可行性下界（命题 2）",
    "contrib1",
)
rep(
    "在标称物理下与全系统持平（94.0% 对 93.6%）",
    "在标称物理下与挖出规则 campaign 臂持平（94.0% 对 93.6%）",
    "p3-tuned",
)
rep(
    "| 全系统 campaign 数字 93.6% ± 0.7%（VI-B，图 2 第 4 柱；即 **挖出规则 campaign 臂**：16 s、未加余量） |",
    "| **挖出规则 campaign 臂** 93.6% ± 0.7%（VI-B，图 2 第 4 柱；16 s、未加余量） |",
    "ledger-row1",
)
rep(
    "全系统相对手工基线的领先**很小**",
    "全系统策略相对手工基线的领先**很小**",
    "lockbox-margin",
)
rep(
    "(i) 全系统相对手工基线的领先很小",
    "(i) 全系统策略相对手工基线的领先很小",
    "lim7-margin",
)
rep(
    "极区挖掘日志按提前量桶的尝试数、精确事件数（成功建链时长）与右删失数见附录 D（表 D1），KM 曲线各分位数的事件/删失支撑一并给出。该审计直接回答了三个可核查的问题：14–18 s 带是否为空（它很薄，非空——各桶计数见表 D1）",
    "按提前量桶的尝试数、精确事件数（成功建链时长）与右删失数见附录 D：被动无盾日志见表 D1A，规则生效日志见表 D1B（后者仅作一致性检查），KM 曲线各分位数的事件/删失支撑一并给出。该审计直接回答了三个可核查的问题：14–18 s 带是否为空（它很薄，非空——各桶计数见表 D1A）",
    "va-pointer",
)
rep(
    "| 漂移响应（表 IV，表 C2） |",
    "| 漂移响应（表 IV，表 C3） |",
    "ledger-c3",
)
rep(
    "| 实例 | 全系统无盾 | 全系统+挖掘16 s | **全系统+τ_used=18 s** | 全系统+调好常数 | PPO-MLP 无盾 | PPO-MLP+挖掘16 s | 奖励 λ = 8 |",
    "| 实例 | 全系统策略无盾 | 全系统策略+挖掘16 s | **全系统策略+τ_used=18 s** | 全系统策略+调好常数 | PPO-MLP 无盾 | PPO-MLP+挖掘16 s | 奖励 λ = 8 |",
    "lockbox-header",
)

P.write_text(t, encoding="utf-8")
print("applied:", done)
