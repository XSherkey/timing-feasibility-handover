"""Merge Phase H numbers into results/routeA/summary.json."""
from __future__ import annotations

import json
import statistics as st
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SUM = ROOT / "results" / "routeA" / "summary.json"


def main() -> None:
    s = json.load(open(SUM, encoding="utf-8"))

    h1 = json.load(open(ROOT / "results" / "routeA" / "h1_advance_dist.json", encoding="utf-8"))
    out = {}
    for arm in ("penalty_lam8", "no_knowledge"):
        sel = [r for r in h1 if r["arm"] == arm]
        out[arm] = dict(
            n=len(sel),
            mean_adv_ref=round(st.mean(r["ref"]["mean"] for r in sel), 2),
            sd_adv_ref=round(st.mean(r["ref"]["sd"] for r in sel), 2),
            share_below16=round(st.mean(r["ref"]["share_below16"] for r in sel), 3),
            hsr_ref=round(st.mean(r["ref"]["arctic"] for r in sel), 1),
            hsr_sig32=round(st.mean(r["sig32"]["arctic"] for r in sel), 1),
        )
    paired = [r["sig32"]["arctic"] - q["sig32"]["arctic"]
              for r, q in zip([x for x in h1 if x["arm"] == "penalty_lam8"],
                              [x for x in h1 if x["arm"] == "no_knowledge"])]
    out["paired_sig32_diff"] = dict(mean=round(st.mean(paired), 1),
                                    sd=round(st.stdev(paired), 1) if len(paired) > 1 else 0.0)
    s["H1"] = out

    h2 = json.load(open(ROOT / "results" / "routeA" / "h2_margin.json", encoding="utf-8"))
    s["H2"] = {phys: {f"m{m}": dict(mean=round(st.mean(r[f"m{m}"] for r in h2 if r["physics"] == phys), 1),
                                    min=round(min(r[f"m{m}"] for r in h2 if r["physics"] == phys), 1))
                      for m in (0, 2, 4)}
               for phys in ("ref", "sig32", "drift44")}
    s["H2"]["tau_probed"] = {phys: [r["tau_probed"] for r in h2 if r["physics"] == phys]
                             for phys in ("ref", "sig32", "drift44")}

    g3 = json.load(open(ROOT / "results" / "routeA" / "g3_drift_table_5seed.json", encoding="utf-8"))
    s["H3"] = {str(round(acq - 1.2, 1)): dict(
        n=len([r for r in g3 if r["acq"] == acq]),
        fixed18=round(st.mean(r["fixed18"] for r in g3 if r["acq"] == acq), 1),
        fixed18_sd=round(st.stdev(r["fixed18"] for r in g3 if r["acq"] == acq), 1),
        calib=round(st.mean(r["calib"] for r in g3 if r["acq"] == acq), 1),
        calib_sd=round(st.stdev(r["calib"] for r in g3 if r["acq"] == acq), 1),
    ) for acq in sorted({r["acq"] for r in g3})}

    SUM.write_text(json.dumps(s, indent=2, ensure_ascii=False), encoding="utf-8")
    print("sections:", list(s))
    print(json.dumps({k: s[k] for k in ("H1", "H2", "H3")}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
