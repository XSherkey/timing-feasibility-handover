"""T0-02 — add a Nomenclature block and make every table caption state its latitude band (EN + ZH)."""
from __future__ import annotations

from pathlib import Path

D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"

NOMEN_EN = """## Nomenclature

*Bands.* **polar** means site latitude |lat| ≥ 70° and is used by every main-text table; the **support
band** |lat| ≥ 68° is used only by the two support-audit panels of Appendix D, because that is the band
the mined rule scopes. No table mixes the two.

*Metrics.* **HSR** is the attempt-weighted share of successful handovers in the stated band.
**S** is the satisfaction score of Section III (weighted reliability, latency and power).
**late share** is the share of attempts whose recorded cause is ``late_handover``.

*Quantities.* **T_z** is the acquisition requirement of one attempt (seconds of lead actually needed).
**p(a)** is the probability that an attempt launched with lead *a* is late. **τ\\*** is the probed
estimate of the lead at which p(a) first falls below ε = 5%, measured on the validation window.
**τ_used = min(τ\\* + m, 24 s)** is the deployed threshold, with **m = 2 s** the cost-asymmetric margin.
**ā** is the grid point above which measured failures vanish (18 s at nominal physics).

*Arms.* **mined-rule campaign arm** is the 16 s rule with no margin (the 93.6% campaign figure).
**deployed probe-calibrated algorithm** is the same rule at τ_used = 18 s (93.31% on common episodes).
**tuned constant** is the highest-elevation controller with a fixed 18 s lead and no learning (94.0%).
**oracle shield** clamps each attempt to its realised requirement (upper reference, 93.31%).
**A0–A8** are the contribution-isolation arms of Section VI-H.

"""

BANDS = {
    "**Table III. Penalty dose-response (polar HSR and satisfaction S, mean ± sd, n = 10; shield column for reference).**":
    "**Table III. Penalty dose-response (polar HSR and satisfaction S, mean ± sd, n = 10; polar band |lat| ≥ 70°; shield column for reference).**",
    "**Table IV. Drift response (polar HSR, mean ± sd, n = 5).**":
    "**Table IV. Drift response (polar HSR, mean ± sd, n = 10; polar band |lat| ≥ 70°).**",
    "**Table V. Cross-intent transfer (polar HSR, mean ± sd, n = 5).**":
    "**Table V. Cross-intent transfer (polar HSR, mean ± sd, n = 5; polar band |lat| ≥ 70°; descriptive, see Section VI-J).**",
    "**Table VI. Alternative physics (polar HSR, n = 5; frozen policies, shield = rule (4) with τ∗ = 18 s).**":
    "**Table VI. Alternative physics (polar HSR, mean over n = 5 policy seeds; polar band |lat| ≥ 70°; frozen policies; the shield applies rule (4) with τ_used = 18 s where a shield is present).**",
    "**Table C1. Frozen-policy factorial, archived checkpoint set, polar HSR (%) per seed, common episodes.**":
    "**Table C1. Frozen-policy factorial, archived checkpoint set, polar HSR (%) per seed (|lat| ≥ 70°), common episodes.**",
    "**Table C2. Deployed-threshold completion and oracle reference, polar HSR (%) per seed, common episodes.**":
    "**Table C2. Deployed-threshold completion and oracle reference, polar HSR (%) per seed (|lat| ≥ 70°), common episodes.**",
    "**Table C3. Drift response per seed, polar HSR (%): fixed 18 s constant / probe-calibrated (τ∗ in parentheses), common episodes.**":
    "**Table C3. Drift response per seed, polar HSR (%) at |lat| ≥ 70°: fixed 18 s constant / probe-calibrated (τ∗ in parentheses), common episodes.**",
}

