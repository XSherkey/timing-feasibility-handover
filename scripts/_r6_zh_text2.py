"""R7 ZH part 4: the five remaining strings with corrected anchors."""
from __future__ import annotations

from pathlib import Path

D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"
z = D / "paper_zh.md"
t = z.read_text(encoding="utf-8")
done = []


def rep(old, new, label):
    global t
    n = t.count(old)
    if n != 1:
        print(f"  MISS [{label}] {n}")
        return
    t = t.replace(old, new, 1)
    done.append(label)


rep("**τ\\*** 为 p(a) 首次低于", "**τ∗** 为 p(a) 首次低于", "nomen-tau")
rep("而与机械规则的 κ 为 0（该规则无方差）",
    "而与机械规则的 κ 是*未定义*而非 0（该规则准入每一条提案，没有方差）", "kappa")
rep("A8 复现到 0.02 pp", "A8 复现到 0.03 pp", "a8")
rep("被动日志从不触及", "被动日志覆盖得太薄、无法辨识", "never", count=2) if t.count("被动日志从不触及") == 2 else None
if t.count("被动日志从不触及") == 2:
    t = t.replace("被动日志从不触及", "被动日志覆盖得太薄、无法辨识")
    done.append("never")
elif t.count("被动日志从不触及") == 1:
    t = t.replace("被动日志从不触及", "被动日志覆盖得太薄、无法辨识", 1)
    done.append("never")
else:
    print("  never count", t.count("被动日志从不触及"))

z.write_text(t, encoding="utf-8")
print("applied:", done)
