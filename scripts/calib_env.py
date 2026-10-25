"""Evaluate scripted handover policies in the twin (pre-RL calibration).

Two reference policies are run to check that the twin reproduces the paper's
baseline behaviour before any learning happens:

``naive``
    Always hand over to the highest-elevation candidate with the default
    preparation advance -- the "hand-crafted reward" regime that ignores the
    preparation timing.
``smart``
    Prefer a same-plane target that has a feeder route, and use a long
    advance -- the regime the mined constraint enforces.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from almond.twin.env import HandoverEnv, EnvConfig
from almond.twin.twin import DigitalTwin, TwinConfig

GROUPS = {
    "arctic>70": lambda lat: abs(lat) > 70,
    "65-70": lambda lat: 65 <= abs(lat) <= 70,
    "30-65": lambda lat: 30 <= abs(lat) < 65,
    "<30": lambda lat: abs(lat) < 30,
}


def scripted(env: HandoverEnv, mode: str, advance_bucket: int):
    """Return (target, advance) action arrays for the current observation."""
    B, K = env.batch, env.K
    si, t = env.site, env.t_idx
    cand = env.cand_idx[si, t]
    cc = np.maximum(cand, 0)
    el_c = env.el[si[:, None], cc, t[:, None]]
    hop_c = env.hop[cc, t[:, None]]
    srv = np.maximum(env.serving, 0)
    nrm_s = env.nrm[srv, t]
    same = np.einsum("bki,bi->bk", env.nrm[cc, t[:, None]], nrm_s) > 0.995
    path_ok = (hop_c >= 0) & (cand >= 0)
    if mode == "naive":
        tgt = np.ones(B, dtype=np.int64)  # highest-elevation candidate
        adv = np.full(B, advance_bucket, dtype=np.int64)
    else:
        # score: reachable same-plane first, then reachable, then elevation
        score = (
            path_ok.astype(np.float32) * 2.0
            + same.astype(np.float32) * 3.0
            + np.clip(el_c / 90.0, 0, 1) * 0.5
        )
        score = np.where(path_ok, score, -1.0)
        best = np.argmax(score, axis=1)
        tgt = np.where(np.take_along_axis(score, best[:, None], axis=1)[:, 0] > 0, best + 1, 0)
        adv = np.full(B, advance_bucket, dtype=np.int64)
    return tgt, adv


def run(env: HandoverEnv, mode: str, advance_bucket: int, episodes: int, seed: int = 0):
    rng = np.random.default_rng(seed)
    per_inst = []
    for _ in range(episodes):
        env.reset()
        for _s in range(env.cfg.episode_steps):
            tg, ad = scripted(env, mode, advance_bucket)
            env.step(tg, ad)
        st = env.episode_stats()
        lat = np.array([env.site_lat[s] for s in env.site])
        for i in range(env.batch):
            per_inst.append((lat[i], st["hsr"][i], st["attempts"][i], st["lat_p95"][i]))
    return np.array(per_inst, dtype=np.float64)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", default="cal")
    ap.add_argument("--hours", type=float, default=1.5)
    ap.add_argument("--episodes", type=int, default=12)
    ap.add_argument("--batch", type=int, default=32)
    ap.add_argument("--episode-steps", type=int, default=240)
    args = ap.parse_args()

    cfg = TwinConfig(horizon_s=args.hours * 3600, tag=args.tag)
    twin = DigitalTwin(cfg).build()
    econf = EnvConfig(episode_steps=args.episode_steps)
    env = HandoverEnv(twin, econf, batch=args.batch, seed=1)

    print(f"{'policy':<22}{'group':<12}{'HSR%':>7}{'attempts':>10}{'lat_p95':>9}")
    for mode, adv in (("naive", 0), ("smart", 5)):
        data = run(env, mode, adv, args.episodes)
        lat, hsr, att, lp = data[:, 0], data[:, 1], data[:, 2], data[:, 3]
        for gname, f in GROUPS.items():
            m = np.array([f(x) for x in lat])
            if not m.any():
                continue
            w = att[m]
            hsr_w = float(np.sum(hsr[m] * w) / max(w.sum(), 1e-9)) * 100
            print(f"{mode + ' adv=' + str(adv):<22}{gname:<12}{hsr_w:7.1f}{w.mean():10.1f}{np.median(lp[m]):9.1f}")
        w = att
        print(f"{mode + ' adv=' + str(adv):<22}{'ALL':<12}{np.sum(hsr * w) / max(w.sum(), 1e-9) * 100:7.1f}"
              f"{w.mean():10.1f}{np.median(lp):9.1f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
