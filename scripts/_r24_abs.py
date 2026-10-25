import re
from pathlib import Path

t = Path(r"../From Human Intent to In-Orbit Action/IEEE_Trans_新版本/paper_en.md").read_text(encoding="utf-8")
i = t.find("**Abstract—**")
j = t.find("**Index Terms—**")
a = t[i:j]
print("words:", len(re.findall(r"[A-Za-z0-9']+", a)))
print(a)
