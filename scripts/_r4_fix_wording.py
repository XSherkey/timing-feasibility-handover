"""R4 (v16) part 2: wording/notation fixes from review 9.

  * Limitation 5: cross-intent n = 5 -> n = 10 (and drift n).
  * Limitation 7: "at or just beyond" -> "at or within".
  * "pre-registered margin" -> "pre-specified margin".
  * Prop 4(ii): the eps'/eps mix-up.
  * Nomenclature: tau\\* -> tau-asterisk operator; a-bar wording.
  * one sentence separating the passive cluster-bootstrap interval from the probe interval.
"""
from __future__ import annotations

from pathlib import Path

D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"
p = D / "paper_en.md"
t = p.read_text(encoding="utf-8")
done = []


def rep(old: str, new: str, label: str) -> None:
    global t
    n = t.count(old)
    if n != 1:
        raise SystemExit(f"[{label}] expected 1, found {n}")
    t = t.replace(old, new, 1)
    done.append(label)


rep("5. **Small-n effects.** Cross-intent transfer is n = 5 per arm; the penalty drift analysis is 10 seeds with heterogeneous seed-level behaviour (sd 17.9 pp); the drift boundary is five seeds.",
    "5. **Sample sizes.** The cross-intent transfer now uses ten training seeds (nine of which committed a rule at intent 0); the drift ladder and the margin sweep use ten policy seeds; the probe-identification study reports five policy seeds and says so where it appears. Seed-level behaviour remains heterogeneous (sd up to 17.9 pp on the reward-penalty arm), which is why every contrast in this paper is paired.",
    "lim5")

rep("i.e. at or just beyond the 1.2 pp tolerance defined in Section VI-A",
    "i.e. at or within the 1.2 pp tolerance defined in Section VI-A",
    "lim7-tol")

rep("against a pre-registered\nmargin of 1.0 pp",
    "against a pre-specified margin of 1.0 pp",
    "tost-wording")

rep("(ii) *True plateau at the crossing level:* if π is flat at height π(a) = ε′ with π(a) = ε over an interval,",
    "(ii) *True plateau at the crossing level:* if π is flat at height ε over an interval,",
    "prop4-ii")

rep("**τ_used = min(τ\\* + m, 24 s)** is the deployed threshold",
    "**τ_used = min(τ∗ + m, 24 s)** is the deployed threshold",
    "nomen-tau")

rep("the passive log covers the informative band thinly—705 of 8,682 attempts (8.1%) fall in the 14–16 s band, against 37.7% in the modal bucket",
    "the passive log covers the informative band thinly—705 of 8,682 attempts (8.1%) fall in the 14–16 s band, against 37.7% in the modal bucket. The cluster-bootstrap interval of 10–18 s quoted below is an *identification* interval for the passive log; it is not the confidence interval of the active probe, which forces coverage and is reported separately in Section V-C",
    "cluster-vs-probe")

p.write_text(t, encoding="utf-8")
print("applied:", done)
