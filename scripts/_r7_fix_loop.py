from pathlib import Path

p = Path(__file__).resolve().parent / "_r7_refs_code.py"
t = p.read_text(encoding="utf-8")
old = "    for old, new in zip(REFS[::2], REFS[1::2]):"
new = "    for old, new in REFS:"
if old not in t:
    raise SystemExit("loop line not found")
t = t.replace(old, new, 1)
p.write_text(t, encoding="utf-8")
print("patched loop")
