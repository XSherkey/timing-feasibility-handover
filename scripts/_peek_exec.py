from pathlib import Path
p = Path(r"D:\almond-repro\almond\framework\kg.py")
s = p.read_text(encoding="utf-8")
import re
m = re.search(r"EXECUTABLE_EFFECTS\s*=\s*[^\n]*(?:\n[ \t]+[^\n]*)*", s)
print("BEFORE:")
print(m.group(0) if m else "not found")
