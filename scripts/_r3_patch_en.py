"""R3 revision: apply the reviewer's seven must-fix items to paper_en.md.

Every replacement is checked to occur exactly once; the script aborts otherwise so a
silent no-op cannot slip into the build.
"""
from __future__ import annotations

from pathlib import Path

P = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本" / "paper_en.md"
t = P.read_text(encoding="utf-8")
applied = []


def rep(old: str, new: str, label: str) -> None:
    global t
    n = t.count(old)
    if n != 1:
        raise SystemExit(f"[{label}] expected 1 occurrence, found {n}")
    t = t.replace(old, new, 1)
    applied.append(label)


# ---------------------------------------------------------------- fix 3: Prop 1 plateau
rep(
    "Suppose failures vanish above some grid point: p(a) = 0 for all a ≥ ā (in the nominal-physics probe data ā = 16 s).",
    "Suppose failures vanish above some grid point: p(a) = 0 for all a ≥ ā. Two grid points must be kept apart here, because an earlier draft conflated them. The probe's ε = 5% crossing is τ* = 16 s, which is a *quantile*, not a zero-failure point. The first grid point at which the measured late-handover share is exactly zero is ā = 18 s (deployed τ = 18 s arm: 0.87% late at 16 s, 0.00% at 18 s). The corollary applies to ā = 18 s; with ā = 16 s it would be false, and the 0.87% residual is exactly why the deployed algorithm carries the 2 s margin.",
    "P1-plateau",
)
rep(
    "(ii) *Plateau corollary—the only global conclusion we claim.*",
    "(ii) *Plateau corollary—the only global conclusion we claim.*",
    "P1-noop",
)
rep(
    "so *every* global maximizer satisfies a*(λ) ≤ ā:",
    "so *every* global maximizer satisfies a*(λ) ≤ ā (with ā = 18 s in this twin; the bound with ā = 16 s would require the 0.87% residual to be zero, which it is not):",
    "P1-bound",
)

# ---------------------------------------------------------------- fix 2: Prop 2 support claim
rep(
    "In our passive logs, by contrast, the advance distribution concentrates *below* the requirement (polar mean lead 9.5–11.3 s against a 16 s need; essentially no attempts in the 14–18 s band), so the informative region is never visited: no estimator fed by that logging process identifies the quantile, at any sample size. The failure is one of *support*, not of censoring alone—and it is permanent for that logging process, while a designed experiment that forces coverage restores identification (Proposition 4).",
    "In our passive logs, by contrast, the advance distribution concentrates *below* the requirement: the polar mean lead is 9.5–11.3 s against a 16 s need, and only 0.3% of polar attempts (67 of 22,807) fall in the 14–16 s bucket, with a further 1.5% above 16 s (Appendix D, Table D1). The informative region is therefore not *absent*—its support is positive, and infinitely many samples from this logging process would identify the quantile there—but it is *thin*, and at any budget a field study can afford the quantile is effectively unidentifiable: the count in the informative band is what the estimate would rest on, and that count is 67. We therefore claim **effective-support failure under a sample budget**, not information-theoretic impossibility: the passive log under-covers the informative region by two orders of magnitude relative to the region where the policy actually operates, which makes the crossing estimated from it dominated by noise (the probe's own run-to-run sd is 2.45 s at 2 episodes per advance), and a designed experiment that forces coverage removes the limitation (Proposition 4).",
    "P2-support",
)
rep(
    "The correct and narrower statement is Claim 2: in passive operation of this system, the informative region is never exercised, so the bound is invisible to any learner fed by the passive stream—until an experiment changes the support.",
    "The correct and narrower statement is Claim 2: in passive operation of this system the informative region is *thinly* exercised (67 attempts out of 22,807), so within any affordable sample budget the bound is effectively invisible to a learner fed by the passive stream—until an experiment changes the support and pays for the coverage it needs.",
    "P2-remark",
)
rep(
    "so the informative region of the outcome data is never covered—a support failure, formalized in Proposition 2—and the naive reading of the log is biased downward by censoring.",
    "so the informative region of the outcome data is barely covered (67 of 22,807 polar attempts)—an *effective*-support failure, formalized in Proposition 2—and the naive reading of the log is biased downward by censoring.",
    "P2-abstract",
)

# ---------------------------------------------------------------- fix 2b: KM is a diagnostic
rep(
    "the magnitude is recovered from censored logs by Kaplan–Meier estimation and fixed by an active probe executed on the *deployed* policy, with a cost-asymmetric safety margin",
    "the magnitude is fixed by an active probe executed on the *deployed* policy (with Kaplan–Meier estimation of the censored log used as a diagnostic consistency check, not as the source of the deployed threshold), plus a cost-asymmetric safety margin",
    "KM-abstract",
)

