"""R27 part 2: demote the second-constraint conclusion, soften 'survives a change of physics'."""
from __future__ import annotations

import re
from pathlib import Path

p = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本" / "paper_en.md"
t = p.read_text(encoding="utf-8")
done = []

# 1. the second-family conclusion (whitespace tolerant)
pat = re.compile(r"The second family\s+is thus learnable, calibratable and auditable with the same pipeline, and it buys a cleaner failure profile\s+"
                 r"rather than a higher score[^.]*\.", re.S)
NEW = ("What the second family establishes is therefore narrower than a management benefit: the *form* transfers—one rule "
       "language, one probe, one gate, one audit—the guard is not identifiable from the success curve, and the cap has no "
       "net effect on success. Whether a 3.4% + 1.1% profile is better than a 0.0% + 4.5% one depends on what a late "
       "handover and a window violation cost in signalling, outage time and grade of service, which this paper does not "
       "measure; we therefore do not claim the exchange as an improvement.")
t, n = pat.subn(NEW, t, count=1)
print("second-family claim replaced:", n)

# 2. 'survives a change of physics' must not survive in the introduction
for old, new in [
    ("and survives a change of physics", "and can be re-calibrated when the physics changes"),
    ("survives a change of physics", "can be re-calibrated when the physics changes"),
]:
    c = t.count(old)
    if c:
        t = t.replace(old, new)
        done.append(f"{old!r} x{c}")

t = re.sub(r"\n{3,}", "\n\n", t)
p.write_text(t, encoding="utf-8")
print("edits:", done)
print("'survives a change' left:", t.count("survives a change of physics"))
print("'recovers the pre-drift':", t.count("recovers the pre-drift"))
