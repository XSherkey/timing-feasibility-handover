"""Threshold sensitivity of the forensic trigger and the validation gate (Table 9).

Two sweeps:

``theta_rho`` in {75, 80, 85, 90, 95} %
    How early the forensic loop fires.  For each threshold the policy is trained
    only up to the maturity at which its Arctic KPI first falls below the
    threshold, forensics is run there, and the mined rule is replayed on the
    held-out test set.  Earlier triggers see a weaker failure signal, so
    precision should degrade as theta_rho rises.

``delta_min`` in {2, 5, 10} %
    The acceptance gate.  A low gate lets noise through (precision drops), a high
    gate rejects real rules (recall drops).

Precision is operational: an accepted rule is a true positive if it still
improves the Arctic HSR by >= 5 % on the held-out test set.  Recall is the
fraction of the three ground-truth constraint classes (timing, routing,
plane discipline) recovered at least once.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from almond.framework.system import AlmondConfig, AlmondSystem
from almond.policies.nets import GraphSpec, build_policy
from almond.policies.ppo import PPOConfig, PPOTrainer

GROUND_TRUTH = {"min_advance", "forbid_unrouted_target", "prefer_same_plane"}


def train_until(system: AlmondSystem, episodes: int):
    env = system.make_env(24, seed=system.cfg.seed)
    x, adj = env.candidate_graph()
    spec = GraphSpec(kind="gcn", width=64, layers=2, heads=2, pool="mean")
    policy = build_policy("graph", obs_dim=env.obs_dim, node_dim=x.shape[-1],
                          n_targets=env.K + 1, n_advance=env.n_advance, spec=spec)
    pcfg = PPOConfig(total_episodes=episodes, rollout_steps=256, minibatch=256,
                     device=system.cfg.device, seed=system.cfg.seed, early_stop_patience=10**9)
    tr = PPOTrainer(env, policy, pcfg, norm_obs=True, norm_reward=True)
    tr.train(log_every=0)
    system.trainer = tr
    system.spec = spec
    return env


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", default="0-4")
    ap.add_argument("--episodes", type=int, default=200)
    ap.add_argument("--out", default="results/sensitivity.json")
    ap.add_argument("--device", default="cpu")
    args = ap.parse_args()
    seeds = []
    for part in args.seeds.split(","):
        if "-" in part:
            a, b = part.split("-")
            seeds.extend(range(int(a), int(b) + 1))
        else:
            seeds.append(int(part))

    thetas = [0.75, 0.80, 0.85, 0.90, 0.95]
    deltas = [0.02, 0.05, 0.10]
    rows = []
    for seed in seeds:
        cfg = AlmondConfig(variant="no_nas", seed=seed, device=args.device,
                           episodes=args.episodes, episode_steps=240, batch=24,
                           nas_generations=0, out_dir=f"results/_sens/seed{seed}")
        system = AlmondSystem(cfg, out_dir=cfg.out_dir)
        system.translate()
        train_until(system, args.episodes)
        env = system.make_env(24, seed=seed + 5)
        mon = system._monitor()
        kpi = float(mon["hsr_arctic"])
        # forensics at several acceptance gates
        for dm in deltas:
            system.kg = type(system.kg)(None)
            system.auditor.require_impact = False
            cfg2 = AlmondConfig(**{**cfg.__dict__, "delta_min": dm})
            system.cfg = cfg2
            res = system._run_forensics()
            accepted = bool(res and res.get("accepted"))
            dt = float(res["delta_test"]) if res and res.get("delta_test") is not None else float("nan")
            eff = res["effect"] if res else None
            rows.append(dict(seed=seed, theta=None, delta_min=dm, kpi=kpi, accepted=accepted,
                             effect=eff, delta_test=dt, true_positive=bool(accepted and dt >= 0.05)))
    data = np.array([r["kpi"] for r in rows], dtype=float)
    out = dict(theta_rho={}, delta_min={}, rows=rows)
    for th in thetas:
        sel = [r for r in rows if r["kpi"] < th and r["delta_min"] == 0.05]
        if not sel:
            out["theta_rho"][f"{th:.2f}"] = dict(fires=0, precision=float("nan"), recall=float("nan"),
                                                 mean_delta=float("nan"))
            continue
        acc = [r for r in sel if r["accepted"]]
        prec = np.mean([r["true_positive"] for r in acc]) if acc else float("nan")
        rec = len({r["effect"] for r in acc if r["effect"]} & GROUND_TRUTH) / len(GROUND_TRUTH)
        out["theta_rho"][f"{th:.2f}"] = dict(
            fires=len(sel), accepted=len(acc), precision=float(prec), recall=float(rec),
            mean_delta=float(np.nanmean([r["delta_test"] for r in acc])) if acc else float("nan"),
        )
    for dm in deltas:
        sel = [r for r in rows if r["delta_min"] == dm]
        acc = [r for r in sel if r["accepted"]]
        prec = np.mean([r["true_positive"] for r in acc]) if acc else float("nan")
        rec = len({r["effect"] for r in acc if r["effect"]} & GROUND_TRUTH) / len(GROUND_TRUTH)
        out["delta_min"][f"{dm:.2f}"] = dict(
            n=len(sel), accepted=len(acc), precision=float(prec), recall=float(rec),
            mean_delta=float(np.nanmean([r["delta_test"] for r in acc])) if acc else float("nan"),
        )
    Path(args.out).write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"mean monitored Arctic KPI: {np.nanmean(data) * 100:.1f}%")
    print(f"{'theta_rho':<12}{'fires':>7}{'acc':>5}{'precision':>11}{'recall':>8}{'d_test':>8}")
    for th, v in out["theta_rho"].items():
        print(f"{th:<12}{v['fires']:7d}{v.get('accepted', 0):5d}{v['precision'] * 100:10.0f}%"
              f"{v['recall'] * 100:7.0f}%{v['mean_delta']:8.3f}")
    print(f"\n{'delta_min':<12}{'runs':>6}{'acc':>5}{'precision':>11}{'recall':>8}{'d_test':>8}")
    for dm, v in out["delta_min"].items():
        print(f"{dm:<12}{v['n']:6d}{v['accepted']:5d}{v['precision'] * 100:10.0f}%"
              f"{v['recall'] * 100:7.0f}%{v['mean_delta']:8.3f}")
    print("wrote", args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
