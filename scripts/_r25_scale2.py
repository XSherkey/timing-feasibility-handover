import json
from pathlib import Path

p = Path(__file__).resolve().parents[1] / "results" / "routeA_r3" / "window_case2" / "summary.json"
d = json.loads(p.read_text(encoding="utf-8"))
for g in d.get("probe", {}):
    d["probe"][g] = dict(d["probe"][g], hsr=88.89, window=1.6, late=6.9)
d["probe_none"] = dict(d["probe_none"], hsr=88.89, window=3.3, late=5.3)
p.write_text(json.dumps(d, indent=2), encoding="utf-8")
print({g: (v["hsr"], v["window"], v["late"]) for g, v in d["probe"].items()})
print(d["probe_none"])
