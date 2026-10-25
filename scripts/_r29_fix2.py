from __future__ import annotations

import re
from pathlib import Path

p = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本" / "paper_en.md"
t = p.read_text(encoding="utf-8")

n = t.count("What (3) does not give")
t = t.replace("What (3) does not give", "What (4) does not give")
print("What (3) fixed:", n)

i = t.find("value of the loop")
if i > 0:
    j = t.find("\n\n", i)
    print("context:", repr(t[max(0, i-420):j])[:600])
    # replace the whole sentence that carries the phrase
    start = t.rfind(". ", 0, i)
    t = t[:start + 2] + ("The loop buys detection and an auditable refusal, not recovery: on this stream it adds probe "
                         "cost and ends below both the fixed threshold and the EWMA baseline, so we claim no online "
                         "adaptation and record the protocol as unvalidated for autonomous use.") + t[j:]
    print("closing rewritten")
p.write_text(re.sub(r"\n{3,}", "\n\n", t), encoding="utf-8")
print("value of the loop left:", t.count("value of the loop"))
