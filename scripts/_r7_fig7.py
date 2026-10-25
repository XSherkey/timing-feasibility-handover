"""R8 part 9: the Fig. 7 caption (lambda frontier) still quotes the pre-unification shield values."""
from __future__ import annotations

import json
from pathlib import Path

D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"
ROOT = Path(__file__).resolve().parents[2] / "almond-repro"
h = json.loads((ROOT / "results" / "routeA_r3" / "headline_consistent" / "summary.json").read_text(encoding="utf-8"))
A = h["arms"]
sh, ss = A["almond_rule18"]["summary"]["mean"], A["almond_rule18"]["satisfaction_mean"]
best_s = A["lam8"]["satisfaction_mean"]

p = D / "paper_en.md"
t = p.read_text(encoding="utf-8")
i = t.find("**Fig. 7.**")
if i < 0:
    raise SystemExit("Fig. 7 caption not found")
j = t.find("\n\n", i)
CAP = (f"**Fig. 7.** Reward injection is a dose-response, and the shield dominates it. Left: polar HSR against "
       f"the penalty coefficient λ over the eight-point scan (error bars ±sd over ten seeds); the dashed line "
       f"is the deployed shield ({sh:.2f}%). The curve is not monotone—λ = 0.3 and 0.5 sit below the "
       f"no-penalty arm. Right: the (HSR, S) frontier; the shield (star; S = {ss:.1f}) is above and to the "
       f"right of every penalty point (best penalty point S = {best_s:.1f} at λ = 8).")
t = t[:i] + CAP + t[j:]
p.write_text(t, encoding="utf-8")
print("EN Fig. 7 caption updated")

z = D / "paper_zh.md"
s = z.read_text(encoding="utf-8")
i = s.find("**图 7.**")
if i < 0:
    raise SystemExit("ZH Fig. 7 caption not found")
j = s.find("\n\n", i)
CAPZ = (f"**图 7.** 奖励注入是剂量-反应，且盾支配它。左：极区 HSR 对惩罚系数 λ 的八点扫描"
        f"（误差棒为十个种子的 ±sd）；虚线为部署盾（{sh:.2f}%）。曲线并不单调——λ = 0.3 与 0.5 低于无惩罚臂。"
        f"右：(HSR, S) 前沿；盾（星标；S = {ss:.1f}）位于所有惩罚点的右上方（最优惩罚点 S = {best_s:.1f}，λ = 8）。")
s = s[:i] + CAPZ + s[j:]

# ZH drift caption
old = ("**表 V. 漂移响应（极区 HSR，mean ± sd，n = 10 个策略种子、traffic seed 0，极区取 |lat| ≥ 70°；"
       "两行常数控制器与策略无关，故 s")
k = s.find(old)
if k > 0:
    end = s.find("**", k + 10)
    end2 = s.find("\n", k)
    print("ZH drift caption:", repr(s[k:end2][:200]))
z.write_text(s, encoding="utf-8")
print("ZH Fig. 7 caption updated")
