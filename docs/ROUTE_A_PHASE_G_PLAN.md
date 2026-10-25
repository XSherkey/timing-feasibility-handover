# 路线 A 实验工作计划 · 第二阶段（Phase G，给执行智能体的操作说明）

> 2026-10-23。第一阶段（F1–F5）已完成，交付物在 `results/routeA/`（先读 `results/routeA/SUMMARY.md`，
> 尤其 §1–§4 三个"未按预期"的任务）。本阶段依据 F 阶段结论修补残余缺口，**补完后实验证据闭环，进入论文写作阶段**。
>
> 必读文件：`results/routeA/SUMMARY.md`、`docs/THEORY_TFA.md` §3 与 §4、
> `docs/EVIDENCE_PACKAGE.md`（已含 A12–A16）。

---

## 0. F 阶段改变了什么（本阶段的工作前提）

F 阶段三个任务没有按原预期走，但都没有推翻路线 A，只是把三条主张改成了更精确的形态：

| 原主张 | F 阶段后的修正形态 | 残余缺口（本阶段补齐） |
|---|---|---|
| A6 "奖励注入无效" | **剂量-反应**：λ=8 补回 12.6 pp（71.8→84.4）但仍差盾 9.2 pp、方差大 10 倍；主张改写为"奖励路径需极端系数、收益递减、稳定性差" | λ 渐近线未探明（审稿人会问"λ=32 呢"）；只报了 HSR 没报 S |
| A5/PCS "探测跟随物理" | 端到端成立，但 ① sig32 上 PCS 91.6±2.5 **低于**常数 93.4（probe 只有 2 episodes，噪声未压）；② τ\* 存在 ±2 s 内在不可辨识区间 | 用 probe_episodes=8 复跑 sig32 端到端；量化"选错平台点"的代价 |
| A12 验证门 +20.5 pp | 方向成立但 ① n=5，Wilcoxon p=0.0625 已是 n=5 最小可达值，**不构成统计显著**；② 注入是**替换**式，门开后退化为无知识（71.9 vs 无注入 91.8），对照不干净 | 干净设计（追加式注入）+ 扩到 n≥8 |
| E12 常数基线 | 升级为 A15：**常数有约 2 s 安全余量**，+3.2 s 起急剧失效（−7.3 pp）、+5.6 s 掉 13.3 pp；τ\* 校准全程贴天花板 | F1b 漂移扫描只有 seed0，需扩 seed |

**叙事决定（已拍板，勿再改）**：论文按"常数有 2 s 余量 → 超出后崩溃 → 探测校准把边界随物理移动"写，
漂移扫描**曲线**放正文，不用单一 +2 s 点做标题（+2 s 点上常数与 PCS 持平是"余量内"的正常现象，不构成反证）。
本阶段 G3 负责把这条曲线变成多 seed 的。

---

## 1. 总原则（与第一阶段相同，重申关键的）

1. 只追加不覆盖：新产物进 `results/routeA_g*/`；F 阶段与旧 campaign 目录只读。
2. 每条命令追加进 `results/routeA/commands.log`（标注任务号 G1–G6）。
3. 代码改动只加 flag、不改旧默认：`probe_episodes` 默认值**保持 2**（保住旧 campaign 可复现性），
   新实验显式传 8；论文方法节再说明"推荐 8"。
4. 每个任务有验收标准；达不到先上报，不得调参凑数。
5. 完成后在 `docs/EVIDENCE_PACKAGE.md` 追加 A17 起的条目。

---

## 2. 任务 G1：验证门——干净设计 + 统计功效（2–3 天）

### 2.1 代码改动：`run_multi_intent.py` 加"追加式注入"

已核实：现有 `InjectedLLM.__call__` 对 `forensic_hypothesis` 调用**直接返回注入候选、不再调真 LLM**
（替换式，见 `scripts/run_multi_intent.py` 第 82–85 行）；取证管线消费的是
`hyp.get("hypotheses", [])` 列表（`almond/framework/forensics.py:278-279`）。因此支持追加式：

