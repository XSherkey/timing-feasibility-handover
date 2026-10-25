"""R8 part 7: ZH structural mirrors — C1 merge, C3->C2, D1 reshape, equations, kappa, captions."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / "almond-repro"
D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"
fc = json.loads((ROOT / "results" / "routeA_r3" / "factorial_consistent" / "summary.json").read_text(encoding="utf-8"))
F = fc["arms"]

z = D / "paper_zh.md"
t = z.read_text(encoding="utf-8")
done = []

# ---- merge C1 + C2 -------------------------------------------------------
i = t.find("**表 C1.")
j = t.find("\n\n", t.find("| 晚切换占比", t.find("**表 C2.")))
if i < 0 or j < 0:
    raise SystemExit(f"ZH C1/C2 not found ({i},{j})")
rows = ["| 种子 | 无盾 | τ = 16 s | τ = 18 s（部署） | τ = 20 s | oracle |", "|---|---|---|---|---|---|"]
for k in range(10):
    rows.append("| %d | %.1f | %.1f | %.1f | %.1f | %.1f |" % (
        k, F["none"]["polar"][k], F["rule16"]["polar"][k], F["rule18"]["polar"][k],
        F["rule20"]["polar"][k], F["oracle"]["polar"][k]))
rows.append("| 均值 ± 标准差 | %.1f ± %.1f | %.2f ± %.2f | **%.2f ± %.2f** | %.2f ± %.2f | %.2f ± %.2f |" % (
    F["none"]["summary"]["mean"], F["none"]["summary"]["sd"],
    F["rule16"]["summary"]["mean"], F["rule16"]["summary"]["sd"],
    F["rule18"]["summary"]["mean"], F["rule18"]["summary"]["sd"],
    F["rule20"]["summary"]["mean"], F["rule20"]["summary"]["sd"],
    F["oracle"]["summary"]["mean"], F["oracle"]["summary"]["sd"]))
late16 = sum(F["rule16"]["late"]) / len(F["rule16"]["late"])
nl = F["none"]["late"]
rows.append("| 晚切换占比 | %.1f–%.1f%%（均值 %.1f%%） | %.2f%% | 0.00%% | 0.00%% | 0.00%% |" % (
    min(nl), max(nl), sum(nl) / len(nl), late16))
C1 = ("**表 C1. 冻结策略因子化（campaign 检查点），极区 HSR（%）逐种子（|lat| ≥ 70°、traffic seed 0、共同回合，"
      "n = 10 个策略种子）。无盾列为施加任何约束之前的同一批十个检查点；τ = 18 s 列为部署阈值，"
      "oracle 列在每个种子上与它重合。**\n\n" + "\n".join(rows) + "\n")
t = t[:i] + C1 + t[j:]
t = t.replace("**表 C3. 逐种子漂移响应", "**表 C2. 逐种子漂移响应", 1)
t = t.replace("| 漂移响应（表 V，表 C3） |", "| 漂移响应（表 V，表 C2） |", 1)
t = t.replace("（表 V，表 C3）", "（表 V，表 C2）")
done.append("C1-merge")

# ---- D1A/D1B reshape -----------------------------------------------------
for tag in ("表 D1A.", "表 D1B."):
    a = t.find("**" + tag)
    b = t.find("\n\n", t.find("| 合计 |", a))
    if a < 0 or b < 0:
        print("  skip", tag)
        continue
    block = t[a:b]
    out, head_done = [], False
    for ln in [x for x in block.splitlines() if x.strip()]:
        if not ln.startswith("|"):
            out.append(ln)
            continue
        cells = [c.strip() for c in ln.strip().strip("|").split("|")]
        if set("".join(cells)) <= set("- "):
            out.append("| --- | --- | --- | --- |")
            continue
        if not head_done:
            out.append("| 提前量桶（s） | 尝试数 | 精确 + 删失 + 竞争 = 尝试数 | 占比 |")
            head_done = True
            continue
        if len(cells) < 6:
            continue
        try:
            att = int(cells[1].replace(",", ""))
        except ValueError:
            continue
        exc, cen, comp = (int(c.replace(",", "")) for c in cells[2:5])
        if cells[0].startswith("合计"):
            out.append(f"| **合计** | **{att:,}** | {exc:,} + {cen:,} + {comp:,} = {att:,} | **100%** |")
        else:
            out.append(f"| {cells[0]} | {att:,} | {exc:,} + {cen:,} + {comp:,} = {att:,} | {cells[5]} |")
    t = t[:a] + "\n".join(out) + t[b:]
done.append("D1")

# ---- equations -----------------------------------------------------------
pairs = [
    ("success   ⇔   route  ∧  a ≥ T_z  ∧  a ≤ V_z  ∧  elevation ≥ mask,                    (1)",
     "success  iff  route  and  a ≥ T_z\n         and  a ≤ V_z  and  elevation ≥ mask.                            (1)"),
    ("P_D( late under Π_τ ) = P_D( T_z > max(a, τ) ) ≤ P_D( T_z > τ ) ≤ ε,             (3)",
     "P_D( late under Π_τ ) = P_D( T_z > max(a, τ) )\n                      ≤ P_D( T_z > τ ) ≤ ε.                              (3)"),
]
for old, new in pairs:
    if t.count(old) == 1:
        t = t.replace(old, new, 1)
        done.append(old[:12])

# ---- kappa row -----------------------------------------------------------
i = t.find("| 机械（schema） |")
if i > 0:
    j = t.find("\n", i)
    t = t[:i] + "| 机械（schema） | 20/20 | 1.00 | 未定义（—） |" + t[j:]
    done.append("kappa")

z.write_text(t, encoding="utf-8")
print("applied:", done)
