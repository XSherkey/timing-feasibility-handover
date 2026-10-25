"""Add a --window flag to eval_shield.py so every selection step can be confined to validation."""
from __future__ import annotations

from pathlib import Path

p = Path(__file__).resolve().parents[1] / "scripts" / "eval_shield.py"
t = p.read_text(encoding="utf-8")

old = '    ap.add_argument("--out", default=None)'
new = (
    '    ap.add_argument("--window", default="test",\n'
    '                    choices=("train", "validation", "test"),\n'
    '                    help="time window of the twin to evaluate on (test by default; "\n'
    '                         "validation is the only window that any selection step may touch)")\n'
    '    ap.add_argument("--out", default=None)'
)
if t.count(old) != 1:
    raise SystemExit("anchor 1 missing")
t = t.replace(old, new, 1)

old2 = 'test_idx = splits.indices(twin.n_time, "test", args.steps)'
new2 = 'test_idx = splits.indices(twin.n_time, args.window, args.steps)'
if t.count(old2) != 1:
    raise SystemExit("anchor 2 missing")
t = t.replace(old2, new2, 1)

p.write_text(t, encoding="utf-8")
print("eval_shield.py patched")
