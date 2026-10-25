"""Merge sweep files and print the rendered seed prompt (verification helper).

Two jobs in one process start, because on this machine every interpreter start is
expensive:

1. merge ``sweep_*_v2.json`` and ``sweep_*_v2b.json`` into one file per arm;
2. render the topology-seed prompt with a representative payload, so it can be
   checked that the model really receives the measured regime statistics, the
   design brief and the evaluation table (the call log stores responses only).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def merge(parts: list[Path], out: Path) -> int:
    runs, config = [], None
    for p in parts:
        if not p.exists():
            continue
        d = json.loads(p.read_text(encoding="utf-8"))
        runs.extend(d.get("runs", []))
        config = config or d.get("config")
    runs.sort(key=lambda r: r.get("seed", 0))
    out.write_text(json.dumps(dict(config=config, runs=runs, merged=[p.name for p in parts]),
                              indent=2, default=str), encoding="utf-8")
    rewards = [r["best_reward"] for r in runs if r.get("best_reward") is not None]
    mean = sum(rewards) / len(rewards) if rewards else float("nan")
    print(f"{out.name}: {len(runs)} seeds, mean best {mean:.2f}")
    return len(runs)


def show_prompt() -> None:
    from almond.llm.prompts import render_prompt

    payload = dict(
        regime_tags=dict(polar=True, sparse_isl=True),
        regime_hint="sparse polar connectivity; prefer graph convolution over attention",
        design_brief="a design that conditions on edge semantics instead of treating all edges alike",
        regime_stats=dict(polar_sites=5, no_route_fraction=0.035, hop_p50=0.0, hop_p90=1.0,
                          visibility_below_60s_fraction=0.017, elevation_p50_deg=30.1),
        task=dict(task="LEO handover control", constraints=["parameters <= 50000"]),
        history=[dict(kind="gcn", width=64, layers=2, params=27029, satisfaction=63.3,
                      arctic_hsr=68.8, diag=dict(advance_min_bucket_fraction=0.731))],
    )
    user = render_prompt("topology_seed", payload)["user"]
    print("\n--- rendered topology_seed prompt (first 1400 chars) ---")
    print(user[:1400])
    checks = {
        "measured regime statistics": "no_route_fraction" in user,
        "design brief": "design brief" in user.lower(),
        "evaluation table": "satisfaction" in user,
        "new switches documented": "edge_types" in user and "head_width" in user,
        "no unresolved placeholder": "<" + "regime_stats>" not in user,
    }
    print("\n--- prompt content checks ---")
    for k, v in checks.items():
        print(f"  {k:<28} {v}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--merge", action="store_true")
    ap.add_argument("--prompt", action="store_true")
    args = ap.parse_args()
    if args.merge:
        nas = ROOT / "results" / "nas"
        n = merge([nas / "sweep_llm_v2.json", nas / "sweep_llm_v2b.json"], nas / "sweep_llm_all.json")
        m = merge([nas / "sweep_random_v2.json", nas / "sweep_random_v2b.json"], nas / "sweep_random_all.json")
        print(f"merged arms: llm {n} seeds, random {m} seeds")
    if args.prompt:
        show_prompt()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
