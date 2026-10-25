from pathlib import Path

p = Path(__file__).resolve().parents[1] / "experiments" / "r3lib.py"
t = p.read_text(encoding="utf-8")
old = 'r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")'
new = ('r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8",\n'
       '                       errors="replace", cwd=str(ROOT))')
if t.count(old) != 1:
    raise SystemExit("subprocess call not found")
t = t.replace(old, new, 1)
p.write_text(t, encoding="utf-8")
print("subprocess cwd set to ROOT")
