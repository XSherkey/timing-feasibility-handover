"""Inter-satellite-link topology and routing.

The ISL graph is built per decision epoch from the SGP4 positions.  Two
polar-specific effects are modelled explicitly because they dominate the Arctic
failure mode studied in the paper:

* **Seam suppression**: cross-plane links between counter-rotating planes at
  high latitude have very large relative angular rate and are operationally
  disabled above a configurable latitude (default 70 deg).  With a polar shell
  this removes a large fraction of the cross-plane connectivity exactly where
  the planes converge.
* **Range limit**: links beyond ``max_range_km`` are dropped, which in a sparse
  polar shell increases the hop count to the nearest feeder gateway.

Routing is minimum-hop BFS from the set of satellites that currently hold a
feeder link to a ground gateway.  The hop count feeds the link-acquisition-time
model (route re-programming cost) and the environment's reachability test.
"""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass

import numpy as np
from scipy.spatial import cKDTree

from .geometry import R_EARTH, isl_visible


@dataclass
class ISLConfig:
    max_range_km: float = 5200.0
    min_elev_km: float = 120.0
    seam_lat_deg: float = 70.0  # cross-plane links disabled above this latitude
    seam_enabled: bool = True
    #: number of optical ISL terminals per satellite (2 intra-plane + 2 cross-plane)
    max_degree: int = 4
    #: probability that a legitimate link is unavailable (sparse-ISL regimes)
    dropout: float = 0.0
    seed: int = 0


def _plane_normals(pos: np.ndarray, vel: np.ndarray | None = None) -> np.ndarray:
    """Unit orbit-normal direction for every satellite.

    Two satellites belong to the same orbital plane when their angular-momentum
    directions are (nearly) parallel.  When velocities are available the exact
    specific angular momentum ``r x v`` is used; otherwise the caller must supply
    normals derived from a temporal difference of positions.
    """
    if vel is None:
        raise ValueError("velocities or precomputed normals are required")
    n = np.cross(pos, vel)
    nn = np.linalg.norm(n, axis=-1, keepdims=True)
    return n / np.maximum(nn, 1e-9)


def build_isl_adjacency(
    pos: np.ndarray,
    cfg: ISLConfig,
    lat_deg: np.ndarray,
    normals: np.ndarray | None = None,
) -> np.ndarray:
    """Boolean adjacency matrix for one instant.

    ``pos`` is ``(n_sat, 3)`` in ECEF km, ``lat_deg`` is ``(n_sat,)``,
    ``normals`` is ``(n_sat, 3)`` unit orbit normal.

    Links are added greedily in order of increasing range subject to the
    per-satellite terminal budget ``cfg.max_degree``, which reproduces the
    degree-limited mesh of a real optical-ISL constellation (a satellite cannot
    illuminate every geometrically visible neighbour).
    """
    pos = np.asarray(pos, dtype=np.float64)
    n = pos.shape[0]
    tree = cKDTree(pos)
    pairs = tree.query_pairs(cfg.max_range_km, output_type="ndarray")
    adj = np.zeros((n, n), dtype=bool)
    if not len(pairs):
        return adj
    los = isl_visible(pos, cfg.max_range_km, cfg.min_elev_km)
    keep = los[pairs[:, 0], pairs[:, 1]]
    pairs = pairs[keep]
    if not len(pairs):
        return adj
    if cfg.seam_enabled and normals is not None:
        # same-plane test: angular-momentum directions nearly parallel
        same_plane = np.einsum("ij,ij->i", normals[pairs[:, 0]], normals[pairs[:, 1]]) > 0.995
        high_lat = (np.abs(lat_deg[pairs[:, 0]]) > cfg.seam_lat_deg) | (
            np.abs(lat_deg[pairs[:, 1]]) > cfg.seam_lat_deg
        )
        pairs = pairs[same_plane | (~high_lat)]
        if not len(pairs):
            return adj
    d = np.linalg.norm(pos[pairs[:, 0]] - pos[pairs[:, 1]], axis=1)
    order = np.argsort(d)
    pairs = pairs[order]
    deg = np.zeros(n, dtype=np.int16)
    for a, b in pairs:
        if deg[a] < cfg.max_degree and deg[b] < cfg.max_degree:
            adj[a, b] = True
            adj[b, a] = True
            deg[a] += 1
            deg[b] += 1
    return adj


def hop_count_to_gateway(adj: np.ndarray, gateway_nodes: np.ndarray) -> np.ndarray:
    """Minimum hop count from every satellite to the nearest gateway satellite.

    Satellites that are themselves gateways get 0; unreachable ones get -1.
    """
    n = adj.shape[0]
    dist = np.full(n, -1, dtype=np.int16)
    q: deque[int] = deque()
    for g in np.flatnonzero(gateway_nodes):
        dist[g] = 0
        q.append(int(g))
    if not q:
        return dist
    while q:
        u = q.popleft()
        nbrs = np.flatnonzero(adj[u])
        for v in nbrs:
            if dist[v] < 0:
                dist[v] = dist[u] + 1
                q.append(int(v))
    return dist


def isl_graph_metrics(adj: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Degree and two-hop degree per node."""
    deg = adj.sum(axis=1).astype(np.int16)
    a2 = (adj.astype(np.int8) @ adj.astype(np.int8)) > 0
    deg2 = a2.sum(axis=1).astype(np.int16)
    return deg, deg2


def polar_seam_fraction(adj: np.ndarray, lat_deg: np.ndarray, seam_lat: float = 70.0) -> float:
    """Fraction of potential cross-plane links above the seam latitude that exist."""
    high = np.abs(lat_deg) > seam_lat
    if not np.any(high):
        return float("nan")
    sub = adj[np.ix_(high, high)]
    n = high.sum()
    if n < 2:
        return float("nan")
    return float(sub.sum() / (n * (n - 1)))


def ecef_to_latlon(pos: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    r = np.linalg.norm(pos, axis=-1)
    lat = np.rad2deg(np.arcsin(np.clip(pos[..., 2] / r, -1.0, 1.0)))
    lon = np.rad2deg(np.arctan2(pos[..., 1], pos[..., 0]))
    return lat, lon


def satellite_altitude_km(pos: np.ndarray) -> np.ndarray:
    return np.linalg.norm(pos, axis=-1) - R_EARTH
