"""Register Figs 8-9 in the docx builder."""
from __future__ import annotations

from pathlib import Path

p = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本" / "build_paper_docx.js"
t = p.read_text(encoding="utf-8")
old = '  7: "fig7_gate.png",'
new = '  7: "fig7_gate.png",\n  8: "fig8_architecture.png",\n  9: "fig9_passive_support.png",'
if old not in t:
    raise SystemExit("FIG_FILES tail not found")
t = t.replace(old, new, 1)
p.write_text(t, encoding="utf-8")
print("figures 8-9 registered")
