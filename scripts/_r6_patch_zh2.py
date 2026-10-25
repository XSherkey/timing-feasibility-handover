"""R6 part 2 (ZH): the remaining numeric 'full system' attachments."""
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


rep("全系统的端到端 campaign 数字 93.6% ± 0.7% 另行复现",
    "挖出规则 campaign 臂的端到端数字 93.6% ± 0.7% 另行复现", "n1")
rep("从纯奖励 campaign 臂的 22.1% 降到全系统的 0.6%",
    "从纯奖励 campaign 臂的 22.1% 降到挖出规则 campaign 臂的 0.6%", "n2")
rep("（全系统）调好的 18 s 常数之下",
    "（全系统策略）调好的 18 s 常数之下", "n3")
rep("盾在同一批回合上优于无盾——全系统 92.93/94.80/94.24 对 68.37/71.12/72.47",
    "盾在同一批回合上优于无盾——全系统策略 92.93/94.80/94.24 对 68.37/71.12/72.47", "n4")

P.write_text(t, encoding="utf-8")
print("applied:", done)
