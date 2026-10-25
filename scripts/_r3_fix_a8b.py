"""Fix three issues in the isolation table/text (multi-line string handled correctly)."""
from __future__ import annotations

from pathlib import Path

D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"

NOTE_EN = (
    "*A8 has no deployed rule.* It is a controller baseline, not a shielded policy: the policy is "
    "\"hand over to the highest-elevation routed candidate\" and the lead is a single constant, re-selected "
    "on the validation window from {14, 16, 18, 20, 22} s (validation polar HSR 84.9, 91.8, 92.8, 92.5, "
    "92.5; the grid returns 18 s). It is the strongest no-learning competitor to the shield, and the point "
    "of the row is that the shield is indistinguishable from it."
)

EN = [
    ("| A8 | highest-elevation controller, lead re-probed on validation | `--` | 93.33 | -0.02 | 91.67 |",
     "| A8 | highest-elevation controller, lead re-selected on validation | no constraint rule: max-elevation controller with a fixed 18 s lead | 93.33 | -0.02 | 91.67 |"),
    ("and A8\u2014a highest-elevation controller whose lead is re-probed on validation\u2014tracks the shield to within -0.02 pp at nominal physics",
     "and A8\u2014a highest-elevation controller whose lead is re-selected on the validation window\u2014tracks the shield to within 0.02 pp at nominal physics"),
    ("A7 reproduces A0 to within -0.07 pp",
     "A7 reproduces A0 to within 0.07 pp"),
    ("a highest-elevation controller whose lead is re-probed on validation matches it within 0.03 pp",
     "a highest-elevation controller whose lead is re-selected on the validation window matches it within 0.03 pp"),
]

ZH = [
    ("| A8 | 最高仰角控制器，验证窗口重探提前量 | — | 93.33 | \u22120.02 | 91.67 |",
     "| A8 | 最高仰角控制器，提前量在验证窗口上重选 | 无约束规则：最高仰角控制器 + 固定 18 s 提前量 | 93.33 | \u22120.02 | 91.67 |"),
]

for name, pairs in (("paper_en.md", EN), ("paper_zh.md", ZH)):
    p = D / name
    t = p.read_text(encoding="utf-8")
    done = 0
    for old, new in pairs:
        if t.count(old) == 1:
            t = t.replace(old, new, 1)
            done += 1
        else:
            print(f"  {name}: MISS ({t.count(old)}) {old[:70]}")
    if name == "paper_en.md" and "A8 has no deployed rule" not in t:
        anchor = "| A8 | highest-elevation controller, lead re-selected on validation"
        i = t.find(anchor)
        if i < 0:
            raise SystemExit("A8 row not found after replacement")
        j = t.find("\n\n", i)
        t = t[:j] + "\n\n" + NOTE_EN + "\n" + t[j:]
        done += 1
        print("  note inserted")
    p.write_text(t, encoding="utf-8")
    print(name, "applied:", done)
