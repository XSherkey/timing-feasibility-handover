"""Show the block order of the final document, marking images and the References heading."""
import sys
from pathlib import Path

from docx import Document
from docx.table import Table
from docx.text.paragraph import Paragraph

D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"
name = sys.argv[1] if len(sys.argv) > 1 else "Paper_EN_v12.docx"
doc = Document(D / name)

blocks = []
for child in doc.element.body.iterchildren():
    tag = child.tag.split("}")[-1]
    if tag == "p":
        para = Paragraph(child, doc)
        has_img = bool(child.findall(".//{http://schemas.openxmlformats.org/drawingml/2006/main}blip"))
        blocks.append(("IMG" if has_img else "P", para.text.strip()[:70]))
    elif tag == "tbl":
        blocks.append(("TBL", ""))

refs_at = None
for i, (kind, text) in enumerate(blocks):
    if text.startswith("References") or text.startswith("参考文献"):
        refs_at = i
        break
print("total blocks:", len(blocks), "| references heading at", refs_at)
print("--- last 24 blocks ---")
for kind, text in blocks[-24:]:
    print(f"  {kind:4s} {text}")
print("--- images after the references heading ---")
if refs_at is not None:
    for i, (kind, text) in enumerate(blocks[refs_at:], start=refs_at):
        if kind == "IMG":
            print("   image at block", i)
