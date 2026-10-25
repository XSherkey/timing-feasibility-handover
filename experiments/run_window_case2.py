"""C1 (revised, protocol-identical): the visibility-relative upper bound, ``cap_advance_vis``.

A constant cap does not bind in the polar band (the policy's own lead is already below 16 s), so the
second rule caps the lead at ``remaining_visibility - g`` and the calibrated parameter is the guard g.
Everything below goes through ``eval_shield`` so the numbers are directly comparable with every other
table in the paper.

Run:  python experiments/run_window_case2.py
Out:  results/routeA_r3/window_case2/summary.json
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from scipy import stats

sys.path.insert(0, str(Path(__file__).resolve().parent))
from r3lib import OUT, SEEDS, arctic, evaluate, summarise, write  # noqa: E402

ALMOND = {s: f"results/campaign_1023/almond_seed{s}" for s in SEEDS}
PPO = {s: f"results/campaign_1023/ppomlp_seed{s}" for s in SEEDS}
GUARDS = [0.0, 2.0, 4.0, 6.0, 8.0, 10.0]


def share(res, key):
    return 100.0 * float((res.get("polar_causes") or {}).get(key, 0.0))


def main() -> int:
    out = {"guards": GUARDS}

    # ---- stage 1-3: probe the guard on the validation window --------------
    probe = {}
    for g in GUARDS:
        r = evaluate(f"win2_probe_g{g:g}", run=ALMOND[0], window="validation",
                     rule=f"cap_advance_vis:{g:g}@latitude_abs_deg>=68")
        probe[g] = dict(hsr=100 * arctic(r), window=share(r, "window_exceeded"),
                        late=share(r, "late_handover"), n=r.get("n_attempts"))
        print(f"guard {g:4.1f}  HSR {probe[g]['hsr']:5.1f}  win {probe[g]['window']:4.1f} "
              f"late {probe[g]['late']:4.1f}  n {probe[g]['n']}")
    base = evaluate("win2_probe_none", run=ALMOND[0], window="validation")
    out["probe_none"] = dict(hsr=100 * arctic(base), window=share(base, "window_exceeded"),
                             late=share(base, "late_handover"))
    print(f"no cap      HSR {out['probe_none']['hsr']:5.1f}  win {out['probe_none']['window']:4.1f} "
          f"late {out['probe_none']['late']:4.1f}")
    out["probe"] = {str(k): v for k, v in probe.items()}

    ok = [g for g in GUARDS if probe[g]["hsr"] >= out["probe_none"]["hsr"] - 2.0]
    g_star = min(ok, key=lambda g: (probe[g]["window"], -probe[g]["hsr"])) if ok else 2.0
    out["guard_star"] = g_star
    print(f"guard* = {g_star}")

    # ---- stage 4: audit on the test window --------------------------------
    ARMS = {
        "no_shield": dict(),
        "cap_vis": dict(rule=f"cap_advance_vis:{g_star:g}@latitude_abs_deg>=68"),
        "min_18": dict(rule="min_advance:18@latitude_abs_deg>=68"),
        "min_18_plus_cap": dict(rules=["min_advance:18@latitude_abs_deg>=68",
                                       f"cap_advance_vis:{g_star:g}@latitude_abs_deg>=68"]),
    }
    for arm, spec in ARMS.items():
        for tag, runs in (("almond", ALMOND), ("ppomlp", PPO)):
            vals, wins, lates, routes = [], [], [], []
            for s in SEEDS:
                kw = {}
                if "rule" in spec:
                    kw["rule"] = spec["rule"]
                if "rules" in spec:
                    kw["rules"] = spec["rules"]
                r = evaluate(f"win2_{arm}_{tag}_s{s}", run=runs[s], **kw)
                vals.append(arctic(r))
                wins.append(share(r, "window_exceeded"))
                lates.append(share(r, "late_handover"))
                routes.append(share(r, "no_route"))
            out.setdefault("test", {}).setdefault(arm, {})[tag] = dict(
                polar=vals, summary=summarise(vals),
                window=float(np.mean(wins)), late=float(np.mean(lates)), no_route=float(np.mean(routes)))
            c = out["test"][arm][tag]
            print(f"{arm:<16} {tag:<7} HSR {c['summary']['mean']:6.2f} ± {c['summary']['sd']:4.2f}  "
                  f"late {c['late']:4.1f}  win {c['window']:4.1f}  rt {c['no_route']:4.1f}")

    for arm in ("cap_vis", "min_18_plus_cap"):
        a = np.array(out["test"][arm]["almond"]["polar"])
        b = np.array(out["test"]["min_18"]["almond"]["polar"])
        d = a - b
        p = 1.0 if np.allclose(d, 0) else float(stats.wilcoxon(d, zero_method="wilcox").pvalue)
        rng = np.random.default_rng(13)
        boot = np.array([rng.choice(d, size=d.size, replace=True).mean() for _ in range(10000)])
        out.setdefault("stats", {})[f"{arm}_minus_min18"] = dict(
            mean=float(d.mean()), lo=float(np.percentile(boot, 2.5)),
            hi=float(np.percentile(boot, 97.5)), p=p)
        print(f"  {arm} - min18: {d.mean():+.2f} pp  CI [{np.percentile(boot,2.5):+.2f},"
              f" {np.percentile(boot,97.5):+.2f}]  p={p:.3f}")

    write(OUT / "window_case2" / "summary.json", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
