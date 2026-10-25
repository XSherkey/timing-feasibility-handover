"""Aggregate the route-A results into results/routeA/summary.json + a readable table."""
from __future__ import annotations

import glob
import json
import statistics as st
from pathlib import Path

import numpy as np
from scipy import stats

ROOT = Path(__file__).resolve().parents[1]


def arctic_of(p: Path) -> float:
    d = json.load(open(p, encoding="utf-8"))
    return 100 * d["final"]["arctic"]["hsr"]


def multi_rows(root: Path) -> dict[int, list[float]]:
    """seed -> [intent0..3 arctic]"""
    out = {}
    for p in sorted(glob.glob(str(root / "summary.json"))):
        d = json.load(open(p, encoding="utf-8"))
        seed = int(root.name.rsplit("_s", 1)[1])
        out[seed] = [100 * (r["arctic"] or 0) for r in d]
    return out


def wilcoxon(a, b) -> tuple[float, float]:
    if len(a) != len(b) or len(a) < 3:
        return float("nan"), float("nan")
    try:
        r = stats.wilcoxon(a, b)
        return float(r.statistic), float(r.pvalue)
    except ValueError:
        return float("nan"), float("nan")


summary = {}

# ---------------------------------------------------------------- F1
f1p = ROOT / "results" / "routeA" / "f1_table.json"
f1b = ROOT / "results" / "routeA" / "f1b_drift_table.json"
if f1p.exists():
    t = json.load(open(f1p, encoding="utf-8"))
    f1 = {}
    for k in "ABCDEF":
        v = [r["arctic"] for r in t.get(k, [])]
        if v:
            f1[k] = dict(n=len(v), mean=round(st.mean(v), 1),
                         sd=round(st.stdev(v), 1) if len(v) > 1 else 0.0)
    if f1b.exists():
        f1["drift_sweep"] = json.load(open(f1b, encoding="utf-8"))
    summary["F1"] = f1

# ---------------------------------------------------------------- F2
f2 = {}
for name, pattern in (("gate", "routeA_f2/g_shared_gate_s*"),
                      ("nogate", "routeA_f2/h_shared_nogate_s*"),
                      ("noinject", "multi_shared_s*")):
    rows = {}
    for d in sorted(glob.glob(str(ROOT / "results" / pattern))):
        p = Path(d)
        if not (p / "summary.json").exists():
            continue
        seed = int(p.name.rsplit("_s", 1)[1])
        rows[seed] = [100 * (r["arctic"] or 0) for r in json.load(open(p / "summary.json", encoding="utf-8"))]
    f2[name] = rows

intents = {}
for arm, rows in f2.items():
    if rows:
        n = len(rows)
        intents[arm] = [round(st.mean([r[i] for r in rows.values()]), 1) for i in range(4)]
        intents[arm + "_n"] = n
common = sorted(set(f2.get("gate", {})) & set(f2.get("nogate", {})) &
                set(f2.get("noinject", {})))
pair = {}
if common:
    g = [st.mean(f2["gate"][s][1:]) for s in common]
    h = [st.mean(f2["nogate"][s][1:]) for s in common]
    ni = [st.mean(f2["noinject"][s][1:]) for s in common]
    pair = dict(seeds=common,
                gate=round(st.mean(g), 1), nogate=round(st.mean(h), 1), noinject=round(st.mean(ni), 1),
                diff_gate_minus_nogate=round(st.mean(np.array(g) - np.array(h)), 1),
                diff_gate_minus_noinject=round(st.mean(np.array(g) - np.array(ni)), 1),
                p_gate_vs_nogate=round(wilcoxon(g, h)[1], 4))
summary["F2"] = dict(intents=intents, paired=pair)

# ---------------------------------------------------------------- F3
f3 = {}
for lam in ("lam0.3", "lam0.5", "lam2.0", "lam8.0"):
    vals = []
    for p in glob.glob(str(ROOT / "results" / "routeA_f3" / lam / "no_forensics_seed*" / "run_summary.json")):
        d = json.load(open(p, encoding="utf-8"))
        if d.get("ok"):
            vals.append(100 * d["final"]["arctic"]["hsr"])
    if vals:
        f3[lam] = dict(n=len(vals), mean=round(st.mean(vals), 1), sd=round(st.stdev(vals), 1),
                       min=round(min(vals), 1), max=round(max(vals), 1))
# reference points
base = [arctic_of(Path(p)) for p in glob.glob(str(ROOT / "results" / "campaign_clean" / "no_forensics_seed*" / "run_summary.json"))]
pen1 = [arctic_of(Path(p)) for p in glob.glob(str(ROOT / "results" / "campaign_penalty" / "no_forensics_seed*" / "run_summary.json"))]
f3["lambda=0 (no knowledge)"] = dict(n=len(base), mean=round(st.mean(base), 1), sd=round(st.stdev(base), 1))
f3["lambda=1.0 (existing)"] = dict(n=len(pen1), mean=round(st.mean(pen1), 1), sd=round(st.stdev(pen1), 1))
shield = [arctic_of(Path(p)) for p in glob.glob(str(ROOT / "results" / "campaign_1023" / "almond_seed*" / "run_summary.json"))]
f3["decision shield (reference)"] = dict(n=len(shield), mean=round(st.mean(shield), 1), sd=round(st.stdev(shield), 1))
summary["F3"] = f3

# ---------------------------------------------------------------- F4
f4p = ROOT / "results" / "routeA" / "f4_probe_convergence.json"
f4 = {}
if f4p.exists():
    f4["convergence"] = json.load(open(f4p, encoding="utf-8"))["rows"]
    f4["min_episodes"] = json.load(open(f4p, encoding="utf-8"))["min_episodes"]
for tag, path in (("probe_ref_s0", ROOT / "results" / "routeA_f4" / "probe_ref_s0.json"),
                  ("probe_sig32_s0", ROOT / "results" / "routeA_f4" / "probe_sig32_s0.json")):
    if path.exists():
        d = json.load(open(path, encoding="utf-8"))
        f4[tag] = dict(tau=d["tau_star"], ci=d["tau_ci"], episodes=d["episodes_per_advance"])
summary["F4"] = f4

# ---------------------------------------------------------------- F5
f5p = ROOT / "results" / "routeA" / "f5_table.json"
if f5p.exists():
    summary["F5"] = json.load(open(f5p, encoding="utf-8"))

(ROOT / "results" / "routeA" / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
print(json.dumps(summary, indent=2, ensure_ascii=False))
