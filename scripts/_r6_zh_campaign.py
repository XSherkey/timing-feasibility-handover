from pathlib import Path

p = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本" / "paper_zh.md"
t = p.read_text(encoding="utf-8")
old = ("跨协议一致性：端到端 campaign 数字（93.6 ± 0.7，图 5）与冻结 τ = 16 s 臂测量的是同一条已提交规则在两种协议下的表现"
       "——带规则的训练运行，对比共同回合上的固定权重——均值相差 ≈1.2 pp")
new = ("同一协议下的数字：端到端 campaign 数字（92.44 ± 0.07，图 5）与冻结 τ = 16 s 臂测量的是同一条已提交规则"
       "——带规则的训练运行，对比共同回合上的固定权重——均值相差 0.0 pp")
print("count", t.count(old))
if t.count(old) == 1:
    t = t.replace(old, new, 1)
    p.write_text(t, encoding="utf-8")
    print("fixed")
