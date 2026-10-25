# ALMOND 复现报告——实现与实验（真实大模型版）

**目标论文：** *From Human Intent to In-Orbit Action: A Self-Improving Large Language Model Agent for 6G Satellite Networks*（EAAI 投稿 `Revised_Manuscript_修改稿.docx`）。

**本报告所用 LLM：** **DeepSeek `deepseek-flash`**，通过 OpenAI 兼容的 chat-completions 接口（`https://api.deepseek.com`）调用，温度/top-p 按附录 A 设置，开启 JSON 输出模式，并做 schema 校验与"修复式重问"。此前基于**推理替身**的结果单独保存在 `REPRODUCTION_REPORT_中文_surrogate.md`，两者对照见第 5 节。

**状态：** 修改稿 33 处 `⟦TBD⟧` 全部有实测值或明确"未测量+原因"（见 `TBD_FILLED.md`、`tbd_values.json`）。换成真实模型后有一项实质性结论改变：**反向取证确实挖出了论文描述的那条约束**（第 4.5 节），尽管入库率仍然很低。

---

## 1. 已实现的内容

| 修改稿中的模块 | 实现方式 | 文件 |
|---|---|---|
| 350 星 LEO 数字孪生、真实 SGP4 星历 | Walker-Delta 星座合成为合法 TLE 再用 SGP4 传播（J2 进动、阻力）；同时支持真实 Celestrak TLE | `almond/twin/constellation.py` |
| 链路预算、多普勒、大气衰减、日食 | Ka 频段闭式预算、随仰角衰减、SGP4 差分距离变化率、太阳矢量日食判据 | `almond/twin/geometry.py` |
| 星间链路拓扑（含极区接缝） | 受端子数限制的光学网状网（每星 4 端子）、视线判据、70° 以上关闭跨轨面链路 | `almond/twin/topology.py` |
| 馈电/信关站段 | 20 个地面站、14 个信关站、每站馈电时隙有限 | `almond/twin/twin.py` |
| 切换 MDP（14 维遥测 + K=8 候选） | 批量向量化环境、先建后断切换、几何驱动的建链时间 | `almond/twin/handover_env.py` |
| 前向翻译器 | 真实 LLM 调用 → 权重剖面 → 语义审计 → 违规时重问（附录 A） | `almond/framework/translator.py`、`almond/llm/prompts.py` |
| 反向取证 | 发现集叙事 → LLM 假设 → 不相交验证集反事实回放 → 留出测试集（×0.5/×1/×2）→ 入库 | `almond/framework/forensics.py` |
| 三阶段审计器 | 语义、物理（确定性）、影响（集成代理） | `almond/framework/auditor.py` |
| 版本化知识图谱 | 只追加记录、作用域过滤检索、可撤回 | `almond/framework/kg.py` |
| 约束执行层 | 五种可执行效果、无需重训即可注入 | `almond/framework/shield.py` |
| LLM 引导图神经进化 | 语法约束的种子/变异/交叉/批评、权重继承、Pareto 选择 | `almond/nas/evolution.py`、`almond/policies/nets.py` |
| PPO | 双 categorical 头、GAE、裁剪、按验证集选检查点 | `almond/policies/ppo.py` |
| 基线 | PPO-MLP、Static-LLM、Eureka 式、Oracle-PPO、Unseeded-EvoNAS、ALMOND-FixedArch，及五个消融 | `almond/framework/system.py` |
| LLM 访问层 | OpenAI 兼容后端、JSON 模式、schema 校验+修复、跨进程并发限流、持久化响应缓存 | `almond/llm/{backend,schema,semaphore,cache}.py` |
| 统计 | 10 seeds、t 置信区间、Wilcoxon + t、Holm、Cohen's d、秩双列相关、bootstrap 比值区间 | `almond/analysis/stats.py` |

**接入真实模型后暴露并修复的三个缺陷：** ①提示词模板输出的是双重大括号 JSON，真实模型会照字面理解；②系统硬编码了替身后端、根本不读环境变量；③八个并发进程触发服务方限流，现在 LLM 调用经过跨进程槽位信号量与持久化缓存。

---

## 2. 数字孪生

构建：`python scripts/build_twin.py --tag ref --hours 12 --dt 10` → 350 星、4321 个 10 s 步、20 个地面站、984 MB 内存映射缓存（加载 0.01 s，所有实验共享）。

