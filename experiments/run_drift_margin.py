"""T2-03/T2-07 - drift ladder and margin study at n = 10, plus the probe-calibrated constant (A8).

Regimes are the acquisition-signalling values in the manifest (1.2 s nominal, then +2.0, +3.2 and
+4.4 s of drift).  Arms:
  * ``const_fixed18``  - highest-elevation controller, fixed 18 s lead, no re-probe (the tuned constant)
  * ``const_probed``   - same controller, lead re-probed on the drifted twin (+2 s margin)   [A8]
  * ``shield_fixed18`` - deployed policy + 18 s shield rule, no re-probe
  * ``shield_probed``  - deployed policy + shield at the re-probed threshold (+2 s margin)
Margins m in {0, 2, 4} s are swept on the probe-calibrated shield at every regime.

Run:  python experiments/run_drift_margin.py
Out:  results/routeA_r3/drift_margin/summary.json
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from r3lib import DRIFT_ACQ, MANIFEST, OUT, SEEDS, arctic, evaluate, paired_stats, summarise, write

ALMOND = {s: f"results/campaign_1023/almond_seed{s}" for s in SEEDS}
NOMINAL = MANIFEST["physics_nominal_acq_signaling"]
MARGINS = MANIFEST["margin_s"]


def probe_threshold(acq: float, seeds: list[int]) -> dict[int, float]:
    """Per-seed tau*: archived probes where available, else the regime mode from the archive."""
    archived = {}
    for s in seeds:
        for pat in (f"results/routeA_g3/probe_s{s}_acq{acq:g}.json",
                    f"results/routeA_h2/probe_s{s}_sig32.json" if abs(acq - 3.2) < 1e-9 else "",
                    f"results/routeA_h2/probe_s{s}_drift44.json" if abs(acq - 4.4) < 1e-9 else "",
                    f"results/routeA_h2/probe_s{s}_ref.json" if abs(acq - 1.2) < 1e-9 else ""):
            p = Path(pat) if pat else None
            if p and p.exists():
                archived[s] = float(json.loads(p.read_text(encoding="utf-8"))["tau_star"])
                break
    known = [v for v in archived.values()]
    mode = float(np.median(known)) if known else {1.2: 16.0, 3.2: 18.0, 4.4: 20.0, 5.6: 22.0}[acq]
    return {s: archived.get(s, mode) for s in seeds}


def main() -> int:
    out = dict(regimes={}, margins={}, probes={})
    for acq in DRIFT_ACQ:
        taus = probe_threshold(acq, SEEDS)
        out["probes"][f"{acq:g}"] = taus
        tau_mode = float(np.median(list(taus.values())))
        regime = {"acq_signaling_s": acq, "drift_s": round(acq - NOMINAL, 2),
                  "tau_star": taus, "tau_mode": tau_mode, "arms": {}}
        for name, kw in (
            ("const_fixed18", dict(policy="maxel", lead=18.0)),
            ("const_probed", dict(policy="maxel", lead=tau_mode + 2.0)),
            ("shield_fixed18", dict(rule="min_advance:18@latitude_abs_deg>=68")),
            ("shield_probed", dict(rule=f"min_advance:{tau_mode + 2:g}@latitude_abs_deg>=68")),
        ):
            vals = []
            for s in SEEDS:
                if kw.get("policy") == "maxel":
                    r = evaluate(f"drift_{acq:g}_{name}_s{s}", policy="maxel", lead=kw["lead"], acq=acq)
                else:
                    r = evaluate(f"drift_{acq:g}_{name}_s{s}", run=ALMOND[s], rule=kw["rule"], acq=acq)
                vals.append(arctic(r))
            regime["arms"][name] = dict(polar=vals, summary=summarise(vals))
        # margin sweep on the probe-calibrated shield
        regime["margin"] = {}
        for m in MARGINS:
            rule = f"min_advance:{tau_mode + m:g}@latitude_abs_deg>=68"
            vals = [arctic(evaluate(f"margin_{acq:g}_m{m:g}_s{s}", run=ALMOND[s], rule=rule, acq=acq))
                    for s in SEEDS]
            regime["margin"][f"m{m:g}"] = dict(rule=rule, polar=vals, summary=summarise(vals))
        out["regimes"][f"{acq:g}"] = regime
        print(f"acq {acq:g}: const18 {regime['arms']['const_fixed18']['summary']['mean']:.2f} "
              f"constProbe {regime['arms']['const_probed']['summary']['mean']:.2f} "
              f"shield18 {regime['arms']['shield_fixed18']['summary']['mean']:.2f} "
              f"shieldProbe {regime['arms']['shield_probed']['summary']['mean']:.2f}")

    # contrasts at the largest drift
    worst = out["regimes"][f"{max(DRIFT_ACQ):g}"]
    out["contrast_fixed_vs_probed_at_max_drift"] = paired_stats(
        worst["arms"]["shield_probed"]["polar"], worst["arms"]["shield_fixed18"]["polar"])
    out["contrast_constant_vs_shield_at_max_drift"] = paired_stats(
        worst["arms"]["shield_probed"]["polar"], worst["arms"]["const_probed"]["polar"])
    write(OUT / "drift_margin" / "summary.json", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
