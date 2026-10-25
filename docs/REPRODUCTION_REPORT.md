# ALMOND reproduction — implementation and experiment report (real-LLM run)

**Target paper:** *From Human Intent to In-Orbit Action: A Self-Improving Large Language Model Agent for 6G Satellite Networks* (EAAI submission `Revised_Manuscript_修改稿.docx`).

**LLM backend of this report:** **DeepSeek `deepseek-flash`** through the OpenAI-compatible chat-completions API (`https://api.deepseek.com`), temperature/top-p per Appendix A, JSON output mode, schema validation with repair re-prompts. The earlier surrogate-backed results are kept separately in `REPRODUCTION_REPORT_surrogate.md` and compared in §5.

**Status:** all 33 `⟦TBD⟧` markers of the manuscript have a measured value or an explicit "not measured" with the reason (`TBD_FILLED.md`, `tbd_values.json`). The real model changes one substantive conclusion: **the reverse-forensic loop now mines exactly the constraint the paper describes** (§4.5), although it commits rarely.

---

## 1. What was built

| Manuscript component | Implementation | File |
|---|---|---|
| 350-satellite LEO digital twin, real-SGP4 ephemeris | Walker-delta constellation synthesised as valid TLEs and propagated with SGP4 (J2 precession, drag); real Celestrak TLEs also supported | `almond/twin/constellation.py` |
| Link budget, Doppler, atmospheric attenuation, eclipse | Closed-form Ka-band budget, elevation-dependent attenuation, SGP4-derived range rate, Sun-vector eclipse test | `almond/twin/geometry.py` |
| ISL topology incl. polar seam | Degree-limited optical mesh (4 terminals/satellite), LOS test, cross-plane links disabled above 70° | `almond/twin/topology.py` |
| Feeder/gateway segment | 20 ground sites, 14 gateway stations, bounded feeder slots per gateway | `almond/twin/twin.py` |
| Handover MDP (14 telemetry fields + K=8 candidates) | Batched vectorised environment, make-before-break handover, geometry-driven acquisition time | `almond/twin/handover_env.py` |
| Forward translator | Real LLM call → weight profile → semantic audit → re-prompt on violation (Appendix A) | `almond/framework/translator.py`, `almond/llm/prompts.py` |
| Reverse forensics | Discovery narratives → LLM hypothesis → counterfactual replay on a disjoint validation set → held-out test (×0.5/×1/×2) → commit | `almond/framework/forensics.py` |
| Three-stage auditor | Semantic, physics (deterministic), impact (ensemble surrogate) | `almond/framework/auditor.py` |
| Versioned knowledge graph | Append-only records, scope-filtered retrieval, retraction | `almond/framework/kg.py` |
| Constraint shield | Five executable effects, injection without retraining | `almond/framework/shield.py` |
| LLM-guided graph neuroevolution | Grammar-constrained seeds/mutation/crossover/critique, weight inheritance, Pareto selection | `almond/nas/evolution.py`, `almond/policies/nets.py` |
| PPO | Two categorical heads, GAE, clipping, validation checkpoint selection | `almond/policies/ppo.py` |
| Baselines | PPO-MLP, Static-LLM, Eureka-style, Oracle-PPO, Unseeded-EvoNAS, ALMOND-FixedArch, five ablations | `almond/framework/system.py` |
| LLM access layer | OpenAI-compatible backend, JSON-mode, schema validator + repair, cross-process concurrency limiter, persistent response cache | `almond/llm/{backend,schema,semaphore,cache}.py` |
| Statistics | 10 seeds, t-CI, Wilcoxon + t, Holm, Cohen's d, rank-biserial, bootstrap ratio CI | `almond/analysis/stats.py` |

**What the real model changed in the harness.** Three defects surfaced only once a real endpoint was in the loop and were fixed: (i) the prompt templates emitted doubled JSON braces that a real model reads literally; (ii) the system hard-coded the surrogate backend and never consulted the environment; (iii) eight concurrent processes tripped provider throttling, so LLM calls now pass through a cross-process slot semaphore and a persistent response cache.

---

## 2. The digital twin

Build: `python scripts/build_twin.py --tag ref --hours 12 --dt 10` → 350 satellites, 4321 epochs of 10 s, 20 ground sites, 984 MB memory-mapped cache (loads in 0.01 s, shared by all runs).

