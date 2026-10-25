# ALMOND 复现实验证据包（Route A：机制论文）

> 2026-10-23。本文件只做一件事：把"可以写进论文的每一条主张"和"支撑它的实验、数字、产物"一一对上，
> 并在每条后面标明**审稿人会怎么攻击**。理论全文见 `THEORY_TFA.md`，这里是可交付的清单。

---

## 0. 一句话定位

> LEO 切换的可靠性由一个**可识别、可注入、可转移的可行性阈值**决定；
> 策略与架构搜索几乎不贡献；本文给出该阈值的自动获取（删失估计）、
> 可审计注入（决策盾而非奖励项）与跨意图转移（共享知识图谱）。

**不能写的话**：我们的智能体学得更好 / 我们的策略更优 / 端到端性能领先。
理由见 §3 的 E12 常数基线。

---

## 1. 主张 → 证据 → 产物

| # | 主张 | 关键数字 | 产物 | 攻击点（已自曝） |
|---|---|---|---|---|
| A1 | 极区失效是**计时可行性**问题，不是学习能力 | 晚切换率 22.0%（Oracle/Static）→ 0.6%（ALMOND）；盾前两臂 71.8 vs 68.4 | E2/E6，`campaign_1023/` | "你怎么排除是策略差"：E2 用同权重同 rollout 对照 |
| A2 | 约束盾把可行性恢复成**策略无关** | 10 个独立策略 τ=16 时全部 92.4±0.1；随机策略+盾 89.1 | E2/E3，`factorial_matched.json` | 只测了极区；中纬仍依赖选星 |
| A3 | LLM 恢复的幅值 ≈ 该区域 **p95** | 10/10 seed 都给 16 s；KM p95=15.80 s | E4/E11，`km.json` | 谓词（纬度 64–70/全局）不稳定 |
| A4 | LLM 幅值**不随物理漂移** | +2 s 信令后仍 16 s，掉 2–5.6 pp | E7，`campaign_sig32/` | 这是负面结果，必须写 |
| A5 | 探测+等渗**能跟随物理**，但**必须在部署策略上探测**；朴素 in-loop 探测（早期策略）逐 seed 失败率 2/5（G4），改为部署后探测 + m=2 后 5/5 到天花板（H2） | ref 0 损失；sig32 +3.3 pp；H2 的 m=2：ref 94.0 / sig32 93.9 / drift 93.9 | E8 + G4 + H2，`campaign_pcs3_*`、`routeA_g4/`、`routeA_h2/` | 早期策略探测是根因，episode 数不是（G4 已证） |
| A6 | **注入方式**决定成败 | 同一知识：奖励惩罚 72.1±9.3 vs 决策盾 93.6±0.7（+21.5 pp） | E9，`campaign_penalty/` | λ 只扫了 1.0（2 seed 扫过 0.3） |
| A7 | 约束**跨意图转移** | 共享 KG：时延/功耗/平衡 +19.7/+28.2/+22.6 pp（n=4） | E14，`multi_shared_*/` | n=4；需要"验证门会拒"的对照 |
| A8 | **常数基线追平**学习系统 | max-elevation+18 s：94.0±0.7（ALMOND 93.6±0.7） | E12/E16，`fig_gap_decomposition.png` | 这是论文必须正面处理的最强反证 |
| A9 | 反事实验证门过滤掉**会变差**的候选 | 6 个自然候选中 4 个 Δ_test < 0；门全部拒绝 | E18，`gate_probe.json` | 门本身有噪声（见 A10） |
| A10 | 门有两个缺陷：估计噪声 ±2.2 pp（2 episodes）；用早期策略估计，与部署价值相关性弱 | 2 ep → ±2.2；8 ep → ±0.6；seed0 门测 +10.6% vs 部署 +1.4%；seed1 门测 30.9% vs 部署 45.6% | E19，`gate_noise.json` | 自曝项，审稿人复现必然发现 |
| A11 | 手写 oracle 规则（修正 bug 后）仍然不够 | 78.0±12.2 vs 挖掘规则 93.6±0.7 | E15，`campaign_oracle_fixed/` | 只测了一种手写规则 |
| A12 | **验证门在多意图协议中的因果价值**：同一条有害候选，门开 71.9 / 门关 51.3 | +20.5 pp，5/5 配对同向，Wilcoxon p=0.0625（n=5 最小值） | F2，`routeA_f2/` | 计划指定的 8 s 规则实测无害（+0.2），改用 `cap_advance:6` |
| A13 | **奖励注入是剂量-反应，不是"无效"**：λ=0/0.3/0.5/1.0/2.0/8.0 → 71.8/74.0/74.3/72.1/79.7/84.4 | λ=8 仍比盾低 9.2 pp，方差大 10 倍（6.8 vs 0.7） | F3，`routeA_f3/` | 原 A6 的"惩罚无效"表述**必须改写** |
| A14 | **探测阈值有 ±2 s 的内在不可辨识区间**：τ\* 的 run-to-run sd = 2.45/2.83/1.10/1.10（2/4/8/16 ep） | 且系统性偏低（14–16 而非 16）；桶内 bootstrap 低估方差 | F4，`routeA/f4_probe_convergence.json` | **G4 进一步证伪了"加到 8 就好"**，见 A21 |
| A15 | **常数的失效边界**：+2 s 只掉 0.6 pp，+3.2 s 掉 7.3 pp，+5.6 s 掉 13.3 pp；按 τ\* 校准始终在天花板 | 固定 18 s：93.3 → 92.4 → 86.0 → 83.6 → 80.0；校准：92.4 → 92.4 → 93.2 → 93.2 → 92.9 | F1/F1b，`routeA_f1/` | 论文须按"有 2 s 安全余量"表述 |
| A16 | **替代物理下方向不变**：no-seam 孪生上盾前 70.9/61.4 → 盾后 96.1/95.8 | late 失效 26.0%/35.4% 仍是主导类 | F5，`routeA_f5/` | 只测了两个替代物理；almond 在该物理下未触发取证 |
| **A17** | **验证门（干净设计）**：追加式注入下，门开 92.1 / 门关 49.2；门开与无注入差 +0.4 pp | **+42.9 pp**（5/5）；替换式扩到 n=10 为 **+19.1 pp，p=0.0020** | G1，`routeA_g1/` | 门关臂靠"提交全部候选"实现，属设计选择 |
| **A18** | **λ 的最优在 λ=8（84.4），之后下降**（16:81.8 / 32:81.2 / 64:74.5）；盾 (93.6, S=77.8) 在 (HSR,S) 上支配全部 λ 点 | 盾 HSR 高 9.2 pp、S 高 5.5、方差小 10 倍 | G2，`routeA_g2/` | 只测到 λ=64；更大 λ 未测 |
| **A19** | **常数边界的多 seed 复现**：漂移 0/+2/+3.2/+4.4 → 常数 94.1/93.2/87.7/86.1，校准 94.1/93.2/94.0/94.0 | 拐点在 +2 与 +3.2 s 之间，3 seeds 一致 | G3，`routeA_g3/` | 3 seeds；τ\* 精准是这批抽样的运气（见 A14） |
| **A20**（已降级） | **奖励注入的知识在漂移下退回无知水平**：+2 s 下 55.4 vs 无知识 58.1 | 标称 84.4（+5.5 pp），漂移后 −2.7 pp（逐 seed sd 17.9）；分布**更宽**（sd 4.01）而非更窄 | H1，`routeA/h1_advance_dist.json` | 原"−29 pp 是最脆弱形态"的说法**已删除** |
| **A21** | **probe_episodes=8 反而更差**：ref 92.8（τ=14,16,14）vs 93.4；sig32 90.6（2/5 给 16）vs 91.6；每低一个平台点 ≈ −4.8 pp | 探测成本仅 0.46%（2 ep）/1.83%（8 ep）训练步数 | G4/G4b/G5，`routeA_g4/` | 推翻 F 阶段的"用 8"建议；PCS 不能声称稳定给出正确阈值 |
| **A22** | **惩罚脆弱性的机制被证伪**：λ=8 的提前量分布**更宽**（sd 4.01 vs 3.06）、均值更高（10.21 vs 9.54 s），不是被压窄 | 漂移下 55.4 vs 58.1（−2.7 pp，sd 17.9）≈ 无知 | H1，`routeA_h1/` | 该臂标称 +5.5 pp，漂移后归零 |
| **A23** | **保守校准**：探测部署策略 + m=2 是最小可用余量，无 seed 回退 | ref 93.4→94.0、sig32 93.4→93.9、drift 93.9→93.9；m=4 不更优 | H2，`routeA_h2/` | 余量是保险不是收益；收益仅 0.5–0.6 pp |
| **A24** | **5 seeds 的漂移曲线**：+3.2 s 起常数 89.0±2.1，校准 93.9±0.7；+4.4 s 为 87.7±2.7 vs 93.3±1.4 | 拐点稳定在 +2…+3.2 s | H3，`routeA_g3/`+`routeA_h3/` | seed4 在 +4.4 处探测低一档（91.1） |

