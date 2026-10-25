"""Patch step 3: flush the paragraph buffer before every structural emission."""
from __future__ import annotations

from pathlib import Path

D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"
p = D / "build_paper_docx.js"
s = p.read_text(encoding="utf-8")
n = 0

pairs = [
    ('  if (/^##\\s+/.test(line)) {\n    children.push(',
     '  if (/^##\\s+/.test(line)) {\n    flushPara();\n    children.push('),
    ('  if (/^\\*\\*(Fig\\.|图|Table|表)\\s*[^*]+\\*/.test(bodyLine)) {\n    children.push(captionPara(bodyLine));',
     '  if (/^\\*\\*(Fig\\.|图|Table|表)\\s*[^*]+\\*/.test(bodyLine)) {\n    flushPara();\n    children.push(captionPara(bodyLine));'),
    ('  if (line.startsWith("**Manuscript v2") || line.startsWith("**稿件 v2")) {\n    children.push(',
     '  if (line.startsWith("**Manuscript v2") || line.startsWith("**稿件 v2")) {\n    flushPara();\n    children.push('),
    ('  if (inRefs && /^\\[\\d+\\]/.test(bodyLine)) {\n    const refText',
     '  if (inRefs && /^\\[\\d+\\]/.test(bodyLine)) {\n    flushPara();\n    const refText'),
]
for old, new in pairs:
    if old in s:
        s = s.replace(old, new, 1)
        n += 1
    else:
        print("  MISS:", old[:60])
p.write_text(s, encoding="utf-8")
print("flushed before", n, "structural branches")
