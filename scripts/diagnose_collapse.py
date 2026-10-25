"""Step-level diagnosis of a collapsed policy.

Reports, per episode step, why the handover pipeline does not produce successful
handovers: whether a session is active, whether a serving link exists, whether
the policy is allowed to command, whether it does, and -- when it does -- how the
requested lead compares with the acquisition time and the remaining visibility.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

import numpy as np
import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from almond.policies.nets import GraphSpec, build_policy
from almond.policies.ppo import RunningNorm
from almond.twin.env import EnvConfig, HandoverEnv
from almond.twin.twin import DigitalTwin, TwinConfig


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True)
    ap.add_argument("--tag", default="ref")
    ap.add_argument("--hours", type=float, default=12.0)
    ap.add_argument("--episodes", type=int, default=2)
    ap.add_argument("--batch", type=int, default=32)
    args = ap.parse_args()

    run = Path(args.run)
    blob = torch.load(run / "policy.pt", map_location="cpu", weights_only=False)
    spec = GraphSpec.from_dict(blob["spec"])
    twin = DigitalTwin(TwinConfig(tag=args.tag, horizon_s=args.hours * 3600)).build(verbose=False)
    w = blob.get("weights") or dict(w_rel=0.57, w_lat=0.14, w_pow=0.29)
    env = HandoverEnv(twin, EnvConfig(episode_steps=240, w_rel=w["w_rel"], w_lat=w["w_lat"],
                                      w_pow=w["w_pow"]), batch=args.batch, seed=1234)
    x, adj = env.candidate_graph()
    pol = build_policy("graph", obs_dim=env.obs_dim, node_dim=x.shape[-1],
                       n_targets=env.K + 1, n_advance=env.n_advance, spec=spec)
    pol.load_state_dict(blob["policy"])
    pol.eval()
    _on = blob.get("obs_norm")
    obs_norm = RunningNorm(len(_on["mean"])) if _on else None
    if obs_norm is not None:
        obs_norm.load_state_dict(_on)

    cnt = Counter()
    leads, setups, trems, elevs = [], [], [], []
    rew_parts = Counter()
    tgt_hist = np.zeros(env.K + 1, dtype=np.int64)
    adv_hist = np.zeros(env.n_advance, dtype=np.int64)
    fails = Counter()

    for ep in range(args.episodes):
        obs = env.reset(t_range=(3540, 3760))
        for _s in range(env.cfg.episode_steps):
            xx, aa = env.candidate_graph()
            o = obs_norm(obs) if obs_norm is not None else obs
            cand = env.cand_idx[env.site, env.t_idx]
            mask = np.concatenate([np.ones((env.batch, 1), bool), cand >= 0], axis=1)
            with torch.no_grad():
                lt, la, _v = pol(torch.as_tensor(o, dtype=torch.float32),
                                 torch.as_tensor(xx, dtype=torch.float32),
                                 torch.as_tensor(aa, dtype=torch.float32))
            lt = np.where(mask, lt.numpy(), -1e9)
            at = lt.argmax(-1)
            ad = la.numpy().argmax(-1)
            tgt_hist += np.bincount(at, minlength=env.K + 1)
            adv_hist += np.bincount(ad, minlength=env.n_advance)

            session = env.session.copy()
            srv = env.serving.copy()
            cd = env.cooldown.copy()
            lead = env.cfg.a_min_s + ad * env.cfg.a_step_s
            cnt["steps"] += env.batch
            cnt["session"] += int(session.sum())
            cnt["serving"] += int((srv >= 0).sum())
            cnt["cooldown_ready"] += int(((cd == 0) & session & (srv >= 0)).sum())
            cnt["commands"] += int(((at > 0) & session & (srv >= 0) & (cd == 0)).sum())
            cnt["active_when_ready"] += int((at[((cd == 0) & session & (srv >= 0))] > 0).sum())

            obs, rew, done, info = env.step(at, ad, record=True)
            cnt["success"] += int(info["success"].sum())
            cnt["failure"] += int(info["failure"].sum())
            cnt["lost"] += int(info["lost"].sum())
            for a in env.attempt_log[len(leads):]:
                leads.append(a["handover_advance_s"])
                setups.append(a["t_setup_s"])
                trems.append(a["remaining_visibility_s"])
                elevs.append(a["elevation_deg"])
                if not a["success"]:
                    fails[a.get("cause", "?")] += 1
            if np.any(info["success"]):
                rew_parts["success"] += int(info["success"].sum())
        st = env.episode_stats()
        print(f"ep{ep}: hsr={np.nanmean(st['hsr']):.3f} attempts={int(st['attempts'].sum())} "
              f"successes={int(st['successes'].sum())} drops={int(st['drops'].sum())}")

    steps = max(1, cnt["steps"])
    print("\n--- step accounting (fractions of all terminal-steps) ---")
    for k in ("session", "serving", "cooldown_ready", "commands", "success", "failure", "lost"):
        print(f"  {k:<14} {cnt[k] / steps * 100:6.2f}%")
    ready = max(1, cnt["cooldown_ready"])
    print(f"  P(choose a target | allowed)      {cnt['active_when_ready'] / ready * 100:6.2f}%")
    print(f"\ntarget action histogram : {np.round(tgt_hist / tgt_hist.sum(), 3).tolist()}")
    print(f"advance action histogram: {np.round(adv_hist / adv_hist.sum(), 3).tolist()}")
    if leads:
        lead = np.array(leads); setup = np.array(setups); trem = np.array(trems); el = np.array(elevs)
        print(f"\nattempts logged: {len(lead)}")
        print(f"  lead   p10/50/90 = {np.percentile(lead, [10, 50, 90]).round(1)}")
        print(f"  t_setup p10/50/90 = {np.nanpercentile(setup, [10, 50, 90]).round(1)}")
        print(f"  trem    p10/50/90 = {np.percentile(trem, [10, 50, 90]).round(1)}")
        print(f"  P(lead >= t_setup) = {(lead >= setup).mean():.3f}   "
              f"P(lead <= trem) = {(lead <= trem).mean():.3f}   "
              f"P(both) = {((lead >= setup) & (lead <= trem)).mean():.3f}")
        print(f"  elevation p50 = {np.median(el):.1f} deg, below mask {np.mean(el <= 5):.2%}")
    print(f"failure causes: {dict(fails)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
