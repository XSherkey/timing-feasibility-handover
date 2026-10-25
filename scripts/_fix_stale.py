from pathlib import Path
p = Path(r"D:\almond-repro\almond\llm\semaphore.py")
s = p.read_text(encoding="utf-8")
s = s.replace("stale_s: float = 300.0", "stale_s: float = 60.0", 1)
p.write_text(s, encoding="utf-8")
print("stale_s -> 60 s (a call cannot legitimately hold a slot longer than the 90 s HTTP timeout)")
