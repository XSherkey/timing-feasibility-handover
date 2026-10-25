"""R10 part 8: the Chinese Section V-C/V-A probe statement and the VI-A data-flow paragraph."""
from __future__ import annotations

from pathlib import Path

D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"
z = D / "paper_zh.md"
s = z.read_text(encoding="utf-8")
done = []


def repz(old, new, label):
    global s
    n = s.count(old)
    if n != 1:
        print(f"  MISS [{label}] {n}: {old[:40]}")
        return
    s = s.replace(old, new, 1)
    done.append(label)


repz("在当前产物中，探测运行在留出的评估窗口上（与训练和发现集均不相交）；标定/评估分离问题在第六节 A 中明确讨论。",
     "在当前产物中，探测在两个留出窗口上都运行过并返回同一阈值——验证窗口（65–75%）与评估窗口（82–95%）上都是 "
     "τ∗ = 16 s，二者都与训练和发现集不相交。archival 数字（表 II–V、图 5）使用评估窗口的探测；three-way 数字"
     "（表 X 的 lockbox 行）只用验证窗口的探测，第六节 A 说明哪张表属于哪个协议。", "VC-probe")

# the VI-A data-flow paragraph: find the sentence about calibration steps touching the evaluation window
import re
m = re.search(r"三个标定步骤[^。]*评估窗口[^。]*。", s)
if m:
    old = m.group(0)
    new = ("三个标定步骤——门的重放、定 τ∗ 的探测、以及 λ 与余量的选择——全部在验证窗口上完成；"
           "门只在候选的验证重放增益高于 5 pp 且下界为正时准入，评估窗口从不进入该决定。"
           "表 III–IX、XI、XII 的 archival 数字来自更早一轮，那一轮里这三次选择恰好在评估窗口上评估；"
           "之所以仍报告它，是因为它复现了原有流水线，而第六节 I 表明三路协议会选回同样的选择"
           "（τ∗ = 16 s、λ = 8、m = 2），因此数字相差不超过 0.05 pp。本文没有任何主张依赖 archival 结构。")
    s = s.replace(old, new, 1)
    done.append("VIA")
else:
    print("VI-A sentence not matched")

# Limitation 7
i = s.find("7. **Lockbox")
if i > 0:
    j = s.find("\n", i)
    L7 = ("7. **Lockbox 范围。** 三路协议把每一次选择移到验证窗口，lockbox 只在事后被评分，"
          "实例化为三个平移历元（±2/7/14 天轨道相位）。它没有重跑的是**发现**：叙述、谓词提案与检查点"
          "本身只产生一次，都在 0–60% 训练窗口上并被固定。因此 lockbox 约束的是标定的乐观偏差，"
          "而不是发现的乐观偏差。两点保留：部署臂与调好常数在每个 lockbox 实例上相差不超过 0.03 pp，"
          "所以标定买到的是自动化与可审计性而非精度；lockbox 孪生与标定共享同一星座、流量模型与时间视界，"
          "超出该孪生族的泛化未被检验。")
    s = s[:i] + L7 + s[j:]
    done.append("L7")

z.write_text(s, encoding="utf-8")
print("applied:", done)
