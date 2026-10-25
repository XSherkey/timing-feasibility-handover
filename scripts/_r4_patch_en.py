"""R4 (v6): apply the fourth review's must-fix list to paper_en.md."""
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


# ---- 2. Table D1 counts vs prose (load-bearing) ---------------------------
rep(
    "In our passive logs, by contrast, the advance distribution concentrates *below* the requirement: the polar mean lead is 9.5–11.3 s against a 16 s need, and only 0.3% of polar attempts (67 of 22,807) fall in the 14–16 s bucket, with a further 1.5% above 16 s (Appendix D, Table D1).",
    "In our passive logs, by contrast, the advance distribution concentrates *below* the requirement: the mean lead is 9.5–11.3 s against a 16 s need. In the near-polar band that the rule scopes (|lat| ≥ 68°; Appendix D, Table D1), only 0.3% of attempts (67 of 22,807) fall in the 14–16 s bucket immediately below the crossing, while 92.5% sit at or above 16 s—91.1% of them exactly in the 16–18 s bucket—because the deployed arms apply the mined rule at evaluation. The band that would *locate* the crossing is therefore the thin one; the mass at 16 s is mass at the rule's own value, which confirms that the rule is applied but says nothing about where the crossing lies.",
    "D1-counts",
)

# ---- 3. VI-A contradiction ------------------------------------------------
rep(
    "a lockbox evaluation window never touched by any selection step; re-running the headline comparisons under that lockbox protocol is outstanding work (Limitation 7).",
    "a lockbox evaluation window never touched by any selection step. The lockbox comparison is executed in the next paragraph; what it does and does not constrain is recorded in Limitation 7.",
    "VIA-contradiction",
)

# ---- 9. "retired" -> "bounded" -------------------------------------------
rep(
    "and Limitation 7 is retired in favor of the residual caveats restated there.",
    "and Limitation 7 is *bounded*—reduced from \"not evaluated\" to \"evaluated under frozen selection\"—rather than retired; the residual caveats are restated there.",
    "retired",
)

# ---- 4. lockbox probe seeds ----------------------------------------------
rep(
    "Two points of bookkeeping on that probe: it was executed on two representative policy seeds (0 and 4) rather than all ten, because the probed quantity is a property of the twin's acquisition physics rather than of the policy seed, and the two independent probes agreed exactly (16 s, identical per-advance late rates); and the value was frozen before any lockbox rollout, so no lockbox data entered it.",
    "Two points of bookkeeping on that probe. First, it was executed on two policy seeds (0 and 4) rather than all ten, and we do not claim that the threshold is independent of the policy seed—Proposition 3(iii) says the deployment distribution is policy-dependent. What we can say is empirical and narrower: in the margin study of Section V-D the same probe was run on **five** policy seeds at each of three physics regimes and returned the identical threshold at every seed and regime (16/18/20 s), and the two lockbox probes (seeds 0 and 4) agreed exactly, down to the per-advance late rates. The lockbox therefore uses a **representative threshold frozen from those probes**—an empirical choice justified by five-seed agreement, not a policy-independence result. Second, the value was frozen before any lockbox rollout, so no lockbox data entered it.",
    "lockbox-probe",
)

# ---- 5. ordering (ii) pairing --------------------------------------------
rep(
    "(ii) *Shielded full vs shielded PPO-MLP*: 92.93 vs 91.89, 94.80 vs 93.62, 94.24 vs 93.04. Note that the *unshielded* comparison does **not** favour the full system on the +7 d instance (68.37 vs 69.42), and we do not claim that it does; the controller families are indistinguishable without the shield, as Section VI-B reports on the original episodes.",
    "(ii) *Controller families under the same rule*—the apples-to-apples pairing: full + mined 16 s vs PPO-MLP + mined 16 s, i.e. 92.33 vs 91.89, 94.37 vs 93.62, 93.62 vs 93.04 (+0.44, +0.75, +0.58 pp). The deployed-versus-baseline pairing is a different question and is labelled as such: full + τ_used = 18 s vs PPO-MLP + mined 16 s, i.e. 92.93 vs 91.89, 94.80 vs 93.62, 94.24 vs 93.04. An earlier draft called the second pairing \"shielded full vs shielded PPO-MLP\", which was ambiguous because the two arms carry different thresholds. Note that the *unshielded* comparison does **not** favour the full system on the +7 d instance (68.37 vs 69.42), and we do not claim that it does; the controller families are indistinguishable without a shield, as Section VI-B reports on the original episodes.",
    "pairing",
)

