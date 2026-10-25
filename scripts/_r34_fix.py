"""R34: review-27 fixes - the Proposition 1 sign, the probe estimand, and the number/label conflicts."""
from __future__ import annotations

import re
from pathlib import Path

D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"
main = D / "paper_en.md"
supp_path = D / "supplementary" / "supp_en.md"
t = main.read_text(encoding="utf-8")
s = supp_path.read_text(encoding="utf-8")
done = []


def rep(old, new, label, target="main"):
    global t, s
    src = t if target == "main" else s
    n = src.count(old)
    if n != 1:
        print("  MISS", label, n)
        return
    if target == "main":
        t = t.replace(old, new, 1)
    else:
        s = s.replace(old, new, 1)
    done.append(label)


# ---------------- 1. Proposition 1: the left-neighbour inequality ----------------
rep("λ·[p(a*−Δ) − p(a*)] ≤ Δr(a*−Δ, a*) and λ·[p(a*) − p(a*+Δ)] ≤ Δr(a*, a*+Δ)",
    "λ·[p(a*−Δ) − p(a*)] ≥ Δr(a*−Δ, a*)  and  λ·[p(a*) − p(a*+Δ)] ≤ Δr(a*, a*+Δ)",
    "prop1 left inequality")
rep("at any global maximizer a*(λ) ∈ argmax_{a∈G} R_λ, neither adjacent move improves:",
    "at any global maximizer a*(λ) ∈ argmax_{a∈G} R_λ, no adjacent move improves (for a* at the edge of the grid only "
    "the interior neighbour exists, and the corresponding inequality is the only one that applies):",
    "prop1 boundary caveat")

# ---------------- 2. Proposition 4: unify what is observed ----------------
rep("*Claim.* What the experiment estimates is the survival function of the realised requirement, π(a) = P(T_z > a), on "
    "the grid G = {6, 8, …, 26} s, from the realised setups recorded at each forced advance. It is *not* the "
    "unconditional observed late rate: that rate also absorbs the competing classes, so π(a) and P(late at advance a) "
    "coincide only when route and window failures are independent of the requirement at that advance, which is an "
    "assumption we flag rather than verify.",
    "*Claim.* The estimand is the late-rate curve the probe can actually observe, π̂(a) = P(late at commanded advance a "
    "under forced coverage), sampled on the grid G = {6, 8, …, 26} s and fitted by PAVA; the crossing is where the fit "
    "falls to ε. The ideal target π(a) = P(T_z > a) coincides with π̂ only when routing and window failures are "
    "independent of the requirement at that advance, which we assume rather than verify. The twin additionally records "
    "the realised setup time of every attempt—a *simulator privilege*, not something a deployed gateway necessarily "
    "reports—and we use it only as a diagnostic: the two agree here to within a grid step (the probe's crossing is 16 s "
    "on every seed, the realised-requirement 95th percentile is 15.80 s), which is the check that supports the "
    "assumption in this twin. A real deployment that cannot report T_z can still run this probe, because the estimator "
    "reads success and failure, not T_z.",
    "prop4 estimand unified")

# ---------------- 3. probe budget: one pair of numbers ----------------
rep("an estimator-bias phenomenon: doubling the budget from 2 to 8 episodes per advance *lowered* the estimate from the "
    "16 s grid point toward 14 s",
    "an estimator-bias phenomenon: raising the budget from 2 to 16 episodes per advance *lowered* the estimate from the "
    "16 s grid point toward 14 s", "probe budget 8->16")

# ---------------- 4. Fig. 6 caption: eight points incl. lambda = 0 ----------------
rep("polar HSR against the penalty coefficient λ over the eight-point scan (error bars ±sd over ten seeds)",
    "polar HSR against the penalty coefficient λ over eight points—the seven coefficients of the scan plus the "
    "no-penalty arm λ = 0 (error bars ±sd over ten seeds)", "fig6 eight-point")

# ---------------- 5. abstract wording: separation and scope ----------------
rep("at +2 s the tuned constant still holds 92.4% against 93.2% for the re-probed threshold, and only at +3.2 s do the "
    "two separate (86.0% against 93.2%).",
    "at +2 s the tuned constant still holds 92.4% against 93.2% for the re-probed threshold, and the two separate "
    "materially only at +3.2 s (86.0% against 93.2%).", "abstract separation")
rep("the two bounds act on one interval, and its length, not either endpoint, sets the score.",
    "the two bounds act on one interval, and in the settings we test its length, not either endpoint, sets the score.",
    "abstract interval scope")

# ---------------- 6. A7 predicate footnote in the isolation table ----------------
rep("A8 is deterministic: its row reports the difference from A0 measured against A0's seed distribution",
    "A7 removes the language model, the Kaplan–Meier stage and the gate, but its rule carries one extra atom "
    "(`elevation_deg >= 15`) that A0 does not, so A7 is a pipeline-level ablation rather than a pure component "
    "ablation and we read it as such. A8 is deterministic: its row reports the difference from A0 measured against "
    "A0's seed distribution", "A7 caveat")

# ---------------- 7. Fig. 4 caption: the probe's observable curve ----------------
rep("(a) Late-handover rate against the handover advance in the passive no-shield log",
    "(a) Late-handover rate against the handover advance in the passive no-shield log",
    "fig4 anchor")

main.write_text(re.sub(r"\n{3,}", "\n\n", t), encoding="utf-8")
supp_path.write_text(re.sub(r"\n{3,}", "\n\n", s), encoding="utf-8")
print("edits:", done)
