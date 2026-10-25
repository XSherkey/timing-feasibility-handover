"""R33 part 3: trim two long paragraphs to hold 16 pages without touching the new content."""
from __future__ import annotations

import re
from pathlib import Path

p = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本" / "paper_en.md"
t = p.read_text(encoding="utf-8")
done = []


def sub_para(start: str, new: str, label: str):
    global t
    i = t.find(start)
    if i < 0:
        print("  MISS", label)
        return
    j = t.find("\n\n", i)
    old = len(re.findall(r"[A-Za-z0-9']+", t[i:j]))
    t = t[:i] + new + t[j:]
    done.append(f"{label}: {old}->{len(re.findall(chr(39)+chr(39), new)) if False else len(re.findall(r'[A-Za-z0-9]+', new))}w")


# 1. the reflected-censoring paragraph in II (related work) - keep the citation, cut the enumeration
sub_para("**Reflection, shielding, censoring.**",
         "**Reflection, shielding, censoring.** Reflexion-style agents improve by verbal self-reflection in episodic "
         "memory [2]. Shields and runtime assurance are established—a monitor overrides actions that would violate a "
         "hand-written specification [1], [29]. We claim neither as novel: here the specification is *mined from "
         "censored failure logs*, its parameter is *measured on the deployed policy* with a cost-asymmetric margin, and "
         "the shield doubles as an *audit instrument* that separates what the policy learned from what the constraint "
         "enforces. Right-censoring itself is textbook survival analysis [10], [11]; what we have not seen in this "
         "literature is the use of *support failure* to explain why passive logs cannot pin a timing constraint down to "
         "the precision a deployment needs (705 of 8,682 attempts in the informative band; Proposition 2), with a "
         "designed probe as the instrument that restores the support (Proposition 4). Isotonic (PAVA) regression "
         "supplies the monotone fit [30], [31]; constrained MDPs and shaping [12], [14], [24] encode requirements in the "
         "objective, and our results delimit rather than contradict them. Twins of orbital mechanics and link budgets "
         "are used mainly for offline validation [16]–[18]; we use the twin as ground truth against which mined "
         "constraints are stress-tested.",
         "related work trimmed")

# 2. Stage 1 paragraph: the new cluster sentence made it long; compress the mechanics
sub_para("Every attempt yields (context, a, outcome)",
         "Every attempt yields (context, a, outcome) with outcome ∈ {ok, late_handover, no_route, window_exceeded, "
         "below_elevation}. For region z, a successful attempt is an exact observation of T_z (the twin records the "
         "realised setup time) and a late handover at advance a is a right-censored observation of T_z at a under the "
         "non-informative-censoring assumption stated below. We estimate F_z by Kaplan–Meier over the attempt stream, "
         "stratified by region, and read off q_z(ε) at ε = 5%. The estimator plays two roles: diagnostic (it quantifies "
         "the naive estimator's truncation bias, 6.45 s vs 4.08 s median) and sanity bound (a probe result inconsistent "
         "with the KM curve is rejected).",
         "stage-1 trimmed")

t = re.sub(r"\n{3,}", "\n\n", t)
p.write_text(t, encoding="utf-8")
print("edits:", done)
print("words:", len(re.findall(r"[A-Za-z0-9']+", t)))
