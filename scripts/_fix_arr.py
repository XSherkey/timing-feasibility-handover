from pathlib import Path
p = Path(r"D:\almond-repro\almond\twin\handover_env.py")
s = p.read_text(encoding="utf-8")
s = s.replace("session_arrival_per_min: float = 0.09", "session_arrival_per_min: float = 0.18")
p.write_text(s, encoding="utf-8")
print("session arrival 0.09 -> 0.18 /min (service duty ~60%)")
