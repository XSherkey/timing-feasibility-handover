import sys
sys.path.insert(0, r"D:\almond-repro")
import numpy as np
from almond.llm.surrogate import forward_translate
from almond.framework.translator import INTENT_TEMPLATES
for name in ("reliability_first","latency_first","power_first","balanced"):
    d = forward_translate({"intent": INTENT_TEMPLATES[name]}, np.random.default_rng(0))
    print(f"{name:<18}", d["weights"])
