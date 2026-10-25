"""F4: how many probe episodes does the calibrated threshold need?

The probe estimate tau* comes from a forced-advance sweep.  This script measures
its sampling stability as a function of the number of episodes per advance, using
the same isotonic estimator the in-loop PCS uses (AlmondSystem._isotonic_tau).

Acceptance (plan §6): the standard deviation of tau* must reach <= 1 s, and the
smallest episode count that achieves it is the one to use by default.

Usage
-----
    python scripts/_routeA_f4.py --run results/campaign_1023/almond_seed0
    python scripts/_routeA_f4.py --run ... --episodes 2,4,8,16 --repeats 5
"""
from __future__ import annotations

import argparse
import json
import statistics as st
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from almond.framework.system import AlmondSystem  # noqa: E402
from almond.policies.nets import GraphSpec, build_policy  # noqa: E402
from almond.policies.ppo import PPOConfig, PPOTrainer  # noqa: E402
from almond.twin.env import EnvConfig, HandoverEnv  # noqa: E402
from almond.twin.twin import DigitalTwin, TwinConfig  # noqa: E402

LOG = ROOT / "results" / "routeA" / "commands.log"
ADV = (6, 8, 10, 12, 14, 16, 18, 20, 22, 24, 26)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True)
    ap.add_argument("--episodes", default="2,4,8,16")
    ap.add_argument("--repeats", type=int, default=5)
    ap.add_argument("--eps", type=float, default=0.05)
    ap.add_argument("--lat", type=float, default=70.0)
    ap.add_argument("--steps", type=int, default=240)
    ap.add_argument("--batch", type=int, default=32)
    ap.add_argument("--out", default="results/routeA/f4_probe_convergence.json")
    args = ap.parse_args()

    with LOG.open("a", encoding="utf-8") as fh:
        fh.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] [F4] {' '.join(sys.argv)}\n")

    import torch

    ck = torch.load(Path(args.run) / "policy.pt", map_location="cpu", weights_only=False)
    weights = ck.get("weights") or dict(w_rel=0.7, w_lat=0.1, w_pow=0.2)
    twin = DigitalTwin(TwinConfig(horizon_s=12 * 3600)).build(verbose=False)
    env = HandoverEnv(twin, EnvConfig(episode_steps=args.steps, w_rel=weights["w_rel"],
                                      w_lat=weights["w_lat"], w_pow=weights["w_pow"],
                                      drop_penalty=0.30, switch_penalty=0.10),
                      batch=args.batch, seed=0)
    x0, _ = env.candidate_graph()
    policy = build_policy("graph", obs_dim=env.obs_dim, node_dim=x0.shape[-1],
                          n_targets=env.K + 1, n_advance=env.n_advance,
                          spec=GraphSpec.from_dict(ck["spec"]))
    policy.load_state_dict(ck["policy"])
    trainer = PPOTrainer(env, policy, PPOConfig(device="cpu", seed=0, deterministic=True))
    if trainer.obs_norm is not None and ck.get("obs_norm"):
        trainer.obs_norm.load_state_dict(ck["obs_norm"])

    from almond.framework.forensics import SplitConfig

    trange = SplitConfig().indices(twin.n_time, "test", args.steps)

    def probe(n_episodes: int, rng_seed: int) -> float:
        xs, ys = [], []
        for a in ADV:
            b = int(np.clip(round((a - env.cfg.a_min_s) / env.cfg.a_step_s), 0, env.cfg.a_max_bucket))
            env.rng = np.random.default_rng(rng_seed)
            for _ in range(n_episodes):
                env.reset(t_range=trange)
                for _s in range(env.cfg.episode_steps):
                    x, adj = env.candidate_graph()
                    at, _aa, _lp, _v = trainer._act(env.obs(), x, adj, deterministic=True)
                    env.step(at, np.full(env.batch, b, dtype=np.int64), record=True)
            for att in env.attempt_log:
                if abs(att["latitude_abs_deg"]) >= args.lat:
                    late = att["cause"] == "late_handover"
                    xs.append(float(a))
                    ys.append(1.0 if late else 0.0)
        return float(AlmondSystem._isotonic_tau(np.asarray(xs), np.asarray(ys), args.eps))

    rows = []
    for n in [int(e) for e in args.episodes.split(",") if e.strip()]:
        taus = [probe(n, 1000 + 17 * k) for k in range(args.repeats)]
        rows.append(dict(episodes=n, taus=taus, mean=st.mean(taus),
                         sd=st.stdev(taus) if len(taus) > 1 else 0.0))
        print(f"episodes/advance={n:>3}  tau* = {[round(t, 1) for t in taus]}  "
              f"mean {st.mean(taus):.1f}  sd {rows[-1]['sd']:.2f}", flush=True)

    ok = [r for r in rows if r["sd"] <= 1.0]
    best = min(ok, key=lambda r: r["episodes"]) if ok else None
    print(f"\nminimum episodes with sd <= 1 s: {best['episodes'] if best else 'none in range'}")
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(dict(run=args.run, rows=rows,
                                              min_episodes=best["episodes"] if best else None), indent=2),
                              encoding="utf-8")
    print("wrote", args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
