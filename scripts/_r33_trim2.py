"""R33 part 5: compress Claim 2 (no numbers lost) to recover the page."""
from __future__ import annotations

import re
from pathlib import Path

p = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本" / "paper_en.md"
t = p.read_text(encoding="utf-8")

i = t.find("*Claim 2 (binary-outcome channel")
j = t.find("\n\n", i)
OLD = t[i:j]
NEW = ("*Claim 2 (binary-outcome channel: identification fails by support).* Restrict the observer to the realised binary "
       "outcomes {1{T_z ≤ a_i}} at the advances the logger happened to produce. Wherever those advances cover a "
       "neighbourhood of the quantile—by randomisation, or because the policy's own support reaches there—the outcomes "
       "identify F_z there, which is exactly what the probe of Section V-C exploits. In the passive no-shield log of the "
       "baseline policies (|lat| ≥ 68°, ten seeds, 8,682 attempts; Appendix D, Table D1A) the advance distribution "
       "concentrates *below* the requirement: mean lead 9.09 s, 37.7% of attempts in the 6–8 s bucket, 8.1% (705 "
       "attempts, 91 of them late) in the 14–16 s band immediately below the crossing, and 8.9% at or above 16 s. Fig. 4a "
       "shows this and Fig. 4b adds the budget curve: resampling attempts independently collapses the crossing interval "
       "to one grid step, while resampling (seed, site) blocks keeps it at several seconds even at the full passive "
       "budget. The region is therefore *sampled but thin*—with 91 late handovers among 705 attempts the local late rate "
       "has a standard error of ≈1.3 pp, and the band is ≈4.6× thinner than the modal bucket—and at the budgets a field "
       "study can afford the crossing estimated from it is dominated by noise (the probe's own run-to-run sd is 2.45 s "
       "at two episodes per advance). The rule-applied logs (Table D1B) put 91.1% of attempts at 16 s, which is the "
       "rule's own signature; they are a consistency check and the two panels are never pooled. What this establishes is "
       "**effective-support failure at an affordable budget**, not information-theoretic impossibility: the support is "
       "positive—infinitely many samples would identify the quantile—but it under-covers the informative region by ≈4.6×, "
       "and a designed experiment that forces coverage lifts the limitation (Proposition 4).")
t = t[:i] + NEW + t[j:]
t = re.sub(r"\n{3,}", "\n\n", t)
p.write_text(t, encoding="utf-8")
print("claim2 words:", len(re.findall(r"[A-Za-z0-9']+", NEW)), "was", len(re.findall(r"[A-Za-z0-9']+", OLD)))
