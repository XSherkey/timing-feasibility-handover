import csv
import json

rows = list(csv.DictReader(open("results/routeA_r3/llm_proposals/proposals.csv", encoding="utf-8")))
print(len(rows))
for r in rows:
    rule = json.loads(r["p1_rule"]) if r["p1_rule"] else {}
    print("%2s | %-14s | %s | mag=%s" % (
        r["narrative_id"],
        (rule.get("effect") or "-"),
        json.dumps(rule.get("atoms"), ensure_ascii=False),
        r.get("p2_magnitude")))
print()
print("--- narrative 1 ---")
print(rows[0]["narrative"][:700])
print()
print("--- narrative 7 ---")
print(rows[6]["narrative"][:700])
