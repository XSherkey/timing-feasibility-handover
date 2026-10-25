"""Write the per-task tables the plan asks for (f2_table.json, f3_table.json)."""
import glob
import json
import os
import statistics as st


def f2() -> None:
    out = {}
    for arm, pat in (("gate", "results/routeA_f2/g_shared_gate_s*"),
                     ("nogate", "results/routeA_f2/h_shared_nogate_s*"),
                     ("noinject", "results/multi_shared_s*")):
        rows = {}
        for d in sorted(glob.glob(pat)):
            p = os.path.join(d, "summary.json")
            if not os.path.exists(p):
                continue
            seed = int(d.rsplit("_s", 1)[1])
            rows[str(seed)] = [{k: r.get(k) for k in
                                ("intent", "arctic", "midlat", "satisfaction", "kg_active", "kg_magnitudes")}
                               for r in json.load(open(p, encoding="utf-8"))]
        out[arm] = rows
    json.dump(out, open("results/routeA/f2_table.json", "w", encoding="utf-8"), indent=2)
    print("f2_table.json arms:", {k: len(v) for k, v in out.items()})


def f3() -> None:
    out = {}
    for d in sorted(glob.glob("results/routeA_f3/lam*")):
        lam = os.path.basename(d)
        vals = {}
        for p in glob.glob(os.path.join(d, "no_forensics_seed*", "run_summary.json")):
            x = json.load(open(p, encoding="utf-8"))
            if x.get("ok"):
                seed = os.path.basename(os.path.dirname(p)).rsplit("_seed", 1)[1]
                vals[seed] = 100 * x["final"]["arctic"]["hsr"]
        if vals:
            out[lam] = dict(per_seed=vals, mean=round(st.mean(vals.values()), 1),
                            sd=round(st.stdev(vals.values()), 1), n=len(vals))
    json.dump(out, open("results/routeA/f3_table.json", "w", encoding="utf-8"), indent=2)
    print("f3_table.json:", {k: (v["n"], v["mean"], v["sd"]) for k, v in out.items()})


if __name__ == "__main__":
    f2()
    f3()
