"""R23 part 2: merge the duplicated 'Threshold ledger' lead-in into one paragraph."""
from __future__ import annotations

from pathlib import Path

D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"
p = D / "paper_en.md"
t = p.read_text(encoding="utf-8")

pointer = ("*Threshold ledger.* Which rule each reported number executes is tabulated in Appendix G of the "
           "supplementary material; no number in this paper depends on reading that table.")
print("pointer found:", t.count(pointer))
if t.count(pointer) == 1:
    t = t.replace(pointer, "", 1)
    t = t.replace("\n\n\n", "\n\n")
    # attach the pointer to the substantive paragraph
    anchor = "any passage that does not is an error to be corrected."
    if t.count(anchor) == 1:
        t = t.replace(anchor, anchor + " The full ledger, with the exchange-rate oracles, is Table G1 of the "
                                      "supplementary material; no number in this paper depends on reading it.", 1)
        print("pointer merged")
    p.write_text(t, encoding="utf-8")

import re
t = p.read_text(encoding="utf-8")
print("threshold-ledger paragraphs:", len(re.findall(r"Threshold ledger", t)))
