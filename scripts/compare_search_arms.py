"""Compare two search arms (LLM-seeded vs unseeded) under one protocol.

Outputs the paired per-seed comparison, the anytime metrics at fixed evaluation
budgets, and a plain statement of what is and is not resolvable with the number
of seeds available.  Kept deliberately conservative: with five seeds a paired
difference is reported with its exact win/loss count rather than a p-value that
would be over-read.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
BUDGETS = (5, 10, 20, 40)


def load(p: Path) -> dict:
    return json.loads(p.read_text(encoding="utf-8"))


def best_at(trace: list[dict], budget: int) -> float:
    """Best-so-far objective after ``budget`` evaluations."""
    if not trace:
        return float("nan")
    seen = [t["best_reward"] for t in trace if t.get("evals", 0) <= budget]
    if not seen:
        return float(trace[0]["best_reward"])
    return float(max(seen))


def hv_at(trace: list[dict], budget: int, param_budget: int = 50_000) -> float:
    """Two-dimensional hypervolume of (satisfaction, parameter cost) at a budget.

    Reconstructed from the trace, because only the per-generation snapshots stored
    hypervolume.  Cost axis runs from 0 to 1 (parameter budget), gain is the
    objective; the value is the area dominated by the evaluated points.
    """
    pts = [(min(1.0, t["params"] / param_budget), t["reward"])
           for t in trace if t.get("evals", 0) <= budget and "params" in t]
    if not pts:
        return float("nan")
    pts.sort()
    hv, best = 0.0, 0.0
    for i, (cost, gain) in enumerate(pts):
        best = max(best, gain)
        nxt = pts[i + 1][0] if i + 1 < len(pts) else 1.0
        hv += best * max(0.0, nxt - cost)
    return float(hv)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--llm", default="results/nas/sweep_llm.json")
    ap.add_argument("--random", default="results/nas/sweep_random.json")
    ap.add_argument("--out", default="results/nas/arm_comparison.json")
    args = ap.parse_args()

    A = load(ROOT / args.llm)
    B = load(ROOT / args.random)
    ra = {r["seed"]: r for r in A.get("runs", [])}
    rb = {r["seed"]: r for r in B.get("runs", [])}
    seeds = sorted(set(ra) & set(rb))
    if not seeds:
        print("no overlapping seeds")
        return 1

    print(f"seeds compared: {seeds}")
    print(f"protocol: {json.dumps(A.get('config', {}), default=str)[:300]}\n")

    rows = []
    print(f"{'seed':>4}{'LLM best':>10}{'rand best':>10}{'delta':>8}"
          f"{'evals→LLM':>11}{'evals→rand':>12}")
    for s in seeds:
        a, b = ra[s], rb[s]
        ba = max((t["reward"] for t in a.get("trace", [])), default=float("nan"))
        bb = max((t["reward"] for t in b.get("trace", [])), default=float("nan"))
        rows.append(dict(seed=s, llm=ba, random=bb, delta=ba - bb,
                         llm_spec=a.get("spec", {}), random_spec=b.get("spec", {}),
                         llm_evals=a.get("evaluated"), random_evals=b.get("evaluated")))
        print(f"{s:>4}{ba:>10.1f}{bb:>10.1f}{ba - bb:>+8.1f}")

    d = np.array([r["delta"] for r in rows], dtype=float)
    wins = int((d > 0).sum())
    print(f"\npaired deltas: mean {d.mean():+.2f}, median {np.median(d):+.2f}, "
          f"LLM better in {wins}/{len(d)} seeds")
    print(f"LLM  mean {np.mean([r['llm'] for r in rows]):.1f} ± "
          f"{np.std([r['llm'] for r in rows], ddof=1):.1f}")
    print(f"rand mean {np.mean([r['random'] for r in rows]):.1f} ± "
          f"{np.std([r['random'] for r in rows], ddof=1):.1f}")

    print("\nanytime objective (mean over seeds) at fixed evaluation budgets:")
    header = f"{'budget':>7}{'LLM':>9}{'random':>9}{'delta':>8}"
    print(header)
    anytime = {}
    for b in BUDGETS:
        la = np.nanmean([best_at(ra[s].get("trace", []), b) for s in seeds])
        lb = np.nanmean([best_at(rb[s].get("trace", []), b) for s in seeds])
        anytime[b] = dict(llm=float(la), random=float(lb), delta=float(la - lb))
        print(f"{b:>7}{la:>9.1f}{lb:>9.1f}{la - lb:>+8.1f}")

    print("\nanytime hypervolume (mean over seeds):")
    hv = {}
    for b in BUDGETS:
        la = np.nanmean([hv_at(ra[s].get("trace", []), b) for s in seeds])
        lb = np.nanmean([hv_at(rb[s].get("trace", []), b) for s in seeds])
        hv[b] = dict(llm=float(la), random=float(lb), delta=float(la - lb))
        print(f"{b:>7}{la:>9.3f}{lb:>9.3f}{la - lb:>+8.3f}")

    # a paired sign test is the honest summary at n = 5
    from math import comb

    k = max(wins, len(d) - wins)
    p_two = min(1.0, 2 * sum(comb(len(d), i) for i in range(k, len(d) + 1)) / 2 ** len(d))
    print(f"\nsign test on the paired deltas: {wins}/{len(d)} wins, two-sided p = {p_two:.2f}")

    out = dict(seeds=seeds, rows=rows, paired_mean=float(d.mean()),
               paired_median=float(np.median(d)), wins=wins, n=len(d),
               anytime=anytime, anytime_hv=hv, sign_test_p=float(p_two),
               protocol=A.get("config", {}))
    p = ROOT / args.out
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    print("wrote", p.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
