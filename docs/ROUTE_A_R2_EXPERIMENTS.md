# Route A 第二轮审稿（R2）实验与修改计划

**日期**：2026-10-24
**触发**：`IEEE_Trans_新版本/论文理论审稿意见2.docx`（第二轮拒稿级意见）
**执行者**：代码/实验智能体（本文件为其唯一任务说明）
**工作目录**：`D:\Desktop_Files\论文\1. LLM Satellite Reinforcement Learning\自己写\almond-repro`
**论文目录**：`D:\Desktop_Files\论文\1. LLM Satellite Reinforcement Learning\自己写\From Human Intent to In-Orbit Action\IEEE_Trans_新版本`（其中 `paper_en.md` / `paper_zh.md` 已有带 [E1]–[E4] 标记的槽位，本计划产出的数字填入这些槽位）

---

## 0. 背景（一页读懂）

我们在复现并审计自己的 ALMOND 系统（LEO 卫星切换：LLM 翻译意图 + PPO 图策略 + 从失败日志挖掘约束）。论文核心主张：几乎全部已报道增益来自一条计时可行性约束（极区切换提前量 ≥ 16 s），它必须由决策盾执行而非奖励惩罚。第二轮审稿人确认 v3 有进步，但仍拒稿，理由四条：

1. **命题 1 离散化重写后仍缺全局结论的合法性**（已在文本侧改为离散网格版，见 paper_en.md IV.B；实验侧需要支持"λ 扫描中实现提前量始终低于阈值"的逐 λ 提前量分布数字，已有 h1 产物，可能只需重新汇总）；
2. **命题 3 只能给加法界**（文本已改，无需实验）；
3. **KM 支撑集审计不足**：要"每个提前量桶的尝试数/精确事件数/右删失数"与按状态分层的 KM 敏感性分析（**E4**）；
4. **测试集泄漏只披露未解决**：要求真正独立 lockbox 评估，最好是独立轨道相位/独立交通实例（**E2**）；并要求逐次真实需求的 oracle shield 参照（**E3**）；阈值台账中 τ=18（含余量的部署算法）臂缺失（**E1**）。

## 1. 总原则与不变量（违反即返工）

1. **旧目录零写入**：`results/routeA*`（F/G/H 阶段既有产物）、`results/campaign_1023/`、`results/routeA_f3/` 等既有目录一律只读。所有新产物写入 `results/routeA_r2/`。
2. **回归闸**：任何代码改动后必须重跑默认路径回归，期望 `92.4 / 93.8 / 78.8`（ALMOND seed0 三个业务倍数的极区 HSR）与改动前**逐位一致**；并在 `results/routeA_r2/REGRESSION.md` 记录改动前后数字。
3. **lockbox 铁律**：E2 中任何选择步骤（探测 τ、门准入、λ）**不得**触碰 lockbox 数据。lockbox 孪生上的评估只跑一次，不许"看一眼再调"。
4. **命令留痕**：每条命令追加到 `results/routeA_r2/commands.log`（时间戳 + 命令 + 退出码）。
5. **执行顺序**：先 C（代码改动）→ 回归 → E1 → E4 → E3 → E2（E2 最后，因为它是头条实验，前面所有步骤必须已稳定）。
6. 全部 CPU 运行；每条 `eval_shield` 评估约 1–3 分钟，λ 扫描类训练已存在（不许重训）。

## 2. 代码改动（C1–C5）

### C1. `scripts/eval_shield.py`：新增 `--epoch-doy`（lockbox 孪生）

- 现状：第 ~136 行 `DigitalTwin(TwinConfig(tag=args.twin, horizon_s=args.hours * 3600, **twin_kwargs))`；`TwinConfig` 在 `almond/twin/twin.py` 第 45–46 行有 `epoch_year=2026, epoch_doy=292.25`。
- 改动：新增 CLI 参数 `--epoch-doy FLOAT`，非空时 `twin_kwargs["epoch_doy"] = args.epoch_doy`。
- 验证：`python scripts/eval_shield.py --run results/campaign_1023/almond_fixedarch_seed0 --rule "min_advance:16@latitude_abs_deg>=68" --epoch-doy 299.25 --out results/routeA_r2/_smoke_lockbox.json` 可运行且极区 HSR 与默认孪生不同（相位已变），但同参数重跑逐位一致（确定性）。

