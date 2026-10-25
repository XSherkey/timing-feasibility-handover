"""T0 inventory: what already exists, with which physics and how many seeds."""
from __future__ import annotations

import glob
import json
import os
from collections import Counter, defaultdict


def scan(root: str) -> dict:
    runs = sorted(glob.glob(os.path.join(root, "*_seed*", "run_summary.json")))
    methods = Counter()
    seeds = defaultdict(list)
    cfgs = Counter()
    ok = 0
    for p in runs:
        d = json.load(open(p, encoding="utf-8"))
        m = d.get("method") or os.path.basename(os.path.dirname(p)).rsplit("_seed", 1)[0]
        s = int(os.path.basename(os.path.dirname(p)).rsplit("_seed", 1)[1])
        methods[m] += 1
        seeds[m].append(s)
        ok += bool(d.get("ok"))
        c = d.get("config") or {}
        cfgs[(c.get("twin_tag"), c.get("twin_hours"), c.get("feeder_slots"),
              c.get("isl_seam_enabled"), c.get("acq_signaling_s"),
              c.get("probe_calibrated"), c.get("late_risk_weight"))] += 1
    return dict(root=root, n=len(runs), ok=ok, methods=dict(methods),
                seeds={k: sorted(v) for k, v in seeds.items()},
                configs={str(k): v for k, v in cfgs.items()})


def multi(root: str) -> dict:
    out = {}
    for d in sorted(glob.glob(os.path.join(root, "multi_*"))):
        intents = sorted(os.path.basename(x) for x in glob.glob(os.path.join(d, "intent*")))
        out[os.path.basename(d)] = dict(
            intents=len(intents),
            summary=os.path.exists(os.path.join(d, "summary.json")),
            kg=os.path.exists(os.path.join(d, "knowledge_graph.json")),
        )
    return out


print("== campaign-style runs ==")
for root in ("results/campaign_1023", "results/campaign_pcs3_ref", "results/campaign_pcs3_sig32",
             "results/campaign_penalty", "results/campaign_clean", "results/campaign_sig32",
             "results/campaign_regime_ref4", "results/campaign_regime_noseam",
             "results/campaign_regime_tight3", "results/campaign_oracle_fixed",
             "results/campaign_ablate"):
    r = scan(root)
    print(f"\n{r['root']}: {r['n']} runs, {r['ok']} ok")
    print("  methods:", r["methods"])
    print("  seeds  :", r["seeds"])
    for k, v in r["configs"].items():
        print(f"  cfg {k}: {v} runs")

print("\n== multi-intent ==")
for name, d in multi("results").items():
    print(f"  {name}: intents={d['intents']} summary={d['summary']} kg={d['kg']}")
