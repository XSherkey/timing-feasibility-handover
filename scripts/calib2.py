"""Calibrate the link-acquisition-time model against the twin geometry.

Target statements from the manuscript (Sec. 4.2, abstract):

* a minimum handover advance of about 10-12 s is required at low elevation in
  the Arctic;
* injection of that rule raises Arctic success above 90-95%, while preparation
  below 12 s leaves Arctic success under 60% (the naive-baseline regime);
* mid-latitude service is insensitive to the advance.

This script reports the acquisition-time distribution per latitude so the
physical coefficients can be chosen to reproduce those statements *before* any
reinforcement learning is run.
"""
from __future__ import annotations

import argparse
import itertools
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from almond.twin.geometry import link_acquisition_time_s
from almond.twin.twin import DigitalTwin, TwinConfig

BASE = dict(
    t_signaling_s=1.8,
    t_sync_base_s=0.8,
    doppler_coeff_s=0.00020,
    hop_coeff_s=0.42,
    low_el_coeff_s=2.0,
    t_slot_s=0.9,
)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", default="cal")
    ap.add_argument("--hours", type=float, default=1.5)
    ap.add_argument("--dt", type=float, default=10.0)
    ap.add_argument("--feeder-slots", type=int, default=8)
    ap.add_argument("--sweep", action="store_true", help="sweep low_el/hop/t_slot coefficients")
    args = ap.parse_args()

    cfg = TwinConfig(
        horizon_s=args.hours * 3600, dt_s=args.dt, tag=args.tag, feeder_slots=args.feeder_slots
    )
    twin = DigitalTwin(cfg).build()
    el, hop, doprate, press = twin["el"], twin["hop"], twin["doprate"], twin["feed_press"]
    slots = cfg.feeder_slots

    groups = {
        "arctic>70": [i for i in twin.user_site_index if abs(twin.sites[i].lat_deg) > 70],
        "subarctic 65-70": [i for i in twin.user_site_index if 65 <= abs(twin.sites[i].lat_deg) <= 70],
        "midlat 30-65": [i for i in twin.user_site_index if 30 <= abs(twin.sites[i].lat_deg) < 65],
        "equatorial<30": [i for i in twin.user_site_index if abs(twin.sites[i].lat_deg) < 30],
    }

    def stats(params):
        out = {}
        for gname, idxs in groups.items():
            acq_hi, acq_lo, noh, noPath = [], [], [], []
            for si in idxs:
                e = el[si]
                vis = e > cfg.elev_mask_deg
                reach = vis & (hop >= 0)
                acq = link_acquisition_time_s(
                    np.deg2rad(e), doprate[si], hop, press[si], feeder_slots=slots, **params
                )
                hi = reach & (e > 25.0)
                lo = reach & (e > 10.0) & (e < 15.0)
                if hi.any():
                    acq_hi.append(acq[hi])
                if lo.any():
                    acq_lo.append(acq[lo])
                noPath.append(((hop < 0) & vis).sum() / max(vis.sum(), 1))
            a_hi = np.concatenate(acq_hi) if acq_hi else np.array([np.nan])
            a_lo = np.concatenate(acq_lo) if acq_lo else np.array([np.nan])
            out[gname] = dict(
                hi50=np.percentile(a_hi, 50),
                lo50=np.percentile(a_lo, 50),
                lo90=np.percentile(a_lo, 90),
                lo95=np.percentile(a_lo, 95),
                nopath=float(np.mean(noPath)) * 100,
            )
        return out

    if args.sweep:
        print("sweeping coefficients (looking for arctic arctic_lo50~9, lo95~12, mid lat lo50~5)\n")
        rows = []
        for low, hc, ts in itertools.product([1.5, 2.0, 2.5], [0.35, 0.42, 0.55], [0.7, 0.9, 1.2]):
            p = dict(BASE, low_el_coeff_s=low, hop_coeff_s=hc, t_slot_s=ts)
            s = stats(p)
            a, m = s["arctic>70"], s["midlat 30-65"]
            rows.append((low, hc, ts, a["lo50"], a["lo95"], m["lo50"], m["hi50"]))
            print(
                f"low={low:4.1f} hop={hc:4.2f} slot={ts:4.2f} | "
                f"arctic lo50={a['lo50']:5.1f} lo95={a['lo95']:5.1f} | "
                f"mid lo50={m['lo50']:5.1f} hi50={m['hi50']:5.1f}"
            )
        return 0

    s = stats(BASE)
    print(f"feeder_slots={slots}  horizon={args.hours}h")
    print(f"{'group':<18}{'hi_p50':>8}{'lo_p50':>8}{'lo_p90':>8}{'lo_p95':>8}{'pathless%':>11}")
    for g, v in s.items():
        print(
            f"{g:<18}{v['hi50']:8.1f}{v['lo50']:8.1f}{v['lo90']:8.1f}{v['lo95']:8.1f}{v['nopath']:10.1f}%"
        )
    print("\nper site (elevation 10-15 deg, reachable):")
    for si in twin.user_site_index:
        e = el[si]
        vis = e > cfg.elev_mask_deg
        reach = vis & (hop >= 0)
        acq = link_acquisition_time_s(
            np.deg2rad(e), doprate[si], hop, press[si], feeder_slots=slots, **BASE
        )
        lo = reach & (e > 10.0) & (e < 15.0)
        hi = reach & (e > 25.0)
        print(
            f"  {twin.sites[si].name:<14}{twin.sites[si].lat_deg:7.2f}"
            f"  hop_p50={np.median(hop[hi]) if hi.any() else float('nan'):4.1f}"
            f"  press_p50={np.median(press[si][hi]) if hi.any() else float('nan'):5.1f}"
            f"  acq_lo_p50={np.percentile(acq[lo], 50) if lo.any() else float('nan'):5.1f}"
            f"  acq_lo_p90={np.percentile(acq[lo], 90) if lo.any() else float('nan'):5.1f}"
            f"  pathless={100 * ((hop < 0) & vis).sum() / max(vis.sum(), 1):5.1f}%"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
