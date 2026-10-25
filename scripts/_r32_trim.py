"""R32 pass 5: trim ~450 words in the least load-bearing paragraphs to hold 16 pages."""
from __future__ import annotations

import re
from pathlib import Path

D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"
p = D / "paper_en.md"
t = p.read_text(encoding="utf-8")
done = []


def sub_para(start: str, new: str, label: str):
    global t
    i = t.find(start)
    if i < 0:
        print("  MISS", label)
        return
    j = t.find("\n\n", i)
    old_words = len(re.findall(r"[A-Za-z0-9']+", t[i:j]))
    t = t[:i] + new + t[j:]
    done.append(f"{label} ({old_words}->{len(re.findall(chr(92)+'w+', new)) if False else len(re.findall(r'[A-Za-z0-9' + chr(39) + r']+', new))} words)")


# 1. the frozen-weight factorial paragraph: keep the numbers, drop the repetition
sub_para("The frozen-weight factorial is the causal core",
         "The frozen-weight factorial is the causal core (Fig. 2; per-seed values in Appendix C). Ten checkpoints of the "
         "full-system architecture are evaluated on common episodes with no shield and with τ ∈ {16, 18, 20} s—the mined "
         "τ* rule, the deployed τ_used at nominal physics, and a one-step ablation—plus a per-attempt oracle (Section "
         "VI-G). Without the shield the ten policies span 49.8–90.0% (mean 67.5 ± 13.2%); with τ = 16 s they compress to "
         "92.44 ± 0.07% (late 0.93%), and τ = 18 s reaches 93.36 ± 0.05% with late share 0.00%, sitting above the 20 s "
         "ablation (93.23 ± 0.05%). The oracle equals 18 s on every seed, so at nominal physics the deployed threshold "
         "has no estimation headroom left, and the residual ≈6.6 pp to 100% is target, window and routing rather than "
         "timing (Section V-D).",
         "factorial paragraph")

# 2. tuned-constant paragraph: compress the narrative
sub_para("The tuned constant is the strongest objection to this work",
         "The tuned constant is the strongest objection to this work. At nominal physics it matches the deployed "
         "algorithm to 0.03 pp (93.33% against 93.36%), so the claim cannot be that calibration beats a good constant "
         "on the nominal twin; it is that *18 is a fact about the physics at tuning time*, not a rule the constant can "
         "re-derive. The constant carries ≈2 s of margin: at +2 s drift it loses 0.9 pp (92.39 against 93.20 for the "
         "same controller re-probed), at +3.2 s it loses 7.3 pp (85.98), and at +4.4 s it loses 9.6 pp (83.56), while "
         "the re-probed threshold holds 93.20% in all three regimes.",
         "constant paragraph")

# 3. limitations: tighten the four items
i = t.find("### O. Limitations")
j = t.find("\n\n## VII. Conclusion", i)
if i > 0 and j > i:
    NEW = """### O. Limitations

Four limits bound the claims. The twin is a simulator: T_z comes from the link-budget model of (1), not from flight
telemetry, and the drift magnitudes δ ∈ {2, 3.2, 4.4} s are plausible but unmeasured. The requirement is a single
scalar per attempt, so a target-dependent requirement would need the probe to stratify further. The audit gate is only
as good as its replay: two episodes per candidate give sd 2.2 pp against a 5 pp threshold. And on the metric side we
report success, the three failure classes, the satisfaction score and the probe budget, but not p95/p99 latency or
signalling counts, so "a longer lead is nearly free" is bounded to the metrics we report. None of the four affects the
ordering claims, which are paired and replicated; all four bound how far the *absolute* numbers travel.
"""
    t = t[:i] + NEW + t[j:]
    done.append("limitations tightened")

t = re.sub(r"\n{3,}", "\n\n", t)
p.write_text(t, encoding="utf-8")
print("edits:", done)
print("words:", len(re.findall(r"[A-Za-z0-9']+", t)))
