import re
from pathlib import Path

from docx import Document

D = Path(r"../From Human Intent to In-Orbit Action/IEEE_Trans_新版本")
doc = Document(str(D / "Paper_EN_IEEE_v82.docx"))

# order of figures vs references
body = doc.element.body
order = []
for child in body.iterchildren():
    tag = child.tag.split("}")[-1]
    if tag == "p":
        txt = "".join(n.text or "" for n in child.iter() if n.tag.endswith("}t"))
        if txt.strip().startswith("Fig."):
            order.append(("caption", txt.strip()[:14]))
        if "REFERENCES" in txt.upper() and len(txt) < 40:
            order.append(("REFS", txt.strip()[:20]))
        if child.findall(".//{http://schemas.openxmlformats.org/drawingml/2006/main}blip"):
            order.append(("image", ""))
print("body order (figures/refs):")
for o in order:
    print("  ", o)

t = (D / "paper_en.md").read_text(encoding="utf-8")
print("\nduplicate 'Acquisition requirement' paragraphs:", t.count("**Acquisition requirement.**"))
print("'five physically motivated':", t.count("five physically motivated"))
print("limitations:", re.findall(r"Four limits[^.]*\.", t)[:1], "| all four:", t.count("all four bound"))
print("abstract drift:", re.findall(r"at \+2 s the tuned constant[^.]*\.", t)[:1])
print("Stray '**' in table captions:", [m.group(0)[:40] for m in re.finditer(r"\*\*Table [A-Za-z0-9]+\.(?:(?!\*\*).)*$", t, flags=re.M)][:3])
