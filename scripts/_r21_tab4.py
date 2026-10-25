"""R21 part 5: move Table IV (10-column dose-response grid, plotted in Fig. 4) to the supplement, and trim the closing sections."""
from __future__ import annotations

import re
from pathlib import Path

D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"
p = D / "paper_en.md"
supp_path = D / "supplementary" / "supp_en.md"
t = p.read_text(encoding="utf-8")
supp = supp_path.read_text(encoding="utf-8")

before = len(re.findall(r"^\*\*Table ", t, flags=re.M))

i = t.find("**Table IV.")
j = t.find("\n\n", t.find("| λ = 64 |", i))
if i > 0 and j > i:
    block = t[i:j]
    t = t[:i] + ("*Grid.* The full λ grid behind Fig. 4 is Table M1 of the supplementary material.\n") + t[j:]
    supp = supp.rstrip() + "\n\n## Appendix M. Dose-response grid\n\n" + block.replace(
        "**Table IV.", "**Table M1.") + "\n"
    print("Table IV moved")

after = len(re.findall(r"^\*\*Table ", t, flags=re.M))
print("main tables:", before, "->", after)

# trim the limitations and conclusion
i = t.find("### M. Limitations")
if i > 0:
    j = t.find("## VII. Conclusion", i)
    OLD = t[i:j]
    NEW = """### M. Limitations

Three limits bound the claims. The twin is a simulator: T_z comes from a link-budget model calibrated to published
constellation and terminal parameters, not from flight telemetry, and the drift magnitudes δ ∈ {2, 3.2, 4.4} s are
plausible but not measured on orbit. The requirement is a single scalar per attempt; a requirement that depends on
the *target* as well as the region would need the probe to stratify further, which the plateau analysis suggests is
feasible but we have not run. And the audit gate is only as good as its replay: with two episodes per candidate its
estimator has sd 2.2 pp against a 5 pp threshold, so borderline candidates are coin flips until eight episodes
tighten sd to 0.6 pp. None of the three affects the ordering claims, which are paired and replicated; all three
bound how far the *absolute* numbers travel.

"""
    t = t[:i] + NEW + t[j:]
    print("limitations compressed")

p.write_text(re.sub(r"\n{3,}", "\n\n", t), encoding="utf-8")
supp_path.write_text(supp, encoding="utf-8")
print("words:", len(re.findall(r"[A-Za-z0-9']+", t)))
