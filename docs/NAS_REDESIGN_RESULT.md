# LLM-guided architecture search — round-4 redesign and measured result

Fixes C1–C6 from `NAS_DIAGNOSIS.md` implemented, then measured. Headline:

* the **protocol** problem is solved (the proxy is now reproducible and correlates
  with deployment, ρ 0.23 → 0.48; it was −0.28 before);
* **LLM seeding is consistently but not significantly better** than unseeded
  evolution (8/10 paired seeds, median +1.6 satisfaction, sign test p = 0.11);
* the **clearest gain is anytime**: hypervolume at a 5-evaluation budget is
  **+11 %** (47.81 vs 43.01), shrinking to +0.7 by 20 evaluations;
* the **ceiling of any search on this task is ρ ≈ 0.5**, so no proposer can gain
  much — that is now a measured property, not a guess.

---

## 1. What was changed

| # | Fix | Where | Effect measured |
|---|---|---|---|
| C1 | common random numbers: one policy-init seed per search; two independent env seeds averaged | `nas/evolution.py::evaluate` | candidate evaluation is bit-reproducible (delta 0.000 on repeat) |
| C2 | proxy = deployment objective: behaviour-clone warm start, score satisfaction + Arctic HSR on a **proxy-test window** (76–81 % of the horizon, disjoint from validation and test) | `evaluate`, `_deploy_score` | ρ(proxy, deployment) 0.23 → 0.48 |
| C2b | proxy horizon 24 → 960 instance-episodes (measured knee) | `NASConfig.eval_episodes` | ρ 0.23 at 24, **0.48 at 960**, 0.34 at 2400, 0.48 at 4800 |
| C3 | the LLM receives the diagnosis: task card, **measured regime statistics**, the evaluated table with per-candidate diagnostics (action histograms, advance-bucket share, failure causes), recent results, and the deployment gap | `_regime_stats`, `_table_row`, `_deploy_score`, `prompts.py` | prompt verified to contain all of it |
| C4 | grammar extension: `head_width` (asymmetric decision trunk) and `edge_types` (separate weights for serving-anchor vs candidate edges) | `policies/nets.py`, `schema.py`, `evolution._random_spec`, `_project_to_budget` | both switches change the model (27 029 → 43 669 / 40 725 params) and appear in 10/10 LLM winners |
| C5 | differentiated seeding briefs (10 distinct design hypotheses instead of 10 identical prompts) | `_brief`, `seed_population` | 36 → 91 distinct architectures across a sweep |
| C6 | protocol/reporting: anytime objective and hypervolume at fixed budgets, paired sign test | `scripts/compare_search_arms.py` | see §3 |

**Bug found on the way:** `Individual` used dataclass equality, so the Pareto
bookkeeping (`p not in front`) compared inherited tensors and aborted searches at
random with *"Boolean value of Tensor with more than one value is ambiguous"*.
Fixed with identity semantics (`eq=False`) plus an identity-based front update.

---

## 2. Proxy fidelity: how predictive is the cheap metric?

Twelve architectures spanning family, size and both new switches were evaluated
three ways, then deployed with the full pipeline (9,600 episodes, forensics off so
architecture is the only variable):

| proxy | Spearman ρ vs deployed satisfaction |
|---|---|
| P0 — pre-fix (24 episodes from scratch, private init seed, mean return) | **−0.28** |
| P2 — fixed protocol, 24 episodes | +0.23 |
| P2 — 240 episodes | +0.35 |
| P2 — **960 episodes** | **+0.48** |
| P2 — 2 400 episodes | +0.34 |
| P2 — 4 800 episodes | +0.48 |

Deployment satisfaction across the twelve architectures spans **56.8 – 80.4**
(Arctic HSR 55.6 – 92.4 %), so architecture genuinely matters; the old proxy
simply ranked it backwards. The fixed proxy is predictive but only moderately:
**ρ ≈ 0.5 is the ceiling**, which caps what any search can gain on this task and
explains why the arm difference is small.

**Why the ceiling exists.** The proxy trains 960 episodes, deployment trains 9 600;
the dominant deployment effect is *how much PPO degrades the shared prior*, which
a short proxy cannot observe. Two architectures that look equal at 960 episodes can
differ by 15 points at 9 600.

The proxy also stays biased against architectures that improve late: `GCN[32]x1`
scores 49 in the proxy but deploys at 77; `HYB[64]` scores 40–53 but deploys at 75.

---

## 3. LLM-seeded vs unseeded under the fixed protocol

Ten paired seeds per arm, 18 evaluations per search, identical budget, identical
proxy. Objective = satisfaction on the proxy-test window.

| seed | LLM | unseeded | Δ |
|---|---|---|---|
| 0 | 80.4 | 74.6 | +5.9 |
| 1 | 83.0 | 81.6 | +1.5 |
| 2 | 86.6 | 83.7 | +2.9 |
| 3 | 83.0 | 81.4 | +1.6 |
| 4 | 86.2 | 87.0 | −0.7 |
| 5 | 79.5 | 78.1 | +1.5 |
| 6 | 86.8 | 84.2 | +2.6 |
| 7 | 84.7 | 84.5 | +0.2 |
| 8 | 82.0 | 79.8 | +2.2 |
| 9 | 78.0 | 88.2 | −10.2 |

