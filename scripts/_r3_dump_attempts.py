"""Add --dump-attempts to eval_shield.py (full attempt log as JSON) for the narrative study."""
from __future__ import annotations

from pathlib import Path

p = Path(__file__).resolve().parents[1] / "scripts" / "eval_shield.py"
t = p.read_text(encoding="utf-8")

old = '''    ap.add_argument("--dump-advance-dist", default=None,
                    help="write the polar handover-advance distribution to this JSON")'''
new = '''    ap.add_argument("--dump-advance-dist", default=None,
                    help="write the polar handover-advance distribution to this JSON")
    ap.add_argument("--dump-attempts", default=None,
                    help="write the full attempt log (JSON) to this path, for narrative studies")'''
if t.count(old) != 1:
    raise SystemExit("arg anchor missing")
t = t.replace(old, new, 1)

old2 = """    if args.dump_advance_dist:"""
new2 = """    if args.dump_attempts:
        Path(args.dump_attempts).parent.mkdir(parents=True, exist_ok=True)
        Path(args.dump_attempts).write_text(
            json.dumps(attempts, default=float), encoding="utf-8")
        print(f"wrote {len(attempts)} attempts to {args.dump_attempts}")

    if args.dump_advance_dist:"""
if t.count(old2) != 1:
    raise SystemExit("dump anchor missing")
t = t.replace(old2, new2, 1)

p.write_text(t, encoding="utf-8")
print("eval_shield: --dump-attempts added")
