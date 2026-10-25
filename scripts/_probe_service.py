import sys, numpy as np
sys.path.insert(0, r"D:\almond-repro")
from almond.twin.twin import DigitalTwin, TwinConfig
from almond.twin.env import HandoverEnv, EnvConfig
twin = DigitalTwin(TwinConfig(tag="ref", horizon_s=12*3600)).build(verbose=False)
env = HandoverEnv(twin, EnvConfig(episode_steps=240), batch=32, seed=0)
rng = np.random.default_rng(0)
obs = env.reset(t_range=(3540, 3760))
sess = []; up = []; srvpos = []; off = []; served = []; attempts = 0
for _ in range(240):
    at = rng.integers(0, env.K + 1, size=env.batch)
    ad = rng.integers(0, env.n_advance, size=env.batch)
    obs, r, d, info = env.step(at, ad)
    sess.append(env.session.mean()); srvpos.append((env.serving >= 0).mean()); off.append((env.offline > 0).mean())
    served.append(info["served"].mean()); attempts += int(info["commanded"].sum())
print("session-on mean %.3f | serving>=0 %.3f | offline %.3f | served %.3f | commanded/step %.2f" % (
    np.mean(sess), np.mean(srvpos), np.mean(off), np.mean(served), attempts/240))
st = env.episode_stats()
print("attempts %.0f successes %.0f drops %.0f  HSR %.3f" % (st["attempts"].sum(), st["successes"].sum(), st["drops"].sum(), st["hsr"].mean()))
# how long does a session last once started?
print("episode_stats keys", list(st.keys()))
