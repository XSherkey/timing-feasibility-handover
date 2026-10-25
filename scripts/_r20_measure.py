import re
from pathlib import Path

t = Path(r"../From Human Intent to In-Orbit Action/IEEE_Trans_新版本/paper_en.md").read_text(encoding="utf-8")
parts = re.split(r"\n(?=## )", t)
for p in parts:
    head = p.split("\n", 1)[0][:52]
    words = len(re.findall(r"[A-Za-z0-9']+", p))
    print("%5d  %s" % (words, head))
print("total", len(re.findall(r"[A-Za-z0-9']+", t)))
