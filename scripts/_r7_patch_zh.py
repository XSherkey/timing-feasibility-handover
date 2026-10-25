"""R7 (v9) ZH: drop the revision note, compress the abstract, fix the residual wording."""
from __future__ import annotations

from pathlib import Path

P = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本" / "paper_zh.md"
t = P.read_text(encoding="utf-8")
done = []

i = t.find("**稿件 v")
if i < 0:
    raise SystemExit("banner not found")
j = t.find("\n", i)
t = t[:i] + t[j + 1:]
while t.startswith("\n"):
    t = t[1:]
done.append("banner-removed")

a = t.find("## 摘要")
b = t.find("**关键词", a)
if a < 0 or b < 0:
    raise SystemExit("abstract bounds")
ABSTRACT = """## 摘要

低轨星座的切换可靠性通常被当作强化学习（RL）问题处理，近期系统报告了把 RL 与大语言模型（LLM）耦合所带来的巨大增益。本文忠实复现其中一个系统，并审计其增益究竟由什么构成。在 350 颗卫星的数字孪生上，单条计时约束几乎解释了全部已报道的改进：把该下界施加到**冻结**权重、在相同回合上评分，极区切换成功率从 67.5% ± 13.2% 提升到挖掘下界的 92.4% ± 0.3% 与部署下界的 93.3% ± 0.3%；而没有它时，十个检查点散布于 49.8–90.0%，两个策略族无法区分。原因具有结构性：被动日志对信息带的覆盖很薄——8,682 次尝试中仅 705 次（8.1%）落在 14–16 s 带，而众数桶占 37.7%——因此在任何付得起的预算下，该下界实际上不可识别：这是给定样本预算下的有效支撑失败，而不是信息论意义上的不可能。因此我们把这类的知识从奖励层移到决策层：LLM 只提出约束的**谓词**，绝不给出幅值；幅值由在部署策略上执行的探测确定，代价不对称的余量吸收残余平台，反事实审计门只在回放之后准入候选。边界如实陈述：调好的常数在标称物理下与系统持平，但在 3.2 s 建链漂移下损失 6–7 个百分点；五种子门槛研究只是描述性的；lockbox 冻结选择，而不是重新选择。

"""
t = t[:a] + ABSTRACT + t[b:]
done.append("abstract")

old = "因此结果数据最具信息量的区域——需求两侧——几乎从未被试探；任何估计器，无论同一日志过程提供多少数据，都无法识别输入从未到达之处的量（命题 2）。"
new = "因此结果数据最具信息量的区域——需求正下方——覆盖显著偏薄（被动日志中 8.1% 对众数桶 37.7%）；在任何付得起的样本预算下，该处的有效支撑不足，交点实际上不可识别——这是有效支撑失败，而非信息论意义上的永久不可能（命题 2）。"
if t.count(old) == 1:
    t = t.replace(old, new, 1)
    done.append("intro-strong")
else:
    print("intro-strong MISSING")

old = "极区平均提前量约 9.5–11.3 s，而需求为 16 s"
new = "极区平均提前量约 9.5–11.3 s（该数字取自 |lat| ≥ 70° 的混合 campaign；下面使用的被动无盾日志为 |lat| ≥ 68°，均值 9.09 s），而需求为 16 s"
if t.count(old) == 1:
    t = t.replace(old, new, 1)
    done.append("band-clarify")

old = "全系统臂 92.43）"
if t.count(old) == 1:
    t = t.replace(old, "挖出规则臂 92.43）", 1)
    done.append("fig2-arm")

old = "在标称物理下与全系统持平（94.0% ± 0.7% 对 93.6% ± 0.7%）"
if t.count(old) == 1:
    t = t.replace(old, "在标称物理下与挖出规则 campaign 臂持平（94.0% ± 0.7% 对 93.6% ± 0.7%）", 1)
    done.append("tuned-arm")

old = "该常数约有 2 s 的安全余量"
if t.count(old) == 1:
    t = t.replace(old, "该常数约有 2 s 的安全余量", 1)

P.write_text(t, encoding="utf-8")
print("applied:", done)
