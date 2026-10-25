import sys, time, numpy as np, torch
sys.path.insert(0, r"D:\Desktop_Files\论文\1. LLM Satellite Reinforcement Learning\自己写\almond-repro")
from almond.twin.twin import DigitalTwin, TwinConfig
from almond.twin.env import HandoverEnv, EnvConfig
from almond.policies.nets import GraphSpec, build_policy

t0=time.time(); tw = DigitalTwin(TwinConfig(tag="ref", horizon_s=12*3600)).build(verbose=False)
print("twin load %.2fs" % (time.time()-t0))
env = HandoverEnv(tw, EnvConfig(episode_steps=240), batch=24, seed=0)
# warm the mmap pages we will touch
env.reset()
x, adj = env.candidate_graph()
pol = build_policy("graph", obs_dim=env.obs_dim, node_dim=x.shape[-1], n_targets=env.K+1, n_advance=env.n_advance, spec=GraphSpec(kind="gcn", width=64, layers=2))
for dev in ("cpu","cuda"):
    p = pol.to(dev)
    N=600
    env.reset()
    obs = env.obs()
    t0=time.time()
    for _ in range(N):
        xx, aa = env.candidate_graph()
        ot=torch.as_tensor(obs, device=dev); xt=torch.as_tensor(xx, device=dev); at=torch.as_tensor(aa, device=dev)
        with torch.no_grad():
            lt, la, v = p(ot, xt, at)
            a1 = lt.argmax(-1).cpu().numpy(); a2 = la.argmax(-1).cpu().numpy()
        obs, r, d, i = env.step(a1, a2)
    dt = time.time()-t0
    print(f"{dev}: {N} steps in {dt:.2f}s -> {dt/N*1000:.2f} ms/step")
    # env only
    obs = env.reset()
    t0=time.time()
    for _ in range(N):
        xx, aa = env.candidate_graph()
        ot=np.asarray(obs); xt=np.asarray(xx); at=np.asarray(aa)
        a1 = np.zeros(env.batch, dtype=np.int64); a2 = np.zeros(env.batch, dtype=np.int64)
        obs, r, d, i = env.step(a1, a2)
    dt = time.time()-t0
    print(f"  env only: {dt/N*1000:.2f} ms/step")
