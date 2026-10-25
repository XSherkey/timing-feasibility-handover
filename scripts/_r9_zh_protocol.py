"""R10 part 6: A8 rounding consistency and the ZH mirror of the protocol changes."""
from __future__ import annotations

from pathlib import Path

D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"

# ---- EN: A8 delta cell should read -0.03 in both columns ------------------
p = D / "paper_en.md"
t = p.read_text(encoding="utf-8")
old = "| 93.33 | -0.03 | 91.67 | -0.02 [-0.06, +0.00] | 0.500 |"
new = "| 93.33 | -0.03 | 91.67 | -0.03 [-0.06, +0.00] | 0.500 |"
if t.count(old) == 1:
    t = t.replace(old, new, 1)
    p.write_text(t, encoding="utf-8")
    print("EN A8 fixed")
else:
    print("EN A8 count", t.count(old))

# ---- ZH: mirror the protocol paragraphs and the numbers -------------------
z = D / "paper_zh.md"
s = z.read_text(encoding="utf-8")
done = []


def repz(old_s, new_s, label):
    global s
    n = s.count(old_s)
    if n != 1:
        print(f"  MISS [{label}] {n}: {old_s[:50]}")
        return
    s = s.replace(old_s, new_s, 1)
    done.append(label)


i = s.find("为精确而非安慰")
if i < 0:
    i = s.find("精确版本见第六节 A")
if i > 0:
    j = s.find("\n\n", i)
    VE = ("为精确而非安慰。发现只用训练期日志（0–60%）。此后每一步选择——门的准入、定 τ∗ 的探测、"
          "惩罚系数 λ 与余量 m——都在验证窗口（65–75%）上完成，且门只在候选的验证重放增益高于 5 pp "
          "且下界为正时准入。评估窗口（82–95%）与任何 lockbox 实例都不参与准入：它们只被事后评分，"
          "第六节 A 的「两协议」声明说明每个报告数字属于哪一个。本文早期草稿曾把门描述为同时在评估窗口上重放；"
          "那是第六节 A 的 archival 协议，只适用于第一轮结果，本文没有任何数字依赖它。")
    s = s[:i] + VE + s[j:]
    done.append("VE")

i = s.find("三个标定步骤")
if i > 0:
    j = s.find("\n\n", i)
    VIA = ("三个标定步骤——门的重放、定 τ∗ 的探测、以及 λ 与余量的选择——全部在验证窗口上完成。门只在候选的验证"
           "重放增益高于 5 pp 且下界为正时准入；评估窗口从不进入该决定。表 III–IX、XI、XII 的 archival 数字来自"
           "更早一轮，那一轮里这三次选择恰好在评估窗口上评估；之所以仍报告它，是因为它复现了原有流水线，"
           "而第六节 I 表明三路协议会选回同样的选择（τ∗ = 16 s、λ = 8、m = 2），因此数字相差不超过 0.05 pp。"
           "本文没有任何主张依赖 archival 结构。")
    s = s[:i] + VIA + s[j:]
    done.append("VIA")

i = s.find("7. **Lockbox 范围。**")
if i > 0:
    j = s.find("\n\n", i)
    L7 = ("7. **Lockbox 范围。** 三路协议把每一次选择移到验证窗口，lockbox 只在事后被评分，且实例化为三个平移历元"
          "（±2/7/14 天轨道相位）。它没有重跑的是**发现**：叙述、谓词提案与检查点本身只产生一次，都在 0–60% 训练窗口上，"
          "并被固定。因此 lockbox 约束的是标定的乐观偏差，而不是发现的乐观偏差。两点保留：部署臂与调好常数在每个 "
          "lockbox 实例上都相差不超过 0.03 pp，所以标定买到的是自动化与可审计性，不是精度；lockbox 孪生与标定共享"
          "同一星座、流量模型与时间视界结构，因此超出该孪生族的泛化未被检验。")
    s = s[:i] + L7 + s[j:]
    done.append("L7")

repz("带部署的 τ = 18 s 盾时横跨 92.7–93.7%（sd 0.26）",
     "带部署的 τ = 18 s 盾时横跨 93.3–93.5%（sd 0.05，表 C1）", "prop3")
repz("实测带盾后的晚切换占比为 0.93%（对 ε = 5%）",
     "实测带盾后的晚切换占比为 τ = 16 s 时的 0.93% 与 τ = 18 s 时的 0.00%（对 ε = 5%）", "late")
repz("| 93.33 | −0.03 | 91.67 |",
     "| 93.33 | −0.03 | 91.67 |", "noop")

z.write_text(s, encoding="utf-8")
print("ZH applied:", done)
