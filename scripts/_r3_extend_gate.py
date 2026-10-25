"""Extend the gate candidate bank with genuinely harmful candidates (cap effects)."""
from __future__ import annotations

from pathlib import Path

p = Path(__file__).resolve().parents[1] / "experiments" / "run_gate_systematic.py"
t = p.read_text(encoding="utf-8")
old = '''    ("G20", "prefer_same_plane:0@latitude_abs_deg>=0"),
]'''
new = '''    ("G20", "prefer_same_plane:0@latitude_abs_deg>=0"),
    # deliberately harmful: caps that cut the lead below the acquisition requirement
    ("G21", "cap_advance:6@latitude_abs_deg>=68"),
    ("G22", "cap_advance:8@latitude_abs_deg>=68"),
    ("G23", "cap_advance:10@latitude_abs_deg>=0"),
    ("G24", "cap_advance:12@latitude_abs_deg>=68"),
    ("G25", "prefer_long_visibility:0@latitude_abs_deg>=0"),
    ("G26", "cap_advance:4@latitude_abs_deg>=68"),
]'''
if t.count(old) != 1:
    raise SystemExit("bank tail not found")
t = t.replace(old, new, 1)
p.write_text(t, encoding="utf-8")
print("bank extended to 26 candidates")
