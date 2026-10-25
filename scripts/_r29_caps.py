"""R29 part 3: clarify the deterministic-arm rows in Tables IX and X, and verify D2 in the built supplement."""
from __future__ import annotations

import re
import zipfile
from pathlib import Path

from docx import Document

D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"
p = D / "paper_en.md"
t = p.read_text(encoding="utf-8")
done = []

# Table IX caption: A8 is deterministic
i = t.find("**Table IX. Contribution isolation")
if i > 0:
    j = t.find("\n\n", i)
    cap = t[i:j].rstrip()
    if "A8 is deterministic" not in cap:
        add = (" A8 is deterministic: its row reports the difference from A0 measured against A0's seed "
               "distribution, so the interval describes the learned arm's variability, not A8's, and the TOST "
               "column states equivalence with that reading.")
        if cap.endswith("**"):
            cap = cap[:-2] + add + "**"
        else:
            cap = cap + add
        t = t[:i] + cap + t[j:]
        done.append("Table IX caption")

# Table X caption: tuned constant is deterministic
i = t.find("**Table X. Lockbox vs evaluation window")
if i > 0:
    j = t.find("\n\n", i)
    cap = t[i:j].rstrip()
    if "tuned constant is deterministic" not in cap:
        add = (" The tuned constant is deterministic, so the deployed-minus-constant contrast is read against the "
               "deployed arm's seed distribution; the TOST statement applies to that reading.")
        if cap.endswith("**"):
            cap = cap[:-2] + add + "**"
        else:
            cap = cap + add
        t = t[:i] + cap + t[j:]
        done.append("Table X caption")

p.write_text(re.sub(r"\n{3,}", "\n\n", t), encoding="utf-8")
print("edits:", done)

# verify D2 columns in the built supplement
doc = Document(str(D / "supplementary" / "supp_en.docx"))
for tbl in doc.tables:
    head = [c.text.strip() for c in tbl.rows[0].cells]
    if "validation gain" in head[1] if len(head) > 1 else False:
        print("D2 header:", head, "rows:", len(tbl.rows))
    elif "id" == head[0] and len(head) == 5:
        print("D2-like table:", head)
