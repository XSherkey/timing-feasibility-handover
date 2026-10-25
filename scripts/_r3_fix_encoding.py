from pathlib import Path

p = Path(__file__).resolve().parents[1] / "experiments" / "r3lib.py"
t = p.read_text(encoding="utf-8")
bad = 'r = subprocess.run(cmd, capture_output=True, text=True, encoding=utf-8, errors=replace)'
good = 'r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")'
if bad not in t:
    raise SystemExit("line not found")
t = t.replace(bad, good, 1)
p.write_text(t, encoding="utf-8")
print("fixed")
