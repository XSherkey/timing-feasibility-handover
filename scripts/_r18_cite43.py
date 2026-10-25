"""R18: cite the prior report honestly (it is under review, not published) and stop relying on it."""
from __future__ import annotations

from pathlib import Path

D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"

NEW43 = ('[43] Z. Xu, Y. Zhang, C. Sun, S. Lu, and C. Li, "From human intent to in-orbit action: A self-learning '
         'large language model agent for 6G satellite networks," manuscript under review, 2026. (This is the prior '
         'report of the ALMOND pipeline audited here. Because it is not yet accepted, nothing in this paper depends '
         'on its availability: the reproduced pipeline is fully specified by Appendix A, the nomenclature, and the '
         'sealed artefacts, which are the objects of the audit.)')

for name in ("paper_en.md", "paper_zh.md"):
    p = D / name
    t = p.read_text(encoding="utf-8")

    # 1. rebuild reference 43 cleanly (the earlier edit left a duplicated gloss)
    i = t.find("[43] Z. Xu")
    if i > 0:
        j = t.find("\n\n", i)
        t = t[:i] + NEW43 + t[j:]
        print(name, "[43] rewritten")

    # 2. "published configuration" is factually wrong while [43] is under review
    n = t.count("its published configuration")
    t = t.replace("its published configuration", "the configuration documented in the prior report")
    t = t.replace("published configuration and sealed artefacts", "documented configuration and sealed artefacts")
    print(name, "'published configuration' occurrences:", n)

    p.write_text(t, encoding="utf-8")

# 3. one sentence in Section VI-A: the paper does not depend on [43]
p = D / "paper_en.md"
t = p.read_text(encoding="utf-8")
anchor = "All arms share the twin, the time-based train/validation/test splits"
i = t.find(anchor)
if i > 0:
    j = t.find("\n\n", i)
    add = (" The audited pipeline itself is specified in this paper—Appendix A lists every command, the "
           "nomenclature fixes every symbol, and the sealed artefacts hold every per-seed value—so the audit does "
           "not depend on the publication status of the prior report [43]; a reader can rerun everything from the "
           "material included here.")
    t = t[:j] + add + t[j:]
    p.write_text(t, encoding="utf-8")
    print("EN VI-A independence sentence added")

z = D / "paper_zh.md"
s = z.read_text(encoding="utf-8")
i = s.find("所有臂共享同一孪生")
if i > 0:
    j = s.find("\n\n", i)
    addz = ("被审计的流水线本身已在本文中完整给出——附录 A 列出全部命令、符号表固定每个记号、封存产物保存每个种子的数值——"
            "因此本审计不依赖于先前报告 [43] 的录用状态；读者可以仅凭本文材料重跑全部实验。")
    s = s[:j] + addz + s[j:]
    z.write_text(s, encoding="utf-8")
    print("ZH VI-A independence sentence added")
