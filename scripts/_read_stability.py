import json
from pathlib import Path
p = Path(r"D:\almond-repro\results\llm_stability.json")
d = json.loads(p.read_text(encoding="utf-8"))
print("meta:", json.dumps(d.get("_meta", {}), indent=2)[:600])
print()
print(f"{'call type':<24}{'exact':>8}{'semantic':>10}{'schema-fail':>13}{'retry':>8}{'calls':>7}")
for k, v in d.items():
    if k == "_meta":
        continue
    print(f"{k:<24}{v['exact_match']*100:7.0f}%{v['semantic_equivalence']*100:9.0f}%"
          f"{v['schema_failure_rate']*100:12.1f}%{v['retry_rate']*100:7.1f}%{v['n_calls']:7d}")
