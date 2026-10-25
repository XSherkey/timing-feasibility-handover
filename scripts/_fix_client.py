from pathlib import Path
p = Path(r"D:\almond-repro\almond\llm\backend.py")
s = p.read_text(encoding="utf-8")
# ReplayBackend also needs the repair_note parameter
s = s.replace("    def complete(self, call_type: str, payload: dict, seed: int = 0) -> LLMResponse:\n        key = cache_key(call_type, payload, seed)",
              "    def complete(self, call_type: str, payload: dict, seed: int = 0, repair_note: str = \"\") -> LLMResponse:\n        key = cache_key(call_type, payload, seed)")
# SurrogateBackend signature too
s = s.replace("    def complete(self, call_type: str, payload: dict, seed: int = 0) -> LLMResponse:\n        from .prompts import render_prompt\n        from . import surrogate as S",
              "    def complete(self, call_type: str, payload: dict, seed: int = 0, repair_note: str = \"\") -> LLMResponse:\n        from .prompts import render_prompt\n        from . import surrogate as S")
# summary(): count schema retries
s = s.replace("""        return dict(
            calls=n,
            tokens_in=toks_in,
            tokens_out=toks_out,
            latency_s=lat,""",
"""        return dict(
            calls=n,
            tokens_in=toks_in,
            tokens_out=toks_out,
            latency_s=lat,
            schema_failures=sum(1 for r in self.records if not r.get("schema_ok", True)),""")
p.write_text(s, encoding="utf-8")
print("backend patched")