- 新增 `--inject-bad-rule-extra RULE`（与现有 `--inject-bad-rule` 互斥）：
  真 LLM 正常提案（好规则），注入候选**追加**进 `hypotheses` 列表，两者一起过 audit + gate。
- 保持 `--inject-bad-rule`（替换式）不变，旧 F2 结果继续可复现。
- 实现后先 smoke（1 seed、--episodes 600）：检查门开时 KG 最终应**只含**挖出的好规则
  （magnitude≈16，kg_active=1）、不含 6 s 候选；门关（shared_nogate + extra）时 KG 含 6 s。

### 2.2 正式实验

| 臂 | 内容 | seed |
|---|---|---|
| I. clean_gate | `--mode shared --inject-bad-rule-extra "cap_advance:6@latitude_abs_deg>=68"` | 0–4 |
| J. gate 原臂（已有） | F2 的 G 臂 seeds 0–4 | 0–4 |
| K. nogate 原臂（扩） | `--mode shared_nogate --inject-bad-rule "cap_advance:6@latitude_abs_deg>=68"` | **5–9**（J 的对应臂同样扩 5–9） |

即 gate vs nogate 最终 n=10（seeds 0–9）；若机时紧张，最低 n=8（seeds 0–7），p 可低至 0.0078。

### 2.3 验收标准

1. 臂 I 的 intents 1–3 均值应与现有无注入 `multi_shared_s0..s4`（91.8）**差 ≤ 2 pp**
   （坏规则被拒、好规则保留——这是"门不误伤"的证据）。
2. 臂 J vs K（n=10）：配对差 ≥ +15 pp 且 Wilcoxon p ≤ 0.01（n=10 全部同向时 p≈0.002）。
3. 交付 `results/routeA/g1_gate_power.json` + EVIDENCE_PACKAGE.md 追加 A17。

---

## 3. 任务 G2：奖励注入渐近线 + HSR–S 前沿（1–2 天，可与 G1 排队并行）

### 3.1 λ 渐近扫描

F3 的 λ=8 → 84.4 引出审稿人必问："继续加大呢？"补三个点：

```
python scripts/run_campaign.py --methods no_forensics --seeds 0-9 --episodes 9600 --eval-every 1200 \
    --device cpu --spec-file results/nas/llm_spec.json --late-risk-tau 16 --late-risk-weight L \
    --out results/routeA_g2/penalty_lamL        (L ∈ {16, 32, 64})
```

### 3.2 提取 S，画前沿

从全部 λ 臂（0/0.3/0.5/1.0/2.0/8.0/16/32/64）的 `run_summary.json` 同时提取**极区 HSR** 和
**satisfaction S**，做 (HSR, S) 散点：盾对应点 (93.6, 79.1——用 E13 的 18 s 值)。核心论证：
要么惩罚路径的 HSR 渐近线在盾之下（S 再高也没用），要么 λ 大到追平 HSR 时 S 崩了——
**盾在 (HSR, S) 平面上不被任何 λ 支配**。这是 A13 的最终形态。

### 3.3 G2b（加分项，便宜）：惩罚知识随物理漂移吗？

奖励把知识**烤进权重**——它和常数、LLM 幅值一样应该不跟随物理。验证（纯评估）：

```
python scripts/eval_shield.py --run results/routeA_f3/lam8.0/no_forensics_seedS --acq-signaling 3.2 --seed S ...
```

对 λ=8 臂的 10 seeds 在 +2 s 物理下重评估（无盾、只换孪生物理）。
预期：λ=8 策略在 sig32 下掉到 80 档（它学到的是 a≥16，而新物理需要 18）。
若成立，与 A15/A4 合起来形成完整对称性：**常数失效、LLM 幅值失效、奖励烤入的权重失效——
只有探测重新推导的盾跟随**。这是论文里非常漂亮的一组三连对照。