# ---------------------------------------------------------------- fix 7: positioning
rep(
    "We argue this reframes the design question for learned controllers in satellite networks: what matters is where operational knowledge lives, how it is obtained, and whether it can be audited.",
    "We argue this reframes the design question for learned controllers in satellite networks: what matters is where operational knowledge lives, how it is obtained, and whether it can be audited. The paper is deliberately a systems-and-audit contribution with formal scope notes—Propositions 1–4 delimit where the reward channel, the passive log, the projection and the probe can and cannot be trusted—rather than a new theory of constrained reinforcement learning.",
    "positioning-abstract",
)

# ---------------------------------------------------------------- fix 1: Prop 3 proof
rep(
    "P_D( late under Π_τ ) = P_D( T_z > τ ) ≤ ε,                                    (3)",
    "P_D( late under Π_τ ) = P_D( T_z > max(a, τ) ) ≤ P_D( T_z > τ ) ≤ ε,             (3)",
    "P3-eq",
)
rep(
    "*Proof.* (i) Under Π_τ every attempt's timing advance is ≥ τ, and the attempt is late exactly when T_z > τ; hence P(late under Π_τ) = P_D(T_z > τ) = 1 − F_z,D(τ) ≤ ε by the quantile property.",
    "*Proof.* (i) Under Π_τ the executed advance is max(a, τ), which is ≥ τ, so the timing failure event satisfies {late under Π_τ} = {T_z > max(a, τ)} ⊆ {T_z > τ}. Hence P_D(late under Π_τ) ≤ P_D(T_z > τ) ≤ ε by the quantile property. The inclusion is strict whenever the policy already chose a > τ (the projection then leaves the action unchanged and the attempt can still be late for T_z ∈ (τ, a]); the bound therefore holds with equality only in the special case a ≤ τ almost surely.",
    "P3-proof",
)
rep(
    "a bound that follows directly from the definition of a quantile—no multiplication of probabilities, no conditional-independence assumption.",
    "a bound that follows directly from the definition of a quantile and from the event inclusion above—no multiplication of probabilities, no conditional-independence assumption.",
    "P3-sentence",
)
rep(
    "Because D is policy-dependent, a τ calibrated on one policy's distribution is a bound for that distribution: transferring it to another controller or operator intent is an empirical question, tested in Section VI-F, not a consequence of (3).",
    "Because D is policy-dependent, a τ calibrated on one policy's distribution is a bound for that distribution: transferring it to another controller or operator intent is an empirical question, tested in Section VI-F, not a consequence of (3). In the notation of (3), D is the deployment distribution, while τ is calibrated under a calibration distribution D_cal produced by the policy (and the physics) at measurement time; (3) is exact only when D = D_cal, and the gap D ≠ D_cal is the drift term re-measured in Section VI-D, not a defect of the bound.",
    "P3-D",
)

# ---------------------------------------------------------------- fix 4: ledger pipe-free + naming
rep("`min_advance:16 @ \\|lat\\| ≥ 68`, as mined", "`min_advance:16 @ lat_abs ≥ 68`, as mined", "ledger-1")
rep("`min_advance:18 @ \\|lat\\| ≥ 68`", "`min_advance:18 @ lat_abs ≥ 68`", "ledger-2")
rep("`min_advance:20 @ \\|lat\\| ≥ 68`", "`min_advance:20 @ lat_abs ≥ 68`", "ledger-3")
rep(
    "the mined rule `min_advance:16 @ |lat| ≥ 68` is the *τ* rule* (the estimate, margin not applied), not τ_used.",
    "the mined rule `min_advance:16 @ lat_abs ≥ 68` is the *τ\\* rule* (the estimate, margin not applied), not τ_used. Four names are used throughout the paper and nowhere else: **mined-rule campaign arm** (τ* = 16 s, no margin; the 93.6% figure), **deployed probe-calibrated algorithm** (τ_used = 18 s; 93.31% at nominal physics), **tuned constant** (18 s lead, no learning; 94.0%) and **oracle shield** (per-attempt realized requirement; 93.31%).",
    "ledger-names",
)

