"""R3 revision, final: version banners and the Chinese Fig. 2 caption."""
from __future__ import annotations

from pathlib import Path

D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"

en = D / "paper_en.md"
t = en.read_text(encoding="utf-8")
old = "**Manuscript v4 — 2026-10-24.**"
new = "**Manuscript v5 — 2026-10-24 (R3 revision).** This version applies the seven must-fix items of the third review: the Proposition 3 proof is stated as an event inclusion (the equality was wrong), Proposition 2 claims effective-support failure under a sample budget rather than information-theoretic impossibility, Proposition 1's empirical plateau is the 18 s zero-failure point rather than the 16 s ε-crossing, the threshold ledger is cut loose from the `|` inside table cells (which had garbled the rendered table) and its four names are fixed, the lockbox orderings carry explicit pairings and a 1.2 pp tolerance, the audit-gate candidate count is corrected to four, and the paper states its positioning as a systems-and-audit contribution with formal scope notes."
if old in t:
    t = t.replace(old, new, 1)
    en.write_text(t, encoding="utf-8")
    print("EN banner updated")
else:
    print("EN banner NOT found")

zh = D / "paper_zh.md"
t = zh.read_text(encoding="utf-8")
old = "**稿件 v4（中文审阅版）——2026-10-24。**"
new = "**稿件 v5（中文审阅版）——2026-10-24（第三轮修订）。** 本版落实第三轮审稿的七项必修：命题 3 的证明改为事件包含式（原等式有误）；命题 2 改称\"给定样本预算下的有效支撑失败\"而非信息论不可能；命题 1 的经验平台期改用 18 s 的零失效点而非 16 s 的 ε 交点；阈值台账去掉了表格单元内的 `|`（它曾使渲染出的表格错乱）并统一了四个名称；lockbox 排序给出显式配对与 1.2 pp 容差；审计门候选计数更正为四条；全文把定位明确为\"带适用范围注记的系统与审计\"贡献。"
if old in t:
    t = t.replace(old, new, 1)
    print("ZH banner updated")

old_fig = "**图 2.** 差距从何而来。极区 HSR（均值，n = 10 个种子）：纯奖励 PPO-MLP 72.6；同一条知识以最优系数（λ = 8）写入奖励 84.4；同一条知识作为盾施加到基线策略 91.8；全系统 93.6；无学习的调好常数 94.0。"
new_fig = "**图 2.** 差距从何而来。极区 HSR（均值，n = 10 个种子）：纯奖励 PPO-MLP 72.6；同一条知识以最优系数（λ = 8）写入奖励 84.4；同一条知识作为盾施加到基线策略 91.8；**挖出规则 campaign 臂**（16 s 盾、未加余量）93.6；**调好的常数**（18 s 提前量、无学习）94.0。93.6 这根柱是 campaign 的 16 s 臂，**不是**部署的探测标定算法（18 s，93.31；它出现在图 3 的因子化中）。"
if old_fig in t:
    t = t.replace(old_fig, new_fig, 1)
    print("ZH fig2 caption updated")
else:
    print("ZH fig2 caption NOT found")
zh.write_text(t, encoding="utf-8")
