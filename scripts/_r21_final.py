"""R21 part 7: final ~900-word compression across Sections III, V, VI-B, VI-D and VII."""
from __future__ import annotations

import re
from pathlib import Path

D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"
p = D / "paper_en.md"
t = p.read_text(encoding="utf-8")
w0 = len(re.findall(r"[A-Za-z0-9']+", t))
edits = []


def sub(old: str, new: str, label: str) -> None:
    global t
    n = t.count(old)
    if n != 1:
        print("  MISS", label, n)
        return
    t = t.replace(old, new, 1)
    edits.append(label)


# --- Section III: drop the redundant enumeration of link-budget terms -----
i = t.find("**Constellation and links.**")
j = t.find("\n\n", i)
if i > 0 and j > i:
    sub(t[i:j], ("**Constellation and links.** The twin models a 350-satellite Walker constellation in three shells—a "
                 "polar shell of 200 satellites (10 planes × 20, 89.5°, 700 km), a mid-latitude shell of 120 "
                 "(6 × 20, 53°, 550 km) and an equatorial shell of 30 (2 × 15, 5°, 600 km)—propagated with SGP4 over "
                 "a 12 h horizon at 10 s resolution, with the same pipeline accepting real TLE archives (Iridium "
                 "NEXT, OneWeb, Galileo, GPS). Link budgets model free-space loss with elevation-dependent "
                 "atmospheric attenuation at 20 GHz over 250 MHz channels, Doppler shift, inter-satellite links "
                 "(range ≤ 5200 km), eclipse periods and gateway feeder capacity; a polar gateway sees an order of "
                 "magnitude more candidates than a mid-latitude one, and a feeder cap of ten simultaneous links "
                 "makes feeder access scarce exactly above the polar seam at 70°, where inter-plane handovers carry "
                 "a seam penalty. Sites experience Poisson session arrivals with video and emergency traffic mixes; "
                 "polar sites see visibility windows of several minutes."), "III links paragraph")

# --- Section V: compress the four-stage description -----------------------
i = t.find("**Stage 2—propose, with the model as a hypothesis generator.**")
j = t.find("\n\n", i)
if i > 0 and j > i:
    sub(t[i:j], ("**Stage 2: propose, with the model as a hypothesis generator.** The model is given the failure "
                 "narratives and a constrained predicate grammar, and asked for one rule as JSON (Appendix E). It is "
                 "asked only for the predicate: the magnitude is a measurement this section is about to make, and "
                 "letting the model propose both is what made the earlier version of this pipeline uncalibrated."),
        "V stage-2 paragraph")

# --- Section VI-B: drop the restatement of the protocol -------------------
i = t.find("The decomposition is arithmetic within a single protocol.")
j = t.find("\n\n", i)
if i > 0 and j > i:
    sub(t[i:j], ("The decomposition is arithmetic within a single protocol: the 24.1 pp gap from the reward-only "
                 "baseline to the mined-rule arm is recovered by applying the constraint to the baseline's *own* "
                 "weights, leaving 0.7 pp for everything the full-system training adds beyond a shielded baseline. "
                 "The constraint, not the learner, carries the gap."), "VI-B decomposition paragraph")

# --- Section VI-D: compress the boundary discussion -----------------------
i = t.find("The tuned constant is the strongest non-learned competitor")
j = t.find("\n\n", i)
if i > 0 and j > i and len(t[i:j]) > 800:
    sub(t[i:j], ("The tuned constant is the strongest non-learned competitor, and its failure boundary is sharp: it "
                 "matches the mined rule at nominal physics (93.3 vs 92.4) and loses 7.4–9.8 pp once the "
                 "requirement moves, because a fixed 18 s lead cannot follow a requirement that has moved by 2 s "
                 "and consumed the 2 s margin. Re-probing under the perturbed physics holds the ceiling across all "
                 "ten seeds and four regimes (Fig. 3), which is the practical content of the calibration claim: the "
                 "constant encodes a measurement made once, and the probe re-makes it."), "VI-D boundary paragraph")

# --- Conclusion: shorter ---------------------------------------------------
i = t.find("## VII. Conclusion")
j = len(t)
if i > 0:
    tail = t[i:]
    k = tail.find("\n\n## References")
    body = tail[:k] if k > 0 else tail
    sub(body, """## VII. Conclusion

Handover reliability in LEO constellations is usually framed as a learning problem. We reproduced one
system built on that framing and found that a single timing constraint, mined from censored failure logs and
injected at decision time, accounts for nearly all of its reported gain: 23.4 of the 24.1 pp, with the
learned component worth under a point. The reason the constraint is missed is structural rather than
algorithmic—trained policies concentrate below the requirement, so the passive log barely samples the region
that would inform it, and a reward penalty must distort the objective to reach it. The method that follows is
deliberately unglamorous: censor-aware fitting, a probe on the deployed policy, a cost-asymmetric margin, and
an audit gate that replays candidates before they act. It carries no guarantee that the mined rule is the
right rule; it carries an auditable procedure for finding out.
""", "conclusion")
t = t + ""

p.write_text(re.sub(r"\n{3,}", "\n\n", t), encoding="utf-8")
w1 = len(re.findall(r"[A-Za-z0-9']+", t))
print("edits:", edits)
print("words:", w0, "->", w1, "(-%d)" % (w0 - w1))
