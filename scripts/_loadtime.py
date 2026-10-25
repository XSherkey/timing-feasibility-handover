import sys, time
sys.path.insert(0, r"D:\Desktop_Files\论文\1. LLM Satellite Reinforcement Learning\自己写\almond-repro")
from almond.twin.twin import DigitalTwin, TwinConfig
cfg = TwinConfig(tag="ref", horizon_s=12*3600)
print("fingerprint", cfg.fingerprint())
t0=time.time(); tw = DigitalTwin(cfg); print("ctor %.2fs" % (time.time()-t0)); print("dir", tw.cache_dir.name, "exists", tw.cache_dir.exists())
t0=time.time(); tw.build(verbose=True); print("build/load %.2fs" % (time.time()-t0))
