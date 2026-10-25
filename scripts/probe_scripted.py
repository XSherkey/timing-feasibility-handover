"""Scripted-policy probe: does the twin reproduce the paper's reliability story?

Runs four scripted controllers (no learning) over the whole site set and reports
handover success by region.  The decisive quantity is the *preparation lead*
sweep: if the twin is calibrated correctly, the highest-elevation-target rule at
a short lead should leave a deep Arctic gap while a longer lead (the constraint
the forensic loop mines) closes it, and mid-latitude service should be almost
insensitive to the lead.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from almond.twin.env import EnvConfig, HandoverEnv
from almond.twin.twin import DigitalTwin, TwinConfig

REGIONS = {
    "arctic>70": lambda x: x > 70,
    "65-70": lambda x: 65 <= x <= 70,
    "30-65": lambda x: 30 <= x < 65,
    "<30": lambda x: x < 30,
}


def choose(env, mode):
    B, K = env.batch, env.K
    si, t = env.site, env.t_idx
    cand = env.cand_idx[si, t]
    cc = np.maximum(cand, 0)
    valid = cand >= 0
    el_c = env.el[si[:, None], cc, t[:, None]]
    hop_c = env.hop[cc, t[:, None]]
    srv = np.maximum(env.serving, 0)
    same = np.einsum("bki,bi->bk", env.nrm[cc, t[:, None]], env.nrm[srv, t]) > 0.995
    path = hop_c >= 0
    trem = env.trem[si, srv, t]
    svc = env.service_left[si, srv, t]
    threshold = 40.0 if mode.startswith("early") else 8.0
    must = (svc <= threshold) | (trem <= 40.0)
    if mode.endswith("same_plane"):
        score = np.where(path, 3.0 * same + el_c / 90.0, -1.0)
    elif mode.endswith("routed"):
        score = np.where(path, 1.0 + el_c / 90.0 + same, -1.0)
    else:  # highest elevation
        score = np.where(valid, 1.0 + el_c / 90.0, -1.0)
    best = np.argmax(score, axis=1)
    tgt = np.where(np.take_along_axis(score, best[:, None], axis=1)[:, 0] > 0, best + 1, 0)
    tgt = np.where(must, tgt, 0)
    return tgt


def run(env, mode, lead_bucket, episodes):
    rows = []
    for _ in range(episodes):
        env.reset()
        for _s in range(env.cfg.episode_steps):
            env.step(choose(env, mode), np.full(env.batch, lead_bucket, dtype=np.int64))
        st = env.episode_stats()
        lat = env.site_lat[env.site]
        for i in range(env.batch):
            rows.append(dict(lat=float(lat[i]), hsr=float(st["hsr"][i]),
                             attempts=int(st["attempts"][i]), successes=int(st["successes"][i])))
    return rows


def summarise(rows):
    out = {}
    for name, f in REGIONS.items():
        sel = [r for r in rows if f(abs(r["lat"]))]
        att = sum(r["attempts"] for r in sel)
        out[name] = sum(r["successes"] for r in sel) / att * 100 if att else float("nan")
    att = sum(r["attempts"] for r in rows)
    out["ALL"] = sum(r["successes"] for r in rows) / att * 100 if att else float("nan")
    out["att_per_ep"] = att / max(len(rows), 1)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", default="probe")
    ap.add_argument("--hours", type=float, default=1.5)
    ap.add_argument("--episodes", type=int, default=4)
    ap.add_argument("--batch", type=int, default=40)
    ap.add_argument("--steps", type=int, default=240)
    args = ap.parse_args()

    twin = DigitalTwin(TwinConfig(horizon_s=args.hours * 3600, tag=args.tag)).build(verbose=False)
    env = HandoverEnv(twin, EnvConfig(episode_steps=args.steps), batch=args.batch, seed=7)
    hdr = f"{'policy':<26}" + "".join(f"{k:>9}" for k in list(REGIONS) + ["ALL"]) + f"{'att/ep':>8}"
    print(hdr)
    print("-" * len(hdr))
    for mode in ("elev", "elev_routed", "elev_same_plane", "early_same_plane"):
        for bucket in (0, 1, 2, 3, 4, 5):
            rows = run(env, mode, bucket, args.episodes)
            s = summarise(rows)
            lead = env.cfg.a_min_s + bucket * env.cfg.a_step_s
            print(f"{mode + ' lead=' + str(int(lead)) + 's':<26}"
                  + "".join(f"{s[k]:9.1f}" for k in list(REGIONS) + ["ALL"])
                  + f"{s['att_per_ep']:8.1f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
