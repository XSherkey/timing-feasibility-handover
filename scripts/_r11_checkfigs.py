from pathlib import Path

from docx import Document
from docx.text.paragraph import Paragraph

D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"
doc = Document(D / "Paper_EN_v54.docx")
seq = []
for ch in doc.element.body.iterchildren():
    tag = ch.tag.split("}")[1]
    if tag == "p":
        p = Paragraph(ch, doc)
        has = bool(ch.findall(".//{http://schemas.openxmlformats.org/drawingml/2006/main}blip"))
        seq.append(("IMG" if has else "P", p))
    elif tag == "tbl":
        seq.append(("T", None))
for i, (k, p) in enumerate(seq):
    if k != "IMG":
        continue
    nxt = seq[i + 1][1] if i + 1 < len(seq) else None
    label = nxt.runs[0].text if (nxt is not None and nxt.runs) else "?"
    print(i, "|", label, "|", (nxt.text if nxt is not None else "")[:52])
