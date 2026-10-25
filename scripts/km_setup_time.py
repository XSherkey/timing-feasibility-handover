"""Kaplan-Meier estimate of the link-setup time T_setup from censored attempts.

Why this matters
----------------
``t_setup_s`` is only recorded when a link is actually established.  An attempt
that fails *because the advance was too short* tells us ``T_setup > a`` and
nothing more: it is **right-censored**.  Pooling only the successful attempts
therefore truncates the distribution and hides the polar penalty — which is
exactly the signal a reward-driven learner would also miss.

Estimator
---------
For each regime ``z`` we fit a Kaplan-Meier survival curve ``S_z(t)`` with
``t_i = t_setup`` (event) or ``t_i = advance_i`` (censored, cause =
late_handover), and report the median and the 90th percentile:
the required advance is ``q_eps = S^{-1}(eps)``.

Usage
-----
    python scripts/km_setup_time.py --root results/campaign_1023
    python scripts/km_setup_time.py --root results/campaign_1023 --json out.json
"""
from __future__ import annotations

import argparse
import glob
import json
import os
from collections import defaultdict

import numpy as np


def load_attempts(root: str) -> list[dict]:
    out: list[dict] = []
    for p in sorted(glob.glob(os.path.join(root, "*_seed*", "run_summary.json"))):
        d = json.load(open(p, encoding="utf-8"))
        if d.get("ok"):
            out.extend(d["final"]["attempts"])
    return out


def km(times: np.ndarray, events: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Kaplan-Meier survival curve.  Returns (time grid, S(t)) with S at unique times."""
    order = np.argsort(times)
    t = times[order]
    e = events[order]
    uniq = np.unique(t)
    surv = []
    s = 1.0
    for u in uniq:
        at_risk = np.sum(t >= u)
        d = np.sum((t == u) & e)
        if at_risk > 0 and d > 0:
            s *= 1.0 - d / at_risk
        surv.append(s)
    return uniq, np.asarray(surv)


def quantile(t: np.ndarray, s: np.ndarray, q: float) -> float:
    """Smallest time whose survival is <= q (i.e. the q-quantile of T)."""
    idx = np.where(s <= q)[0]
    return float(t[idx[0]]) if idx.size else float("nan")


def region_of(att: dict) -> str:
    lat = abs(att["latitude_abs_deg"])
    if lat >= 70.0:
        return "polar"
    if lat >= 55.0:
        return "mid"
    if lat < 15.0:
        return "equat"
    return "mild"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default="results/campaign_1023")
    ap.add_argument("--json", default=None)
    args = ap.parse_args()

    attempts = load_attempts(args.root)
    print(f"{len(attempts)} attempts from {args.root}\n")

    groups: dict[str, list[dict]] = defaultdict(list)
    for att in attempts:
        groups[region_of(att)].append(att)
        groups[f"{region_of(att)}/el<15"].append(att) if att["elevation_deg"] < 15 else None
        if int(att.get("plane_change", 0)) == 1:
            groups[f"{region_of(att)}/planechg"].append(att)

    out = {}
    print(f"{'regime':<20}{'n':>8}{'events':>8}{'censored':>10}"
          f"{'median':>9}{'p75':>8}{'p90':>8}{'p95':>8}")
    print("-" * 78)
    for name in ("polar", "polar/el<15", "polar/planechg", "mid", "mid/el<15", "equat"):
        atts = groups.get(name) or []
        times, events = [], []
        for att in atts:
            a = float(att["handover_advance_s"])
            if att["success"]:
                ts = att.get("t_setup_s")
                if ts is None or not np.isfinite(ts):
                    continue
                times.append(float(ts))
                events.append(1)
            elif att["cause"] == "late_handover":
                times.append(a)
                events.append(0)
            # other failure modes are competing risks; excluded here
        if not times:
            continue
        times = np.asarray(times)
        events = np.asarray(events)
        t, s = km(times, events)
        rec = dict(n=int(times.size), events=int(events.sum()),
                   censored=int((1 - events).sum()),
                   median=quantile(t, s, 0.5), p75=quantile(t, s, 0.25),
                   p90=quantile(t, s, 0.10), p95=quantile(t, s, 0.05))
        out[name] = rec
        print(f"{name:<20}{rec['n']:>8d}{rec['events']:>8d}{rec['censored']:>10d}"
              f"{rec['median']:>9.2f}{rec['p75']:>8.2f}{rec['p90']:>8.2f}{rec['p95']:>8.2f}")

    if args.json:
        json.dump(out, open(args.json, "w", encoding="utf-8"), indent=2)
        print(f"\nwrote {args.json}")

    print("\nReading: a large censored fraction means the *successful* attempts are a")
    print("biased sample of the link-setup time; the naive mean over successes")
    print("under-states T_setup by the amount shown in `median - naive_p50`.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
