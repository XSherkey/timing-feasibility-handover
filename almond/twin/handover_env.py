"""Handover-control environment of the ALMOND digital twin.

The environment is a *batched* Markov decision process over ``B`` independent
"service instances".  An instance is one ground terminal (site) observed over a
window of the twin horizon.  At every decision epoch (``dt`` = 10 s) the agent

* selects a **target** among the ``K`` best candidates offered by the twin, or
  decides to keep the current serving satellite, and
* sets the **preparation lead time** ``L = a_min + m * a_step`` seconds, i.e. how
  long the terminal is dual-homed before the radio switch.

A commanded handover succeeds when

1. the target has an inter-satellite route to a feeder gateway,
2. the preparation lead time covers the physical acquisition time ``t_setup``,
3. the preparation still fits inside the serving link's remaining visibility,
4. the target is itself above the elevation mask.

``t_setup`` is geometry-driven (see
:func:`almond.twin.geometry.link_acquisition_time_s`) plus a **plane-change
penalty**: a handover that keeps the orbital plane needs no route change at
all, whereas a cross-plane handover performed *above the polar seam* must
rebuild its feeder route inside the plane, because every cross-plane ISL link is
disabled above the seam latitude.  That asymmetry is the mechanism behind the
polar failure zone studied in the paper.

The reliability signal available to the agent is *session continuity*.  The
hand-crafted baseline of the paper instead optimises a radio-quality proxy
(``use_snr_proxy``), which is what makes it blind to the preparation-timing
constraint.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .geometry import link_acquisition_time_s
from .twin import DigitalTwin

#: latency normalisation bounds of the metric layer (paper Sec. 4.1)
L_MAX_MS = 150.0
L_MIN_MS = 20.0
#: SNR used for the transmit-power normalisation
SNR_REQ_DB = 10.0
#: ISL one-hop latency: propagation over ~4000 km plus optical-switch processing
ISL_HOP_MS = 13.3 + 1.5
#: offline duration (decision epochs) after a session drop
RECONNECT_STEPS = 6


@dataclass
class EnvConfig:
    dt_s: float = 10.0
    episode_steps: int = 240  # 40 min of service per episode
    k_candidates: int = 8
    a_min_s: float = 6.0
    a_step_s: float = 2.0
    a_max_bucket: int = 10
    elev_mask_deg: float = 10.0
    seam_lat_deg: float = 70.0
    #: minimum dwell time between two handover attempts
    dwell_steps: int = 3
    #: power/spectrum cost of one unit of dual-homing time
    dual_homing_cost: float = 0.05
    #: offered load per satellite (Mbps) used by the queueing model
    base_offered_mbps: float = 600.0
    #: traffic multiplier (test splits use 0.5 and 2.0)
    traffic_scale: float = 1.0
    #: session process
    session_arrival_per_min: float = 0.18
    video_duration_s: float = 600.0
    emergency_duration_s: float = 120.0
    #: reward weights (overridden by the intent profile / LLM proposal)
    w_rel: float = 0.34
    w_lat: float = 0.33
    w_pow: float = 0.33
    #: hand-crafted baseline shaping terms
    switch_penalty: float = 0.05
    use_snr_proxy: bool = False
    snr_proxy_ref_db: float = 25.0
    #: failure penalty applied to the reliability sub-reward of the step reward
    drop_penalty: float = 0.30
    #: coefficients of the link-acquisition model (see geometry.py)
    acq_signaling_s: float = 1.2
    acq_sync_base_s: float = 0.6
    acq_doppler_coeff: float = 0.0001
    acq_hop_coeff: float = 0.10
    acq_lowel_coeff: float = 0.6
    seam_penalty_s: float = 6.0
    crossplane_penalty_s: float = 0.3
    #: cost of waiting for a free feeder slot at the target gateway (seconds)
    feeder_slot_cost_s: float = 1.8
    #: reward-shaping terms that mimic a committed constraint *as a penalty*
    #: (the "penalty" arm of the penalty-vs-shield experiment).  Off by default.
    late_risk_tau: float = 0.0      # 0 disables; e.g. 16.0 s
    late_risk_lat: float = 68.0     # regime threshold (deg)
    late_risk_weight: float = 0.0   # penalty per late-risky decision
    #: cost of *early preparation*: while the terminal waits for the new link it
    #: runs dual-homing, splitting RF chains between the old and the new beam.
    #: Without this the optimal lead is simply "as long as possible" and the whole
    #: control problem collapses to a constant (measured: max-elevation + 20 s
    #: saturates the twin).  0 disables (legacy behaviour, default).
    dual_homing_latency_ms_per_s: float = 0.0
    dual_homing_power_per_s: float = 0.0
    #: running availability window (decision epochs)
    avail_window: int = 12
    #: per-attempt oracle shield: clamp the polar lead to the *realised* acquisition
    #: requirement.  An upper reference for any policy-independent threshold, and a
    #: diagnostic of how much of the residual loss is estimation rather than targeting.
    oracle_min_advance: bool = False


class HandoverEnv:
    """Batched handover MDP over the digital twin."""

    def __init__(self, twin: DigitalTwin, cfg: EnvConfig | None = None, batch: int = 32, seed: int = 0):
        self.twin = twin
        self.cfg = cfg or EnvConfig()
        self.batch = batch
        self.rng = np.random.default_rng(seed)
        self.n_sites = len(twin.sites)
        self.nsat = twin.n_sat
        self.nt = twin.n_time
        self.K = self.cfg.k_candidates
        self.n_advance = self.cfg.a_max_bucket + 1
        self._bind_arrays()
        self._allocate()

    # ------------------------------------------------------------------ #
    # set-up
    # ------------------------------------------------------------------ #
    def _bind_arrays(self) -> None:
        t = self.twin
        self.el = t["el"]
        self.snr = t["snr"]
        self.rng_km = t["rng"]
        self.rrate = t["rr"]
        self.cap = t["cap"]
        self.trem = t["trem"]
        self.service_left = t["service_left"]
        self.doprate = t["doprate"]
        self.hop = t["hop"]
        self.deg = t["deg"]
        self.deg2 = t["deg2"]
        self.lat_sat = t["lat_sat"]
        self.eclipse = t["eclipse"]
        self.nrm = t["nrm"]
        self.cand_idx = t["cand_idx"]
        self.feed_press = t["feed_press"]
        self.user_idx = np.asarray(self.twin.user_site_index, dtype=np.int32)
        self.site_lat = np.asarray([s.lat_deg for s in self.twin.sites], dtype=np.float32)
        self.site_pvideo = np.asarray([s.video_frac for s in self.twin.sites], dtype=np.float32)

    def _allocate(self) -> None:
        B = self.batch
        self.site = np.zeros(B, dtype=np.int32)
        self.t_idx = np.zeros(B, dtype=np.int32)
        self.serving = np.full(B, -1, dtype=np.int32)
        self.session = np.zeros(B, dtype=bool)
        self.offline = np.zeros(B, dtype=np.int32)
        self.cooldown = np.zeros(B, dtype=np.int32)
        self.avail_hist = np.zeros((B, self.cfg.avail_window), dtype=np.float32)
        self.avail_ptr = np.zeros(B, dtype=np.int32)
        self.steps = np.zeros(B, dtype=np.int32)
        self.attempts = np.zeros(B, dtype=np.int64)
        self.successes = np.zeros(B, dtype=np.int64)
        self.drops = np.zeros(B, dtype=np.int64)
        self.late_attempts = np.zeros(B, dtype=np.int64)
        self.handover_counts = np.zeros(B, dtype=np.int64)
        self.lead_used = np.zeros(B, dtype=np.float32)
        self.dual_homing = np.zeros(B, dtype=np.float32)
        self.last_action = np.zeros(B, dtype=np.int64)
        self.lat_hist: list[np.ndarray] = []
        self.pow_hist: list[np.ndarray] = []
        self.snr_hist: list[np.ndarray] = []
        self.attempt_log: list[dict] = []

    # ------------------------------------------------------------------ #
    # episode management
    # ------------------------------------------------------------------ #
    def reset(
        self,
        sites: np.ndarray | None = None,
        starts: np.ndarray | None = None,
        t_range: tuple[int, int] | None = None,
    ) -> np.ndarray:
        B = self.batch
        cfg = self.cfg
        if sites is None:
            sites = self.user_idx[self.rng.integers(0, len(self.user_idx), size=B)]
        self.site = np.asarray(sites, dtype=np.int32)
        if starts is None:
            lo, hi = (0, self.nt - cfg.episode_steps - 2) if t_range is None else t_range
            hi = max(lo + 1, hi - cfg.episode_steps)
            starts = self.rng.integers(lo, hi, size=B)
        self.t_idx = np.asarray(starts, dtype=np.int32)
        self.serving = self._initial_serving()
        self.session = self.rng.random(B) < 0.85
        self.offline = np.zeros(B, dtype=np.int32)
        self.cooldown = np.zeros(B, dtype=np.int32)
        self.avail_hist[:] = self.session[:, None]
        self.avail_ptr[:] = 0
        self.steps[:] = 0
        self.attempts[:] = 0
        self.successes[:] = 0
        self.drops[:] = 0
        self.late_attempts[:] = 0
        self.handover_counts[:] = 0
        self.lead_used[:] = 0.0
        self.dual_homing[:] = 0.0
        self.last_action[:] = 0
        self.lat_hist = []
        self.pow_hist = []
        self.snr_hist = []
        self.attempt_log = []
        return self.obs()

    def teacher_action(self) -> tuple[np.ndarray, np.ndarray]:
        """Analytic controller used only to warm-start the actor (behaviour clone).

        Picks, among the candidates that are visible and routed, the one whose
        acquisition time fits inside the remaining visibility and whose elevation
        is highest; the requested lead is the smallest advance bucket that still
        covers the acquisition time.  This is the twin's own physics, not a tuned
        policy: it exists so the PPO actor does not have to discover the lead-time
        structure by exploration, which is what made half the seeds collapse onto
        "never hand over".
        """
        cfg = self.cfg
        B = self.batch
        si, t = self.site, self.t_idx
        cand = self.cand_idx[si, t]                      # (B, K)
        K = cand.shape[1]
        cc = np.maximum(cand, 0)
        valid = cand >= 0
        el = np.where(valid, self.el[si[:, None], cc, t[:, None]], -1.0)
        hop = np.where(valid, self.hop[cc, t[:, None]], -1.0)
        trem = np.where(valid, self.trem[si[:, None], cc, t[:, None]], 0.0)
        srv = np.maximum(self.serving, 0)
        # flatten to evaluate the acquisition time for every (terminal, candidate)
        t_setup = self._acq_time(
            np.repeat(si, K), np.repeat(srv, K), cc.reshape(-1), np.repeat(t, K)
        ).reshape(B, K)
        feasible = valid & (hop >= 0) & (el > cfg.elev_mask_deg) & (t_setup <= trem)
        score = np.where(feasible, el, -1e9)
        best = np.argmax(score, axis=1)
        has = feasible[np.arange(B), best]
        target = np.where(has, best + 1, 0).astype(np.int64)
        need = t_setup[np.arange(B), best]
        bucket = np.ceil((need - cfg.a_min_s) / cfg.a_step_s)
        bucket = np.clip(np.nan_to_num(bucket, nan=0.0), 0, cfg.a_max_bucket).astype(np.int64)
        return target, np.where(has, bucket, 0).astype(np.int64)

    def _initial_serving(self) -> np.ndarray:
        c = self.cand_idx[self.site, self.t_idx, 0]
        el_c = self.el[self.site, c, self.t_idx]
        return np.where((c >= 0) & (el_c > self.cfg.elev_mask_deg), c, -1).astype(np.int32)

    # ------------------------------------------------------------------ #
    # geometry helpers
    # ------------------------------------------------------------------ #
    def _acq_time(self, si, srv, tgt, t) -> np.ndarray:
        """Link acquisition time for a handover from ``srv`` to ``tgt``."""
        cfg = self.cfg
        el_t = self.el[si, tgt, t]
        dop = self.doprate[si, tgt, t]
        hop = self.hop[tgt, t]
        same_plane = np.einsum(
            "ij,ij->i", self.nrm[srv, t].astype(np.float64), self.nrm[tgt, t].astype(np.float64)
        ) > 0.995
        above_seam = np.abs(self.lat_sat[tgt, t]) > cfg.seam_lat_deg
        base = link_acquisition_time_s(
            np.deg2rad(el_t),
            dop,
            np.maximum(hop, 0),
            self.feed_press[tgt, t],
            feeder_slots=int(getattr(self.twin.cfg, "feeder_queue_slots", 3)),
            t_slot_s=cfg.feeder_slot_cost_s,
            t_signaling_s=cfg.acq_signaling_s,
            t_sync_base_s=cfg.acq_sync_base_s,
            doppler_coeff_s=cfg.acq_doppler_coeff,
            hop_coeff_s=cfg.acq_hop_coeff,
            low_el_coeff_s=cfg.acq_lowel_coeff,
        )
        plane_penalty = np.where(
            same_plane, 0.0, np.where(above_seam, cfg.seam_penalty_s, cfg.crossplane_penalty_s)
        )
        return base + plane_penalty

    def same_plane_mask(self, srv: np.ndarray, cand: np.ndarray, t: np.ndarray) -> np.ndarray:
        """(B, K) mask: candidate shares the serving satellite's orbital plane."""
        cc = np.maximum(cand, 0)
        return np.einsum("bki,bi->bk", self.nrm[cc, t[:, None]], self.nrm[srv, t]) > 0.995

    def _latency_ms(self, si, srv, t) -> np.ndarray:
        cfg = self.cfg
        rng_km = self.rng_km[si, srv, t]
        hop = np.maximum(self.hop[srv, t], 0)
        cap = np.maximum(self.cap[si, srv, t], 1.0)
        load = np.minimum(0.985, cfg.base_offered_mbps * cfg.traffic_scale / cap)
        queue = 4.0 * load / (1.0 - load)
        return rng_km / 299.792458 + hop * ISL_HOP_MS + queue

    def _power_norm(self, si, srv, t) -> np.ndarray:
        snr = self.snr[si, srv, t]
        p = 10.0 ** ((SNR_REQ_DB - snr) / 10.0)
        p = np.where(self.eclipse[srv, t], p * 1.35, p)
        return np.clip(p / 1.5, 0.0, 1.0)

    # ------------------------------------------------------------------ #
    # observation
    # ------------------------------------------------------------------ #
    @property
    def obs_dim(self) -> int:
        return 14 + 4 + 6 * self.K + 3

    def obs(self) -> np.ndarray:
        B = self.batch
        si, t = self.site, self.t_idx
        srv = np.maximum(self.serving, 0)
        el_s = self.el[si, srv, t]
        snr_s = self.snr[si, srv, t]
        rr_s = self.rrate[si, srv, t]
        dop_s = self.doprate[si, srv, t]
        trem_s = self.trem[si, srv, t]
        svc_s = self.service_left[si, srv, t]
        hop_s = self.hop[srv, t]
        cap_s = self.cap[si, srv, t]
        lat_band = np.clip(np.abs(self.site_lat[si]) / 90.0, 0.0, 1.0)

        cand = self.cand_idx[si, t]
        c_valid = cand >= 0
        cc = np.maximum(cand, 0)
        el_c = self.el[si[:, None], cc, t[:, None]]
        snr_c = self.snr[si[:, None], cc, t[:, None]]
        hop_c = self.hop[cc, t[:, None]]
        cap_c = self.cap[si[:, None], cc, t[:, None]]
        same = self.same_plane_mask(srv, cand, t)
        path_ok = (hop_c >= 0) & c_valid
        hop_mean = np.nan_to_num(np.where(path_ok, hop_c, 0).mean(axis=1))

        f_buf = np.clip(self._load_frac(srv, t), 0.0, 1.0)
        core = np.stack(
            [
                np.clip(snr_s / 30.0, 0.0, 1.5),
                np.clip(el_s / 90.0, 0.0, 1.0),
                np.clip(np.abs(rr_s) / 8.0, 0.0, 1.0),
                np.clip(np.abs(dop_s) / 6.0e3, 0.0, 1.0),
                np.clip(dop_s / 1.0e3, -5.0, 5.0),
                f_buf,
                np.clip(hop_mean / 15.0, 0.0, 1.0),
                np.where(self.eclipse[srv, t], 0.6, 1.0),
                self._power_norm(si, srv, t),
                np.clip(self.deg[srv, t] / 4.0, 0.0, 1.0),
                np.clip(self.deg2[srv, t] / 12.0, 0.0, 1.0),
                self.eclipse[srv, t].astype(np.float32),
                lat_band.astype(np.float32),
                np.where(self.session, self.site_pvideo[si], 0.0).astype(np.float32),
            ],
            axis=1,
        )
        srv_block = np.stack(
            [
                np.clip(svc_s / 300.0, 0.0, 1.5),
                np.clip(trem_s / 600.0, 0.0, 1.5),
                np.clip(np.maximum(hop_s, 0) / 15.0, 0.0, 1.0),
                np.clip(cap_s / 1200.0, 0.0, 1.2),
            ],
            axis=1,
        )
        cand_block = np.stack(
            [
                np.clip(el_c / 90.0, 0.0, 1.0),
                np.clip(snr_c / 30.0, 0.0, 1.5),
                np.clip(np.maximum(hop_c, 0) / 15.0, 0.0, 1.0),
                np.clip(cap_c / 1200.0, 0.0, 1.2),
                same.astype(np.float32),
                path_ok.astype(np.float32),
            ],
            axis=2,
        ).reshape(B, -1)
        adj_block = np.stack(
            [
                np.clip(self.deg[srv, t] / 4.0, 0.0, 1.0),
                np.clip(self.deg2[srv, t] / 12.0, 0.0, 1.0),
                np.clip(hop_mean / 15.0, 0.0, 1.0),
            ],
            axis=1,
        )
        return np.concatenate([core, srv_block, cand_block, adj_block], axis=1).astype(np.float32)

    def candidate_graph(self) -> tuple[np.ndarray, np.ndarray]:
        """Local handover subgraph for the graph-grammar policies.

        ``x`` is ``(B, 1 + K, 7)`` and ``adj`` is ``(B, 1 + K, 1 + K)``.
        Node 0 is the serving satellite, nodes ``1..K`` the candidate shortlist.
        Candidates sharing an orbital plane are connected (no route change is
        needed to move between them).
        """
        B, K = self.batch, self.K
        si, t = self.site, self.t_idx
        srv = np.maximum(self.serving, 0)
        cand = self.cand_idx[si, t]
        valid = (cand >= 0).astype(np.float32)
        cc = np.maximum(cand, 0)
        el_c = np.clip(self.el[si[:, None], cc, t[:, None]] / 90.0, 0.0, 1.0)
        snr_c = np.clip(self.snr[si[:, None], cc, t[:, None]] / 30.0, 0.0, 1.5)
        hop_c = np.clip(np.maximum(self.hop[cc, t[:, None]], 0) / 15.0, 0.0, 1.0)
        cap_c = np.clip(self.cap[si[:, None], cc, t[:, None]] / 1200.0, 0.0, 1.2)
        path_c = (self.hop[cc, t[:, None]] >= 0).astype(np.float32)
        nrm_c = self.nrm[cc, t[:, None]]
        srv_snr = np.clip(self.snr[si, srv, t] / 30.0, 0.0, 1.5)
        srv_el = np.clip(self.el[si, srv, t] / 90.0, 0.0, 1.0)
        srv_hop = np.clip(np.maximum(self.hop[srv, t], 0) / 15.0, 0.0, 1.0)
        srv_cap = np.clip(self.cap[si, srv, t] / 1200.0, 0.0, 1.2)
        srv_feat = np.stack(
            [srv_el, srv_snr, srv_hop, srv_cap, np.ones(B, np.float32), np.ones(B, np.float32),
             np.zeros(B, np.float32)],
            axis=1,
        )
        cand_feat = np.stack([el_c, snr_c, hop_c, cap_c, path_c, valid, np.ones_like(path_c)], axis=2)
        x = np.concatenate([srv_feat[:, None, :], cand_feat], axis=1)
        dot = np.einsum("bki,bji->bkj", nrm_c, nrm_c)
        adj = np.zeros((B, K + 1, K + 1), dtype=np.float32)
        adj[:, 0, 1:] = valid
        adj[:, 1:, 0] = valid
        adj[:, 1:, 1:] = (dot > 0.995).astype(np.float32)
        idx = np.arange(K + 1)
        adj[:, idx, idx] = 1.0
        return x.astype(np.float32), adj

    def _load_frac(self, srv, t) -> np.ndarray:
        si = self.site
        cap = np.maximum(self.cap[si, srv, t], 1.0)
        return self.cfg.base_offered_mbps * self.cfg.traffic_scale / cap

    # ------------------------------------------------------------------ #
    # dynamics
    # ------------------------------------------------------------------ #
    def step(self, target_action, advance_action, shield=None, record: bool = False):
        """Advance one decision epoch.

        ``target_action`` in ``[0, K]`` (0 = keep), ``advance_action`` in
        ``[0, a_max_bucket]``.  ``shield`` is an optional callable
        ``(env, target, advance) -> (target, advance)`` implementing committed
        knowledge-graph constraints.
        """
        cfg = self.cfg
        B = self.batch
        tgt_a = np.asarray(target_action, dtype=np.int64)
        adv_a = np.asarray(advance_action, dtype=np.int64)
        if shield is not None:
            tgt_a, adv_a = shield(self, tgt_a, adv_a)
        self.t_idx = np.minimum(self.t_idx + 1, self.nt - 1)
        self.steps += 1
        t = self.t_idx
        si = self.site

        # --- traffic process ---------------------------------------------- #
        # ``session`` is the user's demand for service; ``offline`` is the link
        # re-establishment timer.  A dropped link *stalls* the session for
        # ``RECONNECT_STEPS`` epochs but does not cancel it -- if it did, the
        # terminal would stay out of service until the next Poisson arrival
        # (about 11 minutes), which both dominates the reward and makes the
        # environment unlearnable.
        self.offline = np.maximum(self.offline - 1, 0)
        self.cooldown = np.maximum(self.cooldown - 1, 0)
        p_arr = 1.0 - np.exp(-cfg.session_arrival_per_min / 60.0 * cfg.dt_s)
        self.session = self.session | (self.rng.random(B) < p_arr * cfg.traffic_scale)
        dur = np.where(
            self.rng.random(B) < self.site_pvideo[si], cfg.video_duration_s, cfg.emergency_duration_s
        )
        self.session = self.session & (self.rng.random(B) > cfg.dt_s / dur)

        need = self.session & (self.serving < 0) & (self.offline == 0)
        if np.any(need):
            best = self.cand_idx[si[need], t[need], 0]
            el_b = self.el[si[need], best, t[need]]
            self.serving[need] = np.where(el_b > cfg.elev_mask_deg, best, -1)
            self.cooldown[need] = cfg.dwell_steps

        # --- serving link state ------------------------------------------- #
        srv = self.serving
        srv_c = np.maximum(srv, 0)
        trem_s = np.where(srv >= 0, self.trem[si, srv_c, t], 0.0)

        # --- commanded handovers ------------------------------------------ #
        lead = cfg.a_min_s + adv_a * cfg.a_step_s
        commanded = (tgt_a > 0) & (srv >= 0) & (self.cooldown == 0) & self.session
        success = np.zeros(B, dtype=bool)
        failure = np.zeros(B, dtype=bool)
        t_setup = np.full(B, np.inf)
        targets = np.full(B, -1, dtype=np.int32)
        if np.any(commanded):
            idx = np.flatnonzero(commanded)
            tgt = self.cand_idx[si[idx], t[idx], tgt_a[idx] - 1]
            targets[idx] = tgt
            hop_t = self.hop[tgt, t[idx]]
            t_setup[idx] = self._acq_time(si[idx], srv[idx], tgt, t[idx])
            if cfg.oracle_min_advance:
                # per-attempt oracle: give the controller exactly the lead this
                # particular handover needs, but only inside the polar scope of the
                # mined rule (so the comparison isolates the threshold, not the scope)
                polar = np.abs(self.site_lat[si[idx]]) >= 68.0
                lead[idx] = np.where(polar, np.maximum(lead[idx], t_setup[idx]), lead[idx])
            el_t = self.el[si[idx], tgt, t[idx]]
            path_ok = (hop_t >= 0) & (tgt >= 0)
            lead_ok = lead[idx] >= t_setup[idx]
            fits = lead[idx] <= trem_s[idx]
            visible = el_t > cfg.elev_mask_deg
            ok = path_ok & lead_ok & fits & visible
            success[idx[ok]] = True
            failure[idx[~ok]] = True
            # WHY the attempt failed, as an error code a real gateway would log.
            # This is what the enriched discovery set feeds to the forensic loop;
            # without it the narratives only say "session lost", which biases the
            # mined hypothesis towards whichever cause happens to sort first.
            cause = np.where(
                ok, "ok",
                np.where(~visible, "below_elevation",
                         np.where(~path_ok, "no_route",
                                  np.where(~lead_ok, "late_handover", "window_exceeded"))),
            )
            self.attempts[idx] += 1
            self.successes[idx[ok]] += 1
            self.late_attempts[idx[~ok & ~fits]] += 1
            self.serving[idx[ok]] = tgt[ok]
            self.cooldown[idx] = cfg.dwell_steps
            self.lead_used[idx] = lead[idx]
            if record:
                self._log_attempt(idx, t, srv, tgt, lead, trem_s, t_setup, hop_t, el_t, ok, cause)
        self.last_action = tgt_a * self.n_advance + adv_a
        max_lead = cfg.a_min_s + cfg.a_max_bucket * cfg.a_step_s
        self.dual_homing = np.where(commanded, lead / max_lead, 0.0)

        if np.any(failure):
            self.drops[failure] += 1
            self.offline[failure] = RECONNECT_STEPS
            self.serving[failure] = -1

        # --- unplanned link loss ------------------------------------------ #
        srv = self.serving
        srv_c = np.maximum(srv, 0)
        el_s = self.el[si, srv_c, t]
        up = (srv >= 0) & (el_s > cfg.elev_mask_deg)
        lost = self.session & (~up) & (self.offline == 0)
        if np.any(lost):
            self.drops[lost] += 1
            self.attempts[lost] += 1
            self.offline[lost] = RECONNECT_STEPS
            self.serving[lost] = -1

        up = (self.serving >= 0) & (
            self.el[si, np.maximum(self.serving, 0), t] > cfg.elev_mask_deg
        )
        served = self.session & up

        # --- metrics ------------------------------------------------------ #
        lat = np.full(B, np.nan)
        pow_n = np.full(B, np.nan)
        snr_now = np.zeros(B)
        if np.any(served):
            s2 = self.serving[served]
            lat[served] = self._latency_ms(si[served], s2, t[served])
            pow_n[served] = self._power_norm(si[served], s2, t[served])
            snr_now[served] = self.snr[si[served], s2, t[served]]
        lat_metric = np.where(np.isnan(lat), L_MAX_MS * 1.5, lat)
        pow_metric = np.where(np.isnan(pow_n), 1.0, pow_n) + cfg.dual_homing_cost * self.dual_homing
        slack = np.zeros(B)
        if cfg.dual_homing_latency_ms_per_s or cfg.dual_homing_power_per_s:
            # Dual-homing is not free, and the cost is the *slack*, not the lead:
            # a terminal that commands a handover ``lead`` seconds ahead gets the
            # new link up after ``t_setup``, so it holds two links for
            # ``max(0, lead - t_setup)`` seconds.  A lead shorter than the setup
            # time simply fails; a lead much longer than it wastes capacity.  The
            # optimum is therefore interior, and it moves with the regime.
            slack = np.where(commanded & success, np.maximum(lead - t_setup, 0.0), 0.0)
            lat_metric = lat_metric + cfg.dual_homing_latency_ms_per_s * slack
            pow_metric = pow_metric + cfg.dual_homing_power_per_s * slack

        self.avail_hist[np.arange(B), self.avail_ptr] = served.astype(np.float32)
        self.avail_ptr = (self.avail_ptr + 1) % cfg.avail_window
        avail = self.avail_hist.mean(axis=1)

        n_rel = np.clip((avail - 0.5) / 0.5, 0.0, 1.0)
        n_lat = np.clip((L_MAX_MS - lat_metric) / (L_MAX_MS - L_MIN_MS), 0.0, 1.0)
        n_pow = np.clip(1.0 - pow_metric, 0.0, 1.0)
        if cfg.use_snr_proxy:
            # hand-crafted baseline: reliability is a *radio-quality* proxy, so a
            # session-continuity failure caused by insufficient preparation time
            # is not represented in the reward
            n_rel = np.clip(snr_now / cfg.snr_proxy_ref_db, 0.0, 1.0)
        reward = cfg.w_rel * n_rel + cfg.w_lat * n_lat + cfg.w_pow * n_pow
        if cfg.switch_penalty:
            reward = reward - cfg.switch_penalty * commanded.astype(np.float32)
        if cfg.drop_penalty:
            reward = np.where(failure | lost, reward - cfg.drop_penalty, reward)
        if cfg.late_risk_tau > 0.0 and cfg.late_risk_weight:
            # the same knowledge as the shield, injected as a *reward penalty*:
            # the agent has to learn to obey it, which is what the penalty-vs-shield
            # contrast measures.
            risky = commanded & (lead < cfg.late_risk_tau) & (np.abs(self.site_lat[si]) >= cfg.late_risk_lat)
            reward = np.where(risky, reward - cfg.late_risk_weight, reward)

        # report the *effective* latency / power so that the satisfaction metric sees
        # the same dual-homing cost the reward does (otherwise the KPI would ignore
        # a cost the learner pays, and "longest lead" would look free in the table)
        self.lat_hist.append((lat + cfg.dual_homing_latency_ms_per_s * slack).copy())
        self.pow_hist.append((pow_n + cfg.dual_homing_power_per_s * slack).copy())
        self.snr_hist.append(snr_now.copy())
        self.handover_counts += success

        done = self.steps >= cfg.episode_steps
        info = dict(
            success=success,
            failure=failure,
            lost=lost,
            served=served,
            commanded=commanded,
            t_setup=t_setup,
            targets=targets,
            lead=lead,
            reward=reward,
        )
        return self.obs(), reward.astype(np.float32), np.full(B, done), info

    def _log_attempt(self, idx, t, srv, tgt, lead, trem_s, t_setup, hop_t, el_t, ok, cause=None) -> None:
        """Record one attempt with the full telemetry a forensic rule may use."""
        si = self.site
        nrm_s = self.nrm[srv[idx], t[idx]]
        nrm_t = self.nrm[tgt, t[idx]]
        same = np.einsum("ij,ij->i", nrm_s, nrm_t) > 0.995
        snr_t = self.snr[si[idx], tgt, t[idx]]
        dop = self.doprate[si[idx], tgt, t[idx]]
        lat_t = np.abs(self.lat_sat[tgt, t[idx]])
        load = (self.cfg.base_offered_mbps * self.cfg.traffic_scale) / np.maximum(
            self.cap[si[idx], np.maximum(srv[idx], 0), t[idx]], 1.0
        )
        batt = np.where(self.eclipse[np.maximum(srv[idx], 0), t[idx]], 0.6, 1.0)
        for j, b in enumerate(idx):
            self.attempt_log.append(
                dict(
                    step=int(self.steps[b]),
                    t_index=int(t[b]),
                    site=self.twin.sites[int(si[b])].name,
                    lat=float(self.site_lat[si[b]]),
                    serving=int(srv[b]),
                    target=int(tgt[j]),
                    elevation_deg=float(el_t[j]),
                    handover_advance_s=float(lead[b]),
                    isl_hop_count=int(hop_t[j]),
                    doppler_rate_hz_s=float(dop[j]),
                    latitude_abs_deg=float(self.site_lat[si[b]]),
                    satellite_latitude_deg=float(lat_t[j]),
                    snr_db=float(snr_t[j]),
                    remaining_visibility_s=float(trem_s[b]),
                    plane_change=float(0.0 if same[j] else 1.0),
                    path_available=float(1.0 if hop_t[j] >= 0 else 0.0),
                    buffer_occupancy=float(load[j]),
                    battery_state=float(batt[j]),
                    eclipse=float(self.eclipse[max(int(srv[b]), 0), t[b]]),
                    t_setup_s=float(t_setup[b]),
                    success=bool(ok[j]),
                    cause=str(cause[j]) if cause is not None else ("ok" if ok[j] else "unknown"),
                )
            )

    # ------------------------------------------------------------------ #
    # episode statistics
    # ------------------------------------------------------------------ #
    def episode_stats(self) -> dict:
        att = np.maximum(self.attempts, 1)
        lat = np.stack(self.lat_hist, axis=0) if self.lat_hist else np.zeros((1, self.batch))
        with np.errstate(invalid="ignore"):
            if np.any(~np.isnan(lat)):
                lat_p95 = np.nanpercentile(lat, 95, axis=0)
                lat_mean = np.nanmean(lat, axis=0)
            else:
                lat_p95 = np.full(self.batch, np.nan)
                lat_mean = np.full(self.batch, np.nan)
        return dict(
            hsr=self.successes / att,
            attempts=self.attempts.copy(),
            successes=self.successes.copy(),
            drops=self.drops.copy(),
            handovers=self.handover_counts.copy(),
            lat_p95=lat_p95,
            lat_mean=lat_mean,
            served_frac=np.mean(~np.isnan(lat), axis=0),
        )
