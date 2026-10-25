"""Assemble the reproduction report and the TBD -> measured-value mapping.

Reads every experiment artefact under ``results/`` and emits

* ``docs/REPRODUCTION_REPORT.md``  - full report (design, calibration, tables)
* ``docs/tbd_values.json``         - machine-readable TBD -> value map
* ``docs/TBD_FILLED.md``           - the TBD table alone
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]


def load(p, default=None):
    f = ROOT / p
    if not f.exists():
        return default
    try:
        return json.loads(f.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return default


def fmt(x, nd=2, suffix=""):
    if x is None:
        return "n/a"
    try:
        v = float(x)
    except (TypeError, ValueError):
        return str(x)
    if not np.isfinite(v):
        return "n/a"
    return f"{v:.{nd}f}{suffix}"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="docs")
    args = ap.parse_args()
    out = ROOT / args.out
    out.mkdir(parents=True, exist_ok=True)

    tables = load("results/analysis/tables.json")
    latency = load("results/latency_benchmark.json")
    stress = load("results/auditor_stress.json")
    stability = load("results/llm_stability.json")
    impact = load("results/impact_predictor.json")
    fidelity = load("results/fidelity.json")
    sensitivity = load("results/sensitivity.json")
    nas_llm = load("results/nas/llm_spec.json")
    nas_rand = load("results/nas/random_spec.json")
    env_meta = load("data/cache/twin_ref_e85c26203e2a/meta.json")

    tbd: dict[str, dict] = {}

    def put(key, value, source, note=""):
        tbd[key] = dict(value=value, source=source, note=note)

    # ---------- reliability / Table 8 ---------- #
    if tables:
        reg = tables["region"]
        for m, e in reg.items():
            for r in ("arctic", "subarctic", "midlat", "equatorial", "overall"):
                s = e[r]
                put(f"hsr.{m}.{r}",
                    f"{s['mean']:.1f} ± {s['std']:.1f} (95% CI {s['ci_low']:.1f}-{s['ci_high']:.1f})",
                    f"campaign/{m}", f"n={s['n']} seeds")
            put(f"satisfaction.{m}", f"{e['satisfaction']['mean']:.1f} ± {e['satisfaction']['std']:.1f}",
                f"campaign/{m}")
            put(f"params.{m}", f"{e['params']['mean']:.0f}", f"campaign/{m}")
            put(f"kg_active.{m}", f"{e['kg_active']:.1f}", f"campaign/{m}")
        if "almond" in reg and "oracle" in reg:
            put("oracle_arctic_hsr", f"{reg['oracle']['arctic']['mean']:.1f}%",
                "campaign/oracle", "Sec. 4.2 oracle value")
            put("almond_minus_oracle_arctic",
                f"{reg['almond']['arctic']['mean'] - reg['oracle']['arctic']['mean']:+.1f} pp",
                "campaign", "remaining ALMOND-oracle gap")
        conv = tables.get("convergence", {})
        for m, v in conv.items():
            put(f"ep90.{m}", f"{v['episodes_90']['mean']:.0f} ± {v['episodes_90']['std']:.0f}",
                f"campaign/{m}", "episodes to 90% of own asymptote")
            put(f"epS75.{m}", f"{v['episodes_s75']['mean']:.0f} ± {v['episodes_s75']['std']:.0f}",
                f"campaign/{m}", "episodes to S>=75")
            put(f"peakS.{m}", f"{v['peak_S']['mean']:.1f} ± {v['peak_S']['std']:.1f}",
                f"campaign/{m}")
        for m, v in tables.get("convergence_ratio", {}).items():
            put(f"speed_ratio.{m}", f"{v['ratio']:.2f}x (95% CI {v['lo']:.2f}-{v['hi']:.2f})",
                "campaign", "baseline episodes / ALMOND episodes")
        for t in tables.get("paired_region", {}).get("arctic", []):
            put(f"paired.{t['name']}",
                f"median diff {t['median_diff']:+.1f} pp, Wilcoxon p={t['p_wilcoxon']:.4f}, "
                f"Holm p={t['p_holm']:.4f}, Cohen d={t['cohen_d']:.2f}, r_rb={t['rank_biserial']:.2f}",
                "campaign")

    # ---------- latency / Table 6 ---------- #
    if latency:
        v = latency["variants"]
        for k, d in v.items():
            if "mean_ms" in d:
                put(f"latency.{k}", f"{d['mean_ms']:.3f} ms mean / {d['p99_ms']:.3f} ms p99",
                    "latency_benchmark", latency["board"]["cpu"])
        put("policy_switch",
            f"{latency['policy_switch']['load_state_dict_ms']:.3f} ms restore, "
            f"{latency['policy_switch']['serialized_bytes']} B serialized", "latency_benchmark")
        put("policy_bytes", f"{latency['weight_bytes_fp32'] / 1024:.1f} KB (FP32 weights)", "latency_benchmark")
        if "quantisation_effect" in latency:
            for k, d in latency["quantisation_effect"].items():
                put(f"quant.{k}",
                    f"HSR {d['hsr_all_fp32']:.1f}->{d['hsr_all_quant']:.1f}%, arctic "
                    f"{d['hsr_arctic_fp32']:.1f}->{d['hsr_arctic_quant']:.1f}%, flaps/h "
                    f"{d['flaps_per_hour_fp32']:.2f}->{d['flaps_per_hour_quant']:.2f}",
                    "latency_benchmark")

    # ---------- auditor / Table 7 ---------- #
    if stress:
        for cls, sc in stress["summary"].items():
            acc = sc["false_acceptance"]
            rej = sc["false_rejection"]
            acc_s = "-" if acc is None else f"{acc * 100:.0f}%"
            rej_s = "-" if rej is None else f"{rej * 100:.0f}%"
            put(f"audit.{cls}",
                f"semantic {sc['semantic_detect'] * 100:.0f}%, physics {sc['physics_detect'] * 100:.0f}%, "
                f"accept {acc_s}, reject {rej_s}",
                "auditor_stress")
        put("audit.false_acceptance", f"{stress['overall']['false_acceptance'] * 100:.1f}%", "auditor_stress")
        put("audit.false_rejection", f"{stress['overall']['false_rejection'] * 100:.1f}%", "auditor_stress")
    if stability:
        for ct, v in stability.items():
            if not isinstance(v, dict) or "exact_match" not in v:
                continue  # skips the "_meta" block
            put(f"llm_stability.{ct}",
                f"exact {v['exact_match'] * 100:.0f}%, semantic {v['semantic_equivalence'] * 100:.0f}%, "
                f"schema-fail {v['schema_failure_rate'] * 100:.1f}%", "llm_stability")
    if impact:
        put("impact_mae", f"{impact['mae']:.2f} ms (target sd {impact['delta_latency_std']:.2f} ms)",
            "impact_predictor")
        put("impact_calibration", f"slope {impact['calibration_slope']:.2f}", "impact_predictor")
        put("impact_flip_rate", f"{impact['decision_flip_rate'] * 100:.0f}%", "impact_predictor")

    # ---------- fidelity / Sec 4.8 ---------- #
    if fidelity:
        lb = fidelity["link_budget"]
        put("twin_link_budget",
            f"range error p95 {lb['range_error_db_p95']:.4f} dB, max {lb['range_error_db_max']:.4f} dB; "
            f"SNR recomputation p95 {lb['snr_error_db_p95']:.3f} dB", "fidelity")
        s = fidelity["summary"]
        put("twin_rule_replication", f"{s['rules_replicated']}/{s['rules_tested']} "
            f"({s['replication_rate'] * 100:.0f}%)", "fidelity")

    # ---------- sensitivity / Table 9 ---------- #
    if sensitivity:
        def _pct(x):
            x = float(x)
            return "n/a" if not np.isfinite(x) else f"{x * 100:.0f}%"

        for th, v in sensitivity["theta_rho"].items():
            put(f"sens.theta.{th}",
                f"fires {v['fires']}, precision {_pct(v['precision'])}, recall {_pct(v['recall'])}",
                "sensitivity")
        for dm, v in sensitivity["delta_min"].items():
            put(f"sens.delta.{dm}",
                f"accepted {v['accepted']}/{v['n']}, precision {_pct(v['precision'])}, "
                f"recall {_pct(v['recall'])}", "sensitivity")

    # ---------- NAS ---------- #
    if nas_llm:
        d = nas_llm.get("nas") or {}
        put("nas.llm_spec", json.dumps(nas_llm["spec"]), "nas/llm_spec")
        put("nas.llm_evals", f"{d.get('evaluated', 'n/a')} architectures", "nas/llm_spec")
        put("nas.llm_wall", f"{nas_llm.get('wall_s', float('nan')):.0f} s", "nas/llm_spec")
    if nas_rand:
        d = nas_rand.get("nas") or {}
        put("nas.random_spec", json.dumps(nas_rand["spec"]), "nas/random_spec")
        put("nas.random_evals", f"{d.get('evaluated', 'n/a')} architectures", "nas/random_spec")
        put("nas.random_wall", f"{nas_rand.get('wall_s', float('nan')):.0f} s", "nas/random_spec")

    # ---------- compute cost ---------- #
    if tables:
        walls = []
        for m in ("almond", "ppomlp"):
            pass
    campaign_walls = {}
    for d in sorted((ROOT / "results" / "campaign").glob("*/run_summary.json")):
        try:
            r = json.loads(d.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        campaign_walls.setdefault(r["method"], []).append(r.get("wall_s", float("nan")))
    if campaign_walls:
        for m, w in campaign_walls.items():
            put(f"wall.{m}", f"median {np.nanmedian(w):.0f} s per seed-run "
                f"({np.nanmedian(w) / 3600:.3f} h)", "campaign")

    # ---------- environment ---------- #
    if env_meta:
        put("twin.constellation", f"{env_meta['n_sat']} sats, {env_meta['n_time']} steps, "
            f"dt {env_meta['dt_s']} s, horizon {env_meta['horizon_s'] / 3600:.0f} h",
            "data/cache/.../meta.json")

    (out / "tbd_values.json").write_text(json.dumps(tbd, indent=2), encoding="utf-8")

    # ---------- TBD table ---------- #
    lines = ["# TBD -> measured value map\n",
             "Every entry names the artefact it was read from. Values that could not be measured are",
             "listed in the report's limitations section rather than invented here.\n",
             "| key | measured value | source | note |", "|---|---|---|---|"]
    for k, v in tbd.items():
        lines.append(f"| `{k}` | {v['value']} | {v['source']} | {v['note']} |")
    (out / "TBD_FILLED.md").write_text("\n".join(lines), encoding="utf-8")

    print(f"[report] {len(tbd)} TBD entries -> {out / 'tbd_values.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
