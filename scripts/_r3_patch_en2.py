"""R3 revision, part 2: ledger naming in the abstract, Section VI-B and Fig. 2."""
from __future__ import annotations

from pathlib import Path

P = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本" / "paper_en.md"
t = P.read_text(encoding="utf-8")


def rep(old: str, new: str, label: str) -> None:
    global t
    n = t.count(old)
    if n != 1:
        raise SystemExit(f"[{label}] expected 1, found {n}")
    t = t.replace(old, new, 1)
    print("ok", label)


rep(
    "applied to *frozen* policy weights and scored on identical episodes, one rule—\"never command a polar handover with less than 16 s of lead\"—raises polar handover success on *frozen* policy weights and identical episodes from 67.5% ± 13.2% to 93.3% ± 0.3% (the deployed τ = 18 s variant; 92.4% ± 0.3% for the mined τ* = 16 s rule itself), while the between-checkpoint spread",
    "applied to *frozen* policy weights and scored on identical episodes, one lower bound on the handover lead raises polar handover success from 67.5% ± 13.2% to 93.31% ± 0.26% (the **deployed probe-calibrated algorithm**, τ_used = 18 s; the **mined-rule arm**, τ* = 16 s with no margin, gives 92.43% ± 0.30%), while the between-checkpoint spread",
    "abstract-naming",
)

rep(
    "The full system (mined constraint + shield) reaches 93.6% ± 0.7%, and a hand-tuned constant with no learning at all (\"highest-elevation candidate, fixed 18 s lead\") reaches 94.0% ± 0.7%.",
    "The **mined-rule campaign arm** (the full system with the mined 16 s rule and no margin) reaches 93.6% ± 0.7%, and a **tuned constant** with no learning at all (\"highest-elevation candidate, fixed 18 s lead\") reaches 94.0% ± 0.7%. These four names—mined-rule campaign arm, deployed probe-calibrated algorithm, tuned constant, oracle shield—are used consistently for the rest of the paper (threshold ledger, Section V-D).",
    "VI-B-naming",
)

rep(
    "**Fig. 2.** Where the gap comes from. Polar HSR (mean, n = 10 seeds): reward-only PPO-MLP 72.6; the same knowledge in the reward at its best coefficient (λ = 8) 84.4; the same knowledge as a shield on the baseline's policies 91.8; the full system 93.6; a tuned constant with no learning 94.0. Bars 1, 2, and 4 share the campaign protocol; bars 3 and 5 are common-episode factorial values;",
    "**Fig. 2.** Where the gap comes from. Polar HSR (mean, n = 10 seeds): reward-only PPO-MLP 72.6; the same knowledge in the reward at its best coefficient (λ = 8) 84.4; the same knowledge as a shield on the baseline's policies 91.8; the **mined-rule campaign arm** (16 s shield, no margin) 93.6; the **tuned constant** (18 s lead, no learning) 94.0. The 93.6 bar is the campaign 16 s arm, *not* the deployed probe-calibrated algorithm (18 s), which is 93.31 and appears in the factorial (Fig. 3). Bars 1, 2, and 4 share the campaign protocol; bars 3 and 5 are common-episode factorial values;",
    "fig2-caption",
)

P.write_text(t, encoding="utf-8")
print("done")
