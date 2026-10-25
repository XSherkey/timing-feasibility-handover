# WRITING_TODO — 交稿前必须处理（Route A 论文 v1）

> 2026-10-24。写作阶段产出：`main.md`（带 `[A##]` 溯源标记的内部稿）、
> `main.tex`（IEEEtran 投稿稿，已去标记）、`figures/`（7 图）。
> 本文件只列**必须由人或补实验解决**的缺口；能在写作层修的不在此列。

## P0（不解决不能投）

1. **参考文献未核实。** 40 条 `\bibitem` 中约 15 条沿用旧稿（Lira/Huang/Kou/Xie/Ma/Zhou/Shinn/
   Cai/Nasir/Farajzadeh/Liang/Mao/Paul/Fourati/Zhu 等），其余为按主题补齐的占位条目
   （部分年份/卷期待核，个别条目作者为占位）。**投稿前必须逐条核对 DOI 或删除**。
   建议：保留 25–30 条已核实的，宁少勿假。
2. **LaTeX 未在本机编译。** 本机无 TeX 发行版（pdflatex/xelatex/latexmk 均不存在）。
   需在有 TeX 的环境编译一次，检查：图表浮动位置、`\columnwidth` 图宽、
   Table III 的 9 列宽度、参考文献与引用的 `\cite` 一致性（当前正文尚未插入 `\cite`，需补）。
3. **正文没有 `\cite`。** `main.tex` 的 Related Work 用叙述代替引用，投稿版必须在每处
   claim 后插入 `\cite{...}`（约 40 处）。
4. **作者/单位/基金/利益冲突** 均为占位（Anonymous Authors）。

## P1（审稿人会抓）

5. **图 2 的 "91.8"**：该值是 ppomlp + 16 s 盾（common-episode factorial），
   与 "72.6（campaign PPO-MLP）" 不同源。图注已写 "on PPO-MLP"，但两臂的 seed 协议不同，
   建议在图注补一句"evaluated on common episodes"。
6. **S 指标的归一化常数**（150 ms SLA、20 ms floor、功率上下界）沿用旧稿描述，
   需对照 `almond/analysis/metrics.py` 再核一次（写作时未读代码）。
7. **"exploration is not the issue"** 是论证（命题 2）而非实验。若审稿人要求，
   需补一个"加大探索/熵系数"的对照（约 30 min 机器时间，10 seeds）。
8. **LLM 型号与版本**：正文只写 "a hosted instruction-tuned model"。投稿版应写明
   模型名/版本/温度/提示词长度，并把提示词放附录（旧稿 Appendix A 可复用）。
9. **E17 经济学边界**（"提前准备近乎免费"）只在 Limitations 第 6 条出现，没有对应表。
   要么在附录加一张 τ–成本表，要么把该条降为"本孪生的经济学假设"一句。

## P2（打磨）

10. 标题三选一尚未定稿（`docs/ROUTE_A_WRITING_PLAN.md` §2 给了三个方向）。
11. 摘要 250 词上限需核（当前约 280 词）。
12. 图 1 的 `\Pi_\tau` 与正文符号一致；图 3 的图注需说明"common episodes"。
13. 术语表统一：正文已统一用 feasibility / selection quality / decision shield / probe /
    margin / audit gate / knowledge graph；旧稿的 "self-improving"、"self-auditing" 已全部删除。
14. 附录 A 的命令需与实际仓库路径一致（当前为 `scripts/...` 相对路径）。

## 已完成（无需再动）

- 数字溯源：`scripts/check_paper_numbers.py` 抽样 33 个数字，**0 处不一致**。
- `[A##]` 标记只存在于 `main.md`（内部稿），`main.tex` 为 0，符合计划 §8.1。
- 五条 Limitations 全部写入（§VI-H，6 条，多于计划要求的 5 条）。
- 两条负面结果（H1 机制证伪、G4 的 8-episode 反效果）均写入正文，未藏。
- 7 张图全部由 `scripts/paper_figures.py` 从封版 JSON 生成，无手抄数字。
