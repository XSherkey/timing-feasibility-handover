from pathlib import Path

p = Path(__file__).resolve().parents[1] / "experiments" / "r3lib.py"
t = p.read_text(encoding="utf-8")

old = '''def _key(params: dict) -> str:
    import re

    items = sorted((k, str(v)) for k, v in params.items())
    raw = "_".join(f"{k}{v}" for k, v in items)
    return re.sub(r"[^A-Za-z0-9_=-]+", "-", raw)[:180]'''
new = '''def _key(params: dict) -> str:
    import hashlib
    import re

    items = sorted((k, str(v)) for k, v in params.items())
    raw = "_".join(f"{k}{v}" for k, v in items)
    slug = re.sub(r"[^A-Za-z0-9_=-]+", "-", raw)[:60].strip("-")
    return f"{slug}_{hashlib.sha1(raw.encode('utf-8')).hexdigest()[:12]}"'''
if t.count(old) != 1:
    raise SystemExit("key fn not found")
t = t.replace(old, new, 1)
p.write_text(t, encoding="utf-8")
print("cache key hashed")
