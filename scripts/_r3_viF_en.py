"""R3 (v11): update the cross-intent prose (n = 8, exact p, discovery-failure note)."""
from __future__ import annotations

from pathlib import Path

D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"
p = D / "paper_en.md"
t = p.read_text(encoding="utf-8")

old_start = t.find("### F. One constraint, four intents")
old_end = t.find("### G.", old_start)
NEW = """### F. One constraint, four intents

A constraint mined under a reliability-first intent is inherited by three later intents that are
**forbidden to mine**: latency-first, power-first and balanced. Under a shared knowledge graph the
three reach 89.59%, 89.41% and 90.33%; with a fresh graph per intent they reach 76.53%, 71.60% and
75.28%. The gain is +13.06, +17.81 and +15.05 pp, exact two-sided Wilcoxon p = 0.0156 on eight
training seeds (Table V), and the first intent—which is identical in both arms—differs by 0.04 pp
(p = 1.00), as it must. The effect is large because feasibility is intent-independent: whatever the
next objective, the constraint removes the same failure class.

Two qualifications belong with the number. *First, discovery does not always commit.* On one of the
eight seeds the discovery pipeline returned no committed rule (the gate admitted nothing), and on that
seed both arms fall to 72–76%; we report it rather than drop it, because it is the honest failure rate
of an automatic pipeline (7/8 commits). *Second,* the seeds on which nothing was committed contribute
identically to both arms, so they dilute the contrast rather than bias it.

"""
t = t[:old_start] + NEW + t[old_end:]
p.write_text(t, encoding="utf-8")
print("VI-F prose replaced")
