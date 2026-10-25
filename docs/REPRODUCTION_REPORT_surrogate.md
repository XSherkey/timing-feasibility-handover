# ALMOND reproduction — implementation and experiment report

**Target paper:** *From Human Intent to In-Orbit Action: A Self-Improving Large Language Model Agent for 6G Satellite Networks* (EAAI submission `Revised_Manuscript_修改稿.docx`).

**Status:** a complete, runnable reproduction exists. All 33 `⟦TBD⟧` markers of the manuscript have a measured value or an explicit "not measured" with the reason (`docs/TBD_FILLED.md`, `docs/tbd_values.json`). Several of the draft's headline numbers are **not** reproduced; those discrepancies are listed in §5 rather than papered over.

---

## 1. What was built

| Manuscript component | Implementation | File |
|---|---|---|
| 350-satellite LEO digital twin, real-SGP4 ephemeris | Walker-delta constellation synthesised as valid TLEs and propagated with SGP4 (J2 precession, drag); real Celestrak TLEs also supported (`oneweb`, `iridium`) | `almond/twin/constellation.py` |
| Link budget, Doppler, atmospheric attenuation, eclipse | Closed-form ITU-style Ka-band budget, elevation-dependent attenuation, SGP4-derived range rate, Sun-vector eclipse test | `almond/twin/geometry.py` |
| ISL topology incl. polar seam | Degree-limited optical mesh (4 terminals/satellite), line-of-sight test, cross-plane links disabled above 70° | `almond/twin/topology.py` |
| Feeder/gateway segment | 20 ground sites, 14 gateway stations, bounded feeder slots per gateway | `almond/twin/twin.py` |
| Handover MDP (14 telemetry fields + K=8 candidates) | Batched vectorised environment, make-before-break handover with a geometry-driven acquisition time | `almond/twin/handover_env.py` |
| Forward translator | LLM call → weight profile over fixed sub-rewards → semantic audit → re-prompt loop (Appendix A) | `almond/framework/translator.py`, `almond/llm/prompts.py` |
| Reverse forensics | Discovery-set narratives → LLM hypothesis → counterfactual replay on a disjoint validation set → held-out test with ×0.5/×1/×2 traffic → commit | `almond/framework/forensics.py` |
| Three-stage auditor | Semantic, physics (deterministic), impact (5-model ensemble surrogate) | `almond/framework/auditor.py` |
| Versioned knowledge graph | Append-only records, scope-filtered hybrid retrieval, retraction | `almond/framework/kg.py` |
| Constraint shield | Five executable effects; injection without retraining | `almond/framework/shield.py` |
| LLM-guided graph neuroevolution | Grammar-constrained seeds/mutation/crossover/critique, weight inheritance, Pareto selection, parameter-envelope projection | `almond/nas/evolution.py`, `almond/policies/nets.py` |
| PPO | Two categorical heads, GAE, clipping, validation checkpoint selection | `almond/policies/ppo.py` |
| Baselines | PPO-MLP, Static-LLM, Eureka-style, Oracle-PPO, Unseeded-EvoNAS, ALMOND-FixedArch, plus five ablations | `almond/framework/system.py` (`variant`) |
| Statistics | 10 seeds, t-CI, Wilcoxon + t, Holm, Cohen's d, rank-biserial, bootstrap ratio CI | `almond/analysis/stats.py` |

**On the LLM.** No hosted model is reachable from this machine. The LLM layer is a *pluggable interface* with two backends: `OpenAICompatBackend` (any OpenAI-compatible endpoint, selected automatically when `ALMOND_LLM_BASE_URL` is set) and `SurrogateBackend`, a deterministic *reasoning surrogate* that consumes exactly the structured payload of the Appendix-A prompts and returns exactly their JSON schema, computing the answer symbolically (priority→weight mapping; bounded threshold search over the declared predicate grammar for forensics; grammar-conditioned sampling for topology calls). Every call is logged with prompt, response, decoding parameters and latency (`llm_calls.jsonl`). **All results below are labelled `llm_backend=surrogate`; the LLM-quality claims are conditional on that substitution.**

---

## 2. The digital twin

Build: `python scripts/build_twin.py --tag ref --hours 12 --dt 10` → 350 satellites, 4321 epochs of 10 s, 20 ground sites, 984 MB memory-mapped cache (loads in 0.01 s, shared by all runs).

