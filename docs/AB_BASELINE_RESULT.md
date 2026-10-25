# Experiments A and B — what the method is actually worth

Two baselines were missing from every earlier round. Both are now measured on the
final code, the fixed protocol and the same seeds (10 each, deterministic training,
held-out test window, ×0.5/×1/×2 traffic).

**A — how good is the prior alone?** The twin's analytic controller executed
directly (`teacher`), and the same controller deployed through the cloned network
with training, forensics and the shield all switched off (`bc_only`).

**B — does the LLM matter inside the forensic loop?** ALMOND with the
forward-translation call still served by `deepseek-flash`, but the
*forensic-hypothesis* call routed to the deterministic symbolic surrogate. The only
difference from the full system is who writes the hypotheses.

---

## 1. Result

| arm | Arctic HSR (95 % CI) | median | intent satisfaction | rule commits | what it is |
|---|---|---|---|---|---|
| analytic controller only | 85.9 [84.9, 86.8] | 85.6 | 73.4 | – | no network, no learning |
| behaviour-cloned prior only | 86.1 [84.9, 87.3] | 86.4 | 73.5 | – | deployed clone, no PPO |
| PPO on the prior, **surrogate** hypotheses | 70.6 [62.4, 78.8] | 73.0 | 60.7 | **0.0 / run** | forensic loop runs, nothing is accepted |
| PPO on the prior, **LLM** hypotheses (ALMOND) | **93.6 [93.2, 94.0]** | 93.5 | **77.8** | **1.0 / run** | full system |
| PPO-MLP, no forensic loop | 72.6 [62.7, 82.6] | 69.9 | 46.9 | – | radio-quality reward baseline |
| ALMOND without the forensic loop | 65.5 [56.8, 74.3] | 63.0 | 59.0 | – | ablation |

Paired over the same seeds:

* ALMOND − analytic controller = **+7.7 pp, 10/10 seeds**
* ALMOND − surrogate hypotheses = **+23.0 pp, 10/10 seeds**
* surrogate − analytic controller = **−15.3 pp** (PPO with no accepted constraint
  is *worse* than doing nothing)

---

## 2. Three findings, in order of importance

### F1 — PPO destroys a competent prior, and this is now measured

The analytic controller already achieves 85.9 %. Putting PPO on top of it *without*
an accepted constraint lands at 65.5–72.6 %, i.e. **PPO removes 13–20 pp**. The
manuscript's premise — that the reward proxy is misaligned with session continuity
— is therefore not an assumption but a measured effect of this twin.

This also reframes what the system is for: it is not "learning handover control
from scratch", it is **stopping RL from undoing a good controller**.

### F2 — The analytic controller is a strong baseline the paper has to face

85.9 % Arctic HSR with no learning at all. Any performance claim must be stated
relative to it, not relative to PPO-MLP (72.6 %) or to an ablated ALMOND (65.5 %).
Against this baseline the full apparatus is worth **+7.7 pp Arctic / +4.4
satisfaction points**, consistently (10/10) but not dramatically.

### F3 — The LLM's contribution is real, and it is specifically "hypotheses that replicate"

With the symbolic generator in place of the LLM, the loop still runs, still proposes
three candidates per run, and every candidate passes the semantic and physics
auditor — but **none of them ever clears the validation gate and replicates on the
held-out test**: 0.0 commits per run, and the arm falls to 70.6 %.

With the LLM, **every run commits exactly one rule** (all of them `min_advance`) and
the arm reaches 93.6 % with a standard deviation of 0.7 pp.

So the LLM is not contributing "plausible-looking rules" (the surrogate produces
those too, and they are worthless) — it is contributing **rules that survive
independent counterfactual validation**, which is precisely the mechanism the paper
claims. This is the strongest single piece of evidence in favour of the framework,
and it only became visible once both generators were run under one protocol.

---

## 3. Claim-by-claim status after A and B

