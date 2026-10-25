"""R20 part 4: second compression pass (scope paragraph, intro, method, lockbox)."""
from __future__ import annotations

import re
from pathlib import Path

D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"
p = D / "paper_en.md"
t = p.read_text(encoding="utf-8")
edits = []


def swap(old: str, new: str, label: str) -> None:
    global t
    n = t.count(old)
    if n != 1:
        print("  MISS", label, n)
        return
    t = t.replace(old, new, 1)
    edits.append(label)


# 1. Proposition 1 scope paragraph: keep the claim, drop the repetition
i = t.find("*Scope.* This is a result about one reward family")
if i > 0:
    j = t.find("\n\n### C. Proposition 2", i)
    NEW = ("*Scope.* This is a result about one reward family on a discrete grid, not about any reward optimizer: "
           "the penalty −λp(a) does carry information about F_z, and a large enough coefficient can in principle "
           "push the advance into the feasible band. What the proposition establishes is structural—the optimum "
           "lands where marginal cost balances λ-discounted marginal failure reduction (i) and can never pass the "
           "point where failures vanish (ii)—so a reward channel that must distort the objective to reach "
           "feasibility stops strictly short of the requirement below that distortion threshold. The dose-response "
           "of Section VI-C (peak at λ = 8, reversal beyond it, 9.2 pp below the shield, per-attempt lead stuck at "
           "9.5–10.2 s) is the measured signature of (i), not an assumed consequence.")
    t = t[:i] + NEW + t[j:]
    edits.append("Prop-1 scope shortened")

# 2. Introduction: the paragraph that restates the abstract in list form
old = ("We find this worth reporting for three reasons. First, the effect is large and causal")
i = t.find(old)
if i > 0:
    j = t.find("\n\n", t.find("constraint is worth twenty.", i))
    if j < 0:
        j = t.find("\n\n", i)
    t = t[:i] + ("We report this for three reasons. The effect is large and causal—applying the constraint to frozen "
                 "weights, with every other factor held constant, moves mean polar HSR from 67.5% ± 13.2% to "
                 "93.36% ± 0.05%, and the per-seed spread collapses from 49.8–90.0% to 93.3–93.5% (Fig. 2). The "
                 "learned component, by contrast, is worth a few points: across arms the policies are hard to tell "
                 "apart from a hand-crafted baseline (Section VI-B). Second, the *reason* the gain is missed is "
                 "structural: trained policies concentrate below the requirement (mean lead ≈ 9.5–11.3 s against a "
                 "16 s need), so the region that would inform the estimate is barely sampled—705 of 8,682 passive "
                 "attempts in the 14–16 s band—and the constraint is therefore not recoverable from the log that "
                 "records the failure. Third, the same constraint behaves completely differently depending on where "
                 "it is injected: as a reward term it needs an order-of-magnitude coefficient, lands 10.4 pp below "
                 "the decision-layer form, and buys no robustness; as a shield it needs no learning, no coefficient, "
                 "and tracks the physics when the requirement is re-measured.\n\n") + t[j + 2:]
    edits.append("Introduction list compressed")

# 3. Method: fold the four stage headings into one paragraph each
t = t.replace("**Stage 1—censor-aware fitting.**", "**Stage 1: censor-aware fitting.**")
edits.append("stage headings kept")

t = re.sub(r"\n{3,}", "\n\n", t)
p.write_text(t, encoding="utf-8")
print("edits:", edits)
print("words now:", len(re.findall(r"[A-Za-z0-9']+", t)))
