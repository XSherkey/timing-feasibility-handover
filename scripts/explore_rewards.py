"""Compare a hand-crafted (SNR-proxy) reward against the audited reward.

This is the decisive calibration/validation step of the reproduction: if the
twin is set up correctly, the hand-crafted multi-objective reward must leave a
polar reliability gap while the audited reward does not.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from almond.policies.nets import GraphSpec, build_policy
from almond.policies.ppo import PPOConfig, PPOTrainer
from almond.twin.env import EnvConfig, HandoverEnv
from almond.twin.twin import DigitalTwin, TwinConfig

REGIONS = {
    "arctic": lambda x: x > 70,
    "65-70": lambda x: 65 <= x <= 70,
    "30-65": lambda x: 30 <= x < 65,
    "<30": lambda x: x < 30,
}


def eval_policy(trainer, env, episodes=3, t_range=None, shield=None):
    rows = []
    for _ in range(episodes):
        obs = env.reset(t_range=t_range)
        for _s in range(env.cfg.episode_steps):
            x, adj = env.candidate_graph()
            at, aa, _lp, _v = trainer._act(obs, x, adj, deterministic=True, mask=trainer.action_mask(env))
            obs, rew, done, info = env.step(at, aa, shield=shield)
        st = env.episode_stats()
        lat = env.site_lat[env.site]
        for i in range(env.batch):
            rows.append(
                dict(lat=float(lat[i]), hsr=float(st["hsr"][i]), attempts=int(st["attempts"][i]),
                     successes=int(st["successes"][i]))
            )
    return rows


def summarise(rows):
    out = {}
    for name, f in REGIONS.items():
        sel = [r for r in rows if f(abs(r["lat"]))]
        att = sum(r["attempts"] for r in sel)
        suc = sum(r["successes"] for r in sel)
        out[name] = (suc / att * 100) if att else float("nan")
    att = sum(r["attempts"] for r in rows)
    suc = sum(r["successes"] for r in rows)
    out["ALL"] = (suc / att * 100) if att else float("nan")
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", default="probe")
    ap.add_argument("--hours", type=float, default=1.5)
    ap.add_argument("--episodes", type=int, default=400)
    ap.add_argument("--batch", type=int, default=32)
    ap.add_argument("--steps", type=int, default=240)
    ap.add_argument("--device", default="cuda")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--modes", default="handcrafted,audited")
    args = ap.parse_args()

    twin = DigitalTwin(TwinConfig(horizon_s=args.hours * 3600, tag=args.tag)).build(verbose=False)
    print(f"twin: {twin.n_sat} sats, {twin.n_time} steps")
    hdr = f"{'mode':<14}" + "".join(f"{k:>9}" for k in list(REGIONS) + ["ALL"])
    print(hdr)
    results = {}
    for mode in args.modes.split(","):
        handcrafted = mode == "handcrafted"
        ecfg = EnvConfig(
            episode_steps=args.steps,
            w_rel=0.4 if handcrafted else 0.8,
            w_lat=0.4 if handcrafted else 0.12,
            w_pow=0.2 if handcrafted else 0.08,
            use_snr_proxy=handcrafted,
            drop_penalty=0.0 if handcrafted else 0.30,
        )
        env = HandoverEnv(twin, ecfg, batch=args.batch, seed=args.seed)
        x, adj = env.candidate_graph()
        spec = GraphSpec(kind="gcn", width=64, layers=2, heads=2, pool="mean")
        pol = build_policy("graph", obs_dim=env.obs_dim, node_dim=x.shape[-1],
                           n_targets=env.K + 1, n_advance=env.n_advance, spec=spec)
        pcfg = PPOConfig(total_episodes=args.episodes, rollout_steps=512, minibatch=256,
                         epochs=4, lr=3e-4, device=args.device, seed=args.seed,
                         early_stop_patience=10**9)
        tr = PPOTrainer(env, pol, pcfg)
        t0 = time.time()
        res = tr.train(log_every=0)
        rows = eval_policy(tr, env, episodes=4)
        s = summarise(rows)
        print(f"{mode:<14}" + "".join(f"{s[k]:9.1f}" for k in list(REGIONS) + ["ALL"]) +
              f"   ({res['episodes']} ep, {time.time()-t0:.0f}s, {pol.param_count()} params)")
        results[mode] = dict(summary=s, episodes=res["episodes"], params=pol.param_count())
    out = Path("results") / f"reward_compare_{args.tag}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print("wrote", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
