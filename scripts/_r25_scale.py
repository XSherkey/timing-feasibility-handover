"""Scale the probe block of window_case2/summary.json back to percent (arctic already returns %)."""
import json
from pathlib import Path

p = Path(__file__).resolve().parents[1] / "results" / "routeA_r3" / "window_case2" / "summary.json"
d = json.loads(p.read_text(encoding="utf-8"))
for k, v in d.get("probe", {}).items():
    for key in ("hsr", "window", "late"):
        if v.get(key) is not None and v[key] > 200:
            v[key] = v[key] / 100.0
if d.get("probe_none", {}).get("hsr", 0) > 200:
    for key in ("hsr", "window", "late"):
        d["probe_none"][key] = d["probe_none"][key] / 100.0
p.write_text(json.dumps(d, indent=2), encoding="utf-8")
print("probe hsr values:", {k: round(v["hsr"], 2) for k, v in d["probe"].items()})
print("no cap:", {k: round(v, 2) for k, v in d["probe_none"].items()})
print("guard*:", d["guard_star"])
