import re
from pathlib import Path

p = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本" / "supplementary" / "supp_en.md"
s = p.read_text(encoding="utf-8")
i = s.find("**Table H2.")
j = s.find("\n\n", i)
cap = s[i:j]
k = cap.find("Paired over the ten seeds")
print("found at", k)
if k > 0:
    NEW = ("The re-probed constant is the same controller with its lead re-selected, so the two rows differ by a "
           "deterministic amount, reported descriptively (+0.00, +0.81, +7.22 and +9.64 pp at 0/+2/+3.2/+4.4 s); no "
           "paired test over policy seeds is applied, because no policy is involved.")
    cap2 = cap[:k] + NEW
    s = s[:i] + cap2 + s[j:]
    p.write_text(s, encoding="utf-8")
    print("rewritten")
