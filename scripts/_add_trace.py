from pathlib import Path
p = Path(r"D:\almond-repro\almond\nas\evolution.py")
s = p.read_text(encoding="utf-8")

# a per-evaluation trace so the search can be compared "anytime", not only at
# generation boundaries
old = """        self.eval_count += 1
        self.gpu_s += ind.gpu_s
        return ind"""
new = """        self.eval_count += 1
        self.gpu_s += ind.gpu_s
        # anytime trace: best-so-far reward and hypervolume after every evaluation
        self.trace.append(
            dict(
                evals=self.eval_count,
                gpu_s=float(self.gpu_s),
                reward=float(ind.reward),
                params=int(ind.params),
                best_reward=float(
                    max(
                        (q.reward for q in self.population + [ind]
                         if q.feasible(self.cfg.param_budget, self.cfg.latency_budget_ms)),
                        default=ind.reward,
                    )
                ),
            )
        )
        return ind"""
assert old in s
s = s.replace(old, new, 1)

old = "        self.history: list[dict] = []"
new = "        self.history: list[dict] = []\n        self.trace: list[dict] = []"
assert old in s
s = s.replace(old, new, 1)

old = """            history=self.history,
            critiques=self.critiques,"""
new = """            history=self.history,
            trace=self.trace,
            critiques=self.critiques,"""
assert old in s
s = s.replace(old, new, 1)
p.write_text(s, encoding="utf-8")
print("per-evaluation trace added")
