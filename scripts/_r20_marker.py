"""R20 part 9: cut the front matter at the Introduction heading (the Nomenclature marker is gone)."""
from __future__ import annotations

from pathlib import Path

D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"
p = D / "build_paper_docx.js"
s = p.read_text(encoding="utf-8")

old = '/^##\\s*(Nomenclature|Index Terms|索引|符号表)/.test(line)'
new = '/^##\\s*(Nomenclature|Index Terms|I\\. Introduction|索引|符号表)/.test(line)'
if old not in s:
    raise SystemExit("marker regex not found")
s = s.replace(old, new, 1)
p.write_text(s, encoding="utf-8")
print("split marker now matches the Introduction heading")
