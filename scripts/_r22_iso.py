import json
from pathlib import Path

p = Path(r"../almond-repro/results/routeA_r3/isolation/summary.json")
d = json.loads(p.read_text(encoding="utf-8"))
arms = d["arms"]
print("arms:", list(arms.keys()))
for k, v in arms.items():
    if isinstance(v, dict):
        keys = list(v.keys())[:6]
        print(k, "->", keys)
        break
print(json.dumps(arms.get("A6", arms), indent=1)[:1200])
