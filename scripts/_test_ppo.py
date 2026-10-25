import sys, time
sys.path.insert(0, r"D:\Desktop_Files\论文\1. LLM Satellite Reinforcement Learning\自己写\almond-repro")
import numpy as np, torch
from almond.twin.twin import DigitalTwin, TwinConfig
from almond.twin.env import HandoverEnv, EnvConfig
from almond.policies.nets import build_policy, GraphSpec
from almond.policies.ppo import PPOConfig, PPOTrainer

twin = DigitalTwin(TwinConfig(horizon_s=5400, tag="cal")).build()
print("twin ok", twin.n_sat, twin.n_time)
ecfg = EnvConfig(episode_steps=120)
env = HandoverEnv(twin, ecfg, batch=16, seed=0)
print("obs_dim", env.obs_dim, "K", env.K, "n_adv", env.n_advance)
x, adj = env.candidate_graph()
print("graph", x.shape, adj.shape)
pol = build_policy("flat", obs_dim=env.obs_dim, node_dim=x.shape[-1], n_targets=env.K+1, n_advance=env.n_advance)
print("flat params", pol.param_count())
gpol = build_policy("graph", obs_dim=env.obs_dim, node_dim=x.shape[-1], n_targets=env.K+1, n_advance=env.n_advance, spec=GraphSpec(kind="gcn", width=64, layers=2))
print("graph params", gpol.param_count(), gpol.spec.describe())
pcfg = PPOConfig(total_episodes=40, rollout_steps=64, minibatch=64, epochs=2, device="cuda", lr=1e-3, early_stop_patience=1000)
tr = PPOTrainer(env, pol, pcfg)
t0=time.time()
res = tr.train(log_every=5)
print("trained", res["episodes"], "episodes in", round(res["wall_s"],1), "s; updates", res["updates"])
ev = tr.evaluate(episodes=3)
rows = ev["rows"]
print("eval HSR mean %.3f  arctic %.3f" % (
    np.mean([r["hsr"] for r in rows]),
    np.mean([r["hsr"] for r in rows if abs(r["lat"])>70]) if any(abs(r["lat"])>70 for r in rows) else float("nan")))
