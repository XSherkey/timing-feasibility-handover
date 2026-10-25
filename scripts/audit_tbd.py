"""Audit the TBD value map: how many entries, how many are n/a, spot-check key ones."""
from __future__ import annotations

import json
from pathlib import Path

p = Path(__file__).resolve().parents[1] / "docs" / "tbd_values.json"
d = json.loads(p.read_text(encoding="utf-8"))
print("total entries:", len(d))
na = [k for k, v in d.items() if v["value"] in ("n/a", "", None)]
print("n/a entries:", len(na), na[:8])
for k in (
    "hsr.almond.arctic",
    "hsr.ppomlp.arctic",
    "hsr.almond_fixedarch.arctic",
    "oracle_arctic_hsr",
    "latency.ort_cpu_fp32",
    "latency.ort_cpu_int8",
    "policy_switch",
    "audit.false_rejection",
    "audit.false_acceptance",
    "llm_stability.forward_translate",
    "impact_mae",
    "twin_link_budget",
    "twin_rule_replication",
    "sens.delta.0.10",
    "sens.theta.0.85",
    "wall.almond",
    "nas.llm_evals",
    "params.almond",
    "satisfaction.almond",
):
    if k in d:
        print(f"  {k:<34} {d[k]['value']}")
