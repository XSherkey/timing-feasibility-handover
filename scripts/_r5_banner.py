"""R5 (v7): version banners."""
from __future__ import annotations

from pathlib import Path

D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"

EN = ("**Manuscript v7 — 2026-10-24 (R5 revision).** This version fixes the fifth review's list. "
      "The support audit is now split into two panels—passive no-shield logs (Table D1A, 8,682 attempts, "
      "8.1% in the 14–16 s band against 37.7% in the modal 6–8 s bucket) and rule-applied logs (Table D1B, "
      "22,807 attempts, 91.1% at 16–18 s, reported only as a consistency check)—because pooling them made "
      "the passive-coverage claim circular; every percentage that cited \"67 of 22,807\" is now the passive "
      "figure, and the unsupported \"two orders of magnitude\" phrasing is removed. The Introduction and "
      "Contribution 1 no longer say that no estimator can identify the bound at any sample size. The ledger "
      "names replace \"full system\" wherever a number is attached (Table II, Table VI, the lockbox table). "
      "Equation (4) is typeset with its plus sign, the appendix command keeps its ``>=``, +0.4 pp becomes "
      "+0.37 pp, the 1 pp tolerance becomes the 1.2 pp tolerance, and the five-seed probe agreement is "
      "explicitly scoped to the three regimes that exclude +4.4 s drift.")

ZH = ("**稿件 v7（中文审阅版）——2026-10-24（第五轮修订）。** 本版落实第五轮审稿清单。"
      "支撑审计拆成两个面板——被动无盾日志（表 D1A，8,682 次尝试，14–16 s 带占 8.1%，而众数 6–8 s 桶占 37.7%）"
      "与规则生效日志（表 D1B，22,807 次尝试，91.1% 落在 16–18 s，仅作一致性检查）——因为合并会让"
      "「被动日志覆盖不足」的论证变成循环论证；凡引用「67/22,807」的百分比一律改为被动数字，"
      "并删去被动数据不支持的「两个数量级」表述。引言与贡献 1 不再说「任何估计器在任何样本量下都无法识别」。"
      "凡附着数字处一律用台账名称替代「全系统」（表 II、表 VI、lockbox 表）。公式 (4) 补齐加号，"
      "附录命令保留 ``>=``，+0.4 pp 改为 +0.37 pp，1 pp 容差改为 1.2 pp 容差，"
      "五种子探测一致性明确限定为不含 +4.4 s 漂移的三档。")

for name, new, marker in (("paper_en.md", EN, "**Manuscript v6"), ("paper_zh.md", ZH, "**稿件 v6")):
    p = D / name
    t = p.read_text(encoding="utf-8")
    i = t.find(marker)
    if i < 0:
        raise SystemExit(f"banner not found in {name}")
    j = t.find("\n", i)
    t = t[:i] + new + t[j:]
    p.write_text(t, encoding="utf-8")
    print("banner updated:", name)
