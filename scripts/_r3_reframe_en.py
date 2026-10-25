"""R3 (v10) — reframe the paper on the isolation evidence (title, abstract, contributions, VI-H)."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / "almond-repro"
P = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本" / "paper_en.md"
t = P.read_text(encoding="utf-8")
iso = json.loads((ROOT / "results" / "routeA_r3" / "isolation" / "summary.json").read_text(encoding="utf-8"))
done = []


def rep(old: str, new: str, label: str) -> None:
    global t
    n = t.count(old)
    if n != 1:
        raise SystemExit(f"[{label}] expected 1, found {n}")
    t = t.replace(old, new, 1)
    done.append(label)


# ---------------------------------------------------------------- title
rep("# Feasibility, Not Learning: Censoring-Aware Mining and Conservative Injection of Handover Constraints for Autonomous LEO Satellite Networks",
    "# Probe-Calibrated Conservative Injection of Handover Constraints for Autonomous LEO Satellite Networks",
    "title")

# ---------------------------------------------------------------- abstract
a = t.find("## Abstract")
b = t.find("## Nomenclature")
ABSTRACT = """## Abstract

Handover reliability in low Earth orbit constellations is usually treated as a reinforcement-learning problem, and recent systems report large gains from coupling RL with large language models. We reproduce one such system and audit what its gains consist of. On a 350-satellite twin, a single timing constraint explains nearly all of the reported improvement: applied to frozen weights on identical episodes, a lower bound on the handover lead raises polar handover success from 67.5 ± 13.2% to 92.4 ± 0.3%, and to 93.3 ± 0.3% once a 2 s cost-asymmetric margin is added; without it ten checkpoints scatter across 49.8–90.0%. The bound is not recoverable from the passive log: the informative band holds 8.1% of attempts, and a cluster bootstrap over (seed, site) blocks places the 5% crossing anywhere between 10 s and 18 s. A contribution-isolation experiment then asks which components are load-bearing, holding the shield, the probe and the margin fixed. Seven provenance variants—language model, hand-written predicates, latitude grid, random predicates, with and without the Kaplan–Meier stage and the audit gate—land within 0.11 pp of the full pipeline, and a highest-elevation controller whose lead is re-probed on validation matches it within 0.03 pp with no learning at all. What does matter is calibration and admission: under 3.2 s of acquisition drift the re-probed threshold holds 93.2% against 86.0% for a tuned constant, and the audit gate admits no harmful candidate and rejects no good one on a 26-candidate bank. We therefore locate the contribution in the calibration-and-audit protocol rather than in the learner, and say so explicitly.

"""
t = t[:a] + ABSTRACT + t[b:]
done.append("abstract")

# ---------------------------------------------------------------- contributions
c0 = t.find("**Contributions.**")
if c0 < 0:
    c0 = t.find("1. **A mechanism, formalized")
c1 = t.find("## II. Related Work")
if c0 < 0 or c1 < 0:
    raise SystemExit("contributions block not found")
CONTRIB = """**Contributions.**

1. **A mechanism, with a causal audit.** A two-factor decomposition of handover reliability into feasibility and selection quality, three propositions that state what the reward channel, the passive log and the projection can and cannot deliver, and a frozen-policy factorial that measures the decomposition on common episodes: the constraint is worth 23.4 of the 24.0 pp between the reward-only baseline and the shielded system, while ten checkpoints without it scatter over 49.8–90.0%.
2. **A calibration protocol for the magnitude.** The bound is not read off the censored log; it is *measured* on the deployed policy by an active probe under an isotonic fit—Fig. 9 shows why the log cannot substitute (a cluster bootstrap puts the crossing anywhere in 10–18 s)—and then wrapped in a cost-asymmetric margin whose direction is chosen by measuring the two failure costs.
3. **A contribution-isolation experiment that narrows our own claim.** Holding the shield, the probe and the margin fixed, seven provenance variants land within 0.11 pp of the full pipeline and a probe-calibrated constant controller within 0.03 pp (Section VI-H). The language model and the Kaplan–Meier stage are therefore presented as automation of discovery and diagnosis, not as sources of performance.
4. **An admission-and-governance protocol.** A counterfactual replay gate over a 26-candidate bank (0 false accepts, 0 false rejects), a versioned knowledge graph with commit, deprecation and rollback rules, and a three-way lockbox that confines every selection to the validation window before the evaluation instances are touched.

"""
t = t[:c0] + CONTRIB + t[c1:]
done.append("contributions")

# ---------------------------------------------------------------- VI-H numbers
rows = []
order = [
    ("A0_full", "full pipeline (LLM predicate, KM, probe, gate, shared KG)"),
    ("A1_human", "hand-written predicate, chosen on validation"),
    ("A2_grid", "latitude threshold chosen by grid search"),
    ("A3_randomBest", "random predicate admitted by the gate"),
    ("A4_noKM", "full pipeline without the Kaplan–Meier stage"),
    ("A5_noGate", "full pipeline without the audit gate"),
    ("A7_probeOnly", "probe + margin + shield only"),
    ("A8_constantProbe", "highest-elevation controller, lead re-probed on validation"),
]
ARMS = iso["arms"]
for key, desc in order:
    v = ARMS.get(key, {})
    pol = v.get("polar") or {}
    ev = pol.get("eval", {}).get("mean")
    lb = pol.get("lb299.25", {}).get("mean")
    rule = v.get("rule") or "--"
    c = iso["contrasts_vs_A0"].get(key, {}).get("eval", {})
    diff = "--" if key == "A0_full" else ("%+.2f" % c.get("mean_diff", 0.0))
    rows.append("| %s | %s | `%s` | %.2f | %s | %s |" % (
        key.split("_")[0], desc, rule, ev if ev is not None else float("nan"), diff,
        "%.2f" % lb if lb is not None else "--"))
TABLE7 = ("| arm | component provenance | deployed rule | polar HSR, test (%) | vs A0 (pp) | lockbox +7 d (%) |\n"
          "|---|---|---|---|---|---|\n" + "\n".join(rows) + "\n")
rep("@@TABLE_ISOLATION@@", "**Table VII. Contribution isolation (polar HSR at |lat| ≥ 70°, n = 10 policy seeds, common "
    "episodes; all selection on the validation window).**\n\n" + TABLE7, "table7")

a8 = iso["contrasts_vs_A0"]["A8_constantProbe"]["eval"]
a7 = iso["contrasts_vs_A0"]["A7_probeOnly"]["eval"]
rep("A7 reproduces A0 with neither the language\nmodel nor the KM estimate nor the gate in the loop, and A8—a highest-elevation controller whose lead\nis re-probed on validation—tracks the shield within @@A8_DIFF@@ pp at nominal physics.",
    "A7 reproduces A0 to within %.2f pp with neither the language model nor the KM estimate nor the gate in the loop, and A8—a highest-elevation controller whose lead is re-probed on validation—tracks the shield to within %.2f pp at nominal physics (bootstrap 95%% CI [%.2f, %.2f]) and %.2f pp on the lockbox instance."
    % (a7["mean_diff"], a8["mean_diff"], a8["ci95"][0], a8["ci95"][1],
       iso["contrasts_vs_A0"]["A8_constantProbe"]["lb299.25"]["mean_diff"]),
    "a8-sentence")

P.write_text(t, encoding="utf-8")
print("applied:", done)
