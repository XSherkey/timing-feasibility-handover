"""Sweep acquisition-model coefficients against the scripted baseline.

The calibration target, taken from the manuscript's Sec. 4.2, is:

* a policy that always hands over to the best-elevation satellite with the
  minimum preparation advance should keep ~55% of Arctic handovers;
* the same policy should be near 99% at mid-latitude;
* a long advance (10-12 s and above) should restore >90-95% in the Arctic.
"""
from __future__ import annotations

import argparse
import itertools
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from almond.twin.env import EnvConfig, HandoverEnv
from almond.twin.twin import DigitalTwin, TwinConfig

GROUPS = {
    "arctic>70": lambda lat: abs(lat) > 70,
    "65-70": lambda lat: 65 <= abs(lat) <= 70,
    "30-65": lambda lat: 30 <= abs(lat) < 65,
    "<30": lambda lat: abs(lat) < 30,
}


def scripted(env: HandoverEnv, mode: str, bucket: int):
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
        tgt = np.ones(B, dtype=np.int64)
    else:
        score = (
            3.0 * path_ok.astype(np.float32)
            + 3.0 * same.astype(np.float32)
            + np.clip(el_c / 90.0, 0, 1) * 0.5
        )
        score = np.where(path_ok, score, -1.0)
        best = np.argmax(score, axis=1)
        tgt = np.where(np.take_along_axis(score, best[:, None], axis=1)[:, 0] > 0, best + 1, 0)
    return tgt, np.full(B, bucket, dtype=np.int64)


def evaluate(env, mode, bucket, episodes, seed=0):
    rows = []
    for _ in range(episodes):
        env.reset()
        for _s in range(env.cfg.episode_steps):
            env.step(*scripted(env, mode, bucket))
        st = env.episode_stats()
        lat = env.site_lat[env.site]
        for i in range(env.batch):
            rows.append((lat[i], st["hsr"][i], st["attempts"][i], st["drops"][i], st["lat_p95"][i]))
    return np.array(rows, dtype=np.float64)


def report(rows, label):
    lat, hsr, att = rows[:, 0], rows[:, 1], rows[:, 2]
    out = {}
    for g, f in GROUPS.items():
        m = np.array([f(x) for x in lat])
        if not m.any() or att[m].sum() == 0:
            out[g] = float("nan")
            continue
        out[g] = float(np.sum(hsr[m] * att[m]) / att[m].sum()) * 100
    out["ALL"] = float(np.sum(hsr * att) / max(att.sum(), 1e-9)) * 100
    print(
        f"{label:<28}"
        + "".join(f"{out[g]:7.1f}" for g in list(GROUPS) + ["ALL"])
        + f"{att.mean():8.1f}"
    )
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", default="cal")
    ap.add_argument("--hours", type=float, default=1.5)
    ap.add_argument("--episodes", type=int, default=6)
    ap.add_argument("--batch", type=int, default=32)
    ap.add_argument("--sweep", action="store_true")
    ap.add_argument("--steps", type=int, default=240)
    args = ap.parse_args()

    twin = DigitalTwin(TwinConfig(horizon_s=args.hours * 3600, tag=args.tag)).build()
    hdr = f"{'setting':<28}" + "".join(f"{g:>7}" for g in list(GROUPS) + ["ALL"]) + f"{'att/ep':>8}"
    print(hdr)
    print("-" * len(hdr))

    def run_with(**kw):
        ecfg = EnvConfig(episode_steps=args.steps, **kw)
        env = HandoverEnv(twin, ecfg, batch=args.batch, seed=1)
        rows = evaluate(env, "naive", 0, args.episodes)
        return env, rows

    if args.sweep:
        for seam, hop_c in itertools.product([4.0, 6.0, 8.0], [0.10, 0.20]):
            env, rows = run_with(seam_penalty_s=seam, acq_hop_coeff=hop_c)
            report(rows, f"naive a=4 seam={seam} hop={hop_c}")
        return 0

    env, rows = run_with()
    report(rows, "naive advance=4s")
    for b in (1, 2, 3, 4, 5, 6):
        env, rows = run_with()
        env2 = HandoverEnv(twin, EnvConfig(episode_steps=args.steps), batch=args.batch, seed=2)
        rows2 = evaluate(env2, "naive", b, args.episodes)
        report(rows2, f"naive advance={4 + 2 * b}s")
    env3 = HandoverEnv(twin, EnvConfig(episode_steps=args.steps), batch=args.batch, seed=3)
    rows3 = evaluate(env3, "smart", 5, args.episodes)
    report(rows3, "smart advance=14s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
