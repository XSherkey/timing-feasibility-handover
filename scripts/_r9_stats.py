"""R10 part 4: paired statistics for the isolation and lockbox tables."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from scipy import stats

ROOT = Path(__file__).resolve().parents[2] / "almond-repro"
iso = json.loads((ROOT / "results" / "routeA_r3" / "isolation" / "summary.json").read_text(encoding="utf-8"))
lk = json.loads((ROOT / "results" / "routeA_r3" / "lockbox_consistent" / "summary.json").read_text(encoding="utf-8"))
rng = np.random.default_rng(11)


def paired(a, b, reps=10000):
    a = np.asarray(a, float)
    b = np.asarray(b, float)
    d = a - b
    boot = np.array([rng.choice(d, size=d.size, replace=True).mean() for _ in range(reps)])
    lo, hi = np.percentile(boot, [2.5, 97.5])
    try:
        p = stats.wilcoxon(a, b, zero_method="wilcox").pvalue
    except ValueError:
        p = float("nan")
    return float(d.mean()), float(lo), float(hi), float(p)


print("=== isolation: arm - A0 (test window) ===")
a0 = iso["arms"]["A0_full"]["per_seed"]["eval"]
for arm in ["A1_hp3", "A2_lat60", "A3_random", "A4_nokm", "A5_nogate", "A7_probe_only", "A8_maxel"]:
    if arm not in iso["arms"]:
        continue
    v = iso["arms"][arm]["per_seed"]["eval"]
    m, lo, hi, p = paired(v, a0)
    print(f"{arm:14s} {m:+.3f} pp  [{lo:+.3f}, {hi:+.3f}]  p={p:.4f}")

print("\n=== lockbox: deployed - baseline (paired over seeds) ===")
for base in ["mined_16", "ppomlp_mined_16", "tuned_constant", "reward_lam8"]:
    for inst in ("eval", "lb299.25", "lb306.25", "lb290.25"):
        m, lo, hi, p = paired(lk["instances"][inst]["deployed_18"]["polar"],
                              lk["instances"][inst][base]["polar"])
        print(f"{base:16s} {inst:10s} {m:+.3f} [{lo:+.3f}, {hi:+.3f}] p={p:.4f}")
    print()
