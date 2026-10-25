from pathlib import Path
p = Path(r"D:\almond-repro\almond\nas\evolution.py")
s = p.read_text(encoding="utf-8")
old = """        spec = self._project_to_budget(ind.spec, env, x)
        ind.spec = spec
        policy = build_policy("""
new = """        spec = self._project_to_budget(ind.spec, env, x)
        ind.spec = spec
        # seed per (search seed, evaluation index) so a re-run of the same search
        # reproduces the same proxy rewards instead of depending on global state
        import random as _random

        import torch as _torch

        _seed = int(self.cfg.seed) * 100003 + self.eval_count
        _random.seed(_seed)
        np.random.seed(_seed)
        _torch.manual_seed(_seed)
        policy = build_policy("""
assert old in s
s = s.replace(old, new, 1)
p.write_text(s, encoding="utf-8")
print("evolver evaluation seeding added")
