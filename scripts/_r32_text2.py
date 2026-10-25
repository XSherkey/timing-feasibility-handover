"""R32 pass 2: cross-intent wording, Table H1 label, and a check of the docx title metadata."""
from __future__ import annotations

import re
from pathlib import Path

D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"
main = D / "paper_en.md"
supp_path = D / "supplementary" / "supp_en.md"
t = main.read_text(encoding="utf-8")
s = supp_path.read_text(encoding="utf-8")
done = []

# 1. cross-intent: empirical transfer, not a theorem
old = ("The effect is large because feasibility is intent-independent: whatever the next objective, the constraint "
       "removes the same failure class.")
new = ("The effect is large because the constraint removes the same failure class whatever the next objective, but we "
       "state it as an empirical transfer: Proposition 3 bounds the timing channel under one deployment distribution "
       "D_Π, and a change of intent changes that distribution. What we claim is that the shared graph transfers well in "
       "the four intents we test, not that a single quantile theorem guarantees it across intents.")
if t.count(old) == 1:
    t = t.replace(old, new, 1)
    done.append("cross-intent wording")

# 2. Table H1: say which 16 s rule the row is
old = ("**Table H1. Drift ladder (polar HSR, |lat| ≥ 70°, campaign policies, traffic seed 0, identical episodes, ten "
       "policy seeds per grid point; δ is extra acquisition signalling latency). Protocol: archival.**")
new = ("**Table H1. Drift ladder (polar HSR, |lat| ≥ 70°, campaign policies, traffic seed 0, identical episodes, ten "
       "policy seeds per grid point; δ is extra acquisition signalling latency). Protocol: archival. The row labelled "
       "“16 s rule” is the narrative-inferred rule of Section VI-D—same magnitude, a wider predicate drawn from the "
       "failure narratives—not the mined-rule campaign arm of Table III, whose 16 s value is 92.44%, so the two rows "
       "are not the same experiment and must not be compared row-wise.**")
if s.count(old) == 1:
    s = s.replace(old, new, 1)
    done.append("Table H1 label")

main.write_text(re.sub(r"\n{3,}", "\n\n", t), encoding="utf-8")
supp_path.write_text(re.sub(r"\n{3,}", "\n\n", s), encoding="utf-8")
print("edits:", done)

# 3. where does the docx title metadata come from?
b = D / "build_paper_docx.js"
js = b.read_text(encoding="utf-8")
for m in re.finditer(r".*docTitle.*", js):
    print("   ", m.group(0)[:120])
