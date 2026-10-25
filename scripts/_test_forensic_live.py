import sys, json, time
sys.path.insert(0, r"D:\almond-repro")
import numpy as np
from almond.llm.backend import LLMClient, LLMLog, OpenAICompatBackend
from almond.llm.surrogate import FIELD_SCHEMA, EFFECT_GRAMMAR
from almond.llm.schema import validate_response

rng = np.random.default_rng(3)
fails, succ = [], []
for _ in range(50):
    fails.append(dict(elevation_deg=float(rng.uniform(9, 14)), handover_advance_s=float(rng.choice([6, 8, 10])),
                      isl_hop_count=int(rng.integers(1, 6)), doppler_rate_hz_s=float(rng.uniform(1500, 4000)),
                      latitude_abs_deg=float(rng.uniform(70, 82)), snr_db=float(rng.uniform(7, 15)),
                      remaining_visibility_s=float(rng.uniform(10, 45)), plane_change=1.0, path_available=1.0,
                      buffer_occupancy=0.55, battery_state=1.0, eclipse=0.0))
for _ in range(120):
    succ.append(dict(elevation_deg=float(rng.uniform(25, 75)), handover_advance_s=float(rng.choice([14, 16, 18])),
                     isl_hop_count=int(rng.integers(0, 3)), doppler_rate_hz_s=float(rng.uniform(400, 1500)),
                     latitude_abs_deg=float(rng.uniform(30, 68)), snr_db=float(rng.uniform(16, 28)),
                     remaining_visibility_s=float(rng.uniform(120, 420)), plane_change=0.0, path_available=1.0,
                     buffer_occupancy=0.5, battery_state=1.0, eclipse=0.0))
narr = [f"at t={r['elevation_deg']:.0f}s on Resolute, elevation {r['elevation_deg']:.1f} deg, advance "
        f"{r['handover_advance_s']:.0f} s, ISL hops {r['isl_hop_count']}, plane change {int(r['plane_change'])}, "
        f"remaining visibility {r['remaining_visibility_s']:.0f} s -> session lost" for r in fails[:10]]
payload = dict(policy_id="pi_almon", region_tags={"polar": True, "regime": "arctic"}, kpi="hsr",
               kpi_value=0.55, threshold=0.85, failure_narratives=narr, failure_rows=fails,
               success_rows=succ, field_schema=FIELD_SCHEMA, effect_grammar=EFFECT_GRAMMAR)
log = LLMLog("results/llm_live_calls.jsonl")
client = LLMClient(OpenAICompatBackend(), log)
t0 = time.time()
data = client("forensic_hypothesis", payload, seed=11)
ok, prob = validate_response("forensic_hypothesis", data)
print(f"{time.time()-t0:.1f}s schema_ok={ok} {prob}")
for h in data["hypotheses"]:
    print("RULE:", json.dumps(h["if"]["all"]), "->", json.dumps(h["then"]))
    print("  why:", h.get("rationale", "")[:200])
print("retries:", client.schema_retries)
