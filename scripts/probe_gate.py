"""What does the counterfactual gate actually filter?

The single-intent ablation could not answer this: the mined candidate always passed
the 5% gate, so ``no_counterfactual`` came out bit-identical.  The right question is
not "does removing the gate change the mined rule" but "what would happen if a
*plausible but wrong* candidate were committed".

This script replays a frozen policy with and without a list of candidate rules on
the validation and test splits (the engine's own ``replay_rule``), and prints the
effect of committing each one.  A candidate is admitted only if it improves both
splits by at least ``--delta``; the point is that several natural candidates are
rejected *and would have hurt*.

Usage
-----
    python scripts/probe_gate.py --run results/campaign_1023/almond_seed0
    python scripts/probe_gate.py --policy teacher
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from almond.framework.forensics import SplitConfig, replay_rule, score  # noqa: E402
from almond.framework.kg import Constraint  # noqa: E402
from almond.policies.nets import GraphSpec, build_policy  # noqa: E402
from almond.policies.ppo import PPOConfig, PPOTrainer  # noqa: E402
from almond.twin.env import EnvConfig, HandoverEnv  # noqa: E402
from almond.twin.twin import DigitalTwin, TwinConfig  # noqa: E402

#: (name, effect, magnitude, atoms) - a mix of sensible, too-weak, too-strong and
#: wrong-scope candidates, all of which an LLM could plausibly propose.
CANDIDATES = [
    ("weak lead (8 s, polar)", "min_advance", 8.0, [("latitude_abs_deg", ">=", 68)]),
    ("mined-style (16 s, polar)", "min_advance", 16.0, [("latitude_abs_deg", ">=", 68)]),
    ("very long (26 s, global)", "min_advance", 26.0, []),
    ("wrong scope (18 s, equator)", "min_advance", 18.0, [("latitude_abs_deg", "<", 30)]),
    ("structural (same plane, polar)", "prefer_same_plane", 0.0, [("latitude_abs_deg", ">=", 70)]),
    ("low-elevation only (16 s)", "min_advance", 16.0, [("elevation_deg", "<=", 15)]),
]


def make_constraint(name: str, effect: str, magnitude: float, atoms: list) -> Constraint:
    return Constraint(
        id=name[:8].replace(" ", "_"),
        version=1,
        atoms=[{"field": f, "cmp": c, "value": float(v)} for f, c, v in atoms],
        effect=effect,
        magnitude=float(magnitude),
        nl_reading=name,
        provenance={},
        confidence=1.0,
        scope_tags={},
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", default=None)
    ap.add_argument("--policy", default="ckpt", choices=("ckpt", "teacher"))
    ap.add_argument("--twin", default="ref")
    ap.add_argument("--hours", type=float, default=12.0)
    ap.add_argument("--batch", type=int, default=32)
    ap.add_argument("--steps", type=int, default=240)
    ap.add_argument("--episodes", type=int, default=2)
    ap.add_argument("--delta", type=float, default=0.05)
    ap.add_argument("--seed", type=int, default=0)
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

    def policy_fn(obs, x, adj, deterministic=True):
        if args.policy == "teacher":
            return env.teacher_action()
        at, aa, _lp, _v = trainer._act(obs, x, adj, deterministic=deterministic)
        return at, aa

    splits = SplitConfig()
    val = splits.indices(twin.n_time, "validation", args.steps)
    test = splits.indices(twin.n_time, "test", args.steps)

    base_val = replay_rule(env, policy_fn, None, args.episodes, val)
    base_test = replay_rule(env, policy_fn, None, args.episodes, test)
    bv = score(base_val["rows"], "arctic")["hsr"]
    bt = score(base_test["rows"], "arctic")["hsr"]
    print(f"baseline (no constraint): validation {100 * bv:5.1f}%   test {100 * bt:5.1f}%")
    print(f"gate: admit only if delta_val >= {100 * args.delta:.0f}% and delta_test >= {100 * args.delta:.0f}%\n")
    print(f"{'candidate':<32}{'val':>8}{'d_val':>8}{'test':>8}{'d_test':>8}   verdict")

    rows = []
    for name, effect, mag, atoms in CANDIDATES:
        c = make_constraint(name, effect, mag, atoms)
        rv = replay_rule(env, policy_fn, c, args.episodes, val)
        rt = replay_rule(env, policy_fn, c, args.episodes, test)
        hv = score(rv["rows"], "arctic")["hsr"]
        ht = score(rt["rows"], "arctic")["hsr"]
        dv, dt = hv - bv, ht - bt
        admit = dv >= args.delta and dt >= args.delta
        verdict = "ADMIT" if admit else ("reject" + ("  <-- would hurt" if dt < 0 else "  <-- no gain"))
        print(f"{name:<32}{100 * hv:>7.1f}%{100 * dv:>+7.1f}{100 * ht:>7.1f}%{100 * dt:>+7.1f}   {verdict}")
        rows.append(dict(name=name, val=hv, d_val=dv, test=ht, d_test=dt, admit=bool(admit)))

    if args.out:
        json.dump(dict(run=args.run, policy=args.policy, baseline=(bv, bt), rows=rows),
                  open(args.out, "w", encoding="utf-8"), indent=2)
        print(f"\nwrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
