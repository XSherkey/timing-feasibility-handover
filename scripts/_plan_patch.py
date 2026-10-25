from pathlib import Path

p = Path(__file__).resolve().parent / "_plan_docx.py"
t = p.read_text(encoding="utf-8")
old = '    if line.startswith("# "):'
new = '''    if line.strip() == "---":
        i += 1
        continue
    if line.startswith("# "):'''
print("found:", t.count(old))
t = t.replace(old, new, 1)
p.write_text(t, encoding="utf-8")
print("patched")
