"""Smoke test for the digital twin: build a small constellation and sanity check."""
from __future__ import annotations

import sys
import time

import numpy as np

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[1]))

from almond.twin.constellation import (
    DENSITY200_SPEC,
    REFERENCE_SPEC,
    WalkerConstellation,
    altitude_to_mean_motion,
    build_constellation,
    make_tle,
)
from almond.twin.sites import USER_SITES


def main() -> int:
    print("== mean motion check ==")
    print("700 km ->", round(altitude_to_mean_motion(700.0), 4), "rev/day")
    print("550 km ->", round(altitude_to_mean_motion(550.0), 4), "rev/day")

    print("\n== TLE synthesis round-trip ==")
    tle = make_tle(12345, 2026, 292.25, 89.5, 45.0, 0.0002, 0.0, 90.0, 14.5710)
    print(tle.strip())
    from sgp4.api import Satrec

    lines = tle.strip().splitlines()
    sat = Satrec.twoline2rv(lines[1], lines[2])
    print("parsed satnum", sat.satnum, "incl", round(np.degrees(sat.inclo), 3))

    print("\n== propagation ==")
    t0 = time.time()
    c = WalkerConstellation(REFERENCE_SPEC, 2026, 292.25)
    print(REFERENCE_SPEC.describe())
    from sgp4.api import jday

    jd, fr = jday(2026, 10, 19, 0, 0, 0.0)
    prop = c.propagate(jd, 3600.0, 10.0)
    t_sec, pos, vel = prop.t_sec, prop.ecef, prop.ecef_vel
    print(f"propagated {c.n_sat} sats x {t_sec.size} steps in {time.time() - t0:.2f}s")
    r = np.linalg.norm(pos, axis=-1)
    print("altitude km: mean %.1f  min %.1f  max %.1f" % (r.mean() - 6378.137, r.min() - 6378.137, r.max() - 6378.137))
    print("speed km/s: mean %.3f" % np.linalg.norm(vel, axis=-1).mean())

    print("\n== geometry vs one site ==")
    from almond.twin.geometry import doppler_hz, range_rate, received_snr_db

    site = [s for s in USER_SITES if s.name == "Longyearbyen"][0]
    se = site.ecef()
    d = pos - se[None, None, :]
    rng = np.linalg.norm(d, axis=-1)
    u = se / np.linalg.norm(se)
    el = np.degrees(np.arcsin(np.clip(np.einsum("ijk,k->ij", d, u) / rng, -1, 1)))
    snr = received_snr_db(rng, np.deg2rad(el))
    rr = range_rate(pos, se, 10.0)
    dop = doppler_hz(rr, 20e9) / 1e3
    vis = el > 10.0
    print("visible count: mean %.1f max %d" % (vis.sum(axis=0).mean(), vis.sum(axis=0).max()))
    print("SNR dB over visible: mean %.1f  p05 %.1f" % (snr[vis].mean(), np.percentile(snr[vis], 5)))
    print("doppler kHz: p05 %.1f p95 %.1f" % (np.percentile(dop[vis], 5), np.percentile(dop[vis], 95)))
    print("max doppler rate kHz/s: %.3f" % (
        np.abs(np.gradient(dop, 10.0, axis=1))[vis].max()
    ))

    print("\n== polar seam check ==")
    from almond.twin.topology import (
        ISLConfig,
        build_isl_adjacency,
        ecef_to_latlon,
        hop_count_to_gateway,
    )

    lat0, lon0 = ecef_to_latlon(pos[:, 0, :])
    lat_all, _ = ecef_to_latlon(pos)
    nrm = np.cross(prop.eci[:, 0, :], prop.eci_vel[:, 0, :])
    nrm /= np.maximum(np.linalg.norm(nrm, axis=-1, keepdims=True), 1e-9)
    adj = build_isl_adjacency(pos[:, 0, :].astype(np.float64), ISLConfig(), lat0, nrm)
    print("ISL edges at t=0:", int(adj.sum() // 2), " mean degree %.2f" % adj.sum(axis=1).mean())
    high = np.abs(lat0) > 70
    print("sats above 70N:", int(high.sum()))
    print("mean degree above 70N: %.2f  below: %.2f" % (
        adj[high].sum(axis=1).mean(), adj[~high].sum(axis=1).mean()))
    # gateway visibility
    gw = np.zeros(pos.shape[0], dtype=bool)
    for site in [s for s in USER_SITES if s.is_gateway]:
        se = site.ecef()
        d = pos[:, 0, :] - se[None, :]
        rr = np.linalg.norm(d, axis=-1)
        e = np.degrees(np.arcsin(np.clip(d @ (se / np.linalg.norm(se)) / rr, -1, 1)))
        gw |= e > 10.0
    hop = hop_count_to_gateway(adj, gw)
    print("gateway sats:", int(gw.sum()), " hop min/mean/max:", hop.min(), round(float(hop[hop >= 0].mean()), 2), hop.max())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
