import re
from pathlib import Path

t = Path(r"../From Human Intent to In-Orbit Action/IEEE_Trans_新版本/paper_en.md").read_text(encoding="utf-8")
i = t.find("## VI. Experimental Evaluation")
j = t.find("## VII. Conclusion")
sec = t[i:j]
parts = re.split(r"\n(?=### )", sec)
for p in parts:
    head = p.split("\n", 1)[0][:60]
    words = len(re.findall(r"[A-Za-z0-9']+", p))
    print("%5d  %s" % (words, head))
