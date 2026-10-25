"""Calibrate the link-acquisition-time model against the twin geometry.

The manuscript asserts (Sec. 4.2) that a minimum handover advance of about
10-12 s is required at low elevation in the Arctic, whereas preparation time
below 12 s drives Arctic handover success from 99% to under 60%.  This script
reports the distribution of the modelled acquisition time so that the
parameters of the physical model can be checked against that statement before
any reinforcement learning is run.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from almond.twin.geometry import link_acquisition_time_s
from almond.twin.twin import DigitalTwin, TwinConfig

ACQ = dict(
    t_signaling_s=1.8,
    t_sync_base_s=0.8,
    doppler_coeff_s=0.00045,
    hop_coeff_s=0.95,
    low_el_coeff_s=2.0,
    el_ref_rad=np.deg2rad(25.0),
)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", default="smoke")
    ap.add_argument("--hours", type=float, default=1.5)
    ap.add_argument("--dt", type=float, default=10.0)
    args = ap.parse_args()

    cfg = TwinConfig(horizon_s=args.hours * 3600, dt_s=args.dt, tag=args.tag)
    twin = DigitalTwin(cfg).build()
    hop = twin["hop"]
    el = twin["el"]
    doprate = twin["doprate"]

    hdr = (
        f"{'site':<14}{'lat':>7}{'vis':>6}{'hop_hi':>7}{'hop_lo':>7}"
        f"{'acq_hi':>7}{'acq_lo':>7}{'acq_lo90':>9}{'nopath%':>9}"
    )
    print(hdr)
    print("-" * len(hdr))

    def med(a, m, q=50):
        return float(np.percentile(a[m], q)) if m.any() else float("nan")

    for si in twin.user_site_index:
        site = twin.sites[si]
        e = el[si]
        vis = e > cfg.elev_mask_deg
        acq = link_acquisition_time_s(np.deg2rad(e), doprate[si], hop, **ACQ)
        hi = vis & (e > 25.0)
        lo = vis & (e > 10.0) & (e < 15.0)
        nopath = ((hop < 0) & vis).sum() / max(vis.sum(), 1)
        print(
            f"{site.name:<14}{site.lat_deg:7.2f}{vis.sum(axis=0).mean():6.1f}"
            f"{np.median(hop[hi]) if hi.any() else float('nan'):7.1f}"
            f"{np.median(hop[lo]) if lo.any() else float('nan'):7.1f}"
            f"{med(acq, hi):7.1f}{med(acq, lo):7.1f}{med(acq, lo, 90):9.1f}"
            f"{nopath * 100:8.1f}%"
        )

    print("\nhop distribution over site-visible satellite instants:")
    for si in twin.user_site_index:
        e = el[si]
        vis = e > cfg.elev_mask_deg
        h = hop[vis]
        if not h.size:
            continue
        hh = h[h >= 0]
        print(
            f"  {twin.sites[si].name:<14} p05={np.percentile(hh, 5):4.0f} p50={np.percentile(hh, 50):4.0f} "
            f"p95={np.percentile(hh, 95):4.0f} max={hh.max():3.0f} unreachable={100 * (h < 0).mean():5.1f}%"
        )

    print("\nfeeder links active at once:")
    gwl = twin["gw_links"]
    print(f"  mean = {gwl.sum(axis=0).mean():.1f}  max = {int(gwl.sum(axis=0).max())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
