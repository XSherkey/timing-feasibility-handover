from pathlib import Path

p = Path(__file__).resolve().parents[1] / "experiments" / "r3lib.py"
t = p.read_text(encoding="utf-8")
old = '''    if cp.exists():
        return json.loads(cp.read_text(encoding="utf-8"))'''
new = '''    if cp.exists():
        return _normalise(json.loads(cp.read_text(encoding="utf-8")))'''
if t.count(old) != 1:
    raise SystemExit("cache-hit path not found")
t = t.replace(old, new, 1)
p.write_text(t, encoding="utf-8")
print("cache hit normalised")
