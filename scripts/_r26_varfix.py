from pathlib import Path

p = Path(__file__).resolve().parent / "_r26_var.py"
t = p.read_text(encoding="utf-8")
old = "{a['mean']:.2f}"
new = "{a['summary']['mean']:.2f}"
print("hits:", t.count(old))
t = t.replace(old, new, 1)
p.write_text(t, encoding="utf-8")
print("patched")
