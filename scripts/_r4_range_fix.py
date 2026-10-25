"""R4 (v26) final: fix the window/route range sentence so the numbers are monotone."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / "almond-repro"
D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"
h = json.loads((ROOT / "results" / "routeA_r3" / "headline_consistent" / "summary.json").read_text(encoding="utf-8"))
A = h["arms"]
c = lambda k, key: 100.0 * A[k]["causes"].get(key, 0.0)

win = [c(k, "window_exceeded") for k in ("ppomlp_none", "noforensics_none", "almond_rule16")]
rou = [c(k, "no_route") for k in ("ppomlp_none", "noforensics_none", "almond_rule16")]

p = D / "paper_en.md"
t = p.read_text(encoding="utf-8")
old = (f"Window and route failures stay within "
       f"{c('almond_rule16','window_exceeded'):.1f}–{c('ppomlp_none','no_route'):.1f}% in every row; the shield "
       f"trades a fraction of window violations ({c('ppomlp_none','window_exceeded'):.1f}% → "
       f"{c('almond_rule16','window_exceeded'):.1f}%) for the late handovers it removes, exactly as Eq. (3) "
       f"predicts.")
new = (f"Window failures move only from {min(win):.1f}% to {max(win):.1f}% and route failures stay between "
       f"{min(rou):.1f}% and {max(rou):.1f}%: the shield trades a fraction of window violations for the late "
       f"handovers it removes, exactly as Eq. (3) predicts.")
if t.count(old) != 1:
    raise SystemExit(f"EN sentence found {t.count(old)}")
t = t.replace(old, new, 1)
p.write_text(t, encoding="utf-8")
print("EN fixed")

z = D / "paper_zh.md"
s = z.read_text(encoding="utf-8")
old_z = (f"窗口与路由失效在每行都不超过 "
         f"{c('almond_rule16','window_exceeded'):.1f}–{c('ppomlp_none','no_route'):.1f}%；盾用少量窗口违例"
         f"（{c('ppomlp_none','window_exceeded'):.1f}% → {c('almond_rule16','window_exceeded'):.1f}%）换掉了它消除的晚切换，"
         f"恰如式（3）所预言。")
new_z = (f"窗口失效只从 {min(win):.1f}% 变到 {max(win):.1f}%，路由失效保持在 {min(rou):.1f}% 至 {max(rou):.1f}% 之间："
         f"盾用少量窗口违例换掉了它消除的晚切换，恰如式（3）所预言。")
if s.count(old_z) == 1:
    s = s.replace(old_z, new_z, 1)
    z.write_text(s, encoding="utf-8")
    print("ZH fixed")
else:
    print("ZH sentence not found, count:", s.count(old_z))