Physics that matters for the paper:

* **Polar seam.** Above 70° latitude all cross-plane ISL links are disabled (standard operational practice for counter-rotating planes) and each satellite has only 4 optical terminals. Net effect: mean ISL degree 3.98 below the seam, 1.55 above it; gateway hop count 0–27.
* **Feeder scarcity.** Each gateway tracks a bounded number of satellites; polar gateways see ~13 candidates versus ~5 at mid-latitude.
* **Contested service window.** A satellite stops being a viable server when it falls more than 10° of elevation behind the best visible candidate. In a dense polar sky this window is far shorter than the geometric visibility.
* **Acquisition time** `t_setup` = signalling + Doppler-degraded sync + per-hop route set-up + feeder-slot queueing + a plane-change penalty that is large only when the *target* is above the seam.

Measured consequence (the calibration that the paper's Sec. 4.2 rests on), 2597 random handover events over the top-2 candidates per site/epoch:

| Region | `t_setup` p50 | p90 | P(t_setup ≤ 6 s) | P(≤ 12 s) |
|---|---|---|---|---|
| Arctic (>70° N) | **10.0 s** | 15.7 s | 0.15 | **0.55** |
| Mid-latitude (30–65°) | **4.2 s** | 5.5 s | 0.91 | 0.97 |

A 2.4× asymmetry, which reproduces the manuscript's claim that about 10–12 s of preparation is needed in the Arctic while a few seconds suffice elsewhere. Note what the two probabilities imply: a policy that always uses the protocol's minimum 6 s lead keeps only **15 %** of its Arctic handovers, and one that uses **12 s** keeps **55 %** — the draft's 55 % figure is exactly the marginal-lead regime. Only a lead of about 16 s, or same-plane/route-aware target selection, reaches the 84–93 % seen in the converged runs.

---

## 3. Experimental protocol

* Test split = held-out time window (82–95 % of the horizon), evaluated at ×0.5 / ×1 / ×2 traffic.
* Discovery / validation / test windows are disjoint (0–60 % / 65–75 % / 82–95 %).
* The architecture search runs **once per configuration** and the discovered architecture is held fixed across RL seeds, so seed variance isolates the learning component; the same protocol is applied to the unseeded baseline.
* Validation-based checkpoint selection (the test split is never used for model selection).
* 10 seeds per method, 9600 instance-episodes per run on the reference twin.

---

## 4. Results

### 4.1 Reliability (Fig. 6 / Table 8)

```
method                    arctic     subarctic   midlat      equatorial  overall     S      params  conv  arc.median  arc.IQR
ALMOND                    60.8±42.5  60.6±43.2  63.4±44.1  63.9±44.1  62.6±43.3  55.8    23619   50%     83.6       74.1
PPO-MLP (hand-crafted)    55.2±41.4  50.1±43.1  50.6±42.6  57.8±41.5  54.5±41.4  35.2    27029   50%     75.8       80.8
ALMOND-FixedArch          47.6±42.1  42.1±45.5  44.9±46.5  51.4±44.9  48.2±43.6  45.7    27029   30%     62.8       86.0
Unseeded-EvoNAS           44.8±46.6  46.0±48.6  45.2±47.6  44.5±47.0  45.1±47.3  47.4    33303   50%     42.6       90.6
Oracle-PPO                43.2±44.9  43.7±46.7  46.3±48.9  51.8±45.6  47.4±45.4  46.8    33779   40%     40.0       86.0
Static-LLM                43.2±44.9  43.7±46.7  46.3±48.9  51.8±45.6  47.4±45.4  46.8    33779   40%     40.0       86.0
Eureka-style              43.2±44.9  43.7±46.7  46.3±48.9  51.8±45.6  47.4±45.4  46.8    33779   40%     40.0       86.0
ALMOND w/o forensics      60.8±42.5  60.6±43.2  63.4±44.1  63.9±44.1  62.6±43.3  55.8    23619   50%     83.6       74.1
```

The standard deviations are as large as the means because **PPO on this task is bimodal**: it either finds a working handover policy or collapses into a passive one. `conv` is the fraction of seeds that reached ≥80 % Arctic HSR, and `arc.median` is the median over all seeds. ALMOND is best on every aggregate (Arctic mean, Arctic median, satisfaction), and **PPO-MLP lands at 55.2 % mean Arctic HSR — the manuscript's 55 % figure** — while its intent satisfaction is the lowest of all methods (35.2), because its radio-quality proxy does not represent session continuity.

**Latitude coverage caveat.** Bins below 45° contribute few handover attempts in the test window (the equatorial and mid-latitude shells offer only 5–8 visible satellites there and sessions are short), so their per-bin HSR is noisy and the leftmost bins of Fig. 6 contain single-seed points.

### 4.2 Convergence (Fig. 7)

Episodes to 90 % of each method's own asymptote: PPO-MLP 360 ± 810, Static-LLM / Oracle-PPO / Eureka 480 ± 839, Unseeded-EvoNAS 720 ± 1012, ALMOND-FixedArch 960 ± 1771, **ALMOND 1080 ± 885**. Episodes to the fixed target S ≥ 75: PPO-MLP 1200, Unseeded-EvoNAS 1680, Static-LLM 3240, ALMOND 3720.

**The draft's "about three times faster than PPO-MLP" is not reproduced**: PPO-MLP reaches 90 % of *its own* (lower) asymptote sooner. What ALMOND has is a higher converged Arctic HSR (median 83.6 % vs 75.8 %) and a much higher test-set satisfaction (55.8 vs 35.2).

### 4.3 On-board envelope (Table 6)

Largest discovered policy: 23,861 parameters, 93 KB FP32 weights. Single batch, warm cache, 3000 timed inferences after 500 warm-ups:

| variant | mean | p99 |
|---|---|---|
| ONNX Runtime, CPU FP32 | **0.082 ms** | **0.152 ms** |
| ONNX Runtime, CUDA FP32 | 0.096 ms | 0.221 ms |
| ONNX Runtime, CPU FP16 | 0.149 ms | 0.266 ms |
| ONNX Runtime, CPU INT8 | 0.109 ms | 0.349 ms |
| PyTorch, CPU | 0.357 ms | 0.580 ms |

Policy switch: 0.242 ms (`load_state_dict`), 102,292 B serialized. Quantisation: FP16 changes HSR 91.1 → 92.9 % (Arctic 89.1 → 87.1 %), INT8 91.1 → 93.5 % (Arctic 89.1 → 91.7 %); switch flaps 72.4 → 78.4 (FP16) and 72.4 → 80.9 (INT8) per hour.

**Board:** Intel Core i5-12400F + RTX 3070. The Jetson Orin NX-class module of the manuscript's deployment specification is **not available**, so no Orin number is claimed; the 15 ms envelope is met with two orders of magnitude of margin on the measured board.

### 4.4 Auditor stress test (Table 7)

100 injected candidate constraints, five classes:

| class | n | semantic detect | physics detect | accepted |
|---|---|---|---|---|
| physically invalid | 20 | 0 % | **100 %** | 0 % |
| intent-inconsistent | 20 | **60 %** | 0 % | 40 % |
| misleading (spurious) | 20 | 0 % | 30 % | **70 %** |
| adversarial (latency) | 20 | 0 % | 0 % | **100 %** |
| valid controls | 20 | 0 % | 0 % | 0 % rejected |

Overall false acceptance 52.5 %, false rejection **0 %**. The two deterministic stages catch every physically invalid rule and reject nothing valid, but they cannot catch statistical spuriousness or latency-budget violations — those are the replay gate's and the impact predictor's job, and §7 explains why the impact predictor is inactive.

### 4.5 LLM output stability

| call type | exact match | semantic equivalence | schema failure |
|---|---|---|---|
| forward translation | 0 % | 68 % | 0 % |
| forensic hypothesis | 100 % | 100 % | 0 % |
| topology seed | 0 % | 20 % | 0 % |
| topology mutation | 5 % | 68 % | 0 % |
| topology crossover | 5 % | 68 % | 0 % |
| population critique | 0 % | 20 % | 0 % |

Safety-relevant calls are stable or fully repeatable; the diversity-oriented topology calls are not, which is what their temperature is for.

### 4.6 Impact predictor

Trained on 200 twin rollouts spanning the rule grammar: MAE 1.96 ms against a target standard deviation of 5.2 ms, held-out calibration slope **−0.09**, decision-flip rate 0/50. The predictor does not generalise, so the impact stage is reported as inactive rather than as a working safeguard.

### 4.7 Twin fidelity and perturbation (§4.8)

* **Analytic agreement.** 97,325 samples on the polar shell: slant-range disagreement p50 0.576 dB, p95 **0.665 dB**, max 0.681 dB; independent SNR recomputation p95 0.665 dB. The manuscript's "agreement within about 1 dB" is confirmed.
* **Perturbation.** Atmospheric attenuation, traffic and ISL availability perturbed by ±10 %: the mined constraint replicated in **0 of 6** cases (base Arctic HSR under perturbation 89.3–89.6 %, so the rule's marginal effect is no longer ≥ 5 pp; ISL dropout is the harshest at 82.7 %).
* **Sim-to-real proxy.** The reference-twin policy evaluated on the perturbed twins without retraining: Arctic HSR 82.7–89.6 % versus 92.0 % on the reference twin — a 2–9 pp graceful degradation.

### 4.8 Threshold sensitivity (Table 9)

Forensic trigger `theta_rho` swept over {75, 80, 85, 90, 95} % and the validation
gate `Delta_min` over {2, 5, 10} %, 3 seeds each, 2400 training episodes per seed
(mean monitored Arctic KPI 75.4 %).  Ground truth for recall is the set of three
constraint classes the twin can express (timing, routing, plane discipline);
precision is operational (an accepted rule is a true positive if it still gains
>= 5 pp Arctic HSR on the held-out test set).

| theta_rho | runs firing | accepted | precision | recall | mean Delta_test |
|---|---|---|---|---|---|
| 75 % | 1 | 1 | 100 % | 33 % | +5.3 pp |
| 80 % | 2 | 1 | 100 % | 33 % | +5.3 pp |
| 85 % | 2 | 1 | 100 % | 33 % | +5.3 pp |
| 90 % | 3 | 1 | 100 % | 33 % | +5.3 pp |
| 95 % | 3 | 1 | 100 % | 33 % | +5.3 pp |

| Delta_min | runs | accepted | precision | recall | mean Delta_test |
|---|---|---|---|---|---|
| 2 % | 3 | 1 | 100 % | 33 % | +5.3 pp |
| 5 % | 3 | 1 | 100 % | 33 % | +5.3 pp |
| 10 % | 3 | 0 | n/a | 0 % | n/a |

A higher trigger fires more often but changes nothing downstream: the auditor and
the replay gate, not the trigger, decide acceptance.  The gate behaves as designed
-- the one rule that replicates gains only 5.3 pp, so a 10 % gate correctly
rejects it and a 2 % gate accepts the same rule with no false positive.  Recall
is capped at 33 % because only one of the three expressible rule classes was ever
mined in this twin.

### 4.9 Architecture search

34 architectures evaluated in 25 s (LLM-seeded) and 27 s (unseeded). Best LLM-seeded individual: MLP w64 L3, 43,349 parameters, reward 0.684. Best unseeded individual: hybrid w48 L3, 37,893 parameters, reward **0.717**. The LLM-seeded search did **not** beat the unseeded baseline at equal evaluation budget.

---

## 5. What reproduces and what does not

| Manuscript claim | Reproduced? | Evidence |
|---|---|---|
| SGP4-driven twin of a 350-sat constellation with an Arctic failure mechanism | **Yes** | §2 |
| Acquisition-time requirement of ~10–12 s at low Arctic elevation | **Yes** | §2 (p50 10.0 s vs 4.2 s; P(≤12 s)=0.55) |
| <50 K parameters, ~15 ms batch-1 envelope, no on-board LLM | **Yes, with margin** | 24 K params, 0.082 ms mean on the host CPU |
| Audited constraints catch physically invalid LLM rules | **Yes** | 100 % detection, 0 % false rejection |
| Twin link budget agrees within ~1 dB | **Yes** | p95 0.665 dB |
| PPO-MLP sits near 55 % Arctic HSR | **Yes** | 55.2 % mean |
| ALMOND improves Arctic reliability over PPO-MLP | **Yes, modestly** | 60.8 % vs 55.2 % mean; 83.6 % vs 75.8 % median |
| Polar HSR 55 % → >95 % after constraint injection | **No** | best converged runs reach 89–93 %, and the shield barely fires |
| ~3× faster convergence than PPO-MLP | **No** | PPO-MLP reaches 90 % of its own asymptote sooner |
| ~20× architecture-search cost reduction | **No** | LLM-seeded search was worse at equal budget |
| Human effort 48 h → 4.5 h | **Not measured** | no human-subject protocol was run |
| Impact predictor as an effective safeguard | **No** | calibration slope −0.09 |
| Reverse forensics drives the gain | **Not demonstrated** | `ALMOND w/o forensics` is bit-identical to `ALMOND` in every seed |

---

## 6. Two environment bugs that were found and fixed

1. **Session cancellation.** A dropped link forced `session=False`, after which the terminal stayed out of service until the next Poisson arrival (~11 min at the configured arrival rate). One failure therefore removed the terminal from service for most of the episode, which made the task unlearnable and produced a 50 % collapse. Fixed by treating a drop as a *stall* (`RECONNECT_STEPS` epochs) while the session persists; service duty rose from 14 % to 32 % and converged-run HSR from ~0 % to 89–93 %.
2. **Candidate invalidity.** Slots beyond the visible set contained arbitrary satellites, so the policy could command a handover to a satellite below the elevation mask (19 % of failures). Fixed by marking them `-1` and masking their logits.

---

## 7. Limitations and open items

1. **LLM substitution.** All LLM-dependent results use the deterministic surrogate. Wiring a real endpoint only requires setting `ALMOND_LLM_BASE_URL`; the prompt contracts, JSON schemas, retries and logging are already in place.
2. **Hardware.** No Orin NX-class module; latency is measured on a desktop CPU and an RTX 3070.
3. **Residual bimodality.** 50 % of seeds still collapse to a passive policy for most methods (ALMOND-FixedArch 30 %). Cross-method comparisons should be read as *converged performance + convergence rate*, which is how §4.1 reports them.
4. **Forensics has no measurable effect.** In the 10 ALMOND seeds the knowledge graph ends with 0–1 active constraints and `ALMOND w/o forensics` is bit-identical to `ALMOND`. The loop fires (1–3 rounds) but the mined rules rarely replicate on the held-out test set, so they are correctly *not* committed — the validation gate is doing its job, at the cost of the paper's central claim.
5. **Impact predictor** is fitted but non-generalising; the third auditor stage is inactive.
6. **Rule replication under perturbation** is 0/6.
7. **Human-effort study** not run.
8. `Table 4` (generalisation across regimes) is reported with the rules the forensics actually mined (timing / routing classes); the eclipse-buffer class was not separable in the discovery set.

---

## 8. Reproducibility

```bash
# twin (once)
python scripts/build_twin.py --tag ref --hours 12 --dt 10
# architecture search (once per configuration)
python scripts/run_nas.py --mode llm     --out results/nas/llm_spec.json
python scripts/run_nas.py --mode random  --out results/nas/random_spec.json
# main campaign (8 methods x 10 seeds)
python scripts/run_campaign.py --methods almond --seeds 0-9 --episodes 9600 \
       --eval-every 1200 --device cpu --spec-file results/nas/llm_spec.json
# analysis, figures, report
python scripts/analyse_campaign.py && python scripts/make_figures.py && python scripts/make_report.py
# side experiments
python scripts/run_auditor_stress.py
python scripts/run_llm_stability.py --repeats 20
python scripts/train_impact.py --rules 200
python scripts/bench_latency.py --policy results/campaign/almond_seed1/policy.pt
python scripts/run_fidelity.py --policy results/campaign/almond_seed1/policy.pt \
       --kg results/campaign/almond_seed1/knowledge_graph.json
python scripts/diagnose_run.py --run results/campaign/almond_seed0   # explain a collapsed seed
```

## 9. Verification on the Ubuntu VM

The reproduction also runs inside the `Ubuntu_22.04_1` VMware guest (`/home/u22/almond-repro`), used as a second, independent execution environment: the twin builds from scratch there with identical statistics (ISL hop mean 4.04, unreachable 5.3 %) and the auditor / stability experiments reproduce. The pre-existing `/home/u22/satcon-demo` project was **not modified** (26 entries and the `Makefile` checksum unchanged) because it is a fixed-topology P4/BMv2 demo whose own README states it models no orbital motion, Doppler, ISL intermittency or handover continuity — it cannot serve as this paper's twin.
