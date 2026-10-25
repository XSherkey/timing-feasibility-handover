"""Link geometry, Doppler, link budget and eclipse modelling.

All computations are deterministic closed-form expressions.  They form the
"metric layer" of the twin: the normalisation bounds of the sub-rewards and the
physics checks of the auditor are derived from these functions and are never
modified by the LLM.
"""
from __future__ import annotations

import numpy as np

R_EARTH = 6378.137  # km
C_LIGHT = 299792.458  # km/s
K_BOLTZMANN_DBW = -228.6  # dBW/K/Hz


# --------------------------------------------------------------------------- #
# Geometry
# --------------------------------------------------------------------------- #
def site_vectors(site_ecef: np.ndarray, sat_ecef: np.ndarray):
    """Return (range_km, elevation_rad, azimuth_rad, unit_los) for one site.

    ``sat_ecef`` has shape ``(n_sat, n_time, 3)``; the returned arrays have shape
    ``(n_sat, n_time)``.
    """
    d = sat_ecef - site_ecef[None, None, :]
    rng = np.linalg.norm(d, axis=-1)
    u = site_ecef / np.linalg.norm(site_ecef)
    sin_el = np.einsum("ijk,k->ij", d, u) / rng
    sin_el = np.clip(sin_el, -1.0, 1.0)
    el = np.arcsin(sin_el)

    # local east/north basis
    lon = np.arctan2(site_ecef[1], site_ecef[0])
    lat = np.arctan2(site_ecef[2], np.hypot(site_ecef[0], site_ecef[1]))
    east = np.array([-np.sin(lon), np.cos(lon), 0.0])
    north = np.array(
        [-np.sin(lat) * np.cos(lon), -np.sin(lat) * np.sin(lon), np.cos(lat)]
    )
    e_comp = np.einsum("ijk,k->ij", d, east)
    n_comp = np.einsum("ijk,k->ij", d, north)
    az = np.arctan2(e_comp, n_comp) % (2 * np.pi)
    return rng, el, az, d / rng[..., None]


def range_rate(sat_ecef: np.ndarray, site_ecef: np.ndarray, dt_s: float) -> np.ndarray:
    """Range rate (km/s) by central difference along the time axis."""
    rng = np.linalg.norm(sat_ecef - site_ecef[None, None, :], axis=-1)
    rr = np.gradient(rng, dt_s, axis=1, edge_order=1)
    return rr


def doppler_hz(range_rate_kmps: np.ndarray, freq_hz: float) -> np.ndarray:
    return -freq_hz * range_rate_kmps / C_LIGHT


# --------------------------------------------------------------------------- #
# Link budget
# --------------------------------------------------------------------------- #
def free_space_loss_db(d_km: np.ndarray, freq_hz: float) -> np.ndarray:
    f_ghz = freq_hz / 1e9
    return 92.45 + 20.0 * np.log10(np.maximum(d_km, 1.0)) + 20.0 * np.log10(f_ghz)


def atmospheric_loss_db(el_rad: np.ndarray, freq_ghz: float = 20.0, rain: float = 1.0) -> np.ndarray:
    """Elevation-dependent atmospheric attenuation (clear-sky + scaled rain).

    Zenith attenuation follows the order of magnitude quoted by ITU-R P.618 for
    Ka-band (0.4 dB at 20 GHz, 1.2 dB at 30 GHz); the cosecant scaling is the
    standard plane-parallel-air approximation, capped to avoid the singularity
    at the horizon where the link is anyway below the elevation mask.
    """
    zen = 0.4 * (freq_ghz / 20.0) ** 1.6
    el = np.maximum(el_rad, np.deg2rad(5.0))
    a = zen * rain / np.sin(el)
    return np.minimum(a, 12.0)


def received_snr_db(
    rng_km: np.ndarray,
    el_rad: np.ndarray,
    *,
    freq_hz: float = 20e9,
    eirp_dbw: float = 50.0,
    g_over_t_db: float = 5.0,
    bandwidth_hz: float = 250e6,
    rain: float = 1.0,
    extra_loss_db: float = 1.0,
) -> np.ndarray:
    """Downlink SNR in dB for a given bandwidth."""
    fspl = free_space_loss_db(rng_km, freq_hz)
    atm = atmospheric_loss_db(el_rad, freq_hz / 1e9, rain)
    cn0 = eirp_dbw - fspl - atm - extra_loss_db + g_over_t_db - K_BOLTZMANN_DBW
    cn = cn0 - 10.0 * np.log10(bandwidth_hz)
    return cn


def spectral_efficiency(snr_db: np.ndarray, cap: float = 4.5) -> np.ndarray:
    """Shannon efficiency clipped to a realistic adaptive-modulation cap (bps/Hz)."""
    snr = 10.0 ** (snr_db / 10.0)
    return np.minimum(np.log2(1.0 + snr), cap)


def link_capacity_mbps(snr_db: np.ndarray, bandwidth_hz: float = 250e6, cap: float = 4.5) -> np.ndarray:
    return spectral_efficiency(snr_db, cap) * bandwidth_hz / 1e6


