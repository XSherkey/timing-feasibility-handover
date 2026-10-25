"""R3 helper patch: normalise eval_shield output (list of per-traffic records)."""
from __future__ import annotations

from pathlib import Path

p = Path(__file__).resolve().parents[1] / "experiments" / "r3lib.py"
t = p.read_text(encoding="utf-8")

old = '''    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0 or not cp.exists():
        raise RuntimeError(f"eval failed: {' '.join(cmd)}\\n{r.stdout[-800:]}\\n{r.stderr[-800:]}")
    return json.loads(cp.read_text(encoding="utf-8"))'''
new = '''    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0 or not cp.exists():
        raise RuntimeError(f"eval failed: {' '.join(cmd)}\\n{r.stdout[-800:]}\\n{r.stderr[-800:]}")
    raw = json.loads(cp.read_text(encoding="utf-8"))
    return _normalise(raw)


def _normalise(raw):
    """eval_shield writes one record per traffic multiplier; collapse to attempts-weighted means."""
    if isinstance(raw, dict):
        return raw
    if not isinstance(raw, list) or not raw:
        raise RuntimeError("empty eval output")
    if len(raw) == 1:
        return raw[0]
    def wavg(key):
        num = sum(float(r[key][0]) * float(r[key][1]) for r in raw if r.get(key) and r[key][1])
        den = sum(float(r[key][1]) for r in raw if r.get(key) and r[key][1])
        return [num / den if den else None, int(den)]
    first = dict(raw[0])
    for key in ("arctic", "midlat", "equatorial", "overall"):
        if all(r.get(key) for r in raw):
            first[key] = wavg(key)
    first["sat_records"] = [dict(satisfaction=r.get("satisfaction"),
                                 arctic=r.get("satisfaction_arctic")) for r in raw]
    return first'''
if t.count(old) != 1:
    raise SystemExit("evaluate() block not found")
t = t.replace(old, new, 1)

old2 = '''def late_share(res: dict) -> float:
    for k in ("late_share", "late_handover_share"):
        if k in res and res[k] is not None:
            return 100.0 * float(res[k])
    return float("nan")'''
new2 = '''def late_share(res: dict) -> float:
    for k in ("late_share", "late_handover_share"):
        if k in res and res[k] is not None:
            return 100.0 * float(res[k])
    pc = res.get("polar_causes") or {}
    if "late_handover" in pc:
        return 100.0 * float(pc["late_handover"])
    return float("nan")'''
if t.count(old2) != 1:
    raise SystemExit("late_share block not found")
t = t.replace(old2, new2, 1)
p.write_text(t, encoding="utf-8")
print("r3lib patched")