---

## 2. 差距分解（论文的核心图）

```
PPO-MLP（只有奖励）                72.6 ± 16.1
同一知识写进奖励（λ=1.0）           72.1 ±  9.3
PPO-MLP 策略 + 决策盾              91.8 ±  1.1
max-elevation + 18 s（不学习）      94.0 ±  0.7
ALMOND（学习策略 + 盾）             93.6 ±  0.7
```

读法：**21 pp 里约 19 pp 来自"有没有可行性约束"，2 pp 来自策略/标定，而常数把最后 2 pp 也吃掉。**
论文的贡献因此必须落在"约束从哪里来、怎么注入、能不能复用"，而不是"策略更好"。

---

## 3. 必须写进 Limitations 的四件事

1. **常数基线**：max-elevation + 18 s 达到 94.0±0.7，高于 ALMOND。任何"性能领先"的措辞都不成立。
2. **策略无关性**：盾前 ALMOND 与 PPO-MLP 的策略无差别（71.8 vs 68.4），训练权重不受取证影响
   （`best_state` 从未被恢复，`policy.pt` 是最后一轮）。
3. **单意图消融无效**：`no_memory` / `no_counterfactual` 在单意图协议下与 ALMOND 逐位相同；
   它们的价值只能在多意图协议（A7）里体现。
