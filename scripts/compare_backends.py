"""Compare the surrogate-backed campaign with the real-LLM campaign.

Produces ``results/backend_comparison.json`` and a markdown table showing, per
method, the Arctic handover success (mean / median / convergence rate), the
intent-satisfaction score, and the weights the forward translator produced under
each backend.  Also summarises LLM usage (calls, tokens, latency, schema
retries) so the cost of the real model is auditable.
"""
from __future__ import annotations

import argparse
import json
import statistics as st
from collections import defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
ORDER = [
    "almond", "almond_fixedarch", "oracle", "no_forensics", "static_llm",
    "eureka", "ppomlp", "unseeded_evonas",
]
DISPLAY = {
    "almond": "ALMOND", "almond_fixedarch": "ALMOND-FixedArch", "oracle": "Oracle-PPO",
    "no_forensics": "ALMOND w/o forensics", "static_llm": "Static-LLM",
    "eureka": "Eureka-style", "ppomlp": "PPO-MLP", "unseeded_evonas": "Unseeded-EvoNAS",
}


def load(campaign: Path) -> dict[str, list[dict]]:
    out: dict[str, list[dict]] = defaultdict(list)
    if not campaign.exists():
        return out
    for p in sorted(campaign.glob("*/run_summary.json")):
        try:
            r = json.loads(p.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        if r.get("ok"):
            out[r["method"]].append(r)
    return out


def stats(runs: list[dict]) -> dict:
    if not runs:
        return {}
    arc = np.array([r["final"]["arctic"]["hsr"] * 100 for r in runs], dtype=float)
    sat = np.array([r["final"]["satisfaction"] for r in runs], dtype=float)
    conv = int(np.sum(arc >= 80.0))
    w = np.array([[r["weights"]["w_rel"], r["weights"]["w_lat"], r["weights"]["w_pow"]] for r in runs])
    return dict(
        n=len(runs),
        arctic_mean=float(np.mean(arc)),
        arctic_std=float(np.std(arc, ddof=1)) if len(arc) > 1 else 0.0,
        arctic_median=float(np.median(arc)),
        converged=conv,
        converged_rate=conv / len(runs),
        satisfaction=float(np.mean(sat)),
        weights_w_rel=float(np.mean(w[:, 0])),
        weights_w_lat=float(np.mean(w[:, 1])),
        weights_w_pow=float(np.mean(w[:, 2])),
        params=float(np.mean([r.get("params", np.nan) for r in runs])),
        kg_active=float(np.mean([r.get("kg", {}).get("n_active", 0) for r in runs])),
        forensic_commits=float(np.mean([sum(1 for f in (r.get("forensics") or []) if f.get("accepted")) for r in runs])),
    )


def llm_usage(runs: list[dict]) -> dict:
    calls = [r.get("llm", {}).get("calls", 0) for r in runs]
    tin = [r.get("llm", {}).get("tokens_in", 0) for r in runs]
    tout = [r.get("llm", {}).get("tokens_out", 0) for r in runs]
    retries = [r.get("llm", {}).get("schema_retries", 0) for r in runs]
    lat = [r.get("llm", {}).get("latency_s", 0.0) for r in runs]
    backends = sorted({r.get("llm", {}).get("backend", "?") for r in runs})
    models = sorted({r.get("llm", {}).get("model", "?") for r in runs})
    return dict(
        backends=backends, models=models,
        calls_total=int(sum(calls)), calls_median=float(np.median(calls)) if calls else 0.0,
        tokens_in=int(sum(tin)), tokens_out=int(sum(tout)),
        schema_retries=int(sum(retries)),
        latency_s_total=float(sum(lat)), latency_s_median=float(np.median(lat)) if lat else 0.0,
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--surrogate", default="results/campaign_surrogate")
    ap.add_argument("--real", default="results/campaign")
    ap.add_argument("--out", default="results/backend_comparison.json")
    args = ap.parse_args()

    sur = load(ROOT / args.surrogate)
    real = load(ROOT / args.real)
    out = dict(surrogate={}, real={}, llm=dict(surrogate={}, real={}))
    lines = []
    for name, data, key in (("surrogate", sur, "surrogate"), ("real", real, "real")):
        for m, runs in data.items():
            out[key][m] = stats(runs)
        out["llm"][key] = llm_usage([r for runs in data.values() for r in runs])

    methods = [m for m in ORDER if m in out["real"] or m in out["surrogate"]]
    lines.append("| method | surrogate Arctic (mean/med/conv) | real-LLM Arctic (mean/med/conv) | Δ mean | ")
    lines.append("|---|---|---|---|")
    for m in methods:
        s = out["surrogate"].get(m, {})
        r = out["real"].get(m, {})
        def fmt(d):
            if not d:
                return "n/a"
            return f"{d['arctic_mean']:.1f}/{d['arctic_median']:.1f}/{d['converged']}-of-{d['n']}"
        delta = (
            f"{r['arctic_mean'] - s['arctic_mean']:+.1f}"
            if s and r
            else "n/a"
        )
        lines.append(f"| {DISPLAY.get(m, m)} | {fmt(s)} | {fmt(r)} | {delta} |")

    lines.append("")
    lines.append("| method | weights (w_rel/w_lat/w_pow), surrogate | weights, real | satisfaction sur./real |")
    lines.append("|---|---|---|---|")
    for m in methods:
        s = out["surrogate"].get(m, {})
        r = out["real"].get(m, {})
        def w(d):
            return "n/a" if not d else f"{d['weights_w_rel']:.2f}/{d['weights_w_lat']:.2f}/{d['weights_w_pow']:.2f}"
        def sat(d):
            return "n/a" if not d else f"{d['satisfaction']:.1f}"
        lines.append(f"| {DISPLAY.get(m, m)} | {w(s)} | {w(r)} | {sat(s)} / {sat(r)} |")

    (ROOT / args.out).write_text(json.dumps(out, indent=2), encoding="utf-8")
    md = ROOT / args.out.replace(".json", ".md")
    md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    print()
    for key in ("surrogate", "real"):
        u = out["llm"][key]
        print(f"[{key}] backends={u['backends']} models={u['models']} calls={u['calls_total']} "
              f"tokens_in={u['tokens_in']} tokens_out={u['tokens_out']} "
              f"schema_retries={u['schema_retries']} llm_latency_total={u['latency_s_total']:.0f}s")
    print("wrote", args.out, "and", md.name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