* **Polar seam.** Above 70° all cross-plane ISL links are disabled (counter-rotating planes) and each satellite has 4 optical terminals: mean ISL degree 3.98 below the seam, 1.55 above it; gateway hop count 0–27.
* **Feeder scarcity.** Each gateway tracks a bounded number of satellites; polar gateways see ~13 candidates versus ~5 at mid-latitude.
* **Contested service window.** A satellite stops being a viable server when it falls 10° of elevation behind the best visible candidate.
* **Acquisition time** `t_setup` = signalling + Doppler-degraded sync + per-hop route set-up + feeder-slot queueing + a plane-change penalty that is large only when the *target* is above the seam.

Measured on 2597 random handover events (top-2 candidates per site/epoch):

| Region | `t_setup` p50 | p90 | P(t_setup ≤ 6 s) | P(≤ 12 s) |
|---|---|---|---|---|
| Arctic (>70° N) | **10.0 s** | 15.7 s | 0.15 | **0.55** |
| Mid-latitude (30–65°) | **4.2 s** | 5.5 s | 0.91 | 0.97 |

A 2.4× asymmetry, reproducing the manuscript's "about 10–12 s in the Arctic". A policy that always uses the protocol minimum of 6 s keeps only 15 % of its Arctic handovers; 12 s keeps 55 % — the draft's 55 % is the marginal-lead regime.

---

## 3. Protocol

* Test split = held-out time window (82–95 % of the horizon), evaluated at ×0.5 / ×1 / ×2 traffic; discovery (0–60 %), validation (65–75 %) and test are disjoint.
* The architecture search runs once per configuration (real LLM for the ALMOND-configured search, random sampling for the unseeded baseline, 34 evaluations each) and the discovered architecture is held fixed across RL seeds.
* Validation-based checkpoint selection; the test split is never used for model selection.
* Forward translation is cached per intent, so every seed of a method shares one audited weight profile; forensic hypotheses stay per-seed because their payload embeds that seed's trajectories.
* 9600 instance-episodes per run; 10 seeds per method where the wall clock allowed (achieved: ppomlp 10, no_forensics 10, static_llm 10, oracle 10, almond 6, eureka 4, almond_fixedarch 4, unseeded_evonas 3 — the shortfall is caused by provider latency in the forensic loop, and is reported rather than hidden).

---

## 4. Results (real LLM)

### 4.1 Reliability (Fig. 6 / Table 8)

```
method                    arctic     subarctic  midlat     equatorial overall    S      params n   conv  median  IQR
ALMOND                    59.9±46.4  62.6±48.5  61.4±47.7  60.5±46.9  61.0±47.3  56.5   39189  6    67%   88.9   68.3
Eureka-style              63.6±43.1  54.7±47.6  66.5±45.2  66.0±44.2  64.8±44.1  56.0   39189  4    50%   81.1   33.8
Unseeded-EvoNAS           60.0±50.8  64.2±55.6  63.0±54.6  65.9±45.2  63.4±51.1  58.1   29813  3    67%   88.3   44.5
ALMOND-FixedArch          52.3±38.4  59.2±41.2  62.1±42.8  58.9±44.2  59.2±41.6  50.4   27029  4    25%   58.9   32.1
PPO-MLP (hand-crafted)    50.6±42.4  43.4±41.6  51.7±44.7  54.5±46.2  51.8±43.7  36.0   27029  10   40%   69.7   85.9
Static-LLM                34.3±43.6  33.9±44.0  36.3±44.4  38.0±46.3  36.0±44.4  38.7   39189  10   30%    3.9   82.7
Oracle-PPO                31.5±40.9  29.5±42.1  36.4±43.4  39.6±44.0  35.7±42.1  35.0   39189  10   30%   11.6   70.3
ALMOND w/o forensics      29.5±41.8  25.5±41.6  27.4±40.5  32.1±43.0  29.2±41.8  35.1   39189  10   30%    1.8   68.8
```

* Convergence rate (`conv`, seeds reaching ≥80 % Arctic HSR): ALMOND 4/6 = **67 %**, the highest of the methods with n ≥ 6; PPO-MLP 4/10, Static-LLM and Oracle 3/10.
* Median Arctic HSR: ALMOND **88.9 %** against PPO-MLP 69.7 %, Static-LLM 3.9 %, Oracle 11.6 %.
* ALMOND has the best satisfaction among n ≥ 6 methods (56.5), PPO-MLP the worst (36.0).
* The two small-n methods (Eureka 63.6 %, Unseeded 60.0 %) have overlapping intervals with ALMOND and cannot be separated at n = 3–4.

### 4.2 Convergence (Fig. 7)

