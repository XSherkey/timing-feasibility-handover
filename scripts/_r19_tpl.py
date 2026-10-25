from pathlib import Path

from docx import Document

p = Path(r"D:\Desktop_Files\论文\1. LLM Satellite Reinforcement Learning\自己写\IEEE 格式"
         r"\Transactions-template-and-instructions-on-how-to-create-your-article-formatted (4).docx")
d = Document(str(p))
print("sections:", len(d.sections))
for i, s in enumerate(d.sections):
    cols = s._sectPr.xpath("./w:cols/@w:num")
    print(i, "page", round(s.page_width.inches, 2), "x", round(s.page_height.inches, 2),
          "| margins L/R/T/B", round(s.left_margin.inches, 2), round(s.right_margin.inches, 2),
          round(s.top_margin.inches, 2), round(s.bottom_margin.inches, 2), "| cols", cols)

print("\nstyles:", [st.name for st in d.styles][:30])
print("\nfirst paragraphs:")
for para in d.paragraphs[:20]:
    txt = para.text.strip()
    if txt:
        print("  [", para.style.name, "]", txt[:90])
