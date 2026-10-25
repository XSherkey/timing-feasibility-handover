"""Why does a candidate never clear the validation gate?  Print every stage."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from almond.framework.auditor import Auditor
from almond.framework.forensics import ForensicEngine, SplitConfig, replay_rule, score
from almond.framework.kg import KnowledgeGraph
from almond.llm.backend import LLMClient, LLMLog, _default_backend
from almond.policies.nets import GraphSpec, build_policy
from almond.twin.env import EnvConfig, HandoverEnv
from almond.twin.twin import DigitalTwin, TwinConfig

run = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("results/campaign_v1_legacy/almond_seed1")
mode = sys.argv[2] if len(sys.argv) > 2 else "enriched"

blob = torch.load(run / "policy.pt", map_location="cpu", weights_only=False)
spec = GraphSpec.from_dict(blob["spec"])
twin = DigitalTwin(TwinConfig(tag="ref", horizon_s=12 * 3600)).build(verbose=False)
w = blob.get("weights") or dict(w_rel=0.57, w_lat=0.14, w_pow=0.29)
env = HandoverEnv(twin, EnvConfig(episode_steps=240, w_rel=w["w_rel"], w_lat=w["w_lat"], w_pow=w["w_pow"]),
                  batch=24, seed=13)
x, adj = env.candidate_graph()
pol = build_policy("graph", obs_dim=env.obs_dim, node_dim=x.shape[-1],
                   n_targets=env.K + 1, n_advance=env.n_advance, spec=spec)
pol.load_state_dict(blob["policy"])
pol.eval()


def policy_fn(obs, xx, aa, deterministic=True):
    cand = env.cand_idx[env.site, env.t_idx]
    mask = np.concatenate([np.ones((env.batch, 1), bool), cand >= 0], axis=1)
    with torch.no_grad():
        lt, la, _v = pol(torch.as_tensor(obs, dtype=torch.float32),
                         torch.as_tensor(xx, dtype=torch.float32),
                         torch.as_tensor(aa, dtype=torch.float32))
    lt = np.where(mask, lt.numpy(), -1e9)
    return lt.argmax(-1), la.numpy().argmax(-1)


splits = SplitConfig()
print("split ranges:", {k: splits.indices(twin.n_time, k, env.cfg.episode_steps)
                        for k in ("train", "validation", "test")})
for which in ("train", "validation", "test"):
    r = replay_rule(env, policy_fn, None, 3, splits.indices(twin.n_time, which, env.cfg.episode_steps))
    att = r["attempts"]
    from collections import Counter
    print(f"{which:<11} attempts={len(att):4d} "
          f"success={sum(1 for a in att if a['success']):4d} "
          f"score={score(r['rows'], 'arctic')} "
          f"causes={dict(Counter(a.get('cause') for a in att))}")

llm = LLMClient(_default_backend(), LLMLog(Path("results/_dbg_calls.jsonl")))
kg_path = Path("results/_dbg_kg.json")
if kg_path.exists():
    kg_path.unlink()
fe = ForensicEngine(twin=twin, env=env, policy_fn=policy_fn, llm=llm, kg=KnowledgeGraph(kg_path),
                    auditor=Auditor(impact=None, require_impact=False), splits=splits,
                    delta_min=0.05)
res = fe.run(max_attempts=1, validate_episodes=3, test_episodes=3, discovery_mode=mode)
print("\n--- stage log ---")
for e in res.stage_log:
    if e.get("event") in ("discovery", "baseline", "audit", "validation", "test", "commit",
                          "latency_violation", "no_failures"):
        print(" ", {k: (round(v, 4) if isinstance(v, float) else v) for k, v in e.items()})
print("\naccepted:", res.accepted, "delta_val", round(res.delta_val, 4),
      "delta_test", round(res.delta_test, 4))
