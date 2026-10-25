# 路线 A 实验工作计划（给执行智能体的操作说明）

> 2026-10-23。论文已决定走"机制/审计"路线（Route A）。本文件是**实验与代码工作的唯一执行依据**。
> 论文写作不在本阶段范围内；你只做实验、改代码、汇总数据。
>
> 先读这两个文件再动手（30 分钟，必读）：
> - `docs/THEORY_TFA.md` — 理论命题与 E1–E19 全部实验背景
> - `docs/EVIDENCE_PACKAGE.md` — 主张 A1–A11 与证据、攻击面的映射
>
> 本计划补 5 块拼图：**F1（决定性）→ F2 → F3 → F4 → F5**，最后汇总。

---

## 0. 背景（一段话）

旧稿声称"LLM 让 RL 学得更好"，被复现实验推翻。新故事是：LEO 切换可靠性 ≈ 可行性因子 × 选择质量因子；
可行性因子被失败日志的**右删失**遮蔽，无法靠奖励优化识别（命题 2）；把从删失日志恢复出的下界
编译成**决策盾**后可靠性恢复且**与策略无关**（E2/E3）；但一个手调常数（最高仰角 + 18 s，E12）在标称
物理下追平学习系统——这是审稿人最强的攻击点。论文要把 E12 从"威胁"转化为"动机"：
**常数在标称下持平，物理一漂移就失效，而探测校准盾（PCS）自动跟随**。
F1 就是验证这条因果链的关键实验，**必须最先做，其结果决定后续叙事是否成立**。

---

## 1. 总原则（任何任务都适用）

1. **只追加，不覆盖。** 已有 `results/campaign_*`、`results/multi_*`、`results/verify_1023` 等目录
   **一律视为只读基准**。所有新产物写入新的 `results/routeA_<任务名>/` 目录。
   代码改动遵循"加新 flag、不改旧默认行为"，保证旧命令逐位可复现旧结果。
2. **每条命令进日志。** 在 `results/routeA/` 下维护 `commands.log`，每跑一条命令，追加一行
   `[时间戳] [任务号] 完整命令行`。汇总数字必须能凭此日志逐位重跑。
3. **先自检环境。** 开工第一件事：`python scripts/check_env.py`，输出附在交付物里。
   训练类任务统一 `--device cpu`（与 EVIDENCE_PACKAGE §4 一致）；eval/probe 类脚本本身只用 cpu。
4. **seed 纪律。** 凡与已有实验配对的（F1 对 pcs3、F2 补 fresh_s3），用**相同 seed**；
   新增扫描类实验用 seeds 0–4（5 seeds），与 campaign_pcs3_* 对齐。
5. **验收制。** 每个任务有"验收标准"。达不到时**停下来报告，不要自行调参凑数**；
   尤其 F1 若结果与预期相反（常数在扰动物理下不掉点），这是"前提被推翻"级事件，立即上报。
6. **不写论文。** 不要改 `docs/THEORY_TFA.md` 的正文结论；但每个任务完成后在
   `docs/EVIDENCE_PACKAGE.md` 末尾追加一行新证据（A12、A13…，格式照抄现有表格）。

---

## 2. 任务 T0：资产盘点（0.5 天，先做）

目的：确认哪些东西已存在，避免重复烧机时。

1. 检查以下目录的完整性并记录每个 run 是否有 `run_summary.json`：
   - `results/campaign_1023/`（10 seeds × 8 臂主实验）
   - `results/campaign_pcs3_ref/`、`results/campaign_pcs3_sig32/`（各 5 seeds）
   - `results/campaign_penalty/`（λ=1.0，应 10 seeds）
   - `results/campaign_regime_noseam/`、`results/campaign_regime_tight3/`、`results/campaign_regime_ref4/`
     —— 这三个很可能是 E10 修 `twin_tag` 接线时的验证运行，先读各自 `index.jsonl` 和
     `run_summary.json`，搞清楚它们到底跑了什么物理配置、什么臂、几个 seed。
   - `results/multi_shared_s0..s4`、`results/multi_fresh_s0..s4`：
     已知 `multi_fresh_s3` 只有 intent0、**缺 summary.json，是残次品**，需补跑（见 F2）。
     其余 9 个目录应各有 4 个 intent 子目录 + summary.json，逐一确认。
