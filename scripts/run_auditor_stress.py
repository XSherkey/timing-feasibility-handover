"""Auditor stress test (manuscript Sec. 4.6, Table 7).

Injects 100 candidate constraints across the five classes the paper specifies and
measures, per auditor stage, the detection rate, the false-acceptance rate and
the false-rejection rate.

Classes
-------
``invalid``       physically impossible (negative advance, elevation > 90 deg, ...)
``inconsistent``  contradicts the stated intent priority
``misleading``    statistically spurious predicate fitted on a tiny sample
``adversarial``   passes replay but violates the latency budget
``control``       valid rules that must be accepted (false-rejection probe)
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from almond.framework.auditor import Auditor, ImpactPredictor, physics_audit, semantic_audit_constraint
from almond.llm.surrogate import EFFECT_GRAMMAR, FIELD_SCHEMA, forensic_hypothesis

INTENT = {
    "priorities": {"reliability": "highest", "latency": "low", "power": "medium"},
    "requirements": ["uninterrupted Arctic video"],
}
SCOPE = dict(polar=True, regime="arctic", latitude_abs_deg=78.0)


def _valid_rules(rng, n):
    out = []
    # valid controls must be *consistent* with the declared (reliability-first)
    # intent, so power-capping effects are excluded from this class by design
    names = ("min_advance", "forbid_unrouted_target", "prefer_same_plane")
    for _ in range(n):
        name = names[int(rng.integers(0, len(names)))]
        eff = next(e for e in EFFECT_GRAMMAR if e["name"] == name)
        atoms = [
            {"field": "elevation_deg", "cmp": "<=", "value": float(rng.choice([10, 12, 15, 20]))},
            {"field": "handover_advance_s", "cmp": "<=", "value": float(rng.choice([6, 8, 10]))},
        ]
        if name == "forbid_unrouted_target":
            atoms = [{"field": "path_available", "cmp": "==", "value": 0}]
        elif name == "prefer_same_plane":
            atoms = [{"field": "plane_change", "cmp": "==", "value": 1}]
        elif name == "power_cap":
            atoms = [{"field": "battery_state", "cmp": "<=", "value": 0.6}]
        elif name == "buffer_drain":
            atoms = [{"field": "buffer_occupancy", "cmp": ">=", "value": 0.7}]
        mag = 0.0
        if name == "min_advance":
            mag = float(rng.choice(eff["params"]["seconds"]))
        elif name == "power_cap":
            mag = float(rng.choice(eff["params"]["max_lead_s"]))
        elif name == "buffer_drain":
            mag = float(rng.choice(eff["params"]["max_buffer"]))
        out.append(dict(cls="control", atoms=atoms, effect=name, magnitude=mag))
    return out


def _invalid_rules(rng, n):
    out = []
    for _ in range(n):
        kind = int(rng.integers(0, 4))
        if kind == 0:
            atoms = [{"field": "elevation_deg", "cmp": "<=", "value": float(rng.choice([-5.0, -20.0]))}]
            eff, mag = "min_advance", 12.0
        elif kind == 1:
            atoms = [{"field": "handover_advance_s", "cmp": "<=", "value": -8.0}]
            eff, mag = "min_advance", 12.0
        elif kind == 2:
            atoms = [{"field": "elevation_deg", "cmp": "<=", "value": 15.0}]
            eff, mag = "min_advance", -6.0
        else:
            atoms = [{"field": "elevation_deg", "cmp": "<=", "value": 120.0}]
            eff, mag = "prefer_same_plane", 0.0
        out.append(dict(cls="invalid", atoms=atoms, effect=eff, magnitude=mag))
    return out


def _inconsistent_rules(rng, n):
    out = []
    for _ in range(n):
        kind = int(rng.integers(0, 2))
        if kind == 0:
            atoms = [{"field": "battery_state", "cmp": "<=", "value": 0.6}]
            eff, mag = "power_cap", 6.0
        else:
            atoms = [{"field": "elevation_deg", "cmp": "<=", "value": 15.0}]
            eff, mag = "min_advance", 16.0
        out.append(dict(cls="inconsistent", atoms=atoms, effect=eff, magnitude=mag))
    return out


def _misleading_rules(rng, n, twin=None):
    """Predicates that look predictive on a tiny sample but are spurious."""
    out = []
    fields = ["buffer_occupancy", "snr_db", "doppler_rate_hz_s", "isl_hop_count", "satellite_apex"]
    for _ in range(n):
        f = fields[int(rng.integers(0, 4))]
        v = float(rng.uniform(1, 30))
        atoms = [{"field": f, "cmp": "<=" if rng.random() < 0.5 else ">=", "value": v}]
        out.append(dict(cls="misleading", atoms=atoms, effect="min_advance", magnitude=10.0))
    return out


def _adversarial_rules(rng, n):
    out = []
    for _ in range(n):
        atoms = [
            {"field": "elevation_deg", "cmp": "<=", "value": float(rng.choice([5.0, 6.0, 8.0]))},
            {"field": "isl_hop_count", "cmp": ">=", "value": float(rng.choice([6, 8, 10]))},
        ]
        out.append(dict(cls="adversarial", atoms=atoms, effect="min_advance", magnitude=14.0))
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-per-class", type=int, default=20)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--out", default="results/auditor_stress.json")
    args = ap.parse_args()

    rng = np.random.default_rng(args.seed)
    n = args.n_per_class
    cases = (
        _invalid_rules(rng, n)
        + _inconsistent_rules(rng, n)
        + _misleading_rules(rng, n)
        + _adversarial_rules(rng, n)
        + _valid_rules(rng, n)
    )
    auditor = Auditor(impact=None, require_impact=False)
    rows = []
    for c in cases:
        sem = semantic_audit_constraint(c["atoms"], c["effect"], INTENT)
        phy = physics_audit(c["atoms"], c["effect"], c["magnitude"], SCOPE)
        rows.append(
            dict(
                cls=c["cls"],
                effect=c["effect"],
                semantic_ok=sem.ok,
                physics_ok=phy.ok,
                accepted=sem.ok and phy.ok,
                reason=(sem.reason or phy.reason),
            )
        )

    summary = {}
    for cls in ("invalid", "inconsistent", "misleading", "adversarial", "control"):
        sel = [r for r in rows if r["cls"] == cls]
        if not sel:
            continue
        summary[cls] = dict(
            n=len(sel),
            semantic_detect=float(np.mean([not r["semantic_ok"] for r in sel])),
            physics_detect=float(np.mean([not r["physics_ok"] for r in sel])),
            false_acceptance=float(np.mean([r["accepted"] for r in sel])) if cls != "control" else None,
            false_rejection=float(np.mean([not r["accepted"] for r in sel])) if cls == "control" else None,
        )
    overall = dict(
        n=len(rows),
        false_acceptance=float(np.mean([r["accepted"] for r in rows if r["cls"] != "control"])),
        false_rejection=float(np.mean([not r["accepted"] for r in rows if r["cls"] == "control"])),
    )
    out = dict(summary=summary, overall=overall, rows=rows)
    p = Path(args.out)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"{'class':<14}{'n':>4}{'sem_det':>9}{'phy_det':>9}{'accept':>8}{'reject':>8}")
    for cls, s in summary.items():
        acc = "-" if s["false_acceptance"] is None else f"{s['false_acceptance'] * 100:.0f}%"
        rej = "-" if s["false_rejection"] is None else f"{s['false_rejection'] * 100:.0f}%"
        print(f"{cls:<14}{s['n']:4d}{s['semantic_detect'] * 100:8.0f}%{s['physics_detect'] * 100:8.0f}%{acc:>8}{rej:>8}")
    print(f"overall: false acceptance {overall['false_acceptance'] * 100:.1f}%, "
          f"false rejection {overall['false_rejection'] * 100:.1f}%  -> {p}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