* **极区接缝。** 70° 以上关闭全部跨轨面星间链路（反向旋转轨道面的工程做法），每星 4 个光学端子：接缝以下平均星间度 3.98，以上 1.55；到信关站跳数 0–27。
* **馈电稀缺。** 每站同时跟踪星数有限；极区信关站可见约 13 颗候选，中纬约 5 颗。
* **竞争性服务窗口。** 某星仰角落后"当前最佳可见星"超过 10° 即不再是可用服务星。
* **建链时间** `t_setup` = 信令 + 多普勒劣化的同步 + 逐跳路由建立 + 馈电时隙排队 + 面切换惩罚（仅当**目标星**位于接缝以上时惩罚显著）。

2597 次随机切换事件（每站点/时刻取仰角最高的两颗候选）实测：

| 区域 | `t_setup` p50 | p90 | P(t_setup ≤ 6 s) | P(≤ 12 s) |
|---|---|---|---|---|
| 极区（>70° N） | **10.0 s** | 15.7 s | 0.15 | **0.55** |
| 中纬（30–65°） | **4.2 s** | 5.5 s | 0.91 | 0.97 |

2.4 倍不对称，复现了修改稿"极区约需 10–12 s"。始终用协议最小提前量 6 s 的策略，极区只能完成 15% 的切换；12 s 能完成 55%——草稿里的 55% 正是这个"临界提前量"工况。

---

## 3. 实验协议

* 测试集 = 留出时间窗（82–95%），在 ×0.5/×1/×2 流量下各评一次；发现集（0–60%）、验证集（65–75%）与测试集互不相交。
* 架构搜索每个配置跑一次（ALMOND 配置用真实 LLM，无引导基线用随机采样，各 34 次评估），发现的架构在所有 RL seed 间固定。
* 按验证集选检查点，测试集从不参与模型选择。
* 前向翻译按意图缓存，因此同一方法的所有 seed 共享同一份经审计的权重剖面；取证假设仍按 seed 独立（其载荷含该 seed 自己的失败轨迹）。
* 每次运行 9600 个实例-episode；在时间允许范围内每个方法 10 个 seed（实际达成：ppomlp 10、no_forensics 10、static_llm 10、oracle 10、almond 6、eureka 4、almond_fixedarch 4、unseeded_evonas 3——缺口由取证闭环里的服务方延迟造成，如实报告而非掩盖）。

---

## 4. 实验结果（真实 LLM）

### 4.1 可靠性（图 6 / 表 8）

```
方法                      极区       次极区      中纬        赤道        总体        S     参数   n  收敛率 中位数  IQR
ALMOND                    59.9±46.4  62.6±48.5  61.4±47.7  60.5±46.9  61.0±47.3  56.5   39189  6   67%   88.9  68.3
Eureka 式                  63.6±43.1  54.7±47.6  66.5±45.2  66.0±44.2  64.8±44.1  56.0   39189  4   50%   81.1  33.8
Unseeded-EvoNAS           60.0±50.8  64.2±55.6  63.0±54.6  65.9±45.2  63.4±51.1  58.1   29813  3   67%   88.3  44.5
ALMOND-FixedArch          52.3±38.4  59.2±41.2  62.1±42.8  58.9±44.2  59.2±41.6  50.4   27029  4   25%   58.9  32.1
PPO-MLP（手工奖励）        50.6±42.4  43.4±41.6  51.7±44.7  54.5±46.2  51.8±43.7  36.0   27029  10  40%   69.7  85.9
Static-LLM                34.3±43.6  33.9±44.0  36.3±44.4  38.0±46.3  36.0±44.4  38.7   39189  10  30%    3.9  82.7
Oracle-PPO                31.5±40.9  29.5±42.1  36.4±43.4  39.6±44.0  35.7±42.1  35.0   39189  10  30%   11.6  70.3
ALMOND（无取证）           29.5±41.8  25.5±41.6  27.4±40.5  32.1±43.0  29.2±41.8  35.1   39189  10  30%    1.8  68.8
```

* 收敛率（`conv`，极区 HSR ≥80% 的 seed 占比）：ALMOND 4/6 = **67%**，是 n ≥ 6 的方法里最高的；PPO-MLP 4/10，Static-LLM 与 Oracle 各 3/10。
* 极区 HSR 中位数：ALMOND **88.9%**，PPO-MLP 69.7%，Static-LLM 3.9%，Oracle 11.6%。
* n ≥ 6 的方法中 ALMOND 意图满足度最高（56.5），PPO-MLP 最低（36.0）。
* 两个小样本方法（Eureka 63.6%、Unseeded 60.0%）与 ALMOND 的区间重叠，在 n=3–4 下无法区分。