Episodes to 90 % of each method's own asymptote: PPO-MLP 240 ± 759, Static-LLM 240 ± 506, ALMOND-FixedArch 300 ± 600, Eureka 600 ± 693, ALMOND **1800 ± 2370**, Unseeded 0. Episodes to S ≥ 75: PPO-MLP 1080, Unseeded 3200, Static-LLM 3360, ALMOND 4000.

**The draft's "about three times faster than PPO-MLP" is not reproduced**: PPO-MLP reaches 90 % of *its own, much lower* asymptote sooner. It also has the highest validation-monitor peak (88.9 vs ALMOND 74.3) while scoring the lowest satisfaction on the held-out test set (36.0) — its radio-quality proxy does not survive the distribution shift.

### 4.3 On-board envelope (Table 6)

Largest discovered policy (real-LLM search): **MLP, width 64, 2 layers, 96-wide context encoder, 39,189 parameters, 153 KB FP32 weights.** Single batch, warm cache, 2000 timed inferences after 300 warm-ups on an Intel i5-12400F:

| variant | mean | p99 |
|---|---|---|
| ONNX Runtime, CPU FP32 | **0.045 ms** | **0.069 ms** |
| ONNX Runtime, CPU FP16 | 0.052 ms | 0.089 ms |
| ONNX Runtime, CPU INT8 | 0.055 ms | 0.127 ms |
| ONNX Runtime, CUDA FP32 | 0.046 ms | 0.103 ms |
| PyTorch, CPU | 0.165 ms | 0.277 ms |

Policy switch: 0.175 ms `load_state_dict`, 161,830 B serialized. Quantisation: FP16 → HSR 91.1 → 92.8 % (Arctic 89.1 → 87.1 %), INT8 → 93.5 % (Arctic 89.1 → 91.7 %); switch flaps 72.4 → 78.1 (FP16) / 80.9 (INT8) per hour. The Jetson Orin NX-class module is **not available**, so no Orin figure is claimed; the 15 ms envelope holds with two orders of magnitude of margin on the measured board.

### 4.4 Auditor stress test (Table 7)

100 injected candidate constraints, five classes (unchanged from the surrogate run — this experiment does not call the LLM): physically invalid 0 accepted (physics stage 100 % detection), intent-inconsistent 40 % accepted (semantic stage 60 % detection), misleading 70 % accepted, adversarial 100 % accepted, valid controls **0 % rejected**. Overall false acceptance 52.5 %, false rejection **0 %**. Statistical spuriousness and latency violations need the replay gate and the impact predictor, and §7 explains why the latter is inactive.

### 4.5 Reverse forensics with the real model — the substantive change

On a realistic discovery set the real model proposes the paper's rule and its neighbours verbatim:

```
IF elevation_deg <= 14 AND handover_advance_s <= 10  THEN min_advance(12)
IF elevation_deg <= 14 AND plane_change == 1         THEN prefer_same_plane
IF plane_change == 1  AND isl_hop_count >= 3         THEN forbid_unrouted_target
```

The surrogate could only reach this by grid search over a fixed threshold list; the model reaches it by reading the narratives, and the three hypotheses cover exactly the timing / plane / routing classes the manuscript describes for Table 4.

**But the loop still rarely commits.** Over the 6 ALMOND seeds the knowledge graph ends with 0.17 active constraints and 0.17 accepted commits on average (one seed committed one rule, `min_advance`), because the validation gate requires a ≥5 pp gain on a *disjoint* validation set and most proposed rules do not clear it. The gate is doing its job; the consequence is that forensics cannot yet be credited with the performance gap.

### 4.6 LLM output stability (Table 7)

24 calls per safety-relevant type, two intents, four independent repeat groups:

| call type | exact match | semantic equivalence | schema failures | calls needing repair |
|---|---|---|---|---|
| forward translation | 0 % | **88 %** | 0 % | 0 % |
| forensic hypothesis | 0 % | **67 %** | 0 % | 29.2 % |

No response is byte-identical — the model always writes a fresh `analysis` / `rationale` — but 88 % of translation groups agree on the weight ordering and the rounded profile, and 67 % of forensic groups agree on the predicate and effect. **29 % of forensic calls needed a repair re-prompt** (unknown field, >2 atoms, or a missing effect); the validator plus repair loop converted every one of them into a valid artifact, so the schema-failure rate is 0 %. Across the whole campaign: 55 calls, 11 schema retries, 0 exhausted.

### 4.7 Impact predictor, twin fidelity and search

