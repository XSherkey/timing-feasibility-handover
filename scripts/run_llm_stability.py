"""LLM output stability (manuscript Sec. 4.6, item ii).

Each call type is repeated ``--repeats`` times per intent over five intents.
Reports, per call type:

* exact-match rate - bytewise identical responses after canonical JSON
  serialisation;
* semantic-equivalence rate - the decision content is the same (same weight
  ordering and rounded profile, same predicate, same graph family);
* schema-failure rate and the fraction of calls that needed a repair re-prompt.

Works with either backend: pass ``--backend surrogate`` or leave it on ``auto``
to use whatever ``ALMOND_LLM_*`` points at.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from almond.framework.translator import INTENT_TEMPLATES
from almond.llm.backend import LLMClient, LLMLog, SurrogateBackend, _default_backend
from almond.llm.schema import validate_response

INTENTS = ["reliability_first", "latency_first", "power_first", "balanced", "reliability_first"]
TYPES = [
    "forward_translate",
    "forensic_hypothesis",
    "topology_seed",
    "topology_mutation",
    "topology_crossover",
    "population_critique",
]
#: the two safety-relevant call types get the full repeat budget
SAFETY = {"forward_translate", "forensic_hypothesis"}


def canon(obj) -> str:
    return json.dumps(obj, sort_keys=True, default=str)


def semantic_key(call_type: str, data: dict) -> str:
    if call_type == "forward_translate":
        w = data.get("weights", {})
        order = tuple(sorted(w, key=lambda k: -float(w.get(k, 0))))
        q = tuple(round(float(w.get(k, 0)), 1) for k in order)
        return f"{order}|{q}"
    if call_type == "forensic_hypothesis":
        hyps = data.get("hypotheses", [])
        if not hyps:
            return "empty"
        h = hyps[0]
        atoms = tuple(sorted(
            (a["field"], a["cmp"], round(float(a["value"]), 3)) for a in h["if"]["all"]
        ))
        return f"{atoms}|{h['then']['effect']}|{round(float(h['then'].get('magnitude', 0)), 1)}"
    return canon({k: v for k, v in data.items() if k != "rationale"})


def make_payload(call_type: str, intent_name: str, seed: int) -> dict:
    from almond.llm.surrogate import EFFECT_GRAMMAR, FIELD_SCHEMA

    intent = INTENT_TEMPLATES[intent_name]
    rng = np.random.default_rng(seed)
    if call_type == "forward_translate":
        return dict(intent=intent, env_desc="LEO handover", task_short_desc="handover")
    if call_type == "forensic_hypothesis":
        fails, succ = [], []
        for _ in range(40):
            fails.append(dict(step=10, site="Alert", elevation_deg=float(rng.uniform(8, 14)),
                              handover_advance_s=float(rng.choice([6, 8])),
                              isl_hop_count=int(rng.integers(1, 5)),
                              doppler_rate_hz_s=float(rng.uniform(1000, 3000)),
                              latitude_abs_deg=float(rng.uniform(70, 80)),
                              snr_db=float(rng.uniform(8, 16)),
                              remaining_visibility_s=float(rng.uniform(20, 90)),
                              plane_change=1.0, path_available=1.0,
                              buffer_occupancy=0.4, battery_state=1.0, eclipse=0.0))
        for _ in range(80):
            succ.append(dict(step=10, site="Alert", elevation_deg=float(rng.uniform(25, 70)),
                             handover_advance_s=float(rng.choice([14, 16])),
                             isl_hop_count=int(rng.integers(0, 3)),
                             doppler_rate_hz_s=float(rng.uniform(500, 1500)),
                             latitude_abs_deg=float(rng.uniform(30, 65)),
                             snr_db=float(rng.uniform(16, 26)),
                             remaining_visibility_s=float(rng.uniform(120, 400)),
                             plane_change=0.0, path_available=1.0,
                             buffer_occupancy=0.5, battery_state=1.0, eclipse=0.0))
        return dict(policy_id="pi", region_tags={"polar": True}, kpi="hsr", kpi_value=0.55,
                    threshold=0.85, failure_narratives=[f"at t=100s, elevation {r['elevation_deg']:.1f} deg, "
                                                        f"advance {r['handover_advance_s']:.0f} s -> session lost"
                                                        for r in fails[:8]],
                    failure_rows=fails, success_rows=succ,
                    field_schema=FIELD_SCHEMA, effect_grammar=EFFECT_GRAMMAR)
    if call_type == "topology_seed":
        return dict(regime_tags={"polar": True, "sparse_isl": True},
                    regime_hint="sparse polar connectivity", history=[])
    if call_type == "topology_mutation":
        return dict(sketch=dict(kind="gcn", width=64, layers=2, heads=1, pool="mean",
                                ctx_width=64, ctx_layers=1),
                    fitness_feedback=dict(objective="params", too_large=True))
    if call_type == "topology_crossover":
        return dict(sketch_a=dict(kind="gcn", width=64, layers=2, heads=1, pool="mean",
                                  ctx_width=64, ctx_layers=1),
                    sketch_b=dict(kind="hybrid", width=128, layers=3, heads=4, pool="max",
                                  ctx_width=96, ctx_layers=2))
    if call_type == "population_critique":
        return dict(elites=[dict(kind="gcn", width=64, layers=2, reward=0.5, params=27000)],
                    probs=dict(mutation_rate=0.35, crossover_rate=0.4))
    raise ValueError(call_type)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repeats", type=int, default=20, help="repeats for safety-relevant calls")
    ap.add_argument("--other-repeats", type=int, default=8)
    ap.add_argument("--intents", type=int, default=5)
    ap.add_argument("--out", default="results/llm_stability.json")
    ap.add_argument("--backend", default="auto", choices=["auto", "surrogate"])
    ap.add_argument("--types", default="all", help="comma-separated subset of call types")
    args = ap.parse_args()

    backend = SurrogateBackend() if args.backend == "surrogate" else _default_backend()
    log_path = Path(args.out).with_suffix(".calls.jsonl")
    if log_path.exists():
        log_path.unlink()
    client = LLMClient(backend, LLMLog(log_path), max_retries=4)
    print(f"backend={client.backend.name} model={getattr(client.backend, 'model', 'n/a')}")

    types = TYPES if args.types == "all" else [t.strip() for t in args.types.split(",") if t.strip()]
    out = {}
    for ct in types:
        n_rep = args.repeats if ct in SAFETY else args.other_repeats
        group = max(2, n_rep // 4)
        retries_before = client.schema_retries
        exact, sem, n_ok, n_calls = [], [], 0, 0
        for i, intent in enumerate(INTENTS[: args.intents]):
            for base in range(4):
                resps = []
                for r in range(group):
                    data = client.try_call(ct, make_payload(ct, intent, 1000 * i + base),
                                           seed=10_000 * i + 100 * base + r, default=None)
                    n_calls += 1
                    if data is None:
                        continue
                    ok, _ = validate_response(ct, data)
                    n_ok += int(ok)
                    resps.append(data)
                if len(resps) >= 2:
                    keys = [canon(d) for d in resps]
                    sems = [semantic_key(ct, d) for d in resps]
                    exact.append(len(set(keys)) == 1)
                    vals, counts = np.unique(sems, return_counts=True)
                    sem.append(float(counts.max() / len(sems)))
        retries_here = client.schema_retries - retries_before
        out[ct] = dict(
            exact_match=float(np.mean(exact)) if exact else float("nan"),
            semantic_equivalence=float(np.mean(sem)) if sem else float("nan"),
            schema_failure_rate=float(1.0 - n_ok / max(n_calls, 1)),
            retry_rate=float(retries_here / max(n_calls, 1)),
            retries=retries_here,
            n_calls=n_calls,
            n_groups=len(exact),
        )
        print(f"  {ct:<24} exact {out[ct]['exact_match']*100:5.0f}%  semantic "
              f"{out[ct]['semantic_equivalence']*100:5.0f}%  calls {n_calls}")

    summary = client.log.summary()
    out["_meta"] = dict(
        backend=client.backend.name,
        model=getattr(client.backend, "model", "surrogate"),
        schema_retries=int(client.schema_retries),
        exhausted=int(client.exhausted),
        **summary,
    )
    Path(args.out).write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"\n{'call type':<24}{'exact':>8}{'semantic':>10}{'schema-fail':>13}{'retry':>8}")
    for ct in types:
        v = out[ct]
        print(f"{ct:<24}{v['exact_match']*100:7.0f}%{v['semantic_equivalence']*100:9.0f}%"
              f"{v['schema_failure_rate']*100:12.1f}%{v['retry_rate']*100:7.1f}%")
    print("meta:", json.dumps(out["_meta"], indent=2))
    print("wrote", args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
