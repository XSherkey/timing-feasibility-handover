"""Fix the policy construction in the two new experiment scripts (match eval_shield exactly)."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

PATCH = {
    "experiments/run_window_case2.py": [
        ('    pol = build_policy(GraphSpec.from_dict(ck["spec"]), seed=0)\n    pol.load_state_dict(ck["state_dict"])',
         '    x0, adj0 = env.candidate_graph()\n'
         '    pol = build_policy("graph", obs_dim=env.obs_dim, node_dim=x0.shape[-1],\n'
         '                       n_targets=env.K + 1, n_advance=env.n_advance,\n'
         '                       spec=GraphSpec.from_dict(ck["spec"]))\n'
         '    pol.load_state_dict(ck["policy"])'),
    ],
    "experiments/run_closed_loop.py": [
        ('    pol = build_policy(GraphSpec.from_dict(ck["spec"]), seed=policy_seed)\n    pol.load_state_dict(ck["state_dict"])',
         '    x0, adj0 = env.candidate_graph()\n'
         '    pol = build_policy("graph", obs_dim=env.obs_dim, node_dim=x0.shape[-1],\n'
         '                       n_targets=env.K + 1, n_advance=env.n_advance,\n'
         '                       spec=GraphSpec.from_dict(ck["spec"]))\n'
         '    pol.load_state_dict(ck["policy"])'),
    ],
}

for rel, subs in PATCH.items():
    p = ROOT / rel
    t = p.read_text(encoding="utf-8")
    for old, new in subs:
        n = t.count(old)
        print(rel, "->", n)
        if n == 1:
            t = t.replace(old, new, 1)
    p.write_text(t, encoding="utf-8")
print("patched")
