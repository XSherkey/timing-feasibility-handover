"""Self-test of the round-4 search protocol (no LLM calls, no sweeps).

Checks three things before any expensive run:

1. every new grammar switch builds a policy that forwards and counts parameters;
2. one candidate evaluation runs end-to-end (warm start -> PPO -> deployment score
   -> diagnostics -> search table), and is reproducible with the same seed;
3. the proxy score is in the expected range and the diagnostics are populated.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from almond.nas.evolution import Evolver, Individual, NASConfig
from almond.policies.nets import GraphSpec, build_policy
from almond.twin.env import EnvConfig, HandoverEnv
from almond.twin.twin import DigitalTwin, TwinConfig


def check_forward() -> None:
    twin = DigitalTwin(TwinConfig(tag="ref", horizon_s=2 * 3600)).build(verbose=False)
    env = HandoverEnv(twin, EnvConfig(episode_steps=40), batch=4, seed=0)
    x, adj = env.candidate_graph()
    obs = env.obs()
    specs = [
        GraphSpec(kind="mlp", width=64, layers=2),
        GraphSpec(kind="gcn", width=64, layers=2),
        GraphSpec(kind="gcn", width=64, layers=1, edge_types=1),
        GraphSpec(kind="gcn", width=64, layers=2, head_width=128),
        GraphSpec(kind="att", width=64, layers=2, heads=2, head_width=96),
        GraphSpec(kind="hybrid", width=64, layers=2, heads=2, edge_types=1, head_width=32),
    ]
    print(f"{'spec':<58}{'params':>9}  forward")
    for s in specs:
        pol = build_policy("graph", obs_dim=env.obs_dim, node_dim=x.shape[-1],
                           n_targets=env.K + 1, n_advance=env.n_advance, spec=s)
        lt, la, v = pol(torch.as_tensor(obs, dtype=torch.float32),
                        torch.as_tensor(x, dtype=torch.float32),
                        torch.as_tensor(adj, dtype=torch.float32))
        assert lt.shape == (4, env.K + 1) and la.shape == (4, env.n_advance) and v.shape == (4,)
        assert torch.isfinite(lt).all() and torch.isfinite(v).all()
        print(f"{s.describe():<58}{pol.param_count():>9}  ok")
    # the two switches must actually change the parameter count
    base = build_policy("graph", obs_dim=env.obs_dim, node_dim=x.shape[-1], n_targets=env.K + 1,
                        n_advance=env.n_advance, spec=GraphSpec(kind="gcn", width=64, layers=2)).param_count()
    et = build_policy("graph", obs_dim=env.obs_dim, node_dim=x.shape[-1], n_targets=env.K + 1,
                      n_advance=env.n_advance, spec=GraphSpec(kind="gcn", width=64, layers=2, edge_types=1)).param_count()
    hw = build_policy("graph", obs_dim=env.obs_dim, node_dim=x.shape[-1], n_targets=env.K + 1,
                      n_advance=env.n_advance, spec=GraphSpec(kind="gcn", width=64, layers=2, head_width=128)).param_count()
    print(f"\nedge_types off/on: {base} -> {et}   head_width 0/128: {base} -> {hw}")
    assert et > base and hw != base, "the new switches do not change the model"


def check_evaluate() -> None:
    twin = DigitalTwin(TwinConfig(tag="ref", horizon_s=12 * 3600)).build(verbose=False)

    def env_factory(batch, steps, seed=None):
        return HandoverEnv(twin, EnvConfig(episode_steps=steps), batch=batch, seed=seed or 0)

    cfg = NASConfig(population=2, generations=0, eval_episodes=24, batch=8, episode_steps=120,
                    eval_seeds=2, deploy_episodes=1, bc_episodes=3, bc_epochs=4, seed=0)
    ev = Evolver(None, env_factory, cfg, use_llm=False, weights=dict(w_rel=0.68, w_lat=0.11, w_pow=0.21))
    ev.regime_stats = ev._regime_stats()
    print("\nregime statistics:", ev.regime_stats)
    ind = Individual(spec=GraphSpec(kind="gcn", width=64, layers=2))
    out = ev.evaluate(ind)
    print(f"\nsatisfaction={out.reward:.1f} arctic_hsr={out.hsr_arctic:.3f} "
          f"params={out.params} latency={out.latency_ms:.2f}ms")
    print("diagnostics:", out.diag)
    print("table row:", ev.table[-1])
    assert 0.0 <= out.reward <= 100.0, "satisfaction out of range"
    assert out.diag, "diagnostics missing"
    assert ev.table, "search table not filled"

    # reproducibility: same config, same candidate, fresh evolver
    ev2 = Evolver(None, env_factory, cfg, use_llm=False, weights=dict(w_rel=0.68, w_lat=0.11, w_pow=0.21))
    out2 = ev2.evaluate(Individual(spec=GraphSpec(kind="gcn", width=64, layers=2)))
    print(f"repeat run: satisfaction={out2.reward:.1f} (delta {abs(out2.reward - out.reward):.3f})")
    assert abs(out2.reward - out.reward) < 1e-6, "candidate evaluation is not reproducible"


if __name__ == "__main__":
    check_forward()
    check_evaluate()
    print("\nall self-tests passed")