2. 确认脚本入口及关键参数（已核对，直接采信）：
   - `scripts/eval_shield.py`：支持 `--policy {ckpt,teacher,random,maxel,maxvis,staged}`、
     `--lead`、`--rule`、`--acq-signaling`、`--seed`、`--out`、`--label`，以及 `--twin`/`--hours`。
     它的评估协议与 campaign 最终评估相同（同一 test split / batch / traffic mix）。
   - `scripts/probe_feasibility.py`：目前**没有**等渗拟合和 bootstrap，只有逐 advance 的
     原始 late 率与 `tau* = min{a : late ≤ ε}`（输出末行打印）。
   - `scripts/run_multi_intent.py`：`--mode {shared,fresh}`、`--seed`、`--intents`、
     `--episodes 9600`、`--eval-every 1200`、`--spec results/nas/llm_spec.json`。**没有**
     "注入坏规则"和"关验证门"的入口，需要加（见 F2 代码改动）。
   - `scripts/run_campaign.py`：支持 `--acq-signaling`、`--no-seam`、`--feeder-slots`、
     `--isl-dropout`、`--constellation`、`--probe-calibrated`、`--late-risk-tau/weight`。
3. 交付：一段盘点结论（哪些已有、哪些缺、机器时预算），写入 `results/routeA/t0_inventory.md`。

---

## 3. 任务 F1：常数基线 × 物理扰动（决定性实验，0.5–1 天）

### 3.1 目的与假设

验证叙事链：**标称常数（maxel+18 s）在标称物理 ≈ 93.3（复现 E12）→ 在 +2 s 信令物理下显著掉点
→ 给常数"事后重调"也追不回 PCS → PCS（16→18 s）自动跟随**。

E7/E8 已证明"LLM 挖出的 τ=16 不跟随物理"；但**常数是否跟随尚无数据**。
若常数在扰动物理下也不掉点，整个动机链断裂，必须立刻上报。

### 3.2 执行步骤

全部用 `eval_shield.py`（纯评估，每个配置几分钟）。seeds 用 0–4（5 seeds）。
建议写成循环脚本 `scripts/_routeA_f1.py`（下划线前缀，遵守仓库临时脚本命名惯例），
或直接在 shell 里循环，但**每条命令进 commands.log**。

矩阵（策略 = maxel 即"最高仰角 + 固定提前量"常数规则）：

| 臂 | 命令骨架 |
|---|---|
| A. 标称 sanity | `python scripts/eval_shield.py --policy maxel --lead 18 --seed S --out results/routeA_f1/maxel18_ref_sS.json` |
| B. 扰动物理 × 标称常数 | `... --lead 18 --acq-signaling 3.2 --out results/routeA_f1/maxel18_sig32_sS.json` |
| C. 扰动物理 × 事后重调常数 | `... --lead 20 --acq-signaling 3.2 --out .../maxel20_sig32_sS.json` |
| D. 扰动物理 × 重调常数（再宽） | `... --lead 22 --acq-signaling 3.2 --out .../maxel22_sig32_sS.json` |

S ∈ {0,1,2,3,4}。另加两个参照臂（已有数据，只需从旧结果抄录进同一张表，不用重跑）：

- E. PCS 在 sig32 上的表现：`results/campaign_pcs3_sig32/almond_seedS` 的极区 HSR（E8 已有）。
- F. 学习策略 + 挖出的 16 s 盾在 sig32 上的表现：`results/campaign_sig32/` 对应 seed。

注意：`eval_shield.py` 的输出 JSON 里取**极区（latitude_abs_deg ≥ 68°）HSR** 和 satisfaction S 两个数；
从每个 `--out` JSON 里提取，连同命令一起记入 `results/routeA/f1_table.json`。

### 3.3 验收标准

1. 臂 A 的 5-seed 均值落在 92.5–94.0（与 E12 的 93.3/93.6 同量级）。偏离 >1.5 pp 先检查
   seed/协议是否对齐，查不出就上报。
