import json, glob
from pathlib import Path
rows = []
for p in glob.glob(r"D:\almond-repro\results\campaign\*\run_summary.json"):
    d = json.loads(Path(p).read_text(encoding="utf-8"))
    if not d.get("ok"):
        continue
    f = [e for e in (d.get("forensics") or []) if e.get("accepted")]
    rows.append(dict(method=d["method"], seed=d["seed"],
                     arc=d["final"]["arctic"]["hsr"] * 100,
                     model=(d.get("llm") or {}).get("model", "?"),
                     spec=f'{d["spec"]["kind"]}-w{d["spec"]["width"]}-L{d["spec"]["layers"]}',
                     commits=len(f),
                     rules=[(e.get("effect"), e.get("delta_test")) for e in f]))
rows.sort(key=lambda r: (r["method"], r["seed"]))
print(f"{'method':<18}{'seed':>5}{'arctic':>9}{'model':>16}{'spec':>14}{'commits':>9}")
for r in rows:
    print(f'{r["method"]:<18}{r["seed"]:>5}{r["arc"]:>8.1f}%{r["model"]:>16}{r["spec"]:>14}{r["commits"]:>9}')
print()
from collections import defaultdict
agg = defaultdict(list)
for r in rows:
    agg[r["method"]].append(r)
print(f"{'method':<18}{'n':>3}{'arctic mean':>13}{'commits':>9}{'conv(>=80)':>12}")
for m, rs in agg.items():
    arc = [x["arc"] for x in rs]
    print(f"{m:<18}{len(rs):>3}{sum(arc)/len(arc):>12.1f}%{sum(x['commits'] for x in rs):>9}"
          f"{sum(1 for a in arc if a>=80)}/{len(arc):<10}")
print()
alm = [r for r in rows if r["method"] == "almond"]
for mdl in ("deepseek-flash", "deepseek-v4-pro"):
    sub = [r["arc"] for r in alm if r["model"] == mdl]
    if sub:
        print(f"ALMOND {mdl:<18} n={len(sub)} mean={sum(sub)/len(sub):.1f}% values={[round(x,1) for x in sub]}")
