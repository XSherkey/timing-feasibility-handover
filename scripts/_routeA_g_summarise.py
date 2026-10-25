"""Merge Phase G numbers into results/routeA/summary.json (adds a G1-G5 block)."""
from __future__ import annotations

import glob
import json
import os
import statistics as st
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SUM = ROOT / "results" / "routeA" / "summary.json"


def hsr_s(pattern: str) -> tuple[list[float], list[float]]:
    hs, ss = [], []
    for p in glob.glob(pattern):
        d = json.load(open(p, encoding="utf-8"))
        if d.get("ok"):
            hs.append(100 * d["final"]["arctic"]["hsr"])
            ss.append(d["final"]["satisfaction"])
    return hs, ss


def main() -> None:
    summary = json.load(open(SUM, encoding="utf-8")) if SUM.exists() else {}

    # G1
    g1p = ROOT / "results" / "routeA" / "g1_gate_power.json"
    if g1p.exists():
        summary["G1"] = json.load(open(g1p, encoding="utf-8"))

    # G2: lambda asymptote + HSR/S frontier
    rows = []
    for lam, pat in (("0", "results/campaign_clean/no_forensics_seed*/run_summary.json"),
                     ("0.3", "results/routeA_f3/lam0.3/no_forensics_seed*/run_summary.json"),
                     ("0.5", "results/routeA_f3/lam0.5/no_forensics_seed*/run_summary.json"),
                     ("1.0", "results/campaign_penalty/no_forensics_seed*/run_summary.json"),
                     ("2.0", "results/routeA_f3/lam2.0/no_forensics_seed*/run_summary.json"),
                     ("8.0", "results/routeA_f3/lam8.0/no_forensics_seed*/run_summary.json"),
                     ("16", "results/routeA_g2/lam16/no_forensics_seed*/run_summary.json"),
                     ("32", "results/routeA_g2/lam32/no_forensics_seed*/run_summary.json"),
                     ("64", "results/routeA_g2/lam64/no_forensics_seed*/run_summary.json")):
        hs, ss = hsr_s(pat)
        if hs:
            rows.append(dict(lam=lam, n=len(hs), hsr=round(st.mean(hs), 1),
                             sd=round(st.stdev(hs), 1) if len(hs) > 1 else 0.0,
                             S=round(st.mean(ss), 1)))
    # shield reference points
    hs, ss = hsr_s("results/campaign_1023/almond_seed*/run_summary.json")
    shield = dict(lam="shield", n=len(hs), hsr=round(st.mean(hs), 1),
                  sd=round(st.stdev(hs), 1), S=round(st.mean(ss), 1))
    summary["G2"] = dict(frontier=rows, shield=shield)

    # G2b
    p = ROOT / "results" / "routeA" / "g2b_penalty_drift.json"
    if p.exists():
        d = json.load(open(p, encoding="utf-8"))
        summary["G2b"] = dict(n=len(d),
                              nominal=round(st.mean(r["nominal"] for r in d), 1),
                              sig32=round(st.mean(r["sig32"] for r in d), 1),
                              drop=round(st.mean(r["sig32"] - r["nominal"] for r in d), 1))

    # G3
    p = ROOT / "results" / "routeA" / "g3_drift_table.json"
    if p.exists():
        d = json.load(open(p, encoding="utf-8"))
        by = {}
        for acq in sorted({r["acq"] for r in d}):
            sel = [r for r in d if r["acq"] == acq]
            by[str(acq)] = dict(n=len(sel),
                                fixed18=round(st.mean(r["fixed18"] for r in sel), 1),
                                calib=round(st.mean(r["calib"] for r in sel), 1),
                                taus=[r["tau_star"] for r in sel])
        summary["G3"] = by

    # G4
    g4 = {}
    for tag, pat in (("pcs8_sig32", "results/routeA_g4/pcs8_sig32/almond_seed*/run_summary.json"),
                     ("pcs8_ref", "results/routeA_g4/pcs8_ref/almond_seed*/run_summary.json"),
                     ("pcs3_sig32", "results/campaign_pcs3_sig32/almond_seed*/run_summary.json"),
                     ("pcs3_ref", "results/campaign_pcs3_ref/almond_seed*/run_summary.json")):
        hs, ss = hsr_s(pat)
        taus = []
        for p in glob.glob(pat):
            d = json.load(open(p, encoding="utf-8"))
            for e in (d.get("events") or []):
                if e.get("event") == "probe_tau":
                    taus.append(e.get("tau"))
        if hs:
            g4[tag] = dict(n=len(hs), arctic=round(st.mean(hs), 1),
                           sd=round(st.stdev(hs), 1) if len(hs) > 1 else 0.0,
                           S=round(st.mean(ss), 1), taus=taus)
    p = ROOT / "results" / "routeA" / "g4b_plateau_cost.json"
    if p.exists():
        d = json.load(open(p, encoding="utf-8"))
        g4["plateau"] = {tag: {str(o): round(st.mean(r[f"{tag}_tau{o}"] for r in d), 1)
                               for o in off}
                         for tag, off in (("ref", (14, 16, 18)), ("sig32", (16, 18, 20)))}
    summary["G4"] = g4

    # G5: probe cost
    probe_files = sorted(glob.glob(str(ROOT / "results" / "routeA_f4" / "probe_*.json")))
    eps = attempts = 0
    for p in probe_files:
        d = json.load(open(p, encoding="utf-8"))
        eps += len(d["rows"]) * d["episodes_per_advance"]
        attempts += sum(r["n"] for r in d["rows"])
    summary["G5"] = dict(probe_files=len(probe_files), episodes_2=eps, attempts=attempts,
                         steps_2=eps * 240, ratio_2=round(100 * eps * 240 / (9600 * 240), 2),
                         episodes_8=eps * 4, ratio_8=round(100 * eps * 4 * 240 / (9600 * 240), 2))

    SUM.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print("sections:", list(summary))
    print(json.dumps({k: summary[k] for k in ("G2b", "G5")}, ensure_ascii=False, indent=2))
    print("G2 frontier:", json.dumps(summary.get("G2", {}).get("frontier"), ensure_ascii=False))
    print("G2 shield:", summary.get("G2", {}).get("shield"))
    print("G4:", json.dumps(summary.get("G4", {}), ensure_ascii=False))


if __name__ == "__main__":
    main()
