"""T1-05 — remove review-response meta-commentary from the Chinese manuscript."""
from __future__ import annotations

from pathlib import Path

P = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本" / "paper_zh.md"
t = P.read_text(encoding="utf-8")
done = []


def rep(old: str, new: str, label: str) -> None:
    global t
    n = t.count(old)
    if n != 1:
        raise SystemExit(f"[{label}] expected 1, found {n}")
    t = t.replace(old, new, 1)
    done.append(label)


rep("这里必须区分两个网格点，因为上一版把它们混为一谈：", "这里必须区分两个网格点：", "corollary")
rep("上一版写作\"尝试恰在 T_z > τ 时晚切换\"，那是错的。", "", "prop3-proof")
rep("上一版写作\"三条有害\"，实际是四条。若无回放阶段", "若无回放阶段", "gate-count")
rep("检验四条排序，每条都给出显式配对，因为上一版留有歧义：", "检验四条排序，每条都给出显式配对：", "orderings")
rep("上一版把后者称作「带盾全系统对带盾 PPO-MLP」，因两臂阈值不同而有歧义。",
    "后一对比较的两臂阈值不同，回答的是另一个问题。", "pairing")
rep("故容差为 **≤ 1.20 pp**（上一版写作\"1 pp 以内\"，数字并不支持）。", "故容差为 **≤ 1.20 pp**。", "tolerance")
rep("我们用一张表陈述这一点，因为早期版本曾试图调和一个不成立的等式，审稿人正确地指出了它。",
    "我们用一张表陈述这一点，因为散文容易写下一个并不成立的等式。", "ledger-intro")
rep("并且**把两种日志体制分开报告**，因为上一版把它们合并了，审稿人正确地指出：合并后有 91% 的质量堆在 16 s。",
    "并且**把两种日志体制分开报告**，因为合并会把规则自身的签名与被动词的覆盖率混为一谈。", "appendixD")
rep("（上一版只报了合并表，91% 的质量正来自那里；本次更正把第四节 C 的百分比从\"67/22,807 ≈ 0.3%\"改为\"705/8,682 ≈ 8.1%\"，并删去了被动数据并不支持的\"两个数量级\"说法。）",
    "第四节 C 的百分比按被动面板计算（705/8,682 ≈ 8.1%），不按本表计算。", "appendixD-parenthetical")
rep("早期版本在训练循环内、第一块之后立即探测，为的并不是最终部署的策略估计阈值。",
    "在训练循环内、第一块之后立即探测，估计的并不是最终部署策略的阈值。", "probe-history")
rep("*适用范围——直白说明，因为此处极易言过其实。*", "*适用范围。*", "scope")
rep("两条后果，直白陈述。", "两条后果如下。", "consequences")
rep("\"几乎没有尝试\"这一早期版本的措辞是否成立（它不精确；计数才是精确的版本）。",
    "\"几乎没有尝试\"这一粗略措辞是否成立（它不精确；计数才是精确的版本）。", "d1-wording")

P.write_text(t, encoding="utf-8")
print("applied:", done)
