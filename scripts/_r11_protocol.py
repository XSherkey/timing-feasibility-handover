"""R12 part 2: protocol labels, seed counts, and the statistics now cited in the tables."""
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
        print(f"  MISS [{label}] {n}: {old[:60]}")
        return
    t = t.replace(old, new, 1)
    done.append(label)


# ---- 1. Section VI-A: Table IX is not archival ---------------------------
rep("The archival numbers of Tables III–IX, XI and XII were produced in an earlier round",
    "The archival numbers of Tables III–VIII, XI and XII were produced in an earlier round", "archival-list")

# ---- 2. seed counts ------------------------------------------------------
rep("holds the ceiling across five seeds and three regimes (Fig. 3)",
    "holds the ceiling across ten policy seeds and four regimes (Fig. 3)", "seeds-1")
rep("On the second-round drift ladder of Fig. 8 (five seeds per point, identical episodes across arms)",
    "On the drift ladder of Fig. 8 (ten policy seeds per point, identical episodes across arms)", "seeds-2")

# ---- 3. protocol label in the captions ----------------------------------
for tag, label in (
    ("**Table III. Failure attribution", "**Protocol: archival (evaluation-window calibration).** "),
    ("**Table IV. Penalty dose-response", "**Protocol: archival.** "),
    ("**Table V. Drift response", "**Protocol: archival.** "),
    ("**Table VI. Cross-intent transfer", "**Protocol: archival.** "),
    ("**Table VII. Alternative physics", "**Protocol: archival.** "),
    ("**Table VIII. Drift ladder", "**Protocol: archival.** "),
    ("**Table IX. Contribution isolation", "**Protocol: validation-only.** "),
):
    i = t.find(tag)
    if i < 0:
        print("  caption not found:", tag[:30])
        continue
    # insert the protocol sentence right after the bold title
    close = t.find("**", i + 2)
    # the title ends at the first ".**"
    end = t.find(".**", i + 2)
    if end < 0:
        end = close
    insert_at = end + 3
    t = t[:insert_at] + " " + label + t[insert_at:]
    done.append(tag[:20])

# Table X caption: say the first column is archival explicitly
rep("**Table X. Full three-way lockbox (polar HSR, |lat| ≥ 70°, campaign policies, traffic seed 0, "
    "n = 10 policy seeds per instance).**",
    "**Table X. Lockbox vs evaluation window (polar HSR, |lat| ≥ 70°, campaign policies, traffic seed 0, "
    "n = 10 policy seeds per instance). The first data column is the archival evaluation-window "
    "instantiation; the last three are the three-way lockbox instances. They are not the same protocol, and "
    "the table marks each column accordingly.**", "tableX-caption")

p.write_text(t, encoding="utf-8")
print("applied:", done)