* **Impact predictor** (unchanged, LLM-free): MAE 1.96 ms against a target sd of 5.2 ms, held-out calibration slope **−0.09**, decision flips 0/50 → the third auditor stage is reported as inactive.
* **Twin fidelity:** 97,325 polar-shell samples, slant-range disagreement p50 0.576 dB / p95 **0.665 dB** / max 0.681 dB; independent SNR recomputation p95 0.665 dB. The manuscript's "within about 1 dB" holds.
* **Perturbation:** with the real-LLM policy the reference Arctic HSR is 91.8 %; ±10 % atmospheric attenuation leaves it at 91.8 %, traffic ±10 % at 91.6–91.9 %, **ISL dropout −10 % at 84.6 %** (−7.2 pp), combined at 89.2 %. Rule replication is not applicable in that seed (no committed constraint).
* **Architecture search (real LLM):** 34 evaluations in 18 s, best reward **1.417** (MLP w64 L2, 39,189 parameters). Unseeded control at the same budget: best **1.400** (hybrid w32 L2, 29,813 parameters). The LLM seeding is now marginally *better* rather than worse, but the 20× cost claim still does not reproduce — both searches cost the same 34 evaluations.

### 4.8 LLM cost

Real-model campaign: **55 calls**, 47,073 prompt tokens and 54,185 completion tokens, 315 s of total API latency, 11 schema retries, median 6.7 s per call. At a representative US$ 0.28/M-token-class price this is ≈ US$ 0.03 for the entire campaign; the dominant cost is compute, not inference.

---

## 5. Real model vs surrogate

Same seeds, same twin, same harness; only the backend differs (`results/backend_comparison.md`).

| method | surrogate Arctic (mean/median/conv) | real-LLM Arctic (mean/median/conv) | Δ mean |
|---|---|---|---|
| ALMOND | 60.8 / 83.6 / 5-of-10 | 59.9 / 88.9 / 4-of-6 | −0.8 |
| ALMOND-FixedArch | 47.6 / 62.8 / 3-of-10 | 52.3 / 58.9 / 1-of-4 | +4.7 |
| Oracle-PPO | 43.2 / 40.0 / 4-of-10 | 31.5 / 11.6 / 3-of-10 | −11.7 |
| Static-LLM | 43.2 / 40.0 / 4-of-10 | 34.3 / 3.9 / 3-of-10 | −8.9 |
| ALMOND w/o forensics | 60.8 / 83.6 / 5-of-10 | 29.5 / 1.8 / 3-of-10 | −31.3 |
| Eureka-style | 43.2 / 40.0 / 4-of-10 | 63.6 / 81.1 / 2-of-4 | +20.5 |
| PPO-MLP | 55.2 / 75.8 / 5-of-10 | 50.6 / 69.7 / 4-of-10 | −4.6 |
| Unseeded-EvoNAS | 44.8 / 42.6 / 5-of-10 | 60.0 / 88.3 / 2-of-3 | +15.2 |

Weight profiles the two backends produce for the same reliability-first intent: surrogate 0.59/0.14/0.26, real model **0.68/0.11/0.21** — the real model weights reliability markedly more, which is what the intent asks for.

**How much of this is noise?** PPO-MLP is LLM-independent (fixed architecture, hand-coded weights 0.40/0.40/0.20) yet moved from 55.2 to 50.6 between the two campaigns at the same seeds. That puts the campaign-to-campaign noise floor at **≈5 pp**, and per-seed variance is far larger (±40 pp) because of the bimodality. The same-seed comparison of ALMOND against ALMOND-without-forensics makes the point sharply: with **zero committed knowledge** the two runs differ by +67, +91, +88, −92, 0 pp across seeds. RL training on this task is chaotic — a 1e-7 difference in a matmul reduction flips a discrete handover decision — so the harness is **not bit-reproducible across processes**, per-seed pairing is invalid, and every comparison in this report is unpaired over independent seeds. Differences below ~10 pp should not be interpreted.

---

## 6. What reproduces and what does not

