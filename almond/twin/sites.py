"""Ground sites: user terminals and gateway (feeder-link) stations.

The reference scenario is an Arctic video service above 70 deg N, following the
manuscript.  Additional sites at lower latitudes provide the latitude bins used
by the reliability figure and the generalisation scenarios (equatorial shell,
mid-latitude shell).
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np

R_EARTH = 6378.137  # km


@dataclass(frozen=True)
class Site:
    """A fixed ground terminal."""

    name: str
    lat_deg: float
    lon_deg: float
    alt_km: float = 0.0
    #: user terminals carry traffic; gateways provide feeder links.  A site may
    #: be both (e.g. Svalbard ground station with a co-located test terminal).
    is_user: bool = True
    is_gateway: bool = True
    #: relative weight of video vs emergency traffic for this site
    video_frac: float = 0.7
    region: str = "arctic"

    @property
    def lat_bin(self) -> float:
        """Latitude used for binning (absolute value)."""
        return abs(self.lat_deg)

    def ecef(self) -> np.ndarray:
        lat = math.radians(self.lat_deg)
        lon = math.radians(self.lon_deg)
        r = R_EARTH + self.alt_km
        return np.array(
            [r * math.cos(lat) * math.cos(lon), r * math.cos(lat) * math.sin(lon), r * math.sin(lat)],
            dtype=np.float64,
        )

    def up(self) -> np.ndarray:
        lat = math.radians(self.lat_deg)
        lon = math.radians(self.lon_deg)
        return np.array(
            [math.cos(lat) * math.cos(lon), math.cos(lat) * math.sin(lon), math.sin(lat)],
            dtype=np.float64,
        )

    def east(self) -> np.ndarray:
        lat = math.radians(self.lat_deg)
        lon = math.radians(self.lon_deg)
        return np.array([-math.sin(lon), math.cos(lon), 0.0], dtype=np.float64)

    def north(self) -> np.ndarray:
        lat = math.radians(self.lat_deg)
        lon = math.radians(self.lon_deg)
        return np.array(
            [-math.sin(lat) * math.cos(lon), -math.sin(lat) * math.sin(lon), math.cos(lat)],
            dtype=np.float64,
        )


#: Reference Arctic user terminals (> 70 deg N) plus lower-latitude sites that
#: populate the latitude bins of the reliability study.
USER_SITES: list[Site] = [
    Site("Alert", 82.50, -62.35, is_user=True, is_gateway=False, video_frac=0.8, region="arctic"),
    Site("Longyearbyen", 78.22, 15.65, is_user=True, is_gateway=True, video_frac=0.7, region="arctic"),
    Site("Resolute", 74.70, -94.83, is_user=True, is_gateway=False, video_frac=0.75, region="arctic"),
    Site("SachsHarbour", 71.99, -125.25, is_user=True, is_gateway=False, video_frac=0.7, region="arctic"),
    Site("Tromso", 69.65, 18.96, is_user=True, is_gateway=True, video_frac=0.6, region="subarctic"),
    Site("Kiruna", 67.85, 20.97, is_user=True, is_gateway=True, video_frac=0.6, region="subarctic"),
    Site("Fairbanks", 64.84, -147.72, is_user=True, is_gateway=True, video_frac=0.6, region="subarctic"),
    Site("Reykjavik", 64.13, -21.90, is_user=True, is_gateway=False, video_frac=0.55, region="subarctic"),
    Site("Edinburgh", 55.95, -3.19, is_user=True, is_gateway=True, video_frac=0.5, region="midlat"),
    Site("Berlin", 52.52, 13.40, is_user=True, is_gateway=True, video_frac=0.5, region="midlat"),
    Site("Rome", 41.90, 12.50, is_user=True, is_gateway=False, video_frac=0.5, region="midlat"),
    Site("Nairobi", -1.29, 36.82, is_user=True, is_gateway=True, video_frac=0.45, region="equatorial"),
    Site("Singapore", 1.35, 103.82, is_user=True, is_gateway=True, video_frac=0.45, region="equatorial"),
    Site("Quito", -0.18, -78.47, is_user=True, is_gateway=False, video_frac=0.45, region="equatorial"),
]

#: Dedicated feeder-link stations (no user traffic).  Added to the gateway set so
#: that the ISL routing burden matches a realistic ground-segment deployment.
GATEWAY_SITES: list[Site] = [
    Site("Svalbard_GS", 78.23, 15.39, is_user=False, is_gateway=True, region="arctic"),
    Site("Andoya_GS", 69.28, 16.02, is_user=False, is_gateway=True, region="subarctic"),
    Site("PokerFlat_GS", 65.12, -147.43, is_user=False, is_gateway=True, region="subarctic"),
    Site("Fucino_GS", 42.06, 13.55, is_user=False, is_gateway=True, region="midlat"),
    Site("Hartebeesthoek_GS", -25.89, 27.69, is_user=False, is_gateway=True, region="midlat"),
    Site("Guam_GS", 13.58, 144.85, is_user=False, is_gateway=True, region="equatorial"),
]

ALL_SITES: list[Site] = USER_SITES + GATEWAY_SITES


#: Latitude bins used for the per-bin handover-success curves (Fig. 6).
LAT_BINS = [
    ("0-15", 0.0, 15.0),
    ("15-30", 15.0, 30.0),
    ("30-45", 30.0, 45.0),
    ("45-55", 45.0, 55.0),
    ("55-65", 55.0, 65.0),
    ("65-70", 65.0, 70.0),
    ("70-75", 70.0, 75.0),
    ("75-82", 75.0, 90.0),
]


def sites_by_region(region: str) -> list[Site]:
    return [s for s in USER_SITES if s.region == region]


def user_sites() -> list[Site]:
    return list(USER_SITES)


def gateway_sites() -> list[Site]:
    return [s for s in ALL_SITES if s.is_gateway]