### C2. `almond/twin/handover_env.py` + `scripts/eval_shield.py`：oracle-min-advance 盾

- 原理：env.step 在判定成功前已对本尝试算出真实建链需求 `t_setup`（`handover_env.py` 第 ~489–499 行）。oracle 盾 = 决策时刻把 lead 钳到 `max(lead, t_setup)`（只对极区谓词生效，与 mined rule 同作用域，便于对照）。
- 改动：
  1. `EnvConfig` 增加布尔字段 `oracle_min_advance: bool = False`。
  2. `handover_env.py` step 内、`lead_ok` 计算之前（第 ~499 行处）：若 `self.cfg.oracle_min_advance` 且 `|site_lat| >= 68`，则 `lead[idx] = np.maximum(lead[idx], t_setup[idx])`（注意要在 `_log_attempt` 记录的 lead 是**钳后**值，保证尝试日志反映实际执行的动作）。
  3. `eval_shield.py` 新增 `--oracle-shield` 开关：置 `env_cfg.oracle_min_advance = True`，且与 `--rule` 互斥（parser 层检查）。
- 验证：同一 checkpoint、同一 seed，`--oracle-shield` 的晚切换占比应≈0；与 `--rule min_advance:16...` 结果不同（oracle 更高或持平）。

### C3. `scripts/probe_feasibility.py`：新增 `--window {test,validation}`

- 现状：第 137 行硬编码 `test_idx = SplitConfig().indices(twin.n_time, "test", args.steps)`。
- 改动：`ap.add_argument("--window", default="test")`；`splits.indices(twin.n_time, args.window, args.steps)`（SplitConfig.indices 的 `which` 直接支持 "validation"）。
- 用途：E2 lockbox 协议的标定探测只允许在验证窗口跑（`--window validation`）。
- 验证：`--window validation` 与 `--window test` 产出不同（窗口不同），各自重跑逐位一致。

### C4. 新脚本 `scripts/_routeA_r2_km_audit.py`（KM 支撑审计）

- 输入：`results/campaign_1023/*_seed*/run_summary.json` 的 `final.attempts`（字段已核实齐全：`handover_advance_s, t_setup_s, cause, success, latitude_abs_deg, elevation_deg, isl_hop_count, plane_change, buffer_occupancy`）。
- 输出 `results/routeA_r2/km_support_audit.json`：
  1. **表 D1 数据**：极区（|lat|≥68）全部尝试按提前量桶 {6–8, 8–10, 10–12, 12–14, 14–16, 16–18, ≥18} 的 attempts / exact events（success 且 t_setup 有效）/ right-censored（cause=late_handover）计数，及桶末 KM 生存值；
  2. **KM 曲线上分位数支撑**：p50/p90/p95 各自由哪些桶的事件/删失承载（事件发生时间与删失时间的最大贡献桶）；
  3. **分层 KM**：按 elevation 带（<25°, 25–40°, >40°）、isl_hop_count（0 / 1 / ≥2）、plane_change（0/1）分层，各层给 naive 中位（仅成功尝试）vs KM 中位；输出层间差值。
- 实现：复用 `scripts/km_setup_time.py` 的 `km()` 与量化函数（import 或复制），不要改动 km_setup_time.py 本身。

### C5. 新脚本 `scripts/_routeA_r2_llm_meta.py`（LLM 版本元数据）

- 输入：`results/campaign_1023/*/llm_calls.jsonl`（先 `head -1` 核实字段，应含时间戳与模型字段；若没有模型字段，记录"产物未存模型字段"这一事实本身）。
- 输出 `results/routeA_r2/llm_meta.json`：每次调用的最早/最晚时间戳、调用次数、模型字段取值集合、按 run 的分组统计。用于论文 III 节版本钉扎声明（paper 已写声明框架，只需核对事实）。

## 3. 实验（E1–E5）

### E1. 因子化 τ=18 臂（填论文 [E1] 槽位；VI-B、V.D 台账）

补齐阈值台账中间一行：部署算法（τ*=16 + 余量 m=2）在标称物理下的实际阈值 18 s。

