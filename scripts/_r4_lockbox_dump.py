import json

d = json.load(open("results/routeA_r2/lockbox_summary.json", encoding="utf-8"))
for ep in ("e299", "e306", "e290"):
    print("==", ep)
    for arm in d[ep]:
        v = d[ep][arm]
        if isinstance(v, dict) and "mean" in v:
            print("   %-10s n=%2d mean=%6.2f sd=%5.2f late=%s"
                  % (arm, v.get("n", -1), v["mean"], v.get("sd", float("nan")), v.get("late")))
    print()
print("traffic_robustness:", json.dumps(d.get("traffic_robustness"), indent=1)[:400])
