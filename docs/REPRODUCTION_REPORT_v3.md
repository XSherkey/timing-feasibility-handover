# ALMOND reproduction — test report v3 (training stabilised, 10 seeds, single model)

**Target paper:** *From Human Intent to In-Orbit Action: A Self-Improving Large Language Model Agent for 6G Satellite Networks* (EAAI `Revised_Manuscript_修改稿.docx`).

**What changed since v2**

1. **The PPO collapse is diagnosed and fixed.** Every previous campaign had 50–70 % of seeds frozen on the degenerate "never hand over" policy. Two interventions remove it and one makes runs reproducible.
2. **All 80 runs use `deepseek-flash`**; the v4-pro arm is dropped (it separated nothing in v2 and costs more).
3. **Full campaign re-run**: 8 methods × 10 seeds, then the architecture search and the forensic-recall experiments re-run against the new policies.
4. **The comparison is now resolvable**, and it decomposes the gain in a way the earlier reports could not.

---

## 1. Why the policies collapsed, and what fixed it

**Diagnosis** (`scripts/diagnose_collapse.py` on a 0 % seed): the target head put **100 % of its probability on action 0 = "no handover"**; `P(choose a target | allowed) = 0.00 %`; all 131 "attempts" were unplanned link losses, not commands. The reason "do nothing" is not merely a local optimum but a *good* one: the environment re-acquires a serving satellite by itself (`need = session & (serving < 0)`), so a passive terminal is still served ~79 % of steps, while a commanded handover pays a switch cost and — when the requested lead time is wrong — a drop penalty plus six offline steps. Exploration never reaches the first successful handover, so half the seeds settle there.

**Fix 1 — behaviour-cloning warm start.** `HandoverEnv.teacher_action()` is the twin's own analytic controller: among candidates that are visible, routed, and whose acquisition time fits inside the remaining visibility, take the highest elevation and request the smallest lead bucket that covers the acquisition time. The actor is cloned onto it for 6 episodes / 12 epochs before PPO starts (label-smoothed cross-entropy on both heads). **Applied identically to all eight methods**, so it is a shared initialisation, not a per-method advantage. Result: 4/4 probe seeds at 92–94 % (previously 3/10 converged); the full campaign then reached **10/10 or 9/10 converged in every forensics-enabled arm**.

**Fix 2 — deterministic seeding.** Three places leaked randomness: policy construction drew from an unseeded global RNG (so the *initial weights* differed between two identical runs), the trainer seeded only torch/numpy at construction time, and the architecture search built policies without seeding. All three now seed from the configuration: `random`, `numpy`, `torch`, `torch.use_deterministic_algorithms(True)`, single-threaded, and a per-(search seed, evaluation index) seed inside the evolver. **Verified: two separate processes running the same configuration now return bit-identical results** (`arctic 0.8610747051114024`, `S 52.54589946973588` in both).

What this buys: the manuscript's paired statistics become meaningful, and a 5 pp difference is no longer inside the scheduling noise.

---

## 2. Protocol

Test split = held-out window (82–95 %), ×0.5/×1/×2 traffic; discovery (0–60 %), validation (65–75 %) and test disjoint. One architecture search frozen across seeds. Validation checkpoint selection. 9,600 instance-episodes per run, 10 seeds per method, **all 80 runs complete**. One run had been aborting intermittently (`Boolean value of Tensor with more than one value is ambiguous`): `Individual` used the default dataclass equality, which compared the inherited parameter tensors whenever the Pareto front used `in` / `not in`. The class now uses identity semantics (`eq=False`) and the front bookkeeping compares identities, so the table below is the full 10 seeds. Backend `deepseek-flash`, JSON mode, 8,192-token budget (a reasoning-budget bug that returned empty content was fixed earlier), response cache keyed by model.

---

## 3. Reliability (Fig. 6 / Table 8)

```
method                  arctic    subarctic  midlat    equatorial overall   S     conv  median  IQR
ALMOND                  93.6±0.7  83.4±20.7  91.9±5.2  90.0±2.0   91.5±3.6  77.8  10/10  93.5   1.0
ALMOND-FixedArch        92.7±1.9  79.5±21.1  90.9±5.1  89.7±1.5   90.3±3.6  76.1  10/10  93.4   1.1
Eureka-style            92.7±2.0  79.5±21.0  91.2±4.9  90.6±2.0   90.5±3.6  76.4  10/10  93.4   1.3
Unseeded-EvoNAS         90.3±9.9  82.5±22.3  93.1±2.6  90.2±2.0   90.6±5.8  76.3   9/10  93.5   1.6
PPO-MLP                 72.6±16.1 56.3±25.5  88.9±4.3  89.6±2.1   81.5±7.4  46.9   4/10  69.9  20.4
Oracle-PPO              71.8±13.6 54.6±26.4  89.2±4.1  89.7±1.5   81.1±7.3  63.5   3/10  66.8  20.5
Static-LLM              71.8±13.6 54.6±26.4  89.2±4.1  89.7±1.5   81.1±7.3  63.5   3/10  66.8  20.5
ALMOND w/o forensics    65.5±14.1 37.4±26.9  87.8±4.2  89.6±2.0   77.9±6.8  59.0   2/10  63.0   9.1
```

