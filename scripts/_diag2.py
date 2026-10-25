import sys, json, numpy as np, torch
sys.path.insert(0, r"D:\almond-repro")
from almond.twin.twin import DigitalTwin, TwinConfig
from almond.twin.env import HandoverEnv, EnvConfig
from almond.policies.nets import GraphSpec, build_policy

twin = DigitalTwin(TwinConfig(tag="ref", horizon_s=12*3600)).build(verbose=False)
env = HandoverEnv(twin, EnvConfig(episode_steps=240), batch=28, seed=101)
blob = torch.load("results/campaign/almond_fixedarch_seed0/policy.pt", map_location="cpu", weights_only=False)
spec = GraphSpec.from_dict(blob["spec"])
x, adj = env.candidate_graph()
pol = build_policy("graph", obs_dim=env.obs_dim, node_dim=x.shape[-1], n_targets=env.K+1, n_advance=env.n_advance, spec=spec)
pol.load_state_dict(blob["policy"]); pol.eval()
env.reset(t_range=(3600, 3900))
for _ in range(240):
    xx, aa = env.candidate_graph()
    cand = env.cand_idx[env.site, env.t_idx]
    m = np.concatenate([np.ones((env.batch,1), bool), cand>=0], axis=1)
    with torch.no_grad():
        lt, la, _ = pol(torch.as_tensor(env.obs()), torch.as_tensor(xx), torch.as_tensor(aa))
    lt = lt.numpy(); lt[~m] = -1e9
    env.step(lt.argmax(-1), la.numpy().argmax(-1), record=True)
st = env.episode_stats()
fails = [r for r in env.attempt_log if not r["success"]]
att = env.attempt_log
print("total attempts", len(att), "HSR %.3f" % (1-len(fails)/max(len(att),1)))
def frac(pred):
    return 100*sum(1 for r in fails if pred(r))/max(len(fails),1)
print("fail: no_path %.0f%% lead<t_setup %.0f%% lead>trem %.0f%%" % (
  frac(lambda r: r["path_available"]<0.5), frac(lambda r: r["handover_advance_s"] < r["t_setup_s"]-1e-9),
  frac(lambda r: r["handover_advance_s"] > r["remaining_visibility_s"]+1e-9)))
by_site = {}
for r in att:
    d = by_site.setdefault(r["site"], [0,0])
    d[1]+=1
    if r["success"]: d[0]+=1
for s,(ok,n) in sorted(by_site.items(), key=lambda kv: -kv[1][1]):
    print(f"  {s:<14} HSR {100*ok/max(n,1):5.1f}%  attempts {n}")
print("lead median", np.median([r["handover_advance_s"] for r in att]),
      " t_setup median", np.median([r["t_setup_s"] for r in att]),
      " trem median", np.median([r["remaining_visibility_s"] for r in att]))
