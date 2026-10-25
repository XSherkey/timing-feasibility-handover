"""R3 (v11) ZH sync: Table V, VI-F prose, the LLM subsection and Appendix E."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / "almond-repro"
D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"
p = D / "paper_zh.md"
t = p.read_text(encoding="utf-8")
ci = json.loads((ROOT / "results" / "routeA_r3" / "cross_intent" / "summary.json").read_text(encoding="utf-8"))
llm = json.loads((ROOT / "results" / "routeA_r3" / "llm_proposals" / "summary.json").read_text(encoding="utf-8"))
pi = ci["per_intent"]
done = []

# ---- Table V -------------------------------------------------------------
start = t.find("**表 V.")
end = t.find("\n\n", t.find("|", start))
if start < 0:
    raise SystemExit("Table V ZH not found")
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
            pi["power_first"]["pair"]["mean_diff"], pi["balanced"]["pair"]["mean_diff"]),
        "| 精确 Wilcoxon p | %.4f | %.4f | %.4f | %.4f | |" % tuple(
            (pi[k]["pair"]["wilcoxon_p"] or 1.0) for k in
            ("reliability_first", "latency_first", "power_first", "balanced"))]
new = ("**表 V. 跨意图转移（极区 HSR，|lat| ≥ 70°，按策略种子取均值；八个训练种子中有 %d 个在意图 0 提交了规则，"
       "未提交的种子在两臂中贡献相同）。**\n\n" % ci["committed"]["n"] + "\n".join(rows) + "\n")
t = t[:start] + new + t[end:]
done.append("Table V")

# ---- VI-F prose ----------------------------------------------------------
s = t.find("### F. 一条约束，四种意图")
e = t.find("### G.", s)
NEWF = """### F. 一条约束，四种意图

在可靠性优先意图下挖掘的约束，被三个**禁止挖掘**的后续意图（时延优先、功耗优先、平衡）继承。共享图谱下三者分别达到 89.59%、89.41%、90.33%；每意图新建图谱下只有 76.53%、71.60%、75.28%。增益为 +13.06、+17.81、+15.05 pp，八个训练种子上精确双侧 Wilcoxon p = 0.0156（表 V），而两臂中完全相同的第一意图只差 0.04 pp（p = 1.00），理当如此。效应之大源于可行性是意图无关的：无论下一个目标是什么，该约束移除的是同一个失效类。

两点限定必须与这个数字同时给出。**第一，发现并不总是提交。** 八个种子中有一个的发现流水线没有返回任何被提交的规则（门未准入任何候选），该种子上两臂都掉到 72–76%；我们如实报告而不剔除它，因为这正是一个自动流水线的真实失败率（7/8 提交）。**第二，** 未提交的种子在两臂中贡献相同，因此它稀释对比而不是使其有偏。

"""
t = t[:s] + NEWF + t[e:]
done.append("VI-F")

# ---- LLM subsection ------------------------------------------------------
S = t.find("### L. 局限性")
LLM = f"""### L. 语言模型究竟提出了什么

既然隔离实验把语言模型降为"发现自动化"，它自身的质量就必须被测出来而不是被断言。我们把二十条**仅来自训练窗口**的失败叙事送入最终 prompt 的两个变体：P1 只要求谓词，P2 要求谓词**与**幅值并附一句理由。所有回答原文保存在附录 E，并用流水线本身的同一 schema 校验。

二十条 P1 回答全部通过 schema 校验，且被独立标注者判定为语义有效，因此标注者间系数是**未定义**而非很高：零分歧、零方差时 Cohen's κ 的分母为零。我们报告原始一致率（20/20）并说明这一退化，而不是给出一个没有意义的 κ。

幅值才是有信息量的部分。在标称物理下需求为 16 s，模型给出的均值是 {llm['magnitude']['mean']:.1f} s——系统性偏短；把同一批叙事中所有建链时间整体 +2 s 后重发，{llm['magnitude']['n_pairs']} 条中有 {llm['magnitude']['unchanged_under_2s_drift']} 条（{100 * llm['magnitude']['share_unchanged']:.0f}%）的幅值**完全不动**。一个对它所描述的物理毫无反应的量，不可能是部署幅值——这正是流水线只从模型取谓词、而在孪生上测量幅值的原因。这是第五节 B 那个拆分动机的定量版本。

"""
t = t[:S] + LLM + t[S:]
done.append("LLM section")

# ---- Appendix E ----------------------------------------------------------
t = t.replace("## 参考文献", "## 附录 E. Prompt 与原始输出\n\n本研究所用 prompt 见英文稿附录 E 与 `results/routeA_r3/llm_proposals/prompt_examples.md`（三条完整 prompt/输出对）以及 `proposals.csv`（全部二十条，含两种变体的原始 JSON）。\n\n## 参考文献", 1)
done.append("Appendix E")

p.write_text(t, encoding="utf-8")
print("applied:", done)
