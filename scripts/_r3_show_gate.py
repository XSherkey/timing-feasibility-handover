import json

d = json.load(open("results/routeA_r3/gate_systematic/summary.json", encoding="utf-8"))
for r in d["bank"]:
    print("%s %-8s short %+6.2f long %+6.2f test %+6.2f admit_long=%s"
          % (r["id"], r["class"], r["delta_short"], r["delta_long"], r["delta_test"], r["admit_long"]))
print()
for b in ("short", "long"):
    g = d["gate"][b]
    print(b, "FA", round(g["false_accept"], 3), "FR", round(g["false_reject"], 3),
          "admitted", g["n_admitted"],
          "on", None if g["hsr_gate_on_pp"] is None else round(g["hsr_gate_on_pp"], 2),
          "offworst", round(g["hsr_gate_off_worst_pp"], 2),
          "mean admitted", round(g["mean_delta_admitted_pp"], 2))
    print("   confusion", g["confusion"])
