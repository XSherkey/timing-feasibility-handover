"""R11 part 2: mirror the transposed lockbox table and the protocol paragraph into Chinese."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / "almond-repro"
D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"
lk = json.loads((ROOT / "results" / "routeA_r3" / "lockbox_consistent" / "summary.json").read_text(encoding="utf-8"))
gs = json.loads((ROOT / "results" / "routeA_r3" / "gate_systematic" / "summary.json").read_text(encoding="utf-8"))
I = lk["instances"]
INSTS = [("eval", "评估窗口（archival）"), ("lb299.25", "+7 d（three-way）"),
         ("lb306.25", "+14 d（three-way）"), ("lb290.25", "−2 d（three-way）")]
ARMS = [("no_shield", "无盾，全系统"), ("ppomlp_no_shield", "无盾，PPO-MLP"),
        ("mined_16", "挖掘 16 s 规则"), ("deployed_18", "**部署，τ_used = 18 s**"),
        ("tuned_constant", "调好常数 18 s"), ("ppomlp_mined_16", "PPO-MLP + 16 s 规则"),
        ("reward_lam8", "奖励惩罚 λ = 8"), ("oracle", "oracle 盾")]
n_adm = sum(1 for b in gs["bank"] if b["admit_short"])

z = D / "paper_zh.md"
t = z.read_text(encoding="utf-8")

i = t.find("| 实例 | 无盾（全）")
if i < 0:
    raise SystemExit("ZH lockbox table not found")
j = t.find("\n\n", t.find("| lockbox −2", i))
if j < 0:
    j = t.find("\n\n", t.find("| −2 d", i))
rows = ["| 臂 | " + " | ".join(lbl for _, lbl in INSTS) + " |", "|" + "---|" * 5]
for arm, lab in ARMS:
    cells = " | ".join("%.2f" % I[inst][arm]["summary"]["mean"] for inst, _ in INSTS)
    rows.append(f"| {lab} | {cells} |")
t = t[:i] + "\n".join(rows) + t[j:]

old = ("挖出规则、门判定与 λ = 8 都保持最初冻结的样子——这也意味着这三项的选择仍源自最初的评估窗口；"
       "lockbox 冻结该选择并测量它，不重新选择任何东西。")
new = (f"这三项选择也都能仅凭验证窗口重新得到：探测在验证窗口上返回 τ∗ = 16 s，λ 扫描在验证窗口上返回 λ = 8"
       f"（验证极区 HSR 81.52%），而只按验证重放重跑门的准入，得到的准入与拒绝完全相同"
       f"（{n_adm} 条准入、{26 - n_adm} 条拒绝；去掉评估窗口重放后没有任何候选的判定改变）。"
       f"因此 lockbox 测量的是一组「仅凭验证窗口即可复现」的选择；它额外保证的是：这一组选择从未被 lockbox 触碰。")
print("ZH lockbox para count", t.count(old))
if t.count(old) == 1:
    t = t.replace(old, new, 1)

z.write_text(t, encoding="utf-8")
print("ZH updated")
