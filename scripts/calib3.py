"""Calibrate the link-acquisition-time model against the twin geometry.

Reports, per latitude group, the probability that a handover attempted with a
given preparation advance completes its make-before-break procedure.  Those
curves are what the manuscript's reliability claims rest on:

* the naive baseline (advance < 6 s) should sit near 55% above 70 N;
* an advance of 10-12 s should restore >90-95% above 70 N;
* mid-latitude service should already be ~99% at a small advance.

Run ``--sweep`` to compare coefficient sets; run with no flag for the report.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from almond.twin.geometry import link_acquisition_time_s
from almond.twin.twin import DigitalTwin, TwinConfig

ADVANCES = (2, 4, 6, 8, 10, 12, 14, 16, 20)


def acq_params(cfg: TwinConfig) -> dict:
    return dict(t_signaling_s=cfg.t_signaling_s, t_sync_base_s=cfg.t_sync_base_s)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", default="cal")
    ap.add_argument("--hours", type=float, default=1.5)
    ap.add_argument("--dt", type=float, default=10.0)
    args = ap.parse_args()

    cfg = TwinConfig(horizon_s=args.hours * 3600, dt_s=args.dt, tag=args.tag)
    twin = DigitalTwin(cfg).build()
    el, hop, doprate, press = twin["el"], twin["hop"], twin["doprate"], twin["feed_press"]

    groups = {
        "arctic >70": [i for i in twin.user_site_index if abs(twin.sites[i].lat_deg) > 70],
        "subarctic 65-70": [i for i in twin.user_site_index if 65 <= abs(twin.sites[i].lat_deg) <= 70],
        "midlat 30-65": [i for i in twin.user_site_index if 30 <= abs(twin.sites[i].lat_deg) < 65],
        "equator <30": [i for i in twin.user_site_index if abs(twin.sites[i].lat_deg) < 30],
    }

    print(f"feeder_slots(routing)={cfg.feeder_slots} feeder_queue_slots={cfg.feeder_queue_slots}")
    print(f"{'group':<18}{'n_links':>9}{'p50':>7}{'p90':>7}{'p95':>7}  " + "".join(f"{a:>6}s" for a in ADVANCES) + f"{'pathless':>10}")
    for gname, idxs in groups.items():
        acqs, nopath, nlink = [], [], 0
        for si in idxs:
            e = el[si]
            vis = e > cfg.elev_mask_deg
            reach = vis & (hop >= 0)
            nlink += int(reach.sum())
            acq = link_acquisition_time_s(
                np.deg2rad(e), doprate[si], hop, press, feeder_slots=cfg.feeder_queue_slots
            )
            acqs.append(acq[reach])
            nopath.append(((hop < 0) & vis).sum() / max(vis.sum(), 1))
        a = np.concatenate(acqs)
        succ = [float((a <= x).mean()) * 100 for x in ADVANCES]
        print(
            f"{gname:<18}{nlink:9d}{np.percentile(a, 50):7.1f}{np.percentile(a, 90):7.1f}"
            f"{np.percentile(a, 95):7.1f}  "
            + "".join(f"{s:6.1f}" for s in succ)
            + f"{np.mean(nopath) * 100:9.1f}%"
        )

    print("\nper site (low-elevation band 10-15 deg, reachable):")
    for si in twin.user_site_index:
        e = el[si]
        vis = e > cfg.elev_mask_deg
        reach = vis & (hop >= 0)
        acq = link_acquisition_time_s(
            np.deg2rad(e), doprate[si], hop, press, feeder_slots=cfg.feeder_queue_slots
        )
        lo = reach & (e > 10.0) & (e < 15.0)
        if not lo.any():
            continue
        print(
            f"  {twin.sites[si].name:<14}{twin.sites[si].lat_deg:7.2f}"
            f"  hop={np.median(hop[lo]):4.1f} press={np.median(press[lo]):5.1f}"
            f"  acq p50={np.percentile(acq[lo], 50):5.1f} p90={np.percentile(acq[lo], 90):5.1f}"
            f"  P(<=12s)={100 * (acq[lo] <= 12).mean():5.1f}%"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
