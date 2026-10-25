from pathlib import Path

p = Path(__file__).resolve().parents[1] / "experiments" / "run_isolation_lean.py"
t = p.read_text(encoding="utf-8")
pairs = [
    ("SEL = [0, 1, 2]", "SEL = [0, 1]"),
    ("while len(RANDOM) < 20:", "while len(RANDOM) < 12:"),
    ('instances = {"eval": None, **{f"lb{e:g}": e for e in LOCKBOX_EPOCHS}}',
     'instances = {"eval": None, **{f"lb{e:g}": e for e in LOCKBOX_EPOCHS[:1]}}'),
]
for old, new in pairs:
    if t.count(old) != 1:
        raise SystemExit("missing: " + old[:40])
    t = t.replace(old, new, 1)
p.write_text(t, encoding="utf-8")
print("trimmed")