### 3.4 验收标准

1. 渐近线明确（< 90 或 S 崩溃），或者如实报告"λ=64 追平但代价是 X"——如实即可，两种结果都有写法。
2. G2b 方向符合预期（掉 ≥ 5 pp）；若 λ=8 策略在 sig32 下纹丝不动，上报（这反而奇怪，需查）。
3. 交付 `results/routeA/g2_frontier.json` + 前沿图 PNG + EVIDENCE_PACKAGE.md 追加 A18。

---

## 4. 任务 G3：F1b 漂移扫描扩 seed（0.5–1 天，纯评估+探测，便宜优先做）

F1b 的"常数余量边界"曲线目前只有 seed0。扩到 **seeds 0–2**（至少 3 seeds；
若 G3 跑得快可到 0–4），漂移档 {0, +2, +3.2, +4.4, +5.6}：

1. 每 (seed, 档)：先用 `scripts/probe_feasibility.py --episodes 8`（**8 episodes，F4 的结论**）
   探 τ*；
2. 再跑 `eval_shield.py --policy maxel --lead L`（L ∈ {18, 20, 22, 24} 小网格）找该 seed 的最优常数；
3. 以及 `eval_shield.py --rule "min_advance:TAU@latitude_abs_deg>=68"` 的校准臂。

可复用 F 阶段的 `scripts/_routeA_f1b.py`，把 seed 循环和 `--episodes 8` 参数化。

### 验收标准

1. 多 seed 下"固定 18 s 在 +3.2 s 起崩溃、校准臂贴天花板"方向 3/3 一致；
   边界档（+2 与 +3.2 之间）允许 ±0.8 s 的 seed 间抖动，如实报告。
2. 交付 `results/routeA/g3_drift_sweep.json`（每 seed × 档 × 臂）+ 多 seed 边界曲线图
   （带 min-max 带）。EVIDENCE_PACKAGE.md 追加 A19（替代/升级 A15 的 seed0 版本）。

---

## 5. 任务 G4：PCS 端到端复跑（probe_episodes=8）+ 不可辨识性代价（2–3 天，最重的任务）

### 5.1 为什么必须做

F1 暴露了一个尴尬数字：sig32 上 PCS 端到端 91.6±2.5 **低于**手调常数 93.4。
原因已查明（F4）：in-loop 探测默认 2 episodes，τ\* 的 sd 2.45，部分 seed 探到 16 而非 18。
论文标题级数字不能用 sd 2.5 的版本。**注意：这不改变 A5 的方向，只是把噪声压掉。**

### 5.2 代码改动与复跑

已核实 `AlmondConfig.probe_episodes` 字段存在（`almond/framework/system.py:113`，默认 2），
`run_campaign.py` 只是没有 CLI 入口。加：

```python
ap.add_argument("--probe-episodes", type=int, default=2)
```

（`run_one` 会把 base 里与 dataclass 字段同名的键写进 cfg，无需其它改动。）然后：

```
# sig32 主数字（5 seeds，替换 campaign_pcs3_sig32 的标题位）
python scripts/run_campaign.py --methods almond --seeds 0-4 --episodes 9600 --eval-every 1200 \
    --device cpu --spec-file results/nas/llm_spec.json --acq-signaling 3.2 \
    --probe-calibrated --probe-episodes 8 --out results/routeA_g4/pcs8_sig32
# ref  sanity（3 seeds，确认 0 损失声明不受影响）
python scripts/run_campaign.py --methods almond --seeds 0-2 --episodes 9600 --eval-every 1200 \
    --device cpu --spec-file results/nas/llm_spec.json \
    --probe-calibrated --probe-episodes 8 --out results/routeA_g4/pcs8_ref
```

### 5.3 不可辨识性代价量化（纯评估，便宜）

