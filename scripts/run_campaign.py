"""Experiment campaign runner for the ALMOND reproduction.

Every method is expressed as an :class:`AlmondConfig` variant so that the
comparison is the *same* pipeline with components switched off, which is what
makes the factorial ablation (Table 8) honest.

Usage
-----
    python scripts/run_campaign.py --methods almond,ppomlp --seeds 0,1,2
    python scripts/run_campaign.py --methods all --seeds 0-9 --out results/campaign

A per-run JSON is written immediately so a crashed campaign loses only the run
in flight.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import traceback
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from almond.framework.system import AlmondConfig, AlmondSystem

#: method name -> (variant, extra config overrides)
METHODS = {
    "almond": ("full", {}),
    "almond_fixedarch": ("fixed_arch", {}),
    "no_forensics": ("no_forensics", {}),
    "no_memory": ("no_memory", {}),
    "no_counterfactual": ("no_counterfactual", {}),
    "no_nas": ("no_nas", {}),
    "ppomlp": ("handcrafted", {"nas_generations": 0, "nas_population": 1, "forensics_after": 10**9}),
    "static_llm": ("static_llm", {"nas_generations": 0, "nas_population": 1, "forensics_after": 10**9}),
    "eureka": ("eureka", {"nas_generations": 0, "nas_population": 1}),
    "oracle": ("oracle", {"nas_generations": 0, "nas_population": 1}),
    "unseeded_evonas": ("no_nas", {}),
}

MAIN_METHODS = (
    "almond",
    "almond_fixedarch",
    "ppomlp",
    "static_llm",
    "eureka",
    "oracle",
    "unseeded_evonas",
    "no_forensics",
)


def parse_seeds(spec: str) -> list[int]:
    out: list[int] = []
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            a, b = part.split("-")
            out.extend(range(int(a), int(b) + 1))
        else:
            out.append(int(part))
    return out


def run_one(method: str, seed: int, out_root: Path, base: dict) -> dict:
    variant, extra = METHODS[method]
    out = out_root / f"{method}_seed{seed}"
    out.mkdir(parents=True, exist_ok=True)
    if (out / "run_summary.json").exists() and not base.get("force", False):
        return json.loads((out / "run_summary.json").read_text(encoding="utf-8"))
    cfg = AlmondConfig(variant=variant, seed=seed, out_dir=str(out))
    for k, v in base.items():
        if k in cfg.__dataclass_fields__ and k != "force":
            setattr(cfg, k, v)
    # method-specific overrides win over the CLI defaults
    for k, v in extra.items():
        setattr(cfg, k, v)
    if base.get("spec_file"):
        cfg.fixed_spec = json.loads(Path(base["spec_file"]).read_text(encoding="utf-8"))
    t0 = time.time()
    try:
        system = AlmondSystem(cfg, out_dir=out)
        res = system.run()
        res["method"] = method
        res["ok"] = True
    except Exception as exc:  # pragma: no cover - campaign robustness
        res = dict(method=method, seed=seed, ok=False, error=str(exc), traceback=traceback.format_exc())
    res["wall_s"] = time.time() - t0
    (out / "run_summary.json").write_text(json.dumps(res, indent=2, default=float), encoding="utf-8")
    return res


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--methods", default=",".join(MAIN_METHODS))
    ap.add_argument("--seeds", default="0-9")
    ap.add_argument("--out", default=None)
    ap.add_argument("--episodes", type=int, default=300)
    ap.add_argument("--batch", type=int, default=24)
    ap.add_argument("--steps", type=int, default=240)
    ap.add_argument("--eval-every", type=int, default=25)
    ap.add_argument("--forensics-after", type=int, default=25)
    ap.add_argument("--nas-generations", type=int, default=4)
    ap.add_argument("--nas-population", type=int, default=10)
    ap.add_argument("--nas-eval-episodes", type=int, default=40)
    ap.add_argument("--nas-batch", type=int, default=8)
    ap.add_argument("--device", default="cuda")
    ap.add_argument("--twin-tag", default="ref")
    ap.add_argument("--twin-hours", type=float, default=12.0)
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--spec-file", default=None, help="reuse a pre-discovered architecture")
    ap.add_argument("--lr", type=float, default=3e-4)
    ap.add_argument("--ent-coef", type=float, default=0.01)
    ap.add_argument("--rollout-steps", type=int, default=256)
    ap.add_argument("--epochs", type=int, default=4)
    # regime-perturbation knobs (theory: the mined threshold must track the physics)
    ap.add_argument("--acq-signaling", type=float, default=None,
                    help="override the link-acquisition signalling time (s)")
    ap.add_argument("--acq-sync", type=float, default=None, help="override the sync base time (s)")
    ap.add_argument("--seam-penalty", type=float, default=None,
                    help="override the cross-plane penalty above the seam (s)")
    # twin-level physical overrides (the tag alone does NOT change the physics)
    ap.add_argument("--feeder-slots", type=int, default=None)
    ap.add_argument("--no-seam", action="store_true", help="disable the polar seam penalty in the twin")
    ap.add_argument("--isl-dropout", type=float, default=None)
    ap.add_argument("--constellation", default=None)
    # Probe-Calibrated Shield (PCS): measured magnitude instead of the LLM's
    ap.add_argument("--probe-calibrated", action="store_true",
                    help="replace the mined magnitude with an actively probed threshold")
    ap.add_argument("--probe-eps", type=float, default=0.05)
    ap.add_argument("--probe-episodes", type=int, default=2,
                    help="episodes per advance in the PCS probe (F4: 8 halves the threshold noise)")
    # penalty-vs-shield contrast: same knowledge, injected into the reward instead
    ap.add_argument("--late-risk-tau", type=float, default=0.0)
    ap.add_argument("--late-risk-lat", type=float, default=68.0)
    ap.add_argument("--late-risk-weight", type=float, default=0.0)
    # cost of early preparation (dual-homing); 0 keeps the legacy "lead is free" twin
    ap.add_argument("--dh-latency-ms-per-s", type=float, default=0.0)
    ap.add_argument("--dh-power-per-s", type=float, default=0.0)
    args = ap.parse_args()

    out_root = Path(args.out or (Path(__file__).resolve().parents[1] / "results" / "campaign"))
    out_root.mkdir(parents=True, exist_ok=True)
    methods = [m.strip() for m in args.methods.split(",") if m.strip()]
    if methods == ["all"]:
        methods = list(MAIN_METHODS)
    seeds = parse_seeds(args.seeds)
    base = dict(
        episodes=args.episodes,
        batch=args.batch,
        episode_steps=args.steps,
        eval_every=args.eval_every,
        forensics_after=args.forensics_after,
        nas_generations=args.nas_generations,
        nas_population=args.nas_population,
        nas_eval_episodes=args.nas_eval_episodes,
        nas_batch=args.nas_batch,
        device=args.device,
        twin_tag=args.twin_tag,
        twin_hours=args.twin_hours,
        force=args.force,
        spec_file=args.spec_file,
        acq_signaling_s=args.acq_signaling,
        acq_sync_base_s=args.acq_sync,
        seam_penalty_s=args.seam_penalty,
        feeder_slots=args.feeder_slots,
        isl_seam_enabled=(False if args.no_seam else None),
        isl_dropout=args.isl_dropout,
        constellation=args.constellation,
        probe_calibrated=args.probe_calibrated,
        probe_eps=args.probe_eps,
        probe_episodes=args.probe_episodes,
        late_risk_tau=args.late_risk_tau,
        late_risk_lat=args.late_risk_lat,
        late_risk_weight=args.late_risk_weight,
        dual_homing_latency_ms_per_s=args.dh_latency_ms_per_s,
        dual_homing_power_per_s=args.dh_power_per_s,
    )
    index = out_root / "index.jsonl"
    print(f"[campaign] {len(methods)} methods x {len(seeds)} seeds -> {out_root}")
    for method in methods:
        for seed in seeds:
            print(f"[campaign] {method} seed={seed} ...", flush=True)
            res = run_one(method, seed, out_root, base)
            ok = res.get("ok", False)
            fin = res.get("final", {}) if ok else {}
            msg = ""
            if ok and fin:
                msg = (
                    f"arctic={fin.get('arctic', {}).get('hsr', float('nan')) * 100:5.1f}% "
                    f"mid={fin.get('midlat', {}).get('hsr', float('nan')) * 100:5.1f}% "
                    f"S={fin.get('satisfaction', float('nan')):5.1f}"
                )
            print(f"[campaign]   {'ok' if ok else 'FAIL'} {msg} ({res.get('wall_s', 0):.0f}s)", flush=True)
            with index.open("a", encoding="utf-8") as fh:
                fh.write(
                    json.dumps(
                        dict(method=method, seed=seed, ok=ok, wall_s=res.get("wall_s"),
                             error=res.get("error"), final=res.get("final")),
                        default=float,
                    )
                    + "\n"
                )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