2. **判定规则**：若臂 B 相对臂 A 掉点 ≥ 2 pp，且臂 C/D 的最高恢复值仍低于臂 E ≥ 1 pp，
   则 F1 成功，动机链成立。若臂 B 掉点 < 2 pp（常数居然鲁棒），立即上报并附全部原始数字。
3. 交付：`results/routeA/f1_table.json`（每臂 × 每 seed 的极区 HSR、S）+
   一段结论文本（含 5-seed 均值 ± sd）。

---

## 4. 任务 F2：多意图补全 + "验证门价值"对照（2–3 天）

### 4.1 补跑残次品

`multi_fresh_s3` 缺 intents 1–3。补跑：

```
python scripts/run_multi_intent.py --mode fresh --seed 3 --out results/multi_fresh_s3
```

（参数默认值即协议规定值，但**显式写全**：`--episodes 9600 --eval-every 1200
--spec results/nas/llm_spec.json --device cpu`。）跑完后确认 4 个 intent 子目录 + summary.json 齐全。
机时较长（cpu、4 个意图串行），放后台/夜间跑，期间做 F2 的代码改动。

### 4.2 代码改动：加"验证门价值"对照

**动机**（EVIDENCE_PACKAGE 攻击点 A7 的第二条）：目前 `no_counterfactual` 组件没有任何正面对照，
审稿人可以问"你怎么证明验证门不是摆设"。E18 已证明门会拒掉 6 个自然候选中的 4 个
（Δ_test<0），但那是在单意图协议里。**要在多意图协议里展示：一个"讲得通但有害"的规则，
在有门时被拦下、在无门时污染后续意图。**

改动（只加不改）：

1. `scripts/run_multi_intent.py` 增加 `--inject-bad-rule "RULE"` 参数（语法与 eval_shield 相同，
   例如 `min_advance:8@latitude_abs_deg>=68`——E18 已验证它 Δ_test<0）。该规则作为候选约束
   在 intent0 取证后**注入知识图谱**。
2. 增加 `--mode shared_nogate`：与 `shared` 的唯一差别是候选约束**跳过 counterfactual 验证门**
   直接入 KG（需要在 `almond/framework/system.py` 里找到 gate 调用点，加一个开关配置项，
   默认 False 不改变现有行为）。
3. 实现后先做 smoke：1 个 seed、`--episodes` 缩到 600、`--eval-every 600`，确认
   `shared_nogate + inject-bad-rule` 的 KG 里确实留下了 8 s 规则、`shared + inject-bad-rule` 的 KG 里没有。

### 4.3 正式跑（seeds 0–4）

| 臂 | 命令 |
|---|---|
| G. shared + 坏规则 | `run_multi_intent.py --mode shared --inject-bad-rule "min_advance:8@latitude_abs_deg>=68" --seed S --out results/routeA_f2/shared_badrule_sS` |
| H. shared_nogate + 坏规则 | `... --mode shared_nogate --inject-bad-rule ... --out results/routeA_f2/nogate_badrule_sS` |

S ∈ {0,...,4}。已有数据复用：现有 `multi_shared_s*`（= 臂"shared 无注入"）、
补跑后的 `multi_fresh_s3` 与其余 `multi_fresh_s*`。

### 4.4 验收标准与交付

1. 臂 G 的 intents 1–3 表现应与现有 `multi_shared_s*` **无显著差异**（坏规则被门拦下）；
   臂 H 的 intents 1–3 应显著恶化（差值即"验证门的价值"，预期 +10 pp 量级，方向必须为正）。
   用逐 seed 配对差 + Wilcoxon 符号秩检验汇总。
2. 交付：`results/routeA/f2_table.json`（每臂 × 每 seed × intent0–3 的 HSR/S）+ 结论一段。
3. EVIDENCE_PACKAGE.md 追加 A12（验证门在多意图协议中的因果价值，n=5）。

---

## 5. 任务 F3：E9 λ 扫描补全（1–2 天，可与 F2 并行排队）

堵攻击点 A6（"λ 只扫了 1.0"）。`campaign_penalty/` 已有 λ=1.0 × 10 seeds，补三个系数：