def link_acquisition_time_s(
    el_rad: np.ndarray,
    doppler_rate_hz_s: np.ndarray,
    hop_count: np.ndarray,
    feeder_pressure: np.ndarray | None = None,
    *,
    t_signaling_s: float = 1.2,
    t_sync_base_s: float = 0.6,
    doppler_coeff_s: float = 0.00020,
    hop_coeff_s: float = 0.42,
    low_el_coeff_s: float = 1.5,
    el_ref_rad: float = np.deg2rad(25.0),
    feeder_slots: int = 3,
    t_slot_s: float = 1.8,
) -> np.ndarray:
    """Time required to establish a make-before-break handover.

    Five physically motivated components:

    * signalling round trip for the handover request/acknowledgement,
    * carrier/symbol synchronisation, which degrades with Doppler rate,
    * route establishment along the ISL path to the feeder gateway (grows with
      the number of hops that must be re-programmed),
    * low-elevation acquisition penalty: at grazing elevation the tracker, the
      automatic-gain-control loop and the uplink timing advance need longer to
      converge,
    * feeder-slot contention: a gateway tracks only ``feeder_slots`` satellites
      at once, so a handover that needs a new feeder slot queues behind the
      other satellites competing for that gateway.  Because a polar gateway
      sees an order of magnitude more satellites than a mid-latitude one, this
      term is the dominant reason Arctic preparation needs a longer advance.

    ``feeder_pressure`` is the number of satellites simultaneously visible from
    the target's best gateway; it may be ``None`` when feeder contention is not
    modelled.
    """
    el = np.maximum(el_rad, np.deg2rad(5.0))
    t_sync = t_sync_base_s + doppler_coeff_s * np.abs(doppler_rate_hz_s)
    t_route = hop_coeff_s * np.maximum(hop_count, 0)
    low = np.clip(1.0 - np.sin(el) / np.sin(el_ref_rad), 0.0, 1.0)
    t_lowel = low_el_coeff_s * low
    t_feed = np.zeros_like(el)
    if feeder_pressure is not None:
        ratio = np.maximum(feeder_pressure, 1).astype(np.float64) / float(feeder_slots)
        t_feed = t_slot_s * np.maximum(ratio - 1.0, 0.0)
    return t_signaling_s + t_sync + t_route + t_lowel + t_feed


# --------------------------------------------------------------------------- #
# Eclipse
# --------------------------------------------------------------------------- #
def sun_unit_vector_ecef(jd: np.ndarray, fr: np.ndarray) -> np.ndarray:
    """Approximate geocentric sun direction in ECEF, shape ``(n_time, 3)``."""
    from .constellation import gmst_angle

    n = jd - 2451545.0 + fr
    L = np.deg2rad(np.mod(280.460 + 0.9856474 * n, 360.0))
    g = np.deg2rad(np.mod(357.528 + 0.9856003 * n, 360.0))
    lam = L + np.deg2rad(1.915) * np.sin(g) + np.deg2rad(0.020) * np.sin(2 * g)
    eps = np.deg2rad(23.439 - 0.0000004 * n)
    # geocentric equatorial (inertial) unit vector
    x = np.cos(lam)
    y = np.cos(eps) * np.sin(lam)
    z = np.sin(eps) * np.sin(lam)
    v = np.stack([x, y, z], axis=-1)
    v /= np.linalg.norm(v, axis=-1, keepdims=True)
    # rotate into ECEF
    th = gmst_angle(jd, fr)
    c, s = np.cos(th), np.sin(th)
    out = np.empty_like(v)
    out[:, 0] = c * v[:, 0] + s * v[:, 1]
    out[:, 1] = -s * v[:, 0] + c * v[:, 1]
    out[:, 2] = v[:, 2]
    return out


def eclipse_mask(sat_ecef: np.ndarray, sun_ecef_unit: np.ndarray) -> np.ndarray:
    """Boolean eclipse flag, shape ``(n_sat, n_time)``.

    A satellite is eclipsed when the Earth blocks the Sun-satellite line: the
    satellite is on the anti-sun side and its perpendicular distance to the
    Sun-Earth axis is smaller than the Earth radius.
    """
    s = sun_ecef_unit[None, :, :]
    dot = np.einsum("ijk,ijk->ij", sat_ecef, np.broadcast_to(s, sat_ecef.shape))
    perp = np.linalg.norm(sat_ecef - dot[..., None] * np.broadcast_to(s, sat_ecef.shape), axis=-1)
    return (dot < 0.0) & (perp < R_EARTH)


# --------------------------------------------------------------------------- #
# ISL geometry
# --------------------------------------------------------------------------- #
def isl_visible(
    pos: np.ndarray,
    max_range_km: float = 5200.0,
    min_elev_km: float = 100.0,
) -> np.ndarray:
    """Line-of-sight test for every satellite pair at one instant.

    ``pos`` has shape ``(n_sat, 3)``.  Two satellites see each other when their
    separation is below ``max_range_km`` and the straight line between them does
    not intersect the Earth (approximated by the distance from the Earth centre
    to the segment exceeding ``R_EARTH + min_elev_km``).
    """
    n = pos.shape[0]
    diff = pos[:, None, :] - pos[None, :, :]
    d = np.linalg.norm(diff, axis=-1)
    # distance from origin to each segment
    a = -pos[None, :, :]  # from sat_j
    b = diff
    bb = np.einsum("ijk,ijk->ij", b, b)
    t = np.clip(-np.einsum("ijk,ijk->ij", a, b) / np.maximum(bb, 1e-9), 0.0, 1.0)
    closest = a + t[..., None] * b
    dmin = np.linalg.norm(closest, axis=-1)
    los = (dmin > R_EARTH + min_elev_km) & (d < max_range_km)
    np.fill_diagonal(los, False)
    return los
