import os

from almond.llm.backend import OpenAICompatBackend

be = OpenAICompatBackend()
print("backend:", be.name, be.model, be.base_url)
r = be.complete("forward_translate", {"intent": "reliability first", "regions": ["polar"]}, seed=0)
print("reply:", str(r)[:300])