| Manuscript claim | Reproduced? | Evidence |
|---|---|---|
| SGP4-driven twin of a 350-sat constellation with an Arctic failure mechanism | **Yes** | §2 |
| Acquisition-time requirement of ~10–12 s at low Arctic elevation | **Yes** | §2 (p50 10.0 vs 4.2 s; P(≤12 s)=0.55) |
| <50 K parameters, ~15 ms batch-1 envelope, no on-board LLM | **Yes, with margin** | 39 K params, 0.045 ms mean on the host CPU |
| LLM translates intent into a reliability-dominated reward profile | **Yes** | 0.68/0.11/0.21 from the real model |
| Reverse forensics recovers the polar timing constraint | **Yes** (real LLM only) | §4.5, including `min_advance(12)` at low elevation |
| Audited constraints reject physically invalid rules | **Yes** | 100 % detection, 0 % false rejection |
| Twin link budget agrees within ~1 dB | **Yes** | p95 0.665 dB |
| PPO-MLP sits near 55 % Arctic HSR | **Yes** | 50.6 % (55.2 % surrogate) |
| ALMOND improves Arctic reliability over PPO-MLP | **Yes, modestly** | 59.9 vs 50.6 mean; 88.9 vs 69.7 median; convergence 67 % vs 40 % |
| Mined knowledge drives the gain | **No** | 0.17 commits per run; the ablation is swamped by run-to-run variance |
| Polar HSR 55 % → >95 % after constraint injection | **No** | best converged runs reach 89–93 % |
| ~3× faster convergence than PPO-MLP | **No** | PPO-MLP reaches 90 % of its own asymptote sooner |
| ~20× architecture-search cost reduction | **No** | equal budget; LLM search marginally better, not cheaper |
| Human effort 48 h → 4.5 h | **Not measured** | no human-subject protocol |
| Impact predictor as an effective safeguard | **No** | calibration slope −0.09 |

---

## 7. Limitations

1. **Run-to-run determinism.** The harness is not bit-reproducible (§5). Until the trainer is made deterministic (single-threaded deterministic kernels, fixed seeds everywhere), only unpaired comparisons over ≥10 seeds and differences above ~10 pp are meaningful, and the ablation table cannot isolate component effects.
2. **Forensic throughput.** The forensic loop costs one LLM round-trip plus replays per trigger, which is what truncated ALMOND to 6 seeds in the time available.
3. **Commit rate.** The validation gate accepts roughly one rule per six seeds. Raising recall needs richer discovery sets (more non-timing failures) rather than a looser gate.
4. **Hardware.** No Orin NX-class module; latency measured on a desktop CPU and an RTX 3070.
5. **Model dependence.** Results are for `deepseek-flash` at the Appendix-A decoding settings. The interface accepts any OpenAI-compatible endpoint, so cross-model replication is a configuration change, not a code change.
6. **Impact predictor** non-generalising; **rule replication under perturbation** could not be evaluated in the reported seed (no committed rule).
7. **Human-effort study** not run; `Table 4` reports the two rule classes the forensics actually mined plus the timing rule.

---

## 8. Reproducibility

```bash
export ALMOND_LLM_BASE_URL=https://api.deepseek.com
export ALMOND_LLM_API_KEY=<key>
export ALMOND_LLM_MODEL=deepseek-flash
export ALMOND_LLM_CONCURRENCY=4          # cross-process slot semaphore
export ALMOND_LLM_CACHE_DIR=results/llm_cache

python scripts/build_twin.py --tag ref --hours 12 --dt 10
python scripts/run_nas.py --mode llm    --out results/nas/llm_spec.json
python scripts/run_nas.py --mode random --out results/nas/random_spec.json
python scripts/llm_live_smoke.py                     # 6-call contract check
python scripts/run_campaign.py --methods almond --seeds 0-9 --episodes 9600 \
       --eval-every 1200 --device cpu --spec-file results/nas/llm_spec.json
python scripts/analyse_campaign.py && python scripts/make_figures.py && python scripts/make_report.py
python scripts/compare_backends.py                   # surrogate vs real
python scripts/paired_forensics.py                   # ablation + noise evidence
python scripts/run_llm_stability.py --types forward_translate,forensic_hypothesis --repeats 12
python scripts/bench_latency.py --policy results/campaign/almond_seed1/policy.pt
python scripts/run_fidelity.py  --policy results/campaign/almond_seed1/policy.pt \
       --kg results/campaign/almond_seed1/knowledge_graph.json
```

## 9. Verification on the Ubuntu VM

The code also runs inside the `Ubuntu_22.04_1` VMware guest (`/home/u22/almond-repro`): the twin builds from scratch with identical statistics (ISL hop mean 4.04, unreachable 5.3 %) and the auditor/stability experiments reproduce. The pre-existing `/home/u22/satcon-demo` project was not modified (26 entries, `Makefile` checksum unchanged); it is a fixed-topology P4/BMv2 demo whose own README states it models no orbital motion, Doppler, ISL intermittency or handover continuity, so it cannot serve as this paper's twin.
