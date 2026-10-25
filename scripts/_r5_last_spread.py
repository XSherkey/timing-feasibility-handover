from pathlib import Path

p = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本" / "paper_en.md"
t = p.read_text(encoding="utf-8")
old = "The per-seed spread collapses from \u00b113.2 to \u00b10.26 pp."
new = "The per-seed spread collapses from \u00b113.2 to \u00b10.05 pp."
print("spread count", t.count(old))
if t.count(old) == 1:
    t = t.replace(old, new, 1)
    p.write_text(t, encoding="utf-8")
    print("spread fixed")

import re
for k in ("93.31", "92.43", "93.17"):
    for m in re.finditer(re.escape(k), t):
        print(k, "::", repr(t[max(0, m.start() - 110):m.start() + 70]))
