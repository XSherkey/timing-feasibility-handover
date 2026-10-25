"""R4 part 2b: apply the remaining wording fixes with the correct anchor for the cluster/probe note."""
from __future__ import annotations

from pathlib import Path

D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"
p = D / "paper_en.md"
t = p.read_text(encoding="utf-8")

old = ("(705 of 8,682 passive attempts in the 14–16 s band, against 37.7% at 6–8 s), and within any "
       "budget a field study can afford the bound is therefore effectively unidentifiable from that "
       "stream alone (Proposition 2: effective-support failure un")
i = t.find(old)
if i < 0:
    raise SystemExit("anchor missing")
# insert a sentence right after the parenthetical, before "and within any budget"
mark = "(705 of 8,682 passive attempts in the 14–16 s band, against 37.7% at 6–8 s)"
if t.count(mark) != 1:
    raise SystemExit(f"mark count {t.count(mark)}")
t = t.replace(mark, mark + ", a cluster-bootstrap *identification* interval that is not the probe's confidence interval (Section V-C)", 1)

# and finish the earlier items that never got written
pairs = [
    ("5. **Small-n effects.** Cross-intent transfer is n = 5 per arm; the penalty drift analysis is 10 seeds with heterogeneous seed-level behaviour (sd 17.9 pp); the drift boundary is five seeds.",
     "5. **Sample sizes.** The cross-intent transfer uses ten training seeds (nine of which committed a rule at intent 0); the drift ladder and the margin sweep use ten policy seeds; the probe-identification study reports five policy seeds and says so where it appears. Seed-level behaviour remains heterogeneous (sd up to 17.9 pp on the reward-penalty arm), which is why every contrast in this paper is paired."),
    ("i.e. at or just beyond the 1.2 pp tolerance defined in Section VI-A",
     "i.e. at or within the 1.2 pp tolerance defined in Section VI-A"),
    ("against a pre-registered\nmargin of 1.0 pp", "against a pre-specified margin of 1.0 pp"),
    ("(ii) *True plateau at the crossing level:* if π is flat at height π(a) = ε′ with π(a) = ε over an interval,",
     "(ii) *True plateau at the crossing level:* if π is flat at height ε over an interval,"),
    ("**τ_used = min(τ\\* + m, 24 s)** is the deployed threshold",
     "**τ_used = min(τ∗ + m, 24 s)** is the deployed threshold"),
]
applied = []
for old_s, new_s in pairs:
    if t.count(old_s) == 1:
        t = t.replace(old_s, new_s, 1)
        applied.append(old_s[:36])
    else:
        print("  MISS:", t.count(old_s), old_s[:60])
p.write_text(t, encoding="utf-8")
print("applied:", applied)
