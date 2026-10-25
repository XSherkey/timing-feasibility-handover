"""R11 part 4: make the Table XI caption fully bold so the caption parser cannot leave a stray marker."""
from __future__ import annotations

from pathlib import Path

D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"
p = D / "paper_en.md"
t = p.read_text(encoding="utf-8")

old_start = "**Table XI. Audit gate over 26 candidates.** Each candidate is labelled harmful, neutral or good by its "
i = t.find(old_start)
if i < 0:
    raise SystemExit("Table XI caption not found")
j = t.find("\n\n", i)
body = t[i + len("**Table XI. Audit gate over 26 candidates.** "):j]
NEW = ("**Table XI. Audit gate over 26 candidates. Each candidate is labelled harmful, neutral or good by its "
       "measured effect on the evaluation window—a post-hoc audit label, never an input to the gate—while the "
       "gate itself admits only on a validation-window replay gain above 5 pp with a positive lower bound. The "
       "confusion is therefore between an admission decision taken on validation and a label assigned on the "
       "evaluation window, which is what makes it an honest audit rather than a tautology.**")
t = t[:i] + NEW + t[j:]
p.write_text(t, encoding="utf-8")
print("EN Table XI caption made fully bold")

z = D / "paper_zh.md"
s = z.read_text(encoding="utf-8")
i = s.find("**表 XI.")
if i > 0:
    j = s.find("\n\n", i)
    NEWZ = ("**表 XI. 26 条候选上的审计门。每条候选按其在评估窗口上的实测效应被标为有害、中性或好——这是事后审计标签，"
            "从不作为门的输入；门本身只在候选的验证窗口重放增益高于 5 pp 且下界为正时准入。因此混淆矩阵比较的是"
            "「在验证窗口上做出的准入决定」与「在评估窗口上赋予的标签」，这正是它算作诚实审计而非同义反复的原因。**")
    s = s[:i] + NEWZ + s[j:]
    z.write_text(s, encoding="utf-8")
    print("ZH Table XI caption made fully bold")
