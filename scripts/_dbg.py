import numpy as np, sys
sys.path.insert(0,r"D:\Desktop_Files\论文\1. LLM Satellite Reinforcement Learning\自己写\almond-repro")
from almond.twin.constellation import make_tle, REFERENCE_SPEC, WalkerConstellation
from sgp4.api import jday, Satrec
tle = make_tle(10000, 2026, 292.25, 89.5, 0.0, 0.0002, 0.0, 0.0, 14.5789)
print(tle)
l = tle.strip().splitlines()
sat = Satrec.twoline2rv(l[1], l[2])
jd, fr = jday(2026,10,19,0,0,0.0)
print("epoch", sat.jdsatepoch, sat.jdsatepochF, "target", jd, fr)
jd_a = np.full(5, jd); fr_a = np.array([0.0,0.0001,0.001,0.01,0.04])
e,r,v = sat.sgp4_array(jd_a, fr_a)
print("err", e)
print(r if r is not None else "none")
e2,r2,v2 = sat.sgp4_array(np.array([jd]), np.array([0.0]))
print("single err", e2, r2)
