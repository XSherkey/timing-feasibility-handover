"""Does the search proxy predict deployment?  (the experiment that gates everything)

Twelve architectures across the grammar are evaluated three ways in one process:

* ``P0`` - the pre-fix proxy: 24 episodes from scratch, a private init seed per
  candidate, mean episode return;
* ``P2`` - the fixed proxy: common init seed, behaviour-cloning warm start,
  satisfaction on the validation split, averaged over two env seeds;
* ``deploy`` - the full deployment pipeline (9,600 episodes, same intent weights,
  no forensic loop so that architecture is the only difference).

The output answers the only question that matters before rebuilding the search:
how well does each proxy rank architectures relative to deployment quality.
"""
from __future__ import annotations

import argparse
import json
import random
import sys
import time
from pathlib import Path

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from almond.framework.system import AlmondConfig, AlmondSystem
from almond.nas.evolution import Evolver, Individual, NASConfig
from almond.policies.nets import GraphSpec, build_policy
from almond.policies.ppo import PPOConfig, PPOTrainer
from almond.twin.env import EnvConfig, HandoverEnv
from almond.twin.twin import DigitalTwin, TwinConfig

WEIGHTS = dict(w_rel=0.68, w_lat=0.11, w_pow=0.21)


def spec_ladder() -> list[GraphSpec]:
    """Twelve architectures spanning family, size and the two new switches."""
    return [
        GraphSpec(kind="gcn", width=32, layers=1),
        GraphSpec(kind="gcn", width=64, layers=2),
        GraphSpec(kind="gcn", width=64, layers=2, edge_types=1),
        GraphSpec(kind="gcn", width=64, layers=3),
        GraphSpec(kind="gcn", width=128, layers=2),
        GraphSpec(kind="mlp", width=64, layers=2),
        GraphSpec(kind="mlp", width=128, layers=3),
        GraphSpec(kind="att", width=64, layers=2, heads=2),
        GraphSpec(kind="att", width=64, layers=2, heads=2, head_width=128),
        GraphSpec(kind="hybrid", width=64, layers=2, heads=2),
        GraphSpec(kind="hybrid", width=64, layers=2, heads=2, edge_types=1),
        GraphSpec(kind="gcn", width=96, layers=2, head_width=32, edge_types=1),
    ]


def spearman(a: list[float], b: list[float]) -> float:
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    if np.allclose(a, a[0]) or np.allclose(b, b[0]):
        return float("nan")
    ra = np.argsort(np.argsort(a)).astype(float)
    rb = np.argsort(np.argsort(b)).astype(float)
    return float(np.corrcoef(ra, rb)[0, 1])


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="results/nas/proxy_fidelity.json")
    ap.add_argument("--episodes", type=int, default=9600)
    ap.add_argument("--limit", type=int, default=12)
    args = ap.parse_args()

    twin = DigitalTwin(TwinConfig(tag="ref", horizon_s=12 * 3600)).build(verbose=False)

    def env_factory(batch, steps, seed=None):
        return HandoverEnv(twin, EnvConfig(episode_steps=steps, w_rel=WEIGHTS["w_rel"],
                                           w_lat=WEIGHTS["w_lat"], w_pow=WEIGHTS["w_pow"]),
                           batch=batch, seed=seed or 0)

    # P2 machinery: the fixed protocol, exactly as the search uses it
    cfg = NASConfig(population=2, generations=0, eval_episodes=24, batch=8, episode_steps=240,
                    eval_seeds=2, deploy_episodes=1, bc_episodes=4, bc_epochs=8, seed=0)
    ev = Evolver(None, env_factory, cfg, use_llm=False, weights=WEIGHTS)
    ev.regime_stats = ev._regime_stats()

    def p0_score(spec: GraphSpec, idx: int) -> float:
        """Pre-fix proxy: from scratch, private init seed, mean episode return."""
        env = env_factory(8, 160, seed=0)
        x, adj = env.candidate_graph()
        s = idx + 1
        random.seed(s)
        np.random.seed(s)
        torch.manual_seed(s)
        pol = build_policy("graph", obs_dim=env.obs_dim, node_dim=x.shape[-1],
                           n_targets=env.K + 1, n_advance=env.n_advance, spec=spec)
        pcfg = PPOConfig(total_episodes=24, rollout_steps=64, minibatch=64, epochs=2, lr=1e-3,
                         device="cpu", early_stop_patience=10**9, bc_episodes=0,
                         deterministic=True, seed=s)
        tr = PPOTrainer(env, pol, pcfg, norm_obs=True, norm_reward=True)
        res = tr.train(log_every=0)
        return float(np.mean([m["ret"] for m in res["ep_metrics"]] or [-1.0]))

    specs = spec_ladder()[: args.limit]
    rows = []
    for i, spec in enumerate(specs):
        t0 = time.time()
        p0 = p0_score(spec, i)
        t1 = time.time()
        ind = ev.evaluate(Individual(spec=spec))
        t2 = time.time()
        # deployment: the real pipeline, forensic loop off so architecture is the
        # only variable
        cfg_dep = AlmondConfig(variant="no_forensics", seed=0, episodes=args.episodes,
                               eval_every=1200, device="cpu", fixed_spec=spec.to_dict(),
                               out_dir=str(ROOT / "results" / "_probe" / f"spec{i}"))
        sys_dep = AlmondSystem(cfg_dep, out_dir=cfg_dep.out_dir)
        res = sys_dep.run()
        t3 = time.time()
        rows.append(
            dict(
                index=i,
                spec=spec.describe(),
                spec_dict=spec.to_dict(),
                params=int(ind.params),
                p0=round(p0, 4),
                p2=round(float(ind.reward), 2),
                p2_arctic=round(float(ind.hsr_arctic) * 100, 1),
                deploy_satisfaction=round(float(res["final"]["satisfaction"]), 2),
                deploy_arctic=round(float(res["final"]["arctic"]["hsr"]) * 100, 1),
                diag=ind.diag,
                seconds=dict(p0=round(t1 - t0, 1), p2=round(t2 - t1, 1), deploy=round(t3 - t2, 1)),
            )
        )
        print(f"[{i:2d}] {spec.describe():<52} P0={p0:6.3f} P2={ind.reward:5.1f} "
              f"deploy S={res['final']['satisfaction']:5.1f} arctic={res['final']['arctic']['hsr'] * 100:5.1f}% "
              f"({t3 - t0:.0f}s)", flush=True)

    rho0 = spearman([r["p0"] for r in rows], [r["deploy_satisfaction"] for r in rows])
    rho2 = spearman([r["p2"] for r in rows], [r["deploy_satisfaction"] for r in rows])
    rho2a = spearman([r["p2_arctic"] for r in rows], [r["deploy_arctic"] for r in rows])
    out = dict(weights=WEIGHTS, protocol=cfg.__dict__, rows=rows,
               rho_p0_vs_deploy=rho0, rho_p2_vs_deploy=rho2, rho_p2arctic_vs_deployarctic=rho2a)
    p = ROOT / args.out
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")

    print("\nrank correlation with deployment satisfaction:")
    print(f"  P0 (old proxy)   rho = {rho0:+.2f}")
    print(f"  P2 (fixed proxy) rho = {rho2:+.2f}")
    print(f"  P2 arctic HSR vs deployed arctic HSR: rho = {rho2a:+.2f}")
    print("wrote", p.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
