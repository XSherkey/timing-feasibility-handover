"""R7 part 7: the two-protocol statement, the gate reference, and the remaining caption/text fixes."""
from __future__ import annotations

import json
from pathlib import Path

D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"
ROOT = Path(__file__).resolve().parents[2] / "almond-repro"
h = json.loads((ROOT / "results" / "routeA_r3" / "headline_consistent" / "summary.json").read_text(encoding="utf-8"))
A = h["arms"]

p = D / "paper_en.md"
t = p.read_text(encoding="utf-8")
done = []


def rep(old, new, label):
    global t
    n = t.count(old)
    if n != 1:
        print(f"  MISS [{label}] {n}")
        return
    t = t.replace(old, new, 1)
    done.append(label)


# 1. Section V-C: the probe runs on both windows
rep("In the present artefacts the probe runs on the held-out evaluation window (disjoint from training and "
    "from discovery); the calibration/evaluation separation question is discusse",
    "In the present artefacts the probe is run on both held-out windows and returns the same threshold on "
    "both—τ∗ = 16 s on the validation window (65–75%) and 16 s on the evaluation window (82–95%), both "
    "disjoint from training and from discovery. The *archival* numbers (Tables II–IV, Fig. 5) use the "
    "evaluation-window probe; the *three-way* numbers (Table IX, lockbox rows) use the validation-only probe, "
    "and Section VI-A states which table belongs to which protocol. The calibration/evaluation separation "
    "question is discusse", "viC-probe")

# 2. Section VI-A: name the two protocols explicitly
i = t.find("### A. Protocol")
j = t.find("\n\n", t.find("the precise version is given in Section VI-A", i))
if i < 0:
    raise SystemExit("VI-A not found")
anchor = t.find("the precise version is given in Section VI-A", i)
para_end = t.find("\n\n", anchor)
TWO = ("\n\n**Two protocols, one data set.** This paper reports under two calibration protocols on the same "
       "ten campaign policies and the same episodes, and every table declares which one it uses. The "
       "*archival protocol* (Tables II, III, IV, V, VII, VIII, X and Fig. 2–5) calibrates the threshold probe, "
       "the gate replay and the penalty coefficient on the evaluation window (82–95%) and then reports on that "
       "same window; it is an honest re-calibration structure, not a lockbox. The *three-way protocol* "
       "(Table IX) moves every selection—probe, gate replay, λ, margin—onto the validation window (65–75%) and "
       "never touches the lockbox instances, which are the evaluation window instantiated at three shifted "
       "twin epochs. Because both windows return the same threshold (16 s) and the same λ (8), the two "
       "protocols differ in what they *permit*, not in what they *select*; the archival numbers are therefore "
       "directly comparable to the lockbox numbers, and Table IX reports both.")
t = t[:para_end] + TWO + t[para_end:]
done.append("viA-two-protocols")

# 3. Section VI-E: point at the 26-candidate table
rep("The gate is not decorative. In a controlled study we handed it six candidates an LLM could plausibly "
    "propose, with the following held-out deltas and verdicts:",
    "The gate is not decorative. In a controlled study we handed it six candidates an LLM could plausibly "
    "propose, with the following held-out deltas and verdicts (the full bank of 26 candidates is summarized in "
    "Table XI):", "viE-gate-ref")

# 4. Table IV caption: which rows are n = 10 and which n = 5
rep("**Table IV. Drift response (polar HSR, mean ± sd, n = 10 policy seeds, traffic seed 0, polar band |lat| ≥ 70°; "
    "the two constant-controller rows are policy-independent and therefore have sd 0.00).**",
    "**Table IV. Drift response (polar HSR, mean ± sd, traffic seed 0, polar band |lat| ≥ 70°). The four "
    "shielded and constant rows are n = 10 policy seeds; the two constant rows are policy-independent, so their "
    "sd is 0.00. The last row is the probe study, which uses five policy seeds and is marked as such.**",
    "table4-caption")

# 5. Section VI-L: preliminary status
rep("**Table X. Annotation of the twenty proposals.",
    "These twenty proposals are a qualitative first measurement, not a statistical claim: twenty narratives "
    "from ten training windows, two annotators, and a rubric coarse enough that κ is best read as a "
    "disagreement locator rather than as a quality score.\n\n**Table X. Annotation of the twenty proposals.",
    "viL-preliminary")

p.write_text(t, encoding="utf-8")
print("applied:", done)
