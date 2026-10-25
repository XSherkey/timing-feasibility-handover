"""Build (or refresh) the digital-twin cache.

Usage:
    python scripts/build_twin.py --tag ref --hours 12 --dt 10
    python scripts/build_twin.py --tag eclipse --hours 12 --rain 1.0
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from almond.twin.twin import DigitalTwin, TwinConfig


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", default="ref")
    ap.add_argument("--constellation", default="ref350")
    ap.add_argument("--hours", type=float, default=12.0)
    ap.add_argument("--dt", type=float, default=10.0)
    ap.add_argument("--epoch-doy", type=float, default=292.25)
    ap.add_argument("--rain", type=float, default=1.0, help="atmospheric attenuation scale")
    ap.add_argument("--isl-max-range", type=float, default=5200.0)
    ap.add_argument("--isl-max-degree", type=int, default=4)
    ap.add_argument("--isl-seam-lat", type=float, default=70.0)
    ap.add_argument("--no-seam", action="store_true")
    ap.add_argument("--isl-dropout", type=float, default=0.0)
    ap.add_argument("--feeder-slots", type=int, default=4)
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    cfg = TwinConfig(
        constellation=args.constellation,
        horizon_s=args.hours * 3600.0,
        dt_s=args.dt,
        epoch_doy=args.epoch_doy,
        rain_scale=args.rain,
        isl_max_range_km=args.isl_max_range,
        isl_seam_lat_deg=args.isl_seam_lat,
        isl_seam_enabled=not args.no_seam,
        isl_dropout=args.isl_dropout,
        feeder_slots=args.feeder_slots,
        tag=args.tag,
    )
    t0 = time.time()
    twin = DigitalTwin(cfg).build(force=args.force)
    print(f"[build] {time.time() - t0:.1f}s  -> {twin.cache_dir}")
    meta = json.loads((twin.cache_dir / "meta.json").read_text())
    print("\n== coverage ==")
    for name, c in meta["coverage"].items():
        if name.startswith("_"):
            print(f"{name}: {c}")
            continue
        print(
            f"{name:<14} lat={c['lat']:6.2f}  mean_visible={c['mean_visible']:5.1f} "
            f"coverage={c['coverage_frac'] * 100:5.1f}%"
        )
    hop = twin["hop"]
    print(f"\nhop: mean {hop[hop >= 0].mean():.2f}  max {hop.max()}  unreachable {(hop < 0).mean() * 100:.1f}%")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