τ\* 的 ±2 s 平台到底花多少钱？冻结策略（`campaign_1023/almond_seed0..4`）×
τ ∈ {14, 16, 18}（ref）与 τ ∈ {16, 18, 20}（sig32）各跑 `eval_shield.py`，5 seeds。
E4 单 seed 显示 14→91.9 / 16→92.4 / 18→93.3，多 seed 后给出"选错平台点的代价 ≤ X pp"的定量上界，
与 A14 合写成"精度上限与代价"一节。

### 5.4 验收标准

1. `pcs8_sig32`：5-seed 均值 ≥ 92.0 且 sd ≤ 1.5（对照旧 91.6±2.5；F1b 的校准臂上界约 93.2）。
   仍低于常数 93.4 可接受——标题叙事是"余量内持平、余量外崩溃 + 自动跟随"，不是逐点取胜。
2. `pcs8_ref` 与 campaign_pcs3_ref 差 ≤ 0.3 pp（0 损失声明保持）。
3. 交付 `results/routeA/g4_pcs8.json` + EVIDENCE_PACKAGE.md 追加 A20（替换 E8 的标题位数字，旧数字降级为"2-episode 探测"脚注）。

---

## 6. 任务 G5：探测成本记账（0.5 天，便宜）

审稿人攻击面："探测是不是免费作弊？" 从 G3/G4 的 probe 输出里直接统计：
每推导一次 τ* 消耗的 attempt 数（= advances 数 × episodes × 每 episode attempt 数）与
wall time，折算成相对训练预算（9600 episodes）的比例。不需要新实验，写个汇总脚本即可。
交付 `results/routeA/g5_probe_cost.json` + EVIDENCE_PACKAGE.md 追加 A21。

---

## 7. 任务 G6：主张变更清单（写作阶段的输入，0.5 天）

写一个 `docs/CLAIMS_DELTA.md`，把 THEORY_TFA §3 的 A1–A11 逐条对照 F/G 两阶段的最终形态，
标明：**不变 / 改写（给新措辞）/ 新增（A12 起）/ 废弃**。至少覆盖：

- A6 → A13 剂量-反应改写（新措辞照抄 SUMMARY §3 的结论句）；
- A5 → A14+A20：精度上限 ±2 s、代价 ≤ X pp（G4 数字）、推荐 probe_episodes=8；
- A12 → A17：n=10、干净对照；
- A15 → A19：多 seed 边界曲线；
- 新增：惩罚知识不随物理漂移（G2b，若通过）。

此文件是之后论文重写的"diff 底稿"，只做清单不做写作。

---

## 8. 汇总与交付

1. `results/routeA/SUMMARY.md` 追加 Phase G 一节（每任务：问题、验收打勾、关键数字）。
2. `results/routeA/summary.json` 合并 G1–G5 数字。
3. EVIDENCE_PACKAGE.md 追加 A17–A21 与 G 阶段复现命令。
4. 自检：新产物全在 `routeA_g*`；commands.log 覆盖 100%；每个验收标准有明确结论。

## 9. 顺序与机时

| 顺序 | 任务 | 机时 | 备注 |
|---|---|---|---|
| 1 | **G3** 漂移扫描扩 seed | 半天（eval+probe 为主） | 便宜且 A15 升级依赖它 |
| 2 | G2 / G2b λ 渐近 + 前沿 | 3 λ × 10 seeds ≈ 3 个过夜 | 可与 G1 串行排队 |
| 3 | G1 代码 + smoke，然后 I/J/K 臂 | I 臂 5 runs + J/K 扩 10 runs，约 3–4 过夜 | 最重，尽早启动 |
| 4 | G4 代码 + pcs8 复跑 | sig32 5 runs + ref 3 runs ≈ 2 个过夜 | 与 G1/G2 并行机时 |
| 5 | G4 不可辨识代价 + G5 | 数小时 eval | 穿插进行 |
| 6 | G6 清单 | 半天 | 全部数字落定后写 |

总周期约 1 周（两路并行）。**G 阶段完成后停手汇报，不要开始写论文**——论文重写将另行给指导文件。
