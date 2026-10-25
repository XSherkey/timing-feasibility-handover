# 路线 A 实验工作计划 · 第三阶段（Phase H，收尾，给执行智能体的操作说明）

> 2026-10-23。Phase F/G 已完成（见 `results/routeA/SUMMARY.md`）。**这是实验阶段的最后一轮**：
> 两个小实验把残余软肋转化为论文资产，然后进入写作阶段。
> 总机时 ≤ 1.5 天。

---

## 0. 为什么还有这一轮

Phase G 留下两件事：

1. **PCS 精度软肋被 G4 暴露得更清楚**：探测阈值在 14–16 s 平台内本质不可辨识（A14），
   8 episodes 反而引入偏低偏差（A21），sig32 上 2/5 个 seed 给 16 而非 18。
   但 G4b 同时给出了关键事实：**代价严重不对称**——τ 选低一个平台点损失 4.8 pp，
   选高到 18/20/26 几乎免费（93.2–94.0 平台），直到 a_max=26 截断。
   ⇒ 这指向一个标准的决策论修法：**代价不对称下应取保守（偏高）阈值**。
   若 H2 成立，A14/A21 从"限制"改写为"动机"：正因为平台不可辨识且欠保护代价远高于过保护，
   我们才需要（并且只需）保守校准。

2. **G2b 的 −29 pp 机制还是推断**（SUMMARY §G2b 自述"待专门实验证实"），
   且 λ=8 策略在 sig32 下 55.4 低于一切对照——它到底"比无知更差"还是"只是没帮上忙"，
   必须测无知识参照臂才能下结论。审稿人必问。

H3 是可选加固。H 阶段完成后**实验封版**，开始写论文。

---

## 1. 总原则（同前两阶段）

只追加不覆盖；新产物进 `results/routeA_h*/`；命令追加进 `results/routeA/commands.log`；
验收不达标先上报；完成后 EVIDENCE_PACKAGE.md 追加 A22 起。

---

## 2. 任务 H1：惩罚脆弱性的机制实验（0.5 天，纯评估，便宜）

### 2.1 问题与假设

假设（SUMMARY §G2b 的推断）：λ=8 的惩罚把策略的提前量分布**压在阈值附近**
（学到"只要 ≥16 就不被罚"，质量集中到 16–18 s 桶），消掉了策略天然的余量；
物理一漂移，分布整体落在新的下界之下，且因为分布窄，晚切换率飙升。
对照：无知识策略的提前量分布更分散、均值更低，但它在 sig32 下也不会比"被压窄的分布"更差。

### 2.2 实验（每臂 10 seeds，纯 rollout，不训练）

从 `routeA_f3/lam8.0/no_forensics_seed*` 和 `campaign_1023/no_forensics_*` 各加载 ckpt，
在 **两种物理**（标称 / `--acq-signaling 3.2`）下跑 `eval_shield.py` 式 rollout（无盾），
记录**极区决策的提前量桶分布**（每 seed：各桶占比、均值、< 当前 τ* 的占比）与极区 HSR。

- 臂 a：`routeA_f3/lam8.0`（λ=8，知识在权重里）
- 臂 b：`campaign_1023/no_forensics`（无知识参照）——**G2b 缺的就是这个参照**

实现提示：`eval_shield.py` 的 `env.attempt_log` 已记录每次 attempt（含 cause）；
提前量桶可从 attempt 记录或动作记录恢复——先读 `almond/twin/env.py` 的 attempt_log 结构，
若不含 chosen advance，则改用 `--rule` 空跑 + 从 trainer 动作统计；
必要时给 `eval_shield.py` 加 `--dump-advance-dist OUT` flag（只加不改默认）。

### 2.3 验收标准（任一即可写，但要如实）

1. 臂 a 分布显著压窄且集中在 16 附近、臂 b 分散 → 机制坐实；
   且 sig32 下臂 b 的 HSR 显著高于臂 a（惩罚知识"比无知更差"成立，A20 是强主张）。
2. 若 sig32 下臂 b ≈ 臂 a（惩罚只是没帮上忙），A20 降级为
   "惩罚知识不带来漂移鲁棒性，且标称下远差于盾"——CLAIMS_DELTA 同步改。

交付：`results/routeA/h1_advance_dist.json`（每臂 × 每 seed × 物理的分布 + HSR）+
分布对比图。EVIDENCE_PACKAGE.md 追加 A22。

---

## 3. 任务 H2：代价不对称的保守校准（1 天，决定 PCS 最终形态）

### 3.1 设计

利用 G4b 的不对称性：给探测阈值加安全余量 m，

```
τ_used = min( τ*_probed + m,  a_max - 2 )     # a_max=26，留 2 s 防截断
```

扫描 m ∈ {0, 2, 4} × 物理 {ref, sig32, +3.2drift} × seeds 0–4，
评估臂 = 冻结策略（`campaign_1023/almond_seed*`）+ `eval_shield.py --rule "min_advance:TAU@latitude_abs_deg>=68"`，
其中 TAU 用该 (seed, 物理) 下 probe 实测的 τ*（复用 G3 的探测产物）+ m。

关键验收点：

1. **sig32 下 m=2 或 m=4 是否让 5/5 seeds 到达天花板**（即修掉 G4 的 2/5 失败）；
2. **ref 下是否仍 0 损失**（m=2 → τ=18 → G4b 显示 94.0，应略优于 16 的 93.4；m=4 → 20，93.2 持平）；
3. **+3.2 drift 下是否同样贴天花板**（τ*≈20 + m 后 ≤ 24，G3 by_lead 显示 24 仍 93.2）。

### 3.2 与 G4 的关系

- 若 H2 通过：A5/A14/A21 合并改写为"**代价不对称校准的 PCS**"：
  探测给出平台位置，m 由代价不对称性决定（欠保护 −4.8 pp/步 vs 过保护 ≈0），
  不再需要逐 seed 正确的 τ*。论文的 PCS 一节按此写，G4 的 2/5 失败率变成
  "朴素 PCS 的逐 seed 失败率，由 m 校准消除"的对照证据（这本身是很好的消融表）。
- 若 m=4 在 ref 或 sig32 上出现可测回退（>0.5 pp），取通过验收的最小 m，并如实报告边界。

交付：`results/routeA/h2_margin.json`（m × 物理 × seed 的 HSR 表）+
一张"朴素 PCS vs 保守 PCS vs 常数"的三线漂移图（横轴漂移、纵轴 HSR）。
EVIDENCE_PACKAGE.md 追加 A23，并**改写 A5 条目**指向最终形态。

---

## 4. 任务 H3（可选加固）：G3 漂移表扩到 5 seeds（0.5 天）

G3 目前是 3 seeds。把 seeds 3–4 补齐（复用 `_routeA_f1b.py` 的 seed 循环，
探测用 `--episodes 8`），A19 从 3 seeds 升到 5 seeds。若机时紧张可跳过。

---

## 5. 封版标准（全部满足后宣布实验结束）

- [ ] H1 有明确结论（机制坐实或降级，两种都算完成）。
- [ ] H2 有明确的最小 m 与三线漂移图。
- [ ] `results/routeA/SUMMARY.md` 追加 Phase H 一节。
- [ ] `docs/CLAIMS_DELTA.md` 更新（A5 最终形态、A20 措辞按 H1 结论定稿）。
- [ ] `docs/EVIDENCE_PACKAGE.md` 追加 A22–A23（+A24 若 H3 做）。
- [ ] `summary.json` 合并 H1–H3。

**此后不再新增实验**；论文写作指导文件另行下发。