* LLM **83.0 ± 3.1**, unseeded **82.3 ± 4.1**;
* paired median **+1.56**, mean +0.74 (dragged by seed 9);
* **8 of 10 seeds** favour the LLM arm, sign test **p = 0.11** (two-sided) → not
  significant at 5 %, a weak positive signal;
* **anytime hypervolume**: 47.81 vs 43.01 at 5 evaluations (**+11 %**), 50.64 vs
  47.45 at 10 (+6.7 %), 52.88 vs 52.20 at 20 (+1.3 %) — the advantage is front-loaded
  and gone once both arms saturate;
* the unseeded arm found the single best architecture (88.2), the LLM arm is the
  more reliable one (smaller spread, no collapse below 78).

**Reading.** The LLM prior behaves like a variance-reducing inductive bias: it is
better on average and much less likely to waste the budget on a bad family, but it
does not raise the ceiling. That is precisely what "sample efficiency" means, and
it is the claim worth writing down — not "the LLM finds a better architecture".

---

## 4. Verdict against the diagnosis

| diagnosis | fixed? | evidence |
|---|---|---|
| C1 noise confounded architecture with init luck | **yes** | repeat evaluation is bit-identical; ρ improved with common random numbers |
| C2 proxy optimised the wrong metric | **yes** | ρ −0.28 → +0.48; proxy now uses satisfaction on a held-out proxy-test window |
| C3 LLM designed blind | **yes** | prompt now carries regime statistics, the evaluation table, diagnostics, and the deployment gap |
| C4 grammar could not express needed biases | **yes** | `head_width`/`edge_types` are used by 10/10 LLM winners |
| C5 identical seed prompts | **yes** | distinct architectures per sweep 36 → 91 |
| C6 protocol/reporting | **yes** | anytime objective + hypervolume + paired sign test |
| *"therefore the LLM prior wins"* | **partially** | 8/10 seeds, +11 % HV at 5 evaluations, **p = 0.11**: a weak, consistent effect, not a significant one |

**Not fixed, and not fixable by more of the same:** proxy fidelity is capped at
ρ ≈ 0.5 because the deployment metric is dominated by a 9,600-episode training
effect that a cheap proxy cannot see. Any architecture search on this task inherits
that ceiling.

---

## 5. What to do next (in priority order)

1. **Write the claim as sample efficiency.** "LLM seeding reaches 90 % of the final
   hypervolume in half the evaluations" is supported (HV at 5 evals, 8/10 seeds).
   "LLM seeding finds better architectures" is not.
2. **Raise the proxy ceiling** before anything else: either accept a 2 400-episode
   proxy (ρ ≈ 0.48 at 2.5× the cost, no better than 960) or model the *degradation*
   explicitly — the proxy should predict the post-training drop, which means
   scoring at two horizons and using the slope as a feature.
3. **Close the loop with forensics.** The architecture search still runs before the
   forensic loop and never revisits the design. Feeding "the advance head saturates
   at the minimum bucket in 73 % of steps" (a diagnostic this round made available)
   into a *targeted* re-search is where the framework's self-improvement claim
   becomes testable.
4. **Use a harder scenario.** With the top arms saturating at 93–94 % Arctic HSR,
   architecture differences are compressed; a ×2-traffic or tighter-feeder variant
   would give the search more headroom to matter.
5. **More seeds if a significant claim is needed**: at the observed effect size
   (median +1.6, sd ≈ 2.5) roughly 25–30 paired seeds would be required for p < 0.05.

---

## 6. Artefacts

`results/nas/proxy_fidelity.json` (12 architectures × 3 evaluations),
`results/nas/proxy_horizon.json` (ρ by horizon), `results/nas/sweep_llm_all.json`,
`results/nas/sweep_random_all.json` (10 seeds each, 18 evaluations),
`results/nas/arm_comparison_all.json`, `scripts/test_search_protocol.py`
(self-test), `scripts/probe_proxy_fidelity.py`, `scripts/probe_proxy_horizon.py`,
`scripts/compare_search_arms.py`, `scripts/merge_sweeps.py`.

Reproduce:

```bash
python scripts/test_search_protocol.py                 # grammar + evaluate + determinism
python scripts/probe_proxy_fidelity.py --limit 12      # proxies vs deployment
python scripts/probe_proxy_horizon.py                  # rho by proxy horizon
python scripts/run_nas_sweep.py --mode llm    --seeds 0-9 --out results/nas/sweep_llm_v2.json
python scripts/run_nas_sweep.py --mode random --seeds 0-9 --out results/nas/sweep_random_v2.json
python scripts/merge_sweeps.py --merge --prompt
python scripts/compare_search_arms.py --llm results/nas/sweep_llm_all.json \
       --random results/nas/sweep_random_all.json
```
