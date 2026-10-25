"""R7 part 1: document assembly and notation fixes from review 10."""
from __future__ import annotations

from pathlib import Path

D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"
p = D / "paper_en.md"
t = p.read_text(encoding="utf-8")
done = []


def rep(old, new, label, count=1):
    global t
    n = t.count(old)
    if n != count:
        print(f"  MISS [{label}] {n} (want {count})")
        return
    t = t.replace(old, new)
    done.append(label)


# 1. stray Table V caption glued to the Fig. 4 caption
stray = ("The passivity of the log, not its size, is the binding constraint.**Table V. Cross-intent transfer "
         "(polar HSR at |lat| ≥ 70°, mean over 10 policy seeds; 9 of them committed a rule at intent 0, and the "
         "table reports all seeds, so seeds without a committed rule contribute identically to both arms).**")
rep(stray, "The passivity of the log, not its size, is the binding constraint.", "stray-table-v")

# 2. escaped asterisk in the nomenclature
rep("**τ\\*** is the probed", "**τ∗** is the probed", "nomen-tau")

# 3. the introduction still carried the old sd's
rep("93.3% ± 0.3% (the deployed τ = 18 s variant; the mined τ∗ = 16 s rule alone gives 92.4% ± 0.3%)",
    "93.36% ± 0.05% (the deployed τ = 18 s variant; the mined τ∗ = 16 s rule alone gives 92.44% ± 0.07%)",
    "intro-sd")

# 4. Eq. (1): replace the two glyphs a text extractor mangles with words
rep("success   ⇔   route  ∧  a ≥ T_z  ∧  a ≤ V_z  ∧  elevation ≥ mask,                    (1)",
    "success   iff   route  and  a ≥ T_z  and  a ≤ V_z  and  elevation ≥ mask,             (1)",
    "eq1")

# 5. "never exercise" -> coverage language
rep("cannot pin down a timing constraint that trained policies never exercise (Proposition 2)",
    "cannot pin down a timing constraint that trained policies leave almost unexercised "
    "(705 of 8,682 attempts in the informative band; Proposition 2)", "never-1")
rep("*operational knowledge that passive logs never exercise must leave the reward layer and enter the decision layer*",
    "*operational knowledge that passive logs cover too thinly to identify must leave the reward layer and "
    "enter the decision layer*", "never-2")

# 6. the stale 93.6 cross-protocol sentence
rep("the end-to-end campaign figure (93.6 ± 0.7, Fig. 5) and the frozen τ = 16 s arm measure the same commitment",
    "the end-to-end campaign figure (92.44 ± 0.07, Fig. 5) and the frozen τ = 16 s arm measure the same commitment",
    "campaign-figure")

# 7. six provenance variants plus one controller baseline
rep("seven provenance variants land within 0.11 pp of the full pipeline",
    "six provenance variants land within 0.11 pp of the full pipeline", "six-1")
rep("seven provenance variants land within 0.11 pp of the full pipeline and a probe-calibrated constant controller within 0.0",
    "six provenance variants land within 0.11 pp of the full pipeline and a probe-calibrated constant controller within 0.0",
    "six-2")

# 8. A8 difference arithmetic
rep("tracks the shield to within 0.02 pp at nominal physics (bootstrap 95% CI [-0.06, 0.00])",
    "tracks the shield to within 0.03 pp at nominal physics (bootstrap 95% CI [-0.06, 0.00])", "a8-diff")

# 9. the doubled tuned-constant sentence in VI-D
rep("matches the deployed algorithm at nominal physics (93.33% against 93.36% with the shield, and 93.36% for the "
    "\"highest-elevation candidate, fixed lead\" policy itself, Table IV)",
    "matches the deployed algorithm at nominal physics: 93.33% for the constant against 93.36% for the deployed "
    "shield on the same episodes (Table IV)", "vid-constant")

# 10. kappa: undefined, not zero agreement
rep("and κ against the mechanical rubric is 0 because that rubric\nhas no variance",
    "and κ against the mechanical rubric is *undefined* rather than zero—the mechanical rubric admits every "
    "proposal, so it has no variance to correlate with", "kappa")

p.write_text(t, encoding="utf-8")
print("applied:", done)
