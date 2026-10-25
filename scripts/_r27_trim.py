"""R27 part 5: trim the new sections and park Table XII in the supplement to hold 16 pages."""
from __future__ import annotations

import re
from pathlib import Path

D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"
p = D / "paper_en.md"
supp_path = D / "supplementary" / "supp_en.md"
t = p.read_text(encoding="utf-8")
supp = supp_path.read_text(encoding="utf-8")
done = []

# 1. trim the second-family probe paragraph
i = t.find("Probing `g` over {0, 2, 4, 6, 8, 10} s on the validation window")
j = t.find("\n\n", t.find("sets the success rate.", i))
if i > 0 and j > i:
    NEW = ("Probing `g` over {0, 2, 4, 6, 8, 10} s on the validation window returns a flat curve: 88.9% polar HSR and "
           "6.9% late at every guard, against 88.9% and 5.3% without a cap, while the window class falls from 3.3% to "
           "1.6%. The guard is therefore not identifiable from the success curve; the *interval* is what matters, not "
           "either endpoint.")
    t = t[:i] + NEW + t[j:]
    done.append("probe paragraph trimmed")

# 2. trim the closed-loop closing paragraph
i = t.find("Table IXc gives the four reference points.")
j = t.find("\n\n", t.find("the value of the loop is the auditable decision, not the number.", i))
if i > 0 and j > i:
    NEW = ("Table IXc gives the four reference points. The fixed threshold loses 5.2 pp across the drift (95.8% to "
           "90.6%). The loop detects the drift in **one chunk** (15 decision epochs, ~150 s of twin time) and spends 52 "
           "polar probe attempts, 1.7% of the stream. The gate then *rejects* its own candidate: at +2 s the replay "
           "predicts no net gain, because the extra lead buys late successes at the price of window failures—the "
           "trade-off of Table IXb—so the loop rolls back to 18 s and ends at 89.7%, below the fixed threshold and "
           "below the EWMA quantile (93.6%). We report this as a failure of replay-based admission under drift, not as "
           "a demonstrated recovery: an online quantile is enough at this drift magnitude, and the loop's value here is "
           "the auditable refusal, not the score.")
    t = t[:i] + NEW + t[j:]
    done.append("closed-loop paragraph tightened")

# 3. park Table XII in the supplement
i = t.find("**Table XII.")
if i > 0:
    j = t.find("\n\n", t.find("| independent judge", i))
    block = t[i:j]
    t = t[:i] + ("*Annotation table.* The four views, their counts and the κ values are Table J1 of the supplementary "
                 "material.") + t[j:]
    supp = supp.rstrip() + "\n\n## Appendix J1. Annotation of the twenty proposals\n\n" + \
        block.replace("**Table XII.", "**Table J1.") + "\n"
    done.append("Table XII -> J1")

t = re.sub(r"\n{3,}", "\n\n", t)
p.write_text(t, encoding="utf-8")
supp_path.write_text(supp, encoding="utf-8")
print("edits:", done, "| words:", len(re.findall(r"[A-Za-z0-9']+", t)))
