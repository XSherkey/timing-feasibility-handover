"""Fix the KM estimator in the precision study (correct at-risk accounting)."""
from __future__ import annotations

from pathlib import Path

p = Path(__file__).resolve().parent / "run_precision.py"
t = p.read_text(encoding="utf-8")

old_start = t.index("def km_curve(sample):")
old_end = t.index("def crossing(sample):")
NEW = '''def km_curve(sample):
    """Kaplan-Meier survival of T_z with right-censoring at the advance for late attempts."""
    tz = np.array([r["tz"] if r["ok"] else r["adv"] for r in sample], dtype=float)
    ev = np.array([1 if r["ok"] else 0 for r in sample], dtype=int)
    times = np.unique(tz)
    surv, s = [], 1.0
    for t in times:
        at_risk = float(np.sum(tz >= t))
        d = float(np.sum((tz == t) & (ev == 1)))
        if at_risk > 0 and d > 0:
            s *= (1.0 - d / at_risk)
        surv.append((float(t), s))
    return surv


'''
t = t[:old_start] + NEW + t[old_end:]
p.write_text(t, encoding="utf-8")
print("km_curve replaced")
