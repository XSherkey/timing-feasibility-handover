# Why the LLM-guided architecture search shows no advantage — diagnosis and redesign

Evidence from this reproduction: `results/nas/sweep_llm.json`, `sweep_random.json`
(5 seeds × 42 evaluations per arm), `results/analysis/bc_vs_final.json`, and the
code in `almond/nas/evolution.py`.

## 0. The one number that explains almost everything

Grouping all 420 proxy evaluations by parameter count and decomposing the variance:

| quantity | value |
|---|---|
| evaluations of the **same** architecture (27,029 params, n = 113) | reward 0.758 – 1.341 |
| **repeat noise** (within-architecture SD) | **0.114** |
| **architecture signal** (between-architecture SD of means) | **0.073** |
| noise / signal | **1.56** |

A single evaluation of a candidate is *noisier than the entire spread between
candidates*. With 42 one-shot evaluations and no repetition, the search is ranking
noise. Under that condition every prior ties: LLM-seeded (1.159 ± 0.132) and
unseeded (1.175 ± 0.135) cannot separate, and any claim about "structural priors"
is untestable. So the current null result is **not evidence that LLM priors are
useless** — it is evidence that the *experiment cannot see them*.

Secondary observation: the LLM arm produced **36 distinct architectures in 210
evaluations**, the random arm **81**. The LLM prior is *reducing* diversity, which
is the opposite of what an exploration prior should do when there is no reliable
signal to exploit.

---

## 1. Root causes, ranked by how much of the gap they explain

### C1 — The fitness evaluation confounds architecture with initialisation luck (largest)

`Evolver.evaluate()` seeds each candidate with `seed = cfg.seed * 100003 + eval_count`
— **a different initialisation for every candidate**. Combined with 24 episodes
(≈3 logged rollouts of 8-env batches × 160 steps), the score is mostly "did this
particular random init escape the collapse basin", which we know is bimodal
(50–70 % of from-scratch runs collapse).

**Fix (cheapest, highest leverage): common random numbers.**
* one fixed policy-init seed and one fixed set of environment seeds for **all**
  candidates in a search;
* average 2–3 independent evaluation seeds (env only) per candidate;
* raise `eval_episodes` to ≥ 60 and keep batch 8;
* report the standard error and re-evaluate the top-k before ranking.

Expected: repeat-noise SD drops by roughly 3–5× (to ≈0.03), at the same or lower
total budget, because the expensive part is training, not the extra env seeds.

### C2 — The proxy objective is not the deployment metric

Fitness = mean episode return after 24 episodes **from scratch**. Deployment =
Arctic HSR / intent satisfaction after 9,600 episodes **with the behaviour-cloned
prior**. We measured the consequence directly: the search picked an MLP that
deployed at **26 %** Arctic HSR while a fixed GCN deployed at **69 %** in the same
pipeline. A noise-free version of this fitness would still optimise the wrong thing.

**Fix: evaluate candidates the way they will be deployed.**
* behaviour-clone the analytic teacher into each candidate first (`PPOTrainer.warm_start`,
  already implemented — the search simply does not use it);
* score with the deployment metric on the validation split: attempt-weighted Arctic
  HSR and intent satisfaction, not mean return;
* two episodes suffice: after cloning the policy already sits at S ≈ 81 %, so the
  metric is informative at episode 0 rather than at episode 9,600;
* optionally add the "learning-curve area" (satisfaction at episodes 0, 300, 900)
  if search speed itself is part of the claim.

### C3 — The LLM is asked to design blind

What the model actually receives today:

| call | payload | problem |
|---|---|---|
| `topology_seed` | regime tags, a **constant** `regime_hint` string, `history=[]` | the prompt has a "previous best families" slot that the code always fills with an empty list; the hint is one hardcoded sentence for every search and every seed |
| `topology_mutation` | the parent sketch + three booleans (`objective`, `too_large`, `underfit`) | no reward value, no failure diagnosis, no per-head statistics |
| `topology_crossover` | two sketches | no performance information at all |
| `population_critique` | four elites' rewards + two rates | only tunes mutation/crossover rates — almost no useful degrees of freedom |

**Fix: give it the diagnosis, not the sketch.** The prompt should carry
* twin statistics: ISL degree and hop histogram, candidate-count distribution,
  fraction of steps with no routed candidate, telemetry ranges at failures;
