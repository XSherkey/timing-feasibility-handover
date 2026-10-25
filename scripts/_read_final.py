import json
from pathlib import Path
lat = json.loads(Path(r"D:\almond-repro\results\latency_benchmark.json").read_text(encoding="utf-8"))
print("params:", lat["params"], "weight KB:", round(lat["weight_bytes_fp32"]/1024,1))
print("spec:", lat["spec"])
print("board:", lat["board"]["cpu"], "|", lat["board"]["gpu"])
cmp = json.loads(Path(r"D:\almond-repro\results\backend_comparison.json").read_text(encoding="utf-8"))
print("llm surrogate:", {k: v for k, v in cmp["llm"]["surrogate"].items() if k != "backends"})
print("llm real:", {k: v for k, v in cmp["llm"]["real"].items()})
