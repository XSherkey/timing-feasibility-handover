"""R21 part 2: set the reference list at 8 pt (IEEE style) and tighten its spacing."""
from __future__ import annotations

import sys
from pathlib import Path

from docx import Document
from docx.shared import Pt

path = Path(sys.argv[1])
doc = Document(str(path))
n = 0
for para in doc.paragraphs:
    txt = para.text.strip()
    if txt.startswith("[") and "]" in txt[:5]:
        para.paragraph_format.space_after = Pt(0)
        para.paragraph_format.space_before = Pt(0)
        para.paragraph_format.line_spacing = 1.0
        for run in para.runs:
            run.font.size = Pt(8)
        n += 1
doc.save(str(path))
print(f"references set at 8pt: {n} paragraphs")