```bash
for s in 0 1 2 3 4 5 6 7 8 9; do
  python scripts/eval_shield.py --run results/campaign_1023/almond_fixedarch_seed$s \
      --rule "min_advance:18@latitude_abs_deg>=68" \
      --out results/routeA_r2/factorial_tau18_seed$s.json
done
```

- 汇总 `results/routeA_r2/factorial_tau18.json`（per-seed 极区 HSR + mean ± sd + span），并把 τ=18 逐种子值并入 `factorial_tau16/20` 的既有汇总文件副本（放 routeA_r2 下，不改旧文件）。
- 同时重跑 τ=16 与 τ=20 臂到 routeA_r2 下（同协议、同命令、新 out 路径），确认与附录 C 既有数字**逐位一致**（这是新目录的"同一性证明"）。
- 期望（不写进论文，仅供自检）：18 s 臂均值在 93.6–94.1 之间，晚切换占比 ≈0%。

### E4. KM 支撑审计（填论文 [E4] 槽位；附录 D 表 D1 + V.A）

```bash
python scripts/_routeA_r2_km_audit.py
```

- 产物：`results/routeA_r2/km_support_audit.json` + `km_support_audit.md`（人读版表 D1 + 分层表）。
- 自检：14–16 s 桶的 attempts 数必须打印出来（论文 V.A 已写"thin, not empty"，数字必须与该措辞相容：若 14–18 桶尝试数实际为 0，立即停下并在 REGRESSION.md 报告——论文文本需要随之改）。

### E3. 逐次真实需求 oracle 盾（填论文 [E3] 槽位；VI-G）

先 C2 回归，然后：

1. **因子化 oracle 臂**（与表 C1 相同回合/种子）：

```bash
for s in 0 1 2 3 4 5 6 7 8 9; do
  python scripts/eval_shield.py --run results/campaign_1023/almond_fixedarch_seed$s \
      --oracle-shield --out results/routeA_r2/oracle_factorial_seed$s.json
done
```

2. **漂移阶梯**（与表 C2 相同协议，`--acq-signaling` 对应 δ=0/+2/+3.2/+4.4；δ 参数值沿用既有 g3 脚本中的取值，先读 `scripts/_routeA_g3.py` 核实）：

```bash
# 对每个 δ，5 seeds × {oracle, mined16, tau18(=τ_used), constant18}
# constant18 用：--policy maxel --lead 18（先 --help 核实参数名）
```

- 汇总 `results/routeA_r2/oracle_ladder.json`：阶梯 = {no-knowledge, reward λ=8, mined τ*16, τ_used18, constant18, oracle} × {δ 四档} 的极区 HSR（mean ± sd, n=5 或 n=10）。
- 期望自检：oracle 臂 ≥ 全部非 oracle 臂；oracle 在 δ=0 时应显著高于 94.1（τ=20 臂），若 oracle ≈ 94–95 说明天花板接近，损失主要来自目标/窗口选择而非估计。

### E2. Lockbox 独立评估（填论文 [E2] 槽位；VI-A + 局限 7 翻转）

**协议（严格遵守 §1.3）**：标定输入在见到 lockbox 数据前全部冻结——挖掘规则（只用训练日志）、门判定（按原结果）、λ=8（按原选择）；唯一允许在"旧数据"上重做的是**验证窗口探测**（C3 的 `--window validation`），它不用 lockbox 数据。

1. **标定（在默认孪生的验证窗口上，一次）**：

```bash
for s in 0 4; do   # 2 个代表种子即可，τ* 是物理量不是策略量；若两种子不一致再扩到 5
  python scripts/probe_feasibility.py --run results/campaign_1023/almond_fixedarch_seed$s \
      --regime polar --episodes 8 --window validation \
      --out results/routeA_r2/lockbox_calib_val_seed$s.json
done
```

记录验证窗口探测给出的 τ*_val（预期 16 s）。**τ_used(lockbox) = min(τ*_val + 2, 24) = 18。此值一经确定不得再改。**

