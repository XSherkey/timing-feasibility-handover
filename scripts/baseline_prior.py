"""Experiment A: how good is the prior alone?

Two questions, ten seeds each:

``teacher``   the twin's own analytic controller, executed directly -- no network,
              no learning.  This is the strongest "hand-engineered" reference and
              the number ALMOND actually has to beat.
``bc_only``   the behaviour-cloned network with training, forensics and the shield
              all switched off (``skip_ppo``), so the only thing in play is the
              prior as the deployed policy represents it.

The evaluation uses the campaign's own final-eval protocol (held-out test window,
three traffic multipliers) so the numbers are directly comparable with the
campaign table.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from almond.analysis.metrics import attempt_weighted_hsr, satisfaction
from almond.framework.system import AlmondConfig, AlmondSystem
from almond.twin.env import EnvConfig, HandoverEnv
from almond.twin.twin import DigitalTwin, TwinConfig

WEIGHTS = dict(w_rel=0.68, w_lat=0.11, w_pow=0.21)
TRAFFIC = (0.5, 1.0, 2.0)
TEST = (0.82, 0.95)


def rollout_teacher(twin, seed: int, batch: int = 32, episodes: int = 2) -> dict:
    """Execute the analytic controller directly and score it."""
    env = HandoverEnv(twin, EnvConfig(episode_steps=240, w_rel=WEIGHTS["w_rel"],
                                      w_lat=WEIGHTS["w_lat"], w_pow=WEIGHTS["w_pow"]),
                      batch=batch, seed=seed)
    lo, hi = TEST
    t0, t1 = int(lo * twin.n_time), int(hi * twin.n_time)
    rows = []
    for mult in TRAFFIC:
        env.cfg.traffic_scale = mult
        for _ in range(episodes):
            env.reset(t_range=(t0, t1))
            for _s in range(env.cfg.episode_steps):
                at, aa = env.teacher_action()
                env.step(at, aa, record=False)
            st = env.episode_stats()
            lat = env.site_lat[env.site]
            for i in range(env.batch):
                rows.append(dict(lat=float(lat[i]), hsr=float(st["hsr"][i]),
                                 attempts=int(st["attempts"][i]),
                                 successes=int(st["successes"][i]),
                                 lat_p95=float(st["lat_p95"][i]) if not np.isnan(st["lat_p95"][i]) else float("nan"),
                                 power_mean=float(np.nanmean([p[i] for p in env.pow_hist])) if env.pow_hist else 0.5))
    env.cfg.traffic_scale = 1.0
    return dict(satisfaction=float(satisfaction(rows, WEIGHTS)),
                arctic=float(attempt_weighted_hsr(rows)) * 100,
                overall=float(attempt_weighted_hsr(rows, min_abs_lat=None)) * 100)


def run_bc_only(seed: int, spec: dict, episodes: int = 9600) -> dict:
    cfg = AlmondConfig(variant="no_forensics", seed=seed, episodes=episodes, eval_every=1200,
                       device="cpu", skip_ppo=True, bc_episodes=6, bc_epochs=12,
                       fixed_spec=dict(spec),
                       out_dir=str(ROOT / "results" / "_prior" / f"bc_seed{seed}"))
    system = AlmondSystem(cfg, out_dir=cfg.out_dir)
    res = system.run()
    # with skip_ppo the system returns the final evaluation directly, without the
    # usual wrapper, so accept both shapes
    fin = res.get("final", res)
    return dict(satisfaction=float(fin["satisfaction"]),
                arctic=float(fin["arctic"]["hsr"]) * 100,
                overall=float(fin["overall"]["hsr"]) * 100)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", default="0-9")
    ap.add_argument("--out", default="results/baseline_prior.json")
    args = ap.parse_args()
    seeds = []
    for part in args.seeds.split(","):
        if "-" in part:
            a, b = part.split("-")
            seeds.extend(range(int(a), int(b) + 1))
        elif part:
            seeds.append(int(part))

    spec = json.loads((ROOT / "results/nas/llm_spec.json").read_text(encoding="utf-8"))
    spec = spec.get("spec", spec)
    twin = DigitalTwin(TwinConfig(tag="ref", horizon_s=12 * 3600)).build(verbose=False)

    rows = []
    for s in seeds:
        t = rollout_teacher(twin, seed=s)
        b = run_bc_only(s, spec)
        rows.append(dict(seed=s, teacher=t, bc_only=b))
        print(f"seed {s}: teacher S={t['satisfaction']:5.1f} arctic={t['arctic']:5.1f}%   "
              f"bc_only S={b['satisfaction']:5.1f} arctic={b['arctic']:5.1f}%", flush=True)

    def agg(key: str, field: str) -> dict:
        v = np.array([r[key][field] for r in rows], dtype=float)
        half = 1.96 * v.std(ddof=1) / np.sqrt(len(v)) if len(v) > 1 else 0.0
        return dict(mean=float(v.mean()), std=float(v.std(ddof=1)) if len(v) > 1 else 0.0,
                    median=float(np.median(v)), ci_low=float(v.mean() - half),
                    ci_high=float(v.mean() + half), n=int(len(v)))

    summary = {k: {f: agg(k, f) for f in ("satisfaction", "arctic", "overall")}
               for k in ("teacher", "bc_only")}
    out = dict(weights=WEIGHTS, traffic=list(TRAFFIC), test_window=list(TEST),
               spec=spec, rows=rows, summary=summary)
    p = ROOT / args.out
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")

    print("\n--- summary (mean over seeds, 95% CI) ---")
    for k in ("teacher", "bc_only"):
        a = summary[k]["arctic"]
        s = summary[k]["satisfaction"]
        print(f"{k:<8} arctic {a['mean']:5.1f}% [{a['ci_low']:5.1f},{a['ci_high']:5.1f}]  "
              f"satisfaction {s['mean']:5.1f} [{s['ci_low']:5.1f},{s['ci_high']:5.1f}]")
    print("wrote", p.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
