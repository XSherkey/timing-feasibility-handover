"""R21: trim to 16 pages. Every cut is verified: table captions and section headings are counted before/after."""
from __future__ import annotations

import re
from pathlib import Path

D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"
p = D / "paper_en.md"
supp_path = D / "supplementary" / "supp_en.md"

t = p.read_text(encoding="utf-8")
supp = supp_path.read_text(encoding="utf-8")

caps_before = len(re.findall(r"^\*\*Table ", t, flags=re.M))
heads_before = len(re.findall(r"^### ", t, flags=re.M))
print("before: tables", caps_before, "subsections", heads_before)
edits = []


def sub1(old: str, new: str, label: str) -> None:
    global t
    n = t.count(old)
    if n != 1:
        print("  MISS", label, n)
        return
    t = t.replace(old, new, 1)
    edits.append(label)


# ---- 1. Section VI-I: drop the protocol re-statement ---------------------
i = t.find("The earlier protocol let three choices touch the evaluation window")
j = t.find("Re-scoring the four archived coefficients", i)
if i > 0 and j > i:
    t = t[:i] + ("The three-way protocol of Section VI-A is instantiated here: discovery on 0–60%, calibration on "
                 "65–75%, and a lockbox at 82–95% re-instantiated three times by shifting the twin epoch by +7, +14 "
                 "and −2 days. No selection step touches the lockbox. ") + t[j:]
    edits.append("VI-I protocol restatement cut")

# ---- 2. Section VI-G: compress the readings ------------------------------
i = t.find("Three readings. First, the oracle is drift-immune by construction")
j = t.find("\n\n", t.find("a distinction no other arm in this paper can make.", i))
if i > 0 and j > i:
    NEW = ("Three readings. The oracle is drift-immune by construction (93.36 at every grid point, sd 0.05) "
           "because it reads each attempt's realised requirement; the gap between the fixed threshold and the "
           "oracle opens only under drift (0.00, 0.94, 7.35, 9.89 pp at δ = 0/+2/+3.2/+4.4 s), which is the "
           "measured price of a fixed threshold and exactly what per-regime re-probing closes (Section VI-D); and "
           "at nominal physics none of the remaining ≈6.6 pp is estimation error—it is target, window and routing, "
           "so only a stronger controller could close it, and Sections VI-A and VI-B measure how little the current "
           "ones differ. The sharpest negative result sits beside them: the reward-penalty arm starts +6.6 pp above "
           "the no-knowledge policies and ends 3.1 pp below them once the requirement moves (+6.6, −2.6, −3.2, "
           "−3.1 pp), so a penalty trained on the nominal requirement is worse than no knowledge as soon as the "
           "requirement moves. The oracle is an upper reference, not a deployable controller, but it separates "
           "\"the estimate was wrong\" from \"the constraint was right and the policy around it was not\".")
    t = t[:i] + NEW + t[j:]
    edits.append("VI-G readings compressed")

# ---- 3. move two short paragraphs to the supplement ----------------------
moved = []
for start, end_marker in (
    ("**Probe cost and limits.**", "**Single-intent ablations.**"),
    ("**Single-intent ablations.**", "**Per-attempt oracle shield.**"),
):
    i = t.find(start)
    j = t.find(end_marker, i)
    if i > 0 and j > i:
        moved.append(t[i:j].strip())
        t = t[:i] + t[j:]
if moved:
    supp = supp.rstrip() + "\n\n## Appendix J. Probe cost and single-intent ablations\n\n" + "\n\n".join(moved) + "\n"
    edits.append("probe cost + ablations moved")

# ---- 4. move Table XI to the supplement ----------------------------------
i = t.find("**Table XI.")
if i > 0:
    j = t.find("\n\n", t.find("| good (measured effect", i))
    if j < 0:
        j = t.find("\n\n", t.find("|", t.find("|", i) + 2))
    block = t[i:j]
    t = t[:i] + ("*Gate confusion.* On the 26-candidate bank the gate admits no harmful candidate and rejects no "
                 "good one—0 false accepts, 0 false rejects; the three neutral candidates are rejected by "
                 "construction, so they are excluded from the false-rejection count. The full matrix is Table K1 of "
                 "the supplementary material.\n") + t[j:]
    supp = supp.rstrip() + "\n\n## Appendix K. Gate confusion\n\n" + block.replace(
        "**Table XI.", "**Table K1.") + "\n"
    edits.append("Table XI moved")

t = re.sub(r"\n{3,}", "\n\n", t)
p.write_text(t, encoding="utf-8")
supp_path.write_text(supp, encoding="utf-8")

caps_after = len(re.findall(r"^\*\*Table ", t, flags=re.M))
heads_after = len(re.findall(r"^### ", t, flags=re.M))
print("after: tables", caps_after, "subsections", heads_after)
print("edits:", edits)
print("words:", len(re.findall(r"[A-Za-z0-9']+", t)))
