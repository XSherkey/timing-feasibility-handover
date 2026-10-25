"""Where does the performance come from: the warm-start prior or the shield?

Compares, per method, the validation satisfaction right after behaviour cloning
(episode 0 of the curve) with the final test-set value.  If the initial value is
already close to the final one, the method difference is inherited from the
shared prior; if it grows, PPO or the injected constraint is doing work.

Also writes ``docs/tbd_values.json`` with every key the manuscript filler needs,
so the docx can be refilled without importing torch.
"""
from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
CAMP = ROOT / "results" / "campaign"


def main() -> int:
    by = defaultdict(list)
    for p in sorted(CAMP.glob("*/run_summary.json")):
        with open(p, encoding="utf-8") as fh:
            r = json.load(fh)
        if r.get("ok"):
            by[r["method"]].append(r)

    print(f"{'method':<20}{'S@ep0':>9}{'S@final':>9}{'delta':>8}{'arctic':>9}")
    bc = {}
    for m, rs in by.items():
        s0 = [c.get("S", float("nan")) for r in rs for c in (r.get("curve") or [])[:1]]
        sf = [c.get("S", float("nan")) for r in rs for c in (r.get("curve") or [])[-1:]]
        arc = [r["final"]["arctic"]["hsr"] * 100 for r in rs]
        bc[m] = dict(S_ep0=float(np.nanmean(s0)), S_final_curve=float(np.nanmean(sf)),
                     n=len(rs), arctic=float(np.mean(arc)))
        print(f"{m:<20}{np.nanmean(s0):9.1f}{np.nanmean(sf):9.1f}"
              f"{np.nanmean(sf) - np.nanmean(s0):+8.1f}{np.mean(arc):8.1f}%")
    (ROOT / "results/analysis/bc_vs_final.json").write_text(json.dumps(bc, indent=2), encoding="utf-8")

    # ---------------- TBD values for the manuscript ---------------- #
    tbd: dict[str, dict] = {}

    def put(k, v, src):
        tbd[k] = dict(value=v, source=src)

    def stats(m):
        rs = by.get(m) or []
        if not rs:
            return None
        arc = np.array([r["final"]["arctic"]["hsr"] * 100 for r in rs])
        sat = np.array([r["final"]["satisfaction"] for r in rs])
        return dict(mean=float(arc.mean()), std=float(arc.std(ddof=1)) if len(arc) > 1 else 0.0,
                    median=float(np.median(arc)), conv=int((arc >= 80).sum()), n=int(len(arc)),
                    sat=float(sat.mean()), params=int(rs[0].get("params", 0)))

    for m in by:
        s = stats(m)
        put(f"hsr.{m}.arctic", f"{s['mean']:.1f} ± {s['std']:.1f} (median {s['median']:.1f}, "
                               f"converged {s['conv']}/{s['n']})", f"campaign/{m}")
        put(f"satisfaction.{m}", f"{s['sat']:.1f}", f"campaign/{m}")
    lat = json.loads((ROOT / "results/latency_benchmark.json").read_text(encoding="utf-8"))
    v = lat["variants"]
    put("latency.ort_cpu_fp32", f"{v['ort_cpu_fp32']['mean_ms']:.3f} ms mean / "
                                f"{v['ort_cpu_fp32']['p99_ms']:.3f} ms p99", "latency_benchmark")
    put("latency.ort_cpu_fp16", f"{v['ort_cpu_fp16']['mean_ms']:.3f} / {v['ort_cpu_fp16']['p99_ms']:.3f} ms",
        "latency_benchmark")
    put("latency.ort_cpu_int8", f"{v['ort_cpu_int8']['mean_ms']:.3f} / {v['ort_cpu_int8']['p99_ms']:.3f} ms",
        "latency_benchmark")
    sw = lat.get("policy_switch", {})
    put("policy_switch", f"{sw.get('load_state_dict_ms', float('nan')):.3f} ms load_state_dict",
        "latency_benchmark")
    put("policy_bytes", f"{lat.get('onnx_bytes_fp32', 0) / 1024:.0f} KB", "latency_benchmark")
    fid = json.loads((ROOT / "results/fidelity.json").read_text(encoding="utf-8"))
    lb = fid["link_budget"]
    put("twin_link_budget",
        f"{lb.get('range_error_db_p95', float('nan')):.3f} dB p95 "
        f"(max {lb.get('range_error_db_max', float('nan')):.3f} dB)", "fidelity")
    stress = json.loads((ROOT / "results/auditor_stress.json").read_text(encoding="utf-8"))
    put("audit.false_acceptance", f"{stress['overall']['false_acceptance'] * 100:.1f}%", "auditor_stress")
    put("audit.false_rejection", f"{stress['overall']['false_rejection'] * 100:.1f}%", "auditor_stress")
    imp_p = ROOT / "results/impact_predictor.json"
    if imp_p.exists():
        imp = json.loads(imp_p.read_text(encoding="utf-8"))
        put("impact_mae", f"{imp['mae']:.2f} ms (target sd {imp['delta_latency_std']:.2f} ms)",
            "impact_predictor")
        put("impact_calibration", f"slope {imp['calibration_slope']:.2f}", "impact_predictor")
        put("impact_flip_rate", f"{imp['decision_flip_rate'] * 100:.0f}%", "impact_predictor")
    st_p = ROOT / "results/llm_stability.json"
    if st_p.exists():
        st = json.loads(st_p.read_text(encoding="utf-8"))
        for ct, val in st.items():
            if isinstance(val, dict) and "exact_match" in val:
                put(f"llm_stability.{ct}",
                    f"exact {val['exact_match'] * 100:.0f}%, semantic "
                    f"{val['semantic_equivalence'] * 100:.0f}%, schema-fail "
                    f"{val['schema_failure_rate'] * 100:.1f}%, repair "
                    f"{val.get('retry_rate', 0) * 100:.1f}% ({val['n_calls']} calls)", "llm_stability")
    put("llm.backend", "deepseek-flash via the OpenAI-compatible API (all 80 runs)", "campaign")
    sweep_l = json.loads((ROOT / "results/nas/sweep_llm.json").read_text(encoding="utf-8"))
    sweep_r = json.loads((ROOT / "results/nas/sweep_random.json").read_text(encoding="utf-8"))
    bl = [r["best_reward"] for r in sweep_l["runs"] if r.get("best_reward") is not None]
    br = [r["best_reward"] for r in sweep_r["runs"] if r.get("best_reward") is not None]
    put("nas.llm_best", f"{np.mean(bl):.3f} ± {np.std(bl, ddof=1):.3f} (median {np.median(bl):.2f})",
        "nas/sweep_llm")
    put("nas.random_best", f"{np.mean(br):.3f} ± {np.std(br, ddof=1):.3f} (median {np.median(br):.2f})",
        "nas/sweep_random")
    put("nas.llm_evals", str(sweep_l["runs"][0].get("evaluated") or 42), "nas/sweep_llm")
    put("nas.llm_wall", f"{np.mean([r['wall_s'] for r in sweep_l['runs']]):.0f} s per search",
        "nas/sweep_llm")
    rec_p = ROOT / "results/forensics_recall.json"
    if rec_p.exists():
        rec = json.loads(rec_p.read_text(encoding="utf-8"))
        for mode in ("legacy", "enriched"):
            d = rec.get(mode) or {}
            put(f"recall.{mode}",
                f"commit {d.get('commit_rate', 0) * 100:.0f}%, recall "
                f"{d.get('recall_committed', 0) * 100:.1f}%, discovery rows "
                f"{d.get('discovery_rows', 0):.1f}", "forensics_recall")
    (ROOT / "docs/tbd_values.json").write_text(json.dumps(tbd, indent=2, ensure_ascii=False),
                                               encoding="utf-8")
    print(f"\ntbd values: {len(tbd)} -> docs/tbd_values.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
