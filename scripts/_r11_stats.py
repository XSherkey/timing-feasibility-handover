"""R12 part 1: statistics the reviewer asked to see in the tables."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from scipy import stats

ROOT = Path(__file__).resolve().parents[2] / "almond-repro"
iso = json.loads((ROOT / "results" / "routeA_r3" / "isolation" / "summary.json").read_text(encoding="utf-8"))
h = json.loads((ROOT / "results" / "routeA_r3" / "headline_consistent" / "summary.json").read_text(encoding="utf-8"))
dm = json.loads((ROOT / "results" / "routeA_r3" / "drift_margin" / "summary.json").read_text(encoding="utf-8"))
rng = np.random.default_rng(5)


def ci(d, reps=10000):
    d = np.asarray(d, float)
    boot = np.array([rng.choice(d, size=d.size, replace=True).mean() for _ in range(reps)])
    return np.percentile(boot, [2.5, 97.5])


def tost_p(d, margin=1.0):
    """Two one-sided tests: is |mean difference| < margin?"""
    d = np.asarray(d, float)
    n = d.size
    se = d.std(ddof=1) / np.sqrt(n) if n > 1 else 0.0
    if se == 0:
        return 0.0 if abs(d.mean()) < margin else 1.0
    t1 = (d.mean() + margin) / se      # H0: mu <= -margin
    t2 = (margin - d.mean()) / se      # H0: mu >= +margin
    return float(max(1 - stats.norm.cdf(t1), 1 - stats.norm.cdf(t2)))


a0 = iso["arms"]["A0_full"]["per_seed"]["eval"]
print("arm  delta   CI            p_wilcox  TOST(margin 1.0)")
for arm, lab in [("A1_human", "A1"), ("A2_grid", "A2"), ("A3_randomBest", "A3"), ("A4_noKM", "A4"),
                 ("A5_noGate", "A5"), ("A7_probeOnly", "A7"), ("A8_constantProbe", "A8")]:
    v = np.array(iso["arms"][arm]["per_seed"]["eval"]) - np.array(a0)
    lo, hi = ci(v)
    try:
        pw = stats.wilcoxon(v, zero_method="wilcox").pvalue if np.any(v != 0) else 1.0
    except ValueError:
        pw = 1.0
    print(f"{lab}  {v.mean():+.3f}  [{lo:+.3f},{hi:+.3f}]  {pw:.3f}   {tost_p(v):.3f}")

print("\nVI: cross-intent Holm over three intents")
p_raw = 0.0039
print("raw p =", p_raw, "Holm (3 tests) =", min(1.0, 3 * p_raw))

print("\nV: drift CI, fixed vs re-probed")
for r in ("3.2", "4.4", "5.6"):
    fx = np.array(dm["regimes"][r]["arms"]["shield_fixed18"]["polar"]) if "shield_fixed18" in dm["regimes"][r]["arms"] else None
    rp = np.array(dm["regimes"][r]["arms"]["shield_probed"]["polar"]) if "shield_probed" in dm["regimes"][r]["arms"] else None
    if fx is not None and rp is not None:
        d = rp - fx
        lo, hi = ci(d)
        print(f"+{r}s  {d.mean():+.2f} [{lo:+.2f},{hi:+.2f}]")
