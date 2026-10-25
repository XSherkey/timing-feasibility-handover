"""Live smoke test of the real LLM backend against the six call types.

Runs one call of each type through the real endpoint, prints the raw response,
whether it satisfies the Appendix-A schema, how many repair attempts were needed
and the token/latency cost.  This is the gate that decides whether the real-model
campaign can be launched.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from almond.framework.translator import INTENT_TEMPLATES
from almond.llm.backend import LLMClient, LLMLog, OpenAICompatBackend
from almond.llm.schema import validate_response

CALL_TYPES = (
    "forward_translate",
    "forensic_hypothesis",
    "topology_seed",
    "topology_mutation",
    "topology_crossover",
    "population_critique",
)


def payloads(seed: int = 0) -> dict[str, dict]:
    rng = np.random.default_rng(seed)
    fails, succ = [], []
    for _ in range(40):
        fails.append(dict(
            step=int(rng.integers(5, 200)), site="Alert", lat=82.5, serving=12, target=37,
            elevation_deg=float(rng.uniform(10, 14)), handover_advance_s=float(rng.choice([6, 8])),
            isl_hop_count=int(rng.integers(1, 5)), doppler_rate_hz_s=float(rng.uniform(1000, 3000)),
            latitude_abs_deg=float(rng.uniform(70, 80)), snr_db=float(rng.uniform(8, 16)),
            remaining_visibility_s=float(rng.uniform(20, 70)), plane_change=1.0, path_available=1.0,
            buffer_occupancy=0.4, battery_state=1.0, eclipse=0.0, t_setup_s=13.0, success=False))
    for _ in range(80):
        succ.append(dict(
            step=int(rng.integers(5, 200)), site="Alert", lat=82.5, serving=12, target=37,
            elevation_deg=float(rng.uniform(25, 70)), handover_advance_s=float(rng.choice([14, 16])),
            isl_hop_count=int(rng.integers(0, 3)), doppler_rate_hz_s=float(rng.uniform(500, 1500)),
            latitude_abs_deg=float(rng.uniform(30, 65)), snr_db=float(rng.uniform(16, 26)),
            remaining_visibility_s=float(rng.uniform(120, 400)), plane_change=0.0, path_available=1.0,
            buffer_occupancy=0.5, battery_state=1.0, eclipse=0.0, t_setup_s=4.0, success=True))
    return {
        "forward_translate": dict(
            intent=INTENT_TEMPLATES["reliability_first"],
            env_desc="LEO handover: 14 telemetry fields + 8 candidates; action = target and lead time.",
            task_short_desc="LEO handover control with a 350-satellite digital twin",
            knowledge_context=dict(constraints=[]),
        ),
        "forensic_hypothesis": dict(
            policy_id="pi_almon", region_tags={"polar": True}, kpi="hsr", kpi_value=0.55, threshold=0.85,
            failure_narratives=[f"at t={r['step']*10}s on Alert, elevation {r['elevation_deg']:.1f} deg, "
                                f"advance {r['handover_advance_s']:.0f} s, hops {r['isl_hop_count']}, "
                                f"plane change {int(r['plane_change'])}, visibility left "
                                f"{r['remaining_visibility_s']:.0f} s -> session lost" for r in fails[:8]],
            failure_rows=fails, success_rows=succ,
            field_schema=[], effect_grammar=[],
        ),
        "topology_seed": dict(regime_tags={"polar": True, "sparse_isl": True},
                             regime_hint="sparse polar connectivity; prefer graph convolution over attention",
                             history=[]),
        "topology_mutation": dict(
            sketch=dict(kind="gcn", width=64, layers=2, heads=1, pool="mean", ctx_width=64, ctx_layers=1),
            fitness_feedback=dict(objective="params", too_large=True)),
        "topology_crossover": dict(
            sketch_a=dict(kind="gcn", width=64, layers=2, heads=1, pool="mean",
                          ctx_width=64, ctx_layers=1),
            sketch_b=dict(kind="hybrid", width=128, layers=3, heads=4, pool="max",
                          ctx_width=96, ctx_layers=2)),
        "population_critique": dict(
            elites=[dict(kind="gcn", width=64, layers=2, reward=0.5, params=27000),
                    dict(kind="mlp", width=128, layers=3, reward=0.62, params=41000)],
            probs=dict(mutation_rate=0.35, crossover_rate=0.4)),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--calls", default="all")
    ap.add_argument("--out", default="results/llm_live_smoke.json")
    args = ap.parse_args()

    log = LLMLog(Path("results") / "llm_live_calls.jsonl")
    client = LLMClient(OpenAICompatBackend(), log, max_retries=4)
    print(f"backend={client.backend.name} model={client.backend.model} url={client.backend.base_url}")

    types = CALL_TYPES if args.calls == "all" else tuple(args.calls.split(","))
    p = payloads()
    out = {}
    for ct in types:
        t0 = time.time()
        try:
            data = client(ct, p[ct], seed=7)
            ok, problem = validate_response(ct, data)
            dt = time.time() - t0
            print(f"\n=== {ct} ===  {dt:.1f}s  schema_ok={ok} {problem}")
            text = json.dumps(data, ensure_ascii=False)
            print(text[:900] + (" ..." if len(text) > 900 else ""))
            out[ct] = dict(ok=ok, problem=problem, latency_s=dt, data=data)
        except Exception as exc:
            dt = time.time() - t0
            print(f"\n=== {ct} ===  {dt:.1f}s  FAILED: {exc}")
            out[ct] = dict(ok=False, error=str(exc), latency_s=dt)
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    print("\n--- summary ---")
    print(f"schema retries: {client.schema_retries}, exhausted: {client.exhausted}, calls: {client.calls}")
    print(json.dumps(client.log.summary(), indent=2))
    print("wrote", args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
