"""Render COVER_LETTER.md into a clean, editable .docx and a .pdf."""
from __future__ import annotations

import re
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Pt, Inches

D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"
src = D / "COVER_LETTER.md"
out = D / "COVER_LETTER.docx"

doc = Document()
sec = doc.sections[0]
sec.left_margin = sec.right_margin = Inches(1.0)
sec.top_margin = sec.bottom_margin = Inches(1.0)
normal = doc.styles["Normal"]
normal.font.name = "Times New Roman"
normal.font.size = Pt(11)

lines = src.read_text(encoding="utf-8").splitlines()
i = 0
while i < len(lines):
    raw = lines[i].rstrip()
    if not raw.strip() or raw.strip() == "---":
        i += 1
        continue
    if raw.startswith("# "):
        p = doc.add_paragraph()
        r = p.add_run(raw[2:].strip())
        r.bold = True
        r.font.size = Pt(12)
        p.paragraph_format.space_after = Pt(8)
        i += 1
        continue
    if raw.startswith("**") and raw.rstrip().endswith("**") and raw.count("**") == 2:
        p = doc.add_paragraph()
        text = raw.strip().strip("*")
        if text.lower().startswith(("to:", "date:", "manuscript title:", "authors:", "type:")):
            r = p.add_run(text)
            r.font.size = Pt(10.5)
            p.paragraph_format.space_after = Pt(2)
        else:
            r = p.add_run(text)
            r.bold = True
            r.font.size = Pt(11)
            p.paragraph_format.space_before = Pt(8)
            p.paragraph_format.space_after = Pt(4)
        i += 1
        continue
    # body paragraph: join wrapped lines
    buf = [raw]
    i += 1
    while i < len(lines) and lines[i].strip() and not lines[i].startswith(("#", "**", "---")):
        buf.append(lines[i].strip())
        i += 1
    text = " ".join(buf)
    # strip markdown emphasis but keep words
    text = text.replace("**", "").replace("*", "")
    p = doc.add_paragraph(text)
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p.paragraph_format.space_after = Pt(8)

doc.save(str(out))
print("written", out, "paragraphs", len(doc.paragraphs))
