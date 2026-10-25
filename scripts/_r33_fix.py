"""R33: review-26 fixes - tighten the four absolute phrases, scope Props 1 and 4, sync the proof, fix attribution."""
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


# ---------------- 1. four absolute phrases ----------------
rep("the constraint is therefore not recoverable from the log",
    "the constraint is therefore not recoverable *to the precision a deployment needs* from the log we have",
    "intro 'not recoverable'")
rep("the bound is effectively invisible to a learner fed by the passive stream",
    "the bound is effectively invisible to a learner fed by the passive stream at the budgets we test",
    "remark 'any affordable budget'")
rep("the passive process cannot localize the crossing",
    "the passive process cannot localize the crossing to the required 2 s precision",
    "stage-1 'cannot localize'")
rep("a precision floor that a controlled probe removes",
    "a precision floor that a controlled probe is designed to lift", "abstract 'removes'")

# ---------------- 2. Proposition 1: keep it conditional ----------------
rep("The corollary applies to ā = 18 s; with ā = 16 s it would be false, and the 0.93% residual is exactly why the "
    "deployed algorithm carries the 2 s margin.",
    "The proposition is a conditional statement: *if* p(a)=0 for all a ≥ ā, the corollary follows. The 18 s point is an "
    "evaluation-sample observation, not an established zero of the population distribution, so we do not push the "
    "corollary through it; what the sample supports is the weaker statement that the deployed arm carries a 2 s margin "
    "because a 0.93% residual remains at 16 s.", "prop1 conditional")
rep("(with ā = 18 s in this twin; the bound with ā = 16 s would require the 0.93% residual to be zero, which it is not)",
    "(the bound is conditional on the zero-failure premise; the 0.93% residual at 16 s is why the deployed arm carries "
    "a margin instead of relying on it)", "prop1 parenthetical")

# ---------------- 3. Proposition 4: what is estimated ----------------
rep("*Claim.* The forced-advance experiment observes π(a) = P(late | a) = P(T_z > a), a non-increasing survival "
    "function, on the grid G = {6, 8, …, 26} s.",
    "*Claim.* What the experiment estimates is the survival function of the realised requirement, π(a) = P(T_z > a), on "
    "the grid G = {6, 8, …, 26} s, from the realised setups recorded at each forced advance. It is *not* the "
    "unconditional observed late rate: that rate also absorbs the competing classes, so π(a) and P(late at advance a) "
    "coincide only when route and window failures are independent of the requirement at that advance, which is an "
    "assumption we flag rather than verify.", "prop4 claim aligned")

# ---------------- 4. supplement: proof must be conditioned ----------------
i = s.find("(i) Under Π_τ the executed advance is max(a, τ)")
if i > 0:
    j = s.find("\n\n", i)
    OLD = s[i:j]
    NEW = ("*Proof.* (i) Condition on the protected scope A_Π, where Π_τ acts: the executed advance is max(a, τ) ≥ τ, so "
           "the timing-failure event satisfies {late under Π_τ} = {T_z > max(a, τ)} ⊆ {T_z > τ}, and with τ a "
           "(1−ε)-quantile of T_z under D_Π we get P(late under Π_τ | A_Π) ≤ P(T_z > τ | A_Π) ≤ ε by the quantile "
           "property. The inclusion is strict whenever the policy already chose a > τ (the projection then leaves the "
           "action unchanged and the attempt can still be late for T_z ∈ (τ, a]); the bound therefore holds with equality "
           "only in the special case a ≤ τ almost surely. Outside A_Π no projection is applied, so nothing is claimed "
           "there. (ii) The unconditional tail bound does not control the conditional tail; a counterexample suffices "
           "(take E ⊇ {T_z > τ} with P(E) ≪ 1). (iii) Each dependence is present in the conjunction; (4) contains none "
           "of them. □")
    s = s[:i] + NEW + s[j:]
    done.append("supp proof conditioned")

# ---------------- 5. attribution: name the 16 s arm ----------------
rep("between the reward-only baseline and the shielded system",
    "between the reward-only baseline and the 16 s mined-rule arm without the margin",
    "contributions #1 attribution")
for m in list(re.finditer(r"23\.4 of the 24\.1 pp", t))[1:]:
    pass
t, n = re.subn(r"(23\.4 of the 24\.1 pp)(?! gap between a reward-only baseline \(68\.37%\))",
               lambda mm: mm.group(1), t)
print("  attribution sites:", len(re.findall(r"23\.4 of the 24\.1 pp", t)))

# ---------------- 6. 'evaluation row' -> 'evaluation-window column' ----------------
t = t.replace("the evaluation row of Table VII", "the evaluation-window column of Table VII")
done.append("evaluation row wording")

main.write_text(re.sub(r"\n{3,}", "\n\n", t), encoding="utf-8")
supp_path.write_text(re.sub(r"\n{3,}", "\n\n", s), encoding="utf-8")
print("edits:", done)
