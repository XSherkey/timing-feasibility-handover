"""Shared vocabulary of the constraint grammar (fields and executable effects).

Kept in a leaf module so that the prompt templates, the schema validator, the
knowledge graph and the surrogate backend all agree on one definition.
"""
from __future__ import annotations

FIELDS = frozenset(
    {
        "elevation_deg",
        "handover_advance_s",
        "isl_hop_count",
        "doppler_rate_hz_s",
        "latitude_abs_deg",
        "snr_db",
        "remaining_visibility_s",
        "plane_change",
        "path_available",
        "buffer_occupancy",
        "battery_state",
        "eclipse",
    }
)

EFFECTS = frozenset(
    {
        "min_advance",
        "forbid_unrouted_target",
        "prefer_same_plane",
        "power_cap",
        "buffer_drain",
        "cap_advance",
        "prefer_long_visibility",
    }
)
