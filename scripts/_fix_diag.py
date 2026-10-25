from pathlib import Path
p = Path(r"D:\almond-repro\scripts\diagnose_run.py")
s = p.read_text(encoding="utf-8")
s = s.replace("""    obs_norm = blob.get("obs_norm")""",
"""    _on = blob.get("obs_norm")
    obs_norm = None
    if _on:
        from almond.policies.ppo import RunningNorm
        obs_norm = RunningNorm(len(_on["mean"]))
        obs_norm.load_state_dict(_on)""")
p.write_text(s, encoding="utf-8")
print("patched")
