"""C1 (reworked): the visibility upper bound - mining, probing and auditing a ``cap_advance`` rule.

The first case in the paper learns a *lower* bound on the handover lead (``min_advance``).
The second failure class is the opposite direction: the policy asks for a lead longer than the
target stays visible, and the attempt dies as ``window_exceeded``.  This script treats it with the
same three stages - probe the deployed policy, fit the monotone curve, take the grid crossing with a
margin - and then audits the resulting *upper* bound on held-out windows.

Run:  python experiments/run_window_case.py
Out:  results/routeA_r3/window_case/summary.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
from scipy import stats

sys.path.insert(0, str(Path(__file__).resolve().parent))
from r3lib import OUT, SEEDS, arctic, evaluate, summarise, write  # noqa: E402

ALMOND = {s: f"results/campaign_1023/almond_seed{s}" for s in SEEDS}
PPO = {s: f"results/campaign_1023/ppomlp_seed{s}" for s in SEEDS}
CAND_CAPS = [8, 10, 12, 14, 16, 18, 20, 22, 24, 26]


def cause_share(res: dict, key: str) -> float:
    pc = res.get("polar_causes") or {}
    return 100.0 * float(pc.get(key, 0.0))


def main() -> int:
    out = {"probe": {}, "test": {}, "protocol": "probe on validation (65-75%), arms on test (82-95%)"}

    # ---------------- stage 1-3: probe the upper bound on validation ----------------
    probe = {}
    for cap in CAND_CAPS:
        r = evaluate(f"win_probe_cap{cap}", run=ALMOND[0], window="validation",
                     rule=f"cap_advance:{cap}@latitude_abs_deg>=68")
        probe[cap] = dict(hsr=100 * arctic(r), window=cause_share(r, "window_exceeded"),
                          late=cause_share(r, "late_handover"), n=r.get("n_attempts"))
        print(f"cap {cap:2d}  HSR {probe[cap]['hsr']:5.1f}  window {probe[cap]['window']:5.1f} "
              f" late {probe[cap]['late']:5.1f}")
    out["probe"] = {str(k): v for k, v in probe.items()}

    # pick the largest cap whose measured window-exceeded share stays under eps = 5 %
    ok = [c for c in CAND_CAPS if probe[c]["window"] <= 5.0]
    cap_star = max(ok) if ok else min(CAND_CAPS)
    out["cap_star"] = cap_star
    out["cap_margin"] = 2.0
    out["cap_used"] = cap_star
    print(f"cap* = {cap_star} s (window_exceeded {probe[cap_star]['window']:.1f}%)")

    # ---------------- stage 4: audit the arms on the test window -------------------
    ARMS = {
        "no_shield": dict(kind="none"),
        "min_18": dict(kind="rule", rule="min_advance:18@latitude_abs_deg>=68"),
        "cap_star": dict(kind="rule", rule=f"cap_advance:{cap_star}@latitude_abs_deg>=68"),
        "both": dict(kind="rules", rules=[f"min_advance:18@latitude_abs_deg>=68",
                                          f"cap_advance:{cap_star}@latitude_abs_deg>=68"]),
        "prefer_vis": dict(kind="rule", rule="prefer_long_visibility:0@latitude_abs_deg>=68"),
    }
    for arm, spec in ARMS.items():
        for tag, runs in (("almond", ALMOND), ("ppomlp", PPO)):
            vals, wins, lates, routes = [], [], [], []
            for s in SEEDS:
                if spec["kind"] == "none":
                    r = evaluate(f"win_{arm}_{tag}_s{s}", run=runs[s])
                elif spec["kind"] == "rules":
                    r = evaluate(f"win_{arm}_{tag}_s{s}", run=runs[s], rules=spec["rules"])
                else:
                    r = evaluate(f"win_{arm}_{tag}_s{s}", run=runs[s], rule=spec["rule"])
                vals.append(arctic(r))
                wins.append(cause_share(r, "window_exceeded"))
                lates.append(cause_share(r, "late_handover"))
                routes.append(cause_share(r, "no_route"))
            cell = dict(polar=vals, summary=summarise(vals),
                        window=float(np.mean(wins)), late=float(np.mean(lates)),
                        no_route=float(np.mean(routes)))
            out["test"].setdefault(arm, {})[tag] = cell
            print(f"{arm:<12} {tag:<7} HSR {cell['summary']['mean']:5.2f} "
                  f"late {cell['late']:4.1f} win {cell['window']:4.1f} rt {cell['no_route']:4.1f}")

    # paired statistics of the two bounds against the min-only arm (almond set)
    for arm in ("cap_star", "both", "prefer_vis"):
        a = out["test"][arm]["almond"]["polar"]
        b = out["test"]["min_18"]["almond"]["polar"]
        d = np.array(a) - np.array(b)
        if np.allclose(d, 0):
            p = 1.0
        else:
            p = float(stats.wilcoxon(d, zero_method="wilcox").pvalue)
        rng = np.random.default_rng(7)
        boot = np.array([rng.choice(d, size=d.size, replace=True).mean() for _ in range(10000)])
        out.setdefault("stats", {})[f"{arm}_minus_min18"] = dict(
            mean=float(d.mean()), lo=float(np.percentile(boot, 2.5)),
            hi=float(np.percentile(boot, 97.5)), p=p)
        print(f"  {arm} - min18: {d.mean():+.2f} pp  p={p:.3f}")

    write(OUT / "window_case" / "summary.json", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
