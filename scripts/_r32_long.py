import re
from pathlib import Path

t = Path(r"../From Human Intent to In-Orbit Action/IEEE_Trans_新版本/paper_en.md").read_text(encoding="utf-8")
paras = [p for p in t.split("\n\n") if p.strip() and not p.strip().startswith(("|", "**Table", "**Fig", "#", "```"))]
scored = sorted(((len(re.findall(r"[A-Za-z0-9']+", p)), p) for p in paras), reverse=True)
for n, p in scored[:12]:
    print(n, "|", p[:110].replace("\n", " "))
