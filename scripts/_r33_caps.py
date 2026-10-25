"""R33 part 6: force the G2/G3 captions into a single bold span."""
from __future__ import annotations

import re
from pathlib import Path

p = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本" / "supplementary" / "supp_en.md"
s = p.read_text(encoding="utf-8")

for start in ("**Table G2.", "**Table G3."):
    i = s.find(start)
    if i < 0:
        print("missing", start)
        continue
    j = s.find("\n\n", i)
    block = s[i:j]
    clean = block.replace("*", "").strip()
    s = s[:i] + "**" + clean + "**" + s[j:]
    print("fixed", start, "->", s[i:i + 40].replace("\n", " "))

p.write_text(re.sub(r"\n{3,}", "\n\n", s), encoding="utf-8")
print("asterisk count in G2/G3 captions:",
      s[s.find("**Table G2."):s.find("**Table G3.")].count("*"),
      s[s.find("**Table G3."):s.find("## Appendix H.")].count("*"))
