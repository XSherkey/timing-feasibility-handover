"""Renumber the figures so that numerical order equals first-citation order, and rebuild.

Old -> new mapping is derived from the first in-text mention of each figure:
  old 3 (per-seed factorial)   -> 1
  old 5 (drift)                -> 2
  old 9 (passive support)      -> 3
  old 1 (pipeline)             -> 4
  old 2 (gap waterfall)        -> 5
  old 7 (gate)                 -> 6
  old 4 (lambda dose-response) -> 7
  old 6 (six references)       -> 8
  old 8 (deployment)           -> 9
"""
from __future__ import annotations

import re
from pathlib import Path

D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"
MAP = {3: 1, 5: 2, 9: 3, 1: 4, 2: 5, 7: 6, 4: 7, 6: 8, 8: 9}
FILES = {1: "fig3_policy_independence.png", 2: "fig5_drift.png", 3: "fig9_passive_support.png",
         4: "fig1_pipeline.png", 5: "fig2_gap.png", 6: "fig7_gate.png", 7: "fig4_lambda_frontier.png",
         8: "fig6_forms.png", 9: "fig8_architecture.png"}

for name, lab in (("paper_en.md", "Fig."), ("paper_zh.md", "图")):
    p = D / name
    t = p.read_text(encoding="utf-8")
    if "@@F" in t:
        raise SystemExit(f"{name}: already renumbered")
    # pass 1: old numbers -> tokens
    if name == "paper_en.md":
        t = re.sub(r"Fig\.\s*(\d+)", lambda m: f"@@F{m.group(1)}@@", t)
    else:
        t = re.sub(r"图\s*(\d+)", lambda m: f"@@F{m.group(1)}@@", t)
    # pass 2: tokens -> new numbers
    def to_new(m):
        old = int(m.group(1))
        new = MAP[old]
        return f"Fig. {new}" if name == "paper_en.md" else f"图 {new}"
    t = re.sub(r"@@F(\d+)@@", to_new, t)
    p.write_text(t, encoding="utf-8")
    print(name, "renumbered")

# builder: figure files keyed by the NEW numbers
js = D / "build_paper_docx.js"
s = js.read_text(encoding="utf-8")
start = s.find("const FIG_FILES = {")
end = s.find("};", start)
if start < 0 or end < 0:
    raise SystemExit("FIG_FILES block not found")
NEW = "const FIG_FILES = {\n" + "".join(f'  {k}: "{v}",\n' for k, v in sorted(FILES.items())) + "}"
s = s[:start] + NEW + s[end + 2:]
js.write_text(s, encoding="utf-8")
print("builder FIG_FILES remapped")
