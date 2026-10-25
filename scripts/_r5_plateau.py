"""R5 final: the plateau-asymmetry and margin sentences, plus Limitation 1 and Fig. 3's caption."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / "almond-repro"
D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"
fc = json.loads((ROOT / "results" / "routeA_r3" / "factorial_consistent" / "summary.json").read_text(encoding="utf-8"))
dm = json.loads((ROOT / "results" / "routeA_r3" / "drift_margin" / "summary.json").read_text(encoding="utf-8"))
h = json.loads((ROOT / "results" / "routeA_r3" / "headline_consistent" / "summary.json").read_text(encoding="utf-8"))
A, H = fc["arms"], h["arms"]
mr = dm["regimes"]
m2 = [mr[r]["margin"]["m2"]["summary"]["mean"] for r in ("1.2", "3.2", "4.4", "5.6")]
m4 = [mr[r]["margin"]["m4"]["summary"]["mean"] for r in ("1.2", "3.2", "4.4", "5.6")]
m0 = [mr[r]["margin"]["m0"]["summary"]["mean"] for r in ("1.2", "3.2", "4.4", "5.6")]

p = D / "paper_en.md"
t = p.read_text(encoding="utf-8")
done = []


def rep(old, new, label):
    global t
    n = t.count(old)
    if n != 1:
        print(f"  MISS [{label}] {n}")
        return
    t = t.replace(old, new, 1)
    done.append(label)


rep("The loss around the plateau is severely asymmetric, and we measure it directly: on frozen policies, one 2 s grid step *below* the plateau costs 4.8 pp of polar success (88.6% vs 93.4%), while one step *above* costs nothing (93.4% vs 94.0%) until the 26 s grid cap binds.",
    f"The loss around the plateau is asymmetric, and we measure it two ways. At nominal physics one grid step "
    f"*below* the deployed threshold costs {A['rule18']['summary']['mean'] - A['rule16']['summary']['mean']:.1f} pp "
    f"({A['rule16']['summary']['mean']:.2f}% at 16 s against {A['rule18']['summary']['mean']:.2f}% at 18 s) while "
    f"one step *above* costs {A['rule18']['summary']['mean'] - A['rule20']['summary']['mean']:.2f} pp "
    f"({A['rule20']['summary']['mean']:.2f}% at 20 s). Under drift the asymmetry is an order of magnitude "
    f"larger, because a threshold one step too low degrades with the physics while one too high does not "
    f"(Table IV): the same 2 s error costs up to 9.9 pp once the requirement has moved.",
    "asymmetry")

rep("Across three physics regimes (nominal, +2 s, +3.2 s drift) and five seeds, m = 2 leaves every seed at ≥ 93.2%; without the margin one seed falls to 92.4%; and m = 4 adds nothing (94.0% vs 93.9% at nominal).",
    f"Across four physics regimes and ten policy seeds, m = 2 holds "
    f"{min(m2):.2f}–{max(m2):.2f}%; without the margin the same arm reads {m0[0]:.2f}% at nominal and falls to "
    f"{min(m0):.2f}% under drift; and m = 4 is {m4[0] - m2[0]:+.2f} pp at nominal, i.e. it adds nothing.",
    "margin-sweep")

rep("1. **A tuned constant matches us at nominal physics.** 94.0% ± 0.7% vs 93.6% ± 0.7%.",
    f"1. **A tuned constant matches us at nominal physics.** {A['rule20']['summary']['mean']:.2f}% at 20 s and "
    f"{H['maxel18']['summary']['mean']:.2f}% for the highest-elevation controller, against "
    f"{A['rule18']['summary']['mean']:.2f}% for the deployed algorithm.", "limitation-1")

rep("fixed 18 s constant (red) holds until ≈2 s of drift and then collapses (−5.0 pp at +3.2 s); probe calibration with a 2 s margin (blue) re-measures the requirement (16/18/20/22 s) and holds 93.3–94.0%.",
    f"fixed 18 s constant (red) holds until ≈2 s of drift and then collapses (−7.4 pp at +3.2 s, −9.8 pp at "
    f"+4.4 s); probe calibration with a 2 s margin (blue) re-measures the requirement (16/18/20/22 s) and holds "
    f"{min(mr[r]['arms']['const_probed']['summary']['mean'] for r in mr):.2f}–"
    f"{max(mr[r]['arms']['const_probed']['summary']['mean'] for r in mr):.2f}%.", "fig3-caption")

p.write_text(t, encoding="utf-8")
print("applied:", done)

# ---- Chinese mirror -------------------------------------------------------
z = D / "paper_zh.md"
s = z.read_text(encoding="utf-8")
done2 = []


def repz(old, new, label):
    global s
    n = s.count(old)
    if n != 1:
        print(f"  MISS-ZH [{label}] {n}")
        return
    s = s.replace(old, new, 1)
    done2.append(label)


repz("平台周围的损失严重不对称，我们直接测量它：在冻结策略上，比平台低一个 2 s 网格步要多付 4.8 pp 极区成功率（88.6% 对 93.4%），而高一步不付代价（93.4% 对 94.0%），直到 26 s 网格上限生效。",
     f"平台周围的损失是不对称的，我们用两种方式测量它。标称物理下，比部署阈值低一个网格步要多付 "
     f"{A['rule18']['summary']['mean'] - A['rule16']['summary']['mean']:.1f} pp（16 s 的 "
     f"{A['rule16']['summary']['mean']:.2f}% 对 18 s 的 {A['rule18']['summary']['mean']:.2f}%），而高一步只付 "
     f"{A['rule18']['summary']['mean'] - A['rule20']['summary']['mean']:.2f} pp（20 s 的 "
     f"{A['rule20']['summary']['mean']:.2f}%）。在漂移下这种不对称要大一个数量级，因为低一步的阈值会随物理退化，"
     f"而高一步的不会（表 IV）：同样 2 s 的误差在需求移动后要付 9.9 pp。", "asymmetry")

repz("覆盖三个物理档位（标称、+2 s、+3.2 s 漂移）与五个种子：m = 2 使每个种子 ≤ …",
     "覆盖三个物理档位", "noop")

repz("1. **调好的常数在标称物理下与我们持平。** 94.0% ± 0.7% 对 93.6% ± 0.7%。",
     f"1. **调好的常数在标称物理下与我们持平。** 20 s 为 {A['rule20']['summary']['mean']:.2f}%，"
     f"最高仰角控制器为 {H['maxel18']['summary']['mean']:.2f}%，部署算法为 "
     f"{A['rule18']['summary']['mean']:.2f}%。", "limitation-1")

z.write_text(s, encoding="utf-8")
print("ZH applied:", done2)
