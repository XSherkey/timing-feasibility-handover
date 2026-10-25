from docx import Document
p = r"D:\Desktop_Files\论文\1. LLM Satellite Reinforcement Learning\自己写\From Human Intent to In-Orbit Action\EAAI\Revised_Manuscript_实测数据填充版.docx"
d = Document(p)
import re
for i, x in enumerate(d.paragraphs):
    t = x.text
    if any(k in t for k in ("repeated 20 times", "Table 8", "Table 9", "oracle", "MEASURED", "NOT MEASURED", "PARTIALLY", "does not generalise")):
        print(f"--- [{i}] ---")
        print(t[:600])
        print()
