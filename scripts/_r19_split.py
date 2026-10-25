"""R19 part 8: split the per-seed appendices (C, D) out into a supplementary document."""
from __future__ import annotations

from pathlib import Path

D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"

POINTER_EN = ("\n\n*Supplementary material.* Appendices C and D—the per-seed values for the two load-bearing "
              "experiments and the full support audit, together with the 26-candidate gate bank—are provided as "
              "a separate supplementary document, because they are per-seed tables that no reader needs in order "
              "to follow the argument. The main text quotes every number it uses from them.\n")
POINTER_ZH = ("\n\n*补充材料。* 附录 C 与 D——两项承重实验的逐种子数值、完整支撑审计，以及 26 条候选门银行——"
              "作为单独的补充文档提供，因为它们是逐种子表格，读者理解论证并不需要它们；正文引用的每个数字都已在主文中给出。\n")

for name, start, end, pointer, supp_name, title in (
    ("paper_en.md", "## Appendix C.", "## Appendix E.", POINTER_EN, "supp_en.md",
     "**Supplementary Material for “Probe-Calibrated Conservative Injection of Handover Constraints for "
     "Autonomous LEO Satellite Networks”**\n\nThis document carries the per-seed tables (Appendix C) and the "
     "support audit (Appendix D) that the main text cites but does not reproduce. Section and table numbers are "
     "identical to those used in the main text.\n"),
    ("paper_zh.md", "## 附录 C.", "## 附录 E.", POINTER_ZH, "supp_zh.md",
     "**补充材料：《面向自主 LEO 卫星网络的探测标定式切换约束保守注入》**\n\n本文档包含主文引用但未复现的逐种子表（附录 C）"
     "与支撑审计（附录 D）；章节与表号与主文一致。\n"),
):
    p = D / name
    t = p.read_text(encoding="utf-8")
    i = t.find(start)
    j = t.find(end, i)
    if i < 0 or j < 0:
        raise SystemExit(f"{name}: appendix markers not found ({i}, {j})")
    block = t[i:j]
    t = t[:i] + t[j:]
    # put the pointer just before Appendix E
    k = t.find(end)
    t = t[:k] + pointer.strip() + "\n\n" + t[k:]
    p.write_text(t, encoding="utf-8")

    supp = D / supp_name
    supp.write_text(title + "\n\n" + block, encoding="utf-8")
    print(f"{name}: appendix C/D moved to {supp_name} ({len(block)} chars)")
