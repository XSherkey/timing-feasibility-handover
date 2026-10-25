"""R10 part 3: the kappa sentence, the schema note, and the Introduction repositioning."""
from __future__ import annotations

from pathlib import Path

D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"
p = D / "paper_en.md"
t = p.read_text(encoding="utf-8")
done = []


def rep(old, new, label):
    global t
    n = t.count(old)
    if n != 1:
        print(f"  MISS [{label}] {n}: {old[:70]}")
        return
    t = t.replace(old, new, 1)
    done.append(label)


# ---- 1. kappa sentence ---------------------------------------------------
rep("the two annotators agree on only four of the five\nitems where they differ",
    "the two annotators disagree on 4 of the 20 proposals (16/20 agreement), and that disagreement "
    "concentrates exactly on the rules whose scope is arguable—a low κ here is evidence *against* deploying "
    "a model-proposed rule without review, not evidence for the model", "kappa")

# ---- 2. schema note ------------------------------------------------------
rep("atoms       : list of {\"field\": ..., \"cmp\": one of \"lt\",\"le\",\"gt\",\"ge\",\"eq\",\"ne\",\n"
    "               \"value\": number}   # <, <=, >, >=, ==, != spelled out so the schema\n"
    "                                 # survives copy-paste through any PDF pipeline",
    "atoms       : list of {\"field\": ..., \"cmp\": one of \"lt\",\"le\",\"gt\",\"ge\",\"eq\",\"ne\",\n"
    "               \"value\": number}   # illustrative, not literal JSON: comments are\n"
    "                                 # stripped and the operator names are spelled out.\n"
    "                                 # The raw model outputs quoted below are valid JSON.",
    "schema-note")

# ---- 3. repositioning: the opening of the Introduction -------------------
i = t.find("## I. Introduction")
if i < 0:
    raise SystemExit("Introduction not found")
j = t.find("\n\n", t.find("\n\n", i) + 2)  # end of the first body paragraph
first_para_start = t.find("\n\n", i) + 2
FIRST = ("Low-earth-orbit constellations hand over several times an hour, and a handover that starts too "
         "late is a dropped call that no amount of target selection can recover. The literature treats this "
         "as a reinforcement-learning problem and reports large gains from coupling RL with a large language "
         "model. We rebuilt one such system, reproduced its numbers, and asked a narrower question: *what "
         "part of the gain is the controller, and what part is a constraint the controller was never asked "
         "to learn?*\n\n"
         "The answer shapes the paper. **We do not claim a stronger controller, a better learner, or a "
         "performance-optimal policy.** Under one protocol and ten independent training runs, the learned "
         "component is worth about 0.7 pp; a single timing constraint, applied at decision time, is worth "
         "23.4 of the 24.1 pp gap between a reward-only baseline and the deployed system. The contribution we "
         "do claim is an *audit and calibration protocol*—one that shows where the performance actually "
         "comes from, measures the constraint on the deployed policy, keeps a wrong candidate off the "
         "network, and survives a change of physics—together with the negative results that make the "
         "protocol necessary.")
t = t[:first_para_start] + FIRST + t[j:]
done.append("intro-opening")

p.write_text(t, encoding="utf-8")
print("applied:", done)
