from pathlib import Path

p = Path(__file__).resolve().parents[1] / "experiments" / "run_closed_loop.py"
t = p.read_text(encoding="utf-8")
old = """                vals = rng.choice(GRID, size=int(pick.sum()))
                buckets = np.rint(np.clip((vals - env.cfg.a_min_s) / env.cfg.a_step_s,
                                          0, env.cfg.a_max_bucket)).astype(np.int64)
                aa = np.where(pick, buckets, aa)"""
new = """                vals = rng.choice(GRID, size=int(pick.sum()))
                buckets = np.rint(np.clip((vals - env.cfg.a_min_s) / env.cfg.a_step_s,
                                          0, env.cfg.a_max_bucket)).astype(np.int64)
                aa = aa.copy()
                aa[pick] = buckets"""
print("found:", t.count(old))
t = t.replace(old, new, 1)
p.write_text(t, encoding="utf-8")
print("patched probe assignment")
