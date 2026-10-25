"""R28 pass 1: main-text consistency fixes from review 21."""
from __future__ import annotations

import re
from pathlib import Path

D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"
p = D / "paper_en.md"
t = p.read_text(encoding="utf-8")
done = []


def rep(old, new, label):
    global t
    n = t.count(old)
    if n != 1:
        print("  MISS", label, n)
        return
    t = t.replace(old, new, 1)
    done.append(label)


# 1. abstract: correct the drift pairing
rep("while the re-probed threshold holds 93.2% against 86.0% for a tuned constant.",
    "at +2 s the tuned constant still holds 92.4% against 93.2% for the re-probed threshold, and only at +3.2 s "
    "do the two separate (86.0% against 93.2%).", "abstract drift pairing")

# 2. A8 is not probe-calibrated
rep("six provenance variants land within 0.11 pp of the full pipeline and a probe-calibrated constant controller "
    "within 0.03 pp (Section VI-H).",
    "six provenance variants land within 0.11 pp of the full pipeline, and a highest-elevation controller whose lead "
    "is re-selected on the validation window—no probe, no gate—lands within 0.03 pp (Section VI-H).", "A8 wording")

# 3. gate protocol: admission is validation-only
rep("the frozen policy is rolled out with and without the candidate on a validation split, then on a disjoint "
    "evaluation-window split under three traffic multipliers, and the candidate must improve both by at least 5%.",
    "the frozen policy is rolled out with and without the candidate on the validation split, under three traffic "
    "multipliers, and the candidate must improve the replay by at least 5 pp. The evaluation window is not part of "
    "admission: a separate replay there, run after the decision, is what assigns the post-hoc label used to audit "
    "the gate.", "gate protocol unified")

# 4. VI-A: which tables carry archival numbers
rep("Tables III–VIII, XI and XII report archival numbers, with the evaluation row of Table X; the lockbox columns of "
    "Table IX and Table X report three-way numbers.",
    "Tables III, VI, IX, IXb and IXc report archival numbers, with the evaluation row of Table X; the archival drift "
    "and gate tables (H2, K1) and the annotation table (J1) are in the supplementary material; the lockbox columns of "
    "Tables IX and X report three-way numbers.", "VI-A table list")

# 5. statistics section reference
rep("Statistics are paired on the policy seed throughout (Section VI-J)",
    "Statistics are paired on the policy seed for every comparison between learned policies (Section VI-L)",
    "VI-A statistics ref")

# 6. limitations count
rep("Three limits bound the claims.", "Four limits bound the claims.", "limits count")
rep("None of the four affects the ordering claims", "None of the four affects the ordering claims", "limits closing anchor")
if "all three bound how far" in t:
    t = t.replace("all three bound how far", "all four bound how far")
    done.append("limits 'all three' -> 'all four'")

# 7. equations: T_z becomes (1) and the rest shift by one
t = t.replace("+ penalty(seam, plane),                                        (5)", "+ penalty(seam, plane),                                        (1)")
for old, new in (("(4)", "(5)"), ("(3)", "(4)"), ("(2)", "(3)"), ("(1)", "(2)")):
    pass  # handled below by explicit renumbering
# explicit renumbering of the remaining four labels, high to low
for old, new in ((r"\.\s+\(4\)\s*$", "X4X"),):
    pass
lines = t.splitlines()
out = []
for ln in lines:
    s = ln.rstrip()
    if re.search(r"\(\s*4\s*\)\s*$", s) and "penalty(seam" not in s:
        ln = re.sub(r"\(\s*4\s*\)\s*$", "(5)", ln)
    elif re.search(r"\(\s*3\s*\)\s*$", s) and "penalty(seam" not in s:
        ln = re.sub(r"\(\s*3\s*\)\s*$", "(4)", ln)
    elif re.search(r"\(\s*2\s*\)\s*$", s) and "penalty(seam" not in s:
        ln = re.sub(r"\(\s*2\s*\)\s*$", "(3)", ln)
    elif re.search(r"\(\s*1\s*\)\s*$", s) and "penalty(seam" not in s:
        ln = re.sub(r"\(\s*1\s*\)\s*$", "(2)", ln)
    out.append(ln)
t = "\n".join(out)
t = t.replace("Eq. (3) predicts", "Eq. (4) predicts")
t = t.replace("form of (3)", "form of (4)")
t = t.replace("top of (3)", "top of (4)")
t = t.replace("with (3); it is not", "with (4); it is not")
t = t.replace("because the (3)", "because the (4)")
done.append("equation renumbering")

# 8. cite Fig. 9 in the body so it does not land after the references
rep("The pipeline (Fig. 1) has four stages.",
    "The pipeline (Fig. 1) has four stages, and its deployment view—three services over a versioned knowledge graph, "
    "with the shield reading committed constraints at decision time (Fig. 9)—is what the rest of the paper assumes.",
    "Fig. 9 cited early")

# 9. feeder slots wording
rep("`t_slot = 1.8 s` and `s = 3` feeder slots against the `P` satellites visible from the target's best gateway,",
    "`t_slot = 1.8 s` and `s` feeder slots (three in the nominal configuration, reduced to one in the "
    "capacity-stress arm) against the `P` satellites visible from the target's best gateway,", "feeder slots explained")

t = re.sub(r"\n{3,}", "\n\n", t)
p.write_text(t, encoding="utf-8")
print("edits:", done)
print("equation labels:", re.findall(r"\(([1-5])\)\s*$", t, flags=re.M))
