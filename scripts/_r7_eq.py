"""R8 part 4: split the displayed equations so no line can wrap, and fix the caption spacing."""
from __future__ import annotations

from pathlib import Path

D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"
p = D / "paper_en.md"
t = p.read_text(encoding="utf-8")
done = []


def rep(old, new, label):
    global t
    n = t.count(old)
    if n != 1:
        print(f"  MISS [{label}] {n}")
        return
    t = t.replace(old, new, 1)
    done.append(label)


rep("success   iff   route  and  a ≥ T_z  and  a ≤ V_z  and  elevation ≥ mask,             (1)",
    "success  iff  route  and  a ≥ T_z\n"
    "         and  a ≤ V_z  and  elevation ≥ mask.                            (1)", "eq1")

rep("HSR(z)    =   E[ 1{route} · 1{T_z ≤ a ≤ V_z} · 1{elevation ≥ mask} ].                 (2)",
    "HSR(z) = E[ 1{route} · 1{T_z ≤ a ≤ V_z}\n"
    "            · 1{elevation ≥ mask} ].                                    (2)", "eq2")

rep("P_D( late under Π_τ ) = P_D( T_z > max(a, τ) ) ≤ P_D( T_z > τ ) ≤ ε,             (3)",
    "P_D( late under Π_τ ) = P_D( T_z > max(a, τ) )\n"
    "                      ≤ P_D( T_z > τ ) ≤ ε.                              (3)", "eq3")

rep("τ_used = min(τ∗ + m, 24 s),    m = 2 s                                                          (4)",
    "τ_used = min(τ∗ + m, 24 s),   m = 2 s                                  (4)", "eq4")

# caption/table spacing for the appendix tables
for tag in ("Table D1A.", "Table D1B.", "Table C1.", "Table C2."):
    k = t.find("**" + tag)
    if k > 0:
        nl = t.find("\n", k)
        if t[nl + 1:nl + 2] != "\n":
            t = t[:nl + 1] + "\n" + t[nl + 1:]

p.write_text(t, encoding="utf-8")
print("applied:", done)
