"""R10 part 9: replace the Chinese V-C probe sentence and the V-A data-flow paragraph."""
from __future__ import annotations

import re
from pathlib import Path

D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"
z = D / "paper_zh.md"
s = z.read_text(encoding="utf-8")
done = []

# V-C: the probe sentence
old = "在当前产物中，探测运行在留出评估窗口上（与训练和发现集均不相交）；标定/评估分离问题在第六节 A 中明确讨论。"
new = ("在当前产物中，探测在**两个**留出窗口上都运行过并返回同一阈值——验证窗口（65–75%）与评估窗口（82–95%）上"
       "都是 τ∗ = 16 s，二者都与训练和发现集不相交。archival 数字（表 III–VII、IX 与图 2–5）使用评估窗口的探测；"
       "three-way 数字（表 X 的 lockbox 行）只用验证窗口的探测，第六节 A 的「两协议」段落说明哪张表属于哪一个。")
if s.count(old) == 1:
    s = s.replace(old, new, 1)
    done.append("VC")
else:
    print("VC count", s.count(old))

# V-A data-flow paragraph: from the bold lead-in to the end of the paragraph
i = s.find("**数据流，精确陈述——因为标定与评估在当前产物中触及同一窗口。**")
if i > 0:
    j = s.find("\n\n", i)
    NEW = ("**数据流。** 孪生视界按时间划分为训练窗口（0–60%）、验证窗口（65–75%）与评估窗口（82–95%），互不相交。"
           "发现（叙事生成、假设提案）只使用训练期日志。此后三个标定步骤——审计门的重放、定 τ∗ 的探测、"
           "以及 λ 与余量的选择——**全部在验证窗口上完成**；门只在候选的验证重放增益高于 5 pp 且下界为正时准入，"
           "评估窗口从不进入该决定。表 III–IX、XI、XII 的 archival 数字来自更早一轮，那一轮里这三次选择恰好在评估窗口上"
           "评估；之所以仍报告它，是因为它复现了原有流水线，而第六节 I 表明三路协议会选回同样的选择"
           "（τ∗ = 16 s、λ = 8、m = 2），因此数字相差不超过 0.05 pp。本文没有任何主张依赖 archival 结构。")
    s = s[:i] + NEW + s[j:]
    done.append("VA")

z.write_text(s, encoding="utf-8")
print("applied:", done)