```
python scripts/run_campaign.py --methods no_forensics --seeds 0-9 --episodes 9600 --eval-every 1200 \
    --device cpu --spec-file results/nas/llm_spec.json --late-risk-tau 16 --late-risk-weight L \
    --out results/routeA_f3/penalty_lamL        (L ∈ {0.3, 0.5, 2.0})
```

### 验收标准

1. 三个 λ 的 10-seed 极区 HSR 全部落在"无知识"区间（参照 `campaign_1023/no_forensics_*` 的
   71.8 ± 12.6）± 3 pp 内，即**没有任何 λ 能让奖励注入接近盾注入（93.6）**。
   这是要写进论文的定量边界："在该任务族里，惩罚强度扫描无法补救奖励层的注入失败"。
2. 若某个 λ 意外达到 85+，立即上报（这会动摇 A6）。
3. 交付：`results/routeA/f3_table.json` + EVIDENCE_PACKAGE.md 追加 A13。

---

## 6. 任务 F4：PCS 探测噪声收敛（1 天代码 + 1 天跑）

堵攻击点 A5（"5 个 seed 里 1 个探测仍给 16 s"）。目标：让 τ* 的识别在
2–16 episode 预算内达到 bootstrap CI 宽度 ≤ 1 s，并在 sig32 物理下 5/5 seeds 给出 18 s。

### 6.1 代码改动（`scripts/probe_feasibility.py`，只加不改）

1. 等渗拟合：对 `(advance, late_rate)` 序列做 PAVA 单调不减拟合（注意 late 率随 a 递减是
   期望方向；以"成功/late 互补" whichever 保证单调方向后取交点），τ* 取拟合曲线首次
   ≤ ε 的 advance。保留现有原始输出。
2. Bootstrap：episode 是抽样单位。对每个 advance 桶内的 episode 成败有放回重采样 B=200 次，
   每次重算拟合 τ*_b，报告 5%/95% 分位作为 CI。
3. 自适应停早：`--episodes auto`——从 2 起步，每次翻倍（上限 16），当 CI 宽度 ≤ `--ci-width 1.0` s
   时停止。打印每轮的 n 与 CI。
4. 输出 JSON 增加 `tau_star`、`tau_ci`、`fit_rows` 字段；`--out` 缺省时仍打印到 stdout。

改动后在**两种物理**下验证探测本身（用 `campaign_1023/almond_seed0` 的 ckpt，快）：

```
python scripts/probe_feasibility.py --run results/campaign_1023/almond_seed0 --regime polar --episodes auto --out results/routeA_f4/probe_ref_s0.json
python scripts/probe_feasibility.py --run results/campaign_1023/almond_seed0 --regime polar --episodes auto --acq-signaling 3.2 --out results/routeA_f4/probe_sig32_s0.json
```

期望：ref → τ*=16，sig32 → τ*=18。

### 6.2 正式验证（seeds 0–4）

对 `campaign_1023/almond_seed{0..4}` 的 ckpt 各跑上述两种物理，共 10 次探测。

### 6.3 端到端复验（确认 0 损失声明不受影响）

用改后的探测重跑 PCS campaign（确认自动探测驱动的 `--probe-calibrated` 端到端数字不回退）：

```
python scripts/run_campaign.py --methods almond --seeds 0-4 --episodes 9600 --eval-every 1200 \
    --device cpu --spec-file results/nas/llm_spec.json --probe-calibrated \
    --out results/routeA_f4/pcs_ref
python scripts/run_campaign.py --methods almond --seeds 0-4 --episodes 9600 --eval-every 1200 \
    --device cpu --spec-file results/nas/llm_spec.json --acq-signaling 3.2 --probe-calibrated \
    --out results/routeA_f4/pcs_sig32
```

（若 `run_campaign.py` 的 `--probe-calibrated` 内部走的是另一套探测代码而非
`probe_feasibility.py`，需要把 PAVA+CI 同步进去或让 campaign 调用脚本——先读
`almond/framework/system.py` 中 `probe` 相关代码再决定，保持两处逻辑一致。）

### 验收标准

1. 探测层：sig32 物理下 5/5 seeds τ*=18（CI 不含 16）；ref 物理下 5/5 seeds τ*=16。
2. 端到端：`routeA_f4/pcs_ref` 的极区 HSR 与 `campaign_pcs3_ref` 差 ≤ 0.3 pp；
   `pcs_sig32` 相比 `campaign_pcs3_sig32` 不回退（允许 ±0.5 pp 噪声）。
