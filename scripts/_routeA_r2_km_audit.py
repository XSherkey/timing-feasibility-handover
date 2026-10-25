"""R2 / C4: audit the support of the Kaplan-Meier estimate.

The reviewer asks three things the paper did not show:

  D1  for every advance bucket, how many attempts, how many *exact* events and how
      many right-censored observations carry the estimate, and the KM value at the
      bucket edge;
  D2  which buckets actually carry the p50 / p90 / p95 quantiles quoted in the paper;
  D3  a stratified sensitivity analysis: naive median (successes only) versus KM
      median inside elevation bands, hop-count bands and plane-change strata.

Outputs results/routeA_r2/km_support_audit.json and .md.  Nothing in results/ is
modified; km_setup_time.py is imported, not edited.
"""
from __future__ import annotations

import argparse
import glob
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from km_setup_time import km, quantile  # noqa: E402

LAT_POLAR = 68.0
BUCKETS = [(6, 8), (8, 10), (10, 12), (12, 14), (14, 16), (16, 18), (18, 99)]


def load(root: str, arms: tuple[str, ...] | None = None) -> list[dict]:
    out = []
    for p in sorted(glob.glob(str(Path(root) / "*_seed*" / "run_summary.json"))):
        d = json.load(open(p, encoding="utf-8"))
        if not d.get("ok"):
            continue
        name = Path(p).parent.name.rsplit("_seed", 1)[0]
        if arms and name not in arms:
            continue
        out.extend(d["final"]["attempts"])
    return out


def observations(atts: list[dict]) -> tuple[np.ndarray, np.ndarray]:
    """(time, event) pairs: successes give the exact t_setup, late handovers are censored."""
    times, events = [], []
    for a in atts:
        adv = float(a["handover_advance_s"])
        if a["success"]:
            ts = a.get("t_setup_s")
            if ts is None or not np.isfinite(ts):
                continue
            times.append(float(ts))
            events.append(1)
        elif a.get("cause") == "late_handover":
            times.append(adv)
            events.append(0)
    return np.asarray(times), np.asarray(events)


def bucket_table(polar: list[dict]) -> list[dict]:
    t, e = observations(polar)
    grid, surv = km(t, e) if t.size else (np.array([]), np.array([]))
    rows = []
    for lo, hi in BUCKETS:
        sel = [a for a in polar if lo <= float(a["handover_advance_s"]) < hi]
        exact = sum(1 for a in sel if a["success"])
        cens = sum(1 for a in sel if a.get("cause") == "late_handover")
        other = len(sel) - exact - cens
        edge = float(hi) if hi < 99 else float("inf")
        s_edge = float(surv[grid <= edge][-1]) if grid.size and np.any(grid <= edge) else None
        rows.append(dict(bucket=f"[{lo},{hi})", attempts=len(sel), exact_events=exact,
                         right_censored=cens, competing_risk=other, km_at_edge=s_edge))
    return rows


def quantile_support(polar: list[dict]) -> dict:
    t, e = observations(polar)
    if not t.size:
        return {}
    grid, surv = km(t, e)
    out = {}
    for name, q in (("p50", 0.5), ("p90", 0.10), ("p95", 0.05)):
        val = quantile(grid, surv, q)
        lo = max(0, int(np.searchsorted(grid, val)) - 1)
        hi = min(len(grid) - 1, int(np.searchsorted(grid, val)))
        out[name] = dict(value=val, event_time=float(grid[hi]),
                         surrounding_grid=[float(grid[lo]), float(grid[hi])],
                         n_at_risk_at_value=int(np.sum(t >= val)) if np.isfinite(val) else 0)
    return out


