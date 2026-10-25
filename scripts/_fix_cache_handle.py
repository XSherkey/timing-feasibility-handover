from pathlib import Path
p = Path(r"D:\almond-repro\almond\llm\backend.py")
s = p.read_text(encoding="utf-8")
old = """        self.calls = 0
        self.schema_retries = 0
        self.exhausted = 0"""
new = """        self.calls = 0
        self.schema_retries = 0
        self.exhausted = 0
        self._cache = None"""
assert old in s
s = s.replace(old, new, 1)
p.write_text(s, encoding="utf-8")
print("cache handle added")
