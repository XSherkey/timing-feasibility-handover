"""R20 part 3: compress Related Work, fold Table Xb into a statistics paragraph, trim protocol and LLM subsections."""
from __future__ import annotations

import re
from pathlib import Path

D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"
p = D / "paper_en.md"
t = p.read_text(encoding="utf-8")
edits = []


def swap(old: str, new: str, label: str) -> None:
    global t
    if t.count(old) != 1:
        print("  MISS", label, t.count(old))
        return
    t = t.replace(old, new, 1)
    edits.append(label)


# ---------------------------------------------------------------- 1. Table Xb -> paragraph
i = t.find("**Table Xb.")
if i > 0:
    j = t.find("\n\n", t.find("| deployed − reward λ = 8", i))
    block = t[i:j]
    STAT = ("**Paired statistics.** Over the ten policy seeds, deployed − mined 16 s = +0.53 pp "
            "(95% CI +0.38 to +0.94, exact Wilcoxon p ≤ 0.002); deployed − PPO-MLP+16 s = +1.17 pp "
            "(+0.38 to +2.40, p ≤ 0.004); deployed − reward λ = 8 = +10.42 pp (+5.65 to +17.24, p ≤ 0.002); "
            "deployed − tuned constant = −0.00 pp (−0.08 to +0.06, p ≤ 1.000), which is equivalence at the "
            "pre-specified 1.0 pp margin (TOST p < 0.001). Intervals span the four per-instance bootstrap "
            "resamples; p values are the largest of the four exact tests.")
    t = t[:i] + STAT + t[j:]
    edits.append("Table Xb -> paragraph")

# ---------------------------------------------------------------- 2. Related work, tighter
old_start = "**LLMs as translators of intent into rewards.**"
old_end = "**Positioning.** Table I summarizes"
i = t.find(old_start)
j = t.find(old_end)
if i > 0 and j > i:
    NEW_RW = """**LLMs as translators of intent.** Language models have been used to turn operator intent into network configurations, service-level objectives and RL reward functions—zero-touch configuration, generative intent abstraction, LLM-searched reward functions, LLM-as-teacher, Eureka-style reward code and reward generation from task descriptions [3]–[9]. They establish that semantic translation works; their shared and usually unstated assumption is that the reward is the right place for the translated knowledge. Our experiments contradict that assumption under control: the same constraint placed in the reward needs a coefficient ≈10× beyond any reasonable default, peaks 9.2 pp below the decision-layer form, and buys no robustness to physical drift, while the decision-layer form is coefficient-free (Section VI-C). *Where* operational knowledge enters the loop is thus the design variable, not how well it is translated.

**Reflection, shielding, censoring.** Reflexion-style agents improve by verbal self-reflection in episodic memory [2]; our backward loop shares the motive but grounds reflection in twin telemetry, validates hypotheses by counterfactual replay on disjoint data, and persists them in a versioned graph rather than in free text. Shields and runtime assurance are established—a monitor overrides actions that would violate a hand-written specification [1], [29]. We do not claim the shield as novel. Here the specification is *mined from censored failure logs*, its parameter is *measured on the deployed policy* with a cost-asymmetric margin, and the shield doubles as an *audit instrument*: because the projection bounds the timing channel by ε (Proposition 3), it separates what the policy learned from what the constraint enforces, which is the decomposition our experiments exploit. Right-censoring itself is textbook survival analysis [10], [11]; what we have not seen in the networked-systems literature is the use of *support failure* to explain why passive logs cannot pin down a timing constraint that trained policies leave almost unexercised (705 of 8,682 attempts in the informative band; Proposition 2), and a designed probe as the instrument that restores the missing support (Proposition 4). Censoring alone implies no universal non-identifiability—binary outcomes at well-spread advances do identify the curve, and the probe relies on it; the obstacle in passive operation is that advances are neither well spread nor independent of the environment. Isotonic (PAVA) regression supplies the monotone fit [30], [31]; constrained MDPs and shaping [12], [14], [24] encode requirements in the objective, and our results delimit rather than contradict them: a requirement censored in the logs cannot be learned through the reward at any coefficient without distorting the objective (Proposition 1), whereas at decision time it is exact and auditable. Twins of orbital mechanics and link budgets are used mainly for offline validation [16]–[18]; we use the twin as the ground truth against which mined constraints are stress-tested, including under deliberate physics perturbations.

"""
    t = t[:i] + NEW_RW + t[j:]
    edits.append("Related Work compressed")

# ---------------------------------------------------------------- 3. Protocol subsection trim
old = t[t.find("### A. Protocol"):t.find("### B. Feasibility dominates")]
if len(old) > 500:
    NEW_A = """### A. Protocol

Every number in this paper comes from one of two calibration protocols, and the protocol is stated wherever a number appears. In the **archival** protocol the three choices (predicate, threshold, margin) were fixed on the evaluation window itself; in the **three-way** protocol they were fixed on the validation window only, and the evaluation window and three epoch-shifted lockbox instances were then scored once. Tables III–VIII, XI and XII report archival numbers, with the evaluation row of Table X; the lockbox columns of Table IX and Table X report three-way numbers. Nothing else differs: campaigns use the same ten policy seeds, traffic seed 0 and identical episodes, so a difference between arms is a difference in what was injected, not in what was sampled.

Arms are the frozen campaign checkpoints: a no-knowledge PPO-MLP baseline, the mined 16 s rule applied at decision time, the same rule once as a reward penalty at λ = 8, the probed threshold with margin (τ_used = 18 s), a tuned constant 18 s lead with no learning, the shield applied to the baseline's weights, and an oracle that clamps each attempt to its realised requirement. Statistics are paired on the policy seed throughout (Section VI-J); *n* always counts independent training runs, never episodes.

"""
    t = t.replace(old, NEW_A)
    edits.append("Protocol compressed")

# ---------------------------------------------------------------- 4. LLM subsection trim
i = t.find("### L. What the language model actually proposes")
j = t.find("### M. Limitations")
if i > 0 and j > i:
    NEW_L = """### L. What the language model actually proposes

The discovery stage is a language model, so its reliability matters. We ran the miner twenty times on the training-window narratives (Appendix E reproduces three calls verbatim, prompt and raw JSON). All twenty proposals are schema-valid: every predicate uses declared telemetry fields and an executable effect, so the mechanical rule admits 20/20. What the model reliably gets right is the *predicate*—the polar band, the latitude field, the direction of the inequality—and what it does not get right is the *magnitude*: proposals cluster at 10–12 s against a measured requirement of 16 s, and the two prompt variants disagree on magnitude far more often than on predicate. The predicate is therefore admitted, and the magnitude is re-measured by the probe rather than taken from the model, which is exactly the division of labour of Section V.

Two human-labelled views of the same twenty proposals disagree with the mechanical rule and with each other: a domain labeler judged 4 of 20 deployable as written, while a coarser reading judged 12. Neither disagreement is about syntax; both are about whether a rule that is *true* on the training window is *safe* on the deployed one—the question the audit gate answers by replay rather than by reading.\n\n"""
    t = t[:i] + NEW_L + t[j:]
    edits.append("LLM subsection compressed")

t = re.sub(r"\n{3,}", "\n\n", t)
p.write_text(t, encoding="utf-8")
print("edits:", edits)
print("words now:", len(re.findall(r"[A-Za-z0-9']+", t)))
