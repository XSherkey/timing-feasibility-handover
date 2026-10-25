"""The digital twin: precomputed orbital, link and routing state.

The twin is deterministic given ``(constellation, epoch, horizon, dt)``.  All
expensive work happens once in :meth:`DigitalTwin.build` and is memory-mapped
from disk, so that dozens of training runs share a single physical model.  This
is what makes a 350-satellite, SGP4-driven twin affordable for hundreds of
seeds of reinforcement learning.
"""
from __future__ import annotations

import hashlib
import json
import math
from dataclasses import asdict, dataclass, field
from pathlib import Path

import numpy as np

from .constellation import build_constellation, gmst_angle
from .geometry import (
    atmospheric_loss_db,
    doppler_hz,
    eclipse_mask,
    free_space_loss_db,
    link_capacity_mbps,
    range_rate,
    received_snr_db,
    sun_unit_vector_ecef,
)
from .sites import ALL_SITES, USER_SITES, Site
from .topology import (
    ISLConfig,
    build_isl_adjacency,
    ecef_to_latlon,
    hop_count_to_gateway,
    isl_graph_metrics,
)

CACHE_ROOT = Path(__file__).resolve().parents[2] / "data" / "cache"


@dataclass
class TwinConfig:
    constellation: str = "ref350"
    epoch_year: int = 2026
    epoch_doy: float = 292.25
    horizon_s: float = 12 * 3600.0
    dt_s: float = 10.0
    elev_mask_deg: float = 10.0
    #: a satellite is a viable server only while its elevation is within this
    #: many degrees of the best visible candidate (contested service window)
    service_margin_deg: float = 10.0
    freq_hz: float = 20e9
    bandwidth_hz: float = 250e6
    eirp_dbw: float = 50.0
    g_over_t_db: float = 5.0
    rain_scale: float = 1.0
    isl_max_range_km: float = 5200.0
    isl_min_elev_km: float = 120.0
    isl_seam_lat_deg: float = 70.0
    isl_seam_enabled: bool = True
    isl_max_degree: int = 4
    isl_dropout: float = 0.0
    #: simultaneous feeder links a single gateway can maintain.  A polar gateway
    #: sees an order of magnitude more satellites than a mid-latitude one, so
    #: this cap is what makes feeder access scarce exactly above the seam.
    feeder_slots: int = 10
    feeder_min_elev_deg: float = 15.0
    #: feeder slots actually free for a *new* handover at any instant (the rest
    #: are already committed to ongoing sessions); this is the queueing term.
    feeder_queue_slots: int = 3
    k_candidates: int = 8
    #: coefficients of the link-acquisition model (Sec. 3.2.2 / 4.1)
    t_signaling_s: float = 1.2
    t_sync_base_s: float = 0.6
    tag: str = "ref"

    @property
    def n_time(self) -> int:
        return int(round(self.horizon_s / self.dt_s)) + 1

    def fingerprint(self) -> str:
        """Stable hash of the physical configuration.

        Numeric values are normalised to float so that ``12 * 3600`` and
        ``12.0 * 3600.0`` produce the same cache key; otherwise a caller passing
        an int horizon silently triggers a full cache rebuild.
        """
        d = asdict(self) if hasattr(self, "__dataclass_fields__") else dict(self)
        d.pop("tag", None)

        def norm(v):
            if isinstance(v, bool):
                return v
            if isinstance(v, (int, float)):
                return round(float(v), 9)
            if isinstance(v, dict):
                return {k: norm(x) for k, x in v.items()}
            if isinstance(v, (list, tuple)):
                return [norm(x) for x in v]
            return v

        blob = json.dumps(norm(d), sort_keys=True).encode()
        return hashlib.sha1(blob).hexdigest()[:12]


