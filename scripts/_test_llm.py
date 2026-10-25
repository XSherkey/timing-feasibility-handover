import sys, json
sys.path.insert(0, r"D:\Desktop_Files\论文\1. LLM Satellite Reinforcement Learning\自己写\almond-repro")
import numpy as np
from almond.llm.backend import LLMClient, SurrogateBackend, LLMLog
from almond.llm.prompts import render_prompt

client = LLMClient(SurrogateBackend(), LLMLog())
intent = {"priorities": {"reliability": "highest", "latency": "low", "power": "medium"},
          "requirements": ["uninterrupted Arctic video", "session continuity above 99%"]}
p = client("forward_translate", {"intent": intent, "env_desc": "LEO handover", "task_short_desc": "handover"}, seed=1)
print("weights", p["weights"], "sum", round(sum(p["weights"].values()),6))
print("prompt chars", len(render_prompt("forward_translate", {"intent": intent})["user"]))

rng = np.random.default_rng(0)
fails = []
for i in range(60):
    fails.append(dict(elevation_deg=float(rng.uniform(8, 14)), handover_advance_s=float(rng.choice([4,6])),
                      isl_hop_count=int(rng.integers(1,6)), plane_change=1, latitude_abs_deg=float(rng.uniform(70,82)),
                      path_available=1, snr_db=float(rng.uniform(6,14)), doppler_rate_hz_s=float(rng.uniform(1000,4000)),
                      remaining_visibility_s=float(rng.uniform(5,20)), buffer_occupancy=0.4, battery_state=1.0, eclipse=0))
succ = []
for i in range(120):
    succ.append(dict(elevation_deg=float(rng.uniform(20, 80)), handover_advance_s=float(rng.choice([10,12,14])),
                     isl_hop_count=int(rng.integers(0,4)), plane_change=int(rng.integers(0,2)), latitude_abs_deg=float(rng.uniform(30,70)),
                     path_available=1, snr_db=float(rng.uniform(14,26)), doppler_rate_hz_s=float(rng.uniform(800,2000)),
                     remaining_visibility_s=float(rng.uniform(30,200)), buffer_occupancy=0.5, battery_state=1.0, eclipse=0))
q = client("forensic_hypothesis", {"policy_id":"pi_0","region_tags":{"polar":True},"kpi":"hsr","kpi_value":0.55,
                                   "threshold":0.85,"failure_rows":fails,"success_rows":succ}, seed=3)
for h in q["hypotheses"]:
    print("RULE:", json.dumps(h["if"]), "->", h["then"], "|", h["rationale"])
t = client("topology_seed", {"regime_tags":{"polar":True,"sparse_isl":True}}, seed=5)
print("seed:", t["kind"], t["width"], t["layers"], t["heads"])
m = client("topology_mutation", {"sketch":t,"fitness_feedback":{"objective":"params","too_large":True}}, seed=6)
print("mut:", m["kind"], m["width"], m["layers"], m["rationale"])
c = client("topology_crossover", {"sketch_a":t,"sketch_b":m}, seed=7)
print("cross:", c["kind"], c["width"], c["layers"])
cr = client("population_critique", {"elites":[{"layers":2,"width":64},{"layers":3,"width":128}],"probs":{"mutation_rate":0.3,"crossover_rate":0.4}}, seed=8)
print("crit:", cr["mutation_rate"], cr["crossover_rate"])
print("log summary:", client.log.summary())
