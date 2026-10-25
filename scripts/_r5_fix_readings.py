"""Fix the contradictory 'every drift level' phrasing in the ladder readings (EN + ZH)."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / "almond-repro"
D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"
lad = json.loads((ROOT / "results" / "routeA_r3" / "ladder_consistent" / "summary.json").read_text(encoding="utf-8"))
R = lad["regimes"]
mn = lambda reg, arm: R[reg][arm]["summary"]["mean"]
d = [mn(t, "reward_lam8") - mn(t, "no_knowledge") for t in ("nominal", "plus2s", "plus3p2s", "plus4p4s")]

p = D / "paper_en.md"
t = p.read_text(encoding="utf-8")
old = ("the reward-penalty arm falls *below* the no-knowledge policies at every drift level "
       "(%s pp), so a penalty trained on the nominal requirement is worse than no knowledge once the "
       "requirement moves." % ", ".join("%+.1f" % x for x in d))
new = (f"the reward-penalty arm starts {d[0]:+.1f} pp *above* the no-knowledge policies at nominal physics and "
       f"ends {abs(d[-1]):.1f} pp *below* them once the requirement has moved "
       f"({', '.join('%+.1f' % x for x in d)} pp at δ = 0/+2/+3.2/+4.4 s), so a penalty trained on the nominal "
       f"requirement is worse than no knowledge as soon as the requirement moves.")
if t.count(old) != 1:
    print("  EN anchor count", t.count(old))
else:
    t = t.replace(old, new, 1)
    p.write_text(t, encoding="utf-8")
    print("EN fixed")

z = D / "paper_zh.md"
s = z.read_text(encoding="utf-8")
old_z = ("奖励惩罚臂在**每一个**漂移档位下都落到无知识策略**之下**（%s pp），即按标称需求训练出的惩罚，"
         "一旦需求移动就比没有知识更差。" % ", ".join("%+.1f" % x for x in d))
new_z = (f"奖励惩罚臂在标称物理下比无知识策略高 {d[0]:+.1f} pp，而需求一旦移动就落到它们**之下**，最终低 "
         f"{abs(d[-1]):.1f} pp（δ = 0/+2/+3.2/+4.4 s 处分别为 {', '.join('%+.1f' % x for x in d)} pp）——"
         f"按标称需求训练出的惩罚，需求一移动就比没有知识更差。")
if s.count(old_z) != 1:
    print("  ZH anchor count", s.count(old_z))
    i = s.find("奖励惩罚臂在**每一个**漂移档位下")
    print("  ZH context:", repr(s[i:i + 120]))
else:
    s = s.replace(old_z, new_z, 1)
    z.write_text(s, encoding="utf-8")
    print("ZH fixed")
