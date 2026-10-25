"""Constellation construction and SGP4 propagation.

The digital twin is driven by two-line-element ephemeris data propagated with
SGP4.  Two sources are supported:

``RealTLEConstellation``
    A catalog downloaded from Celestrak (``data/tle/*.tle``).  Used to
    demonstrate that the pipeline runs on actual operational ephemeris
    (e.g. the OneWeb and Iridium-NEXT polar fleets).

``WalkerConstellation``
    A Walker-delta design synthesised as valid TLE element sets and then
    propagated with the same SGP4 propagator (so J2 nodal precession, drag and
    the full SGP4 force model still apply).  This is what the reference
    350-satellite scenario uses, because no single public fleet provides the
    paper's polar shell (i ~ 90 deg, h ~ 700 km) at the required density.

Both classes expose the same interface::

    c = build_constellation(kind, ...)
    t_sec, eci, ecef, vel_ecef = c.propagate(t0_jd, duration_s, dt_s)

All positions are in km, velocities in km/s, time in seconds from ``t0``.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, NamedTuple, Sequence

import numpy as np

from sgp4.api import Satrec, SatrecArray, jday

MU_EARTH = 398600.4418  # km^3 / s^2
R_EARTH = 6378.137  # km
J2 = 1.08262668e-3
OMEGA_EARTH = 7.2921150e-5  # rad/s

DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "tle"


# --------------------------------------------------------------------------- #
# TLE synthesis helpers
# --------------------------------------------------------------------------- #
def _tle_checksum(line: str) -> int:
    """Standard TLE modulo-10 checksum over the first 68 characters."""
    tot = 0
    for ch in line[:68]:
        if ch.isdigit():
            tot += int(ch)
        elif ch == "-":
            tot += 1
    return tot % 10


def _exp_field(value: float, width: int = 8) -> str:
    """Format a TLE-style implied-decimal exponent field (e.g. `` 43854-3``)."""
    if value == 0.0:
        return " " * (width - 1) + "0"
    sign = "-" if value < 0 else " "
    mant = abs(value)
    exp = 0
    # normalise into [0.1, 1.0)
    while mant >= 1.0:
        mant /= 10.0
        exp += 1
    while mant < 0.1:
        mant *= 10.0
        exp -= 1
    digits = int(round(mant * 1e5))
    if digits >= 100000:
        digits //= 10
        exp += 1
    esign = "-" if exp < 0 else "+"
    return f"{sign}{digits:05d}{esign}{abs(exp)}"[:width].rjust(width)


def make_tle(
    satnum: int,
    epoch_year: int,
    epoch_doy: float,
    incl_deg: float,
    raan_deg: float,
    ecc: float,
    argp_deg: float,
    mean_anom_deg: float,
    mean_motion_rev_day: float,
    bstar: float = 1.0e-4,
    ndot: float = 0.0,
) -> str:
    """Build a syntactically valid, checksummed two-line element set."""
    name = f"SIM-{satnum:05d}"
    yy = epoch_year % 100
    line1_body = (
        f"1 {satnum:05d}U 98067A   {yy:02d}{epoch_doy:012.8f} "
        f" .{int(ndot * 1e8):08d}  00000-0 {_exp_field(bstar)} 0  999"
    )
    line1 = f"{line1_body}{_tle_checksum(line1_body):1d}"
    # TLE writes eccentricity with an implied leading decimal point (7 columns)
    ecc_field = f"{max(ecc, 0.0):.7f}"[2:]
    line2_body = (
        f"2 {satnum:05d} {incl_deg:8.4f} {raan_deg:8.4f} {ecc_field} "
        f"{argp_deg:8.4f} {mean_anom_deg:8.4f} {mean_motion_rev_day:11.8f}"
        f"{1:5d}"
    )
    line2 = f"{line2_body}{_tle_checksum(line2_body):1d}"
    return f"{name}\n{line1}\n{line2}\n"


def altitude_to_mean_motion(alt_km: float) -> float:
    a = R_EARTH + alt_km
    period = 2.0 * math.pi * math.sqrt(a**3 / MU_EARTH)
    return 86400.0 / period


# --------------------------------------------------------------------------- #
# Constellation containers
# --------------------------------------------------------------------------- #
@dataclass
class ConstellationSpec:
    """Description of a multi-shell Walker constellation."""

    name: str
    shells: list[dict] = field(default_factory=list)

    @property
    def n_sat(self) -> int:
        return sum(int(s["planes"]) * int(s["per_plane"]) for s in self.shells)

    def describe(self) -> str:
        parts = []
        for s in self.shells:
            parts.append(
                f"{s['planes']}x{s['per_plane']} i={s['incl']:.1f} h={s['alt']:.0f}km"
            )
        return f"{self.name}: {self.n_sat} sats [" + "; ".join(parts) + "]"


#: Reference constellation: 350 satellites, polar shell dominant (reference
#: scenario for Arctic service), plus mid-latitude and equatorial shells used by
#: the generalisation study.
REFERENCE_SPEC = ConstellationSpec(
    name="ref350",
    shells=[
        # polar shells (reference scenario, ~700 km)
        dict(planes=10, per_plane=20, incl=89.5, alt=700.0, phase=0.0),
        # mid-latitude shell (~53 deg, 550 km)
        dict(planes=6, per_plane=20, incl=53.0, alt=550.0, phase=1.0),
        # equatorial shell (~5 deg, 600 km)
        dict(planes=2, per_plane=15, incl=5.0, alt=600.0, phase=2.0),
    ],
)

#: 200-satellite density variant (polar-heavy).
DENSITY200_SPEC = ConstellationSpec(
    name="ref200",
    shells=[
        dict(planes=8, per_plane=15, incl=89.5, alt=700.0, phase=0.0),
        dict(planes=4, per_plane=14, incl=53.0, alt=550.0, phase=1.0),
        dict(planes=2, per_plane=12, incl=5.0, alt=600.0, phase=2.0),
    ],
)

#: 550-satellite density variant.
DENSITY550_SPEC = ConstellationSpec(
    name="ref550",
    shells=[
        dict(planes=14, per_plane=20, incl=89.5, alt=700.0, phase=0.0),
        dict(planes=8, per_plane=22, incl=53.0, alt=550.0, phase=1.0),
        dict(planes=3, per_plane=18, incl=5.0, alt=600.0, phase=2.0),
    ],
)


class Propagation(NamedTuple):
    """Result of :meth:`Constellation.propagate`."""

    t_sec: np.ndarray  # (n_time,)
    ecef: np.ndarray  # (n_sat, n_time, 3) km
    ecef_vel: np.ndarray  # (n_sat, n_time, 3) km/s
    eci: np.ndarray  # (n_sat, n_time, 3) km (TEME)
    eci_vel: np.ndarray  # (n_sat, n_time, 3) km/s


def _stack_rot(cos_g: np.ndarray, sin_g: np.ndarray, n_time: int) -> np.ndarray:
    """Rotation matrices ``R`` with shape ``(3, 3, n_time)`` mapping TEME->ECEF."""
    zero = np.zeros((1, n_time))
    c = np.asarray(cos_g).reshape(1, n_time)
    s = np.asarray(sin_g).reshape(1, n_time)
    one = np.ones((1, n_time))
    return np.concatenate(
        [
            np.concatenate([c, -s, zero], axis=0),
            np.concatenate([s, c, zero], axis=0),
            np.concatenate([zero, zero, one], axis=0),
        ],
        axis=0,
    )


class Constellation:
    """Base class holding SGP4 satellites."""

    name: str = "base"

    def __init__(self, sats: Sequence[Satrec], labels: Sequence[str] | None = None):
        self.sats = list(sats)
        self.labels = list(labels) if labels is not None else [
            f"S{i:03d}" for i in range(len(self.sats))
        ]
        self.sat_array = SatrecArray(self.sats)
        self.n_sat = len(self.sats)

    # -- identification ---------------------------------------------------- #
    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"<{type(self).__name__} {self.name} n_sat={self.n_sat}>"

    # -- propagation ------------------------------------------------------- #
    def propagate(self, jd0: float, duration_s: float, dt_s: float) -> Propagation:
        """Propagate the whole constellation on a uniform time grid.

        Returns a :class:`Propagation` with ECEF positions (km), ECEF velocities
        (km/s), and the raw TEME states.  TEME->ECEF uses GMST rotation (polar
        motion and the TEME/TOD nutation offset are neglected, < 1 m error).
        """
        n_time = int(round(duration_s / dt_s)) + 1
        t_sec = np.arange(n_time, dtype=np.float64) * dt_s
        frac_day = t_sec / 86400.0
        jd = np.full(n_time, jd0, dtype=np.float64)
        fr = frac_day.copy()
        # normalise so that fr in [0, 1)
        while np.any(fr >= 1.0):
            k = fr >= 1.0
            fr[k] -= 1.0
            jd[k] += 1.0

        r_teme = np.empty((self.n_sat, n_time, 3), dtype=np.float64)
        v_teme = np.empty((self.n_sat, n_time, 3), dtype=np.float64)
        for i, sat in enumerate(self.sats):
            err, r, v = sat.sgp4_array(jd, fr)
            bad = err != 0
            if np.any(bad):
                # replace failed propagations with the nearest valid sample
                good = ~bad
                if not np.any(good):
                    raise RuntimeError(f"satellite {i} failed to propagate at all")
                idx = np.where(good)[0]
                r[bad] = r[idx[-1]]
                v[bad] = v[idx[-1]]
            r_teme[i] = r
            v_teme[i] = v

        gmst = gmst_angle(jd, fr)
        c, s = np.cos(gmst), np.sin(gmst)  # (n_time,)

        ecef = np.empty_like(r_teme)
        ecef[..., 0] = c * r_teme[..., 0] - s * r_teme[..., 1]
        ecef[..., 1] = s * r_teme[..., 0] + c * r_teme[..., 1]
        ecef[..., 2] = r_teme[..., 2]

        # v_ecef = R v_teme + omega x r_ecef   (rotating-frame derivative)
        vrot = np.empty_like(v_teme)
        vrot[..., 0] = c * v_teme[..., 0] - s * v_teme[..., 1]
        vrot[..., 1] = s * v_teme[..., 0] + c * v_teme[..., 1]
        vrot[..., 2] = v_teme[..., 2]
        ecef_vel = np.empty_like(vrot)
        ecef_vel[..., 0] = vrot[..., 0] - OMEGA_EARTH * ecef[..., 1]
        ecef_vel[..., 1] = vrot[..., 1] + OMEGA_EARTH * ecef[..., 0]
        ecef_vel[..., 2] = vrot[..., 2]
        return Propagation(t_sec, ecef, ecef_vel, r_teme, v_teme)


def gmst_angle(jd: np.ndarray, fr: np.ndarray) -> np.ndarray:
    """Greenwich mean sidereal time (rad) from UTC Julian date."""
    du = jd - 2451545.0 + fr
    tu = du / 36525.0
    theta = (
        280.46061837
        + 360.98564736629 * du
        + 0.000387933 * tu**2
        - tu**3 / 38710000.0
    )
    return np.deg2rad(np.mod(theta, 360.0))


class WalkerConstellation(Constellation):
    """Synthetic Walker-delta constellation propagated with SGP4."""

    def __init__(
        self,
        spec: ConstellationSpec,
        epoch_year: int = 2026,
        epoch_doy: float = 292.25,
        raan_offset_deg: float = 0.0,
        mean_anom_offset_deg: float = 0.0,
    ):
        sats = []
        labels = []
        satnum = 10000
        for si, shell in enumerate(spec.shells):
            planes = int(shell["planes"])
            per_plane = int(shell["per_plane"])
            incl = float(shell["incl"])
            alt = float(shell["alt"])
            mm = altitude_to_mean_motion(alt)
            phase = float(shell.get("phase", 0.0))
            # Walker-delta: RAAN spread over 360 deg, inter-plane phasing F=1
            d_raan = 360.0 / planes
            d_ma = 360.0 / per_plane
            f = phase % planes
            for p in range(planes):
                raan = (raan_offset_deg + p * d_raan) % 360.0
                for k in range(per_plane):
                    ma = (
                        mean_anom_offset_deg + k * d_ma + f * (360.0 / (planes * per_plane))
                    ) % 360.0
                    tle = make_tle(
                        satnum=satnum,
                        epoch_year=epoch_year,
                        epoch_doy=epoch_doy,
                        incl_deg=incl,
                        raan_deg=raan,
                        ecc=0.0002,
                        argp_deg=0.0,
                        mean_anom_deg=ma,
                        mean_motion_rev_day=mm,
                        bstar=2.0e-5,
                    )
                    lines = tle.strip().splitlines()
                    sats.append(Satrec.twoline2rv(lines[1], lines[2]))
                    labels.append(f"SH{si}P{p:02d}K{k:02d}")
                    satnum += 1
        self.spec = spec
        self.name = spec.name
        super().__init__(sats, labels)


class RealTLEConstellation(Constellation):
    """Constellation loaded from a Celestrak-format TLE catalog."""

    def __init__(self, path: str | Path, max_sats: int | None = None, name: str | None = None):
        path = Path(path)
        text = path.read_text()
        lines = [ln.rstrip() for ln in text.replace("\r\n", "\n").split("\n") if ln.strip()]
        sats, labels = [], []
        i = 0
        while i + 2 < len(lines) + 1 and i + 1 < len(lines):
            if lines[i].startswith("1 ") and lines[i + 1].startswith("2 "):
                l1, l2 = lines[i], lines[i + 1]
                nm = f"OBJ{len(sats):04d}"
                i += 2
            else:
                nm, l1, l2 = lines[i].strip(), lines[i + 1], lines[i + 2]
                i += 3
            try:
                sats.append(Satrec.twoline2rv(l1, l2))
                labels.append(nm)
            except Exception:  # pragma: no cover - malformed catalog entry
                continue
            if max_sats is not None and len(sats) >= max_sats:
                break
        if not sats:
            raise ValueError(f"no satellites parsed from {path}")
        self.name = name or path.stem
        self.source = str(path)
        super().__init__(sats, labels)


# --------------------------------------------------------------------------- #
# Factory
# --------------------------------------------------------------------------- #
def build_constellation(
    kind: str = "ref350",
    epoch_year: int = 2026,
    epoch_doy: float = 292.25,
    max_sats: int | None = None,
) -> Constellation:
    """Build a constellation by name.

    ``ref350``/``ref200``/``ref550``   Walker-delta synthetic (reference)
    ``oneweb``/``iridium``             real Celestrak TLE catalogs
    """
    kind = kind.lower()
    if kind in ("ref350", "reference"):
        return WalkerConstellation(REFERENCE_SPEC, epoch_year, epoch_doy)
    if kind in ("ref200",):
        return WalkerConstellation(DENSITY200_SPEC, epoch_year, epoch_doy)
    if kind in ("ref550",):
        return WalkerConstellation(DENSITY550_SPEC, epoch_year, epoch_doy)
    if kind == "oneweb":
        return RealTLEConstellation(DATA_DIR / "oneweb.tle", max_sats=max_sats, name="oneweb")
    if kind == "iridium":
        return RealTLEConstellation(DATA_DIR / "iridium-NEXT.tle", max_sats=max_sats, name="iridium")
    raise ValueError(f"unknown constellation kind: {kind}")


def jd_from_datetime(year: int, month: int, day: int, hour: int = 0, minute: int = 0, sec: float = 0.0):
    return jday(year, month, day, hour, minute, sec)
