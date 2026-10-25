"""Paired comparison of ALMOND against its own ablations, and knowledge-graph activity.

ALMOND and ``ALMOND w/o forensics`` share the same seed, the same discovered
architecture and (through the response cache) the same audited weight profile, so
a per-seed difference isolates the effect of the reverse-forensic loop and its
committed constraints.
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]


def load(d: Path) -> dict[tuple[str, int], dict]:
    out = {}
    if not d.exists():
        return out
    for p in d.glob("*/run_summary.json"):
        try:
            r = json.loads(p.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        if r.get("ok"):
            out[(r["method"], r["seed"])] = r
    return out


def arctic(r: dict) -> float:
    return r["final"]["arctic"]["hsr"] * 100.0


def main() -> int:
    which = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "results" / "campaign"
    runs = load(which)
    print(f"campaign: {which}  ({len(runs)} runs)")
    seeds = sorted({s for (_, s) in runs})
    print("\npaired ALMOND vs ALMOND-without-forensics (same seed, arch and weights):")
    print(f"{'seed':>5}{'ALMOND':>9}{'no-fore':>9}{'delta':>9}{'kg':>5}{'commits':>9}")
    deltas = []
    for s in seeds:
        a, b = runs.get(("almond", s)), runs.get(("no_forensics", s))
        if not (a and b):
            continue
        da, db = arctic(a), arctic(b)
        kg = a.get("kg", {}).get("n_active", 0)
        cm = sum(1 for f in (a.get("forensics") or []) if f.get("accepted"))
        deltas.append(da - db)
        print(f"{s:5d}{da:8.1f}%{db:8.1f}%{da - db:+9.1f}{kg:5d}{cm:9d}")
    if deltas:
        print(f"mean paired delta {np.mean(deltas):+.1f} pp "
              f"(median {np.median(deltas):+.1f}, n={len(deltas)})")

    print("\nknowledge-graph activity (mean per run):")
    by = defaultdict(list)
    for (m, _s), r in runs.items():
        by[m].append(r)
    for m in ("almond", "no_forensics", "eureka", "oracle", "static_llm",
              "unseeded_evonas", "almond_fixedarch", "ppomlp"):
        rs = by.get(m)
        if not rs:
            continue
        kg = np.mean([r.get("kg", {}).get("n_active", 0) for r in rs])
        cm = np.mean([sum(1 for f in (r.get("forensics") or []) if f.get("accepted")) for r in rs])
        triggers = np.mean([len(r.get("forensics") or []) for r in rs])
        print(f"  {m:<18} n={len(rs):2d}  forensic_rounds={triggers:.2f}  "
              f"commits={cm:.2f}  kg_active={kg:.2f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
