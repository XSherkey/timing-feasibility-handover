import sys, numpy as np
sys.path.insert(0, r"D:\Desktop_Files\论文\1. LLM Satellite Reinforcement Learning\自己写\almond-repro")
from almond.twin.twin import DigitalTwin, TwinConfig
from almond.twin.env import HandoverEnv, EnvConfig
from almond.policies.nets import GraphSpec, build_policy
from almond.policies.ppo import PPOConfig, PPOTrainer

twin = DigitalTwin(TwinConfig(horizon_s=5400, tag="probe")).build(verbose=False)
env = HandoverEnv(twin, EnvConfig(episode_steps=240, w_rel=0.8, w_lat=0.12, w_pow=0.08), batch=32, seed=0)
x, adj = env.candidate_graph()
pol = build_policy("graph", obs_dim=env.obs_dim, node_dim=x.shape[-1], n_targets=env.K+1, n_advance=env.n_advance, spec=GraphSpec(kind="gcn", width=64, layers=2))
tr = PPOTrainer(env, pol, PPOConfig(total_episodes=300, rollout_steps=512, minibatch=256, device="cuda", early_stop_patience=10**9))
tr.train(log_every=0)
env.reset(); log=[]
for _ in range(240):
    xx, aa_ = env.candidate_graph()
    at, ad, _lp, _v = tr._act(env.obs(), xx, aa_, deterministic=True)
    env.step(at, ad, record=True)
log = env.attempt_log
att = [r for r in log]
fails = [r for r in att if not r["success"]]
print(f"attempts={len(att)} fails={len(fails)} HSR={1-len(fails)/max(len(att),1):.3f}")
def frac(pred, sub=fails):
    return 100*sum(1 for r in sub if pred(r))/max(len(sub),1)
print("fail reasons: no_path %.1f%%  lead<t_setup %.1f%%  lead>trem %.1f%%  target_below_mask %.1f%%" % (
  frac(lambda r: r["path_available"] < 0.5),
  frac(lambda r: r["handover_advance_s"] < r["t_setup_s"] - 1e-9),
  frac(lambda r: r["handover_advance_s"] > r["remaining_visibility_s"] + 1e-9),
  frac(lambda r: r["elevation_deg"] <= 10)))
ok = [r for r in att if r["success"]]
for name, sub in (("success", ok), ("fail", fails)):
    if sub:
        print(f"{name}: lead med {np.median([r['handover_advance_s'] for r in sub]):.0f}s  "
              f"trem med {np.median([r['remaining_visibility_s'] for r in sub]):.0f}s  "
              f"t_setup med {np.median([r['t_setup_s'] for r in sub]):.1f}s  "
              f"hop med {np.median([r['isl_hop_count'] for r in sub]):.0f}  "
              f"planechg {np.mean([r['plane_change'] for r in sub])*100:.0f}%  "
              f"lat med {np.median([r['lat'] for r in sub]):.0f}")
# arctic only
arc = [r for r in att if abs(r["lat"])>70]
arcf = [r for r in arc if not r["success"]]
print(f"arctic attempts={len(arc)} HSR={1-len(arcf)/max(len(arc),1):.3f}")
print("arctic fails: no_path %.1f%% lead<t_setup %.1f%% lead>trem %.1f%%" % (
  frac(lambda r: r["path_available"]<0.5, arcf), frac(lambda r: r["handover_advance_s"] < r["t_setup_s"]-1e-9, arcf),
  frac(lambda r: r["handover_advance_s"] > r["remaining_visibility_s"]+1e-9, arcf)))
print("arctic t_setup p50/p90 %.1f/%.1f  trem p50 %.0f" % (
  np.median([r["t_setup_s"] for r in arc]), np.percentile([r["t_setup_s"] for r in arc],90),
  np.median([r["remaining_visibility_s"] for r in arc])))
mid = [r for r in att if 30<=abs(r["lat"])<65]
print("mid t_setup p50/p90 %.1f/%.1f  trem p50 %.0f  HSR %.3f" % (
  np.median([r["t_setup_s"] for r in mid]), np.percentile([r["t_setup_s"] for r in mid],90),
  np.median([r["remaining_visibility_s"] for r in mid]),
  1-sum(1 for r in mid if not r["success"])/max(len(mid),1)))