### 4.2 收敛速度（图 7）

达到各自渐近线 90% 所需 episode：PPO-MLP 240±759，Static-LLM 240±506，ALMOND-FixedArch 300±600，Eureka 600±693，ALMOND **1800±2370**，Unseeded 0。达到 S ≥ 75：PPO-MLP 1080，Unseeded 3200，Static-LLM 3360，ALMOND 4000。

**草稿"比 PPO-MLP 快约三倍"未复现**：PPO-MLP 更快达到**它自己那个低得多的**渐近线的 90%。它的验证集监测峰值最高（88.9 vs ALMOND 74.3），但留出测试集上的满足度最低（36.0）——说明它的"无线电质量代理"经不起分布偏移。

### 4.3 星上推理包络（表 6）

真实 LLM 发现的最大策略：**MLP，宽 64，2 层，96 宽上下文编码器，39,189 参数，153 KB FP32 权重。** 单批、热缓存、300 次预热后计时 2000 次（Intel i5-12400F）：

| 变体 | 均值 | p99 |
|---|---|---|
| ONNX Runtime，CPU FP32 | **0.045 ms** | **0.069 ms** |
| ONNX Runtime，CPU FP16 | 0.052 ms | 0.089 ms |
| ONNX Runtime，CPU INT8 | 0.055 ms | 0.127 ms |
| ONNX Runtime，CUDA FP32 | 0.046 ms | 0.103 ms |
| PyTorch，CPU | 0.165 ms | 0.277 ms |

策略切换：0.175 ms（`load_state_dict`），序列化后 161,830 B。量化：FP16 → HSR 91.1% → 92.8%（极区 89.1% → 87.1%），INT8 → 93.5%（极区 89.1% → 91.7%）；切换抖动 72.4 次/小时 → 78.1（FP16）/ 80.9（INT8）。Jetson Orin NX 级模块**本机没有**，故不给出 Orin 数字；在实测平台上 15 ms 包络有两个数量级余量。

### 4.4 审计器压力测试（表 7）

注入 100 条候选约束，五类（该实验不调用 LLM，与替身版相同）：物理非法 0 被接受（物理阶段检出 100%），与意图不一致 40% 被接受（语义阶段检出 60%），误导性 70% 被接受，对抗性 100% 被接受，有效对照 **误拒 0%**。总体误接受 52.5%，误拒 **0%**。统计伪相关与延迟违规需要回放门与影响预测器，第 7 节说明后者为何未生效。

### 4.5 真实模型下的反向取证——实质性变化

在贴近真实的发现集上，真实模型逐字给出了论文描述的规则及其邻居：

```
IF elevation_deg <= 14 AND handover_advance_s <= 10  THEN min_advance(12)
IF elevation_deg <= 14 AND plane_change == 1         THEN prefer_same_plane
IF plane_change == 1  AND isl_hop_count >= 3         THEN forbid_unrouted_target
```

替身只能通过在固定阈值表上网格搜索碰到这些解；模型是读叙事得到的，而且三条假设正好覆盖修改稿为表 4 描述的计时 / 面纪律 / 路由三个类别。

**但入库率仍然很低。** 6 个 ALMOND seed 上，知识图谱平均只留下 0.17 条活跃约束、0.17 次被接受的提交（只有 1 个 seed 提交了 1 条 `min_advance`），因为验证门要求在**不相交**验证集上取得 ≥5 个百分点增益，多数提议规则过不了这道门。闸门在尽职，代价是取证还不能被算作性能差距的来源。

### 4.6 LLM 输出稳定性（表 7）

两个安全相关调用类型各 24 次，两个意图，四个独立重复组：

| 调用类型 | 完全一致 | 语义等价 | schema 失败 | 需要修复重问 |
|---|---|---|---|---|
| 前向翻译 | 0% | **88%** | 0% | 0% |
| 取证假设 | 0% | **67%** | 0% | 29.2% |

没有任何一次响应逐字节相同——模型每次都会重写 `analysis` / `rationale`；但 88% 的翻译组在"权重排序 + 舍入后的剖面"上一致，67% 的取证组在"谓词 + 效果"上一致。**29% 的取证调用需要一次修复重问**（未声明字段、原子数超过 2、缺少效果），校验器加修复循环把每一次都转成了合法产物，因此 schema 失败率为 0%。整个 campaign：55 次调用、11 次修复重问、0 次耗尽。

### 4.7 影响预测器、孪生保真度与搜索