95 % CI of Arctic HSR: ALMOND [93.2, 94.0], ALMOND-FixedArch [91.5, 93.9], Eureka [91.4, 93.9], Unseeded [84.2, 96.5], PPO-MLP [62.7, 82.6], Oracle/Static [63.4, 80.3], ALMOND w/o forensics [56.8, 74.3].

**Two groups, cleanly separated:**

* **with the forensic loop** — ALMOND 93.6, FixedArch 92.7, Eureka 92.7, Unseeded 90.3; converged 9–10 of 10;
* **without it** — PPO-MLP 72.6, Oracle 71.8, Static-LLM 71.8, ALMOND w/o forensics 65.5; converged 2–4 of 10.

ALMOND vs ALMOND-without-forensics is a **28.1 pp** gap with non-overlapping intervals; ALMOND vs PPO-MLP is **21.0 pp**, also non-overlapping. Both are the paper's central claims and both now hold at n = 10.

**What does *not* separate:** ALMOND (93.6) vs ALMOND-FixedArch (92.7) vs Eureka (92.7) vs Unseeded (90.3). The LLM-guided architecture search and the extra machinery buy nothing measurable over "translate + forensic loop"; the subarctic band is thin (some seeds have no subarctic attempts, hence the ±20 pp) and is not discriminative. The ceiling is 93–94 %, not the manuscript's ">95 %".

---

## 4. Where the performance comes from (the important decomposition)

Validation satisfaction immediately after cloning (episode 0) versus at the end of training:

| method | S after cloning | S at end | change |
|---|---|---|---|
| ALMOND | 80.9 | 86.9 | **+5.9** |
| ALMOND-FixedArch | 80.8 | 85.3 | +4.5 |
| Eureka-style | 80.8 | 85.0 | +4.2 |
| Unseeded-EvoNAS | 81.0 | 84.7 | +3.6 |
| **ALMOND w/o forensics** | 80.6 | 69.2 | **−11.4** |
| Oracle-PPO | 80.8 | 72.7 | −8.0 |
| Static-LLM | 80.8 | 72.7 | −8.0 |
| PPO-MLP | 86.4 | 82.1 | −4.3 |

Read this carefully, because it changes the interpretation of the whole table:

1. **The level is the prior.** The shared analytic controller already gives ≈81 % validation satisfaction. Every method starts there.
2. **PPO's own reward degrades it.** Without an injected constraint, ten thousand PPO episodes *lower* the metric by 4–11 pp — the reward proxy (radio quality for PPO-MLP, availability for the others) is systematically misaligned with session continuity, exactly the paper's premise.
3. **The mined constraint is what flips the sign.** The forensic arms end 4–6 pp *above* the prior; the non-forensic arms end 4–11 pp below it. The 28.1 pp ALMOND-vs-ablation gap is therefore "recover the degradation and add a little", not "learn the task from scratch".

This is a more defensible story than "the agent learns handover policy", and it is the one the data supports. It also means the paper should claim: *the LLM-mined constraint prevents RL from destroying a competent analytic prior*, not *the LLM discovers a policy from scratch*.

`Oracle-PPO` and `Static-LLM` are **bit-identical** (71.8, same intervals): in this build the hand-coded oracle rule is never applied, so the oracle arm is degenerate and should either be fixed or dropped from the manuscript.

---

## 5. Architecture search (Fig. 8)

Five seeds per arm, 42 evaluations each, identical budgets, now reproducible:

| arm | best proxy reward | median | winner architectures |
|---|---|---|---|
| ALMOND-seeded | **1.159 ± 0.132** | 1.13 | GCN-64, HYB-64, ATT-32 variants |
| Unseeded-EvoNAS | **1.175 ± 0.135** | 1.17 | GCN/ATT/hybrid variants |

No advantage, no cost reduction — the same conclusion as v2, now on a deterministic trainer. Fig. 8 panels: (a) anytime best-so-far (the two curves overlap), (b) per-seed best reward (medians 1.13 vs 1.17), (c) the deployment consequence — Arctic HSR with forensics (median 93 %), without (62 %), and PPO-MLP (70 %). The search objective simply does not predict the deployed metric, which is why the architecture freeze across seeds is a weak protocol.

---

