import sys, numpy as np
sys.path.insert(0, r"D:\Desktop_Files\论文\1. LLM Satellite Reinforcement Learning\自己写\almond-repro")
from almond.twin.twin import DigitalTwin, TwinConfig
cfg = TwinConfig(horizon_s=5400, dt_s=10, tag="cal", feeder_slots=8)
tw = DigitalTwin(cfg).build()
fp = tw["feed_press"]; el = tw["el"]; hop = tw["hop"]
print("feed_press max", int(fp.max()), "mean", float(fp.mean()), "p90", float(np.percentile(fp[fp>0],90)) if (fp>0).any() else 0)
gws = tw.gateway_site_index
print("n gateway sites", len(gws))
for gi in gws[:8]:
    col = el[gi]
    print(f"  {tw.sites[gi].name:<16} mean sats>15deg = {float((col>15).sum(axis=0).mean()):.1f}  max {int((col>15).sum(axis=0).max())}")
print("hop p50 overall", np.percentile(hop[hop>=0],50))
