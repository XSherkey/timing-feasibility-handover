from docx import Document
p = r"D:\Desktop_Files\论文\1. LLM Satellite Reinforcement Learning\自己写\From Human Intent to In-Orbit Action\EAAI\Revised_Manuscript_修改稿.docx"
d = Document(p)
for i in (114, 117, 119, 121, 123, 125, 127, 129):
    print(f"===== [{i}] =====")
    print(d.paragraphs[i].text)
    print()
