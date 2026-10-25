from pathlib import Path
p = Path(r"D:\almond-repro\almond\llm\backend.py")
s = p.read_text(encoding="utf-8")
# initialise the per-instance semaphore handle
old = """        self.json_mode = json_mode
        if not self.base_url:"""
new = """        self.json_mode = json_mode
        self._sem = None
        if not self.base_url:"""
assert old in s
s = s.replace(old, new, 1)
# a stuck request should fail fast enough for a retry, not block for minutes
s = s.replace("timeout_s: float = 180.0,", "timeout_s: float = 90.0,", 1)
p.write_text(s, encoding="utf-8")
print("semaphore wired; per-attempt timeout 90 s")
