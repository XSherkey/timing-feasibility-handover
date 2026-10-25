"""R7 (v9) ZH: join the remaining code continuations and fix reference [43]."""
from __future__ import annotations

from pathlib import Path

P = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本" / "paper_zh.md"
lines = P.read_text(encoding="utf-8").splitlines(keepends=True)
out = []
i = 0
joined = 0
while i < len(lines):
    cur = lines[i]
    if cur.rstrip("\n").rstrip().endswith("\\") and i + 1 < len(lines):
        nxt = lines[i + 1]
        merged = cur.rstrip("\n").rstrip()[:-1].rstrip() + " " + nxt.lstrip()
        out.append(merged)
        joined += 1
        i += 2
        continue
    out.append(cur)
    i += 1
t = "".join(out)
print("joined", joined)

old = 'submitted to *Eng. Appl. Artif. Intell.* (under review)'
if t.count(old) == 1:
    t = t.replace(old, "submitted for publication, 2026", 1)
    print("ref [43] updated")

P.write_text(t, encoding="utf-8")
print("remaining continuation lines:",
      sum(1 for l in t.splitlines() if l.rstrip().endswith("\\")))
