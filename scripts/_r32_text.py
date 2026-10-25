"""R32 pass 1: the wording/definition fixes of review 25 (no new data yet)."""
from __future__ import annotations

import re
from pathlib import Path

D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"
p = D / "paper_en.md"
t = p.read_text(encoding="utf-8")
done = []


def rep(old, new, label):
    global t
    n = t.count(old)
    if n != 1:
        print("  MISS", label, n)
        return
    t = t.replace(old, new, 1)
    done.append(label)


# ---------------------------------------------------------------- 1. abstract: precision, not impossibility
rep("The bound is not recoverable from the passive log: only 8.1% of attempts fall in the informative band, and a "
    "cluster bootstrap over (seed, site) blocks places the 5% crossing anywhere between 10 s and 18 s.",
    "The passive log localises that bound to about 0.2 s in point estimate but not to the 2 s precision a deployment "
    "needs: the informative band holds only 8.1% of attempts, and a cluster bootstrap over (seed, site) blocks places "
    "the 5% crossing anywhere between 10 s and 18 s. Censoring alone therefore implies no impossibility—it implies a "
    "precision floor that a controlled probe removes.", "abstract precision claim")

# ---------------------------------------------------------------- 2. abstract: the upper bound is a test, not a win
rep("The same three stages also learn an *upper* bound: a visibility-relative cap cuts the window violations the "
    "lower bound introduces by three quarters but converts them one-for-one into late failures, so the success rate "
    "is unchanged—the two bounds act on one interval, and its length, not either endpoint, sets the score.",
    "We also run the same three stages on an *upper* bound: a visibility-relative cap cuts the window violations the "
    "lower bound introduces by three quarters but converts them one-for-one into late failures, so the success rate is "
    "unchanged and the guard is not identifiable from it—the two bounds act on one interval, and its length, not either "
    "endpoint, sets the score.", "abstract upper bound")

# ---------------------------------------------------------------- 3. intro: who owns 23.4 of 24.1
rep("a single timing constraint, applied at decision time, is worth 23.4 of the 24.1 pp gap between a reward-only "
    "baseline and the deployed system",
    "a single timing constraint, applied at decision time, is worth 23.4 of the 24.1 pp gap between a reward-only "
    "baseline (68.37%) and the *mined-rule* arm at 16 s (92.44%); the deployed 18 s arm adds the 2 s margin on top of "
    "that and lands at 93.36%, and we keep the two accounts separate throughout", "intro bookkeeping")

# ---------------------------------------------------------------- 4. Prop 3: protected scope
rep("let D denote the per-attempt deployment distribution over contexts and requirements.",
    "let A_Π = {attempts on which P_z holds} be the *protected scope*—the only attempts the projection touches—and let "
    "D be the per-attempt deployment distribution over contexts and requirements, with D_Π its restriction to A_Π.",
    "prop3 scope definition")

rep("*Claim.* (i) *Additive bound—what a quantile gives without any further assumption.* If τ is a (1−ε)-quantile of "
    "T_z under D, i.e., P_D(T_z ≤ τ) ≥ 1 − ε, then the late-handover contribution to failure under the shield is "
    "bounded by ε:",
    "*Claim.* (i) *Additive bound—what a quantile gives without any further assumption.* The bound is stated on the "
    "protected scope, because attempts outside A_Π are not projected and can fail late at their own rate. If τ is a "
    "(1−ε)-quantile of T_z under D_Π, i.e., P_{D_Π}(T_z ≤ τ) ≥ 1 − ε, then the late-handover contribution to failure "
    "inside the scope is bounded by ε:", "prop3 claim scoped")

t, n = re.subn(r"P_D\( late under Π_τ \) = P_D\( T_z > max\(a, τ\) \)",
               "P_{D_Π}( late under Π_τ ) = P_{D_Π}( T_z > max(a, τ) )", t)
print("  eq(4) LHS scoped:", n)
t, n2 = re.subn(r"≤ P_D\( T_z > τ \) ≤ ε\.", "≤ P_{D_Π}( T_z > τ ) ≤ ε.", t)
print("  eq(4) RHS scoped:", n2)
if n and n2:
    done.append("eq(4) scoped")

# ---------------------------------------------------------------- 5. Prop 4: what the probe actually does
rep("*Claim.* The forced-advance experiment observes π(a) = P(late | a) = P(T_z > a), a non-increasing survival "
    "function, on the grid G = {6, 8, …, 26} s.",
    "*Setup, stated because it bounds what the probe can claim.* The probe does not rerun whole episodes at fixed "
    "advances. Inside one continuous stream it overrides the *commanded* advance on a random subset of polar attempts, "
    "sampling the grid at each decision epoch, and records the realised requirement T_z = t_setup of every attempt. "
    "The estimated curve is therefore the empirical survival function of the realised requirements, "
    "π(a) = P(T_z > a), read off the attempts that were forced to each grid point; it is an intervention on the called "
    "action, not a frozen-state counterfactual, and the stream continues to evolve after each override. Two "
    "consequences follow: the requirement sample is not conditioned on the commanded lead except through trajectory "
    "feedback (a forced attempt changes which attempts are observed later), and the estimate is therefore an "
    "approximation whose error we report empirically rather than bound.\n\n*Claim.* The forced-advance experiment "
    "observes π(a) = P(late | a) = P(T_z > a), a non-increasing survival function, on the grid G = {6, 8, …, 26} s.",
    "prop4 intervention semantics")

# ---------------------------------------------------------------- 6. Prop 1: zero is a finite-sample statement
rep("(In the twin the latter condition holds across the full λ scan of Section VI-C: even at λ = 64 the mean "
    "realized lead stays near 10 s.)",
    "(In the twin the mean realised lead stays near 10 s across the full λ scan of Section VI-C, which is consistent "
    "with that condition but does not verify it action by action; we report it as consistent evidence, not as proof.)",
    "prop1 condition scoped")

rep("The first grid point at which the measured late-handover share is exactly zero is ā = 18 s",
    "The first grid point at which no late handover is observed in the evaluation sample is ā = 18 s—a finite-sample "
    "statement, not a proof that p(18) = 0 in the population",
    "prop1 zero-failure empirical")

# ---------------------------------------------------------------- 7. KM competing risks
rep("We report the censored-aware numbers with the caveat that Assumption A (non-informative censoring) is a modeling "
    "assumption;",
    "Two scope statements belong here. Assumption A (non-informative censoring) is a modelling assumption; and because "
    "the estimator keeps only successes and late handovers, it targets the requirement *conditional on no competing "
    "failure*, so `no_route` and `window_exceeded` are excluded by design—a restriction that is only valid if those "
    "classes carry no information about T_z beyond the region, which we cannot verify from the log and therefore "
    "report as a limitation of the diagnostic rather than of the threshold. We report the censored-aware numbers with "
    "that caveat;", "KM competing risks")

t = re.sub(r"\n{3,}", "\n\n", t)
p.write_text(t, encoding="utf-8")
print("edits:", done)
