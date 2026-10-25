"""R7 ZH part 7: D1A/D1B sum column, Table IV caption, protocol paragraphs, Fig. 3 caption, VI-L note."""
from __future__ import annotations

import json
from pathlib import Path

D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"
ROOT = Path(__file__).resolve().parents[2] / "almond-repro"
h = json.loads((ROOT / "results" / "routeA_r3" / "headline_consistent" / "summary.json").read_text(encoding="utf-8"))
A = h["arms"]

z = D / "paper_zh.md"
t = z.read_text(encoding="utf-8")
done = []

# ---- D1A / D1B sum column -------------------------------------------------
for tag in ("表 D1A.", "表 D1B."):
    i = t.find("**" + tag)
    j = t.find("\n\n", t.find("| 合计 |", i))
    if i < 0 or j < 0:
        print("  skip", tag)
        continue
    block = t[i:j]
    out = []
    for ln in block.splitlines():
        if not ln.startswith("|"):
            out.append(ln)
            continue
        cells = [c.strip() for c in ln.strip().strip("|").split("|")]
        if set("".join(cells)) <= set("- "):
            out.append(ln)
            continue
        if cells[0] in ("提前量桶（s）", "合计", "提前量桶") or not cells[1].replace(",", "").isdigit():
            if cells[0] == "合计":
                cells = cells + [str(sum(int(c.replace(",", "")) for c in cells[2:5]))]
            else:
                cells = cells + ["Σ = 精确 + 删失 + 竞争"]
            out.append("| " + " | ".join(cells) + " |")
            continue
        exc, cen, comp = (int(c.replace(",", "")) for c in cells[2:5])
        out.append("| " + " | ".join(cells + [f"{exc + cen + comp:,}"]) + " |")
    t = t[:i] + "\n".join(out) + t[j:]
    done.append(tag)

# ---- Table IV caption -----------------------------------------------------
old = "**表 IV. 漂移响应（极区 HSR，mean ± sd，n = 10 个策略种子、traffic seed 0，极区取 |lat| ≥ 70°；两行常数控制器与策略无关，故 sd = 0.00）。**"
new = ("**表 IV. 漂移响应（极区 HSR，mean ± sd，traffic seed 0，极区取 |lat| ≥ 70°）。四个带盾/常数行为 "
       "n = 10 个策略种子；两个常数行与策略无关，故 sd = 0.00。最后一行为探测研究，使用五个策略种子并已注明。**")
if t.count(old) == 1:
    t = t.replace(old, new, 1)
    done.append("table4-caption")

# ---- protocol paragraphs --------------------------------------------------
old_probe = "在当前产物中，探测运行在留出的评估窗口上（与训练和发现都不相交）"
new_probe = ("在当前产物中，探测在**两个**留出窗口上都运行过，并返回同一阈值——验证窗口（65–75%）上的 "
             "τ∗ = 16 s 与评估窗口（82–95%）上的 16 s，二者都与训练和发现不相交。**archival** 数字（表 II–IV、图 5）"
             "使用评估窗口的探测；**three-way** 数字（表 IX 的 lockbox 行）只用验证窗口的探测，"
             "第六节 A 说明哪张表属于哪个协议")
if t.count(old_probe) == 1:
    t = t.replace(old_probe, new_probe, 1)
    done.append("viC-probe")

anchor = t.find("精确版本见第六节 A")
if anchor > 0:
    end = t.find("\n\n", anchor)
    TWO = ("\n\n**两个协议，一套数据。** 本文在**同一批**十个 campaign 策略与同一批回合上使用两个标定协议，"
           "每张表都声明自己属于哪一个。**Archival 协议**（表 II、III、IV、V、VII、VIII、X 与图 2–5）"
           "在评估窗口（82–95%）上标定阈值探测、门重放与惩罚系数，然后在同一窗口上报告；这是诚实的"
           "事后重标定结构，不是 lockbox。**Three-way 协议**（表 IX）把所有选择——探测、门重放、λ、余量——"
           "移到验证窗口（65–75%），从不触碰 lockbox 实例，后者是评估窗口在三个平移孪生历元上的实例化。"
           "由于两个窗口返回同一阈值（16 s）与同一 λ（8），两个协议的差别在它们**允许**什么，"
           "而不在它们**选出**什么；因此 archival 数字与 lockbox 数字可直接比较，表 IX 同时报告两者。")
    t = t[:end] + TWO + t[end:]
    done.append("viA-two-protocols")

# ---- Fig. 3 caption -------------------------------------------------------
i = t.find("**图 3.**")
if i > 0:
    j = t.find("\n\n", i)
    CAP = (f"**图 3.** 奖励注入是剂量-反应，而盾支配它。左：极区 HSR 对惩罚系数 λ 的八点扫描"
           f"（误差棒为十个种子的 ±sd）；虚线为部署盾（{A['almond_rule18']['summary']['mean']:.2f}%）。"
           f"曲线并不单调：λ = 0.3 与 0.5 *低于*无惩罚臂，直到 λ = 2 才重新越过。右：(HSR, S) 前沿；"
           f"盾（星标；S = {A['almond_rule18']['satisfaction_mean']:.1f}）位于所有惩罚点的右上方"
           f"（最优惩罚点 S = {A['lam8']['satisfaction_mean']:.1f}，λ = 8）。")
    t = t[:i] + CAP + t[j:]
    done.append("fig3-caption")

# ---- VI-L preliminary -----------------------------------------------------
i = t.find("**表 XI.")
if i > 0:
    t = t[:i] + ("这二十条提案是定性的首次测量，而不是统计结论：十个训练窗口的二十条叙述、两位标注者、"
                 "以及一个粗到只能把 κ 读作「分歧定位器」而非质量分数的量规。\n\n") + t[i:]
    done.append("viL-preliminary")

z.write_text(t, encoding="utf-8")
print("applied:", done)
