"""Diagnose a collapsed ALMOND/PPO run: what is the policy actually doing?

Loads a trained policy from a campaign run, rolls it out on the test split and
reports the action distribution, the attempt/success/drop counts, the lead-time
choice, the achieved availability and where the reward mass sits.  Used to
explain the bimodal outcome (converged vs collapsed runs).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from almond.policies.nets import GraphSpec, build_policy
from almond.twin.env import EnvConfig, HandoverEnv
from almond.twin.twin import DigitalTwin, TwinConfig


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True, help="campaign run directory")
    ap.add_argument("--tag", default="ref")
    ap.add_argument("--hours", type=float, default=12.0)
    ap.add_argument("--episodes", type=int, default=2)
    ap.add_argument("--batch", type=int, default=32)
    args = ap.parse_args()

    run = Path(args.run)
    blob = torch.load(run / "policy.pt", map_location="cpu", weights_only=False)
    spec = GraphSpec.from_dict(blob["spec"])
    twin = DigitalTwin(TwinConfig(tag=args.tag, horizon_s=args.hours * 3600)).build(verbose=False)
    weights = blob.get("weights") or dict(w_rel=0.57, w_lat=0.14, w_pow=0.29)
    env = HandoverEnv(
        twin,
        EnvConfig(episode_steps=240, w_rel=weights["w_rel"], w_lat=weights["w_lat"], w_pow=weights["w_pow"]),
        batch=args.batch,
        seed=4242,
    )
    x, adj = env.candidate_graph()
    pol = build_policy("graph", obs_dim=env.obs_dim, node_dim=x.shape[-1],
                       n_targets=env.K + 1, n_advance=env.n_advance, spec=spec)
    pol.load_state_dict(blob["policy"])
    pol.eval()
    _on = blob.get("obs_norm")
    obs_norm = None
    if _on:
        from almond.policies.ppo import RunningNorm
        obs_norm = RunningNorm(len(_on["mean"]))
        obs_norm.load_state_dict(_on)

    tgt_hist = np.zeros(env.K + 1, dtype=np.int64)
    adv_hist = np.zeros(env.n_advance, dtype=np.int64)
    attempts = successes = drops = 0
    served_steps = 0
    total_steps = 0
    leads: list[float] = []
    tset: list[float] = []
    fails_kind = {"no_path": 0, "lead_lt_setup": 0, "lead_gt_trem": 0, "target_dark": 0}

    for _ in range(args.episodes):
        obs = env.reset(t_range=(3540, 3760))
        for _s in range(env.cfg.episode_steps):
            xx, aa = env.candidate_graph()
            o = obs_norm(obs) if obs_norm else obs
            cand = env.cand_idx[env.site, env.t_idx]
            m = np.concatenate([np.ones((env.batch, 1), bool), cand >= 0], axis=1)
            with torch.no_grad():
                lt, la, _v = pol(torch.as_tensor(o, dtype=torch.float32),
                                 torch.as_tensor(xx, dtype=torch.float32),
                                 torch.as_tensor(aa, dtype=torch.float32))
            lt = lt.numpy()
            lt = np.where(m, lt, -1e9)
            at = lt.argmax(-1)
            ad = la.numpy().argmax(-1)
            tgt_hist += np.bincount(at, minlength=env.K + 1)
            adv_hist += np.bincount(ad, minlength=env.n_advance)
            obs, rew, done, info = env.step(at, ad, record=True)
            served_steps += int(info["served"].sum())
            total_steps += env.batch
        st = env.episode_stats()
        attempts += int(st["attempts"].sum())
        successes += int(st["successes"].sum())
        drops += int(st["drops"].sum())

    for r in env.attempt_log:
        if r["success"]:
            continue
        if r["path_available"] < 0.5:
            fails_kind["no_path"] += 1
        if r["handover_advance_s"] < r["t_setup_s"] - 1e-9:
            fails_kind["lead_lt_setup"] += 1
        if r["handover_advance_s"] > r["remaining_visibility_s"] + 1e-9:
            fails_kind["lead_gt_trem"] += 1
        if r["elevation_deg"] <= 10:
            fails_kind["target_dark"] += 1
    leads = [r["handover_advance_s"] for r in env.attempt_log]
    tset = [r["t_setup_s"] for r in env.attempt_log]

    out = dict(
        run=str(run),
        variant=blob.get("variant"),
        kept=f"target==0 in {100 * tgt_hist[0] / max(tgt_hist.sum(), 1):.1f}% of decisions",
        target_hist=(tgt_hist / max(tgt_hist.sum(), 1)).round(3).tolist(),
        advance_hist=(adv_hist / max(adv_hist.sum(), 1)).round(3).tolist(),
        attempts=attempts,
        successes=successes,
        drops=drops,
        hsr=successes / max(attempts, 1),
        served_fraction=served_steps / max(total_steps, 1),
        lead_median=float(np.median(leads)) if leads else None,
        t_setup_median=float(np.median(tset)) if tset else None,
        failure_kinds=fails_kind,
        n_attempts_logged=len(env.attempt_log),
    )
    print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
