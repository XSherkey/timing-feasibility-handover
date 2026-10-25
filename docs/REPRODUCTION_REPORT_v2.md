# ALMOND reproduction — test report v2 (10 seeds, dual model, enriched forensics)

**Target paper:** *From Human Intent to In-Orbit Action: A Self-Improving Large Language Model Agent for 6G Satellite Networks* (EAAI submission `Revised_Manuscript_修改稿.docx`).

**What is new in this version**

1. **Ten seeds per method** for all eight configurations (80 runs), with **three of ALMOND's ten seeds served by `deepseek-v4-pro`** and seven by `deepseek-flash`, so the model dimension is measured rather than assumed.
2. **A controlled architecture A/B** (same variant, searched MLP swapped for the fixed GCN and vice versa, 5 seeds each), added because the raw table suggested an architecture effect.
3. **An enriched forensic discovery set** (stratified by the gateway error code the twin now records) plus **two new executable effects** the grammar was missing, evaluated on ten frozen policies in both modes.
4. **Redrawn Fig. 8, 9, 10** and refreshed Fig. 6, 7.
5. §6 lists, without hedging, which claims survive this round.

**Headline:** the pipeline is real and runs end to end, the on-board envelope and the auditor results hold, and the forensic loop now mines the timing rule — but **the method differences in the reliability table are not resolvable at ten seeds**, because every configuration is bimodal (converge or collapse) and the A/B shows the same pipeline scoring 56 % or 54 % depending only on which architecture label was attached. The paper's comparative claims cannot be supported by this harness as it stands.

---

## 1. Protocol

