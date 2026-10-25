"""Build experiments/manifest_r3.json — the single source of truth for the R3 suite.

Records the twin identity, the time windows, the traffic multipliers, the policy-seed
list, the physics-drift settings and the metric definitions.  Every other script reads
this file; none of them may hard-code a seed or an episode id.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TLE_DIR = ROOT / "data" / "tle"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()[:16]


def git_head() -> str | None:
    try:
        r = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True)
        return r.stdout.strip() or None
    except Exception:
        return None


def main() -> int:
    from almond.framework.forensics import SplitConfig
    from almond.twin.twin import TwinConfig

    cfg = TwinConfig()
    splits = SplitConfig()
    tles = sorted(TLE_DIR.glob("*.tle")) + sorted(TLE_DIR.glob("*.txt"))
    manifest = {
        "manifest_version": "r3-1",
        "twin": {
            "fingerprint": cfg.fingerprint(),
            "epoch_year": cfg.epoch_year,
            "epoch_doy": cfg.epoch_doy,
            "horizon_h": 12.0,
            "dt_s": 10.0,
            "n_sats": 350,
            "constellation": getattr(cfg, "constellation", "walker"),
            "feeder_slots": getattr(cfg, "feeder_slots", 4),
            "isl_seam_enabled": getattr(cfg, "isl_seam_enabled", True),
            "isl_dropout": getattr(cfg, "isl_dropout", 0.0),
            "git_head": git_head(),
        },
        "tle": {
            "dir": str(TLE_DIR.relative_to(ROOT)) if TLE_DIR.exists() else None,
            "files": [dict(name=p.name, sha256=sha256(p)) for p in tles],
            "note": "Walker-generated constellation; no real TLE is used (Limitation)",
        },
        "windows": {
            "train": list(splits.train),
            "validation": list(splits.validation),
            "lockbox": list(splits.test),
        },
        "traffic_eval": list(splits.test_traffic),
        "policy_seeds": list(range(10)),
        "selection_seeds": [0, 1, 2],
        "lockbox_epochs": [299.25, 306.25, 290.25],
        "physics_drift_acq_signaling": [1.2, 3.2, 4.4, 5.6],
        "physics_nominal_acq_signaling": 1.2,
        "margin_s": [0.0, 2.0, 4.0],
        "metrics": {
            "HSR": "attempt-weighted share of successful handovers in a latitude band",
            "polar_band_deg": 70.0,
            "support_band_deg": 68.0,
            "late_share": "share of attempts whose cause is late_handover",
            "S": "satisfaction = weighted combination of reliability, latency and power (almond.analysis.metrics.satisfaction)",
        },
        "costs": {
            "probe_env_steps": 10500,
            "eval_env_steps_per_run": 240 * 32 * 3,
        },
    }
    out = ROOT / "experiments" / "manifest_r3.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print("wrote", out)
    print(json.dumps({k: manifest[k] for k in ("windows", "policy_seeds", "lockbox_epochs")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
