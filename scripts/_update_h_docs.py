"""Update EVIDENCE_PACKAGE (A22-A24, rewrite A5/A20) and CLAIMS_DELTA for Phase H."""
from pathlib import Path

EP = Path(r"docs/EVIDENCE_PACKAGE.md")
t = EP.read_text(encoding="utf-8")

a5_old = ("| A5 | 主动探测+等渗**能跟随物理**且不误伤 | ref 0 损失（93.4=93.4）；"
          "+2 s 场景 +3.3 pp（90.4 vs 87.0） | E8，`campaign_pcs3_*` | 探测噪声（5 seed 中 1 个仍给 16） |")
a5_new = ("| A5 | 探测+等渗**能跟随物理**，但**必须在部署策略上探测**；"
          "朴素 in-loop 探测（早期策略）逐 seed 失败率 2/5（G4），改为部署后探测 + m=2 后 5/5 到天花板（H2） | "
          "ref 0 损失；sig32 +3.3 pp；H2 的 m=2：ref 94.0 / sig32 93.9 / drift 93.9 | E8 + G4 + H2，"
          "`campaign_pcs3_*`、`routeA_g4/`、`routeA_h2/` | 早期策略探测是根因，episode 数不是（G4 已证） |")

a20_old_prefix = "| **A20** |"
# replace A20 row wholesale
import re

lines = t.splitlines()
out = []
for ln in lines:
    if ln.startswith("| A5 |"):
        out.append(a5_new)
    elif ln.startswith("| **A20** |"):
        out.append("| **A20**（已降级） | **奖励注入的知识在漂移下退回无知水平**：+2 s 下 55.4 vs 无知识 58.1"
                   " | 标称 84.4（+5.5 pp），漂移后 −2.7 pp（逐 seed sd 17.9）；分布**更宽**（sd 4.01）而非更窄 | "
                   "H1，`routeA/h1_advance_dist.json` | 原\"−29 pp 是最脆弱形态\"的说法**已删除** |")
    else:
        out.append(ln)
t = "\n".join(out) + "\n"

add = """
| **A22** | **惩罚脆弱性的机制被证伪**：λ=8 的提前量分布**更宽**（sd 4.01 vs 3.06）、均值更高（10.21 vs 9.54 s），不是被压窄 | 漂移下 55.4 vs 58.1（−2.7 pp，sd 17.9）≈ 无知 | H1，`routeA_h1/` | 该臂标称 +5.5 pp，漂移后归零 |
| **A23** | **保守校准**：探测部署策略 + m=2 是最小可用余量，无 seed 回退 | ref 93.4→94.0、sig32 93.4→93.9、drift 93.9→93.9；m=4 不更优 | H2，`routeA_h2/` | 余量是保险不是收益；收益仅 0.5–0.6 pp |
| **A24** | **5 seeds 的漂移曲线**：+3.2 s 起常数 89.0±2.1，校准 93.9±0.7；+4.4 s 为 87.7±2.7 vs 93.3±1.4 | 拐点稳定在 +2…+3.2 s | H3，`routeA_g3/`+`routeA_h3/` | seed4 在 +4.4 处探测低一档（91.1） |
"""
marker = "| **A21** |"
if "A22" not in t:
    idx = t.find(marker)
    end = t.find("\n", idx)
    t = t[:end + 1] + add.strip("\n") + "\n" + t[end + 1:]
t = t.replace("python scripts/_routeA_g_summarise.py",
              "python scripts/_routeA_g_summarise.py\n\n# Phase H 追加（A22–A24）\n"
              "python scripts/_routeA_h1.py\npython scripts/_routeA_h2.py\n"
              "python scripts/_routeA_g3.py --seeds 3,4 --out-dir routeA_h3 --table h3_drift_table_s34.json", 1)
EP.write_text(t, encoding="utf-8")
print("EVIDENCE_PACKAGE updated")

CD = Path(r"docs/CLAIMS_DELTA.md")
c = CD.read_text(encoding="utf-8")
c = c.replace(
    "| A5 | 探测+等渗**平均而言**跟随物理，标称下 0 损失 | ref 93.4；sig32 +3.3 pp | **中**：逐 seed 2/5 会偏低（A21） |",
    "| A5 | 探测+等渗**在部署策略上**跟随物理；加 m=2 余量后 5/5 到天花板 | ref 94.0 / sig32 93.9 / drift 93.9；朴素 in-loop 探测 2/5 失败 | **强**（H2；早期策略探测是根因） |")
c = c.replace(
    "| 新 A20 | **烤进权重对漂移最脆弱** | −29.0 pp vs 常数 −0.6 / PCS −1.8 / LLM 规则 −6.6 | 强（10 seeds） |",
    "| 新 A20（已降级） | **奖励注入不换来任何漂移鲁棒性**：漂移后回到无知水平（55.4 vs 58.1）；且其分布更宽，\"被压窄\"的机制假设已被证伪 | −29 pp 的绝对值 vs 常数 −0.6 / PCS −1.8 | 强（10 seeds + 分布测量） |")
if "H1 已证伪" not in c:
    c += ("\n\n## 5. Phase H 的两处修订（定稿）\n\n"
          "1. **A5/PCS 的最终形态**：探测必须在**部署策略**上做（G4 的 2/5 失败源于早期策略探测，"
          "不是 episode 太少），再取余量 m=2。朴素 PCS 的失败率成为对照（H2）。\n"
          "2. **A20 降级**：H1 已证伪\"分布被压窄\"的机制；可写的只有\"奖励注入不带来漂移鲁棒性\"，"
          "\"最脆弱形态\"的说法删除。\n")
CD.write_text(c, encoding="utf-8")
print("CLAIMS_DELTA updated")
