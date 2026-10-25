"""R4 (v6): version banners."""
from __future__ import annotations

from pathlib import Path

D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"

en = D / "paper_en.md"
t = en.read_text(encoding="utf-8")
i = t.find("**Manuscript v5")
j = t.find("\n", i)
if i < 0:
    raise SystemExit("EN banner not found")
new = ("**Manuscript v6 — 2026-10-24 (R4 revision).** This version fixes the fourth review's "
       "consistency list: the Table D1 counts now agree with the prose (67 of 22,807 attempts in the "
       "14-16 s bucket, 20,771 in 16-18 s, 92.5% at or above 16 s) and the band is named as near-polar "
       "|lat| >= 68 deg throughout; Section VI-A no longer says the lockbox is outstanding work while the "
       "next paragraph reports it; Limitation 7 is *bounded* rather than retired; the lockbox threshold is "
       "justified by five-seed agreement instead of a claim that it is policy-seed independent; lockbox "
       "ordering (ii) is split into the same-rule pairing and the deployed-versus-baseline pairing; "
       "Contribution 2 and the Introduction now describe Kaplan-Meier as a diagnostic and the passive-log "
       "failure as effective-support under a budget; the ledger names replace \"full system\" wherever a "
       "number is attached; and the small-number inconsistencies (+0.37 pp, <=1.20 pp, p95 band) are fixed. "
       "Appendix C tables are renumbered C1/C2/C3 (the prime was dropped because it is lost in text "
       "extraction).")
t = t[:i] + new + t[j:]
en.write_text(t, encoding="utf-8")
print("EN banner updated")

zh = D / "paper_zh.md"
t = zh.read_text(encoding="utf-8")
i = t.find("**稿件 v5")
j = t.find("\n", i)
if i < 0:
    raise SystemExit("ZH banner not found")
new = ("**稿件 v6（中文审阅版）——2026-10-24（第四轮修订）。** 本版落实第四轮审稿的一致性清单："
       "表 D1 的计数与正文一致（14–16 s 桶 67/22,807、16–18 s 桶 20,771、16 s 及以上占 92.5%），"
       "全篇把该带称为近极区 |lat| ≥ 68°；第六节 A 不再一边说 lockbox 是遗留工作、一边在下一段报告它；"
       "局限 7 由「退役」改为「收窄」；锁箱阈值以五种子一致性为依据，而不再声称与策略种子无关；"
       "lockbox 排序 (ii) 拆成「同规则配对」与「部署系统对基线配对」；贡献 2 与引言改为"
       "「KM 仅作诊断、被动日志的失效是给定预算下的有效支撑失败」；凡附着数字处一律使用台账四名称，"
       "不再用「全系统」；并修正小数字（+0.37 pp、≤1.20 pp、p95 的带定义）。"
       "附录 C 的表重编号为 C1/C2/C3（去掉撇号，因为它在文本抽取中会丢失）。")
t = t[:i] + new + t[j:]
zh.write_text(t, encoding="utf-8")
print("ZH banner updated")
