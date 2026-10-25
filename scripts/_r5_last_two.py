"""R5 last: the oracle-ladder sentence and the provenance note in Section VI-I."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / "almond-repro"
D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"
fc = json.loads((ROOT / "results" / "routeA_r3" / "factorial_consistent" / "summary.json").read_text(encoding="utf-8"))
A = fc["arms"]
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


rep("On the frozen factorial the oracle arm returns 93.31% ± 0.26 (late share 0.00%)—identical to the deployed τ = 18 s arm",
    f"On the frozen factorial the oracle arm returns {A['oracle']['summary']['mean']:.2f}% ± "
    f"{A['oracle']['summary']['sd']:.2f} (late share 0.00%)—identical to the deployed τ = 18 s arm",
    "oracle-ladder")

rep("This matters because an earlier version of this table mixed the fixed-architecture replica policies (used by the factorial of Table C2, whose deployed arm reads 93.31 on the evaluation window) with a traffic seed that varied per policy seed; the two protocols differ by about 1 pp on the same arm, which is larger than the effect of the epoch shift itself. Table VIII therefore reports the campaign policies only, and the evaluation row is the reference the lockbox rows are compared against.",
    "Every table in this paper—the factorial of Appendix C, the headline bars of Fig. 5, the isolation arms of Table VII and the lockbox rows here—now uses the same campaign policies, the same traffic seed and the same episode protocol; the only thing that changes between rows of Table VIII is the twin epoch itself.",
    "provenance-note")

p.write_text(t, encoding="utf-8")
print("applied:", done)
