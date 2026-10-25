"""Last stale-value fixes: the ledger labels and the two intro/limitation sentences."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / "almond-repro"
D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"
fc = json.loads((ROOT / "results" / "routeA_r3" / "factorial_consistent" / "summary.json").read_text(encoding="utf-8"))
h = json.loads((ROOT / "results" / "routeA_r3" / "headline_consistent" / "summary.json").read_text(encoding="utf-8"))
A, H = fc["arms"], h["arms"]

# English
p = D / "paper_en.md"
t = p.read_text(encoding="utf-8")
old = "| Mined-rule campaign arm, 93.6% ± 0.7% (VI-B, Fig. 5, bar 4) |"
new = (f"| Mined-rule campaign arm, {A['rule16']['summary']['mean']:.2f}% ± "
       f"{A['rule16']['summary']['sd']:.2f}% (VI-B, Fig. 5, bar 4) |")
if t.count(old) == 1:
    t = t.replace(old, new, 1)
    p.write_text(t, encoding="utf-8")
    print("EN ledger fixed")
else:
    print("EN ledger count", t.count(old))

# Chinese
z = D / "paper_zh.md"
s = z.read_text(encoding="utf-8")
pairs = [
    ("| 调好的常数 94.0%（图 5 第 5 柱） |",
     f"| 调好的常数 {H['maxel18']['summary']['mean']:.2f}%（图 5 第 5 柱） |"),
    ("1. **调好的常数在标称物理下与本文持平。** 94.0% ± 0.7% 对 93.6% ± 0.7%。",
     f"1. **调好的常数在标称物理下与本文持平。** 20 s 为 {A['rule20']['summary']['mean']:.2f}%，"
     f"最高仰角控制器为 {H['maxel18']['summary']['mean']:.2f}%，部署算法为 {A['rule18']['summary']['mean']:.2f}%。"),
    ("挖出规则 campaign 臂的端到端数字 93.6% ± 0.7% 另行复现，与冻结 τ = 16 s 臂的均值相差 ≈1.2 pp（第六节 B）。",
     f"挖出规则 campaign 臂在同一协议下读数为 {A['rule16']['summary']['mean']:.2f}% ± "
     f"{A['rule16']['summary']['sd']:.2f}%（第六节 B）。"),
    ("| **挖出规则 campaign 臂** 93.6% ± 0.7%（VI-B，图 5 第 4 柱；16 s、未加余量） |",
     f"| **挖出规则 campaign 臂** {A['rule16']['summary']['mean']:.2f}% ± "
     f"{A['rule16']['summary']['sd']:.2f}%（VI-B，图 5 第 4 柱；16 s、未加余量） |"),
]
done = []
for old, new in pairs:
    if s.count(old) == 1:
        s = s.replace(old, new, 1)
        done.append(old[:24])
    else:
        print("  MISS:", s.count(old), old[:50])
z.write_text(s, encoding="utf-8")
print("ZH applied:", done)
