"""R7 (v9) EN: fix reference [43] wording (no 'under review' in the citation)."""
from __future__ import annotations

from pathlib import Path

P = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本" / "paper_en.md"
t = P.read_text(encoding="utf-8")
old = 'submitted to *Eng. Appl. Artif. Intell.* (under review). (Prior report of the ALMOND pipeline'
new = 'submitted for publication, 2026. (Prior report of the ALMOND pipeline'
if t.count(old) != 1:
    raise SystemExit(f"anchor not found ({t.count(old)})")
t = t.replace(old, new, 1)
P.write_text(t, encoding="utf-8")
print("ref [43] updated")
