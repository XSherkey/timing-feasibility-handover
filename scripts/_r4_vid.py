"""R4 (v16) part 6: rewrite the Section VI-D paragraph to match the rebuilt Table IV."""
from __future__ import annotations

from pathlib import Path

D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"

NEW = (
    "The tuned constant is the strongest objection to this work, and it deserves a subsection. "
    "\"Highest-elevation candidate, fixed 18 s lead\" matches the deployed algorithm at nominal physics "
    "(93.33% against 93.36% with the shield, and 93.36% for the \"highest-elevation candidate, fixed lead\" "
    "policy itself, Table IV). Its limitation is that *18* is a fact about the physics at tuning time, not a "
    "fact the rule can re-derive. We stress the acquisition path with δ ∈ {0, +2, +3.2, +4.4} s of additional "
    "signalling latency and re-evaluate ten policy seeds per point (Table IV). The constant carries ≈2 s of "
    "margin: at +2 s it loses 0.9 pp (92.39 against 93.20 for the same controller re-probed), at +3.2 s it "
    "loses 7.3 pp (85.98), and at +4.4 s it loses 9.6 pp (83.56). Probe calibration, which re-measures the "
    "requirement under each physics (τ∗ = 16/18/20/22 s) and adds the same 2 s margin, holds 93.20% in all "
    "three drifted regimes—it is flat where the constant collapses. The shielded policies show the same "
    "pattern one grid step higher in absolute terms (93.36 → 83.47 fixed, 93.23 re-probed). On the "
    "second-round drift ladder of Fig. 8 (five seeds per point, identical episodes across arms) the same "
    "comparison at nominal and +2 s physics reads: no knowledge (74.5 → 54.6), reward λ = 8 (84.4 → 55.4), "
    "the LLM's narrative-inferred 16 s rule (92.5 → 85.1, because its magnitude does not track), the tuned "
    "18 s constant (93.3 → 92.4), the deployed probe-calibrated τ_used = 18 s shield (93.4 → 92.5), and the "
    "per-attempt oracle (93.4 → 93.4). Only the re-measurable shields start high and stay there."
)

p = D / "paper_en.md"
t = p.read_text(encoding="utf-8")
i = t.find("The tuned constant is the strongest objection")
j = t.find("\n\n", t.find("start high and stay there.", i))
if i < 0 or j < 0:
    raise SystemExit("VI-D paragraph not found")
t = t[:i] + NEW + t[j:]
p.write_text(t, encoding="utf-8")
print("EN VI-D rewritten")

ZH_NEW = (
    "调好的常数是本文最强的反对意见，值得单列一节。\"最高仰角候选 + 固定 18 s 提前量\"在标称物理下与部署算法持平"
    "（93.33% 对带盾的 93.36%；该控制器本身为 93.36%，见表 IV）。它的局限在于：*18* 是调参时刻物理的事实，"
    "而不是规则能重新推导的事实。我们对建链路经施加 δ ∈ {0, +2, +3.2, +4.4} s 的额外信令时延，并逐点重评十个策略种子（表 IV）。"
    "该常数约有 2 s 的余量：+2 s 时损失 0.9 pp（92.39，而同一控制器重探后为 93.20），+3.2 s 时损失 7.3 pp（85.98），"
    "+4.4 s 时损失 9.6 pp（83.56）。探测标定在每个物理档位下重新测量需求（τ∗ = 16/18/20/22 s）并加上同样的 2 s 余量，"
    "在三个漂移档位上都守住 93.20%——常数崩溃之处它是平的。带盾策略呈同一模式，只是绝对值高一个网格步"
    "（固定 93.36 → 83.47，重探 93.23）。图 8 的第二轮漂移阶梯（每点五个种子、各臂回合相同）在标称与 +2 s 下读数为："
    "无知识（74.5 → 54.6）、奖励 λ = 8（84.4 → 55.4）、LLM 叙事推断的 16 s 规则（92.5 → 85.1，因为其幅值不跟随物理）、"
    "调好的 18 s 常数（93.3 → 92.4）、部署的探测标定 τ_used = 18 s 盾（93.4 → 92.5）、逐尝试 oracle（93.4 → 93.4）。"
    "只有可重新测量的盾起点高且留得住。"
)

z = D / "paper_zh.md"
s = z.read_text(encoding="utf-8")
i = s.find("调好的常数是本文最强的反对意见")
j = s.find("\n\n", s.find("留得住。", i))
if i < 0 or j < 0:
    print("ZH paragraph not found; skipping")
else:
    s = s[:i] + ZH_NEW + s[j:]
    z.write_text(s, encoding="utf-8")
    print("ZH VI-D rewritten")
