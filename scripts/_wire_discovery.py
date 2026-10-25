from pathlib import Path
p = Path(r"D:\almond-repro\almond\framework\system.py")
s = p.read_text(encoding="utf-8")

# 1) new config knob: which discovery-set construction the forensic loop uses
old = "    max_forensic_rounds: int = 1"
new = "    max_forensic_rounds: int = 1\n    discovery_mode: str = \"enriched\"  # \"legacy\" reproduces the pre-enrichment sampling"
assert old in s
s = s.replace(old, new, 1)

# 2) pass it through to the engine
old = """        res = fe.run(
            max_attempts=1,
            validate_episodes=cfg.validate_episodes,
            test_episodes=cfg.test_episodes,
        )"""
new = """        res = fe.run(
            max_attempts=1,
            validate_episodes=cfg.validate_episodes,
            test_episodes=cfg.test_episodes,
            discovery_mode=cfg.discovery_mode,
        )"""
assert old in s
s = s.replace(old, new, 1)

# 3) record the discovery-set composition with the result
old = """            n_candidates=res.n_candidates,
            stages=res.stage_log,
        )"""
new = """            n_candidates=res.n_candidates,
            discovery_mode=cfg.discovery_mode,
            discovery=next((e for e in res.stage_log if e.get("event") == "discovery"), None),
            stages=res.stage_log,
        )"""
assert old in s
s = s.replace(old, new, 1)
p.write_text(s, encoding="utf-8")
print("system: discovery_mode wired")
