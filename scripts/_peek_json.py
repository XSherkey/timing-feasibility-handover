import json
from pathlib import Path
s = json.loads(Path(r"D:\almond-repro\results\auditor_stress.json").read_text(encoding="utf-8"))
print("top keys:", list(s.keys()))
print("summary keys:", list(s["summary"].keys()))
for k, v in s["summary"].items():
    print(f"  {k:<14} {v}")
print("overall:", s.get("overall"))
lat = json.loads(Path(r"D:\almond-repro\results\latency_benchmark.json").read_text(encoding="utf-8"))
print("\nlatency keys:", list(lat.keys()))
print("variants:", {k: {kk: round(vv,4) for kk,vv in v.items()} for k, v in lat["variants"].items()})
