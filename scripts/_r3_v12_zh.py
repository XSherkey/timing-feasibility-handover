"""v12 ZH sync: n = 10 cross-intent and the annotation table."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / "almond-repro"
D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"
p = D / "paper_zh.md"
t = p.read_text(encoding="utf-8")
ci = json.loads((ROOT / "results" / "routeA_r3" / "cross_intent" / "summary.json").read_text(encoding="utf-8"))
pi = ci["per_intent"]
done = []

# Table V
start = t.find("**表 V.")
end = t.find("\n\n", t.find("|", start))
rows = ["| 知识图谱 | 意图 0 可靠性 | 意图 1 时延 | 意图 2 功耗 | 意图 3 平衡 | n |",
        "|---|---|---|---|---|---|",
        "| 共享（继承） | %.2f | **%.2f** | **%.2f** | **%.2f** | %d |" % (
            pi["reliability_first"]["shared"]["mean"], pi["latency_first"]["shared"]["mean"],
            pi["power_first"]["shared"]["mean"], pi["balanced"]["shared"]["mean"], len(ci["seeds"])),
        "| 每意图新建 | %.2f | %.2f | %.2f | %.2f | %d |" % (
            pi["reliability_first"]["fresh"]["mean"], pi["latency_first"]["fresh"]["mean"],
            pi["power_first"]["fresh"]["mean"], pi["balanced"]["fresh"]["mean"], len(ci["seeds"])),
        "| 转移增益（pp） | +%.2f | +%.2f | +%.2f | +%.2f | |" % (
            pi["reliability_first"]["pair"]["mean_diff"], pi["latency_first"]["pair"]["mean_diff"],
            pi["power_first"]["pair"]["mean_diff"], pi["balanced"]["pair"]["mean_diff"])]
t = t[:start] + ("**表 V. 跨意图转移（极区 HSR，|lat| ≥ 70°，%d 个策略种子取均值；其中 %d 个在意图 0 提交了规则，"
                 "表内包含全部种子，未提交的种子在两臂中贡献相同）。**\n\n"
                 % (len(ci["seeds"]), ci["committed"]["n"]) + "\n".join(rows) + "\n") + t[end:]
done.append("Table V")

# VI-F
s = t.find("### F. 一条约束，四种意图")
e = t.find("### G.", s)
NEWF = """### F. 一条约束，四种意图

在可靠性优先意图下挖掘的约束，被三个**禁止挖掘**的后续意图（时延优先、功耗优先、平衡）继承。共享图谱下三者分别达到 90.21%、89.99%、90.75%；每意图新建图谱下只有 72.19%、68.22%、69.85%。增益为 +18.02、+21.77、+20.91 pp，十个训练种子上精确双侧 Wilcoxon p = 0.0039（表 V），而两臂中完全相同的第一意图只差 0.03 pp（p = 1.00），理当如此。效应之大源于可行性是意图无关的。

两点限定必须与这个数字同时给出。**第一，发现并不总是提交。** 十个种子中有一个的发现流水线没有返回任何被提交的规则（门未准入任何候选），该种子上两臂都掉到 72–76%；我们如实报告而不剔除它，因为这正是一个自动流水线的真实失败率（9/10 提交）。**第二，** 未提交的种子在两臂中贡献相同，因此它稀释对比而不是使其有偏。

"""
t = t[:s] + NEWF + t[e:]
done.append("VI-F")

# VI-L annotation paragraph
old = "二十条 P1 回答全部通过 schema 校验，且被独立标注者判定为语义有效，因此标注者间系数是**未定义**而非很高：零分歧、零方差时 Cohen's κ 的分母为零。我们报告原始一致率（20/20）并说明这一退化，而不是给出一个没有意义的 κ。"
new = """二十条 P1 回答全部通过 schema 校验：每个谓词都只用已声明字段、效果可执行，因此机械规则接受 20/20（表 IX）。但语法合法不等于可部署，两个针对"可部署性"的标注既与机械规则不一致，彼此也不一致。一位领域标注者按书面规则（附录 E）判定 20 条中 4 条可直接部署、16 条需修改，典型原因是作用域漏掉了部分证据（用 `plane_change` 或仰角守卫只覆盖一半失败），或全局作用域会在没有失败的区域抬高提前量。第二位标注者只回答"运维能否原样部署"，接受 2/20。两次操作性标注之间的 Cohen's κ 为 0.23（原始一致率 0.80），而与机械规则的 κ 为 0（该规则无方差）。有价值的读数是这个差距而不是任何单一比率：**每条**提案都语法正确，**五分之一**无需修改即可部署，而两位标注者在存在分歧的五条中只对四条达成一致。这正是流水线所假设的分工——模型是提案生成器，决定什么能触碰网络的是审计门，不是模型。

**表 IX. 二十条提案的标注。** 机械：谓词使用已声明字段且有可执行效果。可部署（作者）：规则可原样部署。可部署（第二标注者）：独立的操作性判断。κ 基于"可部署"这一二值结果。

| 标注者 | 接受 | 比率 | κ（对作者） |
|---|---|---|---|
| 机械（schema） | 20/20 | 1.00 | 0.00 |
| 作者（操作规则） | 4/20 | 0.20 | — |
| 第二标注者（操作性） | 2/20 | 0.10 | 0.23 |
| 原始一致率（作者 vs 第二） | — | 0.80 | — |
"""
if t.count(old) != 1:
    raise SystemExit(f"VI-L anchor found {t.count(old)}")
t = t.replace(old, new, 1)
done.append("VI-L")

p.write_text(t, encoding="utf-8")
print("applied:", done)
