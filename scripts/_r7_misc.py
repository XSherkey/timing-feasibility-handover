"""R8 part 5: Table XII kappa cell, drift caption, protocol clarification, gate note, appendix A command block."""
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
        print(f"  MISS [{label}] {n}: {old[:60]}")
        return
    t = t.replace(old, new, 1)
    done.append(label)


# 1. kappa cell in the annotation table
i = t.find("| mechanical (schema) |")
if i > 0:
    j = t.find("\n", i)
    row = t[i:j]
    print("kappa row was:", row)
    t = t[:i] + "| mechanical (schema) | 20/20 | 1.00 | undefined (—) |" + t[j:]
    done.append("kappa-row")

# 2. drift table caption wording
rep("**Table V. Drift response (polar HSR, mean ± sd, traffic seed 0, polar band |lat| ≥ 70°). The four "
    "shielded and constant rows are n = 10 policy seeds; the two constant rows are policy-independent, so their "
    "sd is 0.00. The last row is the probe study, which uses five policy seeds and is marked as such.**",
    "**Table V. Drift response (polar HSR, mean ± sd, traffic seed 0, polar band |lat| ≥ 70°). The two "
    "constant-controller rows are evaluated on the same n = 10 policy seeds but do not depend on the policy, so "
    "their sd is 0.00; the two shielded rows are n = 10 policy seeds; the last row is the probe study, which "
    "uses five policy seeds and is marked as such.**", "drift-caption")

# 3. Section VI-A: say explicitly that the evaluation row is the archival instantiation
rep("Because both windows return the same threshold (16 s) and the same λ (8), the two "
    "protocols differ in what they *permit*, not in what they *select*; the archival numbers are therefore "
    "directly comparable to the lockbox numbers, and Table X reports both.",
    "Because both windows return the same threshold (16 s) and the same λ (8), the two "
    "protocols differ in what they *permit*, not in what they *select*. Table X therefore labels its first "
    "row *archival*—it is the evaluation-window instantiation of the same pipeline, not a lockbox instance—and "
    "its three lower rows *three-way*; the four rows share one policy set and one episode protocol, so they are "
    "comparable row to row.", "viA-archival")

# 4. gate false-rejection note
rep("False acceptance 0%, false rejection 0% at both replay budgets.",
    "False acceptance 0% and false rejection 0% at both replay budgets, where the two rates are defined on the "
    "harmful-versus-good decision that the gate actually makes; the three neutral candidates are rejected by "
    "construction, because admission requires a replay gain above 5 pp.", "gate-fr")

p.write_text(t, encoding="utf-8")
print("applied:", done)
