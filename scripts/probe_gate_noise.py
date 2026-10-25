"""How reliable is the counterfactual gate?

The gate admits a candidate only if the replay improvement clears a threshold.  That
replay is a short, random draw, so the *decision* inherits the sampling noise.  This
script measures the distribution of the measured improvement for one fixed rule as a
function of the number of replay episodes and of the environment seed.

Usage
-----
    python scripts/probe_gate_noise.py --run results/campaign_1023/almond_seed0
    python scripts/probe_gate_noise.py --run ... --episodes 2,4,8,16 --seeds 5
"""
from __future__ import annotations

import argparse
import json
import statistics as st
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from almond.framework.forensics import SplitConfig, replay_rule, score  # noqa: E402
from almond.framework.kg import Constraint  # noqa: E402
from almond.policies.nets import GraphSpec, build_policy  # noqa: E402
from almond.policies.ppo import PPOConfig, PPOTrainer  # noqa: E402
from almond.twin.env import EnvConfig, HandoverEnv  # noqa: E402
from almond.twin.twin import DigitalTwin, TwinConfig  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True)
    ap.add_argument("--twin", default="ref")
    ap.add_argument("--hours", type=float, default=12.0)
    ap.add_argument("--batch", type=int, default=24)  # the engine's batch
    ap.add_argument("--steps", type=int, default=240)
    ap.add_argument("--episodes", default="2,4,8,16")
    ap.add_argument("--seeds", type=int, default=5)
    ap.add_argument("--tau", type=float, default=16.0)
    ap.add_argument("--lat", type=float, default=68.0)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    import torch

    ck = torch.load(Path(args.run) / "policy.pt", map_location="cpu", weights_only=False)
    weights = ck.get("weights") or dict(w_rel=0.7, w_lat=0.1, w_pow=0.2)
    twin = DigitalTwin(TwinConfig(tag=args.twin, horizon_s=args.hours * 3600)).build(verbose=False)

    rule = Constraint(
        id="mined", version=1,
        atoms=[{"field": "latitude_abs_deg", "cmp": ">=", "value": args.lat},
               {"field": "handover_advance_s", "cmp": "<=", "value": args.tau}],
        effect="min_advance", magnitude=args.tau, nl_reading="mined", provenance={},
        confidence=1.0, scope_tags={},
    )

    env_cfg = EnvConfig(episode_steps=args.steps, w_rel=weights["w_rel"],
                        w_lat=weights["w_lat"], w_pow=weights["w_pow"],
                        drop_penalty=0.30, switch_penalty=0.10)
    env = HandoverEnv(twin, env_cfg, batch=args.batch, seed=0)
    x0, _ = env.candidate_graph()
    policy = build_policy("graph", obs_dim=env.obs_dim, node_dim=x0.shape[-1],
                          n_targets=env.K + 1, n_advance=env.n_advance,
                          spec=GraphSpec.from_dict(ck["spec"]))
    policy.load_state_dict(ck["policy"])
    trainer = PPOTrainer(env, policy, PPOConfig(device="cpu", seed=0, deterministic=True))
    if trainer.obs_norm is not None and ck.get("obs_norm"):
        trainer.obs_norm.load_state_dict(ck["obs_norm"])

    def policy_fn(obs, x, adj, deterministic=True):
        at, aa, _lp, _v = trainer._act(obs, x, adj, deterministic=deterministic)
        return at, aa

    splits = SplitConfig()
    test = splits.indices(twin.n_time, "test", args.steps)
    eps_list = [int(e) for e in args.episodes.split(",") if e.strip()]

    print(f"policy {Path(args.run).name}, rule min_advance {args.tau}s @ lat>={args.lat}")
    print(f"{'episodes':>9}{'env seeds':>11}{'mean d_test':>13}{'sd':>8}{'min':>8}{'max':>8}{'P(d<0)':>9}")
    out = []
    for eps in eps_list:
        deltas = []
        for k in range(args.seeds):
            env.rng = np.random.default_rng(17 + 1000 * k)  # engine uses cfg.seed+17
            env.reset()
            base = replay_rule(env, policy_fn, None, eps, test)
            with_c = replay_rule(env, policy_fn, rule, eps, test)
            bt = score(base["rows"], "arctic")["hsr"]
            ht = score(with_c["rows"], "arctic")["hsr"]
            deltas.append(ht - bt)
        d = np.array(deltas) * 100
        print(f"{eps:>9}{args.seeds:>11}{d.mean():>+12.1f}{d.std(ddof=1) if len(d) > 1 else 0:>8.1f}"
              f"{d.min():>+8.1f}{d.max():>+8.1f}{(d < 0).mean():>8.0%}")
        out.append(dict(episodes=eps, mean=float(d.mean()),
                        sd=float(d.std(ddof=1)) if len(d) > 1 else 0.0,
                        min=float(d.min()), max=float(d.max()),
                        p_negative=float((d < 0).mean())))
    if args.out:
        json.dump(out, open(args.out, "w", encoding="utf-8"), indent=2)
        print("wrote", args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
