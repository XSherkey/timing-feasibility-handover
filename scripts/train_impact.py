"""Train and validate the impact predictor used by the third auditor stage.

Generates twin rollouts spanning the grammar of candidate rules (the manuscript
quotes ~10,000 rollouts), measures the realised latency and reward shift of each
rule against a no-rule baseline, fits the 5-member ensemble, and reports the
mean absolute error, the calibration slope on held-out rollouts, and the rate at
which ensemble uncertainty flips an audit decision.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from almond.framework.auditor import ImpactPredictor
from almond.framework.kg import Constraint
from almond.framework.shield import compile_constraints
from almond.llm.surrogate import EFFECT_GRAMMAR
from almond.twin.env import EnvConfig, HandoverEnv
from almond.twin.twin import DigitalTwin, TwinConfig

ELEV_TH = [8, 10, 12, 15, 20]
ADV_TH = [6, 8, 10, 12]
HOP_TH = [2, 3, 4, 6]


def sample_rule(rng):
    eff = EFFECT_GRAMMAR[int(rng.integers(0, len(EFFECT_GRAMMAR)))]
    name = eff["name"]
    atoms = [{"field": "elevation_deg", "cmp": "<=", "value": float(rng.choice(ELEV_TH))}]
    if rng.random() < 0.6:
        atoms.append({"field": "handover_advance_s", "cmp": "<=", "value": float(rng.choice(ADV_TH))})
    if rng.random() < 0.3:
        atoms.append({"field": "isl_hop_count", "cmp": ">=", "value": float(rng.choice(HOP_TH))})
    mag = 0.0
    if name == "min_advance":
        mag = float(rng.choice(eff["params"]["seconds"]))
    elif name == "power_cap":
        mag = float(rng.choice(eff["params"]["max_lead_s"]))
    elif name == "buffer_drain":
        mag = float(rng.choice(eff["params"]["max_buffer"]))
    return dict(atoms=atoms, effect=name, magnitude=mag)


def scripted(env, adv_bucket=2):
    """A fixed, decent scripted controller so that the shift is rule-attributable."""
    K = env.K
    si, t = env.site, env.t_idx
    cand = env.cand_idx[si, t]
    cc = np.maximum(cand, 0)
    valid = cand >= 0
    el_c = env.el[si[:, None], cc, t[:, None]]
    hop = env.hop[cc, t[:, None]]
    srv = np.maximum(env.serving, 0)
    same = np.einsum("bki,bi->bk", env.nrm[cc, t[:, None]], env.nrm[srv, t]) > 0.995
    score = np.where(valid & (hop >= 0), 1.0 + el_c / 90.0 + same, -1.0)
    best = np.argmax(score, axis=1)
    tgt = np.where(np.take_along_axis(score, best[:, None], axis=1)[:, 0] > 0, best + 1, 0)
    svc = env.service_left[si, srv, t]
    tgt = np.where(svc <= 40.0, tgt, 0)
    return tgt, np.full(env.batch, adv_bucket, dtype=np.int64)


def rollout(env, constraint, episodes=1):
    shield = compile_constraints([constraint], env.cfg) if constraint else None
    lats, rets = [], []
    for _ in range(episodes):
        env.reset()
        r_sum = 0.0
        for _s in range(env.cfg.episode_steps):
            tg, ad = scripted(env)
            _obs, r, _d, _i = env.step(tg, ad, shield=shield)
            r_sum += float(np.mean(r))
        st = env.episode_stats()
        lp = st["lat_p95"]
        lats.append(float(np.nanmedian(lp)) if np.any(~np.isnan(lp)) else 150.0)
        rets.append(r_sum / env.cfg.episode_steps)
    return float(np.mean(lats)), float(np.mean(rets))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", default="probe")
    ap.add_argument("--hours", type=float, default=1.5)
    ap.add_argument("--rules", type=int, default=200)
    ap.add_argument("--batch", type=int, default=8)
    ap.add_argument("--steps", type=int, default=200)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--out", default="results/impact_predictor.json")
    args = ap.parse_args()

    twin = DigitalTwin(TwinConfig(horizon_s=args.hours * 3600, tag=args.tag)).build(verbose=False)
    env = HandoverEnv(twin, EnvConfig(episode_steps=args.steps), batch=args.batch, seed=args.seed)
    rng = np.random.default_rng(args.seed)

    base_lat, base_ret = rollout(env, None, episodes=2)
    X, y_lat, y_rew, meta = [], [], [], []
    for i in range(args.rules):
        r = sample_rule(rng)
        c = Constraint(id="tmp", version=1, atoms=r["atoms"], effect=r["effect"],
                       magnitude=r["magnitude"], nl_reading="")
        lat, ret = rollout(env, c, episodes=1)
        X.append(ImpactPredictor.featurise(r["atoms"], r["effect"], r["magnitude"],
                                           dict(latitude_abs_deg=72.0, polar=True)))
        y_lat.append(lat - base_lat)
        y_rew.append(ret - base_ret)
        meta.append(r)
    X = np.asarray(X)
    y_lat = np.asarray(y_lat)
    y_rew = np.asarray(y_rew)

    n = len(X)
    perm = rng.permutation(n)
    n_tr = int(0.75 * n)
    tr, te = perm[:n_tr], perm[n_tr:]
    pred = ImpactPredictor(n_models=5, hidden=256, seed=args.seed)
    pred.fit(X[tr], y_lat[tr], epochs=500, lr=1e-3)
    mu, sd = pred.predict(X[te])
    mae = float(np.mean(np.abs(mu - y_lat[te])))
    rmse = float(np.sqrt(np.mean((mu - y_lat[te]) ** 2)))
    slope = float(np.polyfit(y_lat[te], mu, 1)[0]) if np.std(y_lat[te]) > 1e-9 else float("nan")
    # decision flips: predicted decision changes when the uncertainty band is used
    budget = 40.0
    tight = mu + 2 * sd <= budget
    loose = mu <= budget
    flips = int(np.sum(tight != loose))
    out = dict(
        n_rules=int(n),
        base_latency_p95=base_lat,
        base_return=base_ret,
        delta_latency_mean=float(y_lat.mean()),
        delta_latency_std=float(y_lat.std()),
        mae=mae,
        rmse=rmse,
        calibration_slope=slope,
        decision_flip_rate=flips / max(len(te), 1),
        ensemble_sd_mean=float(sd.mean()),
        rules=meta,
    )
    pred.save(str(Path(args.out).with_suffix(".npz")))
    Path(args.out).write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"rules={n}  delta_lat mean={y_lat.mean():+.1f} ms (sd {y_lat.std():.1f})")
    print(f"MAE={mae:.2f} ms  RMSE={rmse:.2f}  calibration slope={slope:.2f}  "
          f"decision-flip rate={flips}/{len(te)}")
    print("wrote", args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
