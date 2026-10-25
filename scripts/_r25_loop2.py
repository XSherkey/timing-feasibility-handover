from pathlib import Path

p = Path(__file__).resolve().parents[1] / "experiments" / "run_closed_loop.py"
t = p.read_text(encoding="utf-8")

# 1. faster alarm
old = "                if cusum > 6.0 and alarm_chunk is None:"
new = "                if cusum > 3.0 and alarm_chunk is None:"
print("cusum:", t.count(old)); t = t.replace(old, new, 1)

# 2. the gate must replay on the pre-probe chunk (unforced advances), not the probe chunk
old2 = """                    recent = [a for a in hist if a["step"] >= (c - 1) * CHUNK_STEPS]"""
new2 = """                    lo_step, hi_step = (c - 2) * CHUNK_STEPS, (c - 1) * CHUNK_STEPS
                    recent = [a for a in hist if lo_step <= a["step"] < hi_step]"""
print("gate window:", t.count(old2)); t = t.replace(old2, new2, 1)

p.write_text(t, encoding="utf-8")
print("patched loop timing/gate")