4. **早期准备在本孪生里近乎免费**：双连接代价相对一次掉线（0.30 惩罚 + 6 步离线）小两个量级，
   最优提前量饱和到上界；把 KPI 从 p95 换成均值只把 S 从 78.4 改到 78.8。
   **代价系数从 0 扫到 150 ms/s，最优提前量始终是 18 s**（c≥20 后完全饱和，因为
   受影响步的 `n_lat` 已触底）。这不是"度量选得不好"，是经济学本身的不对称。

---

## 4. 复现命令（每条主张都能重跑）

```powershell
# 环境自检
python scripts/check_env.py

# E2/E3 冻结策略 × 盾（20 策略 × 3 条件）
python scripts/eval_shield.py --run results/campaign_1023/almond_seed0 --rule "min_advance:16@latitude_abs_deg>=68"

# E7/E8 物理扰动 + PCS
python scripts/run_campaign.py --methods almond --seeds 0-4 --episodes 9600 --eval-every 1200 `
    --device cpu --spec-file results/nas/llm_spec.json --acq-signaling 3.2 --probe-calibrated `
    --out results/campaign_pcs3_sig32

# E9 惩罚 vs 盾
python scripts/run_campaign.py --methods no_forensics --seeds 0-9 --episodes 9600 --eval-every 1200 `
    --device cpu --spec-file results/nas/llm_spec.json --late-risk-tau 16 --late-risk-weight 1.0 `
    --out results/campaign_penalty

# E14 多意图共享 KG
python scripts/run_multi_intent.py --mode shared --seed 0

# E16 差距分解图
python scripts/make_gap_figure.py
```

