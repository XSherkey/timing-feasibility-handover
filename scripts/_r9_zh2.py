"""R10 part 7: the two Chinese strings with their exact wording, plus VI-A and Limitation 7."""
from __future__ import annotations

from pathlib import Path

D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"
z = D / "paper_zh.md"
s = z.read_text(encoding="utf-8")
done = []


def repz(old, new, label):
    global s
    n = s.count(old)
    if n != 1:
        print(f"  MISS [{label}] {n}: {old[:40]}")
        return
    s = s.replace(old, new, 1)
    done.append(label)


repz("部署 τ = 18 s 盾下横跨 92.7–93.7%（sd 0.26）",
     "部署 τ = 18 s 盾下横跨 93.3–93.5%（sd 0.05，表 C1）", "prop3")

repz("实测带盾后的晚切换占比为 0.9%（对 ε = 5%）",
     "实测带盾后的晚切换占比为 τ = 16 s 时的 0.93%、τ = 18 s 时的 0.00%（对 ε = 5%）", "late")

# VI-A data-flow: find the paragraph that still says three steps touch the evaluation window
i = s.find("评估窗口")
cands = [k for k in range(len(s)) if s.startswith("评估窗口", k)]
hit = -1
for k in cands:
    seg = s[k - 200:k + 260]
    if "三个" in seg or "三处" in seg or "三道" in seg:
        hit = k
        break
print("VI-A candidate at", hit, repr(s[hit - 200:hit + 260]) if hit > 0 else "")

z.write_text(s, encoding="utf-8")
print("applied:", done)
