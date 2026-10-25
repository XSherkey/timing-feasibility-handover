from pathlib import Path
p = Path(r"D:\almond-repro\almond\framework\system.py")
s = p.read_text(encoding="utf-8")
# the config default must be "auto" (otherwise it always forces the surrogate)
assert 'llm_backend: str = "surrogate"' in s
s = s.replace('llm_backend: str = "surrogate"', 'llm_backend: str = "auto"', 1)
assert 'if cfg.llm_backend == "surrogate" or _os.environ.get("ALMOND_LLM_BACKEND") == "surrogate":' in s
p.write_text(s, encoding="utf-8")
print("llm_backend default -> auto")
