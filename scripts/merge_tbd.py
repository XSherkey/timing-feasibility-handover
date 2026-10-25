"""Merge the real-LLM measurement artefacts into the TBD value map."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
p = ROOT / "docs" / "tbd_values.json"
d = json.loads(p.read_text(encoding="utf-8"))

cmp_path = ROOT / "results" / "backend_comparison.json"
if cmp_path.exists():
    cmp = json.loads(cmp_path.read_text(encoding="utf-8"))
    for m, s in cmp["real"].items():
        d[f"real.hsr.{m}.arctic"] = dict(
            value=(f"{s['arctic_mean']:.1f} ± {s['arctic_std']:.1f} "
                   f"(median {s['arctic_median']:.1f}, convergence {s['converged']}/{s['n']})"),
            source=f"campaign/{m} (deepseek-flash)",
            note="real-LLM run",
        )
    u = cmp["llm"]["real"]
    d["llm.real.usage"] = dict(
        value=(f"{u['calls_total']} calls, {u['tokens_in']} prompt / {u['tokens_out']} completion "
               f"tokens, {u['schema_retries']} schema retries, {u['latency_s_total']:.0f} s total"),
        source="backend_comparison",
        note="deepseek-flash",
    )
    d["llm.backend"] = dict(
        value="deepseek-flash via OpenAI-compatible API (surrogate kept only as offline fallback)",
        source="backend_comparison",
        note="real model",
    )

st_path = ROOT / "results" / "llm_stability.json"
if st_path.exists():
    st = json.loads(st_path.read_text(encoding="utf-8"))
    for ct, v in st.items():
        if ct == "_meta" or not isinstance(v, dict) or "exact_match" not in v:
            continue
        d[f"llm_stability.{ct}"] = dict(
            value=(f"exact {v['exact_match'] * 100:.0f}%, semantic {v['semantic_equivalence'] * 100:.0f}%, "
                   f"schema-fail {v['schema_failure_rate'] * 100:.1f}%, repair re-prompts "
                   f"{v['retry_rate'] * 100:.1f}% ({v['n_calls']} calls)"),
            source="llm_stability",
            note="real LLM",
        )

p.write_text(json.dumps(d, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"TBD entries: {len(d)}")
for k in ("llm.backend", "llm.real.usage", "llm_stability.forward_translate",
          "llm_stability.forensic_hypothesis", "real.hsr.almond.arctic", "real.hsr.ppomlp.arctic"):
    if k in d:
        print(f"  {k:<40} {d[k]['value']}")
