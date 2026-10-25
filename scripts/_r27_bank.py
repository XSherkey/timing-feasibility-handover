import json
from pathlib import Path

d = json.loads(Path("results/routeA_r3/gate_systematic/summary.json").read_text(encoding="utf-8"))
for c in d["bank"]:
    print(f"{c['id']:>4} {c['delta_test']:+7.2f} {c['delta_short']:+7.2f} {c['class']:<8} "
          f"admit={c['admit_short']} {c['rule']}")
