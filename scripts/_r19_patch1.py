"""R19: add an IEEE Transactions mode to the builder (two columns, IEEE page box, column-width tables/figures)."""
from __future__ import annotations

from pathlib import Path

D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"
p = D / "build_paper_docx.js"
s = p.read_text(encoding="utf-8")

if "const IEEE =" in s:
    raise SystemExit("already patched")

# ---------------------------------------------------------------- 1. constants
old = 'const CONTENT_WIDTH = 9000; // A4, 1in margins, in twips (leave slack for grid rounding)'
new = '''const IEEE = process.env.IEEE === "1";
let CONTENT_WIDTH = 9000; // review build: A4, 1in margins
const COL_WIDTH = IEEE ? 5004 : 9000;  // one IEEE column (3.47 in) or the whole review page
if (IEEE) CONTENT_WIDTH = 10368;       // two-column text box (7.2 in) for full-width tables'''
if old not in s:
    raise SystemExit("CONTENT_WIDTH line not found")
s = s.replace(old, new, 1)

# ---------------------------------------------------------------- 2. font sizes
old = 'const BODY_SIZE = 21; // 10.5pt'
new = 'const BODY_SIZE = IEEE ? 20 : 21; // 10pt in IEEE mode'
s = s.replace(old, new, 1)
old = 'const SMALL_SIZE = 18; // 9pt'
new = 'const SMALL_SIZE = IEEE ? 16 : 18; // 8pt in IEEE mode'
s = s.replace(old, new, 1)

# ---------------------------------------------------------------- 3. figures at column width
old = '  const widthTwips = 5800;'
new = '  const widthTwips = IEEE ? COL_WIDTH - 40 : 5800;'
s = s.replace(old, new, 1)

# ---------------------------------------------------------------- 4. table widths + wide flag
old = '''  const totalW = weights.reduce((a, b) => a + b, 0);
  const widths = weights.map((w) => Math.max(700, Math.round((w / totalW) * CONTENT_WIDTH)));
  const scale = CONTENT_WIDTH / widths.reduce((a, b) => a + b, 0);'''
new = '''  const wide = nCols >= 6;                       // wide tables get their own one-column section
  const target = IEEE ? (wide ? CONTENT_WIDTH : COL_WIDTH) : CONTENT_WIDTH;
  const totalW = weights.reduce((a, b) => a + b, 0);
  const widths = weights.map((w) => Math.max(500, Math.round((w / totalW) * target)));
  const scale = target / widths.reduce((a, b) => a + b, 0);'''
if old not in s:
    raise SystemExit("table width block not found")
s = s.replace(old, new, 1)

# tag the returned table so the section splitter can find it
old = "const tbl = new Table({"
if old in s:
    s = s.replace(old, "const tbl = new Table({", 1)
# find the return statement of parseTable to tag
import re
m = re.search(r"\n  return (tbl|new Table\(\{[\s\S]*?\n  \}\)|table);", s)
print("parseTable return pattern:", bool(m))

p.write_text(s, encoding="utf-8")
print("constants patched")
