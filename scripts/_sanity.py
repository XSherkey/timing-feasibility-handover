import sys, numpy as np, torch
sys.path.insert(0, r"D:\almond-repro")
from almond.twin.twin import DigitalTwin, TwinConfig
from almond.twin.env import HandoverEnv, EnvConfig
from almond.policies.nets import GraphSpec, build_policy
from almond.policies.ppo import PPOConfig, PPOTrainer
twin = DigitalTwin(TwinConfig(tag="ref", horizon_s=12*3600)).build(verbose=False)
env = HandoverEnv(twin, EnvConfig(episode_steps=200, w_rel=0.57, w_lat=0.14, w_pow=0.29), batch=16, seed=0)
x, adj = env.candidate_graph()
pol = build_policy("graph", obs_dim=env.obs_dim, node_dim=x.shape[-1], n_targets=env.K+1, n_advance=env.n_advance, spec=GraphSpec(kind="gcn", width=64, layers=2))
tr = PPOTrainer(env, pol, PPOConfig(total_episodes=300, rollout_steps=256, minibatch=256, device="cpu", early_stop_patience=10**9))
tr.train(log_every=0)
res = tr.evaluate(episodes=3, t_range=(3600, 3900))
rows = res["rows"]
att = res["attempts"]
print("HSR %.3f  params %d" % (np.mean([r["hsr"] for r in rows]), pol.param_count()))
fails = [r for r in att if not r["success"]]
def frac(p): return 100*sum(1 for r in fails if p(r))/max(len(fails),1)
print("fails: no_path %.0f%% lead<t_setup %.0f%% lead>trem %.0f%%" % (
  frac(lambda r: r["path_available"]<0.5), frac(lambda r: r["handover_advance_s"]<r["t_setup_s"]-1e-9),
  frac(lambda r: r["handover_advance_s"]>r["remaining_visibility_s"]+1e-9)))
arc = [r for r in rows if abs(r["lat"])>70]; mid=[r for r in rows if 30<=abs(r["lat"])<65]
def h(s): 
    a=sum(x["attempts"] for x in s); return 100*sum(x["successes"] for x in s)/max(a,1)
print("arctic %.1f%%  mid %.1f%%  lead_med %.0f  tsetup_med %.1f" % (h(arc), h(mid),
  np.median([r["handover_advance_s"] for r in att]), np.median([r["t_setup_s"] for r in att])))