class DigitalTwin:
    """Physical model of the constellation + ground segment."""

    def __init__(self, cfg: TwinConfig | None = None, cache_dir: Path | None = None):
        self.cfg = cfg or TwinConfig()
        self.cache_dir = Path(cache_dir) if cache_dir else CACHE_ROOT / f"twin_{self.cfg.tag}_{self.cfg.fingerprint()}"
        self.sites: list[Site] = list(ALL_SITES)
        self.user_site_index: list[int] = [i for i, s in enumerate(self.sites) if s.is_user]
        self.gateway_site_index: list[int] = [i for i, s in enumerate(self.sites) if s.is_gateway]
        self._data: dict[str, np.ndarray] = {}

    # ------------------------------------------------------------------ #
    # Build / load
    # ------------------------------------------------------------------ #
    def build(self, force: bool = False, verbose: bool = True) -> "DigitalTwin":
        if self.cache_dir.exists() and not force:
            missing = self._missing_files()
            if not missing:
                if verbose:
                    print(f"[twin] cache hit: {self.cache_dir}")
                return self.load()
            if verbose:
                print(f"[twin] cache incomplete ({missing}), rebuilding")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        cfg = self.cfg
        if verbose:
            print(f"[twin] building {cfg.constellation} horizon={cfg.horizon_s / 3600:.1f}h dt={cfg.dt_s}s")
        const = build_constellation(cfg.constellation, cfg.epoch_year, cfg.epoch_doy)
        self.constellation = const
        self.n_sat = const.n_sat
        from sgp4.api import jday

        jd0, fr0 = jday(cfg.epoch_year, 1, 1, 0, 0, 0.0)
        jd0 = jd0 + (cfg.epoch_doy - 1.0)
        prop = const.propagate(jd0, cfg.horizon_s, cfg.dt_s)
        t_sec, pos, vel = prop.t_sec, prop.ecef, prop.ecef_vel
        # inertial orbit normals (specific angular momentum) for the seam test
        nrm = np.cross(prop.eci, prop.eci_vel)
        nrm /= np.maximum(np.linalg.norm(nrm, axis=-1, keepdims=True), 1e-9)
        lat_sat, lon_sat = ecef_to_latlon(pos)
        nt = t_sec.size

        # --- eclipse ---------------------------------------------------- #
        frac = (fr0 + t_sec / 86400.0)
        jd = np.full(nt, jd0)
        while np.any(frac >= 1.0):
            k = frac >= 1.0
            frac[k] -= 1.0
            jd[k] += 1.0
        sun = sun_unit_vector_ecef(jd, frac)
        ecl = eclipse_mask(pos.astype(np.float64), sun)

        # --- ground-segment geometry ------------------------------------ #
        n_site = len(self.sites)
        el = np.empty((n_site, self.n_sat, nt), dtype=np.float32)
        rng_km = np.empty_like(el)
        rr = np.empty_like(el)
        snr = np.empty_like(el)
        cap = np.empty_like(el)
        doprate = np.empty_like(el)
        for si, site in enumerate(self.sites):
            site_ecef = site.ecef()
            d = pos.astype(np.float64) - site_ecef[None, None, :]
            r = np.linalg.norm(d, axis=-1)
            u = site_ecef / np.linalg.norm(site_ecef)
            el_rad = np.arcsin(np.clip(np.einsum("ijk,k->ij", d, u) / r, -1.0, 1.0))
            rrate = range_rate(pos.astype(np.float64), site_ecef, cfg.dt_s)
            elev_deg = np.rad2deg(el_rad)
            s = received_snr_db(
                r,
                el_rad,
                freq_hz=cfg.freq_hz,
                eirp_dbw=cfg.eirp_dbw,
                g_over_t_db=cfg.g_over_t_db,
                bandwidth_hz=cfg.bandwidth_hz,
                rain=cfg.rain_scale,
            )
            c = link_capacity_mbps(s, cfg.bandwidth_hz)
            el[si] = elev_deg.astype(np.float32)
            rng_km[si] = r.astype(np.float32)
            rr[si] = rrate.astype(np.float32)
            snr[si] = s.astype(np.float32)
            cap[si] = c.astype(np.float32)
            dop = doppler_hz(rrate, cfg.freq_hz)
            doprate[si] = np.gradient(dop, cfg.dt_s, axis=1).astype(np.float32)
            if verbose and (si % 5 == 0 or si == n_site - 1):
                print(f"[twin]   site {si + 1}/{n_site} {site.name}")

        # --- remaining visibility and contested service window ------------ #
        # ``trem`` is the geometric time until the elevation crosses the mask,
        # stored as a float with sub-step interpolation so that a 10 s decision
        # step does not quantise the preparation-advance choice.
        #
        # ``service_left`` is the time until the satellite is superseded by a
        # candidate that is more than ``service_margin_deg`` better.  In a dense
        # polar sky many satellites converge over the pole, so this *contested*
        # window is far shorter than the geometric one: a policy that waits for
        # the serving link to degrade has much less preparation time above
        # 70 deg N.  It is exposed to the policy as an urgency signal.
        mask = el > cfg.elev_mask_deg
        big = np.float32(cfg.horizon_s * 10.0)
        sat_ix = np.arange(self.n_sat)[:, None]
        best_el = el.max(axis=1)  # (n_site, nt)

        def _remaining(vis_mask):
            out = np.empty_like(el)
            for si in range(n_site):
                vis = vis_mask[si]
                nxt = np.full(vis.shape, nt, dtype=np.int32)
                cur = np.full(self.n_sat, nt, dtype=np.int32)
                for i in range(nt - 1, -1, -1):
                    col = vis[:, i]
                    cur = np.where(~col, i, cur)
                    nxt[:, i] = cur
                steps_left = (nxt - np.arange(nt)[None, :]).astype(np.float32) * cfg.dt_s
                nxt_c = np.clip(nxt, 0, nt - 1)
                el_now = el[si]
                el_nxt = el_now[sat_ix, nxt_c]
                denom = np.maximum(el_now - el_nxt, 1e-3)
                frac = np.clip((el_now - cfg.elev_mask_deg) / denom, 0.0, 1.0)
                t_float = steps_left - cfg.dt_s * (1.0 - frac)
                out[si] = np.where(vis, t_float, 0.0).astype(np.float32)
                out[si][out[si] > big] = big
            return out

        trem = _remaining(mask)
        serv = mask & ((el - best_el[:, None, :]) > -cfg.service_margin_deg)
        service_left = _remaining(serv)

        # --- ISL topology + gateway hop counts -------------------------- #
        isl_cfg = ISLConfig(
            max_range_km=cfg.isl_max_range_km,
            min_elev_km=cfg.isl_min_elev_km,
            seam_lat_deg=cfg.isl_seam_lat_deg,
            seam_enabled=cfg.isl_seam_enabled,
            max_degree=cfg.isl_max_degree,
            dropout=cfg.isl_dropout,
        )
        rng_np = np.random.default_rng(1234)
        hop = np.full((self.n_sat, nt), -1, dtype=np.int8)
        deg = np.zeros((self.n_sat, nt), dtype=np.int16)
        deg2 = np.zeros((self.n_sat, nt), dtype=np.int16)
        gw_links = np.zeros((self.n_sat, nt), dtype=bool)
        feed_press = np.zeros((self.n_sat, nt), dtype=np.int16)
        for i in range(nt):
            p = pos[:, i, :].astype(np.float64)
            lat_i = lat_sat[:, i]
            adj = build_isl_adjacency(p, isl_cfg, lat_i, nrm[:, i, :])
            if cfg.isl_dropout > 0.0:
                tri = np.triu(adj, 1)
                drop = (rng_np.random(tri.shape) < cfg.isl_dropout) & tri
                adj = (adj & ~drop) & ~drop.T
            # feeder access: each gateway tracks a bounded number of satellites,
            # prioritised by elevation.  Polar gateways see far more candidates
            # than the slot budget, so feeder access is scarce above the seam.
            gset = np.zeros(self.n_sat, dtype=bool)
            for gi in self.gateway_site_index:
                col = el[gi, :, i]
                ok = np.flatnonzero(col > cfg.feeder_min_elev_deg)
                n_cand = ok.size
                if n_cand > cfg.feeder_slots:
                    order = ok[np.argsort(-col[ok])[: cfg.feeder_slots]]
                else:
                    order = ok
                gset[order] = True
                if n_cand:
                    feed_press[ok, i] = np.maximum(feed_press[ok, i], n_cand)
            gw_links[:, i] = gset
            hop[:, i] = hop_count_to_gateway(adj, gset)
            d1, d2 = isl_graph_metrics(adj)
            deg[:, i] = d1
            deg2[:, i] = d2
            if verbose and i % 500 == 0:
                print(f"[twin]   isl step {i + 1}/{nt}")

        # --- candidate shortlist --------------------------------------- #
        k = cfg.k_candidates
        cand_idx = np.full((n_site, nt, k), -1, dtype=np.int16)
        for si in range(n_site):
            e = el[si].T  # (nt, nsat)
            e_masked = np.where(mask[si].T, e, -1e9)
            order = np.argsort(-e_masked, axis=1)[:, :k]
            # a slot is valid only when the satellite is actually above the mask
            ok = np.take_along_axis(e_masked, order, axis=1) > -1e8
            cand_idx[si] = np.where(ok, order, -1).astype(np.int16)

        self._data = dict(
            t_sec=t_sec.astype(np.float32),
            pos=pos.astype(np.float32),
            lat_sat=lat_sat.astype(np.float32),
            lon_sat=lon_sat.astype(np.float32),
            eclipse=ecl,
            nrm=nrm.astype(np.float32),
            el=el,
            rng=rng_km,
            rr=rr,
            snr=snr,
            cap=cap,
            doprate=doprate,
            trem=trem,
            service_left=service_left,
            hop=hop,
            deg=deg,
            deg2=deg2,
            gw_links=gw_links,
            feed_press=feed_press,
            cand_idx=cand_idx,
        )
        self.save()
        meta = dict(
            constellation=cfg.constellation,
            n_sat=int(self.n_sat),
            n_time=int(nt),
            dt_s=cfg.dt_s,
            horizon_s=cfg.horizon_s,
            sites=[s.name for s in self.sites],
            user_sites=[self.sites[i].name for i in self.user_site_index],
            n_gateway_sites=len(self.gateway_site_index),
            config=asdict(cfg),
            coverage=self.coverage_summary(),
        )
        (self.cache_dir / "meta.json").write_text(json.dumps(meta, indent=2))
        if verbose:
            print(f"[twin] saved to {self.cache_dir}")
        return self

    def _array_files(self) -> list[str]:
        return [
            "t_sec", "pos", "lat_sat", "lon_sat", "eclipse", "nrm", "el", "rng", "rr", "service_left",
            "snr", "cap", "doprate", "trem", "hop", "deg", "deg2", "gw_links", "feed_press", "cand_idx",
        ]

    def _missing_files(self) -> list[str]:
        return [n for n in self._array_files() if not (self.cache_dir / f"{n}.npy").exists()]

    def save(self) -> None:
        for k, v in self._data.items():
            np.save(self.cache_dir / f"{k}.npy", v)

    def load(self) -> "DigitalTwin":
        for k in self._array_files():
            self._data[k] = np.load(self.cache_dir / f"{k}.npy", mmap_mode="r")
        self.n_sat = int(self._data["pos"].shape[0])
        meta = json.loads((self.cache_dir / "meta.json").read_text())
        self.meta = meta
        return self

    # ------------------------------------------------------------------ #
    # Accessors
    # ------------------------------------------------------------------ #
    def __getitem__(self, key: str) -> np.ndarray:
        return self._data[key]

    @property
    def n_time(self) -> int:
        return int(self._data["t_sec"].size)

    @property
    def dt(self) -> float:
        return float(self.cfg.dt_s)

    def t_index(self, t_s: float) -> int:
        return int(np.clip(round(t_s / self.cfg.dt_s), 0, self.n_time - 1))

    # ------------------------------------------------------------------ #
    # Diagnostics
    # ------------------------------------------------------------------ #
    def coverage_summary(self) -> dict:
        """Basic sanity statistics: visible-satellite counts and hop distances."""
        cfg = self.cfg
        out = {}
        for si in self.user_site_index:
            site = self.sites[si]
            vis = (self._data["el"][si] > cfg.elev_mask_deg).sum(axis=0)
            served = self._data["el"][si].max(axis=0) > cfg.elev_mask_deg
            out[site.name] = dict(
                lat=site.lat_deg,
                mean_visible=float(vis.mean()),
                max_visible=int(vis.max()),
                coverage_frac=float(served.mean()),
            )
        hop = self._data["hop"]
        out["_hop"] = dict(
            mean_positive=float(hop[hop >= 0].mean()),
            unreachable_frac=float((hop < 0).mean()),
            max=int(hop.max()),
        )
        return out

    def analytic_link_budget(self, site: Site, sat_index: int, t_index: int) -> dict:
        """Closed-form link budget for one satellite/site/instant (validated in 4.8)."""
        cfg = self.cfg
        r = float(self._data["rng"][self.sites.index(site), sat_index, t_index])
        e = float(self._data["el"][self.sites.index(site), sat_index, t_index])
        fspl = 92.45 + 20 * math.log10(r) + 20 * math.log10(cfg.freq_hz / 1e9)
        atm = float(atmospheric_loss_db(np.deg2rad(e), cfg.freq_hz / 1e9, cfg.rain_scale))
        cn0 = cfg.eirp_dbw - fspl - atm - 1.0 + cfg.g_over_t_db + 228.6
        return dict(range_km=r, elevation_deg=e, fspl_db=fspl, atm_db=atm, cn0_dbhz=cn0)
