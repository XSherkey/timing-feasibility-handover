import re
from pathlib import Path

p = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本" / "supplementary" / "supp_en.md"
s = p.read_text(encoding="utf-8")
i = s.find("**Table H2.")
j = s.find("\n\n", i)
cap = s[i:j]
print("caption:\n", cap[:1200])

pat = re.compile(r"Paired over the ten seeds[\s\S]*?from \+2 s on\)", re.S)
NEW = ("The re-probed constant is the same controller with its lead re-selected, so the two rows differ by a "
       "deterministic amount, reported descriptively (+0.00, +0.81, +7.22 and +9.64 pp at 0/+2/+3.2/+4.4 s) and "
       "without a paired test over policy seeds because no policy is involved")
s2, n = pat.subn(NEW, s, count=1)
print("replaced:", n)
p.write_text(s2, encoding="utf-8")
