"""R14 part 1: the same-protocol sentence, the 0/0 scoping, oracle headroom, and Fig. 2's seed claim."""
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


# 1. the same-protocol sentence (contradicted by the protocol row)
rep("Every row of Table X is produced by the same policy set, the same traffic seed and the same episode protocol; "
    "the only thing that changes between rows is the twin epoch.",
    "Every row of Table X uses the same policy set, the same traffic seed and the same episodes, so row-to-row "
    "differences are not protocol artefacts; but the protocol is not the same across all four columns. The first "
    "column is the archival evaluation-window instantiation, in which the three selections were evaluated on the "
    "window they are reported on; the last three columns are three-way lockbox instances, in which every selection "
    "was made on the validation window and the column window was only scored. Within the three lockbox columns, "
    "the only thing that changes is the twin epoch.", "same-protocol")

# 2. the 0/0 scope in the contribution list and the abstract
rep("A counterfactual replay gate over a 26-candidate bank (0 false accepts, 0 false rejects)",
    "A counterfactual replay gate over a 26-candidate bank (0 false accepts and 0 false rejects on that bank, "
    "where the three neutral candidates are rejected by construction rather than by judgement)", "contrib-00")

rep("the audit gate admits no harmful candidate and rejects no good one in a 26-candidate bank",
    "the audit gate admits no harmful candidate and rejects no good one on the 26-candidate bank we built "
    "(neutral candidates excluded, since the admission threshold rejects them by construction)", "abstract-00")

# 3. the oracle headroom on lockbox instances
i = t.find("All four orderings survive the change of window.")
if i > 0:
    j = t.find("\n\n", i)
    add = (" One residual deserves a sentence, because the tables invite the question: at nominal physics the "
           "deployed threshold is oracle-optimal (the two rows coincide to 0.00 pp), whereas under the "
           "epoch-shifted lockbox instances the oracle sits 0.12–0.40 pp above the deployed arm (91.79 vs 91.67 "
           "at +7 d, 93.43 vs 93.03 at +14 d, 93.16 vs 92.91 at −2 d). That gap is the measured price of the "
           "plateau: a threshold calibrated on the validation window is optimal for the requirement distribution "
           "it was calibrated on, and an epoch shift moves that distribution slightly.")
    t = t[:j] + add + t[j:]
    done.append("oracle-headroom")

# 4. Fig. 2's "every seed" claim scoped to nominal physics
rep("the per-attempt oracle coincides with τ = 18 s on every seed.",
    "the per-attempt oracle coincides with τ = 18 s on every seed at nominal physics (on the epoch-shifted "
    "lockbox instances a small headroom remains; Table X).", "fig2-scope")

p.write_text(t, encoding="utf-8")
print("applied:", done)
