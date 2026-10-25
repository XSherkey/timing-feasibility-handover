"""Reconcile the paper's naive-versus-KM numbers with the audit's stratified result.

The audit found the within-stratum bias to be ~0.0-0.2 s, while the paper quotes a
2.4 s aggregate gap (4.08 naive vs 6.45 KM).  This script recomputes both under the
combinations that could explain the difference (latitude cut-off, arm set) so the
paper can report the right decomposition.
"""
from __future__ import annotations

import glob
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from km_setup_time import km, quantile  # noqa: E402


def load(root: str) -> list[dict]:
    out = []
    for p in sorted(glob.glob(str(Path(root) / "*_seed*" / "run_summary.json"))):
        d = json.load(open(p, encoding="utf-8"))
        if d.get("ok"):
            for a in d["final"]["attempts"]:
                a["_arm"] = Path(p).parent.name.rsplit("_seed", 1)[0]
                out.append(a)
    return out


def naive_km(atts: list[dict]) -> dict:
    succ = [float(a["t_setup_s"]) for a in atts
            if a["success"] and a.get("t_setup_s") is not None and np.isfinite(a["t_setup_s"])]
    times, events = [], []
    for a in atts:
        adv = float(a["handover_advance_s"])
        if a["success"]:
            ts = a.get("t_setup_s")
            if ts is None or not np.isfinite(ts):
                continue
            times.append(float(ts)); events.append(1)
        elif a.get("cause") == "late_handover":
            times.append(adv); events.append(0)
    t, e = np.asarray(times), np.asarray(events)
    if not t.size:
        return dict(n=0)
    g, s = km(t, e)
    return dict(n=int(t.size), successes=len(succ),
                naive_p50=float(np.median(succ)) if succ else float("nan"),
                naive_p95=float(np.percentile(succ, 95)) if succ else float("nan"),
                km_p50=quantile(g, s, 0.5), km_p90=quantile(g, s, 0.10),
                km_p95=quantile(g, s, 0.05))


def main() -> int:
    atts = load(str(ROOT / "results" / "campaign_1023"))
    rows = []
    for lat in (70.0, 68.0):
        for arms in (None, ("almond", "almond_fixedarch")):
            sel = [a for a in atts if abs(float(a["latitude_abs_deg"])) >= lat
                   and (arms is None or a["_arm"] in arms)]
            r = naive_km(sel)
            r.update(lat_cut=lat, arms="all" if arms is None else "almond*")
            rows.append(r)
    json.dump(rows, open(ROOT / "results" / "routeA_r2" / "km_reconcile.json", "w",
                         encoding="utf-8"), indent=2)
    print(f"{'lat':>5} {'arms':>8} {'n':>7} {'naive50':>9} {'km50':>8} {'naive95':>9} {'km95':>8}")
    for r in rows:
        print(f"{r['lat_cut']:>5} {r['arms']:>8} {r['n']:>7} {r['naive_p50']:>9.2f} "
              f"{r['km_p50']:>8.2f} {r['naive_p95']:>9.2f} {r['km_p95']:>8.2f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
