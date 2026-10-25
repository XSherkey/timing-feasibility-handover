"""R8 part 6: ZH numbers, table renumbering and the structural mirrors."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / "almond-repro"
D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"
lk = json.loads((ROOT / "results" / "routeA_r3" / "lockbox_consistent" / "summary.json").read_text(encoding="utf-8"))
dm = json.loads((ROOT / "results" / "routeA_r3" / "drift_margin" / "summary.json").read_text(encoding="utf-8"))
I = lk["instances"]
INSTS = ["eval", "lb299.25", "lb306.25", "lb290.25"]
lm = lambda i, a: I[i][a]["summary"]["mean"]
gap_mined = [lm(i, "deployed_18") - lm(i, "mined_16") for i in INSTS]
gap_ppo = [lm(i, "deployed_18") - lm(i, "ppomlp_mined_16") for i in INSTS]
loss32 = dm["regimes"]["1.2"]["arms"]["const_fixed18"]["summary"]["mean"] - dm["regimes"]["4.4"]["arms"]["const_fixed18"]["summary"]["mean"]
loss44 = dm["regimes"]["1.2"]["arms"]["const_fixed18"]["summary"]["mean"] - dm["regimes"]["5.6"]["arms"]["const_fixed18"]["summary"]["mean"]

z = D / "paper_zh.md"
t = z.read_text(encoding="utf-8")
done = []


def rep(old, new, label):
    global t
    n = t.count(old)
    if n != 1:
        print(f"  MISS [{label}] {n}: {old[:50]}")
        return
    t = t.replace(old, new, 1)
    done.append(label)


# numbers
rep("部署臂比挖掘 16 s 规则高 1.4–2.1 pp，比同规则 PPO-MLP 基线高 2.3–3.4 pp",
    f"部署臂比挖掘 16 s 规则高 {min(gap_mined):.2f}–{max(gap_mined):.2f} pp，比同规则 PPO-MLP 基线高 "
    f"{min(gap_ppo):.2f}–{max(gap_ppo):.2f} pp", "ordering")
rep("此后常数损失 6–7 pp", f"此后常数损失 {loss32:.1f}–{loss44:.1f} pp", "drift-loss")
rep("约束值奖励基线到带盾系统之间 24.0 pp 中的 23.4 pp", "约束值奖励基线到带盾系统之间 24.1 pp 中的 23.4 pp", "gap-24")

# ledger caption + renumber II..XI -> III..XII
i = t.find("| 臂（位置） |")
if i < 0:
    raise SystemExit("ZH ledger not found")
lead = t.rfind("\n\n", 0, i)
CAP = ("**表 II. 阈值台账：每个被报告的数字执行的是哪条规则（第五节 D）。** 每一行给出臂、该臂实际执行的规则，"
       "以及它标定到的阈值；正文任何位置引用的数字都可以经由这张表追溯。**\n\n")
t = t[:lead + 2] + CAP + t[lead + 2:]
done.append("ledger-caption")

order = ["XI", "X", "IX", "VIII", "VII", "VI", "V", "IV", "III", "II"]
mapping = {"II": "III", "III": "IV", "IV": "V", "V": "VI", "VI": "VII", "VII": "VIII",
           "VIII": "IX", "IX": "X", "X": "XI", "XI": "XII"}
t = t.replace("**表 II. 阈值台账", "@@LEDGER@@")
for key in order:
    t = t.replace("表 " + key, f"@@T{key}@@")
for key in order:
    t = t.replace(f"@@T{key}@@", "表 " + mapping[key])
t = t.replace("@@LEDGER@@", "**表 II. 阈值台账")
done.append("renumber")

z.write_text(t, encoding="utf-8")
print("applied:", done)
