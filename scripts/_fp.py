import sys
sys.path.insert(0, r"D:\Desktop_Files\论文\1. LLM Satellite Reinforcement Learning\自己写\almond-repro")
from almond.twin.twin import TwinConfig
print("A", TwinConfig(tag="ref", horizon_s=12*3600).fingerprint())
print("B", TwinConfig(tag="ref", horizon_s=12.0*3600.0).fingerprint())
print("C", TwinConfig(tag="ref", horizon_s=43200.0, dt_s=10.0).fingerprint())