### 4.1 路线 A 追加实验（A12–A16）

```powershell
# F1 常数 × 物理扰动（+2 s）与漂移幅度扫描
python scripts/_routeA_f1.py
python scripts/_routeA_f1b.py

# F2 验证门价值（多意图 + 注入有害候选 + 关/开验证门）
python scripts/run_multi_intent.py --mode shared        --seed 0 --inject-bad-rule "cap_advance:6@latitude_abs_deg>=68" --out results/routeA_f2/g_shared_gate_s0
python scripts/run_multi_intent.py --mode shared_nogate --seed 0 --inject-bad-rule "cap_advance:6@latitude_abs_deg>=68" --out results/routeA_f2/h_shared_nogate_s0

# F3 λ 剂量-反应（0.3 / 0.5 / 2.0 / 8.0，各 10 seeds）
python scripts/run_campaign.py --methods no_forensics --seeds 0-9 --episodes 9600 --eval-every 1200 `
    --device cpu --spec-file results/nas/llm_spec.json --late-risk-tau 16 --late-risk-weight 8.0 `
    --out results/routeA_f3/lam8.0

# F4 探测阈值收敛（2/4/8/16 episodes × 5 repeats）
python scripts/_routeA_f4.py --run results/campaign_1023/almond_seed0 --episodes 2,4,8,16 --repeats 5

# F5 替代物理（no-seam / feeder-3，3 臂 × 5 seeds）
python scripts/_routeA_f5.py --configs noseam,feeder3

# Phase G 追加（A17–A21）
python scripts/run_multi_intent.py --mode shared        --seed 0 --inject-bad-rule-extra "cap_advance:6@latitude_abs_deg>=68" --out results/routeA_g1/i_clean_gate_s0
python scripts/run_multi_intent.py --mode shared_nogate --seed 0 --inject-bad-rule-extra "cap_advance:6@latitude_abs_deg>=68" --out results/routeA_g1/i2_clean_nogate_s0
python scripts/run_campaign.py --methods no_forensics --seeds 0-9 --late-risk-tau 16 --late-risk-weight 64 --out results/routeA_g2/lam64
python scripts/_routeA_g3.py
python scripts/run_campaign.py --methods almond --seeds 0-4 --acq-signaling 3.2 --probe-calibrated --probe-episodes 8 --out results/routeA_g4/pcs8_sig32
python scripts/_routeA_g2b_g4b.py
python scripts/_routeA_g1_analysis.py
python scripts/_routeA_g_summarise.py

# Phase H 追加（A22–A24）
python scripts/_routeA_h1.py
python scripts/_routeA_h2.py
python scripts/_routeA_g3.py --seeds 3,4 --out-dir routeA_h3 --table h3_drift_table_s34.json
```

---

## 5. 若要争取"方法优越"（Route B）的最小可行设计

结论是：**必须让"早期准备"在评价指标里真正昂贵**，且昂贵程度随区域/负载变化。
可辩护的做法只有一条——把代价记成**累积能量**（可加量，不受 p95/均值稀释），
并让双连接的能耗依容量占用率变化（容量紧张区更贵）。这样：

* 极区（容量充裕，但建链慢）→ 最优提前量 ≈ 16–18 s；
* 赤道（容量紧张，建链快）→ 最优提前量 ≈ 6–8 s；
* 任何单一常数在两侧都会付代价，区域自适应（或按区域标定）才有净增益。

代价：约 2–3 天实现 + 全部关键实验重跑（约 3 小时机器时间），
且必须在论文中把能耗模型作为**设计选择**明确声明。
