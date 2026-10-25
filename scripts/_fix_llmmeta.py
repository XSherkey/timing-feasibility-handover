from pathlib import Path
p = Path(r"D:\almond-repro\almond\framework\system.py")
s = p.read_text(encoding="utf-8")
old = "            llm=self.llm_log.summary(),"
new = """            llm=dict(
                **self.llm_log.summary(),
                backend=self.llm.backend.name,
                model=getattr(self.llm.backend, "model", "surrogate"),
                schema_retries=int(getattr(self.llm, "schema_retries", 0)),
            ),"""
assert old in s
s = s.replace(old, new, 1)
p.write_text(s, encoding="utf-8")
print("run summaries now record the LLM backend")
