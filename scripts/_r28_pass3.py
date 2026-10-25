"""R28 pass 3: two contradictory sentences - the limitations count and the H2 paired-test claim."""
from __future__ import annotations

import re
from pathlib import Path

D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"
main = D / "paper_en.md"
supp_path = D / "supplementary" / "supp_en.md"
t = main.read_text(encoding="utf-8")
s = supp_path.read_text(encoding="utf-8")

t, n1 = re.subn(r"all three\s*\nbound how far", "all four\nbound how far", t)
print("limitations closing fixed:", n1)

old = ("Paired over the ten seeds, the re-probed constant beats the fixed one by 0.81 pp at +2 s, 7.22 pp at +3.2 s "
       "and 9.64 pp at +4.4 s, and is identical at nominal physics (bootstrap 95% CI of the difference excludes zero "
       "from +2 s on)")
new = ("The re-probed constant is the same controller with its lead re-selected, so the two rows differ by a "
       "deterministic amount and we report it descriptively—+0.00, +0.81, +7.22 and +9.64 pp at 0/+2/+3.2/+4.4 s—"
       "without a paired test over policy seeds, because no policy is involved")
print("H2 claim present:", s.count(old))
s = s.replace(old, new, 1)

t = re.sub(r"\n{3,}", "\n\n", t)
s = re.sub(r"\n{3,}", "\n\n", s)
main.write_text(t, encoding="utf-8")
supp_path.write_text(s, encoding="utf-8")
print("all four bound:", t.count("all four\nbound how far"))