# ---------------------------------------------------------------- fix 5: lockbox precision
rep(
    "Four orderings are tested: (i) any shield beats no shield; (ii) full-system policies beat the PPO-MLP baseline; (iii) the full system with its validation-calibrated shield is within 1 pp of the baseline under its best rule; (iv) the decision-layer shield beats the best reward-penalty coefficient.",
    "Four orderings are tested, each with an explicit pairing, because an earlier draft left them ambiguous. (i) *Within a policy family*, the shield beats no shield on identical episodes: full 92.93/94.80/94.24 vs 68.37/71.12/72.47, and PPO-MLP 91.89/93.62/93.04 vs 69.42/72.32/73.36. (ii) *Shielded full vs shielded PPO-MLP*: 92.93 vs 91.89, 94.80 vs 93.62, 94.24 vs 93.04. Note that the *unshielded* comparison does **not** favour the full system on the +7 d instance (68.37 vs 69.42), and we do not claim that it does; the controller families are indistinguishable without the shield, as Section VI-B reports on the original episodes. (iii) The full system with its validation-calibrated shield is within a stated tolerance of the baseline under its best rule: the gaps are +1.04, +1.18 and +1.20 pp, so the tolerance is **1.2 pp** (an earlier draft said \"within 1 pp\", which the numbers do not support). (iv) The decision-layer shield beats the best reward-penalty coefficient: 92.93 vs 81.83, 94.80 vs 84.41, 94.24 vs 84.49.",
    "lockbox-orderings",
)
rep(
    "The single calibration input re-anchored before lockbox evaluation is the threshold probe, re-run on the *validation* window only (never the evaluation window): it returns τ* = 16 s (identically on seeds 0 and 4), giving τ_used = 18 s; the mined rule, the gate decisions, and λ = 8 remain exactly as originally frozen.",
    "the single calibration input re-anchored before lockbox evaluation is the threshold probe, re-run on the *validation* window only (never the evaluation window): it returns τ* = 16 s, giving τ_used = 18 s. Two points of bookkeeping on that probe: it was executed on two representative policy seeds (0 and 4) rather than all ten, because the probed quantity is a property of the twin's acquisition physics rather than of the policy seed, and the two independent probes agreed exactly (16 s, identical per-advance late rates); and the value was frozen before any lockbox rollout, so no lockbox data entered it. The mined rule, the gate decisions, and λ = 8 remain exactly as originally frozen—which also means that the *selection* of those three items still originates in the original evaluation window; the lockbox freezes that selection and measures it, it does not re-select anything.",
    "lockbox-calib",
)

# ---------------------------------------------------------------- fix 6: gate counts
rep(
    "Of the six, four degrade held-out success outright and a fifth buys almost nothing; without the replay stage, five of the six—including three harmful ones—would have been committed.",
    "Counting precisely: four of the six degrade held-out success outright (−1.5, −3.1, −2.1, −2.8 pp), a fifth (+1.5 pp) does not reach the 5 pp admission bar, and only the system's own proposal is admitted. An earlier draft wrote \"three harmful ones\"; the count is four. Without the replay stage a gate-less pipeline would have committed all six, four of them harmful.",
    "gate-counts",
)
rep(
    "a paired +42.9 pp, 5/5 seeds in the same direction (Fig. 7, left). In the replacement design (the harmful candidate displaces the model's proposal, n = 10), gate on 70.1% vs gate off 51.0%, +19.1 pp, Wilcoxon p = 0.002 (Fig. 7, right).",
    "a paired +42.9 pp, 5/5 seeds in the same direction (Fig. 7, left)—a descriptive result at n = 5, for which the smallest attainable two-sided Wilcoxon p is 0.0625, so no significance claim is attached to it. In the replacement design (the harmful candidate displaces the model's proposal, n = 10), gate on 70.1% vs gate off 51.0%, +19.1 pp, Wilcoxon p = 0.002 (Fig. 7, right); that is the design that carries the statistical claim.",
    "gate-stats",
)

# ---------------------------------------------------------------- fix 5b: limitation 7 tolerance
rep(
    "(i) the full-system margin over the hand-crafted baseline is small (+0.9–1.2 pp)—the value is the constraint, not the controller;",
    "(i) the full-system margin over the hand-crafted baseline is small (+0.9–1.2 pp, i.e. at or just beyond a 1 pp tolerance)—the value is the constraint, not the controller;",
    "lim7",
)

# ---------------------------------------------------------------- fix 6b: cross-intent wording already preliminary; tighten
rep(
    "This is, to our knowledge, the first controlled measurement of cross-intent transfer for mined constraints in this setting; with n = 5 per arm and the evaluation window shared with calibration (Section VI-A), it is *preliminary evidence* of transfer within this twin, not a general law of cross-intent reuse.",
    "This is, to our knowledge, the first controlled measurement of cross-intent transfer for mined constraints in this setting; with n = 5 per arm, no lockbox replication of this particular contrast, and the evaluation window shared with calibration (Section VI-A), it is *preliminary evidence* of transfer within this twin—a hypothesis with a measured effect size, not a general law of cross-intent reuse.",
    "transfer-wording",
)

P.write_text(t, encoding="utf-8")
print("applied", len(applied), "edits:")
for a in applied:
    print("  -", a)
