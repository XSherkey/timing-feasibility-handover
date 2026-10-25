from pathlib import Path

p = Path(__file__).resolve().parent / "_r35_letter2.py"
t = p.read_text(encoding="utf-8")
old = '        rest = m.group(2).replace("**", "").replace("*", "")'
new = ('        import html as _html\n'
       '        rest = _html.unescape(m.group(2).replace("**", "").replace("*", ""))')
print("found:", t.count(old))
t = t.replace(old, new, 1)
p.write_text(t, encoding="utf-8")
print("patched")
