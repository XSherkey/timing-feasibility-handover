"""Run the architecture search over several seeds per configuration (Fig. 8).

One search per configuration (as the campaign uses) is enough to *pick* an
architecture, but it cannot support a claim about search efficiency: a single
call per arm has no variance estimate.  This script repeats each arm and stores
every per-evaluation trace plus the final front, so Fig. 8 can show

* best-so-far reward against evaluations consumed (anytime performance, mean with
  the seed band),
* hypervolume against evaluations,
* evaluations needed to reach a fixed reward level per arm.

Both arms get the identical budget (population, generations, evaluation episodes),
so the only difference is whether the LLM proposes the seeds/mutations/critiques.
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
    ap.add_argument("--seeds", default="0-4")
    ap.add_argument("--out", default="results/nas/sweep_llm.json")
    ap.add_argument("--population", type=int, default=6)
    ap.add_argument("--generations", type=int, default=3)
    ap.add_argument("--eval-episodes", type=int, default=960,
                    help="proxy training episodes per candidate (960 is the measured knee)")
    ap.add_argument("--batch", type=int, default=8)
    ap.add_argument("--steps", type=int, default=160)
    ap.add_argument("--device", default="cpu")
    args = ap.parse_args()

    seeds = []
    for part in args.seeds.split(","):
        part = part.strip()
        if "-" in part:
            a, b = part.split("-")
            seeds.extend(range(int(a), int(b) + 1))
        elif part:
            seeds.append(int(part))

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    runs = []
    for seed in seeds:
        variant = "full" if args.mode == "llm" else "no_nas"
        cfg = AlmondConfig(
            variant=variant, seed=seed, device=args.device,
            nas_generations=args.generations, nas_population=args.population,
            nas_eval_episodes=args.eval_episodes, nas_batch=args.batch,
            episode_steps=args.steps, episodes=1,
            out_dir=str(out.parent / f"{args.mode}_seed{seed}"),
        )
        system = AlmondSystem(cfg, out_dir=cfg.out_dir)
        system.translate()
        t0 = time.time()
        spec = system.search_architecture()
        nas = system.nas_result or {}
        runs.append(
            dict(
                seed=seed,
                spec=spec.to_dict(),
                wall_s=time.time() - t0,
                evaluated=nas.get("evaluated"),
                best_reward=nas.get("best_reward"),
                trace=nas.get("trace", []),
                history=nas.get("history", []),
                front=[
                    dict(spec=p["spec"], params=p["params"], reward=p["reward"],
                         latency_ms=p["latency_ms"])
                    for p in nas.get("front", [])
                ],
            )
        )
        print(f"  [{args.mode} seed={seed}] best={nas.get('best_reward'):.3f} "
              f"evals={nas.get('evaluated')} {spec.describe()} ({runs[-1]['wall_s']:.0f}s)")

    out.write_text(json.dumps(dict(mode=args.mode, config=vars(args), runs=runs),
                              indent=2, default=float), encoding="utf-8")
    best = [r["best_reward"] for r in runs if r["best_reward"] is not None]
    print(f"[{args.mode}] {len(runs)} seeds  best reward mean {np.mean(best):.3f} "
          f"+- {np.std(best, ddof=1):.3f}  -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
