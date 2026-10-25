"""Make the pipeline figure Fig. 1.

Step 1: cite the pipeline early in the introduction (before any other figure citation).
Step 2: rotate the figure numbers 4->1->2->3->4 and remap the builder's file table.
"""
from __future__ import annotations

import re
from pathlib import Path

D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"

EN_OLD = ("and the natural reading is that the *learning* produced them.")
EN_NEW = ("and the natural reading is that the *learning* produced them. Fig. 1 shows the shape of the "
          "answer we end up with: the constraint is measured on the deployed system, committed through "
          "an audit gate, and enforced at decision time rather than inside the reward.")
ZH_OLD = "而自然的解读是：这些增益来自**学习**本身。"
ZH_NEW = ("而自然的解读是：这些增益来自**学习**本身。图 1 给出我们最终得到的答案的形状：约束在部署系统上被测出、"
          "经审计门提交，并在决策时刻执行，而不是写进奖励。")

ROT = {4: 1, 1: 2, 2: 3, 3: 4, 5: 5, 6: 6, 7: 7, 8: 8, 9: 9}
CUR_FILES = {1: "fig3_policy_independence.png", 2: "fig5_drift.png", 3: "fig9_passive_support.png",
             4: "fig1_pipeline.png", 5: "fig2_gap.png", 6: "fig7_gate.png", 7: "fig4_lambda_frontier.png",
             8: "fig6_forms.png", 9: "fig8_architecture.png"}

for name, old, new in (("paper_en.md", EN_OLD, EN_NEW), ("paper_zh.md", ZH_OLD, ZH_NEW)):
    p = D / name
    t = p.read_text(encoding="utf-8")
    if new.split("：")[0][:20] in t or "Fig. 1 shows the shape of the answer" in t:
        print(name, "already has the early citation")
        continue
    if t.count(old) != 1:
        raise SystemExit(f"{name}: anchor found {t.count(old)} times")
    t = t.replace(old, new, 1)
    p.write_text(t, encoding="utf-8")
    print(name, "early pipeline citation added")

# ---- rotate the numbers --------------------------------------------------
for name in ("paper_en.md", "paper_zh.md"):
    p = D / name
    t = p.read_text(encoding="utf-8")
    if "@@G" in t:
        raise SystemExit(f"{name}: leftover tokens")
    if name == "paper_en.md":
        t = re.sub(r"Fig\.\s*(\d+)", lambda m: f"@@G{m.group(1)}@@", t)
        t = re.sub(r"@@G(\d+)@@", lambda m: f"Fig. {ROT[int(m.group(1))]}", t)
    else:
        t = re.sub(r"图\s*(\d+)", lambda m: f"@@G{m.group(1)}@@", t)
        t = re.sub(r"@@G(\d+)@@", lambda m: f"图 {ROT[int(m.group(1))]}", t)
    p.write_text(t, encoding="utf-8")
    print(name, "rotated")

# ---- builder file table --------------------------------------------------
js = D / "build_paper_docx.js"
s = js.read_text(encoding="utf-8")
start = s.find("const FIG_FILES = {")
end = s.find("};", start)
new_files = {ROT[c]: f for c, f in CUR_FILES.items()}
block = "const FIG_FILES = {\n" + "".join(f'  {k}: "{v}",\n' for k, v in sorted(new_files.items())) + "}"
s = s[:start] + block + s[end + 2:]
js.write_text(s, encoding="utf-8")
print("builder remapped:", {k: v for k, v in sorted(new_files.items()) if k <= 4})
