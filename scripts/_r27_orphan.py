"""R27 part 4: delete the orphaned Table V body and repoint its references."""
from __future__ import annotations

import re
from pathlib import Path

D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"
p = D / "paper_en.md"
t = p.read_text(encoding="utf-8")

i = t.find("*Drift table.*")
if i < 0:
    raise SystemExit("pointer not found")
j = t.find("\n\n### ", i)
seg = t[i:j]
rows = [ln for ln in seg.splitlines() if ln.startswith("|")]
print("orphan rows:", len(rows))
t = t[:i] + ("*Drift table.* The per-regime numbers plotted in Fig. 7, with the probe study and its bootstrap, are "
             "Table H2 of the supplementary material; every value quoted in this section is in that table.") + t[j:]

# repoint the four references
n = 0
for m in reversed(list(re.finditer(r"Table V(?![I])", t))):
    t = t[:m.start()] + "Table H2" + t[m.end():]
    n += 1
print("refs repointed:", n)

t = re.sub(r"\n{3,}", "\n\n", t)
p.write_text(t, encoding="utf-8")
print("words:", len(re.findall(r"[A-Za-z0-9']+", t)))