* Test split = held-out window (82–95 % of the horizon), evaluated at ×0.5/×1/×2 traffic; discovery (0–60 %), validation (65–75 %) and test are disjoint.
* One architecture search per configuration, frozen across RL seeds (the paper's protocol). The search is additionally repeated over five seeds per arm to measure search variance (§4).
* Validation-based checkpoint selection; the test split never selects a model.
* 9,600 instance-episodes per run; 10 seeds for all eight methods.
* Forward translation cached per intent *and per model*, so the three `deepseek-v4-pro` seeds cannot silently reuse the flash artifact.
* Backend: OpenAI-compatible chat completions. **A reasoning-token budget issue was found and fixed:** with `max_tokens=2048` the long forensic prompts were consumed entirely by reasoning tokens and the endpoint returned empty content with `finish_reason=length`; the budget is now 8,192 with an automatic doubling retry.

---

## 2. Reliability at ten seeds (Fig. 6 / Table 8)

```
method                    arctic     subarctic  midlat     equatorial overall    S      params conv  median  IQR
ALMOND-FixedArch          69.0±36.7  66.3±38.4  68.7±38.3  63.9±39.8  68.5±37.5  58.2   27029  70%   84.3   12.8
PPO-MLP (hand-crafted)    50.6±42.4  43.4±41.6  51.7±44.7  54.5±46.2  51.8±43.7  36.0   27029  40%   69.7   85.9
Static-LLM                34.3±43.6  33.9±44.0  36.3±44.4  38.0±46.3  36.0±44.4  38.7   39189  30%    3.9   82.7
Unseeded-EvoNAS           33.1±39.6  28.9±42.8  30.9±40.3  41.5±39.5  34.3±39.3  35.0   29813  30%   14.2   72.0
Oracle-PPO                31.5±40.9  29.5±42.1  36.4±43.4  39.6±44.0  35.7±42.1  35.0   39189  30%   11.6   70.3
ALMOND w/o forensics      29.5±41.8  25.5±41.6  27.4±40.5  32.1±43.0  29.2±41.8  35.1   39189  30%    1.8   68.8
Eureka-style              26.7±43.1  27.8±44.8  26.1±42.3  27.4±44.1  26.9±43.4  35.1   39189  30%    0.0   65.0
ALMOND                    26.2±42.3  27.8±44.8  28.3±45.6  27.7±44.6  27.5±44.3  36.0   39189  30%    0.0   60.4
```

Every configuration is bimodal: **no method converged in more than 7 of 10 seeds**, and five of them converged in 3 or fewer. The standard deviation is larger than the mean difference between any pair. Consequently:

* the ordering above is **not** a ranking of methods; it is one draw from a bimodal process (Fig. 6 right panel shows the 95 % intervals overlap for six of the eight methods);
* the only configuration that separated itself, **ALMOND-FixedArch (69.0 %, 7/10 converged)**, did so on the *fixed* architecture with the LLM weights and the forensic loop — i.e. without the paper's architecture search.

### Cross-model arm

| arm | n | Arctic HSR (mean) | per-seed |
|---|---|---|---|
| `deepseek-flash` | 7 | 26.0 % | 0, 0, 0, 0, 92.1, 89.7, 0 |
| `deepseek-v4-pro` | 3 | 26.9 % | 0, 80.6, 0 |

The two models are indistinguishable at this sample size; both show the same collapse pattern, so **the collapse is a property of the RL training, not of the model**. Translation weights differ only mildly (flash 0.68/0.11/0.21, v4-pro 0.69/0.11/0.20 for the reliability-first intent).

---

## 3. Architecture control: the apparent architecture effect is noise

The table above invites the reading "the searched MLP is bad, the fixed GCN is good": every method on the searched MLP sits at 26–36 %, and the two on the fixed GCN at 51–69 %. That reading is wrong, and the control proves it.

| arm | variant | architecture | n | Arctic mean | per-seed |
|---|---|---|---|---|---|
| fixed-arch variant, **searched MLP** | `fixed_arch` | MLP w64 L2 | 5 | **55.9 %** | 91.9, 89.5, 5.9, 0.0, 92.1 |
| full variant, **fixed GCN** | `full` | GCN w64 L2 | 5 | **54.5 %** | 0.0, 90.4, 89.4, 89.4, 3.5 |

Swapping the architecture in either direction leaves the mean at ≈ 55 %. The 26 % vs 69 % gap in §2 is therefore **convergence luck**, not architecture: with five seeds, each arm has two or three collapses, and which arm looks better is decided by how many of its seeds happened to escape the collapse.

This is the single most important result of this round. It means:

* the reliability table cannot support **any** component claim (ALMOND vs ablation, vs baselines, vs Oracle) at n = 10;
* the paper's Table 8 ablation needs the training instability fixed before it can be reported at all;
* reporting a mean ± sd over a bimodal outcome is itself misleading, which is why convergence rates are printed alongside.

---

## 4. Architecture search (Fig. 8)

Five seeds per arm, 42 evaluations each, identical budgets:

| arm | best proxy reward (mean ± sd) | median | architectures found |
|---|---|---|---|
| ALMOND-seeded | **1.146 ± 0.206** | 1.07 | HYB-64, ATT-32×3, GCN-64×3, ATT-32×2, GCN/hybrid |
| Unseeded-EvoNAS | **1.170 ± 0.189** | 1.04 | hybrid, GCN, ATT variants |

The distributions overlap almost completely (Fig. 8, panels a and b). **The ≈20× cost claim does not reproduce, and neither does a quality advantage**; if anything the unseeded arm has the higher mean.

Fig. 8 panel (c) is the part a reviewer needs: the search optimises a *short-budget PPO return*, and that proxy is only loosely coupled to the deployed metric. The campaign froze the architecture of a single 3-generation search, which happened to land on an MLP; the five 4-generation sweeps land mostly on GCN/hybrid. **A single search run is not a reliable protocol**, which is itself a finding about the paper's design.

---

## 5. Forensic recall with an enriched discovery set

### 5.1 What was changed

1. **Error codes.** The twin now records *why* each handover attempt failed (`late_handover`, `no_route`, `window_exceeded`, `below_elevation`), as a real gateway would log an error code, and the narratives carry it.
2. **Stratified sampling.** The old discovery selection sorted by route availability then acquisition time, which produced 122 rows per run dominated by `no_route`/`window_exceeded` and *no* `late_handover` at all. The new one samples up to eight rows per error code, so every class present is represented (≈13 rows per run).
3. **Two missing effects.** The effect grammar had no remedy for `window_exceeded` (requested lead longer than the target stays visible), so those failures could never be turned into an accepted rule. `cap_advance` and `prefer_long_visibility` were added; the auditor's executable-effect whitelist was extended to match (before that, both were rejected as "not executable").
4. **Remedy mapping in the prompt.** Each effect now carries a one-line statement of the failure mode it removes, and the prompt tells the model to use the error code to pick the effect. Without it the model proposed only `min_advance` / `prefer_same_plane` regardless of the discovery set.

### 5.2 Controlled evaluation on frozen policies

Ten trained PPO-MLP policies, never retrained, both modes on identical splits and identical LLM seeds:

| metric | legacy | enriched |
|---|---|---|
| discovery rows per run | 121.8 | **13.3** |
| failure classes present | 3 (491 / 169 / 557) | 3 (24 / 52 / 56) |
| candidates proposed | 1.8 | 1.7 |
| rules committed | 1 / 10 | **2 / 10** |
| recall (classes covered / present) | 5.9 % | **11.8 %** |
| timing class covered | 1 / 10 runs | **2 / 10 runs** |
| mean Δ_test of committed rules | +24.8 pp | +19.7 pp |

**The concrete win.** On `ppomlp_seed4` the legacy discovery set produced a routing rule that passed validation but *lost* 12.8 pp on the held-out test and was correctly rejected; the enriched set produced a timing rule (`min_advance`) that replicated at **+14.8 pp**. Enrichment doubled both the commit rate and recall.

**The ceiling.** Recall is still 12 %. The binding constraint is now the validation gate, not the hypothesis: on a policy already at 83–91 % Arctic HSR the remaining failure classes account for 2–15 % of attempts, so a 5 pp gate on three validation episodes rejects most genuinely helpful rules. Lowering Δ_min to 2 % would admit more, at the cost of precision (§6).

---

## 6. What survives this round

| Manuscript claim | Verdict | Evidence |
|---|---|---|
| SGP4 twin of a 350-satellite constellation with an Arctic failure mechanism | **holds** | §2, p50 acquisition 10.0 s polar vs 4.2 s mid-latitude |
| Acquisition time ≈ 10–12 s at low Arctic elevation | **holds** | P(≤12 s) = 0.55 |
| <50 K parameters, ~15 ms single-batch envelope, no on-board LLM | **holds, with margin** | 39,189 params; ONNX CPU 0.045 ms mean / 0.069 ms p99; ×91–×332 headroom (Fig. 10) |
| Link budget within ~1 dB of the analytic value | **holds** | p95 0.665 dB, max 0.681 dB |
| Auditor rejects physically invalid rules | **holds** | 100 % physics detection, 0 % false rejection (Fig. 9) |
| LLM translates intent into a reliability-dominated profile | **holds** | 0.68/0.11/0.21 (flash), 0.69/0.11/0.20 (v4-pro) |
| Forensic loop recovers the polar timing rule | **holds** | `min_advance(12)` at elevation ≤ 14° and lead ≤ 10 s; +19 pp validated |
| Enriching the discovery set raises forensic recall | **holds, modestly** | 5.9 % → 11.8 %, commits 1/10 → 2/10, one harmful rule replaced by a helpful one |
| PPO-MLP sits near 55 % Arctic HSR | **holds** | 50.6 % |
| ALMOND beats PPO-MLP / Oracle / ablations on Arctic reliability | **not supported** | 26.2 % vs 50.6 %; intervals overlap for six of eight methods; A/B shows ±35 pp is convergence luck |
| Mined knowledge drives the gain | **not supported** | the only separated configuration is the fixed-arch arm, and the ablation cannot be resolved |
| Polar HSR 55 % → >95 % after constraint injection | **not supported** | best converged runs 89–93 % |
| ≈3× faster convergence | **not supported** | PPO-MLP reaches 90 % of its own asymptote in 240 episodes vs ALMOND 960 |
| ≈20× architecture-search cost reduction | **not supported** | 1.146 vs 1.170 best reward at equal budget, n = 5 |
| Impact predictor as an effective safeguard | **not supported** | calibration slope −0.09, flips 0/50 |
| Human effort 48 h → 4.5 h | **not measured** | no human-subject protocol |

---

## 7. Limitations

1. **Training instability dominates.** Until the PPO collapse is fixed (deterministic kernels, lower LR / longer warm-up, or a scripted warm start), no comparative claim in this harness is resolvable, and the ablation table is not reportable. This is the top priority for the next round.
2. **Recall ceiling.** 12 % with a 5 pp gate at an 85 % baseline. A stronger design would gate on *per-class* improvement rather than aggregate HSR.
3. **Single search run.** The campaign's architecture came from one 3-generation search; five sweeps disagree, so the paper's protocol should search multiple seeds and select on held-out deployment performance, not on the proxy reward.
4. **Hardware.** No Jetson Orin NX-class module was available; latency is measured on an i5-12400F and an RTX 3070, and no Orin number is claimed.
5. **Model dependence.** Results are for `deepseek-flash` and `deepseek-v4-pro` at the Appendix-A decoding settings; the three-seed v4-pro arm is too small to resolve anything.

---

## 8. Artefacts

`results/campaign` (80 runs), `results/campaign_v1_legacy` (previous 76-run campaign), `results/ab_fixedarch_mlp`, `results/ab_almond_gcn` (architecture control), `results/nas/sweep_llm.json`, `results/nas/sweep_random.json` (five-seed searches), `results/forensics_recall.json` (enriched vs legacy forensics), `results/llm_stability.json`, `results/auditor_stress.json`, `results/latency_benchmark.json`, `results/fidelity.json`, `figures/fig6–fig10`.

Commands:

```bash
export ALMOND_LLM_BASE_URL=https://api.deepseek.com ALMOND_LLM_MODEL=deepseek-flash
export ALMOND_LLM_MAX_TOKENS=8192 ALMOND_LLM_CONCURRENCY=4

python scripts/run_campaign.py --methods almond --seeds 0-9 --episodes 9600 \
       --eval-every 1200 --device cpu --spec-file results/nas/llm_spec.json
python scripts/run_campaign.py --methods almond_fixedarch --seeds 0-4 \
       --spec-file results/nas/llm_spec.json --out results/ab_fixedarch_mlp   # architecture A/B
python scripts/run_nas_sweep.py --mode llm    --seeds 0-4 --generations 4
python scripts/run_nas_sweep.py --mode random --seeds 0-4 --generations 4
python scripts/run_forensics_recall.py --runs "results/campaign/ppomlp_seed*" --limit 10
python scripts/analyse_campaign.py && python scripts/make_figures.py && python scripts/make_figures_three.py
```
