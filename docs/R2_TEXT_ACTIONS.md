# R2 之后论文需要改的地方（逐槽位）

> 2026-10-24。本文件只列修改点与可用的数字，不改论文正文（下一轮统一合并）。
> 数据来源：`results/routeA_r2/R2_REPORT.md`、`lockbox_summary.json`、`oracle_ladder.json`、
> `factorial_tau18.json`、`km_support_audit.json`、`llm_meta.json`。

## 1. [E1] 阈值台账：补 τ=18 行（V.D 台账、VI-B、附录 C 表 C1）

在 τ=16 与 τ=20 之间插入部署行：

| 阈值 τ（@lat≥68） | 极区 HSR（10 seeds） | sd | 晚切换占比 |
|---|---|---|---|
| 16 s（挖掘值 τ\*） | 92.43 | 0.30 | 0.87% |
| **18 s（τ\* + m=2，部署值）** | **93.31** | **0.26** | **0.00%** |
| 20 s（τ\* + m=4，上界） | 93.17 | 0.26 | 0.00% |

要点：**τ=18 高于 τ=20**，为"m=2 是最小可用余量、再大开始用窗口换晚切换"提供直接证据。
同一性：在归档臂上重跑 τ16/τ20 与 `verify_1023/factorial.json` **逐位一致（10/10，Δ=0.0）**。

## 2. [E2] VI-A 新增 "Lockbox evaluation" 段；局限 7 翻转

**协议两句**：标定（挖掘规则、门、λ=8）在看到任何 lockbox 数据前冻结；唯一重做的是
**验证窗口**探测（τ\*=16，seed 0/4 一致），得 `τ_used = 18 s`。

| 实例（epoch_doy） | full 无盾 | full+τ18 | ppomlp+16 | λ=8 |
|---|---|---|---|---|
| +7 d（299.25） | 68.37 ± 15.11 | **92.93 ± 0.97** | 91.89 ± 1.59 | 81.83 ± 9.55 |
| +14 d（306.25） | 71.12 ± 15.94 | **94.80 ± 1.01** | 93.62 ± 1.60 | 84.41 ± 7.34 |
| −2 d（290.25） | 72.47 ± 13.16 | **94.24 ± 0.82** | 93.04 ± 1.33 | 84.49 ± 7.24 |

- 四条排序（盾>无盾、full>ppomlp、full+18 ≥ ppomlp+16−1、λ8<盾）在 **3/3** 实例成立；
- 换交通实例（eval seed 100/200）后排序不变（full+τ18 94.53–96.18 vs ppomlp+16 93.58–95.42）；
- 晚切换率在三个实例上均为 **0.00%**。

**局限 7 改写**：从"测试集泄漏只披露未解决"改为
"**已在三个独立轨道相位（±2/7/14 天）与两个交通实例上复核，排序保持；领先幅度 +0.9–1.2 pp 属小效应**"。
摘要若要提，只能一句："an independent-epoch lockbox preserves every ordering"。

## 3. [E3] VI-G 新增 "Per-attempt oracle shield" 段

句式建议：oracle 是"若逐次知道真实建仓需求"的上界参照。

| δ | oracle | τ18 | mined16 | constant18 |
|---|---|---|---|---|
| 0 | 93.41 | **93.41** | 92.50 | 93.33 |
| +2.0 | 93.41 | 92.47 | 85.09 | 92.39 |
| +3.2 | 93.41 | 86.08 | 82.03 | 85.98 |
| +4.4 | 93.41 | 83.67 | 78.28 | 83.56 |

**必须写的一句（这是新证据）**：标称物理下部署阈值与 oracle **完全相同**（93.41），
即估计环节在标称下无改进空间，剩余损失（约 6.6 pp）全部来自目标/窗口/路由；
漂移下差距打开（+4.4 s 时 9.7 pp），这才是"固定阈值"的代价、也是重新探测的理由。

## 4. [E4] V.A 末段 + 附录 D 表 D1 —— **必须改写的句子**

原句（"朴素估计 4.08 s vs KM 6.45 s，这 2.4 s 就是看不见的机制"）**不能原样保留**，因为：

- 4.08→6.45 只在 **lat≥70 + 全部 8 臂** 时成立，且主要由未学约束的基线臂贡献；
- **部署臂内部**是 6.47→6.96（**0.49 s**）；
- **分层内部**偏差 0.02–0.20 s；**p95 几乎无偏**（15.76→15.80）。

建议替换为：

> "The naive-versus-KM gap depends on how censored the attempts are: 2.4 s across the
> mixed campaign (dominated by the baseline arms that fire early), 0.5 s inside the
> deployed arms, and 0.02–0.2 s inside elevation/hop/plane strata; the p95 is nearly
> unbiased (15.76 vs 15.80 s). The damage of censoring is therefore not a shifted median
> but the removal of the low-advance region from the observable sample, which is why the
> threshold near the p95 cannot be extrapolated from successes alone (Proposition 2)."

附录 D 表 D1 直接用 `km_support_audit.md` 的表（含 [14,16) 桶 67 次尝试，支撑 "thin, not empty"）。

## 5. [C5] III 节版本声明

可写：所有实验使用 **`deepseek-flash`**（openai 兼容接口），442 次调用中 171 次命中缓存。
**不可写**具体日期时间：日志无时间戳字段，只有文件 mtime（2026-10-23 11:04–12:40）。

## 6. 其他

- VI-A 的协议段需加一句"lockbox 实例由 epoch_doy 平移生成，轨迹相位独立、窗口不重叠"；
- 局限性目前有 6 条，新增 lockbox 后第 7 条（泄漏）删除，其余保留；
- 若审稿人追问"full 只领先 ppomlp 1 pp"，回答已在 E2：领先虽小但**方向在 3/3 实例与 2 个交通实例上稳定**，
  且价值主张本来就不在控制器（盾值 +22–24 pp）。