2. **构造 lockbox 孪生**：用 C1 的 `--epoch-doy`。基线 epoch_doy=292.25；取 **三个** lockbox 实例增加稳健性：`299.25`（+7 天）、`306.25`（+14 天）、`290.25`（−2 天），另各配 2 个交通种子（`--seed` 已存在，用 `--seed 100/200` 改变流量实例）。在 `results/routeA_r2/lockbox_twins.json` 记录每个实例的 (epoch_doy, seed)。

3. **lockbox 臂**（每个 lockbox 实例 × 每个臂 × 10 种子（有 checkpoint 的臂）；评估一次，不回头）：

| 臂 | 命令骨架 |
|---|---|
| full-system 无盾 | `eval_shield --run .../almond_fixedarch_seed$s`（lockbox 孪生参数） |
| full-system + mined16 | `--rule "min_advance:16@latitude_abs_deg>=68"` |
| full-system + τ_used18（标定盾） | `--rule "min_advance:18@latitude_abs_deg>=68"` |
| full-system + constant18 | `--policy maxel --lead 18`（核实参数） |
| PPO-MLP 无盾 | `--run results/campaign_1023/ppomlp_seed$s`（目录名先核实） |
| PPO-MLP + mined16 | 同上 + rule |
| reward λ=8 无盾 | `--run results/routeA_f3/lam8.0/no_forensics_seed$s` |
| reward λ=8 + mined16 | 同上 + rule |

4. **汇总**：`results/routeA_r2/lockbox_summary.json` + `lockbox.md`：按 lockbox 实例分组的 per-seed 极区 HSR；核心对比 = {full+mined16, full+τ_used18, ppomlp+mined16, lam8} vs 各自在默认评估窗口上的数字（既有，从 summary.json 读）——即"窗口内数字"对"独立窗口数字"。
5. **判定标准（写进 lockbox.md）**：若 full-system+盾 在全部三个 lockbox 实例上保持 ≥ ppomlp+盾 − 1pp 且排序（盾 > 无盾；full > ppomlp；λ=8 < 盾）保持，则 lockbox 验证通过，论文局限 7 从"遗留工作"改为"已完成，见 VI-A"；若不通过，如实报告并分析失败模式（这是论文的一部分，不是计划的失败）。

## 4. 产物与论文章节映射

| 论文槽位 | 位置 | 需要的产物 |
|---|---|---|
| [E1] | V.D 台账段、VI-B 因子化段、附录 C 表 C1 增列 | `factorial_tau18.json` + 同目录 τ16/20 重跑一致性证明 |
| [E2] | VI-A "Lockbox evaluation" 段、局限 7、（可能）摘要 | `lockbox_summary.json`、`lockbox.md`、`lockbox_twins.json`、`lockbox_calib_val_seed*.json` |
| [E3] | VI-G "Per-attempt oracle shield" 段 | `oracle_factorial_seed*.json`、`oracle_ladder.json` |
| [E4] | V.A 末段、附录 D 表 D1 与分层敏感性 | `km_support_audit.json/.md` |
| C5 | III 节 LLM 版本声明核对 | `llm_meta.json` |

## 5. 交付清单（自检后逐项打勾）

- [ ] `results/routeA_r2/REGRESSION.md`：C1–C5 每步改动前后默认路径数字（92.4 / 93.8 / 78.8）逐位一致记录
- [ ] `commands.log` 完整（时间戳 + 退出码）
- [ ] E1–E5 全部 JSON/MD 产物存在且字段齐全
- [ ] 旧目录零写入（用 mtime 抽查 `results/routeA*`、`results/campaign_1023/` 最近修改时间早于本计划时间）
- [ ] lockbox.md 含判定结论（通过/不通过 + 依据）
- [ ] 若 E4 发现 14–18 s 桶尝试数为 0 或与论文"thin, not empty"冲突：停下并在 REGRESSION.md 醒目标注（论文文本需回改）

## 6. 明确不做的事

- 不重训任何策略；不改 `results/routeA*` 既有汇总（SUMMARY.md、summary.json）——本轮结果由论文作者在下一轮统一合并进论文。
- 不在 lockbox 数据上做任何形式的模型/阈值/门/λ 选择。
- 不改 `scripts/km_setup_time.py`、`scripts/probe_gate.py` 的行为（只允许新增参数化，默认行为必须不变——回归闸保证）。
- 不生成论文 docx；只产出数据与报告。
