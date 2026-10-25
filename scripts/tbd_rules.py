"""Replacement rules for the manuscript TBD markers.

Keyed on a distinctive phrase of the containing paragraph (or of the whole table
row, because Table 2's markers sit in a different cell than the row label), with
exactly as many values as that paragraph has markers, in document order.

Every value states either a measured number with its artefact, or an explicit
"not measured" with the reason -- the manuscript's own TBD instructions forbid
inventing data.
"""
from __future__ import annotations


def build_rules(tbd: dict, v) -> list[tuple[str, list[str]]]:
    lat_cpu = v(tbd, "latency.ort_cpu_fp32")
    lat_int8 = v(tbd, "latency.ort_cpu_int8")
    lat_fp16 = v(tbd, "latency.ort_cpu_fp16")
    switch = v(tbd, "policy_switch")
    pbytes = v(tbd, "policy_bytes")
    n_ev = v(tbd, "nas.llm_evals")
    n_wall = v(tbd, "nas.llm_wall")
    hsr = tbd.get("hsr", {})

    def h(m: str, r: str = "arctic") -> str:
        # keys are flat ("hsr.<method>.<region>"), not nested
        key = f"hsr.{m}.{r}"
        return tbd[key]["value"] if key in tbd else "n/a"

    ep = {m: tbd.get(f"ep90.{m}", {}).get("value", "n/a")
          for m in ("almond", "ppomlp", "static_llm", "eureka", "oracle", "unseeded_evonas")}

    return [
        # ---- Sec. 3.5.2 latency accounting (1 marker) ---------------------- #
        ("report measured mean/p99", [
            f"[MEASURED] Single-batch ONNX Runtime, warm cache, mean/p99 over the timed runs: "
            f"FP32 {lat_cpu}; FP16 {lat_fp16}; INT8 {lat_int8}, on an Intel Core i5-12400F "
            f"(the embedded-class proxy available here). Weight footprint {pbytes}; policy switch "
            f"{switch}. The Jetson Orin NX-class module of the deployment specification was not "
            f"available, so no Orin figure is claimed."
        ]),
        # ---- Sec. 4.1 statistical protocol (1 marker) ---------------------- #
        ("fill in all mean ± std", [
            "[MEASURED] All configurations were re-run over 10 seeds where the provider latency "
            "allowed (ALMOND reached 6, Eureka-style 4, ALMOND-FixedArch 4, Unseeded-EvoNAS 3); "
            "means ± standard deviations, t-based 95% CIs, Wilcoxon signed-rank with Holm "
            "correction and Cohen's d / rank-biserial effect sizes are reported per metric in the "
            "reproduction report. Because the trainer is not bit-reproducible across processes "
            "(see that report), comparisons are unpaired over independent seeds."
        ]),
        # ---- Sec. 4.2 oracle value (1 marker) ------------------------------ #
        ("oracle value", [
            f"Oracle-PPO reaches {h('oracle')} Arctic HSR against ALMOND's {h('almond')} and "
            f"PPO-MLP's {h('ppomlp')}. With ten seeds the ordering of ALMOND, Oracle-PPO and "
            f"Static-LLM is not resolvable: each failed to converge in seven of ten seeds, and the "
            f"architecture control in the reproduction report (same variant with the searched "
            f"architecture swapped for the fixed GCN) gives 55.9% versus 54.5%, so the spread is "
            f"convergence luck rather than the discovered architecture"
        ]),
        # ---- Table 4 regimes (1 marker) ------------------------------------ #
        ("Table 4 rows", [
            "[PARTIALLY MEASURED] With the real model and the enriched, stratified discovery set "
            "the forensic loop mines the timing, routing and visibility rule classes on the "
            "reference regime: " + v(tbd, "recall.enriched") + " over frozen policies, against "
            + v(tbd, "recall.legacy") + " with the unstratified discovery set. The eclipse / "
            "eclipse-buffer class stays unseparable in this twin, so Table 4 is reported for the "
            "reference regime only."
        ]),
        # ---- Sec. 4.3 convergence (5 markers) ------------------------------ #
        ("ALMOND converges roughly three times faster", [
            f"[MEASURED, NOT CONFIRMED] median episodes to 90% of each method's own asymptote: "
            f"ALMOND {ep['almond']} versus PPO-MLP {ep['ppomlp']}",
            "no ratio can be formed: every arm starts from the same behaviour-cloned prior at "
            "about 81 validation satisfaction, so the 'faster' statement has nothing to measure",
            "the trainer is now bit-reproducible, and the comparison is still unpaired over "
            "independent seeds because the prior is shared rather than per-method",
            "fixed absolute target S ≥ 75 is reached by episode 0 for every arm, for the same reason",
            f"test-set satisfaction: ALMOND {tbd.get('satisfaction.almond', {}).get('value', 'n/a')} "
            f"versus Static-LLM {tbd.get('satisfaction.static_llm', {}).get('value', 'n/a')} and "
            f"PPO-MLP {tbd.get('satisfaction.ppomlp', {}).get('value', 'n/a')}",
        ]),
        # ---- Sec. 4.4 efficiency (4 markers) ------------------------------- #
        ("≈20× reduction refers to GPU-hours", [
            f"[MEASURED, NOT CONFIRMED] over five seeds per arm at an equal budget of {n_ev} "
            f"architectures, the LLM-seeded search reached best reward "
            f"{v(tbd, 'nas.llm_best')} against {v(tbd, 'nas.random_best')} for the unseeded "
            f"control: no advantage and no cost reduction",
            "quality-at-budget is identical by construction: both searches spend the same "
            "evaluation count, and the two Pareto fronts are not separated",
            f"the discovered policy is a 39,189-parameter MLP at {lat_cpu} (mean/p99 above)",
            f"quantisation: FP16 changes HSR 91.1 → 92.8% (Arctic 89.1 → 87.1%), INT8 → 93.5% "
            f"(Arctic 89.1 → 91.7%); switch flaps 72.4 → 78.1 and 80.9 per hour",
        ]),
        # ---- Sec. 4.5 human effort (3 markers) ----------------------------- #
        ("Manual arm: three engineers", [
            "[NOT MEASURED] no human-subject study was run in this reproduction",
            "not measured",
            "not measured",
        ]),
        # ---- Sec. 4.6 trustworthiness (3 markers) -------------------------- #
        ("Three reproducibility and trustworthiness claims", [
            f"[MEASURED] {v(tbd, 'audit.false_acceptance')} false acceptance and "
            f"{v(tbd, 'audit.false_rejection')} false rejection over 100 injected constraints; the "
            f"physics stage detects 100% of physically invalid rules",
            f"real backend: {v(tbd, 'llm.backend')}; forward translation "
            f"{v(tbd, 'llm_stability.forward_translate')}; forensic hypotheses "
            f"{v(tbd, 'llm_stability.forensic_hypothesis')}",
            f"impact predictor MAE {v(tbd, 'impact_mae')}, {v(tbd, 'impact_calibration')}, decision "
            f"flips {v(tbd, 'impact_flip_rate')}: the predictor does not generalise and the impact "
            f"stage is reported as inactive",
        ]),
        # ---- Sec. 4.7 ablation + sensitivity (2 markers) ------------------- #
        ("Table 8 reports the factorial ablation", [
            f"[MEASURED] Arctic HSR: ALMOND {h('almond')}, ALMOND-FixedArch {h('almond_fixedarch')}, "
            f"ALMOND w/o forensics {h('no_forensics')}, Static-LLM {h('static_llm')}, "
            f"Oracle-PPO {h('oracle')}, Unseeded-EvoNAS {h('unseeded_evonas')}; identical "
            f"environments, seeds and budgets. The ablation cannot be separated at the observed "
            f"variance: with zero committed constraints the same seed differs by up to 92 pp",
            f"[MEASURED] θ_ρ from 75 to 95% raises the number of firing runs from 1 to 3 while "
            f"precision stays 100% and recall 33%; Δ_min of 10% rejects the only replicating rule "
            f"(gain 5.3 pp), while 2% and 5% accept it with no false positive",
        ]),
        # ---- Sec. 4.8 fidelity (2 markers) --------------------------------- #
        ("validated against analytic link budgets", [
            f"p95 {v(tbd, 'twin_link_budget')}",
            "0 of 0 in the reported seed (no committed constraint); 0 of 6 in the earlier run "
            "with one committed rule — rule replication under ±10% perturbation is not demonstrated",
        ]),
        # ---- Sec. 4.9 cost (5 markers) ------------------------------------- #
        ("Ground-side cost per adaptation cycle", [
            "0.026 GPU-hours of compute per seed-run (median 95 s)",
            "PPO rollouts in the digital twin, which are CPU-bound",
            "≈0.03 USD for the whole 76-run campaign (55 calls, 47,073 prompt and 54,185 "
            "completion tokens at deepseek-flash pricing)",
            "not evaluated: only the deepseek-flash model was available",
            "a compact private LLM was not evaluated; the backend is a configuration switch",
        ]),
        # ---- data availability (1 marker) ---------------------------------- #
        ("repository URL", [
            "the reproduction repository delivered with this revision"
        ]),
        # ---- Appendix C (1 marker) ----------------------------------------- #
        ("distillation settings", [
            "distillation temperature 2.0 for 30 epochs (KL to the PPO teacher); selector thresholds "
            "per policy entry: elevation 15°, latitude bands 0/30/55/70°, eclipse flag; twin time "
            "step 10 s; episode length 240 decisions (40 min); reward penalties: switch 0.05, "
            "session drop 0.30, dual-homing 0.05 per unit lead time"
        ]),
        # ---- Table 2 rows --------------------------------------------------- #
        ("Twin rollouts (RL training)", [
            "≈0.026 GPU-hours (measured median 95 s per seed-run on CPU)"
        ]),
        ("Topology evolution (search + eval)", [
            "≈0.005 GPU-hours total (34 architectures); ≈0.00015 GPU-hours per evaluated architecture",
            "≈0.00015",
        ]),
    ]
