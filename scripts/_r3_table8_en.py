from pathlib import Path

P = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本" / "paper_en.md"
t = P.read_text(encoding="utf-8")

T8 = """**Table VIII. Full three-way lockbox (polar HSR, |lat| ≥ 70°, n = 10 policy seeds per instance; every selection made on the validation window and frozen before any lockbox rollout).**

| instance | mined-rule campaign arm | deployed probe-calibrated (τ_used = 18 s) | tuned constant | PPO-MLP + mined 16 s | reward λ = 8 | oracle shield |
|---|---|---|---|---|---|---|
| evaluation window 82–95% | 92.33 | 92.93 | 93.00 | 91.89 | 81.83 | 92.93 |
| lockbox +7 d (299.25) | 92.94 | 93.55 | 93.62 | 92.47 | 82.61 | 93.55 |
| lockbox +14 d (306.25) | 94.37 | 94.80 | 94.79 | 93.62 | 84.41 | 94.80 |
| lockbox −2 d (290.25) | 93.62 | 94.24 | 94.21 | 93.04 | 84.49 | 94.24 |

All four orderings survive the change of window: shielded beats unshielded; the deployed algorithm is at or above the same-rule baseline; it lies within the ≤1.20 pp tolerance of the tuned constant; and the decision-layer shield beats the best reward penalty by 9–11 pp. The difference between the evaluation-window column and the lockbox rows is what a reader should look at when judging optimism, and it is small relative to the effect of the constraint itself (21–23 pp)."""

if "@@TABLE_FULL_LOCKBOX@@" not in t:
    raise SystemExit("placeholder missing")
t = t.replace("@@TABLE_FULL_LOCKBOX@@", T8, 1)
P.write_text(t, encoding="utf-8")
print("Table VIII inserted; remaining placeholders:",
      t.count("@@"), t.count("@@TABLE"))
