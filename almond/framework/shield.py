"""Executable form of committed knowledge-graph constraints (the "shield").

A constraint is compiled into an action transformation
``(env, target_action, advance_action) -> (target_action, advance_action)`` that
runs inside the environment step.  Seven effects are executable:

``min_advance``
    raise the requested preparation lead time to at least ``magnitude`` seconds
    whenever the predicate fires;
``forbid_unrouted_target``
    replace a commanded target that has no feeder route by the best routed
    candidate;
``prefer_same_plane``
    when the predicate fires, prefer a same-plane candidate (no route change);
``power_cap``
    clamp the requested lead time to ``magnitude`` seconds (bounded
    dual-homing) when the battery state is low;
``cap_advance``
    clamp the requested lead time to ``magnitude`` seconds (bounded dual-homing
    under a visibility predicate);
``prefer_long_visibility``
    replace the commanded target by the routed candidate with the longest
    remaining visibility - the remedy for the ``window_exceeded`` class, where the
    requested lead is longer than the target will stay visible;
``buffer_drain``
    prefer the candidate with the lowest queue pressure.

The shield is what the paper calls "injection of the mined constraint": it
changes behaviour *without* retraining the policy weights, so the before/after
comparison of Sec. 4.2 keeps the actor frozen.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .kg import Constraint


def _predicate_mask(c: Constraint, env, target_action=None) -> np.ndarray:
    """Evaluate the constraint predicate on the current batch state.

    ``plane_change`` is a property of the *requested* target, so the target action
    has to be passed in; it was previously hard-coded to zero, which made every
    predicate that mentions a plane change unreachable (the hand-coded oracle rule
    is exactly such a predicate, so that arm silently degenerated into Static-LLM).
    """
    B = env.batch
    si, t = env.site, env.t_idx
    srv = np.maximum(env.serving, 0)
    cand = env.cand_idx[si, t]
    cc = np.maximum(cand, 0)
    trem = env.trem[si, srv, t]
    el_s = env.el[si, srv, t]
    snr_s = env.snr[si, srv, t]
    # plane change of the *requested* handover (0 = no handover requested)
    if target_action is None:
        plane_change = np.zeros(B)
    else:
        ta = np.asarray(target_action, dtype=np.int64)
        has = ta > 0
        tgt = np.where(has, env.cand_idx[si, t, np.maximum(ta - 1, 0)], -1)
        # NB: ``same_plane_mask`` expects the full (B, K) candidate matrix, so the
        # per-row requested target is compared directly against the serving normal.
        n_srv = env.nrm[srv, t]
        n_tgt = env.nrm[np.maximum(tgt, 0), t]
        same = np.einsum("bi,bi->b", n_tgt, n_srv) > 0.995
        plane_change = np.where(has & (tgt >= 0), (~same).astype(np.float64), 0.0)
    leaf = dict(
        elevation_deg=el_s,
        handover_advance_s=np.full(B, env.cfg.a_min_s, dtype=np.float64),
        isl_hop_count=env.hop[srv, t].astype(np.float64),
        doppler_rate_hz_s=env.doprate[si, srv, t],
        latitude_abs_deg=np.abs(env.site_lat[si]),
        snr_db=snr_s,
        remaining_visibility_s=trem,
        plane_change=plane_change,
        path_available=(env.hop[srv, t] >= 0).astype(np.float64),
        buffer_occupancy=env._load_frac(srv, t),
        battery_state=np.where(env.eclipse[srv, t], 0.6, 1.0),
        eclipse=env.eclipse[srv, t].astype(np.float64),
    )
    m = np.ones(B, dtype=bool)
    for a in c.atoms:
        f, op, v = a["field"], a["cmp"], float(a["value"])
        vals = leaf.get(f)
        if vals is None:
            continue
        with np.errstate(invalid="ignore"):
            if op == "<=":
                m &= vals <= v
            elif op == ">=":
                m &= vals >= v
            elif op == "<":
                m &= vals < v
            elif op == ">":
                m &= vals > v
            elif op == "==":
                m &= vals == v
            elif op == "!=":
                m &= vals != v
    return m


def _best_routed(env, idx, same_plane_only: bool = False) -> np.ndarray:
    """Index (1..K) of the best routed candidate, 0 if none."""
    idx = np.asarray(idx, dtype=np.int64)
    si = env.site[idx]
    t = env.t_idx[idx]
    cand = env.cand_idx[si, t]
    cc = np.maximum(cand, 0)
    hop = env.hop[cc, t[:, None]]
    srv = np.maximum(env.serving[idx], 0)
    same = env.same_plane_mask(srv, cand, t)
    el = env.el[si[:, None], cc, t[:, None]]
    ok = (hop >= 0) & (cand >= 0)
    if same_plane_only:
        ok = ok & same
    score = np.where(ok, 1.0 + np.clip(el / 90.0, 0, 1) + 0.5 * same, -1.0)
    best = np.argmax(score, axis=1)
    found = np.take_along_axis(score, best[:, None], axis=1)[:, 0] > 0
    return np.where(found, best + 1, 0).astype(np.int64)


def _best_visibility(env, idx) -> np.ndarray:
    """Index (1..K) of the candidate with the longest remaining visibility."""
    idx = np.asarray(idx, dtype=np.int64)
    si = env.site[idx]
    t = env.t_idx[idx]
    cand = env.cand_idx[si, t]
    cc = np.maximum(cand, 0)
    trem = env.trem[si[:, None], cc, t[:, None]]
    hop = env.hop[cc, t[:, None]]
    ok = (hop >= 0) & (cand >= 0)
    score = np.where(ok, trem, -1.0)
    best = np.argmax(score, axis=1)
    found = np.take_along_axis(score, best[:, None], axis=1)[:, 0] > 0
    return np.where(found, best + 1, 0).astype(np.int64)


def compile_constraint(c: Constraint, env_cfg):
    """Compile one constraint into a closure over (env, target, advance)."""

    def apply(env, target_action: np.ndarray, advance_action: np.ndarray):
        mask = _predicate_mask(c, env, target_action)
        if not np.any(mask):
            return target_action, advance_action
        ta = target_action.copy()
        aa = advance_action.copy()
        if c.effect == "min_advance":
            need_bucket = int(np.ceil((float(c.magnitude) - env_cfg.a_min_s) / env_cfg.a_step_s))
            need_bucket = int(np.clip(need_bucket, 0, env_cfg.a_max_bucket))
            aa = np.where(mask, np.maximum(aa, need_bucket), aa)
        elif c.effect == "forbid_unrouted_target":
            bad = mask & (ta > 0)
            if np.any(bad):
                cand = env.cand_idx[env.site[bad], env.t_idx[bad], np.maximum(ta[bad] - 1, 0)]
                hop = env.hop[np.maximum(cand, 0), env.t_idx[bad]]
                need_fix = hop < 0
                if np.any(need_fix):
                    idx = np.flatnonzero(bad)[need_fix]
                    repl = _best_routed(env, idx)
                    ta[idx] = repl
        elif c.effect == "prefer_same_plane":
            need = mask & (ta > 0)
            if np.any(need):
                idx = np.flatnonzero(need)
                repl = _best_routed(env, idx, same_plane_only=True)
                ta[idx] = np.where(repl > 0, repl, ta[idx])
        elif c.effect == "cap_advance_vis":
            # cap the lead at (remaining visibility - magnitude) on the predicate rows
            si, t = env.site, env.t_idx
            srv = np.maximum(env.serving, 0)
            trem = env.trem[si, srv, t]
            cap_s = np.clip(trem - float(c.magnitude), env_cfg.a_min_s, 26.0)
            cap_bucket = np.rint(np.clip((cap_s - env_cfg.a_min_s) / env_cfg.a_step_s,
                                         0, env_cfg.a_max_bucket)).astype(np.int64)
            aa = np.where(mask & np.isfinite(trem), np.minimum(aa, cap_bucket), aa)
        elif c.effect in ("power_cap", "cap_advance"):
            cap_bucket = int(np.clip((float(c.magnitude) - env_cfg.a_min_s) / env_cfg.a_step_s, 0, env_cfg.a_max_bucket))
            aa = np.where(mask, np.minimum(aa, cap_bucket), aa)
        elif c.effect == "prefer_long_visibility":
            need = mask & (ta > 0)
            if np.any(need):
                idx = np.flatnonzero(need)
                repl = _best_visibility(env, idx)
                ta[idx] = np.where(repl > 0, repl, ta[idx])
        elif c.effect == "buffer_drain":
            need = mask & (ta > 0)
            if np.any(need):
                idx = np.flatnonzero(need)
                repl = _best_routed(env, idx)
                ta[idx] = np.where(repl > 0, repl, ta[idx])
        return ta, aa

    apply.__name__ = f"shield_{c.id}_{c.effect}"
    return apply


def compile_constraints(constraints: list[Constraint], env_cfg):
    """Compose several constraints into one shield (applied in version order)."""
    comps = [compile_constraint(c, env_cfg) for c in constraints]
    if not comps:
        return None

    def shield(env, target_action, advance_action):
        ta, aa = target_action, advance_action
        for f in comps:
            ta, aa = f(env, ta, aa)
        return ta, aa

    shield.__name__ = "shield_" + "+".join(c.id for c in constraints)
    return shield


# --------------------------------------------------------------------------- #
# metrics for the injected-rule experiment
# --------------------------------------------------------------------------- #
@dataclass
class ShieldStats:
    applications: int = 0
    targets_redirected: int = 0
    advances_raised: int = 0
    advances_capped: int = 0
