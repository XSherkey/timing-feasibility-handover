"""R6 (v8): version banners."""
from __future__ import annotations

from pathlib import Path

D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"

EN = ("**Manuscript v8 — 2026-10-24 (R6 revision).** This version finishes what v7 started. The last three "
      "traces of the pooled support audit are gone from Proposition 2 and its remark: the informative band "
      "now carries 705 attempts (8.1% of 8,682 passive attempts, 91 late) rather than \"67 of 22,807\", and "
      "the \"two orders of magnitude\" comparison is replaced by the measured factor of ≈4.6 against the modal "
      "6–8 s bucket. Contribution 1 no longer says the action support \"misses\" the informative region; it "
      "says effective support is insufficient under a sample budget. The ledger names replace \"full system\" "
      "in the remaining numeric passages (the tuned-constant comparison, the threshold ledger's first row, the "
      "lockbox caption and header, the two margin statements). Section V-A points at Table D1A/D1B rather "
      "than the retired single table, and the ledger's drift-row cross-reference is corrected to Table C3. "
      "Tables D1A and D1B are verified row by row in the source: each satisfies attempts = exact + censored "
      "+ competing risk, the column sums equal the declared totals (8,682 and 22,807), and every share "
      "equals attempts/total.")

ZH = ("**稿件 v8（中文审阅版）——2026-10-24（第六轮修订）。** 本版完成 v7 未竟的部分。命题 2 及其备注中最后三处"
      "「合并审计」的残留已清除：信息带现在是 705 次尝试（占 8,682 次被动尝试的 8.1%，其中 91 次晚切换），"
      "不再是「67/22,807」；「两个数量级」改为与众数 6–8 s 桶相比的实测约 4.6 倍。贡献 1 不再说动作支撑「不覆盖」"
      "信息区域，而是说「在给定样本预算下有效支撑不足」。凡附着数字处一律用台账名称替代「全系统」"
      "（调好常数的对比、台账首行、lockbox 表题与表头、两处领先幅度表述）。第五节 A 指向表 D1A/D1B 而非已废弃的"
      "单表，台账的漂移行交叉引用更正为表 C3。表 D1A 与 D1B 已在源文件中逐行校验：每行满足"
      "「尝试数 = 精确事件 + 右删失 + 竞争风险」，列合计等于申明总数（8,682 与 22,807），且每个占比都等于"
      "该行尝试数除以总数。")

for name, new, marker in (("paper_en.md", EN, "**Manuscript v7"), ("paper_zh.md", ZH, "**稿件 v7")):
    p = D / name
    t = p.read_text(encoding="utf-8")
    i = t.find(marker)
    if i < 0:
        raise SystemExit(f"banner not found in {name}")
    j = t.find("\n", i)
    t = t[:i] + new + t[j:]
    p.write_text(t, encoding="utf-8")
    print("banner updated:", name)
