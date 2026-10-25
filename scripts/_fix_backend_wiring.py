from pathlib import Path
p = Path(r"D:\almond-repro\almond\framework\system.py")
s = p.read_text(encoding="utf-8")
old = """        self.llm_log = LLMLog(self.out / "llm_calls.jsonl")
        backend = SurrogateBackend()
        self.llm = LLMClient(backend, self.llm_log)"""
new = """        self.llm_log = LLMLog(self.out / "llm_calls.jsonl")
        # honour the environment: a configured OpenAI-compatible endpoint is used
        # automatically; ALMOND_LLM_BACKEND=surrogate forces the offline fallback
        import os as _os

        from ..llm.backend import _default_backend

        if cfg.llm_backend == "surrogate" or _os.environ.get("ALMOND_LLM_BACKEND") == "surrogate":
            backend = SurrogateBackend()
        else:
            backend = _default_backend()
        self.llm = LLMClient(backend, self.llm_log)"""
assert old in s, "backend construction block not found"
s = s.replace(old, new, 1)
p.write_text(s, encoding="utf-8")
print("system now uses the configured backend")
