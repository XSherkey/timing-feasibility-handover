"""Add the two missing Chinese figure captions (new Fig. 3 passive support, new Fig. 9 deployment)."""
from __future__ import annotations

from pathlib import Path

D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"
p = D / "paper_zh.md"
t = p.read_text(encoding="utf-8")

CAP3 = ("**图 3.** 被动支撑与样本预算。(a) 被动无盾日志（PPO-MLP，十个种子，|lat| ≥ 68°，8,682 次尝试）中"
        "晚切换率随提前量的变化，附二项 95% 区间与 PAVA 单调拟合；阴影为 5% 交点的簇自助 95% 区间（10–18 s）。"
        "(b) 该区间宽度随抽取尝试数的变化：按尝试独立重采样（浅色）在 1,000 次时就压到一个网格步，"
        "而按 (seed, site) 分块重采样（深色）在满预算下仍有数秒。约束来自日志的被动性，而不是它的规模。")
CAP9 = ("**图 9.** 部署视图。发现（训练窗口）、标定与准入（验证窗口）与部署是围绕版本化知识图谱的三个独立服务。"
        "盾在决策时刻读取已提交约束且不写任何东西；监控在漂移时安排重新探测，回滚恢复上一个已提交版本。"
        "接口与失败路径见第六节 K。")

added = []
if "**图 3.** 被动支撑与样本预算" not in t:
    mark = "## 图注\n\n"
    i = t.find(mark)
    if i < 0:
        raise SystemExit("ZH captions heading not found")
    t = t[: i + len(mark)] + CAP3 + "\n\n" + t[i + len(mark):]
    added.append("fig3")
if "**图 9.** 部署视图" not in t:
    j = t.rfind("**图 8.**")
    if j < 0:
        j = t.rfind("**图 7.**")
    e = t.find("\n", j)
    t = t[: e + 1] + "\n" + CAP9 + "\n" + t[e + 1:]
    added.append("fig9")

p.write_text(t, encoding="utf-8")
print("added:", added)
