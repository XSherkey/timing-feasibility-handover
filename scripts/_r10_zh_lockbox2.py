"""R11 part 3: the Chinese lockbox sentence with its exact wording."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / "almond-repro"
D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"
gs = json.loads((ROOT / "results" / "routeA_r3" / "gate_systematic" / "summary.json").read_text(encoding="utf-8"))
n_adm = sum(1 for b in gs["bank"] if b["admit_short"])

z = D / "paper_zh.md"
t = z.read_text(encoding="utf-8")
old = ("挖掘规则、门判定与 λ = 8 保持原冻结状态——这也意味着这三项的**选择**仍然源自原始评估窗口："
       "锁箱冻结该选择并测量它，不重新选择任何东西。")
new = (f"这三项选择也都能仅凭验证窗口重新得到：探测在验证窗口上返回 τ∗ = 16 s，λ 扫描在验证窗口上返回 λ = 8"
       f"（验证极区 HSR 81.52%），而只按验证重放重跑门的准入，得到的准入与拒绝完全相同"
       f"（{n_adm} 条准入、{26 - n_adm} 条拒绝；去掉评估窗口重放后没有任何候选的判定改变）。"
       f"因此锁箱测量的是一组「仅凭验证窗口即可复现」的选择；它额外保证的是：这一组选择从未被锁箱触碰。")
print("count", t.count(old))
if t.count(old) == 1:
    t = t.replace(old, new, 1)
    z.write_text(t, encoding="utf-8")
    print("fixed")
