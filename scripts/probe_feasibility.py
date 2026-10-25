"""Active de-censoring probe, with an isotonic fit and a bootstrap interval.

Why this exists
---------------
The failure log only reveals ``T_setup > a`` for rejected attempts, so any reader —
the LLM included — can only infer the requirement inside the range of advances the
policy actually tried.  The probe removes the censoring the only way it can be
removed: by *trying* the longer advances.

Estimator (v2)
--------------
Each advance bucket yields a set of episode outcomes.  The *point estimate* is the
pooled late rate per bucket, smoothed with a decreasing isotonic (PAVA) fit, and
``tau*`` is the first advance whose fitted rate is inside ``eps``.  The *interval*
comes from resampling **episodes within each bucket** (the episode is the
independent unit) and refitting, so the reported CI answers "how stable is the
threshold under a different draw of experience?" rather than "how stable is the
pooled mean?".

``--episodes auto`` doubles the budget from 2 until the CI width is inside
``--ci-width`` seconds (or the cap is reached), which is the number the in-loop
PCS should default to.

Usage
-----
    python scripts/probe_feasibility.py --run results/campaign_1023/almond_seed0
    python scripts/probe_feasibility.py --run ... --episodes auto --acq-signaling 3.2
    python scripts/probe_feasibility.py --policy teacher --regime polar
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from almond.policies.nets import GraphSpec, build_policy  # noqa: E402
from almond.policies.ppo import PPOConfig, PPOTrainer  # noqa: E402
from almond.twin.env import EnvConfig, HandoverEnv  # noqa: E402
from almond.twin.twin import DigitalTwin, TwinConfig  # noqa: E402

DEFAULT_ADVANCES = (6, 8, 10, 12, 14, 16, 18, 20, 22, 24, 26)


def bucket_for(a: float, cfg: EnvConfig) -> int:
    return int(np.clip(round((a - cfg.a_min_s) / cfg.a_step_s), 0, cfg.a_max_bucket))


def isotonic_rates(counts: np.ndarray, lates: np.ndarray, grid: np.ndarray, eps: float) -> float:
    """PAVA (decreasing) fit of late rate vs advance; return the first grid point <= eps."""
    if len(grid) < 2:
        return float(grid[0]) if len(grid) else float("nan")
    rates = lates / np.maximum(counts, 1)
    vals = rates.astype(float).tolist()
    wts = counts.astype(float).tolist()
    starts = list(range(len(grid)))
    i = 0
    while i < len(vals) - 1:
        if vals[i] < vals[i + 1]:  # violation of the expected non-increasing shape
            w = wts[i] + wts[i + 1]
            vals[i] = (vals[i] * wts[i] + vals[i + 1] * wts[i + 1]) / w
            wts[i] = w
            del vals[i + 1], wts[i + 1], starts[i + 1]
            if i > 0:
                i -= 1
        else:
            i += 1
    fitted = np.empty(len(grid))
    for k, st in enumerate(starts):
        end = starts[k + 1] if k + 1 < len(starts) else len(grid)
        fitted[st:end] = vals[k]
    hit = grid[fitted <= eps]
    return float(hit[0]) if hit.size else float(grid[-1])


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", default=None)
    ap.add_argument("--policy", default="ckpt", choices=("ckpt", "teacher", "zero"))
    ap.add_argument("--twin", default="ref")
    ap.add_argument("--hours", type=float, default=12.0)
    ap.add_argument("--regime", default="polar", choices=("polar", "mid", "equat"))
    ap.add_argument("--advances", default=",".join(str(a) for a in DEFAULT_ADVANCES))
    ap.add_argument("--episodes", default="2", help="episodes per advance, or 'auto'")
    ap.add_argument("--max-episodes", type=int, default=16)
    ap.add_argument("--ci-width", type=float, default=1.0)
    ap.add_argument("--bootstrap", type=int, default=200)
    ap.add_argument("--batch", type=int, default=32)
    ap.add_argument("--steps", type=int, default=240)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--acq-signaling", type=float, default=None)
    ap.add_argument("--eps", type=float, default=0.05)
    ap.add_argument("--window", default="test", choices=("test", "validation", "train"),
                    help="split used for the forced-advance rollouts; calibration for the "
                         "lockbox protocol must use 'validation'")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    twin = DigitalTwin(TwinConfig(tag=args.twin, horizon_s=args.hours * 3600)).build(verbose=False)
    ck = None
    if args.policy == "ckpt":
        import torch

        ck = torch.load(Path(args.run) / "policy.pt", map_location="cpu", weights_only=False)
    weights = (ck or {}).get("weights") or dict(w_rel=0.7, w_lat=0.1, w_pow=0.2)
    env_cfg = EnvConfig(
        episode_steps=args.steps,
        w_rel=weights["w_rel"], w_lat=weights["w_lat"], w_pow=weights["w_pow"],
        drop_penalty=0.30, switch_penalty=0.10,
        **({"acq_signaling_s": args.acq_signaling} if args.acq_signaling is not None else {}),
    )
    env = HandoverEnv(twin, env_cfg, batch=args.batch, seed=args.seed + 4242)
    x0, _ = env.candidate_graph()

    trainer = None
    if args.policy == "ckpt":
        policy = build_policy("graph", obs_dim=env.obs_dim, node_dim=x0.shape[-1],
                              n_targets=env.K + 1, n_advance=env.n_advance,
                              spec=GraphSpec.from_dict(ck["spec"]))
        policy.load_state_dict(ck["policy"])
        trainer = PPOTrainer(env, policy, PPOConfig(device="cpu", seed=args.seed, deterministic=True))
        if trainer.obs_norm is not None and ck.get("obs_norm"):
            trainer.obs_norm.load_state_dict(ck["obs_norm"])

    def base_action(obs, x, adj):
        if args.policy == "teacher":
            return env.teacher_action()
        if args.policy == "zero":
            return np.zeros(env.batch, dtype=np.int64), np.zeros(env.batch, dtype=np.int64)
        at, aa, _lp, _v = trainer._act(obs, x, adj, deterministic=True)
        return at, aa

    from almond.framework.forensics import SplitConfig

    test_idx = SplitConfig().indices(twin.n_time, args.window, args.steps)
    lat_mask = dict(polar=lambda v: v >= 70.0, mid=lambda v: 30.0 <= v < 70.0,
                    equat=lambda v: v < 15.0)[args.regime]
    advances = [float(a) for a in args.advances.split(",") if a.strip()]
    grid = np.asarray(advances)

    # per-advance, per-episode outcome counts (episode = bootstrap unit)
    per_episode: dict[float, list[tuple[int, int]]] = {a: [] for a in advances}

    def run_budget(episodes: int) -> dict[float, list[tuple[int, int]]]:
        out: dict[float, list[tuple[int, int]]] = {a: [] for a in advances}
        for a in advances:
            b = bucket_for(a, env_cfg)
            for _ in range(episodes):
                env.cfg.traffic_scale = 1.0
                env.reset(t_range=test_idx)
                for _s in range(env.cfg.episode_steps):
                    x, adj = env.candidate_graph()
                    at, _aa = base_action(env.obs(), x, adj)
                    env.step(at, np.full(env.batch, b, dtype=np.int64), record=True)
                n = late = 0
                for att in env.attempt_log:
                    if lat_mask(abs(att["latitude_abs_deg"])):
                        n += 1
                        late += att["cause"] == "late_handover"
                out[a].append((n, late))
        return out

    def estimate(per: dict[float, list[tuple[int, int]]], rng=None) -> tuple[float, np.ndarray, np.ndarray]:
        counts, lates = [], []
        for a in advances:
            rows = per[a]
            if rng is not None and rows:
                idx = rng.integers(0, len(rows), size=len(rows))
                rows = [rows[i] for i in idx]
            counts.append(sum(r[0] for r in rows))
            lates.append(sum(r[1] for r in rows))
        counts = np.asarray(counts, dtype=float)
        lates = np.asarray(lates, dtype=float)
        return isotonic_rates(counts, lates, grid, args.eps), counts, lates

    def ci(per: dict[float, list[tuple[int, int]]], b: int) -> tuple[float, float]:
        rng = np.random.default_rng(12345)
        taus = [estimate(per, rng)[0] for _ in range(b)]
        return float(np.percentile(taus, 5)), float(np.percentile(taus, 95))

    if args.episodes == "auto":
        budget = 2
        while True:
            per = run_budget(budget)
            tau, _c, _l = estimate(per)
            lo, hi = ci(per, args.bootstrap)
            print(f"  episodes/advance={budget:>2}  tau*={tau:5.1f}  CI=[{lo:.1f},{hi:.1f}]  width={hi - lo:.2f} s")
            if hi - lo <= args.ci_width or budget >= args.max_episodes:
                break
            budget = min(budget * 2, args.max_episodes)
    else:
        budget = int(args.episodes)
        per = run_budget(budget)
        tau, _c, _l = estimate(per)
        lo, hi = ci(per, args.bootstrap)
        print(f"  episodes/advance={budget:>2}  tau*={tau:5.1f}  CI=[{lo:.1f},{hi:.1f}]  width={hi - lo:.2f} s")

    rows = []
    for a in advances:
        n = sum(r[0] for r in per[a])
        late = sum(r[1] for r in per[a])
        rows.append(dict(advance=a, n=n, late_rate=(late / n if n else float("nan"))))
        print(f"    a={a:5.1f}s n={n:5d} late={100 * (late / n if n else float('nan')):5.1f}%")

    print(f"\n  tau* = {tau:.1f} s   CI95 = [{lo:.1f}, {hi:.1f}]   episodes/advance = {budget}   "
          f"regime={args.regime}  policy={args.policy if args.policy != 'ckpt' else Path(args.run).name}")

    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        json.dump(dict(regime=args.regime, eps=args.eps, tau_star=tau, tau_ci=[lo, hi],
                       episodes_per_advance=budget, rows=rows, window=args.window,
                       acq_signaling=args.acq_signaling, run=args.run or args.policy),
                  open(args.out, "w", encoding="utf-8"), indent=2)
        print("wrote", args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
