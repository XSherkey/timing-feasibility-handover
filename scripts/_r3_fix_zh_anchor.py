from pathlib import Path

p = Path(__file__).resolve().parent / "_r3_sync_zh.py"
t = p.read_text(encoding="utf-8")
old = 'rep("### L. 局限性", VIH + "### L. 局限性", "sections")'
new = 'rep("### H. 局限性", VIH + "### L. 局限性", "sections")'
if old not in t:
    raise SystemExit("anchor line not found")
t = t.replace(old, new, 1)
p.write_text(t, encoding="utf-8")
print("fixed ZH anchor")