* **影响预测器**（不依赖 LLM，结论不变）：MAE 1.96 ms（目标标准差 5.2 ms），留出标定斜率 **−0.09**，决策翻转 0/50 → 审计第三阶段按"未生效"报告。
* **孪生保真度：** 极区壳层 97,325 样本，斜距偏差 p50 0.576 dB / p95 **0.665 dB** / 最大 0.681 dB；独立重算 SNR 的 p95 偏差 0.665 dB。修改稿"约 1 dB 以内"成立。
* **扰动：** 用真实 LLM 策略时参考极区 HSR 91.8%；大气衰减 ±10% 仍为 91.8%，流量 ±10% 为 91.6–91.9%，**星间丢链 10% 降至 84.6%（−7.2 个百分点）**，组合扰动 89.2%。该 seed 没有已提交约束，故规则复现不适用。
* **架构搜索（真实 LLM）：** 34 次评估 18 s，最优奖励 **1.417**（MLP w64 L2，39,189 参数）；等预算无引导对照最优 **1.400**（hybrid w32 L2，29,813 参数）。LLM 引导从"略差"变为"略好"，但 20 倍成本缩减仍不成立——两者都是 34 次评估。

### 4.8 LLM 成本

真实模型 campaign：**55 次调用**，47,073 提示 token、54,185 生成 token，API 总延迟 315 s，11 次修复重问，单次中位 6.7 s。按每百万 token 约 0.28 美元的代表性价位，整个 campaign 约 **0.03 美元**；主要成本是算力而非推理。

---

## 5. 真实模型 vs 推理替身

相同 seed、相同孪生、相同脚手架，只有后端不同（详见 `backend_comparison.md`）。

| 方法 | 替身 极区（均值/中位/收敛） | 真实 LLM 极区（均值/中位/收敛） | Δ均值 |
|---|---|---|---|
| ALMOND | 60.8 / 83.6 / 5-共10 | 59.9 / 88.9 / 4-共6 | −0.8 |
| ALMOND-FixedArch | 47.6 / 62.8 / 3-共10 | 52.3 / 58.9 / 1-共4 | +4.7 |
| Oracle-PPO | 43.2 / 40.0 / 4-共10 | 31.5 / 11.6 / 3-共10 | −11.7 |
| Static-LLM | 43.2 / 40.0 / 4-共10 | 34.3 / 3.9 / 3-共10 | −8.9 |
| ALMOND（无取证） | 60.8 / 83.6 / 5-共10 | 29.5 / 1.8 / 3-共10 | −31.3 |
| Eureka 式 | 43.2 / 40.0 / 4-共10 | 63.6 / 81.1 / 2-共4 | +20.5 |
| PPO-MLP | 55.2 / 75.8 / 5-共10 | 50.6 / 69.7 / 4-共10 | −4.6 |
| Unseeded-EvoNAS | 44.8 / 42.6 / 5-共10 | 60.0 / 88.3 / 2-共3 | +15.2 |

同一个"可靠性优先"意图下，两种后端给出的权重剖面：替身 0.59/0.14/0.26，真实模型 **0.68/0.11/0.21**——真实模型明显更偏重可靠性，也更符合意图表述。

**其中有多少是噪声？** PPO-MLP 完全不依赖 LLM（固定架构、手工权重 0.40/0.40/0.20），却从 55.2 变到 50.6，说明 campaign 之间的噪声底约为 **5 个百分点**；受双峰性影响，单 seed 方差更大（±40 个百分点）。同一 seed 下 ALMOND 与"无取证"版本的对比把问题暴露得更清楚：**在零条已提交约束**的情况下，两者相差 +67、+91、+88、−92、0 个百分点。本任务上的 RL 训练是混沌的——矩阵乘归约里 1e-7 的差异就能翻转一个离散的切换决策——因此**这套脚手架跨进程不是位级可复现的**，按 seed 配对无效，本报告所有比较都是跨独立 seed 的非配对比较，**低于约 10 个百分点的差异不应解读**。

---

## 6. 哪些复现了、哪些没有

