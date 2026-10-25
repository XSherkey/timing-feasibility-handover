"""Metric definitions shared by the campaign, the search proxy and the reports.

Kept in a leaf module so that ``almond.nas.evolution`` can score candidates with
exactly the metric the deployment pipeline reports, without importing the system
module (which imports the evolver).
"""
from __future__ import annotations

import numpy as np

L_MAX_MS = 150.0
L_MIN_MS = 20.0


def satisfaction(rows: list[dict], weights: dict) -> float:
    """S(pi) = 100 * sum_i w_i n_i over the evaluated metrics (paper Sec. 4.1).

    The latency term prefers ``lat_mean`` over ``lat_p95`` when the rows carry it.
    This matters: dual-homing only touches the few epochs around a handover, so a
    p95 latency is structurally blind to the cost of early preparation while the
    mean is not.  Older rows fall back to ``lat_p95``.
    """
    if not rows:
        return float("nan")
    att = np.array([r["attempts"] for r in rows], dtype=float)
    if att.sum() <= 0:
        att = np.ones_like(att)
    w = att / att.sum()
    hsr = float(np.sum(w * np.array([r["hsr"] for r in rows])))
    lats = np.array([r.get("lat_mean", r.get("lat_p95", float("nan"))) for r in rows], dtype=float)
    ok = ~np.isnan(lats)
    lat = float(np.nansum(w[ok] * lats[ok]) / max(w[ok].sum(), 1e-9)) if ok.any() else L_MAX_MS
    pows = np.array([r.get("power_mean", 0.5) for r in rows], dtype=float)
    powm = float(np.nanmean(pows)) if len(pows) else 1.0
    n_rel = np.clip((hsr - 0.5) / 0.5, 0.0, 1.0)
    n_lat = np.clip((L_MAX_MS - lat) / (L_MAX_MS - L_MIN_MS), 0.0, 1.0)
    n_pow = np.clip(1.0 - powm, 0.0, 1.0)
    return float(100.0 * (weights["w_rel"] * n_rel + weights["w_lat"] * n_lat + weights["w_pow"] * n_pow))


def attempt_weighted_hsr(rows: list[dict], min_abs_lat: float | None = 70.0) -> float:
    """Attempt-weighted handover success rate, optionally restricted to a band."""
    if not rows:
        return float("nan")
    sel = rows if min_abs_lat is None else [r for r in rows if abs(r["lat"]) > min_abs_lat]
    if not sel:
        return float("nan")
    att = float(sum(r["attempts"] for r in sel))
    if att <= 0:
        return float("nan")
    return float(sum(r["successes"] for r in sel) / att)