| claim | status | evidence |
|---|---|---|
| The twin reproduces the polar timing constraint and the link budget | **holds** | 10.0 s vs 4.2 s acquisition; 0.665 dB p95 |
| On-board envelope, no on-board LLM | **holds** | 39,189 params, 0.045 ms mean |
| The auditor rejects physically invalid rules | **holds** | 100 % detection, 0 % false rejection |
| The LLM translates intent into a reliability-dominated reward | **holds** | 0.68/0.11/0.21 |
| The forensic loop mines a rule that replicates | **holds** | 1 rule/run, `min_advance(12)`, +14…+46 pp validated |
| **LLM hypotheses beat a non-LLM generator** | **holds, strongly** | +23.0 pp, 10/10, 0 vs 1 commit per run |
| **The method beats a hand-engineered controller** | **holds, modestly** | +7.7 pp Arctic, 10/10, CIs disjoint |
| ALMOND beats its own ablations as a *system* | **partially** | vs no-forensics +28.1 pp; vs FixedArch/Eureka/Unseeded it ties |
| The architecture search contributes | **not supported** | 83.0 vs 82.3, 8/10, p = 0.11; proxy ρ ceiling 0.5 |
| "≈3× faster convergence" | **not supported** | every arm starts at ≈81 % from the shared prior |
| "55 % → >95 %" | **not supported** | ceiling 93–94 % |
| Human effort 48 h → 4.5 h | **not measured** | no human-subject protocol |
| Impact predictor as a safeguard | **not supported** | calibration slope −0.09 |

---

## 4. Threats to validity (state these in the paper)

1. **The controller is ours.** The +7.7 pp margin is measured against a controller I
   wrote inside this twin. A weaker controller would inflate the margin, a stronger
   one would erase it. The honest statement is "ALMOND improves on *this* analytic
   controller by 7.7 pp", not "on human engineering in general".
2. **One rule class.** All ten committed rules are `min_advance`. The knowledge
   graph is therefore a single-rule store in practice, which weakens the
   "versioned multi-constraint memory" narrative.
3. **Ceiling.** 93.6 % is close to what the scenario allows; the remaining headroom
   is small and the top four arms (ALMOND, FixedArch, Eureka, Unseeded) are
   statistically tied.
4. **Surrogate is not a strawman, but it is weak.** It proposes three candidates per
   run and passes the auditor; it fails at *replication*, which is the property that
   matters. A stronger symbolic searcher might close part of the 23 pp gap.
5. **No human-effort measurement**, so the "4.5 h vs 48 h" claim has no evidence of
   any kind.

---

## 5. Recommended framing for the manuscript

> The reward proxy behind RL on this task is misaligned with session continuity:
> PPO applied to a competent analytic controller *loses* 13–20 pp. A language model
> that reverse-engineers failing trajectories into an executable constraint recovers
> that loss and adds a further 7.7 pp over the controller (10/10 seeds), while a
> symbolic hypothesis generator produces rules that pass every static audit and
> none that replicate — 0 versus 1 committed rule per run, 70.6 % versus 93.6 %
> Arctic HSR. The value of the LLM is therefore not fluent rule text but
> *validation-surviving* constraints.

Everything about the architecture search, convergence speed, the >95 % target and
the human-effort comparison should be dropped or explicitly marked as not supported.

---

## 6. Artefacts

`results/baseline_prior.json` (A: teacher and BC-only, 10 seeds),
`results/campaign_surrogate_forensics/` (B, 10 runs),
`results/ab_summary.json`, `results/campaign/` (comparison arms),
`scripts/baseline_prior.py`, `scripts/report_ab.py`,
`almond/llm/backend.py::RoutedBackend` (per-call-type backend routing),
`almond/framework/system.py::skip_ppo` (prior-only switch).

```bash
python scripts/baseline_prior.py --seeds 0-9
ALMOND_LLM_SURROGATE_CALLS=forensic_hypothesis \
python scripts/run_campaign.py --methods almond --seeds 0-9 --episodes 9600 \
       --eval-every 1200 --device cpu --spec-file results/nas/llm_spec.json \
       --out results/campaign_surrogate_forensics
python scripts/report_ab.py
```