## 6. Forensic recall, legacy vs enriched discovery (10 frozen policies)

| metric | legacy | enriched |
|---|---|---|
| discovery rows per run | 336.3 | **23.6** |
| failure causes | late 2784 / route 130 / window 449 | **80 / 76 / 80** (balanced) |
| rules committed | 7 / 10 | **8 / 10** |
| recall (classes covered / present) | 23 % | **27 %** |
| aligned proposals | 0.68 | 0.67 |
| effects proposed | route 9, advance 10, plane 7, visibility 2 | route 10, advance 10, **visibility 10** |

Enrichment did what it was designed to do: it rebalanced a discovery set that was 85 % one failure class into an even three-way split (336 → 24 rows), raised commits 70 → 80 %, raised recall 23 → 27 %, and made the model propose the visibility-aware remedy (`prefer_long_visibility`) in **all ten** policies instead of two. Two grammar effects had to be added for this to be possible (`cap_advance`, `prefer_long_visibility`); before that the auditor rejected them as "not executable", which is why the earlier recall ceiling was structural rather than a model limitation.

---

## 7. Claims, after the fix

| Manuscript claim | Verdict | Evidence |
|---|---|---|
| SGP4 twin, 350 satellites, Arctic failure mechanism | **holds** | polar acquisition p50 10.0 s vs 4.2 s mid-latitude |
| <50 K parameters, ~15 ms envelope, no on-board LLM | **holds** | 39,189 params; 0.045 ms mean / 0.069 ms p99; ×91–×332 headroom |
| Link budget within ~1 dB | **holds** | p95 0.665 dB |
| Auditor rejects physically invalid rules | **holds** | 100 % physics detection, 0 % false rejection |
| LLM translates intent into a reliability-dominated profile | **holds** | 0.68/0.11/0.21 |
| Forensic loop mines the polar timing rule | **holds** | `min_advance(12)` at elevation ≤14° and lead ≤10 s; +14 to +46 pp validated |
| ALMOND beats PPO-MLP on Arctic reliability | **holds** | 93.6 vs 72.6 (CIs disjoint), convergence 10/10 vs 4/10 |
| Ablation: removing forensics costs the gain | **holds** | 93.6 vs 65.5 (CIs disjoint) |
| The architecture search contributes | **not supported** | 93.6 vs 92.7 vs 92.7 for searched / fixed / Eureka; 1.159 vs 1.175 on the search objective |
| Polar HSR 55 % → >95 % | **not supported** | ceiling 93–94 % |
| ≈3× faster convergence | **not supported** | after warm start every arm starts ≈81 %; no separation |
| ≈20× search-cost reduction | **not supported** | equal budget, no quality advantage |
| Impact predictor as a safeguard | **not supported** | calibration slope −0.09 |
| Human effort 48 h → 4.5 h | **not measured** | no human-subject protocol |

---

## 8. Limitations

1. **Shared prior.** The behaviour-cloning warm start supplies the level; the reported differences measure what PPO and the mined constraints do *on top of it*. A manuscript using these numbers must say so — and should report a `no-warm-start` arm as the "from scratch" baseline (2–3 of 10 seeds converge there, at ~26–50 %).
2. **Ceiling.** 93–94 % in the Arctic means the scenario is no longer discriminative among the top four arms; a harder variant (higher traffic multiplier, tighter feeder slots) would be needed to separate them.
3. **Degenerate oracle arm.** Oracle-PPO equals Static-LLM exactly.
4. **Recall 27 %.** The validation gate, not the hypothesis, is now the binding constraint.
5. **Hardware.** No Jetson Orin NX-class module; latency measured on an i5-12400F and an RTX 3070.
6. **One model.** `deepseek-flash` only, by decision: v4-pro separated nothing and cost more.

---

## 9. Artefacts

`results/campaign` (80 runs), `results/campaign_v2_prewarm` (previous, pre-fix), `results/nas/sweep_llm.json`, `results/nas/sweep_random.json`, `results/forensics_recall.json`, `results/analysis/{tables.json,summary.md,bc_vs_final.json}`, `results/{latency_benchmark,auditor_stress,llm_stability,fidelity}.json`, `figures/fig6–fig10`, `docs/tbd_values.json`.

```bash
python scripts/run_campaign.py --methods almond --seeds 0-9 --episodes 9600 \
       --eval-every 1200 --device cpu --spec-file results/nas/llm_spec.json
python scripts/diagnose_collapse.py --run results/campaign/almond_seed0   # collapse diagnosis
python scripts/run_nas_sweep.py --mode llm    --seeds 0-4 --generations 4
python scripts/run_forensics_recall.py --runs "results/campaign/ppomlp_seed*" --limit 10
python scripts/finalize.py && python scripts/finalize2.py
```
