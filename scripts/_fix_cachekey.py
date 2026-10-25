from pathlib import Path
p = Path(r"D:\almond-repro\almond\llm\backend.py")
s = p.read_text(encoding="utf-8")
old = '''def cache_key(call_type: str, payload: dict, seed: int) -> str:
    blob = json.dumps(dict(call_type=call_type, payload=payload, seed=seed), sort_keys=True, default=str)
    return hashlib.sha1(blob.encode()).hexdigest()'''
new = '''def cache_key(call_type: str, payload: dict, seed: int, model: str = "default") -> str:
    """Cache identity: call type, payload, seed **and** the serving model.

    The model must be part of the key, otherwise a run against a second endpoint
    would silently reuse the first model's audited artifacts and the cross-model
    comparison would be meaningless.
    """
    blob = json.dumps(
        dict(call_type=call_type, payload=payload, seed=seed, model=model),
        sort_keys=True, default=str,
    )
    return hashlib.sha1(blob.encode()).hexdigest()'''
assert old in s
s = s.replace(old, new, 1)
p.write_text(s, encoding="utf-8")
print("cache key now model-aware")
