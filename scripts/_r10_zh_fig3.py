"""R11 part 7: the Chinese Fig. 3 caption (drift), and the Fig. 1 citation for ordering."""
from __future__ import annotations

import json
from pathlib import Path

D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"
ROOT = Path(__file__).resolve().parents[2] / "almond-repro"
dm = json.loads((ROOT / "results" / "routeA_r3" / "drift_margin" / "summary.json").read_text(encoding="utf-8"))
R = dm["regimes"]
fx = [R[r]["arms"]["const_fixed18"]["summary"]["mean"] for r in ("1.2", "3.2", "4.4", "5.6")]
rp = [R[r]["arms"]["const_probed"]["summary"]["mean"] for r in ("1.2", "3.2", "4.4", "5.6")]

z = D / "paper_zh.md"
t = z.read_text(encoding="utf-8")
i = t.find("**图 3.** 奖励注入是剂量-反应")
if i < 0:
    raise SystemExit("ZH Fig. 3 caption not found")
j = t.find("\n\n", i)
CAP = (f"**图 3.** 调好常数的失效边界，以及重新探测买到了什么。极区 HSR 对额外建链时延（campaign 策略、traffic seed 0、"
       f"n = 10 个策略种子，阴影为 ±sd）：固定 18 s 常数（红）在 δ = 0/+2/+3.2/+4.4 s 下读数为 "
       + " / ".join("%.2f" % v for v in fx) + f"，即约 2 s 漂移内稳得住，之后在 +3.2 s 掉 "
       f"{fx[0] - fx[2]:.1f} pp、+4.4 s 掉 {fx[0] - fx[3]:.1f} pp；同一控制器在每个物理档位重探阈值"
       f"（蓝，τ∗ = 16/18/20/22 s 加 2 s 余量）读数为 " + " / ".join("%.2f" % v for v in rp) +
       "。常数在标称物理下并不弱，它只是**固定**的——固定阈值是调参时刻物理的事实。**")
t = t[:i] + CAP + t[j:]

old = "我们主张的贡献是一个**审计与标定协议**"
if t.count(old) == 1:
    new = ("使这一切可测量的流水线见图 1：删失失败日志进入 Kaplan–Meier 恢复，语言模型只提出谓词，"
           "探测在部署策略上测量幅值，得到的约束经准入门在决策时刻注入。我们主张的贡献是一个**审计与标定协议**")
    t = t.replace(old, new, 1)
z.write_text(t, encoding="utf-8")
print("ZH Fig. 3 caption restored; Fig. 1 cited")
