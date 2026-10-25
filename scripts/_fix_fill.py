"""Patcher: let table-cell rules match on the whole row's text."""
from pathlib import Path

p = Path(__file__).resolve().parents[1] / "scripts" / "fill_docx.py"
s = p.read_text(encoding="utf-8")

old = '''    def process(paragraph) -> None:
        text = paragraph.text
        markers = MARKER.findall(text)
        if not markers:
            return
        stats["markers"] += len(markers)
        values = None
        for ctx, vals in rules:
            if ctx in text:
                values = vals
                break'''
new = '''    def process(paragraph, row_context: str = "") -> None:
        text = paragraph.text
        markers = MARKER.findall(text)
        if not markers:
            return
        stats["markers"] += len(markers)
        values = None
        haystack = text + " || " + row_context
        for ctx, vals in rules:
            if ctx in haystack:
                values = vals
                break'''
assert old in s
s = s.replace(old, new, 1)

old2 = '''    for tbl in doc.tables:
        for row in tbl.rows:
            for cell in row.cells:
                for p in cell.paragraphs:
                    process(p)'''
new2 = '''    for tbl in doc.tables:
        for row in tbl.rows:
            row_ctx = " ".join(c.text for c in row.cells)
            for cell in row.cells:
                for p in cell.paragraphs:
                    process(p, row_ctx)'''
assert old2 in s
s = s.replace(old2, new2, 1)
p.write_text(s, encoding="utf-8")
print("patched fill_docx.py")
