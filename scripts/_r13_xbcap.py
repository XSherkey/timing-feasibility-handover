"""R14 part 8: rewrite the Table Xb caption as one bold span with no inner '**'."""
from __future__ import annotations

from pathlib import Path

D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"

for name, old_start, new_cap in (
    ("paper_en.md", "**Table Xb.", "**Table Xb. Paired statistics for the four orderings of the table above (paired over the ten "
                                   "policy seeds; the interval spans the four per-instance bootstrap 95% CIs, and "
                                   "the p value is the largest of the four exact Wilcoxon tests).**"),
    ("paper_zh.md", "**表 Xb.", "**表 Xb. 上表四条排序的配对统计（在十个策略种子上配对；区间为四个实例自助 95% CI 的并集范围，"
                                "p 值为四个精确 Wilcoxon 检验中的最大值）。**"),
):
    p = D / name
    t = p.read_text(encoding="utf-8")
    i = t.find(old_start)
    if i < 0:
        print("  missing", name)
        continue
    j = t.find("\n\n", i)
    t = t[:i] + new_cap + t[j:]
    p.write_text(t, encoding="utf-8")
    print(name, "caption rewritten")
