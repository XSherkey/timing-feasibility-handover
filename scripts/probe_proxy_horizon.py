"""Which proxy horizon becomes predictive?  (follow-up to probe_proxy_fidelity)

The first probe showed that variance control and the deployment-facing metric are
necessary but not sufficient: with 24 proxy episodes rho(proxy, deployment) was
still ~0.2, because deployment is dominated by what happens over 9,600 episodes
of PPO *after* the warm start, and a 24-episode proxy cannot see that.

This script re-scores the same twelve architectures at several training horizons
(240 / 960 / 2400 / 4800 instance-episodes) and reports the rank correlation with
the deployment results already measured, so the search can use the cheapest
horizon that is actually predictive.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from almond.nas.evolution import Evolver, NASConfig
from almond.policies.nets import GraphSpec, build_policy
from almond.policies.ppo import PPOConfig, PPOTrainer
from almond.twin.env import EnvConfig, HandoverEnv
from almond.twin.twin import DigitalTwin, TwinConfig

WEIGHTS = dict(w_rel=0.68, w_lat=0.11, w_pow=0.21)


def spearman(a, b) -> float:
    a = np.asarray(a, float)
    b = np.asarray(b, float)
    if np.allclose(a, a[0]) or np.allclose(b, b[0]):
        return float("nan")
    ra = np.argsort(np.argsort(a)).astype(float)
    rb = np.argsort(np.argsort(b)).astype(float)
    return float(np.corrcoef(ra, rb)[0, 1])


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--probe", default="results/nas/proxy_fidelity.json")
    ap.add_argument("--horizons", default="240,960,2400,4800")
    ap.add_argument("--out", default="results/nas/proxy_horizon.json")
    args = ap.parse_args()

    probe = json.loads((ROOT / args.probe).read_text(encoding="utf-8"))
    rows = probe["rows"]
    deploy = [r["deploy_satisfaction"] for r in rows]
    print(f"{len(rows)} architectures, deployment satisfaction "
          f"{min(deploy):.1f} .. {max(deploy):.1f}\n")

    twin = DigitalTwin(TwinConfig(tag="ref", horizon_s=12 * 3600)).build(verbose=False)

    def env_factory(batch, steps, seed=None):
        return HandoverEnv(twin, EnvConfig(episode_steps=steps, w_rel=WEIGHTS["w_rel"],
                                           w_lat=WEIGHTS["w_lat"], w_pow=WEIGHTS["w_pow"]),
                           batch=batch, seed=seed or 0)

    base = NASConfig(population=2, generations=0, batch=8, episode_steps=240,
                     eval_seeds=2, deploy_episodes=2, bc_episodes=6, bc_epochs=12, seed=0)
    ev = Evolver(None, env_factory, base, use_llm=False, weights=WEIGHTS)

    horizons = [int(h) for h in args.horizons.split(",")]
    results: dict[str, dict] = {}
    for N in horizons:
        scores = []
        t0 = time.time()
        for r in rows:
            spec = GraphSpec.from_dict(r["spec_dict"])
            env = env_factory(8, 240, seed=1)
            x, adj = env.candidate_graph()
            import random as _random

            import torch as _torch

            s = 7
            _random.seed(s)
            np.random.seed(s)
            _torch.manual_seed(s)
            pol = build_policy("graph", obs_dim=env.obs_dim, node_dim=x.shape[-1],
                               n_targets=env.K + 1, n_advance=env.n_advance, spec=spec)
            pcfg = PPOConfig(total_episodes=N, rollout_steps=64, minibatch=64, epochs=2, lr=1e-3,
                             device="cpu", early_stop_patience=10**9,
                             bc_episodes=base.bc_episodes, bc_epochs=base.bc_epochs, seed=s)
            tr = PPOTrainer(env, pol, pcfg, norm_obs=True, norm_reward=True)
            tr.warm_start()
            tr.train(log_every=0)
            sc = ev._deploy_score(tr)
            scores.append(float(sc["S"]))
        rho = spearman(scores, deploy)
        results[str(N)] = dict(scores=scores, rho=rho, seconds=round(time.time() - t0, 1))
        print(f"horizon {N:5d}: rho = {rho:+.2f}   "
              f"scores {min(scores):.1f}..{max(scores):.1f}   ({results[str(N)]['seconds']:.0f}s)",
              flush=True)

    print("\nper-architecture detail:")
    print(f"{'spec':<52}{'deploy':>8}" + "".join(f"{('h=' + str(N)):>9}" for N in horizons))
    for i, r in enumerate(rows):
        line = f"{r['spec'][:50]:<52}{deploy[i]:>8.1f}"
        for N in horizons:
            line += f"{results[str(N)]['scores'][i]:>9.1f}"
        print(line)

    out = dict(rows=rows, deploy=deploy, horizons=results,
               note="rho is Spearman correlation of each proxy horizon with deployment satisfaction")
    p = ROOT / args.out
    p.write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    print("\nwrote", p.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
