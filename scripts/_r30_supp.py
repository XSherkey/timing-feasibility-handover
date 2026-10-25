"""R30 part 2: supplement cross-references and the D2 rule column."""
from __future__ import annotations

import json
import re
from pathlib import Path

D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"
ROOT = Path(__file__).resolve().parents[2] / "almond-repro"
supp_path = D / "supplementary" / "supp_en.md"
s = supp_path.read_text(encoding="utf-8")
done = []


def rep(old, new, label):
    global s
    n = s.count(old)
    if n != 1:
        print("  MISS", label, n)
        return
    s = s.replace(old, new, 1)
    done.append(label)


# 1. Prop-3 proof: the quantile bound is now (4)
rep("(iii) Each dependence is present in the conjunction; (3) contains none of them.",
    "(iii) Each dependence is present in the conjunction; (4) contains none of them.", "proof (3)->(4)")

# 2. Table L1: the shield executes the margin formula, now (5)
rep("the shield applies rule (4) with τ_used = 18 s where a shield is present",
    "the shield applies the threshold of (5) with τ_used = 18 s where a shield is present", "L1 rule (4)->(5)")

# 3. Appendix E points at the LLM study, which is Section VI-N in the main text
s = s.replace("the one used in the study of Section VI-L", "the one used in the study of Section VI-N")
s = s.replace("Three observations that the statistics of Section VI-L quantify", "Three observations that the statistics of Section VI-N quantify")
done.append("Appendix E VI-L -> VI-N")

# 4. threshold ledger: the drift table is H2, and the per-seed one C2
rep("Drift response (Table V, Table C2)", "Drift response (Table H2, Table C2)", "G1 drift table ref")

# 5. D2: restore the executed-rule column
gs = json.loads((ROOT / "results" / "routeA_r3" / "gate_systematic" / "summary.json").read_text(encoding="utf-8"))
rows = ["| id | executed rule | validation gain (pp) | admission | evaluation effect (pp) | post-hoc label |",
        "|---|---|---|---|---|---|"]
for c in sorted(gs["bank"], key=lambda b: b["id"]):
    rows.append(f"| {c['id']} | `{c['rule']}` | {c['delta_short']:+.2f} | "
                f"{'admit' if c['admit_short'] else 'reject'} | {c['delta_test']:+.2f} | {c['class']} |")
D2 = ("**Table D2. The full 26-candidate gate bank.** The gate decides on the validation gain only (admission "
      "requires > 5 pp); the evaluation effect is measured afterwards, on the window the gate never sees, and is what "
      "assigns the post-hoc label — harmful if that effect is negative, neutral if 0 ≤ Δ < 5 pp, good if Δ ≥ 5 pp. "
      "Because the label comes from a column the gate never reads, the confusion matrix is an audit and not a "
      "tautology. Two proposals (G04 at 28 s, G19 at 30 s) exceed the 26 s action grid: their magnitude is projected "
      "onto the grid before evaluation, so the gate reviews the *projected* candidate, which is why those two rows "
      "carry identical gains and are not independent evidence.\n\n" + "\n".join(rows) + "\n")
i = s.find("**Table D2.")
if i > 0:
    j = s.find("\n\n## Appendix ", i)
    s = s[:i] + D2 + ("" if j < 0 else s[j:])
    done.append("D2 with rule column")

supp_path.write_text(re.sub(r"\n{3,}", "\n\n", s), encoding="utf-8")
print("edits:", done)
print("D2 rows:", len(rows) - 2)
