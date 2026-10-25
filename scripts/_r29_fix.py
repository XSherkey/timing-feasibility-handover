"""R29: the four blocking items of review 22."""
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


# ---- 1. bank paragraph: composition and the neutral definition -------------
rep("seven are harmful (−8.1 to −27.6 pp: four caps below the requirement, two visibility-preference rules and "
    "one unscoped variant), three are neutral (|Δ| ≤ 1.0 pp: an 8 s polar lead, a 20 s polar cap and an unscoped "
    "routing rule) and sixteen are good (+6.2 to +21.6 pp).",
    "seven are harmful (−8.1 to −27.6 pp: five caps set below the requirement and two visibility-preference rules), "
    "three are neutral (0 ≤ Δ < 5 pp: an 8 s polar lead, a 20 s polar cap and an unscoped routing rule) and sixteen "
    "are good (+6.2 to +21.6 pp).", "bank composition + neutral def")

# ---- 2. statistics: deterministic arms get their own rule ------------------
rep("Every comparison in this paper is paired on the policy seed: the same ten training seeds appear in\nevery arm, "
    "and every arm is scored on the same episodes.",
    "Every comparison *between learned policies* is paired on the policy seed: the same ten training seeds appear in "
    "every arm, and every arm is scored on the same episodes. A deterministic controller—the tuned constant, the "
    "re-probed constant, A8—carries no training variance, so a paired test over seeds would manufacture ten "
    "observations from one; those arms are reported as single values, their differences from a learned arm are read "
    "against that arm's seed distribution rather than tested as if both varied, and where an environment-level "
    "replicate exists it is used (Section VI-A, five traffic seeds).", "statistics split")

# ---- 3. protocol labels for IX / IXb / IXc ---------------------------------
rep("Tables III, VI, IX, IXb and IXc report archival numbers, with the evaluation row of Table X;",
    "Tables III and VI report archival numbers, and so does the evaluation row of Table X; Table IX reports "
    "validation-only selections with the lockbox columns scored three-way, and Tables IXb and IXc select on the "
    "validation window and score once on the test window;", "protocol labels")

# ---- 4. equation references after the renumbering --------------------------
rep("The expectation in (2) is over the joint distribution", "The expectation in (3) is over the joint distribution",
    "eq ref (2)->(3) a")
rep("absent that assumption, (2) is the exact expression", "absent that assumption, (3) is the exact expression",
    "eq ref (2)->(3) b")
for old, new in (
    ("(ii) *What (3) does not give*", "(ii) *What (4) does not give*"),
    ("Even with (3), HSR", "Even with (4), HSR"),
    ("not a consequence of (3). In the notation of (3), D", "not a consequence of (4). In the notation of (4), D"),
    ("at measurement time; (3) is exact only when", "at measurement time; (4) is exact only when"),
):
    if t.count(old) == 1:
        t = t.replace(old, new, 1)
        done.append(f"eq ref {old[:24]}")

# ---- 5. feeder capacity: two different parameters --------------------------
rep("`t_slot = 1.8 s` and `s` feeder slots (three in the nominal configuration, one in the capacity-stress arm) "
    "against the `P` satellites visible from the target's best gateway,",
    "`t_slot = 1.8 s` and `s = 3` gateway tracking slots—the number of satellites a gateway can hold in its "
    "acquisition queue, which is a property of the acquisition model, not of the feeder capacity—against the `P` "
    "satellites visible from the target's best gateway,", "feeder acquisition slots")
rep("With feeder capacity reduced to three slots per gateway the same shield lifts the arms only to 69.5–70.0%",
    "With the twin's feeder capacity cut from its nominal ten simultaneous links to three, the same shield lifts the "
    "arms only to 69.5–70.0%", "feeder capacity stress wording")

# ---- 6. deployment cross-reference ----------------------------------------
rep("Interfaces and failure paths are specified in Section VI-K.",
    "Interfaces and failure paths are specified in Section VI-M.", "VI-K -> VI-M")

# ---- 7. closed loop: narrow the closing sentence ---------------------------
i = t.find("which is why the paper reports that contrast")
j = t.find("the value of the loop is the auditable decision, not the number", 0)
if j > 0:
    k = t.find("\n\n", j)
    t = t[:j] + ("the loop adds probe cost and ends below both the fixed threshold and the EWMA baseline; we therefore "
                 "claim no online recovery, and record the protocol as unvalidated for autonomous use.") + t[k:]
    done.append("closed-loop closing narrowed")

t = re.sub(r"\n{3,}", "\n\n", t)
p.write_text(t, encoding="utf-8")
print("edits:", done)
