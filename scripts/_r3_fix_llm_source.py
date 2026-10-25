"""Patch run_llm_proposals.py: draw the narratives from the dumped training-window attempt log."""
from __future__ import annotations

from pathlib import Path

p = Path(__file__).resolve().parents[1] / "experiments" / "run_llm_proposals.py"
t = p.read_text(encoding="utf-8")

old = '''def training_failures() -> list[dict]:
    p = ROOT / "results" / "campaign_1023" / "ppomlp_seed0" / "run_summary.json"
    d = json.loads(p.read_text(encoding="utf-8"))
    n_time = 4320
    rows = [a for a in d["final"]["attempts"]
            if a["t_index"] < TRAIN_FRAC * n_time
            and (a.get("cause") in ("late_handover", "window_exceeded", "no_route"))]
    rows.sort(key=lambda a: float(a.get("handover_advance_s", 0.0)))
    return rows[:N_NARR * 4]'''
new = '''def training_failures() -> list[dict]:
    """Failures from the TRAINING window only, produced by a passive no-shield rollout."""
    p = OUT / "llm_proposals" / "train_attempts.json"
    rows = json.loads(p.read_text(encoding="utf-8"))
    n_time = 4320
    rows = [a for a in rows
            if a["t_index"] < TRAIN_FRAC * n_time
            and a.get("cause") in ("late_handover", "window_exceeded", "no_route")]
    rows.sort(key=lambda a: float(a.get("handover_advance_s", 0.0)))
    return rows[: N_NARR * 4]'''
if t.count(old) != 1:
    raise SystemExit("training_failures not found")
t = t.replace(old, new, 1)
p.write_text(t, encoding="utf-8")
print("narrative source switched to the training-window dump")
