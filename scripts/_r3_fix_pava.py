"""Fix the PAVA helper: return one fitted value per bin (block sizes, not weights)."""
from __future__ import annotations

from pathlib import Path

p = Path(__file__).resolve().parents[1] / "experiments" / "run_passive_identifiability.py"
t = p.read_text(encoding="utf-8")

start = t.index("def pava_decreasing")
end = t.index("def curve(")
new = '''def pava_decreasing(x: np.ndarray, y: np.ndarray, w: np.ndarray) -> np.ndarray:
    """Pool-adjacent-violators for a non-increasing sequence; one value per bin."""
    y = -np.asarray(y, dtype=float)
    w = np.asarray(w, dtype=float)
    vals, wts, cnt = [], [], []
    for yi, wi in zip(y, w):
        vals.append(yi)
        wts.append(max(wi, 1e-9))
        cnt.append(1)
        while len(vals) > 1 and vals[-2] > vals[-1]:
            v2, w2, c2 = vals.pop(), wts.pop(), cnt.pop()
            v1, w1, c1 = vals.pop(), wts.pop(), cnt.pop()
            vals.append((v1 * w1 + v2 * w2) / (w1 + w2))
            wts.append(w1 + w2)
            cnt.append(c1 + c2)
    out = []
    for v, c in zip(vals, cnt):
        out.extend([v] * c)
    return -np.asarray(out)


'''
t = t[:start] + new + t[end:]
p.write_text(t, encoding="utf-8")
print("PAVA fixed")
