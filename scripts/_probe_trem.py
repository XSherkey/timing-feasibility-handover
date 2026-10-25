import sys, numpy as np
sys.path.insert(0, r"D:\Desktop_Files\论文\1. LLM Satellite Reinforcement Learning\自己写\almond-repro")
from almond.twin.twin import DigitalTwin, TwinConfig
tw = DigitalTwin(TwinConfig(horizon_s=5400, tag="probe")).build(verbose=False)
trem = tw["trem"]; el = tw["el"]; hop = tw["hop"]
for si in tw.user_site_index:
    s = tw.sites[si]
    vis = el[si] > 10
    sv = trem[si] > 0
    t = trem[si][sv]
    print(f"{s.name:<14}{s.lat_deg:7.1f}  geometric_links={vis.sum():7d}  service_links={sv.sum():7d}"
          f"  trem p50={np.median(t):6.1f} p90={np.percentile(t,90):6.1f} max={t.max():6.0f}"
          f"  frac<12s={100*(t<12).mean():5.1f}%")