NOMEN_ZH = """## 符号表

*纬度带。* **polar** 指站点 |lat| ≥ 70°，正文所有主表均用此带；**支撑带** |lat| ≥ 68° 仅用于附录 D 的两个支撑审计面板，因为那正是挖掘规则的作用域。任何一张表都不混用两个带。

*指标。* **HSR** 为所指纬度带内按尝试数加权的切换成功率。**S** 为第三节的满意度（可靠性、时延、功耗加权）。**late share** 为原因码为 ``late_handover`` 的尝试占比。

*量。* **T_z** 为单次尝试的建链需求（实际所需提前量，秒）。**p(a)** 为以提前量 *a* 发起时晚切换的概率。**τ\\*** 为 p(a) 首次低于 ε = 5% 处的提前量估计，在验证窗口上测得。**τ_used = min(τ\\* + m, 24 s)** 为部署阈值，**m = 2 s** 为代价不对称余量。**ā** 为实测失败消失的网格点（标称物理下 18 s）。

*臂。* **挖出规则 campaign 臂**为 16 s 规则、不加余量（campaign 93.6%）。**部署的探测标定算法**为同一条规则取 τ_used = 18 s（共同回合 93.31%）。**调好的常数**为最高仰角控制器 + 固定 18 s 提前量、无学习（94.0%）。**oracle 盾**把每次尝试钳到其真实需求（上界参照，93.31%）。**A0–A8** 为第六节 H 的贡献隔离臂。

"""

BANDS_ZH = {
    "**表 III. 惩罚剂量-响应（极区 HSR 与满意度 S，mean ± sd，n = 10；盾列作参照）。**":
    "**表 III. 惩罚剂量-响应（极区 HSR 与满意度 S，mean ± sd，n = 10；极区取 |lat| ≥ 70°；盾列作参照）。**",
    "**表 IV. 漂移响应（极区 HSR，mean ± sd，n = 5）。**":
    "**表 IV. 漂移响应（极区 HSR，mean ± sd，n = 10；极区取 |lat| ≥ 70°）。**",
    "**表 V. 跨意图转移（极区 HSR，mean ± sd，n = 5）。**":
    "**表 V. 跨意图转移（极区 HSR，mean ± sd，n = 5；极区取 |lat| ≥ 70°；描述性结果，见第六节 J）。**",
    "**表 VI. 替代物理（极区 HSR，n = 5；冻结策略，盾 = 规则 (4)，τ∗ = 18 s）。**":
    "**表 VI. 替代物理（极区 HSR，五个策略种子的均值；极区取 |lat| ≥ 70°；冻结策略；带盾臂施加规则 (4)，τ_used = 18 s）。**",
    "**表 C1. 冻结策略因子化（归档检查点集），极区 HSR（%）逐种子，共同回合。**":
    "**表 C1. 冻结策略因子化（归档检查点集），极区 HSR（%）逐种子（|lat| ≥ 70°），共同回合。**",
    "**表 C2. 部署阈值补齐与 oracle 参照，极区 HSR（%）逐种子，共同回合。**":
    "**表 C2. 部署阈值补齐与 oracle 参照，极区 HSR（%）逐种子（|lat| ≥ 70°），共同回合。**",
    "**表 C3. 漂移响应逐种子，极区 HSR（%）：固定 18 s 常数 / 探测标定（括号内为 τ∗），共同回合。**":
    "**表 C3. 漂移响应逐种子，极区 HSR（%）取 |lat| ≥ 70°：固定 18 s 常数 / 探测标定（括号内为 τ∗），共同回合。**",
}

for name, nomen, bands, anchor in (
    ("paper_en.md", NOMEN_EN, BANDS, "**Index Terms**"),
    ("paper_zh.md", NOMEN_ZH, BANDS_ZH, "**关键词**"),
):
    p = D / name
    t = p.read_text(encoding="utf-8")
    if "## Nomenclature" in t or "## 符号表" in t:
        print(name, "nomenclature already present")
    else:
        i = t.find(anchor)
        j = t.find("\n", i)
        t = t[: j + 1] + "\n" + nomen + t[j + 1:]
        print(name, "nomenclature inserted")
    n = 0
    for old, new in bands.items():
        if t.count(old) == 1:
            t = t.replace(old, new, 1)
            n += 1
    p.write_text(t, encoding="utf-8")
    print(name, "captions updated:", n, "/", len(bands))
