"""Finish: rotate the ZH figure numbers (tolerant) and remap the builder's file table."""
from __future__ import annotations

import re
from pathlib import Path

D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"
ROT = {4: 1, 1: 2, 2: 3, 3: 4, 5: 5, 6: 6, 7: 7, 8: 8, 9: 9}
CUR_FILES = {1: "fig3_policy_independence.png", 2: "fig5_drift.png", 3: "fig9_passive_support.png",
             4: "fig1_pipeline.png", 5: "fig2_gap.png", 6: "fig7_gate.png", 7: "fig4_lambda_frontier.png",
             8: "fig6_forms.png", 9: "fig8_architecture.png"}

p = D / "paper_zh.md"
t = p.read_text(encoding="utf-8")
if "@@G" in t:
    t = re.sub(r"@@G(\d+)@@", lambda m: f"图 {ROT.get(int(m.group(1)), m.group(1))}", t)
    print("cleaned leftover tokens")
elif "图 1 给出我们最终得到的答案" in t:
    t = re.sub(r"图\s*(\d+)",
               lambda m: f"@@G{m.group(1)}@@" if int(m.group(1)) in ROT else m.group(0), t)
    t = re.sub(r"@@G(\d+)@@", lambda m: f"图 {ROT[int(m.group(1))]}", t)
    print("ZH rotated")
p.write_text(t, encoding="utf-8")

js = D / "build_paper_docx.js"
s = js.read_text(encoding="utf-8")
start = s.find("const FIG_FILES = {")
end = s.find("};", start)
new_files = {ROT[c]: f for c, f in CUR_FILES.items()}
s = s[:start] + ("const FIG_FILES = {\n" + "".join(f'  {k}: "{v}",\n' for k, v in sorted(new_files.items())) + "}") + s[end + 2:]
js.write_text(s, encoding="utf-8")
print("builder remapped:", {k: new_files[k] for k in sorted(new_files)})
