import sys
sys.path.insert(0,r"D:\Desktop_Files\论文\1. LLM Satellite Reinforcement Learning\自己写\almond-repro")
from almond.twin.constellation import make_tle
from sgp4.api import Satrec
l = make_tle(10000, 2026, 292.25, 89.5, 0.0, 0.0002, 0.0, 0.0, 14.5789).strip().splitlines()
s = Satrec.twoline2rv(l[1], l[2])
print("no_kozai rad/min", s.no_kozai, "ecco", s.ecco, "inclo", s.inclo, "argpo", s.argpo, "mo", s.mo, "nodeo", s.nodeo)
print("bstar", s.bstar, "error on init", s.error)
real = Satrec.twoline2rv(
 "1 44714U 19074B   26292.10353693  .00048057  00000+0  43854-3 0  9992",
 "2 44714  53.1443 186.7069 0002756 134.2207 225.9036 15.67409625383554")
print("real no_kozai", real.no_kozai, "ecco", real.ecco)
print("len line1", len(l[1]), "len line2", len(l[2]))
print(repr(l[1])); print(repr(l[2]))
print("cols mm:", repr(l[2][52:63]))
