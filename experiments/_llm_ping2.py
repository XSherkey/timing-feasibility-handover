import json
import os
import urllib.request

from almond.llm.backend import OpenAICompatBackend

be = OpenAICompatBackend()
body = {
    "model": be.model,
    "messages": [
        {"role": "system", "content": "You are a JSON-only assistant."},
        {"role": "user", "content": "Return {\"ok\": true, \"n\": 3} and nothing else."},
    ],
    "temperature": 0.0,
    "response_format": {"type": "json_object"},
}
req = urllib.request.Request(
    f"{be.base_url}/chat/completions",
    data=json.dumps(body).encode(),
    headers={"Content-Type": "application/json", "Authorization": f"Bearer {be.api_key}"},
    method="POST",
)
with urllib.request.urlopen(req, timeout=60) as resp:
    out = json.loads(resp.read().decode())
print("model:", out.get("model"), "| content:", out["choices"][0]["message"]["content"][:120])
