"""Make the plan document read cleanly: replace the two wide tables with bullet lists."""
from __future__ import annotations

from pathlib import Path

D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"
p = D / "REVISION_PLAN.md"
t = p.read_text(encoding="utf-8")

B_OLD_START = "| 编号 | 动作 | 需要新仿真？ | 回应哪条 |"
B_OLD_END = "**回应了**：统计单元（5）、bank 构造（2）、开销指标（8）。"
i = t.find(B_OLD_START)
j = t.find(B_OLD_END)
NEW_B = """- **B1 分层统计**（不需要新仿真）。把 n 拆成 policy seed × episode block × epoch，用分层 bootstrap 重算全部置信区间；
  并把 A8 与两个常数臂标为确定性控制器，不与学习臂共用配对结构。→ 回应第 5 条。
- **B2 重造候选 bank**（小时级回放）。不再人工围绕已知答案构造，改为按谓词文法**抽样生成** 26 条，
  覆盖边界、互相冲突、不同失效机制三类；报告 precision/recall 的区间以及对回放预算的敏感性。→ 回应第 2 条。
- **B3 网络开销指标**（不需要新仿真）。p95/p99 时延、dual-homing 占用时长、信令次数、video 与 emergency 分流结果，
  全部从已存的 per-attempt 日志计算。→ 回应第 8 条。
- **B4 统计口径补齐**（不需要新仿真）。把 κ 的原始 2×2 列联表、以及每个对比的 Cohen's d_z 放进补充材料；
  Fig. 5 的"五根柱 + 一个引用值"在正文里写清。→ 回应第 2、3 条。

"""
t = t[:i] + NEW_B + t[j:]

C_OLD_START = "| 编号 | 实验 | 设计要点 | 回应哪条 |"
C_OLD_END = "**回应了**：跨约束族（1）、在线漂移（3）"
i = t.find(C_OLD_START)
j = t.find(C_OLD_END)
NEW_C = """- **C1 第二类约束：路由 / 馈电容量。** 在孪生已有的 feeder 容量维度上，用同一套"挖谓词 → 探针定幅值 → 审计门 → 盾"
  流程做一次完整案例。现有 Table L1 已经显示：把馈电容量压到 3 个时隙后，时序可行性被盾修复，但 `no_route`
  升到 26–30%，即容量成为新瓶颈——把它扩展成一个完整案例，正好回答"除了这条 16–18 s 规则你还证明了什么"。
  → 回应第 1 条（最关键）。
- **C2 在线漂移。** 只允许部署时可获得的信号（late-share 的 CUSUM 检测）触发重探，报告检测延迟、
  校准期性能、探针引发的新失败与资源开销、误触发代价。→ 回应第 3 条。

"""
t = t[:i] + NEW_C + t[j:]
p.write_text(t, encoding="utf-8")
print("tables replaced with bullets; chars", len(t))
