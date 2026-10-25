"""R12 part 8: figures 6 and 7 are cited out of order (dose-response before gate). Swap them."""
from __future__ import annotations

from pathlib import Path

D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"

# ---- swap the numbers in both manuscripts --------------------------------
for name, pre in (("paper_en.md", "Fig. "), ("paper_zh.md", "图 ")):
    p = D / name
    t = p.read_text(encoding="utf-8")
    before6, before7 = t.count(pre + "6"), t.count(pre + "7")
    t = t.replace(pre + "6", "@@SIX@@").replace(pre + "7", pre + "6").replace("@@SIX@@", pre + "7")
    p.write_text(t, encoding="utf-8")
    print(f"{name}: {before6} sixes, {before7} sevens swapped")

# ---- swap the image mapping in the builder ------------------------------
b = D / "build_paper_docx.js"
s = b.read_text(encoding="utf-8")
old6 = '6: "fig7_gate.png"'
old7 = '7: "fig4_lambda_frontier.png"'
if old6 in s and old7 in s:
    s = s.replace(old6, '6: "@@GATE@@"').replace(old7, '7: "fig7_gate.png"').replace('6: "@@GATE@@"', '6: "fig4_lambda_frontier.png"')
    b.write_text(s, encoding="utf-8")
    print("builder FIG_FILES swapped")
else:
    print("FIG_FILES pattern not found; inspect manually")
    import re
    for m in re.finditer(r"\d+: \"fig[^\"]+\"", s):
        print("  ", m.group(0))
