"""R24 part 2: a 210-word abstract that also scopes the claim to the twin we audit."""
from __future__ import annotations

import re
from pathlib import Path

p = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本" / "paper_en.md"
t = p.read_text(encoding="utf-8")

i = t.find("**Abstract—**")
j = t.find("**Index Terms—**")
old = t[i:j]

NEW = """**Abstract—** Handover reliability in low Earth orbit constellations is usually treated as a reinforcement-learning problem. We reproduce one such system and audit what its gains consist of. On a 350-satellite twin, a single timing constraint explains nearly all of the reported improvement: applied to frozen weights on identical episodes, a lower bound on the handover lead raises polar handover success from 67.5 ± 13.2% to 92.44 ± 0.07%, and to 93.36 ± 0.05% with a 2 s cost-asymmetric margin; without it ten checkpoints scatter across 49.8–90.0%. The bound is not recoverable from the passive log: only 8.1% of attempts fall in the informative band, and a cluster bootstrap over (seed, site) blocks places the 5% crossing anywhere between 10 s and 18 s. Holding the shield, the probe and the margin fixed, six provenance variants land within 0.11 pp of the full pipeline, and a highest-elevation controller whose lead is re-selected on the validation window matches it within 0.03 pp with no learning at all. What matters is calibration and admission: under 2 s of acquisition drift a reward penalty falls *below* having no knowledge at all (52.0% against 54.6%), while the re-probed threshold holds 93.2% against 86.0% for a tuned constant. In the twin we audit, the contribution is the calibration-and-audit protocol, not the learner.

"""
t = t[:i] + NEW + t[j:]
p.write_text(t, encoding="utf-8")
print("abstract words:", len(re.findall(r"[A-Za-z0-9']+", NEW)))
