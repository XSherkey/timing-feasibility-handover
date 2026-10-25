"""R8 part 8: split the Chinese equations so no line wraps."""
from __future__ import annotations

from pathlib import Path

D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"
z = D / "paper_zh.md"
t = z.read_text(encoding="utf-8")
pairs = [
    ("成功   ⇔   路由可达  ∧  a ≥ T_z  ∧  a ≤ V_z  ∧  仰角高于掩码,                            (1)",
     "成功  iff  路由可达  and  a ≥ T_z\n           and  a ≤ V_z  and  仰角高于掩码.                    (1)"),
    ("HSR(z) =   E[ 1{路由} · 1{T_z ≤ a ≤ V_z} · 1{仰角 ≥ 掩码} ].                            (2)",
     "HSR(z) = E[ 1{路由} · 1{T_z ≤ a ≤ V_z}\n            · 1{仰角 ≥ 掩码} ].                          (2)"),
    ("P_D( 盾下晚切换 ) = P_D( T_z > max(a, τ) ) ≤ P_D( T_z > τ ) ≤ ε,                  (3)",
     "P_D( 盾下晚切换 ) = P_D( T_z > max(a, τ) )\n                  ≤ P_D( T_z > τ ) ≤ ε.                    (3)"),
]
done = []
for old, new in pairs:
    if t.count(old) == 1:
        t = t.replace(old, new, 1)
        done.append(old[:10])
    else:
        print("  MISS", t.count(old), old[:40])
z.write_text(t, encoding="utf-8")
print("applied:", done)
