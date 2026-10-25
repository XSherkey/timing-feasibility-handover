"""Fix three issues in the isolation table/text:
  1. A8's "deployed rule" cell was '--' (A8 is a controller, not a shield rule) -> describe it.
  2. A8's lead is chosen by a validation grid search, not by the isotonic probe -> wording.
  3. 'to within -0.07 pp' printed a signed difference inside a 'within' phrase -> absolute value.
"""
from __future__ import annotations

from pathlib import Path

D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"

EN = [
    # 1. the table cell
    ("| A8 | highest-elevation controller, lead re-probed on validation | `--` | 93.33 | -0.02 | 91.67 |",
     "| A8 | highest-elevation controller, lead re-selected on validation | no constraint rule: controller is max-elevation with a fixed lead of 18 s | 93.33 | -0.02 | 91.67 |"),
    # 2. wording in the body
    ("and A8—a highest-elevation controller whose lead is re-probed on validation—tracks the shield to within -0.02 pp at nominal physics",
     "and A8—a highest-elevation controller whose lead is re-selected on the validation window—tracks the shield to within 0.02 pp at nominal physics"),
    ("A7 reproduces A0 to within -0.07 pp",
     "A7 reproduces A0 to within 0.07 pp"),
    # 3. abstract
    ("a highest-elevation controller whose lead is re-probed on validation matches it within 0.03 pp",
     "a highest-elevation controller whose lead is re-selected on the validation window matches it within 0.03 pp"),
]

ZH = [
    ("| A8 | 最高仰角控制器，验证窗口重探提前量 | — | 93.33 | −0.02 | 91.67 |",
     "| A8 | 最高仰角控制器，提前量在验证窗口上重选 | 无约束规则：控制器为最高仰角 + 固定提前量 18 s | 93.33 | −0.02 | 91.67 |"),
    ("A8 复现到 0.02 pp", "A8 复现到 0.02 pp"),
]

NOTE_EN = ("*A8 has no deployed rule.* It is a controller baseline, not a shielded policy: the policy is
\"hand over to the highest-elevation routed candidate\" and the lead is a single constant, re-selected on
the validation window from {14, 16, 18, 20, 22} s (validation polar HSR 84.9, 91.8, 92.8, 92.5, 92.5;
the grid returns 18 s). It is the strongest no-learning competitor to the shield, and the point of the
row is that it is indistinguishable from it.\n")

for name, pairs in (("paper_en.md", EN), ("paper_zh.md", ZH)):
    p = D / name
    t = p.read_text(encoding="utf-8")
    done = []
    for old, new in pairs:
        if t.count(old) == 1:
            t = t.replace(old, new, 1)
            done.append(old[:40])
        else:
            print(f"  {name}: MISS ({t.count(old)}) {old[:60]}")
    if name == "paper_en.md" and "A8 has no deployed rule" not in t:
        anchor = "| A8 | highest-elevation controller, lead re-selected on validation"
        i = t.find(anchor)
        j = t.find("\n\n", i)
        t = t[:j] + "\n\n" + NOTE_EN + t[j:]
        done.append("note")
    p.write_text(t, encoding="utf-8")
    print(name, "applied:", len(done))
