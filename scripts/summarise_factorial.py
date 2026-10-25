"""Summarise the frozen-policy x shield factorial (results/verify_1023/factorial.json)."""
import json
import statistics as st
from collections import defaultdict

d = json.load(open(r"results/verify_1023/factorial.json", encoding="utf-8"))

tab = defaultdict(dict)
for r in d:
    arm, cond = r["label"].split("/")
    name, seed = arm.rsplit("_s", 1)
    tab[(name, int(seed))][cond] = r

print(f"{'arm':<10}{'seed':>5}{'no shield':>11}{'+16 s':>9}{'+20 s':>9}{'mid none':>10}{'mid 16':>9}{'S none':>8}{'S 20':>8}")
print("-" * 82)
for (name, seed) in sorted(tab):
    e = tab[(name, seed)]
    a = e["none"]["arctic"][0] * 100
    b = e["tau16"]["arctic"][0] * 100
    c = e["tau20"]["arctic"][0] * 100
    m0 = e["none"]["midlat"][0] * 100
    m1 = e["tau16"]["midlat"][0] * 100
    print(f"{name:<10}{seed:>5}{a:>10.1f}%{b:>8.1f}%{c:>8.1f}%{m0:>9.1f}%{m1:>8.1f}%"
          f"{e['none']['satisfaction']:>8.1f}{e['tau20']['satisfaction']:>8.1f}")

print()
for name in ("almond", "ppomlp"):
    for cond in ("none", "tau16", "tau20"):
        v = [tab[(name, s)][cond]["arctic"][0] * 100 for s in range(10)]
        s_ = [tab[(name, s)][cond]["satisfaction"] for s in range(10)]
        print(f"{name:<8} {cond:<6} arctic {st.mean(v):5.1f} +- {st.stdev(v):4.1f} "
              f"(median {st.median(v):5.1f}, min {min(v):5.1f})   S {st.mean(s_):5.1f}")

print()
print("paired deltas (same weights, only the shield changes):")
for name in ("almond", "ppomlp"):
    d16 = [tab[(name, s)]["tau16"]["arctic"][0] - tab[(name, s)]["none"]["arctic"][0] for s in range(10)]
    d20 = [tab[(name, s)]["tau20"]["arctic"][0] - tab[(name, s)]["none"]["arctic"][0] for s in range(10)]
    print(f"  {name:<8} tau16 {100 * st.mean(d16):+6.1f} pp (min {100 * min(d16):+.1f}, max {100 * max(d16):+.1f})"
          f"   tau20 {100 * st.mean(d20):+6.1f} pp (min {100 * min(d20):+.1f}, max {100 * max(d20):+.1f})")
    # correlation between the arm's own advance use and the shield gain
    print(f"           seeds helped most: {sorted(range(10), key=lambda s: -tab[(name, s)]['tau20']['arctic'][0] + tab[(name, s)]['none']['arctic'][0])[:3]}")
