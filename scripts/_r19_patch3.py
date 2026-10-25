"""R19 part 3: hoist the IEEE flag above its first use."""
from __future__ import annotations

from pathlib import Path

D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"
p = D / "build_paper_docx.js"
s = p.read_text(encoding="utf-8")

# remove the late declaration
old = '''const IEEE = process.env.IEEE === "1";
let CONTENT_WIDTH = 9000; // review build: A4, 1in margins'''
new = '''let CONTENT_WIDTH = 9000; // review build: A4, 1in margins'''
assert old in s
s = s.replace(old, new, 1)

# insert the flag right after isZh is known
anchor = "const isZh ="
i = s.find(anchor)
assert i >= 0
line_end = s.find("\n", i)
s = s[:line_end + 1] + 'const IEEE = process.env.IEEE === "1";\n' + s[line_end + 1:]

p.write_text(s, encoding="utf-8")
print("IEEE flag hoisted")
