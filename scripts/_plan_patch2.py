from pathlib import Path

p = Path(__file__).resolve().parent / "_plan_docx.py"
t = p.read_text(encoding="utf-8")

old = """            for ri, row in enumerate(rows):"""
new = """            # column widths proportional to the longest cell in each column
            lens = [max(len(r[c]) if c < len(r) else 0 for r in rows) for c in range(ncol)]
            total = sum(lens) or ncol
            widths = [max(0.8, 6.9 * l / total) for l in lens]
            table.autofit = False
            for ri, row in enumerate(rows):"""
print("anchor1:", t.count(old))
t = t.replace(old, new, 1)

old2 = """                    for para in cells[ci].paragraphs:"""
new2 = """                    cells[ci].width = __import__("docx").shared.Inches(widths[ci])
                    for para in cells[ci].paragraphs:"""
print("anchor2:", t.count(old2))
t = t.replace(old2, new2, 1)
p.write_text(t, encoding="utf-8")
print("patched")
