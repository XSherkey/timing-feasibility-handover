"""Fix the figure placement: cite Fig. 6 in the body (EN + ZH) and refresh the builder metadata."""
from __future__ import annotations

from pathlib import Path

D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"

# ---- EN: cite Fig. 6 at the end of Section VI-D --------------------------
p = D / "paper_en.md"
t = p.read_text(encoding="utf-8")
old = ("These are measured statements over five seeds and three regimes, not a probabilistic guarantee; "
       "a guarantee would require confidence bounds on the probe curve plus a bounded-drift assumption "
       "between calibration and deployment physics, neither of which we claim.")
new = ("These are measured statements over five seeds and three regimes, not a probabilistic guarantee; "
       "a guarantee would require confidence bounds on the probe curve plus a bounded-drift assumption "
       "between calibration and deployment physics, neither of which we claim. Fig. 6 puts the six "
       "reference points on one axis at nominal and at +2 s of drift, on identical episodes: every arm "
       "that does not re-measure falls with the physics, and only the probe-calibrated shield and the "
       "per-attempt oracle stay where they started.")
if t.count(old) != 1:
    raise SystemExit("EN anchor not found")
t = t.replace(old, new, 1)
p.write_text(t, encoding="utf-8")
print("EN: Fig. 6 cited")

# ---- ZH: same place ------------------------------------------------------
p = D / "paper_zh.md"
t = p.read_text(encoding="utf-8")
i = t.find("### D. 常数基线的失效边界")
j = t.find("### E.", i)
seg = t[i:j]
tail = seg.rstrip().split("\n")[-1]
if not tail:
    raise SystemExit("ZH tail not found")
add = ("图 6 把六个参照点放在同一根轴上（标称与 +2 s 漂移、相同回合）：不做重新测量的臂都随物理一起下坠，"
       "只有探测标定的盾与逐尝试 oracle 留在原处。")
t = t[:j].rstrip() + "\n\n" + add + "\n\n" + t[j:]
p.write_text(t, encoding="utf-8")
print("ZH: Fig. 6 cited")

# ---- builder metadata ----------------------------------------------------
js = D / "build_paper_docx.js"
s = js.read_text(encoding="utf-8")
s = s.replace(': "Feasibility, Not Learning: Censoring-Aware Mining and Conservative Injection of Handover Constraints for Autonomous LEO Satellite Networks";',
              ': "Probe-Calibrated Conservative Injection of Handover Constraints for Autonomous LEO Satellite Networks";')
s = s.replace(': "可行性，而非学习：面向自主 LEO 卫星网络的切换约束感知挖掘与保守注入";',
              ': "面向自主 LEO 卫星网络的探测标定式切换约束保守注入";')
js.write_text(s, encoding="utf-8")
print("builder metadata updated")
