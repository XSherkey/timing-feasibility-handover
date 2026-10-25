"""R19 part 4: continuous section breaks, and split after the abstract rather than at the first heading."""
from __future__ import annotations

from pathlib import Path

D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"
p = D / "build_paper_docx.js"
s = p.read_text(encoding="utf-8")

# 1. continuous breaks
old = """    page: { size: { width: PAGE.width, height: PAGE.height }, margin: PAGE.margin },
    ...(cols > 1 ? { column: { count: cols, space: 360 } } : {}),"""
new = """    type: SectionType.CONTINUOUS,
    page: { size: { width: PAGE.width, height: PAGE.height }, margin: PAGE.margin },
    ...(cols > 1 ? { column: { count: cols, space: 360 } } : {}),"""
if old not in s:
    raise SystemExit("section properties block not found")
s = s.replace(old, new, 1)

# 2. import SectionType
if "SectionType," not in s.split("} from \"docx\";")[0]:
    s = s.replace("  ShadingType,", "  SectionType,\n  ShadingType,", 1)

# 3. split after the abstract: the front matter is title + authors + abstract + index terms
old = """    if (firstH1 < 0) firstH1 = children.length;"""
new = """    if (firstH1 < 0 && /^##\\s*(Nomenclature|Index Terms|索引|符号表)/.test(line)) {
      firstH1 = children.length;
    }"""
if old not in s:
    raise SystemExit("H1 marker not found")
s = s.replace(old, new, 1)

p.write_text(s, encoding="utf-8")
print("continuous sections + abstract split")
