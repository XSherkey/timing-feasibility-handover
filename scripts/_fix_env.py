from pathlib import Path
p = Path(r"D:\almond-repro\almond\twin\handover_env.py")
s = p.read_text(encoding="utf-8")
s = s.replace("RECONNECT_STEPS = 3", "RECONNECT_STEPS = 6")
# the outage flag must not silently clear `session` anywhere else either
assert "self.offline > 0, False, self.session" not in s, "another session-clamp remains"
p.write_text(s, encoding="utf-8")
print("RECONNECT_STEPS -> 6; no session clamp remains")
