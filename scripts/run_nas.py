"""Run the architecture search once per configuration and save the result.

The ground-side topology search is an offline, seasonal step (manuscript
Sec. 3.3.6); running it once per configuration and holding the discovered
architecture fixed across reinforcement-learning seeds isolates the
seed-to-seed variance of the *learning* component instead of conflating it with
search randomness.  The same protocol is applied to the unseeded baseline, so
the comparison in Sec. 4.4 remains budget-matched.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from almond.framework.system import AlmondConfig, AlmondSystem


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", default="llm", choices=["llm", "random"])
    ap.add_argument("--out", default="results/nas/llm_spec.json")
    ap.add_argument("--population", type=int, default=10)
    ap.add_argument("--generations", type=int, default=3)
    ap.add_argument("--eval-episodes", type=int, default=24)
    ap.add_argument("--batch", type=int, default=8)
    ap.add_argument("--steps", type=int, default=160)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--device", default="cpu")
    args = ap.parse_args()

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    variant = "full" if args.mode == "llm" else "no_nas"
    cfg = AlmondConfig(
        variant=variant, seed=args.seed, device=args.device,
        nas_generations=args.generations, nas_population=args.population,
        nas_eval_episodes=args.eval_episodes, nas_batch=args.batch,
        episode_steps=args.steps, episodes=1, out_dir=str(out.parent / f"seed{args.seed}"),
    )
    system = AlmondSystem(cfg, out_dir=cfg.out_dir)
    system.translate()
    t0 = time.time()
    spec = system.search_architecture()
    res = dict(
        mode=args.mode,
        spec=spec.to_dict(),
        wall_s=time.time() - t0,
        nas=system.nas_result,
        config=vars(args),
    )
    out.write_text(json.dumps(res, indent=2, default=float), encoding="utf-8")
    print(f"[nas:{args.mode}] {spec.describe()}  params-logged  wall {res['wall_s']:.0f}s -> {out}")
    if system.nas_result:
        print(f"  evaluated={system.nas_result['evaluated']}  best_reward={system.nas_result['best_reward']:.3f}")
        for p in system.nas_result["front"][:5]:
            print(f"    {p['spec']['kind']:<7} w{p['spec']['width']:<4} L{p['spec']['layers']} "
                  f"params={p['params']:<6} reward={p['reward']:.3f} lat={p['latency_ms']:.2f}ms")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
