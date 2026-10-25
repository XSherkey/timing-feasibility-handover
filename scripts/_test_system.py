import sys, json, time
sys.path.insert(0, r"D:\Desktop_Files\论文\1. LLM Satellite Reinforcement Learning\自己写\almond-repro")
from almond.framework.system import AlmondSystem, AlmondConfig
cfg = AlmondConfig(variant="full", seed=0, device="cuda", episodes=60, eval_every=20,
                   forensics_after=20, nas_generations=1, nas_population=4, nas_eval_episodes=20,
                   nas_batch=6, episode_steps=120, batch=16, rollout_steps=128, minibatch=128,
                   validate_episodes=1, test_episodes=1, twin_tag="cal", twin_hours=1.5)
t0=time.time()
sysm = AlmondSystem(cfg, out_dir=r"D:\Desktop_Files\论文\1. LLM Satellite Reinforcement Learning\自己写\almond-repro\results\_smoke")
out = sysm.run()
print("wall", round(time.time()-t0,1))
print("weights", out["weights"])
print("spec", out["spec"])
print("params", out["params"])
print("kg", out["kg"])
print("forensics", [(f["accepted"], f["effect"], f["magnitude"], round(f["delta_test"],3)) for f in out["forensics"]])
print("curve", [(c["episodes"], round(c.get("S",0),1), round(c.get("hsr_arctic",0),3)) for c in out["curve"]])
print("final", {k: (round(v["hsr"],3) if isinstance(v,dict) and "hsr" in v else v) for k,v in out["final"].items() if k in ("overall","arctic","midlat","equatorial","satisfaction")})
