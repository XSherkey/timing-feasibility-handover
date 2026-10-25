"""Debug one forensic call: render the real prompt and show the raw HTTP exchange."""
from __future__ import annotations

import json
import sys
import urllib.request
from pathlib import Path

import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from almond.framework.forensics import ForensicEngine, SplitConfig, episodes_to_narratives
from almond.llm.backend import DECODING, MAX_TOKENS
from almond.llm.prompts import render_prompt
from almond.llm.surrogate import EFFECT_GRAMMAR, FIELD_SCHEMA
from almond.policies.nets import GraphSpec, build_policy
from almond.twin.env import EnvConfig, HandoverEnv
from almond.twin.twin import DigitalTwin, TwinConfig

MODE = sys.argv[1] if len(sys.argv) > 1 else "enriched"
run = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("results/campaign/almond_seed1")

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
    import numpy as np
    cand = env.cand_idx[env.site, env.t_idx]
    mask = np.concatenate([np.ones((env.batch, 1), bool), cand >= 0], axis=1)
    with torch.no_grad():
        lt, la, _v = pol(torch.as_tensor(obs, dtype=torch.float32),
                         torch.as_tensor(xx, dtype=torch.float32),
                         torch.as_tensor(aa, dtype=torch.float32))
    lt = np.where(mask, lt.numpy(), -1e9)
    return lt.argmax(-1), la.numpy().argmax(-1)


class _Stop(Exception):
    pass


fe = ForensicEngine(twin=twin, env=env, policy_fn=policy_fn, llm=lambda *a, **k: (_ for _ in ()).throw(_Stop()),
                    kg=None, auditor=None, splits=SplitConfig())
disc = fe.discovery_rows(mode=MODE)
print(f"mode={MODE} discovery rows={len(disc)}")
from collections import Counter
print("causes:", dict(Counter(r.get("cause") for r in disc)))

base_val = None
payload = dict(
    policy_id="pi", region_tags=dict(polar=True, regime="arctic"), kpi="hsr", kpi_value=0.42,
    threshold=0.85, failure_narratives=episodes_to_narratives(disc, enriched=(MODE == "enriched")),
    failure_rows=disc, success_rows=[], field_schema=FIELD_SCHEMA, effect_grammar=EFFECT_GRAMMAR,
)
prompt = render_prompt("forensic_hypothesis", payload)
print(f"prompt chars: system={len(prompt['system'])} user={len(prompt['user'])}")
print("first narrative:", payload["failure_narratives"][0][:200])

body = dict(
    model="deepseek-flash",
    messages=[{"role": "system", "content": prompt["system"]}, {"role": "user", "content": prompt["user"]}],
    temperature=DECODING["forensic_hypothesis"]["temperature"],
    top_p=DECODING["forensic_hypothesis"]["top_p"],
    max_tokens=MAX_TOKENS,
    seed=0,
    response_format={"type": "json_object"},
)
req = urllib.request.Request(
    "https://api.deepseek.com/chat/completions",
    data=json.dumps(body).encode(),
    headers={"Content-Type": "application/json",
             "Authorization": f"Bearer {__import__('os').environ['ALMOND_LLM_API_KEY']}"},
    method="POST",
)
try:
    with urllib.request.urlopen(req, timeout=120) as resp:
        raw = resp.read().decode()
    print("HTTP OK, body bytes:", len(raw))
    out = json.loads(raw)
    msg = out["choices"][0]["message"]
    print("finish_reason:", out["choices"][0].get("finish_reason"))
    print("content len:", len(msg.get("content") or ""))
    print("content preview:", (msg.get("content") or "")[:400])
    print("usage:", out.get("usage"))
except urllib.error.HTTPError as exc:
    print("HTTPError", exc.code)
    print(exc.read().decode()[:800])
except Exception as exc:
    print("EXC", type(exc).__name__, exc)
