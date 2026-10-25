"""Patch build_paper_docx.js so consecutive body lines become ONE paragraph.

The manuscript is hard-wrapped, and the builder emitted one paragraph per wrapped line, which is
what produced the ragged half-sentences in the PDF. This joins runs of plain lines and keeps every
structural element (tables, headings, captions, lists, references, code) on its own boundary.
"""
from __future__ import annotations

import re
from pathlib import Path

D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"
p = D / "build_paper_docx.js"
s = p.read_text(encoding="utf-8")

if "const paraBuf" in s:
    raise SystemExit("already patched")

# 1. declare the buffer next to the other loop state
s = s.replace("let codeBuf = [];", "let codeBuf = [];\nlet paraBuf = [];", 1)

# 2. helper: flush the accumulated body paragraph (with figure placement)
anchor = "const flushCode = () => {"
helper = '''const isStructural = (ln) => {
  const t = ln.trim();
  return (
    !t ||
    t.startsWith("|") ||
    t.startsWith("```") ||
    t.startsWith("#") ||
    /^\\*\\*(Fig\\.|图|Table|表)\\s*/.test(t) ||
    /^\\[\\d+\\]/.test(t) ||
    /^\\d+\\.\\s/.test(t) ||
    /^[-*]\\s/.test(t) ||
    /^---+$/.test(t)
  );
};

'''
s = s.replace(anchor, helper + anchor, 1)

p.write_text(s, encoding="utf-8")
print("patch step 1 written; next: wire the buffer into the loop")