3. 交付：`results/routeA/f4_table.json`（每 seed × 物理的 τ*、CI、端到端 HSR）
   + EVIDENCE_PACKAGE.md 追加 A14。

---

## 7. 任务 F5：替代物理配置的差距分解复现（1–2 天）

堵"单一孪生"攻击。T0 已盘点 `campaign_regime_*` 三个目录；**先判断它们够不够**：
若它们已覆盖"同一批臂 × 替代物理"且 seed 数 ≥ 3，则只做汇总表，不新跑。
不够则按下补跑（mini-factorial，seeds 0–4，臂 = almond, ppomlp, no_forensics）：

```
# 无缝极地（seam 惩罚关闭，E10 验证过物理已生效：seam off → 94.8）
python scripts/run_campaign.py --methods almond,ppomlp,no_forensics --seeds 0-4 --episodes 9600 \
    --eval-every 1200 --device cpu --spec-file results/nas/llm_spec.json --no-seam \
    --out results/routeA_f5/noseam
```

另选一个替代配置（`--constellation` 的合法取值先 `grep -n constellation almond/framework/system.py
scripts/build_twin.py` 查清再选；`--feeder-slots` 或 `--isl-dropout` 亦可作为扰动轴，
选一个即可）：

```
python scripts/run_campaign.py --methods almond,ppomlp,no_forensics --seeds 0-4 ... <替代配置> \
    --out results/routeA_f5/alt1
```

### 验收标准

核心结论在两个替代物理下**方向不变**：① 盾前 almond ≈ ppomlp（策略无关）；② 晚切换率
仍是唯一随臂大幅变化的失效类；③ 加 16/18 s 盾后两臂同时升到该区间的天花板。
若有任一方向反转，如实记录并上报（这可能是论文里最有信息量的发现，也可能是 bug——先查）。
交付：`results/routeA/f5_table.json`（失效归因 × 臂 × 配置）+ EVIDENCE_PACKAGE.md 追加 A15。

---

## 8. 汇总与交付（0.5 天，全部任务完成后）

1. 写 `results/routeA/SUMMARY.md`：F1–F5 每段一节 = 问题、命令索引（指向 commands.log）、
   关键数字表、验收标准逐条打勾、未决问题。
2. 写 `results/routeA/summary.json`：机器可读版核心数字（F1 各臂 HSR、F2 配对差与 p 值、
   F3 λ 表、F4 τ* 表、F5 失效归因表）。
3. 更新 `docs/EVIDENCE_PACKAGE.md`：追加 A12–A15 四行 + 复现命令区块追加 routeA 命令。
4. 最终自检清单：
   - [ ] 所有新产物在 `results/routeA_*`，旧目录零改动（`git status` 核对）。
   - [ ] commands.log 覆盖 100% 新命令。
   - [ ] 每个验收标准有明确通过/不通过结论；不通过的已上报而非掩盖。
   - [ ] 所有"5 seeds"任务确实是 5 个独立 seed，不是同一 seed 跑 5 次。

---

## 9. 机时预算与顺序

| 顺序 | 任务 | 机时（cpu） | 备注 |
|---|---|---|---|
| 1 | T0 盘点 | <1 h | 含读代码 |
| 2 | **F1** | <1 h eval | **先做；结果决定叙事是否成立** |
| 3 | F2 补跑 fresh_s3 | 数小时–过夜 | 后台跑，期间做 4.2 代码改动 |
| 4 | F2 G/H 臂 × 5 seeds | 2× 过夜量级 | 可与 F3 排队并行 |
| 5 | F3 λ 扫描 ×3 × 10 seeds | 3× 过夜量级 | 与 F2 串行排队即可 |
| 6 | F4 代码 + 探测验证 | 半天 | 端到端 PCS 复验与 F2/F3 并行 |
| 7 | F5 两个配置 × 3 臂 × 5 seeds | 2× 过夜量级 | 视 T0 盘点可减免 |
| 8 | 汇总 | 半天 | |

总周期约 1–1.5 周（串行排队），并行可压到 1 周内。
