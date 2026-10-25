"""R7 ZH part 2: C3 rebuild (anchor differs) — the other three tables already applied."""
from __future__ import annotations

import json
from pathlib import Path

D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"
ROOT = Path(__file__).resolve().parents[2] / "almond-repro"
fc = json.loads((ROOT / "results" / "routeA_r3" / "factorial_consistent" / "summary.json").read_text(encoding="utf-8"))
c3 = json.loads((ROOT / "results" / "routeA_r3" / "c3_deployed" / "summary.json").read_text(encoding="utf-8"))
dm = json.loads((ROOT / "results" / "routeA_r3" / "drift_margin" / "summary.json").read_text(encoding="utf-8"))
F = fc["arms"]

z = D / "paper_zh.md"
t = z.read_text(encoding="utf-8")
i = t.find("**表 C3. 漂移响应逐种子")
if i < 0:
    raise SystemExit("ZH C3 caption not found")
j = t.find("\n\n", t.find("|", t.find("| 均值", i)) if t.find("| 均值", i) > 0 else t.find("|", i + 200))
if j < 0:
    raise SystemExit("ZH C3 end not found")

const = [dm["regimes"][r]["arms"]["const_fixed18"]["summary"]["mean"] for r in ("1.2", "3.2", "4.4", "5.6")]
probed = [dm["regimes"][r]["arms"]["const_probed"]["summary"]["mean"] for r in ("1.2", "3.2", "4.4", "5.6")]
rows = ["| 种子 | 无盾 | τ = 16 s | 部署（τ = 18 s） | +2.0 s 漂移 | +3.2 s 漂移 | +4.4 s 漂移 | 增益（无盾→部署） |",
        "|---|---|---|---|---|---|---|---|"]
for k in range(10):
    none = F["none"]["polar"][k]
    dep = c3["0"]["polar"][k]
    rows.append("| %d | %.1f | %.1f | %.2f | %.2f | %.2f | %.2f | +%.1f |" % (
        k, none, F["rule16"]["polar"][k], dep,
        c3["+2"]["polar"][k], c3["+3.2"]["polar"][k], c3["+4.4"]["polar"][k], dep - none))
rows.append("| 均值 ± 标准差 | %.1f ± %.1f | %.2f ± %.2f | %.2f ± %.2f | %.2f ± %.2f | %.2f ± %.2f | %.2f ± %.2f | — |" % (
    F["none"]["summary"]["mean"], F["none"]["summary"]["sd"],
    F["rule16"]["summary"]["mean"], F["rule16"]["summary"]["sd"],
    c3["0"]["summary"]["mean"], c3["0"]["summary"]["sd"],
    c3["+2"]["summary"]["mean"], c3["+2"]["summary"]["sd"],
    c3["+3.2"]["summary"]["mean"], c3["+3.2"]["summary"]["sd"],
    c3["+4.4"]["summary"]["mean"], c3["+4.4"]["summary"]["sd"]))
C3 = ("**表 C3. 逐种子漂移响应（极区 HSR，|lat| ≥ 70°，campaign 策略、traffic seed 0，n = 10 个策略种子）。"
      "带盾列在多个种子上几乎相同，是因为一旦施加约束，带内的结果由约束而非策略决定——残余散布"
      "（sd 0.05，两个种子 93.45–93.47）是选择质量，也就是图 2 展示的同一种散布。调好常数与策略无关，"
      "只给档位均值：固定 18 s 为 " + " / ".join("%.2f" % v for v in const) + "，重探为 " +
      " / ".join("%.2f" % v for v in probed) + "（δ = 0/+2/+3.2/+4.4 s）。**\n\n" + "\n".join(rows) + "\n")
t = t[:i] + C3 + t[j:]
z.write_text(t, encoding="utf-8")
print("ZH C3 rebuilt")
