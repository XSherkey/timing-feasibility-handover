"""R5 ZH: the asymmetry, margin sweep, limitation 1 and Fig. 3 caption, with the real Chinese strings."""
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
m2 = [mr[r]["margin"]["m2"]["summary"]["mean"] for r in mr]
m4 = [mr[r]["margin"]["m4"]["summary"]["mean"] for r in mr]
m0 = [mr[r]["margin"]["m0"]["summary"]["mean"] for r in mr]
cp = [mr[r]["arms"]["const_probed"]["summary"]["mean"] for r in mr]

z = D / "paper_zh.md"
s = z.read_text(encoding="utf-8")
done = []


def repz(old, new, label):
    global s
    n = s.count(old)
    if n != 1:
        print(f"  MISS [{label}] {n}")
        return
    s = s.replace(old, new, 1)
    done.append(label)


repz("平台附近的损失是严重不对称的，我们直接测量了它：在冻结策略上，比平台低一个 2 s 网格步损失 4.8 pp 极区成功率（88.6% 对 93.4%），高一个步在 26 s 网格上限之前不花任何代价（93.4% 对 94.0%）。",
     f"平台附近的损失是不对称的，我们用两种方式测量它。标称物理下，比部署阈值低一个网格步要多付 "
     f"{A['rule18']['summary']['mean'] - A['rule16']['summary']['mean']:.1f} pp（16 s 的 "
     f"{A['rule16']['summary']['mean']:.2f}% 对 18 s 的 {A['rule18']['summary']['mean']:.2f}%），而高一步只付 "
     f"{A['rule18']['summary']['mean'] - A['rule20']['summary']['mean']:.2f} pp（20 s 的 "
     f"{A['rule20']['summary']['mean']:.2f}%）。在漂移下这种不对称要大一个数量级，因为低一步的阈值会随物理退化，"
     f"而高一步的不会（表 IV）：同样 2 s 的误差在需求移动后要付 9.9 pp。", "asymmetry")

repz("三个物理档位（标称、+2 s、+3.2 s 漂移）、五个种子下，m = 2 使每个种子都 ≥ 93.2%；无余量时有一个种子掉到 92.4%；m = 4 不再更好（标称下 94.0% 对 93.9%）。",
     f"四个物理档位、十个策略种子下，m = 2 守住 {min(m2):.2f}–{max(m2):.2f}%；无余量时同一条臂在标称下读 "
     f"{m0[0]:.2f}%、在漂移下最低 {min(m0):.2f}%；m = 4 在标称下为 {m4[0]:.2f}%（{m4[0] - m2[0]:+.2f} pp），"
     f"即没有增加任何东西。", "margin")

repz("**图 3.** 常数的失效边界。极区 HSR 对额外建链时延（均值 ± min–max 带，n = 5）：固定 18 s 常数（红）撑到约 2 s 漂移后开始崩溃（+3.2 s 处 −5.0 pp）；带 2 s 余量的探测标定（蓝）重新测量需求（16/18/20/22 s），守住 93.3–94.0%。",
     f"**图 3.** 常数的失效边界。极区 HSR 对额外建链时延（campaign 策略、traffic seed 0，n = 10）："
     f"固定 18 s 常数（红）撑到约 2 s 漂移后开始崩溃（+3.2 s 处 −7.4 pp，+4.4 s 处 −9.8 pp）；"
     f"带 2 s 余量的探测标定（蓝）重新测量需求（16/18/20/22 s），守住 {min(cp):.2f}–{max(cp):.2f}%。",
     "fig3")

i = s.find("**调好的常数在标称物理下与我们持平。**")
if i > 0:
    j = s.find("\n", i)
    s = s[:i] + (f"**调好的常数在标称物理下与我们持平。** 20 s 为 {A['rule20']['summary']['mean']:.2f}%，"
                 f"最高仰角控制器为 {H['maxel18']['summary']['mean']:.2f}%，部署算法为 "
                 f"{A['rule18']['summary']['mean']:.2f}%。") + s[j:]
    done.append("limitation-1")

z.write_text(s, encoding="utf-8")
print("applied:", done)