# ---- 6. contribution 2: KM is diagnostic ---------------------------------
rep(
    "The magnitude is recovered by Kaplan–Meier estimation from censored failures and fixed by an active probe on the deployed policy under an isotonic fit, then wrapped in a cost-asymmetric 2 s margin.",
    "Kaplan–Meier estimation of the censored log serves as a diagnostic consistency check, not as the source of the deployed threshold; the magnitude is fixed by an active probe on the deployed policy under an isotonic fit, then wrapped in a cost-asymmetric 2 s margin.",
    "contribution2",
)

# ---- 7. Intro over-strong ------------------------------------------------
rep(
    "so the region of advance space where outcomes are informative—just below and just above the requirement—is almost never exercised; no estimator, however much data the same logging process supplies, can identify a quantity where its inputs never go (Proposition 2).",
    "so the region of advance space where outcomes are informative—just below the requirement—is covered two orders of magnitude more thinly than the region the policy actually operates in (67 of 22,807 near-polar attempts in this system), and within any budget a field study can afford the bound is therefore effectively unidentifiable from that stream alone (Proposition 2: effective-support failure under a sample budget, not an information-theoretic impossibility).",
    "intro-strong",
)

# ---- 8. ledger naming in Table II and Fig. 2 -----------------------------
rep(
    "| **full system (mined + shield)** | **0.6%** | 3.6% | 2.3% | **93.6 ± 0.7** |",
    "| **mined-rule campaign arm (16 s, no margin)** | **0.6%** | 3.6% | 2.3% | **93.6 ± 0.7** |",
    "table2-name",
)
rep(
    "the same knowledge as a shield on the baseline's policies 91.8; the **mined-rule campaign arm** (16 s shield, no margin) 93.6; the **tuned constant** (18 s lead, no learning) 94.0.",
    "the same knowledge as a shield on the baseline's policies 91.8; the **mined-rule campaign arm** (16 s shield, no margin) 93.6; the **tuned constant** (18 s lead, no learning) 94.0.",
    "fig2-name-noop",
)

# ---- I. small numbers ----------------------------------------------------
rep(
    "while rejecting none of the system's own good proposals in the tested runs (+0.4 pp)",
    "while leaving the system's own good proposal intact (+0.37 pp on five runs—a descriptive statement, not a guarantee of never rejecting)",
    "abstract-04",
)
rep(
    "the gaps are +1.04, +1.18 and +1.20 pp, so the tolerance is **1.2 pp** (an earlier draft said \"within 1 pp\", which the numbers do not support).",
    "the gaps are +1.04, +1.18 and +1.20 pp, so the tolerance is **≤ 1.20 pp** (an earlier draft said \"within 1 pp\", which the numbers do not support).",
    "tolerance",
)
rep(
    "**Table C1′. Deployed-threshold completion and oracle reference, polar HSR (%) per seed, common episodes.**",
    "**Table C2. Deployed-threshold completion and oracle reference, polar HSR (%) per seed, common episodes.**",
    "table-c2",
)
rep(
    "**Table C2. Drift response per seed, polar HSR (%): fixed 18 s constant / probe-calibrated (τ∗ in parentheses), common episodes.**",
    "**Table C3. Drift response per seed, polar HSR (%): fixed 18 s constant / probe-calibrated (τ∗ in parentheses), common episodes.**",
    "table-c3",
)
rep(
    "It answers three reviewable questions directly: whether the 14–18 s band is empty (it is thin, not empty: 67 attempts in the 14–16 s bucket),",
    "It answers three reviewable questions directly: whether the 14–18 s band is empty (it is thin, not empty: 67 attempts in the 14–16 s bucket, against 20,771 in 16–18 s),",
    "d1-text",
)

P.write_text(t, encoding="utf-8")
print("EN v6 edits applied")
