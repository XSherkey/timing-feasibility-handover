"""R27: repair the v80 damage - restore contribution isolation, renumber, and stop the text over-claiming."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
D = ROOT / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"
HIST = D / "_history"
p = D / "paper_en.md"
t = p.read_text(encoding="utf-8")
done = []

# ---------------------------------------------------------------- 1. restore VI-H
src = sorted(HIST.glob("paper_en_v79_*.md"))[-1]
old = src.read_text(encoding="utf-8")
i = old.find("### H. Contribution isolation")
j = old.find("### I. Full three-way lockbox")
block = old[i:j].strip()
print("restored block chars:", len(block), "| has Table IX:", "**Table IX." in block)
anchor = "### H. Two bounds, one interval"
k = t.find(anchor)
if k < 0:
    raise SystemExit("two-bounds heading not found")
t = t[:k] + block + "\n\n" + t[k:]
done.append("restored VI-H isolation")

# ---------------------------------------------------------------- 2. renumber
RENAME = [
    ("### H. Two bounds, one interval", "### I. Two bounds, one interval"),
    ("### I. Closed loop: detect, probe, admit or roll back", "### J. Closed loop: detect, probe, admit or roll back"),
    ("### I. Full three-way lockbox", "### K. Full three-way lockbox"),
    ("### J. Statistical protocol", "### L. Statistical protocol"),
    ("### K. Deployment and governance", "### M. Deployment and governance"),
    ("### L. What the language model actually proposes", "### N. What the language model actually proposes"),
    ("### M. Limitations", "### O. Limitations"),
]
for a, b in RENAME:
    if t.count(a) == 1:
        t = t.replace(a, b, 1)
done.append("renumbered")

# ---------------------------------------------------------------- 3. fix cross references
REF = [
    ("Section VI-J summarises the decomposition", "Section VI-L summarises the decomposition"),
    ("the lockbox columns of Table IX", "the lockbox columns of Table IX"),
    ("Section VI-I states which table belongs", "Section VI-K states which table belongs"),
    ("reported in Section VI-K", "reported in Section VI-M"),
]
for a, b in REF:
    n = t.count(a)
    if n == 1 and a != b:
        t = t.replace(a, b, 1)
        done.append(f"ref {a[:28]}")

# ---------------------------------------------------------------- 4. abstract: honest closed loop
rep_old = ("The same three stages learn the *upper* bound as well: a visibility-relative cap removes three quarters of "
           "the window violations that the lower bound introduces, at unchanged success, because the two bounds act on "
           "one interval. A closed loop that detects a 2 s drift, probes in service and gates the result recovers the "
           "pre-drift level with a one-chunk detection delay; a simple EWMA quantile matches it here, which we report "
           "rather than hide.")
rep_new = ("The same three stages also learn an *upper* bound: a visibility-relative cap cuts the window violations the "
           "lower bound introduces by three quarters but converts them one-for-one into late failures, so the success "
           "rate is unchanged—the two bounds act on one interval, and its length, not either endpoint, sets the score. "
           "A closed loop detects a 2 s drift within one chunk and probes in service, but its audit gate rejects the "
           "candidate update, so the loop ends below the fixed threshold (89.7% against 90.6%); a simple EWMA quantile "
           "recovers to 93.6%. We report that as a failure of replay-based admission under drift, not as a success.")
print("abstract old present:", t.count(rep_old))
if t.count(rep_old) == 1:
    t = t.replace(rep_old, rep_new, 1)
    done.append("abstract honest")

# ---------------------------------------------------------------- 5. demote the second-constraint claim
claim_old = ("The second family is thus learnable, calibratable and auditable with the same pipeline, and it buys a cleaner "
             "failure profile rather than a higher score—which is the honest reading of a feasibility interval with two ends.")
claim_new = ("What the second family establishes is therefore narrower than a management benefit: the *form* transfers (one "
             "rule language, one probe, one gate, one audit), the guard is not identifiable from the success curve, and the "
             "cap has no net effect on success. Whether a 3.4% + 1.1% profile is better than 0.0% + 4.5% depends on what a "
             "late handover and a window violation cost in signalling, outage time and grade of service—quantities this "
             "paper does not measure, so we do not claim the exchange is an improvement.")
print("claim present:", t.count(claim_old))
if t.count(claim_old) == 1:
    t = t.replace(claim_old, claim_new, 1)
    done.append("second-constraint demoted")

# ---------------------------------------------------------------- 6. the natural-candidate paragraph
i = t.find("The six natural candidates, with their held-out deltas and verdicts:")
if i > 0:
    j = t.find("\n\n", t.find("committed all six, four of them harmful.", i))
    bank = ("The bank is 26 candidates, each scored by its held-out delta on the evaluation window: seven are harmful "
            "(−8.1 to −27.6 pp: four caps below the requirement, two visibility-preference rules and one unscoped "
            "variant), three are neutral (|Δ| ≤ 1.0 pp: an 8 s polar lead, a 20 s polar cap and an unscoped routing "
            "rule) and sixteen are good (+6.2 to +21.6 pp). The gate admits all sixteen good candidates and rejects all "
            "seven harmful ones; the three neutral candidates fall below the 5 pp admission bar by construction, so "
            "they are excluded from the false-rejection count rather than counted as misses.")
    t = t[:i] + bank + t[j:]
    done.append("bank paragraph rewritten")

# ---------------------------------------------------------------- 7. deterministic arms note
cap_old = "The two constant-controller rows are evaluated on the same n = 10 policy seeds but do not depend on the policy, so their sd is 0.00;"
cap_new = ("The two constant-controller rows do not depend on the policy: they are re-evaluated on the same episodes but carry "
           "no policy variance, so they are reported as single values and are not entered into any paired test over seeds;")
print("table V caption:", t.count(cap_old))
if t.count(cap_old) == 1:
    t = t.replace(cap_old, cap_new, 1)
    done.append("Table V paired-test note")

t = re.sub(r"\n{3,}", "\n\n", t)
p.write_text(t, encoding="utf-8")
print("edits:", done)
