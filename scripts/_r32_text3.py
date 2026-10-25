"""R32 pass 3: fix the line-wrapped cross-intent sentence and the document title metadata."""
from __future__ import annotations

import re
from pathlib import Path

D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"
main = D / "paper_en.md"
t = main.read_text(encoding="utf-8")

pat = re.compile(r"The effect is large because feasibility is intent-independent: whatever the next\s+objective, the "
                 r"constraint removes the same failure class\.")
NEW = ("The effect is large because the constraint removes the same failure class whatever the next objective, but we "
       "state it as an empirical transfer: Proposition 3 bounds the timing channel under one deployment distribution "
       "D_Π, and a change of intent changes that distribution. What we claim is that the shared graph transfers well "
       "over the four intents we test, not that one quantile theorem guarantees it across intents.")
t, n = pat.subn(NEW, t, count=1)
print("cross-intent replaced:", n)
main.write_text(t, encoding="utf-8")

js_path = D / "build_paper_docx.js"
js = js_path.read_text(encoding="utf-8")
old = ': "Probe-Calibrated Conservative Injection of Handover Constraints for Autonomous LEO Satellite Networks";'
new = ': "Timing-Feasibility Constraints for LEO Handover: Attribution, Calibration and Audit in a Digital Twin";'
print("docTitle found:", js.count(old))
js = js.replace(old, new, 1)
js_path.write_text(js, encoding="utf-8")
print("docTitle updated")
