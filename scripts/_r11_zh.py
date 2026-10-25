"""R12 part 5: fully bold the last two captions; then mirror the round's changes into Chinese."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / "almond-repro"
D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"
iso = json.loads((ROOT / "results" / "routeA_r3" / "isolation" / "summary.json").read_text(encoding="utf-8"))
gs = json.loads((ROOT / "results" / "routeA_r3" / "gate_systematic" / "summary.json").read_text(encoding="utf-8"))
lk = json.loads((ROOT / "results" / "routeA_r3" / "lockbox_consistent" / "summary.json").read_text(encoding="utf-8"))

# ---------- EN: bold the two captions --------------------------------------
p = D / "paper_en.md"
t = p.read_text(encoding="utf-8")
for start in ("**Table XII. Annotation of the twenty proposals.**", "**Table D2. The full 26-candidate gate bank.**"):
    i = t.find(start)
    if i < 0:
        continue
    j = t.find("\n\n", i)
    line = t[i:j]
    if line.endswith("**"):
        continue
    t = t[:i] + line + "**" + t[j:]
p.write_text(t, encoding="utf-8")
print("EN captions bolded")

# ---------- ZH mirror ------------------------------------------------------
z = D / "paper_zh.md"
s = z.read_text(encoding="utf-8")
done = []

PROTO = [("**表 III.", "**协议：archival（评估窗口标定）。**"),
         ("**表 IV.", "**协议：archival。**"),
         ("**表 V.", "**协议：archival。**"),
         ("**表 VI.", "**协议：archival。**"),
         ("**表 VII.", "**协议：archival。**"),
         ("**表 VIII.", "**协议：archival。**"),
         ("**表 IX.", "**协议：仅验证窗口。**")]
for key, note in PROTO:
    i = s.find(key)
    if i < 0:
        print("  no caption:", key)
        continue
    end = s.find(".**", i + 2)
    if end < 0:
        continue
    s = s[:end + 3] + " " + note + s[end + 3:]
    done.append(key)

# seeds
s = s.replace("在五种子和三个物理档位下守住天花板（图 3）", "在十个策略种子与四个档位下守住天花板（图 3）")
s = s.replace("图 8 的第二轮漂移阶梯（每点五个种子、各臂回合相同）", "图 8 的漂移阶梯（每点十个策略种子、各臂回合相同）")

# ZH Table IX: TOST column
i = s.find("| 臂 | 组件来源 |")
if i > 0:
    j = s.find("\n\n", s.find("| A8 |", i))
    if j < 0:
        j = s.find("\n\n", s.find("| A8", i))
    block = s[i:j]
    lines = block.splitlines()
    if len(lines) > 2:
        lines[0] = lines[0].rstrip(" |") + " | TOST p（margin 1.0 pp） |"
        lines[1] = lines[1] + "---|"
        for k in range(2, len(lines)):
            lines[k] = lines[k].rstrip(" |") + (" | < 0.001 |" if not lines[k].startswith("| A0") else " | — |")
        s = s[:i] + "\n".join(lines) + s[j:]
        done.append("ZH-IX")

# ZH Table X: protocol row
i = s.find("| 臂 | 评估窗口（archival）")
if i > 0:
    j = s.find("\n", s.find("|---|", i))
    s = s[:j + 1] + "| 协议 | archival | three-way | three-way | three-way |\n" + s[j + 1:]
    done.append("ZH-X")

# ZH D2 appendix
bank = gs["bank"]
rows = ["| id | 谓词 | 验证重放增益（pp） | 评估窗口效应（pp） | 门 | 标签 |", "|---|---|---|---|---|---|"]
for b in sorted(bank, key=lambda x: x["id"]):
    rows.append(f"| {b['id']} | `{b['rule']}` | {b['delta_short']:+.2f} | {b['delta_test']:+.2f} | "
                f"{'准入' if b['admit_short'] else '拒绝'} | {b['class']} |")
D2 = ("**表 D2. 完整的 26 条候选门银行。** 每条候选给出门真正使用的验证窗口重放增益、仅作事后标签的评估窗口效应、"
      "判定与标签。三条中性候选按构造被拒绝——准入要求增益高于 5 pp——因此不计入误拒；误拒只在「有害对好」这一判定上定义。**\n\n"
      + "\n".join(rows) + "\n")
anchor = "## 附录 E"
if anchor in s:
    s = s.replace(anchor, D2 + "\n" + anchor, 1)
    done.append("ZH-D2")

z.write_text(s, encoding="utf-8")
print("ZH applied:", done)
