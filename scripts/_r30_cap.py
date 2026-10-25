import re
from pathlib import Path

p = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本" / "supplementary" / "supp_en.md"
s = p.read_text(encoding="utf-8")

i = s.find("**Table D2.")
j = s.find("\n\n", i)
cap = s[i:j]
print("old caption:\n", cap[:400], "\n---")

NEW_CAP = ("**Table D2. The full 26-candidate gate bank.** The gate decides on the validation gain only (admission "
           "requires > 5 pp); the evaluation effect is measured afterwards, on the window the gate never sees, and is "
           "what assigns the post-hoc label — harmful if that effect is negative, neutral if 0 ≤ Δ < 5 pp, good if "
           "Δ ≥ 5 pp. Because the label comes from a column the gate never reads, the confusion matrix is an audit and "
           "not a tautology. Two proposals (G04 at 28 s, G19 at 30 s) exceed the 26 s action grid: their magnitude is "
           "projected onto the grid before evaluation, so the gate reviews the projected candidate, which is why those "
           "two rows carry identical gains and are not independent evidence.")

body = s[j:]
body = body.replace("| id | executed rule | validation gain (pp) | admission | evaluation effect (pp) | post-hoc label |",
                    "| id | executed rule | validation gain (pp) | gate | evaluation effect (pp) | post-hoc label |", 1)
s = s[:i] + NEW_CAP + body
p.write_text(s, encoding="utf-8")
print("caption replaced, header renamed")
print("stray single asterisks in caption:", NEW_CAP.count("*") - 4)
