import json, collections
p = r"D:\almond-repro\results\llm_stability.calls.jsonl"
c = collections.Counter(); ok = collections.Counter()
for line in open(p, encoding="utf-8"):
    r = json.loads(line)
    c[r["call_type"]] += 1
    ok[r["call_type"]] += int(r.get("schema_ok", True))
for k, v in c.items():
    print(f"{k:<24} calls {v:4d}  schema_ok {ok[k]:4d}")
print("total", sum(c.values()))
