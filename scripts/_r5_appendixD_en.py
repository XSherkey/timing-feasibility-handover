"""R5 (v7): replace Appendix D with a two-panel support audit (passive vs rule-applied).

The v6 table pooled the two log regimes, which made the passive-coverage claim circular.
"""
from __future__ import annotations

from pathlib import Path

P = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本" / "paper_en.md"
t = P.read_text(encoding="utf-8")

NEW = """## Appendix D. Support audit for the censored-log claims

The identification claims of Proposition 2 and the KM diagnostics of Section V-A rest on *where attempts actually occur*, so we report the counts—and we now report them **separately for the two log regimes**, because an earlier version pooled them and a reviewer correctly objected that 91% of the pooled mass sat at 16 s. Those masses come from the arms that execute the mined rule at evaluation; a rule-applied log cannot be used to show that the *passive* log under-covers the informative band.

**Table D1A. Passive no-shield logs (PPO-MLP, ten seeds, evaluation episodes without any rule; site |lat| ≥ 68°; 8,682 attempts).**

| advance bucket (s) | attempts | exact events | right-censored | competing risk | share of attempts |
|---|---|---|---|---|---|
| 6–8 | 3,270 | 2,112 | 969 | 189 | 37.7% |
| 8–10 | 1,411 | 714 | 657 | 40 | 16.3% |
| 10–12 | 2,465 | 2,171 | 195 | 99 | 28.4% |
| 12–14 | 56 | 47 | 6 | 3 | 0.6% |
| 14–16 | 705 | 543 | 91 | 71 | 8.1% |
| 16–18 | 568 | 531 | 17 | 20 | 6.5% |
| ≥ 18 | 207 | 200 | 0 | 7 | 2.4% |
| total | 8,682 | 6,318 | 1,935 | 429 | 100% |

Every row satisfies attempts = exact events + right-censored + competing risk, and the column sums match the totals. The passive log places its mass at low advances (mean 9.09 s, median 8.00 s, 37.7% in the 6–8 s bucket); the band immediately below the crossing, 14–16 s, carries 8.1% of attempts (705) and the mass at or above 16 s is 8.9%. The crossing is therefore **sampled but thin**: with 91 late handovers among the 705 attempts in that band, the standard error of the local late rate is ≈1.3 pp, and the band is ≈4.6× thinner than the modal bucket—so a crossing estimated from passive data alone is dominated by sampling noise and by the choice of band edges. That is what we mean by effective-support failure under a budget; it is not an absence of support, and it is not an information-theoretic impossibility.

**Table D1B. Rule-applied logs (deployed arms, ten seeds; the 16 s mined rule executed at evaluation; |lat| ≥ 68°; 22,807 attempts).**

| advance bucket (s) | attempts | exact events | right-censored | competing risk | share of attempts |
|---|---|---|---|---|---|
| 6–8 | 350 | 86 | 228 | 36 | 1.5% |
| 8–10 | 109 | 68 | 26 | 15 | 0.5% |
| 10–12 | 1,152 | 1,041 | 67 | 44 | 5.1% |
| 12–14 | 48 | 45 | 2 | 1 | 0.2% |
| 14–16 | 67 | 39 | 12 | 16 | 0.3% |
| 16–18 | 20,771 | 19,439 | 227 | 1,105 | 91.1% |
| ≥ 18 | 310 | 301 | 0 | 9 | 1.4% |
| total | 22,807 | 21,019 | 562 | 1,226 | 100% |

The 91.1% at 16–18 s is the rule's own signature—an attempt is logged at the advance the controller commanded, and under the rule that is 16 s. We report this panel as a consistency check that the rule was executed, **not** as evidence about coverage; the two panels are never pooled in this paper. (An earlier version reported only the pooled table, which is where the 91% mass came from; the correction changes the percentages in Section IV-C from "67 of 22,807 ≈ 0.3%" to "705 of 8,682 ≈ 8.1%", and removes the "two orders of magnitude" phrasing, which the passive data do not support.)

*Quantile support.* On the passive log the KM curve's quantiles are p50 = 6.80 s, p90 = 13.57 s and p95 = 15.81 s. The 15.80 s quoted in Section IV-C is the |lat| ≥ 70° mixed band; the 0.01 s difference is the band definition, not a discrepancy.

*Sensitivity of Assumption A—stratified naive-vs-KM comparison.* The size of the naive-versus-KM gap depends on how censored the attempts in the sample are, so a single global gap number is misleading. On the mixed campaign (all eight arms, |lat| ≥ 70°) the medians are 4.08 s naive vs 6.45 s KM (2.4 s gap); restricted to the deployed arms (|lat| ≥ 70°) the gap shrinks to 0.49 s (6.47 s vs 6.96 s); at |lat| ≥ 68° it is 6.43 s vs 7.05 s. The p95 is nearly unbiased everywhere (15.76 vs 15.80 s on the mixed campaign; 15.78 vs 15.80 s in the deployed arms). Stratified by state, the median bias stays small: +0.02/+0.03 s across elevation bands (n = 3,493/19,314), +0.00/+0.02/+0.20 s across hop counts (n = 15,606/6,579/622), +0.01 s by plane-change flag, and +0.04/+0.06 s by buffer occupancy (n = 4,515/18,292). The plane-change stratum has 918 attempts and zero successes, so its naive median is undefined—exactly the censoring pattern Assumption A must be checked against. The damage of censoring is therefore not a uniformly shifted median but the removal of the low-advance region from the observable sample, which is what Proposition 2's support argument formalizes.

"""

i = t.find("## Appendix D")
j = t.find("## References")
if i < 0 or j < 0 or i >= j:
    raise SystemExit("Appendix D boundaries not found")
t = t[:i] + NEW + "---\n\n" + t[j:]
P.write_text(t, encoding="utf-8")
print("Appendix D replaced")