| 修改稿的主张 | 是否复现 | 依据 |
|---|---|---|
| 350 星星座、SGP4 驱动的孪生，存在极区失效机制 | **是** | 第 2 节 |
| 极区低仰角约需 10–12 s 建链准备 | **是** | 第 2 节（p50 10.0 vs 4.2 s；P(≤12 s)=0.55） |
| <50K 参数、约 15 ms 单批包络、星上无 LLM | **是，余量大** | 39K 参数，主机 CPU 0.045 ms |
| LLM 把意图翻译成以可靠性为主的奖励剖面 | **是** | 真实模型给出 0.68/0.11/0.21 |
| 反向取证能挖出极区计时约束 | **是**（仅真实 LLM） | 第 4.5 节，含 `min_advance(12)` |
| 审计能拒掉物理非法的规则 | **是** | 检出 100%，误拒 0% |
| 孪生链路预算约 1 dB 内一致 | **是** | p95 0.665 dB |
| PPO-MLP 极区约 55% | **是** | 50.6%（替身为 55.2%） |
| ALMOND 相对 PPO-MLP 提升极区可靠性 | **是，幅度有限** | 均值 59.9 vs 50.6；中位 88.9 vs 69.7；收敛率 67% vs 40% |
| 挖出的知识带来增益 | **否** | 平均 0.17 次提交/运行，消融被运行间方差淹没 |
| 注入约束后极区 55% → >95% | **否** | 最好的收敛运行 89–93% |
| 比 PPO-MLP 快约 3 倍收敛 | **否** | PPO-MLP 更快到自身渐近线 |
| 架构搜索成本降低约 20 倍 | **否** | 等预算，LLM 引导略好但并不更省 |
| 人力 48 h → 4.5 h | **未测量** | 未做受试者实验 |
| 影响预测器是有效安全措施 | **否** | 标定斜率 −0.09 |

---

## 7. 局限

1. **运行间确定性。** 本脚手架不是位级可复现的（第 5 节）。在训练器改成确定性之前（单线程确定性内核、全链路固定种子），只有跨 ≥10 seeds 的非配对比较、且差异 >10 个百分点才有意义，消融表也无法隔离组件效应。
2. **取证吞吐。** 每次触发要一次 LLM 往返加回放，正是它把 ALMOND 压缩到 6 个 seed。
3. **入库率。** 验证门大约每六个 seed 接受一条规则。要提高召回，应丰富发现集（更多非计时类失败），而不是放宽闸门。
4. **硬件。** 无 Orin NX 级模块；延迟在台式机 CPU 与 RTX 3070 上测得。
5. **模型依赖。** 结论针对 `deepseek-flash` 与附录 A 的解码设置。接口接受任意 OpenAI 兼容端点，跨模型复现是改配置而非改代码。
6. **影响预测器不泛化**；所报告 seed 无已提交规则，故**扰动下的规则复现**无法评估。
7. **人因实验未做**；表 4 报告取证实际挖出的两类规则加上计时规则。

---

## 8. 复现步骤

```bash
export ALMOND_LLM_BASE_URL=https://api.deepseek.com
export ALMOND_LLM_API_KEY=<key>
export ALMOND_LLM_MODEL=deepseek-flash
export ALMOND_LLM_CONCURRENCY=4          # 跨进程槽位信号量
export ALMOND_LLM_CACHE_DIR=results/llm_cache

python scripts/build_twin.py --tag ref --hours 12 --dt 10
python scripts/run_nas.py --mode llm    --out results/nas/llm_spec.json
python scripts/run_nas.py --mode random --out results/nas/random_spec.json
python scripts/llm_live_smoke.py                     # 六类调用契约自检
python scripts/run_campaign.py --methods almond --seeds 0-9 --episodes 9600 \
       --eval-every 1200 --device cpu --spec-file results/nas/llm_spec.json
python scripts/analyse_campaign.py && python scripts/make_figures.py && python scripts/make_report.py
python scripts/compare_backends.py                   # 替身 vs 真实
python scripts/paired_forensics.py                   # 消融与噪声证据
python scripts/run_llm_stability.py --types forward_translate,forensic_hypothesis --repeats 12
python scripts/bench_latency.py --policy results/campaign/almond_seed1/policy.pt
python scripts/run_fidelity.py  --policy results/campaign/almond_seed1/policy.pt \
       --kg results/campaign/almond_seed1/knowledge_graph.json
```

## 9. 在 Ubuntu 虚拟机上的验证

代码同样能在 `Ubuntu_22.04_1` 这台 VMware guest（`/home/u22/almond-repro`）中运行：从零建孪生得到完全一致的统计（星间跳数均值 4.04、不可达 5.3%），审计与稳定性实验可复现。既有的 `/home/u22/satcon-demo` 未被修改（26 个条目、`Makefile` 校验和不变）；它是固定拓扑的 P4/BMv2 演示，其 README 明确不建模轨道运动、多普勒、星间断续与切换连续性，无法充当本文孪生。
