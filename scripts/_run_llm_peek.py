import json, sys
p = sys.argv[1]
rows = [json.loads(l) for l in open(p, encoding="utf-8")]
print("calls:", len(rows))
for r in rows[-8:]:
    print(f"  {r['call_type']:<22} seed={r['seed']:<6} ok={r.get('schema_ok')} attempts={r.get('attempts')} "
          f"lat={r.get('latency_s',0):5.1f}s tok_out={r.get('tokens_out')} problem={str(r.get('schema_problem'))[:80]}")
print("total schema retries:", sum(1 for r in rows if not r.get('schema_ok', True)))
