"""R19 part 9: move appendices A, B, E to the supplement as well, then re-measure."""
from __future__ import annotations

from pathlib import Path

D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"

for name, supp_name, marks, title_extra in (
    ("paper_en.md", "supp_en.md",
     ["## Appendix A.", "## Appendix B.", "## Appendix E.", "## References"],
     "\n\nThis document also carries the reproduction commands (Appendix A), the latency note (Appendix B) and "
     "the prompt/raw-output appendix (Appendix E).\n"),
    ("paper_zh.md", "supp_zh.md",
     ["## 附录 A.", "## 附录 B.", "## 附录 E.", "## 参考文献"],
     "\n\n本文档同时包含复现命令（附录 A）、时延说明（附录 B）与 prompt/原始输出附录（附录 E）。\n"),
):
    p = D / name
    t = p.read_text(encoding="utf-8")
    supp = D / supp_name
    s = supp.read_text(encoding="utf-8")

    for a, b in (("## Appendix A.", "## Appendix B."), ("## Appendix B.", "## Appendix E."),
                 ("## Appendix E.", "## References")):
        i = t.find(a)
        j = t.find(b, i)
        if i < 0 or j < 0:
            print(f"  {name}: {a} not found")
            continue
        block = t[i:j]
        t = t[:i] + t[j:]
        s = s.rstrip() + "\n\n" + block.strip() + "\n"
        print(f"  {name}: moved {a}")

    # a short pointer in the main text, right before the references
    ptr = ("\n\n*Supplementary material.* The reproduction commands, the latency note, the prompt appendix and the "
           "per-seed tables travel in the supplementary document; the main text is self-contained for reading, "
           "the supplement is what makes it re-runnable.\n" if "en" in name else
           "\n\n*补充材料。* 复现命令、时延说明、prompt 附录与逐种子表格都在补充文档中；主文自身足以阅读，"
           "补充文档则使其可复现。\n")
    k = t.find("## References" if "en" in name else "## 参考文献")
    if k > 0:
        t = t[:k] + ptr.strip() + "\n\n" + t[k:]
    p.write_text(t, encoding="utf-8")
    supp.write_text(s, encoding="utf-8")