def strata(polar: list[dict]) -> dict:
    defs = {
        "elevation": lambda a: "<25" if a["elevation_deg"] < 25 else ("25-40" if a["elevation_deg"] < 40 else ">40"),
        "isl_hops": lambda a: "0" if int(a.get("isl_hop_count", 0)) <= 0 else ("1" if int(a["isl_hop_count"]) == 1 else ">=2"),
        "plane_change": lambda a: "1" if int(a.get("plane_change", 0)) == 1 else "0",
        "buffer": lambda a: "<0.3" if float(a.get("buffer_occupancy", 0) or 0) < 0.3 else ">=0.3",
    }
    out = {}
    for dim, key in defs.items():
        groups: dict[str, list[dict]] = defaultdict(list)
        for a in polar:
            groups[key(a)].append(a)
        rows = {}
        for g, atts in sorted(groups.items()):
            succ = [float(a["t_setup_s"]) for a in atts
                    if a["success"] and a.get("t_setup_s") is not None and np.isfinite(a["t_setup_s"])]
            t, e = observations(atts)
            if t.size:
                g_grid, s = km(t, e)
                med_km = quantile(g_grid, s, 0.5)
            else:
                med_km = float("nan")
            rows[g] = dict(n=len(atts), successes=len(succ),
                           naive_median=float(np.median(succ)) if succ else float("nan"),
                           km_median=med_km,
                           bias=float(med_km - np.median(succ)) if succ and np.isfinite(med_km) else float("nan"))
        out[dim] = rows
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default="results/campaign_1023")
    ap.add_argument("--arms", default="almond,almond_fixedarch")
    ap.add_argument("--out", default="results/routeA_r2/km_support_audit.json")
    ap.add_argument("--md", default="results/routeA_r2/km_support_audit.md")
    args = ap.parse_args()

    arms = tuple(a.strip() for a in args.arms.split(",") if a.strip())
    atts = load(args.root, arms)
    polar = [a for a in atts if abs(float(a["latitude_abs_deg"])) >= LAT_POLAR]
    all_polar = [a for a in load(args.root) if abs(float(a["latitude_abs_deg"])) >= LAT_POLAR]

    payload = dict(lat_polar=LAT_POLAR, arms=list(arms), n_attempts_total=len(atts),
                   n_polar=len(polar), n_polar_all_arms=len(all_polar),
                   bucket_table=bucket_table(polar),
                   bucket_table_all_arms=bucket_table(all_polar),
                   quantiles=quantile_support(polar),
                   strata=strata(polar))
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    json.dump(payload, open(args.out, "w", encoding="utf-8"), indent=2)

    lines = ["# KM support audit (R2 / C4)", "",
             f"Polar = |lat| >= {LAT_POLAR}. Arms: {', '.join(arms)}. "
             f"{len(atts)} attempts, {len(polar)} polar.", "",
             "## Table D1 - support by advance bucket", "",
             "| bucket | attempts | exact events | right-censored | competing risk | KM S at edge |",
             "|---|---|---|---|---|---|"]
    for r in payload["bucket_table"]:
        s = "-" if r["km_at_edge"] is None else f"{r['km_at_edge']:.4f}"
        lines.append(f"| {r['bucket']} | {r['attempts']} | {r['exact_events']} | "
                     f"{r['right_censored']} | {r['competing_risk']} | {s} |")
    lines += ["", "## Quantile support", ""]
    for k, v in payload["quantiles"].items():
        lines.append(f"- {k} = {v['value']:.2f} s (event time {v['event_time']:.2f}; "
                     f"grid neighbours {v['surrounding_grid']}; at risk {v['n_at_risk_at_value']})")
    lines += ["", "## Stratified KM (naive vs censoring-aware median)", ""]
    for dim, rows in payload["strata"].items():
        lines += [f"**{dim}**", "", "| stratum | n | successes | naive median | KM median | bias |",
                  "|---|---|---|---|---|---|"]
        for g, r in rows.items():
            lines.append(f"| {g} | {r['n']} | {r['successes']} | {r['naive_median']:.2f} | "
                         f"{r['km_median']:.2f} | {r['bias']:+.2f} |")
        lines.append("")
    Path(args.md).write_text("\n".join(lines), encoding="utf-8")

    print(f"polar attempts {len(polar)} (all arms {len(all_polar)})")
    for r in payload["bucket_table"]:
        print(f"  {r['bucket']:>8}  attempts {r['attempts']:6d}  exact {r['exact_events']:5d}  "
              f"censored {r['right_censored']:5d}  competing {r['competing_risk']:4d}")
    for k, v in payload["quantiles"].items():
        print(f"  {k} = {v['value']:.2f} s")
    print("wrote", args.out, "and", args.md)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
