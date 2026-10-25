"""R7 (v9) EN: drop the revision note, compress the abstract, and clean the residual names."""
from __future__ import annotations

import re
from pathlib import Path

P = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本" / "paper_en.md"
t = P.read_text(encoding="utf-8")
done = []


def rep(old: str, new: str, label: str) -> None:
    global t
    n = t.count(old)
    if n != 1:
        raise SystemExit(f"[{label}] expected 1, found {n}")
    t = t.replace(old, new, 1)
    done.append(label)


# ---- 1. remove the revision note from the front matter -------------------
m = re.search(r"\*\*Manuscript v8[^\n]*\*\*\n\n?", t)
if not m:
    raise SystemExit("revision banner not found")
t = t[: m.start()] + t[m.end():]
done.append("banner-removed")

# ---- 2. compress the abstract to <=250 words ----------------------------
i = t.find("## Abstract")
j = t.find("**Index Terms", i)
if i < 0 or j < 0:
    raise SystemExit("abstract bounds not found")
ABSTRACT = """## Abstract

Handover reliability in low Earth orbit constellations is usually treated as a reinforcement-learning problem, and recent systems report large gains from coupling RL with large language models. We began with a faithful reproduction of one such system and ended with an audit of what its gains consist of. On a 350-satellite twin, a single timing constraint explains nearly all of the reported improvement: applied to frozen policy weights and scored on identical episodes, a lower bound on the handover lead raises polar handover success from 67.5 ± 13.2% to 92.4 ± 0.3% for the mined bound and 93.3 ± 0.3% at the deployed bound, while without it ten checkpoints scatter across 49.8–90.0% and the two policy families are indistinguishable. The cause is structural: the passive log covers the informative band of advance space thinly—705 of 8,682 attempts (8.1%) fall in the 14–16 s band, against 37.7% in the modal bucket—so within any budget a field study can afford the bound is effectively unidentifiable: an effective-support failure under a sample budget, not an information-theoretic impossibility. We therefore move such knowledge out of the reward and into the decision layer. The language model proposes only a constraint's predicate, never its magnitude; the magnitude is fixed by probing the deployed policy, a cost-asymmetric margin absorbs the residual plateau, and a counterfactual audit gate admits candidates only after replay. We state the boundaries plainly: a hand-tuned constant matches the system at nominal physics but loses 6–7 pp under 3.2 s of acquisition drift; the five-seed gate study is descriptive rather than significant; and the lockbox freezes the selection instead of re-selecting it.

"""
t = t[:i] + ABSTRACT + t[j:]
done.append("abstract")

# ---- 3. intro: the "inputs never go" phrasing ---------------------------
old = "so the region of advance space where outcomes are informative—just below the requirement—is covered several times more thinly than the modal operating region"
if old in t:
    t = t.replace(
        old,
        "so the region of advance space where outcomes are informative—just below the requirement—is covered several times more thinly than the modal operating region (8.1% of attempts against 37.7%)",
        1,
    )
    done.append("intro-thin")

# ---- 4. band clarification for the 9.5-11.3 s figure --------------------
rep(
    "the mean lead is 9.5–11.3 s against a 16 s need.",
    "the mean lead is 9.5–11.3 s against a 16 s need (that figure is the |lat| ≥ 70° mixed campaign; the passive no-shield log of the baseline, |lat| ≥ 68°, has a mean of 9.09 s and is the one used below).",
    "band-clarify",
)

# ---- 5. one more numeric 'full system' ---------------------------------
rep(
    "this is the constraint the full system uses)",
    "this is the constraint the mined-rule campaign arm executes)",
    "constraint-arm",
)

P.write_text(t, encoding="utf-8")
print("applied:", done)
