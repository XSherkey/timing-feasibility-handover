"""R5 ZH: rebuild the ladder table and readings with the unified numbers."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / "almond-repro"
D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"
lad = json.loads((ROOT / "results" / "routeA_r3" / "ladder_consistent" / "summary.json").read_text(encoding="utf-8"))
dm = json.loads((ROOT / "results" / "routeA_r3" / "drift_margin" / "summary.json").read_text(encoding="utf-8"))
R = lad["regimes"]
mn = lambda reg, arm: R[reg][arm]["summary"]["mean"]
deployed = {r: dm["regimes"][r]["arms"]["shield_fixed18"]["summary"]["mean"] for r in dm["regimes"]}
const = {r: dm["regimes"][r]["arms"]["const_fixed18"]["summary"]["mean"] for r in dm["regimes"]}
REG = [("1.2", "0"), ("3.2", "+2.0 s"), ("4.4", "+3.2 s"), ("5.6", "+4.4 s")]
LAD = {"1.2": "nominal", "3.2": "plus2s", "4.4": "plus3p2s", "5.6": "plus4p4s"}
gaps = [mn(LAD[k], "oracle") - deployed[k] for k, _ in REG]
oracle_sd = max(R[LAD[k]]["oracle"]["summary"]["sd"] for k, _ in REG)
lam_vs_none = [mn(LAD[k], "reward_lam8") - mn(LAD[k], "no_knowledge") for k, _ in REG]

z = D / "paper_zh.md"
t = z.read_text(encoding="utf-8")

i = t.find("| δ | oracle |")
j = t.find("\n\n", t.find("| +4.4 s", i))
rows = ["| δ | oracle | τ = 18 s（固定） | 16 s 规则（作为盾） | 调好的 18 s 常数 | 奖励 λ = 8 | 无知识 |",
        "|---|---|---|---|---|---|---|"]
for key, lab in REG:
    tag = LAD[key]
    rows.append("| %s | %.2f | %.2f | %.2f | %.2f | %.2f | %.2f |" % (
        lab, mn(tag, "oracle"), deployed[key], mn(tag, "narrative_16s_rule"),
        const[key], mn(tag, "reward_lam8"), mn(tag, "no_knowledge")))
CAP = ("**表 X. 漂移阶梯（极区 HSR，|lat| ≥ 70°，campaign 策略、traffic seed 0、相同回合，"
       "每个网格点十个策略种子；δ 为额外建链信令时延）。**\n\n" + "\n".join(rows) + "\n")
t = t[:i] + CAP + t[j:]

# readings
i = t.find("三个读法。其一，oracle 按构造对漂移免疫")
j = t.find("\n\n", t.find("这是本文其它任何臂都做不到的。", i))
NEW = (f"三个读法。其一，oracle 按构造对漂移免疫——每一格均为 {mn('nominal','oracle'):.2f}（全部阶梯格子 sd "
       f"{oracle_sd:.2f}）——因为它读取每次尝试已实现的需求。其二，固定阈值与 oracle 的差距只在漂移下打开"
       f"（δ = 0/+2/+3.2/+4.4 s 处分别为 {', '.join('%.2f' % g for g in gaps)} pp）：这个差距是*固定阈值*的实测代价，"
       f"正是分档位重新探测（第六节 D）要弥合的东西。其三，阶梯把到天花板的剩余损失定位到：标称物理下它不含任何估计误差"
       f"（部署臂等于 oracle），而是目标/窗口/路由——因此弥合它需要的是更强的*控制器*，而第六节 B 与第六节 A 已测量了"
       f"现有控制器之间的差异有多小。还有第四个读法必须并列，因为它是本文最尖锐的否结果：奖励惩罚臂在**每一个**漂移档位下"
       f"都落到无知识策略**之下**（{', '.join('%+.1f' % d for d in lam_vs_none)} pp），即按标称需求训练出的惩罚，"
       f"一旦需求移动就比没有知识更差。oracle 是上参照而非可部署控制器——它预设了任何运营系统都不具备的知识——"
       f"但它把\"估计错了\"与\"约束对了而周围的策略不行\"区分开来，这是本文其它任何臂都做不到的。")
t = t[:i] + NEW + t[j:]
z.write_text(t, encoding="utf-8")
print("ZH ladder + readings rebuilt")
print("gaps", [round(g, 2) for g in gaps], "lam-vs-none", [round(x, 2) for x in lam_vs_none])
