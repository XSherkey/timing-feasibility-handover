"""R5: rebuild the support audit separately for passive (no-shield) and rule-applied logs.

The v6 Table D1 mixed the two: it was computed from `final.attempts` of the *deployed*
arms, which apply the mined 16 s rule at evaluation, so 91% of their attempts sit at
16 s.  That cannot support a claim about what the *passive* log covers.  This script
splits the two regimes and writes results/routeA_r2/km_support_split.json.
"""
from __future__ import annotations

import glob
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from km_setup_time import km, quantile  # noqa: E402

LAT = 68.0
BUCKETS = [(6, 8), (8, 10), (10, 12), (12, 14), (14, 16), (16, 18), (18, 99)]
GROUPS = {
    "passive_ppomlp": ("ppomlp",),
    "passive_nomining": ("no_forensics",),
    "rule_applied_almond": ("almond", "almond_fixedarch"),
}


def load(group: str) -> list[dict]:
    out = []
    for p in sorted(glob.glob(str(ROOT / "results" / "campaign_1023" / "*_seed*" / "run_summary.json"))):
        d = json.load(open(p, encoding="utf-8"))
        if not d.get("ok"):
            continue
        arm = Path(p).parent.name.rsplit("_seed", 1)[0]
        if arm not in GROUPS[group]:
            continue
        for a in d["final"]["attempts"]:
            if abs(float(a["latitude_abs_deg"])) >= LAT:
                out.append(a)
    return out


def table(atts: list[dict]) -> dict:
    rows = []
    tot = 0
    for lo, hi in BUCKETS:
        sel = [a for a in atts if lo <= float(a["handover_advance_s"]) < hi]
        exact = sum(1 for a in sel if a["success"])
        cens = sum(1 for a in sel if a.get("cause") == "late_handover")
        other = len(sel) - exact - cens
        rows.append(dict(bucket="[%d,%d)" % (lo, hi if hi < 99 else 99), attempts=len(sel),
                         exact=exact, censored=cens, competing=other))
        tot += len(sel)
    adv = np.array([float(a["handover_advance_s"]) for a in atts]) if atts else np.array([])
    times, events = [], []
    for a in atts:
        if a["success"]:
            ts = a.get("t_setup_s")
            if ts is not None and np.isfinite(ts):
                times.append(float(ts)); events.append(1)
        elif a.get("cause") == "late_handover":
            times.append(float(a["handover_advance_s"])); events.append(0)
    q = {}
    if times:
        g, s = km(np.asarray(times), np.asarray(events))
        q = dict(p50=quantile(g, s, 0.5), p90=quantile(g, s, 0.10), p95=quantile(g, s, 0.05))
    return dict(rows=rows, total=tot,
                mean_advance=float(adv.mean()) if adv.size else None,
                median_advance=float(np.median(adv)) if adv.size else None,
                share_ge16=float(np.mean(adv >= 16)) if adv.size else None,
                quantiles=q)


def main() -> int:
    out = {}
    for g in GROUPS:
        atts = load(g)
        out[g] = table(atts)
        r = out[g]
        print("==", g, "| attempts", r["total"], "| mean adv %.2f | median %.2f | share>=16 %.3f"
              % (r["mean_advance"], r["median_advance"], r["share_ge16"]))
        for row in r["rows"]:
            print("   %-8s %6d  exact %5d  cens %5d  comp %4d  (%+.1f%%)"
                  % (row["bucket"], row["attempts"], row["exact"], row["censored"],
                     row["competing"], 100.0 * row["attempts"] / max(r["total"], 1)))
        print("   quantiles:", {k: round(v, 2) for k, v in r["quantiles"].items()})
    (ROOT / "results" / "routeA_r2" / "km_support_split.json").write_text(
        json.dumps(out, indent=2), encoding="utf-8")
    print("wrote results/routeA_r2/km_support_split.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
