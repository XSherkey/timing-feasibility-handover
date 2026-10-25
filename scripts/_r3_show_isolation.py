import json

d = json.load(open("results/routeA_r3/isolation/summary.json", encoding="utf-8"))
print("selections:", {k: (v.get("best") if isinstance(v, dict) else None) for k, v in d["selections"].items()})
print()
for arm, v in d["arms"].items():
    if "polar" in v:
        print("%-18s rule=%-46s eval %6.2f  lb299 %6.2f  lb306 %6.2f  lb290 %6.2f"
              % (arm, v["rule"][:46],
                 v["polar"]["eval"]["mean"], v["polar"]["lb299.25"]["mean"],
                 v["polar"]["lb306.25"]["mean"], v["polar"]["lb290.25"]["mean"]))
    elif "instances" in v:
        print("%-18s lead=%s  eval %6.2f  lb299 %6.2f  lb306 %6.2f  lb290 %6.2f"
              % (arm, v["best_lead"],
                 v["instances"]["eval"]["summary"]["mean"], v["instances"]["lb299.25"]["summary"]["mean"],
                 v["instances"]["lb306.25"]["summary"]["mean"], v["instances"]["lb290.25"]["summary"]["mean"]))
print()
print("decision:", json.dumps(d["decision"], indent=1))
c = d["contrasts_vs_A0"].get("A8_constantProbe")
if c:
    for inst, st in c.items():
        print("A8 vs A0", inst, "diff %.2f CI %s p=%s" % (st["mean_diff"], st["ci95"], st["wilcoxon_p"]))
