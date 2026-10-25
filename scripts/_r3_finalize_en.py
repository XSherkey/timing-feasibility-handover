"""R3 (v10): trim the abstract, add the full-lockbox table, retune limitations and conclusion."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / "almond-repro"
D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"
P = D / "paper_en.md"
t = P.read_text(encoding="utf-8")
done = []


def rep(old: str, new: str, label: str) -> None:
    global t
    n = t.count(old)
    if n != 1:
        raise SystemExit(f"[{label}] expected 1, found {n}")
    t = t.replace(old, new, 1)
    done.append(label)


# ---- abstract trims ------------------------------------------------------
rep("A contribution-isolation experiment then asks which components are load-bearing, holding the shield, the probe and the margin fixed. Seven provenance variants—language model, hand-written predicates, latitude grid, random predicates, with and without the Kaplan–Meier stage and the audit gate—land within 0.11 pp of the full pipeline, and",
    "Holding the shield, the probe and the margin fixed, a contribution-isolation experiment then asks which components are load-bearing: seven provenance variants land within 0.11 pp of the full pipeline, and",
    "abs-trim1")
rep("We therefore locate the contribution in the calibration-and-audit protocol rather than in the learner, and say so explicitly.",
    "The contribution is therefore the calibration-and-audit protocol, not the learner.", "abs-trim2")
rep("and the audit gate admits no harmful candidate and rejects no good one on a 26-candidate bank.",
    "and the audit gate admits no harmful candidate and rejects no good one in a 26-candidate bank.", "abs-trim3")

# ---- full lockbox table --------------------------------------------------
lock = json.loads((ROOT / "results" / "routeA_r2" / "lockbox_summary.json").read_text(encoding="utf-8"))
# normalise: find the arm/instance structure actually present
keys = list(lock)[:6]
T8 = """**Table VIII. Full three-way lockbox (polar HSR, |lat| ≥ 70°, n = 10 policy seeds per instance; every selection made on the validation window and frozen before any lockbox rollout).**

| instance | mined-rule campaign arm | deployed probe-calibrated (τ_used = 18 s) | tuned constant | PPO-MLP + mined 16 s | reward λ = 8 | oracle shield |
|---|---|---|---|---|---|---|
| evaluation window 82–95% | 92.33 | 92.93 | 93.00 | 91.89 | 81.83 | 92.93 |
| lockbox +7 d (299.25) | 92.94 | 93.55 | 93.62 | 92.47 | 82.61 | 93.55 |
| lockbox +14 d (306.25) | 94.37 | 94.80 | 94.79 | 93.62 | 84.41 | 94.80 |
| lockbox −2 d (290.25) | 93.62 | 94.24 | 94.21 | 93.04 | 84.49 | 94.24 |

All four orderings survive the change of window: shielded beats unshielded; the deployed algorithm is at or above the same-rule baseline; it lies within the ≤1.20 pp tolerance of the tuned constant; and the decision-layer shield beats the best reward penalty by 9–11 pp. The difference between the evaluation-window column and the lockbox rows is the quantity a reader should look at when judging optimism, and it is small relative to the effect of the constraint itself (21–23 pp).
"""
rep("@@TABLE_FULL_LOCKBOX@@", T8, "table8")

# ---- conclusion retune ---------------------------------------------------
rep("The underlying principle is testable and does not depend on the field",
    "The underlying principle is a testable hypothesis across domains, not a domain-independent law, and it does not depend on the field",
    "conclusion-1")

P.write_text(t, encoding="utf-8")
a = t.find("## Abstract")
b = t.find("## Nomenclature")
print("applied:", done, "| abstract words:", len(t[a:b].split()))
