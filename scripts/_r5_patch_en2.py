"""R5 (v7) part 2 (EN): passive-log percentages, naming, small numbers."""
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


# ---- abstract / intro / claim 2 percentages ------------------------------
rep(
    "so the informative region of the outcome data is barely covered (67 of 22,807 polar attempts)—an *effective*-support failure",
    "so the informative region of the outcome data is thinly covered (705 of 8,682 passive attempts in the 14–16 s band, against 37.7% in the modal 6–8 s bucket)—an *effective*-support failure",
    "abs-pct",
)
rep(
    "so the region of advance space where outcomes are informative—just below the requirement—is covered two orders of magnitude more thinly than the region the policy actually operates in (67 of 22,807 near-polar attempts in this system), and within any budget a field study can afford the bound is therefore effectively unidentifiable from that stream alone",
    "so the region of advance space where outcomes are informative—just below the requirement—is covered several times more thinly than the modal operating region (705 of 8,682 passive attempts in the 14–16 s band, against 37.7% at 6–8 s), and within any budget a field study can afford the bound is therefore effectively unidentifiable from that stream alone",
    "intro-pct",
)
rep(
    "In the near-polar band that the rule scopes (|lat| ≥ 68°; Appendix D, Table D1), only 0.3% of attempts (67 of 22,807) fall in the 14–16 s bucket immediately below the crossing, while 92.5% sit at or above 16 s—91.1% of them exactly in the 16–18 s bucket—because the deployed arms apply the mined rule at evaluation. The band that would *locate* the crossing is therefore the thin one; the mass at 16 s is mass at the rule's own value, which confirms that the rule is applied but says nothing about where the crossing lies.",
    "In the passive no-shield log of the baseline policies (|lat| ≥ 68°, ten seeds, 8,682 attempts; Appendix D, Table D1A) the mean lead is 9.09 s, 37.7% of attempts sit in the 6–8 s bucket and 8.1% (705 attempts) fall in the 14–16 s band immediately below the crossing, with 8.9% at or above 16 s. The crossing is therefore *sampled but thin*: with 91 late handovers among those 705 attempts the local late rate has a standard error of ≈1.3 pp, and the band is ≈4.6× thinner than the modal bucket. Separately, the rule-applied logs (Table D1B) put 91.1% of their attempts at 16 s, which is the rule's own signature and is reported as a consistency check only—the two panels are never pooled.",
    "claim2-pct",
)

# ---- +0.4 -> +0.37 -------------------------------------------------------
rep(
    "reach 92.1% versus 91.8% with no injection at all (+0.4 pp on five seeds)",
    "reach 92.1% versus 91.8% with no injection at all (+0.37 pp on five seeds)",
    "gate-037",
)

# ---- tolerance wording ---------------------------------------------------
rep(
    "(i) the full-system margin over the hand-crafted baseline is small (+0.9–1.2 pp, i.e. at or just beyond a 1 pp tolerance)",
    "(i) the full-system margin over the hand-crafted baseline is small (+0.9–1.2 pp, i.e. at or just beyond the 1.2 pp tolerance defined in Section VI-A)",
    "lim7-tol",
)

# ---- lockbox five-seed coverage -----------------------------------------
rep(
    "in the margin study of Section V-D the same probe was run on **five** policy seeds at each of three physics regimes and returned the identical threshold at every seed and regime (16/18/20 s), and the two lockbox probes (seeds 0 and 4) agreed exactly, down to the per-advance late rates.",
    "in the margin study of Section V-D the same probe was run on **five** policy seeds at three physics regimes—nominal, +2 s and +3.2 s of drift, i.e. every regime *except* +4.4 s, where Table IV shows one seed probing 20 s instead of 22 s—and returned the identical threshold at every seed and regime (16/18/20 s); the two lockbox probes (seeds 0 and 4) agreed exactly, down to the per-advance late rates.",
    "five-seed-scope",
)

# ---- Table II note: campaign 16 s vs 0.87% ------------------------------
rep(
    "| **mined-rule campaign arm (16 s, no margin)** | **0.6%** | 3.6% | 2.3% | **93.6 ± 0.7** |",
    "| **mined-rule campaign arm (16 s, no margin)** | **0.6%** | 3.6% | 2.3% | **93.6 ± 0.7** |\n\n*Note.* The 0.6% late share here is the campaign protocol (training with the rule in the loop, ten seeds); the frozen-policy factorial reports 0.87% for the same 16 s rule on common episodes (Table C1). The difference is the protocol, not the rule, and neither number belongs to the deployed 18 s arm (0.00%).",
    "table2-note",
)

# ---- Table VI naming -----------------------------------------------------
rep(
    "| Twin | arm | no shield | + shield | binding class after shield |\n|---|---|---|---|---|\n| seam disabled | full system | 70.9 | 96.1 | window/route ≈ 4% |\n| seam disabled | PPO-MLP | 61.4 | 95.8 | window/route ≈ 4% |\n| feeder 3 slots | full system | 54.2 | 79.4 | no_route ≈ 20% |\n| feeder 3 slots | PPO-MLP | 54.7 | 79.9 | no_route ≈ 20% |",
    "| Twin | arm (frozen checkpoints) | no shield | + shield | binding class after shield |\n|---|---|---|---|---|\n| seam disabled | full-system policies | 70.9 | 96.1 | window/route ≈ 4% |\n| seam disabled | PPO-MLP policies | 61.4 | 95.8 | window/route ≈ 4% |\n| feeder 3 slots | full-system policies | 54.2 | 79.4 | no_route ≈ 20% |\n| feeder 3 slots | PPO-MLP policies | 54.7 | 79.9 | no_route ≈ 20% |",
    "table6-names",
)

# ---- equation (4) readability -------------------------------------------
rep(
    "τ_used = min( τ∗ + m, 24 s ),   m = 2 s,                                                        (4)",
    "τ_used = min(τ∗ + m, 24 s),    m = 2 s                                                          (4)",
    "eq4",
)

P.write_text(t, encoding="utf-8")
print("EN v7 edits applied")
