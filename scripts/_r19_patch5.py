"""R19 part 5: IEEE front matter — inline 'Abstract—' and 'Index Terms—', black headings."""
from __future__ import annotations

import re
from pathlib import Path

D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"

KEY_EN = ("**Index Terms—** handover management, low Earth orbit satellite networks, constraint injection, "
          "survival analysis with censoring, threshold calibration, audit and admission.")
KEY_ZH = ("**索引词——** 切换管理，低轨卫星网络，约束注入，删失生存分析，阈值标定，审计与准入。")

for name, abs_head, abs_prefix, keyline in (
    ("paper_en.md", "## Abstract", "**Abstract—** ", KEY_EN),
    ("paper_zh.md", "## 摘要", "**摘要——** ", KEY_ZH),
):
    p = D / name
    t = p.read_text(encoding="utf-8")
    # remove the "## Abstract" heading line
    n = t.count(abs_head + "\n\n")
    if n != 1:
        print(f"  {name}: abstract heading count {n}")
    else:
        t = t.replace(abs_head + "\n\n", "", 1)
    # prefix the abstract paragraph
    i = t.find(abs_prefix)
    if i < 0:
        # find the paragraph that follows the removed heading position
        m = re.search(r"(## Nomenclature|## 符号表)", t)
        if m:
            j = t.find("\n\n", m.start()) + 2
            t = t[:j] + abs_prefix + t[j:]
            print(f"  {name}: abstract prefixed")
    else:
        print(f"  {name}: abstract already prefixed")
    # add index terms right before the nomenclature heading
    m = re.search(r"(## Nomenclature|## 符号表)", t)
    if m and "Index Terms—" not in t and "索引词——" not in t:
        t = t[:m.start()] + keyline + "\n\n" + t[m.start():]
        print(f"  {name}: index terms added")
    p.write_text(t, encoding="utf-8")

# headings must be black (Word's built-in heading styles are blue)
b = D / "build_paper_docx.js"
s = b.read_text(encoding="utf-8")
old = 'run(line.slice(4).trim(), { bold: true, size: 24 })'
if old in s:
    s = s.replace(old, 'run(line.slice(4).trim(), { bold: true, size: 24, color: "000000" })', 1)
    print("H2 colour fixed")
old = 'run(line.slice(3).trim(), { bold: true, size: 26 })'
if old in s:
    s = s.replace(old, 'run(line.slice(3).trim(), { bold: true, size: 26, color: "000000", smallCaps: true })', 1)
    print("H1 colour + small caps")
b.write_text(s, encoding="utf-8")
