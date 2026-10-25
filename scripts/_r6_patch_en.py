"""R6 (v8): finish the Prop-2 numbers, Contribution 1, and the ledger naming residuals (EN)."""
from __future__ import annotations

from pathlib import Path

P = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本" / "paper_en.md"
t = P.read_text(encoding="utf-8")
done = []


def rep(old: str, new: str, label: str) -> None:
    global t
    n = t.count(old)
    if n != 1:
        raise SystemExit(f"[{label}] expected 1, found {n}")
    t = t.replace(old, new, 1)
    done.append(label)


# ---- 1. Prop 2 residual numbers ------------------------------------------
rep(
    "the count in the informative band is what the estimate would rest on, and that count is 67.",
    "the count in the informative band is what the estimate would rest on, and that count is 705 (8.1% of the 8,682 passive attempts, 91 of them late).",
    "p2-count",
)
rep(
    "in passive operation of this system the informative region is *thinly* exercised (67 attempts out of 22,807)",
    "in passive operation of this system the informative region is *thinly* exercised (705 attempts out of 8,682)",
    "p2-remark",
)
rep(
    "the passive log under-covers the informative region by two orders of magnitude relative to the region where the policy actually operates, which makes the crossing estimated from it dominated by noise",
    "the passive log under-covers the informative region by a factor of about 4.6 relative to the modal 6–8 s bucket (8.1% against 37.7%), which makes the crossing estimated from it dominated by noise",
    "p2-scale",
)

# ---- 2. Contribution 1 ----------------------------------------------------
rep(
    "a feasibility bound is not identifiable from passively logged outcomes when the action support misses the informative region (Proposition 2)",
    "a feasibility bound is not identifiable from passively logged outcomes when effective support in the informative region is insufficient under a sample budget (Proposition 2)",
    "contrib1",
)

# ---- 3. ledger naming residuals ------------------------------------------
rep(
    "matches the full system at nominal physics (94.0% vs 93.6%).",
    "matches the mined-rule campaign arm at nominal physics (94.0% vs 93.6%).",
    "p3-tuned",
)
rep(
    "| Full-system campaign figure 93.6% ± 0.7% (VI-B, Fig. 2, bar 4) |",
    "| Mined-rule campaign arm, 93.6% ± 0.7% (VI-B, Fig. 2, bar 4) |",
    "ledger-row1",
)
rep(
    "the full system's margin over the hand-crafted baseline is *small*",
    "the full-system policies' margin over the hand-crafted baseline is *small*",
    "via-margin",
)
rep(
    "(i) the full-system margin over the hand-crafted baseline is small",
    "(i) the full-system policies' margin over the hand-crafted baseline is small",
    "lim7-margin",
)
rep(
    "Three lockbox instances are evaluated—epoch_doy 299.25 (+7 d), 306.25 (+14 d), and 290.25 (−2 d)—with the frozen full-system policies, the PPO-MLP baseline, and the reward-penalty arm, each under no shield, the mined 16 s rule, the validation-calibrated τ_used = 18 s shield, and, for the full system, the tuned 18 s constant (mean ± sd over seeds; per-seed values in the sealed artefacts):",
    "Three lockbox instances are evaluated—epoch_doy 299.25 (+7 d), 306.25 (+14 d), and 290.25 (−2 d)—with the frozen full-system policies, the PPO-MLP baseline, and the reward-penalty arm, each under no shield, the mined 16 s rule, the validation-calibrated τ_used = 18 s shield, and, for the full-system policies, the tuned 18 s constant (mean ± sd over seeds; per-seed values in the sealed artefacts). In the table, *full* abbreviates \"full-system policies\"; the mined-rule campaign arm of Table II is a different arm and is not part of this table:",
    "lockbox-caption",
)

# ---- 6. Section V-A pointer ---------------------------------------------
rep(
    "the 14–18 s band is not empty—it is thin (per-advance counts in Table D1)",
    "the 14–18 s band is not empty—it is thin (per-advance counts in Table D1A for the passive log; Table D1B is the rule-applied consistency check)",
    "va-pointer",
)

# ---- Appendix C cross-reference -----------------------------------------
rep(
    "| Drift response (Table IV, Table C2) |",
    "| Drift response (Table IV, Table C3) |",
    "ledger-c3",
)

P.write_text(t, encoding="utf-8")
print("applied:", done)