* the full search table: each candidate's spec, params, latency, proxy score,
  deployment check, and **its category of failure** (e.g. "target head collapses to
  no-handover", "advance head saturates at the minimum bucket", "underfits at low
  elevation");
* the trained proxy policy's diagnostics: action histogram, per-head entropy,
  dominant failure cause from `attempt_log`;
* the mapping from *previous* searches to deployment outcomes (the closed-loop
  feedback missing today).

With that, a proposal becomes a hypothesis about a diagnosed limitation ("the
advance head needs capacity, keep the graph trunk, widen the context encoder"),
which is precisely what an LLM is better at than random mutation.

### C4 — The grammar cannot express the fixes the task needs

`GraphSpec` = {mlp, gcn, att, hybrid} × width / layers / heads / pool / ctx. What
this task actually needs, and what the grammar cannot express:

* **partial observability** — `remaining_visibility_s`, Doppler trend and elevation
  slope are only observable as a time series; there is no frame stacking, no GRU,
  no temporal convolution;
* **edge semantics** — same-plane, cross-plane and above-seam links have different
  physics; a GCN with one weight matrix cannot condition on that;
* **head asymmetry** — the two failures we observe are head-specific (target head
  collapsing to action 0, advance head saturating), yet trunk and heads share one
  width;
* **auxiliary objectives** — no auxiliary head for "predict time-to-loss", which
  would directly supply what the advance decision needs.

**Fix: extend the grammar with four primitives** (frame stack k ∈ {1,2,4}, GRU over
k steps, edge-type-conditioned GCN, asymmetric trunk/head widths, optional
auxiliary head). This both gives the LLM something meaningful to choose and makes
the space big enough that a good prior can beat random search.

### C5 — Zero-shot seeding is pseudo-replication, and freezes the population

The ten seed calls differ only by sampling seed: identical payload → near-identical
proposals (36 distinct sizes vs 81 for random). And because one search result is
frozen across all RL seeds, the framework never revisits the architecture when the
forensic loop finds a new limitation.

**Fixes:** seed with *explicitly differentiated* briefs (smallest viable / graph-heavy /
temporal / head-asymmetric), or 3 LLM seeds + 7 random; and connect the loops so a
forensic finding can trigger a targeted re-search (`almond` variant "closed-loop").

### C6 — Statistical protocol

Five seeds per arm, unpaired, and only the final best compared. Report instead:
anytime hypervolume at fixed *wall-clock*, quality at fixed evaluation count
(5/10/20/40), and paired tests over evaluation index with common random numbers.
With the variance fixed, 5 seeds may suffice; without it, no number of seeds helps.

---

## 2. What to do first (cheap, decisive, ~1–2 h of compute)

Before rebuilding the search, answer one question: **does any proxy we can afford
correlate with deployment quality?**

Experiment `probe_proxy_fidelity`:
1. sample ~20 architectures from the grammar (stratified by kind and size);
2. for each, evaluate under three proxies:
   P0 = current (from scratch, 24 episodes, per-candidate init seed),
   P1 = common random numbers + 3 eval seeds (variance fixed),
   P2 = P1 + behaviour-clone warm start, scored on validation satisfaction;
3. deploy each architecture with the full pipeline (9,600 episodes with the prior,
   the fixed forensic rules) and record Arctic HSR / satisfaction;
4. report Spearman ρ(proxy, deployment) for P0/P1/P2.

Decision rule:
* ρ(P0) ≈ 0 and ρ(P2) > 0.6 → the fix is worth building; the LLM prior can then be
  measured against random on a signal that exists;
* ρ(P1) ≈ ρ(P2) ≈ 0 → architecture genuinely does not matter for this task (the v3
  data hints at this: searched MLP 93.6 vs fixed GCN 92.7, i.e. second order next to
  the forensic loop's −28 pp), and the contribution should be repositioned rather
  than optimised.

---

## 3. Repositioning the contribution (independent of the above)

The v3 campaign says the architecture is second order for final quality:
searched MLP 93.6 %, fixed GCN 92.7 %, without forensics 65.5 %. So "a better
architecture" is a weak claim on this task. Two stronger, defensible framings:

1. **Sample efficiency**: LLM priors should reach a *given deployment quality* with
   fewer full-pipeline evaluations. That is measurable, useful operationally, and
   is where a prior can plausibly win — but only after C1/C2 make the metric usable.
2. **Closed loop with forensics**: the LLM designs the reward *and* the architecture
   from the same diagnosis. Today the forward translator, the forensic loop and the
   architecture search are three disconnected stages; the framework's actual novelty
   is that they share a knowledge graph. Wiring "forensic finding → targeted
   architecture hypothesis → evaluation → deployment check" back into the KG would
   make the system's claim about *self-improvement* testable, which it currently
   is not.

A harder scenario (×2 traffic, tighter feeder slots, or a longer horizon) is worth
adding regardless: with the top four arms saturated at 93–94 %, the Arctic metric
has no headroom left to discriminate anything.
