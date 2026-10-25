"""Use the PPO trainer's deterministic action API in both new experiment scripts."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

PATCH = {
    "experiments/run_window_case2.py": [
        ('    at, aa = pol.act(env.obs(), x, adj)',
         '    at, aa, _lp, _v = trainer._act(env.obs(), x, adj, deterministic=True)'),
        ('    x0, adj0 = env.candidate_graph()\n',
         '    x0, adj0 = env.candidate_graph()\n'
         '    from almond.policies.ppo import PPOConfig, PPOTrainer\n'
         '    trainer = PPOTrainer(pol, PPOConfig(device="cpu", seed=0, deterministic=True))\n'),
    ],
    "experiments/run_closed_loop.py": [
        ('                at, aa = pol.act(env.obs(), x, adj)',
         '                at, aa, _lp, _v = trainer._act(env.obs(), x, adj, deterministic=True)'),
        ('    x0, adj0 = env.candidate_graph()\n',
         '    x0, adj0 = env.candidate_graph()\n'
         '    from almond.policies.ppo import PPOConfig, PPOTrainer\n'
         '    trainer = PPOTrainer(pol, PPOConfig(device="cpu", seed=policy_seed, deterministic=True))\n'),
    ],
}

for rel, subs in PATCH.items():
    p = ROOT / rel
    t = p.read_text(encoding="utf-8")
    for old, new in subs:
        n = t.count(old)
        print(rel, repr(old[:40]), "->", n)
        if n >= 1:
            t = t.replace(old, new, 1)
    p.write_text(t, encoding="utf-8")
print("patched action API")
