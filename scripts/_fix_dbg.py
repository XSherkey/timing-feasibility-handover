from pathlib import Path
p = Path(r"D:\almond-repro\scripts\debug_forensic_call.py")
s = p.read_text(encoding="utf-8")
s = s.replace("from almond.llm.prompts import DECODING, render_prompt",
              "from almond.llm.backend import DECODING, MAX_TOKENS\nfrom almond.llm.prompts import render_prompt")
s = s.replace("max_tokens=1024,", "max_tokens=MAX_TOKENS,")
p.write_text(s, encoding="utf-8")
print("fixed imports")
